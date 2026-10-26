"""Generate comprehensive saved-data reproduction report for R9."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.reproduce_canonical_study import (
    APPROVED_PUBLIC_PROVENANCE_SPEC,
    CANONICAL_BUNDLE_SHA256,
    CANONICAL_WRAPPER_BLOCK_SHA256,
    EXPECTED_PUBLIC_MANIFEST_SHA256,
    REQUIRED_INPUT_FILES,
    REQUIRED_OUTPUT_FILES,
    compare_metrics_trees,
    count_fields,
)

EXPECTED_CANDIDATE_ZIP_SHA256 = "1d5f9f4bb2d50bbb885746fe4d26f34ca5af1cacdbcad7e0005c2af8ea1086c1"
EXPECTED_BUNDLE_V2_SHA256 = "442b5933858caafc9da3c06ee9398637213ed30d7a7db80195c0babb1195ef34"
EXPECTED_RUNTIME_WRAPPER_SHA256 = "6eabc4f0a2065780fab6e6bdf28711f7902e97d3738b3f200543a8d86939113f"

NATIVE_METRIC_FILES = [
    "overall_metrics.json",
    "per_condition_metrics.json",
    "per_technique_metrics.json",
    "retrieval_conditional_metrics.json",
    "failure_decomposition.json",
    "run_provenance.json",
]


def compute_sha256(path: Path) -> str:
    """Compute hex SHA-256 of file bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path) -> Any:
    """Load JSON file from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def find_bundle_file(bundle_dir: Path, rel_path: str) -> Path | None:
    """Locate file inside bundle directory respecting standard or flat layout."""
    direct = bundle_dir / rel_path
    if direct.is_file():
        return direct
    if "/" not in rel_path:
        for subdir in ("inputs", "outputs", "provenance", "runtime"):
            cand = bundle_dir / subdir / rel_path
            if cand.is_file():
                return cand
    return None


def generate_reproduction_report(
    bundle_dir: Path | str,
    replay_out_dir: Path | str,
    candidate_zip: Path | str,
    bundle_v2: Path | str,
    output_report: Path | str | None = None,
    strict: bool = True,
) -> tuple[dict[str, Any], int]:
    """Generate comprehensive reproduction report consuming actual replay outputs.

    Enforces fail-closed validation on all candidate packages, canonical descriptors,
    financial reconciliation logs, and metric tree comparisons.
    """
    repo_root = Path(__file__).resolve().parents[1]
    bundle_dir = Path(bundle_dir).resolve()
    replay_out_dir = Path(replay_out_dir).resolve()
    candidate_zip = Path(candidate_zip).resolve()
    bundle_v2 = Path(bundle_v2).resolve()

    defects: list[str] = []

    # 1. Candidate ZIP validation
    zip_sha = None
    zip_size = None
    zip_is_valid = False
    zip_status = "FAIL"

    if not candidate_zip.exists():
        zip_status = "FAIL_MISSING_CANDIDATE_ZIP"
        defects.append(
            f"FAIL_MISSING_CANDIDATE_ZIP: Candidate ZIP archive not found at {candidate_zip}"
        )
    elif not zipfile.is_zipfile(candidate_zip):
        zip_size = candidate_zip.stat().st_size
        zip_sha = compute_sha256(candidate_zip)
        zip_status = "FAIL_INVALID_ZIP"
        defects.append(
            f"FAIL_INVALID_ZIP: Candidate file {candidate_zip} is not a valid zip archive"
        )
    else:
        zip_size = candidate_zip.stat().st_size
        zip_sha = compute_sha256(candidate_zip)
        try:
            with zipfile.ZipFile(candidate_zip, "r") as zf:
                corrupt_entry = zf.testzip()
                if corrupt_entry is not None:
                    zip_status = "FAIL_INVALID_ZIP"
                    defects.append(
                        f"FAIL_INVALID_ZIP: Corrupt entry found in {candidate_zip}: {corrupt_entry}"
                    )
                else:
                    zip_is_valid = True
        except Exception as exc:
            zip_status = "FAIL_INVALID_ZIP"
            defects.append(f"FAIL_INVALID_ZIP: Error testing candidate zip {candidate_zip}: {exc}")

        if zip_is_valid:
            if zip_sha != EXPECTED_CANDIDATE_ZIP_SHA256:
                zip_status = "FAIL_ZIP_HASH_MISMATCH"
                defects.append(
                    f"FAIL_ZIP_HASH_MISMATCH: Candidate ZIP SHA mismatch (actual={zip_sha}, expected={EXPECTED_CANDIDATE_ZIP_SHA256})"
                )
            else:
                zip_status = "PASS"

    candidate_zip_section = {
        "path": candidate_zip.name,
        "sha256": zip_sha,
        "expected_sha256": EXPECTED_CANDIDATE_ZIP_SHA256,
        "sha_match": (zip_sha == EXPECTED_CANDIDATE_ZIP_SHA256),
        "size_bytes": zip_size,
        "is_valid_zip": zip_is_valid,
        "source_release_tag": "v4-candidate-package-r7",
        "source_release_url": "https://github.com/habachcp6/RAG2ATTCK/releases/tag/untagged-4ed2f6c54faf905aba18",
        "status": zip_status,
    }

    # 2. Canonical metric bundle v2 binding validation
    bundle_v2_sha = None
    bundle_v2_match = False
    candidate_base_git_sha = None
    bundle_v2_status = "FAIL"

    if not bundle_v2.exists():
        bundle_v2_status = "FAIL_BUNDLE_HASH_MISMATCH"
        defects.append(
            f"FAIL_BUNDLE_HASH_MISMATCH: canonical_metric_bundle_v2.json not found at {bundle_v2}"
        )
    else:
        bundle_v2_sha = compute_sha256(bundle_v2)
        bundle_v2_match = bundle_v2_sha == EXPECTED_BUNDLE_V2_SHA256
        if not bundle_v2_match:
            bundle_v2_status = "FAIL_BUNDLE_HASH_MISMATCH"
            defects.append(
                f"FAIL_BUNDLE_HASH_MISMATCH: canonical_metric_bundle_v2.json SHA mismatch (actual={bundle_v2_sha}, expected={EXPECTED_BUNDLE_V2_SHA256})"
            )
        else:
            bundle_v2_status = "PASS"

        try:
            bundle_v2_data = load_json(bundle_v2)
            candidate_base_git_sha = bundle_v2_data.get("candidate_base_git_sha")
        except Exception as exc:
            bundle_v2_status = "FAIL_BUNDLE_HASH_MISMATCH"
            defects.append(
                f"FAIL_BUNDLE_HASH_MISMATCH: Failed reading JSON from {bundle_v2}: {exc}"
            )

    bundle_v2_rel = (
        bundle_v2.relative_to(repo_root).as_posix()
        if bundle_v2.is_relative_to(repo_root)
        else bundle_v2.as_posix()
    )
    bundle_v2_section = {
        "path": bundle_v2_rel,
        "sha256": bundle_v2_sha,
        "expected_sha256": EXPECTED_BUNDLE_V2_SHA256,
        "sha_match": bundle_v2_match,
        "candidate_base_git_sha": candidate_base_git_sha,
        "status": bundle_v2_status,
    }

    # 3. Base descriptor (manifest) validation
    base_descriptor_section: dict[str, Any] = {
        "path": "base_public_v3/canonical_bundle_manifest.json",
        "sha256": None,
        "derived_from_bundle_sha256": None,
        "status": "FAIL",
    }
    manifest_data: dict[str, Any] = {}

    if not bundle_dir.exists():
        base_descriptor_section["status"] = "FAIL_MISSING_BUNDLE_DIR"
        defects.append(
            f"FAIL_MISSING_BUNDLE_DIR: Target bundle directory does not exist at {bundle_dir}"
        )
    else:
        manifest_path = None
        for cand_manifest in (
            bundle_dir / "canonical_bundle_manifest.json",
            bundle_dir / "public_package_manifest.json",
            bundle_dir / "canonical_metric_bundle_v1.json",
        ):
            if cand_manifest.is_file():
                manifest_path = cand_manifest
                break

        if manifest_path is None:
            base_descriptor_section["status"] = "FAIL_MISSING_BUNDLE_DIR"
            defects.append(
                f"FAIL_MISSING_BUNDLE_DIR: Missing canonical_bundle_manifest.json in {bundle_dir}"
            )
        else:
            manifest_sha = compute_sha256(manifest_path)
            base_descriptor_section["path"] = (
                manifest_path.relative_to(bundle_dir.parent).as_posix()
                if manifest_path.is_relative_to(bundle_dir.parent)
                else manifest_path.as_posix()
            )
            base_descriptor_section["sha256"] = manifest_sha
            try:
                manifest_data = load_json(manifest_path)
                derived_sha = manifest_data.get("derived_from", {}).get("bundle_sha256")
                base_descriptor_section["derived_from_bundle_sha256"] = derived_sha

                if manifest_sha != EXPECTED_PUBLIC_MANIFEST_SHA256:
                    base_descriptor_section["status"] = "FAIL_MANIFEST_HASH_MISMATCH"
                    defects.append(
                        f"FAIL_MANIFEST_HASH_MISMATCH: Manifest SHA mismatch (actual={manifest_sha}, expected={EXPECTED_PUBLIC_MANIFEST_SHA256})"
                    )
                elif derived_sha != CANONICAL_BUNDLE_SHA256:
                    base_descriptor_section["status"] = "FAIL_DERIVED_SHA_MISMATCH"
                    defects.append(
                        f"FAIL_DERIVED_SHA_MISMATCH: Derived bundle SHA mismatch (actual={derived_sha}, expected={CANONICAL_BUNDLE_SHA256})"
                    )
                else:
                    base_descriptor_section["status"] = "PASS_AUTHENTICATED"
            except Exception as exc:
                base_descriptor_section["status"] = "FAIL_CORRUPT_MANIFEST"
                defects.append(
                    f"FAIL_CORRUPT_MANIFEST: Failed parsing manifest {manifest_path}: {exc}"
                )

    # 4. Input files audit (exact 10 files)
    input_files_map: dict[str, str] = {}
    missing_inputs: list[str] = []
    mismatched_inputs: list[str] = []

    expected_inputs_spec = manifest_data.get("source_file_digests") or {
        k: v.get("sha256") if isinstance(v, dict) else v
        for k, v in manifest_data.get("raw_input_files", {}).items()
    }

    for req_in in sorted(REQUIRED_INPUT_FILES):
        p = find_bundle_file(bundle_dir, f"inputs/{req_in}") or find_bundle_file(bundle_dir, req_in)
        if p is None or not p.is_file():
            missing_inputs.append(req_in)
            input_files_map[req_in] = "MISSING"
        else:
            act_sha = compute_sha256(p)
            input_files_map[req_in] = act_sha
            exp_sha = expected_inputs_spec.get(req_in)
            if exp_sha and act_sha != exp_sha:
                mismatched_inputs.append(f"{req_in} ({act_sha} != {exp_sha})")

    if missing_inputs:
        defects.append(f"FAIL_MISSING_FILES: Missing required input files: {missing_inputs}")
    if mismatched_inputs:
        defects.append(f"FAIL_FILE_HASH_MISMATCH: Input file hash mismatch: {mismatched_inputs}")

    inputs_ok = (
        len(missing_inputs) == 0 and len(mismatched_inputs) == 0 and len(input_files_map) == 10
    )
    input_files_audit = {
        "total_files": len(input_files_map),
        "all_verified": inputs_ok,
        "status": "PASS" if inputs_ok else "FAIL",
        "files": input_files_map,
    }

    # 5. Output files audit (exact 8 files)
    output_files_map: dict[str, str] = {}
    missing_outputs: list[str] = []
    mismatched_outputs: list[str] = []

    expected_outputs_spec = manifest_data.get("output_file_digests") or {
        k: v.get("sha256") if isinstance(v, dict) else v
        for k, v in manifest_data.get("accepted_analytical_outputs", {}).items()
    }

    for req_out in sorted(REQUIRED_OUTPUT_FILES):
        p = find_bundle_file(bundle_dir, f"outputs/{req_out}") or find_bundle_file(
            bundle_dir, req_out
        )
        if p is None or not p.is_file():
            missing_outputs.append(req_out)
            output_files_map[req_out] = "MISSING"
        else:
            act_sha = compute_sha256(p)
            output_files_map[req_out] = act_sha
            exp_sha = expected_outputs_spec.get(req_out)
            if exp_sha and act_sha != exp_sha:
                mismatched_outputs.append(f"{req_out} ({act_sha} != {exp_sha})")

    if missing_outputs:
        defects.append(f"FAIL_MISSING_FILES: Missing required output files: {missing_outputs}")
    if mismatched_outputs:
        defects.append(f"FAIL_FILE_HASH_MISMATCH: Output file hash mismatch: {mismatched_outputs}")

    outputs_ok = (
        len(missing_outputs) == 0 and len(mismatched_outputs) == 0 and len(output_files_map) == 8
    )
    output_files_audit = {
        "total_files": len(output_files_map),
        "all_verified": outputs_ok,
        "status": "PASS" if outputs_ok else "FAIL",
        "files": output_files_map,
    }

    # 6. Sanitized provenance audit (exact 4 assets)
    prov_map: dict[str, str] = {}
    missing_prov: list[str] = []
    mismatched_prov: list[str] = []

    for rel_p, exp_sha in sorted(APPROVED_PUBLIC_PROVENANCE_SPEC.items()):
        p = find_bundle_file(bundle_dir, rel_p)
        if p is None or not p.is_file():
            missing_prov.append(rel_p)
            prov_map[rel_p] = "MISSING"
        else:
            act_sha = compute_sha256(p)
            prov_map[rel_p] = act_sha
            if act_sha != exp_sha:
                mismatched_prov.append(f"{rel_p} ({act_sha} != {exp_sha})")

    if missing_prov:
        defects.append(f"FAIL_MISSING_FILES: Missing required provenance assets: {missing_prov}")
    if mismatched_prov:
        defects.append(
            f"FAIL_FILE_HASH_MISMATCH: Provenance asset hash mismatch: {mismatched_prov}"
        )

    prov_ok = len(missing_prov) == 0 and len(mismatched_prov) == 0 and len(prov_map) == 4
    sanitized_provenance_audit = {
        "total_assets": len(prov_map),
        "all_verified": prov_ok,
        "status": "PASS" if prov_ok else "FAIL",
        "assets": prov_map,
    }

    # 7. Runtime recovery wrapper audit
    wrapper_path = find_bundle_file(bundle_dir, "runtime/runtime_recovery_wrapper.py")
    wrapper_sha = None
    wrapper_block_sha = None
    wrapper_ok = False

    if wrapper_path is None or not wrapper_path.is_file():
        defects.append("FAIL_MISSING_FILES: Missing runtime/runtime_recovery_wrapper.py")
    else:
        wrapper_sha = compute_sha256(wrapper_path)
        try:
            tree = ast.parse(wrapper_path.read_text(encoding="utf-8"))
            raw_block = ""
            for node in tree.body:
                if (
                    isinstance(node, ast.Assign)
                    and any(
                        isinstance(t, ast.Name) and t.id == "RAW_WRAPPER_BLOCK"
                        for t in node.targets
                    )
                    and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                ):
                    raw_block = node.value.value
                    break
            if raw_block:
                wrapper_block_sha = hashlib.sha256(raw_block.encode("utf-8")).hexdigest()
            else:
                defects.append(
                    "FAIL_FILE_HASH_MISMATCH: RAW_WRAPPER_BLOCK constant not found in runtime wrapper"
                )
        except Exception as exc:
            defects.append(f"FAIL_FILE_HASH_MISMATCH: Error parsing runtime wrapper AST: {exc}")

        if (
            wrapper_sha == EXPECTED_RUNTIME_WRAPPER_SHA256
            and wrapper_block_sha == CANONICAL_WRAPPER_BLOCK_SHA256
        ):
            wrapper_ok = True
        else:
            defects.append(
                f"FAIL_FILE_HASH_MISMATCH: Runtime wrapper digest mismatch "
                f"(file_sha={wrapper_sha}, block_sha={wrapper_block_sha})"
            )

    runtime_wrapper_audit = {
        "runtime_recovery_wrapper_sha256": wrapper_sha,
        "ast_raw_wrapper_block_sha256": wrapper_block_sha,
        "status": "PASS" if wrapper_ok else "FAIL",
    }

    # 8. Dynamic financial reconciliation
    financial_reconciliation: dict[str, Any] = {
        "total_study_budget_usd": None,
        "prior_pilot_provisional_hold_usd": None,
        "initial_available_usd": None,
        "cumulative_settled_cost_usd": None,
        "remaining_available_balance_usd": None,
        "completed_records": 0,
        "provider_attempts": 0,
        "monetary_reserves_created": 0,
        "monetary_settlements_executed": 0,
        "detected_retries": 0,
        "retry_target": None,
        "status": "FAIL",
    }

    anchor_file = find_bundle_file(bundle_dir, "inputs/.study_anchor.json") or find_bundle_file(
        bundle_dir, ".study_anchor.json"
    )
    summary_file = find_bundle_file(bundle_dir, "inputs/run_summary.json") or find_bundle_file(
        bundle_dir, "run_summary.json"
    )
    journal_file = find_bundle_file(bundle_dir, "inputs/request_journal.jsonl") or find_bundle_file(
        bundle_dir, "request_journal.jsonl"
    )

    if anchor_file and summary_file and journal_file:
        try:
            anchor_data = load_json(anchor_file)
            summary_data = load_json(summary_file)

            total_budget = Decimal(str(anchor_data.get("total_budget_usd", "0")))
            prior_hold = Decimal(str(anchor_data.get("prior_pilot_provisional_hold_usd", "0")))
            initial_avail = Decimal(str(anchor_data.get("initial_available_usd", "0")))

            budget_summary = summary_data.get("study_budget", {})
            settled_cost = Decimal(str(budget_summary.get("cumulative_settled_cost_usd", "0")))
            avail_balance = Decimal(
                str(budget_summary.get("uncommitted_available_balance_usd", "0"))
            )

            arithmetic_valid = initial_avail == (total_budget - prior_hold) and avail_balance == (
                initial_avail - settled_cost
            )

            request_attempts: list[dict[str, Any]] = []
            reserves: list[dict[str, Any]] = []
            settlements: list[dict[str, Any]] = []
            key_attempts: dict[tuple[str, str], list[dict[str, Any]]] = {}

            with open(journal_file, "r", encoding="utf-8") as f:
                for line in f:
                    line_str = line.strip()
                    if not line_str:
                        continue
                    entry = json.loads(line_str)
                    evt = entry.get("event")
                    if evt == "attempt_receipt":
                        request_attempts.append(entry)
                        k = tuple(entry.get("key", []))
                        if len(k) == 2:
                            key_attempts.setdefault(k, []).append(entry)
                    elif evt == "monetary_reserve":
                        reserves.append(entry)
                    elif evt == "monetary_settle":
                        settlements.append(entry)

            retries = [k for k, atts in key_attempts.items() if len(atts) > 1]
            retry_target_str = str(retries[0]) if retries else None

            counts_valid = (
                len(settlements) == 6400
                and len(request_attempts) == 6401
                and len(reserves) == 6400
                and len(retries) == 1
                and retries[0] == ("view_d870d574", "rag_k1")
            )

            financial_reconciliation.update(
                {
                    "total_study_budget_usd": f"{total_budget:.8f}",
                    "prior_pilot_provisional_hold_usd": f"{prior_hold:.8f}",
                    "initial_available_usd": f"{initial_avail:.8f}",
                    "cumulative_settled_cost_usd": f"{settled_cost:.8f}",
                    "remaining_available_balance_usd": f"{avail_balance:.8f}",
                    "completed_records": len(settlements),
                    "provider_attempts": len(request_attempts),
                    "monetary_reserves_created": len(reserves),
                    "monetary_settlements_executed": len(settlements),
                    "detected_retries": len(retries),
                    "retry_target": retry_target_str,
                    "status": "PASS_EXACT_RECONCILIATION"
                    if (arithmetic_valid and counts_valid)
                    else "FAIL",
                }
            )

            if not arithmetic_valid:
                defects.append(
                    "FAIL_FINANCIAL_RECONCILIATION_MISMATCH: Budget balance arithmetic violated"
                )
            if not counts_valid:
                defects.append(
                    f"FAIL_FINANCIAL_RECONCILIATION_MISMATCH: Journal counts mismatch "
                    f"(settlements={len(settlements)}, attempts={len(request_attempts)}, retries={len(retries)})"
                )
        except Exception as exc:
            financial_reconciliation["status"] = "FAIL"
            defects.append(
                f"FAIL_FINANCIAL_RECONCILIATION_MISMATCH: Error processing finance logs: {exc}"
            )
    else:
        defects.append(
            "FAIL_MISSING_FILES: Missing financial ledger files (.study_anchor.json, run_summary.json, or request_journal.jsonl)"
        )

    # 9. Dynamic comparison of regenerated replay outputs
    regenerated_evaluation: dict[str, Any] = {}
    missing_replay_files: list[str] = []

    if not replay_out_dir.exists():
        defects.append(
            f"FAIL_MISSING_REPLAY_OUTPUTS: Replay output directory does not exist at {replay_out_dir}"
        )

    for fname in NATIVE_METRIC_FILES:
        section_key = fname.replace(".json", "")
        regen_path = replay_out_dir / "regenerated_native_6" / fname
        if not regen_path.is_file():
            regen_path = replay_out_dir / fname

        canon_path = find_bundle_file(bundle_dir, f"outputs/{fname}") or find_bundle_file(
            bundle_dir, fname
        )

        if not regen_path.is_file():
            missing_replay_files.append(fname)
            regenerated_evaluation[section_key] = {
                "field_count": 0,
                "float_tolerance": "1e-12",
                "monetary_comparison": "exact Decimal",
                "status": "MISSING_REPLAY_OUTPUT",
            }
            continue

        if canon_path is None or not canon_path.is_file():
            regenerated_evaluation[section_key] = {
                "field_count": 0,
                "float_tolerance": "1e-12",
                "monetary_comparison": "exact Decimal",
                "status": "MISSING_CANONICAL_OUTPUT",
            }
            continue

        try:
            actual_obj = load_json(regen_path)
            expected_obj = load_json(canon_path)
            f_count = count_fields(actual_obj)
            match_ok, disc = compare_metrics_trees(
                actual_obj, expected_obj, path=fname, float_tolerance=1e-12
            )

            entry: dict[str, Any] = {
                "field_count": f_count,
                "float_tolerance": "1e-12",
                "monetary_comparison": "exact Decimal",
                "status": "MATCH" if match_ok else "MISMATCH",
            }
            if not match_ok:
                entry["discrepancies"] = disc[:10]
                defects.append(
                    f"FAIL_REPLAY_METRIC_MISMATCH: Metric discrepancies in {fname} ({len(disc)} differences)"
                )
            regenerated_evaluation[section_key] = entry
        except Exception as exc:
            regenerated_evaluation[section_key] = {
                "field_count": 0,
                "float_tolerance": "1e-12",
                "monetary_comparison": "exact Decimal",
                "status": "ERROR",
                "error": str(exc),
            }
            defects.append(f"FAIL_REPLAY_METRIC_MISMATCH: Failed comparing {fname}: {exc}")

    # RQ analysis comparison
    rq_regen_path = replay_out_dir / "regenerated_rq" / "rq_analysis.json"
    if not rq_regen_path.is_file():
        rq_regen_path = replay_out_dir / "rq_analysis.json"

    rq_canon_path = find_bundle_file(bundle_dir, "outputs/rq_analysis.json") or find_bundle_file(
        bundle_dir, "rq_analysis.json"
    )

    if not rq_regen_path.is_file():
        missing_replay_files.append("rq_analysis.json")
        regenerated_evaluation["rq_analysis"] = {
            "field_count": 0,
            "bootstrap_iterations": 1000,
            "bootstrap_seed": 42,
            "scientific_fields_status": "MISSING_REPLAY_OUTPUT",
            "status": "MISSING_REPLAY_OUTPUT",
        }
    elif rq_canon_path is None or not rq_canon_path.is_file():
        regenerated_evaluation["rq_analysis"] = {
            "field_count": 0,
            "bootstrap_iterations": 1000,
            "bootstrap_seed": 42,
            "scientific_fields_status": "MISSING_CANONICAL_OUTPUT",
            "status": "MISSING_CANONICAL_OUTPUT",
        }
    else:
        try:
            actual_rq = load_json(rq_regen_path)
            expected_rq = load_json(rq_canon_path)
            rq_count = count_fields(actual_rq)
            match_rq_ok, disc_rq = compare_metrics_trees(
                actual_rq, expected_rq, path="rq_analysis.json", float_tolerance=1e-12
            )

            rq_entry: dict[str, Any] = {
                "field_count": rq_count,
                "bootstrap_iterations": 1000,
                "bootstrap_seed": 42,
                "scientific_fields_status": "MATCH" if match_rq_ok else "MISMATCH",
                "status": "MATCH" if match_rq_ok else "MISMATCH",
            }
            if not match_rq_ok:
                rq_entry["discrepancies"] = disc_rq[:10]
                defects.append(
                    f"FAIL_REPLAY_METRIC_MISMATCH: RQ analysis discrepancies ({len(disc_rq)} differences)"
                )
            regenerated_evaluation["rq_analysis"] = rq_entry
        except Exception as exc:
            regenerated_evaluation["rq_analysis"] = {
                "field_count": 0,
                "bootstrap_iterations": 1000,
                "bootstrap_seed": 42,
                "scientific_fields_status": "ERROR",
                "status": "ERROR",
                "error": str(exc),
            }
            defects.append(f"FAIL_REPLAY_METRIC_MISMATCH: Failed comparing rq_analysis.json: {exc}")

    if missing_replay_files:
        defects.append(
            f"FAIL_MISSING_REPLAY_OUTPUTS: Missing regenerated replay output files: {missing_replay_files}"
        )

    # 10. Verdict and overall defect evaluation
    defects_count = len(defects)
    if defects_count == 0:
        verdict = "PASS_CANONICAL_OFFLINE_VERIFIED"
    else:
        # Assign primary defect code from the first failure
        primary_code = defects[0].split(":")[0].strip()
        verdict = primary_code

    verifier_path = repo_root / "scripts/reproduce_canonical_study.py"
    verifier_sha = compute_sha256(verifier_path) if verifier_path.is_file() else None

    report: dict[str, Any] = {
        "schema_version": "r9_saved_data_reproduction_report_v1",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "verifier_script": "scripts/reproduce_canonical_study.py",
        "verifier_sha256": verifier_sha,
        "candidate_package_zip": candidate_zip_section,
        "base_descriptor": base_descriptor_section,
        "input_files_audit": input_files_audit,
        "output_files_audit": output_files_audit,
        "sanitized_provenance_audit": sanitized_provenance_audit,
        "runtime_wrapper_audit": runtime_wrapper_audit,
        "financial_reconciliation": financial_reconciliation,
        "regenerated_evaluation_deep_comparison": regenerated_evaluation,
        "canonical_metric_bundle_v2_binding": bundle_v2_section,
        "verdict": verdict,
        "defects_count": defects_count,
        "defects": defects,
    }

    if output_report is not None:
        out_path = Path(output_report).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Report written to {out_path}")

    exit_code = 1 if (strict and defects_count > 0) else 0
    return report, exit_code


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate comprehensive saved-data reproduction report for R9."
    )
    repo_root = Path(__file__).resolve().parents[1]
    default_bundle = repo_root / ".tmp/unpacked_v4/base_public_v3"
    if not default_bundle.exists():
        default_bundle = repo_root / "artifacts/public_package_staging/03_public_canonical_package"

    parser.add_argument(
        "--bundle-dir",
        type=Path,
        default=default_bundle,
        help="Path to canonical bundle directory (default: .tmp/unpacked_v4/base_public_v3)",
    )
    parser.add_argument(
        "--replay-out-dir",
        type=Path,
        default=repo_root / ".tmp/r9_replay_output",
        help="Path to replay evaluation output directory (default: .tmp/r9_replay_output)",
    )
    parser.add_argument(
        "--candidate-zip",
        type=Path,
        default=repo_root / ".tmp/downloaded_candidate/public_v4_candidate_20261003.zip",
        help="Path to candidate ZIP file (default: .tmp/downloaded_candidate/public_v4_candidate_20261003.zip)",
    )
    parser.add_argument(
        "--bundle-v2",
        type=Path,
        default=repo_root / "artifacts/results/canonical_metric_bundle_v2.json",
        help="Path to canonical_metric_bundle_v2.json",
    )
    parser.add_argument(
        "--output-report",
        type=Path,
        default=repo_root / "reports/evidence/r9_saved_data_reproduction_report.json",
        help="Path to output report JSON file",
    )
    parser.add_argument(
        "--strict",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Exit with return code 1 if any defect is found (default: True)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    report, exit_code = generate_reproduction_report(
        bundle_dir=args.bundle_dir,
        replay_out_dir=args.replay_out_dir,
        candidate_zip=args.candidate_zip,
        bundle_v2=args.bundle_v2,
        output_report=args.output_report,
        strict=args.strict,
    )
    print("=" * 80)
    print(f"R9 REPRODUCTION REPORT VERDICT: {report['verdict']}")
    print(f"Total Defects Detected:        {report['defects_count']}")
    if report["defects"]:
        print("\nDefects list:")
        for idx, defect in enumerate(report["defects"], 1):
            print(f"  {idx}. {defect}")
    print("=" * 80)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
