"""Comprehensive Offline Analysis for Research Questions RQ1, RQ2, and RQ3.

Computes:
- RQ1: Controlled comparison of No-RAG vs RAG (k=1, 3, 5, 10) on exact technique attribution,
  with delta metrics, relative gains, McNemar significance tests, and paired bootstrap CIs.
- RQ2: Retrieval vs. Generation error decomposition, measuring retrieval Recall@k,
  downstream generation accuracy conditioned on retrieval success, and failure source attribution.
- RQ3: Retrieval depth ablation (k in 1, 3, 5, 10 vs 0), latency, token expenditure, monetary
  costs (pricing-v1 tariffs), Pareto trade-offs, and paired Single-View vs Contextual-View
  diagnostics.

Secondary statistical tests (McNemar test, paired bootstrap CIs) do not alter headline protocol.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Support direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.experiment_metrics import (
    CONDITIONS,
    EvaluationInputs,
    canonical_json_bytes,
    compute_condition_metrics,
    compute_failure_decomposition,
    compute_retrieval_conditional_metrics,
    load_evaluation_inputs,
)
from src.experiment.authorization import ScientificProtocolApproval
from src.experiment.monetary_ledger import (
    calculate_attempt_token_cost,
    load_pricing_config,
)

ANALYSIS_TOOL_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Statistical Testing Helpers
# ---------------------------------------------------------------------------


def compute_mcnemar_test(
    y_baseline: Sequence[bool],
    y_treatment: Sequence[bool],
) -> dict[str, Any]:
    """Compute McNemar test on paired binary classification outcomes.

    Contingency table:
      a: both correct (1, 1)
      b: treatment correct, baseline incorrect (1, 0) -> treatment win (discordant)
      c: treatment incorrect, baseline correct (0, 1) -> baseline win (discordant)
      d: both incorrect (0, 0)

    Calculates:
      - Chi-squared statistic with Edwards continuity correction:
        chi2 = (|b - c| - 1)^2 / (b + c) if (b + c) > 0 and |b - c| >= 1 else 0.0
      - Asymptotic p-value from chi2(df=1)
      - Exact two-sided binomial p-value for B(b + c, 0.5)
    """
    if len(y_baseline) != len(y_treatment):
        raise ValueError(
            f"Length mismatch for paired McNemar test: {len(y_baseline)} vs {len(y_treatment)}"
        )

    n = len(y_baseline)
    a = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if y_b and y_t)
    b = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if not y_b and y_t)
    c = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if y_b and not y_t)
    d = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if not y_b and not y_t)

    discordant = b + c
    if discordant == 0:
        chi2_stat = 0.0
        p_value_chi2 = 1.0
        p_value_exact = 1.0
    else:
        diff = abs(b - c)
        chi2_stat = ((diff - 1.0) ** 2) / discordant if diff >= 1.0 else 0.0

        try:
            from scipy.stats import binomtest, chi2

            p_value_chi2 = float(chi2.sf(chi2_stat, df=1))
            k_min = min(b, c)
            p_value_exact = float(binomtest(k_min, discordant, 0.5).pvalue)
        except ImportError:
            p_value_chi2 = float(math.erfc(math.sqrt(chi2_stat / 2.0)))
            k_min = min(b, c)
            cum_prob = sum(
                math.comb(discordant, i) * (0.5**discordant) for i in range(k_min + 1)
            )
            p_value_exact = min(1.0, 2.0 * cum_prob)

    odds_ratio = (b / c) if c > 0 else (float("inf") if b > 0 else 1.0)

    return {
        "paired_samples": n,
        "contingency_table": {
            "both_correct_a": a,
            "treatment_win_b": b,
            "baseline_win_c": c,
            "both_incorrect_d": d,
            "total_discordant": discordant,
        },
        "chi2_statistic": chi2_stat,
        "p_value_chi2": p_value_chi2,
        "p_value_exact": p_value_exact,
        "odds_ratio": odds_ratio,
        "significant_at_05": p_value_exact < 0.05,
        "significant_at_01": p_value_exact < 0.01,
    }


def compute_paired_bootstrap_ci(
    scores_treatment: Sequence[float],
    scores_baseline: Sequence[float],
    *,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical percentile bootstrap CI for paired delta (Treatment - Baseline)."""
    if len(scores_treatment) != len(scores_baseline):
        raise ValueError("Paired bootstrap requires equal sample counts")

    n = len(scores_treatment)
    if n == 0:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean_delta": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
        }

    arr_treat = np.array(scores_treatment, dtype=np.float64)
    arr_base = np.array(scores_baseline, dtype=np.float64)

    rng = np.random.default_rng(seed)
    deltas = np.empty(num_samples, dtype=np.float64)

    for i in range(num_samples):
        indices = rng.integers(0, n, size=n)
        deltas[i] = np.mean(arr_treat[indices]) - np.mean(arr_base[indices])

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_lower = float(np.percentile(deltas, lower_pct))
    ci_upper = float(np.percentile(deltas, upper_pct))
    mean_delta = float(np.mean(deltas))
    std_error = float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0

    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "mean_delta": mean_delta,
        "std_error": std_error,
        "num_samples": num_samples,
        "alpha": alpha,
    }


def compute_single_bootstrap_ci(
    scores: Sequence[float],
    *,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical percentile bootstrap CI for a single metric series."""
    n = len(scores)
    if n == 0:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
        }

    arr = np.array(scores, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = np.empty(num_samples, dtype=np.float64)

    for i in range(num_samples):
        indices = rng.integers(0, n, size=n)
        means[i] = np.mean(arr[indices])

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    ci_lower = float(np.percentile(means, lower_pct))
    ci_upper = float(np.percentile(means, upper_pct))
    est_mean = float(np.mean(means))
    std_error = float(np.std(means, ddof=1)) if num_samples > 1 else 0.0

    return {
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
        "mean": est_mean,
        "std_error": std_error,
        "num_samples": num_samples,
        "alpha": alpha,
    }


def compute_macro_f1_bootstrap_ci(
    records_treat: Sequence[Mapping[str, Any]],
    records_base: Sequence[Mapping[str, Any]],
    ground_truth: Mapping[str, tuple[str, ...]],
    universe_size: int = 474,
    *,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute bootstrap CI for paired difference in Macro-F1 across 474 universe."""
    n = len(records_treat)
    if n == 0 or len(records_base) != n:
        return {"ci_lower": None, "ci_upper": None, "mean_delta": None}

    treat_pairs = [
        (
            r["sample_id"],
            r.get("parsed_technique_ids", [None])[0] if r["parse_status"] == "VALID" else None,
            set(ground_truth.get(r["sample_id"], ())),
        )
        for r in records_treat
    ]
    base_pairs = [
        (
            r["sample_id"],
            r.get("parsed_technique_ids", [None])[0] if r["parse_status"] == "VALID" else None,
            set(ground_truth.get(r["sample_id"], ())),
        )
        for r in records_base
    ]

    def _calc_fast_macro_f1(pairs_subset: Sequence[tuple[str, Optional[str], set[str]]]) -> float:
        active_classes: set[str] = set()
        for _, pred, gt in pairs_subset:
            if pred:
                active_classes.add(pred)
            active_classes.update(gt)

        if not active_classes or universe_size <= 0:
            return 0.0

        f1_sum = 0.0
        for tid in active_classes:
            tp = sum(1 for _, pred, gt in pairs_subset if pred == tid and tid in gt)
            fp = sum(1 for _, pred, gt in pairs_subset if pred == tid and tid not in gt)
            fn = sum(1 for _, pred, gt in pairs_subset if tid in gt and pred != tid)

            if tp + fp == 0 and tp + fn == 0:
                continue
            prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            f1_sum += f1

        return f1_sum / universe_size

    rng = np.random.default_rng(seed)
    deltas = np.empty(num_samples, dtype=np.float64)

    for i in range(num_samples):
        indices = rng.integers(0, n, size=n)
        sub_t = [treat_pairs[idx] for idx in indices]
        sub_b = [base_pairs[idx] for idx in indices]
        f1_t = _calc_fast_macro_f1(sub_t)
        f1_b = _calc_fast_macro_f1(sub_b)
        deltas[i] = f1_t - f1_b

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(deltas, lower_pct)),
        "ci_upper": float(np.percentile(deltas, upper_pct)),
        "mean_delta": float(np.mean(deltas)),
        "std_error": float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
    }


# ---------------------------------------------------------------------------
# RQ1 Analysis: Controlled Comparison (No-RAG vs RAG)
# ---------------------------------------------------------------------------


def compute_rq1(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
    *,
    bootstrap_samples: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute RQ1: Controlled comparison of No-RAG vs RAG (k=1,3,5,10) on technique attribution.

    Evaluates:
      - End-to-end accuracy, Valid-output accuracy, Macro-F1 across 474-class universe.
      - Delta vs No-RAG baseline (both absolute and relative percentage gain).
      - Statistical significance via paired McNemar test and paired bootstrap CIs.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    scorable_by_cond: dict[str, list[dict[str, Any]]] = {}
    correctness_by_cond_sample: dict[str, dict[str, bool]] = {}

    for cond in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = []
        sample_correctness = {}

        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")

            is_scorable = False
            if status == "ambiguous":
                is_scorable = protocol.d2c_ambiguous_ground_truth != "EXCLUDE"
            elif status == "unmapped" or not gt:
                is_scorable = protocol.d2b_empty_ground_truth == "TREAT_AS_NEGATIVE"
            else:
                is_scorable = True

            if is_scorable:
                scorable_records.append(r)
                is_correct = (
                    r["parse_status"] == "VALID"
                    and bool(r.get("parsed_technique_ids"))
                    and r["parsed_technique_ids"][0] in set(gt)
                )
                sample_correctness[sid] = is_correct

        scorable_by_cond[cond] = scorable_records
        correctness_by_cond_sample[cond] = sample_correctness

    base_cond = "no_rag"
    base_metrics = condition_metrics[base_cond]
    base_correctness = correctness_by_cond_sample[base_cond]
    common_scorable_sids = sorted(base_correctness.keys())

    base_bools = [base_correctness[sid] for sid in common_scorable_sids]
    base_scores = [1.0 if b else 0.0 for b in base_bools]

    universe_size = (
        len(inputs.corpus_ids)
        if inputs.corpus_ids
        else (len(inputs.registry) if inputs.registry else 474)
    )

    by_condition_rq1 = {}

    for cond in CONDITIONS:
        m = condition_metrics[cond]
        cond_bools = [correctness_by_cond_sample[cond][sid] for sid in common_scorable_sids]
        cond_scores = [1.0 if b else 0.0 for b in cond_bools]

        acc_ci = compute_single_bootstrap_ci(
            cond_scores, num_samples=bootstrap_samples, seed=seed
        )

        cond_result: dict[str, Any] = {
            "condition": cond,
            "scorable_sample_count": m["scorable_sample_count"],
            "accuracy_end_to_end": m["accuracy_end_to_end"],
            "accuracy_valid_outputs": m["accuracy_valid_outputs"],
            "macro_f1": m["macro_f1"],
            "correct_count": m["correct_count"],
            "accuracy_e2e_ci_95": [acc_ci["ci_lower"], acc_ci["ci_upper"]],
        }

        if cond == base_cond:
            cond_result["is_baseline"] = True
            cond_result["delta_vs_baseline"] = None
        else:
            delta_acc_e2e = (
                m["accuracy_end_to_end"] - base_metrics["accuracy_end_to_end"]
                if m["accuracy_end_to_end"] is not None
                and base_metrics["accuracy_end_to_end"] is not None
                else None
            )
            delta_acc_valid = (
                m["accuracy_valid_outputs"] - base_metrics["accuracy_valid_outputs"]
                if m["accuracy_valid_outputs"] is not None
                and base_metrics["accuracy_valid_outputs"] is not None
                else None
            )
            delta_f1 = (
                m["macro_f1"] - base_metrics["macro_f1"]
                if m["macro_f1"] is not None and base_metrics["macro_f1"] is not None
                else None
            )

            rel_gain_acc = (
                (delta_acc_e2e / base_metrics["accuracy_end_to_end"] * 100.0)
                if (delta_acc_e2e is not None and base_metrics["accuracy_end_to_end"])
                else None
            )
            rel_gain_f1 = (
                (delta_f1 / base_metrics["macro_f1"] * 100.0)
                if (delta_f1 is not None and base_metrics["macro_f1"])
                else None
            )

            mcnemar = compute_mcnemar_test(base_bools, cond_bools)
            paired_acc_ci = compute_paired_bootstrap_ci(
                cond_scores, base_scores, num_samples=bootstrap_samples, seed=seed
            )
            paired_f1_ci = compute_macro_f1_bootstrap_ci(
                scorable_by_cond[cond],
                scorable_by_cond[base_cond],
                inputs.ground_truth,
                universe_size=universe_size,
                num_samples=bootstrap_samples,
                seed=seed,
            )

            cond_result["is_baseline"] = False
            cond_result["delta_vs_baseline"] = {
                "delta_accuracy_end_to_end": delta_acc_e2e,
                "delta_accuracy_valid_outputs": delta_acc_valid,
                "delta_macro_f1": delta_f1,
                "relative_gain_accuracy_e2e_pct": rel_gain_acc,
                "relative_gain_macro_f1_pct": rel_gain_f1,
                "delta_accuracy_e2e_ci_95": [
                    paired_acc_ci["ci_lower"],
                    paired_acc_ci["ci_upper"],
                ],
                "delta_macro_f1_ci_95": [paired_f1_ci["ci_lower"], paired_f1_ci["ci_upper"]],
                "mcnemar_test": mcnemar,
            }

        by_condition_rq1[cond] = cond_result

    rag_conditions = [c for c in CONDITIONS if c != base_cond]
    best_cond = max(
        rag_conditions,
        key=lambda c: by_condition_rq1[c]["accuracy_end_to_end"] or -1.0,
    )

    return {
        "schema_version": "1.0.0",
        "research_question": (
            "RQ1: Controlled comparison of No-RAG vs RAG on exact technique attribution"
        ),
        "baseline_condition": base_cond,
        "best_rag_condition": best_cond,
        "best_rag_accuracy_delta": by_condition_rq1[best_cond]["delta_vs_baseline"][
            "delta_accuracy_end_to_end"
        ],
        "best_rag_macro_f1_delta": by_condition_rq1[best_cond]["delta_vs_baseline"][
            "delta_macro_f1"
        ],
        "by_condition": by_condition_rq1,
    }


# ---------------------------------------------------------------------------
# RQ2 Analysis: Retrieval vs Generation Error Decomposition
# ---------------------------------------------------------------------------


def compute_rq2(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    retrieval_cond_metrics: Optional[dict[str, Any]] = None,
    failure_decomp_metrics: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compute RQ2: Retrieval vs. Generation error decomposition.

    Evaluates:
      - Upstream retrieval quality (Hit@k, Macro-Recall@k).
      - Downstream generation accuracy conditioned on retrieval success.
      - Error source decomposition: retrieval miss vs generation misattribution vs system error.
    """
    if retrieval_cond_metrics is None:
        retrieval_cond_metrics = compute_retrieval_conditional_metrics(inputs, protocol)
    if failure_decomp_metrics is None:
        failure_decomp_metrics = compute_failure_decomposition(inputs, protocol)

    by_condition_rq2 = {}

    for cond in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = []

        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "mapped" and gt:
                scorable_records.append(r)

        total_scorable = len(scorable_records)
        is_rag = cond != "no_rag"

        if not is_rag:
            failures = [
                r
                for r in scorable_records
                if not (
                    r["parse_status"] == "VALID"
                    and bool(r.get("parsed_technique_ids"))
                    and r["parsed_technique_ids"][0]
                    in set(inputs.ground_truth.get(r["sample_id"], ()))
                )
            ]
            correct_count = total_scorable - len(failures)
            by_condition_rq2[cond] = {
                "condition": cond,
                "retrieval_k": 0,
                "total_scorable_samples": total_scorable,
                "correct_count": correct_count,
                "total_failures": len(failures),
                "retrieval_hit_rate": 0.0,
                "macro_recall": 0.0,
                "P_correct_given_retrieval_success": None,
                "P_correct_given_retrieval_failure": (
                    (correct_count / total_scorable) if total_scorable > 0 else None
                ),
                "error_decomposition": {
                    "retrieval_miss_failure_count": 0,
                    "retrieval_miss_failure_pct": 0.0,
                    "generation_misattribution_count": len(
                        [r for r in failures if r["parse_status"] == "VALID"]
                    ),
                    "system_or_parse_failure_count": len(
                        [r for r in failures if r["parse_status"] != "VALID"]
                    ),
                },
            }
            continue

        k = int(cond[5:])
        ret_cond = retrieval_cond_metrics["by_condition"].get(cond, {})
        fail_decomp = failure_decomp_metrics["by_condition"].get(cond, {})

        hits, recalls = [], []
        retrieval_miss_records = []
        retrieval_success_records = []

        for r in scorable_records:
            gt = set(inputs.ground_truth.get(r["sample_id"], ()))
            retrieved = {c["technique_id"] for c in r.get("retrieved_candidates", [])}
            found = retrieved & gt
            has_hit = bool(found)
            hits.append(int(has_hit))
            recalls.append(len(found) / len(gt) if gt else 0.0)

            if has_hit:
                retrieval_success_records.append(r)
            else:
                retrieval_miss_records.append(r)

        hit_rate = (sum(hits) / total_scorable) if total_scorable > 0 else None
        macro_recall = (sum(recalls) / total_scorable) if total_scorable > 0 else None

        def is_correct(rec):
            return (
                rec["parse_status"] == "VALID"
                and bool(rec.get("parsed_technique_ids"))
                and rec["parsed_technique_ids"][0]
                in set(inputs.ground_truth.get(rec["sample_id"], ()))
            )

        correct_count = sum(1 for r in scorable_records if is_correct(r))
        failed_records = [r for r in scorable_records if not is_correct(r)]
        total_failures = len(failed_records)

        # Disjoint partition of failures into upstream retrieval vs downstream generation
        retrieval_miss_errors = [r for r in failed_records if r in retrieval_miss_records]
        gen_misattribution_errors = [
            r
            for r in failed_records
            if r in retrieval_success_records and r["parse_status"] == "VALID"
        ]
        system_or_parse_errors = [
            r
            for r in failed_records
            if r in retrieval_success_records and r["parse_status"] != "VALID"
        ]

        ret_miss_count = len(retrieval_miss_errors)
        gen_misatt_count = len(gen_misattribution_errors)
        sys_parse_count = len(system_or_parse_errors)

        by_condition_rq2[cond] = {
            "condition": cond,
            "retrieval_k": k,
            "total_scorable_samples": total_scorable,
            "correct_count": correct_count,
            "total_failures": total_failures,
            "retrieval_hit_rate": hit_rate,
            "macro_recall": macro_recall,
            "retrieval_success_count": len(retrieval_success_records),
            "retrieval_miss_count": len(retrieval_miss_records),
            "P_correct_given_retrieval_success": ret_cond.get(
                "P_correct_given_retrieval_success"
            ),
            "P_correct_given_retrieval_failure": ret_cond.get(
                "P_correct_given_retrieval_failure"
            ),
            "retrieval_success_correct_count": ret_cond.get("retrieval_success_correct_count"),
            "retrieval_failure_correct_count": ret_cond.get("retrieval_failure_correct_count"),
            "error_decomposition": {
                "retrieval_miss_error_count": ret_miss_count,
                "retrieval_miss_fraction_of_failures": (
                    (ret_miss_count / total_failures) if total_failures > 0 else 0.0
                ),
                "generation_misattribution_count": gen_misatt_count,
                "generation_misattribution_fraction_of_failures": (
                    (gen_misatt_count / total_failures) if total_failures > 0 else 0.0
                ),
                "system_or_parse_error_count": sys_parse_count,
                "system_or_parse_fraction_of_failures": (
                    (sys_parse_count / total_failures) if total_failures > 0 else 0.0
                ),
            },
            "independent_diagnostic_axes": {
                "retrieval_miss_rate": fail_decomp.get("retrieval_miss_rate"),
                "provider_failure_rate": fail_decomp.get("provider_failure_rate"),
                "parse_failure_rate": fail_decomp.get("parse_failure_rate"),
                "invalid_attack_id_rate": fail_decomp.get("invalid_attack_id_rate"),
                "valid_but_wrong_classification_rate": fail_decomp.get(
                    "valid_but_wrong_classification_rate"
                ),
                "overlap_retrieval_miss_and_wrong": fail_decomp.get(
                    "overlap_retrieval_miss_and_wrong_classification"
                ),
            },
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ2: Retrieval vs. Generation error decomposition",
        "by_condition": by_condition_rq2,
    }


# ---------------------------------------------------------------------------
# RQ3 Analysis: k / Latency / Cost Trade-offs & View Diagnostics
# ---------------------------------------------------------------------------


def compute_rq3(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
    pricing_config: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compute RQ3: Retrieval depth ablation (k in 1,3,5,10 vs 0), latency, tokens, and views.

    Evaluates:
      - Performance curve across k: Accuracy, Macro-F1, Recall@k.
      - Latency distribution: Mean, median, p95, sum (ms).
      - Token usage: Mean prompt/completion/total tokens, sum.
      - Financial cost calculation: Total cost ($), cost/query, cost/correct attribution.
      - Paired Single-View vs Contextual-View diagnostics.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    if pricing_config is None:
        try:
            pricing_config, _ = load_pricing_config()
        except Exception:
            pricing_config = {}

    tradeoff_by_condition = {}
    base_cost_usd = 0.0

    for cond in CONDITIONS:
        k = 0 if cond == "no_rag" else int(cond[5:])
        m = condition_metrics[cond]
        rows = [r for r in inputs.records if r["condition"] == cond]

        latencies = [r["latency_ms"] for r in rows if r.get("latency_ms") is not None]
        mean_lat = float(np.mean(latencies)) if latencies else None
        median_lat = float(np.median(latencies)) if latencies else None
        p95_lat = float(np.percentile(latencies, 95)) if latencies else None
        sum_lat = float(np.sum(latencies)) if latencies else None

        prompt_tokens = [r["prompt_tokens"] for r in rows if r.get("prompt_tokens") is not None]
        comp_tokens = [
            r["completion_tokens"] for r in rows if r.get("completion_tokens") is not None
        ]
        total_tokens = [r["total_tokens"] for r in rows if r.get("total_tokens") is not None]

        mean_prompt_tok = float(np.mean(prompt_tokens)) if prompt_tokens else None
        mean_comp_tok = float(np.mean(comp_tokens)) if comp_tokens else None
        mean_tot_tok = float(np.mean(total_tokens)) if total_tokens else None
        sum_prompt_tok = sum(prompt_tokens)
        sum_comp_tok = sum(comp_tokens)
        sum_tot_tok = sum(total_tokens)

        total_cost = Decimal("0.0")
        if pricing_config:
            for r in rows:
                p_tok = r.get("prompt_tokens")
                c_tok = r.get("completion_tokens")
                if p_tok is not None and c_tok is not None:
                    try:
                        cost = calculate_attempt_token_cost(p_tok, c_tok, pricing_config)
                        total_cost += cost
                    except Exception:
                        pass
        total_cost_usd = float(total_cost)
        if cond == "no_rag":
            base_cost_usd = total_cost_usd

        scorable_count = m["scorable_sample_count"]
        correct_count = m["correct_count"]

        cost_per_query = (total_cost_usd / scorable_count) if scorable_count > 0 else None
        cost_per_correct = (total_cost_usd / correct_count) if correct_count > 0 else None

        tradeoff_by_condition[cond] = {
            "condition": cond,
            "retrieval_k": k,
            "accuracy_end_to_end": m["accuracy_end_to_end"],
            "accuracy_valid_outputs": m["accuracy_valid_outputs"],
            "macro_f1": m["macro_f1"],
            "latency_ms": {
                "mean": mean_lat,
                "median": median_lat,
                "p95": p95_lat,
                "sum": sum_lat,
            },
            "tokens": {
                "mean_prompt_tokens": mean_prompt_tok,
                "mean_completion_tokens": mean_comp_tok,
                "mean_total_tokens": mean_tot_tok,
                "sum_prompt_tokens": sum_prompt_tok,
                "sum_completion_tokens": sum_comp_tok,
                "sum_total_tokens": sum_tot_tok,
            },
            "financial_cost_usd": {
                "total_cost_usd": total_cost_usd,
                "cost_per_scorable_query_usd": cost_per_query,
                "cost_per_correct_attribution_usd": cost_per_correct,
                "marginal_cost_vs_baseline_usd": total_cost_usd - base_cost_usd,
            },
        }

    # Paired Single-View vs Contextual-View Diagnostics
    view_diagnostics_by_condition = {}

    for cond in CONDITIONS:
        rows = [r for r in inputs.records if r["condition"] == cond]

        single_records = []
        contextual_records = []
        pair_to_views: dict[str, dict[str, Any]] = defaultdict(dict)

        for r in rows:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status != "mapped" or not gt:
                continue

            v_type = r.get("view_type")
            p_id = r.get("pair_id")

            is_correct = (
                r["parse_status"] == "VALID"
                and bool(r.get("parsed_technique_ids"))
                and r["parsed_technique_ids"][0] in set(gt)
            )

            if v_type == "single":
                single_records.append((sid, is_correct))
            elif v_type == "contextual":
                contextual_records.append((sid, is_correct))

            if p_id and v_type:
                pair_to_views[p_id][v_type] = {"sample_id": sid, "correct": is_correct}

        single_acc = (
            sum(1 for _, c in single_records if c) / len(single_records)
            if single_records
            else None
        )
        contextual_acc = (
            sum(1 for _, c in contextual_records if c) / len(contextual_records)
            if contextual_records
            else None
        )
        view_delta = (
            contextual_acc - single_acc
            if contextual_acc is not None and single_acc is not None
            else None
        )

        complete_pairs = [p for p in pair_to_views.values() if "single" in p and "contextual" in p]
        both_corr = sum(
            1 for p in complete_pairs if p["single"]["correct"] and p["contextual"]["correct"]
        )
        single_only = sum(
            1 for p in complete_pairs if p["single"]["correct"] and not p["contextual"]["correct"]
        )
        contextual_only = sum(
            1 for p in complete_pairs if not p["single"]["correct"] and p["contextual"]["correct"]
        )
        both_incorr = sum(
            1
            for p in complete_pairs
            if not p["single"]["correct"] and not p["contextual"]["correct"]
        )

        n_pairs = len(complete_pairs)
        single_bools = [p["single"]["correct"] for p in complete_pairs]
        contextual_bools = [p["contextual"]["correct"] for p in complete_pairs]
        mcnemar_views = (
            compute_mcnemar_test(single_bools, contextual_bools) if complete_pairs else None
        )

        view_diagnostics_by_condition[cond] = {
            "condition": cond,
            "single_view_sample_count": len(single_records),
            "contextual_view_sample_count": len(contextual_records),
            "single_view_accuracy_e2e": single_acc,
            "contextual_view_accuracy_e2e": contextual_acc,
            "view_accuracy_delta": view_delta,
            "paired_complete_pairs_count": n_pairs,
            "pair_concordance": {
                "both_correct_count": both_corr,
                "both_correct_pct": (both_corr / n_pairs * 100.0) if n_pairs > 0 else 0.0,
                "single_only_correct_count": single_only,
                "single_only_correct_pct": (single_only / n_pairs * 100.0) if n_pairs > 0 else 0.0,
                "contextual_only_correct_count": contextual_only,
                "contextual_only_correct_pct": (
                    (contextual_only / n_pairs * 100.0) if n_pairs > 0 else 0.0
                ),
                "both_incorrect_count": both_incorr,
                "both_incorrect_pct": (both_incorr / n_pairs * 100.0) if n_pairs > 0 else 0.0,
            },
            "mcnemar_test_views": mcnemar_views,
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ3: Retrieval depth & efficiency ablation and view diagnostics",
        "tradeoffs_by_condition": tradeoff_by_condition,
        "view_diagnostics": view_diagnostics_by_condition,
    }


# ---------------------------------------------------------------------------
# Comprehensive Full Study Pipeline
# ---------------------------------------------------------------------------


def run_rq_analysis(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    *,
    pricing_config: Optional[dict[str, Any]] = None,
    bootstrap_samples: int = 1000,
    seed: int = 42,
    output_dir: Optional[Path | str] = None,
) -> dict[str, Any]:
    """Execute complete RQ1, RQ2, and RQ3 analyses and optionally write reports."""
    cond_metrics = {
        c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
    }
    ret_cond_metrics = compute_retrieval_conditional_metrics(inputs, protocol)
    fail_decomp_metrics = compute_failure_decomposition(inputs, protocol)

    rq1 = compute_rq1(
        inputs,
        protocol,
        cond_metrics,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    rq2 = compute_rq2(inputs, protocol, ret_cond_metrics, fail_decomp_metrics)
    rq3 = compute_rq3(inputs, protocol, cond_metrics, pricing_config=pricing_config)

    overall_summary = {
        "schema_version": "1.0.0",
        "analysis_tool_version": ANALYSIS_TOOL_VERSION,
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "rq1": rq1,
        "rq2": rq2,
        "rq3": rq3,
    }

    if output_dir is not None:
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        json_file = out_path / "rq_analysis.json"
        json_file.write_bytes(canonical_json_bytes(overall_summary) + b"\n")

        md_file = out_path / "rq_analysis_summary.md"
        md_content = generate_rq_markdown_report(overall_summary)
        md_file.write_text(md_content, encoding="utf-8")

    return overall_summary


# ---------------------------------------------------------------------------
# Markdown Report Generation
# ---------------------------------------------------------------------------


def generate_rq_markdown_report(analysis_dict: dict[str, Any]) -> str:
    """Format structured RQ analysis dictionary into publication-grade Markdown."""
    rq1 = analysis_dict.get("rq1", {})
    rq2 = analysis_dict.get("rq2", {})
    rq3 = analysis_dict.get("rq3", {})

    lines = [
        "# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)",
        "",
        f"- **Experiment ID**: `{analysis_dict.get('experiment_id')}`",
        f"- **Manifest SHA-256**: `{analysis_dict.get('manifest_sha256')}`",
        f"- **Protocol SHA-256**: `{analysis_dict.get('protocol_sha256')}`",
        f"- **Generated At**: `{analysis_dict.get('analysis_timestamp')}`",
        "",
        "---",
        "",
        "## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)",
        "",
        "> *To what extent does MITRE ATT&CK-grounded RAG improve technique attribution accuracy?*",
        "| Cond | N | Acc(e2e) | 95% CI | Valid Acc | F1 | d_Acc | d_F1 | McNemar p |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for cond in CONDITIONS:
        row = rq1.get("by_condition", {}).get(cond, {})
        n = row.get("scorable_sample_count", "-")
        acc_v = row.get("accuracy_end_to_end")
        acc = f"{acc_v:.4f}" if acc_v is not None else "-"
        ci = row.get("accuracy_e2e_ci_95", [None, None])
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if (ci and ci[0] is not None) else "-"
        valid_v = row.get("accuracy_valid_outputs")
        valid_acc = f"{valid_v:.4f}" if valid_v is not None else "-"
        f1_v = row.get("macro_f1")
        f1 = f"{f1_v:.4f}" if f1_v is not None else "-"

        if row.get("is_baseline"):
            delta_acc = "Baseline"
            delta_f1 = "Baseline"
            p_val = "-"
        else:
            d = row.get("delta_vs_baseline", {})
            d_acc_val = d.get("delta_accuracy_end_to_end")
            d_f1_val = d.get("delta_macro_f1")
            delta_acc = f"{d_acc_val:+.4f}" if d_acc_val is not None else "-"
            delta_f1 = f"{d_f1_val:+.4f}" if d_f1_val is not None else "-"
            p = d.get("mcnemar_test", {}).get("p_value_exact")
            p_val = f"{p:.4e}" if p is not None else "-"

        lines.append(
            f"| `{cond}` | {n} | {acc} | {ci_str} | {valid_acc} | {f1} | "
            f"{delta_acc} | {delta_f1} | {p_val} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## RQ2: Retrieval vs. Generation Error Decomposition",
        "",
        "> *How does retrieval quality affect final attribution, and where do failures originate?*",
        "",
        "| Condition | k | Recall@k | Hit Rate | P(Corr|Succ) | P(Corr|Fail) | "
        "Ret Miss % | Gen Misatt % | Sys/Parse % |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    for cond in CONDITIONS:
        row = rq2.get("by_condition", {}).get(cond, {})
        k = row.get("retrieval_k", 0)
        rec_v = row.get("macro_recall")
        rec = f"{rec_v:.4f}" if rec_v is not None else "-"
        hit_v = row.get("retrieval_hit_rate")
        hit = f"{hit_v:.4f}" if hit_v is not None else "-"
        p_succ_v = row.get("P_correct_given_retrieval_success")
        p_succ = f"{p_succ_v:.4f}" if p_succ_v is not None else "-"
        p_fail_v = row.get("P_correct_given_retrieval_failure")
        p_fail = f"{p_fail_v:.4f}" if p_fail_v is not None else "-"

        err = row.get("error_decomposition", {})
        ret_err_pct = (
            f"{err['retrieval_miss_fraction_of_failures'] * 100:.1f}%"
            if "retrieval_miss_fraction_of_failures" in err
            else "-"
        )
        gen_err_pct = (
            f"{err['generation_misattribution_fraction_of_failures'] * 100:.1f}%"
            if "generation_misattribution_fraction_of_failures" in err
            else "-"
        )
        sys_err_pct = (
            f"{err['system_or_parse_fraction_of_failures'] * 100:.1f}%"
            if "system_or_parse_fraction_of_failures" in err
            else "-"
        )

        lines.append(
            f"| `{cond}` | {k} | {rec} | {hit} | {p_succ} | {p_fail} | "
            f"{ret_err_pct} | {gen_err_pct} | {sys_err_pct} |"
        )

    lines.extend([
        "",
        "---",
        "",
        "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs",
        "",
        "> *What is the resource trade-off across candidate depths k in {1, 3, 5, 10}?*",
        "",
        "| Condition | k | Mean Latency (ms) | p95 Latency (ms) | Mean Tokens | "
        "Total Cost ($) | Cost / Correct ($) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    tradeoffs = rq3.get("tradeoffs_by_condition", {})
    for cond in CONDITIONS:
        row = tradeoffs.get(cond, {})
        k = row.get("retrieval_k", 0)
        lat = row.get("latency_ms", {})
        mean_l = f"{lat.get('mean', 0.0):.1f}" if lat.get("mean") is not None else "-"
        p95_l = f"{lat.get('p95', 0.0):.1f}" if lat.get("p95") is not None else "-"

        tok = row.get("tokens", {})
        mean_t = (
            f"{tok.get('mean_total_tokens', 0.0):.1f}"
            if tok.get("mean_total_tokens") is not None
            else "-"
        )

        cost = row.get("financial_cost_usd", {})
        tot_c = (
            f"${cost.get('total_cost_usd', 0.0):.5f}"
            if cost.get("total_cost_usd") is not None
            else "-"
        )
        corr_c = (
            f"${cost.get('cost_per_correct_attribution_usd', 0.0):.5f}"
            if cost.get("cost_per_correct_attribution_usd") is not None
            else "-"
        )

        lines.append(
            f"| `{cond}` | {k} | {mean_l} | {p95_l} | {mean_t} | {tot_c} | {corr_c} |"
        )

    lines.extend([
        "",
        "### Paired View Diagnostics (Single-View vs Contextual-View)",
        "",
        "| Condition | Single Acc | Contextual Acc | Delta (Ctx - Sgl) | "
        "Concordant Both Corr | Ctx Win | Sgl Win |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ])

    views = rq3.get("view_diagnostics", {})
    for cond in CONDITIONS:
        row = views.get(cond, {})
        s_acc = (
            f"{row.get('single_view_accuracy_e2e', 0.0):.4f}"
            if row.get("single_view_accuracy_e2e") is not None
            else "-"
        )
        c_acc = (
            f"{row.get('contextual_view_accuracy_e2e', 0.0):.4f}"
            if row.get("contextual_view_accuracy_e2e") is not None
            else "-"
        )
        d_val = row.get("view_accuracy_delta")
        d_str = f"{d_val:+.4f}" if d_val is not None else "-"

        p_conc = row.get("pair_concordance", {})
        both_c = p_conc.get("both_correct_count", "-")
        ctx_win = p_conc.get("contextual_only_correct_count", "-")
        sgl_win = p_conc.get("single_only_correct_count", "-")

        lines.append(
            f"| `{cond}` | {s_acc} | {c_acc} | {d_str} | {both_c} | {ctx_win} | {sgl_win} |"
        )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline Research Question Evaluator (RQ1, RQ2, RQ3)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to run manifest.json",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Directory containing run manifest.json and condition prediction files",
    )
    parser.add_argument(
        "--protocol-file",
        type=Path,
        default=Path("config/experiment_protocol_v1.json"),
        help="Path to frozen experiment_protocol_v1.json",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/analysis"),
        help="Directory to write rq_analysis.json and rq_analysis_summary.md",
    )
    parser.add_argument(
        "--pricing-file",
        type=Path,
        default=Path("config/pricing_v1.json"),
        help="Path to pricing configuration file",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples for confidence intervals",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible bootstrap sampling",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="Repository root for artifact path resolution (defaults to git repo root)",
    )

    args = parser.parse_args(argv)

    manifest_path = args.manifest
    if manifest_path is None and args.run_dir is not None:
        manifest_path = args.run_dir / "manifest.json"

    if manifest_path is None or not manifest_path.is_file():
        print(f"Error: Manifest file not found at {manifest_path}", file=sys.stderr)
        return 1

    proto_path = Path(args.protocol_file).resolve()
    if not proto_path.is_file():
        print(f"Error: Protocol file not found at {proto_path}", file=sys.stderr)
        return 1

    proto_dict = json.loads(proto_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)

    pricing_config = None
    if args.pricing_file and Path(args.pricing_file).is_file():
        pricing_config = json.loads(Path(args.pricing_file).read_bytes())

    manifest_dir = manifest_path.parent
    prediction_paths = {c: manifest_dir / f"{c}_predictions.jsonl" for c in CONDITIONS}

    repo_root = (
        Path(args.repository_root).resolve()
        if args.repository_root
        else Path(__file__).resolve().parents[2]
    )
    inputs = load_evaluation_inputs(manifest_path, prediction_paths, repository_root=repo_root)

    print(f"Loaded evaluation inputs for experiment: {inputs.experiment_id}")
    print(f"Evaluating RQ1, RQ2, and RQ3 with {args.bootstrap_samples} bootstrap samples...")

    results = run_rq_analysis(
        inputs,
        protocol,
        pricing_config=pricing_config,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        output_dir=args.output_dir,
    )

    print("Offline evaluation complete. Summary:")
    print(f"  Best RAG Condition (RQ1): {results['rq1']['best_rag_condition']}")
    print(f"  Accuracy Gain vs No-RAG: {results['rq1']['best_rag_accuracy_delta']:+.4f}")
    print(f"  Outputs saved to: {args.output_dir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
