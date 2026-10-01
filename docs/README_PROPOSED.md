# RAG2ATT&CK

**Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs**

*Tiêu đề tiếng Việt:* **Đánh giá tác động của Retrieval-Augmented Generation dựa trên MITRE ATT&CK đối với việc ánh xạ Windows Endpoint Logs sang ATT&CK Techniques**

[![Status: Protocol v1.1 Frozen & Pilot Verified](https://img.shields.io/badge/Status-Protocol%20v1.1%20Frozen%20%26%20Pilot%20Verified-blue.svg)](#project-status)
[![Canonical Lock: canonical-lock-v1](https://img.shields.io/badge/Canonical%20Lock-canonical--lock--v1-success.svg)](config/canonical_experiment_lock_v1.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)
[![Zero-Cost Reproduction: Offline Guard](https://img.shields.io/badge/Reproduction-100%25%20Offline%20Verified-teal.svg)](docs/reproducibility.md)

---

## Abstract & Motivation

RAG2ATT&CK is a research prototype designed to investigate whether grounding Large Language Models (LLMs) with external knowledge from the MITRE ATT&CK® matrix via Retrieval-Augmented Generation (RAG) improves the accuracy and reliability of automated threat technique attribution from raw Windows endpoint telemetry.

### Research Positioning

> *Although RAG has been investigated for cybersecurity log analysis and ATT&CK mapping, controlled evaluations of ATT&CK-grounded RAG specifically for technique-level attribution from Windows endpoint telemetry remain limited. This project evaluates the effect of retrieval augmentation and separately analyzes retrieval quality and downstream classification performance.*

This project does **not** claim to invent Retrieval-Augmented Generation, ATT&CK mapping methodologies, or LLM-assisted log triage. Instead, it contributes a strictly controlled empirical evaluation isolating the performance delta introduced by domain-specific retrieval grounding.

---

## Research Questions

The study investigates three core research questions:

### RQ1 (Primary Research Question)
> **To what extent does MITRE ATT&CK-grounded RAG improve the accuracy of LLM-based ATT&CK technique attribution from Windows endpoint logs compared with the same LLM without retrieval augmentation?**
>
> *(Việc bổ sung MITRE ATT&CK-grounded RAG ảnh hưởng như thế nào đến độ chính xác của LLM khi ánh xạ Windows endpoint logs sang ATT&CK Techniques so với cùng mô hình không sử dụng RAG?)*

*Objective:* Measure the end-to-end attribution accuracy gain (if any) when augmenting an identical LLM with a dedicated ATT&CK retrieval component under identical prompting and configuration conditions.

---

### RQ2 (Error Decomposition & Retrieval Impact)
> **How does retrieval quality affect the final accuracy of ATT&CK technique attribution?**
>
> *(Chất lượng retrieval ảnh hưởng như thế nào đến độ chính xác cuối cùng của ATT&CK Technique mapping?)*

*Objective:* Decouple and quantify failure modes within the RAG pipeline:
```text
RAG Failure
├── Retrieval Failure
│   └── Ground-truth technique is NOT present in the retrieved Top-k candidates
│
└── Generation / Classification Failure
    └── Ground-truth technique WAS retrieved, but the LLM failed to select it
```

---

### RQ3 (Retrieval Depth & Efficiency Ablation)
> **How does the number of retrieved ATT&CK candidates (Top-k) affect mapping accuracy and processing cost?**
>
> *(Số lượng ATT&CK candidates được retrieval (Top-k) ảnh hưởng như thế nào đến độ chính xác và chi phí xử lý của ATT&CK Technique mapping?)*

*Objective:* Conduct a parameter ablation study over candidate depths ($k \in \{1, 3, 5, 10\}$) to observe the trade-off between retrieval recall, context-window noise, token expenditure, and inference latency.

---

## Working Hypotheses

The following hypotheses serve as working assumptions for experimental validation:

* **H1:** MITRE ATT&CK-grounded RAG improves technique attribution performance compared with the same LLM without retrieval.
* **H2:** Higher retrieval $\text{Recall}@k$ is positively associated with higher end-to-end mapping accuracy.
* **H3:** Increasing $k$ initially improves mapping performance, but excessive retrieved context introduces distractors (noise) and increases token/latency cost.

---

## Core Experimental Design

This research is designed as a **controlled empirical evaluation** comparing two distinct pipelines on the exact same telemetry inputs.

### Pipeline Architectures

#### 1. Baseline Pipeline (No-RAG)
```text
Windows Endpoint Log
        ↓
       LLM
        ↓
MITRE ATT&CK Technique
```

#### 2. Experimental Pipeline (RAG)
```text
Windows Endpoint Log
        ↓
MITRE ATT&CK Retriever
        ↓
Top-k relevant ATT&CK Techniques
        ↓
Log + Retrieved ATT&CK Knowledge
        ↓
       LLM
        ↓
MITRE ATT&CK Technique
```

### Controlled Variables

To preserve experimental validity, all parameters outside the retrieval mechanism remain strictly identical:
* **Dataset & Samples:** Same test split and telemetry instances across both arms.
* **Language Model & Provider:** Strictly pinned to `openai`, model `gpt-5.6-luna`, `reasoning_effort=xhigh`, `api_interface=responses` across arms.
* **Provider Version Policy (Resolved in Protocol v1.1 - D3):** Frozen under `ALLOW_LATEST_WITH_TIMESTAMP_BINDING`, requiring UTC request/response timestamps and returned `system_fingerprint` capture in the request journal.
* **Inference Parameters:** Fixed interface, reasoning effort, and output constraints. Parameters such as temperature, top_p, and seed use provider defaults and are not treatment variables.
* **Prompt Schema:** Standardized prompt template (`prompts/baseline_v1.txt`), differing only by the conditional injection of the retrieved context block.
* **Output Constraint:** Identical JSON output schema requiring a `technique_id` string, followed by the same post-hoc ATT&CK syntax and registry validation.
* **Experimental Input:** Exact same telemetry input (`endpoint_evidence`) across both arms.

The sole experimental variable is:
```text
MITRE ATT&CK retrieval:
OFF vs ON
```

*Note:* Provider comparisons (e.g., GPT vs. Gemini vs. Claude) are explicitly excluded from the core experiment to avoid confounding variables.

---

## Telemetry Input & Attribution Output

### Input Specification
The input consists of structured Windows endpoint security logs, focusing on:
* Windows Security Event Logs (e.g., Process Creation Event ID 4688, Account Creation Event ID 4720)
* Microsoft Sysmon telemetry (e.g., Event ID 1: Process Create, Event ID 3: Network Connect, Event ID 11: File Create, Event ID 13: Registry Event)
* Standard structured Windows endpoint telemetry events.

*Implementation Note:* No SIEM infrastructure or Wazuh decoder reimplementation is required. Native structured Windows/Sysmon event fields provide sufficient signal for the research prototype.

### Output Specification
The primary output for evaluation is the canonical MITRE ATT&CK Technique or Sub-technique identifier:
* **Primary Target:** Exact ID string (e.g., `T1059.001`, `T1053.005`, `T1003.001`).
* **Secondary Metadata (Recorded for diagnostics):** Technique name, candidate rank, and model self-assessed confidence.

---

## Anti-Label-Leakage Protocol

To guarantee methodological integrity and prevent target leakage from detection rules or benchmark artifacts:

> **Ground-truth labels and rule-derived ATT&CK metadata must be excluded from inference inputs to prevent label leakage.**

The frozen synthetic generator builds evidence from the event-specific `INFERENCE_ALLOWLIST` in `src/synthetic.py`; its permitted fields vary by event type. Preflight accepts only `sample_id` and `endpoint_evidence` at the top level of each inference row and rejects added answer-bearing fields, including when their artifact hashes have been recomputed. Real-data sanitization remains a separate T15 prerequisite.

---

## Dataset Strategy

The evaluation pipeline strictly separates synthetic benchmark evaluation from real telemetry validation:

### 1. Stage B Synthetic Benchmark (Development & Diagnostic Evaluation)
A frozen synthetic benchmark comprising 670 scenario pairs (1,340 views partitioned into 1,280 TEST views and 60 DEV views, spanning single-event and contextual-event representations).
- Bound by cryptographic SHA-256 digests in [`config/canonical_experiment_lock_v1.json`](config/canonical_experiment_lock_v1.json).
- Used for pipeline integrity verification, parser and schema validation, anti-leakage auditing, and retrieval diagnostics (T20).
- Covers representative target technique classes alongside unmapped/ambiguous negative controls.
- *The synthetic benchmark is strictly an engineering and diagnostic evaluation artifact. It is not real telemetry and is not used to claim real-world empirical performance.*

### 2. Real Telemetry (Pilot & Eventual Empirical Evaluation)
The final empirical validation and the T15 pilot require legitimate, sanitized real-world Windows endpoint telemetry traces with verified MITRE ATT&CK ground-truth labels.
- While candidate collections (such as Windows-APT 2025 traces) have been considered, approved real telemetry remains **currently unavailable / not finalized** in the repository.
- Accordingly, the T15 real-data No-RAG pilot is status `PARTIAL / BLOCKED — DATA_UNAVAILABLE` until an approved real-data source meeting all provenance and sanitization criteria is integrated.

---

## MITRE ATT&CK Knowledge Base & Retrieval

### Knowledge Corpus
* Grounded directly in official MITRE ATT&CK Enterprise STIX/JSON data, pinned to **v19.2** (`attack/corpus/enterprise-windows-v19.2.jsonl`, 474 documents).
* Extracted document chunks incorporate:
  * Technique ID
  * Technique Name
  * Detailed Description
  * Target Platforms (Windows-scoped)
  * Detection-related information
  * Selected Procedure examples (strictly curated to avoid near-duplicate leakage against evaluation logs).

### Lightweight Retrieval Engine
To maintain experimental reproducibility without heavy infrastructure overhead:
* **Embedding Model:** Dense representations via `sentence-transformers/all-MiniLM-L6-v2` (pinned revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, dimension 384, L2 normalized).
* **Vector Index:** Flat inner product vector indexing (`IndexFlatIP`, cosine similarity) managed by `FAISS` (`attack/index/enterprise-windows-v19.2.index`).
* **Retrieval Limits:** Canonical candidate depths $k \in \{1, 3, 5, 10\}$ (default: 5).
* *Zero heavyweight dependencies:* No external vector database servers, no knowledge graphs, and no Elasticsearch clusters required.

---

## Frozen Evaluation Protocol v1.1 & Metrics

Scientific evaluation decisions are frozen under [`config/experiment_protocol_v1.json`](config/experiment_protocol_v1.json) (SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`):

| Protocol Decision | Frozen Policy | Scientific Rationale |
| :--- | :--- | :--- |
| **D1: Raw Response Policy** | `RECORD_ONLY` | Full raw responses logged for auditability; parsed field used for metrics. |
| **D2a: Ground-Truth Semantics** | `ANY_MATCH` | For multi-label views, prediction matching any valid ground-truth ID is scored correct. |
| **D2b: Empty Ground-Truth** | `EXCLUDE` | Unmapped samples excluded from scorable attribution accuracy denominator. |
| **D2c: Ambiguous Ground-Truth** | `EXCLUDE` | Ambiguous samples excluded from scorable accuracy denominator. |
| **D2d: Macro-F1 Class Universe** | `FROZEN_BENCHMARK_UNIVERSE` | Evaluated across the fixed universe of target benchmark technique classes. |
| **D2e: Invalid ATT&CK ID Denominator** | `INCLUDE_IN_DENOMINATOR` | Malformed/hallucinated IDs count as prediction failures in the denominator. |
| **D2f: API Error Denominator** | `INCLUDE_IN_DENOMINATOR` | Provider errors are not omitted; they count as failures in end-to-end evaluation. |
| **D2g: Retired ATT&CK IDs** | `ALLOW_HISTORICAL` | Valid historical IDs present in STIX v19.2 are accepted if syntactically correct. |
| **D2h: Conditional Retrieval** | `ANY_GT_RETRIEVED` | Retrieval success defined as any true technique present in Top-k. |
| **D2i: Failure Precedence** | `INDEPENDENT_AXES` | Retrieval failure and classification failure reported on orthogonal axes. |
| **D2j: Zero Denominator** | `NULL` | Undefined denominators render explicit `null` rather than artificial 0.0. |
| **D3: Model Version Policy** | `ALLOW_LATEST_WITH_TIMESTAMP_BINDING` | Pinned model string with exact UTC timestamps and system fingerprints. |
| **D4: Concurrency Policy** | `SEQUENTIAL_ONLY` | Single-worker sequential dispatch eliminates concurrency non-determinism. |
| **D5: Budget Policy** | `HARD_CAP_WORST_CASE_ATTEMPTS` | Budget capped by worst-case provider attempt bounds. |
| **D6: T15 Prerequisite Policy** | `NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK` | Stage B synthetic benchmark decoupling from real-telemetry availability. |
| **D7: Dataset Scope** | `PAIRED_TEST` | Canonical evaluation scope bound to the 1,280-view TEST cohort. |

---

## Current Repository Structure

```text
RAG2ATTCK/
├── .github/workflows/          # CI and Real Retrieval Integration workflows
├── attack/
│   ├── corpus/                 # Enterprise Windows ATT&CK v19.2 corpus (474 docs)
│   ├── index/                  # FAISS index, docmap, and provenance manifests
│   └── raw/                    # Raw MITRE ATT&CK STIX v19.2 release JSON
├── config/
│   ├── canonical_experiment_lock_v1.json # Immutable lock of 15 canonical artifacts
│   ├── experiment_config.json  # Canonical experiment configuration
│   ├── experiment_protocol_v1.json # Frozen scientific protocol v1.1 decisions (D1-D7)
│   ├── model.json              # Canonical LLM provider configuration
│   ├── pricing_v1.json         # Pinned API pricing specifications
│   └── retrieval.json          # Retrieval hyperparameter specification
├── data/
│   ├── ground_truth/synthetic/ # Frozen Stage B benchmark (1,340 views, 670 pairs)
│   └── synthetic/              # Smoke test cases
├── docs/
│   ├── presentation/           # Presentation slides (slides.md, slides.pptx)
│   ├── reproducibility.md      # Comprehensive offline reproduction guide
│   └── sanitized_evidence_manifest.json # Complete artifact packaging manifest
├── prompts/                    # Frozen baseline prompt template
├── reports/
│   ├── evidence/
│   │   ├── dev_cost_pilot_20261001/ # Byte-preserved 20-request pilot evidence
│   │   └── reproducibility_package_manifest.md # Reproducibility package evidence
│   └── T20_retrieval_diagnostics.md # Retrieval evaluation report
├── scripts/
│   ├── generate_slides.py      # Automated PowerPoint deck builder
│   ├── reproduce_study.py      # Full offline verification & reproduction pipeline
│   ├── run_offline_tests.py    # Egress-intercepting offline test runner
│   └── verify_t20_canonical_artifacts.py # Independent T20 hash recomputation
├── src/
│   ├── baseline/               # Baseline No-RAG pipeline
│   ├── evaluation/             # Canonical evaluator & error decomposition
│   ├── experiment/             # Gated runner, journal, monetary ledger, authorization
│   ├── llm/                    # OpenAI Responses API client, schemas, budget guard
│   ├── rag/                    # RAG pipeline with controlled-treatment invariants
│   └── retrieval/              # FAISS retriever, embedders, and corpus loader
└── tests/                      # Unit, contract, and integration test suites (1,200+ tests)
```

---

## Project Status

**Engineering Status:** Complete and verified across Linux (Ubuntu) and Windows in CI.
- **Stage B Synthetic Benchmark:** 670 scenario pairs (1,340 views) fully generated, schema-validated, anti-leakage verified, and locked under `canonical-lock-v1`.
- **Knowledge Base & Retriever:** Pinned MITRE ATT&CK v19.2 knowledge corpus and FAISS vector index with dense `all-MiniLM-L6-v2` embeddings.
- **Protocol v1.1 Frozen:** All scientific decisions (D1–D7) approved and locked under hash `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`.
- **Offline Evaluator Infrastructure:** Canonical evaluator implements decoupled error decomposition, conditional accuracy, and atomic 6-artifact export.

**Empirical Research Status:**
- **Retrieval Diagnostics (T20):** Independently evaluated on 756 positive views:
  - $Hit@1 = 4.23\%$, $Hit@3 = 16.80\%$, $Hit@5 = 24.21\%$, $Hit@10 = 45.11\%$.
  - Ground-truth absent from Top-10 rate: $54.89\%$.
  - Canonical anchor analysis on 296 eligible pairs yields strictly better retrieval ranks for single-event views in 65 pairs (22.0%) vs. 23 pairs (7.8%) for contextual-event views (208 equal). Under a secondary strict single-technique cohort (252 pairs), single-event achieved better ranks in 59 pairs vs. 23 pairs (170 equal). These represent observed empirical retrieval rank differences under dense semantic search.
  - Semantic gap identified in `T1136.001` (0% Top-10 hits across 99 positive views).
- **Approved DEV Cost Pilot (2026-10-01):**
  - Executed 20 real OpenAI Responses API calls across 4 DEV views and all 5 conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`) using `gpt-5.6-luna` with `reasoning_effort=xhigh`.
  - 100% valid schema adherence, zero provider retries.
  - Measured spend: **$0.0242094**; projected uncached Standard-price test cost: **$8.20** (conservative input: **$8.99**).
- **Canonical 1,280-View TEST Execution:** Fully implemented and cryptographically locked. Execution is in-flight or awaiting live run termination under PID 50192. Evaluator enforces a strict fail-closed contract requiring all 6,400 records.
- **Real Telemetry Availability:** T15 real-data pilot remains separated (`DATA_UNAVAILABLE`) pending an approved, legitimate, sanitized real-world Windows telemetry dataset.

---

## Offline Reproduction Quickstart

To reproduce all artifact hashes, recompute retrieval diagnostics, execute the canonical evaluator, and generate figures and tables:

```bash
# 1. Install dependencies
uv sync

# 2. Run offline reproduction pipeline
uv run python scripts/reproduce_study.py

# 3. View generated report and figures
cat outputs/reproduction/reproduction_report.md
```

For full step-by-step instructions, see the [`docs/reproducibility.md`](docs/reproducibility.md) guide.

---

## License & Provenance

- **License:** This project is distributed under the terms of the MIT License. Note that while the repository metadata declares MIT licensing, a standalone `LICENSE` text file is currently not present in the repository tree.
- **Runtime Launcher Binding:** The pinned executable runtime launcher hash is `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa` (incorporating a Windows WinError 5/32 exponential backoff retry wrapper for atomic filesystem operations).
- **Technique Naming Alignment:** Active ATT&CK technique `T1059.009` is named `'Command & Scripting: Cloud API'`. ATT&CK technique `T1218.012` is named `'System Binary Proxy Execution: Verclsid'`.
