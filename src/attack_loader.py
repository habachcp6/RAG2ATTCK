"""
RAG2ATTCK - MITRE ATT&CK Loader & Reference Reconciliation Module (Task 5)
Handles acquiring Enterprise ATT&CK v19.2 STIX JSON, verifying checksums,
building the immutable technique catalog, and performing transition audits.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import urllib.request
from typing import Any, Dict, List, Optional, Set, Tuple


ATTACK_VERSION = "19.2"
ATTACK_REPO = "https://github.com/mitre-attack/attack-stix-data"
ATTACK_V19_2_COMMIT = "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4"
ATTACK_V19_2_URL = f"https://raw.githubusercontent.com/mitre-attack/attack-stix-data/{ATTACK_V19_2_COMMIT}/enterprise-attack/enterprise-attack-19.2.json"
EXPECTED_ATTACK_SIZE = 53835637
EXPECTED_ATTACK_SHA256 = "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4"


@dataclass(frozen=True)
class AttackTechnique:
    technique_id: str
    name: str
    description: str
    is_subtechnique: bool
    parent_technique_id: Optional[str]
    tactics: List[str]
    platforms: List[str]
    revoked: bool
    deprecated: bool
    revoked_by: Optional[str]
    created: str
    modified: str
    url: str


def download_attack_reference(
    workspace_root: Path,
    url: str = ATTACK_V19_2_URL,
    target_dir: Optional[Path] = None,
    expected_size: int = EXPECTED_ATTACK_SIZE,
    expected_sha256: str = EXPECTED_ATTACK_SHA256,
    chunk_size: int = 1024 * 1024
) -> Tuple[Path, str, int]:
    """
    Downloads Enterprise ATT&CK v19.2 from immutable GitHub commit SHA to attack/raw/enterprise-v19.2/
    using staging and verifies size and expected SHA-256 before moving to final destination.
    Returns (final_path, sha256_hash, file_size).
    """
    ws = workspace_root.resolve()
    dest_dir = target_dir or (ws / "attack" / "raw" / "enterprise-v19.2")
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_file = dest_dir / "enterprise-attack-19.2.json"

    staging_dir = ws / ".cache" / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)
    staging_file = staging_dir / "enterprise-attack-19.2.json.tmp"

    if target_file.exists() and target_file.stat().st_size == expected_size:
        sha256 = hashlib.sha256(target_file.read_bytes()).hexdigest()
        if sha256 == expected_sha256:
            return target_file, sha256, target_file.stat().st_size
        else:
            raise ValueError(f"Existing ATT&CK file SHA-256 mismatch: expected {expected_sha256}, got {sha256}")

    print(f"[*] Downloading ATT&CK v19.2 reference from immutable source {url}...")
    req = urllib.request.Request(url, headers={"User-Agent": "RAG2ATTCK-Pipeline/1.0"})
    hasher = hashlib.sha256()
    total_downloaded = 0

    with urllib.request.urlopen(req) as resp, open(staging_file, "wb") as out_f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            out_f.write(chunk)
            hasher.update(chunk)
            total_downloaded += len(chunk)

    computed_hash = hasher.hexdigest()
    print(f"[+] Downloaded {total_downloaded} bytes. Computed SHA-256: {computed_hash}")

    if total_downloaded != expected_size:
        if staging_file.exists():
            staging_file.unlink()
        raise ValueError(
            f"ATT&CK download size mismatch: expected {expected_size}, got {total_downloaded}"
        )

    if computed_hash != expected_sha256:
        if staging_file.exists():
            staging_file.unlink()
        raise ValueError(
            f"ATT&CK download SHA-256 mismatch: expected {expected_sha256}, got {computed_hash}"
        )

    # Move from staging to raw
    if target_file.exists():
        target_file.unlink()
    shutil.move(str(staging_file), str(target_file))

    return target_file, computed_hash, total_downloaded


def parse_attack_bundle(stix_path: Path) -> Dict[str, AttackTechnique]:
    """
    Parses STIX 2.1 JSON bundle for Enterprise ATT&CK and extracts techniques.
    """
    with open(stix_path, "r", encoding="utf-8") as f:
        bundle = json.load(f)

    techniques: Dict[str, AttackTechnique] = {}
    objects = bundle.get("objects", [])

    # First pass: gather relationships (e.g. subtechnique-of, revoked-by)
    parent_map: Dict[str, str] = {}
    revocation_map: Dict[str, str] = {}

    for obj in objects:
        if obj.get("type") == "relationship":
            rel_type = obj.get("relationship_type")
            source_ref = obj.get("source_ref")
            target_ref = obj.get("target_ref")
            if rel_type == "subtechnique-of":
                parent_map[source_ref] = target_ref
            elif rel_type == "revoked-by":
                revocation_map[source_ref] = target_ref

    # Second pass: attack patterns
    attack_pattern_id_to_stix: Dict[str, str] = {}
    stix_to_technique_id: Dict[str, str] = {}

    for obj in objects:
        if obj.get("type") == "attack-pattern":
            stix_id = obj.get("id")
            ext_refs = obj.get("external_references", [])
            mitre_id = None
            url = ""
            for ref in ext_refs:
                if ref.get("source_name") == "mitre-attack":
                    mitre_id = ref.get("external_id")
                    url = ref.get("url", "")
                    break
            if mitre_id:
                stix_to_technique_id[stix_id] = mitre_id

    for obj in objects:
        if obj.get("type") == "attack-pattern":
            stix_id = obj.get("id")
            ext_refs = obj.get("external_references", [])
            mitre_id = None
            url = ""
            for ref in ext_refs:
                if ref.get("source_name") == "mitre-attack":
                    mitre_id = ref.get("external_id")
                    url = ref.get("url", "")
                    break

            if not mitre_id:
                continue

            name = obj.get("name", "")
            description = obj.get("description", "")
            is_sub = obj.get("x_mitre_is_subtechnique", False)
            platforms = obj.get("x_mitre_platforms", [])
            revoked = obj.get("revoked", False)
            deprecated = obj.get("x_mitre_deprecated", False)
            created = obj.get("created", "")
            modified = obj.get("modified", "")

            tactics = []
            for phase in obj.get("kill_chain_phases", []):
                if phase.get("kill_chain_name") == "mitre-attack":
                    tactics.append(phase.get("phase_name"))

            parent_mitre_id = None
            if is_sub and stix_id in parent_map:
                parent_stix = parent_map[stix_id]
                parent_mitre_id = stix_to_technique_id.get(parent_stix)

            revoked_by_id = None
            if revoked and stix_id in revocation_map:
                target_stix = revocation_map[stix_id]
                revoked_by_id = stix_to_technique_id.get(target_stix)

            tech = AttackTechnique(
                technique_id=mitre_id,
                name=name,
                description=description,
                is_subtechnique=is_sub,
                parent_technique_id=parent_mitre_id,
                tactics=tactics,
                platforms=platforms,
                revoked=revoked,
                deprecated=deprecated,
                revoked_by=revoked_by_id,
                created=created,
                modified=modified,
                url=url
            )
            techniques[mitre_id] = tech

    return techniques


def generate_attack_manifest(
    workspace_root: Path,
    stix_file: Path,
    sha256: str,
    file_size: int,
    techniques: Dict[str, AttackTechnique]
) -> Path:
    """
    Generates data/metadata/attack_manifest.json summarizing the ATT&CK release.
    """
    ws = workspace_root.resolve()
    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    manifest_file = meta_dir / "attack_manifest.json"

    windows_techniques = {
        tid: t for tid, t in techniques.items()
        if "Windows" in t.platforms and not t.revoked and not t.deprecated
    }

    manifest_data = {
        "schema_version": "1.0.0",
        "task": "T5_ACQUIRE_ATTACK_REFERENCE",
        "task_status": "PASS",
        "attack_version": ATTACK_VERSION,
        "repository": ATTACK_REPO,
        "immutable_git_commit": ATTACK_V19_2_COMMIT,
        "immutable_raw_source": ATTACK_V19_2_URL,
        "acquisition_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "expected_sha256": EXPECTED_ATTACK_SHA256,
        "computed_sha256": sha256,
        "sha256_verified": sha256 == EXPECTED_ATTACK_SHA256,
        "stix_file": {
            "path": str(stix_file.relative_to(ws)).replace("\\", "/"),
            "size_bytes": file_size,
            "sha256": sha256
        },
        "catalog_statistics": {
            "total_techniques_and_subtechniques": len(techniques),
            "revoked_count": sum(1 for t in techniques.values() if t.revoked),
            "deprecated_count": sum(1 for t in techniques.values() if t.deprecated),
            "active_count": sum(1 for t in techniques.values() if not t.revoked and not t.deprecated),
            "windows_active_count": len(windows_techniques),
            "windows_root_techniques": sum(1 for t in windows_techniques.values() if not t.is_subtechnique),
            "windows_subtechniques": sum(1 for t in windows_techniques.values() if t.is_subtechnique)
        }
    }

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)

    return manifest_file
