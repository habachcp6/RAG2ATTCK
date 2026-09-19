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

## Required source metadata

Before a live pilot can start, the source manifest must document `source`,
`license`, `version`, `acquisition_date`, `schema`, `sanitization_status`, and
`is_real_data=true`. Raw telemetry must not be committed where licensing or
privacy rules prohibit it; a manifest, hash and sanitized derived input are
acceptable project artifacts.

## Execution boundary

The pilot must use the frozen model/prompt/schema configuration and the
existing finite request budget. It must not alter RAG behavior or make claims
about the primary benchmark. T15 must remain incomplete until both genuine
data and API access are available and the required tests/regression pass.
