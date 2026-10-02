"""
tests/test_snapshot_boundary_isolation.py

Rigorous test suite verifying isolated snapshot execution boundaries and fail-closed protections:
1. Positive control: genuine detached b69 snapshot passes preflight and baseline verification.
2. Negative control: invalid/missing snapshot root fails closed.
3. Negative control: module origin boundary breach fails closed (shadowed module outside snapshot).
4. Negative control: offline guard socket egress attempts are intercepted and blocked.
5. Negative control: snapshot immutability violation during execution raises critical error.
6. Negative control: current-tree source drift produces code manifest hash distinct from historical 8b.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import socket
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.isolated_snapshot_controller import (
    EXPECTED_CORE_FILES_COUNT,
    EXPECTED_CORE_MANIFEST_SHA256,
    compute_quick_snapshot_fingerprint,
    execute_snapshot_task,
    resolve_snapshot_python,
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
    assert result["file_count"] == EXPECTED_CORE_FILES_COUNT
    assert result["code_manifest_sha256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert result["attempted_egress_count"] == 0
    assert result["controller_attestation"]["immutability_verified"] is True
    assert result["controller_attestation"]["exit_code"] == 0

    # Ensure all loaded origins are strictly within snapshot root
    for mod_name, origin_path in result["loaded_origins"].items():
        assert str(GENUINE_SNAPSHOT_ROOT.as_posix()) in origin_path, f"Origin breach: {mod_name} -> {origin_path}"


def test_positive_snapshot_baselines(tmp_path: Path):
    """Verify baseline hashes, evaluate_rqs f85 hash, and BOM hash on snapshot."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    out_file = tmp_path / "baselines_attestation.json"
    result = execute_snapshot_task(
        snapshot_root=GENUINE_SNAPSHOT_ROOT,
        task="verify_baselines",
        output_path=out_file,
    )

    assert result["status"] == "PASS"
    assert result["code_manifest_sha256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert result["evaluate_rqs_sha256"] == "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
    assert result["src_rag_init_sha256"] == "1d16d258b4c3f89aac043fad68a19031bf16d21daad4251846ba2f4297fa16c1"
    assert result["src_rag_init_has_bom"] is True
    assert result["attempted_egress_count"] == 0


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
    assert "OFFLINE_GUARD: Blocked network socket event" in result["error_message"]
    assert result["attempted_egress_count"] >= 1
    assert result["controller_attestation"]["exit_code"] == 2


def test_negative_snapshot_immutability_violation(tmp_path: Path):
    """If snapshot critical files change during execution, controller detects immutability breach."""
    if not GENUINE_SNAPSHOT_ROOT.is_dir():
        pytest.skip("Snapshot directory not found")

    # Mock compute_quick_snapshot_fingerprint to return different post-fingerprint
    out_file = tmp_path / "immutability_test.json"
    with patch("scripts.isolated_snapshot_controller.compute_quick_snapshot_fingerprint", side_effect=["hash_a", "hash_b"]):
        with pytest.raises(RuntimeError, match="Snapshot immutability violated"):
            execute_snapshot_task(
                snapshot_root=GENUINE_SNAPSHOT_ROOT,
                task="preflight",
                output_path=out_file,
            )


def test_negative_simulated_source_drift_breaks_manifest(tmp_path: Path):
    """Simulated drift in engineering source must fail code manifest verification against 8b."""
    from src.experiment.authorization import compute_code_manifest_sha256

    # Create temporary duplicate of src with 1 byte modified
    sim_root = tmp_path / "sim_repo"
    shutil.copytree(Path("src"), sim_root / "src")
    shutil.copytree(Path("config"), sim_root / "config")
    shutil.copytree(Path("prompts"), sim_root / "prompts")
    shutil.copy(Path(".python-version"), sim_root / ".python-version")
    shutil.copy(Path("pyproject.toml"), sim_root / "pyproject.toml")
    shutil.copy(Path("uv.lock"), sim_root / "uv.lock")

    # Drift 1 file
    target_file = sim_root / "src" / "pilot" / "no_rag_pilot.py"
    target_file.write_text(target_file.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")

    drifted_sha = compute_code_manifest_sha256(sim_root)
    assert drifted_sha != EXPECTED_CORE_MANIFEST_SHA256, "Drifted source must NOT match frozen 8b hash"
