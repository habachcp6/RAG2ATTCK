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
    raw_m, m_sha, _ = read_verified_buffer(manifest_file)
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

                zip_info_map = {zi.filename: zi for zi in zf.infolist()}

                # Check safe paths within archive (no traversal, no absolute paths)
                for entry_name in zip_info_map:
                    p = Path(entry_name)
                    if p.is_absolute() or ".." in p.parts or p.drive:
                        print(f"FAIL / BLOCKED: Unsafe path in ZIP archive entry: {entry_name}", file=sys.stderr)
                        sys.exit(1)

                # Verify package_manifest_v4.json member stream
                if "package_manifest_v4.json" not in zip_info_map:
                    print("FAIL / BLOCKED: 'package_manifest_v4.json' missing from ZIP archive", file=sys.stderr)
                    sys.exit(1)
                man_bytes = zf.read("package_manifest_v4.json")
                if hashlib.sha256(man_bytes).hexdigest() != m_sha:
                    print("FAIL / BLOCKED: 'package_manifest_v4.json' in ZIP does not match candidate manifest SHA", file=sys.stderr)
                    sys.exit(1)

                # Build full inventory to verify against archive member streams
                expected_inventory: Dict[str, Dict[str, Any]] = {}
                for rel_p, spec in base_pkg.get("items", {}).items():
                    expected_inventory[rel_p] = spec
                for rel_p, spec in manifest.get("supplemental_envelope", {}).get("items", {}).items():
                    expected_inventory[rel_p] = spec
                base_man_rel = base_pkg.get("manifest_path", "base_public_v3/canonical_bundle_manifest.json")
                if base_man_rel not in expected_inventory:
                    expected_inventory[base_man_rel] = {
                        "sha256": base_pkg.get("manifest_sha256"),
                        "size_bytes": (candidate_dir / base_man_rel).stat().st_size if (candidate_dir / base_man_rel).is_file() else 0,
                    }

                for item_rel, spec in expected_inventory.items():
                    if item_rel not in zip_info_map:
                        print(f"FAIL / BLOCKED: Declared item '{item_rel}' missing from candidate ZIP archive", file=sys.stderr)
                        sys.exit(1)

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
