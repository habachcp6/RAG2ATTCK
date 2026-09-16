# RAG2ATTCK Data & Ground Truth Execution Plan

## 1. Project Context & Frozen Research Methodology
This execution plan governs the Data & Ground Truth pipeline of **RAG2ATTCK** (`D:\RAG2ATT&CK`), evaluating MITRE ATT&CK-grounded retrieval-augmented generation (RAG) for technique-level attribution from Windows endpoint telemetry.

The research methodology specified in `ORIGINAL_REQUEST.md` is strictly frozen. No subagent or orchestrator may alter, relax, reinterpret, or replace the pipeline logic, task ordering, validation criteria, gate conditions, or evaluation units.

---

## 2. Dependency Graph & Gating Architecture

```
T0 ──→ T1 ──→ T2 ──→ T3 ──→ T4 ──┬──→ T6 ──→ T7 ──→ T8 ──→ T9 ──→ T10 ──→ T11
  │                                 │
  └──→ T5-acquire (parallel) ──────→ T5-reconcile ──┘
```

### Stage Summary & Gate Conditions:
- **T0 — Preflight**: Confirm workspace paths, Windows junction safety, disk capacity (free space >= max(estimate + 1 GiB, 5 GiB)), and runtime environment.
  - *Gate Condition*: Halt if paths uncontained, capacity insufficient, or source assets missing.
- **T1 — Scaffold & Reproducible Environment**: Local Git, pinned dependencies (`pyproject.toml`, `uv.lock`), structured config (`config/data_ground_truth.json`), staged CLI, and prerequisite enforcement.
- **T2 — Dataset Acquisition & Multiset Reconciliation**:
  - Download and verify Windows-APT 2025 v3 (`b8fmtzvpy8.3`) 21 files against Mendeley catalog SHA-256 hashes.
  - Strict file role separation: 16 period CSVs are ingest collections; `combined.csv` is reconciliation-only (never added to observations).
  - Multiset reconciliation: formal multiset comparison using canonical row representation.
  - *Gate Condition*: Halt on hash mismatch or unresolved representation discrepancies.
- **T3 — Schema Profiling, Observation Units & Record Indexing**:
  - Profile 16 period CSVs with quoted/multiline CSV parsing.
  - Strict parse accounting: `source_logical_rows = successfully_parsed_records + rejected_malformed_records`.
  - Deterministic opaque record ID formula: `rec_{SHA256(file_sha256 + ':' + logical_record_ordinal)[:16]}`.
  - The logical record ordinal is the 0-indexed CSV record ordinal after the header. A malformed logical record keeps its ordinal and must not renumber later valid observations.
  - Field profiling distinguishes schema-absent fields, present-but-empty fields, explicit null literals, and non-empty values.
  - Row-level deterministic index (`record_index.csv`) and parse error ledger (`parse_error_ledger.json`).
- **T4 — Verify Independent Event-Level Ground Truth**:
  - Independent lineage verification: inspect all candidate lineage sources (telemetry CSVs, scenario manifests, validation summaries, documentation, publication XML, timestamps, Caldera references).
  - Explicit rule: **Do NOT promote detector/rule mappings (`_source.rule.mitre.id`) or scenario lists to independent ground truth.**
  - *Gate Condition*: Halt immediately if independent event-level lineage is absent. Mark all downstream tasks (T5-reconcile, T6–T11) `NOT_RUN`.
- **T5-acquire — Enterprise ATT&CK Reference Acquisition**:
  - Pin Enterprise ATT&CK v19.2 to immutable Git commit SHA `6cda5ad8462c79e14fbb872f4e09059b18e0cfc4`.
  - Validate file size (`53835637` bytes) and expected SHA-256 (`dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`).
  - *Note*: `T5-reconcile` remains `NOT_RUN` while Task 4 is blocked.
- **T6–T11 — Downstream Pipeline (Currently NOT_RUN)**:
  - T6: Leakage audit & input policy.
  - T7: Sanitization, deduplication & grouping.
  - T8: Class selection & quota freeze before holdout.
  - T9: Partition & sampling manifests.
  - T10: Validation & clean reproduction.
  - T11: Full audit package & human approval (Decisions A & B).

---

## 3. Prerequisite Enforcement & Execution Guardrails
Each CLI stage programmatically validates predecessor artifacts and hashes through reusable validators in `src/artifacts.py`. A file with the expected name is not sufficient.
1. `preflight`: Standalone; produces `data/metadata/preflight.json` and `data/metadata/source_context.json`.
2. `acquire-attack`: Requires valid `preflight.json`. Produces `attack/raw/enterprise-v19.2/` and `data/metadata/attack_manifest.json`.
3. `acquire-dataset`: Requires valid `preflight.json`. Produces `data/raw/windows_apt_2025/v3/` and `data/metadata/dataset_manifest.json`.
4. `reconcile`: Requires valid `preflight.json` and a hash-verified `dataset_manifest.json`. Produces `data/metadata/reconciliation_log.json` and `data/audit/reconciliation_report.md`.
5. `profile`: Requires valid `preflight.json`, a hash-verified `dataset_manifest.json`, and a Task 2 reconciliation artifact whose exact or semantic/representation reconciliation is resolved. If `reconciliation_log.json` remains `RECONCILIATION_DIVERGENT` with unresolved discrepancies, this stage exits before generating T3 artifacts.
6. `audit-gt`: Requires the same resolved Task 2 gate plus validated `schema_profile.json`, `parse_error_ledger.json`, and `record_index.json`/`record_index.csv` hash integrity. It produces `ground_truth_register.json`, `join_diagnostics.json`, `gate_blocker_task4.json`, `reports/ground_truth_provenance.md`, and `reports/gate_blocker_task4.md` only after prerequisites pass.

## 4. Corrected Current-State Gate

The corrected Task 2 artifact currently reports:

- raw exact equality: false
- semantic/representation reconciliation: unresolved
- unresolved non-equivalent cell differences: 15,713
- gate result: `RECONCILIATION_DIVERGENT`

Therefore, for the current production workspace, Task 3 and Task 4 artifacts from earlier runs are retained only as historical diagnostics. They are not validly executable outputs of the corrected pipeline until a human decision resolves or waives the Task 2 discrepancy.
