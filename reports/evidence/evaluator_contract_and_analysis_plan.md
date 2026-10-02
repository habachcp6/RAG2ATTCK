# Evaluator Contract Verification & Offline RQ Analysis Plan

- **Author**: Subagent B (Evaluator & Analysis Preparation Specialist)
- **Phase**: S1/S2 (Evaluator & Analysis Preparation)
- **Dedicated Worktree**: `D:/RAG2ATTCK-worktrees/prep-evaluator-s1`
- **Branch**: `codex/s1-evaluator-prep` (PR #27)
- **Status**: PENDING CODEX REVIEW (Not final approved)
- **Execution Mode**: Strictly OFFLINE (ZERO live provider/API calls; in-flight live matrix untouched)
- **Timestamp**: `2026-10-02T01:15:00Z`

---

## 1. Executive Summary & Purpose

The purpose of this subagent assignment is to independently verify and harden the scientific evaluation infrastructure, implement publication-grade offline statistical analysis tooling, and execute comprehensive contract repairs addressing all items from the Codex Orchestration Review (`artifacts/orchestration/analysis_reproduction_review_20261002.md`), the subsequent Codex differential probe (`FAIL | B_NATIVE_TARIFF_CONFORMANCE`), and the execution-mode provenance boundary directive (`FAIL/INSUFFICIENT_EVIDENCE | BD_MODE_BOUNDARY`).

In strict adherence to the project's frozen protocol principles:
1. **Zero live provider calls**: All testing, evaluation, and diagnostic verification was executed offline against synthetic and fixture datasets. No in-flight live matrix predictions were scored or altered (strictly 0 egress).
2. **Canonical protocol preservation**: The canonical evaluator entrypoint in `src/evaluation/experiment_metrics.py` remains fail-closed behind the `ScientificProtocolApproval` contract (D1–D7). No flags, bypasses, or ad-hoc defaults can unblock scoring without explicit verified approval.
3. **Dedicated offline analysis pipeline**: Created `scripts/analysis/evaluate_rqs.py` to compute publication-grade metrics and statistical tests for Research Questions **RQ1**, **RQ2**, and **RQ3**.
4. **Comprehensive offline test suite**: Created `tests/test_evaluator_offline_contract.py` containing 46 rigorous tests validating every edge case of the evaluation contract, financial accounting, failure semantics, native tariff conformance, execution-mode boundaries, subset Macro-F1 calculations, and analysis tools.
5. **Codex Review Repairs Completed (Items 1–9, B_NATIVE_TARIFF_REPAIR, & BD_MODE_BOUNDARY)**:
   - **Item 1 (Strict Pricing Validation)**: Tariffs, bounds, and ceilings validated against `config/pricing_v1.json`. Fail-closed on missing keys or unknown tiers; zero-cost fallbacks are strictly prohibited.
   - **Item 2 (Ledger/Journal Reconciliation - B_RECONCILE_REPAIR2 & B_NATIVE_TARIFF_REPAIR)**: Parses `attempt_receipt` and `monetary_settle` events, verifies ordinal and attempt uniqueness, binds record SHA-256 against prediction records, accounts for retries, and preserves study-wide financial accounting with prior-pilot hold ($0.05264010) preserved without adding to individual condition costs.
   - **B_NATIVE_TARIFF_REPAIR (Native Tariff Delegation)**: Eliminated custom calculation loops in `reconcile_journal_and_ledger` and delegated directly to native frozen `calculate_request_cost_from_receipts` in `src.experiment.monetary_ledger`. Added `RecordObjectAdapter` for getattr binding, fail-closed enforcement on `req_breach`, and distinguishing tests covering positive control ($0.00000370), worst-case fee on `RATE_LIMIT` / `TIMEOUT` / `API_FAILURE` ($0.53974560), missing `service_tier`, foreign model receipts, `INCOMPLETE` status with tokens, final-receipt drift, and logical worst ceiling breaches ($2.15898240).
   - **BD_MODE_BOUNDARY (Execution-Mode Boundary & Honest Provenance)**: Added execution-mode metadata tracking to `run_rq_analysis` (`execution_mode`, `dataset_split`, `fixture_only`, `provenance_status`). Enforces honest provenance separation between diagnostic mock fixtures (`provenance_status='diagnostic_fixture'`, triggering an explicit Markdown alert banner) and canonical empirical study data (`provenance_status='canonical_study'`). Added distinguishing positive and diagnostic control tests.
   - **Item 3 (Three Cost Denominators)**: Discloses `cost_per_logical_request_usd` (N=1,280), `cost_per_scorable_query_usd` (N=718), and `cost_per_correct_attribution_usd`, alongside explicit real expenditure disclosures on excluded views (311 ambiguous + 251 unmapped).
   - **Item 4 (Robust CLI Root Resolution)**: Resolves default protocol, pricing, output, and ledger paths against `--repository-root` or `repo_root` (`Path(__file__).resolve().parents[2]`), ensuring deterministic execution regardless of caller CWD.
   - **Item 5 (Distinguishing 474-Class Macro-F1 Test)**: Mathematically demonstrates that 471 unobserved classes contribute 0.0 and denominator is strictly 474, proving that an observed-only denominator (dividing by 3) fails by a factor of 158x.
   - **Item 6 (Comprehensive Regressions)**: Test coverage for unknown pricing tiers, negative tokens, cached > prompt tokens, cached token tariffs, missing usage worst-case attempt charge ($0.53974560), duplicate receipt ordinals, duplicate monetary settles, and hash mismatches.
   - **Item 7 (Pair-Cluster Bootstrap & View Cohort Counts)**: Implements pair-cluster bootstrap resampling by `pair_id` (clustering single and contextual views together to preserve intra-pair correlation; designated as an exploratory diagnostic) and explicitly discloses exact TEST scorable view counts (278 single views, 440 contextual views; 718 total).
   - **Item 8 (RQ2 D2i Semantics & No-RAG N/A Handling)**: Evaluates independent failure axes without forced mutual exclusion or causal partitioning claims; tracks overlaps (`overlap_retrieval_miss_and_wrong_classification`, `overlap_retrieval_miss_and_provider_failure`); sets No-RAG retrieval and conditional metrics strictly to `None`/`null` (not 0.0); sets zero-denominator percentages to `None`/`null` per D2j.
   - **Item 9 (UNIFIED_MAPPING_R2 - True Subset Macro-F1 & Fresh Schema Synchronization)**:
     - **True View Subset Macro-F1**: Evaluates true Macro-F1 across the frozen 474-class universe for single-view ($N=278$ scorable) and contextual-view ($N=440$ scorable) subsets by passing view subsets directly to frozen `compute_condition_metrics`. Exports `single_view_macro_f1`, `contextual_view_macro_f1`, and `view_macro_f1_delta` under `/rq3/view_diagnostics/{c}/`.
     - **True GT Complexity Subset Macro-F1**: In `compute_stratified_gt_complexity_producer`, evaluates true Macro-F1 across the frozen 474-class universe for single-GT ($N=678$ scorable) and multi-GT ($N=40$ scorable) subsets via direct delegation to `compute_condition_metrics`. Replaces duplicate overall condition Macro-F1 with `single_gt_macro_f1`, `multi_gt_macro_f1`, and `complexity_macro_f1_delta`, retaining overall condition Macro-F1 strictly as an explicitly labeled reference (`overall_macro_f1_reference`).
     - **Mathematical Distinctness with Known-Answer Rational Fractions**: Validated against dedicated known-answer fixture `_fixture_474_discordant_known_answer` over the 474-class universe with exact rational numerical assertions:
       * Single-View Macro-F1 = $5 / 1422 \approx 0.003516$ (differs from overall by $1/316 \approx 0.003165$)
       * Contextual-View Macro-F1 = $8 / 1422 \approx 0.005626$ (differs from overall by $1/948 \approx 0.001055$)
       * View Macro-F1 Delta = $1 / 474 \approx 0.002110$
       * Overall Condition Macro-F1 (Reference) = $19 / 2844 \approx 0.006681$
       * Single-GT Macro-F1 = $10 / 1422 \approx 0.007032$ (differs from overall by $1/2844 \approx 0.000352$)
       * Multi-GT Macro-F1 = $1 / 474 \approx 0.002110$ (differs from overall by $13/2844 \approx 0.004571$)
       * Complexity Macro-F1 Delta = $-7 / 1422 \approx -0.004923$
     - **Fresh Schema Generation**: Regenerated fresh schema `artifacts/orchestration/fixture_export_schema_3625.json` (and synchronized `fixture_export_schema_b172.json`) via `scripts/analysis/build_fixture_export_schema.py`, binding exact source hash `c48eeb27b19626344e5f10b2cac674437b4053bb01f014060905702c52235f95` and 1,679 leaf pointers across 7 export files.

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
- Within the 718 scorable views, the view distribution is explicitly documented as **278 single views** and **440 contextual views**.

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
  Plus overlap metrics (`overlap_retrieval_miss_and_wrong_classification`, `overlap_retrieval_miss_and_provider_failure`) to quantify correlated multi-fault events.

### 3.8 Null Zero Denominators (D2j)
- In `per_technique_metrics.json` and `rq_analysis.json`: when denominators are zero, precision, recall, conditional metrics, and percentages evaluate strictly to `None` / `null` rather than artificial 0.0 or 1.0.

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

We implemented a publication-grade analysis engine in `scripts/analysis/evaluate_rqs.py` designed to consume completed run directories or canonical evaluation artifacts.

### 4.1 Research Question 1 (RQ1): Controlled Attribution Accuracy
- **Core Question**: *To what extent does MITRE ATT&CK-grounded RAG improve exact technique attribution accuracy compared to No-RAG?*
- **Computed Metrics**:
  - `accuracy_end_to_end` per condition.
  - `accuracy_valid_outputs` per condition.
  - `macro_f1` (over invariant 474 universe).
  - Absolute delta: $\Delta \text{Acc} = \text{Acc}_{\text{rag\_k}} - \text{Acc}_{\text{no\_rag}}$.
  - Relative gain percentage: $\frac{\text{Acc}_{\text{rag\_k}} - \text{Acc}_{\text{no\_rag}}}{\text{Acc}_{\text{no\_rag}}} \times 100\%$.
- **Statistical Significance & Resampling**:
  - **Paired McNemar Test**:
    Evaluates discordant pairs ($b$: No-RAG wrong & RAG right; $c$: No-RAG right & RAG wrong). Computes Edwards continuity-corrected $\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$ and exact two-sided binomial $p$-value from $B(b + c, 0.5)$.
  - **Pair-Cluster Bootstrap Confidence Intervals (95% CI)**:
    Resampling is grouped by `pair_id` so that both single and contextual views from the same pair are sampled together, preserving intra-pair correlation structure. Labeled explicitly as an exploratory diagnostic (`resampling_method = "pair_cluster_bootstrap"`). Computes empirical percentile bounds $[q_{0.025}, q_{0.975}]$ for $\Delta \text{Accuracy}$ and $\Delta \text{Macro-F1}$ over $B = 1000$ cluster resamples.

### 4.2 Research Question 2 (RQ2): Independent Failure Axes & Retrieval Quality
- **Core Question**: *How does retrieval quality affect final attribution, and where do failures originate?*
- **Upstream Retrieval Quality**:
  - Hit@k / Binary Recall@k: fraction of scorable samples where $\text{GT} \cap \text{Candidates} \neq \emptyset$.
  - Macro Recall@k: average fraction of ground-truth techniques retrieved in top-$k$.
  - Retrieval Miss count and rate.
- **Downstream Generation Conditioning (D2h)**:
  - $P(\text{Correct} \mid \text{Retrieval Success})$: Accuracy of LLM when ground truth was provided in context.
  - $P(\text{Correct} \mid \text{Retrieval Failure})$: Accuracy of LLM when ground truth was absent from context.
- **Canonical Independent Failure Axes (D2i)**:
  Failures are reported across 5 non-mutually-exclusive diagnostic axes:
  1. `retrieval_miss`: Retriever failed to include any ground-truth technique ($GT \cap C = \emptyset$).
  2. `provider_failure`: Network timeouts, rate limits, or API dropouts.
  3. `parse_failure`: Malformed JSON or unparseable technique structure.
  4. `invalid_attack_id`: Hallucinated or non-existent ATT&CK IDs.
  5. `valid_but_wrong_classification`: Syntactically valid registry IDs that do not match ground truth.
  - **Overlap Tracking**: Multi-fault events are explicitly counted and reported:
    - `overlap_retrieval_miss_and_wrong_classification`
    - `overlap_retrieval_miss_and_provider_failure`
    - `overlap_retrieval_miss_and_parse_failure`
    - `overlap_retrieval_miss_and_invalid_id`
  - **No-RAG Semantics**: For $k=0$ (`no_rag`), retrieval metrics (Hit@k, Recall@k, retrieval miss) and retrieval-conditional accuracies are strictly set to `None`/`null` (`retrieval_metrics.applicable = false`), avoiding misleading 0.0 values.
  - **Zero Denominators (D2j)**: Rates and percentages with zero denominators evaluate strictly to `None`/`null`.

### 4.3 Research Question 3 (RQ3): Retrieval Depth, Latency, Cost Trade-offs & View Diagnostics
- **Core Question**: *What is the resource trade-off across candidate depths $k \in \{1, 3, 5, 10\}$ vs Baseline ($k=0$)?*
- **Resource & Efficiency Trade-offs**:
  - **Latency Distribution**: Mean, median, p95, and total latency (ms) per condition.
  - **Token Accounting**: Mean prompt, completion, total, and prompt cached tokens per query.
- **Rigorous Financial Accounting & Reconciliation**:
  - **Strict Pricing Config Validation**: Validates `config/pricing_v1.json` for model rate parity, service tiers, currency ($USD), cache tariffs (write: $0.25/1M, read: $0.02/1M), and maximum spend ceilings ($19.99). Fails closed immediately on missing rates; no zero fallbacks.
  - **Journal & Ledger Reconciliation**:
    - Reconciles `attempt_receipt` and `monetary_settle` events against final predictions.
    - Enforces uniqueness of receipt ordinals and attempt indices.
    - Validates record hash binding (`record_sha256`) against prediction bytes.
    - Identifies retried attempts and computes reconciled costs including failed/retry expenditure.
    - Missing token usage records are billed at the native worst-case attempt fee ($0.53974560), tracking `missing_usage_records_count` and `missing_usage_charged_usd`.
  - **Whole-Study Financial Accounting**:
    - Discloses `total_study_budget_usd` ($19.99).
    - Preserves prior pilot provisional hold ($0.05264010) study-wide without adding it to individual condition costs.
    - Computes `net_remaining_uncommitted_budget_usd`.
  - **Three Explicit Cost Denominators**:
    1. `cost_per_logical_request_usd`: Total expenditure divided by all 1,280 benchmark views.
    2. `cost_per_scorable_query_usd`: Total expenditure divided by 718 scorable queries.
    3. `cost_per_correct_attribution_usd`: Total expenditure divided by $N_{\text{correct}}$.
  - **Excluded Views Real Expenditure**:
    - Discloses real expenditure committed to the 311 ambiguous views and 251 unmapped views (`cost_of_all_excluded_views_usd`, `ambiguous_views_spend_usd`, `unmapped_views_spend_usd`).
- **Paired View Diagnostics (Single-View vs Contextual-View)**:
  - Discloses exact TEST scorable view counts: **278 single views** and **440 contextual views** (718 total).
  - Evaluates:
    - $\text{Accuracy}_{\text{single}}$ vs $\text{Accuracy}_{\text{contextual}}$.
    - View delta: $\Delta_{\text{view}} = \text{Acc}_{\text{contextual}} - \text{Acc}_{\text{single}}$.
    - Pair concordance breakdown on complete scorable pairs: both correct, single-only correct, contextual-only correct, both incorrect.
    - McNemar paired test on Single vs Contextual accuracy.

### 4.4 Robust CLI Root Resolution
- CLI argument `--repository-root` defaults to `Path(__file__).resolve().parents[2]`.
- `--protocol-file`, `--pricing-file`, `--journal-file`, `--study-ledger-file`, and `--output-dir` resolve deterministically against `repo_root` when provided as relative paths.
- Execution from external working directories behaves identically to root-level invocation.

### 4.5 Automated Output Artifacts
`evaluate_rqs.py` generates two self-contained artifacts:
- `rq_analysis.json`: Machine-readable structured JSON with all numerical metrics, pair-cluster CIs, p-values, failure axes, reconciled financial accounting, and metadata.
- `rq_analysis_summary.md`: Publication-ready GitHub-Flavored Markdown report containing structured summary tables for RQ1, RQ2, and RQ3.

### 4.6 Codex Probe Investigation & Repair Resolution (B_RECONCILE_REPAIR2)
Following initial implementation, an independent probe (`artifacts/orchestration/probe_b_receipt_reconciliation.py`) was executed to stress-test journal and ledger reconciliation under adversarial drift mutations. The probe surfaced three critical fail-open vulnerabilities:
1. **Manifest binding gap**: Injected mismatched header manifest SHA (`b`*64 vs records `a`*64) was accepted instead of fail-closed.
2. **Cost recomputation bypass**: Settlement claiming $1.23 for a receipt calculating to $0.0000490 was accepted without reconciliation against attempt receipts.
3. **Ledger ignored**: Supplied `study_ledger_data` claiming $9.99 was ignored without one-to-one ledger verification.

**Architectural Hardening Implemented**:
- **Header & Matrix Enforcement**: Exact header event requirement, matching record manifest SHA-256. Integer ordinals must be strictly contiguous positive sequences (1..N). Complete matrix coverage requires all records to be completed and settled; foreign settlement/receipt keys are rejected immediately.
- **Per-Request Cost Recalculation**: Recomputes per-attempt and per-request costs using native tariff models (including retries, worst-case missing usage charges of $0.53974560, and prompt cache read/write rates). Settlement costs must match computed receipt sums exactly; discrepancies fail closed.
- **Reservation Hold Lifecycle**: `complete` verifies record SHA-256 but does NOT release reservation holds; only `monetary_settle`, `monetary_cancel_orphan`, or `cancel_hold` releases holds. Native `amount_usd` is read from `monetary_cancel_orphan`. Conservation invariant `held == cost + refund` is strictly enforced.
- **Read-Only Ledger Validation**: Compares supplied ledger data one-to-one against journal complete/settle events, pricing contract SHA, record SHAs, costs, refunds, and balance conservation equation (`total - pilot - settled - active == available`).
- **Probe Fail-Closed**: Running `probe_b_receipt_reconciliation.py` now fails closed immediately with `ValueError: Journal header manifest_sha256 mismatch with records` (exit code 1).

---

## 5. Verification Test Suite (`tests/test_evaluator_offline_contract.py`)

A comprehensive test suite of 46 rigorous tests verifies every aspect of the evaluation contract, financial accounting, failure semantics, mutation edge cases, and analysis tooling.

### 5.1 Test Inventory

| # | Test Function Name | Tested Component | Status |
| :-: | :--- | :--- | :-: |
| 1 | `test_evaluator_contract_five_conditions_matrix` | 5 conditions enforcement | **PASSED** |
| 2 | `test_evaluator_contract_fixed_474_class_macro_f1_distinguishing` | Distinguishing 474 Macro-F1 test (158x penalty on observed-only) | **PASSED** |
| 3 | `test_evaluator_contract_any_match_multilabel_ground_truth` | D2a ANY_MATCH multi-label GT | **PASSED** |
| 4 | `test_evaluator_contract_unmapped_and_ambiguous_gt_exclusion` | D2b/D2c exclusion & counts | **PASSED** |
| 5 | `test_evaluator_contract_end_to_end_failure_denominator` | D2e/D2f invalid ID & API errors in e2e acc | **PASSED** |
| 6 | `test_evaluator_contract_invalid_and_retired_id_diagnostics` | D2g syntax vs unknown vs retired IDs | **PASSED** |
| 7 | `test_evaluator_contract_independent_failure_axes` | D2i independent diagnostic axes | **PASSED** |
| 8 | `test_evaluator_contract_null_zero_denominators` | D2j NULL zero denominators | **PASSED** |
| 9 | `test_evaluator_cli_contract_subprocess_execution` | CLI subprocess execution with dev journal | **PASSED** |
| 10 | `test_pricing_config_strict_validation` | Strict pricing tariff, ceiling, and key validation | **PASSED** |
| 11 | `test_malformed_token_values_validation` | Negative token rejection and cached > prompt tokens | **PASSED** |
| 12 | `test_cached_token_rates_tariff_accounting` | Cache read ($0.02) vs cache write ($0.25) pricing | **PASSED** |
| 13 | `test_missing_usage_worst_case_attempt_charge` | Native worst-case attempt fee ($0.53974560) on missing usage | **PASSED** |
| 14 | `test_reconciled_financial_accounting_with_retries` | Financial reconciliation accounting for retried attempts | **PASSED** |
| 15 | `test_reconciliation_duplicate_and_mismatched_keys_fail` | Rejects duplicate ordinals, duplicate settles, hash mismatches | **PASSED** |
| 16 | `test_reconciliation_mutation_foreign_and_missing_header` | B_RECONCILE: foreign/missing/duplicate header validation | **PASSED** |
| 17 | `test_reconciliation_mutation_settlement_vs_receipt_cost_and_refund_mismatch` | B_RECONCILE: settlement drift & conservation failure | **PASSED** |
| 18 | `test_reconciliation_mutation_ledger_vs_journal_drift` | B_RECONCILE: ledger cost/hash drift & missing/extra keys | **PASSED** |
| 19 | `test_reconciliation_mutation_missing_and_extra_keys` | B_RECONCILE: matrix coverage & non-contiguous ordinals | **PASSED** |
| 20 | `test_reconciliation_mutation_two_retries_with_cached_usage` | B_RECONCILE: 2 retries (3 attempts) with cached tariffs | **PASSED** |
| 21 | `test_reconciliation_mutation_missing_usage` | B_RECONCILE: missing token usage worst-case attempt charge | **PASSED** |
| 22 | `test_reconciliation_mutation_orphan_cancellation` | B_RECONCILE: orphan hold release with native amount_usd | **PASSED** |
| 23 | `test_reconciliation_mutation_complete_without_settle` | B_RECONCILE: complete without settle fail-closed | **PASSED** |
| 24 | `test_reconciliation_mutation_nonfinite_and_malformed_amounts` | B_RECONCILE: NaN/Inf/negative amounts & float token counts | **PASSED** |
| 25 | `test_cli_subprocess_mismatched_journal_or_ledger_fails` | B_RECONCILE: public CLI failure on mutated journal/ledger | **PASSED** |
| 26 | `test_explicit_cost_denominators_and_excluded_views` | 3 explicit cost denominators & excluded views spend | **PASSED** |
| 27 | `test_study_wide_financial_accounting_and_pilot_hold` | Preserves prior pilot hold ($0.05264010) study-wide | **PASSED** |
| 28 | `test_cli_repository_root_resolution_from_external_cwd` | CLI defaults resolved against repo root from external CWD | **PASSED** |
| 29 | `test_pair_cluster_bootstrap_resampling` | Pair-cluster bootstrap resampling by `pair_id` | **PASSED** |
| 30 | `test_rq2_independent_failure_axes_and_no_rag_na` | RQ2 D2i independent axes, overlaps, and No-RAG N/A semantics | **PASSED** |
| 31 | `test_rq3_view_diagnostics_scorable_counts` | TEST split scorable view counts (278 single, 440 contextual) & true subset Macro-F1 | **PASSED** |
| 32 | `test_stratified_gt_complexity_producer` | Evaluator proposed producer: true subset Macro-F1 for single-GT and multi-GT, delta, and overall reference | **PASSED** |
| 33 | `test_subset_macro_f1_distinct_fixture_edge_cases` | Mathematical distinctness of subset Macro-F1 on `_fixture_474`, empty/null subsets, discordant predictions, multi-label GT | **PASSED** |
| 34 | `test_mcnemar_test_statistical_properties` | McNemar chi2, exact binomial, odds ratio | **PASSED** |
| 35 | `test_rq1_controlled_comparison_computation` | RQ1 metrics, deltas, relative gains, pair-cluster CIs | **PASSED** |
| 36 | `test_run_rq_analysis_generates_all_artifacts` | Full analysis pipeline generating JSON & MD | **PASSED** |
| 37 | `test_native_tariff_positive_control_success` | B_NATIVE_TARIFF: Positive control computes exact native tariff ($0.00000370) | **PASSED** |
| 38 | `test_native_tariff_probe_rate_limit_charges_worst_case` | B_NATIVE_TARIFF: Probe rate limit charges worst case ($0.53974560) & detects undercharge | **PASSED** |
| 39 | `test_native_tariff_probe_missing_service_tier_breaches_fail_closed` | B_NATIVE_TARIFF: Missing service tier breaches fail-closed | **PASSED** |
| 40 | `test_native_tariff_probe_foreign_model_breaches_fail_closed` | B_NATIVE_TARIFF: Foreign model receipt breaches fail-closed | **PASSED** |
| 41 | `test_native_tariff_incomplete_status_with_tokens_computes_exact_tariff` | B_NATIVE_TARIFF: INCOMPLETE status with tokens computes token tariff | **PASSED** |
| 42 | `test_native_tariff_transport_failures_charged_worst_case` | B_NATIVE_TARIFF: TIMEOUT and API_FAILURE receipts charged worst attempt fee | **PASSED** |
| 43 | `test_native_tariff_final_receipt_drift_vs_record_breaches` | B_NATIVE_TARIFF: Final receipt drift vs record (tokens, response ID, model) breaches fail-closed | **PASSED** |
| 44 | `test_native_tariff_logical_worst_ceiling_breach_fails_closed` | B_NATIVE_TARIFF: Total cost exceeding logical worst ceiling ($2.15898240) breaches fail-closed | **PASSED** |
| 45 | `test_provenance_mode_boundary_diagnostic_fixture` | BD_MODE_BOUNDARY: Diagnostic fixture data retains explicit non-canonical provenance | **PASSED** |
| 46 | `test_provenance_mode_boundary_canonical_study_positive_control` | BD_MODE_BOUNDARY: Canonical live test data earns canonical_study status without warning | **PASSED** |

### 5.2 Test Execution Results
```bash
uv run pytest tests/test_evaluator_offline_contract.py -v
============================= 46 passed in 14.80s =============================

uv run pytest tests/test_experiment_evaluation.py -q
============================= 94 passed in 14.07s =============================

Combined Total: 140 passed in 25.12s (OFFLINE_GUARD: installed=True attempted_egress=0)
```

### 5.3 Code Quality & Linter Compliance
```bash
uv run ruff check scripts/analysis/evaluate_rqs.py tests/test_evaluator_offline_contract.py
All checks passed!

uv run ruff format --check scripts/analysis/evaluate_rqs.py tests/test_evaluator_offline_contract.py
2 files already formatted
```

---

## 6. Artifact Provenance & File Integrity

| File Path | SHA-256 Digest | Purpose |
| :--- | :--- | :--- |
| `scripts/analysis/evaluate_rqs.py` | `c48eeb27b19626344e5f10b2cac674437b4053bb01f014060905702c52235f95` | Offline RQ1/RQ2/RQ3 analysis script with B_NATIVE_TARIFF_REPAIR, BD_MODE_BOUNDARY, & UNIFIED_MAPPING_R2 |
| `scripts/analysis/__init__.py` | `28b40746d09b574e95393ac9e2a95879116cd9d4c7a86afb1be7be573f9ad54a` | Analysis package initializer |
| `tests/test_evaluator_offline_contract.py` | `3171b7fecbe351741b03e8ae2bf49397d9b3a5f8eda4abe9e62195a6f820252f` | Evaluator offline contract test suite (46 tests) with distinct 474 known-answer rational assertions |
| `artifacts/orchestration/fixture_export_schema_3625.json` | `b478cc9fcd71ce1cf88d00f079dd7b2f399091bb976ae2993a635963ab69762b` | Fresh fixture export schema with 1,679 leaf pointers bound to `evaluate_rqs.py` SHA-256 |
| `reports/evidence/evaluator_contract_and_analysis_plan.md` | *This document* | Comprehensive Phase S1 evidence document |

---

## 7. Protocol Compliance Checklist

- [x] PRE_SHA verified: `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`
- [x] Strictly ZERO live provider/API calls executed (0 egress).
- [x] In-flight live matrix untouched; zero scores generated for live runs.
- [x] Core evaluator frozen in `src/evaluation/experiment_metrics.py` untouched.
- [x] Verified 5 conditions matrix (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`).
- [x] Verified fixed 474-class Macro-F1 denominator (`FROZEN_BENCHMARK_UNIVERSE`) with distinguishing test.
- [x] Verified D2a ANY_MATCH multi-GT semantics.
- [x] Verified D2b/D2c unmapped (251) and ambiguous (311) ground truth exclusions.
- [x] Verified D2e/D2f end-to-end failure denominators (invalid IDs and API failures penalized).
- [x] Verified D2g invalid syntax vs unknown vs retired ID diagnostics.
- [x] Verified D2i independent failure axes without forced mutual exclusion or causal partitioning claims.
- [x] Verified D2j NULL zero denominators.
- [x] Completed Codex Review Repair 1: Strict pricing configuration validation (fail-closed, no zero fallback).
- [x] Completed Codex Review Repair 2 (B_RECONCILE_REPAIR2): Full ledger and journal reconciliation with hash binding, read-only ledger validation, probe fail-closed, and 10 distinguishing mutation regressions.
- [x] Completed Codex Review Repair (B_NATIVE_TARIFF_REPAIR): Direct delegation to native frozen `calculate_request_cost_from_receipts`, `RecordObjectAdapter`, fail-closed breach propagation, and 8 dedicated tests (positive control, worst-case fee on transport/rate-limit, missing service tier, foreign model, `INCOMPLETE` with tokens, final receipt drift, ceiling breach).
- [x] Completed Codex Review Repair (BD_MODE_BOUNDARY): Execution-mode boundary and honest provenance tracking implemented in `run_rq_analysis` and `generate_rq_markdown_report`, backed by diagnostic fixture and canonical positive control tests.
- [x] Completed Codex Review Repair 3: Three explicit cost denominators and excluded views spend disclosure.
- [x] Completed Codex Review Repair 4: Robust CLI root resolution (`--repository-root`).
- [x] Completed Codex Review Repair 5: Distinguishing known-answer 474-class Macro-F1 test.
- [x] Completed Codex Review Repair 6: Comprehensive regression suite for tariffs, retries, and malformed inputs.
- [x] Completed Codex Review Repair 7: Pair-cluster bootstrap resampling by `pair_id` and exact view counts (278 single, 440 contextual).
- [x] Completed Codex Review Repair 8: RQ2 D2i independent failure axes, overlap accounting, and No-RAG N/A semantics.
- [x] Completed Codex Review Round 3 (UNIFIED_MAPPING_R2): True subset Macro-F1 calculated across 474-class universe for view diagnostics (single-view N=278, contextual-view N=440) and GT complexity (single-GT N=678, multi-GT N=40), overall reference Macro-F1 clearly labeled.
- [x] Completed Codex Review B362: Distinct known-answer 474 fixture (`_fixture_474_discordant_known_answer`) with exact closed-form rational fraction assertions (single-view 5/1422, contextual-view 8/1422, overall 19/2844, single-GT 10/1422, multi-GT 1/474), mathematical divergence assertions from overall Macro-F1, and fresh schema generation (`fixture_export_schema_3625.json`) with matching source hash.
- [x] Full test suite passed (46/46 offline contract tests, 94/94 evaluation suite tests; 140 total).
- [x] Ruff lint and format checks passed with zero errors (`line-length = 100`).
