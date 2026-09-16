"""
Unit tests for Task 3 Schema Profiling & Record Indexing (src/profiler.py).
Tests deterministic opaque ID generation, strict parse accounting,
record index CSV integrity, and profile metadata artifacts.
"""

import csv
import hashlib
import json
from pathlib import Path
import pytest

from src.profiler import generate_opaque_record_id


def test_generate_opaque_record_id_formula():
    """Verify deterministic opaque ID formula: rec_{SHA-256(sha256 + ':' + str(ordinal))[:16]}."""
    dummy_sha = "a" * 64
    ordinal = 42
    token = f"{dummy_sha}:{ordinal}".encode("utf-8")
    expected = f"rec_{hashlib.sha256(token).hexdigest()[:16]}"

    computed = generate_opaque_record_id(dummy_sha, ordinal)
    assert computed == expected
    assert len(computed) == 20  # 'rec_' (4) + 16 hex chars
    assert computed.startswith("rec_")


def test_generate_opaque_record_id_deterministic():
    """Repeated calls with same arguments must produce identical IDs."""
    h = hashlib.sha256(b"test").hexdigest()
    id1 = generate_opaque_record_id(h, 0)
    id2 = generate_opaque_record_id(h, 0)
    assert id1 == id2

    # Different ordinals must produce different IDs
    id3 = generate_opaque_record_id(h, 1)
    assert id1 != id3

    # Different hashes must produce different IDs
    h2 = hashlib.sha256(b"test2").hexdigest()
    id4 = generate_opaque_record_id(h2, 0)
    assert id1 != id4


def test_production_parse_accounting():
    """Verify production parse error ledger strictly enforces accounting equation."""
    ledger_path = Path("data/metadata/parse_error_ledger.json")
    assert ledger_path.exists(), "parse_error_ledger.json must exist"

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    assert ledger["accounting_invariant_holds"] is True
    assert ledger["source_logical_rows"] == ledger["successfully_parsed_records"] + ledger["rejected_malformed_records"]
    assert ledger["source_logical_rows"] == 102011
    assert ledger["successfully_parsed_records"] == 102011
    assert ledger["rejected_malformed_records"] == 0
    assert ledger["error_count"] == 0


def test_production_record_index_csv():
    """Verify production record_index.csv has exactly 102,011 rows and required columns."""
    index_csv = Path("data/metadata/record_index.csv")
    assert index_csv.exists(), "record_index.csv must exist"

    with open(index_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ["record_id", "source_file", "source_file_sha256", "record_ordinal"]
        row_count = 0
        first_row = None
        for row in reader:
            if row_count == 0:
                first_row = row
            row_count += 1

    assert row_count == 102011
    assert first_row is not None
    assert first_row["record_id"].startswith("rec_")
    assert len(first_row["source_file_sha256"]) == 64
    assert first_row["record_ordinal"] == "0"


def test_production_schema_profile():
    """Verify production schema profile metadata."""
    profile_path = Path("data/metadata/schema_profile.json")
    assert profile_path.exists(), "schema_profile.json must exist"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    assert profile["source_logical_rows"] == 102011
    assert profile["successfully_parsed_records"] == 102011
    assert profile["rejected_malformed_records"] == 0
    assert profile["unique_field_count"] == 377
