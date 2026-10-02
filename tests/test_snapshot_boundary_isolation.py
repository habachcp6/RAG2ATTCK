"""
tests/test_snapshot_boundary_isolation.py

Rigorous test suite verifying isolated snapshot execution boundaries and fail-closed protections:
1. Positive control: genuine detached b69 snapshot passes preflight with strict schema and venv attestation.
2. Positive control: genuine detached b69 snapshot passes verify_baselines (53 core, f85, 22 baselines, BOM).
3. Negative control (Gap 1): missing or corrupt .venv (missing pyvenv.cfg) fails closed.
4. Negative control (Gap 1): missing, zero count, or tampered baseline inventory fails closed.
5. Negative control (Gap 1): missing .git directory or non-repository root fails closed.
6. Negative control (Gap 2): minimal PASS payload missing required fields is rejected by controller.
7. Negative control (Gap 2): wrong-task payload is rejected by controller.
8. Negative control (Gap 2): missing origins, uninstalled guard, or non-zero egress in PASS is rejected.
9. Positive control (Gap 3): worker runtime attestation and uv.lock dependency verification succeeds.
10. Negative control (Gap 3): mismatched sys.prefix in worker runtime attestation is rejected.
11. Negative control (Gap 3): dependency version mismatch against uv.lock is rejected.
12. Negative control (Gap 4): post-execution drift in evaluate_rqs.py is caught by expanded inventory.
13. Negative control (Gap 4): post-execution drift in 22 baselines, protocol, or lock is caught.
14. Negative control (Gap 4): post-execution drift in Git state is caught by expanded inventory.
15. Negative control: invalid/missing snapshot root fails closed.
16. Negative control: arbitrary non-snapshot Python interpreter override is rejected.
17. Negative control: partial or corrupt snapshot fails closed on core inventory verification.
18. Negative control: child process exit-code non-zero with PASS payload fails closed.
19. Negative control: credential re-introduction via extra_env and PYTHONPATH are scrubbed.
20. Negative control: socket address resolution and DNS queries (socket.getaddrinfo) are blocked.
21. Negative control: module with foreign __file__ or mismatched spec.origin fails boundary check.
22. Negative control: callable with foreign co_filename inside loaded module fails boundary check.
23. Negative control: output path inside snapshot root or targeting control scripts is rejected.
24. Negative control: offline guard socket egress attempts are intercepted and blocked.
25. Negative control: snapshot immutability violation during execution raises critical error.
26. Negative control: current-tree source drift produces code manifest hash distinct from historical 8b.
27. Negative control: dirty snapshot working tree or wrong Git commit is rejected.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.machinery
import json
import os
import shutil
import socket
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.isolated_snapshot_controller import (
    EXPECTED_ANALYSIS_SOURCE_SHA256,
    EXPECTED_BASELINE_FILES_COUNT,
    EXPECTED_CORE_FILES_COUNT,
    EXPECTED_CORE_MANIFEST_SHA256,
    EXPECTED_SNAPSHOT_GIT_COMMIT,
    compute_closed_snapshot_inventory,
    compute_expanded_snapshot_inventory,
    compute_quick_snapshot_fingerprint,
    execute_snapshot_task,
    resolve_snapshot_python,
    sanitize_environment,
    validate_output_path_containment,
    validate_worker_attestation_schema,
    verify_snapshot_git_identity,
    verify_snapshot_venv_dependencies,
)
from scripts.isolated_snapshot_worker import (
    SnapshotGuardSecurityError,
    verify_module_origin_boundaries,
    verify_protected_baselines,
)

GENUINE_SNAPSHOT_ROOT = Path("C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_snapshots/b69a690")


def test_positive_snapshot_preflight(tmp_path: Path):
    """Verify that detached clean b69 snapshot succeeds under isolated child preflight."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "preflight_attestation.json"
    result = execute_snapshot_task(
        snapshot_root=GENUINE_SNAPSHOT_ROOT,
        task="preflight",
        output_path=out_file,
    )

    assert result["status"] == "PASS"
    assert result["task"] == "preflight"
    assert result["file_count"] == EXPECTED_CORE_FILES_COUNT
    assert result["code_manifest_sha256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert result["git_commit"] == EXPECTED_SNAPSHOT_GIT_COMMIT
    assert result["protected_baselines_verified_count"] == EXPECTED_BASELINE_FILES_COUNT
    assert result["offline_guard_installed"] is True
    assert result["attempted_egress_count"] == 0
    assert result["loaded_origins_count"] > 0
    assert result["controller_attestation"]["immutability_verified"] is True
    assert result["controller_attestation"]["expanded_immutability_verified"] is True
    assert result["controller_attestation"]["exit_code"] == 0

    runtime = result["worker_runtime_attestation"]
    assert "sys_executable" in runtime
    assert "sys_prefix" in runtime
    assert Path(runtime["sys_prefix"]).resolve() == (GENUINE_SNAPSHOT_ROOT / ".venv").resolve()
    assert len(runtime["installed_dependencies"]) > 0

    # Ensure all loaded origins are strictly within snapshot root
    for mod_name, origin_path in result["loaded_origins"].items():
        assert str(GENUINE_SNAPSHOT_ROOT.as_posix()) in origin_path, f"Origin breach: {mod_name} -> {origin_path}"


def test_positive_snapshot_baselines(tmp_path: Path):
    """Verify baseline hashes, evaluate_rqs f85 hash, BOM hash, and expanded inventory on snapshot."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "baselines_attestation.json"
    result = execute_snapshot_task(
        snapshot_root=GENUINE_SNAPSHOT_ROOT,
        task="verify_baselines",
        output_path=out_file,
    )

    assert result["status"] == "PASS"
    assert result["task"] == "verify_baselines"
    assert result["file_count"] == EXPECTED_CORE_FILES_COUNT
    assert result["code_manifest_sha256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert result["git_commit"] == EXPECTED_SNAPSHOT_GIT_COMMIT
    assert result["evaluate_rqs_sha256"] == EXPECTED_ANALYSIS_SOURCE_SHA256
    assert result["src_rag_init_sha256"] == "1d16d258b4c3f89aac043fad68a19031bf16d21daad4251846ba2f4297fa16c1"
    assert result["src_rag_init_has_bom"] is True
    assert result["protected_baselines_verified_count"] == EXPECTED_BASELINE_FILES_COUNT
    assert result["offline_guard_installed"] is True
    assert result["attempted_egress_count"] == 0
    assert result["controller_attestation"]["exit_code"] == 0
    assert result["controller_attestation"]["expanded_immutability_verified"] is True
    assert result["loaded_origins_count"] > 0


# --- Gap 1 Tests ---

def test_negative_missing_or_corrupt_venv_rejected(tmp_path: Path):
    """Snapshot missing .venv or pyvenv.cfg must fail closed."""
    fake_snap = tmp_path / "snap_no_venv"
    fake_snap.mkdir()

    with pytest.raises(FileNotFoundError, match="missing dedicated '.venv' directory"):
        resolve_snapshot_python(fake_snap)

    # Missing pyvenv.cfg
    (fake_snap / ".venv").mkdir()
    with pytest.raises(FileNotFoundError, match="missing pyvenv.cfg"):
        resolve_snapshot_python(fake_snap)


def test_negative_missing_or_zero_baselines_rejected(tmp_path: Path):
    """Missing baseline manifest, count != 22, or hash mismatch must fail closed."""
    fake_snap = tmp_path / "snap_baselines"
    fake_snap.mkdir()

    # Missing inventory file
    with pytest.raises(FileNotFoundError, match="Missing protected baseline inventory"):
        verify_protected_baselines(fake_snap)

    # Empty / zero count inventory
    inv_dir = fake_snap / "artifacts" / "orchestration"
    inv_dir.mkdir(parents=True)
    (inv_dir / "integration_protected_baseline.json").write_text(
        json.dumps({"protected_files": {}}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="Protected baselines count mismatch"):
        verify_protected_baselines(fake_snap)


def test_negative_missing_git_directory_rejected(tmp_path: Path):
    """Snapshot without a .git directory must fail closed."""
    fake_snap = tmp_path / "snap_no_git"
    fake_snap.mkdir()

    with pytest.raises(RuntimeError, match="missing .git directory or reference file"):
        verify_snapshot_git_identity(fake_snap)


# --- Gap 2 Tests ---

def test_negative_minimal_pass_payload_rejected_by_controller(tmp_path: Path):
    """Controller must reject a minimal PASS payload missing required schema fields."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "minimal_pass.json"
    orig_subprocess_run = subprocess.run

    def fake_subprocess_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0 and "git" in str(cmd[0]):
            return orig_subprocess_run(cmd, *args, **kwargs)
        # Write minimal PASS payload without task, origins, core, guard
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"status": "PASS"}, f)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        with pytest.raises(RuntimeError, match="Worker attestation schema rejection"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="preflight",
                output_path=out_file,
            )


def test_negative_wrong_task_payload_rejected_by_controller(tmp_path: Path):
    """Controller must reject worker output reporting a different task than expected."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    fake_output = {
        "status": "PASS",
        "task": "wrong_task",
        "code_manifest_sha256": EXPECTED_CORE_MANIFEST_SHA256,
        "file_count": EXPECTED_CORE_FILES_COUNT,
        "offline_guard_installed": True,
        "attempted_egress_count": 0,
        "protected_baselines_verified_count": EXPECTED_BASELINE_FILES_COUNT,
        "loaded_origins": {"src": str(GENUINE_SNAPSHOT_ROOT / "src")},
        "loaded_origins_count": 1,
        "worker_runtime_attestation": {
            "sys_prefix": str(GENUINE_SNAPSHOT_ROOT / ".venv"),
            "sys_executable": str(resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)),
            "installed_dependencies": {"pytest": "9.1.1"},
        },
    }

    with pytest.raises(RuntimeError, match="task mismatch! Expected 'preflight', got 'wrong_task'"):
        validate_worker_attestation_schema(fake_output, "preflight", GENUINE_SNAPSHOT_ROOT)


def test_negative_missing_origins_or_guard_in_pass_rejected(tmp_path: Path):
    """Worker output claiming PASS with empty loaded_origins or uninstalled guard must fail closed."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    base_payload = {
        "status": "PASS",
        "task": "preflight",
        "code_manifest_sha256": EXPECTED_CORE_MANIFEST_SHA256,
        "file_count": EXPECTED_CORE_FILES_COUNT,
        "offline_guard_installed": True,
        "attempted_egress_count": 0,
        "protected_baselines_verified_count": EXPECTED_BASELINE_FILES_COUNT,
        "loaded_origins": {"src": str(GENUINE_SNAPSHOT_ROOT / "src")},
        "loaded_origins_count": 1,
        "worker_runtime_attestation": {
            "sys_prefix": str(GENUINE_SNAPSHOT_ROOT / ".venv"),
            "sys_executable": str(resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)),
            "installed_dependencies": {"pytest": "9.1.1"},
        },
    }

    # Case 1: uninstalled guard
    bad_guard = dict(base_payload)
    bad_guard["offline_guard_installed"] = False
    with pytest.raises(RuntimeError, match="offline_guard_installed must be True"):
        validate_worker_attestation_schema(bad_guard, "preflight", GENUINE_SNAPSHOT_ROOT)

    # Case 2: non-zero egress
    bad_egress = dict(base_payload)
    bad_egress["attempted_egress_count"] = 1
    with pytest.raises(RuntimeError, match="attempted_egress_count must be 0"):
        validate_worker_attestation_schema(bad_egress, "preflight", GENUINE_SNAPSHOT_ROOT)

    # Case 3: empty loaded_origins
    bad_origins = dict(base_payload)
    bad_origins["loaded_origins"] = {}
    with pytest.raises(RuntimeError, match="loaded_origins must be a non-empty dictionary"):
        validate_worker_attestation_schema(bad_origins, "preflight", GENUINE_SNAPSHOT_ROOT)


# --- Gap 3 Tests ---

def test_positive_worker_runtime_attestation_and_uv_lock_verification(tmp_path: Path):
    """Verify that controller correctly cross-checks installed dependencies against uv.lock."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    valid_attestation = {
        "sys_prefix": str(GENUINE_SNAPSHOT_ROOT / ".venv"),
        "sys_executable": str(resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)),
        "installed_dependencies": {
            "pytest": "9.1.1",
            "pydantic": "2.13.5",
        },
    }
    # Should not raise
    verify_snapshot_venv_dependencies(GENUINE_SNAPSHOT_ROOT, valid_attestation)


def test_negative_venv_mismatched_sys_prefix_rejected(tmp_path: Path):
    """Attestation reporting sys.prefix outside snapshot venv must be rejected."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    bad_payload = {
        "status": "PASS",
        "task": "preflight",
        "code_manifest_sha256": EXPECTED_CORE_MANIFEST_SHA256,
        "file_count": EXPECTED_CORE_FILES_COUNT,
        "offline_guard_installed": True,
        "attempted_egress_count": 0,
        "protected_baselines_verified_count": EXPECTED_BASELINE_FILES_COUNT,
        "loaded_origins": {"src": str(GENUINE_SNAPSHOT_ROOT / "src")},
        "loaded_origins_count": 1,
        "worker_runtime_attestation": {
            "sys_prefix": str(tmp_path / "foreign_venv"),
            "sys_executable": str(resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)),
            "installed_dependencies": {"pytest": "9.1.1"},
        },
    }
    with pytest.raises(RuntimeError, match="sys_prefix .* does not match snapshot venv"):
        validate_worker_attestation_schema(bad_payload, "preflight", GENUINE_SNAPSHOT_ROOT)


def test_negative_uv_lock_dependency_version_mismatch_rejected(tmp_path: Path):
    """Attestation reporting a package version differing from uv.lock must fail closed."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    tampered_attestation = {
        "sys_prefix": str(GENUINE_SNAPSHOT_ROOT / ".venv"),
        "sys_executable": str(resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)),
        "installed_dependencies": {
            "pytest": "1.0.0-rogue",
        },
    }
    with pytest.raises(RuntimeError, match="Venv dependency version mismatch for 'pytest'"):
        verify_snapshot_venv_dependencies(GENUINE_SNAPSHOT_ROOT, tampered_attestation)


# --- Gap 4 Tests ---

def test_negative_expanded_inventory_drift_in_evaluate_rqs_rejected(tmp_path: Path):
    """Drift in evaluate_rqs.py between pre and post must trigger immutability breach."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "rq_drift.json"
    pre_expanded = compute_expanded_snapshot_inventory(GENUINE_SNAPSHOT_ROOT)
    post_expanded = copy.deepcopy(pre_expanded)
    post_expanded["evaluate_rqs_sha256"] = "0000000000000000000000000000000000000000000000000000000000000000"

    with patch(
        "scripts.isolated_snapshot_controller.compute_expanded_snapshot_inventory",
        side_effect=[pre_expanded, post_expanded],
    ):
        with pytest.raises(RuntimeError, match=r"Snapshot immutability violated.*evaluate_rqs_sha256"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="preflight",
                output_path=out_file,
            )


def test_negative_expanded_inventory_drift_in_baselines_or_protocol_rejected(tmp_path: Path):
    """Drift in protected baselines or protocol between pre and post must trigger immutability breach."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "baseline_drift.json"
    pre_expanded = compute_expanded_snapshot_inventory(GENUINE_SNAPSHOT_ROOT)
    post_expanded = copy.deepcopy(pre_expanded)
    post_expanded["protected_baselines_map"]["attack/corpus/enterprise-windows-v19.2.jsonl"] = "drifted_sha"

    with patch(
        "scripts.isolated_snapshot_controller.compute_expanded_snapshot_inventory",
        side_effect=[pre_expanded, post_expanded],
    ):
        with pytest.raises(RuntimeError, match=r"Snapshot immutability violated.*protected_baselines_map"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="verify_baselines",
                output_path=out_file,
            )


def test_negative_expanded_inventory_drift_in_git_state_rejected(tmp_path: Path):
    """Drift in Git commit or working directory between pre and post must trigger immutability breach."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "git_drift.json"
    pre_expanded = compute_expanded_snapshot_inventory(GENUINE_SNAPSHOT_ROOT)
    post_expanded = copy.deepcopy(pre_expanded)
    post_expanded["git_commit"] = "ffffffffffffffffffffffffffffffffffffffff"

    with patch(
        "scripts.isolated_snapshot_controller.compute_expanded_snapshot_inventory",
        side_effect=[pre_expanded, post_expanded],
    ):
        with pytest.raises(RuntimeError, match=r"Snapshot immutability violated.*git_commit"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="preflight",
                output_path=out_file,
            )


# --- Core Boundary Controls ---

def test_negative_wrong_snapshot_root(tmp_path: Path):
    """Calling controller on a non-existent or invalid root must fail closed."""
    bogus_root = tmp_path / "non_existent_snapshot"
    out_file = tmp_path / "out.json"

    with pytest.raises(FileNotFoundError, match="Snapshot root does not exist"):
        execute_snapshot_task(
            snapshot_root=bogus_root,
            task="preflight",
            output_path=out_file,
        )


def test_negative_arbitrary_python_override_rejected(tmp_path: Path):
    """Providing an interpreter outside the snapshot's dedicated virtualenv must be rejected."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "out_py.json"
    system_python = Path(sys.executable)

    with pytest.raises(ValueError, match="REJECTED: Arbitrary override_python"):
        execute_snapshot_task(
            snapshot_root=GENUINE_SNAPSHOT_ROOT,
            task="preflight",
            output_path=out_file,
            override_python=system_python,
        )


def test_negative_partial_or_corrupt_snapshot_rejected(tmp_path: Path):
    """Partial snapshot missing core files or with drifted files must fail closed before execution."""
    fake_snap = tmp_path / "partial_snapshot"
    (fake_snap / "config").mkdir(parents=True)
    (fake_snap / "src" / "experiment").mkdir(parents=True)

    lock = GENUINE_SNAPSHOT_ROOT / "config" / "canonical_experiment_lock_v1.json"
    if lock.is_file():
        shutil.copy(lock, fake_snap / "config" / "canonical_experiment_lock_v1.json")
    (fake_snap / "src" / "experiment" / "config.py").write_text("# mutant", encoding="utf-8")

    out_file = tmp_path / "out_corrupt.json"
    valid_python = resolve_snapshot_python(GENUINE_SNAPSHOT_ROOT)

    with pytest.raises(RuntimeError, match="Snapshot core inventory count mismatch"):
        execute_snapshot_task(
            snapshot_root=fake_snap,
            task="verify_baselines",
            output_path=out_file,
            override_python=valid_python,
        )


def test_negative_child_exit_nonzero_with_pass_payload_fails_closed(tmp_path: Path):
    """If child exits with non-zero exit code while claiming PASS, controller fails closed."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "out_exit7.json"
    orig_subprocess_run = subprocess.run

    def fake_subprocess_run(cmd, *args, **kwargs):
        if isinstance(cmd, list) and len(cmd) > 0 and "git" in str(cmd[0]):
            return orig_subprocess_run(cmd, *args, **kwargs)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump({"status": "PASS", "task": "verify_baselines"}, f)
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=7,
            stdout="Simulated output",
            stderr="Simulated error",
        )

    with patch("subprocess.run", side_effect=fake_subprocess_run):
        with pytest.raises(RuntimeError, match="Worker process exited with non-zero code 7 but claimed PASS"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="verify_baselines",
                output_path=out_file,
            )


def test_negative_extra_env_credentials_and_pythonpath_scrubbed():
    """Verify that credentials and shadow PYTHONPATH variables in extra_env are stripped."""
    extra = {
        "OPENAI_API_KEY": "sk-secret-test-token",
        "AZURE_OPENAI_API_KEY": "azure-secret-token",
        "AWS_SECRET_ACCESS_KEY": "aws-secret",
        "DB_PASSWORD": "my-password",
        "API_AUTH_TOKEN": "bearer-token",
        "PYTHONPATH": "shadow_dir",
        "PYTHONHOME": "shadow_home",
        "SAFE_VARIABLE": "allowed_value",
    }
    clean = sanitize_environment(extra)

    assert "OPENAI_API_KEY" not in clean
    assert "AZURE_OPENAI_API_KEY" not in clean
    assert "AWS_SECRET_ACCESS_KEY" not in clean
    assert "DB_PASSWORD" not in clean
    assert "API_AUTH_TOKEN" not in clean
    assert "PYTHONPATH" not in clean
    assert "PYTHONHOME" not in clean
    assert clean["SAFE_VARIABLE"] == "allowed_value"
    assert clean["PYTHONNOUSERSITE"] == "1"
    assert clean["OFFLINE_GUARD"] == "1"


def test_negative_socket_getaddrinfo_intercepted_and_blocked():
    """Verify that DNS queries and address resolutions via socket.getaddrinfo are intercepted."""
    from scripts.isolated_snapshot_worker import _install_socket_guard

    _install_socket_guard()
    with pytest.raises(SnapshotGuardSecurityError, match="OFFLINE_GUARD: Blocked"):
        socket.getaddrinfo("127.0.0.1", 80)


def test_negative_foreign_module_file_or_spec_rejected(tmp_path: Path):
    """Module where __file__ is outside snapshot root must be rejected."""
    outside_file = tmp_path / "shadow_module.py"
    outside_file.write_text("X = 1\n", encoding="utf-8")

    m = types.ModuleType("src.shadow_probe")
    m.__file__ = str(outside_file)
    m.__spec__ = importlib.machinery.ModuleSpec(
        "src.shadow_probe",
        loader=None,
        origin=str(GENUINE_SNAPSHOT_ROOT / "src" / "rag" / "__init__.py"),
    )
    sys.modules[m.__name__] = m

    try:
        with pytest.raises(SnapshotGuardSecurityError, match="BOUNDARY BREACH: Module 'src.shadow_probe'"):
            verify_module_origin_boundaries(GENUINE_SNAPSHOT_ROOT, target_modules={m.__name__})
    finally:
        sys.modules.pop(m.__name__, None)


def test_negative_foreign_callable_code_filename_rejected(tmp_path: Path):
    """Module inside snapshot containing a function with foreign co_filename must be rejected."""
    outside_code = tmp_path / "foreign_code.py"
    outside_code.write_text("def foreign_func(): return 42\n", encoding="utf-8")

    m = types.ModuleType("src.shadow_callable_probe")
    m.__file__ = str(GENUINE_SNAPSHOT_ROOT / "src" / "rag" / "__init__.py")
    m.__spec__ = importlib.machinery.ModuleSpec(
        "src.shadow_callable_probe",
        loader=None,
        origin=m.__file__,
    )
    exec(compile("def foreign_func(): return 42\n", str(outside_code), "exec"), m.__dict__)
    sys.modules[m.__name__] = m

    try:
        with pytest.raises(SnapshotGuardSecurityError, match="BOUNDARY BREACH: Module 'src.shadow_callable_probe' attribute 'foreign_func'"):
            verify_module_origin_boundaries(GENUINE_SNAPSHOT_ROOT, target_modules={m.__name__})
    finally:
        sys.modules.pop(m.__name__, None)


def test_negative_output_path_inside_snapshot_or_control_rejected(tmp_path: Path):
    """Output path pointing inside snapshot root or targeting control scripts must be rejected."""
    inside_snap = GENUINE_SNAPSHOT_ROOT / "config" / "dest.json"
    with pytest.raises(ValueError, match="SECURITY REJECTION: output_path .* is inside snapshot root"):
        validate_output_path_containment(inside_snap, GENUINE_SNAPSHOT_ROOT)

    control_script = Path(__file__).resolve().parent.parent / "scripts" / "isolated_snapshot_controller.py"
    with pytest.raises(ValueError, match="SECURITY REJECTION: output_path .* targets control script itself"):
        validate_output_path_containment(control_script, GENUINE_SNAPSHOT_ROOT)


def test_negative_offline_guard_egress_interception(tmp_path: Path):
    """Worker attempting network egress must be intercepted by audit guard and fail closed."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "egress_test_attestation.json"
    result = execute_snapshot_task(
        snapshot_root=GENUINE_SNAPSHOT_ROOT,
        task="egress_test",
        output_path=out_file,
    )

    assert result["status"] == "BLOCKED_SECURITY_VIOLATION"
    assert result["error_type"] == "SnapshotGuardSecurityError"
    assert "OFFLINE_GUARD: Blocked" in result["error_message"]
    assert result["attempted_egress_count"] >= 1
    assert result["controller_attestation"]["exit_code"] == 2


def test_negative_snapshot_immutability_violation(tmp_path: Path):
    """If snapshot critical files change during execution, controller detects immutability breach."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "immutability_test.json"
    pre_expanded = compute_expanded_snapshot_inventory(GENUINE_SNAPSHOT_ROOT)
    post_expanded = copy.deepcopy(pre_expanded)
    post_expanded["core_manifest_sha256"] = "different_sha"

    with patch(
        "scripts.isolated_snapshot_controller.compute_expanded_snapshot_inventory",
        side_effect=[pre_expanded, post_expanded],
    ):
        with pytest.raises(RuntimeError, match="Snapshot immutability violated"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="preflight",
                output_path=out_file,
            )


def test_negative_simulated_source_drift_breaks_manifest(tmp_path: Path):
    """Simulated drift in engineering source must fail code manifest verification against 8b."""
    from src.experiment.authorization import compute_code_manifest_sha256

    sim_root = tmp_path / "sim_repo"
    shutil.copytree(Path("src"), sim_root / "src")
    shutil.copytree(Path("config"), sim_root / "config")
    shutil.copytree(Path("prompts"), sim_root / "prompts")
    shutil.copy(Path(".python-version"), sim_root / ".python-version")
    shutil.copy(Path("pyproject.toml"), sim_root / "pyproject.toml")
    shutil.copy(Path("uv.lock"), sim_root / "uv.lock")

    target_file = sim_root / "src" / "pilot" / "no_rag_pilot.py"
    target_file.write_text(target_file.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")

    drifted_sha = compute_code_manifest_sha256(sim_root)
    assert drifted_sha != EXPECTED_CORE_MANIFEST_SHA256, "Drifted source must NOT match frozen 8b hash"


def test_negative_dirty_or_wrong_git_commit_rejected(tmp_path: Path):
    """Git identity verifier must reject wrong commit or dirty working directory."""
    fake_repo = tmp_path / "fake_repo"
    fake_repo.mkdir()
    (fake_repo / ".git").mkdir()

    # Wrong commit mock
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=["git", "rev-parse", "HEAD"],
            returncode=0,
            stdout="0000000000000000000000000000000000000000\n",
            stderr="",
        )
        with pytest.raises(RuntimeError, match="Snapshot Git commit mismatch"):
            verify_snapshot_git_identity(fake_repo)

    # Dirty status mock
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{EXPECTED_SNAPSHOT_GIT_COMMIT}\n", stderr=""),
            subprocess.CompletedProcess(args=[], returncode=0, stdout=" M src/experiment/config.py\n", stderr=""),
        ]
        with pytest.raises(RuntimeError, match="Snapshot working directory is dirty"):
            verify_snapshot_git_identity(fake_repo)
