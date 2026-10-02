# Table 4: RQ2 Retrieval Performance, Conditional Accuracy & Error Decomposition

| Condition | Hit Rate (Recall@k) | $P(\text{Correct} \mid \text{Retrieval Hit})$ | $P(\text{Correct} \mid \text{Retrieval Miss})$ | Errors | Misses | Overlap (Miss $\cap$ Wrong) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG (k=0)** | N/A | N/A | N/A | 158 | N/A | N/A |
| **RAG (k=1)** | 3.76% | 100.00% | 76.12% | 165 | 691 | 165 |
| **RAG (k=3)** | 16.43% | 97.46% | 74.83% | 154 | 600 | 151 |
| **RAG (k=5)** | 24.09% | 97.11% | 73.03% | 152 | 545 | 147 |
| **RAG (k=10)** | 44.71% | 91.28% | 70.03% | 147 | 397 | 119 |

*Error Decomposition (k=10, N=718): Misattributions $= 147$, Retrieval Misses $= 397$, Overlap (Miss $\cap$ Wrong) $= 119$ ($80.95\%$ of errors). Under Protocol Decision D2i, failure axes are evaluated independently without forced mutual exclusivity.*
