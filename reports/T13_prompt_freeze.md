# T13: Base Prompt Freeze Report — No-RAG Baseline Infrastructure

## Executive Summary
This report documents the formal prompt freeze completed under Task **T13** of the **RAG2ATTCK** research project. It establishes the canonical base prompt template stored at `prompts/baseline_v1.txt`. 

This prompt is frozen for the duration of the baseline evaluation and is specifically designed to be shared verbatim between the **No-RAG Baseline** condition and the future **ATT&CK-Grounded RAG** condition, ensuring strict experimental symmetry.

---

## 1. Prompt Objective
The primary objective of the base prompt is to instruct the frontier model (`gpt-5.6-luna`) to act as an expert threat intelligence and SOC analyst performing technique attribution on Windows endpoint telemetry.

The prompt directs the model to:
1. Parse and analyze sanitized behavioral telemetry (process execution, command-line arguments, parent-child relationships, file system modifications, Windows registry changes, and network activity).
2. Correlate the observed behaviors against the MITRE ATT&CK Enterprise matrix.
3. Select the single most specific and accurate MITRE ATT&CK Technique or Sub-technique ID that characterizes the primary malicious activity.

---

## 2. Output Contract
The model's output is governed by a strict, non-conversational contract:
- **Format:** A single, bare JSON object adhering to the schema:
  ```json
  {"technique_id": "<ATT&CK_ID>"}
  ```
  Where `<ATT&CK_ID>` is formatted either as a technique (`T####`) or sub-technique (`T####.###`).
- **Zero Extraneous Text:** The prompt explicitly forbids:
  - Markdown code fences (e.g., ````json ... ````).
  - Chain-of-thought or reasoning narratives in the visible payload (reasoning occurs entirely inside the model's internal thinking window via `reasoning_effort="xhigh"`).
  - Analytical justifications, confidence scores, or alternative candidate rankings.
  - Conversational pleasantries, introductory framing, or sign-offs.

This output contract enables deterministic JSON deserialization and feeds directly into the post-hoc validation pipeline (syntax verification followed by Enterprise ATT&CK v19.2 registry membership check).

---

## 3. No-RAG / RAG Matching Policy
A central requirement of the RAG2ATTCK experimental design is that **the prompt template must be identical in both No-RAG and RAG conditions**. 

### Symmetry Architecture
| Dimension | No-RAG Baseline Condition | ATT&CK-Grounded RAG Condition |
| :--- | :--- | :--- |
| **Prompt Template** | `prompts/baseline_v1.txt` | `prompts/baseline_v1.txt` (Identical) |
| **Task Instructions** | Identical wording | Identical wording |
| **Output Contract** | `{"technique_id": "..."}` | `{"technique_id": "..."}` |
| **Endpoint Evidence** | Populated via `{ENDPOINT_EVIDENCE}` | Populated via `{ENDPOINT_EVIDENCE}` (Identical) |
| **Reference Context** | `{RETRIEVED_CONTEXT}` replaced by `""` (empty string) | `{RETRIEVED_CONTEXT}` replaced by retrieved ATT&CK reference text |

Under this design, the experimental intervention is strictly isolated to the data injected into `{RETRIEVED_CONTEXT}`. No changes to wording, persona, task framing, or formatting rules occur between conditions.

---

## 4. Shared Generic Instruction for Context Handling
To achieve complete prompt symmetry without requiring prompt branching or conditional instructions, `baseline_v1.txt` incorporates the following universal context clause:

> *"If reference context is provided below, use it as supporting information for the attribution. If no reference context is provided, perform the attribution using the endpoint evidence alone."*

### Why This Preserves Symmetric Reasoning
1. **Neutrality:** The instruction does not tell the model that reference context is superior to internal parametric memory, nor does it mandate blind adherence to retrieved chunks.
2. **Graceful Handling of Null Context:** In the No-RAG baseline, `{RETRIEVED_CONTEXT}` evaluates to an empty string. The model encounters the instruction, recognizes that no reference context follows, and seamlessly relies on its internal knowledge base to evaluate the endpoint evidence.
3. **Absence of Asymmetric Guidance:** The prompt does not grant the RAG condition specialized analytical heuristics, chain-of-thought protocols, or task exemptions that the No-RAG baseline lacks.

---

## 5. Prohibited Fields and Leakage Prevention
To ensure the attribution task reflects genuine analytical reasoning rather than trivial metadata extraction, the prompt and input payloads strictly exclude all answer-bearing, detector-derived, or annotation metadata.

The following fields and patterns are **strictly prohibited** from ever entering the prompt or evidence payloads:
1. **`rule.mitre.*` Fields:** Any detector or Wazuh rule mappings referencing MITRE techniques, tactics, or sub-techniques.
2. **Detector Descriptions:** Rule titles, alert names, or detection descriptions (e.g., "Wazuh Rule 100201: Mimikatz LSASS Dump Detected").
3. **Ground-Truth Labels:** Canonical technique IDs (`T####`), tactic names, or class labels from the source dataset.
4. **Scenario & Annotation Metadata:** Scenario names (e.g., `APT29_Day1`), campaign identifiers, execution scripts, run numbers, step numbers, or evaluator notes.
5. **Simulated Victim Hostnames / Labels Indicating Attack Step:** Any synthetic labels or annotations indicating malicious execution sequence boundaries.

The sanitizer pipeline guarantees that `{ENDPOINT_EVIDENCE}` contains exclusively sanitized, behavioral endpoint telemetry (Sysmon event fields, timestamps, process names, command lines, hashes, network connections, and registry keys).

---

## 6. Allowed Future RAG Context Insertion Point
The prompt reserves exactly one designated insertion point for external retrieval:

```text
---
REFERENCE CONTEXT:
{RETRIEVED_CONTEXT}
---
```

- In **No-RAG Baseline:** `{RETRIEVED_CONTEXT}` is formatted as an empty string (`""`). The section header remains benign and unpopulated.
- In **RAG Experiments:** The retrieval engine injects retrieved text chunks (e.g., ATT&CK Technique descriptions, detection guidance, and sub-technique procedures from Enterprise ATT&CK v19.2) directly into this block.

No other portion of the prompt may be modified or augmented by the retrieval system.

---

## 7. Version Freeze Rule
1. **Immutability:** Once Task T13 is declared complete and committed, `prompts/baseline_v1.txt` is permanently frozen.
2. **Zero In-Flight Modifications:** Under no circumstances may `baseline_v1.txt` be altered during smoke testing, baseline evaluation, or comparative analysis.
3. **Versioning Protocol:** If prompt refinement, task re-framing, or schema evolution is mandated by future research phases, it must be introduced as a new, distinct artifact (e.g., `prompts/baseline_v2.txt`), accompanied by an updated freeze report (`reports/T13_prompt_v2_freeze.md`) and explicit ablation justification.
