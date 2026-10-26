# RAG2ATT&CK — Independent Offline Reproducibility Guide (`v1.0.0-rag2attck-study`)

This document provides the complete, step-by-step protocol for an external researcher or reviewer to independently verify and reproduce all canonical empirical findings, diagnostic evaluations, financial ledger reconciliations, and cryptographic integrity locks of the **RAG2ATT&CK** study from a clean Git clone and the official public release package.

---

## 1. Reproducibility Principles & Zero-Cost Guarantee

To ensure scientific rigor and eliminate barriers to replication:

1. **Strictly Offline Execution (`OFFLINE_GUARD` — Zero Financial Cost & Zero API Keys):**
   - No paid API keys (e.g., OpenAI, Anthropic) are needed to reproduce the study findings.
   - All evaluation datasets, raw retrieval diagnostics, model outputs from the canonical 6,400-record live study (`synthetic-paired-test-1`), and MITRE ATT&CK v19.2 corpora are cryptographically sealed.
   - All reproduction and verification commands execute under `scripts/run_offline_tests.py`, which installs a Python socket-level network egress guard (`OFFLINE_GUARD: installed=True attempted_egress=0`) and strips ambient API credentials.

2. **Cryptographic Hash Immutability & Official Release Anchors:**
   - **Official Release Tag:** [`v1.0.0-rag2attck-study`](https://github.com/habachcp6/RAG2ATTCK/releases/tag/v1.0.0-rag2attck-study) (`Release ID: 402490699`), pointing to merge commit `ca8d39824a72e80053371e208506bfdc6332dc5d` (`tree: f868b5bf7ce52b79e2d8906f0436edec9c84b446`, identical to accepted candidate commit `d6c4827eda7d9e07054d85158e921f71374d137d`).
   - **Protected Baseline (`22` Files):** 21 git-tracked baseline artifacts plus 1 raw MITRE ATT&CK v19.2 STIX bundle (`attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`, SHA-256 `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`) preserved byte-identical to baseline commit `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`.
   - **Four Immutable Experimental Trust Anchors:**
     - `artifacts/results/canonical_metric_bundle_v2.json` (`49,465` bytes, SHA-256 `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34`)
     - `reports/evidence/canonical_run_seal_v1.json` (`3,046` bytes, SHA-256 `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701`)
     - `reports/evidence/populated_report_slots_canonical.json` (`15,010` bytes, SHA-256 `7c5a37f2659035108a70b7f161114f5d35e6c903a5e77df1d395164fbb75e77e`)
     - `public_v4_candidate_20261003.zip` (`2,343,105` bytes, SHA-256 `1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1`, Release Asset ID `607731773`)
   - **Scientific Protocol Lock (`Protocol v1.1`):** Locked in [`config/experiment_protocol_v1.json`](../config/experiment_protocol_v1.json) (file SHA-256 `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb`; canonical decisions digest `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`).

3. **Five Distinct Scientific Provenance Tiers:**
   All data and outputs in this study belong to one of five explicitly separated tiers:
   - **Tier 1 (Canonical Source & Baseline Artifacts):** The 22 protected baseline files (`PROTECTED_BASELINE_22`) and 15 core artifacts sealed under [`config/canonical_experiment_lock_v1.json`](../config/canonical_experiment_lock_v1.json).
   - **Tier 2 (Evaluator Fixture Diagnostics):** Known-answer synthetic unit test fixture records (`sample_count=5`) in `outputs/reproduction/fixture_diagnostics/` with `_fixture_metadata.json` (`fixture_only=True`) used strictly to verify offline mathematical correctness of evaluator functions.
   - **Tier 3 (DEV Cost Pilot Evidence):** Real-provider exploratory pilot records on OpenAI `gpt-5.6-luna` across 4 DEV views and all 5 conditions (20 records, `$0.0242094 USD` standard / `$0.05264010 USD` provisional hold) in `reports/evidence/dev_cost_pilot_20261001/`.
   - **Tier 4 (T20 Retrieval Diagnostics):** Full Stage B benchmark dense retrieval evaluation across 756 positive views and 670 scenario pairs (`all-MiniLM-L6-v2`, revision `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, `IndexFlatIP`).
   - **Tier 5 (Completed Canonical TEST Study Matrix — `synthetic-paired-test-1`):** The completed, cryptographically sealed 1,280 TEST views $\times$ 5 conditions (`6,400` records, `6,401` provider attempts, `6,387` VALID dispatches, `13` INCOMPLETE max-token records, `1` transient API retry on `view_d870d574:rag_k1`, `$6.57575890 USD` settled spend, `exit_code=0` in `canonical_run_seal_v1.json`), packaged inside `public_v4_candidate_20261003.zip` (`base_public_v3/`) and summarized in `artifacts/results/canonical_metric_bundle_v2.json`.

---

## 2. System Requirements & Environment Matrix

### 2.1 Hardware & Operating System
- **OS:** Windows 10/11, Linux (Ubuntu 22.04 / 24.04+), or macOS 13+.
- **CPU:** Standard x86_64 or ARM64 multi-core processor (no GPU required).
- **RAM:** Minimum 4 GB available memory.
- **Disk Space:** ~1.5 GB free space (for repository checkout, `.venv`, the 53.8 MB raw STIX v19.2 JSON, and unpacked release verification outputs).

### 2.2 Python & Environment Tiers (`Saved-Data Replay` vs. `Full Authoring Suite`)

The repository enforces `requires-python = ">=3.13.0"` in [`pyproject.toml`](../pyproject.toml) and pins `3.13` in [`.python-version`](../.python-version) (verified on **`Python 3.13.0`** across Windows 11 and Ubuntu 24.04).

| Environment Tier | Purpose & Scope | Required Toolchain & Packages | Mutates `uv.lock`? |
| :--- | :--- | :--- | :---: |
| **Tier A: Saved-Data Replay & Core Verification (Default)** | Reproduce all canonical `Native-6` and `RQ1–RQ3` metrics from `public_v4_candidate_20261003.zip`, verify package/ZIP integrity, audit the 170-requirement traceability matrix, check cross-artifact consistency, and run the standard CI test suite (`pytest -m "not integration"`). | `Python >= 3.13.0` (`3.13.0` tested), `uv`, `git`, and frozen dependencies via `uv sync --frozen`. | **No** |
| **Tier B: Full 178-Node Workstation Authoring & QA Suite (Optional)** | Additionally execute the 4 DOCX report-authoring tests in `tests/test_populate_report.py` (`scripts/export_report_docx.py`) and the 2 proprietary slide-deck AST authoring tests in `tests/test_presentation_and_repro_regressions.py` (`scripts/artifact_tool_deck_updater.mjs`), plus staged local bundle tests. | Tier A + `python-docx==1.2.0` installed into `.venv` (`uv pip install --python .venv/Scripts/python.exe python-docx==1.2.0`), `Node.js` + `@oai/artifact-tool` runtime, `PYTHONNOUSERSITE=1`, `PYTHONPATH=.`, and staged bundle directories. | **No** |

> [!IMPORTANT]
> **Why `uv.lock` is never modified for Tier B authoring extras:**
> Both `pyproject.toml` and `uv.lock` are part of `CRITICAL_CODE_PATTERNS` in [`src/experiment/authorization.py`](../src/experiment/authorization.py). Installing `python-docx==1.2.0` directly into the git-ignored `.venv` via `uv pip install` enables the DOCX authoring tests without altering the frozen experiment lockfile. In clean public environments without `@oai/artifact-tool`, the 2 proprietary JS deck-updater execution tests automatically skip via `@pytest.mark.skipif(not has_artifact_tool_runtime())`.

---

## 3. Unified Clean-Clone Canonical Reproduction Workflow (`v1.0.0-rag2attck-study`)

Every command below has been tested end-to-end on a clean clone of tag `v1.0.0-rag2attck-study` (`ca8d39824a72e80053371e208506bfdc6332dc5d`).

### Step 3.1: Clone Repository, Checkout Release Tag & Sync Frozen Environment

**Linux / macOS (Bash) & Windows (PowerShell):**
```bash
git clone https://github.com/habachcp6/RAG2ATTCK.git
cd RAG2ATTCK
git checkout v1.0.0-rag2attck-study

# Verify commit SHA matches ca8d39824a72e80053371e208506bfdc6332dc5d:
git rev-parse HEAD

# Create .venv and install exact frozen dependencies from uv.lock:
uv sync --frozen
```

### Step 3.2: Acquire & Verify the Raw MITRE ATT&CK v19.2 STIX Bundle (Baseline File #22)

21 of the 22 protected baseline files are tracked directly in Git. The 53.8 MB raw STIX v19.2 JSON (`attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`, SHA-256 `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`) is `.gitignore`d due to file size and is required by `load_evaluation_inputs()` during `--replay-evaluation` and by `scripts/verify_report_metadata.py`. Fetch and hash-verify it using the built-in loader (identical to `.github/workflows/ci.yml`):

```bash
uv run python -c "from pathlib import Path; from src.attack_loader import download_attack_reference; download_attack_reference(Path('.'))"
```

### Step 3.3: Download, Verify & Unpack `public_v4_candidate_20261003.zip`

Download the official release package asset (`2,343,105` bytes, SHA-256 `1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1`) from Release [`v1.0.0-rag2attck-study`](https://github.com/habachcp6/RAG2ATTCK/releases/tag/v1.0.0-rag2attck-study) and unpack it into `.tmp/public_v4_unpacked`:

**Linux / macOS (Bash):**
```bash
mkdir -p .tmp
curl -fL "https://github.com/habachcp6/RAG2ATTCK/releases/download/v1.0.0-rag2attck-study/public_v4_candidate_20261003.zip" \
  -o .tmp/public_v4_candidate_20261003.zip
echo "1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1  .tmp/public_v4_candidate_20261003.zip" | sha256sum -c -
unzip -q -o .tmp/public_v4_candidate_20261003.zip -d .tmp/public_v4_unpacked
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Force -Path .tmp | Out-Null
curl.exe -fL "https://github.com/habachcp6/RAG2ATTCK/releases/download/v1.0.0-rag2attck-study/public_v4_candidate_20261003.zip" `
  -o ".tmp/public_v4_candidate_20261003.zip"
$zipHash = (Get-FileHash -Algorithm SHA256 ".tmp/public_v4_candidate_20261003.zip").Hash.ToLower()
if ($zipHash -ne "1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1") { throw "SHA-256 mismatch: $zipHash" }
Expand-Archive -Path ".tmp/public_v4_candidate_20261003.zip" -DestinationPath ".tmp/public_v4_unpacked" -Force
```

### Step 3.4: Verify the 34-Member Public v4 Package & ZIP Stream Integrity (`OFFLINE_GUARD`)

```bash
uv run python scripts/run_offline_tests.py -m scripts.verify_canonical_package_acceptance \
  --candidate-dir .tmp/public_v4_unpacked \
  --candidate-zip .tmp/public_v4_candidate_20261003.zip \
  --expected-manifest-sha256 dbc2e133e8de30d6afa8345dcfa8b82890b13367a2bb24775278cc814a83dee2
```

*Expected output:*
- `ACCEPTANCE VERIFICATION VERDICT: PASS`
- `Archive SHA-256: 1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1`
- `Package Manifest SHA-256: dbc2e133e8de30d6afa8345dcfa8b82890b13367a2bb24775278cc814a83dee2`
- `Base Manifest SHA-256: 32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c`
- `Verified Items: 30 items (23 base, 7 supp)`, `Verified Semantic Roles: 8`, `Privacy Scan: CLEAN (0 violations)`
- `OFFLINE_GUARD: installed=True attempted_egress=0`

### Step 3.5: Execute Guarded Canonical Saved-Data Scientific Replay (`scripts/reproduce_canonical_study.py`)

Run the authoritative saved-data replay helper against `.tmp/public_v4_unpacked/base_public_v3` using the 4 saved-data replay flags (`--verify-hashes --audit-costs --replay-evaluation --demo`):

```bash
uv run python scripts/run_offline_tests.py -m scripts.reproduce_canonical_study \
  --repository-root . \
  --bundle-dir .tmp/public_v4_unpacked/base_public_v3 \
  --output-dir .tmp/canonical_replay_output \
  --expected-manifest-sha 32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c \
  --verify-hashes \
  --audit-costs \
  --replay-evaluation \
  --demo
```

*What this command verifies and recomputes:*
1. **`--verify-hashes`:** Authenticates `canonical_bundle_manifest.json` (`32f520c0...`), all 10 canonical input files (`manifest.json`, 5 condition prediction JSONLs, `request_journal.jsonl`, `run_summary.json`, `study_ledger.json`, `.study_anchor.json`), all 8 canonical analytical output files (`overall_metrics.json`, `per_condition_metrics.json`, `per_technique_metrics.json`, `retrieval_conditional_metrics.json`, `failure_decomposition.json`, `run_provenance.json`, `rq_analysis.json`, `rq_analysis_summary.md`), 4 sanitized provenance records, and `runtime_recovery_wrapper.py` (`RAW_WRAPPER_BLOCK` digest `e4a0115f...`).
2. **`--audit-costs`:** Reconciles the `$19.99000000` budget cap, `$0.05264010` prior pilot hold, `$6.57575890` settled spend across 6,400 records (`6,401` provider attempts, `1` transient API retry on `('view_d870d574', 'rag_k1')`), and `$13.36160100` remaining uncommitted balance.
3. **`--replay-evaluation`:** Re-executes `evaluate_experiment()` (`Native-6` outputs) and `run_rq_analysis()` (`RQ1–RQ3` with `1,000` cluster bootstrap iterations, `seed=42`) from the raw prediction JSONLs into `.tmp/canonical_replay_output` and performs deep typed tree comparison against the accepted canonical outputs (`float_tolerance=1e-12`, exact `Decimal` currency equality, `0` discrepancies across `2,331` Native-6 fields and `791` RQ fields).
4. **`--demo`:** Runs dynamic operator inspection across exemplar views (`view_0088e302`, `view_0265275a`, `view_026cbe9e`).
5. *Expected final verdict:* `VERDICT: PASS_CANONICAL_OFFLINE_VERIFIED` and `OFFLINE_GUARD: installed=True attempted_egress=0`.

> [!NOTE]
> **Why `--verify-hashes --audit-costs --replay-evaluation --demo` is used on the release checkout instead of `--all`:**
> Passing `--all` (or `--verify-baseline`) invokes `verify_protected_baseline(repository_root)`, which verifies both `PROTECTED_BASELINE_22` and whether `compute_code_manifest_sha256(repository_root)` equals the historical S1 execution code manifest `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` (from historical commit `b69a6909acda4c7588744acc7e1d6c20bfce2612`). Because post-S1 closeout hardening added fail-closed path and symlink checks to `src/experiment/authorization.py`, `compute_code_manifest_sha256` on the final release tree (`d41ca7c2...`) intentionally differs from `8b1b3ea4...`.
>
> To run `--all` (including `--verify-baseline` against the historical S1 code manifest `8b1b3ea4...`), provision the portable historical `b69a690` snapshot first and pass it as `--repository-root`:
> ```bash
> uv run python scripts/provision_snapshot.py --target-dir ../rag2attck_snapshot_b69a690
> uv run python scripts/run_offline_tests.py -m scripts.reproduce_canonical_study \
>   --repository-root ../rag2attck_snapshot_b69a690 \
>   --bundle-dir .tmp/public_v4_unpacked/base_public_v3 \
>   --output-dir .tmp/canonical_replay_output_all \
>   --expected-manifest-sha 32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c \
>   --all
> ```

### Step 3.6: Verify Report Metadata, Cross-Artifact Consistency & 170-Requirement Matrix

```bash
# 1. Verify Table 6 hashes, DOCX formatting invariants, zero-denominator cases, and STIX v19.2 census:
uv run python scripts/run_offline_tests.py -m scripts.verify_report_metadata

# 2. Verify strict cross-artifact numerical & OpenXML consistency against Canonical Metric Bundle v2:
uv run python scripts/run_offline_tests.py -m scripts.check_cross_artifact_consistency \
  --strict --scope all \
  --metric-bundle artifacts/results/canonical_metric_bundle_v2.json \
  --expected-bundle-sha256 442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34

# 3. Verify 170-requirement closeout traceability matrix (141 git blob bindings across 21 files):
uv run python scripts/run_offline_tests.py -m scripts.verify_requirements_matrix_audit

# 4. Verify R9 final artifact inventory (59/59 files and visual QA inspection record):
uv run python scripts/run_offline_tests.py -m scripts.generate_r9_artifact_inventory \
  --output .tmp/r9_inventory_check.json \
  --rc-output .tmp/r9_rc_check.json
```

---

## 4. Secondary Historical Diagnostics & Evaluator Fixture Helper (`scripts/reproduce_study.py`)

Alongside the primary canonical study replay script (`scripts/reproduce_canonical_study.py`), the repository retains [`scripts/reproduce_study.py`](../scripts/reproduce_study.py) for reproducing the **Tier 1 (S1 Snapshot Code Manifest `8b1b3ea4...` & 15 Canonical Lock Artifacts)**, **Tier 2 (Evaluator Unit Fixtures)**, **Tier 3 (DEV Cost Pilot)**, and **Tier 4 (Stage B T20 Retrieval Diagnostics)** artifacts established prior to the full TEST study run. Because Stage 1 verifies the historical S1 execution code manifest (`8b1b3ea4...`), point `--repository-root` at the provisioned `b69a690` snapshot directory:

```bash
uv run python scripts/provision_snapshot.py --target-dir ../rag2attck_snapshot_b69a690
uv run python scripts/run_offline_tests.py -m scripts.reproduce_study \
  --repository-root ../rag2attck_snapshot_b69a690 \
  --output .tmp/reproduction_report.md \
  --json-output .tmp/reproduction_verdict.json
```

### What `scripts/reproduce_study.py` verifies:
1. **Stage 1 (Hash & S1 Code Manifest Audit):** Audits SHA-256 hashes of the 15 canonical lock v1 artifacts, frozen protocol v1.1 (`d3bf3d31...`), critical S1 code manifest (`8b1b3ea4...`), and the 10 DEV cost pilot evidence files (`reports/evidence/dev_cost_pilot_20261001/`).
2. **Stage 2 (Stage B T20 Retrieval Diagnostics):** Recomputes Stage B T20 dense retrieval diagnostics across all 756 positive benchmark views (`Hit@1 = 4.23%`, `Hit@3 = 16.80%`, `Hit@5 = 24.21%`, `Hit@10 = 45.11%`; `T1136.001` semantic embedding gap `0/99` hits at Top-10) and canonical anchor pairwise comparisons across 670 scenario pairs (296 eligible canonical anchor pairs: Single-event strictly better in `65` pairs `[22.0%]`, Contextual-event better in `23` pairs `[7.8%]`, `208` pairs equal `[70.3%]`). Also verifiable standalone on the release checkout via:
   ```bash
   uv run python scripts/run_offline_tests.py -m scripts.verify_t20_canonical_artifacts
   ```
3. **Stage 3 (Evaluator Fixture & DEV Pilot Audit):** Runs `evaluate_experiment()` on the 5-sample synthetic unit fixture (`fixture_only=True`) and audits the 20-record DEV pilot (`$0.0242094 USD`).
4. **Fail-Closed Split Contract Check:** Verifies that attempting authoritative evaluation on the `dev` split pilot directory fails closed:
   ```bash
   uv run python scripts/run_offline_tests.py -m scripts.reproduce_study \
     --repository-root ../rag2attck_snapshot_b69a690 \
     --run-evaluator \
     --run-dir reports/evidence/dev_cost_pilot_20261001
   # Expected: [FAIL_CLOSED] Authoritative evaluation requires canonical 'test' split matrix (1,280 samples). Provided manifest has split='dev'.
   ```

---

## 5. Running the Offline Regression Test Suites

### 5.1 Standard Clean-Clone CI Test Suite (Tier A)
After running Steps 3.1–3.2 and provisioning the historical `b69a690` snapshot (`uv run python scripts/provision_snapshot.py --target-dir ../rag2attck_snapshot_b69a690`), run the full offline test suite:

**Linux / macOS (Bash):**
```bash
PYTHONNOUSERSITE=1 PYTHONPATH=. RAG2ATTCK_SNAPSHOT_ROOT=../rag2attck_snapshot_b69a690 \
  uv run python scripts/run_offline_tests.py -m pytest -m "not integration" -q
```

**Windows (PowerShell):**
```powershell
$env:PYTHONNOUSERSITE = "1"
$env:PYTHONPATH = "."
$env:RAG2ATTCK_SNAPSHOT_ROOT = (Resolve-Path "../rag2attck_snapshot_b69a690").Path
uv run python scripts/run_offline_tests.py -m pytest -m "not integration" -q
```

### 5.2 Full 178-Node Closeout Acceptance Suite (Tier B Workstation Authoring Mode)
To execute the exact 178-node acceptance suite recorded in Release Asset `workstation_acceptance_d6c4827_sanitized.log` (`178 passed, 0 skipped, 0 failed`):
1. Install `python-docx==1.2.0` into `.venv` (`uv pip install --python .venv/Scripts/python.exe python-docx==1.2.0`).
2. Ensure `Node.js` and `@oai/artifact-tool` are present in the workstation runtime cache (for the 2 JS deck-updater tests in `tests/test_presentation_and_repro_regressions.py`).
3. Stage the unpacked Public v4 package at `artifacts/public_package_staging/04_public_v4_candidate` (with `public_v4_candidate_20261003.zip` at `artifacts/public_package_staging/public_v4_candidate_20261003.zip`) and `base_public_v3` at `artifacts/public_package_staging/canonical-bundle-public-v1`, plus the canonical v1 bundle directory in `CANONICAL_BUNDLE_DIR`.
4. Run the 11 acceptance test modules under `scripts/run_offline_tests.py` with `PYTHONNOUSERSITE=1` and `PYTHONPATH=.`.

---

## 6. Runtime Provenance, OS Concurrency, Errata & License Disclosures

- **Runtime Launcher Binding:** The pinned executable runtime launcher hash is `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa` (`RAW_WRAPPER_BLOCK` SHA-256 `e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68`).
- **Windows Filesystem Concurrency Wrapper:** On Windows platforms, filesystem locking anomalies during atomic journal commits and prediction file renames (`WinError 5` [Access Denied] and `WinError 32` [Sharing Violation]) are handled via a 12-attempt retry wrapper in `StudyBudgetLedger._write_atomically_unlocked` and `_write_anchor_atomically_unlocked`.
- **License Disclosure:** This project is licensed under the MIT License — see the standalone [`LICENSE`](../LICENSE) file in the repository root.
- **Post-Release Audit Errata (`release_closeout_acceptance.json`):**
  - The checksum-pinned release asset `release_closeout_acceptance.json` (`Asset ID: 679064106`, `11,969` bytes, SHA-256 `aa8e4bcf52e2b2ca6631b16e1458891069423108bfbbdb6ce40b2ca46b50e6ba`) is preserved byte-identical on Release `v1.0.0-rag2attck-study`.
  - Its `post_approval_execution_phase_ii.main_branch_integration.merged_at_utc` field (`"2026-10-26T18:08:06Z"`) reflects the GitHub auto-merge timestamp of ancestor PRs `#24–#29`, whereas PR `#30`'s own `merged_at` timestamp in the GitHub Pulls API is `"2026-10-26T18:08:04Z"` (merge commit `ca8d39824a72e80053371e208506bfdc6332dc5d` commit timestamp `"2026-10-26T18:08:03Z"`).
- **Technique Naming Alignment:** Active ATT&CK technique `T1059.009` is named `'Command & Scripting: Cloud API'`. ATT&CK technique `T1218.012` is named `'System Binary Proxy Execution: Verclsid'`.
- **Scope Boundary:** All empirical findings reported in this repository are strictly bounded to the frozen `synthetic-paired-v1` benchmark (`670` scenario pairs / `1,340` views; `718` scorable TEST views across `440` clusters and `8` positively supported ground-truth techniques). Real-world enterprise telemetry (`T15`) remains `DATA_UNAVAILABLE`.
