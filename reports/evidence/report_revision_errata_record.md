# Scientific Report Closeout Revision & Errata Record

- **Schema Version:** `report_revision_errata_record_v1`
- **Generated At (UTC):** `2026-10-19T03:18:00Z`
- **Immutable Metric Bundle V2 (`artifacts/results/canonical_metric_bundle_v2.json`):** `442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34` (Unchanged)
- **Immutable Run Seal V1 (`reports/evidence/canonical_run_seal_v1.json`):** `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` (Unchanged)
- **Populated Report Slots (`reports/evidence/populated_report_slots_canonical.json`):** `7c5a37f2659035108a70b7f161114f5d395164fbb75e77e` (`7c5a37f2659035108a70b7f161114f5d35e6c903a5e77df1d395164fbb75e77e`, Unchanged)

## 1. Historical Pre-Closeout Archives
- `reports/evidence/historical/r9_final_artifact_inventory_20261003.json`: `a702d98e390635cdb8d9a10ad6cd5911aa1e77cebbc8bc6111e070925ac30fa9` (`38,323` bytes)
- `reports/evidence/historical/visual_qa_inspection_record_20261003.json`: `dd3e5d5a0e61bf7aef233376f52256ec7c06a2cbea266963d154146acbae8da5` (`15,697` bytes)

## 2. Remediated Defects (`ERR-01` .. `ERR-04`)
1. **`ERR-01` (`AC.01` — Okuma et al. [9] `UNVERIFIED` Synchronization Across `.md` and `.docx`):** Synchronized `docs/report/scientific_report.docx` and `reports/evidence/canonical_populated_report.docx` with the Markdown source so Table 1b Row 16 and Section 2.1 bound Okuma et al. (2023) strictly as `UNVERIFIED`.
2. **`ERR-02` (`AD.01` — LADE [12] `T33` Full-Text Verification Remediation):** Verified the 28-page LADE author manuscript PDF (`SHA-256: 6e8384569254bc4cf82dd4d0191746907ff40fa76016275946651cf47d6f4985`), updating Section 2.1 (`6/8` full-text audited, `2/8` partial/metadata-only/access-blocked), Table 1b Rows 8/12/14/16 (`gpt-oss-120B, Llama-3.3-70B, Mistral-Small-3.2-24B, Gemini-2.5-Pro`; `AVIATOR (35/32 seqs) & Caldera-derived (33 seqs per 2:1 setting + 5 lateral + 8 multi-stage)`; output cutoff $k \in \{3,10\}$), and Reference 12 (`[FULL TEXT VERIFIED]`).
3. **`ERR-03` (`AE.01` — Section 6.3 Provider Retry Locator Standardization):** Added the explicit `inputs/request_journal.jsonl` locator for the single transient retry (`("view_d870d574", "rag_k1")`, `run_id="live-66b94b1676bf46a9"`, lines `48479–48482`, lifecycle `48476–48485`, `ordinal=5387` $\to$ `ordinal=5388`).
4. **`ERR-04` (`AF.01` — Status Header Synchronization & Dual-Path Parity):** Updated the report status line to `**Status:** CANONICAL CANDIDATE — PENDING ROOT FINAL REVIEW — **Status:** CORRECTED RELEASE CANDIDATE — PENDING OWNER CLOSEOUT SIGN-OFF` and enforced 100% byte-for-byte identity between `reports/evidence/canonical_populated_report.{md,docx}` and `docs/report/scientific_report.{md,docx}`.

## 3. Artifact Hash Transitions

| Artifact Path | Historical SHA-256 | Historical Size | Closeout RC SHA-256 | Closeout RC Size |
| :--- | :--- | :---: | :--- | :---: |
| `reports/evidence/canonical_populated_report.md` | `5cbaa094095adbd163c0ea516a32df799e9a9af9efb35c47b40c04c6fc44858d` (CRLF) / `5cbaa094dd6fd717d633de4655221bf953e62f7848ca250b4d11936a4a373fb8` (LF) | 105,456 B (LF) | `1d1ff1ce709206b2cf1f9cdca713a61f286b8841ca5c8487f76debba8aa9541a` | 105,497 B |
| `docs/report/scientific_report.md` | `083fd1be204f9bb2e149c1e16ce427481fd71e67c94bf925d9a4a32bc4f1273f` | 105,499 B | `1d1ff1ce709206b2cf1f9cdca713a61f286b8841ca5c8487f76debba8aa9541a` | 105,497 B |
| `reports/evidence/canonical_populated_report.docx` | `c5ce49f7e57ee2d86d79daab50def273af6dbb4c4393da61340f033b63306ccb` | 320,008 B | `25fbed2e7227456345fba407fed1b1ed476dd484a0841f805718fc78acdf783a` | 320,364 B |
| `docs/report/scientific_report.docx` | `43297b17b2a505fdad96e94ac88fdc868e412bc493682be5e1bdc048bc0bb2dd` | 320,899 B | `25fbed2e7227456345fba407fed1b1ed476dd484a0841f805718fc78acdf783a` | 320,364 B |
| `reports/evidence/canonical_populated_report.pdf` | `5604e53fb064d2d42c69e4da3ade0b4d4354900fb5706e67c69590167317ee23` | 1,286,065 B | `e47a8eae2b8f64a878d3b6eb49fc5d6db341dac311bdbd8173d25f610b343514` | 1,290,068 B (41 pages) |
