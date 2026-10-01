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
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable

from src.baseline.pipeline import BaselinePipeline
from src.experiment.authorization import (
    REPO_ROOT,
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    ScientificProtocolApproval,
    compute_protocol_sha256,
    protocol_decision_dict,
    protocol_to_dict,
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
from src.experiment.journal import (
    EVENT_ATTEMPT_RECEIPT,
    EVENT_MONETARY_CANCEL_HOLD,
    EVENT_MONETARY_CANCEL_ORPHAN,
    EVENT_MONETARY_RESERVE,
    EVENT_MONETARY_SETTLE,
    EVENT_RESERVATION_ABANDONED,
    RequestState,
    make_reservation_abandoned_event,
    validate_attempt_event,
    validate_live_transition,
    validate_reservation_abandonment,
)
from src.experiment.monetary_ledger import (
    StudyBudgetLedger,
    calculate_request_cost_from_receipts,
    load_pricing_config,
    round_credit_down,
)
from src.experiment.path_safety import validate_untrusted_output_path
from src.experiment.redaction import sanitize_secrets
from src.experiment.schemas import CONDITIONS, ExperimentConfig, ExperimentRecord
from src.llm.client import LiveBudget, LiveBudgetExceededError, LLMClient
from src.llm.schemas import validate_technique_id
from src.rag.pipeline import RAGPipeline
from src.retrieval.retriever import (
    Embedder,
    FAISSRetriever,
    SentenceTransformerEmbedder,
    StubEmbedder,
)


@dataclass(frozen=True)
class MockReply:
    raw_text: str = '{"technique_id":"T1059.001"}'
    status: str = "completed"
    input_tokens: int | None = 10
    output_tokens: int | None = 1
    refusal: str | None = None
    service_tier: str | None = "default"
    model: str | None = "gpt-5.6-luna"
    response_id: str | None = None


class MockProvider:
    """A concrete in-memory fake, not a pluggable network-capable provider factory."""

    def __init__(self, outcomes=None):
        self.outcomes = outcomes or {}
        self.responses = self
        self.calls = []
        self.key = None
        self.attempt = 0

    @property
    def call_count(self) -> int:
        return len(self.calls)

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
            service_tier=getattr(outcome, "service_tier", "default"),
            model=getattr(outcome, "model", "gpt-5.6-luna"),
            id=getattr(outcome, "response_id", None),
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


def _verify_resume_manifest_consistency(manifest: dict[str, Any], plan: ValidatedPlan) -> None:
    """Fail closed if stored run manifest has drifted from current validated plan."""
    # 1. Code identity
    if manifest.get("git_commit_sha") != plan.manifest.get("git_commit_sha"):
        raise LiveExecutionBlockedError(
            f"cannot resume run: code identity drift (manifest {manifest.get('git_commit_sha')} "
            f"!= current {plan.manifest.get('git_commit_sha')})"
        )

    # 2. Config SHA
    if manifest.get("config_sha256") != plan.manifest.get("config_sha256"):
        raise LiveExecutionBlockedError(
            f"cannot resume run: config SHA-256 drift (manifest {manifest.get('config_sha256')} "
            f"!= current {plan.manifest.get('config_sha256')})"
        )

    # 3. Complete artifact hash map
    manifest_artifacts = manifest.get("artifacts", {})
    plan_artifacts = plan.manifest.get("artifacts", {})
    if set(manifest_artifacts) != set(plan_artifacts):
        raise LiveExecutionBlockedError("cannot resume run: artifact set drift")
    for name, plan_art in plan_artifacts.items():
        if manifest_artifacts.get(name, {}).get("sha256") != plan_art.get("sha256"):
            raise LiveExecutionBlockedError(f"cannot resume run: artifact '{name}' SHA-256 drift")

    # 4. Prompt, model, retrieval config
    if manifest.get("model") != plan.manifest.get("model"):
        raise LiveExecutionBlockedError("cannot resume run: model configuration drift")
    if manifest.get("retrieval") != plan.manifest.get("retrieval"):
        raise LiveExecutionBlockedError("cannot resume run: retrieval configuration drift")
    if manifest.get("model_version") != plan.manifest.get("model_version"):
        raise LiveExecutionBlockedError("cannot resume run: model version drift")

    # 5. Dataset, split, sample matrix
    if manifest.get("split") != plan.manifest.get("split"):
        raise LiveExecutionBlockedError("cannot resume run: dataset split drift")
    if manifest.get("benchmark_version") != plan.manifest.get("benchmark_version"):
        raise LiveExecutionBlockedError("cannot resume run: benchmark version drift")
    if manifest.get("attack_release") != plan.manifest.get("attack_release"):
        raise LiveExecutionBlockedError("cannot resume run: ATT&CK release drift")
    if manifest.get("sample_ids") != plan.manifest.get("sample_ids"):
        raise LiveExecutionBlockedError("cannot resume run: sample ID ordering or membership drift")
    if manifest.get("samples") != plan.manifest.get("samples"):
        raise LiveExecutionBlockedError("cannot resume run: sample metadata drift")
    if manifest.get("expected_request_count") != plan.manifest.get("expected_request_count"):
        raise LiveExecutionBlockedError("cannot resume run: expected request count drift")

    # 6. Retry, concurrency, budget semantics
    if manifest.get("execution") != plan.manifest.get("execution"):
        raise LiveExecutionBlockedError("cannot resume run: execution semantics drift")

    # 7. Conditions
    if manifest.get("conditions") != plan.manifest.get("conditions"):
        raise LiveExecutionBlockedError("cannot resume run: experiment conditions drift")

    # 8. Output schema
    if manifest.get("output_schema_sha256") != plan.manifest.get("output_schema_sha256"):
        raise LiveExecutionBlockedError("cannot resume run: output schema SHA-256 drift")


@dataclass
class ResumeState:
    """Encapsulates resumed journal state while maintaining 3-tuple unpack compatibility."""

    records: dict[tuple[str, str], ExperimentRecord]
    spent: int
    recoverable_reservation: tuple[str, str] | None
    orphan_reservation: tuple[tuple[str, str], Decimal] | None = None
    receipts_by_key: dict[tuple[str, str], list[dict[str, Any]]] | None = None
    settled_keys: set[tuple[str, str]] | None = None
    settled_events: dict[tuple[str, str], dict[str, Any]] | None = None
    completed_last_ordinal_by_key: dict[tuple[str, str], int] | None = None

    def __post_init__(self) -> None:
        if self.receipts_by_key is None:
            self.receipts_by_key = {}
        if self.settled_keys is None:
            self.settled_keys = set()
        if self.settled_events is None:
            self.settled_events = {}
        if self.completed_last_ordinal_by_key is None:
            self.completed_last_ordinal_by_key = {}

    def __iter__(self):
        yield self.records
        yield self.spent
        yield self.recoverable_reservation


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
    is_live = manifest.get("execution_mode") == "live"
    monetary_reserved_key = None
    monetary_reserved_amount = None
    receipts_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    settled_keys: set[tuple[str, str]] = set()
    settled_events: dict[tuple[str, str], dict[str, Any]] = {}
    completed_last_ordinal_by_key: dict[tuple[str, str], int] = {}

    for event in journal[1:]:
        key = tuple(event.get("key", []))
        kind = event.get("event")
        if key not in matrix:
            raise ValueError("journal key outside experiment matrix")
        if kind == EVENT_MONETARY_RESERVE:
            if not is_live:
                raise ValueError("monetary_reserve event only permitted in live execution")
            if active is not None or key in completed:
                raise ValueError("duplicate or overlapping journal monetary reserve")
            if monetary_reserved_key is not None:
                raise ValueError("prior monetary reserve was not closed")
            monetary_reserved_key = key
            monetary_reserved_amount = Decimal(str(event.get("amount_usd", "2.15898240")))
        elif kind == "begin" and set(event) == {"event", "key"}:
            if is_live:
                raise ValueError(
                    "legacy begin event is forbidden in live journal; "
                    "expected RESERVED transition"
                )
            if active is not None or key in completed:
                raise ValueError("duplicate or overlapping journal begin")
            active, start = key, consumed
            active_state = RequestState.DISPATCH_STARTED
        elif kind == "transition" and set(event) == {"event", "key", "state"}:
            state_val = event["state"]
            try:
                target_state = RequestState(state_val)
            except (ValueError, TypeError) as exc:
                raise ValueError(f"unknown transition state: {state_val}") from exc
            if target_state == RequestState.RESERVED:
                if active is not None or key in completed:
                    raise ValueError("duplicate or overlapping journal reservation")
                if is_live:
                    validate_live_transition(None, target_state, consumed, consumed)
                active, start = key, consumed
                active_state = RequestState.RESERVED
                if monetary_reserved_key is not None and monetary_reserved_key != key:
                    raise ValueError("monetary reserve key does not match RESERVED transition key")
            else:
                if active != key:
                    raise ValueError("transition event for inactive request")
                if is_live:
                    active_state = validate_live_transition(
                        active_state, target_state, consumed, start
                    )
                else:
                    active_state = target_state
        elif kind == "attempt" and set(event) == {"event", "key", "ordinal"}:
            if is_live:
                if active != key:
                    raise ValueError("invalid attempt journal")
                validate_attempt_event(
                    active_state, active, key, event["ordinal"], consumed + 1
                )
            else:
                if (
                    active != key
                    or type(event["ordinal"]) is not int
                    or event["ordinal"] != consumed + 1
                ):
                    raise ValueError("invalid attempt journal")
            consumed += 1
        elif kind == EVENT_ATTEMPT_RECEIPT:
            if not is_live:
                raise ValueError("attempt_receipt event only permitted in live execution")
            if active != key or active_state != RequestState.DISPATCH_STARTED:
                raise ValueError(
                    "attempt_receipt event only permitted during active DISPATCH_STARTED"
                )
            rec_ord = event.get("ordinal")
            rec_idx = event.get("attempt_index")
            if type(rec_ord) is not int or rec_ord != consumed:
                raise ValueError(
                    f"attempt_receipt ordinal {rec_ord} does not match journal consumed {consumed}"
                )
            expected_idx = consumed - start - 1
            if type(rec_idx) is not int or rec_idx != expected_idx:
                raise ValueError(
                    f"attempt_receipt attempt_index {rec_idx} does not match "
                    f"expected {expected_idx}"
                )
            key_receipts = receipts_by_key.setdefault(key, [])
            if any(
                r.get("ordinal") == rec_ord or r.get("attempt_index") == rec_idx
                for r in key_receipts
            ):
                raise ValueError(f"duplicate attempt_receipt for key {key} in journal")
            key_receipts.append(event)
        elif kind == EVENT_RESERVATION_ABANDONED and set(event) == {"event", "key"}:
            if not is_live:
                raise ValueError("reservation_abandoned event only permitted in live execution")
            validate_reservation_abandonment(active_state, active, event["key"], consumed, start)
            active = None
            active_state = None
            monetary_reserved_key = None
            monetary_reserved_amount = None
        elif kind == EVENT_MONETARY_CANCEL_ORPHAN:
            if not is_live:
                raise ValueError("monetary_cancel_orphan event only permitted in live execution")
            if active is not None:
                raise ValueError("monetary_cancel_orphan not permitted while request is active")
            if monetary_reserved_key != key:
                raise ValueError("monetary_cancel_orphan key mismatch with open reserve")
            monetary_reserved_key = None
            monetary_reserved_amount = None
        elif kind == EVENT_MONETARY_CANCEL_HOLD:
            if not is_live:
                raise ValueError("monetary_cancel_hold event only permitted in live execution")
            monetary_reserved_key = None
            monetary_reserved_amount = None
        elif kind == "complete" and set(event) == {"event", "key", "record_sha256"}:
            if active != key:
                raise ValueError("completed journal lacks a valid execution")
            if is_live:
                validate_live_transition(
                    active_state, RequestState.RECORD_COMMITTED, consumed, start
                )
            record = records.get(key)
            if record is None or consumed == start:
                raise ValueError("completed journal lacks a valid execution")
            if (
                digest(canonical_bytes(record.model_dump())) != event["record_sha256"]
                or record.request_attempt_count != consumed - start
            ):
                raise ValueError("record/journal hash or request accounting mismatch")
            completed.add(key)
            completed_last_ordinal_by_key[key] = consumed
            active = None
            active_state = None
            monetary_reserved_key = None
            monetary_reserved_amount = None
        elif kind == EVENT_MONETARY_SETTLE:
            if not is_live:
                raise ValueError("monetary_settle event only permitted in live execution")
            if key not in completed:
                raise ValueError("monetary_settle event for uncommitted request")
            if key in settled_keys:
                raise ValueError(f"duplicate monetary_settle event for {key}")
            settled_keys.add(key)
            settled_events[key] = event
        else:
            raise ValueError("unknown or malformed journal event")

    orphan_reservation = None
    if monetary_reserved_key is not None and active_state is None:
        orphan_reservation = (monetary_reserved_key, monetary_reserved_amount)
        monetary_reserved_key = None

    recoverable_reservation = None
    if active is not None:
        if active_state == RequestState.RESERVED and consumed == start:
            recoverable_reservation = active
            active = None
            active_state = None
        else:
            raise ValueError("in-flight request state is ambiguous; human reconciliation required")
    if completed != set(records) or consumed > cap:
        raise ValueError("unjournaled prediction or request budget exceeded")

    return ResumeState(
        records=records,
        spent=consumed,
        recoverable_reservation=recoverable_reservation,
        orphan_reservation=orphan_reservation,
        receipts_by_key=receipts_by_key,
        settled_keys=settled_keys,
        settled_events=settled_events,
        completed_last_ordinal_by_key=completed_last_ordinal_by_key,
    )


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
    extra_tokens=(),
):
    actual_run_id = run_id or manifest.get("run_id") or ("fixture-" + manifest_sha[:16])
    raw_resp = None
    raw_logged = False
    if raw_response_policy == "RECORD_ONLY":
        raw_resp = getattr(execution, "raw_text", None)
        if raw_resp is not None:
            raw_resp = sanitize_secrets(raw_resp, extra_tokens=extra_tokens)
        raw_logged = raw_resp is not None
    elif raw_response_policy == "LOG_SEPARATELY":
        raise ValueError("LOG_SEPARATELY raw-response storage is not implemented")
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
        returned_model_id=getattr(execution, "returned_model_id", None),
        response_id=getattr(execution, "response_id", None),
        system_fingerprint=getattr(execution, "system_fingerprint", None),
        request_timestamp_utc=getattr(execution, "request_timestamp_utc", None),
        response_timestamp_utc=getattr(execution, "response_timestamp_utc", None),
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
        error_message=sanitize_secrets(execution.invalid_reason, extra_tokens=extra_tokens),
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
    directory = validate_untrusted_output_path(directory)
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
            records, spent, _ = _resume_state(
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
    allow_dirty: bool = False,
    embedder: Embedder | None = None,
) -> dict[str, Any]:
    """Execute controlled live experiment with explicit authorization gates.

    DEFAULT IS DENY (LIVE_EXECUTION_BLOCKED).
    Requires explicit human authorization, hash-bound protocol approval (D1-D7),
    and verified pre-dispatch gates. Provider construction occurs strictly after gates pass.
    """
    # Production live execution strictly forbids any caller embedder override.
    # Rejection occurs immediately before key/env/filesystem operations.
    if provider_factory is None and embedder is not None:
        raise ValueError(
            "embedder override is forbidden in production live execution; "
            "production must instantiate pinned real SentenceTransformerEmbedder"
        )

    # Pre-dispatch authorization & readiness validation (BLOCKER-2)
    plan_in_repo = False
    try:
        plan_in_repo = hasattr(plan, "root") and plan.root.resolve() == REPO_ROOT.resolve()
    except Exception:
        plan_in_repo = False
    is_test = plan.manifest.get("split") == "test"
    is_canonical = is_test and (
        len(getattr(plan, "samples", [])) == 1280
        or plan_in_repo
    )
    effective_allow_dirty = False if is_canonical else allow_dirty

    from src.experiment.authorization import validate_experiment_readiness

    validate_experiment_readiness(
        plan=plan,
        protocol=protocol,
        authorization=authorization,
        output_dir=directory,
        allow_dirty=effective_allow_dirty,
        is_live=True,
        is_resume=resume,
    )
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

    directory = validate_untrusted_output_path(directory)

    api_key = None
    if provider_factory is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key or not api_key.strip():
            raise LiveExecutionBlockedError(
                "LIVE_EXECUTION_BLOCKED: OPENAI_API_KEY is not configured in environment"
            )

    use_guard = (provider_factory is None) or getattr(authorization, "use_money_guard", False)
    study_ledger = None
    pricing_config = None
    R_logical_worst = Decimal("2.15898240")
    if use_guard:
        if (
            provider_factory is None
            and getattr(authorization, "study_ledger_path", None) is not None
        ):
            raise LiveExecutionBlockedError(
                "LIVE_EXECUTION_BLOCKED: Custom study_ledger_path is not permitted "
                "in canonical production execution"
            )
        if (
            provider_factory is None
            and getattr(authorization, "study_anchor_path", None) is not None
        ):
            raise LiveExecutionBlockedError(
                "LIVE_EXECUTION_BLOCKED: Custom study_anchor_path is not permitted "
                "in canonical production execution"
            )
        target_code_root = getattr(plan, "root", None) or REPO_ROOT
        pricing_config, _ = load_pricing_config(repo_root=target_code_root)
        R_logical_worst = Decimal(
            str(
                pricing_config.get("reservation_bounds", {}).get(
                    "default_logical_worst_usd", "2.15898240"
                )
            )
        )
        ledger_path = getattr(authorization, "study_ledger_path", None)
        anchor_path = getattr(authorization, "study_anchor_path", None)
        study_ledger = StudyBudgetLedger(
            ledger_path=ledger_path,
            anchor_path=anchor_path,
            pricing_config=pricing_config,
            code_root=target_code_root,
            output_directory=directory,
            experiment_id=plan.manifest["experiment_id"],
        )

    if use_guard and study_ledger is not None:
        if not resume and study_ledger.is_already_initialized:
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Study has already been initialized (anchor at "
                f"{study_ledger.anchor_path}); new output directory '{directory}' "
                f"cannot start fresh un-resumed execution without explicit authorized reset."
            )
        if resume and getattr(study_ledger, "output_dir_mismatch", False):
            raise LiveExecutionBlockedError(
                f"LIVE_EXECUTION_BLOCKED: Output directory '{directory}' does not match "
                f"study anchor recorded directory."
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

            # Check complete run manifest consistency against current validated plan
            _verify_resume_manifest_consistency(manifest, plan)

            manifest_sha = digest(canonical_bytes(manifest))
            resume_state = _resume_state(
                directory, manifest, manifest_sha, cap, snapshot_registry, corpus_ids
            )
            records = resume_state.records
            spent = resume_state.spent
            recoverable_reservation = resume_state.recoverable_reservation
            orphan_reservation = resume_state.orphan_reservation

            if use_guard and study_ledger is not None:
                if study_ledger.has_breach:
                    raise LiveExecutionBlockedError(
                        "LIVE_EXECUTION_BLOCKED: Study ledger has prior breach; "
                        "resume dispatch permanently blocked"
                    )
                # 1. Recovery and verification for all completed records
                for comp_key, comp_rec in records.items():
                    comp_key_str = f"{comp_key[0]}:{comp_key[1]}"
                    comp_receipts = resume_state.receipts_by_key.get(comp_key, [])
                    cost, breach, breach_reason = calculate_request_cost_from_receipts(
                        attempts_consumed=comp_rec.request_attempt_count,
                        receipts=comp_receipts,
                        record=comp_rec,
                        pricing_config=pricing_config,
                        tier="default",
                        expected_model=manifest["model"]["model"],
                        most_recent_attempt_ordinal=(
                            resume_state.completed_last_ordinal_by_key.get(comp_key)
                        ),
                    )
                    if breach:
                        raise LiveExecutionBlockedError(
                            f"LIVE_EXECUTION_BLOCKED: monetary receipt breach on recovery "
                            f"for {comp_key_str}: {breach_reason}"
                        )
                    rec_sha = digest(canonical_bytes(comp_rec.model_dump()))
                    expected_refund = round_credit_down(R_logical_worst - cost)

                    if comp_key in resume_state.settled_keys:
                        # Verify consistency of already settled journal event
                        j_event = resume_state.settled_events.get(comp_key)
                        if j_event is not None:
                            if (
                                Decimal(str(j_event.get("cost_usd"))) != cost
                                or Decimal(str(j_event.get("refund_usd"))) != expected_refund
                                or j_event.get("record_sha256") != rec_sha
                                or j_event.get("breach", False)
                            ):
                                raise LiveExecutionBlockedError(
                                    f"LIVE_EXECUTION_BLOCKED: settled journal record drift "
                                    f"or breach for {comp_key_str}"
                                )
                        # Enforce complete settled join with study ledger
                        led_entry = study_ledger.settled_records.get(comp_key_str)
                        if led_entry is None:
                            raise LiveExecutionBlockedError(
                                f"LIVE_EXECUTION_BLOCKED: settled record {comp_key_str} in journal "
                                f"is missing from study ledger; rolled-back, missing, or archived "
                                f"ledger history rejected"
                            )
                        if (
                            Decimal(str(led_entry.get("cost_usd"))) != cost
                            or Decimal(str(led_entry.get("refund_usd"))) != expected_refund
                            or led_entry.get("record_sha256") != rec_sha
                            or led_entry.get("breach", False)
                        ):
                            raise LiveExecutionBlockedError(
                                f"LIVE_EXECUTION_BLOCKED: settled ledger record drift "
                                f"or breach for {comp_key_str}"
                            )
                    else:
                        # Complete-without-settle recovery
                        led_entry = study_ledger.settled_records.get(comp_key_str)
                        if led_entry is not None:
                            if (
                                Decimal(str(led_entry.get("cost_usd"))) != cost
                                or Decimal(str(led_entry.get("refund_usd"))) != expected_refund
                                or led_entry.get("record_sha256") != rec_sha
                                or led_entry.get("breach", False)
                            ):
                                raise LiveExecutionBlockedError(
                                    f"LIVE_EXECUTION_BLOCKED: complete-without-settle record "
                                    f"{comp_key_str} conflicts with existing ledger settlement"
                                )
                            refund = Decimal(str(led_entry.get("refund_usd")))
                        else:
                            refund = study_ledger.settle(
                                key_str=comp_key_str,
                                cost_usd=cost,
                                reserved_amount_usd=R_logical_worst,
                                record_sha256=rec_sha,
                            )
                        _append(
                            journal_file,
                            {
                                "event": EVENT_MONETARY_SETTLE,
                                "key": list(comp_key),
                                "cost_usd": str(cost),
                                "refund_usd": str(refund),
                                "record_sha256": rec_sha,
                                "breach": False,
                            },
                        )
                        resume_state.settled_keys.add(comp_key)

                # 2. Orphan reservation crash before RESERVED
                if orphan_reservation is not None:
                    orph_key, orph_amt = orphan_reservation
                    orph_key_str = f"{orph_key[0]}:{orph_key[1]}"
                    study_ledger.cancel_orphan_hold(orph_key_str, orph_amt)
                    _append(
                        journal_file,
                        {
                            "event": EVENT_MONETARY_CANCEL_ORPHAN,
                            "key": list(orph_key),
                            "amount_usd": str(orph_amt),
                        },
                    )

                # 3. Recoverable reservation crash in RESERVED before dispatch
                if recoverable_reservation is not None:
                    _append(
                        journal_file,
                        make_reservation_abandoned_event(recoverable_reservation),
                    )
                    rec_key_str = f"{recoverable_reservation[0]}:{recoverable_reservation[1]}"
                    study_ledger.cancel_orphan_hold(rec_key_str, R_logical_worst)
                    _append(
                        journal_file,
                        {
                            "event": EVENT_MONETARY_CANCEL_HOLD,
                            "key": list(recoverable_reservation),
                            "amount_usd": str(R_logical_worst),
                        },
                    )
            elif recoverable_reservation is not None:
                _append(
                    journal_file,
                    make_reservation_abandoned_event(recoverable_reservation),
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
            if use_guard and study_ledger is not None:
                summary["study_budget"] = study_ledger.get_summary()
            _write_summary(directory, summary)
            return summary

        sensitive_tokens: list[str] = []
        if api_key:
            sensitive_tokens.append(api_key)
        if authorization and authorization.human_approval_token:
            sensitive_tokens.append(authorization.human_approval_token)
        for env_name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "CUSTOM_SECRET_KEY"):
            val = os.environ.get(env_name)
            if val and len(val.strip()) >= 4:
                sensitive_tokens.append(val.strip())

        # -------------------------------------------------------------------
        # RETRIEVAL CONSTRUCTION & VALIDATION: Strictly BEFORE provider construction.
        # Initialization failure must yield zero provider construction/calls.
        # -------------------------------------------------------------------
        import faiss
        import numpy as np

        retrieval_manifest = parse_json(plan.snapshots["retrieval_manifest"])
        expected_model_id = plan.config.retrieval.embedding_model
        expected_revision = plan.config.retrieval.embedding_revision
        expected_dimension = plan.config.retrieval.embedding_dimension

        manifest_model_id = retrieval_manifest.get("embedding_model_id")
        manifest_revision = retrieval_manifest.get("embedding_model_revision")
        manifest_dimension = retrieval_manifest.get("embedding_dimension")

        if manifest_model_id != expected_model_id:
            raise ValueError(
                f"retrieval manifest model_id mismatch: expected '{expected_model_id}', "
                f"got '{manifest_model_id}'"
            )
        if manifest_revision != expected_revision:
            raise ValueError(
                f"retrieval manifest revision mismatch: expected '{expected_revision}', "
                f"got '{manifest_revision}'"
            )
        if manifest_dimension != expected_dimension:
            raise ValueError(
                f"retrieval manifest dimension mismatch: expected {expected_dimension}, "
                f"got {manifest_dimension}"
            )

        if provider_factory is None and embedder is not None:
            raise ValueError(
                "embedder override is forbidden in production live execution; "
                "production must instantiate pinned real SentenceTransformerEmbedder"
            )

        if embedder is None:
            # Canonical live retrieval always instantiates pinned real SentenceTransformerEmbedder
            embedder = SentenceTransformerEmbedder(
                model_id=expected_model_id,
                revision=expected_revision,
            )

        docmap = parse_json(plan.snapshots["document_mapping"])
        raw_index = faiss.deserialize_index(np.frombuffer(plan.snapshots["index"], dtype=np.uint8))

        if raw_index.d != expected_dimension:
            raise ValueError(
                f"FAISS index dimension ({raw_index.d}) mismatch with "
                f"expected dimension ({expected_dimension})"
            )
        if len(docmap) != raw_index.ntotal:
            raise ValueError(
                f"Document mapping count ({len(docmap)}) mismatch with "
                f"FAISS index total ({raw_index.ntotal})"
            )

        # Pre-provider probe: validate embedder capability, shape, and numerical validity
        # strictly BEFORE provider construction/dispatch. Catches broken embedders before
        # any condition (including condition='no_rag') is executed.
        try:
            probe_vec = embedder.encode(["attribution canary probe"])
        except Exception as exc:
            raise ValueError(f"embedder probe failed during encoding: {exc}") from exc

        if not hasattr(probe_vec, "shape") or probe_vec.shape != (1, expected_dimension):
            actual_shape = getattr(probe_vec, "shape", None)
            raise ValueError(
                f"embedder probe produced invalid shape {actual_shape}; "
                f"expected (1, {expected_dimension})"
            )
        if not np.isfinite(probe_vec).all():
            raise ValueError("embedder probe produced non-finite values (NaN/Inf)")

        retriever = FAISSRetriever(
            index=raw_index,
            document_mapping=docmap,
            config=retrieval_manifest,
            embedder=embedder,
        )

        # -------------------------------------------------------------------
        # PROVIDER CONSTRUCTION: Strictly AFTER all pre-dispatch gates pass.
        # -------------------------------------------------------------------
        current_attempt_receipts: list[dict[str, Any]] = []

        def _on_attempt(receipt_data: dict[str, Any]) -> None:
            nonlocal current_attempt_receipts
            receipt = {
                "event": EVENT_ATTEMPT_RECEIPT,
                "key": list(budget.key) if budget.key else [],
                "ordinal": budget.count,
                **receipt_data,
            }
            _append(journal_file, receipt)
            current_attempt_receipts.append(receipt)

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
                extra_secrets=sensitive_tokens,
                service_tier="default" if use_guard else None,
                attempt_callback=_on_attempt if use_guard else None,
            )
        else:
            client = LLMClient(
                config_dict=snapshot_model,
                registry_ids=set(snapshot_registry),
                live_budget=budget,
                is_live=True,
                api_key=api_key,
                extra_secrets=sensitive_tokens,
                service_tier="default" if use_guard else None,
                attempt_callback=_on_attempt if use_guard else None,
            )
            provider = client.client

        baseline = BaselinePipeline(client=client, prompt_template=snapshot_prompt)
        rag = RAGPipeline(client=client, retriever=retriever, prompt_template=snapshot_prompt)

        d1_policy = (
            protocol.d1_raw_response_policy
            if protocol
            else (authorization.d1_raw_response_policy_approved or "DISCARD")
        )

        new_records = 0
        stopped_reason: str | None = None
        for sample in plan.samples:
            for condition in CONDITIONS:
                key = (sample.sample_id, condition)
                key_str = f"{sample.sample_id}:{condition}"
                if key in records:
                    continue
                if budget.is_exhausted():
                    break

                if use_guard and study_ledger is not None:
                    # Clean USD exhaustion check BEFORE reservation:
                    # No extra attempt on refused reserve
                    if study_ledger.uncommitted_available_balance_usd < R_logical_worst:
                        stopped_reason = "USD_BUDGET_LIMIT"
                        break
                    try:
                        study_ledger.reserve(key_str, R_logical_worst)
                    except LiveExecutionBlockedError as exc:
                        if "Insufficient study budget" in str(exc):
                            stopped_reason = "USD_BUDGET_LIMIT"
                            break
                        raise
                    _append(
                        journal_file,
                        {
                            "event": EVENT_MONETARY_RESERVE,
                            "key": list(key),
                            "amount_usd": str(R_logical_worst),
                        },
                    )

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
                current_attempt_receipts.clear()

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
                    extra_tokens=sensitive_tokens,
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
                rec_sha = digest(canonical_bytes(record.model_dump()))
                _append(
                    journal_file,
                    {
                        "event": "complete",
                        "key": list(key),
                        "record_sha256": rec_sha,
                    },
                )

                # 7. Settle monetary transaction
                if use_guard and study_ledger is not None:
                    attempts_consumed = budget.count - before
                    cost, breach, breach_reason = calculate_request_cost_from_receipts(
                        attempts_consumed=attempts_consumed,
                        receipts=current_attempt_receipts,
                        record=record,
                        pricing_config=pricing_config,
                        tier="default",
                        expected_model=manifest["model"]["model"],
                        most_recent_attempt_ordinal=budget.count,
                    )
                    refund = study_ledger.settle(
                        key_str=key_str,
                        cost_usd=cost,
                        reserved_amount_usd=R_logical_worst,
                        record_sha256=rec_sha,
                        breach=breach,
                        breach_reason=breach_reason,
                    )
                    _append(
                        journal_file,
                        {
                            "event": EVENT_MONETARY_SETTLE,
                            "key": list(key),
                            "cost_usd": str(cost),
                            "refund_usd": str(refund),
                            "record_sha256": rec_sha,
                            "breach": breach,
                            "breach_reason": breach_reason,
                        },
                    )
                    if breach:
                        summary = {
                            "complete": False,
                            "stopped_reason": "METADATA_BREACH",
                            "has_breach": True,
                            "record_count": len(records) + 1,
                            "requests_consumed": budget.count,
                            "consumed_provider_attempts": budget.count,
                            "new_records": new_records + 1,
                            "execution_mode": "live",
                            "run_id": live_run_id,
                            "study_budget": study_ledger.get_summary(),
                        }
                        _write_summary(directory, summary)
                        raise LiveExecutionBlockedError(
                            f"LIVE_EXECUTION_BLOCKED: Receipt ceiling or metadata breach: "
                            f"{breach_reason}. Attempt held worst-case charge ${cost}. "
                            f"Next dispatch blocked."
                        )

                budget.key = None
                records[key] = record
                new_records += 1

                if stop_after is not None and new_records == stop_after:
                    break

            if (
                budget.is_exhausted()
                or (stop_after is not None and new_records == stop_after)
                or (stopped_reason is not None)
            ):
                break

        summary = {
            "complete": (
                (len(records) == len(plan.samples) * len(CONDITIONS))
                and (stopped_reason is None)
            ),
            "record_count": len(records),
            "requests_consumed": budget.count,
            "consumed_provider_attempts": budget.count,
            "new_records": new_records,
            "execution_mode": "live",
            "run_id": live_run_id,
        }
        if stopped_reason is not None:
            summary["stopped_reason"] = stopped_reason
        if use_guard and study_ledger is not None:
            summary["study_budget"] = study_ledger.get_summary()
        _write_summary(directory, summary)
        return summary
