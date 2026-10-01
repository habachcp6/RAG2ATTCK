# RAG2ATT&CK - Independent Offline Reproducibility Guide

This document provides a comprehensive, step-by-step guide for an external researcher or reviewer to independently verify and reproduce all empirical findings, diagnostic evaluations, and cryptographic integrity locks of the **RAG2ATT&CK** study.

---

## 1. Reproducibility Principles & Zero-Cost Guarantee

To ensure scientific rigor and eliminate barriers to replication:

1. **Strictly Offline Execution (Zero Financial Cost & Zero API Keys):**
   - No paid API keys (e.g., OpenAI, Anthropic) are needed to reproduce the study findings.
   - All evaluation datasets, raw retrieval diagnostics, model outputs from the real-provider pilot, and MITRE ATT&CK corpora are committed directly to the repository as byte-preserved artifacts.
   - The reproduction pipeline operates under an enforced offline guard that disallows network egress and strips any accidental environment credentials.

2. **Cryptographic Hash Immutability (Canonical Lock v1):**
   - 15 core artifacts (datasets, prompt templates, retrieval index, models, and configs) are bound by SHA-256 digests in [`config/canonical_experiment_lock_v1.json`](../config/canonical_experiment_lock_v1.json).
   - The scientific evaluation protocol decisions (D1–D7) are immutably locked under [`config/experiment_protocol_v1.json`](../config/experiment_protocol_v1.json) with hash `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`.
   - The critical source code is locked under digest `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4`.

3. **Five Distinct Scientific Provenance Tiers:**
   To maintain absolute transparency, all data and outputs in this study belong to one of 5 distinct tiers:
   - **Tier 1 (Canonical Source Artifacts):** The 15 frozen artifacts committed in the repository and sealed under `canonical-lock-v1`.
   - **Tier 2 (Evaluator Fixture Diagnostics):** Known-answer synthetic unit test fixture records (`sample_count=5`) exported to `outputs/reproduction/fixture_diagnostics/` with explicit `_fixture_metadata.json` (`fixture_only=True`) to verify offline mathematical correctness of evaluator metrics.
   - **Tier 3 (DEV Cost Pilot Evidence):** Real-provider exploratory pilot records on OpenAI `gpt-5.6-luna` across 4 DEV views and all 5 conditions (20 records, $0.0242 USD spend) in `reports/evidence/dev_cost_pilot_20261001/`.
   - **Tier 4 (T20 Retrieval Diagnostics):** Full benchmark dense retrieval evaluation across 756 positive views and 670 scenario pairs, establishing canonical anchor pairwise rank differences (296 pairs) and lexical gaps (`T1136.001`).
   - **Tier 5 (Canonical TEST Study Matrix):** The full 1,280 samples x 5 conditions (6,400 records) live test execution (`synthetic-paired-test-1`), which is in-flight or awaiting live run termination under PID 50192. The evaluator enforces a strict fail-closed contract if run outputs are incomplete.

---

## 2. System Requirements & Environment Setup

### 2.1 Hardware & OS
- **OS:** Linux (Ubuntu 22.04+), macOS (13+), or Windows 10/11.
- **CPU:** Standard x86_64 or ARM64 multi-core processor (no GPU required for reproduction).
- **RAM:** Minimum 4 GB available memory.
- **Disk Space:** ~500 MB for repository checkout, virtual environment, and generated outputs.

### 2.2 Software Prerequisites
- **Python:** Version 3.12 or 3.13.
- **Package Manager:** `uv` (recommended) or standard `pip` + `venv`.
- **Git:** Git 2.30+.
- **Optional Dependencies:** `matplotlib` (for PNG figures) and `python-pptx` (for PowerPoint generation). The core audit and recomputation pipeline operates with strictly Python standard library.

### 2.3 Environment Setup (using `uv`)

```bash
# 1. Clone repository (if not already local)
git clone https://github.com/habachcp6/RAG2ATTCK.git
cd RAG2ATTCK

# 2. Check out target branch
git checkout codex/s1-reproducibility-presentation

# 3. Create virtual environment and synchronize dependencies
uv venv
uv sync
```

Alternatively, with standard Python:
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -e .
pip install matplotlib python-pptx
```

---

## 3. Automated One-Click Reproduction Pipeline

The repository provides a single, unified reproduction script: [`scripts/reproduce_study.py`](../scripts/reproduce_study.py).

To execute the entire verification suite:
```bash
uv run python scripts/reproduce_study.py
```

### CLI Execution Modes:
- `uv run python scripts/reproduce_study.py --all`: Run complete pipeline (default).
- `uv run python scripts/reproduce_study.py --verify-hashes`: Audit SHA-256 hashes of canonical locks and evidence.
- `uv run python scripts/reproduce_study.py --recompute-t20`: Recompute T20 retrieval diagnostic metrics from raw JSONL rows.
- `uv run python scripts/reproduce_study.py --run-fixture-diagnostics`: Run evaluator on synthetic test fixtures only (outputs to `outputs/reproduction/fixture_diagnostics/`).
- `uv run python scripts/reproduce_study.py --run-evaluator --run-dir <DIR>`: Execute authoritative evaluation on a completed canonical run directory (enforces fail-closed validation of full 1,280 x 5 matrix).
- `uv run python scripts/reproduce_study.py --generate-figures`: Generate publication figures (requires `matplotlib`).
- `uv run python scripts/reproduce_study.py --generate-tables`: Generate Markdown summary tables.

### What the script executes:
1. **Stage 1 (Cryptographic Hash Audit):** Checks SHA-256 hashes of all 15 canonical artifacts, the frozen protocol v1.1, the code manifest, and the 10 DEV cost pilot evidence files.
2. **Stage 2 (T20 Retrieval Diagnostics):** Recomputes Hit@k, Macro Recall@k, and absent rates across all 756 positive views; performs canonical anchor pairwise analysis across 670 scenario pairs.
3. **Stage 3 (Evaluator Fixture Diagnostics & Pilot Audit):** Runs `evaluate_experiment()` under Protocol v1.1 on known-answer unit fixtures (writing `outputs/reproduction/fixture_diagnostics/_fixture_metadata.json`), and audits the real-provider DEV pilot records.
4. **Stage 4 (Publication Figures):** Generates publication-ready 300 DPI figures in `outputs/reproduction/figures/`.
5. **Stage 5 (Summary Tables):** Generates markdown comparison tables in `outputs/reproduction/tables/`.

### Verified Offline Egress Guard:
To verify that the reproduction script does not leak credentials or make outbound network calls:
```bash
uv run python scripts/run_offline_tests.py -c "import sys; from scripts.reproduce_study import main; sys.exit(main(['--verify-hashes']))"
```
*Expected output:* `OFFLINE_GUARD: installed=True attempted_egress=0`.

---

## 4. Manual Step-by-Step Verification

For external researchers wishing to verify each component independently using standard command-line tools or custom scripts:

### Step 4.1: Verify Cryptographic Artifact Hashes
Read [`config/canonical_experiment_lock_v1.json`](../config/canonical_experiment_lock_v1.json) and calculate the SHA-256 hash of each file:

**Linux / macOS (Bash):**
```bash
sha256sum config/experiment_config.json
# Expected: 961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac

sha256sum data/ground_truth/synthetic/ground_truth.jsonl
# Expected: 8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608

sha256sum attack/corpus/enterprise-windows-v19.2.jsonl
# Expected: b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75
```

**Windows (PowerShell):**
```powershell
Get-FileHash -Algorithm SHA256 config\experiment_config.json
Get-FileHash -Algorithm SHA256 data\ground_truth\synthetic\ground_truth.jsonl
Get-FileHash -Algorithm SHA256 attack\corpus\enterprise-windows-v19.2.jsonl
```

All 15 hashes must match the values documented in [`docs/sanitized_evidence_manifest.json`](sanitized_evidence_manifest.json).

---

### Step 4.2: Recomputing T20 Retrieval Diagnostics (RQ2)
To recompute the headline retrieval performance metrics from the raw diagnostic JSONL rows:
```bash
uv run python scripts/verify_t20_canonical_artifacts.py
```

**Expected Headline Results:**
| Metric | Depth $k=1$ | Depth $k=3$ | Depth $k=5$ | Depth $k=10$ |
| :--- | :---: | :---: | :---: | :---: |
| **Hit@k** | 4.23% (32/756) | 16.80% (127/756) | 24.21% (183/756) | 45.11% (341/756) |
| **Macro Recall@k** | 3.46% | 15.90% | 23.13% | 43.14% |

**Key Diagnostic Insights to Verify:**
1. **Semantic Embedding Gap (`T1136.001`):** The local account creation technique `T1136.001` achieves **0 hits out of 99 positive views** in Top-10 ($Hit@10 = 0.0\%$). Dense bi-encoders using `all-MiniLM-L6-v2` fail to map Windows Event ID 4720 ("A user account was created") because the STIX technique description emphasizes threat actor objectives rather than specific event log tokens.
2. **Canonical Anchor Pairwise Comparison (670 candidate pairs):**
   - **Canonical Anchor Cohort (296 eligible pairs):** Single-event view contains exactly one technique that also appears in the contextual view. Single-event representation achieves a strictly better rank in **65 pairs (22.0%)**, Contextual-event in **23 pairs (7.8%)**, and **208 pairs (70.3%)** have equal rank (147 both absent from Top-10, 61 identical Top-10 rank). 374 pairs are excluded due to multi-label single view or missing anchor.
   - **Secondary Strict Single-Technique Cohort (252 eligible pairs):** Both single and contextual views contain exactly one identical technique. Single-event is better in **59 pairs (23.4%)** vs. **23 pairs (9.1%)** for Contextual-event (170 pairs equal).
   - *Scientific Note:* These empirical numbers represent observed retrieval rank differences under dense semantic search (`all-MiniLM-L6-v2`) on `synthetic-paired-v1`.

---

### Step 4.3: Auditing the Real-Provider DEV Cost Pilot (RQ3)
Inspect [`reports/evidence/dev_cost_pilot_20261001/summary.json`](../reports/evidence/dev_cost_pilot_20261001/summary.json) and associated prediction files:

```bash
# Verify record validity and unique response IDs
uv run python -c "
import json
from pathlib import Path

p = Path('reports/evidence/dev_cost_pilot_20261001')
for cond in ['no_rag', 'rag_k1', 'rag_k3', 'rag_k5', 'rag_k10']:
    rows = [json.loads(l) for l in (p / f'{cond}_predictions.jsonl').read_text().splitlines()]
    print(f'{cond}: {len(rows)} records, all VALID: {all(r[\"parse_status\"] == \"VALID\" for r in rows)}')
"
```

**Verified Pilot Empirical Statistics:**
- Total requests executed: 20 across 4 DEV views (2 single, 2 contextual) across all 5 conditions.
- Provider retries: 0 (100% first-attempt success).
- Total input tokens: 42,213; Total output tokens (including reasoning): 13,139.
- Measured standard price cost: **$0.0242094 USD**; conservative rate cost: **$0.0263201 USD**.
- Latency mean: **8,127.6 ms** per request.
- Token growth factor from $k=0$ (No-RAG: 643 tokens/req) to $k=10$ (RAG k=10: 4,536 tokens/req) is **~7.05x**.

---

### Step 4.4: Canonical Evaluator Execution & Contract Check
Run the unit test suite verifying evaluator behavior and fail-closed security properties under OFFLINE_GUARD:
```bash
uv run python scripts/run_offline_tests.py -m pytest tests/test_experiment_evaluation.py -q
```
*Expected result:* 94 tests pass in ~15 seconds with `OFFLINE_GUARD: installed=True attempted_egress=0`. Note: Raw pytest without OFFLINE_GUARD is forbidden. Full reproduction of live provider runs requires running with real credentials under the strict budget guard ($19.99 USD hard cap), whereas offline reproduction validates against committed frozen artifacts.

To test the authoritative evaluation path on an incomplete or pilot run (verifying fail-closed enforcement):
```bash
uv run python scripts/reproduce_study.py --run-evaluator --run-dir reports/evidence/dev_cost_pilot_20261001
```
*Expected result:* Fails closed with explicit diagnostic message:
`[FAIL_CLOSED] Authoritative evaluation requires canonical 'test' split matrix (1,280 samples). Provided manifest has split='dev'.`

---

## 5. Compiling Presentation Slides (PPTX & Markdown)

The presentation deck is provided in two complementary formats:
1. **Markdown Outline / Scaffold:** [`docs/presentation/slides.md`](presentation/slides.md) (12 slides structured for thesis defense / technical presentation).
2. **Materialized PowerPoint Deck:** [`docs/presentation/slides.pptx`](presentation/slides.pptx) (16:9 widescreen, custom cybersecurity color palette, embedded metric cards and figures).

To re-generate the PPTX slides programmatically:
```bash
uv run python scripts/generate_slides.py
```
*Verification output:* Confirms 12 slides generated, verified layout geometry (13.333 x 7.500 inches), and zero text overflow.

---

## 6. Directory of Generated Reproduction Outputs

When `scripts/reproduce_study.py` completes, outputs are stored in `outputs/reproduction/`:

```text
outputs/reproduction/
├── reproduction_report.md             # Complete timestamped verification log
├── fixture_diagnostics/               # Unit test fixture diagnostics (Mathematical Verification Only)
│   ├── _fixture_metadata.json         # Explicit metadata: {"fixture_only": true, "sample_count": 5}
│   ├── overall_metrics.json           # Accuracy, scorable sample counts, macro scores
│   ├── per_condition_metrics.json     # Per-condition performance across k in {0, 1, 3, 5, 10}
│   ├── per_technique_metrics.json     # Per-class precision, recall, and F1
│   ├── retrieval_conditional_metrics.json # P(Correct | Retrieved) vs P(Correct | Not Retrieved)
│   ├── failure_decomposition.json     # Independent axes of error decomposition
│   └── run_provenance.json            # Machine, environment, git, and protocol hashes
├── figures/                           # High-resolution 300 DPI publication plots
│   ├── fig_rq2_per_technique_breakdown.png # Hit@10 vs Absent-from-Top10 bar chart
│   ├── fig_rq2_retrieval_hit_rates.png     # Hit@k & Recall@k curve vs candidate depth k
│   └── fig_rq3_pilot_token_scaling.png     # Input & output token growth across RAG depths
└── tables/                            # Publication summary tables in GitHub Markdown
    ├── table_1_retrieval_diagnostics.md
    ├── table_2_per_technique_retrieval.md
    ├── table_3_dev_pilot_resource_usage.md
    └── table_4_pairwise_representation_comparison.md
```

---

## 7. Security, Anti-Leakage, and Privacy Audit

- **Zero Credentials:** The codebase and all evidence bundles have been scanned with automated regex byte-scanners; no `OPENAI_API_KEY`, AWS credentials, or bearer tokens exist in any committed file.
- **Anti-Label Leakage:** Raw inference rows (`data/ground_truth/synthetic/inference.jsonl`) undergo strict allowlist filtering (`INFERENCE_ALLOWLIST` in `src/synthetic.py`). Fields such as `technique_id`, `rule_name`, `tactic`, and `description` are strictly stripped prior to evaluation. Top-level row keys are restricted strictly to `sample_id` and `endpoint_evidence`.
- **Offline Network Isolation:** The test suite and reproduction scripts utilize the `offline_guard` (`scripts/run_offline_tests.py`), which intercepts socket creations and logs any attempted external network egress, ensuring absolute experimental isolation.

---

## 8. Runtime Provenance, OS Concurrency & License Disclosures

- **Runtime Launcher Binding:** The pinned executable runtime launcher hash is `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`.
- **Windows Filesystem Concurrency Wrapper:** On Windows platforms, filesystem locking anomalies during atomic journal commits and prediction file renames (`WinError 5` [Access Denied] and `WinError 32` [Sharing Violation]) are handled via a dedicated 12-attempt retry wrapper in `StudyBudgetLedger._write_atomically_unlocked` and `_write_anchor_atomically_unlocked` to ensure transactional record integrity without corrupted states.
- **License Disclosure:** The repository root `README.md` declares that the project is licensed under the MIT License. Note that a standalone `LICENSE` text file is currently not committed in the repository tree.
- **Technique Naming Alignment:** Active ATT&CK technique `T1059.009` is named `'Command & Scripting: Cloud API'`. ATT&CK technique `T1218.012` is named `'System Binary Proxy Execution: Verclsid'`.
- **Scope Boundary:** The empirical results and diagnostic observations reported herein are strictly bounded to the frozen `synthetic-paired-v1` benchmark (670 scenario pairs / 1,340 views). This research prototype does not claim generalizable empirical performance on in-the-wild real enterprise telemetry without an approved, sanitized real-world dataset.
