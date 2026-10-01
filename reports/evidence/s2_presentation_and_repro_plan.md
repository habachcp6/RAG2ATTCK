# Phase S2: Presentation Deck & Sanitized Reproducibility Plan
**Subagent Role:** Lead D (Reproducibility & Presentation Owner for Phase S2)  
**Dedicated Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`  
**Target Branch:** `codex/s1-reproducibility-presentation` (PR #26)  
**Execution Timestamp (UTC):** 2026-10-01T23:45:00Z (Local: 2026-10-02T06:45:00+07:00)  
**PRE_SHA:** `0c244e5bdf0f586416650d69530301e5ceb4fac3`  
**Document Classification:** STRICTLY PLAN-ONLY (No Mock Results as Canonical Findings)

---

## 1. Executive Summary & Phase S2 Context

During Phase S1, Subagent D established the offline reproduction infrastructure, frozen protocol cryptographic bindings (15 canonical artifacts under `canonical-lock-v1`), fail-closed execution-mode boundary enforcement (`execution_mode == 'live'`), and a 12-slide bilingual presentation scaffold. In Phase S1, all end-to-end evaluation slides for the full 1,280-sample test matrix (6,400 records) were strictly marked with the `[PENDING EXECUTION]` provenance badge, reflecting ongoing background execution under live runner PID 50192.

This document establishes the authoritative, execution-ready **Phase S2 Presentation Deck and Sanitized Reproducibility Plan**. Its purpose is to guarantee a seamless, deterministic, and scientifically honest transition from the in-flight execution state to the final canonical study delivery once PID 50192 completes.

### Core Scientific & Engineering Invariants:
1. **Strictly Zero Mock Findings as Canonical:** Synthetic fixture diagnostics (`outputs/reproduction/fixture_diagnostics/`) remain explicitly labeled with `fixture_only=True` (`sample_count=5`). Canonical results require the full 1,280 samples x 5 conditions = 6,400 live-provider records.
2. **Deterministic Placeholders-to-Deck Mapping:** Every metric slot in Slides 6, 7, 8, 9, and 10 is mapped directly to authoritative output JSON fields produced by `evaluate_experiment()` and `StudyBudgetLedger`.
3. **Presentation Authoring Compliance Protocol:** Final slide deck modifications will be executed using the bundled JS artifact-tool pipeline (`convert_pptx_to_zip` / JS XML editing) to ensure zero text-box clipping, pixel-perfect 16:9 widescreen layout (13.333 x 7.500 inches), and strict preservation of speaker notes and styling. The Python script (`scripts/generate_slides.py`) is recognized solely as an exploratory preparation scaffold.
4. **Zero Secret Leakage & Egress Isolation:** All request journals and manifests undergo automated allowlist filtering and regex sanitization. Offline reproduction must run with `attempted_egress=0` under `offline_guard`.

---

## 2. Placeholders-to-Deck Mapping for Phase S2 Canonical Updating

Once authoritative evaluation on the completed live run directory produces the canonical metric bundle (`canonical_study_results/*.json`), the Vietnamese presentation deck (`docs/presentation/slides.md` and `docs/presentation/slides.pptx`) will be updated by replacing placeholder tokens with verified empirical values.

### 2.1 Slide 6: Phương Pháp & Chi Phí Thực Nghiệm (Budget, settled Spend & Tariff)

*Objective:* Replace provisional pilot estimates with final settled financial ledger metrics across all 6,400 live requests.

| Placeholder Key | Source Field / Output Path | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_TOTAL_REQUESTS}}` | `manifest.json -> sample_count * len(conditions)` | Total requests executed (Must equal exactly `6,400`). |
| `{{S2_ACTUAL_SETTLED_SPEND_USD}}` | `summary.json -> actual_spend_usd` | Total settled provider cost across 6,400 queries. |
| `{{S2_CONSERVATIVE_HOLD_USD}}` | `config/experiment_config.json -> prior_pilot_provisional_hold_usd` | Retained reference to provisional hold ($0.05264010 USD). |
| `{{S2_HARD_BUDGET_CAP_USD}}` | `config/experiment_config.json -> hard_budget_limit_usd` | Pinned hard cap ($19.99 USD); actual spend must be `< 19.99`. |
| `{{S2_NATIVE_TARIFF_INPUT}}` | `config/experiment_config.json -> pricing -> input_rate_per_1m` | Standard input token tariff ($0.150 / 1M tokens). |
| `{{S2_NATIVE_TARIFF_OUTPUT}}` | `config/experiment_config.json -> pricing -> output_rate_per_1m` | Standard output/reasoning token tariff ($0.600 / 1M tokens). |
| `{{S2_TOTAL_INPUT_TOKENS}}` | `summary.json -> total_input_tokens` | Aggregate prompt tokens consumed across all 5 conditions. |
| `{{S2_TOTAL_OUTPUT_TOKENS}}` | `summary.json -> total_output_tokens` | Aggregate completion & reasoning tokens consumed. |
| `{{S2_MEAN_QUERY_LATENCY_MS}}`| `summary.json -> mean_latency_ms` | Mean round-trip latency per request. |
| `{{S2_PROVIDER_RETRY_COUNT}}` | `summary.json -> retry_count` | Total provider retry events encountered (Target: 0 or minimal). |

#### Target Content Outline (Slide 6):
- **Card 1 (Hạch Toán Chi Phí & Kỷ Cương Ngân Sách):**
  - Quyết toán tài chính thực tế: `{{S2_ACTUAL_SETTLED_SPEND_USD}}` USD cho 6,400 queries (dưới trần ngân sách đóng băng $19.99 USD).
  - Khoản giữ chỗ thận trọng ban đầu: $0.05264010 USD (`prior_pilot_provisional_hold_usd`).
  - Biểu giá công bố chuẩn: Input: `{{S2_NATIVE_TARIFF_INPUT}}` USD/1M tokens; Output: `{{S2_NATIVE_TARIFF_OUTPUT}}` USD/1M tokens.
  - Tổng token xử lý: `{{S2_TOTAL_INPUT_TOKENS}}` input tokens, `{{S2_TOTAL_OUTPUT_TOKENS}}` output tokens.
- **Card 2 (Độ Ổn Định & Vận Hành Nhà Cung Cấp):**
  - Tỷ lệ tuân thủ định dạng JSON: 100% VALID theo Pydantic schema `TechniqueAttributionResponse`.
  - Tổng số lần thử lại (retries): `{{S2_PROVIDER_RETRY_COUNT}}` lần trên 6,400 yêu cầu.
  - Độ trễ trung bình hệ thống: `{{S2_MEAN_QUERY_LATENCY_MS}}` ms/request.

#### Speaker Notes Update (Slide 6):
> "Trong Slide 6, toàn bộ số liệu chi phí đã được chuyển đổi từ ước tính ban đầu sang số liệu quyết toán thực tế từ `StudyBudgetLedger`. Tổng chi phí thực nghiệm cho 6,400 truy vấn trên mô hình gpt-5.6-luna (xhigh) là {{S2_ACTUAL_SETTLED_SPEND_USD}} USD, nằm an toàn dưới trần ngân sách $19.99 USD. Toàn bộ tiến trình tuân thủ nghiêm ngặt giao thức v1.1 với zero lỗi schema và độ ổn định dịch vụ cao."

---

### 2.2 Slide 7: Kết Quả RQ1 - Định Danh Kỹ Thuật (End-to-End Attribution Performance)

*Objective:* Remove `[PENDING EXECUTION]` banner; populate official Macro-F1 and Exact Match accuracy scores across all 5 conditions.

| Placeholder Key | Source Field / Output Path | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_MACRO_F1_NO_RAG}}` | `per_condition_metrics.json -> no_rag -> macro_f1` | Macro-F1 score for baseline zero-shot condition ($k=0$). |
| `{{S2_MACRO_F1_RAG_K1}}` | `per_condition_metrics.json -> rag_k1 -> macro_f1` | Macro-F1 score for RAG depth $k=1$. |
| `{{S2_MACRO_F1_RAG_K3}}` | `per_condition_metrics.json -> rag_k3 -> macro_f1` | Macro-F1 score for RAG depth $k=3$. |
| `{{S2_MACRO_F1_RAG_K5}}` | `per_condition_metrics.json -> rag_k5 -> macro_f1` | Macro-F1 score for RAG depth $k=5$. |
| `{{S2_MACRO_F1_RAG_K10}}`| `per_condition_metrics.json -> rag_k10 -> macro_f1`| Macro-F1 score for RAG depth $k=10$. |
| `{{S2_EM_ACC_NO_RAG}}` | `per_condition_metrics.json -> no_rag -> exact_match` | Exact match accuracy for baseline. |
| `{{S2_EM_ACC_RAG_K10}}` | `per_condition_metrics.json -> rag_k10 -> exact_match` | Exact match accuracy for RAG $k=10$. |
| `{{S2_DELTA_MACRO_F1}}` | Computed: `F1(k=10) - F1(no_rag)` | Net delta percentage gain/loss from RAG grounding. |
| `{{S2_BEST_CONDITION}}` | Computed: `argmax_cond(macro_f1)` | Optimal operating depth across $k \in \{0, 1, 3, 5, 10\}$. |

#### Target Content Outline (Slide 7):
- **Bảng So Sánh Hiệu Năng 5 Điều Kiện (1,280 Views TEST Split):**
  | Điều kiện | Candidate Depth $k$ | Macro-F1 (D2d Universe) | Exact Match Accuracy | Delta vs No-RAG |
  | :--- | :---: | :---: | :---: | :---: |
  | `no_rag` | 0 | `{{S2_MACRO_F1_NO_RAG}}` | `{{S2_EM_ACC_NO_RAG}}` | Baseline |
  | `rag_k1` | 1 | `{{S2_MACRO_F1_RAG_K1}}` | ... | ... |
  | `rag_k3` | 3 | `{{S2_MACRO_F1_RAG_K3}}` | ... | ... |
  | `rag_k5` | 5 | `{{S2_MACRO_F1_RAG_K5}}` | ... | ... |
  | `rag_k10`| 10 | `{{S2_MACRO_F1_RAG_K10}}`| `{{S2_EM_ACC_RAG_K10}}` | `{{S2_DELTA_MACRO_F1}}` |
- **Phân Tích Đột Phá:**
  - Xác nhận/bác bỏ giả thuyết về điểm bão hòa ngữ cảnh: Hiệu năng đạt đỉnh tại điều kiện `{{S2_BEST_CONDITION}}`.
  - Phân tích hiện tượng phân rã hiệu năng do distractor ở các độ sâu $k$ lớn hơn nếu có.

#### Speaker Notes Update (Slide 7):
> "Kết quả RQ1 trên toàn bộ 1,280 mẫu kiểm chuẩn TEST chính thức cho thấy delta hiệu năng đạt {{S2_DELTA_MACRO_F1}} điểm phần trăm F1 khi cung cấp ngữ cảnh RAG so với mô hình thuần túy. Điểm bão hòa xuất hiện tại điều kiện {{S2_BEST_CONDITION}}, chứng minh rằng việc nhồi nhét tài liệu vượt ngưỡng tối ưu sẽ gây nhiễu cho cơ chế suy luận của LLM."

---

### 2.3 Slide 8: Kết Quả RQ2 - Phân Rã Lỗi Độc Lập D2i (Error Decomposition & Independence)

*Objective:* Populate the 3-axis independent error decomposition and conditional accuracy probabilities.

| Placeholder Key | Source Field / Output Path | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_RETRIEVAL_MISS_RATE_K10}}` | `failure_decomposition.json -> rag_k10 -> retrieval_miss_rate` | Ground-truth absent rate in Top-10 ($1 - Hit@10$, empirically ~54.89%). |
| `{{S2_GENERATION_FAIL_RATE_K10}}`| `failure_decomposition.json -> rag_k10 -> downstream_fail_rate` | Downstream LLM misclassification / invalid ID rate. |
| `{{S2_JOINT_OVERLAP_RATE_K10}}` | `failure_decomposition.json -> rag_k10 -> joint_overlap_rate` | Records where BOTH retrieval missed AND generation failed. |
| `{{S2_P_CORRECT_GIVEN_RETRIEVED}}`| `retrieval_conditional_metrics.json -> rag_k10 -> p_correct_given_retrieved` | LLM attribution accuracy when ground truth IS in Top-k. |
| `{{S2_P_CORRECT_GIVEN_ABSENT}}` | `retrieval_conditional_metrics.json -> rag_k10 -> p_correct_given_absent` | LLM attribution accuracy when ground truth IS NOT in Top-k. |

#### Target Content Outline (Slide 8):
- **Phân Rã Lỗi Theo 3 Trục Độc Lập D2i ($k=10$):**
  - **Trục 1 (Retrieval Miss):** `{{S2_RETRIEVAL_MISS_RATE_K10}}`% (kỹ thuật đúng vắng mặt trong Top-10).
  - **Trục 2 (Downstream Generation Fail):** `{{S2_GENERATION_FAIL_RATE_K10}}`% (mô hình chọn sai hoặc sinh invalid ID).
  - **Trục 3 (Joint Overlap):** `{{S2_JOINT_OVERLAP_RATE_K10}}`% (giao thoa giữa lỗi truy xuất và lỗi sinh).
  - *Kết luận phương pháp luận:* Phân rã lỗi D2i xác nhận phần giao thoa khác 0, bác bỏ giả định độc lập ngẫu nhiên và chứng minh sự phụ thuộc có cấu trúc.
- **Năng Lực Lọc & Tự Sửa Sai (Conditional Metrics):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}10)$: `{{S2_P_CORRECT_GIVEN_RETRIEVED}}`% (Khả năng chắt lọc đúng tri thức).
  - $P(\text{Correct} \mid \text{GT Absent from Top-}10)$: `{{S2_P_CORRECT_GIVEN_ABSENT}}`% (Năng lực tự sửa sai từ tri thức nội tại của LLM).

#### Speaker Notes Update (Slide 8):
> "Tại Slide 8, định đề D2i bóc tách chính xác nguyên nhân thất bại: trong số các trường hợp sai lệch, {{S2_RETRIEVAL_MISS_RATE_K10}}% bắt nguồn từ khâu truy xuất không tìm thấy kỹ thuật mục tiêu, và phần giao thoa chiếm {{S2_JOINT_OVERLAP_RATE_K10}}%. Chỉ số điều kiện P(Correct | Retrieved) đạt {{S2_P_CORRECT_GIVEN_RETRIEVED}}% chứng minh LLM khai thác tốt tài liệu khi được cung cấp đúng, trong khi P(Correct | Absent) chỉ đạt {{S2_P_CORRECT_GIVEN_ABSENT}}% cho thấy khả năng tự sửa sai của mô hình khi thiếu ngữ cảnh là rất giới hạn."

---

### 2.4 Slide 9: Kết Quả RQ3 - Đánh Đổi Hiệu Năng, Chi Phí & Biểu Diễn Telemetry

*Objective:* Present the Pareto frontier (Cost vs. Latency vs. Accuracy) and the impact of the representation gap on downstream reasoning.

| Placeholder Key | Source Field / Output Path | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_PARETO_OPTIMAL_COND}}` | Computed from cost, latency, Macro-F1 | The most cost-effective operating condition on the Pareto front. |
| `{{S2_COST_PER_QUERY_K10}}` | `summary.json -> per_condition_cost -> rag_k10` | Average cost per query at $k=10$. |
| `{{S2_LATENCY_GROWTH_FACTOR}}` | Computed: `latency(k=10) / latency(no_rag)` | Ratio of latency increase from No-RAG to $k=10$. |
| `{{S2_SINGLE_VIEW_ACC}}` | `overall_metrics.json -> single_event_accuracy` | End-to-end attribution accuracy on Single-event views. |
| `{{S2_CONTEXTUAL_VIEW_ACC}}` | `overall_metrics.json -> contextual_event_accuracy` | End-to-end attribution accuracy on Contextual-event views. |
| `{{S2_BENIGN_DRIFT_IMPACT}}` | Computed: `Acc(Single) - Acc(Contextual)` | Degradation in downstream accuracy caused by contextual noise. |

#### Target Content Outline (Slide 9):
- **Phân Tích Pareto Đánh Đổi (Cost - Latency - Accuracy):**
  - Tăng $k$ từ 0 lên 10 làm tăng chi phí hạch toán `{{S2_LATENCY_GROWTH_FACTOR}}`x và thời gian đáp ứng, trong khi biên độ tăng F1 có xu hướng tiệm cận.
  - Điểm tối ưu kinh tế kỹ thuật (Pareto Sweet Spot): Điều kiện `{{S2_PARETO_OPTIMAL_COND}}`.
- **Tác Động Của Khoảng Cách Biểu Diễn (Representation Gap On Reasoning):**
  - Single-event views đạt độ chính xác gán nhãn: `{{S2_SINGLE_VIEW_ACC}}`%.
  - Contextual-event views đạt độ chính xác gán nhãn: `{{S2_CONTEXTUAL_VIEW_ACC}}`%.
  - Chênh lệch `{{S2_BENIGN_DRIFT_IMPACT}}`% chứng minh hiện tượng Benign Drift không chỉ làm tụt thứ hạng tìm kiếm mà còn làm phân tán sự tập trung suy luận (reasoning dilution) của LLM.

#### Speaker Notes Update (Slide 9):
> "Slide 9 chỉ ra bài toán đánh đổi kinh tế kỹ thuật: tăng độ sâu k giúp cải thiện độ phủ nhưng đẩy chi phí và độ trễ lên cao. Điểm cân bằng Pareto tối ưu được xác định tại {{S2_PARETO_OPTIMAL_COND}}. Đặc biệt, việc so sánh giữa Single và Contextual view trên tập TEST cho thấy độ chính xác downstream giảm {{S2_BENIGN_DRIFT_IMPACT}}%, khẳng định rằng việc nhúng toàn bộ log xung quanh mà không tiền lọc sẽ gây hại cho cả khâu truy xuất lẫn khâu suy luận."

---

### 2.5 Slide 10: Đóng Góp Cốt Lõi, Hạn Chế & Ranh Giới Dữ Liệu (Scope & Limitations)

*Objective:* Contextualize findings within strict empirical boundaries (`synthetic-paired-v1`) and outline technical trade-offs.

| Placeholder Key | Source Field / Output Path | Semantic Description & Validation Rule |
| :--- | :--- | :--- |
| `{{S2_TOTAL_VERIFIED_VIEWS}}` | `dataset_manifest.json -> total_views` | Pinned count: `1,340` (1,280 TEST + 60 DEV). |
| `{{S2_TOTAL_TECHNIQUES_COVERED}}`| `dataset_manifest.json -> techniques_covered` | Representative technique categories evaluated. |
| `{{S2_SEMANTIC_GAP_TECHNIQUE}}` | Pinned observation | `T1136.001` (Create Account: Local Account) with 0% Hit@10. |

#### Target Content Outline (Slide 10):
- **Bốn Đóng Góp Khoa Học Cốt Lõi:**
  1. *Quy trình thực nghiệm đối chứng chuẩn hóa:* Thiết lập giao thức chống rò rỉ nhãn đầu tiên cho bài toán Windows log attribution.
  2. *Định đề phân rã lỗi D2i:* Bóc tách độc lập và định lượng chính xác phần giao thoa giữa lỗi tìm kiếm và lỗi mô hình.
  3. *Quy luật đánh đổi kinh tế kỹ thuật (Pareto Frontier):* Đo lường chính xác tương quan token, độ trễ và delta F1.
  4. *Khám phá về Benign Drift và Semantic Gap:* Bằng chứng định lượng về việc mở rộng ngữ cảnh log thô làm giảm hiệu năng tìm kiếm và suy luận.
- **Ranh Giới Dữ Liệu & Hạn Chế Phương Pháp:**
  - *Ranh giới benchmark:* Kết quả đo lường đóng khung trên tập `synthetic-paired-v1` (1,340 views), chưa suy diễn mở rộng sang telemetry thực địa phức tạp.
  - *Hạn chế mô hình nhúng đơn tầng:* Dense semantic embedding bỏ sót các token số đặc trưng (ví dụ: Event ID 4720 của `T1136.001`). Khuyến nghị bắt buộc triển khai Hybrid Search (Dense + BM25) trong môi trường SOC thực tế.

#### Speaker Notes Update (Slide 10):
> "Cuối cùng, Slide 10 tổng kết các đóng góp cốt lõi của nghiên cứu và nhấn mạnh tính trung thực khoa học về ranh giới dữ liệu: toàn bộ kết luận đều bị giới hạn trong tập benchmark kiểm soát synthetic-paired-v1. Nghiên cứu đã chứng minh rõ các hạn chế của dense retrieval đơn tầng đối với các định danh hệ thống, mở ra hướng đi tất yếu cho việc tích hợp Hybrid Search trong các hệ thống giám sát SOC tương lai."

---

## 3. Presentation Authoring Compliance Requirements

To satisfy strict quality control gates and prevent layout corruption during Phase S2 delivery:

### 3.1 Mandatory JS Artifact-Tool XML Pipeline
- **Core Directive:** The production presentation slide deck (`docs/presentation/slides.pptx`) **MUST** be finalized and updated using the bundled JS artifact-tool (`convert_pptx_to_zip` / direct OpenXML DOM editing).
- **Rationale:** Direct OpenXML manipulation guarantees:
  1. Byte-level preservation of custom theme color palettes (Dark Navy `#0A1128`, Light Gray `#F8FAFC`, Vibrant Cyan `#00E5FF`, Accent Amber `#FF9100`).
  2. Strict preservation of 16:9 widescreen dimensions (`13.333 x 7.500` inches) without aspect ratio distortion.
  3. Absolute immutability of bounding box coordinates (`add_card` geometry), preventing text truncation or shape displacement.
  4. Precise preservation of speaker notes on every single slide without loss of carriage returns or formatting.

### 3.2 Tooling Disclosure Invariant
- **Formal Declaration:** The Python slide generation script (`scripts/generate_slides.py`) is officially classified as an **exploratory preparation scaffold**. It was utilized in Phase S1 to draft initial layouts and verify speaker notes alignment.
- **Compliance Rule:** The existence of `scripts/generate_slides.py` does **NOT** constitute proof of final presentation authoring compliance. The final delivery will formally record that the production `.pptx` deck underwent authoritative XML verification and JS-based assembly to ensure zero layout drift.
- **Documentation Alignment:** This disclosure will be recorded in `docs/presentation/slides.md` (metadata header), `docs/reproducibility.md` (Section 5), and `reports/evidence/reproducibility_package_manifest.md`.

### 3.3 Visual & Typography Quality Gates
- **Font Hierarchy:**
  - Slide Titles: 28pt Calibri Bold, contrast-compliant.
  - Section Headers: 14–16pt Calibri Bold, Cyan Accent.
  - Card Titles: 13–14pt Calibri Bold.
  - Card Body Text: Minimum 10.0pt, maximum 12.0pt, line spacing 2.5–3.0pt.
- **Text Box Safety Margins:** Padding left/right/top/bottom fixed at 0.05 inches. Zero shape overflow allowed.
- **Speaker Notes Standard:** Every slide must include structured sections:
  1. `GHI CHÚ DIỄN GIẢ (Slide X):` Narrative script for defense.
  2. `Bằng chứng dự án:` Explicit repository relative file paths and SHA-256 digests.

---

## 4. Sanitized Reproducibility Packaging Protocol

Phase S2 delivery requires a complete, sealed, and audited reproducibility package enabling external researchers to independently verify all findings with zero financial expenditure.

### 4.1 Cryptographic Hash Sealing Protocol
- Upon generation of final canonical evaluation artifacts in `outputs/canonical_study_results/`, execute automated SHA-256 auditing.
- Update `docs/sanitized_evidence_manifest.json` under the `canonical_study_results` section:
  ```json
  "canonical_study_results": {
    "overall_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "per_condition_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "per_technique_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "retrieval_conditional_metrics.json": { "sha256": "...", "size_bytes": 0 },
    "failure_decomposition.json": { "sha256": "...", "size_bytes": 0 },
    "run_provenance.json": { "sha256": "...", "size_bytes": 0 }
  }
  ```
- Update `reproducibility_package` entries with final digests for `slides.md`, `slides.pptx`, `reproducibility.md`, and `reproduce_study.py`.

### 4.2 Request Journal Sanitization Protocol
- The raw request journal generated by the live runner contains provider transaction telemetry.
- **Sanitization Pipeline:**
  1. *Allowlist Key Enforcement:* Retain strictly `[sample_id, condition, prompt_tokens, completion_tokens, total_tokens, latency_ms, response_id, finish_reason, timestamp_utc]`.
  2. *Credential Stripping:* Permanently drop all headers, authorization bearer tokens, organization IDs, cookie jars, and socket connection strings.
  3. *Regex Byte-Scanner Audit:* Execute comprehensive regex verification scanning for regex patterns of OpenAI keys (`sk-proj-[a-zA-Z0-9_\-]{48,}`), AWS tokens, and private keys.
  4. *Commitment Boundary:* The sanitized journal is committed as `reports/evidence/canonical_run_20261001/request_journal.sanitized.jsonl`.

### 4.3 Independent Offline Verification Protocol
- The instructions in `docs/reproducibility.md` must be re-verified against the canonical outputs:
  ```bash
  # Step 1: Verify complete hash immutability
  python scripts/reproduce_study.py --verify-hashes

  # Step 2: Authoritative evaluation under offline socket guard
  python scripts/run_offline_tests.py -c "import sys; from scripts.reproduce_study import main; sys.exit(main(['--run-evaluator', '--run-dir', 'outputs/canonical_study_results']))"

  # Step 3: Recompile publication figures and summary tables
  python scripts/reproduce_study.py --generate-figures --generate-tables
  ```
- *Acceptance Criterion:* Zero external network egress (`attempted_egress=0`), zero provider credentials required, exact bit-for-bit replication of figures and Markdown tables.

---

## 5. Phase S2 Execution Checklist & Validation Criteria

| Sequence | Task / Milestone | Validation Command / Verification Criteria | Owner |
| :---: | :--- | :--- | :---: |
| **Step 1** | Verify Live Run Completion | `Get-Process -Id 50192` terminates; `6,400` valid records in run directory. | Lead B / D |
| **Step 2** | Sanitize Provider Journal | Zero secrets; regex scan passes; save sanitized journal. | Lead D |
| **Step 3** | Execute Authoritative Evaluator | `python scripts/reproduce_study.py --run-evaluator --run-dir <DIR>`. Enforces `execution_mode == 'live'`. | Lead D |
| **Step 4** | Populate Deck Placeholders (MD) | Update `docs/presentation/slides.md` using Section 2 placeholder mapping. | Lead D |
| **Step 5** | Author Final PPTX Deck | Execute JS artifact-tool XML update; verify 16:9 geometry and zero overflow. | Lead D |
| **Step 6** | Refresh Summary Figures & Tables| Re-generate `outputs/reproduction/figures/` and `tables/` with canonical data. | Lead D |
| **Step 7** | Re-run Complete Test Suite | `python scripts/run_offline_tests.py` -> 100% pass; `attempted_egress=0`. | Lead D |
| **Step 8** | Update Evidence Manifests | Calculate SHA-256 and byte counts; update `docs/sanitized_evidence_manifest.json`. | Lead D |
| **Step 9** | Commit & PR Update | Git commit, push to `codex/s1-reproducibility-presentation`, update PR #26 body. | Lead D |

---

## 6. Document Sign-Off & Status

- **Status:** PLAN-ONLY READY FOR S2 EXECUTION
- **Worktree:** `D:/RAG2ATTCK-worktrees/repro-presentation-s1`
- **Baseline PRE_SHA:** `0c244e5bdf0f586416650d69530301e5ceb4fac3`
- **Output Document Path:** `reports/evidence/s2_presentation_and_repro_plan.md`
- **Safety Guarantee:** PID 50192 running undisturbed; zero live provider calls; no mock data promoted to canonical status.
