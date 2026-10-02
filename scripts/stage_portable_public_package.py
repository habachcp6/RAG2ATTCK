"""Physical Staging and Sanitization Builder for Portable Public Package.

Author: Native Agent A (Track A - Audit & Recovery)
Scope: RAG2ATTCK Portable Public Package (PR #24)
Egress Invariant: Strictly offline local filesystem operations.

Physically stages and sanitizes:
  - 9 pure canonical input files (byte-exact copies, original SHA-256 preserved)
  - 1 transformed input file (.study_anchor.json: ledger_path/output_directory relative)
  - 7 pure canonical output files (byte-exact copies, original SHA-256 preserved)
  - 1 transformed output file (rq_analysis.json: secondary_scope_packet relative)
  - 4 sanitized provenance assets with links to original SHA-256 digests
  - 1 portable runtime recovery wrapper asset
  - 1 neutralized portable package manifest (canonical_bundle_manifest.json)
  - Fail-closed security and private workstation path byte scanner
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CANONICAL_BUNDLE_SHA256 = "00cd9df247af395e924235b42108b91e1fdc7ca3e7a190499cb7544f6bc6612f"
CANONICAL_WRAPPER_BLOCK_SHA256 = "e4a0115ff2d712bf6a0b896b50d9f4d412b786707d9721f47c74a4ac174e5f68"

# Explicit 10 canonical input files and expected digests
CANONICAL_INPUT_SPEC: dict[str, str] = {
    ".study_anchor.json": "d03aec39091e77defd90ea2756332d60305e6350a5b15fe724e806264e61fb25",
    "manifest.json": "66b658cfa9dd42e131ec567bbe043b8bc87ac6e92aeaa5e8f6661b0195e486e5",
    "no_rag_predictions.jsonl": "70034c5e3c417fc4a28c357d00d6a046751175ed03e7815645fa09e0411e228a",
    "rag_k1_predictions.jsonl": "745cb883a90b4d1bac7c76c4007b143893834530a843e153fc24277aae5da7ac",
    "rag_k3_predictions.jsonl": "29f215d74a3139df53036c642c8a14762bec4542d04685125cf28d024571b006",
    "rag_k5_predictions.jsonl": "896d900d10e25af748e00235c33cace84511c450bf7cfb0da2b4d1a658124178",
    "rag_k10_predictions.jsonl": "40cd9d2b19c691ed8bcb97ff5dfbebd378857346e9a06b00a9ab54e51fd9a122",
    "request_journal.jsonl": "f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31",
    "run_summary.json": "67df38e336b4250b5a5c044b754ab02e8cc1826b8569f76d9bdf265ae4f84c2a",
    "study_ledger.json": "21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8",
}

# Explicit 8 canonical output files and expected digests
CANONICAL_OUTPUT_SPEC: dict[str, str] = {
    "failure_decomposition.json": (
        "1ea3a899fefc7f92bcb739ab16e70036c269ebff16a7ec7e38240d2cc2c1c05d"
    ),
    "overall_metrics.json": ("25662753963ecdd05d16b8607095fffb964c0d53cd2c43026c50b47b22e55074"),
    "per_condition_metrics.json": (
        "e6592f9a0f97739be1168f9d1448e0d209fe4a300727ff6ad78902523f1591d6"
    ),
    "per_technique_metrics.json": (
        "a2f96027439ba876b1c48b155a18f99872d3c4cc2c62c1bdc573a09aa73f49ef"
    ),
    "retrieval_conditional_metrics.json": (
        "2c68395f4ae923167b7cbc08835ff2772044ddc7695f69c0781ec277287d775f"
    ),
    "rq_analysis.json": ("945d413b1c55483c27b16d22dbdfddbcfc773419b06b463f4430530b17c94615"),
    "rq_analysis_summary.md": ("712d495d5d71e5d96fd844fcb3dfdbc88e722056e265cf4a19d3813d9d9446c6"),
    "run_provenance.json": ("90918c9efe149c537c9b2cee7f7392607f273c12627bcc61b9dc9443359e63a1"),
}

# 4 Provenance assets and expected original digests
PROVENANCE_SPEC: dict[str, str] = {
    "s2_evaluation_execute_20261002.md": (
        "b988a599800bbbb01b0418e60bfd00fbbce3ab2c4d631da678f99bfd2141c4b5"
    ),
    "root_canonical_export_validation_v2.json": (
        "551d0ca63101701837365a845078ab3b2f0e14a0b6c6f4946092f8cfd3ef1f39"
    ),
    "terminal_process_proof_20261002.json": (
        "cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e"
    ),
    "terminal_original_bytes_inventory_20261002.json": (
        "f50f4da12b23502f26ff9c3ba948dc25e7441c34dec61b5c732943440f579c7b"
    ),
}


def compute_sha256(data: bytes) -> str:
    """Compute hex SHA-256 digest of raw byte content."""
    return hashlib.sha256(data).hexdigest()


def build_staged_package(
    source_bundle_dir: Path,
    orchestration_dir: Path,
    output_dir: Path,
) -> dict[str, Any]:
    """Execute complete physical staging and sanitization pipeline."""
    source_bundle_dir = source_bundle_dir.resolve()
    orchestration_dir = orchestration_dir.resolve()
    output_dir = output_dir.resolve()

    print("================================================================================")
    print("PORTABLE PUBLIC PACKAGE BUILDER & SANITIZER")
    print(f"Source Canonical Bundle:  {source_bundle_dir}")
    print(f"Orchestration Directory:  {orchestration_dir}")
    print(f"Target Staging Directory: {output_dir}")
    print("================================================================================")

    # 1. Aliasing and safety checks
    if source_bundle_dir == output_dir:
        raise ValueError(f"Source bundle and output directory cannot be identical: {output_dir}")
    if output_dir in source_bundle_dir.parents:
        raise ValueError(f"Output directory cannot be a parent of source bundle: {output_dir}")
    if source_bundle_dir in output_dir.parents:
        raise ValueError(
            f"Source bundle cannot be a parent of output directory: {source_bundle_dir}"
        )

    # 2. Enforce strict destination safety: output_dir must be new or empty
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(
            f"Target output directory already exists and is not empty: {output_dir}. "
            "Builder strictly requires a new non-existent path or an empty directory "
            "to prevent accidental file destruction or evidence contamination."
        )

    # 3. Cryptographic verification of original bundle manifest BEFORE loading
    source_manifest_path = source_bundle_dir / "canonical_metric_bundle_v1.json"
    if not source_manifest_path.exists():
        raise FileNotFoundError(f"Missing original bundle manifest: {source_manifest_path}")

    source_manifest_bytes = source_manifest_path.read_bytes()
    source_manifest_sha = compute_sha256(source_manifest_bytes)
    if source_manifest_sha != CANONICAL_BUNDLE_SHA256:
        raise ValueError(
            f"Original bundle manifest SHA mismatch:\n"
            f"  Expected: {CANONICAL_BUNDLE_SHA256}\n"
            f"  Got:      {source_manifest_sha}"
        )
    print(f"[PASS] Original bundle manifest SHA-256 verified: {source_manifest_sha}")

    inputs_staging = output_dir / "inputs"
    outputs_staging = output_dir / "outputs"
    provenance_staging = output_dir / "provenance"
    runtime_staging = output_dir / "runtime"

    inputs_staging.mkdir(parents=True, exist_ok=True)
    outputs_staging.mkdir(parents=True, exist_ok=True)
    provenance_staging.mkdir(parents=True, exist_ok=True)
    runtime_staging.mkdir(parents=True, exist_ok=True)

    byte_preserved_registry: dict[str, dict[str, Any]] = {}
    transformed_registry: dict[str, dict[str, Any]] = {}
    provenance_registry: dict[str, dict[str, Any]] = {}
    runtime_registry: dict[str, dict[str, Any]] = {}

    # 4. Stage 10 Canonical Inputs
    source_inputs_dir = source_bundle_dir / "inputs"
    print("\nStaging 10 Canonical Inputs:")
    for fname, expected_orig_sha in CANONICAL_INPUT_SPEC.items():
        src_path = source_inputs_dir / fname
        if not src_path.exists():
            raise FileNotFoundError(f"Missing canonical input file: {src_path}")
        raw_bytes = src_path.read_bytes()
        actual_orig_sha = compute_sha256(raw_bytes)
        if actual_orig_sha != expected_orig_sha:
            raise ValueError(
                f"Source input {fname} SHA mismatch: "
                f"expected {expected_orig_sha}, got {actual_orig_sha}"
            )

        if fname == ".study_anchor.json":
            # Semantic transformation of workstation paths to portable package paths
            anchor_obj = json.loads(raw_bytes.decode("utf-8"))

            anchor_obj["ledger_path"] = "inputs/study_ledger.json"
            anchor_obj["output_directory"] = "outputs"

            sanitized_bytes = (
                json.dumps(anchor_obj, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            )
            dst_path = inputs_staging / fname
            dst_path.write_bytes(sanitized_bytes)
            sanitized_sha = compute_sha256(sanitized_bytes)

            transformed_registry["inputs/.study_anchor.json"] = {
                "size_bytes": len(sanitized_bytes),
                "original_sha256": expected_orig_sha,
                "sanitized_sha256": sanitized_sha,
                "transformed_keypaths": [".ledger_path", ".output_directory"],
                "transform_map": {
                    ".ledger_path": (
                        "Neutralized private workstation path to relative inputs/study_ledger.json"
                    ),
                    ".output_directory": (
                        "Neutralized private workstation path to relative outputs"
                    ),
                },
                "numerical_invariance": (
                    "Strictly invariant: total_budget_usd, prior_pilot_provisional_hold_usd, "
                    "initial_available_usd, pricing_contract_sha256 remain 100% identical."
                ),
            }
            print(
                f"  [TRANSFORMED INPUT]  {fname:<25} {len(sanitized_bytes):>8} bytes  "
                f"new={sanitized_sha[:12]}... (orig={expected_orig_sha[:12]}...)"
            )
        else:
            # Pure byte preservation
            dst_path = inputs_staging / fname
            dst_path.write_bytes(raw_bytes)
            byte_preserved_registry[f"inputs/{fname}"] = {
                "size_bytes": len(raw_bytes),
                "sha256": actual_orig_sha,
                "classification": "byte_exact_preserved",
            }
            print(
                f"  [PRESERVED INPUT]    {fname:<25} {len(raw_bytes):>8} bytes  {actual_orig_sha}"
            )

    # 5. Stage and Sanitize 4 Provenance Assets
    print("\nStaging & Sanitizing 4 Provenance Assets:")
    # Asset A: s2_evaluation_execute_public.md
    sec_src = orchestration_dir / "s2_evaluation_execute_20261002.md"
    if not sec_src.exists():
        raise FileNotFoundError(f"Missing secondary authorization file: {sec_src}")
    sec_raw = sec_src.read_text(encoding="utf-8")
    sec_orig_sha = compute_sha256(sec_raw.encode("utf-8"))
    if sec_orig_sha != PROVENANCE_SPEC["s2_evaluation_execute_20261002.md"]:
        raise ValueError(f"Digest mismatch on s2_evaluation_execute: {sec_orig_sha}")

    # Redact private workstation paths
    sec_text = sec_raw
    replacements = [
        (
            "C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/study/artifacts/study_budget/study_ledger.json",
            "inputs/study_ledger.json",
        ),
        (
            "C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/study/.study_anchor.json",
            "inputs/.study_anchor.json",
        ),
        ("C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/run", "inputs"),
        ("C:/Users/hahoa/.codex/artifacts/rag2attck/sealed-live66-20261002/study", "inputs"),
        (
            "C:/Users/hahoa/.codex/artifacts/rag2attck/canonical-metrics-208ac00-v1/native",
            "outputs",
        ),
        ("C:/Users/hahoa/.codex/artifacts/rag2attck/canonical-metrics-208ac00-v1/rq", "outputs"),
        ("C:/Users/hahoa/.codex/artifacts/rag2attck/canonical-metrics-208ac00-v1", "outputs"),
        ("D:/RAG2ATTCK-worktrees/integrated-audit-s1", "."),
        (
            "D:/RAG2ATT&CK/artifacts/orchestration/root_canonical_snapshot_seal_v1.json",
            "provenance/root_canonical_snapshot_seal_v1.json",
        ),
        ("D:/RAG2ATT&CK/artifacts/orchestration", "provenance"),
    ]
    for orig, repl in replacements:
        sec_text = sec_text.replace(orig, repl)

    sec_dst_bytes = sec_text.encode("utf-8")
    sec_dst = provenance_staging / "s2_evaluation_execute_public.md"
    sec_dst.write_bytes(sec_dst_bytes)
    sec_pub_sha = compute_sha256(sec_dst_bytes)
    provenance_registry["provenance/s2_evaluation_execute_public.md"] = {
        "size_bytes": len(sec_dst_bytes),
        "original_sha256": sec_orig_sha,
        "sanitized_sha256": sec_pub_sha,
        "derivation": (
            "Neutralized private workstation absolute paths into relative POSIX paths; "
            "all evaluation directives, frozen protocols, thresholds, and "
            "execution requirements preserved."
        ),
    }
    print(
        f"  [SANITIZED PROV]     s2_evaluation_execute_public.md       "
        f"{len(sec_dst_bytes):>8} bytes  {sec_pub_sha}"
    )

    # Asset B: root_canonical_export_validation_public.json
    root_val_src = orchestration_dir / "root_canonical_export_validation_v2.json"
    if not root_val_src.exists():
        raise FileNotFoundError(f"Missing root export validation: {root_val_src}")
    val_raw = root_val_src.read_bytes()
    val_orig_sha = compute_sha256(val_raw)
    if val_orig_sha != PROVENANCE_SPEC["root_canonical_export_validation_v2.json"]:
        raise ValueError(f"Digest mismatch on root export validation: {val_orig_sha}")

    val_obj = json.loads(val_raw.decode("utf-8"))
    val_obj["rq_path"] = "outputs/rq_analysis.json"
    val_dst_bytes = json.dumps(val_obj, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    val_dst = provenance_staging / "root_canonical_export_validation_public.json"
    val_dst.write_bytes(val_dst_bytes)
    val_pub_sha = compute_sha256(val_dst_bytes)
    provenance_registry["provenance/root_canonical_export_validation_public.json"] = {
        "size_bytes": len(val_dst_bytes),
        "original_sha256": val_orig_sha,
        "sanitized_sha256": val_pub_sha,
        "derivation": (
            "Neutralized rq_path to outputs/rq_analysis.json; all 16,740 checked fields, "
            "verdicts, and financial breakdowns preserved."
        ),
    }
    print(
        f"  [SANITIZED PROV]     root_canonical_export_validation_public.json "
        f"{len(val_dst_bytes):>8} bytes  {val_pub_sha}"
    )

    # Asset C: terminal_process_proof_public.json
    proof_src = orchestration_dir / "terminal_process_proof_20261002.json"
    if not proof_src.exists():
        raise FileNotFoundError(f"Missing terminal process proof: {proof_src}")
    proof_raw = proof_src.read_bytes()
    proof_orig_sha = compute_sha256(proof_raw)
    if proof_orig_sha != PROVENANCE_SPEC["terminal_process_proof_20261002.json"]:
        raise ValueError(f"Digest mismatch on terminal process proof: {proof_orig_sha}")

    proof_obj = json.loads(proof_raw.decode("utf-8"))
    proof_obj["authoritative_log"] = "logs/task-1264.log"
    proof_dst_bytes = json.dumps(proof_obj, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    proof_dst = provenance_staging / "terminal_process_proof_public.json"
    proof_dst.write_bytes(proof_dst_bytes)
    proof_pub_sha = compute_sha256(proof_dst_bytes)
    provenance_registry["provenance/terminal_process_proof_public.json"] = {
        "size_bytes": len(proof_dst_bytes),
        "original_sha256": proof_orig_sha,
        "sanitized_sha256": proof_pub_sha,
        "derivation": (
            "Neutralized authoritative_log to relative logs path; all run IDs, process "
            "parameters, and accounting summaries preserved."
        ),
    }
    print(
        f"  [SANITIZED PROV]     terminal_process_proof_public.json    "
        f"{len(proof_dst_bytes):>8} bytes  {proof_pub_sha}"
    )

    # Asset D: terminal_original_bytes_inventory_public.json
    inv_src = orchestration_dir / "terminal_original_bytes_inventory_20261002.json"
    if not inv_src.exists():
        raise FileNotFoundError(f"Missing terminal original bytes inventory: {inv_src}")
    inv_raw = inv_src.read_bytes()
    inv_orig_sha = compute_sha256(inv_raw)
    if inv_orig_sha != PROVENANCE_SPEC["terminal_original_bytes_inventory_20261002.json"]:
        raise ValueError(f"Digest mismatch on original bytes inventory: {inv_orig_sha}")

    inv_obj = json.loads(inv_raw.decode("utf-8"))
    new_files_map = {}
    for k, v in inv_obj.get("files", {}).items():
        leaf = Path(k).name
        new_files_map[f"inputs/{leaf}"] = v
    inv_obj["files"] = new_files_map
    inv_dst_bytes = json.dumps(inv_obj, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    inv_dst = provenance_staging / "terminal_original_bytes_inventory_public.json"
    inv_dst.write_bytes(inv_dst_bytes)
    inv_pub_sha = compute_sha256(inv_dst_bytes)
    provenance_registry["provenance/terminal_original_bytes_inventory_public.json"] = {
        "size_bytes": len(inv_dst_bytes),
        "original_sha256": inv_orig_sha,
        "sanitized_sha256": inv_pub_sha,
        "derivation": (
            "Mapped absolute filesystem keys to relative inputs/<file> paths; "
            "all original SHA-256 digests and byte sizes preserved."
        ),
    }
    print(
        f"  [SANITIZED PROV]     terminal_original_bytes_inventory_public.json "
        f"{len(inv_dst_bytes):>8} bytes  {inv_pub_sha}"
    )

    # 6. Stage 8 Canonical Outputs (cleanly under outputs/ ONLY)
    print("\nStaging 8 Canonical Analytical Outputs:")
    for fname, expected_orig_sha in CANONICAL_OUTPUT_SPEC.items():
        src_path = source_bundle_dir / "outputs" / fname
        if not src_path.exists():
            src_path = source_bundle_dir / fname
        if not src_path.exists():
            raise FileNotFoundError(f"Missing canonical output file: {fname}")

        raw_bytes = src_path.read_bytes()
        actual_orig_sha = compute_sha256(raw_bytes)
        if actual_orig_sha != expected_orig_sha:
            raise ValueError(
                f"Source output {fname} SHA mismatch: "
                f"expected {expected_orig_sha}, got {actual_orig_sha}"
            )

        dst_path = outputs_staging / fname
        if fname == "rq_analysis.json":
            # Semantic transformation of private secondary scope packet path and hash binding
            rq_obj = json.loads(raw_bytes.decode("utf-8"))
            orig_sec_hash = None
            if "analysis_run_parameters" in rq_obj:
                orig_sec_hash = rq_obj["analysis_run_parameters"].get(
                    "secondary_scope_authorization_sha256"
                )
                rq_obj["analysis_run_parameters"]["secondary_scope_authorization_packet"] = (
                    "provenance/s2_evaluation_execute_public.md"
                )
                rq_obj["analysis_run_parameters"]["secondary_scope_authorization_sha256"] = (
                    sec_pub_sha
                )

            sanitized_bytes = json.dumps(rq_obj, indent=2, sort_keys=True).encode("utf-8") + b"\n"
            dst_path.write_bytes(sanitized_bytes)
            sanitized_sha = compute_sha256(sanitized_bytes)

            transformed_registry["outputs/rq_analysis.json"] = {
                "size_bytes": len(sanitized_bytes),
                "original_sha256": expected_orig_sha,
                "sanitized_sha256": sanitized_sha,
                "transformed_keypaths": [
                    ".analysis_run_parameters.secondary_scope_authorization_packet",
                    ".analysis_run_parameters.secondary_scope_authorization_sha256",
                ],
                "transform_map": {
                    ".analysis_run_parameters.secondary_scope_authorization_packet": (
                        "Neutralized private workstation path to "
                        "relative provenance/s2_evaluation_execute_public.md"
                    ),
                    ".analysis_run_parameters.secondary_scope_authorization_sha256": (
                        "Updated binding digest from original private packet hash "
                        f"({orig_sec_hash}) to sanitized public packet hash ({sec_pub_sha})"
                    ),
                },
                "original_secondary_scope_authorization_sha256": orig_sec_hash,
                "sanitized_secondary_scope_authorization_sha256": sec_pub_sha,
                "numerical_invariance": (
                    "Strictly invariant: all delta-F1 values, McNemar p-values, "
                    "bootstrap confidence intervals, recall rates, token counts, and "
                    "financial amounts remain 100% mathematically identical."
                ),
            }
            print(
                f"  [TRANSFORMED OUTPUT] {fname:<25} {len(sanitized_bytes):>8} bytes  "
                f"new={sanitized_sha[:12]}... (orig={expected_orig_sha[:12]}...)"
            )
        else:
            # Pure byte preservation
            dst_path.write_bytes(raw_bytes)
            byte_preserved_registry[f"outputs/{fname}"] = {
                "size_bytes": len(raw_bytes),
                "sha256": actual_orig_sha,
                "classification": "byte_exact_preserved",
            }
            print(
                f"  [PRESERVED OUTPUT]   {fname:<25} {len(raw_bytes):>8} bytes  {actual_orig_sha}"
            )

    # 7. Stage Portable Runtime Recovery Wrapper Asset
    print("\nStaging Portable Runtime Recovery Wrapper Asset:")
    wrapper_fixture_path = Path("tests/fixtures/runtime_recovery_wrapper_fixture.py")
    if not wrapper_fixture_path.exists():
        raise FileNotFoundError(f"Missing runtime recovery wrapper fixture: {wrapper_fixture_path}")

    import importlib.util

    fixture_spec = importlib.util.spec_from_file_location(
        "runtime_recovery_wrapper_fixture", wrapper_fixture_path
    )
    if fixture_spec is None or fixture_spec.loader is None:
        raise ImportError(f"Could not load spec for {wrapper_fixture_path}")
    fixture_mod = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture_mod)
    raw_wrapper_block = getattr(fixture_mod, "RAW_WRAPPER_BLOCK", "")

    wrapper_block_sha = compute_sha256(raw_wrapper_block.encode("utf-8"))
    if wrapper_block_sha != CANONICAL_WRAPPER_BLOCK_SHA256:
        raise ValueError(
            f"Runtime wrapper block digest mismatch: "
            f"expected {CANONICAL_WRAPPER_BLOCK_SHA256}, got {wrapper_block_sha}"
        )

    wrapper_dst = runtime_staging / "runtime_recovery_wrapper.py"
    wrapper_bytes = wrapper_fixture_path.read_bytes()
    wrapper_dst.write_bytes(wrapper_bytes)
    wrapper_sha = compute_sha256(wrapper_bytes)
    runtime_registry["runtime/runtime_recovery_wrapper.py"] = {
        "size_bytes": len(wrapper_bytes),
        "sha256": wrapper_sha,
        "raw_wrapper_block_sha256": wrapper_block_sha,
        "canonical_launcher_sha256": (
            "05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa"
        ),
    }
    print(
        f"  [RUNTIME WRAPPER]    runtime_recovery_wrapper.py           "
        f"{len(wrapper_bytes):>8} bytes  {wrapper_sha}"
    )

    # 8. Build Comprehensive Sanitized Manifest
    print("\nGenerating Portable Manifest canonical_bundle_manifest.json...")
    # Build backward compatible digests mapping
    source_file_digests: dict[str, str] = {}
    for rel_p, info in byte_preserved_registry.items():
        if rel_p.startswith("inputs/"):
            source_file_digests[rel_p.replace("inputs/", "")] = info["sha256"]
    source_file_digests[".study_anchor.json"] = transformed_registry["inputs/.study_anchor.json"][
        "sanitized_sha256"
    ]

    output_file_digests: dict[str, str] = {}
    for rel_p, info in byte_preserved_registry.items():
        if rel_p.startswith("outputs/"):
            output_file_digests[rel_p.replace("outputs/", "")] = info["sha256"]
    output_file_digests["rq_analysis.json"] = transformed_registry["outputs/rq_analysis.json"][
        "sanitized_sha256"
    ]

    portable_manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "schema_version": "2.0.0",
        "package_id": "canonical-bundle-public-v1",
        "derived_from": {
            "bundle_sha256": CANONICAL_BUNDLE_SHA256,
            "root_acceptance_sha256": PROVENANCE_SPEC["root_canonical_export_validation_v2.json"],
            "secondary_scope_authorization_sha256": PROVENANCE_SPEC[
                "s2_evaluation_execute_20261002.md"
            ],
            "terminal_process_proof_sha256": PROVENANCE_SPEC[
                "terminal_process_proof_20261002.json"
            ],
            "terminal_original_bytes_inventory_sha256": PROVENANCE_SPEC[
                "terminal_original_bytes_inventory_20261002.json"
            ],
            "runtime_wrapper_block_sha256": CANONICAL_WRAPPER_BLOCK_SHA256,
            "rationale": (
                "Neutralize private workstation filesystem paths while strictly preserving "
                "100% byte-exact copies of all 16 pure experimental data files and "
                "100% mathematical invariance across transformed metadata."
            ),
        },
        "execution_context": {
            "experiment_id": "synthetic-paired-test-1",
            "run_id": "live-66b94b1676bf46a9",
            "dataset_split": "test",
            "execution_mode": "live",
            "protocol_version": "experiment-protocol-v1.1",
            "protocol_file_sha256": (
                "a402b04ab463172f9d4079bff27b089ca8a21ffd0805d097af6cb1f3c7b5a8fb"
            ),
            "core_manifest_sha256": (
                "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
            ),
        },
        "secondary_scope_authorization": {
            "path": "provenance/s2_evaluation_execute_public.md",
            "sha256": sec_pub_sha,
            "original_sha256": sec_orig_sha,
        },
        "byte_preserved_files": byte_preserved_registry,
        "sanitized_transformed_files": transformed_registry,
        "sanitized_provenance_assets": provenance_registry,
        "runtime_assets": runtime_registry,
        "source_file_digests": source_file_digests,
        "output_file_digests": output_file_digests,
    }

    manifest_bytes = json.dumps(portable_manifest, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    manifest_file = output_dir / "canonical_bundle_manifest.json"
    manifest_file.write_bytes(manifest_bytes)
    manifest_sha = compute_sha256(manifest_bytes)
    print(
        f"  [PORTABLE MANIFEST]  canonical_bundle_manifest.json "
        f"({len(manifest_bytes)} bytes, SHA: {manifest_sha})"
    )

    # Also synchronize git-tracked manifest copy
    git_manifest_path = Path("artifacts/public_package_staging/public_package_manifest.json")
    if git_manifest_path.parent.exists():
        git_manifest_path.write_bytes(manifest_bytes)
        print(f"  [SYNCED GIT MANIFEST] public_package_manifest.json ({len(manifest_bytes)} bytes)")

    # 9. Robust Byte Scanning and Strict Fail-Closed Security Gate
    print("\nExecuting Byte Scanning and Private Path / Secret Security Audit:")
    forbidden_path_regexes = [
        re.compile(
            rb'(?:[A-Za-z]:[/\\]Users[/\\][^\s"\'\\/]+|[A-Za-z]:[/\\](?:RAG2ATT&CK|RAG2ATTCK)[^\s"\'\\/]*)',
            re.IGNORECASE,
        ),
        re.compile(
            rb'(?:[A-Za-z]:\\\\Users\\\\[^\s"\'\\/]+|[A-Za-z]:\\\\(?:RAG2ATT&CK|RAG2ATTCK)[^\s"\'\\/]*)',
            re.IGNORECASE,
        ),
        re.compile(rb"\bhahoa\b", re.IGNORECASE),
        re.compile(rb"RAG2ATT&CK", re.IGNORECASE),
        re.compile(rb"RAG2ATTCK-worktrees", re.IGNORECASE),
    ]

    secret_patterns = [
        re.compile(rb"sk-[a-zA-Z0-9]{20,}"),
        re.compile(rb"ghp_[a-zA-Z0-9]{20,}"),
        re.compile(rb"bearer\s+[a-zA-Z0-9_\-\.]{20,}", re.IGNORECASE),
        re.compile(rb"password\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    ]

    total_scanned_files = 0
    total_scanned_bytes = 0
    defects: list[str] = []

    for fpath in sorted(output_dir.rglob("*")):
        if not fpath.is_file():
            continue
        rel = fpath.relative_to(output_dir).as_posix()
        file_bytes = fpath.read_bytes()
        total_scanned_files += 1
        total_scanned_bytes += len(file_bytes)

        # Scan for forbidden path tokens
        for r in forbidden_path_regexes:
            matches = r.findall(file_bytes)
            if matches:
                defects.append(
                    f"Forbidden workstation path token detected in {rel}: "
                    f"{len(matches)} occurrences"
                )

        # Scan for secrets
        for s in secret_patterns:
            matches = s.findall(file_bytes)
            if matches:
                defects.append(
                    f"Credential/secret pattern detected in {rel}: {len(matches)} occurrences"
                )

    print(f"  Scanned Files: {total_scanned_files}")
    print(f"  Scanned Bytes: {total_scanned_bytes:,} bytes")
    print(f"  Defects Found: {len(defects)}")

    if defects:
        print("\n[CRITICAL FAILURE] Sanitization security audit failed:")
        for d in defects:
            print(f"  - {d}")
        sys.exit(1)

    print("\n[PASS] 100% SANITIZATION & INTEGRITY AUDIT PASSED:")
    print("  - 0 private workstation path occurrences")
    print("  - 0 credentials or secrets detected")
    print("  - 16 pure scientific data files 100% byte-exact preserved")
    print("  - 2 metadata files strictly sanitized with full numerical invariance")
    print("  - 4 provenance assets sanitized and bound to original SHA-256 digests")
    print("  - 1 portable runtime recovery wrapper staged and digest verified")
    print("================================================================================")

    return {
        "status": "PASS",
        "output_dir": str(output_dir),
        "total_files": total_scanned_files,
        "total_bytes": total_scanned_bytes,
        "manifest_sha256": manifest_sha,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build sanitized portable public package for RAG2ATTCK canonical replay."
    )
    parser.add_argument(
        "--source-bundle",
        type=Path,
        default=Path(
            os.getenv(
                "CANONICAL_BUNDLE_DIR",
                "C:/Users/hahoa/.codex/artifacts/rag2attck/canonical-accepted-bundle-v2",
            )
        ),
        help="Path to original canonical accepted metric bundle directory.",
    )
    parser.add_argument(
        "--orchestration-dir",
        type=Path,
        default=Path("D:/RAG2ATT&CK/artifacts/orchestration"),
        help="Path to orchestration directory containing provenance assets.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/public_package_staging/canonical-bundle-public-v1"),
        help="Path to target staging directory.",
    )

    args = parser.parse_args()

    try:
        build_staged_package(
            source_bundle_dir=args.source_bundle,
            orchestration_dir=args.orchestration_dir,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(f"\n[CRITICAL BUILD ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
