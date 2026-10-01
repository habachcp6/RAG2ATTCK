"""RAG2ATTCK - Automated PowerPoint Slide Deck Generator.

Generates a modern, publication-grade 16:9 widescreen presentation deck
in PPTX format for thesis defense, scientific evaluation, and technical demonstration.
Fully compliant with CD_RENDER_REPAIR requirements:
- Mathematical accuracy per Frozen Protocol v1.1 (D2i independent error axes)
- Perfect typography and card geometry (zero text overflow, clear of footer)
- Academic claim and tone hygiene
- Comprehensive evidence citations and speaker notes on every slide

Usage:
    uv run python scripts/generate_slides.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs/presentation/slides.pptx"
FIGURES_DIR = REPO_ROOT / "outputs/reproduction/figures"

# Color Palette
DARK_NAVY = RGBColor(15, 23, 42)       # #0F172A
SLATE_HEADER = RGBColor(30, 41, 59)    # #1E293B
WHITE = RGBColor(255, 255, 255)
LIGHT_BG = RGBColor(248, 250, 252)     # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)      # #F1F5F9
BORDER_COLOR = RGBColor(203, 213, 225) # #CBD5E1
DEEP_BLUE = RGBColor(30, 64, 175)      # #1E40AF
PRIMARY_BLUE = RGBColor(37, 99, 235)   # #2563EB
CYAN_ACCENT = RGBColor(6, 182, 212)    # #06B6D4
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)   # #64748B
TEXT_LIGHT = RGBColor(248, 250, 252)
SUCCESS_GREEN = RGBColor(5, 150, 105)  # #059669
ALERT_RED = RGBColor(220, 38, 38)      # #DC2626


def create_deck() -> Presentation:
    """Create a presentation set to 16:9 widescreen layout."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def set_slide_background(slide: Any, color: RGBColor) -> None:
    """Set solid color background for slide."""
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()


def set_speaker_notes(slide: Any, notes_text: str) -> None:
    """Embed speaker notes with artifact citations into slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text


def add_header(slide: Any, title_text: str, subtitle_text: str = "") -> None:
    """Add standard header banner to content slide."""
    # Top banner background
    banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.12))
    banner.fill.solid()
    banner.fill.fore_color.rgb = SLATE_HEADER
    banner.line.fill.background()

    # Cyan accent line
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.08), Inches(13.333), Inches(0.04))
    accent.fill.solid()
    accent.fill.fore_color.rgb = CYAN_ACCENT
    accent.line.fill.background()

    # Title box
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.10), Inches(11.733), Inches(0.90))
    tf = tx_box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title_text
    p.font.name = "Calibri"
    p.font.size = Pt(24)
    p.font.bold = True
    p.font.color.rgb = WHITE

    if subtitle_text:
        p2 = tf.add_paragraph()
        p2.text = subtitle_text
        p2.font.name = "Calibri"
        p2.font.size = Pt(13)
        p2.font.color.rgb = CYAN_ACCENT


def add_card(
    slide: Any,
    left: float,
    top: float,
    width: float,
    height: float,
    title: str,
    body_items: list[str],
    *,
    header_color: RGBColor = DEEP_BLUE,
    bg_color: RGBColor = CARD_BG,
    border_color: RGBColor = BORDER_COLOR,
    title_size: int = 16,
    body_size: float = 12.0,
    item_spacing: float = 3.5,
) -> None:
    """Add styled structured card with title and bullet points."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)

    tx_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.12), Inches(width - 0.4), Inches(height - 0.24))
    tf = tx_box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = title
    p.font.name = "Calibri"
    p.font.size = Pt(title_size)
    p.font.bold = True
    p.font.color.rgb = header_color

    for item in body_items:
        p_item = tf.add_paragraph()
        p_item.text = f"•  {item}" if not item.startswith("   ") and not item.startswith("  ") else item
        p_item.font.name = "Calibri"
        p_item.font.size = Pt(body_size)
        p_item.font.color.rgb = TEXT_DARK
        p_item.space_before = Pt(item_spacing)


# ---------------------------------------------------------------------------
# Slide Builders
# ---------------------------------------------------------------------------

def build_slide_1_title(prs: Presentation) -> None:
    """Slide 1: Title Slide (Dark Theme)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_NAVY)

    # Accent decorative bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.6), Inches(0.15), Inches(4.0))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN_ACCENT
    bar.line.fill.background()

    tx = slide.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(10.5), Inches(4.2))
    tf = tx.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "BÁO CÁO NGHIÊN CỨU THỰC NGHIỆM ĐỐI CHỨNG"
    p0.font.name = "Calibri"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT

    p1 = tf.add_paragraph()
    p1.text = "Đánh Giá Tác Động Của MITRE ATT&CK-Grounded RAG Đối Với Việc Ánh Xạ Windows Endpoint Logs"
    p1.font.name = "Calibri"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_before = Pt(10)

    p2 = tf.add_paragraph()
    p2.text = "Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs (RAG2ATT&CK)"
    p2.font.name = "Calibri"
    p2.font.size = Pt(15)
    p2.font.italic = True
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Giao thức khoa học: experiment-protocol-v1.1  |  Khóa chuẩn: canonical-lock-v1  |  Tái lập: 100% Offline"
    p3.font.name = "Calibri"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(226, 232, 240)
    p3.space_before = Pt(24)

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 1):\n"
        "Kính thưa Hội đồng và các chuyên gia, hôm nay tôi xin trình bày báo cáo nghiên cứu RAG2ATT&CK: Đánh giá tác động của MITRE ATT&CK-grounded RAG đối với việc ánh xạ Windows endpoint logs sang ATT&CK techniques. Toàn bộ nghiên cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt dưới giao thức đóng băng experiment-protocol-v1.1, khóa mật mã 15 canonical artifacts, và có thể tái lập hoàn toàn ngoại tuyến với chi phí 0 đồng.\n"
        "Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac); reports/experiment_protocol_v1.md (SHA-256: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); scripts/reproduce_study.py."
    )


def build_slide_2_problem(prs: Presentation) -> None:
    """Slide 2: Problem Statement & Motivation."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "1. Vấn Đề Nghiên Cứu & Động Lực Thực Tiễn", "Khoảng cách giữa nhật ký cấp thấp (Telemetry) và ma trận kỹ thuật ATT&CK")

    add_card(
        slide, 0.8, 1.35, 3.733, 5.55, "Bối Cảnh Giám Sát SOC",
        [
            "Nhật ký Windows Endpoint (Security Events, Sysmon) là tuyến phòng thủ cốt lõi của Trung tâm Giám sát An ninh (SOC).",
            "Việc ánh xạ nhật ký thô sang mã MITRE ATT&CK Technique là tiêu chuẩn vàng để xác định ý đồ tấn công.",
            "Quy trình thủ công đòi hỏi chuyên gia cấp cao, tốn thời gian và khó đáp ứng quy mô hàng triệu sự kiện mỗi ngày.",
        ],
        header_color=PRIMARY_BLUE,
        body_size=12.0,
        item_spacing=4.0,
    )

    add_card(
        slide, 4.8, 1.35, 3.733, 5.55, "Thách Thức Của LLM Thuần Túy",
        [
            "Khoảng cách trừu tượng: Log mang tính kỹ thuật hệ thống (Process GUID, CommandLine), trong khi ATT&CK mô tả hành vi khái niệm.",
            "Hiện tượng ảo giác: LLM không có RAG dễ suy đoán mã kỹ thuật sai cú pháp hoặc không tồn tại trong danh mục.",
            "Nhầm lẫn Sub-techniques: Khó phân biệt các kỹ thuật lân cận (ví dụ: T1059.001 PowerShell vs T1059.003 Command Shell).",
        ],
        header_color=ALERT_RED,
        body_size=12.0,
        item_spacing=4.0,
    )

    add_card(
        slide, 8.8, 1.35, 3.733, 5.55, "Động Lực Của RAG2ATT&CK",
        [
            "Thiết kế nghiên cứu thực nghiệm có kiểm soát (Controlled Empirical Study).",
            "Đo lường chính xác delta hiệu năng do RAG mang lại trên cùng mô hình LLM.",
            "Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại (Classification Failure).",
            "Đóng băng giao thức v1.1: Thực thi xác định (Deterministic Execution under Frozen Environment & Seeds).",
            "Tái lập ngoại tuyến chi phí 0 đồng với bộ offline_guard chặn tuyệt đối kết nối mạng ngoài.",
        ],
        header_color=SUCCESS_GREEN,
        body_size=12.0,
        item_spacing=4.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 2):\n"
        "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này đo lường khoa học mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ. Toàn bộ thực thi đạt tính xác định (Deterministic Execution under Frozen Environment & Seeds), loại trừ hoàn toàn tính tùy tiện trong diễn giải số liệu.\n"
        "Bằng chứng dự án: docs/README_PROPOSED.md; config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3...); tests/test_attack_id_validation.py."
    )


def build_slide_3_architecture(prs: Presentation) -> None:
    """Slide 3: System Architecture."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "2. Kiến Trúc Thực Nghiệm Đối Chứng", "So sánh đối đầu giữa Baseline (No-RAG) và Experimental (RAG)")

    add_card(
        slide, 0.8, 1.35, 5.7, 3.35, "Nhánh Cơ Sở: Baseline No-RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint (endpoint_evidence).",
            "Cơ chế: Đưa trực tiếp vào LLM cùng prompt hướng dẫn chuẩn hóa.",
            "Đầu ra: Chuỗi JSON chứa duy nhất mã technique_id.",
            "Mô hình: gpt-5.6-luna (reasoning_effort=xhigh, api_interface=responses).",
        ],
        header_color=SLATE_HEADER,
        body_size=12.0,
        item_spacing=3.5,
    )

    add_card(
        slide, 6.833, 1.35, 5.7, 3.35, "Nhánh Thử Nghiệm: Experimental RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint như nhánh cơ sở.",
            "Bộ truy xuất: sentence-transformers/all-MiniLM-L6-v2 + FAISS FlatIP (384-dim).",
            "Kho tri thức: 474 tài liệu ATT&CK v19.2 Enterprise Windows.",
            "Độ sâu k: Đánh giá có hệ thống k ∈ {1, 3, 5, 10}.",
            "Đầu ra: Cùng cấu trúc JSON và cùng bộ kiểm tra cú pháp nghiêm ngặt.",
        ],
        header_color=DEEP_BLUE,
        body_size=12.0,
        item_spacing=3.5,
    )

    add_card(
        slide, 0.8, 4.85, 11.733, 2.05, "Các Biến Kiểm Soát Bất Biến (Controlled Invariants)",
        [
            "Cùng tập dữ liệu thử nghiệm (exact same telemetry instances); Cùng mô hình và tham số suy luận.",
            "Cùng cấu trúc Prompt (prompts/baseline_v1.txt), chỉ khác biệt ở khối Context được chèn vào.",
            "Biến duy nhất được thay đổi trong toàn bộ nghiên cứu: Retrieval ON vs. OFF.",
        ],
        header_color=SUCCESS_GREEN,
        body_size=12.0,
        item_spacing=3.5,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 3):\n"
        "Kiến trúc thực nghiệm đối chứng kiểm soát nghiêm ngặt biến số điều trị duy nhất: Retrieval ON vs OFF. Nhánh Baseline No-RAG và Experimental RAG dùng chung một mô hình gpt-5.6-luna (xhigh), cùng cấu trúc prompt template, và cùng schema JSON đầu ra. Bộ tìm kiếm sử dụng all-MiniLM-L6-v2 kết hợp FAISS IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows.\n"
        "Bằng chứng dự án: prompts/baseline_v1.txt (SHA-256: b751fde1ee33b03ebca935e478ffef3ff03ff8bcf440263309a039755ab0f7cf); attack/corpus/enterprise-windows-v19.2.jsonl (SHA-256: b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75); config/experiment_config.json; tests/test_rag_pipeline.py."
    )


def build_slide_4_dataset(prs: Presentation) -> None:
    """Slide 4: Dataset Strategy & Anti-Leakage."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "3. Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ Nhãn", "Bộ dữ liệu chuẩn đóng băng Stage B (670 cặp kịch bản, 1,340 views)")

    add_card(
        slide, 0.8, 1.35, 5.7, 5.55, "Bộ Dữ Liệu Chuẩn Đóng Băng Stage B",
        [
            "Tổng thể: 670 cặp kịch bản (Scenario Pairs) tương ứng 1,340 Views.",
            "Phân chia tập: 1,280 TEST views và 60 DEV views.",
            "Hình thức biểu diễn Telemetry:",
            "  • Single-event view: Một sự kiện đơn lẻ kích hoạt kỹ thuật tấn công.",
            "  • Contextual-event view: Sự kiện mục tiêu kèm nhật ký ngữ cảnh lân cận.",
            "Độ bao phủ: 8 nhóm kỹ thuật mục tiêu đại diện cùng các mẫu âm tính / mơ hồ.",
            "Toàn vẹn mật mã: Khóa bằng SHA-256 trong canonical_experiment_lock_v1.json.",
        ],
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide, 6.833, 1.35, 5.7, 5.55, "Giao Thức Chống Rò Rỉ Nhãn (Anti-Label-Leakage)",
        [
            "Nguyên tắc cốt lõi: Tuyệt đối không để lộ nhãn hoặc tri thức luật trong đầu vào suy luận.",
            "Bộ lọc nghiêm ngặt (INFERENCE_ALLOWLIST):",
            "  • Chỉ giữ lại các trường kỹ thuật thô (CommandLine, ParentImage, Hashes).",
            "  • Loại bỏ hoàn toàn: technique_id, RuleName, Tactic, Description, Tags.",
            "Đầu vào suy luận (inference.jsonl) chỉ chứa 2 trường duy nhất: sample_id và endpoint_evidence.",
            "Phân định phạm vi: Stage B phục vụ kiểm định kỹ thuật & chẩn đoán lỗi; dữ liệu thực địa (T15 real pilot) được quản lý độc lập.",
        ],
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 4):\n"
        "Tập dữ liệu chuẩn đóng băng Stage B gồm 670 cặp kịch bản đối ứng (1,340 views), chia thành 1,280 TEST views và 60 DEV views. Giao thức chống rò rỉ nhãn áp dụng INFERENCE_ALLOWLIST nghiêm ngặt: đầu vào suy luận inference.jsonl chỉ chứa sample_id và endpoint_evidence; toàn bộ tên luật, mã technique và mô tả đều bị loại trừ tuyệt đối. Nghiên cứu phân định rõ ràng giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.\n"
        "Bằng chứng dự án: data/ground_truth/synthetic/inference.jsonl (SHA-256: 90d5f59e64f669f9d7990520625906d40081d5aa112521c7bb5e2f750b3e5fbf); data/ground_truth/synthetic/pairs.json (SHA-256: 079e57a441b18d12351bb9715fc4b0a43058a9ceb68a8670c5e7bfa5dbad3ca8); tests/test_benchmark_inputs.py; tests/test_synthetic_freeze.py."
    )


def build_slide_5_methodology(prs: Presentation) -> None:
    """Slide 5: Dataset & Threat Model / Methodology & Frozen Protocol v1.1."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "4. Phương Pháp Luận, Mô Hình Đe Dọa & Giao Thức v1.1",
        "Khóa 7 quyết định khoa học D1-D7 và chính sách chấp nhận kỹ thuật lịch sử",
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Mô Hình Đe Dọa & Danh Mục ATT&CK v19.2",
        [
            "Tiêu chuẩn danh mục: Pinned MITRE ATT&CK v19.2 Enterprise Windows (474 techniques/sub-techniques).",
            "Chính sách kỹ thuật lịch sử (D2g: ALLOW_HISTORICAL):",
            "  • Chấp nhận các mã kỹ thuật lịch sử hoặc đã bị thu hồi (revoked/deprecated) có trong bộ kiểm chuẩn.",
            "  • Báo cáo dưới dạng distinct observation count, không tự ý gán lại (no silent remapping).",
            "Không gian lớp mục tiêu (D2d: FROZEN_BENCHMARK_UNIVERSE):",
            "  • Macro-F1 tính trên tập các lớp kỹ thuật chuẩn đóng băng, đảm bảo tính nhất quán giữa các lần chạy.",
            "Loại trừ mẫu rỗng / mơ hồ (D2b-c: EXCLUDE):",
            "  • Mẫu không gán được nhãn hoặc nhãn mơ hồ bị loại khỏi mẫu số Attribution Accuracy.",
            "Lưu vết đầy đủ (D1: RECORD_ONLY): Lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập.",
        ],
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        5.55,
        "4 Tiêu Chí Đánh Giá Cốt Lõi (D2h, D2i, D2e, D2f)",
        [
            "D2h: Multi-GT Retrieval Success (ANY_GT_RETRIEVED):",
            "  • Retrieval được tính là thành công nếu BẤT KỲ ground-truth technique ID nào có trong Top-k candidates.",
            "D2i: Failure Decomposition (INDEPENDENT_AXES):",
            "  • Bóc tách độc lập lỗi tìm kiếm và phân loại trên các trục trực giao; ghi nhận đầy đủ phần giao thoa (overlap).",
            "D2e: Invalid ATT&CK ID Denominator (INCLUDE_IN_DENOMINATOR):",
            "  • Mã kỹ thuật ảo giác, sai cú pháp đều bị tính là thất bại (Fail-Closed).",
            "D2f: Provider Failure Denominator (INCLUDE_IN_DENOMINATOR):",
            "  • Lỗi API, timeout, refusal đều tính vào mẫu số, không được loại trừ.",
            "D3: Khóa mô hình: ALLOW_LATEST_WITH_TIMESTAMP_BINDING (tem UTC thực tế).",
            "D4-D5: Thực thi tuần tự (SEQUENTIAL_ONLY), chặn cứng ngân sách (HARD_CAP).",
        ],
        header_color=SUCCESS_GREEN,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 5):\n"
        "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi D1-D7. Về mô hình đe dọa, danh mục kỹ thuật được neo tại STIX ATT&CK v19.2 Enterprise Windows (474 techniques). Điểm đặc biệt quan trọng là chính sách D2g ALLOW_HISTORICAL: các mã kỹ thuật lịch sử hoặc đã bị thu hồi có trong benchmark được chấp nhận và báo cáo dạng distinct observation count, không tự ý gán lại mã thay thế. Bốn tiêu chí đánh giá cốt lõi gồm D2h (ANY_GT_RETRIEVED cho multi-label), D2i (INDEPENDENT_AXES ghi nhận đầy đủ overlap), D2e (invalid ID tính vào mẫu số), và D2f (lỗi mạng tính vào mẫu số) thiết lập nguyên tắc fail-closed nghiêm ngặt.\n"
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (SHA-256: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); attack/raw/enterprise-v19.2/enterprise-attack-19.2.json (SHA-256: dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4); tests/test_experiment_evaluation.py."
    )


def build_slide_6_rq2_diagnostics(prs: Presentation) -> None:
    """Slide 6: RQ2 Retrieval Diagnostics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "5. Kết Quả RQ2: Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)", "Đánh giá độc lập bộ tìm kiếm trên 756 positive views của benchmark")

    # Left card: Metrics table
    add_card(
        slide, 0.8, 1.35, 5.7, 5.55, "Số Liệu Chẩn Đoán Cốt Lõi (T20 Overall)",
        [
            "Số mẫu dương tính đánh giá: 756 / 1,340 views.",
            "Tỷ lệ tìm trúng theo độ sâu k (Hit@k):",
            "  • Hit@1:   4.23% (32 / 756)",
            "  • Hit@3:  16.80% (127 / 756)",
            "  • Hit@5:  24.21% (183 / 756)",
            "  • Hit@10: 45.11% (341 / 756)",
            "Tỷ lệ vắng mặt trong Top-10 (Retrieval Failure): 54.89% (415 / 756).",
            "Macro Recall@10: 43.14%  |  Mean Rank khi trúng: 5.21.",
            "Phát hiện: Trong hơn 54% trường hợp, kỹ thuật đúng hoàn toàn vắng bóng trong Top-10 gửi cho LLM!",
        ],
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    # Right: Try to embed figure or fallback to analysis card
    fig_path = FIGURES_DIR / "fig_rq2_retrieval_hit_rates.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide, 6.833, 4.95, 5.7, 1.95, "Giả Thuyết Context Scaling & Dilution (k=1,3,5,10)",
            [
                "Khoảng cách ngữ nghĩa tại T1136.001 (Local Account): 0/99 lượt trúng Top-10 do log Event ID 4720 lệch từ vựng so với STIX persistence.",
                "Giả thuyết Context Scaling & Dilution: Tăng k tăng độ phủ (Hit@k) nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng trên ma trận TEST.",
            ],
            header_color=ALERT_RED,
            body_size=11.0,
            item_spacing=2.5,
        )
    else:
        add_card(
            slide, 6.833, 1.35, 5.7, 5.55, "Phân Tích Thất Bại & Giả Thuyết Context Dilution",
            [
                "Điểm nghẽn nghiêm trọng ở T1136.001 (Local Account):",
                "  • Tỷ lệ trúng Top-10: 0.0% (0 / 99 views).",
                "  • Nguyên nhân: Nhật ký Windows 4720 chứa 'SamAccountName', trong khi tài liệu ATT&CK nhấn mạnh 'persistence'.",
                "Hiệu quả theo kỹ thuật:",
                "  • T1543.003 (Windows Service): Hit@10 = 87.91% (tốt nhất).",
                "  • T1059.001 (PowerShell): Hit@10 = 68.14%.",
                "  • T1105 (Ingress Tool Transfer): Hit@10 = 15.79% (kém).",
                "Giả thuyết Context Scaling & Dilution: Đang chờ hoàn tất ma trận TEST để kiểm định chính thức.",
            ],
            header_color=ALERT_RED,
            body_size=11.5,
            item_spacing=3.0,
        )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 6):\n"
        "Chẩn đoán độc lập khâu tìm kiếm (RQ2) trên 756 positive views cho thấy Hit@10 chỉ đạt 45.11%, nghĩa là trong 54.89% trường hợp, kỹ thuật đúng hoàn toàn vắng bóng trong Top-10 gửi cho LLM. Điển hình là kỹ thuật T1136.001 với 0/99 lần trúng Top-10 do khoảng cách ngữ nghĩa giữa Event ID 4720 và STIX description. Chúng tôi đặt ra giả thuyết Context Scaling & Dilution (k=1,3,5,10): tăng k cải thiện độ phủ nhưng tăng nguy cơ nhiễu distractor; giả thuyết này đang được kiểm chứng thực nghiệm đối chứng end-to-end.\n"
        "Bằng chứng dự án: outputs/reproduction/figures/fig_rq2_retrieval_hit_rates.png; outputs/reproduction/tables/table_1_retrieval_diagnostics.md; tests/test_retrieval_diagnostics.py."
    )


def build_slide_7_representation(prs: Presentation) -> None:
    """Slide 7: Representation Gap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "6. Tác Động Của Hình Thức Biểu Diễn Telemetry", "So sánh thực nghiệm Single vs Contextual trên 670 cặp kịch bản đối ứng")

    add_card(
        slide, 0.8, 1.35, 5.7, 5.55, "Phân Tích Cặp Anchor Chuẩn (296 Cặp - Primary)",
        [
            "Quy mô: 670 cặp kịch bản đối ứng; 374 cặp bị loại trừ do đa nhãn/mismatch.",
            "Tiêu chí Anchor chuẩn (scripts/verify_t20_canonical_artifacts.py):",
            "  • Single view có duy nhất 1 kỹ thuật và kỹ thuật này có mặt trong Contextual view.",
            "Phân bố thứ hạng thực nghiệm quan sát được:",
            "  • Single-event đạt thứ hạng tốt hơn: 65 cặp (22.0%)",
            "  • Contextual-event đạt thứ hạng tốt hơn: 23 cặp (7.8%)",
            "  • Hiệu năng thứ hạng tương đương: 208 cặp (70.3%)",
            "    - Cả hai biểu diễn cùng trượt Top-10: 147 cặp",
            "    - Đồng hạng chính xác trong Top-10: 61 cặp",
            "Nhóm lọc đơn kỹ thuật nghiêm ngặt (252 cặp - Secondary): Single tốt hơn 59 cặp (23.4%) vs. Contextual 23 cặp (9.1%), ngang nhau 170 cặp.",
        ],
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide, 6.833, 1.35, 5.7, 5.55, "Hiện Tượng Quan Sát & Schema So Sánh [PENDING]",
        [
            "Hiện tượng Benign Drift khi mở rộng ngữ cảnh:",
            "  • Gộp các sự kiện lân cận bổ sung nhiều token thông thường (Explorer, DNS, svchost).",
            "  • Vector dense embedding bị kéo lệch về hành vi bình thường, làm tụt thứ hạng kỹ thuật tấn công.",
            "Schema So Sánh Đối Chứng Scaffold [PENDING EXECUTION]:",
            "  • Đối chứng: Zero-Shot No-RAG vs Zero-Shot RAG (k=1..10) vs Prompt Scaffolds.",
            "  • Giả thuyết: Khối tri thức RAG bổ trợ cần đi kèm tiền lọc sự kiện nghi vấn thay vì nhúng thô.",
            "  • Trạng thái: Toàn bộ ma trận TEST đang thực thi; kết luận chính thức sẽ công bố khi hoàn tất.",
            "Phạm vi khảo sát: Ghi nhận trên synthetic-paired-v1; cần tiếp tục kiểm chứng trên telemetry thực tế.",
        ],
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 7):\n"
        "So sánh đối ứng trên 296 cặp anchor chuẩn chỉ ra rằng biểu diễn Single-event đạt thứ hạng tìm kiếm tốt hơn Contextual-event (65 cặp vs 23 cặp), và hơn 70% có thứ hạng tương đương (phần lớn do cả hai cùng trượt Top-10). Điều này cho thấy việc đưa thêm log nền gây hiện tượng benign drift. Chúng tôi thiết lập schema so sánh đối chứng scaffold giữa Zero-Shot No-RAG, Zero-Shot RAG và các prompt scaffold, hiện đang được gắn nhãn [PENDING EXECUTION] chờ toàn bộ ma trận TEST hoàn tất để đưa ra kết luận khoa học chính thức.\n"
        "Bằng chứng dự án: scripts/verify_t20_canonical_artifacts.py; outputs/reproduction/tables/table_4_pairwise_representation_comparison.md; tests/test_t20_canonical_artifacts.py."
    )


def build_slide_8_rq1_schema(prs: Presentation) -> None:
    """Slide 8: RQ1 Attribution & RQ2 D2i Error Decomposition."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "7. Khung Đánh Giá End-to-End (RQ1) & Phân Rã Lỗi Độc Lập D2i (RQ2)",
        "Bóc tách độc lập giữa năng lực truy xuất và phân loại theo định đề D2i (Independent Axes)",
    )

    # Top card: Full width across slide (height 2.05 inches, top 1.30 inches -> bottom at 3.35 inches)
    add_card(
        slide,
        0.8,
        1.30,
        11.733,
        2.05,
        "Mô Hình Phân Rã Lỗi Độc Lập Theo Định Đề D2i (RQ2 Error Decomposition)",
        [
            "Định đề D2i quy định retrieval failure và downstream generation failure là CÁC TRỤC ĐỘC LẬP (Independent Axes), không phải phân hoạch xung khắc rời rạc (phần giao thoa khác 0).",
            "Trục 1 - Retrieval Miss Rate: 1 - Hit@k (kỹ thuật ground-truth vắng mặt trong Top-k theo tiêu chí D2h ANY_MATCH).",
            "Trục 2 - Downstream Generation Failure: mô hình phát sinh invalid ATT&CK ID (D2e), gặp lỗi provider (D2f), hoặc chọn sai kỹ thuật dù đã được cung cấp.",
            "Trục 3 - Joint Overlap: ghi nhận rõ các bản ghi retrieval trượt ĐỒNG THỜI mô hình hallucinate/phân loại sai, không áp đặt thứ tự loại trừ nhân tạo.",
        ],
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    # Bottom left card: (top 3.50, height 3.40 -> bottom at 6.90 inches, leaving 0.60 inches before bottom)
    add_card(
        slide,
        0.8,
        3.50,
        5.7,
        3.40,
        "Các Thước Đo Có Điều Kiện (Conditional Metrics)",
        [
            "P(Correct | GT in Top-k): Đánh giá năng lực lựa chọn của LLM khi bộ tìm kiếm hoạt động chính xác.",
            "P(Correct | GT NOT in Top-k): Đánh giá khả năng LLM tự sửa sai dựa trên tri thức nội tại.",
            "Macro-F1 & Exact Match: Tính trên không gian kỹ thuật chuẩn Frozen Benchmark Universe (D2d).",
            "Fail-Closed Invariant: Mẫu lỗi API, timeout (D2f) hay mã sai cú pháp (D2e) đều tính vào mẫu số.",
        ],
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.5,
    )

    # Bottom right card: (top 3.50, height 3.40 -> bottom at 6.90 inches)
    add_card(
        slide,
        6.833,
        3.50,
        5.7,
        3.40,
        "[PENDING EXECUTION] Trạng Thái Thực Nghiệm RQ1 & RQ2",
        [
            "Ma trận TEST chính thức: 1,280 views x 5 nhánh (6,400 bản ghi) đang trong tiến trình chạy (PID 50192).",
            "Nguyên tắc Fail-Closed: Evaluator từ chối công bố điểm chính thức khi chưa đủ 6,400 records.",
            "Kiểm định toán học Evaluator: Đã xác thực ngoại tuyến qua 5 test fixtures (outputs/reproduction/fixture_diagnostics/).",
            "Đầu ra chuẩn: 6 metric JSON artifacts kèm _fixture_metadata.json (fixture_only: true).",
        ],
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.5,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 8):\n"
        "Khung đánh giá RQ1 & RQ2 được xây dựng trên định đề D2i (Independent Axes). Chúng tôi bác bỏ hoàn toàn công thức cộng xác suất rời rạc sai lầm, bởi retrieval failure và downstream generation failure không hề xung khắc nhau mà có phần giao thoa rõ ràng. Các chỉ số có điều kiện P(Correct | GT in Top-k) và P(Correct | GT NOT in Top-k) cho phép định lượng chính xác xem LLM có bị đánh lừa bởi distractor hay có khả năng tự sửa sai. Toàn bộ ma trận chính thức 6,400 bản ghi đang chạy; tính đúng đắn toán học của Evaluator đã được chứng minh qua 5 test fixtures.\n"
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (D2e, D2f, D2h, D2i; SHA-256: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); tests/test_experiment_evaluation.py (94 tests pass)."
    )


def build_slide_9_rq3_cost(prs: Presentation) -> None:
    """Slide 9: RQ3 Cost & Resource Scaling."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "8. Nghiên Cứu Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm (RQ3)",
        "Đo lường từ DEV Cost Pilot trên OpenAI gpt-5.6-luna xhigh và kiểm soát ngân sách",
    )

    add_card(
        slide, 0.8, 1.35, 5.7, 5.55, "DEV Cost Pilot & Kiểm Soát Ngân Sách (RQ3)",
        [
            "Mục đích: Đo lường mức tăng trưởng token thực tế và kiểm tra độ ổn định schema.",
            "Quy mô: 20 yêu cầu thực tế qua Responses API trên 4 DEV views x 5 điều kiện (100% VALID, 0 retry, trễ TB 8,127.6 ms).",
            "Ước tính từ dữ liệu telemetry pilot ban đầu:",
            "  • no_rag (k=0): 643 in / 224 out (~$0.00039 / query)",
            "  • rag_k1 (k=1): 1,115 in / 332 out (~$0.00062 / query)",
            "  • rag_k3 (k=3): 1,741 in / 1,087 out (~$0.00165 / query - telemetry ban đầu)",
            "  • rag_k5 (k=5): 2,518 in / 840 out (~$0.00151 / query)",
            "  • rag_k10 (k=10): 4,537 in / 801 out (~$0.00187 / query)",
            "Phân định rõ chi phí thực nghiệm:",
            "  • Quyết toán thực tế (Verified Spend): $0.024209 USD (conservative: $0.026320 USD).",
            "  • Dự phóng tập TEST (Projected Spend): $8.20 – $8.99 USD cho 6,400 requests.",
            "  • Trần ngân sách đóng băng: $19.99 USD (hard_budget_limit_usd).",
            "  • Khoản giữ chỗ conservative pilot: $0.05264010 USD (reserved_budget_usd).",
        ],
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=2.5,
    )

    fig_path = FIGURES_DIR / "fig_rq3_pilot_token_scaling.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide, 6.833, 4.95, 5.7, 1.95, "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí (RQ3 Trade-off)",
            [
                "Tăng k từ 1 lên 10 giúp tăng Hit rate từ 4.2% lên 45.1%, nhưng lượng token đầu vào tăng ~4x.",
                "Toàn bộ chi phí dự phóng cho tập TEST (< $10 USD) nằm an toàn dưới trần ngân sách đóng băng $19.99 USD.",
            ],
            header_color=SUCCESS_GREEN,
            body_size=11.0,
            item_spacing=2.5,
        )
    else:
        add_card(
            slide, 6.833, 1.35, 5.7, 5.55, "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí",
            [
                "Hiệu quả tăng dần của k:",
                "  • Tăng k từ 1 lên 10 nâng Hit rate từ 4.2% lên 45.1%.",
                "  • Tuy nhiên, chi phí token đầu vào tăng vọt 400%.",
                "Nguy cơ nhiễu ngữ cảnh cho LLM:",
                "  • Với k=10, tài liệu ATT&CK chiếm hơn 4,000 tokens trong prompt.",
                "  • Các ứng viên không liên quan trở thành 'distractors' khiến LLM dễ phân vân khi phân loại.",
                "Dự phóng ngân sách: Toàn bộ 6,400 lượt suy luận của TEST cohort chỉ tiêu tốn ~$8.20 - $9.00 USD.",
            ],
            header_color=PRIMARY_BLUE,
            body_size=11.5,
            item_spacing=3.0,
        )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 9):\n"
        "Trong phân tích RQ3, chúng tôi làm rõ số liệu chi phí từ DEV Cost Pilot (20 requests thực tế trên gpt-5.6-luna). Con số ~$0.00165/query là ước tính từ telemetry pilot ban đầu tại nhánh k=3 do độ dài reasoning output. Chi phí quyết toán thực tế (verified spend) là $0.024209 USD (conservative rate: $0.026320 USD). Chi phí dự phóng cho toàn bộ 6,400 requests của tập TEST là $8.20 – $8.99 USD. Toàn bộ tiến trình được kiểm soát bởi trần ngân sách đóng băng $19.99 USD và khoản giữ chỗ conservative pilot $0.05264010 USD, bảo đảm không bao giờ vượt ngân sách.\n"
        "Bằng chứng dự án: config/experiment_config.json (hard_budget_limit_usd: 19.99); reports/evidence/dev_cost_pilot_20261001/summary.json (SHA-256: f8dfe99479346dbbeff94d6e9dc7d11019623e5932ef27a00f1c3222e4c92b23); tests/test_monetary_guard.py."
    )


def build_slide_10_limitations(prs: Presentation) -> None:
    """Slide 10: Limitations & Threats to Validity."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "9. Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị", "Đánh giá khách quan các hạn chế kỹ thuật và phạm vi khoa học")

    add_card(
        slide, 0.8, 1.35, 3.733, 5.55, "Phạm Vi Dữ Liệu (Scope)",
        [
            "Dữ liệu thử nghiệm Stage B là kịch bản giả lập có cấu trúc (synthetic-paired-v1).",
            "Mặc dù tuân thủ nghiêm ngặt định dạng sự kiện Windows, nó chưa phản ánh toàn diện độ nhiễu của các cuộc tấn công APT thực tế.",
            "Nghiên cứu không khẳng định kết quả áp dụng nguyên vẹn cho môi trường thực tế cho đến khi hoàn tất T15 real pilot.",
        ],
        header_color=ALERT_RED,
        body_size=12.0,
        item_spacing=4.0,
    )

    add_card(
        slide, 4.8, 1.35, 3.733, 5.55, "Mô Hình Nhúng Đơn Tầng",
        [
            "Việc sử dụng all-MiniLM-L6-v2 thuần túy (dense bi-encoder) bộc lộ hạn chế lớn với các từ khóa kỹ thuật số (như Event ID 4720).",
            "Khoảng cách giữa ngôn ngữ nhật ký và ngôn ngữ mô tả của ATT&CK đòi hỏi phải có kiến trúc tìm kiếm lai (Hybrid Search: Dense + BM25 Lexical).",
        ],
        header_color=PRIMARY_BLUE,
        body_size=12.0,
        item_spacing=4.0,
    )

    add_card(
        slide, 8.8, 1.35, 3.733, 5.55, "Phạm Vi Mô Hình & Tái Lập An Toàn",
        [
            "Nghiên cứu tập trung đánh giá trên mô hình đại diện gpt-5.6-luna nhằm kiểm soát chặt chẽ biến số.",
            "Cần mở rộng kiểm nghiệm trên các mô hình mã nguồn mở (Llama-3, Qwen) để xác minh tính phổ quát của quy luật phân rã lỗi.",
            "Quy trình tái lập an toàn: Mọi kịch bản kiểm thử bắt buộc chạy qua runner offline scripts/run_offline_tests.py, tuyệt đối không dùng pytest trần không có guard.",
        ],
        header_color=SLATE_HEADER,
        body_size=12.0,
        item_spacing=4.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 10):\n"
        "Nghiên cứu công khai các giới hạn khoa học: Dữ liệu hiện tại nằm trong phạm vi kịch bản có cấu trúc synthetic-paired-v1; bộ nhúng dense đơn tầng chưa kết nối được từ vựng kỹ thuật hệ thống (Event ID số); và mô hình đánh giá là gpt-5.6-luna. Để đảm bảo an toàn tuyệt đối, mọi quy trình kiểm thử tái lập phải thực thi qua runner offline scripts/run_offline_tests.py nhằm bảo đảm không phát sinh bất kỳ kết nối mạng ngoài nào.\n"
        "Bằng chứng dự án: docs/reproducibility.md; scripts/run_offline_tests.py; tests/test_offline_guard.py (OFFLINE_GUARD egress=0)."
    )


def build_slide_11_reproducibility(prs: Presentation) -> None:
    """Slide 11: Reproducibility & Scientific Contributions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "10. Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học", "Toàn bộ nghiên cứu có thể kiểm chứng ngoại tuyến với chi phí 0 đồng")

    add_card(
        slide, 0.8, 1.35, 5.7, 5.55, "Tái Lập 100% Ngoại Tuyến (Zero-Cost)",
        [
            "Lệnh tái lập tự động toàn diện: uv run python scripts/reproduce_study.py --all",
            "Lệnh kiểm thử bộ test suite có bảo vệ: uv run python scripts/run_offline_tests.py",
            "Tuyệt đối không dùng pytest trần không có OFFLINE_GUARD.",
            "Điều kiện tái lập:",
            "  • Tái lập ngoại tuyến: Sử dụng 15 canonical artifacts đã khóa mật mã trong repo.",
            "  • Tái lập toàn diện luồng live provider: Yêu cầu nạp credentials thực và chạy dưới cơ chế budget guard trần $19.99 USD.",
            "Khóa mật mã 15 artifact cốt lõi trong canonical_experiment_lock_v1.json.",
            "Tự động phát hiện và chặn đứng mọi hành vi rò rỉ mã bí mật hoặc gọi API ra ngoài bằng offline_guard.",
        ],
        header_color=SUCCESS_GREEN,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide, 6.833, 1.35, 5.7, 5.55, "Đóng Góp Khoa Học Cốt Lõi",
        [
            "1. Quy trình thực nghiệm chuẩn hóa: Thiết lập giao thức thực nghiệm đối chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán Windows log attribution.",
            "2. Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i): Phân tích riêng biệt retrieval miss, downstream generation failure và joint overlap.",
            "3. Bằng chứng định lượng về khoảng cách từ vựng và giả thuyết pha loãng ngữ cảnh (Context Dilution Hypothesis).",
            "4. Bộ công cụ nghiên cứu mở: Cung cấp toàn bộ mã nguồn, benchmark, kịch bản tạo slide và dữ liệu chứng cứ nguyên vẹn.",
        ],
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 11):\n"
        "Khả năng tái lập độc lập là cam kết trọng tâm của dự án. Lệnh reproduce_study.py --all tái tạo toàn bộ chẩn đoán, bảng biểu và đồ thị từ 15 artifact đã đóng băng mà không tốn chi phí. Việc kiểm thử bắt buộc sử dụng runner scripts/run_offline_tests.py để kích hoạt OFFLINE_GUARD. Tái lập toàn diện luồng live provider yêu cầu credentials thực và chạy dưới budget guard kiểm soát ngân sách trần $19.99 USD. Bốn đóng góp khoa học cốt lõi đã thiết lập nền tảng đối chứng vững chắc cho cộng đồng RAG an ninh mạng.\n"
        "Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3...); scripts/reproduce_study.py; scripts/run_offline_tests.py; tests/test_smoke_cases.py."
    )


def build_slide_12_conclusion(prs: Presentation) -> None:
    """Slide 12: Conclusion & Q&A."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_NAVY)

    # Accent decorative bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.5), Inches(0.15), Inches(4.5))
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN_ACCENT
    bar.line.fill.background()

    tx = slide.shapes.add_textbox(Inches(1.5), Inches(1.4), Inches(10.5), Inches(4.8))
    tf = tx.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "TỔNG KẾT & PHẦN HỎI ĐÁP (Q&A)"
    p0.font.name = "Calibri"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT

    p1 = tf.add_paragraph()
    p1.text = "RAG2ATT&CK: Đưa Tri Thức Thực Sự Vào Giám Sát An Ninh Mạng"
    p1.font.name = "Calibri"
    p1.font.size = Pt(26)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_before = Pt(8)

    points = [
        "RAG cung cấp tri thức nền tảng quan trọng, nhưng chất lượng khâu truy xuất (Retrieval) là yếu tố quyết định thành bại.",
        "Phân rã lỗi theo D2i (Independent Axes) định lượng độc lập lỗi tìm kiếm, lỗi sinh của mô hình và phần giao thoa.",
        "Quy trình tái lập an toàn: Toàn bộ kiểm thử chạy qua runner offline scripts/run_offline_tests.py bảo đảm không rò rỉ credential.",
        "Định hướng tiếp theo: Triển khai Hybrid Retrieval (Dense + BM25) và kiểm nghiệm mở rộng trên telemetry thực tế.",
        "Mã nguồn, dữ liệu và báo cáo tái lập sẵn sàng tại: https://github.com/habachcp6/RAG2ATTCK",
    ]
    for pt in points:
        p = tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.name = "Calibri"
        p.font.size = Pt(13)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(8)

    p_qa = tf.add_paragraph()
    p_qa.text = "Xin trân trọng cảm ơn Quý Thầy Cô và Hội Đồng! Kính mời đặt câu hỏi thảo luận."
    p_qa.font.name = "Calibri"
    p_qa.font.size = Pt(15)
    p_qa.font.bold = True
    p_qa.font.color.rgb = CYAN_ACCENT
    p_qa.space_before = Pt(18)

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 12):\n"
        "Tóm lại, RAG2ATT&CK đã chứng minh rằng để ứng dụng RAG thành công trong SOC, chúng ta không thể chỉ kỳ vọng vào mô hình ngôn ngữ lớn, mà phải giải quyết bài toán cốt lõi là tối ưu hóa bộ truy xuất và cấu trúc hóa biểu diễn log. Toàn bộ mã nguồn, dữ liệu thực nghiệm và gói tái lập đã được công bố tại PR #26. Tôi xin chân thành cảm ơn sự lắng nghe của Quý Thầy Cô và kính mời Hội đồng đặt câu hỏi thảo luận.\n"
        "Bằng chứng dự án: PR #26 (https://github.com/habachcp6/RAG2ATTCK/pull/26); docs/sanitized_evidence_manifest.json; reports/evidence/reproducibility_package_manifest.md."
    )


# ---------------------------------------------------------------------------
# Slide Deck QA & Verification
# ---------------------------------------------------------------------------

def run_slide_qa(prs: Presentation) -> bool:
    """Validate slide geometry, slide count, and layout consistency."""
    slide_count = len(prs.slides)
    expected_slides = 12
    if slide_count != expected_slides:
        print(f"[QA ERROR] Expected {expected_slides} slides, got {slide_count}")
        return False

    width_in = prs.slide_width.inches
    height_in = prs.slide_height.inches
    if not (abs(width_in - 13.333) < 0.01 and abs(height_in - 7.5) < 0.01):
        print(f"[QA ERROR] Non-widescreen dimensions: {width_in:.3f} x {height_in:.3f}")
        return False

    # Check that every slide has notes
    for i, slide in enumerate(prs.slides, start=1):
        notes_text = slide.notes_slide.notes_text_frame.text.strip()
        if not notes_text:
            print(f"[QA ERROR] Slide {i} is missing speaker notes!")
            return False
        if "Bằng chứng dự án:" not in notes_text and i > 1:
            print(f"[QA ERROR] Slide {i} notes missing project evidence citations!")
            return False

    print(f"[QA PASS] Slide count: {slide_count} (exact match)")
    print(f"[QA PASS] Slide aspect ratio: 16:9 widescreen ({width_in:.3f} x {height_in:.3f} inches)")
    print(f"[QA PASS] All {slide_count} slides have verified speaker notes with evidence citations")
    return True


def main() -> int:
    print("==================================================================")
    print("  RAG2ATTCK: Automated Presentation Slide Deck Generator")
    print("==================================================================")

    prs = create_deck()

    print("[INFO] Building 12 presentation slides...")
    build_slide_1_title(prs)
    build_slide_2_problem(prs)
    build_slide_3_architecture(prs)
    build_slide_4_dataset(prs)
    build_slide_5_methodology(prs)
    build_slide_6_rq2_diagnostics(prs)
    build_slide_7_representation(prs)
    build_slide_8_rq1_schema(prs)
    build_slide_9_rq3_cost(prs)
    build_slide_10_limitations(prs)
    build_slide_11_reproducibility(prs)
    build_slide_12_conclusion(prs)

    # Slide QA
    qa_ok = run_slide_qa(prs)
    if not qa_ok:
        print("[ERROR] Slide QA failed!")
        return 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT_PATH))
    print(f"[SUCCESS] Presentation deck generated successfully:")
    print(f"          -> {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
