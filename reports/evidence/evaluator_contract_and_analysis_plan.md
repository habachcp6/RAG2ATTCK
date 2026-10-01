# Evaluator Contract Verification & Offline RQ Analysis Plan

- **Author**: Subagent B (Evaluator & Analysis Preparation Specialist)
- **Phase**: S1 (Evaluator & Analysis Preparation)
- **Dedicated Worktree**: `D:/RAG2ATTCK-worktrees/prep-evaluator-s1`
- **Branch**: `codex/s1-evaluator-prep`
- **PRE_SHA**: `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`
- **Execution Mode**: Strictly OFFLINE (ZERO live provider/API calls; in-flight live matrix untouched)
- **Timestamp**: `2026-10-02T03:25:00Z`

---

## 1. Executive Summary & Purpose

The purpose of this subagent assignment is to independently verify and harden the scientific evaluation infrastructure and create automated, offline statistical analysis tooling for the RAG2ATTCK study.

In strict adherence to the project's frozen protocol principles:
1. **Zero live provider calls**: All testing, evaluation, and diagnostic verification was executed offline against synthetic and fixture datasets. No in-flight live matrix predictions were scored or altered.
2. **Canonical protocol preservation**: The canonical evaluator entrypoint in `src/evaluation/experiment_metrics.py` remains fail-closed behind the `ScientificProtocolApproval` contract (D1–D7). No flags, bypasses, or ad-hoc defaults can unblock scoring without explicit verified approval.
3. **Dedicated offline analysis pipeline**: Created `scripts/analysis/evaluate_rqs.py` to compute publication-grade metrics and statistical tests for Research Questions **RQ1**, **RQ2**, and **RQ3**.
4. **Comprehensive offline test suite**: Created `tests/test_evaluator_offline_contract.py` containing 16 rigorous tests validating every edge case of the evaluation contract and analysis tools.

---

## 2. Authoritative Ground Truth TEST Cohort Join

Per the frozen dataset manifest (`data/ground_truth/synthetic/dataset_manifest.json`) and ground truth annotations (`ground_truth.jsonl`, `split_manifest.json`), the exact join across the **1,280 TEST views** is:

| Category | View Count | Ground Truth Semantics | Protocol Action (D2b/D2c) | Scorable Cohort |
| :--- | :---: | :--- | :--- | :---: |
| **Mapped Positives** | **718** | Valid MITRE ATT&CK technique IDs | Retained in scoring | **Included (N=718)** |
| ↳ *Single-GT* | 678 | Exactly 1 technique ID annotated | Retained in scoring | Included |
| ↳ *Multi-GT* | 40 | 2+ technique IDs annotated | Evaluated via ANY_MATCH (D2a) | Included |
| **Ambiguous GT** | **311** | Multiple plausible or vague techniques | **EXCLUDE** (D2c) | Excluded |
| **Unmapped GT** | **251** | Telemetry lacks attack technique mapping | **EXCLUDE** (D2b) | Excluded |
| **Total TEST Cohort** | **1,280** | Complete paired benchmark split | 640 Single + 640 Contextual | **718 Scorable** |

This guarantees that:
- The denominator for end-to-end accuracy ($N_{\text{scorable}}$) is strictly **718** on the TEST split.
- Ambiguous (311) and unmapped (251) views are tracked and reported with explicit audit reasons (`AMBIGUOUS_GROUND_TRUTH`, `UNMAPPED_GROUND_TRUTH`) without corrupting attribution accuracy.

---

## 3. Evaluator CLI & Output Contracts Verification

We conducted an independent code audit and test suite verification of `src/evaluation/experiment_metrics.py` and the CLI wrapper in `src/experiment/__main__.py`:

### 3.1 Five Experimental Conditions
- The benchmark evaluates exactly 5 conditions: `no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`.
- Missing, duplicated, or extraneous condition names fail closed immediately during input validation.

### 3.2 Fixed 474-Class Macro-F1 Denominator (D2d)
- Under policy `d2d_macro_f1_universe = "FROZEN_BENCHMARK_UNIVERSE"`, the class universe is frozen to the 474 techniques present in the enterprise ATT&CK corpus.
- For any class with support = 0 and predictions = 0, $F_1 = 0.0$.
- Macro-F1 is computed strictly as $\frac{1}{474} \sum_{c=1}^{474} F_{1, c}$. The denominator never fluctuates based on model predictions or test cohort presence.

### 3.3 ANY_MATCH Multi-GT Semantics (D2a)
- For the 40 multi-GT samples, if the model predicts a single valid technique ID that exists anywhere in the sample's ground-truth set ($\hat{y} \in Y_{\text{true}}$), the prediction is scored as correct.
- If the predicted ID is outside the ground truth set, it is scored as incorrect.

### 3.4 Excluded Unmapped and Ambiguous Ground Truth (D2b/D2c)
- When `d2b_empty_ground_truth = "EXCLUDE"` and `d2c_ambiguous_ground_truth = "EXCLUDE"`, unmapped and ambiguous samples are excluded from `scorable_records`.
- Condition outputs record `unmapped_ground_truth_count`, `ambiguous_ground_truth_count`, and their respective exclusion reason strings.

### 3.5 End-to-End Failure Denominators (D2e/D2f)
- `accuracy_end_to_end` evaluates:
  $$\text{Accuracy}_{\text{e2e}} = \frac{N_{\text{correct}}}{N_{\text{scorable}}}$$
  All records for scorable samples are retained in the denominator, regardless of parse status (`VALID`, `INVALID_ID`, `MALFORMED_RESPONSE`, `TIMEOUT`, `API_FAILURE`). Invalid IDs and API errors count as failures (0 in numerator, 1 in denominator).
- `accuracy_valid_outputs` evaluates:
  $$\text{Accuracy}_{\text{valid}} = \frac{N_{\text{correct}}}{N_{\text{valid\_scorable}}}$$
  Restricting the denominator to records that parsed successfully into valid ATT&CK IDs.

### 3.6 Invalid and Retired-ID Diagnostics (D2g)
- Failed completions are decomposed into:
  - `invalid_syntax_count`: Malformed ID strings failing syntax validation regex (`validate_attack_id_syntax`).
  - `unknown_id_count`: Syntactically valid IDs that do not exist in the pinned ATT&CK v19.2 registry.
  - `retired_id_observation_count`: IDs present in the registry but marked `deprecated: true` or `revoked: true`.

### 3.7 Independent Failure Axes (D2i)
- `compute_failure_decomposition` evaluates 5 independent diagnostic axes without forced mutual exclusion or arbitrary priority hierarchies:
  1. `retrieval_miss_rate`
  2. `provider_failure_rate`
  3. `parse_failure_rate`
  4. `invalid_attack_id_rate`
  5. `valid_but_wrong_classification_rate`
  Plus `overlap_retrieval_miss_and_wrong_classification` to quantify correlated errors.

### 3.8 Null Zero Denominators (D2j)
- In `per_technique_metrics.json`: when `d2j_zero_denominator = "NULL"`, classes with 0 support and 0 predictions report `precision = None`, `recall = None`, and `f1 = None` rather than an artificial 0.0 or 1.0.

### 3.9 Six Canonical Output Artifacts
The evaluator writes six JSON files atomically using temporary replacement (`.json.tmp` -> `.json` with `fsync`):
1. `overall_metrics.json`
2. `per_condition_metrics.json`
3. `per_technique_metrics.json`
4. `retrieval_conditional_metrics.json`
5. `failure_decomposition.json`
6. `run_provenance.json`

---

## 4. Offline Research Question Analysis Tools (`scripts/analysis/evaluate_rqs.py`)

We implemented a dedicated analysis engine in `scripts/analysis/evaluate_rqs.py` designed to consume completed run directories or canonical evaluation artifacts.

### 4.1 Research Question 1 (RQ1): Controlled Attribution Accuracy
- **Core Question**: *To what extent does MITRE ATT&CK-grounded RAG improve exact technique attribution accuracy compared to No-RAG?*
- **Computed Metrics**:
  - `accuracy_end_to_end` per condition.
  - `accuracy_valid_outputs` per condition.
  - `macro_f1` (over invariant 474 universe).
  - Absolute delta: $\Delta \text{Acc} = \text{Acc}_{\text{rag\_k}} - \text{Acc}_{\text{no\_rag}}$.
  - Relative gain percentage: $\frac{\text{Acc}_{\text{rag\_k}} - \text{Acc}_{\text{no\_rag}}}{\text{Acc}_{\text{no\_rag}}} \times 100\%$.
- **Secondary Statistical Tests**:
  - **Paired McNemar Test**:
    Evaluates discordant pairs ($b$: No-RAG wrong & RAG right; $c$: No-RAG right & RAG wrong). Computes Edwards continuity-corrected $\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$ and exact two-sided binomial $p$-value from $B(b + c, 0.5)$.
  - **Paired Bootstrap Confidence Intervals (95% CI)**:
    $B = 1000$ paired resamples with replacement using a deterministic seed (`numpy.random.default_rng(seed)`), computing empirical percentile bounds $[q_{0.025}, q_{0.975}]$ for $\Delta \text{Accuracy}$ and $\Delta \text{Macro-F1}$.

### 4.2 Research Question 2 (RQ2): Retrieval vs. Generation Error Decomposition
- **Core Question**: *How does retrieval quality affect final attribution, and where do failures originate?*
- **Computed Metrics**:
  - **Upstream Retrieval Quality**:
    - Hit@k / Binary Recall@k: fraction of scorable samples where $\text{GT} \cap \text{Candidates} \neq \emptyset$.
    - Macro Recall@k: average fraction of ground-truth techniques retrieved in top-$k$.
    - Retrieval Miss count and rate.
  - **Downstream Generation Conditioning (D2h)**:
    - $P(\text{Correct} \mid \text{Retrieval Success})$: Accuracy of LLM when ground truth was provided in context.
    - $P(\text{Correct} \mid \text{Retrieval Failure})$: Accuracy of LLM when ground truth was absent from context.
  - **Pipeline Error Decomposition (Disjoint Partition of All Failures)**:
    Every failed sample is partitioned into exactly one root cause:
    1. **Retrieval Miss Error**: Retriever failed to retrieve ground truth ($GT \cap C = \emptyset$). Upstream retrieval bottleneck.
    2. **Generation Misattribution Error**: Retriever succeeded ($GT \cap C \neq \emptyset$), but LLM chose a distractor candidate. Downstream reasoning bottleneck.
    3. **Generation System/Parse Error**: Retriever succeeded, but LLM output was unparseable or API failed.
    Sum of errors: $\text{Retrieval Miss} + \text{Gen Misattribution} + \text{System/Parse} = \text{Total Failures}$ ($100\%$).

### 4.3 Research Question 3 (RQ3): Retrieval Depth, Latency, Cost Trade-offs & View Diagnostics
- **Core Question**: *What is the resource trade-off across candidate depths $k \in \{1, 3, 5, 10\}$ vs Baseline ($k=0$)?*
- **Resource & Efficiency Trade-offs**:
  - **Latency Distribution**: Mean, median, p95, and total latency (ms) per condition.
  - **Token Accounting**: Mean prompt, completion, and total tokens per query.
  - **Monetary Cost**: Computed directly from `config/pricing_v1.json` via `calculate_attempt_token_cost`:
    - Total cost ($USD) per condition.
    - Cost per scorable query ($USD/sample).
    - Cost per correct attribution: $\frac{\text{Total Cost}}{N_{\text{correct}}}$.
    - Marginal cost per accuracy point gained.
- **Paired View Diagnostics (Single-View vs Contextual-View)**:
  - Each pair in the benchmark contains 1 single-event view (isolated evidence) and 1 contextual-event view (with background events).
  - Evaluates:
    - $\text{Accuracy}_{\text{single}}$ vs $\text{Accuracy}_{\text{contextual}}$.
    - View delta: $\Delta_{\text{view}} = \text{Acc}_{\text{contextual}} - \text{Acc}_{\text{single}}$.
    - Pair concordance breakdown: Both correct, single-only correct, contextual-only correct, both incorrect.
    - McNemar paired test on Single vs Contextual accuracy.

### 4.4 Automated Output Artifacts
`evaluate_rqs.py` generates two self-contained artifacts:
- `rq_analysis.json`: Machine-readable structured JSON with all numerical metrics, CIs, p-values, and metadata.
- `rq_analysis_summary.md`: Publication-ready GitHub-Flavored Markdown report containing structured summary tables for RQ1, RQ2, and RQ3.

---

## 5. Verification Test Suite (`tests/test_evaluator_offline_contract.py`)

A comprehensive test suite was written to verify every aspect of the evaluation contract and analysis tooling.

### 5.1 Test Inventory

| # | Test Function Name | Tested Component | Status |
| :-: | :--- | :--- | :-: |
| 1 | `test_evaluator_contract_five_conditions_matrix` | 5 conditions enforcement | **PASSED** |
| 2 | `test_evaluator_contract_fixed_474_class_macro_f1` | Invariant Macro-F1 denominator | **PASSED** |
| 3 | `test_evaluator_contract_any_match_multilabel_ground_truth` | D2a ANY_MATCH multi-label GT | **PASSED** |
| 4 | `test_evaluator_contract_unmapped_and_ambiguous_gt_exclusion` | D2b/D2c exclusion & counts | **PASSED** |
| 5 | `test_evaluator_contract_end_to_end_failure_denominator` | D2e/D2f invalid ID & API errors in e2e acc | **PASSED** |
| 6 | `test_evaluator_contract_invalid_and_retired_id_diagnostics` | D2g syntax vs unknown vs retired IDs | **PASSED** |
| 7 | `test_evaluator_contract_independent_failure_axes` | D2i independent diagnostic axes | **PASSED** |
| 8 | `test_evaluator_contract_null_zero_denominators` | D2j NULL zero denominators | **PASSED** |
| 9 | `test_evaluator_cli_contract_subprocess_execution` | CLI subprocess execution with dev journal | **PASSED** |
| 10 | `test_mcnemar_test_statistical_properties` | McNemar chi2, exact binomial, odds ratio | **PASSED** |
| 11 | `test_paired_bootstrap_ci_bounds` | Paired bootstrap percentile CI bounds | **PASSED** |
| 12 | `test_rq1_controlled_comparison_computation` | RQ1 metrics, deltas, relative gains, CIs | **PASSED** |
| 13 | `test_rq2_error_decomposition_computation` | RQ2 recall, conditional acc, disjoint error partition | **PASSED** |
| 14 | `test_rq3_tradeoffs_and_view_diagnostics` | RQ3 latency, token, cost, paired views | **PASSED** |
| 15 | `test_run_rq_analysis_generates_all_artifacts` | Full analysis pipeline generating JSON & MD | **PASSED** |
| 16 | `test_evaluate_rqs_cli_subprocess_execution` | `evaluate_rqs.py` CLI subprocess execution | **PASSED** |

### 5.2 Test Execution Results
```bash
uv run pytest tests/test_evaluator_offline_contract.py -v
============================= 16 passed in 9.27s ==============================

uv run pytest tests/test_evaluator_offline_contract.py tests/test_experiment_evaluation.py -q
============================ 110 passed in 19.63s =============================
```

### 5.3 Code Quality & Linter Compliance
```bash
uv run ruff check scripts/analysis/evaluate_rqs.py tests/test_evaluator_offline_contract.py
All checks passed!
```

---

## 6. Artifact Provenance & File Integrity

| File Path | SHA-256 Digest | Purpose |
| :--- | :--- | :--- |
| `scripts/analysis/evaluate_rqs.py` | `2a6ee0385da2424deb667dc26e5e76dc591d95b91147f1a569fdd515accc4dd8` | Offline RQ1/RQ2/RQ3 analysis script |
| `scripts/analysis/__init__.py` | `28b40746d09b574e95393ac9e2a95879116cd9d4c7a86afb1be7be573f9ad54a` | Analysis package initializer |
| `tests/test_evaluator_offline_contract.py` | `748a15cf4f3fbd4cb70fc5d879de385d398dbed6da6ef8085f440f0409a4753b` | Evaluator offline contract test suite |
| `reports/evidence/evaluator_contract_and_analysis_plan.md` | `b6af0316b508b9b3810faf99794bcd060fe71ee0e1fa451f32617be67a7ce66c` (prior to this cell update) | Comprehensive Phase S1 evidence document |

---

## 7. Protocol Compliance Checklist

- [x] PRE_SHA verified: `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`
- [x] Strictly ZERO live provider/API calls executed.
- [x] In-flight live matrix untouched; zero scores generated for live runs.
- [x] Verified 5 conditions matrix (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`).
- [x] Verified fixed 474-class Macro-F1 denominator (`FROZEN_BENCHMARK_UNIVERSE`).
- [x] Verified D2a ANY_MATCH multi-GT semantics.
- [x] Verified D2b/D2c unmapped (251) and ambiguous (311) ground truth exclusions.
- [x] Verified D2e/D2f end-to-end failure denominators (invalid IDs and API failures penalized).
- [x] Verified D2g invalid syntax vs unknown vs retired ID diagnostics.
- [x] Verified D2i independent failure axes.
- [x] Verified D2j NULL zero denominators.
- [x] Implemented `scripts/analysis/evaluate_rqs.py` (RQ1, RQ2, RQ3, McNemar, Bootstrap CIs, Pricing).
- [x] Implemented `tests/test_evaluator_offline_contract.py` (16 test cases).
- [x] Full test suite passed (16/16 offline contract tests, 110/110 evaluation suite tests).
- [x] Ruff lint checks passed with zero errors (`line-length = 100`).
