#!/usr/bin/env python3
"""
scripts/verify_canonical_package_acceptance.py

Required Acceptance Path Runner for RAG2ATT&CK Public v4 Candidate Package.
Enforces fail-closed semantics:
- Missing required package inputs, non-existent directories, or missing candidate-zip results
  in immediate FAIL / BLOCKED (exit code 1).
- No silent skips allowed in acceptance mode.
- Validates base v3 byte exactness, supplemental v4 envelope, role indices, privacy scan,
  and comprehensive byte-level ZIP archive member streams.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.build_public_v4_package import (
    BASE_V3_DESCRIPTOR_SHA256,
    OUTPUT_V4_DEFAULT_DIR,
    OUTPUT_V4_DEFAULT_ZIP,
    REQUIRED_ROLES,
    read_verified_buffer,
    run_privacy_scan,
)
from scripts.verify_public_v4_package import verify_package


def run_acceptance_verification(
    candidate_dir: Path,
    candidate_zip: Path | None = None,
    expected_manifest_sha256: str | None = None,
) -> Dict[str, Any]:
    """Execute required acceptance verification path. Fails closed on any missing input."""
    # 1. Require candidate directory
    if not candidate_dir.is_dir():
        print(
            f"FAIL / BLOCKED: Candidate package directory does not exist at: {candidate_dir}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 2. Verify package with portable verifier (validates schema, inventory completeness, role semantics, privacy)
    try:
        verif_result = verify_package(candidate_dir, expected_manifest_sha256)
    except Exception as exc:
        print(f"FAIL / BLOCKED: Portable verifier rejected candidate package: {exc}", file=sys.stderr)
        sys.exit(1)

    # 3. Verify manifest contents and role index targets
    manifest_file = candidate_dir / "package_manifest_v4.json"
    raw_m, m_sha, m_len = read_verified_buffer(manifest_file)
    manifest = json.loads(raw_m.decode("utf-8"))

    role_index = manifest.get("role_index", {})
    for role in REQUIRED_ROLES:
        if role not in role_index:
            print(f"FAIL / BLOCKED: Missing required role '{role}' in manifest role index", file=sys.stderr)
            sys.exit(1)
        target_f = candidate_dir / role_index[role]
        if not target_f.is_file():
            print(f"FAIL / BLOCKED: Target file for role '{role}' missing: {target_f}", file=sys.stderr)
            sys.exit(1)

    # 4. Verify base v3 descriptor matches trusted anchor
    base_pkg = manifest.get("base_package", {})
    if base_pkg.get("manifest_sha256") != BASE_V3_DESCRIPTOR_SHA256:
        print(
            f"FAIL / BLOCKED: Base v3 manifest SHA mismatch: {base_pkg.get('manifest_sha256')} != {BASE_V3_DESCRIPTOR_SHA256}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 5. Verify ZIP archive integrity if provided
    zip_verified = False
    zip_sha = None
    zip_len = None
    if candidate_zip is not None:
        # Fail closed immediately if explicitly provided candidate ZIP does not exist
        if not candidate_zip.is_file():
            print(
                f"FAIL / BLOCKED: Explicitly provided candidate ZIP archive does not exist at: {candidate_zip}",
                file=sys.stderr,
            )
            sys.exit(1)

        _, zip_sha, zip_len = read_verified_buffer(candidate_zip)

        try:
            with zipfile.ZipFile(candidate_zip, "r") as zf:
                # Test archive structure for corruption
                corrupt_file = zf.testzip()
                if corrupt_file is not None:
                    print(f"FAIL / BLOCKED: Candidate ZIP corrupted at entry: {corrupt_file}", file=sys.stderr)
                    sys.exit(1)

                seen_filenames = set()
                zip_info_map = {}
                for zi in zf.infolist():
                    if zi.filename in seen_filenames:
                        print(f"FAIL / BLOCKED: Duplicate entry in ZIP archive: '{zi.filename}'", file=sys.stderr)
                        sys.exit(1)
                    seen_filenames.add(zi.filename)
                    zip_info_map[zi.filename] = zi

                # Check safe paths within archive (no traversal, no backslashes, no absolute paths)
                for entry_name in seen_filenames:
                    if "\\" in entry_name or entry_name.startswith("/"):
                        print(f"FAIL / BLOCKED: Unsafe path in ZIP archive entry: {entry_name}", file=sys.stderr)
                        sys.exit(1)
                    p = Path(entry_name)
                    if p.is_absolute() or ".." in p.parts or p.drive:
                        print(f"FAIL / BLOCKED: Unsafe path in ZIP archive entry: {entry_name}", file=sys.stderr)
                        sys.exit(1)

                # Strict ZIP Membership Validation
                base_items_dict = base_pkg.get("items", {})
                supp_items_dict = manifest.get("supplemental_envelope", {}).get("items", {})
                tools_dict = manifest.get("verification_tools", {})
                base_man_rel = base_pkg.get("manifest_path", "base_public_v3/canonical_bundle_manifest.json")

                allowed_membership = (
                    set(base_items_dict.keys())
                    | set(supp_items_dict.keys())
                    | set(tools_dict.keys())
                    | {
                        base_man_rel,
                        "package_manifest_v4.json",
                        "README.md",
                    }
                )

                # In-stream Privacy Scan on non-binary members
                private_path_patterns = [
                    re.compile(r"C:[\\/]Users[\\/][a-zA-Z0-9_.-]+", re.IGNORECASE),
                    re.compile(r"D:[\\/](?:RAG2ATTCK|Users|worktrees)[\\/a-zA-Z0-9_.-]*", re.IGNORECASE),
                    re.compile(r"/home/[a-zA-Z0-9_.-]+", re.IGNORECASE),
                ]
                credential_patterns = [
                    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
                    re.compile(r"ghp_[a-zA-Z0-9]{20,}"),
                    re.compile(r"Bearer\s+[a-zA-Z0-9_.=-]{30,}", re.IGNORECASE),
                ]
                email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
                binary_exts = {".zip", ".pyc", ".png", ".jpg", ".parquet"}

                for entry_name in sorted(seen_filenames):
                    if Path(entry_name).suffix in binary_exts:
                        continue
                    raw_bytes = zf.read(entry_name)
                    try:
                        content = raw_bytes.decode("utf-8")
                    except UnicodeDecodeError:
                        continue

                    for pat in private_path_patterns:
                        matches = pat.findall(content)
                        if matches:
                            print(
                                f"FAIL / BLOCKED: Privacy violation in ZIP member '{entry_name}': Private path '{matches[0]}'",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                    for pat in credential_patterns:
                        matches = pat.findall(content)
                        if matches:
                            print(
                                f"FAIL / BLOCKED: Privacy violation in ZIP member '{entry_name}': Credential pattern detected",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                    for e in email_pattern.findall(content):
                        if not e.endswith("example.com") and not e.endswith("schema.org"):
                            print(
                                f"FAIL / BLOCKED: Privacy violation in ZIP member '{entry_name}': Email address '{e}'",
                                file=sys.stderr,
                            )
                            sys.exit(1)

                # Reject any undeclared member
                undeclared_members = seen_filenames - allowed_membership
                if undeclared_members:
                    print(
                        f"FAIL / BLOCKED: Undeclared member '{sorted(undeclared_members)[0]}' in candidate ZIP archive",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                # Reject if any declared / required member is missing
                missing_members = allowed_membership - seen_filenames
                if missing_members:
                    print(
                        f"FAIL / BLOCKED: Declared item '{sorted(missing_members)[0]}' missing from candidate ZIP archive",
                        file=sys.stderr,
                    )
                    sys.exit(1)

                # Build full inventory to verify against archive member streams
                expected_inventory: Dict[str, Dict[str, Any]] = {}
                for rel_p, spec in base_items_dict.items():
                    expected_inventory[rel_p] = spec
                for rel_p, spec in supp_items_dict.items():
                    expected_inventory[rel_p] = spec
                for rel_p, spec in tools_dict.items():
                    expected_inventory[rel_p] = spec

                expected_inventory[base_man_rel] = {
                    "sha256": base_pkg.get("manifest_sha256"),
                    "size_bytes": (candidate_dir / base_man_rel).stat().st_size if (candidate_dir / base_man_rel).is_file() else 0,
                }
                expected_inventory["package_manifest_v4.json"] = {
                    "sha256": m_sha,
                    "size_bytes": m_len,
                }
                readme_target = candidate_dir / "README.md"
                if readme_target.is_file():
                    _, r_sha, r_len = read_verified_buffer(readme_target)
                    expected_inventory["README.md"] = {
                        "sha256": r_sha,
                        "size_bytes": r_len,
                    }

                for item_rel, spec in expected_inventory.items():
                    # Stream hashing directly from ZIP member stream
                    member_bytes = zf.read(item_rel)
                    member_sha = hashlib.sha256(member_bytes).hexdigest()
                    member_len = len(member_bytes)

                    if member_sha != spec["sha256"]:
                        print(
                            f"FAIL / BLOCKED: ZIP member stream SHA mismatch for '{item_rel}': actual {member_sha} != expected {spec['sha256']}",
                            file=sys.stderr,
                        )
                        sys.exit(1)
                    if member_len != spec["size_bytes"]:
                        print(
                            f"FAIL / BLOCKED: ZIP member stream size mismatch for '{item_rel}': actual {member_len} != expected {spec['size_bytes']}",
                            file=sys.stderr,
                        )
                        sys.exit(1)

            zip_verified = True
        except zipfile.BadZipFile as exc:
            print(f"FAIL / BLOCKED: Invalid or corrupt ZIP archive: {exc}", file=sys.stderr)
            sys.exit(1)

    return {
        "status": "PASS",
        "directory_verified": True,
        "archive_verified": zip_verified,
        "candidate_directory": str(candidate_dir),
        "candidate_zip": str(candidate_zip) if candidate_zip else None,
        "archive_sha256": zip_sha,
        "archive_size_bytes": zip_len,
        "manifest_sha256": m_sha,
        "base_manifest_sha256": verif_result["base_manifest_sha256"],
        "verified_base_items": verif_result["verified_base_items"],
        "verified_supplemental_items": verif_result["verified_supplemental_items"],
        "verified_total_items": verif_result["verified_base_items"] + verif_result["verified_supplemental_items"],
        "verified_roles_count": len(role_index),
        "privacy_violations_count": verif_result["privacy_violations_count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Required Acceptance Path for RAG2ATT&CK Public v4 Package")
    parser.add_argument("--candidate-dir", type=Path, default=OUTPUT_V4_DEFAULT_DIR, help="Candidate directory path")
    parser.add_argument("--candidate-zip", type=Path, default=OUTPUT_V4_DEFAULT_ZIP, help="Candidate ZIP archive path")
    parser.add_argument("--expected-manifest-sha256", type=str, default=None, help="Expected manifest SHA-256")
    parser.add_argument("--output-report", type=Path, default=None, help="Path to write JSON acceptance report")
    args = parser.parse_args()

    result = run_acceptance_verification(
        candidate_dir=args.candidate_dir,
        candidate_zip=args.candidate_zip,
        expected_manifest_sha256=args.expected_manifest_sha256,
    )

    if args.output_report:
        args.output_report.parent.mkdir(parents=True, exist_ok=True)
        args.output_report.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("================================================================================")
    print(" ACCEPTANCE VERIFICATION VERDICT: PASS")
    print("================================================================================")
    print(f"  Candidate Dir:            {result['candidate_directory']}")
    print(f"  Directory Verified:       {result['directory_verified']}")
    print(f"  Candidate ZIP Archive:    {result['candidate_zip']}")
    print(f"  Archive Verified:         {result['archive_verified']} (Member stream SHA & size checked)")
    if result["archive_sha256"]:
        print(f"  Archive SHA-256:          {result['archive_sha256']}")
    print(f"  Package Manifest SHA-256: {result['manifest_sha256']}")
    print(f"  Base Manifest SHA-256:    {result['base_manifest_sha256']}")
    print(f"  Verified Items:           {result['verified_total_items']} items ({result['verified_base_items']} base, {result['verified_supplemental_items']} supp)")
    print(f"  Verified Semantic Roles:  {result['verified_roles_count']}")
    print(f"  Privacy Scan:             CLEAN (0 violations)")
    print("================================================================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())
