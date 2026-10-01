# Runtime Recovery & Integrity Audit Report (Phase S1)

**Auditor:** Subagent A — Runtime Recovery & Integrity Auditor  
**Conversation Handle:** `eeafba1b-8596-40b9-af66-73abb6c2ea59`  
**Dedicated Worktree:** `D:/RAG2ATTCK-worktrees/audit-recovery-s1`  
**Dedicated Branch:** `codex/s1-audit-recovery`  
**Base Commit (PRE_SHA):** `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`  
**Audit Policy:** Strictly ZERO live provider/API calls; zero modifications to `canonical-live-usd1999` or live outputs.  

---

## 1. Executive Summary

During the canonical live experiment execution on Windows (`run_id: live-66b94b1676bf46a9`), historical process **PID 14356** (Task `task-1215`) terminated prematurely with exit code `1` due to an unhandled `PermissionError: [WinError 5] Access is denied` during an atomic file replacement (`os.replace`) in `StudyBudgetLedger._write_atomically_unlocked`.

Subsequent investigation and resumption under **PID 50192** (Task `task-1264`) demonstrated:
1. **Zero Data Loss & Zero Duplication:** Exactly 225 completed sample-condition pairs (45 samples × 5 conditions) were committed to disk, reconciled against `request_journal.jsonl`, and settled in `study_ledger.json` with zero record loss, zero duplicate attempts, and zero active reservation leaks.
2. **Deterministic Resumption:** The runner's state reconstruction (`_resume_state`) accurately identified 225 settled keys, 0 orphan reservations, and 0 recoverable reservations, resuming smoothly at record 226 without budget drift.
3. **Robust Windows Locking Wrapper:** The native launcher wrapper in `launch_canonical_resume.py` (`SHA256: 05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`) implements a 12-attempt exponential backoff retry loop specifically handling Windows `WinError 5` (Access is denied) and `WinError 32` (Sharing violation).
4. **Portable Test Validation:** 16 isolated failure-injection unit tests were authored in `tests/test_runtime_recovery_wrapper.py`, backed by the portable fixture `tests/fixtures/runtime_recovery_wrapper_fixture.py`. All 16 tests pass with 100% success under the offline test runner (`scripts/run_offline_tests.py -m pytest`, `attempted_egress=0`).

---

## 2. Forensic Investigation of Task-1215 Termination

### 2.1 Historical Task Log Provenance

| Artifact / Task | Host Path | OS PID | Size | Creation Time (UTC) | Last Write Time (UTC) | SHA-256 Digest |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **`task-1215.log`** | `C:\Users\hahoa\.gemini\antigravity\brain\cd393b52-6d99-4f23-878e-7afbb7e0ecf9\.system_generated\tasks\task-1215.log` | 14356 | 1,829 B | 2026-10-01T19:28:35Z | 2026-10-01T19:46:17Z | `e7fcdfc8e44c1ce63b7e8b566866669500530f95bd3011a7d49f719beea87d58` |
| **`task-1264.log`** | `C:\Users\hahoa\.gemini\antigravity\brain\cd393b52-6d99-4f23-878e-7afbb7e0ecf9\.system_generated\tasks\task-1264.log` | 50192 | 333 B | 2026-10-01T19:48:36Z | 2026-10-01T19:48:46Z | `47835a53b5dccd7efb360931885613471df8137232cdd576cbf65ec5e8788c07` |

A sanitized machine-readable record is preserved in `reports/evidence/sanitized_historical_logs.json`. Both log files have been inspected and confirmed to contain **zero API keys, zero authentication tokens, and zero personal credentials**.

### 2.2 Strict Distinction: Observed Facts vs Hypothesized Causes

| Aspect | Status | Technical Details |
| :--- | :---: | :--- |
| **Callsite & Exact Error** | **PROVEN FACT** | `os.replace` at line 741 of `monetary_ledger.py` raised `PermissionError: [WinError 5] Access is denied` during `tmp_file.replace(self.ledger_path)`. |
| **Execution Boundary** | **PROVEN FACT** | Failed at `runner.py:1372` inside `study_ledger.reserve(key_str, R_logical_worst)` when attempting reservation for sample 46 (record 226). This was strictly prior to appending `monetary_reserve` to `request_journal.jsonl` (line 1378), prior to transitioning to `RESERVED` / `DISPATCH_STARTED` (lines 1388–1394), and prior to provider dispatch (line 1407). |
| **Ledger File State at Failure** | **PROVEN FACT** | Because `MoveFileExW` failed before target replacement, `study_ledger.json` was never overwritten or corrupted. The `.tmp` file was left orphaned, but `_write_atomically_unlocked` safely unlinks pre-existing `.tmp` files upon subsequent execution. |
| **Unwrapped Code Defect** | **PROVEN FACT** | In commit `80dbeb3`, `_write_atomically_unlocked` lacked retry tolerance for transient Windows file-system errors, treating an instantaneous `PermissionError` as fatal and propagating it to process termination (exit code 1). |
| **Hypothesis A: Parallel Reader Handle** | **UNPROVEN / HYPOTHESIZED** | Transcript step 1224 records subagent `177ee041-021f-4040-a812-def4e4d4ea8e` actively reading `study_ledger.json` to monitor progress around the time of failure. On Windows NT, standard file read operations opened without `FILE_SHARE_DELETE` (such as standard Python `open()`, PowerShell `Get-Content`, or CLI inspectors) prevent concurrent atomic replacement via `MoveFileExW`, generating WinError 5 (`ERROR_ACCESS_DENIED`) or WinError 32 (`ERROR_SHARING_VIOLATION`). In the absence of kernel-level handle tracing (ETW/Sysinternals Process Monitor), this remains a plausible hypothesis. |
| **Hypothesis B: OS Antivirus / Indexer Locks** | **UNPROVEN / HYPOTHESIZED** | Background services on Windows 11 (Windows Defender real-time scanning, Windows Search Indexer `SearchIndexer.exe`, or IDE file watchers) momentarily open newly modified files for metadata extraction or scanning, producing transient WinError 5/32 collisions lasting 10–500 ms. In the absence of kernel-level event tracing, this also remains an unproven hypothesis. |

---

## 3. Resumption & Accounting Analysis (Task-1264)

### 3.1 Historical Resume Boundary vs In-Flight Job Execution

It is essential to distinguish between the **frozen historical resume boundary** (at record 225 where task-1215 crashed and task-1264 resumed) and **dynamic in-flight supervisor snapshots** taken later while the resumed background job continued processing subsequent samples:

1. **Frozen Historical Resume Boundary (Sample 45 / Record 225):**
   - **Complete Events (`complete`):** Exactly **225** events in `request_journal.jsonl`.
   - **Provider Attempt Events (`attempt` / `attempt_receipt`):** Exactly **225** events (every request in the 225 prefix succeeded on attempt index 0).
   - **Settle Events (`monetary_settle`):** Exactly **225** events.
   - **Cumulative Settled Cost:** USD **0.22590550**.
   - **Active Reservations:** USD **0.00** (`active_reservations == {}`).
   - **Uncommitted Available Balance:** USD **19.71145440**.
   - **Last Journal Event at Boundary:** `monetary_settle` for sample 45, condition `rag_k10`.
   - **Resumed Request Accounting:** `spent = 225`.

2. **Subsequent In-Flight Snapshots (PID 50192 Ongoing Execution):**
   - Subsequent supervisor queries observed attempt ordinals advancing past 600 (e.g. ordinal 605 for sample 121 condition `rag_k10`).
   - These dynamic attempt counts occurred hours after successful resumption and must not be confused with the frozen resume state at the 225th record.

### 3.2 State Reconstruction (`_resume_state`) Verification

When `launch_canonical_resume.py` resumed under PID 50192, `_resume_state` performed full verification:
1. **Prediction Files:**
   - `no_rag_predictions.jsonl`: 45 valid records (including canary record `dabf60970aa5a18d93f95976aafdaeef2d747e24d9bcb7b13176e63e2edde034`).
   - `rag_k1_predictions.jsonl`: 45 valid records.
   - `rag_k3_predictions.jsonl`: 45 valid records.
   - `rag_k5_predictions.jsonl`: 45 valid records.
   - `rag_k10_predictions.jsonl`: 45 valid records.
   - Total records on disk: **225** records. Each record matched canonical manifest schema, ATT&CK registry v19.2 IDs, and corpus technique IDs.
2. **Journal Reconstruction:**
   - 225 complete request lifecycles: `monetary_reserve` $\rightarrow$ `RESERVED` $\rightarrow$ `DISPATCH_STARTED` $\rightarrow$ `attempt` $\rightarrow$ `attempt_receipt` $\rightarrow$ `RESPONSE_RECEIVED` $\rightarrow$ `PARSED` $\rightarrow$ `complete` $\rightarrow$ `monetary_settle`.
   - Active state at journal end: `active == None`, `active_state == None`.
   - `recoverable_reservation == None`, `orphan_reservation == None`.
3. **Monetary Settlement Verification:**
   - Every completed prediction matched an existing `monetary_settle` event in the journal with matching hash, cost, and refund.
   - Joined with `study_ledger.json`: Exactly 225 settled records present in `settled_records`.
   - Balance conservation invariant verified:
     $$\$19.99000000 - \$0.05264010\ (\text{pilot}) - \$0.22590550\ (\text{settled}) - \$0.00\ (\text{holds}) = \mathbf{\$19.71145440}$$
4. **Resumption Point:**
   - Resumption started cleanly at sample 46 (record 226).
   - Zero duplicate dispatches occurred. Zero attempts or reservations were lost.

---

## 4. Audit of the Native Launcher Wrapper

### 4.1 Launcher Identity & Integrity
- **Script Path:** `C:\Users\hahoa\.gemini\antigravity\brain\cd393b52-6d99-4f23-878e-7afbb7e0ecf9\scratch\launch_canonical_resume.py`
- **Whole File SHA-256 Digest:** `05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`
- **Extracted Wrapper Block SHA-256 Digest:** `e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68`
- **Portable Fixture Module:** `tests/fixtures/runtime_recovery_wrapper_fixture.py`

### 4.2 Wrapper Engineering Characteristics
1. **Targeted Exception Filtering:** Catches `PermissionError` and `OSError` only when `winerror in (5, 32)` or `isinstance(exc, PermissionError)`. Non-retriable exceptions (`FileNotFoundError`, `ValueError`, disk quota errors) fail fast immediately on attempt 0 without sleeping.
2. **Mathematically Bounded Exponential Backoff:**
   - Attempt sequence: 12 attempts maximum (indices 0 to 11).
   - Delays: $0.05 \times 1.5^i$ seconds for $i \in [0, 10]$.
   - Cumulative sleep duration: $\sum_{i=0}^{10} 0.05 \times 1.5^i \approx 8.55$ seconds.
   - *Latency Qualification:* While the retry iteration count and sleep intervals are strictly bounded by mathematical construction, the underlying OS filesystem call latency (e.g. storage I/O, filter driver responsiveness) is governed by operating system scheduling and cannot be strictly bounded.
3. **Fail-Closed Behavior:** On attempt 11 (the 12th iteration), the caught exception is re-raised via bare `raise`, unwinding through the dual-lock context manager and terminating safely without state corruption.

---

## 5. Failure-Injection Unit Test Suite

The test suite `tests/test_runtime_recovery_wrapper.py` was created to evaluate the wrapper and ledger invariants under simulated Windows failure conditions. To ensure portability across any development machine or CI runner, tests import the isolated fixture `tests.fixtures.runtime_recovery_wrapper_fixture` without hardcoded machine paths.

### 5.1 Test Results Matrix (16/16 PASSED)

| Test ID | Test Function | Target Property | Result |
| :--- | :--- | :--- | :---: |
| 1 | `test_launcher_hash_and_wrapper_binding` | Validates fixture SHA-256 matches canonical block; optional live launcher check | **PASSED** |
| 2 | `test_finite_retry_bound_raises_after_12_attempts_winerror_5` | Exactly 12 attempts on WinError 5, 11 backoff sleeps, re-raises | **PASSED** |
| 3 | `test_finite_retry_bound_winerror_32_sharing_violation` | Exactly 12 attempts on WinError 32 (sharing violation) | **PASSED** |
| 4 | `test_transient_failure_recovers_within_bound` | Survives 4 failures, succeeds on 5th attempt, updates hold | **PASSED** |
| 5 | `test_non_retriable_oserror_raises_immediately_zero_retries` | Non-retriable `winerror=2` fails fast on attempt 0 (0 sleeps) | **PASSED** |
| 6 | `test_anchor_finite_retry_bound_raises_after_12_attempts` | Anchor writer retries up to 12 times and raises | **PASSED** |
| 7 | `test_runner_zero_provider_dispatch_when_reserve_fails` | Strictly 0 provider dispatches, 0 prediction rows on reserve failure | **PASSED** |
| 8 | `test_ledger_state_and_disk_preserved_on_failed_reserve` | Disk ledger and memory state preserved uncorrupted on write failure | **PASSED** |
| 9 | `test_journal_budget_cannot_be_reset` | `JournalBudget.reset()` raises `ValueError` (cannot be reset) | **PASSED** |
| 10 | `test_anchor_exists_without_ledger_fails_closed` | Missing ledger fails closed (`LiveExecutionBlockedError`) | **PASSED** |
| 11 | `test_request_runtime_does_not_mutate_anchor` | Anchor digest remains byte-identical across requests | **PASSED** |
| 12 | `test_dual_lock_released_on_unhandled_exception` | Both lock files unlinked on exception; re-acquisition succeeds | **PASSED** |
| 13 | `test_reserve_lock_cleanup_on_write_failure` | Lock files released cleanly on write failure | **PASSED** |
| 14 | `test_unwrapped_fails_immediately_on_first_transient_lock` | Unwrapped method fails immediately on attempt 1 | **PASSED** |
| 15 | `test_wrapped_survives_transient_lock_that_resolves` | Wrapped method recovers on attempt 3 without process abort | **PASSED** |
| 16 | `test_both_fail_closed_on_permanent_lock` | Permanent failure fails closed under both modes | **PASSED** |

### 5.2 Offline Runner Output

```text
$ .venv\Scripts\python.exe scripts\run_offline_tests.py -m pytest tests\test_runtime_recovery_wrapper.py -v
============================= test session starts =============================
platform win32 -- Python 3.13.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\RAG2ATTCK-worktrees\audit-recovery-s1
plugins: anyio-4.15.1
collected 16 items

tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_launcher_hash_and_wrapper_binding PASSED [  6%]
tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_finite_retry_bound_raises_after_12_attempts_winerror_5 PASSED [ 12%]
tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_finite_retry_bound_winerror_32_sharing_violation PASSED [ 18%]
tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_transient_failure_recovers_within_bound PASSED [ 25%]
tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_non_retriable_oserror_raises_immediately_zero_retries PASSED [ 31%]
tests/test_runtime_recovery_wrapper.py::TestFiniteRetryBound::test_anchor_finite_retry_bound_raises_after_12_attempts PASSED [ 37%]
tests/test_runtime_recovery_wrapper.py::TestNoProviderDispatchOnRetryFailure::test_runner_zero_provider_dispatch_when_reserve_fails PASSED [ 43%]
tests/test_runtime_recovery_wrapper.py::TestNoBudgetOrStateReset::test_ledger_state_and_disk_preserved_on_failed_reserve PASSED [ 50%]
tests/test_runtime_recovery_wrapper.py::TestNoBudgetOrStateReset::test_journal_budget_cannot_be_reset PASSED [ 56%]
tests/test_runtime_recovery_wrapper.py::TestCrashConsistencyLedgerAndAnchor::test_anchor_exists_without_ledger_fails_closed PASSED [ 62%]
tests/test_runtime_recovery_wrapper.py::TestCrashConsistencyLedgerAndAnchor::test_request_runtime_does_not_mutate_anchor PASSED [ 68%]
tests/test_runtime_recovery_wrapper.py::TestExceptionPropagationAndDualLockSafety::test_dual_lock_released_on_unhandled_exception PASSED [ 75%]
tests/test_runtime_recovery_wrapper.py::TestExceptionPropagationAndDualLockSafety::test_reserve_lock_cleanup_on_write_failure PASSED [ 81%]
tests/test_runtime_recovery_wrapper.py::TestCompareWrappedVsUnwrappedBehavior::test_unwrapped_fails_immediately_on_first_transient_lock PASSED [ 87%]
tests/test_runtime_recovery_wrapper.py::TestCompareWrappedVsUnwrappedBehavior::test_wrapped_survives_transient_lock_that_resolves PASSED [ 93%]
tests/test_runtime_recovery_wrapper.py::TestCompareWrappedVsUnwrappedBehavior::test_both_fail_closed_on_permanent_lock PASSED [100%]

============================= 16 passed in 3.98s ==============================
OFFLINE_GUARD: installed=True attempted_egress=0
```

---

## 6. Audit Conclusion & Sign-Off

1. **Observed Failure Mechanism:** The termination of task-1215 was an unhandled `PermissionError: [WinError 5] Access is denied` during `os.replace` on Windows. The external agent holding the conflicting file handle remains unproven in the absence of kernel-level file handle tracing.
2. **Resumption Correctness:** Task-1264 resumed cleanly from disk state. Exactly 225 records were committed in the historical prefix, 0 records or attempts lost, 0 duplicate calls, and 0 active reservation leaks.
3. **Safety & Invariant Preservation:** The launcher retry wrapper successfully mitigates Windows transient locks while maintaining strict finite retry bounds, fail-closed exception propagation, and zero state corruption.
4. **Portability:** The test suite and fixture are fully portable, containing zero private machine paths, and runnable under offline guards in CI environments.
5. **Compliance:** Strictly zero live provider calls were made during this audit. All operations were performed in an isolated worktree.

---

## Appendix A: Sanitized Task Log Excerpts

### A.1 Task-1215 Terminal Failure Excerpt
```text
=== LAUNCHING CANONICAL RESUME (PID: 14356, stop_after=6399) ===
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100%|##########| 103/103 [00:00<00:00, 1842.67it/s]
Traceback (most recent call last):
  File "launch_canonical_resume.py", line 159, in <module>
    launch_resume(stop_after=st_after, dry_run=is_dry)
  File "launch_canonical_resume.py", line 124, in launch_resume
    summary = run_live_experiment(
        plan=plan,
        ...
        stop_after=stop_after,
    )
  File "src/experiment/runner.py", line 1372, in run_live_experiment
    study_ledger.reserve(key_str, R_logical_worst)
  File "src/experiment/monetary_ledger.py", line 808, in reserve
    self._write_atomically_unlocked()
  File "src/experiment/monetary_ledger.py", line 741, in _write_atomically_unlocked
    tmp_file.replace(self.ledger_path)
  File "pathlib/_local.py", line 780, in replace
    os.replace(self, target)
PermissionError: [WinError 5] Access is denied: 'D:\RAG2ATT&CK\artifacts\study_budget\study_ledger.tmp' -> 'D:\RAG2ATT&CK\artifacts\study_budget\study_ledger.json'
```

### A.2 Task-1264 Resume Startup Excerpt
```text
=== LAUNCHING CANONICAL RESUME (PID: 50192, stop_after=6399) ===
Loading weights: 100%|##########| 103/103 [00:00<00:00, 1903.06it/s]
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
```
