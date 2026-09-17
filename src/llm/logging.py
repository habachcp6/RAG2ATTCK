"""
RAG2ATTCK - LLM Execution Logging and Serialization Module (Milestone M2)
Handles:
- WallClockTimer: Precision wall-clock timer covering full request lifecycle including retries and backoff
- Serialization of ExecutionRecord to dict, JSON, and CSV formats
- Batch record writing and audit logging
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
import time
from typing import Any, Dict, Iterable, List, Optional

from src.llm.schemas import ExecutionRecord

logger = logging.getLogger("rag2attck.llm")


# ---------------------------------------------------------------------------
# 1. Wall-Clock Duration Timer
# ---------------------------------------------------------------------------

class WallClockTimer:
    """
    Context manager measuring total wall-clock duration in milliseconds.
    
    Latency semantics:
    Measures duration from the initial API request attempt until the final
    returned status, strictly including all retry attempts and backoff sleeps.
    """

    def __init__(self) -> None:
        self.start_perf: float = 0.0
        self.end_perf: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> WallClockTimer:
        self.start_perf = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end_perf = time.perf_counter()
        self.elapsed_ms = (self.end_perf - self.start_perf) * 1000.0


# ---------------------------------------------------------------------------
# 2. Record Serialization and Persistence
# ---------------------------------------------------------------------------

CSV_FIELDNAMES = [
    "sample_id",
    "condition",
    "provider",
    "model",
    "reasoning_effort",
    "prompt_version",
    "predicted_technique_id",
    "parse_status",
    "invalid_reason",
    "input_tokens",
    "output_tokens",
    "latency_ms",
    "retry_count",
    "error_type",
]


def serialize_record(record: ExecutionRecord) -> Dict[str, Any]:
    """Serialize an ExecutionRecord to a Python dictionary."""
    return record.to_dict()


def log_execution(
    record: ExecutionRecord,
    custom_logger: Optional[logging.Logger] = None
) -> None:
    """Log an execution record event at INFO level."""
    log = custom_logger or logger
    log.info(
        "Sample: %s | Condition: %s | Status: %s | Predicted: %s | Latency: %.2f ms | Retries: %d",
        record.sample_id,
        record.condition,
        record.parse_status,
        record.predicted_technique_id or "N/A",
        record.latency_ms,
        record.retry_count,
    )


def append_record_jsonl(record: ExecutionRecord, output_file: Path | str) -> None:
    """Append a single ExecutionRecord as a JSON line to output_file."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "a", encoding="utf-8") as f:
        f.write(record.to_json() + "\n")


def save_records_jsonl(records: Iterable[ExecutionRecord], output_file: Path | str) -> None:
    """Save a collection of ExecutionRecords to a JSONL file."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(r.to_json() + "\n")


def save_records_csv(records: Iterable[ExecutionRecord], output_file: Path | str) -> None:
    """Save a collection of ExecutionRecords to a CSV file."""
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for r in records:
            writer.writerow(r.to_dict())


def format_execution_summary(records: List[ExecutionRecord]) -> Dict[str, Any]:
    """
    Computes summary statistics across a set of execution records.
    """
    if not records:
        return {
            "total_records": 0,
            "valid_count": 0,
            "valid_rate": 0.0,
            "status_counts": {},
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "mean_latency_ms": 0.0,
            "total_retries": 0,
        }

    total = len(records)
    valid_count = sum(1 for r in records if r.is_valid)
    status_counts: Dict[str, int] = {}
    for r in records:
        st = str(r.parse_status)
        status_counts[st] = status_counts.get(st, 0) + 1

    total_in = sum(r.input_tokens or 0 for r in records)
    total_out = sum(r.output_tokens or 0 for r in records)
    total_retries = sum(r.retry_count for r in records)
    mean_latency = sum(r.latency_ms for r in records) / total

    return {
        "total_records": total,
        "valid_count": valid_count,
        "valid_rate": valid_count / total,
        "status_counts": status_counts,
        "total_input_tokens": total_in,
        "total_output_tokens": total_out,
        "mean_latency_ms": round(mean_latency, 2),
        "total_retries": total_retries,
    }
