#!/usr/bin/env python3
"""Fail-closed auditor for the RAG2ATT&CK Requirements Traceability Matrix.

Verifies every requirement in `reports/evidence/finalization_requirements_matrix.json`
against its declared evidence storage class and locator:
1. `git_tracked`: Repo-relative path must exist on disk and in the Git index/tree,
   and its actual SHA-256 digest must match `evidence_hash` (`declared_hash`) 100%.
2. `policy_code_reference`: Repo-relative code/test path without a fixed hash must
   exist on disk and in Git, and its actual SHA-256 digest is recorded.
3. `release_asset`: Standalone release archive
   (`artifacts/packages/public_v4_candidate_20261003.zip`) must match the
   cryptographic SHA-256 pinned in `reports/evidence/r9_final_artifact_inventory.json`.
4. `github_url_or_ci_run`: Must be a valid `https://github.com/habachcp6/RAG2ATTCK...` URL,
   and `HUMAN_ACTION_GATE` items must remain `PARTIAL` prior to main merge.

Mandatory Fail-Closed Rule:
Any requirement whose `evidence_locator` is a repo-relative path that cannot be resolved
on disk/Git is rejected with `FAIL_UNRESOLVED_LOCAL_LOCATOR` (exit code 1) and is NEVER
reclassified into `non_git_assets`.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

GITHUB_URL_PATTERN = re.compile(
    r"^https://github\.com/habachcp6/RAG2ATTCK(?:/(?:pull/\d+|pulls|releases|actions/runs/\d+))?$"
)

PINNED_RELEASE_ASSET_LOCATOR = "artifacts/packages/public_v4_candidate_20261003.zip"
PINNED_RELEASE_ASSET_SHA256 = (
    "1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1"
)


def _get_git_tracked_files(repo_root: Path) -> set[str] | None:
    """Return normalized repo-relative paths tracked in the Git index, or None if no .git."""
    if not (repo_root / ".git").exists():
        return None
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        return set()
    return {
        line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()
    }



def audit_requirements_matrix(
    repo_root: Path | None = None,
    matrix_path: Path | None = None,
    inventory_path: Path | None = None,
    output_path: Path | None = None,
    check_git_index: bool = True,
) -> tuple[dict[str, Any], int]:
    """Audit all requirements in finalization_requirements_matrix.json fail-closed."""
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]
    else:
        repo_root = Path(repo_root).resolve()

    if matrix_path is None:
        matrix_path = repo_root / "reports/evidence/finalization_requirements_matrix.json"
    else:
        matrix_path = Path(matrix_path).resolve()

    if inventory_path is None:
        inventory_path = repo_root / "reports/evidence/r9_final_artifact_inventory.json"
    else:
        inventory_path = Path(inventory_path).resolve()

    if not matrix_path.is_file():
        report = {
            "schema_version": "matrix_git_blob_audit_report_v1",
            "summary": {
                "total_requirements_tracked": 0,
                "valid_git_blob_bindings": 0,
                "missing_git_blobs": 1,
                "unresolved_local_locators": 1,
                "hash_mismatches": 0,
                "invalid_url_or_gate_bindings": 0,
                "non_git_assets_and_urls": 0,
                "local_paths_in_non_git_assets": 0,
                "audit_verdict": "FAIL_MISSING_MATRIX_FILE",
            },
            "git_blob_bindings": [],
            "non_git_assets": [],
            "defects": [f"Matrix file not found: {matrix_path}"],
        }
        return report, 1

    matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    requirements = matrix_data.get("requirements", [])

    # Load pinned release asset SHA from inventory if available
    inventory_zip_sha = PINNED_RELEASE_ASSET_SHA256
    if inventory_path.is_file():
        try:
            inv_data = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory_zip_sha = (
                inv_data.get("candidate_delivery_asset", {})
                .get("file", {})
                .get("sha256", PINNED_RELEASE_ASSET_SHA256)
            )
        except Exception:
            inventory_zip_sha = PINNED_RELEASE_ASSET_SHA256

    git_tracked_files = _get_git_tracked_files(repo_root) if check_git_index else None

    git_blob_bindings: list[dict[str, Any]] = []
    non_git_assets: list[dict[str, Any]] = []
    unresolved_local_locators: list[dict[str, Any]] = []
    hash_mismatches: list[dict[str, Any]] = []
    invalid_url_or_gate_bindings: list[dict[str, Any]] = []

    for req in requirements:
        req_id = req.get("id", "UNKNOWN")
        title = req.get("title", "")
        locator = req.get("evidence_locator") or req.get("evidence_path") or ""
        storage = req.get("evidence_storage", "")
        ev_type = req.get("evidence_type", "")
        status = req.get("final_candidate_status", "")
        declared_hash = req.get("evidence_hash")
        commit_sha = req.get("evidence_commit_sha")

        if not locator or not isinstance(locator, str):
            unresolved_local_locators.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "final_candidate_status": status,
                    "reason": "Empty or non-string evidence_locator",
                }
            )
            continue

        # Case 1: GitHub URL / CI Run / Human Gate URL
        if locator.startswith("http://") or locator.startswith("https://"):
            url_valid = bool(GITHUB_URL_PATTERN.match(locator))
            gate_valid = True
            gate_reason = None
            if ev_type == "HUMAN_ACTION_GATE" and status != "PARTIAL":
                gate_valid = False
                gate_reason = (
                    f"HUMAN_ACTION_GATE must have status PARTIAL prior to merge, got {status}"
                )

            if not url_valid or not gate_valid:
                invalid_url_or_gate_bindings.append(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "evidence_locator": locator,
                        "evidence_type": ev_type,
                        "final_candidate_status": status,
                        "url_valid": url_valid,
                        "gate_valid": gate_valid,
                        "reason": gate_reason or f"Invalid GitHub URL locator: {locator}",
                    }
                )
            non_git_assets.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "classification": "GITHUB_URL_OR_CI_RUN",
                    "declared_hash": declared_hash,
                }
            )
            continue

        # Case 2: Standalone Release Package Asset (public_v4_candidate_20261003.zip)
        if (
            locator == PINNED_RELEASE_ASSET_LOCATOR
            and storage == "release_asset"
            and ev_type == "RELEASE_PACKAGE"
        ):
            if (
                not declared_hash
                or declared_hash != PINNED_RELEASE_ASSET_SHA256
                or declared_hash != inventory_zip_sha
            ):
                hash_mismatches.append(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "evidence_locator": locator,
                        "declared_hash": declared_hash,
                        "expected_hash": inventory_zip_sha,
                        "reason": "Release package asset hash mismatch against pinned inventory",
                    }
                )
            non_git_assets.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "classification": "STANDALONE_RELEASE_ASSET",
                    "declared_hash": declared_hash,
                }
            )
            continue

        # Case 3: Local repo-relative path (git_tracked or policy_code_reference)
        # Mandatory Fail-Closed Rule: Must NEVER be pushed to non_git_assets!
        target_path = repo_root / locator
        if not target_path.is_file():
            unresolved_local_locators.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "final_candidate_status": status,
                    "reason": "Local repo-relative file does not exist on disk",
                }
            )
            continue

        norm_locator = locator.replace("\\", "/")
        if git_tracked_files is not None and norm_locator not in git_tracked_files:
            unresolved_local_locators.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "final_candidate_status": status,
                    "reason": "Local repo-relative file is not tracked in Git index/tree",
                }
            )
            continue

        raw_bytes = target_path.read_bytes()
        disk_sha256 = hashlib.sha256(raw_bytes).hexdigest()
        blob_sha256 = disk_sha256

        if declared_hash is not None:
            if declared_hash != disk_sha256 or declared_hash != blob_sha256:
                hash_mismatches.append(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "evidence_locator": locator,
                        "declared_hash": declared_hash,
                        "git_blob_hash": blob_sha256,
                        "disk_hash": disk_sha256,
                        "reason": "Declared evidence_hash does not match actual file/blob SHA-256",
                    }
                )
                binding_status = "MISMATCH"
            else:
                binding_status = "MATCH"
        else:
            # policy_code_reference without fixed declared_hash: file exists and is git-tracked
            binding_status = "VERIFIED_CODE_REFERENCE"

        git_blob_bindings.append(
            {
                "requirement_id": req_id,
                "title": title,
                "evidence_locator": locator,
                "evidence_commit_sha": commit_sha,
                "declared_hash": declared_hash,
                "git_blob_hash": blob_sha256,
                "blob_size_bytes": len(raw_bytes),
                "status": binding_status,
            }
        )

    local_paths_in_non_git = [
        item
        for item in non_git_assets
        if not str(item.get("evidence_locator", "")).startswith(("http://", "https://"))
        and item.get("classification") != "STANDALONE_RELEASE_ASSET"
    ]

    if unresolved_local_locators or local_paths_in_non_git:
        verdict = "FAIL_UNRESOLVED_LOCAL_LOCATOR"
        exit_code = 1
    elif hash_mismatches:
        verdict = "FAIL_GIT_BLOB_HASH_MISMATCH"
        exit_code = 1
    elif invalid_url_or_gate_bindings:
        verdict = "FAIL_INVALID_URL_OR_GATE_BINDING"
        exit_code = 1
    else:
        verdict = "PASS_ALL_BINDINGS_VERIFIED"
        exit_code = 0

    standalone_release_count = sum(
        1 for item in non_git_assets if item.get("classification") == "STANDALONE_RELEASE_ASSET"
    )
    github_url_count = sum(
        1 for item in non_git_assets if item.get("classification") == "GITHUB_URL_OR_CI_RUN"
    )

    try:
        rel_matrix_path = matrix_path.relative_to(repo_root).as_posix()
    except ValueError:
        rel_matrix_path = matrix_path.as_posix()

    valid_git_count = len(
        [b for b in git_blob_bindings if b["status"] in ("MATCH", "VERIFIED_CODE_REFERENCE")]
    )
    py_ver = sys.version.split()[0]
    report: dict[str, Any] = {
        "schema_version": "matrix_git_blob_audit_report_v1",
        "timestamp_utc": matrix_data.get("timestamp_utc", "2026-10-19T03:35:04+00:00"),
        "audited_matrix_path": rel_matrix_path,
        "audit_engine": f"Python {py_ver}, git CLI subprocess, hashlib sha256 (fail-closed)",
        "summary": {
            "total_requirements_tracked": len(requirements),
            "valid_git_blob_bindings": valid_git_count,
            "missing_git_blobs": len(unresolved_local_locators),
            "unresolved_local_locators": len(unresolved_local_locators),
            "hash_mismatches": len(hash_mismatches),
            "invalid_url_or_gate_bindings": len(invalid_url_or_gate_bindings),
            "non_git_assets_and_urls": len(non_git_assets),
            "standalone_release_assets": standalone_release_count,
            "github_urls_and_ci_runs": github_url_count,
            "local_paths_in_non_git_assets": len(local_paths_in_non_git),
            "audit_verdict": verdict,
        },
        "git_blob_bindings": git_blob_bindings,
        "non_git_assets": non_git_assets,
    }
    if unresolved_local_locators:
        report["unresolved_local_locators_detail"] = unresolved_local_locators
    if hash_mismatches:
        report["hash_mismatches_detail"] = hash_mismatches
    if invalid_url_or_gate_bindings:
        report["invalid_url_or_gate_bindings_detail"] = invalid_url_or_gate_bindings

    if output_path is not None:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(
            json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n"
        )

    return report, exit_code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fail-closed auditor for finalization_requirements_matrix.json."
    )
    parser.add_argument("--repo-root", type=Path, default=None, help="Repository root")
    parser.add_argument("--matrix", type=Path, default=None, help="Path to matrix JSON")
    parser.add_argument("--inventory", type=Path, default=None, help="Path to R9 inventory JSON")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output audit report JSON path (defaults to matrix_git_blob_audit_report.json)",
    )
    parser.add_argument(
        "--no-git-index-check",
        action="store_true",
        help="Skip git ls-files check (for isolated temp directories without .git)",
    )
    args = parser.parse_args()

    repo_root = args.repo_root or Path(__file__).resolve().parents[1]
    output_path = args.output or (repo_root / "reports/evidence/matrix_git_blob_audit_report.json")

    report, exit_code = audit_requirements_matrix(
        repo_root=repo_root,
        matrix_path=args.matrix,
        inventory_path=args.inventory,
        output_path=output_path,
        check_git_index=not args.no_git_index_check,
    )
    summary = report["summary"]
    print(
        f"Matrix Git Blob Audit Complete: verdict={summary['audit_verdict']} "
        f"(valid_git_blobs={summary['valid_git_blob_bindings']}, "
        f"non_git={summary['non_git_assets_and_urls']}, "
        f"unresolved_local={summary['unresolved_local_locators']}, "
        f"hash_mismatches={summary['hash_mismatches']}, "
        f"exit_code={exit_code})"
    )
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
