from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.evaluation.retrieval_diagnostics import (
    BenchmarkView,
    calculate_metrics,
    load_benchmark_views,
    make_diagnostic_record,
    run_diagnostics,
)
from src.retrieval.retriever import RetrievalResult


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def _fixture_paths(tmp_path: Path, *, duplicate_input: bool = False, missing_gt: bool = False, bad_id: bool = False):
    inference = [{"sample_id": "view_1", "endpoint_evidence": "EventID 1 cmd.exe"},
                 {"sample_id": "view_2", "endpoint_evidence": "EventID 1 powershell.exe"}]
    if duplicate_input:
        inference[1]["sample_id"] = "view_1"
    gt = [{"view_id": "view_1", "label_status": "mapped", "technique_ids": ["T1059.003"]},
          {"view_id": "view_2", "label_status": "mapped", "technique_ids": ["T1059.001"]}]
    if missing_gt:
        gt = gt[:1]
    if bad_id:
        gt[0]["technique_ids"] = ["not-an-attack-id"]
    views = [{"view_id": "view_1", "pair_id": "pair_1", "view_type": "single"},
             {"view_id": "view_2", "pair_id": "pair_1", "view_type": "contextual"}]
    pairs = [{"pair_id": "pair_1", "split": "test"}]
    paths = {name: tmp_path / f"{name}.jsonl" for name in ("inference", "ground_truth", "views", "pairs")}
    _write_jsonl(paths["inference"], inference)
    _write_jsonl(paths["ground_truth"], gt)
    _write_jsonl(paths["views"], views)
    _write_jsonl(paths["pairs"], pairs)
    return paths


def _split_fixture_paths(tmp_path: Path):
    inference = [
        {"sample_id": "view_test", "endpoint_evidence": "test evidence"},
        {"sample_id": "view_dev", "endpoint_evidence": "dev evidence"},
    ]
    ground_truth = [
        {"view_id": "view_test", "label_status": "mapped", "technique_ids": ["T1059.003"]},
        {"view_id": "view_dev", "label_status": "mapped", "technique_ids": ["T1059.001"]},
    ]
    views = [
        {"view_id": "view_test", "pair_id": "pair_test", "view_type": "single"},
        {"view_id": "view_dev", "pair_id": "pair_dev", "view_type": "contextual"},
    ]
    pairs = [
        {"pair_id": "pair_test", "split": "test"},
        {"pair_id": "pair_dev", "split": "dev"},
    ]
    paths = {name: tmp_path / f"{name}.jsonl" for name in ("inference", "ground_truth", "views", "pairs")}
    _write_jsonl(paths["inference"], inference)
    _write_jsonl(paths["ground_truth"], ground_truth)
    _write_jsonl(paths["views"], views)
    _write_jsonl(paths["pairs"], pairs)
    paths["split_manifest"] = tmp_path / "split_manifest.json"
    paths["split_manifest"].write_text(
        json.dumps({"test": ["pair_test"], "dev": ["pair_dev"]}),
        encoding="utf-8",
    )
    return paths


def _result(rank: int, technique_id: str, score: float = 0.5) -> RetrievalResult:
    return RetrievalResult(technique_id, score, {"name": technique_id}, rank)


def _view(gt: tuple[str, ...] = ("T1059.003",)) -> BenchmarkView:
    return BenchmarkView("view_1", "cmd.exe", "view_1", "pair_1", "TEST", "single", "mapped", "mapped_single", gt)


def test_loader_rejects_duplicate_sample_id(tmp_path: Path):
    paths = _fixture_paths(tmp_path, duplicate_input=True)
    with pytest.raises(ValueError, match="Duplicate sample_id"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_loader_rejects_missing_ground_truth(tmp_path: Path):
    paths = _fixture_paths(tmp_path, missing_gt=True)
    with pytest.raises(ValueError, match="missing_gt"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_loader_rejects_missing_endpoint_evidence(tmp_path: Path):
    paths = _fixture_paths(tmp_path)
    rows = [json.loads(line) for line in paths["inference"].read_text(encoding="utf-8").splitlines()]
    rows[1]["endpoint_evidence"] = ""
    _write_jsonl(paths["inference"], rows)
    with pytest.raises(ValueError, match="missing endpoint_evidence"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_loader_rejects_malformed_attack_id(tmp_path: Path):
    paths = _fixture_paths(tmp_path, bad_id=True)
    with pytest.raises(ValueError, match="malformed ATT&CK IDs"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_orphan_view_is_rejected(tmp_path: Path):
    paths = _fixture_paths(tmp_path)
    views_rows = [json.loads(line) for line in paths["views"].read_text(encoding="utf-8").splitlines() if line]
    views_rows.append({"view_id": "view_orphan", "pair_id": "pair_1", "view_type": "single"})
    _write_jsonl(paths["views"], views_rows)
    with pytest.raises(ValueError, match="orphan_views"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_missing_view_is_rejected(tmp_path: Path):
    paths = _fixture_paths(tmp_path)
    views_rows = [json.loads(line) for line in paths["views"].read_text(encoding="utf-8").splitlines() if line]
    _write_jsonl(paths["views"], views_rows[:1])
    with pytest.raises(ValueError, match="missing_views"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_duplicate_ground_truth_technique_is_rejected(tmp_path: Path):
    paths = _fixture_paths(tmp_path)
    gt_rows = [json.loads(line) for line in paths["ground_truth"].read_text(encoding="utf-8").splitlines() if line]
    gt_rows[0]["technique_ids"] = ["T1059.001", "T1059.001"]
    _write_jsonl(paths["ground_truth"], gt_rows)
    with pytest.raises(ValueError, match="duplicate ATT&CK technique IDs"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])


def test_view_referencing_unknown_pair_is_rejected(tmp_path: Path):
    paths = _fixture_paths(tmp_path)
    views_rows = [json.loads(line) for line in paths["views"].read_text(encoding="utf-8").splitlines() if line]
    views_rows[0]["pair_id"] = "unknown_pair"
    _write_jsonl(paths["views"], views_rows)
    with pytest.raises(ValueError, match="references unknown pair_id"):
        load_benchmark_views(paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"])



def test_record_uses_retrieval_only_and_multi_label_query_hit_is_any_match():
    view = _view(("T1059.003", "T1059.001"))
    record = make_diagnostic_record(view, [_result(1, "T1105"), _result(2, "T1059.001")], {})
    assert record["ground_truth_best_rank"] == 2
    assert record["ground_truth_technique_ranks"] == {"T1059.003": None, "T1059.001": 2}
    assert record["hit_at_1"] is False
    assert record["hit_at_3"] is True
    assert record["recall_at_1"] == 0.0
    assert record["recall_at_3"] == 0.5
    assert record["retrieved_candidates"][0]["technique_id"] == "T1105"


def test_multi_label_metrics_distinguish_query_hit_recall_and_specific_rank():
    view = _view(("T1059.001", "T1059.003"))
    record = make_diagnostic_record(
        view,
        [_result(1, "T1059.003"), _result(2, "T1105")],
        {},
    )
    metrics = calculate_metrics([record])

    assert record["hit_at_1"] is True
    assert record["recall_at_1"] == 0.5
    assert metrics["overall_positive"]["hit_rate_at_1"] == 1.0
    assert metrics["overall_positive"]["macro_recall_at_1"] == 0.5
    assert metrics["overall_positive"]["gt_absent_from_top10_count"] == 0
    assert metrics["per_technique"]["T1059.003"]["hit_rate_at_1"] == 1.0
    assert metrics["per_technique"]["T1059.003"]["gt_absent_from_top10_count"] == 0
    assert metrics["per_technique"]["T1059.001"]["hit_rate_at_1"] == 0.0
    assert metrics["per_technique"]["T1059.001"]["hit_rate_at_10"] == 0.0
    assert metrics["per_technique"]["T1059.001"]["gt_absent_from_top10_count"] == 1
    assert metrics["per_technique"]["T1059.001"]["gt_absent_from_top10_rate"] == 1.0


def test_record_rejects_non_contiguous_ranks():
    with pytest.raises(ValueError, match="contiguous"):
        make_diagnostic_record(_view(), [_result(2, "T1059.003")], {})


def test_negative_has_no_recall_semantics():
    negative_view = BenchmarkView(
        "view_1", "cmd.exe", "view_1", "pair_1", "TEST", "single", "unmapped", "unmapped", tuple()
    )
    record = make_diagnostic_record(negative_view, [_result(1, "T1105")], {})
    assert record["ground_truth_best_rank"] is None
    assert record["hit_at_10"] is None
    metrics = calculate_metrics([record])
    assert metrics["positive_sample_count"] == 0
    assert metrics["negative_sample_count"] == 1
    assert metrics["overall_positive"]["hit_rate_at_1"] is None
    assert metrics["overall_positive"]["macro_recall_at_1"] is None
    assert metrics["category_counts"]["unmapped"] == 1


def test_metrics_known_rank_four():
    record = make_diagnostic_record(
        _view(),
        [_result(1, "T1105"), _result(2, "T1547.001"), _result(3, "T1053.005"), _result(4, "T1059.003")],
        {},
    )
    metrics = calculate_metrics([record])["overall_positive"]
    assert metrics["hit_rate_at_1"] == 0.0
    assert metrics["hit_rate_at_3"] == 0.0
    assert metrics["hit_rate_at_5"] == 1.0
    assert metrics["hit_rate_at_10"] == 1.0
    assert metrics["macro_recall_at_1"] == 0.0
    assert metrics["macro_recall_at_3"] == 0.0
    assert metrics["macro_recall_at_5"] == 1.0
    assert metrics["macro_recall_at_10"] == 1.0
    assert metrics["recall_at_1"] == 0.0
    assert metrics["recall_at_3"] == 0.0
    assert metrics["recall_at_5"] == 1.0
    assert metrics["recall_at_10"] == 1.0


def test_negative_diagnostic_name_describes_counted_value():
    negative_view = BenchmarkView(
        "view_1", "cmd.exe", "view_1", "pair_1", "TEST", "single", "unmapped", "unmapped", tuple()
    )
    record = make_diagnostic_record(negative_view, [_result(1, "T1105")], {})
    diagnostics = calculate_metrics([record])["negative_diagnostics"]
    assert diagnostics["negative_samples_with_candidates"] == 1
    assert "top10_candidate_count" not in diagnostics


def test_split_manifest_must_be_an_exact_partition(tmp_path: Path):
    paths = _split_fixture_paths(tmp_path)
    views = load_benchmark_views(
        paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"], paths["split_manifest"]
    )
    assert {view.pair_id for view in views} == {"pair_test", "pair_dev"}


@pytest.mark.parametrize(
    ("manifest", "pairs", "match"),
    [
        ({"test": [], "dev": ["pair_dev"]}, None, "missing"),
        ({"test": ["pair_test", "pair_test"], "dev": ["pair_dev"]}, None, "Duplicate TEST"),
        ({"test": ["pair_test"], "dev": ["pair_dev", "pair_dev"]}, None, "Duplicate DEV"),
        ({"test": ["pair_test", "pair_dev"], "dev": ["pair_dev"]}, None, "both TEST and DEV"),
        ({"test": ["pair_test", "unknown"], "dev": ["pair_dev"]}, None, "unknown"),
        ({"test": ["pair_dev"], "dev": ["pair_test"]}, None, "disagrees"),
        ({"test": ["pair_test", "pair_dev"], "dev": []}, None, "disagrees"),
    ],
)
def test_split_manifest_invalid_states_fail_closed(tmp_path: Path, manifest, pairs, match):
    paths = _split_fixture_paths(tmp_path)
    if pairs is not None:
        _write_jsonl(paths["pairs"], pairs)
    paths["split_manifest"].write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match=match):
        load_benchmark_views(
            paths["inference"], paths["ground_truth"], paths["views"], paths["pairs"], paths["split_manifest"]
        )


def test_run_is_semantically_deterministic(tmp_path: Path):
    views = [_view()]

    class FakeRetriever:
        config = {"corpus_sha256": "c", "index_sha256": "i", "embedding_model_revision": "r"}

        def retrieve(self, query: str, k: int):
            assert query == "cmd.exe"
            assert k == 10
            return [_result(1, "T1059.003"), _result(2, "T1105")]

    first = tmp_path / "first.jsonl"
    first_metrics = tmp_path / "first.json"
    second = tmp_path / "second.jsonl"
    second_metrics = tmp_path / "second.json"
    run_diagnostics(views, FakeRetriever(), first, first_metrics)
    run_diagnostics(views, FakeRetriever(), second, second_metrics)
    assert first.read_text(encoding="utf-8") == second.read_text(encoding="utf-8")
    assert json.loads(first_metrics.read_text(encoding="utf-8")) == json.loads(second_metrics.read_text(encoding="utf-8"))


def test_retrieval_prefix_consistency():
    """The retriever's supported k values must be prefixes of one ranking."""
    faiss = pytest.importorskip("faiss")
    import numpy as np

    from src.retrieval.retriever import FAISSRetriever, StubEmbedder, normalize_l2

    embedder = StubEmbedder(dimension=8)
    documents = [
        {"technique_id": f"T{index:04d}", "name": str(index), "retrieval_text": f"document {index}"}
        for index in range(12)
    ]
    index = faiss.IndexFlatIP(8)
    index.add(normalize_l2(embedder.encode([doc["retrieval_text"] for doc in documents])))
    retriever = FAISSRetriever(index, documents, {}, embedder=embedder)
    rankings = {k: [row.technique_id for row in retriever.retrieve("query", k)] for k in (1, 3, 5, 10)}
    assert rankings[1] == rankings[3][:1]
    assert rankings[3] == rankings[5][:3]
    assert rankings[5] == rankings[10][:5]
