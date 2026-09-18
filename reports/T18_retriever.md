# Task T18: Deterministic FAISS Retriever with Pinned Embeddings Report

## Executive Summary
- **Task ID**: T18
- **Branch**: `task/t18-faiss-retriever` (parent: `task/t17-attack-corpus` at commit `8b84677`)
- **Status**: COMPLETE / PASS
- **Target Deliverables**:
  1. Retrieval configuration: `config/retrieval.json`
  2. Retriever module: `src/retrieval/retriever.py`
  3. FAISS index artifact: `attack/index/enterprise-windows-v19.2.index` (728,109 bytes, SHA-256: `7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5`)
  4. Document mapping artifact: `attack/index/enterprise-windows-v19.2.docmap.json` (1,591,447 bytes, SHA-256: `a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586`)
  5. Index manifest artifact: `attack/index/enterprise-windows-v19.2.manifest.json` (770 bytes, SHA-256: `ad1fc8c8118ef897943597e30c3ab71cf30556f675b38bbeba6772537127ed0a`)
  6. Test suite: `tests/test_retriever.py` (14 total tests: 10 offline unit tests + 4 integration tests, 100% pass)
  7. Pytest configuration: registered `integration` marker in `pyproject.toml`
  8. Documentation report: `reports/T18_retriever.md`
- **Integrity Highlights**:
  - Pinned Hugging Face model commit revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (exact 40-character hex commit SHA).
  - FAISS `IndexFlatIP` with L2-normalized embeddings guarantees mathematically exact, zero-distortion cosine similarity.
  - Deterministic tie-breaking via FAISS full-corpus search (`ntotal`) and secondary sort `(-score, technique_id)` guarantees 100% reproducibility and strict prefix consistency across $k \in \{1, 3, 5, 10\}$.
  - 100% byte-for-byte reproducibility across independent builds.
  - Zero evaluation metadata / labels (`ground_truth`, `technique_label`, `expected_technique`, `attack_label`, etc.) leaked into retrieved context.
  - Clean separation between offline tests (stub embedder, no network) and integration tests (live model weights).

---

## 1. Technical Specification & Parameters

| Parameter | Value | Description / Constraint |
| :--- | :--- | :--- |
| **Embedding Model ID** | `sentence-transformers/all-MiniLM-L6-v2` | Frozen dense sentence embedding model |
| **Model Revision** | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` | Pinned immutable 40-character hex commit SHA on Hugging Face Hub |
| **Embedding Dimension** | `384` | Dense vector dimensionality |
| **Normalization** | `L2` | Unit norm ($\|v\|_2 = 1.0$) applied to documents and queries |
| **Similarity Metric** | `cosine` | Inner product on L2-normalized vectors: $\langle \hat{u}, \hat{v} \rangle = \cos(u, v)$ |
| **FAISS Index Type** | `IndexFlatIP` | Exact brute-force inner product search over dense float32 vectors |
| **FAISS Version** | `1.15.1` | Installed CPU build (`faiss-cpu==1.15.1`) |
| **Input Corpus File** | `attack/corpus/enterprise-windows-v19.2.jsonl` | Active Windows ATT&CK v19.2 corpus |
| **Input Corpus SHA-256** | `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75` | Verified immutable input digest |
| **Document Count** | `474` | Exact count of active Windows techniques and subtechniques |
| **Supported Depths ($k$)** | `[1, 3, 5, 10]` | Retrieval depths evaluated in benchmark experiments |
| **Default Depth ($k$)** | `5` | Standard default retrieval depth |

---

## 2. Python 3.13 and Dependency Resolution Audit

- **Python Runtime**: Python 3.13.0 (`cpython-3.13.0-windows-x86_64-none`)
- **Package Manager**: `uv`
- **Installed Packages**:
  - `faiss-cpu==1.15.1` (pre-compiled binary wheel `faiss_cpu-1.15.1-cp313-cp313-win_amd64.whl`)
  - `sentence-transformers==6.0.1` (`sentence_transformers-6.0.1-py3-none-any.whl`)
  - `torch==2.14.0` (`torch-2.14.0-cp313-cp313-win_amd64.whl`)
  - `transformers==5.17.0`
  - `tokenizers==0.23.2`
  - `numpy==2.5.3`
- **C++ Compiler Dependency**: None. All wheels are official pre-built binary wheels for Windows x86_64 and CPython 3.13. No MSVC or C++ compiler required.

---

## 3. Mathematical Framework & Deterministic Tie-Breaking

### 3.1 Cosine Similarity via L2 Normalization and IndexFlatIP
1. For query vector $q \in \mathbb{R}^d$ and document vector $d_i \in \mathbb{R}^d$, L2 normalization yields:
   $$\hat{q} = \frac{q}{\|q\|_2}, \quad \hat{d}_i = \frac{d_i}{\|d_i\|_2}$$
2. FAISS `IndexFlatIP` computes the exact inner product:
   $$\text{IP}(\hat{q}, \hat{d}_i) = \sum_{j=1}^d \hat{q}_j \hat{d}_{i, j} = \frac{q \cdot d_i}{\|q\|_2 \|d_i\|_2} = \text{sim}_{\cos}(q, d_i)$$
3. With $N = 474$ documents and $d = 384$, memory consumption is $\approx 728 \text{ KB}$ and search latency is $<0.1 \text{ ms}$, ensuring exact zero-distortion brute-force search.

### 3.2 Deterministic Global Tie-Breaking
When candidate scores are tied (or indistinguishable at float32 boundary):
1. The retriever queries FAISS across all $N_{\text{total}} = 474$ candidates:
   ```python
   distances, indices = self.index.search(norm_query_vec, ntotal)
   ```
2. Candidates are mapped to tuples: `(float(score), technique_id: str, doc: dict)`.
3. A stable Python sort is applied with compound key:
   ```python
   candidates.sort(key=lambda item: (-item[0], item[1]))
   ```
   - Primary sort: `-item[0]` (descending similarity score; highest score first).
   - Secondary sort: `item[1]` (ascending ATT&CK `technique_id`; deterministic lexicographical order).
4. Top $k$ is obtained via slicing `candidates[:k]`.

### 3.3 Prefix Consistency Invariant
Because sorting is applied globally before slicing, for any $k_1 < k_2 \in \{1, 3, 5, 10\}$:
$$\text{results}(k_1) \equiv \text{results}(k_2)[:k_1]$$
This invariant is tested and proven across all supported $k$ depths in both offline unit tests and live integration tests.

---

## 4. Artifact Inventory & Integrity Checksums

| Artifact File | Size (bytes) | SHA-256 Digest | Purpose / Description |
| :--- | :--- | :--- | :--- |
| `config/retrieval.json` | 920 | `e5d263bba5b3a43697950c4bc1532f83fe1a2f64704e6727289ee0f55cf4a953` | Canonical retrieval config with pinned revision |
| `attack/index/enterprise-windows-v19.2.index` | 728,109 | `7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5` | Serialized binary FAISS IndexFlatIP (474 vectors) |
| `attack/index/enterprise-windows-v19.2.docmap.json` | 1,591,447 | `a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586` | Ordered mapping of vector indices to ATT&CK document metadata |
| `attack/index/enterprise-windows-v19.2.manifest.json` | 770 | `ad1fc8c8118ef897943597e30c3ab71cf30556f675b38bbeba6772537127ed0a` | Integrity manifest with SHA-256 digests and provenance |

### Deterministic Rebuild Verification
An independent clean rebuild in temporary storage verified:
- Rebuilt Index SHA-256: `7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5` (100% byte-identical)
- Rebuilt Docmap SHA-256: `a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586` (100% byte-identical)

---

## 5. Verification & Test Results

### 5.1 Test Suite Structure
The test suite in `tests/test_retriever.py` enforces strict operational separation:
- `TestFAISSRetrieverOffline`: 10 unit tests requiring 0 internet, using `StubEmbedder` or synthetic test vectors.
- `TestFAISSRetrieverIntegration`: 4 integration tests marked with `@pytest.mark.integration`, validating real model loading, index integrity, concept attribution, and prefix consistency.

### 5.2 Offline Test Results (`uv run pytest -m "not integration" -v`)
```
tests/test_retriever.py::TestFAISSRetrieverOffline::test_config_structure_and_revision_pinning PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_stub_embedder_determinism PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_l2_normalization_unit_length PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_index_flat_ip_cosine_equivalence PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_deterministic_secondary_sort_tie_breaking PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_prefix_consistency_across_k PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_k_bounds_and_validation PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_serialization_and_manifest_roundtrip PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_manifest_tamper_rejection PASSED
tests/test_retriever.py::TestFAISSRetrieverOffline::test_format_retrieved_context_no_leakage PASSED

===================== 217 passed, 4 deselected in 21.19s ======================
```

### 5.3 Integration Test Results (`uv run pytest -m integration -v`)
```
tests/test_retriever.py::TestFAISSRetrieverIntegration::test_real_sentence_transformer_loads_pinned_revision PASSED
tests/test_retriever.py::TestFAISSRetrieverIntegration::test_real_index_loading_and_manifest_verification PASSED
tests/test_retriever.py::TestFAISSRetrieverIntegration::test_real_index_attribution_queries PASSED
tests/test_retriever.py::TestFAISSRetrieverIntegration::test_supported_k_depths_on_real_index PASSED

===================== 4 passed, 217 deselected in 21.44s ======================
```

### 5.4 ATT&CK Concept Retrieval Smoke Validation

| Concept / Query | Expected Class | Top Retrieved Candidates | Similarity Score | Verification |
| :--- | :--- | :--- | :--- | :--- |
| `powershell.exe -ExecutionPolicy Bypass -enc SQBFAFgA` | `T1059.001` (PowerShell) | `[T1059.001] PowerShell` (Rank 1)<br>`[T1546.013] PowerShell Profile` (Rank 2) | 0.4967 | PASS (Rank 1) |
| `schtasks.exe /create /tn MyTask /tr C:\evil.exe /sc onlogon` | `T1053.005` (Scheduled Task) | `[T1053.005] Scheduled Task` (Rank 1)<br>`[T1053.002] At` (Rank 2) | 0.4582 | PASS (Rank 1) |
| `net user /add create a local user account` | `T1136.001` (Local Account) | `[T1136.001] Local Account` (Rank 1)<br>`[T1098.007] Additional Local/Domain Groups` (Rank 2) | 0.5172 | PASS (Rank 1) |
| `download tool from remote server ingress tool transfer certutil` | `T1105` (Ingress Tool Transfer) | `[T1105] Ingress Tool Transfer` (Rank 1)<br>`[T1570] Lateral Tool Transfer` (Rank 2) | 0.4722 | PASS (Rank 1) |

### 5.5 Full Regression Results (`uv run pytest -v`)
```
============================ 221 passed in 40.87s =============================
```
- Total test files: 16
- Total collected items: 221
- Total passed: 221 (100%)
- Total failed: 0
- Total skipped/xfailed: 0

---

## 6. Readiness for Task T19 (RAG Pipeline Integration)

1. **Deterministic Index**: Pre-built index and document mapping are serialized and verified in `attack/index/`.
2. **Provenance Key**: Manifest exposes `index_sha256: 7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5` for inclusion in `RetrievalMetadata`.
3. **Retrieval API**: `FAISSRetriever.from_saved()` and `retriever.retrieve(evidence, k=k)` provide simple, zero-drift interfaces for T19.
4. **Context Formatting**: `retriever.format_retrieved_context(results)` formats candidates cleanly without any evaluation label leakage.
