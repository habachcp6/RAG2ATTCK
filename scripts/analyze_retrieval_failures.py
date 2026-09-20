"""Deterministic retrieval failure analysis for RAG2ATTCK Task T20.

Analyzes stored scientific artifacts without rerunning retrieval:
- Recomputes per-technique metrics and cross-checks against retrieval_metrics.json.
- Analyzes Single vs Contextual pair rankings (comparison_rank = rank if rank is not None else 11).
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

ANALYSIS_VERSION = "1.0.0"
SUPPORTED_K = (1, 3, 5, 10)
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


def resolve_comparison_rank(rank: int | None, default_absent: int = 11) -> int:
    """Defined absent rank rule: comparison_rank = rank if rank is not None else 11."""
    return rank if rank is not None else default_absent


def _get_technique_rank(record: Mapping[str, Any], technique_id: str) -> int | None:
    """Extract rank for a specific technique from record ground-truth ranks or candidates."""
    ranks = record.get("ground_truth_technique_ranks")
    if isinstance(ranks, Mapping) and technique_id in ranks:
        val = ranks[technique_id]
        return int(val) if isinstance(val, int) else None
    for cand in record.get("retrieved_candidates", ()):
        if cand.get("technique_id") == technique_id:
            val = cand.get("rank")
            return int(val) if isinstance(val, int) else None
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
        retrieved_ranks = [r for r in ranks if r is not None]

        hit_1 = sum(1 for r in ranks if r is not None and r <= 1)
        hit_3 = sum(1 for r in ranks if r is not None and r <= 3)
        hit_5 = sum(1 for r in ranks if r is not None and r <= 5)
        hit_10 = sum(1 for r in ranks if r is not None and r <= 10)

        absent_count = sum(1 for r in ranks if r is None or r > 10)
        absent_rate = absent_count / n_pos if n_pos > 0 else None

        med_rank = median(retrieved_ranks) if retrieved_ranks else None
        mean_rank = mean(retrieved_ranks) if retrieved_ranks else None

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
            "macro_recall_at_10": None,
            "mean_ground_truth_rank_when_retrieved": None,
            "median_ground_truth_rank_when_retrieved": None,
        }

    best_ranks = [r.get("ground_truth_best_rank") for r in positive_rows]
    retrieved_ranks = [r for r in best_ranks if r is not None]

    hit_1 = sum(1 for r in best_ranks if r is not None and r <= 1)
    hit_3 = sum(1 for r in best_ranks if r is not None and r <= 3)
    hit_5 = sum(1 for r in best_ranks if r is not None and r <= 5)
    hit_10 = sum(1 for r in best_ranks if r is not None and r <= 10)

    absent_count = sum(1 for r in best_ranks if r is None or r > 10)
    absent_rate = absent_count / n_pos

    # Calculate macro recall@10
    recalls_10: list[float] = []
    for r in positive_rows:
        gt_ids = r.get("ground_truth_technique_ids", [])
        if not gt_ids:
            continue
        ranks_dict = r.get("ground_truth_technique_ranks", {})
        hits = sum(1 for tid in gt_ids if ranks_dict.get(tid) is not None and ranks_dict[tid] <= 10)
        recalls_10.append(hits / len(gt_ids))
    macro_recall_10 = mean(recalls_10) if recalls_10 else None

    return {
        "evaluated_positive_samples": n_pos,
        "gt_absent_from_top10_count": absent_count,
        "gt_absent_from_top10_rate": absent_rate,
        "hit_rate_at_1": hit_1 / n_pos,
        "hit_rate_at_3": hit_3 / n_pos,
        "hit_rate_at_5": hit_5 / n_pos,
        "hit_rate_at_10": hit_10 / n_pos,
        "macro_recall_at_10": macro_recall_10,
        "mean_ground_truth_rank_when_retrieved": mean(retrieved_ranks) if retrieved_ranks else None,
        "median_ground_truth_rank_when_retrieved": median(retrieved_ranks) if retrieved_ranks else None,
    }


def verify_canonical_metric_consistency(
    recomputed_per_technique: Mapping[str, Mapping[str, Any]],
    canonical_metrics: Mapping[str, Any],
    tolerance: float = 1e-9,
) -> None:
    """Verify consistency between recomputed metrics and canonical retrieval_metrics.json.

    Fails closed (raises ValueError) if counts differ or rates exceed float tolerance.
    """
    canon_per_tech = canonical_metrics.get("per_technique", {})
    if not isinstance(canon_per_tech, Mapping):
        raise TypeError("Canonical metrics missing 'per_technique' mapping")

    missing_techs = sorted(set(recomputed_per_technique) - set(canon_per_tech))
    if missing_techs:
        raise ValueError(f"Techniques missing from canonical metrics: {missing_techs}")

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
                    f"Technique {tid} metric mismatch on {field}: recomputed={r_val} != canonical={c_val}"
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
                        f"Technique {tid} rate mismatch on {field}: recomputed={r_val} != canonical={c_val}"
                    )
            elif abs(float(r_val) - float(c_val)) > tolerance:
                raise ValueError(
                    f"Technique {tid} rate mismatch on {field}: recomputed={r_val} != canonical={c_val}"
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


def analyze_single_vs_contextual_pairs(
    diagnostics_rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Perform pairwise ranking comparison across comparable positive scenario pairs.

    Semantics:
    - Target pairs: N=296 pairs where single view category in ('mapped_single', 'mapped_multi').
    - comparison_rank = rank if rank is not None else 11.
    - Single better: single_rank < contextual_rank
    - Contextual better: contextual_rank < single_rank
    - Equal: single_rank == contextual_rank
    - Both absent Top-10: single_rank > 10 and contextual_rank > 10 (i.e. both rank is None)
    """
    pairs_map: dict[str, dict[str, Mapping[str, Any]]] = defaultdict(dict)
    for row in diagnostics_rows:
        pair_id = row.get("pair_id")
        view_type = row.get("view_type")
        if pair_id and view_type:
            pairs_map[pair_id][view_type] = row

    comparable_pair_ids = sorted(
        pid
        for pid, views in pairs_map.items()
        if "single" in views
        and "contextual" in views
        and views["single"].get("category") in ("mapped_single", "mapped_multi")
    )

    n_pairs = len(comparable_pair_ids)
    single_better = 0
    contextual_better = 0
    equal = 0
    both_absent_top10 = 0

    for pid in comparable_pair_ids:
        s_view = pairs_map[pid]["single"]
        c_view = pairs_map[pid]["contextual"]

        s_rank = s_view.get("ground_truth_best_rank")
        c_rank = c_view.get("ground_truth_best_rank")

        s_comp = resolve_comparison_rank(s_rank)
        c_comp = resolve_comparison_rank(c_rank)

        if s_comp < c_comp:
            single_better += 1
        elif c_comp < s_comp:
            contextual_better += 1
        else:
            equal += 1

        if s_comp > 10 and c_comp > 10:
            both_absent_top10 += 1

    top10_equal = equal - both_absent_top10

    return {
        "both_absent": both_absent_top10,
        "both_absent_rate": both_absent_top10 / n_pairs if n_pairs else 0.0,
        "both_absent_top10": both_absent_top10,
        "both_absent_top10_rate": both_absent_top10 / n_pairs if n_pairs else 0.0,
        "comparable_pairs": n_pairs,
        "comparison_rule": "comparison_rank = rank if rank is not None else 11",
        "contextual_better": contextual_better,
        "contextual_better_rate": contextual_better / n_pairs if n_pairs else 0.0,
        "equal": equal,
        "equal_rate": equal / n_pairs if n_pairs else 0.0,
        "single_better": single_better,
        "single_better_rate": single_better / n_pairs if n_pairs else 0.0,
        "top10_equal": top10_equal,
        "top10_equal_rate": top10_equal / n_pairs if n_pairs else 0.0,
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
    """Analyze retrieval performance for T1136.001 positive views."""
    t1136_views = [
        r
        for r in diagnostics_rows
        if "T1136.001" in r.get("ground_truth_technique_ids", ())
    ]
    n_views = len(t1136_views)

    ranks = [_get_technique_rank(r, "T1136.001") for r in t1136_views]
    hit_10_count = sum(1 for r in ranks if r is not None and r <= 10)
    absent_count = sum(1 for r in ranks if r is None or r > 10)

    return {
        "absent_top10_count": absent_count,
        "absent_top10_rate": absent_count / n_views if n_views else 0.0,
        "evaluated_positive_views": n_views,
        "median_ground_truth_rank_when_retrieved": None,
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
        f"Hits: Hit@1={data.get('hit_at_1')}, Hit@3={data.get('hit_at_3')}, Hit@5={data.get('hit_at_5')}, Hit@10={data.get('hit_at_10')}",
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


def build_failure_analysis_summary(
    diagnostics_rows: Sequence[Mapping[str, Any]],
    canonical_metrics: Mapping[str, Any],
    provenance_hashes: Mapping[str, str],
) -> dict[str, Any]:
    """Assemble complete, deterministic failure analysis summary."""
    per_technique = recompute_per_technique_metrics(diagnostics_rows)
    verify_canonical_metric_consistency(per_technique, canonical_metrics)

    overall_positive = recompute_overall_positive_metrics(diagnostics_rows)
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
    """Serialize summary to byte-deterministic JSON with sort_keys=True, indent=2, and trailing newline."""
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
    )

    serialized = serialize_summary_deterministic(summary)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(serialized, encoding="utf-8", newline="\n")

    if not args.quiet:
        print("Deterministic retrieval failure analysis completed.")
        print(f"  Diagnostics: {args.diagnostics}")
        print(f"  Output:      {args.output}")
        print("  Key results:")
        print(f"    Positive samples:      {summary['overall_positive']['evaluated_positive_samples']}")
        print(f"    Comparable pairs:      {summary['single_vs_contextual']['comparable_pairs']}")
        print(f"    Single better:         {summary['single_vs_contextual']['single_better']} ({summary['single_vs_contextual']['single_better_rate']:.1%})")
        print(f"    Contextual better:     {summary['single_vs_contextual']['contextual_better']} ({summary['single_vs_contextual']['contextual_better_rate']:.1%})")
        print(f"    Equal:                 {summary['single_vs_contextual']['equal']} ({summary['single_vs_contextual']['equal_rate']:.1%}) [both absent Top-10: {summary['single_vs_contextual']['both_absent_top10']} ({summary['single_vs_contextual']['both_absent_top10_rate']:.1%}), tied within Top-10: {summary['single_vs_contextual']['top10_equal']} ({summary['single_vs_contextual']['top10_equal_rate']:.1%})]")
        print(f"    Both absent Top-10:    {summary['single_vs_contextual']['both_absent_top10']} ({summary['single_vs_contextual']['both_absent_top10_rate']:.1%})")
        print(f"    T1105 views:           {summary['t1105_hard_negatives']['evaluated_positive_views']}")
        print(f"    T1218.012 Top-1 count: {summary['t1105_hard_negatives']['t1218_012_top1_count']} ({summary['t1105_hard_negatives']['t1218_012_top1_rate']:.1%})")
        print(f"    T1136.001 absent:      {summary['t1136_001_failure']['absent_top10_count']}/{summary['t1136_001_failure']['evaluated_positive_views']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
