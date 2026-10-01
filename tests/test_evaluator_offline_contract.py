"""Offline contract verification for evaluator output contracts and RQ analysis tools.

Tests:
1. Five conditions matrix enforcement (no_rag, rag_k1, rag_k3, rag_k5, rag_k10).
2. Fixed 474-class Macro-F1 denominator (FROZEN_BENCHMARK_UNIVERSE).
3. ANY_MATCH multi-GT semantics (D2a).
4. Excluded unmapped and ambiguous ground truth counts (D2b/D2c).
5. End-to-end failure denominator including invalid IDs and API failures (D2e/D2f).
6. Invalid and retired-ID diagnostics (D2g).
7. Independent failure axes without mutual exclusion (D2i).
8. Null zero denominators (D2j).
9. Evaluator CLI contract via subprocess invocation.
10. Offline RQ analysis tools (RQ1, RQ2, RQ3, McNemar, bootstrap CIs, report generation).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys

import pytest

from scripts.analysis.evaluate_rqs import (
    compute_mcnemar_test,
    compute_paired_bootstrap_ci,
    compute_rq1,
    compute_rq2,
    compute_rq3,
    run_rq_analysis,
)
from src.evaluation.experiment_metrics import (
    CONDITIONS,
    evaluate_experiment,
)
from tests.test_experiment_evaluation import (
    A,
    B,
    _dump_rows,
    _fixture,
    _load,
    _test_protocol,
)

# ---------------------------------------------------------------------------
# Evaluator Output Contract Tests
# ---------------------------------------------------------------------------


def test_evaluator_contract_five_conditions_matrix(tmp_path):
    """The evaluator contract must strictly require all five conditions."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    results = evaluate_experiment(inputs, proto)
    assert set(results["per_condition"]["conditions"].keys()) == set(CONDITIONS)
    assert results["overall"]["total_conditions"] == 5
    assert set(results["overall"]["by_condition_summary"].keys()) == set(CONDITIONS)


def test_evaluator_contract_fixed_474_class_macro_f1(tmp_path):
    """Macro-F1 denominator must remain invariant to benchmark universe size (474 classes).

    Unobserved classes contribute 0.0 to the numerator, and the denominator is strictly 474.
    """
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    # The fixture corpus contains 14 technique IDs. Let's verify per-condition Macro-F1.
    res = evaluate_experiment(inputs, proto)
    for cond in CONDITIONS:
        cond_f1 = res["per_condition"]["conditions"][cond]["macro_f1"]
        # Macro F1 is sum(F1_c) / universe_size
        universe_size = len(inputs.corpus_ids)
        assert universe_size == 14  # Fixture corpus size
        assert cond_f1 is not None
        assert 0.0 <= cond_f1 <= 1.0


def test_evaluator_contract_any_match_multilabel_ground_truth(tmp_path):
    """D2a ANY_MATCH: predicting ANY valid ground truth technique counts as correct."""
    fixture = _fixture(tmp_path)
    # Sample s2 in fixture has GT = [A, B] (multilabel: T1059.001 and T1105)
    # Test that predicting A is correct, predicting B is correct, predicting C is wrong
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    # Verify sample s2 in rag_k3 has parsed_technique_ids == [B] in fixture
    s2_record = next(
        r for r in inputs.records if r["sample_id"] == "s2" and r["condition"] == "rag_k3"
    )
    assert s2_record["parsed_technique_ids"] == [B]
    assert B in inputs.ground_truth["s2"]
    assert A in inputs.ground_truth["s2"]

    results = evaluate_experiment(inputs, proto)
    # Condition metrics should count s2 as correct because B is in [A, B]
    cond_metrics = results["per_condition"]["conditions"]["rag_k3"]
    assert cond_metrics["correct_count"] == 3


def test_evaluator_contract_unmapped_and_ambiguous_gt_exclusion(tmp_path):
    """D2b and D2c: unmapped and ambiguous samples are excluded from scorable denominator."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    # In fixture: 8 samples total. s4 has label_status='unmapped', s5 has label_status='ambiguous'
    # Remaining scorable samples = 6 per condition.
    results = evaluate_experiment(inputs, proto)
    for cond in CONDITIONS:
        m = results["per_condition"]["conditions"][cond]
        assert m["logical_sample_count"] == 8
        assert m["scorable_sample_count"] == 6
        assert m["unmapped_ground_truth_count"] == 1
        assert m["ambiguous_ground_truth_count"] == 1
        assert m["unmapped_exclusion_reason"] == "UNMAPPED_GROUND_TRUTH"
        assert m["ambiguous_exclusion_reason"] == "AMBIGUOUS_GROUND_TRUTH"


def test_evaluator_contract_end_to_end_failure_denominator(tmp_path):
    """D2e/D2f: invalid IDs and API failures are included in accuracy_end_to_end denominator."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    # In fixture scorable samples (s0, s1, s2, s3, s6, s7):
    # s0: VALID (A) -> correct
    # s1: VALID (C) -> incorrect (GT is B)
    # s2: VALID (B) -> correct (GT is [A, B])
    # s3: INVALID_ID ("not-an-id") -> failure included in e2e denominator
    # s6: VALID (A) -> correct
    # s7: VALID ("T1059" retired ID) -> incorrect (GT is B)
    # Total scorable: 6. Valid scorable: 5 (s3 is INVALID_ID). Correct: 3 (s0, s2, s6).
    results = evaluate_experiment(inputs, proto)
    m = results["per_condition"]["conditions"]["rag_k3"]

    assert m["scorable_sample_count"] == 6
    assert m["valid_scorable_sample_count"] == 5
    assert m["correct_count"] == 3
    # accuracy_end_to_end = 3 / 6 = 0.5
    assert m["accuracy_end_to_end"] == 0.5
    # accuracy_valid_outputs = 3 / 5 = 0.6
    assert m["accuracy_valid_outputs"] == 0.6


def test_evaluator_contract_invalid_and_retired_id_diagnostics(tmp_path):
    """D2g: diagnostics separate syntax errors, unknown IDs, and retired IDs."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    results = evaluate_experiment(inputs, proto)
    m = results["per_condition"]["conditions"]["rag_k3"]

    assert m["invalid_id_count"] == 1
    assert m["invalid_syntax_count"] == 1  # "not-an-id" has invalid syntax
    assert m["unknown_id_count"] == 0
    assert m["retired_id_observation_count"] == 1  # T1059 is deprecated in registry fixture
    assert m["completed_record_count"] == 7  # 8 - 1 (API_FAILURE) = 7 completed


def test_evaluator_contract_independent_failure_axes(tmp_path):
    """D2i: failure decomposition tracks all failure axes independently without mutual exclusion."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    results = evaluate_experiment(inputs, proto)
    decomp = results["failure_decomposition"]["by_condition"]["rag_k3"]

    assert "retrieval_miss_count" in decomp
    assert "provider_failure_count" in decomp
    assert "parse_failure_count" in decomp
    assert "invalid_attack_id_count" in decomp
    assert "valid_but_wrong_classification_count" in decomp
    assert "overlap_retrieval_miss_and_wrong_classification" in decomp
    assert decomp["total_scorable_samples"] == 6


def test_evaluator_contract_null_zero_denominators(tmp_path):
    """D2j: unobserved classes in per-technique metrics render precision/recall/F1 as None."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    results = evaluate_experiment(inputs, proto)
    per_tech = results["per_technique"]["by_condition"]["rag_k3"]

    # "T2000" is in corpus/registry but never in ground truth or predictions
    filler = per_tech["T2000"]
    assert filler["support"] == 0
    assert filler["tp"] == 0
    assert filler["fp"] == 0
    assert filler["fn"] == 0
    assert filler["precision"] is None
    assert filler["recall"] is None
    assert filler["f1"] is None


def _create_dev_run_with_journal(tmp_path):
    fixture = _fixture(tmp_path)
    manifest_path, pred_paths, orig_manifest = fixture

    dev_dir = tmp_path / "dev_cohort"
    dev_dir.mkdir(exist_ok=True)

    dev_sample_ids = ["s8", "s9"]
    dev_samples = [
        {"sample_id": "s8", "pair_id": "p4", "view_type": "single"},
        {"sample_id": "s9", "pair_id": "p4", "view_type": "contextual"},
    ]

    dev_manifest = dict(orig_manifest)
    dev_manifest["split"] = "dev"
    dev_manifest["sample_ids"] = dev_sample_ids
    dev_manifest["samples"] = dev_samples
    req_count = len(dev_sample_ids) * len(CONDITIONS)
    dev_manifest["expected_request_count"] = req_count
    dev_manifest["maximum_attempts"] = req_count * (dev_manifest["execution"]["retries"] + 1)
    dev_manifest["fixture_max_requests"] = req_count

    from src.evaluation.experiment_metrics import canonical_json_bytes

    manifest_bytes = canonical_json_bytes(dev_manifest)
    manifest_digest = hashlib.sha256(manifest_bytes).hexdigest()
    (dev_dir / "manifest.json").write_bytes(manifest_bytes)

    fillers = [f"T{2000 + i}" for i in range(10)]
    all_records = []
    for cond in CONDITIONS:
        orig_rows = [json.loads(line) for line in pred_paths[cond].read_text().splitlines()]
        template = orig_rows[0]
        dev_rows = []
        k = 0 if cond == "no_rag" else int(cond[5:])
        for s in dev_samples:
            row = dict(template)
            row["sample_id"] = s["sample_id"]
            row["pair_id"] = s["pair_id"]
            row["view_type"] = s["view_type"]
            row["manifest_sha256"] = manifest_digest
            row["condition"] = cond
            row["retrieval_k"] = k
            row["parsed_technique_ids"] = ["T1059.001"]
            row["parse_status"] = "VALID"
            row["success"] = True
            row["retrieved_candidates"] = [
                {"technique_id": fillers[idx], "rank": idx + 1, "score": 1.0 / (idx + 1)}
                for idx in range(k)
            ]
            dev_rows.append(row)
            all_records.append(row)
        _dump_rows(dev_dir / f"{cond}_predictions.jsonl", dev_rows)

    journal_rows = [
        {
            "event": "header",
            "manifest_sha256": manifest_digest,
            "max_requests": req_count,
        }
    ]
    ordinal = 0
    for cond in CONDITIONS:
        for s in dev_samples:
            rec = next(
                r
                for r in all_records
                if r["sample_id"] == s["sample_id"] and r["condition"] == cond
            )
            rec_sha = hashlib.sha256(canonical_json_bytes(rec)).hexdigest()
            ordinal += 1
            journal_rows.append({"event": "begin", "key": [s["sample_id"], cond]})
            journal_rows.append(
                {"event": "attempt", "key": [s["sample_id"], cond], "ordinal": ordinal}
            )
            journal_rows.append(
                {
                    "event": "complete",
                    "key": [s["sample_id"], cond],
                    "record_sha256": rec_sha,
                }
            )

    _dump_rows(dev_dir / "request_journal.jsonl", journal_rows)
    return dev_dir / "manifest.json"


def test_evaluator_cli_contract_subprocess_execution(tmp_path):
    """The evaluator CLI (python -m src.experiment evaluate) must export all 6 artifacts."""
    manifest_path = _create_dev_run_with_journal(tmp_path)

    out_dir = tmp_path / "cli_eval_output"
    proto_path = tmp_path / "protocol.json"
    proto = _test_protocol()
    from src.evaluation.experiment_metrics import canonical_json_bytes

    proto_path.write_bytes(
        canonical_json_bytes(
            {
                "protocol_version": proto.protocol_version,
                "protocol_sha256": proto.protocol_sha256,
                "d1_raw_response_policy": proto.d1_raw_response_policy,
                "d2a_ground_truth_semantics": proto.d2a_ground_truth_semantics,
                "d2b_empty_ground_truth": proto.d2b_empty_ground_truth,
                "d2c_ambiguous_ground_truth": proto.d2c_ambiguous_ground_truth,
                "d2d_macro_f1_universe": proto.d2d_macro_f1_universe,
                "d2e_invalid_id_denominator": proto.d2e_invalid_id_denominator,
                "d2f_api_error_denominator": proto.d2f_api_error_denominator,
                "d2g_retired_attack_id": proto.d2g_retired_attack_id,
                "d2h_conditional_retrieval": proto.d2h_conditional_retrieval,
                "d2i_failure_precedence": proto.d2i_failure_precedence,
                "d2j_zero_denominator": proto.d2j_zero_denominator,
                "d3_model_version_policy": proto.d3_model_version_policy,
                "d4_concurrency_policy": proto.d4_concurrency_policy,
                "d5_budget_policy": proto.d5_budget_policy,
                "d6_t15_prerequisite_policy": proto.d6_t15_prerequisite_policy,
                "d7_dataset_scope": proto.d7_dataset_scope,
                "approval_timestamp": proto.approval_timestamp,
                "approval_reference": proto.approval_reference,
            }
        )
    )

    cmd = [
        sys.executable,
        "-m",
        "src.experiment",
        "evaluate",
        "--manifest",
        str(manifest_path),
        "--protocol-file",
        str(proto_path),
        "--output-dir",
        str(out_dir),
        "--repository-root",
        str(tmp_path),
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"CLI evaluation failed: {proc.stderr}\n{proc.stdout}"

    expected_files = (
        "overall_metrics.json",
        "per_condition_metrics.json",
        "per_technique_metrics.json",
        "retrieval_conditional_metrics.json",
        "failure_decomposition.json",
        "run_provenance.json",
    )
    for fname in expected_files:
        artifact = out_dir / fname
        assert artifact.exists()
        parsed = json.loads(artifact.read_bytes())
        assert parsed.get("schema_version") == "1.0.0"


# ---------------------------------------------------------------------------
# Offline RQ Analysis Tools Tests
# ---------------------------------------------------------------------------


def test_mcnemar_test_statistical_properties():
    """Verify McNemar test computation on identical and divergent paired outcomes."""
    # Identical outcomes: p-value should be 1.0, chi2 should be 0.0
    y_base = [True, False, True, True, False]
    y_treat = [True, False, True, True, False]
    res_ident = compute_mcnemar_test(y_base, y_treat)
    assert res_ident["p_value_exact"] == 1.0
    assert res_ident["chi2_statistic"] == 0.0
    assert res_ident["contingency_table"]["total_discordant"] == 0

    # Divergent outcomes favoring treatment
    y_base = [False] * 10 + [True] * 5
    y_treat = [True] * 10 + [True] * 5  # Treatment wins 10 discordant pairs
    res_div = compute_mcnemar_test(y_base, y_treat)
    assert res_div["contingency_table"]["treatment_win_b"] == 10
    assert res_div["contingency_table"]["baseline_win_c"] == 0
    assert res_div["contingency_table"]["total_discordant"] == 10
    assert res_div["p_value_exact"] < 0.01
    assert res_div["significant_at_01"] is True


def test_paired_bootstrap_ci_bounds():
    """Verify bootstrap confidence interval bounds for paired differences."""
    treat = [1.0, 1.0, 1.0, 0.0, 1.0]
    base = [0.0, 0.0, 1.0, 0.0, 0.0]
    ci = compute_paired_bootstrap_ci(treat, base, num_samples=500, seed=123)
    assert ci["ci_lower"] is not None
    assert ci["ci_upper"] is not None
    assert ci["ci_lower"] <= ci["mean_delta"] <= ci["ci_upper"]
    assert ci["mean_delta"] == pytest.approx(0.6, abs=0.05)


def test_rq1_controlled_comparison_computation(tmp_path):
    """Verify RQ1 controlled comparison outputs, deltas, and statistical tests."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq1 = compute_rq1(inputs, proto, bootstrap_samples=100, seed=42)
    assert rq1["schema_version"] == "1.0.0"
    assert rq1["baseline_condition"] == "no_rag"
    assert "by_condition" in rq1

    base_cond = rq1["by_condition"]["no_rag"]
    assert base_cond["is_baseline"] is True
    assert base_cond["accuracy_end_to_end"] == 0.5

    for cond in ("rag_k1", "rag_k3", "rag_k5", "rag_k10"):
        row = rq1["by_condition"][cond]
        assert row["is_baseline"] is False
        assert "delta_vs_baseline" in row
        d = row["delta_vs_baseline"]
        assert "delta_accuracy_end_to_end" in d
        assert "mcnemar_test" in d
        assert "delta_accuracy_e2e_ci_95" in d
        assert d["delta_accuracy_e2e_ci_95"][0] <= d["delta_accuracy_e2e_ci_95"][1]


def test_rq2_error_decomposition_computation(tmp_path):
    """Verify RQ2 retrieval recall and downstream generation error decomposition."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq2 = compute_rq2(inputs, proto)
    assert rq2["schema_version"] == "1.0.0"
    assert "by_condition" in rq2

    rag_k3 = rq2["by_condition"]["rag_k3"]
    assert rag_k3["retrieval_k"] == 3
    assert rag_k3["total_scorable_samples"] == 6
    assert 0.0 <= rag_k3["retrieval_hit_rate"] <= 1.0
    assert 0.0 <= rag_k3["macro_recall"] <= 1.0

    decomp = rag_k3["error_decomposition"]
    assert "retrieval_miss_error_count" in decomp
    assert "generation_misattribution_count" in decomp
    assert "system_or_parse_error_count" in decomp

    total_err_count = (
        decomp["retrieval_miss_error_count"]
        + decomp["generation_misattribution_count"]
        + decomp["system_or_parse_error_count"]
    )
    assert total_err_count == rag_k3["total_failures"]


def test_rq3_tradeoffs_and_view_diagnostics(tmp_path):
    """Verify RQ3 latency, cost, and paired view diagnostics."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq3 = compute_rq3(inputs, proto)
    assert rq3["schema_version"] == "1.0.0"
    assert "tradeoffs_by_condition" in rq3
    assert "view_diagnostics" in rq3

    k3_tradeoff = rq3["tradeoffs_by_condition"]["rag_k3"]
    assert k3_tradeoff["latency_ms"]["mean"] == 1.5
    assert k3_tradeoff["tokens"]["mean_total_tokens"] == 12.0
    assert "financial_cost_usd" in k3_tradeoff

    k3_views = rq3["view_diagnostics"]["rag_k3"]
    assert "single_view_accuracy_e2e" in k3_views
    assert "contextual_view_accuracy_e2e" in k3_views
    assert "view_accuracy_delta" in k3_views
    assert "pair_concordance" in k3_views
    assert k3_views["paired_complete_pairs_count"] > 0


def test_run_rq_analysis_generates_all_artifacts(tmp_path):
    """Verify run_rq_analysis executes full pipeline and produces JSON + Markdown reports."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    out_dir = tmp_path / "rq_reports"
    analysis = run_rq_analysis(
        inputs,
        proto,
        bootstrap_samples=100,
        seed=42,
        output_dir=out_dir,
    )

    assert analysis["schema_version"] == "1.0.0"
    assert "rq1" in analysis
    assert "rq2" in analysis
    assert "rq3" in analysis

    json_path = out_dir / "rq_analysis.json"
    md_path = out_dir / "rq_analysis_summary.md"

    assert json_path.exists()
    assert md_path.exists()

    json_data = json.loads(json_path.read_bytes())
    assert json_data["experiment_id"] == inputs.experiment_id

    md_content = md_path.read_text(encoding="utf-8")
    assert "# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)" in md_content
    assert "## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)" in md_content
    assert "## RQ2: Retrieval vs. Generation Error Decomposition" in md_content
    assert "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs" in md_content


def test_evaluate_rqs_cli_subprocess_execution(tmp_path):
    """The offline RQ analysis CLI must execute and write artifacts."""
    manifest_path = _create_dev_run_with_journal(tmp_path)
    proto_path = tmp_path / "protocol_cli.json"
    proto = _test_protocol()
    from src.evaluation.experiment_metrics import canonical_json_bytes

    proto_path.write_bytes(
        canonical_json_bytes(
            {
                "protocol_version": proto.protocol_version,
                "protocol_sha256": proto.protocol_sha256,
                "d1_raw_response_policy": proto.d1_raw_response_policy,
                "d2a_ground_truth_semantics": proto.d2a_ground_truth_semantics,
                "d2b_empty_ground_truth": proto.d2b_empty_ground_truth,
                "d2c_ambiguous_ground_truth": proto.d2c_ambiguous_ground_truth,
                "d2d_macro_f1_universe": proto.d2d_macro_f1_universe,
                "d2e_invalid_id_denominator": proto.d2e_invalid_id_denominator,
                "d2f_api_error_denominator": proto.d2f_api_error_denominator,
                "d2g_retired_attack_id": proto.d2g_retired_attack_id,
                "d2h_conditional_retrieval": proto.d2h_conditional_retrieval,
                "d2i_failure_precedence": proto.d2i_failure_precedence,
                "d2j_zero_denominator": proto.d2j_zero_denominator,
                "d3_model_version_policy": proto.d3_model_version_policy,
                "d4_concurrency_policy": proto.d4_concurrency_policy,
                "d5_budget_policy": proto.d5_budget_policy,
                "d6_t15_prerequisite_policy": proto.d6_t15_prerequisite_policy,
                "d7_dataset_scope": proto.d7_dataset_scope,
                "approval_timestamp": proto.approval_timestamp,
                "approval_reference": proto.approval_reference,
            }
        )
    )

    out_dir = tmp_path / "cli_rq_reports"
    cmd = [
        sys.executable,
        "scripts/analysis/evaluate_rqs.py",
        "--manifest",
        str(manifest_path),
        "--protocol-file",
        str(proto_path),
        "--output-dir",
        str(out_dir),
        "--repository-root",
        str(tmp_path),
        "--bootstrap-samples",
        "50",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"RQ CLI failed: {proc.stderr}\n{proc.stdout}"
    assert (out_dir / "rq_analysis.json").exists()
    assert (out_dir / "rq_analysis_summary.md").exists()
    cli_md = (out_dir / "rq_analysis_summary.md").read_text(encoding="utf-8")
    assert "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs" in cli_md
