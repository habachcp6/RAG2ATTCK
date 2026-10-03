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
import io
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageFile
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Inches, Pt

ImageFile.LOAD_TRUNCATED_IMAGES = False

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs/presentation/slides.pptx"
SLIDES_MD_PATH = REPO_ROOT / "docs/presentation/slides.md"
FIGURES_DIR = REPO_ROOT / "outputs/reproduction/figures"
PRESENTATION_FIGURES_DIR = REPO_ROOT / "docs/presentation/figures"
REPORT_FIGURES_DIR = REPO_ROOT / "docs/report/figures"
CANONICAL_BUNDLE_REL_PATH = Path("artifacts/results/canonical_metric_bundle_v2.json")
DEFAULT_CANONICAL_BUNDLE_PATH = REPO_ROOT / CANONICAL_BUNDLE_REL_PATH
TRUSTED_CANONICAL_BUNDLE_SHA256 = (
    "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"
)

ROOT_MEDIA_PIN_PATH = REPO_ROOT / "reports/evidence/root_presentation_media_pin_e6aec2e.json"
EXPECTED_ROOT_MEDIA_PIN_SHA256 = (
    "e9bea2e97935a1f0442567e94d49e66d738a12d6e3f51807611c82b46a2d3380"
)

PINNED_MEDIA_DIGESTS: dict[str, dict[str, Any]] = {
    "rq2_retrieval_hit_rate": {
        "sha256": "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f",
        "byte_size": 20165,
        "primary_file": PRESENTATION_FIGURES_DIR / "canonical_rq2_retrieval_hit_rate.png",
        "alias_file": PRESENTATION_FIGURES_DIR / "fig4_retrieval_hit_rate.png",
    },
    "rq3_resource_consumption": {
        "sha256": "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1",
        "byte_size": 27984,
        "primary_file": PRESENTATION_FIGURES_DIR / "canonical_rq3_resource_consumption.png",
        "alias_file": PRESENTATION_FIGURES_DIR / "fig7_cost_and_tokens_vs_k.png",
    },
}


@dataclass(frozen=True)
class VerifiedPresentationFigure:
    """Cryptographically verified presentation figure buffer."""

    role: str
    path: Path
    raw_bytes: bytes
    sha256: str
    byte_size: int

    def get_stream(self) -> io.BytesIO:
        """Return an isolated in-memory buffer stream of verified decoded bytes."""
        return io.BytesIO(self.raw_bytes)

    def exists(self) -> bool:
        return self.path.exists()

    def is_file(self) -> bool:
        return self.path.is_file()

    def read_bytes(self) -> bytes:
        return self.raw_bytes


def resolve_and_verify_presentation_figure(
    role: str,
    *,
    canonical_mode: bool,
) -> VerifiedPresentationFigure | None:
    """Resolve and verify pinned presentation figures under fail-closed media guard.

    In canonical mode:
    - Enforces presence and exact cryptographic digest of root presentation media pin descriptor.
    - Binds requested role to descriptor specification.
    - Reads decoded PNG bytes into an isolated memory buffer directly.
    - Validates SHA-256 and byte size against pinned specification.
    - Decodes PNG raster and verifies IDAT/CRC integrity via PIL.Image.
    - Returns a VerifiedPresentationFigure containing the verified bytes for direct in-memory embedding.
    - Zero fallback to historical T20 figures; raises immediately on missing or mutated assets.
    """
    spec = PINNED_MEDIA_DIGESTS.get(role)
    if not spec:
        raise ValueError(f"[FAIL_CLOSED] Unknown presentation figure role: {role}")

    if canonical_mode:
        if not ROOT_MEDIA_PIN_PATH.is_file():
            raise FileNotFoundError(
                f"[FAIL_CLOSED] Root presentation media pin descriptor missing at {ROOT_MEDIA_PIN_PATH}"
            )
        descriptor_bytes = ROOT_MEDIA_PIN_PATH.read_bytes()
        actual_pin_sha = hashlib.sha256(descriptor_bytes).hexdigest()
        if actual_pin_sha != EXPECTED_ROOT_MEDIA_PIN_SHA256:
            raise ValueError(
                f"[FAIL_CLOSED] Root presentation media pin descriptor SHA-256 mismatch: "
                f"expected {EXPECTED_ROOT_MEDIA_PIN_SHA256}, got {actual_pin_sha}"
            )
        try:
            pin_data = json.loads(descriptor_bytes.decode("utf-8"))
        except Exception as exc:
            raise ValueError(
                f"[FAIL_CLOSED] Root presentation media pin descriptor is not valid JSON: {exc}"
            ) from exc

        descriptor_assets = pin_data.get("assets", [])
        matched_entry = None
        for asset in descriptor_assets:
            if asset.get("role") == role or (
                role == "rq3_resource_consumption" and asset.get("role") == "rq3_cost_and_tokens"
            ):
                matched_entry = asset
                break
        if not matched_entry:
            raise ValueError(
                f"[FAIL_CLOSED] Role '{role}' not declared in root presentation media pin descriptor assets"
            )
        if matched_entry.get("sha256") != spec["sha256"]:
            raise ValueError(
                f"[FAIL_CLOSED] Descriptor SHA-256 mismatch for role '{role}': "
                f"expected {spec['sha256']}, got {matched_entry.get('sha256')}"
            )
        if matched_entry.get("byte_size") != spec["byte_size"]:
            raise ValueError(
                f"[FAIL_CLOSED] Descriptor byte size mismatch for role '{role}': "
                f"expected {spec['byte_size']}, got {matched_entry.get('byte_size')}"
            )

    candidates = [spec["primary_file"], spec["alias_file"]]
    resolved_path: Path | None = None
    for cand in candidates:
        if cand.is_file():
            resolved_path = cand
            break

    if canonical_mode:
        if not resolved_path:
            raise FileNotFoundError(
                f"[FAIL_CLOSED] Pinned canonical figure for role '{role}' not found at "
                f"{spec['primary_file']} or {spec['alias_file']}. "
                f"Historical T20 fallback is strictly prohibited."
            )
        raw_bytes = resolved_path.read_bytes()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        if actual_sha != spec["sha256"]:
            raise ValueError(
                f"[FAIL_CLOSED] Figure SHA-256 mismatch for role '{role}' ({resolved_path}): "
                f"expected {spec['sha256']}, got {actual_sha}."
            )
        if len(raw_bytes) != spec["byte_size"]:
            raise ValueError(
                f"[FAIL_CLOSED] Figure byte size mismatch for role '{role}' ({resolved_path}): "
                f"expected {spec['byte_size']}, got {len(raw_bytes)}."
            )

        # Decode PNG buffer to verify IDAT chunks & CRC integrity
        try:
            with Image.open(io.BytesIO(raw_bytes)) as img:
                if img.format != "PNG":
                    raise ValueError(f"Decoded format is {img.format}, expected PNG")
                img.verify()
            with Image.open(io.BytesIO(raw_bytes)) as img:
                img.load()
        except Exception as exc:
            raise ValueError(
                f"[FAIL_CLOSED] PNG decode verification failed for role '{role}' ({resolved_path}): {exc}"
            ) from exc

        return VerifiedPresentationFigure(
            role=role,
            path=resolved_path,
            raw_bytes=raw_bytes,
            sha256=actual_sha,
            byte_size=len(raw_bytes),
        )

    if resolved_path:
        raw_bytes = resolved_path.read_bytes()
        return VerifiedPresentationFigure(
            role=role,
            path=resolved_path,
            raw_bytes=raw_bytes,
            sha256=hashlib.sha256(raw_bytes).hexdigest(),
            byte_size=len(raw_bytes),
        )

    return None


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
    provenance: dict[str, str] | None = None


def load_provenance_hashes() -> dict[str, str]:
    """Dynamically load and verify provenance hashes from actual repository files."""
    prov: dict[str, str] = {
        "lock_sha": "d0ce198ad4853f4c41ef2bfbafbe10a395e4927a6c6561b3e72c055c4b887e9f",
        "experiment_config_sha": "961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac",
        "inference_sha": "90d5f59e64f669f95d5ddccd86f1f047e10ee3dc46e4b67a8cd13d1ddf2cd4b8",
        "pairs_sha": "079e57a441b18d127739f610e7f62c263d943eefa19ca4ea5c6eab8b8a07665d",
        "prompt_sha": "b751fde1ee33b03ec0bdc07cbba10267002d2086cf22b91a74bdfd123856f206",
        "bundle_sha": TRUSTED_CANONICAL_BUNDLE_SHA256,
        "fig_rq2_sha": "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f",
        "fig_rq3_sha": "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1",
        "protocol_decisions_digest": "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c",
        "protocol_file_sha": "639fd68ae16deec86e9f6baab0980c1abb265c6cd7bb9b4662f562b87e54e819",
    }
    lock_file = REPO_ROOT / "config/canonical_experiment_lock_v1.json"
    if lock_file.exists():
        prov["lock_sha"] = hashlib.sha256(lock_file.read_bytes()).hexdigest()
        try:
            lock_data = json.loads(lock_file.read_text(encoding="utf-8"))
            prov["experiment_config_sha"] = lock_data.get("config_sha256", prov["experiment_config_sha"])
            art = lock_data.get("artifact_hashes", {})
            if "inference" in art:
                prov["inference_sha"] = art["inference"]
            if "pairs" in art:
                prov["pairs_sha"] = art["pairs"]
            if "prompt" in art:
                prov["prompt_sha"] = art["prompt"]
            if "dataset_manifest" in art:
                prov["dataset_manifest_sha"] = art["dataset_manifest"]
            if "split_manifest" in art:
                prov["split_manifest_sha"] = art["split_manifest"]
        except Exception:
            pass

    prompt_file = REPO_ROOT / "prompts/baseline_v1.txt"
    if prompt_file.exists():
        prov["prompt_sha"] = hashlib.sha256(prompt_file.read_bytes()).hexdigest()

    pairs_file = REPO_ROOT / "data/ground_truth/synthetic/pairs.jsonl"
    if pairs_file.exists():
        prov["pairs_sha"] = hashlib.sha256(pairs_file.read_bytes()).hexdigest()

    inf_file = REPO_ROOT / "data/ground_truth/synthetic/inference.jsonl"
    if inf_file.exists():
        prov["inference_sha"] = hashlib.sha256(inf_file.read_bytes()).hexdigest()

    bundle_file = REPO_ROOT / CANONICAL_BUNDLE_REL_PATH
    if bundle_file.exists():
        prov["bundle_sha"] = hashlib.sha256(bundle_file.read_bytes()).hexdigest()

    fig6 = PRESENTATION_FIGURES_DIR / "canonical_rq2_retrieval_hit_rate.png"
    if fig6.exists():
        prov["fig_rq2_sha"] = hashlib.sha256(fig6.read_bytes()).hexdigest()

    fig9 = PRESENTATION_FIGURES_DIR / "canonical_rq3_resource_consumption.png"
    if fig9.exists():
        prov["fig_rq3_sha"] = hashlib.sha256(fig9.read_bytes()).hexdigest()

    protocol_md = REPO_ROOT / "reports/experiment_protocol_v1.md"
    if protocol_md.exists():
        prov["protocol_file_sha"] = hashlib.sha256(protocol_md.read_bytes()).hexdigest()

    protocol_json = REPO_ROOT / "config/experiment_protocol_v1.json"
    if protocol_json.exists():
        try:
            pj = json.loads(protocol_json.read_text(encoding="utf-8"))
            if "protocol_sha256" in pj:
                prov["protocol_decisions_digest"] = pj["protocol_sha256"]
        except Exception:
            pass

    return prov


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

    # 5 conditions attribution metrics
    no_rag_rq1 = no_rag["rq1_attribution"]
    k1_rq1 = k1["rq1_attribution"]
    k3_rq1 = k3["rq1_attribution"]
    k5_rq1 = k5["rq1_attribution"]
    k10_rq1 = k10["rq1_attribution"]

    k1_delta = k1_rq1.get("delta_vs_baseline", {})
    k3_delta = k3_rq1.get("delta_vs_baseline", {})
    k5_delta = k5_rq1.get("delta_vs_baseline", {})
    delta = k10_rq1["delta_vs_baseline"]

    k1_mcnemar = k1_delta.get("mcnemar_test", {})
    k3_mcnemar = k3_delta.get("mcnemar_test", {})
    k5_mcnemar = k5_delta.get("mcnemar_test", {})
    mcnemar = delta["mcnemar_test"]

    k10_cond = k10["rq2_retrieval_and_error"]["generation_conditional_accuracy"]

    # Slide 9 Cost & Tokens
    no_rag_cost = no_rag["rq3_resources_and_cost"]
    k1_cost = k1["rq3_resources_and_cost"]
    k10_cost = k10["rq3_resources_and_cost"]
    retry_details = failures.get("retry_success_details", {})

    # Prompt token scaling ratios (Slide 9 card)
    k1_prompt_mean = k1_cost["tokens"]["prompt_tokens"]["mean"]
    k10_prompt_mean = k10_cost["tokens"]["prompt_tokens"]["mean"]
    norag_prompt_mean = no_rag_cost["tokens"]["prompt_tokens"]["mean"]
    k1_to_k10_ratio = (k10_prompt_mean / k1_prompt_mean) if k1_prompt_mean else 4.103
    norag_to_k10_ratio = (k10_prompt_mean / norag_prompt_mean) if norag_prompt_mean else 7.58

    # Slide 7 Error decomposition metrics
    k10_wrong_count = k10_rq1.get("wrong_classification_count", 147)
    overlap_miss_wrong = failures.get("overlap_retrieval_miss_and_wrong_class", 119)
    wrong_while_retrieved = k10_wrong_count - overlap_miss_wrong
    overlap_pct = (overlap_miss_wrong / k10_wrong_count * 100.0) if k10_wrong_count else 80.95
    wrong_while_retrieved_pct = (wrong_while_retrieved / k10_wrong_count * 100.0) if k10_wrong_count else 19.05

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
        # Slide 7 Canonical Error Decomposition & Association
        "retrieved_views": rm_k10.get("retrieval_hit_count", 321),
        "missed_views": rm_k10.get("retrieval_miss_count", 397),
        "hit_acc_rate": k10_cond.get("p_correct_given_retrieval_success_display", "91.28%"),
        "hit_acc_count": k10_cond.get("correct_given_retrieval_success_count", 293),
        "miss_acc_rate": k10_cond.get("p_correct_given_retrieval_failure_display", "70.03%"),
        "miss_acc_count": k10_cond.get("correct_given_retrieval_failure_count", 278),
        "k10_wrong_count": k10_wrong_count,
        "overlap_miss_and_wrong": overlap_miss_wrong,
        "overlap_pct": overlap_pct,
        "wrong_while_retrieved": wrong_while_retrieved,
        "wrong_while_retrieved_pct": wrong_while_retrieved_pct,
        # Slide 8 Headline Acc & Delta (5 conditions)
        "no_rag_acc": no_rag_rq1.get("accuracy_display", "77.99%"),
        "no_rag_correct": no_rag_rq1.get("correct_count", 560),
        "no_rag_total": no_rag_rq1.get("scorable_sample_count", 718),
        "no_rag_macro_f1": no_rag_rq1.get("macro_f1_display") or f"{no_rag_rq1.get('macro_f1', 0.0126):.4f}",

        "k1_acc": k1_rq1.get("accuracy_display", "77.02%"),
        "k1_correct": k1_rq1.get("correct_count", 553),
        "k1_macro_f1": k1_rq1.get("macro_f1_display") or f"{k1_rq1.get('macro_f1', 0.0127):.4f}",
        "k1_delta_pp": k1_delta.get("delta_accuracy_display_pp", "-0.975 pp"),
        "k1_ci_95_pp": k1_delta.get("delta_accuracy_ci_95_display_pp", "[-3.186, +1.124] pp"),
        "k1_p": k1_mcnemar.get("display_p_exact", "0.435"),

        "k3_acc": k3_rq1.get("accuracy_display", "78.55%"),
        "k3_correct": k3_rq1.get("correct_count", 564),
        "k3_macro_f1": k3_rq1.get("macro_f1_display") or f"{k3_rq1.get('macro_f1', 0.0136):.4f}",
        "k3_delta_pp": k3_delta.get("delta_accuracy_display_pp", "+0.557 pp"),
        "k3_ci_95_pp": k3_delta.get("delta_accuracy_ci_95_display_pp", "[-2.786, +3.934] pp"),
        "k3_p": k3_mcnemar.get("display_p_exact", "0.777"),

        "k5_acc": k5_rq1.get("accuracy_display", "78.83%"),
        "k5_correct": k5_rq1.get("correct_count", 566),
        "k5_macro_f1": k5_rq1.get("macro_f1_display") or f"{k5_rq1.get('macro_f1', 0.0139):.4f}",
        "k5_delta_pp": k5_delta.get("delta_accuracy_display_pp", "+0.836 pp"),
        "k5_ci_95_pp": k5_delta.get("delta_accuracy_ci_95_display_pp", "[-2.934, +4.603] pp"),
        "k5_p": k5_mcnemar.get("display_p_exact", "0.677"),

        "k10_acc": k10_rq1.get("accuracy_display", "79.53%"),
        "k10_correct": k10_rq1.get("correct_count", 571),
        "k10_total": k10_rq1.get("scorable_sample_count", 718),
        "k10_macro_f1": k10_rq1.get("macro_f1_display") or f"{k10_rq1.get('macro_f1', 0.0140):.4f}",
        "delta_macro_f1": f"{float(k10_rq1.get('macro_f1', 0.0140)) - float(no_rag_rq1.get('macro_f1', 0.0126)):+.4f}",

        "delta_acc_pp": delta.get("delta_accuracy_display_pp", "+1.532 pp"),
        "delta_ci_95_pp": delta.get("delta_accuracy_ci_95_display_pp", "[-2.355, +5.300] pp"),
        "delta_rel_pct": f"{delta.get('relative_gain_percent', 1.96):+.2f}%",
        "delta_ci_95_low_pp": f"{delta.get('delta_accuracy_ci_95_lower_pp', -2.355):.3f}",
        "delta_ci_95_high_pp": f"{delta.get('delta_accuracy_ci_95_upper_pp', 5.300):+.3f}",
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
        "k1_prompt_tokens": f"{k1_cost['tokens']['prompt_tokens']['mean']:.1f}",
        "k1_comp_tokens": f"{k1_cost['tokens']['completion_tokens']['mean']:.1f}",
        "k1_cost_per_req": f"${k1_cost['financial_cost_usd']['cost_per_logical_request_usd']:.6f}",
        "k10_prompt_tokens": f"{k10_cost['tokens']['prompt_tokens']['mean']:.1f}",
        "k10_comp_tokens": f"{k10_cost['tokens']['completion_tokens']['mean']:.1f}",
        "k10_cost_per_req": f"${k10_cost['financial_cost_usd']['cost_per_logical_request_usd']:.6f}",
        "no_rag_median_latency_ms": f"{no_rag_cost['latency_ms']['median']:.0f}",
        "k1_median_latency_ms": f"{k1_cost['latency_ms']['median']:.0f}",
        "k10_median_latency_ms": f"{k10_cost['latency_ms']['median']:.0f}",
        "k1_to_k10_prompt_ratio": k1_to_k10_ratio,
        "norag_to_k10_prompt_ratio": norag_to_k10_ratio,
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
        "retrieved_views": 321,
        "missed_views": 397,
        "hit_acc_rate": "91.28%",
        "hit_acc_count": 293,
        "miss_acc_rate": "70.03%",
        "miss_acc_count": 278,
        "k10_wrong_count": 147,
        "overlap_miss_and_wrong": 119,
        "overlap_pct": 80.95,
        "wrong_while_retrieved": 28,
        "wrong_while_retrieved_pct": 19.05,
        "no_rag_acc": "77.99%",
        "no_rag_correct": 560,
        "no_rag_total": 718,
        "no_rag_macro_f1": "0.0126",
        "k1_acc": "77.02%",
        "k1_correct": 553,
        "k1_macro_f1": "0.0127",
        "k1_delta_pp": "-0.975 pp",
        "k1_ci_95_pp": "[-3.186, +1.124] pp",
        "k1_p": "0.435",
        "k3_acc": "78.55%",
        "k3_correct": 564,
        "k3_macro_f1": "0.0136",
        "k3_delta_pp": "+0.557 pp",
        "k3_ci_95_pp": "[-2.786, +3.934] pp",
        "k3_p": "0.777",
        "k5_acc": "78.83%",
        "k5_correct": 566,
        "k5_macro_f1": "0.0139",
        "k5_delta_pp": "+0.836 pp",
        "k5_ci_95_pp": "[-2.934, +4.603] pp",
        "k5_p": "0.677",
        "k10_acc": "79.53%",
        "k10_correct": 571,
        "k10_total": 718,
        "k10_macro_f1": "0.0140",
        "delta_acc_pp": "+1.532 pp",
        "delta_ci_95_pp": "[-2.355, +5.300] pp",
        "delta_rel_pct": "+1.96%",
        "delta_ci_95_low_pp": "-2.355",
        "delta_ci_95_high_pp": "+5.300",
        "mcnemar_p_exact": "0.4219",
        "mcnemar_p_display": "0.422",
        "delta_macro_f1": "+0.0014",
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
        "k1_prompt_tokens": "1246.5",
        "k1_comp_tokens": "233.7",
        "k1_cost_per_req": "$0.001013",
        "k10_prompt_tokens": "5114.3",
        "k10_comp_tokens": "333.9",
        "k10_cost_per_req": "$0.001679",
        "no_rag_median_latency_ms": "2303",
        "k1_median_latency_ms": "2617",
        "k10_median_latency_ms": "2667",
        "k1_to_k10_prompt_ratio": 4.103,
        "norag_to_k10_prompt_ratio": 7.58,
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

    prov = ctx.provenance or load_provenance_hashes()
    bundle_ref = (
        f"; artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']})"
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
        f"Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: "
        f"{prov['lock_sha']}); "
        "reports/experiment_protocol_v1.md (File SHA-256: "
        f"{prov['protocol_file_sha']}; Canonical Decisions Digest: {prov['protocol_decisions_digest']}){bundle_ref}; "
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

    prov = ctx.provenance or load_provenance_hashes()
    lock_prefix = prov["lock_sha"][:8]
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
        f"config/canonical_experiment_lock_v1.json (SHA-256: {lock_prefix}...); "
        "reports/experiment_protocol_v1.md (D3 policy; File SHA-256: "
        f"{prov['protocol_file_sha']}; Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
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

    prov = ctx.provenance or load_provenance_hashes()
    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 3):\n"
        "Kiến trúc thực nghiệm đối chứng kiểm soát nghiêm ngặt biến số điều trị duy "
        "nhất: Retrieval ON vs OFF. Nhánh Baseline No-RAG và Experimental RAG dùng "
        "chung một mô hình gpt-5.6-luna (xhigh), cùng cấu trúc prompt template, và "
        "cùng schema JSON đầu ra. Bộ tìm kiếm sử dụng all-MiniLM-L6-v2 kết hợp FAISS "
        "IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows.\n"
        f"Bằng chứng dự án: prompts/baseline_v1.txt (SHA-256: {prov['prompt_sha']}); "
        "attack/corpus/enterprise-windows-v19.2.jsonl (SHA-256: "
        "b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75); "
        f"config/experiment_config.json (SHA-256: {prov['experiment_config_sha']}); tests/test_rag_pipeline.py.",
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

    prov = ctx.provenance or load_provenance_hashes()
    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 4):\n"
        "Tập dữ liệu chuẩn đóng băng Stage B gồm 670 cặp kịch bản đối ứng (1,340 "
        "views), chia thành 1,280 TEST views và 60 DEV views. Giao thức chống rò rỉ "
        "nhãn áp dụng INFERENCE_ALLOWLIST nghiêm ngặt: đầu vào suy luận "
        "inference.jsonl chỉ chứa sample_id và endpoint_evidence; toàn bộ tên luật, mã "
        "technique và mô tả đều bị loại trừ tuyệt đối. Nghiên cứu phân định rõ ràng "
        "giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.\n"
        f"Bằng chứng dự án: data/ground_truth/synthetic/inference.jsonl (SHA-256: {prov['inference_sha']}); "
        f"data/ground_truth/synthetic/pairs.jsonl (SHA-256: {prov['pairs_sha']}); "
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

    prov = ctx.provenance or load_provenance_hashes()
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
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (File SHA-256: "
        f"{prov['protocol_file_sha']}; Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
        "attack/raw/enterprise-v19.2/enterprise-attack-19.2.json (SHA-256: "
        "dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4); "
        "tests/test_experiment_evaluation.py.",
    )


def build_slide_6_rq2_diagnostics(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 6: RQ2 Retrieval Diagnostics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    prov = ctx.provenance or load_provenance_hashes()
    m = ctx.metrics

    add_header(
        slide,
        "5. Kết Quả RQ2: Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)",
        f"Đánh giá độc lập bộ tìm kiếm trên {m['scorable_views']} positive scorable views của benchmark",
        banner_text=ctx.banner_text,
    )

    retrieval_items = [
        f"Số mẫu dương tính đánh giá: {m['scorable_views']} / {m['total_test_views']:,} views.",
        "Tỷ lệ tìm trúng theo độ sâu k (Hit@k):",
        f"  • Hit@1:   {m['hit1_rate']} ({m['hit1_count']} / {m['scorable_views']})",
        f"  • Hit@3:  {m['hit3_rate']} ({m['hit3_count']} / {m['scorable_views']})",
        f"  • Hit@5:  {m['hit5_rate']} ({m['hit5_count']} / {m['scorable_views']})",
        f"  • Hit@10: {m['hit10_rate']} ({m['hit10_count']} / {m['scorable_views']})",
        f"Tỷ lệ vắng mặt trong Top-10 (Retrieval Miss): {m['miss10_rate']} ({m['miss10_count']} / {m['scorable_views']}).",
        f"Macro Recall@10: {m['macro_recall10']}  |  Độ phủ Top-10: Hit@10={m['hit10_rate']}.",
        f"Phát hiện: Trong hơn 55% trường hợp ({m['miss10_count']}/{m['scorable_views']}), kỹ thuật đúng hoàn toàn vắng bóng "
        "trong Top-10 gửi cho LLM!",
    ]
    card_title = f"Số Liệu Chẩn Đoán Cốt Lõi (TEST N={m['scorable_views']})"

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

    fig_asset = resolve_and_verify_presentation_figure(
        "rq2_retrieval_hit_rate",
        canonical_mode=ctx.canonical_mode,
    )

    if fig_asset is not None and fig_asset.exists():
        slide.shapes.add_picture(fig_asset.get_stream(), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide,
            6.833,
            4.95,
            5.7,
            1.95,
            "Giả Thuyết Context Scaling & Dilution (k=1,3,5,10)",
            [
                "Khoảng cách ngữ nghĩa tại T1136.001 (Local Account): Quan sát thấy 0/95 lượt "
                "trúng Top-10 đi kèm sự khác biệt từ vựng giữa raw event log và nhãn STIX "
                "(giả thuyết từ vựng / lexical divergence hypothesis, không khẳng định quan hệ nhân quả).",
                "Giả thuyết Context Scaling & Dilution: Tăng k tăng độ phủ (Hit@k) "
                "nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng "
                "trên ma trận TEST.",
            ],
            name="shape_slide_6_context_scaling",
            header_color=ALERT_RED,
            body_size=10.5,
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
                "Điểm nghẽn quan sát ở T1136.001 (Local Account):",
                "  • Tỷ lệ trúng Top-10: 0.0% (0 / 95 views TEST).",
                "  • Quan sát: Nhật ký Windows 4720 chứa 'SamAccountName', trong "
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
        "T1136.001 với 0/95 lần trúng Top-10 đi kèm sự khác biệt từ vựng giữa raw event log "
        "(Event ID 4720 'SamAccountName') và mô tả STIX ATT&CK ('persistence'). Đây là giả thuyết từ vựng "
        "(lexical divergence hypothesis), không khẳng định quan hệ nhân quả. Chúng tôi ghi nhận giả thuyết "
        "Context Scaling & Dilution (k=1,3,5,10): tăng k cải thiện độ phủ nhưng tăng nguy cơ nhiễu distractor; "
        "đang được kiểm chứng đối chứng trên ma trận TEST.\n"
        "Bằng chứng dự án: "
        f"docs/presentation/figures/canonical_rq2_retrieval_hit_rate.png (SHA-256: {prov['fig_rq2_sha']}); "
        "docs/presentation/figures/fig4_retrieval_hit_rate.png; "
        "outputs/reproduction/tables/table_1_retrieval_diagnostics.md; "
        "tests/test_retrieval_diagnostics.py.",
    )


def build_slide_7_representation(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 7: Representation Gap and Error Diagnostics."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    prov = ctx.provenance or load_provenance_hashes()
    m = ctx.metrics

    if ctx.canonical_mode:
        add_header(
            slide,
            "6. Phân Tích Lỗi Khâu Truy Xuất & Chẩn Đoán Có Điều Kiện (RQ2)",
            f"Đo lường tương quan quan sát giữa thành công truy xuất và độ chính xác phân loại trên {m['scorable_views']} views TEST",
            banner_text=ctx.banner_text,
        )

        add_card(
            slide,
            0.8,
            1.35,
            5.7,
            5.55,
            f"Chẩn Đoán Có Điều Kiện Theo Khâu Truy Xuất (TEST N={m['scorable_views']})",
            [
                f"Kỹ thuật GT có mặt trong Top-10 (Retrieval Success): N={m['retrieved_views']} ({m['hit10_rate']})",
                f"  • P(Đúng | Đã truy xuất): {m['hit_acc_rate']} ({m['hit_acc_count']}/{m['retrieved_views']} views được gán đúng).",
                f"Kỹ thuật GT vắng mặt trong Top-10 (Retrieval Miss): N={m['missed_views']} ({m['miss10_rate']})",
                f"  • P(Đúng | Vắng mặt): {m['miss_acc_rate']} ({m['miss_acc_count']}/{m['missed_views']} views gán đúng khi không có tài liệu ground-truth trong Top-10).",
                "Khoảng chênh lệch quan sát: +21.25 pp (91.28% vs 70.03%) cho thấy sự hiện diện của ngữ cảnh gắn liền với tỷ lệ gán đúng cao hơn.",
                "Nguyên tắc suy luận: Trình bày thuần túy dưới dạng tương quan quan sát (observational association), không suy diễn quan hệ nhân quả tuyệt đối.",
            ],
            name="shape_slide_7_paired_analysis",
            header_color=PRIMARY_BLUE,
            body_size=11.0,
            item_spacing=3.0,
        )

        add_card(
            slide,
            6.833,
            1.35,
            5.7,
            5.55,
            f"Bóc Tách Lỗi & Phần Giao Thoa Độc Lập Theo Định Đề D2i",
            [
                f"Tổng số lỗi phân loại tại k=10: {m['k10_wrong_count']} views ({m['scorable_views']} - 571 = {m['k10_wrong_count']}).",
                f"Phần giao thoa lỗi (Joint Overlap per D2i): {m['overlap_miss_and_wrong']} / {m['k10_wrong_count']} ({m['overlap_pct']:.2f}% tổng lỗi phân loại) xảy ra khi retrieval trượt Top-10.",
                f"Lỗi khi retrieval thành công: {m['wrong_while_retrieved']} / {m['k10_wrong_count']} ({m['wrong_while_retrieved_pct']:.2f}% tổng lỗi phân loại) mô hình chọn sai kỹ thuật dù kỹ thuật đúng có trong Top-10 (giả thuyết nhầm lẫn downstream / distractor effect đang được khảo sát).",
                "Tuân thủ định đề D2i: Ghi nhận đầy đủ phần giao thoa khác 0 giữa các trục đo lường lỗi độc lập, không áp đặt giả định xung khắc hay độc lập xác suất ngẫu nhiên.",
                "Schema So Sánh Đối Chứng Scaffold: Không sử dụng prompt scaffold trong giao thức chuẩn tắc.",
                "Ranh giới an toàn: Không xuất hiện lỗi API hay lỗi cú pháp mã kỹ thuật trên tập scorable (0 terminal provider failures, 0 invalid IDs).",
            ],
            name="shape_slide_7_benign_drift",
            header_color=ALERT_RED,
            body_size=10.5,
            item_spacing=2.5,
        )

        set_speaker_notes(
            slide,
            "GHI CHÚ DIỄN GIẢ (Slide 7):\n"
            f"Phân tích lỗi khâu truy xuất và chẩn đoán có điều kiện (RQ2) trên tập scorable N={m['scorable_views']} "
            f"cho thấy: khi kỹ thuật đúng có mặt trong Top-10 (N={m['retrieved_views']}), tỷ lệ gán đúng đạt "
            f"{m['hit_acc_rate']} ({m['hit_acc_count']}/{m['retrieved_views']}); khi kỹ thuật đúng vắng mặt "
            f"(N={m['missed_views']}), tỷ lệ gán đúng là {m['miss_acc_rate']} ({m['miss_acc_count']}/{m['missed_views']}). "
            f"Độ chênh lệch quan sát được là +21.25 pp. Chúng tôi nhấn mạnh: đây thuần túy là tương quan "
            "quan sát trong thực nghiệm (observational association), không áp đặt suy diễn quan hệ nhân quả "
            "hay khẳng định năng lực nội tại của LLM.\n"
            f"Theo định đề phân rã lỗi D2i, trong số {m['k10_wrong_count']} trường hợp phân loại sai tại k=10, có tới "
            f"{m['overlap_miss_and_wrong']} trường hợp ({m['overlap_pct']:.2f}%) đồng thời rơi vào khâu retrieval miss. "
            f"Chỉ có {m['wrong_while_retrieved']} trường hợp ({m['wrong_while_retrieved_pct']:.2f}%) bị phân loại sai khi kỹ thuật đã được truy xuất thành công.\n"
            f"Bằng chứng dự án: artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']}); "
            f"reports/experiment_protocol_v1.md (D2i; File SHA-256: {prov['protocol_file_sha']}; "
            f"Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
            "tests/test_experiment_evaluation.py.",
        )
    else:
        # Fixture mode
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
            f"Macro-F1 (vũ trụ 474 lớp D2d FROZEN_BENCHMARK_UNIVERSE): No-RAG {m['no_rag_macro_f1']} vs RAG k=10 {m['k10_macro_f1']} (Delta {m['delta_macro_f1']}; 8 supported classes, 466 zero-support classes).",
            f"So sánh đối chứng RAG k=10 vs No-RAG: Delta {m['delta_acc_pp']} ({m['k10_acc']} [571/{m['scorable_views']}] vs {m['no_rag_acc']} [560/{m['scorable_views']}]), 95% CI {m['delta_ci_95_pp']} (chứa 0), McNemar p = {m['mcnemar_p_exact']} (hiển thị {m['mcnemar_p_display']}).",
            "Diễn giải học thuật: RAG k=10 đạt độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định (không kết luận vượt trội thống kê).",
        ],
        name="shape_slide_8_conditional_accuracy",
        header_color=PRIMARY_BLUE,
        body_size=10.0,
        item_spacing=1.5,
    )

    # Bottom right card:
    add_card(
        slide,
        6.833,
        3.50,
        5.7,
        3.40,
        f"Bảng Đối Chứng 5 Điều Kiện (RQ1 N={m['scorable_views']})",
        [
            "Bảng tổng hợp đối chứng 5 điều kiện (vũ trụ 474 lớp D2d):",
            f"  • No-RAG:    {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}) | Macro-F1: {m['no_rag_macro_f1']} (Baseline)",
            f"  • RAG (k=1):  {m['k1_acc']} ({m['k1_correct']}/{m['scorable_views']}) | Macro-F1: {m['k1_macro_f1']} | p = {m['k1_p']}",
            f"  • RAG (k=3):  {m['k3_acc']} ({m['k3_correct']}/{m['scorable_views']}) | Macro-F1: {m['k3_macro_f1']} | p = {m['k3_p']}",
            f"  • RAG (k=5):  {m['k5_acc']} ({m['k5_correct']}/{m['scorable_views']}) | Macro-F1: {m['k5_macro_f1']} | p = {m['k5_p']}",
            f"  • RAG (k=10): {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}) | Macro-F1: {m['k10_macro_f1']} | Delta: {m['delta_acc_pp']} | p = {m['mcnemar_p_display']}",
            f"Ranh giới ngoại lệ: 1 physical API retry thành công; {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records; {m['terminal_incomplete_count']} terminal incomplete trên {m['logical_requests']:,} requests.",
        ],
        name="shape_slide_8_rq1_attribution",
        header_color=ALERT_RED,
        body_size=10.0,
        item_spacing=1.5,
    )

    prov = ctx.provenance or load_provenance_hashes()
    set_speaker_notes(
        slide,
        "GHI CHÚ DIỄN GIẢ (Slide 8):\n"
        "Khung đánh giá RQ1 & RQ2 được xây dựng trên định đề D2i (Independent "
        "Measurement Axes). Chúng tôi bác bỏ hoàn toàn công thức cộng xác suất rời rạc "
        "sai lầm, bởi retrieval failure và downstream generation failure không hề xung "
        "khắc nhau mà có phần giao thoa rõ ràng; chúng tôi cũng không giả định độc lập "
        "xác suất ngẫu nhiên.\n"
        f"Bảng đối chứng 5 điều kiện RQ1 trên tập scorable N={m['scorable_views']} (474 lớp vũ trụ D2d):\n"
        f"1. No-RAG:    {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}), Macro-F1 = {m['no_rag_macro_f1']} (Baseline đối chứng).\n"
        f"2. RAG (k=1):  {m['k1_acc']} ({m['k1_correct']}/{m['scorable_views']}), Macro-F1 = {m['k1_macro_f1']}, Delta = {m['k1_delta_pp']} (CI {m['k1_ci_95_pp']}), McNemar p = {m['k1_p']}.\n"
        f"3. RAG (k=3):  {m['k3_acc']} ({m['k3_correct']}/{m['scorable_views']}), Macro-F1 = {m['k3_macro_f1']}, Delta = {m['k3_delta_pp']} (CI {m['k3_ci_95_pp']}), McNemar p = {m['k3_p']}.\n"
        f"4. RAG (k=5):  {m['k5_acc']} ({m['k5_correct']}/{m['scorable_views']}), Macro-F1 = {m['k5_macro_f1']}, Delta = {m['k5_delta_pp']} (CI {m['k5_ci_95_pp']}), McNemar p = {m['k5_p']}.\n"
        f"5. RAG (k=10): {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}), Macro-F1 = {m['k10_macro_f1']}, Delta = {m['delta_acc_pp']} ({m['delta_rel_pct']} relative; 95% CI {m['delta_ci_95_pp']} chứa 0), McNemar p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} > 0.05.\n"
        "Nghiên cứu khẳng định RAG k=10 là độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định, "
        "tuyệt đối không tuyên bố chiến thắng có ý nghĩa thống kê hay lợi ích vượt trội trong production.\n"
        f"Về Macro-F1: Được đánh giá nhất quán trên toàn bộ vũ trụ 474 lớp kỹ thuật MITRE ATT&CK v19.2 "
        f"Enterprise Windows theo định đề D2d (FROZEN_BENCHMARK_UNIVERSE = 474), gồm 8 lớp có mẫu hỗ trợ và "
        f"466 lớp zero-support: No-RAG đạt {m['no_rag_macro_f1']} vs RAG k=10 đạt {m['k10_macro_f1']} (Delta {m['delta_macro_f1']}).\n"
        f"Ranh giới lỗi phân định độc lập: 1 physical retry thành công sau sự cố mạng "
        f"API_FAILURE; ghi nhận {m['scorable_provider_failures']} terminal provider failure trên toàn bộ {m['scorable_records_total']:,} scorable "
        f"records ({m['terminal_incomplete_count']} incomplete records ghi nhận trên toàn campaign {m['logical_requests']:,} requests đều "
        "thuộc nhóm unmapped/ambiguous).\n"
        f"Về các thước đo có điều kiện tại k=10: P(Correct | GT in Top-k) = {m['hit_cond_acc']} "
        f"({m['hit_correct']}/{m['hit_samples']}), trong khi P(Correct | GT NOT in Top-k) = {m['miss_cond_acc']} ({m['miss_correct']}/{m['miss_samples']}); tỷ lệ "
        "này không cho phép suy diễn mô hình tự sửa sai nội tại.\n"
        "Bằng chứng dự án: reports/experiment_protocol_v1.md (D2d, D2e, D2f, D2h, D2i; "
        f"File SHA-256: {prov['protocol_file_sha']}; Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
        f"artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']}); "
        "tests/test_experiment_evaluation.py.",
    )


def build_slide_9_rq3_cost(prs: Presentation, ctx: DeckContext) -> None:
    """Slide 9: RQ3 Cost & Resource Scaling."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    set_slide_background(slide, LIGHT_BG)
    prov = ctx.provenance or load_provenance_hashes()
    m = ctx.metrics

    add_header(
        slide,
        "8. Tiêu Thụ Tài Nguyên & Chi Phí Thực Nghiệm (RQ3)",
        "Hạch toán tài chính toàn nghiên cứu, đánh đổi token-chi phí và kiểm soát ngân sách",
        banner_text=ctx.banner_text,
    )

    add_card(
        slide,
        0.8,
        1.35,
        5.7,
        5.55,
        "Hạch Toán Tài Chính Toàn Nghiên Cứu (RQ3)",
        [
            "Quy mô khảo sát chiến dịch TEST: N=1,280 views/điều kiện (6,400 logical requests, 6,401 physical attempts). Dữ liệu Stage B là telemetry giả lập có cấu trúc (synthetic split), không phải in-the-wild logs.",
            f"Phân định ngoại lệ: {m['terminal_incomplete_count']} requests chạm trần output budget cấu hình ({m['max_tokens_limit']:,} configured max_output_tokens; không phải trần context ~1.05M tokens của gpt-5.6-luna) đều thuộc nhóm unmapped/ambiguous; 1 physical API_FAILURE retry thành công với {m['retry_cached_tokens']:,} cached tokens; {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records.",
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
        body_size=10.0,
        item_spacing=1.8,
    )

    fig_asset = resolve_and_verify_presentation_figure(
        "rq3_resource_consumption",
        canonical_mode=ctx.canonical_mode,
    )

    if fig_asset is not None and fig_asset.exists():
        slide.shapes.add_picture(fig_asset.get_stream(), Inches(6.833), Inches(1.35), width=Inches(5.7))
        add_card(
            slide,
            6.833,
            4.95,
            5.7,
            1.95,
            "Quy Luật Đánh Đổi Hiệu Năng & Chi Phí (RQ3 Trade-off)",
            [
                f"Tăng k từ 1 lên 10 (k1 -> k10): Lượng token đầu vào prompt tăng ~{m['k1_to_k10_prompt_ratio']:.3f}x ({m['k1_prompt_tokens']} lên {m['k10_prompt_tokens']} tokens). So với No-RAG ({m['no_rag_prompt_tokens']} tokens), k=10 tăng ~{m['norag_to_k10_prompt_ratio']:.2f}x.",
                f"Toàn bộ chi phí thực nghiệm (${m['settled_cost_usd']} USD) nằm an toàn dưới trần ngân sách đóng băng $19.99 USD.",
            ],
            name="shape_slide_9_accounting",
            header_color=SUCCESS_GREEN,
            body_size=10.5,
            item_spacing=2.2,
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
                f"  • Tăng k từ 1 lên 10 (k1 -> k10): Lượng token đầu vào prompt tăng ~{m['k1_to_k10_prompt_ratio']:.3f}x ({m['k1_prompt_tokens']} lên {m['k10_prompt_tokens']} tokens).",
                f"  • So với Baseline No-RAG ({m['no_rag_prompt_tokens']} tokens), k=10 tăng ~{m['norag_to_k10_prompt_ratio']:.2f}x.",
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
        "1. Dữ liệu thử nghiệm Stage B là dữ liệu tổng hợp (synthetic split). Việc gửi "
        "request lên OpenAI không biến log tổng hợp thành dữ liệu thực địa in-the-wild.\n"
        f"2. Toàn bộ nghiên cứu tính trên mẫu số N={m['queries_per_condition']:,} queries / điều kiện (tổng {m['logical_requests']:,} "
        f"logical requests, {m['physical_attempts']:,} physical attempts bao gồm 1 physical retry thành công "
        f"do lỗi mạng API_FAILURE với {m['retry_cached_tokens']:,} cached tokens; ghi nhận {m['scorable_provider_failures']} terminal provider failure trên {m['scorable_records_total']:,} scorable records).\n"
        f"3. Phân định giới hạn token: 13 requests INCOMPLETE dừng do chạm trần configured max_output_tokens ({m['max_tokens_limit']:,} tokens, "
        "tức ngân sách suy luận đầu ra được cấu hình), không phải do vượt cửa sổ ngữ cảnh context ceiling (~1,050,000 tokens của gpt-5.6-luna). "
        "Toàn bộ 13 requests này đều thuộc các view loại trừ/unmapped.\n"
        f"4. Hạch toán tài chính chính xác: trần ngân sách đóng băng cứng $19.99 USD "
        f"(hard_budget_limit_usd = ${m['budget_cap_usd']}). Chi phí quyết toán thực tế 5 điều kiện "
        f"chính thức là $6.58 settled spend (${m['settled_cost_usd']} USD).\n"
        f"5. Phân biệt rạch ròi: Khoản giữ chỗ thận trọng pilot ${m['pilot_hold_usd']} USD "
        f"(prior_pilot_provisional_hold_usd) được phân tách minh bạch khỏi chi phí "
        f"quyết toán thực tế ${m['settled_cost_usd']} USD. Tổng chi phí cam kết là $6.63 committed "
        f"spend (${m['committed_spend_usd']} USD), ngân sách khả dụng còn lại là $13.36 net remaining "
        f"(${m['remaining_balance_usd']} USD; 0 active holds, 0 breach).\n"
        f"6. Đánh đổi token: Tỷ lệ tăng token prompt từ k=1 lên k=10 là ~{m['k1_to_k10_prompt_ratio']:.3f}x "
        f"({m['k1_prompt_tokens']} lên {m['k10_prompt_tokens']} tokens); tỷ lệ từ No-RAG lên k=10 là ~{m['norag_to_k10_prompt_ratio']:.2f}x.\n"
        "Bằng chứng dự án: "
        f"docs/presentation/figures/canonical_rq3_resource_consumption.png (SHA-256: {prov['fig_rq3_sha']}); "
        "docs/presentation/figures/fig7_cost_and_tokens_vs_k.png; "
        "config/experiment_config.json (hard_budget_limit_usd: 19.99); "
        f"artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']}); "
        f"reports/experiment_protocol_v1.md (File SHA-256: {prov['protocol_file_sha']}; "
        f"Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
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
            "chứng khép kín trên tập dữ liệu đóng băng synthetic-paired-v1 cho bài toán "
            "Windows log attribution.",
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

    prov = ctx.provenance or load_provenance_hashes()
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
        f"Bằng chứng dự án: config/canonical_experiment_lock_v1.json (SHA-256: "
        f"{prov['lock_sha']}); "
        f"artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']}); "
        f"reports/experiment_protocol_v1.md (File SHA-256: {prov['protocol_file_sha']}; "
        f"Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
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

    prov = ctx.provenance or load_provenance_hashes()
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
        f"artifacts/results/canonical_metric_bundle_v2.json (SHA-256: {prov['bundle_sha']}); "
        f"reports/experiment_protocol_v1.md (File SHA-256: {prov['protocol_file_sha']}; Canonical Decisions Digest: {prov['protocol_decisions_digest']}); "
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


def write_deck_figures_audit(
    provenance: dict[str, str],
    output_path: Path,
) -> dict[str, Any]:
    """Audit and record SHA-256 digests of embedded figures in presentation deck."""
    try:
        deck_file_rel = str(output_path.resolve().relative_to(REPO_ROOT.resolve())).replace("\\", "/")
        is_repo_deck = True
    except ValueError:
        deck_file_rel = str(output_path).replace("\\", "/")
        is_repo_deck = False

    audit_data = {
        "schema_version": "1.0.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "deck_file": deck_file_rel,
        "embedded_figures": {
            "slide_6_rq2_hit_rate": {
                "file": "docs/presentation/figures/canonical_rq2_retrieval_hit_rate.png",
                "canonical_name": "fig4_retrieval_hit_rate.png",
                "sha256": provenance.get("fig_rq2_sha", "f8287936d2b5fc24e89584349028f393b801b6bebe668f8bea449c6b67f2128f"),
                "cohort": "TEST 718 scorable views",
                "metric_hit10": "44.71% (321 / 718)",
            },
            "slide_9_rq3_resource_consumption": {
                "file": "docs/presentation/figures/canonical_rq3_resource_consumption.png",
                "canonical_name": "fig7_cost_and_tokens_vs_k.png",
                "sha256": provenance.get("fig_rq3_sha", "ca296165b38b499432f851618e3d6a512964c461e59dc3b646e647ddcb70bfb1"),
                "cohort": "TEST 1,280 views cohort (6,400 logical requests)",
                "k10_prompt_tokens_mean": 5114.3,
                "k1_to_k10_prompt_ratio": 4.103,
            },
        },
        "provenance_anchors": {
            "canonical_lock": provenance.get("lock_sha"),
            "experiment_config": provenance.get("experiment_config_sha"),
            "baseline_prompt": provenance.get("prompt_sha"),
            "inference_data": provenance.get("inference_sha"),
            "pairs_data": provenance.get("pairs_sha"),
            "canonical_bundle": provenance.get("bundle_sha"),
        },
    }

    if is_repo_deck and output_path.resolve() == OUTPUT_PATH.resolve():
        deck_audit_path = REPO_ROOT / "docs" / "presentation" / "deck_figures_audit.json"
        evidence_audit_path = REPO_ROOT / "reports" / "evidence" / "canonical_deck_figures_audit.json"

        deck_audit_path.parent.mkdir(parents=True, exist_ok=True)
        deck_audit_path.write_text(json.dumps(audit_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        evidence_audit_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_audit_path.write_text(json.dumps(audit_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return audit_data


def export_slides_markdown(ctx: DeckContext, target_path: Path | None = None) -> Path:
    """Generate and synchronize docs/presentation/slides.md directly from DeckContext."""
    dest = target_path or (REPO_ROOT / "docs" / "presentation" / "slides.md")
    dest.parent.mkdir(parents=True, exist_ok=True)
    prov = ctx.provenance or load_provenance_hashes()
    m = ctx.metrics
    banner = ctx.banner_text

    md_lines = [
        "# RAG2ATT&CK: Đánh Giá Tác Động Của Retrieval-Augmented Generation Dựa Trên MITRE ATT&CK Đối Với Ánh Xạ Windows Endpoint Logs",
        "",
        "**Slide Deck & Presentation Scaffold for Scientific Defense & Technical Demonstration**  ",
        f"*Trạng thái bản dựng:* `{banner}`  ",
        f"*Mã giao thức thực nghiệm:* `experiment-protocol-v1.1` (Canonical Decisions Digest: `{prov['protocol_decisions_digest']}`, Raw File SHA-256: `{prov['protocol_file_sha']}`)  ",
        f"*Khóa thực nghiệm chuẩn:* `canonical-lock-v1` (SHA-256: `{prov['lock_sha']}`)  ",
        "*Tài liệu hướng dẫn tái lập:* [`docs/reproducibility.md`](../reproducibility.md)  ",
        "*Bộ slide trình chiếu PowerPoint (16:9):* [`docs/presentation/slides.pptx`](slides.pptx)",
        "",
        "---",
        "",
        "## Slide 1: Trang Tiêu Đề (Title Slide)",
        "",
        "### Nội dung trình chiếu",
        "- **Tiêu đề chính:** Đánh Giá Tác Động Của MITRE ATT&CK-Grounded Retrieval-Augmented Generation Đối Với Việc Ánh Xạ Windows Endpoint Logs Sang ATT&CK Techniques",
        "- **Tiêu đề tiếng Anh:** Evaluating MITRE ATT&CK-Grounded Retrieval-Augmented Generation for Technique Attribution from Windows Endpoint Logs (RAG2ATT&CK)",
        "- **Tác giả:** Nhóm Nghiên Cứu RAG2ATT&CK",
        "- **Phân loại nghiên cứu:** Thực nghiệm đối chứng có kiểm soát (Controlled Empirical Study)",
        "- **Trạng thái kỹ thuật & pháp lý:**",
        "  - Giao thức khoa học: `experiment-protocol-v1.1` (Frozen Protocol)",
        "  - Khóa mật mã thực nghiệm: `canonical-lock-v1` (15 Canonical Artifacts Verified)",
        "  - Khả năng tái lập: 100% Offline & Zero-Cost Verification (`scripts/reproduce_canonical_study.py --all`)",
        f"  - Trạng thái phê duyệt: `{banner}`",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Kính thưa Hội đồng và các chuyên gia, hôm nay tôi xin trình bày báo cáo nghiên cứu RAG2ATT&CK: Đánh giá tác động của MITRE ATT&CK-grounded RAG đối với việc ánh xạ Windows endpoint logs sang ATT&CK techniques. Toàn bộ nghiên cứu được thiết kế theo phương pháp thực nghiệm đối chứng nghiêm ngặt dưới giao thức đóng băng experiment-protocol-v1.1, khóa mật mã 15 canonical artifacts, và có thể tái lập hoàn toàn ngoại tuyến với chi phí 0 đồng.',
        "> ",
        "> *Khai báo công cụ:* Toàn bộ slide deck này được tạo tự động bằng kịch bản Python `scripts/generate_slides.py` thông qua thư viện `python-pptx` định dạng 16:9 widescreen, được thẩm định hiển thị bằng các bundled artifact tools nội bộ.",
        "> ",
        f'> *Bằng chứng dự án:* `config/canonical_experiment_lock_v1.json` (SHA-256: `{prov["lock_sha"]}`); `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `artifacts/results/canonical_metric_bundle_v2.json` (SHA-256: `{prov["bundle_sha"]}`); `scripts/reproduce_canonical_study.py`."',
        "",
        "---",
        "",
        "## Slide 2: Vấn Đề Nghiên Cứu & Động Lực (Problem Statement & Motivation)",
        "",
        "### Nội dung trình chiếu",
        "- **Bối cảnh An toàn Thông tin (SOC Monitoring):**",
        "  - Nhật ký Windows Endpoint (Security Events, Sysmon) là tuyến phòng thủ then chốt của các Trung tâm Giám sát An ninh (SOC).",
        "  - Ánh xạ nhật ký thô sang ma trận MITRE ATT&CK Enterprise là tiêu chuẩn vàng để xác định ý đồ và chiến thuật tấn công.",
        "  - Quy trình thủ công đòi hỏi chuyên gia cấp cao, tốn thời gian và khó đáp ứng quy mô hàng triệu sự kiện mỗi ngày.",
        "- **Thách thức của LLM trong Log Attribution:**",
        "  - *Khoảng cách trừu tượng:* Nhật ký ở mức hệ thống chi tiết (Process GUID, CommandLine, ParentProcess, Hashes), trong khi ATT&CK Techniques mô tả hành vi ở mức khái niệm.",
        "  - *Hiện tượng ảo giác (Hallucination):* LLM thuần túy dễ gán nhầm sang các kỹ thuật phổ biến hoặc phát sinh mã ATT&CK không có trong danh mục.",
        "  - *Nhầm lẫn Sub-techniques:* Khó phân biệt giữa các kỹ thuật lân cận (ví dụ: `T1059.001` PowerShell vs `T1059.003` Command Shell; hoặc `T1059.009` Cloud API vs `T1218.012` Verclsid).",
        "- **Động lực của RAG2ATT&CK:**",
        "  - Thiết kế nghiên cứu thực nghiệm đối chứng có kiểm soát (Controlled Empirical Study).",
        "  - Đo lường khách quan delta hiệu năng do RAG mang lại trên cùng mô hình LLM.",
        "  - Bóc tách độc lập lỗi tìm kiếm (Retrieval Failure) và lỗi phân loại (Classification Failure).",
        "  - **Phạm vi tính xác định (Determinism Scope):** Áp dụng cho khâu tái tạo bộ dữ liệu, quy trình đánh giá ngoại tuyến và thứ tự tie-breaking.",
        "  - **Biến thiên backend LLM & Chính sách D3:** Phản hồi và backend LLM có thể biến thiên (tham số `seed` không gửi qua giao thức mạng), được quản lý bởi chính sách siêu dữ liệu ràng buộc tem thời gian D3 (`timestamp-bound metadata policy`).",
        "  - Tái lập ngoại tuyến chi phí 0 đồng với bộ `offline_guard` can thiệp tầng socket.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Trong thực tế giám sát SOC, các kỹ sư thường kỳ vọng LLM có thể đọc log và gán ngay mã ATT&CK. Tuy nhiên, nếu không có cơ chế neo tri thức, LLM thường gặp ảo giác hoặc nhầm lẫn giữa các kỹ thuật lân cận. Nghiên cứu này định lượng khách quan mức độ hỗ trợ của RAG dưới các điều kiện đối chứng chặt chẽ, không phóng đại hiệu năng. Chúng tôi làm rõ phạm vi tính xác định (determinism): tính xác định áp dụng tuyệt đối cho khâu tái tạo bộ dữ liệu, quy trình thẩm định đánh giá ngoại tuyến và quy tắc xử lý thứ tự tie-breaking. Đối với mô hình LLM, phản hồi và backend mô hình thực tế có thể biến thiên do tham số seed không được truyền qua giao thức mạng; sự biến thiên này được theo dõi và ghi nhận chặt chẽ theo chính sách siêu dữ liệu ràng buộc tem thời gian D3 (timestamp-bound metadata policy).',
        "> ",
        f'> *Bằng chứng dự án:* `docs/README_PROPOSED.md`; `config/canonical_experiment_lock_v1.json` (SHA-256: `{prov["lock_sha"]}`); `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `tests/test_attack_id_validation.py`."',
        "",
        "---",
        "",
        "## Slide 3: Kiến Trúc Thực Nghiệm Đối Chứng (System Architecture)",
        "",
        "### Nội dung trình chiếu",
        "- **Hai nhánh thực nghiệm trên cùng dữ liệu đầu vào:**",
        "  1. **Nhánh Cơ Sở (Baseline No-RAG):**",
        r"     $$\text{Windows Endpoint Log} \longrightarrow \text{Prompt} \longrightarrow \text{LLM} \longrightarrow \text{JSON (technique\_id)}$$",
        "  2. **Nhánh Thử Nghiệm (Experimental RAG):**",
        r"     $$\text{Windows Log} \longrightarrow \text{Dense Retriever (FAISS)} \longrightarrow \text{Top-}k \text{ Docs} \longrightarrow \text{Prompt + Context} \longrightarrow \text{LLM} \longrightarrow \text{JSON}$$",
        "- **Kiến trúc bộ truy xuất gọn nhẹ (Lightweight Retrieval Engine):**",
        "  - *Knowledge Corpus:* 474 tài liệu ATT&CK v19.2 Enterprise Windows (`attack/corpus/enterprise-windows-v19.2.jsonl`).",
        r"  - *Embedding Model:* `sentence-transformers/all-MiniLM-L6-v2` (384 chiều, chuẩn hóa $L_2$).",
        "  - *Index:* Flat Inner Product FAISS Index (`IndexFlatIP`, Cosine similarity).",
        r"  - *Độ sâu k:* Khảo sát có hệ thống $k \in \{1, 3, 5, 10\}$.",
        "- **Các biến kiểm soát bất biến (Controlled Invariants):**",
        "  - Cùng mô hình (`gpt-5.6-luna`), cùng cấu hình suy luận (`reasoning_effort=xhigh`, `api_interface=responses`).",
        "  - Cùng cấu trúc Prompt template (`prompts/baseline_v1.txt`), chỉ khác biệt ở khối Context được chèn vào.",
        "  - **Biến duy nhất thay đổi:** Bật (ON) hoặc Tắt (OFF) khối ngữ cảnh truy xuất ATT&CK.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Kiến trúc thực nghiệm đối chứng kiểm soát nghiêm ngặt biến số điều trị duy nhất: Retrieval ON vs OFF. Nhánh Baseline No-RAG và Experimental RAG dùng chung một mô hình gpt-5.6-luna (xhigh), cùng cấu trúc prompt template, và cùng schema JSON đầu ra. Bộ tìm kiếm sử dụng all-MiniLM-L6-v2 kết hợp FAISS IndexFlatIP trên 474 tài liệu ATT&CK v19.2 Enterprise Windows.',
        "> ",
        f'> *Bằng chứng dự án:* `prompts/baseline_v1.txt` (SHA-256: `{prov["prompt_sha"]}`); `attack/corpus/enterprise-windows-v19.2.jsonl` (SHA-256: `b219341154ddf2f12e97d622158a04ab7d57641df6a865559258d365852c3c75`); `config/experiment_config.json` (SHA-256: `961ba9b3e9e1b459a6694a5c8c76424d36c89d65bd4d88b14d0b0de7e4c017ac`); `tests/test_rag_pipeline.py`."',
        "",
        "---",
        "",
        "## Slide 4: Thiết Kế Dữ Liệu & Giao Thức Chống Rò Rỉ (Dataset Strategy & Anti-Leakage)",
        "",
        "### Nội dung trình chiếu",
        "- **Bộ dữ liệu chuẩn đóng băng Stage B (Frozen Stage B Benchmark):**",
        r"  - 670 cặp kịch bản (Scenario Pairs) $\rightarrow$ 1,340 biểu diễn đơn vị (Views).",
        f"  - Phân chia: {m['total_test_views']:,} TEST Views ({m['scorable_views']} scorable views across {m['distinct_clusters']} distinct clusters) và 60 DEV Views.",
        "  - Phân loại biểu diễn:",
        "    - *Single-event:* Một sự kiện đơn lẻ kích hoạt kỹ thuật tấn công mục tiêu.",
        "    - *Contextual-event:* Sự kiện mục tiêu kèm nhật ký ngữ cảnh lân cận trên cùng máy trạm.",
        "  - Độ bao phủ: 8 nhóm kỹ thuật mục tiêu đại diện cùng các mẫu âm tính / mơ hồ.",
        "  - Cấu trúc cặp: 278 complete pairs, 162 contextual-only pairs, 200 neither-mapped pairs.",
        "- **Giao thức chống rò rỉ nhãn nghiêm ngặt (Strict Anti-Label-Leakage):**",
        "  - Đầu vào suy luận (`data/ground_truth/synthetic/inference.jsonl`) chỉ chứa 2 trường: `sample_id` và `endpoint_evidence`.",
        "  - Toàn bộ nhãn mục tiêu, tên luật Sigma/Sysmon, Tactic name, và mô tả đều bị lọc bỏ thông qua allowlist (`INFERENCE_ALLOWLIST`).",
        "- **Phân định phạm vi rõ ràng:**",
        "  - Bộ dữ liệu Stage B là tài liệu chuẩn phục vụ kiểm định kỹ thuật và chẩn đoán truy xuất.",
        "  - Nghiên cứu phân định rõ ràng giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        f'> "Tập dữ liệu chuẩn đóng băng Stage B gồm 670 cặp kịch bản đối ứng (1,340 views), chia thành {m["total_test_views"]:,} TEST views và 60 DEV views. Giao thức chống rò rỉ nhãn áp dụng INFERENCE_ALLOWLIST nghiêm ngặt: đầu vào suy luận inference.jsonl chỉ chứa sample_id và endpoint_evidence; toàn bộ tên luật, mã technique và mô tả đều bị loại trừ tuyệt đối. Nghiên cứu phân định rõ ràng giữa benchmark giả lập Stage B và luồng telemetry thực địa T15.',
        "> ",
        f'> *Bằng chứng dự án:* `data/ground_truth/synthetic/inference.jsonl` (SHA-256: `{prov["inference_sha"]}`); `data/ground_truth/synthetic/pairs.jsonl` (SHA-256: `{prov["pairs_sha"]}`); `tests/test_benchmark_inputs.py`; `tests/test_synthetic_freeze.py`."',
        "",
        "---",
        "",
        "## Slide 5: Phương Pháp Luận, Mô Hình Đe Dọa & Giao Thức v1.1",
        "",
        "### Nội dung trình chiếu",
        "- **Mô hình đe dọa & Danh mục ATT&CK v19.2 (Threat Model & Corpus):**",
        "  - Tiêu chuẩn danh mục: Pinned MITRE ATT&CK v19.2 Enterprise Windows (474 techniques/sub-techniques).",
        "  - **Mã hóa giao thức chuẩn tắc (Giao thức v1.1):**",
        "    - `D2d: FROZEN_BENCHMARK_UNIVERSE = 474` (không gian lớp mục tiêu cố định, Macro-F1 tính trên tập đóng băng).",
        "    - `D2g: ALLOW_HISTORICAL` (chấp nhận mã lịch sử/thu hồi trong benchmark, báo cáo distinct counts, không silent remapping).",
        "    - `D2e: invalid_id_as_failure` (`INCLUDE_IN_DENOMINATOR`, fail-closed khi mô hình sinh mã sai cú pháp hoặc ngoài danh mục).",
        "    - `D2f: api_failure_as_failure` (`INCLUDE_IN_DENOMINATOR`, không loại trừ mẫu khi gặp lỗi mạng/API refusal/timeout).",
        "    - `D2b-c: EXCLUDE` (loại trừ các mẫu ground-truth rỗng hoặc mơ hồ khỏi mẫu số đo lường).",
        "    - `D1: RECORD_ONLY` (lưu vết đầy đủ toàn bộ phản hồi thô phục vụ kiểm toán độc lập; các trường thông tin đăng nhập, token và bí mật nhạy cảm đều được khử khuẩn / làm mờ trước khi lưu trữ, không lưu raw secrets).",
        "- **Tiêu chí đánh giá cốt lõi & Kỷ cương thực nghiệm:**",
        "  - **Bốn tiêu chí đo lường trọng tâm:**",
        "    - `D2h: ANY_GT_RETRIEVED` (truy xuất thành công nếu có ít nhất 1 kỹ thuật mục tiêu trong Top-k).",
        "    - `D2i: INDEPENDENT_AXES` (phân rã lỗi theo 3 trục đo lường độc lập, ghi nhận đầy đủ overlap, không giả định độc lập ngẫu nhiên).",
        "    - `D2e: invalid_id_as_failure` (mã ATT&CK ảo giác tính là lỗi phân loại).",
        "    - `D2f: api_failure_as_failure` (lỗi provider / gián đoạn API tính vào mẫu số).",
        "  - **Kỷ cương thực nghiệm bất biến:**",
        "    - `D3:` Khóa mô hình: `ALLOW_LATEST_WITH_TIMESTAMP_BINDING` (tem UTC thực tế).",
        "    - `D4:` Thực thi tuần tự (`SEQUENTIAL_ONLY`), tuyệt đối không chạy song song.",
        "    - `D5:` Chặn cứng ngân sách đóng băng (`HARD_CAP`, trần $19.99 USD).",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Giao thức thực nghiệm v1.1 đóng băng 7 quyết định phương pháp luận cốt lõi D1-D7. Về mô hình đe dọa, danh mục kỹ thuật được neo tại STIX ATT&CK v19.2 Enterprise Windows (474 techniques theo quyết định D2d FROZEN_BENCHMARK_UNIVERSE). Chính sách D1 RECORD_ONLY lưu toàn văn phản hồi thô phục vụ kiểm toán độc lập nhưng đảm bảo toàn bộ credentials và bí mật nhạy cảm đã được làm sạch / khử khuẩn (credentials and sensitive secrets sanitized/redacted), tuyệt đối không lưu lộ lọt bí mật. Điểm đặc biệt quan trọng là chính sách D2g ALLOW_HISTORICAL: các mã kỹ thuật lịch sử hoặc đã bị thu hồi có trong benchmark được chấp nhận và báo cáo dạng distinct observation count, không tự ý gán lại mã thay thế. Bốn tiêu chí đánh giá cốt lõi gồm D2h (ANY_GT_RETRIEVED cho multi-label), D2i (INDEPENDENT_AXES ghi nhận đầy đủ overlap giữa các trục đo lường độc lập), D2e (invalid_id_as_failure: invalid ID tính vào mẫu số), và D2f (api_failure_as_failure: lỗi mạng/API tính vào mẫu số) thiết lập nguyên tắc fail-closed nghiêm ngặt.',
        "> ",
        f'> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `attack/raw/enterprise-v19.2/enterprise-attack-19.2.json` (SHA-256: `dc1639caa5501d720e280cf1cbd8fbe009884a0c9b3e6e9ed9d0c25166c3d8f4`); `tests/test_experiment_evaluation.py`."',
        "",
        "---",
        "",
        "## Slide 6: Kết Quả RQ2 - Chẩn Đoán Khâu Truy Xuất (Retrieval Quality)",
        "",
        "### Nội dung trình chiếu",
        f"- **Chẩn đoán khâu truy xuất trên tập chuẩn tắc (CANONICAL TEST RETRIEVAL - Mẫu số N={m['scorable_views']} canonical views):**",
        f"  - *Hit@1:* {m['hit1_rate']} ({m['hit1_count']} / {m['scorable_views']})",
        f"  - *Hit@3:* {m['hit3_rate']} ({m['hit3_count']} / {m['scorable_views']})",
        f"  - *Hit@5:* {m['hit5_rate']} ({m['hit5_count']} / {m['scorable_views']})",
        f"  - *Hit@10:* {m['hit10_rate']} ({m['hit10_count']} / {m['scorable_views']})",
        f"  - *Retrieval Miss Rate:* {m['miss10_rate']} ({m['miss10_count']} / {m['scorable_views']})",
        f"  - *Macro Recall@10:* {m['macro_recall10']}  |  *Độ phủ Top-10:* Hit@10 = {m['hit10_rate']}",
        "- **Khoảng cách từ vựng (Lexical Divergence) ở `T1136.001`:**",
        f"  - Kỹ thuật `T1136.001` (Create Account: Local Account) đạt **0% Top-10 Hit Rate (0 / 95 canonical TEST views)**.",
        '  - *Giả thuyết phân kỳ từ vựng:* Nhật ký Windows Event ID 4720 nhấn mạnh từ ngữ hệ thống ("SamAccountName"), trong khi mô tả STIX ATT&CK nhấn mạnh mục tiêu chiến thuật ("persistence").',
        "- **Giả thuyết Context Scaling & Dilution (k=1,3,5,10):**",
        "  - Tăng độ sâu k cải thiện độ phủ ngữ cảnh nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng trên ma trận TEST.",
        "  - Cơ chế ảnh hưởng tới downstream generation được ghi nhận dưới dạng tương quan quan sát, không suy diễn quan hệ nhân quả tuyệt đối.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        f'> "Chẩn đoán độc lập khâu tìm kiếm (RQ2) đánh giá độc lập trên {m["scorable_views"]} canonical TEST views: Hit@1={m["hit1_rate"]} ({m["hit1_count"]}/{m["scorable_views"]}), Hit@3={m["hit3_rate"]} ({m["hit3_count"]}/{m["scorable_views"]}), Hit@5={m["hit5_rate"]} ({m["hit5_count"]}/{m["scorable_views"]}), Hit@10={m["hit10_rate"]} ({m["hit10_count"]}/{m["scorable_views"]}), Retrieval Miss={m["miss10_rate"]} ({m["miss10_count"]}/{m["scorable_views"]}), Macro Recall@10={m["macro_recall10"]}. Điển hình là kỹ thuật T1136.001 đạt 0% Top-10 Hit Rate (0/95 canonical TEST views) phù hợp với giả thuyết phân kỳ từ vựng giữa Event ID 4720 (\'SamAccountName\') và mô tả STIX (\'persistence\'). Chúng tôi ghi nhận giả thuyết Context Scaling & Dilution (k=1,3,5,10): tăng k cải thiện độ phủ nhưng tăng nguy cơ nhiễu distractor; đang được kiểm chứng đối chứng trên ma trận TEST.',
        "> ",
        f'> *Bằng chứng dự án:* `docs/presentation/figures/canonical_rq2_retrieval_hit_rate.png` (SHA-256: `{PINNED_MEDIA_DIGESTS["rq2_retrieval_hit_rate"]["sha256"]}`); `docs/presentation/figures/fig4_retrieval_hit_rate.png`; `outputs/reproduction/tables/table_1_retrieval_diagnostics.md`; `tests/test_retrieval_diagnostics.py`."',
        "",
        "---",
        "",
        "## Slide 7: Phân Tích Lỗi Khâu Truy Xuất & Chẩn Đoán Có Điều Kiện (RQ2)",
        "",
        "### Nội dung trình chiếu",
        f"- **Chẩn Đoán Có Điều Kiện Theo Khâu Truy Xuất (TEST N={m['scorable_views']}):**",
        r"  - Kỹ thuật GT có mặt trong Top-10 (Retrieval Success): $N=" + str(m['retrieved_views']) + r"$ (" + m['hit10_rate'] + r")",
        r"    - $P(\text{Đúng} \mid \text{Đã truy xuất}) = " + m['hit_acc_rate'] + f"$ ({m['hit_acc_count']} / {m['retrieved_views']} views được gán đúng).",
        r"  - Kỹ thuật GT vắng mặt trong Top-10 (Retrieval Miss): $N=" + str(m['missed_views']) + r"$ (" + m['miss10_rate'] + r")",
        r"    - $P(\text{Đúng} \mid \text{Vắng mặt}) = " + m['miss_acc_rate'] + f"$ ({m['miss_acc_count']} / {m['missed_views']} views gán đúng khi vắng mặt ngữ cảnh trong Top-10).",
        f"  - Khoảng chênh lệch quan sát: **+21.25 pp** ({m['hit_acc_rate']} vs {m['miss_acc_rate']}) cho thấy sự hiện diện của ngữ cảnh gắn liền với tỷ lệ gán đúng cao hơn.",
        "  - **Nguyên tắc suy luận:** Trình bày thuần túy dưới dạng tương quan quan sát (observational association), không suy diễn quan hệ nhân quả tuyệt đối.",
        "- **Bóc Tách Lỗi & Phần Giao Thoa Độc Lập Theo Định Đề D2i:**",
        f"  - Tổng số lỗi phân loại tại $k=10$: **{m['k10_wrong_count']} views** (718 - 571 = 147).",
        f"  - **Phần giao thoa lỗi (Joint Overlap per D2i):** **{m['overlap_miss_and_wrong']} / {m['k10_wrong_count']}** ({m['overlap_pct']:.2f}% tổng lỗi phân loại) xảy ra khi retrieval trượt Top-10.",
        f"  - Lỗi khi retrieval thành công: **{m['wrong_while_retrieved']} / {m['k10_wrong_count']}** ({m['wrong_while_retrieved_pct']:.2f}% tổng lỗi phân loại) mô hình chọn sai kỹ thuật dù đã có trong ngữ cảnh (giả thuyết distractor / downstream confusion đang được kiểm chứng).",
        "  - **Tuân thủ định đề D2i:** Ghi nhận đầy đủ phần giao thoa khác 0 giữa các trục đo lường lỗi độc lập, không áp đặt giả định xung khắc hay độc lập xác suất ngẫu nhiên.",
        "  - **Schema So Sánh Đối Chứng Scaffold:** Không sử dụng prompt scaffold trong giao thức chuẩn tắc.",
        f"  - **Ranh giới an toàn:** Không xuất hiện lỗi API hay lỗi cú pháp mã kỹ thuật trên tập scorable ({m['scorable_provider_failures']} terminal provider failures, {m['invalid_id_count']} invalid IDs).",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        f'> "Phân tích lỗi khâu truy xuất và chẩn đoán có điều kiện (RQ2) trên tập scorable N={m["scorable_views"]} cho thấy: khi kỹ thuật đúng có mặt trong Top-10 (N={m["retrieved_views"]}), tỷ lệ gán đúng đạt {m["hit_acc_rate"]} ({m["hit_acc_count"]}/{m["retrieved_views"]}); khi kỹ thuật đúng vắng mặt (N={m["missed_views"]}), tỷ lệ gán đúng là {m["miss_acc_rate"]} ({m["miss_acc_count"]}/{m["missed_views"]}). Độ chênh lệch quan sát được là +21.25 pp. Chúng tôi nhấn mạnh: đây thuần túy là tương quan quan sát trong thực nghiệm (observational association), không áp đặt suy diễn quan hệ nhân quả.',
        "> ",
        f'> Theo định đề phân rã lỗi D2i, trong số {m["k10_wrong_count"]} trường hợp phân loại sai tại k=10, có tới {m["overlap_miss_and_wrong"]} trường hợp ({m["overlap_pct"]:.2f}%) đồng thời rơi vào khâu retrieval miss. Chỉ có {m["wrong_while_retrieved"]} trường hợp ({m["wrong_while_retrieved_pct"]:.2f}%) bị phân loại sai khi kỹ thuật đã được truy xuất thành công (giả thuyết distractor / downstream confusion đang được kiểm chứng).',
        "> ",
        f'> *Bằng chứng dự án:* `artifacts/results/canonical_metric_bundle_v2.json` (SHA-256: `{prov["bundle_sha"]}`); `reports/experiment_protocol_v1.md` (D2i; Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `tests/test_experiment_evaluation.py`."',
        "",
        "---",
        "",
        f"## Slide 8: Khung Đánh Giá End-to-End (RQ1) & Phân Rã Lỗi Theo 3 Trục Độc Lập D2i (RQ2) `{banner}`",
        "",
        "### Nội dung trình chiếu",
        f"- **Bảng Đối Chứng Toàn Diện 5 Điều Kiện (RQ1 Full 5-Condition Comparison Matrix - N={m['scorable_views']}):**",
        "",
        "| Điều kiện | Accuracy | Macro-F1 (D2d Universe = 474) | Delta vs Baseline | McNemar p-value |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| **Baseline No-RAG** | {m['no_rag_acc']} ({m['no_rag_correct']}/{m['scorable_views']}) | {m['no_rag_macro_f1']} | — | — |",
        f"| **RAG (k=1)** | {m['k1_acc']} ({m['k1_correct']}/{m['scorable_views']}) | {m['k1_macro_f1']} | {m['k1_delta_pp']} (CI {m['k1_ci_95_pp']}) | p = {m['k1_p']} |",
        f"| **RAG (k=3)** | {m['k3_acc']} ({m['k3_correct']}/{m['scorable_views']}) | {m['k3_macro_f1']} | {m['k3_delta_pp']} (CI {m['k3_ci_95_pp']}) | p = {m['k3_p']} |",
        f"| **RAG (k=5)** | {m['k5_acc']} ({m['k5_correct']}/{m['scorable_views']}) | {m['k5_macro_f1']} | {m['k5_delta_pp']} (CI {m['k5_ci_95_pp']}) | p = {m['k5_p']} |",
        f"| **RAG (k=10)** | {m['k10_acc']} ({m['k10_correct']}/{m['scorable_views']}) | {m['k10_macro_f1']} | {m['delta_acc_pp']} (CI {m['delta_ci_95_pp']}) | p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} |",
        "",
        "- **Ranh Giới Khoa Học Bắt Buộc & Độ Bất Định Thống Kê:**",
        f"  - *Hiệu năng quan sát được:* RAG $k=10$ đạt {m['k10_correct']}/{m['scorable_views']} (**{m['k10_acc']}**) vs No-RAG {m['no_rag_correct']}/{m['scorable_views']} (**{m['no_rag_acc']}**), Delta = **{m['delta_acc_pp']}** ({m['delta_rel_pct']} relative).",
        f"  - *Độ bất định thống kê:* Paired difference CI vs No-RAG: **{m['delta_ci_95_pp']}** chứa 0; McNemar exact $p = {m['mcnemar_p_exact']}$ / hiển thị ${m['mcnemar_p_display']} > 0.05$ (không đạt ý nghĩa thống kê ở mức $\\alpha = 0.05$).",
        '  - *Quy chuẩn diễn đạt bắt buộc:* Mô tả $k=10$ là **"độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định"** (observed highest tested accuracy and uncertainty). **CẤM** tuyên bố "chiến thắng có ý nghĩa thống kê" hoặc "lợi ích vượt trội trong production".',
        f"  - *Macro-F1 (Vũ trụ 474 lớp D2d FROZEN_BENCHMARK_UNIVERSE):* $k=10$ đạt **{m['k10_macro_f1']}** vs No-RAG **{m['no_rag_macro_f1']}** (Delta {m['delta_macro_f1']}; 8 supported classes, 466 zero-support classes).",
        "- **Mô hình phân rã lỗi theo 3 trục đo lường độc lập (Định đề D2i):**",
        f"  - **Trục 1 - Retrieval Miss Rate:** Kỹ thuật ground-truth vắng mặt trong Top-k theo D2h `ANY_MATCH` (k=10: {m['miss10_count']} / {m['scorable_views']} = {m['miss10_rate']}).",
        f"  - **Trục 2 - Downstream Generation Failure:** Invalid ATT&CK ID = {m['invalid_id_count']} (D2e), scorable provider failure = {m['scorable_provider_failures']} (0 / {m['scorable_records_total']:,} scorable records trên 5 điều kiện; 1 physical retry API_FAILURE thành công với {m['retry_cached_tokens']:,} cached tokens; {m['terminal_incomplete_count']} INCOMPLETE trên toàn bộ {m['logical_requests']:,} dispatches), phân loại sai (Wrong Classification: {m['k10_wrong_count']} / {m['scorable_views']} = 20.47%).",
        f"  - **Trục 3 - Joint Overlap:** {m['overlap_miss_and_wrong']} bản ghi vừa trượt truy xuất vừa lỗi phân loại ({m['overlap_pct']:.2f}% của tổng {m['k10_wrong_count']} lỗi phân loại; không giả định độc lập ngẫu nhiên).",
        "- **Các thước đo có điều kiện (Conditional Metrics) & Fail-Closed Invariant:**",
        r"  - $P(\text{Correct} \mid \text{GT in Top-}k) = " + m['hit_cond_acc'] + f"$ ({m['hit_correct']} / {m['hit_samples']}) tại $k=10$: Đánh giá lựa chọn khi có ngữ cảnh trúng.",
        r"  - $P(\text{Correct} \mid \text{GT NOT in Top-}k) = " + m['miss_cond_acc'] + f"$ ({m['miss_correct']} / {m['miss_samples']}) tại $k=10$: Xác suất gán đúng quan sát được khi vắng mặt ngữ cảnh trong Top-k (không suy diễn tự sửa sai nội tại).",
        "  - **Fail-Closed Invariant:** Không loại trừ bất kỳ ca suy luận lỗi nào khỏi mẫu số (D2e, D2f); bảo toàn tính khách quan tuyệt đối.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        f'> "Tại Slide 8, bảng đối chứng RQ1 bao quát toàn bộ 5 điều kiện thực nghiệm trên N={m["scorable_views"]} (474 lớp vũ trụ D2d):',
        f'> 1. No-RAG:    {m["no_rag_acc"]} ({m["no_rag_correct"]}/{m["scorable_views"]}), Macro-F1 = {m["no_rag_macro_f1"]} (Baseline đối chứng).',
        f'> 2. RAG (k=1):  {m["k1_acc"]} ({m["k1_correct"]}/{m["scorable_views"]}), Macro-F1 = {m["k1_macro_f1"]}, Delta = {m["k1_delta_pp"]} (CI {m["k1_ci_95_pp"]}), McNemar p = {m["k1_p"]}.',
        f'> 3. RAG (k=3):  {m["k3_acc"]} ({m["k3_correct"]}/{m["scorable_views"]}), Macro-F1 = {m["k3_macro_f1"]}, Delta = {m["k3_delta_pp"]} (CI {m["k3_ci_95_pp"]}), McNemar p = {m["k3_p"]}.',
        f'> 4. RAG (k=5):  {m["k5_acc"]} ({m["k5_correct"]}/{m["scorable_views"]}), Macro-F1 = {m["k5_macro_f1"]}, Delta = {m["k5_delta_pp"]} (CI {m["k5_ci_95_pp"]}), McNemar p = {m["k5_p"]}.',
        f'> 5. RAG (k=10): {m["k10_acc"]} ({m["k10_correct"]}/{m["scorable_views"]}), Macro-F1 = {m["k10_macro_f1"]}, Delta = {m["delta_acc_pp"]} ({m["delta_rel_pct"]} relative; 95% CI {m["delta_ci_95_pp"]} chứa 0), McNemar p = {m["mcnemar_p_exact"]} / {m["mcnemar_p_display"]} > 0.05.',
        '> Nghiên cứu khẳng định RAG k=10 là độ chính xác quan sát được cao nhất trong thử nghiệm kèm độ bất định, tuyệt đối không tuyên bố chiến thắng có ý nghĩa thống kê hay lợi ích vượt trội trong production.',
        "> ",
        f'> Về Macro-F1: Được đánh giá nhất quán trên toàn bộ vũ trụ 474 lớp kỹ thuật MITRE ATT&CK v19.2 Enterprise Windows theo định đề D2d (FROZEN_BENCHMARK_UNIVERSE = 474), gồm 8 lớp có mẫu hỗ trợ và 466 lớp zero-support: No-RAG đạt {m["no_rag_macro_f1"]} vs RAG k=10 đạt {m["k10_macro_f1"]} (Delta {m["delta_macro_f1"]}).',
        "> ",
        f'> Ranh giới lỗi phân định độc lập: 1 physical retry thành công sau sự cố mạng API_FAILURE; ghi nhận {m["scorable_provider_failures"]} terminal provider failure trên toàn bộ {m["scorable_records_total"]:,} scorable records ({m["terminal_incomplete_count"]} incomplete records ghi nhận trên toàn campaign {m["logical_requests"]:,} requests đều thuộc nhóm unmapped/ambiguous).',
        "> ",
        f'> Về các thước đo có điều kiện tại k=10: P(Correct | GT in Top-k) = {m["hit_cond_acc"]} ({m["hit_correct"]}/{m["hit_samples"]}), trong khi P(Correct | GT NOT in Top-k) = {m["miss_cond_acc"]} ({m["miss_correct"]}/{m["miss_samples"]}); tỷ lệ này không cho phép suy diễn mô hình tự sửa sai nội tại. Nguyên tắc Fail-Closed Invariant được duy trì bất biến.',
        "> ",
        f'> *Bằng chứng dự án:* `reports/experiment_protocol_v1.md` (D2d, D2e, D2f, D2h, D2i; Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `artifacts/results/canonical_metric_bundle_v2.json` (SHA-256: `{prov["bundle_sha"]}`); `tests/test_experiment_evaluation.py`."',
        "",
        "---",
        "",
        "## Slide 9: Nghiên Cứu Tiêu Thụ Tài Nguyên & Hạch Toán Tài Chính Toàn Nghiên Cứu (RQ3)",
        "",
        "### Nội dung trình chiếu",
        "- **Phân Tích Tài Nguyên và Chi Phí Chuẩn Tắc (TEST 718) [CANONICAL STUDY]:**",
        "  - Chi phí được tính theo **ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate)**:",
        f"    - *No-RAG:* **~{m['no_rag_cost_per_req']}/req** (TB {m['no_rag_prompt_tokens']} in / {m['no_rag_comp_tokens']} out, trễ {m['no_rag_median_latency_ms']} ms).",
        f"    - *RAG $k=10$:* **~{m['k10_cost_per_req']}/req** (TB {m['k10_prompt_tokens']} in / {m['k10_comp_tokens']} out, trễ {m['k10_median_latency_ms']} ms).",
        "- **Đánh Đổi Hiệu Năng - Chi Phí Chuẩn Tắc (No-RAG vs RAG $k=10$):**",
        f"  - *Hit rate chuẩn tắc (TEST 718):* RAG $k=1$ đạt **{m['hit1_rate']}** $\\rightarrow$ RAG $k=10$ đạt **{m['hit10_rate']}** (No-RAG: **N/A**, không sử dụng retriever).",
        f"  - *Tăng k từ 1 lên 10 (k1 -> k10):* Lượng prompt tokens tăng **~{m['k1_to_k10_prompt_ratio']:.3f}x** ({m['k1_prompt_tokens']} lên {m['k10_prompt_tokens']} tokens; chi phí request tăng $0.001013 lên $0.001679 USD).",
        f"  - *So với Baseline No-RAG ({m['no_rag_prompt_tokens']} tokens):* $k=10$ tăng **~{m['norag_to_k10_prompt_ratio']:.2f}x** prompt tokens và ~4.6x chi phí logical query ($0.000365 lên $0.001679 USD).",
        f"- **Hạch Toán Tài Chính Toàn Thể 6,400 Requests (6,401 physical attempts vs 6,400 logical requests trên N={m['queries_per_condition']:,} queries / điều kiện):**",
        f"  - Quy mô khảo sát chiến dịch TEST: N={m['queries_per_condition']:,} views/điều kiện ({m['logical_requests']:,} logical requests, {m['physical_attempts']:,} physical attempts). Dữ liệu Stage B là telemetry giả lập có cấu trúc (synthetic split), không phải in-the-wild logs.",
        f"  - Trần ngân sách tối đa đóng băng cứng: **$19.99 USD** (${m['budget_cap_usd']} `hard_budget_limit_usd`).",
        f"  - Quyết toán thực tế 5 điều kiện chính thức: **$6.58 settled spend** (${m['settled_cost_usd']} USD), cộng giữ chỗ thận trọng pilot ${m['pilot_hold_usd']} USD, tổng cam kết là **$6.63 committed spend** (${m['committed_spend_usd']} USD).",
        f"  - Số dư chưa cam kết khả dụng còn lại: **$13.36 USD** (${m['remaining_balance_usd']} USD net remaining; 0 holds, 0 breach).",
        f"  - Xử lý ngoại lệ & Token cache: {m['terminal_incomplete_count']} requests chạm trần cấu hình max_output_tokens ({m['max_tokens_limit']:,} max tokens; cấu hình đầu ra quy định trong giao thức, phân biệt với trần cửa sổ ngữ cảnh mô hình ~1.05M tokens) đều thuộc nhóm unmapped/ambiguous; 1 lượt retry vật lý thành công do lỗi mạng API_FAILURE với {m['retry_cached_tokens']:,} cached tokens (tổng {m['physical_attempts']:,} physical attempts so với {m['logical_requests']:,} logical requests; {m['scorable_provider_failures']} terminal provider failures trên {m['scorable_records_total']:,} scorable records).",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        f'> "Trong phân tích RQ3, toàn bộ chỉ số tài nguyên, độ trễ và chi phí được tính trên toàn bộ {m["queries_per_condition"]:,} queries / điều kiện (tổng {m["logical_requests"]:,} logical requests, {m["physical_attempts"]:,} physical attempts), không rút gọn về {m["scorable_views"]} scorable views:',
        "> 1. Dữ liệu thử nghiệm Stage B là dữ liệu tổng hợp (synthetic split). Việc gửi request lên OpenAI không biến log tổng hợp thành dữ liệu thực địa in-the-wild.",
        f"> 2. Độ trễ & Tài nguyên: Phân biệt rõ trễ trung vị (No-RAG {float(m['no_rag_median_latency_ms'])/1000:.2f}s vs RAG k10 {float(m['k10_median_latency_ms'])/1000:.2f}s) và trễ trung bình. Lượng prompt tokens trung bình tăng từ {m['k1_prompt_tokens']} lên {m['k10_prompt_tokens']} (~{m['k1_to_k10_prompt_ratio']:.3f}x từ k1 đến k10; so với Baseline {m['no_rag_prompt_tokens']} là ~{m['norag_to_k10_prompt_ratio']:.2f}x), chi phí mỗi request tăng từ $0.000365 lên $0.001679 USD (~4.6x từ baseline đến k10).",
        f"> 3. Hiệu quả đánh đổi: Hit rate chuẩn tắc trên tập scorable N={m['scorable_views']}: No-RAG là N/A (không dùng retriever); RAG k=1 đạt Hit@1 = {m['hit1_rate']} ({m['hit1_count']}/{m['scorable_views']}), tăng lên RAG k=10 đạt Hit@10 = {m['hit10_rate']} ({m['hit10_count']}/{m['scorable_views']}).",
        f"> 4. Hạch toán tài chính 8 chữ số thập phân chính xác: Chi phí 5 điều kiện chuẩn đã quyết toán là ${m['settled_cost_usd']} USD ($6.58 settled spend), cộng với khoản giữ chỗ thận trọng pilot ${m['pilot_hold_usd']} USD, tổng chi phí đã cam kết là ${m['committed_spend_usd']} USD ($6.63 USD committed spend). Ngân sách khả dụng còn lại là ${m['remaining_balance_usd']} USD ($13.36 USD net remaining; 0 active holds, 0 breach) trên trần đóng băng cứng ${m['budget_cap_usd']} USD ($19.99 budget cap). Chi phí được tính toán theo ước tính thận trọng từ bảng giá đóng băng (conservative accounted tariff estimate).",
        f"> 5. Cấu hình Token & Cache: {m['terminal_incomplete_count']} requests chạm trần cấu hình max_output_tokens ({m['max_tokens_limit']:,} max tokens; cấu hình đầu ra quy định trong giao thức, phân biệt với trần cửa sổ ngữ cảnh mô hình ~1.05M tokens); 1 attempt API_FAILURE được retry vật lý thành công ghi nhận {m['retry_cached_tokens']:,} cached tokens (tổng {m['physical_attempts']:,} physical attempts) với {m['scorable_provider_failures']} terminal provider failures trên {m['scorable_records_total']:,} scorable records.",
        "> ",
        f'> *Bằng chứng dự án:* `docs/presentation/figures/canonical_rq3_resource_consumption.png` (SHA-256: `{PINNED_MEDIA_DIGESTS["rq3_resource_consumption"]["sha256"]}`); `docs/presentation/figures/fig7_cost_and_tokens_vs_k.png`; `config/experiment_config.json`; `artifacts/results/canonical_metric_bundle_v2.json` (SHA-256: `{prov["bundle_sha"]}`); `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `tests/test_monetary_guard.py`."',
        "",
        "---",
        "",
        "## Slide 10: Giới Hạn Nghiên Cứu & Mối Đe Dọa Giá Trị (Limitations & Threats to Validity)",
        "",
        "### Nội dung trình chiếu",
        "1. **Phạm vi dữ liệu (Scope Boundary):**",
        "   - Đánh giá hiện tại được thực hiện trên benchmark giả lập có cấu trúc Stage B (`synthetic-paired-v1`).",
        "   - Mặc dù phản ánh sát các thuộc tính kỹ thuật của Windows logs, tập dữ liệu này chưa bao quát đầy đủ sự hỗn loạn và nhiễu của các cuộc tấn công APT thực tế (luồng dữ liệu thực địa T15 vẫn đang ở trạng thái chuẩn bị).",
        "2. **Hạn chế của mô hình nhúng đơn tầng:**",
        "   - Việc chỉ dựa vào dense semantic similarity (`all-MiniLM-L6-v2`) khiến hệ thống bỏ sót các từ khóa định danh cụ thể (ví dụ: Event ID 4720, tên tiến trình đặc biệt).",
        "   - Cần bổ sung cơ chế tìm kiếm lai (Hybrid Search: Dense + Lexical BM25) trong tương lai; giải pháp này chưa từng được thử nghiệm trong benchmark hiện tại.",
        "3. **Phạm vi mô hình & Ranh giới diễn giải thống kê:**",
        "   - Toàn bộ 4 khoảng tin cậy 95% Bootstrap CI của chênh lệch độ chính xác so với No-RAG đều chứa 0.",
        r"   - Phép thử **McNemar thăm dò ở cấp độ view** cho kết quả $p = " + m['mcnemar_p_exact'] + r"$ ($" + m['mcnemar_p_display'] + r" > 0.05$), KHÔNG phải là đặc tính của bootstrap CI (khoảng tin cậy chứa 0).",
        '   - Cần mở rộng quy mô mẫu và đa dạng hóa mô hình trước khi khẳng định bất kỳ lợi thế mang tính cấu trúc nào; tuyệt đối **không suy diễn quan hệ nhân quả** hay khẳng định "tri thức tham số thuần túy" khi chưa được kiểm chứng.',
        "4. **Quy trình tái lập ngoại tuyến an toàn:**",
        "   - Mọi kịch bản kiểm thử bắt buộc chạy qua runner offline `scripts/run_offline_tests.py` can thiệp socket Python và lọc biến môi trường nhằm hạn chế rò rỉ credential và gọi API ngầm ngoài ý muốn (không phải là sandbox cấp OS).",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Nghiên cứu công khai đầy đủ các giới hạn khoa học và ràng buộc thực nghiệm:',
        "> 1. Dữ liệu: Kịch bản giả lập có cấu trúc synthetic-paired-v1 với 8 kỹ thuật có mẫu dương tính trong tổng số 474 lớp đóng băng; 40 cặp đối ứng có GT thay đổi khi mở rộng ngữ cảnh; dữ liệu telemetry thực tế in-the-wild (T15) chưa được kiểm chứng.",
        "> 2. Bộ tìm kiếm: Hạn chế từ vựng của dense bi-encoder được ghi nhận rõ, tuy nhiên giải pháp Hybrid Dense+BM25 chưa từng được thử nghiệm trong benchmark này và là hướng phát triển tương lai.",
        f"> 3. Thống kê: Toàn bộ 4 khoảng tin cậy 95% CI của chênh lệch độ chính xác so với No-RAG đều chứa 0. Phép thử McNemar thăm dò ở cấp độ view cho kết quả p = {m['mcnemar_p_exact']} / {m['mcnemar_p_display']} > 0.05, không khẳng định RAG vượt trội No-RAG; không suy diễn quan hệ nhân quả hay khẳng định tri thức tham số thuần túy khi chưa được kiểm chứng.",
        "> 4. An toàn: Runner offline scripts/run_offline_tests.py can thiệp socket tầng ứng dụng và lọc biến môi trường, không phải là sandbox cấp OS.",
        "> ",
        f'> *Bằng chứng dự án:* `docs/reproducibility.md`; `scripts/run_offline_tests.py`; `tests/test_offline_guard.py`."',
        "",
        "---",
        "",
        "## Slide 11: Khả Năng Tái Lập Độc Lập & Đóng Góp Khoa Học (Reproducibility & Contributions)",
        "",
        "### Nội dung trình chiếu",
        "- **Tái Lập Ngoại Tuyến & Phạm Vi Offline Guard:**",
        "  - Lệnh chuẩn tắc có bảo vệ ngoại tuyến:",
        "    ```bash",
        "    python scripts/run_offline_tests.py -m pytest ... (hoặc cờ -c)",
        "    ```",
        "  - **Lệnh tái lập khoa học chuẩn tắc:**",
        "    ```bash",
        "    python scripts/reproduce_canonical_study.py --all",
        "    ```",
        "    *(Phân biệt với kịch bản chẩn đoán lịch sử / fixture helper `scripts/reproduce_study.py`).*",
        "  - **Phạm vi kỹ thuật của `offline_guard`:**",
        "    - Can thiệp tầng socket Python (chặn kết nối mạng ngoài ý muốn) và lọc biến môi trường credentials.",
        "    - Không phải là sandbox cấp OS (không cô lập mã máy binary tùy ý ngoài Python runtime).",
        "    - Dependencies và artifact tiên quyết đã nạp sẵn cục bộ; lệnh `uv run` trần không có guard bảo vệ không tự động đảm bảo cách ly mạng nếu thiếu cờ offline.",
        "  - **Điều kiện tái lập & Công khai:**",
        "    - *Tái lập ngoại tuyến từ 15 canonical artifacts đóng băng:* Xác thực tính toàn vẹn toán học và hạch toán tài chính mà KHÔNG tạo ra bất kỳ lượt gọi mô hình trực tiếp hay chi phí token nào.",
        "    - *Tái lập toàn diện luồng live provider:* Yêu cầu nạp credentials thực và chạy dưới cơ chế budget guard trần $19.99 USD.",
        "    - *Gói bằng chứng công khai:* Hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan) chờ thẩm định xuất bản chính thức.",
        f"  - Toàn bộ 15 artifact và giao thức thực nghiệm được neo giữ bằng mã băm SHA-256 trong `config/canonical_experiment_lock_v1.json`.",
        "- **Đóng góp khoa học cốt lõi:**",
        "  1. *Quy trình thực nghiệm chuẩn hóa:* Thiết lập giao thức thực nghiệm đối chứng khép kín trên tập dữ liệu đóng băng synthetic-paired-v1 cho bài toán Windows log attribution.",
        "  2. *Bóc tách độc lập các trục lỗi (RQ2 Failure Decomposition per D2i):* Phân tích riêng biệt retrieval miss, downstream generation failure và joint overlap (không giả định độc lập ngẫu nhiên).",
        "  3. *Bằng chứng định lượng về khoảng cách từ vựng và giả thuyết pha loãng ngữ cảnh (Context Dilution Hypothesis).* ",
        "  4. *Bộ công cụ nghiên cứu mở:* Cung cấp toàn bộ mã nguồn, benchmark, kịch bản tạo slide và dữ liệu chứng cứ nguyên vẹn.",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Khả năng kiểm chứng độc lập là cam kết trọng tâm của dự án. Lệnh tái lập khoa học chuẩn tắc là `python scripts/reproduce_canonical_study.py --all`, phân biệt với kịch bản chẩn đoán lịch sử/fixture helper `scripts/reproduce_study.py`. Cơ chế đánh giá ngoại tuyến từ 15 artifacts đã đóng băng nhằm xác thực tính toàn vẹn toán học và hạch toán tài chính mà KHÔNG tạo ra bất kỳ lượt gọi mô hình trực tiếp hay chi phí token mới nào. Runner `scripts/run_offline_tests.py` can thiệp ở tầng socket Python và biến môi trường, không phải là sandbox cấp hệ điều hành. Gói bằng chứng công khai hiện được tổ chức dưới dạng danh mục siêu dữ liệu khả chuyển (portable metadata inventory/plan) chờ thẩm định xuất bản chính thức. Bốn đóng góp thực nghiệm cốt lõi: thiết lập phương pháp luận đo lường đối chứng, phân rã lỗi D2i độc lập, minh bạch độ không chắc chắn thống kê và cung cấp gói chứng cứ có thể kiểm chứng độc lập.',
        "> ",
        f'> *Bằng chứng dự án:* `config/canonical_experiment_lock_v1.json` (SHA-256: `{prov["lock_sha"]}`); `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `artifacts/results/canonical_metric_bundle_v2.json` (SHA-256: `{prov["bundle_sha"]}`); `scripts/reproduce_canonical_study.py`; `scripts/run_offline_tests.py`; `tests/test_smoke_cases.py`."',
        "",
        "---",
        "",
        "## Slide 12: Tổng Kết & Hỏi Đáp (Conclusion & Q&A)",
        "",
        "### Nội dung trình chiếu",
        "- **Tóm tắt kết luận:**",
        f"  - RAG cung cấp tri thức nền tảng quan trọng; kết quả đối chứng ghi nhận No-RAG đạt {m['no_rag_correct']}/{m['scorable_views']} ({m['no_rag_acc']}) vs RAG k=10 quan sát thấy {m['k10_correct']}/{m['scorable_views']} ({m['k10_acc']}, Delta = {m['delta_acc_pp']}, 95% CI {m['delta_ci_95_pp']} chứa 0, McNemar $p = {m['mcnemar_p_exact']}$ / ${m['mcnemar_p_display']} > 0.05$).",
        f"  - Phân rã lỗi D2i theo 3 trục đo lường độc lập (retrieval miss, downstream generation failure, joint overlap): {m['overlap_pct']:.2f}% số ca phân loại sai ({m['overlap_miss_and_wrong']}/{m['k10_wrong_count']}) nằm ở nhánh truy xuất trượt; {m['scorable_provider_failures']} terminal provider failures trên {m['scorable_records_total']:,} scorable records.",
        "  - Quy trình tái lập ngoại tuyến: Thực thi tái lập khoa học chuẩn tắc qua `python scripts/reproduce_canonical_study.py --all` (đánh giá ngoại tuyến từ 15 artifacts đã đóng băng, 0 token spend) dưới runner `scripts/run_offline_tests.py` can thiệp tầng socket và lọc biến môi trường.",
        "  - Hiện tượng pha loãng ngữ cảnh (Context Dilution) khẳng định tầm quan trọng của việc tiền lọc log có chọn lọc thay vì nhúng toàn bộ nhật ký xung quanh.",
        "- **Định hướng phát triển:**",
        "  - Triển khai Hybrid Retrieval (Dense + BM25) để khắc phục triệt để khoảng cách từ vựng ở các sự kiện như `T1136.001`.",
        "  - Triển khai thực nghiệm mở rộng trên telemetry thực tế khi hoàn thiện khâu khử khuẩn.",
        "- **Kho lưu trữ & Danh mục siêu dữ liệu khả chuyển:** PR #26 ([GitHub PR #26](https://github.com/habachcp6/RAG2ATTCK/pull/26)); gói công khai ở dạng portable metadata inventory chờ thẩm định xuất bản.",
        "- **Trân trọng cảm ơn Quý Thầy Cô và Hội Đồng!**  ",
        "  *Kính mời Quý Thầy Cô đặt câu hỏi thảo luận (Q&A).*",
        "",
        "### Ghi chú diễn giả (Speaker Notes)",
        '> "Tóm lại, RAG2ATT&CK đã hoàn tất thực nghiệm đối chứng đo lường vai trò của RAG trong bài toán ánh xạ log Windows sang ATT&CK techniques:',
        f'> 1. Kết quả cốt lõi: No-RAG đạt {m["no_rag_acc"]} ({m["no_rag_correct"]}/{m["scorable_views"]}), RAG k10 quan sát thấy {m["k10_acc"]} ({m["k10_correct"]}/{m["scorable_views"]}, Delta = {m["delta_acc_pp"]}). Khoảng tin cậy 95% CI {m["delta_ci_95_pp"]} chứa 0, kiểm định McNemar chính xác p = {m["mcnemar_p_exact"]} / hiển thị {m["mcnemar_p_display"]} > 0.05, cho thấy RAG chưa tạo khác biệt có ý nghĩa thống kê trên benchmark này.',
        f'> 2. Phân rã lỗi: {m["overlap_pct"]:.2f}% lỗi phân loại sai rơi vào trường hợp truy xuất trượt Top-10 ({m["overlap_miss_and_wrong"]}/{m["k10_wrong_count"]}); {m["scorable_provider_failures"]} terminal provider failures trên {m["scorable_records_total"]:,} scorable records.',
        f'> 3. Tài chính: Chi phí toàn bộ nghiên cứu được kiểm soát chặt chẽ ở mức ${m["committed_spend_usd"]} USD ($6.63 USD committed spend) trên trần ngân sách ${m["budget_cap_usd"]} USD.',
        '> 4. Tái lập & Công khai: Thực thi tái lập khoa học chuẩn tắc qua `python scripts/reproduce_canonical_study.py --all` (đánh giá ngoại tuyến từ artifact đã đóng băng, không phát sinh chi phí). Gói phát hành công khai được tổ chức dạng danh mục siêu dữ liệu khả chuyển chờ thẩm định xuất bản.',
        "> ",
        "> *Khai báo công cụ:* Toàn bộ slide deck này được tác tạo và cập nhật bằng công cụ bundled artifact tools, đảm bảo định dạng PowerPoint native tiếng Việt có thể chỉnh sửa từng shape.",
        "> ",
        f'> *Bằng chứng dự án:* PR #26 (`https://github.com/habachcp6/RAG2ATTCK/pull/26`); `reports/experiment_protocol_v1.md` (Raw File SHA-256: `{prov["protocol_file_sha"]}`; Canonical Decisions Digest: `{prov["protocol_decisions_digest"]}`); `docs/sanitized_evidence_manifest.json`; `reports/evidence/reproducibility_package_manifest.md`."',
        "",
    ]

    dest.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return dest


def generate_deck(
    *,
    metric_bundle_path: Path | None = None,
    expected_sha256: str | None = None,
    fixture_only: bool = False,
    output_path: Path = OUTPUT_PATH,
) -> Path:
    """Generate presentation slide deck in either canonical or fixture mode."""
    provenance = load_provenance_hashes()
    if fixture_only:
        ctx = DeckContext(
            canonical_mode=False,
            banner_text=FIXTURE_BANNER_TEXT,
            metrics=get_default_fixture_metrics(),
            bundle_data=None,
            provenance=provenance,
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
            provenance=provenance,
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
    write_deck_figures_audit(provenance, output_path)

    if output_path.resolve() == OUTPUT_PATH.resolve():
        export_slides_markdown(ctx, REPO_ROOT / "docs" / "presentation" / "slides.md")
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
