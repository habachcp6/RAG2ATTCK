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
        "acc_num": 0.7799,
        "f1": "0.0126",
        "ci": "[74.64%, 80.88%]",
    },
    "rag_k1": {
        "label": "RAG (k=1)",
        "acc": "77.02%",
        "acc_num": 0.7702,
        "f1": "0.0127",
        "ci": "[73.80%, 80.12%]",
    },
    "rag_k3": {
        "label": "RAG (k=3)",
        "acc": "78.55%",
        "acc_num": 0.7855,
        "f1": "0.0136",
        "ci": "[75.32%, 81.65%]",
    },
    "rag_k5": {
        "label": "RAG (k=5)",
        "acc": "78.83%",
        "acc_num": 0.7883,
        "f1": "0.0139",
        "ci": "[75.61%, 81.93%]",
    },
    "rag_k10": {
        "label": "RAG (k=10)",
        "acc": "79.53%",
        "acc_num": 0.7953,
        "f1": "0.0140",
        "ci": "[76.35%, 82.59%]",
        "p_val": "0.422",
    },
}

CANONICAL_SETTLED_COST = "$6.57575890"
CANONICAL_MAPPED_COHORT = 718


@dataclass(frozen=True)
class MetricBinding:
    """Represents a bound metric field mapping."""
    metric_id: str
    bundle_pointer: str
    canonical_value: Any
    formatted_string: str
    locator: str


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def is_svg_element_visible(elem: ET.Element) -> bool:
    """Returns False if SVG element has explicit hidden style or attribute."""
    style = elem.attrib.get("style", "").lower().replace(" ", "")
    if "display:none" in style or "visibility:hidden" in style or "opacity:0" in style:
        return False
    if elem.attrib.get("display") == "none":
        return False
    if elem.attrib.get("visibility") == "hidden":
        return False
    if elem.attrib.get("opacity") in ["0", "0.0"]:
        return False
    return True


def extract_visible_svg_texts(tree: ET.Element) -> List[str]:
    """Extract visible text content ignoring comments and hidden elements."""
    visible = []
    for elem in tree.iter():
        if elem.tag.endswith("text") and elem.text:
            if is_svg_element_visible(elem):
                visible.append(elem.text.strip())
    return visible


def validate_narrative_metric_bindings(text: str, context_label: str) -> List[str]:
    """
    Validate narrative metrics across Markdown, DOCX, PPTX using structured binding rules.
    Detects unauthorized accuracy and p-value mutations without requiring a specific denylist.
    """
    errors = []

    # 1. Accuracy bindings: match any pattern indicating technique attribution accuracy
    acc_patterns = [
        re.compile(r"(?:accuracy|acc)[^\d%]{0,25}(\d+\.\d+)%", re.I),
        re.compile(r"(\d+\.\d+)%[^\d%]{0,25}(?:accuracy|acc)", re.I),
    ]
    valid_acc_values = {"77.99", "77.02", "78.55", "78.83", "79.53", "91.28", "70.03", "91.3", "70.0"}
    for pat in acc_patterns:
        for m in pat.finditer(text):
            val_str = m.group(1)
            # If value looks like an attribution accuracy (70% - 99%)
            val_f = float(val_str)
            if 70.0 <= val_f <= 99.0 and val_str not in valid_acc_values:
                # Check if it's bootstrap CI bounds
                if val_str not in ["74.64", "80.88", "73.80", "80.12", "75.32", "81.65", "75.61", "81.93", "76.35", "82.59"]:
                    errors.append(f"{context_label}: Unauthorized accuracy value '{val_str}%' does not match any canonical bundle condition")

    # 2. McNemar p-value bindings
    p_patterns = [
        re.compile(r"(?:exact\s*p|p[- ]value|mcnemar\s*p|p\s*=|\bp\s*)(\d+\.\d+)", re.I),
    ]
    for pat in p_patterns:
        for m in pat.finditer(text):
            p_str = m.group(1)
            p_f = float(p_str)
            # In this study, the only hypothesis test reported is McNemar p = 0.422 (alpha = 0.05)
            if 0.01 <= p_f <= 0.99 and p_str != "0.422" and p_str != "0.05":
                errors.append(f"{context_label}: Unauthorized p-value '{p_str}' violates canonical McNemar binding (expected 0.422)")

    return errors


def validate_table3_structure_and_bindings(content: str) -> List[str]:
    """Parse Markdown Table 3 and strictly check presence of all conditions and exact cell bindings."""
    errors = []
    lines = content.splitlines()

    found_conditions: Dict[str, Dict[str, str]] = {}
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 6:
                cond_col = parts[1]
                for c_key, c_info in CANONICAL_TABLE3_CONDITIONS.items():
                    if c_info["label"] in cond_col:
                        found_conditions[c_key] = {
                            "acc": parts[2],
                            "f1": parts[3],
                            "ci": parts[4] if len(parts) > 4 else "",
                            "p": parts[6] if len(parts) > 6 else "",
                        }

    # Verify all 5 conditions present (cardinality gate)
    for c_key, c_info in CANONICAL_TABLE3_CONDITIONS.items():
        if c_key not in found_conditions:
            errors.append(f"Table 3 missing required condition row: '{c_info['label']}'")
        else:
            row = found_conditions[c_key]
            if row["acc"] != c_info["acc"]:
                errors.append(f"Table 3 {c_info['label']} accuracy cell mismatch: expected '{c_info['acc']}', got '{row['acc']}'")
            if row["f1"] != c_info["f1"]:
                errors.append(f"Table 3 {c_info['label']} Macro-F1 cell mismatch: expected '{c_info['f1']}', got '{row['f1']}'")
            if c_key == "rag_k10":
                if "p_val" in c_info and row["p"] != c_info["p_val"]:
                    errors.append(f"Table 3 {c_info['label']} p-value cell mismatch: expected '{c_info['p_val']}', got '{row['p']}'")

    return errors


def validate_table5_structure_and_bindings(content: str) -> List[str]:
    """Parse Markdown Table 5 and strictly verify settled cost in its designated row."""
    errors = []
    clean = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)
    m_settled = re.search(r"Cumulative Settled Expenditure[^\d]{1,20}([0-9]+\.[0-9]+)", clean)
    if not m_settled:
        errors.append("Table 5 missing required Cumulative Settled Expenditure reconciliation entry")
    else:
        settled_val = m_settled.group(1)
        if settled_val != "6.57575890":
            errors.append(f"Table 5 Settled Expenditure mismatch: expected '$6.57575890', got '${settled_val}'")

    lines = clean.splitlines()
    first_100_lines = "\n".join(lines[:100])
    if "718" in first_100_lines:
        errors.append("Table 5 incorrectly references mapped cohort 718 (cost measured on total campaign N=1,280)")

    return errors
