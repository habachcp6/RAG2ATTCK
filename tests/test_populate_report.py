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
    DEFAULT_TEMPLATE_PATH,
    DISCLAIMER_TEXT,
    REQUIRED_FIXTURE_FILES,
    assert_fixture_safety,
    format_int,
    format_latency,
    format_pct,
    format_pp,
    format_usd,
    run_pipeline,
    validate_finite_number,
)


@pytest.fixture
def real_fixture_copy(tmp_path: Path) -> Path:
    """Create an isolated temporary copy of the authoritative reproduction fixtures."""
    dest = tmp_path / "fixture_diagnostics"
    dest.mkdir(parents=True)
    for fname in REQUIRED_FIXTURE_FILES:
        src = DEFAULT_FIXTURE_DIR / fname
        if not src.is_file():
            pytest.skip(f"Authoritative fixture file missing: {src}")
        shutil.copy2(src, dest / fname)
    return dest


# ==============================================================================
# 1. Mode Gate & Safety Boundary Tests
# ==============================================================================


def test_canonical_mode_disabled(tmp_path: Path) -> None:
    """Safety gate: Canonical mode is disabled pending root S2 terminal audit seal."""
    out_md = tmp_path / "out.md"
    with pytest.raises(
        RuntimeError,
        match=r"\[FAIL_CLOSED\] Canonical mode is disabled pending root S2 terminal audit seal\.",
    ):
        run_pipeline(
            fixture_dir=DEFAULT_FIXTURE_DIR,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=out_md,
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
