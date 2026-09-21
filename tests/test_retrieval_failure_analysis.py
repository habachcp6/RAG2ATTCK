"""Unit tests for deterministic retrieval failure analysis (v1.1.0).

Tests cover:
- Pairwise anchor-based comparison semantics (Tests 1-8)
- Exact technique-set consistency (Test 9)
- Overall metric mismatch detection (Test 10)
- T1136 dynamic median (Test 11)
- Canonical end-to-end verification (Test 12)
- Determinism / CLI execution
"""

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
    validate_canonical_input_consistency,
    validate_rank_value,
    verify_canonical_metric_consistency,
    verify_overall_metric_consistency,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DIAGNOSTICS = REPO_ROOT / "artifacts/retrieval/retrieval_diagnostics.jsonl"
CANONICAL_METRICS = REPO_ROOT / "artifacts/retrieval/retrieval_metrics.json"
CANONICAL_VIEWS = REPO_ROOT / "data/ground_truth/synthetic/views.jsonl"
CANONICAL_PAIRS = REPO_ROOT / "data/ground_truth/synthetic/pairs.jsonl"
CANONICAL_GROUND_TRUTH = REPO_ROOT / "data/ground_truth/synthetic/ground_truth.jsonl"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _make_row(
    pair_id: str,
    view_type: str,
    category: str,
    gt_ids: list[str],
    gt_ranks: dict[str, int | None],
) -> dict:
    """Build a minimal diagnostics row for pairwise tests."""
    return {
        "pair_id": pair_id,
        "view_type": view_type,
        "category": category,
        "ground_truth_technique_ids": gt_ids,
        "ground_truth_technique_ranks": gt_ranks,
    }


# ---------------------------------------------------------------------------
# Basic utility tests
# ---------------------------------------------------------------------------

def test_compute_file_sha256(tmp_path: Path) -> None:
    test_file = tmp_path / "hello.txt"
    test_file.write_bytes(b"hello world\n")
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
    # macro recall fields present
    assert "macro_recall_at_1" in overall
    assert "macro_recall_at_3" in overall
    assert "macro_recall_at_5" in overall
    assert "macro_recall_at_10" in overall


# ---------------------------------------------------------------------------
# TEST 1 — Contextual additional label must NOT hijack the comparison
# The most important regression test.
# ---------------------------------------------------------------------------

def test_pairwise_contextual_extra_label_does_not_hijack() -> None:
    """Test 1: Contextual extra label must not hijack single-anchor comparison.

    Scenario:
      single GT = [T1059.003], rank = 5
      contextual GT = [T1059.003, T1105], T1059.003 rank = 8, T1105 rank = 2

    Old (buggy) best_rank method would compare 5 vs 2 -> contextual_better.
    Correct anchor method compares T1059.003: 5 vs 8 -> single_better.
    """
    records = [
        _make_row("p1", "single", "mapped_single",
                  ["T1059.003"], {"T1059.003": 5}),
        _make_row("p1", "contextual", "mapped_multi",
                  ["T1059.003", "T1105"], {"T1059.003": 8, "T1105": 2}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["excluded_pairs"] == 0
    assert result["single_better"] == 1, (
        "Expected single_better=1 (anchor T1059.003: rank 5 < rank 8), "
        "but contextual extra label T1105@rank2 must NOT hijack the comparison"
    )
    assert result["contextual_better"] == 0
    assert result["equal"] == 0


# ---------------------------------------------------------------------------
# TEST 2 — Same anchor technique improves in contextual view
# ---------------------------------------------------------------------------

def test_pairwise_same_technique_improves_in_contextual() -> None:
    """Test 2: Correctly identifies contextual_better when anchor rank improves."""
    records = [
        _make_row("p1", "single", "mapped_single",
                  ["T1059.003"], {"T1059.003": 8}),
        _make_row("p1", "contextual", "mapped_multi",
                  ["T1059.003", "T1105"], {"T1059.003": 3, "T1105": 1}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["contextual_better"] == 1, (
        "T1059.003: single rank=8, contextual rank=3 -> contextual_better"
    )
    assert result["single_better"] == 0
    assert result["equal"] == 0


# ---------------------------------------------------------------------------
# TEST 3 — Same anchor technique ranks equal within Top-10
# ---------------------------------------------------------------------------

def test_pairwise_same_technique_equal_in_top10() -> None:
    """Test 3: Equal outcome when anchor ranks match within Top-10."""
    records = [
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
        _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["equal"] == 1
    assert result["top10_equal"] == 1
    assert result["both_absent_top10"] == 0
    assert result["single_better"] == 0
    assert result["contextual_better"] == 0


# ---------------------------------------------------------------------------
# TEST 4 — Both absent Top-10
# ---------------------------------------------------------------------------

def test_pairwise_both_absent() -> None:
    """Test 4: Both absent -> equal with both_absent_top10 += 1."""
    records = [
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": None}),
        _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": None}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["equal"] == 1
    assert result["both_absent_top10"] == 1
    assert result["top10_equal"] == 0
    assert result["single_better"] == 0
    assert result["contextual_better"] == 0


# ---------------------------------------------------------------------------
# TEST 5 — Single absent, contextual retrieved
# ---------------------------------------------------------------------------

def test_pairwise_single_absent_contextual_retrieved() -> None:
    """Test 5: Single absent, contextual retrieved -> contextual_better."""
    records = [
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": None}),
        _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["contextual_better"] == 1
    assert result["single_better"] == 0
    assert result["equal"] == 0


# ---------------------------------------------------------------------------
# TEST 6 — Single retrieved, contextual absent
# ---------------------------------------------------------------------------

def test_pairwise_single_retrieved_contextual_absent() -> None:
    """Test 6: Single retrieved, contextual absent -> single_better."""
    records = [
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 2}),
        _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": None}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 1
    assert result["single_better"] == 1
    assert result["contextual_better"] == 0
    assert result["equal"] == 0


# ---------------------------------------------------------------------------
# TEST 7 — Anchor missing from contextual GT (fail-closed / explicit exclusion)
# ---------------------------------------------------------------------------

def test_pairwise_anchor_missing_from_contextual_ranks() -> None:
    """Test 7: Anchor not in contextual GT -> excluded with specific reason.

    single GT = [T1059.003]
    contextual GT = [T1105] (no T1059.003 in ranks)
    Must NOT silently compare T1105. Must exclude explicitly.
    """
    records = [
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
        _make_row("p1", "contextual", "mapped_single", ["T1105"], {"T1105": 1}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 0
    assert result["excluded_pairs"] == 1
    assert result["excluded_reasons"]["anchor_missing_from_contextual_ranks"] == 1
    # No comparison outcome was produced
    assert result["single_better"] == 0
    assert result["contextual_better"] == 0
    assert result["equal"] == 0


# ---------------------------------------------------------------------------
# TEST 8 — Multi-label single view is excluded
# ---------------------------------------------------------------------------

def test_pairwise_multi_label_single_view_excluded() -> None:
    """Test 8: Single view with multiple GT techniques -> excluded with reason."""
    records = [
        _make_row("p1", "single", "mapped_multi",
                  ["T1059.003", "T1105"], {"T1059.003": 3, "T1105": 5}),
        _make_row("p1", "contextual", "mapped_multi",
                  ["T1059.003", "T1105"], {"T1059.003": 3, "T1105": 5}),
    ]
    result = analyze_single_vs_contextual_pairs(records)
    assert result["eligible_pairs"] == 0
    assert result["excluded_pairs"] == 1
    assert result["excluded_reasons"]["single_not_mapped_single"] == 1


# ---------------------------------------------------------------------------
# TEST 8b — Partition invariant across mixed pairs
# ---------------------------------------------------------------------------

def test_pairwise_partition_invariant() -> None:
    """Verify partition: single_better + contextual_better + equal == eligible_pairs."""
    records = [
        # eligible: single_better
        _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 2}),
        _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 5}),
        # eligible: contextual_better
        _make_row("p2", "single", "mapped_single", ["T1059.003"], {"T1059.003": 8}),
        _make_row("p2", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
        # eligible: equal (both absent)
        _make_row("p3", "single", "mapped_single", ["T1059.003"], {"T1059.003": None}),
        _make_row("p3", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": None}),
        # excluded: multi-label single
        _make_row("p4", "single", "mapped_multi", ["T1", "T2"], {"T1": 1, "T2": 2}),
        _make_row("p4", "contextual", "mapped_multi", ["T1", "T2"], {"T1": 1, "T2": 2}),
        # excluded: anchor missing from contextual
        _make_row("p5", "single", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
        _make_row("p5", "contextual", "mapped_single", ["T1105"], {"T1105": 1}),
        # no GT (non-positive) — pair_id with single but no GT -> excluded
        {"pair_id": "p6", "view_type": "single", "category": "unmapped",
         "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}},
        {"pair_id": "p6", "view_type": "contextual", "category": "unmapped",
         "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}},
    ]
    result = analyze_single_vs_contextual_pairs(records)

    sb = result["single_better"]
    cb = result["contextual_better"]
    eq = result["equal"]
    eligible = result["eligible_pairs"]

    assert sb + cb + eq == eligible, (
        f"Partition violated: {sb}+{cb}+{eq}={sb+cb+eq} != eligible={eligible}"
    )
    assert result["both_absent_top10"] + result["top10_equal"] == result["equal"]
    assert result["candidate_pairs"] == result["eligible_pairs"] + result["excluded_pairs"]

    # Specific expectations
    assert sb == 1
    assert cb == 1
    assert eq == 1
    assert eligible == 3
    assert result["excluded_pairs"] == 3  # p4, p5, p6


# ---------------------------------------------------------------------------
# TEST 9 — Exact technique set consistency
# ---------------------------------------------------------------------------

def test_exact_technique_set_consistency_missing_from_recomputed() -> None:
    """Test 9a: Canonical has technique missing from recomputed -> ValueError."""
    canonical = {
        "per_technique": {
            "T1": {"evaluated_positive_samples": 5, "gt_absent_from_top10_count": 0,
                   "gt_absent_from_top10_rate": 0.0,
                   "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
                   "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
                   "median_ground_truth_rank_when_retrieved": 1.0},
            "T2": {"evaluated_positive_samples": 3, "gt_absent_from_top10_count": 0,
                   "gt_absent_from_top10_rate": 0.0,
                   "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
                   "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
                   "median_ground_truth_rank_when_retrieved": 1.0},
        }
    }
    # Recomputed only has T1 — missing T2
    recomputed = {
        "T1": {"evaluated_positive_samples": 5, "gt_absent_from_top10_count": 0,
               "gt_absent_from_top10_rate": 0.0,
               "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
               "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
               "median_ground_truth_rank_when_retrieved": 1.0},
    }
    with pytest.raises(ValueError, match="Technique set mismatch"):
        verify_canonical_metric_consistency(recomputed, canonical)


def test_exact_technique_set_consistency_extra_in_recomputed() -> None:
    """Test 9b: Recomputed has extra technique not in canonical -> ValueError."""
    canonical = {
        "per_technique": {
            "T1": {"evaluated_positive_samples": 5, "gt_absent_from_top10_count": 0,
                   "gt_absent_from_top10_rate": 0.0,
                   "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
                   "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
                   "median_ground_truth_rank_when_retrieved": 1.0},
        }
    }
    # Recomputed has T1 + extra T2
    recomputed = {
        "T1": {"evaluated_positive_samples": 5, "gt_absent_from_top10_count": 0,
               "gt_absent_from_top10_rate": 0.0,
               "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
               "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
               "median_ground_truth_rank_when_retrieved": 1.0},
        "T2": {"evaluated_positive_samples": 3, "gt_absent_from_top10_count": 0,
               "gt_absent_from_top10_rate": 0.0,
               "hit_rate_at_1": 1.0, "hit_rate_at_3": 1.0,
               "hit_rate_at_5": 1.0, "hit_rate_at_10": 1.0,
               "median_ground_truth_rank_when_retrieved": 1.0},
    }
    with pytest.raises(ValueError, match="Technique set mismatch"):
        verify_canonical_metric_consistency(recomputed, canonical)


def test_exact_technique_set_consistency_match_passes() -> None:
    """Test 9c: Exact matching technique sets should not raise."""
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
        **matching,
        "T1059.001": {**matching["T1059.001"], "evaluated_positive_samples": 11},
    }
    with pytest.raises(ValueError, match="metric mismatch on evaluated_positive_samples"):
        verify_canonical_metric_consistency(bad_count, canonical)

    # Rate mismatch -> fails closed
    bad_rate = {**matching, "T1059.001": {**matching["T1059.001"], "hit_rate_at_1": 0.25}}
    with pytest.raises(ValueError, match="rate mismatch on hit_rate_at_1"):
        verify_canonical_metric_consistency(bad_rate, canonical)


# ---------------------------------------------------------------------------
# TEST 10 — Overall metric mismatch detection
# ---------------------------------------------------------------------------

def test_overall_metric_mismatch_hit_rate() -> None:
    """Test 10: Overall Hit@10 mismatch -> fail closed."""
    canonical = {
        "overall_positive": {
            "evaluated_positive_samples": 100,
            "gt_absent_from_top10_count": 50,
            "gt_absent_from_top10_rate": 0.5,
            "hit_rate_at_1": 0.1,
            "hit_rate_at_3": 0.2,
            "hit_rate_at_5": 0.3,
            "hit_rate_at_10": 0.5,
            "macro_recall_at_1": 0.09,
            "macro_recall_at_3": 0.18,
            "macro_recall_at_5": 0.27,
            "macro_recall_at_10": 0.45,
            "mean_ground_truth_rank_when_retrieved": 5.0,
            "median_ground_truth_rank_when_retrieved": 5,
        }
    }
    # Matching should not raise
    verify_overall_metric_consistency(dict(canonical["overall_positive"]), canonical)

    # Hit@10 mismatch
    bad = {**canonical["overall_positive"], "hit_rate_at_10": 0.6}
    with pytest.raises(ValueError, match="mismatch on hit_rate_at_10"):
        verify_overall_metric_consistency(bad, canonical)

    # Count mismatch
    bad_count = {**canonical["overall_positive"], "evaluated_positive_samples": 99}
    with pytest.raises(ValueError, match="mismatch on evaluated_positive_samples"):
        verify_overall_metric_consistency(bad_count, canonical)


# ---------------------------------------------------------------------------
# TEST 11 — T1136 dynamic median (not hardcoded None)
# ---------------------------------------------------------------------------

def test_t1136_median_dynamic_with_some_retrieved() -> None:
    """Test 11a: Median computed dynamically when some views ARE retrieved."""
    records = [
        {
            "sample_id": "v1",
            "ground_truth_technique_ids": ["T1136.001"],
            "ground_truth_technique_ranks": {"T1136.001": 2},
        },
        {
            "sample_id": "v2",
            "ground_truth_technique_ids": ["T1136.001"],
            "ground_truth_technique_ranks": {"T1136.001": 6},
        },
        {
            "sample_id": "v3",
            "ground_truth_technique_ids": ["T1136.001"],
            "ground_truth_technique_ranks": {"T1136.001": None},
        },
    ]
    result = analyze_t1136_001_failure(records)
    assert result["evaluated_positive_views"] == 3
    assert result["top10_hit_count"] == 2
    assert result["absent_top10_count"] == 1
    # Median of [2, 6] = 4.0
    assert result["median_ground_truth_rank_when_retrieved"] == pytest.approx(4.0)


def test_t1136_median_dynamic_all_absent() -> None:
    """Test 11b: Median is None when all views are absent from Top-10."""
    records = [
        {
            "sample_id": f"view_{i}",
            "ground_truth_technique_ids": ["T1136.001"],
            "ground_truth_technique_ranks": {"T1136.001": None},
        }
        for i in range(5)
    ]
    result = analyze_t1136_001_failure(records)
    assert result["evaluated_positive_views"] == 5
    assert result["absent_top10_count"] == 5
    assert result["absent_top10_rate"] == 1.0
    assert result["top10_hit_count"] == 0
    assert result["top10_hit_rate"] == 0.0
    # Dynamic median: no retrieved ranks -> None
    assert result["median_ground_truth_rank_when_retrieved"] is None


# ---------------------------------------------------------------------------
# T1105 hard negatives
# ---------------------------------------------------------------------------

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
    assert dist[0]["technique_id"] == "T1218.012"
    assert dist[0]["count"] == 4
    # Tie between T1003.002 and T1053.005 (both count 2): sorted alphabetically
    assert dist[1]["technique_id"] == "T1003.002"
    assert dist[1]["count"] == 2
    assert dist[2]["technique_id"] == "T1053.005"
    assert dist[2]["count"] == 2


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------

def test_deterministic_json_serialization() -> None:
    data = {
        "z": 1,
        "a": [3, 2, 1],
        "m": {"nested_z": 9, "nested_a": 8},
    }
    serialized = serialize_summary_deterministic(data)
    assert serialized.endswith("\n")
    lines = serialized.splitlines()
    assert '  "a": [' in lines[1]
    assert '  "m": {' in lines[6]
    assert '    "nested_a": 8,' in lines[7]
    assert '    "nested_z": 9' in lines[8]
    assert '  "z": 1' in lines[10]

    # Verify byte idempotence
    assert serialize_summary_deterministic(data) == serialized


# ---------------------------------------------------------------------------
# inspect_sample
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# TEST 12 — Canonical end-to-end (corrected expected values)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not CANONICAL_DIAGNOSTICS.exists(), reason="Canonical diagnostics missing")
def test_canonical_analysis_end_to_end() -> None:
    """Test 12: End-to-end verification against canonical repo artifacts.

    Pairwise results are the CORRECTED anchor-based values:
    - Candidate pairs: 670 (all pairs with both single+contextual views)
    - Eligible pairs: 296 (single-view mapped_single with exactly 1 GT technique)
    - Excluded: 374 (non-positive rows: unmapped/ambiguous with empty GT)
    - single_better: 65
    - contextual_better: 23
    - equal: 208
    - both_absent_top10: 147 (subset of equal=208)
    - top10_equal: 61 (subset of equal=208)

    These are the methodologically correct anchor-based values, where anchor
    = single-event view's single GT technique, compared at the same rank in
    the contextual view.
    """
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
    # All macro recall fields present and match canonical
    assert "macro_recall_at_1" in overall
    assert "macro_recall_at_3" in overall
    assert "macro_recall_at_5" in overall
    assert "macro_recall_at_10" in overall
    assert overall["macro_recall_at_10"] == pytest.approx(0.43143738977072316, rel=1e-6)

    # Single vs Contextual verification — CORRECTED anchor-based values
    svc = summary["single_vs_contextual"]
    assert svc["comparison_mode"] == "same_technique_anchor"
    assert svc["candidate_pairs"] == 670
    assert svc["eligible_pairs"] == 296
    assert svc["excluded_pairs"] == 374
    assert svc["excluded_reasons"]["single_not_mapped_single"] == 374
    assert svc["comparable_pairs"] == 296  # alias for eligible_pairs
    assert svc["single_better"] == 65
    assert svc["contextual_better"] == 23
    assert svc["equal"] == 208
    assert svc["both_absent_top10"] == 147
    assert svc["both_absent"] == 147
    assert svc["top10_equal"] == 61
    assert svc["top10_equal_rate"] == pytest.approx(61 / 296)
    assert svc["both_absent_top10"] + svc["top10_equal"] == svc["equal"]
    assert svc["single_better"] + svc["contextual_better"] + svc["equal"] == 296

    # T1105 verification (T1105 analysis is not affected by pairwise fix)
    t1105 = summary["t1105_hard_negatives"]
    assert t1105["evaluated_positive_views"] == 114
    assert t1105["t1218_012_top1_count"] == 48
    assert t1105["t1218_012_top1_rate"] == pytest.approx(48 / 114)
    dist = t1105["top1_competitor_distribution"]
    assert dist[0]["technique_id"] == "T1218.012"
    assert dist[0]["count"] == 48
    assert dist[1]["technique_id"] == "T1003.002"
    assert dist[1]["count"] == 26

    # T1136.001 verification — dynamic median
    t1136 = summary["t1136_001_failure"]
    assert t1136["evaluated_positive_views"] == 99
    assert t1136["top10_hit_count"] == 0
    assert t1136["absent_top10_count"] == 99
    assert t1136["absent_top10_rate"] == 1.0
    # Dynamic median: all absent -> None
    assert t1136["median_ground_truth_rank_when_retrieved"] is None


# ---------------------------------------------------------------------------
# Determinism test
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# REGRESSION TESTS — Structural integrity hardening (Phase 1)
# ---------------------------------------------------------------------------

class TestDuplicatePairViewDetection:
    """§1.1: Duplicate (pair_id, view_type) must raise ValueError."""

    def test_duplicate_single_row_raises(self) -> None:
        records = [
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 5}),
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
        ]
        with pytest.raises(ValueError, match="Duplicate.*pair_id.*view_type"):
            analyze_single_vs_contextual_pairs(records)

    def test_duplicate_contextual_row_raises(self) -> None:
        records = [
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 5}),
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
        ]
        with pytest.raises(ValueError, match="Duplicate.*pair_id.*view_type"):
            analyze_single_vs_contextual_pairs(records)

    def test_duplicate_must_not_silently_change_counts(self) -> None:
        """Ensure duplicate is caught before counts can be affected."""
        records = [
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 5}),
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": 1}),
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 4}),
        ]
        with pytest.raises(ValueError, match="Duplicate"):
            analyze_single_vs_contextual_pairs(records)


class TestRankSchemaValidation:
    """§1.5: Malformed rank values must be rejected."""

    def test_rank_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="must be >= 1"):
            validate_rank_value(0)

    def test_rank_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="must be >= 1"):
            validate_rank_value(-1)

    def test_rank_bool_true_raises(self) -> None:
        with pytest.raises(ValueError, match="got bool"):
            validate_rank_value(True)

    def test_rank_bool_false_raises(self) -> None:
        with pytest.raises(ValueError, match="got bool"):
            validate_rank_value(False)

    def test_rank_string_raises(self) -> None:
        with pytest.raises(ValueError, match="got str"):
            validate_rank_value("3")

    def test_rank_float_raises(self) -> None:
        with pytest.raises(ValueError, match="got float"):
            validate_rank_value(3.0)

    def test_rank_exceeds_max_k_raises(self) -> None:
        with pytest.raises(ValueError, match="exceeds MAX_RETRIEVAL_K"):
            validate_rank_value(11)

    def test_valid_ranks_pass(self) -> None:
        assert validate_rank_value(None) is None
        for r in range(1, 11):
            assert validate_rank_value(r) == r

    def test_malformed_rank_in_pairwise_analysis(self) -> None:
        """Malformed rank in actual pairwise data must propagate."""
        records = [
            _make_row("p1", "single", "mapped_single", ["T1059.003"], {"T1059.003": True}),
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
        ]
        with pytest.raises(ValueError, match="got bool"):
            analyze_single_vs_contextual_pairs(records)


class TestCachedBestRankVerification:
    """§1.6: Recomputed best_rank must match cached field."""

    def test_wrong_cached_best_rank_raises(self) -> None:
        records = [
            {
                "sample_id": "s1",
                "ground_truth_technique_ids": ["T1059.001"],
                "ground_truth_technique_ranks": {"T1059.001": 3},
                "ground_truth_best_rank": 1,  # Wrong! Should be 3
            },
        ]
        with pytest.raises(ValueError, match="recomputed best_rank.*cached"):
            recompute_overall_positive_metrics(records)

    def test_multi_label_wrong_cached_best_raises(self) -> None:
        records = [
            {
                "sample_id": "s1",
                "ground_truth_technique_ids": ["T1059.001", "T1105"],
                "ground_truth_technique_ranks": {"T1059.001": 5, "T1105": 2},
                "ground_truth_best_rank": 5,  # Wrong! Should be min(5,2)=2
            },
        ]
        with pytest.raises(ValueError, match="recomputed best_rank.*cached"):
            recompute_overall_positive_metrics(records)

    def test_correct_cached_best_rank_passes(self) -> None:
        records = [
            {
                "sample_id": "s1",
                "ground_truth_technique_ids": ["T1059.001", "T1105"],
                "ground_truth_technique_ranks": {"T1059.001": 5, "T1105": 2},
                "ground_truth_best_rank": 2,  # Correct: min(5,2)=2
            },
        ]
        result = recompute_overall_positive_metrics(records)
        assert result["evaluated_positive_samples"] == 1


class TestMeanRankVerification:
    """§1.7: Mean rank must be verified in canonical metric consistency."""

    def test_missing_mean_field_in_canonical_raises(self) -> None:
        canonical = {
            "per_technique": {
                "T1": {
                    "evaluated_positive_samples": 5,
                    "gt_absent_from_top10_count": 0,
                    "gt_absent_from_top10_rate": 0.0,
                    "hit_rate_at_1": 1.0,
                    "hit_rate_at_3": 1.0,
                    "hit_rate_at_5": 1.0,
                    "hit_rate_at_10": 1.0,
                    "median_ground_truth_rank_when_retrieved": 1.0,
                    # mean_ground_truth_rank_when_retrieved intentionally missing
                },
            }
        }
        recomputed = {
            "T1": {
                "evaluated_positive_samples": 5,
                "gt_absent_from_top10_count": 0,
                "gt_absent_from_top10_rate": 0.0,
                "hit_rate_at_1": 1.0,
                "hit_rate_at_3": 1.0,
                "hit_rate_at_5": 1.0,
                "hit_rate_at_10": 1.0,
                "median_ground_truth_rank_when_retrieved": 1.0,
                "mean_ground_truth_rank_when_retrieved": 1.0,
            },
        }
        with pytest.raises(ValueError, match="mean rank mismatch"):
            verify_canonical_metric_consistency(recomputed, canonical)

    def test_wrong_mean_field_raises(self) -> None:
        canonical = {
            "per_technique": {
                "T1": {
                    "evaluated_positive_samples": 5,
                    "gt_absent_from_top10_count": 0,
                    "gt_absent_from_top10_rate": 0.0,
                    "hit_rate_at_1": 1.0,
                    "hit_rate_at_3": 1.0,
                    "hit_rate_at_5": 1.0,
                    "hit_rate_at_10": 1.0,
                    "median_ground_truth_rank_when_retrieved": 1.0,
                    "mean_ground_truth_rank_when_retrieved": 2.5,
                },
            }
        }
        recomputed = {
            "T1": {
                "evaluated_positive_samples": 5,
                "gt_absent_from_top10_count": 0,
                "gt_absent_from_top10_rate": 0.0,
                "hit_rate_at_1": 1.0,
                "hit_rate_at_3": 1.0,
                "hit_rate_at_5": 1.0,
                "hit_rate_at_10": 1.0,
                "median_ground_truth_rank_when_retrieved": 1.0,
                "mean_ground_truth_rank_when_retrieved": 3.0,  # Wrong
            },
        }
        with pytest.raises(ValueError, match="mean rank mismatch"):
            verify_canonical_metric_consistency(recomputed, canonical)


class TestAnchorIntegrityViolation:
    """§1.3: Anchor missing from single ranks is an integrity violation, not exclusion."""

    def test_anchor_missing_from_single_ranks_raises(self) -> None:
        records = [
            {
                "pair_id": "p1",
                "view_type": "single",
                "category": "mapped_single",
                "ground_truth_technique_ids": ["T1059.003"],
                "ground_truth_technique_ranks": {},  # Anchor missing!
            },
            _make_row("p1", "contextual", "mapped_single", ["T1059.003"], {"T1059.003": 3}),
        ]
        with pytest.raises(ValueError, match="integrity violation"):
            analyze_single_vs_contextual_pairs(records)


class TestProvenanceCrossValidation:
    """§1.8: Cross-validate provenance artifacts."""

    def test_valid_provenance_passes(self) -> None:
        diag = [
            {"sample_id": "v1", "pair_id": "p1", "view_type": "single",
             "ground_truth_technique_ids": ["T1"], "ground_truth_technique_ranks": {"T1": 1}},
            {"sample_id": "v2", "pair_id": "p1", "view_type": "contextual",
             "ground_truth_technique_ids": ["T1"], "ground_truth_technique_ranks": {"T1": 2}},
        ]
        views = [
            {"view_id": "v1", "pair_id": "p1", "view_type": "single"},
            {"view_id": "v2", "pair_id": "p1", "view_type": "contextual"},
        ]
        pairs = [{"pair_id": "p1"}]
        gt = [
            {"view_id": "v1", "technique_ids": ["T1"]},
            {"view_id": "v2", "technique_ids": ["T1"]},
        ]
        # Should not raise
        validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_diagnostic_sample_missing_from_views_raises(self) -> None:
        diag = [{"sample_id": "v_missing", "pair_id": "p1", "view_type": "single",
                 "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}}]
        views = [{"view_id": "v1", "pair_id": "p1", "view_type": "single"}]
        pairs = [{"pair_id": "p1"}]
        gt = [{"view_id": "v1", "technique_ids": []}]
        with pytest.raises(ValueError, match="not found in canonical views"):
            validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_view_type_mismatch_raises(self) -> None:
        diag = [{"sample_id": "v1", "pair_id": "p1", "view_type": "contextual",
                 "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}}]
        views = [{"view_id": "v1", "pair_id": "p1", "view_type": "single"}]
        pairs = [{"pair_id": "p1"}]
        gt = [{"view_id": "v1", "technique_ids": []}]
        with pytest.raises(ValueError, match="View type mismatch"):
            validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_pair_id_mismatch_raises(self) -> None:
        diag = [{"sample_id": "v1", "pair_id": "p_wrong", "view_type": "single",
                 "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}}]
        views = [{"view_id": "v1", "pair_id": "p1", "view_type": "single"}]
        pairs = [{"pair_id": "p1"}, {"pair_id": "p_wrong"}]
        gt = [{"view_id": "v1", "technique_ids": []}]
        with pytest.raises(ValueError, match="Pair ID mismatch"):
            validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_gt_technique_ids_mismatch_raises(self) -> None:
        diag = [{"sample_id": "v1", "pair_id": "p1", "view_type": "single",
                 "ground_truth_technique_ids": ["T1", "T2"],
                 "ground_truth_technique_ranks": {"T1": 1, "T2": 3}}]
        views = [{"view_id": "v1", "pair_id": "p1", "view_type": "single"}]
        pairs = [{"pair_id": "p1"}]
        gt = [{"view_id": "v1", "technique_ids": ["T1"]}]  # Missing T2
        with pytest.raises(ValueError, match="GT technique IDs mismatch"):
            validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_missing_canonical_views_raises(self) -> None:
        diag = [{"sample_id": "v1", "pair_id": "p1", "view_type": "single",
                 "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}}]
        views = [
            {"view_id": "v1", "pair_id": "p1", "view_type": "single"},
            {"view_id": "v2", "pair_id": "p1", "view_type": "contextual"},
        ]
        pairs = [{"pair_id": "p1"}]
        gt = [
            {"view_id": "v1", "technique_ids": []},
            {"view_id": "v2", "technique_ids": []},
        ]
        with pytest.raises(ValueError, match="canonical views missing"):
            validate_canonical_input_consistency(diag, views, pairs, gt)

    def test_duplicate_sample_id_raises(self) -> None:
        diag = [
            {"sample_id": "v1", "pair_id": "p1", "view_type": "single",
             "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}},
            {"sample_id": "v1", "pair_id": "p1", "view_type": "single",
             "ground_truth_technique_ids": [], "ground_truth_technique_ranks": {}},
        ]
        views = [{"view_id": "v1", "pair_id": "p1", "view_type": "single"}]
        pairs = [{"pair_id": "p1"}]
        gt = [{"view_id": "v1", "technique_ids": []}]
        with pytest.raises(ValueError, match="Duplicate sample_id"):
            validate_canonical_input_consistency(diag, views, pairs, gt)
