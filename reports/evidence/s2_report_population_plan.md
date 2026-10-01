# Scientific Report Population Plan for Phase S2: Canonical Execution to Publication Delivery

**Task Handle:** Subagent C: Research Report & Publication Lead (Phase S2 Planning)  
**Assigned Worktree:** `D:/RAG2ATTCK-worktrees/report-s1`  
**Git Branch:** `codex/s1-report-related-work` (PR #25)  
**PRE_SHA:** `b4bd35ffe1b947027c858835c477c0bdef9c8118`  
**Date:** October 2026  
**Document Status:** DRAFT — PENDING CODEX SUPERVISOR REVIEW  
**Operational Invariant 1 (Strictly Plan-Only):** Strictly **ZERO** invented numerical results; all pending experimental tables and narrative statistics remain explicit schemas with formal placeholders (`[TBD_AT_EXECUTION]`) until canonical execution outputs are finalized.  
**Operational Invariant 2 (Empirical Grounding):** Strictly **ZERO** mock, fixture, or synthetic pilot numbers shall be presented as canonical findings. All populated figures and metrics must trace bijectively to authoritative outputs in `outputs/canonical_evaluation/` and `outputs/canonical_analysis/`.  
**Operational Invariant 3 (Zero Egress Invariant):** All post-execution analysis, report population, figure generation, and compilation scripts execute under the offline socket guard (`OFFLINE_GUARD: installed=True attempted_egress=0`).  

---

## 1. Executive Summary and Phase S2 Lifecycle

Phase S1 established a cryptographically grounded, publication-quality research report scaffold (`docs/report/scientific_report.md` and `docs/report/scientific_report.docx`) governed by Scientific Protocol v1.1 (Decisions D1–D7). In Phase S1, all literature comparators, threat boundaries, evaluator invariants, and taxonomic census definitions were verified and frozen.

The purpose of this document is to specify the **complete, deterministic population protocol** for Phase S2. Once the canonical live execution engine completes the planned 6,400 inference requests across the 1,280 paired TEST views under the USD 19.99 budget guard, this plan governs the step-by-step extraction, formatting, population, visual compilation, and verification of the final publication deliverable.

```
+----------------------------------------------------------------------------------------------------+
|                                    PHASE S2 EXECUTION PIPELINE                                      |
+----------------------------------------------------------------------------------------------------+
| 1. CANONICAL EXECUTION                                                                              |
|    - 6,400 live requests: 1,280 TEST views x 5 conditions (no_rag, rag_k1, rag_k3, rag_k5, rag_k10) |
|    - Live budget ledger: USD 19.99 hard ceiling; concurrency = 1; local JSONL journals             |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
| 2. CANONICAL EVALUATION & ANALYSIS                                                                 |
|    - evaluate_experiment() -> outputs/canonical_evaluation/ (EXACTLY 6 NATIVE FILES):             |
|      * overall_metrics.json                                                                        |
|      * per_condition_metrics.json                                                                  |
|      * per_technique_metrics.json                                                                  |
|      * retrieval_conditional_metrics.json                                                          |
|      * failure_decomposition.json                                                                  |
|      * run_provenance.json                                                                         |
|    - Specialist B analysis runner -> outputs/canonical_analysis/                                    |
|      * rq_analysis.json (unified analysis containing: rq1, rq2, rq3,                               |
|        rq3.tradeoffs_by_condition, and rq3.view_diagnostics)                                       |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
| 3. REPORT POPULATION & VISUALIZATION                                                               |
|    - scripts/reproduce_study.py -> docs/report/figures/ (Figures 1-4, 300 DPI PNG)                 |
|    - scripts/populate_report.py -> docs/report/scientific_report.md (Tables 2-6 & Narratives)       |
+----------------------------------------------------------------------------------------------------+
                                                  |
                                                  v
+----------------------------------------------------------------------------------------------------+
| 4. PUBLICATION COMPILATION & VISUAL QA                                                             |
|    - scripts/export_report_docx.py -> docs/report/scientific_report.docx                            |
|    - Native Word COM export -> docs/report/scientific_report.pdf                                   |
|    - Independent offline QA: verify_report_metadata.py & pypdfium2 visual inspection               |
+----------------------------------------------------------------------------------------------------+
```

> [!IMPORTANT]
> **Native Evaluator Contract Alignment:** The canonical evaluation engine (`src/evaluation/experiment_metrics.py:evaluate_experiment`) exports **exactly six native JSON files**:
> 1. `overall_metrics.json`
> 2. `per_condition_metrics.json`
> 3. `per_technique_metrics.json`
> 4. `retrieval_conditional_metrics.json`
> 5. `failure_decomposition.json`
> 6. `run_provenance.json`
>
> Legacy or non-standard file identifiers (such as `evaluation_summary.json` or `condition_metrics.json`) **do NOT exist** in the RAG2ATTCK codebase and must never be referenced by population or analysis scripts. All evaluation metrics are parsed directly and authoritatively from these six native exports.
>
> **Specialist B Analysis Contract Alignment:** Specialist B exports **a single unified analysis deliverable**: `outputs/canonical_analysis/rq_analysis.json`. Specialist B does *not* export multi-file splits (such as `pairwise_representation_comparison.json` or `resource_scaling.json`). All research question syntheses, representation comparisons, subset macro calculations, and cost-latency trade-offs are structured under canonical top-level branches: `rq1`, `rq2`, `rq3`, `rq3.tradeoffs_by_condition`, and `rq3.view_diagnostics`.

---

## 2. Placeholders-to-Artifact Mapping Specification

Every placeholder in `docs/report/scientific_report.md` and `docs/report/scientific_report.docx` maps directly and bijectively to a canonical evaluation artifact.

### 2.1 Table Mapping Overview

| Report Table | Table Title | Primary Source Artifact | Output JSON Key / Sub-path |
| :--- | :--- | :--- | :--- |
| **Table 1a** | Comparator Matrix (Part 1: Comparators 1–4) | *Frozen in Phase S1* | Fully populated; literature review anchor. |
| **Table 1b** | Comparator Matrix (Part 2: Comparators 5–8 + RAG2ATTCK) | *Frozen in Phase S1* | Fully populated; literature review anchor. |
| **Table 2a** | Primary Attribution Performance Across Experimental Conditions | `outputs/canonical_evaluation/per_condition_metrics.json`<br>`outputs/canonical_analysis/rq_analysis.json` | `/conditions/{c}/accuracy_end_to_end`<br>`/conditions/{c}/accuracy_valid_outputs`<br>`/conditions/{c}/macro_f1`<br>`.rq1.mapped_single_accuracy`, `.rq1.mapped_multi_accuracy` |
| **Table 2b** | Attribution Diagnostic Metrics Across Experimental Conditions | `outputs/canonical_evaluation/per_condition_metrics.json`<br>`outputs/canonical_evaluation/failure_decomposition.json` | `/conditions/{c}/completed_record_count`<br>`/conditions/{c}/parse_failure_count`<br>`/conditions/{c}/invalid_id_count`<br>`/conditions/{c}/invalid_id_rate` (native denominator) |
| **Table 3** | Representation Stratification: Single vs. Contextual Views | `outputs/canonical_analysis/rq_analysis.json` | `.rq1.representation_stratification`<br>`.rq1.pairwise_comparison` |
| **Table 4** | Decoupled Failure Decomposition Matrix | `outputs/canonical_evaluation/failure_decomposition.json`<br>`outputs/canonical_evaluation/retrieval_conditional_metrics.json` | `/by_condition/{c}`<br>`retrieval_miss_count`, `valid_but_wrong_classification_count`<br>`retrieval_failure_correct_count`, overlap tracking |
| **Table 5** | Resource Consumption and Latency Scaling Across Depths | `outputs/canonical_analysis/rq_analysis.json` | `.rq3.by_condition[{c}]`<br>`.rq3.tradeoffs_by_condition` |
| **Table 6** | Cryptographic Reproducibility Manifest | File System Checksums (`hashlib.sha256`) | 12 baseline hashes preserved intact;<br>runtime prediction & ledger hashes in dedicated supplementary section |

---

### 2.2 Granular Table Population Rules

#### A. Table 2a: Primary Attribution Performance Across Conditions
- **Target Section:** Section 6.1 (RQ1: Retrieval-Augmented Attribution Efficacy)
- **Target Rows:** 5 experimental conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`)
- **Source Artifacts:** `outputs/canonical_evaluation/per_condition_metrics.json` (canonical evaluator) and `outputs/canonical_analysis/rq_analysis.json` (Specialist B analysis deliverable)
- **Field Mappings:**
  1. `Scorable Views ($N$)`: Fixed integer `718` across all rows (Protocol Decisions D2b & D2c: 678 single-GT + 40 multi-GT mapped positive views).
  2. `Headline Accuracy ($\text{Acc}_{\text{e2e}}$)`: Extracted from canonical pointer `/conditions/{c}/accuracy_end_to_end`. Formatted as `XX.XX%` (e.g., `42.34%`).
  3. `Valid Output Accuracy ($\text{Acc}_{\text{valid}}$)`: Extracted from canonical pointer `/conditions/{c}/accuracy_valid_outputs`. Formatted as `XX.XX%`.
  4. `474-Class Macro-F1`: Extracted from canonical pointer `/conditions/{c}/macro_f1`. Formatted as `XX.XX%` (or decimal `0.XXXX`).
  5. `Mapped-Single Acc ($N=678$)`: Extracted from Specialist B's `outputs/canonical_analysis/rq_analysis.json` under `.rq1.by_condition[c].mapped_single_accuracy`. Formatted as `XX.XX%`.
  6. `Mapped-Multi Acc ($N=40$)`: Extracted from Specialist B's `outputs/canonical_analysis/rq_analysis.json` under `.rq1.by_condition[c].mapped_multi_accuracy`. Formatted as `XX.XX%`.
- **Units & Formatting:** Metric percentages `XX.XX%`; sample counts integer $N$.
- **Methodological Invariants & The Three Distinct Denominators:**
  - **Denominator 1: Fixed Positive Scorable Views ($N=718$):** The authoritative denominator for condition headline accuracy ($\text{Acc}_{\text{e2e}} = \text{correct\_count} / 718$). Comprises 678 single-GT and 40 multi-GT mapped positive views across the 1,280 TEST views.
  - **Denominator 2: Logical Completed Records ($N=1,280$ per condition):** All 1,280 samples dispatched per condition. Terminal completed attempts (`completed_record_count`) count all records with terminal parse status $\in \{\text{VALID}, \text{INVALID\_ID}, \text{MALFORMED\_RESPONSE}\}$. Provider failures and parse failures natively divide by `logical_sample_count` ($1,280$).
  - **Denominator 3: Active Windows Taxonomy Universe ($N=474$ classes):** Every technique class in the frozen 474-class universe is evaluated. Unobserved classes (Case A: support=0, pred=0; Case B: support>0, pred=0; Case C: support=0, pred>0) contribute exactly 0.0 to the numerator sum (`f1_sum += 0.0`), dividing by 474.
  - **Vetted Offline Producer Invariant:** Breakdown accuracies and Macro-F1 metrics for single-GT ($N=678$) and multi-GT ($N=40$) subsets do NOT exist as native fields in frozen `per_condition_metrics.json`. They must be computed and provided by Specialist B's vetted offline analysis deliverable (`outputs/canonical_analysis/rq_analysis.json` branch `rq1`) or a dedicated vetted offline producer script (`scripts/reproduce_study.py`) evaluated over the scorable view subsets.
  - Multi-label correctness is governed by `ANY_MATCH` ($I_{\text{correct}} = 1$ if predicted ID $\in Y_{\text{GT}}$).
  - Headline accuracy incorporates provider and parse failures in the denominator.

#### B. Table 2b: Attribution Diagnostic Metrics Across Conditions
- **Target Section:** Section 6.1 (Diagnostic Sub-table)
- **Target Rows:** 5 experimental conditions
- **Source Artifacts:** `outputs/canonical_evaluation/per_condition_metrics.json` and `outputs/canonical_evaluation/failure_decomposition.json`
- **Field Mappings:**
  1. `Completed Records`: Extracted from canonical pointer `/conditions/{c}/completed_record_count` (terminal completed requests out of the 1,280 logical samples where parse status $\in \{\text{VALID}, \text{INVALID\_ID}, \text{MALFORMED\_RESPONSE}\}$, including genuine parse failures and invalid IDs). This is NOT `718 minus failures`.
  2. `Parse Failures`: Extracted from canonical pointer `/conditions/{c}/parse_failure_count` (native rate `parse_failure_rate`, dividing by `logical_sample_count` = 1,280).
  3. `Invalid ATT&CK IDs`: Extracted from canonical pointer `/conditions/{c}/invalid_id_count`.
  4. `Invalid ID Rate (%)`: Extracted directly from native canonical pointer `/conditions/{c}/invalid_id_rate` (which natively divides `invalid_id_count` by `completed_record_count`), formatted as `XX.XX%`.
- **Units & Formatting:** Integer counts and percentage rates `XX.XX%`.
- **Native Denominator Preservation Invariant:**
  - Invalid-ID rate, provider failure rate, and parse failure rate use their native exported denominators (`completed_record_count` or `logical_sample_count`); population scripts must preserve native exported rates and denominators without recalculating everything over 718.
  - Strictly distinguishes `INVALID_ID` (syntactically valid JSON where predicted ID fails canonical regex or active registry lookup) from `MALFORMED_RESPONSE` (structural JSON decode failure or missing `technique_id` key).

#### C. Table 3: Representation Stratification: Single-Event vs. Contextual-Event Views
- **Target Section:** Section 6.1 (Telemetry Representation Analysis)
- **Target Rows:** 5 experimental conditions
- **Source Artifact:** `outputs/canonical_analysis/rq_analysis.json` (Specialist B analysis deliverable, branch `rq1.representation_stratification` and `rq1.pairwise_comparison`)
- **Field Mappings:**
  1. `Single-Event $\text{Acc}_{\text{e2e}}$ ($N=278$)`: Single view subset headline accuracy (`rq1.representation_stratification.by_condition[c].single_event.accuracy`).
  2. `Contextual-Event $\text{Acc}_{\text{e2e}}$ ($N=440$)`: Contextual view subset headline accuracy (`rq1.representation_stratification.by_condition[c].contextual_event.accuracy`).
  3. `Single Macro-F1`: Macro-F1 over single views (`rq1.representation_stratification.by_condition[c].single_event.macro_f1`).
  4. `Contextual Macro-F1`: Macro-F1 over contextual views (`rq1.representation_stratification.by_condition[c].contextual_event.macro_f1`).
  5. `$\Delta \text{Acc}$ (Context - Single)`: Computed difference in percentage points (`contextual_event.accuracy - single_event.accuracy`). Formatted with explicit sign: `+X.XX pp` or `-X.XX pp`.
- **Units & Formatting:** Percentages `XX.XX%`; difference in percentage points `pp`.
- **Complete Scorable Pairs Census & Methodological Invariants:**
  - Evaluated on the authoritative join across the 640 total TEST scenario pairs (1,280 views):
    * **278 Complete Scorable Pairs:** Exactly 278 scenario pairs where *both* single-event and contextual-event views are mapped ($278 \times 2 = 556$ views).
    * **162 Contextual-Only Mapped Pairs:** Exactly 162 scenario pairs where *only* the contextual-event view is mapped (the single-event view is unmapped or ambiguous, $162 \times 1 = 162$ views).
    * **200 Unmapped Pairs:** Exactly 200 scenario pairs where *neither* view is mapped ($200 \times 2 = 400$ views; excluded per D2b/D2c).
    * **Reconciliation to 718 Mapped Positive Views:** $556 + 162 = 718$ total mapped positive views (278 single views + 440 contextual views; $278 + 162 = 440$).
  - **Pairwise Comparison Scope:** The pairwise representation comparison in `rq_analysis.json` (`rq1.pairwise_comparison`: win/loss/equal rates) evaluates strictly over the **278 complete scorable pairs** where both representations possess verified ground truth, eliminating confounding from asymmetric unmapped views.
  - **Vetted Offline Producer Invariant:** Single vs. contextual subset macro-F1 and accuracy metrics are computed by Specialist B's offline analysis deliverable (`rq_analysis.json`) rather than claimed to be native fields in `per_condition_metrics.json`.
  - Stratification evaluates whether multi-event background context aids or impairs LLM reasoning.

#### D. Table 4: Decoupled Failure Decomposition Matrix
- **Target Section:** Section 6.2 (RQ2: Retrieval Quality and Failure Decomposition)
- **Target Rows:** 5 experimental conditions
- **Source Artifacts:** `outputs/canonical_evaluation/failure_decomposition.json` and `outputs/canonical_evaluation/retrieval_conditional_metrics.json` (and `outputs/canonical_analysis/rq_analysis.json` branch `rq2`)
- **Field Mappings:**
  1. `Total Errors`: Computed as `718 - correct_count`.
  2. `Upstream Retrieval Miss ($GT \notin \text{Top-}k$)`: Extracted from `/by_condition/{c}/retrieval_miss_count`. Value is `N/A` for `no_rag`.
  3. `Downstream Selection Failure ($GT \in \text{Top-}k \land \text{Wrong}$)`: Count of scorable views where $\text{Top-}k \cap Y_{\text{GT}} \neq \emptyset$, but the model emitted an incorrect prediction.
  4. `Correct Attribution Despite GT Absent from Top-k ($GT \notin \text{Top-}k \land \text{Correct}$)`: Extracted from `retrieval_conditional_metrics.json` via `/by_condition/{c}/retrieval_failure_correct_count`.
     * Description: Count of scorable views where Top-k retrieval misses the ground truth ($GT \notin \text{Top-}k$), yet the LLM still outputs a correct ground-truth technique. This phenomenon is reported neutrally as non-retrieved correct attribution; it acknowledges potential partial contextual clues or telemetry artifacts in the prompt alongside pre-training memory, without asserting internal reasoning mechanisms or claiming exclusive causal attribution to parametric knowledge alone.
  5. `Invalid ATT&CK ID`: Extracted from `/by_condition/{c}/invalid_attack_id_count`.
  6. `Parse Failure`: Extracted from `/by_condition/{c}/parse_failure_count`.
  7. `Provider / Timeout Failure`: Extracted from `/by_condition/{c}/provider_failure_count`.
- **Units & Formatting:** Integer counts.
- **Methodological Invariants & Non-Exclusivity:**
  - Evaluated along independent diagnostic axes per Protocol Decision D2i without artificial forced mutual exclusivity.
  - Specifically, in `src/evaluation/experiment_metrics.py:compute_failure_decomposition`, upstream retrieval misses and downstream wrong classifications can overlap and are explicitly tracked via `overlap_retrieval_miss_and_wrong_classification`.

#### E. Table 5: Resource Consumption and Latency Scaling Across Retrieval Depths
- **Target Section:** Section 6.3 (RQ3: Retrieval Depth, API Cost, and Latency Trade-Offs)
- **Target Rows:** 5 experimental conditions
- **Source Artifact:** `outputs/canonical_analysis/rq_analysis.json` (Specialist B analysis deliverable, branch `rq3` and `rq3.tradeoffs_by_condition`, derived from `study_ledger.json` settlements and execution records)
- **Field Mappings:**
  1. `Total Input Tokens`: Sum of prompt input tokens across all 1,280 samples in condition (`rq3.by_condition[c].total_input_tokens`).
  2. `Total Output Tokens`: Sum of completion and reasoning tokens (`rq3.by_condition[c].total_output_tokens`).
  3. `Mean Output Tokens / Req`: Average output tokens per request (`rq3.by_condition[c].mean_output_tokens`, formatted as `XXX.X`).
  4. `Mean Latency (s)`: Mean wall-clock latency (`rq3.by_condition[c].mean_latency_seconds`, formatted as `X.XXs`).
  5. `Median Latency (s)`: Median latency (`rq3.by_condition[c].median_latency_seconds`, formatted as `X.XXs`).
  6. `P95 Latency (s)`: 95th percentile latency (`rq3.by_condition[c].p95_latency_seconds`, formatted as `X.XXs`).
  7. `Total Cost (USD)`: Total settled condition cost formatted as `USD XX.XX` (e.g., `USD 1.84`).
  8. `Mean Cost / Query (USD)`: Average cost per query formatted as `USD X.XXXX` (e.g., `USD 0.0014`).
- **Units & Formatting:** Token counts integer; latency seconds `X.XXs`; cost formatted as plain text `USD XX.XX` (strictly zero raw `$` to protect LaTeX math parsers).
- **Tariff Parameters & Monetary Invariants:**
  - Standard evaluated tariff rates: **USD 0.150 per 1,000,000 input tokens** and **USD 0.600 per 1,000,000 output tokens** (inclusive of hidden reasoning tokens).
  - Study budget ceiling: **USD 19.99** (`total_study_budget_usd`).
  - Prior pilot provisional hold: **USD 0.05264010** (`prior_pilot_hold_usd`).
  - Net starting available balance: **USD 19.93735990** (`net_available_starting_budget_usd`).
  - Token counts extracted from authoritative Responses API `usage` headers.

#### F. Table 6: Cryptographic Reproducibility Manifest
- **Target Section:** Section 8.2 (Cryptographic Reproducibility Inventory)
- **Source:** Direct cryptographic hashing (`hashlib.sha256()`) of disk assets
- **Baseline Preservation Invariant:** All 12 baseline asset hashes verified and frozen in Phase S1 are retained completely intact in their original table section.
- **Dedicated Supplementary Provenance Section:**
  - In Phase S2, canonical runtime execution and evaluation artifacts are appended into a distinct, dedicated supplementary provenance section (or sub-table), NOT modifying or replacing the 12 original baseline hashes:
    * `outputs/canonical_runs/predictions_no_rag.jsonl`: File SHA-256
    * `outputs/canonical_runs/predictions_rag_k1.jsonl`: File SHA-256
    * `outputs/canonical_runs/predictions_rag_k3.jsonl`: File SHA-256
    * `outputs/canonical_runs/predictions_rag_k5.jsonl`: File SHA-256
    * `outputs/canonical_runs/predictions_rag_k10.jsonl`: File SHA-256
    * `outputs/canonical_runs/study_ledger.json`: File SHA-256
    * `outputs/canonical_evaluation/run_provenance.json`: File SHA-256
    * `outputs/canonical_analysis/rq_analysis.json`: File SHA-256

---

### 2.3 Scientific Figures Specification (Figures 1–4)

To elevate the scientific report to publication standards, four figures will be generated by `scripts/reproduce_study.py` and embedded into `docs/report/scientific_report.md` and the compiled DOCX:

```
+----------------------------------------------------------------------------------------------------+
| FIGURE SPECIFICATIONS (docs/report/figures/)                                                       |
+----------------------------------------------------------------------------------------------------+
| Figure 1: fig1_attribution_scaling.png                                                             |
|   - Type: Multi-line plot with shaded 95% bootstrap confidence bands                               |
|   - X-axis: Retrieval Depth k (0=No-RAG, 1, 3, 5, 10)                                              |
|   - Y-axis: Metric Score (%) [Dual lines: Headline Acc_e2e and Macro-F1]                           |
|   - Caption: Headline Attribution Accuracy and 474-Class Macro-F1 as a function of retriever depth.|
+----------------------------------------------------------------------------------------------------+
| Figure 2: fig2_failure_decomposition.png                                                           |
|   - Type: Grouped multi-panel bar chart with explicit empirical overlap view                       |
|   - Categories: Upstream Miss, Downstream Selection Error, Invalid ATT&CK ID, Provider/Parse Err, |
|     and Overlap (Upstream Miss & Wrong Classification)                                              |
|   - Rationale: Protocol Decision D2i specifies non-exclusive failure axes; axes CAN OVERLAP.       |
|     No artificial 100% partition is imposed; independent failure rates and overlap are plotted.    |
|   - Caption: Decoupled Non-Exclusive Failure Axes and Empirical Overlap Across Conditions.         |
+----------------------------------------------------------------------------------------------------+
| Figure 3: fig3_representation_disparity.png                                                        |
|   - Type: Paired grouped bar chart with delta indicators                                           |
|   - Groups: 5 conditions; Bars: Single-Event Views (N=278) vs Contextual-Event Views (N=440)       |
|   - Caption: Telemetry Representation Attribution Disparity (Single-Event vs. Contextual-Event).   |
+----------------------------------------------------------------------------------------------------+
| Figure 4: fig4_cost_latency_pareto.png                                                             |
|   - Type: Pareto frontier scatter plot                                                             |
|   - X-axis: Mean Latency (seconds); Y-axis: Headline Accuracy (%); Bubble size: Total Cost (USD)   |
|   - Caption: Attribution Efficacy vs. Operational Latency and Cost Pareto Frontier.                |
+----------------------------------------------------------------------------------------------------+
```

- **Styling Rules for Figures:**
  - Format: High-resolution PNG (300 DPI), RGB color space.
  - Aspect Ratio: 16:9 or 3:2, max width 6.0 inches (to fit within 6.50in portrait page margins).
  - Fonts: Georgia or DejaVu Serif matching report typography; minimum font size 9pt.
  - Palette: Colorblind-safe palette (e.g., Seaborn `colorblind` or Okabe-Ito).

---

### 2.4 Text Narrative Placeholders Mapping

| Document Section | Target Narrative Subsection | Artifact Key / Statistical Analysis Required |
| :--- | :--- | :--- |
| **Abstract** | Quantitative Summary (Lines ~21) | Objective quantitative summary across all 5 experimental conditions. Headline $\text{Acc}_{\text{e2e}}$ deltas across conditions (reported with signed percentage points: $+X.XX\text{ pp}$ or $-X.XX\text{ pp}$, avoiding presumption that $k=10$ is optimal or saturating; comparative analyses are exploratory). Macro-F1 deltas, ratio of upstream retrieval misses to downstream selection errors, and settled budget spend under USD 19.99 ceiling. |
| **Section 6.1** | RQ1 Headline Findings Narrative | Condition-by-condition comparisons: McNemar's test $p$-value and paired bootstrap confidence intervals comparing `no_rag` against each RAG depth; report all conditions neutrally and objectively without assuming monotonic improvement (recognizing flat, positive, or negative regimes); mapped-single vs mapped-multi attribution fidelity from Specialist B's `rq_analysis.json` (`rq1`). |
| **Section 6.2** | RQ2 Failure Decomposition Narrative | Quantification of failure axes: upstream retrieval misses ($GT \notin \text{Top-}k$) vs downstream selection errors ($GT \in \text{Top-}k \land \text{Wrong}$); empirical overlap (`overlap_retrieval_miss_and_wrong_classification`); frequency of non-retrieved correct attribution (correct despite GT absent from Top-k, acknowledged neutrally as potential partial prompt clues alongside parametric memory, without asserting internal reasoning mechanisms or causal claims); empirical verdict on the Contextual Dilution Hypothesis. |
| **Section 6.3** | RQ3 Operational Trade-Offs Narrative | Latency inflation analysis: percentage change in mean and P95 latency from No-RAG across RAG depths. Cost scaling under tariff (USD 0.150/1M in, USD 0.600/1M out); cost efficiency (accuracy delta per token/dollar). Identification of operational Pareto trade-offs from Specialist B's `rq_analysis.json` (`rq3` and `rq3.tradeoffs_by_condition`). |
| **Section 7** | Discussion & Practical SOC Deployment | Practical architectural recommendations for SOC log pipelines: triage heuristic filtering, dense pre-filtering, and selective LLM escalation based on empirical Pareto efficiency. |

---

## 3. Invariants and Quality Assurance Protocol

### 3.1 Strict Units of Measurement and Assumptions

To guarantee clarity and eliminate ambiguity across all audiences, every metric must adhere to uniform units:

| Dimension | Standard Unit | Formatting String | Example | Forbidden Formats |
| :--- | :--- | :--- | :--- | :--- |
| **Financial / Currency** | United States Dollar (USD) | `USD XX.XX` or `USD X.XXXX` | `USD 19.99`, `USD 0.0242` | `$19.99`, `$\$19.99$` (triggers LaTeX math error) |
| **Attribution Accuracy** | Percentage (%) | `XX.XX%` | `45.11%`, `92.45%` | `0.4511` (in tables), `45%` (unrounded) |
| **Macro-Averaged F1** | Percentage or Decimal | `XX.XX%` (or `0.XXXX`) | `43.14%` or `0.4314` | Inconsistent precision across rows |
| **Inference Latency** | Seconds (s) | `X.XXs` | `8.13s`, `14.20s` | Milliseconds without unit, raw floats |
| **Token Counts** | Integer Count | Comma-separated | `42,213`, `15,766,654` | `42k`, exponential notation `4.2e4` |
| **Performance Delta** | Percentage Points (pp) | `+X.XX pp` / `-X.XX pp` | `+5.30 pp`, `-2.15 pp` | `%` when describing difference of percentages |

---

### 3.2 Automated Verification Protocol (`scripts/verify_report_metadata.py`)

Prior to publication sign-off, the automated verification script `scripts/verify_report_metadata.py` must be executed under the offline guard harness. It enforces five mandatory verification stages:

1. **Stage 1 (Cryptographic Table 6 Check):**
   - Hashes all physical files referenced in Table 6 directly from disk using SHA-256.
   - Verifies that every cited file digest matches disk bytes with zero mismatch.
2. **Stage 2 (DOCX Table 6 Manifest Check):**
   - Parses `docs/report/scientific_report.docx` via `python-docx`.
   - Extracts Table 6 rows and confirms that compiled DOCX hashes exactly match markdown and disk.
3. **Stage 3 (Evaluator Invariants & Zero-Denominator Proofs):**
   - Validates Protocol Decision D2j (`NULL` convention) across all three zero-denominator boundary cases:
     * *Case A (Unobserved Class: support=0, pred=0):* `precision=None, recall=None, f1=None`.
     * *Case B (Unpredicted Class: support>0, pred=0):* `precision=None, recall=0.0, f1=0.0`.
     * *Case C (Unobserved False Positive: support=0, pred>0):* `precision=0.0, recall=None, f1=0.0`.
   - Confirms that all three cases contribute exactly 0.0 to condition Macro-F1 numerator sum divided by 474.
4. **Stage 4 (Word Formatting Invariants):**
   - Title paragraph check: Run font color is pure black `RGBColor(0, 0, 0)`; paragraph XML contains zero `<w:pBdr>` border tags.
   - References check: Exactly 13 reference paragraphs statically numbered `[1]`..`[13]`; style is NOT Word's continuous `List Number`.
   - Table width check: All 8 tables have total column width $\le 6.50$ inches in portrait orientation.
5. **Stage 5 (STIX v19.2 Raw Census Invariants):**
   - Validates census numbers directly against `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`: exactly 858 attack-patterns, 149 revoked, 12 deprecated, 161 unique inactive (0 overlap), 697 active enterprise, and 474 active Windows (176 root, 298 sub-techniques).
   - Confirms that Section 3.1 report text matches these numbers.

---

### 3.3 Word Document (.docx) Formatting Invariants

The compiled Microsoft Word document must strictly adhere to the layout specifications verified in Phase S1:
1. **Margins & Orientation:** Standard portrait orientation (8.5 $\times$ 11 inches) with 1.0-inch margins on all sides. Printable width is exactly 6.50 inches.
2. **Typographic Hierarchy:**
   - Title: Georgia 24pt Bold, pure black (`#000000`), 12pt space after, zero border.
   - Heading 1: Georgia 16pt Bold, primary accent (`#092C4C`), 12pt space before, 6pt space after, keep-with-next enabled.
   - Heading 2: Georgia 13pt Bold, secondary accent (`#1F4E79`), 10pt space before, 4pt space after, keep-with-next enabled.
   - Heading 3: Georgia 11pt Bold, body accent (`#24292F`), 6pt space before, 2pt space after.
   - Body Text: Calibri 10.5pt, regular, 1.15 line spacing, 4pt space after.
   - Code Blocks: Consolas 9pt, 1.0 line spacing, shaded box (`#F6F8FA`) with thin gray border.
3. **Professional Table Pagination Rules:**
   - Every table row must have `<w:cantSplit/>` to prevent ugly page-boundary mid-row splits.
   - Every table header row (row 0) must have `<w:tblHeader/>` to repeat headers when tables cross pages.
   - Table widths must be explicitly computed and constrained: total width $\le 6.50$ inches.
4. **References Formatting:**
   - References must be statically numbered strings `[1]` through `[13]`.
   - Must use standard Paragraph style with hanging indent (0.35 inches), avoiding Word's dynamic `List Number` style to prevent global numbering bleed.

---

### 3.4 Native Word COM Export, Offline QA Backend, and Visual Inspection Procedure

To ensure 100% fidelity before publication delivery, the following automated procedure will be executed on the Windows workstation:

```powershell
# 1. Compile DOCX from populated Markdown
uv run python scripts/export_report_docx.py

# 2. Render and Export via Native Microsoft Word COM Automation
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$docPath = (Resolve-Path "docs/report/scientific_report.docx").Path
$pdfPath = [System.IO.Path]::ChangeExtension($docPath, ".pdf")
$doc = $word.Documents.Open($docPath)
$doc.SaveAs([ref]$pdfPath, [ref]17) # 17 = wdFormatPDF
$doc.Close([ref]$false)
$word.Quit()

# 3. Rasterize PDF Pages to PNG for Visual Inspection
uv run python -c "
import pypdfium2 as pdfium
from pathlib import Path
pdf_path = Path('docs/report/scientific_report.pdf')
out_dir = Path('reports/evidence/pdf_inspection')
out_dir.mkdir(parents=True, exist_ok=True)
pdf = pdfium.PdfDocument(pdf_path)
for i, page in enumerate(pdf):
    image = page.render(scale=2.0).to_pil()
    image.save(out_dir / f'page_{i+1:02d}.png')
print(f'Rasterized {len(pdf)} pages to {out_dir}')
"
```

> [!IMPORTANT]
> **Offline QA Backend & COM Independence:** Windows Microsoft Word COM automation (`New-Object -ComObject Word.Application`) is host-dependent and is NOT guaranteed to be socket-proof under strict offline-guard harnesses. Therefore, an independent, offline QA backend (`scripts/verify_report_metadata.py` using `python-docx`, combined with offline headless PDF rasterization via `pypdfium2` and programmatic metadata assertions) serves as the authoritative, socket-proof verification gate (`OFFLINE_GUARD: attempted_egress=0`). Full visual QA inspection across all pages with zero remaining placeholders (`[TBD_AT_EXECUTION]`) is mandatory prior to final Phase S2 delivery.

**Visual Inspection Checklist:**
- [ ] Page 1 Header: Title pure black, no border, author name, project name, date, and draft status cleanly aligned.
- [ ] Literature Review Tables: Table 1a and Table 1b fit within margins without column text squeezing.
- [ ] Results Tables: Tables 2a, 2b, 3, 4, and 5 display populated figures cleanly; column headers aligned; no overlapping text.
- [ ] Figures 1–4: Centered, clear 300 DPI resolution, readable axis labels, no clipping of legends.
- [ ] Table 6 (Manifest): All hashes legible and unclipped; baseline section and supplementary provenance section separated cleanly.
- [ ] References: Statically numbered [1]..[13], hanging indents aligned, no duplicate counters.
- [ ] Zero Remaining Placeholders: No `[TBD_AT_EXECUTION]` or unresolved tokens remain anywhere in the document.

---

## 4. Phase S2 Population Script Specifications

To ensure fully automated, reproducible population, two helper scripts are planned for construction during Phase S2. Both scripts will be developed and tested against fixture schemas under the strict offline socket guard harness (`attempted_egress=0`):

### 4.1 `scripts/reproduce_study.py` (Figure & Metric Engine)
- **Status:** New planned file to be implemented in Phase S2.
- **Inputs:** `outputs/canonical_evaluation/` (6 native files), `outputs/canonical_analysis/rq_analysis.json` (Specialist B), and `outputs/canonical_runs/`.
- **Outputs:**
  - `docs/report/figures/fig1_attribution_scaling.png`
  - `docs/report/figures/fig2_failure_decomposition.png`
  - `docs/report/figures/fig3_representation_disparity.png`
  - `docs/report/figures/fig4_cost_latency_pareto.png`
- **Responsibilities & Safeguards:**
  - Loads canonical evaluation outputs and `rq_analysis.json`.
  - Computes bootstrap confidence intervals without making network calls.
  - Renders 300 DPI publication plots adhering to colorblind-safe palettes and serif typography.
  - Generates Figure 2 as independent non-mutually-exclusive failure axes with explicit empirical overlap view (`overlap_retrieval_miss_and_wrong_classification`).
  - Accompanied by unit tests validating behavior on null, missing, negative differences, and overlapping failure data.

### 4.2 `scripts/populate_report.py` (Scaffold Populator)
- **Status:** New planned file to be implemented in Phase S2.
- **Inputs:** `docs/report/scientific_report.md` (template scaffold), `outputs/canonical_evaluation/` (6 native files), and `outputs/canonical_analysis/rq_analysis.json`.
- **Outputs:** Updated `docs/report/scientific_report.md` with populated tables and narratives.
- **Responsibilities & Safeguards:**
  - Replaces all `[TBD_AT_EXECUTION]` table cell placeholders with exact formatted values matching the canonical pointers and format rules in Section 2.
  - Uses native denominators for all diagnostic rates (does not force rates over 718).
  - Injects statistical test results (McNemar's test, bootstrap intervals) into narrative paragraphs neutrally and objectively without assuming monotonic improvement or inferring internal reasoning mechanisms.
  - Appends canonical prediction file and ledger hashes to the dedicated supplementary section of Table 6, preserving the 12 original baseline hashes intact.
  - Automatically triggers `scripts/export_report_docx.py` and runs `scripts/verify_report_metadata.py` under the offline guard.
  - Tested with schema fixture unit tests covering empty, malformed, negative delta, and zero-denominator cases under D2j NULL.

---

## 5. Commit & Worktree State

- **Worktree:** `D:/RAG2ATTCK-worktrees/report-s1`
- **Branch:** `codex/s1-report-related-work` (PR #25)
- **PRE_SHA:** `b4bd35ffe1b947027c858835c477c0bdef9c8118`
- **Document Status:** `DRAFT — PENDING CODEX SUPERVISOR REVIEW`
- **Offline Guard Status:** Verified active (`attempted_egress=0`).
- **Plan File:** `reports/evidence/s2_report_population_plan.md`
