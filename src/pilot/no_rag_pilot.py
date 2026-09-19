"""Bounded No-RAG pilot infrastructure.

The runner is intentionally provenance-first.  It refuses to treat the
repository's synthetic benchmark or engineering smoke cases as real telemetry.
When a legitimate sanitized source is supplied later, the same runner can
execute it through the frozen ``BaselinePipeline`` with ``condition=no_rag``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence


REQUIRED_SOURCE_FIELDS = (
    "source",
    "license",
    "version",
    "acquisition_date",
    "schema",
    "sanitization_status",
)


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


def validate_source_manifest(manifest: Mapping[str, Any]) -> None:
    """Require explicit provenance and a real, sanitized data declaration."""

    missing = [field for field in REQUIRED_SOURCE_FIELDS if not manifest.get(field)]
    if missing:
        raise ValueError(f"source manifest missing required fields: {', '.join(missing)}")
    if manifest.get("is_real_data") is not True:
        raise DataUnavailableError("source manifest does not declare is_real_data=true")
    status = str(manifest.get("sanitization_status", "")).lower()
    if status not in {"sanitized", "fully_sanitized", "anonymized"}:
        raise DataUnavailableError(
            "source manifest must declare a recognized sanitization_status "
            "(sanitized, fully_sanitized, or anonymized)"
        )


def load_pilot_samples(path: Path | str, limit: int = 20) -> list[PilotSample]:
    if type(limit) is not int or limit < 1:
        raise ValueError("limit must be a positive integer")
    rows = load_jsonl(path)
    samples: list[PilotSample] = []
    seen: set[str] = set()
    for index, row in enumerate(rows):
        sample_id = row.get("sample_id")
        evidence = row.get("endpoint_evidence")
        source_id = row.get("source_id", "")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError(f"sample index {index}: invalid sample_id")
        if sample_id.strip() in seen:
            raise ValueError(f"Duplicate sample_id {sample_id.strip()!r}")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"sample index {index}: endpoint_evidence is required")
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"sample index {index}: source_id is required")
        normalized_id = sample_id.strip()
        seen.add(normalized_id)
        samples.append(PilotSample(normalized_id, source_id.strip(), evidence))
        if len(samples) >= limit:
            break
    if not samples:
        raise ValueError("pilot input contains no samples")
    return samples


def _record_to_dict(sample: PilotSample, record: Any) -> dict[str, Any]:
    prediction_id = getattr(record, "predicted_technique_id", None)
    parse_status = getattr(record, "parse_status", None)
    if hasattr(parse_status, "value"):
        parse_status = parse_status.value
    invalid_reason = getattr(record, "invalid_reason", None)
    error_type = getattr(record, "error_type", None)
    return {
        "sample_id": sample.sample_id,
        "source_id": sample.source_id,
        "prediction": {"technique_id": prediction_id},
        "valid_attack_id": bool(getattr(record, "is_valid", False)),
        "parse_status": parse_status,
        "latency_ms": getattr(record, "latency_ms", None),
        "input_tokens": getattr(record, "input_tokens", None),
        "output_tokens": getattr(record, "output_tokens", None),
        "retry_count": getattr(record, "retry_count", 0),
        "error": invalid_reason or error_type,
    }


def run_no_rag_pilot(samples: Iterable[PilotSample], pipeline: PilotPipeline) -> list[dict[str, Any]]:
    """Run each sample with a structurally empty retrieved context."""

    output: list[dict[str, Any]] = []
    for sample in samples:
        try:
            record = pipeline.run_sample(
                sample_id=sample.sample_id,
                endpoint_evidence=sample.endpoint_evidence,
                retrieved_context=None,
                condition="no_rag",
            )
            output.append(_record_to_dict(sample, record))
        except Exception as exc:  # preserve per-sample failures for engineering analysis
            output.append(
                {
                    "sample_id": sample.sample_id,
                    "source_id": sample.source_id,
                    "prediction": {"technique_id": None},
                    "valid_attack_id": False,
                    "parse_status": "API_FAILURE",
                    "latency_ms": 0.0,
                    "input_tokens": None,
                    "output_tokens": None,
                    "retry_count": 0,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
    return output


def summarize_predictions(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(records)
    valid = sum(bool(record.get("valid_attack_id")) for record in records)
    successes = sum(record.get("parse_status") not in {"API_FAILURE", "TIMEOUT"} for record in records)
    latencies = [float(record["latency_ms"]) for record in records if isinstance(record.get("latency_ms"), (int, float))]
    input_tokens = [int(record["input_tokens"]) for record in records if isinstance(record.get("input_tokens"), int)]
    output_tokens = [int(record["output_tokens"]) for record in records if isinstance(record.get("output_tokens"), int)]
    return {
        "sample_count": total,
        "api_or_pipeline_success_count": successes,
        "api_or_pipeline_success_rate": successes / total if total else None,
        "valid_attack_id_count": valid,
        "valid_attack_id_rate": valid / total if total else None,
        "mean_latency_ms": sum(latencies) / len(latencies) if latencies else None,
        "total_input_tokens": sum(input_tokens) if input_tokens else None,
        "total_output_tokens": sum(output_tokens) if output_tokens else None,
        "total_retries": sum(int(record.get("retry_count") or 0) for record in records),
        "failure_count": sum(bool(record.get("error")) for record in records),
    }


def write_jsonl(path: Path | str, records: Sequence[Mapping[str, Any]]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(dict(record), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the bounded real-data No-RAG pilot")
    parser.add_argument("--input", type=Path, required=True, help="Sanitized real telemetry JSONL")
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)

    if not args.input.is_file() or not args.source_manifest.is_file():
        raise DataUnavailableError("DATA_UNAVAILABLE: approved input or source manifest is missing")
    manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
    validate_source_manifest(manifest)
    samples = load_pilot_samples(args.input, args.limit)

    from src.baseline.pipeline import BaselinePipeline

    records = run_no_rag_pilot(samples, BaselinePipeline())
    write_jsonl(args.output, records)
    print(json.dumps(summarize_predictions(records), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
