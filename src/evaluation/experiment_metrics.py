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
from dataclasses import field as dc_field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from src.experiment.authorization import (
    ScientificProtocolApproval,
    protocol_decision_dict,
    validate_scientific_protocol,
)
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
        "returned_model_id",
        "response_id",
        "system_fingerprint",
        "request_timestamp_utc",
        "response_timestamp_utc",
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


def evaluate_end_to_end(*args: Any, **kwargs: Any) -> Any:
    """Canonical evaluator entrypoint.

    Requires an explicit, verified ScientificProtocolApproval contract.
    Caller-supplied flags (e.g. approved=True, force=True, arbitrary policy dicts)
    cannot enable scoring and fail closed with HumanDecisionRequired.
    """
    protocol = kwargs.get("protocol")
    if protocol is None or not isinstance(protocol, ScientificProtocolApproval):
        raise HumanDecisionRequired("HUMAN_DECISION_REQUIRED: " + "; ".join(UNRESOLVED_POLICIES))
    if not args:
        raise ValueError("inputs argument is required")
    output_dir = kwargs.get("output_dir")
    expected_id = kwargs.get("expected_experiment_id")
    return evaluate_experiment(
        args[0], protocol, output_dir=output_dir, expected_experiment_id=expected_id
    )


def evaluate_conditional_accuracy(*args: Any, **kwargs: Any) -> Any:
    """No canonical conditional accuracy is inferred without frozen protocol."""
    protocol = kwargs.get("protocol")
    if protocol is None or not isinstance(protocol, ScientificProtocolApproval):
        raise HumanDecisionRequired("HUMAN_DECISION_REQUIRED: " + "; ".join(UNRESOLVED_POLICIES))
    if not args:
        raise ValueError("inputs argument is required")
    return compute_retrieval_conditional_metrics(args[0], protocol)


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
    ground_truth_status: Mapping[str, str] = dc_field(default_factory=dict)
    manifest_data: Mapping[str, Any] = dc_field(default_factory=dict)
    corpus_ids: tuple[str, ...] = dc_field(default_factory=tuple)


def load_evaluation_inputs(
    manifest_path: Path | str,
    prediction_paths: Mapping[str, Path | str],
    *,
    repository_root: Path | str,
) -> EvaluationInputs:
    """Validate the complete TEST1280 or DEV x five-condition matrix, without scoring."""
    manifest = _json(Path(manifest_path).read_bytes())
    target_split = manifest.get("split", "test")
    expected_count = 1280 if target_split == "test" else len(manifest.get("sample_ids", []))
    return _load_evaluation_inputs(
        manifest_path,
        prediction_paths,
        repository_root=repository_root,
        expected_sample_count=expected_count,
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
    _require(manifest.get("status") in {"pre_freeze", "frozen"}, "unsupported freeze status")
    _require(
        manifest.get("execution_mode") in {"mock_fixture", "live"},
        "only mock_fixture or live records are supported before freeze",
    )
    target_split = manifest.get("split")
    _require(target_split in {"test", "dev"}, "only complete TEST or DEV cohort is supported")
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
    ground_truth_status = {}
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
        if split_pairs[pair_id] == target_split:
            expected_samples[sample_id] = {
                "sample_id": sample_id,
                "pair_id": pair_id,
                "view_type": view_type,
            }
            ground_truth[sample_id] = tuple(sorted(ids))
            ground_truth_status[sample_id] = label_status
    _require(
        set(pair_views) == set(pairs)
        and all(sorted(v) == ["contextual", "single"] for v in pair_views.values()),
        "every pair must have exactly single/contextual views",
    )
    sample_ids = sorted(expected_samples)
    _require(
        len(sample_ids) == expected_sample_count,
        f"{target_split.upper()} cohort cardinality mismatch",
    )
    _require(
        manifest.get("sample_ids") == sample_ids,
        f"manifest must contain ALL {target_split.upper()} views without GT filtering",
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
    summary_path = Path(manifest_path).resolve().parent / "run_summary.json"
    if summary_path.is_file():
        summary_data = _json(summary_path.read_bytes())
        _require(
            summary_data.get("complete") is not False,
            "evaluator rejects incomplete run (complete=false)",
        )
        _require(
            not summary_data.get("stopped_reason"),
            f"evaluator rejects stopped run: {summary_data.get('stopped_reason')}",
        )
        _require(not summary_data.get("has_breach"), "evaluator rejects breached run")

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
        ground_truth_status=ground_truth_status,
        manifest_data=dict(manifest),
        corpus_ids=tuple(sorted(corpus_ids)),
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
    d1_policy = manifest.get("protocol", {}).get("d1_raw_response_policy", "DISCARD")
    if d1_policy == "DISCARD":
        _require(
            row["raw_response"] is None and row["raw_response_logged"] is False,
            "raw response logging is disabled under DISCARD policy",
        )
    elif d1_policy == "RECORD_ONLY":
        _require(
            (row["raw_response"] is None or isinstance(row["raw_response"], str))
            and isinstance(row["raw_response_logged"], bool),
            "invalid raw response logging under RECORD_ONLY policy",
        )
    elif d1_policy == "LOG_SEPARATELY":
        _require(
            row["raw_response"] is None and row["raw_response_logged"] is True,
            "raw response must be logged separately under LOG_SEPARATELY policy",
        )
    else:
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
    for field in ("returned_model_id", "response_id", "system_fingerprint"):
        _require(row[field] is None or isinstance(row[field], str), f"invalid {field}")
    for ts_field in ("request_timestamp_utc", "response_timestamp_utc"):
        _require(row[ts_field] is None or isinstance(row[ts_field], str), f"invalid {ts_field}")
        if row[ts_field] is not None:
            ts = datetime.fromisoformat(row[ts_field])
            _require(
                ts.utcoffset() is not None and ts.utcoffset().total_seconds() == 0,
                f"{ts_field} must be UTC",
            )
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
    cap = manifest.get("fixture_max_requests") or manifest.get("authorized_max_provider_attempts")
    _require(
        _integer(cap, minimum=1) and cap >= len(records),
        "invalid fixture request budget",
    )
    _require(
        events[0] == {"event": "header", "manifest_sha256": manifest_sha256, "max_requests": cap},
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
        elif kind == "transition" and set(event) == {"event", "key", "state"}:
            if event["state"] == "RESERVED":
                _require(
                    active is None and key not in completed,
                    "duplicate/overlapping journal reservation",
                )
                active, start = key, consumed
            else:
                _require(active == key, "transition for inactive key")
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
        elif kind == "monetary_reserve":
            _require(
                active is None and key not in completed,
                "duplicate or overlapping monetary reserve",
            )
        elif kind == "attempt_receipt":
            _require(active == key, "attempt_receipt for inactive key")
        elif kind == "monetary_settle":
            _require(key in completed, "monetary_settle before complete")
            _require(
                not event.get("breach", False),
                f"evaluator rejects run with monetary breach: {event.get('breach_reason')}",
            )
        elif kind in ("monetary_cancel_orphan", "monetary_cancel_hold", "reservation_abandoned"):
            _require(key in by_key, f"{kind} key outside prediction matrix")
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


def _atomic_write_json(path: Path, data: Mapping[str, Any]) -> None:
    """Write machine-readable JSON artifact atomically using temp replace."""
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".json.tmp")
    temp.unlink(missing_ok=True)
    with temp.open("xb") as handle:
        handle.write(canonical_json_bytes(data) + b"\n")
        handle.flush()
        import os

        os.fsync(handle.fileno())
    temp.replace(path)


def verify_evaluator_provenance(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    expected_experiment_id: str | None = None,
) -> None:
    """Validate that run provenance strictly matches protocol, manifest, and inputs.

    Fails closed on foreign experiment ID, corrupted hashes, or protocol drift.
    """
    if not isinstance(protocol, ScientificProtocolApproval):
        raise TypeError(f"Expected ScientificProtocolApproval, got {type(protocol).__name__}")
    validate_scientific_protocol(protocol)

    manifest = inputs.manifest_data
    if expected_experiment_id and inputs.experiment_id != expected_experiment_id:
        raise ValueError(
            f"foreign experiment ID: expected {expected_experiment_id}, got {inputs.experiment_id}"
        )

    if manifest:
        if manifest.get("experiment_id") != inputs.experiment_id:
            raise ValueError(
                f"foreign experiment ID: inputs has {inputs.experiment_id}, "
                f"manifest has {manifest.get('experiment_id')}"
            )
        manifest_proto_sha = manifest.get("protocol_sha256")
        if manifest_proto_sha and manifest_proto_sha != protocol.protocol_sha256:
            raise ValueError(
                f"wrong protocol hash: manifest has {manifest_proto_sha}, "
                f"evaluator given {protocol.protocol_sha256}"
            )
        artifacts = manifest.get("artifacts", {})
        if "experiment_config" in artifacts and manifest.get("config_sha256"):
            if manifest["config_sha256"] != artifacts["experiment_config"]["sha256"]:
                raise ValueError(
                    "wrong config hash: manifest config_sha256 does not match artifact"
                )
        if "ground_truth" in artifacts:
            gt_sha = artifacts["ground_truth"]["sha256"]
            for r in inputs.records:
                if r.get("ground_truth_sha256") != gt_sha:
                    raise ValueError("wrong GT hash: record ground_truth_sha256 mismatch")
        if "inference" in artifacts:
            inf_sha = artifacts["inference"]["sha256"]
            for r in inputs.records:
                if r.get("dataset_sha256") != inf_sha:
                    raise ValueError("wrong dataset hash: record dataset_sha256 mismatch")
        if "prompt" in artifacts:
            prompt_sha = artifacts["prompt"]["sha256"]
            for r in inputs.records:
                if r.get("prompt_sha256") != prompt_sha:
                    raise ValueError("wrong prompt hash: record prompt_sha256 mismatch")

    # Record identity and completeness checks
    by_condition: dict[str, set[str]] = defaultdict(set)
    for r in inputs.records:
        cond = r["condition"]
        sid = r["sample_id"]
        if sid in by_condition[cond]:
            raise ValueError(f"unexpected duplicate record: sample {sid} in condition {cond}")
        by_condition[cond].add(sid)
        if r.get("experiment_id") != inputs.experiment_id:
            raise ValueError(
                f"foreign experiment ID: record has {r.get('experiment_id')}, "
                f"inputs has {inputs.experiment_id}"
            )

    expected_samples = set(inputs.sample_ids)
    for cond in CONDITIONS:
        missing = expected_samples - by_condition[cond]
        if missing:
            raise ValueError(f"missing logical sample in condition {cond}: {len(missing)} missing")

    # Model provenance drift check: all records with returned_model_id must match
    returned_models = {
        r.get("returned_model_id") for r in inputs.records if r.get("returned_model_id") is not None
    }
    if len(returned_models) > 1:
        models_str = sorted(returned_models)
        raise ValueError(
            f"model provenance drift detected: multiple returned_model_ids in run: {models_str}"
        )

    # Timestamp consistency and tamper prevention
    for r in inputs.records:
        req_ts = r.get("request_timestamp_utc")
        resp_ts = r.get("response_timestamp_utc")
        parse_st = r.get("parse_status")
        is_transport_failure = parse_st in (
            ParseStatus.API_FAILURE.value,
            ParseStatus.TIMEOUT.value,
            "API_FAILURE",
            "TIMEOUT",
        )
        if req_ts is None and resp_ts is not None:
            raise ValueError(
                f"timestamp anomaly on record {r.get('sample_id')}: "
                f"response timestamp present without request timestamp"
            )
        if req_ts is not None and resp_ts is None:
            if not is_transport_failure:
                raise ValueError(
                    f"incomplete timestamps on record {r.get('sample_id')}: "
                    f"request_timestamp_utc={req_ts}, response_timestamp_utc={resp_ts}"
                )
        if req_ts is not None and resp_ts is not None:
            t_req = datetime.fromisoformat(req_ts)
            t_resp = datetime.fromisoformat(resp_ts)
            if t_resp < t_req:
                raise ValueError(
                    f"timestamp tampering detected: response ({resp_ts}) before request ({req_ts})"
                )


def compute_condition_metrics(
    records: Sequence[Mapping[str, Any]],
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition: str,
) -> dict[str, Any]:
    """Compute primary scientific metrics for one experimental condition under protocol."""
    cond_records = [r for r in records if r["condition"] == condition]
    logical_sample_count = len(cond_records)

    scorable_records = []
    unmapped_count = 0
    ambiguous_count = 0
    for r in cond_records:
        sid = r["sample_id"]
        gt = inputs.ground_truth.get(sid, ())
        status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
        if status == "ambiguous":
            ambiguous_count += 1
            if protocol.d2c_ambiguous_ground_truth != "EXCLUDE":
                scorable_records.append(r)
        elif status == "unmapped" or not gt:
            unmapped_count += 1
            if protocol.d2b_empty_ground_truth == "TREAT_AS_NEGATIVE":
                scorable_records.append(r)
        else:
            scorable_records.append(r)

    scorable_sample_count = len(scorable_records)
    coverage = scorable_sample_count / logical_sample_count if logical_sample_count > 0 else None

    completed_records = [
        r
        for r in cond_records
        if r["parse_status"] in {"VALID", "INVALID_ID", "MALFORMED_RESPONSE"}
    ]
    invalid_id_records = [r for r in cond_records if r["parse_status"] == "INVALID_ID"]
    invalid_id_rate = (
        len(invalid_id_records) / len(completed_records) if completed_records else None
    )

    syntax_error_records = []
    unknown_id_records = []
    for r in invalid_id_records:
        tids = r.get("parsed_technique_ids", [])
        if not tids:
            syntax_error_records.append(r)
        else:
            tid = tids[0]
            if not validate_attack_id_syntax(tid):
                syntax_error_records.append(r)
            else:
                unknown_id_records.append(r)

    invalid_syntax_count = len(syntax_error_records)
    invalid_syntax_rate = (
        invalid_syntax_count / len(completed_records) if completed_records else None
    )
    unknown_id_count = len(unknown_id_records)
    unknown_id_rate = unknown_id_count / len(completed_records) if completed_records else None

    provider_failure_records = [
        r
        for r in cond_records
        if r["parse_status"] in {"TIMEOUT", "REFUSAL", "INCOMPLETE", "API_FAILURE"}
    ]
    provider_failure_rate = (
        len(provider_failure_records) / logical_sample_count if logical_sample_count > 0 else None
    )

    parse_failure_records = [r for r in cond_records if r["parse_status"] == "MALFORMED_RESPONSE"]
    parse_failure_rate = (
        len(parse_failure_records) / logical_sample_count if logical_sample_count > 0 else None
    )

    retired_count = 0
    for r in cond_records:
        for tid in r.get("parsed_technique_ids", []):
            flags = inputs.registry.get(tid, {})
            if flags.get("deprecated") or flags.get("revoked"):
                retired_count += 1
    retired_id_rate = retired_count / len(completed_records) if completed_records else None

    # D2a ANY_MATCH: predicted ID must belong to GT set
    correct_records = []
    for r in scorable_records:
        sid = r["sample_id"]
        gt = set(inputs.ground_truth.get(sid, ()))
        if r["parse_status"] == "VALID" and r.get("parsed_technique_ids"):
            pred = r["parsed_technique_ids"][0]
            if pred in gt:
                correct_records.append(r)

    correct_count = len(correct_records)
    accuracy_end_to_end = (
        correct_count / scorable_sample_count if scorable_sample_count > 0 else None
    )

    valid_scorable_records = [r for r in scorable_records if r["parse_status"] == "VALID"]
    accuracy_valid_outputs = (
        correct_count / len(valid_scorable_records) if valid_scorable_records else None
    )

    # D2d Macro-F1 across frozen retrieval corpus universe (invariant size)
    technique_universe = (
        sorted(inputs.corpus_ids) if inputs.corpus_ids else sorted(inputs.registry.keys())
    )
    universe_size = len(technique_universe)
    f1_sum = 0.0
    for tid in technique_universe:
        tp = sum(
            1
            for r in scorable_records
            if r.get("parsed_technique_ids") == [tid]
            and tid in inputs.ground_truth.get(r["sample_id"], ())
        )
        fp = sum(
            1
            for r in scorable_records
            if r.get("parsed_technique_ids") == [tid]
            and tid not in inputs.ground_truth.get(r["sample_id"], ())
        )
        fn = sum(
            1
            for r in scorable_records
            if tid in inputs.ground_truth.get(r["sample_id"], ())
            and r.get("parsed_technique_ids") != [tid]
        )
        support = sum(
            1 for r in scorable_records if tid in inputs.ground_truth.get(r["sample_id"], ())
        )
        predictions = sum(1 for r in scorable_records if r.get("parsed_technique_ids") == [tid])
        if support == 0 and predictions == 0:
            # Zero denominator per D2d/D2j: unobserved class contributes 0.0 to numerator sum
            f1 = 0.0
        else:
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1_sum += f1

    macro_f1 = (f1_sum / universe_size) if universe_size > 0 else None

    return {
        "condition": condition,
        "logical_sample_count": logical_sample_count,
        "scorable_sample_count": scorable_sample_count,
        "valid_scorable_sample_count": len(valid_scorable_records),
        "completed_record_count": len(completed_records),
        "coverage": coverage,
        "accuracy_end_to_end": accuracy_end_to_end,
        "accuracy_valid_outputs": accuracy_valid_outputs,
        "macro_f1": macro_f1,
        "correct_count": correct_count,
        "invalid_id_count": len(invalid_id_records),
        "invalid_id_rate": invalid_id_rate,
        "invalid_syntax_count": invalid_syntax_count,
        "invalid_syntax_rate": invalid_syntax_rate,
        "unknown_id_count": unknown_id_count,
        "unknown_id_rate": unknown_id_rate,
        "provider_failure_count": len(provider_failure_records),
        "provider_failure_rate": provider_failure_rate,
        "parse_failure_count": len(parse_failure_records),
        "parse_failure_rate": parse_failure_rate,
        "retired_id_observation_count": retired_count,
        "retired_id_rate": retired_id_rate,
        "unmapped_ground_truth_count": unmapped_count,
        "ambiguous_ground_truth_count": ambiguous_count,
        "unmapped_exclusion_reason": "UNMAPPED_GROUND_TRUTH" if unmapped_count else None,
        "ambiguous_exclusion_reason": "AMBIGUOUS_GROUND_TRUTH" if ambiguous_count else None,
    }


def compute_retrieval_conditional_metrics(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
) -> dict[str, Any]:
    """Compute retrieval-conditional metrics at actual retrieved k under D2h ANY_GT_RETRIEVED."""
    by_condition = {}
    for condition in CONDITIONS[1:]:  # rag_k1, rag_k3, rag_k5, rag_k10
        k = int(condition[5:])
        cond_records = [r for r in inputs.records if r["condition"] == condition]
        scorable_records = []
        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "mapped" and gt:
                scorable_records.append(r)

        retrieval_success_records = []
        retrieval_failure_records = []
        for r in scorable_records:
            gt = set(inputs.ground_truth.get(r["sample_id"], ()))
            retrieved_ids = {c["technique_id"] for c in r.get("retrieved_candidates", [])}
            if bool(retrieved_ids & gt):
                retrieval_success_records.append(r)
            else:
                retrieval_failure_records.append(r)

        def is_correct(r):
            if r["parse_status"] == "VALID" and r.get("parsed_technique_ids"):
                return r["parsed_technique_ids"][0] in set(
                    inputs.ground_truth.get(r["sample_id"], ())
                )
            return False

        succ_count = len(retrieval_success_records)
        fail_count = len(retrieval_failure_records)

        succ_correct = sum(1 for r in retrieval_success_records if is_correct(r))
        fail_correct = sum(1 for r in retrieval_failure_records if is_correct(r))

        p_correct_given_success = (succ_correct / succ_count) if succ_count > 0 else None
        p_correct_given_failure = (fail_correct / fail_count) if fail_count > 0 else None

        by_condition[condition] = {
            "retrieval_k": k,
            "scorable_sample_count": len(scorable_records),
            "retrieval_success_count": succ_count,
            "retrieval_failure_count": fail_count,
            "P_correct_given_retrieval_success": p_correct_given_success,
            "P_correct_given_retrieval_failure": p_correct_given_failure,
            "retrieval_success_correct_count": succ_correct,
            "retrieval_failure_correct_count": fail_correct,
        }

    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "retrieval_success_definition": protocol.d2h_conditional_retrieval,
        "by_condition": by_condition,
    }


def compute_failure_decomposition(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
) -> dict[str, Any]:
    """Analyze failures along independent diagnostic axes without forced mutual exclusion."""
    by_condition = {}
    for condition in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == condition]
        scorable_records = []
        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "mapped" and gt:
                scorable_records.append(r)

        total_scorable = len(scorable_records)
        retrieval_misses = 0
        provider_failures = 0
        parse_failures = 0
        invalid_attack_ids = 0
        valid_but_wrong = 0
        overlap_retrieval_miss_and_wrong = 0

        for r in scorable_records:
            gt = set(inputs.ground_truth.get(r["sample_id"], ()))
            status = r["parse_status"]
            retrieved = {c["technique_id"] for c in r.get("retrieved_candidates", [])}
            is_rag = condition != "no_rag"
            retrieval_miss = is_rag and not bool(retrieved & gt)
            if retrieval_miss:
                retrieval_misses += 1

            if status in {"TIMEOUT", "REFUSAL", "INCOMPLETE", "API_FAILURE"}:
                provider_failures += 1
            elif status == "MALFORMED_RESPONSE":
                parse_failures += 1
            elif status == "INVALID_ID":
                invalid_attack_ids += 1
            elif status == "VALID":
                pred = r.get("parsed_technique_ids", [None])[0]
                if pred not in gt:
                    valid_but_wrong += 1
                    if retrieval_miss:
                        overlap_retrieval_miss_and_wrong += 1

        by_condition[condition] = {
            "total_scorable_samples": total_scorable,
            "retrieval_miss_count": retrieval_misses,
            "retrieval_miss_rate": (retrieval_misses / total_scorable) if total_scorable else None,
            "provider_failure_count": provider_failures,
            "provider_failure_rate": (provider_failures / total_scorable)
            if total_scorable
            else None,
            "parse_failure_count": parse_failures,
            "parse_failure_rate": (parse_failures / total_scorable) if total_scorable else None,
            "invalid_attack_id_count": invalid_attack_ids,
            "invalid_attack_id_rate": (invalid_attack_ids / total_scorable)
            if total_scorable
            else None,
            "valid_but_wrong_classification_count": valid_but_wrong,
            "valid_but_wrong_classification_rate": (valid_but_wrong / total_scorable)
            if total_scorable
            else None,
            "overlap_retrieval_miss_and_wrong_classification": overlap_retrieval_miss_and_wrong,
        }

    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "failure_axes": [
            "retrieval_miss",
            "provider_failure",
            "parse_failure",
            "invalid_attack_id",
            "valid_but_wrong_classification",
        ],
        "by_condition": by_condition,
    }


def compute_technique_metrics(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
) -> dict[str, Any]:
    """Compute per-technique TP, FP, FN, precision, recall, and F1 per condition."""
    technique_universe = (
        sorted(inputs.corpus_ids) if inputs.corpus_ids else sorted(inputs.registry.keys())
    )
    by_condition = {}
    for condition in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == condition]
        scorable_records = [
            r
            for r in cond_records
            if inputs.ground_truth_status.get(
                r["sample_id"],
                "mapped" if inputs.ground_truth.get(r["sample_id"]) else "unmapped",
            )
            == "mapped"
            and inputs.ground_truth.get(r["sample_id"])
        ]
        per_class = {}
        for tid in technique_universe:
            tp = sum(
                1
                for r in scorable_records
                if r.get("parsed_technique_ids") == [tid]
                and tid in inputs.ground_truth.get(r["sample_id"], ())
            )
            fp = sum(
                1
                for r in scorable_records
                if r.get("parsed_technique_ids") == [tid]
                and tid not in inputs.ground_truth.get(r["sample_id"], ())
            )
            fn = sum(
                1
                for r in scorable_records
                if tid in inputs.ground_truth.get(r["sample_id"], ())
                and r.get("parsed_technique_ids") != [tid]
            )
            support = sum(
                1 for r in scorable_records if tid in inputs.ground_truth.get(r["sample_id"], ())
            )
            if tp + fp == 0 and support == 0:
                per_class[tid] = {
                    "tp": 0,
                    "fp": 0,
                    "fn": 0,
                    "support": 0,
                    "precision": None,
                    "recall": None,
                    "f1": None,
                }
            else:
                prec = (
                    tp / (tp + fp)
                    if (tp + fp) > 0
                    else (None if protocol.d2j_zero_denominator == "NULL" else 0.0)
                )
                rec = (
                    tp / (tp + fn)
                    if (tp + fn) > 0
                    else (None if protocol.d2j_zero_denominator == "NULL" else 0.0)
                )
                f1 = (
                    (2 * tp / (2 * tp + fp + fn))
                    if (2 * tp + fp + fn) > 0
                    else (None if protocol.d2j_zero_denominator == "NULL" else 0.0)
                )
                per_class[tid] = {
                    "tp": tp,
                    "fp": fp,
                    "fn": fn,
                    "support": support,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                }
        by_condition[condition] = per_class

    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "by_condition": by_condition,
    }


def compute_run_provenance(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
) -> dict[str, Any]:
    """Capture execution provenance for evaluation artifacts."""
    manifest = inputs.manifest_data
    run_id = manifest.get("run_id") if manifest else None
    if not run_id and inputs.records:
        run_id = inputs.records[0].get("run_id")
    returned_models = sorted(
        list(
            {
                r.get("returned_model_id")
                for r in inputs.records
                if r.get("returned_model_id") is not None
            }
        )
    )
    system_fingerprints = sorted(
        list(
            {
                r.get("system_fingerprint")
                for r in inputs.records
                if r.get("system_fingerprint") is not None
            }
        )
    )
    model_provenance = {
        "configured_provider": manifest.get("model", {}).get("provider") if manifest else None,
        "configured_model": manifest.get("model", {}).get("model") if manifest else None,
        "returned_models": returned_models,
        "system_fingerprints": system_fingerprints,
        "has_response_ids": any(r.get("response_id") is not None for r in inputs.records),
        "has_timestamps": any(r.get("request_timestamp_utc") is not None for r in inputs.records),
    }
    return {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "execution_mode": inputs.execution_mode,
        "run_id": run_id,
        "git_commit_sha": manifest.get("git_commit_sha") if manifest else None,
        "config_sha256": manifest.get("config_sha256") if manifest else None,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "protocol_decisions": protocol_decision_dict(protocol),
        "model_provenance": model_provenance,
        "dataset_sha256": manifest.get("artifacts", {}).get("inference", {}).get("sha256")
        if manifest
        else None,
        "ground_truth_sha256": manifest.get("artifacts", {}).get("ground_truth", {}).get("sha256")
        if manifest
        else None,
        "corpus_sha256": manifest.get("artifacts", {}).get("corpus", {}).get("sha256")
        if manifest
        else None,
        "index_sha256": manifest.get("artifacts", {}).get("index", {}).get("sha256")
        if manifest
        else None,
        "prompt_sha256": manifest.get("artifacts", {}).get("prompt", {}).get("sha256")
        if manifest
        else None,
        "attack_release": manifest.get("attack_release", "19.2") if manifest else "19.2",
        "model": manifest.get("model", {}) if manifest else {},
        "model_version": manifest.get("model_version") if manifest else None,
        "evaluation_timestamp": datetime.now(UTC).isoformat(),
    }


def evaluate_experiment(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    output_dir: Path | str | None = None,
    expected_experiment_id: str | None = None,
) -> dict[str, Any]:
    """Execute complete canonical evaluation across all conditions and write artifacts.

    Fails closed if provenance or protocol contract is invalid.
    """
    verify_evaluator_provenance(inputs, protocol, expected_experiment_id=expected_experiment_id)

    per_condition = {}
    for condition in CONDITIONS:
        per_condition[condition] = compute_condition_metrics(
            inputs.records, inputs, protocol, condition
        )

    overall_scorable = sum(m["scorable_sample_count"] for m in per_condition.values())
    overall_correct = sum(m["correct_count"] for m in per_condition.values())
    overall_logical = sum(m["logical_sample_count"] for m in per_condition.values())
    overall_accuracy_e2e = (overall_correct / overall_scorable) if overall_scorable > 0 else None

    overall_valid_scorable = sum(m["valid_scorable_sample_count"] for m in per_condition.values())
    overall_accuracy_valid = (
        (overall_correct / overall_valid_scorable) if overall_valid_scorable > 0 else None
    )

    overall_completed = sum(m["completed_record_count"] for m in per_condition.values())
    overall_invalid_id_count = sum(m["invalid_id_count"] for m in per_condition.values())
    overall_invalid_id_rate = (
        (overall_invalid_id_count / overall_completed) if overall_completed > 0 else None
    )

    overall_invalid_syntax_count = sum(m["invalid_syntax_count"] for m in per_condition.values())
    overall_invalid_syntax_rate = (
        (overall_invalid_syntax_count / overall_completed) if overall_completed > 0 else None
    )

    overall_unknown_id_count = sum(m["unknown_id_count"] for m in per_condition.values())
    overall_unknown_id_rate = (
        (overall_unknown_id_count / overall_completed) if overall_completed > 0 else None
    )

    overall_retired_id_count = sum(
        m["retired_id_observation_count"] for m in per_condition.values()
    )
    overall_retired_id_rate = (
        (overall_retired_id_count / overall_completed) if overall_completed > 0 else None
    )

    overall_provider_failure_count = sum(
        m["provider_failure_count"] for m in per_condition.values()
    )
    overall_provider_failure_rate = (
        (overall_provider_failure_count / overall_logical) if overall_logical > 0 else None
    )

    overall_parse_failure_count = sum(m["parse_failure_count"] for m in per_condition.values())
    overall_parse_failure_rate = (
        (overall_parse_failure_count / overall_logical) if overall_logical > 0 else None
    )

    valid_f1s = [m["macro_f1"] for m in per_condition.values() if m["macro_f1"] is not None]
    overall_macro_f1 = (sum(valid_f1s) / len(valid_f1s)) if valid_f1s else None

    overall_metrics = {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "logical_sample_count": overall_logical,
        "scorable_sample_count": overall_scorable,
        "valid_scorable_sample_count": overall_valid_scorable,
        "completed_record_count": overall_completed,
        "coverage": (overall_scorable / overall_logical) if overall_logical > 0 else None,
        "correct_count": overall_correct,
        "accuracy_end_to_end": overall_accuracy_e2e,
        "accuracy_valid_outputs": overall_accuracy_valid,
        "macro_f1": overall_macro_f1,
        "invalid_id_count": overall_invalid_id_count,
        "invalid_id_rate": overall_invalid_id_rate,
        "invalid_syntax_count": overall_invalid_syntax_count,
        "invalid_syntax_rate": overall_invalid_syntax_rate,
        "unknown_id_count": overall_unknown_id_count,
        "unknown_id_rate": overall_unknown_id_rate,
        "retired_id_observation_count": overall_retired_id_count,
        "retired_id_rate": overall_retired_id_rate,
        "provider_failure_count": overall_provider_failure_count,
        "provider_failure_rate": overall_provider_failure_rate,
        "parse_failure_count": overall_parse_failure_count,
        "parse_failure_rate": overall_parse_failure_rate,
        "total_conditions": len(CONDITIONS),
        "by_condition_summary": {
            c: {
                "accuracy_end_to_end": per_condition[c]["accuracy_end_to_end"],
                "accuracy_valid_outputs": per_condition[c]["accuracy_valid_outputs"],
                "macro_f1": per_condition[c]["macro_f1"],
                "invalid_id_rate": per_condition[c]["invalid_id_rate"],
                "provider_failure_rate": per_condition[c]["provider_failure_rate"],
                "parse_failure_rate": per_condition[c]["parse_failure_rate"],
            }
            for c in CONDITIONS
        },
    }

    per_condition_metrics = {
        "schema_version": "1.0.0",
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "conditions": per_condition,
    }

    retrieval_cond = compute_retrieval_conditional_metrics(inputs, protocol)
    failure_decomp = compute_failure_decomposition(inputs, protocol)
    technique_metrics = compute_technique_metrics(inputs, protocol)
    run_provenance = compute_run_provenance(inputs, protocol)

    result = {
        "overall": overall_metrics,
        "per_condition": per_condition_metrics,
        "per_technique": technique_metrics,
        "retrieval_conditional": retrieval_cond,
        "failure_decomposition": failure_decomp,
        "run_provenance": run_provenance,
    }

    if output_dir is not None:
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)
        _atomic_write_json(out_path / "overall_metrics.json", overall_metrics)
        _atomic_write_json(out_path / "per_condition_metrics.json", per_condition_metrics)
        _atomic_write_json(out_path / "per_technique_metrics.json", technique_metrics)
        _atomic_write_json(out_path / "retrieval_conditional_metrics.json", retrieval_cond)
        _atomic_write_json(out_path / "failure_decomposition.json", failure_decomp)
        _atomic_write_json(out_path / "run_provenance.json", run_provenance)

    return result


def validate_evaluator_compatibility(
    protocol: ScientificProtocolApproval,
    plan: Any,
) -> dict[str, Any]:
    """Validate that plan configuration and artifacts strictly meet evaluator requirements.

    Validates D1-D7 evaluator contract compliance (D1, D2a-D2j, D3, artifacts).
    Fails closed on protocol mismatch, missing artifacts, or schema incompatibility.
    """
    if not isinstance(protocol, ScientificProtocolApproval):
        raise TypeError(f"Expected ScientificProtocolApproval, got {type(protocol).__name__}")
    validate_scientific_protocol(protocol, plan)

    if plan is None:
        raise ValueError("Plan is required for evaluator compatibility validation")

    # Validate condition matrix
    if tuple(plan.config.conditions) != CONDITIONS:
        raise ValueError(
            f"Plan conditions {plan.config.conditions} do not match evaluator matrix {CONDITIONS}"
        )

    # Validate raw response policy compatibility (D1)
    if protocol.d1_raw_response_policy == "RECORD_ONLY":
        if not getattr(plan.config.logging, "raw_response", False):
            raise ValueError(
                "Evaluator protocol specifies RECORD_ONLY but plan logging.raw_response is False"
            )
    elif protocol.d1_raw_response_policy == "LOG_SEPARATELY":
        raise ValueError("LOG_SEPARATELY raw-response storage is not implemented")

    # Validate ATT&CK release (D2g)
    attack_release = getattr(plan.config.attack, "release", None) or plan.manifest.get(
        "attack_release"
    )
    if attack_release != "19.2":
        raise ValueError(f"Evaluator requires ATT&CK release 19.2, got '{attack_release}'")

    # Validate required artifacts are present in plan
    plan_artifacts = getattr(plan, "artifacts", None)
    if plan_artifacts is None and hasattr(plan, "manifest"):
        plan_artifacts = plan.manifest.get("artifacts", {})
    if not plan_artifacts:
        plan_artifacts = {}
    required_evaluator_artifacts = {
        "inference",
        "ground_truth",
        "prompt",
        "model_config",
        "retrieval_config",
        "corpus",
        "index",
    }
    missing = required_evaluator_artifacts - set(plan_artifacts.keys())
    if missing:
        raise ValueError(f"Plan missing artifacts required by evaluator: {sorted(missing)}")

    # Validate technique universe if corpus snapshot is available (D2d)
    if hasattr(plan, "snapshots") and "corpus" in plan.snapshots:
        if protocol.d2d_macro_f1_universe == "FROZEN_BENCHMARK_UNIVERSE":
            try:
                corpus_bytes = plan.snapshots["corpus"]
                if not isinstance(corpus_bytes, (bytes, bytearray)):
                    raise ValueError(
                        f"Corpus snapshot must be bytes, got {type(corpus_bytes).__name__}"
                    )
                corpus_lines = corpus_bytes.decode("utf-8").strip().splitlines()
                corpus_tids: set[str] = set()
                for line_idx, line in enumerate(corpus_lines):
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if not isinstance(row, dict) or "technique_id" not in row:
                        raise ValueError(f"Corpus snapshot line {line_idx} missing 'technique_id'")
                    corpus_tids.add(row["technique_id"])
                if len(corpus_tids) != 474:
                    raise ValueError(
                        f"Corpus technique count ({len(corpus_tids)}) differs from universe of 474"
                    )
            except Exception as exc:
                if isinstance(exc, ValueError):
                    raise
                raise ValueError(
                    f"Corpus snapshot invalid for frozen benchmark universe: {exc}"
                ) from exc

    return {
        "status": "VALID",
        "d1_raw_response_policy": protocol.d1_raw_response_policy,
        "d2a_ground_truth_semantics": protocol.d2a_ground_truth_semantics,
        "d2b_empty_ground_truth": protocol.d2b_empty_ground_truth,
        "d2c_ambiguous_ground_truth": protocol.d2c_ambiguous_ground_truth,
        "d2d_macro_f1_universe": protocol.d2d_macro_f1_universe,
        "d2e_invalid_id_denominator": protocol.d2e_invalid_id_denominator,
        "d2f_api_error_denominator": protocol.d2f_api_error_denominator,
        "d2g_retired_attack_id": protocol.d2g_retired_attack_id,
        "d2h_conditional_retrieval": protocol.d2h_conditional_retrieval,
        "d2i_failure_precedence": protocol.d2i_failure_precedence,
        "d2j_zero_denominator": protocol.d2j_zero_denominator,
        "d3_model_version_policy": protocol.d3_model_version_policy,
        "artifacts_verified": sorted(required_evaluator_artifacts),
    }
