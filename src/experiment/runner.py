"""Experiment execution runners for mock fixture and live dispatch with durable resume.

An ambiguous crash is deliberately not retried: local persistence cannot prove
whether an external request was accepted. Terminal failures are completed work.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from src.baseline.pipeline import BaselinePipeline
from src.experiment.authorization import (
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    ScientificProtocolApproval,
    compute_protocol_sha256,
    protocol_decision_dict,
    protocol_to_dict,
    validate_live_authorization,
)
from src.experiment.config import (
    ValidatedPlan,
    _validate_dataset,
    canonical_bytes,
    digest,
    parse_json,
    parse_jsonl,
    registry_ids_from_bytes,
)
from src.experiment.journal import RequestState
from src.experiment.schemas import CONDITIONS, ExperimentConfig, ExperimentRecord
from src.llm.client import LiveBudget, LiveBudgetExceededError, LLMClient
from src.llm.schemas import validate_technique_id
from src.rag.pipeline import RAGPipeline
from src.retrieval.retriever import FAISSRetriever, StubEmbedder


@dataclass(frozen=True)
class MockReply:
    raw_text: str = '{"technique_id":"T1059.001"}'
    status: str = "completed"
    input_tokens: int | None = 10
    output_tokens: int | None = 1
    refusal: str | None = None


class MockProvider:
    """A concrete in-memory fake, not a pluggable network-capable provider factory."""

    def __init__(self, outcomes=None):
        self.outcomes = outcomes or {}
        self.responses = self
        self.calls = []
        self.key = None
        self.attempt = 0

    def activate(self, key):
        self.key = key
        self.attempt = 0

    def create(self, **kwargs):
        self.calls.append((self.key, kwargs))
        outcomes = self.outcomes.get(self.key, [MockReply()])
        outcome = outcomes[min(self.attempt, len(outcomes) - 1)]
        self.attempt += 1
        if isinstance(outcome, BaseException):
            raise outcome
        if type(outcome) is not MockReply:
            raise TypeError("mock outcomes must be MockReply or exception instances")
        return SimpleNamespace(
            status=outcome.status,
            output=[],
            output_text=outcome.raw_text,
            refusal=getattr(outcome, "refusal", None),
            usage=SimpleNamespace(
                input_tokens=outcome.input_tokens, output_tokens=outcome.output_tokens
            ),
        )


def _append(path, value):
    with path.open("ab") as stream:
        stream.write(canonical_bytes(value) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def _exclusive_lock(directory):
    lock = directory / ".run.lock"
    try:
        stream = lock.open("x", encoding="utf-8")
    except FileExistsError as exc:
        raise ValueError(
            "run directory locked; stale locks require explicit human reconciliation"
        ) from exc
    try:
        with stream:
            stream.write(str(os.getpid()))
            stream.flush()
            os.fsync(stream.fileno())
        yield
    finally:
        lock.unlink()


class JournalBudget(LiveBudget):
    """Tracks durable provider attempt spending against authorized attempt budget."""

    def __init__(self, max_requests, journal, *, consumed=0):
        super().__init__(max_requests)
        if type(consumed) is not int or not 0 <= consumed <= max_requests:
            raise ValueError("invalid persisted request spending")
        self._count = consumed
        self.journal = journal
        self.key = None

    @property
    def authorized_max_provider_attempts(self) -> int:
        return self.max_requests

    @property
    def consumed_provider_attempts(self) -> int:
        return self._count

    def consume(self):
        with self._lock:
            if self.key is None:
                raise ValueError("request has no active sample-condition reservation")
            if self._count >= self.max_requests:
                raise LiveBudgetExceededError("explicit experiment request budget exhausted")
            _append(
                self.journal,
                {"event": "attempt", "key": list(self.key), "ordinal": self._count + 1},
            )
            self._count += 1
            return self._count

    def reset(self):
        raise ValueError("persisted experiment request spending cannot be reset")


def _validate_record_binding(record, manifest, manifest_sha, registry_ids, corpus_ids):
    samples = {s["sample_id"]: s for s in manifest["samples"]}
    metadata = samples.get(record.sample_id)
    if metadata is None or (record.pair_id, record.view_type) != (
        metadata["pair_id"],
        metadata["view_type"],
    ):
        raise ValueError("resume sample metadata does not match manifest")
    expected_execution_mode = manifest.get("execution_mode", "mock_fixture")
    if record.execution_mode != expected_execution_mode:
        raise ValueError("record execution_mode does not match manifest")
    expected_run_id = manifest.get("run_id") or ("fixture-" + manifest_sha[:16])
    if record.run_id != expected_run_id:
        raise ValueError("record run_id does not match manifest")
    if expected_execution_mode == "live" and record.run_id.startswith("fixture-"):
        raise ValueError("live run cannot use fixture run_id")
    if expected_execution_mode == "mock_fixture" and not record.run_id.startswith("fixture-"):
        raise ValueError("mock run must use fixture run_id")
    expected = {
        "manifest_sha256": manifest_sha,
        "experiment_id": manifest["experiment_id"],
        "run_id": expected_run_id,
        "execution_mode": expected_execution_mode,
        "provider": manifest["model"]["provider"],
        "model": manifest["model"]["model"],
        "model_version": manifest["model_version"],
        "output_schema_sha256": manifest["output_schema_sha256"],
        "ground_truth_version": manifest["benchmark_version"],
        "attack_release": manifest["attack_release"],
    }
    for field, artifact in (
        ("prompt_sha256", "prompt"),
        ("model_config_sha256", "model_config"),
        ("dataset_sha256", "inference"),
        ("ground_truth_sha256", "ground_truth"),
        ("corpus_sha256", "corpus"),
        ("index_sha256", "index"),
    ):
        expected[field] = manifest["artifacts"][artifact]["sha256"]
    if any(getattr(record, key) != value for key, value in expected.items()):
        raise ValueError("resume record provenance does not match manifest")
    if record.parse_status in {"VALID", "INVALID_ID"}:
        _, status, _ = validate_technique_id(
            record.parsed_technique_ids[0], registry_ids=registry_ids
        )
        if status.value != record.parse_status:
            raise ValueError("record parse status disagrees with captured ATT&CK registry")
    if any(
        c.technique_id not in corpus_ids or c.technique_id not in registry_ids
        for c in record.retrieved_candidates
    ):
        raise ValueError("record candidate is absent from captured corpus/registry")
    if record.request_attempt_count > manifest["execution"]["retries"] + 1:
        raise ValueError("record exceeds bound retry policy")


def _resume_state(directory, manifest, manifest_sha, cap, registry_ids, corpus_ids):
    expected_files = {
        "manifest.json",
        "request_journal.jsonl",
        "run_summary.json",
        "run_summary.json.tmp",
        ".run.lock",
    }
    expected_files.update(f"{c}_predictions.jsonl" for c in CONDITIONS)
    if any(
        path.name not in expected_files or not path.is_file() or path.is_symlink()
        for path in directory.iterdir()
    ):
        raise ValueError("unexpected output-directory contents")
    if any(path.stat().st_nlink > 1 for path in directory.iterdir()):
        raise ValueError("hardlinked output-directory contents")
    records = {}
    for condition in CONDITIONS:
        path = directory / f"{condition}_predictions.jsonl"
        if not path.exists():
            continue
        for row in parse_jsonl(path.read_bytes()):
            record = ExperimentRecord.model_validate(row)
            _validate_record_binding(record, manifest, manifest_sha, registry_ids, corpus_ids)
            key = (record.sample_id, record.condition)
            if key in records or record.condition != condition:
                raise ValueError("duplicate sample-condition or wrong prediction file")
            records[key] = record
    journal = parse_jsonl((directory / "request_journal.jsonl").read_bytes())
    if journal[0] != {"event": "header", "manifest_sha256": manifest_sha, "max_requests": cap}:
        raise ValueError("journal manifest/budget drift")
    active = None
    active_state = None
    completed = set()
    consumed = 0
    start = 0
    matrix = {(s, c) for s in manifest["sample_ids"] for c in CONDITIONS}
    for event in journal[1:]:
        key = tuple(event.get("key", []))
        kind = event.get("event")
        if key not in matrix:
            raise ValueError("journal key outside experiment matrix")
        if kind == "begin" and set(event) == {"event", "key"}:
            if active is not None or key in completed:
                raise ValueError("duplicate or overlapping journal begin")
            active, start = key, consumed
            active_state = RequestState.DISPATCH_STARTED
        elif kind == "transition" and set(event) == {"event", "key", "state"}:
            state_val = event["state"]
            if state_val == RequestState.RESERVED.value:
                if active is not None or key in completed:
                    raise ValueError("duplicate or overlapping journal reservation")
                active, start = key, consumed
                active_state = RequestState.RESERVED
            else:
                if active != key:
                    raise ValueError("transition event for inactive request")
                if state_val == RequestState.DISPATCH_STARTED.value:
                    active_state = RequestState.DISPATCH_STARTED
                elif state_val == RequestState.RESPONSE_RECEIVED.value:
                    active_state = RequestState.RESPONSE_RECEIVED
                elif state_val == RequestState.PARSED.value:
                    active_state = RequestState.PARSED
                else:
                    raise ValueError(f"unknown transition state: {state_val}")
        elif kind == "attempt" and set(event) == {"event", "key", "ordinal"}:
            if (
                active != key
                or type(event["ordinal"]) is not int
                or event["ordinal"] != consumed + 1
            ):
                raise ValueError("invalid attempt journal")
            consumed += 1
        elif kind == "complete" and set(event) == {"event", "key", "record_sha256"}:
            record = records.get(key)
            if active != key or record is None or consumed == start:
                raise ValueError("completed journal lacks a valid execution")
            if (
                digest(canonical_bytes(record.model_dump())) != event["record_sha256"]
                or record.request_attempt_count != consumed - start
            ):
                raise ValueError("record/journal hash or request accounting mismatch")
            completed.add(key)
            active = None
            active_state = None
        else:
            raise ValueError("unknown or malformed journal event")
    if active is not None:
        if active_state == RequestState.RESERVED and consumed == start:
            active = None
            active_state = None
        else:
            raise ValueError("in-flight request state is ambiguous; human reconciliation required")
    if completed != set(records) or consumed > cap:
        raise ValueError("unjournaled prediction or request budget exceeded")
    return records, consumed


def _record(
    plan,
    manifest,
    manifest_sha,
    sample,
    condition,
    execution,
    retrieval,
    attempts,
    *,
    execution_mode="mock_fixture",
    run_id=None,
    raw_response_policy="DISCARD",
):
    actual_run_id = run_id or manifest.get("run_id") or ("fixture-" + manifest_sha[:16])
    raw_resp = None
    raw_logged = False
    if raw_response_policy == "RECORD_ONLY":
        raw_resp = getattr(execution, "raw_text", None)
        raw_logged = raw_resp is not None
    elif raw_response_policy == "LOG_SEPARATELY":
        raw_logged = True
        raw_resp = None
    else:  # DISCARD
        raw_resp = None
        raw_logged = False

    return ExperimentRecord(
        schema_version="1.0.0",
        execution_mode=execution_mode,
        experiment_id=manifest["experiment_id"],
        run_id=actual_run_id,
        manifest_sha256=manifest_sha,
        sample_id=sample.sample_id,
        pair_id=sample.pair_id,
        view_type=sample.view_type,
        condition=condition,
        retrieval_k=0 if retrieval is None else retrieval.k,
        provider=execution.provider,
        model=execution.model,
        model_version=manifest["model_version"],
        prompt_sha256=manifest["artifacts"]["prompt"]["sha256"],
        model_config_sha256=manifest["artifacts"]["model_config"]["sha256"],
        output_schema_sha256=manifest["output_schema_sha256"],
        dataset_sha256=manifest["artifacts"]["inference"]["sha256"],
        ground_truth_sha256=manifest["artifacts"]["ground_truth"]["sha256"],
        ground_truth_version=manifest["benchmark_version"],
        attack_release=manifest["attack_release"],
        corpus_sha256=manifest["artifacts"]["corpus"]["sha256"],
        index_sha256=manifest["artifacts"]["index"]["sha256"],
        retrieved_candidates=[]
        if retrieval is None
        else [
            {"technique_id": tid, "rank": rank, "score": score}
            for tid, rank, score in zip(
                retrieval.technique_ids, retrieval.ranks, retrieval.scores, strict=True
            )
        ],
        raw_response=raw_resp,
        raw_response_logged=raw_logged,
        parsed_technique_ids=[]
        if execution.predicted_technique_id is None
        else [execution.predicted_technique_id],
        parse_status=execution.parse_status,
        prompt_tokens=execution.input_tokens,
        completion_tokens=execution.output_tokens,
        total_tokens=None
        if execution.input_tokens is None or execution.output_tokens is None
        else execution.input_tokens + execution.output_tokens,
        latency_ms=execution.latency_ms,
        retry_count=execution.retry_count,
        request_attempt_count=attempts,
        error_type=execution.error_type,
        error_message=execution.invalid_reason,
        success=execution.is_valid,
        timestamp=datetime.now(UTC).isoformat(),
        terminal=True,
    )


def run_mock_experiment(
    plan: ValidatedPlan,
    directory: Path | str,
    provider: MockProvider,
    *,
    max_requests: int,
    resume: bool = False,
    stop_after: int | None = None,
):
    """Exercise real client/pipelines with a concrete in-memory fake in scratch space.

    max_requests is an explicit fixture budget, never approval of the draft's
    scientific budget. stop_after simulates clean interruption between records.
    """
    if type(provider) is not MockProvider:
        raise ValueError("only the concrete offline MockProvider is accepted")
    if type(max_requests) is not int or max_requests < len(plan.samples) * len(CONDITIONS):
        raise ValueError("fixture max_requests must cover the complete sample-condition matrix")
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive integer")
    if digest(canonical_bytes(plan.manifest)) != plan.manifest_sha256:
        raise ValueError("validated manifest was modified")
    for name, data in plan.snapshots.items():
        if digest(data) != plan.manifest["artifacts"][name]["sha256"]:
            raise ValueError("validated artifact snapshot was modified")
    snapshot_config = ExperimentConfig.model_validate(
        parse_json(plan.snapshots["experiment_config"])
    )
    snapshot_model = parse_json(plan.snapshots["model_config"])
    snapshot_prompt = plan.snapshots["prompt"].decode("utf-8")
    snapshot_registry = registry_ids_from_bytes(plan.snapshots["attack_registry"])
    corpus_ids = frozenset(row["technique_id"] for row in parse_jsonl(plan.snapshots["corpus"]))
    if (
        plan.config != snapshot_config
        or plan.model_config != snapshot_model
        or plan.prompt_template != snapshot_prompt
        or plan.registry_ids != snapshot_registry
        or plan.samples != _validate_dataset(snapshot_config, plan.snapshots)
    ):
        raise ValueError("derived execution inputs differ from validated artifact snapshots")
    directory = Path(directory).resolve()
    # Fake predictions must never appear in canonical scientific output/data paths.
    scratch_root = (plan.root / ".tmp").resolve()
    system_temp = Path(tempfile.gettempdir()).resolve()
    if not (directory.is_relative_to(scratch_root) or directory.is_relative_to(system_temp)):
        raise ValueError("mock outputs must remain under system temp or the validated root's .tmp")
    if directory.is_relative_to(plan.root) and not directory.is_relative_to(scratch_root):
        raise ValueError("mock outputs inside the input root must remain under .tmp")
    manifest = json.loads(canonical_bytes(plan.manifest))
    manifest["execution_mode"] = "mock_fixture"
    manifest["fixture_max_requests"] = max_requests
    manifest_sha = digest(canonical_bytes(manifest))
    existed = directory.exists()
    if existed and not resume:
        raise ValueError("output already exists; use explicit resume")
    if resume and not existed:
        raise ValueError("resume output does not exist")
    directory.mkdir(parents=True, exist_ok=True)
    with _exclusive_lock(directory):
        manifest_file = directory / "manifest.json"
        journal_file = directory / "request_journal.jsonl"
        if resume:
            if parse_json(manifest_file.read_bytes()) != manifest:
                raise ValueError("immutable manifest drift")
            records, spent = _resume_state(
                directory, manifest, manifest_sha, max_requests, snapshot_registry, corpus_ids
            )
        else:
            with manifest_file.open("xb") as stream:
                stream.write(canonical_bytes(manifest) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            _append(
                journal_file,
                {"event": "header", "manifest_sha256": manifest_sha, "max_requests": max_requests},
            )
            records, spent = {}, 0
        remaining_jobs = len(plan.samples) * len(CONDITIONS) - len(records)
        if max_requests - spent < remaining_jobs:
            raise ValueError("remaining explicit budget cannot cover unfinished matrix")
        if remaining_jobs == 0:
            summary = {
                "complete": True,
                "record_count": len(records),
                "requests_consumed": spent,
                "consumed_provider_attempts": spent,
                "new_records": 0,
                "execution_mode": "mock_fixture",
            }
            _write_summary(directory, summary)
            return summary
        budget = JournalBudget(max_requests, journal_file, consumed=spent)
        client = LLMClient(
            config_dict=snapshot_model,
            openai_client=provider,
            registry_ids=set(snapshot_registry),
            live_budget=budget,
            is_live=True,
            sleep_fn=lambda _: None,
        )
        import faiss
        import numpy as np

        retrieval_config = parse_json(plan.snapshots["retrieval_manifest"])
        retriever = FAISSRetriever(
            faiss.deserialize_index(np.frombuffer(plan.snapshots["index"], dtype=np.uint8)),
            parse_json(plan.snapshots["document_mapping"]),
            retrieval_config,
            StubEmbedder(plan.config.retrieval.embedding_dimension),
        )
        baseline = BaselinePipeline(client=client, prompt_template=snapshot_prompt)
        rag = RAGPipeline(client=client, retriever=retriever, prompt_template=snapshot_prompt)
        new_records = 0
        for sample in plan.samples:
            for condition in CONDITIONS:
                key = (sample.sample_id, condition)
                if key in records:
                    continue
                if budget.is_exhausted():
                    break
                _append(journal_file, {"event": "begin", "key": list(key)})
                budget.key = key
                provider.activate(key)
                before = budget.count
                if condition == "no_rag":
                    execution = baseline.run_sample(
                        sample.sample_id, sample.endpoint_evidence, retrieved_context=None
                    )
                    retrieval = None
                else:
                    result = rag.run_sample(
                        sample.sample_id, sample.endpoint_evidence, k=int(condition[5:])
                    )
                    execution, retrieval = result.execution, result.retrieval
                record = _record(
                    plan,
                    manifest,
                    manifest_sha,
                    sample,
                    condition,
                    execution,
                    retrieval,
                    budget.count - before,
                    execution_mode="mock_fixture",
                )
                _validate_record_binding(
                    record, manifest, manifest_sha, snapshot_registry, corpus_ids
                )
                _append(directory / f"{condition}_predictions.jsonl", record.model_dump())
                _append(
                    journal_file,
                    {
                        "event": "complete",
                        "key": list(key),
                        "record_sha256": digest(canonical_bytes(record.model_dump())),
                    },
                )
                budget.key = None
                records[key] = record
                new_records += 1
                if stop_after is not None and new_records == stop_after:
                    break
            if budget.is_exhausted() or (stop_after is not None and new_records == stop_after):
                break
        summary = {
            "complete": len(records) == len(plan.samples) * len(CONDITIONS),
            "record_count": len(records),
            "requests_consumed": budget.count,
            "consumed_provider_attempts": budget.count,
            "new_records": new_records,
            "execution_mode": "mock_fixture",
        }
        _write_summary(directory, summary)
        return summary


def _write_summary(directory, summary):
    """Rebuild derived summary atomically from the validated authoritative journal."""
    temp = directory / "run_summary.json.tmp"
    # A stale temp entry may be a hardlink. Remove only that directory entry so
    # writing the replacement cannot truncate a file outside the run directory.
    temp.unlink(missing_ok=True)
    with temp.open("xb") as stream:
        stream.write(canonical_bytes(summary) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(directory / "run_summary.json")


def run_live_experiment(
    plan: ValidatedPlan,
    directory: Path | str,
    authorization: ExecutionAuthorization | None = None,
    protocol: ScientificProtocolApproval | None = None,
    *,
    provider_factory: Callable[[dict[str, Any], LiveBudget], Any] | None = None,
    resume: bool = False,
    stop_after: int | None = None,
) -> dict[str, Any]:
    """Execute controlled live experiment with explicit authorization gates.

    DEFAULT IS DENY (LIVE_EXECUTION_BLOCKED).
    Requires explicit human authorization, hash-bound protocol approval (D1-D7),
    and verified pre-dispatch gates. Provider construction occurs strictly after gates pass.
    """
    # Gate 1-4: Pre-dispatch authorization & protocol validation
    validate_live_authorization(authorization, plan, protocol=protocol)
    assert authorization is not None

    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive integer")

    # Cryptographic plan & snapshot verification
    if digest(canonical_bytes(plan.manifest)) != plan.manifest_sha256:
        raise ValueError("validated manifest was modified")
    for name, data in plan.snapshots.items():
        if digest(data) != plan.manifest["artifacts"][name]["sha256"]:
            raise ValueError("validated artifact snapshot was modified")

    snapshot_config = ExperimentConfig.model_validate(
        parse_json(plan.snapshots["experiment_config"])
    )
    snapshot_model = parse_json(plan.snapshots["model_config"])
    snapshot_prompt = plan.snapshots["prompt"].decode("utf-8")
    snapshot_registry = registry_ids_from_bytes(plan.snapshots["attack_registry"])
    corpus_ids = frozenset(row["technique_id"] for row in parse_jsonl(plan.snapshots["corpus"]))

    if (
        plan.config != snapshot_config
        or plan.model_config != snapshot_model
        or plan.prompt_template != snapshot_prompt
        or plan.registry_ids != snapshot_registry
        or plan.samples != _validate_dataset(snapshot_config, plan.snapshots)
    ):
        raise ValueError("derived execution inputs differ from validated artifact snapshots")

    cap = (
        authorization.authorized_max_provider_attempts
        if authorization.authorized_max_provider_attempts is not None
        else authorization.authorized_max_requests
    )
    assert cap is not None

    directory = Path(directory).resolve()
    if directory.is_symlink():
        raise ValueError("symlink output directory rejected")

    if provider_factory is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            raise LiveExecutionBlockedError(
                "LIVE_EXECUTION_BLOCKED: OPENAI_API_KEY is not configured in environment"
            )

    existed = directory.exists()
    if existed and not resume:
        raise ValueError("output already exists; use explicit resume")
    if resume and not existed:
        raise ValueError("resume output does not exist")

    directory.mkdir(parents=True, exist_ok=True)

    with _exclusive_lock(directory):
        manifest_file = directory / "manifest.json"
        journal_file = directory / "request_journal.jsonl"

        if resume:
            manifest = parse_json(manifest_file.read_bytes())
            if manifest.get("execution_mode") != "live":
                raise ValueError("cannot resume mock run as live experiment")
            live_run_id = manifest["run_id"]
            if live_run_id.startswith("fixture-"):
                raise ValueError("live run cannot use fixture run_id")

            # Check protocol presence and integrity in stored manifest
            manifest_proto = manifest.get("protocol")
            manifest_proto_sha = manifest.get("protocol_sha256")
            if not manifest_proto or not manifest_proto_sha:
                raise ValueError("cannot resume live run without stored scientific protocol")
            if manifest_proto.get("protocol_sha256") != manifest_proto_sha:
                raise ValueError("manifest protocol SHA-256 mismatch; tampering detected")
            proto_decisions = {k: v for k, v in manifest_proto.items() if k != "protocol_sha256"}
            if compute_protocol_sha256(proto_decisions) != manifest_proto_sha:
                raise ValueError("manifest protocol content has been tampered with")

            # Block Protocol Drift: incoming protocol must match manifest protocol exactly
            if protocol is None:
                raise ValueError("cannot resume live run without incoming scientific protocol")
            if protocol.protocol_sha256 != manifest_proto_sha:
                raise ValueError(
                    "cannot resume run under a different scientific protocol; "
                    "provenance drift rejected"
                )
            if protocol_decision_dict(protocol) != proto_decisions:
                raise ValueError(
                    "cannot resume run under a different scientific protocol; "
                    "decision drift rejected"
                )

            manifest_sha = digest(canonical_bytes(manifest))
            records, spent = _resume_state(
                directory, manifest, manifest_sha, cap, snapshot_registry, corpus_ids
            )
        else:
            live_run_id = f"live-{uuid.uuid4().hex[:16]}"
            manifest = json.loads(canonical_bytes(plan.manifest))
            manifest["execution_mode"] = "live"
            manifest["run_id"] = live_run_id
            manifest["authorized_max_provider_attempts"] = cap
            manifest["fixture_max_requests"] = cap
            manifest["protocol"] = protocol_to_dict(protocol) if protocol else {}
            manifest["protocol_sha256"] = protocol.protocol_sha256 if protocol else None
            # Store only non-sensitive authorization reference (Defect 5)
            manifest["human_authorization_reference"] = digest(
                authorization.human_approval_token.encode("utf-8")
            )[:16]
            manifest_sha = digest(canonical_bytes(manifest))

            with manifest_file.open("xb") as stream:
                stream.write(canonical_bytes(manifest) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())

            _append(
                journal_file,
                {"event": "header", "manifest_sha256": manifest_sha, "max_requests": cap},
            )
            records, spent = {}, 0

        remaining_jobs = len(plan.samples) * len(CONDITIONS) - len(records)
        if cap - spent < remaining_jobs:
            raise ValueError("remaining explicit budget cannot cover unfinished matrix")

        if remaining_jobs == 0:
            summary = {
                "complete": True,
                "record_count": len(records),
                "requests_consumed": spent,
                "consumed_provider_attempts": spent,
                "new_records": 0,
                "execution_mode": "live",
                "run_id": live_run_id,
            }
            _write_summary(directory, summary)
            return summary

        # -------------------------------------------------------------------
        # PROVIDER CONSTRUCTION: Strictly AFTER all pre-dispatch gates pass.
        # -------------------------------------------------------------------
        budget = JournalBudget(cap, journal_file, consumed=spent)
        if provider_factory is not None:
            provider = provider_factory(snapshot_model, budget)
            client = LLMClient(
                config_dict=snapshot_model,
                openai_client=provider,
                registry_ids=set(snapshot_registry),
                live_budget=budget,
                is_live=True,
                sleep_fn=lambda _: None,
            )
        else:
            client = LLMClient(
                config_dict=snapshot_model,
                registry_ids=set(snapshot_registry),
                live_budget=budget,
                is_live=True,
                sleep_fn=lambda _: None,
                api_key=api_key,
            )
            provider = client.client

        import faiss
        import numpy as np

        retrieval_config = parse_json(plan.snapshots["retrieval_manifest"])
        retriever = FAISSRetriever(
            faiss.deserialize_index(np.frombuffer(plan.snapshots["index"], dtype=np.uint8)),
            parse_json(plan.snapshots["document_mapping"]),
            retrieval_config,
            StubEmbedder(plan.config.retrieval.embedding_dimension),
        )
        baseline = BaselinePipeline(client=client, prompt_template=snapshot_prompt)
        rag = RAGPipeline(client=client, retriever=retriever, prompt_template=snapshot_prompt)

        d1_policy = (
            protocol.d1_raw_response_policy
            if protocol
            else (authorization.d1_raw_response_policy_approved or "DISCARD")
        )

        new_records = 0
        for sample in plan.samples:
            for condition in CONDITIONS:
                key = (sample.sample_id, condition)
                if key in records:
                    continue
                if budget.is_exhausted():
                    break

                # 1. RESERVED: durable reservation
                _append(
                    journal_file,
                    {"event": "transition", "key": list(key), "state": "RESERVED"},
                )

                # 2. DISPATCH_STARTED: durable state before outbound call
                _append(
                    journal_file,
                    {"event": "transition", "key": list(key), "state": "DISPATCH_STARTED"},
                )

                budget.key = key
                if hasattr(provider, "activate"):
                    provider.activate(key)

                before = budget.count

                if condition == "no_rag":
                    execution = baseline.run_sample(
                        sample.sample_id, sample.endpoint_evidence, retrieved_context=None
                    )
                    retrieval = None
                else:
                    result = rag.run_sample(
                        sample.sample_id, sample.endpoint_evidence, k=int(condition[5:])
                    )
                    execution, retrieval = result.execution, result.retrieval

                # 3. RESPONSE_RECEIVED: provider returned
                _append(
                    journal_file,
                    {"event": "transition", "key": list(key), "state": "RESPONSE_RECEIVED"},
                )

                record = _record(
                    plan,
                    manifest,
                    manifest_sha,
                    sample,
                    condition,
                    execution,
                    retrieval,
                    budget.count - before,
                    execution_mode="live",
                    run_id=live_run_id,
                    raw_response_policy=d1_policy,
                )

                # 4. PARSED: parsed representation ready
                _append(
                    journal_file,
                    {"event": "transition", "key": list(key), "state": "PARSED"},
                )

                _validate_record_binding(
                    record, manifest, manifest_sha, snapshot_registry, corpus_ids
                )

                # 5. Persist record to prediction file
                _append(directory / f"{condition}_predictions.jsonl", record.model_dump())

                # 6. RECORD_COMMITTED: atomic commit event
                _append(
                    journal_file,
                    {
                        "event": "complete",
                        "key": list(key),
                        "record_sha256": digest(canonical_bytes(record.model_dump())),
                    },
                )

                budget.key = None
                records[key] = record
                new_records += 1

                if stop_after is not None and new_records == stop_after:
                    break

            if budget.is_exhausted() or (stop_after is not None and new_records == stop_after):
                break

        summary = {
            "complete": len(records) == len(plan.samples) * len(CONDITIONS),
            "record_count": len(records),
            "requests_consumed": budget.count,
            "consumed_provider_attempts": budget.count,
            "new_records": new_records,
            "execution_mode": "live",
            "run_id": live_run_id,
        }
        _write_summary(directory, summary)
        return summary
