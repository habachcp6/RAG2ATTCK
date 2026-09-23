"""Independently recompute frozen T20 headline values from captured JSONL rows."""

import json
import math
from collections import defaultdict
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIAGNOSTICS = ROOT / "artifacts/retrieval/retrieval_diagnostics.jsonl"
METRICS = ROOT / "artifacts/retrieval/retrieval_metrics.json"
ANALYSIS = ROOT / "artifacts/analysis/t20_retrieval_failure_summary.json"
GT = ROOT / "data/ground_truth/synthetic/ground_truth.jsonl"
VIEWS = ROOT / "data/ground_truth/synthetic/views.jsonl"
EXPECTED_HASHES = {
    DIAGNOSTICS: "a78377b66db09f23088fc4da73570b06d69c2413a67ad5c789e9808953c24777",
    METRICS: "3e40e18f0d8c430b2f27aa4415f7b2df4b0f45289576be21f34c36dc8d3683be",
    ANALYSIS: "08ff242728a565d3b52e1c74b48a3f178e92cf1a3d762208bb7c690ace73f68b",
    GT: "8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608",
    VIEWS: "1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d",
}
DEPTHS = (1, 3, 5, 10)


def jsonl_by_key(path: Path, key: str) -> dict[str, dict]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        value = row[key]
        if value in result:
            raise ValueError(f"duplicate {key}={value} in {path}")
        result[value] = row
    return result


def check(actual, expected, description: str) -> None:
    if isinstance(expected, float):
        valid = math.isclose(actual, expected, rel_tol=0, abs_tol=1e-15)
    else:
        valid = actual == expected
    if not valid:
        raise ValueError(f"{description}: expected {expected!r}, got {actual!r}")


def main() -> None:
    for path, expected in EXPECTED_HASHES.items():
        check(sha256(path.read_bytes()).hexdigest(), expected, str(path))
    gt = jsonl_by_key(GT, "view_id")
    views = jsonl_by_key(VIEWS, "view_id")
    diagnostics = jsonl_by_key(DIAGNOSTICS, "sample_id")
    check(len(diagnostics), 1340, "diagnostic row count")
    check(set(diagnostics), set(gt), "diagnostic/GT sample IDs")
    check(set(diagnostics), set(views), "diagnostic/view sample IDs")

    hits = {depth: 0 for depth in DEPTHS}
    positive = 0
    t1136_positive = 0
    t1136_ranks = []
    by_pair = defaultdict(dict)
    for sample_id, row in diagnostics.items():
        truth = tuple(gt[sample_id]["technique_ids"])
        check(tuple(row["ground_truth_technique_ids"]), truth, f"{sample_id} GT")
        check(row["label_status"], gt[sample_id]["label_status"], f"{sample_id} label")
        check(row["pair_id"], views[sample_id]["pair_id"], f"{sample_id} pair")
        check(row["view_type"], views[sample_id]["view_type"], f"{sample_id} type")
        candidates = row["retrieved_candidates"]
        check([c["rank"] for c in candidates], list(range(1, 11)), f"{sample_id} ranks")
        candidate_ids = [c["technique_id"] for c in candidates]
        check(len(candidate_ids), len(set(candidate_ids)), f"{sample_id} unique candidates")
        recomputed_ranks = {
            technique: candidate_ids.index(technique) + 1 if technique in candidate_ids else None
            for technique in truth
        }
        check(row["ground_truth_technique_ranks"], recomputed_ranks, f"{sample_id} GT ranks")
        if truth:
            positive += 1
            for depth in DEPTHS:
                hits[depth] += any(
                    rank is not None and rank <= depth for rank in recomputed_ranks.values()
                )
            if "T1136.001" in truth:
                t1136_positive += 1
                if recomputed_ranks["T1136.001"] is not None:
                    t1136_ranks.append(recomputed_ranks["T1136.001"])
        pair = by_pair[row["pair_id"]]
        if row["view_type"] in pair:
            raise ValueError(f"duplicate pair view: {row['pair_id']}/{row['view_type']}")
        pair[row["view_type"]] = (truth, recomputed_ranks)

    check(positive, 756, "positive views")
    check(hits, {1: 32, 3: 127, 5: 183, 10: 341}, "Hit@k numerators")
    check((t1136_positive, len(t1136_ranks)), (99, 0), "T1136.001 counts")
    check(len(by_pair), 670, "candidate pairs")
    comparison = defaultdict(int)
    for pair_id, pair in by_pair.items():
        check(set(pair), {"single", "contextual"}, f"{pair_id} view types")
        single_truth, single_ranks = pair["single"]
        contextual_truth, contextual_ranks = pair["contextual"]
        if len(single_truth) != 1:
            comparison["excluded"] += 1
            continue
        anchor = single_truth[0]
        if anchor not in contextual_truth:
            raise ValueError(f"{pair_id}: missing contextual anchor")
        single_rank = single_ranks[anchor]
        contextual_rank = contextual_ranks[anchor]
        left = single_rank if single_rank is not None else 11
        right = contextual_rank if contextual_rank is not None else 11
        comparison["eligible"] += 1
        comparison["single_better" if left < right else
                   "contextual_better" if right < left else "equal"] += 1
        if left == right == 11:
            comparison["both_absent_top10"] += 1
        if left == right and left <= 10:
            comparison["top10_equal"] += 1
    expected_comparison = {
        "excluded": 374,
        "eligible": 296,
        "single_better": 65,
        "contextual_better": 23,
        "equal": 208,
        "both_absent_top10": 147,
        "top10_equal": 61,
    }
    check(dict(comparison), expected_comparison, "pairwise anchor counts")

    metrics = json.loads(METRICS.read_text(encoding="utf-8"))
    analysis = json.loads(ANALYSIS.read_text(encoding="utf-8"))
    for depth in DEPTHS:
        rate = hits[depth] / positive
        check(metrics["overall_positive"][f"hit_rate_at_{depth}"], rate, f"metrics Hit@{depth}")
        check(analysis["overall_positive"][f"hit_rate_at_{depth}"], rate, f"analysis Hit@{depth}")
    check(metrics["per_technique"]["T1136.001"]["evaluated_positive_samples"],
          99, "metrics T1136.001 positives")
    check(metrics["per_technique"]["T1136.001"]["hit_rate_at_10"],
          0.0, "metrics T1136.001 Hit@10")
    check(metrics["per_technique"]["T1136.001"]["gt_absent_from_top10_count"],
          t1136_positive - len(t1136_ranks), "metrics T1136.001 absent")
    check(metrics["per_technique"]["T1136.001"]["median_ground_truth_rank_when_retrieved"],
          None, "metrics T1136.001 median")
    failure = analysis["t1136_001_failure"]
    for key, value in {
        "evaluated_positive_views": t1136_positive,
        "top10_hit_count": len(t1136_ranks),
        "top10_hit_rate": len(t1136_ranks) / t1136_positive,
        "absent_top10_count": t1136_positive - len(t1136_ranks),
        "absent_top10_rate": 1 - len(t1136_ranks) / t1136_positive,
        "median_ground_truth_rank_when_retrieved": None,
    }.items():
        check(failure[key], value, f"analysis T1136.001 {key}")
    pairwise = analysis["single_vs_contextual"]
    for key, value in expected_comparison.items():
        check(pairwise["excluded_pairs" if key == "excluded" else
                       "eligible_pairs" if key == "eligible" else key],
              value, f"analysis {key}")
    check(pairwise["candidate_pairs"], 670, "analysis candidate pairs")
    print(json.dumps({
        "positive_views": positive,
        "hit_rate_at": {str(depth): hits[depth] / positive for depth in DEPTHS},
        "pairwise": dict(comparison),
        "t1136_001": {"positive_views": t1136_positive, "top10_hits": len(t1136_ranks)},
        "status": "PASS",
    }, sort_keys=True))


if __name__ == "__main__":
    main()
