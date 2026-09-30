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
import stat
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
    evaluate_experiment,
    load_evaluation_inputs,
)
from src.experiment.__main__ import main
from src.experiment.authorization import (
    ExecutionAuthorization,
    HumanAuthorizationRequiredError,
    LiveBudgetRequiredError,
    LiveExecutionBlockedError,
    ProtocolNotFrozenError,
    ScientificProtocolApproval,
    check_live_execution_gates,
    create_test_protocol_approval,
    validate_canonical_experiment_lock,
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
from src.experiment.path_safety import (
    UnsafeOutputPathError,
    is_symlink_or_junction,
    validate_untrusted_output_path,
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


def test_d1_discard_policy_supported(bundle, tmp_path):
    """Approved D1 DISCARD policy sets raw_response=None and raw_response_logged=False."""
    plan = load_plan(bundle[1])
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


def test_d1_record_only_policy_supported(bundle, tmp_path):
    """Approved D1 RECORD_ONLY policy captures raw_response and sets raw_response_logged=True."""
    plan = load_plan(bundle[1])
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


def test_d1_log_separately_blocks_until_storage_is_implemented(bundle, tmp_path):
    """LOG_SEPARATELY fails closed because separate storage is not yet implemented."""
    plan = load_plan(bundle[1])
    output = tmp_path / "d1-log-separately"
    proto = create_test_protocol_approval(d1_raw_response_policy="LOG_SEPARATELY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_LOG_SEP",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    provider_construct_count = 0
    provider_call_count = 0

    class CountingMockProvider(MockProvider):
        def create(self, *args, **kwargs):
            nonlocal provider_call_count
            provider_call_count += 1
            return super().create(*args, **kwargs)

    def counting_factory(cfg, budget):
        nonlocal provider_construct_count
        provider_construct_count += 1
        return CountingMockProvider()

    with pytest.raises(
        ProtocolNotFrozenError,
        match="LIVE_EXECUTION_BLOCKED: LOG_SEPARATELY raw-response storage is not implemented",
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
            stop_after=2,
        )

    assert provider_construct_count == 0
    assert provider_call_count == 0
    prediction_files = list(output.glob("*_predictions.jsonl")) if output.exists() else []
    assert len(prediction_files) == 0

    with pytest.raises(
        ProtocolNotFrozenError,
        match="LIVE_EXECUTION_BLOCKED: LOG_SEPARATELY raw-response storage is not implemented",
    ):
        validate_scientific_protocol(proto, plan)


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


def test_live_output_root_symlink_rejected(bundle, tmp_path):
    """Untrusted symlink output root is rejected before resolution."""
    plan = load_plan(bundle[1])
    real_dir = tmp_path / "real_live_output"
    real_dir.mkdir()
    link_dir = tmp_path / "live-link"
    try:
        link_dir.symlink_to(real_dir)
    except OSError:
        try:
            import _winapi

            _winapi.CreateJunction(str(real_dir), str(link_dir))
        except Exception:
            pytest.skip("Symlinks not permitted on this Windows environment")

    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_SYMLINK",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    construct_count = 0

    def factory(cfg, budget):
        nonlocal construct_count
        construct_count += 1
        return MockProvider()

    with pytest.raises(ValueError, match="symlink output directory rejected"):
        run_live_experiment(
            plan,
            link_dir,
            authorization=auth,
            protocol=proto,
            provider_factory=factory,
        )

    assert construct_count == 0


def test_live_output_parent_symlink_component_rejected(bundle, tmp_path):
    """Untrusted symlink in parent path component is rejected before resolution."""
    plan = load_plan(bundle[1])
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    link_parent = tmp_path / "link-parent"
    try:
        link_parent.symlink_to(real_parent)
    except OSError:
        try:
            import _winapi

            _winapi.CreateJunction(str(real_parent), str(link_parent))
        except Exception:
            pytest.skip("Symlinks not permitted on this Windows environment")

    output = link_parent / "experiment-1"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_PARENT_SYMLINK",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    construct_count = 0

    def factory(cfg, budget):
        nonlocal construct_count
        construct_count += 1
        return MockProvider()

    with pytest.raises(ValueError, match="symlink output directory rejected"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=factory,
        )

    assert construct_count == 0


def test_reserved_crash_recovery_remains_resumable_after_completion(bundle, tmp_path):
    """Safe RESERVED crash recovery writes explicit reservation_abandoned and remains resumable."""
    plan = load_plan(bundle[1])
    output = tmp_path / "reserved-crash-recovery"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_RESERVED_CRASH",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    # 1. Run first record cleanly
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )

    # 2. Inject RESERVED for next key
    first_record_sample = plan.samples[0].sample_id
    next_key = [first_record_sample, CONDITIONS[1]]
    journal_file = output / "request_journal.jsonl"
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESERVED"}
            )
            + b"\n"
        )

    # 3. Resume and finish complete matrix
    summary1 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        resume=True,
    )
    assert summary1["complete"] is True

    # 4. Verify reservation_abandoned event exists in journal exactly for next_key
    events = [parse_json(line) for line in journal_file.read_bytes().splitlines() if line]
    abandoned_events = [
        e for e in events if e.get("event") == "reservation_abandoned" and e.get("key") == next_key
    ]
    assert len(abandoned_events) == 1

    # 5. Create fresh provider with call counter and resume AGAIN
    fresh_calls = 0

    class CountingMockProvider(MockProvider):
        def create(self, **kwargs):
            nonlocal fresh_calls
            fresh_calls += 1
            return super().create(**kwargs)

    summary2 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: CountingMockProvider(),
        resume=True,
    )

    # 6. Verify second resume results
    assert summary2["complete"] is True
    assert summary2["new_records"] == 0
    assert fresh_calls == 0


def test_reservation_abandonment_does_not_consume_budget(bundle, tmp_path):
    """reservation_abandoned event in journal does not consume authorized budget."""
    plan = load_plan(bundle[1])
    output = tmp_path / "abandonment-budget"
    proto = create_test_protocol_approval()
    # Matrix requires 2 samples * 5 conditions = 10 requests
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_ABANDON_BUDGET",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=10,
        allow_live_dispatch=True,
    )

    # Run 1 record
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )

    # Inject RESERVED
    first_record_sample = plan.samples[0].sample_id
    next_key = [first_record_sample, CONDITIONS[1]]
    journal_file = output / "request_journal.jsonl"
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESERVED"}
            )
            + b"\n"
        )

    # Resume with exact budget 10: if abandonment consumed budget, it would fail
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        resume=True,
    )
    assert summary["complete"] is True
    assert summary["requests_consumed"] == 10


def test_dispatched_reservation_cannot_be_abandoned(bundle, tmp_path):
    """Reservation cannot be abandoned after DISPATCH_STARTED or attempts occurred."""
    plan = load_plan(bundle[1])
    output = tmp_path / "dispatched-abandon-fail"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_DISPATCH_ABANDON",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    # Run 1 record
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: MockProvider(),
        stop_after=1,
    )

    # Inject DISPATCH_STARTED and then reservation_abandoned
    first_record_sample = plan.samples[0].sample_id
    next_key = [first_record_sample, CONDITIONS[1]]
    journal_file = output / "request_journal.jsonl"
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESERVED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "reservation_abandoned", "key": next_key}
            )
            + b"\n"
        )

    # Resume must fail closed because dispatched state cannot be abandoned
    with pytest.raises(ValueError, match="Cannot abandon reservation in state DISPATCH_STARTED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, budget: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_reserved_to_response_received(bundle, tmp_path):
    """Live journal rejects illegal direct transition from RESERVED to RESPONSE_RECEIVED."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-trans-1"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_T1",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESPONSE_RECEIVED"}
            )
            + b"\n"
        )

    with pytest.raises(ValueError, match="expected DISPATCH_STARTED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_reserved_to_parsed(bundle, tmp_path):
    """Live journal rejects illegal direct transition from RESERVED to PARSED."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-trans-2"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_T2",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "PARSED"}) + b"\n"
        )

    with pytest.raises(ValueError, match="expected RESPONSE_RECEIVED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_dispatch_started_to_parsed(bundle, tmp_path):
    """Live journal rejects illegal transition from DISPATCH_STARTED directly to PARSED."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-trans-3"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_T3",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "PARSED"}) + b"\n"
        )

    with pytest.raises(ValueError, match="expected RESPONSE_RECEIVED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_response_received_to_complete(bundle, tmp_path):
    """Live journal rejects completing a record without passing through PARSED."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-trans-4"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_T4",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "attempt", "key": next_key, "ordinal": 2}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESPONSE_RECEIVED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "complete", "key": next_key, "record_sha256": "fake_hash"}
            )
            + b"\n"
        )

    with pytest.raises(ValueError, match="expected PARSED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_attempt_before_dispatch_started(bundle, tmp_path):
    """Attempt event before DISPATCH_STARTED is rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-attempt-1"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_ATT1",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "attempt", "key": next_key, "ordinal": 2}) + b"\n"
        )

    with pytest.raises(ValueError, match="Attempt event not allowed in state RESERVED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_attempt_after_response_received(bundle, tmp_path):
    """Attempt event after RESPONSE_RECEIVED is rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-attempt-2"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_ATT2",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "attempt", "key": next_key, "ordinal": 2}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESPONSE_RECEIVED"}
            )
            + b"\n"
        )
        stream.write(
            canonical_bytes({"event": "attempt", "key": next_key, "ordinal": 3}) + b"\n"
        )

    with pytest.raises(ValueError, match="Attempt event not allowed in state RESPONSE_RECEIVED"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_requires_at_least_one_attempt_before_response_received(bundle, tmp_path):
    """Transition to RESPONSE_RECEIVED without at least one attempt is rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "bad-attempt-3"
    proto = create_test_protocol_approval()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_ATT3",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=1,
    )
    journal_file = output / "request_journal.jsonl"
    next_key = [plan.samples[0].sample_id, CONDITIONS[1]]
    with journal_file.open("ab") as stream:
        stream.write(
            canonical_bytes({"event": "transition", "key": next_key, "state": "RESERVED"}) + b"\n"
        )
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"}
            )
            + b"\n"
        )
        # No attempt!
        stream.write(
            canonical_bytes(
                {"event": "transition", "key": next_key, "state": "RESPONSE_RECEIVED"}
            )
            + b"\n"
        )

    with pytest.raises(ValueError, match="at least one provider attempt required"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_live_journal_rejects_legacy_begin_bypass_of_reserved(bundle, tmp_path):
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval()
    output = tmp_path / "live_begin_bypass"
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_LIVE_BEGIN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )
    # Execute 2 records cleanly in live mode
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, b: MockProvider(),
        stop_after=2,
    )
    journal_file = output / "request_journal.jsonl"
    rows = [
        json.loads(line)
        for line in journal_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    # Identify record 2 key: (plan.samples[0].sample_id, CONDITIONS[1])
    key2 = [plan.samples[0].sample_id, CONDITIONS[1]]

    # Rewrite rows: replace RESERVED and DISPATCH_STARTED for key2 with legacy 'begin'
    new_rows = []
    skipped_transitions = 0
    for row in rows:
        if row.get("key") == key2 and row.get("event") == "transition":
            if row.get("state") in ("RESERVED", "DISPATCH_STARTED"):
                if skipped_transitions == 0:
                    new_rows.append({"event": "begin", "key": key2})
                skipped_transitions += 1
                continue
        new_rows.append(row)

    assert skipped_transitions == 2
    journal_file.write_bytes(b"".join(canonical_bytes(r) + b"\n" for r in new_rows))

    # Live resume MUST reject the legacy begin event fail-closed
    with pytest.raises(
        ValueError,
        match="legacy begin event is forbidden in live journal; expected RESERVED transition",
    ):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, b: MockProvider(),
            resume=True,
        )


def test_path_safety_inspection_error_fails_closed(bundle, tmp_path, monkeypatch):
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval()
    output = tmp_path / "probe_dir"
    output.mkdir()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_INSPECT_FAIL",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    orig_lstat = os.lstat

    def failing_lstat(path, *args, **kwargs):
        if Path(path) == output:
            raise PermissionError("EACCES: permission denied")
        return orig_lstat(path, *args, **kwargs)

    monkeypatch.setattr(os, "lstat", failing_lstat)

    # validate_untrusted_output_path directly raises UnsafeOutputPathError
    with pytest.raises(UnsafeOutputPathError, match="cannot safely inspect path component"):
        validate_untrusted_output_path(output)

    # run_live_experiment fails closed before any provider instantiation or writes
    provider_construct_count = 0
    provider_call_count = 0

    class CountingMockProvider(MockProvider):
        def create(self, *args, **kwargs):
            nonlocal provider_call_count
            provider_call_count += 1
            return super().create(*args, **kwargs)

    def counting_factory(cfg, b):
        nonlocal provider_construct_count
        provider_construct_count += 1
        return CountingMockProvider()

    with pytest.raises(UnsafeOutputPathError, match="cannot safely inspect path component"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
        )

    assert provider_construct_count == 0
    assert provider_call_count == 0
    assert not list(output.glob("*.jsonl"))


def test_path_safety_resolve_error_fails_closed(bundle, tmp_path, monkeypatch):
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval()
    output = tmp_path / "resolve_fail_dir"
    output.mkdir()
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_RESOLVE_FAIL",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=20,
        allow_live_dispatch=True,
    )

    orig_resolve = Path.resolve

    def failing_resolve(self, *args, **kwargs):
        if self == output:
            raise PermissionError("EACCES: permission denied during resolve")
        return orig_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", failing_resolve)

    with pytest.raises(UnsafeOutputPathError, match="cannot safely resolve path"):
        validate_untrusted_output_path(output)

    provider_construct_count = 0
    provider_call_count = 0

    class CountingMockProvider(MockProvider):
        def create(self, *args, **kwargs):
            nonlocal provider_call_count
            provider_call_count += 1
            return super().create(*args, **kwargs)

    def counting_factory(cfg, b):
        nonlocal provider_construct_count
        provider_construct_count += 1
        return CountingMockProvider()

    with pytest.raises(UnsafeOutputPathError, match="cannot safely resolve path"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
        )

    assert provider_construct_count == 0
    assert provider_call_count == 0
    assert not list(output.glob("*.jsonl"))


def test_path_safety_detects_arbitrary_reparse_tags_and_attributes(tmp_path, monkeypatch):
    test_dir = tmp_path / "reparse_probe"
    test_dir.mkdir()

    # 1. Fake stat result with arbitrary non-zero st_reparse_tag
    class FakeStatArbitraryReparseTag:
        st_mode = stat.S_IFDIR | 0o755
        st_reparse_tag = 0x0000002A  # Arbitrary non-zero reparse tag
        st_file_attributes = 0

    monkeypatch.setattr(os, "lstat", lambda path, *args, **kwargs: FakeStatArbitraryReparseTag())
    assert is_symlink_or_junction(test_dir) is True
    with pytest.raises(ValueError, match="symlink output directory rejected"):
        validate_untrusted_output_path(test_dir)

    # 2. Fake stat result with FILE_ATTRIBUTE_REPARSE_POINT attribute but st_reparse_tag = 0
    reparse_attr = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)

    class FakeStatReparseAttribute:
        st_mode = stat.S_IFDIR | 0o755
        st_reparse_tag = 0
        st_file_attributes = reparse_attr

    monkeypatch.setattr(os, "lstat", lambda path, *args, **kwargs: FakeStatReparseAttribute())
    assert is_symlink_or_junction(test_dir) is True
    with pytest.raises(ValueError, match="symlink output directory rejected"):
        validate_untrusted_output_path(test_dir)


# ===========================================================================
# 12. Section 24: Scientific Protocol Integrity & Plan Validation Tests
# ===========================================================================


def test_frozen_protocol_v1_integrity_and_validation():
    """Verify config/experiment_protocol_v1.json matches exact frozen SHA-256 and rules."""
    proto_path = ROOT / "config" / "experiment_protocol_v1.json"
    assert proto_path.exists()
    proto_dict = parse_json(proto_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)
    validate_scientific_protocol(protocol)
    assert (
        protocol.protocol_sha256
        == "e7ab9ca3b5a779fc01e4d0b532871377aff041faf9c570c32599fedf26748677"
    )
    assert protocol.d1_raw_response_policy == "RECORD_ONLY"
    assert protocol.d2a_ground_truth_semantics == "ANY_MATCH"
    assert protocol.d2b_empty_ground_truth == "EXCLUDE"
    assert protocol.d2c_ambiguous_ground_truth == "EXCLUDE"
    assert protocol.d2d_macro_f1_universe == "FROZEN_BENCHMARK_UNIVERSE"
    assert protocol.d2e_invalid_id_denominator == "INCLUDE_IN_DENOMINATOR"
    assert protocol.d2f_api_error_denominator == "INCLUDE_IN_DENOMINATOR"
    assert protocol.d2g_retired_attack_id == "ALLOW_HISTORICAL"
    assert protocol.d2h_conditional_retrieval == "ANY_GT_RETRIEVED"
    assert protocol.d2i_failure_precedence == "INDEPENDENT_AXES"
    assert protocol.d2j_zero_denominator == "NULL"
    assert protocol.d3_model_version_policy == "ALLOW_LATEST_WITH_TIMESTAMP_BINDING"
    assert protocol.d4_concurrency_policy == "SEQUENTIAL_ONLY"
    assert protocol.d5_budget_policy == "HARD_CAP_WORST_CASE_ATTEMPTS"
    assert protocol.d6_t15_prerequisite_policy == "NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK"
    assert protocol.d7_dataset_scope == "PAIRED_TEST"


# ===========================================================================
# 13. Section 34 & 35: CLI Preflight & TEST Split Protection Tests
# ===========================================================================


def test_cli_preflight_ready(capsys):
    """CLI preflight succeeds when run with --allow-dirty and outputs EXPERIMENT_PREFLIGHT_READY."""
    ret = main(["preflight", "--allow-dirty"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "EXPERIMENT_PREFLIGHT_READY" in out
    data = json.loads(out)
    assert data["provider_calls"] == 0
    assert data["prediction_writes"] == 0
    assert data["split"] == "test"
    assert data["sample_count"] == 1280
    assert data["condition_count"] == 5
    assert data["expected_requests"] == 6400
    assert data["worst_case_attempts"] == 25600


def test_cli_preflight_dirty_source_blocks(capsys, monkeypatch):
    """CLI preflight detects uncommitted/dirty changes and fails closed."""
    import subprocess

    orig_run = subprocess.run

    def fake_git_status(*args, **kwargs):
        cmd = args[0] if args else kwargs.get("args")
        if isinstance(cmd, list) and "status" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="M src/dirty_file.py\n", stderr="")
        return orig_run(*args, **kwargs)

    monkeypatch.setattr(subprocess, "run", fake_git_status)
    ret = main(["preflight"])
    assert ret == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "dirty" in err


def test_cli_preflight_missing_protocol_file_blocks(capsys, tmp_path):
    """CLI preflight fails closed when protocol file is missing."""
    missing = tmp_path / "nonexistent_protocol.json"
    ret = main(["preflight", "--allow-dirty", "--protocol-file", str(missing)])
    assert ret == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err


def test_cli_preflight_tampered_protocol_hash_blocks(capsys, tmp_path):
    """CLI preflight fails closed when protocol hash is tampered."""
    proto_file = tmp_path / "tampered_protocol.json"
    proto_data = parse_json((ROOT / "config" / "experiment_protocol_v1.json").read_bytes())
    proto_data["protocol_sha256"] = "00" * 32
    proto_file.write_bytes(canonical_bytes(proto_data))
    ret = main(["preflight", "--allow-dirty", "--protocol-file", str(proto_file)])
    assert ret == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "protocol SHA-256 hash mismatch" in err


def test_cli_preflight_insufficient_max_attempts_blocks(capsys):
    """CLI preflight rejects max-attempts smaller than worst-case requirement."""
    ret = main(["preflight", "--allow-dirty", "--max-attempts", "100"])
    assert ret == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "less than worst-case attempts" in err


def test_preflight_guarantees_zero_provider_calls_and_zero_writes(bundle, tmp_path):
    """Preflight execution must never invoke providers or write prediction files."""
    plan = load_plan(bundle[1])
    proto = create_test_protocol_approval()
    gate = check_live_execution_gates(plan, None, protocol=proto)
    assert gate["provider_calls"] == 0
    assert gate["prediction_writes"] == 0
    assert gate["live_execution_permitted"] is False


# ===========================================================================
# 14. Section 37-43: DEV Smoke Harness (10 DEV samples x 5 conditions = 50 calls)
# ===========================================================================


def _make_dev_bundle(tmp_path):
    root = tmp_path / "inputs_dev"
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

    pair_ids = [f"p{i}" for i in range(5)]
    views = []
    truth = []
    inference = []
    pairs = []
    for i in range(5):
        s_single = f"s{2 * i}"
        s_contextual = f"s{2 * i + 1}"
        v_single = {
            "view_id": s_single,
            "pair_id": f"p{i}",
            "view_type": "single",
            "event_ids": [f"e{i}"],
        }
        v_contextual = {
            "view_id": s_contextual,
            "pair_id": f"p{i}",
            "view_type": "contextual",
            "event_ids": [f"e{i}", f"c{i}"],
        }
        views.extend([v_single, v_contextual])

        t_single = {
            "view_id": s_single,
            "label_status": "mapped",
            "technique_ids": ["T1059.001"],
            "rationale": "SECRET_GT_METADATA",
        }
        t_contextual = {
            "view_id": s_contextual,
            "label_status": "ambiguous" if i == 4 else "mapped",
            "technique_ids": [] if i == 4 else ["T1059.001", "T1000"],
            "rationale": "SECRET_GT_METADATA",
        }
        truth.extend([t_single, t_contextual])

        inference.append(
            {"sample_id": s_single, "endpoint_evidence": f"evidence for {s_single}"}
        )
        inference.append(
            {"sample_id": s_contextual, "endpoint_evidence": f"evidence for {s_contextual}"}
        )

        pairs.append(
            {
                "pair_id": f"p{i}",
                "split": "dev",
                "single_view": v_single,
                "contextual_view": v_contextual,
                "single_ground_truth": t_single,
                "contextual_ground_truth": t_contextual,
            }
        )

    registry = {
        "objects": [
            {
                "type": "attack-pattern",
                "external_references": [{"source_name": "mitre-attack", "external_id": tid}],
            }
            for tid in ["T1059.001", "T1000"] + [f"T10{i:02d}" for i in range(1, 11)]
        ]
    }
    config["attack"]["registry"] = store("registry.json", registry)
    config["dataset"]["inference"] = store("inference.jsonl", inference, jsonl=True)
    config["dataset"]["ground_truth"] = store("ground_truth.jsonl", truth, jsonl=True)
    config["dataset"]["views"] = store("views.jsonl", views, jsonl=True)
    config["dataset"]["pairs"] = store("pairs.jsonl", pairs, jsonl=True)
    config["dataset"]["split_manifest"] = store(
        "split_manifest.json", {"dev": pair_ids, "test": []}
    )
    dataset_manifest = {
        "state": "frozen",
        "benchmark_version": "synthetic-paired-v1",
        "attack_version": "19.2",
        "view_count": 10,
        "pair_count": 5,
        "split_counts": {"dev": 5, "test": 0},
        "attack_source_sha256": config["attack"]["registry"]["sha256"],
        "files": {
            name: digest(data) for name, data in snapshots.items() if name != "registry.json"
        },
    }
    config["dataset"]["manifest"] = store("dataset_manifest.json", dataset_manifest)
    config["dataset"]["split"] = "dev"
    config["dataset"]["expected_sample_count"] = 10
    config["dataset"]["expected_pair_count"] = 5
    corpus = [
        {
            "technique_id": tid,
            "name": tid,
            "retrieval_text": "reference " + tid,
            "source_version": "19.2",
        }
        for tid in ["T1059.001", "T1000"] + [f"T10{i:02d}" for i in range(1, 11)]
    ]
    config["attack"]["corpus"] = store("corpus.jsonl", corpus, jsonl=True)
    config["attack"]["document_mapping"] = store("docmap.json", corpus)
    index = faiss.IndexFlatIP(4)
    vectors = np.eye(4, dtype=np.float32)[np.arange(12) % 4]
    index.add(vectors)
    config["attack"]["index"] = store(
        "index.bin", faiss.serialize_index(index).tobytes(), raw=True
    )
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
    config["attack"]["retrieval_manifest"] = store(
        "retrieval_manifest.json", retrieval_manifest
    )
    config["generation"]["config"] = store(
        "model.json", (ROOT / "config" / "model.json").read_bytes(), raw=True
    )
    config["prompt"]["template"] = store(
        "baseline.txt", (ROOT / "prompts" / "baseline_v1.txt").read_bytes(), raw=True
    )
    config_path = root / "experiment.json"
    config_path.write_bytes(canonical_bytes(config))
    return root, config_path, config


def test_dev_smoke_matrix_execution_and_accounting(tmp_path):
    """DEV smoke runs 10 DEV samples x 5 conditions = 50 provider calls with exact accounting."""
    _, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-run"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    # Worst case attempts = 10 samples * 5 conditions * (3 retries + 1) = 200
    auth = ExecutionAuthorization(
        human_approval_token="DEV_SMOKE_AUTH_TOKEN_SECRET_987",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )
    provider = MockProvider()
    summary = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: provider,
    )
    assert summary["complete"] is True
    assert summary["record_count"] == 50
    assert summary["requests_consumed"] == 50
    assert summary["consumed_provider_attempts"] == 50
    assert len(provider.calls) == 50

    # Verify predictions files
    for cond in CONDITIONS:
        pred_file = output / f"{cond}_predictions.jsonl"
        assert pred_file.exists()
        rows = [parse_json(line) for line in pred_file.read_bytes().splitlines() if line]
        assert len(rows) == 10
        expected_k = 0 if cond == "no_rag" else int(cond[5:])
        for r in rows:
            assert r["retrieval_k"] == expected_k
            assert len(r["retrieved_candidates"]) == expected_k


def test_dev_smoke_gt_and_secret_leakage_sentinels(tmp_path):
    """DEV smoke strictly prevents ground-truth and credentials leakage."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-leakage"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    secret_token = "SUPER_SECRET_TOKEN_DO_NOT_LEAK_ABC_123"
    auth = ExecutionAuthorization(
        human_approval_token=secret_token,
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )
    provider = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: provider,
    )

    # 1. Zero GT leakage into provider calls
    assert len(provider.calls) == 50
    for key, kwargs in provider.calls:
        call_str = json.dumps(kwargs)
        assert "SECRET_GT_METADATA" not in call_str
        assert "single_ground_truth" not in call_str
        assert "contextual_ground_truth" not in call_str
        assert "label_status" not in call_str

    # 2. Zero secret token leakage in disk outputs
    for f in output.glob("*"):
        if f.is_file():
            content = f.read_bytes()
            assert secret_token.encode("utf-8") not in content


def test_dev_smoke_evaluator_produces_all_six_artifacts(tmp_path):
    """Canonical evaluator consumes DEV smoke output and generates all six JSON artifacts."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-eval-in"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    auth = ExecutionAuthorization(
        human_approval_token="DEV_EVAL_AUTH_TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )
    provider = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: provider,
    )

    paths = {c: output / f"{c}_predictions.jsonl" for c in CONDITIONS}
    eval_inputs = load_evaluation_inputs(
        output / "manifest.json", paths, repository_root=root
    )
    assert len(eval_inputs.records) == 50
    assert len(eval_inputs.sample_ids) == 10

    eval_out = tmp_path / "dev-smoke-eval-out"
    eval_results = evaluate_experiment(eval_inputs, proto, output_dir=eval_out)
    assert eval_results["overall"]["logical_sample_count"] == 50
    assert eval_results["overall"]["total_conditions"] == 5

    expected_artifacts = (
        "overall_metrics.json",
        "per_condition_metrics.json",
        "per_technique_metrics.json",
        "retrieval_conditional_metrics.json",
        "failure_decomposition.json",
        "run_provenance.json",
    )
    for fname in expected_artifacts:
        fpath = eval_out / fname
        assert fpath.exists()
        loaded = parse_json(fpath.read_bytes())
        assert loaded["schema_version"] == "1.0.0"


def test_dev_smoke_resume_and_in_flight_recovery(tmp_path):
    """DEV smoke staged execution, RESERVED crash recovery, and DISPATCH_STARTED failure."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-recovery"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    auth = ExecutionAuthorization(
        human_approval_token="DEV_RECOVERY_TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )

    # 1. Run 10 records first (stops after 10)
    prov1 = MockProvider()
    summary1 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: prov1,
        stop_after=10,
    )
    assert summary1["complete"] is False
    assert summary1["record_count"] == 10

    # 2. Inject RESERVED transition for record 11
    journal_path = output / "request_journal.jsonl"
    next_key = [plan.samples[2].sample_id, CONDITIONS[0]]
    append_journal_event(
        journal_path,
        {"event": "transition", "key": next_key, "state": "RESERVED"},
    )

    # 3. Resume successfully completes
    prov2 = MockProvider()
    summary2 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: prov2,
        resume=True,
    )
    assert summary2["complete"] is True
    assert summary2["record_count"] == 50
    assert summary2["new_records"] == 40

    # 4. Rerunning completed run makes 0 new calls
    prov3 = MockProvider()
    summary3 = run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: prov3,
        resume=True,
    )
    assert summary3["complete"] is True
    assert summary3["new_records"] == 0
    assert len(prov3.calls) == 0


def test_dev_smoke_resume_dispatch_started_fails_closed(tmp_path):
    """Resume fails closed without blind retries when interrupted during DISPATCH_STARTED."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-dispatch-started-fail"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    auth = ExecutionAuthorization(
        human_approval_token="DEV_RECOVERY_TOKEN_DISPATCH",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )

    # 1. Run 5 records first
    prov1 = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: prov1,
        stop_after=5,
    )

    # 2. Inject an in-flight DISPATCH_STARTED transition for the next logical request
    journal_path = output / "request_journal.jsonl"
    next_key = [plan.samples[1].sample_id, CONDITIONS[0]]
    append_journal_event(
        journal_path,
        {"event": "transition", "key": next_key, "state": "RESERVED"},
    )
    append_journal_event(
        journal_path,
        {"event": "transition", "key": next_key, "state": "DISPATCH_STARTED"},
    )

    # 3. Resume must fail closed; no blind retries or provider dispatch allowed
    prov2 = MockProvider()
    with pytest.raises(ValueError, match="in-flight request state is ambiguous"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=lambda cfg, budget: prov2,
            resume=True,
        )
    # Strictly zero provider calls made on ambiguous resume attempt
    assert len(prov2.calls) == 0


def test_canonical_test_split_protection(tmp_path):
    """Canonical TEST split execution requires all prerequisites; fails closed with 0 calls."""
    config_path = ROOT / "config" / "experiment_config.json"
    plan = load_plan(config_path)
    assert plan.manifest["split"] == "test"
    output = tmp_path / "canonical-test-protection"

    provider = MockProvider()
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="PAIRED_TEST",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )

    # Case 1: Missing protocol -> blocked, 0 provider calls
    auth_valid = ExecutionAuthorization(
        human_approval_token="HUMAN_TOKEN_TEST_SPLIT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=25600,
        allow_live_dispatch=True,
    )
    with pytest.raises(ProtocolNotFrozenError):
        run_live_experiment(
            plan,
            output,
            authorization=auth_valid,
            protocol=None,
            provider_factory=lambda cfg, budget: provider,
        )
    assert len(provider.calls) == 0

    # Case 2: Missing authorization -> blocked, 0 provider calls
    with pytest.raises(LiveExecutionBlockedError):
        run_live_experiment(
            plan,
            output,
            authorization=None,
            protocol=proto,
            provider_factory=lambda cfg, budget: provider,
        )
    assert len(provider.calls) == 0

    # Case 3: Empty human approval token -> blocked, 0 provider calls
    auth_empty_token = ExecutionAuthorization(
        human_approval_token="",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=25600,
        allow_live_dispatch=True,
    )
    with pytest.raises(HumanAuthorizationRequiredError):
        run_live_experiment(
            plan,
            output,
            authorization=auth_empty_token,
            protocol=proto,
            provider_factory=lambda cfg, budget: provider,
        )
    assert len(provider.calls) == 0

    # Case 4: Insufficient budget -> blocked, 0 provider calls
    auth_insufficient_budget = ExecutionAuthorization(
        human_approval_token="HUMAN_TOKEN_TEST_SPLIT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=10,
        allow_live_dispatch=True,
    )
    with pytest.raises(LiveBudgetRequiredError):
        run_live_experiment(
            plan,
            output,
            authorization=auth_insufficient_budget,
            protocol=proto,
            provider_factory=lambda cfg, budget: provider,
        )
    assert len(provider.calls) == 0

    # Case 5: Protocol scope mismatch -> blocked, 0 provider calls
    dev_proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    auth_dev_scope = ExecutionAuthorization(
        human_approval_token="HUMAN_TOKEN_TEST_SPLIT",
        approved_protocol_sha256=dev_proto.protocol_sha256,
        authorized_max_provider_attempts=25600,
        allow_live_dispatch=True,
    )
    with pytest.raises(ProtocolNotFrozenError):
        run_live_experiment(
            plan,
            output,
            authorization=auth_dev_scope,
            protocol=dev_proto,
            provider_factory=lambda cfg, budget: provider,
        )
    assert len(provider.calls) == 0


def test_no_rag_vs_rag_execution_contract(tmp_path):
    """Verify contract: No-RAG has zero candidate techniques; RAG injects exactly k."""
    from collections import defaultdict

    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    output = tmp_path / "dev-smoke-contract"
    proto = create_test_protocol_approval(
        d1_raw_response_policy="RECORD_ONLY",
        d7_dataset_scope="DEV_SMOKE",
        d5_budget_policy="HARD_CAP_WORST_CASE_ATTEMPTS",
    )
    auth = ExecutionAuthorization(
        human_approval_token="CONTRACT_TEST_TOKEN",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=200,
        allow_live_dispatch=True,
    )
    provider = MockProvider()
    run_live_experiment(
        plan,
        output,
        authorization=auth,
        protocol=proto,
        provider_factory=lambda cfg, budget: provider,
    )

    calls_by_cond = defaultdict(list)
    for key, kwargs in provider.calls:
        sample_id, cond = key
        calls_by_cond[cond].append((sample_id, kwargs))

    assert len(calls_by_cond["no_rag"]) == 10
    for sid, kwargs in calls_by_cond["no_rag"]:
        prompt_text = json.dumps(kwargs)
        assert "Candidate 1:" not in prompt_text
        assert "Retrieved Candidates" not in prompt_text

    for cond in CONDITIONS[1:]:
        assert len(calls_by_cond[cond]) == 10
        for sid, kwargs in calls_by_cond[cond]:
            prompt_text = json.dumps(kwargs)
            assert "Candidate 1:" in prompt_text


def test_preflight_validates_output_path_and_evaluator_contract(tmp_path):
    """Preflight CLI checks output path safety, evaluator contract, and test authorization."""
    from src.experiment.__main__ import main

    fake_target = tmp_path / "fake-target"
    fake_target.mkdir()
    symlink_dir = tmp_path / "symlink-out"
    try:
        symlink_dir.symlink_to(fake_target)
        rc = main(["preflight", "--allow-dirty", "--output-dir", str(symlink_dir)])
        assert rc == 1
    except OSError:
        pass

    import io
    import sys

    captured = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = captured
    try:
        rc = main(["preflight", "--allow-dirty"])
    finally:
        sys.stdout = old_stdout

    assert rc == 0
    report = json.loads(captured.getvalue())
    assert report["status"] == "EXPERIMENT_PREFLIGHT_READY"
    assert report["evaluator_contract_valid"] is True
    assert report["output_path_safe"] is True
    assert "test_authorization_status" in report
    assert report["canonical_test_provider_calls"] == 0


# ===========================================================================
# 14. Canonical Lock, Preflight Hardening, Resume Drift, Macro-F1 & Provenance
# ===========================================================================


def test_canonical_lock_rejects_alternate_protocol(tmp_path):
    """Canonical lock rejects any protocol whose SHA-256 does not match lock."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    lock_data = {
        "schema_version": "1.0.0",
        "lock_version": "v1",
        "protocol_sha256": "11" * 32,
        "config_sha256": plan.manifest["config_sha256"],
        "artifact_hashes": {k: v["sha256"] for k, v in plan.manifest["artifacts"].items()},
    }
    lock_path = root / "config" / "canonical_experiment_lock_v1.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(canonical_bytes(lock_data))

    proto = create_test_protocol_approval()
    with pytest.raises(ProtocolNotFrozenError, match="alternate protocol rejected"):
        validate_canonical_experiment_lock(plan, proto, root=root)


def test_canonical_lock_rejects_alternate_config(tmp_path):
    """Canonical lock rejects any plan config whose SHA-256 does not match lock."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    proto = create_test_protocol_approval()
    lock_data = {
        "schema_version": "1.0.0",
        "lock_version": "v1",
        "protocol_sha256": proto.protocol_sha256,
        "config_sha256": "22" * 32,
        "artifact_hashes": {k: v["sha256"] for k, v in plan.manifest["artifacts"].items()},
    }
    lock_path = root / "config" / "canonical_experiment_lock_v1.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(canonical_bytes(lock_data))

    with pytest.raises(ProtocolNotFrozenError, match="alternate config rejected"):
        validate_canonical_experiment_lock(plan, proto, root=root)


def test_canonical_lock_rejects_tampered_artifact_hash(tmp_path):
    """Canonical lock rejects tampered artifact hashes."""
    root, config_path, _ = _make_dev_bundle(tmp_path)
    plan = load_plan(config_path)
    proto = create_test_protocol_approval()
    hashes = {k: v["sha256"] for k, v in plan.manifest["artifacts"].items()}
    hashes["prompt"] = "33" * 32
    lock_data = {
        "schema_version": "1.0.0",
        "lock_version": "v1",
        "protocol_sha256": proto.protocol_sha256,
        "config_sha256": plan.manifest["config_sha256"],
        "artifact_hashes": hashes,
    }
    lock_path = root / "config" / "canonical_experiment_lock_v1.json"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_bytes(canonical_bytes(lock_data))

    with pytest.raises(ProtocolNotFrozenError, match="mismatch with canonical lock"):
        validate_canonical_experiment_lock(plan, proto, root=root)


def test_preflight_rejects_concurrency_not_one(tmp_path, capsys):
    """Preflight rejects execution concurrency other than 1."""
    from src.experiment.authorization import protocol_to_dict

    root, config_path, config = _make_dev_bundle(tmp_path)
    config["execution"]["concurrency"] = 4
    config_path.write_bytes(canonical_bytes(config))
    proto = create_test_protocol_approval(
        d7_dataset_scope="DEV_SMOKE",
        d1_raw_response_policy="RECORD_ONLY",
    )
    proto_path = tmp_path / "protocol.json"
    proto_path.write_bytes(canonical_bytes(protocol_to_dict(proto)))
    rc = main([
        "preflight",
        "--allow-dirty",
        "--config",
        str(config_path),
        "--protocol",
        str(proto_path),
    ])
    assert rc == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "concurrency" in err


def test_preflight_rejects_missing_or_zero_budget(tmp_path, capsys):
    """Preflight rejects plan execution configuration with missing or zero max_requests."""
    from src.experiment.authorization import protocol_to_dict

    root, config_path, config = _make_dev_bundle(tmp_path)
    config["execution"]["max_requests"] = None
    config_path.write_bytes(canonical_bytes(config))
    proto = create_test_protocol_approval(
        d7_dataset_scope="DEV_SMOKE",
        d1_raw_response_policy="RECORD_ONLY",
    )
    proto_path = tmp_path / "protocol.json"
    proto_path.write_bytes(canonical_bytes(protocol_to_dict(proto)))
    rc = main([
        "preflight",
        "--allow-dirty",
        "--config",
        str(config_path),
        "--protocol",
        str(proto_path),
    ])
    assert rc == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "positive max_requests budget" in err


def test_preflight_rejects_empty_test_authorization_token(capsys):
    """Preflight rejects empty or whitespace-only test authorization token."""
    rc = main(["preflight", "--allow-dirty", "--test-authorization-token", "   "])
    assert rc == 1
    err = capsys.readouterr().err
    assert "LIVE_EXECUTION_BLOCKED" in err
    assert "empty or whitespace" in err


def test_preflight_reports_concurrency_and_provider_calls_zero(capsys):
    """Preflight outputs concurrency from plan and provider_calls_during_preflight: 0."""
    rc = main(["preflight", "--allow-dirty"])
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["concurrency"] == 1
    assert data["provider_calls_during_preflight"] == 0


def test_resume_rejects_config_drift(bundle, tmp_path):
    """Resume rejects manifest config SHA-256 drift and guarantees 0 provider calls."""
    root, config_path, _ = bundle
    plan = load_plan(config_path)
    output = tmp_path / "resume-config-drift"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_DRIFT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=50,
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
    manifest_path = output / "manifest.json"
    manifest_data = parse_json(manifest_path.read_bytes())
    manifest_data["config_sha256"] = "99" * 32
    manifest_path.write_bytes(canonical_bytes(manifest_data))

    provider_calls = 0

    def counting_factory(cfg, budget):
        nonlocal provider_calls
        provider_calls += 1
        return MockProvider()

    with pytest.raises(LiveExecutionBlockedError, match="config SHA-256"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
            resume=True,
        )
    assert provider_calls == 0


def test_resume_rejects_prompt_drift(bundle, tmp_path):
    """Resume rejects manifest prompt template drift and guarantees 0 provider calls."""
    root, config_path, _ = bundle
    plan = load_plan(config_path)
    output = tmp_path / "resume-prompt-drift"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_PROMPT_DRIFT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=50,
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
    manifest_path = output / "manifest.json"
    manifest_data = parse_json(manifest_path.read_bytes())
    manifest_data["artifacts"]["prompt"]["sha256"] = "88" * 32
    manifest_path.write_bytes(canonical_bytes(manifest_data))

    provider_calls = 0

    def counting_factory(cfg, budget):
        nonlocal provider_calls
        provider_calls += 1
        return MockProvider()

    with pytest.raises(LiveExecutionBlockedError, match="artifact 'prompt' SHA-256 drift"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
            resume=True,
        )
    assert provider_calls == 0


def test_resume_rejects_model_config_drift(bundle, tmp_path):
    """Resume rejects model configuration drift and guarantees 0 provider calls."""
    root, config_path, _ = bundle
    plan = load_plan(config_path)
    output = tmp_path / "resume-model-drift"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_MODEL_DRIFT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=50,
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
    manifest_path = output / "manifest.json"
    manifest_data = parse_json(manifest_path.read_bytes())
    manifest_data["artifacts"]["model_config"]["sha256"] = "77" * 32
    manifest_path.write_bytes(canonical_bytes(manifest_data))

    provider_calls = 0

    def counting_factory(cfg, budget):
        nonlocal provider_calls
        provider_calls += 1
        return MockProvider()

    with pytest.raises(LiveExecutionBlockedError, match="artifact 'model_config' SHA-256 drift"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
            resume=True,
        )
    assert provider_calls == 0


def test_resume_rejects_code_identity_drift(bundle, tmp_path):
    """Resume rejects code commit identity drift and guarantees 0 provider calls."""
    root, config_path, _ = bundle
    plan = load_plan(config_path)
    output = tmp_path / "resume-code-drift"
    proto = create_test_protocol_approval(d1_raw_response_policy="RECORD_ONLY")
    auth = ExecutionAuthorization(
        human_approval_token="TOKEN_CODE_DRIFT",
        approved_protocol_sha256=proto.protocol_sha256,
        authorized_max_provider_attempts=50,
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
    manifest_path = output / "manifest.json"
    manifest_data = parse_json(manifest_path.read_bytes())
    manifest_data["git_commit_sha"] = "66" * 20
    manifest_path.write_bytes(canonical_bytes(manifest_data))

    provider_calls = 0

    def counting_factory(cfg, budget):
        nonlocal provider_calls
        provider_calls += 1
        return MockProvider()

    with pytest.raises(LiveExecutionBlockedError, match="code identity drift"):
        run_live_experiment(
            plan,
            output,
            authorization=auth,
            protocol=proto,
            provider_factory=counting_factory,
            resume=True,
        )
    assert provider_calls == 0


def test_macro_f1_universe_and_denominator_invariance():
    """Macro-F1 denominator remains invariant to predictions and unobserved classes."""
    from src.evaluation.experiment_metrics import (
        EvaluationInputs,
        compute_condition_metrics,
    )

    proto = create_test_protocol_approval()
    corpus = ("T1001", "T1002", "T1003", "T1004", "T1005")
    gt = {
        "s1": ("T1001",),
        "s2": ("T1002",),
    }
    records = [
        {
            "sample_id": "s1",
            "condition": "no_rag",
            "parsed_technique_ids": ["T1001"],
            "parse_status": "VALID",
        },
        {
            "sample_id": "s2",
            "condition": "no_rag",
            "parsed_technique_ids": ["T1002"],
            "parse_status": "VALID",
        },
    ]
    inputs = EvaluationInputs(
        manifest_sha256="00" * 32,
        experiment_id="exp-macro-f1",
        execution_mode="mock_fixture",
        sample_ids=("s1", "s2"),
        records=tuple(records),
        ground_truth=gt,
        registry={tid: {} for tid in corpus},
        corpus_ids=corpus,
    )
    metrics = compute_condition_metrics(records, inputs, proto, "no_rag")
    # T1001: F1=1.0, T1002: F1=1.0, T1003-T1005: 0.0 -> sum=2.0 / 5 = 0.40
    assert metrics["macro_f1"] == pytest.approx(2.0 / 5.0)

    # Hallucinated ID outside universe must not expand denominator
    records_hallucinated = [
        {
            "sample_id": "s1",
            "condition": "no_rag",
            "parsed_technique_ids": ["T1001"],
            "parse_status": "VALID",
        },
        {
            "sample_id": "s2",
            "condition": "no_rag",
            "parsed_technique_ids": ["T9999"],
            "parse_status": "INVALID_ID",
        },
    ]
    inputs_hal = EvaluationInputs(
        manifest_sha256="00" * 32,
        experiment_id="exp-macro-f1",
        execution_mode="mock_fixture",
        sample_ids=("s1", "s2"),
        records=tuple(records_hallucinated),
        ground_truth=gt,
        registry={tid: {} for tid in corpus},
        corpus_ids=corpus,
    )
    metrics_hal = compute_condition_metrics(records_hallucinated, inputs_hal, proto, "no_rag")
    # T1001: F1=1.0, T1002: F1=0.0 -> sum=1.0 / 5 = 0.20
    assert metrics_hal["macro_f1"] == pytest.approx(1.0 / 5.0)


def test_model_provenance_and_tamper_detection():
    """Model provenance metadata is captured and inverted timestamps trigger tamper detection."""
    from src.evaluation.experiment_metrics import (
        EvaluationInputs,
        compute_run_provenance,
        verify_evaluator_provenance,
    )

    proto = create_test_protocol_approval()
    records = [
        {
            "sample_id": f"s{i}",
            "condition": cond,
            "experiment_id": "exp-prov",
            "returned_model_id": "gpt-4o-2024-08-06",
            "response_id": f"resp_{i}_{cond}",
            "system_fingerprint": "fp_abc123",
            "request_timestamp_utc": "2026-09-30T10:00:00Z",
            "response_timestamp_utc": "2026-09-30T10:00:02Z",
        }
        for i in range(2)
        for cond in ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
    ]
    manifest = {
        "experiment_id": "exp-prov",
        "git_commit_sha": "a" * 40,
        "config_sha256": "b" * 64,
        "protocol_sha256": proto.protocol_sha256,
        "model": {"provider": "openai", "model": "gpt-4o"},
    }
    inputs = EvaluationInputs(
        manifest_sha256="c" * 64,
        experiment_id="exp-prov",
        execution_mode="live",
        sample_ids=("s0", "s1"),
        records=tuple(records),
        ground_truth={"s0": ("T1059.001",), "s1": ("T1105",)},
        registry={},
        manifest_data=manifest,
    )
    verify_evaluator_provenance(inputs, proto)
    prov = compute_run_provenance(inputs, proto)
    assert "model_provenance" in prov
    assert prov["model_provenance"]["returned_models"] == ["gpt-4o-2024-08-06"]
    assert prov["model_provenance"]["system_fingerprints"] == ["fp_abc123"]
    assert prov["model_provenance"]["has_response_ids"] is True
    assert prov["model_provenance"]["has_timestamps"] is True

    # Tampered timestamp: response before request
    tampered_records = list(records)
    tampered_records[0] = dict(records[0])
    tampered_records[0]["request_timestamp_utc"] = "2026-09-30T10:00:05Z"
    tampered_records[0]["response_timestamp_utc"] = "2026-09-30T10:00:01Z"
    tampered_inputs = EvaluationInputs(
        manifest_sha256="c" * 64,
        experiment_id="exp-prov",
        execution_mode="live",
        sample_ids=("s0", "s1"),
        records=tuple(tampered_records),
        ground_truth={"s0": ("T1059.001",), "s1": ("T1105",)},
        registry={},
        manifest_data=manifest,
    )
    with pytest.raises(ValueError, match="timestamp tampering detected"):
        verify_evaluator_provenance(tampered_inputs, proto)


def test_sentinel_leakage_redaction():
    """Secrets, Bearer tokens, OpenAI keys, and sentinels are scrubbed from outputs."""
    from src.experiment.redaction import sanitize_secrets

    raw = "Failed with Bearer my-secret-token-123 and key sk-proj-abcdef1234567890abcdef1234567890"
    sanitized = sanitize_secrets(raw)
    assert "my-secret-token-123" not in sanitized
    assert "sk-proj-abcdef1234567890abcdef1234567890" not in sanitized
    assert "[REDACTED_BEARER_TOKEN]" in sanitized
    assert "[REDACTED_OPENAI_KEY]" in sanitized

    sentinel = "HUMAN_SUPER_SECRET_TOKEN_999"
    sanitized_custom = sanitize_secrets(f"Error for token {sentinel}", extra_tokens=[sentinel])
    assert sentinel not in sanitized_custom
    assert "[REDACTED_SECRET]" in sanitized_custom



