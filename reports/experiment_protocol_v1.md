# RAG2ATTCK — Canonical Experiment Protocol v1

Status: **SCIENTIFIC_PROTOCOL_FROZEN**  
Protocol Version: `experiment-protocol-v1`  
Protocol SHA-256: `e7ab9ca3b5a779fc01e4d0b532871377aff041faf9c570c32599fedf26748677`  
Approval Reference: `RAG2ATTCK-PROTOCOL-V1-FROZEN`  
Approval Timestamp: `2026-09-30T00:00:00+00:00`  

---

## 1. Executive Summary & Purpose

This document records the immutable scientific protocol decisions (D1–D7) governing the RAG2ATTCK canonical experiments. It resolves the open scientific policy requirements defined in roadmap tasks T21, T22, T27, and T28.

All execution gates and offline evaluators bind to this frozen protocol. Automated workers or runner scripts are prohibited from altering any decision or re-interpreting metric semantics without a new, versioned protocol contract and human approval.

---

## 2. Frozen Scientific Decisions (D1–D7)

### D1: Raw Response Policy (`RECORD_ONLY`)
* **Decision**: `RECORD_ONLY`
* **Semantics**: The raw textual completion emitted by the LLM provider is recorded inline within the prediction record (`raw_response: str`, `raw_response_logged: true`) for auditable reproducibility, qualitative examination, and prompt engineering analysis.
* **Privacy & Secret Guard**: No environment credentials, authorization headers, API keys, or human authorization tokens may ever be persisted to journal, manifest, prediction, log, or evaluation artifacts. A fail-closed secret scanner and regression tests enforce zero credential leakage.
* **Alternative Rejected**: `LOG_SEPARATELY` is rejected and fails closed because dedicated out-of-band secure storage is not yet implemented.

### D2a: Multi-Label Ground Truth Semantics (`ANY_MATCH`)
* **Decision**: `ANY_MATCH`
* **Semantics**: The LLM predicts a single ATT&CK technique ID per sample. For samples whose ground truth comprises multiple valid technique annotations, the prediction is scored as correct if:
  $$\text{predicted\_id} \in \text{ground\_truth\_set}$$
* **Constraint**: Ground truth is never artificially coerced into an arbitrary synthetic primary label.

### D2b: Empty / Unmapped Ground Truth (`EXCLUDE`)
* **Decision**: `EXCLUDE`
* **Semantics**: Samples without an applicable ATT&CK mapping (`label_status == "unmapped"` or empty ground truth set) are excluded from the primary headline accuracy and macro-F1 metrics.
* **Accounting Requirement**: They are never silently discarded. The evaluator explicitly reports their total count, coverage percentage, and the explicit exclusion reason (`UNMAPPED_GROUND_TRUTH`).

### D2c: Ambiguous Ground Truth (`EXCLUDE`)
* **Decision**: `EXCLUDE`
* **Semantics**: Samples where expert annotators marked dual-use or ambiguous activity without definitive technique assignment (`label_status == "ambiguous"`) are excluded from primary headline scoring.
* **Accounting Requirement**: Evaluator reports their exact count, percentage, and category diagnostic. No automated system may adjudicate ground truth ambiguity.

### D2d: Macro-F1 Universe (`FROZEN_BENCHMARK_UNIVERSE`)
* **Decision**: `FROZEN_BENCHMARK_UNIVERSE`
* **Semantics**: The macro-averaged F1 class universe is strictly bounded by the frozen candidate technique universe defined in the benchmark retrieval corpus (`attack/corpus/enterprise-windows-v19.2.jsonl`, 474 candidate techniques: 176 parent techniques and 298 subtechniques).
* **Deterministic Invariant**: Model output variations do not alter the denominator or class universe across conditions or runs.

### D2e: Invalid ATT&CK ID Treatment (`INCLUDE_IN_DENOMINATOR`)
* **Decision**: `INCLUDE_IN_DENOMINATOR`
* **Semantics**: Invalid ATT&CK ID rate is computed across completed logical outputs:
  $$\text{invalid\_id\_rate} = \frac{\text{count}(\text{INVALID\_ID})}{\text{completed\_logical\_outputs}}$$
* **Categorization**: The evaluator distinguishes between:
  1. Syntax error (fails `^T[0-9]{4}(\.[0-9]{3})?$`).
  2. Unknown ID (valid syntax, but absent from pinned ATT&CK registry).
  3. Retired / deprecated ID (present in registry with `deprecated` or `revoked` flag).

### D2f: Provider & Parser Failure Accounting (`INCLUDE_IN_DENOMINATOR`)
* **Decision**: `INCLUDE_IN_DENOMINATOR`
* **Headline Metric**: Primary end-to-end accuracy counts logical samples experiencing provider failures (timeouts, API errors, refusals) or parse failures as failures/incorrect:
  $$\text{accuracy\_end\_to\_end} = \frac{\text{count}(\text{correct scorable samples})}{\text{total scorable samples}}$$
* **Conditional Reporting**: The evaluator simultaneously reports `accuracy_valid_completed_outputs` over samples that produced syntactically and semantically valid responses. Headline claims must always report end-to-end accuracy.

### D2g: Pinned ATT&CK Corpus & Retired IDs (`ALLOW_HISTORICAL`)
* **Decision**: `ALLOW_HISTORICAL`
* **Semantics**: ATT&CK is pinned to enterprise release v19.2 (`attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`). Predictions of deprecated or revoked technique IDs are reported as a distinct observation count and not silently remapped to replacement techniques.

### D2h: Retrieval Success Definition (`ANY_GT_RETRIEVED`)
* **Decision**: `ANY_GT_RETRIEVED`
* **Semantics**: In RAG conditions, retrieval is counted as successful for a sample if any ground-truth technique ID appears in the retrieved candidate list:
  $$\text{retrieval\_success} \iff \text{bool}(\text{set}(\text{retrieved\_candidates}) \cap \text{set}(\text{ground\_truth}))$$

### D2i: Failure Decomposition (`INDEPENDENT_AXES`)
* **Decision**: `INDEPENDENT_AXES`
* **Semantics**: Failures are analyzed along independent diagnostic axes:
  - `retrieval_miss`: RAG condition where no GT technique was retrieved.
  - `provider_failure`: Network timeout, HTTP error, refusal, or incomplete response.
  - `parse_failure`: Malformed output format.
  - `invalid_attack_id`: Hallucinated or non-existent ATT&CK ID.
  - `valid_but_wrong_classification`: Valid syntax/ID that does not match ground truth.
* **Invariant**: Diagnostic categories are not forced into an artificial mutually-exclusive precedence hierarchy. Overlap combinations (e.g. retrieval miss coupled with classification error) are explicitly tabulated.

### D2j: Zero Denominator Convention (`NULL`)
* **Decision**: `NULL`
* **Semantics**: Any metric whose denominator evaluates to zero is rendered as `null` (`None` in Python, serialized as `null` in JSON). It must never be silently approximated as `0.0` or `1.0`.

### D3: Model Version & Provenance (`ALLOW_LATEST_WITH_TIMESTAMP_BINDING`)
* **Decision**: `ALLOW_LATEST_WITH_TIMESTAMP_BINDING`
* **Semantics**: When a provider does not expose an immutable model snapshot ID, the runner must never fabricate a snapshot identifier. Instead, the runner permanently captures:
  - Provider identifier (`openai`)
  - Configured model name (`gpt-5.6-luna`)
  - Provider response metadata (`system_fingerprint`, returned model ID)
  - Request and response UTC timestamps
  - Reasoning effort (`xhigh`)
  - Generation parameters (temperature, seed, max tokens)
  - SHA-256 digests of prompt, model config, experiment config, protocol, and code commit SHA.

### D4: Execution Concurrency (`SEQUENTIAL_ONLY`)
* **Decision**: `SEQUENTIAL_ONLY`
* **Semantics**: Canonical experiments execute strictly with `concurrency = 1`. Preflight and live execution reject any configuration or command-line attempt to enable concurrency > 1.

### D5: Finite Budget Enforcement (`HARD_CAP_WORST_CASE_ATTEMPTS`)
* **Decision**: `HARD_CAP_WORST_CASE_ATTEMPTS`
* **Semantics**: Live execution requires an explicit finite positive budget cap covering worst-case attempts:
  $$\text{cap} \ge \text{samples} \times \text{conditions} \times (\text{max\_retries} + 1)$$
  Budget reservations occur prior to each dispatch, persist in the journal, track retries separately, survive crashes/resume, and fail closed upon exhaustion.

### D6: T15 Pilot Real Telemetry Prerequisite (`NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK`)
* **Decision**: `NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK`
* **Semantics**: Controlled synthetic experiments (RQ1–RQ3) are not blocked by the absence of external T15 real telemetry data. However, the absence of real telemetry strictly blocks any scientific claim of real-world generalization or real-telemetry efficacy.

### D7: Dataset Scope & Claim Boundary (`PAIRED_TEST`)
* **Decision**: `PAIRED_TEST` (for canonical experiment); `DEV_SMOKE` (for smoke qualification)
* **Scope Boundary**: The canonical experiment evaluates the 1,280 synthetic paired test views across five conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`). Synthetic benchmark results must never be described as real telemetry.

---

## 3. Cryptographic Decision Digest

The canonical SHA-256 digest of this protocol contract is:
```text
e7ab9ca3b5a779fc01e4d0b532871377aff041faf9c570c32599fedf26748677
```
Computed over the canonical JSON bytes of the decisions mapping. Any mutation of decisions invalidates this signature and immediately halts execution.
