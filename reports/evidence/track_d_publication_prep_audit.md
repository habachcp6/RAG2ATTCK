# BÁO CÁO KIỂM TOÁN CHUẨN BỊ TRACK D (PUBLICATION PREP AUDIT)

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-03T03:09:30+07:00  
**Tác giả:** Native Figures Worker (Track D)  
**Nhánh Git:** `codex/finalization-publication-gen`  
**Base Commit:** `4fafdb290dac59070a43de33f7e299bbb25782e3`  

---

## 1. PHẠM VI VÀ PHÂN QUYỀN TRACK D

Track D chịu trách nhiệm:
1. `scripts/generate_publication_figures.py`: Bộ sinh 8 hình ảnh vector đồ họa xuất bản (Publication Figures).
2. `scripts/generate_publication_tables.py`: Bộ sinh 6 bảng biểu Markdown/JSON xuất bản (Publication Tables).
3. `scripts/check_cross_artifact_consistency.py`: Bộ kiểm tra tính nhất quán chéo văn bản (Cross-Artifact Consistency Checker).
4. `tests/test_cross_artifact_consistency.py`: Bộ kiểm thử tự động kiểm tra rò rỉ đường dẫn, placeholders và tính toàn vẹn dữ liệu.
5. Thư mục đích: `docs/report/figures/` và `docs/report/tables/`.

**Giới Hạn Nghiêm Ngặt:**
- Tuyệt đối không can thiệp hay sửa đổi `docs/report/scientific_report.md`, `scientific_report.docx`, `README.md`, hay `docs/presentation/slides.md` (thuộc phân quyền của Track C, E, F).
- Phân định rạch ròi chế độ chạy thử nghiệm (`--fixture-only`) và chế độ chính thức (`--metric-bundle`).
- Không sinh dữ liệu giả tạo (fake data) để tự nhận là canonical; chờ Root Reviewer nghiệm thu SHA của Bundle v2 mới tiến hành sinh toàn bộ canonical figures/tables.

---

## 2. KHUNG 8 HÌNH ẢNH VECTOR (PUBLICATION FIGURES)

| Mã Hình | Tiêu Đề Xuất Bản | Chủ Đề / Định Dạng | Ghi Chú Kỹ Thuật |
| :--- | :--- | :--- | :--- |
| **Figure 1** | Dual-View Attribution Architecture | Sơ đồ kiến trúc luồng dữ liệu 4 tầng | CTI log -> all-MiniLM-L6-v2 -> FAISS -> gpt-5.6-luna (xhigh) |
| **Figure 2** | Attribution Accuracy vs. Depth $k$ | Biểu đồ cột + đường xu hướng (No-RAG vs k=1,3,5,10) | Mẫu số $N=718$, hiển thị khoảng tin cậy 95% Bootstrap CI |
| **Figure 3** | Macro-F1 vs. Depth $k$ | Đồ thị Macro-F1 trên 474 lớp ATT&CK | Khung 474 frozen classes (8 supported, 466 zero-support) |
| **Figure 4** | Retrieval Hit Rate (Recall@k) | Tỷ lệ tìm thấy kỹ thuật mục tiêu | k=1 (22.98%), k=3 (16.43%), k=5 (24.09%), k=10 (44.71%) |
| **Figure 5** | Conditional Accuracy (Hit vs. Miss) | So sánh $P(\text{Đúng} \mid \text{Hit})$ vs. $P(\text{Đúng} \mid \text{Miss})$ | k=10: 91.28% khi Hit vs. 70.03% khi Miss |
| **Figure 6** | Request Latency Scaling | Độ trễ Mean & Median (ms) theo điều kiện | Phạm vi client loop gồm retry backoff; **Ẩn p95 Latency** |
| **Figure 7** | Cost ($) & Token Consumption | Chi phí sổ cái ($) và tổng token tiêu thụ | Phản ánh phụ phí missing usage k=1; ghi chú 1.540 cached tokens |
| **Figure 8** | Independent Failure Decomposition | Phân rã lỗi độc lập theo Decision D2i | 147 lỗi phân loại, 397 miss, giao thoa 119 (80.95% lỗi) |

---

## 3. KHUNG 6 BẢNG BIỂU XUẤT BẢN (PUBLICATION TABLES)

| Mã Bảng | Tệp Sinh Ra | Nội Dung Chi Tiết |
| :--- | :--- | :--- |
| **Table 1** | `table1_dataset_and_cohort.md` | Phân vùng tập dữ liệu: 1.280 views, 640 pairs, 718 mapped, 311 ambiguous, 251 unmapped, 678 single-GT, 40 multi-GT, 474 macro universe. |
| **Table 2** | `table2_experimental_conditions.md` | Cấu hình 5 điều kiện thực nghiệm, mô hình embedding, faiss index, gpt-5.6-luna, reasoning xhigh, ràng buộc D1-D7. |
| **Table 3** | `table3_rq1_attribution_performance.md` | Hiệu năng RQ1: Accuracy, Macro-F1, Delta vs Baseline, 95% Bootstrap CI, McNemar exact p ($p=0.422$ tại k=10, không có ý nghĩa thống kê). |
| **Table 4** | `table4_rq2_retrieval_and_error.md` | Hiệu năng truy xuất RQ2: Hit rate, P(correct\|hit), P(correct\|miss), phân rã lỗi theo các trục độc lập D2i. |
| **Table 5** | `table5_rq3_resources_and_cost.md` | Tài nguyên RQ3: Latency mean/median ms, phân rã tokens (prompt, completion, cache), chi phí settled ledger, bảo toàn tiền tệ \$19.99 trần. |
| **Table 6** | `table6_provenance_and_hashes.md` | Dòng dõi & mã băm: Git commits, core manifest, protocol, pricing contract, public manifest, terminal seal, bundle v2 hash. |

---

## 4. BỘ KIỂM TRA NHẤT QUÁN CHÉO (CROSS-ARTIFACT CONSISTENCY CHECKER)

Công cụ `scripts/check_cross_artifact_consistency.py` thực hiện:
1. **Quét rò rỉ đường dẫn máy tính cá nhân:** Phát hiện các chuỗi `C:/Users/hahoa`, `D:/RAG2ATTCK` trong toàn bộ tài liệu xuất bản.
   - Kết quả trên artifacts sinh ra bởi Track D: **0 rò rỉ (PASS)**.
   - Kiểm tra inventory toàn repo: Đã phát hiện 1 đường dẫn cá nhân còn sót lại trong tài liệu trình chiếu `docs/presentation/slides.md` (dòng 236), ghi nhận vào báo cáo để chuyển giao cho người sở hữu Track E sửa đổi.
2. **Quét Placeholder:** Phát hiện các chuỗi chưa được điền giá trị như `{{...}}`, `[PENDING]`, `[TBD]`, `TBD_AT_EXECUTION`.
   - Bảng biểu Track D: **0 placeholder (PASS)**.
   - Tài liệu báo cáo `scientific_report.md`: Ghi nhận 295 vị trí `[TBD_AT_EXECUTION]` sẵn sàng để Track C điền số tự động sau khi Bundle v2 được freeze.
3. **Kiểm tra xuất xứ và mã băm:** Kiểm tra `figure_provenance.json` và `table_provenance.json` đầy đủ 8 hình và 6 bảng.

---

## 5. KẾT QUẢ KIỂM THỬ (OFFLINE GUARD)

Chạy kiểm thử với `scripts/run_offline_tests.py tests/test_cross_artifact_consistency.py -v`:
- 5/5 tests đạt (100% PASS) trong 0.32s.
- `OFFLINE_GUARD: installed=True attempted_egress=0`.
- Các ca kiểm thử phủ định (Fail-Closed Negative Controls) hoạt động chính xác: phát hiện rò rỉ đường dẫn, phát hiện placeholder, phát hiện thiếu tệp bảng/hình.
