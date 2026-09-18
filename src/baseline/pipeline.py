"""
RAG2ATTCK - Baseline Pipeline Helper (Milestone M2)
Provides end-to-end baseline execution orchestration:
- Loads prompts/baseline_v1.txt
- Formats prompt placeholders {ENDPOINT_EVIDENCE} and {RETRIEVED_CONTEXT} ("" for No-RAG)
- Executes client predictions and returns structured execution records
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.llm.client import LLMClient
from src.llm.schemas import ExecutionRecord, get_workspace_root, validate_condition


def format_baseline_prompt(
    endpoint_evidence: str,
    retrieved_context: Optional[str] = None,
    prompt_template: Optional[str] = None,
    prompt_path: Optional[Path | str] = None,
) -> str:
    """
    Constructs the prompt by substituting {ENDPOINT_EVIDENCE} and {RETRIEVED_CONTEXT}.
    For No-RAG condition, retrieved_context is substituted with an empty string ("").
    """
    if prompt_template is None:
        ws = get_workspace_root()
        p_path = Path(prompt_path) if prompt_path else (ws / "prompts" / "baseline_v1.txt")
        if not p_path.exists():
            raise FileNotFoundError(f"Baseline prompt template not found at {p_path}")
        prompt_template = p_path.read_text(encoding="utf-8")

    ctx_str = retrieved_context if retrieved_context is not None else ""
    return (
        prompt_template
        .replace("{RETRIEVED_CONTEXT}", ctx_str)
        .replace("{ENDPOINT_EVIDENCE}", endpoint_evidence)
    )


class BaselinePipeline:
    """
    Orchestrates end-to-end baseline (No-RAG) telemetry evaluation.
    """

    def __init__(
        self,
        client: Optional[LLMClient] = None,
        prompt_path: Optional[Path | str] = None,
        prompt_version: str = "baseline_v1",
    ) -> None:
        self.ws_root = get_workspace_root()
        self.client = client or LLMClient()
        self.prompt_version = prompt_version

        p_path = Path(prompt_path) if prompt_path else (self.ws_root / "prompts" / f"{prompt_version}.txt")
        if not p_path.exists():
            raise FileNotFoundError(f"Base prompt not found at {p_path}")
        self.prompt_template = p_path.read_text(encoding="utf-8")

    def run_sample(
        self,
        sample_id: str,
        endpoint_evidence: str,
        retrieved_context: Optional[str] = None,
        condition: str = "no_rag",
    ) -> ExecutionRecord:
        """
        Executes baseline prediction for a single telemetry sample.

        Raises:
            ValueError: If condition is "no_rag" but retrieved_context is non-empty.
        """
        # Runtime condition enum validation
        validate_condition(condition)

        # No-RAG context isolation invariant (enforced at pipeline level too)
        if condition == "no_rag" and retrieved_context is not None and retrieved_context.strip():
            raise ValueError(
                "Research integrity violation: condition='no_rag' but non-empty "
                "retrieved_context was supplied to BaselinePipeline.run_sample(). "
                "No-RAG must be structurally incapable of receiving ATT&CK retrieval context."
            )
        return self.client.predict(
            sample_id=sample_id,
            endpoint_evidence=endpoint_evidence,
            retrieved_context=retrieved_context,
            condition=condition,
            prompt_template=self.prompt_template,
            prompt_version=self.prompt_version,
        )

    def run_batch(
        self,
        samples: Iterable[Dict[str, Any]],
        condition: str = "no_rag",
    ) -> List[ExecutionRecord]:
        """
        Executes baseline predictions sequentially across an iterable of samples.
        Each sample dict must provide 'sample_id' and 'endpoint_evidence' (or 'evidence').
        """
        records: List[ExecutionRecord] = []
        for sample in samples:
            s_id = sample.get("sample_id") or sample.get("id", "unknown_sample")
            evidence = sample.get("endpoint_evidence") or sample.get("evidence", "")
            retrieved = sample.get("retrieved_context")
            record = self.run_sample(
                sample_id=str(s_id),
                endpoint_evidence=str(evidence),
                retrieved_context=retrieved,
                condition=condition,
            )
            records.append(record)
        return records
