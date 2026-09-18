"""
RAG2ATTCK - Deterministic Windows ATT&CK Retrieval Corpus Builder (Task T17)
Generates attack/corpus/enterprise-windows-v19.2.jsonl and its companion manifest
from Enterprise ATT&CK v19.2 STIX reference data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.attack_loader import (
    ATTACK_VERSION,
    ATTACK_V19_2_COMMIT,
    EXPECTED_ATTACK_SHA256,
    AttackTechnique,
    parse_attack_bundle,
)

DEFAULT_STIX_PATH = Path("attack/raw/enterprise-v19.2/enterprise-attack-19.2.json")
DEFAULT_SCOPE_PATH = Path("config/benchmark_scope.json")
DEFAULT_CORPUS_PATH = Path("attack/corpus/enterprise-windows-v19.2.jsonl")
DEFAULT_MANIFEST_PATH = Path("attack/corpus/enterprise-windows-v19.2.manifest.json")

SCHEMA_VERSION = "1.0.0"

PROHIBITED_METADATA_KEYS = frozenset({
    "ground_truth",
    "technique_label",
    "expected_technique",
    "attack_label",
    "label",
    "gt",
    "target",
    "y_true",
    "y_pred",
})


@dataclass(frozen=True)
class CorpusDocument:
    """Deterministic retrieval corpus document for a single ATT&CK technique."""

    technique_id: str
    stix_id: str
    name: str
    description: str
    platforms: List[str]
    tactics: List[str]
    is_subtechnique: bool
    parent_technique_id: Optional[str]
    modified: str
    source_version: str
    retrieval_text: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "description": self.description,
            "is_subtechnique": self.is_subtechnique,
            "modified": self.modified,
            "name": self.name,
            "parent_technique_id": self.parent_technique_id,
            "platforms": self.platforms,
            "retrieval_text": self.retrieval_text,
            "source_version": self.source_version,
            "stix_id": self.stix_id,
            "tactics": self.tactics,
            "technique_id": self.technique_id,
        }

    def to_json_line(self) -> str:
        d = self.to_dict()
        leaked = set(d.keys()) & PROHIBITED_METADATA_KEYS
        if leaked:
            raise ValueError(f"Prohibited evaluation metadata found in document: {leaked}")
        return json.dumps(d, sort_keys=True, ensure_ascii=False)


def extract_stix_ids(stix_path: Path) -> Dict[str, str]:
    """Extracts mapping from MITRE ID to STIX ID from raw STIX 2.1 bundle."""
    with open(stix_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    mapping: Dict[str, str] = {}
    for obj in bundle.get("objects", []):
        if obj.get("type") == "attack-pattern":
            sid = obj.get("id")
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    mid = ref.get("external_id")
                    if mid and sid:
                        mapping[mid] = sid
                    break
    return mapping


def compose_retrieval_text(
    technique_id: str,
    name: str,
    tactics: List[str],
    platforms: List[str],
    description: str,
    parent_technique_id: Optional[str] = None,
) -> str:
    """Deterministic composition of retrieval text from official ATT&CK data only."""
    tactics_str = ", ".join(sorted(tactics))
    platforms_str = ", ".join(sorted(platforms))
    clean_description = description.replace("\r\n", "\n").replace("\r", "\n").strip()

    lines = [
        f"Technique ID: {technique_id}",
        f"Name: {name}",
        f"Tactics: {tactics_str}",
        f"Platforms: {platforms_str}",
    ]
    if parent_technique_id:
        lines.append(f"Parent Technique: {parent_technique_id}")
    lines.append(f"Description:\n{clean_description}")

    return "\n".join(lines)


def build_windows_corpus(
    stix_path: Path = DEFAULT_STIX_PATH,
    output_corpus_path: Path = DEFAULT_CORPUS_PATH,
    output_manifest_path: Path = DEFAULT_MANIFEST_PATH,
    scope_path: Optional[Path] = DEFAULT_SCOPE_PATH,
) -> Tuple[Path, Path, str]:
    """
    Builds the deterministic Windows ATT&CK retrieval corpus and manifest.
    Returns (corpus_path, manifest_path, corpus_sha256).
    """
    if not stix_path.exists():
        raise FileNotFoundError(f"STIX bundle not found at {stix_path}")

    techniques = parse_attack_bundle(stix_path)
    tid_to_stix = extract_stix_ids(stix_path)

    win_active = [
        t for t in techniques.values()
        if "Windows" in t.platforms and not t.revoked and not t.deprecated
    ]
    if len(win_active) != 474:
        raise ValueError(f"Expected 474 active Windows techniques, found {len(win_active)}")

    # Sort strictly ascending by technique_id
    win_active.sort(key=lambda t: t.technique_id)

    root_count = sum(1 for t in win_active if not t.is_subtechnique)
    sub_count = sum(1 for t in win_active if t.is_subtechnique)

    # Benchmark scope verification
    benchmark_catalog: List[str] = []
    if scope_path and scope_path.exists():
        with open(scope_path, "r", encoding="utf-8") as f:
            scope_data = json.load(f)
        benchmark_catalog = scope_data.get("attack_catalog", [])
        win_ids = {t.technique_id for t in win_active}
        missing = [tid for tid in benchmark_catalog if tid not in win_ids]
        if missing:
            raise ValueError(f"Benchmark techniques missing from active Windows corpus: {missing}")

    docs: List[CorpusDocument] = []
    for t in win_active:
        retrieval_text = compose_retrieval_text(
            technique_id=t.technique_id,
            name=t.name,
            tactics=t.tactics,
            platforms=t.platforms,
            description=t.description,
            parent_technique_id=t.parent_technique_id,
        )
        doc = CorpusDocument(
            technique_id=t.technique_id,
            stix_id=tid_to_stix[t.technique_id],
            name=t.name,
            description=t.description,
            platforms=sorted(t.platforms),
            tactics=sorted(t.tactics),
            is_subtechnique=t.is_subtechnique,
            parent_technique_id=t.parent_technique_id,
            modified=t.modified,
            source_version=ATTACK_VERSION,
            retrieval_text=retrieval_text,
        )
        docs.append(doc)

    output_corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_corpus_path, "w", encoding="utf-8", newline="\n") as f:
        for doc in docs:
            f.write(doc.to_json_line() + "\n")

    corpus_bytes = output_corpus_path.read_bytes()
    corpus_sha256 = hashlib.sha256(corpus_bytes).hexdigest()
    corpus_size = len(corpus_bytes)

    manifest_data = {
        "attack_version": ATTACK_VERSION,
        "benchmark_coverage": {
            "coverage_status": f"{len(benchmark_catalog)}/{len(benchmark_catalog)}",
            "covered_benchmark_techniques": len(benchmark_catalog),
            "missing_benchmark_techniques": [],
            "techniques": benchmark_catalog,
            "total_benchmark_techniques": len(benchmark_catalog),
        },
        "corpus_file": str(output_corpus_path.as_posix()),
        "corpus_sha256": corpus_sha256,
        "corpus_size_bytes": corpus_size,
        "document_count": len(docs),
        "generation_command": "python -m src.retrieval.corpus_builder",
        "root_technique_count": root_count,
        "schema_version": SCHEMA_VERSION,
        "source_commit": ATTACK_V19_2_COMMIT,
        "source_stix_sha256": EXPECTED_ATTACK_SHA256,
        "subtechnique_count": sub_count,
    }

    output_manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_manifest_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(manifest_data, f, indent=2, sort_keys=True, ensure_ascii=False)
        f.write("\n")

    return output_corpus_path, output_manifest_path, corpus_sha256


def main():
    parser = argparse.ArgumentParser(description="Build deterministic Windows ATT&CK retrieval corpus.")
    parser.add_argument("--stix-path", type=Path, default=DEFAULT_STIX_PATH)
    parser.add_argument("--scope-path", type=Path, default=DEFAULT_SCOPE_PATH)
    parser.add_argument("--corpus-path", type=Path, default=DEFAULT_CORPUS_PATH)
    parser.add_argument("--manifest-path", type=Path, default=DEFAULT_MANIFEST_PATH)
    args = parser.parse_args()

    c_path, m_path, sha = build_windows_corpus(
        stix_path=args.stix_path,
        output_corpus_path=args.corpus_path,
        output_manifest_path=args.manifest_path,
        scope_path=args.scope_path,
    )
    print(f"[+] Corpus successfully generated at: {c_path}")
    print(f"[+] SHA-256: {sha}")
    print(f"[+] Manifest successfully generated at: {m_path}")


if __name__ == "__main__":
    main()
