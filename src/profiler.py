"""
RAG2ATTCK - Schema Profiling & Observation Unit Module (Task 3)
Profiles raw telemetry records, fields, types, values, observation units,
enforces strict parse accounting, and generates deterministic row-level record index.
"""

from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


def generate_opaque_record_id(file_sha256: str, record_ordinal: int) -> str:
    """
    Generates deterministic opaque record ID from source file SHA-256 and 0-indexed ordinal.
    Formula: rec_{SHA-256(file_sha256 + ':' + str(record_ordinal))[:16]}
    """
    token = f"{file_sha256}:{record_ordinal}".encode("utf-8")
    return f"rec_{hashlib.sha256(token).hexdigest()[:16]}"


def profile_dataset_schemas(
    workspace_root: Path,
    sample_values_limit: int = 5
) -> Dict[str, Any]:
    """
    Profiles all 16 period CSVs in data/raw/windows_apt_2025/v3/.
    Produces:
      - data/metadata/schema_profile.json
      - data/metadata/field_inventory.csv
      - data/metadata/record_index.csv (deterministic row-level index)
      - data/metadata/record_index.json (index manifest)
      - data/metadata/parse_error_ledger.json (exact parse accounting)
    """
    ws = workspace_root.resolve()
    raw_dir = ws / "data" / "raw" / "windows_apt_2025" / "v3"
    meta_dir = ws / "data" / "metadata"
    meta_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = meta_dir / "dataset_manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing dataset manifest: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    file_hashes = {
        item["filename"]: item["sha256"]
        for item in manifest_data["files"]
        if item["role"] == "ingest_period_csv"
    }

    period_files = sorted(file_hashes.keys())
    print(f"[*] Profiling {len(period_files)} period CSV files with strict parse accounting...")

    total_source_logical_rows = 0
    total_parsed_records = 0
    total_malformed_records = 0
    parse_errors: List[Dict[str, Any]] = []

    all_fields: Set[str] = set()
    field_counts = Counter()
    field_types = defaultdict(set)
    field_samples = defaultdict(list)

    file_profiles = {}
    record_index_summary = []
    candidate_labels_counter = Counter()
    windows_event_ids_counter = Counter()
    observation_unit_counter = Counter()

    record_index_csv_path = meta_dir / "record_index.csv"

    with open(record_index_csv_path, "w", encoding="utf-8", newline="") as idx_f:
        index_writer = csv.writer(idx_f)
        index_writer.writerow(["record_id", "source_file", "source_file_sha256", "record_ordinal"])

        for pf in period_files:
            p = raw_dir / pf
            f_hash = file_hashes[pf]
            file_logical_rows = 0
            file_parsed_count = 0
            file_malformed_count = 0

            with open(p, "r", encoding="utf-8-sig", errors="replace") as f:
                reader = csv.reader(f)
                try:
                    header = next(reader)
                except StopIteration:
                    continue

                expected_cols = len(header)
                all_fields.update(header)

                for col_name in header:
                    field_counts[col_name] += 0  # ensure registered

                for row_idx, row in enumerate(reader):
                    file_logical_rows += 1
                    total_source_logical_rows += 1

                    # Parse accounting check
                    if len(row) != expected_cols:
                        file_malformed_count += 1
                        total_malformed_records += 1
                        parse_errors.append({
                            "source_file": pf,
                            "row_index": row_idx,
                            "expected_columns": expected_cols,
                            "actual_columns": len(row),
                            "reason": "COLUMN_COUNT_MISMATCH"
                        })
                        continue

                    # Successfully parsed record
                    ordinal = file_parsed_count
                    rec_id = generate_opaque_record_id(f_hash, ordinal)
                    index_writer.writerow([rec_id, pf, f_hash, ordinal])

                    file_parsed_count += 1
                    total_parsed_records += 1

                    for col_idx, val in enumerate(row):
                        val_str = val.strip()
                        col_name = header[col_idx]
                        if val_str:
                            field_counts[col_name] += 1
                            if len(field_samples[col_name]) < sample_values_limit and val_str not in field_samples[col_name]:
                                field_samples[col_name].append(val_str[:120])

                            # Type profiling
                            if val_str.isdigit() or (val_str.startswith("-") and val_str[1:].isdigit()):
                                field_types[col_name].add("integer")
                            elif val_str.startswith("[") and val_str.endswith("]"):
                                field_types[col_name].add("json_array")
                            elif val_str.lower() in ("true", "false"):
                                field_types[col_name].add("boolean")
                            else:
                                field_types[col_name].add("string")

                            # Candidate labels & observation units
                            if col_name == "_source.rule.mitre.id":
                                candidate_labels_counter[val_str] += 1
                            elif col_name == "_source.data.win.system.eventID":
                                windows_event_ids_counter[val_str] += 1
                            elif col_name == "_source.rule.description":
                                observation_unit_counter[val_str] += 1

            # Invariant check per file
            assert file_logical_rows == file_parsed_count + file_malformed_count

            file_profiles[pf] = {
                "source_logical_rows": file_logical_rows,
                "successfully_parsed_records": file_parsed_count,
                "rejected_malformed_records": file_malformed_count,
                "columns_count": len(header),
                "sha256": f_hash,
                "first_record_id": generate_opaque_record_id(f_hash, 0) if file_parsed_count > 0 else None,
                "last_record_id": generate_opaque_record_id(f_hash, file_parsed_count - 1) if file_parsed_count > 0 else None
            }

            record_index_summary.append({
                "filename": pf,
                "sha256": f_hash,
                "source_logical_rows": file_logical_rows,
                "parsed_records": file_parsed_count,
                "first_record_id": generate_opaque_record_id(f_hash, 0) if file_parsed_count > 0 else None,
                "last_record_id": generate_opaque_record_id(f_hash, file_parsed_count - 1) if file_parsed_count > 0 else None
            })
            print(f"  [+] Profiled {pf}: {file_parsed_count:,} parsed, {file_malformed_count} malformed, {len(header)} cols")

    # Global parse accounting invariant
    assert total_source_logical_rows == total_parsed_records + total_malformed_records

    # Hash record_index.csv
    record_index_sha256 = hashlib.sha256(record_index_csv_path.read_bytes()).hexdigest()

    # Write field_inventory.csv
    field_inventory_file = meta_dir / "field_inventory.csv"
    with open(field_inventory_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "field_name", "present_record_count", "null_record_count",
            "fill_rate_percent", "inferred_types", "sample_values"
        ])
        for col in sorted(all_fields):
            pres = field_counts[col]
            nulls = total_parsed_records - pres
            fill_rate = round((pres / total_parsed_records) * 100, 2) if total_parsed_records > 0 else 0.0
            types_str = ";".join(sorted(field_types[col])) if field_types[col] else "null"
            samples_str = " | ".join(field_samples[col][:3])
            writer.writerow([col, pres, nulls, fill_rate, types_str, samples_str])

    # Write schema_profile.json
    schema_profile_doc = {
        "schema_version": "1.0.0",
        "task": "T3_SCHEMA_PROFILING",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_files": len(period_files),
        "source_logical_rows": total_source_logical_rows,
        "successfully_parsed_records": total_parsed_records,
        "rejected_malformed_records": total_malformed_records,
        "accounting_formula": "source_logical_rows = successfully_parsed_records + rejected_malformed_records",
        "accounting_invariant_holds": (total_source_logical_rows == total_parsed_records + total_malformed_records),
        "unique_field_count": len(all_fields),
        "candidate_labels_distinct_count": len(candidate_labels_counter),
        "candidate_labels_distribution": dict(candidate_labels_counter.most_common(50)),
        "windows_event_ids_distribution": dict(windows_event_ids_counter.most_common(20)),
        "observation_units_distribution": dict(observation_unit_counter.most_common(20)),
        "files_breakdown": file_profiles
    }

    schema_profile_file = meta_dir / "schema_profile.json"
    with open(schema_profile_file, "w", encoding="utf-8") as f:
        json.dump(schema_profile_doc, f, indent=2, ensure_ascii=False)

    # Write record_index.json (manifest for record_index.csv)
    record_index_file = meta_dir / "record_index.json"
    with open(record_index_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "task": "T3_RECORD_INDEX",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_records": total_parsed_records,
            "id_generation_formula": "rec_{hashlib.sha256(f'{source_file_sha256}:{record_ordinal}'.encode('utf-8')).hexdigest()[:16]}",
            "index_format": "CSV",
            "index_file_relative_path": "data/metadata/record_index.csv",
            "index_file_size_bytes": record_index_csv_path.stat().st_size,
            "index_file_sha256": record_index_sha256,
            "files": record_index_summary
        }, f, indent=2, ensure_ascii=False)

    # Write parse_error_ledger.json
    parse_error_file = meta_dir / "parse_error_ledger.json"
    with open(parse_error_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source_logical_rows": total_source_logical_rows,
            "successfully_parsed_records": total_parsed_records,
            "rejected_malformed_records": total_malformed_records,
            "accounting_formula": "source_logical_rows = successfully_parsed_records + rejected_malformed_records",
            "accounting_invariant_holds": (total_source_logical_rows == total_parsed_records + total_malformed_records),
            "error_rate": 0.0 if total_source_logical_rows == 0 else (total_malformed_records / total_source_logical_rows),
            "error_count": len(parse_errors),
            "errors": parse_errors
        }, f, indent=2, ensure_ascii=False)

    print(f"[+] Schema profiling complete: {total_parsed_records:,} parsed, {total_malformed_records} malformed, {len(all_fields)} fields.")
    return schema_profile_doc
