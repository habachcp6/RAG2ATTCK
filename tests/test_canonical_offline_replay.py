"""Unit and Regression Test Suite for Canonical Offline Replay & Integrity.

Author: Native Agent A (Track A - Audit & Recovery)
Scope: RAG2ATTCK Canonical Replay Verification (PR #24)
Egress Invariant: Strictly offline verification without provider calls.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import types
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

DEFAULT_BUNDLE_DIR = Path(
    os.getenv(
        "CANONICAL_BUNDLE_DIR",
        "C:/Users/hahoa/.codex/artifacts/rag2attck/canonical-accepted-bundle-v2",
    )
)
CANONICAL_BUNDLE_SHA256 = "00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f"
CANONICAL_WRAPPER_BLOCK_SHA256 = "e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68"


def compute_sha256(data: bytes) -> str:
    """Compute hex SHA-256 digest of raw byte content."""
    return hashlib.sha256(data).hexdigest()


@pytest.mark.skipif(
    not DEFAULT_BUNDLE_DIR.exists(),
    reason="Canonical accepted bundle not found on CI runner (local artifact)",
)
class TestCanonicalBundleIntegrity:
    """Verifies cryptographic integrity of the Root-accepted canonical metric bundle."""

    def test_bundle_manifest_exists_and_matches_sha(self):
        manifest_path = DEFAULT_BUNDLE_DIR / "canonical_metric_bundle_v1.json"
        assert manifest_path.exists(), f"Bundle manifest not found at {manifest_path}"
        actual_sha = compute_sha256(manifest_path.read_bytes())
        assert actual_sha == CANONICAL_BUNDLE_SHA256, (
            f"Bundle manifest SHA-256 mismatch: {actual_sha} != {CANONICAL_BUNDLE_SHA256}"
        )

    def test_all_10_canonical_inputs_match_digests(self):
        manifest_path = DEFAULT_BUNDLE_DIR / "canonical_metric_bundle_v1.json"
        bundle_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        source_digests = bundle_data.get("source_file_digests", {})
        assert len(source_digests) == 10, f"Expected 10 input files, got {len(source_digests)}"

        inputs_dir = DEFAULT_BUNDLE_DIR / "inputs"
        for fname, expected_sha in source_digests.items():
            fpath = inputs_dir / fname
            assert fpath.exists(), f"Missing input file: {fpath}"
            actual_sha = compute_sha256(fpath.read_bytes())
            assert actual_sha == expected_sha, (
                f"Hash mismatch on {fname}: {actual_sha} != {expected_sha}"
            )

    def test_all_8_canonical_outputs_match_digests(self):
        manifest_path = DEFAULT_BUNDLE_DIR / "canonical_metric_bundle_v1.json"
        bundle_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        output_digests = bundle_data.get("output_file_digests", {})
        assert len(output_digests) == 8, f"Expected 8 output files, got {len(output_digests)}"

        for fname, expected_sha in output_digests.items():
            fpath = DEFAULT_BUNDLE_DIR / fname
            assert fpath.exists(), f"Missing output file: {fpath}"
            actual_sha = compute_sha256(fpath.read_bytes())
            assert actual_sha == expected_sha, (
                f"Hash mismatch on {fname}: {actual_sha} != {expected_sha}"
            )


@pytest.mark.skipif(
    not DEFAULT_BUNDLE_DIR.exists(),
    reason="Canonical accepted bundle not found on CI runner (local artifact)",
)
class TestCanonicalAccountingReconciliation:
    """Verifies monetary ledger, anchor, journal, and retry reconciliation."""

    def test_monetary_arithmetic_consistency(self):
        inputs_dir = DEFAULT_BUNDLE_DIR / "inputs"
        anchor = json.loads((inputs_dir / ".study_anchor.json").read_text(encoding="utf-8"))
        summary = json.loads((inputs_dir / "run_summary.json").read_text(encoding="utf-8"))

        total_budget = Decimal(anchor["total_budget_usd"])
        prior_hold = Decimal(anchor["prior_pilot_provisional_hold_usd"])
        initial_avail = Decimal(anchor["initial_available_usd"])

        # Invariant 1: initial_available = total_budget - prior_hold
        assert initial_avail == (total_budget - prior_hold), "Anchor initial balance math error"

        budget_summary = summary["study_budget"]
        settled_cost = Decimal(budget_summary["cumulative_settled_cost_usd"])
        avail_balance = Decimal(budget_summary["uncommitted_available_balance_usd"])

        # Invariant 2: avail_balance = initial_avail - settled_cost
        assert avail_balance == (initial_avail - settled_cost), (
            "Summary balance reconciliation error"
        )
        assert budget_summary["has_breach"] is False, "Budget breach flagged unexpectedly"

    def test_exact_retry_and_incomplete_accounting(self):
        inputs_dir = DEFAULT_BUNDLE_DIR / "inputs"
        journal_path = inputs_dir / "request_journal.jsonl"

        seen_attempts: set[tuple] = set()
        retried_keys: list[tuple] = []
        attempt_count = 0
        complete_count = 0

        with open(journal_path, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                ev = entry.get("event")
                if ev == "attempt":
                    attempt_count += 1
                    k = tuple(entry.get("key", []))
                    if k in seen_attempts:
                        retried_keys.append(k)
                    else:
                        seen_attempts.add(k)
                elif ev == "complete":
                    complete_count += 1

        assert complete_count == 6400, f"Expected 6,400 complete records, got {complete_count}"
        assert attempt_count == 6401, f"Expected 6,401 attempts, got {attempt_count}"
        assert len(retried_keys) == 1, f"Expected exactly 1 retry, got {len(retried_keys)}"
        assert retried_keys[0] == ("view_d870d574", "rag_k1"), (
            f"Unexpected retried key: {retried_keys[0]}"
        )

    def test_13_incomplete_records_token_ceiling(self):
        inputs_dir = DEFAULT_BUNDLE_DIR / "inputs"
        incompletes = []
        conditions = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]

        for cond in conditions:
            pf = inputs_dir / f"{cond}_predictions.jsonl"
            with open(pf, "r", encoding="utf-8") as f:
                for line in f:
                    r = json.loads(line)
                    if r.get("parse_status") == "INCOMPLETE":
                        incompletes.append(r)

        assert len(incompletes) == 13, (
            f"Expected exactly 13 incomplete records, got {len(incompletes)}"
        )
        for r in incompletes:
            assert r["completion_tokens"] == 8192, (
                "Incomplete record did not hit 8192 token ceiling"
            )
            assert r["error_message"] == "Response incomplete: max_output_tokens"
            assert r["parsed_technique_ids"] == [], (
                "Incomplete record did not fail-closed to empty list"
            )


class TestCriticalCodeInvariants:
    """Verifies that runtime wrapper SHA remains strictly invariant."""

    def test_raw_wrapper_block_sha256(self):
        from tests.fixtures.runtime_recovery_wrapper_fixture import RAW_WRAPPER_BLOCK

        actual_sha = hashlib.sha256(RAW_WRAPPER_BLOCK.encode("utf-8")).hexdigest()
        assert actual_sha == CANONICAL_WRAPPER_BLOCK_SHA256, (
            f"RAW_WRAPPER_BLOCK SHA mismatch: {actual_sha} != {CANONICAL_WRAPPER_BLOCK_SHA256}"
        )


class TestMathematicalComparatorAndFailClosed:
    """Verifies precision tolerance, exact Decimal currency comparison, and fail-closed gates."""

    def test_float_comparison_tolerance_gate(self):
        from scripts.reproduce_canonical_study import compare_metrics_trees

        base_metrics = {"accuracy": 0.7838440111420613, "f1": 0.01336671534494176}
        # Within tolerance (1e-13 difference)
        matching_metrics = {"accuracy": 0.7838440111420613 + 5e-14, "f1": 0.01336671534494176}
        ok, disc = compare_metrics_trees(matching_metrics, base_metrics, float_tolerance=1e-12)
        assert ok is True, f"Expected match within tolerance, got {disc}"

        # Exceeds tolerance (1e-10 difference)
        divergent_metrics = {"accuracy": 0.7838440111420613 + 1e-10, "f1": 0.01336671534494176}
        ok, disc = compare_metrics_trees(divergent_metrics, base_metrics, float_tolerance=1e-12)
        assert ok is False, "Expected failure when exceeding float tolerance"
        assert len(disc) > 0, "Expected discrepancy record for divergent float"

    def test_decimal_currency_exact_comparison(self):
        from scripts.reproduce_canonical_study import compare_metrics_trees

        ledger_metrics = {"settled_cost": "6.57575890", "total_budget": "19.99000000"}
        exact_match = {
            "settled_cost": Decimal("6.57575890"),
            "total_budget": Decimal("19.99000000"),
        }
        ok, disc = compare_metrics_trees(exact_match, ledger_metrics)
        assert ok is True, f"Expected exact Decimal match, got {disc}"

        # Off by 1 Satoshi / 10^-8 USD
        mismatched_cost = {"settled_cost": "6.57575891", "total_budget": "19.99000000"}
        ok, disc = compare_metrics_trees(mismatched_cost, ledger_metrics)
        assert ok is False, "Expected failure on 1e-8 USD currency mismatch"

    def test_fail_closed_on_corrupt_or_empty_scoring(self):
        from scripts.reproduce_canonical_study import compare_metrics_trees

        canonical_payload = {
            "accuracy_end_to_end": 0.7838440111420613,
            "completed_record_count": 6387,
            "provider_failure_count": 13,
        }
        # Corrupted scoring (empty dict or no-op)
        noop_payload = {}
        ok, disc = compare_metrics_trees(noop_payload, canonical_payload)
        assert ok is False, "Expected fail-closed on empty no-op scoring"
        assert len(disc) == 3, f"Expected 3 missing key discrepancies, got {len(disc)}"

    def test_baseline_22_files_verification_on_disk(self):
        from scripts.reproduce_canonical_study import REPO_ROOT, verify_protected_baseline

        ok, logs = verify_protected_baseline(REPO_ROOT)
        assert ok is True, f"Baseline verification failed: {logs}"


class TestDispatchSpiesAndFailClosedReplay:
    """Verifies evaluator/RQ dispatch spies, mutants, and fail-closed missing module gates."""

    @pytest.mark.skipif(
        not DEFAULT_BUNDLE_DIR.exists(),
        reason="Canonical accepted bundle not found on CI runner (local artifact)",
    )
    def test_native_evaluator_invocation_spy(self, monkeypatch, tmp_path):
        """Verify native evaluate_experiment is invoked with strict protocol and inputs."""
        import src.evaluation.experiment_metrics as em
        from scripts.reproduce_canonical_study import REPO_ROOT, replay_saved_evaluation

        spy_called: dict[str, Any] = {}

        def mock_evaluate_experiment(inputs, protocol, output_dir=None):
            spy_called["called"] = True
            spy_called["inputs"] = inputs
            spy_called["protocol"] = protocol
            spy_called["output_dir"] = output_dir
            return {
                "overall": {},
                "per_condition": {},
                "per_technique": {},
                "retrieval_conditional": {},
                "failure_decomposition": {},
                "run_provenance": {},
            }

        monkeypatch.setattr(em, "evaluate_experiment", mock_evaluate_experiment)

        # Call replay helper
        replay_saved_evaluation(DEFAULT_BUNDLE_DIR, tmp_path, REPO_ROOT)

        assert spy_called.get("called") is True, "evaluate_experiment was not invoked"
        assert spy_called["output_dir"] == tmp_path / "regenerated_native_6"
        assert hasattr(spy_called["inputs"], "records")
        assert hasattr(spy_called["protocol"], "protocol_version")

    @pytest.mark.skipif(
        not DEFAULT_BUNDLE_DIR.exists(),
        reason="Canonical accepted bundle not found on CI runner (local artifact)",
    )
    def test_rq_analysis_invocation_spy(self, monkeypatch, tmp_path):
        """Verify run_rq_analysis is genuinely invoked with required analytical parameters."""
        from scripts.reproduce_canonical_study import REPO_ROOT, replay_saved_evaluation

        spy_called: dict[str, Any] = {}

        def mock_run_rq_analysis(**kwargs):
            spy_called["called"] = True
            spy_called["kwargs"] = kwargs
            return {}

        mock_mod = types.ModuleType("scripts.analysis.evaluate_rqs")
        mock_mod.run_rq_analysis = mock_run_rq_analysis  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "scripts.analysis.evaluate_rqs", mock_mod)

        replay_saved_evaluation(DEFAULT_BUNDLE_DIR, tmp_path, REPO_ROOT)

        assert spy_called.get("called") is True, "run_rq_analysis was not invoked"
        kw = spy_called["kwargs"]
        assert kw["bootstrap_samples"] == 1000
        assert kw["seed"] == 42
        assert kw["output_dir"] == tmp_path / "regenerated_rq"
        assert kw["journal_path"] == DEFAULT_BUNDLE_DIR / "inputs/request_journal.jsonl"
        assert kw["study_ledger_path"] == DEFAULT_BUNDLE_DIR / "inputs/study_ledger.json"
        assert kw["repo_root"] == REPO_ROOT

    def test_rq_mutant_fails_closed(self):
        """Verify comparator fails closed on mutant RQ p-value, delta-F1, or empty no-op output."""
        from scripts.reproduce_canonical_study import compare_metrics_trees

        canonical_rq = {
            "analysis_tool_version": "2.0.0",
            "rq1": {
                "headline_delta_f1": 0.05214567,
                "mcnemar_p_value": 0.00012543,
            },
            "rq2": {
                "retrieval_recall_k5": 0.81234567,
                "generation_accuracy_conditioned": 0.94123456,
            },
            "rq3": {"whole_study_financial_accounting": {"total_settled_cost_usd": "6.57575890"}},
        }

        # Mutant 1: Wrong metric (divergent McNemar p-value)
        mutant_p_val = {
            "analysis_tool_version": "2.0.0",
            "rq1": {
                "headline_delta_f1": 0.05214567,
                "mcnemar_p_value": 0.05000000,
            },
            "rq2": {
                "retrieval_recall_k5": 0.81234567,
                "generation_accuracy_conditioned": 0.94123456,
            },
            "rq3": {"whole_study_financial_accounting": {"total_settled_cost_usd": "6.57575890"}},
        }
        ok1, disc1 = compare_metrics_trees(mutant_p_val, canonical_rq, path="rq_analysis.json")
        assert ok1 is False, "Mutant p-value must fail comparison"
        assert any("mcnemar_p_value" in d for d in disc1)

        # Mutant 2: Empty no-op result
        noop_rq = {}
        ok2, disc2 = compare_metrics_trees(noop_rq, canonical_rq, path="rq_analysis.json")
        assert ok2 is False, "No-op empty result must fail closed"
        assert len(disc2) >= 3

    @pytest.mark.skipif(
        not DEFAULT_BUNDLE_DIR.exists(),
        reason="Canonical accepted bundle not found on CI runner (local artifact)",
    )
    def test_missing_rq_module_fails_closed_never_passes(self, monkeypatch, tmp_path):
        """Verify that missing scripts.analysis.evaluate_rqs returns False, NEVER True."""
        from scripts.reproduce_canonical_study import REPO_ROOT, replay_saved_evaluation

        if "scripts.analysis.evaluate_rqs" in sys.modules:
            monkeypatch.delitem(sys.modules, "scripts.analysis.evaluate_rqs")
        if "scripts.analysis" in sys.modules:
            monkeypatch.delitem(sys.modules, "scripts.analysis")

        # In worktree A, evaluate_rqs is naturally not present in repo_root.
        # Calling replay_saved_evaluation must fail closed and return False.
        ok, logs = replay_saved_evaluation(DEFAULT_BUNDLE_DIR, tmp_path, REPO_ROOT)
        assert ok is False, "replay_saved_evaluation MUST return False when RQ module is missing"
        assert any("[FAIL] Missing required RQ analysis module" in line for line in logs)

    def test_missing_evaluator_module_fails_closed_never_passes(self, monkeypatch, tmp_path):
        """Verify that missing src.evaluation.experiment_metrics returns False, NEVER True."""
        import builtins

        from scripts.reproduce_canonical_study import REPO_ROOT, replay_saved_evaluation

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if "src.evaluation.experiment_metrics" in name:
                raise ImportError("Mocked missing evaluator module")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)

        ok, logs = replay_saved_evaluation(DEFAULT_BUNDLE_DIR, tmp_path, REPO_ROOT)
        assert ok is False, "replay_saved_evaluation MUST return False when evaluator is missing"
        assert any("[FAIL] Missing required evaluation module" in line for line in logs)
