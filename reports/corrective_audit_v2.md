# RAG2ATTCK Corrective Audit v2

- Date: 2026-09-16
- Workspace: `D:\RAG2ATT&CK`
- Starting HEAD recorded before work: `a8521b3faeb032b3650e63e7d40412b9078d8d91`
- Frozen methodology: `ORIGINAL_REQUEST.md`
- Critical preservation checks: root `README.md` must remain byte-for-byte unchanged; raw dataset files must remain immutable; T6-T11 must remain not run.

## Executive Determination

The corrected pipeline now enforces predecessor gates with artifact validators instead of filename checks.

Task 2 reconciliation remains unresolved:

- period CSV rows: 102,011
- `combined.csv` rows: 102,011
- exact matching row fingerprints: 36,674
- divergent row fingerprints: 65,337
- semantic/representation reconciliation: `RECONCILIATION_DIVERGENT`
- representation equivalence resolved: false
- unresolved non-equivalent cell differences: 15,713

Therefore the frozen methodology requires STOP at Task 2. Task 3 and Task 4 code paths were repaired and unit-tested, but their existing production artifacts are historical diagnostics, not valid current-stage outputs after the corrected T2 gate.

## Traceability Matrix

| Methodology requirement | Implementing code | Validation/test | Generated artifact | Actual status | Defect or gap |
|---|---|---|---|---|---|
| T0 validates workspace path containment, capacity, runtime, and source context | `src/dataset.py`; `src/artifacts.py::validate_preflight_artifact` | `tests/test_dataset.py`; `tests/test_artifact_gates.py` | `data/metadata/preflight.json`, `data/metadata/source_context.json` | PASS | Pre-existing metadata refresh changed timestamp/runtime path before this pass; validator now requires PASS content, not file existence. |
| T1 provides reproducible scaffold and enforceable gates | `src/data_ground_truth.py`; `src/artifacts.py` | `tests/test_artifact_gates.py` | CLI and config | PASS | Previous CLI checked only filenames. Fixed. |
| T2 acquisition preserves Windows-APT v3 and verifies hashes | `src/acquisition.py`; `src/artifacts.py::validate_dataset_manifest_artifact` | `tests/test_acquisition.py`; `tests/test_artifact_gates.py` | `data/metadata/dataset_manifest.json`; raw v3 files | PASS | Added validator coverage for corrupted raw bytes. |
| T2 reconciliation must not proceed on unresolved representation divergence | `src/reconcile.py`; `src/artifacts.py::validate_reconciliation_artifact` | `tests/test_reconciliation.py`; `tests/test_reconciliation_semantics.py`; `tests/test_artifact_gates.py` | `data/metadata/reconciliation_log.json`; `data/audit/reconciliation_report.md` | STOP | Fixed over-broad Excel-only explanation. Artifact now carries transformation taxonomy and unresolved count. |
| T3 record IDs use source hash plus logical record ordinal | `src/profiler.py` | `tests/test_profiler_invariants.py` | Production T3 artifacts not regenerated after corrected T2 STOP | CODE FIXED; NOT VALIDLY EXECUTABLE | Prior code used successfully parsed count, so malformed rows would renumber later records. Fixed and fixture-tested. |
| T3 distinguishes absent, empty, explicit null, and non-empty fields | `src/profiler.py` | `tests/test_profiler_invariants.py` | Production T3 artifacts not regenerated after corrected T2 STOP | CODE FIXED; NOT VALIDLY EXECUTABLE | Prior inventory collapsed these states. Fixed in code and fixture tests. |
| T3 handles quoted/multiline CSV records | `src/profiler.py` | `tests/test_profiler_invariants.py` | Production T3 artifacts not regenerated after corrected T2 STOP | CODE FIXED; NOT VALIDLY EXECUTABLE | Fixture added. |
| T3 documents observation unit, duplicates, and linkage fields | `src/profiler.py` | Code inspection plus fixture tests | Production T3 artifacts not regenerated after corrected T2 STOP | CODE FIXED; NOT VALIDLY EXECUTABLE | Observation unit is a Wazuh/OpenSearch indexed alert/telemetry record, not independent attack execution truth. |
| T4 evaluates evidence before decision and must be able to accept valid independent lineage | `src/ground_truth.py::evaluate_lineage_evidence`; `inspect_candidate_lineage_sources` | `tests/test_ground_truth.py` | Existing T4 reports annotated as historical | CODE FIXED; NOT VALIDLY EXECUTABLE | Prior code embedded `REJECTED` decisions directly in source rows. Fixed. |
| T4 rejects Wazuh-derived, scenario-wide, timestamp-only, and ambiguous lineage | `src/ground_truth.py` | `tests/test_ground_truth.py` | Existing T4 reports annotated as historical | CODE FIXED; NOT VALIDLY EXECUTABLE | Unit tests now separate decision logic from production conclusion. |
| T5-acquire pins Enterprise ATT&CK v19.2 and verifies immutable hash | `src/attack_loader.py`; `src/artifacts.py::validate_attack_manifest_artifact` | `tests/test_attack_loader.py`; `tests/test_artifact_gates.py` | `data/metadata/attack_manifest.json` | PASS | Added validator coverage for corrupted STIX artifact. |
| STOP/BLOCKED gates prevent downstream execution | `src/artifacts.py`; CLI calls in `src/data_ground_truth.py` | `tests/test_artifact_gates.py` | N/A | PASS | Downstream stages now fail on unresolved T2 and Task 4 STOP. |

## Defects Found and Repairs

1. CLI stages used file-existence checks for prerequisites.
   - Repair: added `src/artifacts.py` validators for schema/task/status/hash/source consistency and wired CLI stages through them.

2. `acquire-attack`, `profile`, and `audit-gt` did not enforce all intended predecessor gates.
   - Repair: `acquire-attack` requires T0; `profile` requires resolved T2; `audit-gt` requires resolved T2 plus validated T3 artifacts.

3. T2 explanation assumed Excel serialization was sufficient.
   - Repair: added cell-level semantic classifier and taxonomy. The corrected artifact still reports unresolved divergence.

4. T3 record ordinals used parsed-count order.
   - Repair: record ID generation now uses logical CSV row ordinal after the header.

5. T3 field profiling collapsed absent, empty, null, and non-empty states.
   - Repair: profiler now tracks these separately and adds duplicate/linkage/observation-unit metadata for future valid T3 runs.

6. T4 lineage audit encoded predetermined rejection outcomes.
   - Repair: candidate rows now expose evidence first; a separate decision function applies acceptance criteria and can return `ACCEPTED` on a valid synthetic independent-lineage fixture.

7. Existing reports claimed current T3/T4 status after a corrected T2 STOP.
   - Repair: older reports were annotated as historical; this report supersedes them.

## Task 2 Reconciliation Determination

The corrected reconciliation taxonomy in `data/metadata/reconciliation_log.json` reports:

| Transformation type | Count | Equivalent? |
|---|---:|:---:|
| `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | 69,352 | Yes |
| `BOOLEAN_CASE_EQUIVALENT` | 15,887 | Yes |
| `NUMERIC_PRECISION_OR_VALUE_LOSS` | 15,440 | No |
| `NUMERIC_FORMAT_EQUIVALENT` | 14,948 | Yes |
| `EXCEL_SERIAL_DATETIME_EQUIVALENT` | 11,282 | Yes |
| `EXCEL_SERIAL_DATETIME_MISMATCH` | 264 | No |
| `TEXT_VALUE_CHANGED` | 4 | No |
| `EXPLICIT_NULL_EMPTY_CHANGED` | 3 | No |
| `PERCENT_DECIMAL_EQUIVALENT` | 2 | Yes |
| `EXCEL_SERIAL_TIME_MISMATCH` | 2 | No |

Because non-equivalent differences remain, Task 2 is not resolved. The current production pipeline must STOP before Task 3.

## Task 3 Observation-Unit Determination

Task 3 production artifacts were not regenerated because the corrected T2 gate blocks T3. The repaired profiler determines the observation unit as one CSV row representing a Wazuh/OpenSearch indexed alert/telemetry record exported by the dataset. Evidence:

- rows carry `_id` and `_index`;
- rows carry Wazuh rule fields such as `_source.rule.id`, `_source.rule.description`, and `_source.rule.mitre.id`;
- many rows contain nested Windows/Sysmon telemetry under `_source.data.win.*`;
- rule-description frequency is not treated as proof of event, repeated alert, aggregate, or independent attack execution unit.

## Task 4 Corrected Lineage-Audit Result

Task 4 production execution is not valid under the corrected run because Task 2 stops first. The Task 4 logic is repaired and fixture-tested.

If a human later resolves or waives Task 2, the corrected lineage audit should be rerun. Based on historical diagnostics and the evidence scanner, the currently available v3 sources remain insufficient for independent event-level ground truth: Wazuh rule mappings are detector-derived, scenario and validation files are scenario-level, and no Caldera operation journals or ability execution logs are present in the frozen v3 snapshot.

## External Primary-Source Search

Primary sources checked:

| Source | URL / identifier | Version/date | Classification | Finding |
|---|---|---|---|---|
| Mendeley Data v3 | `https://data.mendeley.com/datasets/b8fmtzvpy8/3`, DOI `10.17632/b8fmtzvpy8.3` | v3, 2025-12-17 | official dataset snapshot | 21 files: 16 period CSVs, `combined.csv`, README, checksums, scenario manifest, validation summary. No independent execution-lineage artifact. |
| Mendeley public file API v3 | `https://data.mendeley.com/public-api/datasets/b8fmtzvpy8/files?folder_id=root&version=3` | v3 | official metadata inventory | File hashes match the preserved v3 catalog. |
| Data in Brief article | DOI `10.1016/j.dib.2026.112569`; local preserved full text under `data/audit/source_research/` | 2026 | documentation/scenario evidence | Describes Caldera, Wazuh, Sysmon, scenario coverage, validation summaries, and mapped telemetry; does not provide per-event execution lineage. |
| Cyber Science Lab dataset page | `https://cybersciencelab.com/datasets/windows-apt-2025/` | published February 2026 page | documentation only | Confirms 36 APT-inspired scenarios, Caldera emulation, Wazuh/Sysmon capture, and roughly 102,000 records; no event-lineage files are published there. |
| Mendeley Data v4 | `https://data.mendeley.com/datasets/b8fmtzvpy8/4`, DOI `10.17632/b8fmtzvpy8.4` | v4, published 2026-07-03 | official dataset inventory only | Public inventory still has 21 files. Only `README.md` and `checksums.sha256` changed versus v3; telemetry CSVs, `combined.csv`, `scenario_manifest.csv`, and `validation_summary.csv` retain the same public file IDs/hashes. No new lineage artifact appears in public inventory. |
| Wazuh ruleset / Caldera references | referenced by article/source text | external tool/framework docs | detector-derived or framework documentation | Useful for understanding Wazuh/Caldera, but not dataset-specific independent per-event ground truth. |

Windows-APT v4 may contain updated documentation in its README, but the public inventory does not show materially different provenance or execution-lineage resources. Inspecting/adopting v4 as a benchmark remains a separate human decision and was not done.

## Files Changed

- Added: `src/artifacts.py`
- Updated: `src/data_ground_truth.py`, `src/reconcile.py`, `src/profiler.py`, `src/ground_truth.py`
- Added tests: `tests/test_artifact_gates.py`, `tests/test_reconciliation_semantics.py`, `tests/test_profiler_invariants.py`
- Updated tests: `tests/test_ground_truth.py`
- Updated artifacts/reports/docs: `data/metadata/preflight.json`, `data/metadata/source_context.json`, `data/metadata/reconciliation_log.json`, `data/audit/reconciliation_report.md`, `docs/data_ground_truth_execution_plan.md`, `reports/ground_truth_provenance.md`, `reports/gate_blocker_task4.md`, `reports/repair_audit_report.md`, `reports/corrective_audit_v2.md`

## Tests Added or Changed

Added coverage for:

- corrupted prerequisite artifacts and hash validation;
- gate bypass attempts by filename-only artifacts;
- STOP propagation to downstream stages;
- resolved versus unresolved semantic reconciliation;
- logical ordinal stability with malformed CSV records;
- quoted/multiline CSV parsing;
- absent versus empty/null field state accounting;
- independent lineage ACCEPT case;
- detector-derived, scenario-wide, timestamp-only, and ambiguous lineage failures;
- ATT&CK immutable reference integrity.

Latest full-suite result during this pass: `49 passed`.

## T0-T5-Acquire Status After Re-evaluation

| Task | Status | Notes |
|---|---|---|
| T0 | PASS | Current preflight artifact validates as PASS. |
| T1 | PASS | Validators and CLI gate wiring now match the execution plan. |
| T2 acquisition | PASS | v3 raw files remain hash-verified through `dataset_manifest.json`. |
| T2 reconciliation | STOP | `RECONCILIATION_DIVERGENT`; unresolved non-equivalent cell differences remain. |
| T3 | NOT VALIDLY EXECUTABLE | Code repaired and tested; production run blocked by T2 STOP. Existing artifacts are historical. |
| T4 | NOT VALIDLY EXECUTABLE | Logic repaired and tested; production run blocked by T2 STOP. Existing Task 4 blocker is historical. |
| T5-acquire | PASS | ATT&CK v19.2 pinned hash/integrity validated. |
| T5-reconcile | NOT RUN | Blocked before T4/T5-reconcile. |
| T6-T11 | NOT RUN | No downstream artifacts generated. |

## Remaining Blockers

1. Task 2 unresolved representation discrepancies block valid Task 3+ execution.
2. Even if Task 2 is waived later, currently available v3 evidence still does not establish independent event-level ground truth.
3. Windows-APT v4 public inventory does not introduce visible lineage artifacts; reviewing the changed v4 README is a separate human decision and must not silently switch the benchmark.

## Exact Next Human Decision Required

Decide whether to preserve the frozen methodology and obtain corrected/source-author clarification for the unresolved `combined.csv` representation discrepancies, or explicitly waive/modify the Task 2 gate and authorize proceeding from the 16 period CSVs despite unresolved non-equivalent differences. Without that decision, the pipeline must remain stopped before Task 3.
