"""Independent, fail-closed prepare/validate/freeze/verify synthetic stages."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

from src.artifacts import validate_attack_manifest_artifact
from src.attack_loader import EXPECTED_ATTACK_SHA256, ATTACK_VERSION, EXPECTED_ATTACK_SIZE
from src.synthetic import serialize_dataset, load_dataset, get_inference_payload, _sha256_file
from src.synthetic_generator import generate_dataset, SEED, GENERATOR_VERSION
from src.synthetic_stage_b_validation import validate_stage_b
from src.synthetic_validator import validate_template_registry

SOURCE_ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = ["src/synthetic.py", "src/synthetic_validator.py", "src/synthetic_generator.py",
                "src/synthetic_recipes.py", "src/synthetic_predicates.py",
                "src/synthetic_stage_b_validation.py", "src/synthetic_pipeline.py"]
SEMANTIC_FILES = {"events.jsonl", "views.jsonl", "pairs.jsonl", "ground_truth.jsonl", "inference.jsonl", "split_manifest.json"}
REPORT_FILES = {"validation_report.json", "statistics.json", "leakage_audit.json", "duplicate_audit.json"}
FROZEN_FILES = SEMANTIC_FILES | REPORT_FILES | {"generation_metadata.json", "manual_spotcheck.md", "manual_review.json"}


def canonical(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition, message):
    if not condition: raise ValueError(message)


def prerequisites(workspace):
    ws = Path(workspace).resolve()
    registry_path = ws / "config/synthetic_templates.json"
    registry_hash = _sha256_file(registry_path)
    approval = read_json(ws / "config/synthetic_approval.json")
    require(approval.get("approved") is True, "Registry requires explicit semantic approval")
    require(approval.get("registry_sha256") == registry_hash, "Approved registry SHA-256 mismatch")
    require(approval.get("config_sha256") == _sha256_file(ws / "config/data_ground_truth.json"), "Frozen methodology config SHA-256 mismatch")
    manifest = validate_attack_manifest_artifact(ws)
    stix = ws / manifest["stix_file"]["path"]
    require(_sha256_file(stix) == EXPECTED_ATTACK_SHA256 and stix.stat().st_size == EXPECTED_ATTACK_SIZE, "Pinned ATT&CK reference mismatch")
    registry = read_json(registry_path)
    result = validate_template_registry(registry, stix)
    require(result.passed, "Registry validation failed: " + "; ".join(result.errors))
    return registry, registry_path, registry_hash, stix


def generation_metadata(ws, registry_hash):
    hashes = {p: _sha256_file(SOURCE_ROOT / p) for p in SOURCE_FILES}
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", *SOURCE_FILES],
                            cwd=SOURCE_ROOT, capture_output=True, text=True, check=True).stdout.strip()
    return {"schema_version": "1.0.0", "benchmark_version": "synthetic-paired-v1",
            "generator_version": GENERATOR_VERSION, "generator_commit": commit or None,
            "generator_source_sha256": hashes, "seed": SEED, "attack_version": ATTACK_VERSION,
            "attack_source_sha256": EXPECTED_ATTACK_SHA256, "registry_sha256": registry_hash,
            "config_sha256": _sha256_file(ws / "config/data_ground_truth.json"),
            "approval_sha256": _sha256_file(ws / "config/synthetic_approval.json")}


def default_candidate(ws):
    return Path(ws) / ".tmp/synthetic_candidate"


def default_frozen(ws):
    return Path(ws) / "data/ground_truth/synthetic"


def select_spotcheck(pairs):
    # One per family, plus enough DEV negatives to reach four per negative class.
    chosen = {}
    for pair in sorted(pairs, key=lambda p: p.pair_id):
        chosen.setdefault(pair.template_family_id, pair)
    selected = {p.pair_id: p for p in chosen.values()}
    for status in ["unmapped", "ambiguous"]:
        for split in ["dev", "test"]:
            subset = sorted([p for p in pairs if p.split == split and p.contextual_ground_truth.label_status == status], key=lambda p: p.pair_id)
            for pair in subset[:2]: selected[pair.pair_id] = pair
    return sorted(selected.values(), key=lambda p: (p.template_family_id, p.pair_id))


def spotcheck_bytes(pairs):
    lines = ["# Deterministic synthetic manual spot-check", "",
             "Selection: one pair per family and at least two DEV and two TEST pairs per negative class.",
             "This generated package is not a claim of completed manual review.", ""]
    for pair in select_spotcheck(pairs):
        lines += [f"## {pair.pair_id}", f"Family: {pair.template_family_id}; split: {pair.split}",
                  f"Transition: {pair.single_ground_truth.label_status} -> {pair.contextual_ground_truth.label_status}"]
        for kind in ["single", "contextual"]:
            view, gt = getattr(pair, kind + "_view"), getattr(pair, kind + "_ground_truth")
            events = [pair.events[eid] for eid in view.event_ids]
            for title, value in [("raw telemetry", [asdict(e) for e in events]),
                                 ("inference payload", [get_inference_payload(e) for e in events]),
                                 ("ground truth and evidence references", asdict(gt))]:
                lines += [f"### {kind}: {title}", "```json", json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True), "```", ""]
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _hashes(directory, filenames):
    return {name: _sha256_file(directory / name) for name in sorted(filenames)}


def _check_artifacts(directory, required):
    manifest = read_json(directory / "dataset_manifest.json")
    files = manifest.get("files", {})
    require(set(files) == required, "Artifact manifest file set mismatch")
    for name in sorted(required):
        require((directory / name).is_file(), f"Missing artifact: {name}")
        require(_sha256_file(directory / name) == files[name], f"Artifact SHA-256 mismatch: {name}")
    return manifest


def _reports(result):
    duplicates = result.statistics.get("near_duplicates", [])
    return {
        "validation_report.json": {"passed": result.passed, "errors": sorted(result.errors), "warnings": sorted(result.warnings)},
        "statistics.json": result.statistics,
        "leakage_audit.json": {"passed": not any("leak" in e.lower() for e in result.errors),
                               "findings": sorted(e for e in result.errors if "leak" in e.lower()),
                               "audited_views": result.statistics.get("views", 0),
                               "audited_unique_events": result.statistics.get("total_unique_events", 0),
                               "input_policy": "get_inference_payload allowlist"},
        "duplicate_audit.json": {"passed": not duplicates, "threshold": 0.95, "character_ngram_size": 5,
                                 "unacceptable_duplicates": duplicates, "exceptions": []},
    }


def _validate_loaded(ws, directory, registry, registry_path, registry_hash, stix):
    pairs = load_dataset(directory)
    result = validate_stage_b(pairs, directory, stix, registry, registry_path, registry_hash)
    # Sidecars must agree with pairs, not merely carry self-consistent SHA values.
    with tempfile.TemporaryDirectory(prefix="synthetic-sidecars-", dir=ws / ".tmp") as temp:
        expected = serialize_dataset(pairs, Path(temp))
        for name, expected_hash in expected.items():
            if not (directory / name).exists() or _sha256_file(directory / name) != expected_hash:
                result.add_error(f"Canonical sidecar content mismatch: {name}")
    return pairs, result


def prepare_synthetic(workspace, output_dir=None):
    ws = Path(workspace).resolve()
    registry, registry_path, registry_hash, stix = prerequisites(ws)
    output = Path(output_dir) if output_dir is not None else default_candidate(ws)
    require(not output.exists() or not any(output.iterdir()), "Candidate output must be empty; preserve or remove the prior candidate explicitly")
    pairs = generate_dataset(registry, registry_hash)
    hashes = serialize_dataset(pairs, output)
    metadata = generation_metadata(ws, registry_hash)
    write_json(output / "generation_metadata.json", metadata)
    hashes["generation_metadata.json"] = _sha256_file(output / "generation_metadata.json")
    write_json(output / "dataset_manifest.json", {**metadata, "state": "candidate", "files": hashes})
    audit = ws / "data/audit/synthetic_manual_spotcheck.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_bytes(spotcheck_bytes(pairs))
    return {"passed": True, "pairs": len(pairs), "views": 2 * len(pairs), "registry_sha256": registry_hash}


def validate_synthetic(workspace, candidate_dir=None):
    ws = Path(workspace).resolve()
    registry, registry_path, registry_hash, stix = prerequisites(ws)
    directory = Path(candidate_dir) if candidate_dir else default_candidate(ws)
    manifest = read_json(directory / "dataset_manifest.json")
    required = SEMANTIC_FILES | {"generation_metadata.json"}
    if manifest.get("state") == "validated": required |= REPORT_FILES
    require(manifest.get("state") in {"candidate", "validated"}, "Expected candidate/validated manifest")
    _check_artifacts(directory, required)
    require(read_json(directory / "generation_metadata.json") == generation_metadata(ws, registry_hash), "Generation provenance differs from current approved inputs/code")
    (ws / ".tmp").mkdir(exist_ok=True)
    pairs, result = _validate_loaded(ws, directory, registry, registry_path, registry_hash, stix)
    for name, data in _reports(result).items(): write_json(directory / name, data)
    require(result.passed, "Dataset validation failed: " + "; ".join(result.errors))
    require(not result.warnings, "Unresolved dataset validation warnings")
    manifest.update(state="validated", pair_count=len(pairs), view_count=2 * len(pairs),
                    split_counts={s: sum(p.split == s for p in pairs) for s in ["dev", "test"]},
                    files=_hashes(directory, required | REPORT_FILES))
    write_json(directory / "dataset_manifest.json", manifest)
    return {"passed": True, "errors": 0, "statistics": result.statistics}


def _manual_review(pairs, package, review, registry_hash, semantic_hashes):
    require(package == spotcheck_bytes(pairs), "Manual spot-check package content mismatch")
    require(review.get("package_sha256") == hashlib.sha256(package).hexdigest(), "Manual review package hash mismatch")
    require(review.get("registry_sha256") == registry_hash, "Manual review registry hash mismatch")
    require(review.get("semantic_artifact_sha256") == semantic_hashes, "Manual review dataset hash mismatch")
    require(review.get("reviewer") and review.get("review_method") == "agent_inspected_raw_inference_ground_truth", "Manual inspection record is required")
    expected = {p.pair_id for p in select_spotcheck(pairs)}
    cases = review.get("cases", {})
    require(set(cases) == expected, "Manual review does not cover deterministic sample")
    require(all(c.get("status") == "PASS" and c.get("notes") for c in cases.values()), "Unresolved manual semantic finding")
    require(review.get("unresolved_findings") == [], "Manual semantic findings remain unresolved")


def freeze_synthetic(workspace, candidate_dir=None, output_dir=None):
    ws = Path(workspace).resolve()
    candidate = Path(candidate_dir) if candidate_dir else default_candidate(ws)
    require(read_json(candidate / "dataset_manifest.json").get("state") == "validated", "Run validate-synthetic before freezing")
    validate_synthetic(ws, candidate)  # Never trust a stale PASS report.
    pairs = load_dataset(candidate)
    metadata = read_json(candidate / "generation_metadata.json")
    package = (ws / "data/audit/synthetic_manual_spotcheck.md").read_bytes()
    review = read_json(ws / "data/audit/synthetic_manual_review.json")
    semantic_hashes = _hashes(candidate, SEMANTIC_FILES)
    _manual_review(pairs, package, review, metadata["registry_sha256"], semantic_hashes)
    output = Path(output_dir) if output_dir else default_frozen(ws)
    (ws / ".tmp").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="synthetic-freeze-", dir=ws / ".tmp") as temp:
        stage = Path(temp)
        for name in SEMANTIC_FILES | REPORT_FILES | {"generation_metadata.json"}:
            shutil.copyfile(candidate / name, stage / name)
        (stage / "manual_spotcheck.md").write_bytes(package)
        write_json(stage / "manual_review.json", review)
        manifest = {**metadata, "state": "frozen", "pair_count": len(pairs), "view_count": len(pairs) * 2,
                    "split_counts": {s: sum(p.split == s for p in pairs) for s in ["dev", "test"]},
                    "files": _hashes(stage, FROZEN_FILES)}
        write_json(stage / "dataset_manifest.json", manifest)
        if output.exists() and any(output.iterdir()):
            require(set(p.name for p in output.iterdir()) == FROZEN_FILES | {"dataset_manifest.json"}, "Existing frozen directory has unexpected content")
            require(all((output / p.name).read_bytes() == p.read_bytes() for p in stage.iterdir()), "Refusing to overwrite a different frozen benchmark")
        else:
            output.mkdir(parents=True, exist_ok=True)
            for p in sorted(stage.iterdir(), key=lambda p: (p.name == "dataset_manifest.json", p.name)):
                shutil.copyfile(p, output / p.name)
    return {"passed": True, "state": "frozen", "files": manifest["files"]}


def verify_synthetic(workspace, input_dir=None):
    ws = Path(workspace).resolve()
    registry, registry_path, registry_hash, stix = prerequisites(ws)
    directory = Path(input_dir) if input_dir else default_frozen(ws)
    manifest = _check_artifacts(directory, FROZEN_FILES)
    require(manifest.get("state") == "frozen", "Dataset is not frozen")
    metadata = generation_metadata(ws, registry_hash)
    require(read_json(directory / "generation_metadata.json") == metadata, "Frozen generation provenance mismatch")
    require(all(manifest.get(k) == value for k, value in metadata.items()), "Frozen manifest provenance mismatch")
    (ws / ".tmp").mkdir(exist_ok=True)
    pairs, result = _validate_loaded(ws, directory, registry, registry_path, registry_hash, stix)
    require(result.passed and not result.warnings, "Frozen validation failed: " + "; ".join(result.errors + result.warnings))
    require(manifest.get("pair_count") == len(pairs) and manifest.get("view_count") == len(pairs) * 2, "Manifest counts mismatch")
    require(manifest.get("split_counts") == {s: sum(p.split == s for p in pairs) for s in ["dev", "test"]}, "Manifest split counts mismatch")
    for name, data in _reports(result).items():
        require((directory / name).read_bytes() == canonical(data), f"Audit report content mismatch: {name}")
    _manual_review(pairs, (directory / "manual_spotcheck.md").read_bytes(), read_json(directory / "manual_review.json"), registry_hash, _hashes(directory, SEMANTIC_FILES))
    # Recreate semantic outputs from registry+seed, independent of saved pairs.
    with tempfile.TemporaryDirectory(prefix="synthetic-reproduction-", dir=ws / ".tmp") as temp:
        reproduced = serialize_dataset(generate_dataset(registry, registry_hash), Path(temp))
        require(reproduced == _hashes(directory, SEMANTIC_FILES), "Same-seed reproduction hash mismatch")
    return {"passed": True, "pairs": len(pairs), "views": len(pairs) * 2, "artifact_hash_mismatches": 0,
            "reproducibility_hash_mismatches": 0, "run_a_sha256": _hashes(directory, SEMANTIC_FILES), "run_b_sha256": reproduced}
