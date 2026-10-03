"""Regression and fail-closed test suite for R9 reproduction report."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_reproduction_report import (
    generate_reproduction_report,
    main,
)

REAL_BUNDLE = REPO_ROOT / ".tmp/unpacked_v4/base_public_v3"
REAL_CANDIDATE_ZIP = REPO_ROOT / ".tmp/downloaded_candidate/public_v4_candidate_20261003.zip"
REAL_BUNDLE_V2 = REPO_ROOT / "artifacts/results/canonical_metric_bundle_v2.json"
REAL_REPLAY_OUT = REPO_ROOT / ".tmp/r9_replay_output"


def test_missing_candidate_zip_fails(tmp_path: Path):
    """Ensure missing candidate zip fails closed with exit code 1."""
    missing_zip = tmp_path / "nonexistent_candidate.zip"
    out_report = tmp_path / "missing_zip_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=REAL_REPLAY_OUT,
        candidate_zip=missing_zip,
        bundle_v2=REAL_BUNDLE_V2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_MISSING_CANDIDATE_ZIP"
    assert report["defects_count"] > 0
    assert report["candidate_package_zip"]["status"] == "FAIL_MISSING_CANDIDATE_ZIP"
    assert any("FAIL_MISSING_CANDIDATE_ZIP" in d for d in report["defects"])
    assert out_report.exists()

    # Also test CLI invocation
    cli_code = main(
        [
            "--bundle-dir",
            str(REAL_BUNDLE),
            "--replay-out-dir",
            str(REAL_REPLAY_OUT),
            "--candidate-zip",
            str(missing_zip),
            "--bundle-v2",
            str(REAL_BUNDLE_V2),
            "--output-report",
            str(tmp_path / "cli_missing_zip.json"),
        ]
    )
    assert cli_code == 1


def test_invalid_zip_fails(tmp_path: Path):
    """Ensure corrupt/invalid zip file fails closed with exit code 1."""
    corrupt_zip = tmp_path / "corrupt_candidate.zip"
    corrupt_zip.write_bytes(b"NOT_A_VALID_ZIP_FILE_RANDOM_CORRUPT_BYTES_1234567890")
    out_report = tmp_path / "invalid_zip_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=REAL_REPLAY_OUT,
        candidate_zip=corrupt_zip,
        bundle_v2=REAL_BUNDLE_V2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_INVALID_ZIP"
    assert report["defects_count"] > 0
    assert report["candidate_package_zip"]["status"] == "FAIL_INVALID_ZIP"
    assert any("FAIL_INVALID_ZIP" in d for d in report["defects"])


def test_corrupt_bundle_hash_fails(tmp_path: Path):
    """Ensure bundle v2 hash mismatch fails closed with exit code 1 and sha_match=False."""
    corrupt_v2 = tmp_path / "canonical_metric_bundle_v2.json"
    corrupt_v2.write_text(json.dumps({"tampered_payload": True}), encoding="utf-8")
    out_report = tmp_path / "corrupt_bundle_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=REAL_REPLAY_OUT,
        candidate_zip=REAL_CANDIDATE_ZIP,
        bundle_v2=corrupt_v2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_BUNDLE_HASH_MISMATCH"
    assert report["canonical_metric_bundle_v2_binding"]["sha_match"] is False
    assert report["canonical_metric_bundle_v2_binding"]["status"] == "FAIL_BUNDLE_HASH_MISMATCH"
    assert report["defects_count"] > 0
    assert any("FAIL_BUNDLE_HASH_MISMATCH" in d for d in report["defects"])


def test_missing_replay_outputs_fails(tmp_path: Path):
    """Ensure missing replay outputs fails closed with exit code 1."""
    empty_replay_out = tmp_path / "empty_replay_output"
    empty_replay_out.mkdir()
    out_report = tmp_path / "missing_replay_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=empty_replay_out,
        candidate_zip=REAL_CANDIDATE_ZIP,
        bundle_v2=REAL_BUNDLE_V2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_MISSING_REPLAY_OUTPUTS"
    assert report["defects_count"] > 0
    assert any("FAIL_MISSING_REPLAY_OUTPUTS" in d for d in report["defects"])


def test_comparator_mismatch_fails(tmp_path: Path):
    """Ensure comparator detects metric mismatch, sets status MISMATCH, and fails with exit 1."""
    tampered_replay = tmp_path / "tampered_replay_output"
    shutil.copytree(REAL_REPLAY_OUT, tampered_replay)

    overall_metrics_path = tampered_replay / "regenerated_native_6/overall_metrics.json"
    metrics_data = json.loads(overall_metrics_path.read_text(encoding="utf-8"))

    # Tamper with an existing metric field
    if "macro_accuracy" in metrics_data:
        metrics_data["macro_accuracy"] = 0.999999999999
    elif "accuracy" in metrics_data:
        metrics_data["accuracy"] = 0.999999999999
    else:
        first_key = next(iter(metrics_data.keys()))
        if isinstance(metrics_data[first_key], (int, float)):
            metrics_data[first_key] = 999.0
        elif isinstance(metrics_data[first_key], dict):
            metrics_data[first_key]["tampered_score"] = 999.0

    overall_metrics_path.write_text(json.dumps(metrics_data, indent=2), encoding="utf-8")

    out_report = tmp_path / "mismatch_report.json"
    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=tampered_replay,
        candidate_zip=REAL_CANDIDATE_ZIP,
        bundle_v2=REAL_BUNDLE_V2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_REPLAY_METRIC_MISMATCH"
    assert (
        report["regenerated_evaluation_deep_comparison"]["overall_metrics"]["status"] == "MISMATCH"
    )
    assert report["defects_count"] > 0
    assert any("FAIL_REPLAY_METRIC_MISMATCH" in d for d in report["defects"])


def test_positive_control_on_valid_fixtures(tmp_path: Path):
    """Positive control: valid candidate zip, bundle, and replay outputs pass cleanly with exit 0."""
    out_report = tmp_path / "positive_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=REAL_BUNDLE,
        replay_out_dir=REAL_REPLAY_OUT,
        candidate_zip=REAL_CANDIDATE_ZIP,
        bundle_v2=REAL_BUNDLE_V2,
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 0
    assert report["verdict"] == "PASS_CANONICAL_OFFLINE_VERIFIED"
    assert report["defects_count"] == 0
    assert len(report["defects"]) == 0
    assert out_report.exists()

    # Verify report contents
    saved_report = json.loads(out_report.read_text(encoding="utf-8"))
    assert saved_report["schema_version"] == "r9_saved_data_reproduction_report_v1"
    assert saved_report["candidate_package_zip"]["status"] == "PASS"
    assert saved_report["candidate_package_zip"]["sha_match"] is True
    assert saved_report["base_descriptor"]["status"] == "PASS_AUTHENTICATED"
    assert saved_report["input_files_audit"]["status"] == "PASS"
    assert saved_report["input_files_audit"]["total_files"] == 10
    assert saved_report["output_files_audit"]["status"] == "PASS"
    assert saved_report["output_files_audit"]["total_files"] == 8
    assert saved_report["sanitized_provenance_audit"]["status"] == "PASS"
    assert saved_report["sanitized_provenance_audit"]["total_assets"] == 4
    assert saved_report["runtime_wrapper_audit"]["status"] == "PASS"
    assert saved_report["financial_reconciliation"]["status"] == "PASS_EXACT_RECONCILIATION"
    assert saved_report["financial_reconciliation"]["completed_records"] == 6400
    assert saved_report["financial_reconciliation"]["provider_attempts"] == 6401
    assert saved_report["financial_reconciliation"]["detected_retries"] == 1
    assert saved_report["canonical_metric_bundle_v2_binding"]["sha_match"] is True

    # Verify deep comparison dynamic field counts
    deep_comp = saved_report["regenerated_evaluation_deep_comparison"]
    assert deep_comp["overall_metrics"]["status"] == "MATCH"
    assert deep_comp["overall_metrics"]["field_count"] == 120
    assert deep_comp["per_condition_metrics"]["status"] == "MATCH"
    assert deep_comp["per_condition_metrics"]["field_count"] == 276
    assert deep_comp["per_technique_metrics"]["status"] == "MATCH"
    assert deep_comp["per_technique_metrics"]["field_count"] == 35566
    assert deep_comp["retrieval_conditional_metrics"]["status"] == "MATCH"
    assert deep_comp["retrieval_conditional_metrics"]["field_count"] == 81
    assert deep_comp["failure_decomposition"]["status"] == "MATCH"
    assert deep_comp["failure_decomposition"]["field_count"] == 147
    assert deep_comp["run_provenance"]["status"] == "MATCH"
    assert deep_comp["run_provenance"]["field_count"] == 142
    assert deep_comp["rq_analysis"]["status"] == "MATCH"
    assert deep_comp["rq_analysis"]["scientific_fields_status"] == "MATCH"
    assert deep_comp["rq_analysis"]["field_count"] == 2000
