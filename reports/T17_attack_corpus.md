# Task T17: Deterministic Windows ATT&CK Retrieval Corpus Report

## Executive Summary
- **Task ID**: T17
- **Branch**: `task/t17-attack-corpus` (parent: `task/t16-attack-pin` at commit `97c56dc`)
- **Status**: COMPLETE / PASS
- **Target Deliverables**:
  1. Corpus generator module: `src/retrieval/corpus_builder.py` (and package `src/retrieval/__init__.py`)
  2. Corpus artifact: `attack/corpus/enterprise-windows-v19.2.jsonl` (474 lines, 1,548,724 bytes, SHA-256: `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75`)
  3. Companion manifest: `attack/corpus/enterprise-windows-v19.2.manifest.json` (900 bytes, SHA-256: `6bd769324f6ac9193d7df82e7f54f5a1397a41b9bc72be767da5a72b54b3a47c`)
  4. Test suite: `tests/test_attack_corpus.py` (9 comprehensive unit and integration tests, 100% pass)
  5. Documentation report: `reports/T17_attack_corpus.md`
- **Integrity Highlights**:
  - 100% byte-for-byte reproducibility across builds and environments.
  - Zero evaluation metadata / labels (`ground_truth`, `technique_label`, `expected_technique`, `attack_label`, etc.) present in corpus documents.
  - Complete 8/8 benchmark technique coverage.
  - Strictly LF (`\n`) line endings, UTF-8 encoding, and deterministic `sort_keys=True` JSON formatting.
  - Existing baseline production files (`src/attack_loader.py`, etc.) completely untouched.

---

## 1. 11-Field Document Schema

Each line in `attack/corpus/enterprise-windows-v19.2.jsonl` is an independent, valid UTF-8 JSON object adhering to the following schema:

| Field Name | Type | Description | Invariant / Validation Rule |
| :--- | :--- | :--- | :--- |
| `technique_id` | `string` | Canonical MITRE ATT&CK technique identifier | Pattern: `^T\d{4}(\.\d{3})?$` (e.g., `T1059.001`) |
| `stix_id` | `string` | Canonical STIX 2.1 UUID for the attack-pattern | Pattern: `^attack-pattern--[0-9a-f-]+$` |
| `name` | `string` | Official name of technique or subtechnique | Non-empty string |
| `description` | `string` | Official ATT&CK markdown description | Multi-paragraph text, normalized `\n` line endings |
| `platforms` | `list[string]` | Supported execution platforms | Alphabetically sorted; must include `"Windows"` |
| `tactics` | `list[string]` | Associated kill-chain phases | Alphabetically sorted list of tactics (e.g., `["execution"]`) |
| `is_subtechnique` | `boolean` | Flag indicating whether this is a subtechnique | `true` if subtechnique, `false` if root technique |
| `parent_technique_id` | `string \| null` | Technique ID of parent root technique | `^T\d{4}$` if `is_subtechnique=true`; `null` if root |
| `modified` | `string` | ISO 8601 UTC timestamp of last STIX modification | Formatted timestamp string from STIX bundle |
| `source_version` | `string` | Pinned ATT&CK release version | Constant `"19.2"` |
| `retrieval_text` | `string` | Deterministic structured text formatted for embedding | Composed via `compose_retrieval_text()` |

### Schema Enforcement & Serialization
In `src/retrieval/corpus_builder.py`, `CorpusDocument.to_json_line()` guarantees:
- Dictionary keys are sorted alphabetically (`sort_keys=True`).
- Non-ASCII characters are preserved directly in UTF-8 (`ensure_ascii=False`).
- Prohibited evaluation metadata keys are rejected with `ValueError`.

---

## 2. Deterministic `retrieval_text` Composition Template

The embedding text for each technique is composed deterministically from official STIX attributes without any LLM intervention or summarization:

```python
def compose_retrieval_text(
    technique_id: str,
    name: str,
    tactics: List[str],
    platforms: List[str],
    description: str,
    parent_technique_id: Optional[str] = None,
) -> str:
    tactics_str = ", ".join(sorted(tactics))
    platforms_str = ", ".join(sorted(platforms))
    clean_description = description.replace("\r\n", "\n").replace("\r", "\n").strip()

    lines = [
        f"Technique ID: {technique_id}",
        f"Name: {name}",
        f"Tactics: {tactics_str}",
        f"Platforms: {platforms_str}",
    ]
    if parent_technique_id:
        lines.append(f"Parent Technique: {parent_technique_id}")
    lines.append(f"Description:\n{clean_description}")

    return "\n".join(lines)
```

### Template Design Rationale
1. **Identifier Anchoring**: `Technique ID` and `Name` on the first two lines provide immediate lexical and semantic hooks for dense embeddings.
2. **Taxonomic Context**: `Tactics` and `Platforms` (alphabetically sorted) contextualize adversary goals and target environment constraints.
3. **Hierarchy Preservation**: When `parent_technique_id` is present, it explicitly bridges subtechniques to their root technique family.
4. **Complete Adversary Procedures**: The full official `Description` supplies specific threat actor procedures, API calls, and behaviors necessary for semantic matching against endpoint logs.

---

## 3. Census Accounting: From Raw STIX v19.2 to Active Windows Corpus

| Stage | Filter / Operation | Object Count | Delta |
| :--- | :--- | :--- | :--- |
| **Raw STIX Objects** | Enterprise ATT&CK v19.2 (`enterprise-attack-19.2.json`) | 858 `attack-pattern` | - |
| **Active Filtering** | Exclude revoked (`revoked == true`) and deprecated (`x_mitre_deprecated == true`) | 697 active | -161 (33 revoked, 128 deprecated) |
| **Platform Filtering** | Retain only active techniques where `"Windows" in platforms` | **474 active Windows** | -223 (non-Windows active) |
| **Hierarchical Breakdown** | Root techniques (`is_subtechnique == false`) | **176** | 37.1% of Windows corpus |
| **Hierarchical Breakdown** | Subtechniques (`is_subtechnique == true`) | **298** | 62.9% of Windows corpus |

### Graph Invariants
- **Closed Parent Subgraph**: All 298 subtechniques reference a parent technique that is present inside the 474 active Windows corpus. There are 0 orphan subtechniques and 0 cross-platform missing parents.
- **Unique Technique IDs**: Every one of the 474 documents has a unique `technique_id`.
- **1-to-1 STIX Mapping**: Every `technique_id` maps bijectively to exactly one STIX `id`.

---

## 4. Benchmark Scope Coverage Table

All 8 techniques defined in `config/benchmark_scope.json` are verified present in the retrieval corpus:

| Technique ID | Name | Hierarchy | Tactics | Platforms | In Corpus? |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `T1059.001` | PowerShell | Subtechnique (`T1059`) | Execution | Windows | YES |
| `T1059.003` | Windows Command Shell | Subtechnique (`T1059`) | Execution | Windows | YES |
| `T1053.005` | Scheduled Task | Subtechnique (`T1053`) | Execution, Persistence, Privilege Escalation | Windows | YES |
| `T1543.003` | Windows Service | Subtechnique (`T1543`) | Persistence, Privilege Escalation | Windows | YES |
| `T1136.001` | Local Account | Subtechnique (`T1136`) | Persistence | Windows | YES |
| `T1547.001` | Registry Run Keys / Startup Folder | Subtechnique (`T1547`) | Persistence, Privilege Escalation | Windows | YES |
| `T1685.005` | Dynamic-link Library (DLL) | Subtechnique (`T1685`) | Execution | Windows | YES |
| `T1105` | Ingress Tool Transfer | Root technique | Command and Control | AIX, ESXi, Linux, macOS, Network, Windows | YES |

- **Coverage Status**: 8/8 (100.0%)
- **Missing Benchmark Techniques**: None (`[]`)

---

## 5. Determinism & Cryptographic Provenance

To eliminate non-determinism across platforms (Windows vs Linux vs macOS) and repeat runs:
1. **Strict LF Line Endings**: All corpus JSONL lines and manifest JSON files are written with `newline="\n"`. Zero carriage returns (`\r`) exist anywhere in the corpus file.
2. **ASCII Order Sorting**: The 474 techniques are sorted strictly ascending by `technique_id`.
3. **Internal Key & List Sorting**: JSON keys are sorted (`sort_keys=True`), tactics are sorted (`sorted(tactics)`), and platforms are sorted (`sorted(platforms)`).
4. **Pure Functional Manifest**: The manifest contains only static, verifiable attributes of the dataset and source STIX release. Dynamic timestamps (`datetime.now()`) are omitted, ensuring identical SHA-256 hashes across independent builds.

### Cross-Directory Verification
Test `test_corpus_builder_determinism_across_directories` builds the corpus in two separate temporary directories and verifies:
- `raw_bytes_a == raw_bytes_b` (identical byte stream)
- `sha256_a == sha256_b == b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75`

---

## 6. Zero Evaluation Metadata Invariants

To guarantee scientific integrity and prevent data leakage into downstream retrieval (T18) or LLM prompts (T19):
- The prohibited key set is strictly enforced:
  `{"ground_truth", "technique_label", "expected_technique", "attack_label", "label", "gt", "target", "y_true", "y_pred"}`
- `CorpusDocument.to_json_line()` actively scans each record and raises `ValueError` if any prohibited key is detected.
- `tests/test_attack_corpus.py::test_corpus_zero_evaluation_metadata` verifies zero prohibited keys across all 474 records.

---

## 7. Full Manifest Contents

`attack/corpus/enterprise-windows-v19.2.manifest.json`:
```json
{
  "attack_version": "19.2",
  "benchmark_coverage": {
    "coverage_status": "8/8",
    "covered_benchmark_techniques": 8,
    "missing_benchmark_techniques": [],
    "techniques": [
      "T1059.001",
      "T1059.003",
      "T1053.005",
      "T1543.003",
      "T1136.001",
      "T1547.001",
      "T1685.005",
      "T1105"
    ],
    "total_benchmark_techniques": 8
  },
  "corpus_file": "attack/corpus/enterprise-windows-v19.2.jsonl",
  "corpus_sha256": "b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75",
  "corpus_size_bytes": 1548724,
  "document_count": 474,
  "generation_command": "python -m src.retrieval.corpus_builder",
  "root_technique_count": 176,
  "schema_version": "1.0.0",
  "source_commit": "6cda5ad8462c79e14fbb872f4e09059b18e0cfc4",
  "source_stix_sha256": "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4",
  "subtechnique_count": 298
}
```

---

## 8. Test Execution Summary

### Unit & Integration Suite (`tests/test_attack_corpus.py`)
| Test Function | Status | Coverage Focus |
| :--- | :--- | :--- |
| `test_corpus_file_exists_and_accounting` | PASS | File existence, 1,548,724 bytes, 474 lines, SHA-256 verification |
| `test_corpus_schema_and_required_fields` | PASS | 11-field schema, non-null values, ID formatting, sorted lists |
| `test_corpus_zero_evaluation_metadata` | PASS | Zero prohibited label keys in corpus + tamper error raising |
| `test_corpus_strict_technique_id_sorting` | PASS | Uniqueness and strict ascending lexical sort order |
| `test_corpus_active_windows_attributes` | PASS | STIX cross-check: 0 revoked, 0 deprecated, 176 root, 298 subtechniques |
| `test_benchmark_techniques_coverage` | PASS | 8/8 benchmark scope techniques confirmed present with correct hierarchy |
| `test_corpus_builder_determinism_across_directories` | PASS | Cross-directory rebuild produces identical byte stream & SHA-256 |
| `test_corpus_manifest_integrity` | PASS | Manifest schema, metrics, and SHA-256 consistency with corpus file |
| `test_retrieval_text_formatting_and_lf_endings` | PASS | Zero `\r` (CRLF) characters, exact header & hierarchy formatting |

### Full Test Suite Regression
- Total Tests: 207 (198 baseline + 9 corpus tests)
- Failed: 0
- Skipped / Deselected: 0
- Pass Rate: 100%
