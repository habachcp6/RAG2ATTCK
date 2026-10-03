# Public Reproduction Derivation Plan (Additive v4 Envelope Protocol)

> **Status:** ACK READ-ONLY — STRICT HOLD PENDING ROOT REVIEW  
> **Document Identifier:** `reports/evidence/public_repro_derivation_plan_20261003.md`  
> **Revision:** R1 (Factual Inventory Calibration based on `supervisor_public_repro_plan_review_20261003`)  
> **Target Subagent / Owner:** `eeafba1b` (`eeafba1b-8596-40b9-af66-73abb6c2ea59`, Worker Track B `native-bundle`)  
> **Worktree:** `C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_worktrees_20261003/native-bundle`  
> **Branch:** `codex/finalization-bundle-v2` (Accepted at `95c02338d146bfb060accc5efbc63bfab89a686d`)  
> **Accepted Metric Bundle v2 SHA-256:** `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` (49,465 bytes)
> **Root Freeze Envelope SHA-256:** `e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2` (4,335 bytes)

---

## 1. Executive Summary & Protocol Scope

This revised document supersedes the preliminary draft and incorporates the factual findings from the independent metrics review (`supervisor_public_repro_plan_review_20261003`).

### Core Operating Invariants:
1. **STRICT HOLD (No Execution):** No code generation, no live provider calls (`OPENAI_API_KEY` blocked), no scoring/bootstrap recomputations, and no public-package modifications will be performed until Root explicitly issues the `EXECUTE` command.
2. **ZERO Egress Guard:** All future derivation checks must run strictly under `scripts/run_offline_tests.py` with `attempted_egress = 0`.
3. **No Redundant Scorer:** The derivation relies on the existing accepted Builder B (`95c0233`) and frozen scientific logic (`b69a690` / `f85764b8...`), under the locked toolchain (`uv.lock` with NumPy `2.5.3`). No novel mathematical engine or ad-hoc calculation will be introduced.
4. **Additive v4 Package Model:** The public release package `public_v3` (descriptor `32f...`) and accepted metric bundle `442b5933...` remain completely unmodified. The delivery will be structured as an additive **`public_v4` envelope** packaging missing tracked Git artifacts, explicit hash domain mapping, and a Git-anchored Root validation receipt.

---

## 2. Verified Facts & Artifact Inventory Corrections

Independent review of the actual Git objects, disk contents, and `public_v3` package established the following ground truth facts:

### A. Execution Log Reality (`task-1264.log`): 1,141 Bytes, Not >250MB
- **Correction:** The actual execution terminal log `logs/task-1264.log` is **1,141 bytes** (SHA-256: `fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44`).
- **Clarification:** The previously cited hash `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa` belongs to the native launcher script `launch_canonical_resume.py`, not the log file.
- **Resolution:** The claim of multi-gigabyte or >250MB log omission is completely retracted. The genuine 1,141-byte log can either be included directly in the public envelope (following privacy sanitization review) or attested via a verified public derivative with explicit observer boundary disclosures.

### B. Tracked Status of Canonical Run Seal (`canonical_run_seal_v1.json`)
- **Correction:** The run seal is **3,046 bytes** with exact SHA-256 `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701`.
- **Clarification:** This file is **already tracked** in public Git at `reports/evidence/canonical_run_seal_v1.json` (present in commits `b69a690` and `95c0233`). It was merely omitted from the distribution zip `public_v3`, and is NOT a private laboratory secret.
- **Resolution:** The minimal and robust solution is to add and document this exact tracked Git artifact in the additive `public_v4` envelope. Writing a new unanchored scientific derivation is unnecessary.

### C. Distinction Between Raw File Hashes vs. Semantic Mapping Digests
- **Protocol Configuration (`config/experiment_protocol_v1.json`):**
  * Raw File SHA-256: `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb` (1,051 bytes).
  * Semantic Decisions Digest: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` (computed over canonical D1–D7 fields). (computed over canonical D1–D7 fields). (computed over canonical D1–D7 fields).
- **Pricing Configuration (`config/pricing_v1.json`):**
  * Raw File SHA-256: `e8afd6311f04dbbf5c34bb030e88a5b9d394f92c84d3e51feb32b327a08655a5` (1,468 bytes).
  * Contract Semantic Digest: `4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565` (computed over canonical tariff values). (computed over canonical tariff values). (computed over tariff values).
- **Code Manifest:**
  * Digest `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` represents the **semantic code manifest hash** across the 53 frozen core files, computed dynamically by `compute_code_manifest_sha256()`. There is no separate physical file named `code_manifest`.
- **Root Freeze Envelope:**
  * Located at `reports/evidence/root_metric_bundle_v2_freeze_95c0233.json` (SHA-256: `e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2`). Created following B `95c0233` during integration `17ae696`.

### D. Ground Truth & Dataset Paths
- Ground Truth Test Split: `data/ground_truth/synthetic/ground_truth.jsonl` (733,851 bytes, SHA-256: `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608`).
- Paired Views Test Split: `data/ground_truth/synthetic/views.jsonl` (153,500 bytes, SHA-256: `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d`).
- Public Candidate Input Directory: `inputs/{condition}_predictions.jsonl` and `inputs/run_summary.json` (strictly conforming to public package layout, avoiding fabricated paths under `artifacts/results/`).

### E. Locked Toolchain & NumPy Specification
- Lockfile (`uv.lock`): 355,010 bytes, SHA-256: `77cd432fddf200a53671e6496cf1e046441823444cb490b9ead021944f4174a7`.
- Python & NumPy: Python 3.13.0 with NumPy **exactly `2.5.3`** (frozen in `uv.lock`).

### F. Authority Model: Git-Anchored Receipt (Not Asymmetric Digital Signatures)
- The reproduction attestation model relies on **Git-anchored Root validation receipts and commit tree hashes**, NOT PKI asymmetric digital signatures (no private key, public key, or trust-store is claimed or required).

---

## 3. Calibrated Master Evidence Inventory

| Logical Artifact | Concrete Repository Path | Actual File Bytes | Verified SHA-256 Hash | Hash Domain / Authority |
| :--- | :--- | :--- | :--- | :--- |
| **Accepted Metric Bundle v2** | `artifacts/results/canonical_metric_bundle_v2.json` | 49,465 | `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` | Exact file bytes (Canonical Anchor) |
| **Root Freeze Envelope** | `reports/evidence/root_metric_bundle_v2_freeze_95c0233.json` | 4,335 | `e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2` | Exact file bytes (Root Envelope) |
| **Canonical Run Seal v1** | `reports/evidence/canonical_run_seal_v1.json` | 3,046 | `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` | Exact file bytes (Tracked in Git 95c/b69) |
| **Execution Log** | `logs/task-1264.log` | 1,141 | `fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44` | Exact file bytes (Original run terminal log) |
| **Protocol Configuration (Raw JSON)** | `config/experiment_protocol_v1.json` | 1,051 | `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb` | Exact file bytes |
| **Protocol Specification (Report MD)** | `reports/experiment_protocol_v1.md` | 9,628 | `639fd68ae16deec86e9f6baab0980c1abb265c6cd7bb9b4662f562b87e54e819` | Exact file bytes |
| **Protocol Decisions (Semantic)** | `config/experiment_protocol_v1.json` | — | `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` | Decision fields canonical digest (D1–D7) |
| **Pricing File (Raw JSON)** | `config/pricing_v1.json` | 1,468 | `e8afd6311f04dbbf5c34bb030e88a5b9d394f92c84d3e51feb32b327a08655a5` | Exact file bytes |
| **Pricing Contract (Semantic)** | `config/pricing_v1.json` | — | `4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565` | Canonical JSON tariff digest |
| **Code Manifest (53 Core Files)** | `src/, config/, prompts/, pyproject.toml, .python-version` | — | `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` | Canonical JSON digest of path->file-hash mapping (not AST) |
| **RQ Evaluation Source Script** | `scripts/analysis/evaluate_rqs.py` | 126,249 | `f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351` | Exact file bytes (Frozen S2 Evaluator) |
| **Ground Truth Test Dataset** | `data/ground_truth/synthetic/ground_truth.jsonl` | 733,851 | `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608` | Exact file bytes (Synthetic test split ground truth, N=1,280) |
| **Paired Views Test Dataset** | `data/ground_truth/synthetic/views.jsonl` | 153,500 | `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d` | Exact file bytes (Synthetic test paired views, N=1,280 / 640 pairs) |
| **Paired Cases Dataset** | `data/ground_truth/synthetic/pairs.jsonl` | 2,221,465 | `079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d` | Exact file bytes (Benchmark paired telemetry cases) |
| **Locked Dependencies** | `uv.lock` | 355,010 | `77cd432fddf200a53671e6496cf1e046441823444cb490b9ead021944f4174a7` | Exact file bytes (NumPy 2.5.3 frozen environment) |

---

## 4. Proposed Structure of the Additive `public_v4` Envelope

When Root issues the `EXECUTE` directive, the additive package will be constructed without altering `public_v3`:

1. **Inclusion of Tracked Seal:**
   - Package `reports/evidence/canonical_run_seal_v1.json` (`ae7a9ada...`) into `v4/evidence/`.
2. **Inclusion of Execution Log:**
   - Package sanitized `task-1264.log` (`fcacacf6...`) accompanied by a privacy attestation manifest.
3. **Reproducibility Verification Adapter:**
   - Provide an offline verification script consuming public inputs (`inputs/` predictions and `run_summary.json`), joining with ground truth, and verifying the computed metric dictionary hashes byte-for-byte to `442b5933...`.
4. **Validation Receipt:**
   - Package `root_metric_bundle_v2_freeze_95c0233.json` certifying Root acceptance.

---

## 5. Affirmation & Hold Status

Coordinator and Owner B explicitly reaffirm:
- **This document constitutes an updated factual plan, NOT an execution.**
- No files have been created, modified, or generated in `native-bundle`.
- Track B remains completely dormant in **IDLE READ-ONLY** pending Root Reviewer review and explicit `EXECUTE` authorization.
