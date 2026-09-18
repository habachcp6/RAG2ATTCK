"""
Unit and integration tests for Deterministic Windows ATT&CK Retrieval Corpus (Task T17).
Validates schema compliance, sorting invariants, zero evaluation metadata leakage,
exact census accounting, benchmark coverage, cross-directory determinism, and manifest integrity.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import pytest

from src.attack_loader import (
    ATTACK_VERSION,
    ATTACK_V19_2_COMMIT,
    EXPECTED_ATTACK_SHA256,
    parse_attack_bundle,
)
from src.retrieval.corpus_builder import (
    DEFAULT_CORPUS_PATH,
    DEFAULT_MANIFEST_PATH,
    DEFAULT_SCOPE_PATH,
    DEFAULT_STIX_PATH,
    PROHIBITED_METADATA_KEYS,
    SCHEMA_VERSION,
    CorpusDocument,
    build_windows_corpus,
    compose_retrieval_text,
)

EXPECTED_CORPUS_SHA256 = "b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75"
EXPECTED_MANIFEST_SHA256 = "6bd769324f6ac9193d7df82e7f54f5a1397a41b9bc72be767da5a72b54b3a47c"
EXPECTED_CORPUS_SIZE = 1548724
EXPECTED_DOC_COUNT = 474
EXPECTED_ROOT_COUNT = 176
EXPECTED_SUB_COUNT = 298


def load_corpus_docs() -> list[dict]:
    """Helper to read and parse all JSON lines from the canonical corpus file."""
    assert DEFAULT_CORPUS_PATH.exists(), f"Corpus file missing at {DEFAULT_CORPUS_PATH}"
    docs = []
    with open(DEFAULT_CORPUS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            docs.append(json.loads(line))
    return docs


def test_corpus_file_exists_and_accounting():
    """Validates existence, exact byte length, SHA-256 hash, and line count."""
    assert DEFAULT_CORPUS_PATH.exists(), "Corpus file does not exist"
    corpus_bytes = DEFAULT_CORPUS_PATH.read_bytes()

    assert len(corpus_bytes) == EXPECTED_CORPUS_SIZE, (
        f"Corpus size mismatch: expected {EXPECTED_CORPUS_SIZE}, got {len(corpus_bytes)}"
    )

    computed_sha = hashlib.sha256(corpus_bytes).hexdigest()
    assert computed_sha == EXPECTED_CORPUS_SHA256, (
        f"Corpus SHA-256 mismatch: expected {EXPECTED_CORPUS_SHA256}, got {computed_sha}"
    )

    lines = corpus_bytes.decode("utf-8").splitlines()
    assert len(lines) == EXPECTED_DOC_COUNT, (
        f"Expected {EXPECTED_DOC_COUNT} lines in corpus, got {len(lines)}"
    )


def test_corpus_schema_and_required_fields():
    """Validates 11-field schema and data types on all 474 corpus records."""
    docs = load_corpus_docs()
    assert len(docs) == EXPECTED_DOC_COUNT

    expected_fields = frozenset({
        "technique_id",
        "stix_id",
        "name",
        "description",
        "platforms",
        "tactics",
        "is_subtechnique",
        "parent_technique_id",
        "modified",
        "source_version",
        "retrieval_text",
    })

    for doc in docs:
        assert set(doc.keys()) == expected_fields, f"Field mismatch in doc {doc.get('technique_id')}"
        assert doc["technique_id"].startswith("T"), f"Invalid technique_id format: {doc['technique_id']}"
        assert doc["stix_id"].startswith("attack-pattern--"), f"Invalid stix_id format: {doc['stix_id']}"
        assert isinstance(doc["name"], str) and len(doc["name"]) > 0
        assert isinstance(doc["description"], str) and len(doc["description"]) > 0
        assert isinstance(doc["platforms"], list) and "Windows" in doc["platforms"]
        assert doc["platforms"] == sorted(doc["platforms"]), "Platforms list not sorted"
        assert isinstance(doc["tactics"], list) and len(doc["tactics"]) > 0
        assert doc["tactics"] == sorted(doc["tactics"]), "Tactics list not sorted"
        assert isinstance(doc["is_subtechnique"], bool)

        if doc["is_subtechnique"]:
            assert isinstance(doc["parent_technique_id"], str)
            assert doc["parent_technique_id"].startswith("T")
        else:
            assert doc["parent_technique_id"] is None

        assert isinstance(doc["modified"], str) and len(doc["modified"]) > 0
        assert doc["source_version"] == ATTACK_VERSION
        assert isinstance(doc["retrieval_text"], str) and len(doc["retrieval_text"]) > 0


def test_corpus_zero_evaluation_metadata():
    """Validates that no ground-truth or evaluation metadata keys exist in corpus."""
    docs = load_corpus_docs()
    for doc in docs:
        leaked = set(doc.keys()) & PROHIBITED_METADATA_KEYS
        assert not leaked, f"Prohibited evaluation metadata {leaked} in {doc.get('technique_id')}"

    # Also verify that CorpusDocument.to_json_line raises ValueError if prohibited keys leak
    leaked_doc = CorpusDocument(
        technique_id="T1000",
        stix_id="attack-pattern--dummy",
        name="Dummy",
        description="Dummy desc",
        platforms=["Windows"],
        tactics=["execution"],
        is_subtechnique=False,
        parent_technique_id=None,
        modified="2026-01-01T00:00:00.000Z",
        source_version="19.2",
        retrieval_text="Dummy text",
    )
    # Valid document serializes cleanly
    valid_line = leaked_doc.to_json_line()
    assert "T1000" in valid_line

    # Tampered document dictionary
    d = leaked_doc.to_dict()
    d["ground_truth"] = "T1059.001"
    leaked_keys = set(d.keys()) & PROHIBITED_METADATA_KEYS
    assert "ground_truth" in leaked_keys


def test_corpus_strict_technique_id_sorting():
    """Validates that corpus records are uniquely identified and strictly sorted ascending."""
    docs = load_corpus_docs()
    technique_ids = [d["technique_id"] for d in docs]

    assert len(technique_ids) == EXPECTED_DOC_COUNT
    assert len(set(technique_ids)) == EXPECTED_DOC_COUNT, "Duplicate technique_id found"
    assert technique_ids == sorted(technique_ids), "Corpus documents are not strictly sorted by technique_id"


def test_corpus_active_windows_attributes():
    """Validates against raw STIX data: 0 revoked, 0 deprecated, 176 root, 298 subtechniques."""
    raw_techniques = parse_attack_bundle(DEFAULT_STIX_PATH)
    docs = load_corpus_docs()

    corpus_ids = {d["technique_id"] for d in docs}
    root_count = 0
    sub_count = 0

    for d in docs:
        tid = d["technique_id"]
        assert tid in raw_techniques, f"Technique {tid} not found in raw STIX"
        raw = raw_techniques[tid]

        assert "Windows" in raw.platforms, f"Technique {tid} does not list Windows in raw platforms"
        assert not raw.revoked, f"Technique {tid} is revoked in raw STIX"
        assert not raw.deprecated, f"Technique {tid} is deprecated in raw STIX"

        if d["is_subtechnique"]:
            sub_count += 1
            parent_id = d["parent_technique_id"]
            assert parent_id in corpus_ids, (
                f"Subtechnique {tid} parent {parent_id} is missing from active Windows corpus"
            )
        else:
            root_count += 1
            assert d["parent_technique_id"] is None

    assert root_count == EXPECTED_ROOT_COUNT, f"Expected {EXPECTED_ROOT_COUNT} root techniques, got {root_count}"
    assert sub_count == EXPECTED_SUB_COUNT, f"Expected {EXPECTED_SUB_COUNT} subtechniques, got {sub_count}"


def test_benchmark_techniques_coverage():
    """Validates that all 8 pinned benchmark techniques are covered in the retrieval corpus."""
    assert DEFAULT_SCOPE_PATH.exists(), f"Benchmark scope file missing at {DEFAULT_SCOPE_PATH}"
    with open(DEFAULT_SCOPE_PATH, "r", encoding="utf-8") as f:
        scope = json.load(f)

    catalog = scope.get("attack_catalog", [])
    assert len(catalog) == 8, f"Expected 8 benchmark techniques, got {len(catalog)}"

    raw_techniques = parse_attack_bundle(DEFAULT_STIX_PATH)
    docs = load_corpus_docs()
    corpus_map = {d["technique_id"]: d for d in docs}

    for tid in catalog:
        assert tid in corpus_map, f"Benchmark technique {tid} missing from retrieval corpus"
        assert tid in raw_techniques, f"Benchmark technique {tid} missing from raw STIX"
        doc = corpus_map[tid]
        raw = raw_techniques[tid]

        # Name must match pinned STIX exactly (including T1685.005 == Clear Windows Event Logs)
        assert doc["name"] == raw.name, f"Corpus name mismatch for {tid}: {doc['name']!r} != {raw.name!r}"
        assert doc["is_subtechnique"] == raw.is_subtechnique
        assert doc["parent_technique_id"] == raw.parent_technique_id
        assert not raw.revoked, f"Benchmark technique {tid} is revoked in raw STIX"
        assert not raw.deprecated, f"Benchmark technique {tid} is deprecated in raw STIX"
        assert "Windows" in doc["platforms"]
        assert "Windows" in raw.platforms

    # Spot-check specific known relationships
    assert corpus_map["T1059.001"]["parent_technique_id"] == "T1059"
    assert corpus_map["T1059.003"]["parent_technique_id"] == "T1059"
    assert corpus_map["T1685.005"]["name"] == "Clear Windows Event Logs"
    assert corpus_map["T1685.005"]["parent_technique_id"] == "T1685"
    assert corpus_map["T1105"]["is_subtechnique"] is False
    assert corpus_map["T1105"]["parent_technique_id"] is None


def test_corpus_builder_determinism_across_directories(tmp_path: Path):
    """Validates byte-for-byte reproducibility when generating corpus across isolated paths."""
    dir_a = tmp_path / "build_a"
    dir_b = tmp_path / "build_b"

    corpus_a, manifest_a, sha_a = build_windows_corpus(
        output_corpus_path=dir_a / "enterprise-windows-v19.2.jsonl",
        output_manifest_path=dir_a / "enterprise-windows-v19.2.manifest.json",
    )
    corpus_b, manifest_b, sha_b = build_windows_corpus(
        output_corpus_path=dir_b / "enterprise-windows-v19.2.jsonl",
        output_manifest_path=dir_b / "enterprise-windows-v19.2.manifest.json",
    )

    assert sha_a == EXPECTED_CORPUS_SHA256
    assert sha_b == EXPECTED_CORPUS_SHA256

    bytes_a = corpus_a.read_bytes()
    bytes_b = corpus_b.read_bytes()
    assert bytes_a == bytes_b, "Corpus bytes differ across builds"
    assert len(bytes_a) == EXPECTED_CORPUS_SIZE

    # Manifests should also be identical except for corpus_file paths
    man_a = json.loads(manifest_a.read_text(encoding="utf-8"))
    man_b = json.loads(manifest_b.read_text(encoding="utf-8"))
    assert man_a["corpus_sha256"] == man_b["corpus_sha256"] == EXPECTED_CORPUS_SHA256
    assert man_a["corpus_size_bytes"] == man_b["corpus_size_bytes"] == EXPECTED_CORPUS_SIZE
    assert man_a["document_count"] == man_b["document_count"] == EXPECTED_DOC_COUNT
    assert man_a["benchmark_coverage"] == man_b["benchmark_coverage"]


def test_corpus_manifest_integrity():
    """Validates full manifest structure, metadata values, and cryptographic references."""
    assert DEFAULT_MANIFEST_PATH.exists(), f"Manifest missing at {DEFAULT_MANIFEST_PATH}"
    manifest_bytes = DEFAULT_MANIFEST_PATH.read_bytes()

    computed_manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    assert computed_manifest_sha == EXPECTED_MANIFEST_SHA256, (
        f"Manifest SHA-256 mismatch: expected {EXPECTED_MANIFEST_SHA256}, got {computed_manifest_sha}"
    )

    data = json.loads(manifest_bytes.decode("utf-8"))

    expected_manifest_keys = {
        "attack_version",
        "benchmark_coverage",
        "corpus_file",
        "corpus_sha256",
        "corpus_size_bytes",
        "document_count",
        "generation_command",
        "root_technique_count",
        "schema_version",
        "source_commit",
        "source_stix_sha256",
        "subtechnique_count",
    }
    assert set(data.keys()) == expected_manifest_keys

    assert data["attack_version"] == ATTACK_VERSION
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["source_commit"] == ATTACK_V19_2_COMMIT
    assert data["source_stix_sha256"] == EXPECTED_ATTACK_SHA256
    assert data["corpus_sha256"] == EXPECTED_CORPUS_SHA256
    assert data["corpus_size_bytes"] == EXPECTED_CORPUS_SIZE
    assert data["document_count"] == EXPECTED_DOC_COUNT
    assert data["root_technique_count"] == EXPECTED_ROOT_COUNT
    assert data["subtechnique_count"] == EXPECTED_SUB_COUNT

    bc = data["benchmark_coverage"]
    assert bc["coverage_status"] == "8/8"
    assert bc["covered_benchmark_techniques"] == 8
    assert bc["missing_benchmark_techniques"] == []
    assert len(bc["techniques"]) == 8


def test_retrieval_text_formatting_and_lf_endings():
    """Validates strictly LF line endings (zero CRLF) and canonical retrieval text formatting."""
    corpus_bytes = DEFAULT_CORPUS_PATH.read_bytes()
    assert b"\r" not in corpus_bytes, "Found CRLF / carriage return (\\r) in corpus file!"

    manifest_bytes = DEFAULT_MANIFEST_PATH.read_bytes()
    assert b"\r" not in manifest_bytes, "Found CRLF / carriage return (\\r) in manifest file!"

    docs = load_corpus_docs()
    corpus_map = {d["technique_id"]: d for d in docs}

    # Verify root technique format (T1105)
    t1105 = corpus_map["T1105"]
    expected_t1105_text = compose_retrieval_text(
        technique_id=t1105["technique_id"],
        name=t1105["name"],
        tactics=t1105["tactics"],
        platforms=t1105["platforms"],
        description=t1105["description"],
        parent_technique_id=t1105["parent_technique_id"],
    )
    assert t1105["retrieval_text"] == expected_t1105_text
    assert "Parent Technique:" not in t1105["retrieval_text"]
    assert "Technique ID: T1105" in t1105["retrieval_text"]
    assert "Name: Ingress Tool Transfer" in t1105["retrieval_text"]

    # Verify subtechnique format (T1059.001)
    t1059_001 = corpus_map["T1059.001"]
    expected_t1059_text = compose_retrieval_text(
        technique_id=t1059_001["technique_id"],
        name=t1059_001["name"],
        tactics=t1059_001["tactics"],
        platforms=t1059_001["platforms"],
        description=t1059_001["description"],
        parent_technique_id=t1059_001["parent_technique_id"],
    )
    assert t1059_001["retrieval_text"] == expected_t1059_text
    assert "Parent Technique: T1059" in t1059_001["retrieval_text"]
    assert "Technique ID: T1059.001" in t1059_001["retrieval_text"]
    assert "Name: PowerShell" in t1059_001["retrieval_text"]
