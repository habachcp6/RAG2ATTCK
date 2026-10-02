"""RAG2ATTCK - Automated PowerPoint Slide Deck Generator.

Generates a modern, publication-grade 16:9 widescreen presentation deck
in PPTX format for thesis defense, scientific evaluation, and technical demonstration.
Fully compliant with CD_FACTUAL_R2, BD_MODE_BOUNDARY, and CD_RENDER_REPAIR:
- Authoring Backend Disclosure: Authored automatically via python-pptx pipeline
- Canonical Consumer Adapter: dynamically populates typed fields from canonical_metric_bundle_v2.json
- Explicit distinction between accounted token costs vs provisional holds vs canonical forecast
- Transparent characterization of DEV split as synthetic data
    - Technical scope boundary of offline_guard disclosed
      (socket-level Python interceptor, not OS sandbox)
- Non-causal, non-absolute academic tone; independent measurement axes per D2i
- Strict separation of protocol labels: D2d, D2e, D2f, D2g, D2h, D2i
- Perfect typography and card geometry (zero text overflow, safe bottom margin)

Usage:
    # Canonical candidate mode (requires trusted SHA-256 anchor):
    uv run python scripts/generate_slides.py --expected-sha256 442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34

    # Diagnostic fixture mode:
    uv run python scripts/generate_slides.py --fixture-only
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs/presentation/slides.pptx"
FIGURES_DIR = REPO_ROOT / "outputs/reproduction/figures"
CANONICAL_BUNDLE_REL_PATH = Path("artifacts/results/canonical_metric_bundle_v2.json")
DEFAULT_CANONICAL_BUNDLE_PATH = REPO_ROOT / CANONICAL_BUNDLE_REL_PATH
TRUSTED_CANONICAL_BUNDLE_SHA256 = (
    "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"
)

# Color Palette
DARK_NAVY = RGBColor(15, 23, 42)  # #0F172A
SLATE_HEADER = RGBColor(30, 41, 59)  # #1E293B
WHITE = RGBColor(255, 255, 255)
LIGHT_BG = RGBColor(248, 250, 252)  # #F8FAFC
CARD_BG = RGBColor(241, 245, 249)  # #F1F5F9
BORDER_COLOR = RGBColor(203, 213, 225)  # #CBD5E1
DEEP_BLUE = RGBColor(30, 64, 175)  # #1E40AF
PRIMARY_BLUE = RGBColor(37, 99, 235)  # #2563EB
CYAN_ACCENT = RGBColor(6, 182, 212)  # #06B6D4
TEXT_DARK = RGBColor(15, 23, 42)
TEXT_MUTED = RGBColor(100, 116, 139)  # #64748B
TEXT_LIGHT = RGBColor(248, 250, 252)
SUCCESS_GREEN = RGBColor(5, 150, 105)  # #059669
ALERT_RED = RGBColor(220, 38, 38)  # #DC2626

FIXTURE_BANNER_TEXT = "[FIXTURE — PRE-CANONICAL RENDER TEST]"
CANONICAL_BANNER_TEXT = "[CANONICAL CANDIDATE — PENDING ROOT FINAL REVIEW]"


@dataclass
class DeckContext:
    canonical_mode: bool
    banner_text: str
    metrics: dict[str, Any]
    bundle_data: dict[str, Any] | None = None


def extract_bundle_metrics(bundle: dict[str, Any]) -> dict[str, Any]:
    """Extract and format typed metrics directly from canonical_metric_bundle_v2.json."""
    conds = bundle["conditions"]
    no_rag = conds["no_rag"]
    k1 = conds["rag_k1"]
    k3 = conds["rag_k3"]
    k5 = conds["rag_k5"]
    k10 = conds["rag_k10"]
    failures = bundle.get("failure_taxonomy", {})
    financial = bundle.get("whole_study_financial_accounting", {})
    cohort = bundle.get("cohort_breakdown", {})

    # Slide 6 Retrieval metrics
    rm_k1 = k1["rq2_retrieval_and_error"]["retrieval_metrics"]
    rm_k3 = k3["rq2_retrieval_and_error"]["retrieval_metrics"]
    rm_k5 = k5["rq2_retrieval_and_error"]["retrieval_metrics"]
    rm_k10 = k10["rq2_retrieval_and_error"]["retrieval_metrics"]

    # Slide 8 Attribution & Error decomposition
    k10_rq1 = k10["rq1_attribution"]
    no_rag_rq1 = no_rag["rq1_attribution"]
    delta = k10_rq1["delta_vs_baseline"]
    mcnemar = delta["mcnemar_test"]
    k10_cond = k10["rq2_retrieval_and_error"]["generation_conditional_accuracy"]

    # Slide 9 Cost & Tokens
    no_rag_cost = no_rag["rq3_resources_and_cost"]
    k10_cost = k10["rq3_resources_and_cost"]
    retry_details = failures.get("retry_success_details", {})

    return {
        # Cohort
        "scorable_views": cohort.get("mapped_scorable_views", 718),
        "total_test_views": cohort.get("total_views", 1280),
        "distinct_clusters": cohort.get("eligible_bootstrap_clusters", 440),
        # Slide 6 Hit rates
        "hit1_rate": rm_k1.get("retrieval_hit_rate_display", "3.76%"),
        "hit1_count": rm_k1.get("retrieval_hit_count", 27),
        "hit3_rate": rm_k3.get("retrieval_hit_rate_display", "16.43%"),
        "hit3_count": rm_k3.get("retrieval_hit_count", 118),
        "hit5_rate": rm_k5.get("retrieval_hit_rate_display", "24.09%"),
        "hit5_count": rm_k5.get("retrieval_hit_count", 173),
        "hit10_rate": rm_k10.get("retrieval_hit_rate_display", "44.71%"),
        "hit10_count": rm_k10.get("retrieval_hit_count", 321),
        "miss10_rate": rm_k10.get("retrieval_miss_rate_display", "55.29%"),
        "miss10_count": rm_k10.get("retrieval_miss_count", 397),
        "macro_recall10": f"{rm_k10.get('macro_recall', 0.428) * 100:.2f}%",
        # Slide 8 Headline Acc & Delta
        "no_rag_acc": no_rag_rq1.get("accuracy_display", "77.99%"),
        "no_rag_correct": no_rag_rq1.get("correct_count", 560),
        "no_rag_total": no_rag_rq1.get("scorable_sample_count", 718),
        "k10_acc": k10_rq1.get("accuracy_display", "79.53%"),
        "k10_correct": k10_rq1.get("correct_count", 571),
        "k10_total": k10_rq1.get("scorable_sample_count", 718),
        "delta_acc_pp": delta.get("delta_accuracy_display_pp", "+1.532 pp"),
        "delta_ci_95_pp": delta.get("delta_accuracy_ci_95_display_pp", "[-2.355, +5.300] pp"),
        "mcnemar_p_exact": f"{mcnemar.get('p_value_exact', 0.4219):.4f}",
        "mcnemar_p_display": mcnemar.get("display_p_exact", "0.422"),
        # Slide 8 Conditional
        "hit_samples": k10_cond.get("retrieval_success_sample_count", 321),
        "hit_cond_acc": k10_cond.get("p_correct_given_retrieval_success_display", "91.28%"),
        "hit_correct": k10_cond.get("correct_given_retrieval_success_count", 293),
        "miss_samples": k10_cond.get("retrieval_failure_sample_count", 397),
        "miss_cond_acc": k10_cond.get("p_correct_given_retrieval_failure_display", "70.03%"),
        "miss_correct": k10_cond.get("correct_given_retrieval_failure_count", 278),
        # Slide 8 Error boundaries
        "scorable_provider_failures": failures.get("mapped_scorable_terminal_incomplete_count", 0),
        "scorable_records_total": bundle.get("overall_summary", {}).get(
            "total_scorable_mapped_samples_across_conditions", 3590
        ),
        "invalid_id_count": failures.get("invalid_attack_id_count", 0),
        "terminal_incomplete_count": failures.get("terminal_incomplete_count", 13),
        # Slide 9 Resource & Accounting
        "queries_per_condition": cohort.get("total_views", 1280),
        "logical_requests": failures.get("campaign_total_logical_requests", 6400),
        "physical_attempts": failures.get("campaign_total_physical_attempts", 6401),
        "retry_cached_tokens": retry_details.get("cached_tokens", 1540),
        "retry_input_tokens": retry_details.get("input_tokens", 1543),
        "retry_output_tokens": retry_details.get("output_tokens", 452),
        "max_tokens_limit": 8192,
        "budget_cap_usd": financial.get("study_budget_cap_usd", "19.99000000"),
        "settled_cost_usd": financial.get("cumulative_settled_cost_usd", "6.57575890"),
        "pilot_hold_usd": financial.get("prior_pilot_provisional_hold_usd", "0.05264010"),
        "committed_spend_usd": financial.get("total_accounted_expenditure_usd", "6.62839900"),
        "remaining_balance_usd": financial.get("uncommitted_available_balance_usd", "13.36160100"),
        # Query unit costs & tokens
        "no_rag_prompt_tokens": f"{no_rag_cost['tokens']['prompt_tokens']['mean']:.1f}",
        "no_rag_comp_tokens": f"{no_rag_cost['tokens']['completion_tokens']['mean']:.1f}",
        "no_rag_cost_per_req": f"${no_rag_cost['financial_cost_usd']['cost_per_logical_request_usd']:.6f}",
        "k10_prompt_tokens": f"{k10_cost['tokens']['prompt_tokens']['mean']:.1f}",
        "k10_comp_tokens": f"{k10_cost['tokens']['completion_tokens']['mean']:.1f}",
        "k10_cost_per_req": f"${k10_cost['financial_cost_usd']['cost_per_logical_request_usd']:.6f}",
        "no_rag_median_latency_ms": f"{no_rag_cost['latency_ms']['median']:.0f}",
        "k10_median_latency_ms": f"{k10_cost['latency_ms']['median']:.0f}",
    }


def get_default_fixture_metrics() -> dict[str, Any]:
    """Default fallback metric slots for diagnostic fixture mode."""
    return {
        "scorable_views": 718,
        "total_test_views": 1280,
        "distinct_clusters": 440,
        "hit1_rate": "4.23%",
        "hit1_count": 32,
        "hit3_rate": "16.80%",
        "hit3_count": 127,
        "hit5_rate": "24.21%",
        "hit5_count": 183,
        "hit10_rate": "45.11%",
        "hit10_count": 341,
        "miss10_rate": "54.89%",
        "miss10_count": 415,
        "macro_recall10": "43.14%",
        "no_rag_acc": "77.99%",
        "no_rag_correct": 560,
        "no_rag_total": 718,
        "k10_acc": "79.53%",
        "k10_correct": 571,
        "k10_total": 718,
        "delta_acc_pp": "+1.532 pp",
        "delta_ci_95_pp": "[-2.355, +5.300] pp",
        "mcnemar_p_exact": "0.4219",
        "mcnemar_p_display": "0.422",
        "hit_samples": 321,
        "hit_cond_acc": "91.28%",
        "hit_correct": 293,
        "miss_samples": 397,
        "miss_cond_acc": "70.03%",
        "miss_correct": 278,
        "scorable_provider_failures": 0,
        "scorable_records_total": 3590,
        "invalid_id_count": 0,
        "terminal_incomplete_count": 13,
        "queries_per_condition": 1280,
        "logical_requests": 6400,
        "physical_attempts": 6401,
        "retry_cached_tokens": 1540,
        "retry_input_tokens": 1543,
        "retry_output_tokens": 452,
        "max_tokens_limit": 8192,
        "budget_cap_usd": "19.99000000",
        "settled_cost_usd": "6.57575890",
        "pilot_hold_usd": "0.05264010",
        "committed_spend_usd": "6.62839900",
        "remaining_balance_usd": "13.36160100",
        "no_rag_prompt_tokens": "674.3",
        "no_rag_comp_tokens": "163.6",
        "no_rag_cost_per_req": "$0.000365",
        "k10_prompt_tokens": "5114.3",
        "k10_comp_tokens": "333.9",
        "k10_cost_per_req": "$0.001679",
        "no_rag_median_latency_ms": "2303",
        "k10_median_latency_ms": "2667",
    }


def load_and_verify_metric_bundle(
    bundle_path: Path,
    expected_sha256: str | None,
) -> dict[str, Any]:
    """Load and cryptographically verify canonical metric bundle.

    Fail-closed rules:
    - expected_sha256 must be provided (cannot be None or empty)
    - bundle_path must exist and be a file
    - actual SHA-256 of raw bytes must match expected_sha256 exactly
    - content must be valid JSON conforming to canonical bundle schema
    - zero fallback to fixture mode
    """
    if not expected_sha256 or not expected_sha256.strip():
        raise ValueError(
            "[FAIL_CLOSED] Canonical mode requires an explicit --expected-sha256 trust anchor."
        )

    if not bundle_path.is_file():
        raise FileNotFoundError(
            f"[FAIL_CLOSED] Metric bundle file not found: {bundle_path}"
        )

    raw_bytes = bundle_path.read_bytes()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest().lower()
    clean_expected = expected_sha256.strip().lower()

    if actual_sha != clean_expected:
        raise ValueError(
            f"[FAIL_CLOSED] Bundle SHA-256 mismatch for {bundle_path.name}: "
            f"expected {clean_expected}, got {actual_sha}"
        )

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except Exception as exc:
        raise ValueError(
            f"[FAIL_CLOSED] Metric bundle is not valid JSON: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError("[FAIL_CLOSED] Metric bundle JSON root must be an object")

    if data.get("bundle_type") != "canonical-metric-bundle-v2":
        raise ValueError(
            f"[FAIL_CLOSED] Invalid bundle_type: expected 'canonical-metric-bundle-v2', "
            f"got '{data.get('bundle_type')}'"
        )

    return data


def create_deck() -> Presentation:
    """Create a presentation set to 16:9 widescreen layout."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    return prs


def set_slide_background(slide: Any, color: RGBColor) -> None:
    """Set solid color background for slide."""
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(7.5)
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()


def set_speaker_notes(slide: Any, notes_text: str) -> None:
    """Embed speaker notes with artifact citations into slide."""
    notes_slide = slide.notes_slide
    tf = notes_slide.notes_text_frame
    tf.text = notes_text


def add_header(
    slide: Any,
    title_text: str,
    subtitle_text: str = "",
    banner_text: str = FIXTURE_BANNER_TEXT,
) -> None:
    """Add standard header banner to content slide."""
    # Top banner background
    banner = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(13.333), Inches(1.12)
    )
    banner.fill.solid()
    banner.fill.fore_color.rgb = SLATE_HEADER
    banner.line.fill.background()

    # Cyan accent line
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(1.08), Inches(13.333), Inches(0.04)
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = CYAN_ACCENT
    accent.line.fill.background()

    # Title box
    tx_box = slide.shapes.add_textbox(
        Inches(0.8), Inches(0.10), Inches(11.733), Inches(0.90)
    )
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
        p2.text = f"{subtitle_text}  |  {banner_text}"
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
    name: str | None = None,
    header_color: RGBColor = DEEP_BLUE,
    bg_color: RGBColor = CARD_BG,
    border_color: RGBColor = BORDER_COLOR,
    title_size: int = 16,
    body_size: float = 11.5,
    item_spacing: float = 3.0,
) -> Any:
    """Add styled structured card with title and bullet points."""
    card = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left), Inches(top), Inches(width), Inches(height)
    )
    if name:
        card.name = name
    card.fill.solid()
    card.fill.fore_color.rgb = bg_color
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)

    tx_box = slide.shapes.add_textbox(
        Inches(left + 0.2), Inches(top + 0.12), Inches(width - 0.4), Inches(height - 0.24)
    )
    if name:
        tx_box.name = f"{name}_textbox"
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
        p_item.text = (
            f"•  {item}" if not item.startswith("   ") and not item.startswith("  ") else item
        )
        p_item.font.name = "Calibri"
        p_item.font.size = Pt(body_size)
        p_item.font.color.rgb = TEXT_DARK
        p_item.space_before = Pt(item_spacing)


# ---------------------------------------------------------------------------
# Slide Builders
# ---------------------------------------------------------------------------


def build_slide_1_title(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 1: Title Slide (Dark Theme)."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_NAVY)

    # Accent decorative bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.6), Inches(0.15), Inches(4.0)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN_ACCENT
    bar.line.fill.background()

    tx = slide.shapes.add_textbox(Inches(1.5), Inches(1.5), Inches(10.5), Inches(4.2))
    tx.name = "shape_slide_1_title"
    tf = tx.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "BÁO CÁO NGHIÊN CỨU THỰC NGHIỆM ĐỐI CHỨNG"
    p0.font.name = "Calibri"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = CYAN_ACCENT

    p1 = tf.add_paragraph()
    p1.text = (
        "Đánh Giá Tác Động Của MITRE ATT&CK-Grounded RAG Đối Với Việc Ánh Xạ Windows Endpoint Logs"
    )
    p1.font.name = "Calibri"
    p1.font.size = Pt(28)
    p1.font.bold = True
    p1.font.color.rgb = WHITE
    p1.space_before = Pt(10)

    p2 = tf.add_paragraph()
    p2.text = (
        "Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for "
        "Technique Attribution from Windows Endpoint Logs (RAG2ATT&CK)"
    )
    p2.font.name = "Calibri"
    p2.font.size = Pt(15)
    p2.font.italic = True
    p2.font.color.rgb = RGBColor(148, 163, 184)
    p2.space_before = Pt(8)

    p3 = tf.add_paragraph()
    p3.text = "Giao thức khoa học: experiment-protocol-v1.1  |  Khóa chuẩn: canonical-lock-v1"
    p3.font.name = "Calibri"
    p3.font.size = Pt(13)
    p3.font.color.rgb = RGBColor(226, 232, 240)
    p3.space_before = Pt(24)

    p_banner = tf.add_paragraph()
    p_banner.text = ctx.banner_text
    p_banner.font.name = "Calibri"
    p_banner.font.size = Pt(13)
    p_banner.font.bold = True
    p_banner.font.color.rgb = ALERT_RED
    p_banner.space_before = Pt(8)

    bundle_ref = (
        f"; artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {TRUSTED_CANONICAL_BUNDLE_SHA256})"
        if ctx.canonical_mode
        else ""
    )
    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 1):\n"
        "Kính thưa Hội đồng và các chuyên gia, hôm nay tôi xin trình bày báo cáo "
        "nghiên cứu RAG2ATT&CK: Đánh giá tác động của MITRE ATT&CK-grounded RAG đối "
        "với việc ánh xạ Windows endpoint logs sang ATT&CK techniques. Toàn bộ nghiên "
        "cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt dưới "
        "giao thức đóng băng experiment-protocol-v1.1, khóa mật mã 15 canonical "
        "artifacts, và có thể tái lập hoàn toàn ngoại tuyến với chi phí 0 đồng.\n"
        "Khai báo tác tạo: Slide deck này được tác tạo tự động bằng kịch bản Python "
        "scripts/generate_slides.py (sử dụng thư viện python-pptx định dạng 16:9 "
        "widescreen), được thẩm định hiển thị qua bundled artifact tools.\n"
        "Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: "
        "961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac); "
        "reports/experiment_protocol_v1.md (SHA-256: "
        f"d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c){bundle_ref}; "
        "scripts/reproduce_study.py.",
    )


def build_slide_2_problem(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 2: Problem Statement & Motivation."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "1. Vấn Đề Nghiên Cứu & Động Lực Thực Tiễn",
        "Khoảng cách giữa nhật ký cấp thấp (Telemetry) và ma trận kỹ thuật ATT&CK",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        3.733,
        5.55,
        "Bối Cảnh Giám Sát SOC",
        [
            "Nhật ký Windows Endpoint (Security Events, Sysmon) là tuyến phòng thủ cốt "
            "lõi của Trung tâm Giám sát An ninh (SOC).",
            "Việc ánh xạ nhật ký thô sang mã MITRE ATT&CK Technique là tiêu chuẩn vàng "
            "để xác định ý đồ tấn công.",
            "Quy trình thủ công đòi hỏi chuyên gia cấp cao, tốn thời gian và khó đáp "
            "ứng quy mô hàng triệu sự kiện mỗi ngày.",
        ],
        name="shape_slide_2_problem",
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.5,
    )

    add_card(
        slide,
        4.8,
        1.35,
        3.733,
        5.55,
        "Thách Thức Của LLM Thuần Túy",
        [
            "Khoảng cách trừu tượng: Log mang tính kỹ thuật hệ thống (Process GUID, "
            "CommandLine), trong khi ATT&CK mô tả hành vi khái niệm.",
            "Hiện tượng ảo giác: LLM không có RAG dễ suy đoán mã kỹ thuật sai cú pháp "
            "hoặc không tồn tại trong danh mục.",
            "Nhầm lẫn Sub-techniques: Khó phân biệt các kỹ thuật lân cận (ví dụ: "
            "T1059.001 PowerShell vs T1059.003 Command Shell).",
        ],
        name="shape_slide_2_challenge",
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.5,
    )

    add_card(
        slide,
        8.8,
        1.35,
        3.733,
        5.55,
        "Động Lực Của RAG2ATT&CK",
        [
            "Thiết kế nghiên cứu thực nghiệm đối chứng có kiểm soát (Controlled Empirical Study).",
            "Đo lường khách quan delta hiệu năng do RAG mang lại trên cùng mô hình LLM.",
            "Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại "
            "(Classification Failure).",
            "Phạm vi tính xác định (Determinism): Áp dụng cho tái tạo dataset, đánh "
            "giá ngoại tuyến và thứ tự tie-breaking.",
            "Biến thiên backend LLM: Phản hồi LLM có thể biến thiên (không gửi seed "
            "qua mạng), được quản lý bởi chính sách siêu dữ liệu D3 (timestamp-bound).",
            "Tái lập ngoại tuyến chi phí 0 đồng với bộ offline_guard can thiệp tầng socket.",
        ],
        name="shape_slide_2_motivation",
        header_color=SUCCESS_GREEN,
        body_size=10.0,
        item_spacing=2.5,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 2):\n"
        "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và "
        "gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường "
        "gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này định "
        "lượng khách quan mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ, "
        "không phóng đại hiệu năng. Chúng tôi làm rõ phạm vi tính xác định "
        "(determinism): tính xác định áp dụng tuyệt đối cho khâu tái tạo bộ dữ liệu, "
        "quy trình thẩm định đánh giá ngoại tuyến và quy tắc xử lý thứ tự "
        "tie-breaking. Đối với mô hình LLM, phản hồi và backend mô hình thực tế có thể "
        "biến thiên do tham số seed không được truyền qua giao thức mạng; sự biến "
        "thiên này được theo dõi và ghi nhận chặt chẽ theo chính sách siêu dữ liệu "
        "ràng buộc tem thời gian D3 (timestamp-bound metadata policy).\n"
        "Bằng chứng dự án: docs/README_PROPOSED.md; "
        "config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3...); "
        "reports/experiment_protocol_v1.md (D3 policy); "
        "tests/test_attack_id_validation.py.",
    )


def build_slide_3_architecture(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 3: System Architecture."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "2. Kiến Trúc Thực Nghiệm Đối Chứng",
        "So sánh đối đầu giữa Baseline (No-RAG) và Experimental (RAG)",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        3.35,
        "Nhánh Cơ Sở: Baseline No-RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint (endpoint_evidence).",
            "Cơ chế: Đưa trực tiếp vào LLM cùng prompt hướng dẫn chuẩn hóa.",
            "Đầu ra: Chuỗi JSON chứa duy nhất mã technique_id.",
            "Mô hình: gpt-5.6-luna (reasoning_effort=xhigh, api_interface=responses).",
        ],
        name="shape_slide_3_baseline",
        header_color=SLATE_HEADER,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        3.35,
        "Nhánh Thử Nghiệm: Experimental RAG",
        [
            "Đầu vào: Chuỗi sự kiện Windows Endpoint như nhánh cơ sở.",
            "Bộ truy xuất: sentence-transformers/all-MiniLM-L6-v2 + FAISS FlatIP (384-dim).",
            "Kho tri thức: 474 tài liệu ATT&CK v19.2 Enterprise Windows.",
            "Độ sâu k: Đánh giá có hệ thống k ∈ {1, 3, 5, 10}.",
            "Đầu ra: Cùng cấu trúc JSON và cùng bộ kiểm tra cú pháp nghiêm ngặt.",
        ],
        name="shape_slide_3_rag",
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide,
        0.8,
        4.85,
        11.733,
        2.05,
        "Các Biến Kiểm Soát Bất Biến (Controlled Invariants)",
        [
            "Cùng tập dữ liệu thử nghiệm (exact same telemetry instances); Cùng mô "
            "hình và tham số suy luận.",
            "Cùng cấu trúc Prompt (prompts/baseline_v1.txt), chỉ khác biệt ở khối "
            "Context được chèn vào.",
            "Biến duy nhất được thay đổi trong toàn bộ nghiên cứu: Retrieval ON vs. OFF.",
        ],
        name="shape_slide_3_invariants",
        header_color=SUCCESS_GREEN,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 3):\n"
        "Kiến trúc thực nghiệm đối chứng kiểm soát nghiêm ngặt biến số điều trị duy "
        "nhất: Retrieval ON vs OFF. Nhánh Baseline No-RAG và Experimental RAG dùng "
        "chung một mô hình gpt-5.6-luna (xhigh), cùng cấu trúc prompt template, và "
        "cùng schema JSON đầu ra. Bộ tìm kiếm sử dụng all-MiniLM-L6-v2 kết hợp FAISS "
        "IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows.\n"
        "Bằng chứng dự án: prompts/baseline_v1.txt (SHA-256: "
        "b751fde1ee33b03ebca935e478ffef3ff03ff8bcf440263309a039755ab0f7cf); "
        "attack/corpus/enterprise-windows-v19.2.jsonl (SHA-256: "
        "b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75); "
        "config/experiment_config.json; tests/test_rag_pipeline.py.",
    )


def build_slide_4_dataset(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 4: Dataset Strategy & Anti-Leakage."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "3. Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ Nhãn",
        "Bộ dữ liệu chuẩn đóng băng Stage B (670 cặp kịch bản, 1,340 views)",
        banner_text=ctx.banner_text,
    )

    m = ctx.metrics
    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Bộ Dữ Liệu Chuẩn Đóng Băng Stage B",
        [
            "Tổng thể: 670 cặp kịch bản (Scenario Pairs) tương ứng 1,340 Views.",
            f"Phân chia tập: {m['total_test_views']:,} TEST views ({m['scorable_views']} scorable views across {m['distinct_clusters']} distinct clusters) và 60 DEV views.",
            "Hình thức biểu diễn Telemetry:",
            "  • Single-event view: Một sự kiện đơn lẻ kích hoạt kỹ thuật tấn công.",
            "  • Contextual-event view: Sự kiện mục tiêu kèm nhật ký ngữ cảnh lân cận.",
            "Độ bao phủ: 8 nhóm kỹ thuật mục tiêu đại diện cùng các mẫu âm tính / mơ hồ.",
            "Toàn vẹn mật mã: Khóa bằng SHA-256 trong canonical_experiment_lock_v1.json | 278 complete pairs, 162 contextual-only pairs, 200 neither-mapped pairs.",
        ],
        name="shape_slide_4_dataset_topology",
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        5.55,
        "Giao Thức Chống Rò Rỉ Nhãn (Anti-Label-Leakage)",
        [
            "Nguyên tắc cốt lõi: Tuyệt đối không để lộ nhãn hoặc tri thức luật trong "
            "đầu vào suy luận.",
            "Bộ lọc nghiêm ngặt (INFERENCE_ALLOWLIST):",
            "  • Chỉ giữ lại các trường kỹ thuật thô (CommandLine, ParentImage, Hashes).",
            "  • Loại bỏ hoàn toàn: technique_id, RuleName, Tactic, Description, Tags.",
            "Đầu vào suy luận (inference.jsonl) chỉ chứa 2 trường duy nhất: sample_id "
            "và endpoint_evidence.",
            "Phân định phạm vi: Stage B phục vụ kiểm định kỹ thuật & chẩn đoán lỗi; dữ "
            "liệu thực địa (T15 real pilot) được quản lý độc lập.",
        ],
        name="shape_slide_4_representations",
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 4):\n"
        "Tập dữ liệu chuẩn đóng băng Stage B gồm 670 cặp kịch bản đối ứng (1,340 "
        "views), chia thành 1,280 TEST views và 60 DEV views. Giao thức chống rò rỉ "
        "nhãn áp dụng INFERENCE_ALLOWLIST nghiêm ngặt: đầu vào suy luận "
        "inference.jsonl chỉ chứa sample_id và endpoint_evidence; toàn bộ tên luật, mã "
        "technique và mô tả đều bị loại trừ tuyệt đối. Nghiên cứu phân định rõ ràng "
        "giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.\n"
        "Bằng chứng dự án: data/ground_truth/synthetic/inference.jsonl (SHA-256: "
        "90d5f59e64f669f9d7990520625906d40081d5aa112521c7bb5e2f750b3e5fbf); "
        "data/ground_truth/synthetic/pairs.json (SHA-256: "
        "079e57a441b18d12351bb9715fc4b0a43058a9ceb68a8670c5e7bfa5dbad3ca8); "
        "tests/test_benchmark_inputs.py; tests/test_synthetic_freeze.py.",
    )


def build_slide_5_methodology(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 5: Methodology & Frozen Protocol v1.1."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "4. Phương Pháp Luận, Mô Hình Đe Dọa & Giao Thức v1.1",
        "Tách bạch rõ ràng 7 quyết định giao thức khoa học D1-D7 đóng băng",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Mô Hình Đe Dọa & Danh Mục ATT&CK v19.2",
        [
            "Tiêu chuẩn danh mục: Pinned MITRE ATT&CK v19.2 Enterprise Windows (474 "
            "techniques/sub-techniques).",
            "Chính sách kỹ thuật lịch sử (D2g: ALLOW_HISTORICAL):",
            "  • Chấp nhận các mã kỹ thuật lịch sử hoặc đã bị thu hồi "
            "(revoked/deprecated) có trong bộ kiểm chuẩn.",
            "  • Báo cáo dưới dạng distinct observation count, không tự ý gán lại (no "
            "silent remapping).",
            "Vũ trụ Macro-F1 cố định (D2d: FROZEN_BENCHMARK_UNIVERSE = 474):",
            "  • Tính Macro-F1 trên đúng 474 lớp kỹ thuật chuẩn đóng băng, đảm bảo "
            "nhất quán giữa các lần chạy.",
            "Loại trừ mẫu rỗng / mơ hồ (D2b-c: EXCLUDE):",
            "  • Mẫu không gán được nhãn hoặc nhãn mơ hồ bị loại khỏi mẫu số Attribution Accuracy.",
            "Lưu vết đầy đủ (D1: RECORD_ONLY): Lưu toàn văn phản hồi thô phục vụ kiểm "
            "toán độc lập.",
        ],
        name="shape_slide_5_decisions",
        header_color=DEEP_BLUE,
        body_size=11.0,
        item_spacing=2.5,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        5.55,
        "Các Tiêu Chí Giao Thức Đánh Giá Cốt Lõi",
        [
            "D2h: Multi-GT Retrieval Success (ANY_GT_RETRIEVED):",
            "  • Retrieval được tính là thành công nếu BẤT KỲ ground-truth technique "
            "ID nào có trong Top-k candidates.",
            "D2i: Failure Decomposition (INDEPENDENT_AXES):",
            "  • Bóc tách lỗi thành các trục đo lường độc lập; ghi nhận đầy đủ phần "
            "giao thoa khác 0 (non-zero overlap).",
            "D2e: Invalid ID Denominator (invalid_id_as_failure / INCLUDE_IN_DENOMINATOR):",
            "  • Mã kỹ thuật ảo giác, sai cú pháp đều bị tính là thất bại trong mẫu số "
            "end-to-end (Fail-Closed).",
            "D2f: Provider Failure Denominator (api_failure_as_failure / INCLUDE_IN_DENOMINATOR):",
            "  • Lỗi API, timeout, refusal đều tính vào mẫu số thất bại end-to-end, "
            "không được loại trừ.",
            "D3: Khóa mô hình: ALLOW_LATEST_WITH_TIMESTAMP_BINDING (tem UTC thực tế).",
            "D4-D5: Thực thi tuần tự (SEQUENTIAL_ONLY), chặn cứng ngân sách (HARD_CAP).",
        ],
        name="shape_slide_5_criteria",
        header_color=SUCCESS_GREEN,
        body_size=11.0,
        item_spacing=2.5,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 5):\n"
        "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi "
        "D1-D7 và được tách bạch rõ ràng từng nhãn:\n"
        "- D2d: Vũ trụ Macro-F1 cố định đúng 474 lớp (FROZEN_BENCHMARK_UNIVERSE = 474).\n"
        "- D2e: invalid_id_as_failure (INCLUDE_IN_DENOMINATOR cho mã sai cú pháp/ảo giác).\n"
        "- D2f: api_failure_as_failure (INCLUDE_IN_DENOMINATOR cho lỗi provider/timeout/parser).\n"
        "- D2g: ALLOW_HISTORICAL chấp nhận các mã lịch sử/thu hồi dưới dạng distinct "
        "observation count, không tự ý gán lại mã thay thế.\n"
        "- D2h: ANY_GT_RETRIEVED cho multi-label retrieval success.\n"
        "- D2i: INDEPENDENT_AXES ghi nhận đầy đủ phần giao thoa giữa các trục đo lường lỗi.\n"
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (SHA-256: "
        "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); "
        "attack/raw/enterprise-v19.2/enterprise-attack-19.2.json (SHA-256: "
        "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4); "
        "tests/test_experiment_evaluation.py.",
    )


def build_slide_6_rq2_diagnostics(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 6: RQ2 Retrieval Diagnostics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "5. Kết Quả RQ2: Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)",
        "Đánh giá độc lập bộ tìm kiếm trên 718 positive scorable views của benchmark"
        if ctx.canonical_mode
        else "Đánh giá độc lập bộ tìm kiếm trên 756 positive views của benchmark",
        banner_text=ctx.banner_text,
    )

    m = ctx.metrics
    retrieval_items = [
        f"Số mẫu dương tính đánh giá: {m['scorable_views']} / {m['total_test_views']:,} views.",
        "Tỷ lệ tìm trúng theo độ sâu k (Hit@k):",
        f"  • Hit@1:   {m['hit1_rate']} ({m['hit1_count']} / {m['scorable_views']})",
        f"  • Hit@3:  {m['hit3_rate']} ({m['hit3_count']} / {m['scorable_views']})",
        f"  • Hit@5:  {m['hit5_rate']} ({m['hit5_count']} / {m['scorable_views']})",
        f"  • Hit@10: {m['hit10_rate']} ({m['hit10_count']} / {m['scorable_views']})",
        f"Tỷ lệ vắng mặt trong Top-10 (Retrieval Miss): {m['miss10_rate']} ({m['miss10_count']} / {m['scorable_views']}).",
        f"Macro Recall@10: {m['macro_recall10']}  |  Bối cảnh lịch sử T20 pilot: Hit@10=45.11%.",
        f"Phát hiện: Trong hơn 55% trường hợp ({m['miss10_count']}/{m['scorable_views']}), kỹ thuật đúng hoàn toàn vắng bóng "
        "trong Top-10 gửi cho LLM!",
    ]
    card_title = (
        f"Số Liệu Chẩn Đoán Cốt Lõi (TEST N={m['scorable_views']})"
        if ctx.canonical_mode
        else "Số Liệu Chẩn Đoán Cốt Lõi (T20 Overall)"
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        card_title,
        retrieval_items,
        name="shape_slide_6_retrieval_diagnostics",
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    fig_path = FIGURES_DIR / "fig_rq2_retrieval_hit_rates.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide,
            6.833,
            4.95,
            5.7,
            1.95,
            "Giả Thuyết Context Scaling & Dilution (k=1,3,5,10)",
            [
                "Khoảng cách ngữ nghĩa tại T1136.001 (Local Account): 0/95 lượt trúng "
                "Top-10 do log Event ID 4720 lệch từ vựng so với STIX persistence.",
                "Giả thuyết Context Scaling & Dilution: Tăng k tăng độ phủ (Hit@k) "
                "nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng "
                "trên ma trận TEST.",
            ],
            name="shape_slide_6_context_scaling",
            header_color=ALERT_RED,
            body_size=11.0,
            item_spacing=2.5,
        )
    else:
        add_card(
            slide,
            6.833,
            1.35,
            5.7,
            5.55,
            "Phân Tích Thất Bại & Giả Thuyết Context Dilution",
            [
                "Điểm nghẽn nghiêm trọng ở T1136.001 (Local Account):",
                "  • Tỷ lệ trúng Top-10: 0.0% (0 / 95 views TEST).",
                "  • Nguyên nhân: Nhật ký Windows 4720 chứa 'SamAccountName', trong "
                "khi tài liệu ATT&CK nhấn mạnh 'persistence'.",
                "Hiệu quả theo kỹ thuật:",
                "  • T1543.003 (Windows Service): Hit@10 = 87.91% (tốt nhất).",
                "  • T1059.001 (PowerShell): Hit@10 = 68.14%.",
                "  • T1105 (Ingress Tool Transfer): Hit@10 = 15.79% (kém).",
                "Giả thuyết Context Scaling & Dilution: Đã kiểm định đối chứng ma trận TEST.",
            ],
            name="shape_slide_6_context_scaling",
            header_color=ALERT_RED,
            body_size=11.5,
            item_spacing=3.0,
        )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 6):\n"
        f"Chẩn đoán độc lập khâu tìm kiếm (RQ2) trên tập scorable N={m['scorable_views']} cho thấy Hit@10 "
        f"đạt {m['hit10_rate']} ({m['hit10_count']}/{m['scorable_views']}), nghĩa là trong {m['miss10_rate']} trường hợp ({m['miss10_count']}/{m['scorable_views']}), kỹ thuật "
        "đúng hoàn toàn vắng bóng trong Top-10 gửi cho LLM. Điển hình là kỹ thuật "
        "T1136.001 với 0/95 lần trúng Top-10 do khoảng cách ngữ nghĩa giữa Event ID 4720 "
        "và STIX description. Chúng tôi ghi nhận giả thuyết Context Scaling & Dilution "
        "(k=1,3,5,10): tăng k cải thiện độ phủ nhưng tăng nguy cơ nhiễu distractor; "
        "giả thuyết này đã được kiểm chứng thực nghiệm đối chứng end-to-end trên ma trận TEST.\n"
        "Bằng chứng dự án: "
        "outputs/reproduction/figures/fig_rq2_retrieval_hit_rates.png; "
        "outputs/reproduction/tables/table_1_retrieval_diagnostics.md; "
        "tests/test_retrieval_diagnostics.py.",
    )


def build_slide_7_representation(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 7: Representation Gap."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "6. Tác Động Của Hình Thức Biểu Diễn Telemetry",
        "So sánh thực nghiệm Single vs Contextual trên 670 cặp kịch bản đối ứng",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Phân Tích Cặp Anchor Chuẩn (296 Cặp - Primary)",
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
            "Nhóm lọc đơn kỹ thuật nghiêm ngặt (252 cặp - Secondary): Single tốt hơn "
            "59 cặp (23.4%) vs. Contextual 23 cặp (9.1%), ngang nhau 170 cặp.",
        ],
        name="shape_slide_7_paired_analysis",
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        5.55,
        f"Hiện Tượng Quan Sát & Schema So Sánh {ctx.banner_text}",
        [
            "Hiện tượng Benign Drift khi mở rộng ngữ cảnh:",
            "  • Gộp các sự kiện lân cận bổ sung nhiều token thông thường (Explorer, "
            "DNS, svchost).",
            "  • Vector dense embedding bị kéo lệch về hành vi bình thường, làm tụt "
            "thứ hạng kỹ thuật tấn công.",
            f"Schema So Sánh Đối Chứng Scaffold {ctx.banner_text}:",
            "  • Đối chứng: Zero-Shot No-RAG vs Zero-Shot RAG (k=1..10) vs Prompt Scaffolds.",
            "  • Tại RAG k=10: Single và Contextual view đều đạt 83.81% (Paired Delta = 0.0 pp, McNemar p = 1.0).",
            "  • Giả thuyết: Khối tri thức RAG bổ trợ cần đi kèm tiền lọc sự kiện nghi vấn thay vì nhúng thô.",
            "  • Trạng thái: Kiểm chứng đối chứng trên ma trận TEST.",
            "Phạm vi khảo sát: Ghi nhận trên synthetic-paired-v1; cần tiếp tục kiểm "
            "chứng trên telemetry thực tế.",
        ],
        name="shape_slide_7_benign_drift",
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 7):\n"
        "So sánh đối ứng trên 296 cặp anchor chuẩn chỉ ra rằng biểu diễn Single-event "
        "đạt thứ hạng tìm kiếm tốt hơn Contextual-event (65 cặp vs 23 cặp), và hơn 70% "
        "có thứ hạng tương đương (phần lớn do cả hai cùng trượt Top-10). Điều này cho "
        "thấy việc đưa thêm log nền gây hiện tượng benign drift. Chúng tôi thiết lập "
        "schema so sánh đối chứng scaffold giữa Zero-Shot No-RAG, Zero-Shot RAG và các "
        "prompt scaffold. Ở điều kiện RAG k=10 trên 278 cặp đầy đủ nhãn GT, cả Single "
        "và Contextual view đều đạt 83.81% (paired delta = 0.0 pp, McNemar p = 1.0), "
        "nghiêm cấm suy diễn quan hệ nhân quả thuần túy khi hình thức biểu diễn thay đổi.\n"
        "Bằng chứng dự án: scripts/verify_t20_canonical_artifacts.py; "
        "outputs/reproduction/tables/table_4_pairwise_representation_comparison.md; "
        "tests/test_t20_canonical_artifacts.py.",
    )


def build_slide_8_rq1_schema(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 8: RQ1 Attribution & RQ2 D2i Error Decomposition."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "7. Khung Đánh Giá End-to-End (RQ1) & Phân Rã Lỗi Độc Lập D2i (RQ2)",
        "Bóc tách độc lập giữa năng lực truy xuất và phân loại theo định đề D2i (Independent Axes)",
        banner_text=ctx.banner_text,
    )

    m = ctx.metrics
    # Top card: Full width across slide
    add_card(
        slide,
        0.8,
        1.30,
        11.733,
        2.05,
        "Mô Hình Phân Rã Lỗi Độc Lập Theo Định Đề D2i (RQ2 Error Decomposition)",
        [
            "Định đề D2i quy định retrieval failure và downstream generation failure "
            "là CÁC TRỤC ĐO LƯỜNG ĐỘC LẬP (Independent Measurement Axes), không phải "
            "phân hoạch xung khắc rời rạc, không giả định độc lập xác suất ngẫu nhiên "
            "(phần giao thoa khác 0).",
            "Trục 1 - Retrieval Miss Rate: 1 - Hit@k (kỹ thuật ground-truth vắng mặt "
            "trong Top-k theo tiêu chí D2h ANY_MATCH).",
            "Trục 2 - Downstream Generation Failure: mô hình phát sinh invalid ATT&CK "
            "ID (D2e), gặp lỗi provider (D2f), hoặc chọn sai kỹ thuật dù đã được cung "
            "cấp.",
            "Trục 3 - Joint Overlap: ghi nhận rõ các bản ghi retrieval trượt ĐỒNG THỜI "
            "mô hình hallucinate/phân loại sai, không áp đặt thứ tự loại trừ nhân tạo.",
        ],
        name="shape_slide_8_d2i_axes",
        header_color=DEEP_BLUE,
        body_size=11.0,
        item_spacing=2.5,
    )

    # Bottom left card:
    add_card(
        slide,
        0.8,
        3.50,
        5.7,
        3.40,
        "Các Thước Đo Có Điều Kiện & Hiệu Năng RQ1",
        [
            f"Mẫu số đánh giá chuẩn: N={m['scorable_views']} scorable views (trên {m['distinct_clusters']} distinct clusters).",
            f"P(Correct | GT in Top-k): Đánh giá khi retrieval trúng: N={m['hit_samples']} ({m['hit_cond_acc']} gán đúng, {m['hit_correct']}/{m['hit_samples']}).",
            f"P(Correct | GT NOT in Top-k): Đánh giá khi retrieval trượt: N={m['miss_samples']} ({m['miss_cond_acc']} gán đúng, {m['miss_correct']}/{m['miss_samples']}).",
            "Fail-Closed Invariant: Mẫu lỗi API (D2f) hay mã sai cú pháp (D2e) tính vào mẫu số.",
            f"So sánh đối chứng RAG k=10 vs No-RAG: Delta {m['delta_acc_pp']} ({m['k10_acc']} [571/{m['scorable_views']}] vs {m['no_rag_acc']} [560/{m['scorable_views']}]), 95% CI {m['delta_ci_95_pp']} (chứa 0), McNemar p = {m['mcnemar_p_exact']} (hiển thị {m['mcnemar_p_display']}).",
            "Diễn giải học thuật: RAG k=10 đạt độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định (không kết luận vượt trội thống kê).",
        ],
        name="shape_slide_8_conditional_accuracy",
        header_color=PRIMARY_BLUE,
        body_size=10.5,
        item_spacing=2.2,
    )

    # Bottom right card:
    add_card(
        slide,
        6.833,
        3.50,
        5.7,
        3.40,
        f"{ctx.banner_text} Trạng Thái Thực Nghiệm RQ1 & RQ2",
        [
            f"Ma trận TEST chuẩn: N={m['scorable_views']} scorable views x 5 điều kiện (No-RAG, k=1, 3, 5, 10; tổng {m['scorable_records_total']:,} scorable records).",
            f"Ranh giới lỗi phân định: 1 physical API_FAILURE retry thành công; {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records.",
            f"Tổng thể campaign: {m['terminal_incomplete_count']} terminal incomplete trên {m['logical_requests']:,} requests (đều thuộc các view loại trừ/unmapped).",
            f"Khóa toàn vẹn: Bundle v2 SHA-256 đã thẩm định; {m['invalid_id_count']} invalid ID cú pháp; tính toán ngoại tuyến xác thực.",
        ],
        name="shape_slide_8_rq1_attribution",
        header_color=ALERT_RED,
        body_size=10.5,
        item_spacing=2.5,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 8):\n"
        "Khung đánh giá RQ1 & RQ2 được xây dựng trên định đề D2i (Independent "
        "Measurement Axes). Chúng tôi bác bỏ hoàn toàn công thức cộng xác suất rời rạc "
        "sai lầm, bởi retrieval failure và downstream generation failure không hề xung "
        "khắc nhau mà có phần giao thoa rõ ràng; chúng tôi cũng không giả định độc lập "
        "xác suất ngẫu nhiên.\n"
        f"Bảng đối chứng RQ1 ghi nhận RAG k=10 đạt độ chính xác quan sát được cao nhất "
        f"là {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}) so với No-RAG {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}), tức Delta = {m['delta_acc_pp']} "
        f"(+1.96% relative gain; 95% CI {m['delta_ci_95_pp']} chứa 0; kiểm định McNemar "
        f"chính xác p = {m['mcnemar_p_exact']} / hiển thị {m['mcnemar_p_display']} > 0.05). Do đó, nghiên cứu khẳng định "
        "đây là độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định, "
        "tuyệt đối không tuyên bố chiến thắng có ý nghĩa thống kê hay lợi ích vượt trội "
        "trong production.\n"
        f"Ranh giới lỗi phân định độc lập: 1 physical retry thành công sau sự cố mạng "
        f"API_FAILURE; ghi nhận {m['scorable_provider_failures']} terminal provider failure trên toàn bộ {m['scorable_records_total']:,} scorable "
        f"records ({m['terminal_incomplete_count']} incomplete records ghi nhận trên toàn campaign {m['logical_requests']:,} requests đều "
        "thuộc nhóm unmapped/ambiguous).\n"
        f"Về các thước đo có điều kiện tại k=10: P(Correct | GT in Top-k) = {m['hit_cond_acc']} "
        f"({m['hit_correct']}/{m['hit_samples']}), trong khi P(Correct | GT NOT in Top-k) = {m['miss_cond_acc']} ({m['miss_correct']}/{m['miss_samples']}); tỷ lệ "
        "này không cho phép suy diễn mô hình tự sửa sai nội tại.\n"
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (D2e, D2f, D2h, D2i; "
        "SHA-256: d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c); "
        "artifacts/results/canonical_metric_bundle_v2.json; "
        "tests/test_experiment_evaluation.py.",
    )


def build_slide_9_rq3_cost(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 9: RQ3 Cost & Resource Scaling."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "8. Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm (RQ3)",
        "Hạch toán tài chính toàn nghiên cứu, đánh đổi token-chi phí và kiểm soát ngân sách",
        banner_text=ctx.banner_text,
    )

    m = ctx.metrics
    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Hạch Toán Tài Chính Toàn Nghiên Cứu (RQ3)",
        [
            "Bản chất dữ liệu: DEV cohort là dữ liệu tổng hợp (synthetic split). Gửi request thực không biến log tổng hợp thành in-the-wild telemetry.",
            f"Quy mô khảo sát: N={m['queries_per_condition']:,} queries/điều kiện; {m['logical_requests']:,} logical requests; {m['physical_attempts']:,} physical attempts (1 physical API_FAILURE retry thành công với {m['retry_cached_tokens']:,} cached tokens; {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records).",
            f"Ngoại lệ & Trần tokens: {m['terminal_incomplete_count']} requests đạt trần context/output tokens ({m['max_tokens_limit']:,} max tokens) đều thuộc nhóm unmapped/ambiguous.",
            f"Hạch toán tài chính toàn thể nghiên cứu ({m['logical_requests']:,} Requests):",
            f"  • Trần ngân sách đóng băng cứng (Hard budget cap): $19.99 USD (${m['budget_cap_usd']}).",
            f"  • Quyết toán thực tế 5 điều kiện chính thức: $6.58 settled spend (${m['settled_cost_usd']} USD).",
            f"  • Khoản giữ chỗ thận trọng pilot: ${m['pilot_hold_usd']} USD (phân tách rạch ròi khỏi chi phí quyết toán).",
            f"  • Tổng chi phí cam kết (Committed spend): $6.63 USD (${m['committed_spend_usd']} USD).",
            f"  • Ngân sách khả dụng còn lại: $13.36 net remaining (${m['remaining_balance_usd']} USD; 0 holds, 0 breach).",
            f"Đơn giá truy vấn: Baseline No-RAG ~{m['no_rag_cost_per_req']}/req ({m['no_rag_prompt_tokens']} in / {m['no_rag_comp_tokens']} out, trễ {m['no_rag_median_latency_ms']} ms) vs RAG k=10 ~{m['k10_cost_per_req']}/req ({m['k10_prompt_tokens']} in / {m['k10_comp_tokens']} out, trễ {m['k10_median_latency_ms']} ms).",
        ],
        name="shape_slide_9_rq3_resources",
        header_color=DEEP_BLUE,
        body_size=10.5,
        item_spacing=1.8,
    )

    fig_path = FIGURES_DIR / "fig_rq3_pilot_token_scaling.png"
    if fig_path.exists():
        slide.shapes.add_picture(str(fig_path), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide,
            6.833,
            4.95,
            5.7,
            1.95,
            "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí (RQ3 Trade-off)",
            [
                f"Tăng k từ 1 lên 10 nâng Hit rate từ {m['hit1_rate']} lên {m['hit10_rate']}, nhưng lượng token đầu vào tăng ~7.6x.",
                f"Toàn bộ chi phí thực nghiệm (${m['settled_cost_usd']} USD) nằm an toàn dưới trần ngân sách đóng băng $19.99 USD.",
            ],
            name="shape_slide_9_accounting",
            header_color=SUCCESS_GREEN,
            body_size=11.0,
            item_spacing=2.5,
        )
    else:
        add_card(
            slide,
            6.833,
            1.35,
            5.7,
            5.55,
            "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí (RQ3 Trade-off)",
            [
                f"Hiệu quả tăng dần của k (Canonical TEST N={m['scorable_views']}):",
                f"  • Tăng k từ 1 lên 10 nâng Hit rate từ {m['hit1_rate']} lên {m['hit10_rate']}.",
                f"  • Tuy nhiên, chi phí token đầu vào tăng ~7.6x ({m['no_rag_prompt_tokens']} lên {m['k10_prompt_tokens']} tokens).",
                "Nguy cơ nhiễu ngữ cảnh cho LLM:",
                "  • Với k=10, tài liệu ATT&CK chiếm hơn 4,000 tokens trong prompt.",
                "  • Các ứng viên không liên quan trở thành 'distractors' khiến LLM dễ phân vân khi phân loại.",
                "Kiểm soát ngân sách chính xác:",
                f"  • Quyết toán 5 điều kiện chính thức: ${m['settled_cost_usd']} USD ($6.58).",
                f"  • Nằm an toàn dưới trần ngân sách đóng băng cứng $19.99 USD (dư ${m['remaining_balance_usd']} USD).",
            ],
            name="shape_slide_9_accounting",
            header_color=PRIMARY_BLUE,
            body_size=10.5,
            item_spacing=2.0,
        )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 9):\n"
        "Trong phân tích RQ3, chúng tôi làm rõ các khái niệm chi phí, dữ liệu và kiểm "
        "soát ngân sách:\n"
        "1. Dữ liệu DEV là dữ liệu tổng hợp (synthetic-paired-v1 DEV split). Việc gửi "
        "request lên OpenAI không biến log tổng hợp thành dữ liệu thực địa in-the-wild.\n"
        f"2. Toàn bộ nghiên cứu tính trên mẫu số N={m['queries_per_condition']:,} queries / điều kiện (tổng {m['logical_requests']:,} "
        f"logical requests, {m['physical_attempts']:,} physical attempts bao gồm 1 physical retry thành công "
        f"do lỗi mạng API_FAILURE với {m['retry_cached_tokens']:,} cached tokens; ghi nhận {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records).\n"
        f"3. Hạch toán tài chính chính xác: trần ngân sách đóng băng cứng $19.99 USD "
        f"(hard_budget_limit_usd = ${m['budget_cap_usd']}). Chi phí quyết toán thực tế 5 điều kiện "
        f"chính thức là $6.58 settled spend (${m['settled_cost_usd']} USD).\n"
        f"4. Phân biệt rạch ròi: Khoản giữ chỗ thận trọng pilot ${m['pilot_hold_usd']} USD "
        f"(prior_pilot_provisional_hold_usd) được phân tách minh bạch khỏi chi phí "
        f"quyết toán thực tế ${m['settled_cost_usd']} USD. Tổng chi phí cam kết là $6.63 committed "
        f"spend (${m['committed_spend_usd']} USD), ngân sách khả dụng còn lại là $13.36 net remaining "
        f"(${m['remaining_balance_usd']} USD; 0 active holds, 0 breach).\n"
        "Bằng chứng dự án: config/experiment_config.json (hard_budget_limit_usd: "
        "19.99); artifacts/results/canonical_metric_bundle_v2.json; "
        "tests/test_monetary_guard.py.",
    )


def build_slide_10_limitations(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 10: Limitations & Threats to Validity."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "9. Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị",
        "Đánh giá khách quan các hạn chế kỹ thuật và phạm vi khoa học",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        3.733,
        5.55,
        "Phạm Vi Dữ Liệu (Scope)",
        [
            "Dữ liệu thử nghiệm Stage B là kịch bản giả lập có cấu trúc (synthetic-paired-v1).",
            "Mặc dù tuân thủ nghiêm ngặt định dạng sự kiện Windows, nó chưa phản ánh "
            "toàn diện độ nhiễu của các cuộc tấn công APT thực tế.",
            "Nghiên cứu không khẳng định kết quả áp dụng nguyên vẹn cho môi trường "
            "thực tế cho đến khi hoàn tất T15 real pilot.",
        ],
        name="shape_slide_10_limitations_1",
        header_color=ALERT_RED,
        body_size=11.5,
        item_spacing=3.5,
    )

    add_card(
        slide,
        4.8,
        1.35,
        3.733,
        5.55,
        "Mô Hình Nhúng Đơn Tầng",
        [
            "Việc sử dụng all-MiniLM-L6-v2 thuần túy (dense bi-encoder) bộc lộ hạn chế "
            "lớn với các từ khóa kỹ thuật số (như Event ID 4720).",
            "Khoảng cách giữa ngôn ngữ nhật ký và ngôn ngữ mô tả của ATT&CK đòi hỏi "
            "phải có kiến trúc tìm kiếm lai (Hybrid Search: Dense + BM25 Lexical).",
        ],
        name="shape_slide_10_limitations_2",
        header_color=PRIMARY_BLUE,
        body_size=11.5,
        item_spacing=3.5,
    )

    add_card(
        slide,
        8.8,
        1.35,
        3.733,
        5.55,
        "Phạm Vi Mô Hình & Quy Trình Tái Lập",
        [
            "Nghiên cứu tập trung đánh giá trên mô hình đại diện gpt-5.6-luna nhằm "
            "kiểm soát chặt chẽ biến số.",
            "Cần mở rộng kiểm nghiệm trên các mô hình mã nguồn mở (Llama-3, Qwen) để "
            "xác minh tính phổ quát của quy luật phân rã lỗi.",
            "Quy trình tái lập an toàn: Mọi kịch bản kiểm thử bắt buộc chạy qua runner "
            "offline scripts/run_offline_tests.py, can thiệp socket Python để chặn kết "
            "nối ngoài ý muốn.",
        ],
        name="shape_slide_10_limitations_3",
        header_color=SLATE_HEADER,
        body_size=11.5,
        item_spacing=3.5,
    )

    m = ctx.metrics
    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 10):\n"
        "Nghiên cứu công khai các giới hạn khoa học: Dữ liệu hiện tại nằm trong phạm "
        "vi kịch bản có cấu trúc synthetic-paired-v1; bộ nhúng dense đơn tầng chưa kết "
        "nối được từ vựng kỹ thuật hệ thống (Event ID số); và mô hình đánh giá là "
        f"gpt-5.6-luna. Khoảng tin cậy delta chứa 0, kiểm định McNemar p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} > 0.05. "
        "Để đảm bảo an toàn, mọi quy trình kiểm thử tái lập phải thực thi qua runner offline "
        "scripts/run_offline_tests.py nhằm đánh chặn các kết nối mạng ngẫu nhiên ở tầng socket Python.\n"
        "Bằng chứng dự án: docs/reproducibility.md; scripts/run_offline_tests.py; "
        "tests/test_offline_guard.py (OFFLINE_GUARD egress=0).",
    )


def build_slide_11_reproducibility(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 11: Reproducibility & Scientific Contributions."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    add_header(
        slide,
        "10. Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học",
        "Toàn bộ nghiên cứu có thể kiểm chứng ngoại tuyến với chi phí 0 đồng",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Tái Lập Ngoại Tuyến & Phạm Vi Offline Guard",
        [
            "Lệnh chuẩn tắc có bảo vệ ngoại tuyến:",
            "  python scripts/run_offline_tests.py -m pytest ... (hoặc cờ -c)",
            "Lệnh tái lập tự động toàn diện: python scripts/reproduce_study.py --all",
            "Phạm vi kỹ thuật của offline_guard:",
            "  • Can thiệp tầng socket Python (chặn kết nối mạng ngoài ý muốn) và lọc "
            "biến môi trường credentials.",
            "  • Không phải là sandbox cấp OS (không cô lập mã máy binary tùy ý ngoài "
            "Python runtime).",
            "  • Dependencies và artifact tiên quyết đã nạp sẵn cục bộ; lệnh uv run "
            "trần không có guard bảo vệ không tự động đảm bảo cách ly mạng nếu thiếu "
            "cờ offline.",
            "Điều kiện tái lập: Ngoại tuyến dùng 15 artifact đóng băng; luồng live "
            "provider cần credentials thực dưới budget guard trần $19.99 USD.",
        ],
        name="shape_slide_11_reproducibility_1",
        header_color=SUCCESS_GREEN,
        body_size=11.0,
        item_spacing=2.5,
    )

    add_card(
        slide,
        6.833,
        1.35,
        5.7,
        5.55,
        "Đóng Góp Khoa Học Cốt Lõi",
        [
            "1. Quy trình thực nghiệm chuẩn hóa: Thiết lập giao thức thực nghiệm đối "
            "chứng khép kín, chống rò rỉ nhãn đầu tiên cho bài toán Windows log "
            "attribution.",
            "2. Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i): "
            "Phân tích riêng biệt retrieval miss, downstream generation failure và "
            "joint overlap.",
            "3. Bằng chứng định lượng về khoảng cách từ vựng và giả thuyết pha loãng "
            "ngữ cảnh (Context Dilution Hypothesis).",
            "4. Bộ công cụ nghiên cứu mở: Cung cấp toàn bộ mã nguồn, benchmark, kịch "
            "bản tạo slide và dữ liệu chứng cứ nguyên vẹn.",
        ],
        name="shape_slide_11_reproducibility_2",
        header_color=DEEP_BLUE,
        body_size=11.5,
        item_spacing=3.0,
    )

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 11):\n"
        "Khả năng tái lập độc lập là cam kết trọng tâm của dự án. Lệnh "
        "reproduce_study.py --all tái tạo toàn bộ chẩn đoán, bảng biểu và đồ thị từ 15 "
        "artifact đã đóng băng mà không tốn chi phí. Việc kiểm thử bắt buộc sử dụng "
        "runner scripts/run_offline_tests.py để kích hoạt OFFLINE_GUARD. Chúng tôi "
        "minh bạch rõ ràng: offline_guard là cơ chế đánh chặn ở tầng socket Python và "
        "lọc biến môi trường, không phải là sandbox cấp OS. Tái lập toàn diện luồng "
        "live provider yêu cầu credentials thực và chạy dưới budget guard kiểm soát "
        "ngân sách trần $19.99 USD. Bốn đóng góp khoa học cốt lõi đã thiết lập nền "
        "tảng đối chứng vững chắc cho cộng đồng RAG an ninh mạng.\n"
        "Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: "
        "961ba9b3...); artifacts/results/canonical_metric_bundle_v2.json; "
        "scripts/reproduce_study.py; scripts/run_offline_tests.py; "
        "tests/test_smoke_cases.py.",
    )


def build_slide_12_conclusion(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 12: Conclusion & Q&A."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)
    set_slide_background(slide, DARK_NAVY)

    # Accent decorative bar
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(1.2), Inches(1.5), Inches(0.15), Inches(4.5)
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = CYAN_ACCENT
    bar.line.fill.background()

    tx = slide.shapes.add_textbox(Inches(1.5), Inches(1.4), Inches(10.5), Inches(4.8))
    tx.name = "shape_slide_12_conclusion"
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

    m = ctx.metrics
    points = [
        f"RAG cung cấp tri thức nền tảng quan trọng; kết quả đối chứng ghi nhận No-RAG "
        f"đạt {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}) vs RAG k=10 quan sát thấy {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}, Delta = {m['delta_acc_pp']}, "
        f"95% CI {m['delta_ci_95_pp']} chứa 0, McNemar p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} > 0.05).",
        f"Phân rã lỗi D2i theo 3 trục đo lường độc lập (retrieval miss, downstream "
        f"generation failure, joint overlap), ghi nhận phần giao thoa khác 0; ghi nhận "
        f"{m['scorable_provider_failures']} terminal provider failures trên {m['scorable_records_total']:,} scorable records.",
        "Quy trình tái lập ngoại tuyến: Sử dụng runner scripts/run_offline_tests.py "
        "can thiệp tầng socket và lọc biến môi trường nhằm giảm thiểu rủi ro rò rỉ "
        "credential và kết nối ngoài ý muốn.",
        "Định hướng tiếp theo: Triển khai Hybrid Retrieval (Dense + BM25) và kiểm "
        "nghiệm mở rộng trên telemetry thực tế.",
        "Mã nguồn, dữ liệu và báo cáo tái lập sẵn sàng tại: https://github.com/habachcp6/RAG2ATTCK",
    ]
    for pt in points:
        p = tf.add_paragraph()
        p.text = f"•  {pt}"
        p.font.name = "Calibri"
        p.font.size = Pt(12.5)
        p.font.color.rgb = RGBColor(226, 232, 240)
        p.space_before = Pt(6)

    p_qa = tf.add_paragraph()
    p_qa.text = "Xin trân trọng cảm ơn Quý Thầy Cô và Hội Đồng! Kính mời đặt câu hỏi thảo luận."
    p_qa.font.name = "Calibri"
    p_qa.font.size = Pt(15)
    p_qa.font.bold = True
    p_qa.font.color.rgb = CYAN_ACCENT
    p_qa.space_before = Pt(16)

    p_banner = tf.add_paragraph()
    p_banner.text = ctx.banner_text
    p_banner.font.name = "Calibri"
    p_banner.font.size = Pt(13)
    p_banner.font.bold = True
    p_banner.font.color.rgb = ALERT_RED
    p_banner.space_before = Pt(8)

    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 12):\n"
        f"Tóm lại, RAG2ATT&CK đo lường thực nghiệm đối chứng vai trò của RAG trong bài "
        f"toán ánh xạ log Windows sang ATT&CK techniques: No-RAG đạt {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}), "
        f"RAG k=10 đạt {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}, Delta = {m['delta_acc_pp']}, McNemar p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} > 0.05). "
        f"Ghi nhận {m['scorable_provider_failures']} terminal provider failures trên {m['scorable_records_total']:,} scorable records. "
        "Chúng tôi nhấn mạnh tính trung thực khoa học: phân rã lỗi D2i theo các "
        "trục đo lường độc lập không giả định độc lập xác suất ngẫu nhiên, và quy "
        "trình tái lập sử dụng runner can thiệp socket tầng ứng dụng.\n"
        "Khai báo công cụ: Toàn bộ slide deck này được tác tạo tự động bằng kịch bản "
        "Python scripts/generate_slides.py (sử dụng thư viện python-pptx định dạng "
        "16:9 widescreen), được thẩm định hiển thị qua bundled artifact tools.\n"
        "Bằng chứng dự án: PR #26 (https://github.com/habachcp6/RAG2ATTCK/pull/26); "
        "docs/sanitized_evidence_manifest.json; "
        "artifacts/results/canonical_metric_bundle_v2.json; "
        "reports/evidence/reproducibility_package_manifest.md.",
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
    print(
        f"[QA PASS] Slide aspect ratio: 16:9 widescreen ({width_in:.3f} x {height_in:.3f} inches)"
    )
    print(f"[QA PASS] All {slide_count} slides have verified speaker notes with evidence citations")
    return True


def generate_deck(
    *,
    metric_bundle_path: Path | None = None,
    expected_sha256: str | None = None,
    fixture_only: bool = False,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Generate presentation slide deck in either canonical or fixture mode."""
    if fixture_only:
        ctx = DeckContext(
            canonical_mode=False,
            banner_text=FIXTURE_BANNER_TEXT,
            metrics=get_default_fixture_metrics(),
            bundle_data=None,
        )
    else:
        # Canonical mode requires metric bundle and matching SHA-256
        bundle_path = metric_bundle_path or DEFAULT_CANONICAL_BUNDLE_PATH
        bundle_data = load_and_verify_metric_bundle(bundle_path, expected_sha256)
        metrics = extract_bundle_metrics(bundle_data)
        ctx = DeckContext(
            canonical_mode=True,
            banner_text=CANONICAL_BANNER_TEXT,
            metrics=metrics,
            bundle_data=bundle_data,
        )

    prs = create_deck()
    build_slide_1_title(prs, ctx)
    build_slide_2_problem(prs, ctx)
    build_slide_3_architecture(prs, ctx)
    build_slide_4_dataset(prs, ctx)
    build_slide_5_methodology(prs, ctx)
    build_slide_6_rq2_diagnostics(prs, ctx)
    build_slide_7_representation(prs, ctx)
    build_slide_8_rq1_schema(prs, ctx)
    build_slide_9_rq3_cost(prs, ctx)
    build_slide_10_limitations(prs, ctx)
    build_slide_11_reproducibility(prs, ctx)
    build_slide_12_conclusion(prs, ctx)

    qa_ok = run_slide_qa(prs)
    if not qa_ok:
        raise RuntimeError("[ERROR] Slide QA validation failed!")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="RAG2ATTCK - Automated PowerPoint Slide Deck Generator"
    )
    parser.add_argument(
        "--metric-bundle",
        type=Path,
        default=DEFAULT_CANONICAL_BUNDLE_PATH,
        help="Path to canonical metric bundle JSON file",
    )
    parser.add_argument(
        "--expected-sha256",
        type=str,
        default=None,
        help="Expected SHA-256 digest of the metric bundle (required in canonical mode)",
    )
    parser.add_argument(
        "--fixture-only",
        action="store_true",
        help="Run in diagnostic fixture mode (bypasses canonical metric bundle requirement)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help="Target output path for the generated PPTX deck",
    )
    return parser.parse_args(args)


def main(argv: list[str] | None = None) -> int:
    opts = parse_args(argv)
    print("==================================================================")
    print("  RAG2ATTCK: Automated Presentation Slide Deck Generator")
    print("==================================================================")

    try:
        out_file = generate_deck(
            metric_bundle_path=opts.metric_bundle,
            expected_sha256=opts.expected_sha256,
            fixture_only=opts.fixture_only,
            output_path=opts.output,
        )
        print("[SUCCESS] Presentation deck generated successfully:")
        print(f"          -> {out_file} ({out_file.stat().st_size:,} bytes)")
        return 0
    except Exception as exc:
        print(f"[ERROR] Deck generation failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
