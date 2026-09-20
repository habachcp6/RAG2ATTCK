"""Unit tests for deterministic retrieval failure analysis."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.analyze_retrieval_failures import (
    ANALYSIS_VERSION,
    analyze_single_vs_contextual_pairs,
    analyze_t1105_hard_negatives,
    analyze_t1136_001_failure,
    build_failure_analysis_summary,
    compute_file_sha256,
    compute_top_k_hits,
    format_sample_inspection,
    inspect_sample,
    load_json,
    load_jsonl,
    main,
    recompute_overall_positive_metrics,
    recompute_per_technique_metrics,
    resolve_comparison_rank,
    serialize_summary_deterministic,
    verify_canonical_metric_consistency,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIAGNOSTICS = REPO_ROOT / "artifacts/retrieval/retrieval_diagnostics.jsonl"
CANONICAL_METRICS = REPO_ROOT / "artifacts/retrieval/retrieval_metrics.json"
CANONICAL_VIEWS = REPO_ROOT / "data/ground_truth/synthetic/views.jsonl"
CANONICAL_PAIRS = REPO_ROOT / "data/ground_truth/synthetic/pairs.jsonl"
CANONICAL_GROUND_TRUTH = REPO_ROOT / "data/ground_truth/synthetic/ground_truth.jsonl"


def test_compute_file_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "hello.txt"
    test_file.write_bytes(b"hello world\n")
    # sha256("hello world\n") = a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447
    expected_hash = "a948904f2f0f479b8f8197694b30184b0d2ed1c1cd2a1ec0fb85d299a192a447"
    assert compute_file_sha256(test_file) == expected_hash

    with pytest.raises(FileNotFoundError):
        compute_file_sha256(tmp_path / "nonexistent.txt")


def test_load_json_and_jsonl(tmp_path: Path) -> None:
    json_path = tmp_path / "data.json"
    json_path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
    assert load_json(json_path) == {"key": "value"}

    jsonl_path = tmp_path / "data.jsonl"
    jsonl_path.write_text('{"a": 1}\n\n{"b": 2}\n', encoding="utf-8")
    assert load_jsonl(jsonl_path) == [{"a": 1}, {"b": 2}]

    bad_jsonl = tmp_path / "bad.jsonl"
    bad_jsonl.write_text("invalid json line\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON"):
        load_jsonl(bad_jsonl)

    non_object_jsonl = tmp_path / "non_object.jsonl"
    non_object_jsonl.write_text('"just a string"\n', encoding="utf-8")
    with pytest.raises(TypeError, match="Expected JSON object"):
        load_jsonl(non_object_jsonl)

    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "missing.json")

    with pytest.raises(FileNotFoundError):
        load_jsonl(tmp_path / "missing.jsonl")


def test_compute_top_k_hits() -> None:
    assert compute_top_k_hits(1, 1) is True
    assert compute_top_k_hits(1, 3) is True
    assert compute_top_k_hits(2, 1) is False
    assert compute_top_k_hits(3, 3) is True
    assert compute_top_k_hits(4, 3) is False
    assert compute_top_k_hits(5, 5) is True
    assert compute_top_k_hits(6, 5) is False
    assert compute_top_k_hits(10, 10) is True
    assert compute_top_k_hits(11, 10) is False
    assert compute_top_k_hits(None, 10) is False


def test_resolve_comparison_rank_semantics() -> None:
    assert resolve_comparison_rank(1) == 1
    assert resolve_comparison_rank(5) == 5
    assert resolve_comparison_rank(10) == 10
    assert resolve_comparison_rank(None) == 11
    assert resolve_comparison_rank(None, default_absent=15) == 15


def test_recompute_per_technique_metrics_synthetic() -> None:
    records = [
        {
            "sample_id": "s1",
            "ground_truth_technique_ids": ["T1059.001"],
            "ground_truth_technique_ranks": {"T1059.001": 1},
        },
        {
            "sample_id": "s2",
            "ground_truth_technique_ids": ["T1059.001"],
            "ground_truth_technique_ranks": {"T1059.001": 4},
        },
        {
            "sample_id": "s3",
            "ground_truth_technique_ids": ["T1059.001"],
            "ground_truth_technique_ranks": {"T1059.001": None},
        },
        {
            "sample_id": "s4",
            "ground_truth_technique_ids": ["T1105"],
            "ground_truth_technique_ranks": {"T1105": 2},
        },
    ]

    metrics = recompute_per_technique_metrics(records)
    assert "T1059.001" in metrics
    t1 = metrics["T1059.001"]
    assert t1["evaluated_positive_samples"] == 3
    assert t1["hit_rate_at_1"] == pytest.approx(1 / 3)
    assert t1["hit_rate_at_3"] == pytest.approx(1 / 3)
    assert t1["hit_rate_at_5"] == pytest.approx(2 / 3)
    assert t1["hit_rate_at_10"] == pytest.approx(2 / 3)
    assert t1["gt_absent_from_top10_count"] == 1
    assert t1["gt_absent_from_top10_rate"] == pytest.approx(1 / 3)
    assert t1["median_ground_truth_rank_when_retrieved"] == 2.5
    assert t1["mean_ground_truth_rank_when_retrieved"] == 2.5

    t2 = metrics["T1105"]
    assert t2["evaluated_positive_samples"] == 1
    assert t2["hit_rate_at_1"] == 0.0
    assert t2["hit_rate_at_3"] == 1.0
    assert t2["gt_absent_from_top10_count"] == 0


def test_recompute_overall_positive_metrics_synthetic() -> None:
    records = [
        {
            "sample_id": "s1",
            "ground_truth_technique_ids": ["T1059.001"],
            "ground_truth_technique_ranks": {"T1059.001": 1},
            "ground_truth_best_rank": 1,
        },
        {
            "sample_id": "s2",
            "ground_truth_technique_ids": ["T1105"],
            "ground_truth_technique_ranks": {"T1105": None},
            "ground_truth_best_rank": None,
        },
    ]
    overall = recompute_overall_positive_metrics(records)
    assert overall["evaluated_positive_samples"] == 2
    assert overall["hit_rate_at_1"] == 0.5
    assert overall["hit_rate_at_10"] == 0.5
    assert overall["gt_absent_from_top10_count"] == 1
    assert overall["gt_absent_from_top10_rate"] == 0.5
    assert overall["median_ground_truth_rank_when_retrieved"] == 1.0


def test_single_vs_contextual_pair_comparison_synthetic() -> None:
    # 4 pairs:
    # pair_1: single rank 2, contextual rank 5 -> single_better
    # pair_2: single rank 8, contextual rank 3 -> contextual_better
    # pair_3: single rank 4, contextual rank 4 -> equal
    # pair_4: single rank None, contextual rank None -> equal & both_absent_top10
    # pair_5: unmapped category -> should NOT be included in comparable pairs
    records = [
        # pair_1
        {"pair_id": "p1", "view_type": "single", "category": "mapped_single", "ground_truth_best_rank": 2},
        {"pair_id": "p1", "view_type": "contextual", "category": "mapped_single", "ground_truth_best_rank": 5},
        # pair_2
        {"pair_id": "p2", "view_type": "single", "category": "mapped_single", "ground_truth_best_rank": 8},
        {"pair_id": "p2", "view_type": "contextual", "category": "mapped_single", "ground_truth_best_rank": 3},
        # pair_3
        {"pair_id": "p3", "view_type": "single", "category": "mapped_single", "ground_truth_best_rank": 4},
        {"pair_id": "p3", "view_type": "contextual", "category": "mapped_single", "ground_truth_best_rank": 4},
        # pair_4
        {"pair_id": "p4", "view_type": "single", "category": "mapped_single", "ground_truth_best_rank": None},
        {"pair_id": "p4", "view_type": "contextual", "category": "mapped_single", "ground_truth_best_rank": None},
        # pair_5 (non-positive)
        {"pair_id": "p5", "view_type": "single", "category": "unmapped", "ground_truth_best_rank": None},
        {"pair_id": "p5", "view_type": "contextual", "category": "unmapped", "ground_truth_best_rank": None},
    ]

    analysis = analyze_single_vs_contextual_pairs(records)
    assert analysis["comparable_pairs"] == 4
    assert analysis["single_better"] == 1
    assert analysis["contextual_better"] == 1
    assert analysis["equal"] == 2
    assert analysis["both_absent_top10"] == 1
    assert analysis["both_absent"] == 1
    assert analysis["top10_equal"] == 1
    assert analysis["single_better_rate"] == 0.25
    assert analysis["contextual_better_rate"] == 0.25
    assert analysis["equal_rate"] == 0.5
    assert analysis["both_absent_top10_rate"] == 0.25
    assert analysis["top10_equal_rate"] == 0.25
    assert analysis["both_absent_top10"] + analysis["top10_equal"] == analysis["equal"]
    assert "comparison_rank = rank if rank is not None else 11" in analysis["comparison_rule"]


def test_t1105_hard_negatives_distribution_sorting() -> None:
    records = [
        {
            "sample_id": f"s{i}",
            "ground_truth_technique_ids": ["T1105"],
            "retrieved_candidates": [{"rank": 1, "technique_id": "T1218.012"}],
        }
        for i in range(4)
    ] + [
        {
            "sample_id": f"s_b{i}",
            "ground_truth_technique_ids": ["T1105"],
            "retrieved_candidates": [{"rank": 1, "technique_id": "T1003.002"}],
        }
        for i in range(2)
    ] + [
        {
            "sample_id": f"s_c{i}",
            "ground_truth_technique_ids": ["T1105"],
            "retrieved_candidates": [{"rank": 1, "technique_id": "T1053.005"}],
        }
        for i in range(2)
    ] + [
        {
            "sample_id": "other",
            "ground_truth_technique_ids": ["T1059.001"],
            "retrieved_candidates": [{"rank": 1, "technique_id": "T1547.001"}],
        }
    ]

    t1105_analysis = analyze_t1105_hard_negatives(records)
    assert t1105_analysis["evaluated_positive_views"] == 8
    assert t1105_analysis["t1218_012_top1_count"] == 4
    assert t1105_analysis["t1218_012_top1_rate"] == 0.5

    dist = t1105_analysis["top1_competitor_distribution"]
    assert len(dist) == 3
    # First must be T1218.012 with count 4
    assert dist[0]["technique_id"] == "T1218.012"
    assert dist[0]["count"] == 4
    # Tie between T1003.002 and T1053.005 (both count 2): sorted alphabetically
    assert dist[1]["technique_id"] == "T1003.002"
    assert dist[1]["count"] == 2
    assert dist[2]["technique_id"] == "T1053.005"
    assert dist[2]["count"] == 2


def test_t1136_001_failure_synthetic() -> None:
    records = [
        {
            "sample_id": f"view_{i}",
            "ground_truth_technique_ids": ["T1136.001"],
            "ground_truth_technique_ranks": {"T1136.001": None},
        }
        for i in range(5)
    ]
    res = analyze_t1136_001_failure(records)
    assert res["evaluated_positive_views"] == 5
    assert res["absent_top10_count"] == 5
    assert res["absent_top10_rate"] == 1.0
    assert res["top10_hit_count"] == 0
    assert res["top10_hit_rate"] == 0.0


def test_deterministic_json_serialization() -> None:
    data = {
        "z": 1,
        "a": [3, 2, 1],
        "m": {"nested_z": 9, "nested_a": 8},
    }
    serialized = serialize_summary_deterministic(data)
    assert serialized.endswith("\n")
    # Verify sorted keys: "a" appears before "m", "m" before "z"
    lines = serialized.splitlines()
    assert '  "a": [' in lines[1]
    assert '  "m": {' in lines[6]
    assert '    "nested_a": 8,' in lines[7]
    assert '    "nested_z": 9' in lines[8]
    assert '  "z": 1' in lines[10]

    # Verify byte idempotence
    assert serialize_summary_deterministic(data) == serialized


def test_verify_canonical_metric_consistency_checks() -> None:
    canonical = {
        "per_technique": {
            "T1059.001": {
                "evaluated_positive_samples": 10,
                "gt_absent_from_top10_count": 2,
                "gt_absent_from_top10_rate": 0.2,
                "hit_rate_at_1": 0.1,
                "hit_rate_at_3": 0.5,
                "hit_rate_at_5": 0.7,
                "hit_rate_at_10": 0.8,
                "median_ground_truth_rank_when_retrieved": 3.0,
            }
        }
    }

    matching = {
        "T1059.001": {
            "evaluated_positive_samples": 10,
            "gt_absent_from_top10_count": 2,
            "gt_absent_from_top10_rate": 0.2,
            "hit_rate_at_1": 0.1,
            "hit_rate_at_3": 0.5,
            "hit_rate_at_5": 0.7,
            "hit_rate_at_10": 0.8,
            "median_ground_truth_rank_when_retrieved": 3,
        }
    }
    # Should not raise
    verify_canonical_metric_consistency(matching, canonical)

    # Count mismatch -> fails closed
    bad_count = {
        "T1059.001": {
            **matching["T1059.001"],
            "evaluated_positive_samples": 11,
        }
    }
    with pytest.raises(ValueError, match="metric mismatch on evaluated_positive_samples"):
        verify_canonical_metric_consistency(bad_count, canonical)

    # Rate mismatch -> fails closed
    bad_rate = {
        "T1059.001": {
            **matching["T1059.001"],
            "hit_rate_at_1": 0.25,
        }
    }
    with pytest.raises(ValueError, match="rate mismatch on hit_rate_at_1"):
        verify_canonical_metric_consistency(bad_rate, canonical)

    # Missing technique -> fails closed
    missing_tech = {
        "T1059.001": matching["T1059.001"],
        "T9999": matching["T1059.001"],
    }
    with pytest.raises(ValueError, match="missing from canonical metrics"):
        verify_canonical_metric_consistency(missing_tech, canonical)


def test_inspect_sample() -> None:
    records = [
        {
            "sample_id": "view_test_01",
            "pair_id": "pair_01",
            "view_type": "single",
            "split": "TEST",
            "category": "mapped_single",
            "ground_truth_best_rank": 2,
            "ground_truth_technique_ids": ["T1059.001"],
            "ground_truth_technique_ranks": {"T1059.001": 2},
            "hit_at_1": False,
            "hit_at_3": True,
            "hit_at_5": True,
            "hit_at_10": True,
            "retrieved_candidates": [
                {"rank": 1, "technique_id": "T1547.001", "score": 0.512},
                {"rank": 2, "technique_id": "T1059.001", "score": 0.498},
            ],
        }
    ]

    inspected = inspect_sample(records, "view_test_01")
    assert inspected["sample_id"] == "view_test_01"
    assert inspected["ground_truth_technique_ids"] == ["T1059.001"]
    assert inspected["ground_truth_best_rank"] == 2

    formatted = format_sample_inspection(inspected)
    assert "Sample ID: view_test_01" in formatted
    assert "Rank  1: T1547.001 (Score: 0.5120)" in formatted
    assert "Rank  2: T1059.001 (Score: 0.4980)" in formatted

    with pytest.raises(KeyError, match="Sample ID not found: non_existent"):
        inspect_sample(records, "non_existent")


@pytest.mark.skipif(not CANONICAL_DIAGNOSTICS.exists(), reason="Canonical diagnostics missing")
def test_canonical_analysis_end_to_end() -> None:
    """Verify end-to-end failure analysis against canonical repo artifacts."""
    diagnostics_rows = load_jsonl(CANONICAL_DIAGNOSTICS)
    canonical_metrics = load_json(CANONICAL_METRICS)

    hashes = {
        "diagnostics_sha256": compute_file_sha256(CANONICAL_DIAGNOSTICS),
        "ground_truth_sha256": compute_file_sha256(CANONICAL_GROUND_TRUTH),
        "metrics_sha256": compute_file_sha256(CANONICAL_METRICS),
        "pairs_sha256": compute_file_sha256(CANONICAL_PAIRS),
        "views_sha256": compute_file_sha256(CANONICAL_VIEWS),
    }

    summary = build_failure_analysis_summary(
        diagnostics_rows=diagnostics_rows,
        canonical_metrics=canonical_metrics,
        provenance_hashes=hashes,
    )
    assert summary["analysis_version"] == ANALYSIS_VERSION

    # Overall positive verification
    overall = summary["overall_positive"]
    assert overall["evaluated_positive_samples"] == 756
    assert overall["gt_absent_from_top10_count"] == 415
    assert overall["hit_rate_at_1"] == pytest.approx(0.0423280423)
    assert overall["hit_rate_at_10"] == pytest.approx(0.4510582010)

    # Single vs Contextual verification
    svc = summary["single_vs_contextual"]
    assert svc["comparable_pairs"] == 296
    assert svc["single_better"] == 61
    assert svc["contextual_better"] == 52
    assert svc["equal"] == 183
    assert svc["both_absent_top10"] == 130
    assert svc["both_absent"] == 130
    assert svc["top10_equal"] == 53
    assert svc["top10_equal_rate"] == pytest.approx(53 / 296)
    assert svc["both_absent_top10"] + svc["top10_equal"] == svc["equal"]
    assert svc["single_better"] + svc["contextual_better"] + svc["equal"] == 296

    # T1105 verification
    t1105 = summary["t1105_hard_negatives"]
    assert t1105["evaluated_positive_views"] == 114
    assert t1105["t1218_012_top1_count"] == 48
    assert t1105["t1218_012_top1_rate"] == pytest.approx(48 / 114)
    # Competitor distribution top item
    dist = t1105["top1_competitor_distribution"]
    assert dist[0]["technique_id"] == "T1218.012"
    assert dist[0]["count"] == 48
    assert dist[1]["technique_id"] == "T1003.002"
    assert dist[1]["count"] == 26

    # T1136.001 verification
    t1136 = summary["t1136_001_failure"]
    assert t1136["evaluated_positive_views"] == 99
    assert t1136["top10_hit_count"] == 0
    assert t1136["absent_top10_count"] == 99
    assert t1136["absent_top10_rate"] == 1.0


@pytest.mark.skipif(not CANONICAL_DIAGNOSTICS.exists(), reason="Canonical diagnostics missing")
def test_cli_execution_and_repeat_determinism(tmp_path: Path) -> None:
    """Verify CLI main entrypoint and byte-deterministic repeat execution."""
    out_a = tmp_path / "out_a.json"
    out_b = tmp_path / "out_b.json"

    ret_a = main([
        "--diagnostics", str(CANONICAL_DIAGNOSTICS),
        "--metrics", str(CANONICAL_METRICS),
        "--views", str(CANONICAL_VIEWS),
        "--pairs", str(CANONICAL_PAIRS),
        "--ground-truth", str(CANONICAL_GROUND_TRUTH),
        "--output", str(out_a),
        "--quiet",
    ])
    assert ret_a == 0

    ret_b = main([
        "--diagnostics", str(CANONICAL_DIAGNOSTICS),
        "--metrics", str(CANONICAL_METRICS),
        "--views", str(CANONICAL_VIEWS),
        "--pairs", str(CANONICAL_PAIRS),
        "--ground-truth", str(CANONICAL_GROUND_TRUTH),
        "--output", str(out_b),
        "--quiet",
    ])
    assert ret_b == 0

    hash_a = compute_file_sha256(out_a)
    hash_b = compute_file_sha256(out_b)
    assert hash_a == hash_b, f"Deterministic output mismatch: {hash_a} != {hash_b}"
