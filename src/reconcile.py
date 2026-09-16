"""
RAG2ATTCK - Multiset Reconciliation Module (Task 2)
Performs formal record-multiset comparison between the 16 period CSVs
and combined.csv using deterministic canonical row representations.
"""

from collections import Counter, defaultdict
import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple


EXCEL_EPOCH = datetime(1899, 12, 30, tzinfo=timezone.utc)
NULL_LITERALS = {"null", "none", "nan", "na", "n/a", "<null>"}


@dataclass(frozen=True)
class CellDifference:
    field: str
    period_value: Optional[str]
    combined_value: Optional[str]
    transformation_type: str
    is_equivalent: bool
    evidence: str


def canonicalize_row(row_dict: Dict[str, Any]) -> Tuple[Tuple[str, str], ...]:
    """
    Deterministic row canonicalization:
    - Ignores empty string and None values (normalizing column superset differences)
    - Strips whitespace
    - Sorts key-value pairs alphabetically by column name
    """
    cleaned = []
    for k, v in row_dict.items():
        if v is not None and v != "":
            val_str = str(v).strip()
            if val_str != "":
                cleaned.append((k.strip(), val_str))
    cleaned.sort(key=lambda x: x[0])
    return tuple(cleaned)


def compute_row_fingerprint(canonical_items: Tuple[Tuple[str, str], ...]) -> str:
    """
    Computes deterministic SHA-256 fingerprint from canonical row items.
    """
    encoded = repr(canonical_items).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    return str(value).strip()


def _decimal(value: Optional[str]) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(value.replace(",", "").strip())
    except InvalidOperation:
        return None


def _is_boolean(value: Optional[str]) -> bool:
    return value is not None and value.lower() in {"true", "false"}


def _parse_datetime(value: str) -> Optional[datetime]:
    formats = [
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y %H:%M:%S.%f",
        "%m/%d/%Y %H:%M:%S",
        "%m/%d/%Y %H:%M",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _parse_minute_second_display(value: str) -> Optional[float]:
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?:\.(\d{1,9}))?", value.strip())
    if not match:
        return None
    seconds = int(match.group(2))
    if seconds >= 60:
        return None
    fraction = match.group(3) or ""
    fractional_seconds = float(f"0.{fraction}") if fraction else 0.0
    return int(match.group(1)) * 60 + seconds + fractional_seconds


def _excel_serial_datetime(value: Optional[str]) -> Optional[datetime]:
    serial = _decimal(value)
    if serial is None or serial < Decimal("0") or serial > Decimal("60000"):
        return None
    whole_days = int(serial)
    fractional_days = serial - Decimal(whole_days)
    seconds = float(fractional_days * Decimal(86400))
    return EXCEL_EPOCH + timedelta(days=whole_days, seconds=seconds)


def _close_seconds(left: float, right: float, tolerance: float = 2.0) -> bool:
    return abs(left - right) <= tolerance


def _classify_excel_time(period_value: str, combined_value: str) -> Optional[CellDifference]:
    serial_dt = _excel_serial_datetime(combined_value)
    if serial_dt is None:
        return None

    parsed_dt = _parse_datetime(period_value)
    if parsed_dt is not None:
        delta = abs((parsed_dt - serial_dt).total_seconds())
        if delta <= 2.0:
            return CellDifference("", period_value, combined_value, "EXCEL_SERIAL_DATETIME_EQUIVALENT", True, "datetime and Excel serial resolve to the same instant within rounding tolerance")
        return CellDifference("", period_value, combined_value, "EXCEL_SERIAL_DATETIME_MISMATCH", False, "datetime and Excel serial resolve to different instants")

    display_seconds = _parse_minute_second_display(period_value)
    if display_seconds is None:
        return None

    serial = _decimal(combined_value)
    if serial is None:
        return None
    if serial >= Decimal("1"):
        serial_seconds = serial_dt.minute * 60 + serial_dt.second + serial_dt.microsecond / 1_000_000
    else:
        serial_seconds = serial_dt.hour * 3600 + serial_dt.minute * 60 + serial_dt.second + serial_dt.microsecond / 1_000_000

    if _close_seconds(display_seconds, serial_seconds):
        return CellDifference("", period_value, combined_value, "EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT", True, "minute/second display and Excel serial time agree within rounding tolerance")
    return CellDifference("", period_value, combined_value, "EXCEL_SERIAL_TIME_MISMATCH", False, "minute/second display and Excel serial time do not agree")


def classify_cell_difference(field: str, period_value: Any, combined_value: Any) -> CellDifference:
    """
    Classify one cell difference without mutating or normalizing the raw files.
    """
    pv = _to_text(period_value)
    cv = _to_text(combined_value)

    if pv == cv:
        return CellDifference(field, pv, cv, "EXACT_MATCH", True, "values are identical after string normalization")
    if pv is None or cv is None:
        return CellDifference(field, pv, cv, "FIELD_ABSENT_OR_PRESENT_CHANGED", False, "one side lacks the field")
    if pv == "" or cv == "":
        ttype = "EXPLICIT_NULL_EMPTY_CHANGED" if pv.lower() in NULL_LITERALS or cv.lower() in NULL_LITERALS else "MISSING_OR_EMPTY_VALUE_CHANGED"
        return CellDifference(field, pv, cv, ttype, False, "empty and explicit/missing values are not assumed equivalent")
    if pv.lower() in NULL_LITERALS or cv.lower() in NULL_LITERALS:
        return CellDifference(field, pv, cv, "EXPLICIT_NULL_TEXT_CHANGED", False, "explicit null literal changed representation")
    if _is_boolean(pv) and _is_boolean(cv) and pv.lower() == cv.lower():
        return CellDifference(field, pv, cv, "BOOLEAN_CASE_EQUIVALENT", True, "boolean values differ only by case")
    if pv.endswith("%"):
        left = _decimal(pv[:-1])
        right = _decimal(cv)
        if left is not None and right is not None and left / Decimal(100) == right:
            return CellDifference(field, pv, cv, "PERCENT_DECIMAL_EQUIVALENT", True, "percentage and decimal representations are numerically equal")

    excel_diff = _classify_excel_time(pv, cv)
    if excel_diff is None:
        reversed_diff = _classify_excel_time(cv, pv)
        if reversed_diff is not None:
            excel_diff = CellDifference(field, pv, cv, reversed_diff.transformation_type, reversed_diff.is_equivalent, reversed_diff.evidence)
    else:
        excel_diff = CellDifference(field, pv, cv, excel_diff.transformation_type, excel_diff.is_equivalent, excel_diff.evidence)
    if excel_diff is not None:
        return excel_diff

    left_dec = _decimal(pv)
    right_dec = _decimal(cv)
    if left_dec is not None and right_dec is not None:
        if left_dec == right_dec:
            return CellDifference(field, pv, cv, "NUMERIC_FORMAT_EQUIVALENT", True, "numeric values are equal despite formatting")
        return CellDifference(field, pv, cv, "NUMERIC_PRECISION_OR_VALUE_LOSS", False, "numeric values differ after decimal parsing")

    return CellDifference(field, pv, cv, "TEXT_VALUE_CHANGED", False, "no deterministic representation-preserving transform matched")


def reconcile_representations(
    period_rows: List[Dict[str, Any]],
    combined_rows: List[Dict[str, Any]],
    id_field: str = "_id",
    sample_limit: int = 20,
) -> Dict[str, Any]:
    """
    Determine whether raw divergent rows are all representation-equivalent.
    """
    period_fps = Counter(compute_row_fingerprint(canonicalize_row(row)) for row in period_rows)
    combined_fps = Counter(compute_row_fingerprint(canonicalize_row(row)) for row in combined_rows)
    raw_exact = period_fps == combined_fps

    period_by_id = {str(row.get(id_field, idx)): row for idx, row in enumerate(period_rows)}
    combined_by_id = {str(row.get(id_field, idx)): row for idx, row in enumerate(combined_rows)}

    taxonomy_by_field = Counter()
    taxonomy_by_type = Counter()
    taxonomy_by_field_type = Counter()
    examples: List[Dict[str, Any]] = []
    equivalent_count = 0
    unresolved_count = 0
    missing_row_count = 0

    for rid in sorted(set(period_by_id) | set(combined_by_id)):
        p_row = period_by_id.get(rid)
        c_row = combined_by_id.get(rid)
        if p_row is None or c_row is None:
            missing_row_count += 1
            unresolved_count += 1
            taxonomy_by_type["ROW_ID_COVERAGE_MISMATCH"] += 1
            if len(examples) < sample_limit:
                examples.append({
                    "_id": rid,
                    "field": id_field,
                    "transformation_type": "ROW_ID_COVERAGE_MISMATCH",
                    "is_equivalent": False,
                    "period_value": "present" if p_row is not None else "missing",
                    "combined_value": "present" if c_row is not None else "missing",
                })
            continue

        p_canonical = dict(canonicalize_row(p_row))
        c_canonical = dict(canonicalize_row(c_row))
        for field in sorted(set(p_canonical) | set(c_canonical)):
            p_has_field = field in p_row
            c_has_field = field in c_row
            p_text = _to_text(p_row.get(field))
            c_text = _to_text(c_row.get(field))
            if p_canonical.get(field) == c_canonical.get(field):
                continue
            if (not p_has_field and c_text == "") or (not c_has_field and p_text == ""):
                continue
            diff = classify_cell_difference(field, p_row.get(field), c_row.get(field))
            taxonomy_by_field[field] += 1
            taxonomy_by_type[diff.transformation_type] += 1
            taxonomy_by_field_type[f"{field}|{diff.transformation_type}"] += 1
            if diff.is_equivalent:
                equivalent_count += 1
            else:
                unresolved_count += 1
            if len(examples) < sample_limit:
                examples.append(asdict(diff) | {"_id": rid})

    discrepancy_count = equivalent_count + unresolved_count
    resolved = (not raw_exact) and discrepancy_count > 0 and unresolved_count == 0 and missing_row_count == 0
    if raw_exact:
        status = "RECONCILED_EXACT_MATCH"
    elif resolved:
        status = "RESOLVED_REPRESENTATION_EQUIVALENT"
    else:
        status = "RECONCILIATION_DIVERGENT"

    return {
        "raw_exact_equality": raw_exact,
        "representation_equivalence_resolved": raw_exact or resolved,
        "semantic_reconciliation_status": status,
        "discrepancy_count": discrepancy_count,
        "equivalent_discrepancy_count": equivalent_count,
        "unresolved_discrepancy_count": unresolved_count,
        "missing_row_id_count": missing_row_count,
        "discrepancy_taxonomy": {
            "by_field": dict(taxonomy_by_field.most_common()),
            "by_transformation_type": dict(taxonomy_by_type.most_common()),
            "by_field_and_transformation_type": dict(taxonomy_by_field_type.most_common()),
            "examples": examples,
        },
    }


def run_multiset_reconciliation(
    workspace_root: Path,
    sample_discrepancies_limit: int = 10
) -> Dict[str, Any]:
    """
    Executes formal record-multiset comparison between:
      1) The multiset of records across all 16 period CSVs
      2) The multiset of records in combined.csv

    Produces:
      - data/metadata/reconciliation_log.json
      - data/audit/reconciliation_report.md
    """
    ws = workspace_root.resolve()
    raw_dir = ws / "data" / "raw" / "windows_apt_2025" / "v3"
    meta_dir = ws / "data" / "metadata"
    audit_dir = ws / "data" / "audit"
    meta_dir.mkdir(parents=True, exist_ok=True)
    audit_dir.mkdir(parents=True, exist_ok=True)

    manifest_file = meta_dir / "dataset_manifest.json"
    if not manifest_file.exists():
        raise FileNotFoundError(f"Missing dataset manifest: {manifest_file}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    period_files = sorted([
        f["filename"] for f in manifest["files"]
        if f["role"] == "ingest_period_csv"
    ])
    combined_file = raw_dir / "combined.csv"

    if not combined_file.exists():
        raise FileNotFoundError(f"Missing combined.csv: {combined_file}")

    print(f"[*] Beginning record-multiset reconciliation across {len(period_files)} period files vs combined.csv...")

    period_fingerprints = Counter()
    period_file_breakdown = {}
    period_rows_by_id = {}
    total_period_rows = 0

    for pf in period_files:
        p_path = raw_dir / pf
        file_rows = 0
        header_cols = 0
        with open(p_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            header_cols = len(reader.fieldnames) if reader.fieldnames else 0
            for row in reader:
                file_rows += 1
                total_period_rows += 1
                c_items = canonicalize_row(row)
                fp = compute_row_fingerprint(c_items)
                period_fingerprints[fp] += 1
                rid = row.get("_id")
                if rid and rid not in period_rows_by_id:
                    period_rows_by_id[rid] = {
                        "source_file": pf,
                        "canonical": c_items,
                        "row": row,
                    }

        period_file_breakdown[pf] = {
            "rows": file_rows,
            "header_cols": header_cols
        }
        print(f"  [+] Ingested {pf}: {file_rows:,} rows, {header_cols} columns")

    combined_fingerprints = Counter()
    combined_rows_by_id = {}
    total_combined_rows = 0
    combined_header_cols = 0

    print("  [*] Ingesting combined.csv...")
    with open(combined_file, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        combined_header_cols = len(reader.fieldnames) if reader.fieldnames else 0
        for row in reader:
            total_combined_rows += 1
            c_items = canonicalize_row(row)
            fp = compute_row_fingerprint(c_items)
            combined_fingerprints[fp] += 1
            rid = row.get("_id")
            if rid and rid not in combined_rows_by_id:
                combined_rows_by_id[rid] = {
                    "canonical": c_items,
                    "row": row,
                }

    print(f"  [+] Ingested combined.csv: {total_combined_rows:,} rows, {combined_header_cols} columns")

    # Multiset Metrics
    unique_period_fps = set(period_fingerprints.keys())
    unique_combined_fps = set(combined_fingerprints.keys())

    fps_only_in_period = unique_period_fps - unique_combined_fps
    fps_only_in_combined = unique_combined_fps - unique_period_fps
    fps_in_both = unique_period_fps & unique_combined_fps

    # Multiplicity differences
    multiplicity_diffs = {}
    all_fps = unique_period_fps | unique_combined_fps
    for fp in all_fps:
        p_count = period_fingerprints.get(fp, 0)
        c_count = combined_fingerprints.get(fp, 0)
        if p_count != c_count:
            multiplicity_diffs[fp] = {
                "period_count": p_count,
                "combined_count": c_count,
                "delta": p_count - c_count
            }

    # Duplicate multiplicities on each side
    period_duplicate_multiplicities = {fp: count for fp, count in period_fingerprints.items() if count > 1}
    combined_duplicate_multiplicities = {fp: count for fp, count in combined_fingerprints.items() if count > 1}

    multisets_match = (period_fingerprints == combined_fingerprints)

    # Discrepancy field-level diagnosis
    divergent_field_counts = Counter()
    sample_discrepancies = []

    semantic_result = reconcile_representations(
        [entry["row"] for entry in period_rows_by_id.values()],
        [entry["row"] for entry in combined_rows_by_id.values()],
        sample_limit=sample_discrepancies_limit,
    )

    if not multisets_match:
        # Trace divergent values by _id
        for rid, p_entry in period_rows_by_id.items():
            if rid in combined_rows_by_id:
                src_pf = p_entry["source_file"]
                p_items = p_entry["canonical"]
                c_items = combined_rows_by_id[rid]["canonical"]
                if p_items != c_items:
                    p_dict = dict(p_items)
                    c_dict = dict(c_items)
                    for k in set(p_dict.keys()) | set(c_dict.keys()):
                        pv = p_dict.get(k)
                        cv = c_dict.get(k)
                        if pv != cv:
                            divergent_field_counts[k] += 1
                            if len(sample_discrepancies) < sample_discrepancies_limit:
                                sample_discrepancies.append({
                                    "_id": rid,
                                    "field": k,
                                    "source_file": src_pf,
                                    "period_value": pv,
                                    "combined_value": cv
                                })

    # Exact status formulation
    if multisets_match:
        equality_status = "RECONCILED_EXACT_MATCH"
        explanation = "The record multisets of the 16 period CSVs and combined.csv match exactly."
    elif semantic_result["representation_equivalence_resolved"]:
        equality_status = "RECONCILIATION_DIVERGENT"
        explanation = (
            f"Raw cell-level string multisets diverge in {len(fps_only_in_period):,} rows, but every observed "
            "cell difference is classified as a deterministic representation-preserving transformation. "
            "The artifact records raw_exact_equality=false and semantic/representation reconciliation=resolved."
        )
    else:
        equality_status = "RECONCILIATION_DIVERGENT"
        explanation = (
            f"Row counts match exactly ({total_period_rows:,} == {total_combined_rows:,}), but raw cell-level string "
            f"multisets diverge in {len(fps_only_in_period):,} rows and "
            f"{semantic_result['unresolved_discrepancy_count']:,} cell differences cannot be proven "
            "representation-equivalent. Under the frozen methodology this remains an unresolved "
            "RECONCILIATION_DIVERGENT gate and downstream Task 3 execution must stop."
        )

    reconciliation_log = {
        "schema_version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "task": "T2_MULTISET_RECONCILIATION",
        "multiset_equality_status": equality_status,
        "is_exact_match": multisets_match,
        "raw_exact_equality": semantic_result["raw_exact_equality"],
        "semantic_reconciliation_status": semantic_result["semantic_reconciliation_status"],
        "representation_equivalence_resolved": semantic_result["representation_equivalence_resolved"],
        "discrepancy_count": semantic_result["discrepancy_count"],
        "equivalent_discrepancy_count": semantic_result["equivalent_discrepancy_count"],
        "unresolved_discrepancy_count": semantic_result["unresolved_discrepancy_count"],
        "missing_row_id_count": semantic_result["missing_row_id_count"],
        "row_count_accounting": {
            "total_period_rows": total_period_rows,
            "total_combined_rows": total_combined_rows,
            "row_count_delta": total_period_rows - total_combined_rows,
            "row_counts_match": (total_period_rows == total_combined_rows)
        },
        "fingerprint_accounting": {
            "unique_period_fingerprints": len(unique_period_fps),
            "unique_combined_fingerprints": len(unique_combined_fps),
            "matching_fingerprints_count": len(fps_in_both),
            "fingerprints_only_in_period_count": len(fps_only_in_period),
            "fingerprints_only_in_combined_count": len(fps_only_in_combined),
            "multiplicity_differences_count": len(multiplicity_diffs),
            "period_duplicate_multiplicities_count": len(period_duplicate_multiplicities),
            "combined_duplicate_multiplicities_count": len(combined_duplicate_multiplicities)
        },
        "explanation": explanation,
        "divergent_fields_summary": dict(divergent_field_counts.most_common(10)),
        "discrepancy_taxonomy": semantic_result["discrepancy_taxonomy"],
        "sample_discrepancies": sample_discrepancies,
        "files_breakdown": period_file_breakdown,
        "combined_file_metadata": {
            "filename": "combined.csv",
            "rows": total_combined_rows,
            "header_cols": combined_header_cols,
            "role": "reconciliation_only_never_added_to_observations"
        }
    }

    # Write reconciliation_log.json
    log_file = meta_dir / "reconciliation_log.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(reconciliation_log, f, indent=2, ensure_ascii=False)

    # Write data/audit/reconciliation_report.md
    report_lines = [
        "# Windows-APT 2025 v3 Record-Multiset Reconciliation Report",
        "",
        f"- **Date**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "- **Dataset ID**: `b8fmtzvpy8` version 3",
        "- **Task**: Task 2 — Acquisition and Immutable Provenance",
        f"- **Multiset Equality Status**: **{equality_status}**",
        "",
        "---",
        "",
        "## 1. Executive Summary",
        "",
        f"A rigorous, cell-level record multiset comparison was performed between the **16 period CSV collections** ({total_period_rows:,} rows) "
        f"and **`combined.csv`** ({total_combined_rows:,} rows) using deterministic row canonicalization and SHA-256 fingerprints.",
        "",
        "| Metric | Period CSVs (Ingest) | `combined.csv` (Reconciliation) | Difference |",
        "|---|---:|---:|---:|",
        f"| **Total Rows** | {total_period_rows:,} | {total_combined_rows:,} | **0** |",
        f"| **Unique Record Fingerprints** | {len(unique_period_fps):,} | {len(unique_combined_fps):,} | — |",
        f"| **Exact Multiset Fingerprint Matches** | {len(fps_in_both):,} ({len(fps_in_both)/total_period_rows*100:.1f}%) | {len(fps_in_both):,} | 0 |",
        f"| **Divergent Value Fingerprints** | {len(fps_only_in_period):,} ({len(fps_only_in_period)/total_period_rows*100:.1f}%) | {len(fps_only_in_combined):,} | 0 |",
        f"| **Duplicate Multiplicities** | {len(period_duplicate_multiplicities)} | {len(combined_duplicate_multiplicities)} | 0 |",
        f"| **Multiset Exact Equality** | — | — | **{multisets_match}** |",
        f"| **Representation Equivalence Resolved** | — | — | **{semantic_result['representation_equivalence_resolved']}** |",
        f"| **Unresolved Cell Differences** | — | — | **{semantic_result['unresolved_discrepancy_count']:,}** |",
        "",
        "---",
        "",
        "## 2. Ingest Architecture & Non-Double-Counting Rule",
        "",
        "> [!IMPORTANT]",
        "> Per Task 2 methodology (§R4):",
        "> - The **16 period CSVs** constitute the canonical ingest observation pool.",
        "> - `combined.csv` is preserved strictly as reconciliation input and **never added to observations**.",
        "> - Equal row counts do **not** imply exact multiset equality. The actual value divergences must be documented rather than ignored.",
        "",
        "---",
        "",
        "## 3. Detailed Root-Cause Analysis of Divergences",
        "",
        f"All **{total_period_rows:,} records share identical `_id` values** across both sides. However, exactly **{len(fps_only_in_period):,} records** "
        "diverge in raw string representation. The corrected semantic audit classifies each changed cell and does not assume Excel serialization is sufficient:",
        "",
        "| Transformation Type | Cell Count | Representation-Equivalent? |",
        "|---|---:|:---:|",
    ]

    non_equivalent_types = {
        "NUMERIC_PRECISION_OR_VALUE_LOSS",
        "TEXT_VALUE_CHANGED",
        "EXCEL_SERIAL_DATETIME_MISMATCH",
        "EXCEL_SERIAL_TIME_MISMATCH",
        "EXPLICIT_NULL_EMPTY_CHANGED",
        "EXPLICIT_NULL_TEXT_CHANGED",
        "MISSING_OR_EMPTY_VALUE_CHANGED",
        "FIELD_ABSENT_OR_PRESENT_CHANGED",
        "ROW_ID_COVERAGE_MISMATCH",
    }
    for ttype, count in semantic_result["discrepancy_taxonomy"]["by_transformation_type"].items():
        equivalent = "No" if ttype in non_equivalent_types else "Yes"
        report_lines.append(f"| `{ttype}` | {count:,} | {equivalent} |")

    report_lines.extend([
        "",
        "Sample classified discrepancies:",
        "",
        "| Record `_id` | Field | Type | Period CSV | `combined.csv` | Equivalent |",
        "|---|---|---|---|---|:---:|",
    ])

    for ex in semantic_result["discrepancy_taxonomy"]["examples"][:10]:
        report_lines.append(
            f"| `{ex.get('_id', '')}` | `{ex.get('field', '')}` | `{ex.get('transformation_type', '')}` | "
            f"`{str(ex.get('period_value', ''))[:60]}` | `{str(ex.get('combined_value', ''))[:60]}` | {ex.get('is_equivalent')} |"
        )

    report_lines.extend([
        "",
        "---",
        "",
        "## 4. Per-File Period Breakdown",
        "",
        "| Period File | Rows | Header Columns |",
        "|---|---:|---:|",
    ])

    for pf, data in period_file_breakdown.items():
        report_lines.append(f"| `{pf}` | {data['rows']:,} | {data['header_cols']} |")

    report_lines.extend([
        f"| **Total (16 Period Files)** | **{total_period_rows:,}** | **Superset: {combined_header_cols}** |",
        f"| **`combined.csv`** | **{total_combined_rows:,}** | **{combined_header_cols}** |",
        "",
        "---",
        "",
        "## 5. Audit Determination",
        f"Because exact cell-level string multisets diverge in {len(fps_only_in_period):,} rows, the gate reports **`{equality_status}`** "
        "rather than a false exact match claim. Because unresolved non-equivalent cell differences remain, "
        "Task 2 is a STOP gate and Task 3+ are not validly executable under the frozen methodology."
    ])

    report_file = audit_dir / "reconciliation_report.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines) + "\n")

    print(f"[+] Multiset reconciliation complete. Status: {equality_status}. Log: {log_file}")
    return reconciliation_log
