# KẾ HOẠCH TOÀN DIỆN ĐÓNG ĐIỂM CHẤT LƯỢNG VÀ KHẢ NĂNG TÁI LẬP (QUALITY & REPRODUCIBILITY CLOSURE PLAN)

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-03T03:12:00+07:00  
**Tác giả:** Native Quality & Reproducibility Specialist (Track F)  
**Nhánh Git:** `codex/finalization-quality-plan`  
**Base Commit:** `4fafdb290dac59070a43de33f7e299bbb25782e3`  
**Mục Tiêu:** Thiết lập lộ trình kỹ thuật chặt chẽ đạt chuẩn 13 Cổng Kiểm Chứng (V01–V13) nhằm giải quyết dứt điểm các tồn đọng về chất lượng mã nguồn (bao gồm 1.384 vi phạm Ruff và 3 bytes UTF-8 BOM) mà vẫn bảo toàn 100% tính nguyên vẹn khoa học lịch sử và mã băm thực thi đã niêm phong.

---

## 1. NGUYÊN TẮC CỐT LÕI VÀ BẢO TOÀN XUẤT XỨ (PROVENANCE PRINCIPLES)

> [!IMPORTANT]
> **Nguyên Tắc Không Thỏa Hiệp:**
> 1. **Bảo tồn Tuyệt Đối Mã Băm Lịch Sử:** Khóa mã nguồn cốt lõi `core_manifest_sha256: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` gắn liền với 15 tệp snapshot thực thi gốc và chứng thư `cbffe862...` là bất biến. Không được sửa đổi dù chỉ 1 byte trong các tệp đã niêm phong rồi tuyên bố mã băm không đổi.
> 2. **Không Tự Ý Bỏ Qua Lỗi (No Silent Waivers):** Không sử dụng cờ bỏ qua rộng (`--ignore`, `--extend-ignore`) cho 1.384 vi phạm Ruff, không tự hạ thấp tiêu chuẩn kiểm định để tuyên bố đạt một cách giả tạo.
> 3. **Không Thay Đổi Định Nghĩa Khoa Học:** Mọi định nghĩa về Macro-F1 (474 lớp), ANY_MATCH, tập mẫu số $N=718$ mapped views, và các trục lỗi độc lập (Decision D2i) giữ nguyên vẹn 100%.

---

## 2. KIẾN TRÚC PHÂN TẦNG XUẤT XỨ (TWO-TIER PROVENANCE ARCHITECTURE)

Để giải quyết mâu thuẫn giữa (1) việc bảo toàn mã băm nhị phân lịch sử `8b1b3ea...` của 15 tệp nguồn (chứa 3 bytes UTF-8 BOM tại `src/rag/__init__.py`) và (2) yêu cầu mã nguồn sạch hoàn toàn theo chuẩn linter hiện đại (Ruff clean, UTF-8 chuẩn không BOM), chúng tôi đề xuất Kiến Trúc Xuất Xứ Hai Tầng minh bạch:

```
+-----------------------------------------------------------------------------------+
| TẦNG 1: XUẤT XỨ LỊCH SỬ ĐÔNG KẾT (TIER 1 - HISTORICAL FROZEN PROVENANCE)        |
| - 15 tệp cốt lõi bất biến: code_manifest_sha256 = 8b1b3ea...                      |
| - Bao gồm 3 bytes BOM tại src/rag/__init__.py (SHA256: 494f6f...)                |
| - Ràng buộc trực tiếp với Terminal Process Proof: cbffe862...                     |
| - Gắn liền với dữ liệu thô 6.400 requests đã chạy tại commit 80dbeb3              |
| - Chứng minh tính toàn vẹn pháp lý và khoa học của dữ liệu thực nghiệm đã công bố |
+-----------------------------------------------------------------------------------+
                                      │
                                      ▼
           [GIAO THỨC CHUYỂN HÓA BẢO TOÀN AST & SỐ HỌC (AST-INVARIANT PROTOCOL)]
           - Khử 3 bytes BOM bằng chuyển đổi chuẩn: bytes.decode('utf-8-sig').encode('utf-8')
           - Chuẩn hóa định dạng mã nguồn tự động qua ruff format (không đổi AST)
           - Đối chiếu Abstract Syntax Tree: ast.dump(T1) == ast.dump(T2)
           - Kiểm chứng Numerical Replay: Evaluator(T2) cho ra 100% số liệu khớp Bundle v2
                                      │
                                      ▼
+-----------------------------------------------------------------------------------+
| TẦNG 2: MÃ NGUỒN KỸ THUẬT HIỆN ĐẠI (TIER 2 - MODERN CLEAN ENGINEERING SOURCE)     |
| - Toàn bộ mã nguồn tuân thủ Ruff lint & format (0 lỗi, 0 warnings)                |
| - Định dạng tệp 100% chuẩn UTF-8 (không BOM)                                      |
| - Khóa dẫn xuất mới: modern_code_manifest_sha256 (được ghi nhận trong manifest)  |
| - Phục vụ phát triển lâu dài, bảo trì, kiểm thử tích hợp mở rộng                  |
+-----------------------------------------------------------------------------------+
```

---

## 3. LỘ TRÌNH CHI TIẾT 13 CỔNG KIỂM CHỨNG (V01 – V13)

| Mã Cổng | Tên Cổng Kiểm Chứng | Tiêu Chí Đạt Cụ Thể (Pass Criteria) | Trạng Thái Hiện Tại | Kế Hoạch Đóng Điểm |
| :---: | :--- | :--- | :---: | :--- |
| **V01** | **Frozen Core Integrity** | Khóa `config/canonical_experiment_lock_v1.json` khớp `8b1b3ea...` cho 15 tệp lịch sử. | **ĐÃ ĐẠT (PASS)** | Duy trì bảo vệ ở Tầng 1. |
| **V02** | **Monetary Ledger Guard** | Trần \$19.99, chi phí settled \$6.57575890, tạm giữ \$0.05264010, khả dụng \$13.36160100, 0 vi phạm. | **ĐÃ ĐẠT (PASS)** | Đã nghiệm thu độc lập tại b69a690 (Track A). |
| **V03** | **Journal Reconciliation** | 6.401 attempt receipts khớp với 6.400 bản ghi, 1 lần retry thành công, 1.540 cached tokens. | **ĐÃ ĐẠT (PASS)** | Đã tích hợp trong `build_canonical_metric_bundle.py`. |
| **V04** | **Terminal Outcomes** | 7 kết quả đông kết, 6.387 VALID, 13 INCOMPLETE, 0 lỗi cú pháp hoặc mã kỹ thuật không hợp lệ. | **ĐÃ ĐẠT (PASS)** | Đã kiểm chứng độc lập. |
| **V05** | **Benchmark Denominators** | 718 mapped views (678 single-GT, 40 multi-GT), 474 frozen classes (8 supported, 466 unsupported). | **ĐÃ ĐẠT (PASS)** | Đã cấu trúc trong Bundle v2. |
| **V06** | **Numerical Invariance** | Khớp 100% kết quả S2_RQ_V2: No-RAG 77.99%, k10 79.53%, delta +1.532 pp, McNemar p=0.422. | **ĐÃ ĐẠT (PASS)** | Đã đóng băng trong Bundle v2. |
| **V07** | **Metric Bundle Validation** | Bộ sinh và kiểm tra fail-closed `canonical_metric_bundle_v2.json` đạt 100% tests. | **ĐÃ HOÀN TẤT (TRACK B)** | Đã tạo PR #32, chờ Root Reviewer nghiệm thu SHA `e96a3b7...`. |
| **V08** | **Publication Artifacts** | Đủ 8 hình ảnh vector và 6 bảng biểu, 0 rò rỉ đường dẫn cá nhân, 0 placeholder chưa giải quyết. | **SẴN SÀNG (TRACK D)** | Khung generator đã hoàn tất (PR #33), chạy fixture pass 100%. |
| **V09** | **Offline Network Guard** | Toàn bộ kiểm thử chạy qua `scripts/run_offline_tests.py`, `installed=True, attempted_egress=0`. | **ĐÃ ĐẠT (PASS)** | Đang áp dụng bắt buộc cho mọi test. |
| **V10** | **Code Quality & Style** | Khắc phục toàn bộ vi phạm Ruff trên codebase thông qua quy trình AST-invariant. | **KẾ HOẠCH GIAI ĐOẠN F** | Thực hiện tuần tự sau khi Kế hoạch được Root duyệt. |
| **V11** | **UTF-8 BOM Normalization**| Chuẩn hóa 3 bytes BOM tại `src/rag/__init__.py` sang Tầng 2 mà không phá vỡ Tầng 1. | **KẾ HOẠCH GIAI ĐOẠN F** | Áp dụng chuyển đổi có đối chiếu AST. |
| **V12** | **CI Matrix Multi-Platform**| Chạy xanh 100% CI trên Ubuntu-24.04 và Windows-latest (CI, Synthetic, Registry, Integration). | **ĐANG CHẠY TRÊN PR #32** | Đang xác thực trên GitHub Actions. |
| **V13** | **Clean-Clone Repro** | Bản sao clone sạch từ Git có thể tái lập toàn bộ quy trình mà không cần bất kỳ đường dẫn cá nhân nào. | **KẾ HOẠCH GIAI ĐOẠN F** | Viết script kiểm chứng clone độc lập. |

---

## 4. CHI TIẾT XỬ LÝ SỰ CỐ UTF-8 BOM TẠI `src/rag/__init__.py` (CỔNG V11)

### Hiện Trạng Kỹ Thuật:
Tệp `src/rag/__init__.py` bắt đầu bằng 3 byte UTF-8 Byte Order Mark: `0xEF, 0xBB, 0xBF`.
- Mã băm SHA-256 hiện tại (có BOM): `494f6f1c4e7cf5d5d8fa2dc504c568ae98e8d5f3066347da038f4a7c88085601`.
- Mã băm này là một phần cấu thành của `core_manifest_sha256: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4`.
- Một số công cụ linter/format (như Ruff) cảnh báo sự hiện diện của BOM trong mã nguồn Python 3.

### Giải Pháp Kỹ Thuật Đề Xuất (Không Xâm Phạm Dữ Liệu Đông Kết):
1. **Lập Bản Đồ Chuyển Đổi Rõ Ràng (Deterministic Transformation Map):**
   - Không âm thầm xóa BOM trên tệp gốc rồi tự nhận hash cũ.
   - Khi chuyển sang Tầng 2, một công cụ di chuyển chuyên dụng (`scripts/migrate_source_tier2.py`) sẽ đọc tệp dưới dạng nhị phân, kiểm tra chính xác 3 byte đầu là `\xef\xbb\xbf`, ghi lại bản ghi chứng cứ (transformation receipt) với SHA gốc và SHA mới.
2. **Kiểm Tra Bất Biến Cú Pháp (AST Invariance Check):**
   ```python
   import ast

   tree_t1 = ast.parse(path_t1.read_bytes())
   tree_t2 = ast.parse(path_t2.read_bytes())
   assert ast.dump(tree_t1) == ast.dump(tree_t2)
   ```
   Khẳng định rằng việc loại bỏ BOM không làm thay đổi ngữ nghĩa logic hoặc cấu trúc mã thực thi.
3. **Lưu Trữ Song Song:** Giữ liên kết dẫn xuất rõ ràng trong manifest xuất bản, phân định rạch ròi giữa bản ghi lịch sử và bản ghi phát triển.

---

## 5. KẾ HOẠCH KHẮC PHỤC 1.384 VI PHẠM RUFF (CỔNG V10)

### Phân Loại 1.384 Vi Phạm:
Dựa trên phân tích phân bố lỗi Ruff:
- **Nhóm 1: Formatting & Line Length (E501, W291, W292, W293):** Chiếm ~65% vi phạm. Hoàn toàn tự động sửa đổi bằng `ruff format` mà không ảnh hưởng tới AST.
- **Nhóm 2: Import Sorting & Unused Imports (I001, F401):** Chiếm ~20% vi phạm. Tự động chuẩn hóa bằng `ruff check --select I,F401 --fix`.
- **Nhóm 3: Undefined Names / Variables (F821, F841):** Chiếm ~10% vi phạm. Cần rà soát thủ công có kiểm thử hồi quy kèm theo.
- **Nhóm 4: Docstrings & Type Annotations:** Chiếm ~5%.

### Quy Trình Triển Khai:
1. **Giai Đoạn 1 (Prep & Plan):** Trình nộp kế hoạch này và nhận nghiệm thu từ Root Reviewer.
2. **Giai Đoạn 2 (Branching & Staging):** Tạo nhánh riêng `codex/engineering-tier2-quality` từ candidate repo.
3. **Giai Đoạn 3 (Automated Formatting with AST Verification):** Chạy script chuẩn hóa định dạng kèm kiểm tra tự động `assert ast.dump(before) == ast.dump(after)`.
4. **Giai Đoạn 4 (Offline Guard Testing):** Chạy toàn bộ test suite (`scripts/run_offline_tests.py`) đảm bảo 100% tests vượt qua và số liệu thực nghiệm không lệch một chữ số.
5. **Giai Đoạn 5 (CI Verification):** Đẩy lên remote và kiểm chứng CI trên cả Ubuntu và Windows.

---

## 6. CAM KẾT PHẠM VI TRONG PHA HIỆN TẠI

- **KHÔNG** chỉnh sửa bất kỳ tệp nào trong `src/` lúc này.
- **KHÔNG** sửa đổi `pyproject.toml`, `uv.lock` hay cấu hình linter.
- **KHÔNG** xóa 3 bytes BOM tại `src/rag/__init__.py` khi chưa có sự phê chuẩn chính thức của Root Reviewer đối với kế hoạch này.
- **KHÔNG** thực hiện public release hay merge vào `main`.
