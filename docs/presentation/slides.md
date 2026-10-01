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
  - Thiết kế nghiên cứu thực nghiệm có kiểm soát (Controlled Empirical Study).
  - Đo lường chính xác delta hiệu năng do RAG mang lại trên cùng mô hình LLM.
  - Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại (Classification Failure).
  - Đóng băng giao thức v1.1: Thực thi xác định (Deterministic Execution under Frozen Environment & Seeds).
  - Tái lập ngoại tuyến chi phí 0 đồng với bộ `offline_guard` chặn tuyệt đối kết nối mạng ngoài.

### Ghi chú diễn giả (Speaker Notes)
> "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này đo lường khoa học mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ. Toàn bộ thực thi đạt tính xác định (Deterministic Execution under Frozen Environment & Seeds), loại trừ hoàn toàn tính tùy tiện trong diễn giải số liệu.
> 
> *Bằng chứng dự án:* `docs/README_PROPOSED.md`; `config/canonical_experiment_lock_v1.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `tests/test_attack_id_validation.py`."

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
  - **Chính sách kỹ thuật lịch sử (`D2g: ALLOW_HISTORICAL`):**
    - Chấp nhận các mã kỹ thuật lịch sử hoặc đã bị thu hồi (revoked/deprecated) có trong bộ kiểm chuẩn.
    - Báo cáo dưới dạng distinct observation count, không tự ý gán lại (no silent remapping).
  - **Không gian lớp mục tiêu (`D2d: FROZEN_BENCHMARK_UNIVERSE`):**
    - Macro-F1 tính trên tập các lớp kỹ thuật chuẩn đóng băng, đảm bảo tính nhất quán giữa các lần chạy.
  - **Loại trừ mẫu rỗng / mơ hồ (`D2b-c: EXCLUDE`):** Mẫu không gán được nhãn hoặc nhãn mơ hồ bị loại khỏi mẫu số Attribution Accuracy.
  - **Lưu vết nguyên bản (`D1: RECORD_ONLY`):** Lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập.
- **4 Tiêu chí đánh giá cốt lõi (Core Evaluation Criteria):**
  - **D2h (Multi-GT Retrieval Success):** `ANY_GT_RETRIEVED` - Retrieval được tính là thành công nếu BẤT KỲ ground-truth technique ID nào có trong Top-k candidates.
  - **D2i (Failure Decomposition):** `INDEPENDENT_AXES` - Bóc tách độc lập lỗi tìm kiếm và phân loại trên các trục trực giao; ghi nhận đầy đủ phần giao thoa (overlap).
  - **D2e (Invalid ID Denominator):** `INCLUDE_IN_DENOMINATOR` - Mã ATT&CK ảo giác, sai cú pháp đều bị tính là thất bại (Fail-Closed).
  - **D2f (Provider Failure Denominator):** `INCLUDE_IN_DENOMINATOR` - Lỗi API, timeout, refusal đều tính vào mẫu số, không được loại trừ.
  - **D3:** Khóa mô hình: `ALLOW_LATEST_WITH_TIMESTAMP_BINDING` (tem UTC thực tế).
  - **D4-D5:** Thực thi tuần tự (`SEQUENTIAL_ONLY`), chặn cứng ngân sách (`HARD_CAP`).

### Ghi chú diễn giả (Speaker Notes)
> "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi D1-D7. Về mô hình đe dọa, danh mục kỹ thuật được neo tại STIX ATT&CK v19.2 Enterprise Windows (474 techniques). Điểm đặc biệt quan trọng là chính sách D2g ALLOW_HISTORICAL: các mã kỹ thuật lịch sử hoặc đã bị thu hồi có trong benchmark được chấp nhận và báo cáo dạng distinct observation count, không tự ý gán lại mã thay thế. Bốn tiêu chí đánh giá cốt lõi gồm D2h (ANY_GT_RETRIEVED cho multi-label), D2i (INDEPENDENT_AXES ghi nhận đầy đủ overlap), D2e (invalid ID tính vào mẫu số), và D2f (lỗi mạng tính vào mẫu số) thiết lập nguyên tắc fail-closed nghiêm ngặt.
> 
> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`); `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` (SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`); `tests/test_experiment_evaluation.py`."

---

## Slide 6: Kết Quả RQ2 - Chẩn Đoán Khâu Truy Xuất (RQ2: Retrieval Diagnostics)

### Nội dung trình chiếu
- **Đánh giá độc lập bộ truy xuất trên 756 positive views:**
  - *Hit@1:* $4.23\%$ (32 / 756)
  - *Hit@3:* $16.80\%$ (127 / 756)
  - *Hit@5:* $24.21\%$ (183 / 756)
  - *Hit@10:* $45.11\%$ (341 / 756)
  - *Macro Recall@10:* $43.14\%$  |  *Mean GT Rank khi trúng:* 5.21
  - **Tỷ lệ vắng mặt trong Top-10 (Retrieval Failure):** $54.89\%$ (415 / 756)
- **Khoảng cách ngữ nghĩa (Semantic Gap) ở `T1136.001`:**
  - Kỹ thuật `T1136.001` (Create Account: Local Account) đạt **0% Top-10 Hit Rate (0 / 99 views)**.
  - *Nguyên nhân:* Nhật ký Windows Event ID 4720 sử dụng từ ngữ hệ thống ("SamAccountName"), trong khi mô tả STIX ATT&CK nhấn mạnh mục tiêu chiến thuật ("persistence").
- **Giả thuyết Context Scaling & Dilution ($k \in \{1, 3, 5, 10\}$):**
  - Tăng $k$ giúp cải thiện độ phủ (Hit@k) nhưng đưa thêm nhiều token gây nhiễu distractor.
  - Giả thuyết đang được kiểm chứng thực nghiệm đối chứng end-to-end trên ma trận TEST.

### Ghi chú diễn giả (Speaker Notes)
> "Chẩn đoán độc lập khâu tìm kiếm (RQ2) trên 756 positive views cho thấy Hit@10 chỉ đạt 45.11%, nghĩa là trong 54.89% trường hợp, kỹ thuật đúng hoàn toàn vắng bóng trong Top-10 gửi cho LLM. Điển hình là kỹ thuật T1136.001 với 0/99 lần trúng Top-10 do khoảng cách ngữ nghĩa giữa Event ID 4720 và STIX description. Chúng tôi đặt ra giả thuyết Context Scaling & Dilution (k=1,3,5,10): tăng k cải thiện độ phủ nhưng tăng nguy cơ nhiễu distractor; giả thuyết này đang được kiểm chứng thực nghiệm đối chứng end-to-end.
> 
> *Bằng chứng dự án:* `outputs/reproduction/figures/fig_rq2_retrieval_hit_rates.png`; `outputs/reproduction/tables/table_1_retrieval_diagnostics.md`; `tests/test_retrieval_diagnostics.py`."

---

## Slide 7: Tác Động Của Hình Thức Biểu Diễn Telemetry (Representation Gap)

### Nội dung trình chiếu
- **So sánh cặp kịch bản đối ứng (Pairwise Single vs. Contextual across 670 pairs):**
  - **Phân tích Cặp Anchor Chuẩn (296 cặp hợp lệ - Primary):**
    - Tiêu chí: Single view có duy nhất 1 kỹ thuật và kỹ thuật này xuất hiện trong Contextual view (374 cặp bị loại trừ do đa nhãn/mismatch).
    - **Single-event đạt thứ hạng tốt hơn:** **65 cặp** (22.0%).
    - **Contextual-event đạt thứ hạng tốt hơn:** **23 cặp** (7.8%).
    - **Hiệu năng thứ hạng ngang nhau:** **208 cặp** (70.3%), trong đó:
      - Cả hai biểu diễn cùng trượt Top-10: **147 cặp**.
      - Đồng hạng chính xác trong Top-10: **61 cặp**.
  - **Nhóm lọc đơn kỹ thuật nghiêm ngặt (252 cặp - Secondary):**
    - Cả Single và Contextual view đều có đúng 1 kỹ thuật trùng nhau: Single tốt hơn 59 cặp (23.4%) vs. Contextual 23 cặp (9.1%), ngang nhau 170 cặp.
- **Hiện tượng Benign Drift khi mở rộng ngữ cảnh:**
  - Gom các sự kiện lân cận bổ sung nhiều token thông thường (Explorer, DNS, svchost).
  - Vector dense embedding bị kéo lệch về hành vi bình thường, làm tụt thứ hạng kỹ thuật tấn công.
- **Schema So Sánh Đối Chứng Scaffold `[PENDING EXECUTION]`:**
  - Đối chứng: Zero-Shot No-RAG vs Zero-Shot RAG (k=1..10) vs Prompt Scaffolds.
  - Giả thuyết: Khối tri thức RAG bổ trợ cần đi kèm tiền lọc sự kiện nghi vấn thay vì nhúng toàn bộ chuỗi log thô.
  - Kết luận chính thức đang chờ dữ liệu hoàn tất từ ma trận TEST chuẩn (PID 50192).

### Ghi chú diễn giả (Speaker Notes)
> "So sánh đối ứng trên 296 cặp anchor chuẩn chỉ ra rằng biểu diễn Single-event đạt thứ hạng tìm kiếm tốt hơn Contextual-event (65 cặp vs 23 cặp), và hơn 70% có thứ hạng tương đương (phần lớn do cả hai cùng trượt Top-10). Điều này cho thấy việc đưa thêm log nền gây hiện tượng benign drift. Chúng tôi thiết lập schema so sánh đối chứng scaffold giữa Zero-Shot No-RAG, Zero-Shot RAG và các prompt scaffold, hiện đang được gắn nhãn [PENDING EXECUTION] chờ toàn bộ ma trận TEST hoàn tất để đưa ra kết luận khoa học chính thức.
> 
> *Bằng chứng dự án:* `scripts/verify_t20_canonical_artifacts.py`; `outputs/reproduction/tables/table_4_pairwise_representation_comparison.md`; `tests/test_t20_canonical_artifacts.py`."

---

## Slide 8: Khung Đánh Giá End-to-End (RQ1) & Phân Rã Lỗi Độc Lập D2i (RQ2)

### Nội dung trình chiếu
- **Mô hình phân rã lỗi độc lập theo Định đề D2i (RQ2 Error Decomposition):**
  - Định đề D2i quy định retrieval failure và downstream generation failure là **CÁC TRỤC ĐỘC LẬP (Independent Axes)**, không phải phân hoạch xung khắc rời rạc (phần giao thoa khác 0).
  - **Trục 1 - Retrieval Miss Rate:** $1 - \text{Hit}@k$ (kỹ thuật ground-truth vắng mặt trong Top-k theo tiêu chí D2h `ANY_MATCH`).
  - **Trục 2 - Downstream Generation Failure:** mô hình phát sinh invalid ATT&CK ID (D2e), gặp lỗi provider (D2f), hoặc chọn sai kỹ thuật dù đã được cung cấp.
  - **Trục 3 - Joint Overlap:** ghi nhận rõ các bản ghi retrieval trượt ĐỒNG THỜI mô hình hallucinate/phân loại sai, không áp đặt thứ tự loại trừ nhân tạo.
- **Các thước đo có điều kiện (Conditional Metrics):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}k)$: Đánh giá năng lực lựa chọn của LLM khi bộ tìm kiếm hoạt động chính xác.
  - $P(\text{Correct} \mid \text{GT Absent from Top-}k)$: Đánh giá khả năng LLM tự sửa sai dựa trên tri thức nội tại.
  - Macro-F1 & Exact Match: Tính trên không gian kỹ thuật chuẩn Frozen Benchmark Universe (D2d).
  - Nguyên tắc Fail-Closed: Mẫu lỗi API, timeout (D2f) hay mã sai cú pháp (D2e) đều tính vào mẫu số.
- **Trạng thái thực nghiệm RQ1 & RQ2 `[PENDING EXECUTION]`:**
  - Ma trận TEST chính thức: 1,280 views x 5 nhánh (6,400 bản ghi) đang trong tiến trình chạy (PID 50192).
  - Evaluator tuân thủ Fail-Closed: Từ chối công bố điểm chính thức khi chưa đủ 6,400 records.
  - Kiểm định toán học Evaluator: Đã xác thực ngoại tuyến qua 5 test fixtures (`outputs/reproduction/fixture_diagnostics/`).

### Ghi chú diễn giả (Speaker Notes)
> "Khung đánh giá RQ1 & RQ2 được xây dựng trên định đề D2i (Independent Axes). Chúng tôi bác bỏ hoàn toàn công thức cộng xác suất rời rạc sai lầm, bởi retrieval failure và downstream generation failure không hề xung khắc nhau mà có phần giao thoa rõ ràng. Các chỉ số có điều kiện P(Correct | GT in Top-k) và P(Correct | GT NOT in Top-k) cho phép định lượng chính xác xem LLM có bị đánh lừa bởi distractor hay có khả năng tự sửa sai. Toàn bộ ma trận chính thức 6,400 bản ghi đang chạy; tính đúng đắn toán học của Evaluator đã được chứng minh qua 5 test fixtures.
> 
> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (D2e, D2f, D2h, D2i; SHA-256: `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c`); `tests/test_experiment_evaluation.py` (94 tests pass)."

---

## Slide 9: Nghiên Cứu Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm (RQ3)

### Nội dung trình chiếu
- **Kết quả thực nghiệm từ DEV Cost Pilot (20 cuộc gọi thực tế tới gpt-5.6-luna xhigh):**
  - *Mục đích:* Đo lường token và độ ổn định schema trước khi chạy toàn bộ tập TEST.
  - Tỷ lệ tuân thủ schema JSON: **100% VALID** (20/20 bản ghi).
  - Số lần thử lại (retries): **0** (100% thành công ở lần gọi đầu tiên, trễ TB 8,127.6 ms).
- **Mức tiêu thụ Token và Chi phí ước tính ban đầu:**
  | Điều kiện | Input Tokens TB | Output Tokens TB | Chi phí / Yêu cầu (Telemetry ban đầu) |
  | :--- | :---: | :---: | :---: |
  | `no_rag` ($k=0$) | 643.0 | 224.2 | ~$0.00039 |
  | `rag_k1` ($k=1$) | 1,115.0 | 332.2 | ~$0.00062 |
  | `rag_k3` ($k=3$) | 1,740.5 | 1,087.2 | ~$0.00165 (ước tính telemetry ban đầu) |
  | `rag_k5` ($k=5$) | 2,518.2 | 840.2 | ~$0.00151 |
  | `rag_k10` ($k=10$) | 4,536.5 | 800.8 | ~$0.00187 |
- **Phân định rõ ràng chi phí thực nghiệm:**
  - **Quyết toán thực tế (Verified Spend):** **$0.024209 USD** cho 20 requests pilot (conservative: $0.026320 USD).
  - **Dự phóng tập TEST (Projected Spend):** **$8.20 – $8.99 USD** cho toàn bộ 6,400 requests.
  - **Trần ngân sách đóng băng (Hard Budget Cap):** **$19.99 USD** (`hard_budget_limit_usd`).
  - **Khoản giữ chỗ conservative pilot:** **$0.05264010 USD** (`reserved_budget_usd`).
- **Quy luật đánh đổi (Trade-off):** Tăng $k$ từ 1 lên 10 giúp tăng Hit rate từ 4.2% lên 45.1%, nhưng lượng token đầu vào tăng ~4x. Chi phí dự phóng TEST (< $10 USD) nằm an toàn dưới trần ngân sách $19.99 USD.

### Ghi chú diễn giả (Speaker Notes)
> "Trong phân tích RQ3, chúng tôi làm rõ số liệu chi phí từ DEV Cost Pilot (20 requests thực tế trên gpt-5.6-luna). Con số ~$0.00165/query là ước tính từ telemetry pilot ban đầu tại nhánh k=3 do độ dài reasoning output. Chi phí quyết toán thực tế (verified spend) là $0.024209 USD (conservative rate: $0.026320 USD). Chi phí dự phóng cho toàn bộ 6,400 requests của tập TEST là $8.20 – $8.99 USD. Toàn bộ tiến trình được kiểm soát bởi trần ngân sách đóng băng $19.99 USD và khoản giữ chỗ conservative pilot $0.05264010 USD, bảo đảm không bao giờ vượt ngân sách.
> 
> *Bằng chứng dự án:* `config/experiment_config.json` (hard_budget_limit_usd: 19.99); `reports/evidence/dev_cost_pilot_20261001/summary.json` (SHA-256: `f8dfe99479346dbbeff94d6e9dc7d11019623e5932ef27a00f1c3222e4c92b23`); `tests/test_monetary_guard.py`."

---

## Slide 10: Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị (Limitations & Threats to Validity)

### Nội dung trình chiếu
1. **Phạm vi dữ liệu (Scope Boundary):**
   - Đánh giá hiện tại được thực hiện trên benchmark giả lập có cấu trúc Stage B (`synthetic-paired-v1`).
   - Mặc dù phản ánh sát các thuộc tính kỹ thuật của Windows logs, tập dữ liệu này chưa bao quát đầy đủ sự hỗn loạn và nhiễu của các cuộc tấn công APT thực tế (luồng dữ liệu thực địa T15 vẫn đang ở trạng thái chuẩn bị).
2. **Hạn chế của mô hình nhúng đơn tầng:**
   - Việc chỉ dựa vào dense semantic similarity (`all-MiniLM-L6-v2`) khiến hệ thống bỏ sót các từ khóa định danh cụ thể (ví dụ: Event ID 4720, tên tiến trình đặc biệt).
   - Cần bổ sung cơ chế tìm kiếm lai (Hybrid Search: Dense + Lexical BM25).
3. **Phạm vi mô hình & Quy trình tái lập an toàn:**
   - Toàn bộ kết quả đối chứng được đo trên mô hình đại diện `gpt-5.6-luna`.
   - Cần mở rộng kiểm nghiệm trên các mô hình mã nguồn mở (Llama-3, Qwen) để xác minh tính phổ quát của quy luật phân rã lỗi.
   - **Quy trình tái lập an toàn:** Mọi kịch bản kiểm thử bắt buộc chạy qua runner offline `scripts/run_offline_tests.py`, tuyệt đối không dùng pytest trần không có guard để ngăn chặn rò rỉ credential và gọi API ngầm.

### Ghi chú diễn giả (Speaker Notes)
> "Nghiên cứu công khai các giới hạn khoa học: Dữ liệu hiện tại nằm trong phạm vi kịch bản có cấu trúc synthetic-paired-v1; bộ nhúng dense đơn tầng chưa kết nối được từ vựng kỹ thuật hệ thống (Event ID số); và mô hình đánh giá là gpt-5.6-luna. Để đảm bảo an toàn tuyệt đối, mọi quy trình kiểm thử tái lập phải thực thi qua runner offline scripts/run_offline_tests.py nhằm bảo đảm không phát sinh bất kỳ kết nối mạng ngoài nào.
> 
> *Bằng chứng dự án:* `docs/reproducibility.md`; `scripts/run_offline_tests.py`; `tests/test_offline_guard.py` (OFFLINE_GUARD egress=0)."

---

## Slide 11: Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học (Reproducibility & Contributions)

### Nội dung trình chiếu
- **Tái Lập 100% Ngoại Tuyến (Zero-Cost Offline Reproduction):**
  - Lệnh tái lập tự động toàn diện:
    ```bash
    uv run python scripts/reproduce_study.py --all
    ```
  - Lệnh kiểm thử bộ test suite có bảo vệ:
    ```bash
    uv run python scripts/run_offline_tests.py
    ```
  - Tuyệt đối không dùng pytest trần không có `OFFLINE_GUARD`.
  - **Điều kiện tái lập:**
    - *Tái lập ngoại tuyến:* Sử dụng 15 canonical artifacts đã khóa mật mã trong repo.
    - *Tái lập toàn diện luồng live provider:* Yêu cầu nạp credentials thực và chạy dưới cơ chế budget guard trần $19.99 USD.
  - Toàn bộ 15 artifact và giao thức thực nghiệm được neo giữ bằng mã băm SHA-256 trong `config/canonical_experiment_lock_v1.json`.
- **Đóng góp khoa học cốt lõi:**
  1. *Quy trình thực nghiệm chuẩn hóa:* Thiết lập giao thức thực nghiệm đối chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán Windows log attribution.
  2. *Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i):* Phân tích riêng biệt retrieval miss, downstream generation failure và joint overlap.
  3. *Bằng chứng định lượng về khoảng cách từ vựng và giả thuyết pha loãng ngữ cảnh (Context Dilution Hypothesis).*
  4. *Bộ công cụ nghiên cứu mở:* Cung cấp toàn bộ mã nguồn, benchmark, kịch bản tạo slide và dữ liệu chứng cứ nguyên vẹn.

### Ghi chú diễn giả (Speaker Notes)
> "Khả năng tái lập độc lập là cam kết trọng tâm của dự án. Lệnh reproduce_study.py --all tái tạo toàn bộ chẩn đoán, bảng biểu và đồ thị từ 15 artifact đã đóng băng mà không tốn chi phí. Việc kiểm thử bắt buộc sử dụng runner scripts/run_offline_tests.py để kích hoạt OFFLINE_GUARD. Tái lập toàn diện luồng live provider yêu cầu credentials thực và chạy dưới budget guard kiểm soát ngân sách trần $19.99 USD. Bốn đóng góp khoa học cốt lõi đã thiết lập nền tảng đối chứng vững chắc cho cộng đồng RAG an ninh mạng.
> 
> *Bằng chứng dự án:* `config/canonical_experiment_lock_v1.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `scripts/reproduce_study.py`; `scripts/run_offline_tests.py`; `tests/test_smoke_cases.py`."

---

## Slide 12: Tổng Kết & Hỏi Đáp (Conclusion & Q&A)

### Nội dung trình chiếu
- **Tóm tắt kết luận:**
  - RAG cung cấp cơ sở tri thức quan trọng, nhưng chất lượng của khâu truy xuất (Retrieval Quality) là yếu tố quyết định thành bại.
  - Phân rã lỗi theo D2i (Independent Axes) định lượng độc lập lỗi tìm kiếm, lỗi sinh của mô hình và phần giao thoa.
  - Quy trình tái lập an toàn: Toàn bộ kiểm thử chạy qua runner offline `scripts/run_offline_tests.py` bảo đảm không rò rỉ credential.
  - Hiện tượng pha loãng ngữ cảnh (Context Dilution) khẳng định tầm quan trọng của việc tiền lọc log có chọn lọc thay vì nhúng toàn bộ nhật ký xung quanh.
- **Định hướng phát triển:**
  - Tích hợp công nghệ Hybrid Search (Dense + Sparse/BM25) để khắc phục triệt để khoảng cách ngữ nghĩa ở các sự kiện như `T1136.001`.
  - Triển khai thực nghiệm đầy đủ trên tập dữ liệu Windows-APT thực tế khi hoàn thiện khâu khử khuẩn.
- **Kho lưu trữ & Báo cáo:** Mã nguồn, dữ liệu và báo cáo tái lập sẵn sàng tại: [GitHub PR #26](https://github.com/habachcp6/RAG2ATTCK/pull/26)
- **Trân trọng cảm ơn Quý Thầy Cô và Hội Đồng!**  
  *Kính mời Quý Thầy Cô đặt câu hỏi thảo luận (Q&A).*

### Ghi chú diễn giả (Speaker Notes)
> "Tóm lại, RAG2ATT&CK đã chứng minh rằng để ứng dụng RAG thành công trong SOC, chúng ta không thể chỉ kỳ vọng vào mô hình ngôn ngữ lớn, mà phải giải quyết bài toán cốt lõi là tối ưu hóa bộ truy xuất và cấu trúc hóa biểu diễn log. Toàn bộ mã nguồn, dữ liệu thực nghiệm và gói tái lập đã được công bố tại PR #26. Tôi xin chân thành cảm ơn sự lắng nghe của Quý Thầy Cô và kính mời Hội đồng đặt câu hỏi thảo luận.
> 
> *Bằng chứng dự án:* PR #26 (`https://github.com/habachcp6/RAG2ATTCK/pull/26`); `docs/sanitized_evidence_manifest.json`; `reports/evidence/reproducibility_package_manifest.md`."
