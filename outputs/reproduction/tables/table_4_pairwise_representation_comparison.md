# Table 4: Single-Event vs Contextual-Event Telemetry Pairwise Comparison

## Cohort A: Canonical Anchor Comparison (Primary)
- **Eligibility Criterion:** Single-event view contains exactly one ground-truth technique that also appears in the contextual view.

| Outcome Category | Pair Count | Proportion of Eligible (%) | Description |
| :--- | :---: | :---: | :--- |
| **Single Better** | 65 | 21.96% | Single-event view achieved strictly better retrieval rank |
| **Contextual Better** | 23 | 7.77% | Contextual view achieved strictly better retrieval rank |
| **Equal Rank** | 208 | 70.27% | Both views achieved identical rank (or both missed Top-10) |
| *— Both Absent Top-10* | 147 | 49.66% | Neither representation retrieved technique in Top-10 |
| *— Identical Top-10 Rank* | 61 | 20.61% | Both representations retrieved technique at the exact same rank |
| **Total Eligible Pairs** | 296 | 100.0% | Analyzed scenario pairs |
| **Excluded Pairs** | 374 | N/A | Multi-label single view or missing contextual anchor |

## Cohort B: Strict Single-Technique Comparison (Secondary)
- **Eligibility Criterion:** Both single-event and contextual views contain exactly one identical technique.

| Outcome Category | Pair Count | Proportion of Eligible (%) |
| :--- | :---: | :---: |
| **Single Better** | 59 | 23.41% |
| **Contextual Better** | 23 | 9.13% |
| **Equal Rank** | 170 | 67.46% |
| **Total Eligible Pairs** | 252 | 100.0% |

*Scientific Note:* These empirical counts represent observed rank differences under dense semantic search (`all-MiniLM-L6-v2`) on `synthetic-paired-v1`.