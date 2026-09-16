# Windows-APT 2025 v3 Record-Multiset Reconciliation Report

- **Date**: 2026-09-16 04:12:17 UTC
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

---

## 2. Ingest Architecture & Non-Double-Counting Rule

> [!IMPORTANT]
> Per Task 2 methodology (§R4):
> - The **16 period CSVs** constitute the canonical ingest observation pool.
> - `combined.csv` is preserved strictly as reconciliation input and **never added to observations**.
> - Equal row counts do **not** imply exact multiset equality. The actual value divergences must be documented rather than ignored.

---

## 3. Detailed Root-Cause Analysis of Divergences

All **102,011 records share identical `_id` values** across both sides. However, exactly **65,337 records** diverge in raw string representation due to Microsoft Excel date/number serialization introduced by the dataset authors during publication:

| Divergent Field | Affected Record Count | Period CSV Representation | `combined.csv` Representation | Root Cause |
|---|---:|---|---|---|
| `_source.data.win.eventdata.utcTime` | 3,333+ | `24:27.7` | `45627.26699` | Excel serial date number conversion |
| `_source.data.win.eventdata.creationUtcTime` | 1,734+ | `26:00.7` | `45627.26806` | Excel serial date number conversion |
| `_source.data.win.eventdata.binary` | 30+ | `4.60061E+15` | `4.60E+15` | Excel scientific notation precision truncation |
| `_source.predecoder.timestamp` | 5+ | `12/2/2025 15:12` | `45628.63363` | Excel date serial conversion |
| `_source.data.win.eventdata.passwordLastSet` | 4+ | `11/26/2024 1:41` | `45622.07014` | Excel date serial conversion |

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
Because exact cell-level string multisets diverge in 65,337 rows, the gate reports **`RECONCILIATION_DIVERGENT`** rather than a false exact match claim. Ingest proceeds strictly from the 16 period CSVs.
