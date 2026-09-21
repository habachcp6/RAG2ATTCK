# T33 — Related Work and Research Gap

## Scope and evidence policy

This report finalizes the literature positioning for RAG2ATTCK. It uses the
repository's T02 comparator notes/matrix as the extraction record and checks
each bibliographic anchor against a DOI, publisher/research portal, ACL
Anthology/arXiv record, or author manuscript. Details not reported by a
source remain `NOT REPORTED`; the report does not infer them from a method's
name.

## Comparison matrix

| Work | Input / platform | Task and ATT&CK granularity | RAG and corpus | Retrieval / LLM evaluation | Top-k / failure analysis | Dataset and main contribution | Difference from RAG2ATTCK |
|---|---|---|---|---|---|---|---|
| Yang & Hsu (2026; conference 2025, online 2026) | Windows Sysmon; Windows | Malicious-behavior detection and triage explanation; ATT&CK is contextual rather than the primary exact-ID target | RAG with security templates/attack patterns; embedding model and vector database NOT REPORTED | Precision, F1 and FPR across Mistral-7B, phi-2 (2.7B), TinyLlama-1.1B; standalone retriever metrics NOT REPORTED | Retrieval depth ablation and retriever-vs-generation failure decomposition NOT REPORTED (single fixed retrieval setting) | Reconstructed process trees from open-source attack scripts and benign user workflows; total sample counts NOT REPORTED; matched RAG/no-RAG experiments | Binary detection and process-tree focus, not exact technique/sub-technique attribution (`Txxxx.yyy`) or retriever Recall@k |
| Adediran et al. (2026) | AWS CloudTrail JSON logs; AWS Cloud | Cloud threat detection and CloudTrail-to-ATT&CK mapping at technique/sub-technique level | Two-step RAG using MITRE ATT&CK Cloud, AWS Threat Technique Catalogue and threat reports | Accuracy, precision, recall, Macro-F1, per-event latency (4.1 s) and cost (\$0.00376) on Gemini 2.5 Pro; standalone retriever metrics NOT REPORTED | Fixed retrieval depth; depth ablation NOT REPORTED; qualitative error categories with reporting inconsistency (60% vs 26% gap) | 200 labeled events sampled from 1,724 Stratus Red Team events, with expert annotation | Cloud API telemetry and cloud-specific corpus; no Windows paired views or quantitative upstream Recall@k decomposition |
| CAM-LDS (Landauer et al., 2026) | Linux auditd/syslog/IDS sources; Linux | Zero-shot log interpretation and ranked ATT&CK candidate identification | No RAG (zero-shot prompting only); open reproducible CAM-LDS benchmark dataset | Ranked top-1 (41.8%), top-10 (67.2%) results, hit rates and confidence calibration across 5 LLMs | Top-10 is output prediction ranking, not retrieval depth; no RAG failure decomposition | 7 scenarios, 81 techniques, 13 tactics, 198 attack steps, 18 host/network data sources | Linux multi-source dataset and zero-shot prompting framing, not controlled RAG vs No-RAG Windows attribution |
| TechniqueRAG (Lekssays et al., 2025) | CTI report natural language text; cross-platform | Adversarial technique and sub-technique annotation | Multi-stage RAG over MITRE ATT&CK with off-the-shelf retrieval and zero-shot LLM reranking | End-to-end Macro/Micro F1, precision, recall; standalone retriever Hit@k and Recall@k reported | Candidate-pool ranking analysis; no Windows endpoint telemetry or matched single-LLM protocol | TRAM (~1.5K instances) and RC-Threat (~2.5K segments) across ~600 classes; improves CTI annotation under label scarcity | Unstructured text annotation and generator fine-tuning, not endpoint evidence with frozen no-leakage inference views |
| H-TechniqueRAG (Morbiato et al., 2026) | CTI report natural language text; cross-platform | Technique annotation with tactic-to-technique hierarchy; sub-technique modeling NOT REPORTED | Hierarchical RAG over ATT&CK taxonomy partitioned into tactic and technique collections (Sentence-BERT, FAISS IVF) | Micro F1, precision, recall, MAP@10, latency (820 ms), API call reduction (-60%); standalone technique Recall@k NOT REPORTED | Top-k denotes macro tactic retrieval depth (M=3) and candidate quota (Ka=15); prompt depth ablation over k in {1,3,5,10} NOT REPORTED | 4,450 total CTI texts across three datasets (CTI-RCM, MITRE CTI, TRAM); hierarchical routing cuts search space by 77.5% | Establishes the depth/noise precedent in CTI text, but differs in input modality, taxonomy hierarchy and study design |
| Trace2ATT&CK (Lupinacci et al., 2026) | eBPF kernel telemetry and provenance graphs; Linux | Telemetry-to-ATT&CK mapping with ranked candidates and rationales at technique and sub-technique levels | RAG grounded in ATT&CK (Chroma vector store, mxbai-embed-large-v1, top-5 chunks) plus pure prompting baseline | HR@5, MRR@5, NDCG@5 and empty-output failure rate across 7 open-weights LLMs; standalone retriever metrics NOT REPORTED | HR@5/MRR@5/NDCG@5 represent model output ranking cutoffs, not retriever candidate depth k; retrieval depth is fixed at 5 chunks | 347 Linux Atomic Red Team test executions (~62K raw eBPF events/scenario); compares raw telemetry with graph representations | Linux provenance graphs and local open-weight models, not Windows endpoint pairs or k in {1,3,5,10} retrieval ablation |
| Okuma et al. (2023) | Sysmon logs generated from Atomic Red Team; Windows | Automated Sysmon-to-ATT&CK mapping at technique level | Rule/heuristic correlation; no RAG (pre-LLM methodology) | Detection/accuracy-style evaluation; retrieval and LLM metrics not applicable; detailed itemized metrics NOT REPORTED | No top-k retrieval or generation-failure analysis (not applicable to rule matching) | Atomic Red Team reference executions for Sysmon mapping; exact test and event sample counts NOT REPORTED | Earlier Windows mapping precedent, but non-generative rule matching and not an LLM/RAG controlled comparison |
| LADE (Gwak et al., SecureComm 2026 / 2027; presented 2026, online 2026, copyright 2027) | Chronological shell commands and script traces; host-side traces | Multi-stage APT detection, malicious-snippet localization and ATT&CK TTP mapping | In-context multi-stage prompting plus static ATT&CK domain knowledge; vector retriever/corpus NOT APPLICABLE / NOT REPORTED | Anomaly AUC-ROC, snippet localization precision/recall/F1, Top-1/Top-3/Top-10 technique output accuracy | Top-1/Top-3/Top-10 are output prediction ranking cutoffs; RAG retriever depth ablation NOT APPLICABLE / NOT REPORTED | DARPA Transparent Computing traces and Caldera/AVIATOR APT data (35 attack sequences); multi-stage code/sequence analysis | Long code-sequence APT workflow and in-context reasoning, not event-level Windows endpoint evidence with a matched RAG retriever |

## Closest prior work and replication anchor

The closest setting-specific comparators are Yang & Hsu for Windows Sysmon with
RAG/no-RAG contrast, Adediran et al. for controlled ATT&CK-grounded RAG versus
baseline on cloud telemetry, and Trace2ATT&CK for telemetry-to-ATT&CK mapping
with a RAG/prompting comparison. TechniqueRAG and H-TechniqueRAG are the
closest methodological anchors for retrieval-quality and candidate-depth
analysis, but use CTI text rather than endpoint telemetry.

Accordingly, RAG2ATTCK is framed as a controlled replication-and-extension
study evaluating ATT&CK-grounded RAG for exact technique/sub-technique
attribution from Windows endpoint evidence. The extension is the combination
of:

- same-model, same-prompt RAG versus No-RAG comparison;
- exact technique/sub-technique targets under a pinned ATT&CK v19.2 corpus;
- retrieval-depth evaluation at `k ∈ {1, 3, 5, 10}`;
- explicit separation of `GT not in Top-k` retrieval failures from downstream
  selection/generation failures; and
- paired single-event/contextual-event views with per-view ground truth.

## Research gap and allowed claims

Within this reviewed comparator set, the defensible gap is setting-specific
and compositional. The reviewed works establish that RAG for ATT&CK mapping,
Windows/Sysmon telemetry, controlled RAG/no-RAG comparisons, retrieval
metrics, and candidate-depth analysis each have prior precedent. The report
therefore does not claim any of those components as globally novel in
isolation.

Allowed wording:

> RAG2ATTCK evaluates a controlled replication-and-extension design for exact
> ATT&CK technique/sub-technique attribution from Windows endpoint evidence,
> with matched RAG and No-RAG conditions and an explicit decomposition of
> retrieval success, downstream selection, latency and token trade-offs.

Claims to avoid:

- RAG for ATT&CK is novel.
- Windows logs or Sysmon plus RAG are novel.
- Top-k retrieval or retrieval analysis is globally novel.
- RAG/no-RAG comparison is unprecedented.
- The synthetic benchmark repairs or validates the historical Windows-APT
  ground-truth blocker.

## Evidence appendix

| Work | Primary source checked | Location | Evidence level | Scope note |
|---|---|---|---|---|
| Yang & Hsu | Springer SITAIBA 2025 proceedings, SIST Vol. 433, DOI `https://doi.org/10.1007/978-3-032-24063-7_18` | Chapter pp. 235–251; publisher metadata and table of contents | Bibliographic and chapter-level | The source supports Windows Sysmon, process-tree/RAG framing and matched RAG/no-RAG comparison across 3 LLMs. Exact sample count, embedding model, and formal retriever metrics are `NOT REPORTED`. |
| Adediran et al. | Tech Science Press, *Computers, Materials & Continua*, DOI `https://doi.org/10.32604/cmc.2026.077606` | Abstract p. 1; data acquisition pp. 6–7; evaluation pp. 13 and 16–22 | Direct source | Supports 200 sampled CloudTrail events from 1,724 Stratus Red Team events, 20 simulated techniques, ATT&CK/AWS catalogue/threat-report knowledge sources, and reported LLM metrics. Standalone retriever Recall@k and depth ablation are `NOT REPORTED`. |
| CAM-LDS | Springer, *International Journal of Information Security*, DOI `https://doi.org/10.1007/s10207-026-01318-x`; arXiv: `https://arxiv.org/abs/2603.04186` | Abstract; Sections 3–5; Table 4; conclusion | Direct source | Supports Linux scope, seven scenarios, 81 techniques, 13 tactics, 198 attack steps, 18 sources, open artifacts and zero-shot LLM evaluation. Top-10 represents output candidate ranking, not RAG retrieval depth. |
| TechniqueRAG | ACL Anthology, Findings of ACL 2025, DOI `https://doi.org/10.18653/v1/2025.findings-acl.1076`; arXiv: `https://arxiv.org/abs/2505.11988` | Abstract p. 1; method pp. 3–5; metrics p. 6; datasets pp. 5 and 10 | Direct source | Supports off-the-shelf retrieval, zero-shot LLM reranking, BM25/dense retrieval, TRAM/RC-Threat datasets and ranking Hit@k/Recall@k. Operates on unstructured CTI text rather than host telemetry. |
| H-TechniqueRAG | arXiv:2604.14166, `https://arxiv.org/abs/2604.14166` | Abstract; Sections 1, 3, 4; Tables 1–3 | Direct source | Supports hierarchical two-stage retrieval (M=3 tactics, Ka=15 candidate techniques), 77.5% candidate reduction, 4,450 CTI texts across three datasets, latency/API-call claims and comparison with TechniqueRAG. Standalone technique Recall@k is `NOT REPORTED`. |
| Trace2ATT&CK | arXiv:2609.12841, `https://arxiv.org/abs/2609.12841` | Abstract; Sections 3, 5, 6.4, 7; Appendix A | Direct source | Supports eBPF/provenance graphs compressed into DOT command graphs, pure prompting vs RAG across 7 open-weights LLMs, 347 Linux Atomic Red Team tests, fixed 5-chunk retrieval, and HR@5/MRR@5/NDCG@5 output ranking definitions. Standalone retriever Recall@k is `NOT REPORTED`. |
| Okuma et al. | IEEE ICSPIS 2023, DOI `https://doi.org/10.1109/ICSPIS60075.2023.10343783` | Conference metadata and pages 104–109 | Bibliographic/abstract-level | Supports Windows Sysmon mapping to ATT&CK techniques via Atomic Red Team rule correlation. Non-generative, pre-LLM methodology without RAG; exact sample counts beyond the abstract are `NOT REPORTED`. |
| LADE | SecureComm 2026 proceedings (online 2026, copyright 2027), Springer LNICST, DOI `https://doi.org/10.1007/978-3-032-32767-3_11`; author manuscript `https://www3.cs.stonybrook.edu/~stoller/papers/LADE-2026.pdf` | Proceedings metadata; Sections 1, 3, 4 | Direct source | Supports DARPA Transparent Computing and Caldera/AVIATOR traces (35 attack sequences), code-snippet sequences, multi-stage in-context prompting with static ATT&CK knowledge, Top-1/Top-3/Top-10 output ranking, and anomaly AUC-ROC. Dynamic vector RAG is not implemented. |

## Verified references

1. Yang, D.-R.; Hsu, F.-H. “LLM-Based Malicious Behavior Detection from Sysmon
   Event Logs: A Practical System Integrating Process Trees, RAG, and
   In-Context Analysis.” In: Security and Information Technologies with AI,
   Internet Computing and Big-Data Applications (SITAIBA 2025), Smart
   Innovation, Systems and Technologies, vol. 433, pp. 235–251, Springer Cham,
   published online 2026. DOI: <https://doi.org/10.1007/978-3-032-24063-7_18>.
2. Adediran, G.; Awuson-David, K.; Ahmed, Y. “Retrieval-Augmented Large
   Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail
   Mitre ATT&CK Mapping.” Computers, Materials & Continua, vol. 87, no. 2,
   art. 100, 2026. DOI: <https://doi.org/10.32604/cmc.2026.077606>.
3. Landauer, M.; Hotwagner, W.; Boenke, T.; Skopik, F.; Wurzenberger, M.
   “CAM-LDS: cyber attack manifestations for automatic interpretation of
   system logs and security alerts.” International Journal of Information
   Security, vol. 25, no. 5, art. 148, 2026. DOI:
   <https://doi.org/10.1007/s10207-026-01318-x>; preprint:
   <https://arxiv.org/abs/2603.04186>.
4. Lekssays, A.; Shukla, U.; Sencar, H. T.; Parvez, M. R. “TechniqueRAG:
   Retrieval Augmented Generation for Adversarial Technique Annotation in
   Cyber Threat Intelligence Text.” In: Findings of the Association for
   Computational Linguistics: ACL 2025, pp. 20913–20926, 2025. DOI:
   <https://doi.org/10.18653/v1/2025.findings-acl.1076>; arXiv:
   <https://arxiv.org/abs/2505.11988>.
5. Morbiato, F.; Keller, M.; Nair, P.; Romano, L. “Hierarchical Retrieval
   Augmented Generation for Adversarial Technique Annotation in Cyber Threat
   Intelligence Text.” arXiv:2604.14166, 2026.
   <https://arxiv.org/abs/2604.14166>.
6. Lupinacci, M.; Arena, L.; Blefari, F.; Furfaro, A. “A Graph-Based Approach
   for Mapping Kernel-Level Telemetry to MITRE ATT&CK.” arXiv:2609.12841, 2026.
   <https://arxiv.org/abs/2609.12841>.
7. Okuma, M.; Watarai, K.; Okada, S.; Mitsunaga, T. “Automated Mapping Method
   for Sysmon Logs to ATT&CK Techniques by Leveraging Atomic Red Team.” In: 2023
   6th International Conference on Signal Processing and Information Security
   (ICSPIS 2023), pp. 104–109, IEEE, 2023. DOI:
   <https://doi.org/10.1109/ICSPIS60075.2023.10343783>.
8. Gwak, J.-Y.; Strier, A.; Xi, Z.; Yan, G.; Shu, X.; Stoller, S. D.; Yang, P.
   “LADE: LLM-Assisted Advanced Persistent Threat Detection and Explanation.”
   In: Security and Privacy in Communication Networks (SecureComm 2026),
   Lecture Notes of the Institute for Computer Sciences, Social Informatics and
   Telecommunications Engineering (LNICST), pp. 245–273, Springer Cham,
   published online 2026, copyright 2027. DOI:
   <https://doi.org/10.1007/978-3-032-32767-3_11>; author manuscript:
   <https://www3.cs.stonybrook.edu/~stoller/papers/LADE-2026.pdf>.

## Methodological note

The comparison table is literature positioning, not an experimental result.
T20 must report retrieval-only measurements, T15 remains blocked until
legitimate real data and API access exist, and the frozen synthetic benchmark
must not be regenerated or relabeled as part of T33.
