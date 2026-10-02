# Canonical Replay Publication Plan & Offline Reproduction Audit

**Author:** Native Agent A (Track A - Audit & Recovery)  
**Branch:** `codex/s1-audit-recovery` (PR #24)  
**Date:** 2026-10-02  
**Evaluation Git SHA:** `208ac00a9fe86813d4e4ec4fa72b2a943a2e4fdb`  
**Root Scientific Acceptance:** `root_canonical_export_validation_v2.json` (SHA-256: `551d0ca63101701837365a845078ab3b2f0e14a0b6c6f4946092f8cfd3ef1f39`)  
**Canonical Metric Bundle:** `canonical_metric_bundle_v1.json` (SHA-256: `00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f`)  
**Egress Invariant:** Strictly ZERO live provider/API calls (`OFFLINE_GUARD: installed=True attempted_egress=0`).

---

## 1. Executive Summary & Purpose

Root supervisor review officially granted scientific numerical acceptance on the authoritative canonical experiment run (`live-66b94b1676bf46a9`) evaluated under Frozen Scientific Protocol v1.1. Across 16,740 exported metric and diagnostic fields, zero defects or inconsistencies were detected (`root_canonical_export_validation_v2.json`).

This document provides the definitive publication plan and technical audit for enabling any clean public clone of the RAG2ATTCK repository to reproduce, verify, and inspect the canonical experimental findings completely offline, with zero live provider access, zero API keys, and zero financial cost.

---

## 2. Public Clone Offline Reproduction Requirements

### 2.1 Distinction: Historical Diagnostic Pipeline vs. Full Canonical Replay

Prior work in Track D (`scripts/reproduce_study.py`) established reproduction scaffolding targeting:
1. Retrieval diagnostics (T20 pairwise anchor analysis and top-10 absence metrics).
2. Development cost pilot audits (`dev_cost_pilot_20261001`, 10 requests).
3. Synthetic unit test fixtures (T15 mini-fixtures).

In contrast, **Full Canonical Replay** represents the authoritative, complete experimental evaluation of the entire paired test benchmark:
- **Logical Samples:** 6,400 evaluations across 5 conditions (`no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`).
- **Completed Records:** 6,387 records with complete JSON outputs.
- **Provider Failures:** Exactly 13 records truncated by the model's 8,192 `max_output_tokens` ceiling (failing closed safely to empty predictions).
- **Provider Requests Consumed:** 6,401 attempts (6,400 initial reservations + exactly 1 automatic retry on HTTP 500 `InternalServerError`).
- **Cumulative Settled Cost:** \$6.57575890 USD strictly settled against the \$19.99 USD hard budget.

### 2.2 Inventory of Required Public Clone Artifacts

A clean public clone requires the following components to execute authoritative offline verification and reproduction:

| Component | Repository Path / Artifact | Authoritative SHA-256 Digest |
| :--- | :--- | :--- |
| **Python Environment** | `pyproject.toml`, `uv.lock` (Python 3.13) | Tracked in repo root |
| **Protected Baseline (22 files)** | `attack/`, `config/`, `data/`, `docs/`, `prompts/` | Bound to baseline commit `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315` |
| **Canonical Experiment Lock** | `config/canonical_experiment_lock_v1.json` | `d0ce198ad4853f4c41ef2bfbafbe10a395e4927a6c6561b3e72c055c4b887e9f` |
| **Frozen Protocol v1.1 File** | `config/experiment_protocol_v1.json` | `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb` |
| **Frozen Protocol Semantic** | Canonical Decision Tuple | `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` |
| **Core Code Manifest** | 10 Canonical Modules Manifest | `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` |
| **Runtime Wrapper Block** | `src/experiment/runner.py` L47-75 | `e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68` |
| **Accepted Metric Bundle** | `canonical_metric_bundle_v1.json` | `00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f` |

### 2.3 Required Saved Canonical Inputs (10 Files)

These 10 files represent the raw experimental output of the live execution phase (`live-66b94b1676bf46a9`). They are evaluated offline by the metric engines without repeating LLM inference:

1. `inputs/manifest.json` (`66b658cfa9dd42e131ec567bbe043b8bc87ac6e92aeaa5e8f6661b0195e486e5`) - 127,772 bytes
2. `inputs/no_rag_predictions.jsonl` (`70034c5e3c417fc4a28c357d00d6a046751175ed03e7815645fa09e0411e228a`) - 2,207,966 bytes
3. `inputs/rag_k1_predictions.jsonl` (`745cb883a90b4d1bac7c76c4007b143893834530a843e153fc24277aae5da7ac`) - 2,292,294 bytes
4. `inputs/rag_k3_predictions.jsonl` (`29f215d74a3139df53036c642c8a14762bec4542d04685125cf28d024571b006`) - 2,459,866 bytes
5. `inputs/rag_k5_predictions.jsonl` (`896d900d10e25af748e00235c33cace84511c450bf7cfb0da2b4d1a658124178`) - 2,626,661 bytes
6. `inputs/rag_k10_predictions.jsonl` (`40cd9d2b19c691ed8bcb97ff5dfbebd378857346e9a06b00a9ab54e51fd9a122`) - 3,046,881 bytes
7. `inputs/request_journal.jsonl` (`f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`) - 7,571,342 bytes
8. `inputs/run_summary.json` (`67df38e336b4250b5a5c044b754ab02e8cc1826b8569f76d9bdf265ae4f84c2a`) - 593 bytes
9. `inputs/.study_anchor.json` (`d03aec39091e77defd90ea2756332d60305e6350a5b15fe724e806264e61fb25`) - 508 bytes
10. `inputs/study_ledger.json` (`21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8`) - 1,012,943 bytes

### 2.4 Expected Canonical Metric Outputs (8 Files)

1. `overall_metrics.json` (`25662753963ecdd05d16b8607095fffb964c0d53cd2c43026c50b47b22e55074`)
2. `per_condition_metrics.json` (`e6592f9a0f97739be1168f9d1448e0d209fe4a300727ff6ad78902523f1591d6`)
3. `per_technique_metrics.json` (`a2f96027439ba876b1c48b155a18f99872d3c4cc2c62c1bdc573a09aa73f49ef`)
4. `retrieval_conditional_metrics.json` (`2c68395f4ae923167b7cbc08835ff2772044ddc7695f69c0781ec277287d775f`)
5. `failure_decomposition.json` (`1ea3a899fefc7f92bcb739ab16e70036c269ebff16a7ec7e38240d2cc2c1c05d`)
6. `run_provenance.json` (`90918c9efe149c537c9b2cee7f7392607f273c12627bcc61b9dc9443359e63a1`)
7. `rq_analysis.json` (`945d413b1c55483c27b16d22dbdfddbcfc773419b06b463f4430530b17c94615`)
8. `rq_analysis_summary.md` (`712d495d5d71e5d96fd844fcb3dfdbc88e722056e265cf4a19d3813d9d9446c6`)

---

## 3. Publication Plan & Private Sanitization Inventory

An exhaustive byte-level scan was performed across all 19 proposed publication files (21,346,826 total bytes) within the accepted canonical bundle.

### 3.1 Secret & Credential Audit Results

- **Actual Secrets Detected:** **0**
- **Bearer Tokens / API Keys / Passwords:** **0**
- **Scan Summary:** The prediction JSONL files, request journal, ledger, and analysis outputs contain zero API keys, zero authentication tokens, and zero environment variables. All requests were mediated through the project's internal `src/llm/client.py` and `src/experiment/runner.py`, which strictly isolate API keys from logged payloads.

### 3.2 Provenance Identifiers vs. Credentials Policy

The experimental data contains opaque operational identifiers, specifically:
- `response_id` (e.g. `resp_006d5a88265e...`)
- `run_id` (`live-66b94b1676bf46a9`)
- `system_fingerprint` (`fp_...`)

**Classification:** In accordance with established project policy, these strings are **cryptographic and operational provenance identifiers**, not credentials. They grant zero authorization, cannot be used to invoke APIs, and contain no user identity. They are essential for verifying that predictions were legitimately generated by the configured model and were not retroactively synthesized or modified. They MUST be preserved intact in the public release.

### 3.3 Local Path Inventory & Sanitization Analysis

Scanning for machine-specific path strings identified 28 occurrences across 3 metadata files:

| File | Path Occurrences | Specific Fields | Path Values |
| :--- | :---: | :--- | :--- |
| `canonical_metric_bundle_v1.json` | 25 | `source_file_paths` (10 items)<br>`terminal_seal.path`<br>`root_verification.path`<br>`secondary_scope_authorization.path` | `C:\Users\hahoa\.codex\artifacts\...`<br>`D:\RAG2ATT&CK\artifacts\...` |
| `inputs/.study_anchor.json` | 2 | `ledger_path`<br>`output_directory` | `D:\RAG2ATT&CK\artifacts\study_budget\study_ledger.json`<br>`D:\RAG2ATTCK-worktrees\canonical-live-usd1999\...` |
| `rq_analysis.json` | 1 | `secondary_scope_packet.path` | `D:\RAG2ATT&CK\artifacts\orchestration\...` |
| **All Other 16 Files** | **0** | None | Clean (zero local paths) |

### 3.4 Preservation vs. Sanitization Recommendations

1. **Primary Golden Canonical Bundle (Preserve 100% Byte-Exact):**
   - The authoritative bundle at SHA-256 `00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f` should be published in its exact form in releases / scientific archives. The local paths in metadata reflect legitimate build provenance and do not leak credentials or sensitive personal information.
2. **Derived Public Clone Package (`canonical-bundle-public-v1`):**
   - If Root desires complete path portability for public GitHub clone checkouts where paths like `C:\Users\...` might trigger automated static path warnings, an explicitly derived package may be created via a deterministic field transform:
     * Transform: Map absolute Windows paths to repository-relative POSIX paths (e.g. `inputs/manifest.json`, `artifacts/orchestration/...`).
     * Invariance Proof: All 6,400 prediction records, token counts, metrics, costs, and RQ conclusions remain analytically identical.
     * Manifest Rule: The public package manifest will explicitly declare `derived_from: "00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f"` with a distinct SHA-256 to guarantee cryptographic transparency.

---

## 4. Public-Clone Execution Command Plan

For a user cloning the repository from scratch, the following deterministic, offline commands reproduce and verify the canonical study:

### Step 1: Environment Initialization & Invariant Check
```powershell
# Clone and enter repository
git clone https://github.com/habachcp6/RAG2ATTCK.git
cd RAG2ATTCK

# Sync pinned virtual environment
uv sync --frozen

# Verify protected baseline integrity against commit 80dbeb3f
git diff --exit-code 80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315 HEAD -- `
  attack/corpus/enterprise-windows-v19.2.jsonl `
  attack/corpus/enterprise-windows-v19.2.manifest.json `
  attack/index/enterprise-windows-v19.2.docmap.json `
  attack/index/enterprise-windows-v19.2.index `
  attack/index/enterprise-windows-v19.2.manifest.json `
  attack/raw/enterprise-v19.2/enterprise-attack-19.2.json `
  config/benchmark_scope.json `
  config/canonical_experiment_lock_v1.json `
  config/experiment_config.json `
  config/experiment_protocol_v1.json `
  config/model.json `
  config/pricing_v1.json `
  config/retrieval.json `
  data/ground_truth/synthetic/dataset_manifest.json `
  data/ground_truth/synthetic/ground_truth.jsonl `
  data/ground_truth/synthetic/inference.jsonl `
  data/ground_truth/synthetic/pairs.jsonl `
  data/ground_truth/synthetic/split_manifest.json `
  data/ground_truth/synthetic/views.jsonl `
  docs/context/RAG_ATTCK_Project_Tracker_Updated.xlsx `
  docs/context/RAG_ATTCK_Research_Plan_Updated.docx `
  prompts/baseline_v1.txt
```
*Expected Terminal Output:* Exit code 0, empty diff.

### Step 2: Comprehensive Offline Bundle Audit & Demo Inspection
```powershell
# Execute the native offline verification tool under strict egress guard
python scripts/run_offline_tests.py -c "import runpy; runpy.run_path('scripts/reproduce_canonical_study.py', run_name='__main__')"
```
*Expected Terminal Output:*
```text
================================================================================
RAG2ATTCK CANONICAL OFFLINE STUDY VERIFICATION HELPER
Target Bundle Directory: ...\canonical-accepted-bundle-v2
Egress Guard: STRICT ZERO LIVE PROVIDER/API CALLS
================================================================================

[PASS] Bundle manifest verified: 00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f
Verifying 10 Canonical Input Files: ALL [OK]
Verifying 8 Canonical Output Files: ALL [OK]
Cost and Financial Provenance Audit:
  Total Study Budget:              $19.99000000
  Cumulative Settled Cost:         $6.57575890
  Remaining Available Balance:     $13.36160100
  [PASS] Exactly 1 API retry detected: ('view_d870d574', 'rag_k1')
  [PASS] 6,400 records and 6,401 attempts strictly reconciled!
================================================================================
VERDICT: PASS_CANONICAL_OFFLINE_VERIFIED
================================================================================
OFFLINE_GUARD: installed=True attempted_egress=0
```

### Step 3: Automated Pytest Regression Suite
```powershell
# Run 23 automated tests (16 runtime recovery + 7 canonical replay integrity)
python scripts/run_offline_tests.py -m pytest `
  tests/test_runtime_recovery_wrapper.py `
  tests/test_canonical_offline_replay.py -v
```
*Expected Terminal Output:* `23 passed in ~4.5s`, `OFFLINE_GUARD: installed=True attempted_egress=0`.

---

## 5. Verification Checklist & Gate Alignment

- [x] Full scan of publication bytes for credentials completed (0 secrets found).
- [x] Machine-specific local paths enumerated and mapped across all files.
- [x] Opaque response IDs formally classified as provenance identifiers.
- [x] Input 10 and output 8 byte sizes and SHA-256 hashes bound to canonical lock.
- [x] Public clone execution instructions formulated and tested under `guard0`.
- [x] Dedicated helper `scripts/reproduce_canonical_study.py` implemented and verified.
- [x] Automated test suite `tests/test_canonical_offline_replay.py` passing (7/7 tests).
- [x] Zero duplicate scoring executed during preparation (awaiting Root instruction).
