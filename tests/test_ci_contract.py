"""Mutation checks for the combined T20 lint and offline execution gates."""

import shlex
import tomllib
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
INFRASTRUCTURE_PATHS = {
    "src/experiment",
    "src/evaluation/experiment_metrics.py",
    "src/evaluation/fixture_metrics.py",
    "src/pilot/no_rag_pilot.py",
    "tests/test_experiment.py",
    "tests/test_experiment_evaluation.py",
    "tests/test_pilot_hardening.py",
    "tests/test_pre_experiment_integration.py",
    "tests/test_ci_contract.py",
}
GUARDED_PYTHON = ["uv", "run", "python", "scripts/run_offline_tests.py", "-m"]


def _workflow(name):
    return yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))


def _assert_mandatory(entry):
    # Critical gates use GitHub's default success condition and fail the run.
    # Expressions and explicit conditions need review rather than silent acceptance.
    assert "if" not in entry, "critical gate must not be conditionally disabled"
    assert entry.get("continue-on-error", False) is False, "critical gate must be blocking"


def _step(steps, name):
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"missing or duplicate step: {name}"
    _assert_mandatory(matches[0])
    return matches[0]


def _assert_ci(workflow):
    job = workflow["jobs"]["full-test-suite"]
    _assert_mandatory(job)
    assert set(job["strategy"]["matrix"]["os"]) == {"ubuntu-24.04", "windows-latest"}
    steps = job["steps"]
    assert shlex.split(_step(steps, "Lint T20 critical code paths")["run"]) == [
        "uv",
        "run",
        "ruff",
        "check",
        "scripts/analyze_retrieval_failures.py",
        "tests/test_retrieval_failure_analysis.py",
    ]
    lint = shlex.split(_step(steps, "Lint pre-experiment infrastructure")["run"])
    assert lint[:4] == ["uv", "run", "ruff", "check"]
    assert set(lint[4:]) == INFRASTRUCTURE_PATHS
    assert shlex.split(_step(steps, "Run Full Test Suite")["run"]) == (
        GUARDED_PYTHON + ["pytest", "-m", "not integration", "-q"]
    )
    assert shlex.split(
        _step(steps, "Verify frozen synthetic benchmark and same-seed reproduction")["run"]
    ) == GUARDED_PYTHON + ["src.data_ground_truth", "verify-synthetic"]
    names = [step.get("name") for step in steps]
    assert names.index("Acquire ATT&CK v19.2 reference") < names.index("Run Full Test Suite")


def _assert_integration(workflow):
    job = workflow["jobs"]["real-retrieval"]
    _assert_mandatory(job)
    steps = job["steps"]
    test_name = "Run real retrieval integration tests without provider access"
    assert shlex.split(_step(steps, test_name)["run"]) == (
        GUARDED_PYTHON + ["pytest", "-m", "integration", "-q"]
    )
    names = [step.get("name") for step in steps]
    for acquisition in (
        "Install dependencies",
        "Acquire ATT&CK v19.2 reference",
        "Acquire pinned embedding model before offline checks",
    ):
        assert names.index(acquisition) < names.index(test_name)


def test_combined_ci_keeps_lint_guard_and_acquisition_contracts():
    _assert_ci(_workflow("ci.yml"))
    _assert_integration(_workflow("integration.yml"))
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert config["tool"]["ruff"]["target-version"] == "py313"
    assert config["tool"]["ruff"]["line-length"] == 100
    assert config["tool"]["ruff"]["lint"]["select"] == ["E", "F", "W", "I"]


@pytest.mark.parametrize(
    "removed",
    [
        "Lint T20 critical code paths",
        "Lint pre-experiment infrastructure",
        "Run Full Test Suite",
        "Verify frozen synthetic benchmark and same-seed reproduction",
    ],
)
def test_missing_critical_ci_step_is_detected(removed):
    workflow = deepcopy(_workflow("ci.yml"))
    steps = workflow["jobs"]["full-test-suite"]["steps"]
    workflow["jobs"]["full-test-suite"]["steps"] = [s for s in steps if s.get("name") != removed]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


def test_unguarded_test_execution_is_detected():
    workflow = deepcopy(_workflow("ci.yml"))
    _step(workflow["jobs"]["full-test-suite"]["steps"], "Run Full Test Suite")["run"] = (
        'uv run pytest -m "not integration" -q'
    )
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


def test_guarded_execution_before_model_acquisition_is_detected():
    workflow = deepcopy(_workflow("integration.yml"))
    steps = workflow["jobs"]["real-retrieval"]["steps"]
    model_step = _step(steps, "Acquire pinned embedding model before offline checks")
    steps.remove(model_step)
    steps.append(model_step)
    with pytest.raises(AssertionError):
        _assert_integration(workflow)


@pytest.mark.parametrize(
    "workflow_name,job_name,step_name,validate",
    [
        ("ci.yml", "full-test-suite", "Lint T20 critical code paths", _assert_ci),
        (
            "integration.yml",
            "real-retrieval",
            "Run real retrieval integration tests without provider access",
            _assert_integration,
        ),
    ],
)
@pytest.mark.parametrize("location", ["job", "step"])
@pytest.mark.parametrize("key,value", [("if", False), ("continue-on-error", True)])
def test_disabled_or_nonblocking_gate_is_detected(
    workflow_name,
    job_name,
    step_name,
    validate,
    location,
    key,
    value,
):
    workflow = deepcopy(_workflow(workflow_name))
    job = workflow["jobs"][job_name]
    target = job if location == "job" else _step(job["steps"], step_name)
    target[key] = value
    with pytest.raises(AssertionError):
        validate(workflow)
