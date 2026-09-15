# RAG2ATT&CK — Data & Ground Truth Pipeline

Research replication and extension study: Evaluating MITRE ATT&CK-Grounded RAG for Technique Attribution from Windows Endpoint Logs.

## Stage 1: Data & Ground Truth

This repository contains the deterministic, reproducible pipeline for:
1. **Preflight**: Disk space verification, path containment, source preservation (`data/metadata/preflight.json`).
2. **Scaffold**: Environment locking, minimal dependencies, directory structure.
3. **Acquisition**: Windows-APT 2025 v3 (`b8fmtzvpy8`) dataset acquisition and immutable verification.
4. **Profiling**: Telemetry schema profiling, format parsing, and record mapping.
5. **Ground Truth Verification**: Traceable, independent event-level ground truth attribution.
6. **ATT&CK Reference**: Enterprise ATT&CK v19.2 reconciliation and transition auditing.
7. **Leakage Audit**: Sanitization allowlist and answer-bearing field quarantine.
8. **Sanitization & Grouping**: Deduplication (5-gram Jaccard >= 0.95) and scenario dependency grouping.
9. **Class Selection & Quota**: Pre-holdout quota freezing (8->50, 9->45, 10->40).
10. **Partitioning**: Deterministic seeded group partition (`seed=20260915`, SHA-256 mod 5).
11. **Validation & Clean Reproduction**: Offline reproduction and invariant verification.
12. **Audit & Decisions**: Full audit report and human approval gating (Decisions A & B).

## Scope Guardrails
No inference, prompt benchmarking, embeddings, FAISS, or experiment execution during this data preparation stage.
