"""
tests/test_narrative_bindings_regression.py

Regression test suite for F02: Narrative metric bindings condition validation.
Verifies that validate_narrative_metric_bindings() strictly binds metrics to the
active condition and rejects incorrect condition/metric associations, wrong p-values,
unauthorized Macro-F1, and inverted multi-condition comparisons.
Includes all Reviewer R3 probe counterexamples and positive/negative controls.
"""

import pytest
from scripts.publication_bindings import validate_narrative_metric_bindings


class TestNarrativeBindingsRegression:
    """Test suite for reviewer F02 probe counterexamples and controls."""

    # --- Previous Round Regression Cases ---

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

    # --- Reviewer R3 Specific Probes (A through G) ---

    def test_reviewer_probe_a_norag_mcnemar_p_rejected(self):
        """A. No-RAG McNemar p = 0.9999. must fail (Baseline has no McNemar p-value)."""
        text = "No-RAG McNemar p = 0.9999."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for baseline McNemar p-value, got none in: {text}"
        assert any("baseline" in e.lower() or "mcnemar" in e.lower() for e in errors)

    def test_reviewer_probe_b_norag_low_accuracy_rejected(self):
        """B. No-RAG accuracy = 12.34%. must fail (canonical is 77.99%; not bypassed by range gate)."""
        text = "No-RAG accuracy = 12.34%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for 12.34% accuracy, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_reviewer_probe_c_norag_over_100_accuracy_rejected(self):
        """C. No-RAG accuracy = 101%. must fail (canonical is 77.99%)."""
        text = "No-RAG accuracy = 101%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for 101% accuracy, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_reviewer_probe_d_norag_views_accuracy_rejected(self):
        """D. No-RAG accuracy on 718 views = 91.28%. must fail ('views' does not bypass condition)."""
        text = "No-RAG accuracy on 718 views = 91.28%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for views bypass, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_reviewer_probe_e_norag_brackets_accuracy_rejected(self):
        """E. [No-RAG] accuracy = 91.28%. must fail (square brackets do not bypass condition)."""
        text = "[No-RAG] accuracy = 91.28%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for bracket bypass, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_reviewer_probe_f_norag_test_word_accuracy_rejected(self):
        """F. No-RAG TEST accuracy = 100%. must fail ('TEST' does not bypass headline accuracy)."""
        text = "No-RAG TEST accuracy = 100%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for TEST accuracy bypass, got none in: {text}"
        assert any("accuracy" in e.lower() or "mismatch" in e.lower() for e in errors)

    def test_reviewer_probe_g_table_cell_condition_mismatch_rejected(self):
        """G. | No-RAG | Accuracy | 79.53% | must fail (79.53% belongs to RAG k=10, not No-RAG)."""
        text = "| No-RAG | Accuracy | 79.53% |"
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for table condition mismatch, got none in: {text}"
        assert any("accuracy" in e.lower() or "unauthorized" in e.lower() or "mismatch" in e.lower() for e in errors)

    # --- Positive Controls ---

    def test_positive_control_norag_accuracy(self):
        """Positive control: No-RAG accuracy = 77.99%. must PASS."""
        text = "No-RAG accuracy = 77.99%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_rag_k10_accuracy(self):
        """Positive control: RAG k=10 accuracy = 79.53%. must PASS."""
        text = "RAG k=10 accuracy = 79.53%."
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

    def test_positive_control_valid_comparative_statement(self):
        """Positive control: RAG k=10 accuracy = 79.53% versus No-RAG accuracy = 77.99%. must PASS."""
        text = "RAG k=10 accuracy = 79.53% versus No-RAG accuracy = 77.99%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_delta_comparison(self):
        """Positive control: RAG k=10 vs No-RAG: Delta +1.532 pp (79.53% vs 77.99%). must PASS."""
        text = "RAG k=10 vs No-RAG: Delta +1.532 pp (79.53% vs 77.99%)."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_table_cells_correct(self):
        """Positive control: correct table cells must PASS."""
        text = "| No-RAG | 77.99% |\n| RAG (k=10) | 79.53% |"
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_test_suite_passing(self):
        """Positive control: 100% test suite passing must PASS."""
        text = "All tests passed with 100% pass rate across the test suite."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_positive_control_ci_bracket(self):
        """Positive control: CI bracket numbers must PASS."""
        text = "No-RAG achieved 77.99% accuracy [74.64%, 80.88%]."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass, got errors: {errors}"

    def test_ordinary_negative_control_norag_accuracy(self):
        """Ordinary negative control: No-RAG accuracy = 95.55%. must fail."""
        text = "No-RAG accuracy = 95.55%."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected error for 95.55%, got none in: {text}"

    def test_rag_k5_wrong_p_value_0_0315_rejected(self):
        """Reviewer R5 Finding: RAG k=5 with p=0.0315 must be REJECTED fail-closed."""
        text = "RAG k=5 versus No-RAG exact McNemar p = 0.0315."
        errors = validate_narrative_metric_bindings(text, "test")
        assert len(errors) > 0, f"Expected rejection for p=0.0315 attributed to rag_k5, got: {errors}"
        assert any("rag_k5" in e or "mismatched McNemar p-value" in e for e in errors)

    def test_rag_k5_positive_control_p_value_0_677(self):
        """Reviewer R5 Finding: RAG k=5 versus No-RAG exact McNemar p = 0.677 must PASS."""
        text = "RAG k=5 versus No-RAG exact McNemar p = 0.677."
        errors = validate_narrative_metric_bindings(text, "test")
        assert errors == [], f"Expected pass for p=0.677, got errors: {errors}"

    def test_table_subgroup_in_headline_accuracy_cell_rejected(self):
        """Reviewer R5 Finding: Table with 'Accuracy' header must REJECT subgroup value 87.05% for No-RAG."""
        table_text = (
            "| Condition | Accuracy |\n"
            "|---|---|\n"
            "| No-RAG | 87.05% |\n"
        )
        errors = validate_narrative_metric_bindings(table_text, "test")
        assert len(errors) > 0, f"Expected rejection for subgroup 87.05% in headline accuracy column, got: {errors}"
        assert any("mismatched headline accuracy" in e for e in errors)

    def test_table_positive_control_with_header(self):
        """Reviewer R5 Finding: Table with 'Accuracy' header and true headline accuracy 77.99% must PASS."""
        table_text = (
            "| Condition | Accuracy |\n"
            "|---|---|\n"
            "| No-RAG | 77.99% |\n"
            "| RAG (k=10) | 79.53% |\n"
        )
        errors = validate_narrative_metric_bindings(table_text, "test")
        assert errors == [], f"Expected pass for correct table headline accuracy, got errors: {errors}"
