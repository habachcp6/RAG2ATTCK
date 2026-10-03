"""Unit tests for Phase S2 Terminal Audit Script using isolated offline fixtures."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest

from scripts.audit_terminal_run import (
    AuditVerificationError,
    audit_completeness_and_cardinality,
    audit_financial_ledger_and_tariffs,
    audit_journal_join_and_lifecycle,
    audit_production_preloader_and_lifecycle,
    audit_protected_baseline_22_files,
    audit_provenance_and_hash_invariants,
    audit_secret_sanitization,
    audit_terminal_process_proof,
    generate_audit_seal,
    main,
)
from src.experiment.config import canonical_bytes, digest
from src.experiment.schemas import CONDITIONS, Candidate, ExperimentRecord

REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_PRICING_SHA = "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565"


def _valid_terminal_proof_data(
    *,
    run_id: str = "live-66b94b1676bf46a9",
    task_id: str = "task-1264",
    pid: int = 50192,
    start_identity: str = "2026-10-02T01:00:00Z",
    process_status: str = "terminated",
    exit_code: int = 0,
    artifact_log_sha256: str = "a" * 64,
    final_summary: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    default_summary = {
        "complete": True,
        "execution_mode": "live",
        "run_id": run_id,
        "record_count": 6400,
        "requests_consumed": 6401,
        "consumed_provider_attempts": 6401,
        "study_budget": {
            "has_breach": False,
            "total_budget_usd": "19.99000000",
            "cumulative_settled_cost_usd": "6.57575890",
            "uncommitted_available_balance_usd": "13.36160100",
            "prior_pilot_provisional_hold_usd": "0.05264010",
            "active_reservations_usd": "0E-8",
            "pricing_contract_sha256": TEST_PRICING_SHA,
            "settlement_records_count": 6400,
        },
    }
    return {
        "run_id": run_id,
        "task_id": task_id,
        "pid": pid,
        "start_identity": start_identity,
        "process_status": process_status,
        "exit_code": exit_code,
        "artifact_log_sha256": artifact_log_sha256,
        "final_summary": final_summary if final_summary is not None else default_summary,
    }


def _create_real_producer_output(tmp_path: Path) -> Tuple[Path, Path, Dict[str, Any]]:
    """Build a real valid producer output directory using bundle and MockProvider."""
    from src.experiment.config import load_plan
    from src.experiment.runner import MockProvider, run_mock_experiment
    from tests.test_experiment import bundle

    bundle_fn = getattr(bundle, "__wrapped__", bundle)
    root, config_path, _ = bundle_fn(tmp_path)
    cfg = json.loads(config_path.read_bytes())

    # Switch split to dev so load_evaluation_inputs validates 2-sample cohort
    sm_path = root / "split_manifest.json"
    sm = {"dev": ["p1"], "test": []}
    sm_path.write_bytes(json.dumps(sm).encode())
    cfg["dataset"]["split_manifest"]["sha256"] = hashlib.sha256(sm_path.read_bytes()).hexdigest()

    pairs_path = root / "pairs.jsonl"
    pairs = [json.loads(line) for line in pairs_path.read_bytes().splitlines() if line.strip()]
    for p in pairs:
        p["split"] = "dev"
    pairs_data = b"".join(json.dumps(p).encode() + b"\n" for p in pairs)
    pairs_path.write_bytes(pairs_data)
    cfg["dataset"]["pairs"]["sha256"] = hashlib.sha256(pairs_data).hexdigest()

    dm_path = root / "dataset_manifest.json"
    dm = json.loads(dm_path.read_bytes())
    dm["split_counts"] = {"dev": 1, "test": 0}
    dm["files"]["split_manifest.json"] = cfg["dataset"]["split_manifest"]["sha256"]
    dm["files"]["pairs.jsonl"] = cfg["dataset"]["pairs"]["sha256"]
    dm_data = json.dumps(dm).encode() + b"\n"
    dm_path.write_bytes(dm_data)
    cfg["dataset"]["manifest"]["sha256"] = hashlib.sha256(dm_data).hexdigest()

    cfg["dataset"]["split"] = "dev"
    config_path.write_bytes(json.dumps(cfg).encode() + b"\n")

    plan = load_plan(config_path)
    output = tmp_path / "producer_run"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    manifest = json.loads((output / "manifest.json").read_bytes())
    return root, output, manifest


def _create_mock_record(
    sample_id: str,
    condition: str,
    parse_status: str = "VALID",
    prompt_tokens: int = 500,
    completion_tokens: int = 50,
    response_id: str = "resp_123",
) -> ExperimentRecord:
    expected_k = 0 if condition == "no_rag" else int(condition[5:])
    candidates = [
        Candidate(rank=i + 1, technique_id=f"T100{i}", score=round(0.95 - (i * 0.05), 4))
        for i in range(expected_k)
    ]
    is_valid = parse_status == "VALID"
    parsed_ids = ["T1053.005"] if parse_status in {"VALID", "INVALID_ID"} else []

    return ExperimentRecord(
        schema_version="1.0.0",
        experiment_id="synthetic-paired-test-1",
        run_id="live-test",
        sample_id=sample_id,
        condition=condition,
        execution_mode="live",
        provider="openai",
        model="gpt-5.6-luna",
        model_version=None,
        prompt_sha256="b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206",
        model_config_sha256="312c34cedd84106f2004c6070b72aeac1dd84209a464e2993fee3ec87822697f",
        dataset_sha256="90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8",
        ground_truth_sha256="8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608",
        corpus_sha256="b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75",
        index_sha256="7e3b9944870860766ebd5ba76f19a420c1bbe57cebd4e4238b06fd31128578e5",
        output_schema_sha256="b17f2fc84d3a12c35227ece9039f43fc08d7f870cda9e1398ef502b9fdb9feef",
        ground_truth_version="synthetic-paired-v1",
        attack_release="19.2",
        manifest_sha256="2f81076c4cfc3d3bd88b6bfe4b6e39775b8ed398a5623eaa603691cb277a9178",
        pair_id="pair_1",
        view_type="contextual",
        parsed_technique_ids=parsed_ids,
        parse_status=parse_status,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=prompt_tokens + completion_tokens,
        latency_ms=100.0,
        request_attempt_count=1,
        request_timestamp_utc="2026-10-01T00:00:00+00:00",
        response_timestamp_utc="2026-10-01T00:00:01+00:00",
        response_id=response_id,
        raw_response='{"technique_id":"T1053.005"}' if is_valid else '{"refusal":"true"}',
        raw_response_logged=True,
        retrieval_k=expected_k,
        retrieved_candidates=candidates,
        retry_count=0,
        returned_model_id="gpt-5.6-luna",
        success=is_valid,
        terminal=True,
        timestamp="2026-10-01T00:00:01+00:00",
        error_type=None,
        error_message=None,
        system_fingerprint=None,
    )


def test_audit_passes_on_valid_fixture(tmp_path):
    """Verify that audit checks pass cleanly on valid fixture data."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()

    sample_ids = {"view_01", "view_02"}
    records_by_key = {}

    for c in CONDITIONS:
        p = exp_dir / f"{c}_predictions.jsonl"
        lines = []
        for s in sorted(sample_ids):
            rec = _create_mock_record(s, c, response_id=f"resp_{s}_{c}")
            records_by_key[(s, c)] = rec
            lines.append(json.dumps(rec.model_dump()))
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    audited_records = audit_completeness_and_cardinality(
        exp_dir, sample_ids, require_all_conditions=True
    )
    assert len(audited_records) == 10

    # Build valid journal
    jlines = [
        json.dumps(
            {"event": "header", "manifest_sha256": "dummy_manifest_sha", "max_requests": 25600}
        )
    ]
    ord_counter = 1
    for key, rec in records_by_key.items():
        s, c = key
        rec_sha = digest(canonical_bytes(rec.model_dump()))
        jlines.append(
            json.dumps({"event": "monetary_reserve", "key": [s, c], "amount_usd": "2.15898240"})
        )
        jlines.append(json.dumps({"event": "attempt", "key": [s, c], "ordinal": ord_counter}))
        jlines.append(
            json.dumps(
                {
                    "event": "attempt_receipt",
                    "key": [s, c],
                    "ordinal": ord_counter,
                    "attempt_index": 0,
                    "status": "SUCCESS",
                    "service_tier": "default",
                    "model": "gpt-5.6-luna",
                    "input_tokens": rec.prompt_tokens,
                    "output_tokens": rec.completion_tokens,
                    "cached_tokens": 0,
                    "response_id": rec.response_id,
                }
            )
        )
        ord_counter += 1
        jlines.append(json.dumps({"event": "complete", "key": [s, c], "record_sha256": rec_sha}))
        cost = "0.00018500"
        refund = "2.15879740"
        jlines.append(
            json.dumps(
                {
                    "event": "monetary_settle",
                    "key": [s, c],
                    "cost_usd": cost,
                    "refund_usd": refund,
                    "record_sha256": rec_sha,
                    "breach": False,
                    "breach_reason": None,
                }
            )
        )

    (exp_dir / "request_journal.jsonl").write_text("\n".join(jlines) + "\n", encoding="utf-8")
    receipts_by_key, settled_events_by_key = audit_journal_join_and_lifecycle(
        exp_dir, audited_records
    )
    assert len(receipts_by_key) == 10
    assert len(settled_events_by_key) == 10


def test_audit_fails_on_duplicate_complete(tmp_path):
    """Duplicate complete event in journal is detected and raises AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    records_by_key = {}
    for c in CONDITIONS:
        p = exp_dir / f"{c}_predictions.jsonl"
        rec = _create_mock_record("view_01", c, response_id=f"resp_view_01_{c}")
        records_by_key[("view_01", c)] = rec
        p.write_text(json.dumps(rec.model_dump()) + "\n", encoding="utf-8")

    rec_sha = digest(canonical_bytes(records_by_key[("view_01", "no_rag")].model_dump()))
    jlines = [
        json.dumps({"event": "header", "manifest_sha256": "dummy", "max_requests": 100}),
        json.dumps({"event": "attempt", "key": ["view_01", "no_rag"], "ordinal": 1}),
        json.dumps({"event": "complete", "key": ["view_01", "no_rag"], "record_sha256": rec_sha}),
        # duplicate complete!
        json.dumps({"event": "complete", "key": ["view_01", "no_rag"], "record_sha256": rec_sha}),
    ]
    (exp_dir / "request_journal.jsonl").write_text("\n".join(jlines) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Duplicate complete event"):
        audit_journal_join_and_lifecycle(exp_dir, records_by_key)


def test_audit_fails_on_duplicate_settle(tmp_path):
    """Duplicate monetary_settle event in journal is detected and rejected."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    records_by_key = {
        ("view_01", c): _create_mock_record("view_01", c, response_id=f"resp_{c}")
        for c in CONDITIONS
    }
    rec_sha = digest(canonical_bytes(records_by_key[("view_01", "no_rag")].model_dump()))
    jlines = [
        json.dumps({"event": "header", "manifest_sha256": "dummy", "max_requests": 100}),
        json.dumps({"event": "attempt", "key": ["view_01", "no_rag"], "ordinal": 1}),
        json.dumps({"event": "complete", "key": ["view_01", "no_rag"], "record_sha256": rec_sha}),
        json.dumps(
            {
                "event": "monetary_settle",
                "key": ["view_01", "no_rag"],
                "cost_usd": "0.0001",
                "refund_usd": "2.0",
                "record_sha256": rec_sha,
                "breach": False,
            }
        ),
        # duplicate settle!
        json.dumps(
            {
                "event": "monetary_settle",
                "key": ["view_01", "no_rag"],
                "cost_usd": "0.0001",
                "refund_usd": "2.0",
                "record_sha256": rec_sha,
                "breach": False,
            }
        ),
    ]
    (exp_dir / "request_journal.jsonl").write_text("\n".join(jlines) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Duplicate monetary_settle event"):
        audit_journal_join_and_lifecycle(exp_dir, records_by_key)


def test_audit_fails_on_duplicate_receipt(tmp_path):
    """Duplicate attempt_index receipt for key is detected and rejected."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    records_by_key = {
        ("view_01", c): _create_mock_record("view_01", c, response_id=f"resp_{c}")
        for c in CONDITIONS
    }
    jlines = [
        json.dumps({"event": "header", "manifest_sha256": "dummy", "max_requests": 100}),
        json.dumps({"event": "attempt", "key": ["view_01", "no_rag"], "ordinal": 1}),
        json.dumps(
            {
                "event": "attempt_receipt",
                "key": ["view_01", "no_rag"],
                "ordinal": 1,
                "attempt_index": 0,
                "status": "SUCCESS",
            }
        ),
        # duplicate receipt for attempt_index 0!
        json.dumps(
            {
                "event": "attempt_receipt",
                "key": ["view_01", "no_rag"],
                "ordinal": 1,
                "attempt_index": 0,
                "status": "SUCCESS",
            }
        ),
    ]
    (exp_dir / "request_journal.jsonl").write_text("\n".join(jlines) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Duplicate attempt_index 0"):
        audit_journal_join_and_lifecycle(exp_dir, records_by_key)


def test_audit_fails_on_orphan_reservation(tmp_path):
    """Active reservations remaining open in study ledger is rejected."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    ledger_path = artifacts_dir / "study_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "active_reservations": {"view_01:no_rag": "2.15898240"},  # orphan hold!
                "active_reservations_usd": "2.15898240",
                "settled_records": {},
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Active reservations remaining open"):
        audit_financial_ledger_and_tariffs(study_root, validator_root, {}, {}, {})


def test_audit_fails_on_secret_leak(tmp_path):
    """Secret patterns detected in output files are rejected."""
    leak_file = tmp_path / "leaked_predictions.jsonl"
    leak_file.write_text('{"api_key": "sk-proj-1234567890123456789012345"}', encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Secret leak detected"):
        audit_secret_sanitization([leak_file])


def test_audit_accepts_valid_failure_statuses(tmp_path):
    """Scientifically authentic failures (REFUSAL, TIMEOUT, API_FAILURE, MALFORMED_RESPONSE)

    are accepted as valid terminal records.
    """
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    sample_ids = {"view_refusal", "view_timeout", "view_api_err", "view_malformed"}
    failure_statuses = {
        "view_refusal": "REFUSAL",
        "view_timeout": "TIMEOUT",
        "view_api_err": "API_FAILURE",
        "view_malformed": "MALFORMED_RESPONSE",
    }

    for c in CONDITIONS:
        p = exp_dir / f"{c}_predictions.jsonl"
        lines = []
        for s in sorted(sample_ids):
            rec = _create_mock_record(
                s, c, parse_status=failure_statuses[s], response_id=f"resp_{s}_{c}"
            )
            lines.append(json.dumps(rec.model_dump()))
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")

    records = audit_completeness_and_cardinality(exp_dir, sample_ids, require_all_conditions=True)
    assert len(records) == 20
    assert records[("view_refusal", "no_rag")].parse_status == "REFUSAL"
    assert records[("view_timeout", "no_rag")].parse_status == "TIMEOUT"
    assert records[("view_api_err", "no_rag")].parse_status == "API_FAILURE"
    assert records[("view_malformed", "no_rag")].parse_status == "MALFORMED_RESPONSE"


def test_audit_fails_on_missing_test_view(tmp_path):
    """Missing a required test split sample triggers AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    expected_sample_ids = {"view_01", "view_02"}
    # Only write view_01
    for c in CONDITIONS:
        p = exp_dir / f"{c}_predictions.jsonl"
        rec = _create_mock_record("view_01", c)
        p.write_text(json.dumps(rec.model_dump()) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Cardinality error in"):
        audit_completeness_and_cardinality(
            exp_dir, expected_sample_ids, require_all_conditions=True
        )


def test_audit_fails_on_budget_breach(tmp_path):
    """Cumulative settled cost exceeding $19.93735990 raises AuditVerificationError."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    ledger_path = artifacts_dir / "study_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "active_reservations": {},
                "active_reservations_usd": "0.00000000",
                "cumulative_settled_cost_usd": "20.00000000",
                "uncommitted_available_balance_usd": "0.00000000",
                "settled_records": {},
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Ledger settled records count mismatch"):
        audit_financial_ledger_and_tariffs(study_root, validator_root, {"k": 1}, {}, {})


def test_native_ledger_without_has_breach_passes(tmp_path):
    """Native healthy ledger omitting has_breach and breached_records passes cleanly."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    rec = _create_mock_record("view_01", "no_rag", prompt_tokens=728, completion_tokens=76)
    rec_sha = digest(canonical_bytes(rec.model_dump()))
    records_by_key = {("view_01", "no_rag"): rec}

    # Flat receipt matching runner._on_attempt
    receipt = {
        "event": "attempt_receipt",
        "key": ["view_01", "no_rag"],
        "ordinal": 1,
        "attempt_index": 0,
        "status": "SUCCESS",
        "service_tier": "default",
        "model": "gpt-5.6-luna",
        "input_tokens": 728,
        "output_tokens": 76,
        "cached_tokens": 0,
        "response_id": rec.response_id,
    }
    receipts_by_key = {("view_01", "no_rag"): [receipt]}
    settles_by_key = {
        ("view_01", "no_rag"): {
            "cost_usd": "0.00027320",
            "refund_usd": "2.15870920",
            "record_sha256": rec_sha,
            "breach": False,
        }
    }

    # Healthy ledger omitting has_breach
    ledger_path = artifacts_dir / "study_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "service_tier": "default",
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "active_reservations": {},
                "active_reservations_usd": "0.00000000",
                "cumulative_settled_cost_usd": "0.00027320",
                "uncommitted_available_balance_usd": "19.93708670",
                "settlement_records_count": 1,
                "settled_records": {
                    "view_01:no_rag": {
                        "cost_usd": "0.00027320",
                        "refund_usd": "2.15870920",
                        "record_sha256": rec_sha,
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    cost, avail = audit_financial_ledger_and_tariffs(
        study_root, validator_root, records_by_key, receipts_by_key, settles_by_key
    )
    assert cost == Decimal("0.00027320")
    assert avail == Decimal("19.93708670")


def test_ledger_with_has_breach_true_fails(tmp_path):
    """Ledger reporting has_breach=True triggers AuditVerificationError."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    ledger_path = artifacts_dir / "study_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "has_breach": True,  # breached!
                "breached_records": {"view_01:no_rag": "OVER_BUDGET"},
                "active_reservations": {},
                "active_reservations_usd": "0.00000000",
                "cumulative_settled_cost_usd": "0.00027320",
                "uncommitted_available_balance_usd": "19.93708670",
                "settled_records": {},
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Study ledger reports breach"):
        audit_financial_ledger_and_tariffs(study_root, validator_root, {}, {}, {})


def test_ledger_with_non_bool_breach_fails(tmp_path):
    """Ledger with non-boolean has_breach (e.g. string 'false') fails audit."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    ledger_path = artifacts_dir / "study_ledger.json"
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "has_breach": "false",  # string forbidden!
                "active_reservations": {},
                "active_reservations_usd": "0.00000000",
                "cumulative_settled_cost_usd": "0.00027320",
                "uncommitted_available_balance_usd": "19.93708670",
                "settled_records": {},
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Study ledger reports breach"):
        audit_financial_ledger_and_tariffs(study_root, validator_root, {}, {}, {})


def test_audit_fails_on_canary_canonical_digest_mismatch(tmp_path):
    """Canary prediction canonical digest drift is detected and raises AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    rec = _create_mock_record("view_00477e30", "no_rag", response_id="resp_tampered")

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Canary canonical digest drift"):
        audit_provenance_and_hash_invariants(
            validator_root,
            exp_dir,
            {("view_00477e30", "no_rag"): rec},
            canary_raw_firstline_hash=None,
            canary_canonical_digest="dabf60970aa5a18d93f95976aafdaeef2d747e24d9bcb7b13176e63e2edde034",
        )


def test_audit_fails_on_canary_firstline_hash_mismatch(tmp_path):
    """Canary prediction raw line 1 hash drift is detected and raises AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    canary_file = exp_dir / "no_rag_predictions.jsonl"
    canary_file.write_text('{"tampered": true}\n', encoding="utf-8")

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Canary first line raw SHA-256 drift"):
        audit_provenance_and_hash_invariants(
            validator_root,
            exp_dir,
            {},
            canary_raw_firstline_hash="83351ad996f7d4d70910051f47f7a3d4c45a46259431dcf92e764dbf5d554770",
        )


def test_audit_fails_on_launcher_hash_mismatch(tmp_path):
    """Launcher wrapper hash drift is detected and raises AuditVerificationError."""
    launcher_file = tmp_path / "launcher.py"
    launcher_file.write_text("# tampered launcher", encoding="utf-8")

    validator_root = REPO_ROOT
    with pytest.raises(AuditVerificationError, match="Launcher wrapper SHA-256 drift"):
        audit_provenance_and_hash_invariants(
            validator_root,
            tmp_path,
            {},
            canary_raw_firstline_hash=None,
            canary_canonical_digest=None,
            launcher_wrapper_path=launcher_file,
            expected_launcher_hash="05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa",
        )


def test_generate_audit_seal_fails_on_missing_artifact(tmp_path):
    """Seal generation fails closed if any required artifact is missing."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    val_root = REPO_ROOT
    seal_path = tmp_path / "seal.json"

    with pytest.raises(AuditVerificationError, match="Missing required artifact for seal"):
        generate_audit_seal(
            exp_dir,
            study_root,
            val_root,
            seal_path,
            records_by_key={("v1", "no_rag"): _create_mock_record("v1", "no_rag")},
            cumulative_settled_usd=Decimal("0.1"),
            uncommitted_avail_usd=Decimal("19.8"),
            is_production=False,
        )


def test_audit_fails_on_invalid_money_format(tmp_path):
    """Non-finite or boolean monetary fields in ledger trigger ValueError/AuditVerificationError."""
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    anchor_path = study_root / ".study_anchor.json"
    anchor_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "initial_available_usd": "19.93735990",
            }
        ),
        encoding="utf-8",
    )

    ledger_path = artifacts_dir / "study_ledger.json"
    # active_reservations_usd is boolean False (forbidden!)
    ledger_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "study_id": "rag2attack-study-wide",
                "pricing_contract_sha256": TEST_PRICING_SHA,
                "total_budget_usd": "19.99000000",
                "prior_pilot_provisional_hold_usd": "0.05264010",
                "has_breach": False,
                "active_reservations": {},
                "active_reservations_usd": False,  # invalid boolean!
                "cumulative_settled_cost_usd": "0.00027320",
                "uncommitted_available_balance_usd": "19.93708670",
                "settled_records": {},
            }
        ),
        encoding="utf-8",
    )

    validator_root = REPO_ROOT
    with pytest.raises(ValueError, match="must be Decimal, int, or str"):
        audit_financial_ledger_and_tariffs(study_root, validator_root, {}, {}, {})


def test_audit_fails_on_missing_provenance_and_launcher(tmp_path):
    """Missing launcher raises AuditVerificationError (supervisor counterexample 1)."""
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(AuditVerificationError):
        audit_provenance_and_hash_invariants(
            empty, empty, {}, launcher_wrapper_path=empty / "missing-launcher.py"
        )


def _setup_valid_native_study(tmp_path):
    test_native_ledger_without_has_breach_passes(tmp_path)
    study_root = tmp_path / "study"
    ledger_path = study_root / "artifacts" / "study_budget" / "study_ledger.json"
    ledger = json.loads(ledger_path.read_bytes())
    rec = _create_mock_record("view_01", "no_rag", prompt_tokens=728, completion_tokens=76)
    key = ("view_01", "no_rag")
    receipt = {
        "event": "attempt_receipt",
        "key": list(key),
        "ordinal": 1,
        "attempt_index": 0,
        "status": "SUCCESS",
        "service_tier": "default",
        "model": "gpt-5.6-luna",
        "input_tokens": 728,
        "output_tokens": 76,
        "cached_tokens": 0,
        "response_id": rec.response_id,
    }
    rec_sha = digest(canonical_bytes(rec.model_dump()))
    settle = {
        "cost_usd": "0.00027320",
        "refund_usd": "2.15870920",
        "record_sha256": rec_sha,
        "breach": False,
    }
    return study_root, ledger_path, ledger, {key: rec}, {key: [receipt]}, {key: settle}


def test_audit_fails_on_ledger_count_drift(tmp_path):
    """Drift in settlement_records_count raises AuditVerificationError."""
    study_root, ledger_path, ledger, recs, receipts, settles = _setup_valid_native_study(tmp_path)
    ledger["settlement_records_count"] = 999
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="settlement_records_count"):
        audit_financial_ledger_and_tariffs(study_root, REPO_ROOT, recs, receipts, settles)


def test_audit_fails_on_ledger_record_hash_drift(tmp_path):
    """Drift in record_sha256 raises AuditVerificationError."""
    study_root, ledger_path, ledger, recs, receipts, settles = _setup_valid_native_study(tmp_path)
    ledger["settled_records"]["view_01:no_rag"]["record_sha256"] = "0" * 64
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="record_sha256 mismatch"):
        audit_financial_ledger_and_tariffs(study_root, REPO_ROOT, recs, receipts, settles)


def test_audit_fails_on_ledger_refund_drift(tmp_path):
    """Drift in refund_usd raises AuditVerificationError."""
    study_root, ledger_path, ledger, recs, receipts, settles = _setup_valid_native_study(tmp_path)
    ledger["settled_records"]["view_01:no_rag"]["refund_usd"] = "9.00000000"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="Refund drift"):
        audit_financial_ledger_and_tariffs(study_root, REPO_ROOT, recs, receipts, settles)


def test_audit_fails_on_pilot_hold_drift(tmp_path):
    """Drift in prior_pilot_provisional_hold_usd raises AuditVerificationError."""
    study_root, ledger_path, ledger, recs, receipts, settles = _setup_valid_native_study(tmp_path)
    ledger["prior_pilot_provisional_hold_usd"] = "0.10000000"
    ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="pilot hold drift"):
        audit_financial_ledger_and_tariffs(study_root, REPO_ROOT, recs, receipts, settles)


def test_protected_baseline_22_files_pass():
    """All 22 protected baseline files, protocol decisions, and pricing contract pass."""
    res = audit_protected_baseline_22_files(REPO_ROOT)
    assert res["all_22_files_verified"] is True
    assert res["verified_file_count"] == 22
    assert res["protocol_canonical_digest"] == (
        "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"
    )


def test_protected_baseline_file_byte_mismatch(tmp_path):
    """Byte drift in any of the 22 protected baseline files raises AuditVerificationError."""
    fake_inv = tmp_path / "baseline.json"
    dummy_dict = {f"fake_{i}": "0" * 64 for i in range(21)}
    dummy_dict["prompts/baseline_v1.txt"] = "0" * 64
    fake_inv.write_text(
        json.dumps(
            {
                "baseline_sha": "80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315",
                "protected_files": dummy_dict,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        AuditVerificationError,
        match="Protected baseline hash mismatch|Missing protected baseline file",
    ):
        audit_protected_baseline_22_files(REPO_ROOT, fake_inv)


def test_protocol_canonical_digest_mismatch(tmp_path):
    """Tampered protocol decisions or hash raises AuditVerificationError."""
    fake_root = tmp_path / "validator_root"
    fake_root.mkdir()
    cfg_dir = fake_root / "config"
    cfg_dir.mkdir()
    real_proto = json.loads((REPO_ROOT / "config" / "experiment_protocol_v1.json").read_bytes())
    real_proto["d1_raw_response_policy"] = "DISCARD"
    (cfg_dir / "experiment_protocol_v1.json").write_text(json.dumps(real_proto), encoding="utf-8")
    (cfg_dir / "pricing_v1.json").write_text(
        (REPO_ROOT / "config" / "pricing_v1.json").read_text(encoding="utf-8"), encoding="utf-8"
    )

    proto_sha = digest((cfg_dir / "experiment_protocol_v1.json").read_bytes())
    pricing_sha = digest((cfg_dir / "pricing_v1.json").read_bytes())
    prot_files = {
        "config/experiment_protocol_v1.json": proto_sha,
        "config/pricing_v1.json": pricing_sha,
    }
    for i in range(20):
        (fake_root / f"dummy_{i}").write_bytes(b"dummy")
        prot_files[f"dummy_{i}"] = digest(b"dummy")

    fake_inv = tmp_path / "baseline.json"
    fake_inv.write_text(
        json.dumps(
            {
                "baseline_sha": "80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315",
                "protected_files": prot_files,
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        AuditVerificationError,
        match="Protocol canonical digest mismatch|Protocol validation failed",
    ):
        audit_protected_baseline_22_files(fake_root, fake_inv)


def test_production_rejects_active_lockfiles(tmp_path):
    """Presence of active lockfile (study_ledger.lock, etc.) triggers error in production."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    artifacts_dir = study_root / "artifacts" / "study_budget"
    artifacts_dir.mkdir(parents=True)

    # Test study_ledger.lock
    ledger_lock = artifacts_dir / "study_ledger.lock"
    ledger_lock.write_text("lock", encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="active lockfile found"):
        main(["--exp-dir", str(exp_dir), "--study-root", str(study_root), "--is-production"])

    ledger_lock.unlink()

    # Test .study_anchor.lock
    anchor_lock = study_root / ".study_anchor.lock"
    anchor_lock.write_text("lock", encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="active lockfile found"):
        main(["--exp-dir", str(exp_dir), "--study-root", str(study_root), "--is-production"])

    anchor_lock.unlink()

    # Test .run.lock
    run_lock = exp_dir / ".run.lock"
    run_lock.write_text("lock", encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="active lockfile found"):
        main(["--exp-dir", str(exp_dir), "--study-root", str(study_root), "--is-production"])


def test_production_rejects_mock_fixture_mode(tmp_path):
    """Production audit strictly rejects mock_fixture execution mode."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    (study_root / "scripts").mkdir()
    launcher_path = study_root / "scripts" / "run_experiments.py"
    launcher_path.write_text("#!/usr/bin/env python\n", encoding="utf-8")

    (exp_dir / "run_summary.json").write_text(
        json.dumps({"complete": True, "record_count": 6400}), encoding="utf-8"
    )
    proof_file = tmp_path / "proof.json"
    proof_file.write_text(
        json.dumps(_valid_terminal_proof_data(run_id="test_run", task_id="task-1264")),
        encoding="utf-8",
    )
    (exp_dir / "manifest.json").write_text(
        json.dumps({"execution_mode": "mock_fixture", "run_id": "test_run"}), encoding="utf-8"
    )

    with pytest.raises(
        AuditVerificationError, match="Production audit requires execution_mode='live'"
    ):
        main(
            [
                "--exp-dir",
                str(exp_dir),
                "--study-root",
                str(study_root),
                "--terminal-proof-file",
                str(proof_file),
                "--is-production",
            ]
        )


def test_production_requires_terminal_proof_file(tmp_path):
    """Production audit requires valid zero-exit terminal proof file."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    (study_root / "scripts").mkdir()
    launcher_path = study_root / "scripts" / "run_experiments.py"
    launcher_path.write_text("#!/usr/bin/env python\n", encoding="utf-8")
    (exp_dir / "run_summary.json").write_text(
        json.dumps({"complete": True, "record_count": 6400}), encoding="utf-8"
    )

    # Missing argument
    with pytest.raises(
        AuditVerificationError, match="Production audit requires --terminal-proof-file"
    ):
        main(["--exp-dir", str(exp_dir), "--study-root", str(study_root), "--is-production"])

    # Non-zero exit code
    bad_proof = tmp_path / "bad_proof.json"
    bad_proof.write_text(json.dumps(_valid_terminal_proof_data(exit_code=1)), encoding="utf-8")
    with pytest.raises(
        AuditVerificationError, match="Terminal process proof indicates non-zero exit"
    ):
        main(
            [
                "--exp-dir",
                str(exp_dir),
                "--study-root",
                str(study_root),
                "--terminal-proof-file",
                str(bad_proof),
                "--is-production",
            ]
        )


def test_audit_terminal_process_proof_success(tmp_path):
    """Authoritative task terminal proof validation succeeds when exit_code is 0."""
    proof_path = tmp_path / "proof.json"
    proof_path.write_text(
        json.dumps(_valid_terminal_proof_data()),
        encoding="utf-8",
    )
    info = audit_terminal_process_proof(
        proof_path,
        expected_run_id="live-66b94b1676bf46a9",
        expected_task_id="task-1264",
    )
    assert info["exit_code"] == 0
    assert info["task_id"] == "task-1264"
    assert info["pid"] == 50192
    assert len(info["sha256"]) == 64
    assert info["run_id"] == "live-66b94b1676bf46a9"
    assert info["process_status"] == "terminated"
    assert info["final_summary"]["complete"] is True
    assert info["final_summary"]["execution_mode"] == "live"
    assert info["final_summary"]["run_id"] == "live-66b94b1676bf46a9"
    assert info["final_summary"]["record_count"] == 6400
    assert info["final_summary"]["requests_consumed"] == 6401
    assert info["final_summary"]["consumed_provider_attempts"] == 6401
    assert info["final_summary"]["study_budget"]["total_budget_usd"] == "19.99000000"


def test_audit_fails_on_reordered_journal_events(tmp_path):
    """Reordered journal events trigger AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    rec = _create_mock_record("view_01", "no_rag")
    p = exp_dir / "no_rag_predictions.jsonl"
    p.write_text(json.dumps(rec.model_dump()) + "\n", encoding="utf-8")
    for c in CONDITIONS:
        if c != "no_rag":
            (exp_dir / f"{c}_predictions.jsonl").write_text("", encoding="utf-8")

    rec_sha = digest(canonical_bytes(rec.model_dump()))

    # Settle before complete
    jlines = [
        json.dumps({"event": "header", "manifest_sha256": "dummy_sha", "max_requests": 100}),
        json.dumps({"event": "attempt", "key": ["view_01", "no_rag"], "ordinal": 1}),
        json.dumps(
            {
                "event": "monetary_settle",
                "key": ["view_01", "no_rag"],
                "cost_usd": "0.00027320",
                "refund_usd": "2.15870920",
                "record_sha256": rec_sha,
                "breach": False,
            }
        ),
        json.dumps({"event": "complete", "key": ["view_01", "no_rag"], "record_sha256": rec_sha}),
    ]
    (exp_dir / "request_journal.jsonl").write_text("\n".join(jlines) + "\n", encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Reordered journal events"):
        audit_journal_join_and_lifecycle(exp_dir, {("view_01", "no_rag"): rec})


def test_generate_audit_seal_fails_on_missing_required_file(tmp_path):
    """Missing any required artifact for audit seal triggers fail-closed AuditVerificationError."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    rec = _create_mock_record("view_01", "no_rag")

    with pytest.raises(AuditVerificationError, match="Missing required artifact for seal"):
        generate_audit_seal(
            exp_dir,
            study_root,
            REPO_ROOT,
            tmp_path / "seal.json",
            {("view_01", "no_rag"): rec},
            Decimal("0.0"),
            Decimal("19.99"),
        )


def test_terminal_proof_fails_on_missing_fields(tmp_path):
    """Terminal proof missing any required field raises AuditVerificationError."""
    proof_path = tmp_path / "missing_fields_proof.json"
    data = _valid_terminal_proof_data()
    del data["pid"]
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="missing required fields"):
        audit_terminal_process_proof(proof_path)

    # Missing artifact_log_sha256
    data2 = _valid_terminal_proof_data()
    del data2["artifact_log_sha256"]
    proof_path.write_text(json.dumps(data2), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="missing required fields"):
        audit_terminal_process_proof(proof_path)


def test_terminal_proof_fails_on_running_status(tmp_path):
    """Terminal proof with process_status='running' raises AuditVerificationError."""
    proof_path = tmp_path / "running_proof.json"
    data = _valid_terminal_proof_data(process_status="running")
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="process_status is still 'running'"):
        audit_terminal_process_proof(proof_path)


def test_terminal_proof_fails_on_run_and_task_id_mismatch(tmp_path):
    """Terminal proof with mismatched run_id or task_id raises AuditVerificationError."""
    proof_path = tmp_path / "mismatch_proof.json"
    data = _valid_terminal_proof_data(run_id="wrong-run", task_id="wrong-task")
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="run_id mismatch"):
        audit_terminal_process_proof(proof_path, expected_run_id="live-66b94b1676bf46a9")

    with pytest.raises(AuditVerificationError, match="task_id mismatch"):
        audit_terminal_process_proof(proof_path, expected_task_id="task-1264")


def test_terminal_proof_fails_on_summary_missing_required_live_fields(tmp_path):
    """Probe regression: final_summary missing required schema fields is rejected."""
    proof_path = tmp_path / "missing_summary_fields.json"
    data = _valid_terminal_proof_data(
        final_summary={"complete": True, "unexpected": "does not describe the run"}
    )
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="final_summary missing required fields"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
        )


def test_terminal_proof_fails_on_summary_wrong_run_count_mode(tmp_path):
    """Probe regression: final_summary with foreign run_id or mock mode is rejected."""
    proof_path = tmp_path / "wrong_mode.json"
    data = _valid_terminal_proof_data(
        final_summary={
            "complete": True,
            "run_id": "foreign-run",
            "record_count": 1,
            "execution_mode": "mock",
            "requests_consumed": 1,
            "consumed_provider_attempts": 1,
        }
    )
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="run_id mismatch"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
        )


def test_terminal_proof_fails_on_summary_complete_null(tmp_path):
    """Probe regression: final_summary complete=None/non-True is rejected."""
    proof_path = tmp_path / "complete_null.json"
    data = _valid_terminal_proof_data(
        final_summary={"complete": None}
    )
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="missing required fields|strictly True"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
        )


def test_terminal_proof_fails_on_unbound_log_digest(tmp_path):
    """Probe regression: artifact_log_sha256 drifting from authoritative log bytes is rejected."""
    dummy_log = tmp_path / "task.log"
    dummy_log.write_bytes(b"authoritative task log content with timestamps and events\n")
    real_sha = hashlib.sha256(dummy_log.read_bytes()).hexdigest()

    proof_path = tmp_path / "unbound_log_proof.json"
    data = _valid_terminal_proof_data(
        artifact_log_sha256="0" * 64,
    )
    data["authoritative_log"] = str(dummy_log)
    proof_path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="Authoritative log SHA-256 drift"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
        )

    # Positive control with matching log digest succeeds
    data["artifact_log_sha256"] = real_sha
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    info = audit_terminal_process_proof(
        proof_path,
        expected_run_id="live-66b94b1676bf46a9",
        expected_task_id="task-1264",
    )
    assert info["artifact_log_sha256"] == real_sha


def test_generate_audit_seal_fails_on_production_without_terminal_proof(tmp_path):
    """Direct API: generate_audit_seal fails closed when is_production=True lacks proof or baseline."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    records = {("view_01", "no_rag"): _create_mock_record("view_01", "no_rag")}

    # Missing terminal_proof_info
    with pytest.raises(AuditVerificationError, match="Production seal requires verified terminal_proof_info"):
        generate_audit_seal(
            exp_dir,
            study_root,
            REPO_ROOT,
            tmp_path / "seal.json",
            records,
            Decimal("6.57"),
            Decimal("13.36"),
            is_production=True,
            terminal_proof_info=None,
        )


def test_genuine_terminal_process_proof_positive_control():
    """Probe positive control: genuine canonical terminal process proof passes all checks."""
    canonical_proof = Path(r"D:\RAG2ATT&CK\artifacts\orchestration\terminal_process_proof_20261002.json")
    if not canonical_proof.exists():
        pytest.skip("Canonical terminal proof file not found in study root")

    original = json.loads(canonical_proof.read_bytes())
    info = audit_terminal_process_proof(
        canonical_proof,
        expected_run_id=original["run_id"],
        expected_task_id=original["task_id"],
    )
    assert info["exit_code"] == 0
    assert info["run_id"] == "live-66b94b1676bf46a9"
    assert info["final_summary"]["complete"] is True
    assert info["final_summary"]["execution_mode"] == "live"
    assert info["final_summary"]["record_count"] == 6400


def test_positive_native_preloader_and_lifecycle(tmp_path):
    """Real native preloader and _resume_state execute and validate successfully end-to-end."""
    root, output, manifest = _create_real_producer_output(tmp_path)
    inputs = audit_production_preloader_and_lifecycle(root, output, manifest)
    assert len(inputs.records) == 10
    registry_ids = set(inputs.registry.keys())
    corpus_ids = set(inputs.corpus_ids)
    assert len(registry_ids) > 0
    assert len(corpus_ids) > 0

    # Also verify completeness and cardinality with record binding check
    records = audit_completeness_and_cardinality(
        output,
        {"s1", "s2"},
        require_all_conditions=True,
        registry_ids=registry_ids,
        corpus_ids=corpus_ids,
    )
    assert len(records) == 10


def test_preloader_and_lifecycle_fails_on_header_max_requests_drift(tmp_path):
    """Journal header max_requests drift from manifest cap triggers AuditVerificationError."""
    root, output, manifest = _create_real_producer_output(tmp_path)
    jpath = output / "request_journal.jsonl"
    lines = jpath.read_bytes().splitlines()
    header = json.loads(lines[0])
    header["max_requests"] = 6400  # Drift from 10
    lines[0] = json.dumps(header).encode()
    jpath.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(AuditVerificationError, match="journal header does not match"):
        audit_production_preloader_and_lifecycle(root, output, manifest)


def test_preloader_and_lifecycle_fails_on_foreign_header(tmp_path):
    """Foreign or corrupted journal header triggers AuditVerificationError."""
    root, output, manifest = _create_real_producer_output(tmp_path)
    jpath = output / "request_journal.jsonl"
    lines = jpath.read_bytes().splitlines()
    header = json.loads(lines[0])
    header["manifest_sha256"] = "0" * 64  # Foreign manifest hash
    lines[0] = json.dumps(header).encode()
    jpath.write_bytes(b"\n".join(lines) + b"\n")

    with pytest.raises(AuditVerificationError, match="journal header does not match"):
        audit_production_preloader_and_lifecycle(root, output, manifest)


def test_preloader_and_lifecycle_fails_on_candidate_not_in_corpus(tmp_path):
    """Candidate technique ID outside corpus triggers AuditVerificationError."""
    root, output, manifest = _create_real_producer_output(tmp_path)
    pred_path = output / "rag_k1_predictions.jsonl"
    rows = [json.loads(line) for line in pred_path.read_bytes().splitlines() if line.strip()]
    rows[0]["retrieved_candidates"][0]["technique_id"] = "T9999"  # Not in corpus
    pred_path.write_bytes(b"".join(json.dumps(r).encode() + b"\n" for r in rows))

    with pytest.raises(AuditVerificationError, match="candidate not in corpus"):
        audit_production_preloader_and_lifecycle(root, output, manifest)


def test_preloader_and_lifecycle_fails_on_orphan_reservation(tmp_path):
    """Orphan unclosed reservation in journal triggers AuditVerificationError."""
    root, output, manifest = _create_real_producer_output(tmp_path)
    jpath = output / "request_journal.jsonl"
    orphan_event = json.dumps(
        {"event": "monetary_reserve", "key": ["s1", "no_rag"], "amount_usd": "2.15898240"}
    ).encode()
    jpath.write_bytes(jpath.read_bytes() + orphan_event + b"\n")

    with pytest.raises(AuditVerificationError, match="monetary reserve|lifecycle audit failed"):
        audit_production_preloader_and_lifecycle(root, output, manifest)


def test_terminal_proof_fails_on_consistent_wrong_attempts(tmp_path):
    """Probe regression: consistent wrong attempts (0/0 or 6400/6400) are rejected."""
    proof_path = tmp_path / "zero_attempts.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary.update(requests_consumed=0, consumed_provider_attempts=0)
    data = _valid_terminal_proof_data(final_summary=summary)
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="must be a positive integer, got 0"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
            expected_record_count=6400,
        )

    # 6400/6400 when canonical live run requires 6401
    summary2 = _valid_terminal_proof_data()["final_summary"].copy()
    summary2.update(requests_consumed=6400, consumed_provider_attempts=6400)
    data2 = _valid_terminal_proof_data(final_summary=summary2)
    proof_path2 = tmp_path / "attempts_6400.json"
    proof_path2.write_text(json.dumps(data2), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="Canonical live run expects exactly 6,401"):
        audit_terminal_process_proof(
            proof_path2,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
            expected_record_count=6400,
        )


def test_terminal_proof_fails_on_null_attempts(tmp_path):
    """Probe regression: null attempts fields are rejected."""
    proof_path = tmp_path / "null_attempts.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary.update(requests_consumed=None, consumed_provider_attempts=None)
    data = _valid_terminal_proof_data(final_summary=summary)
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="must be a positive integer, got None"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
            expected_record_count=6400,
        )


def test_terminal_proof_fails_on_invalid_cap_swallowed(tmp_path):
    """Probe regression: total_budget_usd=20.00 is strictly rejected without being swallowed."""
    proof_path = tmp_path / "cap_20.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary["study_budget"]["total_budget_usd"] = "20.00"
    data = _valid_terminal_proof_data(final_summary=summary)
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="budget cap exceeded: 20.00 > 19.99"):
        audit_terminal_process_proof(
            proof_path,
            expected_run_id="live-66b94b1676bf46a9",
            expected_task_id="task-1264",
            expected_record_count=6400,
        )


def test_terminal_proof_fails_on_nan_and_inf_budget(tmp_path):
    """Probe regression: non-finite or negative budget amounts are strictly rejected."""
    # NaN
    proof_path = tmp_path / "nan_budget.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary["study_budget"]["total_budget_usd"] = "NaN"
    data = _valid_terminal_proof_data(final_summary=summary)
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="must be finite|not a valid Decimal"):
        audit_terminal_process_proof(proof_path)

    # Infinity
    proof_path2 = tmp_path / "inf_budget.json"
    summary2 = _valid_terminal_proof_data()["final_summary"].copy()
    summary2["study_budget"]["total_budget_usd"] = "Infinity"
    data2 = _valid_terminal_proof_data(final_summary=summary2)
    proof_path2.write_text(json.dumps(data2), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="must be finite"):
        audit_terminal_process_proof(proof_path2)

    # Negative
    proof_path3 = tmp_path / "neg_budget.json"
    summary3 = _valid_terminal_proof_data()["final_summary"].copy()
    summary3["study_budget"]["total_budget_usd"] = "-1.00"
    data3 = _valid_terminal_proof_data(final_summary=summary3)
    proof_path3.write_text(json.dumps(data3), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="must be strictly positive"):
        audit_terminal_process_proof(proof_path3)


def test_terminal_proof_fails_on_mismatched_nested_money(tmp_path):
    """Probe regression: money conservation violation in study_budget is rejected."""
    proof_path = tmp_path / "drifted_money.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary["study_budget"]["cumulative_settled_cost_usd"] = "10.00000000"
    data = _valid_terminal_proof_data(final_summary=summary)
    proof_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(AuditVerificationError, match="money conservation mismatch"):
        audit_terminal_process_proof(proof_path)


def test_generate_audit_seal_fails_on_tampered_terminal_proof(tmp_path):
    """Direct API: generate_audit_seal validates terminal proof details under is_production=True."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    val_root = REPO_ROOT
    dummy_rec = _create_mock_record("v_0", "no_rag")
    records = {(f"v_{i}", "no_rag"): dummy_rec for i in range(6400)}
    valid_baseline = {
        "all_22_files_verified": True,
        "verified_file_count": 22,
        "baseline_sha": "b" * 64,
        "protocol_canonical_digest": "c" * 64,
        "pricing_contract_sha256": TEST_PRICING_SHA,
    }

    # Tampered exit code
    tampered_proof = _valid_terminal_proof_data(exit_code=1)
    with pytest.raises(AuditVerificationError, match="requires terminal proof exit_code=0"):
        generate_audit_seal(
            exp_dir,
            study_root,
            val_root,
            tmp_path / "seal.json",
            records,
            Decimal("6.57575890"),
            Decimal("13.36160100"),
            is_production=True,
            terminal_proof_info=tampered_proof,
            protected_baseline_info=valid_baseline,
        )

    # Tampered attempts
    tampered_proof2 = _valid_terminal_proof_data()
    tampered_proof2["final_summary"]["requests_consumed"] = 0
    with pytest.raises(AuditVerificationError, match="requires exactly 6,401 attempts"):
        generate_audit_seal(
            exp_dir,
            study_root,
            val_root,
            tmp_path / "seal.json",
            records,
            Decimal("6.57575890"),
            Decimal("13.36160100"),
            is_production=True,
            terminal_proof_info=tampered_proof2,
            protected_baseline_info=valid_baseline,
        )


def test_generate_audit_seal_fails_on_wrong_cost_parameter(tmp_path):
    """Direct API: generate_audit_seal fails closed on wrong cumulative_settled_usd."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    dummy_rec = _create_mock_record("v_0", "no_rag")
    records = {(f"v_{i}", "no_rag"): dummy_rec for i in range(6400)}
    valid_baseline = {
        "all_22_files_verified": True,
        "verified_file_count": 22,
        "baseline_sha": "b" * 64,
        "protocol_canonical_digest": "c" * 64,
        "pricing_contract_sha256": TEST_PRICING_SHA,
    }
    proof = _valid_terminal_proof_data()

    with pytest.raises(
        AuditVerificationError,
        match="Production seal cumulative settled cost parameter mismatch",
    ):
        generate_audit_seal(
            exp_dir,
            study_root,
            REPO_ROOT,
            tmp_path / "seal.json",
            records,
            Decimal("1.00000000"),
            Decimal("13.36160100"),
            is_production=True,
            terminal_proof_info=proof,
            protected_baseline_info=valid_baseline,
        )


def test_generate_audit_seal_fails_on_wrong_available_parameter(tmp_path):
    """Direct API: generate_audit_seal fails closed on wrong uncommitted_avail_usd."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    dummy_rec = _create_mock_record("v_0", "no_rag")
    records = {(f"v_{i}", "no_rag"): dummy_rec for i in range(6400)}
    valid_baseline = {
        "all_22_files_verified": True,
        "verified_file_count": 22,
        "baseline_sha": "b" * 64,
        "protocol_canonical_digest": "c" * 64,
        "pricing_contract_sha256": TEST_PRICING_SHA,
    }
    proof = _valid_terminal_proof_data()

    with pytest.raises(
        AuditVerificationError,
        match="Production seal uncommitted available balance parameter mismatch",
    ):
        generate_audit_seal(
            exp_dir,
            study_root,
            REPO_ROOT,
            tmp_path / "seal.json",
            records,
            Decimal("6.57575890"),
            Decimal("1.00000000"),
            is_production=True,
            terminal_proof_info=proof,
            protected_baseline_info=valid_baseline,
        )


def test_generate_audit_seal_fails_on_money_conservation_violation(tmp_path):
    """Direct API: generate_audit_seal fails when money conservation equation is violated."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    dummy_rec = _create_mock_record("v_0", "no_rag")
    records = {(f"v_{i}", "no_rag"): dummy_rec for i in range(6400)}
    valid_baseline = {
        "all_22_files_verified": True,
        "verified_file_count": 22,
        "baseline_sha": "b" * 64,
        "protocol_canonical_digest": "c" * 64,
        "pricing_contract_sha256": TEST_PRICING_SHA,
    }
    proof = _valid_terminal_proof_data()
    proof["final_summary"]["study_budget"]["prior_pilot_provisional_hold_usd"] = "0.10000000"

    with pytest.raises(
        AuditVerificationError,
        match="Production seal money conservation equation violated",
    ):
        generate_audit_seal(
            exp_dir,
            study_root,
            REPO_ROOT,
            tmp_path / "seal.json",
            records,
            Decimal("6.57575890"),
            Decimal("13.36160100"),
            is_production=True,
            terminal_proof_info=proof,
            protected_baseline_info=valid_baseline,
        )


def test_generate_audit_seal_sanitizes_machine_path(tmp_path):
    """Direct API: generate_audit_seal sanitizes personal machine paths in terminal_proof.path."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    for name in [
        "manifest.json",
        "run_summary.json",
        "request_journal.jsonl",
        "no_rag_predictions.jsonl",
        "rag_k1_predictions.jsonl",
        "rag_k3_predictions.jsonl",
        "rag_k5_predictions.jsonl",
        "rag_k10_predictions.jsonl",
    ]:
        (exp_dir / name).write_text("{}\n", encoding="utf-8")
    study_root = tmp_path / "study"
    study_root.mkdir()
    (study_root / ".study_anchor.json").write_text("{}\n", encoding="utf-8")
    (study_root / "artifacts" / "study_budget").mkdir(parents=True)
    (study_root / "artifacts" / "study_budget" / "study_ledger.json").write_text(
        json.dumps({
            "cumulative_settled_cost_usd": "6.57575890",
            "uncommitted_available_balance_usd": "13.36160100",
        }),
        encoding="utf-8",
    )
    (exp_dir / "run_summary.json").write_text(
        json.dumps({
            "study_budget": {
                "cumulative_settled_cost_usd": "6.57575890",
                "uncommitted_available_balance_usd": "13.36160100",
            }
        }),
        encoding="utf-8",
    )

    dummy_rec = _create_mock_record("v_0", "no_rag")
    records = {(f"v_{i}", "no_rag"): dummy_rec for i in range(6400)}
    valid_baseline = {
        "all_22_files_verified": True,
        "verified_file_count": 22,
        "baseline_sha": "b" * 64,
        "protocol_canonical_digest": "c" * 64,
        "pricing_contract_sha256": TEST_PRICING_SHA,
    }
    proof = _valid_terminal_proof_data()
    proof["path"] = r"D:\RAG2ATT&CK\artifacts\orchestration\terminal_process_proof_20261002.json"

    seal_file = tmp_path / "seal.json"
    seal = generate_audit_seal(
        exp_dir,
        study_root,
        REPO_ROOT,
        seal_file,
        records,
        Decimal("6.57575890"),
        Decimal("13.36160100"),
        is_production=True,
        terminal_proof_info=proof,
        protected_baseline_info=valid_baseline,
    )

    assert seal["terminal_proof"]["path"] == "artifacts/orchestration/terminal_process_proof_20261002.json"
    assert "D:" not in seal["terminal_proof"]["path"]


def test_cli_fails_on_mismatched_run_summary_and_proof(tmp_path):
    """Production CLI strictly rejects mismatched run_summary and terminal proof attempts."""
    exp_dir = tmp_path / "exp"
    exp_dir.mkdir()
    study_root = tmp_path / "study"
    study_root.mkdir()
    (study_root / "scripts").mkdir()
    launcher_path = study_root / "scripts" / "run_experiments.py"
    launcher_path.write_text("#!/usr/bin/env python\n", encoding="utf-8")

    dummy_log = tmp_path / "task.log"
    dummy_log.write_bytes(b"authoritative log\n")
    log_sha = hashlib.sha256(dummy_log.read_bytes()).hexdigest()

    (exp_dir / "manifest.json").write_text(
        json.dumps({"execution_mode": "live", "run_id": "live-66b94b1676bf46a9"}), encoding="utf-8"
    )
    (exp_dir / "run_summary.json").write_text(
        json.dumps({
            "complete": True,
            "record_count": 6400,
            "requests_consumed": 6401,
            "consumed_provider_attempts": 6401,
        }),
        encoding="utf-8",
    )

    proof_file = tmp_path / "proof_mismatch.json"
    summary = _valid_terminal_proof_data()["final_summary"].copy()
    summary["requests_consumed"] = 5000
    summary["consumed_provider_attempts"] = 5000
    proof_data = _valid_terminal_proof_data(
        artifact_log_sha256=log_sha,
        final_summary=summary,
    )
    proof_data["authoritative_log"] = str(dummy_log)
    proof_file.write_text(json.dumps(proof_data), encoding="utf-8")

    with pytest.raises(AuditVerificationError, match="mismatch|Canonical live run expects"):
        main(
            [
                "--exp-dir",
                str(exp_dir),
                "--study-root",
                str(study_root),
                "--terminal-proof-file",
                str(proof_file),
                "--log-file-path",
                str(dummy_log),
                "--is-production",
            ]
        )

