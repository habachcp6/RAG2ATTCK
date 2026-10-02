# Phase S2: Presentation Deck & Sanitized Reproducibility Plan

**Subagent Role:** Lead D (Reproducibility & Presentation Lead for Phase S2)  
**Dedicated Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
**Target Branch:** `codex/s1-reproducibility-presentation` (PR #26)  
**Execution Timestamp (UTC):** 2026-10-02T00:15:00Z (Local: 2026-10-02T07:15:00+07:00)  
**PRE_SHA:** `55494a433cc70f15f253e34742d5bda2a4762565`  
**Document Classification:** STRICTLY PLAN-ONLY (Preparation Repair Bounded - UNIFIED_MAPPING_R2 Remediation)  
**Status:** PLAN-ONLY PENDING CODEX APPROVAL (Do NOT treat as final approved for S2 execution)  

---

## 1. Executive Summary & Remediation Context

During Phase S1, Subagent D established the offline reproduction infrastructure, frozen protocol cryptographic bindings (15 canonical artifacts under `canonical-lock-v1`), fail-closed execution-mode boundary enforcement (`execution_mode == 'live'`), and a 12-slide bilingual presentation scaffold. In Phase S1, all end-to-end evaluation slides for the full 1,280-sample test matrix (6,400 records) were strictly marked with the `[PENDING EXECUTION]` provenance badge, reflecting ongoing background execution under live runner PID 50192.

Following Codex Supervisor review **UNIFIED_MAPPING_R2**, this document provides a comprehensive, rigorous remediation of the Phase S2 plan. It resolves all scientific and methodological nuances:
1. Corrects the retrieval embedding model to the frozen repository standard (`sentence-transformers/all-MiniLM-L6-v2`, 384 dimensions, FAISS `IndexFlatIP`).
2. Disentangles marginal view accuracies (278 single views vs 440 contextual views) from paired cohort metrics on the exact 278 complete scorable pairs, documenting internal cohort composition (238 identical GT pairs vs 40 divergent GT pairs).
3. Establishes strictly neutral phrasing for conditional metrics ("Correct attribution despite GT absent from retrieved Top-k") and enumerates the complete 5 failure axes.
4. Unifies authoritative output directory structures across native evaluation (`outputs/canonical_evaluation/`) and secondary research analysis (`outputs/canonical_analysis/rq_analysis.json`).

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
3. **Secondary Research Analysis Contract:** Post-hoc paired metrics across scenario representations, Pareto trade-off curves, and diagnostic representations are compiled into a dedicated secondary analysis bundle: `outputs/canonical_analysis/rq_analysis.json`.
4. **Authoritative Pricing Tariffs & Configuration:** All pricing tariffs and budget parameters are bound directly to `config/pricing_v1.json`, NOT `experiment_config.json`:
   - Runtime model: `gpt-5.6-luna` with `reasoning_effort: xhigh`, service tier `default`.
   - Standard short-context tariffs:
     * Input token tariff: **$0.20 USD / 1M tokens** (`input_per_million`)
     * Cached input read tariff: **$0.02 USD / 1M tokens** (`cache_read_per_million`)
     * Cached input write tariff: **$0.25 USD / 1M tokens** (`cache_write_per_million`)
     * Output & reasoning token tariff: **$1.20 USD / 1M tokens** (`output_per_million`)
   - Budget constraints: Pinned hard cap of **$19.99 USD** (`total_study_budget_usd`), conservative provisional hold of **$0.05264010 USD** (`prior_pilot_provisional_hold_usd`), and net starting available budget of **$19.93735990 USD** (`net_available_starting_budget_usd`).
5. **Frozen Retrieval Pipeline Specification:** In accordance with `config/retrieval.json`:
   - Embedding Model ID: `sentence-transformers/all-MiniLM-L6-v2`
   - Embedding Model Revision: `1110a243fdf4706b3f48f1d95db1a4f5529b4d41`
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
   - Unverified novelty claims ("đầu tiên chống leakage") and prescriptive technology mandates (imposing "HybridSearch" as mandatory) are replaced with objective empirical observations and suggestions for future exploration.
   - Metric differences and deltas are reported strictly in percentage points (`pp`), never percent (`%`).
10. **Documented `@oai/artifact-tool` JavaScript Workflow:**
    - PPTX modifications use the verified JavaScript APIs (`importPptx`, `inspect`, `resolve`, `exportPptx`) documented in `@oai/artifact-tool`.
    - Editing operations run on reference staging copies to verify visual fidelity before updating production files. The resulting `.pptx` remains fully openable, editable, and free of clipping.
    - `scripts/generate_slides.py` is acknowledged strictly as an exploratory preparation scaffold.
11. **Journal Integrity & Offline Reproduction Decoupling:**
    - The native JSONL event stream in `request_journal.jsonl` (`event`, `header`, `transition`, `key`, `state`, `attempt`, `ordinal`, `complete`, `record_sha256`) is preserved with byte-level fidelity, avoiding destructive flat-column allowlists.
    - Existing `reproduce_study.py --generate-figures` reproduces historical Stage B/DEV figures; a dedicated module will handle canonical TEST study figures upon S2 execution. All verification runs under `scripts/run_offline_tests.py` with fail-closed socket guards (`attempted_egress=0`).

---

## 2. Placeholders-to-Deck Mapping for Phase S2 Canonical Updating

Once authoritative evaluation on the completed live run directory produces the canonical metric bundle (strictly the 6 native JSON artifacts in `outputs/canonical_evaluation/` and secondary analysis in `outputs/canonical_analysis/rq_analysis.json`), the Vietnamese presentation deck (`docs/presentation/slides.md` and `docs/presentation/slides.pptx`) will be updated by replacing placeholder tokens with verified empirical values.

### 2.1 Slide 6: Phương Pháp & Chi Phí Thực Nghiệm (Budget, Settled Spend & Tariff)

*Objective:* Replace provisional pilot estimates with settled financial ledger metrics and execution telemetry aggregated across all 6,400 live requests.

| Placeholder Key | Source Path / Extraction Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_TOTAL_REQUESTS}}` | `run_dir/manifest.json -> sample_count * len(conditions)` | Total requests executed (Must equal exactly `6,400`). |
| `{{S2_ACTUAL_SETTLED_SPEND_USD}}` | Aggregated from `request_journal.jsonl` / `StudyBudgetLedger` | Total accounted provider cost (USD) based on lockfile tariffs; must satisfy `< $19.99`. |
| `{{S2_CONSERVATIVE_HOLD_USD}}` | `config/pricing_v1.json -> prior_pilot_provisional_hold_usd` | Retained reference to provisional hold ($0.05264010 USD). |
| `{{S2_HARD_BUDGET_CAP_USD}}` | `config/pricing_v1.json -> total_study_budget_usd` | Pinned hard cap ($19.99 USD); actual spend must be `< 19.99`. |
| `{{S2_NATIVE_TARIFF_INPUT}}` | `config/pricing_v1.json -> tariffs.default.short.input_per_million` | Standard input token tariff ($0.20 / 1M tokens). |
| `{{S2_NATIVE_TARIFF_CACHE_READ}}`| `config/pricing_v1.json -> tariffs.default.short.cache_read_per_million`| Cached prompt read tariff ($0.02 / 1M tokens). |
| `{{S2_NATIVE_TARIFF_OUTPUT}}` | `config/pricing_v1.json -> tariffs.default.short.output_per_million` | Standard output & reasoning token tariff ($1.20 / 1M tokens). |
| `{{S2_TOTAL_INPUT_TOKENS}}` | Aggregated from `request_journal.jsonl` / records | Aggregate prompt tokens consumed across all 5 conditions. |
| `{{S2_TOTAL_OUTPUT_TOKENS}}` | Aggregated from `request_journal.jsonl` / records | Aggregate completion & reasoning tokens consumed. |
| `{{S2_MEAN_QUERY_LATENCY_MS}}`| Mean of `latency_ms` across completed records in journal | Mean round-trip latency per request (excluding initialization wall time). |
| `{{S2_TOTAL_WALL_TIME_HOURS}}`| Runner process wall time (`end_time - start_time`) | Total continuous execution duration in hours. |
| `{{S2_PROVIDER_RETRY_COUNT}}` | Aggregated retry transitions in `request_journal.jsonl` | Total provider retry attempts encountered across the run. |
| `{{S2_PARSE_STATUS_VALID_COUNT}}`| Count of records with `parse_status == 'VALID'` | Empirically verified valid attribution predictions. |

#### Target Content Outline (Slide 6):
- **Card 1 (Hạch Toán Chi Phí & Kỷ Cương Ngân Sách):**
  - Chi phí hạch toán thực tế: `{{S2_ACTUAL_SETTLED_SPEND_USD}}` USD cho 6,400 queries (dưới trần ngân sách đóng băng $19.99 USD tại `config/pricing_v1.json`).
  - Khoản giữ chỗ thận trọng ban đầu: $0.05264010 USD (`prior_pilot_provisional_hold_usd`).
  - Biểu giá niêm yết chuẩn (`gpt-5.6-luna`, tier default, short context): Input: `{{S2_NATIVE_TARIFF_INPUT}}` USD/1M tokens; Cache read: `{{S2_NATIVE_TARIFF_CACHE_READ}}` USD/1M tokens; Output: `{{S2_NATIVE_TARIFF_OUTPUT}}` USD/1M tokens.
  - Tổng token xử lý: `{{S2_TOTAL_INPUT_TOKENS}}` input tokens, `{{S2_TOTAL_OUTPUT_TOKENS}}` output & reasoning tokens.
  - Lưu ý phương pháp: Số liệu chi phí là giá trị ước tính hạch toán dựa trên biểu giá đóng băng và lượng token thực tế (`billing_invoice_queried: false`), không phải hóa đơn thanh toán trực tiếp từ nhà cung cấp.
- **Card 2 (Độ Ổn Định & Vận Hành Nhà Cung Cấp):**
  - Phân loại trạng thái cú pháp theo `ParseStatus`: Ghi nhận `{{S2_PARSE_STATUS_VALID_COUNT}}` kết quả đạt chuẩn VALID theo schema `TechniquePrediction` (trên tổng số 6,400 yêu cầu).
  - Tần suất thử lại mạng / nhà cung cấp: `{{S2_PROVIDER_RETRY_COUNT}}` lần thử lại được ghi nhận trong nhật ký giao dịch.
  - Độ trễ phản hồi logic trung bình: `{{S2_MEAN_QUERY_LATENCY_MS}}` ms/request (tổng thời gian thực thi: `{{S2_TOTAL_WALL_TIME_HOURS}}` giờ).

#### Speaker Notes Update (Slide 6):
> "GHI CHÚ DIỄN GIẢ (Slide 6):  
> Tại Slide 6, toàn bộ số liệu tài chính và vận hành được hạch toán trực tiếp từ nhật ký giao dịch `request_journal.jsonl` và đối soát với `config/pricing_v1.json`. Tổng chi phí hạch toán cho 6,400 truy vấn trên mô hình gpt-5.6-luna (chế độ suy luận xhigh) đạt {{S2_ACTUAL_SETTLED_SPEND_USD}} USD, nằm an toàn trong giới hạn ngân sách 19.99 USD và khoản giữ chỗ ban đầu 0.05264010 USD. Biểu giá áp dụng được chuẩn hóa ở mức 0.20 USD/1M input tokens, 0.02 USD/1M cache read tokens và 1.20 USD/1M output tokens. Về mặt vận hành, hệ thống ghi nhận {{S2_PARSE_STATUS_VALID_COUNT}} kết quả đạt trạng thái VALID theo schema TechniquePrediction, với độ trễ logic trung bình {{S2_MEAN_QUERY_LATENCY_MS}} ms mỗi truy vấn. Cần lưu ý rằng chi phí trên là giá trị hạch toán nội bộ dựa trên số lượng token và biểu giá đã khóa, không phải số liệu trích xuất từ hóa đơn tài chính của OpenAI."

---

### 2.2 Slide 7: Kết Quả RQ1 - Định Danh Kỹ Thuật (End-to-End Attribution Performance)

*Objective:* Remove `[PENDING EXECUTION]` banner; populate official Macro-F1 and End-to-End Accuracy scores across all 5 conditions from native evaluator outputs in `outputs/canonical_evaluation/`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_MACRO_F1_NO_RAG}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/no_rag/macro_f1` | Macro-F1 score for baseline zero-shot condition ($k=0$). |
| `{{S2_MACRO_F1_RAG_K1}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k1/macro_f1` | Macro-F1 score for RAG depth $k=1$. |
| `{{S2_MACRO_F1_RAG_K3}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k3/macro_f1` | Macro-F1 score for RAG depth $k=3$. |
| `{{S2_MACRO_F1_RAG_K5}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k5/macro_f1` | Macro-F1 score for RAG depth $k=5$. |
| `{{S2_MACRO_F1_RAG_K10}}`| `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k10/macro_f1`| Macro-F1 score for RAG depth $k=10$. |
| `{{S2_ACC_E2E_NO_RAG}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/no_rag/accuracy_end_to_end` | End-to-end accuracy for baseline. |
| `{{S2_ACC_E2E_RAG_K1}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k1/accuracy_end_to_end` | End-to-end accuracy for RAG $k=1$. |
| `{{S2_ACC_E2E_RAG_K3}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k3/accuracy_end_to_end` | End-to-end accuracy for RAG $k=3$. |
| `{{S2_ACC_E2E_RAG_K5}}` | `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k5/accuracy_end_to_end` | End-to-end accuracy for RAG $k=5$. |
| `{{S2_ACC_E2E_RAG_K10}}`| `outputs/canonical_evaluation/per_condition_metrics.json -> /conditions/rag_k10/accuracy_end_to_end`| End-to-end accuracy for RAG $k=10$. |
| `{{S2_DELTA_MACRO_F1_PP}}`| Computed: `(F1(k=10) - F1(no_rag)) * 100` | Net delta gain/loss in percentage points (`pp`). |
| `{{S2_BEST_CONDITION}}` | Computed: `argmax_cond(macro_f1)` | Operating condition achieving highest Macro-F1 score. |

#### Target Content Outline (Slide 7):
- **Bảng So Sánh Hiệu Năng 5 Điều Kiện (1,280 Views TEST Split - 718 Positive Scorable Views):**
  | Điều kiện | Candidate Depth $k$ | Macro-F1 (D2d Universe) | End-to-End Accuracy (`accuracy_end_to_end`) | Delta F1 vs No-RAG (pp) |
  | :--- | :---: | :---: | :---: | :---: |
  | `no_rag` | 0 | `{{S2_MACRO_F1_NO_RAG}}` | `{{S2_ACC_E2E_NO_RAG}}` | Baseline |
  | `rag_k1` | 1 | `{{S2_MACRO_F1_RAG_K1}}` | `{{S2_ACC_E2E_RAG_K1}}` | ... |
  | `rag_k3` | 3 | `{{S2_MACRO_F1_RAG_K3}}` | `{{S2_ACC_E2E_RAG_K3}}` | ... |
  | `rag_k5` | 5 | `{{S2_MACRO_F1_RAG_K5}}` | `{{S2_ACC_E2E_RAG_K5}}` | ... |
  | `rag_k10`| 10 | `{{S2_MACRO_F1_RAG_K10}}`| `{{S2_ACC_E2E_RAG_K10}}` | `{{S2_DELTA_MACRO_F1_PP}}` pp |
  *(Lưu ý: Chỉ số độ chính xác đầu ra được lấy từ trường `accuracy_end_to_end` của evaluator; không sử dụng nhãn `exact_match`).*
- **Phân Tích Xu Hướng Hiệu Năng Thực Nghiệm:**
  - Điểm số Macro-F1 cao nhất đạt được tại điều kiện `{{S2_BEST_CONDITION}}`.
  - Phân tích tương quan thực nghiệm khi mở rộng độ sâu ứng viên $k$: Ghi nhận xu hướng thay đổi biên độ cải thiện giữa các mốc $k=1, 3, 5, 10$ trên tập dữ liệu kiểm soát synthetic-paired-v1.

#### Speaker Notes Update (Slide 7):
> "GHI CHÚ DIỄN GIẢ (Slide 7):  
> Kết quả đo lường RQ1 trên toàn bộ 1,280 mẫu kiểm chuẩn của tập TEST (bao gồm 718 mẫu có ground-truth định danh dương tính) phản ánh rõ nét tác động của việc bổ sung tài liệu tham chiếu từ cơ sở tri thức ATT&CK Enterprise v19.2. Điểm số Macro-F1 thay đổi {{S2_DELTA_MACRO_F1_PP}} điểm phần trăm (pp) khi chuyển từ điều kiện no_rag sang rag_k10. Trong 5 điều kiện khảo sát, giá trị Macro-F1 đạt đỉnh tại điều kiện {{S2_BEST_CONDITION}}. Các kết quả này phản ánh đặc tính thực nghiệm của mô hình gpt-5.6-luna khi tiếp nhận danh sách ứng viên từ mô hình nhúng sentence-transformers/all-MiniLM-L6-v2 (chiều vector 384, chỉ mục FAISS IndexFlatIP) đã đóng băng trong config/retrieval.json, cho thấy biên độ cải thiện có xu hướng điều chỉnh khi số lượng ứng viên tăng lên."

---

### 2.3 Slide 8: Kết Quả RQ2 - Phân Rã Lỗi Độc Lập D2i & Đánh Giá Có Điều Kiện

*Objective:* Populate the complete 5-axis independent error decomposition and retrieval-conditional accuracy probabilities from native evaluator JSON outputs in `outputs/canonical_evaluation/`.

| Placeholder Key | Source Path / JSON Pointer | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_RETRIEVAL_MISS_RATE_K10}}` | `failure_decomposition.json -> /by_condition/rag_k10/retrieval_miss_rate` | Trục 1: Ground-truth absent rate in Top-10 candidates. |
| `{{S2_PROVIDER_FAIL_RATE_K10}}` | `failure_decomposition.json -> /by_condition/rag_k10/provider_failure_rate` | Trục 2: Provider failure / API timeout rate. |
| `{{S2_PARSE_FAIL_RATE_K10}}` | `failure_decomposition.json -> /by_condition/rag_k10/parse_failure_rate` | Trục 3: Model JSON schema parsing failure rate. |
| `{{S2_INVALID_ATTACK_ID_RATE_K10}}`| `failure_decomposition.json -> /by_condition/rag_k10/invalid_attack_id_rate` | Trục 4: Syntax regex or v19.2 registry invalidity rate. |
| `{{S2_WRONG_CLASS_RATE_K10}}` | `failure_decomposition.json -> /by_condition/rag_k10/valid_but_wrong_classification_rate` | Trục 5: Valid ATT&CK ID but wrong technique attribution rate. |
| `{{S2_OVERLAP_MISS_AND_WRONG_K10}}`| `failure_decomposition.json -> /by_condition/rag_k10/overlap_retrieval_miss_and_wrong_classification` | Raw count of records where retrieval missed AND downstream classification was wrong. |
| `{{S2_P_CORRECT_GIVEN_RETRIEVED}}`| `retrieval_conditional_metrics.json -> /by_condition/rag_k10/P_correct_given_retrieval_success` | Downstream accuracy given ground truth is present in Top-k. |
| `{{S2_P_CORRECT_GIVEN_ABSENT}}` | `retrieval_conditional_metrics.json -> /by_condition/rag_k10/P_correct_given_retrieval_failure` | Correct attribution despite GT absent from retrieved Top-k. |
| `{{S2_NO_RAG_RETRIEVAL_STATUS}}` | Evaluator invariant | Displayed as `N/A` (retrieval is not applicable at $k=0$; count = 0 reflects absence of applicability, not zero failure). |

#### Target Content Outline (Slide 8):
- **Phân Rã 5 Trục Thất Bại Độc Lập D2i ($k=10$):**
  - **Trục 1 (Retrieval Miss):** `{{S2_RETRIEVAL_MISS_RATE_K10}}` (kỹ thuật đúng vắng mặt trong Top-10 ứng viên được truy xuất).
  - **Trục 2 (Provider Failure):** `{{S2_PROVIDER_FAIL_RATE_K10}}` (lỗi kết nối hoặc timeout dịch vụ nhà cung cấp).
  - **Trục 3 (Parse Failure):** `{{S2_PARSE_FAIL_RATE_K10}}` (lỗi giải mã cấu trúc JSON từ đầu ra mô hình).
  - **Trục 4 (Invalid ATT&CK ID):** `{{S2_INVALID_ATTACK_ID_RATE_K10}}` (mã sinh ra sai cú pháp hoặc không tồn tại trong registry v19.2).
  - **Trục 5 (Valid but Wrong Classification):** `{{S2_WRONG_CLASS_RATE_K10}}` (mã sinh ra hợp lệ nhưng sai kỹ thuật mục tiêu).
  - **Số đếm giao thoa (Overlap Miss & Wrong):** `{{S2_OVERLAP_MISS_AND_WRONG_K10}}` trường hợp đồng thời vừa trượt truy xuất vừa sai phân loại (tương ứng với trường `overlap_retrieval_miss_and_wrong_classification`).
  - *Ghi chú phương pháp luận về `no_rag`:* Điều kiện `no_rag` không áp dụng khâu truy xuất, do đó các chỉ số điều kiện truy xuất được ghi nhận là `N/A` (giá trị 0 trong `failure_decomposition.json` là do không kích hoạt bộ truy xuất, không phải là tỷ lệ lỗi truy xuất bằng 0).
- **Xác Suất Phân Loại Có Điều Kiện ($k=10$):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}10)$: `{{S2_P_CORRECT_GIVEN_RETRIEVED}}` (đo lường độ chính xác khi ứng viên đúng có mặt trong Top-10).
  - $P(\text{Correct} \mid \text{GT Absent from Top-}10)$: `{{S2_P_CORRECT_GIVEN_ABSENT}}` (đo lường khả năng định danh đúng dù kỹ thuật mục tiêu vắng mặt trong Top-k được truy xuất - *Correct attribution despite GT absent from retrieved Top-k*).

#### Speaker Notes Update (Slide 8):
> "GHI CHÚ DIỄN GIẢ (Slide 8):  
> Tại Slide 8, khung đánh giá D2i bóc tách đầy đủ 5 trục lỗi độc lập trong quy trình thực nghiệm: (1) Retrieval miss chiếm {{S2_RETRIEVAL_MISS_RATE_K10}}, (2) Provider failure chiếm {{S2_PROVIDER_FAIL_RATE_K10}}, (3) Parse failure chiếm {{S2_PARSE_FAIL_RATE_K10}}, (4) Invalid ATT&CK ID chiếm {{S2_INVALID_ATTACK_ID_RATE_K10}}, và (5) Phân loại sai dù mã hợp lệ chiếm {{S2_WRONG_CLASS_RATE_K10}}. Số trường hợp đồng thời vừa trượt truy xuất vừa sai phân loại ghi nhận là {{S2_OVERLAP_MISS_AND_WRONG_K10}} mẫu. Khảo sát chỉ số điều kiện khách quan cho thấy: khi kỹ thuật mục tiêu nằm trong danh sách Top-10, xác suất dự đoán đúng P(Correct | Retrieved) đạt {{S2_P_CORRECT_GIVEN_RETRIEVED}}; trong khi đó, xác suất định danh đúng dù kỹ thuật mục tiêu vắng mặt trong Top-10 được truy xuất (Correct attribution despite GT absent from retrieved Top-k) ghi nhận ở mức {{S2_P_CORRECT_GIVEN_ABSENT}}. Sự khác biệt thực nghiệm này phản ánh rõ nét mức độ tương quan giữa danh mục ứng viên được gợi ý và kết quả định danh sau cùng."

---

### 2.4 Slide 9: Kết Quả RQ3 - Đánh Đổi Tài Nguyên & Phân Tích Cặp Biểu Diễn Đối Ứng

*Objective:* Present the Pareto evaluation (Cost vs. Latency vs. Accuracy) and strictly disentangle marginal view distributions from paired cohort metrics on the 278 complete scorable pairs in the TEST split (source: `outputs/canonical_analysis/rq_analysis.json`).

| Placeholder Key | Source Path / Method | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_PARETO_OBSERVED_TRADE_OFF}}`| Computed from cost, latency, Macro-F1 across 5 conditions | The empirical balance point across $(k \in \{0, 1, 3, 5, 10\})$. |
| `{{S2_EST_COST_PER_REQ_K10}}` | Aggregated from `request_journal.jsonl` / `pricing_v1.json` | Average accounted cost per query at $k=10$. |
| `{{S2_EST_COST_PER_REQ_NO_RAG}}`| Aggregated from `request_journal.jsonl` / `pricing_v1.json` | Average accounted cost per query at $k=0$. |
| `{{S2_LATENCY_RATIO_K10_VS_K0}}`| Computed: `mean_latency(rag_k10) / mean_latency(no_rag)` | Ratio of per-record latency increase from No-RAG to RAG $k=10$. |
| `{{S2_TOTAL_TEST_PAIRS}}` | `config/experiment_config.json -> dataset.expected_pair_count` | Pinned count: `640` pairs (1,280 views in TEST split). |
| `{{S2_COMPLETE_SCORABLE_PAIRS}}`| Secondary paired analysis (`rq_analysis.json`) | Exactly `278` complete scorable pairs (both single & contextual have valid mapped GT). |
| `{{S2_CONTEXTUAL_ONLY_PAIRS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `162` pairs with only contextual view mapped. |
| `{{S2_NEITHER_MAPPED_PAIRS}}` | Secondary paired analysis (`rq_analysis.json`) | Exactly `200` pairs with neither view mapped (278 + 162 + 200 = 640). |
| `{{S2_MARGINAL_SINGLE_VIEW_ACC}}`| Marginal evaluation across all 278 single views | End-to-end attribution accuracy across ALL 278 single views with valid GT. |
| `{{S2_MARGINAL_CONTEXT_VIEW_ACC}}`| Marginal evaluation across all 440 contextual views | End-to-end attribution accuracy across ALL 440 contextual views with valid GT. |
| `{{S2_PAIRED_IDENTICAL_GT_PAIRS}}`| Cohort composition (`rq_analysis.json`) | Exactly `238` pairs where single and contextual views share IDENTICAL ground truth. |
| `{{S2_PAIRED_DIVERGENT_GT_PAIRS}}`| Cohort composition (`rq_analysis.json`) | Exactly `40` pairs where single and contextual views have DIFFERENT ground truth. |
| `{{S2_PAIRED_SINGLE_ACC}}` | Computed on 278 complete pairs: `(both_corr + single_only) / 278` | Single-view attribution accuracy within the 278 complete scorable pairs cohort. |
| `{{S2_PAIRED_CONTEXT_ACC}}`| Computed on 278 complete pairs: `(both_corr + context_only) / 278`| Contextual-view attribution accuracy within the 278 complete scorable pairs cohort. |
| `{{S2_PAIRED_DELTA_PP}}` | Computed: `(PAIRED_SINGLE_ACC - PAIRED_CONTEXT_ACC) * 100` | Net attribution accuracy delta on the 278 complete scorable pairs in percentage points (`pp`). |
| `{{S2_PAIRWISE_WIN_RATE_SINGLE}}`| Computed: `single_only_correct / 278` | Win rate where Single is correct and Contextual is incorrect across 278 pairs. |
| `{{S2_PAIRWISE_WIN_RATE_CONTEXT}}`| Computed: `contextual_only_correct / 278` | Win rate where Contextual is correct and Single is incorrect across 278 pairs. |
| `{{S2_PAIRWISE_BOTH_CORRECT_RATE}}`| Computed: `both_correct / 278` | Proportion of pairs where both representations are correct across 278 pairs. |
| `{{S2_PAIRWISE_BOTH_INCORRECT_RATE}}`| Computed: `both_incorrect / 278` | Proportion of pairs where both representations are incorrect across 278 pairs. |

#### Target Content Outline (Slide 9):
- **Phân Tích Đánh Đổi Kinh Tế Kỹ Thuật (Cost - Latency - Accuracy):**
  - Chi phí hạch toán trung bình tăng từ `{{S2_EST_COST_PER_REQ_NO_RAG}}` USD (no_rag) lên `{{S2_EST_COST_PER_REQ_K10}}` USD (rag_k10).
  - Độ trễ logic trung bình tăng `{{S2_LATENCY_RATIO_K10_VS_K0}}`x giữa điều kiện no_rag và rag_k10.
  - Tương quan hiệu năng trên chi phí: Xu hướng biên độ cải thiện Macro-F1 so với tốc độ tiêu hao token khi $k$ tăng từ 1 đến 10.
- **Phân Biệt Rạch Ròi Hai Lớp Đo Lường Biểu Diễn:**
  - **Lớp 1: Phân Phối Biên (Marginal View Accuracy - Kích thước mẫu không bằng nhau, không so sánh nhân quả):**
    * Độ chính xác trên toàn bộ 278 Single views có nhãn hợp lệ: `{{S2_MARGINAL_SINGLE_VIEW_ACC}}`.
    * Độ chính xác trên toàn bộ 440 Contextual views có nhãn hợp lệ: `{{S2_MARGINAL_CONTEXT_VIEW_ACC}}` (278 cặp hoàn chỉnh + 162 cặp chỉ có Contextual = 440 views).
    * *Cảnh báo phương pháp luận:* Tuyệt đối không nhầm lẫn giá trị 440 Contextual views này là độ chính xác của nhóm 278 cặp đối ứng!
  - **Lớp 2: Đánh Giá Đối Ứng Cặp Chuẩn (Paired Cohort Analysis trên 278 Cặp Hoàn Chỉnh):**
    * Thành phần cấu tạo 278 cặp hoàn chỉnh: `238` cặp có ground-truth trùng khớp hoàn toàn (`{{S2_PAIRED_IDENTICAL_GT_PAIRS}}`), và `40` cặp có ground-truth khác biệt (`{{S2_PAIRED_DIVERGENT_GT_PAIRS}}`). Nghiên cứu báo cáo đầy đủ toàn bộ 278 cặp, không âm thầm loại bỏ 40 cặp có nhãn khác biệt.
    * Độ chính xác nội bộ nhóm 278 cặp: Single view = `{{S2_PAIRED_SINGLE_ACC}}` vs Contextual view = `{{S2_PAIRED_CONTEXT_ACC}}` (chênh lệch paired delta: `{{S2_PAIRED_DELTA_PP}}` pp).
    * Phân loại 4 trạng thái đối đầu trên 278 cặp:
      - Chỉ Single đúng: `{{S2_PAIRWISE_WIN_RATE_SINGLE}}` (`single_only_correct`).
      - Chỉ Contextual đúng: `{{S2_PAIRWISE_WIN_RATE_CONTEXT}}` (`contextual_only_correct`).
      - Cả hai cùng đúng: `{{S2_PAIRWISE_BOTH_CORRECT_RATE}}` (`both_correct`).
      - Cả hai cùng sai: `{{S2_PAIRWISE_BOTH_INCORRECT_RATE}}` (`both_incorrect`).

#### Speaker Notes Update (Slide 9):
> "GHI CHÚ DIỄN GIẢ (Slide 9):  
> Slide 9 trình bày hai bình diện đo lường: đánh đổi tài nguyên và phân tích đối ứng hình thức biểu diễn log. Về tài nguyên, khi tăng k từ 0 lên 10, chi phí hạch toán trung bình tăng từ {{S2_EST_COST_PER_REQ_NO_RAG}} USD lên {{S2_EST_COST_PER_REQ_K10}} USD cùng độ trễ logic tăng {{S2_LATENCY_RATIO_K10_VS_K0}} lần. Về hình thức biểu diễn, nghiên cứu phân biệt rạch ròi giữa hai lớp số liệu: (1) Phân phối biên thuần túy ghi nhận độ chính xác trên toàn bộ 278 single views đạt {{S2_MARGINAL_SINGLE_VIEW_ACC}} và trên toàn bộ 440 contextual views đạt {{S2_MARGINAL_CONTEXT_VIEW_ACC}}; đây là hai mẫu có quy mô khác nhau và không mang ý nghĩa so sánh nhân quả trực tiếp. (2) Đánh giá đối ứng cặp được kiểm soát chặt chẽ trên đúng 278 cặp hoàn chỉnh có đủ nhãn ở cả hai góc nhìn (trong đó 238 cặp có nhãn trùng khớp và 40 cặp có nhãn khác biệt được báo cáo đầy đủ, minh bạch). Trên cohort 278 cặp này, độ chính xác của Single đạt {{S2_PAIRED_SINGLE_ACC}} so với {{S2_PAIRED_CONTEXT_ACC}} của Contextual, tạo mức chênh lệch {{S2_PAIRED_DELTA_PP}} điểm phần trăm (pp). Tỷ lệ đối đầu ghi nhận Single thắng trong {{S2_PAIRWISE_WIN_RATE_SINGLE}} số cặp, Contextual thắng trong {{S2_PAIRWISE_WIN_RATE_CONTEXT}}, cả hai cùng đúng chiếm {{S2_PAIRWISE_BOTH_CORRECT_RATE}}, và cả hai cùng sai chiếm {{S2_PAIRWISE_BOTH_INCORRECT_RATE}}."

---

### 2.5 Slide 10: Đóng Góp Cốt Lõi, Hạn Chế & Ranh Giới Dữ Liệu (Scope & Limitations)

*Objective:* Frame findings strictly within empirical benchmark boundaries (`synthetic-paired-v1`) and outline technical trade-offs objectively.

| Placeholder Key | Source Path / Method | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_BENCHMARK_TOTAL_VIEWS}}` | `data/ground_truth/synthetic/dataset_manifest.json -> total_views` | Full synthetic benchmark views: `1,340` (1,280 TEST + 60 DEV). |
| `{{S2_TEST_SPLIT_VIEWS}}` | `config/experiment_config.json -> dataset.expected_sample_count` | Canonical test split views: `1,280` (640 pairs). |
| `{{S2_T20_DIAGNOSTIC_VIEWS}}` | `artifacts/analysis/t20_retrieval_failure_summary.json` | 756 positive views evaluated across full Stage B benchmark (Hit@10 = 45.11%). |
| `{{S2_SEMANTIC_GAP_TECHNIQUE}}` | Historical retrieval observation | `T1136.001` (Create Account: Local Account) exhibiting 0% Hit@10 under dense semantic search. |

#### Target Content Outline (Slide 10):
- **Bốn Đóng Góp Phương Pháp Luận Cốt Lõi:**
  1. *Quy trình đối chứng kiểm soát rò rỉ dữ liệu:* Thiết lập phương pháp thẩm định chặt chẽ, ngăn chặn rò rỉ thông tin ground-truth trong quy trình đánh giá log Windows.
  2. *Khung phân rã lỗi 5 trục D2i:* Định lượng độc lập 5 trục thất bại: retrieval miss, provider failure, parse failure, invalid ID, wrong classification cùng số đếm giao thoa.
  3. *Đo lường đánh đổi tài nguyên:* Cung cấp số liệu định lượng về tương quan giữa số lượng token, độ trễ và biên độ thay đổi Macro-F1 qua các độ sâu $k$.
  4. *Khảo sát thực nghiệm về khoảng cách biểu diễn:* Cung cấp dữ liệu đối đầu trên 278 cặp kịch bản hoàn chỉnh với phân định rạch ròi giữa phân phối biên (278 vs 440 views) và đánh giá đối ứng cặp nội bộ.
- **Ranh Giới Dữ Liệu & Hướng Nghiên Cứu Mở Rộng:**
  - *Ranh giới tập dữ liệu:* Toàn bộ các kết luận thực nghiệm được đóng khung trên tập dữ liệu kiểm soát `synthetic-paired-v1` (1,280 views tập TEST; 1,340 views toàn bộ benchmark), chưa khái quát hóa sang các hệ thống log SOC thực địa với lưu lượng phân tán lớn.
  - *Đặc tính của mô hình nhúng ngữ nghĩa đơn tầng:* Khảo sát chẩn đoán T20 trên 756 mẫu dương tính toàn benchmark ghi nhận tỷ lệ vắng mặt trong Top-10 đạt 54.89% (Hit@10 = 45.11%), trong đó một số kỹ thuật chứa định danh số như `T1136.001` (Event ID 4720) đạt 0% Hit@10. Dữ liệu thực nghiệm này gợi mở tính khả thi của việc kết hợp phương pháp tìm kiếm lai (Hybrid Search: Dense Semantic + Từ khóa/BM25) trong các nghiên cứu tiếp theo.

#### Speaker Notes Update (Slide 10):
> "GHI CHÚ DIỄN GIẢ (Slide 10):  
> Slide 10 tổng kết các đóng góp phương pháp luận và nhấn mạnh ranh giới khoa học của đề tài: mọi kết luận đều được rút ra từ tập kiểm chuẩn synthetic-paired-v1 với 1,280 mẫu kiểm tra chính thức và chưa suy diễn vượt ranh giới này sang môi trường thực địa. Nghiên cứu cũng chỉ ra rằng việc chỉ sử dụng một tầng mô hình nhúng ngữ nghĩa dense embedding (sentence-transformers/all-MiniLM-L6-v2) bộc lộ hạn chế đối với các định danh hệ thống đặc thù (như Event ID trong T1136.001 với 0% Hit@10 trong chẩn đoán T20). Đây là cơ sở thực nghiệm rõ ràng để đề xuất việc khảo sát các kiến trúc Hybrid Search kết hợp từ khóa trong các công trình nghiên cứu tiếp theo."

---

## 3. Presentation Authoring Compliance Requirements

To satisfy strict quality control gates and prevent slide deck corruption during Phase S2 delivery:

### 3.1 Documented JS Artifact-Tool API Pipeline
- **Core Directive:** The production presentation slide deck (`docs/presentation/slides.pptx`) **MUST** be finalized and updated using the documented JavaScript APIs of `@oai/artifact-tool`.
- **Verified API Workflow:**
  In accordance with `API_QUICK_START.md` and `references/implementation.md` in the primary presentation skill:
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
| :---: | :--- | :--- | :--- :
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

- **Status:** PLAN-ONLY PENDING CODEX APPROVAL (UNIFIED_MAPPING_R2 Remediation)  
- **Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
- **PRE_SHA:** `55494a433cc70f15f253e34742d5bda2a4762565`  
- **Output Document Path:** `reports/evidence/s2_presentation_and_repro_plan.md`  
- **Safety Guarantee:** Live runner PID 50192 running undisturbed; zero mock findings promoted to canonical status; zero live provider calls; no destructive modifications to repo source or config files.
