"""
RAG2ATTCK - RAG Pipeline Schemas and Provenance Metadata (Task T19)
Defines Pydantic V2 schemas for retrieval metadata and the RAG composition record.
Preserves baseline ExecutionRecord without mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List
from pydantic import BaseModel, ConfigDict

from src.llm.schemas import ExecutionRecord


class RetrievalMetadata(BaseModel):
    """
    Retrieval provenance tracking the exact ATT&CK candidates injected into the prompt,
    along with index and embedding model hashes.
    """

    k: int
    technique_ids: List[str]
    ranks: List[int]
    scores: List[float]
    corpus_sha256: str
    embedding_model_id: str
    embedding_model_revision: str
    index_sha256: str

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize retrieval metadata to dictionary."""
        return self.model_dump()


class RAGExecutionRecord(BaseModel):
    """
    Composition wrapper holding the baseline ExecutionRecord and RAG RetrievalMetadata.
    Preserves backward compatibility with ExecutionRecord while adding retrieval provenance.
    """

    execution: ExecutionRecord
    retrieval: RetrievalMetadata

    model_config = ConfigDict(
        extra="forbid",
        frozen=False,
    )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Serialize record to JSON string."""
        return self.model_dump_json()
