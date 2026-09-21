"""Known-answer pilot boundary tests; providers are injected fakes throughout."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import MagicMock

import openai
import pytest

from src.baseline.pipeline import BaselinePipeline
from src.llm.client import GLOBAL_LIVE_BUDGET, LiveBudget, LLMClient
from src.llm.schemas import TechniquePrediction
from src.pilot.no_rag_pilot import (
    DataUnavailableError,
    PilotSample,
    build_sidecar_metadata,
    capture_execution_snapshot,
    prepare_pilot_inputs,
    run_no_rag_pilot,
    summarize_predictions,
)
from tests.test_llm_client import create_mock_responses_api_response
from tests.test_no_rag_pilot import (
    _fixture_source_snapshot,
    _run_fixture_samples,
    _write_inputs,
)


def _pipeline(*, budget, is_live=True, config=None):
    provider = MagicMock()
    provider.responses.create.return_value = create_mock_responses_api_response(
        '{"technique_id":"T1059.001"}',
    )
    client = LLMClient(
        openai_client=provider, live_budget=budget, is_live=is_live,
        config_dict=config, registry_ids={"T1059.001"}, sleep_fn=lambda _: None,
    )
    return BaselinePipeline(client=client), provider


def _samples(count=2):
    return [PilotSample(f"s{index}", "source", f"EventID {index}") for index in range(count)]


@pytest.mark.parametrize("error", [
    TypeError("internal programming defect"),
    RuntimeError("500 timeout internal bug"),
    PermissionError("permission denied"),
    FileNotFoundError("missing internal file"),
])
def test_internal_error_propagates_through_actual_client_and_stops_batch(error):
    budget = LiveBudget(2)
    pipeline, provider = _pipeline(budget=budget)
    provider.responses.create.side_effect = error
    with pytest.raises(type(error), match=str(error)):
        _run_fixture_samples(_samples(), pipeline, live_budget=budget)
    assert provider.responses.create.call_count == budget.count == 1
    provider.chat.completions.create.assert_not_called()


def test_expected_provider_error_preserves_metadata_and_next_sample_runs():
    budget = LiveBudget(2)
    pipeline, provider = _pipeline(budget=budget)
    provider.responses.create.side_effect = [
        openai.AuthenticationError("unauthorized", response=MagicMock(), body=None),
        create_mock_responses_api_response('{"technique_id":"T1059.001"}'),
    ]
    run = _run_fixture_samples(_samples(), pipeline, live_budget=budget)
    assert run.complete
    assert [row["parse_status"] for row in run.records] == ["API_FAILURE", "VALID"]
    assert run.records[0]["provider"] == pipeline.client.provider
    assert run.records[0]["model"] == pipeline.client.model
    assert run.records[0]["prompt_version"] == pipeline.prompt_version
    assert run.records[0]["latency_ms"] >= 0
    assert run.records[0]["retry_count"] == 0
    assert provider.responses.create.call_count == budget.count == 2


@pytest.mark.parametrize("samples,match", [
    (_samples(21), "1 to 20"),
    (_samples() + [_samples()[0]], "Duplicate sample_id"),
    (_samples() + [PilotSample("bad", "source", "\x00")], "visible evidence"),
])
def test_bad_batch_is_rejected_before_first_request(samples, match):
    budget = LiveBudget(21)
    pipeline, provider = _pipeline(budget=budget)
    with pytest.raises(ValueError, match=match):
        run_no_rag_pilot(
            iter(samples), pipeline, live_budget=budget,
            source_snapshot=_fixture_source_snapshot(_samples()), approved_source_ids={"source"},
        )
    provider.responses.create.assert_not_called()
    assert budget.count == 0


def test_infinite_input_is_bounded_before_dispatch():
    def samples():
        for index in range(22):
            assert index < 21, "runner consumed beyond its bounded preflight"
            yield PilotSample(f"s{index}", "source", "EventID 1")

    budget = LiveBudget(20)
    pipeline, provider = _pipeline(budget=budget)
    with pytest.raises(ValueError, match="1 to 20"):
        run_no_rag_pilot(
            samples(), pipeline, live_budget=budget,
            source_snapshot=_fixture_source_snapshot(_samples()), approved_source_ids={"source"},
        )
    provider.responses.create.assert_not_called()


@pytest.mark.parametrize("kind,match", [
    ("missing", "explicit finite"),
    ("global", "explicit finite"),
    ("mismatch", "same LiveBudget"),
    ("disabled", "enable request accounting"),
    ("zero", "positive integer"),
    ("oversized", "pilot envelope"),
])
def test_pilot_cannot_fall_back_or_bypass_budget(kind, match):
    client_budget = GLOBAL_LIVE_BUDGET if kind == "global" else LiveBudget(
        0 if kind == "zero" else (100 if kind == "oversized" else 2),
    )
    pipeline, provider = _pipeline(budget=client_budget, is_live=kind != "disabled")
    runner_budget = None if kind == "missing" else (
        LiveBudget(2) if kind == "mismatch" else client_budget
    )
    with pytest.raises(ValueError, match=match):
        _run_fixture_samples(_samples(), pipeline, live_budget=runner_budget)
    provider.responses.create.assert_not_called()


def test_zero_token_usage_survives_client_runner_and_summary():
    budget = LiveBudget(1)
    pipeline, provider = _pipeline(budget=budget)
    response = create_mock_responses_api_response('{"technique_id":"T1059.001"}')
    response.usage.input_tokens = 0
    response.usage.output_tokens = 0
    provider.responses.create.return_value = response
    run = _run_fixture_samples(_samples(1), pipeline, live_budget=budget)
    assert run.records[0]["input_tokens"] == run.records[0]["output_tokens"] == 0
    summary = summarize_predictions(run.records, run=run, live_budget=budget)
    assert summary["total_input_tokens"] == summary["total_output_tokens"] == 0


def test_budget_denial_on_last_sample_is_incomplete_and_not_a_dispatched_retry():
    budget = LiveBudget(1)
    pipeline, provider = _pipeline(budget=budget)
    provider.responses.create.side_effect = openai.RateLimitError(
        "retryable", response=MagicMock(), body=None,
    )
    run = _run_fixture_samples(_samples(1), pipeline, live_budget=budget)
    assert not run.complete
    assert run.budget_exhausted
    assert run.records[0]["parse_status"] == "INCOMPLETE"
    assert run.records[0]["error_type"] == "LiveBudgetExceededError"
    assert run.records[0]["retry_count"] == 0
    assert provider.responses.create.call_count == budget.count == 1


def test_input_hash_and_samples_come_from_one_read(tmp_path, monkeypatch):
    input_path, manifest_path, manifest = _write_inputs(tmp_path)
    read_bytes = Path.read_bytes
    reads = []

    def read_then_replace(path):
        content = read_bytes(path)
        if path == input_path:
            reads.append(path)
            path.write_text('{"sample_id":"tampered"}\n', encoding="utf-8")
        return content

    monkeypatch.setattr(Path, "read_bytes", read_then_replace)
    prepared = prepare_pilot_inputs(input_path, manifest_path, 2, {"approved-source"})
    assert len(reads) == 1
    assert hashlib.sha256(prepared.input_bytes).hexdigest() == manifest["input_sha256"]
    assert [sample.sample_id for sample in prepared.samples] == ["s0", "s1"]


def test_snapshot_binds_actual_prompt_config_and_sidecar_without_reread(tmp_path, monkeypatch):
    input_path, manifest_path, _ = _write_inputs(tmp_path, count=1)
    prepared = prepare_pilot_inputs(input_path, manifest_path, 1, {"approved-source"})
    prompt_path = tmp_path / "prompt.txt"
    model_path = tmp_path / "model.json"
    prompt_path.write_text("frozen {ENDPOINT_EVIDENCE} {RETRIEVED_CONTEXT}", encoding="utf-8")
    model_path.write_text(json.dumps({"model": "fixture-model", "max_retries": 0}), encoding="utf-8")
    snapshot = capture_execution_snapshot(
        inputs=prepared, prompt_path=prompt_path, model_config_path=model_path,
        attack_version="19.2", workspace=Path.cwd(),
    )
    for path in (input_path, manifest_path, prompt_path, model_path):
        path.write_text("CHANGED AFTER CAPTURE", encoding="utf-8")
    budget = LiveBudget(1)
    provider = MagicMock()
    provider.responses.create.return_value = create_mock_responses_api_response('{"technique_id":"T1059.001"}')
    client = LLMClient(
        config_dict=snapshot.model_config, openai_client=provider, is_live=True,
        live_budget=budget, registry_ids={"T1059.001"},
    )

    def forbid_read(*args, **kwargs):
        raise AssertionError("execution/reporting must use the captured bytes")

    monkeypatch.setattr(Path, "read_text", forbid_read)
    monkeypatch.setattr(Path, "read_bytes", forbid_read)
    pipeline = BaselinePipeline(client=client, prompt_template=snapshot.prompt_template)
    run = run_no_rag_pilot(
        prepared.samples, pipeline, live_budget=budget,
        source_snapshot=prepared, approved_source_ids={"approved-source"},
    )
    sidecar = build_sidecar_metadata(snapshot=snapshot, run=run, sample_limit=1, live_budget=budget)
    assert provider.responses.create.call_args.kwargs["input"] == "frozen EventID 0 "
    assert provider.responses.create.call_args.kwargs["model"] == "fixture-model"
    assert sidecar["prompt_sha256"] == hashlib.sha256(snapshot.prompt_bytes).hexdigest()
    assert sidecar["model_config_sha256"] == hashlib.sha256(snapshot.model_config_bytes).hexdigest()
    assert sidecar["source_manifest_sha256"] == hashlib.sha256(prepared.manifest_bytes).hexdigest()
    assert sidecar["input_sha256"] == hashlib.sha256(prepared.input_bytes).hexdigest()
    assert sidecar["sample_ids"] == ["s0"]


def test_schema_implementation_defect_is_not_a_malformed_model_response(monkeypatch):
    budget = LiveBudget(1)
    pipeline, provider = _pipeline(budget=budget)

    def defect(*args, **kwargs):
        raise TypeError("schema programming defect")

    monkeypatch.setattr(TechniquePrediction, "model_validate", defect)
    with pytest.raises(TypeError, match="schema programming defect"):
        _run_fixture_samples(_samples(1), pipeline, live_budget=budget)
    assert provider.responses.create.call_count == budget.count == 1


def test_public_runner_requires_provenance_snapshot_and_explicit_allowlist():
    budget = LiveBudget(2)
    pipeline, provider = _pipeline(budget=budget)
    with pytest.raises(TypeError, match="source_snapshot"):
        run_no_rag_pilot(_samples(), pipeline, live_budget=budget)
    with pytest.raises(TypeError, match="approved_source_ids"):
        run_no_rag_pilot(
            _samples(), pipeline, live_budget=budget,
            source_snapshot=_fixture_source_snapshot(_samples()),
        )
    provider.responses.create.assert_not_called()
    assert budget.count == 0


@pytest.mark.parametrize("malformed", ["missing_snapshot", "mutable_bytes", "mutable_samples", "manifest_array"])
def test_public_runner_rejects_malformed_or_mutable_snapshot(malformed):
    budget = LiveBudget(2)
    pipeline, provider = _pipeline(budget=budget)
    snapshot = _fixture_source_snapshot(_samples())
    if malformed == "missing_snapshot":
        snapshot = None
    elif malformed == "mutable_bytes":
        snapshot = replace(snapshot, input_bytes=bytearray(snapshot.input_bytes))
    elif malformed == "mutable_samples":
        snapshot = replace(snapshot, samples=list(snapshot.samples))
    else:
        snapshot = replace(snapshot, manifest_bytes=b"[]")
    with pytest.raises((TypeError, ValueError), match="snapshot|immutable|JSON object"):
        run_no_rag_pilot(
            _samples(), pipeline, live_budget=budget,
            source_snapshot=snapshot, approved_source_ids={"source"},
        )
    provider.responses.create.assert_not_called()
    assert budget.count == 0


@pytest.mark.parametrize("tampering,expected_error", [
    ("input_hash", "SHA-256 mismatch"),
    ("snapshot_samples", "snapshot samples do not match"),
    ("requested_samples", "requested pilot samples do not match"),
    ("unapproved_source", "approved source allowlist"),
    ("not_real", "is_real_data=true"),
    ("not_sanitized", "sanitization_status"),
    ("manifest_source", "does not match manifest source_id"),
    ("manifest_count", "record count mismatch"),
])
def test_public_runner_rechecks_manifest_hash_and_sample_binding(tampering, expected_error):
    budget = LiveBudget(2)
    pipeline, provider = _pipeline(budget=budget)
    samples = _samples()
    snapshot = _fixture_source_snapshot(samples)
    approved = {"source"}
    manifest = snapshot.manifest
    if tampering == "input_hash":
        snapshot = replace(snapshot, input_bytes=snapshot.input_bytes + b" ")
    elif tampering == "snapshot_samples":
        changed = (replace(samples[0], endpoint_evidence="forged evidence"), samples[1])
        snapshot = replace(snapshot, samples=changed)
    elif tampering == "requested_samples":
        samples[0] = replace(samples[0], endpoint_evidence="forged evidence")
    elif tampering == "unapproved_source":
        approved = {"different-source"}
    else:
        if tampering == "not_real":
            manifest["is_real_data"] = False
        elif tampering == "not_sanitized":
            manifest["sanitization_status"] = "raw"
        elif tampering == "manifest_source":
            manifest["source_id"] = "changed-source"
            approved = {"changed-source"}
        elif tampering == "manifest_count":
            manifest["expected_record_count"] = 3
        snapshot = replace(snapshot, manifest_bytes=json.dumps(manifest).encode("utf-8"))
    with pytest.raises((DataUnavailableError, ValueError), match=expected_error):
        run_no_rag_pilot(
            samples, pipeline, live_budget=budget,
            source_snapshot=snapshot, approved_source_ids=approved,
        )
    provider.responses.create.assert_not_called()
    assert budget.count == 0
