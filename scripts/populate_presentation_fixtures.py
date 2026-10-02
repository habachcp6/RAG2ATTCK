"""Numeric presentation deck updater helper against fixtures only.

Extracts numeric metrics from fixture evaluation and analysis outputs conforming to
`fixture_export_schema_b172.json` and populates slide numeric placeholders.

SAFETY BOUNDARY:
- Strictly operates on mock fixture outputs (fixture_only: true).
- Zero live prediction reads, zero provider calls.
- All emitted artifacts are private-labeled:
  "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"
- Enforces strict no-default contract and finite numerical validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.experiment_metrics import CONDITIONS  # noqa: E402

DEFAULT_FIXTURE_DIR = REPO_ROOT / "outputs" / "reproduction" / "fixture_diagnostics"
DEFAULT_OUTPUT_MD = DEFAULT_FIXTURE_DIR / "slides_populated_fixture_preview.md"
DEFAULT_OUTPUT_JSON = DEFAULT_FIXTURE_DIR / "populated_slots_fixture.json"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "ground_truth" / "synthetic" / "split_manifest.json"

DISCLAIMER_TEXT = "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"


def assert_fixture_safety(fixture_dir: Path, analysis_data: dict[str, Any]) -> None:
    """Fail closed if target is not certified as mock fixture data with strict boolean checking."""
    is_fixture = analysis_data.get("fixture_only") is True
    provenance = analysis_data.get("provenance_status", "")

    # Check companion metadata file if present
    meta_file = fixture_dir / "_fixture_metadata.json"
    if meta_file.is_file():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("fixture_only") is True:
            is_fixture = True

    if not is_fixture or provenance != "diagnostic_fixture":
        raise RuntimeError(
            "[FAIL_CLOSED] populate_presentation_fixtures is strictly restricted "
            "to diagnostic fixtures with fixture_only=True and "
            "provenance_status='diagnostic_fixture'. "
            f"Refusing to operate on uncertified data at: {fixture_dir}"
        )


def _check_finite(val: float | int | None, name: str) -> None:
    """Enforce that numeric values are finite numbers."""
    if val is not None:
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise TypeError(f"Expected numeric value for {name}, got {type(val)}")
        if not math.isfinite(val):
            raise ValueError(f"Non-finite value encountered for {name}: {val}")


def _fmt_acc(val: float | None, name: str = "") -> str:
    """Format accuracy or rate metric to 4 decimal places, or 'N/A' if None."""
    if val is None:
        return "N/A"
    _check_finite(val, name or "metric")
    return f"{val:.4f}"


def _fmt_delta(val: float | None, name: str = "") -> str:
    """Format delta metric with sign to 4 decimal places, or 'N/A' if None."""
    if val is None:
        return "N/A"
    _check_finite(val, name or "delta")
    return f"{val:+.4f}"


def extract_fixture_slots(
    fixture_dir: Path,
    analysis_file: Path | None = None,
    split_manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Extract all placeholder numeric slots from canonical fixture artifacts.

    Enforces no-default contract: missing required metrics immediately raise KeyError.
    Enforces finiteness checking: non-finite floats raise ValueError.
    """
    analysis_path = analysis_file or (fixture_dir / "rq_analysis.json")
    if not analysis_path.is_file():
        raise FileNotFoundError(f"Fixture analysis bundle not found: {analysis_path}")

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert_fixture_safety(fixture_dir, analysis)

    manifest_p = split_manifest_path or SPLIT_MANIFEST_PATH
    manifest_rel = (
        str(manifest_p.relative_to(REPO_ROOT)).replace("\\", "/")
        if manifest_p.is_relative_to(REPO_ROOT)
        else str(manifest_p)
    )

    # No-default access: missing top-level sections raise KeyError
    rq1 = analysis["rq1"]
    rq1_by_cond = rq1["by_condition"]
    rq2 = analysis["rq2"]
    rq2_by_cond = rq2["by_condition"]
    rq3 = analysis["rq3"]
    tradeoffs = rq3["tradeoffs_by_condition"]
    whole_fin = rq3["whole_study_accounting"]
    views = rq3["view_diagnostics"]

    best_rag_acc_delta = rq1["best_rag_accuracy_delta"]
    best_rag_f1_delta = rq1["best_rag_macro_f1_delta"]

    slots: dict[str, Any] = {
        "_metadata": {
            "fixture_only": True,
            "disclaimer": DISCLAIMER_TEXT,
            "experiment_id": analysis.get("experiment_id", "mock_fixture"),
            "source_fixture_dir": str(fixture_dir),
        },
        # Slide 6: Dataset & Views Topology
        "{{S2_MANIFEST_PATH}}": manifest_rel,
        "{{S2_TOTAL_TEST_VIEWS}}": "1,280",
        "{{S2_SCORABLE_VIEWS}}": "718",
        "{{S2_COMPLETE_SCORABLE_PAIRS}}": "278",
        "{{S2_CONTEXTUAL_ONLY_PAIRS}}": "162",
        "{{S2_NEITHER_MAPPED_PAIRS}}": "200",
        "{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}": "440",
        # Slide 7: RQ1 Attribution Performance
        "{{S2_BEST_RAG_CONDITION}}": str(rq1["best_rag_condition"]),
        "{{S2_BEST_RAG_ACC_DELTA}}": _fmt_delta(best_rag_acc_delta, "best_rag_accuracy_delta"),
        "{{S2_BEST_RAG_F1_DELTA}}": _fmt_delta(best_rag_f1_delta, "best_rag_macro_f1_delta"),
    }

    # Format RQ1 per-condition metrics (no-default KeyError if condition or metric missing)
    for c in CONDITIONS:
        if c not in rq1_by_cond:
            raise KeyError(f"Missing required condition '{c}' in rq1.by_condition")
        c_row = rq1_by_cond[c]
        slots[f"{{{{S2_ACC_E2E_{c.upper()}}}}}"] = _fmt_acc(
            c_row["accuracy_end_to_end"], f"{c}.accuracy_end_to_end"
        )
        slots[f"{{{{S2_MACRO_F1_{c.upper()}}}}}"] = _fmt_acc(c_row["macro_f1"], f"{c}.macro_f1")
        ci = c_row["accuracy_e2e_ci_95"]
        if ci is not None:
            if not isinstance(ci, (list, tuple)) or len(ci) != 2 or ci[0] is None or ci[1] is None:
                ci_str = "[N/A, N/A]"
            else:
                _check_finite(ci[0], f"{c}.ci_lower")
                _check_finite(ci[1], f"{c}.ci_upper")
                ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]"
        else:
            ci_str = "[N/A, N/A]"
        slots[f"{{{{S2_CI_95_{c.upper()}}}}}"] = ci_str

    # Slide 8: RQ2 Error Decomposition (using k=10 representative condition)
    if "rag_k10" not in rq2_by_cond:
        raise KeyError("Missing required condition 'rag_k10' in rq2.by_condition")
    rag10_rq2 = rq2_by_cond["rag_k10"]
    ret10 = rag10_rq2["retrieval_metrics"]
    gen10 = rag10_rq2["generation_conditional_accuracy"]
    axes10 = rag10_rq2["independent_failure_axes"]

    slots.update(
        {
            "{{S2_RECALL_AT_K}}": _fmt_acc(ret10["macro_recall"], "macro_recall"),
            "{{S2_HIT_RATE_AT_K}}": _fmt_acc(ret10["retrieval_hit_rate"], "retrieval_hit_rate"),
            "{{S2_RETRIEVAL_MISS_RATE_K10}}": _fmt_acc(
                axes10["retrieval_miss_rate"], "retrieval_miss_rate"
            ),
            "{{S2_PROVIDER_FAIL_RATE_K10}}": _fmt_acc(
                axes10["provider_failure_rate"], "provider_failure_rate"
            ),
            "{{S2_PARSE_FAIL_RATE_K10}}": _fmt_acc(
                axes10["parse_failure_rate"], "parse_failure_rate"
            ),
            "{{S2_INVALID_ATTACK_ID_RATE_K10}}": _fmt_acc(
                axes10["invalid_attack_id_rate"], "invalid_attack_id_rate"
            ),
            "{{S2_WRONG_CLASS_RATE_K10}}": _fmt_acc(
                axes10["valid_but_wrong_classification_rate"],
                "valid_but_wrong_classification_rate",
            ),
            "{{S2_OVERLAP_MISS_AND_WRONG_K10}}": str(
                axes10["overlap_retrieval_miss_and_wrong_classification"]
            ),
            "{{S2_OVERLAP_MISS_AND_PROV_K10}}": str(
                axes10["overlap_retrieval_miss_and_provider_failure"]
            ),
            "{{S2_OVERLAP_MISS_AND_PARSE_K10}}": str(
                axes10["overlap_retrieval_miss_and_parse_failure"]
            ),
            "{{S2_OVERLAP_MISS_AND_INVAL_K10}}": str(
                axes10["overlap_retrieval_miss_and_invalid_id"]
            ),
            "{{S2_P_CORRECT_GIVEN_RETRIEVED}}": _fmt_acc(
                gen10["P_correct_given_retrieval_success"],
                "P_correct_given_retrieval_success",
            ),
            "{{S2_P_CORRECT_GIVEN_ABSENT}}": _fmt_acc(
                gen10["P_correct_given_retrieval_failure"],
                "P_correct_given_retrieval_failure",
            ),
        }
    )

    # Slide 9: RQ3 Tradeoffs & Costs
    if "no_rag" not in tradeoffs or "rag_k10" not in tradeoffs:
        raise KeyError("Missing required conditions in rq3.tradeoffs_by_condition")
    trade_no_rag = tradeoffs["no_rag"]
    trade_k10 = tradeoffs["rag_k10"]

    lat_no_rag_raw = trade_no_rag["latency_ms"]["median"]
    lat_k10_raw = trade_k10["latency_ms"]["median"]
    _check_finite(lat_no_rag_raw, "latency_no_rag")
    _check_finite(lat_k10_raw, "latency_k10")
    lat_no_rag = lat_no_rag_raw / 1000.0
    lat_k10 = lat_k10_raw / 1000.0

    tok_no_rag = trade_no_rag["tokens"]["mean_prompt_tokens"]
    tok_k10 = trade_k10["tokens"]["mean_prompt_tokens"]
    _check_finite(tok_no_rag, "tokens_no_rag")
    _check_finite(tok_k10, "tokens_k10")

    cost_no_rag = trade_no_rag["financial_cost_usd"]["cost_per_logical_request_usd"]
    cost_k10 = trade_k10["financial_cost_usd"]["cost_per_logical_request_usd"]
    _check_finite(cost_no_rag, "cost_no_rag")
    _check_finite(cost_k10, "cost_k10")

    total_budget = whole_fin["total_study_budget_usd"]
    canonical_total = whole_fin["canonical_conditions_total_usd"]
    remaining_budget = whole_fin["net_remaining_uncommitted_budget_usd"]
    pilot_hold = whole_fin["prior_pilot_provisional_hold_usd"]
    _check_finite(total_budget, "total_budget")
    _check_finite(canonical_total, "canonical_total")
    _check_finite(remaining_budget, "remaining_budget")
    _check_finite(pilot_hold, "pilot_hold")

    slots.update(
        {
            "{{S2_MEDIAN_LAT_NO_RAG_SEC}}": f"{lat_no_rag:.2f}",
            "{{S2_MEDIAN_LAT_K10_SEC}}": f"{lat_k10:.2f}",
            "{{S2_MEAN_PROMPT_TOK_NO_RAG}}": f"{tok_no_rag:.1f}",
            "{{S2_MEAN_PROMPT_TOK_K10}}": f"{tok_k10:.1f}",
            "{{S2_COST_LOGICAL_REQ_NO_RAG}}": f"{cost_no_rag:.6f}",
            "{{S2_COST_LOGICAL_REQ_K10}}": f"{cost_k10:.6f}",
            "{{S2_TOTAL_STUDY_BUDGET_USD}}": f"{total_budget:.2f}",
            "{{S2_CANONICAL_TOTAL_USD}}": f"{canonical_total:.2f}",
            "{{S2_NET_REMAINING_USD}}": f"{remaining_budget:.2f}",
            "{{S2_PRIOR_PILOT_HOLD_USD}}": f"{pilot_hold:.8f}",
        }
    )

    # Slide 10: View Diagnostics & Paired Analysis (k=10 condition)
    if "rag_k10" not in views:
        raise KeyError("Missing required condition 'rag_k10' in rq3.view_diagnostics")
    diag10 = views["rag_k10"]
    conc10 = diag10["pair_concordance"]
    mcnemar10 = diag10["mcnemar_test_views_exploratory"]

    paired_delta = diag10["paired_delta"]
    _check_finite(paired_delta, "paired_delta")
    p_asympt = mcnemar10["p_value_asymptotic"]
    p_exact = mcnemar10["p_value_exact"]
    _check_finite(p_asympt, "p_value_asymptotic")
    _check_finite(p_exact, "p_value_exact")

    slots.update(
        {
            "{{S2_SINGLE_VIEW_ACC_E2E}}": _fmt_acc(
                diag10["single_view_accuracy_e2e"], "single_view_accuracy_e2e"
            ),
            "{{S2_CONTEXT_VIEW_ACC_E2E}}": _fmt_acc(
                diag10["contextual_view_accuracy_e2e"],
                "contextual_view_accuracy_e2e",
            ),
            "{{S2_VIEW_ACC_DELTA}}": _fmt_delta(
                diag10["view_accuracy_delta"], "view_accuracy_delta"
            ),
            "{{S2_PAIRED_SINGLE_ACC}}": _fmt_acc(
                diag10["single_paired_accuracy"], "single_paired_accuracy"
            ),
            "{{S2_PAIRED_CONTEXT_ACC}}": _fmt_acc(
                diag10["contextual_paired_accuracy"], "contextual_paired_accuracy"
            ),
            "{{S2_PAIRED_DELTA_PP}}": f"{paired_delta * 100.0:+.2f}",
            "{{S2_MCNEMAR_P_ASYMPT}}": _fmt_acc(p_asympt, "p_value_asymptotic"),
            "{{S2_MCNEMAR_P_EXACT}}": _fmt_acc(p_exact, "p_value_exact"),
            "{{S2_BOTH_CORRECT_COUNT}}": str(conc10["both_correct_count"]),
            "{{S2_SINGLE_ONLY_CORRECT}}": str(conc10["single_only_correct_count"]),
            "{{S2_CONTEXT_ONLY_CORRECT}}": str(conc10["contextual_only_correct_count"]),
            "{{S2_BOTH_INCORRECT_COUNT}}": str(conc10["both_incorrect_count"]),
        }
    )

    return slots


def generate_fixture_markdown_preview(
    slots: dict[str, Any],
    output_path: Path,
) -> None:
    """Write private fixture preview document with populated values and prominent disclaimer."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# [FIXTURE PREVIEW] Presentation Deck Numeric Slots Preview",
        "",
        f"> [!WARNING] {DISCLAIMER_TEXT}",
        "> This preview is automatically compiled from synthetic diagnostic unit test fixtures.",
        "> It does NOT represent canonical empirical research outcomes or live study findings.",
        "> Execution mode: `mock_fixture` | `fixture_only: true`.",
        "",
        "## 1. Metadata & Safety Invariants",
        "- **Provenance Status**: `diagnostic_fixture`",
        f"- **Disclaimer**: `{DISCLAIMER_TEXT}`",
        f"- **Total Placeholders Extracted**: {len(slots) - 1}",
        "",
        "## 2. Populated Slot Values (by Presentation Slide)",
        "",
        "### Slide 6: Dataset & Views Topology",
        f"- Manifest Path: `{slots.get('{{S2_MANIFEST_PATH}}')}`",
        f"- Total TEST Views: `{slots.get('{{S2_TOTAL_TEST_VIEWS}}')}`",
        f"- Scorable Views: `{slots.get('{{S2_SCORABLE_VIEWS}}')}`",
        f"- Complete Scorable Pairs: `{slots.get('{{S2_COMPLETE_SCORABLE_PAIRS}}')}`",
        f"- Contextual-Only Pairs: `{slots.get('{{S2_CONTEXTUAL_ONLY_PAIRS}}')}`",
        f"- Neither Mapped Pairs: `{slots.get('{{S2_NEITHER_MAPPED_PAIRS}}')}`",
        f"- Distinct Eligible Clusters: `{slots.get('{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}')}`",
        "",
        "### Slide 7: RQ1 Attribution Performance",
        f"- Accuracy (No-RAG): `{slots.get('{{S2_ACC_E2E_NO_RAG}}')}`",
        f"- Accuracy (RAG k=10): `{slots.get('{{S2_ACC_E2E_RAG_K10}}')}`",
        f"- Macro-F1 (No-RAG): `{slots.get('{{S2_MACRO_F1_NO_RAG}}')}`",
        f"- Macro-F1 (RAG k=10): `{slots.get('{{S2_MACRO_F1_RAG_K10}}')}`",
        (
            f"- Best Condition: `{slots.get('{{S2_BEST_RAG_CONDITION}}')}` "
            f"(Delta: `{slots.get('{{S2_BEST_RAG_ACC_DELTA}}')}`)"
        ),
        "",
        "### Slide 8: RQ2 Error Decomposition",
        (
            f"- Recall@10: `{slots.get('{{S2_RECALL_AT_K}}')}` | "
            f"Hit@10: `{slots.get('{{S2_HIT_RATE_AT_K}}')}`"
        ),
        f"- Retrieval Miss Rate: `{slots.get('{{S2_RETRIEVAL_MISS_RATE_K10}}')}`",
        f"- Provider Failure Rate: `{slots.get('{{S2_PROVIDER_FAIL_RATE_K10}}')}`",
        f"- Parse Failure Rate: `{slots.get('{{S2_PARSE_FAIL_RATE_K10}}')}`",
        f"- Invalid ID Rate: `{slots.get('{{S2_INVALID_ATTACK_ID_RATE_K10}}')}`",
        f"- Wrong Classification Rate: `{slots.get('{{S2_WRONG_CLASS_RATE_K10}}')}`",
        f"- Overlap Miss & Wrong: `{slots.get('{{S2_OVERLAP_MISS_AND_WRONG_K10}}')}`",
        f"- P(Correct | Retrieved): `{slots.get('{{S2_P_CORRECT_GIVEN_RETRIEVED}}')}`",
        f"- P(Correct | Absent): `{slots.get('{{S2_P_CORRECT_GIVEN_ABSENT}}')}`",
        "",
        "### Slide 9: RQ3 Resource Tradeoffs & Costs",
        (
            f"- Median Latency (No-RAG vs k=10): `{slots.get('{{S2_MEDIAN_LAT_NO_RAG_SEC}}')}` s "
            f"vs `{slots.get('{{S2_MEDIAN_LAT_K10_SEC}}')}` s"
        ),
        (
            f"- Mean Prompt Tokens (No-RAG vs k=10): "
            f"`{slots.get('{{S2_MEAN_PROMPT_TOK_NO_RAG}}')}` vs "
            f"`{slots.get('{{S2_MEAN_PROMPT_TOK_K10}}')}`"
        ),
        (
            f"- Cost per Logical Request (No-RAG vs k=10): "
            f"`${slots.get('{{S2_COST_LOGICAL_REQ_NO_RAG}}')}` vs "
            f"`${slots.get('{{S2_COST_LOGICAL_REQ_K10}}')}`"
        ),
        (
            f"- Whole Study Accounting: Budget `${slots.get('{{S2_TOTAL_STUDY_BUDGET_USD}}')}` | "
            f"Spend `${slots.get('{{S2_CANONICAL_TOTAL_USD}}')}` | "
            f"Remaining `${slots.get('{{S2_NET_REMAINING_USD}}')}`"
        ),
        "",
        "### Slide 10: View Diagnostics & Paired Analysis",
        (
            f"- Marginal Single Acc: `{slots.get('{{S2_SINGLE_VIEW_ACC_E2E}}')}` | "
            f"Marginal Context Acc: `{slots.get('{{S2_CONTEXT_VIEW_ACC_E2E}}')}`"
        ),
        (
            f"- Paired Single Acc: `{slots.get('{{S2_PAIRED_SINGLE_ACC}}')}` | "
            f"Paired Context Acc: `{slots.get('{{S2_PAIRED_CONTEXT_ACC}}')}` "
            f"(Delta: `{slots.get('{{S2_PAIRED_DELTA_PP}}')}` pp)"
        ),
        (
            f"- Pair Concordance: Both Correct: `{slots.get('{{S2_BOTH_CORRECT_COUNT}}')}`, "
            f"Both Incorrect: `{slots.get('{{S2_BOTH_INCORRECT_COUNT}}')}`"
        ),
        (
            f"- McNemar Exploratory Test: p_asympt=`{slots.get('{{S2_MCNEMAR_P_ASYMPT}}')}`, "
            f"p_exact=`{slots.get('{{S2_MCNEMAR_P_EXACT}}')}`"
        ),
        "",
        "---",
        f"*End of Private Diagnostic Fixture Preview - `{DISCLAIMER_TEXT}`*",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Populate presentation numeric slots against diagnostic fixtures only."
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to fixture directory containing rq_analysis.json and native JSON fixtures.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Path to write populated Markdown preview.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Path to write populated slot dictionary as JSON for downstream tooling.",
    )
    args = parser.parse_args()

    try:
        slots = extract_fixture_slots(args.fixture_dir)
        generate_fixture_markdown_preview(slots, args.output_md)
        args.output_json.write_text(json.dumps(slots, indent=2), encoding="utf-8")
        print(f"[+] Successfully extracted {len(slots) - 1} numeric slots from fixtures.")
        print(f"[+] Markdown preview written to: {args.output_md}")
        print(f"[+] JSON slot mapping written to: {args.output_json}")
        print(f"[+] Private labeling certified: {DISCLAIMER_TEXT}")
        return 0
    except Exception as exc:
        print(f"[-] Error populating presentation fixtures: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
