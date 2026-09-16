"""
Task 3 profiling invariants that are independent of production outputs.
"""

import csv
import hashlib
import json
from pathlib import Path

from src.profiler import generate_opaque_record_id, profile_dataset_schemas


def _write_manifest(workspace: Path, files: list[dict]) -> None:
    manifest_path = workspace / "data" / "metadata" / "dataset_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "dataset_id": "b8fmtzvpy8",
                "dataset_version": "3",
                "files": files,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _add_raw_csv(workspace: Path, filename: str, content: str) -> tuple[Path, str]:
    raw_dir = workspace / "data" / "raw" / "windows_apt_2025" / "v3"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / filename
    path.write_text(content, encoding="utf-8")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    return path, sha


def test_malformed_logical_record_does_not_renumber_later_records(tmp_path):
    _, sha = _add_raw_csv(tmp_path, "fixture.csv", "a,b\n1,2\nbad,too,many\n3,4\n")
    _write_manifest(
        tmp_path,
        [{"filename": "fixture.csv", "role": "ingest_period_csv", "sha256": sha}],
    )

    profile_dataset_schemas(tmp_path)

    with open(tmp_path / "data" / "metadata" / "record_index.csv", "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert [row["record_ordinal"] for row in rows] == ["0", "2"]
    assert rows[1]["record_id"] == generate_opaque_record_id(sha, 2)

    ledger = json.loads((tmp_path / "data" / "metadata" / "parse_error_ledger.json").read_text(encoding="utf-8"))
    assert ledger["source_logical_rows"] == 3
    assert ledger["successfully_parsed_records"] == 2
    assert ledger["rejected_malformed_records"] == 1


def test_quoted_delimiter_and_multiline_csv_record_is_single_observation(tmp_path):
    _, sha = _add_raw_csv(tmp_path, "quoted.csv", 'id,message\n1,"hello,\nworld"\n')
    _write_manifest(
        tmp_path,
        [{"filename": "quoted.csv", "role": "ingest_period_csv", "sha256": sha}],
    )

    profile = profile_dataset_schemas(tmp_path)

    assert profile["source_logical_rows"] == 1
    assert profile["successfully_parsed_records"] == 1
    assert profile["rejected_malformed_records"] == 0


def test_field_inventory_distinguishes_absent_empty_null_and_nonempty(tmp_path):
    _, sha1 = _add_raw_csv(tmp_path, "one.csv", "a,b\nvalue,\nother,None\n")
    _, sha2 = _add_raw_csv(tmp_path, "two.csv", "a,c\nthird,present\n")
    _write_manifest(
        tmp_path,
        [
            {"filename": "one.csv", "role": "ingest_period_csv", "sha256": sha1},
            {"filename": "two.csv", "role": "ingest_period_csv", "sha256": sha2},
        ],
    )

    profile_dataset_schemas(tmp_path)

    with open(tmp_path / "data" / "metadata" / "field_inventory.csv", "r", encoding="utf-8") as f:
        rows = {row["field_name"]: row for row in csv.DictReader(f)}

    assert rows["b"]["schema_present_record_count"] == "2"
    assert rows["b"]["schema_absent_record_count"] == "1"
    assert rows["b"]["empty_string_record_count"] == "1"
    assert rows["b"]["explicit_null_record_count"] == "1"
    assert rows["b"]["non_empty_record_count"] == "0"


def test_cmd_profile_consumes_canonical_schema_without_keyerror(monkeypatch, capsys):
    """cmd_profile must consume canonical schema keys without KeyError."""
    from types import SimpleNamespace
    from src.data_ground_truth import cmd_profile

    # Mock _validate_or_exit to avoid running production gates in isolated unit test
    monkeypatch.setattr("src.data_ground_truth._validate_or_exit", lambda ws, stage: None)

    canonical_result = {
        "source_logical_rows": 100,
        "successfully_parsed_records": 98,
        "rejected_malformed_records": 2,
        "unique_field_count": 45,
    }
    monkeypatch.setattr("src.data_ground_truth.profile_dataset_schemas", lambda ws: canonical_result)

    args = SimpleNamespace(workspace=".")
    ret = cmd_profile(args)
    assert ret == 0

    captured = capsys.readouterr()
    assert "Logical rows: 100" in captured.out
    assert "Parsed: 98" in captured.out
    assert "Malformed: 2" in captured.out
    assert "Distinct fields: 45" in captured.out

