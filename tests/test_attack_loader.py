"""
Unit tests for Task 5-acquire ATT&CK Loader (src/attack_loader.py).
Tests immutable commit pinning, SHA-256 integrity verification,
rejection of corrupted artifacts, and attack manifest accuracy.
"""

import json
from pathlib import Path
import pytest

from src.attack_loader import (
    ATTACK_VERSION,
    ATTACK_V19_2_COMMIT,
    ATTACK_V19_2_URL,
    EXPECTED_ATTACK_SIZE,
    EXPECTED_ATTACK_SHA256,
    download_attack_reference
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
    assert manifest["stix_file"]["size_bytes"] == EXPECTED_ATTACK_SIZE

    stats = manifest["catalog_statistics"]
    assert stats["total_techniques_and_subtechniques"] > 600
    assert stats["windows_active_count"] > 200
