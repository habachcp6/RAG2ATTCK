"""
RAG2ATTCK - RAG Pipeline with Controlled-Comparison Invariant (Task T19)
Implements deterministic retrieval-augmented generation for ATT&CK threat attribution:
- Enforces controlled comparison: identical prompt template, model, reasoning effort, and schemas.
- Injects formatted ATT&CK candidates strictly into {RETRIEVED_CONTEXT}.
- Enforces pipeline-level input-field isolation: query retriever and prompt using ONLY endpoint_evidence.
- Preserves No-RAG isolation: baseline condition="no_rag" remains structurally incapable of consuming context.
- Wraps execution and retrieval metadata via composition without mutating baseline schemas.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Union

from src.llm.client import LLMClient
from src.llm.inputs import validate_benchmark_batch
from src.llm.schemas import ExecutionRecord, get_workspace_root, validate_condition
from src.rag.schemas import RAGExecutionRecord, RetrievalMetadata
from src.retrieval.retriever import Embedder, FAISSRetriever, RetrievalResult

SUPPORTED_K = frozenset({1, 3, 5, 10})


def format_rag_prompt(
    endpoint_evidence: str,
    retrieved_context: Optional[str] = None,
    prompt_template: Optional[str] = None,
    prompt_path: Optional[Path | str] = None,
) -> str:
    """
    Constructs the prompt by substituting {ENDPOINT_EVIDENCE} and {RETRIEVED_CONTEXT}.
    Byte-symmetrically matches format_baseline_prompt when retrieved_context is identical.
    """
    if prompt_template is None:
        ws = get_workspace_root()
        p_path = Path(prompt_path) if prompt_path else (ws / "prompts" / "baseline_v1.txt")
        if not p_path.exists():
            raise FileNotFoundError(f"Prompt template not found at {p_path}")
        prompt_template = p_path.read_text(encoding="utf-8")

    ctx_str = retrieved_context if retrieved_context is not None else ""
    return (
        prompt_template
        .replace("{RETRIEVED_CONTEXT}", ctx_str)
        .replace("{ENDPOINT_EVIDENCE}", endpoint_evidence)
    )


class RAGPipeline:
    """
    Orchestrates end-to-end RAG telemetry evaluation with controlled-comparison invariants.
    """

    def __init__(
        self,
        retriever: Optional[FAISSRetriever] = None,
        client: Optional[LLMClient] = None,
        prompt_path: Optional[Path | str] = None,
        prompt_version: str = "baseline_v1",
        default_k: int = 5,
        retrieval_config_path: Optional[Path | str] = None,
        embedder: Optional[Embedder] = None,
        prompt_template: str | None = None,
    ) -> None:
        if default_k not in SUPPORTED_K:
            raise ValueError(
                f"Unsupported default_k={default_k}. Supported values: {sorted(SUPPORTED_K)}"
            )

        self.ws_root = get_workspace_root()
        self.default_k = default_k
        self.prompt_version = prompt_version

        # Initialize or inject FAISSRetriever
        if retriever is not None:
            self.retriever = retriever
        else:
            cfg_path = retrieval_config_path or (self.ws_root / "config" / "retrieval.json")
            self.retriever = FAISSRetriever.from_saved(config_path=cfg_path, embedder=embedder)

        # Initialize or inject LLMClient
        self.client = client or LLMClient()

        if prompt_template is not None:
            self.prompt_template = prompt_template
            return

        # Load frozen prompt template
        p_path = Path(prompt_path) if prompt_path else (self.ws_root / "prompts" / f"{prompt_version}.txt")
        if not p_path.exists():
            raise FileNotFoundError(f"Prompt template not found at {p_path}")
        self.prompt_template = p_path.read_text(encoding="utf-8")

    def format_prompt(
        self,
        endpoint_evidence: str,
        retrieved_context: Optional[str] = None,
    ) -> str:
        """Format prompt using this pipeline's loaded prompt template."""
        return format_rag_prompt(
            endpoint_evidence=endpoint_evidence,
            retrieved_context=retrieved_context,
            prompt_template=self.prompt_template,
        )

    def run_sample(
        self,
        sample_id: str,
        endpoint_evidence: str,
        k: Optional[int] = None,
    ) -> RAGExecutionRecord:
        """
        Executes RAG prediction for a single telemetry sample.

        Steps:
        1. Validates retrieval depth k in SUPPORTED_K {1, 3, 5, 10}.
        2. Retrieves top-k candidates using ONLY endpoint_evidence as query.
        3. Deterministically formats retrieved context string.
        4. Validates RetrievalMetadata provenance before model dispatch.
        5. Dispatches prediction via LLMClient with condition='rag'.
        6. Returns composite RAGExecutionRecord.
        """
        [(sample_id, endpoint_evidence)] = validate_benchmark_batch([
            {"sample_id": sample_id, "endpoint_evidence": endpoint_evidence}
        ])
        retrieval_k = k if k is not None else self.default_k
        if retrieval_k not in SUPPORTED_K:
            raise ValueError(
                f"Unsupported retrieval depth k={retrieval_k}. Supported values: {sorted(SUPPORTED_K)}"
            )

        # 1. Retrieve candidates using ONLY endpoint_evidence
        results: List[RetrievalResult] = self.retriever.retrieve(
            query=endpoint_evidence,
            k=retrieval_k,
        )

        # 2. Format retrieved context using retriever helper
        retrieved_context_str = self.retriever.format_retrieved_context(results)

        # Validate provenance before any model request can be dispatched.
        cfg = getattr(self.retriever, "config", {}) or {}
        retrieval_meta = RetrievalMetadata(
            k=retrieval_k,
            technique_ids=[r.technique_id for r in results],
            ranks=[r.rank for r in results],
            scores=[r.score for r in results],
            corpus_sha256=cfg.get("corpus_sha256"),
            embedding_model_id=cfg.get("embedding_model_id"),
            embedding_model_revision=cfg.get("embedding_model_revision"),
            index_sha256=cfg.get("index_sha256"),
        )

        exec_record: ExecutionRecord = self.client.predict(
            sample_id=sample_id,
            endpoint_evidence=endpoint_evidence,
            retrieved_context=retrieved_context_str,
            condition="rag",
            prompt_template=self.prompt_template,
            prompt_version=self.prompt_version,
        )

        # 5. Return composition wrapper
        return RAGExecutionRecord(
            execution=exec_record,
            retrieval=retrieval_meta,
        )

    def run_batch(
        self,
        samples: Iterable[Dict[str, Any]],
        k: Optional[int] = None,
    ) -> List[RAGExecutionRecord]:
        """
        Executes RAG predictions sequentially across an iterable of sample dicts.

        Pipeline-level input-field isolation:
        Extracts ONLY sample_id and endpoint_evidence.
        Any evaluation metadata, labels (e.g. ground_truth, technique_label,
        attack_label, expected_technique), or extraneous dictionary keys are discarded.
        """
        records: List[RAGExecutionRecord] = []
        for s_id, evidence in validate_benchmark_batch(samples):
            rec = self.run_sample(
                sample_id=s_id,
                endpoint_evidence=evidence,
                k=k,
            )
            records.append(rec)
        return records
