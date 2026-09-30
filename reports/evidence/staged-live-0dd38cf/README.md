# RAG2ATTCK Staged Live Test Evidence Package

This directory contains the machine-generated, cryptographically verified audit evidence for the staged live execution and resume test on merged `main` commit `0dd38cf7c025d73aa2736696e28753a9f480d422`.

## Execution Provenance
- **Repository Commit**: `0dd38cf7c025d73aa2736696e28753a9f480d422`
- **Run ID**: `live-674d2c86c7fa4deb`
- **Protocol Version**: `experiment-protocol-v1.1`
- **Protocol SHA-256**: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`
- **Config SHA-256**: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`
- **Code Manifest SHA-256**: `32f8439dcda33de3de1d02cf9eeac956752ed690f0a2482a3284c8424fbaa4aa`
- **Manifest SHA-256**: `0b682a389bb5b25abbe3205927b4d1d7b9b54dd3437382ab00cee755c04a7139`
- **Human Authorization Reference**: `733a85128d052109` (SHA-256 digest prefix)

## Verification Verdict
```text
STAGED_EVIDENCE_VERIFICATION: PASS
manifest_valid: True
code_manifest_valid: True
protocol_lock_valid: True
config_lock_valid: True
run_id_consistent: True
records: 7
provider_attempts: 7
duplicate_requests: 0
resume_new_records: 2
record_sha_mismatches: 0
journal_sequence_errors: 0
secret_leaks: 0
```

## Record-Level Execution Audit (Derived from Live Artifacts)
| Ordinal | Sample ID | Condition | Status | Response ID | Model ID | Latency | Record SHA-256 |
|---|---|---|---|---|---|---|---|
| 1 | `view_00477e30` | `no_rag` | `VALID` | `resp_0fe1ea0907c98ee8006abd3c2902dc87d08ee9b785c8d32473` | `gpt-5.6-luna` | `5460.5ms` | `2f4aba846be1d228...` |
| 2 | `view_00477e30` | `rag_k1` | `VALID` | `resp_056d900f4ed953a2006abd3c2c2c4887d0a473885d8efa4e40` | `gpt-5.6-luna` | `2348.1ms` | `cd237dd49cb868fd...` |
| 3 | `view_00477e30` | `rag_k3` | `VALID` | `resp_0a45787ac870232d006abd3c2e827087d0bf60381d91d338d8` | `gpt-5.6-luna` | `2654.3ms` | `e4de90ebfb66e986...` |
| 4 | `view_00477e30` | `rag_k5` | `VALID` | `resp_0d0966e2903e196f006abd3c312d3087d0b12e5205bedd4f98` | `gpt-5.6-luna` | `2335.2ms` | `e1531ee8793a5157...` |
| 5 | `view_00477e30` | `rag_k10` | `VALID` | `resp_0dd109ab0e0e3640006abd3c33873087d0961d7f5209859661` | `gpt-5.6-luna` | `2955.9ms` | `8e6129529627875e...` |
| 6 | `view_00540be5` | `no_rag` | `VALID` | `resp_025e53271467f433006abd3d542a5887d0be26fb240cd7c53c` | `gpt-5.6-luna` | `3913.2ms` | `e908797c4346ce79...` |
| 7 | `view_00540be5` | `rag_k1` | `VALID` | `resp_0e7c109e743e7c47006abd3d56f29887d086c8ded24f8f6381` | `gpt-5.6-luna` | `4241.1ms` | `bcb6382de06b1232...` |

## Verification Accounting
- **Initial Run (`--stop-after 5`)**: completed 5 records, 5 provider attempts.
- **Resume Test (`--stop-after 2`)**: appended 2 new records, 2 provider attempts.
- **Total Consumed**: 7 records / 7 attempts.
- **Duplicate Requests**: 0 (0 re-executions).
- **Run ID Continuity**: `live-674d2c86c7fa4deb` maintained across initial run and resume.

## Files in Package
- `staged_live_audit.json`: High-level summary and verification metrics.
- `staged_live_file_hashes.json`: SHA-256 hashes and sizes of all runtime experiment artifacts.
- `journal_audit.json`: Detailed validation of request journal sequence, transitions, ordinals, and completions.
- `records_audit.json`: Detailed record-level metadata, latency, timestamps, and hash bindings.
- `run_summary.json`: Original runner summary output for independent verification.
- `secret_scan.json`: Zero secret leakage verification.
