"""Same-checkout protocol and wire-contract checks with small synthetic fixtures."""

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.evaluation.experiment_metrics import (
    HumanDecisionRequired,
    _load_evaluation_inputs,
    evaluate_conditional_accuracy,
    evaluate_end_to_end,
    retrieval_observations,
)
from src.experiment.__main__ import main
from src.experiment.config import canonical_bytes, load_plan, parse_json
from src.experiment.runner import MockProvider, run_mock_experiment
from src.experiment.schemas import CONDITIONS, ExperimentRecord
from tests import test_experiment as experiment_fixtures

bundle = experiment_fixtures.bundle


@pytest.fixture(autouse=True)
def forbid_live_construction(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("integration fixture attempted live provider/embedder construction")

    monkeypatch.setattr("src.llm.client.openai.OpenAI", fail)
    monkeypatch.setattr("src.retrieval.retriever.SentenceTransformerEmbedder", fail)


@pytest.mark.parametrize("fill_other_placeholders", [False, True])
def test_raw_response_decision_remains_explicit(bundle, capsys, fill_other_placeholders):
    _, config_path, config = bundle
    if fill_other_placeholders:
        changed = deepcopy(config)
        changed["generation"]["model_version"] = "fixture-only-version"
        changed["execution"].update(concurrency=1, max_requests=10)
        config_path.write_bytes(canonical_bytes(changed))
    plan = load_plan(config_path)
    for output in (plan.manifest, plan.report()):
        reasons = output["human_decisions"]
        assert any(reason.startswith("raw_response_logging_policy:") for reason in reasons)
        raw_reason = next(r for r in reasons if r.startswith("raw_response_logging_policy:"))
        assert "T22" in raw_reason and "disables" in raw_reason
        assert "HUMAN_DECISION_REQUIRED" in raw_reason
    assert plan.report()["live_execution_implemented"] is False
    assert plan.report()["scientific_status"] == "NOT_FROZEN"
    assert plan.config.logging.raw_response is False
    assert plan.model_config["logging_policy"]["log_raw_response"] is False
    assert main(["--config", str(config_path), "--dry-run"]) == 2
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "HUMAN_DECISION_REQUIRED"
    assert report["live_execution_implemented"] is False
    assert report["provider_calls"] == report["prediction_writes"] == 0


def test_mock_runner_and_evaluator_share_one_checkout_contract(bundle, tmp_path):
    fixture_root, config_path, _ = bundle
    plan = load_plan(config_path)
    output = tmp_path / "mock-wire-contract"
    provider = MockProvider()
    summary = run_mock_experiment(plan, output, provider, max_requests=10)
    assert summary["complete"] and summary["record_count"] == 10
    assert len(provider.calls) == summary["requests_consumed"] == 10
    assert "SECRET_GT_METADATA" not in json.dumps(provider.calls)
    files = {condition: output / f"{condition}_predictions.jsonl" for condition in CONDITIONS}
    # This existing private fixture seam changes cardinality, never scientific scoring.
    inputs = _load_evaluation_inputs(
        output / "manifest.json", files, repository_root=fixture_root, expected_sample_count=2
    )
    assert len(inputs.records) == 10 and set(inputs.sample_ids) == {"s1", "s2"}
    assert inputs.ground_truth == {"s1": ("T1059.001",), "s2": ()}
    observations = retrieval_observations(inputs)
    assert observations["canonical_scoring"] == "HUMAN_DECISION_REQUIRED"
    assert set(observations["by_condition"]) == set(CONDITIONS[1:])
    for condition, metrics in observations["by_condition"].items():
        assert metrics["retrieval_k"] == int(condition[5:])
        assert metrics["total_samples"] == 2
        assert metrics["positive_samples"] == metrics["non_positive_samples"] == 1
    for record in inputs.records:
        assert record["raw_response"] is None and record["raw_response_logged"] is False
        with pytest.raises(ValidationError):
            ExperimentRecord.model_validate({**record, "ground_truth_technique_ids": ["T1105"]})
    for scorer in (evaluate_end_to_end, evaluate_conditional_accuracy):
        with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
            scorer(inputs, approved=True, force=True, policy={"status": "human_approved"})
    before = {path: path.read_bytes() for path in files.values()}
    resumed_provider = MockProvider()
    resumed = run_mock_experiment(plan, output, resumed_provider, max_requests=10, resume=True)
    assert resumed["new_records"] == 0 and not resumed_provider.calls
    assert all(path.read_bytes() == content for path, content in before.items())
    manifest = parse_json((output / "manifest.json").read_bytes())
    assert manifest["status"] == "pre_freeze"
    assert manifest["execution_mode"] == "mock_fixture"
    assert Path(output).is_relative_to(tmp_path)
