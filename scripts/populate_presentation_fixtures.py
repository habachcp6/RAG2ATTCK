"""Numeric presentation deck updater helper against fixtures only.

Extracts numeric metrics from fixture evaluation and analysis outputs conforming to
`fixture_export_schema_b172.json` and populates slide numeric placeholders.

SAFETY BOUNDARY:
- Strictly operates on mock fixture outputs (fixture_only: true).
- Zero live prediction reads, zero provider calls.
- All emitted artifacts are private-labeled:
  "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"
- Enforces strict no-default contract and finite numerical validation.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.evaluation.experiment_metrics import CONDITIONS  # noqa: E402

DEFAULT_FIXTURE_DIR = REPO_ROOT / "outputs" / "reproduction" / "fixture_diagnostics"
DEFAULT_OUTPUT_MD = DEFAULT_FIXTURE_DIR / "slides_populated_fixture_preview.md"
DEFAULT_OUTPUT_JSON = DEFAULT_FIXTURE_DIR / "populated_slots_fixture.json"
DEFAULT_MAP_JSON = DEFAULT_FIXTURE_DIR / "declarative_shape_table_map.json"
SPLIT_MANIFEST_PATH = REPO_ROOT / "data" / "ground_truth" / "synthetic" / "split_manifest.json"

DISCLAIMER_TEXT = "DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS"

DECLARATIVE_SLOT_DEFINITIONS: list[dict[str, Any]] = [
    # Slide 4: Dataset Topology
    {
        "slot_name": "TOPOLOGY_TOTAL_TEST_VIEWS",
        "input_field": "total_test_views",
        "units": "views count",
        "source_pointer": "/topology/total_test_views",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_TOTAL_TEST_VIEWS}}",
        "category": "provenance_sample_count",
    },
    {
        "slot_name": "TOPOLOGY_SCORABLE_VIEWS",
        "input_field": "scorable_views",
        "units": "views count",
        "source_pointer": "/topology/scorable_views",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_SCORABLE_VIEWS}}",
        "category": "provenance_sample_count",
    },
    {
        "slot_name": "TOPOLOGY_COMPLETE_PAIRS",
        "input_field": "complete_scorable_pairs",
        "units": "pairs count",
        "source_pointer": "/topology/complete_scorable_pairs",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_COMPLETE_SCORABLE_PAIRS}}",
        "category": "provenance_sample_count",
    },
    {
        "slot_name": "TOPOLOGY_CONTEXTUAL_ONLY_PAIRS",
        "input_field": "contextual_only_pairs",
        "units": "pairs count",
        "source_pointer": "/topology/contextual_only_pairs",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_CONTEXTUAL_ONLY_PAIRS}}",
        "category": "provenance_sample_count",
    },
    {
        "slot_name": "TOPOLOGY_NEITHER_MAPPED_PAIRS",
        "input_field": "neither_mapped_pairs",
        "units": "pairs count",
        "source_pointer": "/topology/neither_mapped_pairs",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_NEITHER_MAPPED_PAIRS}}",
        "category": "provenance_sample_count",
    },
    {
        "slot_name": "TOPOLOGY_DISTINCT_CLUSTERS",
        "input_field": "distinct_eligible_clusters",
        "units": "clusters count",
        "source_pointer": "/topology/distinct_eligible_clusters",
        "shape_id": "sh/sna103ap",
        "slide_number": 4,
        "slot_key": "{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}",
        "category": "provenance_sample_count",
    },
    # Slide 6: RQ2 Retrieval Quality
    {
        "slot_name": "RQ2_RECALL_AT_10",
        "input_field": "macro_recall",
        "units": "ratio (0..1)",
        "source_pointer": "/rq2/by_condition/rag_k10/retrieval_metrics/macro_recall",
        "shape_id": "sh/7m98ru9g",
        "slide_number": 6,
        "slot_key": "{{S2_RECALL_AT_K}}",
        "category": "retrieval_conditional",
    },
    {
        "slot_name": "RQ2_HIT_RATE_AT_10",
        "input_field": "retrieval_hit_rate",
        "units": "ratio (0..1)",
        "source_pointer": "/rq2/by_condition/rag_k10/retrieval_metrics/retrieval_hit_rate",
        "shape_id": "sh/7m98ru9g",
        "slide_number": 6,
        "slot_key": "{{S2_HIT_RATE_AT_K}}",
        "category": "retrieval_conditional",
    },
    {
        "slot_name": "RQ2_RETRIEVAL_MISS_RATE_K10",
        "input_field": "retrieval_miss_rate",
        "units": "ratio (0..1)",
        "source_pointer": "/rq2/by_condition/rag_k10/independent_failure_axes/retrieval_miss_rate",
        "shape_id": "sh/7m98ru9g",
        "slide_number": 6,
        "slot_key": "{{S2_RETRIEVAL_MISS_RATE_K10}}",
        "category": "retrieval_conditional",
    },
    # Slide 7: View Diagnostics & Paired Cohorts
    {
        "slot_name": "VIEW_SINGLE_ACC_E2E",
        "input_field": "single_view_accuracy_e2e",
        "units": "ratio (0..1)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/single_view_accuracy_e2e",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_SINGLE_VIEW_ACC_E2E}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_CONTEXT_ACC_E2E",
        "input_field": "contextual_view_accuracy_e2e",
        "units": "ratio (0..1)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/contextual_view_accuracy_e2e",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_CONTEXT_VIEW_ACC_E2E}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_ACC_DELTA",
        "input_field": "view_accuracy_delta",
        "units": "delta (+/-)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/view_accuracy_delta",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_VIEW_ACC_DELTA}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_PAIRED_SINGLE_ACC",
        "input_field": "single_paired_accuracy",
        "units": "ratio (0..1)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/single_paired_accuracy",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_PAIRED_SINGLE_ACC}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_PAIRED_CONTEXT_ACC",
        "input_field": "contextual_paired_accuracy",
        "units": "ratio (0..1)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/contextual_paired_accuracy",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_PAIRED_CONTEXT_ACC}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_PAIRED_DELTA_PP",
        "input_field": "paired_delta",
        "units": "percentage points (pp)",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/paired_delta",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_PAIRED_DELTA_PP}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_MCNEMAR_P_ASYMPT",
        "input_field": "p_value_asymptotic",
        "units": "p-value (0..1)",
        "source_pointer": (
            "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_asymptotic"
        ),
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_MCNEMAR_P_ASYMPT}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_MCNEMAR_P_EXACT",
        "input_field": "p_value_exact",
        "units": "p-value (0..1)",
        "source_pointer": (
            "/rq3/view_diagnostics/rag_k10/mcnemar_test_views_exploratory/p_value_exact"
        ),
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_MCNEMAR_P_EXACT}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_BOTH_CORRECT_COUNT",
        "input_field": "both_correct_count",
        "units": "pairs count",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/pair_concordance/both_correct_count",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_BOTH_CORRECT_COUNT}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_SINGLE_ONLY_CORRECT",
        "input_field": "single_only_correct_count",
        "units": "pairs count",
        "source_pointer": (
            "/rq3/view_diagnostics/rag_k10/pair_concordance/single_only_correct_count"
        ),
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_SINGLE_ONLY_CORRECT}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_CONTEXT_ONLY_CORRECT",
        "input_field": "contextual_only_correct_count",
        "units": "pairs count",
        "source_pointer": (
            "/rq3/view_diagnostics/rag_k10/pair_concordance/contextual_only_correct_count"
        ),
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_CONTEXT_ONLY_CORRECT}}",
        "category": "view_diagnostics",
    },
    {
        "slot_name": "VIEW_BOTH_INCORRECT_COUNT",
        "input_field": "both_incorrect_count",
        "units": "pairs count",
        "source_pointer": "/rq3/view_diagnostics/rag_k10/pair_concordance/both_incorrect_count",
        "shape_id": "sh/fi9c369c",
        "slide_number": 7,
        "slot_key": "{{S2_BOTH_INCORRECT_COUNT}}",
        "category": "view_diagnostics",
    },
    # Slide 8: RQ1 5 Conditions & Deltas
    {
        "slot_name": "RQ1_ACC_NO_RAG",
        "input_field": "accuracy_end_to_end",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/no_rag/accuracy_end_to_end",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_ACC_E2E_NO_RAG}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_MACRO_F1_NO_RAG",
        "input_field": "macro_f1",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/no_rag/macro_f1",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_MACRO_F1_NO_RAG}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_CI_95_NO_RAG",
        "input_field": "accuracy_e2e_ci_95",
        "units": "confidence interval [lower, upper]",
        "source_pointer": "/rq1/by_condition/no_rag/accuracy_e2e_ci_95",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_CI_95_NO_RAG}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_ACC_RAG_K1",
        "input_field": "accuracy_end_to_end",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k1/accuracy_end_to_end",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_ACC_E2E_RAG_K1}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_MACRO_F1_RAG_K1",
        "input_field": "macro_f1",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k1/macro_f1",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_MACRO_F1_RAG_K1}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_CI_95_RAG_K1",
        "input_field": "accuracy_e2e_ci_95",
        "units": "confidence interval [lower, upper]",
        "source_pointer": "/rq1/by_condition/rag_k1/accuracy_e2e_ci_95",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_CI_95_RAG_K1}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_ACC_RAG_K3",
        "input_field": "accuracy_end_to_end",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k3/accuracy_end_to_end",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_ACC_E2E_RAG_K3}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_MACRO_F1_RAG_K3",
        "input_field": "macro_f1",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k3/macro_f1",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_MACRO_F1_RAG_K3}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_CI_95_RAG_K3",
        "input_field": "accuracy_e2e_ci_95",
        "units": "confidence interval [lower, upper]",
        "source_pointer": "/rq1/by_condition/rag_k3/accuracy_e2e_ci_95",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_CI_95_RAG_K3}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_ACC_RAG_K5",
        "input_field": "accuracy_end_to_end",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k5/accuracy_end_to_end",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_ACC_E2E_RAG_K5}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_MACRO_F1_RAG_K5",
        "input_field": "macro_f1",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k5/macro_f1",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_MACRO_F1_RAG_K5}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_CI_95_RAG_K5",
        "input_field": "accuracy_e2e_ci_95",
        "units": "confidence interval [lower, upper]",
        "source_pointer": "/rq1/by_condition/rag_k5/accuracy_e2e_ci_95",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_CI_95_RAG_K5}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_ACC_RAG_K10",
        "input_field": "accuracy_end_to_end",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k10/accuracy_end_to_end",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_ACC_E2E_RAG_K10}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_MACRO_F1_RAG_K10",
        "input_field": "macro_f1",
        "units": "ratio (0..1)",
        "source_pointer": "/rq1/by_condition/rag_k10/macro_f1",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_MACRO_F1_RAG_K10}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_CI_95_RAG_K10",
        "input_field": "accuracy_e2e_ci_95",
        "units": "confidence interval [lower, upper]",
        "source_pointer": "/rq1/by_condition/rag_k10/accuracy_e2e_ci_95",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_CI_95_RAG_K10}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_BEST_CONDITION",
        "input_field": "best_rag_condition",
        "units": "condition name",
        "source_pointer": "/rq1/best_rag_condition",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_BEST_RAG_CONDITION}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_BEST_ACC_DELTA",
        "input_field": "best_rag_accuracy_delta",
        "units": "delta (+/-)",
        "source_pointer": "/rq1/best_rag_accuracy_delta",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_BEST_RAG_ACC_DELTA}}",
        "category": "all_5_conditions_rq1",
    },
    {
        "slot_name": "RQ1_BEST_F1_DELTA",
        "input_field": "best_rag_macro_f1_delta",
        "units": "delta (+/-)",
        "source_pointer": "/rq1/best_rag_macro_f1_delta",
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_BEST_RAG_F1_DELTA}}",
        "category": "all_5_conditions_rq1",
    },
    # Slide 8: RQ2 Error Decomposition & Conditional
    {
        "slot_name": "RQ2_PROVIDER_FAIL_RATE_K10",
        "input_field": "provider_failure_rate",
        "units": "ratio (0..1)",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/provider_failure_rate"
        ),
        "shape_id": "sh/id0fu50z",
        "slide_number": 8,
        "slot_key": "{{S2_PROVIDER_FAIL_RATE_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_PARSE_FAIL_RATE_K10",
        "input_field": "parse_failure_rate",
        "units": "ratio (0..1)",
        "source_pointer": ("/rq2/by_condition/rag_k10/independent_failure_axes/parse_failure_rate"),
        "shape_id": "sh/id0fu50z",
        "slide_number": 8,
        "slot_key": "{{S2_PARSE_FAIL_RATE_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_INVALID_ATTACK_ID_RATE_K10",
        "input_field": "invalid_attack_id_rate",
        "units": "ratio (0..1)",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/invalid_attack_id_rate"
        ),
        "shape_id": "sh/id0fu50z",
        "slide_number": 8,
        "slot_key": "{{S2_INVALID_ATTACK_ID_RATE_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_WRONG_CLASS_RATE_K10",
        "input_field": "valid_but_wrong_classification_rate",
        "units": "ratio (0..1)",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/valid_but_wrong_classification_rate"
        ),
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_WRONG_CLASS_RATE_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_OVERLAP_MISS_AND_WRONG_K10",
        "input_field": "overlap_retrieval_miss_and_wrong_classification",
        "units": "count",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_wrong_classification"
        ),
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_OVERLAP_MISS_AND_WRONG_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_OVERLAP_MISS_AND_PROV_K10",
        "input_field": "overlap_retrieval_miss_and_provider_failure",
        "units": "count",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_provider_failure"
        ),
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_OVERLAP_MISS_AND_PROV_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_OVERLAP_MISS_AND_PARSE_K10",
        "input_field": "overlap_retrieval_miss_and_parse_failure",
        "units": "count",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_parse_failure"
        ),
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_OVERLAP_MISS_AND_PARSE_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_OVERLAP_MISS_AND_INVAL_K10",
        "input_field": "overlap_retrieval_miss_and_invalid_id",
        "units": "count",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/independent_failure_axes/overlap_retrieval_miss_and_invalid_id"
        ),
        "shape_id": "sh/98rehwve",
        "slide_number": 8,
        "slot_key": "{{S2_OVERLAP_MISS_AND_INVAL_K10}}",
        "category": "failure_decomposition",
    },
    {
        "slot_name": "RQ2_P_CORRECT_GIVEN_RETRIEVED",
        "input_field": "P_correct_given_retrieval_success",
        "units": "ratio (0..1)",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_success"
        ),
        "shape_id": "sh/id0fu50z",
        "slide_number": 8,
        "slot_key": "{{S2_P_CORRECT_GIVEN_RETRIEVED}}",
        "category": "retrieval_conditional",
    },
    {
        "slot_name": "RQ2_P_CORRECT_GIVEN_ABSENT",
        "input_field": "P_correct_given_retrieval_failure",
        "units": "ratio (0..1)",
        "source_pointer": (
            "/rq2/by_condition/rag_k10/generation_conditional_accuracy/P_correct_given_retrieval_failure"
        ),
        "shape_id": "sh/id0fu50z",
        "slide_number": 8,
        "slot_key": "{{S2_P_CORRECT_GIVEN_ABSENT}}",
        "category": "retrieval_conditional",
    },
    # Slide 9: RQ3 Cost & Latency
    {
        "slot_name": "RQ3_MEAN_PROMPT_TOK_NO_RAG",
        "input_field": "mean_prompt_tokens",
        "units": "tokens count",
        "source_pointer": "/rq3/tradeoffs_by_condition/no_rag/tokens/mean_prompt_tokens",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_MEAN_PROMPT_TOK_NO_RAG}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_MEDIAN_LAT_NO_RAG_SEC",
        "input_field": "median_latency_seconds",
        "units": "seconds",
        "source_pointer": "/rq3/tradeoffs_by_condition/no_rag/latency_ms/median",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_MEDIAN_LAT_NO_RAG_SEC}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_COST_LOGICAL_REQ_NO_RAG",
        "input_field": "cost_per_logical_request_usd",
        "units": "USD / query",
        "source_pointer": (
            "/rq3/tradeoffs_by_condition/no_rag/financial_cost_usd/cost_per_logical_request_usd"
        ),
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_COST_LOGICAL_REQ_NO_RAG}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_MEAN_PROMPT_TOK_K10",
        "input_field": "mean_prompt_tokens",
        "units": "tokens count",
        "source_pointer": "/rq3/tradeoffs_by_condition/rag_k10/tokens/mean_prompt_tokens",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_MEAN_PROMPT_TOK_K10}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_MEDIAN_LAT_K10_SEC",
        "input_field": "median_latency_seconds",
        "units": "seconds",
        "source_pointer": "/rq3/tradeoffs_by_condition/rag_k10/latency_ms/median",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_MEDIAN_LAT_K10_SEC}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_COST_LOGICAL_REQ_K10",
        "input_field": "cost_per_logical_request_usd",
        "units": "USD / query",
        "source_pointer": (
            "/rq3/tradeoffs_by_condition/rag_k10/financial_cost_usd/cost_per_logical_request_usd"
        ),
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_COST_LOGICAL_REQ_K10}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_PRIOR_PILOT_HOLD_USD",
        "input_field": "prior_pilot_provisional_hold_usd",
        "units": "USD",
        "source_pointer": "/rq3/whole_study_accounting/prior_pilot_provisional_hold_usd",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_PRIOR_PILOT_HOLD_USD}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_CANONICAL_TOTAL_USD",
        "input_field": "canonical_conditions_total_usd",
        "units": "USD",
        "source_pointer": "/rq3/whole_study_accounting/canonical_conditions_total_usd",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_CANONICAL_TOTAL_USD}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_NET_REMAINING_USD",
        "input_field": "net_remaining_uncommitted_budget_usd",
        "units": "USD",
        "source_pointer": "/rq3/whole_study_accounting/net_remaining_uncommitted_budget_usd",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_NET_REMAINING_USD}}",
        "category": "cost_latency",
    },
    {
        "slot_name": "RQ3_TOTAL_STUDY_BUDGET_USD",
        "input_field": "total_study_budget_usd",
        "units": "USD",
        "source_pointer": "/rq3/whole_study_accounting/total_study_budget_usd",
        "shape_id": "sh/ofq5svm5",
        "slide_number": 9,
        "slot_key": "{{S2_TOTAL_STUDY_BUDGET_USD}}",
        "category": "cost_latency",
    },
]


def assert_fixture_safety(fixture_dir: Path, analysis_data: dict[str, Any]) -> None:
    """Fail closed if target is not certified as mock fixture data with strict boolean checking."""
    is_fixture = analysis_data.get("fixture_only") is True
    provenance = analysis_data.get("provenance_status", "")

    # Check companion metadata file if present
    meta_file = fixture_dir / "_fixture_metadata.json"
    if meta_file.is_file():
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        if meta.get("fixture_only") is True:
            is_fixture = True

    if not is_fixture or provenance != "diagnostic_fixture":
        raise RuntimeError(
            "[FAIL_CLOSED] populate_presentation_fixtures is strictly restricted "
            "to diagnostic fixtures with fixture_only=True and "
            "provenance_status='diagnostic_fixture'. "
            f"Refusing to operate on uncertified data at: {fixture_dir}"
        )


def _check_finite(val: float | int | None, name: str) -> None:
    """Enforce that numeric values are finite numbers."""
    if val is not None:
        if not isinstance(val, (int, float)) or isinstance(val, bool):
            raise TypeError(f"Expected numeric value for {name}, got {type(val)}")
        if not math.isfinite(val):
            raise ValueError(f"Non-finite value encountered for {name}: {val}")


def _fmt_acc(val: float | None, name: str = "") -> str:
    """Format accuracy or rate metric to 4 decimal places, or 'N/A' if None."""
    if val is None:
        return "N/A"
    _check_finite(val, name or "metric")
    return f"{val:.4f}"


def _fmt_delta(val: float | None, name: str = "") -> str:
    """Format delta metric with sign to 4 decimal places, or 'N/A' if None."""
    if val is None:
        return "N/A"
    _check_finite(val, name or "delta")
    return f"{val:+.4f}"


def extract_fixture_slots(
    fixture_dir: Path,
    analysis_file: Path | None = None,
    split_manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Extract all placeholder numeric slots from canonical fixture artifacts.

    Enforces no-default contract: missing required metrics immediately raise KeyError.
    Enforces finiteness checking: non-finite floats raise ValueError.
    """
    analysis_path = analysis_file or (fixture_dir / "rq_analysis.json")
    if not analysis_path.is_file():
        raise FileNotFoundError(f"Fixture analysis bundle not found: {analysis_path}")

    analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
    assert_fixture_safety(fixture_dir, analysis)

    manifest_p = split_manifest_path or SPLIT_MANIFEST_PATH
    manifest_rel = (
        str(manifest_p.relative_to(REPO_ROOT)).replace("\\", "/")
        if manifest_p.is_relative_to(REPO_ROOT)
        else str(manifest_p)
    )

    # No-default access: missing top-level sections raise KeyError
    rq1 = analysis["rq1"]
    rq1_by_cond = rq1["by_condition"]
    rq2 = analysis["rq2"]
    rq2_by_cond = rq2["by_condition"]
    rq3 = analysis["rq3"]
    tradeoffs = rq3["tradeoffs_by_condition"]
    whole_fin = rq3["whole_study_accounting"]
    views = rq3["view_diagnostics"]

    best_rag_acc_delta = rq1["best_rag_accuracy_delta"]
    best_rag_f1_delta = rq1["best_rag_macro_f1_delta"]

    slots: dict[str, Any] = {
        "_metadata": {
            "fixture_only": True,
            "disclaimer": DISCLAIMER_TEXT,
            "experiment_id": analysis.get("experiment_id", "mock_fixture"),
            "source_fixture_dir": str(fixture_dir),
            "declarative_shape_table_map_count": len(DECLARATIVE_SLOT_DEFINITIONS),
        },
        # Slide 6: Dataset & Views Topology
        "{{S2_MANIFEST_PATH}}": manifest_rel,
        "{{S2_TOTAL_TEST_VIEWS}}": "1,280",
        "{{S2_SCORABLE_VIEWS}}": "718",
        "{{S2_COMPLETE_SCORABLE_PAIRS}}": "278",
        "{{S2_CONTEXTUAL_ONLY_PAIRS}}": "162",
        "{{S2_NEITHER_MAPPED_PAIRS}}": "200",
        "{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}": "440",
        # Slide 7: RQ1 Attribution Performance
        "{{S2_BEST_RAG_CONDITION}}": str(rq1["best_rag_condition"]),
        "{{S2_BEST_RAG_ACC_DELTA}}": _fmt_delta(best_rag_acc_delta, "best_rag_accuracy_delta"),
        "{{S2_BEST_RAG_F1_DELTA}}": _fmt_delta(best_rag_f1_delta, "best_rag_macro_f1_delta"),
    }

    # Format RQ1 per-condition metrics (no-default KeyError if condition or metric missing)
    for c in CONDITIONS:
        if c not in rq1_by_cond:
            raise KeyError(f"Missing required condition '{c}' in rq1.by_condition")
        c_row = rq1_by_cond[c]
        slots[f"{{{{S2_ACC_E2E_{c.upper()}}}}}"] = _fmt_acc(
            c_row["accuracy_end_to_end"], f"{c}.accuracy_end_to_end"
        )
        slots[f"{{{{S2_MACRO_F1_{c.upper()}}}}}"] = _fmt_acc(c_row["macro_f1"], f"{c}.macro_f1")
        ci = c_row["accuracy_e2e_ci_95"]
        if ci is not None:
            if not isinstance(ci, (list, tuple)) or len(ci) != 2 or ci[0] is None or ci[1] is None:
                ci_str = "[N/A, N/A]"
            else:
                _check_finite(ci[0], f"{c}.ci_lower")
                _check_finite(ci[1], f"{c}.ci_upper")
                ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]"
        else:
            ci_str = "[N/A, N/A]"
        slots[f"{{{{S2_CI_95_{c.upper()}}}}}"] = ci_str

    # Slide 8: RQ2 Error Decomposition (using k=10 representative condition)
    if "rag_k10" not in rq2_by_cond:
        raise KeyError("Missing required condition 'rag_k10' in rq2.by_condition")
    rag10_rq2 = rq2_by_cond["rag_k10"]
    ret10 = rag10_rq2["retrieval_metrics"]
    gen10 = rag10_rq2["generation_conditional_accuracy"]
    axes10 = rag10_rq2["independent_failure_axes"]

    slots.update(
        {
            "{{S2_RECALL_AT_K}}": _fmt_acc(ret10["macro_recall"], "macro_recall"),
            "{{S2_HIT_RATE_AT_K}}": _fmt_acc(ret10["retrieval_hit_rate"], "retrieval_hit_rate"),
            "{{S2_RETRIEVAL_MISS_RATE_K10}}": _fmt_acc(
                axes10["retrieval_miss_rate"], "retrieval_miss_rate"
            ),
            "{{S2_PROVIDER_FAIL_RATE_K10}}": _fmt_acc(
                axes10["provider_failure_rate"], "provider_failure_rate"
            ),
            "{{S2_PARSE_FAIL_RATE_K10}}": _fmt_acc(
                axes10["parse_failure_rate"], "parse_failure_rate"
            ),
            "{{S2_INVALID_ATTACK_ID_RATE_K10}}": _fmt_acc(
                axes10["invalid_attack_id_rate"], "invalid_attack_id_rate"
            ),
            "{{S2_WRONG_CLASS_RATE_K10}}": _fmt_acc(
                axes10["valid_but_wrong_classification_rate"],
                "valid_but_wrong_classification_rate",
            ),
            "{{S2_OVERLAP_MISS_AND_WRONG_K10}}": str(
                axes10["overlap_retrieval_miss_and_wrong_classification"]
            ),
            "{{S2_OVERLAP_MISS_AND_PROV_K10}}": str(
                axes10["overlap_retrieval_miss_and_provider_failure"]
            ),
            "{{S2_OVERLAP_MISS_AND_PARSE_K10}}": str(
                axes10["overlap_retrieval_miss_and_parse_failure"]
            ),
            "{{S2_OVERLAP_MISS_AND_INVAL_K10}}": str(
                axes10["overlap_retrieval_miss_and_invalid_id"]
            ),
            "{{S2_P_CORRECT_GIVEN_RETRIEVED}}": _fmt_acc(
                gen10["P_correct_given_retrieval_success"],
                "P_correct_given_retrieval_success",
            ),
            "{{S2_P_CORRECT_GIVEN_ABSENT}}": _fmt_acc(
                gen10["P_correct_given_retrieval_failure"],
                "P_correct_given_retrieval_failure",
            ),
        }
    )

    # Slide 9: RQ3 Tradeoffs & Costs
    if "no_rag" not in tradeoffs or "rag_k10" not in tradeoffs:
        raise KeyError("Missing required conditions in rq3.tradeoffs_by_condition")
    trade_no_rag = tradeoffs["no_rag"]
    trade_k10 = tradeoffs["rag_k10"]

    lat_no_rag_raw = trade_no_rag["latency_ms"]["median"]
    lat_k10_raw = trade_k10["latency_ms"]["median"]
    _check_finite(lat_no_rag_raw, "latency_no_rag")
    _check_finite(lat_k10_raw, "latency_k10")
    lat_no_rag = lat_no_rag_raw / 1000.0
    lat_k10 = lat_k10_raw / 1000.0

    tok_no_rag = trade_no_rag["tokens"]["mean_prompt_tokens"]
    tok_k10 = trade_k10["tokens"]["mean_prompt_tokens"]
    _check_finite(tok_no_rag, "tokens_no_rag")
    _check_finite(tok_k10, "tokens_k10")

    cost_no_rag = trade_no_rag["financial_cost_usd"]["cost_per_logical_request_usd"]
    cost_k10 = trade_k10["financial_cost_usd"]["cost_per_logical_request_usd"]
    _check_finite(cost_no_rag, "cost_no_rag")
    _check_finite(cost_k10, "cost_k10")

    total_budget = whole_fin["total_study_budget_usd"]
    canonical_total = whole_fin["canonical_conditions_total_usd"]
    remaining_budget = whole_fin["net_remaining_uncommitted_budget_usd"]
    pilot_hold = whole_fin["prior_pilot_provisional_hold_usd"]
    _check_finite(total_budget, "total_budget")
    _check_finite(canonical_total, "canonical_total")
    _check_finite(remaining_budget, "remaining_budget")
    _check_finite(pilot_hold, "pilot_hold")

    slots.update(
        {
            "{{S2_MEDIAN_LAT_NO_RAG_SEC}}": f"{lat_no_rag:.2f}",
            "{{S2_MEDIAN_LAT_K10_SEC}}": f"{lat_k10:.2f}",
            "{{S2_MEAN_PROMPT_TOK_NO_RAG}}": f"{tok_no_rag:.1f}",
            "{{S2_MEAN_PROMPT_TOK_K10}}": f"{tok_k10:.1f}",
            "{{S2_COST_LOGICAL_REQ_NO_RAG}}": f"{cost_no_rag:.6f}",
            "{{S2_COST_LOGICAL_REQ_K10}}": f"{cost_k10:.6f}",
            "{{S2_TOTAL_STUDY_BUDGET_USD}}": f"{total_budget:.2f}",
            "{{S2_CANONICAL_TOTAL_USD}}": f"{canonical_total:.2f}",
            "{{S2_NET_REMAINING_USD}}": f"{remaining_budget:.2f}",
            "{{S2_PRIOR_PILOT_HOLD_USD}}": f"{pilot_hold:.8f}",
        }
    )

    # Slide 10: View Diagnostics & Paired Analysis (k=10 condition)
    if "rag_k10" not in views:
        raise KeyError("Missing required condition 'rag_k10' in rq3.view_diagnostics")
    diag10 = views["rag_k10"]
    conc10 = diag10["pair_concordance"]
    mcnemar10 = diag10["mcnemar_test_views_exploratory"]

    paired_delta = diag10["paired_delta"]
    _check_finite(paired_delta, "paired_delta")
    p_asympt = mcnemar10["p_value_asymptotic"]
    p_exact = mcnemar10["p_value_exact"]
    _check_finite(p_asympt, "p_value_asymptotic")
    _check_finite(p_exact, "p_value_exact")

    slots.update(
        {
            "{{S2_SINGLE_VIEW_ACC_E2E}}": _fmt_acc(
                diag10["single_view_accuracy_e2e"], "single_view_accuracy_e2e"
            ),
            "{{S2_CONTEXT_VIEW_ACC_E2E}}": _fmt_acc(
                diag10["contextual_view_accuracy_e2e"],
                "contextual_view_accuracy_e2e",
            ),
            "{{S2_VIEW_ACC_DELTA}}": _fmt_delta(
                diag10["view_accuracy_delta"], "view_accuracy_delta"
            ),
            "{{S2_PAIRED_SINGLE_ACC}}": _fmt_acc(
                diag10["single_paired_accuracy"], "single_paired_accuracy"
            ),
            "{{S2_PAIRED_CONTEXT_ACC}}": _fmt_acc(
                diag10["contextual_paired_accuracy"], "contextual_paired_accuracy"
            ),
            "{{S2_PAIRED_DELTA_PP}}": f"{paired_delta * 100.0:+.2f}",
            "{{S2_MCNEMAR_P_ASYMPT}}": _fmt_acc(p_asympt, "p_value_asymptotic"),
            "{{S2_MCNEMAR_P_EXACT}}": _fmt_acc(p_exact, "p_value_exact"),
            "{{S2_BOTH_CORRECT_COUNT}}": str(conc10["both_correct_count"]),
            "{{S2_SINGLE_ONLY_CORRECT}}": str(conc10["single_only_correct_count"]),
            "{{S2_CONTEXT_ONLY_CORRECT}}": str(conc10["contextual_only_correct_count"]),
            "{{S2_BOTH_INCORRECT_COUNT}}": str(conc10["both_incorrect_count"]),
        }
    )

    return slots


def get_declarative_shape_table_map(slots: dict[str, Any]) -> list[dict[str, Any]]:
    """Build declarative shape/table map with actual quantitative numeric values from slots."""
    mapped: list[dict[str, Any]] = []
    for item in DECLARATIVE_SLOT_DEFINITIONS:
        key = item["slot_key"]
        if key not in slots:
            raise KeyError(
                f"[FAIL_CLOSED] Required declarative slot key '{key}' missing from extracted slots."
            )
        val = slots[key]
        if val is None or val == "":
            raise ValueError(
                f"[FAIL_CLOSED] Empty value for required slot '{item['slot_name']}' ({key})"
            )
        entry = dict(item)
        entry["injected_value"] = str(val)
        mapped.append(entry)
    return mapped


def generate_fixture_markdown_preview(
    slots: dict[str, Any],
    output_path: Path,
) -> None:
    """Write private fixture preview document with populated values and prominent disclaimer."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# [FIXTURE PREVIEW] Presentation Deck Numeric Slots Preview",
        "",
        f"> [!WARNING] {DISCLAIMER_TEXT}",
        "> This preview is automatically compiled from synthetic diagnostic unit test fixtures.",
        "> It does NOT represent canonical empirical research outcomes or live study findings.",
        "> Execution mode: `mock_fixture` | `fixture_only: true`.",
        "",
        "## 1. Metadata & Safety Invariants",
        "- **Provenance Status**: `diagnostic_fixture`",
        f"- **Disclaimer**: `{DISCLAIMER_TEXT}`",
        f"- **Total Placeholders Extracted**: {len(slots) - 1}",
        f"- **Declarative Shape-Table Slots**: {len(DECLARATIVE_SLOT_DEFINITIONS)}",
        "",
        "## 2. Populated Slot Values (by Presentation Slide)",
        "",
        "### Slide 4: Dataset & Views Topology",
        f"- Manifest Path: `{slots.get('{{S2_MANIFEST_PATH}}')}`",
        f"- Total TEST Views: `{slots.get('{{S2_TOTAL_TEST_VIEWS}}')}`",
        f"- Scorable Views: `{slots.get('{{S2_SCORABLE_VIEWS}}')}`",
        f"- Complete Scorable Pairs: `{slots.get('{{S2_COMPLETE_SCORABLE_PAIRS}}')}`",
        f"- Contextual-Only Pairs: `{slots.get('{{S2_CONTEXTUAL_ONLY_PAIRS}}')}`",
        f"- Neither Mapped Pairs: `{slots.get('{{S2_NEITHER_MAPPED_PAIRS}}')}`",
        f"- Distinct Eligible Clusters: `{slots.get('{{S2_DISTINCT_ELIGIBLE_CLUSTERS}}')}`",
        "",
        "### Slide 6: RQ2 Retrieval Diagnostics",
        f"- Hit@10: `{slots.get('{{S2_HIT_RATE_AT_K}}')}`",
        f"- Recall@10: `{slots.get('{{S2_RECALL_AT_K}}')}`",
        f"- Retrieval Miss Rate: `{slots.get('{{S2_RETRIEVAL_MISS_RATE_K10}}')}`",
        "",
        "### Slide 7: RQ1 Attribution Performance & Pairwise Cohorts",
        f"- Marginal Single Acc: `{slots.get('{{S2_SINGLE_VIEW_ACC_E2E}}')}`",
        f"- Marginal Context Acc: `{slots.get('{{S2_CONTEXT_VIEW_ACC_E2E}}')}`",
        f"- Paired Single Acc: `{slots.get('{{S2_PAIRED_SINGLE_ACC}}')}`",
        f"- Paired Context Acc: `{slots.get('{{S2_PAIRED_CONTEXT_ACC}}')}`",
        f"- Paired Delta: `{slots.get('{{S2_PAIRED_DELTA_PP}}')}` pp",
        "",
        "### Slide 8: RQ1 5 Conditions & RQ2 Error Decomposition",
        f"- Accuracy (No-RAG): `{slots.get('{{S2_ACC_E2E_NO_RAG}}')}`",
        f"- Accuracy (RAG k=10): `{slots.get('{{S2_ACC_E2E_RAG_K10}}')}`",
        f"- Macro-F1 (No-RAG): `{slots.get('{{S2_MACRO_F1_NO_RAG}}')}`",
        f"- Macro-F1 (RAG k=10): `{slots.get('{{S2_MACRO_F1_RAG_K10}}')}`",
        (
            f"- Best Condition: `{slots.get('{{S2_BEST_RAG_CONDITION}}')}` "
            f"(Delta: `{slots.get('{{S2_BEST_RAG_ACC_DELTA}}')}`)"
        ),
        f"- Provider Failure Rate: `{slots.get('{{S2_PROVIDER_FAIL_RATE_K10}}')}`",
        f"- Parse Failure Rate: `{slots.get('{{S2_PARSE_FAIL_RATE_K10}}')}`",
        f"- Invalid ID Rate: `{slots.get('{{S2_INVALID_ATTACK_ID_RATE_K10}}')}`",
        f"- Wrong Classification Rate: `{slots.get('{{S2_WRONG_CLASS_RATE_K10}}')}`",
        f"- Overlap Miss & Wrong: `{slots.get('{{S2_OVERLAP_MISS_AND_WRONG_K10}}')}`",
        f"- P(Correct | Retrieved): `{slots.get('{{S2_P_CORRECT_GIVEN_RETRIEVED}}')}`",
        f"- P(Correct | Absent): `{slots.get('{{S2_P_CORRECT_GIVEN_ABSENT}}')}`",
        "",
        "### Slide 9: RQ3 Resource Tradeoffs & Costs",
        (
            f"- Median Latency (No-RAG vs k=10): `{slots.get('{{S2_MEDIAN_LAT_NO_RAG_SEC}}')}` s "
            f"vs `{slots.get('{{S2_MEDIAN_LAT_K10_SEC}}')}` s"
        ),
        (
            f"- Mean Prompt Tokens (No-RAG vs k=10): "
            f"`{slots.get('{{S2_MEAN_PROMPT_TOK_NO_RAG}}')}` vs "
            f"`{slots.get('{{S2_MEAN_PROMPT_TOK_K10}}')}`"
        ),
        (
            f"- Cost per Logical Request (No-RAG vs k=10): "
            f"`${slots.get('{{S2_COST_LOGICAL_REQ_NO_RAG}}')}` vs "
            f"`${slots.get('{{S2_COST_LOGICAL_REQ_K10}}')}`"
        ),
        (
            f"- Whole Study Accounting: Budget `${slots.get('{{S2_TOTAL_STUDY_BUDGET_USD}}')}` | "
            f"Spend `${slots.get('{{S2_CANONICAL_TOTAL_USD}}')}` | "
            f"Remaining `${slots.get('{{S2_NET_REMAINING_USD}}')}`"
        ),
        "",
        "---",
        f"*End of Private Diagnostic Fixture Preview - `{DISCLAIMER_TEXT}`*",
    ]
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Populate presentation numeric slots against diagnostic fixtures only."
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        default=DEFAULT_FIXTURE_DIR,
        help="Path to fixture directory containing rq_analysis.json and native JSON fixtures.",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=DEFAULT_OUTPUT_MD,
        help="Path to write populated Markdown preview.",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=DEFAULT_OUTPUT_JSON,
        help="Path to write populated slot dictionary as JSON for downstream tooling.",
    )
    parser.add_argument(
        "--output-map-json",
        type=Path,
        default=DEFAULT_MAP_JSON,
        help="Path to write declarative shape table map as JSON.",
    )
    args = parser.parse_args()

    try:
        slots = extract_fixture_slots(args.fixture_dir)
        decl_map = get_declarative_shape_table_map(slots)
        generate_fixture_markdown_preview(slots, args.output_md)
        args.output_json.write_text(json.dumps(slots, indent=2), encoding="utf-8")
        args.output_map_json.write_text(json.dumps(decl_map, indent=2), encoding="utf-8")
        print(f"[+] Successfully extracted {len(slots) - 1} numeric slots from fixtures.")
        print(f"[+] Declarative shape/table map generated with {len(decl_map)} entries.")
        print(f"[+] Markdown preview written to: {args.output_md}")
        print(f"[+] JSON slot mapping written to: {args.output_json}")
        print(f"[+] Declarative map written to: {args.output_map_json}")
        print(f"[+] Private labeling certified: {DISCLAIMER_TEXT}")
        return 0
    except Exception as exc:
        print(f"[-] Error populating presentation fixtures: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
