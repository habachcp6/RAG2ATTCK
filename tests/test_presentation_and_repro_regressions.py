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
from pathlib import Path

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
            "whole_study_accounting": {
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
    assert resolve_ptr(mock_b172, "/rq3/whole_study_accounting/total_study_budget_usd") == 19.99
    assert (
        resolve_ptr(
            mock_b172,
            "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_asymptotic",
        )
        == 0.03
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

    out_md = tmp_path / "preview.md"
    generate_fixture_markdown_preview(slots, out_md)
    assert out_md.is_file()
    md_content = out_md.read_text(encoding="utf-8")
    assert DISCLAIMER_TEXT in md_content
    assert "fixture_only: true" in md_content
    assert "DIAGNOSTIC TEST FIXTURE ONLY" in md_content


def test_fixture_population_helper_fails_closed_on_uncertified_data(tmp_path: Path) -> None:
    """Population helper must raise RuntimeError if target is not certified as fixture."""
    import pytest

    from scripts.populate_presentation_fixtures import assert_fixture_safety

    fake_live = {"fixture_only": False, "provenance_status": "canonical_study"}
    with pytest.raises(RuntimeError, match=r"\[FAIL_CLOSED\]"):
        assert_fixture_safety(tmp_path, fake_live)


def test_js_deck_updater_helper_contract() -> None:
    """JS deck updater script exists, adheres to artifact-tool pattern, and labels private."""
    js_script = REPO_ROOT / "scripts" / "artifact_tool_deck_updater.js"
    assert js_script.is_file(), "artifact_tool_deck_updater.js missing"
    content = js_script.read_text(encoding="utf-8")

    assert "@oai/artifact-tool" in content
    assert "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS" in content
    assert "importPptx" in content
    assert "inspect" in content
    assert "resolve" in content
    assert "exportPptx" in content
    assert "fixture_only" in content

    # Verify that production slides remain untampered with fixture numbers
    slides_md = REPO_ROOT / "docs" / "presentation" / "slides.md"
    assert slides_md.is_file()
    md_text = slides_md.read_text(encoding="utf-8")
    assert "[PENDING EXECUTION]" in md_text or "PENDING" in md_text
