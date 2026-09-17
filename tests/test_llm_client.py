"""
Unit tests for Unified LLM Client (Milestone M2, Tasks T12, R2, R3).

Verifies:
1. Configuration loading from config/model.json.
2. Request construction and symmetric prompt formatting (No-RAG vs RAG).
3. Responses API as the sole frozen experimental interface (no runtime fallback).
4. All 7 parse statuses correctly produced:
   - VALID
   - INVALID_ID (syntax failure and registry failure)
   - MALFORMED_RESPONSE (broken JSON and missing field)
   - REFUSAL
   - INCOMPLETE (max tokens / length cutoff)
   - API_FAILURE (transient errors exhausted or non-retryable error)
   - TIMEOUT
5. Retries and exponential backoff behavior.
6. Total wall-clock latency measurement semantics (including retries and backoff).
7. Global live request budget enforcement (max 5 requests across lifecycle).
8. No-RAG context isolation invariant (ValueError on non-empty retrieved_context).
9. Fail-fast when API key is absent (no placeholder credentials).
10. ZERO live API calls incurred across entire test suite (strictly mocked).
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, call
import pytest
import openai

from src.llm.client import (
    LiveBudget,
    LiveBudgetExceededError,
    LLMClient,
    reset_live_budget,
)
from src.llm.schemas import ParseStatus


# ---------------------------------------------------------------------------
# Test Fixtures & Mock Response Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_live_budget():
    """Ensure global live request budget is reset before each test."""
    reset_live_budget()
    yield
    reset_live_budget()


def create_mock_usage(input_tokens=1500, output_tokens=4200):
    return SimpleNamespace(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        prompt_tokens=input_tokens,
        completion_tokens=output_tokens,
    )


def create_mock_responses_api_response(
    text: str,
    status: str = "completed",
    refusal: str | None = None,
    incomplete_details: str | None = None,
    input_tokens: int = 1500,
    output_tokens: int = 4200,
):
    """Creates a mock response matching OpenAI Responses API structure."""
    resp = SimpleNamespace(
        status=status,
        output_text=text,
        refusal=refusal,
        incomplete_details=incomplete_details,
        usage=create_mock_usage(input_tokens, output_tokens),
    )
    return resp


# ---------------------------------------------------------------------------
# 1. Configuration Loading & Initialization
# ---------------------------------------------------------------------------

def test_llm_client_initialization_defaults():
    """Verify that LLMClient correctly loads config/model.json parameters."""
    client = LLMClient(openai_client=MagicMock())
    assert client.provider == "openai"
    assert client.model == "gpt-5.6-luna"
    assert client.reasoning_effort == "xhigh"
    assert client.api_interface == "responses"
    assert client.max_output_tokens == 8192
    assert client.timeout_seconds == 120.0
    assert client.max_retries == 3
    assert client.retry_initial_delay == 1.0
    assert client.retry_backoff_factor == 2.0
    assert client.is_live is False


def test_llm_client_no_fallback_api_interface():
    """Verify that the client does NOT have a fallback_api_interface attribute."""
    client = LLMClient(openai_client=MagicMock())
    assert not hasattr(client, "fallback_api_interface")
    assert not hasattr(client, "max_completion_tokens")


# ---------------------------------------------------------------------------
# 2. Fail-Fast on Missing API Key
# ---------------------------------------------------------------------------

def test_real_client_fails_without_api_key(monkeypatch):
    """Verify that constructing a real OpenAI client without API key raises ValueError immediately."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
        LLMClient()  # No openai_client injected, no api_key, no env var


def test_real_client_succeeds_with_env_key(monkeypatch):
    """Verify that a real OpenAI client is constructed when OPENAI_API_KEY is present."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-for-unit-tests")
    client = LLMClient()
    assert isinstance(client.client, openai.OpenAI)
    assert client.is_live is True


def test_real_client_succeeds_with_injected_key(monkeypatch):
    """Verify that api_key parameter bypasses env var requirement."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient(api_key="sk-injected-test-key")
    assert isinstance(client.client, openai.OpenAI)
    assert client.is_live is True


def test_mock_client_needs_no_api_key(monkeypatch):
    """Verify that injecting a mock openai_client does not require an API key."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient(openai_client=MagicMock())
    assert client.is_live is False


def test_no_placeholder_credential_created(monkeypatch):
    """Verify that no 'unauthenticated' placeholder is ever used."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    # Must raise, not silently create with placeholder
    with pytest.raises(ValueError):
        LLMClient()


# ---------------------------------------------------------------------------
# 3. Prompt Construction & Condition Isolation
# ---------------------------------------------------------------------------

def test_llm_client_prompt_construction_no_rag():
    """Verify that No-RAG replaces {RETRIEVED_CONTEXT} with empty string."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(
        sample_id="test_001",
        endpoint_evidence="powershell.exe -enc abc",
        retrieved_context=None,
        condition="no_rag",
    )

    assert record.parse_status == ParseStatus.VALID.value
    # Inspect arguments passed to responses.create
    args, kwargs = mock_openai.responses.create.call_args
    passed_input = kwargs["input"]
    assert "powershell.exe -enc abc" in passed_input
    assert "{ENDPOINT_EVIDENCE}" not in passed_input
    assert "{RETRIEVED_CONTEXT}" not in passed_input


def test_llm_client_prompt_construction_rag_context():
    """Verify that RAG condition populates {RETRIEVED_CONTEXT} with reference text."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    mock_context = "ATT&CK Technique: T1059.001 (PowerShell)"
    record = client.predict(
        sample_id="test_002",
        endpoint_evidence="powershell.exe -enc abc",
        retrieved_context=mock_context,
        condition="rag",
    )

    assert record.condition == "rag"
    args, kwargs = mock_openai.responses.create.call_args
    passed_input = kwargs["input"]
    assert mock_context in passed_input
    assert "powershell.exe -enc abc" in passed_input


# ---------------------------------------------------------------------------
# 4. No-RAG Context Isolation Invariant
# ---------------------------------------------------------------------------

def test_no_rag_rejects_non_empty_retrieved_context():
    """No-RAG condition must raise ValueError if non-empty retrieved_context is supplied."""
    mock_openai = MagicMock()
    client = LLMClient(openai_client=mock_openai)

    with pytest.raises(ValueError, match="Research integrity violation"):
        client.predict(
            sample_id="test_isolation",
            endpoint_evidence="some log data",
            retrieved_context="ATT&CK Technique T1059.001: PowerShell execution",
            condition="no_rag",
        )

    # Verify no API call was made
    mock_openai.responses.create.assert_not_called()


def test_no_rag_allows_none_context():
    """No-RAG condition with retrieved_context=None is allowed."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(
        sample_id="test_none",
        endpoint_evidence="log data",
        retrieved_context=None,
        condition="no_rag",
    )
    assert record.parse_status == ParseStatus.VALID.value


def test_no_rag_allows_empty_string_context():
    """No-RAG condition with retrieved_context='' (empty) is allowed."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(
        sample_id="test_empty",
        endpoint_evidence="log data",
        retrieved_context="",
        condition="no_rag",
    )
    assert record.parse_status == ParseStatus.VALID.value


def test_no_rag_rejects_whitespace_only_context():
    """No-RAG condition with whitespace-only retrieved_context is allowed (strip() -> empty)."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    # Whitespace-only should pass (strip() yields "")
    record = client.predict(
        sample_id="test_ws",
        endpoint_evidence="log data",
        retrieved_context="   ",
        condition="no_rag",
    )
    assert record.parse_status == ParseStatus.VALID.value


# ---------------------------------------------------------------------------
# 5. Responses API (Sole Frozen Interface) — Valid Extraction
# ---------------------------------------------------------------------------

def test_responses_api_valid_prediction():
    """Verify successful execution via the frozen Responses API endpoint."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"}),
        input_tokens=1200,
        output_tokens=3400,
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(
        sample_id="sample_valid",
        endpoint_evidence="powershell.exe ExecutionPolicy Bypass",
    )

    assert record.parse_status == ParseStatus.VALID.value
    assert record.predicted_technique_id == "T1059.001"
    assert record.invalid_reason is None
    assert record.input_tokens == 1200
    assert record.output_tokens == 3400
    assert record.retry_count == 0
    assert record.latency_ms >= 0.0
    mock_openai.responses.create.assert_called_once()


def test_no_fallback_when_responses_api_fails():
    """Verify that Responses API errors are NOT silently retried via Chat Completions."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # Responses API raises NotImplementedError — previously this would trigger fallback
    mock_openai.responses.create.side_effect = NotImplementedError("Responses API not available")

    client = LLMClient(openai_client=mock_openai, sleep_fn=mock_sleep)
    record = client.predict(
        sample_id="sample_no_fallback",
        endpoint_evidence="test log",
    )

    # Should be API_FAILURE, NOT a successful Chat Completions response
    assert record.parse_status == ParseStatus.API_FAILURE.value
    assert record.error_type == "NotImplementedError"
    # Chat Completions should NEVER be called
    assert not hasattr(mock_openai.chat, "completions") or not mock_openai.chat.completions.create.called


# ---------------------------------------------------------------------------
# 6. Parse Status Testing: All 7 Distinct Statuses
# ---------------------------------------------------------------------------

def test_status_invalid_id_syntax_failure():
    """Response contains technique_id but with malformed syntax -> INVALID_ID."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T105"})  # Only 3 digits
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_bad_syntax", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.INVALID_ID.value
    assert record.predicted_technique_id == "T105"
    assert "Syntax error" in record.invalid_reason


def test_status_invalid_id_registry_failure():
    """Response contains syntactically valid ID absent from v19.2 -> INVALID_ID."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T9999"})
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_bad_reg", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.INVALID_ID.value
    assert record.predicted_technique_id == "T9999"
    assert "Registry error" in record.invalid_reason


def test_status_malformed_response_broken_json():
    """Response is unparseable text -> MALFORMED_RESPONSE."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        "I believe the technique is T1059."
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_broken_json", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.MALFORMED_RESPONSE.value
    assert record.predicted_technique_id is None
    assert "not valid JSON" in record.invalid_reason


def test_status_malformed_response_missing_technique_id():
    """Response is valid JSON but lacks technique_id field -> MALFORMED_RESPONSE."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique": "T1059.001"})
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_missing_field", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.MALFORMED_RESPONSE.value
    assert record.predicted_technique_id is None
    assert "Missing required 'technique_id' field" in record.invalid_reason


def test_status_refusal():
    """Model explicitly refuses classification -> REFUSAL."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        text="",
        status="refused",
        refusal="I cannot perform cyber threat analysis on this data.",
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_refusal", endpoint_evidence="malicious activity log")

    assert record.parse_status == ParseStatus.REFUSAL.value
    assert record.predicted_technique_id is None
    assert "cannot perform" in record.invalid_reason


def test_status_incomplete():
    """Model terminates before completing structured answer -> INCOMPLETE."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        text="",
        status="incomplete",
        incomplete_details="max_output_tokens reached",
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_incomplete", endpoint_evidence="verbose log")

    assert record.parse_status == ParseStatus.INCOMPLETE.value
    assert record.predicted_technique_id is None
    assert "max_output_tokens" in record.invalid_reason


def test_status_timeout_exhausted_retries():
    """Request experiences persistent timeouts across all retries -> TIMEOUT."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # Raise APITimeoutError on all attempts
    mock_openai.responses.create.side_effect = openai.APITimeoutError(request=MagicMock())

    client = LLMClient(openai_client=mock_openai, sleep_fn=mock_sleep)
    record = client.predict(sample_id="s_timeout", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.TIMEOUT.value
    assert record.predicted_technique_id is None
    assert record.retry_count == 3
    assert record.error_type == "APITimeoutError"
    # Verify mock_sleep was called 3 times (for 3 retries)
    assert mock_sleep.call_count == 3


def test_status_api_failure_non_retryable():
    """Non-retryable API error (e.g. AuthenticationError) fails immediately -> API_FAILURE."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    mock_openai.responses.create.side_effect = openai.AuthenticationError(
        "Invalid API key",
        response=MagicMock(),
        body=None,
    )

    client = LLMClient(openai_client=mock_openai, sleep_fn=mock_sleep)
    record = client.predict(sample_id="s_auth_err", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.API_FAILURE.value
    assert record.predicted_technique_id is None
    assert record.retry_count == 0
    assert record.error_type == "AuthenticationError"
    mock_sleep.assert_not_called()


# ---------------------------------------------------------------------------
# 7. Retries and Exponential Backoff
# ---------------------------------------------------------------------------

def test_transient_retries_and_exponential_backoff_recovery():
    """Verify that transient 429/500 errors trigger backoff and recover upon success."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # Fails on attempt 0 with RateLimitError, attempt 1 with InternalServerError, succeeds on attempt 2
    mock_openai.responses.create.side_effect = [
        openai.RateLimitError("Rate limit reached", response=MagicMock(), body=None),
        openai.InternalServerError("500 Internal Error", response=MagicMock(), body=None),
        create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"})),
    ]

    client = LLMClient(openai_client=mock_openai, sleep_fn=mock_sleep)
    record = client.predict(sample_id="s_retry_recovery", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.VALID.value
    assert record.predicted_technique_id == "T1059.001"
    assert record.retry_count == 2
    assert mock_openai.responses.create.call_count == 3
    assert mock_sleep.call_count == 2

    # Check backoff delays: initial 1.0s, factor 2.0 -> attempt 0 backoff: 1.0s, attempt 1: 2.0s
    mock_sleep.assert_has_calls([call(1.0), call(2.0)])


# ---------------------------------------------------------------------------
# 8. Total Wall-Clock Latency Semantics
# ---------------------------------------------------------------------------

def test_latency_ms_measures_total_wall_clock_duration():
    """Verify that latency_ms captures total wall-clock duration including all retries."""
    mock_openai = MagicMock()

    def delayed_call(*args, **kwargs):
        # Simulate small real execution time
        import time
        time.sleep(0.01)
        return create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"}))

    mock_openai.responses.create.side_effect = delayed_call

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(sample_id="s_latency", endpoint_evidence="test log")

    assert record.parse_status == ParseStatus.VALID.value
    # Latency should be at least 10ms
    assert record.latency_ms >= 10.0
    assert record.retry_count == 0


# ---------------------------------------------------------------------------
# 9. Global Live Request Budget Enforcement (Max 5 Requests)
# ---------------------------------------------------------------------------

def test_live_budget_tracker_unit_logic():
    """Verify that LiveBudget strictly enforces maximum live request limit."""
    budget = LiveBudget(max_requests=5)
    assert budget.count == 0
    assert budget.remaining == 5
    assert not budget.is_exhausted()

    for i in range(1, 6):
        consumed = budget.consume()
        assert consumed == i

    assert budget.count == 5
    assert budget.remaining == 0
    assert budget.is_exhausted()

    # 6th attempt must raise LiveBudgetExceededError
    with pytest.raises(LiveBudgetExceededError, match="budget exhausted"):
        budget.consume()


def test_client_enforces_live_budget_across_calls():
    """Verify that LLMClient in live mode stops and records failure when budget is exhausted."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    custom_budget = LiveBudget(max_requests=3)
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=custom_budget,
        is_live=True,  # Test live budget enforcement
    )

    # 3 successful requests
    for i in range(3):
        rec = client.predict(sample_id=f"live_{i}", endpoint_evidence="evidence")
        assert rec.parse_status == ParseStatus.VALID.value

    assert custom_budget.count == 3
    assert custom_budget.is_exhausted()

    # 4th request must be blocked by budget
    rec4 = client.predict(sample_id="live_4", endpoint_evidence="evidence")
    assert rec4.parse_status == ParseStatus.API_FAILURE.value
    assert "budget exhausted" in rec4.invalid_reason.lower()
    assert mock_openai.responses.create.call_count == 3


def test_client_live_budget_counts_retries():
    """Verify that retry attempts also consume live budget."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # Every call fails with RateLimitError
    mock_openai.responses.create.side_effect = openai.RateLimitError(
        "Rate limit", response=MagicMock(), body=None
    )

    custom_budget = LiveBudget(max_requests=3)
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=custom_budget,
        is_live=True,
        sleep_fn=mock_sleep,
    )

    # Request with retries should exhaust budget on attempt 3
    rec = client.predict(sample_id="live_retry", endpoint_evidence="evidence")
    # Budget was 3, so attempts 0, 1, 2 consumed all 3 slots
    assert custom_budget.count == 3
    assert custom_budget.is_exhausted()
    assert rec.parse_status == ParseStatus.API_FAILURE.value


def test_5_maximum_network_attempts():
    """Prove that at most 5 actual network requests can be dispatched with max budget."""
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # All calls fail with retryable error
    mock_openai.responses.create.side_effect = openai.RateLimitError(
        "Rate limit", response=MagicMock(), body=None
    )

    budget = LiveBudget(max_requests=5)
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=budget,
        is_live=True,
        sleep_fn=mock_sleep,
    )

    # First call: up to 4 attempts (initial + 3 retries), consuming 4 budget units
    rec1 = client.predict(sample_id="net_1", endpoint_evidence="evidence")
    assert budget.count == 4  # initial + 3 retries

    # Second call: only 1 budget unit remaining, then exhaustion
    rec2 = client.predict(sample_id="net_2", endpoint_evidence="evidence")
    assert budget.count == 5
    assert budget.is_exhausted()

    # Total actual network calls = 5 (4 from first sample + 1 from second)
    assert mock_openai.responses.create.call_count == 5

    # Third call: budget exhausted, no network request dispatched
    rec3 = client.predict(sample_id="net_3", endpoint_evidence="evidence")
    assert rec3.parse_status == ParseStatus.API_FAILURE.value
    assert "budget exhausted" in rec3.invalid_reason.lower()
    assert mock_openai.responses.create.call_count == 5  # Still 5, no new calls


def test_budget_exhaustion_prevents_network_dispatch():
    """Prove that budget exhaustion prevents any further network requests."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"})
    )

    budget = LiveBudget(max_requests=0)  # Immediately exhausted
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=budget,
        is_live=True,
    )

    rec = client.predict(sample_id="no_budget", endpoint_evidence="evidence")
    assert rec.parse_status == ParseStatus.API_FAILURE.value
    assert "budget exhausted" in rec.invalid_reason.lower()
    # No network request should have been made
    mock_openai.responses.create.assert_not_called()


def test_no_hidden_fallback_bypasses_budget():
    """Prove no hidden/fallback request can bypass the budget counter.

    Previously, a Responses API error would trigger a Chat Completions fallback
    that consumed a second network request without consuming budget. This test
    confirms that behavior is eliminated.
    """
    mock_openai = MagicMock()
    mock_sleep = MagicMock()

    # Responses API raises a non-retryable error
    mock_openai.responses.create.side_effect = NotImplementedError("Not available")

    budget = LiveBudget(max_requests=1)
    client = LLMClient(
        openai_client=mock_openai,
        live_budget=budget,
        is_live=True,
        sleep_fn=mock_sleep,
    )

    rec = client.predict(sample_id="no_hidden", endpoint_evidence="evidence")

    # Should fail as API_FAILURE, NOT silently fall back
    assert rec.parse_status == ParseStatus.API_FAILURE.value
    # Only 1 network attempt was made (the Responses API call that failed)
    assert mock_openai.responses.create.call_count == 1
    # Budget consumed exactly 1 unit
    assert budget.count == 1
