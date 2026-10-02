# BÁO CÁO DÒNG DÕI VÀ CHỨNG TỰ CANONICAL METRIC BUNDLE V2

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-02T21:26:00+00:00  
**Tác giả:** Native Bundle Worker (Track B)  
**Vị trí Tệp:** `artifacts/results/canonical_metric_bundle_v2.json`  

---

## 1. TỔNG QUAN VÀ MỤC TIÊU BẢO MẬT

Tệp `canonical_metric_bundle_v2.json` đóng vai trò là adapter dữ liệu cấu trúc chuẩn mực duy nhất (Single Source of Truth) kết nối kết quả đánh giá khoa học và sổ cái tài chính từ chiến dịch chạy thực nghiệm 6.400 requests tới các bên tiêu thụ báo cáo (Publication Figures, Tables, Markdown Reports, Slides).

Bundle v2 tuân thủ các nguyên tắc bất biến:
1. **Zero Provider API Calls:** Hoàn toàn ngoại tuyến, không gửi bất kỳ request mạng nào.
2. **Fail-Closed Verification:** Tự động đối chiếu và xác thực toàn bộ mã băm SHA-256 của các tệp đầu vào đối với `canonical_bundle_manifest.json` và `canonical_run_seal_v1.json`.
3. **Phân định Hai Mẫu Số Độc Lập:** Phân biệt rạch ròi mẫu số đánh giá gán nhãn khoa học ($N=718$ mapped views) và mẫu số đo lường hệ thống/tài nguyên ($N=1.280$ queries/điều kiện, $6.400$ toàn chiến dịch).
4. **Bảo Toàn Tiền Tệ Tuyệt Đối:** Xác thực bằng số học `Decimal` bảo toàn tiền tệ: Settled $6.57575890 + Pilot Hold $0.05264010 = Accounted $6.62839900; Available $13.36160100 trong ngân sách trần $19.99000000.
5. **Chính Sách Ẩn p95 Latency:** Khai báo rõ `"NOT REPORTED — approval evidence not established"`; trường giá trị số được đặt là `null` để ngăn tiêu thụ trái phép khi chưa có chứng cứ phê duyệt.

---

## 2. BẢNG DÒNG DÕI NGUỒN GỐC VÀ MÃ BĂM (PROVENANCE & LINEAGE)

| Thành Phần | Giá Trị / Đường Dẫn | SHA-256 / Commit | Ghi Chú |
| :--- | :--- | :--- | :--- |
| **Execution Git Commit** | `HEAD` tại lúc chạy thực nghiệm | `80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315` | Frozen Core Git Commit |
| **Native Evaluation Commit** | `HEAD` tại lúc chạy native evaluator | `208ac00a9fe86813d4e4ec4fa72b2a943a2e4fdb` | Chứa analysis source `c48eeb27b19626344e5f10b2cac674437b4053bb01f014060905702c52235f95` |
| **RQv2 Integrated Commit** | `HEAD` tích hợp phân tích RQv2 | `264ed31472c4f0f74e519938b65876915f9c15a7` | Chứa analysis source `f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351` |
| **Candidate Base Commit** | `HEAD` nghiệm thu Track A | `b69a6909acda4c7588744acc7e1d6c20bfce2612` | Base cho các nhánh finalization |
| **Core Code Manifest** | `config/canonical_experiment_lock_v1.json` | `8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4` | Khóa bất biến 53 tệp cốt lõi |
| **Protocol Canonical** | `config/experiment_protocol_v1.json` | `d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c` | Giao thức thực nghiệm v1.1 |
| **Pricing Contract** | `config/pricing_v1.json` | `4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565` | Hợp đồng biểu giá |
| **Public Manifest** | `canonical_bundle_manifest.json` | `32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c` | Manifest của gói công khai v3 |
| **Canonical Run Seal** | `reports/evidence/canonical_run_seal_v1.json` | `ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701` | Chứng thư niêm phong vận hành |
| **Terminal Proof** | `artifacts/orchestration/...proof.json` | `cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e` | Bằng chứng tiến trình hoàn tất 6.400 records |
| **Analysis Source Code**| `scripts/analysis/evaluate_rqs.py` | `f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351` | Mã phân tích S2_RQ_V2 chính thức |
| **Superseding Authorizing Packet** | `s2_rq_v2_execute_exact_20261002.md` | `c34b1350881d61f153a50fd5fa2b79a9438ece09c2a2b09d022e74e863313570` | Chỉ đạo phân tích S2_RQ_V2 được duyệt |
| **Source Audit Evidence** | `root_integrated_264ed31_source_audit.json` | `b164b13d76a76ed7893ebf6b7e87ff5a28898a15f3425a6764e0f4efa84db608` | Bằng chứng kiểm toán nguồn tích hợp 264ed31 |
| **Private Replay Acceptance** | `root_private_replay_acceptance_20261002.json` | `cdc875da1647552a3596100e2d168f7cb79878e64e50c0f1f59e6a0c4bceed05` | Bằng chứng nghiệm thu replay riêng tư 17.894 trường |
| **Historical Public Packet**| `provenance/s2_evaluation_execute_public.md` | `d515f70426435e9edb79cdc415e91c23b16e189fd171d4db4b04074c9b580aa1` | Gói chỉ đạo ban đầu (gắn với commit 208) |

---

## 3. THU NHẬP VÀ ĐỐI CHIẾU DỮ LIỆU TOKEN CACHE (RECEIPT JOIN)

Từ việc quét toàn bộ `inputs/request_journal.jsonl` và join với predictions:
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

## 4. TỔNG HỢP CÁC KẾT QUẢ SỐ HỌC ĐÃ KIỂM CHỨNG (MACHINE GENERATED)

### RQ1: Đánh Giá Phân Loại Kỹ Thuật (Attribution Accuracy & Macro-F1)
- **Mẫu số đánh giá:** $N = 718$ mapped views (Single-GT: 678, Multi-GT: 40).
- **Macro-F1 Universe:** 474 kỹ thuật đông kết (8 supported, 466 unsupported).

| Điều Kiện | Đúng / Tổng | Độ Chính Xác (%) | 95% Bootstrap CI (%) | Macro-F1 | Delta vs No-RAG (pp) | 95% CI Delta (pp) | McNemar Exact $p$ | Ý Nghĩa Thống Kê ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **No-RAG** | 560 / 718 | 77.99% | [74.64%, 80.88%] | 0.0126 | Baseline | Baseline | — | — |
| **RAG k=1** | 553 / 718 | 77.02% | [73.50%, 80.17%] | 0.0127 | -0.975 pp | [-3.186, +1.124] pp | 0.435 | Không |
| **RAG k=3** | 564 / 718 | 78.55% | [75.00%, 81.74%] | 0.0136 | +0.557 pp | [-2.786, +3.934] pp | 0.777 | Không |
| **RAG k=5** | 566 / 718 | 78.83% | [75.07%, 82.35%] | 0.0139 | +0.836 pp | [-2.934, +4.603] pp | 0.677 | Không |
| **RAG k=10** | 571 / 718 | 79.53% | [75.81%, 82.85%] | 0.0140 | +1.532 pp | [-2.355, +5.300] pp | 0.422 | Không |

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
| **No-RAG** | 2,904.45 | 2,302.82 | *NOT REPORTED* | 863,139 | 209,466 | 1,072,605 | 0 | $0.46714395 |
| **RAG k=1** | 3,514.27 | 2,617.14 | *NOT REPORTED* | 1,595,554 | 299,128 | 1,894,682 | 1,540 | $1.2972335 |
| **RAG k=3** | 4,215.88 | 2,743.17 | *NOT REPORTED* | 2,780,640 | 403,100 | 3,183,740 | 0 | $1.17888 |
| **RAG k=5** | 4,327.26 | 2,873.74 | *NOT REPORTED* | 3,917,047 | 419,880 | 4,336,927 | 0 | $1.48311775 |
| **RAG k=10** | 4,370.71 | 2,667.00 | *NOT REPORTED* | 6,546,274 | 427,346 | 6,973,620 | 0 | $2.1493837 |
| **Tổng Toàn Bộ**| — | — | — | **15,702,654** | **1,758,920** | **17,461,574** | **1.540** | **$6.57575890** |

*Công thức đối soát tài chính `rag_k1`:*  
Token usage estimate $0.75784210 - Observed cache credit $0.00035420 + Missing-usage retained charge $0.53974560 = Settled ledger $1.29723350.  
(Trong đó chi phí bảo lưu missing usage là số tiền giữ lại thận trọng theo quy tắc bảo vệ ngân sách API khi thiếu thông tin sử dụng ở lần thử 0, không phải là hóa đơn thương mại hay phạt hợp đồng).

---

## 5. BẢO ĐẢM TÍNH TOÀN VẸN VÀ KHÔNG GÂY THOÁT RA NGOÀI (OFFLINE GUARD)

Toàn bộ quá trình tạo và xác thực Canonical Metric Bundle v2 được thực thi hoàn toàn trong môi trường tự cách ly:
- Không tạo kết nối HTTP/HTTPS ra ngoài (`attempted_egress = 0`).
- Ghi tệp nhị phân bảo đảm dòng kết thúc LF đồng nhất cross-platform.
- Tự động đối chiếu mã băm thực tế trên đĩa với tệp sidecar `.sha256`.
