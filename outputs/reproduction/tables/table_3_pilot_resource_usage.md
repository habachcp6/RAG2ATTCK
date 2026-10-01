# Table 3: Real-Provider DEV Cost Pilot Empirical Resource Usage

| Condition | Records | Mean Input Tokens | Mean Output Tokens | Total Input Tokens | Total Output Tokens | Status Adherence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `no_rag` | 4 | 643.0 | 224.2 | 2,572 | 897 | 100% VALID |
| `rag_k1` | 4 | 1115.0 | 332.2 | 4,460 | 1,329 | 100% VALID |
| `rag_k10` | 4 | 4536.5 | 800.8 | 18,146 | 3,203 | 100% VALID |
| `rag_k3` | 4 | 1740.5 | 1087.2 | 6,962 | 4,349 | 100% VALID |
| `rag_k5` | 4 | 2518.2 | 840.2 | 10,073 | 3,361 | 100% VALID |

### Cost Summary & Scaling Projections
- **Empirical Pilot Cost (20 requests):** $0.024209 (conservative: $0.026320)
- **Observed Output Mean:** 656.95 tokens/request
- **Observed Latency Mean:** 8127.6 ms
- **Canonical 6,400-Request TEST Projection:** $8.20 (conservative input: $8.99)