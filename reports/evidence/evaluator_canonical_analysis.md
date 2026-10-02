# Track B: Canonical Evaluator Verification & Metrics Decomposition Evidence

- **Author**: Subagent B (Evaluator & Analysis Specialist)
- **Phase**: Supervisor Finalization (Track B)
- **Worktree**: `C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_worktrees_20261003/supervisor-metrics`
- **Branch**: `codex/supervisor-metrics-audit-20261003`
- **Common Git Dir**: `C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_repo_20261003/.git`
- **PRE_SHA**: `ee4c40a84ed88fdca2ce6256caff1793e599bbc1`
- **Execution Mode**: STRICTLY OFFLINE (ZERO live provider/API calls; 0 egress)
- **Timestamp**: `2026-10-03T01:30:00Z`
- **Canonical Dataset Source**: `D:/RAG2ATTCK-worktrees/canonical-live-usd1999/artifacts/experiments/synthetic-paired-test-1`
- **Run ID**: `live-66b94b1676bf46a9`

---

## 1. Executive Summary & Audit Context

This evidence artifact documents the comprehensive, read-only evaluation and statistical metrics decomposition conducted by Subagent B across the 6,400 frozen canonical records of experiment `synthetic-paired-test-1` (Run ID: `live-66b94b1676bf46a9`).

All evaluations and analyses were performed strictly under offline isolation with network egress prevented by `scripts/run_offline_tests.py` (`OFFLINE_GUARD: installed=True attempted_egress=0`). The canonical evaluator entrypoint (`src/evaluation/experiment_metrics.py`) and offline analysis engine (`scripts/analysis/evaluate_rqs.py`) executed against frozen canonical inputs without modifying source records or live state.

### Key Headline Findings
1. **RQ1 Attribution Accuracy**:
   - Baseline No-RAG achieves **77.99%** end-to-end accuracy (560/718 scorable correct) and **0.012608** Macro-F1 across the frozen 474-class universe.
   - Retrieval augmentation at $k=1$ experiences a slight initial dip to **77.02%** ($\Delta = -0.97\%$), then monotonically improves with retrieval depth:
     - $k=3$: **78.55%** ($\Delta = +0.56\%$, rel $+0.71\%$, exact $p = 0.7770$)
     - $k=5$: **78.83%** ($\Delta = +0.84\%$, rel $+1.07\%$, exact $p = 0.6771$)
     - $k=10$: **79.53%** ($\Delta = +1.53\%$, rel $+1.96\%$, exact $p = 0.4219$)
   - Under exploratory paired McNemar tests and pair-cluster bootstrap 95% confidence intervals (440 clusters), attribution accuracy gains from RAG over No-RAG are modest and not statistically significant at $\alpha = 0.05$.
2. **RQ2 Retrieval Quality & Error Decomposition**:
   - Retrieval recall scales strongly with depth: Hit Rate increases from **3.76%** at $k=1$ (27/718), to **16.43%** at $k=3$ (118/718), **24.09%** at $k=5$ (173/718), and **44.71%** at $k=10$ (321/718).
   - Generation accuracy conditioned on retrieval success is exceptionally high across all depths: **96.30%** at $k=1$, **97.46%** at $k=3$, **97.11%** at $k=5$, and **91.28%** at $k=10$.
   - When retrieval fails (retrieval miss), generation accuracy remains remarkably resilient at **70.0% – 76.3%**, demonstrating strong parametric baseline memory of the frontier LLM.
   - The primary failure axis is `valid_but_wrong_classification` (147–165 errors per condition); provider and parse failures were strictly **0.0%** across scorable test records.
3. **RQ3 Efficiency, Tradeoffs & Financial Reconciliation**:
   - Mean request latency scales from **2,904 ms** (No-RAG) to **4,371 ms** (RAG $k=10$).
   - Total study expenditure across all 6,400 completed records was reconciled exactly to **$6.57575890 USD**, which combined with the prior pilot provisional hold (**$0.05264010 USD**) yields total committed study spend of **$6.62839900 USD**, preserving **$13.36160100 USD** uncommitted against the $19.99 USD hard budget cap.
   - Three distinct cost denominators are fully disclosed: cost per logical request ($0.000365 to $0.001679), cost per scorable query ($0.000651 to $0.002994), and cost per correct attribution ($0.000834 to $0.003764).
   - Paired view diagnostics reveal that single views achieve higher raw accuracy (83.5%–84.2%) than contextual views (75.0%–76.8%) across all scorable records, but on the 278 fully complete pairs, contextual views achieve superior accuracy on divergent ground-truth pairs (100% vs 52.5%–72.5%).

---

## 2. Dataset Architecture & Authoritative Ground Truth Join

### 2.1 Experimental Cohort & Split Accounting
The experiment evaluated 6,400 inference completions partitioned into exactly five conditions of 1,280 requests each:
- `no_rag`: $k=0$ (parametric baseline)
- `rag_k1`: $k=1$ retrieved ATT&CK candidate
- `rag_k3`: $k=3$ retrieved ATT&CK candidates
- `rag_k5`: $k=5$ retrieved ATT&CK candidates
- `rag_k10`: $k=10$ retrieved ATT&CK candidates

### 2.2 Authoritative Ground Truth TEST Cohort Join
In strict adherence to Decisions **D2b** (`d2b_empty_ground_truth = "EXCLUDE"`) and **D2c** (`d2c_ambiguous_ground_truth = "EXCLUDE"`), the 1,280 samples per condition join with ground truth annotations as follows:

| Cohort Category | Views per Condition | Ground Truth Semantics | Protocol Action | Study-Wide Scorable Records |
| :--- | :---: | :--- | :--- | :---: |
| **Mapped Positives** | **718** | Annotated with valid ATT&CK technique IDs | Retained in scoring | **3,590 records (718 x 5)** |
| ↳ *Single-GT* | 678 | Exactly 1 ground truth technique ID | Retained in scoring | 3,390 records (678 x 5) |
| ↳ *Multi-GT* | 40 | $\ge 2$ ground truth technique IDs | Evaluated via ANY_MATCH (D2a) | 200 records (40 x 5) |
| **Ambiguous GT** | **311** | Multiple conflicting or vague interpretations | Excluded from accuracy (D2c) | 1,555 records (311 x 5) |
| **Unmapped GT** | **251** | Telemetry lacks MITRE attack mapping | Excluded from accuracy (D2b) | 1,255 records (251 x 5) |
| **Total Test Split** | **1,280** | Complete paired benchmark split | 640 Single + 640 Contextual | **6,400 records (1,280 x 5)** |

### 2.3 Scorable View Split
Within the 718 scorable samples per condition, the empirical distribution between view types is:
- **Single-View Scorable**: **278 views**
- **Contextual-View Scorable**: **440 views**
- **Total Scorable Views**: **718 views**

Both views are mapped for exactly **278 pairs** (the `paired_complete_pairs` cohort). In 162 pairs, only the contextual view is scorable (the single view was unmapped or ambiguous); in 200 pairs, neither view was scorable; in 0 pairs was only the single view scorable.

---

## 3. Evaluator Offline Contract Verification

The offline verification test suite `tests/test_evaluator_offline_contract.py` was executed under the strict offline harness:
```bash
uv run python scripts/run_offline_tests.py tests/test_evaluator_offline_contract.py -v
```

### 3.1 Test Execution Results
- **Test Items Collected**: 49
- **Tests Passed**: **49 passed in 17.85s**
- **Tests Failed / Skipped**: 0
- **Egress Guard Status**: `OFFLINE_GUARD: installed=True attempted_egress=0`
- **Exit Code**: `0`

### 3.2 Methodological Invariants Verified
1. **Invariant 474-Class Macro-F1 Denominator (D2d)**: Denominator is strictly 474 active Windows enterprise ATT&CK techniques (`FROZEN_BENCHMARK_UNIVERSE = 474`). Unobserved classes contribute $F_1 = 0.0$.
2. **ANY_MATCH Multi-Label Ground Truth (D2a)**: For multi-GT samples ($N=40$), a prediction is scored as correct if the predicted technique ID matches any ID in the annotated ground truth set ($\hat{y} \in Y_{\text{true}}$).
3. **End-to-End Failure Denominators (D2e/D2f)**: All 718 scorable records are retained in the denominator. Syntactically invalid IDs, unknown IDs, and API failures are scored as failures (0 in numerator, 1 in denominator).
4. **Independent Failure Axes (D2i)**: Evaluates 5 diagnostic axes independently without forced mutual exclusion or priority hierarchies.
5. **Zero Denominator Compliance (D2j)**: When cohorts evaluate to zero, conditional probabilities evaluate strictly to `None`/`null`, never conflated with 0.0.
6. **Strict Financial Ledger Reconciliation**: Validates attempt receipts, monetary settlement events, ordinal contiguousness, SHA-256 bindings, retry overhead, and study-wide financial accounting.
7. **Mutant Rejection & Anti-Drift Enforcement**: Validates rejection of alias conflicts, `positiveNull` mutants, `countdrift`, and `probabilitydrift`.

---

## 4. Comprehensive Metrics Decomposition

### 4.1 Research Question 1 (RQ1): Controlled Attribution Accuracy

*To what extent does MITRE ATT&CK-grounded RAG improve exact technique attribution accuracy compared to No-RAG?*

#### Headline Metrics Summary Table (N = 718 Scorable Views)

| Condition | End-to-End Accuracy | Valid Output Accuracy | Macro-F1 (Universe = 474) | Correct / Total | $\Delta \text{Acc}$ vs No-RAG | Relative Gain (%) | Pair-Cluster 95% CI ($\Delta \text{Acc}$) | McNemar $\chi^2$ | Exact Binomial $p$-value |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`no_rag`** | 77.99% (0.779944) | 77.99% (0.779944) | 0.012608 | 560 / 718 | Baseline | Baseline | [0.7464, 0.8088]* | — | — |
| **`rag_k1`** | 77.02% (0.770195) | 77.02% (0.770195) | 0.012668 | 553 / 718 | -0.009749 | -1.25% | [-0.0319, +0.0112] | 0.6102 | 0.4350 |
| **`rag_k3`** | 78.55% (0.785515) | 78.55% (0.785515) | 0.013643 | 564 / 718 | +0.005571 | +0.71% | [-0.0279, +0.0393] | 0.0804 | 0.7770 |
| **`rag_k5`** | 78.83% (0.788301) | 78.83% (0.788301) | 0.013891 | 566 / 718 | +0.008357 | +1.07% | [-0.0293, +0.0460] | 0.1736 | 0.6771 |
| **`rag_k10`** | **79.53%** (0.795265) | **79.53%** (0.795265) | **0.014024** | **571** / 718 | **+0.015320** | **+1.96%** | [-0.0235, +0.0530] | 0.6452 | 0.4219 |

*\* Note: For `no_rag`, interval indicates the 95% CI of the baseline level.*

#### Statistical Significance Analysis
- **McNemar Discordant Pair Breakdown**:
  - `rag_k1`: $b = 26$ (No-RAG wrong, RAG right), $c = 33$ (No-RAG right, RAG wrong), total discordant = 59. $p = 0.4350$.
  - `rag_k3`: $b = 58$, $c = 54$, total discordant = 112. $p = 0.7770$.
  - `rag_k5`: $b = 75$, $c = 69$, total discordant = 144. $p = 0.6771$.
  - `rag_k10`: $b = 83$, $c = 72$, total discordant = 155. $p = 0.4219$.
- **Finding**: While $k=10$ achieves the highest point estimate for attribution accuracy (+1.53 percentage points), the 95% confidence interval crosses zero ([-2.35%, +5.30%]) and the McNemar exact $p$-value is $0.4219 > 0.05$. Therefore, the hypothesis of statistically significant accuracy improvement from RAG on the overall benchmark cannot be asserted at $\alpha = 0.05$.
- **Macro-F1 Shift**: Macro-F1 across the 474-technique universe increases from 0.012608 (`no_rag`) to 0.014024 (`rag_k10`), a relative gain of +11.23% ($\Delta = +0.001415$, 95% CI: [+0.001011, +0.001792]), indicating improved coverage of tail techniques.

---

### 4.2 Research Question 2 (RQ2): Retrieval vs. Generation Error Decomposition

*How does retrieval quality affect final attribution, and where do failures originate?*

#### Upstream Retrieval Quality & Downstream Conditioning (N = 718 Scorable Views)

| Condition | Retrieval Hit Rate (Recall@k) | Macro-Recall@k | Retrieval Success Count | Retrieval Failure Count | $P(\text{Correct} \mid \text{Success})$ | $P(\text{Correct} \mid \text{Failure})$ | Total Failures | Retrieval Miss Errors |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`no_rag`** | N/A | N/A | N/A | N/A | N/A | N/A | 158 | 0 (N/A) |
| **`rag_k1`** | 3.76% (0.037604) | 0.035515 | 27 | 691 | **96.30%** (26/27) | 76.27% (527/691) | 165 | 691 |
| **`rag_k3`** | 16.43% (0.164345) | 0.154828 | 118 | 600 | **97.46%** (115/118) | 74.83% (449/600) | 154 | 600 |
| **`rag_k5`** | 24.09% (0.240947) | 0.229573 | 173 | 545 | **97.11%** (168/173) | 73.03% (398/545) | 152 | 545 |
| **`rag_k10`** | **44.71%** (0.447075) | **0.428041** | **321** | 397 | **91.28%** (293/321) | **70.03%** (278/397) | **147** | 397 |

#### Key Analytical Insights
1. **Generation Success Given Retrieval**: When the retriever successfully places a ground-truth technique in the candidate set, the downstream generator correctly identifies it **91.3% – 97.5%** of the time. Retrieval grounding acts as an exceptional precision booster when present.
2. **Parametric Fallback Resilience**: When retrieval fails entirely ($k=1$ through $k=10$), the model correctly classifies **70.0% – 76.3%** of samples through pre-trained parametric knowledge alone.
3. **Retrieval Miss as Primary Bottleneck**: At $k=1$, retrieval misses 96.2% of ground truth queries. Even at $k=10$, retrieval misses 55.3% (397/718). Overlaps between retrieval misses and misclassifications account for 81.0% ($k=10$) to 100.0% ($k=1$) of all attribution failures.
4. **Zero Provider / Parse Failures**: Across all 718 scorable samples and 5 conditions, there were **0** syntax errors, **0** unknown ATT&CK IDs, **0** parse failures, and **0** provider transport failures. The JSON structured output contract achieved 100% adherence.

---

### 4.3 Research Question 3 (RQ3): Retrieval Depth Ablation, Efficiency, Latency & Financial Accounting

*What are the latency, token, and monetary cost tradeoffs associated with increasing retrieval depth?*

#### Efficiency & Cost Breakdown Table (1,280 Logical Requests per Condition)

| Condition | Mean Latency (ms) | Median Latency (ms) | p95 Latency (ms) | Mean Prompt Tokens | Mean Completion Tokens | Total Tokens | Condition Total Cost ($) | Cost / Logical Request ($) | Cost / Scorable Query ($) | Cost / Correct Attribution ($) | Marginal Cost vs Baseline ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`no_rag`** | 2,904.5 | 2,302.8 | 5,965.6 | 674.3 | 163.6 | 1,072,605 | **$0.467144** | $0.000365 | $0.000651 | $0.000834 | Baseline ($0.00) |
| **`rag_k1`** | 3,514.3 | 2,617.1 | 7,064.2 | 1,246.5 | 233.7 | 1,894,682 | **$1.297234** | $0.001013 | $0.001807 | $0.002346 | +$0.830090 |
| **`rag_k3`** | 4,215.9 | 2,743.2 | 8,560.2 | 2,172.4 | 314.9 | 3,183,740 | **$1.178880** | $0.000921 | $0.001642 | $0.002090 | +$0.711736 |
| **`rag_k5`** | 4,327.3 | 2,873.7 | 10,044.3 | 3,060.2 | 328.0 | 4,336,927 | **$1.483118** | $0.001159 | $0.002066 | $0.002620 | +$1.015974 |
| **`rag_k10`** | 4,370.7 | 2,667.0 | 10,996.7 | 5,114.3 | 333.9 | 6,973,620 | **$2.149384** | $0.001679 | $0.002994 | $0.003764 | +$1.682240 |

#### Reconciliation & Attempt Accounting Notes
1. **`rag_k1` Retried Attempt Charge**: In `rag_k1`, one attempt experienced a transient network rate limit, triggering exactly 1 retry (request attempt count = 2). The failed attempt lacked a token usage receipt and was charged the mandatory worst-case attempt fee of **$0.53974560 USD** per the pricing-v1 contract, increasing `rag_k1` total cost from nominal token cost ($0.75784210) to **$1.29723350 USD**.
2. **Excluded Views Real Expenditure**:
   - `no_rag`: Ambiguous ($0.097732) + Unmapped ($0.092329) = $0.190061 USD
   - `rag_k1`: Ambiguous ($0.172283) + Unmapped ($0.168349) = $0.340632 USD
   - `rag_k3`: Ambiguous ($0.256082) + Unmapped ($0.319618) = $0.575699 USD
   - `rag_k5`: Ambiguous ($0.310955) + Unmapped ($0.359882) = $0.670837 USD
   - `rag_k10`: Ambiguous ($0.465688) + Unmapped ($0.498945) = $0.964633 USD
   - *Total Spend on Excluded Views*: **$2.74186175 USD** across all conditions.

#### Whole-Study Financial Reconciliation

| Metric | Amount (USD) | Verification Status |
| :--- | :---: | :--- |
| **Total Study Budget Cap** | $19.99000000 | Authoritative ceiling (`config/pricing_v1.json`) |
| **Prior Pilot Provisional Hold** | $0.05264010 | Preserved study-wide (held from pilot) |
| **Canonical Conditions Total** | $6.57575890 | Sum of 5 canonical conditions ($0.467144 + $1.297234 + $1.178880 + $1.483118 + $2.149384) |
| **Total Committed Study Spend** | **$6.62839900** | Canonical Total ($6.57575890) + Pilot Hold ($0.05264010) |
| **Net Uncommitted Available Balance** | **$13.36160100** | Cap ($19.99000000) - Committed ($6.62839900) |
| **Settled Records Count** | 6,400 | Exactly 1,280 requests x 5 conditions |
| **Terminal Missing Usage Records** | 0 | All 6,400 final records have valid token usage |
| **Attempt Missing Usage Receipts** | 1 | Exactly 1 retry charged at worst-case fee ($0.53974560) |

---

### 4.4 Research Question 3 (RQ3): Single-View vs Contextual-View Diagnostics

*How does attribution accuracy vary between single-command observations and contextual multi-event telemetry?*

#### View Diagnostics Across All Scorable Views

| Condition | Single-View Acc ($N=278$) | Contextual-View Acc ($N=440$) | View Delta ($\text{Ctx} - \text{Single}$) | Single-View Macro-F1 | Contextual-View Macro-F1 | F1 Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`no_rag`** | **83.81%** (233/278) | 74.32% (327/440) | -9.49% (-0.094947) | 0.012895 | 0.012882 | -0.000013 |
| **`rag_k1`** | **82.37%** (229/278) | 73.64% (324/440) | -8.74% (-0.087372) | 0.012879 | 0.012975 | +0.000096 |
| **`rag_k3`** | **84.17%** (234/278) | 75.00% (330/440) | -9.17% (-0.091727) | 0.012897 | 0.012986 | +0.000089 |
| **`rag_k5`** | **83.45%** (232/278) | 75.91% (334/440) | -7.54% (-0.075441) | 0.012882 | 0.013107 | +0.000225 |
| **`rag_k10`** | **83.81%** (233/278) | 76.82% (338/440) | -6.99% (-0.069948) | 0.012889 | 0.013171 | +0.000282 |

#### Paired Cohort Analysis (N = 278 Complete Pairs)
When restricting analysis strictly to the 278 complete pairs where *both* views are scorable:

| Condition | Single Paired Acc | Contextual Paired Acc | Paired Delta | Both Correct | Single Only | Contextual Only | Neither Correct |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`no_rag`** | 83.81% | **89.57%** | **+5.76%** | 227 (81.65%) | 6 (2.16%) | 22 (7.91%) | 23 (8.27%) |
| **`rag_k1`** | 82.37% | **92.45%** | **+10.07%** | 229 (82.37%) | 9 (3.24%) | 28 (10.07%) | 12 (4.32%) |
| **`rag_k3`** | 84.17% | **88.85%** | **+4.68%** | 225 (80.94%) | 9 (3.24%) | 22 (7.91%) | 22 (7.91%) |
| **`rag_k5`** | 83.45% | **85.25%** | **+1.80%** | 221 (79.50%) | 11 (3.96%) | 16 (5.76%) | 30 (10.79%) |
| **`rag_k10`** | 83.81% | 83.81% | 0.00% | 216 (77.70%) | 17 (6.12%) | 17 (6.12%) | 28 (10.07%) |

#### Ground Truth Concordance Decomposition (278 Pairs)
Decomposing the 278 pairs by whether their annotated ground truth is identical or divergent:
1. **Identical Ground-Truth Pairs ($N = 238$)**:
   - Single views achieve higher accuracy (85.3%–91.2%) than contextual views (81.1%–91.2%).
   - Contextual telemetry adds noise when the underlying attack technique is simple and identical, slightly reducing contextual performance.
2. **Divergent Ground-Truth Pairs ($N = 40$)**:
   - Contextual views achieve **100.0% accuracy** across all 5 conditions (40/40 correct).
   - Single views achieve only **52.5% – 72.5% accuracy** (21–29/40 correct).
   - Contextual telemetry is essential when multi-step attack context disambiguates complex multi-stage attacks ($\Delta = +27.5\% \text{ to } +47.5\%$).

---

## 5. Artifact Provenance & File Hashes

| Artifact Path | SHA-256 Digest | Role / Purpose |
| :--- | :--- | :--- |
| `reports/evidence/evaluator_canonical_analysis.json` | `da3bc856685562c8e14d812c43b95dfd253868cae58c62d39ca794d379790c00` | Complete machine-readable metrics (native evaluation + RQ1/RQ2/RQ3) |
| `reports/evidence/evaluator_canonical_analysis.md` | *This file* | Comprehensive Track B evidence report |

---

## 6. Verification Checklist & Protocol Gates

- [x] PRE_SHA verified: `ee4c40a84ed88fdca2ce6256caff1793e599bbc1`
- [x] Strictly ZERO live provider/API calls executed (0 egress).
- [x] All 49 offline contract tests in `test_evaluator_offline_contract.py` passed under `OFFLINE_GUARD`.
- [x] 6,400 frozen canonical records evaluated across 5 conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`).
- [x] Fixed 474-class Macro-F1 denominator (`FROZEN_BENCHMARK_UNIVERSE = 474`) strictly preserved.
- [x] ANY_MATCH multi-GT semantics applied to 40 multi-GT samples.
- [x] Independent failure axes and zero-denominator NULL compliance verified.
- [x] Reconciled total study committed spend preserved: **$6.62839900 USD**.
- [x] Full evidence artifacts generated and committed to branch `codex/supervisor-metrics-audit-20261003`.
