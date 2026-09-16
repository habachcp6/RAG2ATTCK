"""
Reusable artifact validators for the staged Data & Ground Truth pipeline.

The validators are intentionally stricter than file-existence checks: they
verify task identity, schema/status fields, raw-byte hashes, and STOP gates
before a later stage can execute.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


class ArtifactValidationError(RuntimeError):
    """Raised when a pipeline artifact does not satisfy a required gate."""


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _metadata_dir(workspace_root: Path) -> Path:
    return workspace_root.resolve() / "data" / "metadata"


def _load_json(path: Path, artifact_name: str) -> Dict[str, Any]:
    if not path.exists():
        raise ArtifactValidationError(f"{artifact_name} artifact is missing: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise ArtifactValidationError(f"{artifact_name} artifact is not valid JSON: {path}") from exc
    if not isinstance(data, dict):
        raise ArtifactValidationError(f"{artifact_name} artifact must be a JSON object: {path}")
    return data


def _require(condition: bool, artifact_name: str, message: str) -> None:
    if not condition:
        raise ArtifactValidationError(f"{artifact_name}: {message}")


def _require_schema(doc: Dict[str, Any], artifact_name: str, expected_task: str | None = None) -> None:
    schema_version = doc.get("schema_version") or doc.get("meta", {}).get("schema_version")
    task = doc.get("task") or doc.get("meta", {}).get("task")
    _require(schema_version == "1.0.0", artifact_name, "expected schema_version 1.0.0")
    if expected_task is not None:
        _require(task == expected_task, artifact_name, f"expected task {expected_task}, got {task!r}")


def _safe_child(workspace_root: Path, relative_path: str) -> Path:
    ws = workspace_root.resolve()
    target = (ws / relative_path).resolve()
    if not target.is_relative_to(ws):
        raise ArtifactValidationError(f"path escapes workspace: {relative_path}")
    return target


def validate_preflight_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T0_PREFLIGHT"
    doc = _load_json(_metadata_dir(workspace_root) / "preflight.json", artifact_name)
    _require_schema(doc, artifact_name, "T0_PREFLIGHT")
    gate = doc.get("gate_result", {})
    _require(gate.get("status") == "PASS" and gate.get("passed") is True, artifact_name, "gate_result must be PASS")
    _require(doc.get("path_validation", {}).get("all_paths_contained") is True, artifact_name, "workspace paths are not all contained")
    _require(doc.get("capacity_assessment", {}).get("capacity_sufficient") is True, artifact_name, "capacity gate did not pass")
    _require(
        doc.get("source_context", {}).get("verification_status") == "VERIFIED_CANONICAL_PRESERVED",
        artifact_name,
        "source context is not verified",
    )
    return doc


def validate_dataset_manifest_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T2_DATASET_MANIFEST"
    ws = workspace_root.resolve()
    raw_dir = ws / "data" / "raw" / "windows_apt_2025" / "v3"
    doc = _load_json(_metadata_dir(ws) / "dataset_manifest.json", artifact_name)
    _require_schema(doc, artifact_name)
    _require(doc.get("dataset_id") == "b8fmtzvpy8", artifact_name, "unexpected dataset_id")
    _require(str(doc.get("dataset_version")) == "3", artifact_name, "unexpected dataset_version")
    files = doc.get("files")
    _require(isinstance(files, list) and files, artifact_name, "files list is empty or missing")

    ingest_count = 0
    for entry in files:
        _require(isinstance(entry, dict), artifact_name, "manifest file entry is not an object")
        filename = entry.get("filename")
        _require(isinstance(filename, str) and filename, artifact_name, "file entry missing filename")
        file_path = (raw_dir / filename).resolve()
        _require(file_path.is_relative_to(raw_dir.resolve()), artifact_name, f"file path escapes raw directory: {filename}")
        _require(file_path.exists(), artifact_name, f"raw file is missing: {filename}")

        expected_size = entry.get("size_bytes")
        if expected_size is not None:
            _require(file_path.stat().st_size == expected_size, artifact_name, f"size mismatch for {filename}")

        actual_sha = sha256_file(file_path)
        for key in ("sha256", "expected_sha256"):
            expected_sha = entry.get(key)
            if expected_sha:
                _require(actual_sha == expected_sha, artifact_name, f"SHA-256 mismatch for {filename} ({key})")
        if "verified" in entry:
            _require(entry["verified"] is True, artifact_name, f"manifest entry is not verified: {filename}")
        if entry.get("role") == "ingest_period_csv":
            ingest_count += 1

    _require(ingest_count > 0, artifact_name, "no ingest_period_csv files are declared")
    return doc


def validate_reconciliation_artifact(workspace_root: Path, require_resolved: bool = False) -> Dict[str, Any]:
    artifact_name = "T2_MULTISET_RECONCILIATION"
    doc = _load_json(_metadata_dir(workspace_root) / "reconciliation_log.json", artifact_name)
    _require_schema(doc, artifact_name, "T2_MULTISET_RECONCILIATION")
    row_accounting = doc.get("row_count_accounting", {})
    _require(row_accounting.get("row_counts_match") is True, artifact_name, "row counts do not match")

    exact = doc.get("multiset_equality_status") == "RECONCILED_EXACT_MATCH" and doc.get("is_exact_match") is True
    semantic_resolved = (
        doc.get("semantic_reconciliation_status") == "RESOLVED_REPRESENTATION_EQUIVALENT"
        and doc.get("representation_equivalence_resolved") is True
    )
    if require_resolved:
        _require(exact or semantic_resolved, artifact_name, "unresolved representation discrepancies block downstream execution")
    return doc


def validate_schema_profile_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T3_SCHEMA_PROFILING"
    doc = _load_json(_metadata_dir(workspace_root) / "schema_profile.json", artifact_name)
    _require_schema(doc, artifact_name, "T3_SCHEMA_PROFILING")
    _require(doc.get("accounting_invariant_holds") is True, artifact_name, "parse accounting invariant failed")
    _require(doc.get("source_logical_rows") == doc.get("successfully_parsed_records") + doc.get("rejected_malformed_records"), artifact_name, "row accounting mismatch")
    return doc


def validate_record_index_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T3_RECORD_INDEX"
    ws = workspace_root.resolve()
    doc = _load_json(_metadata_dir(ws) / "record_index.json", artifact_name)
    _require_schema(doc, artifact_name, "T3_RECORD_INDEX")
    index_path = _safe_child(ws, doc.get("index_file_relative_path", ""))
    _require(index_path.exists(), artifact_name, "record_index.csv is missing")
    _require(index_path.stat().st_size == doc.get("index_file_size_bytes"), artifact_name, "record_index.csv size mismatch")
    _require(sha256_file(index_path) == doc.get("index_file_sha256"), artifact_name, "record_index.csv SHA-256 mismatch")
    return doc


def validate_parse_error_ledger_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T3_PARSE_ERROR_LEDGER"
    doc = _load_json(_metadata_dir(workspace_root) / "parse_error_ledger.json", artifact_name)
    _require_schema(doc, artifact_name)
    _require(doc.get("accounting_invariant_holds") is True, artifact_name, "parse accounting invariant failed")
    _require(doc.get("source_logical_rows") == doc.get("successfully_parsed_records") + doc.get("rejected_malformed_records"), artifact_name, "row accounting mismatch")
    return doc


def validate_attack_manifest_artifact(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "T5_ACQUIRE_ATTACK_REFERENCE"
    ws = workspace_root.resolve()
    doc = _load_json(_metadata_dir(ws) / "attack_manifest.json", artifact_name)
    _require_schema(doc, artifact_name, "T5_ACQUIRE_ATTACK_REFERENCE")
    _require(doc.get("task_status") == "PASS", artifact_name, "task_status must be PASS")
    _require(doc.get("attack_version") == "19.2", artifact_name, "unexpected ATT&CK version")
    _require(doc.get("sha256_verified") is True, artifact_name, "manifest does not declare SHA-256 verification")

    stix = doc.get("stix_file", {})
    stix_path = _safe_child(ws, stix.get("path", ""))
    _require(stix_path.exists(), artifact_name, "raw STIX file is missing")
    _require(stix_path.stat().st_size == stix.get("size_bytes"), artifact_name, "raw STIX size mismatch")
    actual_sha = sha256_file(stix_path)
    _require(actual_sha == stix.get("sha256"), artifact_name, "raw STIX SHA-256 mismatch")
    _require(actual_sha == doc.get("computed_sha256"), artifact_name, "computed SHA-256 does not match raw STIX")
    _require(actual_sha == doc.get("expected_sha256"), artifact_name, "expected SHA-256 does not match raw STIX")
    return doc


def validate_task4_gate_for_downstream(workspace_root: Path) -> Dict[str, Any]:
    artifact_name = "TASK_4_INDEPENDENT_GROUND_TRUTH"
    doc = _load_json(_metadata_dir(workspace_root) / "gate_blocker_task4.json", artifact_name)
    _require_schema(doc, artifact_name)
    if doc.get("status") == "STOP":
        raise ArtifactValidationError(f"{artifact_name}: STOP gate blocks downstream execution")
    _require(doc.get("status") == "PASS", artifact_name, "expected PASS gate before downstream execution")
    return doc


def validate_stage_prerequisites(workspace_root: Path, stage: str) -> None:
    """
    Validate the executable predecessor gates for a CLI stage.
    """
    ws = workspace_root.resolve()
    stage_key = stage.lower().replace("_", "-")

    if stage_key in {"t5-reconcile", "t6", "t7", "t8", "t9", "t10", "t11"}:
        blocker_path = _metadata_dir(ws) / "gate_blocker_task4.json"
        if blocker_path.exists():
            validate_task4_gate_for_downstream(ws)

    if stage_key in {"acquire-dataset", "acquire-attack"}:
        validate_preflight_artifact(ws)
        return

    if stage_key == "reconcile":
        validate_preflight_artifact(ws)
        validate_dataset_manifest_artifact(ws)
        return

    if stage_key == "profile":
        validate_preflight_artifact(ws)
        validate_dataset_manifest_artifact(ws)
        validate_reconciliation_artifact(ws, require_resolved=True)
        return

    if stage_key == "audit-gt":
        validate_preflight_artifact(ws)
        validate_dataset_manifest_artifact(ws)
        validate_reconciliation_artifact(ws, require_resolved=True)
        validate_schema_profile_artifact(ws)
        validate_record_index_artifact(ws)
        validate_parse_error_ledger_artifact(ws)
        return

    if stage_key in {"t5-reconcile", "t6", "t7", "t8", "t9", "t10", "t11"}:
        validate_preflight_artifact(ws)
        validate_dataset_manifest_artifact(ws)
        validate_reconciliation_artifact(ws, require_resolved=True)
        validate_schema_profile_artifact(ws)
        validate_record_index_artifact(ws)
        validate_parse_error_ledger_artifact(ws)
        validate_task4_gate_for_downstream(ws)
        if stage_key != "t5-reconcile":
            validate_attack_manifest_artifact(ws)
        return

    raise ArtifactValidationError(f"Unknown pipeline stage: {stage}")
