"""
Unit tests for RAG Pipeline (Task T19, src/rag/pipeline.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from src.baseline.pipeline import format_baseline_prompt, BaselinePipeline
from src.llm.client import LLMClient
from src.llm.schemas import ExecutionRecord, get_workspace_root
from src.rag.pipeline import RAGPipeline, format_rag_prompt, SUPPORTED_K
from src.rag.schemas import RAGExecutionRecord, RetrievalMetadata
from src.retrieval.retriever import RetrievalResult
from tests.test_llm_client import create_mock_responses_api_response


# Test 1: format_rag_prompt with no context (matches baseline behavior)
def test_format_rag_prompt_no_context():
    evidence = "EventID 1: Image: cmd.exe"
    prompt = format_rag_prompt(endpoint_evidence=evidence, retrieved_context=None)
    assert evidence in prompt
    assert "{ENDPOINT_EVIDENCE}" not in prompt
    assert "{RETRIEVED_CONTEXT}" not in prompt

# Test 2: format_rag_prompt with context
def test_format_rag_prompt_with_context():
    evidence = "EventID 1: Image: powershell.exe"
    context = "Candidate 1: [T1059.001]"
    prompt = format_rag_prompt(endpoint_evidence=evidence, retrieved_context=context)
    assert evidence in prompt
    assert context in prompt
    assert "{ENDPOINT_EVIDENCE}" not in prompt
    assert "{RETRIEVED_CONTEXT}" not in prompt

# Test 3: Prompt symmetry - No-RAG and RAG produce identical prompts except RETRIEVED_CONTEXT content
def test_prompt_symmetry_rag_vs_baseline():
    evidence = "Common Evidence"
    context = "Common Context"
    
    rag_prompt = format_rag_prompt(endpoint_evidence=evidence, retrieved_context=context)
    base_prompt = format_baseline_prompt(endpoint_evidence=evidence, retrieved_context=context)
    
    assert rag_prompt == base_prompt
    
    rag_prompt_none = format_rag_prompt(endpoint_evidence=evidence, retrieved_context=None)
    base_prompt_none = format_baseline_prompt(endpoint_evidence=evidence, retrieved_context=None)
    
    assert rag_prompt_none == base_prompt_none

# Mock fixture helpers
def _create_mock_retriever():
    mock_retriever = MagicMock()
    mock_retriever.config = {
        'corpus_sha256': 'abc123',
        'embedding_model_id': 'sentence-transformers/all-MiniLM-L6-v2',
        'embedding_model_revision': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        'index_sha256': 'def456',
    }
    mock_retriever.retrieve.return_value = [
        RetrievalResult(technique_id='T1059.001', score=0.95, document={'name': 'PowerShell', 'technique_id': 'T1059.001', 'retrieval_text': 'PowerShell technique'}, rank=1),
    ]
    mock_retriever.format_retrieved_context.return_value = 'Candidate 1: [T1059.001] PowerShell (Similarity Score: 0.9500)\nPowerShell technique'
    return mock_retriever

def _create_mock_client():
    mock_openai = MagicMock()
    mock_openai.responses.create.return_value = create_mock_responses_api_response(
        json.dumps({'technique_id': 'T1059.001'}),
        input_tokens=800,
        output_tokens=1500,
    )
    return LLMClient(openai_client=mock_openai)

# Test 4: RAGPipeline.run_sample mocked end-to-end
def test_rag_pipeline_run_sample_mocked():
    mock_retriever = _create_mock_retriever()
    client = _create_mock_client()
    ws_root = get_workspace_root()
    
    pipeline = RAGPipeline(
        retriever=mock_retriever,
        client=client,
        prompt_path=ws_root / "prompts" / "baseline_v1.txt",
    )
    
    rec = pipeline.run_sample(
        sample_id="test_rag_1",
        endpoint_evidence="powershell log",
    )
    
    assert isinstance(rec, RAGExecutionRecord)
    assert isinstance(rec.execution, ExecutionRecord)
    assert isinstance(rec.retrieval, RetrievalMetadata)
    
    assert rec.execution.sample_id == "test_rag_1"
    assert rec.execution.condition == "rag"
    assert rec.execution.predicted_technique_id == "T1059.001"
    
    assert rec.retrieval.k == 5
    assert rec.retrieval.technique_ids == ["T1059.001"]
    assert rec.retrieval.ranks == [1]
    assert rec.retrieval.scores == [0.95]
    assert rec.retrieval.corpus_sha256 == "abc123"

# Test 5: RAGPipeline.run_batch with input-field isolation
def test_rag_pipeline_run_batch_isolates_input_fields():
    mock_retriever = _create_mock_retriever()
    client = _create_mock_client()
    ws_root = get_workspace_root()
    
    pipeline = RAGPipeline(
        retriever=mock_retriever,
        client=client,
        prompt_path=ws_root / "prompts" / "baseline_v1.txt",
    )
    
    samples = [
        {
            "sample_id": "s1",
            "endpoint_evidence": "some log",
            "ground_truth": "T1059.001",
            "technique_label": "T1059.001",
            "expected_technique": "T1059.001",
            "attack_label": "T1059.001",
            "extra_key": "should_be_ignored"
        }
    ]
    
    records = pipeline.run_batch(samples)
    
    assert len(records) == 1
    mock_retriever.retrieve.assert_called_once_with(query="some log", k=5)
    
    # We intercept the prompt sent to openai to verify leak fields are missing in test 11.

# Test 6: No-RAG isolation invariant still holds
def test_norag_isolation_still_enforced():
    client = _create_mock_client()
    pipeline = BaselinePipeline(client=client)
    
    with pytest.raises(ValueError, match="Research integrity violation"):
        pipeline.run_sample(
            sample_id="test_iso",
            endpoint_evidence="evidence",
            condition="no_rag",
            retrieved_context="some context"
        )

# Test 7: RAGPipeline validates k values
def test_rag_pipeline_rejects_unsupported_k():
    mock_retriever = _create_mock_retriever()
    client = _create_mock_client()
    ws_root = get_workspace_root()
    
    # Invalid default_k
    with pytest.raises(ValueError, match="Unsupported default_k"):
        RAGPipeline(
            retriever=mock_retriever,
            client=client,
            prompt_path=ws_root / "prompts" / "baseline_v1.txt",
            default_k=7
        )
        
    pipeline = RAGPipeline(
        retriever=mock_retriever,
        client=client,
        prompt_path=ws_root / "prompts" / "baseline_v1.txt",
    )
    
    # Invalid k during run_sample
    with pytest.raises(ValueError, match="Unsupported retrieval depth"):
        pipeline.run_sample(sample_id="s1", endpoint_evidence="ev", k=2)

# Test 8: RetrievalMetadata schema validation
def test_retrieval_metadata_schema():
    meta = RetrievalMetadata(
        k=3,
        technique_ids=["T1059.001", "T1059", "T1059.003"],
        ranks=[1, 2, 3],
        scores=[0.9, 0.8, 0.7],
        corpus_sha256='c_sha',
        embedding_model_id='model',
        embedding_model_revision='rev',
        index_sha256='i_sha'
    )
    d = meta.to_dict()
    assert d['k'] == 3
    assert d['technique_ids'] == ["T1059.001", "T1059", "T1059.003"]
    assert d['index_sha256'] == 'i_sha'

# Test 9: RAGExecutionRecord composition
def test_rag_execution_record_composition():
    client = _create_mock_client()
    pipeline = BaselinePipeline(client=client)
    exec_rec = pipeline.run_sample(sample_id="s1", endpoint_evidence="ev")
    
    meta = RetrievalMetadata(
        k=1, technique_ids=["T1059.001"], ranks=[1], scores=[0.9],
        corpus_sha256='a', embedding_model_id='b', embedding_model_revision='c', index_sha256='d'
    )
    
    rag_rec = RAGExecutionRecord(execution=exec_rec, retrieval=meta)
    
    assert rag_rec.execution is exec_rec
    assert rag_rec.retrieval is meta
    assert isinstance(rag_rec.to_dict(), dict)
    assert isinstance(rag_rec.to_json(), str)

# Test 10: Supported k values
def test_supported_k_values():
    assert SUPPORTED_K == {1, 3, 5, 10}

# Test 11: Ground truth fields never reach prompt
def test_ground_truth_never_in_prompt():
    mock_retriever = _create_mock_retriever()
    client = _create_mock_client()
    ws_root = get_workspace_root()
    
    pipeline = RAGPipeline(
        retriever=mock_retriever,
        client=client,
        prompt_path=ws_root / "prompts" / "baseline_v1.txt",
    )
    
    # Intercept client.predict to check arguments
    prompt_captured = []
    original_predict = pipeline.client.predict
    
    def mock_predict(*args, **kwargs):
        prompt_captured.append(kwargs)
        return original_predict(*args, **kwargs)
        
    pipeline.client.predict = mock_predict
    
    sample = {
        "sample_id": "s_leak",
        "endpoint_evidence": "legitimate evidence",
        "ground_truth": "T1234",
        "technique_label": "T1234",
        "expected_technique": "T1234",
        "attack_label": "T1234",
    }
    
    pipeline.run_batch([sample])
    
    assert len(prompt_captured) == 1
    called_kwargs = prompt_captured[0]
    
    # The prompt actually generated internally
    final_prompt = pipeline.format_prompt(
        endpoint_evidence=called_kwargs.get("endpoint_evidence"),
        retrieved_context=called_kwargs.get("retrieved_context")
    )
    
    # These strings should never be found in the prompt
    assert "T1234" not in final_prompt
    assert "ground_truth" not in final_prompt
    assert "technique_label" not in final_prompt
