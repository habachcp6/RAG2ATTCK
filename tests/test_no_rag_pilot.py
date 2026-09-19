from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.pilot.no_rag_pilot import (
    DataUnavailableError,
    PilotSample,
    load_pilot_samples,
    run_no_rag_pilot,
    summarize_predictions,
    validate_source_manifest,
)


def test_source_manifest_requires_real_sanitized_data():
    manifest = {
        "source": "synthetic",
        "license": "internal",
        "version": "1",
        "acquisition_date": "2026-09-20",
        "schema": "jsonl",
        "sanitization_status": "synthetic",
        "is_real_data": False,
    }
    with pytest.raises(DataUnavailableError):
        validate_source_manifest(manifest)


def test_sample_loader_rejects_duplicate_and_empty_evidence(tmp_path: Path):
    path = tmp_path / "samples.jsonl"
    path.write_text(
        json.dumps({"sample_id": "s1", "source_id": "src", "endpoint_evidence": "log"})
        + "\n"
        + json.dumps({"sample_id": "s1", "source_id": "src", "endpoint_evidence": "other"})
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        load_pilot_samples(path)


def test_no_rag_runner_forwards_no_context_and_preserves_metadata():
    calls = []

    class FakePipeline:
        def run_sample(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                predicted_technique_id="T1059.001",
                is_valid=True,
                parse_status="VALID",
                latency_ms=12.5,
                input_tokens=10,
                output_tokens=5,
                retry_count=1,
                invalid_reason=None,
                error_type=None,
            )

    records = run_no_rag_pilot([PilotSample("s1", "source-1", "EventID 1")], FakePipeline())
    assert calls == [{
        "sample_id": "s1",
        "endpoint_evidence": "EventID 1",
        "retrieved_context": None,
        "condition": "no_rag",
    }]
    assert records[0]["prediction"] == {"technique_id": "T1059.001"}
    assert records[0]["valid_attack_id"] is True
    assert records[0]["retry_count"] == 1


def test_runner_normalizes_provider_failure_per_sample():
    class FailingPipeline:
        def run_sample(self, **kwargs):
            raise RuntimeError("provider unavailable")

    records = run_no_rag_pilot([PilotSample("s1", "source-1", "EventID 1")], FailingPipeline())
    assert records[0]["parse_status"] == "API_FAILURE"
    assert "provider unavailable" in records[0]["error"]
    assert summarize_predictions(records)["failure_count"] == 1


def test_valid_source_manifest_is_accepted():
    validate_source_manifest({
        "source": "public-windows-sysmon",
        "license": "CC-BY-4.0",
        "version": "1.0",
        "acquisition_date": "2026-09-20",
        "schema": "Sysmon JSONL",
        "sanitization_status": "sanitized",
        "is_real_data": True,
    })
