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
LOCAL_STAGED_BUNDLE_DIR = (
    Path(__file__).resolve().parents[1]
    / "artifacts/public_package_staging/canonical-bundle-public-v1"
)
EXPECTED_PUBLIC_MANIFEST_SHA256 = "32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c"
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

    def test_strict_type_boolean_not_equal_int(self):
        """Verify strict boolean gate: True must NEVER equal 1, False must NEVER equal 0."""
        from scripts.reproduce_canonical_study import compare_metrics_trees

        ok1, disc1 = compare_metrics_trees(True, 1)
        assert ok1 is False, "True must never equal integer 1"
        assert len(disc1) > 0

        ok2, disc2 = compare_metrics_trees(1, True)
        assert ok2 is False, "Integer 1 must never equal True"
        assert len(disc2) > 0

        ok3, disc3 = compare_metrics_trees(False, 0)
        assert ok3 is False, "False must never equal integer 0"
        assert len(disc3) > 0

        ok4, disc4 = compare_metrics_trees(0, False)
        assert ok4 is False, "Integer 0 must never equal False"
        assert len(disc4) > 0

    def test_non_finite_float_nan_and_inf_rejected(self):
        """Verify non-finite floats (NaN, +Inf, -Inf) fail closed and are rejected."""
        from scripts.reproduce_canonical_study import compare_metrics_trees

        ok_nan, disc_nan = compare_metrics_trees(float("nan"), float("nan"))
        assert ok_nan is False, "NaN floating point must be rejected"
        assert any("Non-finite float rejected" in d for d in disc_nan)

        ok_inf, disc_inf = compare_metrics_trees(float("inf"), float("inf"))
        assert ok_inf is False, "+Inf floating point must be rejected"
        assert any("Non-finite float rejected" in d for d in disc_inf)

        ok_ninf, disc_ninf = compare_metrics_trees(float("-inf"), float("-inf"))
        assert ok_ninf is False, "-Inf floating point must be rejected"
        assert any("Non-finite float rejected" in d for d in disc_ninf)

    def test_loose_numeric_string_rejected(self):
        """Verify loose numeric strings rejected: exact equality required ('001' != '1')."""
        from scripts.reproduce_canonical_study import compare_metrics_trees

        ok1, disc1 = compare_metrics_trees("001", "1")
        assert ok1 is False, "Loose numeric string '001' must not equal '1'"
        assert len(disc1) > 0

        ok2, disc2 = compare_metrics_trees({"id": "001"}, {"id": "1"})
        assert ok2 is False, "Non-monetary dictionary strings must compare exact characters"
        assert len(disc2) > 0

    def test_core_manifest_exception_or_mismatch_fails_closed(self, monkeypatch):
        """Verify verify_protected_baseline fails closed if manifest mismatches or errors."""
        import src.experiment.authorization as auth
        from scripts.reproduce_canonical_study import REPO_ROOT, verify_protected_baseline

        # Subtest A: Hash mismatch fails closed
        monkeypatch.setattr(auth, "compute_code_manifest_sha256", lambda root: "0" * 64)
        ok_mismatch, logs_mismatch = verify_protected_baseline(REPO_ROOT)
        assert ok_mismatch is False, "verify_protected_baseline MUST return False on mismatch"
        assert any("[MISMATCH] Code manifest SHA-256" in line for line in logs_mismatch)

        # Subtest B: Manifest computation raises exception fails closed
        def raise_manifest_err(root):
            raise RuntimeError("Corrupted code repository manifest computation")

        monkeypatch.setattr(auth, "compute_code_manifest_sha256", raise_manifest_err)
        ok_exc, logs_exc = verify_protected_baseline(REPO_ROOT)
        assert ok_exc is False, "verify_protected_baseline MUST return False on exception"
        assert any("[FAIL] Failed computing core code manifest hash" in line for line in logs_exc)


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


class TestBuilderSafetyAndVerifierStrictness:
    """Verifies target directory non-empty fail-closed and strict verifier allowlists."""

    def test_builder_refuses_non_empty_directory_and_preserves_marker(self, tmp_path):
        """Negative test: builder MUST fail closed on non-empty output_dir, preserving marker."""
        from scripts.stage_portable_public_package import build_staged_package

        target_dir = tmp_path / "staged_target"
        target_dir.mkdir(parents=True)
        marker_file = target_dir / "marker_evidence.txt"
        marker_content = "CANONICAL_PRESERVED_EVIDENCE_DO_NOT_DELETE_12345"
        marker_file.write_text(marker_content, encoding="utf-8")

        fake_source = tmp_path / "fake_source"
        fake_source.mkdir(parents=True)
        fake_orch = tmp_path / "fake_orch"
        fake_orch.mkdir(parents=True)

        with pytest.raises(FileExistsError) as exc_info:
            build_staged_package(fake_source, fake_orch, target_dir)

        assert "already exists and is not empty" in str(exc_info.value)
        # Marker must remain 100% intact and undamaged
        assert marker_file.exists(), "Marker file was deleted or moved!"
        assert marker_file.read_text(encoding="utf-8") == marker_content, (
            "Marker file content modified!"
        )
        # No extra files or directories staged
        assert list(target_dir.iterdir()) == [marker_file], "Builder created files despite raising!"

    def test_verifier_fails_closed_on_empty_manifest_inventory(self, tmp_path):
        """Negative test: public verifier MUST return False on empty manifest inventory."""
        from scripts.reproduce_canonical_study import verify_bundle_hashes

        bundle_dir = tmp_path / "empty_bundle"
        bundle_dir.mkdir(parents=True)
        manifest_file = bundle_dir / "canonical_bundle_manifest.json"
        empty_manifest = {
            "bundle_schema_version": "2.0.0",
            "derived_from": {
                "bundle_sha256": CANONICAL_BUNDLE_SHA256,
            },
            "source_file_digests": {},
            "output_file_digests": {},
        }
        manifest_file.write_text(json.dumps(empty_manifest), encoding="utf-8")

        ok, logs = verify_bundle_hashes(bundle_dir)
        assert ok is False, "Verifier must fail closed on empty inventory!"
        assert any("[FAIL] Invalid canonical inputs inventory" in line for line in logs)

    def test_verifier_fails_closed_on_incomplete_inventory(self, tmp_path):
        """Negative test: verifier MUST return False when even 1 input or output is missing."""
        from scripts.reproduce_canonical_study import (
            REQUIRED_INPUT_FILES,
            REQUIRED_OUTPUT_FILES,
            verify_bundle_hashes,
        )

        bundle_dir = tmp_path / "incomplete_bundle"
        bundle_dir.mkdir(parents=True)
        manifest_file = bundle_dir / "canonical_bundle_manifest.json"

        # Missing one input file
        partial_inputs = {k: "a" * 64 for k in list(REQUIRED_INPUT_FILES)[:-1]}
        full_outputs = {k: "b" * 64 for k in REQUIRED_OUTPUT_FILES}

        manifest = {
            "bundle_schema_version": "2.0.0",
            "derived_from": {
                "bundle_sha256": CANONICAL_BUNDLE_SHA256,
            },
            "source_file_digests": partial_inputs,
            "output_file_digests": full_outputs,
        }
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        ok, logs = verify_bundle_hashes(bundle_dir)
        assert ok is False, "Verifier must fail closed when input files count < 10!"
        assert any("[FAIL] Invalid canonical inputs inventory" in line for line in logs)

    def test_verifier_fails_closed_on_missing_provenance_or_runtime_assets(self, tmp_path):
        """Negative test: public verifier MUST return False if provenance/runtime assets missing."""
        from scripts.reproduce_canonical_study import (
            REQUIRED_INPUT_FILES,
            REQUIRED_OUTPUT_FILES,
            verify_bundle_hashes,
        )

        bundle_dir = tmp_path / "missing_prov_bundle"
        bundle_dir.mkdir(parents=True)
        manifest_file = bundle_dir / "canonical_bundle_manifest.json"

        manifest = {
            "bundle_schema_version": "2.0.0",
            "derived_from": {
                "bundle_sha256": CANONICAL_BUNDLE_SHA256,
            },
            "source_file_digests": {k: "a" * 64 for k in REQUIRED_INPUT_FILES},
            "output_file_digests": {k: "b" * 64 for k in REQUIRED_OUTPUT_FILES},
            # Missing sanitized_provenance_assets and runtime_assets
        }
        manifest_file.write_text(json.dumps(manifest), encoding="utf-8")

        ok, logs = verify_bundle_hashes(bundle_dir)
        assert ok is False, "Verifier must fail closed on missing provenance/runtime assets!"
        assert any("[FAIL] Invalid public provenance inventory" in line for line in logs)


class TestPublicStagingManifestAuthenticationAndRQBinding:
    """Verifies public release manifest authentication and secondary scope RQ binding."""

    @pytest.mark.skipif(
        not LOCAL_STAGED_BUNDLE_DIR.exists(),
        reason="Local staged bundle not found",
    )
    def test_staged_public_manifest_matches_root_approved_sha(self):
        """Positive test: staged public package manifest matches expected Root-approved SHA."""
        from scripts.reproduce_canonical_study import (
            EXPECTED_PUBLIC_MANIFEST_SHA256,
            verify_bundle_hashes,
        )

        manifest_path = LOCAL_STAGED_BUNDLE_DIR / "canonical_bundle_manifest.json"
        actual_sha = compute_sha256(manifest_path.read_bytes())
        assert actual_sha == EXPECTED_PUBLIC_MANIFEST_SHA256

        # verify_bundle_hashes succeeds with default expected sha
        ok, logs = verify_bundle_hashes(LOCAL_STAGED_BUNDLE_DIR)
        assert ok is True
        assert any(f"sha256={EXPECTED_PUBLIC_MANIFEST_SHA256}" in line for line in logs)

        # verify_bundle_hashes also succeeds when explicit matching
        # expected_manifest_sha is provided
        ok_exp, logs_exp = verify_bundle_hashes(
            LOCAL_STAGED_BUNDLE_DIR, expected_manifest_sha=EXPECTED_PUBLIC_MANIFEST_SHA256
        )
        assert ok_exp is True

    @pytest.mark.skipif(
        not LOCAL_STAGED_BUNDLE_DIR.exists(),
        reason="Local staged bundle not found",
    )
    def test_staged_public_manifest_fails_on_mismatched_expected_sha(self):
        """Negative test: verifier MUST fail closed if --expected-manifest-sha does not match."""
        from scripts.reproduce_canonical_study import verify_bundle_hashes

        wrong_sha = "0" * 64
        ok, logs = verify_bundle_hashes(LOCAL_STAGED_BUNDLE_DIR, expected_manifest_sha=wrong_sha)
        assert ok is False
        assert any("[MISMATCH] Public release manifest SHA-256" in line for line in logs)

    @pytest.mark.skipif(
        not LOCAL_STAGED_BUNDLE_DIR.exists(),
        reason="Local staged bundle not found",
    )
    def test_rq_analysis_secondary_scope_binding_hash_verified(self):
        """Positive test: outputs/rq_analysis.json has public secondary scope SHA-256 bound."""
        from scripts.reproduce_canonical_study import (
            APPROVED_PUBLIC_PROVENANCE_SPEC,
        )

        rq_path = LOCAL_STAGED_BUNDLE_DIR / "outputs/rq_analysis.json"
        rq_obj = json.loads(rq_path.read_text(encoding="utf-8"))
        actual_binding = rq_obj["analysis_run_parameters"]["secondary_scope_authorization_sha256"]
        expected_pub_sha = APPROVED_PUBLIC_PROVENANCE_SPEC[
            "provenance/s2_evaluation_execute_public.md"
        ]
        assert actual_binding == expected_pub_sha
        assert actual_binding != "b988a599800bbbb01b0418e60bfd00fbbce3ab2c4d631da678f99bfd2141c4b5"

    def test_verifier_fails_closed_on_tampered_rq_binding_hash(self, tmp_path):
        """Negative test: verifier MUST fail closed if rq_analysis binding hash does not match."""
        import shutil

        from scripts.reproduce_canonical_study import (
            EXPECTED_PUBLIC_MANIFEST_SHA256,
            verify_bundle_hashes,
        )

        if not LOCAL_STAGED_BUNDLE_DIR.exists():
            pytest.skip("Local staged bundle not found")

        # Copy staged bundle to tmp_path
        bundle_copy = tmp_path / "tampered_bundle"
        shutil.copytree(LOCAL_STAGED_BUNDLE_DIR, bundle_copy)

        # Tamper the secondary_scope_authorization_sha256 in outputs/rq_analysis.json
        rq_path = bundle_copy / "outputs/rq_analysis.json"
        rq_obj = json.loads(rq_path.read_text(encoding="utf-8"))
        rq_obj["analysis_run_parameters"]["secondary_scope_authorization_sha256"] = "1" * 64
        rq_path.write_text(json.dumps(rq_obj, indent=2), encoding="utf-8")

        ok, logs = verify_bundle_hashes(
            bundle_copy, expected_manifest_sha=EXPECTED_PUBLIC_MANIFEST_SHA256
        )
        assert ok is False
        assert any("secondary_scope_authorization_sha256 binding" in line for line in logs)

    def test_main_fails_closed_before_computation(self, monkeypatch):
        """Negative test: main() MUST exit with code 1 immediately without running replay."""
        import scripts.reproduce_canonical_study as rep

        # Mock verify_protected_baseline to fail
        monkeypatch.setattr(
            rep,
            "verify_protected_baseline",
            lambda root: (False, ["[FAIL] Simulated baseline failure"]),
        )

        replay_called = []
        monkeypatch.setattr(
            rep,
            "replay_saved_evaluation",
            lambda *args, **kwargs: replay_called.append(True) or (True, []),
        )

        monkeypatch.setattr(sys, "argv", ["reproduce_canonical_study.py", "--all"])
        exit_code = rep.main()

        assert exit_code == 1, "main() must return exit code 1 on baseline failure"
        assert len(replay_called) == 0, (
            "replay_saved_evaluation must NOT be called after verification failure"
        )

    def test_main_fails_closed_on_hash_mismatch_before_computation(self, monkeypatch):
        """Negative test: main() MUST exit 1 before computation if hash verification fails."""
        import scripts.reproduce_canonical_study as rep

        # Mock verify_protected_baseline to pass, but verify_bundle_hashes to fail
        monkeypatch.setattr(
            rep,
            "verify_protected_baseline",
            lambda root: (True, ["[PASS] Mocked baseline"]),
        )
        monkeypatch.setattr(
            rep,
            "verify_bundle_hashes",
            lambda *args, **kwargs: (False, ["[FAIL] Mocked hash mismatch"]),
        )

        replay_called = []
        monkeypatch.setattr(
            rep,
            "replay_saved_evaluation",
            lambda *args, **kwargs: replay_called.append(True) or (True, []),
        )

        monkeypatch.setattr(sys, "argv", ["reproduce_canonical_study.py", "--all"])
        exit_code = rep.main()

        assert exit_code == 1, "main() must return exit code 1 on hash verification failure"
        assert len(replay_called) == 0, (
            "replay_saved_evaluation must NOT be called after hash failure"
        )
