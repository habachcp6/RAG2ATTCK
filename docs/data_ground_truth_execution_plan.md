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

---

## 5. Synthetic Paired Benchmark Protocol

### 5.1 Motivation

The Windows-APT pipeline is legitimately blocked at Task 4 (no independent ground truth). A **synthetic paired benchmark** generates controlled Windows endpoint telemetry with fully traceable ground truth established from template → evidence → annotation, bypassing the detector-rule dependency.

### 5.2 Design: Paired Single-Event / Contextual Views

Each **scenario instance** produces two views of the same anchor event:

- **Single-event view**: One anchor event only.
- **Contextual view**: The same anchor event plus 1–5 related events (total 2–6).

Ground truth is annotated **per-view independently**. A single view may legitimately be `ambiguous` while its contextual counterpart is `mapped`, reflecting the additional evidence available in context.

### 5.3 Attribution Rubric (Evidence-Conditioned Closed-World)

Ground-truth labels are benchmark reference annotations constructed under the RAG2ATTCK evidence-conditioned, closed-world attribution rubric and validated against the pinned MITRE ATT&CK catalog.

| Status | Definition |
|---|---|
| **Mapped** | Sufficient positive attribution evidence is present in the view for one or more techniques in the benchmark catalog. |
| **Unmapped** | The visible evidence affirmatively supports a benign/non-attributable interpretation under the closed-world eight-technique rubric. |
| **Ambiguous** | Neither the mapped threshold nor the unmapped threshold can be established from the visible evidence. |

> **Note**: Lack of evidence alone produces **ambiguous**, not unmapped.

### 5.4 Transition Policy (Benchmark v1)

Allowed single → contextual transitions:

| Single Status | Contextual Status | Type |
|---|---|---|
| mapped | mapped (same techniques) | Context confirms |
| mapped(n) | mapped(n+k techniques) | Context expands |
| ambiguous | mapped | Context resolves |
| ambiguous | unmapped | Context resolves negatively |
| ambiguous | ambiguous | Context insufficient |
| unmapped | unmapped | Context confirms benign |

**Disallowed in v1**: mapped→ambiguous, mapped→unmapped, unmapped→ambiguous, unmapped→mapped.

### 5.5 Quota (counted at pair / contextual-view level)

| Category | Test | Dev | Total |
|---|---:|---:|---:|
| Mapped single-label (8 techniques × 50) | 400 | 16 | 416 |
| Mapped multi-label | 40 | 4 | 44 |
| Unmapped | 150 | 6 | 156 |
| Ambiguous | 50 | 4 | 54 |
| **Total** | **640** | **30** | **670** |

### 5.6 ATT&CK Catalog (pinned to STIX v19.2)

`T1059.001`, `T1059.003`, `T1053.005`, `T1543.003`, `T1136.001`, `T1547.001`, `T1685.005`, `T1105`

All 8 techniques verified active (not revoked/deprecated) against pinned STIX snapshot.

### 5.7 Constraints

- **Determinism**: Seed `20260915`; `random.Random(seed)` per scenario, not global.
- **Providers**: Windows Security-Auditing, Windows Eventlog, and Sysmon.
- **Service install**: EID **4697** (Security-Auditing), not 7045 (Service Control Manager/System).
- **Safe indicators**: RFC 5737 IPs, `*.example.invalid` domains.
- **Near-duplicate detection**: Character 5-gram Jaccard ≥ 0.95.
- **Split**: Strict template-family holdout — DEV ∩ TEST template_family_id = ∅.
- **Family diversity**: `ceil(category_quota / num_eligible_families)` — no hard cap.
- **T1136.001 host constraint**: Workstation/member-server only; excluded from DC hosts.
- **No leakage**: Inference payload filtered by allowlist; no technique IDs, ground truth keywords.

### 5.8 Template Registry

Authoritative source: `config/synthetic_templates.json`.

Pipeline: registry → validator → generator → approval report → dataset.

- 64 semantic template families (52 test, 12 dev), with no provider/EventID or
  rationale placeholders
- Evidence predicates in structured DSL (eq, contains_ci, endswith_ci, all/any/not)
- Relation operands use enforced signatures (for example `process_then_file`
  requires process/file event keys; `temporal_before` requires before/after;
  `same_logon` requires an events list with logon identifiers)
- Canonical telemetry tuples: Security-Auditing/Security for EID 4688, 4697,
  4698, 4720; Eventlog/Security for EID 1102; Sysmon/Operational for EID 1,
  3, 11, 13
- EID 1102 is an audit-log-cleared outcome only; T1685.005 single views remain
  ambiguous unless mechanism evidence is visible in that view
- Registry hash verified for freeze integrity

### 5.9 Staged Execution

**Stage A** (prepare & approve):
1. Validate ATT&CK catalog against pinned STIX
2. Create template registry with structured evidence predicates
3. Build schema, registry semantic validator, dataset validator, and tests
4. Create human-review approval package
5. **STOP** → `STATUS: WAITING_FOR_HUMAN_APPROVAL`

**Stage B** (generate & freeze — only after explicit approval):
1. Lock approved templates via registry hash
2. Generate candidate pool from templates
3. Validate all 670 pairs
4. Near-duplicate audit
5. Verify dev/test split holdout
6. Manual spot-check audit
7. Freeze dataset
8. Reproduce from seed
9. Commit & push

### 5.10 Prerequisite Independence

The synthetic pipeline does **not** depend on Windows-APT Task 2 or Task 4 gates. It has its own prerequisite chain:
- `prepare-synthetic`: Requires valid `attack_manifest.json` (T5-acquire PASS).
- `validate-synthetic`: Requires prepared synthetic artifacts.
- `freeze-synthetic`: Requires validation PASS.
- `verify-synthetic`: Requires frozen dataset.

### 5.11 Source Modules

- `src/synthetic.py`: Data model, event builders, ID generation, serialization.
- `src/synthetic_validator.py`: registry semantic validation plus the dataset checks covering schema, quotas, transitions, leakage, host constraints, near-duplicates, and freeze integrity.
- `tests/test_synthetic.py`: Comprehensive test suite with positive and negative tests.
- `config/synthetic_templates.json`: Authoritative template registry (64 families).
