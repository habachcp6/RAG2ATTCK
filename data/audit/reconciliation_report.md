# Windows-APT 2025 v3 Record-Multiset Reconciliation Report

- **Date**: 2026-09-16 16:31:09 UTC
- **Dataset ID**: `b8fmtzvpy8` version 3
- **Task**: Task 2 — Acquisition and Immutable Provenance
- **Multiset Equality Status**: **RECONCILIATION_DIVERGENT**

---

## 1. Executive Summary

A rigorous, cell-level record multiset comparison was performed between the **16 period CSV collections** (102,011 rows) and **`combined.csv`** (102,011 rows) using deterministic row canonicalization and SHA-256 fingerprints.

| Metric | Period CSVs (Ingest) | `combined.csv` (Reconciliation) | Difference |
|---|---:|---:|---:|
| **Total Rows** | 102,011 | 102,011 | **0** |
| **Unique Record Fingerprints** | 102,011 | 102,011 | — |
| **Exact Multiset Fingerprint Matches** | 36,674 (36.0%) | 36,674 | 0 |
| **Divergent Value Fingerprints** | 65,337 (64.0%) | 65,337 | 0 |
| **Duplicate Multiplicities** | 0 | 0 | 0 |
| **Multiset Exact Equality** | — | — | **False** |
| **Representation Equivalence Resolved** | — | — | **False** |
| **Unresolved Cell Differences** | — | — | **15,713** |

---

## 2. Ingest Architecture & Non-Double-Counting Rule

> [!IMPORTANT]
> Per Task 2 methodology (§R4):
> - The **16 period CSVs** constitute the canonical ingest observation pool.
> - `combined.csv` is preserved strictly as reconciliation input and **never added to observations**.
> - Equal row counts do **not** imply exact multiset equality. The actual value divergences must be documented rather than ignored.

---

## 3. Detailed Root-Cause Analysis of Divergences

All **102,011 records share identical `_id` values** across both sides. However, exactly **65,337 records** diverge in raw string representation. The corrected semantic audit classifies each changed cell and does not assume Excel serialization is sufficient:

| Transformation Type | Cell Count | Representation-Equivalent? |
|---|---:|:---:|
| `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | 69,352 | Yes |
| `BOOLEAN_CASE_EQUIVALENT` | 15,887 | Yes |
| `NUMERIC_PRECISION_OR_VALUE_LOSS` | 15,440 | No |
| `NUMERIC_FORMAT_EQUIVALENT` | 14,948 | Yes |
| `EXCEL_SERIAL_DATETIME_EQUIVALENT` | 11,282 | Yes |
| `EXCEL_SERIAL_DATETIME_MISMATCH` | 264 | No |
| `TEXT_VALUE_CHANGED` | 4 | No |
| `EXPLICIT_NULL_EMPTY_CHANGED` | 3 | No |
| `PERCENT_DECIMAL_EQUIVALENT` | 2 | Yes |
| `EXCEL_SERIAL_TIME_MISMATCH` | 2 | No |

Sample classified discrepancies:

| Record `_id` | Field | Type | Period CSV | `combined.csv` | Equivalent |
|---|---|---|---|---|:---:|
| `'-0qa7ZMBNimV4ECv_4DV` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `02:51.3` | `0.001982639` | True |
| `'-0rz7ZMBNimV4ECv04Lf` | `_source.data.win.eventdata.creationUtcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `39:52.3` | `0.027688657` | True |
| `'-0rz7ZMBNimV4ECv04Lf` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `39:52.3` | `0.027688657` | True |
| `'-1onnZMBW7IoYvN2vDm0` | `_source.predecoder.timestamp` | `EXCEL_SERIAL_DATETIME_MISMATCH` | `12/6/2025 21:37` | `45632.90084` | False |
| `'-1pQnZMBW7IoYvN2LDu9` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `51:33.1` | `45632.7858` | True |
| `'-1qln5MBW7IoYvN2AEAV` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `43:23.6` | `45633.23847` | True |
| `'-1qlnZMBW7IoYvN2UD0q` | `_source.data.win.eventdata.creationUtcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `24:28.3` | `45632.85033` | True |
| `'-1qlnZMBW7IoYvN2UD0q` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `24:28.3` | `45632.85033` | True |
| `'-1rcn5MBW7IoYvN2v0MH` | `_source.data.win.eventdata.utcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `44:19.4` | `45633.28078` | True |
| `'-1rtpJMBW7IoYvN2B07T` | `_source.data.win.eventdata.creationUtcTime` | `EXCEL_SERIAL_TIME_DISPLAY_EQUIVALENT` | `20:11.2` | `45634.26402` | True |

---

## 4. Per-File Period Breakdown

| Period File | Rows | Header Columns |
|---|---:|---:|
| `01-03-December.csv` | 8,838 | 289 |
| `03-04-December.csv` | 7,291 | 240 |
| `04-07-December.csv` | 7,750 | 224 |
| `07-10-December.csv` | 9,185 | 227 |
| `1-11-November.csv` | 8,807 | 311 |
| `10-December-P1.csv` | 9,049 | 157 |
| `10-December-P2.csv` | 1,188 | 191 |
| `11-12-December.csv` | 9,655 | 224 |
| `11-16-November.csv` | 6,554 | 147 |
| `12-13-December.csv` | 6,406 | 221 |
| `13-14-December.csv` | 9,738 | 200 |
| `14-17-December.csv` | 5,644 | 204 |
| `22-December.csv` | 1,173 | 175 |
| `23-30-November.csv` | 8,038 | 300 |
| `28-October-01-November.csv` | 693 | 208 |
| `30-November.csv` | 2,002 | 189 |
| **Total (16 Period Files)** | **102,011** | **Superset: 377** |
| **`combined.csv`** | **102,011** | **377** |

---

## 5. Audit Determination
Because exact cell-level string multisets diverge in 65,337 rows, the gate reports **`RECONCILIATION_DIVERGENT`** rather than a false exact match claim. Because unresolved non-equivalent cell differences remain, Task 2 is a STOP gate and Task 3+ are not validly executable under the frozen methodology.
