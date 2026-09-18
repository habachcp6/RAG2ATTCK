# T16: MITRE ATT&CK Enterprise v19.2 Release Pinning & Benchmark Scope Report

## Executive Summary
This report documents the formal validation and formalization of the **MITRE ATT&CK Enterprise v19.2** release pinning and benchmark scope for the **RAG2ATTCK** research project (Task **T16**).

All verification gates have PASSED:
- **Immutable Release Pinning**: Pinned to immutable commit SHA `6cda5ad8462c79e14fbb872f4e09059b18e0cfc4` in repository `mitre-attack/attack-stix-data`. No mutable branch references (`master` / `main`).
- **Cryptographic Integrity**: SHA-256 verified as `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4` over exact file size 53,835,637 bytes.
- **Full Catalog Accounting**: Verified 858 total techniques/subtechniques (697 active, 149 revoked, 12 deprecated).
- **Windows Subcorpus**: 474 active Windows techniques/subtechniques (176 root techniques, 298 subtechniques).
- **Benchmark Scope Formalization**: Created `config/benchmark_scope.json` defining the 8 benchmark classes with automated git provenance verified against commit `93d564b5dbc0415e64ed85d014ae0b5c6e41f7f8`.
- **8/8 Benchmark Technique Coverage**: All 8 benchmark techniques exist in ATT&CK Enterprise v19.2, support the Windows platform, are active (`revoked=False`, `deprecated=False`), and pass post-hoc ID validation.
- **Architectural Alignment**: Confirmed `load_attack_registry()` in `src/llm/schemas.py` invokes `parse_attack_bundle()` from `src/attack_loader.py`, guaranteeing zero divergence between corpus parsing and LLM prediction validation.

---

## 1. Pinned Release Constants & Integrity Verification

The MITRE ATT&CK Enterprise dataset is pinned in `src/attack_loader.py` and recorded in `data/metadata/attack_manifest.json`:

| Parameter | Specification | Verification Result |
| :--- | :--- | :--- |
| **ATT&CK Version** | `19.2` | Matches |
| **Upstream Repository** | `https://github.com/mitre-attack/attack-stix-data` | Verified immutable |
| **Pinned Commit SHA** | `6cda5ad8462c79e14fbb872f4e09059b18e0cfc4` | Full 40-char SHA |
| **Download URL** | `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/6cda5ad8462c79e14fbb872f4e09059b18e0cfc4/enterprise-attack/enterprise-attack-19.2.json` | Pinned to commit hash |
| **Local File Path** | `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` | Exists on disk |
| **Expected Size** | `53,835,637` bytes | Byte-for-byte exact match |
| **Expected SHA-256** | `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4` | Exact match |

---

## 2. STIX Bundle Extraction Accounting

Parsing `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` using `parse_attack_bundle()` yields the following verified census:

| Category | Count | Notes |
| :--- | :--- | :--- |
| **Total Techniques & Subtechniques** | `858` | All STIX `attack-pattern` objects with `mitre-attack` IDs |
| **Revoked Techniques** | `149` | Marked with `revoked: true` or `revoked-by` relationship |
| **Deprecated Techniques** | `12` | Marked with `x_mitre_deprecated: true` |
| **Active Techniques** | `697` | Not revoked and not deprecated |
| **Active Windows Techniques** | `474` | Active techniques listing `"Windows"` in `x_mitre_platforms` |
| **Active Windows Root Techniques** | `176` | Root techniques (`is_subtechnique: false`) |
| **Active Windows Subtechniques** | `298` | Subtechniques (`is_subtechnique: true`) |

This accounting matches `data/metadata/attack_manifest.json` exactly and establishes the universe of 474 Windows techniques for the T17 retrieval corpus.

---

## 3. Benchmark Scope Formalization (`config/benchmark_scope.json`)

To preserve branch isolation and avoid modifying locked baseline files or performing merges/cherry-picks from `main`, the 8 benchmark classes are formalized in `config/benchmark_scope.json`:

```json
{
  "schema_version": "1.0.0",
  "source_main_commit": "93d564b5dbc0415e64ed85d014ae0b5c6e41f7f8",
  "attack_version": "19.2",
  "attack_catalog": [
    "T1059.001",
    "T1059.003",
    "T1053.005",
    "T1543.003",
    "T1136.001",
    "T1547.001",
    "T1685.005",
    "T1105"
  ]
}
```

### Automated Provenance Check
The automated test `test_benchmark_scope_provenance` runs:
```bash
git show 93d564b5dbc0415e64ed85d014ae0b5c6e41f7f8:config/data_ground_truth.json
```
and mechanically asserts that `config/benchmark_scope.json`'s `attack_catalog` is identical to `synthetic_benchmark.attack_catalog` from commit `93d564b5`. This guarantees unbroken scientific lineage from the Stage A benchmark design decision without modifying `config/data_ground_truth.json` on `baseline-infra`.

---

## 4. 8/8 Benchmark Technique Verification Details

All 8 benchmark classes were verified against the Enterprise ATT&CK v19.2 STIX extraction:

| Technique ID | Name | Category | Platforms | Active | In v19.2 STIX | Windows Set (474) | Post-Hoc Valid |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `T1059.001` | PowerShell | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1059.003` | Windows Command Shell | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1053.005` | Scheduled Task | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1543.003` | Windows Service | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1136.001` | Local Account | Sub-technique | Containers, ESXi, Linux, macOS, Network Devices, Windows | True | Yes | Yes | Valid |
| `T1547.001` | Registry Run Keys / Startup Folder | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1685.005` | Clear Windows Event Logs | Sub-technique | Windows | True | Yes | Yes | Valid |
| `T1105` | Ingress Tool Transfer | Root technique | ESXi, Linux, macOS, Network Devices, Windows | True | Yes | Yes | Valid |

### Focus Verification: `T1685.005`
`T1685.005` ("Clear Windows Event Logs") is confirmed to be a valid, active sub-technique of `T1685` ("Disable or Modify Tools") introduced into Enterprise ATT&CK on 2026-04-14. It has `revoked=False`, `deprecated=False`, supports Windows, and is fully recognized by `load_attack_registry()` and `validate_technique_id()`.

---

## 5. Architectural Alignment: STIX Parser and Post-Hoc Validator

Verification confirmed that:
1. `src/llm/schemas.py` (`load_attack_registry`) imports and calls `parse_attack_bundle()` from `src/attack_loader.py`.
2. Both components resolve to the exact same file path: `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json`.
3. The set of technique keys extracted by `parse_attack_bundle()` is identical to `load_attack_registry()` (`assert parsed_keys == registry_keys`).
4. Therefore, the post-hoc validator operates on the exact same universe of ATT&CK concepts as the RAG corpus generator.

---

## 6. Verification Results

All tests in `tests/test_attack_loader.py` passed:
- `test_attack_immutable_pinning`: PASSED
- `test_corrupted_attack_rejection`: PASSED
- `test_production_attack_manifest`: PASSED
- `test_stix_bundle_parsing`: PASSED
- `test_benchmark_scope_provenance`: PASSED
- `test_benchmark_scope_techniques_coverage_and_attributes`: PASSED
- `test_post_hoc_validator_schema_alignment`: PASSED

**Conclusion**: Task T16 is complete and all invariants for ATT&CK v19.2 release pinning and benchmark scope are formally satisfied.
