"""Unit tests for Phase S2 Terminal Audit Script using isolated offline fixtures."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.audit_terminal_run import (
    AuditVerificationError,
    audit_completeness_and_cardinality,
    audit_financial_ledger_and_tariffs,
    audit_journal_join_and_lifecycle,
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
    proof_file.write_text(json.dumps({"exit_code": 0, "pid": 1234}), encoding="utf-8")
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
    bad_proof.write_text(json.dumps({"exit_code": 1}), encoding="utf-8")
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
        json.dumps({"exit_code": 0, "task_id": "task-1264", "pid": 50192}), encoding="utf-8"
    )
    info = audit_terminal_process_proof(proof_path)
    assert info["exit_code"] == 0
    assert info["task_id"] == "task-1264"
    assert info["pid"] == 50192
    assert len(info["sha256"]) == 64


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
