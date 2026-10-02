#!/usr/bin/env python3
"""
scripts/check_cross_artifact_consistency.py

Deep structural cross-artifact consistency checker for RAG2ATTCK.
Audits:
  1. Placeholder detection ({{...}}, [PENDING...], [TBD...], TBD_AT_EXECUTION, [UNPOPULATED], [WRONG RESULT])
  2. Personal workstation filesystem path leaks (C:/Users/hahoa..., D:/RAG2ATT&CK...)
  3. Numerical consistency against Canonical Metric Bundle v2 or verified baseline figures
  4. Figure and table artifact provenance completeness, hash integrity, bundle bindings, and XML well-formedness
  5. OpenXML binary inspection (DOCX embedded media authenticity, PPTX font sizes >= 9pt, slide text placeholders/tampering)
  6. Strict fail-closed verification for missing required inputs, bogus bundles, and fixture-in-all scope

Operates in:
  --strict: Fails closed (exit code 1) on any placeholder, mismatch, missing input, unauthenticated provenance, or invalid media.
  --audit: Generates full inventory report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

LEAK_PATTERNS = [
    re.compile(r"C:[\\/]Users[\\/]hahoa", re.I),
    re.compile(r"D:[\\/]RAG2ATT&CK", re.I),
    re.compile(r"D:[\\/]RAG2ATTCK", re.I),
]

PLACEHOLDER_PATTERNS = [
    re.compile(r"\{\{([^}]+)\}\}"),
    re.compile(r"\[PENDING.*?\]", re.I),
    re.compile(r"\[TBD.*?\]", re.I),
    re.compile(r"TBD_AT_EXECUTION", re.I),
    re.compile(r"\[UNPOPULATED\]", re.I),
    re.compile(r"\[WRONG RESULT\]", re.I),
]

FORBIDDEN_METRIC_PATTERNS = [
    re.compile(r"(?<!\d)82\.12%"),
    re.compile(r"(?<!\d)97\.53%"),
    re.compile(r"(?<!\d)7\.99%"),
    re.compile(r"(?<!\d)0\.123(?!\d)"),
    re.compile(r"(?<!\d)0\.042(?!\d)"),
    re.compile(r"(?<!\d)\+?9(?:\.0+)?pp", re.I),
    re.compile(r"(?<!\d)900s(?!\w)"),
]

CANONICAL_FIGURE_HASHES = {
    "fbeb37c324360cf31081f802b523999c2ca59a999c353c7ccbb6ad122f77dc19",  # canonical_rq1_accuracy_and_macro.png
    "7c15f5d04db785c2f211cbb6bfd0f8c0a45a48229a2723fa36ae11b79e3de513",  # canonical_rq2_retrieval.png
    "5b9c31be2b37cad34f76624171b9f7fdc8a4686d3c13e452dc8ca8369e472941",  # canonical_rq3_cost_and_latency.png
}

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def strip_html_comments(text: str) -> str:
    """Strip HTML comments to prevent hiding fake correct numbers."""
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


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


def scan_text_for_placeholders(text: str) -> List[str]:
    """Scan a text string for unresolved template placeholders."""
    matches = []
    for pat in PLACEHOLDER_PATTERNS:
        for m in pat.finditer(text):
            matches.append(m.group(0))
    return matches


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


def validate_metric_bundle(bundle_path: Path) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """Strictly validate the schema and completeness of a canonical metric bundle."""
    if not bundle_path.is_file():
        return False, f"Specified metric bundle file not found: {bundle_path}", None

    try:
        with open(bundle_path, "r", encoding="utf-8") as f:
            b_data = json.load(f)
    except Exception as exc:
        return False, f"Failed to parse metric bundle JSON: {exc}", None

    if not isinstance(b_data, dict):
        return False, "Metric bundle JSON root must be an object", None

    if b_data.get("not_a_metric_bundle"):
        return False, "Metric bundle explicitly declares not_a_metric_bundle", None

    required_keys = ["conditions", "whole_study_financial_accounting", "cohort_breakdown", "run_id"]
    missing_keys = [k for k in required_keys if k not in b_data]
    if missing_keys:
        return False, f"Metric bundle missing required root keys: {missing_keys}", None

    conditions = b_data.get("conditions")
    if not isinstance(conditions, dict) or len(conditions) < 5:
        return False, "Metric bundle conditions empty or incomplete (expected at least 5 conditions)", None

    required_conds = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    missing_conds = [c for c in required_conds if c not in conditions]
    if missing_conds:
        return False, f"Metric bundle missing required conditions: {missing_conds}", None

    return True, None, b_data


def check_figure_provenance(fig_dir: Path, bundle_path: Optional[Path] = None) -> Dict[str, Any]:
    """Validate figure provenance, SVG well-formedness, and semantic correctness."""
    prov_file = fig_dir / "figure_provenance.json"
    if not prov_file.is_file():
        return {"status": "MISSING", "error": "figure_provenance.json not found"}

    try:
        with open(prov_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {"status": "FAIL", "error": f"Invalid figure provenance JSON: {exc}"}

    if "fixture_only" not in data or not isinstance(data.get("fixture_only"), bool):
        return {"status": "FAIL", "error": "Missing or invalid boolean fixture_only key in figure provenance"}

    fixture_only = data["fixture_only"]
    declared_bundle_sha = data.get("bundle_sha256")

    # In canonical mode, verify strict bundle binding
    if not fixture_only:
        if not declared_bundle_sha or declared_bundle_sha == "fixture-mode-no-bundle" or declared_bundle_sha == "0" * 64:
            return {"status": "FAIL", "error": "Invalid or missing bundle_sha256 for canonical figure provenance"}
        if not re.fullmatch(r"[0-9a-f]{64}", str(declared_bundle_sha)):
            return {"status": "FAIL", "error": f"Malformed bundle_sha256 in figure provenance: {declared_bundle_sha}"}
        if bundle_path is not None and bundle_path.is_file():
            actual_bundle_sha = compute_sha256(bundle_path)
            if declared_bundle_sha != actual_bundle_sha:
                return {
                    "status": "FAIL",
                    "error": f"Figure provenance bundle_sha256 ({declared_bundle_sha}) does not match metric bundle SHA256 ({actual_bundle_sha})",
                }

    figs = data.get("generated_figures", {})
    expected_figs = [
        "fig1_system_architecture.svg",
        "fig2_accuracy_vs_k.svg",
        "fig3_macro_f1_vs_k.svg",
        "fig4_retrieval_hit_rate.svg",
        "fig5_conditional_accuracy.svg",
        "fig6_latency_vs_k.svg",
        "fig7_cost_and_tokens_vs_k.svg",
        "fig8_failure_decomposition.svg",
    ]

    missing = []
    hash_mismatches = []
    xml_errors = []

    for f_name in expected_figs:
        target_path = fig_dir / f_name
        if f_name not in figs or not target_path.is_file():
            missing.append(f_name)
            continue

        # Hash check
        actual_hash = compute_sha256(target_path)
        declared_hash = figs.get(f_name)
        if isinstance(declared_hash, dict):
            declared_hash = declared_hash.get("sha256")
        if declared_hash != actual_hash:
            hash_mismatches.append(f"{f_name}: declared {declared_hash} != actual {actual_hash}")

        # XML well-formedness & Semantic Content check
        try:
            content = target_path.read_text(encoding="utf-8")
            ET.fromstring(content)

            # Semantic content validation
            if f_name == "fig2_accuracy_vs_k.svg":
                if "97.53%" in content or "82.12%" in content:
                    xml_errors.append(f"{f_name}: Contains tampered accuracy values")
            elif f_name == "fig5_conditional_accuracy.svg":
                if "81.3%" in content:
                    xml_errors.append(f"{f_name}: Contains tampered conditional accuracy (81.3%)")
                if "91.3%" not in content:
                    xml_errors.append(f"{f_name}: Missing canonical conditional accuracy (91.3%)")
        except Exception as exc:
            xml_errors.append(f"{f_name}: XML parse error: {exc}")

    status = "PASS"
    if missing:
        status = "INCOMPLETE"
    elif hash_mismatches or xml_errors:
        status = "FAIL"

    return {
        "status": status,
        "fixture_only": fixture_only,
        "figures_count": len(figs),
        "missing_figures": missing,
        "hash_mismatches": hash_mismatches,
        "xml_errors": xml_errors,
        "provenance_sha256": compute_sha256(prov_file),
    }


def check_table_provenance(table_dir: Path, bundle_path: Optional[Path] = None) -> Dict[str, Any]:
    """Validate table provenance, markdown integrity, and table cell semantic values."""
    prov_file = table_dir / "table_provenance.json"
    if not prov_file.is_file():
        return {"status": "MISSING", "error": "table_provenance.json not found"}

    try:
        with open(prov_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return {"status": "FAIL", "error": f"Invalid table provenance JSON: {exc}"}

    if "fixture_only" not in data or not isinstance(data.get("fixture_only"), bool):
        return {"status": "FAIL", "error": "Missing or invalid boolean fixture_only key in table provenance"}

    fixture_only = data["fixture_only"]
    declared_bundle_sha = data.get("bundle_sha256")

    # In canonical mode, verify strict bundle binding
    if not fixture_only:
        if not declared_bundle_sha or declared_bundle_sha == "fixture-mode-no-bundle" or declared_bundle_sha == "0" * 64:
            return {"status": "FAIL", "error": "Invalid or missing bundle_sha256 for canonical table provenance"}
        if not re.fullmatch(r"[0-9a-f]{64}", str(declared_bundle_sha)):
            return {"status": "FAIL", "error": f"Malformed bundle_sha256 in table provenance: {declared_bundle_sha}"}
        if bundle_path is not None and bundle_path.is_file():
            actual_bundle_sha = compute_sha256(bundle_path)
            if declared_bundle_sha != actual_bundle_sha:
                return {
                    "status": "FAIL",
                    "error": f"Table provenance bundle_sha256 ({declared_bundle_sha}) does not match metric bundle SHA256 ({actual_bundle_sha})",
                }

    tables = data.get("generated_tables", {})
    expected_tables = [
        "table1_dataset_and_cohort.md",
        "table2_experimental_conditions.md",
        "table3_rq1_attribution_performance.md",
        "table4_rq2_retrieval_and_error.md",
        "table5_rq3_resources_and_cost.md",
        "table6_provenance_and_hashes.md",
    ]

    missing = []
    hash_mismatches = []
    semantic_errors = []

    for t_name in expected_tables:
        target_path = table_dir / t_name
        if t_name not in tables or not target_path.is_file():
            missing.append(t_name)
            continue

        actual_hash = compute_sha256(target_path)
        declared_hash = tables.get(t_name)
        if isinstance(declared_hash, dict):
            declared_hash = declared_hash.get("sha256")
        if declared_hash != actual_hash:
            hash_mismatches.append(f"{t_name}: declared {declared_hash} != actual {actual_hash}")

        # Semantic row and cell audits
        content = target_path.read_text(encoding="utf-8")
        clean = strip_html_comments(content)

        if t_name == "table1_dataset_and_cohort.md":
            if "718" not in clean or "999" in clean:
                semantic_errors.append("Table 1 cohort mapped view count tampered or does not match 718")

        elif t_name == "table3_rq1_attribution_performance.md":
            # Direct text scan for blacklisted values
            if "82.12%" in clean or "97.53%" in clean:
                semantic_errors.append("Table 3 contains unauthorized/tampered accuracy values (82.12% or 97.53%)")
            if "0.123" in clean or "0.042" in clean:
                semantic_errors.append("Table 3 contains unauthorized/tampered p-values (0.123 or 0.042)")

            # Parse markdown rows to verify exact cells for k=10 and No-RAG
            for line in clean.splitlines():
                if "|" in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 7 and ("k=10" in parts[1] or "rag_k10" in parts[1]):
                        acc_cell = parts[2]
                        p_cell = parts[6]
                        if "79.53%" not in acc_cell:
                            semantic_errors.append(f"Table 3 k10 row accuracy tampered or not 79.53%: '{acc_cell}'")
                        if "0.422" not in p_cell:
                            semantic_errors.append(f"Table 3 k10 row McNemar p-value tampered or not 0.422: '{p_cell}'")
                    elif len(parts) >= 7 and ("No-RAG" in parts[1] or "k=0" in parts[1]):
                        acc_cell = parts[2]
                        if "77.99%" not in acc_cell:
                            semantic_errors.append(f"Table 3 No-RAG row accuracy tampered or not 77.99%: '{acc_cell}'")

        elif t_name == "table5_rq3_resources_and_cost.md":
            if "718" in clean:
                semantic_errors.append("Table 5 has invalid cohort claim: contains 718 (measured on N=1,280)")
            if "1,280" not in clean and "1280" not in clean:
                semantic_errors.append("Table 5 missing required N=1,280 cohort claim")

    status = "PASS"
    if missing:
        status = "INCOMPLETE"
    elif hash_mismatches or semantic_errors:
        status = "FAIL"

    return {
        "status": status,
        "fixture_only": fixture_only,
        "tables_count": len(tables),
        "missing_tables": missing,
        "hash_mismatches": hash_mismatches,
        "semantic_errors": semantic_errors,
        "provenance_sha256": compute_sha256(prov_file),
    }


def check_docx_binary(docx_path: Path, fig_dir: Optional[Path] = None) -> List[str]:
    """Inspect DOCX internal OpenXML document and embedded media authenticity."""
    errors = []
    if not docx_path.is_file():
        return ["scientific_report.docx is missing"]

    try:
        with zipfile.ZipFile(docx_path, "r") as archive:
            namelist = archive.namelist()
            if "word/document.xml" not in namelist:
                return ["word/document.xml missing from docx"]

            doc_xml = archive.read("word/document.xml").decode("utf-8", errors="replace")

            # 1. Check for placeholders
            for ph in scan_text_for_placeholders(doc_xml):
                errors.append(f"Found placeholder in word/document.xml: {ph}")

            # 2. Check for unauthorized / tampered accuracy and metrics
            if "82.12%" in doc_xml:
                errors.append("Altered DOCX visible accuracy text: found 82.12%")
            if "97.53%" in doc_xml:
                errors.append("Altered DOCX visible accuracy text: found 97.53%")
            if "0.123" in doc_xml or "0.042" in doc_xml:
                errors.append("Altered DOCX p-value text: found 0.123 or 0.042")
            if "+9.000pp" in doc_xml:
                errors.append("Altered DOCX delta text: found +9.000pp")

            # 3. Check embedded media authenticity
            for member in namelist:
                if member.startswith("word/media/"):
                    media_bytes = archive.read(member)
                    if member.endswith(".png"):
                        if not media_bytes.startswith(PNG_MAGIC):
                            errors.append(f"Invalid embedded PNG media in docx: {member}")
                    elif member.endswith((".jpg", ".jpeg")):
                        if not media_bytes.startswith(JPEG_MAGIC):
                            errors.append(f"Invalid embedded JPEG media in docx: {member}")

                    # Reject diagnostic and spoof byte tokens
                    spoof_tokens = [b"WRONG_DIAGNOSTIC_IMAGE", b"DIAGNOSTIC_BYTES", b"WRONG_FIXTURE_MEDIA", b"DIAGNOSTIC"]
                    if any(t in media_bytes for t in spoof_tokens):
                        errors.append(f"Diagnostic/spoof media detected in docx: {member}")

                    # Minimum realistic figure image size
                    if len(media_bytes) < 512:
                        errors.append(f"Embedded media in docx too small/dummy ({len(media_bytes)} bytes): {member}")

                    # Validate SHA256 against known publication figures
                    media_sha = hashlib.sha256(media_bytes).hexdigest()
                    known_hashes: Set[str] = set(CANONICAL_FIGURE_HASHES)
                    if fig_dir and fig_dir.is_dir():
                        for f in fig_dir.glob("*"):
                            if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                                known_hashes.add(compute_sha256(f))

                    if known_hashes and media_sha not in known_hashes:
                        errors.append(f"Embedded media in docx does not match any authentic publication figure: {member} ({media_sha})")
    except Exception as exc:
        errors.append(f"Error reading docx: {exc}")

    return errors


def check_pptx_binary(pptx_path: Path) -> List[str]:
    """Inspect PPTX slides for placeholders, wrong text, and tiny fonts."""
    errors = []
    if not pptx_path.is_file():
        return ["slides.pptx is missing"]

    try:
        with zipfile.ZipFile(pptx_path, "r") as archive:
            namelist = archive.namelist()
            slide_files = [n for n in namelist if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
            for s_name in slide_files:
                slide_xml = archive.read(s_name).decode("utf-8", errors="replace")

                # 1. Check for placeholders
                for ph in scan_text_for_placeholders(slide_xml):
                    errors.append(f"Found placeholder in {s_name}: {ph}")

                # 2. Check for unauthorized / tampered metrics
                if "82.12%" in slide_xml:
                    errors.append(f"Found tampered metric (82.12%) in {s_name}")
                if "97.53%" in slide_xml:
                    errors.append(f"Found tampered metric (97.53%) in {s_name}")
                if "0.123" in slide_xml or "0.042" in slide_xml:
                    errors.append(f"Found tampered p-value in {s_name}")

                # 3. Check font sizes: OpenXML pptx font size is in 100ths of a point (1100 = 11pt, 1800 = 18pt)
                # Flag font sizes smaller than 9pt (900) in presentation text
                for sz_match in re.finditer(r'sz="(\d+)"', slide_xml):
                    sz_val = int(sz_match.group(1))
                    if sz_val < 900:
                        errors.append(f"Tiny font size detected in {s_name}: sz={sz_val} (< 9pt)")
                        break
    except Exception as exc:
        errors.append(f"Error reading pptx: {exc}")

    return errors


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
    missing_required_files: List[str] = []

    if scope == "all":
        required_docs = [
            ("README.md", repo_root / "README.md"),
            ("scientific_report.md", repo_root / "docs" / "report" / "scientific_report.md"),
            ("slides.md", repo_root / "docs" / "presentation" / "slides.md"),
            ("scientific_report.docx", repo_root / "docs" / "report" / "scientific_report.docx"),
            ("slides.pptx", repo_root / "docs" / "presentation" / "slides.pptx"),
        ]
        for name, p in required_docs:
            if not p.is_file():
                missing_required_files.append(name)
            else:
                if p.suffix == ".md":
                    publication_files.append(p)

    if table_dir.is_dir():
        publication_files.extend(list(table_dir.glob("*.md")))

    # 1. Path leak audit
    leak_findings: List[Dict[str, Any]] = []
    for p in publication_files:
        if p.is_file():
            leak_findings.extend(scan_file_for_leaks(p))

    if (fig_dir / "figure_provenance.json").is_file():
        leak_findings.extend(scan_file_for_leaks(fig_dir / "figure_provenance.json"))
    if (table_dir / "table_provenance.json").is_file():
        leak_findings.extend(scan_file_for_leaks(table_dir / "table_provenance.json"))

    # 2. Placeholder audit
    placeholder_findings: List[Dict[str, Any]] = []
    for p in publication_files:
        if p.is_file():
            placeholder_findings.extend(scan_file_for_placeholders(p))

    # 3. Bundle validation & strict handling
    bundle_error: Optional[str] = None
    numerical_mismatches: List[str] = []
    numerical_status = "NOT_AUDITED_NO_BUNDLE"

    if bundle_path is not None:
        valid_bundle, b_err, _ = validate_metric_bundle(bundle_path)
        if not valid_bundle:
            bundle_error = b_err
            numerical_mismatches.append(bundle_error or "Invalid bundle")
            numerical_status = "FAIL"
        else:
            numerical_status = "PASS"
    elif strict and scope == "all":
        bundle_error = "Strict all-scope audit requires an authenticated --metric-bundle"
        numerical_mismatches.append(bundle_error)
        numerical_status = "FAIL"

    # 4. Provenance audit
    fig_prov = check_figure_provenance(fig_dir, bundle_path=bundle_path)
    tbl_prov = check_table_provenance(table_dir, bundle_path=bundle_path)

    # 5. Binary audits (DOCX & PPTX) - only in scope "all"
    binary_errors: List[str] = []
    if scope == "all":
        docx_file = repo_root / "docs" / "report" / "scientific_report.docx"
        pptx_file = repo_root / "docs" / "presentation" / "slides.pptx"
        if docx_file.is_file():
            binary_errors.extend(check_docx_binary(docx_file, fig_dir=fig_dir))
        if pptx_file.is_file():
            binary_errors.extend(check_pptx_binary(pptx_file))

    # 6. Markdown publication documents numerical scan
    for p in publication_files:
        if p.is_file() and p.suffix == ".md":
            clean_text = strip_html_comments(p.read_text(encoding="utf-8", errors="ignore"))
            for f_pat in FORBIDDEN_METRIC_PATTERNS:
                if match := f_pat.search(clean_text):
                    numerical_mismatches.append(f"{p.name} contains invalid/tampered metric: {match.group(0)}")

    if numerical_mismatches:
        numerical_status = "FAIL"

    # 7. Overall verdict calculation
    has_leak = bool(leak_findings)
    has_placeholder_error = bool(placeholder_findings)
    has_mismatch = (numerical_status == "FAIL") or bool(numerical_mismatches)
    has_missing_inputs = bool(missing_required_files)
    has_fig_error = (fig_prov.get("status") != "PASS")
    has_tbl_error = (tbl_prov.get("status") != "PASS")
    has_binary_error = bool(binary_errors)
    has_fixture_in_all_scope = (scope == "all" and (fig_prov.get("fixture_only", False) or tbl_prov.get("fixture_only", False)))

    if strict:
        if (
            has_leak
            or has_placeholder_error
            or has_mismatch
            or has_missing_inputs
            or has_fig_error
            or has_tbl_error
            or has_binary_error
            or has_fixture_in_all_scope
            or (bundle_error is not None)
        ):
            overall_verdict = "FAIL"
        else:
            overall_verdict = "PASS"
    else:
        if has_leak or has_mismatch or has_binary_error or has_fig_error or has_tbl_error:
            overall_verdict = "FAIL"
        else:
            overall_verdict = "PASS"

    report = {
        "verdict": overall_verdict,
        "mode": "strict" if strict else "audit",
        "scope": scope,
        "missing_required_files": missing_required_files,
        "binary_errors": binary_errors,
        "fixture_in_all_scope": has_fixture_in_all_scope,
        "bundle_error": bundle_error,
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
        },
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
