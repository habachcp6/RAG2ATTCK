# Public Reproduction Derivation Plan (Additive v4 Envelope Protocol)

> **Status:** Inventory-only implementation and validation completed; additive public package and scientific replay NOT STARTED — HOLD pending Root EXECUTE.
> **Document Identifier:** `reports/evidence/public_repro_derivation_plan_20261003.md`  
> **Revision:** R2 (Current Producer & Input Authority Inventory Completed; Public Package & Replay Scope Held Pending Root EXECUTE)
> **Target Subagent / Owner:** `eeafba1b` (`eeafba1b-8596-40b9-af66-73abb6c2ea59`, Worker Track B `native-bundle`)  
> **Worktree:** `C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_worktrees_20261003/native-bundle`  
> **Branch:** `codex/finalization-bundle-v2` (Accepted at `95c02338d146bfb060accc5efbc63bfab89a686d`)  
> **Accepted Metric Bundle v2 SHA-256:** `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` (49,465 bytes)
> **Root Freeze Envelope SHA-256:** `e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2` (4,335 bytes)

---

## 1. Executive Summary & Protocol Scope

The collector, tests and factual inventory were created under INVENTORY_ONLY authorization. No provider call, statistical scoring/bootstrap recomputation, archive build, public-v3 modification or scientific replay was performed. Future package construction and replay remain separate Root-authorized phases.

Preserve public-v3 descriptor/input/output bytes and frozen metric bundle. Scientific replay uses actual frozen b69 modules and the exact RQ source recorded in the inventory (`scripts/analysis/evaluate_rqs.py`: `f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351`), in a fresh attested child with its own locked runtime. Adapter verification uses accepted B95 code and Root freeze metadata; modern engineering source is a separate provenance domain.

---

## 2. Verified Facts & Artifact Inventory Corrections

Independent review of the actual Git objects, disk contents, and `public_v3` package established the following ground truth facts:

### A. Execution Log Reality (`logs/task-1264.log`): 1,141 Bytes, Not >250MB
- **Correction:** The actual execution terminal log `logs/task-1264.log` is **1,141 bytes** (SHA-256: `fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44`).
- **Clarification:** The previously cited hash `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa` belongs to the native launcher script `launch_canonical_resume.py`, not the log file.
- **Resolution:** The claim of multi-gigabyte or >250MB log omission is completely retracted. The task-1264 digest `fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44` is the ORIGINAL raw log SHA. Include original bytes only after privacy review, or record actual original-to-sanitized byte/hash transformation; do not label a changed derivative with the original digest.

### B. Tracked Status of Canonical Run Seal (`reports/evidence/canonical_run_seal_v1.json`)
- **Correction:** The run seal is **3,046 bytes** with exact SHA-256 `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701`.
- **Clarification:** This file is **already tracked** in public Git at `reports/evidence/canonical_run_seal_v1.json` (present in commits `b69a690` and `95c0233`). It was merely omitted from the distribution zip `public_v3`, and is NOT a private laboratory secret.
- **Resolution:** The minimal and robust solution is to add and document this exact tracked Git artifact in the additive `public_v4` envelope. Writing a new unanchored scientific derivation is unnecessary.

### C. Distinction Between Raw File Hashes vs. Semantic Mapping Digests
- **Protocol Configuration (`config/experiment_protocol_v1.json`):**
  * Raw File SHA-256: `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb` (1,051 bytes).
  * Semantic Decisions Digest: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` (computed over canonical D1–D7 fields).
- **Pricing Configuration (`config/pricing_v1.json`):**
  * Raw File SHA-256: `e8afd6311f04dbbf5c34bb030e88a5b9d394f92c84d3e51feb32b327a08655a5` (1,468 bytes).
  * Contract Semantic Digest: `4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565` (computed over canonical tariff values).
- **Code Manifest:**
  * Digest `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` represents the **semantic code manifest hash** across the 53 frozen core files, computed dynamically by `compute_code_manifest_sha256()`. There is no separate physical file named `code_manifest`.
- **Root Freeze Envelope:**
  * Located at `reports/evidence/root_metric_bundle_v2_freeze_95c0233.json` (SHA-256: `e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2`). Created following B `95c0233` during integration `17ae696`.

### D. Ground Truth Census & Dataset Partitioning
- **Total Benchmark Census:** 1,340 views / 670 pairs total, partitioned by `split_manifest.json` into:
  * **Test Split:** 1,280 views / 640 pairs (evaluated in canonical metric bundle v2).
  * **Dev Split:** 60 views / 30 pairs.
- **Dataset Files & Exact Inventory:**
  * Ground Truth Dataset: `data/ground_truth/synthetic/ground_truth.jsonl` (733,851 bytes, SHA-256: `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608`, 1,340 records / views).
  * Paired Views Dataset: `data/ground_truth/synthetic/views.jsonl` (153,500 bytes, SHA-256: `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d`, 1,340 records / views).
  * Paired Cases Dataset: `data/ground_truth/synthetic/pairs.jsonl` (2,221,465 bytes, SHA-256: `079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d`, 670 records / pairs).
  * Split Manifest: `data/ground_truth/synthetic/split_manifest.json` (10,739 bytes, SHA-256: `37fce63ccaa6db8e13604b7e3783997a10635f58995881b5e41913e6f550f43f`, partitions 640 test pairs and 30 dev pairs).
- **Public Candidate Input Directory:** `inputs/{condition}_predictions.jsonl` and `inputs/run_summary.json` (strictly conforming to public package layout, avoiding fabricated paths under `artifacts/results/`).

### E. Locked Toolchain & NumPy Specification
- Lockfile (`uv.lock`): 355,010 bytes, SHA-256: `77cd432fddf200a53671e6496cf1e046441823444cb490b9ead021944f4174a7`.
- Python & NumPy: Python 3.13.0 with NumPy **exactly `2.5.3`** (frozen in `uv.lock`).

### F. Authority Model: Git-Anchored Receipt (Not Asymmetric Digital Signatures)
- The reproduction attestation model relies on **Git-anchored Root validation receipts and commit tree hashes**, NOT PKI asymmetric digital signatures (no private key, public key, or trust-store is claimed or required).

---

## 3. Calibrated Master Evidence Inventory

| Logical Artifact | Concrete Repository Path | Actual File Bytes | Verified SHA-256 Hash | Hash Domain / Authority |
| :--- | :--- | :--- | :--- | :--- |
| **Accepted Metric Bundle v2** | `artifacts/results/canonical_metric_bundle_v2.json` | 49,465 | `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` | Exact file bytes (Canonical Anchor - Authenticated) |
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
| **Ground Truth Dataset** | `data/ground_truth/synthetic/ground_truth.jsonl` | 733,851 | `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608` | Exact file bytes (Benchmark ground truth, 1,340 views: 1,280 test + 60 dev) |
| **Paired Views Dataset** | `data/ground_truth/synthetic/views.jsonl` | 153,500 | `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d` | Exact file bytes (Benchmark paired views, 1,340 views: 1,280 test + 60 dev) |
| **Paired Cases Dataset** | `data/ground_truth/synthetic/pairs.jsonl` | 2,221,465 | `079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d` | Exact file bytes (Benchmark paired cases, 670 pairs: 640 test + 30 dev) |
| **Split Manifest Dataset Partition** | `data/ground_truth/synthetic/split_manifest.json` | 10,739 | `37fce63ccaa6db8e13604b7e3783997a10635f58995881b5e41913e6f550f43f` | Exact file bytes (Partitioning 640 test pairs / 30 dev pairs) |
| **Locked Dependencies** | `uv.lock` | 355,010 | `77cd432fddf200a53671e6496cf1e046441823444cb490b9ead021944f4174a7` | Exact file bytes (NumPy 2.5.3 frozen environment) |

---

## 4. Proposed Structure of the Additive `public_v4` Envelope

Proposed package-only phase adds the existing Git-tracked seal (`reports/evidence/canonical_run_seal_v1.json`: `ae7a9ada...`) and trusted Root acceptance/lineage receipts (`reports/evidence/root_metric_bundle_v2_freeze_95c0233.json`: `e284344e...`), without modifying base public-v3. The task-1264 digest (`fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44`) is ORIGINAL raw log SHA. Include original bytes only after privacy review, or record actual original-to-sanitized byte/hash transformation; do not label a changed derivative with the original digest.

No new scorer or metric-dictionary hash is defined. Later reproduction runs the existing frozen scientific functions in b69/f85d7f73 and separately the accepted B95 adapter with declared exact source/build timestamp/Root validation inputs. Equality to the entire frozen B442 file requires its full metadata and source closure (49,465 bytes, `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`); this is not equality of a narrowed metric dictionary, nor package construction evidence. Package-only tests cover trusted inventory/derivation completeness and protected bytes; actual scientific replay is a later explicitly executed gate.

## 5. Affirmation & Hold Status

Inventory implementation and validation completed. Public package construction/archive and scientific replay remain NOT STARTED/HOLD. No scientific or PROJECT_FINAL status is inferred from inventory completion.
