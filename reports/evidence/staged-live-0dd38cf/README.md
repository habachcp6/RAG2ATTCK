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
- **Human Authorization Reference**: `733a85128d052109` (SHA-256 prefix)

## Verification Verdict
```text
STAGED_EVIDENCE_VERIFICATION: PASS
manifest_valid: true
run_id_consistent: true
records: 7
provider_attempts: 7
duplicate_requests: 0
resume_new_records: 2
record_sha_mismatches: 0
journal_sequence_errors: 0
secret_leaks: 0
```

## Summary of Staged Requests
1. **Initial Staged Run (`--stop-after 5`)**:
   - `view_00477e30` / `no_rag` (ordinal 1, response: `resp_0fe1ea0907c98ee8006abd3c2902dc87d08ee9b785c8d32473`)
   - `view_00477e30` / `rag_k1` (ordinal 2, response: `resp_056d900f4ed953a2006abd3c2c2c4887d0a473885d8efa4e40`)
   - `view_00477e30` / `rag_k3` (ordinal 3, response: `resp_07d4b46c6bf977e2006abd3c2ea85487d00fca6834d858349d`)
   - `view_00477e30` / `rag_k5` (ordinal 4, response: `resp_021e1a49fbf7a94a006abd3c30ea9c87d000c01a2f64f33668`)
   - `view_00477e30` / `rag_k10` (ordinal 5, response: `resp_07bfa77b0d2da285006abd3c332fc087d0a89781cf4da3a970`)
2. **Resume Test (`--stop-after 2`)**:
   - Prior 5 records preserved without re-execution (`duplicate_requests: 0`).
   - `view_00540be5` / `no_rag` (ordinal 6, response: `resp_0835f8f533a39e80006abd3d68407487d03f024765d1430489`)
   - `view_00540be5` / `rag_k1` (ordinal 7, response: `resp_0cb81255e2e83120006abd3d6a6d6887d00df7fe05ec865620`)

## Files in Package
- `staged_live_audit.json`: High-level summary and verification metrics.
- `staged_live_file_hashes.json`: SHA-256 hashes and sizes of all runtime experiment artifacts.
- `journal_audit.json`: Detailed validation of request journal sequence, transitions, ordinals, and completions.
- `records_audit.json`: Detailed record-level metadata, latency, timestamps, and hash bindings.
- `secret_scan.json`: Zero secret leakage verification.
