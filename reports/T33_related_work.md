# T33 — Related Work and Research Gap

## Scope and evidence policy

Audit date: 2026-09-22. **T33_STATUS: BLOCKED**. Full-text content checks:
**6/8** (Adediran, CAM-LDS journal version, TechniqueRAG ACL version,
H-TechniqueRAG, Trace2ATT&CK, and LADE author manuscript). Yang & Hsu is
abstract/metadata-only; Okuma lacks accessible primary full text. CI and
mergeability do not resolve these source-access blockers.

Claims below are bounded to the source/version and locations in the evidence
appendix. `NOT REPORTED` means absent from the inspected source;
`UNVERIFIED (full text unavailable)` is not a claim that the paper omits a field.
`NOT APPLICABLE` is used only where the inspected method makes a field inapplicable.
Older T02 extraction notes are historical leads, not independent evidence.

## Comparison matrix

| Work | Input / platform | Task and ATT&CK granularity | RAG and corpus | Retrieval / LLM evaluation | Top-k / failure analysis | Dataset and main contribution | Difference from RAG2ATTCK |
|---|---|---|---|---|---|---|---|
| Yang & Hsu (2026; SITAIBA 2025) | Windows Sysmon process trees | Malicious-behavior detection, explanations and mitigation; exact ATT&CK output contract UNVERIFIED | RAG and semantic matching; detailed corpus, embedding and database UNVERIFIED | Abstract reports precision, F1 and FPR for Mistral-7B, phi-2 and TinyLlama-1.1B, with/without RAG | Retriever depth, independent retrieval metrics and decomposition UNVERIFIED (full text unavailable) | Attack samples and simulated benign process trees; sample counts UNVERIFIED | Windows/RAG comparator; detailed exact-ID contrast remains provisional |
| Adediran et al. (2026) | AWS CloudTrail JSON; AWS | Threat detection and technique/sub-technique mapping | Two-step RAG; MITRE Cloud, AWS catalogue and threat reports; text-multilingual-embedding-002 and Vertex AI RAG Vector Database | Accuracy, precision, recall, F1, latency and cost; Gemini 2.5 Pro | Numeric retrieval depth and standalone retriever metrics NOT REPORTED; generation can fail despite relevant retrieved context | 200 events (122 malicious/78 benign) sampled from 1,724; 20 emulations, while abstract reports nine mapped techniques | Cloud telemetry; source inconsistently reports retrieval-generation gaps as 60% and 26% |
| CAM-LDS (Landauer et al., journal 2026) | Linux host/network logs and IDS alerts | Ranked technique predictions; evaluation collapses sub-techniques to parents | Zero-shot, no retrieval; retrieval settings NOT APPLICABLE | Five models, five sampled runs; GPT-5.5 Top-1 41.8%, Top-10 67.2%; output P@k, Recall@k and MRR | k is model-output cutoff, not retriever depth | Seven scenarios, 81 techniques, 13 tactics, 198 log-producing steps, 18 sources | Published version extends the one-model arXiv v1 evaluation; not a RAG ablation |
| TechniqueRAG (Lekssays et al., ACL 2025) | CTI text; platform-independent input | Single/multi-label technique and sub-technique annotation | BM25 retrieves annotated text-label pairs, K=40; DeepSeek v3 reranks; k=3 exemplars augment a fine-tuned Ministral generator | End-to-end P/R/F1; separate ranking P/R/F1 at k={1,3}; standalone Hit@k NOT REPORTED | K is initial pool, k is retained exemplars; ranking cutoff is a distinct evaluation choice | Tram, Procedures, Expert; appendix Tables 5/6 give differing split/total counts, not RC-Threat | Exemplar retrieval and generator fine-tuning, rather than only ATT&CK-description retrieval |
| H-TechniqueRAG (Morbiato et al., 2026 preprint) | CTI text | Tactic-to-technique hierarchy; implemented sub-technique modeling NOT REPORTED | all-MiniLM-L6-v2, 384 dimensions, FAISS IVF; Llama-3-8B-Instruct | Micro P/R/F1, MAP@10, tactic accuracy, latency/API calls | M=3 tactics; up to 15 techniques per tactic (at most 45); tactic-depth analysis differs from prompt k={1,3,5,10} | 1,200 CTI-RCM + 2,800 MITRE CTI + 450 TRAM texts; reported 820 ms and 60% fewer calls | Hierarchical CTI retrieval; standalone technique Recall@k NOT REPORTED |
| Trace2ATT&CK (Lupinacci et al., 2026 preprint) | Linux eBPF telemetry/provenance graphs | Technique and exact sub-technique ranked mapping | Chroma, mxbai-embed-large-v1, 800-word chunks; MMR returns five chunks, fetch_k=20 | Seven local models; HR@5/MRR@5/NDCG@5 on valid mappings, invalid outputs separately | Output cutoff 5 and retrieval depth 5 have separate definitions; standalone retriever Recall@k NOT REPORTED | 347 Linux Atomic Red Team tests; raw-log/graph and prompting/RAG comparisons | Linux graph input and fixed-depth retrieval, not Windows paired-view depth ablation |
| Okuma et al. (2023) | Sysmon logs (title-level evidence) | ATT&CK technique mapping (title-level evidence) | Architecture, RAG/non-RAG classification, embedding/database UNVERIFIED | Exact metrics UNVERIFIED (primary full text unavailable) | UNVERIFIED | Atomic Red Team (title); exact sample counts UNVERIFIED | Bibliographic comparator only until primary method/evaluation text is obtained |
| LADE (Gwak et al.; SecureComm 2026, online 2026, copyright 2027) | Chronological command/script snippets, including Sysmon and PowerShell logs | APT detection, snippet localization and ranked TTP mapping | Rubric prompting with optional ATT&CK descriptions/summaries; dynamic vector retriever NOT APPLICABLE | Detection F1/accuracy; localization P/R; mapping HR/MRR/NDCG at 3 and 10 | k is output-list length, not retriever depth | AVIATOR: 35 attack/32 benign sequences; Caldera-derived controlled sets; DARPA TC discussed as unsuitable, not evaluated data | Sequence-level code analysis and knowledge augmentation |

## Closest prior work and replication anchor

The closest setting-specific comparators are Yang & Hsu for Windows Sysmon with
RAG/no-RAG contrast, Adediran et al. for controlled ATT&CK-grounded RAG versus
baseline on cloud telemetry, and Trace2ATT&CK for telemetry-to-ATT&CK mapping
with a RAG/prompting comparison. TechniqueRAG and H-TechniqueRAG are the
methodological anchors for exemplar ranking and hierarchical candidate selection,
but use CTI text rather than endpoint telemetry.

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
| Yang & Hsu | [Publisher chapter](https://link.springer.com/chapter/10.1007/978-3-032-24063-7_18) | Abstract and bibliographic metadata; pp. 235–251 | PARTIAL | Full chapter is subscription-only. Sample counts and detailed retrieval/scoring claims remain UNVERIFIED; remove unsupported fixed-depth assertions. Publisher currently identifies SIST vol. 8767. |
| Adediran | [Publisher full text](https://www.techscience.com/cmc/v87n2/66657/html) | Abstract; Sections 4.2–4.5, 6.4 | FULL TEXT CHECKED | Distinguish emulations from mapped techniques, and retrieval availability from generator selection. Sections 2 and 6.4 disagree on gap percentage. Numeric k is NOT REPORTED. |
| CAM-LDS | [Journal version](https://link.springer.com/article/10.1007/s10207-026-01318-x) | Sections 5.1–5.2, Fig. 25; published 26 August 2026 | FULL TEXT CHECKED | Five models and five runs belong to this version. [arXiv v1](https://arxiv.org/html/2603.04186v1) instead uses one model; do not mix versions. |
| TechniqueRAG | [ACL proceedings PDF](https://aclanthology.org/2025.findings-acl.1076.pdf) | Sections 3.1–3.2, 4.1–4.2; Appendix B, Tables 5–6 | FULL TEXT CHECKED | Paired examples form the corpus. Correct prior RC-Threat and Hit@k claims. Counts in appendix tables differ; do not present one silently reconciled sample total. |
| H-TechniqueRAG | [Versioned preprint](https://arxiv.org/html/2604.14166v1) | Sections 3.3, 4.1–4.4; Tables 1–3 | FULL TEXT CHECKED | Separate tactic depth, per-tactic quota and MAP cutoff. Sub-technique modeling appears as a possible improvement, not an established evaluated component. |
| Trace2ATT&CK | [Versioned preprint](https://arxiv.org/html/2609.12841v1) | Sections 6.4, 7; Appendix A | FULL TEXT CHECKED | Distinguish MMR fetch pool 20, retrieved chunks 5 and output cutoff 5. Section 7 excludes unparsable outputs from ranking denominators. |
| Okuma | [IEEE record](https://ieeexplore.ieee.org/document/10343783); [conference author index](https://edas.info/web/icspis2023/authors.html) | ICSPIS 2023 bibliographic entry, pp. 104–109 | PARTIAL / ACCESS BLOCKED | IEEE content unavailable in this audit; conference metadata does not establish methods, counts or metrics. Do not infer non-RAG from publication year. |
| LADE | [Author manuscript](https://www3.cs.stonybrook.edu/~stoller/papers/LADE-2026.pdf); [publisher](https://link.springer.com/chapter/10.1007/978-3-032-32767-3_11) | Sections 4, 5.1–5.4; pp. 12–16; publisher metadata | FULL TEXT CHECKED | Replace DARPA dataset and AUC/Top-1 claims with the actual datasets and metrics above. Publisher online date: 20 July 2026; copyright: 2027. |

## Audit corrections and remaining blockers

- Corrected TechniqueRAG corpus, datasets, K/k roles and ranking metrics.
- Corrected LADE evaluated datasets, counts, task metrics and output cutoffs.
- Bound CAM-LDS claims to the journal version; its five-model statement is supported.
- Added Adediran embedding/vector store and separated generated from evaluated data.
- Removed claims of complete source verification based only on metadata or abstracts.
- **HUMAN_ACTION:** obtain lawful full-text access for Yang & Hsu and Okuma, then
  complete the content audit before declaring T33 merge-ready. No source purchase
  or contact with authors has been initiated.
- T02 notes were not edited because they are outside this documentation-only scope.
  Their superseded comparator claims must not override this source-bounded audit.

## References and source identities

1. Yang, D.-R.; Hsu, F.-H. “LLM-Based Malicious Behavior Detection from Sysmon
   Event Logs: A Practical System Integrating Process Trees, RAG, and
   In-Context Analysis.” In: Security and Information Technologies with AI,
   Internet Computing and Big-Data Applications (SITAIBA 2025), Smart
   Innovation, Systems and Technologies, vol. 8767, pp. 235–251, Springer Cham,
   published online 2026. DOI: <https://doi.org/10.1007/978-3-032-24063-7_18>.
2. Adediran, G.; Awuson-David, K.; Ahmed, Y. “Retrieval-Augmented Large
   Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail
   Mitre ATT&CK Mapping.” Computers, Materials & Continua, vol. 87, no. 2,
   art. 100, 2026. DOI: <https://doi.org/10.32604/cmc.2026.077606>.
3. Landauer, M.; Hotwagner, W.; Boenke, T.; Skopik, F.; Wurzenberger, M.
   “CAM-LDS: cyber attack manifestations for automatic interpretation of
   system logs and security alerts.” International Journal of Information
   Security, vol. 25, art. 148, 2026. DOI:
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
