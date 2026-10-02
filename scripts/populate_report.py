"""Scientific Report Populator from Diagnostic Evaluation & Analysis Fixtures.

Safely consumes canonical evaluation JSON fixtures and Specialist B's rq_analysis.json,
formats metrics strictly adhering to Scientific Protocol v1.1 and s2_report_population_plan.md,
and populates placeholders in scientific report templates.

SAFETY & INTEGRITY BOUNDARY:
- Mode gate: Strictly operates under --mode fixture. Canonical mode is hard disabled.
- Strictly operates on mock fixture outputs (fixture_only: true).
- Strictly zero live prediction reads (never touches predictions_*.jsonl).
- Strictly zero provider/network calls (offline socket compliant).
- All generated documents carry prominent private labeling:
  "fixture_only: true" / "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation.experiment_metrics import CONDITIONS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DISCLAIMER_TEXT = "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"
DEFAULT_FIXTURE_DIR = REPO_ROOT / ".tmp" / "s1-offline-reproduction" / "fixture_diagnostics"
FALLBACK_FIXTURE_DIR = REPO_ROOT / "outputs" / "reproduction" / "fixture_diagnostics"
DEFAULT_TEMPLATE_PATH = REPO_ROOT / "docs" / "report" / "scientific_report.md"
DEFAULT_OUTPUT_MD = REPO_ROOT / "reports" / "evidence" / "fixture_populated_report.md"
DEFAULT_AUDIT_JSON = REPO_ROOT / "reports" / "evidence" / "populated_report_slots_fixture.json"

EXPECTED_SOURCE_SHA256 = "c48eeb27b19626344e5f10b2cac674437b4053bb01f014060905702c52235f95"

REQUIRED_FIXTURE_FILES = [
    "per_condition_metrics.json",
    "failure_decomposition.json",
    "retrieval_conditional_metrics.json",
    "overall_metrics.json",
    "run_provenance.json",
    "rq_analysis.json",
    "_fixture_metadata.json",
]


def compute_file_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file on disk."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found on disk: {filepath}")
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def validate_finite_number(
    val: Any,
    name: str,
    min_val: float | None = None,
    max_val: float | None = None,
    allow_none: bool = False,
) -> float | None:
    """Validate that a number is finite and within expected bounds.

    Strictly refuses NaN, Inf, and non-numeric types.
    """
    if val is None:
        if allow_none:
            return None
        raise KeyError(f"Required field {name} is None but null is not allowed")

    if not isinstance(val, (int, float)):
        raise TypeError(f"Field {name} expected int or float, got {type(val).__name__}: {val}")

    fval = float(val)
    if not math.isfinite(fval):
        raise ValueError(f"Field {name} must be finite (got {val})")

    if min_val is not None and fval < min_val:
        raise ValueError(f"Field {name} value {fval} below allowable minimum {min_val}")
    if max_val is not None and fval > max_val:
        raise ValueError(f"Field {name} value {fval} above allowable maximum {max_val}")

    return fval


def format_pct(val: float | None) -> str:
    """Format float in [0, 1] as XX.XX% string, or 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"{val * 100:.2f}%"


def format_pp(val: float | None) -> str:
    """Format signed delta float in [-1, 1] as +X.XX pp / -X.XX pp, or 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"{val * 100:+.2f} pp"


def format_int(val: int | None) -> str:
    """Format integer with thousands separator, or 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"{val:,}"


def format_usd(val: float | None, decimals: int = 2) -> str:
    """Format financial USD string, or 'N/A' if None."""
    if val is None:
        return "N/A"
    return f"USD {val:.{decimals}f}"


def format_latency(val_ms: float | None) -> str:
    """Format latency in milliseconds as seconds (X.XXs), or 'N/A' if None."""
    if val_ms is None:
        return "N/A"
    return f"{val_ms / 1000.0:.2f}s"


def assert_fixture_safety(
    fixture_dir: Path,
    metadata: dict[str, Any] | None = None,
    provenance: dict[str, Any] | None = None,
    analysis: dict[str, Any] | None = None,
    files_dict: dict[str, dict[str, Any]] | None = None,
) -> None:
    """Fail closed if target is not certified as mock fixture data.

    Enforces:
    1. metadata fixture_only == True
    2. provenance execution_mode == "mock_fixture"
    3. analysis fixture_only == True and provenance_status == "diagnostic_fixture"
    4. Cross-file consistency (protocol_version, experiment_id, manifest_sha256)
    5. Source hash verification against evaluate_rqs.py
    """
    if metadata is None:
        meta_path = fixture_dir / "_fixture_metadata.json"
        if not meta_path.is_file():
            raise RuntimeError(
                f"[FAIL_CLOSED] Fixture directory {fixture_dir} lacks _fixture_metadata.json"
            )
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))

    if not metadata.get("fixture_only"):
        raise RuntimeError(
            f"[FAIL_CLOSED] _fixture_metadata.json in {fixture_dir} must declare fixture_only=True"
        )

    if provenance is None:
        prov_path = fixture_dir / "run_provenance.json"
        if prov_path.is_file():
            provenance = json.loads(prov_path.read_text(encoding="utf-8"))
        else:
            provenance = {}

    if provenance and provenance.get("execution_mode") != "mock_fixture":
        raise ValueError(
            f"[FAIL_CLOSED] run_provenance execution_mode in {fixture_dir} "
            f"must be 'mock_fixture' (got {provenance.get('execution_mode')})"
        )

    if analysis is None:
        analysis_path = fixture_dir / "rq_analysis.json"
        if analysis_path.is_file():
            analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        else:
            analysis = {}

    if analysis and not analysis.get("fixture_only"):
        raise ValueError(
            f"[FAIL_CLOSED] rq_analysis.json in {fixture_dir} must declare fixture_only=True"
        )

    if analysis and analysis.get("provenance_status") != "diagnostic_fixture":
        raise ValueError(
            f"[FAIL_CLOSED] rq_analysis provenance_status in {fixture_dir} "
            f"must be 'diagnostic_fixture' (got {analysis.get('provenance_status')})"
        )

    if analysis and "execution_mode" in analysis and analysis["execution_mode"] != "mock_fixture":
        raise ValueError(
            f"[FAIL_CLOSED] rq_analysis execution_mode must be 'mock_fixture' "
            f"(got {analysis['execution_mode']})"
        )

    # Cross-file consistency check (Reject mixed mode)
    if files_dict is not None and provenance:
        base_proto = provenance.get("protocol_version")
        base_exp = provenance.get("experiment_id")
        base_manifest = provenance.get("manifest_sha256")

        for fname, doc in files_dict.items():
            doc_proto = doc.get("protocol_version")
            if doc_proto is not None and base_proto is not None and doc_proto != base_proto:
                raise ValueError(
                    f"[FAIL_CLOSED] Inconsistent protocol_version in {fname}: "
                    f"{doc_proto} != {base_proto}"
                )
            doc_exp = doc.get("experiment_id")
            if doc_exp is not None and base_exp is not None and doc_exp != base_exp:
                raise ValueError(
                    f"[FAIL_CLOSED] Inconsistent experiment_id in {fname}: {doc_exp} != {base_exp}"
                )
            doc_manifest = doc.get("manifest_sha256")
            if (
                doc_manifest is not None
                and base_manifest is not None
                and doc_manifest != base_manifest
            ):
                raise ValueError(
                    f"[FAIL_CLOSED] Inconsistent manifest_sha256 in {fname}: "
                    f"{doc_manifest} != {base_manifest}"
                )

    # Source SHA-256 verification
    if analysis and "source_sha256" in analysis:
        actual_source_hash = analysis["source_sha256"]
        if actual_source_hash != EXPECTED_SOURCE_SHA256:
            raise ValueError(
                f"[FAIL_CLOSED] rq_analysis.json source_sha256 mismatch: "
                f"cited '{actual_source_hash}', expected '{EXPECTED_SOURCE_SHA256}'"
            )


def load_fixture_data(fixture_dir: Path, analysis_file: Path | None = None) -> dict[str, Any]:
    """Load canonical evaluation JSON fixtures and Specialist B's rq_analysis.json.

    Requires ALL 6 canonical evaluator files and _fixture_metadata.json to exist on disk.
    NEVER defaults to empty dictionary.
    """
    if not fixture_dir.is_dir():
        raise FileNotFoundError(f"Fixture directory not found: {fixture_dir}")

    # Check existence of all required files
    for fname in REQUIRED_FIXTURE_FILES:
        target = (
            analysis_file
            if (fname == "rq_analysis.json" and analysis_file)
            else (fixture_dir / fname)
        )
        if not target.is_file():
            raise FileNotFoundError(
                f"[FAIL_CLOSED] Required fixture file missing: {target}. "
                "All 6 canonical evaluator/analysis outputs and _fixture_metadata.json "
                "must be present on disk."
            )

    # Load all files strictly
    meta_path = fixture_dir / "_fixture_metadata.json"
    per_cond_path = fixture_dir / "per_condition_metrics.json"
    failure_decomp_path = fixture_dir / "failure_decomposition.json"
    retrieval_cond_path = fixture_dir / "retrieval_conditional_metrics.json"
    overall_path = fixture_dir / "overall_metrics.json"
    provenance_path = fixture_dir / "run_provenance.json"
    analysis_p = analysis_file or (fixture_dir / "rq_analysis.json")

    metadata = json.loads(meta_path.read_text(encoding="utf-8"))
    per_condition = json.loads(per_cond_path.read_text(encoding="utf-8"))
    failure_decomp = json.loads(failure_decomp_path.read_text(encoding="utf-8"))
    retrieval_cond = json.loads(retrieval_cond_path.read_text(encoding="utf-8"))
    overall = json.loads(overall_path.read_text(encoding="utf-8"))
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    analysis = json.loads(analysis_p.read_text(encoding="utf-8"))

    files_dict = {
        "per_condition_metrics": per_condition,
        "failure_decomposition": failure_decomp,
        "retrieval_conditional_metrics": retrieval_cond,
        "overall_metrics": overall,
        "run_provenance": provenance,
        "rq_analysis": analysis,
    }

    assert_fixture_safety(
        fixture_dir=fixture_dir,
        metadata=metadata,
        provenance=provenance,
        analysis=analysis,
        files_dict=files_dict,
    )

    return {
        "fixture_dir": fixture_dir,
        "metadata": metadata,
        "per_condition_metrics": per_condition,
        "failure_decomposition": failure_decomp,
        "retrieval_conditional_metrics": retrieval_cond,
        "overall_metrics": overall,
        "run_provenance": provenance,
        "rq_analysis": analysis,
    }


def extract_slots(data: dict[str, Any]) -> dict[str, Any]:
    """Extract and format all table slots according to canonical schema pointers.

    Enforces:
    - Zero default: missing required fields raise KeyError.
    - Finite validation: NaN/Inf rejected with ValueError.
    - Derived counts: scorable_n is derived from exports, NOT hardcoded to 718.
    - Downstream selection failure formula:
      downstream_selection_failure = retrieval_success_count - retrieval_success_correct_count
    """
    if "conditions" not in data["per_condition_metrics"]:
        raise KeyError("per_condition_metrics.json missing 'conditions' key")
    per_cond = data["per_condition_metrics"]["conditions"]

    if "by_condition" not in data["failure_decomposition"]:
        raise KeyError("failure_decomposition.json missing 'by_condition' key")
    failure_by_cond = data["failure_decomposition"]["by_condition"]

    if "by_condition" not in data["retrieval_conditional_metrics"]:
        raise KeyError("retrieval_conditional_metrics.json missing 'by_condition' key")
    retrieval_by_cond = data["retrieval_conditional_metrics"]["by_condition"]

    rq_analysis = data["rq_analysis"]
    if "rq1" not in rq_analysis or "by_condition" not in rq_analysis["rq1"]:
        raise KeyError("rq_analysis.json missing 'rq1.by_condition' key")
    rq1_by_cond = rq_analysis["rq1"]["by_condition"]

    if "rq3" not in rq_analysis or "tradeoffs_by_condition" not in rq_analysis["rq3"]:
        raise KeyError("rq_analysis.json missing 'rq3.tradeoffs_by_condition' key")
    rq3_tradeoffs = rq_analysis["rq3"]["tradeoffs_by_condition"]

    if "view_diagnostics" not in rq_analysis["rq3"]:
        raise KeyError("rq_analysis.json missing 'rq3.view_diagnostics' key")
    rq3_views = rq_analysis["rq3"]["view_diagnostics"]

    complexity_by_cond = rq_analysis.get("new_proposed_producer_stratified_gt_complexity", {}).get(
        "by_condition", {}
    )

    slots: dict[str, Any] = {
        "_metadata": {
            "fixture_only": True,
            "disclaimer": DISCLAIMER_TEXT,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_fixture_dir": str(data["fixture_dir"]),
        },
        "table_2a": {},
        "table_2b": {},
        "table_3": {},
        "table_4": {},
        "table_5": {},
    }

    depth_map = {"no_rag": 0, "rag_k1": 1, "rag_k3": 3, "rag_k5": 5, "rag_k10": 10}

    for c in CONDITIONS:
        k = depth_map[c]

        if c not in per_cond:
            raise KeyError(f"Condition '{c}' not found in per_condition_metrics.json")
        c_eval = per_cond[c]

        if c not in rq1_by_cond:
            raise KeyError(f"Condition '{c}' not found in rq_analysis.json (rq1.by_condition)")

        # 1. Derive scorable count dynamically from actual exports
        if "scorable_sample_count" not in c_eval:
            raise KeyError(
                f"Condition '{c}' missing 'scorable_sample_count' in per_condition_metrics.json"
            )
        scorable_n_val = validate_finite_number(
            c_eval["scorable_sample_count"],
            f"{c}.scorable_sample_count",
            min_val=0,
        )
        assert scorable_n_val is not None
        scorable_n = int(scorable_n_val)

        # 2. Table 2a: Attribution Performance
        if "accuracy_end_to_end" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'accuracy_end_to_end'")
        if "accuracy_valid_outputs" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'accuracy_valid_outputs'")
        if "macro_f1" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'macro_f1'")

        acc_e2e = validate_finite_number(
            c_eval["accuracy_end_to_end"],
            f"{c}.accuracy_end_to_end",
            min_val=0.0,
            max_val=1.0,
        )
        acc_valid = validate_finite_number(
            c_eval["accuracy_valid_outputs"],
            f"{c}.accuracy_valid_outputs",
            min_val=0.0,
            max_val=1.0,
        )
        macro_f1 = validate_finite_number(
            c_eval["macro_f1"], f"{c}.macro_f1", min_val=0.0, max_val=1.0
        )

        single_gt_acc = None
        multi_gt_acc = None
        complex_delta = None
        if c in complexity_by_cond:
            c_complex = complexity_by_cond[c]
            single_gt_acc = validate_finite_number(
                c_complex.get("single_gt_accuracy_e2e"),
                f"{c}.single_gt_accuracy_e2e",
                min_val=0.0,
                max_val=1.0,
                allow_none=True,
            )
            multi_gt_acc = validate_finite_number(
                c_complex.get("multi_gt_accuracy_e2e"),
                f"{c}.multi_gt_accuracy_e2e",
                min_val=0.0,
                max_val=1.0,
                allow_none=True,
            )
            complex_delta = validate_finite_number(
                c_complex.get("complexity_accuracy_delta"),
                f"{c}.complexity_accuracy_delta",
                min_val=-1.0,
                max_val=1.0,
                allow_none=True,
            )

        slots["table_2a"][c] = {
            "condition": c,
            "k": k,
            "scorable_n": scorable_n,
            "accuracy_end_to_end": format_pct(acc_e2e),
            "accuracy_valid_outputs": format_pct(acc_valid),
            "macro_f1": format_pct(macro_f1),
            "single_gt_accuracy_e2e": format_pct(single_gt_acc),
            "multi_gt_accuracy_e2e": format_pct(multi_gt_acc),
            "complexity_accuracy_delta": format_pp(complex_delta),
        }

        # 3. Table 2b: Attribution Diagnostics
        if "completed_record_count" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'completed_record_count'")
        if "parse_failure_count" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'parse_failure_count'")
        if "invalid_id_count" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'invalid_id_count'")
        if "invalid_id_rate" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'invalid_id_rate'")

        completed_val = validate_finite_number(
            c_eval["completed_record_count"],
            f"{c}.completed_record_count",
            min_val=0,
        )
        parse_fail_val = validate_finite_number(
            c_eval["parse_failure_count"],
            f"{c}.parse_failure_count",
            min_val=0,
        )
        invalid_id_val = validate_finite_number(
            c_eval["invalid_id_count"], f"{c}.invalid_id_count", min_val=0
        )
        invalid_rate = validate_finite_number(
            c_eval["invalid_id_rate"],
            f"{c}.invalid_id_rate",
            min_val=0.0,
            max_val=1.0,
        )

        slots["table_2b"][c] = {
            "condition": c,
            "scorable_n": scorable_n,
            "completed_outputs": format_int(int(completed_val)),  # type: ignore[arg-type]
            "parse_failures": format_int(int(parse_fail_val)),  # type: ignore[arg-type]
            "invalid_ids": format_int(int(invalid_id_val)),  # type: ignore[arg-type]
            "invalid_id_rate": format_pct(invalid_rate),
        }

        # 4. Table 3: Representation Stratification
        if c not in rq3_views:
            raise KeyError(f"Condition '{c}' not found in rq_analysis.json (rq3.view_diagnostics)")
        c_view = rq3_views[c]

        if "single_view_accuracy_e2e" not in c_view:
            raise KeyError(f"Condition '{c}' missing 'single_view_accuracy_e2e'")
        if "contextual_view_accuracy_e2e" not in c_view:
            raise KeyError(f"Condition '{c}' missing 'contextual_view_accuracy_e2e'")
        if "view_accuracy_delta" not in c_view:
            raise KeyError(f"Condition '{c}' missing 'view_accuracy_delta'")

        single_acc = validate_finite_number(
            c_view["single_view_accuracy_e2e"],
            f"{c}.single_view_accuracy_e2e",
            min_val=0.0,
            max_val=1.0,
            allow_none=True,
        )
        context_acc = validate_finite_number(
            c_view["contextual_view_accuracy_e2e"],
            f"{c}.contextual_view_accuracy_e2e",
            min_val=0.0,
            max_val=1.0,
            allow_none=True,
        )
        single_f1 = validate_finite_number(
            c_view.get("single_view_macro_f1"),
            f"{c}.single_view_macro_f1",
            min_val=0.0,
            max_val=1.0,
            allow_none=True,
        )
        context_f1 = validate_finite_number(
            c_view.get("contextual_view_macro_f1"),
            f"{c}.contextual_view_macro_f1",
            min_val=0.0,
            max_val=1.0,
            allow_none=True,
        )
        delta_acc = validate_finite_number(
            c_view["view_accuracy_delta"],
            f"{c}.view_accuracy_delta",
            min_val=-1.0,
            max_val=1.0,
            allow_none=True,
        )

        slots["table_3"][c] = {
            "condition": c,
            "single_acc": format_pct(single_acc),
            "context_acc": format_pct(context_acc),
            "single_macro_f1": format_pct(single_f1),
            "context_macro_f1": format_pct(context_f1),
            "delta_acc": format_pp(delta_acc),
        }

        # 5. Table 4: Decoupled Failure Decomposition
        if c not in failure_by_cond:
            raise KeyError(f"Condition '{c}' not found in failure_decomposition.json")
        c_fail = failure_by_cond[c]

        if "correct_count" not in c_eval:
            raise KeyError(f"Condition '{c}' missing 'correct_count'")
        correct_c_val = validate_finite_number(
            c_eval["correct_count"], f"{c}.correct_count", min_val=0
        )
        assert correct_c_val is not None
        total_errors = scorable_n - int(correct_c_val)

        if "invalid_attack_id_count" not in c_fail:
            raise KeyError(f"Condition '{c}' missing 'invalid_attack_id_count'")
        if "parse_failure_count" not in c_fail:
            raise KeyError(f"Condition '{c}' missing 'parse_failure_count'")
        if "provider_failure_count" not in c_fail:
            raise KeyError(f"Condition '{c}' missing 'provider_failure_count'")

        invalid_id_fail = validate_finite_number(
            c_fail["invalid_attack_id_count"],
            f"{c}.invalid_attack_id_count",
            min_val=0,
        )
        parse_fail_count = validate_finite_number(
            c_fail["parse_failure_count"],
            f"{c}.parse_failure_count",
            min_val=0,
        )
        prov_fail_count = validate_finite_number(
            c_fail["provider_failure_count"],
            f"{c}.provider_failure_count",
            min_val=0,
        )

        if c == "no_rag":
            ret_miss_str = "N/A"
            downstream_fail_str = "N/A"
            param_recov_str = "N/A"
        else:
            if c not in retrieval_by_cond:
                raise KeyError(f"Condition '{c}' not found in retrieval_conditional_metrics.json")
            c_ret = retrieval_by_cond[c]

            if "retrieval_miss_count" not in c_fail:
                raise KeyError(f"Condition '{c}' missing 'retrieval_miss_count'")
            if "retrieval_success_count" not in c_ret:
                raise KeyError(f"Condition '{c}' missing 'retrieval_success_count'")
            if "retrieval_success_correct_count" not in c_ret:
                raise KeyError(f"Condition '{c}' missing 'retrieval_success_correct_count'")
            if "retrieval_failure_correct_count" not in c_ret:
                raise KeyError(f"Condition '{c}' missing 'retrieval_failure_correct_count'")

            ret_miss = validate_finite_number(
                c_fail["retrieval_miss_count"],
                f"{c}.retrieval_miss_count",
                min_val=0,
            )
            ret_succ = validate_finite_number(
                c_ret["retrieval_success_count"],
                f"{c}.retrieval_success_count",
                min_val=0,
            )
            ret_succ_corr = validate_finite_number(
                c_ret["retrieval_success_correct_count"],
                f"{c}.retrieval_success_correct_count",
                min_val=0,
            )
            param_recov = validate_finite_number(
                c_ret["retrieval_failure_correct_count"],
                f"{c}.retrieval_failure_correct_count",
                min_val=0,
            )

            assert ret_succ is not None and ret_succ_corr is not None
            downstream_fail = int(ret_succ) - int(ret_succ_corr)
            if downstream_fail < 0:
                raise ValueError(
                    f"Negative downstream selection failure for {c}: {downstream_fail}"
                )

            ret_miss_str = format_int(int(ret_miss))  # type: ignore[arg-type]
            downstream_fail_str = format_int(downstream_fail)
            param_recov_str = format_int(int(param_recov))  # type: ignore[arg-type]

        slots["table_4"][c] = {
            "condition": c,
            "total_errors": format_int(total_errors),
            "retrieval_miss": ret_miss_str,
            "downstream_selection_failure": downstream_fail_str,
            "parametric_recovery": param_recov_str,
            "invalid_attack_id": format_int(int(invalid_id_fail)),  # type: ignore[arg-type]
            "parse_failure": format_int(int(parse_fail_count)),  # type: ignore[arg-type]
            "provider_failure": format_int(int(prov_fail_count)),  # type: ignore[arg-type]
        }

        # 6. Table 5: Resource Consumption & Latency Scaling
        if c not in rq3_tradeoffs:
            raise KeyError(
                f"Condition '{c}' not found in rq_analysis.json (rq3.tradeoffs_by_condition)"
            )
        c_trade = rq3_tradeoffs[c]

        if "tokens" not in c_trade:
            raise KeyError(f"Condition '{c}' missing 'tokens' sub-object")
        tokens = c_trade["tokens"]
        if "latency_ms" not in c_trade:
            raise KeyError(f"Condition '{c}' missing 'latency_ms' sub-object")
        latency = c_trade["latency_ms"]
        if "financial_cost_usd" not in c_trade:
            raise KeyError(f"Condition '{c}' missing 'financial_cost_usd' sub-object")
        fin = c_trade["financial_cost_usd"]

        if "mean_completion_tokens" not in tokens:
            raise KeyError(f"Condition '{c}' missing 'mean_completion_tokens'")
        if "mean_prompt_tokens" not in tokens:
            raise KeyError(f"Condition '{c}' missing 'mean_prompt_tokens'")
        if "mean" not in latency or "median" not in latency or "p95" not in latency:
            raise KeyError(f"Condition '{c}' missing latency percentiles")
        if "total_cost_usd" not in fin:
            raise KeyError(f"Condition '{c}' missing 'total_cost_usd'")
        if "cost_per_logical_request_usd" not in fin:
            raise KeyError(f"Condition '{c}' missing 'cost_per_logical_request_usd'")

        mean_comp_tok = validate_finite_number(
            tokens["mean_completion_tokens"],
            f"{c}.mean_completion_tokens",
            min_val=0.0,
        )
        mean_prompt_tok = validate_finite_number(
            tokens["mean_prompt_tokens"],
            f"{c}.mean_prompt_tokens",
            min_val=0.0,
        )
        assert mean_prompt_tok is not None and mean_comp_tok is not None

        sum_prompt_tok = validate_finite_number(
            tokens.get("sum_prompt_tokens", int(round(mean_prompt_tok * 1280))),
            f"{c}.sum_prompt_tokens",
            min_val=0.0,
        )
        sum_comp_tok = validate_finite_number(
            tokens.get("sum_completion_tokens", int(round(mean_comp_tok * 1280))),
            f"{c}.sum_completion_tokens",
            min_val=0.0,
        )

        mean_lat_ms = validate_finite_number(latency["mean"], f"{c}.latency_mean", min_val=0.0)
        med_lat_ms = validate_finite_number(latency["median"], f"{c}.latency_median", min_val=0.0)
        p95_lat_ms = validate_finite_number(latency["p95"], f"{c}.latency_p95", min_val=0.0)

        tot_cost = validate_finite_number(fin["total_cost_usd"], f"{c}.total_cost_usd", min_val=0.0)
        cost_per_req = validate_finite_number(
            fin["cost_per_logical_request_usd"],
            f"{c}.cost_per_logical_request_usd",
            min_val=0.0,
        )

        slots["table_5"][c] = {
            "condition": c,
            "total_input_tokens": format_int(int(sum_prompt_tok)),  # type: ignore[arg-type]
            "total_output_tokens": format_int(int(sum_comp_tok)),  # type: ignore[arg-type]
            "mean_output_tokens_req": f"{mean_comp_tok:.1f}",
            "mean_latency_s": format_latency(mean_lat_ms),
            "median_latency_s": format_latency(med_lat_ms),
            "p95_latency_s": format_latency(p95_lat_ms),
            "total_cost_usd": format_usd(tot_cost, 2),
            "mean_cost_query_usd": format_usd(cost_per_req, 6),
        }

    return slots


def populate_report_text(template_text: str, slots: dict[str, Any], fixture_dir: Path) -> str:
    """Populate markdown template text with formatted slot values and private labels."""
    lines = template_text.splitlines()
    new_lines: list[str] = []

    # Table regex matchers for rows
    t2a_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|.*")
    t2b_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|\s*(\d+)\s*\|.*")
    t3_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")
    t4_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")
    t5_row_pat = re.compile(r"^\|\s*`([a-z0-9_]+)`\s*\|.*")

    in_table: str | None = None

    for line in lines:
        stripped = line.strip()

        # Track which table we are currently scanning
        if "*Table 2a:" in stripped:
            in_table = "table_2a"
            new_lines.append(line)
            continue
        elif "*Table 2b:" in stripped:
            in_table = "table_2b"
            new_lines.append(line)
            continue
        elif "*Table 3:" in stripped:
            in_table = "table_3"
            new_lines.append(line)
            continue
        elif "*Table 4:" in stripped:
            in_table = "table_4"
            new_lines.append(line)
            continue
        elif "*Table 5:" in stripped:
            in_table = "table_5"
            new_lines.append(line)
            continue
        elif stripped.startswith("### ") or (
            stripped.startswith("## ") and not stripped.startswith("## 6.")
        ):
            in_table = None

        # Row replacement logic
        if in_table == "table_2a" and stripped.startswith("| `"):
            m = t2a_row_pat.match(stripped)
            if m:
                c = m.group(1)
                k = m.group(2)
                if c in slots["table_2a"]:
                    s = slots["table_2a"][c]
                    new_line = (
                        f"| `{c}` | {k} | {s['scorable_n']} | {s['accuracy_end_to_end']} | "
                        f"{s['accuracy_valid_outputs']} | {s['macro_f1']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_2b" and stripped.startswith("| `"):
            m = t2b_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_2b"]:
                    s = slots["table_2b"][c]
                    new_line = (
                        f"| `{c}` | {s['scorable_n']} | {s['completed_outputs']} | "
                        f"{s['parse_failures']} | {s['invalid_ids']} | {s['invalid_id_rate']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_3" and stripped.startswith("| `"):
            m = t3_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_3"]:
                    s = slots["table_3"][c]
                    new_line = (
                        f"| `{c}` | {s['single_acc']} | {s['context_acc']} | "
                        f"{s['single_macro_f1']} | {s['context_macro_f1']} | {s['delta_acc']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_4" and stripped.startswith("| `"):
            m = t4_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_4"]:
                    s = slots["table_4"][c]
                    new_line = (
                        f"| `{c}` | {s['total_errors']} | {s['retrieval_miss']} | "
                        f"{s['downstream_selection_failure']} | {s['parametric_recovery']} | "
                        f"{s['invalid_attack_id']} | {s['parse_failure']} | "
                        f"{s['provider_failure']} |"
                    )
                    new_lines.append(new_line)
                    continue

        elif in_table == "table_5" and stripped.startswith("| `"):
            m = t5_row_pat.match(stripped)
            if m:
                c = m.group(1)
                if c in slots["table_5"]:
                    s = slots["table_5"][c]
                    new_line = (
                        f"| `{c}` | {s['total_input_tokens']} | {s['total_output_tokens']} | "
                        f"{s['mean_output_tokens_req']} | {s['mean_latency_s']} | "
                        f"{s['median_latency_s']} | {s['p95_latency_s']} | "
                        f"{s['total_cost_usd']} | {s['mean_cost_query_usd']} |"
                    )
                    new_lines.append(new_line)
                    continue

        new_lines.append(line)

    populated = "\n".join(new_lines)

    # Append Supplementary Execution Provenance table before References (### 8.3)
    supp_marker = "#### Supplementary Execution Provenance (Diagnostic Fixture Mode)"
    if supp_marker not in populated and "### 8.3" in populated:
        fixture_files = [
            ("Diagnostic Overall Metrics", fixture_dir / "overall_metrics.json"),
            (
                "Diagnostic Condition Metrics",
                fixture_dir / "per_condition_metrics.json",
            ),
            (
                "Diagnostic Failure Decomposition",
                fixture_dir / "failure_decomposition.json",
            ),
            (
                "Diagnostic Retrieval Conditional",
                fixture_dir / "retrieval_conditional_metrics.json",
            ),
            ("Diagnostic RQ Analysis", fixture_dir / "rq_analysis.json"),
            ("Diagnostic Run Provenance", fixture_dir / "run_provenance.json"),
        ]

        supp_lines = [
            "",
            supp_marker,
            (
                "The following diagnostic fixture files were consumed during this "
                "offline verification run:"
            ),
            "",
            "| Asset Description | File Path | Digest Type | SHA-256 Digest |",
            "| :--- | :--- | :--- | :--- |",
        ]
        for desc, fpath in fixture_files:
            if fpath.is_file():
                f_hash = compute_file_sha256(fpath)
                try:
                    rel_p = str(fpath.relative_to(REPO_ROOT)).replace("\\", "/")
                except ValueError:
                    rel_p = str(fpath).replace("\\", "/")
                supp_lines.append(f"| **{desc}** | `{rel_p}` | File SHA-256 | `{f_hash}` |")

        supp_lines.extend(["", ""])
        populated = populated.replace("### 8.3", "\n".join(supp_lines) + "### 8.3")

    # Add prominent private labeling warning banner at the very top
    banner = [
        "<!-- FIXTURE_ONLY: true -->",
        "> [!WARNING]",
        f"> **{DISCLAIMER_TEXT}**",
        "> This scientific report preview was populated using synthetic offline test fixtures",
        "> for pipeline verification and presentation readiness purposes only.",
        "> It contains **NO** canonical live experimental results or live model predictions.",
        "",
        "---",
        "",
    ]

    return "\n".join(banner) + populated


def run_pipeline(
    fixture_dir: Path,
    template_path: Path,
    output_path: Path,
    audit_json_path: Path | None = None,
    mode: str = "fixture",
    export_docx: bool = False,
    force_in_place: bool = False,
) -> tuple[Path, dict[str, Any]]:
    """Execute end-to-end report population.

    Enforces:
    - Mode check: canonical mode is disabled pending root S2 terminal audit seal.
    - Safety check: prevents overwriting canonical report template unless forced.
    """
    if mode == "canonical":
        raise RuntimeError(
            "[FAIL_CLOSED] Canonical mode is disabled pending root S2 terminal audit seal."
        )
    elif mode != "fixture":
        raise ValueError(f"Unknown mode: {mode}")

    if output_path.resolve() == DEFAULT_TEMPLATE_PATH.resolve() and not force_in_place:
        raise ValueError(
            "[SAFETY_GUARD] Refusing to overwrite canonical report template "
            f"({DEFAULT_TEMPLATE_PATH}) with fixture data! Specify a different --output "
            "path or provide --force-in-place if explicitly testing template replacement."
        )

    # 1. Load and validate fixture data strictly (fails closed on missing/inconsistent files)
    data = load_fixture_data(fixture_dir)

    # 2. Extract and format slots (fails closed on missing fields or non-finite values)
    slots = extract_slots(data)

    # 3. Read template
    template_text = template_path.read_text(encoding="utf-8")

    # 4. Populate report markdown
    populated_text = populate_report_text(template_text, slots, fixture_dir)

    # 5. Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(populated_text, encoding="utf-8")
    print(f"[OK] Wrote populated fixture report to: {output_path}")

    # 6. Write audit JSON if requested
    if audit_json_path:
        audit_json_path.parent.mkdir(parents=True, exist_ok=True)
        audit_json_path.write_text(
            json.dumps(slots, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] Wrote audit slots JSON to: {audit_json_path}")

    # 7. Optional DOCX compilation
    if export_docx:
        from scripts.export_report_docx import (
            build_docx_from_markdown,
        )

        docx_path = output_path.with_suffix(".docx")
        build_docx_from_markdown(output_path, docx_path)
        print(f"[OK] Exported Word document to: {docx_path}")

    return output_path, slots


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Populate scientific report tables from offline test fixtures (fixture_only: true)."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["fixture", "canonical"],
        default="fixture",
        help="Execution mode (default: fixture). Canonical mode is disabled pending S2 seal.",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to directory containing mock fixture evaluation outputs.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=DEFAULT_TEMPLATE_PATH,
        help="Path to scientific report markdown template.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Path to write populated markdown output.",
    )
    parser.add_argument(
        "--audit-json",
        type=Path,
        default=DEFAULT_AUDIT_JSON,
        help="Path to write populated slots audit JSON.",
    )
    parser.add_argument(
        "--export-docx",
        action="store_true",
        help="Also export populated markdown to Word (.docx).",
    )
    parser.add_argument(
        "--force-in-place",
        action="store_true",
        help="Allow overwriting template file in place (USE WITH CAUTION).",
    )
    return parser.parse_args()


def main() -> None:
    """CLI entrypoint."""
    args = parse_args()

    # Determine active fixture dir
    target_fixture_dir = args.fixture_dir
    if not target_fixture_dir.is_dir() and FALLBACK_FIXTURE_DIR.is_dir():
        print(
            f"[INFO] Default fixture dir not found at {target_fixture_dir}, "
            f"falling back to {FALLBACK_FIXTURE_DIR}"
        )
        target_fixture_dir = FALLBACK_FIXTURE_DIR

    try:
        run_pipeline(
            fixture_dir=target_fixture_dir,
            template_path=args.template,
            output_path=args.output,
            audit_json_path=args.audit_json,
            mode=args.mode,
            export_docx=args.export_docx,
            force_in_place=args.force_in_place,
        )
    except Exception as exc:
        print(f"[ERROR] Population failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
