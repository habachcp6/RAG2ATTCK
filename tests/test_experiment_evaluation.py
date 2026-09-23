"""Offline known-answer fixtures; none of these records are research results."""

import hashlib
import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest

import src.evaluation.experiment_metrics as evaluator_metrics
from src.evaluation.experiment_metrics import (
    CONDITIONS,
    HumanDecisionRequired,
    _load_evaluation_inputs,
    canonical_json_bytes,
    evaluate_conditional_accuracy,
    evaluate_end_to_end,
    export_fixture_diagnostics,
    load_evaluation_inputs,
    retrieval_observations,
)
from src.evaluation.fixture_metrics import (
    FixtureOnlyPolicy,
    single_label_fixture_metrics,
)
from src.experiment.config import load_plan
from src.experiment.runner import MockProvider, run_mock_experiment
from src.experiment.schemas import CONDITIONS as PRODUCER_CONDITIONS
from src.llm.schemas import TechniquePrediction
from tests import test_experiment as experiment_fixtures

producer_bundle = experiment_fixtures.bundle

A, B, C = "T1059.001", "T1105", "T1053.005"


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _dump(path, value):
    path.write_bytes(canonical_json_bytes(value))


def _dump_rows(path, rows):
    path.write_bytes(b"".join(canonical_json_bytes(row) + b"\n" for row in rows))


def _fixture(tmp_path):
    """Eight TEST views, two DEV views; all five execution conditions."""
    fillers = [f"T{2000 + i}" for i in range(10)]
    registry_ids = [A, B, C, "T1059", *fillers]
    truth = [[A], [B], [A, B], [C], [], [], [A], [B], [A], [B]]
    samples = [
        {
            "sample_id": f"s{i}",
            "pair_id": f"p{i // 2}",
            "view_type": "single" if i % 2 == 0 else "contextual",
        }
        for i in range(10)
    ]
    artifact_values = {
        "inference": [
            {"sample_id": s["sample_id"], "endpoint_evidence": f"fixture event {i}"}
            for i, s in enumerate(samples)
        ],
        "ground_truth": [
            {
                "view_id": s["sample_id"],
                "technique_ids": truth[i],
                "label_status": "mapped" if truth[i] else ("unmapped" if i == 4 else "ambiguous"),
            }
            for i, s in enumerate(samples)
        ],
        "views": [
            {
                "view_id": s["sample_id"],
                "pair_id": s["pair_id"],
                "view_type": s["view_type"],
                "event_ids": [f"e{i // 2}"] if i % 2 == 0 else [f"e{i // 2}", f"context{i // 2}"],
            }
            for i, s in enumerate(samples)
        ],
        "corpus": [{"technique_id": tid} for tid in registry_ids],
    }
    artifact_values["pairs"] = [
        {
            "pair_id": f"p{i}",
            "split": "test" if i < 4 else "dev",
            "single_view": artifact_values["views"][2 * i],
            "contextual_view": artifact_values["views"][2 * i + 1],
            "single_ground_truth": artifact_values["ground_truth"][2 * i],
            "contextual_ground_truth": artifact_values["ground_truth"][2 * i + 1],
        }
        for i in range(5)
    ]
    specs = {}
    for name, rows in artifact_values.items():
        path = tmp_path / f"{name}.jsonl"
        _dump_rows(path, rows)
        specs[name] = {"path": path.name, "sha256": _digest(path.read_bytes())}

    def artifact(name, value, *, data=None):
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical_json_bytes(value) if data is None else data)
        specs[name] = {"path": path.name, "sha256": _digest(path.read_bytes())}

    artifact("split_manifest", {"test": [f"p{i}" for i in range(4)], "dev": ["p4"]})
    artifact(
        "attack_registry",
        {
            "objects": [
                {
                    "type": "attack-pattern",
                    "external_references": [{"source_name": "mitre-attack", "external_id": tid}],
                    "x_mitre_deprecated": tid == "T1059",
                }
                for tid in registry_ids
            ]
        },
    )
    artifact("prompt", None, data=b"fixture prompt {ENDPOINT_EVIDENCE} {RETRIEVED_CONTEXT}")
    model = {
        "provider": "fixture",
        "model": "fixture-model",
        "logging_policy": {"log_raw_response": False},
    }
    artifact("model_config", model)
    artifact("index", None, data=b"fixture index - never loaded")
    artifact("document_mapping", [{"technique_id": tid} for tid in registry_ids])
    retrieval = {"supported_k": [1, 3, 5, 10], "corpus_sha256": specs["corpus"]["sha256"]}
    artifact("retrieval_config", retrieval)
    artifact(
        "retrieval_manifest",
        {
            "corpus_sha256": specs["corpus"]["sha256"],
            "index_sha256": specs["index"]["sha256"],
            "document_mapping_sha256": specs["document_mapping"]["sha256"],
        },
    )
    execution = {"retries": 2}
    artifact(
        "experiment_config",
        {"schema_version": "1.0.0", "purpose": "known_answer_fixture_only", "execution": execution},
    )
    artifact(
        "dataset_manifest",
        {
            "benchmark_version": "fixture-only",
            "attack_version": "19.2",
            "state": "frozen",
            "view_count": 10,
            "pair_count": 5,
            "split_counts": {"test": 4, "dev": 1},
            "attack_source_sha256": specs["attack_registry"]["sha256"],
            "files": {
                Path(specs[name]["path"]).name: specs[name]["sha256"]
                for name in ("inference", "ground_truth", "views", "pairs", "split_manifest")
            },
        },
    )
    manifest = {
        "schema_version": "1.0.0",
        "experiment_id": "known-answer-only",
        "status": "pre_freeze",
        "execution_mode": "mock_fixture",
        "git_commit_sha": "1" * 40,
        "config_sha256": specs["experiment_config"]["sha256"],
        "artifacts": specs,
        "model": model,
        "model_version": None,
        "output_schema_sha256": _digest(
            canonical_json_bytes(TechniquePrediction.model_json_schema())
        ),
        "attack_release": "19.2",
        "benchmark_version": "fixture-only",
        "split": "test",
        "conditions": list(CONDITIONS),
        "retrieval": retrieval,
        "sample_ids": [f"s{i}" for i in range(8)],
        "samples": samples[:8],
        "expected_request_count": 40,
        "maximum_attempts": 120,
        "execution": execution,
    }
    manifest_path = tmp_path / "manifest.json"
    _dump(manifest_path, manifest)
    predictions = {}
    first_candidates = [A, C, B, B, A, B, C, B]
    for condition in CONDITIONS:
        k = 0 if condition == "no_rag" else int(condition[5:])
        rows = []
        for i, sample in enumerate(samples[:8]):
            candidates = [first_candidates[i], *fillers]
            if i == 1:
                candidates[2] = B
            if i == 6:
                candidates[2] = A
            # Eight records include invalid syntax, provider/parser failure,
            # multi-label GT, empty GT and retired-but-present registry ID.
            statuses = [
                "VALID",
                "VALID",
                "VALID",
                "INVALID_ID",
                "API_FAILURE",
                "MALFORMED_RESPONSE",
                "VALID",
                "VALID",
            ]
            parsed = [[A], [C], [B], ["not-an-id"], [], [], [A], ["T1059"]]
            row = {
                "schema_version": "1.0.0",
                "execution_mode": "mock_fixture",
                "experiment_id": manifest["experiment_id"],
                "run_id": "fixture-run",
                "manifest_sha256": _digest(canonical_json_bytes(manifest)),
                **sample,
                "condition": condition,
                "retrieval_k": k,
                "provider": model["provider"],
                "model": model["model"],
                "model_version": None,
                "output_schema_sha256": manifest["output_schema_sha256"],
                "ground_truth_version": "fixture-only",
                "attack_release": "19.2",
                "retrieved_candidates": [
                    {"technique_id": tid, "rank": rank, "score": 1.0 / rank}
                    for rank, tid in enumerate(candidates[:k], 1)
                ],
                "raw_response": None,
                "raw_response_logged": False,
                "parsed_technique_ids": parsed[i],
                "parse_status": statuses[i],
                "prompt_tokens": 10,
                "completion_tokens": 2,
                "total_tokens": 12,
                "latency_ms": 1.5,
                "retry_count": 0,
                "request_attempt_count": 1,
                "error_type": None,
                "error_message": None,
                "success": statuses[i] == "VALID",
                "timestamp": "2026-09-22T00:00:00Z",
                "terminal": True,
            }
            for field, name in (
                ("prompt_sha256", "prompt"),
                ("model_config_sha256", "model_config"),
                ("dataset_sha256", "inference"),
                ("ground_truth_sha256", "ground_truth"),
                ("corpus_sha256", "corpus"),
                ("index_sha256", "index"),
            ):
                row[field] = specs[name]["sha256"]
            rows.append(row)
        path = tmp_path / f"{condition}_predictions.jsonl"
        _dump_rows(path, rows)
        predictions[condition] = path
    return manifest_path, predictions, manifest


def _load(tmp_path, fixture):
    return _load_evaluation_inputs(
        fixture[0],
        fixture[1],
        repository_root=tmp_path,
        expected_sample_count=8,
        verify_journal=False,
    )


def _change_row(fixture, field, value, condition="rag_k3", index=0):
    path = fixture[1][condition]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    rows[index][field] = value
    _dump_rows(path, rows)


def _rebind_dataset_artifact(tmp_path, fixture, name, rows):
    """Rehash all external references; leave the other authoritative bytes intact."""
    manifest = fixture[2]
    spec = manifest["artifacts"][name]
    path = tmp_path / spec["path"]
    _dump_rows(path, rows)
    spec["sha256"] = _digest(path.read_bytes())
    dataset_spec = manifest["artifacts"]["dataset_manifest"]
    dataset_path = tmp_path / dataset_spec["path"]
    dataset = json.loads(dataset_path.read_bytes())
    dataset["files"][path.name] = spec["sha256"]
    _dump(dataset_path, dataset)
    dataset_spec["sha256"] = _digest(dataset_path.read_bytes())
    _dump(fixture[0], manifest)
    for prediction_path in fixture[1].values():
        predictions = [json.loads(line) for line in prediction_path.read_bytes().splitlines()]
        for prediction in predictions:
            prediction["manifest_sha256"] = _digest(canonical_json_bytes(manifest))
            prediction["ground_truth_sha256"] = manifest["artifacts"]["ground_truth"]["sha256"]
            prediction["dataset_sha256"] = manifest["artifacts"]["inference"]["sha256"]
        _dump_rows(prediction_path, predictions)


def _rebind_manifest(fixture):
    _dump(fixture[0], fixture[2])
    for path in fixture[1].values():
        rows = [json.loads(line) for line in path.read_bytes().splitlines()]
        for row in rows:
            row["manifest_sha256"] = _digest(canonical_json_bytes(fixture[2]))
        _dump_rows(path, rows)


def test_rehashed_inference_cannot_carry_ground_truth_fields(tmp_path):
    fixture = _fixture(tmp_path)
    path = tmp_path / fixture[2]["artifacts"]["inference"]["path"]
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    rows[0]["technique_ids"] = [A]
    _rebind_dataset_artifact(tmp_path, fixture, "inference", rows)
    with pytest.raises(ValueError, match="inference fields"):
        _load(tmp_path, fixture)


@pytest.mark.parametrize("absolute", [False, True])
def test_manifest_artifact_path_cannot_escape_repository_root(tmp_path, absolute):
    root = tmp_path / "repo"
    root.mkdir()
    fixture = _fixture(root)
    outside = tmp_path / "external"
    outside.mkdir()
    external_inference = outside / "inference.jsonl"
    external_inference.write_bytes((root / "inference.jsonl").read_bytes())
    fixture[2]["artifacts"]["inference"]["path"] = (
        str(external_inference) if absolute else "../external/inference.jsonl"
    )
    _rebind_manifest(fixture)
    with pytest.raises(ValueError, match="artifact path escapes repository root"):
        _load(root, fixture)


def test_rehashed_document_mapping_must_equal_corpus(tmp_path):
    fixture = _fixture(tmp_path)
    manifest = fixture[2]
    mapping_spec = manifest["artifacts"]["document_mapping"]
    mapping_path = tmp_path / mapping_spec["path"]
    mapping = json.loads(mapping_path.read_bytes())
    mapping[0], mapping[1] = mapping[1], mapping[0]
    _dump(mapping_path, mapping)
    mapping_spec["sha256"] = _digest(mapping_path.read_bytes())
    retrieval_spec = manifest["artifacts"]["retrieval_manifest"]
    retrieval_path = tmp_path / retrieval_spec["path"]
    retrieval_manifest = json.loads(retrieval_path.read_bytes())
    retrieval_manifest["document_mapping_sha256"] = mapping_spec["sha256"]
    _dump(retrieval_path, retrieval_manifest)
    retrieval_spec["sha256"] = _digest(retrieval_path.read_bytes())
    _rebind_manifest(fixture)
    with pytest.raises(ValueError, match="document mapping differs from corpus"):
        _load(tmp_path, fixture)


def test_dataset_manifest_counts_must_match_captured_rows(tmp_path):
    fixture = _fixture(tmp_path)
    manifest = fixture[2]
    dataset_spec = manifest["artifacts"]["dataset_manifest"]
    dataset_path = tmp_path / dataset_spec["path"]
    dataset = json.loads(dataset_path.read_bytes())
    dataset["view_count"] += 1
    _dump(dataset_path, dataset)
    dataset_spec["sha256"] = _digest(dataset_path.read_bytes())
    _rebind_manifest(fixture)
    with pytest.raises(ValueError, match="dataset manifest count mismatch"):
        _load(tmp_path, fixture)


def test_rehashed_manifest_cannot_raise_bound_retry_limit(tmp_path):
    fixture = _fixture(tmp_path)
    fixture[2]["execution"]["retries"] = 3
    _rebind_manifest(fixture)
    with pytest.raises(ValueError, match="execution configuration mismatch"):
        _load(tmp_path, fixture)


def test_record_attempts_cannot_exceed_bound_retry_limit(tmp_path):
    fixture = _fixture(tmp_path)
    _change_row(fixture, "request_attempt_count", 4)
    _change_row(fixture, "retry_count", 3)
    with pytest.raises(ValueError, match="exceeds bound retry policy"):
        _load(tmp_path, fixture)


def test_complete_producer_matrix_requires_complete_journal(producer_bundle, tmp_path):
    root, config_path, _ = producer_bundle
    plan = load_plan(config_path)
    output = tmp_path / "producer-journal"
    summary = run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    assert summary["complete"] and summary["record_count"] == 10
    paths = {
        condition: output / f"{condition}_predictions.jsonl"
        for condition in PRODUCER_CONDITIONS
    }
    inputs = _load_evaluation_inputs(
        output / "manifest.json", paths, repository_root=root, expected_sample_count=2
    )
    assert len(inputs.records) == 10
    with pytest.raises(ValueError, match="journal bypass is limited"):
        _load_evaluation_inputs(
            output / "manifest.json",
            paths,
            repository_root=root,
            expected_sample_count=2,
            verify_journal=False,
        )

    journal_path = output / "request_journal.jsonl"
    journal = journal_path.read_bytes().splitlines()
    assert json.loads(journal[-1])["event"] == "complete"
    journal_path.write_bytes(b"\n".join(journal[:-1]) + b"\n")
    assert all(path.read_bytes().strip() for path in paths.values())
    with pytest.raises(ValueError, match="in-flight|incomplete journal"):
        _load_evaluation_inputs(
            output / "manifest.json", paths, repository_root=root, expected_sample_count=2
        )


@pytest.mark.parametrize(
    ("damage", "message"),
    [
        ("forged_hash", "record/journal hash"),
        ("attempt_ordinal", "invalid attempt journal"),
        ("missing_header", "journal header"),
        ("duplicate_complete", "completed journal lacks execution"),
    ],
)
def test_producer_journal_corruption_is_rejected(producer_bundle, tmp_path, damage, message):
    root, config_path, _ = producer_bundle
    plan = load_plan(config_path)
    output = tmp_path / "producer-journal-corrupt"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    paths = {
        condition: output / f"{condition}_predictions.jsonl"
        for condition in PRODUCER_CONDITIONS
    }
    journal_path = output / "request_journal.jsonl"
    events = [json.loads(line) for line in journal_path.read_bytes().splitlines()]
    if damage == "forged_hash":
        events[-1]["record_sha256"] = "0" * 64
    elif damage == "attempt_ordinal":
        events[2]["ordinal"] = 2
    elif damage == "missing_header":
        events.pop(0)
    else:
        events.append(events[-1])
    _dump_rows(journal_path, events)
    with pytest.raises(ValueError, match=message):
        _load_evaluation_inputs(
            output / "manifest.json", paths, repository_root=root, expected_sample_count=2
        )


@pytest.mark.parametrize("suffix", [b"", b"\n\n"])
def test_prediction_jsonl_requires_complete_nonblank_rows(tmp_path, suffix):
    fixture = _fixture(tmp_path)
    path = fixture[1]["no_rag"]
    original = path.read_bytes()
    path.write_bytes(original.removesuffix(b"\n") + suffix)
    with pytest.raises(ValueError, match="JSONL|blank"):
        _load(tmp_path, fixture)


@pytest.mark.parametrize("tamper", ["replace_gt", "swap_gt", "alter_view", "swap_view"])
def test_rehashed_sidecars_cannot_disagree_with_embedded_pair_authority(tmp_path, tamper):
    fixture = _fixture(tmp_path)
    name = "ground_truth" if tamper.endswith("gt") else "views"
    path = tmp_path / fixture[2]["artifacts"][name]["path"]
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    if tamper == "replace_gt":
        rows[0]["technique_ids"] = [B]
    elif tamper == "swap_gt":
        rows[0]["technique_ids"], rows[1]["technique_ids"] = (
            rows[1]["technique_ids"],
            rows[0]["technique_ids"],
        )
    elif tamper == "alter_view":
        rows[0]["event_ids"] = ["different-evidence"]
    else:
        rows[0]["pair_id"], rows[2]["pair_id"] = rows[2]["pair_id"], rows[0]["pair_id"]
    _rebind_dataset_artifact(tmp_path, fixture, name, rows)
    with pytest.raises(ValueError, match="embedded pair .* disagrees with sidecar"):
        _load(tmp_path, fixture)


@pytest.mark.parametrize(
    "field", ["single_view", "contextual_view", "single_ground_truth", "contextual_ground_truth"]
)
def test_embedded_pair_fields_are_required_even_with_recomputed_hashes(tmp_path, field):
    fixture = _fixture(tmp_path)
    path = tmp_path / fixture[2]["artifacts"]["pairs"]["path"]
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    del rows[0][field]
    _rebind_dataset_artifact(tmp_path, fixture, "pairs", rows)
    with pytest.raises(ValueError, match="missing embedded pair"):
        _load(tmp_path, fixture)


@pytest.mark.parametrize("tamper", ["wrong_pair", "wrong_type", "reused_view", "unknown_view"])
def test_embedded_view_metadata_and_unique_coverage_are_required(tmp_path, tamper):
    fixture = _fixture(tmp_path)
    path = tmp_path / fixture[2]["artifacts"]["pairs"]["path"]
    rows = [json.loads(line) for line in path.read_bytes().splitlines()]
    if tamper == "wrong_pair":
        rows[0]["single_view"]["pair_id"] = "p1"
    elif tamper == "wrong_type":
        rows[0]["single_view"]["view_type"] = "contextual"
    elif tamper == "reused_view":
        rows[1]["single_view"]["view_id"] = "s0"
    else:
        rows[0]["single_view"]["view_id"] = "unknown"
    _rebind_dataset_artifact(tmp_path, fixture, "pairs", rows)
    with pytest.raises(ValueError, match="embedded pair view"):
        _load(tmp_path, fixture)


def test_known_answer_retrieval_and_separate_failure_observations(tmp_path):
    inputs = _load(tmp_path, _fixture(tmp_path))
    assert len(inputs.records) == 40
    assert len(inputs.sample_ids) == 8  # Includes both empty-GT negatives.
    assert inputs.ground_truth["s4"] == ()
    report = retrieval_observations(inputs)
    one, three = report["by_condition"]["rag_k1"], report["by_condition"]["rag_k3"]
    # Six positives: three hit k=1; multi-label hit contributes recall 1/2.
    assert one["positive_samples"] == 6
    assert one["non_positive_samples"] == 2
    assert one["hit_rate"] == 1 / 2
    assert one["macro_recall"] == 5 / 12
    assert one["gt_absent_count"] == 3
    assert three["hit_rate"] == 5 / 6
    assert three["macro_recall"] == 3 / 4
    assert three["gt_absent_count"] == 1
    assert one["parse_status_counts"] == {
        "API_FAILURE": 1,
        "INVALID_ID": 1,
        "MALFORMED_RESPONSE": 1,
        "VALID": 5,
    }
    assert one["retired_id_observation_count"] == 1  # Does not redefine invalid IDs.
    assert "conditional_accuracy" not in one
    assert "invalid_id_rate" not in one
    # s6 is correct but k=1 misses its GT; the observations preserve both facts.
    assert next(
        row for row in inputs.records if row["sample_id"] == "s6" and row["condition"] == "rag_k1"
    )["parsed_technique_ids"] == [A]


def test_known_answer_usage_observations_have_sums_and_presence_only(tmp_path):
    inputs = _load(tmp_path, _fixture(tmp_path))
    report = evaluator_metrics.usage_observations(inputs)
    assert report["canonical_scoring"] == "HUMAN_DECISION_REQUIRED"
    assert set(report["by_condition"]) == set(CONDITIONS)
    for condition in CONDITIONS:
        row = report["by_condition"][condition]
        assert row["sample_count"] == 8
        assert row["prompt_tokens"] == {"sum": 80, "present_count": 8, "missing_count": 0}
        assert row["completion_tokens"] == {"sum": 16, "present_count": 8, "missing_count": 0}
        assert row["total_tokens"] == {"sum": 96, "present_count": 8, "missing_count": 0}
        assert row["latency_ms"] == {"sum": 12.0, "present_count": 8, "missing_count": 0}
        assert not any("average" in key or "rate" in key or "cost" in key for key in row)


def test_usage_observations_preserve_missing_tokens_and_zero_latency(tmp_path):
    fixture = _fixture(tmp_path)
    _change_row(fixture, "prompt_tokens", None)
    _change_row(fixture, "total_tokens", None)
    _change_row(fixture, "latency_ms", 0.0)
    row = evaluator_metrics.usage_observations(_load(tmp_path, fixture))["by_condition"]["rag_k3"]
    assert row["prompt_tokens"] == {"sum": 70, "present_count": 7, "missing_count": 1}
    assert row["completion_tokens"] == {"sum": 16, "present_count": 8, "missing_count": 0}
    assert row["total_tokens"] == {"sum": 84, "present_count": 7, "missing_count": 1}
    assert row["latency_ms"] == {"sum": 10.5, "present_count": 8, "missing_count": 0}


def test_no_positive_retrieval_denominator_is_explicitly_null(tmp_path):
    inputs = _load(tmp_path, _fixture(tmp_path))
    negative_fixture = replace(inputs, ground_truth={sid: () for sid in inputs.sample_ids})
    for row in retrieval_observations(negative_fixture)["by_condition"].values():
        assert row["positive_samples"] == 0
        assert row["non_positive_samples"] == 8
        assert row["hit_rate"] is row["macro_recall"] is None
        assert row["gt_absent_count"] == 0


@pytest.mark.parametrize(
    "status", ["TIMEOUT", "REFUSAL", "INCOMPLETE", "API_FAILURE", "MALFORMED_RESPONSE"]
)
def test_execution_statuses_remain_observations_without_failure_precedence(tmp_path, status):
    fixture = _fixture(tmp_path)
    _change_row(fixture, "parse_status", status)
    _change_row(fixture, "parsed_technique_ids", [])
    _change_row(fixture, "success", False)
    inputs = _load(tmp_path, fixture)
    report = retrieval_observations(inputs)["by_condition"]["rag_k3"]
    assert report["parse_status_counts"][status] >= 1
    assert report["hit_rate"] == 5 / 6


@pytest.mark.parametrize("entrypoint", [evaluate_end_to_end, evaluate_conditional_accuracy])
def test_no_config_flag_or_claimed_approval_can_unblock_scoring(entrypoint):
    with pytest.raises(HumanDecisionRequired, match="HUMAN_DECISION_REQUIRED"):
        entrypoint([], approved=True, force=True, policy={"status": "human_approved"})


def test_canonical_loader_does_not_accept_a_smaller_or_gt_selected_cohort(tmp_path):
    fixture = _fixture(tmp_path)
    with pytest.raises(ValueError, match="cardinality"):
        load_evaluation_inputs(fixture[0], fixture[1], repository_root=tmp_path)


@pytest.mark.parametrize(
    "name",
    [
        "inference",
        "ground_truth",
        "prompt",
        "corpus",
        "index",
        "attack_registry",
        "document_mapping",
        "experiment_config",
    ],
)
def test_hashes_bind_actual_bytes(tmp_path, name):
    fixture = _fixture(tmp_path)
    path = tmp_path / fixture[2]["artifacts"][name]["path"]
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        _load(tmp_path, fixture)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("manifest_sha256", "0" * 64, "manifest_sha256"),
        ("prompt_sha256", "0" * 64, "prompt_sha256"),
        ("ground_truth_sha256", "0" * 64, "ground_truth_sha256"),
        ("provider", "other", "provider"),
        ("model", "other", "model"),
        ("condition", "rag_k5", "condition"),
        ("retrieval_k", 5, "retrieval_k"),
        ("pair_id", "p9", "pair_id"),
        ("terminal", False, "nonterminal"),
        ("raw_response", "hidden raw output", "raw response"),
        ("raw_response_logged", True, "raw response"),
        ("parsed_technique_ids", [A, B], "single-ID"),
        ("parsed_technique_ids", ["T9999"], "ID/status"),
        ("success", False, "success/status"),
        ("parse_status", "UNKNOWN", "unknown parse status"),
        ("total_tokens", 999, "token accounting"),
        ("prompt_tokens", -1, "prompt_tokens"),
        ("retry_count", 2, "retry count"),
        ("request_attempt_count", 0, "attempt accounting"),
        ("latency_ms", -1.0, "latency"),
        ("timestamp", "2026-09-22T00:00:00", "UTC"),
        ("ground_truth_technique_ids", [A], "GT labels are forbidden"),
    ],
)
def test_rejects_envelope_and_provenance_tampering(tmp_path, field, value, message):
    fixture = _fixture(tmp_path)
    _change_row(fixture, field, value)
    with pytest.raises(ValueError, match=message):
        _load(tmp_path, fixture)


def test_missing_duplicate_and_unknown_matrix_rows(tmp_path):
    fixture = _fixture(tmp_path)
    path = fixture[1]["no_rag"]
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    for changed in (rows[:-1], rows + [rows[0]], [{**rows[0], "sample_id": "unknown"}, *rows[1:]]):
        _dump_rows(path, changed)
        with pytest.raises(ValueError, match="missing or unexpected|duplicate"):
            _load(tmp_path, fixture)


def test_no_rag_candidate_and_noncontiguous_rank_rejected(tmp_path):
    fixture = _fixture(tmp_path)
    _change_row(
        fixture, "retrieved_candidates", [{"technique_id": A, "rank": 1, "score": 1.0}], "no_rag"
    )
    with pytest.raises(ValueError, match="candidate count"):
        _load(tmp_path, fixture)
    _change_row(fixture, "retrieved_candidates", [], "no_rag")
    _change_row(
        fixture,
        "retrieved_candidates",
        [{"technique_id": A, "rank": rank, "score": 1.0} for rank in (1, 3, 2)],
    )
    with pytest.raises(ValueError, match="noncontiguous"):
        _load(tmp_path, fixture)


def test_duplicate_candidates_and_unbound_config_hash_rejected(tmp_path):
    fixture = _fixture(tmp_path)
    _change_row(
        fixture,
        "retrieved_candidates",
        [{"technique_id": A, "rank": rank, "score": 1.0} for rank in (1, 2, 3)],
    )
    with pytest.raises(ValueError, match="duplicate retrieved candidate"):
        _load(tmp_path, fixture)
    fixture[2]["config_sha256"] = "0" * 64
    _dump(fixture[0], fixture[2])
    with pytest.raises(ValueError, match="experiment config hash mismatch"):
        _load(tmp_path, fixture)


def test_unknown_condition_and_gt_filtering_rejected(tmp_path):
    fixture = _fixture(tmp_path)
    fixture[2]["conditions"] = ["no_rag", "rag_k2"]
    _dump(fixture[0], fixture[2])
    with pytest.raises(ValueError, match="exact five"):
        _load(tmp_path, fixture)
    fixture[2]["conditions"] = list(CONDITIONS)
    fixture[2]["sample_ids"].remove("s4")
    _dump(fixture[0], fixture[2])
    with pytest.raises(ValueError, match="ALL TEST views"):
        _load(tmp_path, fixture)


def test_json_duplicate_keys_and_nonfinite_values_rejected(tmp_path):
    fixture = _fixture(tmp_path)
    fixture[1]["no_rag"].write_bytes(b'{"sample_id":"s0","sample_id":"s1"}\n')
    with pytest.raises(ValueError, match="duplicate JSON key"):
        _load(tmp_path, fixture)
    fixture[1]["no_rag"].write_bytes(b'{"sample_id":"s0","latency_ms":NaN}\n')
    with pytest.raises(ValueError, match="non-finite JSON"):
        _load(tmp_path, fixture)


def test_shuffled_jsonl_has_identical_exports_and_no_overwrite(tmp_path):
    fixture = _fixture(tmp_path)
    before = retrieval_observations(_load(tmp_path, fixture))
    for path in fixture[1].values():
        path.write_bytes(b"\n".join(reversed(path.read_bytes().splitlines())) + b"\n")
    after = retrieval_observations(_load(tmp_path, fixture))
    first, second = tmp_path / "first.json", tmp_path / "second.json"
    export_fixture_diagnostics(before, first)
    export_fixture_diagnostics(after, second)
    assert first.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        export_fixture_diagnostics(after, first)
    blocked = deepcopy(after)
    blocked["execution_mode"] = "research"
    with pytest.raises(ValueError, match="only gated fixture"):
        export_fixture_diagnostics(blocked, tmp_path / "research.json")
    assert not (tmp_path / "research.json").exists()


def test_fixture_export_cannot_write_outside_system_temp(tmp_path):
    fixture = _fixture(tmp_path)
    report = retrieval_observations(_load(tmp_path, fixture))
    output = (
        Path(__file__).resolve().parents[1] / "artifacts" / "evaluation" / "must-not-exist.json"
    )
    with pytest.raises(ValueError, match="system temporary directory"):
        export_fixture_diagnostics(report, output)
    assert not output.exists()


def test_loader_parses_same_bytes_it_hashes(tmp_path, monkeypatch):
    fixture = _fixture(tmp_path)
    truth_path = tmp_path / fixture[2]["artifacts"]["ground_truth"]["path"]
    original = Path.read_bytes
    reads = []

    def change_after_read(path):
        data = original(path)
        if path == truth_path:
            reads.append(path)
            path.write_bytes(b"corrupt bytes after the snapshot was read")
        return data

    monkeypatch.setattr(Path, "read_bytes", change_after_read)
    inputs = _load(tmp_path, fixture)
    assert inputs.ground_truth["s0"] == (A,)
    assert reads == [truth_path]


def _policy(zero_division=0.0):
    return FixtureOnlyPolicy(
        (A, B, C), zero_division, "all_fixture_rows", "known_answer_fixture_only"
    )


def test_hand_calculated_single_label_fixture_metrics():
    # A: TP2 FP1 FN2, B: TP2 FP1 FN2, C: TP1 FP1 FN3.
    truth = [A] * 4 + [B] * 4 + [C] * 4
    predictions = [A, A, B, None, B, B, C, "T9999", C, A, None, None]
    metrics = single_label_fixture_metrics(truth, predictions, policy=_policy())
    assert metrics["sample_count"] == 12
    assert metrics["exact_accuracy"] == 5 / 12
    assert metrics["per_class"][A] == {
        "tp": 2,
        "fp": 1,
        "fn": 2,
        "precision": 2 / 3,
        "recall": 1 / 2,
        "f1": 4 / 7,
    }
    assert metrics["per_class"][B] == metrics["per_class"][A]
    assert metrics["per_class"][C] == {
        "tp": 1,
        "fp": 1,
        "fn": 3,
        "precision": 1 / 2,
        "recall": 1 / 4,
        "f1": 1 / 3,
    }
    assert metrics["macro_precision"] == pytest.approx(11 / 18)
    assert metrics["macro_recall"] == pytest.approx(5 / 12)
    assert metrics["macro_f1"] == pytest.approx(31 / 63)


def test_perfect_all_wrong_subtechnique_and_empty_fixture():
    truth = [A, B, C] * 3
    perfect = single_label_fixture_metrics(truth, truth, policy=_policy())
    assert perfect["exact_accuracy"] == perfect["macro_f1"] == 1.0
    wrong = single_label_fixture_metrics(truth, [B, C, A] * 3, policy=_policy())
    assert wrong["exact_accuracy"] == wrong["macro_f1"] == 0.0
    parent = single_label_fixture_metrics([A], ["T1059"], policy=_policy())
    assert parent["exact_accuracy"] == 0.0  # No partial-credit policy.
    empty = single_label_fixture_metrics([], [], policy=_policy(None))
    assert empty["exact_accuracy"] is None
    assert empty["macro_precision"] is empty["macro_recall"] is empty["macro_f1"] is None


def test_fixture_policy_is_explicit_and_cannot_score_multilabel_or_empty_gt():
    with pytest.raises(ValueError, match="test-only policy"):
        FixtureOnlyPolicy((A,), 0.0, "all_fixture_rows", "canonical")
    for truth in ([[A, B]], [[]], [None]):
        with pytest.raises(ValueError, match="one GT ID"):
            single_label_fixture_metrics(truth, [A], policy=_policy())
    with pytest.raises(TypeError, match="explicit FixtureOnlyPolicy"):
        single_label_fixture_metrics([A], [A], policy=None)
