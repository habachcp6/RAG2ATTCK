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
| Yang & Hsu (2026) | Windows Sysmon; Windows | Malicious-behavior detection and explanation; ATT&CK is contextual rather than the primary exact-ID target | RAG with security templates/attack patterns | Precision, F1 and FPR; retriever metrics NOT REPORTED | Fixed retrieval; no formal retrieval-vs-generation decomposition | Sysmon process-tree reconstruction with RAG and in-context analysis; matched RAG/no-RAG experiments | Binary detection/process-tree focus, not exact technique/sub-technique attribution or retriever Recall@k |
| Adediran et al. (2026) | AWS CloudTrail; AWS Cloud | Threat detection and CloudTrail-to-ATT&CK mapping at technique/sub-technique level | Two-step RAG using MITRE ATT&CK, AWS Threat Technique Catalogue and threat reports | Accuracy, precision, recall, F1, latency and cost; retrieval metrics NOT REPORTED | Fixed k; no systematic retrieval-depth ablation; qualitative error categories | 200 labeled events sampled from 1,724 Stratus Red Team events, with expert annotation | Cloud API telemetry and cloud-specific corpus; no Windows paired views or upstream Recall@k decomposition |
| CAM-LDS (Landauer et al., 2026) | Linux auditd/syslog/IDS sources; Linux | Zero-shot log interpretation and ranked ATT&CK candidate identification | No RAG; open reproducible CAM-LDS dataset | Rank/Hit metrics and an illustrative LLM case study | Top-10 is output ranking, not retrieval depth; no RAG failure decomposition | Seven scenarios, 81 techniques, 18 host/network data sources | Linux multi-source dataset and zero-shot framing, not controlled RAG vs No-RAG Windows attribution |
| TechniqueRAG (Lekssays et al., 2025) | CTI report text; cross-platform | Adversarial technique/sub-technique annotation | RAG over MITRE ATT&CK with off-the-shelf retrieval and LLM reranking | Retrieval Hit@k/Recall@k plus precision/recall/F1-style annotation metrics | Candidate-pool analysis; no Windows endpoint telemetry or matched single-LLM protocol | Multiple CTI benchmarks; improves domain-specific CTI annotation with limited labeled data | Text annotation and generator fine-tuning, not endpoint evidence with frozen no-leakage inference views |
| H-TechniqueRAG (Morbiato et al., 2026) | CTI report text; cross-platform | Technique annotation with tactic-to-technique hierarchy | Hierarchical RAG over ATT&CK taxonomy | F1, latency, API-call reduction and retrieval-space analysis | Explicit depth/context-noise trade-off; not Windows telemetry | Three CTI datasets; hierarchical routing reduces search space and inference cost | Establishes the depth/noise precedent, but differs in text input, hierarchy and study design |
| Trace2ATT&CK (Lupinacci et al., 2026) | eBPF kernel telemetry and provenance graphs; Linux | Telemetry-to-ATT&CK mapping with ranked candidates and rationales | RAG grounded in ATT&CK plus pure prompting baseline | HR@1/3/5, MRR/NDCG and empty-output rate | Output rank cutoffs, not retrieval-depth k; no formal upstream/downstream split | 347 Linux Atomic Red Team tests; compares raw telemetry with graph representations | Linux provenance graphs and local open-weight models, not Windows endpoint pairs or k={1,3,5,10} retrieval ablation |
| Okuma et al. (2023) | Sysmon logs generated from Atomic Red Team; Windows | Automated Sysmon-to-ATT&CK mapping at technique level | Rule/heuristic correlation; no RAG | Detection/accuracy-style evaluation; retrieval and LLM metrics not applicable | No top-k retrieval or generation-failure analysis | Atomic Red Team reference executions for Sysmon mapping | Earlier Windows mapping precedent, but non-generative and not an LLM/RAG controlled comparison |
| LADE (Gwak et al., 2027, SecureComm 2026 proceedings) | Chronological shell commands/scripts; host-side traces | APT detection, malicious-snippet localization and ATT&CK TTP mapping | Prompting plus ATT&CK domain knowledge; no retrieval corpus reported | Accuracy/F1 for detection, precision/recall for localization, MRR/NDCG/Hit Rate for TTP mapping | No RAG-depth ablation; discusses long-context segmentation and summary propagation rather than retriever failure | AVIATOR plus Caldera-derived data; multi-stage code/sequence analysis | Long code-sequence APT workflow, not event-level Windows endpoint evidence with a matched RAG retriever |

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

## Verified references

1. Yang, D.-R.; Hsu, F.-H. “LLM-Based Malicious Behavior Detection from Sysmon
   Event Logs.” DOI: <https://doi.org/10.1007/978-3-032-24063-7_18>.
2. Adediran, G.; Awuson-David, K.; Ahmed, Y. “Retrieval-Augmented Large
   Language Model for AWS Cloud Threat Detection and Modelling: Cloudtrail
   Mitre ATT&CK Mapping.” Computers, Materials & Continua, 2026. DOI:
   <https://doi.org/10.32604/cmc.2026.077606>.
3. Landauer, M.; Hotwagner, W.; Boenke, T.; Skopik, F.; Wurzenberger, M.
   “CAM-LDS: cyber attack manifestations for automatic interpretation of
   system logs and security alerts.” International Journal of Information
   Security, 2026. DOI: <https://doi.org/10.1007/s10207-026-01318-x>.
4. Lekssays, A.; Shukla, U.; Sencar, H. T.; Parvez, M. R. “TechniqueRAG:
   Retrieval Augmented Generation for Adversarial Technique Annotation in
   Cyber Threat Intelligence Text.” Findings of ACL 2025. DOI:
   <https://doi.org/10.18653/v1/2025.findings-acl.1076>; arXiv:
   <https://arxiv.org/abs/2505.11988>.
5. Morbiato, F.; Keller, M.; Nair, P.; Romano, L. “Hierarchical Retrieval
   Augmented Generation for Adversarial Technique Annotation in Cyber Threat
   Intelligence Text.” arXiv:2604.14166. <https://arxiv.org/abs/2604.14166>.
6. Lupinacci, M.; Arena, L.; Blefari, F.; Furfaro, A. “A Graph-Based Approach
   for Mapping Kernel-Level Telemetry to MITRE ATT&CK.” arXiv:2609.12841.
   <https://arxiv.org/abs/2609.12841>.
7. Okuma, M.; Watarai, K.; Okada, S.; Mitsunaga, T. “Automated Mapping Method
   for Sysmon Logs to ATT&CK Techniques by Leveraging Atomic Red Team.” ICSPIS
   2023, pp. 104–109. DOI:
   <https://doi.org/10.1109/ICSPIS60075.2023.10343783>.
8. Gwak, J.-Y.; Strier, A.; Xi, Z.; Yan, G.; Shu, X.; Stoller, S. D.; Yang, P.
   “LADE: LLM-Assisted Advanced Persistent Threat Detection and Explanation.”
   SecureComm 2026 proceedings, published 2027, pp. 245–273. DOI:
   <https://doi.org/10.1007/978-3-032-32767-3_11>; author manuscript:
   <https://www3.cs.stonybrook.edu/~stoller/papers/LADE-2026.pdf>.

## Methodological note

The comparison table is literature positioning, not an experimental result.
T20 must report retrieval-only measurements, T15 remains blocked until
legitimate real data and API access exist, and the frozen synthetic benchmark
must not be regenerated or relabeled as part of T33.
