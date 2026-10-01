"""RAG2ATTCK - Automated PowerPoint Slide Deck Generator.

Generates a modern, publication-grade 16:9 widescreen presentation deck
in PPTX format for thesis defense, scientific evaluation, and technical demonstration.

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
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs/presentation/slides.pptx"
FIGURES_DIR = REPO_ROOT / "outputs/reproduction/figures"

# Color Palette
DARK_NAVY = RGBColor(15, 23, 42)      # #0F172A
SLATE_HEADER = RGBColor(30, 41, 59)   # #1E293B
WHITE = RGBColor(255, 255, 255)
LIGHT_BG = RGBColor(248, 250, 252)    # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)     # #F1F5F9
BORDER_COLOR = RGBColor(203, 213, 225) # #CBD5E1
DEEP_BLUE = RGBColor(30, 64, 175)     # #1E40AF
PRIMARY_BLUE = RGBColor(37, 99, 235)  # #2563EB
CYAN_ACCENT = RGBColor(6, 182, 212)   # #06B6D4
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
TEXT_LIGHT = RGBColor(248, 250, 252)
SUCCESS_GREEN = RGBColor(5, 150, 105) # #059669
ALERT_RED = RGBColor(220, 38, 38)     # #DC2626


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


def add_header(slide: Any, title_text: str, subtitle_text: str = "") -> None:
    """Add standard header banner to content slide."""
    # Top banner background
    banner = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.1))
    banner.fill.solid()
    banner.fill.fore_color.rgb = SLATE_HEADER
    banner.line.fill.background()

    # Cyan accent line
    accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.08), Inches(13.333), Inches(0.04))
    accent.fill.solid()
    accent.fill.fore_color.rgb = CYAN_ACCENT
    accent.line.fill.background()

    # Title box
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.12), Inches(11.7), Inches(0.85))
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
) -> None:
    """Add styled structured card with title and bullet points."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height))
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)

    tx_box = slide.shapes.add_textbox(Inches(left + 0.2), Inches(top + 0.15), Inches(width - 0.4), Inches(height - 0.3))
    tf = tx_box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = title
    p.font.name = "Calibri"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = header_color

    for item in body_items:
        p_item = tf.add_paragraph()
        p_item.text = f"•  {item}"
        p_item.font.name = "Calibri"
        p_item.font.size = Pt(13)
        p_item.font.color.rgb = TEXT_DARK
        p_item.space_before = Pt(6)


# ---------------------------------------------------------------------------
# Slide Builders
# ---------------------------------------------------------------------------

def build_slide_1_title(prs: Presentation) -> None:
    """Slide 1: Title Slide (Dark Theme)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_NAVY)

    # Accent decorative bar
    bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.6), Inches(0.15), Inches(3.8))
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


def build_slide_2_problem(prs: Presentation) -> None:
    """Slide 2: Problem Statement & Motivation."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "1. Vấn Đề Nghiên Cứu & Động Lực Thực Tiễn", "Khoảng cách giữa nhật ký cấp thấp (Telemetry) và ma trận kỹ thuật ATT&CK")

    add_card(
        slide, 0.8, 1.4, 3.7, 5.5, "Bối Cảnh Giám Sát SOC",
        [
            "Nhật ký Windows Endpoint (Security Events, Sysmon) là tuyến phòng thủ cốt lõi của Trung tâm Giám sát An ninh (SOC).",
            "Việc ánh xạ nhật ký thô sang mã MITRE ATT&CK Technique là tiêu chuẩn vàng để xác định ý đồ tấn công.",
            "Quy trình thủ công đòi hỏi chuyên gia cấp cao, tốn thời gian và khó đáp ứng quy mô hàng triệu sự kiện mỗi ngày.",
        ],
        header_color=PRIMARY_BLUE,
    )

    add_card(
        slide, 4.8, 1.4, 3.7, 5.5, "Thách Thức Của LLM Thuần Túy",
        [
            "Khoảng cách trừu tượng: Log mang tính kỹ thuật hệ thống (Process GUID, CommandLine), trong khi ATT&CK mô tả hành vi khái niệm.",
            "Hiện tượng ảo giác: LLM không có RAG dễ suy đoán mã kỹ thuật sai cú pháp hoặc không tồn tại trong danh mục.",
            "Nhầm lẫn Sub-techniques: Khó phân biệt các kỹ thuật lân cận (ví dụ: T1059.001 PowerShell vs T1059.003 Command Shell).",
        ],
        header_color=ALERT_RED,
    )

    add_card(
        slide, 8.8, 1.4, 3.7, 5.5, "Động Lực Của RAG2ATT&CK",
        [
            "Thiết kế nghiên cứu thực nghiệm có kiểm soát (Controlled Empirical Study).",
            "Đo lường chính xác delta hiệu năng do RAG mang lại trên cùng mô hình LLM.",
            "Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại (Classification Failure).",
            "Đóng băng giao thức v1.1 đảm bảo kết quả tái lập tuyệt đối 100% ngoại tuyến.",
        ],
        header_color=SUCCESS_GREEN,
    )


def build_slide_3_architecture(prs: Presentation) -> None:
    """Slide 3: System Architecture."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "2. Kiến Trúc Thực Nghiệm Đối Chứng", "So sánh đối đầu giữa Baseline (No-RAG) và Experimental (RAG)")

    add_card(
        slide, 0.8, 1.4, 5.7, 3.2, "Nhánh Cơ Sở: Baseline No-RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint (endpoint_evidence).",
            "Cơ chế: Đưa trực tiếp vào LLM cùng prompt hướng dẫn chuẩn hóa.",
            "Đầu ra: Chuỗi JSON chứa duy nhất mã technique_id.",
            "Mô hình: gpt-5.6-luna (reasoning_effort=xhigh, api_interface=responses).",
        ],
        header_color=SLATE_HEADER,
    )

    add_card(
        slide, 6.8, 1.4, 5.7, 3.2, "Nhánh Thử Nghiệm: Experimental RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint như nhánh cơ sở.",
            "Bộ truy xuất: sentence-transformers/all-MiniLM-L6-v2 + FAISS FlatIP (384-dim).",
            "Kho tri thức: 474 tài liệu ATT&CK v19.2 Enterprise Windows.",
            "Độ sâu k: Đánh giá có hệ thống k ∈ {1, 3, 5, 10}.",
            "Đầu ra: Cùng cấu trúc JSON và cùng bộ kiểm tra cú pháp nghiêm ngặt.",
        ],
        header_color=DEEP_BLUE,
    )

    add_card(
        slide, 0.8, 4.8, 11.7, 2.1, "Các Biến Kiểm Soát Bất Biến (Controlled Invariants)",
        [
            "Cùng tập dữ liệu thử nghiệm (exact same telemetry instances); Cùng mô hình và tham số suy luận.",
            "Cùng cấu trúc Prompt (prompts/baseline_v1.txt), chỉ khác biệt ở khối Context được chèn vào.",
            "Biến duy nhất được thay đổi trong toàn bộ nghiên cứu: Retrieval ON vs. OFF.",
        ],
        header_color=SUCCESS_GREEN,
    )


def build_slide_4_dataset(prs: Presentation) -> None:
    """Slide 4: Dataset Strategy & Anti-Leakage."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "3. Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ Nhãn", "Bộ dữ liệu chuẩn đóng băng Stage B (670 cặp kịch bản, 1,340 views)")

    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "Bộ Dữ Liệu Chuẩn Đóng Băng Stage B",
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
    )

    add_card(
        slide, 6.8, 1.4, 5.7, 5.5, "Giao Thức Chống Rò Rỉ Nhãn (Anti-Label-Leakage)",
        [
            "Nguyên tắc cốt lõi: Tuyệt đối không để lộ nhãn hoặc tri thức luật trong đầu vào suy luận.",
            "Bộ lọc nghiêm ngặt (INFERENCE_ALLOWLIST):",
            "  • Chỉ giữ lại các trường kỹ thuật thô (CommandLine, ParentImage, Hashes).",
            "  • Loại bỏ hoàn toàn: technique_id, RuleName, Tactic, Description, Tags.",
            "Đầu vào suy luận (inference.jsonl) chỉ chứa 2 trường duy nhất: sample_id và endpoint_evidence.",
            "Phân định phạm vi: Stage B phục vụ kiểm định kỹ thuật & chẩn đoán lỗi; dữ liệu thực địa (T15 real pilot) được quản lý độc lập.",
        ],
        header_color=ALERT_RED,
    )


def build_slide_5_methodology(prs: Presentation) -> None:
    """Slide 5: Methodology & Frozen Protocol v1.1."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "4. Phương Pháp Luận & Giao Thức Đóng Băng v1.1", "Khóa các quyết định khoa học D1-D7 ngăn chặn việc tùy tiện diễn giải số liệu")

    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "Giao Thức Đóng Băng (Decisions D1 - D7)",
        [
            "D1: RECORD_ONLY - Lưu nguyên văn phản hồi thô phục vụ kiểm toán độc lập.",
            "D2a: ANY_MATCH - Dự đoán trúng bất kỳ nhãn đúng nào trong multi-label là đúng.",
            "D2b-c: EXCLUDE - Loại bỏ mẫu rỗng / mơ hồ khỏi mẫu số đo Attribution Accuracy.",
            "D2d: FROZEN_BENCHMARK_UNIVERSE - Tính Macro-F1 trên không gian lớp cố định.",
            "D2e-f: INCLUDE_IN_DENOMINATOR - Mã sai cú pháp và lỗi mạng đều tính là thất bại.",
            "D2h-i: INDEPENDENT_AXES - Bóc tách độc lập lỗi tìm kiếm và lỗi phân loại.",
            "D3: ALLOW_LATEST_WITH_TIMESTAMP_BINDING - Khóa chuỗi mô hình với tem thời gian UTC.",
        ],
        header_color=DEEP_BLUE,
    )

    add_card(
        slide, 6.8, 1.4, 5.7, 5.5, "Nguyên Tắc Fail-Closed & Tính Toàn Vẹn",
        [
            "Nguyên tắc Fail-Closed:",
            "  • Bất kỳ mã ATT&CK nào sai cú pháp, hết hạn (deprecated) không có trong STIX v19.2 đều bị phạt điểm.",
            "  • Lỗi kết nối hoặc timeout không được bỏ qua mà tính vào mẫu số.",
            "Toàn vẹn khóa Canonical Lock v1:",
            "  • Mã SHA-256 giao thức: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c.",
            "  • Mã SHA-256 mã nguồn thực thi: 8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4.",
            "Evaluator tự động khóa và từ chối xuất kết quả nếu dữ liệu bị xáo trộn hoặc thiếu bản ghi.",
        ],
        header_color=SUCCESS_GREEN,
    )


def build_slide_6_rq2_diagnostics(prs: Presentation) -> None:
    """Slide 6: RQ2 Retrieval Diagnostics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "5. Kết Quả RQ2: Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)", "Đánh giá độc lập bộ tìm kiếm trên 756 positive views của benchmark")

    # Left card: Metrics table
    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "Số Liệu Chẩn Đoán Cốt Lõi (T20 Overall)",
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
    )

    # Right: Try to embed figure or fallback to analysis card
    fig_path = FIGURES_DIR / "fig_rq2_retrieval_hit_rates.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.8), Inches(1.4), width=Inches(5.7))
        # Add small caption card below
        add_card(
            slide, 6.8, 5.0, 5.7, 1.9, "Khoảng Cách Ngữ Nghĩa Ở T1136.001",
            [
                "Kỹ thuật T1136.001 (Tạo tài khoản cục bộ) đạt 0/99 lượt trúng trong Top-10!",
                "Nguyên nhân: Log hệ thống (Event ID 4720) dùng từ ngữ kỹ thuật, trong khi STIX mô tả mục tiêu chiến thuật. Dense embedding không vượt qua được khoảng cách này.",
            ],
            header_color=ALERT_RED,
        )
    else:
        add_card(
            slide, 6.8, 1.4, 5.7, 5.5, "Phân Tích Thất Bại & Khoảng Cách Ngữ Nghĩa",
            [
                "Điểm nghẽn nghiêm trọng ở T1136.001 (Local Account):",
                "  • Tỷ lệ trúng Top-10: 0.0% (0 / 99 views).",
                "  • Nguyên nhân: Nhật ký Windows 4720 chứa 'SamAccountName', trong khi tài liệu ATT&CK nhấn mạnh 'persistence'.",
                "Hiệu quả theo kỹ thuật:",
                "  • T1543.003 (Windows Service): Hit@10 = 87.91% (tốt nhất).",
                "  • T1059.001 (PowerShell): Hit@10 = 68.14%.",
                "  • T1105 (Ingress Tool Transfer): Hit@10 = 15.79% (kém).",
            ],
            header_color=ALERT_RED,
        )


def build_slide_7_representation(prs: Presentation) -> None:
    """Slide 7: Representation Gap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "6. Tác Động Của Hình Thức Biểu Diễn Telemetry", "So sánh thực nghiệm Single vs Contextual trên 670 cặp kịch bản đối ứng")

    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "Phân Tích Cặp Anchor Chuẩn (296 Cặp)",
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
            "Nhóm lọc đơn kỹ thuật nghiêm ngặt (252 cặp): Single tốt hơn 59 cặp (23.4%) vs. Contextual 23 cặp (9.1%), ngang nhau 170 cặp.",
        ],
        header_color=PRIMARY_BLUE,
    )

    add_card(
        slide, 6.8, 1.4, 5.7, 5.5, "Hiện Tượng Quan Sát & Hàm Ý Thiết Kế",
        [
            "Hiện tượng suy giảm thứ hạng khi mở rộng ngữ cảnh:",
            "  • Khi gộp các sự kiện lân cận (tiến trình nền, DNS thông thường), các token không độc hại chiếm đa số văn bản.",
            "  • Vector nhúng tổng thể (dense embedding) bị kéo lệch về phía hành vi bình thường (benign drift).",
            "  • Dẫn đến thứ hạng của kỹ thuật tấn công cốt lõi bị tụt lùi so với khi chỉ nhúng log sự kiện đơn lẻ.",
            "Hàm ý thiết kế hệ thống RAG an ninh mạng:",
            "  • Không nên đưa toàn bộ chuỗi log thô nguyên khối vào bộ nhúng vector.",
            "  • Cần áp dụng bộ lọc sự kiện nghi vấn (Event Filter) trước khi thực hiện truy xuất dense semantic.",
            "  • Khảo sát được ghi nhận trên synthetic-paired-v1; cần tiếp tục kiểm chứng trên telemetry thực tế.",
        ],
        header_color=ALERT_RED,
    )


def build_slide_8_rq1_schema(prs: Presentation) -> None:
    """Slide 8: RQ1 Attribution & Error Decomposition Schema."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "7. Khung Đánh Giá End-to-End & Phân Rã Lỗi RQ1", "Bóc tách độc lập giữa năng lực truy xuất và năng lực phân loại của LLM")

    add_card(
        slide, 0.8, 1.4, 11.7, 2.2, "Công Thức Phân Rã Lỗi Có Kiểm Soát (Error Decomposition)",
        [
            "Lỗi gán nhãn cuối cùng (Attribution Error) được phân rã thành 2 thành phần độc lập:",
            "  P(Attribution Error) = P(Retrieval Failure) + P(Classification Failure | Retrieval Success)",
            "  • Retrieval Failure: Kỹ thuật đúng không có trong Top-k (Ground-truth technique is NOT in Top-k).",
            "  • Classification Failure: Kỹ thuật đúng đã có trong Top-k, nhưng LLM chọn sai kỹ thuật khác.",
        ],
        header_color=DEEP_BLUE,
    )

    add_card(
        slide, 0.8, 3.8, 5.7, 3.2, "Các Thước Đo Có Điều Kiện",
        [
            "P(Correct | GT in Top-k): Đánh giá năng lực của LLM khi bộ tìm kiếm hoạt động chính xác.",
            "P(Correct | GT NOT in Top-k): Đánh giá khả năng LLM tự sửa sai dựa trên tri thức nội tại.",
            "Macro-F1 & Exact Match: Tính trên vũ trụ kỹ thuật chuẩn Frozen Benchmark Universe.",
            "Chống rò rỉ: Evaluator chỉ đọc dữ liệu offline, kiểm tra SHA-256 từng bản ghi.",
        ],
        header_color=PRIMARY_BLUE,
    )

    add_card(
        slide, 6.8, 3.8, 5.7, 3.2, "[PENDING EXECUTION] Trạng Thái Thực Nghiệm",
        [
            "Trạng thái thực nghiệm chính thức: [AWAITING LIVE RUN TERMINATION]",
            "  • Ma trận hoàn chỉnh 1,280 mẫu x 5 nhánh (6,400 bản ghi) đang chạy (PID 50192).",
            "  • Nguyên tắc Fail-Closed: Evaluator từ chối công bố điểm chính thức khi chưa đủ 6,400 records.",
            "Kiểm định toán học ngoại tuyến của Evaluator:",
            "  • Đã kiểm tra qua 5 fixture mẫu chuẩn (outputs/reproduction/fixture_diagnostics/).",
            "  • Tự động xuất đủ 6 metric artifacts với _fixture_metadata.json (fixture_only=True).",
        ],
        header_color=ALERT_RED,
    )


def build_slide_9_rq3_cost(prs: Presentation) -> None:
    """Slide 9: RQ3 Cost & Resource Scaling."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "8. Nghiên Cứu Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm RQ3", "Dữ liệu đo lường thực tế từ DEV Cost Pilot trên OpenAI gpt-5.6-luna (20 requests)")

    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "DEV Cost Pilot: 20 Mẫu Thăm Dò Thực Tế",
        [
            "Mục đích: Đo lường mức tăng trưởng token thực tế và kiểm tra độ ổn định schema.",
            "Quy mô: 20 yêu cầu thực tế qua Responses API trên 4 DEV views x 5 nhánh điều kiện.",
            "Tuân thủ Schema: 100% VALID  |  Số lần Retry: 0 (Độ trễ TB: 8,127.6 ms).",
            "Mức tiêu thụ Token trung bình theo điều kiện k:",
            "  • no_rag (k=0): 643 input tokens  |  224 output tokens",
            "  • rag_k1 (k=1): 1,115 input tokens (tăng 1.7x)",
            "  • rag_k3 (k=3): 1,741 input tokens (tăng 2.7x)",
            "  • rag_k5 (k=5): 2,518 input tokens (tăng 3.9x)",
            "  • rag_k10 (k=10): 4,537 input tokens (tăng 7.1x)",
            "Chi phí thanh toán thực tế cho 20 requests: $0.0242 USD (~600 VNĐ).",
            "[PENDING] Toàn bộ ma trận TEST 6,400 requests dự phóng chi phí: $8.20 – $8.99 USD.",
        ],
        header_color=DEEP_BLUE,
    )

    fig_path = FIGURES_DIR / "fig_rq3_pilot_token_scaling.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.8), Inches(1.4), width=Inches(5.7))
        add_card(
            slide, 6.8, 5.0, 5.7, 1.9, "Quy Luật Đánh Đổi (Trade-off)",
            [
                "Tăng k từ 1 lên 10 giúp tăng Hit rate từ 4.2% lên 45.1%, nhưng lượng token đầu vào tăng gấp 4 lần.",
                "Tổng chi phí TEST dưới $10 chứng minh tính khả thi kinh tế cao của phương pháp.",
            ],
            header_color=SUCCESS_GREEN,
        )
    else:
        add_card(
            slide, 6.8, 1.4, 5.7, 5.5, "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí",
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
        )


def build_slide_10_limitations(prs: Presentation) -> None:
    """Slide 10: Limitations & Threats to Validity."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "9. Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị", "Đánh giá khách quan các hạn chế kỹ thuật và phạm vi khoa học")

    add_card(
        slide, 0.8, 1.4, 3.7, 5.5, "Phạm Vi Dữ Liệu (Scope)",
        [
            "Dữ liệu thử nghiệm Stage B là kịch bản giả lập có cấu trúc (synthetic-paired-v1).",
            "Mặc dù tuân thủ nghiêm ngặt định dạng sự kiện Windows, nó chưa phản ánh toàn diện độ nhiễu của các cuộc tấn công APT thực tế.",
            "Nghiên cứu không khẳng định kết quả áp dụng nguyên vẹn cho môi trường thực tế cho đến khi hoàn tất T15 real pilot.",
        ],
        header_color=ALERT_RED,
    )

    add_card(
        slide, 4.8, 1.4, 3.7, 5.5, "Mô Hình Nhúng Đơn Tầng",
        [
            "Việc sử dụng all-MiniLM-L6-v2 thuần túy (dense bi-encoder) bộc lộ hạn chế lớn với các từ khóa kỹ thuật số (như Event ID 4720).",
            "Khoảng cách giữa ngôn ngữ nhật ký và ngôn ngữ mô tả của ATT&CK đòi hỏi phải có kiến trúc tìm kiếm lai (Hybrid Search: Dense + BM25 Lexical).",
        ],
        header_color=PRIMARY_BLUE,
    )

    add_card(
        slide, 8.8, 1.4, 3.7, 5.5, "Phạm Vi Mô Hình LLM",
        [
            "Nghiên cứu tập trung đánh giá trên mô hình đại diện gpt-5.6-luna nhằm kiểm soát chặt chẽ biến số.",
            "Cần mở rộng kiểm nghiệm trên các mô hình mã nguồn mở (Llama-3, Qwen) để xác minh xem quy luật phân rã lỗi có mang tính phổ quát hay không.",
        ],
        header_color=SLATE_HEADER,
    )


def build_slide_11_reproducibility(prs: Presentation) -> None:
    """Slide 11: Reproducibility & Scientific Contributions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(slide, "10. Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học", "Toàn bộ nghiên cứu có thể kiểm chứng ngoại tuyến với chi phí 0 đồng")

    add_card(
        slide, 0.8, 1.4, 5.7, 5.5, "Tái Lập 100% Ngoại Tuyến (Zero-Cost)",
        [
            "Bất kỳ ai cũng có thể kiểm chứng toàn bộ số liệu bằng 1 lệnh duy nhất:",
            "  uv run python scripts/reproduce_study.py",
            "Không cần tài khoản OpenAI, không cần kết nối Internet, không tốn chi phí.",
            "Khóa mật mã 15 artifact cốt lõi trong canonical_experiment_lock_v1.json.",
            "Tự động phát hiện và chặn đứng mọi hành vi rò rỉ mã bí mật hoặc gọi API ra ngoài bằng offline_guard.",
            "Toàn bộ tài liệu hướng dẫn chi tiết tại docs/reproducibility.md.",
        ],
        header_color=SUCCESS_GREEN,
    )

    add_card(
        slide, 6.8, 1.4, 5.7, 5.5, "Đóng Góp Khoa Học Cốt Lõi",
        [
            "1. Quy trình thực nghiệm chuẩn hóa: Thiết lập giao thức thực nghiệm đối chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán Windows log attribution.",
            "2. Bộ chẩn đoán lỗi phân rã: Định lượng rõ ràng tỷ lệ thất bại của dense retrieval (54.9%) so với năng lực phân loại của LLM.",
            "3. Bằng chứng định lượng về Context Dilution: Chứng minh log ngữ cảnh lân cận làm giảm hiệu quả tìm kiếm so với sự kiện đơn lẻ.",
            "4. Bộ công cụ nghiên cứu mở: Cung cấp toàn bộ mã nguồn, benchmark, kịch bản tạo slide và dữ liệu chứng cứ nguyên vẹn.",
        ],
        header_color=DEEP_BLUE,
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
        "Hiện tượng pha loãng ngữ cảnh (Context Dilution) khẳng định cần tiền lọc log thay vì nhúng toàn bộ chuỗi sự kiện.",
        "Định hướng tiếp theo: Triển khai Hybrid Retrieval (Dense + BM25) và kiểm nghiệm mở rộng trên telemetry thực tế.",
        "Mã nguồn, dữ liệu và báo cáo tái lập sẵn sàng tại: https://github.com/habachcp6/RAG2ATTCK",
    ]
    for pt in points:
        p = tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.name = "Calibri"
        p.font.size = Pt(14)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(10)

    p_qa = tf.add_paragraph()
    p_qa.text = "Xin trân trọng cảm ơn Quý Thầy Cô và Hội Đồng! Kính mời đặt câu hỏi thảo luận."
    p_qa.font.name = "Calibri"
    p_qa.font.size = Pt(16)
    p_qa.font.bold = True
    p_qa.font.color.rgb = CYAN_ACCENT
    p_qa.space_before = Pt(20)


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

    print(f"[QA PASS] Slide count: {slide_count} (exact match)")
    print(f"[QA PASS] Slide aspect ratio: 16:9 widescreen ({width_in:.3f} x {height_in:.3f} inches)")
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
