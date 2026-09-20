# T20 — Retrieval Diagnostics

## Scope

T20 evaluates the retriever independently from the LLM. It asks whether a
valid ground-truth ATT&CK technique appears in the retriever's Top-k candidates
when the query contains only `endpoint_evidence`.

- Frozen benchmark: 670 scenario pairs, 1,340 views.
- Split: 1,280 TEST views and 60 DEV views.
- Positive retrieval denominator: 756 mapped views (712 mapped-single and 44
  mapped-multi). Ambiguous/unmapped views are excluded from retrieval metrics.
- Negative/undefined-label views: 584. They are reported separately and do
  not receive a forced Hit@k or Recall@k value.
- No LLM or Responses API call was made.

## Input and isolation contract

Authoritative inputs:

- `data/ground_truth/synthetic/inference.jsonl`
- `data/ground_truth/synthetic/ground_truth.jsonl`
- `data/ground_truth/synthetic/views.jsonl`
- `data/ground_truth/synthetic/pairs.jsonl`
- `data/ground_truth/synthetic/split_manifest.json`

The implementation validates duplicate IDs, missing evidence, missing joins,
malformed ATT&CK IDs, an exact TEST/DEV split partition and corpus membership
before retrieval.
It joins labels after loading the model input. The only argument passed to
`FAISSRetriever.retrieve()` is the input row's `endpoint_evidence`.

For a mapped-multi view, query-level `Hit@k` means that at least one valid
ground-truth technique is present in Top-k. Multi-label `Recall@k` is the
fraction of that view's ground-truth techniques present in Top-k; the report
aggregates it as macro recall across positive views. Per-technique results use
the rank of that specific technique, not the best rank of any label. For
ambiguous and unmapped views, the rank and metric fields are `null`.

## Frozen retrieval configuration and provenance

| Setting | Value |
|---|---|
| Corpus | `attack/corpus/enterprise-windows-v19.2.jsonl` |
| Corpus SHA-256 | `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75` |
| Corpus documents | 474 |
| Index | FAISS `IndexFlatIP` |
| Index SHA-256 | `7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5` |
| Document mapping SHA-256 | `a7de3dfcf2b6e186e639d2922fcbc27766c160ae58bbafea74b5efc0faf30586` |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` |
| Embedding revision | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` |
| Dimension / normalization | 384 / L2 |
| Similarity | cosine via inner product |
| Evaluated k | 1, 3, 5, 10 |

## Overall query-level retrieval hit results

| Metric | Value |
|---|---:|
| Positive views | 756 |
| Hit@1 | 0.0423 |
| Hit@3 | 0.1680 |
| Hit@5 | 0.2421 |
| Hit@10 | 0.4511 |
| Mean GT rank when retrieved | 5.2053 |
| Median GT rank when retrieved | 5 |
| GT absent from Top-10 | 415 / 756 |
| GT absent from Top-10 rate | 0.5489 |

## Overall multi-label recall

| Metric | Value |
|---|---:|
| Macro Recall@1 | 0.0346 |
| Macro Recall@3 | 0.1590 |
| Macro Recall@5 | 0.2313 |
| Macro Recall@10 | 0.4314 |

## Split and view breakdown

| Group | Positive views | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Median rank | GT absent Top-10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| TEST | 718 | 0.0376 | 0.1643 | 0.2409 | 0.4471 | 5 | 397 |
| DEV | 38 | 0.1316 | 0.2368 | 0.2632 | 0.5263 | 5 | 18 |
| single-event | 296 | 0.0541 | 0.1486 | 0.2196 | 0.4628 | 6 | 159 |
| contextual-event | 460 | 0.0348 | 0.1804 | 0.2565 | 0.4435 | 4 | 256 |

| Group | Macro Recall@1 | Macro Recall@3 | Macro Recall@5 | Macro Recall@10 |
|---|---:|---:|---:|---:|
| TEST | 0.0295 | 0.1548 | 0.2296 | 0.4280 |
| DEV | 0.1316 | 0.2368 | 0.2632 | 0.4956 |
| single-event | 0.0541 | 0.1486 | 0.2196 | 0.4628 |
| contextual-event | 0.0221 | 0.1656 | 0.2388 | 0.4112 |

## Label-category breakdown

| Category | Positive views | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Median rank | GT absent Top-10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| mapped-single | 712 | 0.0323 | 0.1601 | 0.2331 | 0.4340 | 5 | 403 |
| mapped-multi | 44 | 0.2045 | 0.2955 | 0.3864 | 0.7273 | 5 | 12 |
| ambiguous | 0 | n.a. | n.a. | n.a. | n.a. | n.a. | n.a. |
| unmapped | 0 | n.a. | n.a. | n.a. | n.a. | n.a. | n.a. |

| Category | Macro Recall@1 | Macro Recall@3 | Macro Recall@5 | Macro Recall@10 |
|---|---:|---:|---:|---:|
| mapped-single | 0.0323 | 0.1601 | 0.2331 | 0.4340 |
| mapped-multi | 0.0720 | 0.1402 | 0.2008 | 0.3902 |
| ambiguous | n.a. | n.a. | n.a. | n.a. |
| unmapped | n.a. | n.a. | n.a. | n.a. |

## Per-technique results

These are specific-technique retrieval hit rates. A different ground-truth
technique retrieved for the same mapped-multi view does not count as a hit.

| Technique | Positive views | Specific Hit@1 | Specific Hit@3 | Specific Hit@5 | Specific Hit@10 | Median rank |
|---|---:|---:|---:|---:|---:|---:|
| T1053.005 | 93 | 0.0753 | 0.1505 | 0.1720 | 0.4516 | 7 |
| T1059.001 | 113 | 0.0177 | 0.3894 | 0.4956 | 0.6814 | 3 |
| T1059.003 | 111 | 0.0180 | 0.0180 | 0.0270 | 0.1712 | 8 |
| T1105 | 114 | 0.0000 | 0.0000 | 0.0000 | 0.1579 | 9 |
| T1136.001 | 99 | 0.0000 | 0.0000 | 0.0202 | 0.1010 | 7 |
| T1543.003 | 114 | 0.0000 | 0.0000 | 0.0351 | 0.3070 | 8 |
| T1547.001 | 106 | 0.1509 | 0.3491 | 0.5755 | 0.9245 | 4.5 |
| T1685.005 | 62 | 0.0806 | 0.5484 | 0.7903 | 0.9839 | 3 |

## Determinism and test evidence

The JSONL writer uses stable input order, stable key ordering and seven-digit
score serialization. Unit tests cover:

- duplicate sample IDs, missing ground truth, missing evidence and malformed
  ATT&CK IDs;
- retrieval-only query isolation;
- contiguous rank validation and Top-k prefix consistency;
- single-label, multi-label Hit@k versus macro Recall@k, specific-technique
  ranks, exact split partition and negative metric semantics; and
- semantic equality across repeated runs.

Targeted command:

```text
uv run pytest tests/test_retrieval_diagnostics.py -q
20 passed
```

Full-benchmark command:

```text
uv run python -m src.evaluation.retrieval_diagnostics
```

Artifacts:

- `artifacts/retrieval/retrieval_diagnostics.jsonl`
- `artifacts/retrieval/retrieval_metrics.json`

Diagnostic JSONL SHA-256:

`a78377b66db09f23088fc4da73570b06d69c2413a67ad5c789e9808953c24777`

Metrics JSON SHA-256:

`83e9cef4ae9714885fb2965bb01664eed6b9e449c2de23b33fe7c88ae8ed531b`

## Limitations

These measurements evaluate retrieval only. They do not estimate LLM
accuracy, RAG-vs-No-RAG improvement, or causal benefit. The positive
denominator follows the frozen per-view ground truth and excludes ambiguous
and unmapped cases. The actual full-regression, integration, frozen-benchmark
verification, review, push and PR gates remain coordinator gates.
