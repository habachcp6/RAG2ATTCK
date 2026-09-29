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

import json
import os
from pathlib import Path

import faiss
import numpy as np
import pytest

from src.evaluation.experiment_metrics import (
    HumanDecisionRequired,
    _load_evaluation_inputs,
    evaluate_conditional_accuracy,
    evaluate_end_to_end,
)
from src.experiment.authorization import (
    ExecutionAuthorization,
    HumanAuthorizationRequiredError,
    LiveBudgetRequiredError,
    LiveExecutionBlockedError,
    ProtocolNotFrozenError,
    check_live_execution_gates,
)
from src.experiment.config import canonical_bytes, digest, load_plan, parse_json
from src.experiment.journal import RequestJournalStateMachine, RequestState
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
    auth_bad_d1 = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=100,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="UNKNOWN_POLICY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(ProtocolNotFrozenError, match="D1 raw response policy"):
        run_live_experiment(plan, output, authorization=auth_bad_d1)

    # D7 invalid
    auth_bad_d7 = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=100,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="INVALID_SCOPE",
    )
    with pytest.raises(ProtocolNotFrozenError, match="D7 dataset scope"):
        run_live_experiment(plan, output, authorization=auth_bad_d7)
    assert not output.exists()


def test_authorization_missing_human_token_zero_calls(bundle, tmp_path):
    """Live execution without a non-empty human authorization token is blocked."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-missing-token"
    for invalid_token in ("", "   "):
        auth = ExecutionAuthorization(
            human_approval_token=invalid_token,
            scientific_protocol_approved=True,
            authorized_max_requests=100,
            allow_live_dispatch=True,
            d1_raw_response_policy_approved="RECORD_ONLY",
            d7_dataset_scope_approved="FULL_BENCHMARK",
        )
        with pytest.raises(HumanAuthorizationRequiredError, match="human approval token"):
            run_live_experiment(plan, output, authorization=auth)
    assert not output.exists()


def test_authorization_missing_or_zero_budget_zero_calls(bundle, tmp_path):
    """Live execution without explicit positive request budget is blocked."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-budget-tests"

    # Missing budget (None)
    auth_none = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=None,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(LiveBudgetRequiredError, match="explicit finite request budget"):
        run_live_experiment(plan, output, authorization=auth_none)

    # Zero budget
    auth_zero = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=0,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot be zero"):
        run_live_experiment(plan, output, authorization=auth_zero)
    assert not output.exists()


def test_authorization_negative_budget_rejected(bundle, tmp_path):
    """Negative budget values are strictly rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-neg-budget"
    auth_neg = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=-10,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot be negative"):
        run_live_experiment(plan, output, authorization=auth_neg)
    assert not output.exists()


def test_authorization_insufficient_budget_rejected(bundle, tmp_path):
    """Budget smaller than complete matrix (2 samples * 5 conditions = 10) is rejected."""
    plan = load_plan(bundle[1])
    output = tmp_path / "live-insufficient-budget"
    auth_small = ExecutionAuthorization(
        human_approval_token="TOKEN",
        scientific_protocol_approved=True,
        authorized_max_requests=9,  # Needs 10
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(LiveBudgetRequiredError, match="cannot cover the required matrix calls"):
        run_live_experiment(plan, output, authorization=auth_small)
    assert not output.exists()


def test_authorization_api_key_alone_does_not_permit_calls(bundle, monkeypatch, tmp_path):
    """Possessing an OPENAI_API_KEY environment variable does not authorize live execution."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-test")
    plan = load_plan(bundle[1])
    output = tmp_path / "live-key-alone"
    with pytest.raises(LiveExecutionBlockedError):
        run_live_experiment(plan, output, authorization=None)
    assert not output.exists()


def test_live_experiment_blocked_even_with_valid_authorization(bundle, tmp_path):
    """Even if an authorization object has all valid fields, live execution remains blocked."""
    plan = load_plan(bundle[1])
    output = tmp_path / "valid-auth-blocked"
    auth = ExecutionAuthorization(
        human_approval_token="HUMAN_AUTH_TOKEN_TEST_VALID",
        scientific_protocol_approved=True,
        authorized_max_requests=10,
        allow_live_dispatch=True,
        d1_raw_response_policy_approved="RECORD_ONLY",
        d7_dataset_scope_approved="FULL_BENCHMARK",
    )
    with pytest.raises(
        LiveExecutionBlockedError, match="live experiment execution is not enabled in this session"
    ):
        run_live_experiment(plan, output, auth)
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
    report_neg = check_live_execution_gates(
        plan,
        ExecutionAuthorization(
            human_approval_token="TOKEN",
            scientific_protocol_approved=True,
            authorized_max_requests=-5,
            allow_live_dispatch=True,
            d1_raw_response_policy_approved="RECORD_ONLY",
            d7_dataset_scope_approved="FULL_BENCHMARK",
        ),
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
