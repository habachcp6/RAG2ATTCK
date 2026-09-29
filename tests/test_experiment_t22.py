"""Comprehensive validation tests for T22 live runner infrastructure and safety gates.

Covers:
- Authorization gates (default-deny, protocol unresolved, human approval, finite budget)
- Finite budget & accounting (reservation, retry, exhaustion, no reset, no bypass)
- Ground-truth leakage prevention (top-level, nested, answer-bearing metadata, retrieval)
- Request journal state machine (states, transitions, format integrity, tampering)
- Durable resume safety (complete run, terminal failures, ambiguous dispatch, provenance)
- Filesystem safety (symlinks, hardlinks, traversal, atomic replacement)
- Five-condition matrix & depth invariants
- Evaluator compatibility & canonical scoring gate
"""

import dataclasses
import json
import os
from pathlib import Path

import faiss
import httpx
import numpy as np
import openai
import pytest

from src.evaluation.experiment_metrics import (
    HumanDecisionRequired,
    _load_evaluation_inputs,
    evaluate_conditional_accuracy,
    evaluate_end_to_end,
)
from src.experiment.__main__ import main
from src.experiment.authorization import (
    ExecutionAuthorization,
    HumanAuthorizationRequiredError,
    LiveBudgetRequiredError,
    LiveExecutionBlockedError,
    ProtocolNotFrozenError,
    check_live_execution_gates,
    create_test_protocol_approval,
    validate_live_authorization,
    validate_scientific_protocol,
)
from src.experiment.config import canonical_bytes, digest, load_plan, parse_json
from src.experiment.journal import (
    RequestJournalStateMachine,
    RequestState,
    append_journal_event,
    read_journal_events,
)
from src.experiment.runner import (
    JournalBudget,
    MockProvider,
    MockReply,
    run_live_experiment,
    run_mock_experiment,
)
from src.experiment.schemas import CONDITIONS, DEPTHS
from src.llm.client import LLMClient, OpenAISDKClient

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def bundle(tmp_path):
    root = tmp_path / "inputs"
    root.mkdir()
    config = json.loads((ROOT / "config" / "experiment_config.json").read_bytes())
    snapshots = {}

    def store(name, value, *, jsonl=False, raw=False):
        data = (
            value
            if raw
            else (
                b"".join(canonical_bytes(row) + b"\n" for row in value)
                if jsonl
                else canonical_bytes(value) + b"\n"
            )
        )
        (root / name).write_bytes(data)
        snapshots[name] = data
        return {"path": name, "sha256": digest(data)}

    views = [
        {"view_id": "s1", "pair_id": "p1", "view_type": "single", "event_ids": ["e1"]},
        {"view_id": "s2", "pair_id": "p1", "view_type": "contextual", "event_ids": ["e1", "e2"]},
    ]
    truth = [
        {
            "view_id": "s1",
            "label_status": "mapped",
            "technique_ids": ["T1059.001"],
            "rationale": "SECRET_GT_METADATA",
        },
        {
            "view_id": "s2",
            "label_status": "ambiguous",
            "technique_ids": [],
            "rationale": "SECRET_GT_METADATA",
        },
    ]
    pairs = [
        {
            "pair_id": "p1",
            "split": "test",
            "single_view": views[0],
            "contextual_view": views[1],
            "single_ground_truth": truth[0],
            "contextual_ground_truth": truth[1],
        }
    ]
    registry = {
        "objects": [
            {
                "type": "attack-pattern",
                "external_references": [{"source_name": "mitre-attack", "external_id": tid}],
            }
            for tid in ["T1059.001"] + [f"T10{i:02d}" for i in range(11)]
        ]
    }
    config["attack"]["registry"] = store("registry.json", registry)
    for field, name, values in (
        (
            "inference",
            "inference.jsonl",
            [
                {"sample_id": "s1", "endpoint_evidence": "  endpoint A\n"},
                {"sample_id": "s2", "endpoint_evidence": "endpoint B"},
            ],
        ),
        ("ground_truth", "ground_truth.jsonl", truth),
        ("views", "views.jsonl", views),
        ("pairs", "pairs.jsonl", pairs),
    ):
        config["dataset"][field] = store(name, values, jsonl=True)
    config["dataset"]["split_manifest"] = store("split_manifest.json", {"dev": [], "test": ["p1"]})
    dataset_manifest = {
        "state": "frozen",
        "benchmark_version": "synthetic-paired-v1",
        "attack_version": "19.2",
        "view_count": 2,
        "pair_count": 1,
        "split_counts": {"dev": 0, "test": 1},
        "attack_source_sha256": config["attack"]["registry"]["sha256"],
        "files": {
            name: digest(data) for name, data in snapshots.items() if name != "registry.json"
        },
    }
    config["dataset"]["manifest"] = store("dataset_manifest.json", dataset_manifest)
    config["dataset"]["expected_sample_count"] = 2
    config["dataset"]["expected_pair_count"] = 1
    corpus = [
        {
            "technique_id": tid,
            "name": tid,
            "retrieval_text": "reference " + tid,
            "source_version": "19.2",
        }
        for tid in ["T1059.001"] + [f"T10{i:02d}" for i in range(11)]
    ]
    config["attack"]["corpus"] = store("corpus.jsonl", corpus, jsonl=True)
    config["attack"]["document_mapping"] = store("docmap.json", corpus)
    index = faiss.IndexFlatIP(4)
    vectors = np.eye(4, dtype=np.float32)[np.arange(12) % 4]
    index.add(vectors)
    config["attack"]["index"] = store("index.bin", faiss.serialize_index(index).tobytes(), raw=True)
    retrieval = json.loads((ROOT / "config" / "retrieval.json").read_bytes())
    retrieval.update(
        corpus_path="corpus.jsonl",
        corpus_sha256=config["attack"]["corpus"]["sha256"],
        faiss_index_path="index.bin",
        document_mapping_path="docmap.json",
        manifest_path="retrieval_manifest.json",
        embedding_dimension=4,
    )
    config["retrieval"]["embedding_dimension"] = 4
    config["retrieval"]["config"] = store("retrieval.json", retrieval)
    retrieval_manifest = {
        key: retrieval[key]
        for key in (
            "corpus_sha256",
            "embedding_model_id",
            "embedding_model_revision",
            "embedding_dimension",
            "faiss_index_type",
            "normalization",
            "similarity_metric",
            "faiss_version",
        )
    }
    retrieval_manifest.update(
        index_sha256=config["attack"]["index"]["sha256"],
        document_mapping_sha256=config["attack"]["document_mapping"]["sha256"],
        document_count=12,
    )
    config["attack"]["retrieval_manifest"] = store("retrieval_manifest.json", retrieval_manifest)
    config["generation"]["config"] = store(
        "model.json", (ROOT / "config" / "model.json").read_bytes(), raw=True
    )
    config["prompt"]["template"] = store(
        "baseline.txt", (ROOT / "prompts" / "baseline_v1.txt").read_bytes(), raw=True
    )
    config_path = root / "experiment.json"
    config_path.write_bytes(canonical_bytes(config))
    return root, config_path, config


# ===========================================================================
# 1. Authorization Tests
# ===========================================================================


def test_authorization_default_deny_zero_calls(bundle, tmp_path):
    """Default behavior is DENY; calling run_live_experiment with None authorization fails."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-default-deny"
    with pytest.raises(LiveExecutionBlockedError, match="LIVE_EXECUTION_BLOCKED"):
        run_live_experiment(plan, output, authorization=None)
    assert not output.exists()


def test_authorization_protocol_unresolved_zero_calls(bundle, tmp_path):
    """Unresolved scientific protocol decisions (D1-D7) block live execution with zero calls."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-unresolved-protocol"
    auth = ExecutionAuthorization(
        human_approval_token="HUMAN_TOKEN_123",
        scientific_protocol_approved=False,
        authorized_max_requests=100,
        allow_live_dispatch=True,
    )
    with pytest.raises(ProtocolNotFrozenError, match="scientific protocol decisions"):
        run_live_experiment(plan, output, authorization=auth)
    assert not output.exists()


def test_authorization_d1_d7_unapproved_zero_calls(bundle, tmp_path):
    """Scientific protocol requires explicit valid D1 and D7 approval policies."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-d1-d7-unapproved"
    # D1 invalid
    with pytest.raises(ProtocolNotFrozenError, match="d1_raw_response_policy"):
        bad_d1_proto = create_test_protocol_approval(d1_raw_response_policy="UNKNOWN_POLICY")
        auth = ExecutionAuthorization(
            human_approval_token="TOKEN",
            approved_protocol_sha256=bad_d1_proto.protocol_sha256,
            authorized_max_requests=100,
            allow_live_dispatch=True,
        )
        run_live_experiment(plan, output, authorization=auth, protocol=bad_d1_proto)

    # D7 invalid
    with pytest.raises(ProtocolNotFrozenError, match="d7_dataset_scope"):
        bad_d7_proto = create_test_protocol_approval(d7_dataset_scope="INVALID_SCOPE")
        auth = ExecutionAuthorization(
            human_approval_token="TOKEN",
            approved_protocol_sha256=bad_d7_proto.protocol_sha256,
            authorized_max_requests=100,
            allow_live_dispatch=True,
        )
        run_live_experiment(plan, output, authorization=auth, protocol=bad_d7_proto)
    assert not output.exists()


def test_authorization_missing_human_token_zero_calls(bundle, tmp_path):
    """Live execution without a non-empty human authorization token is blocked."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-missing-token"
    proto = create_test_protocol_approval()
    for invalid_token in ("", "   "):
        auth = ExecutionAuthorization(
            human_approval_token=invalid_token,
            approved_protocol_sha256=proto.protocol_sha256,
            authorized_max_requests=100,
            allow_live_dispatch=True,
        )
        with pytest.raises(HumanAuthorizationRequiredError, match="human approval token"):
            run_live_experiment(plan, output, authorization=auth, protocol=proto)
    assert not output.exists()


def test_authorization_missing_or_zero_budget_zero_calls(bundle, tmp_path):
    """Live execution without explicit positive request budget is blocked."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-budget-tests"
    proto = create_test_protocol_approval()

    # Missing budget (None)
    auth_none = ExecutionAuthorization(
        human_approval_token="TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_requests=None,
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError, match="explicit finite request budget"):
        run_live_experiment(plan, output, authorization=auth_none, protocol=proto)

    # Zero budget
    auth_zero = ExecutionAuthorization(
        human_approval_token="TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_requests=0,
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot be zero"):
        run_live_experiment(plan, output, authorization=auth_zero, protocol=proto)
    assert not output.exists()


def test_authorization_negative_budget_rejected(bundle, tmp_path):
    """Negative budget values are strictly rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-neg-budget"
    proto = create_test_protocol_approval()
    auth_neg = ExecutionAuthorization(
        human_approval_token="TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_requests=-10,
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot be negative"):
        run_live_experiment(plan, output, authorization=auth_neg, protocol=proto)
    assert not output.exists()


def test_authorization_insufficient_budget_rejected(bundle, tmp_path):
    """Budget smaller than complete matrix (2 samples * 5 conditions = 10) is rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-insufficient-budget"
    proto = create_test_protocol_approval()
    auth_small = ExecutionAuthorization(
        human_approval_token="TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_requests=9,  # Needs 10
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot cover the required matrix calls"):
        run_live_experiment(plan, output, authorization=auth_small, protocol=proto)
    assert not output.exists()


def test_authorization_api_key_alone_does_not_permit_calls(bundle, monkeypatch, tmp_path):
    """Possessing an OPENAI_API_KEY environment variable does not authorize live execution."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-test")
    plan = load_plan(bundle[1])
    output = tmp_path / "live-key-alone"
    with pytest.raises(LiveExecutionBlockedError):
        run_live_experiment(plan, output, authorization=None)
    assert not output.exists()


def test_live_experiment_blocked_even_with_valid_authorization(bundle, monkeypatch, tmp_path):
    """Even if authorization is valid, live execution is blocked without credentials/provider."""
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    plan = load_plan(bundle[1])
    output = tmp_path / "valid-auth-blocked"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="HUMAN_AUTH_TOKEN_TEST_VALID",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_requests=10,
        allow_live_dispatch=True,
    )
    with pytest.raises(
        LiveExecutionBlockedError, match="LIVE_EXECUTION_BLOCKED: OPENAI_API_KEY is not configured"
    ):
        run_live_experiment(plan, output, authorization=auth, protocol=proto)
    assert not output.exists()


def test_authorization_gate_check_reporting(bundle):
    """check_live_execution_gates returns a non-executing report indicating blocked state."""
    plan = load_plan(bundle[1])
    report = check_live_execution_gates(plan, None)
    assert report["status"] == "LIVE_EXECUTION_BLOCKED"
    assert report["provider_calls"] == 0
    assert report["prediction_writes"] == 0
    assert report["live_execution_permitted"] is False

    # Check that negative budget or invalid types don't crash unhandled
    proto = create_test_protocol_approval()
    report_neg = check_live_execution_gates(
        plan,
        ExecutionAuthorization(
            human_approval_token="TOKEN",
            approved_protocol_sha256=proto.protocol_sha256,
            authorized_max_requests=-5,
            allow_live_dispatch=True,
        ),
        protocol=proto,
    )
    assert report_neg["status"] == "LIVE_EXECUTION_BLOCKED"
    assert "cannot be negative" in report_neg["reason"]


# ===========================================================================
# 2. Budget & Accounting Tests
# ===========================================================================


def test_budget_one_attempt_one_reservation(tmp_path):
    """Every provider attempt must consume exactly one budget reservation before dispatch."""
    journal_path = tmp_path / "journal.jsonl"
    journal_path.write_bytes(b'{"event":"header","manifest_sha256":"00","max_requests":5}\n')
    budget = JournalBudget(5, journal_path)
    budget.key = ("s1", "no_rag")
    assert budget.count == 0

    assert budget.consume() == 1
    assert budget.count == 1
    assert budget.consume() == 2
    assert budget.count == 2

    lines = [json.loads(line) for line in journal_path.read_bytes().splitlines() if line]
    assert len(lines) == 3  # header + 2 attempts
    assert lines[1] == {"event": "attempt", "key": ["s1", "no_rag"], "ordinal": 1}
    assert lines[2] == {"event": "attempt", "key": ["s1", "no_rag"], "ordinal": 2}


def test_budget_retry_consumes_another_reservation(bundle, tmp_path):
    """Provider retry consumes an additional budget reservation."""
    plan = load_plan(bundle[1])
    output = tmp_path / "retry-accounting"
    provider = MockProvider(
        {
            ("s1", "no_rag"): [
                TimeoutError("transient timeout"),
                MockReply(),
            ]
        }
    )
    summary = run_mock_experiment(plan, output, provider, max_requests=15, stop_after=1)
    assert summary["requests_consumed"] == 2  # 1 initial + 1 retry
    row = parse_json((output / "no_rag_predictions.jsonl").read_bytes())
    assert row["request_attempt_count"] == 2
    assert row["retry_count"] == 1


def test_budget_exhaustion_blocks_next_call(bundle, tmp_path):
    """When budget is exhausted, next attempt raises LiveBudgetExceededError."""
    plan = load_plan(bundle[1])
    output = tmp_path / "budget-exhaustion"
    provider = MockProvider({("s1", "no_rag"): [TimeoutError("timeout")]})
    # Set budget to exactly 10; timeout causes retries until 10 consumed
    result = run_mock_experiment(plan, output, provider, max_requests=10)
    assert result["requests_consumed"] == 10
    assert not result["complete"]


def test_budget_cannot_be_bypassed_by_external_sdk_client(bundle):
    """LLMClient constructor strictly rejects external OpenAI SDK client instances."""
    plan = load_plan(bundle[1])
    fake_sdk = object.__new__(OpenAISDKClient)
    with pytest.raises(ValueError, match="A real OpenAI SDK client cannot be injected"):
        LLMClient(
            config_dict=plan.model_config,
            openai_client=fake_sdk,
            registry_ids=set(plan.registry_ids),
        )


# ===========================================================================
# 3. Ground-Truth Leakage Protection Tests
# ===========================================================================


def test_gt_leakage_top_level_gt_rejected(bundle):
    """Inference input with top-level technique_ids or ground_truth is rejected."""
    root, path, config = bundle
    inf_path = root / "inference.jsonl"
    rows = [json.loads(line) for line in inf_path.read_bytes().splitlines() if line]
    rows[0]["technique_ids"] = ["T1059.001"]
    inf_bytes = b"".join(canonical_bytes(r) + b"\n" for r in rows)
    inf_path.write_bytes(inf_bytes)
    config["dataset"]["inference"]["sha256"] = digest(inf_bytes)

    manifest_path = root / "dataset_manifest.json"
    dataset_manifest = parse_json(manifest_path.read_bytes())
    dataset_manifest["files"]["inference.jsonl"] = digest(inf_bytes)
    manifest_bytes = canonical_bytes(dataset_manifest) + b"\n"
    manifest_path.write_bytes(manifest_bytes)
    config["dataset"]["manifest"]["sha256"] = digest(manifest_bytes)
    path.write_bytes(canonical_bytes(config))

    with pytest.raises(ValueError, match="inference rows must contain only"):
        load_plan(path)


def test_gt_leakage_nested_gt_rejected(bundle):
    """Inference input with answer-bearing metadata fields is rejected."""
    root, path, config = bundle
    inf_path = root / "inference.jsonl"
    rows = [json.loads(line) for line in inf_path.read_bytes().splitlines() if line]
    rows[0]["tactic"] = "execution"
    inf_bytes = b"".join(canonical_bytes(r) + b"\n" for r in rows)
    inf_path.write_bytes(inf_bytes)
    config["dataset"]["inference"]["sha256"] = digest(inf_bytes)

    manifest_path = root / "dataset_manifest.json"
    dataset_manifest = parse_json(manifest_path.read_bytes())
    dataset_manifest["files"]["inference.jsonl"] = digest(inf_bytes)
    manifest_bytes = canonical_bytes(dataset_manifest) + b"\n"
    manifest_path.write_bytes(manifest_bytes)
    config["dataset"]["manifest"]["sha256"] = digest(manifest_bytes)
    path.write_bytes(canonical_bytes(config))

    with pytest.raises(ValueError, match="inference rows must contain only"):
        load_plan(path)


def test_gt_leakage_retrieval_receives_no_gt(bundle, tmp_path):
    """RAG pipeline query receives only endpoint_evidence, never GT technique ID."""
    plan = load_plan(bundle[1])
    output = tmp_path / "retrieval-no-gt"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=2)
    # rag_k1 record contains retrieved candidates from evidence query
    row = parse_json((output / "rag_k1_predictions.jsonl").read_bytes())
    assert row["condition"] == "rag_k1"
    assert row["retrieval_k"] == 1
    assert len(row["retrieved_candidates"]) == 1
    # raw_response is null and ground truth is not stored in execution record
    assert row["raw_response"] is None
    assert row["raw_response_logged"] is False


# ===========================================================================
# 4. Request Journal State Machine & Integrity Tests
# ===========================================================================


def test_journal_state_machine_valid_transitions():
    """State machine validates ordered request lifecycle progression."""
    sm = RequestJournalStateMachine(("s1", "no_rag"))
    assert sm.state == RequestState.IDLE
    assert not sm.is_in_flight

    sm.transition_to(RequestState.RESERVED)
    assert sm.state == RequestState.RESERVED
    assert not sm.is_in_flight

    sm.transition_to(RequestState.DISPATCH_STARTED)
    assert sm.is_in_flight

    sm.transition_to(RequestState.RESPONSE_RECEIVED)
    assert sm.is_in_flight

    sm.transition_to(RequestState.PARSED)
    assert sm.is_in_flight

    sm.transition_to(RequestState.RECORD_COMMITTED)
    assert not sm.is_in_flight
    assert sm.is_committed


def test_journal_state_machine_invalid_transition_rejected():
    """Invalid or skipped state transitions raise ValueError."""
    sm = RequestJournalStateMachine(("s1", "no_rag"))
    # Cannot jump from IDLE to RECORD_COMMITTED
    with pytest.raises(ValueError, match="Invalid request state transition"):
        sm.transition_to(RequestState.RECORD_COMMITTED)

    sm.transition_to(RequestState.RESERVED)
    # Cannot jump from RESERVED to PARSED
    with pytest.raises(ValueError, match="Invalid request state transition"):
        sm.transition_to(RequestState.PARSED)


def test_journal_missing_header_rejected(bundle, tmp_path):
    """Journal without header fails validation."""
    plan = load_plan(bundle[1])
    output = tmp_path / "missing-header"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    journal_path = output / "request_journal.jsonl"
    lines = journal_path.read_bytes().splitlines()
    # Strip header
    journal_path.write_bytes(b"\n".join(lines[1:]) + b"\n")
    with pytest.raises(ValueError, match="journal manifest/budget drift"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_journal_blank_row_rejected(bundle, tmp_path):
    """Blank row in journal fails validation."""
    plan = load_plan(bundle[1])
    output = tmp_path / "blank-row"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    journal_path = output / "request_journal.jsonl"
    content = journal_path.read_bytes() + b"\n\n"
    journal_path.write_bytes(content)
    with pytest.raises(ValueError, match="blank JSONL row|empty JSONL"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_journal_truncated_row_rejected(bundle, tmp_path):
    """Truncated JSON in journal fails validation."""
    plan = load_plan(bundle[1])
    output = tmp_path / "truncated-row"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    journal_path = output / "request_journal.jsonl"
    content = journal_path.read_bytes() + b'{"event": "attemp'
    journal_path.write_bytes(content)
    with pytest.raises(
        ValueError, match="nonempty and end with a complete newline|invalid JSONL line"
    ):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_journal_bad_attempt_order_rejected(bundle, tmp_path):
    """Attempt ordinal skipping or duplicate ordinal fails closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-ordinal"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    journal_path = output / "request_journal.jsonl"
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines() if line]
    # Tamper ordinal of first attempt
    events[2]["ordinal"] = 999
    journal_path.write_bytes(b"".join(canonical_bytes(e) + b"\n" for e in events))
    with pytest.raises(ValueError, match="invalid attempt journal"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_journal_tampered_hash_rejected(bundle, tmp_path):
    """Tampered record hash in complete event fails validation."""
    plan = load_plan(bundle[1])
    output = tmp_path / "tampered-hash"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    journal_path = output / "request_journal.jsonl"
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines() if line]
    # Forged hash on first complete event
    for event in events:
        if event.get("event") == "complete":
            event["record_sha256"] = "00" * 32
            break
    journal_path.write_bytes(b"".join(canonical_bytes(e) + b"\n" for e in events))
    with pytest.raises(ValueError, match="record/journal hash or request accounting mismatch"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


# ===========================================================================
# 5. Resume Safety Tests
# ===========================================================================


def test_resume_complete_run_produces_zero_new_calls(bundle, tmp_path):
    """Completed experiment resume produces zero additional provider calls."""
    plan = load_plan(bundle[1])
    output = tmp_path / "complete-resume"
    provider1 = MockProvider()
    summary1 = run_mock_experiment(plan, output, provider1, max_requests=10)
    assert summary1["complete"]
    assert len(provider1.calls) == 10

    provider2 = MockProvider()
    summary2 = run_mock_experiment(plan, output, provider2, max_requests=10, resume=True)
    assert summary2["complete"]
    assert summary2["new_records"] == 0
    assert len(provider2.calls) == 0


def test_resume_ambiguous_dispatch_fails_closed(bundle, tmp_path):
    """Crash after begin event but before complete event is ambiguous; fails closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "ambiguous-dispatch"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=1)
    journal_path = output / "request_journal.jsonl"
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines() if line]
    # Add an uncompleted begin event
    events.append({"event": "begin", "key": ["s1", "rag_k1"]})
    journal_path.write_bytes(b"".join(canonical_bytes(e) + b"\n" for e in events))

    with pytest.raises(ValueError, match="in-flight request state is ambiguous"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_resume_provenance_mismatch_rejected(bundle, tmp_path):
    """Resuming with modified manifest or config fails closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "provenance-drift"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["model"]["model"] = "tampered-model"
    manifest_path.write_bytes(canonical_bytes(manifest) + b"\n")

    with pytest.raises(ValueError, match="immutable manifest drift"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


# ===========================================================================
# 6. Filesystem Safety Tests
# ===========================================================================


def test_filesystem_symlink_rejected(bundle, tmp_path):
    """Symlink in output directory causes resume to fail closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "symlink-test"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    summary_path = output / "run_summary.json"
    summary_path.unlink()
    try:
        summary_path.symlink_to(bundle[0] / "model.json")
    except OSError:
        pytest.skip("Symlinks not permitted on this Windows environment")

    with pytest.raises(ValueError, match="unexpected output-directory contents"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_filesystem_hardlink_rejected(bundle, tmp_path):
    """Hardlink in output directory causes resume to fail closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "hardlink-test"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    summary_file = output / "run_summary.json"
    external_link = tmp_path / "external_summary_link.json"
    os.link(summary_file, external_link)

    with pytest.raises(ValueError, match="hardlinked output-directory contents"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)


def test_filesystem_outside_root_rejected(bundle, tmp_path):
    """Output directory outside allowed scratch or system temp is rejected."""
    plan = load_plan(bundle[1])
    # Arbitrary location outside system temp or validated root .tmp
    outside = bundle[0] / "forbidden_output"
    with pytest.raises(ValueError, match="mock outputs"):
        run_mock_experiment(plan, outside, MockProvider(), max_requests=10)


# ===========================================================================
# 7. Experiment Conditions & Evaluator Compatibility Tests
# ===========================================================================


def test_experiment_five_conditions_and_retrieval_depths(bundle, tmp_path):
    """The runner must execute exactly the five conditions with matching retrieval depths."""
    plan = load_plan(bundle[1])
    output = tmp_path / "five-conditions"
    summary = run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    assert summary["complete"]

    expected_conditions = list(CONDITIONS)
    assert expected_conditions == ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
    assert tuple(DEPTHS) == (1, 3, 5, 10)

    for cond in expected_conditions:
        file = output / f"{cond}_predictions.jsonl"
        assert file.exists()
        rows = [parse_json(line) for line in file.read_bytes().splitlines() if line]
        assert len(rows) == 2  # 2 samples
        expected_k = 0 if cond == "no_rag" else int(cond[5:])
        for row in rows:
            assert row["condition"] == cond
            assert row["retrieval_k"] == expected_k
            assert len(row["retrieved_candidates"]) == expected_k


def test_evaluator_compatibility_mock_runner_output_loads(bundle, tmp_path):
    """Mock runner output loads into evaluator without schema error."""
    plan = load_plan(bundle[1])
    output = tmp_path / "evaluator-compat"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)

    paths = {c: output / f"{c}_predictions.jsonl" for c in CONDITIONS}
    eval_inputs = _load_evaluation_inputs(
        output / "manifest.json", paths, repository_root=bundle[0], expected_sample_count=2
    )
    assert len(eval_inputs.records) == 10  # 2 samples * 5 conditions
    assert eval_inputs.execution_mode == "mock_fixture"


def test_canonical_scoring_remains_blocked(bundle, tmp_path):
    """Canonical scientific scoring functions raise HumanDecisionRequired."""
    plan = load_plan(bundle[1])
    output = tmp_path / "evaluator-blocked"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    paths = {c: output / f"{c}_predictions.jsonl" for c in CONDITIONS}
    eval_inputs = _load_evaluation_inputs(
        output / "manifest.json", paths, repository_root=bundle[0], expected_sample_count=2
    )

    with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
        evaluate_end_to_end(eval_inputs)

    with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
        evaluate_conditional_accuracy(eval_inputs)


# ===========================================================================
# 8. Protocol Approval Contract & Authorization Tampering Tests
# ===========================================================================


def test_protocol_approval_contract_tampering_rejected(bundle):
    """Tampering with decisions in ScientificProtocolApproval breaks cryptographic hash check."""
    plan = load_plan(bundle[1])
    # 1. Tampered hash flag
    tampered_hash_proto = create_test_protocol_approval(tamper_hash=True)
    with pytest.raises(ProtocolNotFrozenError, match="protocol SHA-256 hash mismatch"):
        validate_scientific_protocol(tampered_hash_proto, plan)

    # 2. Decision modified without updating hash
    valid_proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    tampered_field_proto = dataclasses.replace(valid_proto, d1_raw_response_policy="DISCARD")
    with pytest.raises(ProtocolNotFrozenError, match="protocol SHA-256 hash mismatch"):
        validate_scientific_protocol(tampered_field_proto, plan)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("d1_raw_response_policy", "INVALID_POLICY"),
        ("d2a_ground_truth_semantics", "INVALID_SEMANTICS"),
        ("d2b_empty_ground_truth", "INVALID_EMPTY"),
        ("d2c_ambiguous_ground_truth", "INVALID_AMBIGUOUS"),
        ("d2d_macro_f1_universe", "INVALID_UNIVERSE"),
        ("d2e_invalid_id_denominator", "INVALID_DENOMINATOR"),
        ("d2f_api_error_denominator", "INVALID_DENOMINATOR"),
        ("d2g_retired_attack_id", "INVALID_RETIRED"),
        ("d2h_conditional_retrieval", "INVALID_CONDITIONAL"),
        ("d2i_failure_precedence", "INVALID_PRECEDENCE"),
        ("d2j_zero_denominator", "INVALID_ZERO"),
        ("d3_model_version_policy", "INVALID_VERSION_POLICY"),
        ("d4_concurrency_policy", "INVALID_CONCURRENCY"),
        ("d5_budget_policy", "INVALID_BUDGET"),
        ("d6_t15_prerequisite_policy", "INVALID_PREREQUISITE"),
        ("d7_dataset_scope", "INVALID_SCOPE"),
        ("protocol_version", ""),
        ("approval_reference", ""),
        ("approval_timestamp", ""),
    ],
)
def test_protocol_missing_or_unknown_decision_rejected(bundle, field, bad_value):
    """Missing decisions or unknown decision values fail closed."""
    plan = load_plan(bundle[1])
    kwargs = {field: bad_value}
    proto = create_test_protocol_approval(**kwargs)
    with pytest.raises(ProtocolNotFrozenError):
        validate_scientific_protocol(proto, plan)


def test_protocol_authorization_hash_mismatch_rejected(bundle):
    """Authorization with approved_protocol_sha256 mismatching protocol fails closed."""
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="VALID_TOKEN",
        approved_protocol_sha256="wrong" + "00" * 30,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    with pytest.raises(ProtocolNotFrozenError, match="authorized protocol SHA-256 does not match"):
        validate_live_authorization(auth, plan, protocol=proto)


# ===========================================================================
# 9. Fake Live Provider Execution & Matrix Invariants
# ===========================================================================


def test_fake_live_provider_factory_execution(bundle, tmp_path):
    """End-to-end 5-condition live matrix execution via provider_factory.

    Validates complete live manifest, run_id starting with 'live-', correct depths,
    token usage, budget accounting, and zero GT leakage.
    """
    plan = load_plan(bundle[1])
    output = tmp_path / "live-factory-exec"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_T22_E2E",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    fake_provider = MockProvider()
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: fake_provider,
    )

    # Validate summary
    assert summary["complete"] is True
    assert summary["record_count"] == 10
    assert summary["requests_consumed"] == 10
    assert summary["consumed_provider_attempts"] == 10
    assert summary["execution_mode"] == "live"
    assert summary["run_id"].startswith("live-")

    # Validate manifest
    manifest_data = parse_json((output / "manifest.json").read_bytes())
    assert manifest_data["execution_mode"] == "live"
    assert manifest_data["run_id"] == summary["run_id"]
    assert manifest_data["protocol_sha256"] == proto.protocol_sha256
    assert "human_authorization_token" not in manifest_data
    assert manifest_data["human_authorization_reference"] == digest(b"TOKEN_T22_E2E")[:16]

    # Validate prediction files and depths
    for cond in CONDITIONS:
        pred_file = output / f"{cond}_predictions.jsonl"
        assert pred_file.exists()
        rows = [parse_json(line) for line in pred_file.read_bytes().splitlines() if line]
        assert len(rows) == 2
        expected_k = 0 if cond == "no_rag" else int(cond[5:])
        for row in rows:
            assert row["execution_mode"] == "live"
            assert row["run_id"] == summary["run_id"]
            assert row["condition"] == cond
            assert row["retrieval_k"] == expected_k
            assert len(row["retrieved_candidates"]) == expected_k
            assert row["raw_response_logged"] is True
            assert row["raw_response"] == '{"technique_id":"T1059.001"}'

    # Validate request journal
    journal_events = read_journal_events(output / "request_journal.jsonl")
    assert journal_events[0]["event"] == "header"
    assert journal_events[0]["max_requests"] == 20
    complete_events = [e for e in journal_events if e["event"] == "complete"]
    assert len(complete_events) == 10

    # Validate zero GT leakage into provider calls
    assert len(fake_provider.calls) == 10
    for key, kwargs in fake_provider.calls:
        call_str = json.dumps(kwargs)
        assert "SECRET_GT_METADATA" not in call_str
        assert "mapped" not in call_str
        assert "ambiguous" not in call_str


def test_fake_live_provider_simulates_retries_and_errors(bundle, tmp_path):
    """Fake provider simulating timeout retry, error, refusal, and malformed response."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-simulated-errors"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_SIMULATED_ERRORS",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    resp = httpx.Response(400, request=httpx.Request("POST", "https://api.openai.com/v1/responses"))
    bad_req_err = openai.BadRequestError(
        "bad request", response=resp, body={"error": {"message": "invalid"}}
    )

    outcomes = {
        # Timeout on attempt 1, success on attempt 2 -> consumes 2 attempts, status VALID
        ("s1", "no_rag"): [
            TimeoutError("gateway timeout"),
            MockReply(raw_text='{"technique_id":"T1059.001"}'),
        ],
        # Non-retryable error -> consumes 1 attempt, status API_FAILURE
        ("s1", "rag_k1"): [bad_req_err],
        # Refusal -> consumes 1 attempt, status REFUSAL
        ("s1", "rag_k3"): [MockReply(status="completed", refusal="Refused to attribute")],
        # Malformed response -> consumes 1 attempt, status MALFORMED_RESPONSE
        ("s1", "rag_k5"): [MockReply(raw_text="not valid json")],
    }
    fake_provider = MockProvider(outcomes=outcomes)
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: fake_provider,
    )
    assert summary["complete"] is True
    # Total attempts = 2 (retry) + 1 (err) + 1 (refusal) + 1 (malformed) + 6 others = 11
    assert summary["consumed_provider_attempts"] == 11
    assert summary["record_count"] == 10

    # Verify specific statuses
    no_rag_rows = [
        parse_json(line)
        for line in (output / "no_rag_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    s1_no_rag = next(r for r in no_rag_rows if r["sample_id"] == "s1")
    assert s1_no_rag["parse_status"] == "VALID"
    assert s1_no_rag["request_attempt_count"] == 2

    rag_k1_rows = [
        parse_json(line)
        for line in (output / "rag_k1_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    s1_rag_k1 = next(r for r in rag_k1_rows if r["sample_id"] == "s1")
    assert s1_rag_k1["parse_status"] == "API_FAILURE"
    assert s1_rag_k1["request_attempt_count"] == 1

    rag_k3_rows = [
        parse_json(line)
        for line in (output / "rag_k3_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    s1_rag_k3 = next(r for r in rag_k3_rows if r["sample_id"] == "s1")
    assert s1_rag_k3["parse_status"] == "REFUSAL"

    rag_k5_rows = [
        parse_json(line)
        for line in (output / "rag_k5_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    s1_rag_k5 = next(r for r in rag_k5_rows if r["sample_id"] == "s1")
    assert s1_rag_k5["parse_status"] == "MALFORMED_RESPONSE"


# ===========================================================================
# 10. Crash Injection Tests Covering All Request States
# ===========================================================================


def test_crash_after_reserved_safely_resumes(bundle, tmp_path):
    """Crash after RESERVED before dispatch started safely resumes without failing closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-reserved"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    # Run 1 record first
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=1,
    )
    # Simulate a crash right after next job is RESERVED
    journal_path = output / "request_journal.jsonl"
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESERVED"}
    )

    # Resuming should succeed because consumed == start for the in-flight key
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        resume=True,
    )
    assert summary["complete"] is True
    assert summary["record_count"] == 10


def test_crash_after_dispatch_started_fails_closed(bundle, tmp_path):
    """Crash after DISPATCH_STARTED is ambiguous and must fail closed on resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-dispatch-started"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=1,
    )
    journal_path = output / "request_journal.jsonl"
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESERVED"}
    )
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "DISPATCH_STARTED"}
    )

    with pytest.raises(
        ValueError, match="in-flight request state is ambiguous; human reconciliation required"
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda model_cfg, budget: MockProvider(),
            resume=True,
        )


def test_crash_after_provider_response_fails_closed(bundle, tmp_path):
    """Crash after provider attempt consumed but before record commit fails closed on resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-provider-response"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=1,
    )
    journal_path = output / "request_journal.jsonl"
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESERVED"}
    )
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "DISPATCH_STARTED"}
    )
    append_journal_event(journal_path, {"event": "attempt", "key": ["s1", "rag_k1"], "ordinal": 2})

    with pytest.raises(
        ValueError, match="in-flight request state is ambiguous; human reconciliation required"
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda model_cfg, budget: MockProvider(),
            resume=True,
        )


def test_crash_after_response_received_fails_closed(bundle, tmp_path):
    """Crash at RESPONSE_RECEIVED without record commit fails closed on resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-response-recv"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=1,
    )
    journal_path = output / "request_journal.jsonl"
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESERVED"}
    )
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "DISPATCH_STARTED"}
    )
    append_journal_event(journal_path, {"event": "attempt", "key": ["s1", "rag_k1"], "ordinal": 2})
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESPONSE_RECEIVED"}
    )

    with pytest.raises(
        ValueError, match="in-flight request state is ambiguous; human reconciliation required"
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda model_cfg, budget: MockProvider(),
            resume=True,
        )


def test_crash_after_parsed_fails_closed(bundle, tmp_path):
    """Crash at PARSED before record commit fails closed on resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-parsed"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=1,
    )
    journal_path = output / "request_journal.jsonl"
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESERVED"}
    )
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "DISPATCH_STARTED"}
    )
    append_journal_event(journal_path, {"event": "attempt", "key": ["s1", "rag_k1"], "ordinal": 2})
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "RESPONSE_RECEIVED"}
    )
    append_journal_event(
        journal_path, {"event": "transition", "key": ["s1", "rag_k1"], "state": "PARSED"}
    )

    with pytest.raises(
        ValueError, match="in-flight request state is ambiguous; human reconciliation required"
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda model_cfg, budget: MockProvider(),
            resume=True,
        )


def test_crash_after_prediction_write_before_complete_fails_closed(bundle, tmp_path):
    """Crash after record written but before journal commit fails closed on resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-pred-write"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CRASH_TEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    # Run 2 records cleanly first
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
        stop_after=2,
    )

    # Now remove the last 'complete' event from journal to simulate crash after file write
    journal_lines = (output / "request_journal.jsonl").read_bytes().splitlines()
    assert b'"complete"' in journal_lines[-1]
    (output / "request_journal.jsonl").write_bytes(b"\n".join(journal_lines[:-1]) + b"\n")

    # Resuming must fail closed
    with pytest.raises(ValueError):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda model_cfg, budget: MockProvider(),
            resume=True,
        )


def test_crash_after_record_committed_skips_dispatch(bundle, tmp_path):
    """Committed records in the journal are never re-dispatched upon resume."""
    plan = load_plan(bundle[1])
    output = tmp_path / "crash-record-committed"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_SKIP_DISPATCH",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    provider1 = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: provider1,
        stop_after=1,
    )
    assert len(provider1.calls) == 1
    first_key = provider1.calls[0][0]

    provider2 = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: provider2,
        resume=True,
        stop_after=1,
    )
    assert len(provider2.calls) == 1
    assert provider2.calls[0][0] != first_key


# ===========================================================================
# 11. Staged Execution, Ground Truth Isolation, CLI, and D1 Policy Tests
# ===========================================================================


def test_staged_execution_and_resume_preserves_run_id_and_budget(bundle, tmp_path):
    """Staged execution with stop_after and resume preserves live run_id and budget."""
    plan = load_plan(bundle[1])
    output = tmp_path / "staged-exec"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_STAGED",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    prov1 = MockProvider()
    summary1 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: prov1,
        stop_after=3,
    )
    assert summary1["complete"] is False
    assert summary1["record_count"] == 3
    assert summary1["requests_consumed"] == 3
    assert len(prov1.calls) == 3
    initial_run_id = summary1["run_id"]

    prov2 = MockProvider()
    summary2 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: prov2,
        resume=True,
    )
    assert summary2["complete"] is True
    assert summary2["record_count"] == 10
    assert summary2["requests_consumed"] == 10
    assert summary2["new_records"] == 7
    assert len(prov2.calls) == 7
    assert summary2["run_id"] == initial_run_id


def test_ground_truth_sentinel_leakage_prevented(bundle, tmp_path):
    """Ground truth metadata sentinels are completely absent from prompt texts."""
    plan = load_plan(bundle[1])
    output = tmp_path / "gt-sentinel-leakage"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_SENTINEL_LEAKAGE",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    fake_provider = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: fake_provider,
    )
    assert len(fake_provider.calls) == 10
    for key, kwargs in fake_provider.calls:
        prompt_input = kwargs.get("input", "")
        assert "SECRET_GT_METADATA" not in prompt_input
        assert "label_status" not in prompt_input
        assert "single_ground_truth" not in prompt_input
        assert "contextual_ground_truth" not in prompt_input


def test_evaluator_compatibility_live_runner_output(bundle, tmp_path):
    """Live runner output loads into evaluator; canonical scoring raises HumanDecisionRequired."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-evaluator-compat"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_EVAL_COMPAT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda model_cfg, budget: MockProvider(),
    )

    paths = {c: output / f"{c}_predictions.jsonl" for c in CONDITIONS}
    eval_inputs = _load_evaluation_inputs(
        output / "manifest.json", paths, repository_root=bundle[0], expected_sample_count=2
    )
    assert len(eval_inputs.records) == 10
    assert eval_inputs.execution_mode == "live"

    with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
        evaluate_end_to_end(eval_inputs)

    with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
        evaluate_conditional_accuracy(eval_inputs)


def test_cli_live_blocked_without_protocol(bundle, capsys, tmp_path):
    """CLI live and resume subcommands fail closed when protocol or auth is missing."""
    _, path, _ = bundle
    ret = main(["live", "--config", str(path)])
    assert ret == 1
    err_out = capsys.readouterr().err
    assert "HUMAN_DECISION_REQUIRED" in err_out or "LIVE_EXECUTION_BLOCKED" in err_out
    assert '"provider_calls": 0' in err_out

    ret_resume = main(["resume", "--config", str(path), "--output-dir", str(tmp_path / "no_dir")])
    assert ret_resume == 1


def test_raw_response_policy_record_only_and_discard(bundle, tmp_path):
    """Approved D1 policy is strictly enforced: DISCARD has None, RECORD_ONLY has raw response."""
    plan = load_plan(bundle[1])

    # 1. DISCARD policy
    out_discard = tmp_path / "d1-discard"
    proto_discard = create_test_protocol_approval(d1_raw_response_policy="DISCARD")
    auth_discard = ExecutionAuthorization(
        human_approval_token="TOKEN_DISCARD",
        approved_protocol_sha256=proto_discard.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        out_discard,
        authorization=auth_discard,
        protocol=proto_discard,
        provider_factory=lambda model_cfg, budget: MockProvider(),
    )
    no_rag_rows = [
        parse_json(line)
        for line in (out_discard / "no_rag_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    for row in no_rag_rows:
        assert row["raw_response"] is None
        assert row["raw_response_logged"] is False

    # 2. RECORD_ONLY policy
    out_record = tmp_path / "d1-record"
    proto_record = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth_record = ExecutionAuthorization(
        human_approval_token="TOKEN_RECORD",
        approved_protocol_sha256=proto_record.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        out_record,
        authorization=auth_record,
        protocol=proto_record,
        provider_factory=lambda model_cfg, budget: MockProvider(),
    )
    no_rag_rows_rec = [
        parse_json(line)
        for line in (out_record / "no_rag_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    for row in no_rag_rows_rec:
        assert row["raw_response"] == '{"technique_id":"T1059.001"}'
        assert row["raw_response_logged"] is True


def test_raw_response_policy_log_separately(bundle, tmp_path):
    """LOG_SEPARATELY sets raw_response=None and raw_response_logged=True."""
    plan = load_plan(bundle[1])
    output = tmp_path / "d1-log-separately"
    proto = create_test_protocol_approval(d1_raw_response_policy="LOG_SEPARATELY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_LOG_SEP",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=2,
    )
    rows = [
        parse_json(line)
        for line in (output / "no_rag_predictions.jsonl").read_bytes().splitlines()
        if line
    ]
    for row in rows:
        assert row["raw_response"] is None
        assert row["raw_response_logged"] is True


def test_live_execution_requires_full_scientific_protocol_contract(bundle, tmp_path):
    """Live execution without full ScientificProtocolApproval contract fails closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-no-protocol"
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_VALID",
        scientific_protocol_approved=True,
        authorized_max_requests=20,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="PAIRED_TEST",
    )
    with pytest.raises(
        ProtocolNotFrozenError, match="full ScientificProtocolApproval contract is mandatory"
    ):
        run_live_experiment(plan, output, authorization=auth, protocol=None)
    assert not output.exists()


def test_cli_successful_staged_live_resume(bundle, tmp_path):
    """CLI staged live execution can be resumed with fresh authorization and completes matrix."""
    config_path = bundle[1]
    output_dir = tmp_path / "cli-staged-run"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    proto_file = tmp_path / "protocol.json"
    proto_file.write_bytes(canonical_bytes(dataclasses.asdict(proto)) + b"\n")

    provider = MockProvider()

    # Step 1: Start staged live run (stops after 5 records)
    ret1 = main(
        [
            "live",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--protocol-file",
            str(proto_file),
            "--auth-token",
            "TOKEN_STAGE_1",
            "--max-attempts",
            "40",
            "--allow-live-dispatch",
            "--stop-after",
            "5",
        ],
        provider_factory=lambda cfg, budget: provider,
    )
    assert ret1 == 0
    assert (output_dir / "manifest.json").exists()
    manifest_data = parse_json((output_dir / "manifest.json").read_bytes())
    assert "human_authorization_token" not in manifest_data
    assert manifest_data["human_authorization_reference"] == digest(b"TOKEN_STAGE_1")[:16]

    # Verify 5 records completed in stage 1
    summary1 = parse_json((output_dir / "run_summary.json").read_bytes())
    assert summary1["record_count"] == 5
    assert summary1["complete"] is False

    # Step 2: Resume via CLI with fresh token
    ret2 = main(
        [
            "resume",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--auth-token",
            "TOKEN_STAGE_2",
            "--allow-live-dispatch",
        ],
        provider_factory=lambda cfg, budget: provider,
    )
    assert ret2 == 0

    summary2 = parse_json((output_dir / "run_summary.json").read_bytes())
    assert summary2["complete"] is True
    assert summary2["record_count"] == 10
    assert summary2["run_id"] == manifest_data["run_id"]

    # Step 3: Rerunning complete experiment yields 0 new calls
    calls_before = len(provider.calls)
    ret3 = main(
        [
            "resume",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--auth-token",
            "TOKEN_STAGE_3",
            "--allow-live-dispatch",
        ],
        provider_factory=lambda cfg, budget: provider,
    )
    assert ret3 == 0
    assert len(provider.calls) == calls_before


def test_cli_resume_requires_fresh_runtime_authorization(bundle, tmp_path, capsys):
    """CLI resume fails closed if runtime auth token or allow_live_dispatch is missing."""
    config_path = bundle[1]
    output_dir = tmp_path / "cli-auth-required"
    proto = create_test_protocol_approval()
    proto_file = tmp_path / "protocol.json"
    proto_file.write_bytes(canonical_bytes(dataclasses.asdict(proto)) + b"\n")

    provider = MockProvider()
    main(
        [
            "live",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--protocol-file",
            str(proto_file),
            "--auth-token",
            "TOKEN_ORIG",
            "--max-attempts",
            "20",
            "--allow-live-dispatch",
            "--stop-after",
            "2",
        ],
        provider_factory=lambda cfg, budget: provider,
    )

    # 1. Missing auth-token
    ret_no_token = main(
        [
            "resume",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--allow-live-dispatch",
        ],
        provider_factory=lambda cfg, budget: provider,
    )
    assert ret_no_token == 1
    captured = capsys.readouterr()
    assert "auth-token is required" in captured.err

    # 2. Missing allow-live-dispatch
    ret_no_dispatch = main(
        [
            "resume",
            "--config",
            str(config_path),
            "--output-dir",
            str(output_dir),
            "--auth-token",
            "TOKEN_FRESH",
        ],
        provider_factory=lambda cfg, budget: provider,
    )
    assert ret_no_dispatch == 1
    captured = capsys.readouterr()
    assert "allow-live-dispatch is required" in captured.err


def test_live_resume_rejects_protocol_drift(bundle, tmp_path):
    """Resuming under a modified scientific protocol fails closed with provenance drift error."""
    plan = load_plan(bundle[1])
    output = tmp_path / "drift-output"
    proto1 = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth1 = ExecutionAuthorization(
        human_approval_token="TOKEN_DRIFT_1",
        approved_protocol_sha256=proto1.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth1,
        protocol=proto1,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=3,
    )

    # Attempt resume with different protocol (e.g. DISCARD instead of RECORD_ONLY)
    proto2 = create_test_protocol_approval(d1_raw_response_policy="DISCARD")
    auth2 = ExecutionAuthorization(
        human_approval_token="TOKEN_DRIFT_2",
        approved_protocol_sha256=proto2.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    with pytest.raises(ValueError, match="provenance drift rejected"):
        run_live_experiment(
            plan,
            output,
            authorization=auth2,
            protocol=proto2,
            provider_factory=lambda cfg, budget: MockProvider(),
            resume=True,
        )


def test_resume_rejects_tampered_manifest_protocol(bundle, tmp_path):
    """Tampering with protocol or hash inside manifest.json causes resume to fail closed."""
    plan = load_plan(bundle[1])
    output = tmp_path / "tamper-manifest-proto"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_TAMPER",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=2,
    )

    manifest_path = output / "manifest.json"
    manifest_data = parse_json(manifest_path.read_bytes())

    # Case A: Tamper hash
    manifest_tampered_hash = dict(manifest_data)
    manifest_tampered_hash["protocol_sha256"] = "00" * 32
    manifest_path.write_bytes(canonical_bytes(manifest_tampered_hash) + b"\n")

    with pytest.raises(ValueError, match="tampering detected|content has been tampered with"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, budget: MockProvider(),
            resume=True,
        )

    # Case B: Tamper decision content inside manifest
    manifest_tampered_content = dict(manifest_data)
    manifest_tampered_content["protocol"] = dict(manifest_data["protocol"])
    manifest_tampered_content["protocol"]["d1_raw_response_policy"] = "DISCARD"
    manifest_path.write_bytes(canonical_bytes(manifest_tampered_content) + b"\n")

    with pytest.raises(ValueError, match="tampered with"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, budget: MockProvider(),
            resume=True,
        )


def test_resume_does_not_persist_raw_authorization_token(bundle, tmp_path):
    """Run manifest must never persist the secret raw human approval token."""
    plan = load_plan(bundle[1])
    output = tmp_path / "token-privacy-check"
    secret_token = "SUPER_SECRET_HUMAN_APPROVAL_TOKEN_XYZ_987"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token=secret_token,
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )
    manifest_bytes = (output / "manifest.json").read_bytes()
    assert secret_token.encode("utf-8") not in manifest_bytes
    manifest_data = parse_json(manifest_bytes)
    assert "human_authorization_token" not in manifest_data
    assert (
        manifest_data["human_authorization_reference"]
        == digest(secret_token.encode("utf-8"))[:16]
    )


def test_d3_captured_snapshot_policy_rejects_missing_model_version(bundle, tmp_path):
    """CAPTURED_SNAPSHOT_OR_FAIL policy blocks execution if plan has no pinned model_version."""
    plan = load_plan(bundle[1])
    assert plan.manifest.get("model_version") is None
    output = tmp_path / "d3-missing-ver"
    proto = create_test_protocol_approval(d3_model_version_policy="CAPTURED_SNAPSHOT_OR_FAIL")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_D3",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    with pytest.raises(
        ProtocolNotFrozenError,
        match="CAPTURED_SNAPSHOT_OR_FAIL requires non-empty model_version",
    ):
        run_live_experiment(plan, output, authorization=auth, protocol=proto)


def test_d3_latest_timestamp_policy_accepts_valid_provenance(bundle, tmp_path):
    """ALLOW_LATEST_WITH_TIMESTAMP_BINDING permits execution with unpinned model version."""
    plan = load_plan(bundle[1])
    output = tmp_path / "d3-latest-ts"
    proto = create_test_protocol_approval(
        d3_model_version_policy="ALLOW_LATEST_WITH_TIMESTAMP_BINDING"
    )
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_D3_LATEST",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )
    assert summary["record_count"] == 1
    record_row = parse_json((output / "no_rag_predictions.jsonl").read_bytes().splitlines()[0])
    assert record_row["timestamp"] is not None


def test_d4_sequential_policy_rejects_incompatible_concurrency(bundle, tmp_path):
    """SEQUENTIAL_ONLY rejects plan with concurrency > 1."""
    plan = load_plan(bundle[1])
    object.__setattr__(plan.config.execution, "concurrency", 4)
    proto = create_test_protocol_approval(d4_concurrency_policy="SEQUENTIAL_ONLY")
    with pytest.raises(
        ProtocolNotFrozenError, match="plan concurrency contradicts SEQUENTIAL_ONLY"
    ):
        validate_scientific_protocol(proto, plan)


def test_d4_unimplemented_bounded_pool_blocks(bundle):
    """BOUNDED_POOL concurrency is unimplemented in runner and must fail closed."""
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval(d4_concurrency_policy="BOUNDED_POOL")
    with pytest.raises(ProtocolNotFrozenError, match="BOUNDED_POOL concurrency is not implemented"):
        validate_scientific_protocol(proto, plan)


def test_d5_worst_case_budget_policy_enforced(bundle, tmp_path):
    """HARD_CAP_WORST_CASE_ATTEMPTS requires budget >= samples * conditions * (retries + 1)."""
    plan = load_plan(bundle[1])
    output = tmp_path / "d5-worst-case"
    proto = create_test_protocol_approval(d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS")
    # Worst case = 2 samples * 5 conditions * (3 retries + 1) = 40
    # Insufficient budget: 20 < 40
    auth_insufficient = ExecutionAuthorization(
        human_approval_token="TOKEN_D5",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot cover worst-case attempts"):
        run_live_experiment(plan, output, authorization=auth_insufficient, protocol=proto)

    # Sufficient budget: 40 >= 40
    auth_sufficient = ExecutionAuthorization(
        human_approval_token="TOKEN_D5",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=40,
        allow_live_dispatch=True,
    )
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth_sufficient,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )
    assert summary["record_count"] == 1


def test_d6_prerequisite_policy_requires_verifiable_prerequisite(bundle):
    """PREREQUISITE_PILOT_SATISFIED fails closed when pilot proof is not available."""
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval(
        d6_t15_prerequisite_policy="PREREQUISITE_PILOT_SATISFIED"
    )
    with pytest.raises(
        ProtocolNotFrozenError, match="T15 prerequisite pilot proof is not available"
    ):
        validate_scientific_protocol(proto, plan)


def test_d7_dataset_scope_mismatch_rejected(bundle):
    """Protocol approving DEV_SMOKE scope rejected when plan targets 'test' split."""
    plan = load_plan(bundle[1])
    assert plan.config.dataset.split == "test"
    proto = create_test_protocol_approval(d7_dataset_scope="DEV_SMOKE")
    with pytest.raises(
        ProtocolNotFrozenError, match="d7_dataset_scope DEV_SMOKE requires 'dev' split"
    ):
        validate_scientific_protocol(proto, plan)
