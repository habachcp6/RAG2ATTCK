# Reproducibility & Presentation Package Evidence Manifest

**Subagent Handle:** Subagent D (Reproducibility & Presentation Owner for Phase S1)  
**Dedicated Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
**Branch:** `codex/s1-reproducibility-presentation`  
**Execution Timestamp (UTC):** 2026-10-01T21:07:00Z (Local: 2026-10-02T04:07:00+07:00)  
**Baseline PRE_SHA:** `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`  
**Execution Policy:** STRICTLY ZERO live provider/API calls. Zero secret leakage. 100% offline verifiable.

---

## 1. Executive Summary & Inventory of Deliverables

Subagent D has completed the inventory, D_REPAIR remediation, and CD_RENDER_REPAIR enhancements across all Phase S1 deliverables. The presentation deck (`docs/presentation/slides.pptx` and `docs/presentation/slides.md`) and offline reproducibility pipeline have been audited and upgraded to enforce mathematical rigor (D2i independent failure axes), zero bounding-box text overflow, consistent widescreen typography, strict academic claim hygiene, and artifact-cited speaker notes on every single slide. An external researcher or reviewer can independently verify every cryptographic artifact hash, recompute the T20 retrieval diagnostics from raw records, execute the canonical evaluation pipeline under Frozen Protocol v1.1, and recompile publication-quality figures, markdown tables, and a 16:9 PowerPoint presentation deck without spending money, querying live LLM APIs, or installing external database infrastructure.

### Complete Table of Authored Deliverables

| Deliverable | File Path | File Size (Bytes) | SHA-256 Digest | Status |
| :--- | :--- | :---: | :--- | :---: |
| **Offline Reproducibility Guide** | `docs/reproducibility.md` | 16,761 | `e0d89163c14b0ff3e22f1a1bfe7339adbaac89b7cd08ef68bc08438097ebb358` | VERIFIED |
| **Offline Reproduction Pipeline** | `scripts/reproduce_study.py` | 50,585 | `118676a617f46b40fad0d87c532b606a8f19d43a9a21a7471ac24a46ae0bb0c7` | VERIFIED |
| **Proposed Reconciled README** | `docs/README_PROPOSED.md` | 19,460 | `48209e0e39ac4e2c2be1e0fa10721ff73c8a404f4cd6276537d02198d586936b` | VERIFIED |
| **Presentation Deck Outline (MD)** | `docs/presentation/slides.md` | 30,547 | `50f573c356dd9fde4ef0f5e399de251659297b0e5ec72beb67e814d6ab084298` | VERIFIED |
| **PowerPoint Deck Builder Script** | `scripts/generate_slides.py` | 50,280 | `471a44a214785bc1fc5af623b7b5f13890809f5f0969661747fd76f3f393ba6e` | VERIFIED |
| **Compiled PowerPoint Deck (PPTX)**| `docs/presentation/slides.pptx` | 374,804 | `b82b25ba494dca81270ca54ee8b0163556e7eef98c1d1a8882313005aa66bc2d` | VERIFIED |
| **Sanitized Evidence Manifest** | `docs/sanitized_evidence_manifest.json` | 12,769 | `05f32a70d26f2531e8d5946fd71114bd0f264a0c871b51eedc06c24ec299e43f` | VERIFIED |

---

## 2. Cryptographic Canonical Lock Verification Audit

The reproduction pipeline verified that all 15 canonical artifacts declared in [`config/canonical_experiment_lock_v1.json`](../../config/canonical_experiment_lock_v1.json) match on disk bit-for-bit:

| Canonical Artifact Key | Bound Relative Path | Expected SHA-256 Digest | Verification Result |
| :--- | :--- | :--- | :---: |
| `attack_registry` | `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` | `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4` | **PASS (Match)** |
| `corpus` | `attack/corpus/enterprise-windows-v19.2.jsonl` | `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75` | **PASS (Match)** |
| `dataset_manifest` | `data/ground_truth/synthetic/dataset_manifest.json` | `4576b793360d02b60d619d199fd34d4555ace33215303ee847715c162a50dcc2` | **PASS (Match)** |
| `document_mapping` | `attack/index/enterprise-windows-v19.2.docmap.json` | `a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586` | **PASS (Match)** |
| `experiment_config` | `config/experiment_config.json` | `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac` | **PASS (Match)** |
| `ground_truth` | `data/ground_truth/synthetic/ground_truth.jsonl` | `8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608` | **PASS (Match)** |
| `index` | `attack/index/enterprise-windows-v19.2.index` | `7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5` | **PASS (Match)** |
| `inference` | `data/ground_truth/synthetic/inference.jsonl` | `90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8` | **PASS (Match)** |
| `model_config` | `config/model.json` | `312c34cedd84106f2004c6070b72aeac1dd84209a464e2993fee3ec87822697f` | **PASS (Match)** |
| `pairs` | `data/ground_truth/synthetic/pairs.jsonl` | `079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d` | **PASS (Match)** |
| `prompt` | `prompts/baseline_v1.txt` | `b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206` | **PASS (Match)** |
| `retrieval_config` | `config/retrieval.json` | `b33a93913e7f6de36f6f9021f77b2c9dcb1d426929162acb250a3c73ac8e6e25` | **PASS (Match)** |
| `retrieval_manifest` | `attack/index/enterprise-windows-v19.2.manifest.json` | `ad1fc8c8118ef897943597e30c3ab71cf30556f675b38bbeba6772537127ed0a` | **PASS (Match)** |
| `split_manifest` | `data/ground_truth/synthetic/split_manifest.json` | `37fce63ccaa6db8e13604b7e3783997a10635f58995881b5e41913e6f550f43f` | **PASS (Match)** |
| `views` | `data/ground_truth/synthetic/views.jsonl` | `1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d` | **PASS (Match)** |
| **Protocol v1.1 Hash** | `config/experiment_protocol_v1.json` | `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` | **PASS (Match)** |
| **Critical Code Hash** | Python core packages (`src/`, `prompts/`) | `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` | **PASS (Match)** |

---

## 3. Independent T20 Retrieval Diagnostics (RQ2)

The reproduction pipeline recomputed all T20 retrieval metrics independently from the raw JSONL rows without FAISS or heavy dependencies:
- **Positive Views Evaluated:** 756 / 1,340 views.
- **Query-Level Hit Rates:**
  - $Hit@1 = 0.0423$ (32 / 756 positive views)
  - $Hit@3 = 0.1680$ (127 / 756 positive views)
  - $Hit@5 = 0.2421$ (183 / 756 positive views)
  - $Hit@10 = 0.4511$ (341 / 756 positive views)
- **Macro Multi-Label Recall:**
  - $\text{Macro Recall}@1 = 0.0346$
  - $\text{Macro Recall}@3 = 0.1590$
  - $\text{Macro Recall}@5 = 0.2313$
  - $\text{Macro Recall}@10 = 0.4314$
- **Retrieval Failure Rate:**
  - Ground-truth absent from Top-10: **415 / 756 views (54.89%)**.
- **Pairwise Representation Comparison (670 candidate pairs):**
  - **Canonical Anchor Cohort (296 eligible pairs):**
    - Single-event view better: **65 pairs (22.0%)**
    - Contextual-event view better: **23 pairs (7.8%)**
    - Equal rank: **208 pairs (70.3%)**, of which **147 pairs** had both views absent from Top-10 and **61 pairs** had identical rank.
    - Excluded pairs: **374 pairs** (due to multi-label single view or missing anchor).
  - **Secondary Strict Single-Technique Cohort (252 eligible pairs):**
    - Single-event better: **59 pairs (23.4%)**
    - Contextual-event better: **23 pairs (9.1%)**
    - Equal rank: **170 pairs (67.5%)**
  - *Empirical Note:* These represent observed retrieval rank differences under dense semantic search (`all-MiniLM-L6-v2`) on `synthetic-paired-v1`.
- **Semantic Gap Discovery (`T1136.001` Local Account):**
  - $Hit@10 = 0.0\%$ (0 / 99 positive views). Windows Event ID 4720 technical terms ("SamAccountName", "A user account was created") fail to match ATT&CK persistence objective descriptions in standard dense semantic embeddings.

---

## 4. Real-Provider DEV Cost Pilot Audit (RQ3)

The reproduction pipeline independently checked the byte-preserved real-provider pilot records in `reports/evidence/dev_cost_pilot_20261001/`:
- **Execution Run ID:** `live-dc6b3166114d401e`
- **Model:** `gpt-5.6-luna` (OpenAI Responses API, `reasoning_effort=xhigh`)
- **Total Requests Executed:** 20 (across 4 DEV views and all 5 conditions: `no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, `rag_k10`)
- **Provider Retries:** 0 (100% first-attempt success)
- **Parse Status:** 100% VALID (20 / 20 records adhered to schema)
- **Input Tokens Measured:** 42,213
- **Output Tokens Measured (including reasoning):** 13,139
- **Mean Latency:** 8,127.6 ms
- **Measured Empirical Cost:** **$0.0242094 USD** (conservative input price: **$0.0263201 USD**)
- **Condition Scaling:**
  - `no_rag` ($k=0$): 643 input tokens/req
  - `rag_k1` ($k=1$): 1,115 input tokens/req (1.73x growth)
  - `rag_k3` ($k=3$): 1,741 input tokens/req (2.71x growth)
  - `rag_k5` ($k=5$): 2,518 input tokens/req (3.92x growth)
  - `rag_k10` ($k=10$): 4,537 input tokens/req (7.05x growth)
- **Extrapolation to Canonical 6,400-Request TEST Set:**
  - Standard rate projection: **$8.20 USD**; conservative input rate: **$8.99 USD**.

---

## 5. Evaluator Fixture Diagnostics & Completed-Run Reproduction Path

### 5.1 Evaluator Fixture Diagnostics (`outputs/reproduction/fixture_diagnostics/`)
The canonical evaluator (`src/evaluation/experiment_metrics.py`) was executed on synthetic unit test fixtures to verify mathematical correctness offline. All 6 metric artifacts were exported into `outputs/reproduction/fixture_diagnostics/` along with an explicit `_fixture_metadata.json` declaring `fixture_only = True`:
1. `_fixture_metadata.json` (`fixture_only: true`, `sample_count: 5`)
2. `overall_metrics.json`
3. `per_condition_metrics.json`
4. `per_technique_metrics.json`
5. `retrieval_conditional_metrics.json`
6. `failure_decomposition.json`
7. `run_provenance.json`

### 5.2 Authoritative Completed-Run Reproduction Path
The reproduction pipeline includes `--manifest` and `--run-dir` CLI options enabling verification of completed 1,280-sample test runs. It enforces fail-closed validation of the full 1,280 x 5 matrix (6,400 records) under Frozen Protocol v1.1. Incomplete runs (e.g. DEV pilot or in-flight live execution) fail closed with clear diagnostic notices.

---

## 6. Generated Publication Figures & Tables

The reproduction script generated 3 high-resolution 300 DPI figures and 4 markdown tables:
- **Figures (`outputs/reproduction/figures/`):**
  - `fig_rq2_retrieval_hit_rates.png`: Hit@k and Recall@k curves vs candidate depth $k \in \{1, 3, 5, 10\}$.
  - `fig_rq2_per_technique_breakdown.png`: Top-10 Hit Rate vs Absent Rate for target techniques.
  - `fig_rq3_pilot_token_scaling.png`: Input/output token usage and latency scaling across conditions.
- **Tables (`outputs/reproduction/tables/`):**
  - `table_1_retrieval_diagnostics.md`: Complete T20 retrieval performance metrics.
  - `table_2_per_technique_retrieval.md`: Per-technique breakdown of hits, absences, and mean ranks.
  - `table_3_dev_pilot_resource_usage.md`: DEV cost pilot empirical token counts and financial costs.
  - `table_4_pairwise_representation_comparison.md`: Detailed breakdown of both canonical anchor (296 pairs) and strict single-technique (252 pairs) cohorts.

---

## 7. Security, Credential & Concurrency Audit

1. **Zero Secret Leakage:**
   - Automated regex scanning verified that no API keys, bearer tokens, passwords, or private keys exist in any committed or generated file.
2. **Offline Isolation:**
   - Verified with `scripts/run_offline_tests.py`:
     ```text
     OFFLINE_GUARD: installed=True attempted_egress=0
     ```
3. **Runtime Launcher Binding & Concurrency Handling:**
   - Runtime launcher hash: `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`.
   - Windows filesystem concurrency wrapper: Windows-specific `WinError 5` (Access Denied) and `WinError 32` (Sharing Violation) filesystem errors during atomic journal flushes and file replacements are handled via a dedicated 12-attempt retry wrapper in `StudyBudgetLedger._write_atomically_unlocked` and `_write_anchor_atomically_unlocked`.
4. **License Status:**
   - Root `README.md` declares MIT License; note that a standalone `LICENSE` text file is not present in the repository tree.
5. **Technique Naming Alignment:**
   - `T1059.009` is named `'Command & Scripting: Cloud API'` (active).
   - `T1218.012` is named `'System Binary Proxy Execution: Verclsid'`.
6. **Scope Invariant:**
   - All empirical evaluations are strictly bounded to the frozen `synthetic-paired-v1` benchmark; no unwarranted claims regarding in-the-wild real enterprise telemetry are made.

---

## 8. Verification Commands & Hashes for Reviewers

```bash
# Full offline reproduction run:
uv run python scripts/reproduce_study.py

# Verified offline egress guard:
uv run python scripts/run_offline_tests.py -c "import sys; from scripts.reproduce_study import main; sys.exit(main(['--verify-hashes']))"

# Evaluator fixture diagnostics only:
uv run python scripts/reproduce_study.py --run-fixture-diagnostics

# Completed run evaluation (fail-closed if incomplete):
uv run python scripts/reproduce_study.py --run-evaluator --run-dir reports/evidence/dev_cost_pilot_20261001

# PowerPoint slide generation & QA:
uv run python scripts/generate_slides.py
```
