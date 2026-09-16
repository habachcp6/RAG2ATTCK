"""
Unit and integration tests for Task 4 Independent Ground Truth Audit (src/ground_truth.py).
Enforces the frozen methodology:
- Rejection of detector labels as independent ground truth
- Rejection of scenario lists and temporal proximity alone
- Comprehensive evaluation of all 10 candidate lineage sources across 14 dimensions
- Multi-label record detection and accounting
- Blocker finding formulation and downstream halting
"""

import json
from pathlib import Path
import pytest

from src.ground_truth import evaluate_lineage_evidence, inspect_candidate_lineage_sources


def test_candidate_lineage_matrix_structure():
    """All 10 candidate sources must be evaluated across required evidence dimensions."""
    sources = inspect_candidate_lineage_sources(Path("."))
    assert len(sources) == 10, "Must inspect all 10 candidate lineage sources"

    required_dimensions = [
        "source", "investigated_files", "candidate_keys", "semantic_scope",
        "granularity", "timestamp_availability", "time_zone_precision",
        "run_identity_availability", "technique_identity_availability",
        "possible_event_linkage", "cardinality_behavior", "ambiguity_conflicts",
        "independent_of_wazuh_detector", "evidence", "decision",
        "acceptance_result", "rejection_reason"
    ]

    for s in sources:
        for dim in required_dimensions:
            assert dim in s, f"Dimension '{dim}' missing in source '{s.get('source')}'"

        assert s["acceptance_result"] == s["decision"]["acceptance_result"]
        assert s["rejection_reason"] == s["decision"]["reason"]


def test_independent_execution_lineage_fixture_accepts():
    """Decision logic must be capable of accepting valid independent event lineage."""
    decision = evaluate_lineage_evidence(
        {
            "source": "synthetic_independent_operation_log",
            "granularity": "event_execution_level",
            "independent_of_wazuh_detector": True,
            "has_event_level_join_key": True,
            "has_run_identifier": True,
            "has_execution_identifier": True,
            "has_technique_identifier": True,
            "has_execution_boundaries": True,
            "coverage_ratio": 1.0,
            "conflicting_mappings_count": 0,
            "linkage_cardinality": "one_to_one",
            "uses_temporal_proximity_only": False,
        }
    )

    assert decision["acceptance_result"] == "ACCEPTED"


def test_detector_derived_lineage_fixture_rejects():
    decision = evaluate_lineage_evidence(
        {
            "source": "wazuh_rule_labels",
            "granularity": "alert_event_level",
            "independent_of_wazuh_detector": False,
            "has_event_level_join_key": True,
            "has_technique_identifier": True,
            "coverage_ratio": 1.0,
        }
    )

    assert decision["acceptance_result"] == "REJECTED"
    assert "detector" in decision["reason"].lower()


def test_scenario_wide_lineage_fixture_rejects():
    decision = evaluate_lineage_evidence(
        {
            "source": "scenario_manifest",
            "granularity": "scenario_campaign_level",
            "independent_of_wazuh_detector": True,
            "has_event_level_join_key": False,
            "has_technique_identifier": True,
            "coverage_ratio": 1.0,
        }
    )

    assert decision["acceptance_result"] == "REJECTED"
    assert "event-level" in decision["reason"]


def test_timestamp_only_lineage_fixture_rejects():
    decision = evaluate_lineage_evidence(
        {
            "source": "timestamps_only",
            "granularity": "event_millisecond_level",
            "independent_of_wazuh_detector": True,
            "has_event_level_join_key": False,
            "has_execution_boundaries": False,
            "uses_temporal_proximity_only": True,
            "coverage_ratio": 1.0,
        }
    )

    assert decision["acceptance_result"] == "REJECTED"
    assert "temporal proximity" in decision["reason"].lower()


def test_ambiguous_partial_lineage_fixture_requires_review_or_rejects():
    decision = evaluate_lineage_evidence(
        {
            "source": "partial_operation_log",
            "granularity": "event_execution_level",
            "independent_of_wazuh_detector": True,
            "has_event_level_join_key": True,
            "has_run_identifier": True,
            "has_execution_identifier": True,
            "has_technique_identifier": True,
            "has_execution_boundaries": True,
            "coverage_ratio": 0.42,
            "conflicting_mappings_count": 7,
            "linkage_cardinality": "one_to_many",
            "uses_temporal_proximity_only": False,
        }
    )

    assert decision["acceptance_result"] in {"REJECTED", "REQUIRES_REVIEW"}


def test_detector_rules_not_independent_gt():
    """Wazuh rule mapping source must be flagged as NOT independent of detector."""
    sources = inspect_candidate_lineage_sources(Path("."))
    rule_source = next(s for s in sources if s["source"] == "period_telemetry_csvs")
    assert rule_source["independent_of_wazuh_detector"] is False
    assert rule_source["acceptance_result"] == "REJECTED"
    assert "detector/rule mappings cannot be promoted to independent" in rule_source["rejection_reason"]


def test_scenario_list_and_temporal_proximity_rejection():
    """Scenario-wide lists and temporal proximity alone must be rejected."""
    sources = inspect_candidate_lineage_sources(Path("."))
    scenario_source = next(s for s in sources if s["source"] == "scenario_manifest_csv")
    temporal_source = next(s for s in sources if s["source"] == "telemetry_timestamps_and_time_zones")

    assert scenario_source["acceptance_result"] == "REJECTED"
    assert temporal_source["acceptance_result"] == "REJECTED"


def test_production_join_diagnostics():
    """Production join_diagnostics.json must reflect accurate counts and multi-labels."""
    diag_path = Path("data/metadata/join_diagnostics.json")
    assert diag_path.exists(), "join_diagnostics.json must exist"

    with open(diag_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    assert d["total_records"] == 102011
    assert d["records_with_wazuh_rule"] == 102011
    assert d["records_with_mitre_mapping"] == 63619
    assert d["unlabeled_records"] == 38392
    assert d["single_label_records"] == 51398
    assert d["multi_label_records"] == 12221

    # Exact sum accounting
    assert d["single_label_records"] + d["multi_label_records"] == d["records_with_mitre_mapping"]
    assert d["records_with_mitre_mapping"] + d["unlabeled_records"] == d["total_records"]

    # Distinct rule counts
    assert d["total_distinct_wazuh_rules_fired"] == 153
    assert d["distinct_wazuh_rules_with_mitre_mapping"] == 89
    assert d["distinct_mitre_techniques"] == 45

    # Gate status
    assert d["gate_status"] == "BLOCKED_STOP"
    assert d["independent_lineage_available"] is False


def test_production_gate_blocker_task4():
    """Task 4 gate blocker artifact must formulate the exact required finding and warnings."""
    blocker_path = Path("data/metadata/gate_blocker_task4.json")
    assert blocker_path.exists(), "gate_blocker_task4.json must exist"

    with open(blocker_path, "r", encoding="utf-8") as f:
        blocker = json.load(f)

    assert blocker["status"] == "STOP"
    assert blocker["independent_lineage_available"] is False
    assert "Windows-APT 2025 v3 does not currently satisfy the frozen primary event-level ground-truth requirement" in blocker["blocker_reason"]
    assert "Windows-APT 2025 v3 does not currently satisfy the frozen primary event-level ground-truth requirement" in blocker["methodological_standing"]["statement"]
    assert "substantive methodological revision" in blocker["methodological_standing"]["relaxing_requirement_warning"]

    # Downstream tasks must be NOT_RUN
    downstream = blocker["affected_downstream_tasks"]
    for task_id, status_desc in downstream.items():
        assert "NOT_RUN" in status_desc, f"Downstream task {task_id} must be NOT_RUN"


def test_blocker_and_provenance_reports_exist():
    """Task 4 Markdown reports must exist and be populated."""
    provenance_md = Path("reports/ground_truth_provenance.md")
    blocker_md = Path("reports/gate_blocker_task4.md")

    assert provenance_md.exists()
    assert blocker_md.exists()
    assert provenance_md.stat().st_size > 1000
    assert blocker_md.stat().st_size > 1000
