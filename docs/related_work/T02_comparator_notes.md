# T02: Core Comparator Papers — Structured Extraction Notes

This document contains structured analytical extractions for the eight core comparator papers evaluated for the **RAG2ATTCK** replication-and-extension study. Each entry strictly follows the 12-field schema (A through L) and draws from verified primary sources (publisher versions, official conference proceedings, or author arXiv manuscripts).

---

## 1. Yang & Hsu (2026)

### A. Bibliographic Identity
- **Title:** LLM-Based Malicious Behavior Detection from Sysmon Event Logs: A Practical System Integrating Process Trees, RAG, and In-Context Analysis
- **Authors:** Dai-Ru Yang and Fu-Hau Hsu
- **Year:** 2026 (presented at SITAIBA 2025, eBook ISBN published 13 August 2026)
- **Venue:** *Security and Information Technologies with AI, Internet Computing and Big-Data Applications* (SITAIBA 2025), *Smart Innovation, Systems and Technologies* (SIST), pp. 235–251. Springer, Cham.
- **DOI / URL:** [10.1007/978-3-032-24063-7_18](https://doi.org/10.1007/978-3-032-24063-7_18)
- **Paper Version Used:** Official Springer publisher chapter.

### B. Research Problem
- **Primary Task:** Malicious behavior detection and explanation from Windows Sysmon event logs.
- **Nature:** Binary classification (detecting whether observed process activity exhibits malicious vs. benign behavior) accompanied by natural-language explanations and recommended mitigation strategies.
- **Secondary Goal:** Practical, explainable triage for Security Operation Centers (SOCs) using open-source, locally deployable LLMs.

### C. Input
- **Data Source:** Microsoft Windows System Monitor (Sysmon) event logs.
- **Unit of Analysis:** Reconstructed process trees (hierarchical process creation trees capturing parent-child process relationships and execution sequences from Sysmon events), rather than isolated single event rows.
- **Datasets:** Open-source attack samples combined with simulated benign process execution trees.

### D. Output
- **Granularity:** Binary malicious vs. benign detection label; qualitative natural-language threat summary/explanation; and operational mitigation recommendations.
- **ATT&CK Mapping:** ATT&CK concepts are referenced contextually in descriptions/retrieval templates, but exact canonical MITRE ATT&CK Technique ID (e.g., `T1059.001`) or Sub-technique attribution is **NOT** the primary structured output target.

### E. Ground Truth
- **Source:** Ground truth is derived from controlled execution of open-source attack scripts and simulated normal user/system activities.
- **Level of Granularity:** Scenario/process-tree level (an entire reconstructed execution tree is labeled as malicious or benign).
- **Circularity / Independence:** High independence from internal model outputs, as labels follow the execution script provenance, though detailed per-event label linkage was not the focus.

### F. RAG Architecture
- **Retrieval Corpus:** Security knowledge base containing attack patterns, behavioral templates, and threat context.
- **Retriever:** Semantic vector matching over security templates and historical attack behavior patterns.
- **Embedding Model:** NOT REPORTED in abstract/preview metadata.
- **Vector Database / Index:** Vector index for semantic similarity search.
- **Top-k:** Evaluated under fixed retrieval configuration; systematic Top-k candidate depth ablation (e.g., k in {1, 3, 5, 10}) is NOT REPORTED.
- **Reranker:** NOT REPORTED.
- **Prompt / Context Composition:** In-context prompt injecting retrieved security templates alongside the serialized process tree hierarchy.
- **LLM Evaluated:** Three open-source models of varying parameter sizes: Mistral-7B, phi-2 (2.7B), and TinyLlama-1.1B.
- **Independent Retrieval Quality:** NOT REPORTED (retriever Recall@k was not independently evaluated or decoupled from downstream detection).

### G. Experimental Design
- **Baseline vs. RAG:** Controlled matched comparison: evaluates each of the three LLMs with RAG vs. without RAG (No-RAG baseline).
- **Ablations:** LLM model scale comparison (7B vs 2.7B vs 1.1B); With-RAG vs Without-RAG contrast.
- **Dataset Size:** Set of attack process trees and benign simulated trees (exact sample count across classes: NOT REPORTED in public preview).
- **Same LLM Across Conditions:** Yes, exactly matched LLM instances evaluated under No-RAG and RAG settings.

### H. Metrics
- Precision
- F1-score
- False Positive Rate (FPR)

### I. Main Result Relevant to Us
- RAG improves Precision and F1-score by an average of 14%–17% across all evaluated LLMs compared to the No-RAG baseline.
- RAG reduces false positives by over 10%.
- Smaller models (TinyLlama-1.1B, phi-2) exhibited the largest relative performance improvements when augmented with RAG, demonstrating that external knowledge grounding compensates for limited parametric knowledge.

### J. Similarities to RAG2ATTCK
- Shares the same endpoint telemetry environment: Windows Sysmon event logs.
- Utilizes the same fundamental experimental contrast: matched LLM No-RAG baseline vs. RAG-enabled pipeline.
- Shares the goal of mitigating hallucination and improving log comprehension through external knowledge retrieval.

### K. Differences from RAG2ATTCK
- **Prediction Target:** Yang & Hsu perform binary malicious behavior detection and narrative explanation; RAG2ATTCK performs exact multiclass MITRE ATT&CK Technique / Sub-technique attribution ID generation (`Txxxx.yyy`).
- **Unit of Observation:** Yang & Hsu use reconstructed multi-event process trees; RAG2ATTCK evaluates structured, sanitized endpoint log event records.
- **Diagnostic Decomposition:** Yang & Hsu do not decouple retriever failure from downstream LLM classification failure; RAG2ATTCK explicitly isolates Retrieval Failure (GT not in Top-k) from Generation/Classification Failure (GT in Top-k but LLM mispredicts).
- **Depth Ablation:** Yang & Hsu do not evaluate retrieval depth k in {1, 3, 5, 10} or measure latency/token costs per k.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Using RAG to analyze Windows Sysmon logs, or proving that RAG improves Sysmon log classification performance over a No-RAG baseline.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, conducting a strictly controlled evaluation for *exact MITRE ATT&CK Technique/Sub-technique attribution* from Windows endpoint telemetry, decoupling retriever recall from LLM selection failure, and systematically analyzing retrieval depth (k) trade-offs against token cost and latency.

---

## 2. AWS CloudTrail RAG Paper — Adediran et al. (2026)

### A. Bibliographic Identity
- **Title:** Retrieval-Augmented Large Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail Mitre ATT&CK Mapping
- **Authors:** Goodness Adediran, Kenny Awuson-David, and Yussuf Ahmed
- **Year:** 2026 (received 13 December 2025, accepted 14 February 2026, published 12 March 2026)
- **Venue:** *Computers, Materials & Continua* (CMC), Vol. 87, No. 2, Article 100. Tech Science Press.
- **DOI / URL:** [10.32604/cmc.2026.077606](https://doi.org/10.32604/cmc.2026.077606)
- **Paper Version Used:** Official publisher open-access HTML version.

### B. Research Problem
- **Primary Task:** Cloud threat detection and ATT&CK mapping on AWS CloudTrail logs using a Retrieval-Augmented LLM pipeline.
- **Nature:** Binary threat classification (malicious vs. benign) combined with MITRE ATT&CK Cloud technique attribution for cloud security operations.

### C. Input
- **Data Source:** AWS CloudTrail audit logs in JSON format, generated via Stratus Red Team attack simulation.
- **Unit of Analysis:** Individual JSON CloudTrail log events containing AWS API calls (event names, event sources, request parameters, user identities, error codes).
- **Dataset Size:** 1,724 total generated CloudTrail events; 200 systematically sampled evaluation events (122 malicious, 78 benign), spanning 9 ATT&CK techniques, 8 tactics, and 9 AWS services.

### D. Output
- **Granularity:** ATT&CK Cloud technique identification (technique-level attribution) plus binary malicious/benign classification.

### E. Ground Truth
- **Source:** Expert-annotated ground truth labels. A cybersecurity expert (MSc, 5+ years SOC/cloud experience, ATT&CK certified) annotated each event using CloudTrail context, the ATT&CK Cloud matrix, the AWS Threat Technique Catalogue, and Stratus Red Team execution context.
- **Independence & Leakage Consideration:** The `stratus-red-team` user-agent string is present in raw CloudTrail logs; the paper explicitly notes this as a potential leakage concern if not audited, as models could shortcut genuine reasoning by pattern-matching the user-agent string rather than analysing the API call semantics.

### F. RAG Architecture
- **Retrieval Corpus:** MITRE ATT&CK Enterprise Cloud matrix, AWS Threat Technique Catalogue, cloud security blogs, and contemporary threat reports.
- **Architecture:** Two-step RAG — CloudTrail JSON event is first sent to the LLM to generate a semantic search query, which is then used for dense retrieval over the knowledge base, followed by grounded generation.
- **Embedding Model:** `text-multilingual-embedding-002`.
- **Chunking:** 1,024-token chunks with 256-token overlap.
- **Vector Database / Index:** Vertex AI RAG Vector Database.
- **Top-k:** Fixed retrieval depth (parameter ablation over variable k was **NOT** reported; identified as future work).
- **Reranker:** None; no reranker or relevance-filter agent was used.
- **LLM Evaluated:** Google Gemini 2.5 Pro.
- **Independent Retrieval Quality:** NOT REPORTED quantitatively (no Recall@k or MRR metrics reported for the retriever alone).

### G. Experimental Design
- **Matched Comparison:** Directly compares Gemini 2.5 Pro *with* RAG vs. Gemini 2.5 Pro *without* RAG (prompt-only baseline) on the identical 200 evaluation CloudTrail events.
- **Same Model Across Conditions:** Yes, strictly matched single-LLM evaluation.
- **Evaluation Scope:** Binary detection (malicious/benign) and ATT&CK technique attribution, with latency and cost measurement.

### H. Metrics
- Accuracy
- Precision
- Recall
- Macro-F1
- End-to-end latency (seconds per event)
- Operational cost (USD per event)

### I. Main Result Relevant to Us
- RAG improves MITRE ATT&CK mapping accuracy from **46% (No-RAG baseline) to 78% (RAG pipeline)** — an absolute gain of +32 percentage points.
- Precision: 69% → 85%; Recall: 46% → 78%; F1: 45% → 79%.
- Operational figures: 4.1 s/event latency, \$0.00376/event cost.
- Error analysis of failure cases revealed three primary error categories: retrieval-generation gap (~26%), knowledge-base gap (~20%), and ambiguous ground truth (~20%). The 60% summary characterizes retrieval quality as the primary overall bottleneck across all error types — it is **NOT** a statement that 60% of individual errors were retrieval non-hits.

### J. Similarities to RAG2ATTCK
- Directly evaluates the empirical delta between No-RAG baseline and ATT&CK-grounded RAG under a strictly matched single-LLM design.
- Evaluates MITRE ATT&CK technique attribution alongside binary threat detection.
- Measures operational cost and inference latency alongside attribution accuracy.

### K. Differences from RAG2ATTCK
- **Telemetry Domain:** AWS CloudTrail cloud API logs vs. Windows endpoint host telemetry (Sysmon / Windows Security Event Log).
- **Retrieval Architecture:** Two-step query-expansion RAG with diverse web/blog sources vs. single-step dense retrieval directly over official pinned MITRE ATT&CK STIX documentation.
- **Retriever Ablation:** Adediran et al. did not ablate retrieval candidate depth (k=1, 3, 5, 10) nor measure quantitative retriever Recall@k.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Conceptualizing a controlled No-RAG vs. RAG comparison for ATT&CK mapping, or demonstrating that RAG significantly improves LLM-based ATT&CK technique identification.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, replicating this controlled contrast in the distinct, high-volume environment of Windows endpoint logs, performing systematic Top-k candidate depth ablation, and providing formal decoupled retrieval diagnostic metrics.

---

## 3. CAM-LDS — Landauer et al. (2026)

### A. Bibliographic Identity
- **Title:** CAM-LDS: Cyber Attack Manifestations for Automatic Interpretation of System Logs and Security Alerts
- **Authors:** Max Landauer, Wolfgang Hotwagner, Thorina Boenke, Florian Skopik, and Markus Wurzenberger
- **Year:** 2026 (published online 26 August 2026; preprint deposited March 2026)
- **Venue:** *International Journal of Information Security*, Vol. 25, Issue 5, Article 148 (2026). Springer Nature. DOI: [10.1007/s10207-026-01318-x](https://doi.org/10.1007/s10207-026-01318-x)
- **Paper Version Used:** Version of Record (VoR) published in *International Journal of Information Security* (2026). (Note: An earlier author manuscript was deposited as arXiv:2603.04186v1 in March 2026).

### B. Research Problem
- **Primary Task:** Benchmark dataset construction and baseline zero-shot LLM evaluation for automated interpretation and ATT&CK mapping of multi-source system logs and security alerts.
- **Focus:** Systematic characterization of attack manifestations across command observability, event frequency, performance metrics, and IDS alerts.

### C. Input
- **Data Source:** Linux-based telemetry collected from 18 distinct sources across Linux hosts (auditd, auth.log, syslog, Apache/Nginx web access logs, network/IDS alerts from Suricata and Zeek, Wazuh agent on Linux hosts). The authors explicitly note that CAM-LDS is a "fully open-source and reproducible Linux-based data set" created to fill the void of Linux attack datasets, contrasting with existing Windows-focused datasets.
- **Unit of Analysis:** Attack step manifestations comprising 10 randomly sampled log lines per source per attack step.
- **Dataset Size:** 7 multi-stage attack scenarios encompassing 198 attack steps generating logs, covering 81 distinct MITRE ATT&CK techniques across 13 tactics.

### D. Output
- **Granularity:** Top-10 ranked MITRE ATT&CK technique IDs (descending likelihood), 7-point Likert scale maliciousness confidence rating, and short natural-language explanations.

### E. Ground Truth
- **Source:** Deterministic emulation scripts executed in a fully reproducible testbed; ground truth technique IDs are directly bound to the specific executed script commands.
- **Independence & Leakage Consideration:** In data preprocessing, explicit ATT&CK technique identifiers and tactic labels were stripped from alerts. However, the study observes that IDS alerts inherently contain residual semantic clues and answer-bearing descriptive text (e.g., signature descriptions closely mirroring attack mechanics) that assist inference without leaking target labels directly. By contrast, RAG2ATTCK evaluates raw/sanitized Windows endpoint event logs (Sysmon/Security) with zero IDS alert signatures or pre-processed detection rules.

### F. RAG Architecture
- **Uses RAG?:** **NO.** CAM-LDS conducts a purely zero-shot, prompt-based LLM evaluation without an external retrieval engine or knowledge base.
- **Retrieval Corpus / Retriever / Vector DB:** NOT APPLICABLE.
- **LLM Evaluated:** Multiple frontier and open-weights models evaluated in the Version of Record: GPT-5.5, GPT-5.2, Llama-4, Qwen3, and Ministral (temperature T=0). (The preliminary March 2026 arXiv preprint evaluated single-model ChatGPT 5.2).

### G. Experimental Design
- **Conditions:** Zero-shot prompting of LLMs on 198 attack steps under ATT&CK v18.1.
- **Ablations:** Correlation of LLM attribution accuracy with manifestation characteristics (command presence, log volume, IDS alert presence).
- **No-RAG vs. RAG:** None (only No-RAG prompting is evaluated).

### H. Metrics
- Rank of highest matching technique (Position #1, #2–#3, #4–#10, or Not in Top 10)
- Hit rate across ranked tiers
- Qualitative explanation quality and confidence calibration

### I. Main Result Relevant to Us
- In the published Version of Record benchmark (198 attack steps, ATT&CK v18.1), the best-performing model achieves a Top-1 accuracy of 41.8% (correct technique placed at rank #1) and a Top-10 accuracy of 67.2% (correct technique within top 10 candidates). For the remaining 32.8% of steps, the model fails to identify the correct technique within its top 10 predictions. (The earlier preprint reported ~33% at top-1/2 and ~66% within top-10 using ChatGPT 5.2).
- Accuracy is heavily dependent on command-line observability and drops severely when command strings are absent.
- IDS alerts introduce substantial residual semantic clues / answer-bearing indicators, boosting classification success compared to raw execution telemetry alone.

### J. Similarities to RAG2ATTCK
- Evaluates exact-match MITRE ATT&CK technique identification from system log data.
- Emphasizes the critical necessity of auditing and controlling for label leakage and answer-bearing alert text.

### K. Differences from RAG2ATTCK
- **No RAG Component:** CAM-LDS does not implement or evaluate retrieval augmentation; it is solely an evaluation of parametric LLM zero-shot capabilities.
- **Input Scope & Platform:** Exclusively Linux-based multi-source telemetry (auditd, auth.log, Suricata, Zeek, Wazuh) rather than standardized Windows endpoint event logs.
- **Sample Selection:** Employs arbitrary 10-line random sampling per log file rather than clean, structured event-level records.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Zero-shot ATT&CK technique mapping from system logs, showing that LLMs can identify ATT&CK IDs from command lines, or identifying residual semantic clues from IDS alerts.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, RAG2ATTCK provides the missing empirical contrast between unaugmented LLMs and ATT&CK-grounded RAG on standardized Windows endpoint logs, testing whether external retrieval mitigates the 32.8% failure rate observed in purely zero-shot LLM log interpretation.

---

## 4. TechniqueRAG — Lekssays et al. (2025)

### A. Bibliographic Identity
- **Title:** TechniqueRAG: Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text
- **Authors:** Ahmed Lekssays, Utsav Shukla, Husrev Taha Sencar, and Md Rizwan Parvez
- **Year:** 2025
- **Venue:** *Findings of the Association for Computational Linguistics: ACL 2025* (Findings of ACL 2025), pp. 1076.
- **DOI / arXiv:** [10.18653/v1/2025.findings-acl.1076](https://doi.org/10.18653/v1/2025.findings-acl.1076) / arXiv:2505.11988v1
- **Paper Version Used:** arXiv:2505.11988v1 / ACL Anthology version.

### B. Research Problem
- **Primary Task:** Automated annotation and mapping of unstructured Cyber Threat Intelligence (CTI) report text to fine-grained MITRE ATT&CK techniques and sub-techniques.
- **Nature:** Domain-specific NLP information extraction and multi-label text classification under extreme data scarcity and large label spaces (~600+ classes).

### C. Input
- **Data Source:** Unstructured natural-language CTI text (sentences, paragraphs, and reports from threat intelligence feeds, TRAM, and RC-Threat).
- **Unit of Analysis:** Textual sentence/paragraph snippets describing adversary actions.

### D. Output
- **Granularity:** Exact canonical MITRE ATT&CK Technique and Sub-technique identifiers.

### E. Ground Truth
- **Source:** Expert-annotated public CTI benchmarks (TRAM, RC-Threat, and curated CTI datasets).
- **Level of Granularity:** Sentence-level / paragraph-level document annotations.

### F. RAG Architecture
- **Retrieval Corpus:** MITRE ATT&CK knowledge base (technique descriptions, execution procedures).
- **Retriever:** Off-the-shelf sparse (BM25) and dense retrievers extracting candidate techniques.
- **Embedding Model:** Pre-trained dense retrievers / sentence embeddings.
- **Vector Database / Index:** Standard vector indexing.
- **Reranker:** Zero-shot instruction-tuned LLM re-ranking module to filter noisy candidates.
- **Top-k:** Evaluates retrieval candidates; explores candidate pool sizes.
- **LLM / Generator:** Parameter-efficient fine-tuned lightweight LLMs (e.g., `TechniqueRAG-FS-Ministral-8B`).
- **Independent Retrieval Quality:** **YES.** Explicitly reports retriever Hit@k / Recall@k before and after re-ranking.

### G. Experimental Design
- **Baselines:** Direct LLM zero-shot/few-shot prompting, standard fine-tuned classifiers, and vanilla RAG without re-ranking.
- **RAG Conditions:** Multi-stage pipeline: Retriever -> LLM Re-ranker -> Fine-tuned Generator.
- **Retrieval Metrics Reported:** Evaluates retrieval recall and precision independently from final generation.

### H. Metrics
- Precision, Recall, Macro-F1, Micro-F1
- Hit@k / Recall@k for retrieval stages

### I. Main Result Relevant to Us
- Demonstrates that vanilla off-the-shelf dense retrievers retrieve significant noise due to fine-grained lexical overlaps across ATT&CK sub-techniques.
- Proves that decoupling candidate retrieval/re-ranking from final generation significantly elevates end-to-end attribution performance in specialized cybersecurity domains.

### J. Similarities to RAG2ATTCK
- Grounded in the official MITRE ATT&CK Enterprise taxonomy.
- Targets exact Technique and Sub-technique attribution.
- Emphasizes the critical dependency of end-to-end accuracy on upstream retrieval quality.

### K. Differences from RAG2ATTCK
- **Input Modality:** Natural language CTI text vs. semi-structured Windows endpoint log telemetry.
- **Model Training:** Involves supervised fine-tuning of the generator LLM; RAG2ATTCK explicitly restricts scope to in-context retrieval augmentation of frozen, unmodified models.
- **Pipeline Complexity:** Multi-stage re-ranking and generator fine-tuning vs. lightweight flat dense retrieval designed for reproducible evaluation.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Proposing RAG for MITRE ATT&CK technique mapping, analyzing retrieval Recall@k in ATT&CK attribution, or demonstrating that retrieval errors propagate to generation errors.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, translating and testing these retrieval-attribution relationships within the structured Windows endpoint telemetry setting, where inputs are noisy system events rather than descriptive human prose.

---

## 5. H-TechniqueRAG — Morbiato et al. (2026)

### A. Bibliographic Identity
- **Title:** Hierarchical Retrieval Augmented Generation for Adversarial Technique Annotation in Cyber Threat Intelligence Text
- **Authors:** Filippo Morbiato, Markus Keller, Priya Nair, and Luca Romano
- **Year:** 2026 (March/April 2026)
- **Venue:** arXiv preprint: arXiv:2604.14166v1
- **DOI / URL:** [arXiv:2604.14166](https://arxiv.org/abs/2604.14166)
- **Paper Version Used:** arXiv:2604.14166v1 author manuscript.

### B. Research Problem
- **Primary Task:** Mitigating context overload, distractor noise, and retrieval latency in LLM-based ATT&CK technique mapping from CTI text.
- **Focus:** Hierarchical decomposition of the ATT&CK search space to optimize retrieval precision and candidate context depth.

### C. Input
- **Data Source:** CTI text reports and attack descriptions.
- **Unit of Analysis:** Unstructured CTI text segments.

### D. Output
- **Granularity:** Two-tier prediction: MITRE ATT&CK Tactic followed by fine-grained Technique / Sub-technique IDs.

### E. Ground Truth
- **Source:** CTI annotation benchmarks derived from public threat intelligence datasets.

### F. RAG Architecture
- **Retrieval Corpus:** MITRE ATT&CK Enterprise matrix structured hierarchically (Tactics -> Techniques -> Sub-techniques).
- **Retriever:** Two-stage hierarchical retriever: Stage 1 retrieves/identifies high-level Tactics; Stage 2 retrieves Techniques strictly constrained within the identified Tactic.
- **Embedding Model:** Dense semantic sentence encoders.
- **Top-k & Context Analysis:** Systematically analyzes retrieval depth k and context size; documents context-window pollution when k is excessive in flat RAG.
- **Reranker:** Tactic-aware re-ranking module.
- **LLM Evaluated:** Open-weights instruction models.
- **Independent Retrieval Quality:** YES, evaluates candidate retrieval hit rate and search space reduction percentage (achieving a 77.5% search space pruning).

### G. Experimental Design
- **Comparisons:** Flat RAG (TechniqueRAG baseline) vs. Hierarchical RAG (H-TechniqueRAG).
- **Ablations:** Effect of context depth (k), latency profiling, and LLM call count reduction.

### H. Metrics
- Macro-F1, Micro-F1, Accuracy
- Retrieval Latency (ms) and API call volume
- Search space reduction ratio (%)

### I. Main Result Relevant to Us
- Increasing retrieval depth k in flat RAG creates a "distractor effect," where irrelevant candidate techniques pollute the prompt and degrade LLM reasoning.
- Constraining retrieval context reduces latency by 62.4% and API calls by 60% while boosting attribution F1 by 3.8%.

### J. Similarities to RAG2ATTCK
- Directly investigates the impact of candidate context depth (Top-k) on attribution accuracy and inference efficiency.
- Explores distractor noise and context saturation in ATT&CK-grounded generation.

### K. Differences from RAG2ATTCK
- **Input Data:** CTI text vs. Windows endpoint telemetry.
- **Retrieval Mechanism:** Complex hierarchical multi-stage routing vs. controlled flat dense retrieval ablation.
- **Research Goal:** Proposes a novel hierarchical algorithmic architecture; RAG2ATTCK conducts an empirical parameter ablation over standard flat RAG (k in {1, 3, 5, 10}).

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Observing that larger Top-k retrieval depths introduce noise/distractors into LLM prompts, or discovering that context depth involves a latency/accuracy trade-off in ATT&CK RAG.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, quantifying the exact empirical inflection point of k in {1, 3, 5, 10} specifically for raw Windows endpoint logs under a strictly controlled single-LLM setup.

---

## 6. Trace2ATT&CK — Lupinacci et al. (2026)

### A. Bibliographic Identity
- **Title:** A Graph-Based Approach for Mapping Kernel-Level Telemetry to MITRE ATT&CK
- **Authors:** Matteo Lupinacci, Luigi Arena, Francesco Blefari, and Angelo Furfaro
- **Year:** 2026 (submitted 11 September 2026)
- **Venue:** arXiv preprint: arXiv:2609.12841v1
- **DOI / URL:** [10.48550/arXiv.2609.12841](https://doi.org/10.48550/arXiv.2609.12841)
- **Paper Version Used:** arXiv:2609.12841v1 author manuscript.

### B. Research Problem
- **Primary Task:** Automated mapping of raw kernel-level system telemetry to MITRE ATT&CK techniques and sub-techniques.
- **Challenge Addressed:** Bridging the semantic gap between high-volume, low-level kernel system calls and high-level behavioral attack descriptions without relying on retrospective CTI text.

### C. Input
- **Platform:** **Linux** operating system.
- **Data Source:** Kernel-level system calls collected via eBPF instrumentation using Tracee (`execve`, file operations, network socket calls).
- **Data Transformation:** System calls are structured into Provenance Graphs (PG), then reduced into serialized "Weighted Command Graphs" in DOT format.
- **Evaluation Dataset:** 347 Linux Atomic Red Team test executions averaging ~62,000 raw eBPF events per scenario.

### D. Output
- **Granularity:** Ranked list of MITRE ATT&CK Technique and Sub-technique candidates along with natural-language supporting rationales.

### E. Ground Truth
- **Source:** Atomic Red Team execution metadata (each test case has a predetermined authoritative ATT&CK technique label).
- **Level of Granularity:** Test-case / execution-scenario level.
- **Circularity / Independence:** High independence; execution is driven by structured emulation manifests.

### F. RAG Architecture
- **Retrieval Corpus:** Official MITRE ATT&CK Enterprise knowledge base indexed in a local Chroma vector database. Technique descriptions chunked into 800-word blocks.
- **Retriever:** Dense semantic retrieval using Maximal Marginal Relevance (MMR, lambda=0.5, fetch_k=20).
- **Embedding Model:** `mxbai-embed-large-v1`.
- **Top-k:** Fixed Top-5 technique chunks retrieved and prepended to the prompt.
- **Reranker:** None.
- **LLM Evaluated:** Seven local open-weights LLMs: `gpt-oss-20b`, `gpt-oss-120b`, `gemma-4-31b-it`, `llama-3.3-70b-instruct`, `deepseek-r1-distill-qwen-32b`, `foundation-sec-8b-reasoning`, `qwen3.5-9b`.
- **Independent Retrieval Quality:** NOT REPORTED (retrieval recall was not independently measured; only end-to-end ranking metrics were reported).

### G. Experimental Design
- **Baselines vs. RAG:** Compared pure prompting (taxonomy-grounded No-RAG baseline) against RAG across all seven local models.
- **Representation Ablation:** Raw eBPF log stream vs. Provenance Graph vs. Compressed Command Graph.
- **Same LLM Across Conditions:** Yes, evaluated across matched local model checkpoints.
- **Top-k Depth Ablation:** Evaluated output ranking metrics at cutoffs 1, 3, 5 (HR@1, HR@3, HR@5), but did **NOT** perform parameter ablation across retrieval candidate depths (k).

### H. Metrics
- Hit Rate at k (HR@1, HR@3, HR@5 in output ranking)
- Mean Reciprocal Rank (MRR@5)
- Normalized Discounted Cumulative Gain (NDCG@5)
- Empty output / context-exceeded failure rate

### I. Main Result Relevant to Us
- RAG consistently improves ATT&CK technique mapping performance over pure prompting across all tested open-weights LLMs.
- Prompting LLMs with raw, uncurated event streams fails catastrophically (empty output rate over 53%–56% due to context saturation and lack of explicit causal structure), whereas structured representations achieve strong mapping accuracy.
- A specialized 8B parameter security model (`foundation-sec-8b-reasoning`) achieved competitive performance against 70B+ general models when grounded via RAG.

### J. Similarities to RAG2ATTCK
- Focuses directly on system telemetry rather than human-written CTI text.
- Directly evaluates the empirical delta between No-RAG prompting and ATT&CK-grounded RAG.
- Targets exact Technique and Sub-technique attribution.

### K. Differences from RAG2ATTCK
- **Operating System:** Linux kernel telemetry (eBPF) vs. Windows endpoint telemetry (Sysmon / Windows Event Logs).
- **Data Representation:** Requires complex provenance graph construction, graph reduction, and DOT serialization; RAG2ATTCK operates on sanitized, native structured event logs.
- **Diagnostic Focus:** Trace2ATT&CK evaluates graph representations vs. raw logs; it does not decouple retriever failure from generation failure, nor does it conduct retrieval Top-k depth parameter ablation.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Showing that RAG improves ATT&CK mapping from system telemetry over an ungrounded LLM baseline, or demonstrating local LLM feasibility for ATT&CK mapping.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, establishing a lightweight, graph-free evaluation protocol for native Windows endpoint logs, while providing decoupled diagnostic metrics linking retrieval success to downstream attribution correctness.

---

## 7. Okuma et al. (2023)

### A. Bibliographic Identity
- **Title:** Automated Mapping Method for Sysmon Logs to ATT&CK Techniques by Leveraging Atomic Red Team
- **Authors:** Momoka Okuma, Koki Watarai, Satoshi Okada, and Takuho Mitsunaga
- **Year:** 2023 (presented November 2023)
- **Venue:** *2023 6th International Conference on Signal Processing and Information Security* (ICSPIS 2023), IEEE.
- **DOI / URL:** [10.1109/ICSPIS60075.2023.10343783](https://doi.org/10.1109/ICSPIS60075.2023.10343783)
- **Paper Version Used:** Official IEEE Conference Proceedings.

### B. Research Problem
- **Primary Task:** Automated rule-based correlation and mapping of Windows Sysmon event logs to MITRE ATT&CK techniques.
- **Nature:** Pre-LLM / heuristic telemetry attribution designed to accelerate SOC log triage.

### C. Input
- **Data Source:** Windows Sysmon event logs generated during execution of Atomic Red Team attack simulation tests.
- **Unit of Analysis:** Sysmon event log streams (Event ID 1 Process Create, etc.).

### D. Output
- **Granularity:** MITRE ATT&CK Technique identifiers.

### E. Ground Truth
- **Source:** Atomic Red Team test metadata defining the executed technique.
- **Independence:** Ground truth is established by the execution framework.

### F. RAG Architecture
- **Uses RAG?:** **NO.** This is a non-LLM, rule/signature-based correlation study developed prior to the widespread application of generative RAG in log analysis.
- **Retriever / Vector DB / LLM:** NOT APPLICABLE.

### G. Experimental Design
- Evaluation of rule-matching heuristic precision and coverage against Atomic Red Team execution logs.

### H. Metrics
- Detection rate, mapping accuracy, false matching frequency.

### I. Main Result Relevant to Us
- Demonstrates that Windows Sysmon event fields (specifically command lines, process images, parent processes) contain sufficient discriminative signal to map adversary activity to MITRE ATT&CK techniques.

### J. Similarities to RAG2ATTCK
- Shares the identical input telemetry domain: Windows Sysmon event logs.
- Shares the identical conceptual goal: mapping endpoint log evidence to MITRE ATT&CK technique categories.

### K. Differences from RAG2ATTCK
- Completely lacks generative AI, LLMs, vector search, or RAG architecture.
- Relies on deterministic rule extraction rather than probabilistic semantic reasoning or retrieval augmentation.

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Proposing that Windows Sysmon logs can be mapped to MITRE ATT&CK techniques, or identifying Sysmon as a viable data source for technique attribution.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, serving as historical technical precedent, establishing the baseline feasibility of Windows Sysmon -> ATT&CK mapping before evaluating modern LLM and RAG paradigms.

---

## 8. LADE — Gwak et al. (2026/2027)

### A. Bibliographic Identity
- **Title:** LADE: LLM-Assisted Advanced Persistent Threat Detection and Explanation
- **Authors:** Joon-Young Gwak, Aubrey Strier, Zhaohan Xi, Guanhua Yan, Xiaokui Shu, Scott D. Stoller, and Ping Yang
- **Year:** 2026 conference / 2027 book copyright (presented at SecureComm 2026 in July 2026; electronic proceedings published July 2026; print proceedings copyright 2027)
- **Venue:** *Security and Privacy in Communication Networks* (SecureComm 2026), Lecture Notes of the Institute for Computer Sciences, Social Informatics and Telecommunications Engineering (LNICST), Springer.
- **DOI / URL:** [10.1007/978-3-032-32767-3_11](https://doi.org/10.1007/978-3-032-32767-3_11)
- **Paper Version Used:** Springer conference proceedings chapter.

### B. Research Problem
- **Primary Task:** Advanced Persistent Threat (APT) detection, attack sequence reconstruction, ATT&CK mapping, and automated narrative explanation from host-side command executions.
- **Decomposition:** Three-phase workflow: (1) Anomaly detection / command sequence filtering, (2) ATT&CK technique identification, (3) Natural language explanation generation.

### C. Input
- **Data Source:** Host-side shell command execution traces and script execution logs (e.g., DARPA Transparent Computing and simulated APT scenarios).
- **Unit of Analysis:** Sequences of shell commands (evaluated on 35 attack sequences averaging ~990 command snippets, ~4.8 lines per snippet).

### D. Output
- **Granularity:** Ranked list of candidate MITRE ATT&CK techniques (evaluating Top-1, Top-3, Top-10 output candidates), paired with natural language narrative attack explanations.

### E. Ground Truth
- **Source:** Scenario execution documentation from benchmark datasets (DARPA TC / simulated APT traces).

### F. RAG Architecture
- **Uses RAG?:** **NO.** LADE relies on multi-stage in-context prompting of LLMs without an external vector database or retrieval-augmented generation component.
- **Retrieval Corpus / Retriever / Vector DB:** NOT APPLICABLE.
- **LLM Evaluated:** Commercial / open LLM prompting engines.
- **Top-k Distinction:** LADE reports **model output ranking accuracy** (Top-1, Top-3, Top-10 predictions generated by the LLM), which must **NOT** be confused with retrieval Top-k candidates retrieved from a vector database.

### G. Experimental Design
- Multi-step prompting pipeline evaluated on 35 attack sequences.
- Compares rule-based/traditional ML baselines against LLM-assisted multi-stage detection and explanation.

### H. Metrics
- Precision, Recall, F1-score
- Top-1, Top-3, Top-10 output ranking accuracy
- Qualitative explanation fidelity

### I. Main Result Relevant to Us
- Confirms that analyzing host command sequences enables effective identification and explanation of multi-step APT behaviors.
- Highlights that evaluating ranked candidate outputs (Top-k output accuracy) provides actionable utility for security analysts compared to rigid single-label classification.

### J. Similarities to RAG2ATTCK
- Focuses on host-side command-level execution behavior.
- Evaluates attribution to MITRE ATT&CK techniques alongside explanation.

### K. Differences from RAG2ATTCK
- **No RAG Mechanism:** LADE does not use retrieval augmentation; it is an in-context multi-stage prompting and reasoning pipeline.
- **Input Scope & Volume:** Evaluated on a limited set of 35 command sequences (~4.7K log lines per scenario), whereas RAG2ATTCK evaluates standardized event-level endpoint telemetry.
- **Top-k Semantics:** LADE's Top-k refers strictly to the LLM's ranked output predictions, whereas RAG2ATTCK's Top-k refers to retriever candidate depth (k in {1, 3, 5, 10}).

### L. Novelty Implications
- **RAG2ATTCK MUST NOT claim novelty for:** Mapping host command sequences to ranked ATT&CK candidate lists, or utilizing LLMs to interpret execution logs.
- **Potential remaining setting-specific contribution:** Within the reviewed comparator set, RAG2ATTCK evaluates whether explicit ATT&CK retrieval augmentation (RAG) resolves the knowledge cutoff and hallucination limitations present in pure in-context prompting pipelines like LADE on standardized Windows endpoint logs.
