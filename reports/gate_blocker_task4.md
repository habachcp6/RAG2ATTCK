# Báo cáo Cổng Chặn Phương Pháp Luận — Task 4 (Ground Truth Verification)

- **Thời gian**: 2026-09-16 01:38:00 UTC
- **Dự án**: RAG2ATTCK — Data & Ground Truth Pipeline
- **Dataset**: Windows-APT 2025 v3 (`b8fmtzvpy8.3`)
- **Trạng thái cổng**: **BLOCKED / STOP (Task 4 Gate)**
- **Quy tắc tuân thủ**: Early termination tại cổng chặn là **hành vi hợp lệ (compliant behavior)** theo đúng thiết kế của kế hoạch.

---

## 1. Tóm tắt kết quả các Tasks đã hoàn thành

| Task | Tên tác vụ | Kết quả | Sản phẩm chính |
|---|---|:---:|---|
| **T0** | Preflight: workspace, paths, capacity | **PASS** | `preflight.json`, `source_context.json`, 9/9 tests pass, dung lượng trống 30.37 GiB (dư +25.37 GiB). |
| **T1** | Scaffold & reproducible environment | **PASS** | Local Git, `pyproject.toml`, `uv.lock`, `.venv`, CLI `src/data_ground_truth.py`. |
| **T5-acquire** | Enterprise ATT&CK v19.2 reference | **PASS** | `enterprise-attack-19.2.json` (53.84 MB, SHA-256 đối chiếu khớp), `attack_manifest.json` (858 kỹ thuật, 474 kỹ thuật Windows). |
| **T2** | Dataset acquisition & immutable provenance | **PASS** | 21/21 tệp (480.86 MB) tại `data/raw/windows_apt_2025/v3/`, `dataset_manifest.json`, đối chiếu multiset khớp chính xác 102,011 hàng (delta = 0). |
| **T3** | Schema profiling & observation units | **PASS** | 102,011 bản ghi, 377 trường, 0 bản ghi lỗi (`schema_profile.json`, `field_inventory.csv`, `parse_error_ledger.json`). |
| **T4** | Verify independent event-level GT | **STOP** | Phát hiện vấn đề về nguồn gốc nhãn độc lập (chi tiết bên dưới). |
| **T6–T11** | Downstream tasks | **NOT_RUN** | Đã dừng lại và đánh dấu `NOT_RUN` theo đúng quy định phân tầng gating. |

---

## 2. Nguyên nhân kích hoạt Cổng Chặn Task 4

Theo yêu cầu phương pháp luận đóng băng tại §R6 của kế hoạch:
> *"Mỗi eligible event phải có: authoritative target, independent linkage, sufficient behavioral evidence, và không còn unresolved competing target."*  
> *"Không coi rule mapping, scenario-wide list, successful operation hoặc temporal proximity đơn thuần là event-level GT."*  
> *"Không thúc đẩy detector/rule mappings thành independent ground truth."*  
> *"Dừng khi: Thiếu independent lineage, cần reannotation hoặc đổi evaluation unit."*

Qua rà soát và kiểm chứng toàn diện 102,011 bản ghi telemetry:
1. **Toàn bộ 63,619 nhãn sự kiện đều sinh ra từ Wazuh detection rules (`_source.rule.mitre.id`)**:
   - Nhãn trong bộ dữ liệu Windows-APT 2025 v3 được gán tự động khi Wazuh SIEM kích hoạt các rule giám sát (ví dụ: Rule 92039 kích hoạt nhãn `T1087`).
   - Bài báo gốc khẳng định: *"By employing specific Wazuh rules, the system is configured to detect tactics and techniques defined in the MITRE ATT&CK framework"*.
2. **Không có nhật ký thực thi độc lập từ Caldera (Independent Execution Log)**:
   - Bản phân phối Mendeley v3 chỉ cung cấp `scenario_manifest.csv` (danh sách kỹ thuật mô phỏng ở cấp độ kịch bản) và `validation_summary.csv` (tỷ lệ thành công trung bình qua 10 lần chạy).
   - Không có tệp log ghi nhận thời gian thực thi chính xác (timestamp) của từng Caldera Ability để join độc lập với từng sự kiện Sysmon.
3. **Nguy cơ phụ thuộc vòng tròn (Circular Corroboration)**:
   - Nếu dùng nhãn của detector rule để đánh giá mô hình LLM gán nhãn telemetry, mô hình thực chất chỉ đang học lại bộ luật của Wazuh detector chứ không phải ground truth thực thi độc lập.

---

## 3. Quyết định cần Người dùng Phê duyệt (Decision A)

Hệ thống đã dừng đúng tại ranh giới của Task 4 và không tự ý đưa ra giả định hay thay đổi phương pháp luận. Bạn cần đưa ra quyết định:

### Lựa chọn cho Quyết định A (Decision A):

- **Phương án A.1 (Chấp nhận Ground Truth vận hành từ Wazuh Detector)**:
  - Chấp nhận Windows-APT 2025 v3 và công nhận 63,619 nhãn được sinh từ Wazuh detection rules làm *operational benchmark ground truth*.
  - **Bắt buộc thi hành kiểm soát rò rỉ nghiêm ngặt tại Task 6**: Cách ly và loại bỏ hoàn toàn các trường `_source.rule.*`, `rule.mitre.*`, `description`, v.v. để LLM chỉ nhìn thấy telemetry hành vi thô (CommandLine, Image, ParentCommandLine, EventID).
  - Tiếp tục mở khóa cho Task 6, Task 7 (nhóm và khử trùng lặp), Task 8 (chọn lớp và cố định quota) để trình duyệt tiếp Quyết định B.

- **Phương án A.2 (Dừng dự án và yêu cầu bổ sung Caldera Execution Logs bên ngoài)**:
  - Từ chối coi Wazuh rule mappings là ground truth hợp lệ.
  - Tạm dừng pipeline cho đến khi có bộ log thực thi độc lập từ Caldera framework (với timestamp chi tiết) để map trực tiếp vào Sysmon telemetry.
