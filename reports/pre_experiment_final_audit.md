# Pre-experiment final engineering audit

This report records engineering evidence only. It does not freeze the scientific
protocol, authorize provider spending, or claim real-data results. The tracker
workbook was inspected read-only; no tracker, frozen benchmark, or live provider
output was written.

## 1. Exact repository state

- Repository: habachcp6/RAG2ATTCK.
- Working branch: fix/pre-experiment-finalization, created at the exact PR #18
  head before edits.
- PR #18: open Draft, base main, technically mergeable before finalization.
- Working-tree cleanliness and exact final Git SHA are to be checked after the
  report commit. A Git commit cannot contain its own SHA; the final handoff
  records the resulting SHA and exact-head Actions conclusions.

## 2. Base/main SHA

cdb19719a179dd43c868a39ca158a662ad3a0eb9, verified against origin/main
at audit start.

## 3. PR #18 original SHA

58554917cec27de97a89c380345f1a32cbefd8f3, verified through GitHub and the
local remote-tracking branch at audit start.

## 4. Final working SHA

The commit carrying this report is the final candidate; run git rev-parse HEAD
in fix/pre-experiment-finalization or inspect PR #18 headRefOid. The final
handoff records the literal SHA and its Actions runs after push, since this
file cannot self-embed the SHA of its own commit.

## 5. Integrated PR lineage

All four reviewed input heads are ancestors of PR #18 and this branch:

| Input | Exact integrated head |
|---|---|
| PR #14, T20 | 3f4de8ce413062c8f76b20d03a1c7530f3c74776 |
| PR #15, T15 | 3e4806cc91908b991645e9239860ec95632e24f8 |
| PR #17, T21 | ebc134f2ee88abf32f50b3f1ab287c27f137df4d |
| PR #16, evaluator | 96e20daa87a5d17458927b3e85ef6d8d3198d956 |

The T20 canonical analysis artifact is byte-identical to PR #14. The T15
pilot code differs from PR #15 only through PR #18 integration formatting.
PR #8 is separate T33 work and is not incorporated here.

## 6. Findings by severity

| Severity | Finding | Resolution |
|---|---|---|
| MAJOR | Direct injection of a real OpenAI SDK client could bypass the one-attempt-one-budget accounting and retain SDK retries. | Rejected injected SDK instances; real constructor retains zero SDK retries and explicit budget accounting. |
| MAJOR | Resume rejected an interrupted derived-summary replacement, while accepting a stale temporary hardlink could overwrite an external file. Mutable hardlinked journal/prediction files could also be appended outside the run directory. | Recover only the known stale derived summary; reject symlinked/hardlinked output entries before dispatch and recreate summary temp exclusively. |
| MAJOR | Evaluator accepted rehashed GT-bearing inference fields, path escapes, corpus/docmap drift, inconsistent counts/retry limits, and a full prediction matrix with an incomplete request journal. | Bound artifacts, config and records to captured bytes; require exact producer journal completion in the public loader. |
| MAJOR | CI contract tests missed trigger, supporting-job, setup and acquisition gate mutations; offline guard missed three DNS audit events. | Added mutation cases and DNS event denial, preserving existing workflow triggers. |
| MINOR, corrected | README and historical reports overstated schema syntax enforcement, synthetic allowlist scrubbing, model backend freeze and prior test finality. | Corrected factual wording while retaining human-owned scientific questions. |
| MINOR, bounded | The Python offline audit hook is not an operating-system network sandbox and does not control arbitrary native executables. | Reviewed guarded subprocess paths: only local Git commands and guarded Python children occur in current tests. No broader isolation claim is made. |

No unresolved local code-review BLOCKER or MAJOR was found. Merge readiness
still requires final-head CI; scientific decisions in section 15 remain open.

## 7. Fixes made

- Strengthened experiment budget, anti-leakage and resume boundaries.
- Required evaluator provenance joins, complete producer journal, exact
  artifact containment, strict JSONL and retry limits.
- Added observation-only token/latency sums and present/missing counts. No
  averages, costs or canonical RQ3 conclusions were defined.
- Strengthened CI mutation contracts and offline DNS attempt detection.
- Added an independent stdlib T20 canonical verifier, without changing its
  frozen artifacts or retrieval method.
- Corrected only factual documentation; the synthetic empirical claim scope,
  metric definitions and raw-response policy are still unresolved.

## 8. Regression tests added

Tests first failed against the relevant old behavior for injected SDK clients,
stale-summary recovery, hardlink overwrite, rehashed inference GT fields,
evaluator path/count/retry/docmap drift, incomplete/tampered journals,
unterminated or blank JSONL, disabled CI triggers/gates and unguarded DNS
events. The independent T20 verifier has a rehashed summary mutation that
must fail on the T1136.001 absence count. Cross-agent read-only reviews found
no remaining BLOCKER or MAJOR in these patches.

## 9. Final local test matrix

| Gate | Command or method | Observed result |
|---|---|---|
| Dependency lock | uv lock --check --offline | PASS, 108 resolved packages |
| Install | uv sync --frozen | PASS, 87 installed packages |
| Dependency consistency | uv pip check | PASS, 87 compatible packages |
| CI T20 Ruff scope | Exact Lint T20 critical code paths command from ci.yml | PASS, 0 findings |
| CI infrastructure Ruff scope | Exact Lint pre-experiment infrastructure command from ci.yml | PASS, 0 findings |
| Added guard Ruff scope | uv run ruff check scripts/offline_guard/sitecustomize.py tests/test_offline_guard.py | PASS, 0 findings |
| Targeted subsystem tests | Guarded 16-file T20/T15/T21/evaluator/CI/retrieval/RAG selection | 643 passed, 0 egress |
| Full non-integration | Guarded pytest -m "not integration" -q | 1,002 passed, 4 deselected, 0 egress |
| Real retrieval integration | Guarded pytest -m integration -q after pinned model acquisition | 4 passed, 1,002 deselected, 0 egress |
| Whitespace/cleanliness | git diff --cached --check and git status | PASS, only 17 intended files staged; final-head recheck follows commit |

Exact rerun commands for the locally observed lint and targeted test gates:

    uv run ruff check scripts/analyze_retrieval_failures.py scripts/verify_t20_canonical_artifacts.py tests/test_retrieval_failure_analysis.py tests/test_t20_canonical_artifacts.py
    uv run ruff check src/experiment src/evaluation/experiment_metrics.py src/evaluation/fixture_metrics.py src/pilot/no_rag_pilot.py tests/test_experiment.py tests/test_experiment_evaluation.py tests/test_pilot_hardening.py tests/test_pre_experiment_integration.py tests/test_ci_contract.py
    .venv\Scripts\python.exe scripts\run_offline_tests.py -m pytest tests\test_retrieval_diagnostics.py tests\test_retrieval_failure_analysis.py tests\test_t20_canonical_artifacts.py tests\test_no_rag_pilot.py tests\test_pilot_hardening.py tests\test_experiment.py tests\test_llm_client.py tests\test_experiment_evaluation.py tests\test_ci_contract.py tests\test_offline_guard.py tests\test_retriever.py tests\test_retrieval_integrity.py tests\test_rag_pipeline.py tests\test_baseline_pipeline.py tests\test_pre_experiment_integration.py tests\test_live_budget.py -q
    .venv\Scripts\python.exe scripts\run_offline_tests.py -m pytest -m "not integration" -q
    .venv\Scripts\python.exe scripts\run_offline_tests.py -m pytest -m integration -q

## 10. Frozen benchmark verification

Guarded verify-synthetic reported passed=true,
artifact_hash_mismatches=0, reproducibility_hash_mismatches=0,
pairs=670, views=1,340, and attempted_egress=0. It regenerated comparison
outputs in scratch space and did not change canonical benchmark files.

## 11. T20 canonical recomputation

scripts/verify_t20_canonical_artifacts.py independently joins the frozen GT
and view sidecars with the saved diagnostic JSONL, recomputes candidate ranks,
Hit@k and same-technique pairwise anchors, then compares committed metrics and
analysis. It hashes all five read sources before recomputation.

| Check | Observed |
|---|---:|
| Positive views | 756 |
| Hit@1 / Hit@3 / Hit@5 / Hit@10 | 0.042328042328042326 / 0.167989417989418 / 0.24206349206349206 / 0.45105820105820105 |
| Candidate / eligible / excluded pairs | 670 / 296 / 374 |
| Single better / contextual better / equal | 65 / 23 / 208 |
| Both absent Top-10 / equal in Top-10 | 147 / 61 |
| T1136.001 positive / Top-10 hit / absent / median rank | 99 / 0 / 99 / null |

The independent verifier and its rehashed-mutation regression passed. T20
remains retrieval-only; no ground truth is sent to retrieval or a model.

## 12. Mock experiment verification

The same-checkout two-view fixture runs five conditions through the concrete
MockProvider, writes 10 records and a request journal, then loads and checks
them in the evaluator. All records use the same sample IDs, schema, model
configuration and prompt; only retrieved context/depth varies. GT-bearing
extra inference fields fail even after coordinated rehash. Completed resume
uses zero additional mock calls. Stale derived summary recovers; ambiguous,
corrupt, symlinked and hardlinked state fails before dispatch. Canonical
scientific scoring raises HUMAN_DECISION_REQUIRED even with caller flags.
No live model call occurred.

The real TEST preflight validates 640 pairs, 1,280 views, five conditions,
6,400 logical requests and 25,600 maximum attempts (three retries after
the first attempt). It exits 2 with HUMAN_DECISION_REQUIRED and reports
provider_calls=0, prediction_writes=0, live_execution_implemented=false,
max_requests=null and scientific_status=NOT_FROZEN.

## 13. CI final-head evidence

Final-head GitHub Actions evidence is necessarily collected after the commit
and push carrying this report. Verify CI, Linux and Windows full-suite jobs,
synthetic verification and Real Retrieval Integration against the literal
PR #18 head SHA in the final handoff. Previous-head green runs are not
substitutes. The committed report does not self-assert a future CI result.

## 14. Protected files verification

The final diff against main contains no changes under data/ground_truth,
attack, prompts, artifacts/retrieval, config/model.json or
config/retrieval.json. The T20 analysis summary differs from main only through
the integrated PR #14 and is byte-identical to that reviewed PR head. The
ATT&CK v19.2 raw registry was copied only as an
ignored local test resource after its SHA-256 matched
dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4.
No protected artifact changed relative to the PR #18 starting HEAD. The
tracker workbook was opened read-only to check Roadmap T15/T21/T22 wording and
was not saved.

## 15. Human decision matrix

Every row below is HUMAN_DECISION_REQUIRED. Options are alternatives for the
researcher, not selections by this audit. Implementing any option requires a
separate reviewed protocol change.

| Decision | Current state | Options and consequences | Files affected after approval |
|---|---|---|---|
| D1 raw response and error-detail retention | Tracker Roadmap T22/F24 asks to cache raw responses. Model and experiment configs disable raw_response storage; records store null/false. Validation/refusal/provider errors can still retain provider text in error_message. | Keep full raw output with access/storage/privacy controls for replay; redact or omit it with less debugging evidence; or retain a bounded sanitized digest/excerpt. Specify error_message treatment consistently. | config/model.json; config/experiment_config.json; src/llm/client.py; src/experiment/runner.py; report and privacy/provenance tests |
| D2a single vs multi-label GT | Output schema predicts one ID; frozen TEST includes mapped_multi views and no primary-label field. | Accept any GT, add a separately approved primary-GT annotation, or redesign prediction as a set. Each changes correctness semantics or schema. | evaluator; GT annotation/sidecar only after separate approval; src/llm/schemas.py if schema changes; README; protocol report |
| D2b empty/unmapped GT | TEST also includes empty GT; canonical accuracy/F1 is blocked. | Exclude with declared denominator; approve an abstention/negative output contract; or report a separate stratum. Abstention requires a prompt/schema/runner change, not evaluator arithmetic alone. | evaluator; prompts/baseline_v1.txt, output schema/parser and runner only after protected protocol approval; protocol report |
| D2c ambiguous GT | Ambiguous views have no resolved technique set. | Exclude and report coverage; adjudicate independently; or retain as a separate non-headline category. | evaluator; GT only after separate approved research change; protocol report |
| D2d Macro-F1 class universe | README names Macro-F1 but does not freeze class set/zero support. | Eight candidate classes, observed GT/predicted union, or wider ATT&CK universe; each gives different macro denominator. | evaluator; README; protocol report |
| D2e invalid-ID denominator | Invalid syntax and unknown registry IDs share INVALID_ID status, with per-record error detail; retired IDs have a separate observation count. There is no canonical rate. | Divide by all logical samples, completed outputs, or parseable outputs; publish coverage alongside rate. | evaluator; protocol report |
| D2f API/error and retry denominator | Provider/parse failures and retries are logged; headline accuracy denominator is unresolved. | Count failed logical samples as incorrect or report successful-call conditional accuracy separately; count attempts only for efficiency. | evaluator; experiment config; protocol report |
| D2g retired/deprecated ATT&CK IDs | Registry membership can accept retired IDs; README formerly implied they are invalid. | Treat as invalid at v19.2; valid if in pinned registry; or a separate status. | evaluator; ATT&CK validation policy; protocol report |
| D2h conditional retrieval success | T20 Hit@k uses any GT; canonical conditional accuracy for multi-label views is unresolved. | Condition on ANY GT present or ALL GT present, with explicit denominators. | evaluator; protocol report |
| D2i failure precedence | A retrieval miss can overlap a provider failure or invalid output; those two terminal parse statuses cannot coexist in one record. | Define ordered exclusive categories or publish nonexclusive retrieval/output axes; neither is frozen. | evaluator; protocol report |
| D2j zero-denominator conventions | Fixture math chooses a test-only zero policy; canonical class/conditional denominators remain open. | Null/not-applicable or zero, with declared inclusion rules. | evaluator; protocol report |
| D3 model-version policy | provider=openai, model=gpt-5.6-luna, effort=xhigh and Responses are configured; exact provider backend version is null and may be unavailable. | Pin a supported immutable snapshot if exposed; or log model ID/response metadata/time and explicitly accept backend drift; or defer live study. Do not invent a version. | config/experiment_config.json; model provenance/records; protocol report |
| D4 concurrency | Draft execution.concurrency is null; mock execution is sequential. | Approve sequential ordering with simpler resume/accounting, or bounded concurrency with rate-limit, ordering and durable atomic budget controls. | config/experiment_config.json; future live runner; protocol report |
| D5 finite live budget | 1,280 views × 5 = 6,400 logical calls; max_retries=3 means at most 4 attempts each, 25,600 attempts. max_requests is null, monetary cost unknown, no live runner. | Approve a finite hard request cap and staged stop/resume plan, possibly below worst case; separately authorize spending. Budget must reserve before every attempt and cover concurrency. | config/experiment_config.json; future live runner; budget/provenance report |
| D6 T15 prerequisite and pilot size | Tracker T21 depends on T15/T20; T15 lacks approved real telemetry/API authorization. Tracker T15 suggests 20–50 samples while current pilot caps at 20. | Require completed T15 before T21 freeze; require it only for real-data claims; or formally declare an optional pilot. Reconcile pilot size without relabeling synthetic as real. | T15/T21 protocol reports; tracker only after human action; pilot config/code only if size changes |
| D7 DATASET CLAIM SCOPE | README/research plan frame synthetic as diagnostic only; T21 draft binds 1,280 TEST synthetic views as a five-condition experiment candidate. Tracker overview also describes a smaller evaluation-sample scope. | A: synthetic primary controlled RQ1–RQ3 with bounded synthetic claims; B: synthetic engineering only and genuine telemetry for empirical claims; C: synthetic primary plus separate real validation. Each changes claim scope and live cohort. | README; config/experiment_config.json; T21/evaluator reports; protocol and eventual paper |

## 16. Remaining blockers

Engineering readiness depends on the final local and exact-head CI gates in
sections 9 and 13. Scientific freeze is blocked by section 15, especially
D1, D2, D5, D6 and D7. T15 live pilot remains DATA_UNAVAILABLE. No T22–T26
run is authorized or implemented by this finalization.

## 17. PR merge-readiness

PR #14, #15, #16 and #17 are incorporated and may be classified
SUPERSEDED_BY_PR18 after the human merges PR #18. They remain open and were
not closed. PR #18 remains Draft; classify it MERGE_READY only after the
exact final-head CI and integration gates pass. No PR was merged.

## 18. Exact recommended next human action

Review this report and the exact PR #18 final-head checks. If satisfied,
manually mark PR #18 ready and merge it. Then decide section 15, beginning
with dataset claim scope and T15 dependency; approve a protocol artifact,
genuine telemetry and a finite API budget before any live experiment.
