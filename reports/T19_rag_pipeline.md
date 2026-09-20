# Task T19: RAG Pipeline with Controlled-Comparison Invariant

## Overview
This report summarizes the implementation and testing of the RAG Pipeline (`src/rag/pipeline.py`), which enforces deterministic retrieval-augmented generation and strict controlled comparisons between RAG and No-RAG conditions.

## Key Design Invariants

1. **Controlled Treatment Design**: RAG and No-RAG conditions use exactly the same language model, prompt template, reasoning effort, and output schema.
2. **Prompt Symmetry**: `format_rag_prompt` produces byte-identical output to `format_baseline_prompt` for identical `endpoint_evidence` and `retrieved_context`.
3. **No-RAG Isolation**: The baseline pipeline explicitly validates that `condition="no_rag"` cannot contain a non-empty `retrieved_context`. This structural isolation remains strictly enforced.
4. **Input-Field Isolation Scope**: The `RAGPipeline.run_batch` method extracts *only* the `sample_id` and `endpoint_evidence`. All other keys (like `ground_truth`, `technique_label`, `expected_technique`, `attack_label`) are strictly discarded to avoid data leakage to the retriever or LLM prompt. (Note: T19 proves this isolation; T09/T10 handles the full leakage audit).
5. **Composition Schema**: RAG output schemas do not mutate the baseline `ExecutionRecord`. Instead, `RAGExecutionRecord` wraps `ExecutionRecord` and `RetrievalMetadata` via composition.
6. **Retrieval Context Formatting**: The retrieved context is formatted deterministically without external labels, injected solely via the `{RETRIEVED_CONTEXT}` placeholder.

## Supported Parameterization
Retrieval limits (`k`) are strictly constrained to `{1, 3, 5, 10}` to maintain experiment consistency and avoid exhaustive combinatorial sweeps.

## Provenance Fields
The `RetrievalMetadata` securely tracks the provenance of information provided in the prompt:
- `k`
- `technique_ids`
- `ranks`
- `scores`
- `corpus_sha256`
- `embedding_model_id`
- `embedding_model_revision`
- `index_sha256`

## Status and Next Steps
- T20 retrieval diagnostics completed.
- End-to-end live evaluation remains pending.
- T15 real-data pilot remains blocked by approved real telemetry availability.

