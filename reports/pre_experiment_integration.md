# Pre-experiment integration verification

This branch verifies the T20, T15, T21 and evaluator infrastructure together.
It is an engineering candidate, not approval to freeze or run research.

## Traceable input stack

Base main: `cdb19719a179dd43c868a39ca158a662ad3a0eb9`.

| Order | Existing PR | Input HEAD |
|---|---|---|
| 1 | #14 / T20 | `3f4de8ce413062c8f76b20d03a1c7530f3c74776` |
| 2 | #15 / T15 | `3e4806cc91908b991645e9239860ec95632e24f8` |
| 3 | #17 / T21 | `ebc134f2ee88abf32f50b3f1ab287c27f137df4d` |
| 4 | #16 / evaluator | `96e20daa87a5d17458927b3e85ef6d8d3198d956` |

All four were merged without textual conflicts into this dedicated branch.
Original PR branches were not changed. PR #8 is excluded and remains draft.

## Repairs

- The inherited T20 Ruff settings remain Python 3.13, line length 100 and
  E/F/W/I. The 176 E501 findings across the integrated scope were corrected.
  Commit `6023c9d` changes formatting only: AST comparison before/after was
  identical for all 11 inspected files (10 changed), including string values.
- Manifest and dry-run reports explicitly include
  `raw_response_logging_policy: HUMAN_DECISION_REQUIRED`. The repository's T22
  roadmap snapshot requests caching, while inherited logging disables it.
  Human reconciliation is required; this branch does not choose a new policy.
- The dry-run report exposes `live_execution_implemented=false`. Raw logging
  stays off; records retain `raw_response=null` and `raw_response_logged=false`.
  T21 remains `NOT_FROZEN`; the public CLI is dry-run-only.
- CI retains the T20 lint gate, adds scoped infrastructure lint and runs tests
  and frozen verification through the offline guard. Reference/model acquisition
  happens before guarded test execution. Mutation tests reject removed,
  unguarded, conditional or nonblocking critical gates.
- A persistent same-checkout regression uses the existing two-view fixture,
  produces ten mock records across five conditions, validates them through the
  evaluator, computes retrieval observations and tests resume without new calls.
  GT annotation sentinels never reach provider requests; adding GT fields to
  execution records fails schema validation. Both canonical scoring entrypoints
  remain blocked even with caller-supplied approval flags.

## Verification contract

The raw-response regressions were observed failing before the new decision
reason was added. The CI suite detected the missing infrastructure lint step.
Independent review then reproduced eight ways of disabling critical gates with
`if: false` or `continue-on-error: true`; those regressions failed before the
repair and passed afterward. Independent review passed the final code commit
`be6ca06c5e43d6e98ea15ebc24da01d467f76793` with no remaining BLOCKER/MAJOR.

The final code must pass scoped Ruff, all non-integration tests, real retrieval
integration, frozen verification, lock/dependency checks and `git diff --check`.
Use the guarded launcher, including for real retrieval tests after cache setup:

```text
python scripts/run_offline_tests.py -m pytest -m "not integration" -q
python scripts/run_offline_tests.py -m pytest -m integration -q
python scripts/run_offline_tests.py -m src.data_ground_truth verify-synthetic
```

Dry-run exit 2 is intentional: structural validation passes while scientific
approval remains unresolved. Expected TEST cohort is 640 pairs / 1,280 views,
6,400 logical requests and at most 25,600 attempts under inherited retry limits.
These are estimates, not approved API usage.

## T20 and protected state

Independent recomputation of the captured diagnostics confirms:

- Positive views: 756.
- Hit@1/3/5/10: 0.042328042328042326 / 0.167989417989418 /
  0.24206349206349206 / 0.45105820105820105.
- Candidate/eligible/excluded pairs: 670 / 296 / 374.
- Single-better/contextual-better/equal: 65 / 23 / 208.
- Both-absent/top10-equal: 147 / 61; both partition identities hold.
- T1136.001: 99 positive views, zero Top-10 hits, 99 absent, median null.

GT, frozen retrieval artifacts, corpus, index, prompts and model/retrieval
configuration were not edited. Workbook/context files are strictly read-only;
no progress or task status was written to any Sheet. The existing analysis
summary changes relative to main come solely from PR #14; its bytes and the
retrieval diagnostics/metrics remain identical to that reviewed PR. No scientific
artifact was regenerated. Frozen verification only reproduces into temporary
scratch space for comparison.

## Remaining human decisions

Raw-response persistence, canonical evaluator semantics (multi-label/empty GT,
macro/failure/invalid-ID denominators, retired IDs, conditional any/all GT and
failure precedence), model-version policy, concurrency, API authorization and
finite budget remain unresolved. T15 additionally requires approved genuine
Windows telemetry and provenance. T33 still requires full-text access for Yang
& Hsu and Okuma; it is not part of this integration branch.

No live LLM calls, research predictions, T22-T26 runs or main merges are
performed. Even after engineering checks pass, scientific status remains
`SCIENTIFIC_PROTOCOL_NOT_FROZEN`. GitHub acceptance requires all required jobs
at the exact final integration HEAD; local passes do not substitute for that.
