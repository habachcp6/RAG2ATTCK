# Phase S2: Presentation Deck & Sanitized Reproducibility Plan

**Subagent Role:** Lead D (Reproducibility & Presentation Lead for Phase S2)  
**Dedicated Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
**Target Branch:** `codex/s1-reproducibility-presentation` (PR #26)  
**Execution Timestamp (UTC):** 2026-10-02T01:25:00Z (Local: 2026-10-02T08:25:00+07:00)  
**PRE_SHA:** `ebe83519b67f8e07ee255164ec3b39f29cf5abcc`  
**Document Classification:** STRICTLY PLAN-ONLY (Preparation Repair Bounded - Aligned to `fixture_export_schema_b172.json`)  
**Status:** PENDING CODEX REVIEW (Do NOT treat as final approved for S2 execution)  

---

## 1. Executive Summary & Remediation Context

During Phase S1, Subagent D established the offline reproduction infrastructure, frozen protocol cryptographic bindings (15 canonical artifacts under `canonical-lock-v1`), fail-closed execution-mode boundary enforcement (`execution_mode == 'live'`), and a 12-slide bilingual presentation scaffold. In Phase S1, all end-to-end evaluation slides for the full 1,280-sample test matrix (6,400 records) were strictly marked with the `[PENDING EXECUTION]` provenance badge, reflecting ongoing background execution under live runner PID 50192.

Following feedback from the Codex Reviewer, this document provides a comprehensive, rigorous realignment of the Phase S2 plan to 100% match the canonical JSON export schema established in `fixture_export_schema_b172.json` (produced by `scripts/analysis/evaluate_rqs.py` at commit `b17276f`):
1. **Explicit Review Status:** Label is strictly designated as `PENDING CODEX REVIEW`. Self-approval is strictly forbidden (the plan remains pending Codex supervisor review and cannot be executed until approved).
2. **100% JSON Pointer Alignment to `fixture_export_schema_b172.json`:**
   - **Slide 6 (Dataset & Views):** Manifest path `data/ground_truth/synthetic/split_manifest.json`, 718 scorable views, 278 complete scorable pairs (440 distinct eligible clusters across 718 views).
   - **Slide 7 (RQ1 Attribution):** Pointers to `/rq1/by_condition/{c}/accuracy_end_to_end`, `/rq1/by_condition/{c}/macro_f1`, `/rq1/by_condition/{c}/accuracy_e2e_ci_95`.
   - **Slide 8 (RQ2 Error Decomposition):** Pointers from `/rq2/by_condition/{c}/...` (retrieval metrics, generation conditional accuracies, independent failure axes, and overlaps).
   - **Slide 9 (RQ3 Tradeoffs & Costs):**
     * Latency: `/rq3/tradeoffs_by_condition/{c}/latency_ms/median` (ms to s: divide by 1000)
     * Tokens: `/rq3/tradeoffs_by_condition/{c}/tokens/mean_prompt_tokens`
     * Cost: `/rq3/tradeoffs_by_condition/{c}/financial_cost_usd/cost_per_logical_request_usd`
     * Whole-study: `/rq3/whole_study_accounting/{total_study_budget_usd, canonical_conditions_total_usd, net_remaining_uncommitted_budget_usd}`
   - **Slide 10 (View Diagnostics & Paired Analysis):** Pointers from `/rq3/view_diagnostics/{c}/...` covering `single_view_accuracy_e2e`, `contextual_view_accuracy_e2e`, `view_accuracy_delta`, `single_paired_accuracy`, `contextual_paired_accuracy`, `paired_delta`, and `mcnemar_test_views_exploratory/p_value_asymptotic` (and exact).
   - **Slide 11 (Architecture & Reproducibility):** Frozen embedding model specification `all-MiniLM-L6-v2` (384 dimensions, revision `1110a24`, FAISS `IndexFlatIP`).

### Core Scientific & Engineering Invariants:
1. **Strictly Zero Mock Findings as Canonical:** Synthetic fixture diagnostics (`outputs/reproduction/fixture_diagnostics/`) remain strictly labeled with `fixture_only=True` (`sample_count=5`, `completed_records=35`, `overall_accuracy=0.5`). Canonical results require the full 1,280 samples x 5 conditions = 6,400 live-provider records.
2. **Native Evaluator Artifact Contract (Full Specialist B Alignment):** The canonical evaluator (`src/evaluation/experiment_metrics.py`) produces exactly 6 native output artifacts in `outputs/canonical_evaluation/`:
   - `overall_metrics.json`
   - `per_condition_metrics.json`
   - `per_technique_metrics.json`
   - `retrieval_conditional_metrics.json`
   - `failure_decomposition.json`
   - `run_provenance.json`  
   *(Notice: The native evaluator exports strictly these 6 files. There are NO `evaluation_summary.json` or `condition_metrics.json` files).*
3. **Secondary Research Analysis Contract:** Post-hoc paired metrics across scenario representations, Pareto trade-off curves, and diagnostic representations are compiled into a dedicated secondary analysis bundle: `outputs/canonical_analysis/rq_analysis.json` conforming to `fixture_export_schema_b172.json`.
4. **Authoritative Pricing Tariffs & Configuration:** All pricing tariffs and budget parameters are bound directly to `config/pricing_v1.json`, NOT `experiment_config.json`:
   - Runtime model: `gpt-5.6-luna` with `reasoning_effort: xhigh`, service tier `default`.
   - Standard short-context tariffs:
     * Input token tariff: **$0.20 USD / 1M tokens** (`input_per_million`)
     * Cached input read tariff: **$0.02 USD / 1M tokens** (`cache_read_per_million`)
     * Cached input write tariff: **$0.25 USD / 1M tokens** (`cache_write_per_million`)
     * Output & reasoning token tariff: **$1.20 USD / 1M tokens** (`output_per_million`)
   - Budget constraints: Pinned hard cap of **$19.99 USD** (`total_study_budget_usd`), conservative provisional hold of **$0.05264010 USD** (`prior_pilot_provisional_hold_usd`), and net starting available budget of **$19.93735990 USD** (`net_available_starting_budget_usd`).
5. **Frozen Retrieval Pipeline Specification:** In accordance with `config/retrieval.json`:
   - Embedding Model ID: `sentence-transformers/all-MiniLM-L6-v2` (short form: `all-MiniLM-L6-v2`)
   - Embedding Model Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (short ref: `1110a24`)
   - Embedding Vector Dimension: `384`
   - Local Index: FAISS `IndexFlatIP` (Cosine similarity via L2 unit vector normalization)
   *(Eliminate all references to obsolete or non-frozen external embedding models such as `text-embedding-3-large`).*
6. **Pydantic Schema Realities:**
   - Prediction payload schema: `TechniquePrediction` in `src/llm/schemas.py` (`technique_id: str`, `extra="forbid"`, `frozen=True`).
   - Execution record schema: `ExperimentRecord` in `src/experiment/schemas.py`.
   - The obsolete identifier `TechniqueAttributionResponse` is permanently removed.
7. **Precise Financial & Telemetry Accounting:**
   - The live runner's native `run_summary.json` contains solely execution status telemetry: `{"complete": ..., "consumed_provider_attempts": ..., "execution_mode": "live", "new_records": ..., "record_count": ..., "requests_consumed": ..., "run_id": ...}`.
   - Financial spend, token totals, latency distributions, and retry counts are aggregated directly from the request journal (`request_journal.jsonl`) receipts and prediction records, reconciled via `StudyBudgetLedger`.
   - Accounted USD cost is an estimated figure computed from token usage and tariffs in `config/pricing_v1.json`, NOT an OpenAI provider invoice (`billing_invoice_queried: false`).
   - Logical per-record latency (`latency_ms` inside records) is rigorously separated from total execution wall time (`wall_time`).
   - Outcomes are evaluated post-hoc across the 7 mutually exclusive parse statuses in `ParseStatus` (`VALID`, `INVALID_ID`, `MALFORMED_RESPONSE`, `REFUSAL`, `INCOMPLETE`, `API_FAILURE`, `TIMEOUT`).
8. **Strict Separation of Dataset Scoping & Provenance Tiers:**
   - **Canonical TEST Study:** 1,280 views (640 pairs) in `test` split. Over 5 conditions = 6,400 attempts. Positive scorable views in TEST: 718.
   - **T20 Retrieval Diagnostics:** Evaluated across the full Stage B synthetic corpus of 1,340 views (1,280 TEST views + 60 DEV views). Among these 1,340 views, there are 756 positive views with scorable ground truth. Top-10 Hit@10 across these 756 views is 45.11% (341/756), giving an absent/miss rate of 54.89% (415/756). This is a full-benchmark diagnostic, distinct from the TEST split alone.
   - **Real-Provider DEV Cost Pilot:** 4 selected views (2 pairs, both single and contextual) across 5 conditions = 20 attempts on `dev` split. Total tokens observed: 42,213 input, 13,139 output. Estimated cost: $0.0242094 standard / $0.02632005 conservative.
   - **Evaluator Unit Test Fixtures (`outputs/reproduction/fixture_diagnostics/`):** 5 samples, 35 completed records, overall accuracy 0.5 under `_fixture_metadata.json` for offline mathematical validation only.
9. **Neutral Tone & Elimination of Speculative/Causal Claims:**
   - All claims of psychological/cognitive LLM disruption ("nhồi nhét gây nhiễu", "gây hại reasoning", "tri thức nội tại") are eliminated.
   - Metric differences and deltas are reported strictly in percentage points (`pp`), never percent (`%`).
10. **Documented `@oai/artifact-tool` JavaScript Workflow:**
    - PPTX modifications use the verified JavaScript APIs (`importPptx`, `inspect`, `resolve`, `exportPptx`) documented in `@oai/artifact-tool`.
    - Editing operations run on reference staging copies to verify visual fidelity before updating production files. The resulting `.pptx` remains fully openable, editable, and free of clipping.
11. **Journal Integrity & Offline Reproduction Decoupling:**
    - The native JSONL event stream in `request_journal.jsonl` is preserved with byte-level fidelity.
    - All verification runs under `scripts/run_offline_tests.py` with fail-closed socket guards (`attempted_egress=0`).

---

## 2. Canonical Slide Deck Mappings & JSON Pointers (Aligned to `fixture_export_schema_b172.json`)

Once authoritative evaluation on the completed live run directory produces the canonical metric bundle (strictly the 6 native JSON artifacts in `outputs/canonical_evaluation/` and secondary analysis in `outputs/canonical_analysis/rq_analysis.json`), the Vietnamese presentation deck (`docs/presentation/slides.md` and `docs/presentation/slides.pptx`) will be updated by replacing placeholder tokens with verified empirical values.

---

### 2.1 Slide 6: Tập Dữ Liệu & Phân Rã Biểu Diễn (Dataset & Views - Split Manifest & Cluster Topology)

*Objective:* Present the empirical dataset topology, split manifest verification, and exact cluster distribution across the TEST split.

| Placeholder Key | Source Path / Extraction Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_MANIFEST_PATH}}` | `data/ground_truth/synthetic/split_manifest.json` | Frozen split manifest path defining DEV (30 pairs) and TEST (640 pairs). |
| `{{S2_TOTAL_TEST_VIEWS}}` | `split_manifest.json -> len(test) * 2` | Total empirical views in TEST split (Must equal exactly `1,280`). |
| `{{S2_SCORABLE_VIEWS}}` | Count of TEST views where `label_status == 'mapped'` and `technique_ids != []` | Total positive scorable views in TEST split (Must equal exactly `718`). |
| `{{S2_COMPLETE_SCORABLE_PAIRS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `278` complete scorable pairs (both single and contextual have valid mapped GT). |
| `{{S2_CONTEXTUAL_ONLY_PAIRS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `162` pairs where only the contextual view has valid mapped GT. |
| `{{S2_NEITHER_MAPPED_PAIRS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `200` pairs where neither view has mapped GT (`278 + 162 + 200 = 640`). |
| `{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `440` distinct eligible clusters (scenario pairs) across the 718 scorable views (`278 + 162 = 440`). |

#### Target Content Outline (Slide 6):
- **Phân Bổ Kịch Bản & Cụm Đối Chứng (Split Manifest Topology):**
  - Tệp kê khai phân chia dữ liệu đóng băng: `data/ground_truth/synthetic/split_manifest.json`.
  - Quy mô tập TEST: 640 cặp kịch bản đối ứng = 1,280 views độc lập.
  - Phân bố nhãn kiểm chuẩn (Ground-Truth Status):
    * Số lượng views có nhãn dương tính tính điểm được (Scorable Views): **718 views**.
    * Số cặp kịch bản hoàn chỉnh (Complete Scorable Pairs): **278 cặp** (cả Single và Contextual view đều có nhãn xác thực hợp lệ).
    * Số cặp kịch bản chỉ có góc nhìn ngữ cảnh (Contextual-Only Pairs): **162 cặp**.
    * Số cặp kịch bản không tính điểm (Neither Mapped Pairs - Ambiguous/Unmapped): **200 cặp**.
    * Số cụm kịch bản hợp lệ tham gia đánh giá (Distinct Eligible Clusters): **440 cụm** trên toàn bộ 718 views (`278 * 2 + 162 = 718`).
- **Ý Nghĩa Phương Pháp Luận Về Phân Tách Cụm:**
  - Ngăn ngừa hiện tượng ngụy biện gộp mẫu: 718 views scorable bắt nguồn từ 440 cụm kịch bản khác nhau, trong đó 278 cụm có tính chất đối ứng kép.

#### Speaker Notes Update (Slide 6):
> "GHI CHÚ DIỄN GIẢ (Slide 6):  
> Tại Slide 6, cấu trúc tập dữ liệu kiểm chuẩn TEST được công khai minh bạch dựa trên tệp split manifest tại `data/ground_truth/synthetic/split_manifest.json`. Trong tổng số 640 cặp kịch bản (1,280 views), nghiên cứu ghi nhận 718 views có nhãn dương tính đạt chuẩn tính điểm (scorable). Về mặt cấu trúc cụm, 718 views này phân bố trên 440 cụm kịch bản hợp lệ (distinct eligible clusters): bao gồm 278 cặp kịch bản hoàn chỉnh có đủ nhãn ở cả hai góc nhìn (chiếm 556 views) và 162 cặp kịch bản chỉ có góc nhìn contextual đạt chuẩn (chiếm 162 views). 200 cặp còn lại thuộc diện nhãn mơ hồ hoặc unmapped được loại trừ khỏi mẫu số tính điểm theo đúng quyết định D2b-c của giao thức."

---

### 2.2 Slide 7: Kết Quả RQ1 - Định Danh Kỹ Thuật (RQ1 Attribution Performance)

*Objective:* Populate official Macro-F1 across the 474-class universe, End-to-End Accuracy scores, and 95% bootstrap confidence intervals across all 5 conditions from `outputs/canonical_analysis/rq_analysis.json` and `outputs/canonical_evaluation/`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_ACC_E2E_NO_RAG}}` | `/rq1/by_condition/no_rag/accuracy_end_to_end` | End-to-end attribution accuracy for baseline zero-shot condition ($k=0$). |
| `{{S2_ACC_E2E_RAG_K1}}` | `/rq1/by_condition/rag_k1/accuracy_end_to_end` | End-to-end attribution accuracy for RAG depth $k=1$. |
| `{{S2_ACC_E2E_RAG_K3}}` | `/rq1/by_condition/rag_k3/accuracy_end_to_end` | End-to-end attribution accuracy for RAG depth $k=3$. |
| `{{S2_ACC_E2E_RAG_K5}}` | `/rq1/by_condition/rag_k5/accuracy_end_to_end` | End-to-end attribution accuracy for RAG depth $k=5$. |
| `{{S2_ACC_E2E_RAG_K10}}`| `/rq1/by_condition/rag_k10/accuracy_end_to_end`| End-to-end attribution accuracy for RAG depth $k=10$. |
| `{{S2_MACRO_F1_NO_RAG}}` | `/rq1/by_condition/no_rag/macro_f1` | Macro-F1 across 474-class universe for baseline ($k=0$). |
| `{{S2_MACRO_F1_RAG_K1}}` | `/rq1/by_condition/rag_k1/macro_f1` | Macro-F1 for RAG depth $k=1$. |
| `{{S2_MACRO_F1_RAG_K3}}` | `/rq1/by_condition/rag_k3/macro_f1` | Macro-F1 for RAG depth $k=3$. |
| `{{S2_MACRO_F1_RAG_K5}}` | `/rq1/by_condition/rag_k5/macro_f1` | Macro-F1 for RAG depth $k=5$. |
| `{{S2_MACRO_F1_RAG_K10}}`| `/rq1/by_condition/rag_k10/macro_f1`| Macro-F1 for RAG depth $k=10$. |
| `{{S2_CI_95_NO_RAG}}` | `/rq1/by_condition/no_rag/accuracy_e2e_ci_95` | 95% bootstrap confidence interval `[lower, upper]` for baseline. |
| `{{S2_CI_95_RAG_K1}}` | `/rq1/by_condition/rag_k1/accuracy_e2e_ci_95` | 95% bootstrap confidence interval `[lower, upper]` for $k=1$. |
| `{{S2_CI_95_RAG_K3}}` | `/rq1/by_condition/rag_k3/accuracy_e2e_ci_95` | 95% bootstrap confidence interval `[lower, upper]` for $k=3$. |
| `{{S2_CI_95_RAG_K5}}` | `/rq1/by_condition/rag_k5/accuracy_e2e_ci_95` | 95% bootstrap confidence interval `[lower, upper]` for $k=5$. |
| `{{S2_CI_95_RAG_K10}}` | `/rq1/by_condition/rag_k10/accuracy_e2e_ci_95` | 95% bootstrap confidence interval `[lower, upper]` for $k=10$. |
| `{{S2_BEST_RAG_CONDITION}}` | `/rq1/best_rag_condition` | The best performing RAG condition by accuracy. |
| `{{S2_BEST_RAG_ACC_DELTA}}` | `/rq1/best_rag_accuracy_delta` | Net accuracy gain of best RAG condition vs baseline No-RAG. |
| `{{S2_BEST_RAG_F1_DELTA}}` | `/rq1/best_rag_macro_f1_delta` | Net Macro-F1 delta of best RAG condition vs baseline No-RAG. |

#### Target Content Outline (Slide 7):
- **Bảng Hiệu Năng RQ1 Trên 718 Positive Scorable Views (TEST Split):**
  | Điều kiện | Candidate Depth $k$ | End-to-End Accuracy (`accuracy_end_to_end`) | 95% Bootstrap CI (`accuracy_e2e_ci_95`) | Macro-F1 (474 Classes) (`macro_f1`) |
  | :--- | :---: | :---: | :---: | :---: |
  | `no_rag` | 0 | `{{S2_ACC_E2E_NO_RAG}}` | `{{S2_CI_95_NO_RAG}}` | `{{S2_MACRO_F1_NO_RAG}}` |
  | `rag_k1` | 1 | `{{S2_ACC_E2E_RAG_K1}}` | `{{S2_CI_95_RAG_K1}}` | `{{S2_MACRO_F1_RAG_K1}}` |
  | `rag_k3` | 3 | `{{S2_ACC_E2E_RAG_K3}}` | `{{S2_CI_95_RAG_K3}}` | `{{S2_MACRO_F1_RAG_K3}}` |
  | `rag_k5` | 5 | `{{S2_ACC_E2E_RAG_K5}}` | `{{S2_CI_95_RAG_K5}}` | `{{S2_MACRO_F1_RAG_K5}}` |
  | `rag_k10`| 10 | `{{S2_ACC_E2E_RAG_K10}}`| `{{S2_CI_95_RAG_K10}}`| `{{S2_MACRO_F1_RAG_K10}}`|
- **Tổng Kết RQ1:**
  - Điều kiện RAG tối ưu nhất: `{{S2_BEST_RAG_CONDITION}}` với mức tăng độ chính xác `{{S2_BEST_RAG_ACC_DELTA}}` và thay đổi Macro-F1 `{{S2_BEST_RAG_F1_DELTA}}`.
  - Toàn bộ khoảng tin cậy 95% được ước lượng qua phương pháp pair-cluster bootstrap resampling (1,000 resamples), bảo toàn tương quan giữa các góc nhìn trong cùng một kịch bản.

#### Speaker Notes Update (Slide 7):
> "GHI CHÚ DIỄN GIẢ (Slide 7):  
> Kết quả đo lường RQ1 trên 718 views scorable của tập TEST phản ánh định lượng hiệu quả định danh kỹ thuật tấn công của gpt-5.6-luna qua các độ sâu truy xuất. Độ chính xác end-to-end tăng từ {{S2_ACC_E2E_NO_RAG}} ở nhánh cơ sở no_rag lên {{S2_ACC_E2E_RAG_K10}} ở nhánh rag_k10, với điểm số cao nhất ghi nhận tại điều kiện {{S2_BEST_RAG_CONDITION}} (chênh lệch {{S2_BEST_RAG_ACC_DELTA}} so với no_rag). Khoảng tin cậy 95% bootstrap được tính toán theo phương pháp pair-cluster nhằm kiểm soát hiện tượng phụ thuộc dữ liệu giữa các views cùng cặp. Chỉ số Macro-F1 được đánh giá nghiêm ngặt trên toàn bộ không gian 474 kỹ thuật ATT&CK v19.2 đóng băng theo định đề D2d."

---

### 2.3 Slide 8: Kết Quả RQ2 - Phân Rã Lỗi Độc Lập D2i & Đánh Giá Có Điều Kiện (RQ2 Error Decomposition)

*Objective:* Populate the 5 independent failure axes, overlap counts, and retrieval-conditional accuracies from `/rq2/by_condition/{c}/...` in `outputs/canonical_analysis/rq_analysis.json`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_RECALL_AT_K}}` | `/rq2/by_condition/rag_k10/retrieval_metrics/macro_recall` | Macro-average recall across scorable queries at $k=10$. |
| `{{S2_HIT_RATE_AT_K}}` | `/rq2/by_condition/rag_k10/retrieval_metrics/retrieval_hit_rate` | Retrieval Hit@10 rate on TEST scorable queries. |
| `{{S2_RETRIEVAL_MISS_RATE_K10}}` | `/rq2/by_condition/rag_k10/independent_failure_axes/retrieval_miss_rate` | Axis 1: Retrieval miss rate (1 - Hit@10). |
| `{{S2_PROVIDER_FAIL_RATE_K10}}` | `/rq2/by_condition/rag_k10/independent_failure_axes/provider_failure_rate` | Axis 2: Provider failure / API timeout rate. |
| `{{S2_PARSE_FAIL_RATE_K10}}` | `/rq2/by_condition/rag_k10/independent_failure_axes/parse_failure_rate` | Axis 3: JSON schema parsing failure rate. |
| `{{S2_INVALID_ATTACK_ID_RATE_K10}}`| `/rq2/by_condition/rag_k10/independent_failure_axes/invalid_attack_id_rate` | Axis 4: Invalid ATT&CK ID rate (regex or catalog invalid). |
| `{{S2_WRONG_CLASS_RATE_K10}}` | `/rq2/by_condition/rag_k10/independent_failure_axes/valid_but_wrong_classification_rate` | Axis 5: Valid ATT&CK ID but wrong technique attribution rate. |
| `{{S2_OVERLAP_MISS_AND_WRONG_K10}}`| `/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_wrong_classification` | Raw count: retrieval missed AND classification wrong. |
| `{{S2_OVERLAP_MISS_AND_PROV_K10}}` | `/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_provider_failure` | Raw count: retrieval missed AND provider failed. |
| `{{S2_OVERLAP_MISS_AND_PARSE_K10}}`| `/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_parse_failure` | Raw count: retrieval missed AND parse failed. |
| `{{S2_OVERLAP_MISS_AND_INVAL_K10}}`| `/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_invalid_id` | Raw count: retrieval missed AND invalid ATT&CK ID generated. |
| `{{S2_P_CORRECT_GIVEN_RETRIEVED}}`| `/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_success` | Downstream accuracy given ground truth is present in Top-k. |
| `{{S2_P_CORRECT_GIVEN_ABSENT}}` | `/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_failure` | Correct attribution despite GT absent from retrieved Top-k. |

#### Target Content Outline (Slide 8):
- **Phân Rã 5 Trục Thất Bại Độc Lập D2i ($k=10$):**
  - **Trục 1 (Retrieval Miss):** `{{S2_RETRIEVAL_MISS_RATE_K10}}` (kỹ thuật đúng vắng mặt trong Top-10 ứng viên được truy xuất).
  - **Trục 2 (Provider Failure):** `{{S2_PROVIDER_FAIL_RATE_K10}}` (lỗi kết nối, refusal hoặc timeout nhà cung cấp).
  - **Trục 3 (Parse Failure):** `{{S2_PARSE_FAIL_RATE_K10}}` (lỗi giải mã cấu trúc JSON từ đầu ra mô hình).
  - **Trục 4 (Invalid ATT&CK ID):** `{{S2_INVALID_ATTACK_ID_RATE_K10}}` (mã sinh ra sai cú pháp hoặc ngoài danh mục v19.2).
  - **Trục 5 (Valid but Wrong Classification):** `{{S2_WRONG_CLASS_RATE_K10}}` (mã sinh ra hợp lệ nhưng sai kỹ thuật mục tiêu).
  - **Ma Trận Giao Thoa Độc Lập (Joint Overlaps):**
    * Trượt truy xuất & Sai phân loại: `{{S2_OVERLAP_MISS_AND_WRONG_K10}}` bản ghi.
    * Trượt truy xuất & Lỗi nhà cung cấp: `{{S2_OVERLAP_MISS_AND_PROV_K10}}` bản ghi.
    * Trượt truy xuất & Lỗi phân tích cú pháp: `{{S2_OVERLAP_MISS_AND_PARSE_K10}}` bản ghi.
    * Trượt truy xuất & Mã không hợp lệ: `{{S2_OVERLAP_MISS_AND_INVAL_K10}}` bản ghi.
  - *Ghi chú phương pháp luận:* Nhánh `no_rag` không thực hiện truy xuất nên các trường đo lường truy xuất được gán giá trị strictly `null` (N/A).
- **Xác Suất Phân Loại Có Điều Kiện Khách Quan ($k=10$):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}10)$: `{{S2_P_CORRECT_GIVEN_RETRIEVED}}`.
  - $P(\text{Correct} \mid \text{GT Absent from Top-}10)$: `{{S2_P_CORRECT_GIVEN_ABSENT}}` (*Correct attribution despite GT absent from retrieved Top-k*).

#### Speaker Notes Update (Slide 8):
> "GHI CHÚ DIỄN GIẢ (Slide 8):  
> Tại Slide 8, khung đánh giá D2i bóc tách toàn diện 5 trục thất bại độc lập mà không áp đặt tính loại trừ nhân tạo. Ở độ sâu k=10, tỷ lệ trượt truy xuất chiếm {{S2_RETRIEVAL_MISS_RATE_K10}}, lỗi phân loại chiếm {{S2_WRONG_CLASS_RATE_K10}}, cùng số đếm giao thoa {{S2_OVERLAP_MISS_AND_WRONG_K10}} trường hợp đồng thời vừa trượt truy xuất vừa sai phân loại. Về mặt xác suất có điều kiện, khi kỹ thuật mục tiêu xuất hiện trong Top-10, mô hình đạt độ chính xác P(Correct | Retrieved) là {{S2_P_CORRECT_GIVEN_RETRIEVED}}. Ngược lại, khi kỹ thuật mục tiêu vắng mặt trong Top-10, xác suất gán nhãn đúng ghi nhận khách quan ở mức {{S2_P_CORRECT_GIVEN_ABSENT}} (Correct attribution despite GT absent from retrieved Top-k)."

---

### 2.4 Slide 9: Kết Quả RQ3 - Đánh Đổi Độ Sâu, Độ Trễ & Chi Phí Tài Chính (RQ3 Tradeoffs & Costs)

*Objective:* Populate empirical latency distributions, token consumption, reconciled per-query financial costs, and whole-study budget ledger accounting from `/rq3/tradeoffs_by_condition/{c}/...` and `/rq3/whole_study_accounting/...` in `outputs/canonical_analysis/rq_analysis.json`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_MEDIAN_LAT_NO_RAG_SEC}}` | `/rq3/tradeoffs_by_condition/no_rag/latency_ms/median` / 1000 | Median latency in seconds for baseline ($k=0$). |
| `{{S2_MEDIAN_LAT_K10_SEC}}` | `/rq3/tradeoffs_by_condition/rag_k10/latency_ms/median` / 1000 | Median latency in seconds for RAG $k=10$. |
| `{{S2_MEAN_PROMPT_TOK_NO_RAG}}` | `/rq3/tradeoffs_by_condition/no_rag/tokens/mean_prompt_tokens` | Mean prompt tokens per request for baseline ($k=0$). |
| `{{S2_MEAN_PROMPT_TOK_K10}}` | `/rq3/tradeoffs_by_condition/rag_k10/tokens/mean_prompt_tokens` | Mean prompt tokens per request for RAG $k=10$. |
| `{{S2_COST_LOGICAL_REQ_NO_RAG}}` | `/rq3/tradeoffs_by_condition/no_rag/financial_cost_usd/cost_per_logical_request_usd` | Reconciled cost per logical request ($N=1,280$) for baseline. |
| `{{S2_COST_LOGICAL_REQ_K10}}` | `/rq3/tradeoffs_by_condition/rag_k10/financial_cost_usd/cost_per_logical_request_usd` | Reconciled cost per logical request ($N=1,280$) for RAG $k=10$. |
| `{{S2_TOTAL_STUDY_BUDGET_USD}}` | `/rq3/whole_study_accounting/total_study_budget_usd` | Pinned study-wide budget cap ($19.99 USD). |
| `{{S2_CANONICAL_TOTAL_USD}}` | `/rq3/whole_study_accounting/canonical_conditions_total_usd` | Reconciled total expenditure across all 5 canonical test conditions (USD). |
| `{{S2_NET_REMAINING_USD}}` | `/rq3/whole_study_accounting/net_remaining_uncommitted_budget_usd` | Net uncommitted study budget remaining after all 6,400 runs (USD). |
| `{{S2_PRIOR_PILOT_HOLD_USD}}` | `/rq3/whole_study_accounting/prior_pilot_provisional_hold_usd` | Retained reference to provisional pilot reservation ($0.05264010 USD). |

#### Target Content Outline (Slide 9):
- **Bảng Đánh Đổi Tài Nguyên Theo Độ Sâu $k \in \{0, 1, 3, 5, 10\}$:**
  | Điều kiện | $k$ | Median Latency (s) | Mean Prompt Tokens | Reconciled Cost / Logical Request ($) | Total Condition Spend ($) |
  | :--- | :---: | :---: | :---: | :---: | :---: |
  | `no_rag` | 0 | `{{S2_MEDIAN_LAT_NO_RAG_SEC}}` s | `{{S2_MEAN_PROMPT_TOK_NO_RAG}}` | `{{S2_COST_LOGICAL_REQ_NO_RAG}}` $ | ... |
  | `rag_k1` | 1 | ... | ... | ... | ... |
  | `rag_k3` | 3 | ... | ... | ... | ... |
  | `rag_k5` | 5 | ... | ... | ... | ... |
  | `rag_k10`| 10 | `{{S2_MEDIAN_LAT_K10_SEC}}` s | `{{S2_MEAN_PROMPT_TOK_K10}}` | `{{S2_COST_LOGICAL_REQ_K10}}` $ | ... |
- **Hạch Toán Ngân Sách Toàn Nghiên Cứu (`whole_study_accounting`):**
  - Trần ngân sách tối đa: `{{S2_TOTAL_STUDY_BUDGET_USD}}` USD (khóa cứng $19.99 USD).
  - Tổng chi phí thực tế cho 5 điều kiện chính thức (6,400 queries): `{{S2_CANONICAL_TOTAL_USD}}` USD.
  - Khoản giữ chỗ thận trọng ban đầu: `{{S2_PRIOR_PILOT_HOLD_USD}}` USD ($0.05264010 USD).
  - Số dư ngân sách khả dụng còn lại: `{{S2_NET_REMAINING_USD}}` USD.
  - *Lưu ý phương pháp:* Chi phí được hạch toán độc lập qua đối soát biên nhận giao dịch (`request_journal.jsonl`) và biểu giá đóng băng tại `config/pricing_v1.json` (`billing_invoice_queried: false`).

#### Speaker Notes Update (Slide 9):
> "GHI CHÚ DIỄN GIẢ (Slide 9):  
> Slide 9 làm rõ quy luật đánh đổi giữa tài nguyên tính toán và chi phí tài chính trong RQ3. Khi mở rộng độ sâu k từ 0 lên 10, lượng prompt token trung bình tăng từ {{S2_MEAN_PROMPT_TOK_NO_RAG}} lên {{S2_MEAN_PROMPT_TOK_K10}} tokens, kéo theo độ trễ trung vị (median latency) tăng từ {{S2_MEDIAN_LAT_NO_RAG_SEC}} giây lên {{S2_MEDIAN_LAT_K10_SEC}} giây. Chi phí trung bình cho mỗi yêu cầu logic tăng từ {{S2_COST_LOGICAL_REQ_NO_RAG}} USD lên {{S2_COST_LOGICAL_REQ_K10}} USD. Toàn bộ 6,400 yêu cầu tiêu tốn tổng cộng {{S2_CANONICAL_TOTAL_USD}} USD, nằm an toàn dưới trần ngân sách 19.99 USD với số dư khả dụng còn lại là {{S2_NET_REMAINING_USD}} USD."

---

### 2.5 Slide 10: Chẩn Đoán Góc Nhìn & Phân Tích Cặp Biểu Diễn (View Diagnostics & Paired Analysis)

*Objective:* Disentangle marginal view distributions from paired cohort metrics on the 278 complete scorable pairs using pointers from `/rq3/view_diagnostics/{c}/...` in `outputs/canonical_analysis/rq_analysis.json`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_SINGLE_VIEW_ACC_E2E}}` | `/rq3/view_diagnostics/rag_k10/single_view_accuracy_e2e` | Marginal attribution accuracy across ALL 278 single views with valid GT. |
| `{{S2_CONTEXT_VIEW_ACC_E2E}}` | `/rq3/view_diagnostics/rag_k10/contextual_view_accuracy_e2e` | Marginal attribution accuracy across ALL 440 contextual views with valid GT. |
| `{{S2_VIEW_ACC_DELTA}}` | `/rq3/view_diagnostics/rag_k10/view_accuracy_delta` | Marginal delta: `single_view_accuracy_e2e - contextual_view_accuracy_e2e`. |
| `{{S2_PAIRED_SINGLE_ACC}}` | `/rq3/view_diagnostics/rag_k10/single_paired_accuracy` | Single-view accuracy within the 278 complete scorable pairs cohort. |
| `{{S2_PAIRED_CONTEXT_ACC}}`| `/rq3/view_diagnostics/rag_k10/contextual_paired_accuracy` | Contextual-view accuracy within the 278 complete scorable pairs cohort. |
| `{{S2_PAIRED_DELTA_PP}}` | `/rq3/view_diagnostics/rag_k10/paired_delta` | Paired delta: `single_paired_accuracy - contextual_paired_accuracy` in pp. |
| `{{S2_MCNEMAR_P_ASYMPT}}` | `/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_asymptotic` | Asymptotic p-value from exploratory paired McNemar test on 278 pairs. |
| `{{S2_MCNEMAR_P_EXACT}}` | `/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_exact` | Exact binomial p-value from exploratory paired McNemar test on 278 pairs. |
| `{{S2_BOTH_CORRECT_COUNT}}` | `/rq3/view_diagnostics/rag_k10/pair_concordance/both_correct_count` | Number of pairs where both representations yielded correct attribution. |
| `{{S2_SINGLE_ONLY_CORRECT}}` | `/rq3/view_diagnostics/rag_k10/pair_concordance/single_only_correct_count` | Number of pairs where only Single view was correct. |
| `{{S2_CONTEXT_ONLY_CORRECT}}`| `/rq3/view_diagnostics/rag_k10/pair_concordance/contextual_only_correct_count` | Number of pairs where only Contextual view was correct. |
| `{{S2_BOTH_INCORRECT_COUNT}}`| `/rq3/view_diagnostics/rag_k10/pair_concordance/both_incorrect_count` | Number of pairs where both representations were incorrect. |

#### Target Content Outline (Slide 10):
- **Phân Biệt Hai Lớp Đo Lường Biểu Diễn:**
  - **Lớp 1: Phân Phối Biên (Marginal View Accuracies - Kích thước mẫu không bằng nhau, không mang tính so sánh nhân quả):**
    * Độ chính xác trên toàn bộ 278 Single views: `{{S2_SINGLE_VIEW_ACC_E2E}}`.
    * Độ chính xác trên toàn bộ 440 Contextual views: `{{S2_CONTEXT_VIEW_ACC_E2E}}` (278 complete pairs + 162 contextual-only pairs = 440 views).
    * Chênh lệch phân phối biên: `{{S2_VIEW_ACC_DELTA}}`.
    * *Cảnh báo khoa học:* Không được nhầm lẫn số liệu 440 contextual views là độ chính xác đối ứng của 278 cặp!
  - **Lớp 2: Đánh Giá Đối Ứng Cặp Chuẩn (Paired Cohort Analysis trên 278 Cặp Hoàn Chỉnh):**
    * Cơ cấu nội bộ của 278 cặp hoàn chỉnh: **238 cặp** có ground-truth trùng khớp hoàn toàn, và **40 cặp** có ground-truth phân kỳ giữa hai góc nhìn. Toàn bộ 278 cặp được báo cáo minh bạch.
    * Độ chính xác đối ứng nội bộ: Single = `{{S2_PAIRED_SINGLE_ACC}}` vs Contextual = `{{S2_PAIRED_CONTEXT_ACC}}` (chênh lệch: `{{S2_PAIRED_DELTA_PP}}` pp).
    * Ma trận hòa hợp cặp (Pair Concordance Matrix across 278 pairs):
      - Cả hai cùng đúng: `{{S2_BOTH_CORRECT_COUNT}}` cặp.
      - Chỉ Single đúng: `{{S2_SINGLE_ONLY_CORRECT}}` cặp.
      - Chỉ Contextual đúng: `{{S2_CONTEXT_ONLY_CORRECT}}` cặp.
      - Cả hai cùng sai: `{{S2_BOTH_INCORRECT_COUNT}}` cặp.
    * Kiểm định McNemar thăm dò: $p_{\text{asymptotic}} =$ `{{S2_MCNEMAR_P_ASYMPT}}`, $p_{\text{exact}} =$ `{{S2_MCNEMAR_P_EXACT}}`.

#### Speaker Notes Update (Slide 10):
> "GHI CHÚ DIỄN GIẢ (Slide 10):  
> Slide 10 làm rõ sự khác biệt giữa phân phối biên và đánh giá đối ứng cặp trên tập TEST. Ở cấp độ phân phối biên với quy mô mẫu không bằng nhau, 278 single views đạt độ chính xác {{S2_SINGLE_VIEW_ACC_E2E}} trong khi 440 contextual views đạt {{S2_CONTEXT_VIEW_ACC_E2E}}. Khi đi sâu vào phân tích đối ứng cặp trên đúng 278 cặp hoàn chỉnh (bao gồm 238 cặp trùng nhãn và 40 cặp phân kỳ nhãn), độ chính xác của Single đạt {{S2_PAIRED_SINGLE_ACC}} so với {{S2_PAIRED_CONTEXT_ACC}} của Contextual, tạo mức chênh lệch paired delta là {{S2_PAIRED_DELTA_PP}} điểm phần trăm (pp). Kiểm định McNemar thăm dò cho thấy mức ý nghĩa thống kê với p_value_asymptotic = {{S2_MCNEMAR_P_ASYMPT}} và p_value_exact = {{S2_MCNEMAR_P_EXACT}}."

---

### 2.6 Slide 11: Đặc Tả Kiến Trúc Mô Hình & Năng Lực Tái Lập (Architecture Specification & Reproducibility)

*Objective:* Detail the frozen retrieval embedding pipeline specification and certified zero-cost offline reproduction protocol.

| Specification Element | Frozen Repository Value / Pointer | Validation Contract |
| :--- | :--- | :--- |
| **Embedding Model ID** | `sentence-transformers/all-MiniLM-L6-v2` (short: `all-MiniLM-L6-v2`) | Pinned in `config/retrieval.json -> embedding.model_name`. |
| **Embedding Dimension** | `384` | Pinned in `config/retrieval.json -> embedding.dimension`. |
| **Model Git Revision** | `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (short: `1110a24`) | Pinned in `config/retrieval.json -> embedding.revision`. |
| **FAISS Index Type** | `IndexFlatIP` (Cosine similarity qua chuẩn hóa $L_2$) | Pinned in `config/retrieval.json -> index.metric`. |
| **Knowledge Corpus** | `attack/corpus/enterprise-windows-v19.2.jsonl` (474 techniques) | Cryptographic hash in `config/canonical_experiment_lock_v1.json`. |
| **Runtime LLM** | `gpt-5.6-luna` (reasoning: xhigh, interface: responses) | Pinned in `config/experiment_config.json`. |
| **Offline Verification Guard** | `scripts/run_offline_tests.py` (`attempted_egress=0`) | Python socket layer interception preventing accidental external network egress. |
| **Automated Reproduction** | `python scripts/reproduce_study.py --all` | Recompiles diagnostics, tables, figures from 15 canonical lockfile artifacts. |

#### Target Content Outline (Slide 11):
- **Đặc Tả Kỹ Thuật Pipeline Nhúng & Truy Xuất Đóng Băng:**
  - Mô hình nhúng chuẩn: `sentence-transformers/all-MiniLM-L6-v2` (`all-MiniLM-L6-v2`).
  - Chiều không gian vector: 384 dimensions.
  - Mã băm phiên bản mô hình (Git Revision): `1110a243fdf4706b3f48f1d95db1a4f5529b4d41` (`1110a24`).
  - Chỉ mục tìm kiếm nội bộ: FAISS `IndexFlatIP` (tính toán Inner Product tương đương Cosine Similarity nhờ chuẩn hóa vector đơn vị $L_2$).
  - Kho ngữ cảnh tri thức: 474 tài liệu kỹ thuật MITRE ATT&CK v19.2 Enterprise Windows (`attack/corpus/enterprise-windows-v19.2.jsonl`).
- **Quy Trình Tái Lập Ngoại Tuyến Chi Phí 0 Đồng:**
  - Thực thi kiểm thử ngoại tuyến hoàn toàn qua runner `scripts/run_offline_tests.py` với cơ chế socket guard chặn đứng rò rỉ mạng (`attempted_egress=0`).
  - Khóa mật mã 15 canonical artifacts trong `config/canonical_experiment_lock_v1.json` bảo đảm tính bất biến tuyệt đối của dữ liệu.

#### Speaker Notes Update (Slide 11):
> "GHI CHÚ DIỄN GIẢ (Slide 11):  
> Toàn bộ kiến trúc thực nghiệm được đóng băng chặt chẽ theo đặc tả kỹ thuật: mô hình nhúng all-MiniLM-L6-v2 (384 chiều, revision 1110a24) kết hợp chỉ mục FAISS IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows. Khả năng tái lập độc lập với chi phí 0 đồng được bảo chứng bởi bộ kiểm thử offline scripts/run_offline_tests.py với cơ chế can thiệp tầng socket bảo đảm attempted_egress=0 và khóa mật mã 15 artifact trong canonical-lock-v1."

---

## 3. Presentation Authoring Compliance Requirements

To satisfy strict quality control gates and prevent slide deck corruption during Phase S2 delivery:

### 3.1 Documented JS Artifact-Tool API Pipeline
- **Core Directive:** The production presentation slide deck (`docs/presentation/slides.pptx`) **MUST** be finalized and updated using the documented JavaScript APIs of `@oai/artifact-tool`.
- **Verified API Workflow:**
  ```javascript
  import { FileBlob, PresentationFile } from "@oai/artifact-tool";

  // Step 1: Load existing presentation as FileBlob
  const presentation = await PresentationFile.importPptx(await FileBlob.load(sourcePath));

  // Step 2: Inspect slide structure and discover exact object IDs
  const snapshot = await presentation.inspect({
    kind: "slide,textbox,shape,image,table,chart,notes,layout",
    maxChars: 12000,
  });

  // Step 3: Resolve only verified IDs from the snapshot and edit in-place
  const targetShape = presentation.resolve(verifiedObjectId);
  targetShape.text.replace(placeholderToken, canonicalValue);

  // Step 4: Export to staging destination and verify
  const exported = await PresentationFile.exportPptx(presentation);
  await exported.save(candidateOutputPath);
  ```
- **Staging & Preservation Rules:**
  1. All updates must be executed on an isolated staging copy (`staging/slides_candidate.pptx`) before replacing the production file.
  2. The source presentation must never be overwritten in-place without snapshot verification.
  3. The resulting `.pptx` deck must be validated to ensure:
     - 16:9 widescreen dimensions (`13.333 x 7.500` inches) remain unaltered.
     - Custom palette styling (Navy `#0A1128`, Vibrant Cyan `#00E5FF`, Accent Amber `#FF9100`) is intact.
     - Zero text box shape clipping or label overflow.
     - Full editability of all text elements and tables (no flattening into static raster images).

### 3.2 Tooling Disclosure Invariant
- **Formal Classification:** The Python script `scripts/generate_slides.py` is officially designated as an **exploratory preparation scaffold**. It was utilized during early Phase S1 to establish initial layouts and prototype card geometry.
- **Compliance Rule:** The existence or execution of `scripts/generate_slides.py` does **NOT** constitute proof of final presentation authoring compliance. The production `.pptx` delivery will formally certify that the deck was inspected and updated via the verified `@oai/artifact-tool` JavaScript pipeline.
- **Documentation Alignment:** This disclosure will be recorded in `docs/presentation/slides.md` (metadata header), `docs/reproducibility.md` (Section 5), and `reports/evidence/reproducibility_package_manifest.md`.

### 3.3 Visual & Typography Quality Gates
- **Font Hierarchy:**
  - Slide Titles: 28pt Calibri Bold.
  - Section Headers: 14–16pt Calibri Bold, Cyan Accent.
  - Card Titles: 13–14pt Calibri Bold.
  - Card Body Text: 10.0pt–12.0pt, line spacing 2.5–3.0pt.
- **Text Box Safety Margins:** Padding left/right/top/bottom fixed at 0.05 inches. Zero shape overflow allowed.
- **Speaker Notes Standard:** Every slide must include structured sections:
  1. `GHI CHÚ DIỄN GIẢ (Slide X):` Narrative script for defense in Vietnamese.
  2. `Bằng chứng dự án:` Explicit repository relative file paths and SHA-256 digests.

---

## 4. Sanitized Reproducibility Packaging Protocol

Phase S2 delivery requires a complete, sealed, and audited reproducibility package enabling external researchers to independently verify all findings with zero financial expenditure.

### 4.1 Cryptographic Hash Sealing Protocol
- Upon generation of final canonical evaluation artifacts in `outputs/canonical_evaluation/` and secondary analysis in `outputs/canonical_analysis/rq_analysis.json`, execute automated SHA-256 auditing.
- Update `docs/sanitized_evidence_manifest.json` under the `canonical_evaluation` section:
  ```json
  "canonical_evaluation": {
    "overall_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "per_condition_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "per_technique_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "retrieval_conditional_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "failure_decomposition.json": { "sha256": "...", "size_bytes": 0 },
    "run_provenance.json": { "sha256": "...", "size_bytes": 0 }
  },
  "canonical_analysis": {
    "rq_analysis.json": { "sha256": "...", "size_bytes": 0 }
  }
  ```
  *(Notice: Specialist B Alignment confirms the evaluator outputs strictly these 6 JSON files into `outputs/canonical_evaluation/`).*
- Update `reproducibility_package` entries with final digests for `slides.md`, `slides.pptx`, `reproducibility.md`, and `reproduce_study.py`.

### 4.2 Request Journal Integrity & Sanitization Protocol
- The raw request journal (`request_journal.jsonl`) generated by the live runner contains event-stream transaction records (`header`, `transition`, `attempt`, `complete`, etc.).
- **Sanitization Protocol:**
  1. *Structural Fidelity:* The native JSONL event stream schema is preserved. Do NOT apply a destructive column allowlist that assumes flat CSV records and breaks replay invariants.
  2. *Secret Scanning:* Execute a comprehensive regex scan across every byte of the file targeting OpenAI project keys (`sk-proj-[a-zA-Z0-9_\-]{48,}`), authorization tokens, and private credentials.
  3. *Sanitization Sealing:* If no secrets are detected, the verified native event journal is committed as `reports/evidence/canonical_run_20261001/request_journal.sanitized.jsonl`. If any transport headers or tokens are present, they are stripped while preserving the core event stream.

### 4.3 Decoupled Offline Reproduction Tooling
- **Distinction of Figure Generation Modules:**
  - Existing `reproduce_study.py --generate-figures` generates historical Stage B diagnostics (`fig_rq2_retrieval_hit_rates.png`, `fig_rq2_per_technique_breakdown.png`) and DEV cost pilot telemetry (`fig_rq3_pilot_token_scaling.png`).
  - For Phase S2 canonical TEST study reproduction, a dedicated visualization routine (`generate_test_study_figures`) will be introduced to render figures from the 6 canonical evaluation outputs (`outputs/canonical_evaluation/`) and secondary analysis (`outputs/canonical_analysis/rq_analysis.json`).
- **Offline Socket Guard Invariant:**
  - All reproduction steps must be executed through `scripts/run_offline_tests.py` under socket-level network blocking:
    ```bash
    # Step 1: Verify complete hash immutability
    python scripts/reproduce_study.py --verify-hashes

    # Step 2: Authoritative evaluation under offline socket guard
    python scripts/run_offline_tests.py -c "import sys; from scripts.reproduce_study import main; sys.exit(main(['--run-evaluator', '--run-dir', 'outputs/canonical_evaluation']))"

    # Step 3: Recompile publication figures and summary tables
    python scripts/reproduce_study.py --generate-figures --generate-tables
    ```
  - *Acceptance Criterion:* Zero external network egress (`attempted_egress=0`), zero provider credentials required, exact replication of metric values and figures.

---

## 5. Phase S2 Execution Checklist & Validation Criteria

| Sequence | Task / Milestone | Validation Command / Verification Criteria | Owner |
| :---: | :--- | :--- | :---: |
| **Step 1** | Verify Live Run Completion | `Get-Process -Id 50192` completes; exactly 6,400 completed records in run directory. | Lead B / D |
| **Step 2** | Sanitize & Audit Request Journal | Comprehensive regex secret scan passes; event structure preserved; commit sanitized journal. | Lead D |
| **Step 3** | Execute Authoritative Evaluator | `python scripts/reproduce_study.py --run-evaluator --run-dir <DIR>`. Enforces `execution_mode == 'live'`. Produces strictly 6 native JSON artifacts in `outputs/canonical_evaluation/`. | Lead D |
| **Step 4** | Execute Secondary Analysis | Compute paired cohort metrics across 278 complete pairs and marginal distributions -> `outputs/canonical_analysis/rq_analysis.json`. | Lead D |
| **Step 5** | Extract Canonical Metrics | Aggregate journal financials; extract pointers from 6 native JSONs and `rq_analysis.json`. | Lead D |
| **Step 6** | Update Markdown Presentation | Replace placeholder tokens in `docs/presentation/slides.md` with verified empirical values. | Lead D |
| **Step 7** | Author Final PPTX Deck via JS API | Execute `@oai/artifact-tool` JavaScript pipeline (`importPptx`, `inspect`, `resolve`, `exportPptx`); verify 16:9 geometry and zero text clipping. | Lead D |
| **Step 8** | Generate Canonical TEST Figures | Compile dedicated canonical figures and Markdown summary tables into `outputs/reproduction/`. | Lead D |
| **Step 9** | Re-run Complete Offline Test Suite | `python scripts/run_offline_tests.py` -> 100% pass; `attempted_egress=0`. | Lead D |
| **Step 10**| Update Evidence Manifests | Calculate SHA-256 and byte counts; update `docs/sanitized_evidence_manifest.json`. | Lead D |
| **Step 11**| Commit & PR Update | Git commit, push to `codex/s1-reproducibility-presentation`, update PR #26 description. | Lead D |

---

## 6. Document Sign-Off & Status

- **Status:** PENDING CODEX REVIEW (Preparation Repair Bounded - Aligned to `fixture_export_schema_b172.json`)  
- **Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
- **PRE_SHA:** `ebe83519b67f8e07ee255164ec3b39f29cf5abcc`  
- **Output Document Path:** `reports/evidence/s2_presentation_and_repro_plan.md`  
- **Safety Guarantee:** Live runner PID 50192 running undisturbed; zero mock findings promoted to canonical status; zero live provider calls; no destructive modifications to repo source or config files.
