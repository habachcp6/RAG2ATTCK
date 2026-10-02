# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)

- **Experiment ID**: `synthetic-paired-test-1`
- **Manifest SHA-256**: `2f81076c4cfc3d3bd88b6bfe4b6e39775b8ed398a5623eaa603691cb277a9178`
- **Protocol Version**: `experiment-protocol-v1.1` (`d3bf3d31ad30...`)
- **Analysis Tool Version**: `2.0.0`
- **Execution Mode**: `live`
- **Dataset Split / Scope**: `test`
- **Provenance Status**: `canonical_study`
- **Report Generated**: `2026-10-02T04:32:51.956332+00:00`

---

## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)

> *Does retrieval augmentation improve exact technique attribution over unaugmented LLM?*

| Condition | End-to-End Acc | 95% CI (Cluster) | Macro-F1 (474) | Delta Acc vs No-RAG | 95% CI Delta | McNemar p (exact) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 0.7799 | [0.7464, 0.8088] | 0.0126 | Baseline | - | - |
| `rag_k1` | 0.7702 | [0.7350, 0.8017] | 0.0127 | -0.0097 (-1.2%) | [-0.0319, +0.0112] | 4.3499e-01 |
| `rag_k3` | 0.7855 | [0.7500, 0.8174] | 0.0136 | +0.0056 (+0.7%) | [-0.0279, +0.0393] | 7.7696e-01 |
| `rag_k5` | 0.7883 | [0.7507, 0.8235] | 0.0139 | +0.0084 (+1.1%) | [-0.0293, +0.0460] | 6.7707e-01 |
| `rag_k10` | 0.7953 | [0.7581, 0.8285] | 0.0140 | +0.0153 (+2.0%) | [-0.0235, +0.0530] | 4.2194e-01 |

- **Best RAG Condition**: `rag_k10` (+0.0153 accuracy delta vs No-RAG)
- **Note on Statistical Tests**: Pair-cluster bootstrap resampling resamples paired views sharing `pair_id` together, preserving intra-pair correlation. These tests are exploratory diagnostics and do not alter frozen headline protocol metrics.

---

## RQ2: Retrieval vs. Generation Error Decomposition

> *Independent diagnostic failure axes and overlap analysis (Decision D2i).* *Hit/Recall and conditional metrics are not applicable to No-RAG.*

| Condition | k | Recall@k | Hit@k | P(Corr | Hit) | P(Corr | Miss) | Ret Miss | Wrong Class | Prov Fail | Parse Fail | Invalid ID |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 0 | - | - | - | - | - | 158 | 0 | 0 | 0 |
| `rag_k1` | 1 | 0.0295 | 0.0376 | 1.0000 | 0.7612 | 691 | 165 | 0 | 0 | 0 |
| `rag_k3` | 3 | 0.1548 | 0.1643 | 0.9746 | 0.7483 | 600 | 154 | 0 | 0 | 0 |
| `rag_k5` | 5 | 0.2296 | 0.2409 | 0.9711 | 0.7303 | 545 | 152 | 0 | 0 | 0 |
| `rag_k10` | 10 | 0.4280 | 0.4471 | 0.9128 | 0.7003 | 397 | 147 | 0 | 0 | 0 |

- **Note on Independent Failure Axes**: Evaluated independently per Decision D2i without forced mutual exclusion or unapproved causal attribution. Overlaps are explicitly tracked in JSON outputs. Retrieval metrics are not applicable to No-RAG.

---

## RQ3: Retrieval Depth, Latency, and Cost Trade-offs

> *What is the resource trade-off across candidate depths k in {1, 3, 5, 10}?*

| Condition | k | Mean Lat (ms) | Mean Tokens | Total Cost ($) | Cost / Logical ($) | Cost / Scorable ($) | Cost / Corr ($) | Excluded ($) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 0 | 2904.5 | 838.0 | $0.46714 | $0.00036 | $0.00065 | $0.00083 | $0.19006 |
| `rag_k1` | 1 | 3514.3 | 1480.2 | $1.29723 | $0.00101 | $0.00181 | $0.00235 | $0.34063 |
| `rag_k3` | 3 | 4215.9 | 2487.3 | $1.17888 | $0.00092 | $0.00164 | $0.00209 | $0.57570 |
| `rag_k5` | 5 | 4327.3 | 3388.2 | $1.48312 | $0.00116 | $0.00207 | $0.00262 | $0.67084 |
| `rag_k10` | 10 | 4370.7 | 5448.1 | $2.14938 | $0.00168 | $0.00299 | $0.00376 | $0.96463 |

### Study-Wide Financial Accounting

- **Total Study Budget**: `$19.99000000`
- **Canonical Conditions Cost**: `$6.57575890`
- **Prior Pilot Provisional Hold**: `$0.05264010`
- **Active Reservations**: `$0.00000000`
- **Total Committed Spend**: `$6.62839900`
- **Net Available Uncommitted Budget**: `$13.36160100`
- **Study-Wide Missing Usage Charges**: 0 terminal records, 1 attempt receipts ($0.53974560)
- **Study-Wide Retried Attempts**: 1
- **Financial Policy**: Prior pilot provisional hold ($0.05264010) is accounted exclusively at the whole-study level and is never allocated to individual canonical conditions. Spending on excluded ambiguous and unmapped views is fully accounted as real monetary spend.

### Paired View Diagnostics (Single-View vs Contextual-View)

> *TEST split scorable cohort contains 278 single views and 440 contextual views.* *Complete paired analysis evaluates the 278 pairs where both views are scorable.*

| Condition | Single Acc | Single F1 (474) | Ctx Acc | Ctx F1 (474) | Single Paired Acc | Ctx Paired Acc | Paired Delta (Ctx - Sgl) | Both Corr | Ctx Win | Sgl Win | Both Incorr |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 0.8705 | 0.0133 | 0.7227 | 0.0120 | 0.8705 | 0.9245 | +0.0540 | 228 | 29 | 14 | 7 |
| `rag_k1` | 0.8561 | 0.0131 | 0.7159 | 0.0121 | 0.8561 | 0.9245 | +0.0683 | 229 | 28 | 9 | 12 |
| `rag_k3` | 0.8417 | 0.0129 | 0.7500 | 0.0130 | 0.8417 | 0.8885 | +0.0468 | 225 | 22 | 9 | 22 |
| `rag_k5` | 0.8345 | 0.0129 | 0.7591 | 0.0131 | 0.8345 | 0.8525 | +0.0180 | 221 | 16 | 11 | 30 |
| `rag_k10` | 0.8381 | 0.0129 | 0.7682 | 0.0132 | 0.8381 | 0.8381 | +0.0000 | 216 | 17 | 17 | 28 |

#### Complete Pair Ground Truth Concordance Decomposition

> *Stratification of complete scorable pairs (N=278) by ground truth technique label concordance:*
> *Identical GT: pairs where single and contextual view share identical ground truth technique labels (N=238).* 
> *Divergent GT: pairs where single and contextual view annotate distinct ground truth technique labels (N=40).* 

| Condition | Identical Pairs | Ident Sgl Acc | Ident Ctx Acc | Ident Delta | Divergent Pairs | Div Sgl Acc | Div Ctx Acc | Div Delta |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 238 | 0.9202 | 0.9328 | +0.0126 | 40 | 0.5750 | 0.8750 | +0.3000 |
| `rag_k1` | 238 | 0.9118 | 0.9118 | +0.0000 | 40 | 0.5250 | 1.0000 | +0.4750 |
| `rag_k3` | 238 | 0.8908 | 0.8697 | -0.0210 | 40 | 0.5500 | 1.0000 | +0.4500 |
| `rag_k5` | 238 | 0.8529 | 0.8277 | -0.0252 | 40 | 0.7250 | 1.0000 | +0.2750 |
| `rag_k10` | 238 | 0.8571 | 0.8109 | -0.0462 | 40 | 0.7250 | 1.0000 | +0.2750 |

---

## NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis

> [!IMPORTANT]
> **Protocol Approval Required**: This is an exploratory proposed producer that evaluates scorable views partitioned into Single-GT (N=678 on TEST) vs Multi-GT (N=40 on TEST under Decision D2a ANY_MATCH). Macro-F1 is evaluated across the frozen 474-class benchmark universe. Explicit supervisor authorization is required prior to canonical reporting inclusion.

| Condition | Single-GT (N) | Single-GT Acc | Single-GT F1 (474) | Multi-GT (N) | Multi-GT Acc (ANY_MATCH) | Multi-GT F1 (474) | Complexity Delta (Acc) | Overall Scorable Acc | Overall F1 (Ref) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 678 | 0.7743 | 0.0130 | 40 | 0.8750 | 0.0070 | +0.1007 | 0.7799 | 0.0126 |
| `rag_k1` | 678 | 0.7566 | 0.0130 | 40 | 1.0000 | 0.0083 | +0.2434 | 0.7702 | 0.0127 |
| `rag_k3` | 678 | 0.7729 | 0.0140 | 40 | 1.0000 | 0.0086 | +0.2271 | 0.7855 | 0.0136 |
| `rag_k5` | 678 | 0.7758 | 0.0143 | 40 | 1.0000 | 0.0089 | +0.2242 | 0.7883 | 0.0139 |
| `rag_k10` | 678 | 0.7832 | 0.0144 | 40 | 1.0000 | 0.0085 | +0.2168 | 0.7953 | 0.0140 |
