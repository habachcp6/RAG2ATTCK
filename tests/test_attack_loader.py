"""
Unit tests for Task 5-acquire ATT&CK Loader (src/attack_loader.py).
Tests immutable commit pinning, SHA-256 integrity verification,
rejection of corrupted artifacts, and attack manifest accuracy.
"""

import json
from pathlib import Path
import subprocess
import pytest

from src.attack_loader import (
    ATTACK_VERSION,
    ATTACK_V19_2_COMMIT,
    ATTACK_V19_2_URL,
    EXPECTED_ATTACK_SIZE,
    EXPECTED_ATTACK_SHA256,
    download_attack_reference,
    parse_attack_bundle,
)
from src.llm.schemas import (
    load_attack_registry,
    validate_technique_id,
    ParseStatus,
)


def test_attack_immutable_pinning():
    """Enterprise ATT&CK v19.2 reference must be pinned to immutable Git commit SHA."""
    assert ATTACK_VERSION == "19.2"
    assert ATTACK_V19_2_COMMIT == "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4"
    assert "master" not in ATTACK_V19_2_URL
    assert "main" not in ATTACK_V19_2_URL
    assert ATTACK_V19_2_COMMIT in ATTACK_V19_2_URL
    assert EXPECTED_ATTACK_SIZE == 53835637
    assert EXPECTED_ATTACK_SHA256 == "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4"


def test_corrupted_attack_rejection(tmp_path):
    """Download verification must reject file with invalid hash when size matches."""
    ws = tmp_path
    dest = ws / "attack" / "raw" / "enterprise-v19.2"
    dest.mkdir(parents=True)
    target = dest / "enterprise-attack-19.2.json"
    with open(target, "wb") as f:
        f.truncate(EXPECTED_ATTACK_SIZE)

    with pytest.raises(ValueError, match="mismatch"):
        download_attack_reference(ws, target_dir=dest)


def test_production_attack_manifest():
    """Verify production attack_manifest.json contents and hash verification."""
    manifest_path = Path("data/metadata/attack_manifest.json")
    assert manifest_path.exists(), "attack_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["attack_version"] == "19.2"
    assert manifest["immutable_git_commit"] == "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4"
    assert manifest["sha256_verified"] is True
    assert manifest["computed_sha256"] == EXPECTED_ATTACK_SHA256
    assert manifest["expected_sha256"] == EXPECTED_ATTACK_SHA256
    assert manifest["stix_file"]["size_bytes"] == EXPECTED_ATTACK_SIZE

    stats = manifest["catalog_statistics"]
    assert stats["total_techniques_and_subtechniques"] == 858
    assert stats["revoked_count"] == 149
    assert stats["deprecated_count"] == 12
    assert stats["active_count"] == 697
    assert stats["windows_active_count"] == 474
    assert stats["windows_root_techniques"] == 176
    assert stats["windows_subtechniques"] == 298


def test_stix_bundle_parsing():
    """Parse raw enterprise-v19.2 STIX bundle and verify accounting statistics."""
    stix_path = Path("attack/raw/enterprise-v19.2/enterprise-attack-19.2.json")
    assert stix_path.exists(), "Raw STIX bundle must exist on disk"
    techniques = parse_attack_bundle(stix_path)
    assert len(techniques) == 858

    active_techs = [t for t in techniques.values() if not t.revoked and not t.deprecated]
    assert len(active_techs) == 697

    win_active = [t for t in active_techs if "Windows" in t.platforms]
    assert len(win_active) == 474

    win_root = [t for t in win_active if not t.is_subtechnique]
    win_sub = [t for t in win_active if t.is_subtechnique]
    assert len(win_root) == 176
    assert len(win_sub) == 298


def test_benchmark_scope_provenance():
    """Automated provenance test verifying benchmark_scope.json matches canonical main commit."""
    scope_file = Path("config/benchmark_scope.json")
    assert scope_file.exists(), "config/benchmark_scope.json must exist"
    with open(scope_file, "r", encoding="utf-8") as f:
        scope = json.load(f)

    assert scope["schema_version"] == "1.0.0"
    assert scope["attack_version"] == "19.2"
    commit = scope["source_main_commit"]
    assert commit == "93d564b5dbc0415e64ed85d014ae0b5c6e41f7f8"

    cmd = ["git", "show", f"{commit}:config/data_ground_truth.json"]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    canonical = json.loads(res.stdout)
    assert scope["attack_catalog"] == canonical["synthetic_benchmark"]["attack_catalog"]


def test_benchmark_scope_techniques_coverage_and_attributes():
    """Verify all 8 benchmark techniques exist in STIX v19.2, are active Windows, and validate."""
    scope_file = Path("config/benchmark_scope.json")
    assert scope_file.exists(), "config/benchmark_scope.json must exist"
    with open(scope_file, "r", encoding="utf-8") as f:
        catalog = json.load(f)["attack_catalog"]
    assert len(catalog) == 8

    stix_path = Path("attack/raw/enterprise-v19.2/enterprise-attack-19.2.json")
    techniques = parse_attack_bundle(stix_path)
    registry = load_attack_registry()

    for tid in catalog:
        assert tid in techniques, f"{tid} missing from parsed STIX bundle"
        assert tid in registry, f"{tid} missing from load_attack_registry()"
        t = techniques[tid]
        assert not t.revoked, f"{tid} is revoked"
        assert not t.deprecated, f"{tid} is deprecated"
        assert "Windows" in t.platforms, f"{tid} does not support Windows"

        is_valid, status, reason = validate_technique_id(tid)
        assert is_valid is True
        assert status == ParseStatus.VALID
        assert reason is None


def test_post_hoc_validator_schema_alignment():
    """Verify load_attack_registry() exactly aligns with parsed STIX bundle keys."""
    stix_path = Path("attack/raw/enterprise-v19.2/enterprise-attack-19.2.json")
    parsed_keys = set(parse_attack_bundle(stix_path).keys())
    registry_keys = load_attack_registry(stix_path)
    assert parsed_keys == registry_keys
