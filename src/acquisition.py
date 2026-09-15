"""
RAG2ATTCK - Dataset Acquisition & Provenance Module (Task 2)
Downloads, verifies, and establishes immutable provenance for Windows-APT 2025 v3.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


class DatasetAcquisitionError(RuntimeError):
    """Raised when dataset acquisition or hash verification fails."""
    pass


def acquire_windows_apt_dataset(
    workspace_root: Path,
    chunk_size: int = 1024 * 1024
) -> Dict[str, Any]:
    """
    Acquires all 21 files of Windows-APT 2025 v3 (Mendeley b8fmtzvpy8.3).
    Verifies sizes and SHA-256 hashes against mendeley_v3_files.json.
    Writes data/metadata/dataset_manifest.json.
    """
    ws = workspace_root.resolve()
    raw_dir = ws / "data" / "raw" / "windows_apt_2025" / "v3"
    raw_dir.mkdir(parents=True, exist_ok=True)

    staging_dir = ws / ".cache" / "staging"
    staging_dir.mkdir(parents=True, exist_ok=True)

    mendeley_catalog_file = ws / "data" / "audit" / "source_research" / "mendeley_v3_files.json"
    if not mendeley_catalog_file.exists():
        raise DatasetAcquisitionError(f"Missing Mendeley file catalog: {mendeley_catalog_file}")

    with open(mendeley_catalog_file, "r", encoding="utf-8") as f:
        file_catalog: List[Dict[str, Any]] = json.load(f)

    manifest_files = []
    total_bytes = 0

    print(f"[*] Beginning Windows-APT 2025 v3 acquisition ({len(file_catalog)} files)...")

    for entry in file_catalog:
        filename = entry["filename"]
        expected_size = entry["size"]
        expected_hash = entry["content_details"]["sha256_hash"]
        download_url = entry["content_details"]["download_url"]
        provider_file_id = entry["id"]
        last_modified = entry.get("last_modified_date", "")

        target_file = raw_dir / filename
        staging_file = staging_dir / f"{filename}.tmp"

        # Determine file role
        if filename == "combined.csv":
            role = "reconciliation_combined_csv"
        elif filename.endswith(".csv") and filename not in ("scenario_manifest.csv", "validation_summary.csv"):
            role = "ingest_period_csv"
        else:
            role = "metadata_manifest"

        # Check if file already exists and matches hash
        if target_file.exists() and target_file.stat().st_size == expected_size:
            computed_hash = hashlib.sha256(target_file.read_bytes()).hexdigest()
            if computed_hash == expected_hash:
                print(f"  [=] Already verified: {filename} ({expected_size} bytes)")
                manifest_files.append({
                    "filename": filename,
                    "provider_file_id": provider_file_id,
                    "download_url": download_url,
                    "size_bytes": expected_size,
                    "sha256": computed_hash,
                    "expected_sha256": expected_hash,
                    "last_modified_date": last_modified,
                    "role": role,
                    "verified": True
                })
                total_bytes += expected_size
                continue

        # If it's one of the pre-saved small metadata files, check source_research first
        pre_saved = ws / "data" / "audit" / "source_research" / filename
        if pre_saved.exists() and pre_saved.stat().st_size == expected_size:
            pre_hash = hashlib.sha256(pre_saved.read_bytes()).hexdigest()
            if pre_hash == expected_hash:
                shutil.copy2(str(pre_saved), str(target_file))
                print(f"  [+] Reused pre-saved metadata: {filename}")
                manifest_files.append({
                    "filename": filename,
                    "provider_file_id": provider_file_id,
                    "download_url": download_url,
                    "size_bytes": expected_size,
                    "sha256": pre_hash,
                    "expected_sha256": expected_hash,
                    "last_modified_date": last_modified,
                    "role": role,
                    "verified": True
                })
                total_bytes += expected_size
                continue

        # Download to staging
        print(f"  [v] Downloading {filename} ({expected_size / (1024**2):.2f} MiB)...")
        req = urllib.request.Request(download_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        hasher = hashlib.sha256()
        dl_bytes = 0

        try:
            with urllib.request.urlopen(req, timeout=120) as resp, open(staging_file, "wb") as out_f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    out_f.write(chunk)
                    hasher.update(chunk)
                    dl_bytes += len(chunk)
        except Exception as e:
            if staging_file.exists():
                staging_file.unlink()
            raise DatasetAcquisitionError(f"Failed to download {filename}: {e}")

        computed_hash = hasher.hexdigest()

        # Check integrity
        if dl_bytes != expected_size:
            if staging_file.exists():
                staging_file.unlink()
            raise DatasetAcquisitionError(
                f"Size mismatch for {filename}: expected {expected_size}, got {dl_bytes}"
            )

        if computed_hash != expected_hash:
            if staging_file.exists():
                staging_file.unlink()
            raise DatasetAcquisitionError(
                f"SHA-256 mismatch for {filename}: expected {expected_hash}, got {computed_hash}"
            )

        # Move to raw destination
        if target_file.exists():
            target_file.unlink()
        shutil.move(str(staging_file), str(target_file))
        print(f"  [+] Verified & Stored: {filename} (SHA-256 match)")

        manifest_files.append({
            "filename": filename,
            "provider_file_id": provider_file_id,
            "download_url": download_url,
            "size_bytes": dl_bytes,
            "sha256": computed_hash,
            "expected_sha256": expected_hash,
            "last_modified_date": last_modified,
            "role": role,
            "verified": True
        })
        total_bytes += dl_bytes

    # Create dataset_manifest.json
    manifest_doc = {
        "schema_version": "1.0.0",
        "dataset_name": "Windows-APT 2025: A Dataset of Attack Scenarios Inspired by Advanced Persistent Threats on Windows Systems",
        "dataset_id": "b8fmtzvpy8",
        "dataset_version": "3",
        "dataset_doi": "10.17632/b8fmtzvpy8.3",
        "publication_doi": "10.1016/j.dib.2026.112569",
        "provider": "Mendeley Data",
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "acquisition_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_files": len(manifest_files),
        "total_bytes": total_bytes,
        "files": manifest_files
    }

    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = meta_dir / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_doc, f, indent=2, ensure_ascii=False)

    print(f"[+] Dataset acquisition complete. Manifest: {manifest_path}")
    return manifest_doc
