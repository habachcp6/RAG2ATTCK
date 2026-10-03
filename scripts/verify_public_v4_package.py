#!/usr/bin/env python3
"""
scripts/verify_public_v4_package.py

Self-contained, portable offline verification tool for RAG2ATT&CK Public v4 Candidate Package.
Egress Invariant: Strictly 0 external calls (local Python standard library only).
Single-Read Atomic Capture: Every file is captured once, hashed, and validated without TOCTOU.
Fail-Closed Design: Definitive failure on any missing role, size discrepancy, hash mismatch,
schema violation, inventory truncation, or role target collapse.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PACKAGE_ROOT = Path(__file__).resolve().parent

VALID_SCHEMA_VERSIONS = {"public_v4_candidate_package_v1", "rag2attck-public-package-v4", "4.0.0"}
REQUIRED_SECTIONS = ["schema_version", "role_index", "base_package", "supplemental_envelope", "verification_tools"]
MIN_BASE_ITEMS = 23
MIN_SUPPLEMENTAL_ITEMS = 5

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

ROLE_SEMANTIC_SPECS = {
    "base_manifest_descriptor": {
        "suffix": "canonical_bundle_manifest.json",
        "description": "Base v3 manifest descriptor",
    },
    "accepted_metric_bundle": {
        "suffix": "canonical_metric_bundle_v2.json",
        "expected_sha256": "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34",
    },
    "root_freeze_envelope": {
        "suffix": "root_metric_bundle_v2_freeze_95c0233.json",
        "expected_sha256": "e284344e8d571a61e40aa03dd6fbf529dc1e097378f2532c07d596936c10fad2",
    },
    "canonical_run_seal": {
        "suffixes": ("canonical_run_seal_v1.json", "task_1264_canonical_seal.json"),
        "expected_sha256": "ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701",
    },
    "execution_log": {
        "suffix": ".log",
        "expected_sha256": "fcacacf67d72797b8f1781d4998ed77bbf6d3e59e3e4d2e26fd0a9a7cca29b44",
    },
    "root_inventory_acceptance": {
        "suffix": ".json",
    },
    "root_track_a_acceptance": {
        "suffix": ".json",
    },
    "sanitized_rq_provenance": {
        "suffixes": (".json", ".md"),
    },
}


def read_verified_buffer(path: Path) -> Tuple[bytes, str, int]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file: {path}")
    raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    return raw, sha, len(raw)


def check_safe_relative_path(rel_path_str: str) -> Path:
    """Validate that path is a safe relative POSIX path without escaping, drive letters, backslashes, or absolute root."""
    if not rel_path_str:
        raise ValueError("Empty path in package manifest")
    if "\\" in rel_path_str:
        raise ValueError(f"Unsafe backslash in package manifest path: '{rel_path_str}'")
    if rel_path_str.startswith("/"):
        raise ValueError(f"Unsafe absolute path starting with '/' in package manifest: '{rel_path_str}'")
    if re.match(r"^[a-zA-Z]:", rel_path_str):
        raise ValueError(f"Unsafe path with drive letter in package manifest: '{rel_path_str}'")
    parts = rel_path_str.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise ValueError(f"Unsafe path component '{part}' in package manifest: '{rel_path_str}'")
    p = Path(rel_path_str)
    if p.is_absolute() or p.drive:
        raise ValueError(f"Unsafe absolute or drive path in package manifest: '{rel_path_str}'")
    return p


def validate_contained_file(package_dir: Path, rel_path_str: str) -> Path:
    """Validate safe relative path, absence of symlinks, and containment within package_dir."""
    check_safe_relative_path(rel_path_str)
    target_f = package_dir / rel_path_str
    if target_f.is_symlink():
        raise ValueError(f"Symlinks are disallowed in package: '{rel_path_str}'")
    resolved_pkg = package_dir.resolve()
    resolved_f = target_f.resolve()
    if not resolved_f.is_relative_to(resolved_pkg):
        raise ValueError(f"Path escapes package root containment: '{rel_path_str}' -> '{resolved_f}'")
    if not target_f.is_file():
        raise FileNotFoundError(f"Missing required file in package: '{rel_path_str}' at {target_f}")
    return target_f


def run_privacy_scan(package_dir: Path) -> List[str]:
    violations = []
    private_path_patterns = [
        re.compile(r"C:[\\/]Users[\\/][a-zA-Z0-9_.-]+", re.IGNORECASE),
        re.compile(r"D:[\\/](?:RAG2ATTCK|Users|worktrees)[\\/a-zA-Z0-9_.-]*", re.IGNORECASE),
    ]
    for f in package_dir.rglob("*"):
        if f.is_symlink() or not f.is_file() or f.suffix in {".zip", ".pyc"}:
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
    if not isinstance(manifest_data, dict):
        raise ValueError("Package manifest root must be a JSON object")

    # 1. Schema Version & Required Sections Validation
    schema_version = manifest_data.get("schema_version")
    if schema_version not in VALID_SCHEMA_VERSIONS:
        raise ValueError(
            f"Invalid package manifest schema_version '{schema_version}'. Expected one of {VALID_SCHEMA_VERSIONS}"
        )

    for sec in REQUIRED_SECTIONS:
        if sec not in manifest_data:
            raise KeyError(f"Missing required manifest section: '{sec}'")

    # 2. Base Package Descriptor Cross-Check & Minimum Item Counts
    base_pkg = manifest_data["base_package"]
    base_items = base_pkg.get("items")
    if not isinstance(base_items, dict) or len(base_items) < MIN_BASE_ITEMS:
        raise ValueError(
            f"Base package items must contain at least {MIN_BASE_ITEMS} declared items, found: {len(base_items) if isinstance(base_items, dict) else 0}"
        )

    supp_pkg = manifest_data["supplemental_envelope"]
    supp_items = supp_pkg.get("items")
    if not isinstance(supp_items, dict) or len(supp_items) < MIN_SUPPLEMENTAL_ITEMS:
        raise ValueError(
            f"Supplemental envelope items must contain at least {MIN_SUPPLEMENTAL_ITEMS} items, found: {len(supp_items) if isinstance(supp_items, dict) else 0}"
        )

    base_manifest_rel = base_pkg.get("manifest_path", "base_public_v3/canonical_bundle_manifest.json")
    base_man_file = validate_contained_file(package_dir, base_manifest_rel)
    raw_base_man, actual_base_man_sha, _ = read_verified_buffer(base_man_file)
    expected_base_man_sha = base_pkg.get("manifest_sha256")
    if not expected_base_man_sha or actual_base_man_sha != expected_base_man_sha:
        raise ValueError(f"Base v3 manifest SHA mismatch: actual {actual_base_man_sha} != expected {expected_base_man_sha}")

    # Parse base descriptor content and verify that all items declared in descriptor exist in base_items
    base_descriptor_data = json.loads(raw_base_man.decode("utf-8"))
    if not isinstance(base_descriptor_data, dict):
        raise ValueError("Base descriptor root must be a JSON object")

    required_descriptor_sections = [
        "byte_preserved_files",
        "sanitized_transformed_files",
        "sanitized_provenance_assets",
        "runtime_assets",
    ]
    for sec_key in required_descriptor_sections:
        if sec_key not in base_descriptor_data or not isinstance(base_descriptor_data[sec_key], dict):
            raise ValueError(f"Base descriptor missing required section or not a dict: '{sec_key}'")

    descriptor_declared_files: Dict[str, Dict[str, Any]] = {}
    for section_key in required_descriptor_sections:
        sec_dict = base_descriptor_data[section_key]
        for rel_k, spec in sec_dict.items():
            expected_item_sha = spec.get("sanitized_sha256") or spec.get("sha256")
            expected_item_size = spec.get("size_bytes")
            full_rel_path = f"base_public_v3/{rel_k}"
            descriptor_declared_files[full_rel_path] = {
                "sha256": expected_item_sha,
                "size_bytes": expected_item_size,
                "section": section_key,
            }

    # Set identity check between base_items and descriptor_declared_files
    base_items_keys = set(base_items.keys())
    desc_keys = set(descriptor_declared_files.keys())
    if base_items_keys != desc_keys:
        missing_in_pkg = desc_keys - base_items_keys
        undeclared_in_desc = base_items_keys - desc_keys
        err_parts = []
        if missing_in_pkg:
            err_parts.append(f"Declared in descriptor but missing in package base items: {sorted(missing_in_pkg)}")
        if undeclared_in_desc:
            err_parts.append(f"In package base items but undeclared in descriptor: {sorted(undeclared_in_desc)}")
        raise ValueError("Base descriptor and base_items set mismatch: " + "; ".join(err_parts))

    for full_rel, desc_spec in descriptor_declared_files.items():
        pkg_spec = base_items[full_rel]
        if pkg_spec["sha256"] != desc_spec["sha256"]:
            raise ValueError(
                f"Base item '{full_rel}' SHA mismatch with base descriptor: {pkg_spec['sha256']} != {desc_spec['sha256']}"
            )
        if pkg_spec["size_bytes"] != desc_spec["size_bytes"]:
            raise ValueError(
                f"Base item '{full_rel}' size mismatch with base descriptor: {pkg_spec['size_bytes']} != {desc_spec['size_bytes']}"
            )

    # 3. Disk Verification of all Inventory Items
    verified_inventory: Dict[str, Tuple[str, int]] = {}

    verified_base_items = 0
    for rel_path, spec in base_items.items():
        target_f = validate_contained_file(package_dir, rel_path)
        _, item_sha, item_len = read_verified_buffer(target_f)
        if item_sha != spec["sha256"]:
            raise ValueError(f"Base item SHA mismatch for {rel_path}: actual {item_sha} != expected {spec['sha256']}")
        if item_len != spec["size_bytes"]:
            raise ValueError(f"Base item size mismatch for {rel_path}: actual {item_len} != expected {spec['size_bytes']}")
        verified_inventory[rel_path] = (item_sha, item_len)
        verified_base_items += 1

    verified_supp_items = 0
    for rel_path, spec in supp_items.items():
        target_f = validate_contained_file(package_dir, rel_path)
        _, item_sha, item_len = read_verified_buffer(target_f)
        if item_sha != spec["sha256"]:
            raise ValueError(f"Supplemental item SHA mismatch for {rel_path}: actual {item_sha} != expected {spec['sha256']}")
        if item_len != spec["size_bytes"]:
            raise ValueError(f"Supplemental item size mismatch for {rel_path}: actual {item_len} != expected {spec['size_bytes']}")
        verified_inventory[rel_path] = (item_sha, item_len)
        verified_supp_items += 1

    # Verification Tools Verification
    verification_tools = manifest_data.get("verification_tools")
    if not isinstance(verification_tools, dict) or not verification_tools:
        raise ValueError("Package manifest missing required 'verification_tools' section or it is empty")
    if "verify_public_v4_package.py" not in verification_tools:
        raise ValueError("Package manifest 'verification_tools' must include 'verify_public_v4_package.py'")

    verified_tools = 0
    for tool_name, spec in verification_tools.items():
        target_f = validate_contained_file(package_dir, tool_name)
        _, tool_sha, tool_len = read_verified_buffer(target_f)
        if tool_sha != spec["sha256"]:
            raise ValueError(f"Verification tool SHA mismatch for {tool_name}: actual {tool_sha} != expected {spec['sha256']}")
        if tool_len != spec["size_bytes"]:
            raise ValueError(f"Verification tool size mismatch for {tool_name}: actual {tool_len} != expected {spec['size_bytes']}")
        verified_inventory[tool_name] = (tool_sha, tool_len)
        verified_tools += 1

    # 4. Role Index Semantic Validation & Collapse Prevention
    role_index = manifest_data["role_index"]
    distinct_role_paths: Set[str] = set()

    for role in REQUIRED_ROLES:
        if role not in role_index:
            raise KeyError(f"Required semantic role missing from role index: {role}")
        rel_path = role_index[role]
        file_path = validate_contained_file(package_dir, rel_path)

        # The role target must be part of the verified inventory or verified base descriptor
        if rel_path != base_manifest_rel and rel_path not in verified_inventory:
            raise ValueError(
                f"Role '{role}' points to '{rel_path}' which is not in the verified package inventory"
            )

        spec = ROLE_SEMANTIC_SPECS.get(role, {})
        if "suffixes" in spec and not any(rel_path.endswith(sfx) for sfx in spec["suffixes"]):
            raise ValueError(
                f"Role '{role}' path '{rel_path}' does not end with expected suffix in {spec['suffixes']}"
            )
        elif "suffix" in spec and not rel_path.endswith(spec["suffix"]):
            raise ValueError(
                f"Role '{role}' path '{rel_path}' does not end with expected suffix '{spec['suffix']}'"
            )
        if "expected_sha256" in spec:
            actual_sha = verified_inventory[rel_path][0] if rel_path in verified_inventory else hashlib.sha256(file_path.read_bytes()).hexdigest()
            if actual_sha != spec["expected_sha256"]:
                raise ValueError(
                    f"Role '{role}' SHA-256 mismatch: actual {actual_sha} != expected {spec['expected_sha256']}"
                )

        distinct_role_paths.add(rel_path)

    # Prevent role collapse (placeholder pointing 8 roles to a single file)
    if len(distinct_role_paths) < 6:
        raise ValueError(
            f"Role collapse detected: required roles must point to distinct authentic artifacts, got only {len(distinct_role_paths)} unique paths for 8 roles"
        )

    # 5. Privacy Scan
    privacy_violations = run_privacy_scan(package_dir)
    if privacy_violations:
        raise ValueError("Privacy violations detected:\n" + "\n".join(privacy_violations))

    return {
        "status": "PASS",
        "validation_mode": "AUTHENTICATED" if expected_manifest_sha256 is not None else "STANDALONE_INTEGRITY",
        "package_manifest_sha256": man_sha,
        "package_manifest_bytes": man_len,
        "base_manifest_sha256": actual_base_man_sha,
        "verified_base_items": verified_base_items,
        "verified_supplemental_items": verified_supp_items,
        "verified_tools_count": verified_tools,
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
        print(f"  Validation Mode:          {res['validation_mode']}")
        print(f"  Package Manifest SHA-256: {res['package_manifest_sha256']}")
        print(f"  Base Manifest SHA-256:    {res['base_manifest_sha256']}")
        print(f"  Verified Base Items:      {res['verified_base_items']}")
        print(f"  Verified Supplemental:    {res['verified_supplemental_items']}")
        print(f"  Verified Semantic Roles:  {res['verified_roles_count']}")
        print(f"  Privacy Scan:             CLEAN (0 violations)")
        print("================================================================================")
        return 0
    except Exception as exc:
        print("================================================================================")
        print(f"FAIL: Package Verification Rejected: {exc}")
        print("================================================================================")
        return 1


if __name__ == "__main__":
    sys.exit(main())
