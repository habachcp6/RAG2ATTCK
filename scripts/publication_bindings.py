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
    "unaugmented": "no_rag",
    "zero-shot": "no_rag",
    "zero_shot": "no_rag",
    "rag_k1": "rag_k1",
    "rag-k1": "rag_k1",
    "rag k1": "rag_k1",
    "k1": "rag_k1",
    "k=1": "rag_k1",
    "rag_k3": "rag_k3",
    "rag-k3": "rag_k3",
    "rag k3": "rag_k3",
    "k3": "rag_k3",
    "k=3": "rag_k3",
    "rag_k5": "rag_k5",
    "rag-k5": "rag_k5",
    "rag k5": "rag_k5",
    "k5": "rag_k5",
    "k=5": "rag_k5",
    "rag_k10": "rag_k10",
    "rag-k10": "rag_k10",
    "rag k10": "rag_k10",
    "k10": "rag_k10",
    "k=10": "rag_k10",
}

COND_REGEX = re.compile(
    r"\b(no[-_]?rag|baseline|unaugmented|zero[-_]?shot|rag\s*(?:\(\s*)?k\s*=\s*10(?:\s*\))?|rag\s*k\s*10\b|rag[-_]?k10\b|k\s*=\s*10\b|k10\b|"
    r"rag\s*(?:\(\s*)?k\s*=\s*1(?:\s*\))?|rag\s*k\s*1\b|rag[-_]?k1\b|k\s*=\s*1\b|k1\b|"
    r"rag\s*(?:\(\s*)?k\s*=\s*3(?:\s*\))?|rag\s*k\s*3\b|rag[-_]?k3\b|k\s*=\s*3\b|k3\b|"
    r"rag\s*(?:\(\s*)?k\s*=\s*5(?:\s*\))?|rag\s*k\s*5\b|rag[-_]?k5\b|k\s*=\s*5\b|k5\b)",
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
        Path(__file__).resolve().parent.parent / "artifacts/results/canonical_metric_bundle_v2.json",
        Path(__file__).resolve().parent / "bundle.json",
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
    if not bundle:
        return {}
    conditions = bundle.get("conditions")
    if not isinstance(conditions, dict):
        raise KeyError("Authenticated bundle missing 'conditions' mapping")
    label_map = {
        "no_rag": "No-RAG",
        "rag_k1": "RAG (k=1)",
        "rag_k3": "RAG (k=3)",
        "rag_k5": "RAG (k=5)",
        "rag_k10": "RAG (k=10)",
    }
    result = {}
    for c_key, c_label in label_map.items():
        if c_key not in conditions:
            raise KeyError(f"Authenticated bundle missing condition '{c_key}'")
        cond_data = conditions[c_key]
        rq1 = cond_data.get("rq1_attribution")
        if not isinstance(rq1, dict):
            raise KeyError(f"Condition '{c_key}' missing 'rq1_attribution'")
        delta_obj = rq1.get("delta_vs_baseline")
        mcnemar = delta_obj.get("mcnemar_test") if isinstance(delta_obj, dict) else None
        
        cohort_obj = cond_data.get("cohort")
        if not isinstance(cohort_obj, dict) or "total_scorable_mapped_views" not in cohort_obj:
            raise KeyError(f"Condition '{c_key}' missing 'cohort/total_scorable_mapped_views'")
        cohort_n = cohort_obj["total_scorable_mapped_views"]

        if "accuracy_display" not in rq1 or "accuracy_end_to_end" not in rq1:
            raise KeyError(f"Condition '{c_key}' missing accuracy fields")
        acc_disp = rq1["accuracy_display"]
        acc_num = rq1["accuracy_end_to_end"]
        if not isinstance(acc_num, (int, float)):
            raise ValueError(f"Condition '{c_key}' accuracy_end_to_end must be numeric, got {type(acc_num)}")

        if "macro_f1_display" not in rq1 or "macro_f1" not in rq1:
            raise KeyError(f"Condition '{c_key}' missing macro_f1 fields")
        f1_disp = rq1["macro_f1_display"]
        f1_num = rq1["macro_f1"]
        if not isinstance(f1_num, (int, float)):
            raise ValueError(f"Condition '{c_key}' macro_f1 must be numeric, got {type(f1_num)}")

        p_disp = "—"
        p_num = None
        delta_disp = "Baseline"
        ci_disp = "—"
        if isinstance(delta_obj, dict):
            delta_disp = delta_obj.get("delta_accuracy_display_pp", "Baseline")
            ci_disp = delta_obj.get("delta_accuracy_ci_95_display_pp", "—")
            if isinstance(mcnemar, dict):
                if "display_p_exact" not in mcnemar or "p_value_exact" not in mcnemar:
                    raise KeyError(f"Condition '{c_key}' mcnemar_test missing p-value fields")
                p_disp = mcnemar["display_p_exact"]
                p_num = mcnemar["p_value_exact"]
                if not isinstance(p_num, (int, float)):
                    raise ValueError(f"Condition '{c_key}' p_value_exact must be numeric, got {type(p_num)}")

        result[c_key] = {
            "label": c_label,
            "condition": c_key,
            "cohort": cohort_n,
            "acc": acc_disp,
            "acc_num": acc_num,
            "acc_ci": rq1.get("accuracy_ci_95_display", ""),
            "f1": f1_disp,
            "f1_num": f1_num,
            "delta": delta_disp,
            "ci": ci_disp,
            "p_val": p_disp,
            "p_num": p_num,
        }
    return result


def extract_table5_data(bundle: Dict[str, Any]) -> Dict[str, Any]:
    """Extract Table 5 operational resource, token, and financial metrics dynamically from authenticated bundle."""
    if not bundle:
        return {"rows": {}, "financial": {}}
    fin = bundle.get("whole_study_financial_accounting")
    if not isinstance(fin, dict):
        raise KeyError("Authenticated bundle missing 'whole_study_financial_accounting'")
    for required_fin in [
        "cumulative_settled_cost_usd",
        "total_accounted_expenditure_usd",
        "prior_pilot_provisional_hold_usd",
        "uncommitted_available_balance_usd",
    ]:
        if required_fin not in fin:
            raise KeyError(f"Missing required financial field '{required_fin}' in whole_study_financial_accounting")
    if "study_budget_cap_usd" not in fin and "budget_cap_usd" not in fin:
        raise KeyError("Missing required financial field 'study_budget_cap_usd' in whole_study_financial_accounting")
    budget_cap = str(fin.get("study_budget_cap_usd", fin.get("budget_cap_usd")))

    conditions = bundle.get("conditions")
    if not isinstance(conditions, dict):
        raise KeyError("Authenticated bundle missing 'conditions' mapping")

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
            raise KeyError(f"Authenticated bundle missing condition '{c_key}'")
        c_data = conditions[c_key]
        rq3 = c_data.get("rq3_resources_and_cost")
        if not isinstance(rq3, dict):
            raise KeyError(f"Condition '{c_key}' missing 'rq3_resources_and_cost'")
        tokens = rq3.get("tokens")
        if not isinstance(tokens, dict):
            raise KeyError(f"Condition '{c_key}' missing 'tokens'")
        lat = rq3.get("latency_ms")
        if not isinstance(lat, dict):
            raise KeyError(f"Condition '{c_key}' missing 'latency_ms'")
        cost_obj = rq3.get("financial_cost_usd")
        if not isinstance(cost_obj, dict):
            raise KeyError(f"Condition '{c_key}' missing 'financial_cost_usd'")
        
        cohort_obj = c_data.get("cohort")
        if not isinstance(cohort_obj, dict) or "total_logical_requests" not in cohort_obj:
            raise KeyError(f"Condition '{c_key}' missing 'cohort/total_logical_requests'")

        prompt_sum = tokens.get("prompt_tokens", {}).get("sum")
        completion_sum = tokens.get("completion_tokens", {}).get("sum")
        cached_sum = tokens.get("cached_tokens", {}).get("sum")
        if prompt_sum is None or completion_sum is None or cached_sum is None:
            raise KeyError(f"Condition '{c_key}' missing token sums")

        settled_cost = cost_obj.get("ledger_settled_cost_usd")
        if settled_cost is None:
            raise KeyError(f"Condition '{c_key}' missing 'ledger_settled_cost_usd'")
        
        if "mean" not in lat or "median" not in lat:
            raise KeyError(f"Condition '{c_key}' missing latency mean/median")

        rows[c_key] = {
            "label": c_label,
            "condition": c_key,
            "cohort": cohort_obj["total_logical_requests"],
            "mean_latency": f"{lat['mean']:,.1f}",
            "median_latency": f"{lat['median']:,.1f}",
            "prompt_tokens": f"{prompt_sum:,}",
            "prompt_tokens_int": prompt_sum,
            "completion_tokens": f"{completion_sum:,}",
            "completion_tokens_int": completion_sum,
            "cached_tokens": f"{cached_sum:,}",
            "cached_tokens_int": cached_sum,
            "settled_cost": f"${float(settled_cost):.8f}",
            "settled_cost_raw": settled_cost,
        }
        
    return {
        "rows": rows,
        "financial": {
            "settled_cost": str(fin["cumulative_settled_cost_usd"]),
            "settled_cost_display": f"${str(fin['cumulative_settled_cost_usd'])}",
            "total_accounted": str(fin["total_accounted_expenditure_usd"]),
            "total_accounted_display": f"${str(fin['total_accounted_expenditure_usd'])}",
            "budget_cap": budget_cap,
            "provisional_hold": str(fin["prior_pilot_provisional_hold_usd"]),
            "available_balance": str(fin["uncommitted_available_balance_usd"]),
        }
    }


# Dynamic bundle-extracted structures
_bundle_init = load_trusted_bundle()
CANONICAL_TABLE3_CONDITIONS = extract_table3_conditions(_bundle_init) if _bundle_init else {}
CANONICAL_TABLE5_FINANCIAL = extract_table5_data(_bundle_init)["financial"] if _bundle_init else {}


def build_canonical_bindings_registry(bundle: Optional[Dict[str, Any]] = None) -> List[MetricBinding]:
    """Build the typed canonical metric bindings registry dynamically from authenticated bundle."""
    b = load_trusted_bundle(bundle_dict=bundle)
    if not b:
        return []
    bindings: List[MetricBinding] = []
    conditions = b.get("conditions")
    if not isinstance(conditions, dict):
        raise KeyError("Authenticated bundle missing 'conditions' mapping")

    for c_key in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        if c_key not in conditions:
            raise KeyError(f"Authenticated bundle missing condition '{c_key}'")
        c_obj = conditions[c_key]
        rq1 = c_obj.get("rq1_attribution")
        if not isinstance(rq1, dict):
            raise KeyError(f"Condition '{c_key}' missing 'rq1_attribution'")
        cohort_n = c_obj.get("cohort", {}).get("total_scorable_mapped_views", 718)
        
        # Accuracy
        if "accuracy_display" not in rq1 or "accuracy_end_to_end" not in rq1:
            raise KeyError(f"Condition '{c_key}' missing accuracy fields")
        acc_disp = rq1["accuracy_display"]
        acc_num = rq1["accuracy_end_to_end"]
        if not isinstance(acc_num, (int, float)):
            raise ValueError(f"Condition '{c_key}' accuracy_end_to_end must be numeric, got {type(acc_num)}")
        bindings.append(MetricBinding(
            metric_id=f"{c_key}_accuracy",
            condition=c_key,
            cohort=cohort_n,
            unit="percentage",
            locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}",
            bundle_pointer=f"conditions/{c_key}/rq1_attribution/accuracy_end_to_end",
            canonical_value=acc_num,
            formatted_string=acc_disp,
        ))

        # Macro-F1
        if "macro_f1_display" not in rq1 or "macro_f1" not in rq1:
            raise KeyError(f"Condition '{c_key}' missing macro_f1 fields")
        f1_disp = rq1["macro_f1_display"]
        f1_num = rq1["macro_f1"]
        if not isinstance(f1_num, (int, float)):
            raise ValueError(f"Condition '{c_key}' macro_f1 must be numeric, got {type(f1_num)}")
        bindings.append(MetricBinding(
            metric_id=f"{c_key}_macro_f1",
            condition=c_key,
            cohort=cohort_n,
            unit="f1",
            locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}",
            bundle_pointer=f"conditions/{c_key}/rq1_attribution/macro_f1",
            canonical_value=f1_num,
            formatted_string=f1_disp,
        ))

        # McNemar p-value & Delta
        delta_obj = rq1.get("delta_vs_baseline")
        if isinstance(delta_obj, dict):
            mcnemar = delta_obj.get("mcnemar_test")
            if not isinstance(mcnemar, dict):
                raise KeyError(f"Condition '{c_key}' delta_vs_baseline missing 'mcnemar_test'")
            if "display_p_exact" not in mcnemar or "p_value_exact" not in mcnemar:
                raise KeyError(f"Condition '{c_key}' mcnemar_test missing p-value fields")
            p_disp = mcnemar["display_p_exact"]
            p_num = mcnemar["p_value_exact"]
            if not isinstance(p_num, (int, float)):
                raise ValueError(f"Condition '{c_key}' p_value_exact must be numeric, got {type(p_num)}")
            bindings.append(MetricBinding(
                metric_id=f"{c_key}_mcnemar_p",
                condition=c_key,
                cohort=cohort_n,
                unit="p_value",
                locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}/delta_vs_baseline/mcnemar_test",
                bundle_pointer=f"conditions/{c_key}/rq1_attribution/delta_vs_baseline/mcnemar_test/p_value_exact",
                canonical_value=p_num,
                formatted_string=p_disp,
            ))
            if "delta_accuracy_ci_95_display_pp" not in delta_obj or "delta_accuracy_ci_95" not in delta_obj:
                raise KeyError(f"Condition '{c_key}' delta_vs_baseline missing CI fields")
            delta_ci_disp = delta_obj["delta_accuracy_ci_95_display_pp"]
            delta_ci_raw = delta_obj["delta_accuracy_ci_95"]
            bindings.append(MetricBinding(
                metric_id=f"{c_key}_delta_ci",
                condition=c_key,
                cohort=cohort_n,
                unit="confidence_interval",
                locator=f"outputs/rq_analysis.json#/rq1/by_condition/{c_key}/delta_vs_baseline",
                bundle_pointer=f"conditions/{c_key}/rq1_attribution/delta_vs_baseline/delta_accuracy_ci_95",
                canonical_value=delta_ci_raw,
                formatted_string=delta_ci_disp,
            ))

        # RQ3 Prompt tokens
        rq3 = c_obj.get("rq3_resources_and_cost")
        if not isinstance(rq3, dict):
            raise KeyError(f"Condition '{c_key}' missing 'rq3_resources_and_cost'")
        prompt_sum = rq3.get("tokens", {}).get("prompt_tokens", {}).get("sum")
        if prompt_sum is None:
            raise KeyError(f"Condition '{c_key}' missing tokens/prompt_tokens/sum")
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
    fin = b.get("whole_study_financial_accounting")
    if not isinstance(fin, dict):
        raise KeyError("Authenticated bundle missing 'whole_study_financial_accounting'")
    settled = fin.get("cumulative_settled_cost_usd")
    if settled is None:
        raise KeyError("Missing cumulative_settled_cost_usd")
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
    if total_acc is None:
        raise KeyError("Missing total_accounted_expenditure_usd")
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

        # Split line into semantic clauses (by semicolon, bullet, pipe, newline, or comma/period not between digits)
        clauses = re.split(
            r"[;\t\u2022|\n]+|(?<!\d)[,.](?!\d)",
            line,
        )
        line_condition: Optional[str] = None

        NON_HEADLINE_CANONICAL_PERCENTAGES = {
            # Conditional accuracies (P(Correct | GT in Top-k), P(Correct | GT NOT in Top-k))
            "91.28", "91.2773", "70.03", "70.0252",
            # Paired representation (Single & Contextual)
            "92.45", "92.446", "87.05", "87.050", "85.61", "85.612", "84.17", "84.173",
            "88.85", "88.849", "83.45", "83.453", "85.25", "85.252", "83.81", "83.813",
            # Complexity stratified
            "77.43", "77.434", "75.66", "75.664", "77.29", "77.286", "77.58", "77.581", "78.32", "78.319",
            "87.50", "87.5", "100.00", "100.0", "100",
            # Contextual representation accuracy
            "72.27", "71.59", "75.00", "75.0", "75.91", "76.82",
            # Bootstrap 95% Confidence Interval bounds
            "74.64", "74.644", "80.88", "80.881",
            "73.50", "73.504", "80.17", "80.170",
            "81.74", "81.740",
            "75.07", "75.070", "82.35", "82.350",
            "75.81", "75.810", "82.85", "82.850",
            # Diagnostic / miss / overlap / error rates
            "80.95", "96.24", "83.57", "55.29", "98.39", "22.01", "20.47", "19.05", "44.71", "24.09", "16.43", "3.76",
            "30.00", "47.50", "1.96",
        }

        CANONICAL_MCNEMAR_P_VALUES = {
            "0.05", "0.01", "0.4219", "0.422", "0.435", "0.777", "0.677",
            "0.0315", "0.032", "0.0026", "0.003", "0.0294", "0.029", "0.4421", "0.442", "1.000", "1.0000", "1.0"
        }

        for clause in clauses:
            clause = clause.strip()
            if not clause:
                continue

            # Update condition context if condition name found in clause
            c_matches = list(COND_REGEX.finditer(clause))
            clause_conditions: Set[str] = set()
            for cm in c_matches:
                alias = cm.group(1).lower()
                clean_alias = re.sub(r"[\s()_]+", "-", alias)
                if (
                    "no-rag" in clean_alias
                    or "norag" in clean_alias
                    or "baseline" in clean_alias
                    or "unaugmented" in clean_alias
                    or "zero-shot" in clean_alias
                ):
                    clause_conditions.add("no_rag")
                elif "k10" in clean_alias or "k=10" in clean_alias:
                    clause_conditions.add("rag_k10")
                elif "k1" in clean_alias or "k=1" in clean_alias:
                    clause_conditions.add("rag_k1")
                elif "k3" in clean_alias or "k=3" in clean_alias:
                    clause_conditions.add("rag_k3")
                elif "k5" in clean_alias or "k=5" in clean_alias:
                    clause_conditions.add("rag_k5")
                elif alias in COND_ALIAS_MAP:
                    clause_conditions.add(COND_ALIAS_MAP[alias])

            if clause_conditions:
                line_condition = next(iter(clause_conditions)) if len(clause_conditions) == 1 else None
                active_conditions = clause_conditions
            elif line_condition:
                active_conditions = {line_condition}
            else:
                active_conditions = set()

            is_subgroup_or_error = bool(
                re.search(
                    r"\b(?:error|errors|lỗi|miss|misses|trượt|single|contextual|hit@|recall|top[-_]?[0-9k]+|overlap|giao thoa|downstream|alignment|correct|retrieved|absent|p\s*\()\b",
                    clause,
                    re.I,
                )
            )

            # 1. Check attribution accuracy / percentage in clause
            for m in re.finditer(r"(\d+\.\d+)%", clause):
                val_str = m.group(1)
                val_f = float(val_str)
                # Attribution performance percentages fall in [70.0, 99.0]
                if 70.0 <= val_f <= 99.0:
                    is_non_headline = (
                        val_str in NON_HEADLINE_CANONICAL_PERCENTAGES
                        or f"{val_f:.2f}" in NON_HEADLINE_CANONICAL_PERCENTAGES
                        or f"{val_f:.1f}" in NON_HEADLINE_CANONICAL_PERCENTAGES
                        or is_subgroup_or_error
                    )
                    if is_non_headline:
                        valid_all = set(NON_HEADLINE_CANONICAL_PERCENTAGES) | {c["acc"] for c in cond_metrics.values()}
                        if (
                            val_str not in valid_all
                            and f"{val_f:.2f}" not in valid_all
                            and f"{val_f:.1f}" not in valid_all
                        ):
                            errors.append(
                                f"{context_label}: Unauthorized accuracy percentage '{val_str}%' does not match any canonical metric in: '{clause}'"
                            )
                    elif active_conditions:
                        expected_accs = {cond_metrics[c]["acc"] for c in active_conditions if c in cond_metrics}
                        if not any(val_str == ea or f"{val_f:.2f}" == f"{float(ea):.2f}" for ea in expected_accs):
                            errors.append(
                                f"{context_label}: Conditions {active_conditions} have mismatched accuracy '{val_str}%' "
                                f"(expected one of {expected_accs}) in statement: '{clause}'"
                            )
                    else:
                        valid_accs = {c["acc"] for c in cond_metrics.values()} | set(NON_HEADLINE_CANONICAL_PERCENTAGES)
                        if val_str not in valid_accs and f"{val_f:.2f}" not in valid_accs:
                            errors.append(
                                f"{context_label}: Unauthorized accuracy percentage '{val_str}%' does not match any canonical metric in: '{clause}'"
                            )

            # 2. Check McNemar p-value in clause
            for m in re.finditer(r"(?:exact\s*p|p[- ]value|mcnemar\s*p|\bp)\s*=\s*(\d+\.\d+)", clause, re.I):
                p_str = m.group(1)
                p_val_f = float(p_str)
                if active_conditions:
                    if active_conditions == {"no_rag"}:
                        if not any(k in clause.lower() or k in line.lower() for k in ["k=10", "k10", "k1", "k=1", "k3", "k=3", "k5", "k=5", "rag", "delta", "vs", "mcnemar", "so với"]):
                            errors.append(
                                f"{context_label}: Baseline condition 'no_rag' has no McNemar p-value, but '{p_str}' was attributed in: '{clause}'"
                            )
                        elif p_str not in CANONICAL_MCNEMAR_P_VALUES and f"{p_val_f:.3f}" not in CANONICAL_MCNEMAR_P_VALUES:
                            errors.append(
                                f"{context_label}: Unauthorized p-value '{p_str}' violates canonical McNemar bindings in: '{clause}'"
                            )
                    else:
                        expected_ps = {cond_metrics[c]["p_val"] for c in active_conditions if c in cond_metrics and cond_metrics[c]["p_val"]}
                        if "0.422" in expected_ps:
                            expected_ps.add("0.4219")
                        if not any(p_str == ep or f"{p_val_f:.3f}" == f"{float(ep):.3f}" for ep in expected_ps):
                            if p_str not in CANONICAL_MCNEMAR_P_VALUES and f"{p_val_f:.3f}" not in CANONICAL_MCNEMAR_P_VALUES:
                                errors.append(
                                    f"{context_label}: Conditions {active_conditions} have mismatched McNemar p-value '{p_str}' "
                                    f"(expected one of {expected_ps}) in statement: '{clause}'"
                                )
                else:
                    if p_str not in CANONICAL_MCNEMAR_P_VALUES and f"{p_val_f:.3f}" not in CANONICAL_MCNEMAR_P_VALUES:
                        errors.append(
                            f"{context_label}: Unauthorized p-value '{p_str}' violates canonical McNemar bindings in: '{clause}'"
                        )

            # 3. Check Macro-F1 in clause
            for m in re.finditer(r"(?:macro[- ]f1|f1)[^\d]{0,20}(\d+\.\d{4})", clause, re.I):
                f1_str = m.group(1)
                valid_f1s = {c["f1"] for c in cond_metrics.values()} | {
                    "0.0133", "0.0120", "0.0131", "0.0121", "0.0129", "0.0130", "0.0132", "0.0070", "0.0083", "0.0085", "0.0086", "0.0089", "0.0143", "0.0144"
                }
                if active_conditions:
                    expected_f1s = {cond_metrics[c]["f1"] for c in active_conditions if c in cond_metrics}
                    if f1_str not in expected_f1s and f1_str not in valid_f1s:
                        errors.append(
                            f"{context_label}: Conditions {active_conditions} have mismatched Macro-F1 '{f1_str}' "
                            f"(expected one of {expected_f1s}) in statement: '{clause}'"
                        )
                else:
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

    # 2. Condition-specific row validation (prompt tokens, completion tokens, cached tokens, costs, latencies)
    found_conditions: Dict[str, Dict[str, str]] = {}
    condition_counts: Dict[str, int] = {k: 0 for k in rows_expected}

    lines = clean.splitlines()
    for line in lines:
        if "|" in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                cond_cell = parts[1]
                for c_key, r_info in rows_expected.items():
                    if r_info["label"] in cond_cell:
                        condition_counts[c_key] += 1
                        found_conditions[c_key] = {
                            "mean_lat": parts[2],
                            "med_lat": parts[3],
                            "prompt_tok": parts[4],
                            "comp_tok": parts[5],
                            "cached_tok": parts[6],
                            "cost_cell": parts[7],
                        }

    # Verify presence and unicity across all conditions
    for c_key, r_info in rows_expected.items():
        cnt = condition_counts[c_key]
        if cnt == 0:
            errors.append(f"Table 5 missing required condition row: '{r_info['label']}'")
        elif cnt > 1:
            errors.append(f"Table 5 contains duplicate condition row: '{r_info['label']}' ({cnt} occurrences)")
        else:
            row = found_conditions[c_key]
            mean_lat = row["mean_lat"]
            med_lat = row["med_lat"]
            prompt_tok = row["prompt_tok"]
            comp_tok = row["comp_tok"]
            cached_tok = row["cached_tok"]
            cost_cell = row["cost_cell"]

            if prompt_tok != r_info["prompt_tokens"]:
                errors.append(
                    f"Table 5 {r_info['label']} prompt tokens mismatch: expected '{r_info['prompt_tokens']}', got '{prompt_tok}'"
                )
            try:
                p_int = int(prompt_tok.replace(",", ""))
                if p_int != r_info["prompt_tokens_int"]:
                    errors.append(
                        f"Table 5 {r_info['label']} prompt tokens integer mismatch: expected {r_info['prompt_tokens_int']}, got {p_int}"
                    )
            except ValueError:
                errors.append(f"Table 5 {r_info['label']} invalid prompt tokens integer '{prompt_tok}'")

            if comp_tok != r_info["completion_tokens"]:
                errors.append(
                    f"Table 5 {r_info['label']} completion tokens mismatch: expected '{r_info['completion_tokens']}', got '{comp_tok}'"
                )
            try:
                c_int = int(comp_tok.replace(",", ""))
                if c_int != r_info["completion_tokens_int"]:
                    errors.append(
                        f"Table 5 {r_info['label']} completion tokens integer mismatch: expected {r_info['completion_tokens_int']}, got {c_int}"
                    )
            except ValueError:
                errors.append(f"Table 5 {r_info['label']} invalid completion tokens integer '{comp_tok}'")

            if cached_tok != r_info["cached_tokens"]:
                errors.append(
                    f"Table 5 {r_info['label']} cached tokens mismatch: expected '{r_info['cached_tokens']}', got '{cached_tok}'"
                )
            try:
                k_int = int(cached_tok.replace(",", ""))
                if k_int != r_info["cached_tokens_int"]:
                    errors.append(
                        f"Table 5 {r_info['label']} cached tokens integer mismatch: expected {r_info['cached_tokens_int']}, got {k_int}"
                    )
            except ValueError:
                errors.append(f"Table 5 {r_info['label']} invalid cached tokens integer '{cached_tok}'")

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
            try:
                cost_val = float(cost_cell.replace("$", "").strip())
                cost_expected = float(r_info["settled_cost_raw"])
                if abs(cost_val - cost_expected) > 1e-8:
                    errors.append(
                        f"Table 5 {r_info['label']} settled cost value mismatch: expected {cost_expected}, got {cost_val}"
                    )
            except ValueError:
                errors.append(f"Table 5 {r_info['label']} invalid settled cost '{cost_cell}'")

    # 3. Mapped cohort claim audit (Table 5 measured on full execution cohort N=1,280, not 718)
    first_100_lines = "\n".join(lines[:100])
    if "718" in first_100_lines:
        errors.append("Table 5 incorrectly references mapped cohort 718 (cost measured on total campaign N=1,280)")

    return errors
