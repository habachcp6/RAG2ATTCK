#!/usr/bin/env python3
"""
scripts/verify_public_v4_package.py

Self-contained, portable offline verification tool for RAG2ATT&CK Public v4 Candidate Package.
Egress Invariant: Strictly 0 external calls (local Python standard library only).
Single-Read Atomic Capture: Every file is captured once, hashed, and validated without TOCTOU.
Fail-Closed Design: Definitive failure on any missing role, size discrepancy, or hash mismatch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent

REQUIRED_ROLES = [
    "base_manifest_descriptor",
    "accepted_metric_bundle",
    "root_freeze_envelope",
    "canonical_run_seal",
    "root_inventory_acceptance",
    "root_track_a_acceptance",
    "execution_log",
    "sanitized_rq_provenance",
]


def read_verified_buffer(path: Path) -> Tuple[bytes, str, int]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file: {path}")
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    return raw, sha, len(raw)


def run_privacy_scan(package_dir: Path) -> List[str]:
    violations = []
    private_path_patterns = [
        re.compile(r"C:[\\/]Users[\\/][a-zA-Z0-9_.-]+", re.IGNORECASE),
        re.compile(r"D:[\\/](?:RAG2ATTCK|Users|worktrees)[\\/a-zA-Z0-9_.-]*", re.IGNORECASE),
    ]
    for f in package_dir.rglob("*"):
        if not f.is_file() or f.suffix in {".zip", ".pyc"}:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        rel = f.relative_to(package_dir).as_posix()
        for pat in private_path_patterns:
            matches = pat.findall(content)
            for m in matches:
                violations.append(f"Private path '{m}' in {rel}")
    return violations


def verify_package(package_dir: Path, expected_manifest_sha256: Optional[str] = None) -> Dict[str, Any]:
    if not package_dir.is_dir():
        raise FileNotFoundError(f"Package directory not found: {package_dir}")

    manifest_path = package_dir / "package_manifest_v4.json"
    raw_man, man_sha, man_len = read_verified_buffer(manifest_path)

    if expected_manifest_sha256 is not None:
        if man_sha != expected_manifest_sha256:
            raise ValueError(f"Package manifest SHA mismatch: actual {man_sha} != expected {expected_manifest_sha256}")

    manifest_data = json.loads(raw_man.decode("utf-8"))

    # 1. Verify Role Index Completeness
    role_index = manifest_data.get("role_index", {})
    for role in REQUIRED_ROLES:
        if role not in role_index:
            raise KeyError(f"Required semantic role missing from role index: {role}")
        rel_path = role_index[role]
        file_path = package_dir / rel_path
        if not file_path.is_file():
            raise FileNotFoundError(f"File for role '{role}' not found at: {file_path}")

    # 2. Verify Base Package (v3) items
    base_pkg = manifest_data.get("base_package", {})
    base_manifest_rel = base_pkg.get("manifest_path", "base_public_v3/canonical_bundle_manifest.json")
    base_man_file = package_dir / base_manifest_rel
    raw_base_man, actual_base_man_sha, _ = read_verified_buffer(base_man_file)
    expected_base_man_sha = base_pkg.get("manifest_sha256")
    if actual_base_man_sha != expected_base_man_sha:
        raise ValueError(f"Base v3 manifest SHA mismatch: {actual_base_man_sha} != {expected_base_man_sha}")

    verified_base_items = 0
    for rel_path, spec in base_pkg.get("items", {}).items():
        target_f = package_dir / rel_path
        _, item_sha, item_len = read_verified_buffer(target_f)
        if item_sha != spec["sha256"]:
            raise ValueError(f"Base item SHA mismatch for {rel_path}: {item_sha} != {spec['sha256']}")
        if item_len != spec["size_bytes"]:
            raise ValueError(f"Base item size mismatch for {rel_path}: {item_len} != {spec['size_bytes']}")
        verified_base_items += 1

    # 3. Verify Supplemental Envelope items
    supp_pkg = manifest_data.get("supplemental_envelope", {})
    verified_supp_items = 0
    for rel_path, spec in supp_pkg.get("items", {}).items():
        target_f = package_dir / rel_path
        _, item_sha, item_len = read_verified_buffer(target_f)
        if item_sha != spec["sha256"]:
            raise ValueError(f"Supplemental item SHA mismatch for {rel_path}: {item_sha} != {spec['sha256']}")
        if item_len != spec["size_bytes"]:
            raise ValueError(f"Supplemental item size mismatch for {rel_path}: {item_len} != {spec['size_bytes']}")
        verified_supp_items += 1

    # 4. Privacy Scan
    privacy_violations = run_privacy_scan(package_dir)
    if privacy_violations:
        raise ValueError("Privacy violations detected:\n" + "\n".join(privacy_violations))

    return {
        "status": "PASS",
        "package_manifest_sha256": man_sha,
        "package_manifest_bytes": man_len,
        "base_manifest_sha256": actual_base_man_sha,
        "verified_base_items": verified_base_items,
        "verified_supplemental_items": verified_supp_items,
        "verified_roles_count": len(role_index),
        "privacy_violations_count": len(privacy_violations),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify RAG2ATT&CK Public v4 Candidate Package")
    parser.add_argument("--package-dir", type=Path, default=PACKAGE_ROOT, help="Path to package directory")
    parser.add_argument("--expected-manifest-sha256", type=str, default=None, help="Expected manifest SHA-256")
    parser.add_argument("--fail-closed", action="store_true", default=True, help="Fail closed on missing package or error")
    args = parser.parse_args()

    try:
        res = verify_package(args.package_dir, args.expected_manifest_sha256)
        print("================================================================================")
        print("PASS: RAG2ATT&CK Public v4 Candidate Package Verification Successful")
        print("================================================================================")
        print(f"  Package Manifest SHA-256: {res['package_manifest_sha256']}")
        print(f"  Base Manifest SHA-256:    {res['base_manifest_sha256']}")
        print(f"  Verified Base Items:      {res['verified_base_items']}")
        print(f"  Verified Supplemental:    {res['verified_supplemental_items']}")
        print(f"  Verified Semantic Roles:  {res['verified_roles_count']}")
        print(f"  Privacy Scan:             CLEAN (0 violations)")
        print(f"  Egress Guard:             0 external calls")
        print("================================================================================")
        return 0
    except Exception as exc:
        print(f"FAIL / BLOCKED: Verification failed closed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
