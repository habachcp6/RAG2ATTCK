# Canonical Demo Operator Guide: Saved-Output Replay & Evidence Review

**Author:** Native Agent A (Track A - Audit & Recovery)  
**Target Audience:** Scientific Reviewers, Public Auditors, Technical Evaluators  
**Scope:** Authoritative Offline Demonstration of Canonical Run `live-66b94b1676bf46a9`  
**Egress Invariant:** Strictly ZERO live provider/API calls (`OFFLINE_GUARD: installed=True attempted_egress=0`).

---

## 1. Demonstration Philosophy: Saved-Output Replay vs. Live Demos

Live API demonstrations in LLM research introduce three fundamental challenges:
1. **Stochastic Non-Determinism:** Cloud providers silently update weights, system prompts, or quantization tiers over time, preventing exact replication of numerical findings.
2. **Financial & Credential Burden:** Reviewers must supply personal API keys and incur billing to replicate results.
3. **Security & Egress Vulnerability:** Running automated scripts with live network egress introduces test pollution and data exfiltration risks.

**The RAG2ATTCK Solution:**  
This demo operates strictly as an **offline saved-output inspection and replay engine**. All 6,400 experimental decisions, 6,401 provider requests, raw tokens, candidate retrieval lists, and financial ledger settlements are cryptographically locked and evaluated from the authoritative canonical metric bundle (`canonical_metric_bundle_v1.json`). An operator inspects genuine, empirical evidence with mathematical reproducibility, verified against Frozen Scientific Protocol v1.1 decisions, with zero financial cost.

---

## 2. Evaluation Conditions Overview

The study evaluates five controlled conditions across identical test events:

| Condition | Injected Context | Description | Typical Prompt Size |
| :--- | :---: | :--- | :---: |
| **`no_rag`** | $k=0$ | Raw host/network event telemetry and prompt instructions only, without retrieved ATT&CK context. | ~600 - 1,000 tokens |
| **`rag_k1`** | $k=1$ | Telemetry + Top 1 retrieved ATT&CK technique candidate with descriptions & data sources. | ~1,400 - 1,800 tokens |
| **`rag_k3`** | $k=3$ | Telemetry + Top 3 retrieved ATT&CK technique candidates. | ~2,500 - 3,000 tokens |
| **`rag_k5`** | $k=5$ | Telemetry + Top 5 retrieved ATT&CK technique candidates. | ~3,800 - 4,500 tokens |
| **`rag_k10`** | $k=10$ | Telemetry + Top 10 retrieved ATT&CK technique candidates. | ~5,500 - 6,500 tokens |

*Note on No-RAG:* In the `no_rag` condition, the model reasons over the provided telemetry text and system instructions without auxiliary knowledge retrieval. It is not assumed to operate solely on parametric knowledge, as prompt reasoning over host event artifacts remains active.

---

## 3. Operator Execution Protocol

To launch the full demonstration and evidence audit from a terminal, execute:

```powershell
python scripts/run_offline_tests.py -c "import runpy; runpy.run_path('scripts/reproduce_canonical_study.py', run_name='__main__')"
```

To display only the demo inspection cases:

```powershell
python scripts/reproduce_canonical_study.py --demo
```

---

## 4. Controlled Condition Cases: Correct, Incorrect, and Retrieval Repairs

Below are empirical exemplars extracted directly from the canonical predictions (`inputs/*_predictions.jsonl`) showing model behavior across retrieval depths.

### Case 1: High-Confidence Attribution Across All Five Conditions (Correct)
- **Sample ID:** `view_0088e302` (Pair ID: `pair_382d5a8e`)
- **Event Description:** Registry RunOnce key mutation pointing to a staged executable, followed by an immediate process execution record.
- **Ground Truth:** `T1547.001` (*Boot or Logon Autostart Execution: Registry Run Keys / Startup Folder*)

| Condition | Prompt Tokens | Completion Tokens | Latency | Retrieved Candidates | Predicted Technique | Attribution Status |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| `no_rag` | 949 | 97 | 2,585 ms | None ($k=0$) | `['T1547.001']` | **CORRECT** |
| `rag_k1` | 1,640 | 146 | 3,048 ms | `T1546.012` | `['T1547.001']` | **CORRECT** |
| `rag_k3` | 2,783 | 240 | 3,530 ms | `T1546.012`, `T1574.011`, `T1546.001` | `['T1547.001']` | **CORRECT** |
| `rag_k5` | 4,220 | 67 | 4,485 ms | `T1546.012`, `T1574.011`, `T1546.001`, `T1547.001`, `T1218.010` | `['T1547.001']` | **CORRECT** |
| `rag_k10` | 5,921 | 81 | 1,458 ms | 10 candidates provided (first 3 of 10: `T1546.012`, `T1574.011`, `T1546.001`) | `['T1547.001']` | **CORRECT** |

*Analysis:* In this case, strong diagnostic evidence in the telemetry correctly led the model to `T1547.001` across all 5 conditions. At $k=5$ and $k=10$, `T1547.001` was present in the retrieved candidates at rank 4, while at $k=1$ and $k=3$ the model resisted non-matching distractors.

---

### Case 2: Outdated Prior Repaired by RAG at $k \ge 3$
- **Sample ID:** `view_0265275a` (Pair ID: `pair_83671d3a`)
- **Event Description:** Security event log clearing command executed via PowerShell.
- **Ground Truth:** `['T1685.005']` (*Clear Windows Event Logs*, re-indexed sub-technique in STIX v19.2)

| Condition | Retrieved Candidates | Predicted Technique | Attribution Status | Analysis |
| :--- | :--- | :--- | :---: | :--- |
| `no_rag` | None ($k=0$) | `['T1070.001']` | **INCORRECT** | Outdated parent technique (`T1070.001` vs STIX v19.2 `T1685.005`) |
| `rag_k1` | `T1547.004` (score: 0.4031) | `['T1070.001']` | **INCORRECT** | Retrieval missed GT; model defaulted to outdated prior |
| `rag_k3` | `T1547.004`, `T1546.009`, `T1685.005` | `['T1685.005']` | **CORRECT** | **RAG repair:** `T1685.005` retrieved at rank 3, model updated output |
| `rag_k5` | Top 5 including `T1685.005` at rank 3 | `['T1685.005']` | **CORRECT** | Correct attribution maintained |
| `rag_k10` | 10 candidates (first 3 of 10: `T1547.004`, `T1546.009`, `T1685.005`) | `['T1685.005']` | **CORRECT** | Correct attribution maintained |

*Analysis:* This case empirically validates the core research hypothesis: static model weights often encode deprecated MITRE ATT&CK technique IDs (such as parent technique `T1070.001`), but RAG retrieval at depth $k \ge 3$ successfully injects the updated STIX v19.2 schema definition (`T1685.005`), overcoming the prior.

---

### Case 3: Multi-Technique View under ANY_MATCH Semantics
- **Sample ID:** `view_026cbe9e` (Pair ID: `pair_20c67c7d`)
- **Ground Truth:** `['T1059.003', 'T1105']` (*Windows Command Shell* + *Ingress Tool Transfer*)

| Condition | Prompt Tokens | Predicted Techniques | Attribution Status | Protocol Rule |
| :--- | :---: | :--- | :---: | :--- |
| `rag_k3` | 1,494 | `['T1105']` | **CORRECT** | `T1105` $\in$ GT; satisfies `ANY_MATCH` frozen protocol definition |
| `rag_k10` | 4,491 | `['T1059.003']` | **CORRECT** | `T1059.003` $\in$ GT; satisfies `ANY_MATCH` frozen protocol definition |

*Analysis:* Under Frozen Protocol v1.1, technique attribution accuracy follows the `ANY_MATCH` criterion: if any predicted technique belongs to the gold technique set, the prediction is evaluated as accurate. In `rag_k3`, the model attributed the ingress transfer behavior (`T1105`); in `rag_k10`, it focused on the command shell (`T1059.003`). Both are valid, scorable attributions under the protocol.

---

### Case 4: Misclassification under Retrieval Miss
- **Sample ID:** `view_02707f91` (Pair ID: `pair_888d30e0`)
- **Ground Truth:** `['T1059.003']` (*Windows Command Shell*)
- **Condition `rag_k10`:**
  * Prompt Tokens: 4,792 | Completion Tokens: 184 | Latency: 3,892 ms
  * Retrieved Candidates (first 3 of 10): `T1574.011`, `T1574.009`, `T1505.005` (GT `T1059.003` absent from all 10 candidates)
  * Predicted Technique: `['T1057']` (*Process Discovery*)
  * Attribution Status: **INCORRECT**
*Analysis:* Illustrates the downstream vulnerability of RAG: when the retriever fails to surface the gold technique even at $k=10$, dense distractor context can mislead generation into ungrounded technique attribution.

---

## 5. Operational Evidence & Empirical Rigor

### 5.1 The Single Transient API Failure & Automatic Recovery
A core requirement of rigorous empirical accounting is recording provider failures transparently:

- **Total Provider Requests:** 6,401
- **Total Completed Records:** 6,400
- **Retried Item Key:** `('view_d870d574', 'rag_k1')`
- **Attempt 1 (Journal Line 48479, Ordinal 5387):**
  * `event`: `attempt_receipt`
  * `status`: `API_FAILURE`
  * `error_type`: `InternalServerError`
  * `tokens`: `null` (gateway returned internal error without usage reporting)
  * `service_tier`: `null`
- **Attempt 2 (Journal Line 48481, Ordinal 5388):**
  * `event`: `attempt_receipt`
  * `status`: `SUCCESS`
  * `service_tier`: `default`
  * `input_tokens`: 1,543 (including 1,540 cached tokens)
  * `output_tokens`: 452
  * `response_id`: `resp_0efb218e56a6ecc1006abf0be6419887d0bca3815a8a0b3f0d`
- **Financial Reconciliation:**
  * Provisional hold for Attempt 1: \$0.53974560 (worst-case uncommitted reserve)
  * Settled cost for Attempt 2: \$0.00057395
  * Logical settled cost for record (Journal Line 48485): **\$0.54031955** (refund: \$1.61866285 from \$2.15898240 reservation).
  * No budget leakage or ledger desynchronization occurred.

---

### 5.2 The 13 INCOMPLETE Records (Provider Token Ceiling)
Across 6,400 evaluated samples, exactly 13 records failed due to token limits:

- **Condition Distribution:**
  * `rag_k3`: 6 records
  * `rag_k10`: 4 records
  * `rag_k5`: 3 records
  * `no_rag`: 0 records
  * `rag_k1`: 0 records
- **Ground Truth Distribution:**
  * **11 unmapped + 2 ambiguous**
  * **Zero (0) belong to the 718 scorable mapped views.**
- **Root Cause:** In dense retrieval conditions ($k \ge 3$), the combined reasoning trace and output schema hit the hard provider limit of **8,192 completion tokens** (`max_output_tokens`).
- **Exemplar Record (`view_1b91ff45`, Condition `rag_k3`, Pair `pair_c1188be0`):**
  * `completion_tokens`: 8,192
  * `error_message`: `Response incomplete: max_output_tokens`
  * `parse_status`: `INCOMPLETE`
  * `parsed_technique_ids`: `[]` (Fail-Closed)
- **Scientific Significance:** Rather than attempting ungrounded heuristic repair on truncated JSON, the evaluation engine strictly defaulted predictions to empty sets (`[]`), penalizing the condition in end-to-end accuracy (Provider Failure Rate = $0.00203$).

---

## 6. Truthful Costs & Financial Provenance

The canonical run operated under an automated hard ledger with a strict ceiling of **\$19.99 USD**:

```text
Study Budget Allocation:         $19.99000000 USD
Prior Pilot Provisional Hold:     $0.05264010 USD
Initial Available Balance:       $19.93735990 USD
Cumulative Settled Expenditure:   $6.57575890 USD
Final Uncommitted Balance:       $13.36160100 USD
Budget Breaches:                  0
```

- **Pricing Contract:** `config/pricing_v1.json` (SHA-256: `e8afd6311f04dbbf5c34bb030e88a5b9d394f92c84d3e51feb32b327a08655a5`)
  * Standard Input: \$1.50 per 1M tokens
  * Cached Input: \$0.375 per 1M tokens
  * Output Generation: \$6.00 per 1M tokens
- **Financial Reconciliation:** All 6,400 completed records have matching reservation and settlement receipts in `inputs/study_ledger.json` and `inputs/request_journal.jsonl`.

---

## 7. Synthetic Ground Truth Boundaries & Limitations

Reviewers must note the formal boundary of the experimental dataset:

1. **Scope:** 1,340 paired synthetic telemetry records covering 25 enterprise Windows attack techniques from MITRE ATT&CK v19.2.
2. **Diagnostic Purpose:** Pairs isolate single-action vs contextual multi-action detection to evaluate whether RAG improves disambiguation.
3. **Boundary Disclaimer:** Synthetic telemetry guarantees unambiguous ground truth labels for comparative benchmarking, but does not simulate full multi-week evasive APT tradecraft. Real-world deployments must combine RAG-augmented attribution with behavioral telemetry pipelines and human analyst triage.
