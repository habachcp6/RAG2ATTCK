"""Deterministic retrieval failure analysis for RAG2ATTCK Task T20.

Analyzes stored scientific artifacts without rerunning retrieval:
- Recomputes per-technique metrics and cross-checks against retrieval_metrics.json.
- Analyzes Single vs Contextual pair rankings using same-technique anchor comparison.
  Anchor rule: use the single-event view's single ground-truth technique ID and compare
  THAT SAME technique's retrieval rank in the corresponding contextual view.
  comparison_rank = rank if rank is not None else 11.
- Analyzes T1105 hard-negative competitors (Top-1 competitor distribution).
- Analyzes T1136.001 complete retrieval failure.
- Provides sample inspection CLI (`--sample <sample_id>`).
- Produces deterministic JSON summary with provenance hashes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from statistics import mean, median
from typing import Any

ANALYSIS_VERSION = "1.1.0"
SUPPORTED_K = (1, 3, 5, 10)
MAX_RETRIEVAL_K = max(SUPPORTED_K)
ABSENT_COMPARISON_RANK = MAX_RETRIEVAL_K + 1
DEFAULT_DIAGNOSTICS_PATH = "artifacts/retrieval/retrieval_diagnostics.jsonl"
DEFAULT_METRICS_PATH = "artifacts/retrieval/retrieval_metrics.json"
DEFAULT_VIEWS_PATH = "data/ground_truth/synthetic/views.jsonl"
DEFAULT_PAIRS_PATH = "data/ground_truth/synthetic/pairs.jsonl"
DEFAULT_GROUND_TRUTH_PATH = "data/ground_truth/synthetic/ground_truth.jsonl"
DEFAULT_OUTPUT_PATH = "artifacts/analysis/t20_retrieval_failure_summary.json"


def compute_file_sha256(path: Path | str) -> str:
    """Compute SHA-256 hex digest of a file in streaming chunks."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found for hash calculation: {target}")
    hasher = hashlib.sha256()
    with target.open("rb") as handle:
        while chunk := handle.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_json(path: Path | str) -> Any:
    """Load and parse a JSON file."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")
    with target.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_jsonl(path: Path | str) -> list[dict[str, Any]]:
    """Load and validate records from a JSONL file."""
    target = Path(path)
    if not target.is_file():
        raise FileNotFoundError(f"File not found: {target}")
    records: list[dict[str, Any]] = []
    with target.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as err:
                raise ValueError(f"{target}:{line_number}: Invalid JSON: {err}") from err
            if not isinstance(obj, dict):
                raise TypeError(
                    f"{target}:{line_number}: Expected JSON object, got {type(obj).__name__}"
                )
            records.append(obj)
    return records


def compute_top_k_hits(rank: int | None, k: int) -> bool:
    """Return True if ground-truth technique was retrieved within top-k ranks."""
    return rank is not None and rank <= k


def resolve_comparison_rank(rank: int | None, default_absent: int = ABSENT_COMPARISON_RANK) -> int:
    """Defined absent rank rule: comparison_rank = rank if rank is not None else 11."""
    return rank if rank is not None else default_absent


def validate_rank_value(value: Any, field_context: str = "") -> int | None:
    """Validate a ground-truth rank value from canonical Top-10 diagnostics.

    Valid values:
    - None (technique not retrieved in Top-k)
    - int in range [1, MAX_RETRIEVAL_K]

    Rejects: bool, zero, negative, float, string, rank > MAX_RETRIEVAL_K.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise ValueError(
            f"Rank must be int or None, got bool: {value!r}"
            f"{f' ({field_context})' if field_context else ''}"
        )
    if not isinstance(value, int):
        raise ValueError(
            f"Rank must be int or None, got {type(value).__name__}: {value!r}"
            f"{f' ({field_context})' if field_context else ''}"
        )
    if value < 1:
        raise ValueError(
            f"Rank must be >= 1, got {value}{f' ({field_context})' if field_context else ''}"
        )
    if value > MAX_RETRIEVAL_K:
        raise ValueError(
            f"Rank {value} exceeds MAX_RETRIEVAL_K={MAX_RETRIEVAL_K}"
            f"{f' ({field_context})' if field_context else ''}"
        )
    return value


def _validate_technique_ids(value: Any, context: str) -> list[str]:
    """Require a JSON list of unique, nonempty technique IDs."""
    if not isinstance(value, list) or any(
        not isinstance(tid, str) or not tid.strip() for tid in value
    ):
        raise ValueError(f"{context}: technique IDs must be a list of nonempty strings")
    if len(value) != len(set(value)):
        raise ValueError(f"{context}: duplicate technique IDs")
    return value


def validate_diagnostic_ground_truth(row: Mapping[str, Any]) -> None:
    """Validate GT structure before eligibility, following the frozen Stage B contract.

    synthetic_validator requires both ambiguous and unmapped GT to have zero
    techniques; retrieval_diagnostics derives mapped_single/multi from GT count.
    """
    context = f"Sample {row.get('sample_id')!r}, pair {row.get('pair_id')!r}"
    ids = _validate_technique_ids(row.get("ground_truth_technique_ids"), context)
    category = row.get("category")
    valid_count = {
        "mapped_single": len(ids) == 1,
        "mapped_multi": len(ids) >= 2,
        "unmapped": len(ids) == 0,
        "ambiguous": len(ids) == 0,
    }
    if not isinstance(category, str) or category not in valid_count:
        raise ValueError(f"{context}: invalid category {category!r}")
    if not valid_count[category]:
        raise ValueError(
            f"{context}: Category/GT count inconsistency: {category!r}, {len(ids)} GT IDs"
        )
    ranks = row.get("ground_truth_technique_ranks")
    if not isinstance(ranks, Mapping):
        raise ValueError(f"{context}: ground_truth_technique_ranks must be a mapping")
    if set(ids) != set(ranks):
        raise ValueError(
            f"{context}: GT/rank keys integrity violation: "
            f"missing={sorted(set(ids) - set(ranks))}, "
            f"extra={sorted(set(ranks) - set(ids), key=str)}"
        )
    for tid, rank in ranks.items():
        validate_rank_value(rank, field_context=f"{context}/{tid}")


def _get_technique_rank(record: Mapping[str, Any], technique_id: str) -> int | None:
    """Extract and validate rank for a specific technique from record ground-truth ranks."""
    ranks = record.get("ground_truth_technique_ranks")
    if isinstance(ranks, Mapping) and technique_id in ranks:
        val = ranks[technique_id]
        return validate_rank_value(val, field_context=f"technique={technique_id}")
    for cand in record.get("retrieved_candidates", ()):
        if cand.get("technique_id") == technique_id:
            val = cand.get("rank")
            return validate_rank_value(val, field_context=f"candidate technique={technique_id}")
    return None


def recompute_per_technique_metrics(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Recompute per-technique retrieval metrics for all mapped techniques."""
    positive_rows = [r for r in diagnostics_rows if r.get("ground_truth_technique_ids")]
    technique_ids = sorted({
        tid for r in positive_rows for tid in r.get("ground_truth_technique_ids", ())
    })

    per_technique: dict[str, dict[str, Any]] = {}
    for tid in technique_ids:
        tech_rows = [r for r in positive_rows if tid in r.get("ground_truth_technique_ids", ())]
        n_pos = len(tech_rows)
        ranks: list[int | None] = [_get_technique_rank(r, tid) for r in tech_rows]
        retrieved_ranks = [r for r in ranks if r is not None and r <= 10]

        hit_1 = sum(1 for r in ranks if r is not None and r <= 1)
        hit_3 = sum(1 for r in ranks if r is not None and r <= 3)
        hit_5 = sum(1 for r in ranks if r is not None and r <= 5)
        hit_10 = sum(1 for r in ranks if r is not None and r <= 10)

        absent_count = sum(1 for r in ranks if r is None or r > 10)
        absent_rate = absent_count / n_pos if n_pos > 0 else None

        # Median rank: only among retrieved (rank <= 10) samples
        med_rank = median(retrieved_ranks) if retrieved_ranks else None
        # Mean rank: only among all non-None ranks (may exceed 10)
        all_retrieved = [r for r in ranks if r is not None]
        mean_rank = mean(all_retrieved) if all_retrieved else None

        per_technique[tid] = {
            "evaluated_positive_samples": n_pos,
            "gt_absent_from_top10_count": absent_count,
            "gt_absent_from_top10_rate": absent_rate,
            "hit_rate_at_1": hit_1 / n_pos if n_pos > 0 else None,
            "hit_rate_at_3": hit_3 / n_pos if n_pos > 0 else None,
            "hit_rate_at_5": hit_5 / n_pos if n_pos > 0 else None,
            "hit_rate_at_10": hit_10 / n_pos if n_pos > 0 else None,
            "mean_ground_truth_rank_when_retrieved": mean_rank,
            "median_ground_truth_rank_when_retrieved": med_rank,
            "positive_sample_count": n_pos,
        }
    return per_technique


def recompute_overall_positive_metrics(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Recompute overall aggregate retrieval metrics across all positive samples."""
    positive_rows = [r for r in diagnostics_rows if r.get("ground_truth_technique_ids")]
    n_pos = len(positive_rows)
    if n_pos == 0:
        return {
            "evaluated_positive_samples": 0,
            "gt_absent_from_top10_count": 0,
            "gt_absent_from_top10_rate": None,
            "hit_rate_at_1": None,
            "hit_rate_at_3": None,
            "hit_rate_at_5": None,
            "hit_rate_at_10": None,
            "macro_recall_at_1": None,
            "macro_recall_at_3": None,
            "macro_recall_at_5": None,
            "macro_recall_at_10": None,
            "mean_ground_truth_rank_when_retrieved": None,
            "median_ground_truth_rank_when_retrieved": None,
        }

    # Recompute best rank from technique rank mapping rather than trusting cached field
    best_ranks: list[int | None] = []
    for r in positive_rows:
        gt_rank_map = r.get("ground_truth_technique_ranks", {})
        valid_ranks = [
            validate_rank_value(v, field_context=f"sample={r.get('sample_id')}/{tid}")
            for tid, v in gt_rank_map.items()
            if v is not None
        ]
        recomputed_best = min(valid_ranks) if valid_ranks else None

        # Cross-check against cached field
        cached_best = r.get("ground_truth_best_rank")
        if recomputed_best != cached_best:
            raise ValueError(
                f"Sample {r.get('sample_id')}: recomputed best_rank={recomputed_best} "
                f"!= cached ground_truth_best_rank={cached_best}. "
                f"Cached field is inconsistent with technique rank mapping."
            )
        best_ranks.append(recomputed_best)
    retrieved_ranks = [r for r in best_ranks if r is not None]

    hit_1 = sum(1 for r in best_ranks if r is not None and r <= 1)
    hit_3 = sum(1 for r in best_ranks if r is not None and r <= 3)
    hit_5 = sum(1 for r in best_ranks if r is not None and r <= 5)
    hit_10 = sum(1 for r in best_ranks if r is not None and r <= 10)

    absent_count = sum(1 for r in best_ranks if r is None or r > 10)
    absent_rate = absent_count / n_pos

    # Calculate macro recall@k for k in {1, 3, 5, 10}
    def _macro_recall_at_k(k: int) -> float | None:
        recalls: list[float] = []
        for r in positive_rows:
            gt_ids = r.get("ground_truth_technique_ids", [])
            if not gt_ids:
                continue
            ranks_dict = r.get("ground_truth_technique_ranks", {})
            hits = sum(
                1 for tid in gt_ids
                if ranks_dict.get(tid) is not None and ranks_dict[tid] <= k
            )
            recalls.append(hits / len(gt_ids))
        return mean(recalls) if recalls else None

    return {
        "evaluated_positive_samples": n_pos,
        "gt_absent_from_top10_count": absent_count,
        "gt_absent_from_top10_rate": absent_rate,
        "hit_rate_at_1": hit_1 / n_pos,
        "hit_rate_at_3": hit_3 / n_pos,
        "hit_rate_at_5": hit_5 / n_pos,
        "hit_rate_at_10": hit_10 / n_pos,
        "macro_recall_at_1": _macro_recall_at_k(1),
        "macro_recall_at_3": _macro_recall_at_k(3),
        "macro_recall_at_5": _macro_recall_at_k(5),
        "macro_recall_at_10": _macro_recall_at_k(10),
        "mean_ground_truth_rank_when_retrieved": (
            mean(retrieved_ranks) if retrieved_ranks else None
        ),
        "median_ground_truth_rank_when_retrieved": (
            median(retrieved_ranks) if retrieved_ranks else None
        ),
    }


def verify_canonical_metric_consistency(
    recomputed_per_technique: Mapping[str, Mapping[str, Any]],
    canonical_metrics: Mapping[str, Any],
    tolerance: float = 1e-9,
) -> None:
    """Verify consistency between recomputed metrics and canonical retrieval_metrics.json.

    Enforces exact technique-set equality and fails closed (raises ValueError) if
    counts differ or rates exceed float tolerance.
    """
    canon_per_tech = canonical_metrics.get("per_technique", {})
    if not isinstance(canon_per_tech, Mapping):
        raise TypeError("Canonical metrics missing 'per_technique' mapping")

    # Enforce exact technique set equality (bidirectional)
    recomputed_ids = set(recomputed_per_technique)
    canonical_ids = set(canon_per_tech)
    if recomputed_ids != canonical_ids:
        missing_from_recomputed = sorted(canonical_ids - recomputed_ids)
        extra_in_recomputed = sorted(recomputed_ids - canonical_ids)
        raise ValueError(
            f"Technique set mismatch: "
            f"missing_from_recomputed={missing_from_recomputed}, "
            f"extra_in_recomputed={extra_in_recomputed}"
        )

    for tid, recomputed in sorted(recomputed_per_technique.items()):
        canon = canon_per_tech.get(tid)
        if not isinstance(canon, Mapping):
            raise TypeError(f"Technique {tid} not an object in canonical metrics")

        # Integer count checks (exact equality)
        int_fields = ("evaluated_positive_samples", "gt_absent_from_top10_count")
        for field in int_fields:
            c_val = canon.get(field)
            r_val = recomputed.get(field)
            if c_val != r_val:
                raise ValueError(
                    f"Technique {tid} metric mismatch on {field}: "
                    f"recomputed={r_val} != canonical={c_val}"
                )

        # Rate checks (tolerance)
        rate_fields = (
            "hit_rate_at_1",
            "hit_rate_at_3",
            "hit_rate_at_5",
            "hit_rate_at_10",
            "gt_absent_from_top10_rate",
        )
        for field in rate_fields:
            c_val = canon.get(field)
            r_val = recomputed.get(field)
            if c_val is None or r_val is None:
                if c_val != r_val:
                    raise ValueError(
                        f"Technique {tid} rate mismatch on {field}: "
                        f"recomputed={r_val} != canonical={c_val}"
                    )
            elif abs(float(r_val) - float(c_val)) > tolerance:
                raise ValueError(
                    f"Technique {tid} rate mismatch on {field}: "
                    f"recomputed={r_val} != canonical={c_val}"
                )

        # Median rank check
        c_med = canon.get("median_ground_truth_rank_when_retrieved")
        r_med = recomputed.get("median_ground_truth_rank_when_retrieved")
        if c_med is None or r_med is None:
            if c_med != r_med:
                raise ValueError(
                    f"Technique {tid} median rank mismatch: recomputed={r_med} != canonical={c_med}"
                )
        elif abs(float(r_med) - float(c_med)) > tolerance:
            raise ValueError(
                f"Technique {tid} median rank mismatch: recomputed={r_med} != canonical={c_med}"
            )

        # Mean rank check
        c_mean = canon.get("mean_ground_truth_rank_when_retrieved")
        r_mean = recomputed.get("mean_ground_truth_rank_when_retrieved")
        if c_mean is None or r_mean is None:
            if c_mean != r_mean:
                raise ValueError(
                    f"Technique {tid} mean rank mismatch: recomputed={r_mean} != canonical={c_mean}"
                )
        elif abs(float(r_mean) - float(c_mean)) > tolerance:
            raise ValueError(
                f"Technique {tid} mean rank mismatch: recomputed={r_mean} != canonical={c_mean}"
            )


def verify_overall_metric_consistency(
    recomputed_overall: Mapping[str, Any],
    canonical_metrics: Mapping[str, Any],
    tolerance: float = 1e-9,
) -> None:
    """Verify overall positive metrics against canonical retrieval_metrics.json.

    Fails closed if counts or rates disagree.
    """
    canon_overall = canonical_metrics.get("overall_positive", {})
    if not isinstance(canon_overall, Mapping):
        raise TypeError("Canonical metrics missing 'overall_positive' mapping")

    # Exact integer fields
    int_fields = ("evaluated_positive_samples", "gt_absent_from_top10_count")
    for field in int_fields:
        c_val = canon_overall.get(field)
        r_val = recomputed_overall.get(field)
        if c_val != r_val:
            raise ValueError(
                f"Overall metric mismatch on {field}: recomputed={r_val} != canonical={c_val}"
            )

    # Float fields with tolerance
    float_fields = (
        "gt_absent_from_top10_rate",
        "hit_rate_at_1",
        "hit_rate_at_3",
        "hit_rate_at_5",
        "hit_rate_at_10",
        "macro_recall_at_1",
        "macro_recall_at_3",
        "macro_recall_at_5",
        "macro_recall_at_10",
        "median_ground_truth_rank_when_retrieved",
        "mean_ground_truth_rank_when_retrieved",
    )
    for field in float_fields:
        c_val = canon_overall.get(field)
        r_val = recomputed_overall.get(field)
        if c_val is None or r_val is None:
            if c_val != r_val:
                raise ValueError(
                    f"Overall metric mismatch on {field}: recomputed={r_val} != canonical={c_val}"
                )
        elif abs(float(r_val) - float(c_val)) > tolerance:
            raise ValueError(
                f"Overall metric mismatch on {field}: recomputed={r_val} != canonical={c_val}"
            )


def analyze_single_vs_contextual_pairs(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Perform pairwise ranking comparison across comparable positive scenario pairs.

    Methodology:
    - Anchor rule: the single-event view's single ground-truth technique ID is selected
      as the anchor technique. Only pairs where the single view has exactly one GT technique
      (mapped_single) are eligible.
    - The anchor technique's retrieval rank is compared across both representations:
        single_rank = single_view["ground_truth_technique_ranks"][anchor]
        contextual_rank = contextual_view["ground_truth_technique_ranks"][anchor]
    - comparison_rank = rank if rank is not None else 11.
    - This ensures apples-to-apples comparison: we measure whether adding contextual events
      improves or degrades retrieval of the SAME ATT&CK technique.
    - If contextual view contains extra GT labels (mapped_multi), only the anchor
      technique's rank in the contextual view is used for comparison.
    - If anchor technique is not present in contextual view's GT rank mapping, the pair
      is excluded with reason "anchor_missing_from_contextual_ranks".

    Counts:
    - single_better: single anchor rank < contextual anchor rank (under absent=11 rule)
    - contextual_better: contextual anchor rank < single anchor rank
    - equal: same rank under absent=11 rule
      - both_absent_top10 (subset of equal): both ranks are None/absent
      - top10_equal (subset of equal): both ranks within Top-10 and tied

    Partition invariant: single_better + contextual_better + equal == eligible_pairs
    """
    pairs_map: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in diagnostics_rows:
        validate_diagnostic_ground_truth(row)
        pair_id = row.get("pair_id")
        view_type = row.get("view_type")
        if not isinstance(pair_id, str) or not pair_id.strip():
            raise ValueError(f"Diagnostic record has invalid pair_id: {pair_id!r}")
        if view_type not in ("single", "contextual"):
            raise ValueError(f"Pair {pair_id!r}: invalid view_type {view_type!r}")
        if view_type in pairs_map[pair_id]:
            raise ValueError(
                f"Duplicate (pair_id={pair_id!r}, view_type={view_type!r}) detected. "
                f"Each pair must have at most one row per view type."
            )
        pairs_map[pair_id][view_type] = row

    candidate_pair_ids = sorted(
        pid
        for pid, views in pairs_map.items()
        if "single" in views and "contextual" in views
    )

    n_candidates = len(candidate_pair_ids)
    single_better = 0
    contextual_better = 0
    equal = 0
    both_absent_top10 = 0
    excluded = 0
    excluded_reasons: Counter[str] = Counter()

    for pid in candidate_pair_ids:
        s_view = pairs_map[pid]["single"]
        c_view = pairs_map[pid]["contextual"]

        s_gt_ids = s_view.get("ground_truth_technique_ids", [])

        # Only eligible if single view has exactly one GT technique (unambiguous anchor)
        if len(s_gt_ids) != 1:
            excluded += 1
            excluded_reasons["single_not_mapped_single"] += 1
            continue

        anchor = s_gt_ids[0]

        s_ranks = s_view.get("ground_truth_technique_ranks", {})
        c_ranks = c_view.get("ground_truth_technique_ranks", {})

        # Schema is valid: an anchor absent from contextual GT is a legitimate exclusion.
        if anchor not in c_ranks:
            excluded += 1
            excluded_reasons["anchor_missing_from_contextual_ranks"] += 1
            continue

        s_rank = validate_rank_value(
            s_ranks[anchor], field_context=f"pair={pid}/single/{anchor}"
        )
        c_rank = validate_rank_value(
            c_ranks[anchor], field_context=f"pair={pid}/contextual/{anchor}"
        )

        s_comp = resolve_comparison_rank(s_rank)
        c_comp = resolve_comparison_rank(c_rank)

        if s_comp < c_comp:
            single_better += 1
        elif c_comp < s_comp:
            contextual_better += 1
        else:
            equal += 1
            if s_comp > MAX_RETRIEVAL_K and c_comp > MAX_RETRIEVAL_K:
                both_absent_top10 += 1

    eligible = n_candidates - excluded
    top10_equal = equal - both_absent_top10

    return {
        "anchor_rule": (
            "Use single-event view's single GT technique as anchor. "
            "Compare anchor technique rank in both views. "
            "comparison_rank = rank if rank is not None else 11."
        ),
        "both_absent": both_absent_top10,
        "both_absent_rate": both_absent_top10 / eligible if eligible else 0.0,
        "both_absent_top10": both_absent_top10,
        "both_absent_top10_rate": both_absent_top10 / eligible if eligible else 0.0,
        "candidate_pairs": n_candidates,
        "comparable_pairs": eligible,
        "comparison_mode": "same_technique_anchor",
        "comparison_rule": "comparison_rank = rank if rank is not None else 11",
        "contextual_better": contextual_better,
        "contextual_better_rate": contextual_better / eligible if eligible else 0.0,
        "eligible_pairs": eligible,
        "equal": equal,
        "equal_rate": equal / eligible if eligible else 0.0,
        "excluded_pairs": excluded,
        "excluded_reasons": dict(sorted(excluded_reasons.items())),
        "single_better": single_better,
        "single_better_rate": single_better / eligible if eligible else 0.0,
        "top10_equal": top10_equal,
        "top10_equal_rate": top10_equal / eligible if eligible else 0.0,
    }


def analyze_t1105_hard_negatives(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Analyze Top-1 competitor distribution for positive views containing T1105.

    Deterministic sorting: count DESC, technique_id ASC.
    """
    t1105_views = [
        r
        for r in diagnostics_rows
        if "T1105" in r.get("ground_truth_technique_ids", ())
    ]
    n_views = len(t1105_views)

    top1_counter: Counter[str] = Counter()
    for r in t1105_views:
        candidates = r.get("retrieved_candidates", ())
        top1 = next((c for c in candidates if c.get("rank") == 1), None)
        if top1 and top1.get("technique_id"):
            top1_counter[str(top1["technique_id"])] += 1
        else:
            top1_counter["NO_CANDIDATE"] += 1

    sorted_competitors = sorted(
        top1_counter.items(),
        key=lambda item: (-item[1], item[0]),
    )

    distribution = [
        {
            "count": count,
            "rate": count / n_views if n_views else 0.0,
            "technique_id": tid,
        }
        for tid, count in sorted_competitors
    ]

    t1218_count = top1_counter.get("T1218.012", 0)
    t1218_rate = t1218_count / n_views if n_views else 0.0

    return {
        "evaluated_positive_views": n_views,
        "t1218_012_top1_count": t1218_count,
        "t1218_012_top1_rate": t1218_rate,
        "top1_competitor_distribution": distribution,
    }


def analyze_t1136_001_failure(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Analyze retrieval performance for T1136.001 positive views.

    The median rank is dynamically calculated from retrieved (rank <= 10) samples.
    If no samples are retrieved in Top-10, median is None.
    """
    t1136_views = [
        r
        for r in diagnostics_rows
        if "T1136.001" in r.get("ground_truth_technique_ids", ())
    ]
    n_views = len(t1136_views)

    ranks = [_get_technique_rank(r, "T1136.001") for r in t1136_views]
    hit_10_count = sum(1 for r in ranks if r is not None and r <= 10)
    absent_count = sum(1 for r in ranks if r is None or r > 10)

    # Dynamic median: computed from retrieved (rank <= 10) samples only
    retrieved_ranks = [r for r in ranks if r is not None and r <= 10]
    median_rank = median(retrieved_ranks) if retrieved_ranks else None

    return {
        "absent_top10_count": absent_count,
        "absent_top10_rate": absent_count / n_views if n_views else 0.0,
        "evaluated_positive_views": n_views,
        "median_ground_truth_rank_when_retrieved": median_rank,
        "top10_hit_count": hit_10_count,
        "top10_hit_rate": hit_10_count / n_views if n_views else 0.0,
    }


def inspect_sample(
    diagnostics_rows: Sequence[Mapping[str, Any]],
    sample_id: str,
) -> dict[str, Any]:
    """Retrieve structured diagnostic data for a specific sample ID."""
    for row in diagnostics_rows:
        if row.get("sample_id") == sample_id:
            return {
                "category": row.get("category"),
                "ground_truth_best_rank": row.get("ground_truth_best_rank"),
                "ground_truth_technique_ids": list(row.get("ground_truth_technique_ids", ())),
                "ground_truth_technique_ranks": dict(row.get("ground_truth_technique_ranks", {})),
                "hit_at_1": row.get("hit_at_1"),
                "hit_at_3": row.get("hit_at_3"),
                "hit_at_5": row.get("hit_at_5"),
                "hit_at_10": row.get("hit_at_10"),
                "pair_id": row.get("pair_id"),
                "retrieved_candidates": list(row.get("retrieved_candidates", ())),
                "sample_id": sample_id,
                "split": row.get("split"),
                "view_type": row.get("view_type"),
            }
    raise KeyError(f"Sample ID not found: {sample_id}")


def format_sample_inspection(data: Mapping[str, Any]) -> str:
    """Format sample inspection result as human-readable text."""
    lines = [
        f"Sample ID: {data.get('sample_id')}",
        f"Pair ID: {data.get('pair_id')}",
        f"View Type: {data.get('view_type')}",
        f"Split: {data.get('split')}",
        f"Category: {data.get('category')}",
        f"Ground-Truth IDs: {data.get('ground_truth_technique_ids')}",
        f"Ground-Truth Technique Ranks: {data.get('ground_truth_technique_ranks')}",
        f"Ground-Truth Best Rank: {data.get('ground_truth_best_rank')}",
        f"Hits: Hit@1={data.get('hit_at_1')}, Hit@3={data.get('hit_at_3')}, "
        f"Hit@5={data.get('hit_at_5')}, Hit@10={data.get('hit_at_10')}",
        "Top Candidates Retrieved:",
    ]
    candidates = data.get("retrieved_candidates", ())
    if not candidates:
        lines.append("  (None)")
    else:
        for cand in candidates:
            rank = cand.get("rank")
            tid = cand.get("technique_id")
            score = cand.get("score")
            score_str = f"{score:.4f}" if isinstance(score, (int, float)) else str(score)
            lines.append(f"  Rank {rank:2d}: {tid} (Score: {score_str})")
    return "\n".join(lines)


def _index_records(
    rows: Sequence[Mapping[str, Any]], key: str, artifact: str,
) -> dict[str, Mapping[str, Any]]:
    """Index canonical records without silently overwriting duplicate identifiers."""
    indexed: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        identifier = row.get(key)
        if not isinstance(identifier, str) or not identifier.strip():
            raise ValueError(f"{artifact}: invalid or missing {key}: {identifier!r}")
        if identifier in indexed:
            raise ValueError(f"Duplicate {key} in {artifact}: {identifier!r}")
        indexed[identifier] = row
    return indexed


def validate_canonical_input_consistency(
    diagnostics_rows: Sequence[Mapping[str, Any]],
    views_rows: Sequence[Mapping[str, Any]],
    pairs_rows: Sequence[Mapping[str, Any]],
    ground_truth_rows: Sequence[Mapping[str, Any]],
) -> None:
    """Validate the frozen Stage B join before any eligibility or metric calculation.

    serialize_dataset emits one GT and diagnostic source view per single/contextual
    view; validate_stage_b requires unique pair/view IDs and matching GT linkage.
    Each pair's embedded views must agree with the standalone views artifact.
    """
    view_by_id = _index_records(views_rows, "view_id", "views")
    gt_by_view = _index_records(ground_truth_rows, "view_id", "ground_truth")
    pair_by_id = _index_records(pairs_rows, "pair_id", "pairs")
    diag_by_id = _index_records(diagnostics_rows, "sample_id", "diagnostics")

    view_ids = set(view_by_id)
    if set(gt_by_view) != view_ids:
        raise ValueError(
            "Ground truth/view ID set mismatch: "
            f"missing_GT={sorted(view_ids - set(gt_by_view))[:5]}, "
            f"unknown_GT={sorted(set(gt_by_view) - view_ids)[:5]}"
        )
    unknown_samples = set(diag_by_id) - view_ids
    if unknown_samples:
        raise ValueError(
            f"Diagnostic samples not found in canonical views: {sorted(unknown_samples)[:5]}"
        )
    missing_samples = view_ids - set(diag_by_id)
    if missing_samples:
        raise ValueError(
            f"{len(missing_samples)} canonical views missing from diagnostics: "
            f"{sorted(missing_samples)[:5]}"
        )

    views_by_pair: dict[str, dict[str, str]] = defaultdict(dict)
    for sid, canon_view in view_by_id.items():
        row = diag_by_id[sid]
        validate_diagnostic_ground_truth(row)
        diag_vtype = row.get("view_type")
        canon_vtype = canon_view.get("view_type")
        if diag_vtype != canon_vtype:
            raise ValueError(
                f"View type mismatch for {sid!r}: "
                f"diagnostic={diag_vtype!r} != canonical view={canon_vtype!r}"
            )
        if canon_vtype not in ("single", "contextual"):
            raise ValueError(f"View {sid!r}: invalid view_type {canon_vtype!r}")

        diag_pid = row.get("pair_id")
        canon_pid = canon_view.get("pair_id")
        for source, pid in (("diagnostic", diag_pid), ("view", canon_pid)):
            if not isinstance(pid, str) or pid not in pair_by_id:
                raise ValueError(
                    f"Pair ID {pid!r} from {source} {sid!r} not found in canonical pairs"
                )
        if diag_pid != canon_pid:
            raise ValueError(
                f"Pair ID mismatch for {sid!r}: "
                f"diagnostic={diag_pid!r} != canonical view={canon_pid!r}"
            )
        if canon_vtype in views_by_pair[canon_pid]:
            raise ValueError(f"Duplicate view_type {canon_vtype!r} for pair_id {canon_pid!r}")
        views_by_pair[canon_pid][canon_vtype] = sid

        canon_gt = gt_by_view[sid]
        canon_gt_ids = _validate_technique_ids(canon_gt.get("technique_ids"), f"GT {sid!r}")
        if set(row["ground_truth_technique_ids"]) != set(canon_gt_ids):
            raise ValueError(f"GT technique IDs mismatch for {sid!r}")
        expected_status = (
            "mapped" if row["category"] in ("mapped_single", "mapped_multi") else row["category"]
        )
        if canon_gt.get("label_status") != expected_status:
            raise ValueError(f"GT label_status/category mismatch for {sid!r}")

    for pid, pair in pair_by_id.items():
        if set(views_by_pair[pid]) != {"single", "contextual"}:
            raise ValueError(f"Pair {pid!r} must have exactly one single and one contextual view")
        for kind in ("single", "contextual"):
            embedded = pair.get(f"{kind}_view")
            if not isinstance(embedded, Mapping):
                raise ValueError(f"Pair {pid!r}: missing or invalid {kind}_view")
            expected_id = views_by_pair[pid][kind]
            if (
                embedded.get("view_id") != expected_id
                or embedded.get("pair_id") != pid
                or embedded.get("view_type") != kind
            ):
                raise ValueError(f"Pair {pid!r}: {kind}_view linkage mismatch")


def build_failure_analysis_summary(
    diagnostics_rows: Sequence[Mapping[str, Any]],
    canonical_metrics: Mapping[str, Any],
    provenance_hashes: Mapping[str, str],
    views_rows: Sequence[Mapping[str, Any]] | None = None,
    pairs_rows: Sequence[Mapping[str, Any]] | None = None,
    ground_truth_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Assemble complete, deterministic failure analysis summary."""
    sources = (views_rows, pairs_rows, ground_truth_rows)
    if any(source is not None for source in sources) and any(source is None for source in sources):
        raise ValueError("Canonical provenance requires views, pairs and ground_truth together")
    for row in diagnostics_rows:
        validate_diagnostic_ground_truth(row)
    if views_rows is not None and pairs_rows is not None and ground_truth_rows is not None:
        validate_canonical_input_consistency(
            diagnostics_rows, views_rows, pairs_rows, ground_truth_rows
        )

    per_technique = recompute_per_technique_metrics(diagnostics_rows)
    verify_canonical_metric_consistency(per_technique, canonical_metrics)

    overall_positive = recompute_overall_positive_metrics(diagnostics_rows)
    verify_overall_metric_consistency(overall_positive, canonical_metrics)

    single_vs_contextual = analyze_single_vs_contextual_pairs(diagnostics_rows)
    t1105 = analyze_t1105_hard_negatives(diagnostics_rows)
    t1136 = analyze_t1136_001_failure(diagnostics_rows)

    summary: dict[str, Any] = {
        "analysis_version": ANALYSIS_VERSION,
        "overall_positive": overall_positive,
        "per_technique": per_technique,
        "provenance": {
            "analysis_version": ANALYSIS_VERSION,
            **provenance_hashes,
        },
        "single_vs_contextual": single_vs_contextual,
        "t1105_hard_negatives": t1105,
        "t1136_001_failure": t1136,
    }
    return summary


def serialize_summary_deterministic(summary: Mapping[str, Any]) -> str:
    """Serialize summary to byte-deterministic JSON with sort_keys=True, indent=2,
    and trailing newline.
    """
    return json.dumps(summary, indent=2, sort_keys=True) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the failure analysis script."""
    parser = argparse.ArgumentParser(
        description="Deterministic retrieval failure analysis for RAG2ATTCK Task T20."
    )
    parser.add_argument(
        "--diagnostics",
        type=Path,
        default=Path(DEFAULT_DIAGNOSTICS_PATH),
        help=f"Path to retrieval diagnostics JSONL (default: {DEFAULT_DIAGNOSTICS_PATH})",
    )
    parser.add_argument(
        "--metrics",
        type=Path,
        default=Path(DEFAULT_METRICS_PATH),
        help=f"Path to canonical retrieval metrics JSON (default: {DEFAULT_METRICS_PATH})",
    )
    parser.add_argument(
        "--views",
        type=Path,
        default=Path(DEFAULT_VIEWS_PATH),
        help=f"Path to views JSONL (default: {DEFAULT_VIEWS_PATH})",
    )
    parser.add_argument(
        "--pairs",
        type=Path,
        default=Path(DEFAULT_PAIRS_PATH),
        help=f"Path to pairs JSONL (default: {DEFAULT_PAIRS_PATH})",
    )
    parser.add_argument(
        "--ground-truth",
        type=Path,
        default=Path(DEFAULT_GROUND_TRUTH_PATH),
        help=f"Path to ground truth JSONL (default: {DEFAULT_GROUND_TRUTH_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(DEFAULT_OUTPUT_PATH),
        help=f"Path to output analysis summary JSON (default: {DEFAULT_OUTPUT_PATH})",
    )
    parser.add_argument(
        "--sample",
        type=str,
        default=None,
        help="Inspect a specific sample_id post-hoc without full analysis execution.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="When inspecting a sample with --sample, output as JSON instead of plaintext.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary logging to stdout.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI execution entrypoint."""
    args = parse_args(argv)

    diagnostics_rows = load_jsonl(args.diagnostics)

    if args.sample:
        try:
            data = inspect_sample(diagnostics_rows, args.sample)
        except KeyError as err:
            print(f"Error: {err}", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(data, indent=2, sort_keys=True))
        else:
            print(format_sample_inspection(data))
        return 0

    canonical_metrics = load_json(args.metrics)

    views_rows = load_jsonl(args.views)
    pairs_rows = load_jsonl(args.pairs)
    ground_truth_rows = load_jsonl(args.ground_truth)

    provenance_hashes = {
        "diagnostics_sha256": compute_file_sha256(args.diagnostics),
        "ground_truth_sha256": compute_file_sha256(args.ground_truth),
        "metrics_sha256": compute_file_sha256(args.metrics),
        "pairs_sha256": compute_file_sha256(args.pairs),
        "views_sha256": compute_file_sha256(args.views),
    }

    summary = build_failure_analysis_summary(
        diagnostics_rows=diagnostics_rows,
        canonical_metrics=canonical_metrics,
        provenance_hashes=provenance_hashes,
        views_rows=views_rows,
        pairs_rows=pairs_rows,
        ground_truth_rows=ground_truth_rows,
    )

    serialized = serialize_summary_deterministic(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")

    if not args.quiet:
        svc = summary["single_vs_contextual"]
        pos = summary["overall_positive"]
        t1105 = summary["t1105_hard_negatives"]
        t1136 = summary["t1136_001_failure"]

        print("Deterministic retrieval failure analysis completed.")
        print(f"  Diagnostics: {args.diagnostics}")
        print(f"  Output:      {args.output}")
        print("  Key results:")
        print(f"    Positive samples:      {pos['evaluated_positive_samples']}")
        print(f"    Candidate pairs:       {svc['candidate_pairs']}")
        print(f"    Eligible pairs:        {svc['eligible_pairs']}")
        print(f"    Excluded pairs:        {svc['excluded_pairs']}")
        if svc["excluded_pairs"] > 0:
            for reason, count in svc["excluded_reasons"].items():
                print(f"      {reason}: {count}")
        sb = svc['single_better']
        print(f"    Single better:         {sb} "
              f"({svc['single_better_rate']:.1%})")
        print(f"    Contextual better:     {svc['contextual_better']} "
              f"({svc['contextual_better_rate']:.1%})")
        print(f"    Equal:                 {svc['equal']} ({svc['equal_rate']:.1%}) "
              f"[both absent Top-10: {svc['both_absent_top10']} "
              f"({svc['both_absent_top10_rate']:.1%}), "
              f"tied within Top-10: {svc['top10_equal']} ({svc['top10_equal_rate']:.1%})]")
        print(f"    Both absent Top-10:    {svc['both_absent_top10']} "
              f"({svc['both_absent_top10_rate']:.1%})")
        print(f"    T1105 views:           {t1105['evaluated_positive_views']}")
        print(f"    T1218.012 Top-1 count: {t1105['t1218_012_top1_count']} "
              f"({t1105['t1218_012_top1_rate']:.1%})")
        print(f"    T1136.001 absent:      {t1136['absent_top10_count']}/"
              f"{t1136['evaluated_positive_views']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
