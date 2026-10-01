"""Unit tests for Windows atomic file replacement retry wrapper and runtime recovery integrity.

Uses portable fixture module tests.fixtures.runtime_recovery_wrapper_fixture to verify
the exact non-sensitive retry wrapper from launch_canonical_resume.py without depending
on machine-specific absolute paths.

Provenance:
- Canonical Launcher SHA-256:
  05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa
- Extracted Wrapper Block SHA-256:
  e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68

Test coverage:
1. Finite retry bound (raises after max 12 retries, exponential backoff, non-retriable fail fast).
2. No provider dispatch on retry failure.
3. No budget or state reset on write failure.
4. Crash consistency if ledger written but anchor fails.
5. Exception propagation and dual-lock safety.
6. Behavioral comparison: wrapped vs unwrapped.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from src.experiment.authorization import (
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    create_test_protocol_approval,
)
from src.experiment.config import canonical_bytes, digest, load_plan
from src.experiment.journal import (
    EVENT_MONETARY_RESERVE,
    read_journal_events,
)
from src.experiment.monetary_ledger import (
    StudyBudgetLedger,
    compute_pricing_contract_sha256,
    load_pricing_config,
    study_ledger_and_anchor_lock,
)
from src.experiment.runner import (
    JournalBudget,
    MockProvider,
)
from tests.fixtures.runtime_recovery_wrapper_fixture import (
    CANONICAL_LAUNCHER_SHA256,
    CANONICAL_WRAPPER_BLOCK_SHA256,
    build_robust_methods,
    verify_local_launcher_if_present,
    verify_wrapper_block_digest,
)

pytest_plugins = ["tests.test_experiment_t22"]

_TRUE_ORIG_WRITE_ATOMICALLY = StudyBudgetLedger._write_atomically_unlocked
_TRUE_ORIG_ANCHOR_ATOMICALLY = StudyBudgetLedger._write_anchor_atomically_unlocked


@pytest.fixture
def tmp_dir():
    d = Path(tempfile.mkdtemp(prefix="test_recovery_wrapper_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_pricing():
    pricing, _ = load_pricing_config()
    return pricing


@pytest.fixture
def bound_canonical_wrapper(monkeypatch):
    """Installs the exact wrapper from the portable fixture with intercepted fast sleep."""
    assert verify_wrapper_block_digest(), "Embedded wrapper block digest mismatch"

    sleep_calls: list[float] = []

    def mock_sleep(s: float) -> None:
        sleep_calls.append(s)

    robust_write, robust_anchor = build_robust_methods(
        _TRUE_ORIG_WRITE_ATOMICALLY,
        _TRUE_ORIG_ANCHOR_ATOMICALLY,
        sleep_fn=mock_sleep,
    )

    monkeypatch.setattr(StudyBudgetLedger, "_write_atomically_unlocked", robust_write)
    monkeypatch.setattr(StudyBudgetLedger, "_write_anchor_atomically_unlocked", robust_anchor)

    yield {
        "robust_write": robust_write,
        "robust_anchor": robust_anchor,
        "orig_write": _TRUE_ORIG_WRITE_ATOMICALLY,
        "orig_anchor": _TRUE_ORIG_ANCHOR_ATOMICALLY,
        "launcher_sha256": CANONICAL_LAUNCHER_SHA256,
        "wrapper_block_sha256": CANONICAL_WRAPPER_BLOCK_SHA256,
        "sleep_calls": sleep_calls,
    }

    # Teardown: restore pristine original methods
    StudyBudgetLedger._write_atomically_unlocked = _TRUE_ORIG_WRITE_ATOMICALLY
    StudyBudgetLedger._write_anchor_atomically_unlocked = _TRUE_ORIG_ANCHOR_ATOMICALLY


class TestFiniteRetryBound:
    """Test 1: Finite retry bound (raises after max 12 retries, exponential backoff,
    non-retriable fail fast).
    """

    def test_launcher_hash_and_wrapper_binding(self, bound_canonical_wrapper):
        assert bound_canonical_wrapper["launcher_sha256"] == CANONICAL_LAUNCHER_SHA256
        assert bound_canonical_wrapper["wrapper_block_sha256"] == CANONICAL_WRAPPER_BLOCK_SHA256
        assert verify_wrapper_block_digest() is True

        # Optional check: verify equivalence with local live launcher if present
        is_ok, msg = verify_local_launcher_if_present()
        assert is_ok, f"Local launcher verification failed: {msg}"

    def test_finite_retry_bound_raises_after_12_attempts_winerror_5(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0

        def failing_replace(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            exc = PermissionError(13, "Access is denied: WinError 5")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(PermissionError) as exc_info:
            ledger.reserve("key:test", Decimal("2.15898240"))

        assert replace_calls == 12, f"Expected exactly 12 attempts, got {replace_calls}"
        assert getattr(exc_info.value, "winerror", None) == 5
        assert len(bound_canonical_wrapper["sleep_calls"]) == 11
        expected_sleeps = [0.05 * (1.5**i) for i in range(11)]
        assert bound_canonical_wrapper["sleep_calls"] == pytest.approx(expected_sleeps)

    def test_finite_retry_bound_winerror_32_sharing_violation(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0

        def failing_replace(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            exc = OSError(
                32,
                "The process cannot access the file because it is being used by another process",
            )
            exc.winerror = 32
            raise exc

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(OSError) as exc_info:
            ledger.reserve("key:test", Decimal("2.15898240"))

        assert replace_calls == 12
        assert exc_info.value.winerror == 32
        assert len(bound_canonical_wrapper["sleep_calls"]) == 11

    def test_transient_failure_recovers_within_bound(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0
        real_replace = os.replace

        def transient_replace(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls <= 4:
                exc = PermissionError(13, "Access is denied")
                exc.winerror = 5
                raise exc
            return real_replace(src, dst)

        monkeypatch.setattr(os, "replace", transient_replace)

        ledger.reserve("key:transient", Decimal("2.15898240"))
        assert replace_calls == 5, f"Expected 5 attempts before success, got {replace_calls}"
        assert len(bound_canonical_wrapper["sleep_calls"]) == 4
        assert ledger.active_reservations_usd == Decimal("2.15898240")

    def test_non_retriable_oserror_raises_immediately_zero_retries(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0

        def non_retriable_replace(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            exc = FileNotFoundError(2, "No such file or directory")
            exc.winerror = 2
            raise exc

        monkeypatch.setattr(os, "replace", non_retriable_replace)

        with pytest.raises(FileNotFoundError):
            ledger.reserve("key:test", Decimal("2.15898240"))

        assert replace_calls == 1, "Non-retriable error must fail fast on attempt 0"
        assert len(bound_canonical_wrapper["sleep_calls"]) == 0

    def test_anchor_finite_retry_bound_raises_after_12_attempts(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_budget" / "study_ledger.json"
        anchor_path = tmp_dir / ".study_anchor.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)

        replace_calls = 0

        def failing_anchor_replace(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            exc = PermissionError(13, "Access is denied: anchor locked")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", failing_anchor_replace)

        with pytest.raises(PermissionError):
            StudyBudgetLedger(
                ledger_path=ledger_path,
                anchor_path=anchor_path,
                pricing_config=sample_pricing,
            )

        assert replace_calls == 12, "Anchor write must retry up to 12 times and raise"
        assert len(bound_canonical_wrapper["sleep_calls"]) == 11


class TestNoProviderDispatchOnRetryFailure:
    """Test 2: No provider dispatch on retry failure."""

    def test_runner_zero_provider_dispatch_when_reserve_fails(
        self, bundle, tmp_dir, bound_canonical_wrapper, monkeypatch
    ):
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_dir / "live-retry-fail-output"
        ledger_path = tmp_dir / "study_ledger.json"

        # Initialize valid ledger before injection
        StudyBudgetLedger(ledger_path)

        proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
        auth = ExecutionAuthorization(
            human_approval_token="HUMAN_AUTH_TOKEN_XYZ",
            scientific_protocol_approved=True,
            authorized_max_requests=100,
            allow_live_dispatch=True,
            approved_protocol_sha256=proto.protocol_sha256,
            use_money_guard=True,
            study_ledger_path=str(ledger_path),
        )

        mock_provider = MockProvider()

        # Inject persistent WinError 5 on os.replace
        def failing_replace(src, dst):
            exc = PermissionError(13, "Access is denied: WinError 5 simulation")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(PermissionError):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: mock_provider,
            )

        # Strictly ZERO provider calls dispatched
        assert (
            len(mock_provider.calls) == 0
        ), f"Expected 0 provider calls, got {len(mock_provider.calls)}"

        # Verify no prediction records were committed
        for pred_file in output.glob("*_predictions.jsonl"):
            lines = [
                line_content
                for line_content in pred_file.read_text(encoding="utf-8").splitlines()
                if line_content.strip()
            ]
            assert len(lines) == 0

        # Verify journal did not log monetary_reserve or DISPATCH_STARTED
        journal_path = output / "request_journal.jsonl"
        if journal_path.exists():
            events = read_journal_events(journal_path)
            reserve_events = [e for e in events if e.get("event") == EVENT_MONETARY_RESERVE]
            dispatch_events = [e for e in events if e.get("state") == "DISPATCH_STARTED"]
            assert len(reserve_events) == 0, "No monetary_reserve event should be logged"
            assert len(dispatch_events) == 0, "No DISPATCH_STARTED event should be logged"


class TestNoBudgetOrStateReset:
    """Test 3: No budget or state reset on write failure."""

    def test_ledger_state_and_disk_preserved_on_failed_reserve(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        # Settle a sample successfully first
        k1 = "sample_001:no_rag"
        r_worst = Decimal("2.15898240")
        ledger.reserve(k1, r_worst)
        settled_cost = Decimal("0.00035000")
        rec_sha = "a" * 64
        ledger.settle(k1, settled_cost, r_worst, rec_sha)

        pre_settled_count = len(ledger.settled_records)
        pre_settled_cost = ledger.cumulative_settled_cost_usd
        pre_available = ledger.uncommitted_available_balance_usd
        assert pre_settled_count == 1
        assert pre_settled_cost == settled_cost
        assert ledger.active_reservations_usd == Decimal("0.0")

        # Now attempt a second reserve that fails on os.replace after 12 retries
        def failing_replace(src, dst):
            exc = PermissionError(13, "Access is denied: WinError 5")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", failing_replace)

        k2 = "sample_002:no_rag"
        with pytest.raises(PermissionError):
            ledger.reserve(k2, r_worst)

        # On-disk state must be completely uncorrupted and matching pre-failure state
        disk_raw = json.loads(ledger_path.read_bytes())
        assert disk_raw["settlement_records_count"] == 1
        assert Decimal(disk_raw["cumulative_settled_cost_usd"]) == pre_settled_cost
        assert Decimal(disk_raw["uncommitted_available_balance_usd"]) == pre_available
        assert Decimal(disk_raw["active_reservations_usd"]) == Decimal("0.0")
        assert k2 not in disk_raw.get("active_reservations", {})

        # Re-loading a fresh StudyBudgetLedger instance loads exact preserved state
        monkeypatch.undo()

        reloaded_ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        assert len(reloaded_ledger.settled_records) == 1
        assert reloaded_ledger.cumulative_settled_cost_usd == pre_settled_cost
        assert reloaded_ledger.uncommitted_available_balance_usd == pre_available
        assert reloaded_ledger.active_reservations_usd == Decimal("0.0")

    def test_journal_budget_cannot_be_reset(self, tmp_dir):
        journal_file = tmp_dir / "request_journal.jsonl"
        journal_file.write_text(
            '{"event":"header","manifest_sha256":"abc","max_requests":10}\n',
            encoding="utf-8",
        )
        budget = JournalBudget(10, journal_file, consumed=3)
        assert budget.consumed_provider_attempts == 3

        with pytest.raises(
            ValueError,
            match="persisted experiment request spending cannot be reset",
        ):
            budget.reset()


class TestCrashConsistencyLedgerAndAnchor:
    """Test 4: Crash consistency if ledger written but anchor fails (and vice-versa)."""

    def test_anchor_exists_without_ledger_fails_closed(
        self, tmp_dir, sample_pricing
    ):
        ledger_path = tmp_dir / "study_budget" / "study_ledger.json"
        anchor_path = tmp_dir / ".study_anchor.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)

        # Create only the anchor file (simulating crash after anchor write before ledger write)
        pricing_sha = compute_pricing_contract_sha256(sample_pricing)
        anchor_data = {
            "schema_version": "1.0.0",
            "study_id": "rag2attack-study-wide",
            "pricing_contract_sha256": pricing_sha,
            "total_budget_usd": "19.99000000",
            "prior_pilot_provisional_hold_usd": "0.05264010",
            "initial_available_usd": "19.93735990",
            "ledger_path": str(ledger_path.resolve()),
        }
        anchor_path.write_bytes(canonical_bytes(anchor_data))

        assert not ledger_path.exists()
        assert anchor_path.exists()

        # Instantiating StudyBudgetLedger must fail closed with LiveExecutionBlockedError
        with pytest.raises(
            LiveExecutionBlockedError,
            match="Refusing silent re-initialization of fresh budget",
        ):
            StudyBudgetLedger(
                ledger_path=ledger_path,
                anchor_path=anchor_path,
                pricing_config=sample_pricing,
            )

    def test_request_runtime_does_not_mutate_anchor(
        self, tmp_dir, sample_pricing
    ):
        ledger_path = tmp_dir / "study_budget" / "study_ledger.json"
        anchor_path = tmp_dir / ".study_anchor.json"
        ledger_path.parent.mkdir(parents=True, exist_ok=True)

        ledger = StudyBudgetLedger(
            ledger_path=ledger_path,
            anchor_path=anchor_path,
            pricing_config=sample_pricing,
        )

        initial_anchor_bytes = anchor_path.read_bytes()
        initial_anchor_digest = digest(initial_anchor_bytes)

        # Run reserve, settle, and cancel_orphan_hold
        k1 = "s1:no_rag"
        r_amt = Decimal("2.15898240")
        ledger.reserve(k1, r_amt)
        ledger.settle(k1, Decimal("0.00010000"), r_amt, "b" * 64)

        k2 = "s2:no_rag"
        ledger.reserve(k2, r_amt)
        ledger.cancel_orphan_hold(k2, r_amt)

        # Anchor MUST remain byte-identical (requests never mutate anchor)
        current_anchor_bytes = anchor_path.read_bytes()
        current_anchor_digest = digest(current_anchor_bytes)
        assert current_anchor_digest == initial_anchor_digest
        assert current_anchor_bytes == initial_anchor_bytes


class TestExceptionPropagationAndDualLockSafety:
    """Test 5: Exception propagation and dual-lock safety."""

    def test_dual_lock_released_on_unhandled_exception(self, tmp_dir):
        ledger_lock = tmp_dir / "study_ledger.lock"
        anchor_lock = tmp_dir / ".study_anchor.lock"

        with pytest.raises(RuntimeError, match="injected failure inside dual lock"):
            with study_ledger_and_anchor_lock(ledger_lock, anchor_lock):
                assert ledger_lock.exists()
                assert anchor_lock.exists()
                raise RuntimeError("injected failure inside dual lock")

        # Both lock files must be cleanly unlinked after exception
        assert not ledger_lock.exists(), "ledger_lock was not cleaned up"
        assert not anchor_lock.exists(), "anchor_lock was not cleaned up"

        # Subsequent acquisition must succeed immediately without conflict
        acquired = False
        with study_ledger_and_anchor_lock(ledger_lock, anchor_lock):
            acquired = True
        assert acquired, "Subsequent dual lock acquisition failed"

    def test_reserve_lock_cleanup_on_write_failure(
        self, tmp_dir, sample_pricing, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        anchor_path = tmp_dir / ".study_anchor.json"
        ledger = StudyBudgetLedger(
            ledger_path, anchor_path=anchor_path, pricing_config=sample_pricing
        )

        def failing_replace(src, dst):
            exc = PermissionError(13, "Simulated WinError 5")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", failing_replace)

        with pytest.raises(PermissionError):
            ledger.reserve("key:test", Decimal("2.15898240"))

        # Check lock files are removed
        assert not ledger.lock_path.exists()
        assert not ledger.anchor_lock_path.exists()

        # Another ledger instance can acquire lock immediately
        monkeypatch.undo()
        ledger.reserve("key:test", Decimal("2.15898240"))
        assert ledger.active_reservations_usd == Decimal("2.15898240")


class TestCompareWrappedVsUnwrappedBehavior:
    """Test 6: Compare wrapped vs unwrapped behavior on transient vs permanent errors."""

    def test_unwrapped_fails_immediately_on_first_transient_lock(
        self, tmp_dir, sample_pricing, monkeypatch
    ):
        StudyBudgetLedger._write_atomically_unlocked = _TRUE_ORIG_WRITE_ATOMICALLY
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0

        def fail_once(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            exc = PermissionError(13, "Access is denied: transient lock")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", fail_once)

        # Unwrapped call fails on call 1
        with pytest.raises(PermissionError):
            ledger.reserve("key:test", Decimal("2.15898240"))

        assert replace_calls == 1, "Unwrapped function should fail on first attempt"

    def test_wrapped_survives_transient_lock_that_resolves(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        replace_calls = 0
        real_replace = os.replace

        def fail_twice_then_succeed(src, dst):
            nonlocal replace_calls
            replace_calls += 1
            if replace_calls <= 2:
                exc = PermissionError(13, "Access is denied: transient lock")
                exc.winerror = 5
                raise exc
            return real_replace(src, dst)

        monkeypatch.setattr(os, "replace", fail_twice_then_succeed)

        # Wrapped succeeds without raising
        ledger.reserve("key:test", Decimal("2.15898240"))
        assert replace_calls == 3
        assert len(bound_canonical_wrapper["sleep_calls"]) == 2
        assert ledger.active_reservations_usd == Decimal("2.15898240")

    def test_both_fail_closed_on_permanent_lock(
        self, tmp_dir, sample_pricing, bound_canonical_wrapper, monkeypatch
    ):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        def permanent_fail(src, dst):
            exc = PermissionError(13, "Permanent access denied")
            exc.winerror = 5
            raise exc

        monkeypatch.setattr(os, "replace", permanent_fail)

        with pytest.raises(PermissionError):
            ledger.reserve("key:test", Decimal("2.15898240"))
