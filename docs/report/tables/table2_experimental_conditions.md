# Table 2: Experimental Conditions & System Configuration

> **[FIXTURE DATA ONLY — PREVIEW ARTIFACT]** This table contains synthetic fixture numbers for validation and review purposes only. Not canonical scientific evidence.

| Condition | Retrieval Depth ($k$) | Dense Retriever | Embedding Model | LLM Reasoner | Reasoning Effort | Output Format |
| :--- | :---: | :--- | :--- | :--- | :---: | :--- |
| **No-RAG** | $k=0$ | None | None | `gpt-5.6-luna` | `xhigh` | Strict JSON Schema |
| **RAG k=1** | $k=1$ | FAISS IndexFlatIP | `all-MiniLM-L6-v2` | `gpt-5.6-luna` | `xhigh` | Strict JSON Schema |
| **RAG k=3** | $k=3$ | FAISS IndexFlatIP | `all-MiniLM-L6-v2` | `gpt-5.6-luna` | `xhigh` | Strict JSON Schema |
| **RAG k=5** | $k=5$ | FAISS IndexFlatIP | `all-MiniLM-L6-v2` | `gpt-5.6-luna` | `xhigh` | Strict JSON Schema |
| **RAG k=10** | $k=10$ | FAISS IndexFlatIP | `all-MiniLM-L6-v2` | `gpt-5.6-luna` | `xhigh` | Strict JSON Schema |

*Protocol Invariants: Concurrency = Sequential-only (D4); Temperature = Provider default for reasoning; Maximum Output Tokens = 8,192; Budget Cap = $19.99 (D5).*
