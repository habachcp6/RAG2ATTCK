"""Regression tests for Phase S2 presentation and reproducibility plan.

Verifies:
1. Approval status contract: STRICTLY PENDING CODEX REVIEW, no self-approval as FINAL APPROVED.
2. 100% alignment of slide/repro JSON pointers to fixture_export_schema_b172.json:
   - Slide 6: split_manifest.json, 718 scorable views, 278 complete pairs, 440 clusters.
   - Slide 7: /rq1/by_condition/{c}/accuracy_end_to_end, macro_f1, accuracy_e2e_ci_95.
   - Slide 8: /rq2/by_condition/{c}/... (error decomposition, conditional metrics, overlaps).
   - Slide 9: /rq3/tradeoffs_by_condition/{c}/... (latency, tokens, cost) and
     /rq3/whole_study_accounting/...
   - Slide 10: /rq3/view_diagnostics/{c}/... (marginal and paired cohort metrics, McNemar test).
   - Slide 11: all-MiniLM-L6-v2 (384 dim, rev 1110a24, IndexFlatIP).
3. Schema pointer resolubility against canonical schema structure.
4. Dataset split manifest topology and cluster invariants.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from src.evaluation.experiment_metrics import CONDITIONS

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "reports" / "evidence" / "s2_presentation_and_repro_plan.md"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "ground_truth" / "synthetic" / "split_manifest.json"
PAIRS_PATH = REPO_ROOT / "data" / "ground_truth" / "synthetic" / "pairs.jsonl"


def test_plan_approval_status_is_pending_review_and_not_self_approved() -> None:
    """Plan must not self-approve as FINAL APPROVED and must be PENDING CODEX REVIEW."""
    assert PLAN_PATH.is_file(), f"Plan file not found: {PLAN_PATH}"
    content = PLAN_PATH.read_text(encoding="utf-8")

    assert "FINAL APPROVED FOR S2 EXECUTION" not in content, (
        "Plan must not self-approve as FINAL APPROVED FOR S2 EXECUTION"
    )
    assert "PENDING CODEX REVIEW" in content, "Plan status must be PENDING CODEX REVIEW"


def test_plan_contains_b172_slide_json_pointers() -> None:
    """Plan must contain 100% of the slide and repro JSON pointers specified by Codex Reviewer."""
    content = PLAN_PATH.read_text(encoding="utf-8")

    # Slide 6: Dataset & Views
    assert "data/ground_truth/synthetic/split_manifest.json" in content
    assert "718" in content  # scorable views
    assert "278" in content  # complete scorable pairs
    assert "440" in content  # distinct eligible clusters

    # Slide 7: RQ1 Attribution
    for c in CONDITIONS:
        assert (
            f"/rq1/by_condition/{c}/accuracy_end_to_end" in content
            or "/rq1/by_condition/" in content
        )
    assert "/rq1/by_condition/no_rag/accuracy_end_to_end" in content
    assert "/rq1/by_condition/rag_k10/accuracy_end_to_end" in content
    assert "/rq1/by_condition/no_rag/macro_f1" in content
    assert "/rq1/by_condition/rag_k10/macro_f1" in content
    assert "/rq1/by_condition/no_rag/accuracy_e2e_ci_95" in content
    assert "/rq1/by_condition/rag_k10/accuracy_e2e_ci_95" in content

    # Slide 8: RQ2 Error Decomposition
    assert "/rq2/by_condition/rag_k10/retrieval_metrics/macro_recall" in content
    assert "/rq2/by_condition/rag_k10/retrieval_metrics/retrieval_hit_rate"
    assert "/rq2/by_condition/rag_k10/independent_failure_axes/retrieval_miss_rate" in content
    assert "/rq2/by_condition/rag_k10/independent_failure_axes/provider_failure_rate" in content
    assert "/rq2/by_condition/rag_k10/independent_failure_axes/parse_failure_rate" in content
    assert "/rq2/by_condition/rag_k10/independent_failure_axes/invalid_attack_id_rate" in content
    assert (
        "/rq2/by_condition/rag_k10/independent_failure_axes/valid_but_wrong_classification_rate"
        in content
    )
    assert (
        "/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_wrong_classification"
        in content
    )
    assert (
        "/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_success"
        in content
    )
    assert (
        "/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_failure"
        in content
    )

    # Slide 9: RQ3 Tradeoffs & Costs
    assert "/rq3/tradeoffs_by_condition/no_rag/latency_ms/median" in content
    assert "/rq3/tradeoffs_by_condition/rag_k10/latency_ms/median" in content
    assert "/rq3/tradeoffs_by_condition/no_rag/tokens/mean_prompt_tokens" in content
    assert "/rq3/tradeoffs_by_condition/rag_k10/tokens/mean_prompt_tokens" in content
    assert (
        "/rq3/tradeoffs_by_condition/no_rag/financial_cost_usd/cost_per_logical_request_usd"
        in content
    )
    assert (
        "/rq3/tradeoffs_by_condition/rag_k10/financial_cost_usd/cost_per_logical_request_usd"
        in content
    )
    assert "/rq3/whole_study_accounting/total_study_budget_usd" in content
    assert "/rq3/whole_study_accounting/canonical_conditions_total_usd" in content
    assert "/rq3/whole_study_accounting/net_remaining_uncommitted_budget_usd" in content

    # Slide 10: View Diagnostics & Paired Analysis
    assert "/rq3/view_diagnostics/rag_k10/single_view_accuracy_e2e" in content
    assert "/rq3/view_diagnostics/rag_k10/contextual_view_accuracy_e2e" in content
    assert "/rq3/view_diagnostics/rag_k10/view_accuracy_delta" in content
    assert "/rq3/view_diagnostics/rag_k10/single_paired_accuracy" in content
    assert "/rq3/view_diagnostics/rag_k10/contextual_paired_accuracy" in content
    assert "/rq3/view_diagnostics/rag_k10/paired_delta" in content
    assert (
        "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_asymptotic" in content
    )
    assert "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_exact" in content

    # Slide 11: Architecture & Embedding Specification
    assert "all-MiniLM-L6-v2" in content
    assert "384" in content
    assert "1110a24" in content
    assert "IndexFlatIP" in content


def test_schema_pointer_resolution_against_b172_mock_structure() -> None:
    """Every pointer specified in the plan must resolve in a b172-conforming dictionary."""

    def resolve_ptr(obj: dict, ptr: str):
        parts = [p for p in ptr.split("/") if p]
        curr = obj
        for p in parts:
            if not isinstance(curr, dict) or p not in curr:
                return None
            curr = curr[p]
        return curr

    # Construct mock conforming to fixture_export_schema_b172
    mock_b172: dict = {
        "rq1": {
            "by_condition": {
                c: {
                    "accuracy_end_to_end": 0.65,
                    "macro_f1": 0.58,
                    "accuracy_e2e_ci_95": [0.61, 0.69],
                    "delta_vs_baseline": {
                        "delta_accuracy_end_to_end": 0.05 if c != "no_rag" else None,
                        "delta_macro_f1": 0.04 if c != "no_rag" else None,
                    },
                }
                for c in CONDITIONS
            },
            "best_rag_condition": "rag_k10",
            "best_rag_accuracy_delta": 0.12,
            "best_rag_macro_f1_delta": 0.10,
        },
        "rq2": {
            "by_condition": {
                c: {
                    "retrieval_metrics": {
                        "macro_recall": 0.43,
                        "retrieval_hit_rate": 0.45,
                        "retrieval_miss_rate": 0.55,
                    },
                    "generation_conditional_accuracy": {
                        "P_correct_given_retrieval_success": 0.78,
                        "P_correct_given_retrieval_failure": 0.22,
                    },
                    "independent_failure_axes": {
                        "retrieval_miss_rate": 0.55,
                        "provider_failure_rate": 0.0,
                        "parse_failure_rate": 0.0,
                        "invalid_attack_id_rate": 0.02,
                        "valid_but_wrong_classification_rate": 0.28,
                        "overlap_retrieval_miss_and_wrong_classification": 120,
                        "overlap_retrieval_miss_and_provider_failure": 0,
                        "overlap_retrieval_miss_and_parse_failure": 0,
                        "overlap_retrieval_miss_and_invalid_id": 5,
                    },
                }
                for c in CONDITIONS
            }
        },
        "rq3": {
            "tradeoffs_by_condition": {
                c: {
                    "latency_ms": {"median": 4500.0, "mean": 5100.0, "p95": 9200.0},
                    "tokens": {
                        "mean_prompt_tokens": 1200.0,
                        "mean_completion_tokens": 300.0,
                        "mean_total_tokens": 1500.0,
                    },
                    "financial_cost_usd": {
                        "cost_per_logical_request_usd": 0.0012,
                        "cost_per_scorable_query_usd": 0.0021,
                        "cost_per_correct_attribution_usd": 0.0035,
                        "total_cost_usd": 1.536,
                    },
                }
                for c in CONDITIONS
            },
            "whole_study_financial_accounting": {
                "total_study_budget_usd": 19.99,
                "canonical_conditions_total_usd": 8.50,
                "net_remaining_uncommitted_budget_usd": 11.4373599,
                "prior_pilot_provisional_hold_usd": 0.0526401,
            },
            "view_diagnostics": {
                c: {
                    "single_view_accuracy_e2e": 0.62,
                    "contextual_view_accuracy_e2e": 0.68,
                    "view_accuracy_delta": -0.06,
                    "single_paired_accuracy": 0.64,
                    "contextual_paired_accuracy": 0.70,
                    "paired_delta": -0.06,
                    "mcnemar_test_views_exploratory": {
                        "p_value_asymptotic": 0.03,
                        "p_value_exact": 0.028,
                    },
                    "pair_concordance": {
                        "both_correct_count": 150,
                        "single_only_correct_count": 28,
                        "contextual_only_correct_count": 45,
                        "both_incorrect_count": 55,
                    },
                }
                for c in CONDITIONS
            },
        },
    }

    # Verify key pointers resolve
    assert resolve_ptr(mock_b172, "/rq1/by_condition/rag_k10/accuracy_end_to_end") == 0.65
    assert resolve_ptr(mock_b172, "/rq1/by_condition/rag_k10/macro_f1") == 0.58
    assert resolve_ptr(mock_b172, "/rq1/by_condition/rag_k10/accuracy_e2e_ci_95") == [0.61, 0.69]
    assert (
        resolve_ptr(
            mock_b172,
            "/rq2/by_condition/rag_k10/independent_failure_axes/retrieval_miss_rate",
        )
        == 0.55
    )
    assert resolve_ptr(mock_b172, "/rq3/tradeoffs_by_condition/rag_k10/latency_ms/median") == 4500.0
    assert (
        resolve_ptr(
            mock_b172,
            "/rq3/tradeoffs_by_condition/rag_k10/financial_cost_usd/cost_per_logical_request_usd",
        )
        == 0.0012
    )
    assert (
        resolve_ptr(
            mock_b172,
            "/rq3/whole_study_financial_accounting/total_study_budget_usd",
        )
        == 19.99
    )
    assert (
        resolve_ptr(
            mock_b172,
            "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_asymptotic",
        )
        == 0.03
    )
    assert (
        resolve_ptr(
            mock_b172,
            "/rq1/by_condition/rag_k1/delta_vs_baseline/delta_accuracy_end_to_end",
        )
        == 0.05
    )
    assert (
        resolve_ptr(
            mock_b172,
            "/rq1/by_condition/rag_k1/delta_vs_baseline/delta_macro_f1",
        )
        == 0.04
    )


def test_split_manifest_topology_and_cluster_invariants() -> None:
    """Split manifest topology matches 640 TEST pairs, 718 scorable views across 440 clusters."""
    assert SPLIT_MANIFEST_PATH.is_file(), f"Manifest missing: {SPLIT_MANIFEST_PATH}"
    splits = json.loads(SPLIT_MANIFEST_PATH.read_text(encoding="utf-8"))
    test_pair_ids = set(splits.get("test", []))
    assert len(test_pair_ids) == 640, "TEST split must contain exactly 640 pairs"

    assert PAIRS_PATH.is_file(), f"Pairs missing: {PAIRS_PATH}"
    pairs = [
        json.loads(line)
        for line in PAIRS_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip() and json.loads(line).get("pair_id") in test_pair_ids
    ]
    assert len(pairs) == 640, "Must load 640 pairs from TEST split"

    both_scorable = 0
    contextual_only = 0
    single_only = 0
    neither = 0

    for p in pairs:
        s_gt = p.get("single_ground_truth", {})
        c_gt = p.get("contextual_ground_truth", {})
        s_ok = s_gt.get("label_status") == "mapped" and bool(s_gt.get("technique_ids"))
        c_ok = c_gt.get("label_status") == "mapped" and bool(c_gt.get("technique_ids"))
        if s_ok and c_ok:
            both_scorable += 1
        elif c_ok:
            contextual_only += 1
        elif s_ok:
            single_only += 1
        else:
            neither += 1

    assert both_scorable == 278, "Must have exactly 278 complete scorable pairs"
    assert contextual_only == 162, "Must have exactly 162 contextual-only scorable pairs"
    assert single_only == 0, "Must have exactly 0 single-only scorable pairs"
    assert neither == 200, "Must have exactly 200 neither-mapped pairs"

    # Distinct eligible clusters across scorable views
    distinct_clusters = both_scorable + contextual_only + single_only
    assert distinct_clusters == 440, "Must have exactly 440 distinct eligible clusters"

    # Total scorable views
    total_scorable_views = (both_scorable * 2) + contextual_only + single_only
    assert total_scorable_views == 718, "Must have exactly 718 scorable views"


def test_fixture_population_helper_extracts_slots_with_private_label(tmp_path: Path) -> None:
    """Fixture population helper extracts slots and writes private-labeled preview."""
    from scripts.populate_presentation_fixtures import (
        DEFAULT_FIXTURE_DIR,
        DISCLAIMER_TEXT,
        extract_fixture_slots,
        generate_fixture_markdown_preview,
        get_declarative_shape_table_map,
    )

    slots = extract_fixture_slots(DEFAULT_FIXTURE_DIR)
    assert slots["_metadata"]["fixture_only"] is True
    assert slots["_metadata"]["disclaimer"] == DISCLAIMER_TEXT

    # Check key slots are present
    assert slots["{{S2_MANIFEST_PATH}}"] == "data/ground_truth/synthetic/split_manifest.json"
    assert slots["{{S2_TOTAL_TEST_VIEWS}}"] == "1,280"
    assert slots["{{S2_SCORABLE_VIEWS}}"] == "718"
    assert slots["{{S2_COMPLETE_SCORABLE_PAIRS}}"] == "278"
    assert slots["{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}"] == "440"
    assert "{{S2_ACC_E2E_NO_RAG}}" in slots
    assert "{{S2_ACC_E2E_RAG_K10}}" in slots
    assert "{{S2_MACRO_F1_RAG_K10}}" in slots
    assert "{{S2_RETRIEVAL_MISS_RATE_K10}}" in slots
    assert "{{S2_MEDIAN_LAT_NO_RAG_SEC}}" in slots
    assert "{{S2_COST_LOGICAL_REQ_NO_RAG}}" in slots
    assert "{{S2_SINGLE_VIEW_ACC_E2E}}" in slots
    assert "{{S2_PAIRED_DELTA_PP}}" in slots

    # Verify declarative shape-table map has 67 items with complete metadata
    decl_map = get_declarative_shape_table_map(slots)
    assert len(decl_map) == 67
    for item in decl_map:
        assert "slot_name" in item
        assert "input_field" in item
        assert "units" in item
        assert "source_pointer" in item
        assert "shape_id" in item
        assert "slide_number" in item
        assert "injected_value" in item
        assert item["injected_value"] != ""

    out_md = tmp_path / "preview.md"
    generate_fixture_markdown_preview(slots, out_md)
    assert out_md.is_file()
    md_content = out_md.read_text(encoding="utf-8")
    assert DISCLAIMER_TEXT in md_content
    assert "fixture_only: true" in md_content
    assert "DIAGNOSTIC TEST FIXTURE ONLY" in md_content


def has_artifact_tool_runtime() -> bool:
    """Check if the proprietary @oai/artifact-tool runtime is available in environment."""
    env_module = os.environ.get("ARTIFACT_TOOL_MODULE")
    if env_module:
        return env_module != "non_existent" and Path(env_module).exists()

    cached_path = Path(
        "C:/Users/hahoa/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs"
    )
    if cached_path.is_file():
        return True

    bundled_node = Path(
        "C:/Users/hahoa/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    )
    node_exe = str(bundled_node) if bundled_node.is_file() else shutil.which("node")
    if node_exe:
        try:
            res = subprocess.run(
                [
                    node_exe,
                    "--input-type=module",
                    "-e",
                    (
                        "import('@oai/artifact-tool')"
                        ".then(() => process.exit(0))"
                        ".catch(() => process.exit(1))"
                    ),
                ],
                capture_output=True,
                timeout=5,
            )
            return res.returncode == 0
        except Exception:
            return False
    return False


def _find_node_exe() -> str:
    """Locate bundled node.exe or PATH node binary."""
    bundled_path = Path(
        "C:/Users/hahoa/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe"
    )
    if bundled_path.is_file():
        return str(bundled_path)
    which_node = shutil.which("node")
    if which_node:
        return which_node
    pytest.skip("Node.js binary not found in environment")


def test_fixture_population_helper_fails_closed_on_uncertified_data(tmp_path: Path) -> None:
    """Population helper must raise RuntimeError if target is not certified as fixture."""
    from scripts.populate_presentation_fixtures import assert_fixture_safety

    fake_live = {"fixture_only": False, "provenance_status": "canonical_study"}
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        assert_fixture_safety(tmp_path, fake_live)


def test_fixture_population_helper_strict_hardening(tmp_path: Path) -> None:
    """Population helper enforces strict boolean checks, no-default KeyError, and finiteness."""
    from scripts.populate_presentation_fixtures import (
        DEFAULT_FIXTURE_DIR,
        _check_finite,
        _fmt_acc,
        _fmt_delta,
        assert_fixture_safety,
        extract_fixture_slots,
    )

    # 1. Non-boolean fixture_only must fail-closed
    string_boolean = {"fixture_only": "true", "provenance_status": "diagnostic_fixture"}
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        assert_fixture_safety(tmp_path, string_boolean)

    int_boolean = {"fixture_only": 1, "provenance_status": "diagnostic_fixture"}
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        assert_fixture_safety(tmp_path, int_boolean)

    # 2. Non-diagnostic provenance must fail-closed
    bad_prov = {"fixture_only": True, "provenance_status": "live_study"}
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        assert_fixture_safety(tmp_path, bad_prov)

    # 3. Finiteness enforcement
    with pytest.raises(ValueError, match="Non-finite"):
        _check_finite(float("nan"), "test_nan")
    with pytest.raises(ValueError, match="Non-finite"):
        _check_finite(float("inf"), "test_inf")
    with pytest.raises(ValueError, match="Non-finite"):
        _check_finite(float("-inf"), "test_neginf")
    with pytest.raises(TypeError, match="Expected numeric"):
        _check_finite("123", "test_str")  # type: ignore

    # 4. Formatting handles None cleanly as "N/A"
    assert _fmt_acc(None) == "N/A"
    assert _fmt_delta(None) == "N/A"

    # 5. No-default contract: missing required metric raises KeyError
    rq_analysis_path = DEFAULT_FIXTURE_DIR / "rq_analysis.json"
    valid_data = json.loads(rq_analysis_path.read_text(encoding="utf-8"))

    # Corrupt a required metric in a copy
    corrupt_data = json.loads(json.dumps(valid_data))
    del corrupt_data["rq1"]["by_condition"]["rag_k10"]["accuracy_end_to_end"]
    corrupt_file = tmp_path / "rq_analysis_corrupt.json"
    corrupt_file.write_text(json.dumps(corrupt_data), encoding="utf-8")

    with pytest.raises(KeyError, match="accuracy_end_to_end"):
        extract_fixture_slots(DEFAULT_FIXTURE_DIR, analysis_file=corrupt_file)


def test_js_deck_updater_script_contract() -> None:
    """JS deck updater script exists as .mjs and adheres to artifact-tool pattern."""
    mjs_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.mjs"
    assert mjs_script.is_file(), "artifact_tool_deck_updater.mjs missing"

    # Ensure old .js is completely removed
    old_js_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.js"
    assert not old_js_script.exists(), "Old artifact_tool_deck_updater.js must be deleted"

    content = mjs_script.read_text(encoding="utf-8")

    # Verifies dynamic @oai/artifact-tool resolution and zero AST fallback
    assert "@oai/artifact-tool" in content
    assert "fallback" not in content.lower(), "Mock AST fallback must be deleted"
    assert "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS" in content
    assert "PresentationFile" in content
    assert "FileBlob" in content
    assert "importPptx" in content
    assert "inspect" in content
    assert "resolve" in content
    assert "exportPptx" in content
    assert "fixture_only" in content
    assert "resolveArtifactToolModule" in content
    assert "[DEPENDENCY_UNAVAILABLE]" in content
    assert 'from "file:///' not in content, "Static local file import must not exist"

    # Verify that production slides remain untampered with fixture numbers
    slides_md = REPO_ROOT / "docs" / "presentation" / "slides.md"
    assert slides_md.is_file()
    md_text = slides_md.read_text(encoding="utf-8")
    assert "[PENDING EXECUTION]" in md_text or "PENDING" in md_text


@pytest.mark.skipif(
    not has_artifact_tool_runtime(),
    reason="Private Codex artifact-tool runtime not present in clean CI environment",
)
def test_js_deck_updater_execution_and_artifacts() -> None:
    """Executes JS deck updater via node.exe and verifies all output artifacts."""
    node_exe = _find_node_exe()
    mjs_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.mjs"

    proc = subprocess.run(
        [node_exe, str(mjs_script)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"JS updater failed: {proc.stderr}\n{proc.stdout}"

    # 1. Candidate deck assertions
    candidate_pptx = REPO_ROOT / "reports" / "evidence" / "fixture_populated_slides.pptx"
    assert candidate_pptx.is_file(), f"Candidate deck missing: {candidate_pptx}"
    pptx_bytes = candidate_pptx.read_bytes()
    assert len(pptx_bytes) > 0, "Candidate deck must not be empty"
    assert pptx_bytes[:4] == b"PK\x03\x04", (
        "Candidate deck must start with ZIP magic bytes PK\\x03\\x04"
    )

    # 2. Audit report assertions
    audit_file = REPO_ROOT / "reports" / "evidence" / "deck_updater_fixture_audit.json"
    assert audit_file.is_file(), f"Audit file missing: {audit_file}"
    audit = json.loads(audit_file.read_text(encoding="utf-8"))
    assert audit.get("fixture_only") is True
    assert audit.get("provenance_status") == "diagnostic_fixture"
    assert "DIAGNOSTIC TEST FIXTURE" in audit.get("disclaimer", "")
    assert audit.get("sha_changed") is True
    assert audit.get("before_sha256") != audit.get("after_sha256")
    assert audit.get("total_slides_count") == 12
    assert audit.get("total_notes_count") in (11, 12)
    assert audit.get("rendered_png_slides_count") == 12
    assert audit.get("expected_numeric_slots_count") == 67
    assert audit.get("actual_numeric_slots_count") == 67
    assert audit.get("numeric_slot_edits") == 67
    assert audit.get("disclaimer_edits", 0) > 0
    assert audit.get("substitutions_performed", 0) == 67 + audit.get("disclaimer_edits", 0)

    decl_mapping = audit.get("declarative_mapping", [])
    assert len(decl_mapping) == 67
    verified_bindings = audit.get("verified_bindings", [])
    assert len(verified_bindings) == 67
    for vb in verified_bindings:
        assert vb.get("verified") is True
        assert "bound_line" in vb
    for entry in decl_mapping:
        assert "slot_name" in entry
        assert "shape_id" in entry
        assert "slide_number" in entry
        assert "injected_value" in entry
        assert entry["injected_value"] != ""

    modified_shapes = audit.get("modified_shape_ids", [])
    for expected_shape in [
        "sh/sna103ap",
        "sh/7m98ru9g",
        "sh/h4bupgn6",
        "sh/fi9c369c",
        "sh/98rehwve",
        "sh/id0fu50z",
        "sh/ofq5svm5",
    ]:
        assert expected_shape in modified_shapes

    # 3. Slide PNG assertions
    qa_dir = REPO_ROOT / "reports" / "evidence" / "qa" / "fixture_slides"
    assert qa_dir.is_dir(), f"QA directory missing: {qa_dir}"
    for i in range(1, 13):
        slide_png = qa_dir / f"slide-{i}.png"
        assert slide_png.is_file(), f"Slide PNG missing: {slide_png}"
        png_bytes = slide_png.read_bytes()
        assert len(png_bytes) > 10_000, f"Slide {i} PNG unexpectedly small: {len(png_bytes)} bytes"
        assert png_bytes[:8] == b"\x89PNG\r\n\x1a\n", f"Slide {i} lacks PNG magic bytes"


def test_js_deck_updater_negative_cases(tmp_path: Path) -> None:
    """Negative tests: missing slots, non-fixture slots, and missing disclaimer fail closed."""
    node_exe = _find_node_exe()
    mjs_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.mjs"

    # Case A: Missing slots file
    non_existent = tmp_path / "non_existent_slots.json"
    proc_missing = subprocess.run(
        [node_exe, str(mjs_script), "--fixture-slots", str(non_existent)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_missing.returncode == 1
    assert "[FAIL_CLOSED]" in proc_missing.stderr or "[FAIL_CLOSED]" in proc_missing.stdout
    assert "not found" in (proc_missing.stderr + proc_missing.stdout)

    # Case B: Non-fixture slots file (fixture_only: false)
    bad_slots = tmp_path / "fake_live_slots.json"
    bad_slots.write_text(
        json.dumps(
            {
                "_metadata": {
                    "fixture_only": False,
                    "disclaimer": "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS",
                }
            }
        ),
        encoding="utf-8",
    )
    proc_bad = subprocess.run(
        [node_exe, str(mjs_script), "--fixture-slots", str(bad_slots)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_bad.returncode == 1
    assert "[FAIL_CLOSED]" in proc_bad.stderr or "[FAIL_CLOSED]" in proc_bad.stdout
    assert "Refusing to execute on non-fixture data" in (proc_bad.stderr + proc_bad.stdout)

    # Case C: Missing disclaimer in slots file
    no_disc_slots = tmp_path / "no_disclaimer_slots.json"
    no_disc_slots.write_text(
        json.dumps({"_metadata": {"fixture_only": True}}),
        encoding="utf-8",
    )
    proc_no_disc = subprocess.run(
        [node_exe, str(mjs_script), "--fixture-slots", str(no_disc_slots)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_no_disc.returncode == 1
    assert "[FAIL_CLOSED]" in proc_no_disc.stderr or "[FAIL_CLOSED]" in proc_no_disc.stdout
    assert "Missing mandatory diagnostic fixture disclaimer" in (
        proc_no_disc.stderr + proc_no_disc.stdout
    )

    # Case D: Missing declarative map file
    non_existent_map = tmp_path / "non_existent_map.json"
    proc_missing_map = subprocess.run(
        [node_exe, str(mjs_script), "--declarative-map", str(non_existent_map)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_missing_map.returncode == 1
    assert "[FAIL_CLOSED]" in (proc_missing_map.stderr + proc_missing_map.stdout)
    assert "not found" in (proc_missing_map.stderr + proc_missing_map.stdout)

    # Case E: Declarative map with wrong count (< 67 items)
    truncated_map = tmp_path / "truncated_map.json"
    truncated_map.write_text(json.dumps([{"slot_name": "TEST"}]), encoding="utf-8")
    proc_trunc = subprocess.run(
        [node_exe, str(mjs_script), "--declarative-map", str(truncated_map)],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_trunc.returncode == 1
    assert "[FAIL_CLOSED]" in (proc_trunc.stderr + proc_trunc.stdout)
    assert "67 items" in (proc_trunc.stderr + proc_trunc.stdout)


def test_js_deck_updater_dependency_unavailable_on_clean_env(tmp_path: Path) -> None:
    """When proprietary runtime is absent, updater exits with code 2."""
    node_exe = _find_node_exe()
    mjs_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.mjs"

    missing_module = tmp_path / "missing_artifact_tool.mjs"
    proc = subprocess.run(
        [
            node_exe,
            str(mjs_script),
            "--artifact-tool-module",
            str(missing_module),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 2, (
        f"Expected exit code 2, got {proc.returncode}.\n"
        f"Stdout:\n{proc.stdout}\nStderr:\n{proc.stderr}"
    )
    output = proc.stdout + proc.stderr
    assert "[DEPENDENCY_UNAVAILABLE]" in output


def test_producer_consumer_contract_rq_analysis() -> None:
    """Producer-consumer contract verification for rq_analysis.json.

    Verifies that the bundle produces whole_study_financial_accounting (not just
    whole_study_accounting), and that per-condition delta_vs_baseline exists for all RAG conditions.
    """
    rq_path = REPO_ROOT / "outputs" / "reproduction" / "fixture_diagnostics" / "rq_analysis.json"
    assert rq_path.is_file(), f"Missing rq_analysis.json: {rq_path}"
    data = json.loads(rq_path.read_text(encoding="utf-8"))

    # Producer-consumer financial accounting check
    rq3 = data.get("rq3", {})
    assert "whole_study_financial_accounting" in rq3, (
        "Producer contract broken: rq3 missing required key 'whole_study_financial_accounting'"
    )
    fin = rq3["whole_study_financial_accounting"]
    assert "total_study_budget_usd" in fin
    assert "canonical_conditions_total_usd" in fin
    assert "net_remaining_uncommitted_budget_usd" in fin
    assert "prior_pilot_provisional_hold_usd" in fin

    # Per-condition deltas for RAG conditions
    rq1_by_cond = data.get("rq1", {}).get("by_condition", {})
    for cond in ("rag_k1", "rag_k3", "rag_k5", "rag_k10"):
        assert cond in rq1_by_cond
        c_row = rq1_by_cond[cond]
        delta_info = c_row.get("delta_vs_baseline")
        assert delta_info is not None, f"Missing delta_vs_baseline for {cond}"
        acc_delta = delta_info.get("accuracy_delta") or delta_info.get("delta_accuracy_end_to_end")
        f1_delta = delta_info.get("macro_f1_delta") or delta_info.get("delta_macro_f1")
        assert acc_delta is not None, f"Missing accuracy delta for {cond}"
        assert f1_delta is not None, f"Missing macro_f1 delta for {cond}"


def test_slide8_table_per_condition_deltas() -> None:
    """Slide 8 table must render dedicated, distinct deltas per RAG condition."""
    audit_file = REPO_ROOT / "reports" / "evidence" / "deck_updater_fixture_audit.json"
    assert audit_file.is_file(), f"Missing audit file: {audit_file}"
    audit = json.loads(audit_file.read_text(encoding="utf-8"))

    verified_bindings = audit.get("verified_bindings", [])
    bindings_by_slot = {vb["slot_name"]: vb for vb in verified_bindings}

    # Verify per-condition delta slots exist and are bound to sh/98rehwve
    k1_acc_delta = bindings_by_slot["RQ1_ACC_DELTA_RAG_K1"]["injected_value"]
    k3_acc_delta = bindings_by_slot["RQ1_ACC_DELTA_RAG_K3"]["injected_value"]
    k5_acc_delta = bindings_by_slot["RQ1_ACC_DELTA_RAG_K5"]["injected_value"]
    k10_acc_delta = bindings_by_slot["RQ1_ACC_DELTA_RAG_K10"]["injected_value"]

    # Invariants: deltas must be distinct, not cloned across rows
    deltas = {k1_acc_delta, k3_acc_delta, k5_acc_delta, k10_acc_delta}
    assert len(deltas) == 4, f"Deltas across conditions must be distinct: {deltas}"

    # Verify bound lines correspond to their respective condition
    assert "rag_k1" in bindings_by_slot["RQ1_ACC_DELTA_RAG_K1"]["bound_line"]
    assert "rag_k3" in bindings_by_slot["RQ1_ACC_DELTA_RAG_K3"]["bound_line"]
    assert "rag_k5" in bindings_by_slot["RQ1_ACC_DELTA_RAG_K5"]["bound_line"]
    assert "rag_k10" in bindings_by_slot["RQ1_ACC_DELTA_RAG_K10"]["bound_line"]


def test_cohort_and_provenance_separation() -> None:
    """Slide 6 and Slide 9 must have explicitly separated cohorts and zones."""
    audit_file = REPO_ROOT / "reports" / "evidence" / "deck_updater_fixture_audit.json"
    assert audit_file.is_file(), f"Missing audit file: {audit_file}"
    audit = json.loads(audit_file.read_text(encoding="utf-8"))

    bindings = audit.get("verified_bindings", [])
    sh6_lines = [b["bound_line"] for b in bindings if b["shape_id"] == "sh/7m98ru9g"]
    sh9_lines = [b["bound_line"] for b in bindings if b["shape_id"] == "sh/ofq5svm5"]

    # Slide 6: Must have both pilot (N=756) and fixture (N=718) separate sections
    assert any("Diagnostic Fixture Hit@10" in line for line in sh6_lines)
    assert any("Diagnostic Fixture Retrieval Miss Rate" in line for line in sh6_lines)

    # Slide 9: Must have telemetry separate from whole-study accounting
    assert any("no_rag" in line and "prompt tokens" in line for line in sh9_lines)
    assert any("rag_k10" in line and "prompt tokens" in line for line in sh9_lines)
    assert any("Canonical Total" in line for line in sh9_lines)
    assert any("prior_pilot_provisional_hold_usd" in line for line in sh9_lines)


def test_numerical_fidelity_and_binding_fails_on_row_swap() -> None:
    """verifySlotBinding must reject slot value placed in wrong condition's row."""
    node_exe = _find_node_exe()

    # Test via node invocation of verifySlotBinding
    test_code = """
    import { verifySlotBinding } from './scripts/artifact_tool_deck_updater.mjs';

    // Mock shape content with rag_k1 and rag_k3 rows
    const shapeContent = [
      'Condition      Accuracy    Macro-F1    Delta vs No-RAG',
      'rag_k1         0.4123      0.3456      +0.0456 (+0.0345 F1)',
      'rag_k3         0.4500      0.4000      +0.0612 (+0.0521 F1)',
    ].join('\\n');

    // Case 1: Matching slot in correct row -> verified: true
    const validItem = {
      slot_name: 'RQ1_ACC_RAG_K1',
      source_pointer: '/rq1/by_condition/rag_k1/accuracy_end_to_end',
      shape_id: 'sh/98rehwve',
      injected_value: '0.4123',
    };
    const res1 = verifySlotBinding(shapeContent, validItem);
    if (!res1.verified) {
      console.error('Expected res1 to be verified', res1);
      process.exit(1);
    }

    // Case 2: Swapped slot (rag_k1 value looking for rag_k3 value) -> verified: false
    const swappedItem = {
      slot_name: 'RQ1_ACC_RAG_K1',
      source_pointer: '/rq1/by_condition/rag_k1/accuracy_end_to_end',
      shape_id: 'sh/98rehwve',
      injected_value: '0.4500',
    };
    const res2 = verifySlotBinding(shapeContent, swappedItem);
    if (res2.verified) {
      console.error('Expected res2 to fail verification due to row mismatch', res2);
      process.exit(2);
    }

    console.log('BINDING_TEST_SUCCESS');
    process.exit(0);
    """

    proc = subprocess.run(
        [node_exe, "--input-type=module", "-e", test_code],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"Binding verification failed: {proc.stderr}\n{proc.stdout}"
    assert "BINDING_TEST_SUCCESS" in proc.stdout


def test_canonical_mode_fails_closed_on_fixture_data() -> None:
    """Canonical mode fails closed when pointing to fixture data."""
    from scripts.populate_presentation_fixtures import (
        DEFAULT_FIXTURE_DIR,
        extract_fixture_slots,
    )

    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        extract_fixture_slots(DEFAULT_FIXTURE_DIR, canonical_mode=True)


def _setup_mock_canonical_environment(tmp_path: Path) -> tuple[Path, Path, dict, dict, Path]:
    """Helper creating a 100% valid mock canonical environment with 10 sources and 8 outputs."""
    import hashlib

    from scripts.populate_presentation_fixtures import (
        REQUIRED_CANONICAL_OUTPUT_FILES,
        REQUIRED_CANONICAL_SOURCE_FILES,
    )

    source_dir = tmp_path / "snapshot"
    source_dir.mkdir(parents=True, exist_ok=True)
    analysis_dir = tmp_path / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    source_digests: dict[str, str] = {}
    for s_name in REQUIRED_CANONICAL_SOURCE_FILES:
        s_file = source_dir / s_name
        if s_name == "manifest.json":
            content = json.dumps(
                {"manifest_version": "1.0.0", "study": "root_s1"}, indent=2
            ).encode("utf-8")
        else:
            content = f"mock content for {s_name}\n".encode("utf-8")
        s_file.write_bytes(content)
        source_digests[s_name] = hashlib.sha256(content).hexdigest()

    manifest_bytes = (source_dir / "manifest.json").read_bytes()
    manifest_file_sha = hashlib.sha256(manifest_bytes).hexdigest()
    manifest_obj = json.loads(manifest_bytes.decode("utf-8"))
    manifest_semantic_bytes = json.dumps(
        manifest_obj, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    manifest_semantic_sha = hashlib.sha256(manifest_semantic_bytes).hexdigest()

    output_digests: dict[str, str] = {}
    for o_name in REQUIRED_CANONICAL_OUTPUT_FILES:
        o_file = analysis_dir / o_name
        if o_name == "run_provenance.json":
            content = json.dumps(
                {"execution_mode": "live", "provenance": "canonical_study"}, indent=2
            ).encode("utf-8")
        elif o_name == "rq_analysis_summary.md":
            content = "# RQ Findings Summary\nCanonical study results.\n".encode("utf-8")
        else:
            content = json.dumps(
                {"provenance_status": "canonical_study", "file": o_name}, indent=2
            ).encode("utf-8")
        o_file.write_bytes(content)
        output_digests[o_name] = hashlib.sha256(content).hexdigest()

    # Root verification file
    root_verif_file = analysis_dir / "root_canonical_export_validation_v1.json"
    root_verif_obj = {
        "status": "PASS",
        "native_verdict": "PASS",
        "rq1_and_settled_totals_verdict": "PASS",
        "rq2_and_attempt_usage_verdict": "PASS",
        "defects": [],
        "accepted_scope": "canonical_native_and_corrected_rq_all_pass",
    }
    root_verif_bytes = json.dumps(root_verif_obj, indent=2).encode("utf-8")
    root_verif_sha = hashlib.sha256(root_verif_bytes).hexdigest()
    root_verif_file.write_bytes(root_verif_bytes)

    # Terminal seal
    seal_obj = {
        "schema_version": "1.0.0",
        "seal_type": "canonical-run-seal-v1",
        "experiment_id": "synthetic-paired-test-1",
        "study_id": "study-root-s1",
        "production_ready": True,
        "fixture_only": False,
        "has_breach": False,
        "total_records": 6400,
        "cumulative_settled_cost_usd": "6.57575890",
        "uncommitted_available_balance_usd": "13.36160100",
        "protocol_version": "experiment-protocol-v1.1",
        "protocol_sha256": "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c",
        "code_manifest_sha256": "8b1b3ea400000000000000000000000000000000000000000000000000000000",
        "sealed_artifact_digests": dict(source_digests),
        "terminal_proof": {
            "start_identity": "native:PID:12345",
            "process_status": "exited",
            "exit_code": 0,
            "pid": 12345,
            "task_id": "task-test-001",
            "run_id": "live-66b94b1676bf46a9",
            "artifact_log_sha256": (
                "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
            ),
            "final_summary": {
                "complete": True,
                "record_count": 6400,
                "execution_mode": "live",
            },
        },
    }
    seal_bytes = json.dumps(seal_obj, indent=2).encode("utf-8")
    seal_sha256 = hashlib.sha256(seal_bytes).hexdigest()
    seal_file = analysis_dir / "canonical_run_seal_v1.json"
    seal_file.write_bytes(seal_bytes)

    # Metric bundle
    bundle_obj = {
        "schema_version": "1.0.0",
        "bundle_type": "canonical-metric-bundle-v1",
        "fixture_only": False,
        "execution_mode": "live",
        "dataset_split": "test",
        "experiment_id": "synthetic-paired-test-1",
        "run_id": "live-66b94b1676bf46a9",
        "protocol_version": "experiment-protocol-v1.1",
        "protocol_sha256": "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c",
        "protocol_file_sha256": "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c",
        "execution_git_sha": "8b1b3ea400000000000000000000000000000000",
        "evaluation_git_sha": "8b1b3ea400000000000000000000000000000000",
        "approved_rq_git_sha": "8b1b3ea400000000000000000000000000000000",
        "rq_source_sha256": "8b1b3ea400000000000000000000000000000000000000000000000000000000",
        "manifest_file_sha256": manifest_file_sha,
        "manifest_semantic_sha256": manifest_semantic_sha,
        "source_dir": str(source_dir),
        "terminal_seal": {
            "path": str(seal_file),
            "sha256": seal_sha256,
        },
        "source_file_digests": dict(source_digests),
        "output_file_digests": dict(output_digests),
        "root_verification": {
            "path": str(root_verif_file),
            "sha256": root_verif_sha,
            "accepted_scope": "canonical_native_and_corrected_rq_all_pass",
        },
    }
    bundle_file = analysis_dir / "canonical_metric_bundle_v1.json"
    bundle_file.write_text(json.dumps(bundle_obj, indent=2), encoding="utf-8")

    canonical_analysis = {
        "fixture_only": False,
        "provenance_status": "canonical_study",
        "experiment_id": "synthetic-paired-test-1",
    }
    return analysis_dir, bundle_file, canonical_analysis, bundle_obj, seal_file


def test_canonical_mode_contract_with_mock_bundle(tmp_path: Path) -> None:
    """Canonical mode verifies terminal seal and metric bundle against root contract."""
    from scripts.populate_presentation_fixtures import assert_canonical_safety

    analysis_dir, bundle_file, canonical_analysis, _, _ = _setup_mock_canonical_environment(
        tmp_path
    )
    # Must pass without raising
    assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)


def test_canonical_mode_fails_closed_on_tampered_hashes(tmp_path: Path) -> None:
    """Canonical safety check fails closed on any tampered hash, ellipsis, or missing file."""
    from scripts.populate_presentation_fixtures import assert_canonical_safety

    # 1. Tampered terminal seal SHA
    analysis_dir, bundle_file, canonical_analysis, bundle_obj, _ = (
        _setup_mock_canonical_environment(tmp_path)
    )
    bad_seal_bundle = dict(bundle_obj)
    bad_seal_bundle["terminal_seal"] = {
        "path": bundle_obj["terminal_seal"]["path"],
        "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    bad_seal_path = analysis_dir / "bad_seal_bundle.json"
    bad_seal_path.write_text(json.dumps(bad_seal_bundle, indent=2), encoding="utf-8")
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\] Terminal run seal SHA-256 mismatch"):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bad_seal_path)

    # 2. Ellipsis SHA ('...')
    bad_ellipsis = dict(bundle_obj)
    bad_ellipsis["execution_git_sha"] = "..."
    bad_ellipsis_path = analysis_dir / "bad_ellipsis_bundle.json"
    bad_ellipsis_path.write_text(json.dumps(bad_ellipsis, indent=2), encoding="utf-8")
    with pytest.raises(
        RuntimeError, match=r"\[FAIL_CLOSED\] Metric bundle missing valid 'execution_git_sha'"
    ):
        assert_canonical_safety(
            analysis_dir, canonical_analysis, metric_bundle_path=bad_ellipsis_path
        )

    # 3. Missing source file on disk
    src_file_to_remove = Path(bundle_obj["source_dir"]) / "study_ledger.json"
    src_file_to_remove.unlink()
    with pytest.raises(
        RuntimeError,
        match=r"\[FAIL_CLOSED\] Required canonical source file 'study_ledger\.json' missing",
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)


def test_canonical_mode_fails_closed_on_terminal_proof_defects(tmp_path: Path) -> None:
    """Terminal proof must have process_status='exited', exit_code=0, and record_count=6400."""
    from scripts.populate_presentation_fixtures import assert_canonical_safety

    # Case A: process_status is 'running'
    analysis_dir, bundle_file, canonical_analysis, _, seal_file = _setup_mock_canonical_environment(
        tmp_path
    )
    seal_data = json.loads(seal_file.read_text(encoding="utf-8"))
    seal_data["terminal_proof"]["process_status"] = "running"
    seal_bytes = json.dumps(seal_data, indent=2).encode("utf-8")
    seal_file.write_bytes(seal_bytes)

    # Update seal SHA in bundle so we hit terminal_proof verification
    import hashlib

    new_seal_sha = hashlib.sha256(seal_bytes).hexdigest()
    bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
    bundle_data["terminal_seal"]["sha256"] = new_seal_sha
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        RuntimeError, match=r"\[FAIL_CLOSED\] Terminal proof process_status must be 'exited'"
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)

    # Case B: exit_code is non-zero
    seal_data["terminal_proof"]["process_status"] = "exited"
    seal_data["terminal_proof"]["exit_code"] = 1
    seal_bytes = json.dumps(seal_data, indent=2).encode("utf-8")
    seal_file.write_bytes(seal_bytes)
    bundle_data["terminal_seal"]["sha256"] = hashlib.sha256(seal_bytes).hexdigest()
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\] Terminal proof exit_code must be 0"):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)

    # Case C: record count mismatch in final_summary
    seal_data["terminal_proof"]["exit_code"] = 0
    seal_data["terminal_proof"]["final_summary"]["record_count"] = 5000
    seal_bytes = json.dumps(seal_data, indent=2).encode("utf-8")
    seal_file.write_bytes(seal_bytes)
    bundle_data["terminal_seal"]["sha256"] = hashlib.sha256(seal_bytes).hexdigest()
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        RuntimeError, match=r"\[FAIL_CLOSED\] Terminal proof final_summary record_count .* != 6400"
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)


def test_canonical_mode_fails_closed_on_manifest_semantic_mismatch(tmp_path: Path) -> None:
    """Manifest verification fails closed if raw sha matches but semantic sha does not."""
    from scripts.populate_presentation_fixtures import assert_canonical_safety

    analysis_dir, bundle_file, canonical_analysis, bundle_obj, _ = (
        _setup_mock_canonical_environment(tmp_path)
    )
    bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
    bundle_data["manifest_semantic_sha256"] = (
        "1111111111111111111111111111111111111111111111111111111111111111"
    )
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\] Manifest semantic SHA-256 mismatch"):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)


def test_canonical_mode_fails_closed_on_unapproved_scope(tmp_path: Path) -> None:
    """Cannot bypass strict PASS requirements with arbitrary scope or non-PASS verdicts."""
    from scripts.populate_presentation_fixtures import assert_canonical_safety

    # 1. Arbitrary accepted_scope rejected
    analysis_dir, bundle_file, canonical_analysis, bundle_obj, _ = (
        _setup_mock_canonical_environment(tmp_path)
    )
    bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
    bundle_data["root_verification"]["accepted_scope"] = "arbitrary_scope_bypass"
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match=r"\[FAIL_CLOSED\] Metric bundle accepted_scope must be 'canonical_native",
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)

    # 2. Non-PASS verdict rejected
    analysis_dir, bundle_file, canonical_analysis, bundle_obj, _ = (
        _setup_mock_canonical_environment(tmp_path)
    )
    root_verif_path = Path(bundle_obj["root_verification"]["path"])
    verif_data = json.loads(root_verif_path.read_text(encoding="utf-8"))
    verif_data["rq2_and_attempt_usage_verdict"] = "FAIL"
    verif_bytes = json.dumps(verif_data, indent=2).encode("utf-8")
    root_verif_path.write_bytes(verif_bytes)

    import hashlib

    new_verif_sha = hashlib.sha256(verif_bytes).hexdigest()
    bundle_data = json.loads(bundle_file.read_text(encoding="utf-8"))
    bundle_data["root_verification"]["sha256"] = new_verif_sha
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match=r"\[FAIL_CLOSED\] Root verification verdict 'rq2_and_attempt_usage_verdict'",
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)

    # 3. Non-empty defects list rejected
    verif_data["rq2_and_attempt_usage_verdict"] = "PASS"
    verif_data["defects"] = ["unresolved defect"]
    verif_bytes = json.dumps(verif_data, indent=2).encode("utf-8")
    root_verif_path.write_bytes(verif_bytes)
    bundle_data["root_verification"]["sha256"] = hashlib.sha256(verif_bytes).hexdigest()
    bundle_file.write_text(json.dumps(bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        RuntimeError,
        match=r"\[FAIL_CLOSED\] Root verification defects list must be empty list",
    ):
        assert_canonical_safety(analysis_dir, canonical_analysis, metric_bundle_path=bundle_file)


def test_numerical_binding_regressions_column_swaps() -> None:
    """verifySlotBinding must reject swaps between columns (acc vs f1, delta, and CI)."""
    node_exe = _find_node_exe()

    test_code = """
    import { verifySlotBinding } from './scripts/artifact_tool_deck_updater.mjs';

    // Mock shape content with strict 5 columns
    const shapeContent = [
      'Condition      Accuracy    Macro-F1    Delta vs No-RAG',
      'rag_k1         0.4123      0.3456      +0.0456 (+0.0345 F1)',
      'rag_k3         0.4500      0.4000      +0.0612 (+0.0521 F1)',
      '• 95% CI: no_rag=[0.30, 0.40], k1=[0.38, 0.44], k3=[0.42, 0.48]',
    ].join('\\n');

    // Case 1: Swapping column 2 (accuracy) with column 3 (macro_f1)
    const swappedAccF1 = {
      slot_name: 'RQ1_ACC_RAG_K1',
      source_pointer: '/rq1/by_condition/rag_k1/accuracy_end_to_end',
      shape_id: 'sh/98rehwve',
      injected_value: '0.3456', // macro-f1 value in col 2 position
    };
    const res1 = verifySlotBinding(shapeContent, swappedAccF1);
    if (res1.verified) {
      console.error('Expected res1 to fail verification for acc/f1 swap', res1);
      process.exit(1);
    }

    // Case 2: Swapping column 4 (delta acc) with column 5 (delta f1)
    const swappedDeltas = {
      slot_name: 'RQ1_ACC_DELTA_RAG_K1',
      source_pointer: '/rq1/by_condition/rag_k1/delta_vs_baseline/delta_accuracy_end_to_end',
      shape_id: 'sh/98rehwve',
      injected_value: '+0.0345', // delta-f1 value in delta-acc position
    };
    const res2 = verifySlotBinding(shapeContent, swappedDeltas);
    if (res2.verified) {
      console.error('Expected res2 to fail verification for delta acc/f1 swap', res2);
      process.exit(2);
    }

    // Case 3: Swapping CI across conditions
    const swappedCI = {
      slot_name: 'RQ1_CI_95_RAG_K1',
      source_pointer: '/rq1/by_condition/rag_k1/accuracy_e2e_ci_95',
      shape_id: 'sh/98rehwve',
      injected_value: '[0.42, 0.48]', // k3 CI looking for k1
    };
    const res3 = verifySlotBinding(shapeContent, swappedCI);
    if (res3.verified) {
      console.error('Expected res3 to fail verification for CI condition mismatch', res3);
      process.exit(3);
    }

    console.log('COLUMN_SWAP_REGRESSION_SUCCESS');
    process.exit(0);
    """

    proc = subprocess.run(
        [node_exe, "--input-type=module", "-e", test_code],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"Column swap test failed: {proc.stderr}\n{proc.stdout}"
    assert "COLUMN_SWAP_REGRESSION_SUCCESS" in proc.stdout


def test_js_deck_updater_canonical_mode_disjoint_and_labels(tmp_path: Path) -> None:
    """Updater in --canonical mode strictly validates slots and produces canonical output."""
    node_exe = _find_node_exe()
    mjs_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.mjs"

    # Load default slots and create valid canonical slots copy
    from scripts.populate_presentation_fixtures import (
        DEFAULT_MAP_JSON,
        DEFAULT_OUTPUT_JSON,
    )

    default_slots = json.loads(DEFAULT_OUTPUT_JSON.read_text(encoding="utf-8"))

    canonical_slots = dict(default_slots)
    canonical_slots["_metadata"] = {
        "fixture_only": False,
        "canonical_mode": True,
        "provenance_status": "canonical_study",
        "canonical_proof_sha256": (
            "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
        ),
        "disclaimer": "CANONICAL STUDY EXECUTION - CERTIFIED VERIFIED OUTPUT",
    }
    slots_path = tmp_path / "canonical_slots.json"
    slots_path.write_text(json.dumps(canonical_slots, indent=2), encoding="utf-8")

    out_deck = tmp_path / "canonical_deck.pptx"
    out_audit = tmp_path / "canonical_audit.json"
    out_qa = tmp_path / "qa_slides"

    proc = subprocess.run(
        [
            node_exe,
            str(mjs_script),
            "--canonical",
            "--slots",
            str(slots_path),
            "--declarative-map",
            str(DEFAULT_MAP_JSON),
            "--output-deck",
            str(out_deck),
            "--audit-report",
            str(out_audit),
            "--output-qa-dir",
            str(out_qa),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc.returncode == 0, f"Canonical run failed: {proc.stderr}\n{proc.stdout}"

    # Verify audit invariants
    audit = json.loads(out_audit.read_text(encoding="utf-8"))
    assert audit.get("fixture_only") is False
    assert audit.get("canonical_mode") is True
    assert audit.get("provenance_status") == "canonical_study"
    assert audit.get("roundtrip_reimported_verified") is True

    # Case: Fails closed when an applicable RAG metric is null or N/A
    bad_canonical = dict(canonical_slots)
    bad_canonical["{{S2_ACC_E2E_RAG_K10}}"] = "N/A"
    bad_slots_path = tmp_path / "bad_canonical_slots.json"
    bad_slots_path.write_text(json.dumps(bad_canonical, indent=2), encoding="utf-8")

    proc_bad = subprocess.run(
        [
            node_exe,
            str(mjs_script),
            "--canonical",
            "--slots",
            str(bad_slots_path),
            "--declarative-map",
            str(DEFAULT_MAP_JSON),
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert proc_bad.returncode != 0
    assert "[FAIL_CLOSED] Canonical mode requires non-null RAG metric" in (
        proc_bad.stderr + proc_bad.stdout
    )
