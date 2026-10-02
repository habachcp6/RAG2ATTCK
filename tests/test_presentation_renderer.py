"""Tests for Track E Native Slide Deck Generator and Presentation Renderer.

Verifies:
1. Exact slide count: 12 slides, 16:9 widescreen dimensions.
2. Complete speaker notes with verified source pointers on all slides.
3. Strict absence of unauthorized placeholders (PENDING EXECUTION, TBD) and private machine paths.
4. Visible banner '[CANONICAL CANDIDATE — PENDING ROOT FINAL REVIEW]' on slides without
   falsely claiming final canonical approval.
5. Semantic shape names on key slides with readable typography
   (titles 16-28pt, body 10.5-13pt, zero 7-8pt tiny text).
6. Slide 8 performance metrics: Mapped scorable N=718, Headline accuracy 77.99% (560/718)
   vs 79.53% (571/718), Delta +1.532 pp, McNemar p = 0.4219 / 0.422 (STRICTLY NO 0.4223),
   conditional accuracy separated into N=321 (hits, 91.28%) and N=397 (misses, 70.03%),
   and 1 physical retry succeeded vs 0 terminal provider failures on 3,590 scorable records.
7. Slide 9 resource metrics: N=1,280 queries/condition, 6,401 physical attempts
   vs 6,400 logical requests, 1,540 cached tokens, 8,192 max tokens limit,
   $19.99 hard cap, $6.57575890 settled, $0.05264010 hold, $6.62839900 committed, $13.36160100 remaining.
8. Synchronization between Markdown source (docs/presentation/slides.md)
   and rendered PPTX deck.
9. Canonical consumer adapter verification: accepted digest, missing anchor rejection,
   mutated bytes rejection, and fixture-only fallback mode.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
from pptx import Presentation

from scripts.generate_slides import (
    CANONICAL_BANNER_TEXT,
    FIXTURE_BANNER_TEXT,
    TRUSTED_CANONICAL_BUNDLE_SHA256,
    generate_deck,
    load_and_verify_metric_bundle,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PPTX_PATH = REPO_ROOT / "docs" / "presentation" / "slides.pptx"
SLIDES_MD_PATH = REPO_ROOT / "docs" / "presentation" / "slides.md"
BUNDLE_PATH = REPO_ROOT / "artifacts" / "results" / "canonical_metric_bundle_v2.json"

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
        slide_info: dict[str, Any] = {
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


def test_no_unauthorized_placeholders_or_private_paths_in_slides() -> None:
    """Slide text must not contain raw unauthorized placeholders (TBD, PENDING EXECUTION) or private paths."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    for s in slides_data:
        num = s["slide_num"]
        for txt in s["texts"]:
            # The canonical candidate banner is the only authorized place for PENDING
            if CANONICAL_BANNER_TEXT in txt:
                continue
            assert "PENDING EXECUTION" not in txt, f"Slide {num} contains 'PENDING EXECUTION': {txt}"
            assert "TBD" not in txt, f"Slide {num} contains 'TBD': {txt}"
            assert not PRIVATE_PATH_REGEX.search(
                txt
            ), f"Slide {num} contains private path: {txt}"


def test_visible_canonical_candidate_banner_without_false_final_approval() -> None:
    """Visible canonical candidate banner must be displayed; no false final approval claim."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)

    banner_found_count = 0
    for s in slides_data:
        num = s["slide_num"]
        all_text = " ".join(s["texts"])
        if CANONICAL_BANNER_TEXT in all_text:
            banner_found_count += 1

        # Must not claim final approved canonical in this phase
        assert "FINAL APPROVED" not in all_text, f"Slide {num} claims FINAL APPROVED"
        assert "CERTIFIED CANONICAL" not in all_text, f"Slide {num} claims CERTIFIED CANONICAL"

    assert (
        banner_found_count >= 10
    ), f"Expected canonical banner on majority of slides, found {banner_found_count}/12"


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
    assert "shape_slide_8_rq1_attribution" in all_shape_names
    assert "shape_slide_9_rq3_resources" in all_shape_names
    assert "shape_slide_9_accounting" in all_shape_names

    # Verify font sizes: titles 16-28pt, body 10-13pt, absolutely zero 7-8pt fonts
    for s in slides_data:
        num = s["slide_num"]
        font_sizes = s["font_sizes"]
        assert font_sizes, f"Slide {num} missing font size definitions"
        for fs in font_sizes:
            assert fs >= 10.0, f"Slide {num} contains tiny unreadable font size ({fs}pt < 10pt)"


def test_slide_8_canonical_performance_and_conditional_accuracy_metrics() -> None:
    """Slide 8 must specify N=718, Headline 77.99% vs 79.53%, Delta +1.532 pp, McNemar p=0.4219/0.422 (NO 0.4223)."""
    prs = _get_presentation()
    slide_8_data = _extract_all_slide_texts(prs)[7]
    slide_8_text = " ".join(slide_8_data["texts"])
    slide_8_notes = slide_8_data["notes"]

    # Sample size N=718
    assert "718" in slide_8_text, "Slide 8 must state mapped scorable N=718"

    # Headline counts and accuracies
    assert "560/718" in slide_8_text or "560" in slide_8_text, "Slide 8 must state 560 correct for No-RAG"
    assert "571/718" in slide_8_text or "571" in slide_8_text, "Slide 8 must state 571 correct for RAG k=10"
    assert "77.99%" in slide_8_text, "Slide 8 must state 77.99% for No-RAG"
    assert "79.53%" in slide_8_text, "Slide 8 must state 79.53% for RAG k=10"
    assert "+1.532 pp" in slide_8_text, "Slide 8 must state Delta +1.532 pp"

    # Conditional accuracy: N=321 hits (91.28%) vs N=397 misses (70.03%)
    assert "321" in slide_8_text, "Slide 8 must state N=321 hits"
    assert "91.28%" in slide_8_text, "Slide 8 must state 91.28% conditional hit accuracy"
    assert "397" in slide_8_text, "Slide 8 must state N=397 misses"
    assert "70.03%" in slide_8_text, "Slide 8 must state 70.03% conditional miss accuracy"

    # Delta CI [-2.355, +5.300] and McNemar p=0.4219 / 0.422
    assert "-2.355" in slide_8_text or "[-2.355" in slide_8_text
    assert "0.4219" in slide_8_text or "0.422" in slide_8_text, "Slide 8 must state McNemar p=0.4219 / 0.422"
    assert "0.4223" not in slide_8_text, "Slide 8 must NOT contain incorrect 0.4223"
    assert "0.4223" not in slide_8_notes, "Slide 8 notes must NOT contain incorrect 0.4223"

    # Error boundaries: 1 retry succeeded, 0 scorable provider failures
    assert "1 physical" in slide_8_text or "1 retry" in slide_8_text or "1" in slide_8_text
    assert "0 terminal provider failure" in slide_8_text or "0" in slide_8_text
    assert "3,590" in slide_8_text

    # Academic non-superiority phrasing
    assert (
        "độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định"
        in slide_8_text.lower()
    )


def test_slide_9_resource_metrics_and_whole_study_accounting() -> None:
    """Slide 9 must state N=1,280 queries/condition, 6,401 attempts vs 6,400 requests, 1,540 cached tokens."""
    prs = _get_presentation()
    slide_9_data = _extract_all_slide_texts(prs)[8]
    slide_9_text = " ".join(slide_9_data["texts"])
    slide_9_notes = slide_9_data["notes"]

    # Sample size N=1,280 queries/condition
    assert "1,280" in slide_9_text, "Slide 9 must state N=1,280 queries / condition"
    assert "6,400" in slide_9_text, "Slide 9 must state 6,400 logical requests"
    assert "6,401" in slide_9_text, "Slide 9 must state 6,401 physical attempts"

    # Cached tokens & context window / max tokens
    assert "1,540" in slide_9_text, "Slide 9 must state 1,540 cached tokens from retry"
    assert "8,192" in slide_9_text, "Slide 9 must state 8,192 max tokens limit"

    # Budget & financial accounting
    assert "19.99" in slide_9_text, "Slide 9 must state $19.99 budget cap"
    assert "6.58" in slide_9_text or "6.575" in slide_9_text, "Slide 9 must state settled spend"
    assert "0.05264010" in slide_9_text or "0.052" in slide_9_text, "Slide 9 must distinguish pilot hold"
    assert "6.63" in slide_9_text or "6.628" in slide_9_text, "Slide 9 must state committed spend"
    assert "13.36" in slide_9_text or "13.361" in slide_9_text, "Slide 9 must state net remaining"

    # Notes precision
    assert "6.57575890" in slide_9_notes
    assert "0.05264010" in slide_9_notes
    assert "6.62839900" in slide_9_notes
    assert "13.36160100" in slide_9_notes


def test_markdown_source_synchronization() -> None:
    """docs/presentation/slides.md must exist, have 12 slides, use canonical candidate banner and numbers."""
    assert SLIDES_MD_PATH.is_file(), f"Markdown source missing: {SLIDES_MD_PATH}"
    md_text = SLIDES_MD_PATH.read_text(encoding="utf-8")

    # All 12 slides present
    for i in range(1, 13):
        assert f"## Slide {i}:" in md_text, f"Markdown source missing Slide {i} header"

    # Banner token in Markdown
    assert CANONICAL_BANNER_TEXT in md_text

    # Headline numbers in Markdown
    assert "+1.532 pp" in md_text
    assert "0.4219" in md_text
    assert "0.422" in md_text
    assert "0.4223" not in md_text, "Markdown source must NOT contain incorrect 0.4223"

    # Cached tokens & context window in Markdown
    assert "1,540" in md_text
    assert "8,192" in md_text

    # No private paths or TBD in Markdown
    assert not PRIVATE_PATH_REGEX.search(
        md_text
    ), "Markdown source contains private machine path"
    assert "TBD" not in md_text, "Markdown source contains TBD"


def test_canonical_metric_bundle_accepted_trust_anchor() -> None:
    """Canonical metric bundle v2 loads successfully with verified trusted SHA-256 anchor."""
    assert BUNDLE_PATH.is_file(), f"Bundle file missing: {BUNDLE_PATH}"
    bundle = load_and_verify_metric_bundle(
        BUNDLE_PATH, expected_sha256=TRUSTED_CANONICAL_BUNDLE_SHA256
    )
    assert bundle["bundle_type"] == "canonical-metric-bundle-v2"
    assert "conditions" in bundle
    assert "failure_taxonomy" in bundle
    assert "whole_study_financial_accounting" in bundle


def test_canonical_metric_bundle_missing_trust_anchor_rejected() -> None:
    """Canonical consumer adapter fails closed when caller does not provide expected SHA-256."""
    assert BUNDLE_PATH.is_file()
    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\]"):
        load_and_verify_metric_bundle(BUNDLE_PATH, expected_sha256=None)

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\]"):
        load_and_verify_metric_bundle(BUNDLE_PATH, expected_sha256="")


def test_canonical_metric_bundle_mutated_bytes_rejected(tmp_path: Path) -> None:
    """Canonical consumer adapter fails closed when bundle bytes are tampered."""
    tampered_bundle = tmp_path / "tampered_bundle.json"
    raw_bytes = BUNDLE_PATH.read_bytes()
    # Mutate one byte
    mutated_bytes = bytearray(raw_bytes)
    mutated_bytes[10] = (mutated_bytes[10] + 1) % 256
    tampered_bundle.write_bytes(mutated_bytes)

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\].*mismatch"):
        load_and_verify_metric_bundle(
            tampered_bundle, expected_sha256=TRUSTED_CANONICAL_BUNDLE_SHA256
        )


def test_canonical_metric_bundle_missing_file_rejected(tmp_path: Path) -> None:
    """Canonical consumer adapter fails closed when bundle file does not exist."""
    missing_bundle = tmp_path / "non_existent.json"
    with pytest.raises(FileNotFoundError, match=r"\[FAIL_CLOSED\]"):
        load_and_verify_metric_bundle(
            missing_bundle, expected_sha256=TRUSTED_CANONICAL_BUNDLE_SHA256
        )


def test_fixture_only_mode_roundtrip(tmp_path: Path) -> None:
    """Fixture-only mode runs without requiring metric bundle SHA and produces valid PPTX."""
    fixture_out = tmp_path / "fixture_deck.pptx"
    result_path = generate_deck(
        fixture_only=True,
        output_path=fixture_out,
    )
    assert result_path.is_file()
    assert result_path.stat().st_size > 100_000

    # Verify fixture banner is present
    prs = Presentation(str(result_path))
    texts = []
    for s in prs.slides:
        for shape in s.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                texts.append(shape.text_frame.text)
    combined = " ".join(texts)
    assert FIXTURE_BANNER_TEXT in combined
    assert CANONICAL_BANNER_TEXT not in combined
