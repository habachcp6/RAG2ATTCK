"""Request budget checks use mocks/transports; never call the OpenAI service."""

from unittest.mock import MagicMock

import httpx
import openai
import pytest

from src.llm.client import GLOBAL_LIVE_BUDGET, LLMClient, LiveBudget
from tests.test_llm_client import create_mock_responses_api_response


def client_with_budget(budget=None, live=True):
    mock = MagicMock()
    mock.responses.create.return_value = create_mock_responses_api_response('{"technique_id":"T1059.001"}')
    return LLMClient(openai_client=mock, live_budget=budget, is_live=live,
                     registry_ids={"T1059.001"}, sleep_fn=lambda _: None)


def test_default_smoke_budget_is_shared_and_bounded():
    GLOBAL_LIVE_BUDGET.reset()
    try:
        clients = [client_with_budget(), client_with_budget()]
        assert all(c.live_budget is GLOBAL_LIVE_BUDGET for c in clients)
        for i in range(6):
            record = clients[i % 2].predict(str(i), "log")
        assert GLOBAL_LIVE_BUDGET.count == 5
        assert sum(c.client.responses.create.call_count for c in clients) == 5
        assert record.error_type == "LiveBudgetExceededError"
    finally:
        GLOBAL_LIVE_BUDGET.reset()


def test_explicit_experiment_budget_shared_across_conditions():
    budget = LiveBudget(max_requests=8)
    baseline, rag = client_with_budget(budget), client_with_budget(budget)
    for i in range(8):
        client = baseline if i % 2 == 0 else rag
        record = client.predict(str(i), "log", condition="no_rag" if i % 2 == 0 else "rag")
        assert record.is_valid
    record = rag.predict("exhausted", "log", condition="rag")
    assert record.error_type == "LiveBudgetExceededError"
    assert "limit of 8" in record.invalid_reason
    assert budget.count == 8
    assert baseline.client.responses.create.call_count + rag.client.responses.create.call_count == 8


@pytest.mark.parametrize("cap", [-1, 1.5, float("inf"), None, True, "10"])
def test_invalid_budget_cannot_be_unlimited(cap):
    with pytest.raises(ValueError, match="max_requests"):
        LiveBudget(cap)


def test_mock_mode_uses_zero_budget_even_with_retries():
    budget = LiveBudget(0)
    client = client_with_budget(budget, live=False)
    client.client.responses.create.side_effect = [TimeoutError(), create_mock_responses_api_response('{"technique_id":"T1059.001"}')]
    assert client.predict("s1", "log").is_valid
    assert client.client.responses.create.call_count == 2
    assert budget.count == 0


def test_parse_failure_does_not_retry_or_consume_extra_budget():
    budget = LiveBudget(5)
    client = client_with_budget(budget)
    client.client.responses.create.return_value = create_mock_responses_api_response("not JSON")
    assert client.predict("s1", "log").parse_status == "MALFORMED_RESPONSE"
    assert budget.count == client.client.responses.create.call_count == 1


def test_sdk_retries_are_budgeted_via_outer_loop(monkeypatch):
    # Exercise the actual SDK over an in-memory HTTP transport returning 503.
    calls = []
    real_openai = openai.OpenAI
    def respond(request):
        calls.append(request)
        return httpx.Response(503, json={"error": {"message": "unavailable"}})
    def factory(**kwargs):
        assert kwargs["max_retries"] == 0
        return real_openai(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(respond)))
    monkeypatch.setattr("src.llm.client.openai.OpenAI", factory)
    budget = LiveBudget(2)
    client = LLMClient(api_key="test-only", live_budget=budget, sleep_fn=lambda _: None)
    try:
        record = client.predict("s1", "log")
        assert record.error_type == "LiveBudgetExceededError"
        assert len(calls) == budget.count == 2
    finally:
        client.client.close()


def test_real_client_cannot_disable_accounting():
    with pytest.raises(ValueError, match="cannot disable"):
        LLMClient(api_key="test-only", is_live=False)
