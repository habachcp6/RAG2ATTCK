"""Unit and Regression Test Suite for Canonical Offline Replay & Integrity.

Author: Native Agent A (Track A - Audit & Recovery)
Scope: RAG2ATTCK Canonical Replay Verification (PR #24)
Egress Invariant: Strictly offline verification without provider calls.
"""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path

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
