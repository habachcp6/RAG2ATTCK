# BÁO CÁO DÒNG DÕI VÀ CHỨNG TỰ CANONICAL METRIC BUNDLE V2

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-03T03:04:00+07:00  
**Tác giả:** Native Bundle Worker (Track B)  
**Mã Băm Bundle v2:** `e96a3b73662071cccec089dbb8fa06b1d7ccba163d057922f749e10174ae5434`  
**Vị trí Tệp:** `artifacts/results/canonical_metric_bundle_v2.json`  

---

## 1. TỔNG QUAN VÀ MỤC TIÊU BẢO MẬT

Tệp `canonical_metric_bundle_v2.json` đóng vai trò là adapter dữ liệu cấu trúc chuẩn mực duy nhất (Single Source of Truth) kết nối kết quả đánh giá khoa học và sổ cái tài chính từ chiến dịch chạy thực nghiệm 6.400 requests tới các bên tiêu thụ báo cáo (Publication Figures, Tables, Markdown Reports, Slides).

Bundle v2 tuân thủ các nguyên tắc bất biến:
1. **Zero Provider API Calls:** Hoàn toàn ngoại tuyến, không gửi bất kỳ request mạng nào.
2. **Fail-Closed Verification:** Tự động đối chiếu và xác thực toàn bộ mã băm SHA-256 của các tệp đầu vào đối với `canonical_bundle_manifest.json` và `canonical_run_seal_v1.json`.
3. **Phân định Hai Mẫu Số Độc Lập:** Phân biệt rạch ròi mẫu số đánh giá gán nhãn khoa học ($N=718$ mapped views) và mẫu số đo lường hệ thống/tài nguyên ($N=1.280$ queries/điều kiện, $6.400$ toàn chiến dịch).
4. **Bảo Toàn Tiền Tệ Tuyệt Đối:** Xác thực bằng số học `Decimal` bảo toàn tiền tệ: Settled \$6.57575890 + Pilot Hold \$0.05264010 = Accounted \$6.62839900; Available \$13.36160100 trong ngân sách trần \$19.99000000.
5. **Chính Sách Ẩn p95 Latency:** Khai báo rõ `"NOT REPORTED — approval evidence not established"`; trường giá trị số được đặt là `null` để ngăn tiêu thụ trái phép khi chưa có chứng cứ phê duyệt.

---

## 2. BẢNG DÒNG DÕI NGUỒN GỐC VÀ MÃ BĂM (PROVENANCE & LINEAGE)

| Thành Phần | Giá Trị / Đường Dẫn | SHA-256 / Commit | Ghi Chú |
| :--- | :--- | :--- | :--- |
| **Execution Git Commit** | `HEAD` tại lúc chạy thực nghiệm | `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315` | Frozen Core Git Commit |
| **Evaluation Git Commit** | `HEAD` tại lúc chạy evaluator | `208ac00a9fe86813d4e4ec4fa72b2a943a2e4fdb` | Evaluator Commit |
| **Candidate Git Commit** | Repo C `finalization_repo_20261003` | `4fafdb290dac59070a43de33f7e299bbb25782e3` | Base của Track B, chứa Track A acceptance `b69a690` |
| **Core Code Manifest** | `config/canonical_experiment_lock_v1.json` | `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` | Khóa bất biến 15 tệp cốt lõi |
| **Protocol Canonical** | `config/experiment_protocol_v1.json` | `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` | Giao thức thực nghiệm v1.1 |
| **Pricing Contract** | `config/pricing_v1.json` | `4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565` | Hợp đồng biểu giá |
| **Public Manifest** | `canonical_bundle_manifest.json` | `32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c` | Manifest của gói công khai v3 |
| **Canonical Run Seal** | `reports/evidence/canonical_run_seal_v1.json` | `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` | Chứng thư niêm phong vận hành |
| **Terminal Proof** | `artifacts/orchestration/...proof.json` | `cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e` | Bằng chứng tiến trình hoàn tất 6.400 records |
| **Analysis Source Code**| `scripts/analysis/evaluate_rqs.py` | `f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351` | Mã phân tích S2_RQ_V2 chính thức |
| **Authorizing Packet** | `provenance/s2_evaluation_execute_public.md` | `d515f70426435e9edb79cdc415e91c23b16e189fd171d4db4b04074c9b580aa1` | Tệp chỉ đạo phân tích được duyệt |
| **Historical S2 Packet**| Gói S2 thử nghiệm ban đầu | `c48eeb276166e511c7ff19904944d18ec0a187d903f0b2f56708ddaf4f9dff55` | Đã được thay thế bởi gói `f85...` / `d51...` |

---

## 3. THU NHẬP VÀ ĐỐI CHIẾU DỮ LIỆU TOKEN CACHE (RECEIPT JOIN)

Từ việc quét toàn bộ `inputs/request_journal.jsonl`:
- **Tổng số attempt receipts:** Đúng 6.401 receipts.
- **Quan sát thành công:** 6.400 quan sát.
- **Quan sát lỗi mạng:** 1 quan sát (`ordinal: 5387`, `view_d870d574`, điều kiện `rag_k1`, lỗi `InternalServerError`, `cached_tokens: null`).
- **Quan sát retry thành công:** 1 quan sát (`ordinal: 5388`, `view_d870d574`, điều kiện `rag_k1`, `cached_tokens: 1540`, `input_tokens: 1543`, `output_tokens: 452`).
- **Tổng token cache toàn bộ chiến dịch:** **1.540 tokens** (toàn bộ nằm ở điều kiện `rag_k1`).
- **Trung bình token cache:**
  - Điều kiện `rag_k1`: $1.540 / 1.280 = 1,203125$ tokens/query.
  - Các điều kiện khác (`no_rag`, `rag_k3`, `rag_k5`, `rag_k10`): $0,0$ tokens/query.
- **Quy tắc tính tổng token:**
  $$\text{Total Tokens} = \text{Prompt Tokens} + \text{Completion Tokens}$$
  Token cache là tập con của Prompt Tokens và **tuyệt đối không được cộng dồn hai lần** vào tổng token.

---

## 4. TỔNG HỢP CÁC KẾT QUẢ SỐ HỌC ĐÃ KIỂM CHỨNG

### RQ1: Đánh Giá Phân Loại Kỹ Thuật (Attribution Accuracy & Macro-F1)
- **Mẫu số đánh giá:** $N = 718$ mapped views (Single-GT: 678, Multi-GT: 40).
- **Macro-F1 Universe:** 474 kỹ thuật đông kết (8 supported, 466 unsupported).

| Điều Kiện | Đúng / Tổng | Độ Chính Xác (%) | 95% Bootstrap CI (%) | Macro-F1 | Delta vs No-RAG (pp) | 95% CI Delta (pp) | McNemar Exact $p$ | Ý Nghĩa Thống Kê ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG** | 560 / 718 | 77.99% | [74.51%, 81.34%] | 0.0126 | Baseline | Baseline | — | — |
| **RAG k=1** | 553 / 718 | 77.02% | [73.54%, 80.36%] | 0.0127 | -0.975 pp | [-4.735, +2.925] pp | 0.638 | Không |
| **RAG k=3** | 564 / 718 | 78.55% | [75.07%, 81.89%] | 0.0136 | +0.557 pp | [-3.064, +4.039] pp | 0.803 | Không |
| **RAG k=5** | 566 / 718 | 78.83% | [75.35%, 82.03%] | 0.0139 | +0.836 pp | [-2.646, +4.457] pp | 0.690 | Không |
| **RAG k=10** | 571 / 718 | 79.53% | [75.81%, 82.85%] | 0.0140 | +1.532 pp | [-2.355, +5.300] pp | 0.422 | Không |

*Bảng chéo McNemar k=10 vs No-RAG:* $a=488, b=83, c=72, d=75, \text{discordant}=155, \chi^2=0.645161, p_{\text{exact}}=0.421938833, p_{\text{asymptotic}}=0.421847975$.

### RQ2: Tách Rời Lỗi Truy Xuất & Sinh Văn Bản (k=10)
- **Truy xuất:** Hit = 321 / 718 (44.71%), Miss = 397 / 718 (55.29%), Macro Recall = 0.4280.
- **Độ chính xác có điều kiện:**
  - $P(\text{Đúng} \mid \text{Truy xuất thành công}) = 293 / 321 = 91.28\%$
  - $P(\text{Đúng} \mid \text{Truy xuất thất bại}) = 278 / 397 = 70.03\%$
- **Trục lỗi độc lập (Decision D2i):**
  - Lỗi phân loại sai: 147 mẫu.
  - Giao thoa Miss $\cap$ Phân loại sai: 119 mẫu ($119 / 147 = 80.95\%$).
  - Truy xuất No-RAG: Khai báo `null` với `applicable: false` (giữ vết 0 trong `raw_evaluator_trace`).

### RQ3: Tài Nguyên, Độ Trễ & Chi Phí (Mẫu số $N=1.280$ queries/điều kiện)

| Điều Kiện | Mean Latency (ms) | Median Latency (ms) | p95 Latency | Prompt Tokens | Completion Tokens | Total Tokens | Cached Tokens | Chi Phí Settled Ledger |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG** | 2.904,45 | 2.302,82 | *NOT REPORTED* | 863.139 | 209.466 | 1.072.605 | 0 | \$0.46714395 |
| **RAG k=1** | 3.514,27 | 2.617,14 | *NOT REPORTED* | 1.595.554 | 299.128 | 1.894.682 | 1.540 | \$1.29723350 |
| **RAG k=3** | 4.215,88 | 2.743,17 | *NOT REPORTED* | 2.780.640 | 403.100 | 3.183.740 | 0 | \$1.17888000 |
| **RAG k=5** | 4.327,26 | 2.873,74 | *NOT REPORTED* | 3.917.047 | 419.880 | 4.336.927 | 0 | \$1.48311775 |
| **RAG k=10** | 4.370,71 | 2.667,00 | *NOT REPORTED* | 6.546.274 | 427.346 | 6.973.620 | 0 | \$2.14938370 |
| **Tổng Toàn Bộ**| — | — | — | **15.702.654** | **1.758.920** | **17.461.574** | **1.540** | **\$6.57575890** |

*Ghi chú tài chính `rag_k1`:* Chi phí ước tính từ token là \$0.75784210; phụ phí phạt missing usage do lỗi mạng ở lần thử 0 là \$0.53974560, dẫn tới tổng settled ledger là \$1.29723350.

---

## 5. KẾT QUẢ KIỂM THỬ TỰ ĐỘNG (OFFLINE GUARD)

Toàn bộ 12 ca kiểm thử chuyên biệt tại `tests/test_canonical_metric_bundle.py` đã vượt qua 100% dưới `scripts/run_offline_tests.py`:
- 7 ca kiểm thử khẳng định (Positive Controls): cấu trúc, cohort, RQ1, RQ2, RQ3 cache, p95 suppression, bảo toàn tiền tệ.
- 5 ca kiểm thử phủ định chặt chẽ (Negative Controls): từ chối manifest bị sửa, từ chối run seal giả mạo, từ chối fixture seal, từ chối vi phạm bảo toàn tiền tệ, từ chối mã nguồn phân tích không khớp hash.
- **Egress Audit:** `installed=True, attempted_egress=0`.
- **Tổng kiểm thử hợp nhất cùng terminal audit:** 68 passed trong 6.28s, 0 lỗi.
