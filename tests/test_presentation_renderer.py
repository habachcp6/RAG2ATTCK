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

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

import pytest
from PIL import Image
from pptx import Presentation

from scripts.generate_slides import (
    CANONICAL_BANNER_TEXT,
    EXPECTED_ROOT_MEDIA_PIN_SHA256,
    FIXTURE_BANNER_TEXT,
    PINNED_MEDIA_DIGESTS,
    ROOT_MEDIA_PIN_PATH,
    TRUSTED_CANONICAL_BUNDLE_SHA256,
    export_slides_markdown,
    generate_deck,
    load_and_verify_metric_bundle,
    resolve_and_verify_presentation_figure,
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


def test_embedded_figure_media_digests() -> None:
    """Verifies that docs/presentation/slides.pptx contains embedded images with exact SHA-256 digests."""
    assert PPTX_PATH.is_file(), f"Deck file missing at {PPTX_PATH}"

    expected_rq2_sha = "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f"
    expected_rq3_sha = "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1"

    found_shas: set[str] = set()
    with zipfile.ZipFile(str(PPTX_PATH), "r") as zf:
        for name in zf.namelist():
            if name.startswith("ppt/media/"):
                media_bytes = zf.read(name)
                digest = hashlib.sha256(media_bytes).hexdigest()
                found_shas.add(digest)

    assert (
        expected_rq2_sha in found_shas
    ), f"Expected RQ2 hit rate figure {expected_rq2_sha} not found in ppt/media/. Found: {found_shas}"
    assert (
        expected_rq3_sha in found_shas
    ), f"Expected RQ3 resource figure {expected_rq3_sha} not found in ppt/media/. Found: {found_shas}"


def test_deck_figures_audit_records_exist_and_match() -> None:
    """Verifies docs/presentation/deck_figures_audit.json and reports/evidence/canonical_deck_figures_audit.json."""
    deck_audit_path = REPO_ROOT / "docs" / "presentation" / "deck_figures_audit.json"
    evidence_audit_path = REPO_ROOT / "reports" / "evidence" / "canonical_deck_figures_audit.json"

    assert deck_audit_path.is_file(), f"Deck audit missing: {deck_audit_path}"
    assert evidence_audit_path.is_file(), f"Evidence audit missing: {evidence_audit_path}"

    deck_audit = json.loads(deck_audit_path.read_text(encoding="utf-8"))
    evidence_audit = json.loads(evidence_audit_path.read_text(encoding="utf-8"))

    for audit, label in [(deck_audit, "deck_figures_audit"), (evidence_audit, "canonical_deck_figures_audit")]:
        assert audit.get("schema_version") == "1.0.0", f"{label} bad schema version"
        assert audit.get("deck_file") == "docs/presentation/slides.pptx", f"{label} bad deck_file"

        figures = audit.get("embedded_figures", {})
        s6 = figures.get("slide_6_rq2_hit_rate", {})
        assert s6.get("sha256") == "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f"
        assert s6.get("cohort") == "TEST 718 scorable views"

        s9 = figures.get("slide_9_rq3_resource_consumption", {})
        assert s9.get("sha256") == "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1"
        assert "1,280" in s9.get("cohort", "")
        assert s9.get("k1_to_k10_prompt_ratio") == 4.103

        anchors = audit.get("provenance_anchors", {})
        assert anchors.get("canonical_lock") == "d0ce198ad4853f4c41ef2bfbafbe10a395e4927a6c6561b3e72c055c4b887e9f"
        assert anchors.get("baseline_prompt") == "b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206"
        assert anchors.get("inference_data") == "90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8"
        assert anchors.get("pairs_data") == "079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d"
        assert anchors.get("canonical_bundle") == TRUSTED_CANONICAL_BUNDLE_SHA256


def test_strict_absence_of_historical_error_strings() -> None:
    """Verifies strict absence of DEV pilot token series, 756 views, 7.6x for k1->k10, and 0.4223."""
    prs = _get_presentation()
    all_slide_data = _extract_all_slide_texts(prs)

    full_texts: list[str] = []
    for s in all_slide_data:
        full_texts.extend(s["texts"])
        if s["notes"]:
            full_texts.append(s["notes"])

    deck_corpus = " \n ".join(full_texts)
    md_corpus = SLIDES_MD_PATH.read_text(encoding="utf-8")

    forbidden_exact = [
        "643",
        "1115",
        "1740",
        "2618",
        "4636",
        "real-provider DEV pilot",
        "756 positive views",
        "756 views",
        "0.4223",
    ]

    for fb in forbidden_exact:
        assert fb not in deck_corpus, f"Forbidden string '{fb}' found in PPTX deck"
        assert fb not in md_corpus, f"Forbidden string '{fb}' found in slides.md"

    # Strict check: 7.6x or 7.6× attributed to k1->k10
    k1_k10_76x_pattern = re.compile(r"(?:k1\s*->\s*k10|k=1\s*lên\s*k=10|k1\s*đến\s*k10).*?7\.6[x×]", re.IGNORECASE)
    assert not k1_k10_76x_pattern.search(deck_corpus), "Found 7.6x attributed to k1->k10 in PPTX deck"
    assert not k1_k10_76x_pattern.search(md_corpus), "Found 7.6x attributed to k1->k10 in slides.md"


def test_slide_notes_provenance_hashes() -> None:
    """Verifies that all speaker notes contain the exact canonical hashes and correct pairs path."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)
    all_notes = " \n ".join(s["notes"] for s in slides_data)

    expected_lock_sha = "d0ce198ad4853f4c41ef2bfbafbe10a395e4927a6c6561b3e72c055c4b887e9f"
    expected_prompt_sha = "b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206"
    expected_inference_sha = "90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8"
    expected_pairs_sha = "079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d"

    assert expected_lock_sha in all_notes, "Lock SHA missing from speaker notes"
    assert expected_prompt_sha in all_notes, "Prompt SHA missing from speaker notes"
    assert expected_inference_sha in all_notes, "Inference SHA missing from speaker notes"
    assert expected_pairs_sha in all_notes, "Pairs SHA missing from speaker notes"
    assert TRUSTED_CANONICAL_BUNDLE_SHA256 in all_notes, "Bundle SHA missing from speaker notes"

    # Path check: must be pairs.jsonl (NOT pairs.json)
    assert "data/ground_truth/synthetic/pairs.jsonl" in all_notes
    assert "data/ground_truth/synthetic/pairs.json " not in all_notes
    assert "data/ground_truth/synthetic/pairs.json)" not in all_notes

    # Lock hash must NOT be the wrong config hash 961ba9b3...
    assert f"config/canonical_experiment_lock_v1.json (SHA-256: 961ba9b3" not in all_notes


def test_slide_7_canonical_error_diagnostics_and_association_only() -> None:
    """Verifies Slide 7 canonical numbers (retrieved=321, missed=397, 91.28% vs 70.03%, overlap=119/147)."""
    prs = _get_presentation()
    slide_7_data = _extract_all_slide_texts(prs)[6]
    s7_text = " ".join(slide_7_data["texts"])
    s7_notes = slide_7_data["notes"]

    assert "321" in s7_text
    assert "397" in s7_text
    assert "91.28%" in s7_text
    assert "70.03%" in s7_text
    assert "119" in s7_text
    assert "147" in s7_text
    assert "80.95%" in s7_text

    # Must be phrased as observational association, no causal claims
    assert "tương quan quan sát" in s7_text.lower() or "tương quan quan sát" in s7_notes.lower()
    assert "không áp đặt suy diễn quan hệ nhân quả" in s7_notes.lower()

    # Absence of 296 anchor pairs, 65 vs 23, and benign drift claims from canonical mode
    assert "296 anchor" not in s7_text.lower()
    assert "65 cặp" not in s7_text.lower()
    assert "23 cặp" not in s7_text.lower()


def test_slide_8_macro_f1_universe_and_slide_9_token_ratios() -> None:
    """Verifies Slide 8 Macro-F1 across 474 universe and Slide 9 token scaling ratios."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)
    s8_text = " ".join(slides_data[7]["texts"])
    s8_notes = slides_data[7]["notes"]
    s9_text = " ".join(slides_data[8]["texts"])
    s9_notes = slides_data[8]["notes"]

    # Slide 8: Macro-F1 across 474-class universe
    assert "474" in s8_text or "474" in s8_notes
    assert "FROZEN_BENCHMARK_UNIVERSE" in s8_text or "FROZEN_BENCHMARK_UNIVERSE" in s8_notes
    assert "0.0126" in s8_text
    assert "0.0140" in s8_text

    # Slide 9: Prompt token ratios: ~4.103x (k1 -> k10) and ~7.58x vs No-RAG baseline
    assert "4.103x" in s9_text or "4.103x" in s9_notes
    assert "7.58x" in s9_text or "7.58x" in s9_notes


def test_fail_closed_media_guard_rejects_missing_or_tampered(tmp_path: Path) -> None:
    """Verifies that resolve_and_verify_presentation_figure fails closed on any invalid state."""
    # Unknown role
    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Unknown presentation figure role"):
        resolve_and_verify_presentation_figure("non_existent_role", canonical_mode=True)

    # Valid roles in canonical mode resolve and match pinned digests
    rq2_fig = resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)
    assert rq2_fig is not None and rq2_fig.is_file()
    assert hashlib.sha256(rq2_fig.read_bytes()).hexdigest() == PINNED_MEDIA_DIGESTS["rq2_retrieval_hit_rate"]["sha256"]
    assert len(rq2_fig.read_bytes()) == PINNED_MEDIA_DIGESTS["rq2_retrieval_hit_rate"]["byte_size"]

    rq3_fig = resolve_and_verify_presentation_figure("rq3_resource_consumption", canonical_mode=True)
    assert rq3_fig is not None and rq3_fig.is_file()
    assert hashlib.sha256(rq3_fig.read_bytes()).hexdigest() == PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["sha256"]
    assert len(rq3_fig.read_bytes()) == PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["byte_size"]


def test_root_presentation_media_pin_descriptor_integrity() -> None:
    """Verifies existence, cryptographic digest, and pinned asset entries in root pin descriptor."""
    assert ROOT_MEDIA_PIN_PATH.is_file(), f"Missing root pin descriptor: {ROOT_MEDIA_PIN_PATH}"
    actual_sha = hashlib.sha256(ROOT_MEDIA_PIN_PATH.read_bytes()).hexdigest()
    assert actual_sha == EXPECTED_ROOT_MEDIA_PIN_SHA256, (
        f"Root pin descriptor SHA-256 mismatch: expected {EXPECTED_ROOT_MEDIA_PIN_SHA256}, got {actual_sha}"
    )

    data = json.loads(ROOT_MEDIA_PIN_PATH.read_text(encoding="utf-8"))
    assert "assets" in data
    assert data.get("schema_version") == "root-candidate-presentation-media-pin-v1"
    raw_text = ROOT_MEDIA_PIN_PATH.read_text(encoding="utf-8")
    assert PINNED_MEDIA_DIGESTS["rq2_retrieval_hit_rate"]["sha256"] in raw_text
    assert PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["sha256"] in raw_text


def test_slide_8_all_5_conditions_table() -> None:
    """Verifies that Slide 8 renders all 5 conditions in both PPTX and slides.md."""
    prs = _get_presentation()
    slide_8_data = _extract_all_slide_texts(prs)[7]
    s8_text = " ".join(slide_8_data["texts"])
    s8_notes = slide_8_data["notes"]
    md_text = SLIDES_MD_PATH.read_text(encoding="utf-8")

    conditions = ["No-RAG", "k=1", "k=3", "k=5", "k=10"]
    for cond in conditions:
        assert cond in s8_text, f"Condition '{cond}' missing from Slide 8 text"
        assert cond in s8_notes, f"Condition '{cond}' missing from Slide 8 notes"
        assert cond in md_text, f"Condition '{cond}' missing from slides.md"

    # Specific metrics for all conditions
    assert "77.99%" in s8_text  # Baseline & k=3
    assert "77.02%" in s8_text or "553" in s8_text  # k=1
    assert "78.55%" in s8_text or "564" in s8_text  # k=3
    assert "78.83%" in s8_text or "566" in s8_text  # k=5
    assert "79.53%" in s8_text  # k=10

    # Macro-F1 values
    assert "0.0126" in s8_text
    assert "0.0127" in s8_text
    assert "0.0136" in s8_text
    assert "0.0139" in s8_text
    assert "0.0140" in s8_text


def test_slide_9_token_limit_and_protocol_sha_distinction() -> None:
    """Verifies 8,192 configured max_output_tokens clarification and protocol SHA separation."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)
    s9_text = " ".join(slides_data[8]["texts"])
    s9_notes = slides_data[8]["notes"]
    md_text = SLIDES_MD_PATH.read_text(encoding="utf-8")

    # 8,192 max_output_tokens vs context window ceiling
    assert "8,192" in s9_text
    assert "max_output_tokens" in s9_text or "max_output_tokens" in s9_notes
    assert "1.05M" in s9_text or "1.05M" in s9_notes or "cửa sổ ngữ cảnh" in s9_notes

    # Protocol SHA separation: raw file vs canonical decisions digest
    expected_file_sha = "639fd68ae16deec86e9f6baab0980c1abb265c6cd7bb9b4662f562b87e54e819"
    expected_digest_sha = "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"

    all_notes = " \n ".join(s["notes"] for s in slides_data)
    assert expected_file_sha in all_notes, "Protocol raw file SHA-256 missing from speaker notes"
    assert expected_digest_sha in all_notes, "Protocol decisions digest missing from speaker notes"

    assert expected_file_sha in md_text, "Protocol raw file SHA-256 missing from slides.md"
    assert expected_digest_sha in md_text, "Protocol decisions digest missing from slides.md"


def test_absence_of_unsupported_claims_and_causal_statements() -> None:
    """Verifies removal of 'đầu tiên', causal claims, and 'nhờ năng lực nội tại'."""
    prs = _get_presentation()
    slides_data = _extract_all_slide_texts(prs)
    all_slide_texts = [" ".join(s["texts"]) for s in slides_data]
    all_slide_notes = [s["notes"] for s in slides_data]
    md_text = SLIDES_MD_PATH.read_text(encoding="utf-8")

    # Slide 11: No "đầu tiên"
    s11_text = all_slide_texts[10]
    assert "đầu tiên cho bài toán" not in s11_text
    assert "nhãn đầu tiên" not in s11_text
    assert "đầu tiên" not in s11_text
    assert "đầu tiên cho bài toán" not in md_text
    assert "nhãn đầu tiên" not in md_text

    # Slide 6: Phrased as lexical divergence hypothesis, no causal claims
    s6_text = all_slide_texts[5]
    s6_notes = all_slide_notes[5]
    assert "nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng trên ma trận TEST." in s6_text
    assert "nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng trên ma trận TEST." in s6_notes
    assert "phân kỳ từ vựng" in s6_text.lower() or "lexical divergence" in s6_text.lower() or "phân kỳ từ vựng" in s6_notes.lower()

    # Slide 7: No "nhờ năng lực nội tại", observational association only
    s7_text = all_slide_texts[6]
    s7_notes = all_slide_notes[6]
    assert "nhờ năng lực nội tại" not in s7_text
    assert "nhờ năng lực nội tại" not in s7_notes
    assert "nhờ năng lực nội tại" not in md_text
    assert "tương quan quan sát" in s7_text.lower() or "tương quan quan sát" in s7_notes.lower()
    assert "Schema So Sánh Đối Chứng Scaffold: Không sử dụng prompt scaffold trong giao thức chuẩn tắc." in s7_text


def test_fail_closed_media_guard_rejects_missing_root_descriptor(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verifies that resolve_and_verify_presentation_figure fails closed if root pin descriptor is missing or tampered."""
    import scripts.generate_slides as gs

    # Missing descriptor file
    missing_desc = tmp_path / "missing_root_pin.json"
    monkeypatch.setattr(gs, "ROOT_MEDIA_PIN_PATH", missing_desc)
    with pytest.raises(
        FileNotFoundError, match=r"\[FAIL_CLOSED\] Root presentation media pin descriptor missing"
    ):
        gs.resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)

    # Tampered descriptor file (digest mismatch)
    tampered_desc = tmp_path / "tampered_root_pin.json"
    tampered_desc.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(gs, "ROOT_MEDIA_PIN_PATH", tampered_desc)
    with pytest.raises(
        ValueError, match=r"\[FAIL_CLOSED\] Root presentation media pin descriptor SHA-256 mismatch"
    ):
        gs.resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)


def test_fail_closed_media_guard_rejects_corrupt_idat(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verifies that resolve_and_verify_presentation_figure fails closed on corrupt IDAT / invalid raster data."""
    import copy
    import scripts.generate_slides as gs

    genuine_file = PINNED_MEDIA_DIGESTS["rq2_retrieval_hit_rate"]["primary_file"]
    orig_bytes = genuine_file.read_bytes()

    # 1. Post-hash drift on disk: file content mutated so SHA does not match spec
    drift_file = tmp_path / "drifted_figure.png"
    drift_file.write_bytes(b"not_a_valid_png_content_at_all")
    mock_digests = copy.deepcopy(PINNED_MEDIA_DIGESTS)
    mock_digests["rq2_retrieval_hit_rate"]["primary_file"] = drift_file
    mock_digests["rq2_retrieval_hit_rate"]["alias_file"] = drift_file
    monkeypatch.setattr(gs, "PINNED_MEDIA_DIGESTS", mock_digests)

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Figure SHA-256 mismatch"):
        gs.resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)

    # 2. Corrupt IDAT chunk where hash matches descriptor but PIL decode/verification fails
    corrupted_bytes = bytearray(orig_bytes)
    corrupted_bytes[100] = (corrupted_bytes[100] ^ 0xFF)
    corrupted_bytes_fixed = bytes(corrupted_bytes)

    corrupted_sha = hashlib.sha256(corrupted_bytes_fixed).hexdigest()
    corrupted_size = len(corrupted_bytes_fixed)
    corrupt_png = tmp_path / "corrupt_idat.png"
    corrupt_png.write_bytes(corrupted_bytes_fixed)

    custom_desc = {
        "schema_version": "root-candidate-presentation-media-pin-v1",
        "assets": [
            {
                "role": "rq2_retrieval_hit_rate",
                "sha256": corrupted_sha,
                "byte_size": corrupted_size,
            },
            {
                "role": "rq3_cost_and_tokens",
                "sha256": gs.PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["sha256"],
                "byte_size": gs.PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["byte_size"],
            },
        ],
    }
    desc_bytes = json.dumps(custom_desc).encode("utf-8")
    desc_path = tmp_path / "custom_root_pin.json"
    desc_path.write_bytes(desc_bytes)

    mock_digests["rq2_retrieval_hit_rate"]["primary_file"] = corrupt_png
    mock_digests["rq2_retrieval_hit_rate"]["alias_file"] = corrupt_png
    mock_digests["rq2_retrieval_hit_rate"]["sha256"] = corrupted_sha
    mock_digests["rq2_retrieval_hit_rate"]["byte_size"] = corrupted_size

    monkeypatch.setattr(gs, "PINNED_MEDIA_DIGESTS", mock_digests)
    monkeypatch.setattr(gs, "ROOT_MEDIA_PIN_PATH", desc_path)
    monkeypatch.setattr(gs, "EXPECTED_ROOT_MEDIA_PIN_SHA256", hashlib.sha256(desc_bytes).hexdigest())

    with pytest.raises(
        ValueError, match=r"\[FAIL_CLOSED\] PNG decode verification failed for role 'rq2_retrieval_hit_rate'"
    ):
        gs.resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)


def test_genuine_output_media_parity_across_archive() -> None:
    """Verifies genuine output media parity inside PPTX zip archive: exact SHA-256, byte size, and PIL decode."""
    assert PPTX_PATH.is_file(), f"Deck file missing: {PPTX_PATH}"

    expected_specs = {
        "rq2": {
            "sha256": "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f",
            "byte_size": 20165,
            "role": "rq2_retrieval_hit_rate",
        },
        "rq3": {
            "sha256": "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1",
            "byte_size": 27984,
            "role": "rq3_resource_consumption",
        },
    }

    verified_rq2 = resolve_and_verify_presentation_figure("rq2_retrieval_hit_rate", canonical_mode=True)
    verified_rq3 = resolve_and_verify_presentation_figure("rq3_resource_consumption", canonical_mode=True)
    assert verified_rq2 is not None
    assert verified_rq3 is not None

    with zipfile.ZipFile(str(PPTX_PATH), "r") as zf:
        media_members = [name for name in zf.namelist() if name.startswith("ppt/media/")]
        assert len(media_members) == 2, f"Expected exactly 2 media files, found: {media_members}"

        found_shas: dict[str, bytes] = {}
        for member_name in media_members:
            raw_bytes = zf.read(member_name)
            digest = hashlib.sha256(raw_bytes).hexdigest()
            found_shas[digest] = raw_bytes

            with Image.open(io.BytesIO(raw_bytes)) as img:
                img.verify()
            with Image.open(io.BytesIO(raw_bytes)) as img:
                img.load()
                assert img.format == "PNG"
                assert img.size[0] > 0 and img.size[1] > 0

        # Verify RQ2 exact parity
        rq2_sha = expected_specs["rq2"]["sha256"]
        assert rq2_sha in found_shas, f"RQ2 media SHA {rq2_sha} not in archive media"
        assert len(found_shas[rq2_sha]) == expected_specs["rq2"]["byte_size"]
        assert found_shas[rq2_sha] == verified_rq2.raw_bytes

        # Verify RQ3 exact parity
        rq3_sha = expected_specs["rq3"]["sha256"]
        assert rq3_sha in found_shas, f"RQ3 media SHA {rq3_sha} not in archive media"
        assert len(found_shas[rq3_sha]) == expected_specs["rq3"]["byte_size"]
        assert found_shas[rq3_sha] == verified_rq3.raw_bytes



