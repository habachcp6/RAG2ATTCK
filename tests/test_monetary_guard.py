"""Comprehensive test suite for USD 20 study-wide monetary runtime guard and ledger."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from src.experiment.authorization import (
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    create_test_protocol_approval,
    protocol_to_dict,
)
from src.experiment.config import canonical_bytes, parse_jsonl
from src.experiment.journal import (
    EVENT_ATTEMPT_RECEIPT,
    EVENT_MONETARY_CANCEL_HOLD,
    EVENT_MONETARY_RESERVE,
    EVENT_MONETARY_SETTLE,
    EVENT_RESERVATION_ABANDONED,
    append_journal_event,
    read_journal_events,
)
from src.experiment.monetary_ledger import (
    StudyBudgetLedger,
    _strict_json_loads,
    calculate_attempt_token_cost,
    calculate_request_cost_from_receipts,
    get_canonical_study_ledger_path,
    load_pricing_config,
    resolve_study_root,
    study_ledger_lock,
)
from src.experiment.runner import MockProvider, MockReply, run_live_experiment
from src.llm.client import GLOBAL_LIVE_BUDGET, LLMClient
from src.retrieval.retriever import StubEmbedder

pytest_plugins = ["tests.test_experiment_t22"]


@pytest.fixture
def tmp_dir():
    d = Path(tempfile.mkdtemp(prefix="test_monetary_"))
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def sample_pricing():
    pricing, _ = load_pricing_config()
    return pricing


class TestProof1RootTempfileHardlink:
    """Proof 1: Hardlink external KEEP file to ledger.with_suffix(.tmp).

    Must fail closed and NEVER overwrite the external file.
    """

    def test_hardlink_tmp_file_rejected_without_overwriting(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        tmp_file = tmp_dir / "study_ledger.tmp"
        keep_file = tmp_dir / "CRITICAL_EXTERNAL_KEEP.txt"

        keep_file.write_text("CRITICAL_KEEP_DATA_DO_NOT_CORRUPT", encoding="utf-8")

        # Create hardlink from keep_file to tmp_file
        try:
            os.link(keep_file, tmp_file)
        except (AttributeError, OSError) as exc:
            pytest.skip(f"Hardlinks not supported on filesystem: {exc}")

        assert tmp_file.exists()
        assert tmp_file.stat().st_nlink > 1

        # Attempt to instantiate StudyBudgetLedger
        with pytest.raises(ValueError, match="hardlinked temporary file rejected"):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        # External file must NOT be modified or truncated
        assert keep_file.read_text(encoding="utf-8") == "CRITICAL_KEEP_DATA_DO_NOT_CORRUPT"

    def test_hardlink_ledger_path_rejected(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        keep_file = tmp_dir / "CRITICAL_KEEP.txt"
        keep_file.write_text("KEEP_CONTENT", encoding="utf-8")

        try:
            os.link(keep_file, ledger_path)
        except (AttributeError, OSError) as exc:
            pytest.skip(f"Hardlinks not supported: {exc}")

        with pytest.raises(ValueError, match="hardlinked ledger file rejected"):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        assert keep_file.read_text(encoding="utf-8") == "KEEP_CONTENT"


class TestProof2TamperedLedgerReload:
    """Proof 2: Settle cost 0.1, edit settled_records[a].cost_usd=0 leaving aggregate unchanged.

    Must fail closed on reload BEFORE any mutation or refund can occur.
    """

    def test_tampered_settled_records_cost_rejected_on_reload(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        key_a = "sample-1:no_rag"
        r_worst = Decimal("2.15898240")
        ledger.reserve(key_a, r_worst)
        cost_01 = Decimal("0.10000000")
        ledger.settle(key_a, cost_01, r_worst, "a" * 64)

        # Inspect raw JSON
        raw = json.loads(ledger_path.read_bytes())
        assert raw["cumulative_settled_cost_usd"] == "0.10000000"
        assert raw["settled_records"][key_a]["cost_usd"] == "0.10000000"

        # Tamper: edit only settled_records[key_a].cost_usd = "0.00000000"
        raw["settled_records"][key_a]["cost_usd"] = "0.00000000"
        ledger_path.write_bytes(json.dumps(raw).encode("utf-8"))

        # Reload must be rejected immediately
        with pytest.raises(ValueError, match="Cumulative settled cost mismatch"):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

    def test_tampered_active_reservations_rejected_on_reload(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        key_a = "sample-1:no_rag"
        ledger.reserve(key_a, Decimal("2.15898240"))

        raw = json.loads(ledger_path.read_bytes())
        raw["active_reservations"][key_a] = "1.00000000"  # tampered
        ledger_path.write_bytes(json.dumps(raw).encode("utf-8"))

        with pytest.raises(ValueError, match="Active reservations aggregate mismatch"):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

    def test_overlapping_active_and_settled_keys_rejected(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        key_a = "sample-1:no_rag"
        ledger.reserve(key_a, Decimal("2.15898240"))
        ledger.settle(key_a, Decimal("0.10000000"), Decimal("2.15898240"), "b" * 64)

        raw = json.loads(ledger_path.read_bytes())
        # Force duplicate key into active_reservations
        raw["active_reservations"][key_a] = "0.50000000"
        raw["active_reservations_usd"] = "0.50000000"
        raw["uncommitted_available_balance_usd"] = str(
            Decimal(raw["uncommitted_available_balance_usd"]) - Decimal("0.50000000")
        )
        ledger_path.write_bytes(json.dumps(raw).encode("utf-8"))

        with pytest.raises(ValueError, match="Integrity violation: keys"):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)


class TestStrictJsonParsing:
    """Strict JSON parsing tests: rejects non-standard constants (NaN, Inf) and duplicate keys."""

    def test_reject_duplicate_json_keys(self):
        dup_json = b'{"total": "20.0", "total": "30.0"}'
        with pytest.raises(ValueError, match="Duplicate JSON key rejected"):
            _strict_json_loads(dup_json)

    def test_reject_nonfinite_json_constants(self):
        nan_json = b'{"val": NaN}'
        with pytest.raises(ValueError, match="Non-standard JSON constant rejected"):
            _strict_json_loads(nan_json)

        inf_json = b'{"val": Infinity}'
        with pytest.raises(ValueError, match="Non-standard JSON constant rejected"):
            _strict_json_loads(inf_json)


class TestPricingConfigAndRootSeparation:
    """Pricing config comes from candidate execution tree (plan.root);
    ledger from stable Git common repo.
    """

    def test_pricing_config_from_code_root(self, tmp_dir, sample_pricing):
        fake_code_root = tmp_dir / "fake_repo"
        fake_config_dir = fake_code_root / "config"
        fake_config_dir.mkdir(parents=True)
        custom_pricing = dict(sample_pricing)
        custom_pricing["total_study_budget_usd"] = "25.00000000"
        (fake_config_dir / "pricing_v1.json").write_bytes(canonical_bytes(custom_pricing))

        loaded, digest_hex = load_pricing_config(repo_root=fake_code_root)
        assert loaded["total_study_budget_usd"] == "25.00000000"

    def test_ledger_anchored_to_study_root(self):
        study_root = resolve_study_root()
        canonical_path = get_canonical_study_ledger_path(study_root)
        assert canonical_path == study_root / "artifacts" / "study_budget" / "study_ledger.json"


class TestStudyWideBudgetPersistence:
    """Budget is study-wide, not reset per new output directory or process."""

    def test_balance_preserved_across_directories(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger1 = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        initial_available = ledger1.uncommitted_available_balance_usd
        assert initial_available == Decimal("19.93735990")

        # Reserve and settle in run 1
        ledger1.reserve("s1:no_rag", Decimal("2.15898240"))
        ledger1.settle("s1:no_rag", Decimal("0.50000000"), Decimal("2.15898240"), "c" * 64)

        # Process / run 2 opens the same ledger
        ledger2 = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        assert ledger2.cumulative_settled_cost_usd == Decimal("0.50000000")
        assert ledger2.uncommitted_available_balance_usd == (
            initial_available - Decimal("0.50000000")
        )


class TestSingleWriterLockRefusal:
    """Single-writer lock prevents concurrent mutations."""

    def test_concurrent_lock_refusal(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        lock_path = ledger_path.with_suffix(".lock")

        # Acquire lock in process 1
        with study_ledger_lock(lock_path):
            # Attempt to acquire lock in process 2
            with pytest.raises(
                ValueError, match="Study budget ledger is locked by another process"
            ):
                with study_ledger_lock(lock_path):
                    pass


class TestBudgetReinitRefusal:
    """Cannot silently re-initialize or tamper with budget totals."""

    def test_reinit_with_different_total_budget_fails(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        tampered_pricing = json.loads(json.dumps(sample_pricing))
        tampered_pricing["total_study_budget_usd"] = "50.00000000"

        with pytest.raises(
            ValueError, match="Pricing contract mismatch|Total study budget mismatch"
        ):
            StudyBudgetLedger(ledger_path, pricing_config=tampered_pricing)


class TestOverBudgetPrevention:
    """Over-budget prevention: zero calls when credit < logical worst reservation."""

    def test_insufficient_credit_blocks_dispatch(self, tmp_dir, sample_pricing):
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        # Artificially reserve almost all available credit
        # Available is 19.94735990. Reserve 18.00000000
        ledger.reserve("drain:no_rag", Decimal("18.00000000"))
        # Remaining available is 1.94735990 < 2.15898240
        assert ledger.uncommitted_available_balance_usd < Decimal("2.15898240")

        with pytest.raises(
            LiveExecutionBlockedError, match="LIVE_EXECUTION_BLOCKED: Insufficient study budget"
        ):
            ledger.reserve("next:no_rag", Decimal("2.15898240"))


class TestMultiAttemptRetryCostRetention:
    """3 timeouts retain worst charge $1.61923680, attempt 4 settles actual cost."""

    def test_three_timeouts_retain_worst_charge(self, sample_pricing):
        receipts = [
            {"attempt_index": 0, "status": "TIMEOUT", "service_tier": "default"},
            {"attempt_index": 1, "status": "TIMEOUT", "service_tier": "default"},
            {"attempt_index": 2, "status": "TIMEOUT", "service_tier": "default"},
            {
                "attempt_index": 3,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
                "cached_tokens": 0,
            },
        ]
        # 3 * 0.53974560 = 1.61923680
        # Attempt 4: input 1000 * 0.25 / 1M = 0.00025; output 500 * 1.20 / 1M = 0.00060 -> 0.00085
        # Total cost: 1.61923680 + 0.00085000 = 1.62008680
        record = SimpleNamespace(
            request_attempt_count=4,
            prompt_tokens=1000,
            completion_tokens=500,
        )
        cost, breach, _ = calculate_request_cost_from_receipts(
            attempts_consumed=4,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is False
        assert cost == Decimal("1.62008680")


class TestConservativeCacheWritePricing:
    """When cache fields absent, conservatively use cache-write price for all prompt tokens."""

    def test_missing_cache_tokens_uses_cache_write_tariff(self, sample_pricing):
        # 10,000 prompt tokens, 1,000 completion tokens, cached_tokens=None
        # Cache write tariff: 0.25 / 1M => 10,000 * 0.25 / 1M = 0.0025
        # Output tariff: 1.20 / 1M => 1,000 * 1.20 / 1M = 0.0012
        # Total: 0.0037
        cost = calculate_attempt_token_cost(
            prompt_tokens=10000,
            completion_tokens=1000,
            pricing_config=sample_pricing,
            cached_tokens=None,
            tier="default",
        )
        assert cost == Decimal("0.00370000")


class TestCeilingMismatchAndUnknownTier:
    """Unknown receipt/tier/token ceiling mismatch holds worst and blocks."""

    def test_output_ceiling_breach_holds_worst_and_flags_breach(self, sample_pricing):
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 9000,  # exceeds 8192 max_output_tokens
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=9000,
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert "exceeded ceiling" in reason
        assert cost == Decimal("0.53974560")

    def test_unknown_tier_holds_worst_and_flags_breach(self, sample_pricing):
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "auto",  # not default
                "input_tokens": 1000,
                "output_tokens": 500,
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=500,
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert "returned tier 'auto' mismatch with required 'default'" in reason
        assert cost == Decimal("0.53974560")


class TestCrashRecoveryEdgeCases:
    """Crash recovery proofs: complete-without-settle, orphan reserve, and in-flight fail-closed."""

    def test_complete_without_settle_recovery(self, tmp_dir, sample_pricing):
        """Simulation: Request completed (committed record exists), but crash before settle."""
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        key_str = "sample-1:no_rag"
        r_worst = Decimal("2.15898240")
        ledger.reserve(key_str, r_worst)

        # Reconstruct settlement directly
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
            }
        ]
        record = SimpleNamespace(request_attempt_count=1)
        cost, breach, _ = calculate_request_cost_from_receipts(
            1, receipts, record, sample_pricing, tier="default"
        )
        refund = ledger.settle(key_str, cost, r_worst, "d" * 64)
        assert refund == r_worst - cost
        assert ledger.cumulative_settled_cost_usd == cost

    def test_orphan_reserve_before_reserved_recovery(self, tmp_dir, sample_pricing):
        """Simulation: Reserve-only crash before RESERVED recorded in journal."""
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        key_str = "sample-1:no_rag"
        r_worst = Decimal("2.15898240")
        ledger.reserve(key_str, r_worst)

        assert ledger.active_reservations_usd == r_worst

        # Recovery cancels orphan hold
        ledger.cancel_orphan_hold(key_str, r_worst)
        assert ledger.active_reservations_usd == Decimal("0.00000000")
        assert ledger.uncommitted_available_balance_usd == Decimal("19.93735990")

    def test_offline_zero_egress(self):
        """Verify global live budget is untouched."""
        assert GLOBAL_LIVE_BUDGET.count == 0


class TestLiveExperimentMonetaryIntegration:
    """Full integration tests of run_live_experiment with StudyBudgetLedger and crash recovery."""

    def test_live_experiment_with_money_guard_lifecycle(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-output"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider()
        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
        )

        assert summary["complete"] is True
        assert "study_budget" in summary
        budget_summary = summary["study_budget"]
        assert budget_summary["service_tier"] == "default"
        assert Decimal(budget_summary["cumulative_settled_cost_usd"]) > Decimal("0.0")

        # Verify journal events
        journal_events = read_journal_events(output / "request_journal.jsonl")
        event_types = [e["event"] for e in journal_events]
        assert EVENT_MONETARY_RESERVE in event_types
        assert EVENT_ATTEMPT_RECEIPT in event_types
        assert EVENT_MONETARY_SETTLE in event_types

        # Verify ledger file on disk
        ledger = StudyBudgetLedger(ledger_path)
        assert ledger.active_reservations_usd == Decimal("0.00000000")
        assert ledger.cumulative_settled_cost_usd > Decimal("0.00000000")

    def test_live_experiment_repeated_execution_zero_cost(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-repeat"
        ledger_path = tmp_path / "study_ledger.json"

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

        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
        )

        ledger1 = StudyBudgetLedger(ledger_path)
        settled_before = ledger1.cumulative_settled_cost_usd

        # Rerun with resume=True
        summary2 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            resume=True,
        )

        assert summary2["new_records"] == 0
        ledger2 = StudyBudgetLedger(ledger_path)
        assert ledger2.cumulative_settled_cost_usd == settled_before

    def test_live_experiment_crash_recovery_complete_without_settle(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-crash-cws"
        ledger_path = tmp_path / "study_ledger.json"

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

        # Run 1 sample and stop
        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            stop_after=1,
        )

        # Tamper: remove the last monetary_settle event from journal
        journal_path = output / "request_journal.jsonl"
        events = read_journal_events(journal_path)
        settle_events = [e for e in events if e["event"] == EVENT_MONETARY_SETTLE]
        assert len(settle_events) == 1
        filtered_events = [e for e in events if e["event"] != EVENT_MONETARY_SETTLE]
        journal_path.unlink()
        for ev in filtered_events:
            append_journal_event(journal_path, ev)

        # Also reset the ledger so the key is in active_reservations rather than settled_records
        settled_key = f"{settle_events[0]['key'][0]}:{settle_events[0]['key'][1]}"
        r_worst = Decimal("2.15898240")
        raw_ledger = json.loads(ledger_path.read_bytes())
        del raw_ledger["settled_records"][settled_key]
        raw_ledger["active_reservations"][settled_key] = str(r_worst)
        raw_ledger["active_reservations_usd"] = str(r_worst)
        raw_ledger["cumulative_settled_cost_usd"] = "0.00000000"
        raw_ledger["settlement_records_count"] = 0
        raw_ledger["uncommitted_available_balance_usd"] = str(
            Decimal(raw_ledger["total_budget_usd"])
            - Decimal(raw_ledger["prior_pilot_provisional_hold_usd"])
            - r_worst
        )
        ledger_path.write_bytes(json.dumps(raw_ledger).encode("utf-8"))

        # Resume execution
        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            resume=True,
        )

        assert summary["complete"] is True
        ledger_resumed = StudyBudgetLedger(ledger_path)
        assert ledger_resumed.active_reservations_usd == Decimal("0.00000000")
        assert ledger_resumed.cumulative_settled_cost_usd > Decimal("0.00000000")

    def test_live_experiment_crash_recovery_recoverable_reservation(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-crash-rec"
        ledger_path = tmp_path / "study_ledger.json"

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

        # Run 1 sample and stop
        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            stop_after=1,
        )

        # Append monetary_reserve and transition RESERVED for next sample
        journal_path = output / "request_journal.jsonl"
        next_key = ["s1", "rag_k1"]
        next_key_str = "s1:rag_k1"
        r_worst = Decimal("2.15898240")

        ledger = StudyBudgetLedger(ledger_path)
        ledger.reserve(next_key_str, r_worst)

        append_journal_event(
            journal_path,
            {"event": EVENT_MONETARY_RESERVE, "key": next_key, "amount_usd": str(r_worst)},
        )
        append_journal_event(
            journal_path,
            {"event": "transition", "key": next_key, "state": "RESERVED"},
        )

        # Resume run
        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            resume=True,
        )

        assert summary["complete"] is True
        events = read_journal_events(journal_path)
        event_types = [e["event"] for e in events]
        assert EVENT_RESERVATION_ABANDONED in event_types
        assert EVENT_MONETARY_CANCEL_HOLD in event_types

    def test_live_experiment_in_flight_crash_fails_closed(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-in-flight"
        ledger_path = tmp_path / "study_ledger.json"

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

        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            stop_after=1,
        )

        # Tamper: simulate in-flight crash on next sample
        journal_path = output / "request_journal.jsonl"
        next_key = ["s1", "rag_k1"]
        append_journal_event(
            journal_path,
            {"event": "transition", "key": next_key, "state": "RESERVED"},
        )
        append_journal_event(
            journal_path,
            {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"},
        )
        append_journal_event(
            journal_path,
            {"event": "attempt", "key": next_key, "ordinal": 2},
        )

        with pytest.raises(
            ValueError, match="in-flight request state is ambiguous; human reconciliation required"
        ):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: MockProvider(),
                resume=True,
            )


class TestReturnedServiceTierHandling:
    """Capture RETURNED service_tier and reject/hold mismatch without tier substitution."""

    def test_mock_response_priority_tier_captured_and_flags_breach(self, sample_pricing):
        captured_receipts = []

        def callback(r):
            captured_receipts.append(r)

        mock_resp = SimpleNamespace(
            status="completed",
            output=[],
            output_text='{"technique_id":"T1059.001"}',
            refusal=None,
            service_tier="priority",
            model="gpt-5.6-luna",
            id="resp-123",
            usage=SimpleNamespace(
                input_tokens=100,
                output_tokens=50,
                input_tokens_details=SimpleNamespace(cached_tokens=0),
            ),
        )
        fake_client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: mock_resp)
        )
        client = LLMClient(
            config_dict={"model": "gpt-5.6-luna", "max_retries": 0},
            openai_client=fake_client,
            is_live=True,
            service_tier="default",
            attempt_callback=callback,
            registry_ids={"T1059.001"},
        )
        record = client.predict(sample_id="s1", endpoint_evidence="test prompt", condition="no_rag")
        assert len(captured_receipts) == 1
        rcpt = captured_receipts[0]
        assert rcpt["requested_service_tier"] == "default"
        assert rcpt["service_tier"] == "priority"

        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=captured_receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert "returned tier 'priority' mismatch with required 'default'" in reason
        assert cost == Decimal("0.53974560")


class TestRecordBindingIntegrity:
    """Receipt usage, model, and response ID binding to committed record."""

    def test_receipt_vs_record_usage_forgery_flags_breach(self, sample_pricing):
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 0,
                "output_tokens": 0,
                "response_id": "receipt-r",
                "model": "gpt-5.6-luna",
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=5000,
            completion_tokens=8192,
            response_id="record-r",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert "Token count mismatch" in reason or "Response ID mismatch" in reason
        assert cost == Decimal("0.53974560")

    def test_duplicate_receipt_indices_flags_breach(self, sample_pricing):
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 100,
                "output_tokens": 50,
            },
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 100,
                "output_tokens": 50,
            },
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=100,
            completion_tokens=50,
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert "Duplicate receipt for attempt_index 0" in reason
        assert cost == Decimal("0.53974560")

    def test_missing_receipt_identity_when_record_has_known_identity_flags_breach(
        self, sample_pricing
    ):
        """Record has known ID/model, but receipt has model=None/response_id=None.

        Must flag breach and retain full reservation (0.53974560), not token cost (0.00085000).
        """
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
                "model": None,
                "response_id": None,
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="KNOWN_PROVIDER_RESPONSE",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
        )
        assert breach is True
        assert cost == Decimal("0.53974560")
        assert "Missing receipt response_id" in reason or "missing model" in reason

    def test_missing_receipt_model_alone_flags_breach(self, sample_pricing):
        """Record has known model, but receipt has model=None."""
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
                "model": None,
                "response_id": "KNOWN_PROVIDER_RESPONSE",
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="KNOWN_PROVIDER_RESPONSE",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert cost == Decimal("0.53974560")
        assert "Missing receipt model" in reason

    def test_missing_receipt_response_id_alone_flags_breach(self, sample_pricing):
        """Record has known response_id, but receipt has response_id=None."""
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
                "model": "gpt-5.6-luna",
                "response_id": None,
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="KNOWN_PROVIDER_RESPONSE",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is True
        assert cost == Decimal("0.53974560")
        assert "Missing receipt response_id" in reason

    def test_mock_records_with_unknown_ids_retain_legacy_compatibility(self, sample_pricing):
        """Mock records where both response IDs are unknown retain legacy compatibility."""
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "service_tier": "default",
                "input_tokens": 1000,
                "output_tokens": 500,
                "model": "gpt-5.6-luna",
                "response_id": None,
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id=None,
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
        )
        assert breach is False
        assert cost == Decimal("0.00085000")

    def test_case_a_duplicate_ordinal_receipts_flags_breach_and_retains_worst(
        self, sample_pricing
    ):
        """Case A: Duplicate ordinals across attempts flag breach and retain full reservation.

        attempts=2, record prompt1000/completion500/modelLuna/id resp-final,
        receipts TIMEOUT idx0 ordinal1 + SUCCESS idx1 ordinal1 => must breach, cost 1.07949120.
        """
        receipts = [
            {
                "attempt_index": 0,
                "status": "TIMEOUT",
                "ordinal": 1,
            },
            {
                "attempt_index": 1,
                "status": "SUCCESS",
                "ordinal": 1,
                "input_tokens": 1000,
                "output_tokens": 500,
                "service_tier": "default",
                "model": "gpt-5.6-luna",
                "response_id": "resp-final",
            },
        ]
        record = SimpleNamespace(
            request_attempt_count=2,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="resp-final",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=2,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
        )
        assert breach is True
        assert cost == Decimal("1.07949120")
        assert "Duplicate receipt ordinal" in reason or "Non-sequential" in reason

    def test_case_b_success_before_final_retry_flags_breach_and_retains_worst(
        self, sample_pricing
    ):
        """Case B: SUCCESS before final attempt flags breach and retains full reservation.

        attempts=2, record prompt1000/completion500/modelLuna/id resp-final,
        receipts SUCCESS idx0 ordinal1 + SUCCESS idx1 ordinal2 => must breach, cost 1.07949120.
        """
        receipts = [
            {
                "attempt_index": 0,
                "status": "SUCCESS",
                "ordinal": 1,
                "response_id": "resp-earlier",
                "model": "gpt-5.6-luna",
                "input_tokens": 1000,
                "output_tokens": 500,
                "service_tier": "default",
            },
            {
                "attempt_index": 1,
                "status": "SUCCESS",
                "ordinal": 2,
                "response_id": "resp-final",
                "model": "gpt-5.6-luna",
                "input_tokens": 1000,
                "output_tokens": 500,
                "service_tier": "default",
            },
        ]
        record = SimpleNamespace(
            request_attempt_count=2,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="resp-final",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=2,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
        )
        assert breach is True
        assert cost == Decimal("1.07949120")
        assert "Attempt 0 has status 'SUCCESS' before final attempt" in reason

    def test_genuine_3_timeouts_1_success_nonzero_globalstart_control(
        self, sample_pricing
    ):
        """Control: Genuine 3 timeouts + 1 success with nonzero globalstart must not breach.

        globalstart=10, ordinals=[11, 12, 13, 14], cost=3*worst + token_cost = 1.62008680.
        """
        receipts = [
            {"attempt_index": 0, "status": "TIMEOUT", "ordinal": 11},
            {"attempt_index": 1, "status": "TIMEOUT", "ordinal": 12},
            {"attempt_index": 2, "status": "TIMEOUT", "ordinal": 13},
            {
                "attempt_index": 3,
                "status": "SUCCESS",
                "ordinal": 14,
                "input_tokens": 1000,
                "output_tokens": 500,
                "model": "gpt-5.6-luna",
                "response_id": "resp-final",
                "service_tier": "default",
            },
        ]
        record = SimpleNamespace(
            request_attempt_count=4,
            prompt_tokens=1000,
            completion_tokens=500,
            model="gpt-5.6-luna",
            response_id="resp-final",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=4,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
            most_recent_attempt_ordinal=14,
        )
        assert breach is False
        assert cost == Decimal("1.62008680")
        assert reason is None

    def test_root_offline_record_incomplete_status_settles_without_breach(
        self, sample_pricing
    ):
        """Offline record with parse_status=INCOMPLETE settles metered tokens without breach.

        Record: model=gpt-5.6-luna, id=resp-incomplete, prompt=1000, completion=8192,
        parse_status=INCOMPLETE, attempts=1.
        Receipt: idx0, ordinal=1, status=INCOMPLETE, tokens=1000/8192, default tier, Luna.
        Must not breach, and settles exact token cost Decimal('0.01008040').
        """
        receipts = [
            {
                "attempt_index": 0,
                "ordinal": 1,
                "status": "INCOMPLETE",
                "input_tokens": 1000,
                "output_tokens": 8192,
                "service_tier": "default",
                "model": "gpt-5.6-luna",
                "response_id": "resp-incomplete",
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=8192,
            response_id="resp-incomplete",
            model="gpt-5.6-luna",
            parse_status="INCOMPLETE",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
            most_recent_attempt_ordinal=1,
        )
        assert breach is False
        assert cost == Decimal("0.01008040")
        assert reason is None

    def test_incomplete_status_before_final_retry_flags_breach_and_retains_worst(
        self, sample_pricing
    ):
        """Returned INCOMPLETE response before final attempt flags breach and retains worst.

        Attempt 0: status=INCOMPLETE (returned response), ordinal=1.
        Attempt 1: status=SUCCESS, ordinal=2.
        Since non-final returned responses cannot be genuine before retry, must breach.
        """
        receipts = [
            {
                "attempt_index": 0,
                "ordinal": 1,
                "status": "INCOMPLETE",
                "input_tokens": 1000,
                "output_tokens": 8192,
                "service_tier": "default",
                "model": "gpt-5.6-luna",
                "response_id": "resp-inc-earlier",
            },
            {
                "attempt_index": 1,
                "ordinal": 2,
                "status": "SUCCESS",
                "input_tokens": 1000,
                "output_tokens": 500,
                "service_tier": "default",
                "model": "gpt-5.6-luna",
                "response_id": "resp-final",
            },
        ]
        record = SimpleNamespace(
            request_attempt_count=2,
            prompt_tokens=1000,
            completion_tokens=500,
            response_id="resp-final",
            model="gpt-5.6-luna",
            parse_status="VALID",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=2,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
            most_recent_attempt_ordinal=2,
        )
        assert breach is True
        assert cost == Decimal("1.07949120")
        assert "Attempt 0 has status 'INCOMPLETE' before final attempt" in reason

    def test_incomplete_with_unknown_tokens_retains_worst(self, sample_pricing):
        """Unknown token usage on INCOMPLETE receipt retains worst-case reservation."""
        receipts = [
            {
                "attempt_index": 0,
                "ordinal": 1,
                "status": "INCOMPLETE",
                "input_tokens": None,
                "output_tokens": None,
                "service_tier": "default",
                "model": "gpt-5.6-luna",
                "response_id": "resp-incomplete",
            }
        ]
        record = SimpleNamespace(
            request_attempt_count=1,
            prompt_tokens=1000,
            completion_tokens=8192,
            response_id="resp-incomplete",
            model="gpt-5.6-luna",
            parse_status="INCOMPLETE",
        )
        cost, breach, reason = calculate_request_cost_from_receipts(
            attempts_consumed=1,
            receipts=receipts,
            record=record,
            pricing_config=sample_pricing,
            tier="default",
            expected_model="gpt-5.6-luna",
            most_recent_attempt_ordinal=1,
        )
        assert breach is True
        assert cost == Decimal("0.53974560")
        assert "Token count mismatch" in reason


class TestCanonicalProductionStudyLedgerOverrideRejection:
    """Production live execution rejects custom study_ledger_path overrides."""

    def test_production_rejects_custom_study_ledger_path(self, bundle, tmp_path, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-canonical")
        from src.experiment.config import load_plan

        plan = load_plan(bundle[1])
        output = tmp_path / "prod-output"
        proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
        auth = ExecutionAuthorization(
            human_approval_token="HUMAN_AUTH_TOKEN_XYZ",
            scientific_protocol_approved=True,
            authorized_max_requests=100,
            allow_live_dispatch=True,
            approved_protocol_sha256=proto.protocol_sha256,
            study_ledger_path=str(tmp_path / "custom_ledger.json"),
        )

        with pytest.raises(
            LiveExecutionBlockedError,
            match="Custom study_ledger_path is not permitted in canonical production execution",
        ):
            run_live_experiment(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=None,
            )


class TestCleanUsdExhaustionAndSummary:
    """Clean USD exhaustion writes honest complete=false stopped_reason=USD_BUDGET_LIMIT summary."""

    def test_clean_usd_exhaustion_zero_calls_on_exhausted_start(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-exhaust-zero"
        ledger_path = tmp_path / "study_ledger.json"

        ledger = StudyBudgetLedger(ledger_path)
        ledger.reserve("dummy:hold1", Decimal("17.80000000"))
        assert ledger.uncommitted_available_balance_usd < Decimal("2.15898240")

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

        provider = MockProvider()
        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
        )

        assert summary["complete"] is False
        assert summary["stopped_reason"] == "USD_BUDGET_LIMIT"
        assert summary["record_count"] == 0
        assert summary["requests_consumed"] == 0
        assert len(provider.calls) == 0

        summary_disk = json.loads((output / "run_summary.json").read_bytes())
        assert summary_disk["complete"] is False
        assert summary_disk["stopped_reason"] == "USD_BUDGET_LIMIT"

    def test_clean_usd_exhaustion_after_committed_sample(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-money-guard-exhaust-partial"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider()
        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            stop_after=1,
        )

        # Drain remaining available balance below 2.15898240
        ledger = StudyBudgetLedger(ledger_path)
        avail = ledger.uncommitted_available_balance_usd
        drain = avail - Decimal("1.00000000")
        ledger.reserve("dummy:drain", drain)
        assert (
            ledger.uncommitted_available_balance_usd
            == Decimal("1.00000000") < Decimal("2.15898240")
        )

        calls_before = len(provider.calls)
        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            resume=True,
        )

        assert summary["complete"] is False
        assert summary["stopped_reason"] == "USD_BUDGET_LIMIT"
        assert summary["record_count"] == 1
        assert summary["requests_consumed"] == 1
        assert len(provider.calls) == calls_before


class TestCliHistoricalCountsReporting:
    """CLI live and resume report accurate historical counts rather than fabricated 0/0."""

    def test_cli_live_clean_usd_stop_returns_honest_summary(self, bundle, tmp_path, capsys):
        from src.experiment.__main__ import main as cli_main

        output_dir = tmp_path / "cli-usd-stop"
        ledger_path = tmp_path / "study_ledger.json"

        ledger = StudyBudgetLedger(ledger_path)
        ledger.reserve("dummy:all", Decimal("18.00000000"))

        proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
        proto_file = tmp_path / "protocol.json"
        proto_file.write_bytes(canonical_bytes(protocol_to_dict(proto)))

        argv = [
            "live",
            "--config", str(bundle[1]),
            "--output-dir", str(output_dir),
            "--auth-token", "HUMAN_TOKEN",
            "--protocol-file", str(proto_file),
            "--allow-live-dispatch",
            "--max-attempts", "100",
            "--use-money-guard",
            "--study-ledger-path", str(ledger_path),
        ]
        with (
            patch(
                "src.experiment.monetary_ledger.get_canonical_study_ledger_path",
                return_value=ledger_path,
            ),
            patch(
                "src.experiment.runner.SentenceTransformerEmbedder",
                return_value=StubEmbedder(4),
            ),
        ):
            ret = cli_main(argv, provider_factory=lambda cfg, bud: MockProvider())

        assert ret == 0
        captured = capsys.readouterr()
        out_summary = json.loads(captured.out)
        assert out_summary["complete"] is False
        assert out_summary["stopped_reason"] == "USD_BUDGET_LIMIT"
        assert out_summary["requests_consumed"] == 0

    def test_cli_error_reports_actual_historical_counts(self, bundle, tmp_path, capsys):
        from src.experiment.__main__ import main as cli_main

        output_dir = tmp_path / "cli-error-counts"
        ledger_path = tmp_path / "study_ledger.json"

        proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
        proto_file = tmp_path / "protocol.json"
        proto_file.write_bytes(canonical_bytes(protocol_to_dict(proto)))

        call_count = 0
        def provider_factory(cfg, bud):
            p = MockProvider()
            orig_create = p.create
            def guarded_create(**kwargs):
                nonlocal call_count
                call_count += 1
                if call_count > 1:
                    raise RuntimeError("Simulated provider failure after 1 call")
                return orig_create(**kwargs)
            p.create = guarded_create
            return p

        argv = [
            "live",
            "--config", str(bundle[1]),
            "--output-dir", str(output_dir),
            "--auth-token", "HUMAN_TOKEN",
            "--protocol-file", str(proto_file),
            "--allow-live-dispatch",
            "--max-attempts", "100",
            "--use-money-guard",
            "--study-ledger-path", str(ledger_path),
        ]
        with (
            patch(
                "src.experiment.monetary_ledger.get_canonical_study_ledger_path",
                return_value=ledger_path,
            ),
            patch(
                "src.experiment.runner.SentenceTransformerEmbedder",
                return_value=StubEmbedder(4),
            ),
        ):
            ret = cli_main(argv, provider_factory=provider_factory)

        assert ret == 1
        captured = capsys.readouterr()
        err_lines = [
            line for line in captured.err.strip().splitlines() if line.strip().startswith("{")
        ]
        assert err_lines, f"No JSON error report found in stderr: {captured.err}"
        err_report = json.loads(err_lines[-1])
        assert err_report["status"] == "LIVE_EXECUTION_BLOCKED"
        assert err_report["provider_calls"] >= 1
        assert err_report["prediction_writes"] >= 1


class TestEvaluatorRejectionOfIncompleteAndBreachedRuns:
    """Evaluator strictly rejects runs that are incomplete or contain monetary breaches."""

    def test_evaluator_rejects_incomplete_summary(self, bundle, tmp_path):
        from src.evaluation.experiment_metrics import _load_evaluation_inputs
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-eval-incomplete"
        ledger_path = tmp_path / "study_ledger.json"

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

        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
            stop_after=1,
        )

        pred_paths = {
            cond: output / f"{cond}_predictions.jsonl"
            for cond in ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
        }
        with pytest.raises(
            ValueError, match="evaluator rejects incomplete run|missing or unexpected sample"
        ):
            _load_evaluation_inputs(
                output / "manifest.json",
                pred_paths,
                repository_root=bundle[0],
                expected_sample_count=2,
            )

    def test_evaluator_rejects_breached_journal(self, bundle, tmp_path):
        from src.evaluation.experiment_metrics import _load_evaluation_inputs
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-eval-breached"
        ledger_path = tmp_path / "study_ledger.json"

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

        summary = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: MockProvider(),
        )
        assert summary["complete"] is True

        journal_path = output / "request_journal.jsonl"
        append_journal_event(
            journal_path,
            {
                "event": EVENT_MONETARY_SETTLE,
                "key": ["s1", "no_rag"],
                "cost_usd": "0.53974560",
                "refund_usd": "1.61923680",
                "record_sha256": "00" * 32,
                "breach": True,
                "breach_reason": "Simulated tier breach",
            },
        )

        pred_paths = {
            cond: output / f"{cond}_predictions.jsonl"
            for cond in ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
        }
        with pytest.raises(ValueError, match="evaluator rejects run with monetary breach"):
            _load_evaluation_inputs(
                output / "manifest.json",
                pred_paths,
                repository_root=bundle[0],
                expected_sample_count=2,
            )


class TestBreachPersistentlyPreventsResume:
    """Metadata/price breach persistently blocks resume dispatch even if settle exists."""

    def test_breach_in_ledger_blocks_resume(self, bundle, tmp_path):
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "live-breach-persist"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider(
            outcomes={("s1", "no_rag"): [MockReply(service_tier="priority")]}
        )
        with pytest.raises(LiveExecutionBlockedError, match="Receipt ceiling or metadata breach"):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: provider,
            )

        ledger = StudyBudgetLedger(ledger_path)
        assert ledger.has_breach is True

        with pytest.raises(
            LiveExecutionBlockedError,
            match="Study ledger has prior breach; resume dispatch permanently blocked",
        ):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: MockProvider(),
                resume=True,
            )


class TestAnchorAndLedgerIntegrityRegressions:
    """Regressions for anchor enforcement, missing ledger fail-closed, and history joins."""

    def test_partial_run_missing_ledger_resume_fails_closed(self, bundle, tmp_path):
        """Regression for FAIL at 77026:

        In commit 77026c9, two-view fixture run with stop_after=1 produced cost 0.00000370.
        Deleting ONLY the temp study ledger then resuming stop_after=1 produced 2 records
        but cumulative cost remained 0.00000370 instead of 0.00000740 because _load_or_initialize
        auto reset missing ledger and resume skipped missing settled entries.

        In REPAIR_USD_FINAL, anchor outside deletable output/ledger path detects missing
        ledger after initialization and fails closed before any provider calls (0 egress).
        """
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "run_output"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider()
        summary1 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            stop_after=1,
        )
        assert summary1["new_records"] == 1
        assert summary1["complete"] is False
        first_cost = Decimal(summary1["study_budget"]["cumulative_settled_cost_usd"])
        assert first_cost > Decimal("0.0")

        # Confirm anchor and ledger both exist
        assert ledger_path.exists()
        anchor_path = tmp_path / ".study_anchor.json"
        assert anchor_path.exists()

        # Delete ONLY temp study ledger (anchor remains intact)
        ledger_path.unlink()
        assert not ledger_path.exists()
        assert anchor_path.exists()

        # Track provider calls before resume
        calls_before = provider.call_count

        # Resume must FAIL CLOSED with zero calls
        with pytest.raises(
            LiveExecutionBlockedError,
            match="Study initialization anchor exists.*study ledger.*is missing",
        ):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: provider,
                resume=True,
                stop_after=1,
            )

        # Zero provider calls were dispatched during failed resume
        assert provider.call_count == calls_before

    def test_new_output_dir_refused_against_initialized_study(self, bundle, tmp_path):
        """New output directory with resume=False refused against already initialized study."""
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output1 = tmp_path / "run_output_1"
        output2 = tmp_path / "run_output_2"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider()
        run_live_exp(
            plan,
            output1,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            stop_after=1,
        )

        calls_before = provider.call_count

        # Attempt to run against a new output directory without resume
        with pytest.raises(
            LiveExecutionBlockedError,
            match="Study has already been initialized.*new output directory.*cannot start fresh",
        ):
            run_live_exp(
                plan,
                output2,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: provider,
                resume=False,
            )

        assert provider.call_count == calls_before
        assert not output2.exists()

    def test_rolled_back_archived_ledger_refused_on_resume(self, bundle, tmp_path):
        """Archived or rolled-back ledger missing settled journal history fails closed on resume."""
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "run_output_rollback"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider = MockProvider()
        # Step 1: Run 1 sample
        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            stop_after=1,
        )

        # Archive copy of ledger containing only 1 record
        archived_ledger_bytes = ledger_path.read_bytes()

        # Step 2: Resume to produce second sample
        run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider,
            resume=True,
            stop_after=1,
        )

        # Overwrite ledger with older archived copy (missing sample 2)
        ledger_path.write_bytes(archived_ledger_bytes)

        calls_before = provider.call_count

        # Resume attempt with rolled-back ledger must fail closed
        with pytest.raises(
            LiveExecutionBlockedError,
            match="missing from study ledger; rolled-back, missing, or archived",
        ):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: provider,
                resume=True,
            )

        assert provider.call_count == calls_before

    def test_budget_19_99_and_net_available(self, tmp_dir, sample_pricing):
        """Total study ceiling is strictly 19.99 USD, net starting available 19.93735990 USD."""
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

        assert ledger.total_budget == Decimal("19.99000000")
        assert ledger.total_budget < Decimal("20.00000000")
        assert ledger.prior_pilot_hold == Decimal("0.05264010")
        assert ledger.uncommitted_available_balance_usd == Decimal("19.93735990")

    def test_unanchored_ledger_refused(self, tmp_dir, sample_pricing):
        """Ledger file existing without initialization anchor fails closed."""
        ledger_path = tmp_dir / "study_ledger.json"
        ledger = StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)
        assert ledger.anchor_path.exists()

        # Delete anchor file only
        ledger.anchor_path.unlink()

        with pytest.raises(
            LiveExecutionBlockedError, match="study initialization anchor.*is missing"
        ):
            StudyBudgetLedger(ledger_path, pricing_config=sample_pricing)

    def test_runner_case_incomplete_followed_by_another_request_and_resume(
        self, bundle, tmp_path
    ):
        """Runner handles INCOMPLETE outcome followed by another request and clean resume."""
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "run_incomplete_resume"
        ledger_path = tmp_path / "study_ledger.json"

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

        # Request 1 returns INCOMPLETE with metered tokens
        reply_inc = MockReply(
            status="incomplete",
            input_tokens=1000,
            output_tokens=8192,
            response_id="resp-inc-1",
        )
        provider1 = MockProvider(
            outcomes={("s1", "no_rag"): [reply_inc]}
        )
        summary1 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider1,
            stop_after=1,
        )
        assert summary1["new_records"] == 1
        assert summary1["complete"] is False

        # Verify record is INCOMPLETE and ledger settled exact tokens without breach
        pred_file = output / "no_rag_predictions.jsonl"
        preds = parse_jsonl(pred_file.read_bytes())
        assert len(preds) == 1
        assert preds[0]["parse_status"] == "INCOMPLETE"
        assert preds[0]["prompt_tokens"] == 1000
        assert preds[0]["completion_tokens"] == 8192

        ledger1 = StudyBudgetLedger(ledger_path)
        assert ledger1.has_breach is False
        assert ledger1.cumulative_settled_cost_usd == Decimal("0.01008040")

        # Request 2 follows up with completed/VALID reply
        reply_val = MockReply(
            status="completed",
            input_tokens=1000,
            output_tokens=500,
            response_id="resp-val-2",
        )
        provider2 = MockProvider(
            outcomes={("s1", "rag_k1"): [reply_val]}
        )
        summary2 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider2,
            resume=True,
            stop_after=1,
        )
        assert summary2["new_records"] == 1
        assert summary2["complete"] is False

        # Control resume: verifies both completed records without breach
        provider3 = MockProvider()
        ledger2 = StudyBudgetLedger(ledger_path)
        assert ledger2.has_breach is False
        # Cost is 0.01008040 (inc) + 0.00085000 (val) = 0.01093040
        assert ledger2.cumulative_settled_cost_usd == Decimal("0.01093040")

        summary3 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider3,
            resume=True,
            stop_after=1,
        )
        assert summary3["new_records"] == 1
        assert summary3["study_budget"]["has_breach"] is False

    def test_tampered_ordinal_resume_zero_call_regression(self, bundle, tmp_path):
        """Tampered receipt ordinal in journal causes resume to fail closed with 0 calls."""
        from src.experiment.config import load_plan
        from tests.test_experiment_t22 import run_live_experiment as run_live_exp

        plan = load_plan(bundle[1])
        output = tmp_path / "run_tampered_ordinal"
        ledger_path = tmp_path / "study_ledger.json"

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

        provider1 = MockProvider()
        summary1 = run_live_exp(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, bud: provider1,
            stop_after=1,
        )
        assert summary1["new_records"] == 1

        # Tamper with attempt_receipt event in journal
        journal_path = output / "request_journal.jsonl"
        events = parse_jsonl(journal_path.read_bytes())
        tampered = False
        for ev in events:
            if ev.get("event") == "attempt_receipt":
                ev["ordinal"] = 99
                tampered = True
                break
        assert tampered is True
        journal_path.write_bytes(
            b"".join(canonical_bytes(e) + b"\n" for e in events)
        )

        # Attempt to resume with fresh provider
        provider2 = MockProvider()
        with pytest.raises(
            ValueError, match="attempt_receipt ordinal 99 does not match journal consumed 1"
        ):
            run_live_exp(
                plan,
                output,
                authorization=auth,
                protocol=proto,
                provider_factory=lambda cfg, bud: provider2,
                resume=True,
                stop_after=1,
            )

        # Must fail closed before ANY provider call is dispatched
        assert provider2.call_count == 0
