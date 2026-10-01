# RAG2ATT&CK: Đánh Giá Tác Động Của Retrieval-Augmented Generation Dựa Trên MITRE ATT&CK Đối Với Ánh Xạ Windows Endpoint Logs

**Slide Deck & Presentation Scaffold for Scientific Defense & Technical Demonstration**  
*Mã giao thức thực nghiệm:* `experiment-protocol-v1.1` (SHA-256: `d3bf3d31...`)  
*Khóa thực nghiệm chuẩn:* `canonical-lock-v1` (SHA-256: `961ba9b3...`)  
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
  - Giao thức khoa học: `experiment-protocol-v1.1` (Frozen)
  - Khóa mật mã thực nghiệm: `canonical-lock-v1` (15 Canonical Artifacts Verified)
  - Khả năng tái lập: 100% Offline & Zero-Cost Verification (`scripts/reproduce_study.py`)

### Ghi chú diễn giả (Speaker Notes)
> "Kính thưa Hội đồng và các chuyên gia, hôm nay tôi xin trình bày báo cáo nghiên cứu RAG2ATT&CK. Đề tài tập trung giải quyết bài toán: Liệu việc bổ sung tri thức MITRE ATT&CK thông qua cơ chế RAG có thực sự nâng cao độ chính xác khi phân loại kỹ thuật tấn công từ nhật ký Windows Endpoint hay không? Toàn bộ nghiên cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt, bóc tách lỗi giữa khâu tìm kiếm và phân loại, và có thể tái lập hoàn toàn ngoại tuyến với chi phí 0 đồng."

---

## Slide 2: Vấn Đề Nghiên Cứu & Động Lực (Problem Statement & Motivation)

### Nội dung trình chiếu
- **Bối cảnh An toàn Thông tin:**
  - Nhật ký Windows Endpoint (Security Event Logs, Sysmon) là tuyến phòng thủ then chốt của các Trung tâm SOC.
  - Việc ánh xạ nhật ký thô sang ma trận MITRE ATT&CK Enterprise là tiêu chuẩn vàng để xác định ý đồ và chiến thuật của kẻ tấn công.
- **Thách thức của LLM trong Log Attribution:**
  - *Khoảng cách trừu tượng:* Nhật ký ở mức hệ thống rất chi tiết (Process GUID, CommandLine, ParentProcess, Hashes), trong khi ATT&CK Techniques mô tả hành vi ở mức khái niệm.
  - *Hiện tượng ảo giác (Hallucination):* LLM thuần túy dễ gán nhầm sang các kỹ thuật phổ biến hoặc phát sinh mã ATT&CK không có trong danh mục.
  - *Nhầm lẫn giữa các kỹ thuật tương tự:* Khó phân biệt giữa các Sub-techniques lân cận (ví dụ: `T1059.001` PowerShell vs `T1059.003` Command Shell; hoặc các kỹ thuật như `T1059.009` Cloud API và `T1218.012` Verclsid).
- **Mục tiêu nghiên cứu:**
  - Thực hiện đánh giá thực nghiệm có kiểm soát (Controlled Empirical Evaluation).
  - Định lượng chính xác mức độ cải thiện (nếu có) khi tích hợp bộ truy xuất ATT&CK chuyên dụng.

### Ghi chú diễn giả (Speaker Notes)
> "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này không nhằm khẳng định hay phủ định LLM một cách cảm tính, mà đo lường khoa học mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ."

---

## Slide 3: Kiến Trúc Thực Nghiệm Đối Chứng (System Architecture)

### Nội dung trình chiếu
- **Hai nhánh thực nghiệm trên cùng dữ liệu đầu vào:**
  1. **Nhánh Cơ Sở (Baseline No-RAG):**
     $$\text{Windows Endpoint Log} \longrightarrow \text{LLM} \longrightarrow \text{ATT\&CK Technique ID (JSON)}$$
  2. **Nhánh Thử Nghiệm (Experimental RAG):**
     $$\text{Windows Log} \longrightarrow \text{Dense Retriever (FAISS)} \longrightarrow \text{Top-}k \text{ Documents} \longrightarrow \text{Prompt + Tri thức} \longrightarrow \text{LLM} \longrightarrow \text{JSON}$$
- **Kiến trúc bộ truy xuất gọn nhẹ (Lightweight Retrieval Engine):**
  - *Knowledge Corpus:* 474 tài liệu ATT&CK v19.2 Enterprise Windows (`attack/corpus/enterprise-windows-v19.2.jsonl`).
  - *Embedding Model:* `sentence-transformers/all-MiniLM-L6-v2` (384 chiều, chuẩn hóa $L_2$).
  - *Index:* Flat Inner Product FAISS Index (`IndexFlatIP`, Cosine similarity).
- **Các biến kiểm soát bất biến (Controlled Invariants):**
  - Cùng mô hình (`gpt-5.6-luna`), cùng cấu hình suy luận (`reasoning_effort=xhigh`), cùng template prompt (`prompts/baseline_v1.txt`), cùng ràng buộc schema JSON đầu ra.
  - **Biến duy nhất thay đổi:** Bật (ON) hoặc Tắt (OFF) khối ngữ cảnh truy xuất ATT&CK.

### Ghi chú diễn giả (Speaker Notes)
> "Để đảm bảo tính hợp lệ thực nghiệm, biến điều trị duy nhất là sự hiện diện của khối ngữ cảnh ATT&CK được truy xuất. Chúng tôi loại bỏ việc so sánh chéo nhiều nhà cung cấp mô hình để tránh biến gây nhiễu (confounding variables). Mọi yếu tố khác từ prompt template đến schema JSON đều được giữ cố định tuyệt đối."

---

## Slide 4: Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ (Dataset Strategy & Anti-Leakage)

### Nội dung trình chiếu
- **Bộ dữ liệu chuẩn đóng băng Stage B (Frozen Stage B Benchmark):**
  - 670 cặp kịch bản (Scenario Pairs) $\rightarrow$ 1,340 biểu diễn đơn vị (Views).
  - Phân chia: 1,280 TEST Views và 60 DEV Views.
  - Phân loại biểu diễn:
    - *Single-event:* Chỉ chứa một sự kiện duy nhất trực tiếp gây ra hành vi.
    - *Contextual-event:* Chứa sự kiện mục tiêu kèm theo các sự kiện ngữ cảnh xung quanh trên cùng máy trạm.
- **Giao thức chống rò rỉ nhãn nghiêm ngặt (Strict Anti-Label-Leakage):**
  - Đầu vào suy luận (`data/ground_truth/synthetic/inference.jsonl`) chỉ chứa 2 trường: `sample_id` và `endpoint_evidence`.
  - Toàn bộ nhãn mục tiêu, tên luật Sigma/Sysmon, Tactic name, và mô tả đều bị lọc bỏ thông qua allowlist (`INFERENCE_ALLOWLIST`).
- **Phân định phạm vi rõ ràng:**
  - Bộ dữ liệu Stage B là tài liệu chuẩn phục vụ kiểm định kỹ thuật và chẩn đoán truy xuất.
  - Nghiên cứu không khẳng định tính khái quát hóa trên dữ liệu thực tế cho đến khi có tập telemetry thực địa được phê duyệt độc lập (T15 real-data scope).

### Ghi chú diễn giả (Speaker Notes)
> "Một điểm then chốt trong nghiên cứu là chống rò rỉ nhãn (Anti-Label-Leakage). Nhiều công trình trước đây vô tình đưa tên luật phát hiện hoặc từ khóa chiến thuật vào prompt khiến kết quả bị phóng đại. Trong RAG2ATT&CK, bộ tiền xử lý chỉ giữ lại các trường kỹ thuật thô của sự kiện. Chúng tôi cũng phân định rõ ràng giữa benchmark giả lập và dữ liệu thực tế để đảm bảo tính trung thực khoa học."

---

## Slide 5: Giao Thức Đánh Giá Đóng Băng v1.1 (Methodology & Frozen Protocol v1.1)

### Nội dung trình chiếu
- **Khóa mật mã giao thức:** `experiment-protocol-v1.1` (SHA-256: `d3bf3d31...`).
- **7 Quyết định khoa học cốt lõi (Decisions D1–D7):**
  - **D1 (Raw Response):** `RECORD_ONLY` - Lưu nguyên văn phản hồi thô phục vụ kiểm toán độc lập.
  - **D2a (GT Semantics):** `ANY_MATCH` - Dự đoán khớp với bất kỳ nhãn ground-truth hợp lệ nào đều được tính là đúng đối với mẫu multi-label.
  - **D2b-c (Exclusion):** `EXCLUDE` - Loại bỏ mẫu rỗng hoặc mẫu mơ hồ khỏi mẫu số tính Attribution Accuracy.
  - **D2d (Universe):** `FROZEN_BENCHMARK_UNIVERSE` - Tính Macro-F1 trên tập các lớp kỹ thuật mục tiêu được xác định trước.
  - **D2e-f (Denominators):** `INCLUDE_IN_DENOMINATOR` - Mã ATT&CK không hợp lệ và lỗi API đều bị tính là lỗi (Fail-Closed).
  - **D2h-i (Failure Decomposition):** `INDEPENDENT_AXES` - Bóc tách độc lập lỗi tìm kiếm và lỗi phân loại.
  - **D3 (Model Policy):** `ALLOW_LATEST_WITH_TIMESTAMP_BINDING` - Khóa chuỗi mô hình với tem thời gian UTC và dấu vân tay hệ thống.
  - **D4-D5 (Budget & Concurrency):** `SEQUENTIAL_ONLY` và `HARD_CAP_WORST_CASE_ATTEMPTS`.

### Ghi chú diễn giả (Speaker Notes)
> "Trước khi chạy bất kỳ thực nghiệm tính điểm nào, toàn bộ các quy tắc tính toán phải được đóng băng dưới Giao thức v1.1. Điều này ngăn chặn việc điều chỉnh luật tính toán sau khi có kết quả. Đặc biệt, chúng tôi áp dụng nguyên tắc Fail-Closed: nếu mô hình trả về mã sai cú pháp hoặc gặp lỗi mạng, mẫu đó đều bị tính là thất bại chứ không được loại trừ để 'làm đẹp' số liệu."

---

## Slide 6: Kết Quả RQ2 - Chẩn Đoán Khâu Truy Xuất (RQ2: Retrieval Diagnostics)

### Nội dung trình chiếu
- **Đánh giá độc lập bộ truy xuất trên 756 positive views:**
  - *Hit@1:* $4.23\%$ (32 / 756)
  - *Hit@3:* $16.80\%$ (127 / 756)
  - *Hit@5:* $24.21\%$ (183 / 756)
  - *Hit@10:* $45.11\%$ (341 / 756)
  - *Macro Recall@10:* $43.14\%$
  - **Tỷ lệ vắng mặt trong Top-10 (Retrieval Failure):** $54.89\%$ (415 / 756)
- **Phát hiện nút thắt cổ chai: Khoảng cách ngữ nghĩa (Semantic Gap) ở `T1136.001`:**
  - Kỹ thuật `T1136.001` (Create Account: Local Account) đạt **0% Top-10 Hit Rate (0 / 99 views)**.
  - *Nguyên nhân:* Nhật ký Windows Event ID 4720 sử dụng từ ngữ hệ thống ("A user account was created", "SamAccountName"), trong khi mô tả STIX ATT&CK nhấn mạnh hành vi và mục đích chiến thuật của kẻ tấn công ("adversaries may create a local account to maintain persistence").
  - Mô hình nhúng thông thường `all-MiniLM-L6-v2` không thể kết nối khoảng cách từ vựng này nếu không có từ điển miền hoặc bộ tìm kiếm hỗn hợp (Hybrid Search).

### Ghi chú diễn giả (Speaker Notes)
> "Kết quả nghiên cứu RQ2 chỉ ra một thực tế quan trọng: Bộ truy xuất dense retrieval độc lập chỉ đạt Hit@10 là 45.11%. Nghĩa là trong gần 55% trường hợp, kỹ thuật đúng hoàn toàn vắng mặt trong Top-10 ứng viên gửi cho LLM. Trường hợp điển hình là T1136.001 với 0/99 lần trúng Top-10. Đây là bằng chứng định lượng rõ ràng cho thấy nút thắt lớn nhất của RAG trong an toàn thông tin nằm ở khâu tìm kiếm ngữ nghĩa."

---

## Slide 7: Tác Động Của Hình Thức Biểu Diễn Telemetry (Representation Gap)

### Nội dung trình chiếu
- **So sánh cặp kịch bản đối ứng (Pairwise Single vs. Contextual across 670 pairs):**
  - Tổng số cặp hợp lệ (Eligible single-technique pairs): 252 cặp.
  - **Single-event tốt hơn Contextual-event:** **59 cặp** (23.4%).
  - **Contextual-event tốt hơn Single-event:** **23 cặp** (9.1%).
  - **Hiệu năng tương đương:** 170 cặp (trong đó cả hai cùng trượt Top-10: 119 cặp).
- **Hiện tượng Pha Loãng Ngữ Cảnh (Context Dilution):**
  - Khi gom nhiều sự kiện trong cùng một cửa sổ thời gian (Contextual representation), các sự kiện nền thông thường (như Explorer, DnsQuery, svchost) bổ sung thêm các token nhiễu.
  - Vector nhúng của toàn bộ đoạn văn bản bị kéo lệch khỏi hành vi độc hại cốt lõi, khiến kỹ thuật tấn công thực sự bị tụt hạng trong danh sách Top-k.
  - *Hàm ý thiết kế:* Cần có cơ chế lọc sự kiện liên quan (Event Filtering) trước khi đưa vào bộ nhúng.

### Ghi chú diễn giả (Speaker Notes)
> "Một phát hiện trực quan hóa sâu sắc là sự chênh lệch biểu diễn: Single-event vượt trội hơn Contextual-event ở 59 cặp so với chỉ 23 cặp chiều ngược lại. Thêm nhiều log xung quanh không giúp bộ truy xuất thông minh hơn, mà ngược lại gây ra hiện tượng pha loãng ngữ cảnh (Context Dilution). Điều này đặt ra yêu cầu phải tiền lọc log trước khi nhúng vector."

---

## Slide 8: Khung Đánh Giá End-to-End & Phân Rã Lỗi RQ1 (Attribution Schema)

### Nội dung trình chiếu
- **Mô hình phân rã lỗi có kiểm soát:**
  $$P(\text{Attribution Error}) = P(\text{Retrieval Failure}) + P(\text{Classification Failure} \mid \text{Retrieval Success})$$
- **Cấu trúc 5 nhánh thực nghiệm:**
  1. `no_rag`: Kiểm tra tri thức nội tại của LLM khi chỉ đọc log.
  2. `rag_k1`: Cung cấp 1 ứng viên có độ tương đồng cao nhất.
  3. `rag_k3`: Cung cấp 3 ứng viên.
  4. `rag_k5`: Độ sâu tiêu chuẩn (mặc định 5 ứng viên).
  5. `rag_k10`: Mở rộng tối đa không gian ứng viên.
- **Tính toán có điều kiện (Conditional Metrics):**
  - $P(\text{Correct} \mid \text{GT Retrieved in Top-}k)$: Đo lường năng lực lựa chọn của LLM khi bộ tìm kiếm đã làm việc thành công.
  - $P(\text{Correct} \mid \text{GT Absent from Top-}k)$: Đo lường khả năng LLM tự sửa sai dựa trên tri thức có sẵn khi bộ tìm kiếm thất bại.
- **Nguyên tắc Fail-Closed của Evaluator:**
  - Evaluator từ chối cho ra điểm số khoa học chính thức nếu tập ma trận chưa chạy trọn vẹn (bảo vệ tính toàn vẹn 6,400 bản ghi của tập TEST).

### Ghi chú diễn giả (Speaker Notes)
> "Khung đánh giá RQ1 của chúng tôi phân rã thành hai trục độc lập: Bộ truy xuất tìm sai, hay LLM phân loại sai dù thông tin đã được cung cấp? Phương pháp này giúp tránh việc đổ lỗi chung chung cho LLM khi thực chất nguyên nhân cốt lõi bắt nguồn từ khâu truy xuất thông tin."

---

## Slide 9: Nghiên Cứu Cắt Giảm & Chi Phí Thực Nghiệm RQ3 (Ablation & Cost Analysis)

### Nội dung trình chiếu
- **Kết quả thực nghiệm từ DEV Cost Pilot (20 cuộc gọi thực tế tới gpt-5.6-luna xhigh):**
  - Tỷ lệ tuân thủ schema JSON: **100% VALID** (20/20 bản ghi).
  - Số lần thử lại (retries): **0** (100% thành công ở lần gọi đầu tiên).
  - Độ trễ trung bình: **8,127.6 ms** (~8.1 giây / request).
- **Mức độ tiêu thụ tài nguyên theo độ sâu $k$:**
  | Điều kiện | Input Tokens TB | Output Tokens TB | Chi phí / Yêu cầu |
  | :--- | :---: | :---: | :---: |
  | `no_rag` ($k=0$) | 643.0 | 224.2 | ~$0.00039 |
  | `rag_k1` ($k=1$) | 1,115.0 | 332.2 | ~$0.00062 |
  | `rag_k3` ($k=3$) | 1,740.5 | 1,087.2 | ~$0.00165 |
  | `rag_k5` ($k=5$) | 2,518.2 | 840.2 | ~$0.00151 |
  | `rag_k10` ($k=10$) | 4,536.5 | 800.8 | ~$0.00187 |
- **Đánh giá chi phí tài chính:**
  - Chi phí thực tế đã thanh toán cho Pilot 20 requests: **$0.0242 USD** (~600 VNĐ).
  - Chi phí ước tính cho toàn bộ 6,400 requests của tập TEST chuẩn: **$8.20 – $8.99 USD** (hoàn toàn nằm trong ngưỡng ngân sách khả thi).
  - **Quy luật đánh đổi:** Tăng $k$ từ 1 lên 10 giúp tăng Hit rate từ 4.2% lên 45.1%, nhưng token đầu vào tăng gấp 4 lần, làm tăng chi phí và thời gian phản hồi.

### Ghi chú diễn giả (Speaker Notes)
> "Dựa trên số liệu thực nghiệm từ DEV Cost Pilot, việc tăng độ sâu k từ 0 lên 10 làm tăng token đầu vào khoảng 7 lần. Toàn bộ 20 request pilot đều tuân thủ schema tuyệt đối và không phát sinh retry nào. Với mức chi phí dự phóng chỉ khoảng 8 đến 9 USD cho toàn bộ 6,400 lượt suy luận của tập TEST, nghiên cứu chứng minh tính khả thi cao về mặt kinh tế khi áp dụng giải pháp này trong môi trường thực nghiệm."

---

## Slide 10: Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị (Limitations & Threats to Validity)

### Nội dung trình chiếu
1. **Phạm vi dữ liệu (Benchmark vs. Real Telemetry):**
   - Đánh giá hiện tại được thực hiện trên benchmark giả lập có cấu trúc Stage B (`synthetic-paired-v1`).
   - Mặc dù phản ánh sát các thuộc tính kỹ thuật của Windows logs, tập dữ liệu này chưa bao quát đầy đủ sự hỗn loạn và nhiễu của các chiến dịch APT thực tế (luồng dữ liệu thực địa T15 vẫn đang ở trạng thái chuẩn bị).
2. **Hạn chế của mô hình nhúng đơn tầng:**
   - Việc chỉ dựa vào dense semantic similarity (`all-MiniLM-L6-v2`) khiến hệ thống bỏ sót các từ khóa định danh cụ thể (ví dụ: Event ID 4720, tên tiến trình đặc biệt).
   - Cần bổ sung cơ chế tìm kiếm lai (Hybrid Search: Dense + Lexical BM25).
3. **Tính đại diện của LLM:**
   - Toàn bộ kết quả đối chứng được đo trên mô hình hàng đầu `gpt-5.6-luna`.
   - Cần kiểm chứng thêm trên các mô hình mã nguồn mở (Llama-3, Qwen) để xác nhận quy luật phân rã lỗi có mang tính khái quát giữa các họ mô hình hay không.

### Ghi chú diễn giả (Speaker Notes)
> "Chúng tôi luôn nhìn nhận nghiên cứu một cách khách quan: Benchmark Stage B rất hữu ích cho việc kiểm định lỗi nhưng chưa thể thay thế hoàn toàn dữ liệu thực tế. Ngoài ra, việc embedding model đơn tầng thất bại ở các Event ID số cho thấy trong tương lai, một hệ thống RAG an ninh mạng bắt buộc phải kết hợp cả tìm kiếm ngữ nghĩa lẫn tìm kiếm từ khóa (Lexical BM25)."

---

## Slide 11: Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học (Reproducibility & Contributions)

### Nội dung trình chiếu
- **Cam kết Tái Lập 100% Ngoại Tuyến (Zero-Cost Reproducibility):**
  - Bất kỳ thành viên hội đồng hoặc nhà nghiên cứu độc lập nào cũng có thể kiểm chứng toàn bộ số liệu bằng lệnh duy nhất:
    ```bash
    uv run python scripts/reproduce_study.py
    ```
  - Không cần mạng Internet, không cần tài khoản hay khóa API trả phí.
  - Toàn bộ 15 artifact và giao thức thực nghiệm được neo giữ bằng mã băm SHA-256.
- **Đóng góp khoa học cốt lõi:**
  1. *Quy trình thực nghiệm chuẩn hóa:* Thiết lập giao thức thực nghiệm đối chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán ánh xạ log Windows sang MITRE ATT&CK.
  2. *Bộ dữ liệu chẩn đoán:* Cung cấp 1,340 lượt kiểm tra có cấu trúc giúp định lượng chính xác điểm yếu của các bộ tìm kiếm dense retrieval trong an toàn thông tin.
  3. *Bằng chứng thực nghiệm định lượng:* Bóc tách độc lập hiện tượng context dilution và khoảng cách từ vựng, đặt nền móng vững chắc cho các cải tiến RAG tiếp theo.

### Ghi chú diễn giả (Speaker Notes)
> "Điểm sáng lớn nhất về mặt kỹ thuật của công trình là tính minh bạch và khả năng tái lập độc lập. Nhờ việc đóng băng 15 artifact và lưu trữ nhật ký thực nghiệm nguyên vẹn, bất kỳ ai cũng có thể chạy lại mã nguồn để xác thực từng con số mà không tốn bất kỳ chi phí nào. Đây là đóng góp thực chất cho cộng đồng nghiên cứu an toàn thông tin."

---

## Slide 12: Tổng Kết & Hỏi Đáp (Conclusion & Q&A)

### Nội dung trình chiếu
- **Tóm tắt kết luận:**
  - RAG cung cấp cơ sở tri thức quan trọng cho LLM, nhưng hiệu quả cuối cùng phụ thuộc rất lớn vào chất lượng của khâu truy xuất (Retrieval Quality).
  - Tăng độ sâu $k$ cải thiện đáng kể Hit rate (từ 4.2% lên 45.1%) nhưng làm tăng gấp 4 lần chi phí token đầu vào.
  - Hiện tượng pha loãng ngữ cảnh (Context Dilution) khẳng định tầm quan trọng của việc tiền lọc log có chọn lọc thay vì nhúng toàn bộ nhật ký xung quanh.
- **Định hướng phát triển:**
  - Tích hợp công nghệ Hybrid Search (Dense + Sparse/BM25) để khắc phục triệt để khoảng cách ngữ nghĩa ở các sự kiện như `T1136.001`.
  - Triển khai thực nghiệm đầy đủ trên tập dữ liệu Windows-APT thực tế khi hoàn thiện khâu khử khuẩn.
- **Trân trọng cảm ơn Quý Thầy Cô và Hội Đồng!**
- *Mời Quý Thầy Cô đặt câu hỏi thảo luận (Q&A).*

### Ghi chú diễn giả (Speaker Notes)
> "Tóm lại, RAG2ATT&CK đã chứng minh rằng để ứng dụng RAG thành công trong SOC, chúng ta không thể chỉ quan tâm đến mô hình ngôn ngữ lớn, mà phải giải quyết bài toán cốt lõi là tối ưu hóa bộ truy xuất và cấu trúc hóa biểu diễn log. Tôi xin chân thành cảm ơn sự lắng nghe của Quý Thầy Cô và kính mời Hội đồng đặt câu hỏi thảo luận."
