# Scientific Report Population Plan for Phase S2: Canonical Execution to Publication Delivery

**Task Handle:** Subagent C: Research Report & Publication Lead (Phase S2 Planning)  
**Assigned Worktree:** `D:/RAG2ATTCK-worktrees/report-s1`  
**Git Branch:** `codex/s1-report-related-work` (PR #25)  
**PRE_SHA:** `c0f7c9d1b607a8c24110ddc33f65a6d735b740a2`  
**Date:** October 2026  
**Document Status:** DRAFT — PENDING CODEX REVIEW  
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
|      * rq_analysis.json (unified analysis containing canonical branches:                           |
|        rq1/by_condition, rq2/by_condition, rq3/tradeoffs_by_condition,                             |
|        rq3/view_diagnostics, and new_proposed_producer_stratified_gt_complexity)                   |
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
> **Specialist B Analysis Contract Alignment:** Specialist B exports **a single unified analysis deliverable**: `outputs/canonical_analysis/rq_analysis.json`. Specialist B does *not* export multi-file splits (such as `pairwise_representation_comparison.json` or `resource_scaling.json`). All research question syntheses are structured under canonical top-level branches aligned 100% with `fixture_export_schema_b172.json`:
> - `/rq1/by_condition/{c}`: Core attribution metrics (`accuracy_end_to_end`, `accuracy_valid_outputs`, `macro_f1`).
> - `/rq2/by_condition/{c}`: Decoupled failure decomposition metrics and retrieval hit rates.
> - `/rq3/tradeoffs_by_condition/{c}`: Latency percentiles (`/latency_ms/{mean, median, p95, sum}`), token usage (`/tokens/{mean_prompt_tokens, mean_completion_tokens, mean_total_tokens, sum_prompt_tokens, sum_completion_tokens, sum_total_tokens}`), and settled financial accounting (`/financial_cost_usd/{total_cost_usd, cost_per_logical_request_usd, cost_per_scorable_query_usd, cost_per_correct_attribution_usd, marginal_cost_vs_baseline_usd}`).
> - `/rq3/view_diagnostics/{c}`: Full view stratification (`single_view_accuracy_e2e`, `contextual_view_accuracy_e2e`, `view_accuracy_delta`), subset macro-F1 (`single_view_macro_f1`, `contextual_view_macro_f1`, `view_macro_f1_delta`), paired complete metrics (`paired_complete_pairs_count`, `single_paired_accuracy`, `contextual_paired_accuracy`, `paired_delta`), pair concordance matrix (`/pair_concordance/*`), and exploratory McNemar tests (`/mcnemar_test_views_exploratory/*`).
> - `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}`: Ground-truth complexity stratification (`single_gt_accuracy_e2e`, `multi_gt_accuracy_e2e`, `complexity_accuracy_delta`, sample counts, and 474-universe Macro-F1).
> Any specialized subset metrics enforce strict **fail-closed** validation (fatal execution error if missing, NEVER defaulting to `0` or `0.0`).

---

## 2. Placeholders-to-Artifact Mapping Specification

Every placeholder in `docs/report/scientific_report.md` and `docs/report/scientific_report.docx` maps directly and bijectively to a canonical evaluation artifact.

### 2.1 Table Mapping Overview

| Report Table | Table Title | Primary Source Artifact | Output JSON Key / Sub-path |
| :--- | :--- | :--- | :--- |
| **Table 1a** | Comparator Matrix (Part 1: Comparators 1–4) | *Frozen in Phase S1* | Fully populated; literature review anchor. |
| **Table 1b** | Comparator Matrix (Part 2: Comparators 5–8 + RAG2ATTCK) | *Frozen in Phase S1* | Fully populated; literature review anchor. |
| **Table 2a** | Primary Attribution Performance & Ground-Truth Complexity Across Conditions | `outputs/canonical_evaluation/per_condition_metrics.json`<br>`outputs/canonical_analysis/rq_analysis.json` | `/conditions/{c}/accuracy_end_to_end`<br>`/conditions/{c}/accuracy_valid_outputs`<br>`/conditions/{c}/macro_f1`<br>`/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/single_gt_accuracy_e2e`<br>`/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/multi_gt_accuracy_e2e`<br>`/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/complexity_accuracy_delta` (fail-closed) |
| **Table 2b** | Attribution Diagnostic Metrics Across Experimental Conditions | `outputs/canonical_evaluation/per_condition_metrics.json`<br>`outputs/canonical_evaluation/failure_decomposition.json` | `/conditions/{c}/completed_record_count`<br>`/conditions/{c}/accuracy_valid_outputs`<br>`/conditions/{c}/invalid_id_count`<br>`/conditions/{c}/invalid_id_rate` (native denominator: completed_record_count)<br>`/conditions/{c}/provider_failure_rate` (native denominator: 1,280 dispatches)<br>`/conditions/{c}/parse_failure_count` |
| **Table 3** | View Stratification: Single vs. Contextual Views | `outputs/canonical_analysis/rq_analysis.json` | `/rq3/view_diagnostics/{c}/single_view_accuracy_e2e`<br>`/rq3/view_diagnostics/{c}/contextual_view_accuracy_e2e`<br>`/rq3/view_diagnostics/{c}/view_accuracy_delta`<br>`/rq3/view_diagnostics/{c}/single_view_macro_f1`<br>`/rq3/view_diagnostics/{c}/contextual_view_macro_f1`<br>`/rq3/view_diagnostics/{c}/paired_complete_pairs_count`<br>`/rq3/view_diagnostics/{c}/single_paired_accuracy`<br>`/rq3/view_diagnostics/{c}/contextual_paired_accuracy`<br>`/rq3/view_diagnostics/{c}/paired_delta`<br>`/rq3/view_diagnostics/{c}/pair_concordance/*`<br>`/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/*` (fail-closed) |
| **Table 4** | Decoupled Failure Decomposition Matrix | `outputs/canonical_evaluation/failure_decomposition.json`<br>`outputs/canonical_evaluation/retrieval_conditional_metrics.json` | `/conditions/{c}/retrieval_miss_count` (or `/by_condition/{c}/retrieval_miss_count`)<br>`/conditions/{c}/valid_but_wrong_classification_count`<br>`/conditions/{c}/retrieval_failure_correct_count`<br>`/by_condition/{c}/overlap_retrieval_miss_and_wrong_classification` |
| **Table 5** | Resource Consumption and Latency Scaling Across Depths | `outputs/canonical_analysis/rq_analysis.json` | `/rq3/tradeoffs_by_condition/{c}/latency_ms/{mean, median, p95, sum}`<br>`/rq3/tradeoffs_by_condition/{c}/tokens/{mean_prompt_tokens, mean_completion_tokens, mean_total_tokens, sum_prompt_tokens, sum_completion_tokens, sum_total_tokens}`<br>`/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/{total_cost_usd, cost_per_logical_request_usd, cost_per_scorable_query_usd, marginal_cost_vs_baseline_usd}` |
| **Table 6** | Cryptographic Reproducibility Manifest | File System Checksums (`hashlib.sha256`) | All baseline asset hashes preserved intact (protocol semantic digest, whole-file configuration digests, runtime wrapper code digest);<br>Dataset split manifest path: `data/ground_truth/synthetic/split_manifest.json` (strictly NOT `data/processed/...`);<br>runtime prediction & ledger hashes in dedicated supplementary provenance section |

---

### 2.2 Granular Table Population Rules

#### A. Table 2a: Primary Attribution Performance and Ground-Truth Complexity Across Conditions
- **Target Section:** Section 6.1 (RQ1: Retrieval-Augmented Attribution Efficacy)
- **Target Rows:** 5 experimental conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`)
- **Source Artifacts:** `outputs/canonical_evaluation/per_condition_metrics.json` (canonical evaluator: `/conditions/{c}/...`), `outputs/canonical_analysis/rq_analysis.json` (Specialist B attribution branch: `/rq1/by_condition/{c}/`), and `outputs/canonical_analysis/rq_analysis.json` (`/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/`).
- **Field Mappings:**
  1. `Scorable Views ($N$)`: Fixed integer `718` across all rows (Protocol Decisions D2b & D2c: 678 single-GT + 40 multi-GT mapped positive views).
  2. `Headline Accuracy ($\text{Acc}_{\text{e2e}}$)`: Extracted from canonical pointer `/conditions/{c}/accuracy_end_to_end` (or Specialist B `/rq1/by_condition/{c}/accuracy_end_to_end`). Formatted as `XX.XX%` (e.g., `42.34%`).
  3. `Valid Output Accuracy ($\text{Acc}_{\text{valid}}$)`: Extracted from canonical pointer `/conditions/{c}/accuracy_valid_outputs` (or Specialist B `/rq1/by_condition/{c}/accuracy_valid_outputs`). Formatted as `XX.XX%`.
  4. `474-Class Macro-F1`: Extracted from canonical pointer `/conditions/{c}/macro_f1` (or Specialist B `/rq1/by_condition/{c}/macro_f1`). Formatted as `XX.XX%` (or decimal `0.XXXX`).
  5. `Single-GT Acc ($N=678$)`: Extracted from canonical leaf pointer `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/single_gt_accuracy_e2e`. Formatted as `XX.XX%`. (Sample count verified via `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/single_gt_sample_count`). Enforces **fail-closed** schema validation (halts with error if missing; NEVER defaults to `0` or `0.0`).
  6. `Multi-GT Acc ($N=40$)`: Extracted from canonical leaf pointer `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/multi_gt_accuracy_e2e`. Formatted as `XX.XX%`. (Sample count verified via `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/multi_gt_sample_count`). Enforces **fail-closed** schema validation (halts with error if missing; NEVER defaults to `0` or `0.0`).
  7. `Complexity Accuracy Delta`: Extracted from canonical leaf pointer `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/complexity_accuracy_delta`. Formatted with explicit sign: `+X.XX pp` or `-X.XX pp`.
- **Units & Formatting:** Metric percentages `XX.XX%`; sample counts integer $N$.
- **Methodological Invariants & The Three Distinct Denominators:**
  - **Denominator 1: Fixed Positive Scorable Views ($N=718$):** The authoritative denominator for condition headline accuracy ($\text{Acc}_{\text{e2e}} = \text{correct\_count} / 718$). Comprises 678 single-GT and 40 multi-GT mapped positive views across the 1,280 TEST views.
  - **Denominator 2: Logical Completed Records ($N=1,280$ per condition):** All 1,280 samples dispatched per condition. Terminal completed attempts (`completed_record_count`) count all records with terminal parse status $\in \{\text{VALID}, \text{INVALID\_ID}, \text{MALFORMED\_RESPONSE}\}$. Provider failures and parse failures natively divide by `logical_sample_count` ($1,280$).
  - **Denominator 3: Active Windows Taxonomy Universe ($N=474$ classes):** Every technique class in the frozen 474-class universe is evaluated under Protocol Decision D2j (`NULL` convention). Unobserved classes (Case A: support=0, pred=0; `precision=None, recall=None, f1=None`), unpredicted classes (Case B: support>0, pred=0; `precision=None, recall=0.0, f1=0.0`), and unobserved false positive classes (Case C: support=0, pred>0; `precision=0.0, recall=None, f1=0.0`) are precisely distinguished and contribute exactly 0.0 to the Macro-F1 numerator sum (`f1_sum += 0.0`), dividing by 474.
  - **Vetted Offline Producer & Fail-Closed Invariant:** Breakdown accuracies and complexity deltas for single-GT ($N=678$) and multi-GT ($N=40$) subsets trace 100% to `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/` in `outputs/canonical_analysis/rq_analysis.json` (as exported by Specialist B's `evaluate_rqs.py` / `fixture_export_schema_b172.json`). Population and verification scripts must NEVER invent custom keys (such as `mapped_single_accuracy` or `mapped_multi_accuracy`) and must enforce strict **fail-closed** validation: if these fields are absent or unresolved, the pipeline must halt immediately with an explicit schema error; it must NEVER default to `0` or `0.0`.
  - Multi-label correctness is governed by `ANY_MATCH` ($I_{\text{correct}} = 1$ if predicted ID $\in Y_{\text{GT}}$).
  - Headline accuracy incorporates provider and parse failures in the denominator.

#### B. Table 2b: Attribution Diagnostic Metrics Across Conditions
- **Target Section:** Section 6.1 (Diagnostic Sub-table)
- **Target Rows:** 5 experimental conditions
- **Source Artifacts:** `outputs/canonical_evaluation/per_condition_metrics.json` and `outputs/canonical_evaluation/failure_decomposition.json`
- **Field Mappings:**
  1. `Completed Records`: Extracted from canonical pointer `/conditions/{c}/completed_record_count` (narrow native definition: terminal completed requests out of the 1,280 logical samples where parse status $\in \{\text{VALID}, \text{INVALID\_ID}, \text{MALFORMED\_RESPONSE}\}$, including genuine parse failures and invalid IDs). This is NOT `718 minus failures`.
  2. `Valid Outputs Accuracy`: Extracted from canonical pointer `/conditions/{c}/accuracy_valid_outputs` (native denominator is valid scorable count `valid_scorable_sample_count`), formatted as `XX.XX%`.
  3. `Invalid ATT&CK ID Count`: Extracted from canonical pointer `/conditions/{c}/invalid_id_count`.
  4. `Invalid ID Rate (%)`: Extracted directly from native canonical pointer `/conditions/{c}/invalid_id_rate` (which natively divides `invalid_id_count` by `completed_record_count`; NOT `invalid_technique_id_rate`), formatted as `XX.XX%`.
  5. `Provider Failure Rate (%)`: Extracted from canonical pointer `/conditions/{c}/provider_failure_rate` (natively dividing `provider_failure_count` by `logical_sample_count` = 1,280 dispatches), formatted as `XX.XX%`.
  6. `Parse Failure Count`: Extracted from canonical pointer `/conditions/{c}/parse_failure_count` (native rate `parse_failure_rate`, dividing by `logical_sample_count` = 1,280).
- **Units & Formatting:** Integer counts and percentage rates `XX.XX%`.
- **Native Denominator Preservation Invariant:**
  - Invalid-ID rate, provider failure rate, and parse failure rate use their native exported denominators (`completed_record_count` or `logical_sample_count`); population scripts must preserve native exported rates and denominators without recalculating everything over 718.
  - Strictly distinguishes `INVALID_ID` (syntactically valid JSON where predicted ID fails canonical regex or active registry lookup) from `MALFORMED_RESPONSE` (structural JSON decode failure or missing `technique_id` key).

#### C. Table 3: View Stratification: Single vs. Contextual Views
- **Target Section:** Section 6.1 (Telemetry Representation Analysis)
- **Target Rows:** 5 experimental conditions
- **Source Artifact:** `outputs/canonical_analysis/rq_analysis.json` (Specialist B analysis deliverable, canonical branch `/rq3/view_diagnostics/{c}/` aligned 100% with `fixture_export_schema_b172.json`)
- **Field Mappings:**
  1. `Single View Accuracy ($\text{Acc}_{\text{e2e}}$)` ($N=278$ scorable): Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/single_view_accuracy_e2e`. Formatted as `XX.XX%`.
  2. `Contextual View Accuracy ($\text{Acc}_{\text{e2e}}$)` ($N=440$ scorable): Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/contextual_view_accuracy_e2e`. Formatted as `XX.XX%`.
  3. `View Accuracy Delta`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/view_accuracy_delta`. Formatted with explicit sign: `+X.XX pp` or `-X.XX pp`.
  4. `Single View Macro-F1`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/single_view_macro_f1` (true view subset Macro-F1 evaluated directly over single-view records, NOT copied overall macro). Formatted as `XX.XX%` (or `0.XXXX`).
  5. `Contextual View Macro-F1`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/contextual_view_macro_f1` (true view subset Macro-F1 evaluated directly over contextual-view records). Formatted as `XX.XX%` (or `0.XXXX`).
  6. `Paired Complete Pairs Count ($N=278$)`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/paired_complete_pairs_count`.
  7. `Single Paired Accuracy`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/single_paired_accuracy`. Formatted as `XX.XX%`.
  8. `Contextual Paired Accuracy`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/contextual_paired_accuracy`. Formatted as `XX.XX%`.
  9. `Paired Delta`: Extracted from canonical leaf pointer `/rq3/view_diagnostics/{c}/paired_delta`. Formatted as `+X.XX pp` or `-X.XX pp`.
  10. `Pair Concordance Matrix`: Extracted from canonical leaf pointers:
      - `both_correct_count`: `/rq3/view_diagnostics/{c}/pair_concordance/both_correct_count`
      - `single_only_correct_count`: `/rq3/view_diagnostics/{c}/pair_concordance/single_only_correct_count`
      - `contextual_only_correct_count`: `/rq3/view_diagnostics/{c}/pair_concordance/contextual_only_correct_count`
      - `both_incorrect_count`: `/rq3/view_diagnostics/{c}/pair_concordance/both_incorrect_count`
  11. `Exploratory McNemar Test`: Extracted from canonical leaf pointers:
      - `treatment_win_b`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/contingency_table/treatment_win_b`
      - `baseline_win_c`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/contingency_table/baseline_win_c`
      - `chi2_statistic`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/chi2_statistic`
      - `p_value_asymptotic`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/p_value_asymptotic`
      - `p_value_exact`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/p_value_exact`
      - `significant_at_05`: `/rq3/view_diagnostics/{c}/mcnemar_test_views_exploratory/significant_at_05`
- **Units & Formatting:** Percentages `XX.XX%`; difference in percentage points `pp`.
- **Complete Scorable Pairs Census & Methodological Invariants:**
  - Evaluated on the authoritative join across the 640 total TEST scenario pairs (1,280 views):
    * **278 Complete Scorable Pairs:** Exactly 278 scenario pairs where *both* single-event and contextual-event views are mapped ($278 \times 2 = 556$ views).
    * **162 Contextual-Only Mapped Pairs:** Exactly 162 scenario pairs where *only* the contextual-event view is mapped (the single-event view is unmapped or ambiguous, $162 \times 1 = 162$ views).
    * **200 Unmapped Pairs:** Exactly 200 scenario pairs where *neither* view is mapped ($200 \times 2 = 400$ views; excluded per D2b/D2c).
    * **Reconciliation to 718 Mapped Positive Views:** $556 + 162 = 718$ total mapped positive views (278 single views + 440 contextual views; $278 + 162 = 440$).
  - **Pairwise Comparison Scope:** Pairwise representation comparisons (win/loss/equal rates across conditions) evaluate strictly over the **278 complete scorable pairs** where both representations possess verified ground truth, eliminating confounding from asymmetric unmapped views.
  - **Fail-Closed Validation Invariant:** All view diagnostic metrics trace 100% to `/rq3/view_diagnostics/{c}/` in `outputs/canonical_analysis/rq_analysis.json`. Population scripts must enforce strict **fail-closed** validation: if any of these fields are missing or unresolved, the script must halt immediately with an explicit schema error; it must NEVER default to `0` or `0.0`.
  - Stratification evaluates whether multi-event background context aids or impairs LLM reasoning.

#### D. Table 4: Decoupled Failure Decomposition Matrix
- **Target Section:** Section 6.2 (RQ2: Retrieval Quality and Failure Decomposition)
- **Target Rows:** 5 experimental conditions
- **Source Artifacts:** `outputs/canonical_evaluation/failure_decomposition.json` and `outputs/canonical_evaluation/retrieval_conditional_metrics.json` (and `outputs/canonical_evaluation/per_condition_metrics.json`)
- **Field Mappings:**
  1. `Total Errors`: Computed as `718 - correct_count`.
  2. `Upstream Retrieval Miss ($GT \notin \text{Top-}k$)`: Extracted from canonical pointer `/conditions/{c}/retrieval_miss_count` (in native `per_condition_metrics.json`) or `/by_condition/{c}/retrieval_miss_count` (in `failure_decomposition.json`). Value is `N/A` for `no_rag`.
  3. `Downstream Selection Failure ($GT \in \text{Top-}k \land \text{Wrong}$)`: Extracted from canonical pointer `/conditions/{c}/valid_but_wrong_classification_count` (or `/by_condition/{c}/valid_but_wrong_classification_count` in `failure_decomposition.json`).
  4. `Correct Attribution Despite GT Absent from Top-k ($GT \notin \text{Top-}k \land \text{Correct}$)`: Extracted from canonical pointer `/conditions/{c}/retrieval_failure_correct_count` (or `/by_condition/{c}/retrieval_failure_correct_count` in `retrieval_conditional_metrics.json`).
     * Description: Count of scorable views where Top-k retrieval misses the ground truth ($GT \notin \text{Top-}k$), yet the LLM still outputs a correct ground-truth technique. This phenomenon is reported neutrally as non-retrieved correct attribution; it acknowledges potential partial contextual clues or telemetry artifacts in the prompt alongside pre-training memory, without asserting internal reasoning mechanisms or claiming exclusive causal attribution to parametric knowledge alone.
  5. `Invalid ATT&CK ID`: Extracted from canonical pointer `/conditions/{c}/invalid_id_count` (or `/by_condition/{c}/invalid_attack_id_count`).
  6. `Parse Failure`: Extracted from canonical pointer `/conditions/{c}/parse_failure_count` (or `/by_condition/{c}/parse_failure_count`).
  7. `Provider / Timeout Failure`: Extracted from canonical pointer `/conditions/{c}/provider_failure_count` (or `/by_condition/{c}/provider_failure_count`).
  8. `Overlap Tracking`: Tracked via canonical pointer `/by_condition/{c}/overlap_retrieval_miss_and_wrong_classification`.
- **Units & Formatting:** Integer counts.
- **Methodological Invariants & Non-Exclusivity:**
  - Evaluated along independent diagnostic axes per Protocol Decision D2i without artificial forced mutual exclusivity.
  - Specifically, in `src/evaluation/experiment_metrics.py:compute_failure_decomposition`, upstream retrieval misses and downstream wrong classifications can overlap and are explicitly tracked via `overlap_retrieval_miss_and_wrong_classification`.

#### E. Table 5: Resource Consumption and Latency Scaling Across Retrieval Depths
- **Target Section:** Section 6.3 (RQ3: Retrieval Depth, API Cost, and Latency Trade-Offs)
- **Target Rows:** 5 experimental conditions
- **Source Artifact:** `outputs/canonical_analysis/rq_analysis.json` (Specialist B analysis deliverable, canonical branch `/rq3/tradeoffs_by_condition/{c}/` aligned 100% with `fixture_export_schema_b172.json`)
- **Field Mappings:**
  1. `Latency Scaling (ms / s)`:
     - Mean Latency: Extracted from `/rq3/tradeoffs_by_condition/{c}/latency_ms/mean` (formatted as `X.XXs`).
     - Median Latency: Extracted from `/rq3/tradeoffs_by_condition/{c}/latency_ms/median` (formatted as `X.XXs`).
     - P95 Latency: Extracted from `/rq3/tradeoffs_by_condition/{c}/latency_ms/p95` (formatted as `X.XXs`).
     - Total Latency Sum: Extracted from `/rq3/tradeoffs_by_condition/{c}/latency_ms/sum` (formatted as `X.XXs`).
  2. `Token Consumption Scaling`:
     - Mean Prompt Tokens / Req: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/mean_prompt_tokens` (formatted as `XXX.X`).
     - Mean Completion Tokens / Req: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/mean_completion_tokens` (formatted as `XXX.X`).
     - Mean Total Tokens / Req: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/mean_total_tokens` (formatted as `XXX.X`).
     - Sum Prompt Tokens: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/sum_prompt_tokens` (comma-separated integer).
     - Sum Completion Tokens: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/sum_completion_tokens` (comma-separated integer).
     - Sum Total Tokens: Extracted from `/rq3/tradeoffs_by_condition/{c}/tokens/sum_total_tokens` (comma-separated integer).
  3. `Financial Cost Scaling (USD)`:
     - Total Settled Cost: Extracted from `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/total_cost_usd`, formatted as `USD XX.XX` (e.g., `USD 1.84`).
     - Cost per Logical Request: Extracted from `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/cost_per_logical_request_usd`, formatted as `USD X.XXXX` (e.g., `USD 0.0014`).
     - Cost per Scorable Query: Extracted from `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/cost_per_scorable_query_usd`, formatted as `USD X.XXXX`.
     - Cost per Correct Attribution: Extracted from `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/cost_per_correct_attribution_usd`, formatted as `USD X.XXXX`.
     - Marginal Cost vs. Baseline: Extracted from `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/marginal_cost_vs_baseline_usd`, formatted as `USD X.XXXX`.
  *(Note: Granular view-level latency and token distributions are systematically accessible via `/rq3/view_diagnostics/{c}/`.)*
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
- **Baseline Preservation Invariant:** All baseline asset hashes verified and frozen in Phase S1 (including protocol semantic digest, whole-file configuration digests, and runtime wrapper code digest) are retained completely intact in their original table section. The plan does not impose an artificial hardcoded count (e.g., exactly 12) if actual row counts differ, ensuring seamless auditability against disk assets.
- **Canonical Dataset Split Manifest Path Invariant:**
  - The authoritative dataset partition split manifest path is `data/ground_truth/synthetic/split_manifest.json` (strictly NOT `data/processed/...` or obsolete interim paths).
  - The Table 6 manifest records the baseline hash of `data/ground_truth/synthetic/dataset_manifest.json`, while runtime test evaluation and analysis outputs record and verify `manifest_sha256` matching `data/ground_truth/synthetic/split_manifest.json`.
- **Dedicated Supplementary Provenance Section:**
  - In Phase S2, canonical runtime execution and evaluation artifacts are appended into a distinct, dedicated supplementary provenance section (or sub-table), NOT modifying or replacing the baseline asset hashes:
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
| **Section 6.1** | RQ1 Headline Findings Narrative | Condition-by-condition comparisons: McNemar's test $p$-value and paired bootstrap confidence intervals comparing `no_rag` against each RAG depth; report all conditions neutrally and objectively without assuming monotonic improvement (recognizing flat, positive, or negative regimes); single-GT ($N=678$) vs multi-GT ($N=40$) attribution complexity evaluated via `/new_proposed_producer_stratified_gt_complexity/by_condition/{c}/` (`single_gt_accuracy_e2e`, `multi_gt_accuracy_e2e`, `complexity_accuracy_delta` with fail-closed schema validation). |
| **Section 6.2** | RQ2 Failure Decomposition Narrative | Quantification of failure axes: upstream retrieval misses ($GT \notin \text{Top-}k$) vs downstream selection errors ($GT \in \text{Top-}k \land \text{Wrong}$); empirical overlap (`overlap_retrieval_miss_and_wrong_classification`); frequency of non-retrieved correct attribution (correct despite GT absent from Top-k, acknowledged neutrally as potential partial prompt clues alongside parametric memory, without asserting internal reasoning mechanisms or causal claims); empirical verdict on the Contextual Dilution Hypothesis. |
| **Section 6.3** | RQ3 Operational Trade-Offs Narrative | Latency inflation analysis: percentage change in mean and P95 latency from No-RAG across RAG depths. Cost scaling under tariff (USD 0.150/1M in, USD 0.600/1M out); cost efficiency (accuracy delta per token/dollar). Identification of operational Pareto trade-offs from Specialist B's `rq_analysis.json` (`/rq3/tradeoffs_by_condition/{c}/` and `/rq3/view_diagnostics/{c}/`). |
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
  - Appends canonical prediction file and ledger hashes to the dedicated supplementary provenance section of Table 6, preserving all baseline asset hashes intact.
  - Automatically triggers `scripts/export_report_docx.py` and runs `scripts/verify_report_metadata.py` under the offline guard.
  - Tested with schema fixture unit tests covering empty, malformed, negative delta, and zero-denominator cases under D2j NULL.

---

## 5. Commit & Worktree State

- **Worktree:** `D:/RAG2ATTCK-worktrees/report-s1`
- **Branch:** `codex/s1-report-related-work` (PR #25)
- **PRE_SHA:** `c0f7c9d1b607a8c24110ddc33f65a6d735b740a2`
- **Document Status:** DRAFT — PENDING CODEX REVIEW
- **Offline Guard Status:** Verified active (`attempted_egress=0`).
- **Plan File:** `reports/evidence/s2_report_population_plan.md`
