"""Known synthetic infrastructure fixtures; no scientific predictions or network."""

import json
import os
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import faiss
import numpy as np
import pytest

from src.experiment.__main__ import main
from src.experiment.config import canonical_bytes, digest, load_plan, parse_json
from src.experiment.runner import (
    JournalBudget,
    MockProvider,
    MockReply,
    run_mock_experiment,
)
from src.experiment.schemas import CONDITIONS, ExperimentConfig, ExperimentRecord

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def forbid_provider_construction(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("unexpected provider or embedding model construction")

    monkeypatch.setattr("src.llm.client.openai.OpenAI", fail)
    monkeypatch.setattr("src.retrieval.retriever.SentenceTransformerEmbedder", fail)


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


def change_config(bundle, mutate):
    _, path, original = bundle
    config = deepcopy(original)
    mutate(config)
    path.write_bytes(canonical_bytes(config))
    return path


def records_in(directory):
    return [
        parse_json(line)
        for condition in CONDITIONS
        for line in (directory / f"{condition}_predictions.jsonl").read_bytes().splitlines()
        if (directory / f"{condition}_predictions.jsonl").is_file()
    ]


def test_canonical_dry_run_counts_and_no_writes(monkeypatch):
    def fail(*args, **kwargs):
        raise AssertionError("dry-run attempted a write")

    monkeypatch.setattr(Path, "write_bytes", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "mkdir", fail)
    plan = load_plan(ROOT / "config" / "experiment_config.json")
    assert len(plan.samples) == 1280
    assert len({s.pair_id for s in plan.samples}) == 640
    assert plan.manifest["expected_request_count"] == 6400
    assert plan.manifest["maximum_attempts"] == 25600
    assert plan.config.execution.max_requests is None
    assert plan.report()["scientific_status"] == "NOT_FROZEN"
    assert plan.report()["status"] == "HUMAN_DECISION_REQUIRED"
    assert plan.manifest["status"] == "pre_freeze"
    assert len(plan.snapshots) == 15
    assert (
        plan.manifest["artifacts"]["experiment_config"]["sha256"] == plan.manifest["config_sha256"]
    )


def test_cli_only_dry_run_and_human_gate(bundle, capsys):
    _, path, _ = bundle
    assert main(["--config", str(path), "--dry-run"]) == 2
    assert json.loads(capsys.readouterr().out)["provider_calls"] == 0
    for option in ("--live", "--force", "--freeze"):
        with pytest.raises(SystemExit):
            main(["--dry-run", option])
    with pytest.raises(SystemExit):
        main(["--config", str(path)])


@pytest.mark.parametrize(
    "mutate",
    [
        lambda c: c["execution"].pop("max_requests"),
        lambda c: c["generation"].pop("model"),
        lambda c: c["conditions"].append("unknown"),
        lambda c: c["conditions"].append("no_rag"),
        lambda c: c["retrieval"].update(depths=[1, 3, 5]),
        lambda c: c["generation"].update(temperature=0),
        lambda c: c["logging"].update(raw_response=True),
        lambda c: c["execution"].update(max_requests=True),
        lambda c: c.update(condition_overrides={"rag_k1": {"model": "different"}}),
    ],
)
def test_strict_config_rejections(bundle, mutate):
    with pytest.raises(ValueError):
        load_plan(change_config(bundle, mutate))


def test_small_fixture_and_budget_preflight(bundle):
    plan = load_plan(bundle[1])
    assert [s.sample_id for s in plan.samples] == ["s1", "s2"]
    assert plan.manifest["expected_request_count"] == 10
    assert plan.manifest["maximum_attempts"] == 40
    with pytest.raises(ValueError, match="exceeds explicit"):
        load_plan(change_config(bundle, lambda c: c["execution"].update(max_requests=9)))


def test_inherited_model_cannot_be_overridden(bundle):
    with pytest.raises(ValueError, match="inherit"):
        load_plan(change_config(bundle, lambda c: c["generation"].update(model="replacement")))


@pytest.mark.parametrize(
    "name",
    [
        "inference.jsonl",
        "ground_truth.jsonl",
        "dataset_manifest.json",
        "views.jsonl",
        "pairs.jsonl",
        "split_manifest.json",
        "baseline.txt",
        "model.json",
        "retrieval.json",
        "corpus.jsonl",
        "index.bin",
        "docmap.json",
        "retrieval_manifest.json",
        "registry.json",
    ],
)
def test_every_bound_artifact_rejects_tampering(bundle, name):
    root, path, _ = bundle
    target = root / name
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError, match="SHA256 mismatch"):
        load_plan(path)


def test_rehashed_inference_with_ground_truth_fields_fails_closed(bundle):
    root, path, config = bundle
    inference_path = root / "inference.jsonl"
    rows = [parse_json(line) for line in inference_path.read_bytes().splitlines()]
    rows[0].update(
        ground_truth_technique_ids=["T1059.001"],
        tactic_labels=["execution"],
        rule_mitre_mapping=["T1059.001"],
        pair_metadata={"answer": "T1059.001"},
        evaluation_only="SECRET_GT_METADATA",
    )
    inference_bytes = b"".join(canonical_bytes(row) + b"\n" for row in rows)
    inference_path.write_bytes(inference_bytes)
    config["dataset"]["inference"]["sha256"] = digest(inference_bytes)

    manifest_path = root / "dataset_manifest.json"
    dataset_manifest = parse_json(manifest_path.read_bytes())
    dataset_manifest["files"]["inference.jsonl"] = digest(inference_bytes)
    manifest_bytes = canonical_bytes(dataset_manifest) + b"\n"
    manifest_path.write_bytes(manifest_bytes)
    config["dataset"]["manifest"]["sha256"] = digest(manifest_bytes)
    path.write_bytes(canonical_bytes(config))

    with pytest.raises(ValueError, match="inference rows must contain only"):
        load_plan(path)


def test_parse_uses_the_same_hashed_bytes_even_if_file_changes(bundle, monkeypatch):
    root, path, _ = bundle
    original_read = Path.read_bytes
    count = 0

    def read_once(p):
        nonlocal count
        data = original_read(p)
        if p == root / "inference.jsonl":
            count += 1
            p.write_bytes(b"malicious replacement\n")
        return data

    monkeypatch.setattr(Path, "read_bytes", read_once)
    plan = load_plan(path)
    assert count == 1
    assert plan.samples[0].endpoint_evidence == "  endpoint A\n"


def test_duplicate_config_key_rejected(bundle):
    path = bundle[1]
    content = path.read_bytes()
    path.write_bytes(b'{"schema_version":"1.0.0",' + content[1:])
    with pytest.raises(ValueError, match="duplicate JSON key"):
        load_plan(path)


def test_fixture_runner_real_client_pipeline_wiring_and_no_leakage(bundle, tmp_path):
    plan = load_plan(bundle[1])
    provider = MockProvider()
    output = tmp_path / "mock-results"
    result = run_mock_experiment(plan, output, provider, max_requests=10)
    assert result["complete"] and result["requests_consumed"] == 10
    assert len(provider.calls) == 10
    rows = records_in(output)
    assert len(rows) == 10
    for row in rows:
        ExperimentRecord.model_validate(row)
        assert row["raw_response"] is None and not row["raw_response_logged"]
        assert row["request_attempt_count"] == 1
        assert row["parsed_technique_ids"] == ["T1059.001"]
        assert row["retrieval_k"] == (
            0 if row["condition"] == "no_rag" else int(row["condition"][5:])
        )
    common = None
    for (sample_id, condition), kwargs in provider.calls:
        payload = kwargs.copy()
        text = payload.pop("input")
        assert "SECRET_GT_METADATA" not in text
        assert "label_status" not in text
        sample = next(s for s in plan.samples if s.sample_id == sample_id)
        assert sample.endpoint_evidence in text
        if condition == "no_rag":
            assert text == plan.prompt_template.replace("{RETRIEVED_CONTEXT}", "").replace(
                "{ENDPOINT_EVIDENCE}", sample.endpoint_evidence
            )
        common = payload if common is None else common
        assert payload == common
    assert parse_json((output / "manifest.json").read_bytes())["execution_mode"] == "mock_fixture"


def test_resume_skips_terminal_failures_and_preserves_spending(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "mock-resume"
    first = MockProvider({("s1", "no_rag"): [TimeoutError("temporary"), MockReply("not json")]})
    a = run_mock_experiment(plan, output, first, max_requests=13, stop_after=2)
    assert a["requests_consumed"] == 3 and a["record_count"] == 2
    before = (output / "no_rag_predictions.jsonl").read_bytes()
    second = MockProvider()
    b = run_mock_experiment(plan, output, second, max_requests=13, resume=True)
    assert b["requests_consumed"] == 11 and b["record_count"] == 10
    assert len(second.calls) == 8
    assert ("s1", "no_rag") not in [key for key, _ in second.calls]
    assert (output / "no_rag_predictions.jsonl").read_bytes().startswith(before)
    third = MockProvider()
    assert (
        run_mock_experiment(plan, output, third, max_requests=13, resume=True)["new_records"] == 0
    )
    assert not third.calls


@pytest.mark.parametrize(
    "damage", ["duplicate", "truncated", "manifest", "journal", "lock", "foreign"]
)
def test_resume_rejects_corruption_and_no_double_call(bundle, tmp_path, damage):
    plan = load_plan(bundle[1])
    output = tmp_path / "resume-corrupt"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=1)
    prediction = output / "no_rag_predictions.jsonl"
    if damage == "duplicate":
        prediction.write_bytes(prediction.read_bytes() * 2)
    elif damage == "truncated":
        prediction.write_bytes(prediction.read_bytes()[:-2])
    elif damage == "manifest":
        (output / "manifest.json").write_text("{}")
    elif damage == "journal":
        journal = output / "request_journal.jsonl"
        journal.write_bytes(b"\n".join(journal.read_bytes().splitlines()[:-1]) + b"\n")
    elif damage == "lock":
        (output / ".run.lock").write_text("stale")
    else:
        (output / "foreign.jsonl").write_text("{}")
    fake = MockProvider()
    with pytest.raises(ValueError):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls


def test_inflight_crash_fails_closed_on_resume(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "interrupted"
    with pytest.raises(KeyboardInterrupt):
        run_mock_experiment(
            plan, output, MockProvider({("s1", "no_rag"): [KeyboardInterrupt()]}), max_requests=10
        )
    fake = MockProvider()
    with pytest.raises(ValueError, match="in-flight"):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls


def test_no_overwrite_or_scientific_output_and_no_network_provider(bundle, tmp_path):
    plan = load_plan(bundle[1])
    with pytest.raises(ValueError, match="MockProvider"):
        run_mock_experiment(plan, tmp_path / "x", object(), max_requests=10)
    with pytest.raises(ValueError, match=".tmp"):
        run_mock_experiment(
            plan,
            plan.root / "artifacts" / "experiments" / "fixture",
            MockProvider(),
            max_requests=10,
        )
    output = tmp_path / "existing"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=1)
    with pytest.raises(ValueError, match="already exists"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10)


def test_cannot_write_into_a_sibling_worktree(bundle):
    plan = load_plan(bundle[1])
    sibling = ROOT.parent / "another-worktree" / "artifacts" / "experiments" / "forbidden"
    with pytest.raises(ValueError, match="system temp"):
        run_mock_experiment(plan, sibling, MockProvider(), max_requests=10)
    assert not sibling.exists()


@pytest.mark.parametrize("field", ["model_config", "prompt_template", "samples", "registry_ids"])
def test_derived_input_mutations_fail_before_dispatch(bundle, tmp_path, field):
    plan = load_plan(bundle[1])
    replacement = {
        "model_config": {**plan.model_config, "model": "different-model"},
        "prompt_template": plan.prompt_template + " altered",
        "samples": (replace(plan.samples[0], endpoint_evidence="SECRET_GT"), plan.samples[1]),
        "registry_ids": frozenset({"T9999"}),
    }[field]
    altered = replace(plan, **{field: replacement})
    fake = MockProvider()
    with pytest.raises(ValueError, match="derived execution inputs"):
        run_mock_experiment(altered, tmp_path / "mutated", fake, max_requests=10)
    assert not fake.calls
    assert not (tmp_path / "mutated").exists()


def test_record_rejects_impossible_timestamp_and_retry_accounting(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "record-validation"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=1)
    row = parse_json((output / "no_rag_predictions.jsonl").read_bytes())
    with pytest.raises(ValueError):
        ExperimentRecord.model_validate({**row, "timestamp": "2026-99-99T99:99:99+00:00"})
    with pytest.raises(ValueError, match="retry_count"):
        ExperimentRecord.model_validate({**row, "retry_count": 1, "request_attempt_count": 1})


def test_pipeline_execution_consumes_snapshots_without_reopening_artifacts(
    bundle, tmp_path, monkeypatch
):
    plan = load_plan(bundle[1])
    original = Path.read_bytes
    for file in bundle[0].iterdir():
        file.write_bytes(b"changed after validation")

    def fail(*args, **kwargs):
        raise AssertionError("runner reopened an artifact after validation")

    monkeypatch.setattr(Path, "read_text", fail)
    monkeypatch.setattr(Path, "read_bytes", fail)
    provider = MockProvider()
    output = tmp_path / "snapshot-execution"
    summary = run_mock_experiment(plan, output, provider, max_requests=10)
    assert summary["complete"] and len(provider.calls) == 10
    rows = [parse_json(line) for line in original(output / "no_rag_predictions.jsonl").splitlines()]
    assert rows[0]["prompt_sha256"] == plan.config.prompt.template.sha256


def test_zero_tokens_preserved_through_actual_client(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "zero-token"
    provider = MockProvider({("s1", "no_rag"): [MockReply(input_tokens=0, output_tokens=0)]})
    run_mock_experiment(plan, output, provider, max_requests=10, stop_after=1)
    row = parse_json((output / "no_rag_predictions.jsonl").read_bytes())
    assert (row["prompt_tokens"], row["completion_tokens"], row["total_tokens"]) == (0, 0, 0)


def test_resume_revalidates_claimed_parse_status_against_captured_registry(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "forged-status"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=1)
    prediction = output / "no_rag_predictions.jsonl"
    row = parse_json(prediction.read_bytes())
    row["parsed_technique_ids"] = ["T9999"]
    prediction.write_bytes(canonical_bytes(row) + b"\n")
    journal_path = output / "request_journal.jsonl"
    journal = [parse_json(line) for line in journal_path.read_bytes().splitlines()]
    journal[-1]["record_sha256"] = digest(canonical_bytes(row))
    journal_path.write_bytes(b"".join(canonical_bytes(event) + b"\n" for event in journal))
    fake = MockProvider()
    with pytest.raises(ValueError, match="captured ATT&CK registry"):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls


def test_budget_exhaustion_and_resume_cannot_reset_allowance(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "exhausted"
    fake = MockProvider({("s1", "no_rag"): [TimeoutError("temporary")]})
    result = run_mock_experiment(plan, output, fake, max_requests=10)
    assert result["requests_consumed"] == len(fake.calls) == 10
    assert not result["complete"]
    with pytest.raises(ValueError, match="remaining explicit budget"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=10, resume=True)
    with pytest.raises(ValueError, match="manifest drift"):
        run_mock_experiment(plan, output, MockProvider(), max_requests=11, resume=True)
    with pytest.raises(ValueError, match="cannot be reset"):
        JournalBudget(1, tmp_path / "journal").reset()


def test_schema_does_not_change_canonical_prediction_contract(bundle):
    config = ExperimentConfig.model_validate(bundle[2])
    assert config.generation.model == "gpt-5.6-luna"
    assert config.conditions == list(CONDITIONS)
    from src.llm.schemas import TechniquePrediction

    assert set(TechniquePrediction.model_json_schema()["properties"]) == {"technique_id"}


def test_resume_rejects_rehashed_candidate_outside_captured_corpus(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "forged-candidate"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=2)
    prediction = output / "rag_k1_predictions.jsonl"
    row = parse_json(prediction.read_bytes())
    row["retrieved_candidates"][0]["technique_id"] = "T9999"
    prediction.write_bytes(canonical_bytes(row) + b"\n")
    journal_path = output / "request_journal.jsonl"
    journal = [parse_json(line) for line in journal_path.read_bytes().splitlines()]
    journal[-1]["record_sha256"] = digest(canonical_bytes(row))
    journal_path.write_bytes(b"".join(canonical_bytes(event) + b"\n" for event in journal))
    fake = MockProvider()
    with pytest.raises(ValueError, match="captured corpus"):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls


def test_complete_resume_repairs_stale_summary_without_dispatch(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "stale-summary"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    (output / "run_summary.json").write_text('{"complete": false}', encoding="utf-8")
    fake = MockProvider()
    result = run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls
    assert result["complete"] and result["requests_consumed"] == 10
    assert parse_json((output / "run_summary.json").read_bytes()) == result


def test_complete_resume_repairs_interrupted_summary_replace_without_dispatch(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "interrupted-summary"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    (output / "run_summary.json").unlink()
    (output / "run_summary.json.tmp").write_bytes(b"{")

    fake = MockProvider()
    result = run_mock_experiment(plan, output, fake, max_requests=10, resume=True)

    assert not fake.calls
    assert result["complete"] and result["record_count"] == 10
    assert parse_json((output / "run_summary.json").read_bytes()) == result
    assert not (output / "run_summary.json.tmp").exists()


def test_resume_summary_temp_hardlink_cannot_overwrite_external_file(bundle, tmp_path):
    plan = load_plan(bundle[1])
    output = tmp_path / "hardlinked-summary"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10)
    sentinel = tmp_path / "external-sentinel.txt"
    sentinel.write_bytes(b"do not overwrite me")
    os.link(sentinel, output / "run_summary.json.tmp")

    fake = MockProvider()
    with pytest.raises(ValueError, match="hardlink"):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)

    assert not fake.calls
    assert sentinel.read_bytes() == b"do not overwrite me"


@pytest.mark.parametrize("name", ["request_journal.jsonl", "rag_k1_predictions.jsonl"])
def test_resume_rejects_hardlinked_mutable_outputs_before_dispatch(bundle, tmp_path, name):
    plan = load_plan(bundle[1])
    output = tmp_path / "hardlinked-output"
    run_mock_experiment(plan, output, MockProvider(), max_requests=10, stop_after=2)
    target = output / name
    external = tmp_path / f"external-{name}"
    original = target.read_bytes()
    external.write_bytes(original)
    target.unlink()
    os.link(external, target)

    fake = MockProvider()
    with pytest.raises(ValueError, match="hardlink"):
        run_mock_experiment(plan, output, fake, max_requests=10, resume=True)
    assert not fake.calls
    assert external.read_bytes() == original
