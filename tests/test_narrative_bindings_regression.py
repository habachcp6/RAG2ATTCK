"""
tests/test_narrative_bindings_regression.py

Regression test suite for F02: Narrative metric bindings condition validation.
Verifies that validate_narrative_metric_bindings() strictly binds metrics to the
active condition and rejects incorrect condition/metric associations, wrong p-values,
unauthorized Macro-F1, and inverted multi-condition comparisons.
"""

import pytest
from scripts.publication_bindings import validate_narrative_metric_bindings


class TestNarrativeBindingsRegression:
    """Test suite for reviewer F02 probe counterexamples and controls."""

    def test_counterexample_1_wrong_p_value_rejected(self):
        """1. RAG k=10 McNemar p = 0.435. must fail (canonical is 0.4219 / 0.422)."""
        text = "RAG k=10 McNemar p = 0.435."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for wrong p-value, got none in: {text}"
        assert any("mismatch" in e.lower() or "unauthorized" in e.lower() or "p-value" in e.lower() for e in errors)

    def test_counterexample_2_wrong_macro_f1_rejected(self):
        """2. No-RAG Macro-F1 = 0.0140. must fail (canonical is 0.0126; 0.0140 belongs to k=10)."""
        text = "No-RAG Macro-F1 = 0.0140."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for cross-condition F1 mismatch, got none in: {text}"
        assert any("macro-f1" in e.lower() or "f1" in e.lower() for e in errors)

    def test_counterexample_3_conditional_acc_attributed_to_norag_rejected(self):
        """3. No-RAG accuracy = 91.28%. must fail (91.28% is conditional top-10, not No-RAG 77.99%)."""
        text = "No-RAG accuracy = 91.28%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for attributing 91.28% to No-RAG, got none in: {text}"
        assert any("accuracy" in e.lower() for e in errors)

    def test_counterexample_4_out_of_range_accuracy_rejected(self):
        """4. No-RAG accuracy = 99.99%. must fail (canonical is 77.99%)."""
        text = "No-RAG accuracy = 99.99%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for bogus 99.99% accuracy, got none in: {text}"
        assert any("accuracy" in e.lower() for e in errors)

    def test_counterexample_5_inverted_comparison_rejected(self):
        """5. No-RAG accuracy = 79.53% versus RAG k=10 accuracy = 77.99%. must fail (inverted!)."""
        text = "No-RAG accuracy = 79.53% versus RAG k=10 accuracy = 77.99%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for inverted comparison, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_positive_control_norag_accuracy(self):
        """Positive control: No-RAG accuracy = 77.99%. must PASS."""
        text = "No-RAG accuracy = 77.99%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_k10_mcnemar_p(self):
        """Positive control: RAG k=10 McNemar p = 0.4219. must PASS."""
        text = "RAG k=10 McNemar p = 0.4219."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_norag_macro_f1(self):
        """Positive control: No-RAG Macro-F1 = 0.0126. must PASS."""
        text = "No-RAG Macro-F1 = 0.0126."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_ordinary_negative_control_norag_accuracy(self):
        """Ordinary negative control: No-RAG accuracy = 95.55%. must fail."""
        text = "No-RAG accuracy = 95.55%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for 95.55%, got none in: {text}"
