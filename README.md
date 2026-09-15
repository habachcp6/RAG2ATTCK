# RAG2ATT&CK

**Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs**

*Tiêu đề tiếng Việt:* **Đánh giá tác động của Retrieval-Augmented Generation dựa trên MITRE ATT&CK đối với việc ánh xạ Windows Endpoint Logs sang ATT&CK Techniques**

[![Status: Research design / early development](https://img.shields.io/badge/Status-Research%20design%20%2F%20early%20development-blue.svg)](#project-status)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](#license)

---

## Abstract & Motivation

RAG2ATT&CK is a research prototype designed to investigate whether grounding Large Language Models (LLMs) with external knowledge from the MITRE ATT&CK® matrix via Retrieval-Augmented Generation (RAG) improves the accuracy and reliability of automated threat technique attribution from raw Windows endpoint telemetry.

### Research Positioning

> *Although RAG has been investigated for cybersecurity log analysis and ATT&CK mapping, controlled evaluations of ATT&CK-grounded RAG specifically for technique-level attribution from Windows endpoint telemetry remain limited. This project evaluates the effect of retrieval augmentation and separately analyzes retrieval quality and downstream classification performance.*

This project does **not** claim to invent Retrieval-Augmented Generation, ATT&CK mapping methodologies, or LLM-assisted log triage. Instead, it contributes a strictly controlled empirical evaluation isolating the performance delta introduced by domain-specific retrieval grounding.

---

## Research Questions

The study investigates three core research questions:

### RQ1 (Primary Research Question)
> **To what extent does MITRE ATT&CK-grounded RAG improve the accuracy of LLM-based ATT&CK technique attribution from Windows endpoint logs compared with the same LLM without retrieval augmentation?**
>
> *(Việc bổ sung MITRE ATT&CK-grounded RAG ảnh hưởng như thế nào đến độ chính xác của LLM khi ánh xạ Windows endpoint logs sang ATT&CK Techniques so với cùng mô hình không sử dụng RAG?)*

*Objective:* Measure the end-to-end attribution accuracy gain (if any) when augmenting an identical LLM with a dedicated ATT&CK retrieval component under identical prompting and configuration conditions.

---

### RQ2 (Error Decomposition & Retrieval Impact)
> **How does retrieval quality affect the final accuracy of ATT&CK technique attribution?**
>
> *(Chất lượng retrieval ảnh hưởng như thế nào đến độ chính xác cuối cùng của ATT&CK Technique mapping?)*

*Objective:* Decouple and quantify failure modes within the RAG pipeline:
```text
RAG Failure
├── Retrieval Failure
│   └── Ground-truth technique is NOT present in the retrieved Top-k candidates
│
└── Generation / Classification Failure
    └── Ground-truth technique WAS retrieved, but the LLM failed to select it
```

---

### RQ3 (Retrieval Depth & Efficiency Ablation)
> **How does the number of retrieved ATT&CK candidates (Top-k) affect mapping accuracy and processing cost?**
>
> *(Số lượng ATT&CK candidates được retrieval (Top-k) ảnh hưởng như thế nào đến độ chính xác và chi phí xử lý của ATT&CK Technique mapping?)*

*Objective:* Conduct a parameter ablation study over candidate depths ($k \in \{1, 3, 5, 10\}$) to observe the trade-off between retrieval recall, context-window noise, token expenditure, and inference latency.

---

## Working Hypotheses

The following hypotheses serve as working assumptions for experimental validation:

* **H1:** MITRE ATT&CK-grounded RAG improves technique attribution performance compared with the same LLM without retrieval.
* **H2:** Higher retrieval $\text{Recall}@k$ is positively associated with higher end-to-end mapping accuracy.
* **H3:** Increasing $k$ initially improves mapping performance, but excessive retrieved context introduces distractors (noise) and increases token/latency cost.

---

## Core Experimental Design

This research is designed as a **controlled empirical evaluation** comparing two distinct pipelines on the exact same telemetry inputs.

### Pipeline Architectures

#### 1. Baseline Pipeline (No-RAG)
```text
Windows Endpoint Log
        ↓
       LLM
        ↓
MITRE ATT&CK Technique
```

#### 2. Experimental Pipeline (RAG)
```text
Windows Endpoint Log
        ↓
MITRE ATT&CK Retriever
        ↓
Top-k relevant ATT&CK Techniques
        ↓
Log + Retrieved ATT&CK Knowledge
        ↓
       LLM
        ↓
MITRE ATT&CK Technique
```

### Controlled Variables

To preserve experimental validity, all parameters outside the retrieval mechanism remain strictly identical:
* **Dataset & Samples:** Same test split and telemetry instances across both arms.
* **Language Model:** Same frozen LLM checkpoint, provider, and model version.
* **Inference Parameters:** Fixed temperature (e.g., $T = 0.0$), top_p, and seed configuration.
* **Prompt Schema:** Standardized prompt template, differing only by the conditional injection of the retrieved context block.
* **Output Constraint:** Identical JSON output schema enforcing strict exact-match technique ID generation.

The sole experimental variable is:
```text
MITRE ATT&CK retrieval:
OFF vs ON
```

*Note:* Provider comparisons (e.g., GPT vs. Gemini vs. Claude) are explicitly excluded from the core experiment to avoid confounding variables.

---

## Telemetry Input & Attribution Output

### Input Specification
The input consists of structured Windows endpoint security logs, focusing on:
* Windows Security Event Logs (e.g., Process Creation Event ID 4688)
* Microsoft Sysmon telemetry (e.g., Event ID 1: Process Create, Event ID 3: Network Connect, Event ID 11: File Create, Event ID 13: Registry Event)
* Standard structured Windows endpoint telemetry events.

*Implementation Note:* No SIEM infrastructure or Wazuh decoder reimplementation is required. Native structured Windows/Sysmon event fields provide sufficient signal for the research prototype.

### Output Specification
The primary output for evaluation is the canonical MITRE ATT&CK Technique or Sub-technique identifier:
* **Primary Target:** Exact ID string (e.g., `T1059.001`, `T1053.005`, `T1003.001`).
* **Secondary Metadata (Recorded for diagnostics):** Technique name, candidate rank, and model self-assessed confidence.

---

## Anti-Label-Leakage Protocol

To guarantee methodological integrity and prevent target leakage from detection rules or benchmark artifacts:

> **Ground-truth labels and rule-derived ATT&CK metadata are removed before inference to prevent label leakage.**

Inference queries apply a **strict field whitelist**:
```text
Permitted Telemetry Whitelist:
├── EventID
├── Image
├── CommandLine
├── ParentImage
├── ParentCommandLine
├── TargetFilename
├── RegistryPath
├── SourceIp
├── DestinationIp
├── DestinationPort
├── User
├── Computer
├── ProcessGuid
├── ParentProcessGuid
└── UtcTime
```

**Explicitly Stripped Fields:** Any fields containing `mitre`, `tactic`, `technique`, `rule_name`, `detection`, `sigma`, `compliance`, or pre-annotated ground-truth labels are scrubbed during data loading.

---

## Dataset Strategy

The evaluation pipeline distinguishes between two stages of data usage:

### 1. Synthetic Development Data
A minimal set of handcrafted Windows/Sysmon-style telemetry events paired with verified ground-truth techniques is used solely for development, unit testing, schema verification, and pipeline sanity checks:
```json
{
  "EventID": 1,
  "Image": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
  "CommandLine": "powershell.exe -NoP -NonI -W Hidden -enc SQBFAFgA...",
  "ParentImage": "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE",
  "User": "CORP\\jdoe",
  "UtcTime": "2026-03-01 10:14:22.120"
}
```
*Ground Truth:* `T1059.001` (Command and Scripting Interpreter: PowerShell).

*Synthetic logs are strictly used to test the parser, sanitizer, LLM API, retriever, and evaluation logic. They are not used as the primary dataset to draw empirical research conclusions.*

### 2. Public ATT&CK-Labeled Benchmark Telemetry
The final empirical evaluation will be conducted on real-world, publicly available Windows endpoint telemetry containing verified MITRE ATT&CK ground truth:

> *The final evaluation dataset will be selected from publicly available Windows endpoint telemetry with MITRE ATT&CK ground-truth labels.*

A dataset currently under consideration is **Windows-APT 2025**, which features labeled Windows telemetry traces. The final selection will be confirmed based on label quality and distribution during experimental setup.

### Target Evaluation Scope (Planned)
* **Technique Coverage:** 8–10 representative Enterprise ATT&CK Techniques / Sub-techniques.
* **Sample Density:** Approximately 40–50 samples per technique class to mitigate class imbalance.
* **Evaluation Corpus:** Planned test set of approximately 400–500 evaluation instances.

---

## MITRE ATT&CK Knowledge Base & Retrieval

### Knowledge Corpus
* Grounded directly in official MITRE ATT&CK Enterprise STIX/JSON data.
* > *The experiment will pin a specific MITRE ATT&CK Enterprise version for reproducibility.*
* Extracted document chunks incorporate:
  * Technique ID
  * Technique Name
  * Detailed Description
  * Target Platforms
  * Detection-related information
  * Selected Procedure examples (strictly curated to avoid near-duplicate leakage against evaluation logs).

### Lightweight Retrieval Engine
To maintain experimental reproducibility without heavy infrastructure overhead:
* **Embedding Model:** Dense representations via `sentence-transformers`.
* **Vector Index:** Flat / L2 vector indexing managed by `FAISS`.
* *Zero heavyweight dependencies:* No external vector database servers (Pinecone, Milvus), no knowledge graphs, and no Elasticsearch clusters required.

#### Document Processing Flow:
```text
MITRE ATT&CK STIX Documents
            ↓
    Text Chunking & Metadata
            ↓
     Embedding Model
            ↓
       FAISS Index
```

#### Inference Query Flow:
```text
Sanitized Windows Log
         ↓
  Embedding Model
         ↓
   FAISS Search
         ↓
Top-k ATT&CK Candidates
         ↓
        LLM
```

---

## Language Model & Inference Protocol

* **Model Usage:** A single, frozen LLM provider API endpoint is utilized across both baseline and experimental arms.
* **Generic Model Positioning:** The same LLM is used for both No-RAG and RAG conditions. A specific model and version will be documented in experiment configurations once finalized.
* **No Fine-Tuning:** The research focuses purely on in-context retrieval augmentation without modifying model weights.

---

## Evaluation Metrics

| Metric | Target Component | Purpose |
| :--- | :--- | :--- |
| **Exact-Match Accuracy** | End-to-End | Primary metric: Fraction of predictions matching ground-truth ATT&CK ID |
| **Macro-F1 Score** | End-to-End | Primary metric: Unweighted mean of F1 scores across technique classes |
| **Precision & Recall** | End-to-End | Per-class false positive and false negative attribution analysis |
| **Invalid ATT&CK ID Rate** | Robustness | Frequency of malformed, deprecated, or hallucinated technique strings |
| **Recall@k** | Retriever | Fraction of samples where ground truth is present in retrieved top-k candidates |
| **Token Usage** | Efficiency (RQ3) | Prompt and completion token consumption per sample |
| **Inference Latency** | Efficiency (RQ3) | Wall-clock inference time (seconds per sample) |

---

## Research Contribution

> **RAG2ATT&CK is a controlled empirical study evaluating the effect of MITRE ATT&CK-grounded retrieval on technique-level attribution from Windows endpoint telemetry. It additionally separates retrieval failures from downstream LLM classification failures and evaluates the effect of retrieval depth on mapping performance and processing cost.**

---

## What This Project is NOT (Scope & Exclusions)

To maintain focus and empirical validity, the project explicitly excludes:
* ❌ An operational SIEM, EDR, or SOC analytical platform.
* ❌ Wazuh parser integration, agent deployment, or decoder reimplementation.
* ❌ Autonomous multi-agent systems or complex agentic decision loops.
* ❌ Knowledge graphs or graph database infrastructure.
* ❌ Custom model training or fine-tuning.
* ❌ Custom SDK development, heavy dashboards, or production backends.
* ❌ Large-scale distributed server infrastructure.

The expected deliverable is a self-contained, reproducible **Python research prototype**, experimental configurations, results logs, and the research report.

---

## Planned Project Structure

```text
RAG2ATTCK/
├── README.md
├── requirements.txt
├── configs/
├── data/
│   ├── synthetic/
│   ├── raw/
│   └── processed/
├── src/
│   ├── data_loader.py
│   ├── sanitizer.py
│   ├── attack_kb.py
│   ├── retriever.py
│   ├── llm_mapper.py
│   └── evaluation.py
├── experiments/
├── results/
├── notebooks/
├── tests/
└── docs/
```

---

## Project Status

**Status:** `Research design / early development`

The project is currently establishing baseline experimental specifications, data sanitization protocols, and evaluation tooling. Specific dataset choices and pinned ATT&CK versions will be committed as experiments transition to execution.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.