"""
Unit tests for Task 2 Dataset Acquisition (src/acquisition.py).
Tests Mendeley file catalog verification, file roles, checksum verification,
and error handling.
"""

import json
from pathlib import Path
import pytest

from src.acquisition import acquire_windows_apt_dataset, DatasetAcquisitionError


def test_mendeley_catalog_existence(tmp_path):
    """Catalog file must be present to acquire dataset."""
    ws = tmp_path
    with pytest.raises(DatasetAcquisitionError, match="Missing Mendeley file catalog"):
        acquire_windows_apt_dataset(ws)


def test_dataset_manifest_contents():
    """Verify production dataset_manifest.json contents, roles, and hashes."""
    manifest_path = Path("data/metadata/dataset_manifest.json")
    assert manifest_path.exists(), "dataset_manifest.json must exist"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["dataset_id"] == "b8fmtzvpy8"
    assert manifest["dataset_version"] == "3" or manifest["dataset_version"] == 3
    assert manifest["dataset_doi"] == "10.17632/b8fmtzvpy8.3"
    assert manifest["total_files"] == 21
    assert manifest["total_bytes"] == 480856926

    files = manifest["files"]
    assert len(files) == 21

    roles = {f["role"] for f in files}
    assert roles == {"ingest_period_csv", "reconciliation_combined_csv", "metadata_manifest"}

    period_files = [f for f in files if f["role"] == "ingest_period_csv"]
    assert len(period_files) == 16

    combined_file = [f for f in files if f["role"] == "reconciliation_combined_csv"]
    assert len(combined_file) == 1
    assert combined_file[0]["filename"] == "combined.csv"

    metadata_files = [f for f in files if f["role"] == "metadata_manifest"]
    assert len(metadata_files) == 4
    meta_names = {f["filename"] for f in metadata_files}
    assert meta_names == {"checksums.sha256", "README.md", "scenario_manifest.csv", "validation_summary.csv"}

    # All files must have verified == True
    for f in files:
        assert f["verified"] is True
        assert len(f["sha256"]) == 64
        assert f["sha256"] == f["expected_sha256"]
