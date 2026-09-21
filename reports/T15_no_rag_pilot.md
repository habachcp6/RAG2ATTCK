# T15 — Small Real-Data No-RAG Pilot

## Status

**STATUS: PARTIAL / BLOCKED — DATA_UNAVAILABLE**

The repository does not currently contain an approved, legitimate sanitized
Windows endpoint telemetry source for the 20-sample pilot. The available
`data/ground_truth/synthetic/` benchmark and `data/synthetic/smoke_cases.jsonl`
are synthetic engineering/research artifacts and are not treated as real data.
No live API requests were made.

## Infrastructure delivered

- `src/pilot/no_rag_pilot.py` validates source provenance, loads bounded JSONL
  samples, calls the frozen `BaselinePipeline` with `condition="no_rag"` and
  `retrieved_context=None`, and records per-sample prediction/schema/error,
  latency, token and retry metadata.
- `tests/test_no_rag_pilot.py` covers provenance gating, duplicate/empty input
  rejection, no-context isolation, per-sample failure normalization and
  metadata preservation.
- `tests/test_pilot_hardening.py` exercises the actual client, budget, baseline
  pipeline and runner with injected providers, including internal-error
  propagation, direct-call limits, budget identity and immutable input snapshots.

## Pilot execution gates

The public runner validates the complete selected batch before dispatch. It
requires 1–20 unique samples with visible evidence and non-empty source IDs, plus
an explicit positive finite `LiveBudget` shared by identity with the client.
The process-global smoke budget is rejected. Request accounting must be enabled
even when a test injects a fake provider. The configured budget must not exceed
`selected_samples * (max_retries + 1)`; a smaller authorized budget may stop the
run early and is reported as incomplete. Each outbound attempt, including a
retry, consumes one unit in `LLMClient`; the runner never consumes another unit.

Only typed provider, connection, timeout and budget errors are normalized.
Programming errors (including `TypeError`), unsupported client interfaces and
filesystem errors propagate and stop the run. Provider errors retain the client's
identity and measured latency. If an operational error escapes the pipeline
without an execution record, its retry count is unknown (`null`), not fabricated
as zero. The summary reports the number of records with unknown retry counts
separately; `total_retries` sums known counts. A retry denied before dispatch is
not counted as an actual retry and leaves the pilot incomplete even when it is
the last selected sample. JSON decoding and schema validation catch only their expected exception
types; they do not mask defects in those implementations. Zero token usage is
preserved as zero.

## Snapshot provenance

`prepare_pilot_inputs` returns immutable `PilotInputs`: source JSONL bytes,
manifest bytes and selected samples. The input hash, record count and parsed
samples all refer to the same read. Source IDs and duplicate IDs are checked
across the input, including rows beyond the selected limit.

`capture_execution_snapshot` captures the model configuration and prompt bytes
before client construction. The CLI passes the captured configuration to
`LLMClient` and the captured prompt to `BaselinePipeline`; reporting never
reopens these files. The sidecar hashes these exact input, manifest, prompt and
configuration bytes, and records selected sample IDs, source/version, ATT&CK
version, captured repository SHA and budget/completion state. Files replaced
after capture cannot silently change the evidence or reported provenance.

The inference response remains the existing single `technique_id` schema and
uses the existing frozen prompt/model settings. These infrastructure changes do
not authorize provider dispatch, introduce real-data results or complete T15.

## Required source metadata

Before a live pilot can start, the source manifest must document all 11 canonical fields defined in `REQUIRED_SOURCE_FIELDS`:
- `dataset_id`
- `source_id`
- `source_reference`
- `license`
- `version`
- `acquisition_date`
- `schema`
- `sanitization_status`
- `is_real_data` (must be `true`)
- `input_sha256`
- `expected_record_count`

The manifest and source allowlist establish that source provenance is declared and integrity-checked (verifying declared source identity, expected source ID, exact input bytes SHA-256, expected record count, and recorded sanitization state); they do not independently prove source authenticity without an external verification mechanism. Raw telemetry must not be committed where licensing or privacy rules prohibit it; a manifest, hash and sanitized derived input are acceptable project artifacts.

## Execution boundary

The pilot must use the frozen model/prompt/schema configuration and the
existing finite request budget. It must not alter RAG behavior or make claims
about the primary benchmark. T15 must remain incomplete until both genuine
data and API access are available and the required tests/regression pass.
