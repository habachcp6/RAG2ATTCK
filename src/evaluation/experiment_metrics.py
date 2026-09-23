"""Offline, pre-freeze evaluation infrastructure; canonical scoring stays closed.

The v1 mapping adapter intentionally does not import the experiment runner. It
reads hash-checked bytes once, joins GT only here, and never creates predictions.
No configuration flag constitutes approval of unresolved scientific policy.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from src.llm.schemas import ParseStatus, TechniquePrediction, validate_attack_id_syntax

CONDITIONS = ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
DEPTHS = (1, 3, 5, 10)
UNRESOLVED_POLICIES = (
    "single-ID scoring against multi-label and empty ground truth",
    "macro class universe, accuracy/failure denominators and zero denominators",
    "retired ATT&CK IDs and invalid-ID-rate denominator",
    "conditional any/all-GT presence and failure category precedence",
)
_ARTIFACTS = frozenset(
    {
        "inference",
        "ground_truth",
        "dataset_manifest",
        "views",
        "pairs",
        "split_manifest",
        "prompt",
        "model_config",
        "retrieval_config",
        "corpus",
        "index",
        "document_mapping",
        "retrieval_manifest",
        "attack_registry",
        "experiment_config",
    }
)
_RECORD_FIELDS = frozenset(
    [
        "schema_version",
        "execution_mode",
        "experiment_id",
        "run_id",
        "manifest_sha256",
        "sample_id",
        "pair_id",
        "view_type",
        "condition",
        "retrieval_k",
        "provider",
        "model",
        "model_version",
        "prompt_sha256",
        "model_config_sha256",
        "output_schema_sha256",
        "dataset_sha256",
        "ground_truth_sha256",
        "ground_truth_version",
        "attack_release",
        "corpus_sha256",
        "index_sha256",
        "retrieved_candidates",
        "raw_response",
        "raw_response_logged",
        "parsed_technique_ids",
        "parse_status",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "latency_ms",
        "retry_count",
        "request_attempt_count",
        "error_type",
        "error_message",
        "success",
        "timestamp",
        "terminal",
    ]
)


class HumanDecisionRequired(RuntimeError):
    """A scientific policy must be approved before canonical scoring exists."""


def evaluate_end_to_end(*args: Any, **kwargs: Any) -> None:
    """Hard gate: even a caller-supplied 'approved' policy cannot enable scoring."""
    raise HumanDecisionRequired("HUMAN_DECISION_REQUIRED: " + "; ".join(UNRESOLVED_POLICIES))


def evaluate_conditional_accuracy(*args: Any, **kwargs: Any) -> None:
    """No canonical conditional accuracy or precedence is silently inferred."""
    raise HumanDecisionRequired("HUMAN_DECISION_REQUIRED: " + "; ".join(UNRESOLVED_POLICIES))


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _reject_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON value: {value}")


def _object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _json(data: bytes) -> Any:
    return json.loads(data, object_pairs_hook=_object, parse_constant=_reject_constant)


def _jsonl(data: bytes) -> list[dict[str, Any]]:
    if not data or not data.endswith(b"\n"):
        raise ValueError("JSONL must be nonempty and end with a complete newline")
    if any(not line.strip() for line in data.splitlines()):
        raise ValueError("blank JSONL row")
    rows = [_json(line) for line in data.splitlines()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError("JSONL rows must be objects")
    return rows


def _unique(rows: Sequence[Mapping[str, Any]], key: str) -> dict[str, Mapping[str, Any]]:
    result = {}
    for row in rows:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"missing {key}")
        if value in result:
            raise ValueError(f"duplicate {key}: {value}")
        result[value] = row
    return result


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _hash(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _integer(value: Any, *, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


@dataclass(frozen=True)
class EvaluationInputs:
    """Evaluation-only join; never pass these rows to an inference pipeline."""

    manifest_sha256: str
    experiment_id: str
    execution_mode: str
    sample_ids: tuple[str, ...]
    records: tuple[dict[str, Any], ...]
    ground_truth: Mapping[str, tuple[str, ...]]
    registry: Mapping[str, Mapping[str, bool]]


def load_evaluation_inputs(
    manifest_path: Path | str,
    prediction_paths: Mapping[str, Path | str],
    *,
    repository_root: Path | str,
) -> EvaluationInputs:
    """Validate the complete TEST1280 x five-condition matrix, without scoring."""
    return _load_evaluation_inputs(
        manifest_path,
        prediction_paths,
        repository_root=repository_root,
        expected_sample_count=1280,
        verify_journal=True,
    )


def _load_evaluation_inputs(
    manifest_path: Path | str,
    prediction_paths: Mapping[str, Path | str],
    *,
    repository_root: Path | str,
    expected_sample_count: int,
    verify_journal: bool = True,
) -> EvaluationInputs:
    """Private fixture seam cannot enable scoring or certify a producer run."""
    root = Path(repository_root).resolve()
    manifest = _json(Path(manifest_path).read_bytes())
    _require(isinstance(manifest, dict), "manifest must be an object")
    _require(manifest.get("schema_version") == "1.0.0", "unsupported manifest version")
    _require(manifest.get("status") == "pre_freeze", "unsupported freeze status")
    _require(
        manifest.get("execution_mode") == "mock_fixture",
        "only mock_fixture records are supported before freeze",
    )
    _require(manifest.get("split") == "test", "only complete TEST cohort is supported")
    _require(
        manifest.get("conditions") == list(CONDITIONS),
        "condition matrix must be the exact five conditions",
    )
    _require(manifest.get("attack_release") == "19.2", "ATT&CK release must remain 19.2")
    _require(_hash(manifest.get("config_sha256")), "invalid config SHA-256")
    _require(
        isinstance(manifest.get("git_commit_sha"), str)
        and re.fullmatch(r"[0-9a-f]{40}", manifest["git_commit_sha"]) is not None,
        "invalid Git commit SHA",
    )
    _require(
        isinstance(manifest.get("experiment_id"), str) and bool(manifest["experiment_id"].strip()),
        "missing experiment_id",
    )
    schema_sha = hashlib.sha256(
        canonical_json_bytes(TechniquePrediction.model_json_schema())
    ).hexdigest()
    _require(manifest.get("output_schema_sha256") == schema_sha, "single-ID output schema mismatch")
    artifacts = manifest.get("artifacts")
    _require(
        isinstance(artifacts, dict) and _ARTIFACTS <= set(artifacts),
        "missing required artifact binding",
    )
    captured: dict[str, bytes] = {}
    for name, spec in artifacts.items():
        _require(
            isinstance(spec, dict) and set(spec) == {"path", "sha256"},
            f"invalid artifact binding: {name}",
        )
        _require(
            isinstance(spec["path"], str) and bool(spec["path"]), f"invalid artifact path: {name}"
        )
        _require(_hash(spec["sha256"]), f"invalid artifact hash: {name}")
        path = Path(spec["path"])
        if not path.is_absolute():
            path = root / path
        path = path.resolve()
        _require(path.is_relative_to(root), f"artifact path escapes repository root: {name}")
        data = path.read_bytes()
        _require(
            hashlib.sha256(data).hexdigest() == spec["sha256"], f"artifact hash mismatch: {name}"
        )
        captured[name] = data  # Parse these exact bytes, never reopen after hashing.

    _require(
        manifest["config_sha256"] == artifacts["experiment_config"]["sha256"],
        "experiment config hash mismatch",
    )
    experiment_config = _json(captured["experiment_config"])
    _require(isinstance(experiment_config, dict), "experiment config must be an object")
    execution = experiment_config.get("execution")
    _require(
        isinstance(execution, dict) and manifest.get("execution") == execution,
        "execution configuration mismatch",
    )
    _require(_integer(execution.get("retries")), "invalid bound retry policy")
    if not verify_journal:
        _require(
            expected_sample_count == 8
            and experiment_config.get("purpose") == "known_answer_fixture_only"
            and manifest.get("experiment_id") == "known-answer-only"
            and manifest.get("benchmark_version") == "fixture-only",
            "journal bypass is limited to the known-answer fixture",
        )

    dataset = _json(captured["dataset_manifest"])
    _require(
        dataset.get("benchmark_version") == manifest.get("benchmark_version"),
        "benchmark version mismatch",
    )
    _require(dataset.get("attack_version") == "19.2", "dataset ATT&CK release mismatch")
    _require(dataset.get("state") == "frozen", "dataset must remain frozen")
    for name in ("inference", "ground_truth", "views", "pairs", "split_manifest"):
        _require(
            dataset.get("files", {}).get(
                f"{name}.jsonl" if name != "split_manifest" else "split_manifest.json"
            )
            == artifacts[name]["sha256"],
            f"dataset manifest hash mismatch: {name}",
        )
    _require(
        dataset.get("attack_source_sha256") == artifacts["attack_registry"]["sha256"],
        "ATT&CK registry binding mismatch",
    )
    model = _json(captured["model_config"])
    _require(model == manifest.get("model"), "model configuration mismatch")
    retrieval = _json(captured["retrieval_config"])
    _require(retrieval == manifest.get("retrieval"), "retrieval configuration mismatch")
    _require(retrieval.get("supported_k") == list(DEPTHS), "retrieval depths mismatch")
    for field, name in (("corpus_sha256", "corpus"),):
        _require(retrieval.get(field) == artifacts[name]["sha256"], f"retrieval {field} mismatch")
    index_manifest = _json(captured["retrieval_manifest"])
    for field, name in (
        ("corpus_sha256", "corpus"),
        ("index_sha256", "index"),
        ("document_mapping_sha256", "document_mapping"),
    ):
        _require(
            index_manifest.get(field) == artifacts[name]["sha256"],
            f"index manifest {field} mismatch",
        )

    registry: dict[str, dict[str, bool]] = {}
    for obj in _json(captured["attack_registry"]).get("objects", []):
        if obj.get("type") != "attack-pattern":
            continue
        for ref in obj.get("external_references", []):
            if ref.get("source_name") == "mitre-attack":
                tid = ref.get("external_id")
                _require(
                    validate_attack_id_syntax(tid) and tid not in registry,
                    "invalid/duplicate registry ID",
                )
                registry[tid] = {
                    "deprecated": bool(obj.get("x_mitre_deprecated", False)),
                    "revoked": bool(obj.get("revoked", False)),
                }
    _require(bool(registry), "empty ATT&CK registry")
    corpus_rows = _jsonl(captured["corpus"])
    corpus_ids = set(_unique(corpus_rows, "technique_id"))
    _require(bool(corpus_ids) and corpus_ids <= set(registry), "corpus IDs absent from registry")
    _require(
        _json(captured["document_mapping"]) == corpus_rows,
        "document mapping differs from corpus",
    )

    inputs = _unique(_jsonl(captured["inference"]), "sample_id")
    _require(
        all(set(row) == {"sample_id", "endpoint_evidence"} for row in inputs.values()),
        "inference fields must contain only sample_id and endpoint_evidence",
    )
    views = _unique(_jsonl(captured["views"]), "view_id")
    truth_rows = _unique(_jsonl(captured["ground_truth"]), "view_id")
    pairs = _unique(_jsonl(captured["pairs"]), "pair_id")
    _require(set(inputs) == set(views) == set(truth_rows), "dataset sample/GT/view join mismatch")
    _require(
        _integer(dataset.get("view_count"))
        and dataset["view_count"] == len(views)
        and _integer(dataset.get("pair_count"))
        and dataset["pair_count"] == len(pairs),
        "dataset manifest count mismatch",
    )
    split_manifest = _json(captured["split_manifest"])
    split_pairs: dict[str, str] = {}
    for split in ("test", "dev"):
        ids = split_manifest.get(split)
        _require(isinstance(ids, list), "split manifest missing list")
        for pair_id in ids:
            _require(
                isinstance(pair_id, str) and pair_id not in split_pairs,
                "duplicate/invalid split pair",
            )
            split_pairs[pair_id] = split
    _require(set(split_pairs) == set(pairs), "split manifest is not an exact partition")
    split_counts = dataset.get("split_counts")
    _require(
        isinstance(split_counts, dict)
        and set(split_counts) == {"test", "dev"}
        and all(_integer(split_counts[split]) for split in ("test", "dev"))
        and all(split_counts[split] == len(split_manifest[split]) for split in ("test", "dev")),
        "dataset manifest count mismatch",
    )
    embedded_view_ids: set[str] = set()
    for pair_id, pair in pairs.items():
        _require(pair.get("split") == split_pairs[pair_id], "pair split disagreement")
        for view_type in ("single", "contextual"):
            embedded_view = pair.get(f"{view_type}_view")
            embedded_truth = pair.get(f"{view_type}_ground_truth")
            _require(isinstance(embedded_view, dict), f"missing embedded pair {view_type}_view")
            _require(
                isinstance(embedded_truth, dict), f"missing embedded pair {view_type}_ground_truth"
            )
            view_id = embedded_view.get("view_id")
            _require(
                isinstance(view_id, str) and view_id in views and view_id not in embedded_view_ids,
                "embedded pair view must reference one unique known view",
            )
            _require(
                embedded_view.get("pair_id") == pair_id
                and embedded_view.get("view_type") == view_type,
                "embedded pair view metadata disagrees with its owning pair",
            )
            _require(embedded_view == views[view_id], "embedded pair view disagrees with sidecar")
            _require(
                embedded_truth == truth_rows[view_id],
                "embedded pair ground truth disagrees with sidecar",
            )
            embedded_view_ids.add(view_id)
    _require(embedded_view_ids == set(views), "embedded pair view coverage mismatch")
    expected_samples: dict[str, dict[str, str]] = {}
    pair_views: dict[str, list[str]] = defaultdict(list)
    ground_truth = {}
    for sample_id, view in views.items():
        pair_id, view_type = view.get("pair_id"), view.get("view_type")
        _require(
            pair_id in pairs and view_type in {"single", "contextual"}, "invalid view metadata"
        )
        pair_views[pair_id].append(view_type)
        _require(
            isinstance(inputs[sample_id].get("endpoint_evidence"), str)
            and bool(inputs[sample_id]["endpoint_evidence"].strip()),
            "missing endpoint evidence",
        )
        truth = truth_rows[sample_id]
        ids = truth.get("technique_ids")
        _require(
            isinstance(ids, list) and all(isinstance(tid, str) for tid in ids),
            "GT IDs must be a list of strings",
        )
        _require(
            len(ids) == len(set(ids)) and set(ids) <= corpus_ids,
            "duplicate/unknown ground-truth ID",
        )
        label_status = truth.get("label_status")
        _require(
            label_status in {"mapped", "ambiguous", "unmapped"}
            and bool(ids) == (label_status == "mapped"),
            "GT label status mismatch",
        )
        if split_pairs[pair_id] == "test":
            expected_samples[sample_id] = {
                "sample_id": sample_id,
                "pair_id": pair_id,
                "view_type": view_type,
            }
            ground_truth[sample_id] = tuple(sorted(ids))
    _require(
        set(pair_views) == set(pairs)
        and all(sorted(v) == ["contextual", "single"] for v in pair_views.values()),
        "every pair must have exactly single/contextual views",
    )
    sample_ids = sorted(expected_samples)
    _require(len(sample_ids) == expected_sample_count, "TEST cohort cardinality mismatch")
    _require(
        manifest.get("sample_ids") == sample_ids,
        "manifest must contain ALL TEST views without GT filtering",
    )
    _require(
        manifest.get("samples") == [expected_samples[sid] for sid in sample_ids],
        "manifest sample metadata mismatch",
    )
    _require(
        manifest.get("expected_request_count") == len(sample_ids) * len(CONDITIONS),
        "request matrix count mismatch",
    )
    _require(
        manifest.get("maximum_attempts")
        == manifest["expected_request_count"] * (execution["retries"] + 1),
        "maximum attempt count mismatch",
    )
    digest = hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()
    _require(
        set(prediction_paths) == set(CONDITIONS),
        "prediction files must cover the exact five conditions",
    )
    rows = []
    run_ids = set()
    for condition in CONDITIONS:
        path = Path(prediction_paths[condition])
        if not path.is_absolute():
            path = root / path
        by_sample = _unique(_jsonl(path.read_bytes()), "sample_id")
        _require(
            set(by_sample) == set(sample_ids),
            f"missing or unexpected sample in condition {condition}",
        )
        for sample_id in sample_ids:
            row = dict(by_sample[sample_id])
            _validate_record(
                row,
                condition,
                expected_samples[sample_id],
                manifest,
                digest,
                artifacts,
                registry,
                corpus_ids,
            )
            run_ids.add(row["run_id"])
            rows.append(row)
    _require(len(run_ids) == 1, "mixed run IDs are not one execution matrix")
    if verify_journal:
        _validate_journal(
            Path(manifest_path).resolve().parent / "request_journal.jsonl",
            manifest,
            digest,
            rows,
        )
    return EvaluationInputs(
        digest,
        manifest["experiment_id"],
        manifest["execution_mode"],
        tuple(sample_ids),
        tuple(rows),
        ground_truth,
        registry,
    )


def _validate_record(row, condition, sample, manifest, digest, artifacts, registry, corpus_ids):
    _require(
        set(row) == _RECORD_FIELDS,
        "record fields do not match v1 envelope (GT labels are forbidden)",
    )
    expected = {
        "schema_version": "1.0.0",
        "execution_mode": manifest["execution_mode"],
        "experiment_id": manifest["experiment_id"],
        "manifest_sha256": digest,
        "condition": condition,
        "retrieval_k": 0 if condition == "no_rag" else int(condition[5:]),
        "provider": manifest["model"]["provider"],
        "model": manifest["model"]["model"],
        "model_version": manifest.get("model_version"),
        "output_schema_sha256": manifest["output_schema_sha256"],
        "ground_truth_version": manifest["benchmark_version"],
        "attack_release": "19.2",
        **sample,
    }
    for key, name in (
        ("prompt_sha256", "prompt"),
        ("model_config_sha256", "model_config"),
        ("dataset_sha256", "inference"),
        ("ground_truth_sha256", "ground_truth"),
        ("corpus_sha256", "corpus"),
        ("index_sha256", "index"),
    ):
        expected[key] = artifacts[name]["sha256"]
    for key, value in expected.items():
        _require(type(row[key]) is type(value) and row[key] == value, f"record {key} mismatch")
    _require(isinstance(row["run_id"], str) and bool(row["run_id"].strip()), "missing run_id")
    _require(row["terminal"] is True, "nonterminal record")
    _require(
        row["raw_response"] is None and row["raw_response_logged"] is False,
        "raw response logging is disabled",
    )
    status = row["parse_status"]
    _require(status in {s.value for s in ParseStatus}, "unknown parse status")
    _require(row["success"] is (status == "VALID"), "success/status contradiction")
    ids = row["parsed_technique_ids"]
    _require(
        isinstance(ids, list) and len(ids) <= 1 and all(isinstance(tid, str) for tid in ids),
        "single-ID output required",
    )
    if status in {"VALID", "INVALID_ID"}:
        _require(len(ids) == 1, "parsed status needs one ID")
        valid = validate_attack_id_syntax(ids[0]) and ids[0] in registry
        _require(valid == (status == "VALID"), "ID/status contradict pinned-registry membership")
    else:
        _require(ids == [], "failed parse cannot have a parsed prediction")
    candidates = row["retrieved_candidates"]
    _require(
        isinstance(candidates, list) and len(candidates) == row["retrieval_k"],
        "candidate count/depth mismatch",
    )
    for rank, candidate in enumerate(candidates, 1):
        _require(
            isinstance(candidate, dict) and set(candidate) == {"technique_id", "rank", "score"},
            "invalid candidate fields",
        )
        _require(
            type(candidate["rank"]) is int and candidate["rank"] == rank,
            "noncontiguous candidate rank",
        )
        _require(candidate["technique_id"] in corpus_ids, "candidate not in corpus")
        _require(
            type(candidate["score"]) in (float, int) and math.isfinite(candidate["score"]),
            "non-finite candidate score",
        )
    _require(
        len({candidate["technique_id"] for candidate in candidates}) == len(candidates),
        "duplicate retrieved candidate",
    )
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        _require(row[field] is None or _integer(row[field]), f"invalid {field}")
    if row["prompt_tokens"] is not None and row["completion_tokens"] is not None:
        _require(
            row["total_tokens"] == row["prompt_tokens"] + row["completion_tokens"],
            "token accounting mismatch",
        )
    else:
        _require(row["total_tokens"] is None, "total tokens cannot invent missing usage")
    _require(
        type(row["latency_ms"]) in (int, float)
        and math.isfinite(row["latency_ms"])
        and row["latency_ms"] >= 0,
        "invalid latency",
    )
    _require(
        _integer(row["retry_count"]) and _integer(row["request_attempt_count"], minimum=1),
        "invalid attempt accounting",
    )
    _require(
        row["retry_count"] <= max(row["request_attempt_count"] - 1, 0),
        "retry count exceeds attempts",
    )
    _require(
        row["request_attempt_count"] <= manifest["execution"]["retries"] + 1,
        "record exceeds bound retry policy",
    )
    for field in ("error_type", "error_message"):
        _require(row[field] is None or isinstance(row[field], str), f"invalid {field}")
    _require(isinstance(row["timestamp"], str), "timestamp must be ISO UTC")
    stamp = datetime.fromisoformat(row["timestamp"])
    _require(
        stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0,
        "timestamp must be UTC",
    )


def _validate_journal(
    path: Path,
    manifest: Mapping[str, Any],
    manifest_sha256: str,
    records: Sequence[Mapping[str, Any]],
) -> None:
    """Require durable completion evidence for every recorded mock dispatch."""
    _require(not path.is_symlink(), "journal cannot be a symlink")
    events = _jsonl(path.read_bytes())
    cap = manifest.get("fixture_max_requests")
    _require(
        _integer(cap, minimum=1) and cap >= len(records),
        "invalid fixture request budget",
    )
    _require(
        events[0]
        == {"event": "header", "manifest_sha256": manifest_sha256, "max_requests": cap},
        "journal header does not match manifest/budget",
    )
    by_key = {(row["sample_id"], row["condition"]): row for row in records}
    _require(len(by_key) == len(records), "duplicate sample-condition record")
    active: tuple[str, str] | None = None
    completed: set[tuple[str, str]] = set()
    consumed = 0
    start = 0
    for event in events[1:]:
        key_fields = event.get("key")
        _require(
            isinstance(key_fields, list)
            and len(key_fields) == 2
            and all(isinstance(value, str) for value in key_fields),
            "invalid journal key",
        )
        key = (key_fields[0], key_fields[1])
        _require(key in by_key, "journal key outside prediction matrix")
        kind = event.get("event")
        if kind == "begin" and set(event) == {"event", "key"}:
            _require(active is None and key not in completed, "duplicate/overlapping journal begin")
            active, start = key, consumed
        elif kind == "attempt" and set(event) == {"event", "key", "ordinal"}:
            _require(
                active == key
                and type(event["ordinal"]) is int
                and event["ordinal"] == consumed + 1,
                "invalid attempt journal",
            )
            consumed += 1
        elif kind == "complete" and set(event) == {"event", "key", "record_sha256"}:
            row = by_key[key]
            _require(active == key and consumed > start, "completed journal lacks execution")
            _require(
                event["record_sha256"] == hashlib.sha256(canonical_json_bytes(row)).hexdigest()
                and row["request_attempt_count"] == consumed - start,
                "record/journal hash or request accounting mismatch",
            )
            completed.add(key)
            active = None
        else:
            raise ValueError("unknown or malformed journal event")
    _require(active is None, "in-flight journal cannot certify a completed matrix")
    _require(completed == set(by_key), "incomplete journal/prediction matrix")
    _require(consumed <= cap, "journal request budget exceeded")


def retrieval_observations(inputs: EvaluationInputs) -> dict[str, Any]:
    """Confirmed positive-view Hit/Recall only, at each condition's actual k.

    Parse statuses are separate observations, not a precedence-based failure
    decomposition. The function does not calculate final accuracy or ID rates.
    """
    result: dict[str, Any] = {}
    for condition in CONDITIONS[1:]:
        k = int(condition[5:])
        rows = sorted(
            (row for row in inputs.records if row["condition"] == condition),
            key=lambda row: row["sample_id"],
        )
        hits, recalls = [], []
        statuses = Counter()
        retired_count = 0
        for row in rows:
            statuses[row["parse_status"]] += 1
            for tid in row["parsed_technique_ids"]:
                flags = inputs.registry.get(tid, {})
                retired_count += bool(flags.get("deprecated") or flags.get("revoked"))
            truth = set(inputs.ground_truth[row["sample_id"]])
            if not truth:
                continue
            found = truth.intersection(
                candidate["technique_id"] for candidate in row["retrieved_candidates"]
            )
            hits.append(int(bool(found)))
            recalls.append(len(found) / len(truth))
        count = len(hits)
        result[condition] = {
            "retrieval_k": k,
            "total_samples": len(rows),
            "positive_samples": count,
            "non_positive_samples": len(rows) - count,
            "hit_rate": sum(hits) / count if count else None,
            "macro_recall": sum(recalls) / count if count else None,
            "gt_absent_count": count - sum(hits),
            "parse_status_counts": dict(sorted(statuses.items())),
            "retired_id_observation_count": retired_count,
        }
    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "execution_mode": inputs.execution_mode,
        "manifest_sha256": inputs.manifest_sha256,
        "status": "EVALUATOR_INFRA_PARTIAL",
        "canonical_scoring": "HUMAN_DECISION_REQUIRED",
        "unresolved_policies": list(UNRESOLVED_POLICIES),
        "by_condition": result,
    }


def usage_observations(inputs: EvaluationInputs) -> dict[str, Any]:
    """Report observed resource totals without scientific denominators or cost claims."""
    by_condition: dict[str, Any] = {}
    for condition in CONDITIONS:
        rows = sorted(
            (row for row in inputs.records if row["condition"] == condition),
            key=lambda row: row["sample_id"],
        )
        observed: dict[str, Any] = {"sample_count": len(rows)}
        for field in ("prompt_tokens", "completion_tokens", "total_tokens", "latency_ms"):
            values = [row[field] for row in rows if row[field] is not None]
            observed[field] = {
                "sum": math.fsum(values) if field == "latency_ms" else sum(values),
                "present_count": len(values),
                "missing_count": len(rows) - len(values),
            }
        by_condition[condition] = observed
    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "execution_mode": inputs.execution_mode,
        "manifest_sha256": inputs.manifest_sha256,
        "status": "EVALUATOR_INFRA_PARTIAL",
        "canonical_scoring": "HUMAN_DECISION_REQUIRED",
        "unresolved_policies": list(UNRESOLVED_POLICIES),
        "by_condition": by_condition,
    }


def export_fixture_diagnostics(report: Mapping[str, Any], output_path: Path | str) -> None:
    """Exclusive-create fixture diagnostic JSON; never overwrite any artifact."""
    _require(
        report.get("execution_mode") == "mock_fixture"
        and report.get("canonical_scoring") == "HUMAN_DECISION_REQUIRED",
        "only gated fixture diagnostics may be exported",
    )
    output = Path(output_path).resolve()
    # A fixture exporter cannot write into artifacts/evaluation. Even a user's
    # home directory may be tracked by Git; require the actual system temp root.
    _require(
        output.is_relative_to(Path(tempfile.gettempdir()).resolve()),
        "fixture output must be inside the system temporary directory",
    )
    data = canonical_json_bytes(dict(report)) + b"\n"
    with output.open("xb") as handle:
        handle.write(data)
