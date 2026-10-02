"""
tests/test_cross_artifact_consistency.py

Comprehensive test suite for Track D publication figure & table generators and
cross-artifact consistency checker.
Validates:
  - Generation of all 8 figures and 6 tables in fixture-only mode with visible warnings
  - XML well-formedness of all generated SVG figures (including Fig 1 & Fig 2)
  - Detection and fail-closed rejection of workstation path leaks
  - Detection and fail-closed rejection of unresolved template placeholders
  - Fail-closed behavior on missing repository inputs (DOCX, PPTX, MD, bundles)
  - Fail-closed behavior on bogus metric bundles
  - Provenance hash verification and tampering detection
  - Numerical table body consistency and denominator protection
  - Fixture rejection in publication-wide (--scope all) audit
  - DOCX embedded media corruption detection (non-PNG bytes)
  - DOCX visible accuracy tampering detection
  - PPTX tiny font size (< 8pt) and [WRONG RESULT] placeholder detection
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import pytest

from scripts.check_cross_artifact_consistency import (
    check_docx_binary,
    check_figure_provenance,
    check_pptx_binary,
    check_table_provenance,
    run_consistency_audit,
    scan_file_for_leaks,
    scan_file_for_placeholders,
)
from scripts.generate_publication_figures import generate_all_figures
from scripts.generate_publication_tables import generate_all_tables


def test_fixture_generation_and_audit(tmp_path: Path):
    """Verify that all 8 figures and 6 tables generate and pass generated-scope audit."""
    fig_dir = tmp_path / "docs" / "report" / "figures"
    tbl_dir = tmp_path / "docs" / "report" / "tables"

    # Generate figures & tables
    fig_prov = generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)
    tbl_prov = generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    assert fig_prov["figures_count"] == 8
    assert fig_prov["fixture_only"] is True
    assert tbl_prov["tables_count"] == 6
    assert tbl_prov["fixture_only"] is True

    # Check provenance functions
    f_res = check_figure_provenance(fig_dir)
    assert f_res["status"] == "PASS"
    assert len(f_res["missing_figures"]) == 0
    assert len(f_res["hash_mismatches"]) == 0
    assert len(f_res["xml_errors"]) == 0

    t_res = check_table_provenance(tbl_dir)
    assert t_res["status"] == "PASS"
    assert len(t_res["missing_tables"]) == 0
    assert len(t_res["hash_mismatches"]) == 0

    # Verify XML well-formedness of every SVG
    for svg_file in fig_dir.glob("*.svg"):
        content = svg_file.read_text(encoding="utf-8")
        ET.fromstring(content)
        assert "FIXTURE" in content.upper()

    # Verify visible fixture warning banner in every Markdown table
    for md_file in tbl_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        assert "FIXTURE" in content.upper()

    # Run consistency checker scoped to generated
    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="generated",
        output_report_path=None,
    )
    assert report["verdict"] == "PASS"
    assert report["leak_audit"]["status"] == "PASS"
    assert report["placeholder_audit"]["status"] == "PASS"


def test_empty_repository_fail_closed(tmp_path: Path):
    """Verify that an empty repository fails closed in strict mode."""
    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="all",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert len(report["missing_required_files"]) > 0


def test_missing_bundle_fail_closed(tmp_path: Path):
    """Verify that specifying a missing bundle fails closed."""
    non_existent = tmp_path / "no_such_bundle.json"
    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=non_existent,
        strict=True,
        scope="all",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert report["numerical_consistency"]["status"] == "FAIL"


def test_bogus_bundle_fail_closed(tmp_path: Path):
    """Verify that a bogus bundle schema fails closed."""
    bogus = tmp_path / "bogus_bundle.json"
    bogus.write_text('{"fixture_only": true, "not_a_metric_bundle": true}', encoding="utf-8")

    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=bogus,
        strict=True,
        scope="all",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert report["numerical_consistency"]["status"] == "FAIL"


def test_leak_detection_fail_closed(tmp_path: Path):
    """Verify that any personal workstation path leak is flagged and fails audit."""
    leaky_file = tmp_path / "leaky_document.md"
    leaky_file.write_text(
        "Here is the local result: `C:/Users/hahoa/.codex/artifacts/rag2attck/results.json`\n",
        encoding="utf-8",
    )

    findings = scan_file_for_leaks(leaky_file)
    assert len(findings) == 1
    assert "C:/Users/hahoa" in findings[0]["matched"]


def test_placeholder_detection_fail_closed(tmp_path: Path):
    """Verify that unresolved template placeholders (including PENDING with PID) are detected."""
    placeholder_file = tmp_path / "incomplete_document.md"
    placeholder_file.write_text(
        "Accuracy is {{NO_RAG_ACCURACY}} and status is [PENDING EXECUTION] PID 50192 or [TBD].\n",
        encoding="utf-8",
    )

    findings = scan_file_for_placeholders(placeholder_file)
    assert len(findings) >= 3
    ph_strings = {f["placeholder"] for f in findings}
    assert any("[PENDING" in s for s in ph_strings)
    assert any("{{NO_RAG_ACCURACY}}" in s for s in ph_strings)
    assert any("[TBD]" in s for s in ph_strings)


def test_tamper_provenance_hash_fail_closed(tmp_path: Path):
    """Verify that modifying a generated file without updating provenance fails closed."""
    fig_dir = tmp_path / "docs" / "report" / "figures"
    generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)

    # Tamper with fig2
    fig2 = fig_dir / "fig2_accuracy_vs_k.svg"
    fig2.write_text(fig2.read_text(encoding="utf-8") + "<!-- tamper -->", encoding="utf-8")

    res = check_figure_provenance(fig_dir)
    assert res["status"] == "FAIL"
    assert len(res["hash_mismatches"]) == 1


def test_tamper_table_body_fail_closed(tmp_path: Path):
    """Verify that tampering with Table 3 values fails closed even if HTML comments retain correct strings."""
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    # Mutate Table 3
    t3 = tbl_dir / "table3_rq1_attribution_performance.md"
    orig = t3.read_text(encoding="utf-8")
    t3.write_text(orig.replace("79.53%", "97.53%") + "\n<!-- 77.99% 79.53% +1.532 pp -->\n", encoding="utf-8")

    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="generated",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert any("Table 3 accuracy" in m for m in report["numerical_consistency"]["mismatches"])


def test_wrong_p_value_fail_closed(tmp_path: Path):
    """Verify that tampering with McNemar p-value fails closed."""
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    t3 = tbl_dir / "table3_rq1_attribution_performance.md"
    orig = t3.read_text(encoding="utf-8")
    t3.write_text(orig.replace("0.422", "0.042"), encoding="utf-8")

    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="generated",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert any("McNemar p-value" in m for m in report["numerical_consistency"]["mismatches"])


def test_wrong_resource_denominator_fail_closed(tmp_path: Path):
    """Verify that asserting N=718 for resource table fails closed."""
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    t5 = tbl_dir / "table5_rq3_resources_and_cost.md"
    t5.write_text(t5.read_text(encoding="utf-8") + "\nAll resources are measured on TEST N=718.\n", encoding="utf-8")

    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="generated",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert any("invalid resource denominator" in m for m in report["numerical_consistency"]["mismatches"])


def test_fixture_rejected_in_all_scope(tmp_path: Path):
    """Verify that fixture artifacts are rejected in full publication (--scope all) audit."""
    fig_dir = tmp_path / "docs" / "report" / "figures"
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    (tmp_path / "README.md").write_text("# RAG2ATTCK\n", encoding="utf-8")
    (tmp_path / "docs" / "report").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "report" / "scientific_report.md").write_text("# Report\n", encoding="utf-8")
    (tmp_path / "docs" / "presentation").mkdir(parents=True, exist_ok=True)
    (tmp_path / "docs" / "presentation" / "slides.md").write_text("# Slides\n", encoding="utf-8")
    (tmp_path / "docs" / "report" / "scientific_report.docx").write_bytes(b"PK\x03\x04")
    (tmp_path / "docs" / "presentation" / "slides.pptx").write_bytes(b"PK\x03\x04")

    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="all",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert report["fixture_in_all_scope"] is True


def test_docx_binary_inspection_fail_closed(tmp_path: Path):
    """Verify that corrupted embedded media or altered visible accuracy in DOCX fails."""
    docx_file = tmp_path / "scientific_report.docx"

    # Test corrupted media
    with zipfile.ZipFile(docx_file, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>79.53%</w:t></w:document>")
        z.writestr("word/media/image1.png", b"WRONG_FIXTURE_MEDIA")

    errors = check_docx_binary(docx_file)
    assert len(errors) == 1
    assert "Invalid embedded PNG media" in errors[0]

    # Test altered visible text
    with zipfile.ZipFile(docx_file, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>97.53%</w:t></w:document>")

    errors = check_docx_binary(docx_file)
    assert len(errors) == 1
    assert "Altered DOCX visible accuracy" in errors[0]


def test_pptx_binary_inspection_fail_closed(tmp_path: Path):
    """Verify that tiny font size or [WRONG RESULT] placeholder in PPTX fails."""
    pptx_file = tmp_path / "slides.pptx"

    with zipfile.ZipFile(pptx_file, "w") as z:
        z.writestr("ppt/slides/slide8.xml", '<p:sld><a:r><a:rPr sz="713"/><a:t>[WRONG RESULT]</a:t></a:r></p:sld>')

    errors = check_pptx_binary(pptx_file)
    assert len(errors) >= 2
    assert any("[WRONG RESULT]" in e for e in errors)
    assert any("Tiny font size" in e for e in errors)
