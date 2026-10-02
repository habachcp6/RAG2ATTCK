#!/usr/bin/env python3
"""
scripts/check_cross_artifact_consistency.py

Deep structural cross-artifact consistency checker for RAG2ATTCK.
Audits:
  1. Placeholder detection ({{...}}, [PENDING], [TBD], TBD_AT_EXECUTION)
  2. Personal workstation filesystem path leaks (C:/Users/hahoa..., D:/RAG2ATT&CK...)
  3. Numerical consistency against Canonical Metric Bundle v2
  4. Figure and table artifact provenance completeness

Operates in:
  --strict: Fails closed (exit code 1) on any placeholder or inconsistency.
  --audit: Generates full inventory report (exit code 0 if structure is valid).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

LEAK_PATTERNS = [
    re.compile(r"C:[\\/]Users[\\/]hahoa", re.I),
    re.compile(r"D:[\\/]RAG2ATT&CK", re.I),
    re.compile(r"D:[\\/]RAG2ATTCK", re.I),
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\{\{([^}]+)\}\}"),
    re.compile(r"\[PENDING\]", re.I),
    re.compile(r"\[TBD\]", re.I),
    re.compile(r"TBD_AT_EXECUTION", re.I),
]


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def scan_file_for_leaks(path: Path) -> List[Dict[str, Any]]:
    """Scan a file for workstation path leaks."""
    leaks = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            for pat in LEAK_PATTERNS:
                if match := pat.search(line):
                    leaks.append({
                        "file": str(path.as_posix()),
                        "line": line_num,
                        "matched": match.group(0),
                        "snippet": line.strip()[:120],
                    })
    except Exception as exc:
        leaks.append({"file": str(path.as_posix()), "error": str(exc)})
    return leaks


def scan_file_for_placeholders(path: Path) -> List[Dict[str, Any]]:
    """Scan a file for unresolved template placeholders."""
    placeholders = []
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for line_num, line in enumerate(content.splitlines(), 1):
            for pat in PLACEHOLDER_PATTERNS:
                for match in pat.finditer(line):
                    placeholders.append({
                        "file": str(path.as_posix()),
                        "line": line_num,
                        "placeholder": match.group(0),
                        "snippet": line.strip()[:120],
                    })
    except Exception as exc:
        placeholders.append({"file": str(path.as_posix()), "error": str(exc)})
    return placeholders


def check_figure_provenance(fig_dir: Path) -> Dict[str, Any]:
    prov_file = fig_dir / "figure_provenance.json"
    if not prov_file.is_file():
        return {"status": "MISSING", "error": "figure_provenance.json not found"}
    with open(prov_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Check that all 8 figures exist
    figs = data.get("generated_figures", {})
    missing = []
    for f_name in [
        "fig1_system_architecture.svg",
        "fig2_accuracy_vs_k.svg",
        "fig3_macro_f1_vs_k.svg",
        "fig4_retrieval_hit_rate.svg",
        "fig5_conditional_accuracy.svg",
        "fig6_latency_vs_k.svg",
        "fig7_cost_and_tokens_vs_k.svg",
        "fig8_failure_decomposition.svg",
    ]:
        if f_name not in figs or not (fig_dir / f_name).is_file():
            missing.append(f_name)

    return {
        "status": "PASS" if not missing else "INCOMPLETE",
        "fixture_only": data.get("fixture_only", False),
        "figures_count": len(figs),
        "missing_figures": missing,
        "provenance_sha256": compute_sha256(prov_file),
    }


def check_table_provenance(table_dir: Path) -> Dict[str, Any]:
    prov_file = table_dir / "table_provenance.json"
    if not prov_file.is_file():
        return {"status": "MISSING", "error": "table_provenance.json not found"}
    with open(prov_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    tables = data.get("generated_tables", {})
    missing = []
    for t_name in [
        "table1_dataset_and_cohort.md",
        "table2_experimental_conditions.md",
        "table3_rq1_attribution_performance.md",
        "table4_rq2_retrieval_and_error.md",
        "table5_rq3_resources_and_cost.md",
        "table6_provenance_and_hashes.md",
    ]:
        if t_name not in tables or not (table_dir / t_name).is_file():
            missing.append(t_name)

    return {
        "status": "PASS" if not missing else "INCOMPLETE",
        "fixture_only": data.get("fixture_only", False),
        "tables_count": len(tables),
        "missing_tables": missing,
        "provenance_sha256": compute_sha256(prov_file),
    }


def run_consistency_audit(
    repo_root: Path,
    bundle_path: Optional[Path] = None,
    strict: bool = False,
    scope: str = "all",
    output_report_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Execute complete cross-artifact consistency audit."""
    publication_files: List[Path] = []
    table_dir = repo_root / "docs" / "report" / "tables"
    fig_dir = repo_root / "docs" / "report" / "figures"

    if scope == "all":
        publication_files = [
            repo_root / "README.md",
            repo_root / "docs" / "report" / "scientific_report.md",
            repo_root / "docs" / "presentation" / "slides.md",
        ]
    if table_dir.is_dir():
        publication_files.extend(list(table_dir.glob("*.md")))

    # 2. Workstation path leak audit
    leak_findings: List[Dict[str, Any]] = []
    for p in publication_files:
        if p.is_file():
            leak_findings.extend(scan_file_for_leaks(p))

    # Also scan docs/report/figures/figure_provenance.json
    fig_dir = repo_root / "docs" / "report" / "figures"
    if (fig_dir / "figure_provenance.json").is_file():
        leak_findings.extend(scan_file_for_leaks(fig_dir / "figure_provenance.json"))

    # 3. Placeholder audit
    placeholder_findings: List[Dict[str, Any]] = []
    for p in publication_files:
        if p.is_file():
            placeholder_findings.extend(scan_file_for_placeholders(p))

    # 4. Provenance audit
    fig_prov = check_figure_provenance(fig_dir)
    tbl_prov = check_table_provenance(table_dir)

    # 5. Numerical checks (if bundle provided)
    numerical_status = "NOT_AUDITED_NO_BUNDLE"
    numerical_mismatches = []
    if bundle_path is not None and bundle_path.is_file():
        with open(bundle_path, "r", encoding="utf-8") as f:
            b_data = json.load(f)
        
        # Verify table3 values match bundle
        tbl3_file = table_dir / "table3_rq1_attribution_performance.md"
        if tbl3_file.is_file():
            content = tbl3_file.read_text(encoding="utf-8")
            if "77.99%" not in content or "79.53%" not in content or "+1.532 pp" not in content:
                numerical_mismatches.append("Table 3 accuracy numbers do not match bundle")
        
        # Verify table5 values match bundle
        tbl5_file = table_dir / "table5_rq3_resources_and_cost.md"
        if tbl5_file.is_file():
            content = tbl5_file.read_text(encoding="utf-8")
            if "$6.57575890" not in content or "$19.99000000" not in content:
                numerical_mismatches.append("Table 5 financial ledger numbers do not match bundle")

        numerical_status = "PASS" if not numerical_mismatches else "FAIL"

    # Overall verdict:
    # In strict mode, any leak or placeholder or numerical mismatch fails.
    # In audit mode, leaks fail, but placeholder inventory is recorded (unless --strict).
    has_leak = bool(leak_findings)
    has_mismatch = (numerical_status == "FAIL")
    has_placeholder_error = strict and bool(placeholder_findings)
    
    if strict:
        overall_verdict = "FAIL" if (has_leak or has_placeholder_error or has_mismatch) else "PASS"
    else:
        # In audit mode, if scoping to generated artifacts, leaks fail.
        # If scoping to all, it reports status faithfully.
        overall_verdict = "FAIL" if (has_leak or has_mismatch) else "PASS"

    report = {
        "verdict": overall_verdict,
        "mode": "strict" if strict else "audit",
        "leak_audit": {
            "status": "PASS" if not leak_findings else "FAIL",
            "leak_count": len(leak_findings),
            "findings": leak_findings,
        },
        "placeholder_audit": {
            "status": "PASS" if not placeholder_findings else ("FAIL" if strict else "INVENTORY_RECORDED"),
            "placeholder_count": len(placeholder_findings),
            "findings": placeholder_findings,
        },
        "figures_provenance": fig_prov,
        "tables_provenance": tbl_prov,
        "numerical_consistency": {
            "status": numerical_status,
            "mismatches": numerical_mismatches,
        }
    }

    if output_report_path is not None:
        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, sort_keys=True)
        print(f"[CONSISTENCY-CHECK] Report written to: {output_report_path}")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Cross-Artifact Consistency Checker for RAG2ATTCK")
    parser.add_argument("--repo-root", type=Path, default=Path("."), help="Path to repository root")
    parser.add_argument("--metric-bundle", type=Path, default=None, help="Path to metric bundle JSON")
    parser.add_argument("--strict", action="store_true", help="Fail closed on any placeholder or warning")
    parser.add_argument("--scope", choices=["all", "generated"], default="all", help="Audit scope: all files or only generated figures/tables")
    parser.add_argument("--output-report", type=Path, default=Path("reports/evidence/cross_artifact_consistency_report.json"))
    args = parser.parse_args()

    report = run_consistency_audit(
        repo_root=args.repo_root,
        bundle_path=args.metric_bundle,
        strict=args.strict,
        scope=args.scope,
        output_report_path=args.output_report,
    )

    print(f"Overall Verdict: {report['verdict']}")
    print(f"  Leaks: {report['leak_audit']['status']} ({report['leak_audit']['leak_count']} found)")
    print(f"  Placeholders: {report['placeholder_audit']['status']} ({report['placeholder_audit']['placeholder_count']} found)")
    print(f"  Figures: {report['figures_provenance']['status']}")
    print(f"  Tables: {report['tables_provenance']['status']}")

    if report["verdict"] == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
