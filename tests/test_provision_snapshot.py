"""
tests/test_provision_snapshot.py

Unit tests for portable snapshot provisioning helper (scripts/provision_snapshot.py):
1. Containment checks: target cannot be source_repo, ancestor, or descendant.
2. Fail-closed policy: existing foreign/dirty directories rejected without deletion.
3. Configured environment fail-closed checks: missing snapshot or missing .venv in CI fails closed.
4. Unconfigured local runner fallback skips cleanly with labeled scope.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.provision_snapshot import check_containment, provision_snapshot
from tests.test_snapshot_boundary_isolation import (
    extract_required_dependencies_from_uv_lock,
    require_genuine_snapshot,
    resolve_snapshot_python,
)


def test_containment_check_rejects_identical_path(tmp_path: Path):
    with pytest.raises(ValueError, match="conflicts with source repo"):
        check_containment(tmp_path, tmp_path)


def test_containment_check_rejects_ancestor_path(tmp_path: Path):
    source = tmp_path / "repo" / "sub"
    source.mkdir(parents=True)
    with pytest.raises(ValueError, match="conflicts with source repo"):
        check_containment(tmp_path, source)


def test_containment_check_rejects_descendant_path(tmp_path: Path):
    target = tmp_path / "repo" / "snapshot_target"
    target.mkdir(parents=True)
    with pytest.raises(ValueError, match="conflicts with source repo"):
        check_containment(target, tmp_path / "repo")


def test_fail_closed_on_dirty_or_foreign_existing_dir(tmp_path: Path):
    source_repo = tmp_path / "dummy_source"
    source_repo.mkdir()
    foreign_dir = tmp_path / "existing_foreign"
    foreign_dir.mkdir()
    sentinel = foreign_dir / "unrelated_file.txt"
    sentinel.write_text("user data")

    match_msg = "Target directory exists and is dirty/mismatched/foreign"
    with pytest.raises(RuntimeError, match=match_msg):
        provision_snapshot(target_dir=foreign_dir, source_repo=source_repo)

    # Must NOT have deleted or wiped the user directory
    assert foreign_dir.is_dir()
    assert sentinel.read_text() == "user data"


def test_fail_closed_on_corrupt_git_dir(tmp_path: Path):
    source_repo = tmp_path / "dummy_source"
    source_repo.mkdir(exist_ok=True)
    corrupt_dir = tmp_path / "corrupt_git"
    corrupt_dir.mkdir()
    (corrupt_dir / ".git").mkdir()

    match_msg = "Target directory exists and is dirty/mismatched/foreign"
    with pytest.raises(RuntimeError, match=match_msg):
        provision_snapshot(target_dir=corrupt_dir, source_repo=source_repo)

    assert corrupt_dir.is_dir()


def test_require_genuine_snapshot_fails_when_env_configured_and_dir_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    missing_dir = tmp_path / "non_existent_snapshot"
    monkeypatch.setenv("RAG2ATTCK_SNAPSHOT_ROOT", str(missing_dir))

    match_msg = "does not exist! Snapshot provisioning is mandatory"
    with pytest.raises(pytest.fail.Exception, match=match_msg):
        require_genuine_snapshot()


def test_require_genuine_snapshot_fails_when_env_configured_and_venv_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    snap_dir = tmp_path / "snap_without_venv"
    snap_dir.mkdir()
    monkeypatch.setenv("RAG2ATTCK_SNAPSHOT_ROOT", str(snap_dir))

    match_msg = "missing a valid dedicated .venv"
    with pytest.raises(pytest.fail.Exception, match=match_msg):
        require_genuine_snapshot()


def test_require_genuine_snapshot_skips_cleanly_when_unconfigured(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delenv("RAG2ATTCK_SNAPSHOT_ROOT", raising=False)
    with patch(
        "tests.test_snapshot_boundary_isolation.Path.is_dir",
        return_value=False,
    ):
        match_msg = "Local test skipped: RAG2ATTCK_SNAPSHOT_ROOT not configured"
        with pytest.raises(pytest.skip.Exception, match=match_msg):
            require_genuine_snapshot()


def test_negative_snapshot_integrity_mismatched_child_sys_prefix_rejected(
    tmp_path: Path,
):
    """
    Fail-closed gate: child process attesting sys.prefix outside snapshot venv
    (even with all required locked dependencies present) must be rejected.
    """
    snap_root = require_genuine_snapshot()
    required_deps = extract_required_dependencies_from_uv_lock(snap_root / "uv.lock")

    foreign_prefix = str((tmp_path / "foreign_venv").absolute())
    tampered_output = {
        "status": "PASS",
        "task": "verify_baselines",
        "offline_guard_installed": True,
        "attempted_egress_count": 0,
        "code_manifest_sha256": "8b512a84976cf36ff9c3a373fc3e04368cf1889c1df5c3a3885d519b5bfb75b9",
        "file_count": 53,
        "protected_baselines_verified_count": 22,
        "loaded_origins": {"src": str(snap_root / "src")},
        "loaded_origins_count": 1,
        "worker_runtime_attestation": {
            "sys_prefix": foreign_prefix,
            "sys_executable": str(resolve_snapshot_python(snap_root).absolute()),
            "installed_dependencies": dict(required_deps),
        },
        "controller_attestation": {
            "exit_code": 0,
        },
    }

    from scripts.provision_snapshot import (
        EXPECTED_SNAPSHOT_GIT_COMMIT,
        _verify_full_snapshot_integrity,
    )

    with patch(
        "scripts.isolated_snapshot_controller.execute_snapshot_task",
        return_value=tampered_output,
    ):
        with pytest.raises(RuntimeError, match="child sys.prefix .* does not match"):
            _verify_full_snapshot_integrity(snap_root, EXPECTED_SNAPSHOT_GIT_COMMIT)


def test_positive_snapshot_integrity_verification_on_genuine_snapshot():
    """Positive control: genuine snapshot passes full integrity gate with real child execution."""
    snap_root = require_genuine_snapshot()
    from scripts.provision_snapshot import (
        EXPECTED_SNAPSHOT_GIT_COMMIT,
        _verify_full_snapshot_integrity,
    )

    _verify_full_snapshot_integrity(snap_root, EXPECTED_SNAPSHOT_GIT_COMMIT)


def test_positive_snapshot_reuse_on_genuine_snapshot(monkeypatch: pytest.MonkeyPatch):
    """Positive control: reusing genuine valid snapshot returns cleanly without modification."""
    snap_root = require_genuine_snapshot()
    repo_root = Path(__file__).resolve().parent.parent

    # Prevent writing to GITHUB_ENV in test
    monkeypatch.delenv("GITHUB_ENV", raising=False)

    reused = provision_snapshot(target_dir=snap_root, source_repo=repo_root)
    assert reused == snap_root
