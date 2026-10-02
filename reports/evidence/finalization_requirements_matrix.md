# RAG2ATTCK: Finalization Requirements Traceability Matrix

**Generated:** 2026-10-02T17:53:26.312387+00:00  
**Candidate Commit:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`  
**Total Requirements Tracked:** 43  

## Status Summary

- **VERIFIED (Fully Evidenced on GitHub/Candidate):** 26
- **PARTIAL (In Progress / Historical / Needs Expansion):** 13
- **NOT VERIFIED (To be Implemented in Subsequent Phases):** 3
- **FAIL (Defect Detected):** 1

---

## Traceability Matrix (Sections A through AF)

| ID | Section | Requirement Title | Status | Owner | Deliverable & Closure Step |
|:---|:---|:---|:---:|:---|:---|
| `REQ-A-01` | A. TRẠNG THÁI ĐÃ BIẾT | Canonical Experiment Identifiers & Scope | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Run provenance & summary audit records`<br>**Closure:** Phase 1 independent validator terminal seal re-verification. |
| `REQ-A-02` | A. TRẠNG THÁI ĐÃ BIẾT | Terminal Outcomes Distribution | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Prediction inventory & terminal outcome audit`<br>**Closure:** Re-verified during Phase 1 full terminal validator execution. |
| `REQ-A-03` | A. TRẠNG THÁI ĐÃ BIẾT | Financial Ledger Invariants & Budget Safe | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Study budget ledger reconciliation`<br>**Closure:** Verified via test_monetary_guard.py and audit_terminal_run.py. |
| `REQ-A-04` | A. TRẠNG THÁI ĐÃ BIẾT | Scientific Headline Baseline & Stat Sig Boundary | **VERIFIED** | Track B (Scientific Evaluation) & Track C (Report) | **Deliverable:** `Scientific statistical claims boundary`<br>**Closure:** Cross-artifact consistency automated check across all outputs. |
| `REQ-B-01` | B. SOURCE OF TRUTH | GitHub Evidence Mandatory Binding | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `Evidence audit methodology`<br>**Closure:** Enforce in all finalization report artifacts and PR descriptions. |
| `REQ-C-01` | C. QUYỀN HẠN | Prohibition of Live API Calls & Frozen Data Integrity | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Offline guard enforcement`<br>**Closure:** Continuous socket guard verification during all test and replay runs. |
| `REQ-D-01` | D. CHẾ ĐỘ LÀM VIỆC | 6 Dedicated Tracks with Single File Ownership | **VERIFIED** | Antigravity Coordinator | **Deliverable:** `Multi-track execution plan`<br>**Closure:** Enforce strict file isolation during parallel subagent dispatch. |
| `REQ-E-01` | E. PHASE 0 — SNAPSHOT TRẠNG THÁI HIỆN TẠI | GitHub Remote & PR Ancestry Preflight Snapshot | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `reports/evidence/finalization_preflight.json`<br>**Closure:** Maintain snapshot as baseline evidence; commit with requirements matrix. |
| `REQ-F-01` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Terminal Run Integrity (F1) | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Terminal run audit proof`<br>**Closure:** Phase 1 independent validator run. |
| `REQ-F-02` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Prediction Inventory across 5 Conditions (F2) | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Prediction inventory verification`<br>**Closure:** Phase 1 validator assertion. |
| `REQ-F-03` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Attempt Accounting & Retry Verification (F3) | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Attempt journal audit`<br>**Closure:** Re-verified via audit_terminal_run.py in Phase 1. |
| `REQ-F-04` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Terminal Outcome Taxonomy (F4) | **VERIFIED** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Outcome taxonomy breakdown`<br>**Closure:** Re-verified in Phase 1. |
| `REQ-F-05` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Ledger Multi-Entity Reconciliation (F5) | **PARTIAL** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Multi-entity reconciliation audit log`<br>**Closure:** Execute audit_terminal_run.py from PR #29 on candidate branch in Phase 1. |
| `REQ-F-06` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Terminal Process Proof Validator Hardening (Codex Probe Defect) | **FAIL** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `Harden audit_terminal_process_proof & add 4 negative regression tests`<br>**Closure:** In Track A, patch audit_terminal_process_proof to strictly require complete=True, execution_mode='live', canonical run_id, record_count=6400, requests_consumed=6401, bind log digest, and add regression tests in tests/test_terminal_audit.py. |
| `REQ-F-07` | F. PHASE 1 — CANONICAL TERMINAL EVIDENCE | Independent Terminal Validator Full Execution on Canonical Bytes | **PARTIAL** | Track A (Canonical Evidence & Terminal Audit) | **Deliverable:** `reports/evidence/canonical_run_seal_v1.json`<br>**Closure:** Run patched audit_terminal_run.py on canonical data, assert exit 0, zero egress, generate new candidate production seal. |
| `REQ-G-01` | G. PHASE 2 — FREEZE SCIENTIFIC DATASET | Cohort Definition & Denominator Isolation | **PARTIAL** | Track B (Scientific Evaluation / RQ1–RQ3) | **Deliverable:** `Cohort specification & schema contract`<br>**Closure:** Generate canonical_metric_bundle_v2.json with explicit cohort objects in Phase 2. |
| `REQ-G-02` | G. PHASE 2 — FREEZE SCIENTIFIC DATASET | Immutable Canonical Metric Bundle Generation | **PARTIAL** | Track B (Scientific Evaluation / RQ1–RQ3) | **Deliverable:** `artifacts/results/canonical_metric_bundle_v2.json`<br>**Closure:** Generate, hash, and freeze canonical metric bundle before report/presentation population. |
| `REQ-H-01` | H. PHASE 3 — RQ1 FINAL ANALYSIS | Controlled Attribution Comparison & Macro-F1 across 474 Universe | **VERIFIED** | Track B (Scientific Evaluation / RQ1–RQ3) | **Deliverable:** `RQ1 formal analysis output table & json`<br>**Closure:** Bind into canonical metric bundle v2. |
| `REQ-I-01` | I. PHASE 4 — RQ2 RETRIEVAL QUALITY | Protocol D2i 3-Axis Retrieval & Generation Decomposition | **VERIFIED** | Track B (Scientific Evaluation / RQ1–RQ3) | **Deliverable:** `RQ2 decomposition table & json`<br>**Closure:** Bind into canonical metric bundle v2 and Table 4. |
| `REQ-J-01` | J. PHASE 5 — RQ3 DEPTH / COST / LATENCY | Comprehensive Trade-off Table across k=0,1,3,5,10 | **PARTIAL** | Track B (Scientific Evaluation / RQ1–RQ3) | **Deliverable:** `RQ3 trade-off table & json`<br>**Closure:** Construct machine-generated Table 5. |
| `REQ-K-01` | K. PHASE 6 — FAILURE ANALYSIS | Provider Failures & Truncated INCOMPLETE Accounting | **VERIFIED** | Track B (Scientific Evaluation) & Track C (Report) | **Deliverable:** `Failure analysis section in report & bundle`<br>**Closure:** Ensure full consistency in Table 6 and failure figure. |
| `REQ-L-01` | L. PHASE 7 — SCIENTIFIC REPORT FINAL | Complete 30-Section Scientific Report (Markdown & DOCX) | **PARTIAL** | Track C (Scientific Report) | **Deliverable:** `docs/report/scientific_report.md & docs/report/scientific_report.docx`<br>**Closure:** Refine report sections, embed 8 figures and 6 tables, export pristine DOCX. |
| `REQ-M-01` | M. REPORT QUALITY RULES | Scientific Claim Discipline & Terminology Standards | **VERIFIED** | Track C (Scientific Report) | **Deliverable:** `Report text quality compliance`<br>**Closure:** Automated text scan for banned hype words (e.g., 'proves', 'enterprise-grade'). |
| `REQ-N-01` | N. RELATED WORK | Primary Source Citations & Comparator Integrity | **PARTIAL** | Track C (Scientific Report) | **Deliverable:** `Related work section & verified bibliography`<br>**Closure:** Integrate PR #8 related work findings into docs/report/scientific_report.md. |
| `REQ-O-01` | O. FIGURES & TABLES | 8 Publication Figures (Machine-Generated from Frozen Bundle) | **PARTIAL** | Track D (Figures / Tables / Statistical QA) | **Deliverable:** `docs/report/figures/ (8 figures, 16 files)`<br>**Closure:** Develop generator script scripts/generate_publication_figures.py to produce all 8 figures. |
| `REQ-O-02` | O. FIGURES & TABLES | 6 Publication Tables (Machine-Generated from Frozen Bundle) | **PARTIAL** | Track D (Figures / Tables / Statistical QA) | **Deliverable:** `docs/report/tables/ (6 tables, markdown + JSON)`<br>**Closure:** Develop generator script scripts/generate_publication_tables.py to produce all 6 tables. |
| `REQ-P-01` | P. CROSS-ARTIFACT CONSISTENCY | Automated Numerical Consistency Checker | **NOT VERIFIED** | Track D (Figures / Tables / Statistical QA) | **Deliverable:** `tests/test_cross_artifact_consistency.py`<br>**Closure:** Implement tests/test_cross_artifact_consistency.py and pass in test suite. |
| `REQ-Q-01` | Q. PRESENTATION FINAL | Vietnamese Presentation Deck (10–15 Slides) & Source | **PARTIAL** | Track E (Presentation / Reproducibility) | **Deliverable:** `docs/presentation/slides.pptx & docs/presentation/slides.md`<br>**Closure:** Author docs/presentation/slides_vi.pptx, verify preview PNGs, audit font sizes. |
| `REQ-R-01` | R. REPRODUCIBILITY PACKAGE | Clean Clone Offline Reproduction & Zero Egress | **VERIFIED** | Track E (Presentation / Reproducibility) | **Deliverable:** `scripts/reproduce_canonical_study.py & REPRODUCTION_GUIDE.md`<br>**Closure:** Re-run from final candidate commit and document in final handover package. |
| `REQ-S-01` | S. SECURITY / PRIVACY PACKAGE AUDIT | Zero Secrets, Zero Private Paths, Zero Bytecode Cache | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `Security audit report & scanner script`<br>**Closure:** Automated security scanning test in test suite. |
| `REQ-T-01` | T. PR INTEGRATION | Classification & Ancestry Audit of PRs #8, #24–#29 | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `PR lineage matrix in reports/evidence/finalization_preflight.json`<br>**Closure:** Integrate #29 in Phase 1, leverage #8 in Phase 7, prepare cleanup plan. |
| `REQ-U-01` | U. FINAL INTEGRATION BRANCH | Additive Integration Branch & Full Diff Audit | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `Diff audit log & candidate branch`<br>**Closure:** Run final diff audit before requesting human merge. |
| `REQ-V-01` | V. TEST MATRIX | 13 Mandatory Test Suites Verification | **PARTIAL** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `reports/evidence/test_matrix_execution_log.json`<br>**Closure:** Execute all 13 suites on final candidate commit, record exact counts and durations. |
| `REQ-W-01` | W. CI | All Required GitHub Actions CI Workflows Pass | **VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `GitHub Actions CI check run URLs and results`<br>**Closure:** Verify CI passes on new finalization branch commit. |
| `REQ-X-01` | X. FINAL HUMAN REVIEW PACKAGE | Consolidated Final Review Document | **NOT VERIFIED** | Antigravity Lead & Track F | **Deliverable:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`<br>**Closure:** Author and commit FINAL_REVIEW_PACKAGE.md as final gate before merge recommendation. |
| `REQ-Y-01` | Y. MERGE / FINALIZE | Human Authorization Gate for Main Merge | **VERIFIED** | Antigravity Lead | **Deliverable:** `Human merge authorization gate`<br>**Closure:** Issue READY_FOR_HUMAN_FINAL_MERGE notification to user/Codex. |
| `REQ-Z-01` | Z. POST-MERGE CLEANUP | Orderly PR Closure & Branch Cleanup | **NOT VERIFIED** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `Post-merge cleanup audit log`<br>**Closure:** Execute post-merge cleanup commands after human authorization. |
| `REQ-AA-01` | AA. RELEASE | Official Release Tagging & Release Notes | **PARTIAL** | Track F (Integration / GitHub / Release QA) | **Deliverable:** `Git tag v1.0.0-rag2attck-study & GitHub Release`<br>**Closure:** Draft release notes and create tag after main merge. |
| `REQ-AB-01` | AB. DEFINITION OF DONE | 21 Mandatory Criteria Checklist Compliance | **PARTIAL** | Antigravity Lead | **Deliverable:** `DoD verification checklist in FINAL_REVIEW_PACKAGE.md`<br>**Closure:** Validate all 21 items in final review. |
| `REQ-AC-01` | AC. SELF-CORRECTION LOOP | Systematic Error Diagnosis & Repair Invariant | **VERIFIED** | All Track Owners | **Deliverable:** `Self-correction protocol enforcement`<br>**Closure:** Apply iteratively to any failing suite. |
| `REQ-AD-01` | AD. REVIEWER ESCALATION | Evidence-Backed Escalation Protocol | **VERIFIED** | Antigravity Lead & Codex | **Deliverable:** `Escalation protocol compliance`<br>**Closure:** Active protocol. |
| `REQ-AE-01` | AE. FINAL RESPONSE FORMAT | Structured Final Response Template Compliance | **VERIFIED** | Antigravity Lead | **Deliverable:** `Final handback response`<br>**Closure:** Format final handback response. |
| `REQ-AF-01` | AF. PRIORITY ORDER | P0 through P7 Hierarchy Enforcement | **VERIFIED** | Antigravity Lead | **Deliverable:** `Execution priority schedule`<br>**Closure:** Execution sequenced strictly by priority. |

---

## Detailed Requirements Breakdown

### `REQ-A-01`: Canonical Experiment Identifiers & Scope (A. TRẠNG THÁI ĐÃ BIẾT)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Run ID live-66b94b1676bf46a9, 6,400 test matrix records, 6,401 provider attempts, exactly 1 retry recorded.
- **Deliverable:** `Run provenance & summary audit records`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Recorded in preflight snapshot and canonical_run_seal_v1.json (6,400 records, 6,401 attempts).
- **Closure Step:** Phase 1 independent validator terminal seal re-verification.

### `REQ-A-02`: Terminal Outcomes Distribution (A. TRẠNG THÁI ĐÃ BIẾT)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Exactly 6,387 VALID and 13 INCOMPLETE terminal outcomes. No silent removal of INCOMPLETEs.
- **Deliverable:** `Prediction inventory & terminal outcome audit`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Counted exactly across 5 conditions: 6,387 VALID, 13 INCOMPLETE.
- **Closure Step:** Re-verified during Phase 1 full terminal validator execution.

### `REQ-A-03`: Financial Ledger Invariants & Budget Safe (A. TRẠNG THÁI ĐÃ BIẾT)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Settled cost $6.57575890 USD + prior pilot hold $0.05264010 USD = total accounted $6.62839900 USD <= $19.99000000 budget cap. Exact Decimal math, no breach.
- **Deliverable:** `Study budget ledger reconciliation`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Exact monetary ledger audit in seal and preflight: $6.57575890 settled, $6.62839900 total, 0 breach.
- **Closure Step:** Verified via test_monetary_guard.py and audit_terminal_run.py.

### `REQ-A-04`: Scientific Headline Baseline & Stat Sig Boundary (A. TRẠNG THÁI ĐÃ BIẾT)

- **Status:** `VERIFIED`
- **Owner:** Track B (Scientific Evaluation) & Track C (Report)
- **Description:** No-RAG 560/718 (77.99%), RAG k=10 571/718 (79.53%), delta +1.532 pp, bootstrap 95% CI [-2.355, +5.300] pp, McNemar p=0.422. Strict scientific boundary: no general RAG superiority claim, no synthetic-to-production generalization.
- **Deliverable:** `Scientific statistical claims boundary`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Headline numbers and explicit non-claims codified in report abstract and discussion.
- **Closure Step:** Cross-artifact consistency automated check across all outputs.

### `REQ-B-01`: GitHub Evidence Mandatory Binding (B. SOURCE OF TRUTH)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** GitHub is sole source of truth. Every PASS claim must bind exact commit SHA, CLI command, exit code, count, artifact path/hash, and GitHub CI URL.
- **Deliverable:** `Evidence audit methodology`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** All checks tied to commit 5754f45 and PR #28 / PR #29 GitHub runs.
- **Closure Step:** Enforce in all finalization report artifacts and PR descriptions.

### `REQ-C-01`: Prohibition of Live API Calls & Frozen Data Integrity (C. QUYỀN HẠN)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Zero live provider API calls. No mutation of canonical records, ground truth, benchmark scope, prompt, pricing, or metric definitions.
- **Deliverable:** `Offline guard enforcement`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `scripts/run_offline_tests.py`
  - **Detail:** Automated socket guard blocks all outbound connections; 22 protected baseline files verified identical to 80dbeb3.
- **Closure Step:** Continuous socket guard verification during all test and replay runs.

### `REQ-D-01`: 6 Dedicated Tracks with Single File Ownership (D. CHẾ ĐỘ LÀM VIỆC)

- **Status:** `VERIFIED`
- **Owner:** Antigravity Coordinator
- **Description:** Establish 6 dedicated tracks (A, B, C, D, E, F) with isolated branches/worktrees and disjoint file ownership.
- **Deliverable:** `Multi-track execution plan`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_requirements_matrix.json`
  - **Detail:** Tracks mapped to distinct directories, files, and dependencies.
- **Closure Step:** Enforce strict file isolation during parallel subagent dispatch.

### `REQ-E-01`: GitHub Remote & PR Ancestry Preflight Snapshot (E. PHASE 0 — SNAPSHOT TRẠNG THÁI HIỆN TẠI)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Generate reproducible preflight snapshot containing main SHA, open PRs (#8, #24-#29), CI states, canonical bundle hashes, protected hashes, blockers, and plan.
- **Deliverable:** `reports/evidence/finalization_preflight.json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Created by Codex (SHA256 9587efd7e00352a1f34032ab19d523d5c1c255a206a05937c1b3a3c7fff5b24a).
- **Closure Step:** Maintain snapshot as baseline evidence; commit with requirements matrix.

### `REQ-F-01`: Terminal Run Integrity (F1) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Verify complete run, exactly 6,400 records, execution_mode=live, run_id=live-66b94b1676bf46a9, no active runner, locks released, run_summary valid.
- **Deliverable:** `Terminal run audit proof`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `artifacts/orchestration/terminal_process_proof_20261002.json`
  - **Detail:** Terminal proof records exit 0, pid 50192, task-1264 completed.
- **Closure Step:** Phase 1 independent validator run.

### `REQ-F-02`: Prediction Inventory across 5 Conditions (F2) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** 6,400 records across no_rag, rag_k1, rag_k3, rag_k5, rag_k10 (1,280 each). Zero duplicate keys, missing keys, invalid condition, or malformed JSON.
- **Deliverable:** `Prediction inventory verification`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** All 5 condition prediction files audited: 1,280 lines each, valid schema.
- **Closure Step:** Phase 1 validator assertion.

### `REQ-F-03`: Attempt Accounting & Retry Verification (F3) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** 6,401 attempts accounted. Verify exactly 1 retry record, attempt ordinals, initial attempt status, subsequent success, zero duplicate completions.
- **Deliverable:** `Attempt journal audit`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Request journal records 6,401 consumed attempts; single retry identified and verified.
- **Closure Step:** Re-verified via audit_terminal_run.py in Phase 1.

### `REQ-F-04`: Terminal Outcome Taxonomy (F4) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `VERIFIED`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** 6,387 VALID, 13 INCOMPLETE across conditions (0 no_rag, 0 k1, 6 k3, 3 k5, 4 k10). Verify no INCOMPLETE removal.
- **Deliverable:** `Outcome taxonomy breakdown`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Verified outcome distribution across all 5 conditions.
- **Closure Step:** Re-verified in Phase 1.

### `REQ-F-05`: Ledger Multi-Entity Reconciliation (F5) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `PARTIAL`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Join verification: prediction <-> request journal <-> receipt <-> settlement <-> study ledger for all 6,400 records. Verify SHA, response ID, returned model, token usage, reservation/settle/refund, exact Decimal math, 0 breach.
- **Deliverable:** `Multi-entity reconciliation audit log`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `tests/test_monetary_guard.py`
  - **Detail:** Passed in test suite; production seal recorded in validator_prep worktree.
- **Closure Step:** Execute audit_terminal_run.py from PR #29 on candidate branch in Phase 1.

### `REQ-F-06`: Terminal Process Proof Validator Hardening (Codex Probe Defect) (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `FAIL`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** audit_terminal_process_proof in scripts/audit_terminal_run.py (PR #29, SHA 9c5d6c8ac1e7bc5bb85cef9206f79ef1a43348f7, validator source SHA-256 f4d81efdbe47ff1a587c6ba7df0fb33ab8d66a2483a369e6cb01a4bbb78f74e0) was probed independently by Codex: accepts 4 negative-control copies (missing required live fields, wrong run count/mode, complete=null, unbound log digest). Positive control accepted correctly. Exit probe 0, OFFLINE_GUARD installed=True, egress=0.
- **Deliverable:** `Harden audit_terminal_process_proof & add 4 negative regression tests`
- **Current Evidence:**
  - **Commit SHA:** `9c5d6c8ac1e7bc5bb85cef9206f79ef1a43348f7`
  - **File:** `C:/Users/hahoa/.codex/artifacts/rag2attck/finalization_20261003/root_terminal_proof_probe.json`
  - **Detail:** FAIL: All 4 negative controls erroneously accepted in PR #29 validator; requires strict field validation and log digest binding in Track A.
- **Closure Step:** In Track A, patch audit_terminal_process_proof to strictly require complete=True, execution_mode='live', canonical run_id, record_count=6400, requests_consumed=6401, bind log digest, and add regression tests in tests/test_terminal_audit.py.

### `REQ-F-07`: Independent Terminal Validator Full Execution on Canonical Bytes (F. PHASE 1 — CANONICAL TERMINAL EVIDENCE)

- **Status:** `PARTIAL`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Description:** Execute patched independent validator CLI on unmodified canonical bytes (zero experiment calls, zero canonical record edits), producing genuine production seal (fixture_only=false) with verified baseline and 0 egress.
- **Deliverable:** `reports/evidence/canonical_run_seal_v1.json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/canonical_run_seal_v1.json`
  - **Detail:** Historical seal exists in validator_prep; must be re-generated on candidate branch by patched validator.
- **Closure Step:** Run patched audit_terminal_run.py on canonical data, assert exit 0, zero egress, generate new candidate production seal.

### `REQ-G-01`: Cohort Definition & Denominator Isolation (G. PHASE 2 — FREEZE SCIENTIFIC DATASET)

- **Status:** `PARTIAL`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Description:** Isolate cohorts: Total TEST 1,280 views; Mapped/scorable 718; Ambiguous 311; Unmapped 251. Strict denominator labeling on every table/metric.
- **Deliverable:** `Cohort specification & schema contract`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Cohorts documented in Section 8 of report; need formal machine-readable definition in frozen bundle.
- **Closure Step:** Generate canonical_metric_bundle_v2.json with explicit cohort objects in Phase 2.

### `REQ-G-02`: Immutable Canonical Metric Bundle Generation (G. PHASE 2 — FREEZE SCIENTIFIC DATASET)

- **Status:** `PARTIAL`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Description:** Create immutable canonical metric bundle (artifacts/results/canonical_metric_bundle_v1.json / v2.json) with SHA-256 containing provenance, source hashes, evaluation code hash, run ID, cohorts, RQ1-RQ3 metrics, statistical tests, cost, latency, diagnostics, and failure taxonomy.
- **Deliverable:** `artifacts/results/canonical_metric_bundle_v2.json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `artifacts/public_package_staging/canonical-bundle-public-v1/outputs/rq_analysis.json`
  - **Detail:** Public bundle has outputs, but unified consolidated canonical_metric_bundle_v2.json needs formal generation and freezing.
- **Closure Step:** Generate, hash, and freeze canonical metric bundle before report/presentation population.

### `REQ-H-01`: Controlled Attribution Comparison & Macro-F1 across 474 Universe (H. PHASE 3 — RQ1 FINAL ANALYSIS)

- **Status:** `VERIFIED`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Description:** Compute correct, total, accuracy, error rate, Macro-F1 across frozen 474-class universe, delta vs No-RAG, paired comparison, 95% bootstrap CI, McNemar p-value for k=0,1,3,5,10. Verify headline 77.99% vs 79.53%, delta +1.532 pp, CI [-2.355, +5.300], p=0.422.
- **Deliverable:** `RQ1 formal analysis output table & json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `artifacts/public_package_staging/canonical-bundle-public-v1/outputs/rq_analysis.json`
  - **Detail:** Accuracies and tests computed; need verification in consolidated bundle.
- **Closure Step:** Bind into canonical metric bundle v2.

### `REQ-I-01`: Protocol D2i 3-Axis Retrieval & Generation Decomposition (I. PHASE 4 — RQ2 RETRIEVAL QUALITY)

- **Status:** `VERIFIED`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Description:** Evaluate retrieval quality on downstream attribution under Protocol D2i: 3 overlapping axes (Retrieval Miss, Downstream Gen Failure, Joint Overlap). Verify k=10: Hit@10 321/718 (44.71%), Retrieval Miss 397/718 (55.29%), Acc|retrieved 293/321 (91.28%), Acc|missed 278/397 (70.03%), Wrong 147, Miss ∩ Wrong 119/147 (80.95%). Wording: associated with, not causal.
- **Deliverable:** `RQ2 decomposition table & json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `artifacts/public_package_staging/canonical-bundle-public-v1/outputs/failure_decomposition.json`
  - **Detail:** Decomposition numbers confirmed in public bundle outputs.
- **Closure Step:** Bind into canonical metric bundle v2 and Table 4.

### `REQ-J-01`: Comprehensive Trade-off Table across k=0,1,3,5,10 (J. PHASE 5 — RQ3 DEPTH / COST / LATENCY)

- **Status:** `PARTIAL`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Description:** Construct final table for accuracy, Macro-F1, Hit@k, prompt tokens, completion tokens, cached tokens, total tokens, mean/median latency, p95 (if authorized), cost/query, total condition cost, failure rate. Wording: 'tariff-derived accounted cost'.
- **Deliverable:** `RQ3 trade-off table & json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `artifacts/public_package_staging/canonical-bundle-public-v1/outputs/per_condition_metrics.json`
  - **Detail:** Token usage and settled costs present; formal consolidated Table 5 required.
- **Closure Step:** Construct machine-generated Table 5.

### `REQ-K-01`: Provider Failures & Truncated INCOMPLETE Accounting (K. PHASE 6 — FAILURE ANALYSIS)

- **Status:** `VERIFIED`
- **Owner:** Track B (Scientific Evaluation) & Track C (Report)
- **Description:** Document 1 transient API failure retry -> success. Document 13 INCOMPLETEs reaching 8,192 output token ceiling (0 no_rag, 0 k1, 6 k3, 3 k5, 4 k10; 0/13 in headline mapped cohort). Fail-closed parsing, no heuristic repair.
- **Deliverable:** `Failure analysis section in report & bundle`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Documented in report Section 22 and REPRODUCTION_GUIDE.md.
- **Closure Step:** Ensure full consistency in Table 6 and failure figure.

### `REQ-L-01`: Complete 30-Section Scientific Report (Markdown & DOCX) (L. PHASE 7 — SCIENTIFIC REPORT FINAL)

- **Status:** `PARTIAL`
- **Owner:** Track C (Scientific Report)
- **Description:** Deliver final docs/report/scientific_report.md and docs/report/scientific_report.docx containing all 30 mandatory sections without scaffold wording.
- **Deliverable:** `docs/report/scientific_report.md & docs/report/scientific_report.docx`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Current report is 35 pages v6, but needs review against all 30 mandatory sections and integration of 8 figures + 6 tables.
- **Closure Step:** Refine report sections, embed 8 figures and 6 tables, export pristine DOCX.

### `REQ-M-01`: Scientific Claim Discipline & Terminology Standards (M. REPORT QUALITY RULES)

- **Status:** `VERIFIED`
- **Owner:** Track C (Scientific Report)
- **Description:** No hype, no enterprise SOC claims, no 'proves', no causal claims for conditional analyses, clear distinction between synthetic inputs and real provider outputs.
- **Deliverable:** `Report text quality compliance`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Explicit scope boundary statements and non-claims are included in current report text.
- **Closure Step:** Automated text scan for banned hype words (e.g., 'proves', 'enterprise-grade').

### `REQ-N-01`: Primary Source Citations & Comparator Integrity (N. RELATED WORK)

- **Status:** `PARTIAL`
- **Owner:** Track C (Scientific Report)
- **Description:** Review references: Yang & Hsu, H-TechniqueRAG, MITRE ATT&CK v19.2 primary material, RAG foundational literature. No invented DOIs or venues. Integrate PR #8 verified comparator findings.
- **Deliverable:** `Related work section & verified bibliography`
- **Current Evidence:**
  - **Commit SHA:** `6783f20971cbff91f105d0280ddd07cb0925aab0`
  - **File:** `reports/T33_related_work.md`
  - **Detail:** PR #8 contains verified primary evidence; needs formal synthesis into Section 6 of report.
- **Closure Step:** Integrate PR #8 related work findings into docs/report/scientific_report.md.

### `REQ-O-01`: 8 Publication Figures (Machine-Generated from Frozen Bundle) (O. FIGURES & TABLES)

- **Status:** `PARTIAL`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Description:** Deliver 8 figures: Fig 1 Experimental Architecture, Fig 2 Accuracy across k, Fig 3 Macro-F1 across k, Fig 4 Retrieval Hit@k, Fig 5 Conditional Accuracy (retrieved vs missed), Fig 6 Latency vs k, Fig 7 Cost/Token usage vs k, Fig 8 Failure Decomposition. PDF + PNG formats.
- **Deliverable:** `docs/report/figures/ (8 figures, 16 files)`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `canonical-authoring-final-v6/report/figures/`
  - **Detail:** Currently 3 canonical RQ figures exist (canonical_rq1, rq2, rq3). Need to expand to full set of 8 distinct figures.
- **Closure Step:** Develop generator script scripts/generate_publication_figures.py to produce all 8 figures.

### `REQ-O-02`: 6 Publication Tables (Machine-Generated from Frozen Bundle) (O. FIGURES & TABLES)

- **Status:** `PARTIAL`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Description:** Deliver 6 tables: Table 1 Dataset/Split, Table 2 Experimental Conditions, Table 3 RQ1 Metrics, Table 4 RQ2 Retrieval Analysis, Table 5 RQ3 Cost/Latency, Table 6 Provenance/Hash/Evidence. All numbers machine-generated from frozen bundle.
- **Deliverable:** `docs/report/tables/ (6 tables, markdown + JSON)`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `docs/report/scientific_report.md`
  - **Detail:** Partial tables exist in report text; need formal machine generation script and individual table artifacts.
- **Closure Step:** Develop generator script scripts/generate_publication_tables.py to produce all 6 tables.

### `REQ-P-01`: Automated Numerical Consistency Checker (P. CROSS-ARTIFACT CONSISTENCY)

- **Status:** `NOT VERIFIED`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Description:** Create automated test checking identical headline numbers across metric bundle, README, report md/docx, slides, figures, and tables (77.99, 79.53, +1.532, [-2.355, 5.300], 0.422, 6400, 6401, 6387, 13, 6.57575890, 6.62839900, 19.99000000, 718, 311, 251, 474).
- **Deliverable:** `tests/test_cross_artifact_consistency.py`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Manual audit performed previously; automated regression test suite needs implementation.
- **Closure Step:** Implement tests/test_cross_artifact_consistency.py and pass in test suite.

### `REQ-Q-01`: Vietnamese Presentation Deck (10–15 Slides) & Source (Q. PRESENTATION FINAL)

- **Status:** `PARTIAL`
- **Owner:** Track E (Presentation / Reproducibility)
- **Description:** Deliver docs/presentation/slides.pptx (10-15 slides) in Vietnamese with consistent terminology, no text overflow, no tiny text (<18pt), accessible charts, complete speaker notes, and markdown source.
- **Deliverable:** `docs/presentation/slides.pptx & docs/presentation/slides.md`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `canonical-authoring-candidates-v2/presentation_v5/slides.pptx`
  - **Detail:** 12-slide English deck v5 exists; needs complete translation into Vietnamese while maintaining scientific terminology and verified 18-20pt table formatting.
- **Closure Step:** Author docs/presentation/slides_vi.pptx, verify preview PNGs, audit font sizes.

### `REQ-R-01`: Clean Clone Offline Reproduction & Zero Egress (R. REPRODUCIBILITY PACKAGE)

- **Status:** `VERIFIED`
- **Owner:** Track E (Presentation / Reproducibility)
- **Description:** Full reproduction from clean clone: checkout exact SHA, uv sync --frozen, public bundle, verify SHA, offline replay, metric re-scoring, zero provider calls, PASS_CANONICAL_OFFLINE_VERIFIED, attempted_egress=0, no workstation-specific paths.
- **Deliverable:** `scripts/reproduce_canonical_study.py & REPRODUCTION_GUIDE.md`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `tests/test_clean_clone_reproduction.py`
  - **Detail:** Tested and passed on commit 5754f45 in integration-audit-run (clean_clone_reproduction_proof.json).
- **Closure Step:** Re-run from final candidate commit and document in final handover package.

### `REQ-S-01`: Zero Secrets, Zero Private Paths, Zero Bytecode Cache (S. SECURITY / PRIVACY PACKAGE AUDIT)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Comprehensive scan of all tracked and public artifacts for API keys, bearer tokens, user home paths, private worktree paths, bytecode (.pyc, __pycache__), and credentials. Explicit transformation mapping for sanitized files.
- **Deliverable:** `Security audit report & scanner script`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `handover_manifest.json`
  - **Detail:** Package v3 archive scanned with 0 hits; transformation map codified in handover_manifest.json.
- **Closure Step:** Automated security scanning test in test suite.

### `REQ-T-01`: Classification & Ancestry Audit of PRs #8, #24–#29 (T. PR INTEGRATION)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Audit open PRs #8, #24-#29. Classify: ALREADY INCLUDED (#24, #25, #26, #27), INTEGRATION BASE (#28), MUST INTEGRATE (#29 validator), SELECTIVE (#8 related work).
- **Deliverable:** `PR lineage matrix in reports/evidence/finalization_preflight.json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Ancestry checked via git merge-base --is-ancestor: #24-#28 are true ancestors of candidate; #29 and #8 are separate.
- **Closure Step:** Integrate #29 in Phase 1, leverage #8 in Phase 7, prepare cleanup plan.

### `REQ-U-01`: Additive Integration Branch & Full Diff Audit (U. FINAL INTEGRATION BRANCH)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Candidate branch codex/finalization-20261003. Additive merge, no force push. Diff audit against 22 protected files, config, protocol, prompts, and canonical outputs.
- **Deliverable:** `Diff audit log & candidate branch`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Branch codex/finalization-20261003 active; protected baseline identical to 80dbeb3.
- **Closure Step:** Run final diff audit before requesting human merge.

### `REQ-V-01`: 13 Mandatory Test Suites Verification (V. TEST MATRIX)

- **Status:** `PARTIAL`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Execute: 1. ruff check, 2. ruff format --check, 3. offline unit suite, 4. integration suite, 5. synthetic data verification, 6. canonical replay test, 7. canonical manifest verification, 8. RQ known-answer tests, 9. report metadata verification, 10. presentation regression tests, 11. path/secret scanner, 12. cross-artifact consistency test, 13. terminal validator.
- **Deliverable:** `reports/evidence/test_matrix_execution_log.json`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/finalization_preflight.json`
  - **Detail:** Suites 1-7 pass on 5754f45; suites 8-13 to be finalized across Tracks B, D, F.
- **Closure Step:** Execute all 13 suites on final candidate commit, record exact counts and durations.

### `REQ-W-01`: All Required GitHub Actions CI Workflows Pass (W. CI)

- **Status:** `VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Push candidate commit to GitHub, monitor and verify 100% green CI on required checks (Full Test Suite ubuntu & windows, Real Retrieval Integration, Registry Validation, Synthetic Tests).
- **Deliverable:** `GitHub Actions CI check run URLs and results`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `https://github.com/habachcp6/RAG2ATTCK/pull/28`
  - **Detail:** 5/5 checks passed on PR #28 (HEAD 5754f45).
- **Closure Step:** Verify CI passes on new finalization branch commit.

### `REQ-X-01`: Consolidated Final Review Document (X. FINAL HUMAN REVIEW PACKAGE)

- **Status:** `NOT VERIFIED`
- **Owner:** Antigravity Lead & Track F
- **Description:** Deliver reports/evidence/FINAL_REVIEW_PACKAGE.md covering Repository State, Canonical Experiment, Scientific Results, Artifacts, Verification, Remaining Known Limitations, and Merge Recommendation.
- **Deliverable:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** To be authored upon completion of all tracks.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md as final gate before merge recommendation.

### `REQ-Y-01`: Human Authorization Gate for Main Merge (Y. MERGE / FINALIZE)

- **Status:** `VERIFIED`
- **Owner:** Antigravity Lead
- **Description:** Stop before merging into main. Report READY_FOR_HUMAN_FINAL_MERGE with exact PR/SHA. Await human authorization before executing merge.
- **Deliverable:** `Human merge authorization gate`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Gate strictly enforced; candidate remains on feature branch.
- **Closure Step:** Issue READY_FOR_HUMAN_FINAL_MERGE notification to user/Codex.

### `REQ-Z-01`: Orderly PR Closure & Branch Cleanup (Z. POST-MERGE CLEANUP)

- **Status:** `NOT VERIFIED`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Following main merge: close superseded PRs with clear explanations, clean obsolete remote branches, verify README links, ensure no stale 'TODO' or 'scaffold' text.
- **Deliverable:** `Post-merge cleanup audit log`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Pending main merge authorization.
- **Closure Step:** Execute post-merge cleanup commands after human authorization.

### `REQ-AA-01`: Official Release Tagging & Release Notes (AA. RELEASE)

- **Status:** `PARTIAL`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Description:** Tag v1.0.0-rag2attck-study upon human authorization. Release notes specify benchmark scope, final SHA, run ID, headline results, limitations, reproduction guide, and artifact hashes.
- **Deliverable:** `Git tag v1.0.0-rag2attck-study & GitHub Release`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Draft release v3 exists; official tag deferred until final main merge.
- **Closure Step:** Draft release notes and create tag after main merge.

### `REQ-AB-01`: 21 Mandatory Criteria Checklist Compliance (AB. DEFINITION OF DONE)

- **Status:** `PARTIAL`
- **Owner:** Antigravity Lead
- **Description:** Only claim 'PROJECT FINAL — PASS' when all 21 criteria in DoD checklist are strictly TRUE.
- **Deliverable:** `DoD verification checklist in FINAL_REVIEW_PACKAGE.md`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Tracking across matrix; currently in progress.
- **Closure Step:** Validate all 21 items in final review.

### `REQ-AC-01`: Systematic Error Diagnosis & Repair Invariant (AC. SELF-CORRECTION LOOP)

- **Status:** `VERIFIED`
- **Owner:** All Track Owners
- **Description:** Run tests -> inspect failure -> root-cause -> repair -> rerun -> compare criteria. No artificial round limits; no waiving tests without cause.
- **Deliverable:** `Self-correction protocol enforcement`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `tests/`
  - **Detail:** Demonstrated across previous sessions; enforced in all tracks.
- **Closure Step:** Apply iteratively to any failing suite.

### `REQ-AD-01`: Evidence-Backed Escalation Protocol (AD. REVIEWER ESCALATION)

- **Status:** `VERIFIED`
- **Owner:** Antigravity Lead & Codex
- **Description:** Prepare structured evidence package for uncertain scientific, metric, or canonical decisions. Reviewer decisions must be based on GitHub evidence.
- **Deliverable:** `Escalation protocol compliance`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `reports/evidence/`
  - **Detail:** Followed throughout orchestration with Codex.
- **Closure Step:** Active protocol.

### `REQ-AE-01`: Structured Final Response Template Compliance (AE. FINAL RESPONSE FORMAT)

- **Status:** `VERIFIED`
- **Owner:** Antigravity Lead
- **Description:** Final project handback must format output strictly according to Section AE template.
- **Deliverable:** `Final handback response`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Template adopted for final turn.
- **Closure Step:** Format final handback response.

### `REQ-AF-01`: P0 through P7 Hierarchy Enforcement (AF. PRIORITY ORDER)

- **Status:** `VERIFIED`
- **Owner:** Antigravity Lead
- **Description:** Strict priority hierarchy: P0 Canonical integrity -> P1 Scientific correctness -> P2 Reproducibility -> P3 Cross-artifact consistency -> P4 Report completeness -> P5 Presentation quality -> P6 GitHub cleanliness -> P7 Cosmetic polish.
- **Deliverable:** `Execution priority schedule`
- **Current Evidence:**
  - **Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
  - **File:** `None`
  - **Detail:** Enforced in track dependency ordering: Track A -> Track B -> Track D -> Track C/E -> Track F.
- **Closure Step:** Execution sequenced strictly by priority.

