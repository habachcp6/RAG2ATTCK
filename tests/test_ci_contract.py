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
ACQUIRE_ATTACK = [
    "uv",
    "run",
    "python",
    "-c",
    "from pathlib import Path; from src.attack_loader import download_attack_reference; "
    "download_attack_reference(Path('.'))",
]
ACQUIRE_MODEL = [
    "uv",
    "run",
    "python",
    "-c",
    "import json; from sentence_transformers import SentenceTransformer; "
    "c=json.load(open('config/retrieval.json', encoding='utf-8')); "
    "SentenceTransformer(c['embedding_model_id'], revision=c['embedding_model_revision'])",
]
REQUIRED_INTEGRATION_PATHS = {
    "src/retrieval/**",
    "src/rag/**",
    "src/experiment/**",
    "src/llm/**",
    "src/baseline/**",
    "src/pilot/**",
    "src/evaluation/**",
    "config/experiment_config.json",
    "config/model.json",
    "config/retrieval.json",
    "attack/corpus/**",
    "attack/index/**",
    "scripts/run_offline_tests.py",
    "scripts/offline_guard/**",
    "tests/test_experiment*.py",
    "tests/test_pre_experiment_integration.py",
    "tests/test_ci_contract.py",
    "tests/test_pilot_hardening.py",
    "tests/test_llm_client.py",
    "tests/test_live_budget.py",
    "tests/test_no_rag_pilot.py",
    "tests/test_baseline_pipeline.py",
    "tests/test_retriever.py",
    "tests/test_retrieval_integrity.py",
    "tests/test_rag_pipeline.py",
    "tests/test_retrieval_diagnostics.py",
    "pyproject.toml",
    "uv.lock",
    ".python-version",
    "src/attack_loader.py",
    ".github/workflows/integration.yml",
}


def _workflow(name):
    return yaml.safe_load((ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8"))


def _assert_mandatory(entry):
    # Critical gates use GitHub's default success condition and fail the run.
    # Expressions and explicit conditions need review rather than silent acceptance.
    assert "if" not in entry, "critical gate must not be conditionally disabled"
    assert entry.get("continue-on-error", False) is False, "critical gate must be blocking"


def _assert_triggers(workflow, *, integration):
    events = workflow["on"]
    assert set(events) == {"push", "pull_request", "workflow_dispatch"}
    for event in ("push", "pull_request"):
        trigger = events[event]
        assert trigger["branches"] == ["main"]
        if integration:
            assert set(trigger) == {"branches", "paths"}
            paths = trigger["paths"]
            assert len(paths) == len(set(paths)), "duplicate path filter"
            assert REQUIRED_INTEGRATION_PATHS <= set(paths)
        else:
            assert trigger == {"branches": ["main"]}, "normal CI must cover all paths"
    if integration:
        assert set(events["push"]["paths"]) == set(events["pull_request"]["paths"])


def _assert_job(job, *, runs_on):
    _assert_mandatory(job)
    assert "needs" not in job, "critical job must not depend on a skippable job"
    assert job["runs-on"] == runs_on


def _step(steps, name):
    matches = [step for step in steps if step.get("name") == name]
    assert len(matches) == 1, f"missing or duplicate step: {name}"
    _assert_mandatory(matches[0])
    return matches[0]


def _assert_common_setup(steps, *, full_history=False):
    checkout = _step(steps, "Checkout repository")
    assert checkout["uses"] == "actions/checkout@v7.0.1"
    assert checkout["with"]["persist-credentials"] is False
    if full_history:
        assert checkout["with"]["fetch-depth"] == 0
    python = _step(steps, "Set up Python")
    assert python["uses"] == "actions/setup-python@v7.0.0"
    assert python["with"]["python-version-file"] == ".python-version"
    uv = _step(steps, "Set up uv")
    assert uv["uses"] == "astral-sh/setup-uv@v10.1.0"
    assert uv["with"]["version"] == "${{ env.UV_VERSION }}"
    for name, command in (
        ("Validate lockfile", "uv lock --check --offline"),
        ("Install dependencies", "uv sync --frozen"),
        ("Check installed dependencies", "uv pip check"),
    ):
        assert _step(steps, name)["run"] == command
    names = [step.get("name") for step in steps]
    ordered = (
        "Checkout repository",
        "Set up Python",
        "Set up uv",
        "Validate lockfile",
        "Install dependencies",
        "Check installed dependencies",
    )
    assert [names.index(name) for name in ordered] == sorted(names.index(name) for name in ordered)


def _assert_ci(workflow):
    _assert_triggers(workflow, integration=False)
    assert workflow["env"]["UV_VERSION"] == "0.11.24"
    assert {"registry-validation", "synthetic-tests", "full-test-suite"} <= set(workflow["jobs"])
    registry = workflow["jobs"]["registry-validation"]
    _assert_job(registry, runs_on="ubuntu-24.04")
    _assert_common_setup(registry["steps"])
    assert _step(registry["steps"], "Validate Synthetic Registry")["run"] == (
        "uv run python scripts/validate_synthetic_registry.py"
    )
    synthetic = workflow["jobs"]["synthetic-tests"]
    _assert_job(synthetic, runs_on="ubuntu-24.04")
    _assert_common_setup(synthetic["steps"])
    assert shlex.split(_step(synthetic["steps"], "Run Synthetic Tests")["run"]) == (
        GUARDED_PYTHON + ["pytest", "tests/test_synthetic.py", "-q"]
    )
    job = workflow["jobs"]["full-test-suite"]
    _assert_job(job, runs_on="${{ matrix.os }}")
    assert job["strategy"]["matrix"] == {"os": ["ubuntu-24.04", "windows-latest"]}
    steps = job["steps"]
    _assert_common_setup(steps, full_history=True)
    assert shlex.split(_step(steps, "Lint T20 critical code paths")["run"]) == [
        "uv",
        "run",
        "ruff",
        "check",
        "scripts/analyze_retrieval_failures.py",
        "scripts/verify_t20_canonical_artifacts.py",
        "tests/test_retrieval_failure_analysis.py",
        "tests/test_t20_canonical_artifacts.py",
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
    assert shlex.split(_step(steps, "Acquire ATT&CK v19.2 reference")["run"]) == ACQUIRE_ATTACK
    names = [step.get("name") for step in steps]
    assert names.index("Acquire ATT&CK v19.2 reference") < names.index("Run Full Test Suite")


def _assert_integration(workflow):
    _assert_triggers(workflow, integration=True)
    assert workflow["env"]["UV_VERSION"] == "0.11.24"
    job = workflow["jobs"]["real-retrieval"]
    _assert_job(job, runs_on="ubuntu-24.04")
    steps = job["steps"]
    _assert_common_setup(steps, full_history=True)
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
        _step(steps, acquisition)
        assert names.index(acquisition) < names.index(test_name)
    assert shlex.split(_step(steps, "Acquire ATT&CK v19.2 reference")["run"]) == ACQUIRE_ATTACK
    assert shlex.split(
        _step(steps, "Acquire pinned embedding model before offline checks")["run"]
    ) == ACQUIRE_MODEL


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


@pytest.mark.parametrize("event", ["push", "pull_request", "workflow_dispatch"])
def test_missing_ci_trigger_is_detected(event):
    workflow = deepcopy(_workflow("ci.yml"))
    del workflow["on"][event]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_ci_trigger_narrowed_away_from_main_is_detected(event):
    workflow = deepcopy(_workflow("ci.yml"))
    workflow["on"][event]["branches"] = ["codex/old-ci-branch"]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize("event", ["push", "pull_request"])
def test_ci_path_filter_is_detected(event):
    workflow = deepcopy(_workflow("ci.yml"))
    workflow["on"][event]["paths"] = ["README.md"]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize("event", ["push", "pull_request"])
@pytest.mark.parametrize("path", ["src/retrieval/**", "src/rag/**", "src/evaluation/**"])
def test_missing_integration_path_trigger_is_detected(event, path):
    workflow = deepcopy(_workflow("integration.yml"))
    workflow["on"][event]["paths"].remove(path)
    with pytest.raises(AssertionError):
        _assert_integration(workflow)


@pytest.mark.parametrize("job_name", ["registry-validation", "synthetic-tests"])
def test_missing_supporting_ci_job_is_detected(job_name):
    workflow = deepcopy(_workflow("ci.yml"))
    del workflow["jobs"][job_name]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize("job_name", ["registry-validation", "synthetic-tests"])
@pytest.mark.parametrize("key,value", [("if", False), ("continue-on-error", True)])
def test_disabled_or_nonblocking_supporting_ci_job_is_detected(job_name, key, value):
    workflow = deepcopy(_workflow("ci.yml"))
    workflow["jobs"][job_name][key] = value
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize(
    "step_name", ["Validate lockfile", "Install dependencies", "Check installed dependencies"]
)
def test_nonblocking_dependency_gate_is_detected(step_name):
    workflow = deepcopy(_workflow("ci.yml"))
    step = _step(workflow["jobs"]["full-test-suite"]["steps"], step_name)
    step["run"] += " || true"
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


def test_matrix_excluding_windows_is_detected():
    workflow = deepcopy(_workflow("ci.yml"))
    workflow["jobs"]["full-test-suite"]["strategy"]["matrix"]["exclude"] = [
        {"os": "windows-latest"}
    ]
    with pytest.raises(AssertionError):
        _assert_ci(workflow)


@pytest.mark.parametrize(
    "workflow_name,job_name,step_name,validate",
    [
        ("ci.yml", "full-test-suite", "Acquire ATT&CK v19.2 reference", _assert_ci),
        (
            "integration.yml",
            "real-retrieval",
            "Acquire ATT&CK v19.2 reference",
            _assert_integration,
        ),
        (
            "integration.yml",
            "real-retrieval",
            "Acquire pinned embedding model before offline checks",
            _assert_integration,
        ),
    ],
)
def test_named_acquisition_without_real_command_is_detected(
    workflow_name, job_name, step_name, validate
):
    workflow = deepcopy(_workflow(workflow_name))
    _step(workflow["jobs"][job_name]["steps"], step_name)["run"] = "echo acquired"
    with pytest.raises(AssertionError):
        validate(workflow)


@pytest.mark.parametrize(
    "workflow_name,job_name,validate",
    [
        ("ci.yml", "full-test-suite", _assert_ci),
        ("integration.yml", "real-retrieval", _assert_integration),
    ],
)
def test_shallow_checkout_for_provenance_tests_is_detected(workflow_name, job_name, validate):
    workflow = deepcopy(_workflow(workflow_name))
    checkout = _step(workflow["jobs"][job_name]["steps"], "Checkout repository")
    checkout["with"]["fetch-depth"] = 1
    with pytest.raises(AssertionError):
        validate(workflow)


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
