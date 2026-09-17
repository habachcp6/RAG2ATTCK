"""
Unit tests for Unified LLM Client (Milestone M2, Tasks T12, R2, R3).

Verifies:
1. Configuration loading from config/model.json.
2. Request construction and symmetric prompt formatting (No-RAG vs RAG).
3. Primary Responses API execution with Pydantic structured output.
4. Operational fallback to Chat Completions API.
5. All 7 parse statuses correctly produced:
   - VALID
   - INVALID_ID (syntax failure and registry failure)
   - MALFORMED_RESPONSE (broken JSON and missing field)
   - REFUSAL
   - INCOMPLETE (max tokens / length cutoff)
   - API_FAILURE (transient errors exhausted or non-retryable error)
   - TIMEOUT
6. Retries and exponential backoff behavior.
7. Total wall-clock latency measurement semantics (including retries and backoff).
8. Global live request budget enforcement (max 5 requests across lifecycle).
9. ZERO live API calls incurred across entire test suite (strictly mocked).
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


def create_mock_chat_completion_response(
    content: str | None,
    finish_reason: str = "stop",
    refusal: str | None = None,
    input_tokens: int = 1500,
    output_tokens: int = 4200,
):
    """Creates a mock response matching OpenAI Chat Completions API structure."""
    message = SimpleNamespace(
        content=content,
        refusal=refusal,
        role="assistant",
    )
    choice = SimpleNamespace(
        message=message,
        finish_reason=finish_reason,
    )
    return SimpleNamespace(
        choices=[choice],
        usage=create_mock_usage(input_tokens, output_tokens),
    )


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
    assert client.fallback_api_interface == "chat_completions"
    assert client.max_output_tokens == 8192
    assert client.max_completion_tokens == 8192
    assert client.timeout_seconds == 120.0
    assert client.max_retries == 3
    assert client.retry_initial_delay == 1.0
    assert client.retry_backoff_factor == 2.0
    assert client.is_live is False


def test_llm_client_default_instantiation_without_key(monkeypatch):
    """Verify default constructor LLMClient() succeeds without NameError when OPENAI_API_KEY is unset."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = LLMClient()
    assert isinstance(client.client, openai.OpenAI)
    assert client.provider == "openai"
    assert client.model == "gpt-5.6-luna"
    assert client.is_live is True


def test_llm_client_default_instantiation_with_key(monkeypatch):
    """Verify default constructor LLMClient() succeeds when OPENAI_API_KEY is provided via env."""
    monkeypatch.setenv("OPENAI_API_KEY", "MOCK_ENV_OPENAI_KEY_FOR_TESTING")
    client = LLMClient()
    assert isinstance(client.client, openai.OpenAI)
    assert client.is_live is True


def test_llm_client_live_flag_requires_key_when_unset(monkeypatch):
    """Verify that is_live=True raises ValueError if no API key is resolved."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
        LLMClient(is_live=True)


# ---------------------------------------------------------------------------
# 2. Prompt Construction & Condition Isolation
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
    # Ensure no retrieval text present
    assert "REFERENCE CONTEXT:\n\n---" in passed_input or "REFERENCE CONTEXT:\r\n\r\n---" in passed_input or "REFERENCE CONTEXT:\n\n" in passed_input


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
# 3. Responses API Primary Interface & Valid Extraction
# ---------------------------------------------------------------------------

def test_responses_api_valid_prediction():
    """Verify successful execution via primary Responses API endpoint."""
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


# ---------------------------------------------------------------------------
# 4. Fallback to Chat Completions API
# ---------------------------------------------------------------------------

def test_fallback_to_chat_completions_when_responses_fails():
    """Verify that client seamlessly falls back to Chat Completions when Responses API fails."""
    mock_openai = MagicMock()
    # Responses API fails with NotImplementedError or BadRequestError
    mock_openai.responses.create.side_effect = NotImplementedError("Responses API not available")
    mock_openai.chat.completions.create.return_value = create_mock_chat_completion_response(
        json.dumps({"technique_id": "T1078.003"}),
        input_tokens=1100,
        output_tokens=2200,
    )

    client = LLMClient(openai_client=mock_openai)
    record = client.predict(
        sample_id="sample_fallback",
        endpoint_evidence="net user /add attacker Pass123",
    )

    assert record.parse_status == ParseStatus.VALID.value
    assert record.predicted_technique_id == "T1078.003"
    assert record.input_tokens == 1100
    assert record.output_tokens == 2200
    mock_openai.responses.create.assert_called_once()
    mock_openai.chat.completions.create.assert_called_once()


# ---------------------------------------------------------------------------
# 5. Parse Status Testing: All 7 Distinct Statuses
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
# 6. Retries and Exponential Backoff
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
# 7. Total Wall-Clock Latency Semantics
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
# 8. Global Live Request Budget Enforcement (Max 5 Requests)
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
