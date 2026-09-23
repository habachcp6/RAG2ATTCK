# T21 pre-freeze experiment infrastructure

Status: **T21_INFRA_READY / NOT_FROZEN**, subject to independent review and final
branch CI. T21 is not Done. Its T15/T20 dependency graph is unchanged. T15 still
requires approved sanitized real telemetry, provenance, explicit provider/API
authorization and an approved finite request budget. No T22–T26 experiment ran.

## Read-only configuration and validation

`config/experiment_config.json` binds the frozen synthetic TEST split: 640 pairs,
1,280 views, all five conditions and 6,400 first attempts. The inherited retry
limit of three yields a maximum of 25,600 attempts. These counts are estimates,
not authorization or a chosen API budget. Model version, concurrency and
`max_requests` remain explicitly unresolved. A missing budget field is invalid;
a present null budget is allowed only as a pre-freeze blocker.

The existing canonical model configuration, single-technique output schema and
base prompt remain unchanged. Provider-default temperature and seed are recorded
as omitted parameters, not invented numeric settings. Raw response storage
remains disabled. Ground-truth semantics and evaluator definitions are human
decisions; the runner does not silently filter multi-label or negative views.

### Unresolved raw-response policy

Both the candidate manifest and dry-run report explicitly list
`raw_response_logging_policy: HUMAN_DECISION_REQUIRED`. The repository's tracker
snapshot (Roadmap, T22, cell F24) requests raw-response caching, while the inherited
model/experiment policy disables persistence. These requirements need human
reconciliation before scientific freeze. This change does not select a logging
policy or edit the tracker: `logging.raw_response=false`, record `raw_response=null`
and `raw_response_logged=false` remain unchanged.
These dedicated fields do not prove that provider output is absent from every
persisted field: schema-validation and refusal details can appear in
`error_message`. Whether to retain or redact such details is part of the
unresolved human raw-response/error-detail policy.

The dry-run report also exposes `live_execution_implemented=false`
(`LIVE_EXECUTION_IMPLEMENTED=NO`). Filling other configuration placeholders does
not resolve the raw-response decision, permit live execution, or freeze T21.

Run the public, non-executing command:

```powershell
python -m src.experiment --dry-run
```

It prints a JSON validation report. Exit 2 means structural checks passed but
human decisions/scientific freeze remain outstanding; exit 1 means invalid or
missing artifacts/configuration. There is no live, freeze, force or execution
command. No SDK or embedding model is constructed. No prediction, manifest or
scientific artifact is written, even when preflight succeeds.

Configuration, inference, GT, view/pair/split maps, dataset manifest, prompt,
model/retrieval configs, ATT&CK registry, corpus, index, document mapping and
retrieval manifest are captured as bytes once. SHA256 checks and all parsing use
those same bytes, including FAISS deserialization. Metadata/path relationships,
pair/view coverage, model settings, release, index shape and document mapping are
cross-checked. All configured artifact paths stay inside the supplied root and
are resolved independently of the caller's working directory.

## Candidate manifest and record contract

The in-memory manifest is schema `1.0.0`, `status=pre_freeze` and
`execution_mode=pre_freeze`. It records code HEAD, exact experiment-config hash,
each artifact path/hash, the captured canonical model and retrieval mappings,
output-schema hash, ordered sample/condition matrix, request estimates, logging
policy and unresolved human decisions. `artifacts.experiment_config` binds the
actual source config bytes; its SHA must match `config_sha256`.

The canonical manifest SHA is calculated over UTF-8 JSON with sorted keys,
`separators=(",", ":")`, `ensure_ascii=False`, `allow_nan=False`, without a trailing
newline. File formatting does not enter the manifest-object SHA; artifact hashes
always bind original file bytes. No manifest is scientifically frozen here.

`ExperimentRecord` is an outer flat schema, retaining the existing client and
RAG metadata internally. It identifies experiment/run/sample/pair/view/condition,
all provenance hashes, exact retrieval depth and ranked candidates, the existing
seven parse statuses, zero or one parsed technique ID, token usage, latency,
retry and actual attempt counts, errors and a UTC timestamp. `success` means a
validly parsed registry ID, not agreement with GT. Unknown token usage stays
null; `raw_response` is null and `raw_response_logged` is false. Frozen
ground-truth annotations and dataset rationales are excluded from inference
inputs and execution records; provider text in `error_message` is governed by
the unresolved logging decision above.

## Mock-only execution and durable resume

`run_mock_experiment` is a Python test harness accepting only the concrete
in-memory `MockProvider`. It reuses the actual `LLMClient`, baseline/RAG pipelines,
FAISS retrieval with `StubEmbedder`, and one explicit journal-backed `LiveBudget`.
It cannot choose a real SDK client or download an embedding model. Fixture
manifests/records explicitly carry `execution_mode=mock_fixture`. In-repository
outputs are allowed only under `.tmp`; other outputs must stay in the resolved
system temporary directory. Sibling worktrees and scientific output paths are
rejected. All pipeline inputs are rederived from captured bytes before execution,
and both pipelines accept the same captured prompt without reopening files.

Files are `manifest.json`, five condition prediction JSONL files,
`request_journal.jsonl` and `run_summary.json`. An exclusive output lock and
fsynced request reservations protect against double dispatch. Resume validates
the immutable manifest, every record, journal sequence, sample-condition key and
persisted request spending. Schema-valid terminal failures are skipped exactly
like successful records. An incomplete journal, interrupted request, truncated
row, duplicate, provenance mismatch, foreign file or stale lock fails closed.
Prediction records and the request journal are never automatically repaired or
silently overwritten. A fully completed resume rebuilds only the derived summary
from validated records/journal, without dispatch. There is no budget reset or
`--force` bypass. Saved candidates must belong to the captured corpus and registry,
even if a modified record has a newly computed journal checksum.

An interrupted write of the derived `run_summary.json.tmp` can be recovered
after validating the journal and records, without new provider calls. Resume
rejects symlinked or hardlinked output entries before dispatch; rebuilding the
summary removes a stale temporary entry before exclusive creation.

An ambiguous interrupted request requires explicit human reconciliation; this
implementation does not claim exactly-once network execution. The budget counts
reservations before dispatch conservatively and never reconstructs spending from
`retry_count`. Unknown monetary cost is reported as unknown, because no approved
price schedule or input-token ceiling is present.

## Validation and remaining gates

The targeted suite uses a manually constructed two-view synthetic fixture and
an offline guard. It covers all five actual provider request shapes, condition
and schema consistency, GT isolation, explicit budgets and retry accounting,
byte/hash binding, resume across terminal failures, interrupted dispatch,
locking, corruption rejection and the canonical 1,280-view dry-run. Scientific
inference and canonical scientific scoring remain unavailable; the mock
evaluator can load and inspect the same-checkout fixture records.

Local verification of implementation commit `07bd81a`: **52 experiment tests**,
**605 non-integration tests** and **4 real-retrieval integration tests** passed,
with `OFFLINE_GUARD: installed=True attempted_egress=0`. Frozen verification
reported `passed=true` and zero artifact/reproducibility hash mismatches; lockfile
and installed-dependency checks also passed. These are infrastructure checks,
not scientific results. The candidate-corruption and stale-summary regressions
were observed failing before their implementation repair.
Scoped Ruff passes for the new package and tests. The two minimally extended
legacy pipeline files retain their existing 12/22 Ruff findings; comparison with
base `cdb19719a179dd43c868a39ca158a662ad3a0eb9` found zero introduced findings.

Branch acceptance still requires scoped Ruff, the full non-integration suite,
real retrieval integration, frozen benchmark verification, dependency integrity,
protected-path diff review and exact-head GitHub CI. These checks are engineering
evidence only and cannot approve T21 freeze or relax the T15/T20 gates.
