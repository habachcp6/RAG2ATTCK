# Table 1: MITRE ATT&CK Retrieval Diagnostics (T20 Overall)

| Metric | Evaluated Depth / Value | Count / Denominator | Rate (%) |
| :--- | :--- | :--- | :--- |
| **Positive Evaluated Views** | N/A | 756 / 1,340 | 56.42% |
| **Hit@1** | k = 1 | 32 / 756 | 4.23% |
| **Hit@3** | k = 3 | 127 / 756 | 16.80% |
| **Hit@5** | k = 5 | 183 / 756 | 24.21% |
| **Hit@10** | k = 10 | 341 / 756 | 45.11% |
| **Macro Recall@1** | k = 1 | Multi-label average | 3.46% |
| **Macro Recall@3** | k = 3 | Multi-label average | 15.90% |
| **Macro Recall@5** | k = 5 | Multi-label average | 23.13% |
| **Macro Recall@10** | k = 10 | Multi-label average | 43.14% |
| **Mean GT Rank (when retrieved)** | Top-10 | 5.21 | N/A |
| **Median GT Rank (when retrieved)** | Top-10 | 5.0 | N/A |
| **Absent from Top-10 (Retrieval Failure)** | k = 10 | 415 / 756 | 54.89% |

*Note:* Evaluated independently on frozen synthetic benchmark Stage B positive views using dense `sentence-transformers/all-MiniLM-L6-v2` and FAISS `IndexFlatIP`.