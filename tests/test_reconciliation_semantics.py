"""
Semantic reconciliation tests for Task 2 representation discrepancies.
"""

import json
from pathlib import Path

from src.reconcile import classify_cell_difference, reconcile_representations


def test_equivalent_boolean_and_numeric_formatting_resolves():
    period_rows = [
        {
            "_id": "row-1",
            "_source.rule.mail": "false",
            "_source.agent.id": "003",
            "_source.data.win.eventdata.utcTime": "2024-12-01 06:24:27.936",
        }
    ]
    combined_rows = [
        {
            "_id": "row-1",
            "_source.rule.mail": "FALSE",
            "_source.agent.id": "3",
            "_source.data.win.eventdata.utcTime": "45627.26699",
        }
    ]

    result = reconcile_representations(period_rows, combined_rows)

    assert result["raw_exact_equality"] is False
    assert result["representation_equivalence_resolved"] is True
    assert result["semantic_reconciliation_status"] == "RESOLVED_REPRESENTATION_EQUIVALENT"
    assert result["unresolved_discrepancy_count"] == 0


def test_unresolved_cell_difference_preserves_divergent_status():
    period_rows = [{"_id": "row-1", "_source.data.win.eventdata.param3": "--com-service"}]
    combined_rows = [{"_id": "row-1", "_source.data.win.eventdata.param3": "#NAME?"}]

    result = reconcile_representations(period_rows, combined_rows)

    assert result["representation_equivalence_resolved"] is False
    assert result["semantic_reconciliation_status"] == "RECONCILIATION_DIVERGENT"
    assert result["unresolved_discrepancy_count"] == 1
    assert result["discrepancy_taxonomy"]["by_transformation_type"]["TEXT_VALUE_CHANGED"] == 1


def test_numeric_precision_loss_is_not_auto_resolved():
    diff = classify_cell_difference("_source.id", "1733171439.18747", "1733171439")

    assert diff.transformation_type == "NUMERIC_PRECISION_OR_VALUE_LOSS"
    assert diff.is_equivalent is False


def test_production_reconciliation_artifact_contains_unresolved_taxonomy():
    log_path = Path("data/metadata/reconciliation_log.json")
    log = json.loads(log_path.read_text(encoding="utf-8"))

    assert log["multiset_equality_status"] == "RECONCILIATION_DIVERGENT"
    assert log["semantic_reconciliation_status"] == "RECONCILIATION_DIVERGENT"
    assert log["representation_equivalence_resolved"] is False
    assert log["unresolved_discrepancy_count"] > 0
    assert "discrepancy_taxonomy" in log
