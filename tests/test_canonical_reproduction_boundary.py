"""Tests verifying the execution-mode boundary in reproduction evaluator.

Ensures that mock fixtures or uncertified records cannot cross the boundary
into canonical study results, and that authoritative evaluation strictly requires
execution_mode == 'live' and split == 'test' across 1,280 samples x 5 conditions.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.reproduce_study import (
    run_authoritative_completed_evaluator,
    run_evaluator_fixture_diagnostics,
)
from src.evaluation.experiment_metrics import CONDITIONS


@pytest.fixture
def test_mock_matrix(tmp_path: Path) -> Path:
    """Create a complete 1,280 x 5 mock matrix with split='test' and
    execution_mode='mock_fixture'."""
    run_dir = tmp_path / "mock_matrix_run"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "schema_version": "1.0.0",
        "experiment_id": "mock-test-1280",
        "split": "test",
        "execution_mode": "mock_fixture",
        "status": "pre_freeze",
        "conditions": list(CONDITIONS),
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Write 1,280 records for each of the 5 conditions
    dummy_row = (
        json.dumps({"sample_id": "s0", "technique_id": "T1059.001", "rationale": "mock"}) + "\n"
    )
    content_1280 = dummy_row * 1280
    for cond in CONDITIONS:
        (run_dir / f"{cond}_predictions.jsonl").write_text(content_1280, encoding="utf-8")

    return run_dir


def test_mock_fixture_1280_matrix_fails_closed(test_mock_matrix: Path, tmp_path: Path) -> None:
    """Test 1: Complete 1,280x5 mock matrix (execution_mode='mock_fixture') MUST fail closed."""
    output_dir = tmp_path / "eval_output"
    output_lines: list[str] = []

    result = run_authoritative_completed_evaluator(
        manifest_path=None,
        run_dir=test_mock_matrix,
        output_dir=output_dir,
        output_lines=output_lines,
    )

    # Must return False
    assert result is False

    # Must NOT create canonical_study_results directory
    canonical_dir = output_dir / "canonical_study_results"
    assert not canonical_dir.exists(), (
        "canonical_study_results must not be created for mock_fixture"
    )

    # Must emit explicit fail-closed message citing execution_mode
    combined_log = "\n".join(output_lines)
    assert "[FAIL_CLOSED]" in combined_log
    assert "execution_mode" in combined_log
    assert "mock_fixture" in combined_log


@pytest.mark.parametrize(
    "invalid_mode",
    [None, "synthetic", "mock", "fixture", "unspecified", ""],
)
def test_missing_or_invalid_execution_mode_fails_closed(
    test_mock_matrix: Path, tmp_path: Path, invalid_mode: str | None
) -> None:
    """Test 2: Manifest with missing or invalid execution_mode MUST fail closed."""
    manifest_path = test_mock_matrix / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    if invalid_mode is None:
        manifest_data.pop("execution_mode", None)
    else:
        manifest_data["execution_mode"] = invalid_mode
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    output_dir = tmp_path / "eval_output_invalid_mode"
    output_lines: list[str] = []

    result = run_authoritative_completed_evaluator(
        manifest_path=manifest_path,
        run_dir=test_mock_matrix,
        output_dir=output_dir,
        output_lines=output_lines,
    )

    assert result is False
    assert not (output_dir / "canonical_study_results").exists()
    combined_log = "\n".join(output_lines)
    assert "[FAIL_CLOSED]" in combined_log
    assert "execution_mode" in combined_log


def test_positive_control_live_mode_and_post_load_validation(
    test_mock_matrix: Path, tmp_path: Path
) -> None:
    """Test 3: Positive control for mode gate and post-load inputs.execution_mode validation."""
    manifest_path = test_mock_matrix / "manifest.json"
    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_data["execution_mode"] = "live"
    manifest_path.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")

    output_dir = tmp_path / "eval_output_live"
    output_lines: list[str] = []

    # 3a. Sub-case: Post-load validation catches an inputs object whose execution_mode != "live"
    fake_mock_inputs = MagicMock()
    fake_mock_inputs.execution_mode = "mock_fixture"

    eval_inputs_target = "src.evaluation.experiment_metrics.load_evaluation_inputs"
    with patch(eval_inputs_target, return_value=fake_mock_inputs):
        result_subvert = run_authoritative_completed_evaluator(
            manifest_path=manifest_path,
            run_dir=test_mock_matrix,
            output_dir=output_dir,
            output_lines=output_lines,
        )
        assert result_subvert is False
        assert not (output_dir / "canonical_study_results").exists()
        assert "inputs.execution_mode='mock_fixture'" in "\n".join(output_lines)

    # 3b. Sub-case: Genuine live inputs pass post-load validation and proceed to evaluation
    output_lines.clear()
    fake_live_inputs = MagicMock()
    fake_live_inputs.execution_mode = "live"
    fake_results = {"overall": {"accuracy_end_to_end": 0.85, "completed_record_count": 6400}}

    with (
        patch(eval_inputs_target, return_value=fake_live_inputs),
        patch("src.evaluation.experiment_metrics.evaluate_experiment", return_value=fake_results),
    ):
        result_live = run_authoritative_completed_evaluator(
            manifest_path=manifest_path,
            run_dir=test_mock_matrix,
            output_dir=output_dir,
            output_lines=output_lines,
        )
        assert result_live is True
        assert (output_dir / "canonical_study_results").exists()
        combined_log = "\n".join(output_lines)
        assert "[PASS] Authoritative evaluation succeeded!" in combined_log
        assert "0.85" in combined_log


def test_fixture_diagnostics_preserves_fixture_only_metadata(tmp_path: Path) -> None:
    """Test 4: Fixture diagnostics runs cleanly in diagnostic namespace with fixture_only=True."""
    output_dir = tmp_path / "repro_output"
    output_lines: list[str] = []

    success = run_evaluator_fixture_diagnostics(output_dir, output_lines)
    assert success is True

    # Must be in fixture_diagnostics, NOT canonical_study_results
    diag_dir = output_dir / "fixture_diagnostics"
    assert diag_dir.exists()
    assert not (output_dir / "canonical_study_results").exists()

    # Verify _fixture_metadata.json
    meta_file = diag_dir / "_fixture_metadata.json"
    assert meta_file.exists()
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    assert meta.get("fixture_only") is True
    assert meta.get("purpose") == "known_answer_fixture_only"

    # Verify all 6 diagnostic artifacts exist and are non-empty
    for fname in (
        "overall_metrics.json",
        "per_condition_metrics.json",
        "per_technique_metrics.json",
        "retrieval_conditional_metrics.json",
        "failure_decomposition.json",
        "run_provenance.json",
    ):
        p = diag_dir / fname
        assert p.exists()
        assert p.stat().st_size > 0
