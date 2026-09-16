"""
Tests for src/dataset.py: Preflight, Path Safety, Capacity, Source Context.
"""

import json
from pathlib import Path
import pytest
import shutil
import sys

from src.dataset import (
    get_default_workspace_root,
    resolve_secure_path,
    verify_all_workspace_paths,
    assess_disk_capacity,
    verify_source_context,
    run_preflight_check,
    PreflightCapacityError,
    PreflightPathSafetyError,
    PreflightSourceContextError,
    PreflightGateBlocked,
)


def test_path_safety_with_ampersand():
    ws = get_default_workspace_root()
    assert "&" in str(ws)
    assert ws.exists()
    assert ws.is_dir()
    resolved = resolve_secure_path(ws, "data/metadata")
    assert resolved.is_relative_to(ws)
    assert str(resolved).endswith("data\\metadata") or str(resolved).endswith("data/metadata")


def test_path_escape_rejection():
    ws = get_default_workspace_root()
    with pytest.raises(PreflightPathSafetyError):
        resolve_secure_path(ws, "../outside_workspace")

    with pytest.raises(PreflightPathSafetyError):
        resolve_secure_path(ws, "C:/Windows/System32")


def test_symlinks_and_junctions_scan():
    ws = get_default_workspace_root()
    symlinks = [p for p in ws.rglob("*") if p.is_symlink()]
    assert len(symlinks) == 0, "No symlinks should exist in workspace root"
    junctions = [p for p in ws.rglob("*") if hasattr(p, "is_junction") and p.is_junction()]
    assert len(junctions) == 0, "No junctions should exist in clean workspace"


def test_capacity_calculation_logic():
    ws = get_default_workspace_root()
    # Mock custom breakdown with total 1.0 GiB (1024^3 bytes)
    one_gib = 1024 * 1024 * 1024
    custom_breakdown = {
        "downloads_and_staging_bytes": 200 * 1024 * 1024,
        "extraction_and_raw_dataset_bytes": 200 * 1024 * 1024,
        "virtual_environment_and_tooling_bytes": 200 * 1024 * 1024,
        "derived_outputs_bytes": 200 * 1024 * 1024,
        "reproduction_run_bytes": 224 * 1024 * 1024,
    }
    cap = assess_disk_capacity(ws, custom_breakdown=custom_breakdown)
    # Estimate is 1024 MiB (1 GiB)
    assert cap.total_estimate_bytes == 1024 * 1024 * 1024
    # Estimate + 1 GiB is 2 GiB
    assert cap.estimate_plus_one_gib_bytes == 2 * one_gib
    # Floor is 5 GiB
    assert cap.minimum_floor_bytes == 5 * one_gib
    # Effective required is max(2 GiB, 5 GiB) = 5 GiB
    assert cap.effective_required_free_bytes == 5 * one_gib
    assert cap.capacity_sufficient is True


def test_capacity_gate_pass_live():
    ws = get_default_workspace_root()
    cap = assess_disk_capacity(ws)
    assert cap.live_free_bytes >= 5 * 1024 * 1024 * 1024
    assert cap.capacity_sufficient is True
    assert cap.headroom_bytes > 0


def test_canonical_docx_xlsx_verification():
    ws = get_default_workspace_root()
    ctx = verify_source_context(ws)
    assert ctx["verification_status"] == "VERIFIED_CANONICAL_PRESERVED"
    docs = ctx["canonical_documents"]
    assert "docx" in docs
    assert "xlsx" in docs
    assert docs["docx"]["sha256"] == "39499aa68188530eed81d1426af4d2f0217e17e10d9d016ddc0b38c0ae7a91af"
    assert docs["xlsx"]["sha256"] == "ed946fa1918af54a0634a317b6bf3d2b4291501219524de691c5da8b15725ef8"
    authors = ctx["official_dataset_reference"]["authors"]
    assert authors == [
        "Maryam Mozaffari",
        "Abbas Yazdinejad",
        "Ali Dehghantanha"
    ]


def _setup_mock_source_research(ws: Path):
    sr_dir = ws / "data" / "audit" / "source_research"
    sr_dir.mkdir(parents=True, exist_ok=True)
    for filename in [
        "article_fulltext.xml",
        "article_sections.txt",
        "checksums.sha256",
        "mendeley_v3_files.json",
        "README.md",
        "scenario_manifest.csv",
        "validation_summary.csv",
    ]:
        (sr_dir / filename).write_text(f"{filename}\n", encoding="utf-8")


def test_canonical_revalidation_case1_valid_metadata_and_files(tmp_path):
    """CASE 1: Valid physical DOCX/XLSX + correct metadata => PASS."""
    ws = tmp_path
    _setup_mock_source_research(ws)

    doc_dir = ws / "docs" / "context"
    doc_dir.mkdir(parents=True)
    docx_file = doc_dir / "RAG_ATTCK_Research_Plan_Updated.docx"
    xlsx_file = doc_dir / "RAG_ATTCK_Project_Tracker_Updated.xlsx"
    docx_content = b"Valid research plan DOCX content"
    xlsx_content = b"Valid project tracker XLSX content"
    docx_file.write_bytes(docx_content)
    xlsx_file.write_bytes(xlsx_content)

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    import hashlib
    (meta_dir / "source_context.json").write_text(
        json.dumps({
            "verification_status": "VERIFIED_CANONICAL_PRESERVED",
            "canonical_documents": {
                "docx": {
                    "path": "docs/context/RAG_ATTCK_Research_Plan_Updated.docx",
                    "size_bytes": len(docx_content),
                    "sha256": hashlib.sha256(docx_content).hexdigest(),
                },
                "xlsx": {
                    "path": "docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx",
                    "size_bytes": len(xlsx_content),
                    "sha256": hashlib.sha256(xlsx_content).hexdigest(),
                }
            }
        }),
        encoding="utf-8"
    )

    ctx = verify_source_context(ws)
    assert ctx["verification_status"] == "VERIFIED_CANONICAL_PRESERVED"
    report = run_preflight_check(ws)
    assert report["gate_result"]["status"] == "PASS"
    assert report["gate_result"]["passed"] is True


def test_canonical_revalidation_case2_metadata_exists_but_files_missing(tmp_path):
    """CASE 2: source_context.json contains plausible metadata but physical files missing => FAIL."""
    ws = tmp_path
    _setup_mock_source_research(ws)

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    (meta_dir / "source_context.json").write_text(
        json.dumps({
            "verification_status": "VERIFIED_CANONICAL_PRESERVED",
            "canonical_documents": {
                "docx": {
                    "path": "docs/context/RAG_ATTCK_Research_Plan_Updated.docx",
                    "size_bytes": 214812,
                    "sha256": "39499aa68188530eed81d1426af4d2f0217e17e10d9d016ddc0b38c0ae7a91af",
                },
                "xlsx": {
                    "path": "docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx",
                    "size_bytes": 49142,
                    "sha256": "ed946fa1918af54a0634a317b6bf3d2b4291501219524de691c5da8b15725ef8",
                }
            }
        }),
        encoding="utf-8"
    )

    with pytest.raises(PreflightSourceContextError, match="Physical canonical file missing"):
        verify_source_context(ws)

    with pytest.raises(PreflightGateBlocked):
        run_preflight_check(ws)


def test_canonical_revalidation_case3_hash_mismatch_fails(tmp_path):
    """CASE 3: Physical canonical document hash differs from saved canonical hash => FAIL."""
    ws = tmp_path
    _setup_mock_source_research(ws)

    doc_dir = ws / "docs" / "context"
    doc_dir.mkdir(parents=True)
    docx_file = doc_dir / "RAG_ATTCK_Research_Plan_Updated.docx"
    xlsx_file = doc_dir / "RAG_ATTCK_Project_Tracker_Updated.xlsx"
    docx_file.write_bytes(b"tampered content")
    xlsx_file.write_bytes(b"tracker content")

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    import hashlib
    (meta_dir / "source_context.json").write_text(
        json.dumps({
            "verification_status": "VERIFIED_CANONICAL_PRESERVED",
            "canonical_documents": {
                "docx": {
                    "path": "docs/context/RAG_ATTCK_Research_Plan_Updated.docx",
                    "size_bytes": len(b"tampered content"),
                    "sha256": "0" * 64,  # Mismatched hash
                },
                "xlsx": {
                    "path": "docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx",
                    "size_bytes": len(b"tracker content"),
                    "sha256": hashlib.sha256(b"tracker content").hexdigest(),
                }
            }
        }),
        encoding="utf-8"
    )

    with pytest.raises(PreflightSourceContextError, match="hash mismatch"):
        verify_source_context(ws)


def test_canonical_revalidation_case4_path_escape_fails(tmp_path):
    """CASE 4: Canonical document path resolves outside workspace => FAIL."""
    ws = tmp_path
    _setup_mock_source_research(ws)

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    (meta_dir / "source_context.json").write_text(
        json.dumps({
            "verification_status": "VERIFIED_CANONICAL_PRESERVED",
            "canonical_documents": {
                "docx": {
                    "path": "../outside_secret.docx",
                    "size_bytes": 100,
                    "sha256": "0" * 64,
                },
                "xlsx": {
                    "path": "docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx",
                    "size_bytes": 100,
                    "sha256": "1" * 64,
                }
            }
        }),
        encoding="utf-8"
    )

    with pytest.raises(PreflightPathSafetyError, match="escapes workspace"):
        verify_source_context(ws)


def test_canonical_revalidation_case5_fresh_initialization_records_hashes(tmp_path):
    """CASE 5: Fresh initialization with real canonical files and no prior metadata => PASS and recorded."""
    ws = tmp_path
    _setup_mock_source_research(ws)

    doc_dir = ws / "docs" / "context"
    doc_dir.mkdir(parents=True)
    docx_file = doc_dir / "RAG_ATTCK_Research_Plan_Updated.docx"
    xlsx_file = doc_dir / "RAG_ATTCK_Project_Tracker_Updated.xlsx"
    docx_bytes = b"Freshly initialized research plan"
    xlsx_bytes = b"Freshly initialized project tracker"
    docx_file.write_bytes(docx_bytes)
    xlsx_file.write_bytes(xlsx_bytes)

    # Note: no data/metadata/source_context.json exists prior to this run
    ctx = verify_source_context(ws)
    assert ctx["verification_status"] == "VERIFIED_CANONICAL_PRESERVED"
    docs = ctx["canonical_documents"]
    import hashlib
    assert docs["docx"]["sha256"] == hashlib.sha256(docx_bytes).hexdigest()
    assert docs["xlsx"]["sha256"] == hashlib.sha256(xlsx_bytes).hexdigest()
    assert docs["docx"]["size_bytes"] == len(docx_bytes)
    assert docs["xlsx"]["size_bytes"] == len(xlsx_bytes)

    # run_preflight_check must write source_context.json and preflight.json
    report = run_preflight_check(ws)
    assert report["gate_result"]["status"] == "PASS"
    written_ctx = json.loads((ws / "data" / "metadata" / "source_context.json").read_text(encoding="utf-8"))
    assert written_ctx["canonical_documents"]["docx"]["sha256"] == hashlib.sha256(docx_bytes).hexdigest()
