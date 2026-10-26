# KẾ HOẠCH TOÀN DIỆN ĐÓNG ĐIỂM CHẤT LƯỢNG VÀ KHẢ NĂNG TÁI LẬP (QUALITY & REPRODUCIBILITY CLOSURE PLAN)

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-03T03:38:00+07:00  
**Tác giả:** Native Quality & Reproducibility Specialist (Track F)  
**Nhánh Git:** `codex/finalization-quality-plan`  
**Base Commit:** `4fafdb290dac59070a43de33f7e299bbb25782e3`  
**Mục Tiêu:** Thiết lập lộ trình kỹ thuật chặt chẽ đạt chuẩn 13 Cổng Kiểm Chứng (V01–V13) nhằm giải quyết dứt điểm các tồn đọng về chất lượng mã nguồn (bao gồm 1.384 vi phạm Ruff và 3 bytes UTF-8 BOM) mà vẫn bảo toàn 100% tính nguyên vẹn khoa học lịch sử và mã băm thực thi đã niêm phong thông qua Kiến Trúc Ranh Giới Hai Tầng (Two-Tier Provenance Boundary Architecture).

---

## 1. NGUYÊN TẮC CỐT LÕI VÀ BẢO TOÀN XUẤT XỨ (PROVENANCE PRINCIPLES)

> [!IMPORTANT]
> **Nguyên Tắc Không Thỏa Hiệp:**
> 1. **Bảo tồn Tuyệt Đối Mã Băm Lịch Sử:** Khóa mã nguồn cốt lõi `core_manifest_sha256: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` gắn liền với đúng **53 tệp cốt lõi** (`src/`, `prompts/`, `config/model.json`, `config/pricing_v1.json`, `config/retrieval.json`, `pyproject.toml`, `uv.lock`, `.python-version`) của snapshot thực thi gốc `b69a6909acda4c7588744acc7e1d6c20bfce2612`. Không được sửa đổi dù chỉ 1 byte trong các tệp đã niêm phong rồi tuyên bố mã băm không đổi.
> 2. **Không Tự Ý Bỏ Qua Lỗi (No Silent Waivers):** Không sử dụng cờ bỏ qua rộng (`--ignore`, `--extend-ignore`) cho 1.384 vi phạm Ruff, không tự hạ thấp tiêu chuẩn kiểm định để tuyên bố đạt một cách giả tạo.
> 3. **Không Thay Đổi Định Nghĩa Khoa Học:** Mọi định nghĩa về Macro-F1 (474 lớp), ANY_MATCH, tập mẫu số $N=718$ mapped views, và các trục lỗi độc lập (Decision D2i) giữ nguyên vẹn 100%.

---

## 2. KIẾN TRÚC PHÂN TẦNG VÀ RANH GIỚI CÔ LẬP THỰC THI (TWO-TIER BOUNDARY ARCHITECTURE)

Để giải quyết mâu thuẫn giữa (1) việc bảo toàn mã băm nhị phân lịch sử `8b1b3ea...` của 53 tệp nguồn cốt lõi (chứa 3 bytes UTF-8 BOM tại `src/rag/__init__.py`) và (2) yêu cầu mã nguồn sạch hoàn toàn theo chuẩn linter hiện đại (Ruff clean, UTF-8 chuẩn không BOM), chúng tôi triển khai Kiến Trúc Ranh Giới Hai Tầng cô lập hoàn toàn môi trường thực thi:

```
+-----------------------------------------------------------------------------------+
| TẦNG 1: XUẤT XỨ LỊCH SỬ ĐÔNG KẾT (TIER 1 - HISTORICAL FROZEN PROVENANCE)        |
| - Vị trí: finalization_snapshots/b69a690 (Detached Clean Snapshot)                |
| - 53 tệp cốt lõi bất biến: core_manifest_sha256 = 8b1b3ea4d11a8e3c...             |
| - Bao gồm 3 bytes BOM tại src/rag/__init__.py: SHA256 1d16d258b4c3...             |
| - Ràng buộc trực tiếp với Terminal Process Proof: cbffe862...                     |
| - Sổ cái tài chính 6.400 requests đã chạy tại commit 80dbeb3                      |
| - Trình điều khiển: scripts/isolated_snapshot_controller.py (Stdlib only)         |
| - Trình thực thi: scripts/isolated_snapshot_worker.py (Socket Guard + Boundary)   |
| - Kiểm tra biên giới Origin: 100% loaded modules thuộc snapshot_root              |
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

### Cơ Chế Bảo Vệ Ranh Giới (Boundary Protection Mechanism)
1. **Isolated Snapshot Controller (`scripts/isolated_snapshot_controller.py`):**
   - Hoàn toàn viết bằng Python standard library (không phụ thuộc bên thứ ba).
   - Thiết lập môi trường sạch cho subprocess con: `PYTHONNOUSERSITE=1`, loại bỏ `PYTHONPATH`, thu hồi thông tin xác thực (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, v.v.).
   - Khởi chạy subprocess bằng cờ `-I` (isolated mode) của Python và `--offline-guard` socket blocking.
   - Đo lường mã băm toàn diện (fingerprint) của toàn bộ snapshot trước và sau khi worker chạy (`pre_fingerprint == post_fingerprint = ae9b992b30275075f20cebc25d64195a54d42db9fdd1c12acc735e664d6d68fd`), đảm bảo snapshot hoàn toàn bất biến (`immutability_verified = True`).
2. **Origin Boundary Guard (`scripts/isolated_snapshot_worker.py`):**
   - Kiểm tra mọi module được nạp thuộc `src.*` qua `__file__`, `__spec__.origin`, và `co_filename`.
   - Bất kỳ module nào được nạp nằm ngoài thư mục `snapshot_root` sẽ bị chặn đứng lập tức (`fail-closed`).
   - Đạt kết quả kiểm chứng thực tế: 25/25 modules nạp vào đều có origin xuất xứ 100% từ `finalization_snapshots/b69a690`.

---

## 3. LỘ TRÌNH CHI TIẾT 13 CỔNG KIỂM CHỨNG (V01 – V13)

| Mã Cổng | Tên Cổng Kiểm Chứng | Tiêu Chí Đạt Cụ Thể (Pass Criteria) | Trạng Thái Hiện Tại | Kế Hoạch Đóng Điểm |
| :---: | :--- | :--- | :---: | :--- |
| **V01** | **Frozen Core Integrity** | Khóa `config/canonical_experiment_lock_v1.json` khớp `8b1b3ea...` cho 53 tệp cốt lõi. | **ĐÃ ĐẠT (PASS)** | Bảo vệ nguyên vẹn tại Tầng 1 qua controller fingerprint. |
| **V02** | **Monetary Ledger Guard** | Trần \$19.99, chi phí settled \$6.57575890, tạm giữ \$0.05264010, khả dụng \$13.36160100, 0 vi phạm. | **ĐÃ ĐẠT (PASS)** | Đã nghiệm thu độc lập tại b69a690 (Track A). |
| **V03** | **Journal Reconciliation** | 6.401 attempt receipts khớp với 6.400 bản ghi, 1 lần retry thành công, 1.540 cached tokens. | **ĐÃ ĐẠT (PASS)** | Đã tích hợp trong `build_canonical_metric_bundle.py`. |
| **V04** | **Terminal Outcomes** | 7 kết quả đông kết, 6.387 VALID, 13 INCOMPLETE, 0 lỗi cú pháp hoặc mã kỹ thuật không hợp lệ. | **ĐÃ ĐẠT (PASS)** | Đã kiểm chứng độc lập. |
| **V05** | **Benchmark Denominators** | 718 mapped views (678 single-GT, 40 multi-GT), 474 frozen classes (8 supported, 466 unsupported). | **ĐÃ ĐẠT (PASS)** | Đã cấu trúc trong Bundle v2. |
| **V06** | **Numerical Invariance** | Khớp 100% kết quả S2_RQ_V2: No-RAG 77.99%, k10 79.53%, delta +1.532 pp, McNemar p=0.422. | **ĐÃ ĐẠT (PASS)** | Đã đóng băng trong Bundle v2. |
| **V07** | **Metric Bundle Validation** | Bộ sinh và kiểm tra fail-closed `canonical_metric_bundle_v2.json` đạt 100% tests (22/22 tests). | **ĐÃ HOÀN TẤT (TRACK B)** | Đã tạo PR #32, SHA `7409ce3...`, CI Run 37060468975 xanh 100%. |
| **V08** | **Publication Artifacts** | Đủ 8 hình ảnh vector và 6 bảng biểu, 0 rò rỉ đường dẫn cá nhân, 0 placeholder chưa giải quyết. | **ĐANG SỬA (TRACK D)** | Đang nâng cấp checker cấu trúc OOXML/SVG và sửa generator. |
| **V09** | **Offline Network Guard** | Toàn bộ kiểm thử chạy qua `scripts/run_offline_tests.py`, `installed=True, attempted_egress=0`. | **ĐÃ ĐẠT (PASS)** | Áp dụng bắt buộc cho mọi test execution. |
| **V10** | **Code Quality & Style** | Khắc phục toàn bộ vi phạm Ruff trên codebase thông qua quy trình AST-invariant. | **KẾ HOẠCH GIAI ĐOẠN F** | Sẵn sàng thực hiện sau khi Root duyệt Boundary Architecture. |
| **V11** | **UTF-8 BOM Normalization**| Chuẩn hóa 3 bytes BOM tại `src/rag/__init__.py` sang Tầng 2 mà không phá vỡ Tầng 1. | **KẾ HOẠCH GIAI ĐOẠN F** | Áp dụng chuyển đổi có đối chiếu AST. |
| **V12** | **CI Matrix Multi-Platform**| Chạy xanh 100% CI trên Ubuntu-24.04 và Windows-latest (CI, Synthetic, Registry, Integration). | **ĐÃ ĐẠT TRÊN PR #32** | 4/4 jobs GitHub Actions pass hoàn hảo. |
| **V13** | **Clean-Clone Repro** | Bản sao clone sạch từ Git có thể tái lập toàn bộ quy trình mà không cần bất kỳ đường dẫn cá nhân nào. | **KẾ HOẠCH GIAI ĐOẠN F** | Tái lập độc lập qua Isolated Snapshot Controller. |

---

## 4. CHI TIẾT XỬ LÝ SỰ CỐ UTF-8 BOM TẠI `src/rag/__init__.py` (CỔNG V11)

### Hiện Trạng Kỹ Thuật:
Tệp `src/rag/__init__.py` bắt đầu bằng 3 byte UTF-8 Byte Order Mark: `0xEF, 0xBB, 0xBF`.
- Mã băm SHA-256 thực tế hiện tại (có BOM): `1d16d258b4c3f89aac043fad68a19031bf16d21daad4251846ba2f4297fa16c1`.
- Mã băm này là một phần cấu thành bất biến của `core_manifest_sha256: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` (53 tệp cốt lõi).
- Trình kiểm tra `scripts/isolated_snapshot_worker.py` trong tác vụ `verify_baselines` đã xác nhận: `src_rag_init_has_bom = True` và SHA khớp chính xác `1d16d258...`.

### Giải Pháp Kỹ Thuật Hai Tầng:
1. **Bảo Tồn Tuyệt Đối Tầng 1:** Tệp gốc có BOM được giữ nguyên trong snapshot lịch sử để phục vụ xác thực mã băm `8b1b3ea...`.
2. **Khử BOM Có Đối Chiếu AST Khi Chuyển Sang Tầng 2:**
   ```python
   import ast

   raw_bytes = path_t1.read_bytes()
   assert raw_bytes.startswith(b"\xef\xbb\xbf")
   clean_bytes = raw_bytes[3:]

   tree_t1 = ast.parse(raw_bytes)
   tree_t2 = ast.parse(clean_bytes)
   assert ast.dump(tree_t1) == ast.dump(tree_t2)
```
   Khẳng định việc loại bỏ BOM không làm thay đổi ngữ nghĩa logic hoặc cấu trúc mã thực thi.

---

## 5. KẾ HOẠCH KHẮC PHỤC 1.384 VI PHẠM RUFF (CỔNG V10)

### Phân Bố Thực Tế 1.384 Vi Phạm:
Dựa trên phân tích tĩnh toàn diện:
- **E501 (Line too long):** **1.110 vi phạm** (chiếm **80.2%** tổng số vi phạm). Đây là các dòng dài vượt quá 88/100 ký tự (chủ yếu trong prompts, docstrings, schema tables). Hoàn toàn tự động format hoặc wrap mà không ảnh hưởng tới AST.
- **I001 (Unsorted imports) & F401 (Unused imports):** ~200 vi phạm (~14.5%). Tự động chuẩn hóa bằng `ruff check --select I,F401 --fix`.
- **F841 / F821 / Các lỗi biến số khác:** ~74 vi phạm (~5.3%). Rà soát thủ công có kiểm thử hồi quy đối chiếu kết quả.

### Quy Trình Triển Khai:
1. **Giai Đoạn 1 (Prep & Plan):** Nghiệm thu Kiến Trúc Ranh Giới Hai Tầng và chứng thư kiểm thử `test_snapshot_boundary_isolation.py`.
2. **Giai Đoạn 2 (Branching & Staging):** Tạo nhánh riêng `codex/engineering-tier2-quality` từ candidate repo.
3. **Giai Đoạn 3 (Automated Formatting with AST Verification):** Chạy script chuẩn hóa định dạng kèm kiểm tra tự động `assert ast.dump(before) == ast.dump(after)`.
4. **Giai Đoạn 4 (Offline Guard Testing):** Chạy toàn bộ test suite (`scripts/run_offline_tests.py`) đảm bảo 100% tests vượt qua và số liệu thực nghiệm không lệch một chữ số.
5. **Giai Đoạn 5 (CI Verification):** Đẩy lên remote và kiểm chứng CI trên cả Ubuntu và Windows.

---

## 6. CHỨNG TỰ THỰC NGHIỆM ĐÃ ĐẠT CỦA BỘ ĐIỀU KHIỂN RANH GIỚI (EVIDENCE ATTESTATION)

Bộ điều khiển `scripts/isolated_snapshot_controller.py` và worker `scripts/isolated_snapshot_worker.py` đã được kiểm thử toàn diện qua bộ test `tests/test_snapshot_boundary_isolation.py` (6 bài test positive và negative controls) dưới `scripts/run_offline_tests.py`:

```
tests/test_snapshot_boundary_isolation.py::test_positive_snapshot_preflight PASSED [ 16%]
tests/test_snapshot_boundary_isolation.py::test_positive_snapshot_baselines PASSED [ 33%]
tests/test_snapshot_boundary_isolation.py::test_negative_wrong_snapshot_root PASSED [ 50%]
tests/test_snapshot_boundary_isolation.py::test_negative_offline_guard_egress_interception PASSED [ 66%]
tests/test_snapshot_boundary_isolation.py::test_negative_snapshot_immutability_violation PASSED [ 83%]
tests/test_snapshot_boundary_isolation.py::test_negative_simulated_source_drift_breaks_manifest PASSED [100%]

============================== 6 passed in 9.21s ==============================
OFFLINE_GUARD: installed=True attempted_egress=0
```

- **Kết quả Attestation:**
  - `pre_fingerprint` == `post_fingerprint` = `ae9b992b30275075f20cebc25d64195a54d42db9fdd1c12acc735e664d6d68fd`
  - `file_count`: 53 tệp cốt lõi
  - `loaded_origins_count`: 25 module nguồn tải vào đều bắt nguồn từ `snapshot_root`
  - `attempted_egress_count`: 0
  - `status`: PASS

---

## 7. CAM KẾT PHẠM VI TRONG PHA HIỆN TẠI

- **KHÔNG** chỉnh sửa bất kỳ tệp nào trong `src/` lúc này.
- **KHÔNG** sửa đổi `pyproject.toml`, `uv.lock` hay cấu hình linter.
- **KHÔNG** xóa 3 bytes BOM tại `src/rag/__init__.py` khi chưa có sự phê chuẩn chính thức của Root Reviewer đối với kế hoạch này.
- **KHÔNG** thực hiện public release hay merge vào `main`.
