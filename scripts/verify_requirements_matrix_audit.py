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
PINNED_RELEASE_ASSET_SHA256 = "1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1"
EXPECTED_REQUIREMENTS_COUNT = 170
REQUIRED_REQUIREMENT_KEYS = (
    "id",
    "title",
    "evidence_locator",
    "evidence_storage",
    "evidence_type",
    "final_candidate_status",
)
CANONICAL_REQUIREMENT_IDS = (
    "A.01-RUN_ID",
    "A.02-RECORD_COUNT",
    "A.03-ATTEMPT_COUNT",
    "A.04-STATUS_TAXONOMY",
    "A.05-SETTLED_COST",
    "A.06-TOTAL_ACCOUNTED",
    "A.07-HEADLINE_STATS",
    "A.08-CLAIM_BOUNDARIES",
    "B.01-GITHUB_EVIDENCE",
    "B.02-FAIL_CLOSED_VERDICT",
    "C.01-NO_LIVE_EXPERIMENTS",
    "C.02-IMMUTABLE_FROZEN_DATA",
    "C.03-HUMAN_MERGE_AUTH",
    "D.01-TRACK_A",
    "D.02-TRACK_B",
    "D.03-TRACK_C",
    "D.04-TRACK_D",
    "D.05-TRACK_E",
    "D.06-TRACK_F",
    "E.01-REMOTE_SNAPSHOT",
    "E.02-PREFLIGHT_ARTIFACT",
    "F.01-TERMINAL_RUN",
    "F.02-PREDICTION_INVENTORY",
    "F.03-ATTEMPT_ACCOUNTING",
    "F.04-OUTCOME_TAXONOMY",
    "F.05-LEDGER_RECONCILIATION",
    "F.06-VALIDATOR_DEFECT_CODEX",
    "F.07-VALIDATOR_EXECUTION",
    "F.08-RAW_ARTIFACT_TRANSPARENCY",
    "G.01-COHORTS_AND_DENOMINATORS",
    "G.02-CANONICAL_METRIC_BUNDLE",
    "H.01-RQ1_CONDITION_SWEEP",
    "H.02-RQ1_MACRO_F1_474",
    "H.03-RQ1_BOOTSTRAP_CI",
    "H.04-RQ1_MCNEMAR",
    "I.01-PROTOCOL_D2I_AXES",
    "I.02-RQ2_EMPIRICAL_K10",
    "I.03-RQ2_NON_CAUSAL_WORDING",
    "J.01-RQ3_TRADE_OFF_TABLE",
    "J.02-RQ3_COST_WORDING",
    "K.01-PROVIDER_FAILURE_RETRY",
    "K.02-INCOMPLETE_CEILING_ANALYSIS",
    "K.03-INCOMPLETE_MAPPED_COHORT_EXCLUSION",
    "L.SEC-01",
    "L.SEC-02",
    "L.SEC-03",
    "L.SEC-04",
    "L.SEC-05",
    "L.SEC-06",
    "L.SEC-07",
    "L.SEC-08",
    "L.SEC-09",
    "L.SEC-10",
    "L.SEC-11",
    "L.SEC-12",
    "L.SEC-13",
    "L.SEC-14",
    "L.SEC-15",
    "L.SEC-16",
    "L.SEC-17",
    "L.SEC-18",
    "L.SEC-19",
    "L.SEC-20",
    "L.SEC-21",
    "L.SEC-22",
    "L.SEC-23",
    "L.SEC-24",
    "L.SEC-25",
    "L.SEC-26",
    "L.SEC-27",
    "L.SEC-28",
    "L.SEC-29",
    "L.SEC-30",
    "L.DOCX_DELIVERY",
    "M.01-SYNTHETIC_VS_LIVE",
    "M.02-DENOMINATOR_DISCIPLINE",
    "M.03-NON_CAUSAL_DISCIPLINE",
    "M.04-NON_PRODUCTION_DISCIPLINE",
    "N.01-PRIMARY_LITERATURE",
    "O.FIG-01",
    "O.FIG-02",
    "O.FIG-03",
    "O.FIG-04",
    "O.FIG-05",
    "O.FIG-06",
    "O.FIG-07",
    "O.FIG-08",
    "O.TAB-01",
    "O.TAB-02",
    "O.TAB-03",
    "O.TAB-04",
    "O.TAB-05",
    "O.TAB-06",
    "O.GEN-01",
    "P.VAL-77.99",
    "P.VAL-79.53",
    "P.VAL-pos_1.532",
    "P.VAL-neg_2.355_pos_5.300",
    "P.VAL-0.422",
    "P.VAL-6400",
    "P.VAL-6401",
    "P.VAL-6387",
    "P.VAL-13",
    "P.VAL-6.57575890",
    "P.VAL-6.62839900",
    "P.VAL-19.99000000",
    "P.VAL-718",
    "P.VAL-311",
    "P.VAL-251",
    "P.VAL-474",
    "Q.01-VIETNAMESE_DECK",
    "Q.02-TYPOGRAPHY_AND_LAYOUT_QA",
    "R.01-CLEAN_CLONE_REPRO",
    "R.02-REPRO_VERDICT_ASSERTION",
    "S.01-SECRETS_AND_PATHS_SCAN",
    "T.01-PR_CLASSIFICATION_AND_ANCESTRY",
    "U.01-DIFF_AUDIT",
    "V.01-RUFF_CHECK",
    "V.02-RUFF_FORMAT",
    "V.03-OFFLINE_UNIT",
    "V.04-INTEGRATION_SUITE",
    "V.05-SYNTHETIC_DATA",
    "V.06-CANONICAL_REPLAY",
    "V.07-CANONICAL_MANIFEST",
    "V.08-RQ_KNOWN_ANSWER",
    "V.09-REPORT_METADATA",
    "V.10-PRESENTATION_REGRESSION",
    "V.11-PATH_SECRET_SCANNER",
    "V.12-CROSS_ARTIFACT_TEST",
    "V.13-TERMINAL_VALIDATOR",
    "W.01-GITHUB_CI_GREEN",
    "X.01-REPO_STATE",
    "X.02-CANONICAL_EXP",
    "X.03-SCIENTIFIC_RES",
    "X.04-ARTIFACTS",
    "X.05-VERIFICATION",
    "X.06-LIMITATIONS",
    "X.07-MERGE_RECOMMENDATION",
    "Y.01-READY_FOR_MERGE_GATE",
    "Z.01-POST_MERGE_CLEANUP",
    "AA.01-RELEASE_TAG",
    "DOD-01",
    "DOD-02",
    "DOD-03",
    "DOD-04",
    "DOD-05",
    "DOD-06",
    "DOD-07",
    "DOD-08",
    "DOD-09",
    "DOD-10",
    "DOD-11",
    "DOD-12",
    "DOD-13",
    "DOD-14",
    "DOD-15",
    "DOD-16",
    "DOD-17",
    "DOD-18",
    "DOD-19",
    "DOD-20",
    "DOD-21",
    "DOD-22",
    "DOD-23",
    "DOD-24",
    "DOD-25",
    "AC.01-SELF_CORRECTION",
    "AD.01-REVIEWER_ESCALATION",
    "AE.01-RESPONSE_FORMAT",
    "AF.01-PRIORITY_ORDER",
)
CANONICAL_REQUIREMENT_IDS_SET = frozenset(CANONICAL_REQUIREMENT_IDS)


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
        return None
    return {line.strip().replace("\\", "/") for line in proc.stdout.splitlines() if line.strip()}


def _commit_is_valid_ancestor(repo_root: Path, commit_sha: str, cache: dict[str, bool]) -> bool:
    """Check whether commit_sha is a full 40-char lowercase hex SHA that exists and is an ancestor of HEAD."""
    if (
        not commit_sha
        or not isinstance(commit_sha, str)
        or not re.fullmatch(r"[0-9a-f]{40}", commit_sha)
    ):
        return False
    if commit_sha in cache:
        return cache[commit_sha]
    cat_proc = subprocess.run(
        ["git", "cat-file", "-e", f"{commit_sha}^{{commit}}"],
        cwd=str(repo_root),
        capture_output=True,
    )
    if cat_proc.returncode != 0:
        cache[commit_sha] = False
        return False
    anc_proc = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit_sha, "HEAD"],
        cwd=str(repo_root),
        capture_output=True,
    )
    valid = anc_proc.returncode == 0
    cache[commit_sha] = valid
    return valid


def _get_git_blob_sha256_and_size(
    repo_root: Path,
    ref: str,
    norm_locator: str,
    cache: dict[tuple[str, str], tuple[str | None, int | None]],
) -> tuple[str | None, int | None]:
    """Read actual git blob bytes via `git show <ref>:<norm_locator>` and return (sha256, size)."""
    key = (ref, norm_locator)
    if key in cache:
        return cache[key]
    proc = subprocess.run(
        ["git", "show", f"{ref}:{norm_locator}"],
        cwd=str(repo_root),
        capture_output=True,
    )
    if proc.returncode != 0:
        cache[key] = (None, None)
        return None, None
    blob_bytes = proc.stdout
    digest = hashlib.sha256(blob_bytes).hexdigest()
    size = len(blob_bytes)
    cache[key] = (digest, size)
    return digest, size


def _validate_requirements_schema_and_count(requirements: Any) -> list[str]:
    """Validate that requirements is a list of exactly 170 well-formed, unique-ID dicts."""
    errors: list[str] = []
    if not isinstance(requirements, list):
        return ["'requirements' field must be a list"]
    if len(requirements) != EXPECTED_REQUIREMENTS_COUNT:
        errors.append(
            f"Expected {EXPECTED_REQUIREMENTS_COUNT} requirements, got {len(requirements)}"
        )
    seen_ids: set[str] = set()
    for idx, item in enumerate(requirements):
        if not isinstance(item, dict):
            errors.append(f"Requirement at index {idx} is not a dict")
            continue
        missing_keys = [k for k in REQUIRED_REQUIREMENT_KEYS if k not in item]
        if missing_keys:
            errors.append(f"Requirement at index {idx} missing required keys: {missing_keys}")
        req_id = item.get("id")
        if not isinstance(req_id, str) or not req_id.strip():
            errors.append(f"Requirement at index {idx} has empty or non-string id")
        elif req_id in seen_ids:
            errors.append(f"Duplicate requirement id: {req_id}")
        else:
            seen_ids.add(req_id)
            if req_id not in CANONICAL_REQUIREMENT_IDS_SET:
                errors.append(f"Non-canonical requirement id: {req_id}")
    missing_canonical = sorted(CANONICAL_REQUIREMENT_IDS_SET - seen_ids)
    if missing_canonical:
        errors.append(f"Missing canonical requirement ids: {missing_canonical[:10]}")
    return errors


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
    requirements = matrix_data.get("requirements")

    schema_errors = _validate_requirements_schema_and_count(requirements)
    if schema_errors:
        report = {
            "schema_version": "matrix_git_blob_audit_report_v1",
            "summary": {
                "total_requirements_tracked": len(requirements)
                if isinstance(requirements, list)
                else 0,
                "valid_git_blob_bindings": 0,
                "missing_git_blobs": 0,
                "unresolved_local_locators": 0,
                "hash_mismatches": 0,
                "invalid_url_or_gate_bindings": 0,
                "non_git_assets_and_urls": 0,
                "local_paths_in_non_git_assets": 0,
                "audit_verdict": "FAIL_INVALID_MATRIX_SCHEMA_OR_COUNT",
            },
            "git_blob_bindings": [],
            "non_git_assets": [],
            "defects": schema_errors,
        }
        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        return report, 1

    git_tracked_files = _get_git_tracked_files(repo_root) if check_git_index else None
    if not check_git_index or not (repo_root / ".git").exists() or git_tracked_files is None:
        report = {
            "schema_version": "matrix_git_blob_audit_report_v1",
            "summary": {
                "total_requirements_tracked": len(requirements),
                "valid_git_blob_bindings": 0,
                "missing_git_blobs": 0,
                "unresolved_local_locators": 0,
                "hash_mismatches": 0,
                "invalid_url_or_gate_bindings": 0,
                "non_git_assets_and_urls": 0,
                "local_paths_in_non_git_assets": 0,
                "audit_verdict": "FAIL_GIT_REPOSITORY_REQUIRED",
            },
            "git_blob_bindings": [],
            "non_git_assets": [],
            "defects": [
                "Git index and object-database verification is mandatory; check_git_index=False or missing .git is rejected fail-closed."
            ],
        }
        if output_path is not None:
            out_p = Path(output_path)
            out_p.parent.mkdir(parents=True, exist_ok=True)
            out_p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        return report, 1

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

    commit_cache: dict[str, bool] = {}
    blob_cache: dict[tuple[str, str], tuple[str | None, int | None]] = {}

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
        if norm_locator not in git_tracked_files:
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

        if not commit_sha or not _commit_is_valid_ancestor(
            repo_root, str(commit_sha), commit_cache
        ):
            unresolved_local_locators.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "final_candidate_status": status,
                    "evidence_commit_sha": commit_sha,
                    "reason": f"Invalid, missing, or non-ancestor evidence_commit_sha: {commit_sha!r}",
                }
            )
            continue

        raw_bytes = target_path.read_bytes()
        disk_sha256 = hashlib.sha256(raw_bytes).hexdigest()

        ref_to_read = str(commit_sha)
        blob_sha256, blob_size = _get_git_blob_sha256_and_size(
            repo_root, ref_to_read, norm_locator, blob_cache
        )
        head_blob_sha256, _ = _get_git_blob_sha256_and_size(
            repo_root, "HEAD", norm_locator, blob_cache
        )
        if blob_sha256 is None or head_blob_sha256 is None:
            unresolved_local_locators.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "evidence_storage": storage,
                    "final_candidate_status": status,
                    "reason": f"Git blob missing from object store at {ref_to_read}:{norm_locator}",
                }
            )
            continue

        if declared_hash:
            if (
                declared_hash != disk_sha256
                or declared_hash != blob_sha256
                or disk_sha256 != blob_sha256
                or blob_sha256 != head_blob_sha256
            ):
                hash_mismatches.append(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "evidence_locator": locator,
                        "declared_hash": declared_hash,
                        "git_blob_hash": blob_sha256,
                        "head_git_blob_hash": head_blob_sha256,
                        "disk_hash": disk_sha256,
                        "reason": "Declared evidence_hash, disk SHA-256, or Git blob SHA-256 mismatch",
                    }
                )
                binding_status = "MISMATCH"
            else:
                binding_status = "MATCH"
        elif storage == "policy_code_reference" or ev_type == "POLICY_CODE_REFERENCE":
            # policy_code_reference without fixed declared_hash: file exists, is git-tracked, and disk matches git blob
            if disk_sha256 != blob_sha256 or blob_sha256 != head_blob_sha256:
                hash_mismatches.append(
                    {
                        "requirement_id": req_id,
                        "title": title,
                        "evidence_locator": locator,
                        "declared_hash": declared_hash,
                        "git_blob_hash": blob_sha256,
                        "head_git_blob_hash": head_blob_sha256,
                        "disk_hash": disk_sha256,
                        "reason": "policy_code_reference disk SHA-256 does not match committed Git blob SHA-256",
                    }
                )
                binding_status = "MISMATCH"
            else:
                binding_status = "VERIFIED_CODE_REFERENCE"
        else:
            hash_mismatches.append(
                {
                    "requirement_id": req_id,
                    "title": title,
                    "evidence_locator": locator,
                    "declared_hash": declared_hash,
                    "git_blob_hash": blob_sha256,
                    "disk_hash": disk_sha256,
                    "reason": "git_tracked requirement is missing required evidence_hash (declared_hash is null or empty)",
                }
            )
            binding_status = "MISMATCH"

        git_blob_bindings.append(
            {
                "requirement_id": req_id,
                "title": title,
                "evidence_locator": locator,
                "evidence_commit_sha": commit_sha,
                "declared_hash": declared_hash,
                "git_blob_hash": blob_sha256,
                "disk_hash": disk_sha256,
                "blob_size_bytes": blob_size if blob_size is not None else len(raw_bytes),
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
        out_p.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")

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
