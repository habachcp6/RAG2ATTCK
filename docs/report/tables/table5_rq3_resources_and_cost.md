# Table 5: RQ3 Operational Resources, Token Consumption & Financial Accounting

> **[FIXTURE DATA ONLY — PREVIEW ARTIFACT]** This table contains synthetic fixture numbers for validation and review purposes only. Not canonical scientific evidence.

| Condition | Mean Latency (ms) | Median Latency (ms) | Prompt Tokens | Completion Tokens | Cached Tokens | Settled Cost ($ USD) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG (k=0)** | 2,904.5 | 2,302.8 | 863,139 | 209,466 | 0 | $0.46714395 |
| **RAG (k=1)** | 3,514.3 | 2,617.1 | 1,595,554 | 299,128 | 1,540 | $1.29723350 |
| **RAG (k=3)** | 4,215.9 | 2,743.2 | 2,780,640 | 403,100 | 0 | $1.17888000 |
| **RAG (k=5)** | 4,327.3 | 2,873.7 | 3,917,047 | 419,880 | 0 | $1.48311775 |
| **RAG (k=10)** | 4,370.7 | 2,667.0 | 6,546,274 | 427,346 | 0 | $2.14938370 |

### Whole-Study Budget Reconciliation (Decision D5)
- **Total Study Budget Cap:** $19.99000000
- **Prior Pilot Provisional Hold:** $0.05264010
- **Cumulative Settled Expenditure:** $6.57575890
- **Total Accounted Expenditure:** $6.62839900
- **Uncommitted Available Balance:** $13.36160100
- **Active Reservations / Breaches:** $0.00 / 0 breaches

*Notes: All resource metrics are measured across the full execution cohort (N=1,280 requests per condition). P95 Latency is NOT REPORTED pending authority approval. RAG k=1 settled cost includes $0.5397 missing-usage penalty from an initial network failure attempt (ordinal 5387) successfully retried on ordinal 5388.*
