"""
Unit tests for Synthetic Smoke Cases & Pipeline (Milestone M3, Tasks T14, R5, R6).

Verifies:
1. Synthetic cases file exists at data/synthetic/smoke_cases.jsonl with 20-30 cases.
2. Case structure, non-research isolation flags, and field formatting.
3. Realistic Sysmon event evidence (Events 1, 3, 11, 13, 4104).
4. All ground-truth techniques pass two-layer Enterprise ATT&CK v19.2 validation.
5. End-to-end smoke pipeline execution with mocked client (0 live API calls).
6. Comprehensive failure pathways suite covers all 7 ParseStatus members.
7. Error handling for missing files and malformed counts.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from src.baseline.smoke import (
    load_smoke_cases,
    run_failure_pathways_suite,
    run_smoke_test_pipeline,
    write_smoke_test_report,
)
from src.llm.client import (
    get_live_request_count,
    reset_live_budget,
)
from src.llm.schemas import (
    ParseStatus,
    get_workspace_root,
    load_attack_registry,
    validate_technique_id,
)


@pytest.fixture(autouse=True)
def ensure_clean_live_budget():
    """Ensure global live API budget is 0 before and after each test."""
    reset_live_budget()
    yield
    reset_live_budget()


# ---------------------------------------------------------------------------
# 1. Synthetic Cases Invariants
# ---------------------------------------------------------------------------

def test_smoke_cases_file_exists_and_quota():
    """Confirms data/synthetic/smoke_cases.jsonl exists and contains 20-30 cases."""
    ws = get_workspace_root()
    cases_file = ws / "data" / "synthetic" / "smoke_cases.jsonl"
    assert cases_file.exists(), f"Missing synthetic cases file at {cases_file}"

    cases = load_smoke_cases(cases_file)
    assert 20 <= len(cases) <= 30, f"Expected 20-30 synthetic cases, found {len(cases)}"
    assert len(cases) == 25, f"Expected exactly 25 cases, found {len(cases)}"


def test_smoke_cases_uniqueness_and_naming():
    """Confirms all sample_ids follow synthetic_### naming and are unique."""
    cases = load_smoke_cases()
    sample_ids = [c["sample_id"] for c in cases]
    assert len(sample_ids) == len(set(sample_ids)), "Duplicate sample_ids found"

    for idx, s_id in enumerate(sample_ids, 1):
        expected = f"synthetic_{idx:03d}"
        assert s_id == expected, f"Expected sample_id {expected}, got {s_id}"


def test_smoke_cases_research_isolation_guardrails():
    """Confirms non-research notices and zero answer-bearing rule leakage."""
    cases = load_smoke_cases()
    for case in cases:
        assert case.get("dataset_purpose") == "ENGINEERING_ONLY_SMOKE_TEST"
        gt = case.get("synthetic_debug_ground_truth")
        assert gt is not None, f"Missing debug ground truth in {case['sample_id']}"
        notice = gt.get("non_research_notice", "")
        assert "engineering-only" in notice.lower()
        assert "never contribute to research" in notice.lower()

        evidence = case.get("endpoint_evidence", "")
        # Confirm prohibited answer-bearing fields are NOT leaked into evidence
        assert "rule.mitre" not in evidence.lower()
        assert "rule.description" not in evidence.lower()
        assert gt["technique_id"] not in evidence


def test_smoke_cases_sysmon_event_coverage():
    """Confirms telemetry evidence includes realistic Sysmon events across the suite."""
    cases = load_smoke_cases()
    all_evidence = "\n".join(c["endpoint_evidence"] for c in cases)

    # Process Creation (Event 1)
    assert "EventID: 1" in all_evidence
    # Network Connection (Event 3)
    assert "EventID: 3" in all_evidence
    # File Create (Event 11)
    assert "EventID: 11" in all_evidence
    # Registry Event (Event 13)
    assert "EventID: 13" in all_evidence
    # Script Block Logging (Event 4104)
    assert "EventID: 4104" in all_evidence


def test_smoke_cases_ground_truth_valid_in_attack_v19_2():
    """Confirms all ground truth technique IDs are valid Enterprise ATT&CK v19.2 IDs."""
    reg = load_attack_registry()
    cases = load_smoke_cases()

    for case in cases:
        gt = case["synthetic_debug_ground_truth"]
        tech_id = gt["technique_id"]
        is_valid, status, reason = validate_technique_id(tech_id, registry_ids=reg)
        assert is_valid is True, f"Case {case['sample_id']} has invalid tech_id {tech_id}: {reason}"
        assert status == ParseStatus.VALID


# ---------------------------------------------------------------------------
# 2. Pipeline Execution and Failure Pathways
# ---------------------------------------------------------------------------

def test_failure_pathways_suite_covers_all_seven_statuses():
    """Verifies that the failure pathways suite exercises all 7 ParseStatus members."""
    reg = load_attack_registry()
    records = run_failure_pathways_suite(registry_ids=reg)

    assert len(records) == 10
    observed_statuses = {r.parse_status for r in records}

    expected_statuses = {
        ParseStatus.VALID,
        ParseStatus.INVALID_ID,
        ParseStatus.MALFORMED_RESPONSE,
        ParseStatus.REFUSAL,
        ParseStatus.INCOMPLETE,
        ParseStatus.API_FAILURE,
        ParseStatus.TIMEOUT,
    }

    assert expected_statuses.issubset(observed_statuses), (
        f"Missing statuses: {expected_statuses - observed_statuses}"
    )

    # Confirm zero live requests consumed during failure suite
    assert get_live_request_count() == 0


def test_smoke_pipeline_end_to_end_mocked(tmp_path: Path):
    """Executes the full smoke pipeline in mock mode and verifies report output."""
    test_report_path = tmp_path / "test_smoke_report.md"

    # Force unauthenticated environment to test mock path safely
    with patch.dict("os.environ", {}, clear=True):
        results = run_smoke_test_pipeline(report_path=test_report_path)

    assert results["total_synthetic_cases"] == 25
    assert results["valid_count"] == 25
    assert results["live_requests_consumed"] == 0
    assert results["mock_requests_count"] == 25
    assert test_report_path.exists()

    report_text = test_report_path.read_text(encoding="utf-8")
    assert "T14: Synthetic Smoke Test" in report_text
    assert "COMPLIANT" in report_text
    assert "synthetic_025" in report_text
    assert "pathway_timeout" in report_text


def test_smoke_cases_loading_validation_errors(tmp_path: Path):
    """Verifies that invalid synthetic cases files raise appropriate errors."""
    # Non-existent file
    with pytest.raises(FileNotFoundError):
        load_smoke_cases(tmp_path / "missing.jsonl")

    # File with too few cases (< 20)
    few_cases = tmp_path / "few.jsonl"
    few_cases.write_text(
        json.dumps({"sample_id": "s1", "endpoint_evidence": "ev"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="between 20 and 30"):
        load_smoke_cases(few_cases)


def test_regenerated_report_no_fallback_references(tmp_path: Path):
    """Verifies that the generated smoke test report contains zero fallback references,
    correctly distinguishes live samples from requests, labels mock telemetry,
    and reflects mock runtime without claiming authenticated runtime or Chat Completions.
    """
    test_report = tmp_path / "regenerated_report.md"
    results = run_smoke_test_pipeline(report_path=test_report, allow_live=False)

    assert test_report.exists()
    content = test_report.read_text(encoding="utf-8")

    # Invariant 1: Sole frozen interface declared, no runtime fallback
    assert "Responses API execution (sole frozen experimental interface, no runtime fallback)" in content
    assert "Chat Completions" not in content
    assert "fallback_api_interface" not in content

    # Invariant 2: No 'fallback' references in report (case-insensitive) except in "no runtime fallback"
    fallback_count = content.lower().count("fallback")
    assert fallback_count == 1, f"Expected exactly 1 occurrence of 'fallback' (in 'no runtime fallback'), got {fallback_count}"

    # Invariant 3: Mock-only runtime status and cost when 0 live calls
    assert "Mock-only / unauthenticated test runtime" in content
    assert "Authenticated Runtime" not in content
    assert "$0.00 (no live requests)" in content
    assert "*(mock telemetry)*" in content

    # Invariant 4: Live samples dispatched vs Live API requests consumed distinct reporting
    assert "Live Samples Dispatched" in content
    assert "Live API Requests Consumed" in content
    assert "per-process smoke-test live request cap" in content


def test_smoke_mock_by_default_even_with_key(monkeypatch, tmp_path: Path):
    """Verifies that run_smoke_test_pipeline defaults to mock even if OPENAI_API_KEY is present."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-env-key-for-smoke-test")
    test_report = tmp_path / "mock_default_report.md"

    res = run_smoke_test_pipeline(report_path=test_report)

    assert res["live_api_requests_consumed"] == 0
    assert res["live_samples_dispatched"] == 0
    assert res["mock_requests_count"] == 25
    assert res["total_synthetic_cases"] == 25


def test_allow_live_without_api_key_raises_value_error(monkeypatch, tmp_path: Path):
    """
    Verifies that allow_live=True raises ValueError immediately when OPENAI_API_KEY
    is absent — no silent fallback to mock mode when live execution is explicitly requested.
    Zero live API requests are consumed before the error.
    """
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    test_report = tmp_path / "live_missing_key_report.md"

    initial_count = get_live_request_count()

    with pytest.raises(ValueError, match="allow_live=True was specified but OPENAI_API_KEY is not set"):
        run_smoke_test_pipeline(report_path=test_report, allow_live=True)

    # No live API requests consumed before the error
    assert get_live_request_count() == initial_count
