# Scientific Report Closeout Revision & Errata Record

- **Schema Version:** `report_revision_errata_record_v1`
- **Generated At (UTC):** `2026-10-19T03:18:00Z`
- **Immutable Metric Bundle V2 (`artifacts/results/canonical_metric_bundle_v2.json`):** `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` (`49,465` bytes, Unchanged)
- **Immutable Run Seal V1 (`reports/evidence/canonical_run_seal_v1.json`):** `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` (`3,046` bytes, Unchanged)
- **Populated Report Slots (`reports/evidence/populated_report_slots_canonical.json`):** `7c5a37f2659035108a70b7f161114f5d35e6c903a5e77df1d395164fbb75e77e` (`15,010` bytes, Unchanged)
- **Immutable Release Archive (`artifacts/packages/public_v4_candidate_20261003.zip`):** `1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1` (`2,343,105` bytes, Unchanged)

## 1. Historical Pre-Closeout Archives
- `reports/evidence/historical/r9_final_artifact_inventory_20261003.json`: `a702d98e390635cdb8d9a10ad6cd5911aa1e77cebbc8bc6111e070925ac30fa9` (`38,323` bytes)
- `reports/evidence/historical/visual_qa_inspection_record_20261003.json`: `dd3e5d5a0e61bf7aef233376f52256ec7c06a2cbea266963d154146acbae8da5` (`15,697` bytes)

## 2. Remediated Defects (`ERR-01` .. `ERR-04`)
1. **`ERR-01` (`AC.01` — Okuma et al. [9] `UNVERIFIED` Synchronization Across `.md` and `.docx`):** Synchronized `docs/report/scientific_report.docx` and `reports/evidence/canonical_populated_report.docx` with the Markdown source so Table 1b Row 16 and Section 2.1 bound Okuma et al. (2023) strictly as `UNVERIFIED`.
2. **`ERR-02` (`AD.01` — LADE [12] `T33` Full-Text Verification Remediation):** Verified the 28-page LADE author manuscript PDF (`SHA-256: 6e8384569254bc4cf82dd4d0191746907ff40fa76016275946651cf47d6f4985`), updating Section 2.1 (`6/8` full-text audited, `2/8` partial/metadata-only/access-blocked), Table 1b Rows 8/12/14/16 (`gpt-oss-120B, Llama-3.3-70B, Mistral-Small-3.2-24B, Gemini-2.5-Pro`; `AVIATOR (35/32 seqs) & Caldera-derived (33 APT seqs per 2:1 & 10:1 setting [including 20 profile, 5 lateral, 8 multi-stage] + 33 benign)`; output cutoff $k \in \{3,10\}$), and Reference 12 (`[FULL TEXT VERIFIED]`).
3. **`ERR-03` (`AE.01` — Section 6.3 Provider Retry Locator Standardization):** Added the explicit `inputs/request_journal.jsonl` locator for the single transient retry (`("view_d870d574", "rag_k1")`, `run_id="live-66b94b1676bf46a9"`, lines `48479–48482`, lifecycle `48476–48485`, `ordinal=5387` $\to$ `ordinal=5388`, settled at `inputs/rag_k1_predictions.jsonl` 1-based physical line `1078` [0-based index `1077`, file `sha256="745cb883a90b4d1bac7c76c4007b143893834530a843e153fc24277aae5da7ac"`] with `record_sha256="e9146fe74aa5769faa5dc7df70205e62924fcf8c0e3a53946c50f96ddb2f8086"` and `raw_line_lf_sha256="9056b85dbba694a622acde4743c11803465c6e84ef34a32a3bb6385d12258562"`). *Historical Errata Note:* Earlier informal references to `"line 5124"` and `"line 1179"` are superseded by the exact physical lines `48479–48482` (`ordinal 5387–5388`) in `inputs/request_journal.jsonl` and 1-based physical line `1078` in `inputs/rag_k1_predictions.jsonl`.
4. **`ERR-04` (`AF.01` — Status Header Synchronization & Dual-Path Parity):** Updated the report status line to `**Status:** CANONICAL CANDIDATE — PENDING ROOT FINAL REVIEW (CORRECTED RELEASE CANDIDATE — PENDING OWNER CLOSEOUT SIGN-OFF)` and enforced 100% byte-for-byte identity between `reports/evidence/canonical_populated_report.{md,docx}` and `docs/report/scientific_report.{md,docx}`.

## 3. Artifact Hash Transitions

| Artifact Path | Historical SHA-256 (`5eb6bd6f`) | Historical Size (`5eb6bd6f`) | Closeout RC SHA-256 | Closeout RC Size |
| :--- | :--- | :---: | :--- | :---: |
| `reports/evidence/canonical_populated_report.md` | `5cbaa094095adbd163c0ea516a32df799e9a9af9efb35c47b40c04c6fc44858d` (LF) / `0cc9a5b971f383c4afef2f2117a6812d6d35d00963304698e9959f868acbc30a` (CRLF) | 105,354 B (LF) / 106,090 B (CRLF) | `e3800226e5ba44af273765132b18a771839fca211bbc2426903bf1f343fbcbed` (LF) / `a9efbdc5f8a53954286f679f0799dd50dbca011e7df1a4883d4a0b88fd33532e` (CRLF) | 105,575 B (LF) / 106,311 B (CRLF) |
| `docs/report/scientific_report.md` | `5cbaa094095adbd163c0ea516a32df799e9a9af9efb35c47b40c04c6fc44858d` (LF) / `0cc9a5b971f383c4afef2f2117a6812d6d35d00963304698e9959f868acbc30a` (CRLF) | 105,354 B (LF) / 106,090 B (CRLF) | `e3800226e5ba44af273765132b18a771839fca211bbc2426903bf1f343fbcbed` (LF) / `a9efbdc5f8a53954286f679f0799dd50dbca011e7df1a4883d4a0b88fd33532e` (CRLF) | 105,575 B (LF) / 106,311 B (CRLF) |
| `reports/evidence/canonical_populated_report.docx` | `c5ce49f7e57ee2d86d79daab50def273af6dbb4c4393da61340f033b63306ccb` | 320,008 B | `d7970749c43c8dc422a170220c48fafc8955be7500eb8dfa8cf743286f9f0032` | 320,401 B |
| `docs/report/scientific_report.docx` | `43297b17b2a505fdad96e94ac88fdc868e412bc493682be5e1bdc048bc0bb2dd` | 320,049 B | `d7970749c43c8dc422a170220c48fafc8955be7500eb8dfa8cf743286f9f0032` | 320,401 B |
| `reports/evidence/canonical_populated_report.pdf` | `5604e53fb064d2d42c69e4da3ade0b4d4354900fb5706e67c69590167317ee23` | 1,286,065 B | `5d01169187c9bb56164efde4acff97e87f0d47deb15dba81139e64b49de635ad` | 1,292,377 B (41 pages) |
