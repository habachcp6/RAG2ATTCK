# RAG2ATT&CK

**Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs**

*Tiêu đề tiếng Việt:* **Đánh giá tác động của Retrieval-Augmented Generation dựa trên MITRE ATT&CK đối với việc ánh xạ Windows Endpoint Logs sang ATT&CK Techniques**

[![Status: Pipeline Implemented & Retrieval Diagnosed](https://img.shields.io/badge/Status-Pipeline%20Implemented%20%26%20Retrieval%20Diagnosed-blue.svg)](#project-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)

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
* **Language Model & Provider:** Same configured model name, provider and interface (`openai`, `gpt-5.6-luna`, `reasoning_effort=xhigh`, `api_interface=responses`) across arms. The exact provider backend-version policy remains unresolved before protocol freeze.
* **Inference Parameters:** Fixed interface, reasoning effort, and output constraints. Note that parameters such as temperature, top_p, and seed are not exposed or configurable for this model/interface in the current implementation, and thus are not treatment variables.
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
* Windows Security Event Logs (e.g., Process Creation Event ID 4688)
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

The frozen synthetic generator builds evidence from the event-specific
`INFERENCE_ALLOWLIST` in `src/synthetic.py`; its permitted fields vary by
event type. T21 preflight accepts only `sample_id` and `endpoint_evidence`
at the top level of each inference row and rejects added answer-bearing fields,
including when their artifact hashes have been recomputed. This is not a
generic scrubber for arbitrary real telemetry; real-data sanitization remains
a separate T15 prerequisite.

---

## Dataset Strategy

The evaluation pipeline strictly separates synthetic benchmark evaluation from real telemetry validation:

### 1. Stage B Synthetic Benchmark (Development & Diagnostic Evaluation)
A frozen synthetic benchmark comprising 670 scenario pairs (1,340 views partitioned into 1,280 TEST views and 60 DEV views, spanning single-event and contextual-event representations).
- Used strictly for pipeline integrity verification, parser and schema validation, anti-leakage auditing, and retrieval diagnostics (T20).
- Covers 8 representative target technique classes alongside unmapped/ambiguous negative controls.
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
* *Zero heavyweight dependencies:* No external vector database servers (Pinecone, Milvus), no knowledge graphs, and no Elasticsearch clusters required.

#### Document Processing Flow:
```text
MITRE ATT&CK STIX Documents
            ↓
    Text Chunking & Metadata
            ↓
     Embedding Model
            ↓
       FAISS Index
```

#### Inference Query Flow:
```text
Sanitized Windows Log
         ↓
  Embedding Model
         ↓
    FAISS Search
         ↓
Top-k ATT&CK Candidates
         ↓
        LLM
```

---

## Language Model & Inference Protocol

* **Model Usage:** The same configured LLM provider API interface is planned across baseline and experimental arms:
  * Provider: `openai`
  * Model: `gpt-5.6-luna`
  * Reasoning Effort: `xhigh`
  * API Interface: `responses`
  * Structured Output: JSON schema requiring a `technique_id` string; post-hoc validation checks ATT&CK ID syntax and registry membership.
* **No Fine-Tuning:** The research focuses purely on in-context retrieval augmentation without modifying model weights.

---

## Evaluation Metrics

| Metric | Target Component | Purpose |
| :--- | :--- | :--- |
| **Exact-Match Accuracy** | End-to-End | Primary metric: Fraction of predictions matching ground-truth ATT&CK ID |
| **Macro-F1 Score** | End-to-End | Primary metric: Unweighted mean of F1 scores across technique classes |
| **Precision & Recall** | End-to-End | Per-class false positive and false negative attribution analysis |
| **Invalid ATT&CK ID Rate** | Robustness | Final treatment of malformed, retired, or unknown IDs and its denominator require protocol freeze |
| **Hit@k / Macro Recall@k (T20 diagnostics)** | Retriever | Hit@k counts positive views with any ground-truth ID in Top-k; Macro Recall@k averages the per-view fraction of ground-truth IDs retrieved. Canonical study scoring remains pending |
| **Token Usage** | Efficiency (RQ3) | Prompt and completion token consumption per sample |
| **Inference Latency** | Efficiency (RQ3) | Wall-clock inference time (seconds per sample) |

---

## Research Contribution

> **RAG2ATT&CK is a controlled empirical study evaluating the effect of MITRE ATT&CK-grounded retrieval on technique-level attribution from Windows endpoint telemetry. It additionally separates retrieval failures from downstream LLM classification failures and evaluates the effect of retrieval depth on mapping performance and processing cost.**

---

## What This Project is NOT (Scope & Exclusions)

To maintain focus and empirical validity, the project explicitly excludes:
* ❌ An operational SIEM, EDR, or SOC analytical platform.
* ❌ Wazuh parser integration, agent deployment, or decoder reimplementation.
* ❌ Autonomous multi-agent systems or complex agentic decision loops.
* ❌ Knowledge graphs or graph database infrastructure.
* ❌ Custom model training or fine-tuning.
* ❌ Custom SDK development, heavy dashboards, or production backends.
* ❌ Large-scale distributed server infrastructure.

The expected deliverable is a self-contained, reproducible **Python research prototype**, experimental configurations, results logs, and the research report.

---

## Current Repository Structure

```text
RAG2ATTCK/
├── .github/workflows/          # CI and Real Retrieval Integration workflows
├── attack/
│   ├── corpus/                 # Enterprise Windows ATT&CK v19.2 corpus
│   └── index/                  # FAISS index, docmap, and provenance manifests
├── config/                     # Canonical model, retrieval, and benchmark configs
├── data/
│   ├── ground_truth/synthetic/ # Frozen Stage B benchmark (1,340 views, 670 pairs)
│   └── synthetic/              # Smoke test cases
├── prompts/                    # Frozen baseline prompt template
├── reports/                    # Task reports (T15, T19, T20, etc.)
├── src/
│   ├── baseline/               # Baseline No-RAG pipeline
│   ├── evaluation/             # Retrieval diagnostics and metric calculation
│   ├── llm/                    # OpenAI client, schemas, live budget management
│   ├── pilot/                  # T15 bounded No-RAG pilot runner and provenance
│   ├── rag/                    # RAG pipeline with controlled-treatment invariants
│   └── retrieval/              # FAISS retriever, embedders, and corpus loader
└── tests/                      # Unit, contract, and integration test suites
```

---

## Project Status

**Current Engineering Status:** Stage B synthetic benchmark, frozen MITRE ATT&CK v19.2 knowledge corpus, FAISS retriever, RAG/No-RAG pipelines, T20 retrieval diagnostics, and T15 bounded No-RAG pilot infrastructure have been implemented and verified with full CI test suites (Linux + Windows) and real retrieval integration tests.

**Current Research & Empirical Status:**
- **Synthetic Benchmark:** Stage B synthetic benchmark (670 scenario pairs, 1,340 views partitioned into 1,280 TEST views and 60 DEV views) is fully frozen and verified for development, schema integrity, and retrieval diagnostics (T20).
- **Retrieval Diagnostics (T20):** Evaluated independently on the 756 positive views of the synthetic benchmark ($Hit@1 \approx 0.0423$, $Hit@10 \approx 0.4511$).
- **End-to-End Evaluation:** The live end-to-end comparative experiment (RAG vs. No-RAG) remains pending.
- **Real Telemetry Availability:** The T15 real-data pilot remains blocked (`DATA_UNAVAILABLE`) pending an approved, legitimate, sanitized real-world Windows telemetry dataset. The synthetic benchmark is explicitly not treated as real telemetry.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
