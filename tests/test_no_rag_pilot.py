from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import openai
import pytest

from src.baseline.pipeline import BaselinePipeline
from src.llm.client import LLMClient, LiveBudget
from src.pilot.no_rag_pilot import (
    MAX_PILOT_SAMPLES,
    DataUnavailableError,
    PilotRun,
    PilotSample,
    build_sidecar_metadata,
    load_pilot_samples,
    prepare_pilot_inputs,
    run_no_rag_pilot,
    summarize_predictions,
    validate_live_budget,
    validate_pilot_limit,
    validate_source_manifest,
)
from tests.test_llm_client import create_mock_responses_api_response


def _write_inputs(tmp_path: Path, *, source_id: str = "approved-source", count: int = 2):
    input_path = tmp_path / "samples.jsonl"
    rows = [
        {"sample_id": f"s{index}", "source_id": source_id, "endpoint_evidence": f"EventID {index}"}
        for index in range(count)
    ]
    input_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    manifest = {
        "dataset_id": "dataset-1",
        "source_id": source_id,
        "source_reference": "https://example.invalid/approved-source",
        "license": "CC-BY-4.0",
        "version": "1.0",
        "acquisition_date": "2026-09-20",
        "schema": {"format": "jsonl", "required": ["sample_id", "endpoint_evidence"]},
        "sanitization_status": "sanitized",
        "is_real_data": True,
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "expected_record_count": count,
    }
    manifest_path = tmp_path / "source_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return input_path, manifest_path, manifest


def test_source_manifest_requires_real_sanitized_data(tmp_path: Path):
    _, _, manifest = _write_inputs(tmp_path)
    manifest["is_real_data"] = False
    with pytest.raises(DataUnavailableError):
        validate_source_manifest(manifest, approved_source_ids={"approved-source"})


def test_source_manifest_hash_mismatch_blocks_before_dispatch(tmp_path: Path):
    input_path, manifest_path, manifest = _write_inputs(tmp_path)
    manifest["input_sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataUnavailableError, match="SHA-256 mismatch"):
        prepare_pilot_inputs(input_path, manifest_path, 1, {"approved-source"})


def test_source_id_mismatch_blocks_before_dispatch(tmp_path: Path):
    input_path, manifest_path, manifest = _write_inputs(tmp_path, source_id="manifest-source")
    rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line]
    rows[0]["source_id"] = "different-source"
    input_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    manifest["input_sha256"] = hashlib.sha256(input_path.read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="does not match manifest source_id"):
        prepare_pilot_inputs(input_path, manifest_path, 1, {"manifest-source"})


@pytest.mark.parametrize("limit", [0, -1, 21, 1000, True])
def test_sample_limit_rejects_out_of_range_values(limit):
    with pytest.raises(ValueError, match="1 to 20"):
        validate_pilot_limit(limit)


def test_sample_limit_accepts_one_and_twenty():
    validate_pilot_limit(1)
    validate_pilot_limit(MAX_PILOT_SAMPLES)


@pytest.mark.parametrize("budget", [0, -1, 1.5, float("inf"), None, True, "10"])
def test_pilot_budget_requires_finite_positive_integer(budget):
    with pytest.raises(ValueError, match="positive integer"):
        validate_live_budget(budget, 1, 3)


def test_sample_loader_rejects_duplicate_ids(tmp_path: Path):
    input_path, _, _ = _write_inputs(tmp_path)
    rows = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line]
    rows[1]["sample_id"] = rows[0]["sample_id"]
    input_path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        load_pilot_samples(input_path)


def test_no_rag_runner_forwards_no_context_and_preserves_metadata():
    calls = []

    class FakePipeline:
        def run_sample(self, **kwargs):
            calls.append(kwargs)
            return SimpleNamespace(
                predicted_technique_id="T1059.001",
                is_valid=True,
                parse_status="VALID",
                condition="no_rag",
                provider="openai",
                model="gpt-5.6-luna",
                reasoning_effort="xhigh",
                prompt_version="baseline_v1",
                latency_ms=12.5,
                input_tokens=10,
                output_tokens=5,
                retry_count=1,
                invalid_reason=None,
                error_type=None,
            )

    run = run_no_rag_pilot([PilotSample("s1", "source-1", "EventID 1")], FakePipeline())
    assert calls == [{
        "sample_id": "s1",
        "endpoint_evidence": "EventID 1",
        "retrieved_context": None,
        "condition": "no_rag",
    }]
    assert run.complete is True
    assert run.records[0]["condition"] == "no_rag"
    assert run.records[0]["provider"] == "openai"
    assert run.records[0]["model"] == "gpt-5.6-luna"
    assert run.records[0]["reasoning_effort"] == "xhigh"
    assert run.records[0]["prompt_version"] == "baseline_v1"


def test_actual_llm_client_budget_pipeline_runner_wiring_without_network():
    mock_openai = MagicMock()
    mock_openai.responses.create.side_effect = [
        create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"})),
        create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"})),
    ]
    budget = LiveBudget(max_requests=2)
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=budget,
        is_live=True,
        registry_ids={"T1059.001"},
        sleep_fn=lambda _: None,
    )
    pipeline = BaselinePipeline(client=client)
    run = run_no_rag_pilot(
        [PilotSample("s1", "source-1", "EventID 1"), PilotSample("s2", "source-1", "EventID 2")],
        pipeline,
        live_budget=budget,
    )
    assert run.complete is True
    assert [row["condition"] for row in run.records] == ["no_rag", "no_rag"]
    assert mock_openai.responses.create.call_count == 2
    assert budget.count == 2


def test_budget_exhaustion_stops_dispatch_and_marks_run_incomplete():
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )
    budget = LiveBudget(max_requests=1)
    pipeline = BaselinePipeline(
        client=LLMClient(
            openai_client=mock_openai,
            live_budget=budget,
            is_live=True,
            registry_ids={"T1059.001"},
        )
    )
    run = run_no_rag_pilot(
        [PilotSample("s1", "source-1", "EventID 1"), PilotSample("s2", "source-1", "EventID 2")],
        pipeline,
        live_budget=budget,
    )
    summary = summarize_predictions(run.records, run=run, live_budget=budget)
    assert mock_openai.responses.create.call_count == 1
    assert run.complete is False
    assert run.budget_exhausted is True
    assert summary["sample_count"] == 1
    assert summary["run_complete"] is False
    assert summary["budget_exhausted"] is True


def test_retry_accounting_consumes_two_budget_units():
    mock_openai = MagicMock()
    mock_openai.responses.create.side_effect = [
        openai.RateLimitError("Rate limit", response=MagicMock(), body=None),
        create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"})),
    ]
    budget = LiveBudget(max_requests=2)
    pipeline = BaselinePipeline(
        client=LLMClient(
            openai_client=mock_openai,
            live_budget=budget,
            is_live=True,
            registry_ids={"T1059.001"},
            sleep_fn=lambda _: None,
        )
    )
    run = run_no_rag_pilot([PilotSample("s1", "source-1", "EventID 1")], pipeline, live_budget=budget)
    summary = summarize_predictions(run.records, run=run, live_budget=budget)
    assert run.complete is True
    assert budget.count == 2
    assert run.records[0]["retry_count"] == 1
    assert summary["total_retries"] == 1


def test_summary_uses_non_overlapping_status_categories():
    records = [
        {"parse_status": "VALID", "valid_attack_id": True, "retry_count": 0},
        {"parse_status": "API_FAILURE", "valid_attack_id": False, "retry_count": 1},
    ]
    summary = summarize_predictions(records)
    assert summary["status_counts"] == {
        "VALID": 1,
        "INVALID_ID": 0,
        "MALFORMED_RESPONSE": 0,
        "REFUSAL": 0,
        "INCOMPLETE": 0,
        "API_FAILURE": 1,
        "TIMEOUT": 0,
    }
    assert summary["valid_prediction_rate"] == 0.5
    assert summary["transport_provider_failure_count"] == 1
    assert "api_or_pipeline_success_count" not in summary
    assert "failure_count" not in summary


def test_valid_source_manifest_and_sidecar_metadata(tmp_path: Path):
    input_path, manifest_path, manifest = _write_inputs(tmp_path, count=1)
    validate_source_manifest(manifest, input_path=input_path, approved_source_ids={"approved-source"})
    run = PilotRun([], 1, 0, False, True)
    budget = LiveBudget(1)
    prompt_path = tmp_path / "prompt.txt"
    model_path = tmp_path / "model.json"
    prompt_path.write_text("prompt", encoding="utf-8")
    model_path.write_text("{}", encoding="utf-8")
    sidecar = build_sidecar_metadata(
        input_path=input_path,
        source_manifest_path=manifest_path,
        prompt_path=prompt_path,
        model_config_path=model_path,
        manifest=manifest,
        run=run,
        sample_limit=1,
        live_budget=budget,
        attack_version="19.2",
        workspace=Path.cwd(),
    )
    assert sidecar["input_sha256"] == manifest["input_sha256"]
    assert sidecar["condition"] == "no_rag"
    assert sidecar["attack_version"] == "19.2"
    assert sidecar["run_completion_status"] == "INCOMPLETE"
