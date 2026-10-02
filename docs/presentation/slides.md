# RAG2ATT&CK: Đánh Giá Tác Động Của Retrieval-Augmented Generation Dựa Trên MITRE ATT&CK Đối Với Ánh Xạ Windows Endpoint Logs

**Slide Deck & Presentation Scaffold for Scientific Defense & Technical Demonstration**  
*Mã giao thức thực nghiệm:* `experiment-protocol-v1.1` (SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`)  
*Khóa thực nghiệm chuẩn:* `canonical-lock-v1` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`)  
*Tài liệu hướng dẫn tái lập:* [`docs/reproducibility.md`](../reproducibility.md)  
*Bộ slide trình chiếu PowerPoint (16:9):* [`docs/presentation/slides.pptx`](slides.pptx)

---

## Slide 1: Trang Tiêu Đề (Title Slide)

### Nội dung trình chiếu
- **Tiêu đề chính:** Đánh Giá Tác Động Của MITRE ATT&CK-Grounded Retrieval-Augmented Generation Đối Với Việc Ánh Xạ Windows Endpoint Logs Sang ATT&CK Techniques
- **Tiêu đề tiếng Anh:** Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs (RAG2ATT&CK)
- **Tác giả:** Nhóm Nghiên Cứu RAG2ATT&CK
- **Phân loại nghiên cứu:** Thực nghiệm đối chứng có kiểm soát (Controlled Empirical Study)
- **Trạng thái kỹ thuật & pháp lý:**
  - Giao thức khoa học: `experiment-protocol-v1.1` (Frozen Protocol)
  - Khóa mật mã thực nghiệm: `canonical-lock-v1` (15 Canonical Artifacts Verified)
  - Khả năng tái lập: 100% Offline & Zero-Cost Verification (`scripts/reproduce_study.py`)

### Ghi chú diễn giả (Speaker Notes)
> "Kính thưa Hội đồng và các chuyên gia, hôm nay tôi xin trình bày báo cáo nghiên cứu RAG2ATT&CK: Đánh giá tác động của MITRE ATT&CK-grounded RAG đối với việc ánh xạ Windows endpoint logs sang ATT&CK techniques. Toàn bộ nghiên cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt dưới giao thức đóng băng experiment-protocol-v1.1, khóa mật mã 15 canonical artifacts, và có thể tái lập hoàn toàn ngoại tuyến với chi phí 0 đồng.
> 
> *Khai báo công cụ:* Toàn bộ slide deck này được tạo tự động bằng kịch bản Python `scripts/generate_slides.py` thông qua thư viện `python-pptx` định dạng 16:9 widescreen, được thẩm định hiển thị bằng các bundled artifact tools nội bộ.
> 
> *Bằng chứng dự án:* `config/canonical_experiment_lock_v1.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `reports/experiment_protocol_v1.md` (SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`); `scripts/reproduce_study.py`."

---

## Slide 2: Vấn Đề Nghiên Cứu & Động Lực (Problem Statement & Motivation)

### Nội dung trình chiếu
- **Bối cảnh An toàn Thông tin (SOC Monitoring):**
  - Nhật ký Windows Endpoint (Security Events, Sysmon) là tuyến phòng thủ then chốt của các Trung tâm Giám sát An ninh (SOC).
  - Ánh xạ nhật ký thô sang ma trận MITRE ATT&CK Enterprise là tiêu chuẩn vàng để xác định ý đồ và chiến thuật tấn công.
  - Quy trình thủ công đòi hỏi chuyên gia cấp cao, tốn thời gian và khó đáp ứng quy mô hàng triệu sự kiện mỗi ngày.
- **Thách thức của LLM trong Log Attribution:**
  - *Khoảng cách trừu tượng:* Nhật ký ở mức hệ thống chi tiết (Process GUID, CommandLine, ParentProcess, Hashes), trong khi ATT&CK Techniques mô tả hành vi ở mức khái niệm.
  - *Hiện tượng ảo giác (Hallucination):* LLM thuần túy dễ gán nhầm sang các kỹ thuật phổ biến hoặc phát sinh mã ATT&CK không có trong danh mục.
  - *Nhầm lẫn Sub-techniques:* Khó phân biệt giữa các kỹ thuật lân cận (ví dụ: `T1059.001` PowerShell vs `T1059.003` Command Shell; hoặc `T1059.009` Cloud API vs `T1218.012` Verclsid).
- **Động lực của RAG2ATT&CK:**
  - Thiết kế nghiên cứu thực nghiệm đối chứng có kiểm soát (Controlled Empirical Study).
  - Đo lường khách quan delta hiệu năng do RAG mang lại trên cùng mô hình LLM.
  - Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại (Classification Failure).
  - **Phạm vi tính xác định (Determinism Scope):** Áp dụng cho khâu tái tạo bộ dữ liệu, quy trình đánh giá ngoại tuyến và thứ tự tie-breaking.
  - **Biến thiên backend LLM & Chính sách D3:** Phản hồi và backend LLM có thể biến thiên (tham số `seed` không gửi qua giao thức mạng), được quản lý bởi chính sách siêu dữ liệu ràng buộc tem thời gian D3 (`timestamp-bound metadata policy`).
  - Tái lập ngoại tuyến chi phí 0 đồng với bộ `offline_guard` can thiệp tầng socket.

### Ghi chú diễn giả (Speaker Notes)
> "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này định lượng khách quan mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ, không phóng đại hiệu năng. Chúng tôi làm rõ phạm vi tính xác định (determinism): tính xác định áp dụng tuyệt đối cho khâu tái tạo bộ dữ liệu, quy trình thẩm định đánh giá ngoại tuyến và quy tắc xử lý thứ tự tie-breaking. Đối với mô hình LLM, phản hồi và backend mô hình thực tế có thể biến thiên do tham số seed không được truyền qua giao thức mạng; sự biến thiên này được theo dõi và ghi nhận chặt chẽ theo chính sách siêu dữ liệu ràng buộc tem thời gian D3 (timestamp-bound metadata policy).
> 
> *Bằng chứng dự án:* `docs/README_PROPOSED.md`; `config/canonical_experiment_lock_v1.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `reports/experiment_protocol_v1.md` (D3 policy); `tests/test_attack_id_validation.py`."

---

## Slide 3: Kiến Trúc Thực Nghiệm Đối Chứng (System Architecture)

### Nội dung trình chiếu
- **Hai nhánh thực nghiệm trên cùng dữ liệu đầu vào:**
  1. **Nhánh Cơ Sở (Baseline No-RAG):**
     $$\text{Windows Endpoint Log} \longrightarrow \text{Prompt} \longrightarrow \text{LLM} \longrightarrow \text{JSON (technique\_id)}$$
  2. **Nhánh Thử Nghiệm (Experimental RAG):**
     $$\text{Windows Log} \longrightarrow \text{Dense Retriever (FAISS)} \longrightarrow \text{Top-}k \text{ Docs} \longrightarrow \text{Prompt + Context} \longrightarrow \text{LLM} \longrightarrow \text{JSON}$$
- **Kiến trúc bộ truy xuất gọn nhẹ (Lightweight Retrieval Engine):**
  - *Knowledge Corpus:* 474 tài liệu ATT&CK v19.2 Enterprise Windows (`attack/corpus/enterprise-windows-v19.2.jsonl`).
  - *Embedding Model:* `sentence-transformers/all-MiniLM-L6-v2` (384 chiều, chuẩn hóa $L_2$).
  - *Index:* Flat Inner Product FAISS Index (`IndexFlatIP`, Cosine similarity).
  - *Độ sâu k:* Khảo sát có hệ thống $k \in \{1, 3, 5, 10\}$.
- **Các biến kiểm soát bất biến (Controlled Invariants):**
  - Cùng mô hình (`gpt-5.6-luna`), cùng cấu hình suy luận (`reasoning_effort=xhigh`, `api_interface=responses`).
  - Cùng cấu trúc Prompt template (`prompts/baseline_v1.txt`), chỉ khác biệt ở khối Context được chèn vào.
  - **Biến duy nhất thay đổi:** Bật (ON) hoặc Tắt (OFF) khối ngữ cảnh truy xuất ATT&CK.

### Ghi chú diễn giả (Speaker Notes)
> "Kiến trúc thực nghiệm đối chứng kiểm soát nghiêm ngặt biến số điều trị duy nhất: Retrieval ON vs OFF. Nhánh Baseline No-RAG và Experimental RAG dùng chung một mô hình gpt-5.6-luna (xhigh), cùng cấu trúc prompt template, và cùng schema JSON đầu ra. Bộ tìm kiếm sử dụng all-MiniLM-L6-v2 kết hợp FAISS IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows.
> 
> *Bằng chứng dự án:* `prompts/baseline_v1.txt` (SHA-256: `b751fde1ee33b03ebca935e478ffef3ff03ff8bcf440263309a039755ab0f7cf`); `attack/corpus/enterprise-windows-v19.2.jsonl` (SHA-256: `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75`); `config/experiment_config.json`; `tests/test_rag_pipeline.py`."

---

## Slide 4: Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ (Dataset Strategy & Anti-Leakage)

### Nội dung trình chiếu
- **Bộ dữ liệu chuẩn đóng băng Stage B (Frozen Stage B Benchmark):**
  - 670 cặp kịch bản (Scenario Pairs) $\rightarrow$ 1,340 biểu diễn đơn vị (Views).
  - Phân chia: 1,280 TEST Views và 60 DEV Views.
  - Phân loại biểu diễn:
    - *Single-event:* Một sự kiện đơn lẻ kích hoạt kỹ thuật tấn công mục tiêu.
    - *Contextual-event:* Sự kiện mục tiêu kèm nhật ký ngữ cảnh lân cận trên cùng máy trạm.
  - Độ bao phủ: 8 nhóm kỹ thuật mục tiêu đại diện cùng các mẫu âm tính / mơ hồ.
- **Giao thức chống rò rỉ nhãn nghiêm ngặt (Strict Anti-Label-Leakage):**
  - Đầu vào suy luận (`data/ground_truth/synthetic/inference.jsonl`) chỉ chứa 2 trường: `sample_id` và `endpoint_evidence`.
  - Toàn bộ nhãn mục tiêu, tên luật Sigma/Sysmon, Tactic name, và mô tả đều bị lọc bỏ thông qua allowlist (`INFERENCE_ALLOWLIST`).
- **Phân định phạm vi rõ ràng:**
  - Bộ dữ liệu Stage B là tài liệu chuẩn phục vụ kiểm định kỹ thuật và chẩn đoán truy xuất.
  - Nghiên cứu phân định rõ ràng giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.

### Ghi chú diễn giả (Speaker Notes)
> "Tập dữ liệu chuẩn đóng băng Stage B gồm 670 cặp kịch bản đối ứng (1,340 views), chia thành 1,280 TEST views và 60 DEV views. Giao thức chống rò rỉ nhãn áp dụng INFERENCE_ALLOWLIST nghiêm ngặt: đầu vào suy luận inference.jsonl chỉ chứa sample_id và endpoint_evidence; toàn bộ tên luật, mã technique và mô tả đều bị loại trừ tuyệt đối. Nghiên cứu phân định rõ ràng giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.
> 
> *Bằng chứng dự án:* `data/ground_truth/synthetic/inference.jsonl` (SHA-256: `90d5f59e64f669f9d7990520625906d40081d5aa112521c7bb5e2f750b3e5fbf`); `data/ground_truth/synthetic/pairs.json` (SHA-256: `079e57a441b18d12351bb9715fc4b0a43058a9ceb68a8670c5e7bfa5dbad3ca8`); `tests/test_benchmark_inputs.py`; `tests/test_synthetic_freeze.py`."

---

## Slide 5: Phương Pháp Luận, Mô Hình Đe Dọa & Giao Thức v1.1

### Nội dung trình chiếu
- **Mô hình đe dọa & Danh mục ATT&CK v19.2 (Threat Model & Corpus):**
  - Tiêu chuẩn danh mục: Pinned MITRE ATT&CK v19.2 Enterprise Windows (474 techniques/sub-techniques).
  - **Mã hóa giao thức chuẩn tắc (Giao thức v1.1):**
    - `D2d: FROZEN_BENCHMARK_UNIVERSE = 474` (không gian lớp mục tiêu cố định, Macro-F1 tính trên tập đóng băng).
    - `D2g: ALLOW_HISTORICAL` (chấp nhận mã lịch sử/thu hồi trong benchmark, báo cáo distinct counts, không silent remapping).
    - `D2e: invalid_id_as_failure` (`INCLUDE_IN_DENOMINATOR`, fail-closed khi mô hình sinh mã sai cú pháp hoặc ngoài danh mục).
    - `D2f: api_failure_as_failure` (`INCLUDE_IN_DENOMINATOR`, không loại trừ mẫu khi gặp lỗi mạng/API refusal/timeout).
    - `D2b-c: EXCLUDE` (loại trừ các mẫu ground-truth rỗng hoặc mơ hồ khỏi mẫu số đo lường).
    - `D1: RECORD_ONLY` (lưu vết đầy đủ toàn bộ phản hồi thô phục vụ kiểm toán độc lập; các trường thông tin đăng nhập, token và bí mật nhạy cảm đều được khử khuẩn / làm mờ trước khi lưu trữ, không lưu raw secrets).
- **Tiêu chí đánh giá cốt lõi & Kỷ cương thực nghiệm:**
  - **Bốn tiêu chí đo lường trọng tâm:**
    - `D2h: ANY_GT_RETRIEVED` (truy xuất thành công nếu có ít nhất 1 kỹ thuật mục tiêu trong Top-k).
    - `D2i: INDEPENDENT_AXES` (phân rã lỗi theo 3 trục đo lường độc lập, ghi nhận đầy đủ overlap, không giả định độc lập ngẫu nhiên).
    - `D2e: invalid_id_as_failure` (mã ATT&CK ảo giác tính là lỗi phân loại).
    - `D2f: api_failure_as_failure` (lỗi provider / gián đoạn API tính vào mẫu số).
  - **Kỷ cương thực nghiệm bất biến:**
    - `D3:` Khóa mô hình: `ALLOW_LATEST_WITH_TIMESTAMP_BINDING` (tem UTC thực tế).
    - `D4:` Thực thi tuần tự (`SEQUENTIAL_ONLY`), tuyệt đối không chạy song song.
    - `D5:` Chặn cứng ngân sách đóng băng (`HARD_CAP`, trần $19.99 USD).

### Ghi chú diễn giả (Speaker Notes)
> "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi D1-D7. Về mô hình đe dọa, danh mục kỹ thuật được neo tại STIX ATT&CK v19.2 Enterprise Windows (474 techniques theo quyết định D2d FROZEN_BENCHMARK_UNIVERSE). Chính sách D1 RECORD_ONLY lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập nhưng đảm bảo toàn bộ credentials và bí mật nhạy cảm đã được làm sạch / khử khuẩn (credentials and sensitive secrets sanitized/redacted), tuyệt đối không lưu lộ lọt bí mật. Điểm đặc biệt quan trọng là chính sách D2g ALLOW_HISTORICAL: các mã kỹ thuật lịch sử hoặc đã bị thu hồi có trong benchmark được chấp nhận và báo cáo dạng distinct observation count, không tự ý gán lại mã thay thế. Bốn tiêu chí đánh giá cốt lõi gồm D2h (ANY_GT_RETRIEVED cho multi-label), D2i (INDEPENDENT_AXES ghi nhận đầy đủ overlap giữa các trục đo lường độc lập), D2e (invalid_id_as_failure: invalid ID tính vào mẫu số), và D2f (api_failure_as_failure: lỗi mạng/API tính vào mẫu số) thiết lập nguyên tắc fail-closed nghiêm ngặt.
> 
> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`); `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` (SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`); `tests/test_experiment_evaluation.py`."

---

## Slide 6: Kết Quả RQ2 - Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)

### Nội dung trình chiếu
- **Chẩn đoán khâu truy xuất trên tập chuẩn tắc (CANONICAL TEST RETRIEVAL - Mẫu số N=718 canonical views):**
  - *Hit@10:* $44.71\%$ (321 / 718)
  - *Retrieval Miss Rate:* $55.29\%$ (397 / 718)
  - *Macro Recall@10:* $42.80\%$
- **Khoảng cách ngữ nghĩa (Semantic Gap) ở `T1136.001`:**
  - Kỹ thuật `T1136.001` (Create Account: Local Account) đạt **0% Top-10 Hit Rate (0 / 95 canonical TEST views)**.
  - *Ngữ cảnh hệ thống:* Nhật ký Windows Event ID 4720 nhấn mạnh từ ngữ hệ thống ("SamAccountName"), trong khi mô tả STIX ATT&CK nhấn mạnh mục tiêu chiến thuật ("persistence").
- **Bản chất nhãn yếu (Weak-Label Diagnostic):**
  - Retrieval miss không đồng nghĩa với vắng mặt hoàn toàn ngữ cảnh hữu ích.
  - Cơ chế ảnh hưởng tới downstream generation vẫn chưa được kiểm chứng sau khi hoàn thành so sánh, không khẳng định giả thuyết nhân quả.

### Ghi chú diễn giả (Speaker Notes)
> "Chẩn đoán độc lập khâu tìm kiếm (RQ2) đánh giá độc lập trên 718 canonical TEST views: Hit@10=44.71% (321/718), Retrieval Miss=55.29% (397/718), Macro Recall@10=42.80%. Điển hình là kỹ thuật T1136.001 đạt 0% Top-10 Hit Rate (0/95 canonical TEST views) do khoảng cách ngữ nghĩa giữa Event ID 4720 ('SamAccountName') và mô tả STIX ('persistence').
> 
> Bối cảnh lịch sử T20 pilot (N=756 views) trước đây ghi nhận: Hit@1=4.23%, Hit@3=16.80%, Hit@5=24.21%, Hit@10=45.11%, Miss=54.89%, Macro Recall@10=43.14%, Mean GT Rank khi trúng=5.21, và T1136.001 trúng 0/99. Chúng tôi nêu rõ Ground Truth vắng mặt trong retrieval là chẩn đoán nhãn yếu: Retrieval miss không đồng nghĩa với vắng mặt ngữ cảnh hữu ích, và cơ chế ảnh hưởng tới downstream generation vẫn chưa được kiểm chứng sau khi hoàn thành đợt so sánh, không khẳng định giả thuyết nhân quả.
> 
> *Bằng chứng dự án:* `outputs/reproduction/figures/fig_rq2_retrieval_hit_rates.png`; `outputs/reproduction/tables/table_1_retrieval_diagnostics.md`; `tests/test_retrieval_diagnostics.py`."

---

## Slide 7: Tác Động Của Hình Thức Biểu Diễn Telemetry (Representation Gap)

### Nội dung trình chiếu
- **Phân Tích 278 Cặp Hoàn Chỉnh Đầy Đủ Nhãn GT (Complete GT-Scorable Paired Views):**
  - Toàn bộ 474 frozen macro classes chỉ có **8 kỹ thuật** xuất hiện trong tập TEST GT (tổng 768 support instances trên 718 scorable views do 40 views đa nhãn multi-GT).
  - Phân tích cặp: **278 cặp đối sánh hoàn chỉnh** (238 cùng GT + 40 khác GT) phân bố trên **440 cụm** kịch bản.
  - Ở điều kiện **RAG $k=10$**, cả Single và Contextual view đều đạt độ chính xác quan sát được là **83.81%** (Paired Delta = 0.0 pp, McNemar $p = 1.0$).
  - Không suy diễn quan hệ nhân quả thuần túy khi nhãn thay đổi giữa các hình thức biểu diễn; kết luận ghi nhận quan sát mô tả độc lập trên ma trận TEST.
- **Hiện tượng Benign Drift khi mở rộng ngữ cảnh:**
  - Gom các sự kiện lân cận bổ sung nhiều token thông thường (Explorer, DNS, svchost).
  - Vector dense embedding bị kéo lệch về hành vi bình thường, làm tụt thứ hạng kỹ thuật tấn công.
- **Schema So Sánh Đối Chứng Scaffold `[PENDING EXECUTION]`:**
  - Đối chứng: Zero-Shot No-RAG vs Zero-Shot RAG ($k=1..10$) vs Prompt Scaffolds.

### Ghi chú diễn giả (Speaker Notes)
> "Tại Slide 7, phân tích 278 cặp hoàn chỉnh đầy đủ nhãn GT (238 cùng GT + 40 khác GT) phân bố trên 440 cụm kịch bản làm rõ cấu trúc ground truth support: toàn bộ 474 classes chỉ có 8 kỹ thuật xuất hiện trong tập TEST GT (768 support instances trên 718 scorable views do có 40 multi-GT views). Ở điều kiện RAG k=10, cả Single và Contextual view đều đạt 83.81% (paired delta = 0.0 pp, McNemar p = 1.0). Chúng tôi duy trì nhãn [PENDING EXECUTION] cho schema đối chứng scaffold, nghiêm cấm suy diễn quan hệ nhân quả thuần túy khi hình thức biểu diễn log thay đổi.
> 
> *Bằng chứng dự án:* `scripts/verify_t20_canonical_artifacts.py`; `outputs/reproduction/tables/table_4_pairwise_representation_comparison.md`; `tests/test_t20_canonical_artifacts.py`."

---

## Slide 8: Khung Đánh Giá End-to-End (RQ1) & Phân Rã Lỗi Theo 3 Trục Độc Lập D2i (RQ2) `[PENDING EXECUTION]`

### Nội dung trình chiếu
- **Bảng Đối Chứng Hiệu Năng RQ1 & Ranh Giới Khoa Học Bắt Buộc:**
  - *Hiệu năng quan sát được:* RAG $k=10$ đạt 571/718 (**79.53%**) vs No-RAG 560/718 (**77.99%**), Delta = **+1.53 pp** (+1.96% relative).
  - *Độ bất định thống kê:*
    - **Absolute Accuracy 95% CIs:** no_rag = [74.65%, 81.06%], k=1 = [72.84%, 79.53%], k=3 = [74.51%, 81.06%], k=5 = [75.63%, 82.03%], k=10 = [76.32%, 82.45%].
    - **Paired difference CIs vs No-RAG:** Toàn bộ khoảng tin cậy chênh lệch cặp đều chứa 0 (k=10 delta CI **[-2.355, +5.300] pp**; kiểm định McNemar thăm dò $p = 0.4223 > 0.05$).
  - *Kiểm định ý nghĩa:* McNemar test $p = 0.4223 > 0.05$ (không đạt ý nghĩa thống kê ở mức $\alpha = 0.05$).
  - *Quy chuẩn diễn đạt bắt buộc:* Mô tả $k=10$ là **"độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định"** (observed highest tested accuracy and uncertainty). **CẤM** tuyên bố "chiến thắng có ý nghĩa thống kê" hoặc "lợi ích vượt trội trong production".
  - *Macro-F1 (474 Frozen Universe):* $k=10$ đạt **0.0140** vs No-RAG **0.0126** (Delta +0.0014, có CI riêng; không dùng p-value của Accuracy thay cho Macro-F1).
- **Mô hình phân rã lỗi theo 3 trục đo lường độc lập (Định đề D2i):**
  - **Trục 1 - Retrieval Miss Rate:** Kỹ thuật ground-truth vắng mặt trong Top-k theo D2h `ANY_MATCH`.
  - **Trục 2 - Downstream Generation Failure:** Invalid ATT&CK ID (D2e), scorable provider failure = 0.0000 (0 / 718) quan sát thực nghiệm (kết hợp 13 INCOMPLETE trên toàn bộ 6,400 dispatches), hoặc phân loại sai (Wrong Classification).
  - **Trục 3 - Joint Overlap:** Ghi nhận rõ các bản ghi vừa trượt truy xuất vừa lỗi phân loại (không giả định độc lập ngẫu nhiên).
- **Các thước đo có điều kiện (Conditional Metrics):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}k) = 91.28\%$ (293 / 321) tại $k=10$: Đánh giá lựa chọn khi có ngữ cảnh trúng.
  - $P(\text{Correct} \mid \text{GT Absent from Top-}k) = 70.03\%$ (278 / 397) tại $k=10$: Xác suất gán đúng quan sát được khi vắng mặt ngữ cảnh trong Top-k (không suy diễn tự sửa sai nội tại).
- **Trạng thái thực nghiệm RQ1 & RQ2 `[PENDING EXECUTION]`:**
  - Kiểm định toán học Evaluator đã xác thực ngoại tuyến qua các test fixtures chuẩn tắc.

### Ghi chú diễn giả (Speaker Notes)
> "Tại Slide 8, bảng đối chứng RQ1 ghi nhận RAG k=10 đạt độ chính xác quan sát được cao nhất là 79.53% (571/718) so với No-RAG 77.99% (560/718), tức Delta = +1.53 pp. Cần phân biệt rõ: Các khoảng tin cậy liệt kê trên bảng là Absolute Accuracy 95% CIs (no_rag [74.65%, 81.06%], k10 [76.32%, 82.45%]); trong khi toàn bộ khoảng tin cậy chênh lệch cặp (paired difference CIs vs No-RAG) đều chứa 0 (khoảng tin cậy delta của RAG k=10 là [-2.355, +5.300] pp, kiểm định McNemar cho p = 0.4223 > 0.05). Do đó, nghiên cứu khẳng định đây là 'độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định', tuyệt đối không tuyên bố chiến thắng có ý nghĩa thống kê hay lợi ích vượt trội trong production.
> 
> Quan sát thực nghiệm ghi nhận scorable provider failure = 0.0000 (0/718) trên các bản ghi scorable, kết hợp với 13 INCOMPLETE trên toàn bộ 6,400 dispatches. Về các thước đo có điều kiện tại k=10: P(Correct | GT in Top-k) = 91.28% (293/321), trong khi P(Correct | GT absent Top-k) = 70.03% (278/397); tỷ lệ này không cho phép suy diễn mô hình tự sửa sai nội tại.
> 
> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (D2e, D2f, D2h, D2i; SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`); `tests/test_experiment_evaluation.py`."

---

## Slide 9: Nghiên Cứu Tiêu Thụ Tài Nguyên & Hạch Toán Tài Chính Toàn Nghiên Cứu (RQ3)

### Nội dung trình chiếu
- **Phân Tích Tài Nguyên và Chi Phí Chuẩn Tắc (TEST 718) [CANONICAL STUDY]:**
  - Chi phí được tính theo **ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate)**:
    - *No-RAG:* **$0.000365 USD** / logical query (TB 674.3 prompt tokens; trễ trung vị 2,303 ms; TB 2.90s).
    - *RAG $k=10$:* **$0.001679 USD** / logical query (TB 5114.3 prompt tokens; trễ trung vị 2,667 ms; TB 4.37s).
  - *Bối cảnh phụ:* DEV pilot 20 requests sơ bộ (~$0.0242 USD) phân tách tuyệt đối khỏi tập TEST.
- **Đánh Đổi Hiệu Năng - Chi Phí Chuẩn Tắc (No-RAG vs RAG $k=10$):**
  - *Hit rate chuẩn tắc (TEST 718):* RAG $k=1$ đạt **3.760%** $\rightarrow$ RAG $k=10$ đạt **44.708%** (No-RAG: **N/A**, không sử dụng retriever).
  - *Prompt tokens:* Tăng **~7.6x** từ baseline đến $k=10$ (674.3 lên 5114.3 tokens).
  - *Chi phí logical query:* Tăng **~4.6x** từ baseline đến $k=10$ ($0.000365 lên $0.001679 USD).
- **Hạch Toán Tài Chính Toàn Thể 6,400 Requests:**
  - Trần ngân sách tối đa đóng băng cứng: **$19.99 USD** ($19.99000000 USD `hard_budget_limit_usd`).
  - Quyết toán thực tế 5 điều kiện chính thức: **$6.58 settled spend** ($6.57575890 USD), cộng giữ chỗ thận trọng pilot $0.05264010 USD, tổng cam kết là **$6.63 committed spend** ($6.62839900 USD).
  - Số dư chưa cam kết khả dụng còn lại: **$13.36 USD** ($13.36160100 USD net remaining; 0 holds, 0 breach).
  - Xử lý ngoại lệ: 13 INCOMPLETE dispatches trên 6,400 requests; 1 lượt retry do lỗi API ($0.53974560 USD missing usage hold được hoàn trả/quyết toán đầy đủ; chi tiết 8 chữ số thập phân lưu trong Speaker Notes).

### Ghi chú diễn giả (Speaker Notes)
> "Trong phân tích RQ3, toàn bộ chỉ số tài nguyên, độ trễ và chi phí được tính trên toàn bộ 1,280 logical views mỗi điều kiện (tổng 6,400 dispatches), không rút gọn về 718 scorable views:
> 1. Độ trễ & Tài nguyên: Phân biệt rõ trễ trung vị (No-RAG 2.30s vs RAG k10 2.67s) và trễ trung bình (No-RAG 2.90s vs RAG k10 4.37s). Lượng prompt tokens trung bình tăng từ 674.3 lên 5114.3 (~7.6x từ baseline đến k10), chi phí mỗi request tăng từ $0.000365 lên $0.001679 USD (~4.6x từ baseline đến k10).
> 2. Hiệu quả đánh đổi: Hit rate chuẩn tắc trên tập scorable N=718: No-RAG là N/A (không dùng retriever); RAG k=1 đạt Hit@1 = 3.760% (27/718), tăng lên RAG k=10 đạt Hit@10 = 44.708% (321/718).
> 3. Hạch toán tài chính 8 chữ số thập phân chính xác: Chi phí 5 điều kiện chuẩn đã quyết toán là $6.57575890 USD ($6.58 settled spend), cộng với khoản giữ chỗ thận trọng pilot $0.05264010 USD, tổng chi phí đã cam kết là $6.62839900 USD ($6.63 USD committed spend). Ngân sách khả dụng còn lại là $13.36160100 USD ($13.36 USD net remaining; 0 holds, 0 breach) trên trần đóng băng cứng $19.99000000 USD ($19.99 budget cap). Chi phí được tính toán theo ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate).
> 4. Bối cảnh lịch sử & Ngoại lệ: DEV pilot lịch sử là 20 requests (~$0.0242 USD). Trên toàn bộ 6,400 requests có 13 INCOMPLETE records; 1 attempt API_FAILURE được retry có khoản phí thiếu usage là $0.53974560 USD.
> 
> *Bằng chứng dự án:* `C:/Users/hahoa/.codex/artifacts/rag2attck/verified-native-figures-v1/canonical_rq3_cost_and_latency.png`; `config/experiment_config.json`; `tests/test_monetary_guard.py`."

---

## Slide 10: Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị (Limitations & Threats to Validity)

### Nội dung trình chiếu
1. **Phạm vi dữ liệu (Scope Boundary):**
   - Đánh giá hiện tại được thực hiện trên benchmark giả lập có cấu trúc Stage B (`synthetic-paired-v1`).
   - Mặc dù phản ánh sát các thuộc tính kỹ thuật của Windows logs, tập dữ liệu này chưa bao quát đầy đủ sự hỗn loạn và nhiễu của các cuộc tấn công APT thực tế (luồng dữ liệu thực địa T15 vẫn đang ở trạng thái chuẩn bị).
2. **Hạn chế của mô hình nhúng đơn tầng:**
   - Việc chỉ dựa vào dense semantic similarity (`all-MiniLM-L6-v2`) khiến hệ thống bỏ sót các từ khóa định danh cụ thể (ví dụ: Event ID 4720, tên tiến trình đặc biệt).
   - Cần bổ sung cơ chế tìm kiếm lai (Hybrid Search: Dense + Lexical BM25) trong tương lai; giải pháp này chưa từng được thử nghiệm trong benchmark hiện tại.
3. **Phạm vi mô hình & Ranh giới diễn giải thống kê:**
   - Toàn bộ 4 khoảng tin cậy 95% Bootstrap CI của chênh lệch độ chính xác so với No-RAG đều chứa 0.
   - Phép thử **McNemar thăm dò ở cấp độ view** cho kết quả $p = 0.4223 > 0.05$, KHÔNG phải là đặc tính của bootstrap CI (khoảng tin cậy chứa 0).
   - Cần mở rộng quy mô mẫu và đa dạng hóa mô hình trước khi khẳng định bất kỳ lợi thế mang tính cấu trúc nào; tuyệt đối **không suy diễn quan hệ nhân quả** hay khẳng định "tri thức tham số thuần túy" khi chưa được kiểm chứng.
4. **Quy trình tái lập ngoại tuyến an toàn:**
   - Mọi kịch bản kiểm thử bắt buộc chạy qua runner offline `scripts/run_offline_tests.py` can thiệp socket Python và lọc biến môi trường nhằm hạn chế rò rỉ credential và gọi API ngầm ngoài ý muốn (không phải là sandbox cấp OS).

### Ghi chú diễn giả (Speaker Notes)
> "Nghiên cứu công khai đầy đủ các giới hạn khoa học và ràng buộc thực nghiệm:
> 1. Dữ liệu: Kịch bản giả lập có cấu trúc synthetic-paired-v1 với 8 kỹ thuật có mẫu dương tính trong tổng số 474 lớp đóng băng; 40 cặp đối ứng có GT thay đổi khi mở rộng ngữ cảnh; dữ liệu telemetry thực tế in-the-wild (T15) chưa được kiểm chứng.
> 2. Bộ tìm kiếm: Hạn chế từ vựng của dense bi-encoder được ghi nhận rõ, tuy nhiên giải pháp Hybrid Dense+BM25 chưa từng được thử nghiệm trong benchmark này và là hướng phát triển tương lai.
> 3. Thống kê: Toàn bộ 4 khoảng tin cậy 95% CI của chênh lệch độ chính xác so với No-RAG đều chứa 0. Phép thử McNemar thăm dò ở cấp độ view cho kết quả p = 0.4223 > 0.05, không khẳng định RAG vượt trội No-RAG; không suy diễn quan hệ nhân quả hay khẳng định tri thức tham số thuần túy khi chưa được kiểm chứng.
> 4. An toàn: Runner offline scripts/run_offline_tests.py can thiệp socket tầng ứng dụng và lọc biến môi trường, không phải là sandbox cấp OS.
> 
> *Bằng chứng dự án:* `docs/reproducibility.md`; `scripts/run_offline_tests.py`; `tests/test_offline_guard.py`."

---

## Slide 11: Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học (Reproducibility & Contributions)

### Nội dung trình chiếu
- **Tái Lập Ngoại Tuyến & Phạm Vi Offline Guard:**
  - Lệnh chuẩn tắc có bảo vệ ngoại tuyến:
    ```bash
    python scripts/run_offline_tests.py -m pytest ... (hoặc cờ -c)
    ```
  - **Lệnh tái lập khoa học chuẩn tắc:**
    ```bash
    python scripts/reproduce_canonical_study.py --all
    ```
    *(Phân biệt với kịch bản chẩn đoán lịch sử / fixture helper `scripts/reproduce_study.py`).*
  - **Phạm vi kỹ thuật của `offline_guard`:**
    - Can thiệp tầng socket Python (chặn kết nối mạng ngoài ý muốn) và lọc biến môi trường credentials.
    - Không phải là sandbox cấp OS (không cô lập mã máy binary tùy ý ngoài Python runtime).
    - Dependencies và artifact tiên quyết đã nạp sẵn cục bộ; lệnh `uv run` trần không có guard bảo vệ không tự động đảm bảo cách ly mạng nếu thiếu cờ offline.
  - **Điều kiện tái lập & Công khai:**
    - *Tái lập ngoại tuyến từ 15 canonical artifacts đóng băng:* Xác thực tính toàn vẹn toán học và hạch toán tài chính mà KHÔNG tạo ra bất kỳ lượt gọi mô hình trực tiếp hay chi phí token nào.
    - *Tái lập toàn diện luồng live provider:* Yêu cầu nạp credentials thực và chạy dưới cơ chế budget guard trần $19.99 USD.
    - *Gói bằng chứng công khai:* Hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan) chờ thẩm định xuất bản chính thức.
  - Toàn bộ 15 artifact và giao thức thực nghiệm được neo giữ bằng mã băm SHA-256 trong `config/canonical_experiment_lock_v1.json`.
- **Đóng góp khoa học cốt lõi:**
  1. *Quy trình thực nghiệm chuẩn hóa:* Thiết lập giao thức thực nghiệm đối chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán Windows log attribution.
  2. *Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i):* Phân tích riêng biệt retrieval miss, downstream generation failure và joint overlap (không giả định độc lập ngẫu nhiên).
  3. *Bằng chứng định lượng về khoảng cách từ vựng và giả thuyết pha loãng ngữ cảnh (Context Dilution Hypothesis).*
  4. *Bộ công cụ nghiên cứu mở:* Cung cấp toàn bộ mã nguồn, benchmark, kịch bản tạo slide và dữ liệu chứng cứ nguyên vẹn.

### Ghi chú diễn giả (Speaker Notes)
> "Khả năng kiểm chứng độc lập là cam kết trọng tâm của dự án. Lệnh tái lập khoa học chuẩn tắc là `python scripts/reproduce_canonical_study.py --all`, phân biệt với kịch bản chẩn đoán lịch sử/fixture helper `scripts/reproduce_study.py`. Cơ chế đánh giá ngoại tuyến từ 15 artifacts đã đóng băng nhằm xác thực tính toàn vẹn toán học và hạch toán tài chính mà KHÔNG tạo ra bất kỳ lượt gọi mô hình trực tiếp hay chi phí token mới nào. Runner `scripts/run_offline_tests.py` can thiệp ở tầng socket Python và biến môi trường, không phải là sandbox cấp hệ điều hành. Gói bằng chứng công khai hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan) chờ thẩm định xuất bản chính thức. Bốn đóng góp thực nghiệm cốt lõi: thiết lập phương pháp luận đo lường đối chứng, phân rã lỗi D2i độc lập, minh bạch độ không chắc chắn thống kê và cung cấp gói chứng cứ có thể kiểm chứng độc lập.
> 
> *Bằng chứng dự án:* `config/canonical_experiment_lock_v1.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `scripts/reproduce_canonical_study.py`; `scripts/run_offline_tests.py`; `tests/test_smoke_cases.py`."

---

## Slide 12: Tổng Kết & Hỏi Đáp (Conclusion & Q&A)

### Nội dung trình chiếu
- **Tóm tắt kết luận:**
  - RAG cung cấp tri thức nền tảng quan trọng; kết quả đối chứng ghi nhận No-RAG đạt 560/718 (77.99%) vs RAG k=10 quan sát thấy 571/718 (79.53%, Delta = +1.53 pp, 95% CI [-2.355, +5.300] pp chứa 0, không có ý nghĩa thống kê).
  - Phân rã lỗi D2i theo 3 trục đo lường độc lập (retrieval miss, downstream generation failure, joint overlap): 80.95% số ca phân loại sai (119/147) nằm ở nhánh truy xuất trượt; các trục lỗi độc lập ghi nhận giao thoa thực tế mà không giả định độc lập ngẫu nhiên.
  - Quy trình tái lập ngoại tuyến: Thực thi tái lập khoa học chuẩn tắc qua `python scripts/reproduce_canonical_study.py --all` (đánh giá ngoại tuyến từ 15 artifacts đã đóng băng, 0 token spend) dưới runner `scripts/run_offline_tests.py` can thiệp tầng socket và lọc biến môi trường.
  - Hiện tượng pha loãng ngữ cảnh (Context Dilution) khẳng định tầm quan trọng của việc tiền lọc log có chọn lọc thay vì nhúng toàn bộ nhật ký xung quanh.
- **Định hướng phát triển:**
  - Triển khai Hybrid Retrieval (Dense + BM25) để khắc phục triệt để khoảng cách ngữ nghĩa ở các sự kiện như `T1136.001`.
  - Triển khai thực nghiệm mở rộng trên telemetry thực tế khi hoàn thiện khâu khử khuẩn.
- **Kho lưu trữ & Danh mục siêu dữ liệu khả chuyển:** PR #26 ([GitHub PR #26](https://github.com/habachcp6/RAG2ATTCK/pull/26)); gói công khai ở dạng portable metadata inventory chờ thẩm định xuất bản.
- **Trân trọng cảm ơn Quý Thầy Cô và Hội Đồng!**  
  *Kính mời Quý Thầy Cô đặt câu hỏi thảo luận (Q&A).*

### Ghi chú diễn giả (Speaker Notes)
> "Tóm lại, RAG2ATT&CK đã hoàn tất thực nghiệm đối chứng đo lường vai trò của RAG trong bài toán ánh xạ log Windows sang ATT&CK techniques:
> 1. Kết quả cốt lõi: No-RAG đạt 77.99% (560/718), RAG k10 quan sát thấy 79.53% (571/718, Delta = +1.53 pp). Khoảng tin cậy 95% CI [-2.355, +5.300] pp chứa 0, cho thấy RAG chưa tạo khác biệt có ý nghĩa thống kê trên benchmark này.
> 2. Phân rã lỗi: 80.95% lỗi phân loại sai rơi vào trường hợp truy xuất trượt Top-10 (119/147).
> 3. Tài chính: Chi phí toàn bộ nghiên cứu được kiểm soát chặt chẽ ở mức $6.628399 USD ($6.63 USD committed spend) trên trần ngân sách $19.99 USD.
> 4. Tái lập & Công khai: Thực thi tái lập khoa học chuẩn tắc qua `python scripts/reproduce_canonical_study.py --all` (đánh giá ngoại tuyến từ artifact đã đóng băng, không phát sinh chi phí). Gói phát hành công khai được tổ chức dạng danh mục siêu dữ liệu khả chuyển chờ thẩm định xuất bản.
> 
> *Khai báo công cụ:* Toàn bộ slide deck này được tác tạo và cập nhật bằng công cụ bundled artifact tools, đảm bảo định dạng PowerPoint native tiếng Việt có thể chỉnh sửa từng shape.
> 
> *Bằng chứng dự án:* PR #26 (`https://github.com/habachcp6/RAG2ATTCK/pull/26`); `docs/sanitized_evidence_manifest.json`; `reports/evidence/reproducibility_package_manifest.md`."
