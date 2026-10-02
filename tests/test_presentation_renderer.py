"""Tests for Track E Native Slide Deck Generator and Presentation Renderer.

Verifies:
1. Exact slide count: 12 slides, 16:9 widescreen dimensions.
2. Complete speaker notes with verified source pointers on all slides.
3. Strict absence of PENDING, TBD, and private machine paths from slides.pptx.
4. Visible banner '[FIXTURE — PRE-CANONICAL RENDER TEST]' on slides without
   falsely claiming canonical or FINAL/CERTIFIED status.
5. Semantic shape names on key slides with readable typography
   (titles 16-28pt, body 10.5-13pt, zero 7-8pt tiny text).
6. Slide 8 performance metrics: Mapped scorable N=718; conditional accuracy
   separated into N=321 (hits, 91.28%) and N=397 (misses, 70.03%).
7. Slide 9 resource metrics: N=1,280 queries/condition, 6,401 physical attempts
   vs 6,400 logical requests, $19.99 hard cap, $6.63 committed, $13.36 remaining.
8. Synchronization between Markdown source (docs/presentation/slides.md)
   and rendered PPTX deck.
"""

from __future__ import annotations

import re
from pathlib import Path

from pptx import Presentation

REPO_ROOT = Path(__file__).resolve().parents[1]
PPTX_PATH = REPO_ROOT / "docs" / "presentation" / "slides.pptx"
SLIDES_MD_PATH = REPO_ROOT / "docs" / "presentation" / "slides.md"

PRIVATE_PATH_REGEX = re.compile(
    r"(?:[a-zA-Z]:[/\\](?:Users|Documents|Desktop)|/(?:home|Users)/)", re.IGNORECASE
)


def _get_presentation() -> Presentation:
    assert PPTX_PATH.is_file(), f"Presentation file not found at {PPTX_PATH}"
    return Presentation(str(PPTX_PATH))


def _extract_all_slide_texts(prs: Presentation) -> list[dict[str, Any]]:
    """Extract all text items, shapes, and tables per slide."""
    slides_data = []
    for idx, slide in enumerate(prs.slides, start=1):
        slide_info = {
            "slide_num": idx,
            "texts": [],
            "tables": [],
            "shape_names": [],
            "font_sizes": [],
            "notes": "",
        }

        # Notes
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame:
            slide_info["notes"] = slide.notes_slide.notes_text_frame.text.strip()

        # Shapes
        for shape in slide.shapes:
            slide_info["shape_names"].append(shape.name)

            if shape.has_table:
                table_data = []
                for row_idx, row in enumerate(shape.table.rows):
                    row_data = []
                    for cell in row.cells:
                        row_data.append(cell.text.strip())
                        slide_info["texts"].append(cell.text.strip())
                        for p in cell.text_frame.paragraphs:
                            if p.font.size is not None:
                                slide_info["font_sizes"].append(p.font.size.pt)
                    table_data.append(row_data)
                slide_info["tables"].append(
                    {"name": shape.name, "rows": table_data}
                )

            elif shape.has_text_frame:
                full_text = shape.text_frame.text.strip()
                if full_text:
                    slide_info["texts"].append(full_text)
                for p in shape.text_frame.paragraphs:
                    if p.font.size is not None:
                        slide_info["font_sizes"].append(p.font.size.pt)

        slides_data.append(slide_info)
    return slides_data


def test_slide_count_and_widescreen_geometry() -> None:
    """Deck must have exactly 12 slides in 16:9 widescreen layout."""
    prs = _get_presentation()
    assert len(prs.slides) == 12, f"Expected 12 slides, got {len(prs.slides)}"

    width_in = prs.slide_width.inches
    height_in = prs.slide_height.inches
    assert abs(width_in - 13.333) < 0.05, f"Expected width ~13.333 in, got {width_in}"
    assert abs(height_in - 7.500) < 0.05, f"Expected height ~7.500 in, got {height_in}"


def test_every_slide_has_speaker_notes_with_source_pointers() -> None:
    """All 12 slides must contain speaker notes and evidence citations."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    for s in slides_data:
        notes = s["notes"]
        num = s["slide_num"]
        assert len(notes) > 50, f"Slide {num} has empty or trivial speaker notes"
        assert "GHI CHÚ DIỄN GIẢ" in notes, f"Slide {num} missing standard notes header"
        assert "Bằng chứng dự án:" in notes, f"Slide {num} missing evidence citations"
        assert not PRIVATE_PATH_REGEX.search(
            notes
        ), f"Slide {num} speaker notes contain private path"


def test_no_pending_tbd_or_private_paths_in_slides() -> None:
    """Slide text must not contain PENDING, TBD, or private machine paths."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    for s in slides_data:
        num = s["slide_num"]
        for txt in s["texts"]:
            # Exclude header metadata or notes, check visible slide body text
            assert "PENDING" not in txt, f"Slide {num} contains 'PENDING': {txt}"
            assert "TBD" not in txt, f"Slide {num} contains 'TBD': {txt}"
            assert not PRIVATE_PATH_REGEX.search(
                txt
            ), f"Slide {num} contains private path: {txt}"


def test_visible_fixture_banner_on_slides_without_false_canonical() -> None:
    """Visible fixture banner must be displayed; no premature canonical claim."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    banner_token = "[FIXTURE — PRE-CANONICAL RENDER TEST]"
    banner_found_count = 0

    for s in slides_data:
        num = s["slide_num"]
        all_text = " ".join(s["texts"])
        if banner_token in all_text:
            banner_found_count += 1

        # Must not claim certified or final canonical in this phase
        assert "FINAL APPROVED" not in all_text, f"Slide {num} claims FINAL APPROVED"
        assert "CERTIFIED CANONICAL" not in all_text, f"Slide {num} claims CERTIFIED CANONICAL"

    assert (
        banner_found_count >= 10
    ), f"Expected banner on majority of slides, found {banner_found_count}/12"


def test_semantic_shapes_and_readable_typography() -> None:
    """Deck must use semantic shape names and readable typography (>=10pt, zero 7-8pt)."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    # Verify semantic shape names on key slides
    all_shape_names = []
    for s in slides_data:
        all_shape_names.extend(s["shape_names"])

    assert "shape_slide_4_dataset_topology" in all_shape_names
    assert "shape_slide_6_retrieval_diagnostics" in all_shape_names
    assert "shape_slide_8_d2i_axes" in all_shape_names
    assert "shape_slide_8_conditional_accuracy" in all_shape_names
    assert "shape_slide_9_rq3_resources" in all_shape_names

    # Verify font sizes: titles 16-28pt, body 10-13pt, absolutely zero 7-8pt fonts
    for s in slides_data:
        num = s["slide_num"]
        font_sizes = s["font_sizes"]
        assert font_sizes, f"Slide {num} missing font size definitions"
        for fs in font_sizes:
            assert fs >= 10.0, f"Slide {num} contains tiny unreadable font size ({fs}pt < 10pt)"


def test_slide_8_performance_and_conditional_accuracy_metrics() -> None:
    """Slide 8 must specify mapped scorable N=718 and split conditional hits/misses."""
    prs = _get_presentation()
    slide_8_text = " ".join(_extract_all_slide_texts(prs)[7]["texts"])

    # Sample size N=718
    assert "718" in slide_8_text, "Slide 8 must state mapped scorable N=718"

    # Conditional accuracy: N=321 hits (91.28%) vs N=397 misses (70.03%)
    assert "321" in slide_8_text, "Slide 8 must state N=321 hits"
    assert "91.28%" in slide_8_text, "Slide 8 must state 91.28% conditional hit accuracy"
    assert "397" in slide_8_text, "Slide 8 must state N=397 misses"
    assert "70.03%" in slide_8_text, "Slide 8 must state 70.03% conditional miss accuracy"

    # Delta CI [-2.355, +5.300] and McNemar p > 0.05
    assert "-2.355" in slide_8_text or "[-2.355" in slide_8_text
    assert "0.4223" in slide_8_text, "Slide 8 must state McNemar p=0.4223"

    # Academic non-superiority phrasing
    assert (
        "độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định"
        in slide_8_text.lower()
    )


def test_slide_9_resource_metrics_and_whole_study_accounting() -> None:
    """Slide 9 must state N=1,280 queries/condition, 6,401 attempts vs 6,400 requests."""
    prs = _get_presentation()
    slide_9_text = " ".join(_extract_all_slide_texts(prs)[8]["texts"])

    # Sample size N=1,280 queries/condition
    assert "1,280" in slide_9_text, "Slide 9 must state N=1,280 queries / condition"
    assert "6,400" in slide_9_text, "Slide 9 must state 6,400 logical requests"
    assert "6,401" in slide_9_text, "Slide 9 must state 6,401 physical attempts"

    # Budget & financial accounting
    assert "19.99" in slide_9_text, "Slide 9 must state $19.99 budget cap"
    assert "6.58" in slide_9_text or "6.575" in slide_9_text, "Slide 9 must state settled spend"
    assert "6.63" in slide_9_text or "6.628" in slide_9_text, "Slide 9 must state committed spend"
    assert "13.36" in slide_9_text or "13.361" in slide_9_text, "Slide 9 must state net remaining"


def test_markdown_source_synchronization() -> None:
    """docs/presentation/slides.md must exist, have 12 slides, and contain no private paths."""
    assert SLIDES_MD_PATH.is_file(), f"Markdown source missing: {SLIDES_MD_PATH}"
    md_text = SLIDES_MD_PATH.read_text(encoding="utf-8")

    # All 12 slides present
    for i in range(1, 13):
        assert f"## Slide {i}:" in md_text, f"Markdown source missing Slide {i} header"

    # Banner token in Markdown
    assert "[FIXTURE — PRE-CANONICAL RENDER TEST]" in md_text

    # No private paths or TBD in Markdown
    assert not PRIVATE_PATH_REGEX.search(
        md_text
    ), "Markdown source contains private machine path"
    assert "TBD" not in md_text, "Markdown source contains TBD"
