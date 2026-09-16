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


def test_source_research_hashes():
    ws = get_default_workspace_root()
    ctx = verify_source_context(ws)
    preserved = {f["filename"]: f["sha256"] for f in ctx["preserved_source_research_files"]}
    assert len(preserved) == 7
    assert preserved["README.md"] == "0ed29fc5948d79e8007bd5911c0cf271e5c065f3c8762a9fe4a81940dac150b2"
    assert preserved["mendeley_v3_files.json"] == "f626ea56a2883febcb1776a20cf6001f306e3a627d987356f81a8e27692cabe9"
    assert preserved["checksums.sha256"] == "0ee0b4f68882f63ac9392b6fe6744c310e931ad27736acd3f58b9a18de0cd647"


def test_python_runtime_version():
    assert sys.version_info.major == 3
    assert sys.version_info.minor == 13


def test_run_preflight_check_generates_valid_json(tmp_path):
    ws = tmp_path
    sr_dir = ws / "data" / "audit" / "source_research"
    sr_dir.mkdir(parents=True)
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

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True)
    (meta_dir / "source_context.json").write_text(
        json.dumps(
            {
                "verification_status": "VERIFIED_CANONICAL_PRESERVED",
                "canonical_documents": {
                    "docx": {
                        "path": "docs/context/RAG_ATTCK_Research_Plan_Updated.docx",
                        "size_bytes": 1,
                        "sha256": "0" * 64,
                    },
                    "xlsx": {
                        "path": "docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx",
                        "size_bytes": 1,
                        "sha256": "1" * 64,
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    report = run_preflight_check(ws)
    assert report["gate_result"]["status"] == "PASS"
    assert report["gate_result"]["passed"] is True

    preflight_json = ws / "data" / "metadata" / "preflight.json"
    assert preflight_json.exists()
    data = json.loads(preflight_json.read_text(encoding="utf-8"))
    assert data["meta"]["task"] == "T0_PREFLIGHT"
    assert data["capacity_assessment"]["capacity_sufficient"] is True
    assert data["gate_result"]["status"] == "PASS"
