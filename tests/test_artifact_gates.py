"""
Tests for reusable artifact validation and pipeline gate enforcement.

These tests intentionally exercise bypass attempts: a downstream stage must not
run merely because a file with the expected name exists.
"""

import hashlib
import json
from pathlib import Path

import pytest

from src.artifacts import (
    ArtifactValidationError,
    validate_attack_manifest_artifact,
    validate_dataset_manifest_artifact,
    validate_stage_prerequisites,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_preflight_stop_artifact_cannot_unlock_acquisition(tmp_path):
    """A syntactically named preflight artifact with STOP status is not a valid T0 gate."""
    _write_json(
        tmp_path / "data" / "metadata" / "preflight.json",
        {
            "meta": {"schema_version": "1.0.0", "task": "T0_PREFLIGHT"},
            "gate_result": {"status": "STOP", "passed": False},
        },
    )

    with pytest.raises(ArtifactValidationError, match="T0_PREFLIGHT"):
        validate_stage_prerequisites(tmp_path, "acquire-dataset")


def test_dataset_manifest_hash_validation_rejects_modified_raw_file(tmp_path):
    """Dataset manifests must be tied to raw bytes, not trusted by filename alone."""
    raw_dir = tmp_path / "data" / "raw" / "windows_apt_2025" / "v3"
    raw_dir.mkdir(parents=True)
    raw_file = raw_dir / "one.csv"
    raw_file.write_text("id,value\n1,changed\n", encoding="utf-8")

    _write_json(
        tmp_path / "data" / "metadata" / "dataset_manifest.json",
        {
            "schema_version": "1.0.0",
            "dataset_id": "b8fmtzvpy8",
            "dataset_version": "3",
            "files": [
                {
                    "filename": "one.csv",
                    "role": "ingest_period_csv",
                    "size_bytes": raw_file.stat().st_size,
                    "sha256": hashlib.sha256(b"id,value\n1,original\n").hexdigest(),
                    "expected_sha256": hashlib.sha256(b"id,value\n1,original\n").hexdigest(),
                    "verified": True,
                }
            ],
        },
    )

    with pytest.raises(ArtifactValidationError, match="SHA-256"):
        validate_dataset_manifest_artifact(tmp_path)


def test_attack_manifest_integrity_rejects_corrupted_stix(tmp_path):
    """ATT&CK manifest validation must recompute the pinned raw STIX hash."""
    attack_dir = tmp_path / "attack" / "raw" / "enterprise-v19.2"
    attack_dir.mkdir(parents=True)
    stix_file = attack_dir / "enterprise-attack-19.2.json"
    stix_file.write_text("corrupted", encoding="utf-8")

    _write_json(
        tmp_path / "data" / "metadata" / "attack_manifest.json",
        {
            "schema_version": "1.0.0",
            "task": "T5_ACQUIRE_ATTACK_REFERENCE",
            "task_status": "PASS",
            "attack_version": "19.2",
            "immutable_git_commit": "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4",
            "expected_sha256": "0" * 64,
            "computed_sha256": "0" * 64,
            "sha256_verified": True,
            "stix_file": {
                "path": "attack/raw/enterprise-v19.2/enterprise-attack-19.2.json",
                "size_bytes": stix_file.stat().st_size,
                "sha256": "0" * 64,
            },
        },
    )

    with pytest.raises(ArtifactValidationError, match="SHA-256"):
        validate_attack_manifest_artifact(tmp_path)


def test_unresolved_task2_blocks_profile_in_production_workspace():
    """The frozen methodology requires STOP before T3 when T2 remains unresolved."""
    with pytest.raises(ArtifactValidationError, match="T2_MULTISET_RECONCILIATION"):
        validate_stage_prerequisites(Path("."), "profile")


def test_task4_stop_blocks_downstream_tasks(tmp_path):
    """A Task 4 STOP artifact must prevent T5-reconcile and T6+ execution."""
    _write_json(
        tmp_path / "data" / "metadata" / "gate_blocker_task4.json",
        {
            "schema_version": "1.0.0",
            "gate": "TASK_4_INDEPENDENT_GROUND_TRUTH",
            "status": "STOP",
            "blocker_reason": "No independent event-level lineage.",
        },
    )

    with pytest.raises(ArtifactValidationError, match="TASK_4_INDEPENDENT_GROUND_TRUTH"):
        validate_stage_prerequisites(tmp_path, "t6")
