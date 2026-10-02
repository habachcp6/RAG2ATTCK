# [FIXTURE PREVIEW] Presentation Deck Numeric Slots Preview

> [!WARNING] DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS
> This preview is automatically compiled from synthetic diagnostic unit test fixtures.
> It does NOT represent canonical empirical research outcomes or live study findings.
> Execution mode: `mock_fixture` | `fixture_only: true`.

## 1. Metadata & Safety Invariants
- **Provenance Status**: `diagnostic_fixture`
- **Disclaimer**: `DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS`
- **Total Placeholders Extracted**: 68
- **Declarative Shape-Table Slots**: 67

## 2. Populated Slot Values (by Presentation Slide)

### Slide 4: Dataset & Views Topology
- Manifest Path: `data/ground_truth/synthetic/split_manifest.json`
- Total TEST Views: `1,280`
- Scorable Views: `718`
- Complete Scorable Pairs: `278`
- Contextual-Only Pairs: `162`
- Neither Mapped Pairs: `200`
- Distinct Eligible Clusters: `440`

### Slide 6: RQ2 Retrieval Diagnostics
- Hit@10: `0.8333`
- Recall@10: `0.8333`
- Retrieval Miss Rate: `0.1667`

### Slide 7: RQ1 Attribution Performance & Pairwise Cohorts
- Marginal Single Acc: `0.5000`
- Marginal Context Acc: `0.5000`
- Paired Single Acc: `0.5000`
- Paired Context Acc: `0.5000`
- Paired Delta: `+0.00` pp
### Slide 8: RQ1 5 Conditions & RQ2 Error Decomposition
- Accuracy (No-RAG): `0.5000`
- Accuracy (RAG k=1): `0.5200` (ΔAcc: `+0.0200`, ΔF1: `+0.0071`)
- Accuracy (RAG k=3): `0.5500` (ΔAcc: `+0.0500`, ΔF1: `+0.0271`)
- Accuracy (RAG k=5): `0.5800` (ΔAcc: `+0.0800`, ΔF1: `+0.0471`)
- Accuracy (RAG k=10): `0.6000` (ΔAcc: `+0.1000`, ΔF1: `+0.0671`)
- Macro-F1 (No-RAG): `0.0929`
- Macro-F1 (RAG k=10): `0.1600`
- Best Condition: `rag_k10` (Delta Acc: `+0.1000`, Delta F1: `+0.0671`)
- Provider Failure Rate: `0.0000`
- Parse Failure Rate: `0.0000`
- Invalid ID Rate: `0.1667`
- Wrong Classification Rate: `0.3333`
- Overlap Miss & Wrong: `0`
- P(Correct | Retrieved): `0.6000`
- P(Correct | Absent): `0.0000`

### Slide 9: RQ3 Resource Tradeoffs & Costs
- Median Latency (No-RAG vs k=10): `7.89` s vs `9.90` s
- Mean Prompt Tokens (No-RAG vs k=10): `643.0` vs `4536.5`
- Cost per Logical Request (No-RAG vs k=10): `$0.000390` vs `$0.001870`
- Whole Study Accounting: Budget `$19.99` | Spend `$8.50` | Remaining `$11.44`

---
*End of Private Diagnostic Fixture Preview - `DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS`*