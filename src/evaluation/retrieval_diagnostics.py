"""Retrieval-only diagnostics for the frozen RAG2ATTCK benchmark.

This module deliberately keeps evaluation labels outside the retriever.  The
retriever receives only ``endpoint_evidence``; labels are joined afterwards by
``sample_id``/``view_id`` for measurement.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from statistics import mean, median
from typing import Any, Iterable, Mapping, Sequence

from src.llm.schemas import validate_attack_id_syntax
from src.retrieval.retriever import FAISSRetriever, RetrievalResult, StubEmbedder


SUPPORTED_K = (1, 3, 5, 10)
_LABEL_STATUSES = {"mapped", "ambiguous", "unmapped"}
_SPLITS = {"TEST", "DEV"}


@dataclass(frozen=True)
class BenchmarkView:
    """The non-sensitive join of one model input and its evaluation metadata."""

    sample_id: str
    endpoint_evidence: str
    view_id: str
    pair_id: str
    split: str
    view_type: str
    label_status: str
    category: str
    ground_truth_technique_ids: tuple[str, ...]


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected an object")
            rows.append(value)
    return rows


def _require_unique(values: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Duplicate {label}: {value!r}")
        seen.add(value)


def _category(label_status: str, technique_ids: Sequence[str]) -> str:
    if label_status == "mapped":
        return "mapped_single" if len(technique_ids) == 1 else "mapped_multi"
    return label_status


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _validate_split_manifest(
    manifest: Mapping[str, Any],
    pair_by_id: Mapping[str, Mapping[str, Any]],
) -> None:
    """Require the manifest to be an exact TEST/DEV partition of canonical pairs."""

    declared: dict[str, str] = {}
    for manifest_key, expected_split in (("test", "TEST"), ("dev", "DEV")):
        ids = manifest.get(manifest_key)
        if not isinstance(ids, list) or any(not isinstance(pair_id, str) for pair_id in ids):
            raise ValueError(f"split manifest missing string list: {manifest_key}")
        _require_unique(ids, f"{expected_split} split pair_id")
        for pair_id in ids:
            if pair_id in declared:
                raise ValueError(f"pair_id appears in both TEST and DEV: {pair_id!r}")
            declared[pair_id] = expected_split

    canonical = set(pair_by_id)
    declared_ids = set(declared)
    missing = sorted(canonical - declared_ids)
    unknown = sorted(declared_ids - canonical)
    if missing or unknown:
        raise ValueError(f"split manifest is not an exact partition: missing={missing[:3]}, unknown={unknown[:3]}")

    disagreements = sorted(
        pair_id
        for pair_id, row in pair_by_id.items()
        if str(row.get("split", "")).upper() != declared[pair_id]
    )
    if disagreements:
        raise ValueError(f"split manifest disagrees with pair metadata: {disagreements[:3]}")


def load_benchmark_views(
    inference_path: Path | str,
    ground_truth_path: Path | str,
    views_path: Path | str,
    pairs_path: Path | str,
    split_manifest_path: Path | str | None = None,
    corpus_path: Path | str | None = None,
) -> list[BenchmarkView]:
    """Load and validate the authoritative benchmark join.

    The function validates the input contract before any retrieval occurs.
    ``ground_truth`` is never returned to the retriever; it is stored only in
    the result objects used by the diagnostic scorer.
    """

    inference_rows = _read_jsonl(Path(inference_path))
    ground_truth_rows = _read_jsonl(Path(ground_truth_path))
    view_rows = _read_jsonl(Path(views_path))
    pair_rows = _read_jsonl(Path(pairs_path))

    inference_by_id: dict[str, dict[str, Any]] = {}
    for row in inference_rows:
        sample_id = row.get("sample_id")
        evidence = row.get("endpoint_evidence")
        if not isinstance(sample_id, str) or not sample_id.strip():
            raise ValueError("inference input has missing or invalid sample_id")
        if not isinstance(evidence, str) or not evidence.strip():
            raise ValueError(f"missing endpoint_evidence for sample_id {sample_id!r}")
        if sample_id in inference_by_id:
            raise ValueError(f"Duplicate sample_id: {sample_id!r}")
        inference_by_id[sample_id] = row

    ground_truth_by_view: dict[str, dict[str, Any]] = {}
    for row in ground_truth_rows:
        view_id = row.get("view_id")
        technique_ids = row.get("technique_ids")
        label_status = row.get("label_status")
        if not isinstance(view_id, str) or not view_id.strip():
            raise ValueError("ground truth row has missing or invalid view_id")
        if view_id in ground_truth_by_view:
            raise ValueError(f"Duplicate ground-truth view_id: {view_id!r}")
        if not isinstance(technique_ids, list) or any(
            not isinstance(value, str) or not validate_attack_id_syntax(value)
            for value in technique_ids
        ):
            raise ValueError(f"malformed ATT&CK IDs for view_id {view_id!r}")
        if label_status not in _LABEL_STATUSES:
            raise ValueError(f"invalid label_status for view_id {view_id!r}: {label_status!r}")
        if label_status == "mapped" and not technique_ids:
            raise ValueError(f"mapped view has no ground-truth technique for {view_id!r}")
        if label_status != "mapped" and technique_ids:
            raise ValueError(f"non-mapped view has ground-truth techniques for {view_id!r}")
        ground_truth_by_view[view_id] = row

    views_by_id: dict[str, dict[str, Any]] = {}
    for row in view_rows:
        view_id = row.get("view_id")
        pair_id = row.get("pair_id")
        view_type = row.get("view_type")
        if not isinstance(view_id, str) or not isinstance(pair_id, str):
            raise ValueError("view row has invalid view_id/pair_id")
        if view_type not in {"single", "contextual"}:
            raise ValueError(f"invalid view_type for {view_id!r}: {view_type!r}")
        if view_id in views_by_id:
            raise ValueError(f"Duplicate view_id: {view_id!r}")
        views_by_id[view_id] = row

    pair_by_id: dict[str, dict[str, Any]] = {}
    for row in pair_rows:
        pair_id = row.get("pair_id")
        split = str(row.get("split", "")).upper()
        if not isinstance(pair_id, str) or split not in _SPLITS:
            raise ValueError(f"invalid pair_id/split: {pair_id!r}/{split!r}")
        if pair_id in pair_by_id:
            raise ValueError(f"Duplicate pair_id: {pair_id!r}")
        pair_by_id[pair_id] = row

    if split_manifest_path is not None:
        manifest = _read_json(Path(split_manifest_path))
        if not isinstance(manifest, Mapping):
            raise ValueError("split manifest must be an object")
        _validate_split_manifest(manifest, pair_by_id)

    _require_unique(inference_by_id, "sample_id")
    if set(inference_by_id) != set(ground_truth_by_view):
        missing_gt = sorted(set(inference_by_id) - set(ground_truth_by_view))
        missing_input = sorted(set(ground_truth_by_view) - set(inference_by_id))
        raise ValueError(f"benchmark join mismatch: missing_gt={missing_gt[:3]} missing_input={missing_input[:3]}")

    result: list[BenchmarkView] = []
    for sample_id, input_row in inference_by_id.items():
        view = views_by_id.get(sample_id)
        gt = ground_truth_by_view[sample_id]
        if view is None:
            raise ValueError(f"missing view reference for sample_id {sample_id!r}")
        pair = pair_by_id.get(view["pair_id"])
        if pair is None:
            raise ValueError(f"missing pair reference for view_id {sample_id!r}")
        split = str(pair.get("split", "")).upper()
        technique_ids = tuple(gt["technique_ids"])
        result.append(
            BenchmarkView(
                sample_id=sample_id,
                endpoint_evidence=input_row["endpoint_evidence"],
                view_id=sample_id,
                pair_id=view["pair_id"],
                split=split,
                view_type=view["view_type"],
                label_status=gt["label_status"],
                category=_category(gt["label_status"], technique_ids),
                ground_truth_technique_ids=technique_ids,
            )
        )

    if corpus_path is not None:
        corpus_ids = {
            json.loads(line)["technique_id"]
            for line in Path(corpus_path).read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        for view in result:
            unknown = set(view.ground_truth_technique_ids) - corpus_ids
            if unknown:
                raise ValueError(f"ground truth IDs absent from retrieval corpus for {view.sample_id}: {sorted(unknown)}")

    return result


def _candidate_dict(results: Sequence[RetrievalResult]) -> list[dict[str, Any]]:
    expected_ranks = list(range(1, len(results) + 1))
    actual_ranks = [result.rank for result in results]
    if actual_ranks != expected_ranks:
        raise ValueError(f"retrieval ranks must be contiguous from 1, got {actual_ranks!r}")
    return [
        {
            "rank": result.rank,
            "technique_id": result.technique_id,
            "score": round(float(result.score), 7),
        }
        for result in results
    ]


def technique_rank(record: Mapping[str, Any], technique_id: str) -> int | None:
    """Return the retrieved rank for one specific ground-truth technique."""

    ranks = record.get("ground_truth_technique_ranks")
    if isinstance(ranks, Mapping) and technique_id in ranks:
        rank = ranks[technique_id]
        return int(rank) if isinstance(rank, int) else None

    # Keep scoring robust for hand-built/legacy records used by callers.
    for candidate in record.get("retrieved_candidates", ()):
        if candidate.get("technique_id") == technique_id:
            rank = candidate.get("rank")
            return int(rank) if isinstance(rank, int) else None
    return None


def make_diagnostic_record(
    view: BenchmarkView,
    results: Sequence[RetrievalResult],
    provenance: Mapping[str, Any],
) -> dict[str, Any]:
    """Create one deterministic diagnostic record from retrieval results."""

    candidates = _candidate_dict(results)
    gt_ids = set(view.ground_truth_technique_ids)
    technique_ranks = {
        technique_id: next(
            (candidate["rank"] for candidate in candidates if candidate["technique_id"] == technique_id),
            None,
        )
        for technique_id in view.ground_truth_technique_ids
    }
    best_rank = min(
        (rank for rank in technique_ranks.values() if rank is not None),
        default=None,
    ) if gt_ids else None
    record: dict[str, Any] = {
        "sample_id": view.sample_id,
        "split": view.split,
        "pair_id": view.pair_id,
        "view_type": view.view_type,
        "label_status": view.label_status,
        "category": view.category,
        "ground_truth_technique_ids": list(view.ground_truth_technique_ids),
        "ground_truth_technique_ranks": technique_ranks,
        "retrieved_candidates": candidates,
        "ground_truth_best_rank": best_rank,
        "hit_at_1": (bool(best_rank is not None and best_rank <= 1) if gt_ids else None),
        "hit_at_3": (bool(best_rank is not None and best_rank <= 3) if gt_ids else None),
        "hit_at_5": (bool(best_rank is not None and best_rank <= 5) if gt_ids else None),
        "hit_at_10": (bool(best_rank is not None and best_rank <= 10) if gt_ids else None),
        "recall_at_1": (
            sum(rank is not None and rank <= 1 for rank in technique_ranks.values()) / len(gt_ids)
            if gt_ids else None
        ),
        "recall_at_3": (
            sum(rank is not None and rank <= 3 for rank in technique_ranks.values()) / len(gt_ids)
            if gt_ids else None
        ),
        "recall_at_5": (
            sum(rank is not None and rank <= 5 for rank in technique_ranks.values()) / len(gt_ids)
            if gt_ids else None
        ),
        "recall_at_10": (
            sum(rank is not None and rank <= 10 for rank in technique_ranks.values()) / len(gt_ids)
            if gt_ids else None
        ),
        "corpus_sha256": provenance.get("corpus_sha256"),
        "index_sha256": provenance.get("index_sha256"),
        "embedding_model_id": provenance.get("embedding_model_id"),
        "embedding_model_revision": provenance.get("embedding_model_revision"),
    }
    # Keep key order explicit so JSONL is stable and easy to diff.
    return record


def _metric_rows(
    rows: Sequence[Mapping[str, Any]],
    *,
    technique_id: str | None = None,
) -> dict[str, Any]:
    positive = [row for row in rows if row["ground_truth_technique_ids"]]
    metrics: dict[str, Any] = {
        "total_samples": len(rows),
        "evaluated_positive_samples": len(positive),
        "non_positive_samples": len(rows) - len(positive),
    }
    for k in SUPPORTED_K:
        if technique_id is None:
            hits = [bool(row[f"hit_at_{k}"]) for row in positive]
            recalls = [float(row[f"recall_at_{k}"]) for row in positive]
        else:
            ranks_for_technique = [technique_rank(row, technique_id) for row in positive]
            hits = [rank is not None and rank <= k for rank in ranks_for_technique]
            recalls = [float(hit) for hit in hits]
        hit_rate = (sum(hits) / len(hits)) if hits else None
        macro_recall = (sum(recalls) / len(recalls)) if recalls else None
        metrics[f"hit_rate_at_{k}"] = hit_rate
        metrics[f"macro_recall_at_{k}"] = macro_recall
        # Compatibility key: it now has true multi-label recall semantics.
        metrics[f"recall_at_{k}"] = macro_recall
    if technique_id is None:
        ranks = [row["ground_truth_best_rank"] for row in positive if row["ground_truth_best_rank"] is not None]
    else:
        ranks = [technique_rank(row, technique_id) for row in positive]
        ranks = [rank for rank in ranks if rank is not None]
    metrics["mean_ground_truth_rank_when_retrieved"] = mean(ranks) if ranks else None
    metrics["median_ground_truth_rank_when_retrieved"] = median(ranks) if ranks else None
    absence_ranks = [
        row["ground_truth_best_rank"] if technique_id is None else technique_rank(row, technique_id)
        for row in positive
    ]
    metrics["gt_absent_from_top10_count"] = sum(rank is None or rank > 10 for rank in absence_ranks)
    metrics["gt_absent_from_top10_rate"] = (
        metrics["gt_absent_from_top10_count"] / len(positive) if positive else None
    )
    return metrics


def calculate_metrics(records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Calculate positive Recall@k and separate negative diagnostics."""

    def grouped(key_fn: Any) -> dict[str, Any]:
        groups: defaultdict[str, list[Mapping[str, Any]]] = defaultdict(list)
        for record in records:
            groups[str(key_fn(record))].append(record)
        return {key: _metric_rows(groups[key]) for key in sorted(groups)}

    positive = [record for record in records if record["ground_truth_technique_ids"]]
    negatives = [record for record in records if not record["ground_truth_technique_ids"]]
    per_technique: dict[str, Any] = {}
    techniques = sorted({tid for record in positive for tid in record["ground_truth_technique_ids"]})
    for technique_id in techniques:
        per_technique[technique_id] = _metric_rows(
            [record for record in positive if technique_id in record["ground_truth_technique_ids"]],
            technique_id=technique_id,
        )

    return {
        "sample_count": len(records),
        "positive_sample_count": len(positive),
        "negative_sample_count": len(negatives),
        "overall_positive": _metric_rows(positive),
        "by_split": grouped(lambda row: row["split"]),
        "by_view_type": grouped(lambda row: row["view_type"]),
        "by_category": grouped(lambda row: row["category"]),
        "category_counts": dict(sorted(Counter(record["category"] for record in records).items())),
        "per_technique": per_technique,
        "negative_diagnostics": {
            "samples": len(negatives),
            "negative_samples_with_candidates": sum(bool(row["retrieved_candidates"]) for row in negatives),
            "no_positive_ground_truth_for_recall": True,
        },
    }


def run_diagnostics(
    views: Sequence[BenchmarkView],
    retriever: FAISSRetriever,
    output_jsonl: Path | str,
    metrics_path: Path | str,
) -> dict[str, Any]:
    """Run retrieval-only diagnostics and write deterministic artifacts."""

    provenance = dict(getattr(retriever, "config", {}) or {})
    records: list[dict[str, Any]] = []
    for view in views:
        # This is the only value passed to retrieve.  Do not add labels or IDs.
        results = retriever.retrieve(query=view.endpoint_evidence, k=max(SUPPORTED_K))
        records.append(make_diagnostic_record(view, results, provenance))

    output_path = Path(output_jsonl)
    metrics_output = Path(metrics_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
    metrics = calculate_metrics(records)
    metrics["provenance"] = {
        key: provenance.get(key)
        for key in (
            "corpus_sha256",
            "index_sha256",
            "document_mapping_sha256",
            "embedding_model_id",
            "embedding_model_revision",
            "embedding_dimension",
            "faiss_index_type",
            "normalization",
            "similarity_metric",
        )
    }
    metrics["diagnostic_jsonl_sha256"] = _hash_file(output_path)
    metrics_output.write_text(
        json.dumps(metrics, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return metrics


def _default_paths(root: Path) -> dict[str, Path]:
    base = root / "data" / "ground_truth" / "synthetic"
    return {
        "inference": base / "inference.jsonl",
        "ground_truth": base / "ground_truth.jsonl",
        "views": base / "views.jsonl",
        "pairs": base / "pairs.jsonl",
        "split_manifest": base / "split_manifest.json",
        "corpus": root / "attack" / "corpus" / "enterprise-windows-v19.2.jsonl",
        "config": root / "config" / "retrieval.json",
        "output": root / "artifacts" / "retrieval" / "retrieval_diagnostics.jsonl",
        "metrics": root / "artifacts" / "retrieval" / "retrieval_metrics.json",
    }


def main(argv: Sequence[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    defaults = _default_paths(root)
    parser = argparse.ArgumentParser(description="Run retrieval-only RAG2ATTCK diagnostics")
    parser.add_argument("--inference", type=Path, default=defaults["inference"])
    parser.add_argument("--ground-truth", type=Path, default=defaults["ground_truth"])
    parser.add_argument("--views", type=Path, default=defaults["views"])
    parser.add_argument("--pairs", type=Path, default=defaults["pairs"])
    parser.add_argument("--split-manifest", type=Path, default=defaults["split_manifest"])
    parser.add_argument("--corpus", type=Path, default=defaults["corpus"])
    parser.add_argument("--config", type=Path, default=defaults["config"])
    parser.add_argument("--output", type=Path, default=defaults["output"])
    parser.add_argument("--metrics", type=Path, default=defaults["metrics"])
    parser.add_argument(
        "--stub-embedder",
        action="store_true",
        help="Use the deterministic offline embedder; intended for tests, not research results.",
    )
    args = parser.parse_args(argv)

    views = load_benchmark_views(
        args.inference,
        args.ground_truth,
        args.views,
        args.pairs,
        args.split_manifest,
        args.corpus,
    )
    embedder = StubEmbedder() if args.stub_embedder else None
    retriever = FAISSRetriever.from_saved(config_path=args.config, embedder=embedder)
    metrics = run_diagnostics(views, retriever, args.output, args.metrics)
    print(json.dumps(metrics["overall_positive"], sort_keys=True))
    print(f"Wrote {len(views)} diagnostic records to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
