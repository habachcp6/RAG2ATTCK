"""Reject inconsistent provenance before model dispatch or serialization."""

from unittest.mock import MagicMock

import pytest

from src.rag.pipeline import RAGPipeline
from src.rag.schemas import RetrievalMetadata
from tests.test_rag_pipeline import _create_mock_retriever


@pytest.fixture
def metadata():
    return dict(k=3, technique_ids=["T1059", "T1059.001", "T1053.005"],
                ranks=[1, 2, 3], scores=[0.9, 0.8, 0.7], corpus_sha256="a" * 64,
                index_sha256="b" * 64, embedding_model_id="pinned-model",
                embedding_model_revision="c" * 40)


@pytest.mark.parametrize("field,value", [
    ("technique_ids", ["T1059"]), ("ranks", [1]), ("scores", [0.1]),
    ("ranks", [0, 1, 2]), ("ranks", [1, 1, 3]), ("ranks", [3, 2, 1]),
    ("technique_ids", ["T1059", "garbage", "T1053.005"]),
    ("technique_ids", ["T1059", "T1059.01", "T1053.005"]),
    ("technique_ids", ["T1059", "T１２３４", "T1053.005"]),
    ("corpus_sha256", "abc"), ("index_sha256", "z" * 64),
    ("embedding_model_id", " "), ("embedding_model_revision", "main"),
    ("scores", [float("nan"), 0.8, 0.7]),
    ("scores", [float("inf"), 0.8, 0.7]),
    ("scores", [float("-inf"), 0.8, 0.7]),
    ("k", 2), ("k", "3"), ("ranks", [True, 2, 3]),
])
def test_invalid_provenance_rejected(metadata, field, value):
    metadata[field] = value
    with pytest.raises(ValueError):
        RetrievalMetadata(**metadata)


def test_valid_provenance_roundtrip(metadata):
    meta = RetrievalMetadata(**metadata)
    assert RetrievalMetadata.model_validate_json(meta.model_dump_json()) == meta


def test_invalid_provenance_prevents_model_call():
    retriever = _create_mock_retriever()
    retriever.config["index_sha256"] = "invalid"
    client = MagicMock()
    pipeline = RAGPipeline(retriever=retriever, client=client)
    with pytest.raises(ValueError, match="index_sha256"):
        pipeline.run_sample("s1", "powershell.exe")
    client.predict.assert_not_called()
