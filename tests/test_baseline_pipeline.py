"""
Unit tests for Baseline Pipeline helper (Milestone M2, src/baseline/pipeline.py).

Verifies:
1. format_baseline_prompt substitution for No-RAG ({RETRIEVED_CONTEXT} -> empty string).
2. format_baseline_prompt substitution for RAG condition ({RETRIEVED_CONTEXT} populated).
3. BaselinePipeline.run_sample end-to-end execution with mock LLM client.
4. BaselinePipeline.run_batch execution over a sequence of telemetry cases.
5. Verification of condition metadata and prediction validity.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from src.baseline.pipeline import BaselinePipeline, format_baseline_prompt
from src.llm.client import LLMClient
from src.llm.schemas import ParseStatus
from tests.test_llm_client import create_mock_responses_api_response


def test_format_baseline_prompt_no_rag():
    """Verify No-RAG prompt formatting replaces RETRIEVED_CONTEXT with empty string."""
    evidence = "EventID 1: Image: C:\\Windows\\System32\\cmd.exe CommandLine: whoami /all"
    prompt = format_baseline_prompt(endpoint_evidence=evidence, retrieved_context=None)

    assert evidence in prompt
    assert "{ENDPOINT_EVIDENCE}" not in prompt
    assert "{RETRIEVED_CONTEXT}" not in prompt


def test_format_baseline_prompt_rag():
    """Verify RAG prompt formatting populates RETRIEVED_CONTEXT placeholder."""
    evidence = "EventID 1: Image: powershell.exe"
    context = "Technique: T1059.001 PowerShell"
    prompt = format_baseline_prompt(endpoint_evidence=evidence, retrieved_context=context)

    assert evidence in prompt
    assert context in prompt
    assert "{ENDPOINT_EVIDENCE}" not in prompt
    assert "{RETRIEVED_CONTEXT}" not in prompt


def test_baseline_pipeline_run_sample_mocked():
    """Verify BaselinePipeline.run_sample executes prediction with condition='no_rag'."""
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({"technique_id": "T1059.001"}),
        input_tokens=800,
        output_tokens=1500,
    )

    client = LLMClient(openai_client=mock_openai)
    pipeline = BaselinePipeline(client=client)

    rec = pipeline.run_sample(
        sample_id="test_sample_101",
        endpoint_evidence="powershell.exe -enc aW52b2tl",
    )

    assert rec.sample_id == "test_sample_101"
    assert rec.condition == "no_rag"
    assert rec.parse_status == ParseStatus.VALID.value
    assert rec.predicted_technique_id == "T1059.001"
    assert rec.input_tokens == 800
    assert rec.output_tokens == 1500


def test_baseline_pipeline_run_batch():
    """Verify BaselinePipeline.run_batch executes across multiple samples."""
    mock_openai = MagicMock()
    mock_openai.responses.create.side_effect = [
        create_mock_responses_api_response(json.dumps({"technique_id": "T1059.001"})),
        create_mock_responses_api_response(json.dumps({"technique_id": "T1078.003"})),
    ]

    client = LLMClient(openai_client=mock_openai)
    pipeline = BaselinePipeline(client=client)

    samples = [
        {"sample_id": "s1", "endpoint_evidence": "powershell.exe"},
        {"sample_id": "s2", "endpoint_evidence": "net user admin"},
    ]

    records = pipeline.run_batch(samples)
    assert len(records) == 2
    assert records[0].sample_id == "s1"
    assert records[0].predicted_technique_id == "T1059.001"
    assert records[0].is_valid is True
    assert records[1].sample_id == "s2"
    assert records[1].predicted_technique_id == "T1078.003"
    assert records[1].is_valid is True


def test_baseline_pipeline_default_instantiation(monkeypatch):
    """Verify default constructor BaselinePipeline() succeeds without NameError."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    pipeline = BaselinePipeline()
    assert isinstance(pipeline.client, LLMClient)
    assert pipeline.prompt_version == "baseline_v1"
    assert "{ENDPOINT_EVIDENCE}" in pipeline.prompt_template
    assert "{RETRIEVED_CONTEXT}" in pipeline.prompt_template
