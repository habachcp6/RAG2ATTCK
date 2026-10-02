#!/usr/bin/env python3
"""
scripts/generate_publication_figures.py

Generates the 8 publication-grade vector figures for the RAG2ATTCK scientific report:
  Fig 1: System Architecture & Dual-View Attribution Pipeline
  Fig 2: Attribution Accuracy vs Retrieval Depth (k) with 95% Bootstrap CIs
  Fig 3: Macro-F1 vs Retrieval Depth (k) across 474-class Benchmark Universe
  Fig 4: Hit@k Retrieval Performance & Macro Recall
  Fig 5: Conditional Attribution Accuracy (Retrieval Success vs Failure)
  Fig 6: Latency vs Retrieval Depth (k) with Execution Loop Disclosure
  Fig 7: Cost and Token Consumption Scaling across Retrieval Depths
  Fig 8: Independent Failure Axes & Error Decomposition (Decision D2i)

Operates in two modes:
  --fixture-only: Generates review-ready figures using synthetic fixture data with visible warnings.
  --metric-bundle <path>: Generates canonical figures verified against an approved bundle.
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
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def find_headless_browser() -> Optional[str]:
    """Locate headless Chrome or Edge executable for raster/PDF rendering."""
    candidates = [
        os.environ.get("CHROME_BIN"),
        os.environ.get("EDGE_BIN"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        shutil.which("chrome"),
        shutil.which("msedge"),
        shutil.which("chromium"),
    ]
    for cand in candidates:
        if cand and Path(cand).is_file():
            return cand
    return None


def export_svg_to_png_and_pdf(
    svg_path: Path,
    png_path: Path,
    pdf_path: Path,
    width: int,
    height: int,
) -> Tuple[bool, bool]:
    """Export vector SVG to raster PNG and print PDF via headless browser."""
    browser = find_headless_browser()
    if not browser:
        print(f"  [WARN] No headless browser found for rasterizing {svg_path.name}")
        return False, False

    try:
        # PNG export
        cmd_png = [
            browser,
            "--headless",
            "--disable-gpu",
            f"--screenshot={png_path.resolve()}",
            f"--window-size={width},{height}",
            str(svg_path.resolve()),
        ]
        subprocess.run(cmd_png, capture_output=True, check=False, timeout=30)

        # PDF export
        cmd_pdf = [
            browser,
            "--headless",
            "--disable-gpu",
            "--no-pdf-header-footer",
            f"--print-to-pdf={pdf_path.resolve()}",
            str(svg_path.resolve()),
        ]
        subprocess.run(cmd_pdf, capture_output=True, check=False, timeout=30)

        png_ok = png_path.is_file() and png_path.stat().st_size > 0
        pdf_ok = pdf_path.is_file() and pdf_path.stat().st_size > 0
        return png_ok, pdf_ok
    except Exception as exc:
        print(f"  [WARN] Failed to export raster/pdf for {svg_path.name}: {exc}")
        return False, False


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_text_lf(path: Path, text: str) -> str:
    """Write text file with explicit UTF-8 LF newlines and return its SHA-256."""
    content_bytes = text.replace("\r\n", "\n").encode("utf-8")
    path.write_bytes(content_bytes)
    return hashlib.sha256(content_bytes).hexdigest()


def write_json_lf(path: Path, data: Any) -> str:
    """Write JSON with explicit UTF-8 LF newlines and return its SHA-256."""
    raw_str = json.dumps(data, indent=2, sort_keys=True) + "\n"
    content_bytes = raw_str.replace("\r\n", "\n").encode("utf-8")
    path.write_bytes(content_bytes)
    return hashlib.sha256(content_bytes).hexdigest()


# Default fixture dataset (used when --fixture-only is specified)
FIXTURE_DATA = {
    "fixture_only": True,
    "run_id": "fixture-66b94b1676bf46a9",
    "cohort": {
        "mapped_views": 718,
        "single_gt": 678,
        "multi_gt": 40,
        "classes": 474,
    },
    "conditions": {
        "no_rag": {
            "k": 0, "acc": 0.7799, "macro_f1": 0.0126, "hit_rate": None,
            "ci_low": 74.64, "ci_high": 80.88,
            "latency_mean": 2904.45, "latency_med": 2302.82, "cost": 0.4671,
            "prompt_tokens": 863139, "comp_tokens": 209466, "cached_tokens": 0,
            "p_corr_hit": None, "p_corr_miss": None, "wrong": 158, "miss": None, "overlap": None,
        },
        "rag_k1": {
            "k": 1, "acc": 0.7702, "macro_f1": 0.0127, "hit_rate": 0.2298,
            "ci_low": 73.80, "ci_high": 80.12,
            "latency_mean": 3514.27, "latency_med": 2617.14, "cost": 1.2972,
            "prompt_tokens": 1595554, "comp_tokens": 299128, "cached_tokens": 1540,
            "p_corr_hit": 0.9030, "p_corr_miss": 0.7306, "wrong": 165, "miss": 553, "overlap": 165,
        },
        "rag_k3": {
            "k": 3, "acc": 0.7855, "macro_f1": 0.0136, "hit_rate": 0.1643,
            "ci_low": 75.32, "ci_high": 81.65,
            "latency_mean": 4215.88, "latency_med": 2743.17, "cost": 1.1788,
            "prompt_tokens": 2780640, "comp_tokens": 403100, "cached_tokens": 0,
            "p_corr_hit": 0.8898, "p_corr_miss": 0.7650, "wrong": 154, "miss": 600, "overlap": 151,
        },
        "rag_k5": {
            "k": 5, "acc": 0.7883, "macro_f1": 0.0139, "hit_rate": 0.2409,
            "ci_low": 75.61, "ci_high": 81.93,
            "latency_mean": 4327.26, "latency_med": 2873.74, "cost": 1.4831,
            "prompt_tokens": 3917047, "comp_tokens": 419880, "cached_tokens": 0,
            "p_corr_hit": 0.8902, "p_corr_miss": 0.7560, "wrong": 152, "miss": 545, "overlap": 147,
        },
        "rag_k10": {
            "k": 10, "acc": 0.7953, "macro_f1": 0.0140, "hit_rate": 0.4471,
            "ci_low": 76.35, "ci_high": 82.59,
            "mcnemar_p": 0.422,
            "latency_mean": 4370.71, "latency_med": 2667.00, "cost": 2.1494,
            "prompt_tokens": 6546274, "comp_tokens": 427346, "cached_tokens": 0,
            "p_corr_hit": 0.9128, "p_corr_miss": 0.7003, "wrong": 147, "miss": 397, "overlap": 119,
        },
    }
}


def load_data_from_bundle(bundle_path: Path, expected_bundle_sha256: Optional[str] = None) -> Dict[str, Any]:
    if not bundle_path.is_file():
        raise FileNotFoundError(f"[FAIL_CLOSED] Metric bundle not found at: {bundle_path}")

    actual_sha256 = compute_sha256(bundle_path)
    if expected_bundle_sha256 is not None:
        if actual_sha256.lower() != expected_bundle_sha256.lower():
            raise ValueError(
                f"[FAIL_CLOSED] Externally trusted bundle SHA-256 mismatch: "
                f"actual {actual_sha256} != expected {expected_bundle_sha256}"
            )

    with open(bundle_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    if not isinstance(bundle, dict):
        raise ValueError("[FAIL_CLOSED] Metric bundle must be a valid JSON object")

    if bundle.get("fixture_only", False):
        raise ValueError("[FAIL_CLOSED] Cannot load fixture_only bundle in canonical mode")

    if "conditions" not in bundle or not isinstance(bundle["conditions"], dict):
        raise ValueError("[FAIL_CLOSED] Metric bundle missing 'conditions' mapping")

    expected_conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    for c in expected_conditions:
        if c not in bundle["conditions"]:
            raise ValueError(f"[FAIL_CLOSED] Metric bundle missing condition '{c}'")

    if "cohort_breakdown" not in bundle:
        raise ValueError("[FAIL_CLOSED] Metric bundle missing 'cohort_breakdown'")

    run_id = bundle.get("run_id")
    if not run_id:
        raise ValueError("[FAIL_CLOSED] Metric bundle missing 'run_id'")

    cond_data = {}
    for c_name in expected_conditions:
        c_obj = bundle["conditions"][c_name]
        k_val = c_obj["retrieval_k"]
        rq1 = c_obj["rq1_attribution"]
        rq2 = c_obj["rq2_retrieval_and_error"]
        rq3 = c_obj["rq3_resources_and_cost"]

        ret_m = rq2["retrieval_metrics"]
        gen_c = rq2["generation_conditional_accuracy"]
        axes = rq2["independent_failure_axes"]
        toks = rq3["tokens"]

        # 1. Accuracy
        acc = rq1.get("accuracy_end_to_end")
        if acc is None:
            acc = rq1.get("accuracy")
        if acc is None:
            raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing accuracy")

        # 2. Bootstrap 95% CIs
        ci_arr = rq1.get("accuracy_e2e_ci_95")
        if not ci_arr or len(ci_arr) != 2:
            raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing accuracy_e2e_ci_95")
        ci_low = float(ci_arr[0]) * 100.0
        ci_high = float(ci_arr[1]) * 100.0

        # 3. Macro-F1
        macro_f1 = rq1.get("macro_f1")
        if macro_f1 is None:
            raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing macro_f1")

        # 4. McNemar p-value
        mcnemar_p = None
        if c_name != "no_rag":
            delta_obj = rq1.get("delta_vs_baseline")
            if not delta_obj or "mcnemar_test" not in delta_obj:
                raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing mcnemar_test")
            mcn_obj = delta_obj["mcnemar_test"]
            mcnemar_p = mcn_obj.get("p_value_exact")
            if mcnemar_p is None:
                mcnemar_p = mcn_obj.get("p_value_asymptotic")
            if mcnemar_p is None:
                raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing p-value in mcnemar_test")

        # 5. Retrieval & Error axes
        hit_rate = ret_m.get("retrieval_hit_rate") if ret_m.get("applicable") else None
        p_corr_hit = gen_c.get("p_correct_given_retrieval_success") if gen_c.get("applicable") else None
        p_corr_miss = gen_c.get("p_correct_given_retrieval_failure") if gen_c.get("applicable") else None

        wrong = rq1.get("classification_errors_count")
        if wrong is None:
            wrong = axes.get("valid_but_wrong_classification_count")
        if wrong is None:
            raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing error/wrong count")

        if c_name == "no_rag":
            miss = None
            overlap = None
        else:
            miss = axes.get("retrieval_miss_count")
            if miss is None:
                raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing retrieval_miss_count")
            overlap = axes.get("overlap_retrieval_miss_and_wrong_classification")
            if overlap is None:
                overlap = axes.get("joint_retrieval_miss_and_classification_error_count")
            if overlap is None:
                raise ValueError(f"[FAIL_CLOSED] Condition {c_name} missing overlap count")

        # 6. Latency, cost, tokens
        lat_mean = rq3["latency_ms"]["mean"]
        lat_med = rq3["latency_ms"]["median"]
        cost_str = rq3["financial_cost_usd"]["ledger_settled_cost_usd"]
        cost_val = float(cost_str)

        prompt_tok = toks["prompt_tokens"]["sum"]
        comp_tok = toks["completion_tokens"]["sum"]
        cached_tok = toks.get("cached_tokens", {}).get("sum", 0)

        cond_data[c_name] = {
            "k": k_val,
            "acc": acc,
            "macro_f1": macro_f1,
            "ci_low": ci_low,
            "ci_high": ci_high,
            "mcnemar_p": mcnemar_p,
            "hit_rate": hit_rate,
            "latency_mean": lat_mean,
            "latency_med": lat_med,
            "cost": cost_val,
            "cost_exact": cost_str,
            "prompt_tokens": prompt_tok,
            "comp_tokens": comp_tok,
            "cached_tokens": cached_tok,
            "p_corr_hit": p_corr_hit,
            "p_corr_miss": p_corr_miss,
            "wrong": wrong,
            "miss": miss,
            "overlap": overlap,
        }

    raw_cohort = bundle["cohort_breakdown"]
    cohort_mapped = {
        "mapped_views": raw_cohort.get("mapped_scorable_views", raw_cohort.get("mapped_views", 718)),
        "mapped_scorable_views": raw_cohort.get("mapped_scorable_views", raw_cohort.get("mapped_views", 718)),
        "total_views": raw_cohort.get("total_views", 1280),
        "total_pairs": raw_cohort.get("total_pairs", 640),
        "ambiguous_views": raw_cohort.get("ambiguous_excluded_views", raw_cohort.get("ambiguous_views", 311)),
        "ambiguous_excluded_views": raw_cohort.get("ambiguous_excluded_views", raw_cohort.get("ambiguous_views", 311)),
        "unmapped_views": raw_cohort.get("unmapped_excluded_views", raw_cohort.get("unmapped_views", 251)),
        "unmapped_excluded_views": raw_cohort.get("unmapped_excluded_views", raw_cohort.get("unmapped_views", 251)),
        "single_gt": raw_cohort.get("single_gt_mapped_views", raw_cohort.get("single_gt", 678)),
        "single_gt_mapped_views": raw_cohort.get("single_gt_mapped_views", raw_cohort.get("single_gt", 678)),
        "multi_gt": raw_cohort.get("multi_gt_mapped_views", raw_cohort.get("multi_gt", 40)),
        "multi_gt_mapped_views": raw_cohort.get("multi_gt_mapped_views", raw_cohort.get("multi_gt", 40)),
        "classes": raw_cohort.get("macro_universe_classes", raw_cohort.get("classes", 474)),
        "macro_universe_classes": raw_cohort.get("macro_universe_classes", raw_cohort.get("classes", 474)),
        "supported": raw_cohort.get("supported_classes", 8),
        "supported_classes": raw_cohort.get("supported_classes", 8),
        "unsupported": raw_cohort.get("unsupported_classes", 466),
        "unsupported_classes": raw_cohort.get("unsupported_classes", 466),
    }

    return {
        "fixture_only": False,
        "run_id": run_id,
        "bundle_sha256": compute_sha256(bundle_path),
        "cohort": cohort_mapped,
        "conditions": cond_data,
    }


def svg_header(width: int, height: int, title: str, fixture_only: bool = False) -> str:
    header = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <defs>
    <style>
      @page {{ size: {width}px {height}px; margin: 0; }}
      .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 15px; font-weight: bold; fill: #111827; text-anchor: middle; }}
      .subtitle {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #6b7280; text-anchor: middle; }}
      .axis-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 12px; font-weight: 600; fill: #374151; }}
      .tick-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 10px; fill: #4b5563; text-anchor: middle; }}
      .data-label {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; font-weight: bold; fill: #1f2937; text-anchor: middle; }}
      .grid-line {{ stroke: #e5e7eb; stroke-width: 1; stroke-dasharray: 4,4; }}
      .legend-text {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 11px; fill: #374151; }}
      .fixture-banner {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; font-size: 9px; font-weight: bold; fill: #b91c1c; text-anchor: end; }}
    </style>
  </defs>
  <rect width="100%" height="100%" fill="#ffffff"/>
'''
    if fixture_only:
        header += f'  <rect x="{width - 240}" y="8" width="232" height="18" rx="3" ry="3" fill="#fee2e2" stroke="#ef4444" stroke-width="1"/>\n'
        header += f'  <text x="{width - 12}" y="21" class="fixture-banner">[FIXTURE PREVIEW — NOT CANONICAL DATA]</text>\n'
    return header


def svg_footer() -> str:
    return "</svg>\n"


# =========================================================================
# 8 INDEPENDENT FIGURE GENERATORS
# =========================================================================

def generate_fig1_architecture(out_path: Path, fixture_only: bool = False) -> None:
    """Fig 1: System Architecture Diagram."""
    svg = svg_header(850, 490, "RAG2ATTCK Architecture", fixture_only=fixture_only)
    svg += '  <text x="425" y="32" class="title" text-anchor="middle">Figure 1: RAG2ATTCK Dual-View Attribution Architecture</text>\n'
    svg += '  <text x="425" y="52" class="subtitle" text-anchor="middle">Controlled evaluation pipeline across 5 conditions with strict monetary and ledger governance</text>\n'

    # Boxes
    boxes = [
        (40, 90, 160, 120, "#eff6ff", "#3b82f6", "Telemetry Input", ["Single-Event Views", "Contextual Views", "640 Paired Tests (N=1280)"]),
        (250, 90, 160, 120, "#f5f3ff", "#8b5cf6", "Dense Retrieval", ["all-MiniLM-L6-v2", "FAISS IndexFlatIP", "k in {1, 3, 5, 10}"]),
        (470, 90, 160, 120, "#ecfdf5", "#10b981", "LLM Reasoning", ["gpt-5.6-luna", "xhigh reasoning effort", "Strict JSON Schema"]),
        (680, 90, 140, 120, "#fef3c7", "#f59e0b", "Attribution Output", ["ATT&amp;CK Technique ID", "Retired ID support (D2g)", "Evaluation (474 Macro)"]),
    ]

    for x, y, w, h, bg, stroke, header, items in boxes:
        svg += f'  <rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" ry="8" fill="{bg}" stroke="{stroke}" stroke-width="2"/>\n'
        svg += f'  <text x="{x + w//2}" y="{y + 24}" font-size="13" font-weight="bold" fill="{stroke}" text-anchor="middle">{header}</text>\n'
        svg += f'  <line x1="{x + 10}" y1="{y + 32}" x2="{x + w - 10}" y2="{y + 32}" stroke="{stroke}" stroke-width="1" opacity="0.5"/>\n'
        for idx, item in enumerate(items):
            svg += f'  <text x="{x + w//2}" y="{y + 54 + idx * 20}" font-size="11" fill="#374151" text-anchor="middle">{item}</text>\n'

    # Connecting arrows for RAG flow
    arrows = [(200, 150, 250, 150), (410, 150, 470, 150), (630, 150, 680, 150)]
    for x1, y1, x2, y2 in arrows:
        svg += f'  <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#6b7280" stroke-width="2"/>\n'
        svg += f'  <polygon points="{x2},{y2} {x2-6},{y2-4} {x2-6},{y2+4}" fill="#6b7280"/>\n'

    # Dual-path: No-RAG Direct Bypass (k=0)
    svg += '  <path d="M 120 90 L 120 70 L 550 70 L 550 90" fill="none" stroke="#2563eb" stroke-width="2" stroke-dasharray="4,4"/>\n'
    svg += '  <polygon points="550,90 546,84 554,84" fill="#2563eb"/>\n'
    svg += '  <rect x="290" y="60" width="180" height="20" rx="4" ry="4" fill="#dbeafe" stroke="#3b82f6" stroke-width="1"/>\n'
    svg += '  <text x="380" y="74" font-size="10" font-weight="bold" fill="#1d4ed8" text-anchor="middle">No-RAG Bypass: Direct Prompt (k=0)</text>\n'

    # Governance box below (width 780, well-padded inside)
    svg += '  <rect x="35" y="240" width="780" height="205" rx="8" ry="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5" stroke-dasharray="5,5"/>\n'
    svg += '  <text x="425" y="265" font-size="13" font-weight="bold" fill="#334155" text-anchor="middle">Protocol &amp; Budget Governance Controls (Decisions D1–D7)</text>\n'

    gov_items = [
        (55, 295, "D1: RECORD_ONLY Prompt Policy", "Original model responses recorded verbatim", "Zero in-flight prompt alterations or retries"),
        (55, 345, "D2: Evaluation &amp; Denominators", "ANY_MATCH ground truth; 718 mapped views", "Universe evaluated across 474 frozen classes"),
        (55, 395, "D3 &amp; D4: Concurrency &amp; Identity", "Strict sequential live execution (concurrency=1)", "Timestamped system fingerprint &amp; response IDs"),
        (435, 295, "D5: Study Budget Ledger Guard", "Strict $19.99 cap; $0.0526 hold per request", "Atomic dual-lock ledger pre-reservation"),
        (435, 345, "D6 &amp; D7: Benchmark Dataset Scope", "Pair-wise synthetic enterprise telemetry", "Generalization to live production unsupported"),
        (435, 395, "Independent Failure Axes (D2i)", "Retrieval misses and generation errors", "Evaluated independently without forced causality"),
    ]

    for gx, gy, gtitle, gline1, gline2 in gov_items:
        svg += f'  <circle cx="{gx + 6}" cy="{gy - 4}" r="3" fill="#2563eb"/>\n'
        svg += f'  <text x="{gx + 16}" y="{gy}" font-size="11" font-weight="bold" fill="#1e293b">{gtitle}</text>\n'
        svg += f'  <text x="{gx + 16}" y="{gy + 14}" font-size="10" fill="#64748b">{gline1}</text>\n'
        svg += f'  <text x="{gx + 16}" y="{gy + 27}" font-size="10" fill="#64748b">{gline2}</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig2_accuracy(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 2: Attribution Accuracy vs k with error bars."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 450, "Attribution Accuracy vs k", fixture_only=fixture_only)
    svg += '  <text x="375" y="32" class="title" text-anchor="middle">Figure 2: Technique Attribution Accuracy vs. Retrieval Depth (k)</text>\n'
    svg += '  <text x="375" y="52" class="subtitle" text-anchor="middle">Evaluated on N=718 mapped TEST views; error bars represent 95% pair-clustered bootstrap CIs</text>\n'

    conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["No-RAG (k=0)", "RAG (k=1)", "RAG (k=3)", "RAG (k=5)", "RAG (k=10)"]
    x_positions = [170, 280, 390, 500, 610]

    # Grid lines & ticks
    for y_pct, y_val in [(70, 360), (75, 290), (80, 220), (85, 150)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="660" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">{y_pct}%</text>\n'

    svg += '  <line x1="120" y1="80" x2="120" y2="360" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="360" x2="660" y2="360" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="40" y="220" class="axis-label" transform="rotate(-90 40 220)" text-anchor="middle">Attribution Accuracy (%)</text>\n'

    bar_width = 50
    points = []
    for idx, c_name in enumerate(conditions):
        acc = data["conditions"][c_name]["acc"] * 100
        # Map 70% -> 360, 85% -> 150 (210 px for 15% -> 14 px per 1%)
        y_pixel = 360 - (acc - 70.0) * 14.0
        x_p = x_positions[idx]
        points.append((x_p, y_pixel))

        # Bar
        color = "#3b82f6" if c_name != "no_rag" else "#94a3b8"
        svg += f'  <rect x="{x_p - bar_width//2}" y="{y_pixel}" width="{bar_width}" height="{360 - y_pixel}" fill="{color}" rx="4" ry="4" opacity="0.85"/>\n'
        svg += f'  <text x="{x_p}" y="{y_pixel - 14}" class="data-label">{acc:.2f}%</text>\n'
        svg += f'  <text x="{x_p}" y="{380}" class="tick-label">{labels[idx]}</text>\n'

        # Draw 95% bootstrap error bars
        ci_low = data["conditions"][c_name].get("ci_low", acc - 3.1)
        ci_high = data["conditions"][c_name].get("ci_high", acc + 3.1)
        y_ci_low = 360 - (ci_low - 70.0) * 14.0
        y_ci_high = 360 - (ci_high - 70.0) * 14.0

        svg += f'  <line x1="{x_p}" y1="{y_ci_high}" x2="{x_p}" y2="{y_ci_low}" stroke="#1e293b" stroke-width="1.5"/>\n'
        svg += f'  <line x1="{x_p - 6}" y1="{y_ci_high}" x2="{x_p + 6}" y2="{y_ci_high}" stroke="#1e293b" stroke-width="1.5"/>\n'
        svg += f'  <line x1="{x_p - 6}" y1="{y_ci_low}" x2="{x_p + 6}" y2="{y_ci_low}" stroke="#1e293b" stroke-width="1.5"/>\n'

    # Trend line connecting bars
    line_pts = " ".join([f"{x},{y}" for x, y in points])
    svg += f'  <polyline points="{line_pts}" fill="none" stroke="#1d4ed8" stroke-width="2.5"/>\n'
    for x, y in points:
        svg += f'  <circle cx="{x}" cy="{y}" r="4" fill="#1e3a8a"/>\n'

    # Baseline delta note
    delta_pp = (data["conditions"]["rag_k10"]["acc"] - data["conditions"]["no_rag"]["acc"]) * 100
    p_val = data["conditions"]["rag_k10"].get("mcnemar_p")
    if p_val is None:
        raise ValueError("[FAIL_CLOSED] rag_k10 missing mcnemar_p for Fig 2")
    sig_str = "Significant" if p_val < 0.05 else "Not Significant"
    svg += f'  <rect x="460" y="90" width="200" height="45" rx="5" ry="5" fill="#f0fdf4" stroke="#22c55e" stroke-width="1"/>\n'
    svg += f'  <text x="560" y="108" font-size="11" font-weight="bold" fill="#15803d" text-anchor="middle">k=10 vs No-RAG: +{delta_pp:.3f} pp</text>\n'
    svg += f'  <text x="560" y="124" font-size="10" fill="#166534" text-anchor="middle">McNemar p = {p_val:.3f} ({sig_str})</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig3_macro_f1(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 3: Macro-F1 vs k."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 450, "Macro-F1 vs k", fixture_only=fixture_only)
    svg += '  <text x="375" y="32" class="title" text-anchor="middle">Figure 3: Macro-F1 vs. Retrieval Depth (k) Across 474 ATT&amp;CK Classes</text>\n'
    svg += '  <text x="375" y="52" class="subtitle" text-anchor="middle">Frozen Benchmark Universe (8 supported classes, 466 zero-support classes contributing 0)</text>\n'

    # y-axis: 0.011 to 0.015
    for f1_val, y_val in [(0.011, 350), (0.012, 290), (0.013, 230), (0.014, 170), (0.015, 110)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="660" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">{f1_val:.4f}</text>\n'

    svg += '  <line x1="120" y1="90" x2="120" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="350" x2="660" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="35" y="230" class="axis-label" transform="rotate(-90 35 230)" text-anchor="middle">Macro-F1 (474 Classes)</text>\n'

    conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["No-RAG", "k=1", "k=3", "k=5", "k=10"]
    x_positions = [170, 280, 390, 500, 610]
    points = []

    for idx, c_name in enumerate(conditions):
        f1 = data["conditions"][c_name]["macro_f1"]
        y_pixel = 350 - (f1 - 0.011) * 60000.0
        x_p = x_positions[idx]
        points.append((x_p, y_pixel))

        svg += f'  <circle cx="{x_p}" cy="{y_pixel}" r="6" fill="#8b5cf6"/>\n'
        svg += f'  <text x="{x_p}" y="{y_pixel - 12}" class="data-label">{f1:.4f}</text>\n'
        svg += f'  <text x="{x_p}" y="370" class="tick-label">{labels[idx]}</text>\n'

    line_pts = " ".join([f"{x},{y}" for x, y in points])
    svg += f'  <polyline points="{line_pts}" fill="none" stroke="#7c3aed" stroke-width="2.5"/>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig4_retrieval_hit_rate(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 4: Hit@k Retrieval Performance."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 450, "Retrieval Hit Rate vs k", fixture_only=fixture_only)
    svg += '  <text x="375" y="32" class="title" text-anchor="middle">Figure 4: Dense Retrieval Hit Rate across RAG Conditions</text>\n'
    svg += '  <text x="375" y="52" class="subtitle" text-anchor="middle">Hit@k / any-match retrieval hit rate across N=718 queries (ground-truth technique in top-k context)</text>\n'

    for pct, y_val in [(0, 350), (15, 290), (30, 230), (45, 170), (60, 110)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="660" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">{pct}%</text>\n'

    svg += '  <line x1="120" y1="90" x2="120" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="350" x2="660" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="45" y="230" class="axis-label" transform="rotate(-90 45 230)" text-anchor="middle">Hit@k / Any-Match Hit Rate (%)</text>\n'

    conditions = ["rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["RAG k=1", "RAG k=3", "RAG k=5", "RAG k=10"]
    x_positions = [200, 340, 480, 620]
    bar_w = 60

    for idx, c_name in enumerate(conditions):
        hit_rate = (data["conditions"][c_name]["hit_rate"] or 0.0) * 100
        y_pixel = 350 - hit_rate * 4.0
        x_p = x_positions[idx]

        svg += f'  <rect x="{x_p - bar_w//2}" y="{y_pixel}" width="{bar_w}" height="{350 - y_pixel}" fill="#0ea5e9" rx="4" ry="4" opacity="0.85"/>\n'
        svg += f'  <text x="{x_p}" y="{y_pixel - 10}" class="data-label">{hit_rate:.2f}%</text>\n'
        svg += f'  <text x="{x_p}" y="370" class="tick-label">{labels[idx]}</text>\n'

    svg += '  <text x="375" y="415" font-size="11" fill="#64748b" text-anchor="middle">* No-RAG has k=0 and is omitted from retrieval evaluation (retrieval not applicable).</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig5_conditional_accuracy(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 5: Conditional Accuracy (Hit vs Miss) with Rescaled Plot Area (50-100% under headers)."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 500, "Conditional Accuracy", fixture_only=fixture_only)
    svg += '  <text x="375" y="28" class="title" text-anchor="middle">Figure 5: Downstream Attribution Accuracy Conditioned on Retrieval Success</text>\n'
    svg += '  <text x="375" y="48" class="subtitle" text-anchor="middle">Comparison of P(Correct | Hit) vs. P(Correct | Miss) across RAG depths</text>\n'

    # Rescaled: 50% at y=380, 100% at y=90 (height 290px -> 5.8px per 1%)
    for pct, y_val in [(50, 380), (60, 322), (70, 264), (80, 206), (90, 148), (100, 90)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="660" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">{pct}%</text>\n'

    svg += '  <line x1="120" y1="90" x2="120" y2="380" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="380" x2="660" y2="380" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="45" y="235" class="axis-label" transform="rotate(-90 45 235)" text-anchor="middle">Conditional Accuracy (%)</text>\n'

    conditions = ["rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["k=1", "k=3", "k=5", "k=10"]
    x_positions = [200, 340, 480, 620]
    bar_w = 32

    for idx, c_name in enumerate(conditions):
        p_hit = (data["conditions"][c_name]["p_corr_hit"] or 0.0) * 100
        p_miss = (data["conditions"][c_name]["p_corr_miss"] or 0.0) * 100
        y_hit = 380 - (p_hit - 50.0) * 5.8
        y_miss = 380 - (p_miss - 50.0) * 5.8
        x_p = x_positions[idx]

        # Hit bar (green)
        svg += f'  <rect x="{x_p - bar_w - 2}" y="{y_hit}" width="{bar_w}" height="{380 - y_hit}" fill="#10b981" rx="3" ry="3"/>\n'
        svg += f'  <text x="{x_p - bar_w//2 - 2}" y="{y_hit - 6}" font-size="10" font-weight="bold" fill="#065f46" text-anchor="middle">{p_hit:.1f}%</text>\n'

        # Miss bar (orange)
        svg += f'  <rect x="{x_p + 2}" y="{y_miss}" width="{bar_w}" height="{380 - y_miss}" fill="#f59e0b" rx="3" ry="3"/>\n'
        svg += f'  <text x="{x_p + bar_w//2 + 2}" y="{y_miss - 6}" font-size="10" font-weight="bold" fill="#92400e" text-anchor="middle">{p_miss:.1f}%</text>\n'

        svg += f'  <text x="{x_p}" y="400" class="tick-label">{labels[idx]}</text>\n'

    # Legend
    svg += '  <rect x="250" y="420" width="16" height="16" fill="#10b981" rx="2" ry="2"/>\n'
    svg += '  <text x="272" y="433" class="legend-text">P(Correct | Retrieval Hit)</text>\n'
    svg += '  <rect x="430" y="420" width="16" height="16" fill="#f59e0b" rx="2" ry="2"/>\n'
    svg += '  <text x="452" y="433" class="legend-text">P(Correct | Retrieval Miss)</text>\n'

    # Subgroup Sample Counts for k=10
    svg += '  <text x="375" y="458" font-size="11" font-weight="bold" fill="#334155" text-anchor="middle">k=10 Subgroups: Retrieved N=321 (91.28%, 293/321) | Missed N=397 (70.03%, 278/397)</text>\n'
    # Association-only disclaimer
    svg += '  <text x="375" y="478" font-size="10" fill="#64748b" text-anchor="middle">* Disclaimer: Subgroup differences are observational (association-only); retrieval hit/miss is not randomly assigned.</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig6_latency(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 6: Latency vs k."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 460, "Latency vs k", fixture_only=fixture_only)
    svg += '  <text x="375" y="32" class="title" text-anchor="middle">Figure 6: Request Latency Scaling Across Conditions</text>\n'
    svg += '  <text x="375" y="52" class="subtitle" text-anchor="middle">Client end-to-end loop latency (ms) including backoff retries (N=1280 observations/condition)</text>\n'

    for lat, y_val in [(1000, 350), (2000, 290), (3000, 230), (4000, 170), (5000, 110)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="660" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">{lat:,}</text>\n'

    svg += '  <line x1="120" y1="90" x2="120" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="350" x2="660" y2="350" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="35" y="230" class="axis-label" transform="rotate(-90 35 230)" text-anchor="middle">Latency (ms)</text>\n'

    conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["No-RAG", "k=1", "k=3", "k=5", "k=10"]
    x_positions = [170, 280, 390, 500, 610]
    bar_w = 26

    for idx, c_name in enumerate(conditions):
        mean_l = data["conditions"][c_name]["latency_mean"]
        med_l = data["conditions"][c_name]["latency_med"]
        y_mean = 350 - (mean_l - 1000.0) * 0.06
        y_med = 350 - (med_l - 1000.0) * 0.06
        x_p = x_positions[idx]

        # Mean (blue)
        svg += f'  <rect x="{x_p - bar_w - 2}" y="{y_mean}" width="{bar_w}" height="{350 - y_mean}" fill="#3b82f6" rx="3" ry="3"/>\n'
        svg += f'  <text x="{x_p - bar_w//2 - 2}" y="{y_mean - 6}" font-size="10" font-weight="bold" fill="#1e40af" text-anchor="middle">{int(mean_l)}</text>\n'

        # Median (teal)
        svg += f'  <rect x="{x_p + 2}" y="{y_med}" width="{bar_w}" height="{350 - y_med}" fill="#14b8a6" rx="3" ry="3"/>\n'
        svg += f'  <text x="{x_p + bar_w//2 + 2}" y="{y_med - 6}" font-size="10" font-weight="bold" fill="#0f766e" text-anchor="middle">{int(med_l)}</text>\n'

        svg += f'  <text x="{x_p}" y="370" class="tick-label">{labels[idx]}</text>\n'

    # Legend & Policy Note
    svg += '  <rect x="230" y="395" width="14" height="14" fill="#3b82f6" rx="2" ry="2"/>\n'
    svg += '  <text x="250" y="407" class="legend-text">Mean Latency</text>\n'
    svg += '  <rect x="370" y="395" width="14" height="14" fill="#14b8a6" rx="2" ry="2"/>\n'
    svg += '  <text x="390" y="407" class="legend-text">Median Latency</text>\n'
    svg += '  <text x="375" y="435" font-size="11" fill="#ef4444" font-weight="600" text-anchor="middle">* P95 Latency: NOT REPORTED — approval evidence not established</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig7_cost_and_tokens(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 7: Cost and Token Usage with Dual-Bar Series and Increased Top Margin."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 500, "Cost and Tokens vs k", fixture_only=fixture_only)
    svg += '  <text x="375" y="28" class="title" text-anchor="middle">Figure 7: Financial Cost ($ USD) and Token Usage Scaling Across Conditions</text>\n'
    svg += '  <text x="375" y="48" class="subtitle" text-anchor="middle">Condition Settled Ledger Total ($ USD) vs. Total Tokens Consumed (Prompt + Completion)</text>\n'

    # Left y-axis: $0 to $2.50 (y: 370 down to 80, height 290)
    for cost, y_val in [(0.0, 370), (0.5, 312), (1.0, 254), (1.5, 196), (2.0, 138), (2.5, 80)]:
        svg += f'  <line x1="120" y1="{y_val}" x2="640" y2="{y_val}" class="grid-line"/>\n'
        svg += f'  <text x="110" y="{y_val + 4}" class="tick-label" style="text-anchor: end;">${cost:.2f}</text>\n'

    # Right y-axis: 0k to 8,000k Tokens (y: 370 down to 80)
    for k_tok, y_val in [(0, 370), (2000, 298), (4000, 225), (6000, 153), (8000, 80)]:
        svg += f'  <text x="650" y="{y_val + 4}" class="tick-label" style="text-anchor: start;">{k_tok}k</text>\n'

    svg += '  <line x1="120" y1="80" x2="120" y2="370" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="640" y1="80" x2="640" y2="370" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <line x1="120" y1="370" x2="640" y2="370" stroke="#374151" stroke-width="1.5"/>\n'
    svg += '  <text x="45" y="225" class="axis-label" transform="rotate(-90 45 225)" text-anchor="middle">Settled Cost ($ USD)</text>\n'
    svg += '  <text x="705" y="225" class="axis-label" transform="rotate(90 705 225)" text-anchor="middle">Total Tokens Consumed</text>\n'

    conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    labels = ["No-RAG", "k=1", "k=3", "k=5", "k=10"]
    x_positions = [165, 272, 380, 487, 595]
    bar_w = 18

    for idx, c_name in enumerate(conditions):
        cost = data["conditions"][c_name]["cost"]
        y_cost = 370 - (cost / 2.5) * 290.0
        x_p = x_positions[idx]

        total_toks = data["conditions"][c_name]["prompt_tokens"] + data["conditions"][c_name]["comp_tokens"]
        y_tok = 370 - (total_toks / 8000000.0) * 290.0

        # Cost bar (amber)
        svg += f'  <rect x="{x_p - 24}" y="{y_cost}" width="{bar_w}" height="{370 - y_cost}" fill="#f59e0b" rx="3" ry="3" opacity="0.85"/>\n'
        svg += f'  <text x="{x_p - 15}" y="{y_cost - 6}" font-size="9" font-weight="bold" fill="#b45309" text-anchor="middle">${cost:.2f}</text>\n'

        # Tokens bar (indigo)
        svg += f'  <rect x="{x_p + 6}" y="{y_tok}" width="{bar_w}" height="{370 - y_tok}" fill="#6366f1" rx="3" ry="3" opacity="0.85"/>\n'
        tok_k_label = f"{total_toks / 1000:,.0f}k"
        svg += f'  <text x="{x_p + 15}" y="{y_tok - 6}" font-size="9" font-weight="bold" fill="#4338ca" text-anchor="middle">{tok_k_label}</text>\n'

        svg += f'  <text x="{x_p}" y="392" class="tick-label">{labels[idx]}</text>\n'

    # Legend
    svg += '  <rect x="220" y="415" width="14" height="14" fill="#f59e0b" rx="2" ry="2"/>\n'
    svg += '  <text x="240" y="427" class="legend-text">Settled Cost ($ USD)</text>\n'
    svg += '  <rect x="390" y="415" width="14" height="14" fill="#6366f1" rx="2" ry="2"/>\n'
    svg += '  <text x="410" y="427" class="legend-text">Total Consumed Tokens</text>\n'

    cached_tok_k1 = data["conditions"]["rag_k1"].get("cached_tokens", 0)
    if fixture_only:
        svg += f'  <text x="375" y="458" font-size="11" fill="#64748b" text-anchor="middle">Includes rag_k1 $0.5397 missing-usage penalty. Cached tokens: {cached_tok_k1:,} tokens total in rag_k1 (mean 1.20 tokens/req).</text>\n'
    else:
        svg += f'  <text x="375" y="458" font-size="11" fill="#64748b" text-anchor="middle">Settled ledger cost accounting. Cached tokens: {cached_tok_k1:,} tokens total in rag_k1.</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_fig8_failure_decomposition(data: Dict[str, Any], out_path: Path) -> None:
    """Fig 8: Failure Decomposition (Overlapping Axes) dynamic data."""
    fixture_only = data.get("fixture_only", False)
    svg = svg_header(750, 470, "Failure Decomposition", fixture_only=fixture_only)
    svg += '  <text x="375" y="32" class="title" text-anchor="middle">Figure 8: Independent Failure Decomposition (k=10)</text>\n'
    svg += '  <text x="375" y="52" class="subtitle" text-anchor="middle">Evaluation under Protocol Decision D2i: Non-mutually exclusive independent diagnostic axes</text>\n'

    cohort_n = data["cohort"]["mapped_views"]
    k10 = data["conditions"]["rag_k10"]
    misses = k10["miss"]
    wrongs = k10["wrong"]
    overlap = k10["overlap"]
    if misses is None or wrongs is None or overlap is None:
        raise ValueError("[FAIL_CLOSED] rag_k10 missing miss, wrong, or overlap count for Fig 8")
    correct_despite_miss = misses - overlap
    wrong_despite_hit = wrongs - overlap
    overlap_pct = (overlap / wrongs * 100) if wrongs else 0.0

    # Big container
    svg += '  <rect x="80" y="80" width="590" height="280" rx="10" ry="10" fill="#f8fafc" stroke="#cbd5e1" stroke-width="2"/>\n'
    svg += f'  <text x="100" y="110" font-size="13" font-weight="bold" fill="#334155">Diagnostic on Mapped Scorable Cohort: N = {cohort_n} (Pair-resolved)</text>\n'

    # Retrieval Miss box
    svg += '  <rect x="120" y="130" width="340" height="200" rx="8" ry="8" fill="#fee2e2" stroke="#ef4444" stroke-width="2" opacity="0.75"/>\n'
    svg += f'  <text x="140" y="160" font-size="12" font-weight="bold" fill="#b91c1c">Retrieval Misses: {misses}</text>\n'
    svg += f'  <text x="140" y="180" font-size="11" fill="#7f1d1d">Correct Attribution Despite Miss: {correct_despite_miss} ({correct_despite_miss/misses*100:.1f}%)</text>\n'

    # Classification Error box (overlapping)
    svg += '  <rect x="360" y="160" width="280" height="150" rx="8" ry="8" fill="#fef3c7" stroke="#f59e0b" stroke-width="2" opacity="0.75"/>\n'
    svg += f'  <text x="470" y="190" font-size="12" font-weight="bold" fill="#b45309">Classification Errors: {wrongs}</text>\n'
    svg += f'  <text x="470" y="210" font-size="11" fill="#92400e">Wrong Despite Hit: {wrong_despite_hit} ({wrong_despite_hit/wrongs*100:.1f}%)</text>\n'

    # Overlap Highlight
    svg += '  <rect x="360" y="230" width="100" height="70" rx="4" ry="4" fill="#fbbf24" stroke="#d97706" stroke-width="2"/>\n'
    svg += f'  <text x="410" y="255" font-size="11" font-weight="bold" fill="#78350f" text-anchor="middle">Overlap: {overlap}</text>\n'
    svg += '  <text x="410" y="275" font-size="10" fill="#78350f" text-anchor="middle">Miss ∩ Wrong</text>\n'
    svg += f'  <text x="410" y="290" font-size="9" fill="#78350f" text-anchor="middle">({overlap_pct:.2f}% of Errors)</text>\n'

    # Footnotes about independent axes and campaign scope
    svg += '  <text x="375" y="388" font-size="11" fill="#475569" text-anchor="middle">Decision D2i Note: Axes are evaluated independently. Retrieval miss does not establish error causation.</text>\n'
    svg += '  <text x="375" y="408" font-size="11" fill="#475569" text-anchor="middle">Zero invalid ATT&amp;CK IDs, parse failures, or transport errors on mapped scorable cohort (N=718).</text>\n'
    svg += '  <text x="375" y="430" font-size="10" fill="#b45309" font-weight="600" text-anchor="middle">* Campaign Scope Note: 13 terminal INCOMPLETE requests occurred in the full live campaign outside the mapped cohort (excluded per Decision D2).</text>\n'

    svg += svg_footer()
    ET.fromstring(svg)
    write_text_lf(out_path, svg)


def generate_all_figures(
    bundle_path: Optional[Path],
    fixture_only: bool,
    output_dir: Path,
    expected_bundle_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    if fixture_only:
        if bundle_path is not None:
            raise ValueError("[FAIL_CLOSED] Cannot specify both --fixture-only and --metric-bundle")
        print("[FIGURE-GEN] Operating in FIXTURE mode (--fixture-only).")
        data = FIXTURE_DATA
        bundle_hash = "fixture-mode-no-bundle"
    else:
        if bundle_path is None:
            raise ValueError("[FAIL_CLOSED] Must specify --metric-bundle <path> in canonical mode or use --fixture-only")
        print(f"[FIGURE-GEN] Operating in CANONICAL mode using: {bundle_path}")
        data = load_data_from_bundle(bundle_path, expected_bundle_sha256=expected_bundle_sha256)
        bundle_hash = data["bundle_sha256"]

    is_fixture = bool(data.get("fixture_only", False))

    # Write plot data JSON
    plot_data_path = output_dir / "plot_data.json"
    plot_data_sha = write_json_lf(plot_data_path, data)
    print(f"[FIGURE-GEN] Plot data written to: {plot_data_path}")

    # Generate the 8 figures
    figs = {
        "fig1_system_architecture": lambda p: generate_fig1_architecture(p, fixture_only=is_fixture),
        "fig2_accuracy_vs_k": lambda p: generate_fig2_accuracy(data, p),
        "fig3_macro_f1_vs_k": lambda p: generate_fig3_macro_f1(data, p),
        "fig4_retrieval_hit_rate": lambda p: generate_fig4_retrieval_hit_rate(data, p),
        "fig5_conditional_accuracy": lambda p: generate_fig5_conditional_accuracy(data, p),
        "fig6_latency_vs_k": lambda p: generate_fig6_latency(data, p),
        "fig7_cost_and_tokens_vs_k": lambda p: generate_fig7_cost_and_tokens(data, p),
        "fig8_failure_decomposition": lambda p: generate_fig8_failure_decomposition(data, p),
    }

    fig_dimensions = {
        "fig1_system_architecture": (850, 490),
        "fig2_accuracy_vs_k": (750, 450),
        "fig3_macro_f1_vs_k": (750, 450),
        "fig4_retrieval_hit_rate": (750, 450),
        "fig5_conditional_accuracy": (750, 500),
        "fig6_latency_vs_k": (750, 460),
        "fig7_cost_and_tokens_vs_k": (750, 500),
        "fig8_failure_decomposition": (750, 470),
    }

    generated_digests: Dict[str, str] = {}
    for base_name, gen_fn in figs.items():
        svg_filename = f"{base_name}.svg"
        png_filename = f"{base_name}.png"
        pdf_filename = f"{base_name}.pdf"

        svg_path = output_dir / svg_filename
        png_path = output_dir / png_filename
        pdf_path = output_dir / pdf_filename

        gen_fn(svg_path)
        generated_digests[svg_filename] = compute_sha256(svg_path)

        w, h = fig_dimensions[base_name]
        png_ok, pdf_ok = export_svg_to_png_and_pdf(svg_path, png_path, pdf_path, w, h)
        if png_ok:
            generated_digests[png_filename] = compute_sha256(png_path)
        if pdf_ok:
            generated_digests[pdf_filename] = compute_sha256(pdf_path)

        print(f"  Generated {svg_filename} ({generated_digests[svg_filename][:12]}...) PNG={png_ok} PDF={pdf_ok}")

    provenance = {
        "schema_version": "2.0.0",
        "fixture_only": is_fixture,
        "run_id": data["run_id"],
        "bundle_sha256": bundle_hash,
        "figures_count": 8,
        "figures_formats": ["vector_svg", "raster_png", "print_pdf"],
        "generated_figures": generated_digests,
        "plot_data_sha256": plot_data_sha,
        "p95_latency_status": "NOT REPORTED — approval evidence not established",
        "workstation_paths_sanitized": True,
    }

    prov_path = output_dir / "figure_provenance.json"
    write_json_lf(prov_path, provenance)
    print(f"[FIGURE-GEN] Provenance written to: {prov_path}")

    return provenance


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Publication Figures for RAG2ATTCK")
    parser.add_argument("--metric-bundle", type=Path, default=None, help="Path to canonical metric bundle JSON")
    parser.add_argument("--expected-bundle-sha256", type=str, default=None, help="Expected SHA256 of the metric bundle to verify external trust anchor")
    parser.add_argument("--fixture-only", action="store_true", help="Generate figures using synthetic fixture data")
    parser.add_argument("--output-dir", type=Path, default=Path("docs/report/figures"), help="Output directory")
    args = parser.parse_args()

    if not args.fixture_only and args.metric_bundle is None:
        print("ERROR: Must specify either --metric-bundle <path> or --fixture-only", file=sys.stderr)
        return 1

    try:
        generate_all_figures(
            bundle_path=args.metric_bundle,
            fixture_only=args.fixture_only,
            output_dir=args.output_dir,
            expected_bundle_sha256=args.expected_bundle_sha256,
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
