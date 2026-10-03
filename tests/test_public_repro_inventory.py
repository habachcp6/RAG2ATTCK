"""
tests/test_public_repro_inventory.py

Unit and integration tests for public reproduction inventory collector.
Verifies all file sizes, SHA-256 digests, and semantic mappings directly against disk
to ensure 100% factual accuracy, read-once mapping integrity, fail-closed CLI checks,
and census synchronization.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.collect_public_repro_inventory import (
    AUTHENTICATED_VALIDATION_LABEL,
    EXPECTED_BUNDLE_SHA256,
    EXPECTED_FREEZE_ENVELOPE_SHA256,
    EXPECTED_PUBLIC_MANIFEST_SHA256,
    INPUT_AUTHORITY_GIT_SHA,
    REPO_ROOT,
    UNANCHORED_VALIDATION_LABEL,
    collect_inventory,
    generate_master_markdown_table,
    get_git_head_sha,
    main,
    read_verified_buffer,
    update_plan_markdown,
    validate_utc_iso_timestamp,
)
from src.experiment.config import canonical_bytes, digest
from src.experiment.authorization import compute_code_manifest, compute_code_manifest_sha256

class TestPublicReproInventory:
    """Test suite for public reproduction master evidence inventory."""

    @pytest.fixture
    def inventory(self) -> dict:
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"
        actual_pkg_dir = pkg_dir if pkg_dir.is_dir() else None
        return collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=actual_pkg_dir,
            expected_public_manifest_sha256=EXPECTED_PUBLIC_MANIFEST_SHA256 if actual_pkg_dir else None,
            expected_bundle_sha256=EXPECTED_BUNDLE_SHA256,
        )

    def test_collect_inventory_schema_and_git_lineage(self, inventory: dict) -> None:
        """Verify top-level schema, dynamic timestamp, and separated git lineage."""
        assert inventory["schema_version"] == "public-repro-inventory-v1"
        assert inventory["source_repository"] == "habachcp6/RAG2ATTCK"
        assert inventory["input_authority_git_sha"] == INPUT_AUTHORITY_GIT_SHA

        # Verify dynamic git head discovery
        assert "producer_git_head_sha" in inventory
        assert len(inventory["producer_git_head_sha"]) == 40
        assert inventory["producer_git_head_sha"] == get_git_head_sha(REPO_ROOT)

        # Verify ISO 8601 UTC timestamp format with trailing 'Z'
        ts = inventory["generated_timestamp_utc"]
        assert ts.endswith("Z")
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed is not None

        # Verify ground truth census
        assert "ground_truth_census" in inventory
        census = inventory["ground_truth_census"]
        assert census["total_pairs"] == 670
        assert census["total_views"] == 1340
        assert census["test_pairs"] == 640
        assert census["test_views"] == 1280
        assert census["dev_pairs"] == 30
        assert census["dev_views"] == 60

        assert "artifacts" in inventory
        assert len(inventory["artifacts"]) >= 16
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

    def test_read_once_mapping_integrity(self) -> None:
        """Verify that code manifest files are read exactly once without duplicate disk access."""
        with patch("scripts.collect_public_repro_inventory.compute_code_manifest") as mock_manifest:
            mock_manifest.return_value = {"src/test.py": "abc123hash"}
            freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
            log_path = REPO_ROOT / "logs/task-1264.log"
            inv = collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
            )
            # Verify compute_code_manifest was called exactly once
            assert mock_manifest.call_count == 1
            # Verify code manifest SHA was computed directly from the returned dictionary
            expected_sha = digest(canonical_bytes({"src/test.py": "abc123hash"}))
            assert inv["summary"]["code_manifest_sha256"] == expected_sha

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
        """Verify benchmark dataset sizes and hashes with census synchronization (1,340 views / 670 pairs)."""
        gt_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Ground Truth Dataset")
        assert gt_art["file_bytes"] == 733851
        assert gt_art["sha256"] == "8f3d73bac7e81336a3e90bfa5a5d0850a51ac5588385ee53ad940bcbc3612608"

        views_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Paired Views Dataset")
        assert views_art["file_bytes"] == 153500
        assert views_art["sha256"] == "1e6b0d3bd525b8fe9f97ba9e5656905597a3939e47c130a9e6f74535e2cd421d"

        pairs_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Paired Cases Dataset")
        assert pairs_art["file_bytes"] == 2221465
        assert pairs_art["sha256"] == "079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d"

        split_art = next(a for a in inventory["artifacts"] if a["logical_name"] == "Split Manifest Dataset Partition")
        assert split_art["file_bytes"] == 10739
        assert split_art["sha256"] == "37fce63ccaa6db8e13604b7e3783997a10635f58995881b5e41913e6f550f43f"

    def test_exact_execution_log_and_canonical_seal(self, inventory: dict) -> None:
        """Verify execution terminal log (1,141 bytes) and run seal constants."""
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
        assert manifest_sha in {
            "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4",
            "ff4f4a89edf889a072f71021dc2c5a6ee89254c9b053156db0c17b9d9010af67",
            "3ec03883062c2b117a1352c78199857a6ae2927a777ae5799daefbc817332dd6",
        }
        assert inventory["summary"]["code_manifest_files_count"] == 53
        assert inventory["summary"]["code_manifest_sha256"] == manifest_sha

    def test_rq_evaluator_integrity(self, inventory: dict) -> None:
        """Verify frozen S2 RQ evaluator source script digest."""
        rq_art = next(a for a in inventory["artifacts"] if a["classification"] == "analysis_source")
        assert rq_art["sha256"] == "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
        assert rq_art["file_bytes"] == 126249

    def test_public_package_comprehensive_coverage(self, inventory: dict) -> None:
        """Verify descriptor 32f and all 23 declared public package items in authenticated mode."""
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"
        if not pkg_dir.is_dir():
            pytest.skip(
                f"Canonical public package staging directory not present at {pkg_dir}; "
                "required in acceptance coverage test"
            )
        pkg = inventory.get("public_canonical_package")
        assert pkg is not None
        assert pkg["manifest_sha256"] == EXPECTED_PUBLIC_MANIFEST_SHA256
        assert pkg["manifest_size_bytes"] == 11193
        assert pkg["validation_mode"] == AUTHENTICATED_VALIDATION_LABEL
        assert pkg["total_declared_items"] == 23

        # Verify all declared items in staging matched
        for item in pkg["declared_items"]:
            assert item["status"] in {
                "VERIFIED_BYTE_EXACT",
                "VERIFIED_SANITIZED_EXACT",
                "VERIFIED_PROVENANCE_EXACT",
                "VERIFIED_RUNTIME_EXACT",
            }

    def test_unanchored_mode_validation_label(self) -> None:
        """Verify that omitting external trust anchor labels validation mode as unanchored."""
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"
        if not pkg_dir.is_dir():
            pytest.skip(
                f"Canonical public package staging directory not present at {pkg_dir}; "
                "required in unanchored mode test"
            )
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"

        inv = collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=pkg_dir,
            expected_public_manifest_sha256=None,
        )
        assert inv["summary"]["public_package_validation_mode"] == UNANCHORED_VALIDATION_LABEL
        assert inv["public_canonical_package"]["validation_mode"] == UNANCHORED_VALIDATION_LABEL

    def test_authenticated_mode_fail_closed_checks(self, tmp_path: Path) -> None:
        """Verify fail-closed behavior when expected trust anchor is supplied."""
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"

        # 1. Non-existent package directory fails closed
        with pytest.raises(FileNotFoundError, match="Public package directory not found"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=tmp_path / "does_not_exist",
                expected_public_manifest_sha256=EXPECTED_PUBLIC_MANIFEST_SHA256,
            )

        # 2. Missing manifest descriptor fails closed
        empty_dir = tmp_path / "empty_pkg"
        empty_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="Public package manifest descriptor not found"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=empty_dir,
                expected_public_manifest_sha256=EXPECTED_PUBLIC_MANIFEST_SHA256,
            )

        # 3. Descriptor hash mismatch fails closed
        fake_manifest = empty_dir / "canonical_bundle_manifest.json"
        fake_manifest.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match="Public manifest digest mismatch"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=empty_dir,
                expected_public_manifest_sha256=EXPECTED_PUBLIC_MANIFEST_SHA256,
            )

        # 4. Declared item missing from staging fails closed
        mock_manifest_dict = {
            "schema_version": "2.0.0",
            "byte_preserved_files": {
                "inputs/missing_item.json": {
                    "sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                    "size_bytes": 100,
                }
            },
        }
        mock_bytes = json.dumps(mock_manifest_dict).encode("utf-8")
        mock_sha = hashlib.sha256(mock_bytes).hexdigest()
        fake_manifest.write_bytes(mock_bytes)

        with pytest.raises(FileNotFoundError, match="declared item missing from staging"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=empty_dir,
                expected_public_manifest_sha256=mock_sha,
            )

        # 5. Declared item content mismatch fails closed
        bad_item = empty_dir / "inputs/missing_item.json"
        bad_item.parent.mkdir(parents=True, exist_ok=True)
        bad_item.write_bytes(b"corrupted content")
        with pytest.raises(ValueError, match="declared item mismatch"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=empty_dir,
                expected_public_manifest_sha256=mock_sha,
            )

    def test_markdown_plan_table_sync(self, inventory: dict) -> None:
        """Verify that markdown derivation plan contains the dynamically generated table and clean census."""
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
        assert "2,221,465" in content
        assert "10,739" in content
        assert "3,046" in content

        # Must mention canonical digests
        assert "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565" in content
        assert "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c" in content

        # Must mention census breakdown
        assert "1,340 views / 670 pairs total" in content
        assert "1,280 views / 640 pairs" in content
        assert "60 views / 30 pairs" in content

        # Ensure outdated 4adfe864 hash is completely gone
        assert "4adfe864" not in content

    def test_b_master_bytes_anchor_and_tamper_rejection(self) -> None:
        """Verify that B v2 master bytes require explicit external anchor and reject tampering fail-closed."""
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"
        pkg_dir = REPO_ROOT / "artifacts/public_package_staging/03_public_canonical_package"
        actual_pkg_dir = pkg_dir if pkg_dir.is_dir() else None

        # 1. Positive authenticated anchor with expected_bundle_sha256
        inv_auth = collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=actual_pkg_dir,
            expected_bundle_sha256=EXPECTED_BUNDLE_SHA256,
        )
        assert inv_auth["summary"]["canonical_bundle_authenticated"] is True
        assert inv_auth["summary"]["canonical_bundle_validation_status"] == "CANONICAL_AUTHENTICATED"
        b_auth = next(a for a in inv_auth["artifacts"] if a["repository_path"] == "artifacts/results/canonical_metric_bundle_v2.json")
        assert b_auth["logical_name"] == "Accepted Metric Bundle v2"
        assert b_auth["validation_status"] == "CANONICAL_AUTHENTICATED"
        assert "Canonical Anchor - Authenticated" in b_auth["domain_authority"]

        # 2. Positive authenticated anchor derived from root freeze envelope
        inv_freeze = collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=actual_pkg_dir,
            expected_freeze_envelope_sha256=EXPECTED_FREEZE_ENVELOPE_SHA256,
        )
        assert inv_freeze["summary"]["canonical_bundle_authenticated"] is True
        assert inv_freeze["summary"]["canonical_bundle_validation_status"] == "CANONICAL_AUTHENTICATED"

        # 3. Tampered bundle bytes mismatch fails closed
        with pytest.raises(ValueError, match="Canonical metric bundle v2 digest mismatch"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=actual_pkg_dir,
                expected_bundle_sha256="d6734866" + "0" * 56,
            )

        # 4. Tampered freeze envelope mismatch fails closed
        with pytest.raises(ValueError, match="Root freeze envelope digest mismatch"):
            collect_inventory(
                repo_root=REPO_ROOT,
                freeze_envelope_path=freeze_path,
                terminal_log_path=log_path,
                public_package_dir=actual_pkg_dir,
                expected_freeze_envelope_sha256="0" * 64,
            )

        # 5. Generic unanchored mode does not claim accepted canonical authority
        inv_unanchored = collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            public_package_dir=actual_pkg_dir,
            expected_bundle_sha256=None,
            expected_freeze_envelope_sha256=None,
        )
        assert inv_unanchored["summary"]["canonical_bundle_authenticated"] is False
        assert inv_unanchored["summary"]["canonical_bundle_validation_status"] == "OBSERVED_NOT_VERIFIED"
        b_un = next(a for a in inv_unanchored["artifacts"] if a["repository_path"] == "artifacts/results/canonical_metric_bundle_v2.json")
        assert b_un["logical_name"] == "Observed Metric Bundle v2 (Unanchored)"
        assert "UNVERIFIED" in b_un["domain_authority"]
        assert b_un["validation_status"] == "OBSERVED_NOT_VERIFIED"

    def test_timestamp_utc_timezone_aware_validation(self) -> None:
        """Verify timezone-aware UTC validation and separation of actual generation vs reproducibility epoch."""
        freeze_path = REPO_ROOT / "reports/evidence/root_metric_bundle_v2_freeze_95c0233.json"
        log_path = REPO_ROOT / "logs/task-1264.log"

        # Valid UTC timestamps
        assert validate_utc_iso_timestamp("2026-10-03T12:34:56Z") == "2026-10-03T12:34:56Z"
        assert validate_utc_iso_timestamp("2026-10-03T12:34:56+00:00") == "2026-10-03T12:34:56Z"

        # Invalid formats fail closed
        with pytest.raises(ValueError, match="Invalid ISO 8601 timestamp"):
            validate_utc_iso_timestamp("not-a-time")
        with pytest.raises(ValueError, match="is naive"):
            validate_utc_iso_timestamp("2026-10-03T12:34:56")
        with pytest.raises(ValueError, match="has non-zero UTC offset"):
            validate_utc_iso_timestamp("2026-10-03T12:34:56+07:00")

        # CLI fails closed with exit code 1 on bad timestamp
        with patch("sys.argv", ["collect_public_repro_inventory.py", "--timestamp-utc", "not-a-time"]):
            assert main() == 1

        # Inventory preserves reproducibility epoch alongside actual timestamp
        inv_ts = collect_inventory(
            repo_root=REPO_ROOT,
            freeze_envelope_path=freeze_path,
            terminal_log_path=log_path,
            timestamp_utc="2026-10-03T00:00:00Z",
        )
        assert inv_ts["generated_timestamp_utc"] == "2026-10-03T00:00:00Z"
        assert inv_ts["reproducibility_epoch_utc"] == "2026-10-03T00:00:00Z"
        assert "actual_generated_timestamp_utc" in inv_ts
        assert inv_ts["actual_generated_timestamp_utc"].endswith("Z")

    def test_check_only_requires_both_external_authorities(self) -> None:
        """Verify that canonical --check-only requires both bundle anchor and public manifest anchor."""
        # 1. No authorities supplied -> exit 1
        with patch("sys.argv", ["collect_public_repro_inventory.py", "--check-only"]):
            assert main() == 1

        # 2. Only manifest anchor supplied -> exit 1
        with patch(
            "sys.argv",
            [
                "collect_public_repro_inventory.py",
                "--check-only",
                "--expected-public-manifest-sha256",
                EXPECTED_PUBLIC_MANIFEST_SHA256,
            ],
        ):
            assert main() == 1

        # 3. Only bundle anchor supplied -> exit 1
        with patch(
            "sys.argv",
            [
                "collect_public_repro_inventory.py",
                "--check-only",
                "--expected-bundle-sha256",
                EXPECTED_BUNDLE_SHA256,
            ],
        ):
            assert main() == 1

        # 4. Both valid authorities supplied via bundle anchor -> exit 0
        with patch(
            "sys.argv",
            [
                "collect_public_repro_inventory.py",
                "--check-only",
                "--expected-bundle-sha256",
                EXPECTED_BUNDLE_SHA256,
                "--expected-public-manifest-sha256",
                EXPECTED_PUBLIC_MANIFEST_SHA256,
            ],
        ):
            assert main() == 0

        # 5. Both valid authorities supplied via root freeze anchor -> exit 0
        with patch(
            "sys.argv",
            [
                "collect_public_repro_inventory.py",
                "--check-only",
                "--expected-freeze-envelope-sha256",
                EXPECTED_FREEZE_ENVELOPE_SHA256,
                "--expected-public-manifest-sha256",
                EXPECTED_PUBLIC_MANIFEST_SHA256,
            ],
        ):
            assert main() == 0

        # 6. Both supplied but bundle digest corrupted -> exit 1
        with patch(
            "sys.argv",
            [
                "collect_public_repro_inventory.py",
                "--check-only",
                "--expected-bundle-sha256",
                "0" * 64,
                "--expected-public-manifest-sha256",
                EXPECTED_PUBLIC_MANIFEST_SHA256,
            ],
        ):
            assert main() == 1

    def test_prose_and_table_dynamic_generation_on_log_mutation(self, inventory: dict, tmp_path: Path) -> None:
        """Verify that mutating artifacts dynamically regenerates both markdown prose and tables without hardcoded strings."""
        import copy

        plan_path = REPO_ROOT / "reports/evidence/public_repro_derivation_plan_20261003.md"
        tmp_plan = tmp_path / "plan.md"
        tmp_plan.write_text(plan_path.read_text(encoding="utf-8"), encoding="utf-8")

        mutated_inv = copy.deepcopy(inventory)
        for art in mutated_inv["artifacts"]:
            if art["classification"] == "terminal_log":
                art["file_bytes"] = 1142
                art["sha256"] = "1111111111111111111111111111111111111111111111111111111111111111"
            elif art["classification"] == "terminal_seal":
                art["file_bytes"] = 3047
                art["sha256"] = "2222222222222222222222222222222222222222222222222222222222222222"

        # First update
        update_plan_markdown(tmp_plan, mutated_inv)
        first_content = tmp_plan.read_text(encoding="utf-8")

        # Factual prose and table must reflect mutated values
        assert "1,142" in first_content
        assert "1111111111111111111111111111111111111111111111111111111111111111" in first_content
        assert "3,047" in first_content
        assert "2222222222222222222222222222222222222222222222222222222222222222" in first_content

        # Stale values must be completely purged from both table and prose
        assert "1,141" not in first_content
        assert "fcacacf6" not in first_content
        assert "3,046" not in first_content
        assert "ae7a9ada" not in first_content

        # Second update must be strictly idempotent
        update_plan_markdown(tmp_plan, mutated_inv)
        second_content = tmp_plan.read_text(encoding="utf-8")
        assert second_content == first_content
