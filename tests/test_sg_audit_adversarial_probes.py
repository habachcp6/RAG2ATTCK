#!/usr/bin/env python3
"""
tests/test_sg_audit_adversarial_probes.py

Independent Adversarial Probe Suite (SG-AUDIT) for RAG2ATT&CK Public v4 Package.
Empirically proves that F05-A / F05-B defensive controls fail closed against
hostile, corrupted, malformed, leaked, or out-of-bounds package fixtures.

Covers all 9 independent audit probes:
  - Probe 1: 1-byte verification tool tampering on disk rejected by verify_package
  - Probe 2: Member stream tampering in ZIP rejected by acceptance verification
  - Probe 3: Duplicate entry in ZIP infolist rejected fail-closed
  - Probe 4: Undeclared member in ZIP rejected fail-closed
  - Probe 5: Private workstation path leak in ZIP rejected fail-closed
  - Probe 6: Substitution of runtime_recovery_wrapper rejected by descriptor set mismatch
  - Probe 7: Path traversal, backslash, drive, dot, and empty components rejected by check_safe_relative_path
  - Probe 8: Symlink and directory escape rejected fail-closed by validate_contained_file
  - Probe 9: Acceptance verification on production candidate package passes cleanly with zero violations
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest.mock
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Ensure utf-8 encoding on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_public_v4_package import (
    BASE_V3_DESCRIPTOR_SHA256,
    OUTPUT_V4_DEFAULT_DIR,
    OUTPUT_V4_DEFAULT_ZIP,
    read_verified_buffer,
)
from scripts.verify_public_v4_package import (
    check_safe_relative_path,
    validate_contained_file,
    verify_package,
)
from scripts.verify_canonical_package_acceptance import run_acceptance_verification


class AuditProbeResult:
    """Structured record of an adversarial probe outcome."""

    def __init__(self, probe_id: int, name: str, description: str):
        self.probe_id = probe_id
        self.name = name
        self.description = description
        self.passed = False
        self.failure_mode: str = ""
        self.observed_error: str = ""
        self.exit_code: int | None = None
        self.details: Dict[str, Any] = {}

    def mark_pass(self, failure_mode: str, observed_error: str, exit_code: int | None = None, **details: Any) -> None:
        self.passed = True
        self.failure_mode = failure_mode
        self.observed_error = observed_error
        self.exit_code = exit_code
        self.details = details

    def mark_fail(self, reason: str) -> None:
        self.passed = False
        self.observed_error = reason


def execute_probe_1(tmp_path: Path) -> AuditProbeResult:
    """Probe 1: Tamper verification tool on disk by 1 byte -> verify_package must fail closed."""
    res = AuditProbeResult(
        1,
        "Tool Disk Byte Tampering",
        "Tamper verify_public_v4_package.py on disk (1 byte change) -> verify_package must FAIL (SHA mismatch)",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir():
        res.mark_fail("Candidate directory not found")
        return res

    clone_dir = tmp_path / "probe1_pkg"
    shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone_dir)

    tool_path = clone_dir / "verify_public_v4_package.py"
    original_bytes = tool_path.read_bytes()
    # Flip the last byte or append a byte
    tampered_bytes = original_bytes + b"\n# audit probe 1 byte tamper\n"
    tool_path.write_bytes(tampered_bytes)

    try:
        verify_package(clone_dir)
        res.mark_fail("verify_package succeeded unexpectedly despite tampered verification tool")
    except ValueError as exc:
        err_msg = str(exc)
        if "Verification tool SHA mismatch for verify_public_v4_package.py" in err_msg:
            res.mark_pass(
                failure_mode="ValueError: Tool SHA mismatch",
                observed_error=err_msg,
                tampered_file="verify_public_v4_package.py",
                original_sha=hashlib.sha256(original_bytes).hexdigest(),
                tampered_sha=hashlib.sha256(tampered_bytes).hexdigest(),
            )
        else:
            res.mark_fail(f"Unexpected ValueError message: {err_msg}")
    except Exception as exc:
        res.mark_fail(f"Unexpected exception type {type(exc)}: {exc}")

    return res


def execute_probe_2(tmp_path: Path) -> AuditProbeResult:
    """Probe 2: Tamper verify_public_v4_package.py in ZIP member stream -> acceptance verification must fail closed."""
    res = AuditProbeResult(
        2,
        "ZIP Member Stream Tampering",
        "Tamper verify_public_v4_package.py in member stream of ZIP -> acceptance verification must FAIL (member stream SHA mismatch)",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir() or not OUTPUT_V4_DEFAULT_ZIP.is_file():
        res.mark_fail("Candidate package or zip not found")
        return res

    tampered_zip = tmp_path / "probe2_tampered.zip"
    with zipfile.ZipFile(OUTPUT_V4_DEFAULT_ZIP, "r") as src_zf, zipfile.ZipFile(tampered_zip, "w") as dst_zf:
        for item in src_zf.infolist():
            content = src_zf.read(item.filename)
            if item.filename == "verify_public_v4_package.py":
                content = content + b"\n# hostile member stream modification\n"
            dst_zf.writestr(item.filename, content)

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/verify_canonical_package_acceptance.py"),
        "--candidate-dir",
        str(OUTPUT_V4_DEFAULT_DIR),
        "--candidate-zip",
        str(tampered_zip),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 1 and "ZIP member stream SHA mismatch for 'verify_public_v4_package.py'" in proc.stderr:
        res.mark_pass(
            failure_mode="FAIL / BLOCKED: Member stream SHA mismatch",
            observed_error=proc.stderr.strip(),
            exit_code=proc.returncode,
        )
    else:
        res.mark_fail(
            f"Expected exit code 1 and member stream mismatch; got rc={proc.returncode}, stderr={proc.stderr}"
        )

    return res


def execute_probe_3(tmp_path: Path) -> AuditProbeResult:
    """Probe 3: Duplicate filename entry in ZIP -> acceptance verification must fail closed at infolist reading."""
    res = AuditProbeResult(
        3,
        "Duplicate ZIP Entry",
        "Create ZIP with 2 duplicate filenames -> acceptance verification must FAIL CLOSED at infolist reading",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir():
        res.mark_fail("Candidate directory not found")
        return res

    dup_zip = tmp_path / "probe3_duplicate.zip"
    with zipfile.ZipFile(dup_zip, "w") as zf:
        # Write valid files
        for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix())
        # Inject duplicate entry
        zf.writestr("README.md", b"# duplicate entry collision attack\n")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/verify_canonical_package_acceptance.py"),
        "--candidate-dir",
        str(OUTPUT_V4_DEFAULT_DIR),
        "--candidate-zip",
        str(dup_zip),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 1 and "Duplicate entry in ZIP archive: 'README.md'" in proc.stderr:
        res.mark_pass(
            failure_mode="FAIL / BLOCKED: Duplicate entry in ZIP archive",
            observed_error=proc.stderr.strip(),
            exit_code=proc.returncode,
        )
    else:
        res.mark_fail(f"Expected duplicate entry rejection; got rc={proc.returncode}, stderr={proc.stderr}")

    return res


def execute_probe_4(tmp_path: Path) -> AuditProbeResult:
    """Probe 4: Undeclared member in ZIP -> acceptance verification must fail closed."""
    res = AuditProbeResult(
        4,
        "Undeclared ZIP Member",
        "Add undeclared member (extra_file.txt) to ZIP -> acceptance verification must FAIL CLOSED (Undeclared member)",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir():
        res.mark_fail("Candidate directory not found")
        return res

    extra_zip = tmp_path / "probe4_extra.zip"
    with zipfile.ZipFile(extra_zip, "w") as zf:
        for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix())
        # Inject undeclared member
        zf.writestr("extra_file.txt", b"malicious undeclared attachment\n")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/verify_canonical_package_acceptance.py"),
        "--candidate-dir",
        str(OUTPUT_V4_DEFAULT_DIR),
        "--candidate-zip",
        str(extra_zip),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 1 and "Undeclared member 'extra_file.txt' in candidate ZIP archive" in proc.stderr:
        res.mark_pass(
            failure_mode="FAIL / BLOCKED: Undeclared member",
            observed_error=proc.stderr.strip(),
            exit_code=proc.returncode,
        )
    else:
        res.mark_fail(f"Expected undeclared member rejection; got rc={proc.returncode}, stderr={proc.stderr}")

    return res


def execute_probe_5(tmp_path: Path) -> AuditProbeResult:
    """Probe 5: Private workstation path leak in ZIP -> acceptance verification must fail closed."""
    res = AuditProbeResult(
        5,
        "Private Workstation Path Leak",
        "Add member with private workstation path (C:\\Users\\fake\\test.txt) to ZIP -> acceptance verification must FAIL CLOSED",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir():
        res.mark_fail("Candidate directory not found")
        return res

    leak_zip = tmp_path / "probe5_leak.zip"
    with zipfile.ZipFile(leak_zip, "w") as zf:
        for f in sorted(OUTPUT_V4_DEFAULT_DIR.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(OUTPUT_V4_DEFAULT_DIR).as_posix())
        # Inject strange / foreign file with private workstation path
        zf.writestr("fake_leak.txt", b"# Leaked info\nWorkstation path: C:\\Users\\fake\\test.txt\n")

    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/verify_canonical_package_acceptance.py"),
        "--candidate-dir",
        str(OUTPUT_V4_DEFAULT_DIR),
        "--candidate-zip",
        str(leak_zip),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode == 1 and "Privacy violation in ZIP member 'fake_leak.txt'" in proc.stderr and "Private path 'C:\\Users\\fake" in proc.stderr:
        res.mark_pass(
            failure_mode="FAIL / BLOCKED: Privacy violation in ZIP member",
            observed_error=proc.stderr.strip(),
            exit_code=proc.returncode,
        )
    else:
        res.mark_fail(f"Expected privacy violation rejection; got rc={proc.returncode}, stderr={proc.stderr}")

    return res


def execute_probe_6(tmp_path: Path) -> AuditProbeResult:
    """Probe 6: Swap runtime_recovery_wrapper.py with another file -> verify_package fails closed on descriptor mismatch."""
    res = AuditProbeResult(
        6,
        "Base Descriptor Set Mismatch (Runtime Assets)",
        "Keep 23 items but replace runtime_recovery_wrapper.py with another file -> verify_package must FAIL (set mismatch)",
    )
    if not OUTPUT_V4_DEFAULT_DIR.is_dir():
        res.mark_fail("Candidate directory not found")
        return res

    clone_dir = tmp_path / "probe6_pkg"
    shutil.copytree(OUTPUT_V4_DEFAULT_DIR, clone_dir)

    manifest_path = clone_dir / "package_manifest_v4.json"
    man_data = json.loads(manifest_path.read_text(encoding="utf-8"))

    runtime_key = "base_public_v3/runtime/runtime_recovery_wrapper.py"
    assert runtime_key in man_data["base_package"]["items"]
    del man_data["base_package"]["items"][runtime_key]
    man_data["base_package"]["items"]["base_public_v3/runtime/replacement_dummy.py"] = {
        "sha256": "0" * 64,
        "size_bytes": 123,
    }
    manifest_path.write_text(json.dumps(man_data, indent=2), encoding="utf-8")

    try:
        verify_package(clone_dir)
        res.mark_fail("verify_package succeeded unexpectedly despite missing runtime asset in base items")
    except ValueError as exc:
        err_msg = str(exc)
        if (
            "Base descriptor and base_items set mismatch" in err_msg
            and "base_public_v3/runtime/runtime_recovery_wrapper.py" in err_msg
        ):
            res.mark_pass(
                failure_mode="ValueError: Base descriptor and base_items set mismatch",
                observed_error=err_msg,
            )
        else:
            res.mark_fail(f"Unexpected ValueError message: {err_msg}")
    except Exception as exc:
        res.mark_fail(f"Unexpected exception type: {exc}")

    return res


def execute_probe_7() -> AuditProbeResult:
    """Probe 7: Verify check_safe_relative_path strictly rejects traversal, backslashes, drive letters, and invalid components."""
    res = AuditProbeResult(
        7,
        "check_safe_relative_path Rejection",
        "Test check_safe_relative_path with traversal/drive/dot/empty patterns: all MUST be rejected (raise ValueError)",
    )
    test_cases = [
        ("C:\\outside\\file.json", "Unsafe backslash in package manifest path"),
        ("..\\outside\\file.json", "Unsafe backslash in package manifest path"),
        ("/etc/passwd", "Unsafe absolute path starting with '/'"),
        ("../../escape", "Unsafe path component '..'"),
        ("sub/./file", "Unsafe path component '.'"),
        ("sub//file", "Unsafe path component ''"),
    ]

    all_passed = True
    probe_details = {}
    for path_str, expected_sub in test_cases:
        try:
            check_safe_relative_path(path_str)
            all_passed = False
            probe_details[path_str] = "FAILED: Did not raise ValueError"
        except ValueError as exc:
            err_msg = str(exc)
            if expected_sub in err_msg:
                probe_details[path_str] = f"PASSED (rejected with: {err_msg})"
            else:
                all_passed = False
                probe_details[path_str] = f"FAILED: Expected '{expected_sub}' in '{err_msg}'"
        except Exception as exc:
            all_passed = False
            probe_details[path_str] = f"FAILED: Unexpected exception {type(exc)}: {exc}"

    if all_passed:
        res.mark_pass(
            failure_mode="ValueError: Safe path violation",
            observed_error="All 6 invalid/malicious path patterns strictly raised ValueError",
            details=probe_details,
        )
    else:
        res.mark_fail(f"Some test cases failed: {probe_details}")

    return res


def execute_probe_8(tmp_path: Path) -> AuditProbeResult:
    """Probe 8: Symlink or containment escape -> validate_contained_file must fail closed."""
    res = AuditProbeResult(
        8,
        "Symlink and Containment Escape Disallowed",
        "Create symlink pointing outside package root -> validate_contained_file MUST reject fail closed (disallow symlinks)",
    )
    pkg_dir = tmp_path / "probe8_pkg"
    pkg_dir.mkdir()
    valid_file = pkg_dir / "valid_item.txt"
    valid_file.write_text("authentic content", encoding="utf-8")

    # 1. Symlink rejection
    outside_target = tmp_path / "outside_secret.txt"
    outside_target.write_text("secret outside package", encoding="utf-8")
    symlink_file = pkg_dir / "symlink_escape.txt"

    symlink_tested = False
    try:
        symlink_file.symlink_to(outside_target)
        try:
            validate_contained_file(pkg_dir, "symlink_escape.txt")
            res.mark_fail("validate_contained_file allowed symlink")
            return res
        except ValueError as exc:
            if "Symlinks are disallowed in package" in str(exc):
                symlink_tested = True
    except (OSError, NotImplementedError):
        # Windows without SeCreateSymbolicLinkPrivilege: mock Path.is_symlink
        with unittest.mock.patch.object(Path, "is_symlink", return_value=True):
            try:
                validate_contained_file(pkg_dir, "valid_item.txt")
                res.mark_fail("validate_contained_file allowed mocked symlink")
                return res
            except ValueError as exc:
                if "Symlinks are disallowed in package" in str(exc):
                    symlink_tested = True

    # 2. Containment escape rejection
    escape_tested = False
    with unittest.mock.patch.object(Path, "is_relative_to", return_value=False):
        try:
            validate_contained_file(pkg_dir, "valid_item.txt")
            res.mark_fail("validate_contained_file allowed containment escape")
            return res
        except ValueError as exc:
            if "Path escapes package root containment" in str(exc):
                escape_tested = True

    if symlink_tested and escape_tested:
        res.mark_pass(
            failure_mode="ValueError: Symlinks are disallowed / Path escapes package root containment",
            observed_error="Symlink rejection and root containment escape both verified",
        )
    else:
        res.mark_fail(f"symlink_tested={symlink_tested}, escape_tested={escape_tested}")

    return res


def execute_probe_9() -> AuditProbeResult:
    """Probe 9: Run canonical acceptance verification on production candidate package."""
    res = AuditProbeResult(
        9,
        "Production Candidate Package Acceptance Verification",
        "Run verify_canonical_package_acceptance.py on actual candidate package -> MUST PASS with zero violations",
    )
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/verify_canonical_package_acceptance.py"),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    if proc.returncode == 0 and "ACCEPTANCE VERIFICATION VERDICT: PASS" in proc.stdout:
        # Extract digest values from stdout
        manifest_sha = None
        base_manifest_sha = None
        archive_sha = None
        for line in proc.stdout.splitlines():
            line_str = line.strip()
            if "Package Manifest SHA-256:" in line_str:
                manifest_sha = line_str.split(":", 1)[1].strip()
            elif "Base Manifest SHA-256:" in line_str:
                base_manifest_sha = line_str.split(":", 1)[1].strip()
            elif "Archive SHA-256:" in line_str:
                archive_sha = line_str.split(":", 1)[1].strip()

        res.mark_pass(
            failure_mode="NONE (VERDICT: PASS)",
            observed_error="None (0 violations, exit code 0)",
            exit_code=proc.returncode,
            manifest_sha256=manifest_sha,
            base_manifest_sha256=base_manifest_sha,
            archive_sha256=archive_sha,
            stdout=proc.stdout.strip(),
        )
    else:
        res.mark_fail(
            f"Acceptance verification failed: exit code {proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}"
        )

    return res


def run_all_probes() -> List[AuditProbeResult]:
    """Run all 9 probes in isolated temporary fixtures and return results."""
    results: List[AuditProbeResult] = []
    with tempfile.TemporaryDirectory(prefix="sg_audit_probes_") as tmp_dir_str:
        tmp_p = Path(tmp_dir_str)
        print(f"[*] SG-AUDIT Workspace: {tmp_p}")

        print("[*] Executing Probe 1 (Tool Disk Byte Tampering)...")
        results.append(execute_probe_1(tmp_p))

        print("[*] Executing Probe 2 (ZIP Member Stream Tampering)...")
        results.append(execute_probe_2(tmp_p))

        print("[*] Executing Probe 3 (Duplicate ZIP Entry)...")
        results.append(execute_probe_3(tmp_p))

        print("[*] Executing Probe 4 (Undeclared ZIP Member)...")
        results.append(execute_probe_4(tmp_p))

        print("[*] Executing Probe 5 (Private Workstation Path Leak in ZIP)...")
        results.append(execute_probe_5(tmp_p))

        print("[*] Executing Probe 6 (Base Descriptor Set Mismatch)...")
        results.append(execute_probe_6(tmp_p))

        print("[*] Executing Probe 7 (check_safe_relative_path Rejection Matrix)...")
        results.append(execute_probe_7())

        print("[*] Executing Probe 8 (Symlink and Containment Escape)...")
        results.append(execute_probe_8(tmp_p))

        print("[*] Executing Probe 9 (Production Candidate Acceptance Verification)...")
        results.append(execute_probe_9())

    return results


# Pytest Test Integration
class TestSGAuditAdversarialProbes:
    def test_probe_1_tool_disk_byte_tampering(self, tmp_path: Path) -> None:
        res = execute_probe_1(tmp_path)
        assert res.passed, f"Probe 1 failed: {res.observed_error}"

    def test_probe_2_zip_member_stream_tampering(self, tmp_path: Path) -> None:
        res = execute_probe_2(tmp_path)
        assert res.passed, f"Probe 2 failed: {res.observed_error}"

    def test_probe_3_duplicate_zip_entry(self, tmp_path: Path) -> None:
        res = execute_probe_3(tmp_path)
        assert res.passed, f"Probe 3 failed: {res.observed_error}"

    def test_probe_4_undeclared_zip_member(self, tmp_path: Path) -> None:
        res = execute_probe_4(tmp_path)
        assert res.passed, f"Probe 4 failed: {res.observed_error}"

    def test_probe_5_private_path_leak(self, tmp_path: Path) -> None:
        res = execute_probe_5(tmp_path)
        assert res.passed, f"Probe 5 failed: {res.observed_error}"

    def test_probe_6_base_descriptor_set_mismatch(self, tmp_path: Path) -> None:
        res = execute_probe_6(tmp_path)
        assert res.passed, f"Probe 6 failed: {res.observed_error}"

    def test_probe_7_check_safe_relative_path(self) -> None:
        res = execute_probe_7()
        assert res.passed, f"Probe 7 failed: {res.observed_error}"

    def test_probe_8_symlink_and_containment_escape(self, tmp_path: Path) -> None:
        res = execute_probe_8(tmp_path)
        assert res.passed, f"Probe 8 failed: {res.observed_error}"

    def test_probe_9_production_candidate_acceptance(self) -> None:
        res = execute_probe_9()
        assert res.passed, f"Probe 9 failed: {res.observed_error}"


def main() -> int:
    print("=" * 80)
    print("SG-AUDIT: INDEPENDENT ADVERSARIAL PROBE SUITE (F05-A / F05-B DEFENSE AUDIT)")
    print("=" * 80)
    results = run_all_probes()

    print("\n" + "=" * 80)
    print("PROBE EXECUTION SUMMARY:")
    print("=" * 80)
    passed_count = sum(1 for r in results if r.passed)
    for r in results:
        status_label = "[PASS]" if r.passed else "[FAIL]"
        print(f"Probe {r.probe_id}: {status_label} {r.name}")
        print(f"  Description:   {r.description}")
        print(f"  Failure Mode:  {r.failure_mode}")
        if r.exit_code is not None:
            print(f"  Exit Code:     {r.exit_code}")
        print(f"  Result / Note: {r.observed_error}")
        if r.probe_id == 9 and r.details:
            print(f"  Archive SHA:   {r.details.get('archive_sha256')}")
            print(f"  Manifest SHA:  {r.details.get('manifest_sha256')}")
            print(f"  Base SHA:      {r.details.get('base_manifest_sha256')}")
        print("-" * 80)

    print(f"\nFinal Verdict: {passed_count}/{len(results)} Probes Passed.")
    print("=" * 80)
    return 0 if passed_count == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
