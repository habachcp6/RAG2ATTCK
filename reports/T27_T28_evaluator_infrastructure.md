# T27/T28 evaluator infrastructure — partial, not executed

Status: **EVALUATOR_INFRA_PARTIAL**. Roadmap T27 and T28 remain **Not Started**.
No research predictions or evaluation results were produced. This work preserves
the single-ID prompt/schema, the complete TEST1280 cohort (including multi-label
and empty-GT views), ATT&CK 19.2, and all frozen scientific artifacts.

## Implemented boundary

The offline evaluator consumes the version 1.0.0 experiment manifest and flat
execution-record mappings. It reads each artifact once, verifies its SHA-256,
then parses those same captured bytes. Dataset-manifest bindings, TEST/DEV pair
partition, two views per pair, sample/GT/view joins, registry/corpus membership,
output-schema identity, and complete sample-by-condition coverage must agree.
Records bind to the canonical manifest hash and its model, schema, prompt,
dataset, GT, corpus, index and sample metadata. GT enters only this evaluator
join, never a prediction record or inference payload. Duplicate, missing,
unknown, nonterminal, inconsistent or corrupt records fail closed.

Only explicitly marked mock-fixture execution records are supported at this
pre-freeze stage. The public loader always requires all 1,280 TEST views and all
five conditions. Tests use a private cardinality seam with eight TEST views and
two DEV views; it does not unlock canonical scoring. The fixture exporter uses
exclusive creation inside the system temporary directory and cannot write
research outputs.

Confirmed retrieval arithmetic follows T20: Hit@k means any GT ID retrieved;
Recall@k is the fraction of a positive view's GT IDs retrieved, averaged over
positive views. Empty GT has no retrieval metric denominator. Candidates come
from each condition's actual recorded depth; the evaluator never runs retrieval.
Parse-status and retired-ID observations stay separate, without inventing a
failure precedence or invalid-ID rate. A retrieval miss can coexist with a
correct final prediction.

## Scientific decisions still required

Both `evaluate_end_to_end` and `evaluate_conditional_accuracy` always raise
`HUMAN_DECISION_REQUIRED`. Caller-provided flags, config or claimed approval
cannot bypass this gate. A reviewed future implementation is required after
the human decisions are recorded; no approval has been inferred here.

- Scoring a single predicted ID against multi-label or empty GT, including
  negative/abstention handling. Do not select a GT-filtered cohort or change the
  output schema to resolve this implicitly.
- Macro class universe, treatment of execution/parse/invalid outcomes in metric
  denominators, and zero-denominator conventions.
- Retired/deprecated ATT&CK validity and invalid-ID-rate denominator. Existing
  registry membership includes retired IDs; the README wording does not settle
  this discrepancy. Their observed count is not an invalid-ID-rate conclusion.
- Any-GT versus all-GT conditional presence for multi-label views and precedence
  between invalid-output, execution, retrieval and downstream failures.

The planned canonical exports remain `end_to_end_metrics.json`, per-class
metrics, `retrieval_conditional_metrics.json`, and `failure_decomposition.json`
under `artifacts/evaluation/<experiment_id>/`; they are not generated here.

## Validation

Known-answer tests use eight mock execution cases, repeated across the five
conditions, and twelve manually calculated single-label arithmetic cases.
The latter require an explicit **fixture-only** class universe, all-fixture-row
denominator and zero-division policy; they do not preregister those choices for
the study. Tests cover exact sub-technique strings, perfect/all-wrong cases,
per-class/macro arithmetic, partial multi-label retrieval, negatives, unknown
and retired IDs, provider/parser failure, actual-byte hash tampering, malformed
JSON and envelopes, complete matrix joins, row-order determinism, no-overwrite,
and hash/read-race prevention. All outputs are temporary fixture diagnostics.

Local validation on the implementation tree:

- Evaluator tests: **51 passed**; full non-integration regression: **604 passed,
  4 deselected**; real-retrieval integration: **4 passed, 604 deselected**.
- Every Python test run above used `scripts/run_offline_tests.py` and reported
  `OFFLINE_GUARD: installed=True attempted_egress=0`.
- `verify-synthetic`: `passed=true`, `artifact_hash_mismatches=0`, and
  `reproducibility_hash_mismatches=0`; its guard also reported zero egress.
- Scoped Ruff and `git diff --check` passed. `uv lock --check --offline` resolved
  the existing 108-package lock; `uv pip check` found all 87 installed packages
  compatible. No dependencies changed.
- Serialized C-to-D interoperability smoke used the current T21 fixture
  builder, config validator and concrete mock runner, then loaded its actual
  manifest and five JSONL files through this evaluator: **2 samples, 5
  conditions, 10 fixture records, 10 mock calls, 0 real calls**. The canonical
  scoring gate remained closed even with a caller-supplied approval flag.

These are local infrastructure checks, not research findings or final-SHA
GitHub Actions evidence. Human scientific decisions and later PR/main CI remain
separate gates.
