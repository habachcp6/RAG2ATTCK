"""Regression tests for scripts/verify_requirements_matrix_audit.py (Step 1.5).

Covers:
1. Positive audit of the production finalization_requirements_matrix.json (141 git blob bindings,
   29 non-git assets/URLs, 0 local paths in non_git_assets, exit code 0).
2. Explicit verification that T.01, U.01, and AC.01-AF.01 resolve to real git-tracked blobs
   with matching SHA-256 digests and are absent from non_git_assets.
3. Negative regression test: injecting a non-existent repo-relative path
   (`docs/audit/non_existent_artifact.json` or `AGENTS.md`) with `local_pending` or `not_applicable`
   on a `VERIFIED` / `POLICY_ENFORCED` requirement fails closed with `FAIL_UNRESOLVED_LOCAL_LOCATOR`
   (exit code 1) instead of leaking into `non_git_assets`.
4. Negative regression test: 1-byte SHA-256 mismatch on a git_tracked requirement fails closed
   with `FAIL_GIT_BLOB_HASH_MISMATCH` (exit code 1).
5. Negative regression test: premature `VERIFIED` status on a `HUMAN_ACTION_GATE` URL fails closed
   with `FAIL_INVALID_URL_OR_GATE_BINDING` (exit code 1).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.verify_requirements_matrix_audit import audit_requirements_matrix

REPO_ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = REPO_ROOT / "reports/evidence/finalization_requirements_matrix.json"


def test_real_requirements_matrix_passes_with_zero_local_exceptions() -> None:
    """Real matrix passes with 141 git blobs, 29 non-git URLs/release assets, and 0 local leaks."""
    report, exit_code = audit_requirements_matrix(repo_root=REPO_ROOT)

    assert exit_code == 0
    summary = report["summary"]
    assert summary["audit_verdict"] == "PASS_ALL_BINDINGS_VERIFIED"
    assert summary["total_requirements_tracked"] == 170
    assert summary["valid_git_blob_bindings"] == 141
    assert summary["non_git_assets_and_urls"] == 29
    assert summary["standalone_release_assets"] == 2
    assert summary["github_urls_and_ci_runs"] == 27
    assert summary["unresolved_local_locators"] == 0
    assert summary["missing_git_blobs"] == 0
    assert summary["hash_mismatches"] == 0
    assert summary["local_paths_in_non_git_assets"] == 0

    git_ids = {item["requirement_id"]: item for item in report["git_blob_bindings"]}
    non_git_ids = {item["requirement_id"]: item for item in report["non_git_assets"]}

    for req_id, expected_loc in [
        ("T.01-PR_CLASSIFICATION_AND_ANCESTRY", "docs/audit/pr_ancestry_audit.json"),
        ("U.01-DIFF_AUDIT", "docs/audit/baseline_diff_audit.json"),
        (
            "AC.01-SELF_CORRECTION",
            "reports/evidence/sg_evidence_audit_independent_probes_record.json",
        ),
        (
            "AD.01-REVIEWER_ESCALATION",
            "reports/evidence/sg_evidence_audit_independent_probes_record.json",
        ),
        (
            "AE.01-RESPONSE_FORMAT",
            "reports/evidence/sg_evidence_audit_independent_probes_record.json",
        ),
        (
            "AF.01-PRIORITY_ORDER",
            "reports/evidence/sg_evidence_audit_independent_probes_record.json",
        ),
    ]:
        assert req_id in git_ids, f"{req_id} must be in git_blob_bindings"
        assert req_id not in non_git_ids, f"{req_id} must NOT be in non_git_assets"
        assert git_ids[req_id]["evidence_locator"] == expected_loc
        assert git_ids[req_id]["status"] == "MATCH"
        assert git_ids[req_id]["declared_hash"] == git_ids[req_id]["git_blob_hash"]


def test_k01_retry_locator_documented_in_matrix() -> None:
    """K.01-PROVIDER_FAILURE_RETRY documents exact request_journal.jsonl lines and ordinals."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    k01 = next(r for r in data["requirements"] if r["id"] == "K.01-PROVIDER_FAILURE_RETRY")
    closure = k01["closure_step"]
    assert "48479-48482" in closure
    assert "ordinal=5387" in closure
    assert "ordinal=5388" in closure
    assert "f36e0f3099ef704e05a21d0839cf3158268fb36b647d8c229bc9f8cf8fd4149a" in closure


@pytest.mark.parametrize(
    ("bad_locator", "bad_storage"),
    [
        ("docs/audit/non_existent_artifact.json", "local_pending"),
        ("AGENTS.md", "not_applicable"),
    ],
)
def test_unresolved_local_locator_fails_closed(
    tmp_path: Path, bad_locator: str, bad_storage: str
) -> None:
    """Negative test: non-existent local locator fails closed (exit 1), never in non_git_assets."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "T.01-PR_CLASSIFICATION_AND_ANCESTRY":
            req["evidence_locator"] = bad_locator
            req["evidence_path"] = bad_locator
            req["evidence_storage"] = bad_storage
            req["evidence_hash"] = None
            req["final_candidate_status"] = "VERIFIED"
            break

    tampered_matrix = tmp_path / "tampered_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=False,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_UNRESOLVED_LOCAL_LOCATOR"
    assert report["summary"]["unresolved_local_locators"] == 1
    non_git_locs = {item["evidence_locator"] for item in report["non_git_assets"]}
    assert bad_locator not in non_git_locs


def test_git_blob_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    """Negative test: tampered declared_hash on a git_tracked requirement fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "A.01-RUN_ID":
            req["evidence_hash"] = "0" * 64
            break

    tampered_matrix = tmp_path / "tampered_hash_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=False,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_GIT_BLOB_HASH_MISMATCH"
    assert report["summary"]["hash_mismatches"] == 1


def test_premature_human_gate_verified_status_fails_closed(tmp_path: Path) -> None:
    """Negative regression test: HUMAN_ACTION_GATE claiming VERIFIED prior to merge fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "C.03-HUMAN_MERGE_AUTH":
            req["final_candidate_status"] = "VERIFIED"
            break

    tampered_matrix = tmp_path / "tampered_gate_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=False,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_INVALID_URL_OR_GATE_BINDING"
    assert report["summary"]["invalid_url_or_gate_bindings"] == 1


def test_git_tracked_missing_hash_fails_closed(tmp_path: Path) -> None:
    """Negative test: git_tracked requirement with missing evidence_hash fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "A.01-RUN_ID":
            req["evidence_hash"] = None
            break

    tampered_matrix = tmp_path / "tampered_missing_hash_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=False,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_GIT_BLOB_HASH_MISMATCH"
    assert report["summary"]["hash_mismatches"] == 1

