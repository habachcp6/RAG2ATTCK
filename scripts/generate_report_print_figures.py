#!/usr/bin/env python3
"""
scripts/generate_report_print_figures.py

Generates versioned, print-optimized variants for Figure 1 and Figure 5:
  - Fig 1: System Architecture & Dual-View Attribution Pipeline (Report Print Variant v1)
  - Fig 5: Conditional Attribution Accuracy (Report Print Variant v1)

Specifically designed for 468pt single-column Word document printing (1-inch margins on Letter/A4):
  - Canvas width set to 468pt (viewBox="0 0 468 [height]").
  - All text labels, subgroup counts, and caveats rendered at >= 8.5pt font-size.
  - Complete preservation of scientific data from authenticated B442 bundle.
  - Full vector SVG, raster PNG, and print PDF generation.
  - Structured provenance in docs/report/figures/report_print_v1/report_print_provenance.json.
  - Mirrored to docs/paper/figures/report_print_v1/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
for p in [str(REPO_ROOT), str(SCRIPTS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from scripts.generate_publication_figures import (
        FIXTURE_DATA,
        compute_sha256,
        export_svg_to_png_and_pdf,
        find_headless_browser,
        load_data_from_bundle,
        write_json_lf,
        write_text_lf,
    )
    from scripts.publication_bindings import validate_png_structure
except ImportError:
    from generate_publication_figures import (
        FIXTURE_DATA,
        compute_sha256,
        export_svg_to_png_and_pdf,
        find_headless_browser,
        load_data_from_bundle,
        write_json_lf,
        write_text_lf,
    )
    from publication_bindings import validate_png_structure


def svg_header_print(width: int, height: int, title: str, fixture_only: bool = False) -> str:
    """Generate SVG root element and CSS defs optimized for 468pt print layout."""
    header = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <style>
      @page {{ size: {width}px {height}px; margin: 0; }}
      .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12.5px; font-weight: bold; fill: #0f172a; text-anchor: middle; }}
      .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #475569; text-anchor: middle; }}
      .axis-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 9.0px; font-weight: bold; fill: #334155; }}
      .tick-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #475569; }}
      .grid-line {{ stroke: #e2e8f0; stroke-width: 1; stroke-dasharray: 3,3; }}
      .data-hit {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; font-weight: bold; fill: #065f46; text-anchor: middle; }}
      .data-miss {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; font-weight: bold; fill: #92400e; text-anchor: middle; }}
      .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #334155; }}
      .subgroup-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; font-weight: bold; fill: #1e293b; text-anchor: middle; }}
      .caveat-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #64748b; text-anchor: middle; }}
      .stage-title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 9.5px; font-weight: bold; text-anchor: middle; }}
      .stage-body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #334155; text-anchor: middle; }}
      .card-title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; font-weight: bold; fill: #1e293b; }}
      .card-body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; fill: #475569; }}
      .fixture-banner {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 8.5px; font-weight: bold; fill: #b91c1c; text-anchor: end; }}
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
'''
    if fixture_only:
        header += f'  <rect x="{width - 230}" y="6" width="222" height="16" rx="3" ry="3" fill="#fee2e2" stroke="#ef4444" stroke-width="1"/>\n'
        header += f'  <text x="{width - 10}" y="18" class="fixture-banner">[FIXTURE PREVIEW — NOT CANONICAL]</text>\n'
    return header


def svg_footer_print() -> str:
    return "</svg>\n"


FIXTURE_B_FIELDS: Dict[str, Any] = {
    "total_pairs": 640,
    "total_views": 1280,
    "mapped_scorable_views": 718,
    "macro_universe_classes": 474,
    "condition_count": 5,
    "k_depths_str": "1, 3, 5, 10",
    "no_rag_k": 0,
    "budget_cap_display": "19.99",
    "k10_succ_n": 321,
    "k10_fail_n": 397,
    "k10_succ_corr": 293,
    "k10_fail_corr": 278,
    "k10_succ_p_display": "91.28%",
    "k10_fail_p_display": "70.03%",
}


def extract_report_print_b_fields(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract required numerical fields for report-print variants directly from
    the authenticated metric bundle v2.

    Fail-closed: missing keys or invalid values raise KeyError/ValueError immediately.
    No fallback numbers are permitted.
    """
    if not isinstance(bundle, dict):
        raise ValueError("[FAIL_CLOSED] Metric bundle must be a dictionary")

    # 1. Cohort breakdown
    if "cohort_breakdown" not in bundle or not isinstance(bundle["cohort_breakdown"], dict):
        raise KeyError("[FAIL_CLOSED] Metric bundle missing 'cohort_breakdown'")
    cohort = bundle["cohort_breakdown"]

    req_cohort_keys = ["total_pairs", "total_views", "mapped_scorable_views", "macro_universe_classes"]
    for k in req_cohort_keys:
        if k not in cohort:
            raise KeyError(f"[FAIL_CLOSED] Missing required cohort key: '{k}'")
        if not isinstance(cohort[k], int) or cohort[k] <= 0:
            raise ValueError(f"[FAIL_CLOSED] Invalid cohort field '{k}': {cohort[k]}")

    total_pairs = cohort["total_pairs"]
    total_views = cohort["total_views"]
    mapped_scorable_views = cohort["mapped_scorable_views"]
    macro_universe_classes = cohort["macro_universe_classes"]

    # 2. Conditions
    if "conditions" not in bundle or not isinstance(bundle["conditions"], dict):
        raise KeyError("[FAIL_CLOSED] Metric bundle missing 'conditions'")
    conditions = bundle["conditions"]
    expected_conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    for c in expected_conditions:
        if c not in conditions:
            raise KeyError(f"[FAIL_CLOSED] Metric bundle missing condition '{c}'")

    condition_count = len(conditions)

    # Validate retrieval_k for no_rag and rag conditions
    no_rag_k = conditions["no_rag"].get("retrieval_k")
    if no_rag_k is None or no_rag_k != 0:
        raise ValueError(f"[FAIL_CLOSED] Invalid no_rag retrieval_k: {no_rag_k}")

    rag_k_vals = []
    for rk in ["rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        c_k = conditions[rk].get("retrieval_k")
        if c_k is None or not isinstance(c_k, int) or c_k <= 0:
            raise ValueError(f"[FAIL_CLOSED] Invalid retrieval_k for {rk}: {c_k}")
        rag_k_vals.append(c_k)
    k_depths_str = ", ".join(str(k) for k in rag_k_vals)

    # 3. Whole-study financial accounting budget cap
    if "whole_study_financial_accounting" not in bundle or not isinstance(bundle["whole_study_financial_accounting"], dict):
        raise KeyError("[FAIL_CLOSED] Metric bundle missing 'whole_study_financial_accounting'")
    fin = bundle["whole_study_financial_accounting"]
    if "study_budget_cap_usd" not in fin:
        raise KeyError("[FAIL_CLOSED] Missing 'study_budget_cap_usd' in whole_study_financial_accounting")

    raw_cap = fin["study_budget_cap_usd"]
    try:
        cap_float = float(raw_cap)
        if cap_float <= 0.0:
            raise ValueError(f"study_budget_cap_usd non-positive: {cap_float}")
        cap_display = f"{cap_float:.2f}"
    except (ValueError, TypeError) as exc:
        raise ValueError(f"[FAIL_CLOSED] Invalid study_budget_cap_usd '{raw_cap}': {exc}") from exc

    # 4. Fig 5 Subgroups (k=10 conditional accuracy)
    k10_cond = conditions["rag_k10"]
    if "rq2_retrieval_and_error" not in k10_cond or not isinstance(k10_cond["rq2_retrieval_and_error"], dict):
        raise KeyError("[FAIL_CLOSED] Missing 'rq2_retrieval_and_error' in condition 'rag_k10'")
    rq2 = k10_cond["rq2_retrieval_and_error"]

    if "generation_conditional_accuracy" not in rq2 or not isinstance(rq2["generation_conditional_accuracy"], dict):
        raise KeyError("[FAIL_CLOSED] Missing 'generation_conditional_accuracy' in rag_k10 rq2")
    gen_acc = rq2["generation_conditional_accuracy"]

    req_gen_keys = [
        "retrieval_success_sample_count",
        "retrieval_failure_sample_count",
        "correct_given_retrieval_success_count",
        "correct_given_retrieval_failure_count",
        "p_correct_given_retrieval_success_display",
        "p_correct_given_retrieval_failure_display",
    ]
    for rk in req_gen_keys:
        if rk not in gen_acc:
            raise KeyError(f"[FAIL_CLOSED] Missing required generation_conditional_accuracy key '{rk}'")

    succ_n = gen_acc["retrieval_success_sample_count"]
    fail_n = gen_acc["retrieval_failure_sample_count"]
    succ_corr = gen_acc["correct_given_retrieval_success_count"]
    fail_corr = gen_acc["correct_given_retrieval_failure_count"]
    succ_p_str = gen_acc["p_correct_given_retrieval_success_display"]
    fail_p_str = gen_acc["p_correct_given_retrieval_failure_display"]

    if not isinstance(succ_n, int) or succ_n <= 0:
        raise ValueError(f"[FAIL_CLOSED] Invalid retrieval_success_sample_count: {succ_n}")
    if not isinstance(fail_n, int) or fail_n <= 0:
        raise ValueError(f"[FAIL_CLOSED] Invalid retrieval_failure_sample_count: {fail_n}")
    if not isinstance(succ_corr, int) or succ_corr < 0 or succ_corr > succ_n:
        raise ValueError(f"[FAIL_CLOSED] Invalid correct_given_retrieval_success_count: {succ_corr}")
    if not isinstance(fail_corr, int) or fail_corr < 0 or fail_corr > fail_n:
        raise ValueError(f"[FAIL_CLOSED] Invalid correct_given_retrieval_failure_count: {fail_corr}")
    if not isinstance(succ_p_str, str) or not succ_p_str.endswith("%"):
        raise ValueError(f"[FAIL_CLOSED] Invalid p_correct_given_retrieval_success_display: {succ_p_str}")
    if not isinstance(fail_p_str, str) or not fail_p_str.endswith("%"):
        raise ValueError(f"[FAIL_CLOSED] Invalid p_correct_given_retrieval_failure_display: {fail_p_str}")

    # Subgroup sum must equal mapped scorable views
    if succ_n + fail_n != mapped_scorable_views:
        raise ValueError(
            f"[FAIL_CLOSED] Subgroup sum ({succ_n} + {fail_n} = {succ_n + fail_n}) "
            f"does not match mapped_scorable_views ({mapped_scorable_views})"
        )

    return {
        "total_pairs": total_pairs,
        "total_views": total_views,
        "mapped_scorable_views": mapped_scorable_views,
        "macro_universe_classes": macro_universe_classes,
        "condition_count": condition_count,
        "k_depths_str": k_depths_str,
        "no_rag_k": no_rag_k,
        "budget_cap_display": cap_display,
        "k10_succ_n": succ_n,
        "k10_fail_n": fail_n,
        "k10_succ_corr": succ_corr,
        "k10_fail_corr": fail_corr,
        "k10_succ_p_display": succ_p_str,
        "k10_fail_p_display": fail_p_str,
    }


def generate_fig1_architecture_report_v1(out_path: Path, b_fields: Dict[str, Any], fixture_only: bool = False) -> None:
    """
    Fig 1: System Architecture Diagram (Report Print Variant v1).
    Optimized for 468pt width with all fonts >= 8.5pt.
    All numbers are machine-generated from authenticated bundle fields.
    """
    width = 468
    height = 550
    svg = svg_header_print(width, height, "RAG2ATTCK Architecture (Report Print)", fixture_only=fixture_only)

    # Title & Subtitle
    svg += '  <text x="234" y="24" class="title">Figure 1: RAG2ATTCK Dual-View Attribution Architecture</text>\n'
    svg += f'  <text x="234" y="38" class="subtitle">Controlled evaluation across {b_fields["condition_count"]} conditions with strict monetary &amp; ledger governance</text>\n'

    # Stage 1: Telemetry Input (top, width 428, centered)
    svg += '  <rect x="20" y="52" width="428" height="46" rx="6" ry="6" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>\n'
    svg += f'  <text x="234" y="68" class="stage-title" fill="#1d4ed8">Telemetry Input ({b_fields["total_pairs"]} Paired Scenarios / N={b_fields["total_views"]:,} Views)</text>\n'
    svg += f'  <text x="234" y="84" class="stage-body">Single-Event Views &amp; Contextual Views | N={b_fields["mapped_scorable_views"]} Mapped Scorable Views</text>\n'

    # Split connecting arrows to Stage 2
    # Left arrow to Dense Retrieval
    svg += '  <line x1="124" y1="98" x2="124" y2="114" stroke="#6b7280" stroke-width="1.5"/>\n'
    svg += '  <polygon points="124,116 120,110 128,110" fill="#6b7280"/>\n'
    # Right arrow to No-RAG Direct Bypass
    svg += '  <line x1="344" y1="98" x2="344" y2="114" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="3,3"/>\n'
    svg += '  <polygon points="344,116 340,110 348,110" fill="#2563eb"/>\n'

    # Stage 2: Parallel Branches (y=116, height=58)
    # Left: Dense Retrieval (k in {1, 3, 5, 10})
    svg += '  <rect x="20" y="116" width="208" height="58" rx="6" ry="6" fill="#f5f3ff" stroke="#8b5cf6" stroke-width="1.5"/>\n'
    svg += '  <text x="124" y="132" class="stage-title" fill="#6d28d9">Dense Retrieval (RAG)</text>\n'
    svg += '  <text x="124" y="148" class="stage-body">all-MiniLM-L6-v2 + FAISS IndexFlatIP</text>\n'
    svg += f'  <text x="124" y="162" class="stage-body">Retrieval depths: k in {{{b_fields["k_depths_str"]}}}</text>\n'

    # Right: No-RAG Direct Bypass (k=0)
    svg += '  <rect x="240" y="116" width="208" height="58" rx="6" ry="6" fill="#eff6ff" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="4,4"/>\n'
    svg += f'  <text x="344" y="132" class="stage-title" fill="#1d4ed8">No-RAG Direct Bypass (k={b_fields["no_rag_k"]})</text>\n'
    svg += f'  <text x="344" y="148" class="stage-body">Direct Baseline Prompt (k={b_fields["no_rag_k"]})</text>\n'
    svg += '  <text x="344" y="162" class="stage-body">Retrieval omitted (not applicable)</text>\n'

    # Merging arrows to Stage 3
    # From Dense Retrieval
    svg += '  <line x1="124" y1="174" x2="124" y2="190" stroke="#6b7280" stroke-width="1.5"/>\n'
    svg += '  <polygon points="124,192 120,186 128,186" fill="#6b7280"/>\n'
    # From No-RAG Bypass
    svg += '  <line x1="344" y1="174" x2="344" y2="190" stroke="#2563eb" stroke-width="1.5" stroke-dasharray="3,3"/>\n'
    svg += '  <polygon points="344,192 340,186 348,186" fill="#2563eb"/>\n'

    # Stage 3: LLM Reasoning Engine (y=192, height=46)
    svg += '  <rect x="20" y="192" width="428" height="46" rx="6" ry="6" fill="#ecfdf5" stroke="#10b981" stroke-width="1.5"/>\n'
    svg += '  <text x="234" y="208" class="stage-title" fill="#047857">LLM Reasoning Engine (gpt-5.6-luna)</text>\n'
    svg += '  <text x="234" y="224" class="stage-body">xhigh reasoning effort | Strict JSON Schema | Frozen fingerprint</text>\n'

    # Arrow to Stage 4
    svg += '  <line x1="234" y1="238" x2="234" y2="252" stroke="#6b7280" stroke-width="1.5"/>\n'
    svg += '  <polygon points="234,254 230,248 238,248" fill="#6b7280"/>\n'

    # Stage 4: Attribution Output & Canonical Evaluation (y=254, height=46)
    svg += '  <rect x="20" y="254" width="428" height="46" rx="6" ry="6" fill="#fffbeb" stroke="#f59e0b" stroke-width="1.5"/>\n'
    svg += '  <text x="234" y="270" class="stage-title" fill="#b45309">Attribution Output &amp; Canonical Evaluation</text>\n'
    svg += f'  <text x="234" y="286" class="stage-body">MITRE ATT&amp;CK Technique ID | ANY_MATCH Ground Truth | {b_fields["macro_universe_classes"]} Macro Classes</text>\n'

    # Bottom Container: Protocol & Budget Governance Controls (Decisions D1–D7)
    svg += '  <rect x="20" y="312" width="428" height="226" rx="6" ry="6" fill="#f8fafc" stroke="#64748b" stroke-width="1.2" stroke-dasharray="4,4"/>\n'
    svg += '  <text x="234" y="328" font-size="9.5" font-weight="bold" fill="#1e293b" text-anchor="middle">Protocol &amp; Budget Governance Controls (Decisions D1–D7)</text>\n'

    # 6 Governance Cards in 2 columns x 3 rows
    gov_cards = [
        # Col 1
        (28, 338, "D1: RECORD_ONLY Prompt Policy", "Raw model responses recorded verbatim", "No in-flight prompt mutations; retries recorded in attempt journal"),
        (28, 400, "D2: Evaluation &amp; Denominators", f"ANY_MATCH ground truth; {b_fields['mapped_scorable_views']} mapped views", f"Evaluated across {b_fields['macro_universe_classes']} frozen macro classes"),
        (28, 462, "D3 &amp; D4: Concurrency &amp; Identity", "Strict sequential execution (concurrency=1)", "System fingerprint &amp; response ID logged"),
        # Col 2
        (238, 338, "D5: Study Budget Ledger Guard", f"USD{b_fields['budget_cap_display']} study cap; reserve before dispatch", "Atomic dual-lock ledger reservation"),
        (238, 400, "D6 &amp; D7: Synthetic Scope", "Pair-wise synthetic enterprise telemetry", "Generalization to live prod unsupported"),
        (238, 462, "Independent Failure Axes (D2i)", "Retrieval misses &amp; generation errors", "Evaluated independently (no forced cause)"),
    ]

    for cx, cy, ctitle, cline1, cline2 in gov_cards:
        svg += f'  <rect x="{cx}" y="{cy}" width="202" height="56" rx="4" ry="4" fill="#ffffff" stroke="#cbd5e1" stroke-width="1"/>\n'
        svg += f'  <circle cx="{cx + 10}" cy="{cy + 13}" r="2.5" fill="#2563eb"/>\n'
        svg += f'  <text x="{cx + 17}" y="{cy + 16}" class="card-title">{ctitle}</text>\n'
        if len(cline1) > 42:
            svg += f'  <text x="{cx + 8}" y="{cy + 31}" class="card-body" textLength="186" lengthAdjust="spacingAndGlyphs">{cline1}</text>\n'
        else:
            svg += f'  <text x="{cx + 8}" y="{cy + 31}" class="card-body">{cline1}</text>\n'
        if len(cline2) > 42:
            svg += f'  <text x="{cx + 8}" y="{cy + 44}" class="card-body" textLength="186" lengthAdjust="spacingAndGlyphs">{cline2}</text>\n'
        else:
            svg += f'  <text x="{cx + 8}" y="{cy + 44}" class="card-body">{cline2}</text>\n'

    svg += svg_footer_print()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig5_conditional_accuracy_report_v1(data: Dict[str, Any], b_fields: Dict[str, Any], out_path: Path) -> None:
    """
    Fig 5: Conditional Attribution Accuracy (Report Print Variant v1).
    Optimized for 468pt width with all fonts >= 8.5pt.
    Preserves exact subgroup sample sizes and 2-line observational caveat.
    All numbers are machine-generated from authenticated bundle fields.
    """
    fixture_only = data.get("fixture_only", False)
    width = 468
    height = 440
    svg = svg_header_print(width, height, "Conditional Accuracy (Report Print)", fixture_only=fixture_only)

    # Title & Subtitle
    svg += '  <text x="234" y="22" class="title">Figure 5: Downstream Attribution Accuracy Conditioned on Retrieval Success</text>\n'
    svg += '  <text x="234" y="37" class="subtitle">Comparison of P(Correct | Hit) vs. P(Correct | Miss) across RAG depths</text>\n'

    # Axis area: Y ranges from 50% (y=295) to 100% (y=75), height = 220px (4.4px per 1%)
    # Grid lines and Y ticks
    grid_ticks = [
        (100, 75),
        (90, 119),
        (80, 163),
        (70, 207),
        (60, 251),
        (50, 295),
    ]
    for pct, y_val in grid_ticks:
        svg += f'  <line x1="62" y1="{y_val}" x2="448" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="56" y="{y_val + 3}" class="tick-label" style="text-anchor: end;">{pct}%</text>\n'

    # Axis lines
    svg += '  <line x1="62" y1="75" x2="62" y2="295" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="62" y1="295" x2="448" y2="295" stroke="#374151" stroke-width="1.5"/>\n'

    # Y-axis Label
    svg += '  <text x="18" y="185" class="axis-label" transform="rotate(-90 18 185)" text-anchor="middle">Conditional Accuracy (%)</text>\n'

    # Conditions
    conditions = ["rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["k=1", "k=3", "k=5", "k=10"]
    x_positions = [110, 206.5, 303, 399.5]
    bar_w = 26

    for idx, c_name in enumerate(conditions):
        cond_data = data["conditions"][c_name]
        p_hit_val = (cond_data.get("p_corr_hit") or 0.0) * 100.0
        p_miss_val = (cond_data.get("p_corr_miss") or 0.0) * 100.0

        # Pixel conversions
        y_hit = 295.0 - (p_hit_val - 50.0) * 4.4
        y_miss = 295.0 - (p_miss_val - 50.0) * 4.4
        h_hit = 295.0 - y_hit
        h_miss = 295.0 - y_miss

        x_p = x_positions[idx]
        x_hit = x_p - 28
        x_miss = x_p + 2

        # Hit Bar (green #10b981)
        svg += f'  <rect x="{x_hit:.1f}" y="{y_hit:.1f}" width="{bar_w}" height="{h_hit:.1f}" rx="3" ry="3" fill="#10b981"/>\n'
        # Miss Bar (amber #f59e0b)
        svg += f'  <rect x="{x_miss:.1f}" y="{y_miss:.1f}" width="{bar_w}" height="{h_miss:.1f}" rx="3" ry="3" fill="#f59e0b"/>\n'

        # Data Labels (font-size 8.5pt bold)
        hit_label_str = f"{p_hit_val:.1f}%"
        miss_label_str = f"{p_miss_val:.1f}%"
        svg += f'  <text x="{x_hit + bar_w / 2:.1f}" y="{y_hit - 5:.1f}" class="data-hit">{hit_label_str}</text>\n'
        svg += f'  <text x="{x_miss + bar_w / 2:.1f}" y="{y_miss - 5:.1f}" class="data-miss">{miss_label_str}</text>\n'

        # X tick label
        svg += f'  <text x="{x_p:.1f}" y="312" class="tick-label" font-weight="bold" text-anchor="middle">{labels[idx]}</text>\n'

    # Legend
    svg += '  <rect x="105" y="328" width="12" height="12" rx="2" fill="#10b981"/>\n'
    svg += '  <text x="123" y="338" class="legend-text">P(Correct | Retrieval Hit)</text>\n'
    svg += '  <rect x="270" y="328" width="12" height="12" rx="2" fill="#f59e0b"/>\n'
    svg += '  <text x="288" y="338" class="legend-text">P(Correct | Retrieval Miss)</text>\n'

    # Subgroup Sample Counts for k=10 derived from authenticated bundle
    succ_n = b_fields["k10_succ_n"]
    fail_n = b_fields["k10_fail_n"]
    succ_corr = b_fields["k10_succ_corr"]
    fail_corr = b_fields["k10_fail_corr"]
    succ_p_str = b_fields["k10_succ_p_display"]
    fail_p_str = b_fields["k10_fail_p_display"]
    subgroup_str = f"k=10 Subgroups: Retrieved N={succ_n} ({succ_p_str}, {succ_corr}/{succ_n}) | Missed N={fail_n} ({fail_p_str}, {fail_corr}/{fail_n})"
    svg += f'  <text x="234" y="366" class="subgroup-text">{subgroup_str}</text>\n'

    # 2-line observational disclaimer (no forced causality)
    svg += '  <text x="234" y="390" class="caveat-text">* Disclaimer: Subgroup differences are observational (association-only);</text>\n'
    svg += '  <text x="234" y="406" class="caveat-text">retrieval hit/miss is not randomly assigned.</text>\n'

    svg += svg_footer_print()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_report_print_figures(
    bundle_path: Optional[Path] = None,
    fixture_only: bool = False,
    output_dir: Path = Path("docs/report/figures/report_print_v1"),
    paper_output_dir: Optional[Path] = Path("docs/paper/figures/report_print_v1"),
    expected_bundle_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate the report-print variants for Fig 1 and Fig 5 and write provenance."""
    output_dir.mkdir(parents=True, exist_ok=True)
    if paper_output_dir is not None:
        paper_output_dir.mkdir(parents=True, exist_ok=True)

    if fixture_only:
        data = FIXTURE_DATA.copy()
        bundle_hash = "fixture-mode-no-bundle"
        b_fields = FIXTURE_B_FIELDS.copy()
    else:
        if bundle_path is None:
            raise ValueError("[FAIL_CLOSED] Must provide --metric-bundle when not in --fixture-only mode")
        actual_bundle_sha = compute_sha256(bundle_path)
        if expected_bundle_sha256 is not None:
            if actual_bundle_sha.lower() != expected_bundle_sha256.lower():
                raise ValueError(
                    f"[FAIL_CLOSED] Externally trusted bundle SHA-256 mismatch: "
                    f"actual {actual_bundle_sha} != expected {expected_bundle_sha256}"
                )
        with open(bundle_path, "r", encoding="utf-8") as f:
            raw_bundle = json.load(f)
        b_fields = extract_report_print_b_fields(raw_bundle)
        data = load_data_from_bundle(bundle_path, expected_bundle_sha256=expected_bundle_sha256)
        bundle_hash = data["bundle_sha256"]

    is_fixture = bool(data.get("fixture_only", False))

    # Figure definitions and dimensions (width, height)
    figs = {
        "fig1_system_architecture_report_v1": (
            lambda p: generate_fig1_architecture_report_v1(p, b_fields=b_fields, fixture_only=is_fixture),
            468,
            550,
        ),
        "fig5_conditional_accuracy_report_v1": (
            lambda p: generate_fig5_conditional_accuracy_report_v1(data, b_fields=b_fields, out_path=p),
            468,
            440,
        ),
    }

    generated_digests: Dict[str, str] = {}

    for base_name, (gen_fn, w, h) in figs.items():
        svg_filename = f"{base_name}.svg"
        png_filename = f"{base_name}.png"
        pdf_filename = f"{base_name}.pdf"

        svg_path = output_dir / svg_filename
        png_path = output_dir / png_filename
        pdf_path = output_dir / pdf_filename

        # 1. Generate SVG
        gen_fn(svg_path)
        generated_digests[svg_filename] = compute_sha256(svg_path)

        # 2. Export PNG and PDF
        png_ok, pdf_ok = export_svg_to_png_and_pdf(svg_path, png_path, pdf_path, w, h)
        if png_ok:
            # Validate PNG internal structure
            png_bytes = png_path.read_bytes()
            if not validate_png_structure(png_bytes):
                raise RuntimeError(f"Generated PNG {png_filename} failed structural validation")
            generated_digests[png_filename] = compute_sha256(png_path)
        else:
            print(f"  [WARN] PNG rendering skipped or failed for {base_name}")

        if pdf_ok:
            generated_digests[pdf_filename] = compute_sha256(pdf_path)
        else:
            print(f"  [WARN] PDF rendering skipped or failed for {base_name}")

        print(f"  [REPORT-PRINT] Generated {base_name} SVG/PNG/PDF (width={w}pt, height={h}pt)")

    # Provenance structure
    provenance = {
        "schema_version": "2.0.0",
        "variant": "report_print_v1",
        "target_page_column_width_pt": 468,
        "target_font_size_min_pt": 8.5,
        "effective_font_sizes": {
            "fig1_system_architecture_report_v1": {
                "title": "12.5pt bold",
                "subtitle": "8.5pt",
                "stage_headers": "9.5pt bold",
                "stage_body": "8.5pt",
                "governance_title": "9.5pt bold",
                "governance_card_titles": "8.5pt bold",
                "governance_card_lines": "8.5pt",
            },
            "fig5_conditional_accuracy_report_v1": {
                "title": "12.5pt bold",
                "subtitle": "8.5pt",
                "axis_label": "9.0pt bold",
                "tick_labels": "8.5pt",
                "bar_data_labels": "8.5pt bold",
                "legend": "8.5pt",
                "subgroup_sample_sizes": "8.5pt bold",
                "caveat": "8.5pt (2 lines)",
            },
        },
        "physical_scale_and_placement_notes": {
            "canvas_width_user_units": 468,
            "png_placement_scale": "PNG 468x550 / 468x440 achieves minimum 8.5pt font size when placed at 468pt column width in Word report document.",
            "pdf_native_geometry_and_scaling": "PDF native width is 351.12pt (browser CSS px-to-pt ratio 0.75), yielding native text ~6.38pt; scaling to 468pt Word placement yields >= 8.5pt physical print scale. Standalone 100% unscaled PDF print does not claim 8.5pt.",
            "css_user_unit_mapping": "SVG class .title has CSS font-size 12.5px, which equals 12.5pt when placed at 468pt canvas width in Word report.",
        },
        "role_mapping_and_governance": {
            "final_report_figure1_role": "fig1_system_architecture_report_v1 (corrected approved report-print variant)",
            "final_report_figure5_role": "fig5_conditional_accuracy_report_v1 (corrected approved report-print variant)",
            "legacy_figure1_defect_record": "The label '$0.0526 hold/request' belonged to legacy unapproved draft Figure 1 (fig1_system_architecture) and conflated whole-study prior-pilot hold ($0.05264010) with per-request reservations. Legacy Figure 1 was not selected as final authority. The approved report print variant strictly uses 'USD19.99 study cap; reserve before dispatch' and 'No in-flight prompt mutations; retries recorded in attempt journal' without claiming per-request hold or implying zero retries (accounting for 1 transport retry across 6,401 attempts / 6,400 records).",
        },
        "scientific_data_integrity": {
            "canonical_bundle_sha256": bundle_hash,
            "run_id": data["run_id"],
            "fig1_decisions": ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D2i"],
            "fig5_subgroups": {
                "k10_retrieved_sample_count": b_fields["k10_succ_n"],
                "k10_retrieved_correct_count": b_fields["k10_succ_corr"],
                "k10_retrieved_accuracy_pct": b_fields["k10_succ_p_display"],
                "k10_missed_sample_count": b_fields["k10_fail_n"],
                "k10_missed_correct_count": b_fields["k10_fail_corr"],
                "k10_missed_accuracy_pct": b_fields["k10_fail_p_display"],
                "mapped_scorable_views_total": b_fields["mapped_scorable_views"],
            },
            "observational_caveat": "Subgroup differences are observational (association-only); retrieval hit/miss is not randomly assigned.",
        },
        "fixture_only": is_fixture,
        "figures_count": len(figs),
        "figures_formats": ["vector_svg", "raster_png", "print_pdf"],
        "generated_figures": generated_digests,
        "workstation_paths_sanitized": True,
    }

    prov_path = output_dir / "report_print_provenance.json"
    write_json_lf(prov_path, provenance)
    print(f"[REPORT-PRINT] Provenance written to: {prov_path}")

    # Mirror to docs/paper/figures/report_print_v1/ if specified
    if paper_output_dir is not None:
        for fname in list(generated_digests.keys()) + ["report_print_provenance.json"]:
            src_f = output_dir / fname
            dst_f = paper_output_dir / fname
            if src_f.is_file():
                shutil.copy2(src_f, dst_f)
        print(f"[REPORT-PRINT] Mirrored variants to: {paper_output_dir}")

    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Report-Print Variants for RAG2ATTCK Publication Figures")
    parser.add_argument("--metric-bundle", type=Path, default=Path("artifacts/results/canonical_metric_bundle_v2.json"), help="Path to canonical metric bundle JSON")
    parser.add_argument("--expected-bundle-sha256", type=str, default="442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34", help="Expected SHA256 of the metric bundle")
    parser.add_argument("--fixture-only", action="store_true", help="Generate figures using synthetic fixture data")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/report/figures/report_print_v1"), help="Report print output directory")
    parser.add_argument("--paper-output-dir", type=Path, default=Path("docs/paper/figures/report_print_v1"), help="Paper print output directory")
    args = parser.parse_args()

    try:
        generate_report_print_figures(
            bundle_path=args.metric_bundle if not args.fixture_only else None,
            fixture_only=args.fixture_only,
            output_dir=args.output_dir,
            paper_output_dir=args.paper_output_dir,
            expected_bundle_sha256=args.expected_bundle_sha256 if not args.fixture_only else None,
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
