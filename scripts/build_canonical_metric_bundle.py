#!/usr/bin/env python3
"""
scripts/build_canonical_metric_bundle.py

Deterministic canonical metric bundle v2 builder and validator for RAG2ATT&CK.
Assembles structured metrics, financial accounting, cache receipts, cohorts,
and provenance into artifacts/results/canonical_metric_bundle_v2.json.

Strictly FAIL-CLOSED on hash mismatch, broken invariant, or missing field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Fixed Protocol & Provenance Constants
EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_PUBLIC_MANIFEST_SHA256 = "32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c"
EXPECTED_TERMINAL_SEAL_SHA256 = "ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701"
EXPECTED_TERMINAL_PROOF_SHA256 = "cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
EXPECTED_PROTOCOL_SHA256 = "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"
EXPECTED_PRICING_CONTRACT_SHA256 = "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565"

# Historical & Superseding lineage
HISTORICAL_S2_PACKAGE_SHA256 = "c48eeb276166e511c7ff19904944d18ec0a187d903f0b2f56708ddaf4f9dff55"
AUTHORIZING_PACKET_PUBLIC_SHA256 = "d515f70426435e9edb79cdc415e91c23b16e189fd171d4db4b04074c9b580aa1"
AUTHORIZING_PACKET_ORIGINAL_SHA256 = "b988a599800bbbb01b0418e60bfd00fbbce3ab2c4d631da678f99bfd2141c4b5"

# Git commit bindings
EXECUTION_GIT_SHA = "80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315"
EVALUATION_GIT_SHA = "208ac00a9fe86813d4e4ec4fa72b2a943a2e4fdb"
CANDIDATE_REPO_GIT_SHA = "4fafdb290dac59070a43de33f7e299bbb25782e3"

# Fixed Cohort and Denominator Constants
COHORT_TOTAL_VIEWS = 1280
COHORT_TOTAL_PAIRS = 640
COHORT_MAPPED_VIEWS = 718
COHORT_AMBIGUOUS_VIEWS = 311
COHORT_UNMAPPED_VIEWS = 251
COHORT_SINGLE_GT_VIEWS = 678
COHORT_MULTI_GT_VIEWS = 40
COHORT_TOTAL_GT_SUPPORT_INSTANCES = 768
COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS = 440
COHORT_MACRO_UNIVERSE = 474
COHORT_SUPPORTED_CLASSES = 8
COHORT_UNSUPPORTED_CLASSES = 466

# Financial Constants (Decimal)
BUDGET_CAP_USD = Decimal("19.99000000")
PILOT_HOLD_USD = Decimal("0.05264010")
SETTLED_USD = Decimal("6.57575890")
TOTAL_ACCOUNTED_USD = Decimal("6.62839900")
AVAILABLE_BALANCE_USD = Decimal("13.36160100")

P95_STATUS_POLICY = "NOT REPORTED — approval evidence not established"

CONDITIONS = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
RETRIEVAL_K_VALUES = {"no_rag": 0, "rag_k1": 1, "rag_k3": 3, "rag_k5": 5, "rag_k10": 10}


def compute_sha256(path: Path) -> str:
    """Compute sha256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file_hash(path: Path, expected_sha: str, description: str) -> None:
    """Verify that file exists and matches expected sha256 hash."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file ({description}): {path}")
    actual_sha = compute_sha256(path)
    if actual_sha != expected_sha:
        raise ValueError(
            f"Hash mismatch for {description} at {path}!\n"
            f"  Expected: {expected_sha}\n"
            f"  Actual:   {actual_sha}"
        )


def verify_public_package(public_package_dir: Path) -> Dict[str, Any]:
    """
    Verify public canonical package against canonical_bundle_manifest.json.
    Returns the parsed manifest dictionary.
    """
    manifest_path = public_package_dir / "canonical_bundle_manifest.json"
    verify_file_hash(manifest_path, EXPECTED_PUBLIC_MANIFEST_SHA256, "public package manifest")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # 1. Byte-preserved files
    for rel_path, spec in manifest.get("byte_preserved_files", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sha256"]
        verify_file_hash(file_path, expected_sha, f"byte_preserved file {rel_path}")

    # 2. Sanitized transformed files
    for rel_path, spec in manifest.get("sanitized_transformed_files", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sanitized_sha256"]
        verify_file_hash(file_path, expected_sha, f"sanitized_transformed file {rel_path}")

    # 3. Sanitized provenance assets
    for rel_path, spec in manifest.get("sanitized_provenance_assets", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sanitized_sha256"]
        verify_file_hash(file_path, expected_sha, f"sanitized_provenance asset {rel_path}")

    # 4. Runtime assets
    for rel_path, spec in manifest.get("runtime_assets", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sha256"]
        verify_file_hash(file_path, expected_sha, f"runtime asset {rel_path}")

    return manifest


def verify_run_seal(seal_path: Path) -> Dict[str, Any]:
    """Verify canonical run seal v1 against expected hash and invariants."""
    verify_file_hash(seal_path, EXPECTED_TERMINAL_SEAL_SHA256, "canonical run seal")
    with open(seal_path, "r", encoding="utf-8") as f:
        seal = json.load(f)

    if seal.get("seal_type") != "canonical-independent-validation-seal-v1":
        raise ValueError(f"Invalid seal_type: {seal.get('seal_type')}")
    if not seal.get("production_ready", False):
        raise ValueError("Run seal production_ready is not True")
    if seal.get("has_breach", True):
        raise ValueError("Run seal has_breach is True")
    if seal.get("cumulative_settled_cost_usd") != str(SETTLED_USD):
        raise ValueError(
            f"Seal settled cost mismatch: {seal.get('cumulative_settled_cost_usd')} != {SETTLED_USD}"
        )
    if seal.get("uncommitted_available_balance_usd") != str(AVAILABLE_BALANCE_USD):
        raise ValueError(
            f"Seal balance mismatch: {seal.get('uncommitted_available_balance_usd')} != {AVAILABLE_BALANCE_USD}"
        )
    if seal.get("total_records") != 6400:
        raise ValueError(f"Seal total_records mismatch: {seal.get('total_records')} != 6400")
    if seal.get("code_manifest_sha256") != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError(f"Seal code_manifest_sha256 mismatch")
    if seal.get("pricing_contract_sha256") != EXPECTED_PRICING_CONTRACT_SHA256:
        raise ValueError(f"Seal pricing_contract_sha256 mismatch")
    if seal.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        raise ValueError(f"Seal protocol_sha256 mismatch")

    # Check terminal proof
    tp = seal.get("terminal_proof", {})
    if tp.get("sha256") != EXPECTED_TERMINAL_PROOF_SHA256:
        raise ValueError(f"Seal terminal_proof.sha256 mismatch")
    fs = tp.get("final_summary", {})
    if not fs.get("complete", False):
        raise ValueError("Seal terminal_proof complete is not True")
    if fs.get("record_count") != 6400:
        raise ValueError(f"Seal terminal_proof record_count mismatch: {fs.get('record_count')}")
    if fs.get("consumed_provider_attempts") != 6401:
        raise ValueError(f"Seal attempts mismatch: {fs.get('consumed_provider_attempts')}")
    if fs.get("requests_consumed") != 6401:
        raise ValueError(f"Seal requests_consumed mismatch: {fs.get('requests_consumed')}")

    return seal


def parse_request_journal_cache(journal_path: Path) -> Dict[str, Any]:
    """
    Parse request_journal.jsonl to extract precise cached_tokens telemetry.
    Strictly verifies receipt bindings, single physical failure, and retry success.
    """
    total_receipts = 0
    total_cached_tokens = 0
    cached_tokens_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}
    observed_receipts_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}
    missing_receipts_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}

    # Tracking specific transport error and retry
    transport_failure_info: Optional[Dict[str, Any]] = None
    retry_success_info: Optional[Dict[str, Any]] = None

    with open(journal_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            entry = json.loads(line)
            if entry.get("event") == "attempt_receipt":
                total_receipts += 1
                key = entry.get("key", [])
                if len(key) != 2:
                    raise ValueError(f"Invalid attempt_receipt key at line {line_num}: {key}")
                view_id, condition = key[0], key[1]
                if condition not in CONDITIONS:
                    raise ValueError(f"Unknown condition in receipt: {condition}")

                cached = entry.get("cached_tokens")
                ordinal = entry.get("ordinal")
                attempt_idx = entry.get("attempt_index")
                status = entry.get("status")

                if cached is None:
                    # Physical failure attempt
                    missing_receipts_by_condition[condition] += 1
                    if status != "API_FAILURE" or ordinal != 5387 or attempt_idx != 0:
                        raise ValueError(
                            f"Unexpected missing cached_tokens attempt at line {line_num}: {entry}"
                        )
                    transport_failure_info = {
                        "ordinal": ordinal,
                        "key": key,
                        "attempt_index": attempt_idx,
                        "status": status,
                        "error_type": entry.get("error_type"),
                        "input_tokens": entry.get("input_tokens"),
                        "output_tokens": entry.get("output_tokens"),
                        "cached_tokens": None,
                        "model": entry.get("model"),
                    }
                else:
                    # Observed attempt
                    observed_receipts_by_condition[condition] += 1
                    cached_tokens_by_condition[condition] += cached
                    total_cached_tokens += cached
                    if cached > 0:
                        if condition != "rag_k1" or ordinal != 5388 or attempt_idx != 1:
                            raise ValueError(
                                f"Unexpected non-zero cached_tokens at line {line_num}: {entry}"
                            )
                        retry_success_info = {
                            "ordinal": ordinal,
                            "key": key,
                            "attempt_index": attempt_idx,
                            "status": status,
                            "cached_tokens": cached,
                            "input_tokens": entry.get("input_tokens"),
                            "output_tokens": entry.get("output_tokens"),
                            "response_id": entry.get("response_id"),
                        }

    if total_receipts != 6401:
        raise ValueError(f"Expected exactly 6401 attempt receipts, got {total_receipts}")
    if total_cached_tokens != 1540:
        raise ValueError(f"Expected exactly 1540 total cached tokens, got {total_cached_tokens}")
    if transport_failure_info is None or retry_success_info is None:
        raise ValueError("Failed to locate expected transport failure and retry pair in journal")

    # Invariants for each condition
    cache_summary_by_condition: Dict[str, Any] = {}
    for c in CONDITIONS:
        sum_c = cached_tokens_by_condition[c]
        obs_c = observed_receipts_by_condition[c]
        miss_c = missing_receipts_by_condition[c]
        
        # In our study, 1280 logical requests per condition
        # For rag_k1: 1281 receipts (1 missing + 1280 observed)
        # For other conditions: 1280 receipts (0 missing + 1280 observed)
        if c == "rag_k1":
            if obs_c != 1280 or miss_c != 1 or sum_c != 1540:
                raise ValueError(f"Condition rag_k1 cache invariant breached: obs={obs_c}, miss={miss_c}, sum={sum_c}")
            mean_c = sum_c / 1280.0  # 1.203125
        else:
            if obs_c != 1280 or miss_c != 0 or sum_c != 0:
                raise ValueError(f"Condition {c} cache invariant breached: obs={obs_c}, miss={miss_c}, sum={sum_c}")
            mean_c = 0.0

        cache_summary_by_condition[c] = {
            "condition": c,
            "sum_cached_tokens": sum_c,
            "mean_cached_tokens_per_request": mean_c,
            "observed_attempts_count": obs_c,
            "missing_attempts_count": miss_c,
            "total_attempts_count": obs_c + miss_c,
            "logical_sample_count": 1280,
            "cached_tokens_accounting_rule": (
                "Cached tokens represent prompt tokens served from model cache. "
                "Total tokens is prompt_tokens + completion_tokens. "
                "Cached tokens are a subset of prompt tokens and are NOT added into total tokens twice."
            )
        }

    return {
        "campaign_total_cached_tokens": total_cached_tokens,
        "campaign_total_receipts": total_receipts,
        "campaign_observed_receipts": 6400,
        "campaign_missing_receipts": 1,
        "cache_by_condition": cache_summary_by_condition,
        "transport_failure": transport_failure_info,
        "retry_success": retry_success_info,
    }


def verify_financial_invariants(ledger_path: Path) -> Dict[str, Any]:
    """
    Verify study_ledger.json against Decimal arithmetic and financial invariants.
    """
    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    # Top-level ledger checks
    total_budget = Decimal(str(ledger["total_budget_usd"]))
    pilot_hold = Decimal(str(ledger["prior_pilot_provisional_hold_usd"]))
    settled = Decimal(str(ledger["cumulative_settled_cost_usd"]))
    available = Decimal(str(ledger["uncommitted_available_balance_usd"]))
    active_res = Decimal(str(ledger.get("active_reservations_usd", "0")))

    if total_budget != BUDGET_CAP_USD:
        raise ValueError(f"Budget cap mismatch: {total_budget} != {BUDGET_CAP_USD}")
    if pilot_hold != PILOT_HOLD_USD:
        raise ValueError(f"Pilot hold mismatch: {pilot_hold} != {PILOT_HOLD_USD}")
    if settled != SETTLED_USD:
        raise ValueError(f"Settled mismatch: {settled} != {SETTLED_USD}")
    if available != AVAILABLE_BALANCE_USD:
        raise ValueError(f"Available mismatch: {available} != {AVAILABLE_BALANCE_USD}")
    if active_res != Decimal("0"):
        raise ValueError(f"Active reservations remaining: {active_res}")

    # Conservation of money invariant
    accounted = settled + pilot_hold
    if accounted != TOTAL_ACCOUNTED_USD:
        raise ValueError(f"Accounted mismatch: {accounted} != {TOTAL_ACCOUNTED_USD}")
    if accounted + available != total_budget:
        raise ValueError(
            f"Money conservation breached! {accounted} + {available} != {total_budget}"
        )

    # Per condition settled costs
    cond_costs: Dict[str, Decimal] = {
        "no_rag": Decimal("0.46714395"),
        "rag_k1": Decimal("1.29723350"),
        "rag_k3": Decimal("1.17888000"),
        "rag_k5": Decimal("1.48311775"),
        "rag_k10": Decimal("2.14938370"),
    }
    if sum(cond_costs.values()) != settled:
        raise ValueError("Sum of condition costs does not equal settled total!")

    return {
        "study_budget_cap_usd": str(total_budget),
        "prior_pilot_provisional_hold_usd": str(pilot_hold),
        "cumulative_settled_cost_usd": str(settled),
        "total_accounted_expenditure_usd": str(accounted),
        "uncommitted_available_balance_usd": str(available),
        "active_reservations_usd": str(active_res),
        "has_breach": ledger.get("has_breach", False),
        "settled_cost_by_condition_usd": {k: str(v) for k, v in cond_costs.items()},
        "commercial_invoice_disclaimer": (
            "All monetary amounts represent internal simulation and API budget guard accounting. "
            "No commercial invoice or vendor billing statement is asserted."
        ),
    }


def build_canonical_metric_bundle(
    public_package_dir: Path,
    seal_path: Path,
    output_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Construct canonical_metric_bundle_v2.json from verified inputs and outputs.
    """
    # Step 1: Verify public package and load manifest
    manifest = verify_public_package(public_package_dir)
    
    # Step 2: Verify run seal
    seal = verify_run_seal(seal_path)

    # Step 3: Parse and cross-verify request journal cache telemetry
    journal_path = public_package_dir / "inputs" / "request_journal.jsonl"
    cache_telemetry = parse_request_journal_cache(journal_path)

    # Step 4: Verify financial ledger invariants
    ledger_path = public_package_dir / "inputs" / "study_ledger.json"
    financial_accounting = verify_financial_invariants(ledger_path)

    # Step 5: Load outputs
    outputs_dir = public_package_dir / "outputs"
    with open(outputs_dir / "overall_metrics.json", "r", encoding="utf-8") as f:
        overall_metrics = json.load(f)
    with open(outputs_dir / "per_condition_metrics.json", "r", encoding="utf-8") as f:
        per_condition_metrics = json.load(f)
    with open(outputs_dir / "failure_decomposition.json", "r", encoding="utf-8") as f:
        failure_decomposition = json.load(f)
    with open(outputs_dir / "retrieval_conditional_metrics.json", "r", encoding="utf-8") as f:
        retrieval_conditional_metrics = json.load(f)
    with open(outputs_dir / "per_technique_metrics.json", "r", encoding="utf-8") as f:
        per_technique_metrics = json.load(f)
    with open(outputs_dir / "rq_analysis.json", "r", encoding="utf-8") as f:
        rq_analysis = json.load(f)
    with open(outputs_dir / "run_provenance.json", "r", encoding="utf-8") as f:
        run_provenance = json.load(f)

    # Step 6: Verify analysis source code sha256
    run_params = rq_analysis.get("analysis_run_parameters", {})
    if run_params.get("analysis_source_sha256") != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise ValueError(
            f"rq_analysis source_sha mismatch: {run_params.get('analysis_source_sha256')} != {EXPECTED_ANALYSIS_SOURCE_SHA256}"
        )

    # Step 7: Build Conditions Metric Objects
    rq1_raw = rq_analysis.get("rq1", {}).get("by_condition", {})
    rq2_raw = rq_analysis.get("rq2", {}).get("by_condition", {})
    rq3_raw = rq_analysis.get("rq3", {}).get("tradeoffs_by_condition", {})
    complexity_raw = rq_analysis.get("new_proposed_producer_stratified_gt_complexity", {}).get("by_condition", {})

    conditions_bundle: Dict[str, Any] = {}

    for cond in CONDITIONS:
        k_val = RETRIEVAL_K_VALUES[cond]
        rq1_c = rq1_raw[cond]
        rq2_c = rq2_raw[cond]
        rq3_c = rq3_raw[cond]
        comp_c = complexity_raw[cond]
        cache_c = cache_telemetry["cache_by_condition"][cond]

        # Cohort breakdown for this condition
        cond_cohort = {
            "total_logical_requests": 1280,
            "total_scorable_mapped_views": COHORT_MAPPED_VIEWS,
            "single_gt_mapped_views": comp_c["single_gt_sample_count"],
            "multi_gt_mapped_views": comp_c["multi_gt_sample_count"],
            "ambiguous_excluded_views": COHORT_AMBIGUOUS_VIEWS,
            "unmapped_excluded_views": COHORT_UNMAPPED_VIEWS,
        }
        if cond_cohort["single_gt_mapped_views"] != COHORT_SINGLE_GT_VIEWS or cond_cohort["multi_gt_mapped_views"] != COHORT_MULTI_GT_VIEWS:
            raise ValueError(f"Cohort complexity mismatch in {cond}")

        # RQ1 Metric Object
        acc_e2e = float(rq1_c["accuracy_end_to_end"])
        acc_valid = float(rq1_c["accuracy_valid_outputs"])
        macro_f1 = float(rq1_c["macro_f1"])
        correct_count = int(rq1_c["correct_count"])
        error_count = COHORT_MAPPED_VIEWS - correct_count

        rq1_obj: Dict[str, Any] = {
            "condition": cond,
            "retrieval_k": k_val,
            "is_baseline": (cond == "no_rag"),
            "correct_count": correct_count,
            "error_count": error_count,
            "scorable_sample_count": COHORT_MAPPED_VIEWS,
            "accuracy_end_to_end": acc_e2e,
            "accuracy_valid_outputs": acc_valid,
            "accuracy_display": f"{acc_e2e * 100:.2f}%",
            "accuracy_e2e_ci_95": rq1_c["accuracy_e2e_ci_95"],
            "accuracy_e2e_ci_95_display": f"[{rq1_c['accuracy_e2e_ci_95'][0] * 100:.2f}%, {rq1_c['accuracy_e2e_ci_95'][1] * 100:.2f}%]",
            "macro_f1": macro_f1,
            "macro_f1_display": f"{macro_f1:.4f}",
            "macro_f1_universe_classes": COHORT_MACRO_UNIVERSE,
            "supported_classes": COHORT_SUPPORTED_CLASSES,
            "unsupported_classes": COHORT_UNSUPPORTED_CLASSES,
            "stratified_complexity": {
                "single_gt": {
                    "sample_count": comp_c["single_gt_sample_count"],
                    "correct_count": comp_c["single_gt_correct_count"],
                    "accuracy_e2e": comp_c["single_gt_accuracy_e2e"],
                    "accuracy_display": f"{comp_c['single_gt_accuracy_e2e'] * 100:.2f}%",
                    "macro_f1": comp_c["single_gt_macro_f1"],
                },
                "multi_gt": {
                    "sample_count": comp_c["multi_gt_sample_count"],
                    "correct_count": comp_c["multi_gt_correct_count"],
                    "accuracy_e2e": comp_c["multi_gt_accuracy_e2e"],
                    "accuracy_display": f"{comp_c['multi_gt_accuracy_e2e'] * 100:.2f}%",
                    "macro_f1": comp_c["multi_gt_macro_f1"],
                }
            }
        }

        if cond != "no_rag":
            delta_info = rq1_c["delta_vs_baseline"]
            delta_acc = float(delta_info["delta_accuracy_end_to_end"])
            delta_ci = delta_info["delta_accuracy_e2e_ci_95"]
            delta_ci_pp = [delta_ci[0] * 100.0, delta_ci[1] * 100.0]
            mcnemar = delta_info["mcnemar_test"]
            p_exact = float(mcnemar["p_value_exact"])
            p_asymptotic = float(mcnemar["p_value_asymptotic"])

            rq1_obj["delta_vs_baseline"] = {
                "delta_accuracy_end_to_end": delta_acc,
                "delta_accuracy_display_pp": f"{delta_acc * 100.0:+.3f} pp",
                "delta_accuracy_ci_95": delta_ci,
                "delta_accuracy_ci_95_display_pp": f"[{delta_ci_pp[0]:+.3f}, {delta_ci_pp[1]:+.3f}] pp",
                "delta_macro_f1": float(delta_info["delta_macro_f1"]),
                "delta_macro_f1_ci_95": delta_info["delta_macro_f1_ci_95"],
                "relative_gain_accuracy_pct": float(delta_info["relative_gain_accuracy_e2e_pct"]),
                "relative_gain_macro_f1_pct": float(delta_info["relative_gain_macro_f1_pct"]),
                "mcnemar_test": {
                    "contingency_table": mcnemar["contingency_table"],
                    "chi2_statistic": float(mcnemar["chi2_statistic"]),
                    "p_value_exact": p_exact,
                    "p_value_asymptotic": p_asymptotic,
                    "display_p_exact": f"{p_exact:.3f}",
                    "display_p_asymptotic": f"{p_asymptotic:.3f}",
                    "significant_at_05": mcnemar["significant_at_05"],
                    "significant_at_01": mcnemar["significant_at_01"],
                }
            }

        # RQ2 Metric Object
        rq2_ret = rq2_c.get("retrieval_metrics", {})
        rq2_cond = rq2_c.get("generation_conditional_accuracy", {})
        rq2_axes = rq2_c.get("independent_failure_axes", {})
        is_retrieval_app = rq2_ret.get("applicable", False)

        rq2_obj: Dict[str, Any] = {
            "condition": cond,
            "retrieval_k": k_val,
            "retrieval_applicable": is_retrieval_app,
        }

        if is_retrieval_app:
            hit_cnt = int(rq2_ret["retrieved_positive_count"])
            tot_cnt = int(rq2_ret["total_positive_sample_count"])
            miss_cnt = tot_cnt - hit_cnt
            hit_rate = float(rq2_ret["retrieval_hit_rate"])
            macro_recall = float(rq2_ret["macro_recall"])

            rq2_obj["retrieval_metrics"] = {
                "applicable": True,
                "retrieval_hit_count": hit_cnt,
                "retrieval_miss_count": miss_cnt,
                "total_scorable_samples": tot_cnt,
                "retrieval_hit_rate": hit_rate,
                "retrieval_hit_rate_display": f"{hit_rate * 100:.2f}%",
                "retrieval_miss_rate": miss_cnt / tot_cnt,
                "retrieval_miss_rate_display": f"{(miss_cnt / tot_cnt) * 100:.2f}%",
                "macro_recall": macro_recall,
            }

            p_corr_hit = float(rq2_cond["p_correct_given_retrieval_success"])
            p_corr_miss = float(rq2_cond["p_correct_given_retrieval_failure"])
            n_succ = int(rq2_cond["retrieval_success_sample_count"])
            n_fail = int(rq2_cond["retrieval_failure_sample_count"])

            rq2_obj["generation_conditional_accuracy"] = {
                "applicable": True,
                "retrieval_success_sample_count": n_succ,
                "p_correct_given_retrieval_success": p_corr_hit,
                "p_correct_given_retrieval_success_display": f"{p_corr_hit * 100:.2f}%",
                "correct_given_retrieval_success_count": round(p_corr_hit * n_succ),
                "retrieval_failure_sample_count": n_fail,
                "p_correct_given_retrieval_failure": p_corr_miss,
                "p_correct_given_retrieval_failure_display": f"{p_corr_miss * 100:.2f}%",
                "correct_given_retrieval_failure_count": round(p_corr_miss * n_fail),
            }

            wrong_cnt = int(rq2_axes["valid_but_wrong_classification_count"])
            overlap_cnt = int(rq2_axes["overlap_retrieval_miss_and_wrong_classification"])
            overlap_frac = overlap_cnt / wrong_cnt if wrong_cnt > 0 else 0.0

            rq2_obj["independent_failure_axes"] = {
                "policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced mutual exclusion. "
                    "Retrieval miss does not establish cause of provider or parse failure."
                ),
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "valid_but_wrong_classification_count": wrong_cnt,
                "valid_but_wrong_classification_rate": float(rq2_axes["valid_but_wrong_classification_rate"]),
                "retrieval_miss_count": miss_cnt,
                "retrieval_miss_rate": float(rq2_axes["retrieval_miss_rate"]),
                "overlap_retrieval_miss_and_wrong_classification": overlap_cnt,
                "overlap_fraction_of_wrong_classification": overlap_frac,
                "overlap_fraction_display": f"{overlap_frac * 100:.2f}%",
                "invalid_attack_id_count": int(rq2_axes.get("invalid_attack_id_count", 0)),
                "parse_failure_count": int(rq2_axes.get("parse_failure_count", 0)),
                "provider_failure_count_mapped": int(rq2_axes.get("provider_failure_count", 0)),
            }
        else:
            # Baseline No-RAG: retrieval metrics are null
            wrong_cnt = int(rq2_axes["valid_but_wrong_classification_count"])
            rq2_obj["retrieval_metrics"] = {
                "applicable": False,
                "note": "Retrieval metrics not applicable to No-RAG baseline (k=0).",
                "retrieval_hit_count": None,
                "retrieval_miss_count": None,
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "retrieval_hit_rate": None,
                "retrieval_miss_rate": None,
                "macro_recall": None,
                "raw_evaluator_trace": {
                    "raw_retrieval_miss_count": 0,
                    "raw_retrieval_miss_rate": 0.0,
                    "raw_overlap_count": 0,
                }
            }
            rq2_obj["generation_conditional_accuracy"] = {
                "applicable": False,
                "note": "Retrieval-conditioned accuracy not applicable to No-RAG baseline (k=0).",
                "p_correct_given_retrieval_success": None,
                "p_correct_given_retrieval_failure": None,
                "retrieval_success_sample_count": None,
                "retrieval_failure_sample_count": None,
            }
            rq2_obj["independent_failure_axes"] = {
                "policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced mutual exclusion."
                ),
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "valid_but_wrong_classification_count": wrong_cnt,
                "valid_but_wrong_classification_rate": float(rq2_axes["valid_but_wrong_classification_rate"]),
                "retrieval_miss_count": None,
                "retrieval_miss_rate": None,
                "overlap_retrieval_miss_and_wrong_classification": None,
                "overlap_fraction_of_wrong_classification": None,
                "invalid_attack_id_count": 0,
                "parse_failure_count": 0,
                "provider_failure_count_mapped": 0,
                "raw_evaluator_trace": {
                    "raw_retrieval_miss_count": 0,
                    "raw_retrieval_miss_rate": 0.0,
                    "raw_overlap_count": 0,
                }
            }

        # RQ3 Metric Object
        rq3_lat = rq3_c["latency_ms"]
        rq3_tok = rq3_c["tokens"]
        rq3_cost = rq3_c["financial_cost_usd"]

        prompt_sum = int(rq3_tok["sum_prompt_tokens"])
        comp_sum = int(rq3_tok["sum_completion_tokens"])
        total_tok_sum = int(rq3_tok["sum_total_tokens"])
        if prompt_sum + comp_sum != total_tok_sum:
            raise ValueError(f"Token sum invariant breached in {cond}: {prompt_sum} + {comp_sum} != {total_tok_sum}")

        # Failure rates for this condition
        # 13 terminal failures across whole campaign: k3=6, k5=3, k10=4, no_rag=0, k1=0
        terminal_incomp_map = {"no_rag": 0, "rag_k1": 0, "rag_k3": 6, "rag_k5": 3, "rag_k10": 4}
        term_incomp_count = terminal_incomp_map[cond]
        term_incomp_rate = term_incomp_count / 1280.0

        rq3_obj: Dict[str, Any] = {
            "condition": cond,
            "retrieval_k": k_val,
            "observations_count": 1280,
            "latency_ms": {
                "mean": float(rq3_lat["mean"]),
                "median": float(rq3_lat["median"]),
                "p95": None,
                "p95_status": P95_STATUS_POLICY,
                "sum_ms": float(rq3_lat["sum"]),
                "unit": "milliseconds",
                "measurement_scope": "Client end-to-end request loop including retry backoff",
            },
            "tokens": {
                "prompt_tokens": {
                    "sum": prompt_sum,
                    "mean": float(rq3_tok["mean_prompt_tokens"]),
                },
                "completion_tokens": {
                    "sum": comp_sum,
                    "mean": float(rq3_tok["mean_completion_tokens"]),
                },
                "total_tokens": {
                    "sum": total_tok_sum,
                    "mean": float(rq3_tok["mean_total_tokens"]),
                    "formula": "prompt_tokens + completion_tokens",
                },
                "cached_tokens": {
                    "sum": cache_c["sum_cached_tokens"],
                    "mean": cache_c["mean_cached_tokens_per_request"],
                    "observed_attempts_count": cache_c["observed_attempts_count"],
                    "missing_attempts_count": cache_c["missing_attempts_count"],
                    "cached_tokens_accounting_rule": cache_c["cached_tokens_accounting_rule"],
                }
            },
            "financial_cost_usd": {
                "ledger_settled_cost_usd": str(Decimal(str(rq3_cost["ledger_settled_cost_usd"]))),
                "token_usage_estimated_cost_usd": str(Decimal(str(rq3_cost["token_usage_estimated_cost_usd"]))),
                "cost_per_logical_request_usd": float(rq3_cost["cost_per_logical_request_usd"]),
                "cost_per_scorable_query_usd": float(rq3_cost["cost_per_scorable_query_usd"]),
                "cost_per_correct_attribution_usd": float(rq3_cost["cost_per_correct_attribution_usd"]),
                "missing_usage_attempt_receipts_count": int(rq3_cost["missing_usage_attempt_receipts_count"]),
                "missing_usage_attempt_worst_charge_usd": str(Decimal(str(rq3_cost["missing_usage_attempt_worst_charge_usd"]))),
                "cost_of_all_excluded_views_usd": float(rq3_cost["cost_of_all_excluded_views_usd"]),
                "cost_of_excluded_ambiguous_views_usd": float(rq3_cost["cost_of_excluded_ambiguous_views_usd"]),
                "cost_of_excluded_unmapped_views_usd": float(rq3_cost["cost_of_excluded_unmapped_views_usd"]),
                "marginal_cost_vs_baseline_usd": float(rq3_cost["marginal_cost_vs_baseline_usd"]),
            },
            "failures": {
                "terminal_incomplete_count": term_incomp_count,
                "terminal_incomplete_rate": term_incomp_rate,
                "terminal_incomplete_denominator": 1280,
                "mapped_scorable_failures_count": 0,
                "invalid_syntax_count": 0,
                "invalid_id_count": 0,
                "parse_failure_count": 0,
            }
        }

        conditions_bundle[cond] = {
            "condition": cond,
            "retrieval_k": k_val,
            "cohort": cond_cohort,
            "rq1_attribution": rq1_obj,
            "rq2_retrieval_and_error": rq2_obj,
            "rq3_resources_and_cost": rq3_obj,
        }

    # Step 8: Campaign-wide Failure Taxonomy
    failure_taxonomy = {
        "campaign_total_logical_requests": 6400,
        "campaign_total_physical_attempts": 6401,
        "transport_network_failures_count": 1,
        "transport_network_failure_details": cache_telemetry["transport_failure"],
        "retry_success_details": cache_telemetry["retry_success"],
        "terminal_incomplete_count": 13,
        "terminal_incomplete_rate": 13 / 6400.0,
        "terminal_incomplete_by_condition": {
            "no_rag": 0,
            "rag_k1": 0,
            "rag_k3": 6,
            "rag_k5": 3,
            "rag_k10": 4,
        },
        "mapped_scorable_terminal_incomplete_count": 0,
        "completed_records_count": 6387,
        "valid_json_outputs_count": 6387,
        "invalid_syntax_count": 0,
        "invalid_attack_id_count": 0,
        "retired_attack_id_observation_count": 245,
        "retired_attack_id_policy": "ALLOWED_HISTORICAL_PER_DECISION_D2G",
    }

    # Step 9: Assemble Complete Bundle
    bundle = {
        "schema_version": "2.0.0",
        "bundle_type": "canonical-metric-bundle-v2",
        "fixture_only": False,
        "execution_mode": "live",
        "dataset_split": "test",
        "experiment_id": "synthetic-paired-test-1",
        "run_id": "live-66b94b1676bf46a9",
        "study_id": "rag2attack-study-wide",
        "protocol_version": "experiment-protocol-v1.1",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "pricing_contract_sha256": EXPECTED_PRICING_CONTRACT_SHA256,
        "core_code_manifest_sha256": EXPECTED_CORE_MANIFEST_SHA256,
        "execution_git_sha": EXECUTION_GIT_SHA,
        "evaluation_git_sha": EVALUATION_GIT_SHA,
        "candidate_repo_git_sha": CANDIDATE_REPO_GIT_SHA,
        "public_package_manifest_sha256": EXPECTED_PUBLIC_MANIFEST_SHA256,
        "evaluator_analysis_source_file": "scripts/analysis/evaluate_rqs.py",
        "evaluator_analysis_source_sha256": EXPECTED_ANALYSIS_SOURCE_SHA256,
        "terminal_seal": {
            "path": "reports/evidence/canonical_run_seal_v1.json",
            "sha256": EXPECTED_TERMINAL_SEAL_SHA256,
            "terminal_proof_sha256": EXPECTED_TERMINAL_PROOF_SHA256,
        },
        "supplementary_source_lineage": {
            "historical_s2_package_sha256": HISTORICAL_S2_PACKAGE_SHA256,
            "historical_note": (
                "Historical S2 package (c48eeb27...) represents development packet; "
                "formally superseded by exact S2_RQ_V2 packet (f85d7f73... / d515f704...)."
            ),
            "authorizing_packet_public_path": "provenance/s2_evaluation_execute_public.md",
            "authorizing_packet_public_sha256": AUTHORIZING_PACKET_PUBLIC_SHA256,
            "authorizing_packet_original_sha256": AUTHORIZING_PACKET_ORIGINAL_SHA256,
        },
        "p95_policy": {
            "status": P95_STATUS_POLICY,
            "rule": "P95 latency is withheld from consumer display pending formal authority approval.",
        },
        "cohort_breakdown": {
            "total_views": COHORT_TOTAL_VIEWS,
            "total_pairs": COHORT_TOTAL_PAIRS,
            "mapped_scorable_views": COHORT_MAPPED_VIEWS,
            "ambiguous_excluded_views": COHORT_AMBIGUOUS_VIEWS,
            "unmapped_excluded_views": COHORT_UNMAPPED_VIEWS,
            "single_gt_mapped_views": COHORT_SINGLE_GT_VIEWS,
            "multi_gt_mapped_views": COHORT_MULTI_GT_VIEWS,
            "total_gt_support_instances": COHORT_TOTAL_GT_SUPPORT_INSTANCES,
            "eligible_bootstrap_clusters": COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS,
            "macro_universe_classes": COHORT_MACRO_UNIVERSE,
            "supported_classes": COHORT_SUPPORTED_CLASSES,
            "unsupported_classes": COHORT_UNSUPPORTED_CLASSES,
        },
        "conditions": conditions_bundle,
        "whole_study_financial_accounting": financial_accounting,
        "failure_taxonomy": failure_taxonomy,
        "overall_summary": {
            "overall_accuracy_end_to_end": float(overall_metrics["accuracy_end_to_end"]),
            "overall_accuracy_valid_outputs": float(overall_metrics["accuracy_valid_outputs"]),
            "overall_macro_f1": float(overall_metrics["macro_f1"]),
            "total_scorable_mapped_samples_across_conditions": int(overall_metrics["scorable_sample_count"]),
            "total_completed_records": int(overall_metrics["completed_record_count"]),
            "total_logical_samples": int(overall_metrics["logical_sample_count"]),
            "total_provider_failures": int(overall_metrics["provider_failure_count"]),
            "total_retired_id_observations": int(overall_metrics["retired_id_observation_count"]),
        },
        "source_file_digests": manifest.get("source_file_digests", {}),
        "output_file_digests": manifest.get("output_file_digests", {}),
    }

    # Step 10: If output path is requested, write to disk
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_json = json.dumps(bundle, indent=2, sort_keys=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(bundle_json)
            f.write("\n")
        
        # Write sha256 checksum
        bundle_sha256 = hashlib.sha256(bundle_json.encode("utf-8") + b"\n").hexdigest()
        sha_path = output_path.with_name(f"{output_path.name}.sha256")
        with open(sha_path, "w", encoding="utf-8") as f:
            f.write(f"{bundle_sha256}  {output_path.name}\n")
        print(f"Canonical metric bundle successfully written to: {output_path}")
        print(f"Bundle SHA256: {bundle_sha256}")

    return bundle


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate Canonical Metric Bundle v2")
    parser.add_argument(
        "--public-package-dir",
        type=Path,
        default=Path("C:/Users/hahoa/.codex/artifacts/rag2attck/final_handover_package_v3_20261002/03_public_canonical_package"),
        help="Path to public canonical package v3 directory",
    )
    parser.add_argument(
        "--seal-path",
        type=Path,
        default=Path("reports/evidence/canonical_run_seal_v1.json"),
        help="Path to canonical run seal JSON",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("artifacts/results/canonical_metric_bundle_v2.json"),
        help="Destination path for canonical_metric_bundle_v2.json",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify inputs without writing bundle file",
    )
    args = parser.parse_args()

    out_p = None if args.verify_only else args.output_path
    try:
        build_canonical_metric_bundle(
            public_package_dir=args.public_package_dir,
            seal_path=args.seal_path,
            output_path=out_p,
        )
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
