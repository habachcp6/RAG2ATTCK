"""Read-only byte-bound preflight. No provider, pipeline or embedder construction."""

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.experiment.schemas import CONDITIONS, Artifact, ExperimentConfig
from src.llm.inputs import validate_benchmark_batch
from src.llm.schemas import TechniquePrediction


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data: bytes):
    def invalid_constant(value):
        raise ValueError(f"non-finite JSON number: {value}")

    return json.loads(data, object_pairs_hook=_object, parse_constant=invalid_constant)


def parse_jsonl(data: bytes):
    if not data or not data.endswith(b"\n"):
        raise ValueError("JSONL must be nonempty and end with a complete newline")
    rows = []
    for line in data.splitlines():
        if not line.strip():
            raise ValueError("blank JSONL row")
        row = parse_json(line)
        if not isinstance(row, dict):
            raise TypeError("JSONL row must be an object")
        rows.append(row)
    return rows


def _index(rows, field):
    result = {}
    for row in rows:
        key = row.get(field)
        if not isinstance(key, str) or not key.strip() or key != key.strip() or key in result:
            raise ValueError(f"missing/invalid/duplicate {field}")
        result[key] = row
    return result


@dataclass(frozen=True)
class Sample:
    sample_id: str
    pair_id: str
    view_type: str
    endpoint_evidence: str


@dataclass(frozen=True)
class ValidatedPlan:
    root: Path
    config: ExperimentConfig
    samples: tuple[Sample, ...]
    manifest: dict
    manifest_sha256: str
    prompt_template: str
    model_config: dict
    registry_ids: frozenset[str]
    snapshots: dict[str, bytes]

    def report(self):
        return {
            "schema_version": "1.0.0",
            "status": "HUMAN_DECISION_REQUIRED",
            "infrastructure_validation": "PASS",
            "scientific_status": "NOT_FROZEN",
            "experiment_id": self.manifest["experiment_id"],
            "sample_count": len(self.samples),
            "condition_count": len(CONDITIONS),
            "expected_request_count": self.manifest["expected_request_count"],
            "maximum_attempts": self.manifest["maximum_attempts"],
            "maximum_output_tokens": self.manifest["maximum_attempts"]
            * self.config.generation.max_output_tokens,
            "monetary_budget": None,
            "monetary_budget_reason": (
                "No approved provider prices or input-token ceiling; no cost claim is made."
            ),
            "max_requests": self.config.execution.max_requests,
            "manifest_sha256": self.manifest_sha256,
            "human_decisions": self.manifest["human_decisions"],
            "provider_calls": 0,
            "prediction_writes": 0,
        }


def _references(config):
    return {
        "inference": config.dataset.inference,
        "ground_truth": config.dataset.ground_truth,
        "dataset_manifest": config.dataset.manifest,
        "views": config.dataset.views,
        "pairs": config.dataset.pairs,
        "split_manifest": config.dataset.split_manifest,
        "prompt": config.prompt.template,
        "model_config": config.generation.config,
        "retrieval_config": config.retrieval.config,
        "corpus": config.attack.corpus,
        "index": config.attack.index,
        "document_mapping": config.attack.document_mapping,
        "retrieval_manifest": config.attack.retrieval_manifest,
        "attack_registry": config.attack.registry,
    }


def _resolve(root: Path, path: str) -> Path:
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else root / candidate).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"artifact path escapes the experiment repository: {path}")
    return resolved


def _read_bound(root: Path, reference: Artifact) -> bytes:
    path = _resolve(root, reference.path)
    data = path.read_bytes()
    if digest(data) != reference.sha256:
        raise ValueError(f"SHA256 mismatch: {reference.path}")
    return data


def registry_ids_from_bytes(data: bytes) -> frozenset[str]:
    """Match the existing registry loader's technique extraction without rereads."""
    bundle = parse_json(data)
    registry = frozenset(
        ref["external_id"]
        for obj in bundle["objects"]
        if obj.get("type") == "attack-pattern"
        for ref in obj.get("external_references", [])
        if ref.get("source_name") == "mitre-attack" and "external_id" in ref
    )
    if not registry:
        raise ValueError("empty ATT&CK registry")
    return registry


def _validate_dataset(config, snapshots):
    manifest = parse_json(snapshots["dataset_manifest"])
    if (
        manifest.get("state"),
        manifest.get("benchmark_version"),
        manifest.get("attack_version"),
    ) != ("frozen", config.dataset.benchmark, config.attack.release):
        raise ValueError("dataset manifest is not the frozen configured benchmark/release")
    for name in ("inference", "ground_truth", "views", "pairs", "split_manifest"):
        ref = _references(config)[name]
        if manifest["files"].get(Path(ref.path).name) != digest(snapshots[name]):
            raise ValueError(f"dataset manifest binding mismatch: {name}")
    if manifest.get("attack_source_sha256") != digest(snapshots["attack_registry"]):
        raise ValueError("ATT&CK registry does not match frozen dataset source")

    inference = _index(parse_jsonl(snapshots["inference"]), "sample_id")
    for row in inference.values():
        if set(row) != {"sample_id", "endpoint_evidence"}:
            raise ValueError("inference rows must contain only sample_id and endpoint_evidence")
    validate_benchmark_batch(inference.values())
    views = _index(parse_jsonl(snapshots["views"]), "view_id")
    truth = _index(parse_jsonl(snapshots["ground_truth"]), "view_id")
    pairs = _index(parse_jsonl(snapshots["pairs"]), "pair_id")
    if set(inference) != set(views) or set(inference) != set(truth):
        raise ValueError("inference/view/GT sample coverage mismatch")
    if len(inference) != manifest["view_count"] or len(pairs) != manifest["pair_count"]:
        raise ValueError("dataset manifest sample count mismatch")
    split = parse_json(snapshots["split_manifest"])
    if set(split) != {"dev", "test"}:
        raise ValueError("split manifest must contain dev and test")
    all_pairs = split["dev"] + split["test"]
    if len(all_pairs) != len(set(all_pairs)) or set(all_pairs) != set(pairs):
        raise ValueError("duplicate, overlapping or missing split pairs")
    for name in ("dev", "test"):
        if len(split[name]) != manifest["split_counts"][name]:
            raise ValueError("split manifest count mismatch")
    view_keys = set()
    for pair_id, pair in pairs.items():
        expected_split = "test" if pair_id in split["test"] else "dev"
        if pair.get("split") != expected_split:
            raise ValueError("pair/split mismatch")
        for view_type in ("single", "contextual"):
            view = pair[f"{view_type}_view"]
            view_id = view["view_id"]
            if view_id in view_keys or view_id not in views or view != views[view_id]:
                raise ValueError("pair/view identity mismatch")
            view_keys.add(view_id)
            if view["pair_id"] != pair_id or view["view_type"] != view_type:
                raise ValueError("invalid pair/view metadata")
            if pair[f"{view_type}_ground_truth"] != truth[view_id]:
                raise ValueError("pair/GT binding mismatch")
    if view_keys != set(views):
        raise ValueError("orphan view")
    selected_pairs = set(split[config.dataset.split])
    selected = tuple(
        Sample(
            sample_id,
            views[sample_id]["pair_id"],
            views[sample_id]["view_type"],
            inference[sample_id]["endpoint_evidence"],
        )
        for sample_id in sorted(inference)
        if views[sample_id]["pair_id"] in selected_pairs
    )
    if (
        len(selected) != config.dataset.expected_sample_count
        or len(selected_pairs) != config.dataset.expected_pair_count
    ):
        raise ValueError("selected sample/pair count mismatch")
    if len(selected) != 2 * len(selected_pairs):
        raise ValueError("each selected pair must have exactly two views")
    return selected


def _validate_retrieval(root, config, snapshots):
    import faiss
    import numpy as np

    retrieval = parse_json(snapshots["retrieval_config"])
    manifest = parse_json(snapshots["retrieval_manifest"])
    expected = {
        "embedding_model_id": config.retrieval.embedding_model,
        "embedding_model_revision": config.retrieval.embedding_revision,
        "embedding_dimension": config.retrieval.embedding_dimension,
        "faiss_index_type": config.retrieval.index_type,
        "normalization": config.retrieval.normalization,
        "similarity_metric": config.retrieval.metric,
        "corpus_sha256": config.attack.corpus.sha256,
    }
    for field, value in expected.items():
        if retrieval.get(field) != value or manifest.get(field) != value:
            raise ValueError(f"retrieval config/manifest mismatch: {field}")
    if retrieval.get("supported_k") != list(config.retrieval.depths):
        raise ValueError("retrieval depth binding mismatch")
    if retrieval.get("faiss_version") != manifest.get("faiss_version"):
        raise ValueError("FAISS version binding mismatch")
    for field, name in (
        ("corpus_path", "corpus"),
        ("faiss_index_path", "index"),
        ("document_mapping_path", "document_mapping"),
        ("manifest_path", "retrieval_manifest"),
    ):
        retrieval_path = _resolve(root, retrieval[field])
        if retrieval_path != _resolve(root, _references(config)[name].path):
            raise ValueError(f"retrieval path binding mismatch: {field}")
    for field, name in (("index_sha256", "index"), ("document_mapping_sha256", "document_mapping")):
        if manifest.get(field) != digest(snapshots[name]):
            raise ValueError(f"retrieval artifact hash binding mismatch: {name}")
    corpus = parse_jsonl(snapshots["corpus"])
    docmap = parse_json(snapshots["document_mapping"])
    if corpus != docmap:
        raise ValueError("document mapping differs from hashed corpus")
    _index(corpus, "technique_id")
    if any(doc.get("source_version") != config.attack.release for doc in corpus):
        raise ValueError("corpus ATT&CK release mismatch")
    # Deserialize the captured, hashed bytes; never reopen the index path.
    index = faiss.deserialize_index(np.frombuffer(snapshots["index"], dtype=np.uint8))
    if not isinstance(index, faiss.IndexFlatIP) or index.metric_type != faiss.METRIC_INNER_PRODUCT:
        raise ValueError("index must be IndexFlatIP/inner product")
    if (
        index.d != config.retrieval.embedding_dimension
        or index.ntotal != len(docmap)
        or len(docmap) != manifest["document_count"]
    ):
        raise ValueError("index dimension/document count mismatch")
    if len(docmap) < max(config.retrieval.depths):
        raise ValueError("corpus cannot satisfy configured retrieval depths")


def _validate_model(config, snapshot):
    model = parse_json(snapshot)
    expected = {
        "provider": config.generation.provider,
        "model": config.generation.model,
        "reasoning_effort": config.generation.reasoning_effort,
        "api_interface": config.generation.api_interface,
        "max_output_tokens": config.generation.max_output_tokens,
        "max_retries": config.execution.retries,
        "timeout_seconds": config.execution.timeout_seconds,
    }
    if any(model.get(key) != value for key, value in expected.items()):
        raise ValueError("generation settings do not inherit the bound canonical model config")
    if "temperature" in model or "seed" in model:
        raise ValueError("provider-default temperature/seed must remain omitted")
    if model.get("logging_policy", {}).get("log_raw_response") is not False:
        raise ValueError("raw response logging policy changed")
    expected_schema = {
        "format": "json_schema",
        "schema_name": "attack_technique_prediction",
        "strict": True,
        "target_field": "technique_id",
    }
    if model.get("structured_output") != expected_schema:
        raise ValueError("canonical single-ID output schema changed")
    return model


def _validate_output_location(path: Path):
    if path.exists() and not path.is_dir():
        raise ValueError("experiment output path is not a directory")
    parent = path
    while not parent.exists():
        parent = parent.parent
    if not parent.is_dir() or not os.access(parent, os.W_OK):
        raise ValueError("experiment output parent is not writable")


def load_plan(config_path: Path | str, *, root: Path | str | None = None) -> ValidatedPlan:
    """Validate captured artifact bytes and return a candidate; perform zero writes."""
    config_path = Path(config_path).resolve()
    root = (
        Path(root).resolve()
        if root is not None
        else (
            config_path.parent.parent if config_path.parent.name == "config" else config_path.parent
        )
    )
    config_bytes = config_path.read_bytes()
    config = ExperimentConfig.model_validate(parse_json(config_bytes))
    references = _references(config)
    snapshots = {name: _read_bound(root, ref) for name, ref in references.items()}
    if not config_path.is_relative_to(root):
        raise ValueError("experiment config must stay inside its artifact root")
    references["experiment_config"] = Artifact(
        path=config_path.relative_to(root).as_posix(), sha256=digest(config_bytes)
    )
    snapshots["experiment_config"] = config_bytes
    samples = _validate_dataset(config, snapshots)
    _validate_retrieval(root, config, snapshots)
    model = _validate_model(config, snapshots["model_config"])
    prompt = snapshots["prompt"].decode("utf-8")
    if any(
        prompt.count(placeholder) != 1
        for placeholder in ("{ENDPOINT_EVIDENCE}", "{RETRIEVED_CONTEXT}")
    ):
        raise ValueError("base prompt must have exactly one instance of each inference placeholder")
    registry = registry_ids_from_bytes(snapshots["attack_registry"])
    expected_requests = len(samples) * len(CONDITIONS)
    if (
        config.execution.max_requests is not None
        and config.execution.max_requests < expected_requests
    ):
        raise ValueError("expected request count exceeds explicit max_requests")
    experiment_id = f"{config.experiment.name}-{config.experiment.version}"
    if Path(experiment_id).name != experiment_id or any(c in experiment_id for c in "/\\:"):
        raise ValueError("experiment ID must be a safe directory name")
    _validate_output_location(root / "artifacts" / "experiments" / experiment_id)
    git = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    git_sha = git.stdout.strip()
    if len(git_sha) != 40:
        raise ValueError("invalid Git commit SHA")
    human = [
        "T15 external prerequisites and T21 dependency remain unresolved",
        "T20 human merge and exact-main CI closure required",
        "T21 scientific freeze and provider/API authorization required",
        "Canonical evaluator definitions require human decision",
    ]
    if config.generation.model_version is None:
        human.append("Exact provider model version requires human freeze")
    if config.execution.concurrency is None:
        human.append("Concurrency requires human freeze")
    if config.execution.max_requests is None:
        human.append("Explicit finite max_requests requires human approval")
    manifest = {
        "schema_version": "1.0.0",
        "execution_mode": "pre_freeze",
        "experiment_id": experiment_id,
        "status": "pre_freeze",
        "git_commit_sha": git_sha,
        "config_sha256": digest(config_bytes),
        "artifacts": {name: ref.model_dump() for name, ref in references.items()},
        "model": model,
        "model_version": config.generation.model_version,
        "output_schema_sha256": digest(canonical_bytes(TechniquePrediction.model_json_schema())),
        "attack_release": config.attack.release,
        "benchmark_version": config.dataset.benchmark,
        "split": config.dataset.split,
        "conditions": list(CONDITIONS),
        "retrieval": parse_json(snapshots["retrieval_config"]),
        "sample_ids": [sample.sample_id for sample in samples],
        "samples": [
            {"sample_id": s.sample_id, "pair_id": s.pair_id, "view_type": s.view_type}
            for s in samples
        ],
        "expected_request_count": expected_requests,
        "maximum_attempts": expected_requests * (config.execution.retries + 1),
        "execution": config.execution.model_dump(),
        "logging": config.logging.model_dump(),
        "human_decisions": human,
    }
    return ValidatedPlan(
        root,
        config,
        samples,
        manifest,
        digest(canonical_bytes(manifest)),
        prompt,
        model,
        registry,
        snapshots,
    )
