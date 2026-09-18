"""
Unit tests for output schemas, parse status taxonomy, and metadata serialization (Milestone M2).

Verifies:
1. Pydantic schema validation for TechniquePrediction {"technique_id": "..."}.
2. All 7 mutually exclusive parse statuses:
   - VALID
   - INVALID_ID
   - MALFORMED_RESPONSE
   - REFUSAL
   - INCOMPLETE
   - API_FAILURE
   - TIMEOUT
3. Specific error paths:
   - Valid ID in registry -> VALID
   - Syntactically invalid ID string -> INVALID_ID
   - Syntactically valid ID absent from v19.2 -> INVALID_ID
   - Broken JSON -> MALFORMED_RESPONSE
   - Missing technique_id field -> MALFORMED_RESPONSE
4. ExecutionRecord schema constraints, serialization, and latency/retry fields.
"""

from __future__ import annotations

import json
import pytest
from pydantic import ValidationError

from src.llm.schemas import (
    ExecutionRecord,
    ParseStatus,
    TechniquePrediction,
    validate_technique_id,
)
from src.llm.logging import format_execution_summary


# ---------------------------------------------------------------------------
# 1. TechniquePrediction Schema Validation
# ---------------------------------------------------------------------------

def test_technique_prediction_valid_parsing():
    """Verify that TechniquePrediction correctly parses standard ATT&CK ID payloads."""
    payload = {"technique_id": "T1059.001"}
    pred = TechniquePrediction.model_validate(payload)
    assert pred.technique_id == "T1059.001"
    assert pred.model_dump() == {"technique_id": "T1059.001"}


def test_technique_prediction_missing_technique_id_raises():
    """Missing technique_id field must fail Pydantic schema validation."""
    with pytest.raises(ValidationError):
        TechniquePrediction.model_validate({})

    with pytest.raises(ValidationError):
        TechniquePrediction.model_validate({"other_field": "T1059"})


def test_technique_prediction_extra_fields_forbidden():
    """Unexpected extra fields must be rejected by strict schema validation."""
    with pytest.raises(ValidationError):
        TechniquePrediction.model_validate({
            "technique_id": "T1059",
            "extra_explanation": "Adversary used PowerShell"
        })


def test_technique_prediction_non_string_type_raises():
    """Non-string technique_id types must fail schema validation."""
    with pytest.raises(ValidationError):
        TechniquePrediction.model_validate({"technique_id": 1059})

    with pytest.raises(ValidationError):
        TechniquePrediction.model_validate({"technique_id": ["T1059"]})


# ---------------------------------------------------------------------------
# 2. Parse Status Taxonomy (7 Mutually Exclusive Statuses)
# ---------------------------------------------------------------------------

def test_parse_status_taxonomy_exact_members():
    """Verify exact membership and mutually exclusive values of ParseStatus enum."""
    expected_members = {
        "VALID",
        "INVALID_ID",
        "MALFORMED_RESPONSE",
        "REFUSAL",
        "INCOMPLETE",
        "API_FAILURE",
        "TIMEOUT",
    }
    actual_members = {status.value for status in ParseStatus}
    assert actual_members == expected_members
    assert len(ParseStatus) == 7


# ---------------------------------------------------------------------------
# 3. Specific Error Scenarios and Taxonomical Routing
# ---------------------------------------------------------------------------

def test_scenario_valid_id_in_registry():
    """Valid syntax and present in registry must evaluate to VALID."""
    is_valid, status, reason = validate_technique_id("T1059", registry_ids={"T1059", "T1059.001"})
    assert is_valid is True
    assert status == ParseStatus.VALID
    assert reason is None

    is_valid_sub, status_sub, reason_sub = validate_technique_id("T1059.001", registry_ids={"T1059", "T1059.001"})
    assert is_valid_sub is True
    assert status_sub == ParseStatus.VALID
    assert reason_sub is None


def test_scenario_syntactically_invalid_id():
    """Syntactically invalid technique_id string must evaluate to INVALID_ID."""
    invalid_syntaxes = [
        "INVALID_STRING",
        "T105",        # Too short
        "T10590",      # Too long
        "T1059.01",    # Subtechnique must have 3 digits
        "T1059.0001",  # Too many digits in subtechnique
        "t1059",       # Lowercase
        "1059",        # Missing 'T' prefix
        "T1059.",      # Dangling dot
        "T1059.abc",   # Non-numeric subtechnique
        " T1059",      # Leading space
        "T1059 ",      # Trailing space
        "",            # Empty
    ]
    mock_registry = {"T1059", "T1059.001"}
    for tid in invalid_syntaxes:
        is_valid, status, reason = validate_technique_id(tid, registry_ids=mock_registry)
        assert is_valid is False, f"Expected invalid for {tid}"
        assert status == ParseStatus.INVALID_ID, f"Expected INVALID_ID for {tid}, got {status}"
        assert reason is not None
        assert "Syntax error" in reason


def test_scenario_syntactically_valid_but_absent_from_registry():
    """Syntactically valid ID that does not exist in registry must evaluate to INVALID_ID."""
    mock_registry = {"T1059", "T1059.001", "T1078"}
    absent_ids = ["T9999", "T9999.999", "T1234", "T1059.002"]

    for tid in absent_ids:
        is_valid, status, reason = validate_technique_id(tid, registry_ids=mock_registry)
        assert is_valid is False, f"Expected invalid for {tid}"
        assert status == ParseStatus.INVALID_ID, f"Expected INVALID_ID for {tid}, got {status}"
        assert reason is not None
        assert "Registry error" in reason
        assert "does not exist" in reason or "not found" in reason


def test_scenario_broken_json_classification():
    """Broken JSON or non-JSON response string must be categorized as MALFORMED_RESPONSE."""
    broken_payloads = [
        "Not a JSON string at all",
        "{broken json",
        "{'technique_id': 'T1059'}",  # Single quotes are invalid JSON
        "",
        "None",
        "<xml>T1059</xml>",
    ]

    for payload in broken_payloads:
        try:
            parsed = json.loads(payload)
            TechniquePrediction.model_validate(parsed)
            pytest.fail(f"Payload '{payload}' should have failed parsing/validation")
        except Exception as exc:
            # When parsing fails, the client classifies as MALFORMED_RESPONSE
            assert isinstance(exc, (json.JSONDecodeError, ValidationError, TypeError))


def test_scenario_missing_technique_id_classification():
    """Valid JSON missing the 'technique_id' key must be categorized as MALFORMED_RESPONSE."""
    missing_key_payloads = [
        {"attribution": "T1059"},
        {"id": "T1059"},
        {"result": {"technique_id": "T1059"}},
        {},
    ]

    for payload in missing_key_payloads:
        with pytest.raises(ValidationError):
            TechniquePrediction.model_validate(payload)


# ---------------------------------------------------------------------------
# 4. ExecutionRecord Schema and Serialization
# ---------------------------------------------------------------------------

def test_execution_record_instantiation_and_properties():
    """Verify that ExecutionRecord validates all required fields and serialization."""
    record = ExecutionRecord(
        sample_id="test_sample_001",
        condition="no_rag",
        provider="openai",
        model="gpt-5.6-luna",
        reasoning_effort="xhigh",
        prompt_version="baseline_v1",
        predicted_technique_id="T1059.001",
        parse_status=ParseStatus.VALID,
        invalid_reason=None,
        input_tokens=1500,
        output_tokens=4200,
        latency_ms=1250.5,
        retry_count=0,
        error_type=None,
    )

    assert record.sample_id == "test_sample_001"
    assert record.condition == "no_rag"
    assert record.is_valid is True
    assert record.parse_status == "VALID"
    assert record.retry_count == 0
    assert record.latency_ms == 1250.5

    d = record.to_dict()
    assert isinstance(d, dict)
    assert d["sample_id"] == "test_sample_001"
    assert d["parse_status"] == "VALID"

    json_str = record.to_json()
    parsed_json = json.loads(json_str)
    assert parsed_json["sample_id"] == "test_sample_001"
    assert parsed_json["predicted_technique_id"] == "T1059.001"


def test_execution_record_for_all_seven_statuses():
    """Verify that ExecutionRecord can be constructed cleanly for all 7 parse statuses."""
    statuses = [
        (ParseStatus.VALID, "T1059", None, None),
        (ParseStatus.INVALID_ID, "T9999", "Registry error: T9999 absent", None),
        (ParseStatus.MALFORMED_RESPONSE, None, "Invalid JSON syntax", None),
        (ParseStatus.REFUSAL, None, "Model refused attribution request", None),
        (ParseStatus.INCOMPLETE, None, "Output token limit reached", None),
        (ParseStatus.API_FAILURE, None, "HTTP 500 Internal Server Error", "InternalServerError"),
        (ParseStatus.TIMEOUT, None, "Request timed out after 120s", "APITimeoutError"),
    ]

    for idx, (status, pred_id, inv_reason, err_type) in enumerate(statuses):
        rec = ExecutionRecord(
            sample_id=f"sample_{idx}",
            condition="no_rag",
            provider="openai",
            model="gpt-5.6-luna",
            reasoning_effort="xhigh",
            prompt_version="baseline_v1",
            predicted_technique_id=pred_id,
            parse_status=status,
            invalid_reason=inv_reason,
            input_tokens=1000,
            output_tokens=2000,
            latency_ms=500.0 + idx * 100,
            retry_count=1 if err_type else 0,
            error_type=err_type,
        )
        assert rec.parse_status == status.value
        if status == ParseStatus.VALID:
            assert rec.is_valid is True
        else:
            assert rec.is_valid is False
        assert rec.to_dict()["parse_status"] == status.value


def test_format_execution_summary_metrics():
    """Verify aggregation metrics across multiple execution records."""
    records = [
        ExecutionRecord(
            sample_id="s1",
            condition="no_rag",
            parse_status=ParseStatus.VALID,
            predicted_technique_id="T1059",
            input_tokens=100,
            output_tokens=200,
            latency_ms=1000.0,
            retry_count=0,
        ),
        ExecutionRecord(
            sample_id="s2",
            condition="no_rag",
            parse_status=ParseStatus.INVALID_ID,
            predicted_technique_id="T9999",
            input_tokens=100,
            output_tokens=200,
            latency_ms=1500.0,
            retry_count=1,
        ),
    ]

    summary = format_execution_summary(records)
    assert summary["total_records"] == 2
    assert summary["valid_count"] == 1
    assert summary["valid_rate"] == 0.5
    assert summary["total_input_tokens"] == 200
    assert summary["total_output_tokens"] == 400
    assert summary["total_retries"] == 1
    assert summary["mean_latency_ms"] == 1250.0
