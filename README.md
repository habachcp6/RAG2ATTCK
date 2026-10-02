# RAG2ATT&CK

**Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs**

*Tiêu đề tiếng Việt:* **Đánh giá tác động của Retrieval-Augmented Generation dựa trên MITRE ATT&CK đối với việc ánh xạ Windows Endpoint Logs sang ATT&CK Techniques**

[![Status: Protocol v1.1 Frozen & Canonical Results Verified](https://img.shields.io/badge/Status-Protocol%20v1.1%20Frozen%20%26%20Canonical%20Results%20Verified-blue.svg)](#project-status)
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

### RQ2 (Error Decomposition & Retrieval Impact per Protocol D2i)
> **How does retrieval quality affect the final accuracy of ATT&CK technique attribution?**
>
> *(Chất lượng retrieval ảnh hưởng như thế nào đến độ chính xác cuối cùng của ATT&CK Technique mapping?)*

*Objective:* Decouple and quantify failure modes within the RAG pipeline along **three independent, non-mutually-exclusive measurement axes** per Protocol Decision `D2i`:
```text
D2i Independent Measurement Axes (Non-Mutually-Exclusive, Overlaps Quantified)
├── Axis 1: Retrieval Miss Rate (D2h ANY_GT_RETRIEVED)
│   └── Ground-truth technique absent from Top-k candidates (55.29% at k=10; 397 / 718 scorable views)
│
├── Axis 2: Downstream Generation Failure (Fail-Closed)
│   └── Model produces invalid ATT&CK ID (D2e), provider failure (D2f), or wrong classification (20.47% at k=10; 147 / 718 views)
│
└── Axis 3: Joint Overlap
    └── Retrieval miss AND downstream misclassification occur simultaneously
        (80.95% of wrong classifications at k=10 occur when retrieval misses; 119 / 147 views)
```

*Methodological note:* In accordance with Protocol `D2i`, these axes are independent measurement dimensions, not disjoint partitions. We explicitly measure the joint overlap between retrieval misses and downstream generation failures rather than assuming stochastic independence.

---

### RQ3 (Retrieval Depth & Efficiency Ablation)
> **How does the number of retrieved ATT&CK candidates (Top-k) affect mapping accuracy and processing cost?**
>
> *(Số lượng ATT&CK candidates được retrieval (Top-k) ảnh hưởng như thế nào đến độ chính xác và chi phí xử lý của ATT&CK Technique mapping?)*

*Objective:* Conduct a parameter ablation study over candidate depths ($k \in \{1, 3, 5, 10\}$) to observe the trade-off between retrieval recall, context-window noise, token expenditure, and inference latency.

---

## Working Hypotheses & Empirical Findings

The following hypotheses served as working assumptions for experimental validation, evaluated against the canonical benchmark:

* **H1:** MITRE ATT&CK-grounded RAG improves technique attribution performance compared with the same LLM without retrieval.
  - *Empirical Finding:* While RAG $k=10$ achieves the highest tested accuracy (79.53% vs No-RAG 77.99%, $\Delta = +1.53$ pp), all paired difference 95% bootstrap confidence intervals contain 0 ($k=10$ delta CI $[-2.355, +5.300]$ pp; McNemar exploratory $p = 0.4219 > 0.05$). RAG $k=1$ (77.02%) and No-RAG (77.99%) have overlapping 95% CIs. **No statistically significant superiority or equivalence is claimed** on this benchmark.
* **H2:** Higher retrieval $\text{Recall}@k$ is positively associated with higher end-to-end mapping accuracy.
  - *Empirical Finding:* Increasing candidate depth from $k=1$ to $k=10$ improves Hit@k from 3.76% to 44.71%. Conditional accuracy shows $P(\text{Correct} \mid \text{GT Retrieved in Top-}10) = 91.28\%$ (293/321) versus $P(\text{Correct} \mid \text{GT Absent from Top-}10) = 70.03\%$ (278/397). Missing retrieval context does not preclude correct classification from parametric memory; no causal self-correction is assumed.
* **H3:** Increasing $k$ initially improves mapping performance, but excessive retrieved context introduces distractors (noise) and increases token/latency cost.
  - *Empirical Finding:* Confirmed: expanding $k$ from 0 to 10 increases average prompt tokens from 674.3 to 5114.3 (~7.6x) and per-query logical cost from $0.000365 to $0.001679 USD (~4.6x), while median latency increases from 2.30s to 2.67s (mean 2.90s to 4.37s).

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

### Controlled Variables & Protocol v1.1 Decisions

To preserve experimental validity, all parameters outside the retrieval mechanism remain strictly identical:
* **Dataset & Samples:** Same test split and telemetry instances across all arms (718 scorable TEST views across 440 distinct eligible clusters).
* **Language Model & Provider:** Standardized configured model name, provider and interface (`openai`, `gpt-5.6-luna`, `reasoning_effort=xhigh`, `api_interface=responses`) across arms.
* **Governance Decisions (Frozen Protocol v1.1):**
  * `D1: RECORD_ONLY`: Full raw responses captured for independent verification; all credentials, tokens, and sensitive secrets were sanitized and redacted (no raw secret leakage).
  * `D3: ALLOW_LATEST_WITH_TIMESTAMP_BINDING`: Pinned with exact UTC timestamp binding.
  * `D4: SEQUENTIAL_ONLY`: Enforces strictly sequential execution (zero concurrency-induced race conditions).
  * `D5: HARD_CAP`: Hard monetary budget limit enforced at $19.99 USD ($19.99000000 USD).
  * `Offline Evaluation`: Verification executes strictly from the 15 cryptographically locked canonical artifacts without live model calls or token expenditure.
* **Inference Parameters:** Fixed interface, reasoning effort, and output constraints. Note that parameters such as temperature, top_p, and seed are not exposed or configurable for this model/interface in the current implementation, and thus are not treatment variables.
* **Prompt Schema:** Standardized prompt template (`prompts/baseline_v1.txt`), differing only by the conditional injection of the retrieved context block.
* **Output Constraint:** Identical JSON output schema requiring a `technique_id` string, followed by the same post-hoc ATT&CK syntax and registry validation.
* **Experimental Input:** Exact same telemetry input (`endpoint_evidence`) across both arms.

The sole experimental variable is:
```text
MITRE ATT&CK retrieval:
OFF (No-RAG) vs ON (RAG k ∈ {1, 3, 5, 10})
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

The frozen synthetic generator builds evidence from the event-specific `INFERENCE_ALLOWLIST` in `src/synthetic.py`; its permitted fields vary by event type. Preflight verification accepts only `sample_id` and `endpoint_evidence` at the top level of each inference row and rejects added answer-bearing fields, including when their artifact hashes have been recomputed. This is not a generic scrubber for arbitrary real telemetry; real-data sanitization remains a separate T15 prerequisite.

---

## Dataset Strategy & Scope Boundary

The evaluation pipeline strictly separates synthetic benchmark evaluation from real telemetry validation:

### 1. Stage B Synthetic Benchmark (`synthetic-paired-v1`)
A frozen synthetic benchmark comprising 670 scenario pairs (1,340 views partitioned into 1,280 TEST views and 60 DEV views, spanning single-event and contextual-event representations across 440 distinct eligible clusters).
- Evaluated on 718 scorable TEST views (278 complete scorable pairs, 162 contextual-only pairs, 200 neither-mapped pairs).
- **Ground Truth Support Boundary:** Exactly **8 technique classes** have positive support in the TEST ground truth (768 support instances across 718 views due to 40 multi-GT views) out of the 474 frozen benchmark universe (`D2d: FROZEN_BENCHMARK_UNIVERSE = 474`).
- **Scope Invariant:** *The synthetic benchmark is strictly an engineering and diagnostic evaluation artifact. It is not real enterprise telemetry. Findings on synthetic logs MUST NOT be extrapolated to production enterprise telemetry or in-the-wild incident response.*

### 2. Real Telemetry (Status: DATA_UNAVAILABLE)
The T15 real-world telemetry pilot remains strictly status `DATA_UNAVAILABLE`.
- Authentic, sanitized multi-technique Windows endpoint telemetry meeting all provenance, ethical, and sanitization standards remains unavailable in the repository.
- Accordingly, no claims are made regarding in-the-wild detection performance or production deployment readiness.

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

## Canonical Experimental Results

The study evaluated all 5 conditions on the 718 scorable TEST views under Protocol v1.1 rules:
- `D2d: FROZEN_BENCHMARK_UNIVERSE = 474` (Macro-F1 calculated over all 474 target classes).
- `D2e: invalid_id_as_failure` (included in denominator; 0 observed on canonical scorable set).
- `D2f: api_failure_as_failure` (included in denominator; 0 observed on canonical scorable set).
- `D2g: ALLOW_HISTORICAL` (historical/deprecated technique IDs tracked as distinct observations without silent remapping).
- `D2h: ANY_GT_RETRIEVED` (multi-label retrieval hit if at least 1 GT technique is in Top-k).
- `D2i: INDEPENDENT_AXES` (failure axes measured independently with explicit overlaps).

### Canonical Candidate Summary & Cryptographic Anchors (Frozen Bundle v2)

The canonical empirical evaluation and report rendering are cryptographically bound to the frozen canonical metric bundle v2:
- **Canonical Metric Bundle v2 SHA-256 Digest:** `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`
- **Candidate Status:** `CANONICAL CANDIDATE — PENDING ROOT FINAL REVIEW`
- **Scientific Protocol Decisions Digest:** `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` (`config/experiment_protocol_v1.json`)
- **Protocol Configuration SHA-256:** `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb`
- **Evaluated Scope:** 718 scorable mapped positive TEST views ($N=718$) over 440 valid pair clusters across 474 active Windows ATT&CK techniques.
- **DOCX Typed Locators:** Table cells in `docs/report/scientific_report.docx` wrap visible text runs inside OpenXML `<w:sdtContent>` tagged with machine-readable `<w:tag>` and `<w:alias>` locators; Table 6 remains un-wrapped for direct cell reading by verification tooling.

### Primary Attribution Performance (RQ1)

| Condition | Top-k | Accuracy | Macro-F1 (474 Classes) | $\Delta$ Acc vs No-RAG | $\Delta$ F1 vs No-RAG | Absolute Accuracy 95% CI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | — | 77.99% (560/718) | 0.0126 | baseline | baseline | [74.64%, 80.88%] |
| `rag_k1` | 1 | 77.02% (553/718) | 0.0127 | -0.97 pp | +0.0001 | [73.50%, 80.17%] |
| `rag_k3` | 3 | 78.55% (564/718) | 0.0136 | +0.56 pp | +0.0010 | [75.00%, 81.74%] |
| `rag_k5` | 5 | 78.83% (566/718) | 0.0139 | +0.84 pp | +0.0013 | [75.07%, 82.35%] |
| `rag_k10`| 10 | **79.53% (571/718)** | **0.0140** | **+1.532 pp** | **+0.0014** | [75.81%, 82.85%] |

> [!IMPORTANT]
> **Statistical Significance & Uncertainty Boundary:**
> - Absolute Accuracy 95% CIs are listed above.
> - **All paired difference bootstrap confidence intervals vs No-RAG contain 0:**
>   - $k=10$ delta CI: **[-2.355, +5.300] pp**
>   - Exact two-sided McNemar test ($k=10$ vs No-RAG): $p = 0.4219$ (reported to 3 decimals as $p = 0.422 > 0.05$; not statistically significant).
> - RAG $k=10$ is reported as the **highest tested accuracy observed in the experiment alongside its uncertainty**. The study does **NOT** claim a statistically significant advantage or production superiority over No-RAG.

### Whole-Study Financial Accounting (RQ3)

- **Hard Budget Limit (`D5`):** $19.99 USD ($19.99000000 USD).
- **Settled Spend (5 Canonical Conditions):** **$6.58 USD** ($6.57575890 USD accounted from frozen tariffs).
- **Provisional Pilot Hold:** $0.05264010 USD (`prior_pilot_provisional_hold_usd`).
- **Total Accounted Committed Spend:** **$6.63 USD** ($6.62839900 USD).
- **Net Remaining Uncommitted Balance:** **$13.36 USD** ($13.36160100 USD; 0 budget breach, 0 active holds).
- **Execution Log Quality:** 6,387 VALID dispatches out of 6,400 total dispatches across 5 conditions; 13 INCOMPLETE records preserved for transparency; 1 transient API failure retry with $0.53974560 hold settled cleanly.
- **P95 Latency Status:** P95 latency is **NOT REPORTED** (withheld per Root policy; `p95_status: "NOT REPORTED — approval evidence not established"`). Observed mean latencies range from $2.90\text{ s}$ to $4.37\text{ s}$ and medians from $2.30\text{ s}$ to $2.87\text{ s}$.

---

## Research Contribution

> **RAG2ATT&CK is a controlled empirical study evaluating the effect of MITRE ATT&CK-grounded retrieval on technique-level attribution from Windows endpoint telemetry. It additionally separates retrieval failures from downstream LLM classification failures using three independent measurement axes per Protocol D2i, and evaluates the effect of retrieval depth on mapping performance and processing cost.**

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
├── config/                     # Canonical model, retrieval, benchmark configs, lock v1
├── data/
│   ├── ground_truth/synthetic/ # Frozen Stage B benchmark (1,340 views, 670 pairs)
│   └── synthetic/              # Smoke test cases
├── docs/                       # Technical documentation, slides, reproducibility guide
│   └── presentation/           # PowerPoint deck, slides markdown, and visual preview
├── prompts/                    # Frozen baseline prompt template
├── reports/                    # Task reports (T15, T19, T20, protocol v1)
│   └── evidence/               # Cryptographic audits, manifests, pilot records
├── scripts/                    # Reproduction pipelines, deck updaters, offline guards
├── src/
│   ├── baseline/               # Baseline No-RAG pipeline
│   ├── evaluation/             # Retrieval diagnostics and metric calculation
│   ├── llm/                    # OpenAI client, schemas, live budget management
│   ├── pilot/                  # T15 bounded No-RAG pilot runner and provenance
│   ├── rag/                    # RAG pipeline with controlled-treatment invariants
│   └── retrieval/              # FAISS retriever, embedders, and corpus loader
└── tests/                      # Unit, contract, regression, and boundary test suites
```

---

## Independent Reproduction & Verification

The canonical study evaluation and analysis can be independently re-evaluated and verified offline with **zero cost and zero network egress** (`OFFLINE_GUARD` socket-level protection).

### Prerequisites & Preparation
1. **Dependencies:** Install frozen dependencies using `uv sync --frozen`.
2. **STIX v19.2 Knowledge Corpus:** Ensure the enterprise ATT&CK STIX bundle is present at `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` with mandatory SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`.
3. **Canonical Accepted Bundle / Portable Package:** The reproduction helper verifies an immutable bundle directory containing:
   - **10 Canonical Input Files:** `manifest.json`, 5 prediction JSONLs (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`), `request_journal.jsonl`, `run_summary.json`, `study_ledger.json`, and `.study_anchor.json`.
   - **8 Accepted Analytical Output Files:** `overall_metrics.json`, `per_condition_metrics.json`, `per_technique_metrics.json`, `retrieval_conditional_metrics.json`, `failure_decomposition.json`, `run_provenance.json`, `rq_analysis.json`, and `rq_analysis_summary.md`.
   - **22 Protected Baseline Files & 15 Artifact Bindings:** Cryptographically verified against frozen digests.

```bash
# Guarded Canonical Scientific Replay (Native-6 evaluation + RQ analysis, bootstrap 1000, seed 42):
python scripts/run_offline_tests.py -m scripts.reproduce_canonical_study \
  --bundle-dir <path/to/canonical-bundle> \
  --repository-root . \
  --output-dir <path/to/isolated-output> \
  --expected-manifest-sha <expected_sha256> \
  --all

# Full offline regression test suite under socket-level egress guard:
python scripts/run_offline_tests.py -m pytest tests/test_presentation_and_repro_regressions.py tests/test_canonical_reproduction_boundary.py -q

# Historical diagnostic fixture helper:
python scripts/reproduce_study.py
```

---

## Project Status

**Current Engineering Status:** Engineering complete pending final integrated CI validation. The frozen MITRE ATT&CK v19.2 knowledge corpus, FAISS retriever, RAG/No-RAG pipelines, canonical evaluation engine, automated 16:9 presentation deck builder, and offline verification runners are implemented and verified with 100% passing tests under `OFFLINE_GUARD` (0 network egress).

**Current Research & Empirical Status:**
- **Synthetic Benchmark (`synthetic-paired-v1`):** Complete (670 total benchmark scenario pairs / 1,340 total paired views across benchmark; partitioned to 440 distinct eligible clusters in the canonical TEST evaluation cohort yielding 718 scorable views across 8 ground-truth techniques).
- **RQ1 Comparative Attribution:** Verified and packaged in candidate (ready for formal publication; not yet published). RAG $k=10$ observed accuracy 79.53% vs No-RAG 77.99% ($\Delta = +1.53$ pp; paired difference 95% CI $[-2.355, +5.300]$ pp contains 0, McNemar $p = 0.4219 > 0.05$).
- **RQ2 Retrieval Diagnostics:** Verified and packaged in candidate. Hit@10 = 44.71%, Recall@10 = 42.80% on 718 scorable views; $T1136.001$ semantic gap 0% hit rate.
- **RQ3 Resource & Financial Accounting:** Verified and packaged in candidate. $6.58 settled spend / $6.63 committed spend on $19.99 hard cap ($13.36 net remaining).
- **Real Telemetry Availability (T15):** Status remains `DATA_UNAVAILABLE` (preserved strictly).

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
