"""Batch validation must finish before any retrieval or model request."""

from unittest.mock import MagicMock

import pytest

from src.baseline.pipeline import BaselinePipeline
from src.rag.pipeline import RAGPipeline


@pytest.fixture(params=[BaselinePipeline, RAGPipeline])
def pipeline(request):
    client = MagicMock()
    if request.param is RAGPipeline:
        return RAGPipeline(client=client, retriever=MagicMock())
    return BaselinePipeline(client=client)


@pytest.mark.parametrize("bad,field", [
    ({"endpoint_evidence": "log"}, "sample_id"),
    ({"sample_id": " " , "endpoint_evidence": "log"}, "sample_id"),
    ({"sample_id": 123, "endpoint_evidence": "log"}, "sample_id"),
    ({"sample_id": None, "id": "fallback", "endpoint_evidence": "log"}, "sample_id"),
    ({"sample_id": "second"}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": ""}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": " \n\t"}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": "\x00\u200b"}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": {"ground_truth": "T1234"}}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": ["log"]}, "endpoint_evidence"),
    ({"sample_id": "second", "endpoint_evidence": None, "evidence": "fallback"}, "endpoint_evidence"),
    (None, "mapping"),
])
def test_invalid_late_sample_prevents_all_dispatch(pipeline, bad, field):
    batch = iter([{"sample_id": "first", "endpoint_evidence": "log"}, bad])
    with pytest.raises(ValueError, match=f"index 1.*{field}"):
        pipeline.run_batch(batch)
    pipeline.client.predict.assert_not_called()
    if isinstance(pipeline, RAGPipeline):
        pipeline.retriever.retrieve.assert_not_called()


def test_duplicate_normalized_id_prevents_all_dispatch(pipeline):
    with pytest.raises(ValueError, match="Duplicate sample_id 'same' at batch index 1"):
        pipeline.run_batch([
            {"sample_id": "same", "endpoint_evidence": "a"},
            {"id": " same ", "evidence": "b"},
        ])
    pipeline.client.predict.assert_not_called()
    if isinstance(pipeline, RAGPipeline):
        pipeline.retriever.retrieve.assert_not_called()


def test_whitelist_aliases_and_unchanged_evidence(pipeline):
    pipeline.run_sample = MagicMock()
    evidence = "  Process: cmd.exe\n"
    pipeline.run_batch([{"id": " s1 ", "evidence": evidence, "ground_truth": "SECRET_LABEL"}])
    kwargs = pipeline.run_sample.call_args.kwargs
    assert kwargs["sample_id"] == "s1"
    assert kwargs["endpoint_evidence"] == evidence
    assert "SECRET_LABEL" not in repr(kwargs)


@pytest.mark.parametrize("sample_id,evidence", [("", "log"), ("s1", " "), ("s1", {"ground_truth": "T1234"})])
def test_direct_sample_cannot_bypass_validation(pipeline, sample_id, evidence):
    with pytest.raises(ValueError, match="Invalid benchmark sample"):
        pipeline.run_sample(sample_id, evidence)
    pipeline.client.predict.assert_not_called()
    if isinstance(pipeline, RAGPipeline):
        pipeline.retriever.retrieve.assert_not_called()
