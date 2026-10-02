"""
scripts/publication_bindings.py

Defines the common structured MetricBinding contract between the frozen
Canonical Metric Bundle v2 and publication artifacts (Markdown, DOCX, PPTX, SVG/PNG/PDF).
Enforces exact locator parsing and typed value bindings without relying on ad-hoc denylists.
Owned by Track D under scripts/.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

TRUSTED_BUNDLE_SHA256 = "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"

CANONICAL_FIGURE_BASENAMES = {
    "fig1_system_architecture",
    "fig2_accuracy_vs_k",
    "fig3_macro_f1_vs_k",
    "fig4_retrieval_hit_rate",
    "fig5_conditional_accuracy",
    "fig6_latency_vs_k",
    "fig7_cost_and_tokens_vs_k",
    "fig8_failure_decomposition",
}

REQUIRED_FORMATS = {"vector_svg", "raster_png", "print_pdf"}

# Canonical condition values from Frozen Bundle v2
CANONICAL_TABLE3_CONDITIONS = {
    "no_rag": {
        "label": "No-RAG",
        "acc": "77.99%",
        "acc_num": 0.7799442896935933,
        "acc_ci": "[74.64%, 80.88%]",
        "f1": "0.0126",
        "delta": "Baseline",
        "ci": "—",
        "p_val": "—",
    },
    "rag_k1": {
        "label": "RAG (k=1)",
        "acc": "77.02%",
        "acc_num": 0.7701949860724234,
        "acc_ci": "[73.50%, 80.17%]",
        "f1": "0.0127",
        "delta": "-0.975 pp",
        "ci": "[-3.186, +1.124] pp",
        "p_val": "0.435",
    },
    "rag_k3": {
        "label": "RAG (k=3)",
        "acc": "78.55%",
        "acc_num": 0.7855153203342619,
        "acc_ci": "[75.00%, 81.74%]",
        "f1": "0.0136",
        "delta": "+0.557 pp",
        "ci": "[-2.786, +3.934] pp",
        "p_val": "0.777",
    },
    "rag_k5": {
        "label": "RAG (k=5)",
        "acc": "78.83%",
        "acc_num": 0.7883008356545961,
        "acc_ci": "[75.07%, 82.35%]",
        "f1": "0.0139",
        "delta": "+0.836 pp",
        "ci": "[-2.934, +4.603] pp",
        "p_val": "0.677",
    },
    "rag_k10": {
        "label": "RAG (k=10)",
        "acc": "79.53%",
        "acc_num": 0.7952646239554317,
        "acc_ci": "[75.81%, 82.85%]",
        "f1": "0.0140",
        "delta": "+1.532 pp",
        "ci": "[-2.355, +5.300] pp",
        "p_val": "0.422",
    },
}

CANONICAL_TABLE5_FINANCIAL = {
    "settled_cost": "6.57575890",
    "settled_cost_display": "$6.57575890",
    "total_accounted": "6.62839900",
    "total_accounted_display": "$6.62839900",
    "budget_cap": "19.99000000",
    "provisional_hold": "0.05264010",
    "available_balance": "13.36160100",
}

CANONICAL_MAPPED_COHORT = 718


@dataclass(frozen=True)
class MetricBinding:
    """Represents a bound metric field mapping between canonical bundle and publication artifacts."""
    metric_id: str
    bundle_pointer: str
    canonical_value: Any
    formatted_string: str
    locator: str


def build_canonical_bindings_registry(bundle: Optional[Dict[str, Any]] = None) -> List[MetricBinding]:
    """Build the typed canonical metric bindings registry."""
    bindings = [
        MetricBinding(
            metric_id="no_rag_accuracy",
            bundle_pointer="conditions/no_rag/rq1_attribution/accuracy_display",
            canonical_value=0.7799442896935933,
            formatted_string="77.99%",
            locator="outputs/rq_analysis.json#/rq1/by_condition/no_rag",
        ),
        MetricBinding(
            metric_id="rag_k1_accuracy",
            bundle_pointer="conditions/rag_k1/rq1_attribution/accuracy_display",
            canonical_value=0.7701949860724234,
            formatted_string="77.02%",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k1",
        ),
        MetricBinding(
            metric_id="rag_k3_accuracy",
            bundle_pointer="conditions/rag_k3/rq1_attribution/accuracy_display",
            canonical_value=0.7855153203342619,
            formatted_string="78.55%",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k3",
        ),
        MetricBinding(
            metric_id="rag_k5_accuracy",
            bundle_pointer="conditions/rag_k5/rq1_attribution/accuracy_display",
            canonical_value=0.7883008356545961,
            formatted_string="78.83%",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k5",
        ),
        MetricBinding(
            metric_id="rag_k10_accuracy",
            bundle_pointer="conditions/rag_k10/rq1_attribution/accuracy_display",
            canonical_value=0.7952646239554317,
            formatted_string="79.53%",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k10",
        ),
        MetricBinding(
            metric_id="rag_k1_mcnemar_p",
            bundle_pointer="conditions/rag_k1/rq1_attribution/delta_vs_baseline/mcnemar_test/display_p_exact",
            canonical_value=0.4349928051221534,
            formatted_string="0.435",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k1/delta_vs_baseline/mcnemar_test",
        ),
        MetricBinding(
            metric_id="rag_k3_mcnemar_p",
            bundle_pointer="conditions/rag_k3/rq1_attribution/delta_vs_baseline/mcnemar_test/display_p_exact",
            canonical_value=0.776602,
            formatted_string="0.777",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k3/delta_vs_baseline/mcnemar_test",
        ),
        MetricBinding(
            metric_id="rag_k5_mcnemar_p",
            bundle_pointer="conditions/rag_k5/rq1_attribution/delta_vs_baseline/mcnemar_test/display_p_exact",
            canonical_value=0.677063,
            formatted_string="0.677",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k5/delta_vs_baseline/mcnemar_test",
        ),
        MetricBinding(
            metric_id="rag_k10_mcnemar_p",
            bundle_pointer="conditions/rag_k10/rq1_attribution/delta_vs_baseline/mcnemar_test/display_p_exact",
            canonical_value=0.422329,
            formatted_string="0.422",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k10/delta_vs_baseline/mcnemar_test",
        ),
        MetricBinding(
            metric_id="rag_k10_delta_ci",
            bundle_pointer="conditions/rag_k10/rq1_attribution/delta_vs_baseline/delta_accuracy_ci_95_display_pp",
            canonical_value=[-0.023547341489689132, 0.05300045580982214],
            formatted_string="[-2.355, +5.300] pp",
            locator="outputs/rq_analysis.json#/rq1/by_condition/rag_k10/delta_vs_baseline",
        ),
        MetricBinding(
            metric_id="cumulative_settled_expenditure",
            bundle_pointer="whole_study_financial_accounting/cumulative_settled_cost_usd",
            canonical_value=Decimal("6.57575890"),
            formatted_string="$6.57575890",
            locator="outputs/rq_analysis.json#/rq3/whole_study_financial_accounting",
        ),
        MetricBinding(
            metric_id="total_accounted_expenditure",
            bundle_pointer="whole_study_financial_accounting/total_accounted_expenditure_usd",
            canonical_value=Decimal("6.62839900"),
            formatted_string="$6.62839900",
            locator="outputs/rq_analysis.json#/rq3/whole_study_financial_accounting",
        ),
    ]
    return bindings


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def validate_png_structure(data: bytes) -> bool:
    """
    Validate PNG chunk framing:
    - Minimum length >= 33 (8-byte signature + 25-byte minimal chunks)
    - Signature: 89 50 4E 47 0D 0A 1A 0A
    - First chunk must be IHDR (length 13)
    - Must contain IDAT chunk
    - Final chunk must be IEND (length 0)
    - Valid chunk length framing across entire stream
    """
    if len(data) < 33:
        return False
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False
    pos = 8
    seen_ihdr = False
    seen_idat = False
    seen_iend = False

    while pos + 8 <= len(data):
        chunk_len = int.from_bytes(data[pos : pos + 4], "big")
        chunk_type = data[pos + 4 : pos + 8]
        if pos + 12 + chunk_len > len(data):
            return False
        if not seen_ihdr:
            if chunk_type != b"IHDR" or chunk_len != 13:
                return False
            seen_ihdr = True
        if chunk_type == b"IDAT":
            seen_idat = True
        elif chunk_type == b"IEND":
            seen_iend = True
            if pos + 12 + chunk_len != len(data):
                return False
            break
        pos += 12 + chunk_len

    return seen_ihdr and seen_idat and seen_iend


def is_svg_element_visible(elem: ET.Element, parent_map: Optional[Dict[ET.Element, ET.Element]] = None) -> bool:
    """Returns False if SVG element or any ancestor has explicit hidden style or attribute."""
    curr: Optional[ET.Element] = elem
    while curr is not None:
        style = curr.attrib.get("style", "").lower().replace(" ", "")
        if "display:none" in style or "visibility:hidden" in style or "opacity:0" in style:
            return False
        if curr.attrib.get("display") == "none":
            return False
        if curr.attrib.get("visibility") == "hidden":
            return False
        if curr.attrib.get("opacity") in ["0", "0.0"]:
            return False
        if parent_map is not None:
            curr = parent_map.get(curr)
        else:
            break
    return True


def extract_visible_svg_texts(tree: ET.Element) -> List[str]:
    """Extract visible text content ignoring comments and hidden elements/ancestors."""
    parent_map = {c: p for p in tree.iter() for c in p}
    visible = []
    for elem in tree.iter():
        if elem.tag.endswith("text") and elem.text:
            if is_svg_element_visible(elem, parent_map):
                visible.append(elem.text.strip())
    return visible


def validate_narrative_metric_bindings(text: str, context_label: str) -> List[str]:
    """
    Validate narrative metrics across Markdown, DOCX, PPTX using structured binding rules.
    Detects unauthorized accuracy and p-value mutations without relying on ad-hoc denylists.
    """
    errors = []

    # Strip HTML / XML comments if present
    clean_text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # 1. Condition-specific accuracy bindings: detect condition-level swaps
    cond_acc_map = {
        "no_rag": "77.99",
        "rag_k1": "77.02",
        "rag_k3": "78.55",
        "rag_k5": "78.83",
        "rag_k10": "79.53",
    }
    cond_pat = re.compile(
        r"\b(no_rag|rag_k1|rag_k3|rag_k5|rag_k10)\b[^\n\r.;]{0,35}?(?:accuracy|acc)?[^\d%]{0,10}(\d+\.\d+)%",
        re.I,
    )
    for m in cond_pat.finditer(clean_text):
        cond_name = m.group(1).lower()
        val_str = m.group(2)
        expected_acc = cond_acc_map.get(cond_name)
        if expected_acc and val_str != expected_acc:
            errors.append(
                f"{context_label}: Condition '{cond_name}' has mismatched accuracy '{val_str}%' (expected '{expected_acc}%')"
            )

    # 2. General attribution accuracy / proportion percentages in [70.0, 99.0]
    valid_pct_values = {
        # All canonical percentages from bundle v2 in [70.0, 99.0]
        "70.03", "70.0", "70", "73.03", "73.0", "73.50", "74.64", "74.83", "75.00", "75.07",
        "75.66", "75.81", "75.91", "76.12", "76.1", "77.02", "77.29", "77.43", "77.58", "77.99",
        "78.32", "78.55", "78.83", "79.53", "80.17", "80.88", "80.95", "81.74", "82.35", "82.85",
        "83.57", "87.50", "91.28", "91.3", "94.43", "96.24", "96.71", "97.11", "97.46", "98.05", "98.31",
        # Common rounded displays
        "100.00", "100.0", "100", "80", "85", "90", "95", "97.5", "89.0", "90.3",
    }
    pct_pat = re.compile(r"(\d+\.\d+)%")
    for m in pct_pat.finditer(clean_text):
        val_str = m.group(1)
        val_f = float(val_str)
        if 70.0 <= val_f <= 99.0 and val_str not in valid_pct_values:
            errors.append(
                f"{context_label}: Unauthorized accuracy/proportion percentage '{val_str}%' does not match any canonical metric"
            )

    # 3. McNemar p-value bindings: valid set across all conditions and alpha thresholds
    p_pat = re.compile(r"(?:exact\s*p|p[- ]value|mcnemar\s*p|\bp)\s*=\s*(\d+\.\d+)", re.I)
    valid_p_values = {"0.422", "0.435", "0.777", "0.677", "0.05", "0.01"}
    for m in p_pat.finditer(clean_text):
        p_str = m.group(1)
        if p_str not in valid_p_values:
            errors.append(
                f"{context_label}: Unauthorized p-value '{p_str}' violates canonical McNemar bindings"
            )

    # 4. Macro-F1 bindings
    f1_pat = re.compile(r"(?:macro[- ]f1|f1)[^\d]{0,20}(\d+\.\d{4})", re.I)
    allowed_f1 = {"0.0126", "0.0127", "0.0136", "0.0139", "0.0140"}
    for m in f1_pat.finditer(clean_text):
        f1_str = m.group(1)
        if f1_str not in allowed_f1:
            errors.append(
                f"{context_label}: Unauthorized Macro-F1 '{f1_str}' violates canonical bundle binding"
            )

    return errors


def validate_table3_structure_and_bindings(content: str) -> List[str]:
    """Parse Markdown Table 3 and strictly check presence of all conditions and exact cell bindings."""
    errors = []
    lines = content.splitlines()

    found_conditions: Dict[str, Dict[str, str]] = {}
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                cond_col = parts[1]
                for c_key, c_info in CANONICAL_TABLE3_CONDITIONS.items():
                    if c_info["label"] in cond_col:
                        found_conditions[c_key] = {
                            "acc": parts[2],
                            "f1": parts[3],
                            "delta": parts[4],
                            "ci": parts[5],
                            "p": parts[6],
                        }

    # Verify all 5 conditions present (cardinality gate)
    for c_key, c_info in CANONICAL_TABLE3_CONDITIONS.items():
        if c_key not in found_conditions:
            errors.append(f"Table 3 missing required condition row: '{c_info['label']}'")
        else:
            row = found_conditions[c_key]
            if row["acc"] != c_info["acc"]:
                errors.append(
                    f"Table 3 {c_info['label']} accuracy cell mismatch: expected '{c_info['acc']}', got '{row['acc']}'"
                )
            if row["f1"] != c_info["f1"]:
                errors.append(
                    f"Table 3 {c_info['label']} Macro-F1 cell mismatch: expected '{c_info['f1']}', got '{row['f1']}'"
                )
            if row["delta"] != c_info["delta"]:
                errors.append(
                    f"Table 3 {c_info['label']} delta cell mismatch: expected '{c_info['delta']}', got '{row['delta']}'"
                )
            if row["ci"] != c_info["ci"]:
                errors.append(
                    f"Table 3 {c_info['label']} CI cell mismatch: expected '{c_info['ci']}', got '{row['ci']}'"
                )
            if row["p"] != c_info["p_val"]:
                errors.append(
                    f"Table 3 {c_info['label']} p-value cell mismatch: expected '{c_info['p_val']}', got '{row['p']}'"
                )

    return errors


def validate_table5_structure_and_bindings(content: str) -> List[str]:
    """Parse Markdown Table 5 and strictly verify settled cost and total accounted expenditure."""
    errors = []
    clean = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    m_settled = re.search(r"Cumulative Settled Expenditure[^\d]{1,20}([0-9]+\.[0-9]+)", clean)
    if not m_settled:
        errors.append("Table 5 missing required Cumulative Settled Expenditure reconciliation entry")
    else:
        settled_val = m_settled.group(1)
        if settled_val != CANONICAL_TABLE5_FINANCIAL["settled_cost"]:
            errors.append(
                f"Table 5 Settled Expenditure mismatch: expected '${CANONICAL_TABLE5_FINANCIAL['settled_cost']}', got '${settled_val}'"
            )

    m_accounted = re.search(r"Total Accounted Expenditure[^\d]{1,20}([0-9]+\.[0-9]+)", clean)
    if not m_accounted:
        errors.append("Table 5 missing required Total Accounted Expenditure reconciliation entry")
    else:
        accounted_val = m_accounted.group(1)
        if accounted_val != CANONICAL_TABLE5_FINANCIAL["total_accounted"]:
            errors.append(
                f"Table 5 Total Accounted Expenditure mismatch: expected '${CANONICAL_TABLE5_FINANCIAL['total_accounted']}', got '${accounted_val}'"
            )

    lines = clean.splitlines()
    first_100_lines = "\n".join(lines[:100])
    if "718" in first_100_lines:
        errors.append("Table 5 incorrectly references mapped cohort 718 (cost measured on total campaign N=1,280)")

    return errors
