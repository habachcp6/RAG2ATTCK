# Evidence Report: Publication-Grade Research Report Scaffold (Phase S1)

**Task Handle:** Subagent C: Research Report & Related-Work Owner (Phase S1)  
**Assigned Worktree:** `D:/RAG2ATTCK-worktrees/report-s1`  
**Git Branch:** `codex/s1-report-related-work`  
**PRE_SHA:** `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315`  
**Audit Date:** 2026-10-02  
**Egress / Provider API Invariant:** Strictly **ZERO** live provider or API calls executed (`OFFLINE_GUARD: installed=True attempted_egress=0`).  
**Numerical Integrity Invariant:** Strictly **ZERO** invented numerical results; all pending experimental tables use formal schema placeholders (`[TBD_AT_EXECUTION]`).  

---

## 1. Environment & Commit Audit

- **PRE_SHA Verified:**
  ```bash
  git rev-parse HEAD
  # Output: 80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315
  ```
- **Branch Verified:** `codex/s1-report-related-work`
- **Clean Workspace Check:** Pre-execution working tree clean, tracking origin cleanly.

---

## 2. Research Materials Studied

The author conducted an exhaustive review and cross-verification of the following authoritative project artifacts:
1. **Canonical Context Documents (`docs/context/`):**
   - Research Plan v1.1 (`RAG_ATTCK_Research_Plan_Updated.docx`, SHA-256: `39499aa68188530eed81d1426af4d2f0217e17e10d9d016ddc0b38c0ae7a91af`).
   - Project Tracker (`RAG_ATTCK_Project_Tracker_Updated.xlsx`, SHA-256: `ed946fa1918af54a0634a317b6bf3d2b4291501219524de691c5da8b15725ef8`).
2. **Canonical Protocol & Benchmark Scope Configurations:**
   - Protocol Contract v1.1 (`config/experiment_protocol_v1.json`, Canonical Decisions Digest: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`, File SHA-256: `a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb`, Protocol Report: `reports/experiment_protocol_v1.md`).
   - Benchmark Scope (`config/benchmark_scope.json`, File SHA-256: `6bd769324f6ac9193d7df82e7f54f5a1397a41b9bc72be767da5a72b54b3a47c`).
3. **PR #8 and Task T33 Primary Evidence:**
   - Inspecting commit `6783f20971cbff91f105d0280ddd07cb0925aab0:reports/T33_related_work.md` and related notes in `docs/related_work/`.
   - Incorporating verified primary sources across all 8 core comparators: Yang & Hsu (2026), Adediran et al. (2026), CAM-LDS (Landauer et al., 2026), TechniqueRAG (Lekssays et al., 2025), H-TechniqueRAG (Morbiato et al., 2026), Trace2ATT&CK (Lupinacci et al., 2026), Okuma et al. (2023), and LADE (Gwak et al., 2026/2027).
   - Accurately reporting source access blockers: 6/8 full-text checked, Yang & Hsu (abstract/metadata only; Springer SIST paywall), Okuma et al. (IEEE bibliographic entry only; full text unavailable).
4. **Task T20 Retrieval Diagnostics and Failure Analysis Evidence:**
   - Reviewing `reports/T20_retrieval_failure_analysis.md` and `reports/T20_retrieval_diagnostics.md`.
   - Baseline empirical metrics across full benchmark (756 positive views: 718 TEST + 38 DEV): $Hit@1 = 4.23\%$, $Hit@3 = 16.80\%$, $Hit@5 = 24.21\%$, $Hit@10 = 45.11\%$, Macro Recall@10 = $43.14\%$.
   - Accurately defining the $54.89\%$ metric: in 415 of 756 positive views, no ground-truth technique was retrieved within Top-10 (the complement of view-level Any-GT Hit@10).
   - Evidence-based findings: severe lexical gap (`T1136.001` $0.0\%$ Hit@10), hard negative crowding (`certutil` LOLBin commands matching `T1218.012` Verclsid and crowding out tool transfer `T1105`), and contextual dilution (anchor-technique rank degraded in $22.0\%$ of eligible pairs vs. improved in only $7.8\%$).
5. **Frozen Infrastructure & Pilot Cost Reports:**
   - Model configuration freeze (`reports/T11_model_freeze.md`, `config/model.json`).
   - Prompt configuration freeze (`reports/T13_prompt_freeze.md`, `prompts/baseline_v1.txt`).
   - ATT&CK corpus and index freeze (`reports/T17_attack_corpus.md`, `reports/T18_retriever.md`, `reports/T19_rag_pipeline.md`).
   - DEV cost pilot audit (`reports/dev_cost_pilot_20261001.md`): 20 live DEV requests consumed 42,213 input / 13,139 output tokens for $\$0.0242$, validating the feasibility of the $\$19.99$ budget guard for the 6,400 planned TEST dispatches.
   - Forensic ground truth audit (`reports/final_repair_validation.md`): Unresolved cell discrepancies in historical Mendeley v3 data necessitating the synthetic dataset boundary.

---

## 3. Mandatory Reviewer Repairs Audit (10 Directives)

The following table documents the exact resolution of the 10 reviewer directives implemented in `docs/report/scientific_report.md`:

| # | Reviewer Directive | Resolution in `docs/report/scientific_report.md` | Verification |
|---|---|---|---|
| **1** | **RQ Numbering & Wording** | Restored canonical numbering throughout Abstract, Section 1.4, Section 6.2, and Section 6.3:<br>- **RQ1:** Retrieval-Augmented Attribution Efficacy.<br>- **RQ2:** Retrieval Quality & Failure Decomposition.<br>- **RQ3:** Retrieval Depth ($k \in \{1, 3, 5, 10\}$), API Cost, and Latency Trade-Offs. | Matches canonical project research questions. |
| **2** | **Dataset View Denominators** | Corrected all scorable denominators to the authoritative join of `split_manifest.json` $\to$ `views.jsonl` $\to$ `ground_truth.jsonl` over 1,280 TEST views:<br>- **718 Mapped Positives:** 278 Single-Event Views, 440 Contextual-Event Views ($278 + 440 = 718$). Comprises 678 single-GT views and 40 multi-GT views.<br>- **311 Ambiguous Views:** 261 Single, 50 Contextual (excluded per D2c).<br>- **251 Unmapped Views:** 101 Single, 150 Contextual (excluded per D2b).<br>Eliminated the erroneous 880 number. | Confirmed via authoritative python join script. |
| **3** | **Exact Asset Digests** | Computed and labelled exact hashes directly from actual bytes:<br>- `config/model.json`: `312c34cedd84106f2004c6070b72aeac1dd84209a464e2993fee3ec87822697f`<br>- `config/retrieval.json`: `b33a93913e7f6de36f6f9021f77b2c9dcb1d426929162acb250a3c73ac8e6e25`<br>- `prompts/baseline_v1.txt`: `b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206`<br>- Clearly distinguished Protocol Decisions Digest (`d3bf3d...`) from File SHA-256 (`a402b0...`). | Verified with `Get-FileHash`. |
| **4** | **Technique Names Audit** | Audited all technique references against pinned STIX v19.2:<br>- Clarified `T1059.009` as active Cloud API technique (not nonexistent, but cross-platform non-Windows).<br>- Corrected `T1218.012` to official name `Verclsid` (System Binary Proxy Execution: Verclsid).<br>- Verified `T1543.006` as a truly nonexistent technique ID (`NOT_IN_RAW`). | STIX v19.2 registry query confirmed. |
| **5** | **Licensing & Affiliation** | Removed fabricated Apache 2.0 assertions and invented author affiliations. Accurately stated: Root `README.md` declares MIT License, noting that no physical `LICENSE` file is committed in the execution checkout. | Matches repository checkout reality. |
| **6** | **Attribution & Upstream Claims** | Removed speculative phrases ("irreversible upstream source-corruption", "catastrophic"). Bounded limitation strictly to audit evidence: Task 2 forensic audit identified 15,713 unresolved cell discrepancies between scenario CSVs and the combined dataset (precision loss, `#NAME?` formula strings, divergent timestamps), which prevent independent verification of authoritative ground truth and mandate a formal stop at Task 2. | Bounded by audit evidence. |
| **7** | **Retrieval Metric Units** | Accurately preserved metric semantics: $54.89\%$ refers to the complement of view-level Any-GT Hit@10 across the full benchmark (415/756 positive views had zero GT techniques in Top-10), not a per-technique absence rate. Explicitly distinguished full benchmark T20 diagnostics (756 views) from canonical TEST-only results (718 views). | Mathematically and taxonomically exact. |
| **8** | **References & Citations** | Truthfully annotated all 8 core comparators with primary source URLs/DOIs and explicit verification status tags (`[FULL TEXT VERIFIED]`, `[PARTIAL / METADATA ONLY]`, `[ACCESS BLOCKED / BIBLIOGRAPHIC RECORD ONLY]`). Marked unknown parameters as `NOT REPORTED` (e.g. Adediran numeric k, TechniqueRAG Hit@k) and `NOT APPLICABLE` where appropriate. | Fully compliant with scholarly truthfulness. |
| **9** | **Runtime Disclosure** | Disclosed the canonical live launcher hash (`05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa`) and the 12-retry wrapper around `StudyBudgetLedger._write_atomically_unlocked` for Windows transient file locking errors (`WindowsError 5` and `WindowsError 32`). | Accurately reflects runtime harness. |
| **10** | **Tone & Phrasing** | Removed promotional adjectives ("frontier", "maximal internal reasoning", "zero label leakage", "exhaustive", "catastrophic", "uncompromising"). Accurately reported configured `reasoning_effort=xhigh`. | Rigorous academic tone throughout. |

---

## 4. Word Document (DOCX) Compilation Pipeline

Per Codex clarification, the markdown scaffold serves as preparation, and a complete materialization pipeline is established to export the publication report to Microsoft Word (`.docx`) format:
- **Compiler Utility:** `scripts/export_report_docx.py`
- **Engine:** `python-docx>=1.2.0` (installed via offline cache into Python 3.13 venv without mutating repo dependencies).
- **Styling & Layout Rules:**
  - Standard 1-inch margins on all sides.
  - Distinct typographic hierarchy (Georgia headings, Calibri body, Consolas code).
  - Native Word tables with dark navy header rows (`#092C4C`), alternating row shading (`#F8FAFC`), custom twip cell padding, and light gray interior borders (`#D0D7DE`).
  - Styled callout blockquotes with thick primary accent left border (`#0969DA`) and background shading (`#F6F8FA`).
  - Formatted inline markdown runs (bold, italic, inline code spans, hyperlinks).
- **Materialized Artifact:** `docs/report/scientific_report.docx` (69,271 bytes, SHA-256: `f33463a362e90a7b2e13bba8437ea4d3a276d1931eb4407ef8105946172fe924`).
- **Turnkey Post-Run Compilation:** Once full matrix execution completes and table placeholders are replaced with verified numbers, running `uv run python scripts/export_report_docx.py` immediately compiles the finalized editable Word deliverable.

---

## 5. Cryptographic Integrity and Verification

### 5.1 Created Artifact Checksums
| File Path | File Size | SHA-256 Checksum | Purpose |
| :--- | :---: | :--- | :--- |
| `docs/report/scientific_report.md` | 69,549 bytes | `014259cd27828bb2b1ba285c0c68ecd4c29397b6d7a2f118611163ebce33b1f9` | Repaired research report markdown scaffold |
| `docs/report/scientific_report.docx` | 75,802 bytes | `4e74a4e680fe65e1d822f49312fc936d3b08cb8f473b6cee62dc53499b046659` | Compiled editable Microsoft Word publication report |
| `scripts/export_report_docx.py` | 32,532 bytes | `6c94a9a499ba22639c322419089dc6349fdfcc2ce46cd4da4b7346427cad373f` | DOCX export tool with LaTeX-to-Unicode converter and layout controls |
| `scripts/verify_report_metadata.py` | 11,144 bytes | `df62d937a775425cf1b1504ba0a5db70c31ab3ded00688f0c3600619154313ce` | Automated verifier for report hashes, evaluator invariants, and DOCX QA |
| `reports/evidence/research_report_scaffold.md` | ~20 KB | Tracked in Git (CD_FACTUAL_R2) | Phase S1 evidence document |

### 5.2 Minor Metadata Refinements (PR #25 Follow-Up)
1. **Reference 7 (Yang & Hsu):** Springer primary page explicitly confirms online publication date is **2 July 2026** (pp. 235–251, SIST vol. 8767, SITAIBA 2025). `[PARTIAL / METADATA ONLY]` status retained as full chapter is subscription paywalled.
2. **Reference 6 (H-TechniqueRAG, Morbiato et al.):** The arXiv primary page displays submission date as **24 March 2026** (despite the `2604` identifier prefix). Recorded "submitted 24 March 2026" explicitly.

### 5.3 Test Regression Verification
Full offline test regression executed via `scripts/run_offline_tests.py`:
- Collected: 1,266 items (1,261 selected, 5 deselected).
- Passed: 1,260 passed, 1 skipped, 0 failed.
- Guard Verification: `OFFLINE_GUARD: installed=True attempted_egress=0`.

### 5.4 Codex Reviewer Directive: CD_RENDER_REPAIR Execution & Validation
Following the Codex Reviewer audit of the compiled Word document, four layout and rendering defects were identified and resolved:
1. **Academic Header & Non-Novelty Tone (Page 1):** Removed all self-proclaimed badge phrases. Replaced the document header with standard academic metadata: Title, Author (Hà Hoàng Bách), Affiliation (RAG2ATT&CK Project), Date (October 2026), and Status (`DRAFT — IN PROGRESS / PENDING EXPERIMENTAL EXECUTION`).
2. **RQ1 Table Width & Margin Compliance (Page 6):** Split Table 2 into Table 2a and Table 2b with explicit widths $\le 6.50$ inches.
3. **Raw TeX Leakage Elimination (Page 17, Section 5.3):** Built a dedicated `latex_to_unicode()` converter in `scripts/export_report_docx.py`.
4. **Table Pagination & Row Splitting (Page 19):** Injected `<w:tblHeader/>` and `<w:cantSplit/>` into all tables.

### 5.5 Codex Reviewer Directive: CD_FACTUAL_R2 Execution & Validation
Following the second Codex Reviewer audit (`FAIL | CD_FACTUAL_R2`), eight factual, methodological, and rendering defects were systematically resolved:
1. **Hash Alignment (`config/benchmark_scope.json`):** Corrected the hash in Section 3.2 (line 120) and Table 6 (line 497) to the true file SHA-256 `d6aa89831dec75362b4fd48de0fd6e7082290f2be0cb7bd0afc6bc518148db8b` (previously confused with corpus manifest `6bd769...`). Created `scripts/verify_report_metadata.py` which cryptographically validates all 12 assets cited in Table 6 against actual bytes on disk.
2. **Evaluator Invariants & Zero-Denominator Boundary Proofs (Section 5.3):**
   - Formally clarified the distinction between per-technique diagnostic exports (`compute_technique_metrics`) and condition-level scalar aggregation (`compute_condition_metrics`).
   - Detailed the three zero-denominator cases under Protocol Decision D2j (`d2j_zero_denominator == "NULL"`):
     - *Case A (Unobserved Class: $\text{support}=0 \land \text{pred}=0$):* `precision=None, recall=None, f1=None` (JSON `null`).
     - *Case B (Unpredicted Class: $\text{support}>0 \land \text{pred}=0$):* `precision=None, recall=0.0, f1=0.0`.
     - *Case C (Unobserved False Positive: $\text{support}=0 \land \text{pred}>0$):* `precision=0.0, recall=None, f1=0.0`.
   - Demonstrated that all three cases contribute exactly $0.0$ to the condition $\text{Macro-F1}$ numerator sum divided by 474. Added automated known-answer unit tests in `scripts/verify_report_metadata.py`.
3. **Table 2b Schema Alignment:** Removed unexported `474-Class Macro Precision` and `474-Class Macro Recall`. Replaced with true condition evaluator outputs: `Condition | Scorable Views (N) | Completed Outputs | Parse Failures | Invalid ATT&CK IDs | Invalid ID Rate (%)`.
4. **References Numbering & List Bleed Elimination:** Eliminated Word's continuous `List Number` counter bleeding (which caused references to number 41..53). Implemented static numbering `[1]`..`[13]` with hanging indent in `export_report_docx.py`. Added strict assertions to `audit_docx_quality` and `verify_report_metadata.py`.
5. **Token Budget Precision (`max_output_tokens=8192`):** Corrected the description in Section 4.2 to document that `max_output_tokens` represents an upper budget bound governing both reasoning and completion tokens, rather than an absolute guarantee against truncation: if exhausted, the API emits `status="incomplete"` with `incomplete_details.reason="max_output_tokens"`.
6. **References 2 & 3 Primary Source Grounding:**
   - Reference 2 updated to: `OpenAI. "GPT-5.6 Luna Model." OpenAI Documentation, accessed 2 October 2026. Available: <https://developers.openai.com/api/docs/models/gpt-5.6-luna>. Specifications: 1,050,000 context window, 128,000 max output capacity. [PRIMARY SOURCE VERIFIED]`. Removed fabricated July 2026 date.
   - Reference 3 updated to: `OpenAI. "Reasoning models." OpenAI Documentation Guides, accessed 2 October 2026. Available: <https://developers.openai.com/api/docs/guides/reasoning>. Note: Details upper budget bounds and incomplete responses (status="incomplete", incomplete_details.reason="max_output_tokens") when max_output_tokens is exhausted. [PRIMARY SOURCE VERIFIED]`.
7. **Table 1 Split (Table 1a & Table 1b):** Split the 10-column Table 1 into Table 1a (Comparators 1–4, 5 columns, total width 6.50 in) and Table 1b (Comparators 5–8 + RAG2ATTCK, 6 columns, total width 6.50 in), completely eliminating column header squeezing in portrait mode.
8. **Word Title & Text Formatting:** Purged Word's default blue border `<w:pBdr>` from Title style and set title text color to pure black `RGBColor(0, 0, 0)`. Updated Affiliation to `RAG2ATT&CK Project`. Unescaped all 24 raw `\%` occurrences in markdown and exporter to standard `%`.

---

## 6. Compliance Statement
Subagent C certifies that:
1. The research report is authored in English with a rigorous, clear synthetic scope: the benchmark is `synthetic-paired-v1` (1,280 views $\times$ 5 conditions), NOT real-world telemetry. Generalization to enterprise telemetry remains unsupported.
2. All 10 mandatory reviewer directives, CD_RENDER_REPAIR, and all 8 CD_FACTUAL_R2 requirements are fully resolved and audited.
3. PR #8 and T33 primary evidence was integrated without exaggeration, and source-access blockers were faithfully disclosed.
4. Strictly zero invented numerical results were produced; all experimental outcome tables are formatted as formal schemas with explicit placeholders (`[TBD_AT_EXECUTION]`).
5. The Markdown scaffold is verified and immediately convertible to a usable, editable DOCX report via `scripts/export_report_docx.py`.
6. Automated verifier `scripts/verify_report_metadata.py` passes 100% of cryptographic, mathematical, and formatting checks.
7. Strictly zero live provider or API calls were initiated (`OFFLINE_GUARD: attempted_egress=0`).
