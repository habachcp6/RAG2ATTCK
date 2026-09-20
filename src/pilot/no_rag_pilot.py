"""Bounded No-RAG pilot infrastructure.

The runner is intentionally provenance-first. It refuses to treat the
repository's synthetic benchmark or engineering smoke cases as real telemetry.
When a legitimate sanitized source is supplied later, the same runner can
execute it through the frozen ``BaselinePipeline`` with ``condition=no_rag``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter
from collections.abc import Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import openai

from src.llm.client import LiveBudgetExceededError


class OperationalProviderError(Exception):
    """Operational or provider failure during live pilot execution."""


OPERATIONAL_EXCEPTIONS: tuple[type[Exception], ...] = (
    LiveBudgetExceededError,
    openai.APIError,
    TimeoutError,
    ConnectionError,
    OperationalProviderError,
)


MAX_PILOT_SAMPLES = 20
REQUIRED_SOURCE_FIELDS = (
    "dataset_id",
    "source_id",
    "source_reference",
    "license",
    "version",
    "acquisition_date",
    "schema",
    "sanitization_status",
    "is_real_data",
    "input_sha256",
    "expected_record_count",
)
VALID_STATUSES = (
    "VALID",
    "INVALID_ID",
    "MALFORMED_RESPONSE",
    "REFUSAL",
    "INCOMPLETE",
    "API_FAILURE",
    "TIMEOUT",
)
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


class PilotPipeline(Protocol):
    def run_sample(
        self,
        sample_id: str,
        endpoint_evidence: str,
        retrieved_context: None = None,
        condition: str = "no_rag",
    ) -> Any:
        ...


@dataclass(frozen=True)
class PilotSample:
    sample_id: str
    source_id: str
    endpoint_evidence: str


@dataclass(frozen=True)
class PilotRun:
    records: list[dict[str, Any]]
    requested_samples: int
    processed_samples: int
    complete: bool
    budget_exhausted: bool


class DataUnavailableError(RuntimeError):
    """Raised when no approved real-data source is available."""


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected a JSON object")
            rows.append(value)
    return rows


def _sha256_file(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_pilot_limit(limit: int) -> None:
    if type(limit) is not int or not 1 <= limit <= MAX_PILOT_SAMPLES:
        raise ValueError(f"limit must be an integer from 1 to {MAX_PILOT_SAMPLES}")


def validate_live_budget(max_requests: int, sample_limit: int, max_retries: int) -> None:
    validate_pilot_limit(sample_limit)
    if type(max_requests) is not int or max_requests <= 0:
        raise ValueError("max_live_requests must be a finite positive integer")
    if type(max_retries) is not int or max_retries < 0:
        raise ValueError("max_retries must be a non-negative integer")
    theoretical_max = sample_limit * (max_retries + 1)
    if max_requests > theoretical_max:
        raise ValueError(
            f"max_live_requests={max_requests} exceeds the pilot envelope "
            f"of {theoretical_max} attempts"
        )


def validate_source_manifest(
    manifest: Mapping[str, Any],
    *,
    input_path: Path | str | None = None,
    approved_source_ids: Collection[str] = (),
) -> None:
    """Validate source identity, exact input bytes and record count before dispatch."""

    missing = [
        field
        for field in REQUIRED_SOURCE_FIELDS
        if field not in manifest or (field != "is_real_data" and not manifest[field])
    ]
    if missing:
        raise ValueError(f"source manifest missing required fields: {', '.join(missing)}")
    if manifest.get("is_real_data") is not True:
        raise DataUnavailableError("source manifest does not declare is_real_data=true")
    status = str(manifest["sanitization_status"]).lower()
    if status not in {"sanitized", "fully_sanitized", "anonymized"}:
        raise DataUnavailableError(
            "source manifest must declare a recognized sanitization_status "
            "(sanitized, fully_sanitized, or anonymized)"
        )
    source_id = manifest["source_id"]
    if not isinstance(source_id, str) or source_id not in set(approved_source_ids):
        raise DataUnavailableError(f"source_id {source_id!r} is not in the approved source allowlist")
    if not isinstance(manifest["input_sha256"], str) or not _SHA256_RE.fullmatch(manifest["input_sha256"]):
        raise ValueError("input_sha256 must be exactly 64 hexadecimal characters")
    expected_count = manifest["expected_record_count"]
    if type(expected_count) is not int or expected_count < 1:
        raise ValueError("expected_record_count must be a positive integer")

    if input_path is not None:
        source_path = Path(input_path)
        if not source_path.is_file():
            raise DataUnavailableError(f"approved input is missing: {source_path}")
        actual_hash = _sha256_file(source_path)
        if actual_hash.lower() != manifest["input_sha256"].lower():
            raise DataUnavailableError(
                f"source input SHA-256 mismatch: expected {manifest['input_sha256']}, got {actual_hash}"
            )
        actual_count = len(load_jsonl(source_path))
        if actual_count != expected_count:
            raise DataUnavailableError(
                f"source record count mismatch: expected {expected_count}, got {actual_count}"
            )


def load_pilot_samples(
    path: Path | str,
    limit: int = MAX_PILOT_SAMPLES,
    *,
    expected_source_id: str | None = None,
) -> list[PilotSample]:
    validate_pilot_limit(limit)
    rows = load_jsonl(path)
    samples: list[PilotSample] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        sample_id = row.get("sample_id")
        evidence = row.get("endpoint_evidence")
        source_id = row.get("source_id", "")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError(f"sample index {index}: invalid sample_id")
        normalized_id = sample_id.strip()
        if normalized_id in seen:
            raise ValueError(f"Duplicate sample_id {normalized_id!r}")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"sample index {index}: endpoint_evidence is required")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"sample index {index}: source_id is required")
        normalized_source_id = source_id.strip()
        if expected_source_id is not None and normalized_source_id != expected_source_id:
            raise ValueError(
                f"sample index {index}: source_id {normalized_source_id!r} "
                f"does not match manifest source_id {expected_source_id!r}"
            )
        seen.add(normalized_id)
        samples.append(PilotSample(normalized_id, normalized_source_id, evidence))
        if len(samples) >= limit:
            break
    if not samples:
        raise ValueError("pilot input contains no samples")
    return samples


def prepare_pilot_inputs(
    input_path: Path | str,
    source_manifest_path: Path | str,
    limit: int,
    approved_source_ids: Collection[str],
) -> tuple[dict[str, Any], list[PilotSample]]:
    manifest_path = Path(source_manifest_path)
    input_file = Path(input_path)
    if not manifest_path.is_file() or not input_file.is_file():
        raise DataUnavailableError("DATA_UNAVAILABLE: approved input or source manifest is missing")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("source manifest must be a JSON object")
    validate_source_manifest(manifest, input_path=input_file, approved_source_ids=approved_source_ids)
    samples = load_pilot_samples(input_file, limit, expected_source_id=manifest["source_id"])
    return manifest, samples


def _record_to_dict(sample: PilotSample, record: Any) -> dict[str, Any]:
    parse_status = getattr(record, "parse_status", None)
    if hasattr(parse_status, "value"):
        parse_status = parse_status.value
    invalid_reason = getattr(record, "invalid_reason", None)
    error_type = getattr(record, "error_type", None)
    return {
        "sample_id": sample.sample_id,
        "source_id": sample.source_id,
        "condition": getattr(record, "condition", "no_rag"),
        "provider": getattr(record, "provider", None),
        "model": getattr(record, "model", None),
        "reasoning_effort": getattr(record, "reasoning_effort", None),
        "prompt_version": getattr(record, "prompt_version", None),
        "prediction": {"technique_id": getattr(record, "predicted_technique_id", None)},
        "valid_attack_id": bool(getattr(record, "is_valid", False)),
        "parse_status": parse_status,
        "latency_ms": getattr(record, "latency_ms", None),
        "input_tokens": getattr(record, "input_tokens", None),
        "output_tokens": getattr(record, "output_tokens", None),
        "retry_count": getattr(record, "retry_count", 0),
        "error_type": error_type,
        "error": invalid_reason or error_type,
    }


def _exception_record(sample: PilotSample, exc: Exception) -> dict[str, Any]:
    error_type = type(exc).__name__
    is_timeout = isinstance(exc, (TimeoutError, openai.APITimeoutError)) or "timeout" in error_type.lower()
    parse_status = (
        "INCOMPLETE"
        if isinstance(exc, LiveBudgetExceededError)
        else ("TIMEOUT" if is_timeout else "API_FAILURE")
    )
    return {
        "sample_id": sample.sample_id,
        "source_id": sample.source_id,
        "condition": "no_rag",
        "provider": None,
        "model": None,
        "reasoning_effort": None,
        "prompt_version": None,
        "prediction": {"technique_id": None},
        "valid_attack_id": False,
        "parse_status": parse_status,
        "latency_ms": 0.0,
        "input_tokens": None,
        "output_tokens": None,
        "retry_count": 0,
        "error_type": error_type,
        "error": f"{error_type}: {exc}",
    }


def _pipeline_budget(pipeline: PilotPipeline) -> Any:
    return getattr(getattr(pipeline, "client", None), "live_budget", None)


def run_no_rag_pilot(
    samples: Iterable[PilotSample],
    pipeline: PilotPipeline,
    *,
    live_budget: Any = None,
) -> PilotRun:
    """Run No-RAG samples and stop immediately when the finite budget is exhausted."""

    sample_list = list(samples)
    budget = live_budget if live_budget is not None else _pipeline_budget(pipeline)
    output: list[dict[str, Any]] = []
    budget_exhausted = False
    for sample in sample_list:
        try:
            record = pipeline.run_sample(
                sample_id=sample.sample_id,
                endpoint_evidence=sample.endpoint_evidence,
                retrieved_context=None,
                condition="no_rag",
            )
            row = _record_to_dict(sample, record)
        except OPERATIONAL_EXCEPTIONS as exc:  # preserve expected operational failures
            row = _exception_record(sample, exc)
        output.append(row)

        if row.get("error_type") == "LiveBudgetExceededError":
            row["parse_status"] = "INCOMPLETE"
            budget_exhausted = True
            break
        if budget is not None and budget.is_exhausted() and len(output) < len(sample_list):
            budget_exhausted = True
            break

    return PilotRun(
        records=output,
        requested_samples=len(sample_list),
        processed_samples=len(output),
        complete=len(output) == len(sample_list),
        budget_exhausted=budget_exhausted or bool(budget is not None and budget.is_exhausted()),
    )


def summarize_predictions(
    records: Sequence[Mapping[str, Any]],
    *,
    run: PilotRun | None = None,
    live_budget: Any = None,
) -> dict[str, Any]:
    counts = Counter(str(record.get("parse_status") or "INCOMPLETE") for record in records)
    total = len(records)
    valid = counts["VALID"]
    latencies = [
        float(record["latency_ms"])
        for record in records
        if isinstance(record.get("latency_ms"), (int, float))
    ]
    input_tokens = [int(record["input_tokens"]) for record in records if isinstance(record.get("input_tokens"), int)]
    output_tokens = [int(record["output_tokens"]) for record in records if isinstance(record.get("output_tokens"), int)]
    budget_exhausted = bool(run and run.budget_exhausted)
    if live_budget is not None:
        budget_exhausted = budget_exhausted or live_budget.is_exhausted()
    return {
        "sample_count": total,
        "status_counts": {status: counts[status] for status in VALID_STATUSES},
        "valid_prediction_rate": valid / total if total else None,
        "transport_provider_failure_count": counts["API_FAILURE"] + counts["TIMEOUT"],
        "mean_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "total_input_tokens": sum(input_tokens) if input_tokens else None,
        "total_output_tokens": sum(output_tokens) if output_tokens else None,
        "total_retries": sum(int(record.get("retry_count") or 0) for record in records),
        "budget_exhausted": budget_exhausted,
        "configured_max_live_requests": getattr(live_budget, "max_requests", None),
        "live_requests_consumed": getattr(live_budget, "count", None),
        "remaining_live_requests": getattr(live_budget, "remaining", None),
        "requested_samples": run.requested_samples if run else total,
        "processed_samples": run.processed_samples if run else total,
        "run_complete": run.complete if run else True,
    }


def write_jsonl(path: Path | str, records: Sequence[Mapping[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def _git_head(workspace: Path) -> str | None:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=workspace,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def build_sidecar_metadata(
    *,
    input_path: Path | str,
    source_manifest_path: Path | str,
    prompt_path: Path | str,
    model_config_path: Path | str,
    manifest: Mapping[str, Any],
    run: PilotRun,
    sample_limit: int,
    live_budget: Any,
    attack_version: str | None,
    workspace: Path,
) -> dict[str, Any]:
    """Build deterministic run-level provenance without including secrets."""

    return {
        "input_sha256": manifest["input_sha256"],
        "source_manifest_sha256": _sha256_file(source_manifest_path),
        "prompt_sha256": _sha256_file(prompt_path),
        "model_config_sha256": _sha256_file(model_config_path),
        "sample_limit": sample_limit,
        "requested_sample_count": run.requested_samples,
        "processed_sample_count": run.processed_samples,
        "condition": "no_rag",
        "attack_version": attack_version,
        "live_budget_configured": live_budget.max_requests,
        "live_requests_consumed": live_budget.count,
        "remaining_budget": live_budget.remaining,
        "budget_exhausted": run.budget_exhausted,
        "run_completion_status": "COMPLETE" if run.complete else "INCOMPLETE",
        "repository_commit_sha": _git_head(workspace),
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded real-data No-RAG pilot")
    parser.add_argument("--input", type=Path, required=True, help="Sanitized real telemetry JSONL")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=MAX_PILOT_SAMPLES)
    parser.add_argument("--live", action="store_true", help="Enable explicitly authorized live API dispatch")
    parser.add_argument("--max-live-requests", type=int)
    parser.add_argument(
        "--approved-source-id",
        action="append",
        required=True,
        help="Approved source ID allowlist entry; repeat for multiple approved sources",
    )
    args = parser.parse_args(argv)

    if not args.live:
        raise DataUnavailableError("DATA_UNAVAILABLE: live pilot requires explicit --live")
    if args.max_live_requests is None:
        raise ValueError("--max-live-requests is required in live mode")
    validate_pilot_limit(args.limit)

    from src.llm.client import LiveBudget, LLMClient
    from src.llm.schemas import get_workspace_root, load_attack_registry

    workspace = get_workspace_root()
    model_config_path = workspace / "config" / "model.json"
    model_config = json.loads(model_config_path.read_text(encoding="utf-8"))
    validate_live_budget(args.max_live_requests, args.limit, int(model_config.get("max_retries", 3)))
    manifest, samples = prepare_pilot_inputs(
        args.input,
        args.source_manifest,
        args.limit,
        args.approved_source_id,
    )

    budget = LiveBudget(max_requests=args.max_live_requests)
    client = LLMClient(
        registry_ids=load_attack_registry(),
        live_budget=budget,
        is_live=True,
    )
    from src.baseline.pipeline import BaselinePipeline

    pipeline = BaselinePipeline(client=client)
    run = run_no_rag_pilot(samples, pipeline, live_budget=budget)
    summary = summarize_predictions(run.records, run=run, live_budget=budget)
    write_jsonl(args.output, run.records)

    prompt_path = workspace / "prompts" / "baseline_v1.txt"
    scope = json.loads((workspace / "config" / "benchmark_scope.json").read_text(encoding="utf-8"))
    sidecar = build_sidecar_metadata(
        input_path=args.input,
        source_manifest_path=args.source_manifest,
        prompt_path=prompt_path,
        model_config_path=model_config_path,
        manifest=manifest,
        run=run,
        sample_limit=args.limit,
        live_budget=budget,
        attack_version=scope.get("attack_version"),
        workspace=workspace,
    )
    sidecar_path = Path(f"{args.output}.meta.json")
    sidecar_path.parent.mkdir(parents=True, exist_ok=True)
    sidecar_path.write_text(json.dumps(sidecar, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
