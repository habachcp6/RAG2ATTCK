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

from src.ground_truth import inspect_candidate_lineage_sources


def test_candidate_lineage_matrix_structure():
    """All 10 candidate sources must be evaluated across all 14 required dimensions."""
    sources = inspect_candidate_lineage_sources(Path("."))
    assert len(sources) == 10, "Must inspect all 10 candidate lineage sources"

    required_dimensions = [
        "source", "investigated_files", "candidate_keys", "semantic_scope",
        "granularity", "timestamp_availability", "time_zone_precision",
        "run_identity_availability", "technique_identity_availability",
        "possible_event_linkage", "cardinality_behavior", "ambiguity_conflicts",
        "independent_of_wazuh_detector", "acceptance_result", "rejection_reason"
    ]

    for s in sources:
        for dim in required_dimensions:
            assert dim in s, f"Dimension '{dim}' missing in source '{s.get('source')}'"

        # Every candidate source must be rejected under frozen methodology
        assert s["acceptance_result"] == "REJECTED", f"Source {s['source']} was not rejected"
        assert len(s["rejection_reason"]) > 0


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
