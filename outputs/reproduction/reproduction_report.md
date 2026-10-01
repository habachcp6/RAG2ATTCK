# RAG2ATTCK - Independent Study Reproduction Report
- Execution Timestamp: 2026-10-02 (Local System)
- Target Worktree: `D:\RAG2ATTCK-worktrees\repro-presentation-s1`
- Execution Mode: STRICTLY OFFLINE (Zero API Calls, Zero Secrets)

=======================================================
  STAGE 1: CRYPTOGRAPHIC HASH & ARTIFACT INTEGRITY AUDIT
=======================================================
[INFO] Canonical Lock: canonical-lock-v1
[INFO] Protocol Version: experiment-protocol-v1.1
[INFO] Bound Artifact Count: 15
  [OK] attack_registry    -> attack/raw/enterprise-v19.2/enterprise-attack-19.2.json (SHA-256 match)
  [OK] corpus             -> attack/corpus/enterprise-windows-v19.2.jsonl (SHA-256 match)
  [OK] dataset_manifest   -> data/ground_truth/synthetic/dataset_manifest.json (SHA-256 match)
  [OK] document_mapping   -> attack/index/enterprise-windows-v19.2.docmap.json (SHA-256 match)
  [OK] experiment_config  -> config/experiment_config.json (SHA-256 match)
  [OK] ground_truth       -> data/ground_truth/synthetic/ground_truth.jsonl (SHA-256 match)
  [OK] index              -> attack/index/enterprise-windows-v19.2.index (SHA-256 match)
  [OK] inference          -> data/ground_truth/synthetic/inference.jsonl (SHA-256 match)
  [OK] model_config       -> config/model.json (SHA-256 match)
  [OK] pairs              -> data/ground_truth/synthetic/pairs.jsonl (SHA-256 match)
  [OK] prompt             -> prompts/baseline_v1.txt (SHA-256 match)
  [OK] retrieval_config   -> config/retrieval.json (SHA-256 match)
  [OK] retrieval_manifest -> attack/index/enterprise-windows-v19.2.manifest.json (SHA-256 match)
  [OK] split_manifest     -> data/ground_truth/synthetic/split_manifest.json (SHA-256 match)
  [OK] views              -> data/ground_truth/synthetic/views.jsonl (SHA-256 match)
  [OK] Protocol v1.1 Decision Hash: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c (MATCH)
  [OK] Critical Code Manifest Hash: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4 (MATCH)

[INFO] DEV Cost Pilot Evidence Checksums (10 files):
  [OK] pilot/dev_experiment_config.json   (SHA-256 match)
  [OK] pilot/dev_protocol_v1.json         (SHA-256 match)
  [OK] pilot/manifest.json                (SHA-256 match)
  [OK] pilot/no_rag_predictions.jsonl     (SHA-256 match)
  [OK] pilot/rag_k10_predictions.jsonl    (SHA-256 match)
  [OK] pilot/rag_k1_predictions.jsonl     (SHA-256 match)
  [OK] pilot/rag_k3_predictions.jsonl     (SHA-256 match)
  [OK] pilot/rag_k5_predictions.jsonl     (SHA-256 match)
  [OK] pilot/request_journal.jsonl        (SHA-256 match)
  [OK] pilot/run_summary.json             (SHA-256 match)

[STATUS] Stage 1 Result: ALL HASHES VERIFIED

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

[INFO] Pairwise Single vs Contextual Telemetry Comparison (670 pairs):
  Eligible single-technique pairs: 252
  Single-event representation better:      59
  Contextual-event representation better:  23
  Equal retrieval performance:             170
  Both absent from Top-10:                 119

=======================================================
  STAGE 3: CANONICAL EVALUATOR EXECUTION & PILOT AUDIT
=======================================================
[INFO] Executing evaluate_experiment under Protocol v1.1 on test fixtures...
  [OK] Exported overall_metrics.json               (1867 bytes)
  [OK] Exported per_condition_metrics.json         (4199 bytes)
  [OK] Exported per_technique_metrics.json         (6365 bytes)
  [OK] Exported retrieval_conditional_metrics.json (1420 bytes)
  [OK] Exported failure_decomposition.json         (2545 bytes)
  [OK] Exported run_provenance.json                (2180 bytes)
  [METRIC] Fixture Overall Accuracy: 0.5
  [METRIC] Fixture Completed Records: 35

[INFO] Auditing real-provider DEV cost pilot evidence bundle (D:\RAG2ATTCK-worktrees\repro-presentation-s1\reports\evidence\dev_cost_pilot_20261001)...
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
  [OK] Generated table_3_pilot_resource_usage.md

=======================================================
  REPRODUCTION PIPELINE SUMMARY: COMPLETE PASS
=======================================================
All artifacts, diagnostics, evaluator contracts, tables, and figures
have been verified and written to `D:\RAG2ATTCK-worktrees\repro-presentation-s1\outputs\reproduction`.