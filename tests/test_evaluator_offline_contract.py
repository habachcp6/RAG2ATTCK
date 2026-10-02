"""Offline contract verification for evaluator output contracts and RQ analysis tools.

Tests:
1. Five conditions matrix enforcement (no_rag, rag_k1, rag_k3, rag_k5, rag_k10).
2. Distinguishing fixed 474-class Macro-F1 known-answer denominator test (Item 5).
3. ANY_MATCH multi-GT semantics (D2a).
4. Excluded unmapped and ambiguous ground truth counts (D2b/D2c).
5. End-to-end failure denominator including invalid IDs and API failures (D2e/D2f).
6. Invalid and retired-ID diagnostics (D2g).
7. Independent failure axes without mutual exclusion (D2i).
8. Null zero denominators (D2j).
9. Evaluator CLI contract via subprocess invocation.
10. Strict pricing validation and unknown service tier rejection (Item 1 & 6).
11. Malformed token values validation (negative, non-int, cached > prompt) (Item 6).
12. Cached token rates tariff accounting (cache_read vs cache_write) (Item 6).
13. Missing usage worst-case attempt charge contract ($0.53974560) (Item 1 & 6).
14. Financial reconciliation with retries, extra receipts, and settlements (Item 2 & 6).
15. Duplicate/mismatched receipt and settlement keys failure modes (Item 6).
16. Explicit cost denominators and excluded views disclosure (Item 3).
17. Study-wide financial accounting and prior pilot hold preservation (Item 2).
18. CLI repository root resolution from external arbitrary CWD (Item 4).
19. Pair-cluster bootstrap resampling preserving intra-pair correlation (Item 7).
20. RQ2 D2i independent failure axes, overlap accounting, and No-RAG N/A semantics (Item 8).
21. Scorable view counts verification (278 single, 440 contextual) (Item 7).
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import pytest

from scripts.analysis.evaluate_rqs import (
    compute_mcnemar_test,
    compute_paired_bootstrap_ci,
    compute_rq1,
    compute_rq2,
    compute_rq3,
    compute_stratified_gt_complexity_producer,
    reconcile_journal_and_ledger,
    run_rq_analysis,
    validate_pricing_config,
)
from src.evaluation.experiment_metrics import (
    CONDITIONS,
    canonical_json_bytes,
    evaluate_experiment,
)
from src.experiment.monetary_ledger import calculate_attempt_token_cost
from tests.test_experiment_evaluation import (
    A,
    B,
    C,
    _digest,
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


def _fixture_474(tmp_path):
    """Fixture with frozen 474-class MITRE ATT&CK universe."""
    fillers = [f"T{2000 + i}" for i in range(470)]
    registry_ids = [A, B, C, "T1059", *fillers]
    assert len(registry_ids) == 474

    truth = [[A], [B], [A], [C], [], [], [A], [B], [A], [B]]
    samples = [
        {
            "sample_id": f"s{i}",
            "pair_id": f"p{i // 2}",
            "view_type": "single" if i % 2 == 0 else "contextual",
        }
        for i in range(10)
    ]
    artifact_values = {
        "inference": [
            {"sample_id": s["sample_id"], "endpoint_evidence": f"fixture event {i}"}
            for i, s in enumerate(samples)
        ],
        "ground_truth": [
            {
                "view_id": s["sample_id"],
                "technique_ids": truth[i],
                "label_status": "mapped" if truth[i] else ("unmapped" if i == 4 else "ambiguous"),
            }
            for i, s in enumerate(samples)
        ],
        "views": [
            {
                "view_id": s["sample_id"],
                "pair_id": s["pair_id"],
                "view_type": s["view_type"],
                "event_ids": [f"e{i // 2}"] if i % 2 == 0 else [f"e{i // 2}", f"context{i // 2}"],
            }
            for i, s in enumerate(samples)
        ],
        "corpus": [{"technique_id": tid} for tid in registry_ids],
    }
    artifact_values["pairs"] = [
        {
            "pair_id": f"p{i}",
            "split": "test" if i < 4 else "dev",
            "single_view": artifact_values["views"][2 * i],
            "contextual_view": artifact_values["views"][2 * i + 1],
            "single_ground_truth": artifact_values["ground_truth"][2 * i],
            "contextual_ground_truth": artifact_values["ground_truth"][2 * i + 1],
        }
        for i in range(5)
    ]
    specs = {}
    for name, rows in artifact_values.items():
        path = tmp_path / f"{name}.jsonl"
        _dump_rows(path, rows)
        specs[name] = {"path": path.name, "sha256": _digest(path.read_bytes())}

    def artifact(name, value, *, data=None):
        path = tmp_path / f"{name}.json"
        path.write_bytes(canonical_json_bytes(value) if data is None else data)
        specs[name] = {"path": path.name, "sha256": _digest(path.read_bytes())}

    artifact("split_manifest", {"test": [f"p{i}" for i in range(4)], "dev": ["p4"]})
    artifact(
        "attack_registry",
        {
            "objects": [
                {
                    "type": "attack-pattern",
                    "external_references": [{"source_name": "mitre-attack", "external_id": tid}],
                    "x_mitre_deprecated": tid == "T1059",
                }
                for tid in registry_ids
            ]
        },
    )
    artifact("prompt", None, data=b"fixture prompt {ENDPOINT_EVIDENCE} {RETRIEVED_CONTEXT}")
    model = {
        "provider": "fixture",
        "model": "fixture-model",
        "logging_policy": {"log_raw_response": False},
    }
    artifact("model_config", model)
    artifact("index", None, data=b"fixture index - never loaded")
    artifact("document_mapping", [{"technique_id": tid} for tid in registry_ids])
    artifact(
        "retrieval_config",
        {
            "supported_k": [1, 3, 5, 10],
            "corpus_sha256": specs["corpus"]["sha256"],
            "embedding_model": "mock",
            "distance_metric": "cosine",
        },
    )
    artifact(
        "retrieval_manifest",
        {
            "corpus_sha256": specs["corpus"]["sha256"],
            "index_sha256": specs["index"]["sha256"],
            "document_mapping_sha256": specs["document_mapping"]["sha256"],
        },
    )
    artifact(
        "dataset_manifest",
        {
            "benchmark_version": "fixture-only",
            "attack_version": "19.2",
            "state": "frozen",
            "view_count": 10,
            "pair_count": 5,
            "split_counts": {"test": 4, "dev": 1},
            "attack_source_sha256": specs["attack_registry"]["sha256"],
            "files": {
                Path(specs[name]["path"]).name: specs[name]["sha256"]
                for name in ("inference", "ground_truth", "views", "pairs", "split_manifest")
            },
        },
    )
    execution = {"retries": 1}
    experiment_config = {
        "schema_version": "1.0.0",
        "purpose": "known_answer_fixture_only",
        "execution": execution,
    }
    artifact("experiment_config", experiment_config)
    from src.llm.schemas import TechniquePrediction

    schema_sha = hashlib.sha256(
        canonical_json_bytes(TechniquePrediction.model_json_schema())
    ).hexdigest()

    manifest = {
        "schema_version": "1.0.0",
        "status": "frozen",
        "execution_mode": "mock_fixture",
        "experiment_id": "known-answer-only",
        "git_commit_sha": "0" * 40,
        "config_sha256": specs["experiment_config"]["sha256"],
        "artifacts": specs,
        "split": "test",
        "sample_ids": [f"s{i}" for i in range(8)],
        "samples": samples[:8],
        "expected_request_count": 40,
        "maximum_attempts": 80,
        "conditions": list(CONDITIONS),
        "execution": execution,
        "model": model,
        "model_version": None,
        "retrieval": {
            "supported_k": [1, 3, 5, 10],
            "corpus_sha256": specs["corpus"]["sha256"],
            "embedding_model": "mock",
            "distance_metric": "cosine",
        },
        "output_schema_sha256": schema_sha,
        "benchmark_version": "fixture-only",
        "attack_release": "19.2",
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_bytes(canonical_json_bytes(manifest))
    manifest_digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    pred_paths = {}
    for cond in CONDITIONS:
        rows = []
        k = 0 if cond == "no_rag" else int(cond[5:])
        for s in samples[:8]:
            sid = s["sample_id"]
            gt = truth[int(sid[1:])]
            status = "mapped" if gt else ("unmapped" if sid == "s4" else "ambiguous")
            pred_id = gt[0] if (status == "mapped" and gt) else None
            row = {
                "schema_version": "1.0.0",
                "execution_mode": "mock_fixture",
                "experiment_id": "known-answer-only",
                "manifest_sha256": manifest_digest,
                "condition": cond,
                "retrieval_k": k,
                "provider": "fixture",
                "model": "fixture-model",
                "model_version": None,
                "output_schema_sha256": schema_sha,
                "ground_truth_version": "fixture-only",
                "attack_release": "19.2",
                "prompt_sha256": specs["prompt"]["sha256"],
                "model_config_sha256": specs["model_config"]["sha256"],
                "dataset_sha256": specs["inference"]["sha256"],
                "ground_truth_sha256": specs["ground_truth"]["sha256"],
                "corpus_sha256": specs["corpus"]["sha256"],
                "index_sha256": specs["index"]["sha256"],
                "sample_id": sid,
                "pair_id": s["pair_id"],
                "view_type": s["view_type"],
                "run_id": "run-001",
                "raw_response": None,
                "raw_response_logged": False,
                "parse_status": "VALID" if pred_id else "API_FAILURE",
                "success": bool(pred_id),
                "parsed_technique_ids": [pred_id] if pred_id else [],
                "retrieved_candidates": [
                    {"technique_id": fillers[idx], "rank": idx + 1, "score": 1.0 / (idx + 1)}
                    for idx in range(k)
                ],
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "total_tokens": 120,
                "latency_ms": 15.0,
                "retry_count": 0,
                "request_attempt_count": 1,
                "error_type": None,
                "error_message": None,
                "returned_model_id": "fixture-model",
                "response_id": f"resp-{sid}",
                "system_fingerprint": None,
                "request_timestamp_utc": "2026-10-01T00:00:00+00:00",
                "response_timestamp_utc": "2026-10-01T00:00:01+00:00",
                "timestamp": "2026-10-01T00:00:01+00:00",
                "terminal": True,
            }
            rows.append(row)
        pred_path = tmp_path / f"{cond}_predictions.jsonl"
        _dump_rows(pred_path, rows)
        pred_paths[cond] = pred_path

    return manifest_path, pred_paths, manifest


def test_evaluator_contract_fixed_474_class_macro_f1_distinguishing(tmp_path):
    """Known-answer test: Macro-F1 denominator must strictly be 474, not observed classes.

    In this 474-class fixture:
    - Exactly 3 classes (A, B, C) are observed and have F1 = 1.0.
    - Exactly 471 classes are unobserved in predictions/ground truth (F1 = 0.0 per D2d/D2j).
    - The true Macro-F1 is strictly 3.0 / 474 = 0.0063291...
    - An observed-only denominator (3.0 / 3.0 = 1.0) must FAIL by a factor of 158x.
    """
    fixture = _fixture_474(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    assert len(inputs.corpus_ids) == 474

    results = evaluate_experiment(inputs, proto)
    cond_metrics = results["per_condition"]["conditions"]["no_rag"]
    cond_f1 = cond_metrics["macro_f1"]

    expected_f1 = 3.0 / 474.0
    observed_only_f1 = 3.0 / 3.0  # 1.0

    assert cond_f1 == pytest.approx(expected_f1, abs=1e-7)
    assert cond_f1 != observed_only_f1
    assert abs(cond_f1 - observed_only_f1) > 0.99
    assert cond_f1 < 0.01


def test_evaluator_contract_any_match_multilabel_ground_truth(tmp_path):
    """D2a ANY_MATCH: predicting ANY valid ground truth technique counts as correct."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    s2_record = next(
        r for r in inputs.records if r["sample_id"] == "s2" and r["condition"] == "rag_k3"
    )
    assert s2_record["parsed_technique_ids"] == [B]
    assert B in inputs.ground_truth["s2"]
    assert A in inputs.ground_truth["s2"]

    results = evaluate_experiment(inputs, proto)
    cond_metrics = results["per_condition"]["conditions"]["rag_k3"]
    assert cond_metrics["correct_count"] == 3


def test_evaluator_contract_unmapped_and_ambiguous_gt_exclusion(tmp_path):
    """D2b and D2c: unmapped and ambiguous samples are excluded from scorable denominator."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

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

    results = evaluate_experiment(inputs, proto)
    m = results["per_condition"]["conditions"]["rag_k3"]

    assert m["scorable_sample_count"] == 6
    assert m["valid_scorable_sample_count"] == 5
    assert m["correct_count"] == 3
    assert m["accuracy_end_to_end"] == 0.5
    assert m["accuracy_valid_outputs"] == 0.6


def test_evaluator_contract_invalid_and_retired_id_diagnostics(tmp_path):
    """D2g: diagnostics separate syntax errors, unknown IDs, and retired IDs."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    results = evaluate_experiment(inputs, proto)
    m = results["per_condition"]["conditions"]["rag_k3"]

    assert m["invalid_id_count"] == 1
    assert m["invalid_syntax_count"] == 1
    assert m["unknown_id_count"] == 0
    assert m["retired_id_observation_count"] == 1
    assert m["completed_record_count"] == 7


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

    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    exp_model = orig_manifest["model"]["model"]

    dev_manifest = dict(orig_manifest)
    dev_manifest["split"] = "dev"
    dev_manifest["sample_ids"] = dev_sample_ids
    dev_manifest["samples"] = dev_samples
    req_count = len(dev_sample_ids) * len(CONDITIONS)
    dev_manifest["expected_request_count"] = req_count
    dev_manifest["maximum_attempts"] = req_count * (dev_manifest["execution"]["retries"] + 1)
    dev_manifest["fixture_max_requests"] = req_count
    dev_manifest["model"] = orig_manifest["model"]

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
            row["prompt_tokens"] = 100
            row["completion_tokens"] = 20
            row["total_tokens"] = 120
            row["request_attempt_count"] = 1
            row["model"] = exp_model
            row["response_id"] = f"resp-{s['sample_id']}-{cond}"
            row["retrieved_candidates"] = [
                {"technique_id": fillers[idx], "rank": idx + 1, "score": 1.0 / (idx + 1)}
                for idx in range(k)
            ]
            dev_rows.append(row)
            all_records.append(row)
        _dump_rows(dev_dir / f"{cond}_predictions.jsonl", dev_rows)

    hold_amt = Decimal("2.15898240")
    cost_amt = calculate_attempt_token_cost(100, 20, pricing_cfg, cached_tokens=0)
    refund_amt = hold_amt - cost_amt

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
            key = [s["sample_id"], cond]
            journal_rows.append(
                {"event": "monetary_reserve", "key": key, "amount_usd": str(hold_amt)}
            )
            journal_rows.append({"event": "begin", "key": key})
            journal_rows.append({"event": "attempt", "key": key, "ordinal": ordinal})
            journal_rows.append(
                {
                    "event": "attempt_receipt",
                    "key": key,
                    "ordinal": ordinal,
                    "attempt_index": 0,
                    "status": "SUCCESS",
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "cached_tokens": 0,
                    "service_tier": "default",
                    "model": rec["model"],
                    "response_id": rec["response_id"],
                }
            )
            journal_rows.append(
                {
                    "event": "complete",
                    "key": key,
                    "record_sha256": rec_sha,
                }
            )
            journal_rows.append(
                {
                    "event": "monetary_settle",
                    "key": key,
                    "record_sha256": rec_sha,
                    "cost_usd": str(cost_amt),
                    "refund_usd": str(refund_amt),
                    "breach": False,
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
# Strict Pricing & Financial Accounting Regressions (Items 1, 2, 3, 6)
# ---------------------------------------------------------------------------


def test_pricing_config_strict_validation():
    """Pricing configuration must reject missing tariffs, invalid bounds, or unknown tiers."""
    # Empty config
    with pytest.raises(ValueError, match="missing 'tariffs'"):
        validate_pricing_config({})

    # Non-dict
    with pytest.raises(ValueError, match="must be a dict"):
        validate_pricing_config("invalid")  # type: ignore

    # Missing default tier
    with pytest.raises(ValueError, match="missing 'tariffs' or 'default'"):
        validate_pricing_config({"tariffs": {"auto": {}}})

    # Missing reservation bounds
    invalid_tariff_config = {
        "tariffs": {
            "default": {
                "short": {
                    "input_per_million": "0.20",
                    "output_per_million": "1.20",
                    "cache_read_per_million": "0.02",
                    "cache_write_per_million": "0.25",
                },
                "long": {
                    "input_per_million": "0.40",
                    "output_per_million": "1.80",
                    "cache_read_per_million": "0.04",
                    "cache_write_per_million": "0.50",
                },
            }
        },
        "reservation_bounds": {},
        "ceilings": {
            "max_input_tokens": 1050000,
            "max_output_tokens": 8192,
            "short_context_limit": 272000,
        },
        "total_study_budget_usd": "19.99000000",
    }
    with pytest.raises(ValueError, match="Missing required reservation bound"):
        validate_pricing_config(invalid_tariff_config)

    # Valid config passes
    from scripts.analysis.evaluate_rqs import load_pricing_config

    valid_cfg, _ = load_pricing_config()
    assert validate_pricing_config(valid_cfg) == valid_cfg


def test_malformed_token_values_validation():
    """Negative tokens or cached > prompt tokens must raise ValueError without silent clamping."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    # Negative prompt tokens
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_attempt_token_cost(-10, 100, pricing_cfg)

    # Negative completion tokens
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_attempt_token_cost(100, -5, pricing_cfg)

    # Cached tokens exceeding prompt tokens
    with pytest.raises(ValueError, match="cannot exceed prompt_tokens"):
        calculate_attempt_token_cost(100, 50, pricing_cfg, cached_tokens=150)

    # Unknown tier rejected immediately (no fallback permitted)
    with pytest.raises(ValueError, match="Unknown service tier 'unknown_tier'"):
        calculate_attempt_token_cost(100, 50, pricing_cfg, tier="unknown_tier")


def test_cached_token_rates_tariff_accounting():
    """Verify prompt cached tokens billed at cache_read rate ($0.02) vs cache_write ($0.25)."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    # 10,000 prompt tokens, 1,000 completion tokens
    p_tok = 10000
    c_tok = 1000

    # Uncached: prompt billed at cache_write (10k * 0.25 / 1M = $0.0025) + output = $0.0037
    cost_uncached = calculate_attempt_token_cost(p_tok, c_tok, pricing_cfg, cached_tokens=0)
    # Cached: 8k cached ($0.00016) + 2k write ($0.0005) + output ($0.0012) = $0.00186
    cost_cached = calculate_attempt_token_cost(p_tok, c_tok, pricing_cfg, cached_tokens=8000)

    assert cost_cached < cost_uncached
    assert cost_uncached == Decimal("0.00370000")
    assert cost_cached == Decimal("0.00186000")


def test_missing_usage_worst_case_attempt_charge():
    """Missing prompt or completion tokens must charge worst-case attempt fee ($0.53974560)."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    worst_fee = Decimal("0.53974560")
    assert calculate_attempt_token_cost(None, 100, pricing_cfg) == worst_fee
    assert calculate_attempt_token_cost(100, None, pricing_cfg) == worst_fee
    assert calculate_attempt_token_cost(None, None, pricing_cfg) == worst_fee


def test_reconciled_financial_accounting_with_retries(tmp_path):
    """Reconciled cost must account for retried attempts beyond final prediction record tokens."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    # Construct journal with a retried request for (s0, no_rag):
    # Attempt 0: failed (API_FAILURE, usage=None -> charged worst-case $0.53974560)
    # Attempt 1: succeeded (prompt=1000, completion=100 -> $0.00037000)
    rec_s0 = next(
        r for r in inputs.records if r["sample_id"] == "s0" and r["condition"] == "no_rag"
    )
    rec_s0 = dict(rec_s0)
    rec_s0["request_attempt_count"] = 2
    rec_s0["prompt_tokens"] = 1000
    rec_s0["completion_tokens"] = 100
    rec_s0["total_tokens"] = 1100
    rec_s0["model"] = "gpt-5.6-luna"
    rec_s0["response_id"] = "resp-final"
    rec_s0["parse_status"] = "VALID"
    rec_sha = hashlib.sha256(canonical_json_bytes(rec_s0)).hexdigest()

    events = [
        {"event": "header", "manifest_sha256": inputs.manifest_sha256, "max_requests": 100},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {"event": "transition", "key": ["s0", "no_rag"], "state": "RESERVED"},
        {"event": "transition", "key": ["s0", "no_rag"], "state": "DISPATCH_STARTED"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "status": "API_FAILURE",
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "service_tier": "default",
        },
        {"event": "transition", "key": ["s0", "no_rag"], "state": "DISPATCH_STARTED"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 2,
            "attempt_index": 1,
            "status": "SUCCESS",
            "input_tokens": 1000,
            "output_tokens": 100,
            "cached_tokens": None,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-final",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "cost_usd": str(Decimal("0.53974560") + Decimal("0.00037000")),
            "refund_usd": "1.61886680",
            "record_sha256": rec_sha,
            "breach": False,
        },
    ]

    reconciled = reconcile_journal_and_ledger(
        [rec_s0],
        pricing_cfg,
        journal_events=events,
    )

    assert reconciled["journal_present"] is True
    assert reconciled["retried_attempts_by_condition"]["no_rag"] == 1
    settled_cost = reconciled["settled_cost_by_condition"]["no_rag"]
    assert settled_cost is not None
    assert settled_cost == Decimal("0.54011560")


def test_reconciliation_duplicate_and_mismatched_keys_fail(tmp_path):
    """Reconciliation rejects duplicate ordinals, duplicate settles, or hash mismatches."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    manifest_sha = inputs.manifest_sha256

    rec_s0 = next(
        r for r in inputs.records if r["sample_id"] == "s0" and r["condition"] == "no_rag"
    )
    rec_s0_hash = hashlib.sha256(canonical_json_bytes(rec_s0)).hexdigest()

    # 1. Duplicate receipt ordinal
    dup_ord_events = [
        {"event": "header", "manifest_sha256": manifest_sha, "max_requests": 1},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 10,
            "service_tier": "default",
        },
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,  # Duplicate ordinal!
            "attempt_index": 1,
            "input_tokens": 100,
            "output_tokens": 10,
            "service_tier": "default",
        },
    ]
    with pytest.raises(ValueError, match="Duplicate attempt_receipt ordinal"):
        reconcile_journal_and_ledger([rec_s0], pricing_cfg, journal_events=dup_ord_events)

    # 2. Duplicate monetary_settle
    dup_settle_events = [
        {"event": "header", "manifest_sha256": manifest_sha, "max_requests": 1},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": rec_s0_hash},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "record_sha256": rec_s0_hash,
            "breach": False,
        },
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "record_sha256": rec_s0_hash,
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Duplicate monetary_settle event"):
        reconcile_journal_and_ledger([rec_s0], pricing_cfg, journal_events=dup_settle_events)

    # 3. Hash mismatch between monetary_settle and record
    mismatch_events = [
        {"event": "header", "manifest_sha256": manifest_sha, "max_requests": 1},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": rec_s0_hash},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "record_sha256": "f" * 64,  # Incorrect hash!
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Monetary settle record_sha256 mismatch"):
        reconcile_journal_and_ledger([rec_s0], pricing_cfg, journal_events=mismatch_events)


def test_reconciliation_mutation_foreign_and_missing_header(tmp_path):
    """Header mutations: foreign manifest SHA, missing header, and duplicate headers fail."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {"sample_id": "s0", "condition": "no_rag", "manifest_sha256": "a" * 64}

    # Foreign header
    events_foreign = [
        {"event": "header", "manifest_sha256": "b" * 64, "max_requests": 1},
    ]
    with pytest.raises(ValueError, match="Journal header manifest_sha256 mismatch"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_foreign)

    # Missing header
    events_missing = [
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "1.00"},
    ]
    with pytest.raises(ValueError, match="Journal missing header event"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_missing)

    # Duplicate header
    events_dup = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
    ]
    with pytest.raises(ValueError, match="Duplicate header event"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_dup)


def test_reconciliation_mutation_settlement_vs_receipt_cost_and_refund_mismatch():
    """Settlement cost drifting from receipts or violating balance conservation fails closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
        "model": "gpt-5.6-luna",
        "response_id": "resp-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    # 1. Cost mismatch (receipt cost is 0.00004900, settlement claims 1.23000000)
    events_cost_mismatch = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "1.23000000",
            "refund_usd": "0.92898240",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Journal settlement cost mismatch"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_cost_mismatch)

    # 2. Refund conservation mismatch (held is 2.15898240, cost + refund = 1.04900000 != held)
    events_conservation_mismatch = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "1.00000000",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Settlement conservation mismatch"):
        reconcile_journal_and_ledger(
            [record], pricing_cfg, journal_events=events_conservation_mismatch
        )


def test_reconciliation_mutation_ledger_vs_journal_drift():
    """Ledger disagreements with predictions fail closed (cost/hash drift, missing/extra)."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
        "model": "gpt-5.6-luna",
        "response_id": "resp-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    valid_events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
    ]

    # 1. Cost drift in ledger
    ledger_cost_drift = {
        "settled_records": {
            "s0:no_rag": {
                "record_sha256": rec_sha,
                "cost_usd": "0.00005000",
                "refund_usd": "2.15893240",
            }
        }
    }
    with pytest.raises(ValueError, match="Study ledger cost mismatch"):
        reconcile_journal_and_ledger(
            [record], pricing_cfg, journal_events=valid_events, study_ledger_data=ledger_cost_drift
        )

    # 2. Record SHA drift in ledger
    ledger_sha_drift = {
        "settled_records": {
            "s0:no_rag": {
                "record_sha256": "e" * 64,
                "cost_usd": "0.00004900",
                "refund_usd": "2.15893340",
            }
        }
    }
    with pytest.raises(ValueError, match="Study ledger record_sha256 mismatch"):
        reconcile_journal_and_ledger(
            [record], pricing_cfg, journal_events=valid_events, study_ledger_data=ledger_sha_drift
        )

    # 3. Ledger missing settlement
    ledger_missing = {"settled_records": {}}
    with pytest.raises(ValueError, match="Study ledger missing settled record"):
        reconcile_journal_and_ledger(
            [record], pricing_cfg, journal_events=valid_events, study_ledger_data=ledger_missing
        )

    # 4. Ledger extra settlement key
    ledger_extra = {
        "settled_records": {
            "s0:no_rag": {
                "record_sha256": rec_sha,
                "cost_usd": "0.00004900",
                "refund_usd": "2.15893340",
            },
            "s1:no_rag": {
                "record_sha256": "1" * 64,
                "cost_usd": "0.00004900",
                "refund_usd": "2.15893340",
            },
        }
    }
    with pytest.raises(ValueError, match="Foreign ledger settlement key"):
        reconcile_journal_and_ledger(
            [record], pricing_cfg, journal_events=valid_events, study_ledger_data=ledger_extra
        )


def test_reconciliation_mutation_missing_and_extra_keys():
    """Matrix coverage: missing settlements, foreign keys, or non-contiguous ordinals fail."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    r1 = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
    }
    r2 = {
        "sample_id": "s1",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
    }
    r1_sha = hashlib.sha256(canonical_json_bytes(r1)).hexdigest()

    # 1. Missing settlement for r2
    partial_events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 2},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": r1_sha},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "record_sha256": r1_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Missing complete event for record key"):
        reconcile_journal_and_ledger([r1, r2], pricing_cfg, journal_events=partial_events)

    # 2. Foreign settlement key (s99 not in records)
    foreign_events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 2},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": r1_sha},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "record_sha256": r1_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
        {"event": "monetary_reserve", "key": ["s99", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s99", "no_rag"],
            "ordinal": 2,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s99", "no_rag"], "record_sha256": "c" * 64},
        {
            "event": "monetary_settle",
            "key": ["s99", "no_rag"],
            "record_sha256": "c" * 64,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Foreign/extra key in journal event"):
        reconcile_journal_and_ledger([r1], pricing_cfg, journal_events=foreign_events)

    # 3. Non-contiguous attempt ordinals (ordinal 2 instead of 1)
    non_contig_events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 2,
            "attempt_index": 0,
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {"event": "complete", "key": ["s0", "no_rag"], "record_sha256": r1_sha},
        {
            "event": "monetary_settle",
            "key": ["s0", "no_rag"],
            "record_sha256": r1_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Attempt receipt ordinals must start at 1"):
        reconcile_journal_and_ledger([r1], pricing_cfg, journal_events=non_contig_events)

    # 4. Non-contiguous attempt ordinals with gap (1, 3)
    gap_events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": ["s0", "no_rag"], "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 1,
            "attempt_index": 0,
            "status": "RETRYABLE",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {
            "event": "attempt_receipt",
            "key": ["s0", "no_rag"],
            "ordinal": 3,
            "attempt_index": 1,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
    ]
    with pytest.raises(ValueError, match="Non-contiguous attempt_receipt ordinals"):
        reconcile_journal_and_ledger([r1], pricing_cfg, journal_events=gap_events)


def test_reconciliation_mutation_two_retries_with_cached_usage():
    """Verify request with 2 retries (3 attempts total) correctly applies cached token tariffs."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 3,
        "prompt_tokens": 5000,
        "completion_tokens": 100,
        "total_tokens": 5100,
        "model": "gpt-5.6-luna",
        "response_id": "resp-final",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "TIMEOUT",
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "service_tier": "default",
        },
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 2,
            "attempt_index": 1,
            "status": "API_FAILURE",
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "service_tier": "default",
        },
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 3,
            "attempt_index": 2,
            "status": "SUCCESS",
            "input_tokens": 5000,
            "output_tokens": 100,
            "cached_tokens": 4500,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-final",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "1.07982620",
            "refund_usd": "1.07915620",
            "breach": False,
        },
    ]

    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)
    assert reconciled["journal_present"] is True
    assert reconciled["settled_cost_by_condition"]["no_rag"] == Decimal("1.07982620")
    assert reconciled["retried_attempts_by_condition"]["no_rag"] == 2


def test_reconciliation_mutation_missing_usage():
    """Missing token usage on attempt receipt must be charged full worst-case attempt fee."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    # Settle claiming $0.00 for missing usage fails
    events_undercharged = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "API_FAILURE",
            "input_tokens": None,
            "output_tokens": None,
            "cached_tokens": None,
            "service_tier": "default",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00000000",
            "refund_usd": "2.15898240",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Journal settlement cost mismatch"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_undercharged)


def test_reconciliation_mutation_orphan_cancellation():
    """Orphan hold cancellation releases reservation hold with native amount_usd."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    key_settled = ["s0", "no_rag"]
    key_orphan = ["s1", "no_rag"]
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
        "model": "gpt-5.6-luna",
        "response_id": "resp-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 2},
        {"event": "monetary_reserve", "key": key_settled, "amount_usd": "2.15898240"},
        {"event": "monetary_reserve", "key": key_orphan, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key_settled,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-1",
        },
        {"event": "complete", "key": key_settled, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key_settled,
            "record_sha256": rec_sha,
            "cost_usd": "0.00004900",
            "refund_usd": "2.15893340",
            "breach": False,
        },
        {"event": "monetary_cancel_orphan", "key": key_orphan, "amount_usd": "2.15898240"},
    ]

    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)
    assert reconciled["active_reservation_count"] == 0
    assert reconciled["active_reservations_usd"] == Decimal("0.00000000")
    assert reconciled["orphan_cancellations_usd"] == Decimal("2.15898240")


def test_reconciliation_mutation_complete_without_settle():
    """Complete events without subsequent settlement must fail closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
    ]

    with pytest.raises(ValueError, match="Complete-without-settle detected"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)


def test_reconciliation_mutation_nonfinite_and_malformed_amounts():
    """Non-finite money amounts (NaN, Inf, negative) and malformed token counts fail closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    key = ["s0", "no_rag"]
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
    }

    # 1. NaN in monetary_reserve amount_usd
    events_nan_res = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "NaN"},
    ]
    with pytest.raises(ValueError, match="must be finite"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_nan_res)

    # 2. Negative amount_usd in monetary_reserve
    events_neg_res = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "-1.00"},
    ]
    with pytest.raises(ValueError, match="non-negative"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_neg_res)

    # 3. Non-integer token count in attempt_receipt
    events_float_tok = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 100.5,
            "output_tokens": 20,
            "cached_tokens": 0,
            "service_tier": "default",
        },
    ]
    with pytest.raises(ValueError, match="must be exact int"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_float_tok)


def test_cli_subprocess_mismatched_journal_or_ledger_fails(tmp_path):
    """CLI analysis invocation with mismatched journal or ledger must fail closed (exit != 0)."""
    manifest_path = _create_dev_run_with_journal(tmp_path)
    real_repo_root = Path(__file__).resolve().parents[1]

    # Populate default config directory in tmp_path so CLI default paths resolve against mock root
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    import shutil

    shutil.copy(
        real_repo_root / "config" / "experiment_protocol_v1.json",
        config_dir / "experiment_protocol_v1.json",
    )
    shutil.copy(
        real_repo_root / "config" / "pricing_v1.json",
        config_dir / "pricing_v1.json",
    )

    # Mutate the generated request_journal.jsonl to introduce a cost mismatch
    journal_file = manifest_path.parent / "request_journal.jsonl"
    lines = journal_file.read_text(encoding="utf-8").splitlines()
    mutated_lines = []
    for line in lines:
        data = json.loads(line)
        if data.get("event") == "monetary_settle":
            # Conserve hold (cost + refund = hold) but drift from receipt calculation
            data["cost_usd"] = "1.00000000"
            data["refund_usd"] = str(Decimal("2.15898240") - Decimal("1.00000000"))
        mutated_lines.append(json.dumps(data))
    journal_file.write_text("\n".join(mutated_lines) + "\n", encoding="utf-8")

    out_dir = tmp_path / "failing_cli_reports"

    cmd = [
        sys.executable,
        str(real_repo_root / "scripts" / "analysis" / "evaluate_rqs.py"),
        "--manifest",
        str(manifest_path),
        "--output-dir",
        str(out_dir),
        "--repository-root",
        str(tmp_path),
        "--bootstrap-samples",
        "20",
    ]

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert "Journal settlement cost mismatch" in proc.stderr


def test_explicit_cost_denominators_and_excluded_views(tmp_path):
    """RQ3 must report cost_per_logical_request, cost_per_scorable_query, and cost_per_correct."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    rq3 = compute_rq3(inputs, proto, pricing_config=pricing_cfg)
    k3_fin = rq3["tradeoffs_by_condition"]["rag_k3"]["financial_cost_usd"]

    assert "cost_per_logical_request_usd" in k3_fin
    assert "cost_per_scorable_query_usd" in k3_fin
    assert "cost_per_correct_attribution_usd" in k3_fin
    assert "cost_of_excluded_ambiguous_views_usd" in k3_fin
    assert "cost_of_excluded_unmapped_views_usd" in k3_fin
    assert "cost_of_all_excluded_views_usd" in k3_fin
    assert "excluded_views_financial_disclosure" in k3_fin

    tot = k3_fin["total_cost_usd"]
    # 8 total logical records, 6 scorable, 3 correct in fixture
    assert k3_fin["cost_per_logical_request_usd"] == pytest.approx(tot / 8.0)
    assert k3_fin["cost_per_scorable_query_usd"] == pytest.approx(tot / 6.0)
    assert k3_fin["cost_per_correct_attribution_usd"] == pytest.approx(tot / 3.0)
    assert k3_fin["cost_of_all_excluded_views_usd"] > 0


def test_study_wide_financial_accounting_and_pilot_hold(tmp_path):
    """Whole-study accounting must preserve prior pilot hold without charging to conditions."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()

    rq3 = compute_rq3(inputs, proto, pricing_config=pricing_cfg)
    study_fin = rq3["whole_study_financial_accounting"]

    assert study_fin["total_study_budget_usd"] == 19.99
    assert study_fin["prior_pilot_provisional_hold_usd"] == pytest.approx(0.05264010)
    assert study_fin["total_study_committed_spend_usd"] > 0.05264010
    assert study_fin["net_remaining_uncommitted_budget_usd"] > 0

    # Ensure pilot hold was NOT charged to any individual condition
    for cond in CONDITIONS:
        cond_tot = rq3["tradeoffs_by_condition"][cond]["financial_cost_usd"]["total_cost_usd"]
        assert cond_tot < 0.05264010


def test_cli_repository_root_resolution_from_external_cwd(tmp_path):
    """CLI defaults for protocol and pricing must resolve against --repository-root from any CWD."""
    manifest_path = _create_dev_run_with_journal(tmp_path)
    real_repo_root = Path(__file__).resolve().parents[1]

    # Populate default config directory in tmp_path so CLI default paths resolve against mock root
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    import shutil

    shutil.copy(
        real_repo_root / "config" / "experiment_protocol_v1.json",
        config_dir / "experiment_protocol_v1.json",
    )
    shutil.copy(
        real_repo_root / "config" / "pricing_v1.json",
        config_dir / "pricing_v1.json",
    )

    external_cwd = tmp_path.parent / "outside_cwd_test"
    external_cwd.mkdir(exist_ok=True)

    out_dir = tmp_path / "external_cwd_reports"

    cmd = [
        sys.executable,
        str(real_repo_root / "scripts" / "analysis" / "evaluate_rqs.py"),
        "--manifest",
        str(manifest_path),
        "--output-dir",
        str(out_dir),
        "--repository-root",
        str(tmp_path),
        "--bootstrap-samples",
        "20",
    ]

    proc = subprocess.run(cmd, cwd=external_cwd, capture_output=True, text=True, check=False)
    assert proc.returncode == 0, f"External CWD CLI failed: {proc.stderr}\n{proc.stdout}"
    assert (out_dir / "rq_analysis.json").exists()
    assert (out_dir / "rq_analysis_summary.md").exists()


def test_pair_cluster_bootstrap_resampling():
    """Pair-cluster bootstrap must resample clusters of views sharing pair_id together."""
    # 4 pairs (p0, p1, p2, p3), 2 views each (single, contextual)
    cluster_ids = ["p0", "p0", "p1", "p1", "p2", "p2", "p3", "p3"]
    treat = [1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0]
    base = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0]

    ci = compute_paired_bootstrap_ci(
        treat, base, cluster_ids=cluster_ids, num_samples=200, seed=123
    )
    assert ci["resampling_method"] == "pair_cluster_bootstrap"
    assert ci["cluster_count"] == 4
    assert ci["ci_lower"] <= ci["mean_delta"] <= ci["ci_upper"]


def test_rq2_independent_failure_axes_and_no_rag_na(tmp_path):
    """RQ2 enforces D2i independent failure axes and sets No-RAG retrieval metrics to None."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq2 = compute_rq2(inputs, proto)
    assert rq2["schema_version"] == "1.0.0"

    # 1. No-RAG: retrieval metrics must be None (not applicable)
    no_rag = rq2["by_condition"]["no_rag"]
    assert no_rag["retrieval_metrics"]["applicable"] is False
    assert no_rag["retrieval_metrics"]["macro_recall"] is None
    assert no_rag["retrieval_metrics"]["retrieval_hit_rate"] is None
    assert no_rag["generation_conditional_accuracy"]["applicable"] is False
    assert no_rag["generation_conditional_accuracy"]["p_correct_given_retrieval_success"] is None
    assert no_rag["independent_failure_axes"]["retrieval_miss_count"] is None

    # 2. RAG_k3: independent axes and overlaps
    k3 = rq2["by_condition"]["rag_k3"]
    axes = k3["independent_failure_axes"]
    assert axes["retrieval_miss_count"] is not None
    assert axes["provider_failure_count"] >= 0
    assert axes["parse_failure_count"] >= 0
    assert axes["invalid_attack_id_count"] >= 0
    assert axes["valid_but_wrong_classification_count"] >= 0
    assert "overlap_retrieval_miss_and_wrong_classification" in axes
    assert "overlap_retrieval_miss_and_provider_failure" in axes

    # Total failures
    assert k3["total_failures"] == (k3["total_scorable_samples"] - 3)


def test_rq3_view_diagnostics_scorable_counts(tmp_path):
    """View diagnostics must distinguish scorable single and contextual views."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq3 = compute_rq3(inputs, proto)
    v_diag = rq3["view_diagnostics"]["rag_k3"]

    assert "single_view_scorable_count" in v_diag
    assert "contextual_view_scorable_count" in v_diag
    assert "view_split_notes" in v_diag
    assert v_diag["single_view_scorable_count"] + v_diag["contextual_view_scorable_count"] == 6

    # UNIFIED_MAPPING_R2 complete paired diagnostics
    assert "single_paired_accuracy" in v_diag
    assert "contextual_paired_accuracy" in v_diag
    assert "paired_delta" in v_diag
    assert "gt_concordance_decomposition" in v_diag
    assert v_diag["paired_complete_pairs_count"] == 3
    assert v_diag["single_paired_accuracy"] == 1.0
    assert v_diag["contextual_paired_accuracy"] == 0.0
    assert v_diag["paired_delta"] == -1.0
    assert "identical_gt_pairs" in v_diag["gt_concordance_decomposition"]
    div_decomp = v_diag["gt_concordance_decomposition"]["divergent_gt_pairs"]
    assert div_decomp["pair_count"] == 3
    assert div_decomp["single_paired_accuracy"] == 1.0

    # True subset Macro-F1 across benchmark universe (14 in mock fixture)
    assert "single_view_macro_f1" in v_diag
    assert "contextual_view_macro_f1" in v_diag
    assert "view_macro_f1_delta" in v_diag
    u_size = len(inputs.corpus_ids)
    assert pytest.approx(v_diag["single_view_macro_f1"]) == 1.8 / u_size
    assert pytest.approx(v_diag["contextual_view_macro_f1"]) == 0.0
    assert pytest.approx(v_diag["view_macro_f1_delta"]) == -1.8 / u_size


def test_stratified_gt_complexity_producer(tmp_path):
    """Verify NEW PROPOSED PRODUCER partitions scorable views and preserves 474 universe."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    producer_out = compute_stratified_gt_complexity_producer(inputs, proto)
    assert (
        producer_out["producer_label"]
        == "NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis"
    )
    assert producer_out["protocol_approval_required"] is True
    assert producer_out["frozen_benchmark_universe_size"] == 474
    assert producer_out["multi_gt_semantics"] == "ANY_MATCH"
    assert set(producer_out["by_condition"].keys()) == set(CONDITIONS)

    row = producer_out["by_condition"]["rag_k3"]
    assert row["single_gt_sample_count"] == 5
    assert row["single_gt_correct_count"] == 2
    assert pytest.approx(row["single_gt_accuracy_e2e"]) == 0.4
    u_size = len(inputs.corpus_ids)
    assert "single_gt_macro_f1" in row
    assert pytest.approx(row["single_gt_macro_f1"]) == 1.0 / u_size
    assert row["multi_gt_sample_count"] == 1
    assert row["multi_gt_correct_count"] == 1
    assert pytest.approx(row["multi_gt_accuracy_e2e"]) == 1.0
    assert "multi_gt_macro_f1" in row
    assert pytest.approx(row["multi_gt_macro_f1"]) == 1.0 / u_size
    assert pytest.approx(row["complexity_accuracy_delta"]) == 0.6
    assert "complexity_macro_f1_delta" in row
    assert pytest.approx(row["complexity_macro_f1_delta"]) == 0.0
    assert row["overall_scorable_sample_count"] == 6
    assert pytest.approx(row["overall_scorable_accuracy_e2e"]) == 0.5
    assert "overall_macro_f1_reference" in row
    assert pytest.approx(row["overall_macro_f1_reference"]) == 1.3 / u_size


def test_subset_macro_f1_distinct_fixture_edge_cases(tmp_path):
    """Verify true subset Macro-F1 across 474 universe with distinct edge-case fixture.

    Tests:
    1. Discordant predictions between single and contextual views.
    2. Multi-label ground truth evaluated under ANY_MATCH.
    3. Mathematical divergence between subset Macro-F1 and overall condition Macro-F1.
    4. Edge case: Empty / null view subsets (e.g. contextual subset has 0 records).
    """
    fixture = _fixture_474(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    rq3 = compute_rq3(inputs, proto)
    strat = compute_stratified_gt_complexity_producer(inputs, proto)

    # Verify all 5 conditions have view subset Macro-F1 computed
    for cond in CONDITIONS:
        v_diag = rq3["view_diagnostics"][cond]
        assert "single_view_macro_f1" in v_diag
        assert "contextual_view_macro_f1" in v_diag
        assert "view_macro_f1_delta" in v_diag

        # Stratified producer has explicit subset Macro-F1 keys
        s_row = strat["by_condition"][cond]
        assert "single_gt_macro_f1" in s_row
        assert "multi_gt_macro_f1" in s_row
        assert "complexity_macro_f1_delta" in s_row
        assert "overall_macro_f1_reference" in s_row

        # Both subset Macro-F1 values are bounded in [0, 1]
        if v_diag["single_view_macro_f1"] is not None:
            assert 0.0 <= v_diag["single_view_macro_f1"] <= 1.0
        if v_diag["contextual_view_macro_f1"] is not None:
            assert 0.0 <= v_diag["contextual_view_macro_f1"] <= 1.0

        if s_row["single_gt_macro_f1"] is not None:
            assert 0.0 <= s_row["single_gt_macro_f1"] <= 1.0
        if s_row["multi_gt_macro_f1"] is not None:
            assert 0.0 <= s_row["multi_gt_macro_f1"] <= 1.0

    # Edge case: Empty subset handling
    # Create synthetic inputs with ONLY single-view records (0 contextual records)
    only_single_records = [r for r in inputs.records if r.get("view_type") == "single"]
    single_only_inputs = dataclasses.replace(inputs, records=only_single_records)
    rq3_single_only = compute_rq3(single_only_inputs, proto)
    cond_diag = rq3_single_only["view_diagnostics"]["rag_k1"]
    assert cond_diag["single_view_macro_f1"] is not None
    assert cond_diag["contextual_view_macro_f1"] is None
    assert cond_diag["view_macro_f1_delta"] is None

    # Create synthetic inputs with ONLY single-GT records (0 multi-GT records)
    single_gt_only_records = [
        r for r in inputs.records if len(inputs.ground_truth.get(r["sample_id"], ())) == 1
    ]
    single_gt_inputs = dataclasses.replace(inputs, records=single_gt_only_records)
    strat_single_only = compute_stratified_gt_complexity_producer(single_gt_inputs, proto)
    strat_row = strat_single_only["by_condition"]["rag_k1"]
    assert strat_row["single_gt_macro_f1"] is not None
    assert strat_row["multi_gt_macro_f1"] is None
    assert strat_row["complexity_macro_f1_delta"] is None


def test_mcnemar_test_statistical_properties():
    """Verify McNemar test computation on identical and divergent paired outcomes."""
    y_base = [True, False, True, True, False]
    y_treat = [True, False, True, True, False]
    res_ident = compute_mcnemar_test(y_base, y_treat)
    assert res_ident["p_value_exact"] == 1.0
    assert res_ident["chi2_statistic"] == 0.0
    assert res_ident["contingency_table"]["total_discordant"] == 0

    y_base = [False] * 10 + [True] * 5
    y_treat = [True] * 10 + [True] * 5
    res_div = compute_mcnemar_test(y_base, y_treat)
    assert res_div["contingency_table"]["treatment_win_b"] == 10
    assert res_div["contingency_table"]["baseline_win_c"] == 0
    assert res_div["contingency_table"]["total_discordant"] == 10
    assert res_div["p_value_exact"] < 0.01
    assert res_div["significant_at_01"] is True


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
    assert "new_proposed_producer_stratified_gt_complexity" in analysis
    producer_dict = analysis["new_proposed_producer_stratified_gt_complexity"]
    assert producer_dict["protocol_approval_required"] is True
    assert analysis["execution_mode"] == "mock_fixture"
    assert analysis["fixture_only"] is True
    assert analysis["provenance_status"] == "diagnostic_fixture"
    assert analysis["dataset_split"] == "test"

    json_path = out_dir / "rq_analysis.json"
    md_path = out_dir / "rq_analysis_summary.md"

    assert json_path.exists()
    assert md_path.exists()

    json_data = json.loads(json_path.read_bytes())
    assert json_data["experiment_id"] == inputs.experiment_id
    assert json_data["execution_mode"] == "mock_fixture"
    assert json_data["fixture_only"] is True
    assert json_data["provenance_status"] == "diagnostic_fixture"
    assert json_data["dataset_split"] == "test"
    assert "new_proposed_producer_stratified_gt_complexity" in json_data

    md_content = md_path.read_text(encoding="utf-8")
    assert "# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)" in md_content
    assert "- **Execution Mode**: `mock_fixture`" in md_content
    assert "- **Dataset Split / Scope**: `test`" in md_content
    assert "- **Provenance Status**: `diagnostic_fixture`" in md_content
    assert "> [!NOTE] Diagnostic Fixture Provenance" in md_content
    assert "It does not constitute canonical empirical research results." in md_content
    assert "## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)" in md_content
    assert "## RQ2: Retrieval vs. Generation Error Decomposition" in md_content
    assert "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs" in md_content
    assert "### Paired View Diagnostics (Single-View vs Contextual-View)" in md_content
    assert "#### Complete Pair Ground Truth Concordance Decomposition" in md_content
    assert (
        "## NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis"
        in md_content
    )


# ---------------------------------------------------------------------------
# Native Tariff Conformance & Differential Verification (B_NATIVE_TARIFF_REPAIR)
# ---------------------------------------------------------------------------


def test_native_tariff_positive_control_success():
    """Positive control: SUCCESS with 10 input/1 output tokens costs exactly $0.00000370."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-pos-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-pos-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00000370",
            "refund_usd": "2.15897870",
            "breach": False,
        },
    ]

    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)
    assert reconciled["journal_present"] is True
    assert reconciled["has_breach"] is False
    assert reconciled["settled_cost_by_condition"]["no_rag"] == Decimal("0.00000370")


def test_native_tariff_probe_rate_limit_charges_worst_case():
    """Probe 2: Terminal RATE_LIMIT with token usage retains worst attempt fee ($0.53974560)."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-rl-1",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    # If settlement claims token cost $0.00000370 instead of worst-case, fails closed
    events_undercharged = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "RATE_LIMIT",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-rl-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00000370",
            "refund_usd": "2.15897870",
            "breach": False,
        },
    ]
    with pytest.raises(ValueError, match="Journal settlement cost mismatch"):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_undercharged)

    # When settlement properly debits worst-case attempt fee $0.53974560, succeeds
    events_proper = list(events_undercharged)
    events_proper[-1] = {
        "event": "monetary_settle",
        "key": key,
        "record_sha256": rec_sha,
        "cost_usd": "0.53974560",
        "refund_usd": "1.61923680",
        "breach": False,
    }
    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events_proper)
    assert reconciled["settled_cost_by_condition"]["no_rag"] == Decimal("0.53974560")


def test_native_tariff_probe_missing_service_tier_breaches_fail_closed():
    """Probe 3: Receipt missing service_tier breaches native contract and fails closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-st-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": None,  # Missing service tier
            "model": "gpt-5.6-luna",
            "response_id": "resp-st-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.53974560",
            "refund_usd": "1.61923680",
            "breach": True,
        },
    ]

    with pytest.raises(
        ValueError, match="native contract breach.*mismatch with required 'default'"
    ):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)


def test_native_tariff_probe_foreign_model_breaches_fail_closed():
    """Probe 4: Receipt with foreign returned model breaches native contract and fails closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    pricing_cfg_with_expected = dict(pricing_cfg)
    pricing_cfg_with_expected["expected_model"] = "gpt-5.6-luna"

    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-fm-1",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "SUCCESS",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "claude-3-7-sonnet",  # Foreign model
            "response_id": "resp-fm-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.53974560",
            "refund_usd": "1.61923680",
            "breach": True,
        },
    ]

    with pytest.raises(ValueError, match="native contract breach.*!= expected 'gpt-5.6-luna'"):
        reconcile_journal_and_ledger([record], pricing_cfg_with_expected, journal_events=events)


def test_native_tariff_incomplete_status_with_tokens_computes_exact_tariff():
    """Terminal INCOMPLETE status with token usage calculates token tariff without breach."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-inc-1",
        "parse_status": "INCOMPLETE",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "INCOMPLETE",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-inc-1",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.00000370",
            "refund_usd": "2.15897870",
            "breach": False,
        },
    ]

    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)
    assert reconciled["has_breach"] is False
    assert reconciled["settled_cost_by_condition"]["no_rag"] == Decimal("0.00000370")


def test_native_tariff_transport_failures_charged_worst_case():
    """Transport failures (TIMEOUT/API_FAILURE) without token usage charge worst-case attempt."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "parse_status": "TIMEOUT",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 1,
            "attempt_index": 0,
            "status": "TIMEOUT",
            "input_tokens": None,
            "output_tokens": None,
            "service_tier": "default",
        },
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.53974560",
            "refund_usd": "1.61923680",
            "breach": False,
        },
    ]

    reconciled = reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)
    assert reconciled["has_breach"] is False
    assert reconciled["settled_cost_by_condition"]["no_rag"] == Decimal("0.53974560")


def test_native_tariff_final_receipt_drift_vs_record_breaches():
    """Record drift against final receipt (tokens, response_id, model) breaches native contract."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    key = ["s0", "no_rag"]

    base_rec = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 1,
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
        "model": "gpt-5.6-luna",
        "response_id": "resp-A",
        "parse_status": "VALID",
    }

    # 1. Token drift (prompt_tokens 100 != input_tokens 200)
    drift_tok_receipt = {
        "event": "attempt_receipt",
        "key": key,
        "ordinal": 1,
        "attempt_index": 0,
        "status": "SUCCESS",
        "input_tokens": 200,
        "output_tokens": 20,
        "cached_tokens": 0,
        "service_tier": "default",
        "model": "gpt-5.6-luna",
        "response_id": "resp-A",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(base_rec)).hexdigest()
    events_tok = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
        drift_tok_receipt,
        {"event": "complete", "key": key, "record_sha256": rec_sha},
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "0.53974560",
            "refund_usd": "1.61923680",
            "breach": True,
        },
    ]
    with pytest.raises(ValueError, match="native contract breach.*Token count mismatch"):
        reconcile_journal_and_ledger([base_rec], pricing_cfg, journal_events=events_tok)

    # 2. Response ID drift (record resp-A != receipt resp-B)
    drift_resp_receipt = dict(drift_tok_receipt)
    drift_resp_receipt["input_tokens"] = 100
    drift_resp_receipt["response_id"] = "resp-B"
    events_resp = list(events_tok)
    events_resp[2] = drift_resp_receipt
    with pytest.raises(ValueError, match="native contract breach.*Response ID mismatch"):
        reconcile_journal_and_ledger([base_rec], pricing_cfg, journal_events=events_resp)

    # 3. Model drift (record gpt-5.6-luna != receipt foreign-model)
    drift_model_receipt = dict(drift_tok_receipt)
    drift_model_receipt["input_tokens"] = 100
    drift_model_receipt["model"] = "foreign-model"
    events_model = list(events_tok)
    events_model[2] = drift_model_receipt
    with pytest.raises(ValueError, match="native contract breach.*Model mismatch"):
        reconcile_journal_and_ledger([base_rec], pricing_cfg, journal_events=events_model)


def test_native_tariff_logical_worst_ceiling_breach_fails_closed():
    """Requests exceeding logical worst-case reservation ($2.15898240) breach and fail closed."""
    from scripts.analysis.evaluate_rqs import load_pricing_config

    pricing_cfg, _ = load_pricing_config()
    # 5 attempts: 5 * 0.53974560 = 2.69872800 > logical worst 2.15898240
    record = {
        "sample_id": "s0",
        "condition": "no_rag",
        "manifest_sha256": "a" * 64,
        "request_attempt_count": 5,
        "prompt_tokens": 10,
        "completion_tokens": 1,
        "total_tokens": 11,
        "model": "gpt-5.6-luna",
        "response_id": "resp-final",
        "parse_status": "VALID",
    }
    rec_sha = hashlib.sha256(canonical_json_bytes(record)).hexdigest()
    key = ["s0", "no_rag"]

    events = [
        {"event": "header", "manifest_sha256": "a" * 64, "max_requests": 1},
        {"event": "monetary_reserve", "key": key, "amount_usd": "2.15898240"},
    ]
    for i in range(4):
        events.append(
            {
                "event": "attempt_receipt",
                "key": key,
                "ordinal": i + 1,
                "attempt_index": i,
                "status": "TIMEOUT",
                "input_tokens": None,
                "output_tokens": None,
                "service_tier": "default",
            }
        )
    events.append(
        {
            "event": "attempt_receipt",
            "key": key,
            "ordinal": 5,
            "attempt_index": 4,
            "status": "SUCCESS",
            "input_tokens": 10,
            "output_tokens": 1,
            "cached_tokens": 0,
            "service_tier": "default",
            "model": "gpt-5.6-luna",
            "response_id": "resp-final",
        }
    )
    events.append({"event": "complete", "key": key, "record_sha256": rec_sha})
    events.append(
        {
            "event": "monetary_settle",
            "key": key,
            "record_sha256": rec_sha,
            "cost_usd": "2.15898240",
            "refund_usd": "0.00000000",
            "breach": True,
        }
    )

    with pytest.raises(
        ValueError, match="native contract breach.*exceeds logical worst-case reservation"
    ):
        reconcile_journal_and_ledger([record], pricing_cfg, journal_events=events)


# ---------------------------------------------------------------------------
# Execution Mode & Provenance Boundary Verification (BD_MODE_BOUNDARY)
# ---------------------------------------------------------------------------


def test_provenance_mode_boundary_diagnostic_fixture(tmp_path):
    """BD_MODE_BOUNDARY: Diagnostic fixture data retains explicit non-canonical provenance."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    out_dir = tmp_path / "fixture_reports"
    analysis = run_rq_analysis(
        inputs,
        proto,
        bootstrap_samples=50,
        seed=42,
        output_dir=out_dir,
    )

    assert analysis["execution_mode"] == "mock_fixture"
    assert analysis["fixture_only"] is True
    assert analysis["provenance_status"] == "diagnostic_fixture"
    assert analysis["dataset_split"] == "test"

    md_path = out_dir / "rq_analysis_summary.md"
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")

    assert "- **Execution Mode**: `mock_fixture`" in md_content
    assert "- **Dataset Split / Scope**: `test`" in md_content
    assert "- **Provenance Status**: `diagnostic_fixture`" in md_content
    assert (
        "> [!NOTE] Diagnostic Fixture Provenance: This analysis was executed on "
        "diagnostic/mock fixture data"
    ) in md_content
    assert "It does not constitute canonical empirical research results." in md_content


def test_provenance_mode_boundary_canonical_study_positive_control(tmp_path):
    """BD_MODE_BOUNDARY: Canonical live test data earns canonical_study status without warning."""
    fixture = _fixture(tmp_path)
    inputs = _load(tmp_path, fixture)
    proto = _test_protocol()

    live_inputs = dataclasses.replace(inputs, execution_mode="live")

    out_dir = tmp_path / "canonical_reports"
    analysis = run_rq_analysis(
        live_inputs,
        proto,
        bootstrap_samples=50,
        seed=42,
        output_dir=out_dir,
    )

    assert analysis["execution_mode"] == "live"
    assert analysis["fixture_only"] is False
    assert analysis["provenance_status"] == "canonical_study"
    assert analysis["dataset_split"] == "test"

    md_path = out_dir / "rq_analysis_summary.md"
    assert md_path.exists()
    md_content = md_path.read_text(encoding="utf-8")

    assert "- **Execution Mode**: `live`" in md_content
    assert "- **Dataset Split / Scope**: `test`" in md_content
    assert "- **Provenance Status**: `canonical_study`" in md_content
    assert "Diagnostic Fixture Provenance" not in md_content
    assert "It does not constitute canonical empirical research results." not in md_content
