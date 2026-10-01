# Real-provider DEV cost pilot — 2026-10-01

The approved pilot produced 20 real OpenAI Responses API records on frozen synthetic DEV views. All 20 records are VALID, with 20 provider attempts and zero retries. This is a partial DEV cost measurement, not a canonical TEST experiment, paired accuracy evaluation, or real Windows-APT telemetry result.

## Provenance and scope

- Executed source commit: `e94447f47a8eee96fb2aa4c3f05be6e37031b705`.
- Run ID: `live-dc6b3166114d401e`; API model and returned model: `gpt-5.6-luna`.
- Generation settings: `reasoning_effort=xhigh`, `max_output_tokens=8192`, retries `3`, concurrency `1`.
- Selected DEV views: `view_03f93863`, `view_0b5e295e`, `view_0bec9523`, `view_0d8155cd` (two contextual and two single views from four pair IDs).
- Each view ran `no_rag`, `rag_k1`, `rag_k3`, `rag_k5`, and `rag_k10`.
- Staging: one canary record, followed by an explicit resume limited to 19 new records. The stage bound was 20 records / at most 80 attempts. D5 requires a 1,200-attempt authorization for the complete 60-view DEV plan; that larger matrix was not executed.
- The manifest correctly retains `complete=false`: 20 of the 300 DEV matrix records exist. No TEST predictions were produced.
- All 14 referenced frozen artifacts were copied byte-for-byte into an isolated DEV artifact root. Model, prompt, retrieval settings, original datasets/GT, canonical config/protocol/lock, and tracker were not changed.
- The derived DEV protocol preserves D1–D6 and changes D7 to `DEV_SMOKE`. It references the user's explicit pilot approval; the recorded approval timestamp is `2026-09-30T22:03:53+00:00` (2026-10-01 in Asia/Saigon).
- DEV config SHA-256: `9061673f61d79cf68d72e012829736940d41b1937ed39b8d23514bc87b1f351e`.
- DEV protocol SHA-256: `9aba55cb942d72cb4922c12fee263af8e4d491f153f5b5ed47aac22d3b00b3a7`.

## Observed usage and estimated cost

| Condition | Records | Input tokens | Output tokens |
| --- | ---: | ---: | ---: |
| no_rag | 4 | 2,572 | 897 |
| rag_k1 | 4 | 4,460 | 1,329 |
| rag_k3 | 4 | 6,962 | 4,349 |
| rag_k5 | 4 | 10,073 | 3,361 |
| rag_k10 | 4 | 18,146 | 3,203 |
| Total | 20 | 42,213 | 13,139 |

Mean output usage was 656.95 tokens per request; the largest record used 2,421 output tokens. Mean recorded latency was 8.128 seconds. Output usage includes billable reasoning, not only the visible JSON answer.

At Standard prices of $0.20 per million input tokens and $1.20 per million output tokens, the usage-based estimate is **$0.0242094**. Applying a conservative $0.25 input rate yields **$0.02632005**. These are price-based estimates, not a queried billing invoice; input-cache discounts were not assumed. Prices were checked in the [GPT-5.6 Luna documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna); [reasoning-token billing](https://developers.openai.com/api/docs/guides/reasoning) explains the output accounting.

## Budget interpretation

An offline `o200k_base` count of all 6,400 planned TEST prompts, using the saved real retrieval diagnostics bound to the frozen corpus/index, estimated 15,766,654 input tokens including serialized output-schema text (API overhead may differ). At the observed pilot output mean, a no-retry Standard-price projection is **$8.1987068**; using the conservative input rate gives approximately **$8.99**.

This four-view pilot does not establish the output distribution, failure rate, or cost of the complete TEST set. $20 appears plausible, but is not guaranteed: without retries, the uncached Standard-rate break-even output mean is approximately 2,194 tokens/request. If every request used the largest observed output count, the projection would already exceed $20. The existing runner caps attempts, not cumulative USD spend; full canonical execution still needs an explicit scope/budget decision.

## Independent verification and evidence

- Two offline mock checks passed, with `attempted_egress=0`: staged stopping/resume and the 80-attempt worst retry case. Mock outputs were kept separate from this live evidence.
- Preflight passed with real credentials present and zero provider calls; source SHA, config/protocol hash binding, DEV scope, and path safety were verified before dispatch.
- The actual run's journal, record checksums, source/config/protocol binding, exact 20-key membership, unique provider response IDs, ordered request/response timestamps, model identity, token usage, and zero-retry accounting were independently checked.
- Exact API-key byte scans of all published run files passed. Credentials and the runtime authorization token are not included.
- [Source-commit CI](https://github.com/habachcp6/RAG2ATTCK/actions/runs/36776110703): Windows/Ubuntu each 1,207 passed; frozen synthetic hash/reproduction mismatches zero.
- [Source-commit real retrieval integration](https://github.com/habachcp6/RAG2ATTCK/actions/runs/36776110809): 5 passed, zero egress.

The byte-preserved manifest, journal, five prediction JSONL files, run summary, derived DEV config/protocol, and calculated evidence summary are under [`evidence/dev_cost_pilot_20261001/`](evidence/dev_cost_pilot_20261001/). `summary.json` lists their SHA-256 checksums. To reconstruct the artifact root for offline auditing, use the executed source checkout, copy the 14 referenced source artifacts to a separate DEV root, place the published config under its `config/dev_experiment_config.json`, and place the run files under its `live-output/`. Validate journal/record bindings without resuming dispatch or scoring this incomplete matrix.
