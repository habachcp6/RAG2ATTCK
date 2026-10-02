"""Unit tests for offline scientific report population helper tool (scripts/populate_report.py).

Verifies:
1. Safety boundary & Execution modes:
   - Canonical mode fails closed pending S2 seal.
   - Fails closed on uncertified non-fixture directories.
   - Requires all 6 canonical evaluator files + _fixture_metadata.json on disk.
   - Enforces strict boolean check for fixture_only is True (rejects truthiness).
2. Bundle manifest hash binding & Provenance consistency:
   - Requires protocol_version, experiment_id, and manifest_sha256 in bundle metadata.
   - Unconditionally requires uniform manifest, experiment, and protocol across all files.
   - Rejects mixed mode or missing provenance fields.
3. Schema & Metric bounds validation:
   - Rejects missing required fields with KeyError (no zero-defaults).
   - Rejects missing sum_prompt_tokens or sum_completion_tokens (no 1280-based fabrication).
   - Rejects NaN, Inf, and out-of-bounds numbers with ValueError.
   - Safely handles legitimate None without TypeError.
4. Correctness of derived metrics:
   - Scorable sample count derived from actual exports (not hardcoded 718).
   - Downstream selection failure: retrieval_success_count - retrieval_success_correct_count.
   - Table 4 for no_rag sets retrieval miss, selection failure, and recovery to 'N/A'.
5. End-to-end execution against reproduction fixture outputs.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.populate_report import (
    DEFAULT_FIXTURE_DIR,
    DEFAULT_SEAL_PATH,
    DEFAULT_TEMPLATE_PATH,
    DISCLAIMER_TEXT,
    REQUIRED_CANONICAL_FILES,
    REQUIRED_FIXTURE_FILES,
    assert_canonical_safety,
    assert_fixture_safety,
    build_prose_slots,
    compute_file_sha256,
    format_currency_value,
    format_int,
    format_latency,
    format_pct,
    format_pp,
    format_pvalue,
    format_usd,
    run_pipeline,
    validate_canonical_output,
    validate_finite_number,
)


@pytest.fixture
def real_fixture_copy(tmp_path: Path) -> Path:
    """Create an isolated temporary copy of the committed report fixtures."""
    dest = tmp_path / "fixture_diagnostics"
    dest.mkdir(parents=True)
    for fname in REQUIRED_FIXTURE_FILES:
        src = DEFAULT_FIXTURE_DIR / fname
        if not src.is_file():
            raise FileNotFoundError(f"Committed fixture file missing: {src}")
        shutil.copy2(src, dest / fname)
    return dest


# ==============================================================================
# 1. Mode Gate & Safety Boundary Tests
# ==============================================================================


def test_canonical_mode_fails_closed_without_seal(tmp_path: Path) -> None:
    """Safety gate: Canonical mode fails closed when root terminal audit seal is missing."""
    out_md = tmp_path / "out.md"
    non_existent_seal = tmp_path / "non_existent_seal.json"
    with pytest.raises(
        FileNotFoundError,
        match=r"\[FAIL_CLOSED\] Canonical run seal not found at:",
    ):
        run_pipeline(
            data_dir=DEFAULT_FIXTURE_DIR,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
            seal_path=non_existent_seal,
            mode="canonical",
        )


def test_unknown_mode_raises_value_error(tmp_path: Path) -> None:
    """Safety gate: Reject unknown execution modes."""
    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match="Unknown mode: unsupported"):
        run_pipeline(
            fixture_dir=DEFAULT_FIXTURE_DIR,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
            mode="unsupported",
        )


def test_safety_prevents_accidental_template_overwrite(
    real_fixture_copy: Path,
) -> None:
    """Safety test: Prohibits overwriting canonical template in-place without force flag."""
    with pytest.raises(ValueError, match=r"\[SAFETY_GUARD\]"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=DEFAULT_TEMPLATE_PATH,
            force_in_place=False,
        )


def test_assert_fixture_safety_rejects_uncertified_dir(tmp_path: Path) -> None:
    """Safety test: Fails closed when operating on uncertified directory without metadata."""
    unsafe_dir = tmp_path / "unsafe_dir"
    unsafe_dir.mkdir()

    with pytest.raises(
        RuntimeError, match=r"\[FAIL_CLOSED\] Fixture directory .* lacks _fixture_metadata\.json"
    ):
        assert_fixture_safety(unsafe_dir)


@pytest.mark.parametrize("invalid_flag", ["true", "True", 1, 0, False, ""])
def test_assert_fixture_safety_rejects_fixture_only_not_strictly_boolean(
    real_fixture_copy: Path, invalid_flag: object
) -> None:
    """Safety test: Fails closed when fixture_only is not strictly boolean True."""
    meta_file = real_fixture_copy / "_fixture_metadata.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    meta["fixture_only"] = invalid_flag
    meta_file.write_text(json.dumps(meta), encoding="utf-8")

    err_msg = r"\[FAIL_CLOSED\] _fixture_metadata\.json .* must declare fixture_only=True strictly"
    with pytest.raises(RuntimeError, match=err_msg):
        assert_fixture_safety(real_fixture_copy)


def test_assert_fixture_safety_accepts_valid_fixture(
    real_fixture_copy: Path,
) -> None:
    """Safety test: Accepts certified fixture directory."""
    assert_fixture_safety(real_fixture_copy)


# ==============================================================================
# 2. File Integrity & Provenance Consistency Tests (Reject Mixed Mode)
# ==============================================================================


@pytest.mark.parametrize("missing_file", REQUIRED_FIXTURE_FILES)
def test_missing_required_file_raises_file_not_found(
    real_fixture_copy: Path, missing_file: str, tmp_path: Path
) -> None:
    """Zero-default integrity: Deleting any required file raises FileNotFoundError."""
    target = real_fixture_copy / missing_file
    target.unlink()
    out_md = tmp_path / "out.md"

    with pytest.raises(
        FileNotFoundError,
        match=rf"\[FAIL_CLOSED\] Required fixture file missing:.*{missing_file}",
    ):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


@pytest.mark.parametrize("bundle_key", ["manifest_sha256", "experiment_id", "protocol_version"])
def test_missing_bundle_key_in_metadata_raises_key_error(
    real_fixture_copy: Path, bundle_key: str
) -> None:
    """Bundle binding: Missing manifest/experiment/protocol in metadata raises KeyError."""
    meta_file = real_fixture_copy / "_fixture_metadata.json"
    meta = json.loads(meta_file.read_text(encoding="utf-8"))
    del meta[bundle_key]
    meta_file.write_text(json.dumps(meta), encoding="utf-8")

    with pytest.raises(KeyError, match=rf"\[FAIL_CLOSED\] .* missing bundle key: '{bundle_key}'"):
        assert_fixture_safety(real_fixture_copy)


@pytest.mark.parametrize("bundle_key", ["manifest_sha256", "experiment_id", "protocol_version"])
def test_missing_provenance_field_in_eval_file_raises_key_error(
    real_fixture_copy: Path, bundle_key: str, tmp_path: Path
) -> None:
    """Unconditional provenance: Missing provenance field in evaluation output raises KeyError."""
    target_file = real_fixture_copy / "per_condition_metrics.json"
    doc = json.loads(target_file.read_text(encoding="utf-8"))
    del doc[bundle_key]
    target_file.write_text(json.dumps(doc), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(
        KeyError,
        match=rf"\[FAIL_CLOSED\] Required provenance field '{bundle_key}' missing",
    ):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_mixed_mode_protocol_version_raises_value_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Reject mixed mode: Mismatched protocol_version across files raises ValueError."""
    target_file = real_fixture_copy / "per_condition_metrics.json"
    doc = json.loads(target_file.read_text(encoding="utf-8"))
    doc["protocol_version"] = "mismatched-protocol-v999"
    target_file.write_text(json.dumps(doc), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Inconsistent protocol_version"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_mixed_mode_manifest_sha256_raises_value_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Reject mixed mode: Mismatched manifest_sha256 across files raises ValueError."""
    target_file = real_fixture_copy / "per_condition_metrics.json"
    doc = json.loads(target_file.read_text(encoding="utf-8"))
    doc["manifest_sha256"] = "deadbeef" * 8
    target_file.write_text(json.dumps(doc), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Inconsistent manifest_sha256"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_mixed_mode_experiment_id_raises_value_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Reject mixed mode: Mismatched experiment_id across files raises ValueError."""
    target_file = real_fixture_copy / "failure_decomposition.json"
    doc = json.loads(target_file.read_text(encoding="utf-8"))
    doc["experiment_id"] = "different_experiment_id"
    target_file.write_text(json.dumps(doc), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Inconsistent experiment_id"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_provenance_execution_mode_mismatch_raises_value_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Reject mixed mode: run_provenance execution_mode != 'mock_fixture' raises ValueError."""
    prov_file = real_fixture_copy / "run_provenance.json"
    prov = json.loads(prov_file.read_text(encoding="utf-8"))
    prov["execution_mode"] = "live_provider"
    prov_file.write_text(json.dumps(prov), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(
        ValueError, match=r"\[FAIL_CLOSED\] run_provenance execution_mode.*must be 'mock_fixture'"
    ):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


# ==============================================================================
# 3. Schema & Metric Bounds Validation (No Defaults, Finite Checking)
# ==============================================================================


def test_missing_required_field_raises_key_error(real_fixture_copy: Path, tmp_path: Path) -> None:
    """Zero-default schema: Missing required field raises KeyError (never defaults to 0)."""
    per_cond_file = real_fixture_copy / "per_condition_metrics.json"
    data = json.loads(per_cond_file.read_text(encoding="utf-8"))
    del data["conditions"]["rag_k1"]["accuracy_end_to_end"]
    per_cond_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(KeyError, match="rag_k1.*accuracy_end_to_end"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_missing_sum_prompt_tokens_raises_key_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Token sum integrity: Missing sum_prompt_tokens raises KeyError (no 1280 fabrication)."""
    rq_file = real_fixture_copy / "rq_analysis.json"
    data = json.loads(rq_file.read_text(encoding="utf-8"))
    del data["rq3"]["tradeoffs_by_condition"]["no_rag"]["tokens"]["sum_prompt_tokens"]
    rq_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(KeyError, match="Condition 'no_rag' missing 'sum_prompt_tokens'"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_missing_sum_completion_tokens_raises_key_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Token sum integrity: Missing sum_completion_tokens raises KeyError (no 1280 fabrication)."""
    rq_file = real_fixture_copy / "rq_analysis.json"
    data = json.loads(rq_file.read_text(encoding="utf-8"))
    del data["rq3"]["tradeoffs_by_condition"]["no_rag"]["tokens"]["sum_completion_tokens"]
    rq_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(KeyError, match="Condition 'no_rag' missing 'sum_completion_tokens'"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_non_finite_metric_raises_value_error(real_fixture_copy: Path, tmp_path: Path) -> None:
    """Finite validation: NaN or Inf in evaluation metrics raises ValueError."""
    per_cond_file = real_fixture_copy / "per_condition_metrics.json"
    data = json.loads(per_cond_file.read_text(encoding="utf-8"))
    data["conditions"]["rag_k1"]["macro_f1"] = float("nan")
    per_cond_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match="must be finite"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_out_of_bounds_metric_raises_value_error(real_fixture_copy: Path, tmp_path: Path) -> None:
    """Bounds validation: Accuracy > 1.0 raises ValueError."""
    per_cond_file = real_fixture_copy / "per_condition_metrics.json"
    data = json.loads(per_cond_file.read_text(encoding="utf-8"))
    data["conditions"]["rag_k1"]["accuracy_end_to_end"] = 1.05
    per_cond_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match="above allowable maximum"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_negative_downstream_selection_failure_raises_value_error(
    real_fixture_copy: Path, tmp_path: Path
) -> None:
    """Identity guard: Negative downstream selection failure raises ValueError."""
    ret_file = real_fixture_copy / "retrieval_conditional_metrics.json"
    data = json.loads(ret_file.read_text(encoding="utf-8"))
    # retrieval_success_count (1) < retrieval_success_correct_count (2) -> impossible
    data["by_condition"]["rag_k1"]["retrieval_success_count"] = 1
    data["by_condition"]["rag_k1"]["retrieval_success_correct_count"] = 2
    ret_file.write_text(json.dumps(data), encoding="utf-8")

    out_md = tmp_path / "out.md"
    with pytest.raises(ValueError, match="Negative downstream selection failure for rag_k1: -1"):
        run_pipeline(
            fixture_dir=real_fixture_copy,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
        )


def test_legitimate_none_formatting() -> None:
    """Legitimate null: None is safely formatted as 'N/A' without TypeError."""
    assert format_pct(None) == "N/A"
    assert format_pp(None) == "N/A"
    assert format_int(None) == "N/A"
    assert format_usd(None) == "N/A"
    assert format_latency(None) == "N/A"

    assert validate_finite_number(None, "opt_field", allow_none=True) is None
    with pytest.raises(KeyError, match="Required field req_field is None"):
        validate_finite_number(None, "req_field", allow_none=False)


# ==============================================================================
# 4. Functional End-to-End Pipeline Execution
# ==============================================================================


def test_run_pipeline_end_to_end_authoritative_fixture(tmp_path: Path) -> None:
    """Functional test: Populates report markdown and audit JSON from authoritative fixtures."""
    out_md = tmp_path / "test_report.md"
    out_json = tmp_path / "test_slots.json"

    run_pipeline(
        fixture_dir=DEFAULT_FIXTURE_DIR,
        template_path=DEFAULT_TEMPLATE_PATH,
        output_path=out_md,
        audit_json_path=out_json,
    )

    assert out_md.is_file()
    assert out_json.is_file()

    content = out_md.read_text(encoding="utf-8")

    # 1. Private label banner & disclaimer check
    assert "<!-- FIXTURE_ONLY: true -->" in content
    assert DISCLAIMER_TEXT in content

    # 2. Table population check: No TBD in populated rows
    lines = content.splitlines()
    table_rows = [line for line in lines if line.strip().startswith("| `")]
    assert len(table_rows) > 0, "No populated table rows found"
    for row in table_rows:
        assert "[TBD_AT_EXECUTION]" not in row, f"Found unpopulated row: {row}"

    # 3. Dynamic scorable count verification (derived from fixture exports, e.g. 6)
    slots = json.loads(out_json.read_text(encoding="utf-8"))
    expected_scorable = slots["table_2a"]["no_rag"]["scorable_n"]
    assert expected_scorable == 6, f"Expected dynamic scorable count 6, got {expected_scorable}"

    # 4. Table 4 identity verification
    # no_rag must have "N/A" for retrieval-conditioned metrics
    no_rag_t4 = slots["table_4"]["no_rag"]
    assert no_rag_t4["retrieval_miss"] == "N/A"
    assert no_rag_t4["downstream_selection_failure"] == "N/A"
    assert no_rag_t4["parametric_recovery"] == "N/A"

    # rag_k1 downstream_selection_failure = (
    #     retrieval_success_count - retrieval_success_correct_count
    # )
    # In fixture: retrieval_success_count = 2, retrieval_success_correct_count = 1 -> difference = 1
    rag_k1_t4 = slots["table_4"]["rag_k1"]
    assert rag_k1_t4["downstream_selection_failure"] == "1"

    # 5. Table 5 verified native token sums (not fabricated from mean * 1280)
    no_rag_t5 = slots["table_5"]["no_rag"]
    assert no_rag_t5["total_input_tokens"] == "3,215"
    assert no_rag_t5["total_output_tokens"] == "1,121"
    # Ensure no fabricated totals (e.g. 643 * 1280 = 823,040)
    assert "823,040" not in content

    # 6. Table 6 cryptographic manifest preservation
    assert "*Table 6: Cryptographic Reproducibility Manifest.*" in content
    assert "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c" in content

    # 7. Supplementary Execution Provenance check
    assert "#### Supplementary Execution Provenance (Diagnostic Fixture Mode)" in content
    assert "run_provenance.json" in content
    assert "retrieval_conditional_metrics.json" in content
    assert "overall_metrics.json" in content

    # 8. Audit JSON structure and safety metadata
    assert slots["_metadata"]["fixture_only"] is True
    assert slots["_metadata"]["disclaimer"] == DISCLAIMER_TEXT


@pytest.fixture
def canonical_bundle(tmp_path: Path) -> tuple[Path, Path]:
    """Create an isolated temporary canonical evaluation bundle and valid metric bundle."""
    bundle_dir = tmp_path / "canonical_diagnostics"
    bundle_dir.mkdir(parents=True)
    for fname in REQUIRED_CANONICAL_FILES:
        src = DEFAULT_FIXTURE_DIR / fname
        if not src.is_file():
            raise FileNotFoundError(f"Fixture file missing: {src}")
        shutil.copy2(src, bundle_dir / fname)

    # Update run_provenance.json to canonical / live
    prov_path = bundle_dir / "run_provenance.json"
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    prov["fixture_only"] = False
    prov["execution_mode"] = "live"
    prov_path.write_text(json.dumps(prov, indent=2), encoding="utf-8")

    # Update rq_analysis.json to canonical / live
    rq_path = bundle_dir / "rq_analysis.json"
    rq = json.loads(rq_path.read_text(encoding="utf-8"))
    rq["fixture_only"] = False
    rq["execution_mode"] = "live"
    rq["provenance_status"] = "canonical_study"
    # Ensure cluster count and delta fields exist for all conditions
    if "rq1" in rq and "by_condition" in rq["rq1"]:
        for c in ("rag_k1", "rag_k3", "rag_k5", "rag_k10"):
            if c in rq["rq1"]["by_condition"]:
                rq["rq1"]["by_condition"][c]["cluster_count"] = 440
                if "delta_vs_baseline" not in rq["rq1"]["by_condition"][c]:
                    rq["rq1"]["by_condition"][c]["delta_vs_baseline"] = {}
                d_info = rq["rq1"]["by_condition"][c]["delta_vs_baseline"]
                d_info["delta_accuracy_e2e_ci_95"] = [-0.01758, 0.04846]
                d_info["mcnemar_test"] = {
                    "p_value_exact": 0.422,
                    "contingency_table": {
                        "both_correct_a": 536,
                        "treatment_win_b": 35,
                        "baseline_win_c": 24,
                        "both_incorrect_d": 123,
                    },
                }
    if "rq3" in rq:
        rq["rq3"]["whole_study_financial_accounting"] = {
            "total_study_budget_usd": 19.99,
            "canonical_conditions_total_usd": 6.57575890,
            "prior_pilot_provisional_hold_usd": 0.05264010,
            "active_reservations_usd": 0.0,
            "orphan_reservations_usd": 0.0,
            "total_study_committed_spend_usd": 6.62839900,
            "net_remaining_uncommitted_budget_usd": 13.36160100,
        }
    rq_path.write_text(json.dumps(rq, indent=2), encoding="utf-8")

    # Compute actual hashes of the 8 canonical output files
    output_digests = {
        fname: compute_file_sha256(bundle_dir / fname) for fname in REQUIRED_CANONICAL_FILES
    }

    # Create certified terminal seal matching bundle
    term_seal_path = tmp_path / "root_canonical_snapshot_seal_v1.json"
    term_seal_data = {
        "seal_version": "1.0.0",
        "seal_status": "CERTIFIED_CANONICAL_AUDIT_SEAL",
        "experiment_id": "known-answer-only",
        "protocol_version": "experiment-protocol-v1",
        "created_at_utc": "2026-10-02T10:00:00Z",
    }
    term_seal_path.write_text(json.dumps(term_seal_data, indent=2), encoding="utf-8")
    term_seal_hash = compute_file_sha256(term_seal_path)

    # Create certified root verification document
    root_verif_path = tmp_path / "root_canonical_export_validation_v2.json"
    root_verif_data = {
        "verdict": "PASS",
        "overall_verdict": "PASS",
        "native_verdict": "PASS",
        "rq1_and_settled_totals_verdict": "PASS",
        "rq2_and_attempt_usage_verdict": "PASS",
        "defects": [],
    }
    root_verif_path.write_text(json.dumps(root_verif_data, indent=2), encoding="utf-8")
    root_verif_hash = compute_file_sha256(root_verif_path)

    manifest_file_hash = "66b658cfa9dd42e131ec567bbe043b8bc87ac6e92aeaa5e8f6661b0195e486e5"
    manifest_semantic_hash = "acf4f5383ad2387e6a21006aae83ba728c7ccb15c9114052e48babfd00e6081e"

    source_digests = {
        ".study_anchor.json": "a" * 64,
        "manifest.json": manifest_file_hash,
        "no_rag_predictions.jsonl": "b" * 64,
        "rag_k10_predictions.jsonl": "c" * 64,
        "rag_k1_predictions.jsonl": "d" * 64,
        "rag_k3_predictions.jsonl": "e" * 64,
        "rag_k5_predictions.jsonl": "f" * 64,
        "request_journal.jsonl": "0" * 64,
        "run_summary.json": "1" * 64,
        "study_ledger.json": "2" * 64,
    }

    # Create certified metric bundle matching bundle hashes
    seal_path = tmp_path / "canonical_metric_bundle_v1.json"
    seal_data = {
        "schema_version": "1.0.0",
        "bundle_type": "canonical-metric-bundle-v1",
        "seal_status": "CERTIFIED_CANONICAL_AUDIT_SEAL",
        "experiment_id": "known-answer-only",
        "protocol_version": "experiment-protocol-v1",
        "fixture_only": False,
        "execution_mode": "live",
        "dataset_split": "test",
        "manifest_file_sha256": manifest_file_hash,
        "manifest_semantic_sha256": manifest_semantic_hash,
        "manifest_sha256": manifest_semantic_hash,
        "source_file_digests": source_digests,
        "output_file_digests": output_digests,
        "terminal_seal": {
            "path": str(term_seal_path),
            "sha256": term_seal_hash,
        },
        "root_verification": {
            "verdict": "PASS",
            "path": str(root_verif_path),
            "sha256": root_verif_hash,
        },
    }
    seal_path.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    return bundle_dir, seal_path


# ==============================================================================
# 5. Canonical Mode & Validation Gate Tests
# ==============================================================================


def test_run_pipeline_canonical_mode_success(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical mode functional test: Executes end-to-end with certified seal."""
    bundle_dir, seal_path = canonical_bundle
    out_md = tmp_path / "canonical_report.md"
    out_json = tmp_path / "canonical_slots.json"

    run_pipeline(
        data_dir=bundle_dir,
        seal_path=seal_path,
        template_path=DEFAULT_TEMPLATE_PATH,
        output_path=out_md,
        audit_json_path=out_json,
        mode="canonical",
    )

    assert out_md.is_file()
    assert out_json.is_file()

    content = out_md.read_text(encoding="utf-8")

    # 1. No fixture warning banner or disclaimer
    assert "<!-- FIXTURE_ONLY: true -->" not in content
    assert DISCLAIMER_TEXT not in content

    # 2. Certified status header and audit note block
    assert "**Status:** CERTIFIED CANONICAL EXPERIMENTAL EVALUATION" in content
    assert "CANONICAL RUN AUDIT SEAL VERIFIED" in content
    assert "CERTIFIED_CANONICAL_AUDIT_SEAL" in content

    # 3. Section 6 intro transformed
    assert "canonical live experimental execution matrix" in content

    # 4. Schema markers stripped from table titles
    assert (
        "*Table 2a: Primary Attribution Performance and Ground-Truth Complexity Across Conditions.*"
        in content
    )
    assert (
        "*Table 3b: Paired Scorable Representation Concordance and McNemar "
        "Discordance ($N=278$ complete pairs).*" in content
    )
    assert "*Table 5b: Whole-Study Financial Ledger and Budget Reconciliation.*" in content

    # 5. Zero unpopulated execution placeholders
    assert "[TBD_AT_EXECUTION]" not in content
    assert "[PENDING" not in content

    # 6. Supplementary provenance table
    assert "#### Supplementary Execution Provenance (Canonical Run Mode)" in content
    assert "canonical_metric_bundle_v1.json" in content

    # 7. Audit JSON metadata
    slots = json.loads(out_json.read_text(encoding="utf-8"))
    assert slots["_metadata"]["fixture_only"] is False
    assert slots["_metadata"]["seal_status"] == "CERTIFIED_CANONICAL_AUDIT_SEAL"
    assert slots["_metadata"]["experiment_id"] == "known-answer-only"

    # 8. Table 2a has 9 columns populated
    t2a_no_rag = slots["table_2a"]["no_rag"]
    assert "single_gt_accuracy_e2e" in t2a_no_rag
    assert "multi_gt_accuracy_e2e" in t2a_no_rag
    assert "complexity_accuracy_delta" in t2a_no_rag

    # 9. Table 3b has 10 columns populated
    t3b_no_rag = slots["table_3b"]["no_rag"]
    assert t3b_no_rag["complete_pairs"] == "278"
    assert t3b_no_rag["mcnemar_p_exact"] == "1.0000"

    # 10. Table 5b has 7 ledger metrics populated
    t5b = slots["table_5b"]
    assert t5b["total_study_budget_usd"] == "19.99"
    assert t5b["canonical_conditions_total_usd"] == "6.5758"


def test_canonical_mode_rejects_missing_seal_file(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Missing seal file raises FileNotFoundError."""
    bundle_dir, _ = canonical_bundle
    missing_seal = tmp_path / "non_existent.json"
    out_md = tmp_path / "out.md"

    with pytest.raises(FileNotFoundError, match=r"\[FAIL_CLOSED\] Canonical run seal not found"):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=missing_seal,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_invalid_seal_status(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Non-certified seal status raises ValueError."""
    bundle_dir, seal_path = canonical_bundle
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["seal_status"] = "PROVISIONAL_SEAL"
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    out_md = tmp_path / "out.md"

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Invalid seal_status"):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_missing_seal_key(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Missing required key in seal raises KeyError."""
    bundle_dir, seal_path = canonical_bundle
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    del seal["manifest_file_sha256"]
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    out_md = tmp_path / "out.md"

    with pytest.raises(
        KeyError, match=r"\[FAIL_CLOSED\] .* missing required key: 'manifest_file_sha256'"
    ):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_fixture_provenance(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Mock fixture provenance in canonical mode raises ValueError."""
    bundle_dir, seal_path = canonical_bundle
    prov_file = bundle_dir / "run_provenance.json"
    prov = json.loads(prov_file.read_text(encoding="utf-8"))
    prov["fixture_only"] = True
    prov_file.write_text(json.dumps(prov), encoding="utf-8")

    # Update output digest in seal so disk-hash check passes and provenance check fires
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["output_file_digests"]["run_provenance.json"] = compute_file_sha256(prov_file)
    seal_path.write_text(json.dumps(seal), encoding="utf-8")

    out_md = tmp_path / "out.md"

    with pytest.raises(
        ValueError, match=r"\[FAIL_CLOSED\] run_provenance\.json .* fixture_only=False strictly"
    ):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_mismatched_seal_hash(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Seal manifest hash mismatch across files raises ValueError."""
    bundle_dir, seal_path = canonical_bundle
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    bad_hash = "deadbeef" * 8
    seal["manifest_file_sha256"] = bad_hash
    seal["manifest_semantic_sha256"] = bad_hash
    seal["manifest_sha256"] = bad_hash
    seal["source_file_digests"]["manifest.json"] = bad_hash
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    out_md = tmp_path / "out.md"

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Inconsistent manifest_sha256"):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_missing_complexity(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Missing ground-truth complexity in rq_analysis raises KeyError."""
    bundle_dir, seal_path = canonical_bundle
    rq_file = bundle_dir / "rq_analysis.json"
    rq = json.loads(rq_file.read_text(encoding="utf-8"))
    del rq["new_proposed_producer_stratified_gt_complexity"]
    rq_file.write_text(json.dumps(rq), encoding="utf-8")

    # Update output digest in seal so disk-hash check passes and complexity check fires
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["output_file_digests"]["rq_analysis.json"] = compute_file_sha256(rq_file)
    seal_path.write_text(json.dumps(seal), encoding="utf-8")

    out_md = tmp_path / "out.md"

    with pytest.raises(KeyError, match=r"new_proposed_producer_stratified_gt_complexity"):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_mode_rejects_missing_whole_study_accounting(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Canonical gate: Missing whole study accounting in rq_analysis raises KeyError."""
    bundle_dir, seal_path = canonical_bundle
    rq_file = bundle_dir / "rq_analysis.json"
    rq = json.loads(rq_file.read_text(encoding="utf-8"))
    if "whole_study_financial_accounting" in rq.get("rq3", {}):
        del rq["rq3"]["whole_study_financial_accounting"]
    if "whole_study_accounting" in rq.get("rq3", {}):
        del rq["rq3"]["whole_study_accounting"]
    rq_file.write_text(json.dumps(rq), encoding="utf-8")

    # Update output digest in seal so disk-hash check passes and accounting check fires
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    seal["output_file_digests"]["rq_analysis.json"] = compute_file_sha256(rq_file)
    seal_path.write_text(json.dumps(seal), encoding="utf-8")

    out_md = tmp_path / "out.md"

    with pytest.raises(KeyError, match=r"rq3\.whole_study_financial_accounting"):
        run_pipeline(
            data_dir=bundle_dir,
            seal_path=seal_path,
            output_path=out_md,
            mode="canonical",
        )


def test_canonical_output_gate_catches_unpopulated_placeholders() -> None:
    """Output gate: Leftover execution placeholders in canonical output raise RuntimeError."""
    sample_text = "Some report section with [TBD_AT_EXECUTION] in a row."
    with pytest.raises(
        RuntimeError, match=r"\[CANONICAL_GATE_VIOLATION\] Found 1 execution placeholders"
    ):
        validate_canonical_output(sample_text)

    sample_text_pending = "Another section with [PENDING_CANONICAL_EXECUTION]."
    with pytest.raises(
        RuntimeError, match=r"\[CANONICAL_GATE_VIOLATION\] Found 1 execution placeholders"
    ):
        validate_canonical_output(sample_text_pending)


def test_canonical_output_gate_catches_fixture_and_scaffold_markers() -> None:
    """Output gate: Fixture markers or scaffold conclusions raise RuntimeError."""
    sample_text = (
        "This report contains DIAGNOSTIC TEST FIXTURE ONLY - NOT CANONICAL NUMERICAL RESULTS."
    )
    with pytest.raises(
        RuntimeError, match=r"\[CANONICAL_GATE_VIOLATION\] Found 1 fixture/scaffold markers"
    ):
        validate_canonical_output(sample_text)

    sample_scaffold = "This is a scaffold conclusion phrase."
    with pytest.raises(
        RuntimeError, match=r"\[CANONICAL_GATE_VIOLATION\] Found 1 fixture/scaffold markers"
    ):
        validate_canonical_output(sample_scaffold)


def test_canonical_metric_bundle_contract_success(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Metric Bundle Contract: Executes canonical pipeline using canonical-metric-bundle-v1."""
    bundle_dir, seal_path = canonical_bundle
    out_md = tmp_path / "bundle_canonical_report.md"
    out_json = tmp_path / "bundle_canonical_slots.json"

    run_pipeline(
        data_dir=bundle_dir,
        metric_bundle=seal_path,
        template_path=DEFAULT_TEMPLATE_PATH,
        output_path=out_md,
        audit_json_path=out_json,
        mode="canonical",
    )

    assert out_md.is_file()
    assert out_json.is_file()

    content = out_md.read_text(encoding="utf-8")
    assert "**Status:** CERTIFIED CANONICAL EXPERIMENTAL EVALUATION" in content
    assert "CANONICAL RUN AUDIT SEAL VERIFIED" in content
    assert "canonical-metric-bundle-v1" in content
    assert "[TBD_AT_EXECUTION]" not in content


def test_canonical_metric_bundle_rejects_output_file_digest_mismatch(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Metric Bundle Gate: Output file digest mismatch raises ValueError."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    seal_data["output_file_digests"]["per_condition_metrics.json"] = "deadbeef" * 8
    corrupted_bundle_path = tmp_path / "corrupted_bundle.json"
    corrupted_bundle_path.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"\[FAIL_CLOSED\] Output file digest mismatch for per_condition_metrics\.json",
    ):
        run_pipeline(
            data_dir=bundle_dir,
            metric_bundle=corrupted_bundle_path,
            output_path=tmp_path / "out.md",
            mode="canonical",
        )


def test_canonical_metric_bundle_rejects_terminal_seal_hash_mismatch(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Metric Bundle Gate: Terminal seal hash mismatch raises ValueError."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    seal_data["terminal_seal"]["sha256"] = "deadbeef" * 8
    bad_seal_bundle_path = tmp_path / "bad_seal_bundle.json"
    bad_seal_bundle_path.write_text(json.dumps(seal_data, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Terminal seal hash mismatch"):
        run_pipeline(
            data_dir=bundle_dir,
            metric_bundle=bad_seal_bundle_path,
            output_path=tmp_path / "out.md",
            mode="canonical",
        )


def test_format_helpers_and_constants() -> None:
    """Format helpers format p-values and currency, and constants are verified."""
    assert format_currency_value(6.5757589) == "6.5758"
    assert format_currency_value(19.99) == "19.99"
    assert format_currency_value(0.0) == "0.00"
    assert format_currency_value(None) == "N/A"

    assert format_pvalue(0.040123) == "0.0401"
    assert format_pvalue(0.00005) == "< 0.0001"
    assert format_pvalue(None) == "N/A"

    assert DEFAULT_SEAL_PATH.name == "canonical_metric_bundle_v1.json"


def test_assert_canonical_safety_standalone(canonical_bundle: tuple[Path, Path]) -> None:
    """Standalone unit check on assert_canonical_safety function."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    # Should succeed without error on valid canonical inputs
    assert_canonical_safety(
        data_dir=bundle_dir,
        seal_path=seal_path,
        seal=seal_data,
        provenance=prov_data,
        analysis=rq_data,
    )


def test_distinct_rq1_vs_rq3_mcnemar_p_values_no_collision(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """Ensure RQ1 depth-vs-baseline and RQ3 McNemar p-values use distinct namespaces."""
    bundle_dir, seal_path = canonical_bundle
    from scripts.populate_report import extract_slots, load_report_data

    data = load_report_data(bundle_dir, mode="canonical", seal_path=seal_path)

    # Inject distinct p-values to verify no collision occurs
    data["rq_analysis"]["rq1"]["by_condition"]["rag_k10"]["delta_vs_baseline"]["mcnemar_test"][
        "p_value_exact"
    ] = 0.422
    data["rq_analysis"]["rq3"]["view_diagnostics"]["rag_k10"]["mcnemar_test_views_exploratory"][
        "p_value_exact"
    ] = 1.0

    table_slots = extract_slots(data, mode="canonical", seal_path=seal_path)
    slots = build_prose_slots(data, table_slots, mode="canonical")

    # RQ1 depth vs baseline p-values
    assert slots["RQ1_K10_MCNEMAR_P_EXACT"] == "0.422"
    # RQ3 view discordance p-values
    assert slots["RAG_K10_VIEW_MCNEMAR_P_EXACT"] == "1.000"
    assert slots["RQ3_K10_VIEW_MCNEMAR_P_EXACT"] == "1.000"
    assert slots["RQ1_K10_MCNEMAR_P_EXACT"] != slots["RAG_K10_VIEW_MCNEMAR_P_EXACT"]


def test_canonical_mode_rejects_missing_keys_without_hardcoded_fallback(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """Canonical mode fails closed (KeyError) when required empirical metrics are missing."""
    bundle_dir, seal_path = canonical_bundle
    from scripts.populate_report import extract_slots, load_report_data

    data = load_report_data(bundle_dir, mode="canonical", seal_path=seal_path)
    table_slots = extract_slots(data, mode="canonical", seal_path=seal_path)

    # Remove cluster_count completely
    if "cluster_count" in data["rq_analysis"]["rq1"]:
        del data["rq_analysis"]["rq1"]["cluster_count"]
    for c in ("rag_k1", "rag_k3", "rag_k5", "rag_k10"):
        if "cluster_count" in data["rq_analysis"]["rq1"]["by_condition"].get(c, {}):
            del data["rq_analysis"]["rq1"]["by_condition"][c]["cluster_count"]

    with pytest.raises(KeyError, match=r"cluster_count"):
        build_prose_slots(data, table_slots, mode="canonical")


def test_canonical_mode_fails_on_missing_output_file_on_disk(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """assert_canonical_safety fails closed if canonical output file is missing on disk."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    # Delete one canonical file
    (bundle_dir / "per_condition_metrics.json").unlink()

    with pytest.raises(
        FileNotFoundError,
        match=r"\[FAIL_CLOSED\] Required canonical output file missing on disk",
    ):
        assert_canonical_safety(
            data_dir=bundle_dir,
            seal_path=seal_path,
            seal=seal_data,
            provenance=prov_data,
            analysis=rq_data,
        )


def test_canonical_mode_fails_on_missing_terminal_seal_file_on_disk(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """assert_canonical_safety fails closed if terminal_seal.path does not exist on disk."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    seal_data["terminal_seal"]["path"] = str(tmp_path / "non_existent_terminal_seal.json")

    with pytest.raises(
        FileNotFoundError,
        match=r"\[FAIL_CLOSED\] Terminal seal file missing on disk",
    ):
        assert_canonical_safety(
            data_dir=bundle_dir,
            seal_path=seal_path,
            seal=seal_data,
            provenance=prov_data,
            analysis=rq_data,
        )


def test_canonical_mode_fails_on_missing_root_verification_doc_on_disk(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """assert_canonical_safety fails closed if root_verification.path does not exist on disk."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    seal_data["root_verification"]["path"] = str(tmp_path / "non_existent_root_verif.json")

    with pytest.raises(
        FileNotFoundError,
        match=r"\[FAIL_CLOSED\] Root verification document missing on disk",
    ):
        assert_canonical_safety(
            data_dir=bundle_dir,
            seal_path=seal_path,
            seal=seal_data,
            provenance=prov_data,
            analysis=rq_data,
        )


def test_canonical_mode_fails_on_root_defects_or_fail_verdict(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """assert_canonical_safety fails closed if root verification has defects or FAIL verdict."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    root_path = Path(seal_data["root_verification"]["path"])
    root_data = json.loads(root_path.read_text(encoding="utf-8"))
    root_data["defects"] = ["Detected discrepancy in metric calculation"]
    root_path.write_text(json.dumps(root_data), encoding="utf-8")
    seal_data["root_verification"]["sha256"] = compute_file_sha256(root_path)

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Root verification contains defects"):
        assert_canonical_safety(
            data_dir=bundle_dir,
            seal_path=seal_path,
            seal=seal_data,
            provenance=prov_data,
            analysis=rq_data,
        )


def test_canonical_mode_accepts_producer_b_canonical_study(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """assert_canonical_safety accepts Specialist B's 'canonical_study' status in rq_analysis."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    rq_data["provenance_status"] = "canonical_study"
    assert_canonical_safety(
        data_dir=bundle_dir,
        seal_path=seal_path,
        seal=seal_data,
        provenance=prov_data,
        analysis=rq_data,
    )


def test_canonical_mode_accepts_native_run_provenance_without_fixture_only(
    canonical_bundle: tuple[Path, Path],
) -> None:
    """assert_canonical_safety accepts native run_provenance.json without fixture_only key."""
    bundle_dir, seal_path = canonical_bundle
    seal_data = json.loads(seal_path.read_text(encoding="utf-8"))
    prov_data = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    rq_data = json.loads((bundle_dir / "rq_analysis.json").read_text(encoding="utf-8"))

    if "fixture_only" in prov_data:
        del prov_data["fixture_only"]
    prov_data["execution_mode"] = "live"

    assert_canonical_safety(
        data_dir=bundle_dir,
        seal_path=seal_path,
        seal=seal_data,
        provenance=prov_data,
        analysis=rq_data,
    )


def test_docx_renderer_preserves_distinct_conditional_probability_labels():
    pytest.importorskip("docx", reason="Optional Word authoring dependency")
    from scripts.export_report_docx import latex_to_unicode

    hit = latex_to_unicode(r"P(\text{Correct}\mid\text{Retrieved}) = 91.28\%")
    miss = latex_to_unicode(r"P(\text{Correct}\mid\text{Absent}) = 70.03\%")
    assert hit == "P(Correct | Retrieved) = 91.28%"
    assert miss == "P(Correct | Absent) = 70.03%"


def test_export_report_docx_resolves_custom_figures_dir(tmp_path: Path) -> None:
    pytest.importorskip("docx", reason="Optional Word authoring dependency")
    from scripts.export_report_docx import build_docx_from_markdown

    custom_fig_dir = tmp_path / "custom_figures"
    custom_fig_dir.mkdir()
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00"
        b"\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    (custom_fig_dir / "figure1_f1_vs_context_length.png").write_bytes(png_bytes)

    md_file = tmp_path / "report.md"
    md_content = (
        "# Minimal Test\n\n"
        "![Figure 1](figure1_f1_vs_context_length.png)\n"
        "*Figure 1: Test caption*\n"
    )
    md_file.write_text(md_content, encoding="utf-8")
    docx_file = tmp_path / "report.docx"

    build_docx_from_markdown(md_file, docx_file, figures_dir=custom_fig_dir)
    assert docx_file.is_file()
    assert docx_file.stat().st_size > 0


def test_run_pipeline_copies_figures_to_target_output_dir(
    tmp_path: Path, canonical_bundle: tuple[Path, Path]
) -> None:
    from scripts.populate_report import run_pipeline

    bundle_dir, seal_path = canonical_bundle
    out_dir = tmp_path / "report_out"
    out_md = out_dir / "scientific_report.md"

    custom_fig_dir = tmp_path / "src_figures"
    custom_fig_dir.mkdir()
    (custom_fig_dir / "figure1_f1_vs_context_length.png").write_bytes(b"dummy_png")
    (custom_fig_dir / "figure_provenance.json").write_text("{}", encoding="utf-8")

    run_pipeline(
        data_dir=bundle_dir,
        seal_path=seal_path,
        output_path=out_md,
        audit_json_path=out_dir / "slots.json",
        mode="canonical",
        figures_dir=custom_fig_dir,
    )

    assert (out_dir / "figures" / "figure1_f1_vs_context_length.png").is_file()
    assert (out_dir / "figures" / "figure_provenance.json").is_file()
