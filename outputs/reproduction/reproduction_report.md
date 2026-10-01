# RAG2ATTCK - Independent Study Reproduction Report
- Execution Mode: STRICTLY OFFLINE (Zero API Calls, Zero Secrets)
- Verification Timestamp (UTC): `2026-10-01T22:01:38Z`
- Target Worktree: `D:\RAG2ATTCK-worktrees\repro-presentation-s1`
- Scientific Provenance Tiers Audited:
  1. Canonical Locked Artifacts (15 bound artifacts)
  2. Evaluator Fixture Diagnostics (offline mathematical correctness)
  3. DEV Cost Pilot Evidence (20 samples, $0.0242 USD)
  4. T20 Retrieval Diagnostics (756 positive views, 296 anchor pairs)
  5. Canonical TEST Study (1,280 samples x 5 conditions = 6,400 records; status check)

=======================================================
  STAGE 1: CRYPTOGRAPHIC HASH & ARTIFACT INTEGRITY AUDIT
=======================================================
[INFO] Canonical Lock: canonical-lock-v1
[INFO] Protocol Version: experiment-protocol-v1.1
[INFO] Bound Artifact Count: 15

[INFO] Verifying 15 bound canonical artifacts:
  [OK] attack_registry      dc1639caa5501d72... (  52573.9 KB)
  [OK] corpus               b219341154ddf2f1... (   1512.4 KB)
  [OK] dataset_manifest     4576b793360d02b6... (      2.4 KB)
  [OK] document_mapping     a7de3dfcf2b6e186... (   1554.1 KB)
  [OK] experiment_config    961ba9b3e9e1b459... (      3.7 KB)
  [OK] ground_truth         8f3d73bac7e81336... (    716.7 KB)
  [OK] index                7e3b994487086076... (    711.0 KB)
  [OK] inference            90d5f59e64f669f9... (   1157.6 KB)
  [OK] model_config         312c34cedd84106f... (      0.9 KB)
  [OK] pairs                079e57a441b18d12... (   2169.4 KB)
  [OK] prompt               b751fde1ee33b03e... (      1.3 KB)
  [OK] retrieval_config     b33a93913e7f6de3... (      0.9 KB)
  [OK] retrieval_manifest   ad1fc8c8118ef897... (      0.8 KB)
  [OK] split_manifest       37fce63ccaa6db8e... (     10.5 KB)
  [OK] views                1e6b0d3bd525b8fe... (    149.9 KB)

[INFO] Verifying Frozen Scientific Protocol v1.1 Decisions:
  [OK] Protocol decisions SHA-256 verified: d3bf3d31ad307100...

[INFO] Verifying Critical Code Manifest SHA-256:
  [OK] Execution critical code SHA-256 verified: 8b1b3ea4d11a8e3c...

[INFO] Verifying Real-Provider DEV Cost Pilot Evidence Bundle (dev_cost_pilot_20261001):
  [OK] dev_experiment_config.json     9061673f61d79cf6... (VALID)
  [OK] dev_protocol_v1.json           fe39e403fdbf9b2c... (VALID)
  [OK] manifest.json                  2ae55058c6fcb2d7... (VALID)
  [OK] no_rag_predictions.jsonl       99fbf3b1aaaf40e1... (VALID)
  [OK] rag_k10_predictions.jsonl      db43b0b8bc42c8e0... (VALID)
  [OK] rag_k1_predictions.jsonl       dc8ae9208bea77cd... (VALID)
  [OK] rag_k3_predictions.jsonl       801538052bf50a60... (VALID)
  [OK] rag_k5_predictions.jsonl       2535542c9ce74dee... (VALID)
  [OK] request_journal.jsonl          1f00e3f34fb78aec... (VALID)
  [OK] summary.json                   f8dfe99479346dbb... (VALID)

[INFO] Runtime Provenance & License Disclosures:
  - Active Launcher SHA-256: 05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa
  - Windows Atomic Rename Wrapper: 12 retries for WinError 5/32 on StudyBudgetLedger
  - License Status: README declares MIT License (standalone LICENSE file absent in tree)

=======================================================
  STAGE 2: INDEPENDENT T20 RETRIEVAL DIAGNOSTICS
=======================================================
[INFO] Diagnostic Rows: 1340 (Total benchmark views: 1,340)
[RESULT] Positive Views Evaluated: 756 / 1,340
  Hit@1:   0.0423 (32/756)
  Hit@3:   0.1680 (127/756)
  Hit@5:   0.2421 (183/756)
  Hit@10:  0.4511 (341/756)
  Macro Recall@1:  0.0346
  Macro Recall@3:  0.1590
  Macro Recall@5:  0.2313
  Macro Recall@10: 0.4314
  Mean GT Rank when Retrieved:   5.21
  Median GT Rank when Retrieved: 5.0
  Ground-Truth Absent from Top-10: 415/756 (54.89%)

[INFO] Canonical Anchor Pairwise Comparison (670 candidate pairs):
  Eligible anchor pairs:                  296
  Excluded pairs (multi-label/mismatch):  374
  Single-event representation better:     65 (22.0%)
  Contextual-event representation better: 23 (7.8%)
  Equal retrieval performance:            208 (70.3%)
    - Both absent from Top-10:            147
    - Identical rank in Top-10:           61

[INFO] Secondary Strict Single-Technique Cohort (both views single-label):
  Eligible pairs:                         252
  Single-event better:                    59
  Contextual-event better:                23
  Equal retrieval performance:            170

=======================================================
  STAGE 3A: EVALUATOR FIXTURE DIAGNOSTICS (TEST FIXTURES)
=======================================================
[INFO] Executing evaluate_experiment on unit test fixtures (Mathematical Verification Only)...
  [OK] Exported _fixture_metadata.json (fixture_only=True)
  [OK] Exported overall_metrics.json               (1867 bytes)
  [OK] Exported per_condition_metrics.json         (4199 bytes)
  [OK] Exported per_technique_metrics.json         (6365 bytes)
  [OK] Exported retrieval_conditional_metrics.json (1420 bytes)
  [OK] Exported failure_decomposition.json         (2545 bytes)
  [OK] Exported run_provenance.json                (2180 bytes)
  [DIAGNOSTIC] Fixture Overall Accuracy: 0.5
  [DIAGNOSTIC] Fixture Completed Records: 35

[INFO] Auditing real-provider DEV cost pilot evidence bundle (dev_cost_pilot_20261001)...
  [AUDIT] Run ID:                  live-dc6b3166114d401e
  [AUDIT] Total Attempts:          20 (retries: 0)
  [AUDIT] Valid Records:           20 / 20 (100% VALID)
  [AUDIT] Total Input Tokens:      42,213
  [AUDIT] Total Output Tokens:     13,139
  [AUDIT] Mean Latency:            8127.6 ms
  [AUDIT] Empirical Spend USD:     $0.024209
  [AUDIT] Conservative Spend USD:  $0.026320
  [INFO] Pilot Condition Token Scaling:
    - no_rag  : input=2572  output=897   (records=4)
    - rag_k1  : input=4460  output=1329  (records=4)
    - rag_k10 : input=18146 output=3203  (records=4)
    - rag_k3  : input=6962  output=4349  (records=4)
    - rag_k5  : input=10073 output=3361  (records=4)

=======================================================
  STAGE 4: PUBLICATION FIGURES GENERATION
=======================================================
  [OK] Generated fig_rq2_retrieval_hit_rates.png
  [OK] Generated fig_rq2_per_technique_breakdown.png
  [OK] Generated fig_rq3_pilot_token_scaling.png

=======================================================
  STAGE 5: SUMMARY TABLES GENERATION
=======================================================
  [OK] Generated table_1_retrieval_diagnostics.md
  [OK] Generated table_2_per_technique_retrieval.md
  [OK] Generated table_3_dev_pilot_resource_usage.md
  [OK] Generated table_4_pairwise_representation_comparison.md

=======================================================
  REPRODUCTION PIPELINE SUMMARY: COMPLETE PASS
=======================================================
All audited artifacts, diagnostics, evaluator contracts, tables, and figures
have been verified and written to `D:\RAG2ATTCK-worktrees\repro-presentation-s1\outputs\reproduction`.