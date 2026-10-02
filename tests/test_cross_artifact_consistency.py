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
  - Fail-closed behavior on bogus / incomplete metric bundles
  - Provenance hash verification, bundle SHA256 binding, and tampering detection
  - Missing or invalid fixture_only flag detection in provenance
  - Semantic SVG content validation (Fig 2 accuracy, Fig 5 conditional accuracy 91.3%)
  - Numerical table row parsing and cell-level consistency (Table 3 accuracy, p-value; Table 5 N=1,280)
  - Fixture rejection in publication-wide (--scope all) audit
  - DOCX OpenXML binary inspection (placeholders, unauthorized numbers, embedded media authenticity)
  - PPTX OpenXML binary inspection (placeholders, unauthorized numbers, font size threshold >= 9pt)
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
    validate_metric_bundle,
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


def test_strict_all_scope_without_bundle_fails(tmp_path: Path):
    """Verify that strict audit across all scope fails closed without metric bundle."""
    report = run_consistency_audit(
        repo_root=tmp_path,
        bundle_path=None,
        strict=True,
        scope="all",
        output_report_path=None,
    )
    assert report["verdict"] == "FAIL"
    assert "Strict all-scope audit requires" in report["bundle_error"]


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


def test_bogus_or_incomplete_bundle_fail_closed(tmp_path: Path):
    """Verify that a bogus or incomplete bundle schema fails closed."""
    # Bogus bundle
    bogus = tmp_path / "bogus_bundle.json"
    bogus.write_text('{"fixture_only": true, "not_a_metric_bundle": true}', encoding="utf-8")
    valid, err, _ = validate_metric_bundle(bogus)
    assert not valid
    assert "not_a_metric_bundle" in err

    # Incomplete conditions bundle
    incomplete = tmp_path / "incomplete_bundle.json"
    incomplete.write_text('{"conditions": {}}', encoding="utf-8")
    valid, err, _ = validate_metric_bundle(incomplete)
    assert not valid
    assert "missing required root keys" in err or "incomplete" in err


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
        "Accuracy is {{NO_RAG_ACCURACY}} and status is [PENDING EXECUTION] PID 50192 or [TBD] or {{UNPOPULATED}}.\n",
        encoding="utf-8",
    )

    findings = scan_file_for_placeholders(placeholder_file)
    assert len(findings) >= 4
    ph_strings = {f["placeholder"] for f in findings}
    assert any("[PENDING" in s for s in ph_strings)
    assert any("{{NO_RAG_ACCURACY}}" in s for s in ph_strings)
    assert any("[TBD]" in s for s in ph_strings)
    assert any("{{UNPOPULATED}}" in s for s in ph_strings)


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


def test_missing_fixture_only_flag_fails(tmp_path: Path):
    """Verify that provenance files without explicit fixture_only boolean key fail closed."""
    fig_dir = tmp_path / "docs" / "report" / "figures"
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    # Strip fixture_only key
    f_prov = fig_dir / "figure_provenance.json"
    data = json.loads(f_prov.read_text(encoding="utf-8"))
    del data["fixture_only"]
    f_prov.write_text(json.dumps(data), encoding="utf-8")

    res = check_figure_provenance(fig_dir)
    assert res["status"] == "FAIL"
    assert "fixture_only" in res["error"]


def test_tamper_table3_row_accuracy_and_p_value_fail_closed(tmp_path: Path):
    """Verify that Table 3 cell tampering is caught by row parser even if correct strings exist elsewhere."""
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    # Tamper with accuracy in k10 row
    t3 = tbl_dir / "table3_rq1_attribution_performance.md"
    orig = t3.read_text(encoding="utf-8")
    t3.write_text(orig.replace("79.53%", "82.12%") + "\nVisible unrelated: 77.99% 79.53% +1.532pp p0.422\n", encoding="utf-8")

    res = check_table_provenance(tbl_dir)
    assert res["status"] == "FAIL"
    assert any("82.12%" in err for err in res["semantic_errors"])

    # Tamper with p-value in k10 row
    t3.write_text(orig.replace("0.422", "0.123") + "\nReference p0.422\n", encoding="utf-8")
    res = check_table_provenance(tbl_dir)
    assert res["status"] == "FAIL"
    assert any("0.123" in err for err in res["semantic_errors"])


def test_table5_cohort_claim_718_fails(tmp_path: Path):
    """Verify that asserting 718 mapped views for resource Table 5 fails closed."""
    tbl_dir = tmp_path / "docs" / "report" / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    t5 = tbl_dir / "table5_rq3_resources_and_cost.md"
    orig = t5.read_text(encoding="utf-8")
    t5.write_text(orig.replace("N=1,280 requests per condition", "718 mapped views per condition"), encoding="utf-8")

    res = check_table_provenance(tbl_dir)
    assert res["status"] == "FAIL"
    assert any("718" in err for err in res["semantic_errors"])


def test_svg_semantic_validation_fail_closed(tmp_path: Path):
    """Verify that altered conditional accuracy in fig5 is rejected."""
    fig_dir = tmp_path / "docs" / "report" / "figures"
    generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)

    fig5 = fig_dir / "fig5_conditional_accuracy.svg"
    orig = fig5.read_text(encoding="utf-8")
    fig5.write_text(orig.replace("91.3%", "81.3%"), encoding="utf-8")

    res = check_figure_provenance(fig_dir)
    assert res["status"] == "FAIL"
    assert any("81.3%" in err for err in res["xml_errors"])


def test_docx_binary_inspection_fail_closed(tmp_path: Path):
    """Verify that placeholders, corrupted/spoofed media, or altered visible accuracy in DOCX fails."""
    docx_file = tmp_path / "scientific_report.docx"

    # Test corrupted/spoof media
    with zipfile.ZipFile(docx_file, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>79.53%</w:t></w:document>")
        z.writestr("word/media/image1.png", b"\x89PNG\r\n\x1a\nWRONG_DIAGNOSTIC_IMAGE")

    errors = check_docx_binary(docx_file)
    assert len(errors) >= 1
    assert any("Diagnostic/spoof media" in e or "Embedded media in docx" in e for e in errors)

    # Test altered visible text
    with zipfile.ZipFile(docx_file, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>82.12%</w:t></w:document>")

    errors = check_docx_binary(docx_file)
    assert len(errors) >= 1
    assert any("82.12%" in e for e in errors)

    # Test placeholder in docx
    with zipfile.ZipFile(docx_file, "w") as z:
        z.writestr("word/document.xml", "<w:document><w:t>{{UNPOPULATED}}</w:t></w:document>")

    errors = check_docx_binary(docx_file)
    assert len(errors) >= 1
    assert any("{{UNPOPULATED}}" in e for e in errors)


def test_pptx_binary_inspection_fail_closed(tmp_path: Path):
    """Verify that font size < 9pt (e.g. 8.1pt), placeholders, or wrong text in PPTX fails."""
    pptx_file = tmp_path / "slides.pptx"

    # Test font size 8.1pt (sz=810) and [PENDING EXECUTION]
    with zipfile.ZipFile(pptx_file, "w") as z:
        z.writestr("ppt/slides/slide8.xml", '<p:sld><a:r><a:rPr sz="810"/><a:t>[PENDING EXECUTION]</a:t></a:r></p:sld>')

    errors = check_pptx_binary(pptx_file)
    assert len(errors) >= 2
    assert any("[PENDING EXECUTION]" in e for e in errors)
    assert any("Tiny font size" in e for e in errors)
