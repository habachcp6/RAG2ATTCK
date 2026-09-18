"""Validate the entire benchmark batch before retrieval or model dispatch."""

from collections.abc import Iterable, Mapping
from typing import Any


def validate_benchmark_batch(samples: Iterable[Mapping[str, Any]]) -> list[tuple[str, str]]:
    """Return only inference fields; preserve evidence bytes and normalize IDs.

    Legacy id/evidence aliases are accepted only when the canonical key is absent.
    Explicit malformed canonical fields must never be masked by an alias.
    """
    validated = []
    seen = set()
    for position, sample in enumerate(samples):
        prefix = f"Invalid benchmark sample at index {position}"
        if not isinstance(sample, Mapping):
            raise ValueError(f"{prefix}: expected a sample mapping")
        sample_id = sample.get("sample_id", sample.get("id"))
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError(f"{prefix}: missing or invalid sample_id; expected a non-empty string")
        sample_id = sample_id.strip()
        if sample_id in seen:
            raise ValueError(f"Duplicate sample_id {sample_id!r} at batch index {position}")
        seen.add(sample_id)
        evidence = sample.get("endpoint_evidence", sample.get("evidence"))
        if not isinstance(evidence, str) or not any(c.isprintable() and not c.isspace() for c in evidence):
            raise ValueError(
                f"{prefix} (sample_id={sample_id!r}): missing or invalid endpoint_evidence; "
                "expected a non-empty string containing visible evidence"
            )
        validated.append((sample_id, evidence))
    return validated
