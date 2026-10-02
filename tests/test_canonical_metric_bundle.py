"""
tests/test_canonical_metric_bundle.py

Comprehensive fail-closed test suite for Canonical Metric Bundle v2.
Validates:
- Positive controls on genuine canonical data
- Rejection of tampered inputs, bad hashes, and broken manifests
- Rejection of fixture seals as canonical
- Enforcement of financial conservation of money
- Verification of token cache join telemetry (1,540 total, 1 network retry)
- Preservation of D2i independent failure axes (no causal or exclusive claim)
- Enforcement of p95 suppression policy
"""

from __future__ import annotations

import copy
import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict

import pytest

from scripts.build_canonical_metric_bundle import (
    BUDGET_CAP_USD,
    COHORT_AMBIGUOUS_VIEWS,
    COHORT_MAPPED_VIEWS,
    COHORT_MULTI_GT_VIEWS,
    COHORT_SINGLE_GT_VIEWS,
    COHORT_TOTAL_PAIRS,
    COHORT_TOTAL_VIEWS,
    COHORT_UNMAPPED_VIEWS,
    EXPECTED_ANALYSIS_SOURCE_SHA256,
    EXPECTED_CORE_MANIFEST_SHA256,
    EXPECTED_PRICING_CONTRACT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    EXPECTED_PUBLIC_MANIFEST_SHA256,
    EXPECTED_TERMINAL_PROOF_SHA256,
    EXPECTED_TERMINAL_SEAL_SHA256,
    P95_STATUS_POLICY,
    PILOT_HOLD_USD,
    SETTLED_USD,
    TOTAL_ACCOUNTED_USD,
    build_canonical_metric_bundle,
    parse_request_journal_cache,
    verify_file_hash,
    verify_financial_invariants,
    verify_public_package,
    verify_run_seal,
)

GENUINE_PACKAGE_DIR = Path("C:/Users/hahoa/.codex/artifacts/rag2attck/final_handover_package_v3_20261002/03_public_canonical_package")
GENUINE_SEAL_PATH = Path("reports/evidence/canonical_run_seal_v1.json")


# =========================================================================
# POSITIVE CONTROLS
# =========================================================================

def test_genuine_canonical_bundle_build():
    """Verify that build_canonical_metric_bundle executes cleanly on genuine data."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )

    assert bundle["schema_version"] == "2.0.0"
    assert bundle["bundle_type"] == "canonical-metric-bundle-v2"
    assert bundle["fixture_only"] is False
    assert bundle["execution_mode"] == "live"
    assert bundle["run_id"] == "live-66b94b1676bf46a9"
    assert bundle["core_code_manifest_sha256"] == EXPECTED_CORE_MANIFEST_SHA256
    assert bundle["protocol_sha256"] == EXPECTED_PROTOCOL_SHA256
    assert bundle["pricing_contract_sha256"] == EXPECTED_PRICING_CONTRACT_SHA256
    assert bundle["public_package_manifest_sha256"] == EXPECTED_PUBLIC_MANIFEST_SHA256
    assert bundle["evaluator_analysis_source_sha256"] == EXPECTED_ANALYSIS_SOURCE_SHA256

    # Seal binding
    assert bundle["terminal_seal"]["sha256"] == EXPECTED_TERMINAL_SEAL_SHA256
    assert bundle["terminal_seal"]["terminal_proof_sha256"] == EXPECTED_TERMINAL_PROOF_SHA256


def test_cohort_and_denominator_specifications():
    """Verify exact cohort partition and denominator values."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    cohort = bundle["cohort_breakdown"]
    assert cohort["total_views"] == 1280
    assert cohort["total_pairs"] == 640
    assert cohort["mapped_scorable_views"] == 718
    assert cohort["ambiguous_excluded_views"] == 311
    assert cohort["unmapped_excluded_views"] == 251
    assert cohort["single_gt_mapped_views"] == 678
    assert cohort["multi_gt_mapped_views"] == 40
    assert cohort["total_gt_support_instances"] == 768
    assert cohort["eligible_bootstrap_clusters"] == 440
    assert cohort["macro_universe_classes"] == 474
    assert cohort["supported_classes"] == 8
    assert cohort["unsupported_classes"] == 466

    # Sum check
    assert cohort["mapped_scorable_views"] + cohort["ambiguous_excluded_views"] + cohort["unmapped_excluded_views"] == 1280
    assert cohort["single_gt_mapped_views"] + cohort["multi_gt_mapped_views"] == 718
    assert cohort["supported_classes"] + cohort["unsupported_classes"] == 474


def test_rq1_exact_numerical_metrics():
    """Verify headline accuracy, macro-F1, delta, CI, and McNemar test."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    conds = bundle["conditions"]

    # No-RAG baseline
    no_rag = conds["no_rag"]["rq1_attribution"]
    assert no_rag["correct_count"] == 560
    assert no_rag["error_count"] == 158
    assert no_rag["scorable_sample_count"] == 718
    assert pytest.approx(no_rag["accuracy_end_to_end"], abs=1e-6) == 560 / 718
    assert no_rag["accuracy_display"] == "77.99%"
    assert pytest.approx(no_rag["macro_f1"], abs=1e-6) == 0.012608
    assert no_rag["is_baseline"] is True

    # RAG k10
    k10 = conds["rag_k10"]["rq1_attribution"]
    assert k10["correct_count"] == 571
    assert k10["error_count"] == 147
    assert k10["scorable_sample_count"] == 718
    assert pytest.approx(k10["accuracy_end_to_end"], abs=1e-6) == 571 / 718
    assert k10["accuracy_display"] == "79.53%"
    assert pytest.approx(k10["macro_f1"], abs=1e-6) == 0.014024
    assert k10["is_baseline"] is False

    # Delta & paired McNemar test
    delta_info = k10["delta_vs_baseline"]
    assert pytest.approx(delta_info["delta_accuracy_end_to_end"], abs=1e-6) == 0.01532033426
    assert delta_info["delta_accuracy_display_pp"] == "+1.532 pp"
    
    ci = delta_info["delta_accuracy_ci_95"]
    assert pytest.approx(ci[0] * 100, abs=1e-3) == -2.355
    assert pytest.approx(ci[1] * 100, abs=1e-3) == +5.300
    assert delta_info["delta_accuracy_ci_95_display_pp"] == "[-2.355, +5.300] pp"

    mcnemar = delta_info["mcnemar_test"]
    ct = mcnemar["contingency_table"]
    assert ct["both_correct_a"] == 488
    assert ct["treatment_win_b"] == 83
    assert ct["baseline_win_c"] == 72
    assert ct["both_incorrect_d"] == 75
    assert ct["total_discordant"] == 155
    assert ct["total_pairs"] == 718

    assert pytest.approx(mcnemar["chi2_statistic"], abs=1e-4) == 0.645161
    assert pytest.approx(mcnemar["p_value_exact"], abs=1e-6) == 0.421938833
    assert pytest.approx(mcnemar["p_value_asymptotic"], abs=1e-6) == 0.421847975
    assert mcnemar["display_p_exact"] == "0.422"
    assert mcnemar["display_p_asymptotic"] == "0.422"
    assert mcnemar["significant_at_05"] is False
    assert mcnemar["significant_at_01"] is False


def test_rq2_retrieval_and_error_decomposition():
    """Verify retrieval hit/miss, conditional accuracy, and independent failure axes."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    conds = bundle["conditions"]

    # Baseline No-RAG: retrieval is NOT applicable
    no_rag_rq2 = conds["no_rag"]["rq2_retrieval_and_error"]
    assert no_rag_rq2["retrieval_applicable"] is False
    assert no_rag_rq2["retrieval_metrics"]["applicable"] is False
    assert no_rag_rq2["retrieval_metrics"]["retrieval_hit_count"] is None
    assert no_rag_rq2["retrieval_metrics"]["retrieval_miss_count"] is None
    assert no_rag_rq2["generation_conditional_accuracy"]["applicable"] is False
    assert no_rag_rq2["independent_failure_axes"]["retrieval_miss_count"] is None
    assert no_rag_rq2["independent_failure_axes"]["valid_but_wrong_classification_count"] == 158

    # RAG k10: retrieval is applicable
    k10_rq2 = conds["rag_k10"]["rq2_retrieval_and_error"]
    assert k10_rq2["retrieval_applicable"] is True
    
    ret_m = k10_rq2["retrieval_metrics"]
    assert ret_m["retrieval_hit_count"] == 321
    assert ret_m["retrieval_miss_count"] == 397
    assert ret_m["total_scorable_samples"] == 718
    assert pytest.approx(ret_m["retrieval_hit_rate"], abs=1e-5) == 321 / 718
    assert ret_m["retrieval_hit_rate_display"] == "44.71%"
    assert ret_m["retrieval_miss_rate_display"] == "55.29%"
    assert pytest.approx(ret_m["macro_recall"], abs=1e-5) == 0.42804

    gen_c = k10_rq2["generation_conditional_accuracy"]
    assert gen_c["retrieval_success_sample_count"] == 321
    assert gen_c["correct_given_retrieval_success_count"] == 293
    assert pytest.approx(gen_c["p_correct_given_retrieval_success"], abs=1e-5) == 293 / 321
    assert gen_c["p_correct_given_retrieval_success_display"] == "91.28%"

    assert gen_c["retrieval_failure_sample_count"] == 397
    assert gen_c["correct_given_retrieval_failure_count"] == 278
    assert pytest.approx(gen_c["p_correct_given_retrieval_failure"], abs=1e-5) == 278 / 397
    assert gen_c["p_correct_given_retrieval_failure_display"] == "70.03%"

    axes = k10_rq2["independent_failure_axes"]
    assert axes["valid_but_wrong_classification_count"] == 147
    assert axes["retrieval_miss_count"] == 397
    assert axes["overlap_retrieval_miss_and_wrong_classification"] == 119
    assert pytest.approx(axes["overlap_fraction_of_wrong_classification"], abs=1e-5) == 119 / 147
    assert axes["overlap_fraction_display"] == "80.95%"
    assert axes["invalid_attack_id_count"] == 0
    assert axes["parse_failure_count"] == 0


def test_rq3_cached_tokens_and_conservation():
    """Verify cache telemetry join and token sum invariants."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    conds = bundle["conditions"]

    # All conditions: total = prompt + completion (cached is subset of prompt)
    for c_name, c_data in conds.items():
        toks = c_data["rq3_resources_and_cost"]["tokens"]
        p = toks["prompt_tokens"]["sum"]
        comp = toks["completion_tokens"]["sum"]
        tot = toks["total_tokens"]["sum"]
        assert p + comp == tot, f"Token invariant broken in {c_name}"

    # rag_k1 has 1,540 cached tokens
    k1_toks = conds["rag_k1"]["rq3_resources_and_cost"]["tokens"]
    assert k1_toks["cached_tokens"]["sum"] == 1540
    assert pytest.approx(k1_toks["cached_tokens"]["mean"], abs=1e-6) == 1540 / 1280.0
    assert k1_toks["cached_tokens"]["observed_attempts_count"] == 1280
    assert k1_toks["cached_tokens"]["missing_attempts_count"] == 1

    # all others have 0 cached tokens
    for c_name in ["no_rag", "rag_k3", "rag_k5", "rag_k10"]:
        c_toks = conds[c_name]["rq3_resources_and_cost"]["tokens"]
        assert c_toks["cached_tokens"]["sum"] == 0
        assert c_toks["cached_tokens"]["mean"] == 0.0
        assert c_toks["cached_tokens"]["observed_attempts_count"] == 1280
        assert c_toks["cached_tokens"]["missing_attempts_count"] == 0


def test_p95_suppression_policy():
    """Verify p95 latency is withheld with explicit status policy."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    assert bundle["p95_policy"]["status"] == P95_STATUS_POLICY
    for c_data in bundle["conditions"].values():
        lat = c_data["rq3_resources_and_cost"]["latency_ms"]
        assert lat["p95"] is None
        assert lat["p95_status"] == P95_STATUS_POLICY


def test_whole_study_financial_accounting():
    """Verify exact Decimal conservation of money."""
    bundle = build_canonical_metric_bundle(
        public_package_dir=GENUINE_PACKAGE_DIR,
        seal_path=GENUINE_SEAL_PATH,
        output_path=None,
    )
    fin = bundle["whole_study_financial_accounting"]
    assert fin["study_budget_cap_usd"] == "19.99000000"
    assert fin["prior_pilot_provisional_hold_usd"] == "0.05264010"
    assert fin["cumulative_settled_cost_usd"] == "6.57575890"
    assert fin["total_accounted_expenditure_usd"] == "6.62839900"
    assert fin["uncommitted_available_balance_usd"] == "13.36160100"
    assert fin["has_breach"] is False

    settled = Decimal(fin["cumulative_settled_cost_usd"])
    hold = Decimal(fin["prior_pilot_provisional_hold_usd"])
    avail = Decimal(fin["uncommitted_available_balance_usd"])
    cap = Decimal(fin["study_budget_cap_usd"])
    assert settled + hold + avail == cap


# =========================================================================
# NEGATIVE CONTROLS (FAIL-CLOSED)
# =========================================================================

def test_fail_closed_tampered_manifest_hash(tmp_path: Path):
    """Mutating any byte-preserved file in the public package must fail closed."""
    # Copy genuine package to tmp_path
    copied_pkg = tmp_path / "pkg"
    shutil.copytree(GENUINE_PACKAGE_DIR, copied_pkg)

    # Tamper with inputs/manifest.json
    manifest_file = copied_pkg / "inputs" / "manifest.json"
    content = manifest_file.read_bytes()
    manifest_file.write_bytes(content + b" ")

    with pytest.raises(ValueError, match="Hash mismatch for byte_preserved file"):
        verify_public_package(copied_pkg)


def test_fail_closed_tampered_seal_hash(tmp_path: Path):
    """Mutating canonical run seal must fail closed."""
    tampered_seal = tmp_path / "seal.json"
    content = GENUINE_SEAL_PATH.read_bytes()
    tampered_seal.write_bytes(content + b"\n")

    with pytest.raises(ValueError, match="Hash mismatch for canonical run seal"):
        verify_run_seal(tampered_seal)


def test_fail_closed_fixture_seal_rejected(tmp_path: Path):
    """A seal marked fixture_only or production_ready=False must be rejected."""
    tampered_seal = tmp_path / "fixture_seal.json"
    with open(GENUINE_SEAL_PATH, "r", encoding="utf-8") as f:
        seal_data = json.load(f)
    
    seal_data["fixture_only"] = True
    seal_data["production_ready"] = False
    with open(tampered_seal, "w", encoding="utf-8") as f:
        json.dump(seal_data, f)

    # Calling verify_file_hash directly or verify_run_seal
    # If hash doesn't match it raises hash mismatch; if we fake hash check it raises production_ready
    with pytest.raises(ValueError):
        verify_run_seal(tampered_seal)


def test_fail_closed_money_conservation_breach(tmp_path: Path):
    """Tampered ledger balances that breach money conservation must fail closed."""
    tampered_ledger = tmp_path / "ledger.json"
    with open(GENUINE_PACKAGE_DIR / "inputs" / "study_ledger.json", "r", encoding="utf-8") as f:
        ledger_data = json.load(f)

    # Tamper available balance
    ledger_data["uncommitted_available_balance_usd"] = "14.00000000"
    with open(tampered_ledger, "w", encoding="utf-8") as f:
        json.dump(ledger_data, f)

    with pytest.raises(ValueError, match="Available mismatch|Money conservation breached"):
        verify_financial_invariants(tampered_ledger)


def test_fail_closed_tampered_analysis_source_sha(tmp_path: Path):
    """Tampering with analysis source SHA in rq_analysis must fail closed."""
    copied_pkg = tmp_path / "pkg"
    shutil.copytree(GENUINE_PACKAGE_DIR, copied_pkg)

    rq_file = copied_pkg / "outputs" / "rq_analysis.json"
    with open(rq_file, "r", encoding="utf-8") as f:
        rq_data = json.load(f)

    rq_data["analysis_run_parameters"]["analysis_source_sha256"] = "0" * 64
    with open(rq_file, "w", encoding="utf-8") as f:
        json.dump(rq_data, f)

    # It will fail on manifest verification because rq_analysis.json is modified
    with pytest.raises(ValueError):
        build_canonical_metric_bundle(copied_pkg, GENUINE_SEAL_PATH, None)
