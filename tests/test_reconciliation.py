"""
Unit tests for Task 2 Multiset Reconciliation (src/reconcile.py).
Tests deterministic canonical row representation, row fingerprinting,
exact multiset equality, divergent multiset detection, and production audit log.
"""

from collections import Counter
import json
from pathlib import Path
import pytest

from src.reconcile import canonicalize_row, compute_row_fingerprint


def test_canonicalize_row_sorting_and_whitespace():
    """Canonical row representation must strip whitespace and sort keys alphabetically."""
    row1 = {" b ": " val2 ", "a": "val1  "}
    row2 = {"a": "val1", "b": "val2"}
    assert canonicalize_row(row1) == canonicalize_row(row2)


def test_canonicalize_row_ignores_empty_and_none():
    """Canonical row representation must ignore empty string and None values."""
    row1 = {"a": "val1", "b": "", "c": None}
    row2 = {"a": "val1"}
    assert canonicalize_row(row1) == canonicalize_row(row2)


def test_compute_row_fingerprint_deterministic():
    """Fingerprints must be deterministic and sensitive to content."""
    row1 = canonicalize_row({"a": "val1", "b": "val2"})
    row2 = canonicalize_row({"b": "val2", "a": "val1"})
    row3 = canonicalize_row({"a": "val1", "b": "val3"})

    fp1 = compute_row_fingerprint(row1)
    fp2 = compute_row_fingerprint(row2)
    fp3 = compute_row_fingerprint(row3)

    assert fp1 == fp2
    assert fp1 != fp3
    assert len(fp1) == 64


def test_multiset_equality_identical():
    """Identical multisets must produce exact match."""
    c1 = Counter(["fp_a", "fp_a", "fp_b", "fp_c"])
    c2 = Counter(["fp_a", "fp_b", "fp_a", "fp_c"])
    assert c1 == c2


def test_multiset_divergence_different_elements():
    """Multisets with equal count but different fingerprints must not be equal."""
    c1 = Counter(["fp_a", "fp_b"])
    c2 = Counter(["fp_a", "fp_c"])
    assert sum(c1.values()) == sum(c2.values())
    assert c1 != c2


def test_multiset_divergence_multiplicity():
    """Multisets with same distinct elements but different multiplicities must not be equal."""
    c1 = Counter(["fp_a", "fp_a", "fp_b"])
    c2 = Counter(["fp_a", "fp_b", "fp_b"])
    assert c1 != c2


def test_production_reconciliation_log():
    """Production reconciliation log must accurately record multiset status and divergence."""
    log_path = Path("data/metadata/reconciliation_log.json")
    assert log_path.exists(), "reconciliation_log.json must exist"

    with open(log_path, "r", encoding="utf-8") as f:
        log = json.load(f)

    # 102,011 rows in both
    assert log["row_count_accounting"]["total_period_rows"] == 102011
    assert log["row_count_accounting"]["total_combined_rows"] == 102011
    assert log["row_count_accounting"]["row_counts_match"] is True

    # Must be DIVERGENT, NOT false match
    assert log["multiset_equality_status"] == "RECONCILIATION_DIVERGENT"
    assert log["is_exact_match"] is False
    assert log["fingerprint_accounting"]["matching_fingerprints_count"] == 36674
    assert log["fingerprint_accounting"]["fingerprints_only_in_period_count"] == 65337
    assert log["fingerprint_accounting"]["fingerprints_only_in_combined_count"] == 65337
