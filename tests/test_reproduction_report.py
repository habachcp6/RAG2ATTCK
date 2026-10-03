"""Regression and fail-closed test suite for R9 reproduction report.

Fully decoupled and hermetic: all tests run without dependency on local .tmp/ staging
or external candidate packages by using minimal synthetic test fixtures.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any
import zipfile

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import scripts.generate_reproduction_report as grr
from scripts.generate_reproduction_report import (
    compute_sha256,
    generate_reproduction_report,
    main,
)
from scripts.reproduce_canonical_study import (
    REQUIRED_INPUT_FILES,
    REQUIRED_OUTPUT_FILES,
)


@pytest.fixture
def synthetic_fixtures(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Provide hermetic synthetic fixtures for reproduction report validation."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir(parents=True, exist_ok=True)

    # 1. Candidate zip package
    cand_zip = fixture_dir / "candidate_synthetic.zip"
    with zipfile.ZipFile(cand_zip, "w") as zf:
        zf.writestr("package_manifest_v4.json", json.dumps({"package": "v4_synthetic"}))
        zf.writestr("README.md", "# Synthetic Package\n")
    cand_zip_sha = compute_sha256(cand_zip)

    # 2. Canonical metric bundle v2
    bundle_v2 = fixture_dir / "canonical_metric_bundle_v2.json"
    bundle_v2.write_text(
        json.dumps(
            {
                "schema_version": "canonical_metric_bundle_v2",
                "candidate_base_git_sha": "c309e497c104cac10f43317c2bd6b8872fa6443a",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    bundle_v2_sha = compute_sha256(bundle_v2)

    # 3. Canonical bundle directory
    bundle_dir = fixture_dir / "canonical_bundle"
    for subdir in ("inputs", "outputs", "provenance", "runtime"):
        (bundle_dir / subdir).mkdir(parents=True, exist_ok=True)

    # 3a. Runtime recovery wrapper
    raw_block = "\ndef recover():\n    return True\n"
    wrapper_code = f'RAW_WRAPPER_BLOCK = """{raw_block}"""\n'
    wrapper_path = bundle_dir / "runtime/runtime_recovery_wrapper.py"
    wrapper_path.write_text(wrapper_code, encoding="utf-8")
    wrapper_sha = compute_sha256(wrapper_path)
    raw_block_sha = hashlib.sha256(raw_block.encode("utf-8")).hexdigest()

    # 3b. Provenance assets
    prov_spec: dict[str, str] = {}
    for prov_rel in (
        "provenance/s2_evaluation_execute_public.md",
        "provenance/root_canonical_export_validation_public.json",
        "provenance/terminal_process_proof_public.json",
        "provenance/terminal_original_bytes_inventory_public.json",
    ):
        p = bundle_dir / prov_rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"synthetic provenance asset: {prov_rel}\n", encoding="utf-8")
        prov_spec[prov_rel] = compute_sha256(p)

    # 3c. Financial ledger files
    (bundle_dir / "inputs/.study_anchor.json").write_text(
        json.dumps(
            {
                "total_budget_usd": "20.00000000",
                "prior_pilot_provisional_hold_usd": "1.00000000",
                "initial_available_usd": "19.00000000",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    (bundle_dir / "inputs/run_summary.json").write_text(
        json.dumps(
            {
                "study_budget": {
                    "cumulative_settled_cost_usd": "5.00000000",
                    "uncommitted_available_balance_usd": "14.00000000",
                }
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # 6400 settlements, 6400 reserves, 6401 attempts (strictly 1 retry on ('view_d870d574', 'rag_k1'))
    journal_lines = [
        json.dumps({"event": "attempt_receipt", "key": ["view_d870d574", "rag_k1"]}),
        json.dumps({"event": "attempt_receipt", "key": ["view_d870d574", "rag_k1"]}),
    ]
    for i in range(1, 6400):
        journal_lines.append(json.dumps({"event": "attempt_receipt", "key": [f"view_{i:04d}", "rag_k1"]}))
    for _ in range(6400):
        journal_lines.append(json.dumps({"event": "monetary_reserve"}))
        journal_lines.append(json.dumps({"event": "monetary_settle"}))
    (bundle_dir / "inputs/request_journal.jsonl").write_text(
        "\n".join(journal_lines) + "\n", encoding="utf-8"
    )

    # 3d. Remaining required input files
    for in_name in REQUIRED_INPUT_FILES:
        p = bundle_dir / "inputs" / in_name
        if not p.is_file():
            p.write_text(json.dumps({"synthetic_input": in_name}), encoding="utf-8")

    # 3e. Required output files
    native_mock: dict[str, Any] = {
        "macro_accuracy": 0.85,
        "accuracy": 0.85,
        "records_count": 6400,
        "status": "VALID",
    }
    for out_name in REQUIRED_OUTPUT_FILES:
        p = bundle_dir / "outputs" / out_name
        if out_name == "rq_analysis.json":
            p.write_text(
                json.dumps(
                    {
                        "rq1": {"accuracy": 0.85, "macro_f1": 0.80},
                        "rq2": {"hit_rate": 0.90},
                        "rq3": {"cost_usd": "5.00000000"},
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        elif out_name == "rq_analysis_summary.md":
            p.write_text("# Synthetic RQ Analysis Summary\n", encoding="utf-8")
        else:
            p.write_text(json.dumps(native_mock, indent=2), encoding="utf-8")

    # 3f. Canonical bundle manifest
    input_digests = {
        fname: compute_sha256(bundle_dir / "inputs" / fname)
        for fname in sorted(REQUIRED_INPUT_FILES)
    }
    output_digests = {
        fname: compute_sha256(bundle_dir / "outputs" / fname)
        for fname in sorted(REQUIRED_OUTPUT_FILES)
    }
    manifest_obj = {
        "source_file_digests": input_digests,
        "output_file_digests": output_digests,
        "derived_from": {"bundle_sha256": "00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f"},
    }
    manifest_path = bundle_dir / "canonical_bundle_manifest.json"
    manifest_path.write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
    manifest_sha = compute_sha256(manifest_path)

    # 4. Replay evaluation directory
    replay_out = fixture_dir / "replay_output"
    (replay_out / "regenerated_native_6").mkdir(parents=True, exist_ok=True)
    (replay_out / "regenerated_rq").mkdir(parents=True, exist_ok=True)

    for fname in grr.NATIVE_METRIC_FILES:
        (replay_out / "regenerated_native_6" / fname).write_text(
            json.dumps(native_mock, indent=2), encoding="utf-8"
        )
    (replay_out / "regenerated_rq/rq_analysis.json").write_text(
        (bundle_dir / "outputs/rq_analysis.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    # Monkeypatch expected constants in generate_reproduction_report module
    monkeypatch.setattr(grr, "EXPECTED_CANDIDATE_ZIP_SHA256", cand_zip_sha)
    monkeypatch.setattr(grr, "EXPECTED_BUNDLE_V2_SHA256", bundle_v2_sha)
    monkeypatch.setattr(grr, "EXPECTED_PUBLIC_MANIFEST_SHA256", manifest_sha)
    monkeypatch.setattr(
        grr,
        "CANONICAL_BUNDLE_SHA256",
        "00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f",
    )
    monkeypatch.setattr(grr, "APPROVED_PUBLIC_PROVENANCE_SPEC", prov_spec)
    monkeypatch.setattr(grr, "EXPECTED_RUNTIME_WRAPPER_SHA256", wrapper_sha)
    monkeypatch.setattr(grr, "CANONICAL_WRAPPER_BLOCK_SHA256", raw_block_sha)

    return {
        "bundle_dir": bundle_dir,
        "replay_out_dir": replay_out,
        "candidate_zip": cand_zip,
        "bundle_v2": bundle_v2,
    }


def test_missing_candidate_zip_fails(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Ensure missing candidate zip fails closed with exit code 1."""
    missing_zip = tmp_path / "nonexistent_candidate.zip"
    out_report = tmp_path / "missing_zip_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=synthetic_fixtures["replay_out_dir"],
        candidate_zip=missing_zip,
        bundle_v2=synthetic_fixtures["bundle_v2"],
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
            str(synthetic_fixtures["bundle_dir"]),
            "--replay-out-dir",
            str(synthetic_fixtures["replay_out_dir"]),
            "--candidate-zip",
            str(missing_zip),
            "--bundle-v2",
            str(synthetic_fixtures["bundle_v2"]),
            "--output-report",
            str(tmp_path / "cli_missing_zip.json"),
        ]
    )
    assert cli_code == 1


def test_invalid_zip_fails(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Ensure corrupt/invalid zip file fails closed with exit code 1."""
    corrupt_zip = tmp_path / "corrupt_candidate.zip"
    corrupt_zip.write_bytes(b"NOT_A_VALID_ZIP_FILE_RANDOM_CORRUPT_BYTES_1234567890")
    out_report = tmp_path / "invalid_zip_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=synthetic_fixtures["replay_out_dir"],
        candidate_zip=corrupt_zip,
        bundle_v2=synthetic_fixtures["bundle_v2"],
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_INVALID_ZIP"
    assert report["defects_count"] > 0
    assert report["candidate_package_zip"]["status"] == "FAIL_INVALID_ZIP"
    assert any("FAIL_INVALID_ZIP" in d for d in report["defects"])


def test_corrupt_bundle_hash_fails(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Ensure bundle v2 hash mismatch fails closed with exit code 1 and sha_match=False."""
    corrupt_v2 = tmp_path / "canonical_metric_bundle_v2.json"
    corrupt_v2.write_text(json.dumps({"tampered_payload": True}), encoding="utf-8")
    out_report = tmp_path / "corrupt_bundle_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=synthetic_fixtures["replay_out_dir"],
        candidate_zip=synthetic_fixtures["candidate_zip"],
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


def test_missing_replay_outputs_fails(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Ensure missing replay outputs fails closed with exit code 1."""
    empty_replay_out = tmp_path / "empty_replay_output"
    empty_replay_out.mkdir()
    out_report = tmp_path / "missing_replay_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=empty_replay_out,
        candidate_zip=synthetic_fixtures["candidate_zip"],
        bundle_v2=synthetic_fixtures["bundle_v2"],
        output_report=out_report,
        strict=True,
    )

    assert exit_code == 1
    assert report["verdict"].startswith("FAIL")
    assert report["verdict"] == "FAIL_MISSING_REPLAY_OUTPUTS"
    assert report["defects_count"] > 0
    assert any("FAIL_MISSING_REPLAY_OUTPUTS" in d for d in report["defects"])


def test_comparator_mismatch_fails(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Ensure comparator detects metric mismatch, sets status MISMATCH, and fails with exit 1."""
    tampered_replay = tmp_path / "tampered_replay_output"
    shutil.copytree(synthetic_fixtures["replay_out_dir"], tampered_replay)

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
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=tampered_replay,
        candidate_zip=synthetic_fixtures["candidate_zip"],
        bundle_v2=synthetic_fixtures["bundle_v2"],
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


def test_positive_control_on_valid_fixtures(tmp_path: Path, synthetic_fixtures: dict[str, Any]):
    """Positive control: valid candidate zip, bundle, and replay outputs pass cleanly with exit 0."""
    out_report = tmp_path / "positive_report.json"

    report, exit_code = generate_reproduction_report(
        bundle_dir=synthetic_fixtures["bundle_dir"],
        replay_out_dir=synthetic_fixtures["replay_out_dir"],
        candidate_zip=synthetic_fixtures["candidate_zip"],
        bundle_v2=synthetic_fixtures["bundle_v2"],
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

    # Verify deep comparison dynamic field statuses
    deep_comp = saved_report["regenerated_evaluation_deep_comparison"]
    assert deep_comp["overall_metrics"]["status"] == "MATCH"
    assert deep_comp["overall_metrics"]["field_count"] > 0
    assert deep_comp["per_condition_metrics"]["status"] == "MATCH"
    assert deep_comp["per_condition_metrics"]["field_count"] > 0
    assert deep_comp["per_technique_metrics"]["status"] == "MATCH"
    assert deep_comp["per_technique_metrics"]["field_count"] > 0
    assert deep_comp["retrieval_conditional_metrics"]["status"] == "MATCH"
    assert deep_comp["retrieval_conditional_metrics"]["field_count"] > 0
    assert deep_comp["failure_decomposition"]["status"] == "MATCH"
    assert deep_comp["failure_decomposition"]["field_count"] > 0
    assert deep_comp["run_provenance"]["status"] == "MATCH"
    assert deep_comp["run_provenance"]["field_count"] > 0
    assert deep_comp["rq_analysis"]["status"] == "MATCH"
    assert deep_comp["rq_analysis"]["scientific_fields_status"] == "MATCH"
    assert deep_comp["rq_analysis"]["field_count"] > 0
