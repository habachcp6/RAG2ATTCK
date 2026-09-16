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
  - Deterministic opaque record ID formula: `rec_{SHA256(file_sha256 + ':' + ordinal)[:16]}`.
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
Each CLI stage programmatically validates predecessor artifacts and hashes:
1. `preflight`: Standalone; produces `data/metadata/preflight.json` and `data/metadata/source_context.json`.
2. `acquire-attack`: Requires valid `preflight.json`. Produces `attack/raw/enterprise-v19.2/` and `data/metadata/attack_manifest.json`.
3. `acquire-dataset`: Requires valid `preflight.json`. Produces `data/raw/windows_apt_2025/v3/` and `data/metadata/dataset_manifest.json`.
4. `reconcile`: Requires `dataset_manifest.json`. Produces `data/metadata/reconciliation_log.json` and `data/audit/reconciliation_report.md`.
5. `profile`: Requires `dataset_manifest.json` and `reconciliation_log.json`. Produces `data/metadata/schema_profile.json`, `field_inventory.csv`, `record_index.csv`, `parse_error_ledger.json`.
6. `audit-gt`: Requires `schema_profile.json`, `field_inventory.csv`, `record_index.csv`. Produces `ground_truth_register.json`, `join_diagnostics.json`, `gate_blocker_task4.json`, `reports/ground_truth_provenance.md`, `reports/gate_blocker_task4.md`.
