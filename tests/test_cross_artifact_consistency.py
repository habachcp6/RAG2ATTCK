"""
tests/test_cross_artifact_consistency.py

Test suite for Track D publication figure & table generators and cross-artifact consistency checker.
Validates:
  - Generation of all 8 figures and 6 tables in fixture-only mode
  - Provenance integrity (no workstation path leaks, explicit units, p95 suppression)
  - Detection and fail-closed rejection of workstation path leaks
  - Detection and fail-closed rejection of unresolved template placeholders
  - Detection of missing table or figure artifacts
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.check_cross_artifact_consistency import (
    check_figure_provenance,
    check_table_provenance,
    run_consistency_audit,
    scan_file_for_leaks,
    scan_file_for_placeholders,
)
from scripts.generate_publication_figures import generate_all_figures
from scripts.generate_publication_tables import generate_all_tables


def test_fixture_generation_and_audit(tmp_path: Path):
    """Verify that all 8 figures and 6 tables generate and pass audit."""
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

    t_res = check_table_provenance(tbl_dir)
    assert t_res["status"] == "PASS"
    assert len(t_res["missing_tables"]) == 0

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
    """Verify that unresolved template placeholders are detected."""
    placeholder_file = tmp_path / "incomplete_document.md"
    placeholder_file.write_text(
        "Accuracy is {{NO_RAG_ACCURACY}} and status is [PENDING] or [TBD].\n",
        encoding="utf-8",
    )

    findings = scan_file_for_placeholders(placeholder_file)
    assert len(findings) == 3
    ph_strings = {f["placeholder"] for f in findings}
    assert "{{NO_RAG_ACCURACY}}" in ph_strings
    assert "[PENDING]" in ph_strings
    assert "[TBD]" in ph_strings


def test_missing_figure_detection(tmp_path: Path):
    """Verify that missing figures are flagged as INCOMPLETE."""
    fig_dir = tmp_path / "figures"
    generate_all_figures(bundle_path=None, fixture_only=True, output_dir=fig_dir)

    # Delete one figure
    target = fig_dir / "fig4_retrieval_hit_rate.svg"
    target.unlink()

    res = check_figure_provenance(fig_dir)
    assert res["status"] == "INCOMPLETE"
    assert "fig4_retrieval_hit_rate.svg" in res["missing_figures"]


def test_missing_table_detection(tmp_path: Path):
    """Verify that missing tables are flagged as INCOMPLETE."""
    tbl_dir = tmp_path / "tables"
    generate_all_tables(bundle_path=None, fixture_only=True, output_dir=tbl_dir)

    # Delete one table
    target = tbl_dir / "table3_rq1_attribution_performance.md"
    target.unlink()

    res = check_table_provenance(tbl_dir)
    assert res["status"] == "INCOMPLETE"
    assert "table3_rq1_attribution_performance.md" in res["missing_tables"]
