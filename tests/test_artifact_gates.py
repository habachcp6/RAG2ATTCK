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


def _write_valid_preflight(ws: Path) -> None:
    """Minimal preflight artifact accepted by validate_preflight_artifact()."""
    _write_json(
        ws / "data" / "metadata" / "preflight.json",
        {
            "meta": {"schema_version": "1.0.0", "task": "T0_PREFLIGHT"},
            "gate_result": {"status": "PASS", "passed": True},
            "path_validation": {"all_paths_contained": True},
            "capacity_assessment": {"capacity_sufficient": True},
            "source_context": {"verification_status": "VERIFIED_CANONICAL_PRESERVED"},
        },
    )


def _write_valid_dataset_manifest(ws: Path) -> None:
    """Tiny deterministic CSV + valid manifest accepted by validate_dataset_manifest_artifact().

    Uses 18-byte synthetic bytes — the validator cares about manifest↔raw-bytes
    integrity, not that the file is the real 480 MB dataset.
    """
    raw_dir = ws / "data" / "raw" / "windows_apt_2025" / "v3"
    raw_dir.mkdir(parents=True)
    content = b"id,value\n1,test\n"
    raw_file = raw_dir / "period.csv"
    raw_file.write_bytes(content)
    digest = hashlib.sha256(content).hexdigest()
    _write_json(
        ws / "data" / "metadata" / "dataset_manifest.json",
        {
            "schema_version": "1.0.0",
            "dataset_id": "b8fmtzvpy8",
            "dataset_version": "3",
            "files": [
                {
                    "filename": "period.csv",
                    "role": "ingest_period_csv",
                    "size_bytes": len(content),
                    "sha256": digest,
                    "expected_sha256": digest,
                    "verified": True,
                }
            ],
        },
    )


def _write_unresolved_reconciliation(ws: Path) -> None:
    """Structurally valid reconciliation log that is intentionally unresolved.

    This causes validate_reconciliation_artifact(..., require_resolved=True) to raise
    ArtifactValidationError matching 'T2_MULTISET_RECONCILIATION'.
    """
    _write_json(
        ws / "data" / "metadata" / "reconciliation_log.json",
        {
            "schema_version": "1.0.0",
            "task": "T2_MULTISET_RECONCILIATION",
            "row_count_accounting": {"row_counts_match": True},
            "multiset_equality_status": "RECONCILIATION_DIVERGENT",
            "is_exact_match": False,
            "semantic_reconciliation_status": "UNRESOLVED",
            "representation_equivalence_resolved": False,
        },
    )


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


def test_unresolved_task2_blocks_profile(tmp_path):
    """T2 reconciliation unresolved must block validate_stage_prerequisites('profile').

    The controlled workspace has valid T0 preflight and T2 dataset manifest so
    that the validator reaches the reconciliation gate — the intended failure point.
    """
    _write_valid_preflight(tmp_path)
    _write_valid_dataset_manifest(tmp_path)
    _write_unresolved_reconciliation(tmp_path)

    with pytest.raises(ArtifactValidationError, match="T2_MULTISET_RECONCILIATION"):
        validate_stage_prerequisites(tmp_path, "profile")


def test_unresolved_task2_blocks_audit_gt(tmp_path):
    """T2 reconciliation unresolved must block validate_stage_prerequisites('audit-gt').

    Same setup as above; verifies the gate also applies to the audit-gt stage.
    """
    _write_valid_preflight(tmp_path)
    _write_valid_dataset_manifest(tmp_path)
    _write_unresolved_reconciliation(tmp_path)

    with pytest.raises(ArtifactValidationError, match="T2_MULTISET_RECONCILIATION"):
        validate_stage_prerequisites(tmp_path, "audit-gt")


def test_filename_only_fake_prerequisite_cannot_bypass_gate(tmp_path):
    """Creating an empty or invalid file with the expected filename cannot bypass the gate."""
    meta_dir = tmp_path / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    # Write a dummy empty or malformed preflight.json
    (meta_dir / "preflight.json").write_text("{}", encoding="utf-8")

    with pytest.raises(ArtifactValidationError):
        validate_stage_prerequisites(tmp_path, "acquire-dataset")

    # Write a file that has schema_version but not PASS status
    (meta_dir / "preflight.json").write_text('{"schema_version": "1.0.0", "task": "T0_PREFLIGHT"}', encoding="utf-8")
    with pytest.raises(ArtifactValidationError):
        validate_stage_prerequisites(tmp_path, "acquire-dataset")


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
        validate_stage_prerequisites(tmp_path, "t5-reconcile")

    with pytest.raises(ArtifactValidationError, match="TASK_4_INDEPENDENT_GROUND_TRUTH"):
        validate_stage_prerequisites(tmp_path, "t6")

