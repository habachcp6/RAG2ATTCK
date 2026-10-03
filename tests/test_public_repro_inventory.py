"""
tests/test_public_repro_inventory.py

Unit and integration tests for public reproduction inventory collector.
Verifies all file sizes, SHA-256 digests, and semantic mappings directly against disk
to ensure 100% factual accuracy and zero divergence.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

import pytest

from scripts.collect_public_repro_inventory import (
    EXPECTED_PUBLIC_MANIFEST_SHA256,
    INPUT_AUTHORITY_GIT_SHA,
    REPO_ROOT,
    collect_inventory,
    generate_master_markdown_table,
    read_verified_buffer,
    update_plan_markdown,
)
from src.experiment.authorization import compute_code_manifest, compute_code_manifest_sha256


class TestPublicReproInventory:
    """Test suite for public reproduction master evidence inventory."""

    @pytest.fixture
    def inventory(self) -> dict:
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"
        return collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=pkg_dir,
            expected_public_manifest_sha256=EXPECTED_PUBLIC_MANIFEST_SHA256,
        )

    def test_collect_inventory_schema_and_git_lineage(self, inventory: dict) -> None:
        """Verify top-level schema, dynamic timestamp, and separated git lineage."""
        assert inventory["schema_version"] == "public-repro-inventory-v1"
        assert inventory["source_repository"] == "habachcp6/RAG2ATTCK"
        assert inventory["input_authority_git_sha"] == INPUT_AUTHORITY_GIT_SHA

        # Verify dynamic git head discovery
        assert "producer_git_head_sha" in inventory
        assert len(inventory["producer_git_head_sha"]) == 40

        # Verify ISO 8601 UTC timestamp format
        ts = inventory["generated_timestamp_utc"]
        parsed = datetime.fromisoformat(ts)
        assert parsed is not None

        assert "artifacts" in inventory
        assert len(inventory["artifacts"]) >= 15
        assert inventory["summary"]["total_master_artifacts"] == len(inventory["artifacts"])

    def test_single_read_verified_buffer_contract(self) -> None:
        """Verify that read_verified_buffer returns atomic bytes, sha256, and length."""
        bundle_path = REPO_ROOT / "artifacts/results/canonical_metric_bundle_v2.json"
        raw_b, sha, length = read_verified_buffer(bundle_path)
        assert len(raw_b) == length
        assert length == 49465
        assert sha == "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"

        # Fail closed on non-existent path
        with pytest.raises(FileNotFoundError):
            read_verified_buffer(REPO_ROOT / "non_existent_file_xyz.json")

    def test_actual_disk_file_bytes_and_hashes(self, inventory: dict) -> None:
        """Verify that every recorded master file exists on disk and matches exact byte length and SHA-256."""
        for art in inventory["artifacts"]:
            if art["file_bytes"] is None:
                continue  # semantic virtual digest

            file_path = REPO_ROOT / art["repository_path"]
            assert file_path.is_file(), f"Missing file on disk: {file_path}"
            raw_bytes = file_path.read_bytes()

            assert len(raw_bytes) == art["file_bytes"], (
                f"Byte size mismatch for {art['logical_name']} at {file_path}!\n"
                f"  Expected: {art['file_bytes']}\n"
                f"  Actual:   {len(raw_bytes)}"
            )

            actual_sha = hashlib.sha256(raw_bytes).hexdigest()
            assert actual_sha == art["sha256"], (
                f"SHA-256 mismatch for {art['logical_name']} at {file_path}!\n"
                f"  Expected: {art['sha256']}\n"
                f"  Actual:   {actual_sha}"
            )

    def test_exact_canonical_metric_bundle_v2(self, inventory: dict) -> None:
        """Verify accepted canonical metric bundle v2 constants."""
        bundle_art = next(a for a in inventory["artifacts"] if a["classification"] == "canonical_bundle")
        assert bundle_art["file_bytes"] == 49465
        assert bundle_art["sha256"] == "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"
        assert inventory["summary"]["canonical_bundle_bytes"] == 49465
        assert inventory["summary"]["canonical_bundle_sha256"] == "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"

    def test_exact_root_freeze_envelope(self, inventory: dict) -> None:
        """Verify root freeze envelope constants."""
        freeze_art = next(a for a in inventory["artifacts"] if a["classification"] == "root_receipt")
        assert freeze_art["file_bytes"] == 4335
        assert freeze_art["sha256"] == "e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2"
        assert inventory["summary"]["freeze_envelope_bytes"] == 4335
        assert inventory["summary"]["freeze_envelope_sha256"] == "e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2"

    def test_exact_protocol_and_pricing_digests(self, inventory: dict) -> None:
        """Verify protocol and pricing raw files and semantic digests."""
        proto_cfg = next(a for a in inventory["artifacts"] if a["classification"] == "protocol_config")
        assert proto_cfg["file_bytes"] == 1051
        assert proto_cfg["sha256"] == "a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb"

        proto_doc = next(a for a in inventory["artifacts"] if a["classification"] == "protocol_document")
        assert proto_doc["file_bytes"] == 9628
        assert proto_doc["sha256"] == "639fd68ae16deec86e9f6baab0980c1abb265c6cd7bb9b4662f562b87e54e819"

        proto_sem = next(a for a in inventory["artifacts"] if a["logical_name"] == "Protocol Decisions (Semantic)")
        assert proto_sem["sha256"] == "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"

        pricing_cfg = next(a for a in inventory["artifacts"] if a["classification"] == "pricing_config")
        assert pricing_cfg["file_bytes"] == 1468
        assert pricing_cfg["sha256"] == "e8afd6311f04dbbf5c34bb030e88a5b9d394f92c84d3e51feb32b327a08655a5"

        pricing_sem = next(a for a in inventory["artifacts"] if a["logical_name"] == "Pricing Contract (Semantic)")
        assert pricing_sem["sha256"] == "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565"

    def test_exact_ground_truth_and_views_sizes(self, inventory: dict) -> None:
        """Verify synthetic benchmark dataset sizes and hashes distinguishing test split from full pairs."""
        gt_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Ground Truth Test Dataset")
        assert gt_art["file_bytes"] == 733851
        assert gt_art["sha256"] == "8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608"

        views_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Paired Views Test Dataset")
        assert views_art["file_bytes"] == 153500
        assert views_art["sha256"] == "1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d"

        pairs_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Paired Cases Dataset")
        assert pairs_art["file_bytes"] == 2221465
        assert pairs_art["sha256"] == "079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d"

    def test_exact_execution_log_and_canonical_seal(self, inventory: dict) -> None:
        """Verify execution terminal log and run seal constants."""
        log_art = next(a for a in inventory["artifacts"] if a["classification"] == "terminal_log")
        assert log_art["file_bytes"] == 1141
        assert log_art["sha256"] == "fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44"

        seal_art = next(a for a in inventory["artifacts"] if a["classification"] == "terminal_seal")
        assert seal_art["file_bytes"] == 3046
        assert seal_art["sha256"] == "ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701"

    def test_code_manifest_integrity(self, inventory: dict) -> None:
        """Verify code manifest across all 53 critical code files."""
        files = compute_code_manifest(REPO_ROOT)
        assert len(files) == 53
        manifest_sha = compute_code_manifest_sha256(REPO_ROOT)
        assert manifest_sha == "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
        assert inventory["summary"]["code_manifest_files_count"] == 53
        assert inventory["summary"]["code_manifest_sha256"] == "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"

    def test_rq_evaluator_integrity(self, inventory: dict) -> None:
        """Verify frozen S2 RQ evaluator source script digest."""
        rq_art = next(a for a in inventory["artifacts"] if a["classification"] == "analysis_source")
        assert rq_art["sha256"] == "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
        assert rq_art["file_bytes"] == 126249

    def test_public_package_comprehensive_coverage(self, inventory: dict) -> None:
        """Verify descriptor 32f and all 23 declared public package items."""
        pkg = inventory.get("public_canonical_package")
        assert pkg is not None
        assert pkg["manifest_sha256"] == EXPECTED_PUBLIC_MANIFEST_SHA256
        assert pkg["manifest_size_bytes"] == 11193
        assert pkg["validation_mode"] == "canonical_authenticated_validation"
        assert pkg["total_declared_items"] == 23

        # Verify all declared items in staging matched
        for item in pkg["declared_items"]:
            assert item["status"] in {
                "VERIFIED_BYTE_EXACT",
                "VERIFIED_SANITIZED_EXACT",
                "VERIFIED_PROVENANCE_EXACT",
                "VERIFIED_RUNTIME_EXACT",
            }

    def test_public_package_trust_anchor_mismatch_fails_closed(self) -> None:
        """Verify that supplying an incorrect expected anchor fails closed."""
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"

        with pytest.raises(ValueError, match="Public manifest digest mismatch"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=pkg_dir,
                expected_public_manifest_sha256="0000000000000000000000000000000000000000000000000000000000000000",
            )

    def test_markdown_plan_table_sync(self, inventory: dict) -> None:
        """Verify that markdown derivation plan contains the dynamically generated table."""
        plan_path = REPO_ROOT / "reports/evidence/public_repro_derivation_plan_20261003.md"
        assert plan_path.is_file()
        content = plan_path.read_text(encoding="utf-8")

        # Must mention exact byte sizes
        assert "49,465" in content
        assert "4,335" in content
        assert "1,141" in content
        assert "1,051" in content
        assert "1,468" in content
        assert "733,851" in content
        assert "153,500" in content
        assert "3,046" in content

        # Must mention canonical digests
        assert "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565" in content
        assert "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c" in content

        # Ensure outdated 4adfe864 hash is completely gone
        assert "4adfe864" not in content
