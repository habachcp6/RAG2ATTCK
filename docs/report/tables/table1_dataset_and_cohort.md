# Table 1: Dataset Partition & Benchmark Cohort Specifications

> **[FIXTURE DATA ONLY — PREVIEW ARTIFACT]** This table contains synthetic fixture numbers for validation and review purposes only. Not canonical scientific evidence.

| Metric / Attribute | Count / Value | Proportion of Cohort | Description & Governance Role |
| :--- | :---: | :---: | :--- |
| **Total Physical Query Views** | 1,280 | 100.00% | 640 Paired Tests (Single-Event + Contextual-Event) |
| **Total Query Pairs (pair_id)** | 640 | — | Paired cluster resampling unit for bootstrap CI |
| **Scorable Mapped Positive Views** | 718 | 56.09% | **Primary Benchmark Denominator (N=718)** |
| ├── *Single-GT Technique Views* | 678 | 94.43% of Mapped | Mapped views with exactly one ground truth ID |
| └── *Multi-GT Technique Views* | 40 | 5.57% of Mapped | Mapped views evaluated under ANY_MATCH (D2a) |
| **Ambiguous Ground Truth Views** | 311 | 24.30% | Excluded from accuracy attribution per D2c |
| **Unmapped Ground Truth Views** | 251 | 19.61% | Excluded from accuracy attribution per D2b |
| **ATT&CK Macro-F1 Universe** | 474 | — | Frozen Benchmark Universe (D2d) |
| ├── *Supported Active Classes* | 8 | 1.69% | Classes with test set support instances (768 total) |
| └── *Zero-Support Macro Classes* | 466 | 98.31% | Unrepresented classes contributing 0 to macro-F1 |

*Note: Ambiguous and unmapped views incurred real LLM inference costs and are fully tracked in the financial ledger.*
