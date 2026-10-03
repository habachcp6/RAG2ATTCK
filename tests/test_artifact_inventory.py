"""Regression tests for R9 Artifact Inventory, Visual QA Inspection Record, and Fail-Closed Enforcement.

Tests fail-closed behavior across:
1. test_empty_directory_fails: Empty directory strictly exits with code 1 and verdict FAIL_MISSING_REQUIRED_ARTIFACTS.
2. test_missing_pptx_fails: Missing PPTX file strictly exits with code 1 and identifies missing artifact.
3. test_missing_previews_fails: Missing slide preview PNG strictly exits with code 1.
4. test_missing_figures_directory_fails: Missing figures directory strictly exits with code 1 and FAIL_MISSING_REQUIRED_ARTIFACTS.
5. test_missing_one_required_figure_fails: Missing 1 required figure strictly exits with code 1 and FAIL_MISSING_REQUIRED_ARTIFACTS.
6. test_missing_provenance_file_fails: Missing figure_provenance.json strictly exits with code 1 and FAIL_MISSING_REQUIRED_ARTIFACTS.
7. test_missing_docx_fails: Missing canonical_populated_report.docx strictly exits with code 1 and FAIL_MISSING_REQUIRED_ARTIFACTS.
8. test_required_png_replaced_with_plain_text_fails: Fake text PNG strictly exits with code 1 and FAIL_STRUCTURE_CHECK.
9. test_docx_with_unrendered_template_tags_fails: DOCX containing {{...}} strictly exits with code 1 and FAIL_STRUCTURE_CHECK.
10. test_missing_expected_digest_fails: Deleting expected digest for required figure strictly exits with code 1 and FAIL_MISSING_EXPECTED_DIGEST.
11. test_figure_tampered_bytes_fails: Modified figure bytes strictly exits with code 1 and FAIL_HASH_MISMATCH.
12. test_wrong_bundle_binding_fails: Tampered bundle_sha256 in figure_provenance strictly exits with code 1 and FAIL_BUNDLE_BINDING_MISMATCH.
13. test_missing_or_mismatched_qa_record_fails: Missing or tampered QA record strictly exits with code 1.
14. test_genuine_artifacts_inventory_passes: Genuine repository passes with exit code 0 and verdict PASS_ALL_ARTIFACTS_VERIFIED.
15. test_cli_execution_fail_closed: CLI executions on empty dir vs genuine repo.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import List

from scripts.generate_r9_artifact_inventory import (
    generate_inventory,
)

REPO_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_ARTIFACT_REL_PATHS = [
    "artifacts/results/canonical_metric_bundle_v2.json",
    "reports/evidence/canonical_run_seal_v1.json",
    "artifacts/public_package_staging/public_package_manifest.json",
    "reports/evidence/canonical_populated_report.md",
    "reports/evidence/canonical_populated_report.docx",
    "reports/evidence/canonical_populated_report.pdf",
    "reports/evidence/populated_report_slots_canonical.json",
    "reports/evidence/research_report_scaffold.md",
    "docs/presentation/slides.pptx",
    "docs/presentation/slides.md",
    "docs/presentation/deck_figures_audit.json",
    "reports/evidence/canonical_deck_figures_audit.json",
    "reports/evidence/qa/visual_qa_inspection_record.json",
] + [f"reports/evidence/qa/fixture_slides/slide-{i}.png" for i in range(1, 13)]


def setup_mock_repo(target_root: Path, omit_paths: List[str] | None = None) -> None:
    """Populate target_root with copies of genuine artifacts except any omitted."""
    omit_set = set(omit_paths or [])
    for rel in REQUIRED_ARTIFACT_REL_PATHS:
        if rel in omit_set:
            continue
        src = REPO_ROOT / rel
        if src.is_file():
            dst = target_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    figures_src = REPO_ROOT / "reports/evidence/figures"
    if figures_src.is_dir() and "reports/evidence/figures" not in omit_set:
        figures_dst = target_root / "reports/evidence/figures"
        figures_dst.mkdir(parents=True, exist_ok=True)
        for f in figures_src.iterdir():
            if f.is_file():
                rel = f"reports/evidence/figures/{f.name}"
                if rel not in omit_set:
                    shutil.copy2(f, figures_dst / f.name)


def test_empty_directory_fails(tmp_path: Path) -> None:
    """Verify that running inventory generation on an empty directory strictly fails closed."""
    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 for empty directory"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert inventory["validation_summary"]["missing_required_count"] > 0
    assert len(inventory["validation_summary"]["missing_required_artifacts"]) >= len(
        REQUIRED_ARTIFACT_REL_PATHS
    )


def test_missing_pptx_fails(tmp_path: Path) -> None:
    """Verify that missing slides.pptx causes fail-closed exit with code 1."""
    setup_mock_repo(tmp_path, omit_paths=["docs/presentation/slides.pptx"])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when PPTX is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert (
        "docs/presentation/slides.pptx"
        in inventory["validation_summary"]["missing_required_artifacts"]
    )
    assert inventory["presentation_and_defense_deck"]["slides_pptx"]["exists"] is False
    assert (
        inventory["presentation_and_defense_deck"]["slides_pptx"]["lifecycle_states"][
            "FILE_PRESENT"
        ]
        is False
    )


def test_missing_previews_fails(tmp_path: Path) -> None:
    """Verify that missing slide preview PNG causes fail-closed exit with code 1."""
    missing_slide = "reports/evidence/qa/fixture_slides/slide-6.png"
    setup_mock_repo(tmp_path, omit_paths=[missing_slide])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when slide preview is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert missing_slide in inventory["validation_summary"]["missing_required_artifacts"]
    assert inventory["visual_qa_mapping"]["slides"]["slide-6.png"]["exists"] is False
    assert (
        inventory["visual_qa_mapping"]["slides"]["slide-6.png"]["lifecycle_states"]["FILE_PRESENT"]
        is False
    )


def test_missing_figures_directory_fails(tmp_path: Path) -> None:
    """Verify that a completely missing reports/evidence/figures dir fails with FAIL_MISSING_REQUIRED_ARTIFACTS."""
    setup_mock_repo(tmp_path, omit_paths=["reports/evidence/figures"])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when figures directory is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert (
        "reports/evidence/figures"
        in inventory["validation_summary"]["missing_required_artifacts"]
    )


def test_missing_one_required_figure_fails(tmp_path: Path) -> None:
    """Verify that missing a single required figure triggers FAIL_MISSING_REQUIRED_ARTIFACTS."""
    target_rel = "reports/evidence/figures/fig4_retrieval_hit_rate.png"
    setup_mock_repo(tmp_path, omit_paths=[target_rel])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when one required figure is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert target_rel in inventory["validation_summary"]["missing_required_artifacts"]
    assert (
        inventory["scientific_figures_inventory"]["files"]["fig4_retrieval_hit_rate.png"][
            "exists"
        ]
        is False
    )


def test_missing_provenance_file_fails(tmp_path: Path) -> None:
    """Verify that missing figure_provenance.json triggers FAIL_MISSING_REQUIRED_ARTIFACTS."""
    target_rel = "reports/evidence/figures/figure_provenance.json"
    setup_mock_repo(tmp_path, omit_paths=[target_rel])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when figure_provenance.json is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert target_rel in inventory["validation_summary"]["missing_required_artifacts"]


def test_missing_docx_fails(tmp_path: Path) -> None:
    """Verify that missing canonical_populated_report.docx triggers FAIL_MISSING_REQUIRED_ARTIFACTS."""
    target_rel = "reports/evidence/canonical_populated_report.docx"
    setup_mock_repo(tmp_path, omit_paths=[target_rel])

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when DOCX is missing"
    assert inventory["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert target_rel in inventory["validation_summary"]["missing_required_artifacts"]


def test_required_png_replaced_with_plain_text_fails(tmp_path: Path) -> None:
    """Verify that replacing a required .png with plain text triggers FAIL_STRUCTURE_CHECK."""
    setup_mock_repo(tmp_path)
    target_file = tmp_path / "reports/evidence/figures/fig4_retrieval_hit_rate.png"
    target_file.write_text("THIS IS PLAIN TEXT, NOT A VALID PNG IMAGE.", encoding="utf-8")

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when PNG is corrupted to plain text"
    assert inventory["verdict"] == "FAIL_STRUCTURE_CHECK"
    assert (
        "reports/evidence/figures/fig4_retrieval_hit_rate.png"
        in inventory["validation_summary"]["structure_failure_artifacts"]
    )
    assert (
        inventory["scientific_figures_inventory"]["files"]["fig4_retrieval_hit_rate.png"][
            "lifecycle_states"
        ]["STRUCTURE_CHECKED"]
        is False
    )


def test_docx_with_unrendered_template_tags_fails(tmp_path: Path) -> None:
    """Verify that a DOCX containing {{...}} triggers FAIL_STRUCTURE_CHECK."""
    setup_mock_repo(tmp_path)
    docx_path = tmp_path / "reports/evidence/canonical_populated_report.docx"

    temp_dir = tmp_path / "docx_unpack"
    with zipfile.ZipFile(docx_path, "r") as zf:
        zf.extractall(temp_dir)

    doc_xml_p = temp_dir / "word" / "document.xml"
    content = doc_xml_p.read_text(encoding="utf-8")
    content = content.replace("Abstract", "Abstract {{UNRENDERED_SLOT_TAG}}")
    doc_xml_p.write_text(content, encoding="utf-8")

    docx_path.unlink()
    with zipfile.ZipFile(docx_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_p in temp_dir.rglob("*"):
            if file_p.is_file():
                zf.write(file_p, file_p.relative_to(temp_dir))

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when DOCX has unrendered template tags"
    assert inventory["verdict"] == "FAIL_STRUCTURE_CHECK"
    assert (
        "reports/evidence/canonical_populated_report.docx"
        in inventory["validation_summary"]["structure_failure_artifacts"]
    )


def test_missing_expected_digest_fails(tmp_path: Path) -> None:
    """Verify that deleting an expected figure digest from provenance triggers FAIL_MISSING_EXPECTED_DIGEST."""
    setup_mock_repo(tmp_path)
    prov_file = tmp_path / "reports/evidence/figures/figure_provenance.json"
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    # Delete digest for fig4_retrieval_hit_rate.png while keeping valid PNG on disk
    del prov_data["generated_figures"]["fig4_retrieval_hit_rate.png"]
    prov_file.write_text(json.dumps(prov_data, indent=2), encoding="utf-8")

    # In order to test missing expected digest without triggering figure_provenance hash mismatch first,
    # we update the expected hash for figure_provenance.json to match the modified file
    import hashlib
    mod_prov_sha = hashlib.sha256(prov_file.read_bytes()).hexdigest()
    from unittest.mock import patch
    import scripts.generate_r9_artifact_inventory as gen_module

    mod_hashes = dict(gen_module.CANONICAL_FIGURE_EXPECTED_HASHES)
    mod_hashes["figure_provenance.json"] = mod_prov_sha

    with patch.object(gen_module, "CANONICAL_FIGURE_EXPECTED_HASHES", mod_hashes):
        inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when expected digest is missing"
    assert inventory["verdict"] == "FAIL_MISSING_EXPECTED_DIGEST"
    assert (
        "reports/evidence/figures/fig4_retrieval_hit_rate.png"
        in inventory["validation_summary"]["missing_authority_artifacts"]
    )


def test_figure_tampered_bytes_fails(tmp_path: Path) -> None:
    """Verify that altering figure bytes while keeping magic header triggers FAIL_HASH_MISMATCH."""
    setup_mock_repo(tmp_path)
    target_file = tmp_path / "reports/evidence/figures/fig4_retrieval_hit_rate.png"
    raw = bytearray(target_file.read_bytes())
    # Keep 8-byte PNG header intact, alter byte 20
    raw[20] = raw[20] ^ 0xFF
    target_file.write_bytes(bytes(raw))

    inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when figure bytes are tampered"
    assert inventory["verdict"] == "FAIL_HASH_MISMATCH"
    assert (
        "reports/evidence/figures/fig4_retrieval_hit_rate.png"
        in inventory["validation_summary"]["hash_mismatch_artifacts"]
    )
    assert (
        inventory["scientific_figures_inventory"]["files"]["fig4_retrieval_hit_rate.png"][
            "lifecycle_states"
        ]["HASH_VERIFIED"]
        is False
    )


def test_wrong_bundle_binding_fails(tmp_path: Path) -> None:
    """Verify that tampered bundle_sha256 in provenance triggers FAIL_BUNDLE_BINDING_MISMATCH."""
    setup_mock_repo(tmp_path)
    prov_file = tmp_path / "reports/evidence/figures/figure_provenance.json"
    prov_data = json.loads(prov_file.read_text(encoding="utf-8"))
    prov_data["bundle_sha256"] = "0" * 64
    prov_file.write_text(json.dumps(prov_data, indent=2), encoding="utf-8")

    import hashlib
    mod_prov_sha = hashlib.sha256(prov_file.read_bytes()).hexdigest()
    from unittest.mock import patch
    import scripts.generate_r9_artifact_inventory as gen_module

    mod_hashes = dict(gen_module.CANONICAL_FIGURE_EXPECTED_HASHES)
    mod_hashes["figure_provenance.json"] = mod_prov_sha

    with patch.object(gen_module, "CANONICAL_FIGURE_EXPECTED_HASHES", mod_hashes):
        inventory, code = generate_inventory(repo_root=tmp_path)

    assert code == 1, "Expected exit code 1 when bundle binding is invalid"
    assert inventory["verdict"] == "FAIL_BUNDLE_BINDING_MISMATCH"
    assert inventory["validation_summary"]["bundle_bound"] is False


def test_missing_or_mismatched_qa_record_fails(tmp_path: Path) -> None:
    """Verify that missing or tampered QA record strictly fails closed."""
    qa_rel = "reports/evidence/qa/visual_qa_inspection_record.json"

    # Sub-case A: Missing QA record
    setup_mock_repo(tmp_path, omit_paths=[qa_rel])
    inv_missing, code_missing = generate_inventory(repo_root=tmp_path)
    assert code_missing == 1
    assert inv_missing["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
    assert qa_rel in inv_missing["validation_summary"]["missing_required_artifacts"]

    # Sub-case B: Mismatched PPTX hash in QA record
    tmp_path_b = tmp_path / "case_b"
    tmp_path_b.mkdir()
    setup_mock_repo(tmp_path_b)
    qa_file_b = tmp_path_b / qa_rel
    data_b = json.loads(qa_file_b.read_text(encoding="utf-8"))
    data_b["scope"]["pptx_target"]["sha256"] = "0" * 64
    if "presentation_deck_qa" in data_b:
        data_b["presentation_deck_qa"]["pptx_target"]["sha256"] = "0" * 64
    qa_file_b.write_text(json.dumps(data_b, indent=2), encoding="utf-8")

    inv_b, code_b = generate_inventory(repo_root=tmp_path_b)
    assert code_b == 1
    assert inv_b["verdict"] == "FAIL_QA_VERIFICATION_MISMATCH"
    assert inv_b["visual_qa_mapping"]["qa_record_verified"] is False
    assert any(
        "PPTX SHA256 mismatch" in err for err in inv_b["visual_qa_mapping"]["qa_validation_errors"]
    )

    # Sub-case C: Mismatched preview hash in QA record
    tmp_path_c = tmp_path / "case_c"
    tmp_path_c.mkdir()
    setup_mock_repo(tmp_path_c)
    qa_file_c = tmp_path_c / qa_rel
    data_c = json.loads(qa_file_c.read_text(encoding="utf-8"))
    data_c["slide_previews"]["slide-9.png"]["sha256"] = "f" * 64
    qa_file_c.write_text(json.dumps(data_c, indent=2), encoding="utf-8")

    inv_c, code_c = generate_inventory(repo_root=tmp_path_c)
    assert code_c == 1
    assert inv_c["verdict"] == "FAIL_QA_VERIFICATION_MISMATCH"
    assert inv_c["visual_qa_mapping"]["qa_record_verified"] is False
    assert any(
        "slide-9.png SHA256 mismatch" in err
        for err in inv_c["visual_qa_mapping"]["qa_validation_errors"]
    )

    # Sub-case D: Mismatched DOCX hash in QA record
    tmp_path_d = tmp_path / "case_d"
    tmp_path_d.mkdir()
    setup_mock_repo(tmp_path_d)
    qa_file_d = tmp_path_d / qa_rel
    data_d = json.loads(qa_file_d.read_text(encoding="utf-8"))
    data_d["scope"]["docx_target"]["sha256"] = "e" * 64
    if "docx_report_qa" in data_d:
        data_d["docx_report_qa"]["docx_target"]["sha256"] = "e" * 64
    qa_file_d.write_text(json.dumps(data_d, indent=2), encoding="utf-8")

    inv_d, code_d = generate_inventory(repo_root=tmp_path_d)
    assert code_d == 1
    assert inv_d["verdict"] == "FAIL_QA_VERIFICATION_MISMATCH"
    assert inv_d["visual_qa_mapping"]["qa_record_verified"] is False
    assert any(
        "DOCX SHA256 mismatch" in err for err in inv_d["visual_qa_mapping"]["qa_validation_errors"]
    )


def test_genuine_artifacts_inventory_passes() -> None:
    """Verify that running inventory generation on genuine repository strictly passes with code 0."""
    inventory, code = generate_inventory(repo_root=REPO_ROOT)

    assert code == 0, f"Expected exit code 0 for genuine repository, got {code}"
    assert inventory["verdict"] == "PASS_ALL_ARTIFACTS_VERIFIED"

    # Presentation Deck Dynamic Inspection
    deck = inventory["presentation_and_defense_deck"]
    assert deck["total_slides"] == 12
    assert deck["speaker_notes_present_all_slides"] is True
    assert deck["pptx_dynamic_inspection"]["valid"] is True
    assert deck["pptx_dynamic_inspection"]["slide_count"] == 12
    assert deck["pptx_dynamic_inspection"]["notes_count"] == 12
    assert deck["slides_md_dynamic_inspection"]["valid"] is True
    assert deck["slides_md_dynamic_inspection"]["heading_count"] == 12
    assert deck["slides_md_dynamic_inspection"]["notes_block_count"] >= 12

    # Lifecycle states for PPTX and DOCX
    pptx_states = deck["slides_pptx"]["lifecycle_states"]
    for state_name in [
        "FILE_PRESENT",
        "HASH_VERIFIED",
        "STRUCTURE_CHECKED",
        "NUMERICAL_CHECKED",
        "RENDERED",
        "VISUALLY_REVIEWED",
    ]:
        assert pptx_states[state_name] is True, f"PPTX state {state_name} should be True"

    docx_states = inventory["scientific_reports"]["canonical_populated_report_docx"][
        "lifecycle_states"
    ]
    for state_name in [
        "FILE_PRESENT",
        "HASH_VERIFIED",
        "STRUCTURE_CHECKED",
        "NUMERICAL_CHECKED",
        "RENDERED",
        "VISUALLY_REVIEWED",
    ]:
        assert docx_states[state_name] is True, f"DOCX state {state_name} should be True"

    # Visual QA Record & Previews
    vqa = inventory["visual_qa_mapping"]
    assert vqa["qa_record_verified"] is True
    assert len(vqa["slides"]) == 12
    for s_name, s_info in vqa["slides"].items():
        assert s_info["exists"] is True
        assert s_info["verified"] is True
        assert s_info["lifecycle_states"]["VISUALLY_REVIEWED"] is True

    # Figures in reports/evidence/figures
    figures_inv = inventory["scientific_figures_inventory"]
    assert figures_inv["total_figures"] == 32
    for f_name, f_info in figures_inv["files"].items():
        assert f_info["exists"] is True
        assert f_info["verified"] is True
        states = f_info["lifecycle_states"]
        assert states["FILE_PRESENT"] is True
        assert states["HASH_VERIFIED"] is True
        assert states["STRUCTURE_CHECKED"] is True
        assert states["NUMERICAL_CHECKED"] is True
        assert states["RENDERED"] is True
        if f_name in ["fig4_retrieval_hit_rate.png", "fig7_cost_and_tokens_vs_k.png"]:
            assert states["VISUALLY_REVIEWED"] is True
        else:
            assert states["VISUALLY_REVIEWED"] is False

    # Summary clean
    summary = inventory["validation_summary"]
    assert summary["missing_required_count"] == 0
    assert summary["missing_authority_count"] == 0
    assert summary["hash_mismatch_count"] == 0
    assert summary["structure_failure_count"] == 0
    assert summary["bundle_bound"] is True
    assert summary["qa_errors"] == []


def test_cli_execution_fail_closed(tmp_path: Path) -> None:
    """Verify that CLI execution returns exit code 0 on real repo and code 1 on empty dir."""
    script_path = REPO_ROOT / "scripts/generate_r9_artifact_inventory.py"

    # Empty tmp_path CLI call
    proc_fail = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert proc_fail.returncode == 1
    assert "FAIL_MISSING_REQUIRED_ARTIFACTS" in proc_fail.stdout

    # Genuine repo CLI call
    proc_pass = subprocess.run(
        [sys.executable, str(script_path), "--repo-root", str(REPO_ROOT)],
        capture_output=True,
        text=True,
    )
    assert proc_pass.returncode == 0
    assert "PASS_ALL_ARTIFACTS_VERIFIED" in proc_pass.stdout
