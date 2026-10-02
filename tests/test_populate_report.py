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
    """Create an isolated temporary canonical evaluation bundle and valid seal."""
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
    rq["provenance_status"] = "canonical"
    rq_path.write_text(json.dumps(rq, indent=2), encoding="utf-8")

    # Create certified seal matching bundle hashes
    seal_path = tmp_path / "canonical_run_seal_v1.json"
    seal_data = {
        "seal_version": "1.0.0",
        "seal_status": "CERTIFIED_CANONICAL_AUDIT_SEAL",
        "experiment_id": "known-answer-only",
        "manifest_sha256": "acf4f5383ad2387e6a21006aae83ba728c7ccb15c9114052e48babfd00e6081e",
        "protocol_version": "experiment-protocol-v1",
        "created_at_utc": "2026-10-02T10:00:00Z",
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
        "*Table 3b: Paired Scorable Representation Concordance and Exploratory McNemar Test.*"
        in content
    )
    assert "*Table 5b: Whole-Study Financial Ledger and Budget Reconciliation.*" in content

    # 5. Zero unpopulated execution placeholders
    assert "[TBD_AT_EXECUTION]" not in content
    assert "[PENDING" not in content

    # 6. Supplementary provenance table
    assert "#### Supplementary Execution Provenance (Canonical Run Mode)" in content
    assert "canonical_run_seal_v1.json" in content

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
    assert t5b["canonical_conditions_total_usd"] == "8.50"


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
    del seal["manifest_sha256"]
    seal_path.write_text(json.dumps(seal), encoding="utf-8")
    out_md = tmp_path / "out.md"

    with pytest.raises(
        KeyError, match=r"\[FAIL_CLOSED\] .* missing required key: 'manifest_sha256'"
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
    seal["manifest_sha256"] = "deadbeef" * 8
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
    del rq["rq3"]["whole_study_accounting"]
    rq_file.write_text(json.dumps(rq), encoding="utf-8")
    out_md = tmp_path / "out.md"

    with pytest.raises(KeyError, match=r"rq3\.whole_study_accounting"):
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

    from scripts.populate_report import compute_file_sha256

    output_digests = {
        fname: compute_file_sha256(bundle_dir / fname) for fname in REQUIRED_CANONICAL_FILES
    }
    seal_hash = compute_file_sha256(seal_path)

    prov_doc = json.loads((bundle_dir / "run_provenance.json").read_text(encoding="utf-8"))
    prov_git_sha = prov_doc.get("git_commit_sha", "1111111111111111111111111111111111111111")

    metric_bundle_data = {
        "schema_version": "1.0.0",
        "bundle_type": "canonical-metric-bundle-v1",
        "fixture_only": False,
        "execution_mode": "live",
        "dataset_split": "test",
        "experiment_id": "known-answer-only",
        "run_id": "live-66b94b1676bf46a9",
        "manifest_file_sha256": "acf4f5383ad2387e6a21006aae83ba728c7ccb15c9114052e48babfd00e6081e",
        "protocol_version": "experiment-protocol-v1",
        "protocol_sha256": "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c",
        "protocol_file_sha256": "a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb",
        "execution_git_sha": prov_git_sha,
        "evaluation_git_sha": prov_git_sha,
        "terminal_seal": {
            "path": str(seal_path),
            "sha256": seal_hash,
        },
        "output_file_digests": output_digests,
        "root_verification": {
            "path": "reports/evidence/root_canonical_export_validation_v2.json",
            "sha256": "abcdef" * 10 + "1234",
            "scope": "ROOT_APPROVED_CANONICAL_NUMERICAL_RESULTS",
        },
    }

    bundle_path = tmp_path / "canonical_metric_bundle_v1.json"
    bundle_path.write_text(json.dumps(metric_bundle_data, indent=2), encoding="utf-8")

    run_pipeline(
        data_dir=bundle_dir,
        metric_bundle=bundle_path,
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
    from scripts.populate_report import compute_file_sha256

    output_digests = {
        fname: compute_file_sha256(bundle_dir / fname) for fname in REQUIRED_CANONICAL_FILES
    }
    output_digests["per_condition_metrics.json"] = "deadbeef" * 8
    seal_hash = compute_file_sha256(seal_path)

    metric_bundle_data = {
        "schema_version": "1.0.0",
        "bundle_type": "canonical-metric-bundle-v1",
        "fixture_only": False,
        "execution_mode": "live",
        "experiment_id": "known-answer-only",
        "protocol_version": "experiment-protocol-v1",
        "terminal_seal": {
            "path": str(seal_path),
            "sha256": seal_hash,
        },
        "output_file_digests": output_digests,
    }
    bundle_path = tmp_path / "corrupted_bundle.json"
    bundle_path.write_text(json.dumps(metric_bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(
        ValueError,
        match=r"\[FAIL_CLOSED\] Output file digest mismatch for per_condition_metrics\.json",
    ):
        run_pipeline(
            data_dir=bundle_dir,
            metric_bundle=bundle_path,
            output_path=tmp_path / "out.md",
            mode="canonical",
        )


def test_canonical_metric_bundle_rejects_terminal_seal_hash_mismatch(
    canonical_bundle: tuple[Path, Path], tmp_path: Path
) -> None:
    """Metric Bundle Gate: Terminal seal hash mismatch raises ValueError."""
    bundle_dir, seal_path = canonical_bundle

    metric_bundle_data = {
        "schema_version": "1.0.0",
        "bundle_type": "canonical-metric-bundle-v1",
        "fixture_only": False,
        "execution_mode": "live",
        "experiment_id": "known-answer-only",
        "protocol_version": "experiment-protocol-v1",
        "terminal_seal": {
            "path": str(seal_path),
            "sha256": "badsealhash" * 5 + "1234",
        },
    }
    bundle_path = tmp_path / "bad_seal_bundle.json"
    bundle_path.write_text(json.dumps(metric_bundle_data, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match=r"\[FAIL_CLOSED\] Terminal seal hash mismatch"):
        run_pipeline(
            data_dir=bundle_dir,
            metric_bundle=bundle_path,
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
