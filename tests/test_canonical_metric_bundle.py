"""
tests/test_canonical_metric_bundle.py

Comprehensive fail-closed test suite for Canonical Metric Bundle v2.
Validates:
- Positive controls on committed and genuine canonical bundle
- Deterministic LF bytes and exact sidecar hash matches on disk
- Rejection of tampered inputs, bad hashes, and broken manifests
- Rejection of fixture seals as canonical (even if hash check bypassed)
- Enforcement of financial conservation of money and item-level reconciliation
- Verification of token cache join telemetry (1,540 total, 1 network retry)
- Detection of retry receipt mutations (foreign view, response_id drift, input drift, status drift)
- Detection of non-integer/boolean cached token types
- Preservation of D2i independent failure axes (no causal or exclusive claim)
- Enforcement of p95 suppression policy
- Machine-generated lineage markdown accuracy and exact table statistics
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import patch

import pytest

from scripts.build_canonical_metric_bundle import (
    CANDIDATE_BASE_GIT_SHA,
    EXECUTION_GIT_SHA,
    EXPECTED_ANALYSIS_SOURCE_SHA256,
    EXPECTED_CORE_MANIFEST_SHA256,
    EXPECTED_PRICING_CONTRACT_SHA256,
    EXPECTED_PROTOCOL_SHA256,
    EXPECTED_PUBLIC_MANIFEST_SHA256,
    EXPECTED_TERMINAL_PROOF_SHA256,
    EXPECTED_TERMINAL_SEAL_SHA256,
    HISTORICAL_ANALYSIS_SOURCE_SHA256,
    NATIVE_EVALUATION_GIT_SHA,
    P95_STATUS_POLICY,
    ROOT_INTEGRATED_SOURCE_AUDIT_SHA256,
    ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256,
    RQ_V2_INTEGRATED_GIT_SHA,
    SUPERSEDING_AUTHORIZING_PACKET_SHA256,
    build_canonical_metric_bundle,
    parse_request_journal_cache,
    verify_canonical_metric_bundle_file,
    verify_financial_invariants,
    verify_public_package,
    verify_run_seal,
)

GENUINE_SEAL_PATH = Path("reports/evidence/canonical_run_seal_v1.json")
COMMITTED_BUNDLE_PATH = Path("artifacts/results/canonical_metric_bundle_v2.json")
COMMITTED_LINEAGE_PATH = Path("reports/evidence/canonical_metric_bundle_v2_lineage.md")


def get_public_package_dir() -> Optional[Path]:
    """Resolve location of public canonical package v3 if available."""
    env_dir = os.environ.get("RAG2ATTCK_PUBLIC_PACKAGE_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir)
    candidates = [
        Path("artifacts/public_package_staging/03_public_canonical_package"),
        Path.home() / ".codex" / "artifacts" / "rag2attck" / "final_handover_package_v3_20261002" / "03_public_canonical_package",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def get_test_bundle() -> Dict[str, Any]:
    """Retrieve bundle either by building from raw package or loading committed candidate."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is not None and GENUINE_SEAL_PATH.is_file():
        return build_canonical_metric_bundle(
            public_package_dir=pkg_dir,
            seal_path=GENUINE_SEAL_PATH,
            output_path=None,
        )
    if COMMITTED_BUNDLE_PATH.is_file():
        actual_bytes = COMMITTED_BUNDLE_PATH.read_bytes()
        return json.loads(actual_bytes.decode("utf-8"))
    pytest.skip("Neither raw public canonical package nor committed bundle is available")


# =========================================================================
# POSITIVE CONTROLS
# =========================================================================

def test_genuine_canonical_bundle_build():
    """Verify that build_canonical_metric_bundle executes cleanly when raw package is present."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")
    if not GENUINE_SEAL_PATH.is_file():
        pytest.skip("Run seal not available in environment")

    bundle = build_canonical_metric_bundle(
        public_package_dir=pkg_dir,
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


def test_disk_bundle_byte_deterministic_and_matches_sidecar():
    """Verify committed bundle has deterministic LF bytes and matches sidecar exactly."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    actual_bytes = COMMITTED_BUNDLE_PATH.read_bytes()
    assert b"\r" not in actual_bytes, "Committed bundle must contain only LF, no CRLF"

    actual_sha = hashlib.sha256(actual_bytes).hexdigest()
    sidecar_path = COMMITTED_BUNDLE_PATH.with_name(f"{COMMITTED_BUNDLE_PATH.name}.sha256")
    assert sidecar_path.is_file(), "Sidecar checksum file must exist"

    sidecar_sha = sidecar_path.read_bytes().decode("utf-8").strip().split()[0]
    assert actual_sha == sidecar_sha, f"Physical byte hash {actual_sha} != sidecar {sidecar_sha}"


def test_verify_bundle_validator_cli():
    """Positive test: verifying bundle with genuine trusted external digest passes cleanly."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    sidecar_path = COMMITTED_BUNDLE_PATH.with_name(f"{COMMITTED_BUNDLE_PATH.name}.sha256")
    trusted_sha = sidecar_path.read_bytes().decode("utf-8").strip().split()[0]
    bundle = verify_canonical_metric_bundle_file(
        COMMITTED_BUNDLE_PATH, expected_sha256=trusted_sha
    )
    assert bundle["schema_version"] == "2.0.0"
    assert bundle["bundle_type"] == "canonical-metric-bundle-v2"
    assert bundle["fixture_only"] is False


def test_validator_fails_closed_missing_expected_trust_anchor():
    """Negative test: missing expected_sha256 in canonical mode must fail closed."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")
    with pytest.raises(
        ValueError,
        match=r"Missing required external trust anchor \(expected_sha256\)",
    ):
        verify_canonical_metric_bundle_file(COMMITTED_BUNDLE_PATH, expected_sha256=None)


def test_validator_structural_only_mode():
    """Structural-only test: mode='structural_only' without expected digest returns status."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")
    res = verify_canonical_metric_bundle_file(COMMITTED_BUNDLE_PATH, mode="structural_only")
    assert res == {"status": "STRUCTURAL_AUDIT_NOT_VERIFIED"}


def test_cohort_and_denominator_specifications():
    """Verify exact cohort partition and denominator values."""
    bundle = get_test_bundle()
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
    bundle = get_test_bundle()
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
    assert pytest.approx(no_rag["accuracy_e2e_ci_95"][0], abs=1e-4) == 0.7464
    assert pytest.approx(no_rag["accuracy_e2e_ci_95"][1], abs=1e-4) == 0.8088

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
    bundle = get_test_bundle()
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
    bundle = get_test_bundle()
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
    assert k1_toks["cached_tokens"]["terminal_requests_known_count"] == 1280
    assert k1_toks["cached_tokens"]["physical_attempts_known_count"] == 1280
    assert k1_toks["cached_tokens"]["physical_attempts_missing_count"] == 1

    # all others have 0 cached tokens
    for c_name in ["no_rag", "rag_k3", "rag_k5", "rag_k10"]:
        c_toks = conds[c_name]["rq3_resources_and_cost"]["tokens"]
        assert c_toks["cached_tokens"]["sum"] == 0
        assert c_toks["cached_tokens"]["mean"] == 0.0
        assert c_toks["cached_tokens"]["terminal_requests_known_count"] == 1280
        assert c_toks["cached_tokens"]["physical_attempts_known_count"] == 1280
        assert c_toks["cached_tokens"]["physical_attempts_missing_count"] == 0


def test_p95_suppression_policy():
    """Verify p95 latency is withheld with explicit status policy."""
    bundle = get_test_bundle()
    assert bundle["p95_policy"]["status"] == P95_STATUS_POLICY
    for c_data in bundle["conditions"].values():
        lat = c_data["rq3_resources_and_cost"]["latency_ms"]
        assert lat["p95"] is None
        assert lat["p95_status"] == P95_STATUS_POLICY


def test_whole_study_financial_accounting():
    """Verify exact Decimal conservation of money."""
    bundle = get_test_bundle()
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


def test_lineage_metadata_and_metric_definitions():
    """Verify lineage binds all 6 distinct SHA identities and metric definitions."""
    bundle = get_test_bundle()
    assert bundle["execution_git_sha"] == EXECUTION_GIT_SHA
    assert bundle["native_evaluation_git_sha"] == NATIVE_EVALUATION_GIT_SHA
    assert bundle["rq_v2_integrated_git_sha"] == RQ_V2_INTEGRATED_GIT_SHA
    assert bundle["candidate_base_git_sha"] == CANDIDATE_BASE_GIT_SHA

    lineage = bundle["supplementary_source_lineage"]
    assert lineage["historical_analysis_source_sha256"] == HISTORICAL_ANALYSIS_SOURCE_SHA256
    assert lineage["superseding_authorizing_packet_sha256"] == SUPERSEDING_AUTHORIZING_PACKET_SHA256
    assert lineage["root_integrated_source_audit_sha256"] == ROOT_INTEGRATED_SOURCE_AUDIT_SHA256
    assert lineage["root_private_replay_acceptance_sha256"] == ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256

    defs = bundle["metric_definitions"]
    assert "any_match_semantics" in defs
    assert "macro_f1" in defs
    assert "bootstrap_parameters" in defs
    assert defs["bootstrap_parameters"]["samples"] == 1000
    assert defs["bootstrap_parameters"]["seed"] == 42
    assert defs["bootstrap_parameters"]["cluster_unit"] == "pair_id"
    assert defs["bootstrap_parameters"]["cluster_count"] == 440


def test_lineage_markdown_table_numerical_exactness():
    """Verify that generated lineage markdown has exact values matching oracle."""
    if not COMMITTED_LINEAGE_PATH.is_file():
        pytest.skip("Committed lineage markdown not found on disk")

    md_text = COMMITTED_LINEAGE_PATH.read_text(encoding="utf-8")
    assert "[74.64%, 80.88%]" in md_text, "No-RAG CI must be [74.64%, 80.88%]"
    assert "[-3.186, +1.124] pp" in md_text, "k1 delta CI must match exact pp"
    assert "0.435" in md_text, "k1 McNemar p must be 0.435"
    assert "[-2.355, +5.300] pp" in md_text, "k10 delta CI must match exact pp"
    assert "0.422" in md_text, "k10 McNemar p must be 0.422"
    assert "$0.75784210" in md_text, "k1 token estimate must be $0.75784210"
    assert "$0.00035420" in md_text, "k1 cache credit must be $0.00035420"
    assert "$0.53974560" in md_text, "k1 missing usage charge must be $0.53974560"
    assert "$1.29723350" in md_text, "k1 settled cost must be $1.29723350"


# =========================================================================
# NEGATIVE CONTROLS (FAIL-CLOSED)
# =========================================================================

def test_fail_closed_tampered_manifest_hash(tmp_path: Path):
    """Mutating any byte-preserved file in the public package must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    copied_pkg = tmp_path / "pkg"
    shutil.copytree(pkg_dir, copied_pkg)

    # Tamper with inputs/manifest.json
    manifest_file = copied_pkg / "inputs" / "manifest.json"
    content = manifest_file.read_bytes()
    manifest_file.write_bytes(content + b" ")

    with pytest.raises(ValueError, match="Hash mismatch for byte_preserved file"):
        verify_public_package(copied_pkg)


def test_fail_closed_tampered_seal_hash(tmp_path: Path):
    """Mutating canonical run seal must fail closed."""
    if not GENUINE_SEAL_PATH.is_file():
        pytest.skip("Run seal not available in environment")

    tampered_seal = tmp_path / "seal.json"
    content = GENUINE_SEAL_PATH.read_bytes()
    tampered_seal.write_bytes(content + b"\n")

    with pytest.raises(ValueError, match="Hash mismatch for canonical run seal"):
        verify_run_seal(tampered_seal)


def test_fail_closed_fixture_seal_rejected(tmp_path: Path):
    """A seal marked fixture_only or production_ready=False must be rejected even if hash bypassed."""
    if not GENUINE_SEAL_PATH.is_file():
        pytest.skip("Run seal not available in environment")

    seal_data = json.loads(GENUINE_SEAL_PATH.read_bytes().decode("utf-8"))
    seal_data["fixture_only"] = True
    seal_data["production_ready"] = True

    tampered_seal = tmp_path / "fixture_seal.json"
    tampered_bytes = json.dumps(seal_data).encode("utf-8")
    tampered_seal.write_bytes(tampered_bytes)

    # Bypass file hash check to test explicit semantic gate
    with patch("scripts.build_canonical_metric_bundle.verify_file_hash", return_value=tampered_bytes):
        with pytest.raises(ValueError, match="Run seal fixture_only must be False"):
            verify_run_seal(tampered_seal)


def test_fail_closed_retry_receipt_foreign_view():
    """Mutating retry attempt receipt to have foreign view_id must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"
    journal_lines = [json.loads(line) for line in journal_path.read_bytes().decode("utf-8").splitlines() if line.strip()]

    # Find ordinal 5388 and mutate view_id
    mutated = False
    for row in journal_lines:
        if row.get("event") == "attempt_receipt" and row.get("ordinal") == 5388:
            row["key"][0] = "foreign_view"
            mutated = True
            break
    assert mutated

    mutant_bytes = "\n".join(json.dumps(r) for r in journal_lines).encode("utf-8")
    with pytest.raises(ValueError, match="Retry receipt view_id|foreign view detected"):
        parse_request_journal_cache(journal_path, raw_journal_bytes=mutant_bytes)


def test_fail_closed_retry_receipt_input_usage_drift():
    """Mutating retry attempt receipt input tokens from 1543 to 1544 must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"
    journal_lines = [json.loads(line) for line in journal_path.read_bytes().decode("utf-8").splitlines() if line.strip()]

    for row in journal_lines:
        if row.get("event") == "attempt_receipt" and row.get("ordinal") == 5388:
            row["input_tokens"] = 1544
            break

    mutant_bytes = "\n".join(json.dumps(r) for r in journal_lines).encode("utf-8")
    with pytest.raises(ValueError, match="Retry receipt input_tokens mismatch"):
        parse_request_journal_cache(journal_path, raw_journal_bytes=mutant_bytes)


def test_fail_closed_retry_receipt_response_id_drift():
    """Mutating retry attempt receipt response_id must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"
    raw_lines = journal_path.read_bytes().decode("utf-8").splitlines()
    journal_lines = [json.loads(line) for line in raw_lines if line.strip()]

    for row in journal_lines:
        if row.get("event") == "attempt_receipt" and row.get("ordinal") == 5388:
            row["response_id"] = "wrong_response_id"
            break

    mutant_bytes = "\n".join(json.dumps(r) for r in journal_lines).encode("utf-8")
    with pytest.raises(ValueError, match="Retry receipt response_id drift"):
        parse_request_journal_cache(journal_path, raw_journal_bytes=mutant_bytes)


def test_fail_closed_boolean_cached_tokens():
    """Attempt receipt with boolean cached_tokens must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"
    raw_lines = journal_path.read_bytes().decode("utf-8").splitlines()
    journal_lines = [json.loads(line) for line in raw_lines if line.strip()]

    # Mutate first attempt receipt
    for row in journal_lines:
        if row.get("event") == "attempt_receipt":
            row["cached_tokens"] = False
            break

    mutant_bytes = "\n".join(json.dumps(r) for r in journal_lines).encode("utf-8")
    with pytest.raises(TypeError, match="cached_tokens must be an integer"):
        parse_request_journal_cache(journal_path, raw_journal_bytes=mutant_bytes)


def test_fail_closed_ledger_item_tampering_top_totals_unchanged():
    """Tampering with an individual settled item cost must fail closed on item reconciliation."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    ledger_path = pkg_dir / "inputs" / "study_ledger.json"
    ledger_data = json.loads(ledger_path.read_bytes().decode("utf-8"))

    # Alter first settled record to 99.00000000
    first_key = next(iter(ledger_data["settled_records"]))
    ledger_data["settled_records"][first_key]["cost_usd"] = "99.00000000"

    mutant_bytes = json.dumps(ledger_data).encode("utf-8")
    with pytest.raises(ValueError, match="reservation balance broken"):
        verify_financial_invariants(ledger_path, raw_ledger_bytes=mutant_bytes)


def test_fail_closed_nan_in_rq_analysis(tmp_path: Path):
    """RQ analysis containing NaN values must be rejected during load."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")
    if not GENUINE_SEAL_PATH.is_file():
        pytest.skip("Run seal not available in environment")

    # Get legitimate manifest and cache
    manifest, cache = verify_public_package(pkg_dir)
    rq_bytes = cache["outputs/rq_analysis.json"]
    tampered_bytes = rq_bytes.replace(
        b'"accuracy_end_to_end": 0.7799442896935933',
        b'"accuracy_end_to_end": NaN',
    )
    cache["outputs/rq_analysis.json"] = tampered_bytes

    with patch(
        "scripts.build_canonical_metric_bundle.verify_public_package",
        return_value=(manifest, cache),
    ):
        with pytest.raises(ValueError, match="Non-finite JSON constant not allowed"):
            build_canonical_metric_bundle(pkg_dir, GENUINE_SEAL_PATH, None)


def test_fail_closed_money_conservation_breach(tmp_path: Path):
    """Tampered ledger balances that breach money conservation must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    tampered_ledger = tmp_path / "ledger.json"
    with open(pkg_dir / "inputs" / "study_ledger.json", "r", encoding="utf-8") as f:
        ledger_data = json.load(f)

    # Tamper available balance
    ledger_data["uncommitted_available_balance_usd"] = "14.00000000"
    with open(tampered_ledger, "w", encoding="utf-8") as f:
        json.dump(ledger_data, f)

    with pytest.raises(ValueError, match="Available mismatch|Money conservation breached"):
        verify_financial_invariants(tampered_ledger)


def test_fail_closed_tampered_analysis_source_sha(tmp_path: Path):
    """Tampering with analysis source SHA in rq_analysis must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")
    if not GENUINE_SEAL_PATH.is_file():
        pytest.skip("Run seal not available in environment")

    copied_pkg = tmp_path / "pkg"
    shutil.copytree(pkg_dir, copied_pkg)

    rq_file = copied_pkg / "outputs" / "rq_analysis.json"
    with open(rq_file, "r", encoding="utf-8") as f:
        rq_data = json.load(f)

    rq_data["analysis_run_parameters"]["analysis_source_sha256"] = "0" * 64
    with open(rq_file, "w", encoding="utf-8") as f:
        json.dump(rq_data, f)

    with pytest.raises(ValueError):
        build_canonical_metric_bundle(copied_pkg, GENUINE_SEAL_PATH, None)


def test_validator_fails_closed_on_rehashed_mutant_vs_trusted_anchor(tmp_path: Path):
    """Sidecar rehashed on mutated payload must fail closed against original expected digest."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")
    sidecar_path = COMMITTED_BUNDLE_PATH.with_name(f"{COMMITTED_BUNDLE_PATH.name}.sha256")
    trusted_anchor = sidecar_path.read_bytes().decode("utf-8").strip().split()[0]

    bundle_data = json.loads(COMMITTED_BUNDLE_PATH.read_bytes().decode("utf-8"))
    bundle_data["conditions"]["no_rag"]["rq1_attribution"]["correct_count"] = 700

    tampered_bundle_file = tmp_path / "canonical_metric_bundle_v2.json"
    tampered_bytes = json.dumps(bundle_data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    tampered_bundle_file.write_bytes(tampered_bytes)

    rehashed_sha = hashlib.sha256(tampered_bytes).hexdigest()
    sidecar_file = tmp_path / "canonical_metric_bundle_v2.json.sha256"
    sidecar_file.write_bytes(f"{rehashed_sha}  canonical_metric_bundle_v2.json\n".encode("utf-8"))

    with pytest.raises(
        ValueError,
        match=r"Bundle integrity breach: actual SHA .* does not match trusted external anchor",
    ):
        verify_canonical_metric_bundle_file(
            tampered_bundle_file, expected_sha256=trusted_anchor
        )


def test_rehashed_tampered_metric_rejected(tmp_path: Path):
    """Mutating scientific metrics (e.g. correct_count) and rehashing sidecar must fail closed."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    bundle_data = json.loads(COMMITTED_BUNDLE_PATH.read_bytes().decode("utf-8"))
    bundle_data["conditions"]["no_rag"]["rq1_attribution"]["correct_count"] = 700

    tampered_bundle_file = tmp_path / "canonical_metric_bundle_v2.json"
    tampered_bytes = json.dumps(bundle_data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    tampered_bundle_file.write_bytes(tampered_bytes)

    rehashed_sha = hashlib.sha256(tampered_bytes).hexdigest()
    sidecar_file = tmp_path / "canonical_metric_bundle_v2.json.sha256"
    sidecar_file.write_bytes(f"{rehashed_sha}  canonical_metric_bundle_v2.json\n".encode("utf-8"))

    with pytest.raises(ValueError, match="correct_count mismatch|accuracy_end_to_end mismatch"):
        verify_canonical_metric_bundle_file(tampered_bundle_file, expected_sha256=rehashed_sha)


def test_rehashed_p95_policy_breach_rejected(tmp_path: Path):
    """Adding numeric p95 value and rehashing sidecar must fail closed."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    bundle_data = json.loads(COMMITTED_BUNDLE_PATH.read_bytes().decode("utf-8"))
    bundle_data["conditions"]["rag_k10"]["rq3_resources_and_cost"]["latency_ms"]["p95"] = 1250.5

    tampered_bundle_file = tmp_path / "canonical_metric_bundle_v2.json"
    tampered_bytes = json.dumps(bundle_data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    tampered_bundle_file.write_bytes(tampered_bytes)

    rehashed_sha = hashlib.sha256(tampered_bytes).hexdigest()
    sidecar_file = tmp_path / "canonical_metric_bundle_v2.json.sha256"
    sidecar_file.write_bytes(f"{rehashed_sha}  canonical_metric_bundle_v2.json\n".encode("utf-8"))

    with pytest.raises(ValueError, match="p95 suppression policy violated"):
        verify_canonical_metric_bundle_file(tampered_bundle_file, expected_sha256=rehashed_sha)


def test_rehashed_tampered_source_pins_rejected(tmp_path: Path):
    """Tampering with execution Git commit and rehashing sidecar must fail closed."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    bundle_data = json.loads(COMMITTED_BUNDLE_PATH.read_bytes().decode("utf-8"))
    bundle_data["execution_git_sha"] = "0" * 40

    tampered_bundle_file = tmp_path / "canonical_metric_bundle_v2.json"
    tampered_bytes = json.dumps(bundle_data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    tampered_bundle_file.write_bytes(tampered_bytes)

    rehashed_sha = hashlib.sha256(tampered_bytes).hexdigest()
    sidecar_file = tmp_path / "canonical_metric_bundle_v2.json.sha256"
    sidecar_file.write_bytes(f"{rehashed_sha}  canonical_metric_bundle_v2.json\n".encode("utf-8"))

    with pytest.raises(ValueError, match="execution_git_sha mismatch"):
        verify_canonical_metric_bundle_file(tampered_bundle_file, expected_sha256=rehashed_sha)


def test_rehashed_tampered_timestamp_rejected(tmp_path: Path):
    """Tampering with analysis_timestamp_utc and rehashing sidecar must fail closed."""
    if not COMMITTED_BUNDLE_PATH.is_file():
        pytest.skip("Committed bundle not found on disk")

    bundle_data = json.loads(COMMITTED_BUNDLE_PATH.read_bytes().decode("utf-8"))
    bundle_data["analysis_timestamp_utc"] = "2026-10-02T16:09:00+00:00"

    tampered_bundle_file = tmp_path / "canonical_metric_bundle_v2.json"
    tampered_bytes = json.dumps(bundle_data, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    tampered_bundle_file.write_bytes(tampered_bytes)

    rehashed_sha = hashlib.sha256(tampered_bytes).hexdigest()
    sidecar_file = tmp_path / "canonical_metric_bundle_v2.json.sha256"
    sidecar_file.write_bytes(f"{rehashed_sha}  canonical_metric_bundle_v2.json\n".encode("utf-8"))

    with pytest.raises(ValueError, match="analysis_timestamp_utc must match.*authoritative"):
        verify_canonical_metric_bundle_file(tampered_bundle_file, expected_sha256=rehashed_sha)


def test_receipt_join_response_id_mismatch_rejected():
    """Lệch response_id giữa receipt và prediction phải fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    manifest, cache = verify_public_package(pkg_dir)
    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"

    # Mutate 1 prediction's response_id in byte cache
    k1_bytes = cache["inputs/rag_k1_predictions.jsonl"]
    lines = k1_bytes.decode("utf-8").splitlines()
    first_pred = json.loads(lines[0])
    first_pred["response_id"] = "resp_mutated_id_12345"
    lines[0] = json.dumps(first_pred)
    mutated_k1_bytes = "\n".join(lines).encode("utf-8")
    cache["inputs/rag_k1_predictions.jsonl"] = mutated_k1_bytes

    with pytest.raises(ValueError, match="response_id mismatch"):
        parse_request_journal_cache(
            journal_path=journal_path,
            raw_journal_bytes=cache["inputs/request_journal.jsonl"],
            predictions_bytes_cache=cache,
        )


def test_receipt_join_model_drift_rejected():
    """Model drift trong attempt receipt phải fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    manifest, cache = verify_public_package(pkg_dir)
    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"
    raw_lines = cache["inputs/request_journal.jsonl"].decode("utf-8").splitlines()
    journal_lines = [json.loads(line) for line in raw_lines if line.strip()]

    # Mutate model of first receipt
    for row in journal_lines:
        if row.get("event") == "attempt_receipt" and row.get("status") == "SUCCESS":
            row["model"] = "gpt-4o"
            break

    mutant_journal_bytes = "\n".join(json.dumps(r) for r in journal_lines).encode("utf-8")
    with pytest.raises(ValueError, match="Receipt model drift|Model mismatch"):
        parse_request_journal_cache(
            journal_path=journal_path,
            raw_journal_bytes=mutant_journal_bytes,
            predictions_bytes_cache=cache,
        )


def test_receipt_join_incomplete_status_mismatch_rejected():
    """Terminal INCOMPLETE receipt status conflicting with pred success must fail closed."""
    pkg_dir = get_public_package_dir()
    if pkg_dir is None:
        pytest.skip("Raw public canonical package not available in CI environment")

    manifest, cache = verify_public_package(pkg_dir)
    journal_path = pkg_dir / "inputs" / "request_journal.jsonl"

    k3_bytes = cache["inputs/rag_k3_predictions.jsonl"]
    lines = k3_bytes.decode("utf-8").splitlines()
    mutated = False
    for idx, line_entry in enumerate(lines):
        pentry = json.loads(line_entry)
        if pentry.get("sample_id") == "view_1b91ff45":
            pentry["success"] = True
            lines[idx] = json.dumps(pentry)
            mutated = True
            break
    assert mutated
    cache["inputs/rag_k3_predictions.jsonl"] = "\n".join(lines).encode("utf-8")

    with pytest.raises(ValueError, match="Status INCOMPLETE requires pred success=False"):
        parse_request_journal_cache(
            journal_path=journal_path,
            raw_journal_bytes=cache["inputs/request_journal.jsonl"],
            predictions_bytes_cache=cache,
        )


def test_validator_rejects_rehashed_mutants(tmp_path: Path):
    """
    Verify that verify_canonical_metric_bundle_file rejects all typed leaf mutations
    even when sidecar checksum is updated to match the mutated bytes.
    """
    import copy
    bundle_path = Path("artifacts/results/canonical_metric_bundle_v2.json")
    if not bundle_path.is_file():
        pytest.skip("canonical_metric_bundle_v2.json not found on disk")

    original_bundle = json.loads(bundle_path.read_text(encoding="utf-8"))

    mutations = [
        (
            "macro_f1",
            lambda d: d["conditions"]["no_rag"]["rq1_attribution"].__setitem__(
                "macro_f1", 999.0
            ),
            "macro_f1 mismatch",
        ),
        (
            "retrieval_hit",
            lambda d: d["conditions"]["rag_k10"]["rq2_retrieval_and_error"][
                "retrieval_metrics"
            ].__setitem__("retrieval_hit_count", 0),
            "retrieval_hit_count mismatch",
        ),
        (
            "exact_p",
            lambda d: d["conditions"]["rag_k10"]["rq1_attribution"]["delta_vs_baseline"][
                "mcnemar_test"
            ].__setitem__("p_value_exact", 999.0),
            "p_value_exact mismatch",
        ),
        (
            "ci_bounds",
            lambda d: d["conditions"]["no_rag"]["rq1_attribution"].__setitem__(
                "accuracy_e2e_ci_95", [0.01, 0.99]
            ),
            "accuracy_e2e_ci_95 mismatch",
        ),
        (
            "prompt_sum",
            lambda d: d["conditions"]["no_rag"]["rq3_resources_and_cost"]["tokens"][
                "prompt_tokens"
            ].__setitem__("sum", 999),
            "prompt_tokens.sum mismatch",
        ),
        (
            "latency_median",
            lambda d: d["conditions"]["no_rag"]["rq3_resources_and_cost"][
                "latency_ms"
            ].__setitem__("median", 999.0),
            "latency_ms.median mismatch",
        ),
        (
            "cache_mean",
            lambda d: d["conditions"]["rag_k1"]["rq3_resources_and_cost"]["tokens"][
                "cached_tokens"
            ].__setitem__("mean", 999.0),
            "cached_tokens.mean mismatch",
        ),
        (
            "source_digest",
            lambda d: d["source_file_digests"].__setitem__("request_journal.jsonl", "0" * 64),
            "source_file_digests.request_journal.jsonl mismatch",
        ),
        (
            "timestamp_fake",
            lambda d: d.__setitem__("analysis_timestamp_utc", "2026-10-02T04:32:51_FAKE"),
            "analysis_timestamp_utc must match exact",
        ),
    ]

    for label, mutate_fn, err_regex in mutations:
        d = copy.deepcopy(original_bundle)
        mutate_fn(d)
        mutant_bytes = json.dumps(d, indent=2, sort_keys=True).encode("utf-8") + b"\n"
        mutant_sha = hashlib.sha256(mutant_bytes).hexdigest()

        test_bundle_file = tmp_path / f"bundle_{label}.json"
        test_sidecar_file = tmp_path / f"bundle_{label}.json.sha256"

        test_bundle_file.write_bytes(mutant_bytes)
        test_sidecar_file.write_bytes(f"{mutant_sha}  {test_bundle_file.name}\n".encode("utf-8"))

        with pytest.raises(ValueError, match=err_regex):
            verify_canonical_metric_bundle_file(test_bundle_file, expected_sha256=mutant_sha)
