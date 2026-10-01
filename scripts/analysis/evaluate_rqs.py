"""Comprehensive Offline Analysis for Research Questions RQ1, RQ2, and RQ3.

Computes:
- RQ1: Controlled comparison of No-RAG vs RAG (k=1, 3, 5, 10) on exact technique attribution,
  with delta metrics, relative gains, McNemar significance tests, and pair-cluster bootstrap CIs.
- RQ2: Retrieval vs. Generation error decomposition, measuring retrieval Recall@k,
  downstream generation accuracy conditioned on retrieval success, and failure source attribution.
- RQ3: Retrieval depth ablation (k in 1, 3, 5, 10 vs 0), latency, token expenditure, monetary
  costs (pricing-v1 tariffs), full ledger/journal reconciliation, explicit cost denominators,
  and paired Single-View vs Contextual-View diagnostics.

Secondary statistical tests (McNemar test, pair-cluster bootstrap CIs) are exploratory diagnostics
accounting for intra-pair correlation; they do not alter frozen headline protocol.
"""

from __future__ import annotations

import argparse
import hashlib
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
    round_cost_up,
)

ANALYSIS_TOOL_VERSION = "1.1.0"


# ---------------------------------------------------------------------------
# Strict Pricing & Financial Ledger Reconciliation Helpers
# ---------------------------------------------------------------------------


def validate_pricing_config(pricing_config: dict[str, Any]) -> dict[str, Any]:
    """Strictly validate the pricing configuration against pricing-v1 contract.

    Invariants:
    - Rejects missing tariffs or missing 'default' service tier.
    - Requires 'short' and 'long' context tables with all 4 per-million rates.
    - Requires reservation_bounds with positive default_attempt_worst_usd and
      default_logical_worst_usd.
    - Requires ceilings with positive integers max_input_tokens, max_output_tokens,
      short_context_limit.
    - Requires total_study_budget_usd.
    - Programming errors propagate; never falls back to zero or default tier silently.
    """
    if not isinstance(pricing_config, dict):
        raise ValueError(f"Pricing config must be a dict, got {type(pricing_config).__name__}")

    tariffs = pricing_config.get("tariffs")
    if not isinstance(tariffs, dict) or "default" not in tariffs:
        raise ValueError("Pricing config missing 'tariffs' or 'default' service tier")

    for tier_name, tier_dict in tariffs.items():
        if not isinstance(tier_dict, dict):
            raise ValueError(f"Tariff for tier '{tier_name}' must be a dict")
        for ctx in ("short", "long"):
            if ctx not in tier_dict:
                raise ValueError(f"Tariff for tier '{tier_name}' missing '{ctx}' context rates")
            rates = tier_dict[ctx]
            for rate_key in (
                "input_per_million",
                "output_per_million",
                "cache_read_per_million",
                "cache_write_per_million",
            ):
                if rate_key not in rates:
                    raise ValueError(f"Tariff '{tier_name}.{ctx}' missing rate '{rate_key}'")
                try:
                    val = Decimal(str(rates[rate_key]))
                    if val < 0:
                        raise ValueError(
                            f"Rate '{rate_key}' in '{tier_name}.{ctx}' cannot be negative"
                        )
                except Exception as exc:
                    raise ValueError(
                        f"Invalid rate '{rate_key}' in tariff '{tier_name}.{ctx}': {exc}"
                    )

    bounds = pricing_config.get("reservation_bounds")
    if not isinstance(bounds, dict):
        raise ValueError("Pricing config missing 'reservation_bounds'")
    for b_key in ("default_attempt_worst_usd", "default_logical_worst_usd"):
        if b_key not in bounds:
            raise ValueError(f"Missing required reservation bound '{b_key}'")
        val = Decimal(str(bounds[b_key]))
        if val <= 0:
            raise ValueError(f"Reservation bound '{b_key}' must be positive")

    ceilings = pricing_config.get("ceilings")
    if not isinstance(ceilings, dict):
        raise ValueError("Pricing config missing 'ceilings'")
    for c_key in ("max_input_tokens", "max_output_tokens", "short_context_limit"):
        if c_key not in ceilings or not isinstance(ceilings[c_key], int) or ceilings[c_key] <= 0:
            raise ValueError(f"Ceilings missing positive integer '{c_key}'")

    if "total_study_budget_usd" not in pricing_config:
        raise ValueError("Pricing config missing 'total_study_budget_usd'")

    return pricing_config


def reconcile_journal_and_ledger(
    records: Sequence[Mapping[str, Any]],
    pricing_config: dict[str, Any],
    *,
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Reconcile request journal attempt receipts and monetary settlements by sample/condition.

    Invariants:
    - Verifies journal header against manifest when present.
    - Strictly checks attempt receipt ordinal uniqueness and attempt_index uniqueness per request.
    - Computes attempt receipt costs using actual returned service tier and cached token rates.
    - Validates monetary settlement hash binding against prediction record SHA-256.
    - Flags monetary breaches and duplicate settlements.
    - Distinguishes canonical condition expenditures from whole-study holds and orphan reservations.
    """
    validate_pricing_config(pricing_config)

    records_by_key = {(r["sample_id"], r["condition"]): r for r in records}

    events: list[dict[str, Any]] = []
    if journal_events is not None:
        events = list(journal_events)
    elif journal_path is not None and Path(journal_path).is_file():
        raw_lines = Path(journal_path).read_text(encoding="utf-8").splitlines()
        events = [json.loads(line) for line in raw_lines if line.strip()]

    if not events:
        return {
            "journal_present": False,
            "receipts_by_condition": {c: [] for c in CONDITIONS},
            "settlements_by_condition": {c: {} for c in CONDITIONS},
            "receipts_cost_by_condition": {c: None for c in CONDITIONS},
            "settled_cost_by_condition": {c: None for c in CONDITIONS},
            "retried_attempts_by_condition": {c: 0 for c in CONDITIONS},
            "active_reservations_usd": Decimal("0.0"),
            "orphan_reservations_usd": Decimal("0.0"),
            "has_breach": False,
            "breach_reasons": [],
        }

    receipts_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    settlements_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    seen_receipt_ordinals: set[int] = set()
    active_reservations: dict[tuple[str, str], Decimal] = {}
    orphan_reservations_usd = Decimal("0.0")
    has_breach = False
    breach_reasons: list[str] = []

    for event in events:
        kind = event.get("event")
        key_raw = event.get("key")
        key = (key_raw[0], key_raw[1]) if isinstance(key_raw, list) and len(key_raw) == 2 else None

        if kind == "attempt_receipt" and key is not None:
            rec_ord = event.get("ordinal")
            rec_idx = event.get("attempt_index")
            if rec_ord in seen_receipt_ordinals:
                raise ValueError(
                    f"Duplicate attempt_receipt ordinal {rec_ord} for key {key} in journal"
                )
            seen_receipt_ordinals.add(rec_ord)

            existing_receipts = receipts_by_key[key]
            if any(r.get("attempt_index") == rec_idx for r in existing_receipts):
                raise ValueError(f"Duplicate attempt_receipt attempt_index {rec_idx} for key {key}")

            tier = event.get("service_tier") or event.get("requested_service_tier") or "default"
            rec_cost = calculate_attempt_token_cost(
                event.get("input_tokens"),
                event.get("output_tokens"),
                pricing_config,
                cached_tokens=event.get("cached_tokens"),
                tier=tier,
            )
            event_copy = dict(event)
            event_copy["calculated_cost_usd"] = rec_cost
            receipts_by_key[key].append(event_copy)

        elif kind == "monetary_settle" and key is not None:
            if key in settlements_by_key:
                raise ValueError(f"Duplicate monetary_settle event for key {key} in journal")
            settlements_by_key[key] = event
            if event.get("breach", False):
                has_breach = True
                breach_reasons.append(str(event.get("breach_reason", "Unknown monetary breach")))

            # Verify hash binding against record
            if key in records_by_key:
                rec_sha = hashlib.sha256(canonical_json_bytes(records_by_key[key])).hexdigest()
                settle_sha = event.get("record_sha256")
                if settle_sha != rec_sha:
                    raise ValueError(
                        f"Monetary settle record_sha256 mismatch for key {key}: "
                        f"{settle_sha} != {rec_sha}"
                    )

        elif kind == "monetary_reserve" and key is not None:
            active_reservations[key] = Decimal(str(event.get("amount_usd", "0.0")))

        elif kind == "complete" and key is not None:
            if key in active_reservations:
                del active_reservations[key]

        elif kind == "monetary_cancel_orphan" and key is not None:
            orphan_reservations_usd += Decimal(str(event.get("refund_usd", "0.0")))

    # Aggregate by condition
    receipts_cost_by_cond: dict[str, Optional[Decimal]] = {}
    settled_cost_by_cond: dict[str, Optional[Decimal]] = {}
    retried_attempts_by_cond: dict[str, int] = {}

    for cond in CONDITIONS:
        cond_receipts = [
            r for (sid, c), r_list in receipts_by_key.items() if c == cond for r in r_list
        ]
        cond_settles = [s for (sid, c), s in settlements_by_key.items() if c == cond]

        if cond_receipts:
            receipts_cost_by_cond[cond] = round_cost_up(
                sum(r["calculated_cost_usd"] for r in cond_receipts)
            )
            retried_attempts_by_cond[cond] = sum(
                1 for r in cond_receipts if r.get("attempt_index", 0) > 0
            )
        else:
            receipts_cost_by_cond[cond] = None
            retried_attempts_by_cond[cond] = 0

        if cond_settles:
            settled_cost_by_cond[cond] = round_cost_up(
                sum(Decimal(str(s["cost_usd"])) for s in cond_settles)
            )
        else:
            settled_cost_by_cond[cond] = None

    active_res_sum = (
        round_cost_up(sum(active_reservations.values())) if active_reservations else Decimal("0.0")
    )

    return {
        "journal_present": True,
        "receipts_by_condition": receipts_by_key,
        "settlements_by_condition": settlements_by_key,
        "receipts_cost_by_condition": receipts_cost_by_cond,
        "settled_cost_by_condition": settled_cost_by_cond,
        "retried_attempts_by_condition": retried_attempts_by_cond,
        "active_reservations_usd": active_res_sum,
        "orphan_reservations_usd": orphan_reservations_usd,
        "has_breach": has_breach,
        "breach_reasons": breach_reasons,
    }


# ---------------------------------------------------------------------------
# Statistical Testing Helpers (with Pair-Cluster Resampling)
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

    disc = b + c
    diff = abs(b - c)

    if disc == 0:
        chi2 = 0.0
        p_val_asymp = 1.0
        p_val_exact = 1.0
    else:
        num = max(0.0, float(diff - 1)) ** 2
        chi2 = num / disc
        p_val_asymp = float(math.erfc(math.sqrt(chi2) / math.sqrt(2.0)))

        k_min = min(b, c)
        prob_tail = sum(math.comb(disc, k) * (0.5**disc) for k in range(k_min + 1))
        p_val_exact = min(1.0, 2.0 * prob_tail)

    return {
        "contingency_table": {
            "total_pairs": n,
            "both_correct_a": a,
            "treatment_win_b": b,
            "baseline_win_c": c,
            "both_incorrect_d": d,
            "total_discordant": disc,
        },
        "chi2_statistic": chi2,
        "p_value_asymptotic": p_val_asymp,
        "p_value_exact": p_val_exact,
        "significant_at_05": p_val_exact < 0.05,
        "significant_at_01": p_val_exact < 0.01,
    }


def compute_paired_bootstrap_ci(
    scores_treatment: Sequence[float],
    scores_baseline: Sequence[float],
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical bootstrap CI for paired differences with pair-cluster resampling.

    When cluster_ids (e.g. pair_id) are provided, resamples clusters with replacement so that
    views sharing a pair_id are sampled together, preserving intra-pair correlation.
    """
    n = len(scores_treatment)
    if n == 0 or len(scores_baseline) != n:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean_delta": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
            "resampling_method": "pair_cluster_bootstrap" if cluster_ids else "paired_bootstrap",
        }

    arr_treat = np.array(scores_treatment, dtype=np.float64)
    arr_base = np.array(scores_baseline, dtype=np.float64)
    rng = np.random.default_rng(seed)
    deltas = np.empty(num_samples, dtype=np.float64)

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            deltas[i] = np.mean(arr_treat[sampled_indices]) - np.mean(arr_base[sampled_indices])

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            deltas[i] = np.mean(arr_treat[indices]) - np.mean(arr_base[indices])

        resampling_method = "paired_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(deltas, lower_pct)),
        "ci_upper": float(np.percentile(deltas, upper_pct)),
        "mean_delta": float(np.mean(deltas)),
        "std_error": float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
    }


def compute_single_bootstrap_ci(
    scores: Sequence[float],
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical percentile bootstrap CI for a single metric series with pair-clustering."""
    n = len(scores)
    if n == 0:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
            "resampling_method": "pair_cluster_bootstrap" if cluster_ids else "single_bootstrap",
        }

    arr = np.array(scores, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = np.empty(num_samples, dtype=np.float64)

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            means[i] = np.mean(arr[sampled_indices])

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            means[i] = np.mean(arr[indices])

        resampling_method = "single_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(means, lower_pct)),
        "ci_upper": float(np.percentile(means, upper_pct)),
        "mean": float(np.mean(means)),
        "std_error": float(np.std(means, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
    }


def compute_macro_f1_bootstrap_ci(
    records_treat: Sequence[Mapping[str, Any]],
    records_base: Sequence[Mapping[str, Any]],
    ground_truth: Mapping[str, tuple[str, ...]],
    universe_size: int = 474,
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute bootstrap CI for paired delta in Macro-F1 across 474 classes with pair-clustering."""
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

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            sub_t = [treat_pairs[idx] for idx in sampled_indices]
            sub_b = [base_pairs[idx] for idx in sampled_indices]
            deltas[i] = _calc_fast_macro_f1(sub_t) - _calc_fast_macro_f1(sub_b)

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            sub_t = [treat_pairs[idx] for idx in indices]
            sub_b = [base_pairs[idx] for idx in indices]
            deltas[i] = _calc_fast_macro_f1(sub_t) - _calc_fast_macro_f1(sub_b)

        resampling_method = "paired_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(deltas, lower_pct)),
        "ci_upper": float(np.percentile(deltas, upper_pct)),
        "mean_delta": float(np.mean(deltas)),
        "std_error": float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
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
      - Statistical significance via paired McNemar test and pair-cluster bootstrap CIs.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    scorable_by_cond: dict[str, list[dict[str, Any]]] = {}
    correctness_by_cond_sample: dict[str, dict[str, bool]] = {}
    sample_pair_map: dict[str, str] = {}

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
                sample_pair_map[sid] = r.get("pair_id") or sid

        scorable_by_cond[cond] = scorable_records
        correctness_by_cond_sample[cond] = sample_correctness

    base_cond = "no_rag"
    base_metrics = condition_metrics[base_cond]
    base_correctness = correctness_by_cond_sample[base_cond]
    common_scorable_sids = sorted(base_correctness.keys())

    base_bools = [base_correctness[sid] for sid in common_scorable_sids]
    base_scores = [1.0 if b else 0.0 for b in base_bools]
    cluster_ids = [sample_pair_map.get(sid, sid) for sid in common_scorable_sids]

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
            cond_scores, cluster_ids=cluster_ids, num_samples=bootstrap_samples, seed=seed
        )

        cond_result: dict[str, Any] = {
            "condition": cond,
            "scorable_sample_count": m["scorable_sample_count"],
            "accuracy_end_to_end": m["accuracy_end_to_end"],
            "accuracy_valid_outputs": m["accuracy_valid_outputs"],
            "macro_f1": m["macro_f1"],
            "correct_count": m["correct_count"],
            "accuracy_e2e_ci_95": [acc_ci["ci_lower"], acc_ci["ci_upper"]],
            "resampling_method": acc_ci.get("resampling_method"),
            "cluster_count": acc_ci.get("cluster_count"),
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
                cond_scores,
                base_scores,
                cluster_ids=cluster_ids,
                num_samples=bootstrap_samples,
                seed=seed,
            )
            paired_f1_ci = compute_macro_f1_bootstrap_ci(
                scorable_by_cond[cond],
                scorable_by_cond[base_cond],
                inputs.ground_truth,
                universe_size=universe_size,
                cluster_ids=cluster_ids,
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
                "exploratory_diagnostics": {
                    "resampling_method": paired_acc_ci.get("resampling_method"),
                    "cluster_count": paired_acc_ci.get("cluster_count"),
                    "note": (
                        "Secondary exploratory diagnostics: pair-clustered bootstrap resampling "
                        "preserves intra-pair correlation between single-view and contextual-view "
                        "samples sharing pair_id; does not alter frozen headline metrics."
                    ),
                },
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

    Invariants (per Decision D2i and D2j):
    - Independent failure axes: retrieval miss, provider failure, parse failure,
      invalid attack ID, and valid-but-wrong classification are evaluated without
      forced mutual exclusion or unapproved causal source-partition claims.
    - Preserves all provider/parse/invalid counts even when a retrieval miss occurs.
    - Explicitly computes and reports overlaps (e.g., retrieval miss + provider failure,
      retrieval miss + valid but wrong classification).
    - For No-RAG: Hit@k, Recall@k, and retrieval-conditioned metrics are strictly NOT APPLICABLE
      (None / null), not observed zero performance.
    - Zero-denominator rates and percentages evaluate to None (null per D2j), never 0.0.
    """
    if retrieval_cond_metrics is None:
        retrieval_cond_metrics = compute_retrieval_conditional_metrics(inputs, protocol)
    if failure_decomp_metrics is None:
        failure_decomp_metrics = compute_failure_decomposition(inputs, protocol)

    by_condition_rq2 = {}

    for cond in CONDITIONS:
        k = 0 if cond == "no_rag" else int(cond[5:])
        is_rag = k > 0

        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = [
            r
            for r in cond_records
            if inputs.ground_truth_status.get(
                r["sample_id"],
                "mapped" if inputs.ground_truth.get(r["sample_id"]) else "unmapped",
            )
            == "mapped"
            and inputs.ground_truth.get(r["sample_id"])
        ]

        total_scorable = len(scorable_records)
        n_correct = sum(
            1
            for r in scorable_records
            if r["parse_status"] == "VALID"
            and bool(r.get("parsed_technique_ids"))
            and r["parsed_technique_ids"][0] in set(inputs.ground_truth.get(r["sample_id"], ()))
        )
        total_failures = total_scorable - n_correct

        # 1. Retrieval & Conditional Metrics (None for No-RAG)
        if is_rag:
            ret_info = retrieval_cond_metrics["by_condition"].get(cond, {})
            retrieval_metrics = {
                "applicable": True,
                "macro_recall": ret_info.get("macro_recall"),
                "retrieval_hit_rate": ret_info.get("retrieval_hit_rate"),
                "retrieved_positive_count": ret_info.get("retrieved_positive_count"),
                "total_positive_sample_count": ret_info.get("total_positive_sample_count"),
            }
            generation_conditional = {
                "applicable": True,
                "p_correct_given_retrieval_success": ret_info.get(
                    "p_correct_given_retrieval_success"
                ),
                "p_correct_given_retrieval_failure": ret_info.get(
                    "p_correct_given_retrieval_failure"
                ),
                "retrieval_success_sample_count": ret_info.get("retrieval_success_sample_count"),
                "retrieval_failure_sample_count": ret_info.get("retrieval_failure_sample_count"),
            }
        else:
            retrieval_metrics = {
                "applicable": False,
                "macro_recall": None,
                "retrieval_hit_rate": None,
                "retrieved_positive_count": None,
                "total_positive_sample_count": None,
                "note": "Retrieval metrics not applicable to No-RAG baseline (k=0).",
            }
            generation_conditional = {
                "applicable": False,
                "p_correct_given_retrieval_success": None,
                "p_correct_given_retrieval_failure": None,
                "retrieval_success_sample_count": None,
                "retrieval_failure_sample_count": None,
                "note": "Retrieval-conditioned metrics not applicable to No-RAG baseline (k=0).",
            }

        # 2. Independent Failure Axes & Overlaps
        ret_misses = 0 if is_rag else None
        prov_failures = 0
        parse_failures = 0
        invalid_attack_ids = 0
        valid_but_wrong = 0

        overlap_miss_and_wrong = 0 if is_rag else None
        overlap_miss_and_provider = 0 if is_rag else None
        overlap_miss_and_parse = 0 if is_rag else None
        overlap_miss_and_invalid = 0 if is_rag else None

        for r in scorable_records:
            gt = set(inputs.ground_truth.get(r["sample_id"], ()))
            status = r["parse_status"]
            retrieved = {c["technique_id"] for c in r.get("retrieved_candidates", [])}
            is_miss = is_rag and not bool(retrieved & gt)

            if is_miss and ret_misses is not None:
                ret_misses += 1

            if status in {"TIMEOUT", "REFUSAL", "INCOMPLETE", "API_FAILURE"}:
                prov_failures += 1
                if is_miss and overlap_miss_and_provider is not None:
                    overlap_miss_and_provider += 1
            elif status == "MALFORMED_RESPONSE":
                parse_failures += 1
                if is_miss and overlap_miss_and_parse is not None:
                    overlap_miss_and_parse += 1
            elif status == "INVALID_ID":
                invalid_attack_ids += 1
                if is_miss and overlap_miss_and_invalid is not None:
                    overlap_miss_and_invalid += 1
            elif status == "VALID":
                pred = r.get("parsed_technique_ids", [None])[0]
                if pred not in gt:
                    valid_but_wrong += 1
                    if is_miss and overlap_miss_and_wrong is not None:
                        overlap_miss_and_wrong += 1

        # Rates relative to total_scorable (None per D2j if zero denominator)
        def _rate_or_none(count: Optional[int], denom: int) -> Optional[float]:
            if count is None or denom <= 0:
                return None
            return count / denom

        ret_miss_rate = _rate_or_none(ret_misses, total_scorable)
        prov_rate = _rate_or_none(prov_failures, total_scorable)
        parse_rate = _rate_or_none(parse_failures, total_scorable)
        inv_rate = _rate_or_none(invalid_attack_ids, total_scorable)
        wrong_rate = _rate_or_none(valid_but_wrong, total_scorable)

        # Fractions among failures (None per D2j if total_failures == 0)
        frac_ret_miss = _rate_or_none(ret_misses, total_failures)
        frac_prov = _rate_or_none(prov_failures, total_failures)
        frac_parse = _rate_or_none(parse_failures, total_failures)
        frac_inv = _rate_or_none(invalid_attack_ids, total_failures)
        frac_wrong = _rate_or_none(valid_but_wrong, total_failures)

        by_condition_rq2[cond] = {
            "condition": cond,
            "retrieval_k": k,
            "total_scorable_samples": total_scorable,
            "total_failures": total_failures,
            "retrieval_metrics": retrieval_metrics,
            "generation_conditional_accuracy": generation_conditional,
            "independent_failure_axes": {
                "retrieval_miss_count": ret_misses,
                "retrieval_miss_rate": ret_miss_rate,
                "provider_failure_count": prov_failures,
                "provider_failure_rate": prov_rate,
                "parse_failure_count": parse_failures,
                "parse_failure_rate": parse_rate,
                "invalid_attack_id_count": invalid_attack_ids,
                "invalid_attack_id_rate": inv_rate,
                "valid_but_wrong_classification_count": valid_but_wrong,
                "valid_but_wrong_classification_rate": wrong_rate,
                "overlap_retrieval_miss_and_wrong_classification": overlap_miss_and_wrong,
                "overlap_retrieval_miss_and_provider_failure": overlap_miss_and_provider,
                "overlap_retrieval_miss_and_parse_failure": overlap_miss_and_parse,
                "overlap_retrieval_miss_and_invalid_id": overlap_miss_and_invalid,
                "rates_among_failures": {
                    "retrieval_miss": frac_ret_miss,
                    "provider_failure": frac_prov,
                    "parse_failure": frac_parse,
                    "invalid_attack_id": frac_inv,
                    "valid_but_wrong_classification": frac_wrong,
                },
                "canonical_d2i_policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced "
                    "mutual exclusion. Retrieval miss does not establish cause of provider or "
                    "parse failure."
                ),
            },
            # Backward-compatible view preserved without causal partition claims
            "error_decomposition": {
                "retrieval_miss_error_count": ret_misses,
                "generation_misattribution_count": valid_but_wrong,
                "system_or_parse_error_count": prov_failures + parse_failures,
                "overlap_retrieval_miss_and_wrong_classification": overlap_miss_and_wrong,
                "retrieval_miss_fraction_of_failures": frac_ret_miss,
                "generation_misattribution_fraction_of_failures": frac_wrong,
                "system_or_parse_fraction_of_failures": _rate_or_none(
                    prov_failures + parse_failures, total_failures
                ),
            },
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ2: Retrieval vs. Generation error decomposition",
        "by_condition": by_condition_rq2,
    }


# ---------------------------------------------------------------------------
# RQ3 Analysis: Retrieval Depth Ablation, Efficiency, & View Diagnostics
# ---------------------------------------------------------------------------


def compute_rq3(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
    *,
    pricing_config: Optional[dict[str, Any]] = None,
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Compute RQ3: Retrieval depth ablation, latency, financial costs, and view diagnostics.

    Evaluates:
      - Performance curve across k: Accuracy, Macro-F1, Recall@k.
      - Latency distribution: Mean, median, p95, sum (ms).
      - Token usage: Mean prompt/completion/total tokens, sum.
      - Financial cost calculation: Full journal/ledger reconciliation, explicit cost denominators:
        * cost_per_logical_request (N=1,280 in TEST)
        * cost_per_scorable_query (N=718 in TEST)
        * cost_per_correct_attribution
      - Real expenditure disclosure for excluded ambiguous (311) and unmapped (251) views.
      - Whole-study accounting including prior pilot hold ($0.05264010) and active reservations.
      - Paired Single-View (278 scorable) vs Contextual-View (440 scorable) diagnostics.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    if pricing_config is None:
        target_root = repo_root or Path(__file__).resolve().parents[2]
        pricing_config, _ = load_pricing_config(repo_root=target_root)

    validate_pricing_config(pricing_config)

    # Reconcile attempt receipts and ledger settlements
    reconciliation = reconcile_journal_and_ledger(
        inputs.records,
        pricing_config,
        journal_path=journal_path,
        journal_events=journal_events,
        study_ledger_path=study_ledger_path,
        study_ledger_data=study_ledger_data,
    )

    tradeoff_by_condition = {}
    base_cost_usd = 0.0

    worst_charge = Decimal(str(pricing_config["reservation_bounds"]["default_attempt_worst_usd"]))

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

        # Token-based estimation per record (worst-case charged on missing usage)
        rec_token_cost = Decimal("0.0")
        missing_usage_count = 0
        missing_usage_cost = Decimal("0.0")
        cost_ambiguous = Decimal("0.0")
        cost_unmapped = Decimal("0.0")

        for r in rows:
            p_tok = r.get("prompt_tokens")
            c_tok = r.get("completion_tokens")
            ca_tok = r.get("cached_tokens")

            if p_tok is None or c_tok is None:
                missing_usage_count += 1
                item_cost = worst_charge
                missing_usage_cost += worst_charge
            else:
                item_cost = calculate_attempt_token_cost(
                    p_tok, c_tok, pricing_config, cached_tokens=ca_tok, tier="default"
                )

            rec_token_cost += item_cost

            # Track spending on excluded views
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "ambiguous":
                cost_ambiguous += item_cost
            elif status == "unmapped" or not gt:
                cost_unmapped += item_cost

        # Determine authoritative condition cost from ledger/receipts if available
        receipts_cost = reconciliation["receipts_cost_by_condition"].get(cond)
        settled_cost = reconciliation["settled_cost_by_condition"].get(cond)
        retried_count = reconciliation["retried_attempts_by_condition"].get(cond, 0)

        if settled_cost is not None:
            authoritative_cost = settled_cost
        elif receipts_cost is not None:
            authoritative_cost = receipts_cost
        else:
            authoritative_cost = rec_token_cost

        total_cost_usd = float(authoritative_cost)
        if cond == "no_rag":
            base_cost_usd = total_cost_usd

        # Explicitly report three distinct cost denominators
        logical_count = len(rows)
        scorable_count = m["scorable_sample_count"]
        correct_count = m["correct_count"]

        cost_per_logical = (total_cost_usd / logical_count) if logical_count > 0 else None
        cost_per_scorable = (total_cost_usd / scorable_count) if scorable_count > 0 else None
        cost_per_correct = (total_cost_usd / correct_count) if correct_count > 0 else None
        cost_all_excluded = float(cost_ambiguous + cost_unmapped)

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
                "token_usage_estimated_cost_usd": float(rec_token_cost),
                "receipts_reconciled_cost_usd": (
                    float(receipts_cost) if receipts_cost is not None else None
                ),
                "ledger_settled_cost_usd": (
                    float(settled_cost) if settled_cost is not None else None
                ),
                "total_cost_usd": total_cost_usd,
                "cost_per_logical_request_usd": cost_per_logical,
                "cost_per_scorable_query_usd": cost_per_scorable,
                "cost_per_correct_attribution_usd": cost_per_correct,
                "marginal_cost_vs_baseline_usd": total_cost_usd - base_cost_usd,
                "missing_usage_records_count": missing_usage_count,
                "missing_usage_worst_charge_usd": float(missing_usage_cost),
                "retried_attempts_count": retried_count,
                "cost_of_excluded_ambiguous_views_usd": float(cost_ambiguous),
                "cost_of_excluded_unmapped_views_usd": float(cost_unmapped),
                "cost_of_all_excluded_views_usd": cost_all_excluded,
                "excluded_views_financial_disclosure": (
                    "Costs of excluded ambiguous (311) and unmapped (251) views remain "
                    "real monetary expenditure incurred during inference and are fully "
                    "included in condition and study totals."
                ),
            },
        }

    # Whole-study financial summary
    total_budget_usd = Decimal(str(pricing_config.get("total_study_budget_usd", "19.99000000")))
    pilot_hold_usd = Decimal(
        str(pricing_config.get("prior_pilot_provisional_hold_usd", "0.05264010"))
    )
    canonical_total = sum(
        Decimal(str(tradeoff_by_condition[c]["financial_cost_usd"]["total_cost_usd"]))
        for c in CONDITIONS
    )
    active_res = reconciliation["active_reservations_usd"]
    orphan_res = reconciliation["orphan_reservations_usd"]
    total_committed = round_cost_up(canonical_total + pilot_hold_usd + active_res)
    uncommitted = round_cost_up(total_budget_usd - total_committed)

    whole_study_accounting = {
        "total_study_budget_usd": float(total_budget_usd),
        "canonical_conditions_total_usd": float(canonical_total),
        "prior_pilot_provisional_hold_usd": float(pilot_hold_usd),
        "active_reservations_usd": float(active_res),
        "orphan_reservations_usd": float(orphan_res),
        "total_study_committed_spend_usd": float(total_committed),
        "net_remaining_uncommitted_budget_usd": float(uncommitted),
        "study_wide_missing_usage_records_count": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["missing_usage_records_count"]
            for c in CONDITIONS
        ),
        "study_wide_missing_usage_charged_usd": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["missing_usage_worst_charge_usd"]
            for c in CONDITIONS
        ),
        "study_wide_retried_attempts_count": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["retried_attempts_count"]
            for c in CONDITIONS
        ),
        "accounting_policy_disclosure": (
            "Prior pilot provisional hold ($0.05264010) is accounted exclusively at the "
            "whole-study level and is never allocated to individual canonical conditions. "
            "Spending on excluded ambiguous and unmapped views is fully accounted as real "
            "monetary spend."
        ),
    }

    # Paired Single-View (278 scorable) vs Contextual-View (440 scorable) Diagnostics
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
            sum(1 for _, c in single_records if c) / len(single_records) if single_records else None
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
            "single_view_scorable_count": len(single_records),
            "contextual_view_scorable_count": len(contextual_records),
            "view_split_notes": (
                "Empirical TEST scorable views: 278 single views and 440 contextual views "
                "(718 total), reflecting mapped ground truth rather than an assumed 50/50 balance."
            ),
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
            "mcnemar_test_views_exploratory": mcnemar_views,
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ3: Retrieval depth & efficiency ablation and view diagnostics",
        "tradeoffs_by_condition": tradeoff_by_condition,
        "whole_study_financial_accounting": whole_study_accounting,
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
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
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
    rq3 = compute_rq3(
        inputs,
        protocol,
        cond_metrics,
        pricing_config=pricing_config,
        journal_path=journal_path,
        journal_events=journal_events,
        study_ledger_path=study_ledger_path,
        study_ledger_data=study_ledger_data,
        repo_root=repo_root,
    )

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
    whole_fin = rq3.get("whole_study_financial_accounting", {})

    lines = [
        "# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)",
        "",
        f"- **Experiment ID**: `{analysis_dict.get('experiment_id')}`",
        f"- **Manifest SHA-256**: `{analysis_dict.get('manifest_sha256')}`",
        f"- **Protocol Version**: `{analysis_dict.get('protocol_version')}` "
        f"(`{analysis_dict.get('protocol_sha256', '')[:12]}...`)",
        f"- **Analysis Tool Version**: `{analysis_dict.get('analysis_tool_version')}`",
        f"- **Report Generated**: `{analysis_dict.get('analysis_timestamp')}`",
        "",
        "---",
        "",
        "## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)",
        "",
        "> *Does retrieval augmentation improve exact technique attribution over unaugmented LLM?*",
        "",
        "| Condition | End-to-End Acc | 95% CI (Cluster) | Macro-F1 (474) | "
        "Delta Acc vs No-RAG | 95% CI Delta | McNemar p (exact) |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    by_cond_rq1 = rq1.get("by_condition", {})
    for cond in CONDITIONS:
        row = by_cond_rq1.get(cond, {})
        acc = f"{row.get('accuracy_end_to_end', 0.0):.4f}"
        ci = row.get("accuracy_e2e_ci_95", [0.0, 0.0])
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci and ci[0] is not None else "-"
        f1 = f"{row.get('macro_f1', 0.0):.4f}" if row.get("macro_f1") is not None else "-"

        if row.get("is_baseline"):
            d_str = "Baseline"
            d_ci_str = "-"
            p_str = "-"
        else:
            d_info = row.get("delta_vs_baseline", {})
            d_acc = d_info.get("delta_accuracy_end_to_end")
            rel_acc = d_info.get("relative_gain_accuracy_e2e_pct")
            d_str = (
                f"{d_acc:+.4f} ({rel_acc:+.1f}%)"
                if d_acc is not None and rel_acc is not None
                else "-"
            )
            d_ci = d_info.get("delta_accuracy_e2e_ci_95", [0.0, 0.0])
            d_ci_str = f"[{d_ci[0]:+.4f}, {d_ci[1]:+.4f}]" if d_ci and d_ci[0] is not None else "-"
            mcn = d_info.get("mcnemar_test", {})
            p_val = mcn.get("p_value_exact")
            p_str = f"{p_val:.4e}" if p_val is not None else "-"

        lines.append(f"| `{cond}` | {acc} | {ci_str} | {f1} | {d_str} | {d_ci_str} | {p_str} |")

    lines.extend(
        [
            "",
            f"- **Best RAG Condition**: `{rq1.get('best_rag_condition')}` "
            f"({rq1.get('best_rag_accuracy_delta', 0.0):+.4f} accuracy delta vs No-RAG)",
            "- **Note on Statistical Tests**: Pair-cluster bootstrap resampling resamples paired "
            "views sharing `pair_id` together, preserving intra-pair correlation. These tests are "
            "exploratory diagnostics and do not alter frozen headline protocol metrics.",
            "",
            "---",
            "",
            "## RQ2: Retrieval vs. Generation Error Decomposition",
            "",
            "> *Independent diagnostic failure axes and overlap analysis (Decision D2i).* "
            "*Hit/Recall and conditional metrics are not applicable to No-RAG.*",
            "",
            "| Condition | k | Recall@k | Hit@k | P(Corr | Hit) | P(Corr | Miss) | "
            "Ret Miss | Wrong Class | Prov Fail | Parse Fail | Invalid ID |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | "
            ":---: | :---: | :---: | :---: | :---: |",
        ]
    )

    by_cond_rq2 = rq2.get("by_condition", {})
    for cond in CONDITIONS:
        row = by_cond_rq2.get(cond, {})
        k = row.get("retrieval_k", 0)
        ret = row.get("retrieval_metrics", {})
        rec = f"{ret.get('macro_recall', 0.0):.4f}" if ret.get("macro_recall") is not None else "-"
        hit = (
            f"{ret.get('retrieval_hit_rate', 0.0):.4f}"
            if ret.get("retrieval_hit_rate") is not None
            else "-"
        )

        gen = row.get("generation_conditional_accuracy", {})
        p_succ = (
            f"{gen.get('p_correct_given_retrieval_success', 0.0):.4f}"
            if gen.get("p_correct_given_retrieval_success") is not None
            else "-"
        )
        p_fail = (
            f"{gen.get('p_correct_given_retrieval_failure', 0.0):.4f}"
            if gen.get("p_correct_given_retrieval_failure") is not None
            else "-"
        )

        axes = row.get("independent_failure_axes", {})
        ret_miss = (
            f"{axes.get('retrieval_miss_count', '-')}"
            if axes.get("retrieval_miss_count") is not None
            else "-"
        )
        wrong = f"{axes.get('valid_but_wrong_classification_count', '-')}"
        prov = f"{axes.get('provider_failure_count', '-')}"
        parse = f"{axes.get('parse_failure_count', '-')}"
        inv = f"{axes.get('invalid_attack_id_count', '-')}"

        lines.append(
            f"| `{cond}` | {k} | {rec} | {hit} | {p_succ} | {p_fail} | "
            f"{ret_miss} | {wrong} | {prov} | {parse} | {inv} |"
        )

    lines.extend(
        [
            "",
            "- **Note on Independent Failure Axes**: Evaluated independently per Decision D2i "
            "without forced mutual exclusion or unapproved causal attribution. Overlaps are "
            "explicitly tracked in JSON outputs. Retrieval metrics are not applicable to No-RAG.",
        ]
    )

    lines.extend(
        [
            "",
            "---",
            "",
            "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs",
            "",
            "> *What is the resource trade-off across candidate depths k in {1, 3, 5, 10}?*",
            "",
            "| Condition | k | Mean Lat (ms) | Mean Tokens | Total Cost ($) | "
            "Cost / Logical ($) | Cost / Scorable ($) | Cost / Corr ($) | Excluded ($) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    tradeoffs = rq3.get("tradeoffs_by_condition", {})
    for cond in CONDITIONS:
        row = tradeoffs.get(cond, {})
        k = row.get("retrieval_k", 0)
        lat = row.get("latency_ms", {})
        mean_l = f"{lat.get('mean', 0.0):.1f}" if lat.get("mean") is not None else "-"

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
        log_c = (
            f"${cost.get('cost_per_logical_request_usd', 0.0):.5f}"
            if cost.get("cost_per_logical_request_usd") is not None
            else "-"
        )
        scor_c = (
            f"${cost.get('cost_per_scorable_query_usd', 0.0):.5f}"
            if cost.get("cost_per_scorable_query_usd") is not None
            else "-"
        )
        corr_c = (
            f"${cost.get('cost_per_correct_attribution_usd', 0.0):.5f}"
            if cost.get("cost_per_correct_attribution_usd") is not None
            else "-"
        )
        excl_c = (
            f"${cost.get('cost_of_all_excluded_views_usd', 0.0):.5f}"
            if cost.get("cost_of_all_excluded_views_usd") is not None
            else "-"
        )

        lines.append(
            f"| `{cond}` | {k} | {mean_l} | {mean_t} | {tot_c} | "
            f"{log_c} | {scor_c} | {corr_c} | {excl_c} |"
        )

    lines.extend(
        [
            "",
            "### Study-Wide Financial Accounting",
            "",
            f"- **Total Study Budget**: `${whole_fin.get('total_study_budget_usd', 19.99):.8f}`",
            f"- **Canonical Conditions Cost**: "
            f"`${whole_fin.get('canonical_conditions_total_usd', 0.0):.8f}`",
            f"- **Prior Pilot Provisional Hold**: "
            f"`${whole_fin.get('prior_pilot_provisional_hold_usd', 0.05264010):.8f}`",
            f"- **Active Reservations**: `${whole_fin.get('active_reservations_usd', 0.0):.8f}`",
            f"- **Total Committed Spend**: "
            f"`${whole_fin.get('total_study_committed_spend_usd', 0.0):.8f}`",
            f"- **Net Available Uncommitted Budget**: "
            f"`${whole_fin.get('net_remaining_uncommitted_budget_usd', 0.0):.8f}`",
            f"- **Study-Wide Missing Usage Charges**: "
            f"{whole_fin.get('study_wide_missing_usage_records_count', 0)} records "
            f"(${whole_fin.get('study_wide_missing_usage_charged_usd', 0.0):.8f})",
            f"- **Financial Policy**: {whole_fin.get('accounting_policy_disclosure', '')}",
            "",
            "### Paired View Diagnostics (Single-View vs Contextual-View)",
            "",
            "> *TEST split scorable cohort contains 278 single views and 440 contextual views.* "
            "*Concordance evaluated on complete scorable pairs.*",
            "",
            "| Condition | Single Acc | Contextual Acc | Delta (Ctx - Sgl) | "
            "Concordant Both Corr | Ctx Win | Sgl Win |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

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
        help="Path to frozen experiment_protocol_v1.json (resolved against repo root if relative)",
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
        help="Path to pricing configuration file (resolved against repo root if relative)",
    )
    parser.add_argument(
        "--journal-file",
        type=Path,
        help="Path to request_journal.jsonl (defaults to run_dir/request_journal.jsonl if present)",
    )
    parser.add_argument(
        "--study-ledger-file",
        type=Path,
        help="Path to study_ledger.json (defaults to artifacts/study_budget if present)",
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

    # 1. Consistently determine repository root first
    repo_root = (
        Path(args.repository_root).resolve()
        if args.repository_root
        else Path(__file__).resolve().parents[2]
    )

    # 2. Resolve manifest path
    manifest_path = args.manifest
    if manifest_path is None and args.run_dir is not None:
        run_d = Path(args.run_dir)
        if not run_d.is_absolute():
            run_d = (repo_root / run_d).resolve()
        manifest_path = run_d / "manifest.json"
    elif manifest_path is not None and not manifest_path.is_absolute():
        manifest_path = (repo_root / manifest_path).resolve()

    if manifest_path is None or not manifest_path.is_file():
        print(f"Error: Manifest file not found at {manifest_path}", file=sys.stderr)
        return 1

    # 3. Resolve protocol path relative to repo_root if not absolute
    if args.protocol_file.is_absolute():
        proto_path = args.protocol_file.resolve()
    else:
        proto_path = (repo_root / args.protocol_file).resolve()

    if not proto_path.is_file():
        print(f"Error: Protocol file not found at {proto_path}", file=sys.stderr)
        return 1

    proto_dict = json.loads(proto_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)

    # 4. Resolve pricing path relative to repo_root if not absolute
    pricing_config = None
    if args.pricing_file is not None:
        if args.pricing_file.is_absolute():
            pricing_path = args.pricing_file.resolve()
        else:
            pricing_path = (repo_root / args.pricing_file).resolve()

        if not pricing_path.is_file():
            print(f"Error: Pricing file not found at {pricing_path}", file=sys.stderr)
            return 1
        pricing_config = json.loads(pricing_path.read_bytes())
        validate_pricing_config(pricing_config)

    # 5. Resolve journal and study ledger paths
    journal_path = None
    if args.journal_file is not None:
        journal_path = (
            args.journal_file.resolve()
            if args.journal_file.is_absolute()
            else (repo_root / args.journal_file).resolve()
        )
    elif (manifest_path.parent / "request_journal.jsonl").is_file():
        journal_path = manifest_path.parent / "request_journal.jsonl"

    study_ledger_path = None
    if args.study_ledger_file is not None:
        study_ledger_path = (
            args.study_ledger_file.resolve()
            if args.study_ledger_file.is_absolute()
            else (repo_root / args.study_ledger_file).resolve()
        )
    elif (repo_root / "artifacts" / "study_budget" / "study_ledger.json").is_file():
        study_ledger_path = repo_root / "artifacts" / "study_budget" / "study_ledger.json"

    # 6. Resolve output directory
    out_dir = args.output_dir
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()

    manifest_dir = manifest_path.parent
    prediction_paths = {c: manifest_dir / f"{c}_predictions.jsonl" for c in CONDITIONS}

    inputs = load_evaluation_inputs(manifest_path, prediction_paths, repository_root=repo_root)

    print(f"Loaded evaluation inputs for experiment: {inputs.experiment_id}")
    print(f"Evaluating RQ1, RQ2, and RQ3 with {args.bootstrap_samples} bootstrap samples...")

    results = run_rq_analysis(
        inputs,
        protocol,
        pricing_config=pricing_config,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        output_dir=out_dir,
        journal_path=journal_path,
        study_ledger_path=study_ledger_path,
        repo_root=repo_root,
    )

    print("Offline evaluation complete. Summary:")
    print(f"  Best RAG Condition (RQ1): {results['rq1']['best_rag_condition']}")
    print(f"  Accuracy Gain vs No-RAG: {results['rq1']['best_rag_accuracy_delta']:+.4f}")
    print(f"  Outputs saved to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
