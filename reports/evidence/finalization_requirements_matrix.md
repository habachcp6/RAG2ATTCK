# RAG2ATTCK: Comprehensive Requirements Traceability Matrix v2

**Generated:** `2026-10-02T18:08:47.701611+00:00`  
**Candidate Base SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`  
**Total Tracked Requirements & Gates:** `170`  

## 1. Candidate Status Summary

> [!IMPORTANT]
> In strict accordance with Codex audit directives, unexecuted candidate gates and deliverables are classified as **`NOT VERIFIED`** or **`PARTIAL`**. Only governing policies are marked as **`POLICY_ENFORCED`**. The terminal validator probe defect discovered by Codex is explicitly classified as **`FAIL`** pending Track A repair.

- **`POLICY_ENFORCED` (Governing Rules & Architectural Contracts):** 23
- **`PARTIAL` (Historical Verification Exists; Candidate Execution Pending):** 66
- **`NOT VERIFIED` (Deliverables / Gates to be Executed in Subsequent Phases):** 80
- **`FAIL` (Defect Detected by Codex Independent Probe):** 1
- **`VERIFIED` (Fully Completed & Tested on Final Candidate):** 0

---

## 2. Evidence Storage Classification

- `git_tracked`: Artifact is checked into the Git repository at a verifiable commit SHA.
- `release_asset`: Artifact is packaged within a standalone release zip archive (e.g. `final_handover_package_v3_20261002.zip`).
- `private_historical`: Artifact resides in private canonical storage or uncommitted audit logs, linked by immutable SHA-256.
- `local_pending`: Artifact is generated locally on the active candidate worktree, pending candidate commit.
- `not_applicable`: Procedural rule, governance policy, or human gate.

---

## 3. Requirements Traceability Matrix Table

| ID | Section | Lines | Title | Type | Storage | Historical | Candidate Status | Owner |
|:---|:---|:---:|:---|:---:|:---:|:---:|:---:|:---|
| `A.01-RUN_ID` | A | Lines 36-37 | Canonical Run ID live-66b94b1676bf46a9 | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.02-RECORD_COUNT` | A | Lines 39-40 | TEST Matrix 6,400 Records | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.03-ATTEMPT_COUNT` | A | Lines 42-45 | 6,401 Provider Attempts with Exactly 1 Retry | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.04-STATUS_TAXONOMY` | A | Lines 47-50 | Terminal Status Taxonomy: 6,387 VALID and 13 INCOMPLETE | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.05-SETTLED_COST` | A | Lines 51-53 | Canonical Settled Accounting $6.57575890 USD | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.06-TOTAL_ACCOUNTED` | A | Lines 54-63 | Total Accounted $6.62839900 USD <= $19.99000000 Ceiling | `CANONICAL_INVARIANT` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `A.07-HEADLINE_STATS` | A | Lines 65-81 | Headline Attribution Accuracies & Comparative Statistics | `CANONICAL_INVARIANT` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `A.08-CLAIM_BOUNDARIES` | A | Lines 82-89 | Scientific Non-Claim Discipline | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `B.01-GITHUB_EVIDENCE` | B | Lines 107-117 | Mandatory GitHub Evidence Binding | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `B.02-FAIL_CLOSED_VERDICT` | B | Lines 118-126 | Fail-Closed Verdict Policy | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `C.01-NO_LIVE_EXPERIMENTS` | C | Lines 149-151 | Prohibition of Live Provider Experiments | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `C.02-IMMUTABLE_FROZEN_DATA` | C | Lines 152-160 | Immutable Frozen Data, Protocol, and 13 INCOMPLETEs | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Antigravity |
| `C.03-HUMAN_MERGE_AUTH` | C | Lines 161-168 | Human Authorization Gate for Main Merge | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `D.01-TRACK_A` | D | Lines 184-192 | TRACK A — Canonical Evidence & Terminal Audit | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `D.02-TRACK_B` | D | Lines 184-192 | TRACK B — Scientific Evaluation / RQ1–RQ3 | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `D.03-TRACK_C` | D | Lines 184-192 | TRACK C — Scientific Report | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `D.04-TRACK_D` | D | Lines 184-192 | TRACK D — Figures / Tables / Statistical QA | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `D.05-TRACK_E` | D | Lines 184-192 | TRACK E — Presentation / Reproducibility | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `D.06-TRACK_F` | D | Lines 184-192 | TRACK F — Integration / GitHub / Release QA | `MULTI_AGENT_TRACK` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | TRACK |
| `E.01-REMOTE_SNAPSHOT` | E | Lines 207-226 | GitHub Remote State & Open PR Lineage Audit | `PREFLIGHT_AUDIT` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `E.02-PREFLIGHT_ARTIFACT` | E | Lines 227-246 | Creation of finalization_preflight.json | `PREFLIGHT_AUDIT` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `F.01-TERMINAL_RUN` | F | Lines 257-268 | F1. Terminal Run Verification | `TERMINAL_EVIDENCE` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `F.02-PREDICTION_INVENTORY` | F | Lines 269-289 | F2. Prediction Inventory (5 Conditions, 6,400 Records) | `TERMINAL_EVIDENCE` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `F.03-ATTEMPT_ACCOUNTING` | F | Lines 290-301 | F3. Attempt Accounting (6,401 Attempts) | `TERMINAL_EVIDENCE` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `F.04-OUTCOME_TAXONOMY` | F | Lines 302-312 | F4. Terminal Outcome Taxonomy (6,387 VALID, 13 INCOMPLETE) | `TERMINAL_EVIDENCE` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `F.05-LEDGER_RECONCILIATION` | F | Lines 313-352 | F5. Full Multi-Entity Ledger Reconciliation | `TERMINAL_EVIDENCE` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `F.06-VALIDATOR_DEFECT_CODEX` | F | Lines 353-374 | F6-DEFECT: audit_terminal_process_proof Fails Open on 4 Negative Controls | `DEFECT_INVESTIGATION` | `private_historical` | `FAIL` | **`FAIL`** | Track |
| `F.07-VALIDATOR_EXECUTION` | F | Lines 353-374 | F6. Patched Independent Validator Execution & Production Seal | `TERMINAL_EVIDENCE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `F.08-RAW_ARTIFACT_TRANSPARENCY` | F | Lines 375-386 | Raw Artifact Provenance & Sanitized Derivation Map | `PROVENANCE_INTEGRITY` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `G.01-COHORTS_AND_DENOMINATORS` | G | Lines 395-412 | Formal Cohort Definitions & Denominator Isolation | `METRIC_SPECIFICATION` | `git_tracked` | `VERIFIED` | `PARTIAL` | Track |
| `G.02-CANONICAL_METRIC_BUNDLE` | G | Lines 413-444 | Immutable Canonical Metric Bundle Generation (v2) | `DELIVERABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `H.01-RQ1_CONDITION_SWEEP` | H | Lines 453-466 | RQ1 Condition Sweep (k=0,1,3,5,10) | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `H.02-RQ1_MACRO_F1_474` | H | Lines 467, 472-475 | RQ1 Macro-F1 across Frozen 474 Universe | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `H.03-RQ1_BOOTSTRAP_CI` | H | Lines 468-471, 487-488 | RQ1 Pair-Cluster Bootstrap 95% CI [-2.355, +5.300] pp | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `H.04-RQ1_MCNEMAR` | H | Lines 490-492 | RQ1 McNemar Statistical Test p=0.422 | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `I.01-PROTOCOL_D2I_AXES` | I | Lines 506-520 | Protocol D2i 3-Axis Decomposition | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `I.02-RQ2_EMPIRICAL_K10` | I | Lines 521-542 | RQ2 Empirical Verification at k=10 | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `I.03-RQ2_NON_CAUSAL_WORDING` | I | Lines 543-552 | Non-Causal Associational Wording Standards | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `J.01-RQ3_TRADE_OFF_TABLE` | J | Lines 557-574 | Comprehensive Trade-Off Metrics across k=0,1,3,5,10 | `METRIC_SPECIFICATION` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `J.02-RQ3_COST_WORDING` | J | Lines 575-586 | Tariff-Derived Accounted Cost Wording Standard | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `K.01-PROVIDER_FAILURE_RETRY` | K | Lines 593-597 | Transient Provider Failure Accounting | `FAILURE_ANALYSIS` | `private_historical` | `VERIFIED` | `PARTIAL` | Track |
| `K.02-INCOMPLETE_CEILING_ANALYSIS` | K | Lines 598-617 | 13 INCOMPLETEs at 8,192 Token Ceiling Analysis | `FAILURE_ANALYSIS` | `git_tracked` | `VERIFIED` | `PARTIAL` | Track |
| `K.03-INCOMPLETE_MAPPED_COHORT_EXCLUSION` | K | Lines 618-624 | 0/13 INCOMPLETEs Belong to Mapped Headline Cohort | `FAILURE_ANALYSIS` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `L.SEC-01` | L | Lines 641 | Report Section 1: Title | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-02` | L | Lines 642 | Report Section 2: Abstract | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-03` | L | Lines 643 | Report Section 3: Introduction | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-04` | L | Lines 644 | Report Section 4: Problem statement | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-05` | L | Lines 645 | Report Section 5: Research questions | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-06` | L | Lines 646 | Report Section 6: Related work | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-07` | L | Lines 647-650 | Report Section 7: Background (ATT&CK, RAG, technique attribution) | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-08` | L | Lines 651 | Report Section 8: Dataset | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-09` | L | Lines 652 | Report Section 9: Synthetic data methodology | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-10` | L | Lines 653 | Report Section 10: Ground-truth construction | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-11` | L | Lines 654 | Report Section 11: Experimental design | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-12` | L | Lines 655 | Report Section 12: No-RAG baseline | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-13` | L | Lines 656 | Report Section 13: RAG architecture | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-14` | L | Lines 657 | Report Section 14: Frozen protocol | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-15` | L | Lines 658 | Report Section 15: Model/provider configuration | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-16` | L | Lines 659 | Report Section 16: Retrieval setup | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-17` | L | Lines 660 | Report Section 17: Evaluation metrics | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-18` | L | Lines 661 | Report Section 18: RQ1 results | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-19` | L | Lines 662 | Report Section 19: RQ2 results | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-20` | L | Lines 663 | Report Section 20: RQ3 results | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-21` | L | Lines 664 | Report Section 21: Statistical analysis | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-22` | L | Lines 665 | Report Section 22: Failure analysis | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-23` | L | Lines 666 | Report Section 23: Cost/resource analysis | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-24` | L | Lines 667 | Report Section 24: Discussion | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-25` | L | Lines 668 | Report Section 25: Threats to validity | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-26` | L | Lines 669 | Report Section 26: Limitations | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-27` | L | Lines 670 | Report Section 27: Reproducibility | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-28` | L | Lines 671 | Report Section 28: Conclusion | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-29` | L | Lines 672 | Report Section 29: References | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.SEC-30` | L | Lines 673 | Report Section 30: Appendix / artifact hashes | `REPORT_SECTION` | `git_tracked` | `PARTIAL` | `PARTIAL` | Track |
| `L.DOCX_DELIVERY` | L | Lines 631-637 | Dual Delivery of Markdown and Pristine DOCX | `DELIVERABLE` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `M.01-SYNTHETIC_VS_LIVE` | M | Lines 690-695 | Distinguish Synthetic Inputs vs Real Provider Outputs | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `M.02-DENOMINATOR_DISCIPLINE` | M | Lines 696-704 | Explicit Denominator & Universe Reporting | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `M.03-NON_CAUSAL_DISCIPLINE` | M | Line 685 | Non-Causal Associational Claims Rule | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `M.04-NON_PRODUCTION_DISCIPLINE` | M | Lines 679-688 | No Enterprise SOC / Production Telemetry Generalization Claims | `POLICY` | `git_tracked` | `VERIFIED` | `POLICY_ENFORCED` | Track |
| `N.01-PRIMARY_LITERATURE` | N | Lines 709-725 | Primary Literature Verification (Yang & Hsu, H-TechniqueRAG, ATT&CK v19.2) | `LITERATURE_INTEGRITY` | `git_tracked` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-01` | O | Lines 732-734 | Figure 1: Experimental Architecture | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-02` | O | Lines 735-737 | Figure 2: Accuracy across k | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-03` | O | Lines 738-740 | Figure 3: Macro-F1 across k | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-04` | O | Lines 741-743 | Figure 4: Retrieval Hit@k | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-05` | O | Lines 744-746 | Figure 5: Conditional Accuracy retrieved vs missed | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-06` | O | Lines 747-749 | Figure 6: Latency vs k | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-07` | O | Lines 750-752 | Figure 7: Cost / token usage vs k | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.FIG-08` | O | Lines 753-755 | Figure 8: Failure Decomposition | `PUBLICATION_FIGURE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-01` | O | Lines 758-760 | Table 1: Dataset / split | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-02` | O | Lines 761-763 | Table 2: Experimental conditions | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-03` | O | Lines 764-766 | Table 3: RQ1 metrics | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-04` | O | Lines 767-769 | Table 4: RQ2 retrieval analysis | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-05` | O | Lines 770-772 | Table 5: RQ3 cost / latency | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.TAB-06` | O | Lines 773-775 | Table 6: Provenance / hash / evidence | `PUBLICATION_TABLE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `O.GEN-01` | O | Lines 776-780 | 100% Machine-Generated Figures and Tables | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Track |
| `P.VAL-77.99` | P | Lines 798 | Consistency Value: 77.99 (No-RAG accuracy percentage) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-79.53` | P | Lines 799 | Consistency Value: 79.53 (RAG k=10 accuracy percentage) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-pos_1.532` | P | Lines 800 | Consistency Value: +1.532 (Observed accuracy percentage point delta) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-neg_2.355_pos_5.300` | P | Lines 801 | Consistency Value: [-2.355, +5.300] (Pair-cluster bootstrap 95% CI pp) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-0.422` | P | Lines 802 | Consistency Value: 0.422 (McNemar test p-value) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-6400` | P | Lines 803 | Consistency Value: 6,400 (Total TEST matrix completed records) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-6401` | P | Lines 804 | Consistency Value: 6,401 (Total consumed provider attempts) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-6387` | P | Lines 805 | Consistency Value: 6,387 (Terminal VALID outcomes count) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-13` | P | Lines 806 | Consistency Value: 13 (Terminal INCOMPLETE outcomes count) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-6.57575890` | P | Lines 807 | Consistency Value: 6.57575890 (Canonical settled expenditure USD) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-6.62839900` | P | Lines 808 | Consistency Value: 6.62839900 (Total accounted study expenditure USD) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-19.99000000` | P | Lines 809 | Consistency Value: 19.99000000 (Total study budget ceiling USD) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-718` | P | Lines 810 | Consistency Value: 718 (Mapped/scorable evaluation views cohort) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-311` | P | Lines 811 | Consistency Value: 311 (Ambiguous views cohort) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-251` | P | Lines 812 | Consistency Value: 251 (Unmapped views cohort) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `P.VAL-474` | P | Lines 813 | Consistency Value: 474 (Frozen ATT&CK v19.2 technique benchmark universe) | `CONSISTENCY_VALUE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `Q.01-VIETNAMESE_DECK` | Q | Lines 824-830, 856-858 | Vietnamese Presentation Deck (12 Slides & 12 Speaker Notes) | `DELIVERABLE` | `git_tracked` | `VERIFIED` | `PARTIAL` | Track |
| `Q.02-TYPOGRAPHY_AND_LAYOUT_QA` | Q | Lines 846-855 | Presentation Layout, Font Sizing (>=18pt), and Overflow QA | `PRESENTATION_QA` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `R.01-CLEAN_CLONE_REPRO` | R | Lines 863-875 | Clean-Clone Offline Reproduction Workflow | `REPRODUCIBILITY` | `git_tracked` | `VERIFIED` | `PARTIAL` | Track |
| `R.02-REPRO_VERDICT_ASSERTION` | R | Lines 878-891 | Replay Verdict PASS_CANONICAL_OFFLINE_VERIFIED & attempted_egress=0 | `REPRODUCIBILITY` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `S.01-SECRETS_AND_PATHS_SCAN` | S | Lines 896-910 | Comprehensive Scanner: Zero Secrets, Zero Private Paths, Zero Bytecode | `SECURITY_AUDIT` | `release_asset` | `VERIFIED` | `PARTIAL` | Track |
| `T.01-PR_CLASSIFICATION_AND_ANCESTRY` | T | Lines 924-954 | Classification and Ancestry Audit of PRs #8, #24–#29 | `PR_AUDIT` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `U.01-DIFF_AUDIT` | U | Lines 969-982 | Full Diff Audit against Protected Baseline | `DIFF_AUDIT` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `V.01-RUFF_CHECK` | V | Line 990 | Suite 1: ruff check | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.02-RUFF_FORMAT` | V | Line 992 | Suite 2: ruff format --check | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.03-OFFLINE_UNIT` | V | Line 996 | Suite 3: Offline unit test suite | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.04-INTEGRATION_SUITE` | V | Line 999 | Suite 4: Integration test suite (no provider) | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.05-SYNTHETIC_DATA` | V | Line 1002 | Suite 5: Synthetic data verification | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.06-CANONICAL_REPLAY` | V | Line 1005 | Suite 6: Canonical replay test | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.07-CANONICAL_MANIFEST` | V | Line 1008 | Suite 7: Canonical manifest verification | `TEST_SUITE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Track |
| `V.08-RQ_KNOWN_ANSWER` | V | Line 1011 | Suite 8: RQ analysis known-answer tests | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `V.09-REPORT_METADATA` | V | Line 1014 | Suite 9: Report metadata verification | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `V.10-PRESENTATION_REGRESSION` | V | Line 1017 | Suite 10: Presentation regression tests | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `V.11-PATH_SECRET_SCANNER` | V | Line 1020 | Suite 11: Path and secret scanner | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `V.12-CROSS_ARTIFACT_TEST` | V | Line 1023 | Suite 12: Cross-artifact consistency test | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `V.13-TERMINAL_VALIDATOR` | V | Line 1026 | Suite 13: Independent terminal validator suite | `TEST_SUITE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `W.01-GITHUB_CI_GREEN` | W | Lines 1043-1060 | All GitHub Actions CI Workflows Pass on Final SHA | `CI_MONITORING` | `local_pending` | `VERIFIED` | `PARTIAL` | Track |
| `X.01-REPO_STATE` | X | Lines 1070-1075 | Repository State Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.02-CANONICAL_EXP` | X | Lines 1076-1082 | Canonical Experiment Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.03-SCIENTIFIC_RES` | X | Lines 1083-1088 | Scientific Results Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.04-ARTIFACTS` | X | Lines 1089-1096 | Artifacts Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.05-VERIFICATION` | X | Lines 1097-1103 | Verification Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.06-LIMITATIONS` | X | Line 1104 | Remaining Known Limitations Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `X.07-MERGE_RECOMMENDATION` | X | Line 1106 | Merge Recommendation Section | `FINAL_REVIEW_FIELD` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `Y.01-READY_FOR_MERGE_GATE` | Y | Lines 1114-1122 | READY_FOR_HUMAN_FINAL_MERGE Gate | `GOVERNANCE_GATE` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `Z.01-POST_MERGE_CLEANUP` | Z | Lines 1141-1150 | Post-Merge PR Closure and Stale Marker Cleanup | `POST_MERGE_CLEANUP` | `not_applicable` | `NOT_APPLICABLE` | `NOT VERIFIED` | Track |
| `AA.01-RELEASE_TAG` | AA | Lines 1156-1174 | Official Release Tagging v1.0.0-rag2attck-study | `RELEASE` | `release_asset` | `PARTIAL` | `NOT VERIFIED` | Track |
| `DOD-01` | AB | Line 1184 | DoD #01: canonical 6400/6400 verified | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-02` | AB | Line 1185 | DoD #02: 6401 attempts reconciled | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-03` | AB | Line 1186 | DoD #03: terminal evidence verified | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-04` | AB | Line 1187 | DoD #04: ledger reconciled | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-05` | AB | Line 1188 | DoD #05: budget safe | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-06` | AB | Line 1189 | DoD #06: canonical metric bundle frozen | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-07` | AB | Line 1190 | DoD #07: RQ1 verified | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-08` | AB | Line 1191 | DoD #08: RQ2 verified | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-09` | AB | Line 1192 | DoD #09: RQ3 verified | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-10` | AB | Line 1193 | DoD #10: report final | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-11` | AB | Line 1194 | DoD #11: DOCX final | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-12` | AB | Line 1195 | DoD #12: figures final | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-13` | AB | Line 1196 | DoD #13: tables final | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-14` | AB | Line 1197 | DoD #14: slides final | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-15` | AB | Line 1198 | DoD #15: reproduction works from clean clone | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-16` | AB | Line 1199 | DoD #16: zero provider calls during reproduction | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-17` | AB | Line 1200 | DoD #17: no secrets/private paths | `DOD_GATE` | `local_pending` | `PARTIAL` | `NOT VERIFIED` | Antigravity |
| `DOD-18` | AB | Line 1201 | DoD #18: cross-artifact numbers match | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-19` | AB | Line 1202 | DoD #19: all tests pass | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-20` | AB | Line 1203 | DoD #20: CI pass at final exact SHA | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-21` | AB | Line 1204 | DoD #21: PR integration resolved | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-22` | AB | Line 1205 | DoD #22: main contains final state | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-23` | AB | Line 1206 | DoD #23: superseded PRs cleaned | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-24` | AB | Line 1207 | DoD #24: final evidence package committed | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `DOD-25` | AB | Line 1208 | DoD #25: release/tag completed or explicitly deferred by human | `DOD_GATE` | `local_pending` | `NOT_APPLICABLE` | `NOT VERIFIED` | Antigravity |
| `AC.01-SELF_CORRECTION` | AC | Lines 1216-1232 | Systematic Diagnosis & Repair Protocol | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `AD.01-REVIEWER_ESCALATION` | AD | Lines 1234-1253 | Evidence-Backed Escalation Protocol | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `AE.01-RESPONSE_FORMAT` | AE | Lines 1255-1331 | Structured Response Template Compliance | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |
| `AF.01-PRIORITY_ORDER` | AF | Lines 1333-1348 | P0 through P7 Hierarchy Enforcement | `POLICY` | `not_applicable` | `NOT_APPLICABLE` | `POLICY_ENFORCED` | Antigravity |

---

## 4. Detailed Specification & Closure Steps

### `A.01-RUN_ID`: Canonical Run ID live-66b94b1676bf46a9

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 36-37)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Recorded in original run summary and canonical_run_seal_v1.json.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `artifacts/experiments/synthetic-paired-test-1/run_summary.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `67df38e336b4250b5a5c044b754ab02e8cc1826b8569f76d9bdf265ae4f84c2a`
- **Description:** Run ID must remain frozen at live-66b94b1676bf46a9.
- **Closure Step:** Phase 1 patched terminal validator verification.

### `A.02-RECORD_COUNT`: TEST Matrix 6,400 Records

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 39-40)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (6,400 records verified in canonical bundle and root independent counts.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/run_summary.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `67df38e336b4250b5a5c044b754ab02e8cc1826b8569f76d9bdf265ae4f84c2a`
- **Description:** Matrix must contain exactly 6,400 completed records across 5 conditions.
- **Closure Step:** Phase 1 independent validator assertion on candidate.

### `A.03-ATTEMPT_COUNT`: 6,401 Provider Attempts with Exactly 1 Retry

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 42-45)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Request journal audited: 6,401 requests consumed, 1 retry.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/request_journal.jsonl`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`
- **Description:** Consumed provider attempts must equal 6,401 with exactly 1 retry recorded.
- **Closure Step:** Phase 1 attempt accounting join in audit_terminal_run.py.

### `A.04-STATUS_TAXONOMY`: Terminal Status Taxonomy: 6,387 VALID and 13 INCOMPLETE

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 47-50)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Taxonomy confirmed: 6387 VALID, 13 INCOMPLETE (0 no_rag, 0 k1, 6 k3, 3 k5, 4 k10).)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/request_journal.jsonl`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`
- **Description:** Exactly 6,387 VALID and 13 INCOMPLETE records. Zero removed records.
- **Closure Step:** Phase 1 validator check.

### `A.05-SETTLED_COST`: Canonical Settled Accounting $6.57575890 USD

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 51-53)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Study ledger settled cost exactly $6.57575890 in Decimal.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/study_ledger.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8`
- **Description:** Settled cost across 6,400 records must match 6.57575890 USD exactly via Decimal.
- **Closure Step:** Phase 1 ledger reconciliation.

### `A.06-TOTAL_ACCOUNTED`: Total Accounted $6.62839900 USD <= $19.99000000 Ceiling

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 54-63)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Zero budget breach confirmed; remaining budget $13.36160100 USD.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/study_ledger.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8`
- **Description:** $6.57575890 settled + $0.05264010 pilot hold = $6.62839900 USD total; 0 breach.
- **Closure Step:** Phase 1 ledger audit.

### `A.07-HEADLINE_STATS`: Headline Attribution Accuracies & Comparative Statistics

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 65-81)
- **Item Type:** `CANONICAL_INVARIANT`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Headline numbers verified in public bundle rq_analysis.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/rq_analysis.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`
- **Description:** No-RAG 560/718 (77.99%), RAG k=10 571/718 (79.53%), delta +1.532 pp, bootstrap 95% CI [-2.355, +5.300] pp, McNemar p=0.422.
- **Closure Step:** Phase 2 freeze into canonical_metric_bundle_v2.json.

### `A.08-CLAIM_BOUNDARIES`: Scientific Non-Claim Discipline

- **Section & Mapping:** A. TRẠNG THÁI ĐÃ BIẾT (Lines 82-89)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Explicitly stated in report Abstract, Introduction, and Limitations.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** No general RAG superiority claims; no causal attribution; no generalization to production host telemetry.
- **Closure Step:** Automated text scan across report and slides.

### `B.01-GITHUB_EVIDENCE`: Mandatory GitHub Evidence Binding

- **Section & Mapping:** B. SOURCE OF TRUTH (Lines 107-117)
- **Item Type:** `POLICY`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (CI workflows enforce deterministic test execution on GitHub runners.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `.github/workflows/ci.yml`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `25227d8ce6b42b103196c8d7b3014a0adbe4826f0430e3fc652b363573c09b9c`
- **Description:** All PASS claims must bind exact commit SHA, command, exit code, count, artifact hash, and GitHub CI URL.
- **Closure Step:** Enforce in all review documents and PR descriptions.

### `B.02-FAIL_CLOSED_VERDICT`: Fail-Closed Verdict Policy

- **Section & Mapping:** B. SOURCE OF TRUTH (Lines 118-126)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead & Codex
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance rule.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Missing evidence must evaluate to NOT VERIFIED; failures evaluate to FAIL; never claim PASS without proof.
- **Closure Step:** Applied throughout requirements matrix.

### `C.01-NO_LIVE_EXPERIMENTS`: Prohibition of Live Provider Experiments

- **Section & Mapping:** C. QUYỀN HẠN (Lines 149-151)
- **Item Type:** `POLICY`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (OFFLINE_GUARD socket barrier active in all reproduction and test suites.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `scripts/run_offline_tests.py`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `fbe51fcfe6fc197b102ce62ebff4e095819777174db2744bf8332155d3bbfe2c`
- **Description:** Zero live provider/API experiment calls with financial cost.
- **Closure Step:** Verify attempted_egress=0 on all replay runs.

### `C.02-IMMUTABLE_FROZEN_DATA`: Immutable Frozen Data, Protocol, and 13 INCOMPLETEs

- **Section & Mapping:** C. QUYỀN HẠN (Lines 152-160)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Protocol and code manifest locked; 22 protected files matched.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `config/canonical_experiment_lock_v1.json`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `b2f0c78a049d564fa72186eebe679ae14df75da61e9389c9377484df70420f4c`
- **Description:** No mutation of experimental data, ground truth, benchmark scope, prompt, protocol, or exclusion of 13 INCOMPLETEs.
- **Closure Step:** Assert zero scientific mutation in diff audit.

### `C.03-HUMAN_MERGE_AUTH`: Human Authorization Gate for Main Merge

- **Section & Mapping:** C. QUYỀN HẠN (Lines 161-168)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead & User
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance gate.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Only human may authorize main merge, research scope changes, or live rerun.
- **Closure Step:** Halt at READY_FOR_HUMAN_FINAL_MERGE.

### `D.01-TRACK_A`: TRACK A — Canonical Evidence & Terminal Audit

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK A
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Canonical evidence verification, journal joins, financial ledger, patched terminal validator. Owned files: scripts/audit_terminal_run.py, tests/test_terminal_audit.py, reports/evidence/canonical_run_seal_v1.json.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `D.02-TRACK_B`: TRACK B — Scientific Evaluation / RQ1–RQ3

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK B
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Dataset freeze, cohort definitions (1280/718/311/251), Macro-F1 across 474 universe, RQ1-RQ3 metrics. Owned files: artifacts/results/canonical_metric_bundle_v2.json, scripts/analysis/evaluate_rqs.py.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `D.03-TRACK_C`: TRACK C — Scientific Report

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK C
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Complete 30-section scientific report in Markdown and DOCX, primary literature verification. Owned files: docs/report/scientific_report.md, docs/report/scientific_report.docx.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `D.04-TRACK_D`: TRACK D — Figures / Tables / Statistical QA

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK D
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Machine-generate 8 figures (PDF/PNG), 6 tables (MD/JSON), automated cross-artifact consistency checker. Owned files: docs/report/figures/, docs/report/tables/, tests/test_cross_artifact_consistency.py.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `D.05-TRACK_E`: TRACK E — Presentation / Reproducibility

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK E
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Vietnamese 12-slide presentation deck maintenance, speaker notes, clean-clone offline reproduction guide. Owned files: docs/presentation/slides.pptx, docs/presentation/slides.md, REPRODUCTION_GUIDE.md.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `D.06-TRACK_F`: TRACK F — Integration / GitHub / Release QA

- **Section & Mapping:** D. CHẾ ĐỘ LÀM VIỆC (Lines 184-192)
- **Item Type:** `MULTI_AGENT_TRACK`
- **Owner:** TRACK F
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Structural track organization.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** PR ancestry audit (#8, #24-#29), CI monitoring, final review package, diff audit, release packaging. Owned files: reports/evidence/FINAL_REVIEW_PACKAGE.md, final handover package.
- **Closure Step:** Sequential execution with disjoint file ownership.

### `E.01-REMOTE_SNAPSHOT`: GitHub Remote State & Open PR Lineage Audit

- **Section & Mapping:** E. PHASE 0 — SNAPSHOT TRẠNG THÁI HIỆN TẠI (Lines 207-226)
- **Item Type:** `PREFLIGHT_AUDIT`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Codex independent preflight recorded with 7 PRs audited.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/finalization_preflight.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `9587efd7e00352a1f34032ab19d523d5c1c255a206a05937c1b3a3c7fff5b24a`
- **Description:** Fetch GitHub remote, record main SHA, all open PRs (#8, #24-#29), mergeability, head SHAs, and CI status.
- **Closure Step:** Committed on candidate branch codex/finalization-20261003 in PR #30.

### `E.02-PREFLIGHT_ARTIFACT`: Creation of finalization_preflight.json

- **Section & Mapping:** E. PHASE 0 — SNAPSHOT TRẠNG THÁI HIỆN TẠI (Lines 227-246)
- **Item Type:** `PREFLIGHT_AUDIT`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (File created by Codex on candidate worktree.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/finalization_preflight.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `9587efd7e00352a1f34032ab19d523d5c1c255a206a05937c1b3a3c7fff5b24a`
- **Description:** Establish reports/evidence/finalization_preflight.json containing UTC timestamp, PR lineage, bundle hashes, protected hashes, and blockers.
- **Closure Step:** Preserve unmodified as baseline snapshot.

### `F.01-TERMINAL_RUN`: F1. Terminal Run Verification

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 257-268)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Terminal process proof records pid 50192 exit 0, task-1264 completed.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `artifacts/orchestration/terminal_process_proof_20261002.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e`
- **Description:** Verify run complete, 6,400 records, execution_mode=live, run_id=live-66b94b1676bf46a9, no active runner, locks released, run_summary valid.
- **Closure Step:** Phase 1 patched terminal validator assertion.

### `F.02-PREDICTION_INVENTORY`: F2. Prediction Inventory (5 Conditions, 6,400 Records)

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 269-289)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (All 5 prediction files audited in canonical bundle.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Multiple (no_rag: 70034c5e..., k1: 745cb883..., k3: 29f215d7..., k5: 896d900d..., k10: 40cd9d2b...)`
- **Description:** 1,280 records each in no_rag, rag_k1, rag_k3, rag_k5, rag_k10. Zero duplicates, zero missing, valid JSON.
- **Closure Step:** Re-verified in Phase 1 validator run.

### `F.03-ATTEMPT_ACCOUNTING`: F3. Attempt Accounting (6,401 Attempts)

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 290-301)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Single retry ordinal identified and verified.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/request_journal.jsonl`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`
- **Description:** Account for exactly 6,401 attempts: verify 1 retry, attempt ordinals, initial attempt failure, subsequent success, zero duplicate completions.
- **Closure Step:** Phase 1 attempt accounting join.

### `F.04-OUTCOME_TAXONOMY`: F4. Terminal Outcome Taxonomy (6,387 VALID, 13 INCOMPLETE)

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 302-312)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Distribution audited: 6387 VALID, 13 INCOMPLETE.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/request_journal.jsonl`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`
- **Description:** Verify distribution across conditions: 0 no_rag, 0 k1, 6 k3, 3 k5, 4 k10; no silent removal of INCOMPLETEs.
- **Closure Step:** Phase 1 validator assertion.

### `F.05-LEDGER_RECONCILIATION`: F5. Full Multi-Entity Ledger Reconciliation

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 313-352)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (All 6,400 joins passed in test_monetary_guard.py.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/study_ledger.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8`
- **Description:** Join verification for all 6,400 records across prediction <-> journal <-> receipt <-> settlement <-> study ledger. Exact Decimal settled $6.57575890, hold $0.05264010, total $6.62839900.
- **Closure Step:** Phase 1 validator execution on canonical data.

### `F.06-VALIDATOR_DEFECT_CODEX`: F6-DEFECT: audit_terminal_process_proof Fails Open on 4 Negative Controls

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 353-374)
- **Item Type:** `DEFECT_INVESTIGATION`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `FAIL`
- **Historical Status:** `FAIL` (Independently discovered and proven by Codex unit probe and full CLI probe.)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `finalization_20261003/root_terminal_proof_probe.json and root_production_cli_probe.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e`
- **Description:** audit_terminal_process_proof in scripts/audit_terminal_run.py (PR #29, SHA 9c5d6c8a, validator hash f4d81efd...) accepts 4 negative controls (missing required live fields, wrong run count/mode, complete=null, unbound log digest). Full production CLI exit 0 incorrectly.
- **Closure Step:** In Track A, patch audit_terminal_process_proof to strictly require complete=True, execution_mode='live', canonical run_id, record_count=6400, requests_consumed=6401, bind log digest bytes, and add 4 regression tests in tests/test_terminal_audit.py.

### `F.07-VALIDATOR_EXECUTION`: F6. Patched Independent Validator Execution & Production Seal

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 353-374)
- **Item Type:** `TERMINAL_EVIDENCE`
- **Owner:** Track A (Canonical Evidence & Terminal Audit)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical seal exists in validator_prep but validator had negative-control defect.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/canonical_run_seal_v1.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Execute patched audit_terminal_run.py on canonical evidence: exit 0, zero egress, 22 protected files verified, true production seal (fixture_only=false).
- **Closure Step:** Run patched validator CLI on candidate in Phase 1.

### `F.08-RAW_ARTIFACT_TRANSPARENCY`: Raw Artifact Provenance & Sanitized Derivation Map

- **Section & Mapping:** F. PHASE 1 — CANONICAL TERMINAL EVIDENCE (Lines 375-386)
- **Item Type:** `PROVENANCE_INTEGRITY`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Artifact inventory clearly demarcates git-tracked, release assets, and private originals.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/finalization_artifact_inventory.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Computed in inventory`
- **Description:** Do not pretend private raw data is in Git; provide immutable hashes, public sanitized manifest, derivation map, reproduction instructions.
- **Closure Step:** Finalize derivation map in release documentation.

### `G.01-COHORTS_AND_DENOMINATORS`: Formal Cohort Definitions & Denominator Isolation

- **Section & Mapping:** G. PHASE 2 — FREEZE SCIENTIFIC DATASET (Lines 395-412)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Cohorts documented in Section 8 of report; need formal machine-readable cohort schema.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Total TEST: 1,280 views; Mapped/scorable: 718; Ambiguous: 311; Unmapped: 251. Strict denominator labeling on every table/metric; no denominator mixing.
- **Closure Step:** Embed formal cohort specification in canonical_metric_bundle_v2.json.

### `G.02-CANONICAL_METRIC_BUNDLE`: Immutable Canonical Metric Bundle Generation (v2)

- **Section & Mapping:** G. PHASE 2 — FREEZE SCIENTIFIC DATASET (Lines 413-444)
- **Item Type:** `DELIVERABLE`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Individual output JSONs exist in public bundle; consolidated bundle v2 pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `artifacts/results/canonical_metric_bundle_v2.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending generation`
- **Description:** Generate artifacts/results/canonical_metric_bundle_v2.json containing provenance, source hashes, code hash, run ID, cohorts, metric definitions, RQ1-RQ3, tests, cost, latency, diagnostics, failure taxonomy, SHA-256.
- **Closure Step:** Execute Phase 2 freeze script, compute SHA-256, lock before downstream population.

### `H.01-RQ1_CONDITION_SWEEP`: RQ1 Condition Sweep (k=0,1,3,5,10)

- **Section & Mapping:** H. PHASE 3 — RQ1 FINAL ANALYSIS (Lines 453-466)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Calculated and verified in public package rq_analysis.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/rq_analysis.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`
- **Description:** Compute correct, total, accuracy, error rate across all 5 conditions.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json.

### `H.02-RQ1_MACRO_F1_474`: RQ1 Macro-F1 across Frozen 474 Universe

- **Section & Mapping:** H. PHASE 3 — RQ1 FINAL ANALYSIS (Lines 467, 472-475)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Calculated and verified in public package rq_analysis.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/rq_analysis.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`
- **Description:** Macro-F1 evaluated across frozen 474 ATT&CK techniques; zero class subsetting.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json.

### `H.03-RQ1_BOOTSTRAP_CI`: RQ1 Pair-Cluster Bootstrap 95% CI [-2.355, +5.300] pp

- **Section & Mapping:** H. PHASE 3 — RQ1 FINAL ANALYSIS (Lines 468-471, 487-488)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Calculated and verified in public package rq_analysis.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/rq_analysis.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`
- **Description:** Evaluate pair-cluster bootstrap confidence interval for delta vs No-RAG.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json.

### `H.04-RQ1_MCNEMAR`: RQ1 McNemar Statistical Test p=0.422

- **Section & Mapping:** H. PHASE 3 — RQ1 FINAL ANALYSIS (Lines 490-492)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Calculated and verified in public package rq_analysis.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/rq_analysis.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `1604a5537b57cefbe86fd59d7fa2acfb8658a27215f7df8a98dfd0c400981156`
- **Description:** Evaluate McNemar test on paired views; verify p=0.422; no claim of statistical significance.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json.

### `I.01-PROTOCOL_D2I_AXES`: Protocol D2i 3-Axis Decomposition

- **Section & Mapping:** I. PHASE 4 — RQ2 RETRIEVAL QUALITY (Lines 506-520)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Confirmed in failure_decomposition.json and retrieval_conditional_metrics.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/failure_decomposition.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `2f6bbd6880ea83296c05a1097fa62ddf42813589b2ce3738a9d31d4512e09395`
- **Description:** Decompose into 3 overlapping axes: Axis 1 Retrieval Miss, Axis 2 Downstream Gen Failure, Axis 3 Joint Overlap.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json and Table 4.

### `I.02-RQ2_EMPIRICAL_K10`: RQ2 Empirical Verification at k=10

- **Section & Mapping:** I. PHASE 4 — RQ2 RETRIEVAL QUALITY (Lines 521-542)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Confirmed in failure_decomposition.json and retrieval_conditional_metrics.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/failure_decomposition.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `2f6bbd6880ea83296c05a1097fa62ddf42813589b2ce3738a9d31d4512e09395`
- **Description:** Hit@10 321/718 (44.71%), Miss 397/718 (55.29%), Acc|retrieved 293/321 (91.28%), Acc|missed 278/397 (70.03%), Wrong 147, Miss ∩ Wrong 119/147 (80.95%).
- **Closure Step:** Bind into canonical_metric_bundle_v2.json and Table 4.

### `I.03-RQ2_NON_CAUSAL_WORDING`: Non-Causal Associational Wording Standards

- **Section & Mapping:** I. PHASE 4 — RQ2 RETRIEVAL QUALITY (Lines 543-552)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Confirmed in failure_decomposition.json and retrieval_conditional_metrics.json.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/failure_decomposition.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `2f6bbd6880ea83296c05a1097fa62ddf42813589b2ce3738a9d31d4512e09395`
- **Description:** Use 'associated with', 'conditional accuracy', 'observed relationship'; strictly avoid causal claims.
- **Closure Step:** Bind into canonical_metric_bundle_v2.json and Table 4.

### `J.01-RQ3_TRADE_OFF_TABLE`: Comprehensive Trade-Off Metrics across k=0,1,3,5,10

- **Section & Mapping:** J. PHASE 5 — RQ3 DEPTH / COST / LATENCY (Lines 557-574)
- **Item Type:** `METRIC_SPECIFICATION`
- **Owner:** Track B (Scientific Evaluation / RQ1–RQ3)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Metrics computed; formal consolidated Table 5 pending machine-generation.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/per_condition_metrics.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `e6592f9a0f97739be1168f9d1448e0d209fe4a300727ff6ad78902523f1591d6`
- **Description:** Compute accuracy, Macro-F1, Hit@k, prompt tokens, completion tokens, cached tokens, total tokens, mean/median latency, p95 (if authorized), cost/query, total condition cost, failure rate.
- **Closure Step:** Generate Table 5 machine artifact.

### `J.02-RQ3_COST_WORDING`: Tariff-Derived Accounted Cost Wording Standard

- **Section & Mapping:** J. PHASE 5 — RQ3 DEPTH / COST / LATENCY (Lines 575-586)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Section 23 of report adheres to tariff-derived accounted cost terminology.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Do not mix estimated billing with actual provider invoice; use wording 'tariff-derived accounted cost' or 'pricing-contract-derived cost'.
- **Closure Step:** Verify wording across all artifacts.

### `K.01-PROVIDER_FAILURE_RETRY`: Transient Provider Failure Accounting

- **Section & Mapping:** K. PHASE 6 — FAILURE ANALYSIS (Lines 593-597)
- **Item Type:** `FAILURE_ANALYSIS`
- **Owner:** Track B (Scientific Evaluation) & Track C (Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Recorded in journal line 5124 (attempt 1 API_FAILURE, attempt 2 SUCCESS).)
- **Evidence Storage:** `private_historical`
- **Evidence Path:** `canonical-accepted-bundle-v2/inputs/request_journal.jsonl`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31`
- **Description:** Document 1 transient API failure retry -> success in report and journal join.
- **Closure Step:** Document in failure section of report.

### `K.02-INCOMPLETE_CEILING_ANALYSIS`: 13 INCOMPLETEs at 8,192 Token Ceiling Analysis

- **Section & Mapping:** K. PHASE 6 — FAILURE ANALYSIS (Lines 598-617)
- **Item Type:** `FAILURE_ANALYSIS`
- **Owner:** Track B (Scientific Evaluation) & Track C (Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Documented in Section 22 of report and REPRODUCTION_GUIDE.md.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** 13 INCOMPLETE outputs reaching max_output_tokens=8192; fail-closed parsing without heuristic repair. Distribution: 0 no_rag, 0 k1, 6 k3, 3 k5, 4 k10.
- **Closure Step:** Embed in failure figure (Figure 8).

### `K.03-INCOMPLETE_MAPPED_COHORT_EXCLUSION`: 0/13 INCOMPLETEs Belong to Mapped Headline Cohort

- **Section & Mapping:** K. PHASE 6 — FAILURE ANALYSIS (Lines 618-624)
- **Item Type:** `FAILURE_ANALYSIS`
- **Owner:** Track B (Scientific Evaluation) & Track C (Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Cross-cohort join proves all 13 INCOMPLETEs are on unmapped/ambiguous views.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::03_public_canonical_package/outputs/failure_decomposition.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `2f6bbd6880ea83296c05a1097fa62ddf42813589b2ce3738a9d31d4512e09395`
- **Description:** Verify and report that 0 of the 13 INCOMPLETE outputs belong to the headline 718 mapped cohort.
- **Closure Step:** Re-verify in canonical_metric_bundle_v2.json.

### `L.SEC-01`: Report Section 1: Title

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 641)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Title. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-02`: Report Section 2: Abstract

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 642)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Abstract. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-03`: Report Section 3: Introduction

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 643)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Introduction. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-04`: Report Section 4: Problem statement

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 644)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Problem statement. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-05`: Report Section 5: Research questions

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 645)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Research questions. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-06`: Report Section 6: Related work

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 646)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Related work. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-07`: Report Section 7: Background (ATT&CK, RAG, technique attribution)

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 647-650)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Background (ATT&CK, RAG, technique attribution). Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-08`: Report Section 8: Dataset

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 651)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Dataset. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-09`: Report Section 9: Synthetic data methodology

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 652)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Synthetic data methodology. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-10`: Report Section 10: Ground-truth construction

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 653)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Ground-truth construction. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-11`: Report Section 11: Experimental design

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 654)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Experimental design. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-12`: Report Section 12: No-RAG baseline

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 655)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: No-RAG baseline. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-13`: Report Section 13: RAG architecture

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 656)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: RAG architecture. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-14`: Report Section 14: Frozen protocol

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 657)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Frozen protocol. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-15`: Report Section 15: Model/provider configuration

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 658)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Model/provider configuration. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-16`: Report Section 16: Retrieval setup

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 659)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Retrieval setup. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-17`: Report Section 17: Evaluation metrics

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 660)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Evaluation metrics. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-18`: Report Section 18: RQ1 results

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 661)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: RQ1 results. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-19`: Report Section 19: RQ2 results

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 662)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: RQ2 results. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-20`: Report Section 20: RQ3 results

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 663)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: RQ3 results. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-21`: Report Section 21: Statistical analysis

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 664)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Statistical analysis. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-22`: Report Section 22: Failure analysis

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 665)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Failure analysis. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-23`: Report Section 23: Cost/resource analysis

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 666)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Cost/resource analysis. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-24`: Report Section 24: Discussion

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 667)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Discussion. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-25`: Report Section 25: Threats to validity

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 668)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Threats to validity. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-26`: Report Section 26: Limitations

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 669)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Limitations. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-27`: Report Section 27: Reproducibility

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 670)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Reproducibility. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-28`: Report Section 28: Conclusion

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 671)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Conclusion. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-29`: Report Section 29: References

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 672)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: References. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.SEC-30`: Report Section 30: Appendix / artifact hashes

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 673)
- **Item Type:** `REPORT_SECTION`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `PARTIAL` (Present in 35-page report v6; pending expansion to 8 figures and 6 tables.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Mandatory final report section: Appendix / artifact hashes. Must contain no scaffold text.
- **Closure Step:** Audit completeness and export matching pristine DOCX.

### `L.DOCX_DELIVERY`: Dual Delivery of Markdown and Pristine DOCX

- **Section & Mapping:** L. PHASE 7 — SCIENTIFIC REPORT FINAL (Lines 631-637)
- **Item Type:** `DELIVERABLE`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (DOCX exists in release v3 (hash 431c4b05...); needs final check after 8 figures and 6 tables integrated.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/scientific_report.docx`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `431c4b05fca249526df443dba347bac96a9f17df42f83b8b33f33b39f49d3d16`
- **Description:** Deliver final docs/report/scientific_report.md and docs/report/scientific_report.docx without scaffold wording.
- **Closure Step:** Export matching DOCX.

### `M.01-SYNTHETIC_VS_LIVE`: Distinguish Synthetic Inputs vs Real Provider Outputs

- **Section & Mapping:** M. REPORT QUALITY RULES (Lines 690-695)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Demarcated in report Section 8 (Dataset) and Section 15 (Provider Config).)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Explicitly distinguish synthetic benchmark endpoint inputs from real provider LLM outputs throughout all report text and metadata.
- **Closure Step:** Enforce wording compliance in final report audit.

### `M.02-DENOMINATOR_DISCIPLINE`: Explicit Denominator & Universe Reporting

- **Section & Mapping:** M. REPORT QUALITY RULES (Lines 696-704)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Explicitly defined in report Section 8 and Section 17.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Must explicitly report: synthetic benchmark universe (474 frozen techniques), ATT&CK v19.2 version, breakdown of mapped (718), unmapped (251), and ambiguous (311) views, and scorable headline denominator (718).
- **Closure Step:** Verify across all 6 tables and 8 figures.

### `M.03-NON_CAUSAL_DISCIPLINE`: Non-Causal Associational Claims Rule

- **Section & Mapping:** M. REPORT QUALITY RULES (Line 685)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Section 19 (RQ2) audited for non-causal phrasing.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Never claim causal retrieval effects when conducting conditional analyses; use associational language only ('associated with', 'observed conditional accuracy').
- **Closure Step:** Text scan for forbidden causal phrasing.

### `M.04-NON_PRODUCTION_DISCIPLINE`: No Enterprise SOC / Production Telemetry Generalization Claims

- **Section & Mapping:** M. REPORT QUALITY RULES (Lines 679-688)
- **Item Type:** `POLICY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `VERIFIED` (Codified in Section 26 (Limitations) and Section 25 (Threats to Validity).)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/report/scientific_report.md`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `0ceb0e5d1656f4d2c88f11379ecb001a182b8a0ff1bb4025d576a8fa3d20476e`
- **Description:** Strictly prohibit claims of production efficacy, enterprise SOC performance, or real-world generalization; do not refer to synthetic logs as real Windows APT telemetry; do not use 'proves'; no cherry-picking.
- **Closure Step:** Text scan for hype words ('proves', 'enterprise SOC', 'production').

### `N.01-PRIMARY_LITERATURE`: Primary Literature Verification (Yang & Hsu, H-TechniqueRAG, ATT&CK v19.2)

- **Section & Mapping:** N. RELATED WORK (Lines 709-725)
- **Item Type:** `LITERATURE_INTEGRITY`
- **Owner:** Track C (Scientific Report)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Verified in PR #8; needs integration into main report Section 6.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `reports/T33_related_work.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `25a585750d87fa05e94b2a8d3e2303bb2ba4ef5b0e50b182fb8f38c356f9ee5b`
- **Description:** Integrate primary evidence from PR #8 (reports/T33_related_work.md) into Section 6 of report; zero invented DOIs/venues.
- **Closure Step:** Synthesize PR #8 into Section 6 of docs/report/scientific_report.md.

### `O.FIG-01`: Figure 1: Experimental Architecture

- **Section & Mapping:** O. FIGURES & TABLES (Lines 732-734)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-01.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Architecture diagram of the synthetic benchmark, RAG retriever, LLM provider, and failure classification pipeline. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-02`: Figure 2: Accuracy across k

- **Section & Mapping:** O. FIGURES & TABLES (Lines 735-737)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-02.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** ATT&CK attribution accuracy across No-RAG and RAG k=1, 3, 5, 10. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-03`: Figure 3: Macro-F1 across k

- **Section & Mapping:** O. FIGURES & TABLES (Lines 738-740)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-03.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Macro-F1 score across k=0, 1, 3, 5, 10 on frozen 474-class universe. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-04`: Figure 4: Retrieval Hit@k

- **Section & Mapping:** O. FIGURES & TABLES (Lines 741-743)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-04.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Retrieval Hit@k curve across k=1, 3, 5, 10. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-05`: Figure 5: Conditional Accuracy retrieved vs missed

- **Section & Mapping:** O. FIGURES & TABLES (Lines 744-746)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-05.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Downstream accuracy conditioned on whether the ground-truth technique was retrieved vs missed. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-06`: Figure 6: Latency vs k

- **Section & Mapping:** O. FIGURES & TABLES (Lines 747-749)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-06.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Mean and median query execution latency as a function of retrieval depth k. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-07`: Figure 7: Cost / token usage vs k

- **Section & Mapping:** O. FIGURES & TABLES (Lines 750-752)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-07.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Prompt, completion, and accounted tariff cost across k=0, 1, 3, 5, 10. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.FIG-08`: Figure 8: Failure Decomposition

- **Section & Mapping:** O. FIGURES & TABLES (Lines 753-755)
- **Item Type:** `PUBLICATION_FIGURE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (3 canonical figures exist in v6; full set of 8 distinct figures pending generation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/figures/o_fig-08.png`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Protocol D2i 3-axis failure breakdown: retrieval misses, generation errors, and joint overlap. Must be machine-generated from frozen bundle in both PDF and PNG formats.
- **Closure Step:** Generate via scripts/generate_publication_figures.py.

### `O.TAB-01`: Table 1: Dataset / split

- **Section & Mapping:** O. FIGURES & TABLES (Lines 758-760)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-01.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Breakdown of 670 scenario pairs, 1,340 views, 1,280 TEST views, 718 mapped, 311 ambiguous, 251 unmapped. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.TAB-02`: Table 2: Experimental conditions

- **Section & Mapping:** O. FIGURES & TABLES (Lines 761-763)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-02.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Specification of 5 conditions: No-RAG, RAG k=1, 3, 5, 10, tariffs, embeddings, prompt template. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.TAB-03`: Table 3: RQ1 metrics

- **Section & Mapping:** O. FIGURES & TABLES (Lines 764-766)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-03.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Accuracy, Macro-F1, error rate, delta vs No-RAG, bootstrap CI, McNemar p-value. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.TAB-04`: Table 4: RQ2 retrieval analysis

- **Section & Mapping:** O. FIGURES & TABLES (Lines 767-769)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-04.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Hit@k, miss rates, conditional accuracy given hit vs miss, failure overlap. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.TAB-05`: Table 5: RQ3 cost / latency

- **Section & Mapping:** O. FIGURES & TABLES (Lines 770-772)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-05.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Prompt tokens, completion tokens, latency, cost/query, total accounted cost. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.TAB-06`: Table 6: Provenance / hash / evidence

- **Section & Mapping:** O. FIGURES & TABLES (Lines 773-775)
- **Item Type:** `PUBLICATION_TABLE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Partial tables in text; machine-generated table files pending.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `docs/report/tables/o_tab-06.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending machine generation`
- **Description:** Cryptographic hashes of baseline, datasets, bundles, scripts, and runtime locks. Machine-generated from frozen bundle.
- **Closure Step:** Generate via scripts/generate_publication_tables.py.

### `O.GEN-01`: 100% Machine-Generated Figures and Tables

- **Section & Mapping:** O. FIGURES & TABLES (Lines 776-780)
- **Item Type:** `POLICY`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Generation invariant.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Every number in all 8 figures and 6 tables must be machine-generated from the frozen canonical bundle.
- **Closure Step:** Enforce via scripts/generate_publication_figures.py and tables script.

### `P.VAL-77.99`: Consistency Value: 77.99 (No-RAG accuracy percentage)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 798)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 77.99 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-79.53`: Consistency Value: 79.53 (RAG k=10 accuracy percentage)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 799)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 79.53 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-pos_1.532`: Consistency Value: +1.532 (Observed accuracy percentage point delta)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 800)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value +1.532 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-neg_2.355_pos_5.300`: Consistency Value: [-2.355, +5.300] (Pair-cluster bootstrap 95% CI pp)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 801)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value [-2.355, +5.300] must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-0.422`: Consistency Value: 0.422 (McNemar test p-value)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 802)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 0.422 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-6400`: Consistency Value: 6,400 (Total TEST matrix completed records)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 803)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 6,400 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-6401`: Consistency Value: 6,401 (Total consumed provider attempts)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 804)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 6,401 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-6387`: Consistency Value: 6,387 (Terminal VALID outcomes count)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 805)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 6,387 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-13`: Consistency Value: 13 (Terminal INCOMPLETE outcomes count)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 806)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 13 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-6.57575890`: Consistency Value: 6.57575890 (Canonical settled expenditure USD)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 807)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 6.57575890 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-6.62839900`: Consistency Value: 6.62839900 (Total accounted study expenditure USD)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 808)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 6.62839900 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-19.99000000`: Consistency Value: 19.99000000 (Total study budget ceiling USD)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 809)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 19.99000000 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-718`: Consistency Value: 718 (Mapped/scorable evaluation views cohort)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 810)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 718 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-311`: Consistency Value: 311 (Ambiguous views cohort)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 811)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 311 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-251`: Consistency Value: 251 (Unmapped views cohort)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 812)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 251 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `P.VAL-474`: Consistency Value: 474 (Frozen ATT&CK v19.2 technique benchmark universe)

- **Section & Mapping:** P. CROSS-ARTIFACT CONSISTENCY (Lines 813)
- **Item Type:** `CONSISTENCY_VALUE`
- **Owner:** Track D (Figures / Tables / Statistical QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Manually verified in v3; automated checker pending implementation.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `tests/test_cross_artifact_consistency.py`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending test implementation`
- **Description:** Value 474 must match identical across canonical bundle, README, report md/docx, slides, figures, and tables.
- **Closure Step:** Assert in tests/test_cross_artifact_consistency.py.

### `Q.01-VIETNAMESE_DECK`: Vietnamese Presentation Deck (12 Slides & 12 Speaker Notes)

- **Section & Mapping:** Q. PRESENTATION FINAL (Lines 824-830, 856-858)
- **Item Type:** `DELIVERABLE`
- **Owner:** Track E (Presentation / Reproducibility)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Inspected: all 12 slides and presenter notes are in Vietnamese with correct 18-20pt table styling.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `docs/presentation/slides.pptx`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `ba80c2a1ad2eb6a760fb169272c15812c54e464b666ad173e26453f14743fe74`
- **Description:** docs/presentation/slides.pptx is ALREADY in Vietnamese (12 slides with complete Vietnamese speaker notes). Maintain accepted terminology and formatting; do not re-translate.
- **Closure Step:** Final gap audit and preview image synchronization.

### `Q.02-TYPOGRAPHY_AND_LAYOUT_QA`: Presentation Layout, Font Sizing (>=18pt), and Overflow QA

- **Section & Mapping:** Q. PRESENTATION FINAL (Lines 846-855)
- **Item Type:** `PRESENTATION_QA`
- **Owner:** Track E (Presentation / Reproducibility)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Passed in release v3 deck audit; slide 9 table body 18pt, headers 20pt.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip::02_presentation_deck/deck_audit.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `630a91ea6b6b71f92576dd45550cfa35aa12a77fe890989f6b4f74d08a5c4e5b`
- **Description:** Zero text overflow, zero tiny text (<18pt body / 20pt headers), accessible legends, consistent units.
- **Closure Step:** Re-verify on final candidate commit.

### `R.01-CLEAN_CLONE_REPRO`: Clean-Clone Offline Reproduction Workflow

- **Section & Mapping:** R. REPRODUCIBILITY PACKAGE (Lines 863-875)
- **Item Type:** `REPRODUCIBILITY`
- **Owner:** Track E (Presentation / Reproducibility)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Tested and passed on 5754f45 in integration audit.)
- **Evidence Storage:** `git_tracked`
- **Evidence Path:** `scripts/reproduce_canonical_study.py`
- **Evidence Commit SHA:** `5754f45f4c46794bf1025bf4ee11644eb9289eb6`
- **Evidence Hash:** `bbdeae728c3ee5ba91583ff6e969019aaef7b8d1b11b5eeb2b28c89ce1577ef3`
- **Description:** Reviewer from clean clone can checkout exact SHA, uv sync --frozen, use public bundle, verify SHA, run offline replay, re-score metrics, with zero provider calls.
- **Closure Step:** Execute fresh clean-clone test on candidate final SHA.

### `R.02-REPRO_VERDICT_ASSERTION`: Replay Verdict PASS_CANONICAL_OFFLINE_VERIFIED & attempted_egress=0

- **Section & Mapping:** R. REPRODUCIBILITY PACKAGE (Lines 878-891)
- **Item Type:** `REPRODUCIBILITY`
- **Owner:** Track E (Presentation / Reproducibility)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Verified in handover package v3 guide.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `REPRODUCTION_GUIDE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `6440ad81a28a38a73fe52e25d2091fb7267fe3dca37e5aa4ecbc9b009e51bcf6`
- **Description:** Assert exit code 0, PASS_CANONICAL_OFFLINE_VERIFIED, and attempted_egress=0 without developer-specific paths.
- **Closure Step:** Re-run assertion on final candidate.

### `S.01-SECRETS_AND_PATHS_SCAN`: Comprehensive Scanner: Zero Secrets, Zero Private Paths, Zero Bytecode

- **Section & Mapping:** S. SECURITY / PRIVACY PACKAGE AUDIT (Lines 896-910)
- **Item Type:** `SECURITY_AUDIT`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Scanned release v3: 0 private paths, 0 secrets, 0 pyc.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `a12a9c6b8990ae0ffbfd4c55373e776bf3620997b564a59a5950d64abd6c85d0`
- **Description:** Scan all tracked and public artifacts for API keys, tokens, user home paths, private worktree paths, bytecode (.pyc, __pycache__).
- **Closure Step:** Re-scan candidate branch before merge.

### `T.01-PR_CLASSIFICATION_AND_ANCESTRY`: Classification and Ancestry Audit of PRs #8, #24–#29

- **Section & Mapping:** T. PR INTEGRATION (Lines 924-954)
- **Item Type:** `PR_AUDIT`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (Verified via git merge-base --is-ancestor.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/finalization_preflight.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `9587efd7e00352a1f34032ab19d523d5c1c255a206a05937c1b3a3c7fff5b24a`
- **Description:** #24-#27: ALREADY INCLUDED; #28: INTEGRATION BASE; #29: MUST INTEGRATE (terminal validator); #8: SELECTIVE (related work).
- **Closure Step:** Integrate #29 in Track A; close superseded PRs after main merge.

### `U.01-DIFF_AUDIT`: Full Diff Audit against Protected Baseline

- **Section & Mapping:** U. FINAL INTEGRATION BRANCH (Lines 969-982)
- **Item Type:** `DIFF_AUDIT`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (22/22 protected files matched in inventory.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/finalization_artifact_inventory.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Computed in inventory`
- **Description:** Assert zero accidental scientific mutation across 22 protected files, config, protocol, prompts, and canonical outputs.
- **Closure Step:** Execute final git diff audit on candidate.

### `V.01-RUFF_CHECK`: Suite 1: ruff check

- **Section & Mapping:** V. TEST MATRIX (Line 990)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Static linting across entire repository. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.02-RUFF_FORMAT`: Suite 2: ruff format --check

- **Section & Mapping:** V. TEST MATRIX (Line 992)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Code formatting check. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.03-OFFLINE_UNIT`: Suite 3: Offline unit test suite

- **Section & Mapping:** V. TEST MATRIX (Line 996)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** pytest on all unit tests. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.04-INTEGRATION_SUITE`: Suite 4: Integration test suite (no provider)

- **Section & Mapping:** V. TEST MATRIX (Line 999)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Retrieval and evaluation integration tests. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.05-SYNTHETIC_DATA`: Suite 5: Synthetic data verification

- **Section & Mapping:** V. TEST MATRIX (Line 1002)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Benchmark dataset schema and integrity tests. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.06-CANONICAL_REPLAY`: Suite 6: Canonical replay test

- **Section & Mapping:** V. TEST MATRIX (Line 1005)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Offline study reproduction verification. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.07-CANONICAL_MANIFEST`: Suite 7: Canonical manifest verification

- **Section & Mapping:** V. TEST MATRIX (Line 1008)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Manifest hash and file inventory checks. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.08-RQ_KNOWN_ANSWER`: Suite 8: RQ analysis known-answer tests

- **Section & Mapping:** V. TEST MATRIX (Line 1011)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Verify exact metric formulas against known ground truth. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.09-REPORT_METADATA`: Suite 9: Report metadata verification

- **Section & Mapping:** V. TEST MATRIX (Line 1014)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Verify slot population and hash binding. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.10-PRESENTATION_REGRESSION`: Suite 10: Presentation regression tests

- **Section & Mapping:** V. TEST MATRIX (Line 1017)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Verify slide XML and layout invariants. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.11-PATH_SECRET_SCANNER`: Suite 11: Path and secret scanner

- **Section & Mapping:** V. TEST MATRIX (Line 1020)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Automated secret and private path scan. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.12-CROSS_ARTIFACT_TEST`: Suite 12: Cross-artifact consistency test

- **Section & Mapping:** V. TEST MATRIX (Line 1023)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** Automated check of 16 headline numbers across all outputs. Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `V.13-TERMINAL_VALIDATOR`: Suite 13: Independent terminal validator suite

- **Section & Mapping:** V. TEST MATRIX (Line 1026)
- **Item Type:** `TEST_SUITE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Passed in previous base commit 5754f45; must be re-executed on final candidate.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/test_matrix_execution_log.json`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending execution`
- **Description:** PR #29 terminal audit tests (including 4 negative controls). Must record command, commit, count, duration, and exit code.
- **Closure Step:** Execute on final candidate and record in test_matrix_execution_log.json.

### `W.01-GITHUB_CI_GREEN`: All GitHub Actions CI Workflows Pass on Final SHA

- **Section & Mapping:** W. CI (Lines 1043-1060)
- **Item Type:** `CI_MONITORING`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `PARTIAL`
- **Historical Status:** `VERIFIED` (5/5 checks passed on commit 5754f45 (PR #28).)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `https://github.com/habachcp6/RAG2ATTCK/actions`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Push candidate commit, monitor CI, assert 100% green checks on final exact SHA; never claim complete with pending CI.
- **Closure Step:** Verify 5/5 green CI on final candidate PR.

### `X.01-REPO_STATE`: Repository State Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Lines 1070-1075)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** main SHA, final candidate SHA, branch, PR. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.02-CANONICAL_EXP`: Canonical Experiment Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Lines 1076-1082)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** run_id, 6400 records, 6401 attempts, status counts, cost. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.03-SCIENTIFIC_RES`: Scientific Results Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Lines 1083-1088)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** RQ1, RQ2, RQ3, statistical analysis. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.04-ARTIFACTS`: Artifacts Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Lines 1089-1096)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** report md/docx, slides, figures, canonical bundle, public manifest, guide. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.05-VERIFICATION`: Verification Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Lines 1097-1103)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** tests, CI, offline replay, zero egress, hash verification. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.06-LIMITATIONS`: Remaining Known Limitations Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Line 1104)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** Document benchmark boundaries without defensive omission. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `X.07-MERGE_RECOMMENDATION`: Merge Recommendation Section

- **Section & Mapping:** X. FINAL HUMAN REVIEW PACKAGE (Line 1106)
- **Item Type:** `FINAL_REVIEW_FIELD`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Final deliverable.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending authoring`
- **Description:** Clear merge recommendation or blocker statement. Formatted in reports/evidence/FINAL_REVIEW_PACKAGE.md.
- **Closure Step:** Author and commit FINAL_REVIEW_PACKAGE.md upon all track completions.

### `Y.01-READY_FOR_MERGE_GATE`: READY_FOR_HUMAN_FINAL_MERGE Gate

- **Section & Mapping:** Y. MERGE / FINALIZE (Lines 1114-1122)
- **Item Type:** `GOVERNANCE_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance gate.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Halt execution prior to main merge; report READY_FOR_HUMAN_FINAL_MERGE with exact PR and SHA.
- **Closure Step:** Issue notification to user/Codex.

### `Z.01-POST_MERGE_CLEANUP`: Post-Merge PR Closure and Stale Marker Cleanup

- **Section & Mapping:** Z. POST-MERGE CLEANUP (Lines 1141-1150)
- **Item Type:** `POST_MERGE_CLEANUP`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Post-merge step.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Close superseded PRs with documented reasons, clean obsolete branches, verify README links, ensure no stale 'TODO' or 'scaffold' text.
- **Closure Step:** Execute after human merge authorization.

### `AA.01-RELEASE_TAG`: Official Release Tagging v1.0.0-rag2attck-study

- **Section & Mapping:** AA. RELEASE (Lines 1156-1174)
- **Item Type:** `RELEASE`
- **Owner:** Track F (Integration / GitHub / Release QA)
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Draft release v3 assets uploaded; official tag deferred until post-merge.)
- **Evidence Storage:** `release_asset`
- **Evidence Path:** `final_handover_package_v3_20261002.zip`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `a12a9c6b8990ae0ffbfd4c55373e776bf3620997b564a59a5950d64abd6c85d0`
- **Description:** Tag release with comprehensive release notes specifying benchmark scope, final SHA, run ID, headline results, limitations, and hashes.
- **Closure Step:** Tag v1.0.0-rag2attck-study upon human authorization.

### `DOD-01`: DoD #01: canonical 6400/6400 verified

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1184)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [canonical 6400/6400 verified]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-02`: DoD #02: 6401 attempts reconciled

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1185)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [6401 attempts reconciled]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-03`: DoD #03: terminal evidence verified

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1186)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [terminal evidence verified]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-04`: DoD #04: ledger reconciled

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1187)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [ledger reconciled]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-05`: DoD #05: budget safe

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1188)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [budget safe]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-06`: DoD #06: canonical metric bundle frozen

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1189)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [canonical metric bundle frozen]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-07`: DoD #07: RQ1 verified

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1190)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [RQ1 verified]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-08`: DoD #08: RQ2 verified

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1191)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [RQ2 verified]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-09`: DoD #09: RQ3 verified

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1192)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [RQ3 verified]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-10`: DoD #10: report final

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1193)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [report final]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-11`: DoD #11: DOCX final

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1194)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [DOCX final]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-12`: DoD #12: figures final

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1195)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [figures final]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-13`: DoD #13: tables final

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1196)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [tables final]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-14`: DoD #14: slides final

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1197)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [slides final]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-15`: DoD #15: reproduction works from clean clone

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1198)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [reproduction works from clean clone]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-16`: DoD #16: zero provider calls during reproduction

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1199)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [zero provider calls during reproduction]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-17`: DoD #17: no secrets/private paths

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1200)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `PARTIAL` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [no secrets/private paths]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-18`: DoD #18: cross-artifact numbers match

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1201)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [cross-artifact numbers match]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-19`: DoD #19: all tests pass

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1202)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [all tests pass]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-20`: DoD #20: CI pass at final exact SHA

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1203)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [CI pass at final exact SHA]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-21`: DoD #21: PR integration resolved

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1204)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [PR integration resolved]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-22`: DoD #22: main contains final state

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1205)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [main contains final state]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-23`: DoD #23: superseded PRs cleaned

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1206)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [superseded PRs cleaned]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-24`: DoD #24: final evidence package committed

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1207)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [final evidence package committed]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `DOD-25`: DoD #25: release/tag completed or explicitly deferred by human

- **Section & Mapping:** AB. DEFINITION OF DONE (Line 1208)
- **Item Type:** `DOD_GATE`
- **Owner:** Antigravity Lead
- **Candidate Status:** `NOT VERIFIED`
- **Historical Status:** `NOT_APPLICABLE` (Historical status noted; candidate gate requires fresh proof.)
- **Evidence Storage:** `local_pending`
- **Evidence Path:** `reports/evidence/FINAL_REVIEW_PACKAGE.md`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `Pending final review`
- **Description:** Mandatory Definition of Done criterion: [release/tag completed or explicitly deferred by human]. Must be strictly TRUE before PROJECT FINAL claim.
- **Closure Step:** Formally audit in FINAL_REVIEW_PACKAGE.md.

### `AC.01-SELF_CORRECTION`: Systematic Diagnosis & Repair Protocol

- **Section & Mapping:** AC. SELF-CORRECTION LOOP (Lines 1216-1232)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance invariant.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Run tests -> inspect -> root-cause -> repair -> rerun. No artificial round limits; no waiving tests without cause.
- **Closure Step:** Enforced throughout execution.

### `AD.01-REVIEWER_ESCALATION`: Evidence-Backed Escalation Protocol

- **Section & Mapping:** AD. REVIEWER ESCALATION (Lines 1234-1253)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance invariant.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Prepare structured evidence package for uncertain decisions; evaluations strictly GitHub-evidence based.
- **Closure Step:** Enforced throughout execution.

### `AE.01-RESPONSE_FORMAT`: Structured Response Template Compliance

- **Section & Mapping:** AE. FINAL RESPONSE FORMAT (Lines 1255-1331)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance invariant.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Final response must strictly format output according to Section AE template.
- **Closure Step:** Enforced throughout execution.

### `AF.01-PRIORITY_ORDER`: P0 through P7 Hierarchy Enforcement

- **Section & Mapping:** AF. PRIORITY ORDER (Lines 1333-1348)
- **Item Type:** `POLICY`
- **Owner:** Antigravity Lead
- **Candidate Status:** `POLICY_ENFORCED`
- **Historical Status:** `NOT_APPLICABLE` (Governance invariant.)
- **Evidence Storage:** `not_applicable`
- **Evidence Path:** `None`
- **Evidence Commit SHA:** `None`
- **Evidence Hash:** `None`
- **Description:** Strict hierarchy: P0 Canonical integrity -> P1 Scientific correctness -> P2 Reproducibility -> P3 Cross-artifact -> P4 Report -> P5 Presentation -> P6 GitHub -> P7 Polish.
- **Closure Step:** Enforced throughout execution.

