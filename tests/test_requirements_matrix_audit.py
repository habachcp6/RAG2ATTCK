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
    unique_git_files = {item["evidence_locator"] for item in report["git_blob_bindings"]}
    assert len(unique_git_files) == 21

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


def test_k01_retry_locator_matches_canonical_run_seal() -> None:
    """K.01-PROVIDER_FAILURE_RETRY dynamically matches canonical_run_seal_v1.json and eliminates 05a21d08."""
    seal_path = REPO_ROOT / "reports/evidence/canonical_run_seal_v1.json"
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    req_journal_sha = seal_data["sealed_artifact_digests"]["request_journal.jsonl"]
    rag_k1_pred_sha = seal_data["sealed_artifact_digests"]["rag_k1_predictions.jsonl"]
    assert len(req_journal_sha) == 64
    assert len(rag_k1_pred_sha) == 64

    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    k01 = next(r for r in data["requirements"] if r["id"] == "K.01-PROVIDER_FAILURE_RETRY")
    closure = k01["closure_step"]
    assert "48479-48482" in closure
    assert "ordinal=5387" in closure
    assert "ordinal=5388" in closure
    assert req_journal_sha in closure
    assert "inputs/rag_k1_predictions.jsonl" in closure
    assert rag_k1_pred_sha in closure
    assert "line 1078" in closure
    assert "e9146fe74aa5769faa5dc7df70205e62924fcf8c0e3a53946c50f96ddb2f8086" in closure
    assert "9056b85dbba694a622acde4743c11803465c6e84ef34a32a3bb6385d12258562" in closure

    broken_digest_fragment = "05a21d08"
    for rel_path in [
        "docs/audit/requirements_traceability_matrix.md",
        "reports/evidence/finalization_requirements_matrix.json",
        "reports/evidence/finalization_requirements_matrix.md",
        "docs/PLAN-rag2attck-closeout.md",
    ]:
        content = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        assert broken_digest_fragment not in content, (
            f"Broken digest fragment {broken_digest_fragment} found in {rel_path}"
        )


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
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_UNRESOLVED_LOCAL_LOCATOR"
    assert report["summary"]["unresolved_local_locators"] == 1
    non_git_locs = {item["evidence_locator"] for item in report["non_git_assets"]}
    assert bad_locator not in non_git_locs


def test_untracked_file_on_disk_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative test: file exists on disk but is not in git ls-files fails closed."""
    import scripts.verify_requirements_matrix_audit as vrma

    orig_tracked = vrma._get_git_tracked_files(REPO_ROOT)
    assert orig_tracked is not None
    filtered_tracked = {p for p in orig_tracked if p != "docs/audit/pr_ancestry_audit.json"}
    monkeypatch.setattr(vrma, "_get_git_tracked_files", lambda _root: filtered_tracked)

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=MATRIX_PATH,
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_UNRESOLVED_LOCAL_LOCATOR"
    assert report["summary"]["unresolved_local_locators"] >= 1


def test_disabled_git_index_or_missing_git_dir_fails_closed(tmp_path: Path) -> None:
    """Negative test: check_git_index=False or missing .git directory fails closed."""
    report_no_idx, exit_no_idx = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=MATRIX_PATH,
        check_git_index=False,
    )
    assert exit_no_idx == 1
    assert report_no_idx["summary"]["audit_verdict"] == "FAIL_GIT_REPOSITORY_REQUIRED"

    # Also test a repo_root without .git
    fake_repo = tmp_path / "no_git_repo"
    fake_repo.mkdir()
    report_no_git, exit_no_git = audit_requirements_matrix(
        repo_root=fake_repo,
        matrix_path=MATRIX_PATH,
        check_git_index=True,
    )
    assert exit_no_git == 1
    assert report_no_git["summary"]["audit_verdict"] == "FAIL_GIT_REPOSITORY_REQUIRED"


def test_zero_commit_sha_fails_closed(tmp_path: Path) -> None:
    """Negative test: 40-zero commit SHA ('0'*40) fails closed with FAIL_UNRESOLVED_LOCAL_LOCATOR."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "A.01-RUN_ID":
            req["evidence_commit_sha"] = "0" * 40
            break

    tampered_matrix = tmp_path / "tampered_zero_sha_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_UNRESOLVED_LOCAL_LOCATOR"
    assert report["summary"]["unresolved_local_locators"] == 1


@pytest.mark.parametrize("target_storage", ["git_tracked", "policy_code_reference"])
@pytest.mark.parametrize("bad_commit_sha", [None, "", "deadbeef" * 5, "shortsha"])
def test_missing_or_empty_commit_sha_fails_closed(
    tmp_path: Path, target_storage: str, bad_commit_sha: str | None
) -> None:
    """Negative test: None, empty, or bogus evidence_commit_sha on git_tracked or policy_code_reference fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    mutated = False
    for req in data["requirements"]:
        if target_storage == "policy_code_reference":
            if req.get("final_candidate_status") == "POLICY_ENFORCED":
                req["evidence_storage"] = "policy_code_reference"
                req["evidence_commit_sha"] = bad_commit_sha
                mutated = True
                break
        elif req.get("evidence_storage") == target_storage:
            req["evidence_commit_sha"] = bad_commit_sha
            mutated = True
            break
    assert mutated, f"No requirement found for target_storage={target_storage}"

    tampered_matrix = tmp_path / f"tampered_{target_storage}_commit_sha_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_UNRESOLVED_LOCAL_LOCATOR"
    assert report["summary"]["unresolved_local_locators"] == 1


@pytest.mark.parametrize("tamper_mode", ["empty", "truncated", "duplicate_id", "missing_key"])
def test_invalid_matrix_schema_or_count_fails_closed(
    tmp_path: Path, tamper_mode: str
) -> None:
    """Negative test: empty, truncated, duplicate-ID, or malformed requirement fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    if tamper_mode == "empty":
        data["requirements"] = []
    elif tamper_mode == "truncated":
        data["requirements"] = data["requirements"][:-1]
    elif tamper_mode == "duplicate_id":
        data["requirements"][1]["id"] = data["requirements"][0]["id"]
    elif tamper_mode == "missing_key":
        del data["requirements"][0]["evidence_storage"]

    tampered_matrix = tmp_path / f"tampered_schema_{tamper_mode}.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_INVALID_MATRIX_SCHEMA_OR_COUNT"


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
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_GIT_BLOB_HASH_MISMATCH"
    assert report["summary"]["hash_mismatches"] == 1


def test_release_package_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    """Negative test: tampered declared_hash on RELEASE_PACKAGE fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req.get("evidence_type") == "RELEASE_PACKAGE":
            req["evidence_hash"] = "a" * 64
            break

    tampered_matrix = tmp_path / "tampered_release_pkg_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=True,
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
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_INVALID_URL_OR_GATE_BINDING"
    assert report["summary"]["invalid_url_or_gate_bindings"] == 1


def test_invalid_github_url_fails_closed(tmp_path: Path) -> None:
    """Negative test: invalid GitHub URL domain/path fails closed."""
    data = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    for req in data["requirements"]:
        if req["id"] == "C.03-HUMAN_MERGE_AUTH":
            req["evidence_locator"] = "https://example.com/not-a-valid-github-url"
            break

    tampered_matrix = tmp_path / "tampered_url_matrix.json"
    tampered_matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=tampered_matrix,
        check_git_index=True,
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
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_GIT_BLOB_HASH_MISMATCH"
    assert report["summary"]["hash_mismatches"] == 1


def test_git_blob_vs_disk_hash_verification_with_git_index_enabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Negative test: when check_git_index=True, a git blob SHA-256 mismatch against disk/declared fails closed."""
    import scripts.verify_requirements_matrix_audit as vrma

    orig_helper = vrma._get_git_blob_sha256_and_size

    def fake_git_blob(repo_root, ref, norm_locator, cache):
        if norm_locator == "reports/evidence/canonical_run_seal_v1.json":
            return "f" * 64, 3046
        return orig_helper(repo_root, ref, norm_locator, cache)

    monkeypatch.setattr(vrma, "_get_git_blob_sha256_and_size", fake_git_blob)

    report, exit_code = audit_requirements_matrix(
        repo_root=REPO_ROOT,
        matrix_path=MATRIX_PATH,
        check_git_index=True,
    )

    assert exit_code == 1
    assert report["summary"]["audit_verdict"] == "FAIL_GIT_BLOB_HASH_MISMATCH"
    assert report["summary"]["hash_mismatches"] >= 1
    mismatch = next(
        m
        for m in report["hash_mismatches_detail"]
        if m.get("evidence_locator") == "reports/evidence/canonical_run_seal_v1.json"
    )
    assert mismatch["git_blob_hash"] == "f" * 64
    assert mismatch["disk_hash"] != mismatch["git_blob_hash"]


