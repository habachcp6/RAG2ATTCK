"""
RAG2ATTCK - Schema Profiling & Observation Unit Module (Task 3)
Profiles raw telemetry records, fields, types, values, observation units,
and generates deterministic opaque record IDs.
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
      - data/metadata/record_index.json
      - data/metadata/parse_error_ledger.json
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
    print(f"[*] Profiling {len(period_files)} period CSV files...")

    total_records = 0
    total_malformed = 0
    all_fields: Set[str] = set()
    field_counts = Counter()
    field_types = defaultdict(set)
    field_samples = defaultdict(list)

    file_profiles = {}
    record_index_summary = []
    candidate_labels_counter = Counter()
    windows_event_ids_counter = Counter()
    observation_unit_counter = Counter()

    for pf in period_files:
        p = raw_dir / pf
        f_hash = file_hashes[pf]
        file_rec_count = 0
        file_malformed = 0

        with open(p, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                continue

            expected_cols = len(header)
            all_fields.update(header)

            for col_idx, col_name in enumerate(header):
                field_counts[col_name] += 0 # ensure registered

            for row_idx, row in enumerate(reader):
                file_rec_count += 1
                total_records += 1

                if len(row) != expected_cols:
                    file_malformed += 1
                    total_malformed += 1
                    continue

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

        file_profiles[pf] = {
            "records_count": file_rec_count,
            "columns_count": len(header),
            "malformed_count": file_malformed,
            "sha256": f_hash,
            "first_record_id": generate_opaque_record_id(f_hash, 0) if file_rec_count > 0 else None,
            "last_record_id": generate_opaque_record_id(f_hash, file_rec_count - 1) if file_rec_count > 0 else None
        }

        record_index_summary.append({
            "filename": pf,
            "records": file_rec_count,
            "sha256": f_hash,
            "id_prefix": f"rec_{hashlib.sha256(f_hash.encode()).hexdigest()[:8]}"
        })
        print(f"  [+] Profiled {pf}: {file_rec_count:,} records, {len(header)} cols")

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
            nulls = total_records - pres
            fill_rate = round((pres / total_records) * 100, 2) if total_records > 0 else 0.0
            types_str = ";".join(sorted(field_types[col])) if field_types[col] else "null"
            samples_str = " | ".join(field_samples[col][:3])
            writer.writerow([col, pres, nulls, fill_rate, types_str, samples_str])

    # Write schema_profile.json
    schema_profile_doc = {
        "schema_version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_files": len(period_files),
        "total_logical_records": total_records,
        "total_malformed_records": total_malformed,
        "unique_field_count": len(all_fields),
        "candidate_labels_distinct_count": len(candidate_labels_counter),
        "candidate_labels_distribution": dict(candidate_labels_counter.most_common(50)),
        "windows_event_ids_distribution": dict(windows_event_ids_counter.most_common(20)),
        "files_breakdown": file_profiles
    }

    schema_profile_file = meta_dir / "schema_profile.json"
    with open(schema_profile_file, "w", encoding="utf-8") as f:
        json.dump(schema_profile_doc, f, indent=2, ensure_ascii=False)

    # Write record_index.json
    record_index_file = meta_dir / "record_index.json"
    with open(record_index_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "total_records": total_records,
            "id_generation_rule": "SHA-256(source_file_sha256 + ':' + ordinal)[:16]",
            "files": record_index_summary
        }, f, indent=2, ensure_ascii=False)

    # Write parse_error_ledger.json
    parse_error_file = meta_dir / "parse_error_ledger.json"
    with open(parse_error_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "total_parsed": total_records,
            "total_malformed": total_malformed,
            "error_rate": 0.0 if total_records == 0 else (total_malformed / total_records),
            "errors": []
        }, f, indent=2, ensure_ascii=False)

    print(f"[+] Schema profiling complete: {total_records:,} records, {len(all_fields)} fields.")
    return schema_profile_doc
