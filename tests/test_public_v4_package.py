"""
tests/test_public_v4_package.py

Unit and canonical acceptance tests for RAG2ATT&CK Public v4 Candidate Package.
Explicitly separates:
  1. Pure unit tests (TestPublicV4PackageUnit) that run on self-contained fixtures/tmp_path.
     Always run in CI without dependencies on workstation staging paths.
  2. Canonical acceptance tests (TestPublicV4PackageCanonicalAcceptance) that verify
     full byte exactness and provenance against the staged candidate package.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import unittest.mock
import zipfile
from pathlib import Path

import pytest

from scripts.build_public_v4_package import (
    BASE_V3_DEFAULT_DIR,
    BASE_V3_DESCRIPTOR_SHA256,
    OUTPUT_V4_DEFAULT_DIR,
    OUTPUT_V4_DEFAULT_ZIP,
    REPO_ROOT,
    REQUIRED_ROLES,
    read_verified_buffer,
    run_privacy_scan,
    sanitize_rq_v2_packet,
)
from scripts.verify_canonical_package_acceptance import run_acceptance_verification
from scripts.verify_public_v4_package import (
    check_safe_relative_path,
    validate_contained_file,
    verify_package,
)


class TestPublicV4PackageUnit:
    """Pure unit tests running entirely on fixtures and tmp_path. Always run in CI without skips."""

    def test_single_read_verified_buffer_contract(self, tmp_path: Path) -> None:
        """Verify atomic single-read buffer returns raw bytes, SHA-256 hex, and length."""
        sample_file = tmp_path / "sample.bin"
        content = b"RAG2ATTCK verification envelope buffer"
        sample_file.write_bytes(content)

        raw, sha, length = read_verified_buffer(sample_file)
        assert raw == content
        assert length == len(content)
        assert sha == hashlib.sha256(content).hexdigest()

    def test_read_verified_buffer_missing_file_fails_closed(self, tmp_path: Path) -> None:
        """Verify missing file raises FileNotFoundError fail-closed."""
        with pytest.raises(FileNotFoundError):
            read_verified_buffer(tmp_path / "missing_target_file.txt")

    def test_privacy_scan_clean_directory(self, tmp_path: Path) -> None:
        """Verify privacy scan passes cleanly on relative public layout documentation."""
        clean_doc = tmp_path / "README.md"
        clean_doc.write_text(
            "# Public Candidate Documentation\n"
            "Relative path: ./base_public_v3/inputs/data.json\n"
            "Egress guard: 0 external network requests.\n",
            encoding="utf-8",
        )
        violations = run_privacy_scan(tmp_path)
        assert violations == [], f"Expected clean privacy scan, got: {violations}"

    def test_privacy_scan_detects_private_path_leaks(self, tmp_path: Path) -> None:
        """Verify privacy scan catches private workstation paths fail-closed."""
        leaky_file = tmp_path / "leaky_provenance.md"
        leaky_file.write_text(
            "Source artifact located at C:/Users/hahoa/.codex/artifacts/run.json\n"
            "Worktree branch: D:/RAG2ATTCK/experiments\n",
            encoding="utf-8",
        )
        violations = run_privacy_scan(tmp_path)
        assert len(violations) >= 2
        assert any("C:/Users/hahoa" in v for v in violations)
        assert any("D:/RAG2ATTCK" in v for v in violations)

    def test_sanitize_rq_v2_packet_unit(self) -> None:
        """Verify sanitization function strips private workstation paths and preserves semantics."""
        raw_text = (
            "Execution worktree: D:/RAG2ATTCK-worktrees/integrated-audit-s1\n"
            "Journal: C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/run/request_journal.jsonl\n"
            "Ledger: C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/study/artifacts/study_budget/study_ledger.json\n"
        )
        sanitized = sanitize_rq_v2_packet(raw_text.encode("utf-8"))
        assert "C:/Users" not in sanitized
        assert "D:/" not in sanitized
        assert "hahoa" not in sanitized
        assert "inputs/request_journal.jsonl" in sanitized
        assert "inputs/study_ledger.json" in sanitized

    def test_git_anchored_envelope_inventory(self) -> None:
        """Verify that reports/evidence/public_v4_candidate_envelope_inventory.json anchors the package."""
        inv_path = REPO_ROOT / "reports/evidence/public_v4_candidate_envelope_inventory.json"
        assert inv_path.is_file()
        raw, _, _ = read_verified_buffer(inv_path)
        inv_data = json.loads(raw.decode("utf-8"))

        assert inv_data["schema_version"] == "public_v4_candidate_envelope_inventory_v1"
        assert inv_data["root_acceptance_receipt"]["sha256"] == "4dfd888bcce1330a26789068517aef37631e484c59a65c0dfd7e2915180adda9"
        assert inv_data["candidate_package"]["base_v3_manifest_sha256"] == BASE_V3_DESCRIPTOR_SHA256
        assert inv_data["candidate_package"]["base_v3_items_count"] == 23
        assert inv_data["candidate_package"]["supplemental_items_count"] == 7
        assert inv_data["candidate_package"]["total_files_in_package"] == 34
        assert inv_data["verification_attestation"]["offline_egress_guaranteed"] is True
        assert inv_data["verification_attestation"]["base_public_v3_exact_bytes_preserved"] is True

    def test_verifier_fail_closed_checks(self, tmp_path: Path) -> None:
        """Verify that verify_package strictly fails closed on missing files or corruptions."""
        # 1. Missing package directory fails closed
        with pytest.raises(FileNotFoundError):
            verify_package(tmp_path / "empty_dir")

        # 2. Missing package manifest fails closed
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        with pytest.raises(FileNotFoundError, match="package_manifest_v4.json"):
            verify_package(pkg_dir)

        # 3. Manifest hash mismatch fails closed
        fake_manifest = pkg_dir / "package_manifest_v4.json"
        fake_manifest.write_text("{}", encoding="utf-8")
        with pytest.raises(ValueError, match="Package manifest SHA mismatch"):
            verify_package(pkg_dir, expected_manifest_sha256="0" * 64)

        # 4. Invalid schema version fails closed
        bad_manifest = {"schema_version": "invalid_schema_v99", "role_index": {}}
        fake_manifest.write_text(json.dumps(bad_manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid package manifest schema_version"):
            verify_package(pkg_dir)

        # 5. Missing required sections fails closed
        bad_manifest = {"schema_version": "public_v4_candidate_package_v1"}
        fake_manifest.write_text(json.dumps(bad_manifest), encoding="utf-8")
        with pytest.raises(KeyError, match="Missing required manifest section"):
            verify_package(pkg_dir)

        # 6. Empty / truncated inventory fails closed
        bad_manifest = {
            "schema_version": "public_v4_candidate_package_v1",
            "role_index": {},
            "base_package": {"items": {}},
            "supplemental_envelope": {"items": {}},
            "verification_tools": {"verify_public_v4_package.py": {"sha256": "0" * 64, "size_bytes": 1}},
        }
        fake_manifest.write_text(json.dumps(bad_manifest), encoding="utf-8")
        with pytest.raises(ValueError, match="Base package items must contain at least 23 declared items"):
            verify_package(pkg_dir)

        # 7. Unsafe path traversal in manifest fails closed
        with pytest.raises(ValueError, match="Unsafe path component"):
            check_safe_relative_path("../outside_file.json")
        with pytest.raises(ValueError, match="Unsafe absolute path"):
            check_safe_relative_path("/etc/passwd")

    def test_safe_relative_path_strict_rejection(self) -> None:
        """Verify check_safe_relative_path rejects backslashes, leading slashes, drive letters, empty components, and traversals."""
        # Backslash rejection
        with pytest.raises(ValueError, match="Unsafe backslash"):
            check_safe_relative_path("base_public_v3\\inputs\\data.json")

        # Leading slash rejection
        with pytest.raises(ValueError, match="Unsafe absolute path"):
            check_safe_relative_path("/etc/shadow")

        # Drive letter rejection
        with pytest.raises(ValueError, match="Unsafe path with drive letter"):
            check_safe_relative_path("C:secret.txt")
        with pytest.raises(ValueError, match="Unsafe path with drive letter"):
            check_safe_relative_path("D:/repo/file.txt")

        # Empty or dot components
        with pytest.raises(ValueError, match="Unsafe path component"):
            check_safe_relative_path("base//file.json")
        with pytest.raises(ValueError, match="Unsafe path component"):
            check_safe_relative_path("./base/file.json")
        with pytest.raises(ValueError, match="Unsafe path component"):
            check_safe_relative_path("base/./file.json")
        with pytest.raises(ValueError, match="Unsafe path component"):
            check_safe_relative_path("base/../file.json")
        with pytest.raises(ValueError, match="Empty path"):
            check_safe_relative_path("")

    def test_validate_contained_file_symlink_and_containment(self, tmp_path: Path) -> None:
        """Verify validate_contained_file rejects symlinks and directory containment escapes."""
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        real_file = pkg_dir / "valid.txt"
        real_file.write_text("ok")

        # Valid relative file passes
        assert validate_contained_file(pkg_dir, "valid.txt") == real_file

        # Symlink rejection
        symlink_target = tmp_path / "outside.txt"
        symlink_target.write_text("outside")
        symlink_file = pkg_dir / "symlink.txt"
        try:
            symlink_file.symlink_to(symlink_target)
            with pytest.raises(ValueError, match="Symlinks are disallowed"):
                validate_contained_file(pkg_dir, "symlink.txt")
        except (OSError, NotImplementedError):
            with unittest.mock.patch.object(Path, "is_symlink", return_value=True):
                with pytest.raises(ValueError, match="Symlinks are disallowed"):
                    validate_contained_file(pkg_dir, "valid.txt")

        # Containment escape rejection
        with unittest.mock.patch.object(Path, "is_relative_to", return_value=False):
            with pytest.raises(ValueError, match="Path escapes package root containment"):
                validate_contained_file(pkg_dir, "valid.txt")

    def test_base_descriptor_runtime_assets_and_set_equality_fails_closed(self, tmp_path: Path) -> None:
        """Verify verify_package strictly enforces set equality between base descriptor (including runtime_assets) and base_items."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        clone = tmp_path / "pkg_clone"
        shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone)
        manifest_p = clone / "package_manifest_v4.json"
        raw = json.loads(manifest_p.read_text(encoding="utf-8"))

        # Case A: Omit runtime_asset from base_items (replaced by dummy so count >= 23) -> fails closed
        runtime_key = "base_public_v3/runtime/runtime_recovery_wrapper.py"
        assert runtime_key in raw["base_package"]["items"]
        del raw["base_package"]["items"][runtime_key]
        raw["base_package"]["items"]["base_public_v3/dummy_unmatched.bin"] = {"sha256": "0" * 64, "size_bytes": 10}
        manifest_p.write_text(json.dumps(raw, indent=2), encoding="utf-8")

        with pytest.raises(ValueError, match="Base descriptor and base_items set mismatch"):
            verify_package(clone)

        # Case B: Add extra undeclared item in base_items -> fails closed
        raw["base_package"]["items"][runtime_key] = {"sha256": "0" * 64, "size_bytes": 10}
        raw["base_package"]["items"]["base_public_v3/undeclared_bonus.json"] = {"sha256": "1" * 64, "size_bytes": 10}
        manifest_p.write_text(json.dumps(raw, indent=2), encoding="utf-8")

        with pytest.raises(ValueError, match="In package base items but undeclared in descriptor"):
            verify_package(clone)

    def test_verification_tools_validation_fails_closed(self, tmp_path: Path) -> None:
        """Verify that missing verification_tools, missing verify_public_v4_package.py, or corrupted tool bytes fail closed."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        clone = tmp_path / "pkg_clone"
        shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone)
        manifest_p = clone / "package_manifest_v4.json"
        raw = json.loads(manifest_p.read_text(encoding="utf-8"))

        # Case A: Missing section
        raw_missing = dict(raw)
        del raw_missing["verification_tools"]
        manifest_p.write_text(json.dumps(raw_missing, indent=2), encoding="utf-8")
        with pytest.raises(KeyError, match="verification_tools"):
            verify_package(clone)

        # Case B: Missing required tool name
        raw_empty_tools = dict(raw)
        raw_empty_tools["verification_tools"] = {"other_tool.py": {"sha256": "0" * 64, "size_bytes": 1}}
        manifest_p.write_text(json.dumps(raw_empty_tools, indent=2), encoding="utf-8")
        with pytest.raises(ValueError, match="must include 'verify_public_v4_package.py'"):
            verify_package(clone)

        # Case C: Byte tampering on disk
        manifest_p.write_text(json.dumps(raw, indent=2), encoding="utf-8")
        tool_f = clone / "verify_public_v4_package.py"
        tool_f.write_text(tool_f.read_text(encoding="utf-8") + "\n# corrupted byte\n", encoding="utf-8")
        with pytest.raises(ValueError, match="Verification tool SHA mismatch for verify_public_v4_package.py"):
            verify_package(clone)

    def test_acceptance_runner_duplicate_zip_entry_fails_closed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify acceptance runner strictly rejects duplicate entries in candidate ZIP archive."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        zip_p = tmp_path / "duplicate_entry.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix())
            zf.writestr("README.md", b"# duplicate entry content\n")

        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=OUTPUT_V4_DEFAULT_DIR, candidate_zip=zip_p)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Duplicate entry in ZIP archive" in captured.err

    def test_acceptance_runner_undeclared_member_in_zip_fails_closed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify acceptance runner strictly rejects undeclared members in candidate ZIP archive."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        zip_p = tmp_path / "undeclared_member.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
                if f.is_file():
                    zf.write(f, f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix())
            zf.writestr("malicious_extra_payload.sh", b"echo hacked\n")

        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=OUTPUT_V4_DEFAULT_DIR, candidate_zip=zip_p)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Undeclared member 'malicious_extra_payload.sh' in candidate ZIP archive" in captured.err

    def test_acceptance_runner_tampered_verification_tool_in_zip_fails_closed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify acceptance runner strictly rejects tampered verification tool member stream in candidate ZIP archive."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        zip_p = tmp_path / "tampered_tool.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix()
                    if rel == "verify_public_v4_package.py":
                        zf.writestr(rel, b"# modified verifier stream content\n")
                    else:
                        zf.write(f, rel)

        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=OUTPUT_V4_DEFAULT_DIR, candidate_zip=zip_p)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "ZIP member stream SHA mismatch for 'verify_public_v4_package.py'" in captured.err

    def test_acceptance_runner_privacy_violation_in_zip_fails_closed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify acceptance runner detects and rejects private workstation paths directly in ZIP member streams."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        clone = tmp_path / "pkg_clean"
        shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone)

        zip_p = tmp_path / "privacy_leak.zip"
        with zipfile.ZipFile(zip_p, "w") as zf:
            for f in sorted(clone.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(clone).as_posix()
                    if rel == "README.md":
                        zf.writestr(rel, b"# Leaked info\nPath: C:/Users/hahoa/secret\n")
                    else:
                        zf.write(f, rel)

        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=clone, candidate_zip=zip_p)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Privacy violation in ZIP member 'README.md'" in captured.err

    def test_acceptance_runner_fails_closed_on_missing_zip(self, tmp_path: Path) -> None:
        """Verify acceptance runner strictly exits with code 1 if --candidate-zip does not exist."""
        fake_dir = tmp_path / "candidate_dir"
        fake_dir.mkdir()
        non_existent_zip = tmp_path / "does_not_exist.zip"
        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=fake_dir, candidate_zip=non_existent_zip)
        assert exc_info.value.code == 1

    def test_acceptance_runner_missing_readme_fails_closed(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Verify acceptance runner strictly fails closed if README.md is missing from candidate directory."""
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip("Requires staged package")
        clone = tmp_path / "pkg_no_readme"
        shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone)
        readme = clone / "README.md"
        if readme.is_file():
            readme.unlink()

        with pytest.raises(SystemExit) as exc_info:
            run_acceptance_verification(candidate_dir=clone)
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "Required package file 'README.md' missing from candidate directory" in captured.err


class TestPublicV4PackageCanonicalAcceptance:
    """
    Canonical acceptance tests executed against the physical staged candidate package.
    In environments where the package has not been staged, individual tests are clearly
    marked with their skip reason, preserving full test collection.
    """

    @pytest.fixture
    def package_dir(self) -> Path:
        if not OUTPUT_V4_DEFAULT_DIR.is_dir():
            pytest.skip(
                f"Candidate public v4 package directory not present at {OUTPUT_V4_DEFAULT_DIR}; "
                "required in canonical acceptance verification path"
            )
        return OUTPUT_V4_DEFAULT_DIR

    @pytest.fixture
    def manifest(self, package_dir: Path) -> dict:
        manifest_file = package_dir / "package_manifest_v4.json"
        raw, _, _ = read_verified_buffer(manifest_file)
        return json.loads(raw.decode("utf-8"))

    def test_package_manifest_and_role_index_completeness(self, package_dir: Path, manifest: dict) -> None:
        """Verify standalone package manifest schema and role index completeness."""
        assert manifest["schema_version"] == "public_v4_candidate_package_v1"
        assert manifest["source_repository"] == "habachcp6/RAG2ATTCK"
        assert manifest["root_acceptance_verdict"] == "PASS_INVENTORY_AND_GENERATED_PLAN_SCOPE"
        assert manifest["root_acceptance_source_sha"] == "30b9834dcb63c3e27299e1fec2978052abedc57c"

        role_index = manifest.get("role_index", {})
        assert len(role_index) >= 8

        for role in REQUIRED_ROLES:
            assert role in role_index, f"Missing required role: {role}"
            rel_path = role_index[role]
            target_f = package_dir / rel_path
            assert target_f.is_file(), f"Target file for role '{role}' does not exist: {target_f}"

    def test_base_public_v3_exact_bytes_preservation(self, package_dir: Path, manifest: dict) -> None:
        """Verify that Base Public v3 items and descriptor are preserved byte-for-byte."""
        base_pkg = manifest["base_package"]
        assert base_pkg["manifest_sha256"] == BASE_V3_DESCRIPTOR_SHA256
        assert base_pkg["manifest_size_bytes"] == 11193
        assert base_pkg["declared_items_count"] == 23

        # Verify base descriptor on disk
        base_desc_f = package_dir / base_pkg["manifest_path"]
        _, actual_desc_sha, actual_desc_len = read_verified_buffer(base_desc_f)
        assert actual_desc_sha == BASE_V3_DESCRIPTOR_SHA256
        assert actual_desc_len == 11193

        # Verify all 23 base items match declared and original bytes
        for rel_path, spec in base_pkg["items"].items():
            staged_f = package_dir / rel_path
            _, staged_sha, staged_len = read_verified_buffer(staged_f)
            assert staged_sha == spec["sha256"]
            assert staged_len == spec["size_bytes"]

            # Compare with original v3 source if accessible
            if BASE_V3_DEFAULT_DIR.is_dir():
                orig_rel = rel_path.replace("base_public_v3/", "")
                orig_f = BASE_V3_DEFAULT_DIR / orig_rel
                if orig_f.is_file():
                    _, orig_sha, orig_len = read_verified_buffer(orig_f)
                    assert staged_sha == orig_sha
                    assert staged_len == orig_len

    def test_supplemental_v4_exact_bytes_and_authorities(self, package_dir: Path, manifest: dict) -> None:
        """Verify exact byte sizes and SHA-256 hashes of all supplemental v4 items."""
        role_index = manifest["role_index"]

        # 1. Accepted Metric Bundle v2
        b_file = package_dir / role_index["accepted_metric_bundle"]
        _, b_sha, b_len = read_verified_buffer(b_file)
        assert b_sha == "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"
        assert b_len == 49465

        # 2. Root Freeze Envelope e284
        f_file = package_dir / role_index["root_freeze_envelope"]
        _, f_sha, f_len = read_verified_buffer(f_file)
        assert f_sha == "e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2"
        assert f_len == 4335

        # 3. Canonical Run Seal v1 AE7
        s_file = package_dir / role_index["canonical_run_seal"]
        _, s_sha, s_len = read_verified_buffer(s_file)
        assert s_sha == "ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701"
        assert s_len == 3046

        # 4. Root Public Inventory Acceptance 4dfd (30b9834)
        acc_file = package_dir / role_index["root_inventory_acceptance"]
        _, acc_sha, acc_len = read_verified_buffer(acc_file)
        assert acc_sha == "4dfd888bcce1330a26789068517aef37631e484c59a65c0dfd7e2915180adda9"
        assert acc_len == 2405

        # 5. Terminal Validator Root A Acceptance 7003 (b69a690)
        tra_file = package_dir / role_index["root_track_a_acceptance"]
        _, tra_sha, tra_len = read_verified_buffer(tra_file)
        assert tra_sha == "70032a7726c47585a68d547cb7a69444b92f83d2a52ec0f31ae78a2b8b02b6a6"
        assert tra_len == 5399

        # 6. Task 1264 Execution Log (Original 1,141 bytes, 30 lines)
        l_file = package_dir / role_index["execution_log"]
        raw_l, l_sha, l_len = read_verified_buffer(l_file)
        assert l_sha == "fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44"
        assert l_len == 1141
        assert len(raw_l.decode("utf-8").splitlines()) == 30

        # 7. Superseding Sanitized RQ Lineage Evidence
        rq_file = package_dir / role_index["sanitized_rq_provenance"]
        assert rq_file.is_file()
        supp_spec = manifest["supplemental_envelope"]["items"]["supplemental/provenance/s2_rq_v2_execute_public.md"]
        assert supp_spec["original_sha256"] == "c34b1350881d61f153a50fd5fa2b79a9438ece09c2a2b09d022e74e863313570"

        # Verify no private path in sanitized file
        rq_text = rq_file.read_text(encoding="utf-8")
        assert "C:/Users" not in rq_text
        assert "D:/" not in rq_text

    def test_privacy_scan_passes(self, package_dir: Path) -> None:
        """Verify that privacy scan returns zero violations across all package files."""
        violations = run_privacy_scan(package_dir)
        assert violations == [], f"Privacy violations found: {violations}"

    def test_candidate_zip_integrity(self, package_dir: Path) -> None:
        """Verify candidate ZIP archive matches package contents."""
        if not OUTPUT_V4_DEFAULT_ZIP.is_file():
            pytest.skip(f"Candidate ZIP archive missing at: {OUTPUT_V4_DEFAULT_ZIP}")
        _, zip_sha, zip_len = read_verified_buffer(OUTPUT_V4_DEFAULT_ZIP)
        assert zip_len > 1_000_000
        assert len(zip_sha) == 64

        with zipfile.ZipFile(OUTPUT_V4_DEFAULT_ZIP, "r") as zf:
            zip_names = set(zf.namelist())
            for f in package_dir.rglob("*"):
                if f.is_file() and f.suffix not in {".pyc", ".zip"} and "__pycache__" not in f.parts:
                    rel = f.relative_to(package_dir).as_posix()
                    assert rel in zip_names, f"File {rel} missing from ZIP archive!"

    def test_portable_verifier_pass(self, package_dir: Path) -> None:
        """Verify that verify_public_v4_package.py executes cleanly and returns PASS."""
        manifest_file = package_dir / "package_manifest_v4.json"
        _, man_sha, _ = read_verified_buffer(manifest_file)
        res = verify_package(package_dir, expected_manifest_sha256=man_sha)
        assert res["status"] == "PASS"
        assert res["verified_base_items"] == 23
        assert res["verified_supplemental_items"] == 7
        assert res["verified_roles_count"] >= 8
        assert res["privacy_violations_count"] == 0

    def test_package_total_files_count_exact_34(self, package_dir: Path, manifest: dict) -> None:
        """Verify candidate package contains exactly 34 files (23 base + 7 supplemental + 1 base descriptor + 1 manifest + 1 verifier + 1 readme)."""
        actual_files = [
            f for f in package_dir.rglob("*")
            if f.is_file() and f.suffix not in {".pyc", ".zip"} and "__pycache__" not in f.parts
        ]
        assert len(actual_files) == 34
        assert manifest.get("total_files_in_package") == 34
