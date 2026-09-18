"""
RAG2ATTCK - RAG Pipeline Schemas and Provenance Metadata (Task T19)
Defines Pydantic V2 schemas for retrieval metadata and the RAG composition record.
Preserves baseline ExecutionRecord without mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List
import math
import re
from pydantic import BaseModel, ConfigDict, model_validator

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
        strict=True,
    )

    @model_validator(mode="after")
    def validate_provenance(self) -> "RetrievalMetadata":
        if self.k not in {1, 3, 5, 10}:
            raise ValueError("k must be one of 1, 3, 5, 10")
        if not (len(self.technique_ids) == len(self.ranks) == len(self.scores) == self.k):
            raise ValueError("technique_ids, ranks and scores lengths must equal k")
        if self.ranks != list(range(1, self.k + 1)):
            raise ValueError("ranks must be exactly [1, ..., k]")
        if any(re.fullmatch(r"T\d{4}(?:\.\d{3})?", tid, flags=re.ASCII) is None for tid in self.technique_ids):
            raise ValueError("technique_ids must use canonical ATT&CK technique ID syntax")
        if any(not math.isfinite(score) for score in self.scores):
            raise ValueError("scores must all be finite")
        for field in ("corpus_sha256", "index_sha256"):
            if re.fullmatch(r"[0-9a-fA-F]{64}", getattr(self, field)) is None:
                raise ValueError(f"{field} must be a 64-character hexadecimal SHA-256")
        if not self.embedding_model_id.strip():
            raise ValueError("embedding_model_id must be non-empty")
        if re.fullmatch(r"[0-9a-fA-F]{40}", self.embedding_model_revision) is None:
            raise ValueError("embedding_model_revision must be an exact 40-character hexadecimal commit")
        return self

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
