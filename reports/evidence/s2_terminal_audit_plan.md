# Phase S2 Terminal Audit Plan: Independent Canonical Validation Protocol (Revision 5)
**Document Version:** 5.0.0 (Codex Review Acceptance Hardening: Protected Baseline 22, Native Preloader, Terminal Proof)  
**Phase:** S2 Terminal Validation (PREPARATION COMPLETE — AWAITING RUNNER TERMINAL EXIT)  
**Auditor:** Independent Canonical Validator (Strictly READ-ONLY)  
**Branch:** `codex/s2-terminal-validator`  
**Target Git Commit:** `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`  
**Governing Protocol:** `experiment-protocol-v1.1` (`d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`)  
**Code Manifest:** `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4`  
**Pricing Contract:** `pricing-v1` (`4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565`)  
**Protected Baseline Inventory:** `artifacts/orchestration/integration_protected_baseline.json` (22 files verified)  
**Launcher Wrapper SHA-256:** `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`  
**Canary First Line Raw SHA-256:** `83351ad996f7d4d70910051f47f7a3d4c45a46259431dcf92e764dbf5d554770`  
**Canary Canonical Record Digest:** `dabf60970aa5a18d93f95976aafdaeef2d747e24d9bcb7b13176e63e2edde034`  

---

## 1. Executive Summary & Resolution of Codex Supervisor Reviews R2 & R3

This document defines the formal, immutable, read-only terminal audit protocol for Phase S2 of the RAG2ATTCK benchmark study. In accordance with Codex Supervisor reviews `FAIL VALIDATOR_IMPLEMENTATION_R2` and probe verdict `FAIL VALIDATOR_PROBE_R3`, the validator implementation, test infrastructure, and probe resistance have been hardened across 10 critical structural items:

1. **Resolution of Supervisor Probe Counterexample 1 (Fail-Closed Provenance & Launcher):**
   - The probe revealed that empty directories previously returned success because file checks were guarded by `if exists:`.
   - Now, provenance checks are strictly fail-closed: missing launcher files, missing canary files, missing canary records in `records_by_key`, or missing lockfile/artifacts immediately raise `AuditVerificationError`.
2. **Resolution of Supervisor Probe Counterexample 2 (Deep Ledger & Hash/Refund/Count Drift):**
   - The probe mutated `settlement_records_count = 999`, `record_sha256 = '0'*64`, and `refund_usd = '9.00000000'`.
   - Now, `audit_financial_ledger_and_tariffs` enforces:
     * `settlement_records_count` must be an integer and equal `len(records_by_key)`.
     * `record_sha256` in ledger must match computed record canonical digest and journal settle event.
     * `refund_usd` in ledger must match journal settle refund and satisfy the conservation equation $\text{refund} = \text{reservation} - \text{cost}$.
     * Every monetary amount must be finite, non-negative, and properly formatted.
3. **CLI Launcher Option & Production Terminal Proof Gates:**
   - Added CLI `--launcher-path` option to `scripts/audit_terminal_run.py`.
   - When `--is-production` is set, three terminal exit proof gates are enforced:
     * Lock release: `.run.lock`, `study_ledger.json.lock`, `.study_anchor.json.lock` must all be unlinked.
     * Clean exit summary: `run_summary.json` must exist, parse strictly, and have `complete: True` and `record_count: 6400`.
     * Mandatory launcher wrapper: `launcher_wrapper_path` must exist and match full 64-hex hash `05b60f05...`.
4. **Explicit Audit Seal Classification:**
   - Non-production (`is_production=False`): `"seal_type": "fixture_evaluation"`, `"fixture_only": True`, `"production_ready": False`.
   - Production (`is_production=True`): `"seal_type": "canonical-independent-validation-seal-v1"`, `"fixture_only": False`, `"production_ready": True`, requiring all 6,400 records and all 10 sealed artifacts.
5. **Native Ledger `has_breach` Semantics:**
   - Correctly handles native absence semantics from `StudyBudgetLedger._sync_to_disk_unlocked()`: absence is accepted as clean (`ledger.get("has_breach", False)`), and presence must be boolean `False` with `breached_records == {}`.
6. **Flattened Receipt Event Parsing:**
   - Accurately parses flattened receipt fields (`ordinal`, `attempt_index`, `status`, `input_tokens`, `output_tokens`, `cached_tokens`, `response_id`, `service_tier`) matching emitter `runner._on_attempt`.
7. **Strict `Decimal` Monetary Validation:**
   - Implemented `validate_finite_nonnegative_money()` rejecting boolean `False`, non-numeric strings, `NaN`, or infinite values.
8. **Comprehensive Unit Test Suite (19/19 Passing):**
   - Includes 2 dedicated counterexample tests reproducing the supervisor's exact probes (`test_audit_fails_on_missing_provenance_and_launcher` and `test_audit_fails_on_ledger_hash_refund_count_drift`).
9. **Offline Guard & Subprocess Egress Protection:**
   - Executed through `scripts/run_offline_tests.py` with `OFFLINE_GUARD` blocking network egress (`attempted_egress=0`, `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`).
10. **Strict Non-Mutating / Non-Locking Architecture:**
    - `StudyBudgetLedger` is NEVER instantiated in the validator. All balances, tariffs, and conservation equations are verified by read-only JSON parsing and independent native math, avoiding Windows file lock conflicts (`os.replace` `[WinError 5]`).

---

## 2. Core Audit Invariants

1. **STRICTLY READ-ONLY:** Zero modifications to live experiment state or live study files.
2. **ZERO LIVE CALLS:** Zero outbound provider dispatches.
3. **NO PREMATURE SCORING:** No evaluation or metric scoring on partial matrices.
4. **NO IN-FLIGHT ACCESS:** Do not poll or read active ledger/prediction files during execution (preventing Windows `os.replace` `[WinError 5]` locks).
5. **FAIL-CLOSED GATES:** Audit execution and canonical sealing occur ONLY after terminal state is authoritatively confirmed across all process, task, lock, and file integrity checks.

---

## 3. Terminal Pre-Conditions & Multi-Source Clean Exit Evidence

Process absence alone is **NOT** clean exit evidence. Terminal state must be independently corroborated across five distinct, authoritative sources:
1. **Authoritative Task State:** Orchestrator task-1264 reports terminal completion (`state == "DONE"`, exit code 0, without unhandled exceptions).
2. **Native Process Absence:** Native PID 50192 is confirmed absent from the Windows operating system process table (`Get-Process -Id 50192` fails with process not found).
3. **File Lock Release:** 
   - `artifacts/experiments/synthetic-paired-test-1/.run.lock` is unlinked.
   - `artifacts/study_budget/study_ledger.json.lock` is unlinked.
   - `.study_anchor.json.lock` is unlinked.
4. **Summary Post-Run State:** `run_summary.json` is inspected only **AFTER** the runner has exited. The audit verifies:
   - `"complete": true`
   - `"record_count": 6400`
   - `"execution_mode": "live"`
   - `"new_records"` is evaluated dynamically against the invocation delta (e.g. $6400 - 225 = 6175$ for task-1264 resume after task-1215), **NOT** hardcoded to 6399.
   - Active canary summary (1 record) is never used as terminal proof while the background process is running.
5. **Cardinal File Bounds:** All 5 prediction files are non-empty and together contain exactly 6,400 records.

---

## 4. Terminal Statuses & Failure Classification

The RAG2ATTCK evaluation taxonomy establishes that scientifically authentic model failures must be preserved as valid observed experimental outcomes. The audit distinguishes strictly between **Scientifically Valid Failure Outcomes** and **Integrity / Provenance Corruption**:

### A. Scientifically Valid Failure Outcomes (Allowed in Benchmark Records):
- `ParseStatus` taxonomy defined in `src.llm.schemas.ParseStatus`:
  1. `VALID`: Model returned valid JSON adhering to schema with known ATT&CK technique ID.
  2. `INVALID_ID`: Model returned valid JSON but with non-existent or retired ATT&CK ID.
  3. `MALFORMED_RESPONSE`: Model output could not be parsed as valid JSON.
  4. `REFUSAL`: Model explicitly refused to answer the prompt.
  5. `INCOMPLETE`: Generation truncated due to context/max token limit.
  6. `API_FAILURE`: Provider returned 5xx server error, bad gateway, or unrecoverable API error.
  7. `TIMEOUT`: Provider request exceeded timeout limit across all allowed retries.
- For failures (`API_FAILURE`, `TIMEOUT`), prompt/completion tokens may be `None` or 0; native tariff policy charges the attempt worst-case reservation (\$0.53974560) without violating integrity.
- These records are **NOT** discarded, filtered, or re-dispatched. They represent frozen scientific benchmark outcomes.

### B. Integrity & Provenance Corruption (Triggers Audit Failure):
- Unparseable JSON lines or non-standard constants (`NaN`, `Infinity`).
- Record hashes mismatching journal `complete` or `monetary_settle` hashes.
- Discrepancy between receipt tokens and record tokens on successful completions.
- Omission of test split view IDs or injection of view IDs outside the frozen split universe.

---

## 5. Chronological Multi-Receipt Financial Audit Contract

The audit validates the financial ledger using the frozen native function `calculate_request_cost_from_receipts` from `src.experiment.monetary_ledger`.
- **CRITICAL INVARIANT:** Do **NOT** instantiate `StudyBudgetLedger` directly (its constructor acquires locks and writes to disk!). The audit performs strictly read-only validation of `study_ledger.json` and `.study_anchor.json`.
- **Exact Function Signature:**
  ```python
  calculate_request_cost_from_receipts(
      attempts_consumed: int,
      receipts: list[dict[str, Any]],
      record: Any,
      pricing_config: dict[str, Any],
      *,
      tier: str = "default",
      expected_model: Optional[str] = None,
      most_recent_attempt_ordinal: Optional[int] = None,
  ) -> tuple[Decimal, bool, Optional[str]]
  ```
- **Audit Procedure per Logical Request `(sample_id, condition)`:**
  1. Collect **all chronological receipts** from `request_journal.jsonl` matching this key (preserving retries, attempt indices, statuses, cached tokens, and input/output tokens).
  2. Pass `attempts_consumed = len(receipts)`, `receipts = key_receipts`, `record = rec`, `pricing_config = pricing_data`, `tier = "default"`, `expected_model = "gpt-5.6-luna"`, `most_recent_attempt_ordinal = key_receipts[-1]["ordinal"]`.
  3. Compute `(cost, breach, reason)`.
  4. Assert `breach is False` and `reason is None`.
  5. Assert that journal `monetary_settle` event has `cost_usd == str(cost)` and `refund_usd == str(Decimal("2.15898240") - cost)`.
  6. Assert that `study_ledger.json["settled_records"][f"{sample_id}:{condition}"]` has `cost_usd == str(cost)`, matching `record_sha256`, and matching `refund_usd`.
- **Study-Wide Budget Conservation:**
  - $\text{cumulative\_settled\_cost\_usd} \le \$19.93735990\text{ USD}$ (\$19.99 total budget cap minus \$0.05264010 prior pilot hold).
  - $\text{active\_reservations} == \{\}$ (zero open holds).
  - $\text{active\_reservations\_usd} \in (\text{"0.00000000"}, \text{"0E-8"})$.
  - $\text{uncommitted\_available\_balance\_usd} == \lfloor \$19.99000000 - \$0.05264010 - \text{cumulative\_settled\_cost\_usd} \rfloor_{8\text{dp}}$.
  - `has_breach is False` and `breached_records == {}`.

---

## 6. Recovery-Aware Journal Lifecycle & Strict JSON Parsing

- **Strict JSON Parsing:** All files are parsed using `_strict_json_loads` (rejects duplicate keys, NaN, Inf).
- **Duplicate Prevention:** The audit **NEVER** silently overwrites events in a dictionary. It tracks seen keys in explicit sets and asserts uniqueness:
  - If a key appears more than once in `complete` events $\to$ Raise `AuditVerificationError`.
  - If a key appears more than once in `monetary_settle` events $\to$ Raise `AuditVerificationError`.
  - If an `attempt_index` appears more than once for a given request key $\to$ Raise `AuditVerificationError`.
- **Recovery Lifecycle Awareness:** Across multi-stage executions (canary $\to$ task-1215 $\to$ task-1264 resume), the journal contains transition events and potential recovery events (`monetary_cancel_orphan`, `monetary_cancel_hold`). The audit verifies that:
  - All attempt ordinals form a strictly contiguous sequence $1..N_{\text{attempts}}$.
  - Each completed record has a valid terminal chain (`complete` $\to$ `monetary_settle`).
  - No orphaned reservations remain open at terminal exit.
- **Allowed Journal Events:** Header, `monetary_reserve`, `transition`, `attempt`, `attempt_receipt`, `complete`, `monetary_settle`, `reservation_abandoned`, `monetary_cancel_orphan`, `monetary_cancel_hold`. Any unrecognized event raises `AuditVerificationError`.

---

## 7. Canary Separate Byte Representations & Artifact Inventory

The audit distinguishes between the two distinct byte representations of the canary sample:
1. **Canary First Line Raw SHA-256:**
   `83351ad996f7d4d70910051f47f7a3d4c45a46259431dcf92e764dbf5d554770`  
   (Computed over raw line 1 bytes including trailing `\n` in `no_rag_predictions.jsonl`).
2. **Canary Canonical Record Digest:**
   `dabf60970aa5a18d93f95976aafdaeef2d747e24d9bcb7b13176e63e2edde034`  
   (Computed via `digest(canonical_bytes(record.model_dump()))`).
3. **Artifact Integrity Verification:**
   - All 15 lock artifacts verified against `config/canonical_experiment_lock_v1.json`.
   - Protocol canonical digest: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`.
   - Core code manifest: `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4`.

---

## 8. Executable Terminal Audit Script & Offline Unit Tests

- **Production Script:** Implemented at [`scripts/audit_terminal_run.py`](scripts/audit_terminal_run.py).
- **Offline Unit Test Suite:** Implemented at [`tests/test_terminal_audit.py`](tests/test_terminal_audit.py).
- **Test Runner Guard:** Implemented at [`scripts/run_offline_tests.py`](scripts/run_offline_tests.py).
- **Test Coverage (39/39 Passed Cleanly):**
  1. `test_audit_passes_on_valid_fixture`: Verifies valid multi-sample flow.
  2. `test_audit_fails_on_duplicate_complete`: Asserts rejection of duplicate complete events.
  3. `test_audit_fails_on_duplicate_settle`: Asserts rejection of duplicate settle events.
  4. `test_audit_fails_on_duplicate_receipt`: Asserts rejection of duplicate attempt receipts.
  5. `test_audit_fails_on_orphan_reservation`: Asserts rejection of unclosed reservations in ledger.
  6. `test_audit_fails_on_secret_leak`: Asserts detection of leaked credential patterns.
  7. `test_audit_accepts_valid_failure_statuses`: Verifies acceptance of authentic failures (`REFUSAL`, `TIMEOUT`, `API_FAILURE`, `MALFORMED_RESPONSE`).
  8. `test_audit_fails_on_missing_test_view`: Asserts rejection when test views are missing.
  9. `test_audit_fails_on_budget_breach`: Asserts rejection if settled cost exceeds available funds.
  10. `test_native_ledger_without_has_breach_passes`: Asserts acceptance of native absence semantics for `has_breach`.
  11. `test_ledger_with_has_breach_true_fails`: Asserts rejection when ledger records `has_breach=True`.
  12. `test_ledger_with_non_bool_breach_fails`: Asserts rejection when `has_breach` is non-boolean (e.g. string `"false"`).
  13. `test_audit_fails_on_canary_canonical_digest_mismatch`: Asserts detection of drift in canonical record digest.
  14. `test_audit_fails_on_canary_firstline_hash_mismatch`: Asserts detection of drift in canary raw first line SHA-256.
  15. `test_audit_fails_on_launcher_hash_mismatch`: Asserts detection of drift in launcher wrapper script SHA-256.
  16. `test_generate_audit_seal_fails_on_missing_artifact`: Asserts fail-closed sealing if any of 10 target files is missing.
  17. `test_audit_fails_on_invalid_money_format`: Asserts rejection of boolean or non-finite monetary values.
  18. `test_audit_fails_on_missing_provenance_and_launcher`: Asserts rejection on empty provenance directory and missing launcher script (reproducing Supervisor Counterexample 1).
  19. `test_audit_fails_on_ledger_count_drift`: Asserts rejection on mutated `settlement_records_count`.
  20. `test_audit_fails_on_ledger_record_hash_drift`: Asserts rejection on mutated `record_sha256`.
  21. `test_audit_fails_on_ledger_refund_drift`: Asserts rejection on mutated `refund_usd`.
  22. `test_audit_fails_on_pilot_hold_drift`: Asserts rejection on mutated prior pilot hold balance.
  23. `test_protected_baseline_22_files_pass`: Asserts clean validation of all 22 protected baseline files, canonical protocol digest, and pricing hash.
  24. `test_protected_baseline_file_byte_mismatch`: Asserts fail-closed rejection on byte drift in any protected baseline file.
  25. `test_protocol_canonical_digest_mismatch`: Asserts fail-closed rejection on drift in canonical protocol digest.
  26. `test_production_rejects_active_lockfiles`: Asserts rejection when native locks (`study_ledger.lock`, `.study_anchor.lock`, `.run.lock`) exist.
  27. `test_production_rejects_mock_fixture_mode`: Asserts rejection if mock fixture mode or test fixtures are detected in production.
  28. `test_production_requires_terminal_proof_file`: Asserts mandatory `--terminal-proof-file` in production mode.
  29. `test_audit_terminal_process_proof_success`: Verifies authoritative verification and SHA-256 binding of terminal process proof.
  30. `test_audit_fails_on_reordered_journal_events`: Asserts rejection when journal events violate required sequential ordering (`attempt` -> `complete` -> `monetary_settle`).
  31. `test_generate_audit_seal_fails_on_missing_required_file`: Asserts seal generation failure if any required production file or baseline is missing.
  32. `test_terminal_proof_fails_on_missing_fields`: Asserts fail-closed rejection when any of the 8 required proof fields is missing.
  33. `test_terminal_proof_fails_on_running_status`: Asserts strict rejection if terminal proof indicates process is still running.
  34. `test_terminal_proof_fails_on_run_and_task_id_mismatch`: Asserts rejection on run_id or task_id drift.
  35. `test_positive_native_preloader_and_lifecycle`: Verifies end-to-end execution of native load_evaluation_inputs and _resume_state without mocks.
  36. `test_preloader_and_lifecycle_fails_on_header_max_requests_drift`: Asserts rejection when journal header max_requests differs from manifest cap.
  37. `test_preloader_and_lifecycle_fails_on_foreign_header`: Asserts rejection on tampered or foreign journal header.
  38. `test_preloader_and_lifecycle_fails_on_candidate_not_in_corpus`: Asserts rejection when retrieved candidates are absent from corpus.
  39. `test_preloader_and_lifecycle_fails_on_orphan_reservation`: Asserts rejection when unclosed reservations remain in journal.

---

## 9. Audit Seal Separation & Secret Sanitization Hygiene

- **Seal Manifest Separation:** The validator generates `reports/evidence/canonical_run_seal_v1.json` in its own private worktree directory. It does **NOT** write to or modify files in the live output directory. Original live files are preserved byte-for-byte.
- **No Self-Digest Loop:** The seal locks digests of live run artifacts (`manifest.json`, `run_summary.json`, `request_journal.jsonl`, 5 prediction files, `study_ledger.json`, `.study_anchor.json`), terminal proof file, and 22 protected baseline files; it does not hash itself.
- **Secret Sanitization Hygiene:**
  - Scans for regex patterns `sk-[a-zA-Z0-9_-]{20,}` and `Bearer\s+[a-zA-Z0-9_\-\.]{20,}`.
  - Logging reports match **COUNTS and FILE PATHS ONLY**, never logging matched secret text or token strings.

---

## 10. Handback Deliverables & S2 Execution Protocol

Upon authoritative notification of task-1264 clean terminal exit and explicit trigger `EXECUTE S2`:

```powershell
# 1. Assert Background Runner Process Absence
Get-Process -Id 50192 -ErrorAction SilentlyContinue

# 2. Run Comprehensive Terminal Audit via CLI (Read-Only)
$EXP_DIR = "artifacts/experiments/synthetic-paired-test-1"
$STUDY_ROOT = ".."
$PROOF_FILE = "reports/evidence/terminal_proof_task1264.json"
$BASELINE_PATH = "artifacts/orchestration/integration_protected_baseline.json"

python scripts/audit_terminal_run.py `
  --exp-dir "$EXP_DIR" `
  --study-root "$STUDY_ROOT" `
  --launcher-path "$STUDY_ROOT/scripts/run_experiments.py" `
  --protected-baseline-path "$BASELINE_PATH" `
  --terminal-proof-file "$PROOF_FILE" `
  --is-production
```

Or via direct Python API:
```python
import os
from pathlib import Path
from src.experiment.config import load_plan
from scripts.audit_terminal_run import (
    audit_completeness_and_cardinality,
    audit_financial_ledger_and_tariffs,
    audit_journal_join_and_lifecycle,
    audit_protected_baseline_22_files,
    audit_provenance_and_hash_invariants,
    audit_secret_sanitization,
    audit_terminal_process_proof,
    generate_audit_seal,
)

VAL_ROOT = Path(__file__).resolve().parent.parent if "__file__" in locals() else Path.cwd()
EXP_DIR = Path(os.environ.get("EXP_DIR", "artifacts/experiments/synthetic-paired-test-1"))
STUDY_ROOT = Path(os.environ.get("STUDY_ROOT", ".."))
SEAL_PATH = VAL_ROOT / "reports/evidence/canonical_run_seal_v1.json"
LAUNCHER_PATH = STUDY_ROOT / "scripts/run_experiments.py"
PROOF_PATH = Path(os.environ.get("TERMINAL_PROOF_FILE", "reports/evidence/terminal_proof.json"))
BASELINE_PATH = VAL_ROOT / "artifacts/orchestration/integration_protected_baseline.json"

plan = load_plan(VAL_ROOT / "config/experiment_config.json")
expected_ids = {s.sample_id for s in plan.samples}

# Run 22-protected baseline verification
baseline_info = audit_protected_baseline_22_files(BASELINE_PATH, VAL_ROOT)

# Run terminal process proof verification
proof_sha = audit_terminal_process_proof(PROOF_PATH)

records = audit_completeness_and_cardinality(EXP_DIR, expected_ids, require_all_conditions=True)
receipts, settles = audit_journal_join_and_lifecycle(EXP_DIR, records)
settled_usd, avail_usd = audit_financial_ledger_and_tariffs(STUDY_ROOT, VAL_ROOT, records, receipts, settles)
audit_provenance_and_hash_invariants(
    VAL_ROOT, EXP_DIR, records, launcher_wrapper_path=LAUNCHER_PATH, is_production=True
)
audit_secret_sanitization(
    list(EXP_DIR.glob("*.json")) + list(EXP_DIR.glob("*.jsonl")) + [
        STUDY_ROOT / ".study_anchor.json",
        STUDY_ROOT / "artifacts/study_budget/study_ledger.json",
    ]
)
seal = generate_audit_seal(
    EXP_DIR,
    STUDY_ROOT,
    VAL_ROOT,
    SEAL_PATH,
    records,
    settled_usd,
    avail_usd,
    is_production=True,
    terminal_proof_path=PROOF_PATH,
    protected_baseline_path=BASELINE_PATH,
)
print("TERMINAL AUDIT PASSED 100%. CANONICAL SEAL GENERATED.")
```

- **Deliverables Transmitted in Handback:**
  - Audit script: `scripts/audit_terminal_run.py`
  - Offline unit tests: `tests/test_terminal_audit.py` (39/39 passed)
  - Offline test runner: `scripts/run_offline_tests.py`
  - Plan document: `reports/evidence/s2_terminal_audit_plan.md`
  - Protected baseline inventory: `artifacts/orchestration/integration_protected_baseline.json` (22 files)
  - Audit seal destination: `reports/evidence/canonical_run_seal_v1.json`

