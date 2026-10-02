# Table 3: RQ1 Technique Attribution Performance & Paired Statistical Inference

| Condition | Attribution Accuracy (%) | Macro-F1 (474 Classes) | Delta vs. No-RAG (pp) | 95% Bootstrap CI (pp) | McNemar Exact $p$ | Significant at $\alpha=0.05$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG (k=0)** | 77.99% | 0.0126 | Baseline | — | — | — |
| **RAG (k=1)** | 77.02% | 0.0127 | -0.975 pp | [-4.735, +2.925] | 0.638 | No |
| **RAG (k=3)** | 78.55% | 0.0136 | +0.557 pp | [-3.064, +4.039] | 0.803 | No |
| **RAG (k=5)** | 78.83% | 0.0139 | +0.836 pp | [-2.646, +4.457] | 0.690 | No |
| **RAG (k=10)** | 79.53% | 0.0140 | +1.532 pp | [-2.355, +5.300] | 0.422 | No |

*McNemar Test Contingency Table (k=10 vs No-RAG): Both Correct $a=488$, RAG-Win $b=83$, No-RAG-Win $c=72$, Both Incorrect $d=75$. Discordant $= 155$, $\chi^2 = 0.645161$, $p = 0.422$.*
