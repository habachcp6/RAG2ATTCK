#!/usr/bin/env python3
"""scripts/run_sg_evidence_audit_probes.py

Independent Adversarial Probes & Security/Evidence Audit Runner (SG-EVIDENCE-AUDIT).
Executes exhaustive adversarial verification against R9 reproduction & inventory scripts,
runs required test suites, and audits all evidence files for zero leaks.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.generate_reproduction_report import (
    EXPECTED_BUNDLE_V2_SHA256,
    EXPECTED_CANDIDATE_ZIP_SHA256,
    generate_reproduction_report,
)
from scripts.generate_r9_artifact_inventory import (
    generate_inventory,
)


def print_step(title: str):
    print("\n" + "=" * 80)
    print(f"[*] {title}")
    print("=" * 80)


def audit_section_1_reproduction_report() -> Dict[str, Any]:
    print_step("SECTION 1: Independent Adversarial Probes on generate_reproduction_report.py")
    results = {}

    real_bundle = REPO_ROOT / ".tmp/unpacked_v4/base_public_v3"
    real_candidate_zip = REPO_ROOT / ".tmp/downloaded_candidate/public_v4_candidate_20261003.zip"
    real_bundle_v2 = REPO_ROOT / "artifacts/results/canonical_metric_bundle_v2.json"
    real_replay_out = REPO_ROOT / ".tmp/r9_replay_output"

    # 1. Empty temporary directory (missing ZIP, missing outputs)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        empty_bundle = tmp_path / "empty_bundle"
        empty_bundle.mkdir()
        missing_zip = tmp_path / "missing_candidate.zip"
        empty_replay_out = tmp_path / "empty_replay_out"
        empty_replay_out.mkdir()
        missing_v2 = tmp_path / "missing_bundle_v2.json"

        report_empty, exit_empty = generate_reproduction_report(
            bundle_dir=empty_bundle,
            replay_out_dir=empty_replay_out,
            candidate_zip=missing_zip,
            bundle_v2=missing_v2,
            output_report=tmp_path / "out_empty.json",
            strict=True,
        )

        assert exit_empty == 1, f"Expected exit 1 on empty dir, got {exit_empty}"
        assert not report_empty["verdict"].startswith("PASS"), f"Verdict should not be PASS: {report_empty['verdict']}"
        assert report_empty["defects_count"] > 0, "Defects count must be > 0"
        print(f"  [PASS] Probe 1.1 (Empty temp dir): exit={exit_empty}, verdict={report_empty['verdict']}, defects={report_empty['defects_count']}")
        results["probe_1_1_empty_dir"] = {
            "passed": True,
            "exit_code": exit_empty,
            "verdict": report_empty["verdict"],
            "defects_count": report_empty["defects_count"],
        }

    # 2. Tampered bundle_v2 hash (single character change or tampered file)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tampered_v2 = tmp_path / "tampered_bundle_v2.json"
        v2_content = json.loads(real_bundle_v2.read_text(encoding="utf-8"))
        # Tamper payload
        v2_content["adversarial_probe_tamper"] = "hostile_modification"
        tampered_v2.write_text(json.dumps(v2_content, indent=2), encoding="utf-8")

        report_v2, exit_v2 = generate_reproduction_report(
            bundle_dir=real_bundle,
            replay_out_dir=real_replay_out,
            candidate_zip=real_candidate_zip,
            bundle_v2=tampered_v2,
            output_report=tmp_path / "out_v2.json",
            strict=True,
        )

        assert exit_v2 == 1, f"Expected exit 1 on tampered bundle v2, got {exit_v2}"
        assert report_v2["canonical_metric_bundle_v2_binding"]["sha_match"] is False, "sha_match must be False"
        assert report_v2["verdict"] == "FAIL_BUNDLE_HASH_MISMATCH", f"Expected FAIL_BUNDLE_HASH_MISMATCH, got {report_v2['verdict']}"
        print(f"  [PASS] Probe 1.2 (Tampered bundle_v2 hash): exit={exit_v2}, sha_match={report_v2['canonical_metric_bundle_v2_binding']['sha_match']}, verdict={report_v2['verdict']}")
        results["probe_1_2_bundle_v2_mismatch"] = {
            "passed": True,
            "exit_code": exit_v2,
            "sha_match": report_v2["canonical_metric_bundle_v2_binding"]["sha_match"],
            "verdict": report_v2["verdict"],
        }

    # 3. Output file with metric discrepancy
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        tampered_replay = tmp_path / "tampered_replay_output"
        shutil.copytree(real_replay_out, tampered_replay)

        overall_metrics_path = tampered_replay / "regenerated_native_6/overall_metrics.json"
        metrics_data = json.loads(overall_metrics_path.read_text(encoding="utf-8"))
        metrics_data["macro_accuracy"] = 0.999999999999
        overall_metrics_path.write_text(json.dumps(metrics_data, indent=2), encoding="utf-8")

        report_disc, exit_disc = generate_reproduction_report(
            bundle_dir=real_bundle,
            replay_out_dir=tampered_replay,
            candidate_zip=real_candidate_zip,
            bundle_v2=real_bundle_v2,
            output_report=tmp_path / "out_disc.json",
            strict=True,
        )

        assert exit_disc == 1, f"Expected exit 1 on metric discrepancy, got {exit_disc}"
        assert report_disc["regenerated_evaluation_deep_comparison"]["overall_metrics"]["status"] == "MISMATCH", "status must be MISMATCH"
        assert report_disc["verdict"] == "FAIL_REPLAY_METRIC_MISMATCH", f"Expected FAIL_REPLAY_METRIC_MISMATCH, got {report_disc['verdict']}"
        print(f"  [PASS] Probe 1.3 (Metric discrepancy): exit={exit_disc}, overall_metrics status={report_disc['regenerated_evaluation_deep_comparison']['overall_metrics']['status']}, verdict={report_disc['verdict']}")
        results["probe_1_3_metric_discrepancy"] = {
            "passed": True,
            "exit_code": exit_disc,
            "metric_status": report_disc["regenerated_evaluation_deep_comparison"]["overall_metrics"]["status"],
            "verdict": report_disc["verdict"],
        }

    # 4. Positive control on genuine canonical data
    report_real, exit_real = generate_reproduction_report(
        bundle_dir=real_bundle,
        replay_out_dir=real_replay_out,
        candidate_zip=real_candidate_zip,
        bundle_v2=real_bundle_v2,
        strict=True,
    )

    assert exit_real == 0, f"Expected exit 0 on genuine data, got {exit_real}"
    assert report_real["verdict"] == "PASS_CANONICAL_OFFLINE_VERIFIED", f"Expected PASS_CANONICAL_OFFLINE_VERIFIED, got {report_real['verdict']}"
    assert report_real["defects_count"] == 0, f"Defects count must be 0, got {report_real['defects_count']}"
    print(f"  [PASS] Probe 1.4 (Real genuine data): exit={exit_real}, verdict={report_real['verdict']}, defects_count={report_real['defects_count']}")
    results["probe_1_4_real_data"] = {
        "passed": True,
        "exit_code": exit_real,
        "verdict": report_real["verdict"],
        "defects_count": report_real["defects_count"],
    }

    return results


def audit_section_2_artifact_inventory() -> Dict[str, Any]:
    print_step("SECTION 2: Independent Adversarial Probes on generate_r9_artifact_inventory.py")
    results = {}

    from tests.test_artifact_inventory import REQUIRED_ARTIFACT_REL_PATHS, setup_mock_repo

    # 1. Empty temporary directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        inv_empty, code_empty = generate_inventory(repo_root=tmp_path)

        assert code_empty == 1, f"Expected exit 1 on empty dir, got {code_empty}"
        assert inv_empty["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS", f"Expected FAIL_MISSING_REQUIRED_ARTIFACTS, got {inv_empty['verdict']}"
        print(f"  [PASS] Probe 2.1 (Empty temp dir): exit={code_empty}, verdict={inv_empty['verdict']}")
        results["probe_2_1_empty_dir"] = {
            "passed": True,
            "exit_code": code_empty,
            "verdict": inv_empty["verdict"],
        }

    # 2. Missing PPTX or missing preview
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        setup_mock_repo(tmp_path, omit_paths=["docs/presentation/slides.pptx"])
        inv_no_pptx, code_no_pptx = generate_inventory(repo_root=tmp_path)

        assert code_no_pptx == 1, f"Expected exit 1 on missing PPTX, got {code_no_pptx}"
        assert inv_no_pptx["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
        assert "docs/presentation/slides.pptx" in inv_no_pptx["validation_summary"]["missing_required_artifacts"]
        print(f"  [PASS] Probe 2.2a (Missing PPTX): exit={code_no_pptx}, verdict={inv_no_pptx['verdict']}")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        setup_mock_repo(tmp_path, omit_paths=["reports/evidence/qa/fixture_slides/slide-6.png"])
        inv_no_prev, code_no_prev = generate_inventory(repo_root=tmp_path)

        assert code_no_prev == 1, f"Expected exit 1 on missing preview, got {code_no_prev}"
        assert inv_no_prev["verdict"] == "FAIL_MISSING_REQUIRED_ARTIFACTS"
        assert "reports/evidence/qa/fixture_slides/slide-6.png" in inv_no_prev["validation_summary"]["missing_required_artifacts"]
        print(f"  [PASS] Probe 2.2b (Missing preview slide-6.png): exit={code_no_prev}, verdict={inv_no_prev['verdict']}")
        results["probe_2_2_missing_pptx_or_preview"] = {
            "passed": True,
            "missing_pptx_exit": code_no_pptx,
            "missing_preview_exit": code_no_prev,
        }

    # 3. QA record pointing to different PPTX hash
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        setup_mock_repo(tmp_path)
        qa_file = tmp_path / "reports/evidence/qa/visual_qa_inspection_record.json"
        data_qa = json.loads(qa_file.read_text(encoding="utf-8"))
        data_qa["scope"]["pptx_target"]["sha256"] = "deadbeef" * 8
        qa_file.write_text(json.dumps(data_qa, indent=2), encoding="utf-8")

        inv_bad_hash, code_bad_hash = generate_inventory(repo_root=tmp_path)
        assert code_bad_hash == 1, f"Expected exit 1 on QA record hash mismatch, got {code_bad_hash}"
        assert inv_bad_hash["verdict"] == "FAIL_QA_VERIFICATION_MISMATCH", f"Expected FAIL_QA_VERIFICATION_MISMATCH, got {inv_bad_hash['verdict']}"
        print(f"  [PASS] Probe 2.3 (QA record points to different PPTX hash): exit={code_bad_hash}, verdict={inv_bad_hash['verdict']}")
        results["probe_2_3_qa_hash_mismatch"] = {
            "passed": True,
            "exit_code": code_bad_hash,
            "verdict": inv_bad_hash["verdict"],
        }

    # 4. Real genuine data
    inv_real, code_real = generate_inventory(repo_root=REPO_ROOT)
    assert code_real == 0, f"Expected exit 0 on genuine repo, got {code_real}"
    assert inv_real["verdict"] == "PASS_ALL_ARTIFACTS_VERIFIED", f"Expected PASS_ALL_ARTIFACTS_VERIFIED, got {inv_real['verdict']}"

    deck = inv_real["presentation_and_defense_deck"]
    assert deck["total_slides"] == 12, f"Expected 12 slides, got {deck['total_slides']}"
    assert deck["speaker_notes_present_all_slides"] is True, "All 12 slides must have speaker notes"
    assert deck["pptx_dynamic_inspection"]["slide_count"] == 12
    assert deck["pptx_dynamic_inspection"]["notes_count"] == 12

    # Slide 6 and slide 9 sharpness in visual QA
    vqa_record_path = REPO_ROOT / "reports/evidence/qa/visual_qa_inspection_record.json"
    vqa_data = json.loads(vqa_record_path.read_text(encoding="utf-8"))
    s6_obs = vqa_data["detailed_observations"]["slide_6"]
    s9_obs = vqa_data["detailed_observations"]["slide_9"]
    assert s6_obs["visual_quality"] == "VERIFIED_SHARP", f"Slide 6 visual quality: {s6_obs['visual_quality']}"
    assert s9_obs["visual_quality"] == "VERIFIED_SHARP", f"Slide 9 visual quality: {s9_obs['visual_quality']}"

    print(f"  [PASS] Probe 2.4 (Real genuine data): exit={code_real}, verdict={inv_real['verdict']}")
    print(f"         12 slides all have notes: {deck['speaker_notes_present_all_slides']} (count={deck['pptx_dynamic_inspection']['notes_count']})")
    print(f"         Slide 6 quality: {s6_obs['visual_quality']}, Slide 9 quality: {s9_obs['visual_quality']}")

    results["probe_2_4_real_data"] = {
        "passed": True,
        "exit_code": code_real,
        "verdict": inv_real["verdict"],
        "total_slides": deck["total_slides"],
        "notes_count": deck["pptx_dynamic_inspection"]["notes_count"],
        "slide_6_quality": s6_obs["visual_quality"],
        "slide_9_quality": s9_obs["visual_quality"],
    }

    return results


def audit_section_3_pytest_suite() -> Dict[str, Any]:
    print_step("SECTION 3: Pytest Verification of Full Regression & Adversarial Suites")
    test_files = [
        "tests/test_reproduction_report.py",
        "tests/test_artifact_inventory.py",
        "tests/test_public_v4_package.py",
        "tests/test_sg_audit_adversarial_probes.py",
    ]
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *test_files,
        "-v",
        "--tb=short",
    ]
    print(f"Running command: {' '.join(cmd)}")
    start_time = time.time()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8")
    elapsed = time.time() - start_time

    print(proc.stdout)
    if proc.stderr:
        print("STDERR:", proc.stderr)

    assert proc.returncode == 0, f"Pytest failed with exit code {proc.returncode}"

    # Parse passed tests count from stdout
    match = re.search(r"(=+)\s+(\d+)\s+passed.*in\s+([\d\.]+)s", proc.stdout)
    passed_count = int(match.group(2)) if match else None
    duration_str = match.group(3) if match else f"{elapsed:.2f}"

    print(f"  [PASS] All Pytest tests passed: {passed_count} passed in {duration_str}s (elapsed: {elapsed:.2f}s)")
    return {
        "passed": True,
        "exit_code": proc.returncode,
        "passed_count": passed_count,
        "duration_seconds": elapsed,
        "stdout_summary": proc.stdout.splitlines()[-1] if proc.stdout else "",
    }


def audit_section_4_security_and_privacy() -> Dict[str, Any]:
    print_step("SECTION 4: Security & Privacy Leak Audit (Zero Workstation Paths, Zero Credentials)")
    target_files = [
        REPO_ROOT / "reports/evidence/r9_saved_data_reproduction_report.json",
        REPO_ROOT / "reports/evidence/r9_final_artifact_inventory.json",
        REPO_ROOT / "reports/evidence/qa/visual_qa_inspection_record.json",
        REPO_ROOT / "reports/evidence/r9_saved_data_reproduction_raw.log",
    ]

    # Regex patterns for leaks
    # 1. Private workstation path patterns: C:\Users\<name>, D:\<path>, /home/<user>, /Users/<user>
    # Note: canonical specs or standard repo rel paths are allowed
    workstation_path_patterns = [
        re.compile(r"[C-Zc-z]:\\Users\\[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
        re.compile(r"[C-Zc-z]:\\(?:rag2attck|workspace|projects|documents|desktop|downloads)\\[a-zA-Z0-9_\-\.\\]+", re.IGNORECASE),
        re.compile(r"/(?:home|Users)/[a-zA-Z0-9_\-\.]+", re.IGNORECASE),
        re.compile(r"hahoa", re.IGNORECASE),
        re.compile(r"DESKTOP-[A-Z0-9]+", re.IGNORECASE),
    ]

    # 2. Credential patterns: API keys, tokens, auth headers, private keys
    credential_patterns = [
        re.compile(r"AIza[0-9A-Za-z-_]{35}"),  # Google API Key
        re.compile(r"sk-[a-zA-Z0-9]{20,48}"),   # OpenAI API Key
        re.compile(r"ghp_[a-zA-Z0-9]{36}"),     # GitHub Token
        re.compile(r"AKIA[0-9A-Z]{16}"),        # AWS Access Key
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        re.compile(r"(?:Bearer\s+[a-zA-Z0-9_\-\.]{20,})"),
        re.compile(r"(?:api[_-]?key|secret|password|access[_-]?token)\s*[:=]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]", re.IGNORECASE),
    ]

    file_audit_results = {}
    total_violations = 0

    for path in target_files:
        assert path.is_file(), f"Target file does not exist: {path}"
        text = path.read_text(encoding="utf-8", errors="replace")
        rel_name = path.relative_to(REPO_ROOT).as_posix()
        violations = []

        # Check workstation paths
        for pat in workstation_path_patterns:
            matches = pat.findall(text)
            if matches:
                violations.extend([f"Workstation path pattern '{pat.pattern}' match: {m}" for m in matches[:5]])

        # Check credentials
        for pat in credential_patterns:
            matches = pat.findall(text)
            if matches:
                violations.extend([f"Credential pattern '{pat.pattern}' match: {m}" for m in matches[:5]])

        file_audit_results[rel_name] = {
            "size_bytes": path.stat().st_size,
            "violations": violations,
            "clean": len(violations) == 0,
        }
        if violations:
            total_violations += len(violations)
            print(f"  [FAIL] {rel_name} has {len(violations)} security/privacy violations:")
            for v in violations:
                print(f"         - {v}")
        else:
            print(f"  [PASS] {rel_name} (size: {path.stat().st_size} bytes): 0 violations detected.")

    assert total_violations == 0, f"Detected {total_violations} privacy/security violations!"
    return {
        "passed": True,
        "files_audited": len(target_files),
        "total_violations": total_violations,
        "file_details": file_audit_results,
    }


def main() -> int:
    print("=" * 80)
    print("STARTING INDEPENDENT SG-EVIDENCE-AUDIT ADVERSARIAL PROBES & VERIFICATION")
    print("=" * 80)

    summary_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo_root": str(REPO_ROOT),
    }

    try:
        summary_report["section_1_reproduction_report"] = audit_section_1_reproduction_report()
        summary_report["section_2_artifact_inventory"] = audit_section_2_artifact_inventory()
        summary_report["section_3_pytest_suite"] = audit_section_3_pytest_suite()
        summary_report["section_4_security_privacy"] = audit_section_4_security_and_privacy()

        summary_report["overall_verdict"] = "AUDIT_PASS_ALL_PROBES_VERIFIED"
        summary_report["auditor"] = "SG-EVIDENCE-AUDIT"

        out_log = REPO_ROOT / "reports/evidence/sg_evidence_audit_independent_probes_record.json"
        out_log.write_text(json.dumps(summary_report, indent=2), encoding="utf-8")
        print("\n" + "=" * 80)
        print(f"[OVERALL VERDICT] {summary_report['overall_verdict']}")
        print(f"Audit record saved to: {out_log}")
        print("=" * 80)
        return 0
    except Exception as exc:
        print(f"\n[FATAL AUDIT FAILURE] {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
