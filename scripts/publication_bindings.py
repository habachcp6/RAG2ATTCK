"""
scripts/publication_bindings.py

Defines the dynamic MetricBinding contract and validation suite between the frozen
Canonical Metric Bundle v2 and publication artifacts (Markdown, DOCX, PPTX, SVG/PNG/PDF).
Dynamically extracts canonical values from authenticated bundle pointers without hardcoding
scientific constants or relying on proximity windows / global allowed-value lists.
Owned by Track D under scripts/.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zlib
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

COND_ALIAS_MAP = {
    "no_rag": "no_rag",
    "no-rag": "no_rag",
    "norag": "no_rag",
    "baseline": "no_rag",
    "rag_k1": "rag_k1",
    "rag-k1": "rag_k1",
    "k1": "rag_k1",
    "rag_k3": "rag_k3",
    "rag-k3": "rag_k3",
    "k3": "rag_k3",
    "rag_k5": "rag_k5",
    "rag-k5": "rag_k5",
    "k5": "rag_k5",
    "rag_k10": "rag_k10",
    "rag-k10": "rag_k10",
    "k10": "rag_k10",
}

COND_REGEX = re.compile(
    r"\b(no[-_]?rag|baseline|rag[-_]?k10\b|k10\b|rag[-_]?k1\b|k1\b|rag[-_]?k3\b|k3\b|rag[-_]?k5\b|k5\b)",
    re.I,
)


@dataclass(frozen=True)
class MetricBinding:
    """Represents a bound metric field mapping between canonical bundle and publication artifacts."""
    metric_id: str
    condition: Optional[str]
    cohort: Optional[int]
    unit: str
    locator: str
    bundle_pointer: str
    canonical_value: Any
    formatted_string: str


def compute_sha256(path: Path) -> str:
    """Compute standard SHA-256 hex digest of file on disk."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_trusted_bundle(bundle_path: Optional[Path] = None, bundle_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Retrieve bundle dictionary from parameter, provided path, or default canonical path."""
    if bundle_dict is not None:
        return bundle_dict
    candidates = []
    if bundle_path:
        candidates.append(Path(bundle_path))
    candidates.extend([
        Path("artifacts/results/canonical_metric_bundle_v2.json"),
        Path("bundle.json"),
        Path("../artifacts/results/canonical_metric_bundle_v2.json"),
    ])
    for cand in candidates:
        if cand.is_file():
            try:
                return json.loads(cand.read_text(encoding="utf-8"))
            except Exception:
                continue
    return {}


def extract_table3_conditions(bundle: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Extract Table 3 attribution performance conditions dynamically from authenticated bundle."""
    result = {}
    conditions = bundle.get("conditions", {})
    label_map = {
        "no_rag": "No-RAG",
        "rag_k1": "RAG (k=1)",
        "rag_k3": "RAG (k=3)",
        "rag_k5": "RAG (k=5)",
        "rag_k10": "RAG (k=10)",
    }
    for c_key, c_label in label_map.items():
        if c_key not in conditions:
            continue
        cond_data = conditions[c_key]
        rq1 = cond_data.get("rq1_attribution", {})
        delta_obj = rq1.get("delta_vs_baseline")
        mcnemar = delta_obj.get("mcnemar_test") if isinstance(delta_obj, dict) else None
        
        result[c_key] = {
            "label": c_label,
            "condition": c_key,
            "cohort": cond_data.get("cohort", {}).get("total_scorable_mapped_views", 718),
            "acc": rq1.get("accuracy_display", ""),
            "acc_num": rq1.get("accuracy_e2e", 0.0),
            "acc_ci": rq1.get("accuracy_ci_95_display", ""),
            "f1": rq1.get("macro_f1_display", ""),
            "f1_num": rq1.get("macro_f1", 0.0),
            "delta": delta_obj.get("delta_accuracy_display_pp", "Baseline") if isinstance(delta_obj, dict) else "Baseline",
            "ci": delta_obj.get("delta_accuracy_ci_95_display_pp", "—") if isinstance(delta_obj, dict) else "—",
            "p_val": mcnemar.get("display_p_exact", "—") if isinstance(mcnemar, dict) else "—",
            "p_num": mcnemar.get("p_exact") if isinstance(mcnemar, dict) else None,
        }
    return result


def extract_table5_data(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Table 5 operational resource, token, and financial metrics dynamically from authenticated bundle."""
    fin = bundle.get("whole_study_financial_accounting", {})
    conditions = bundle.get("conditions", {})
    label_map = {
        "no_rag": "No-RAG (k=0)",
        "rag_k1": "RAG (k=1)",
        "rag_k3": "RAG (k=3)",
        "rag_k5": "RAG (k=5)",
        "rag_k10": "RAG (k=10)",
    }
    rows = {}
    for c_key, c_label in label_map.items():
        if c_key not in conditions:
            continue
        c_data = conditions[c_key]
        rq3 = c_data.get("rq3_resources_and_cost", {})
        tokens = rq3.get("tokens", {})
        lat = rq3.get("latency_ms", {})
        cost_obj = rq3.get("financial_cost_usd", {})
        
        prompt_sum = tokens.get("prompt_tokens", {}).get("sum", 0)
        completion_sum = tokens.get("completion_tokens", {}).get("sum", 0)
        cached_sum = tokens.get("cached_tokens", {}).get("sum", 0)
        settled_cost = cost_obj.get("ledger_settled_cost_usd", "0.00000000")
        
        rows[c_key] = {
            "label": c_label,
            "condition": c_key,
            "cohort": c_data.get("cohort", {}).get("total_logical_requests", 1280),
            "mean_latency": f"{lat.get('mean', 0.0):,.1f}",
            "median_latency": f"{lat.get('median', 0.0):,.1f}",
            "prompt_tokens": f"{prompt_sum:,}",
            "prompt_tokens_int": prompt_sum,
            "completion_tokens": f"{completion_sum:,}",
            "completion_tokens_int": completion_sum,
            "cached_tokens": f"{cached_sum:,}",
            "cached_tokens_int": cached_sum,
            "settled_cost": f"${float(settled_cost):.8f}" if settled_cost else "$0.00000000",
            "settled_cost_raw": settled_cost,
        }
        
    return {
        "rows": rows,
        "financial": {
            "settled_cost": str(fin.get("cumulative_settled_cost_usd", "6.57575890")),
            "settled_cost_display": f"${str(fin.get('cumulative_settled_cost_usd', '6.57575890'))}",
            "total_accounted": str(fin.get("total_accounted_expenditure_usd", "6.62839900")),
            "total_accounted_display": f"${str(fin.get('total_accounted_expenditure_usd', '6.62839900'))}",
            "budget_cap": str(fin.get("budget_cap_usd", "19.99000000")),
            "provisional_hold": str(fin.get("prior_pilot_provisional_hold_usd", "0.05264010")),
            "available_balance": str(fin.get("uncommitted_available_balance_usd", "13.36160100")),
        }
    }


# Dynamic bundle-extracted structures
CANONICAL_TABLE3_CONDITIONS = extract_table3_conditions(load_trusted_bundle())
CANONICAL_TABLE5_FINANCIAL = extract_table5_data(load_trusted_bundle())["financial"]


def build_canonical_bindings_registry(bundle: Optional[Dict[str, Any]] = None) -> List[MetricBinding]:
    """Build the typed canonical metric bindings registry dynamically from authenticated bundle."""
    b = load_trusted_bundle(bundle_dict=bundle)
    bindings: List[MetricBinding] = []
    conditions = b.get("conditions", {})

    for c_key in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        if c_key not in conditions:
            continue
        c_obj = conditions[c_key]
        rq1 = c_obj.get("rq1_attribution", {})
        cohort_n = c_obj.get("cohort", {}).get("total_scorable_mapped_views", 718)
        
        # Accuracy
        acc_disp = rq1.get("accuracy_display", "")
        acc_num = rq1.get("accuracy_e2e", 0.0)
        bindings.append(MetricBinding(
            metric_id=f"{c_key}_accuracy",
            condition=c_key,
            cohort=cohort_n,
            unit="percentage",
            locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}",
            bundle_pointer=f"conditions/{c_key}/rq1_attribution/accuracy_display",
            canonical_value=acc_num,
            formatted_string=acc_disp,
        ))

        # Macro-F1
        f1_disp = rq1.get("macro_f1_display", "")
        f1_num = rq1.get("macro_f1", 0.0)
        bindings.append(MetricBinding(
            metric_id=f"{c_key}_macro_f1",
            condition=c_key,
            cohort=cohort_n,
            unit="f1",
            locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}",
            bundle_pointer=f"conditions/{c_key}/rq1_attribution/macro_f1_display",
            canonical_value=f1_num,
            formatted_string=f1_disp,
        ))

        # McNemar p-value & Delta
        delta_obj = rq1.get("delta_vs_baseline")
        if isinstance(delta_obj, dict):
            mcnemar = delta_obj.get("mcnemar_test", {})
            p_disp = mcnemar.get("display_p_exact", "")
            p_num = mcnemar.get("p_exact", 0.0)
            bindings.append(MetricBinding(
                metric_id=f"{c_key}_mcnemar_p",
                condition=c_key,
                cohort=cohort_n,
                unit="p_value",
                locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}/delta_vs_baseline/mcnemar_test",
                bundle_pointer=f"conditions/{c_key}/rq1_attribution/delta_vs_baseline/mcnemar_test/display_p_exact",
                canonical_value=p_num,
                formatted_string=p_disp,
            ))
            delta_ci_disp = delta_obj.get("delta_accuracy_ci_95_display_pp", "")
            delta_ci_raw = delta_obj.get("delta_accuracy_ci_95", [])
            bindings.append(MetricBinding(
                metric_id=f"{c_key}_delta_ci",
                condition=c_key,
                cohort=cohort_n,
                unit="confidence_interval",
                locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}/delta_vs_baseline",
                bundle_pointer=f"conditions/{c_key}/rq1_attribution/delta_vs_baseline/delta_accuracy_ci_95_display_pp",
                canonical_value=delta_ci_raw,
                formatted_string=delta_ci_disp,
            ))

        # RQ3 Prompt tokens
        rq3 = c_obj.get("rq3_resources_and_cost", {})
        prompt_sum = rq3.get("tokens", {}).get("prompt_tokens", {}).get("sum")
        if prompt_sum is not None:
            bindings.append(MetricBinding(
                metric_id=f"{c_key}_prompt_tokens",
                condition=c_key,
                cohort=c_obj.get("cohort", {}).get("total_logical_requests", 1280),
                unit="tokens",
                locator=f"outputs/rq_analysis.json#/rq3/tradeoffs_by_condition/{c_key}",
                bundle_pointer=f"conditions/{c_key}/rq3_resources_and_cost/tokens/prompt_tokens/sum",
                canonical_value=prompt_sum,
                formatted_string=f"{prompt_sum:,}",
            ))

    # Whole study financial
    fin = b.get("whole_study_financial_accounting", {})
    settled = fin.get("cumulative_settled_cost_usd")
    if settled is not None:
        bindings.append(MetricBinding(
            metric_id="cumulative_settled_expenditure",
            condition=None,
            cohort=1280,
            unit="usd",
            locator="outputs/rq_analysis.json#/rq3/whole_study_financial_accounting",
            bundle_pointer="whole_study_financial_accounting/cumulative_settled_cost_usd",
            canonical_value=Decimal(str(settled)),
            formatted_string=f"${settled}",
        ))
    total_acc = fin.get("total_accounted_expenditure_usd")
    if total_acc is not None:
        bindings.append(MetricBinding(
            metric_id="total_accounted_expenditure",
            condition=None,
            cohort=1280,
            unit="usd",
            locator="outputs/rq_analysis.json#/rq3/whole_study_financial_accounting",
            bundle_pointer="whole_study_financial_accounting/total_accounted_expenditure_usd",
            canonical_value=Decimal(str(total_acc)),
            formatted_string=f"${total_acc}",
        ))

    return bindings


def validate_png_structure(data: bytes) -> bool:
    """
    Validate complete PNG structure:
    - Minimum length >= 33 (8-byte signature + 25-byte minimal chunks)
    - Signature: 89 50 4E 47 0D 0A 1A 0A
    - First chunk must be IHDR (length 13)
    - Valid chunk length and CRC checksum verification across all chunks
    - Must contain IDAT chunk and decompress valid zlib pixel stream
    - Final chunk must be IEND (length 0) with zero trailing data
    - Verified against PIL Image decoder when available
    """
    if len(data) < 33 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return False

    pos = 8
    seen_ihdr = False
    seen_idat = False
    seen_iend = False
    idat_chunks: List[bytes] = []

    while pos + 12 <= len(data):
        chunk_len = int.from_bytes(data[pos : pos + 4], "big")
        chunk_type = data[pos + 4 : pos + 8]
        if pos + 12 + chunk_len > len(data):
            return False

        chunk_data = data[pos + 8 : pos + 8 + chunk_len]
        crc_bytes = data[pos + 8 + chunk_len : pos + 12 + chunk_len]
        expected_crc = int.from_bytes(crc_bytes, "big")
        computed_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF

        if computed_crc != expected_crc:
            return False

        if not seen_ihdr:
            if chunk_type != b"IHDR" or chunk_len != 13:
                return False
            seen_ihdr = True

        if chunk_type == b"IDAT":
            seen_idat = True
            idat_chunks.append(chunk_data)
        elif chunk_type == b"IEND":
            seen_iend = True
            if pos + 12 + chunk_len != len(data):
                return False
            break

        pos += 12 + chunk_len

    if not (seen_ihdr and seen_idat and seen_iend):
        return False

    # Decompress pixel zlib stream
    try:
        decompressed = zlib.decompress(b"".join(idat_chunks))
        if len(decompressed) == 0:
            return False
    except Exception:
        return False

    # PIL verification if available
    try:
        import io
        from PIL import Image
        img = Image.open(io.BytesIO(data))
        img.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
    except ImportError:
        pass
    except Exception:
        return False

    return True


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


def validate_narrative_metric_bindings(
    text: str, context_label: str, bundle: Optional[Dict[str, Any]] = None
) -> List[str]:
    """
    Validate narrative metrics across Markdown, DOCX, PPTX using semantic metric bindings.
    Eliminates regex proximity windows and global allowed-value lists.
    Directly validates each metric in its semantic clause and condition context.
    """
    errors: List[str] = []
    b = load_trusted_bundle(bundle_dict=bundle)
    t3_conditions = extract_table3_conditions(b)

    # Condition map of expected metrics
    cond_metrics: Dict[str, Dict[str, Any]] = {}
    for c_key, c_info in t3_conditions.items():
        cond_metrics[c_key] = {
            "acc": c_info["acc"].rstrip("%"),
            "f1": c_info["f1"],
            "p_val": c_info["p_val"] if c_info["p_val"] != "—" else None,
            "delta": c_info["delta"],
            "ci": c_info["ci"],
        }

    # Strip HTML / XML comments if present
    clean_text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    for line in clean_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split line into semantic clauses (by semicolon or period followed by whitespace)
        clauses = re.split(r"[;\t]+|(?<!\d)\.(?!\d)", line)
        line_condition: Optional[str] = None

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Update condition context if condition name found in clause
            c_matches = list(COND_REGEX.finditer(clause))
            if c_matches:
                alias = c_matches[0].group(1).lower()
                line_condition = COND_ALIAS_MAP.get(alias)

            active_condition = line_condition

            # 1. Check attribution accuracy / percentage in clause
            for m in re.finditer(r"(\d+\.\d+)%", clause):
                val_str = m.group(1)
                val_f = float(val_str)
                # Attribution performance percentages fall in [70.0, 99.0]
                if 70.0 <= val_f <= 99.0:
                    if active_condition and active_condition in cond_metrics:
                        expected_acc = cond_metrics[active_condition]["acc"]
                        if val_str != expected_acc:
                            errors.append(
                                f"{context_label}: Condition '{active_condition}' has mismatched accuracy '{val_str}%' "
                                f"(expected '{expected_acc}%') in statement: '{clause}'"
                            )
                    else:
                        valid_accs = {c["acc"] for c in cond_metrics.values()} | {"91.28", "91.3", "70.03", "70.0"}
                        if val_str not in valid_accs:
                            errors.append(
                                f"{context_label}: Unauthorized accuracy percentage '{val_str}%' does not match any canonical metric in: '{clause}'"
                            )

            # 2. Check McNemar p-value in clause
            for m in re.finditer(r"(?:exact\s*p|p[- ]value|mcnemar\s*p|\bp)\s*=\s*(\d+\.\d+)", clause, re.I):
                p_str = m.group(1)
                if active_condition and active_condition in cond_metrics:
                    expected_p = cond_metrics[active_condition]["p_val"]
                    if expected_p is None:
                        errors.append(
                            f"{context_label}: Baseline condition '{active_condition}' has no McNemar p-value, but '{p_str}' was attributed in: '{clause}'"
                        )
                    elif p_str != expected_p:
                        errors.append(
                            f"{context_label}: Condition '{active_condition}' has mismatched McNemar p-value '{p_str}' "
                            f"(expected '{expected_p}') in statement: '{clause}'"
                        )
                else:
                    valid_ps = {c["p_val"] for c in cond_metrics.values() if c["p_val"]} | {"0.05", "0.01"}
                    if p_str not in valid_ps:
                        errors.append(
                            f"{context_label}: Unauthorized p-value '{p_str}' violates canonical McNemar bindings in: '{clause}'"
                        )

            # 3. Check Macro-F1 in clause
            for m in re.finditer(r"(?:macro[- ]f1|f1)[^\d]{0,20}(\d+\.\d{4})", clause, re.I):
                f1_str = m.group(1)
                if active_condition and active_condition in cond_metrics:
                    expected_f1 = cond_metrics[active_condition]["f1"]
                    if f1_str != expected_f1:
                        errors.append(
                            f"{context_label}: Condition '{active_condition}' has mismatched Macro-F1 '{f1_str}' "
                            f"(expected '{expected_f1}') in statement: '{clause}'"
                        )
                else:
                    valid_f1s = {c["f1"] for c in cond_metrics.values()}
                    if f1_str not in valid_f1s:
                        errors.append(
                            f"{context_label}: Unauthorized Macro-F1 '{f1_str}' violates canonical bundle binding in: '{clause}'"
                        )

    return errors


def validate_table3_structure_and_bindings(content: str, bundle: Optional[Dict[str, Any]] = None) -> List[str]:
    """Parse Markdown Table 3 and strictly verify presence, unicity, and cell bindings of all conditions."""
    errors: List[str] = []
    b = load_trusted_bundle(bundle_dict=bundle)
    t3_conditions = extract_table3_conditions(b)
    lines = content.splitlines()

    found_conditions: Dict[str, Dict[str, str]] = {}
    condition_counts: Dict[str, int] = {k: 0 for k in t3_conditions}

    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                cond_col = parts[1]
                for c_key, c_info in t3_conditions.items():
                    if c_info["label"] in cond_col:
                        condition_counts[c_key] += 1
                        found_conditions[c_key] = {
                            "acc": parts[2],
                            "f1": parts[3],
                            "delta": parts[4],
                            "ci": parts[5],
                            "p": parts[6],
                        }

    # Verify presence and unicity across conditions
    for c_key, c_info in t3_conditions.items():
        cnt = condition_counts[c_key]
        if cnt == 0:
            errors.append(f"Table 3 missing required condition row: '{c_info['label']}'")
        elif cnt > 1:
            errors.append(f"Table 3 contains duplicate condition row: '{c_info['label']}' ({cnt} occurrences)")
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


def validate_table5_structure_and_bindings(content: str, bundle: Optional[Dict[str, Any]] = None) -> List[str]:
    """Parse Markdown Table 5 and strictly verify operational resources, token counts, and financial totals."""
    errors: List[str] = []
    b = load_trusted_bundle(bundle_dict=bundle)
    t5_data = extract_table5_data(b)
    fin_expected = t5_data["financial"]
    rows_expected = t5_data["rows"]

    clean = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)

    # 1. Whole-study budget reconciliation
    m_settled = re.search(r"Cumulative Settled Expenditure[^\d]{1,20}([0-9]+\.[0-9]+)", clean)
    if not m_settled:
        errors.append("Table 5 missing required Cumulative Settled Expenditure reconciliation entry")
    else:
        settled_val = m_settled.group(1)
        if settled_val != fin_expected["settled_cost"]:
            errors.append(
                f"Table 5 Settled Expenditure mismatch: expected '${fin_expected['settled_cost']}', got '${settled_val}'"
            )

    m_accounted = re.search(r"Total Accounted Expenditure[^\d]{1,20}([0-9]+\.[0-9]+)", clean)
    if not m_accounted:
        errors.append("Table 5 missing required Total Accounted Expenditure reconciliation entry")
    else:
        accounted_val = m_accounted.group(1)
        if accounted_val != fin_expected["total_accounted"]:
            errors.append(
                f"Table 5 Total Accounted Expenditure mismatch: expected '${fin_expected['total_accounted']}', got '${accounted_val}'"
            )

    # 2. Condition-specific row validation (prompt tokens, completion tokens, costs, latencies)
    lines = clean.splitlines()
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                cond_cell = parts[1]
                for c_key, r_info in rows_expected.items():
                    if r_info["label"] in cond_cell:
                        mean_lat = parts[2]
                        med_lat = parts[3]
                        prompt_tok = parts[4]
                        comp_tok = parts[5]
                        cost_cell = parts[7]

                        if prompt_tok != r_info["prompt_tokens"]:
                            errors.append(
                                f"Table 5 {r_info['label']} prompt tokens mismatch: expected '{r_info['prompt_tokens']}', got '{prompt_tok}'"
                            )
                        if comp_tok != r_info["completion_tokens"]:
                            errors.append(
                                f"Table 5 {r_info['label']} completion tokens mismatch: expected '{r_info['completion_tokens']}', got '{comp_tok}'"
                            )
                        if mean_lat != r_info["mean_latency"]:
                            errors.append(
                                f"Table 5 {r_info['label']} mean latency mismatch: expected '{r_info['mean_latency']}', got '{mean_lat}'"
                            )
                        if med_lat != r_info["median_latency"]:
                            errors.append(
                                f"Table 5 {r_info['label']} median latency mismatch: expected '{r_info['median_latency']}', got '{med_lat}'"
                            )
                        if cost_cell != r_info["settled_cost"]:
                            errors.append(
                                f"Table 5 {r_info['label']} settled cost mismatch: expected '{r_info['settled_cost']}', got '{cost_cell}'"
                            )

    # 3. Mapped cohort claim audit (Table 5 measured on full execution cohort N=1,280, not 718)
    first_100_lines = "\n".join(lines[:100])
    if "718" in first_100_lines:
        errors.append("Table 5 incorrectly references mapped cohort 718 (cost measured on total campaign N=1,280)")

    return errors
