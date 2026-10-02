#!/usr/bin/env python3
"""
scripts/build_canonical_metric_bundle.py

Deterministic canonical metric bundle v2 builder and validator for RAG2ATT&CK.
Assembles structured metrics, financial accounting, cache receipts, cohorts,
and provenance into artifacts/results/canonical_metric_bundle_v2.json.

Strictly FAIL-CLOSED on hash mismatch, broken invariant, or missing field.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Fixed Protocol & Provenance Constants
EXPECTED_CORE_MANIFEST_SHA256 = "8b1b3ea4d11a8e3c0e53aff0ad7d3f8976c68d582d0848747e4be38a292258c4"
EXPECTED_PUBLIC_MANIFEST_SHA256 = "32f520c0db7cfdd3252103eff7910c504e92561faaf2cb273856dc24777c244c"
EXPECTED_TERMINAL_SEAL_SHA256 = "ae7a9ada86927a79e0c6916b44d3f0ba9e1f9756df55dd7b2fce712b35d48701"
EXPECTED_TERMINAL_PROOF_SHA256 = "cbffe862b60c49b5c872837f81b580d5a59197b681f7b7623fd844b897a0981e"
EXPECTED_ANALYSIS_SOURCE_SHA256 = "f85d7f7373e825dcc7171ce4491fd15c6fb755955da245041783fe317bc80351"
EXPECTED_PROTOCOL_SHA256 = "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"
EXPECTED_PRICING_CONTRACT_SHA256 = "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565"

# Historical & Superseding Lineage Hashes
HISTORICAL_ANALYSIS_SOURCE_SHA256 = "c48eeb27b19626344e5f10b2cac674437b4053bb01f014060905702c52235f95"
AUTHORIZING_PACKET_PUBLIC_SHA256 = "d515f70426435e9edb79cdc415e91c23b16e189fd171d4db4b04074c9b580aa1"
AUTHORIZING_PACKET_ORIGINAL_SHA256 = "b988a599800bbbb01b0418e60bfd00fbbce3ab2c4d631da678f99bfd2141c4b5"
SUPERSEDING_AUTHORIZING_PACKET_SHA256 = "c34b1350881d61f153a50fd5fa2b79a9438ece09c2a2b09d022e74e863313570"
ROOT_INTEGRATED_SOURCE_AUDIT_SHA256 = "b164b13d76a76ed7893ebf6b7e87ff5a28898a15f3425a6764e0f4efa84db608"
ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256 = "cdc875da1647552a3596100e2d168f7cb79878e64e50c0f1f59e6a0c4bceed05"

# Git Commit Lineage Bindings
EXECUTION_GIT_SHA = "80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315"
NATIVE_EVALUATION_GIT_SHA = "208ac00a9fe86813d4e4ec4fa72b2a943a2e4fdb"
RQ_V2_INTEGRATED_GIT_SHA = "264ed31472c4f0f74e519938b65876915f9c15a7"
CANDIDATE_BASE_GIT_SHA = "b69a6909acda4c7588744acc7e1d6c20bfce2612"

# Fixed Cohort and Denominator Constants
COHORT_TOTAL_VIEWS = 1280
COHORT_TOTAL_PAIRS = 640
COHORT_MAPPED_VIEWS = 718
COHORT_AMBIGUOUS_VIEWS = 311
COHORT_UNMAPPED_VIEWS = 251
COHORT_SINGLE_GT_VIEWS = 678
COHORT_MULTI_GT_VIEWS = 40
COHORT_TOTAL_GT_SUPPORT_INSTANCES = 768
COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS = 440
COHORT_MACRO_UNIVERSE = 474
COHORT_SUPPORTED_CLASSES = 8
COHORT_UNSUPPORTED_CLASSES = 466

# Financial Constants (Decimal)
BUDGET_CAP_USD = Decimal("19.99000000")
PILOT_HOLD_USD = Decimal("0.05264010")
SETTLED_USD = Decimal("6.57575890")
TOTAL_ACCOUNTED_USD = Decimal("6.62839900")
AVAILABLE_BALANCE_USD = Decimal("13.36160100")
LOGICAL_WORST_CASE_RESERVATION_USD = Decimal("2.15898240")

P95_STATUS_POLICY = "NOT REPORTED — approval evidence not established"

CONDITIONS = ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
RETRIEVAL_K_VALUES = {"no_rag": 0, "rag_k1": 1, "rag_k3": 3, "rag_k5": 5, "rag_k10": 10}

# Declared immutable recorded creation timestamp established during candidate generation.
# Distinct from dynamic runtime regeneration times.
RECORDED_BUNDLE_CREATION_TIMESTAMP_UTC = "2026-10-03T03:20:00+00:00"


def _reject_nonfinite(constant: str) -> None:
    """Fail-closed on NaN, Infinity, -Infinity in JSON input."""
    raise ValueError(f"Non-finite JSON constant not allowed: {constant}")


def check_finite(obj: Any, path: str = "") -> None:
    """Recursively verify all float numbers are strictly finite."""
    if isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError(f"Non-finite float value {obj} found at {path}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            check_finite(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            check_finite(v, f"{path}[{i}]")


def compute_sha256(path: Path) -> str:
    """Compute sha256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def verify_file_hash(path: Path, expected_sha: str, description: str) -> bytes:
    """Verify that file exists, matches expected sha256 hash, and return raw bytes."""
    if not path.is_file():
        raise FileNotFoundError(f"Missing required file ({description}): {path}")
    raw_bytes = path.read_bytes()
    actual_sha = hashlib.sha256(raw_bytes).hexdigest()
    if actual_sha != expected_sha:
        raise ValueError(
            f"Hash mismatch for {description} at {path}!\n"
            f"  Expected: {expected_sha}\n"
            f"  Actual:   {actual_sha}"
        )
    return raw_bytes


def load_and_verify_json(path: Path, expected_sha: str, description: str) -> Dict[str, Any]:
    """Load JSON from disk after single-read hash verification and non-finite rejection."""
    raw_bytes = verify_file_hash(path, expected_sha, description)
    text = raw_bytes.decode("utf-8")
    data = json.loads(text, parse_constant=_reject_nonfinite)
    check_finite(data, description)
    return data


def verify_public_package(public_package_dir: Path) -> Tuple[Dict[str, Any], Dict[str, bytes]]:
    """
    Verify public canonical package against canonical_bundle_manifest.json.
    Returns the parsed manifest dictionary and cached raw bytes of checked files.
    """
    manifest_path = public_package_dir / "canonical_bundle_manifest.json"
    manifest = load_and_verify_json(manifest_path, EXPECTED_PUBLIC_MANIFEST_SHA256, "public package manifest")

    file_bytes_cache: Dict[str, bytes] = {}

    # 1. Byte-preserved files
    for rel_path, spec in manifest.get("byte_preserved_files", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sha256"]
        file_bytes_cache[rel_path] = verify_file_hash(file_path, expected_sha, f"byte_preserved file {rel_path}")

    # 2. Sanitized transformed files
    for rel_path, spec in manifest.get("sanitized_transformed_files", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sanitized_sha256"]
        file_bytes_cache[rel_path] = verify_file_hash(file_path, expected_sha, f"sanitized_transformed file {rel_path}")

    # 3. Sanitized provenance assets
    for rel_path, spec in manifest.get("sanitized_provenance_assets", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sanitized_sha256"]
        file_bytes_cache[rel_path] = verify_file_hash(file_path, expected_sha, f"sanitized_provenance asset {rel_path}")

    # 4. Runtime assets
    for rel_path, spec in manifest.get("runtime_assets", {}).items():
        file_path = public_package_dir / rel_path
        expected_sha = spec["sha256"]
        file_bytes_cache[rel_path] = verify_file_hash(file_path, expected_sha, f"runtime asset {rel_path}")

    return manifest, file_bytes_cache


def verify_run_seal(seal_path: Path) -> Dict[str, Any]:
    """Verify canonical run seal v1 against expected hash and invariants."""
    seal = load_and_verify_json(seal_path, EXPECTED_TERMINAL_SEAL_SHA256, "canonical run seal")

    if seal.get("seal_type") != "canonical-independent-validation-seal-v1":
        raise ValueError(f"Invalid seal_type: {seal.get('seal_type')}")
    if seal.get("fixture_only", False) is not False:
        raise ValueError(f"Run seal fixture_only must be False, got {seal.get('fixture_only')}")
    if not seal.get("production_ready", False):
        raise ValueError(f"Run seal production_ready must be True, got {seal.get('production_ready')}")
    if seal.get("has_breach", True):
        raise ValueError("Run seal has_breach is True")
    if seal.get("cumulative_settled_cost_usd") != str(SETTLED_USD):
        raise ValueError(
            f"Seal settled cost mismatch: {seal.get('cumulative_settled_cost_usd')} != {SETTLED_USD}"
        )
    if seal.get("uncommitted_available_balance_usd") != str(AVAILABLE_BALANCE_USD):
        raise ValueError(
            f"Seal balance mismatch: {seal.get('uncommitted_available_balance_usd')} != {AVAILABLE_BALANCE_USD}"
        )
    if seal.get("total_records") != 6400:
        raise ValueError(f"Seal total_records mismatch: {seal.get('total_records')} != 6400")
    if seal.get("code_manifest_sha256") != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError("Seal code_manifest_sha256 mismatch")
    if seal.get("pricing_contract_sha256") != EXPECTED_PRICING_CONTRACT_SHA256:
        raise ValueError("Seal pricing_contract_sha256 mismatch")
    if seal.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        raise ValueError("Seal protocol_sha256 mismatch")

    # Check terminal proof
    tp = seal.get("terminal_proof", {})
    if tp.get("sha256") != EXPECTED_TERMINAL_PROOF_SHA256:
        raise ValueError("Seal terminal_proof.sha256 mismatch")
    fs = tp.get("final_summary", {})
    if not fs.get("complete", False):
        raise ValueError("Seal terminal_proof complete is not True")
    if fs.get("record_count") != 6400:
        raise ValueError(f"Seal terminal_proof record_count mismatch: {fs.get('record_count')}")
    if fs.get("consumed_provider_attempts") != 6401:
        raise ValueError(f"Seal attempts mismatch: {fs.get('consumed_provider_attempts')}")
    if fs.get("requests_consumed") != 6401:
        raise ValueError(f"Seal requests_consumed mismatch: {fs.get('requests_consumed')}")

    return seal


def parse_request_journal_cache(
    journal_path: Path,
    predictions_dir: Optional[Path] = None,
    raw_journal_bytes: Optional[bytes] = None,
    predictions_bytes_cache: Optional[Dict[str, bytes]] = None,
) -> Dict[str, Any]:
    """
    Parse request_journal.jsonl to extract precise cached_tokens telemetry.
    Strictly verifies receipt bindings, single physical failure, and retry success.
    Enforces complete join across all 6,400 terminal receipts and prediction records
    (including 6,387 SUCCESS and 13 INCOMPLETE) without TOCTOU or silent mismatch pass.
    """
    total_receipts = 0
    total_cached_tokens = 0
    cached_tokens_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}
    observed_receipts_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}
    missing_receipts_by_condition: Dict[str, int] = {c: 0 for c in CONDITIONS}

    # Tracking specific transport error and retry
    transport_failure_info: Optional[Dict[str, Any]] = None
    retry_success_info: Optional[Dict[str, Any]] = None

    # Load predictions for terminal join
    # Prefer verified predictions_bytes_cache to prevent TOCTOU and redundant disk reads
    predictions_map: Dict[Tuple[str, str], Dict[str, Any]] = {}
    if predictions_bytes_cache is not None:
        for cond in CONDITIONS:
            pred_bytes = predictions_bytes_cache.get(f"inputs/{cond}_predictions.jsonl")
            if pred_bytes is None:
                pred_bytes = predictions_bytes_cache.get(f"{cond}_predictions.jsonl")
            if pred_bytes is not None:
                for pline in pred_bytes.decode("utf-8").splitlines():
                    if not pline.strip():
                        continue
                    pentry = json.loads(pline, parse_constant=_reject_nonfinite)
                    sample_id = pentry.get("sample_id")
                    c_val = pentry.get("condition")
                    if sample_id and c_val:
                        predictions_map[(sample_id, c_val)] = pentry

    if not predictions_map and predictions_dir is not None and predictions_dir.is_dir():
        for cond in CONDITIONS:
            pred_file = predictions_dir / f"{cond}_predictions.jsonl"
            if not pred_file.is_file():
                # Try inputs/predictions convention if any
                alt_pred = predictions_dir / "inputs" / f"{cond}_predictions.jsonl"
                if alt_pred.is_file():
                    pred_file = alt_pred
            if pred_file.is_file():
                with open(pred_file, "r", encoding="utf-8") as pf:
                    for pline in pf:
                        if not pline.strip():
                            continue
                        pentry = json.loads(pline, parse_constant=_reject_nonfinite)
                        sample_id = pentry.get("sample_id")
                        c_val = pentry.get("condition")
                        if sample_id and c_val:
                            predictions_map[(sample_id, c_val)] = pentry

    # If predictions were loaded, enforce strict completeness upfront
    if predictions_map:
        if len(predictions_map) != 6400:
            raise ValueError(f"Expected 6400 predictions across all conditions, got {len(predictions_map)}")
        for cond in CONDITIONS:
            cond_count = sum(1 for (sid, c) in predictions_map.keys() if c == cond)
            if cond_count != 1280:
                raise ValueError(f"Expected 1280 predictions for condition {cond}, got {cond_count}")

    # Read journal
    if raw_journal_bytes is not None:
        lines = raw_journal_bytes.decode("utf-8").splitlines()
    else:
        with open(journal_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

    terminal_receipts: Dict[Tuple[str, str], Dict[str, Any]] = {}

    for line_num, line in enumerate(lines, 1):
        if not line.strip():
            continue
        entry = json.loads(line, parse_constant=_reject_nonfinite)
        if entry.get("event") == "attempt_receipt":
            total_receipts += 1
            key = entry.get("key", [])
            if not isinstance(key, list) or len(key) != 2:
                raise ValueError(f"Invalid attempt_receipt key at line {line_num}: {key}")
            view_id, condition = key[0], key[1]
            if condition not in CONDITIONS:
                raise ValueError(f"Unknown condition in receipt: {condition}")

            cached = entry.get("cached_tokens")
            ordinal = entry.get("ordinal")
            attempt_idx = entry.get("attempt_index")
            status = entry.get("status")

            if cached is None:
                # Physical failure attempt
                missing_receipts_by_condition[condition] += 1
                if status != "API_FAILURE" or ordinal != 5387 or attempt_idx != 0:
                    raise ValueError(
                        f"Unexpected missing cached_tokens attempt at line {line_num}: {entry}"
                    )
                if view_id != "view_d870d574":
                    raise ValueError(f"Unexpected view_id for physical failure: {view_id}")
                transport_failure_info = {
                    "ordinal": ordinal,
                    "key": key,
                    "attempt_index": attempt_idx,
                    "status": status,
                    "error_type": entry.get("error_type"),
                    "input_tokens": entry.get("input_tokens"),
                    "output_tokens": entry.get("output_tokens"),
                    "cached_tokens": None,
                    "model": entry.get("model"),
                }
            else:
                # Type validation: must be exact integer, not boolean
                if isinstance(cached, bool) or not isinstance(cached, int):
                    raise TypeError(f"cached_tokens must be an integer, got {type(cached).__name__}: {cached}")
                if cached < 0:
                    raise ValueError(f"Negative cached_tokens at line {line_num}: {cached}")
                inp_val = entry.get("input_tokens")
                if inp_val is not None and isinstance(inp_val, int) and not isinstance(inp_val, bool) and cached > inp_val:
                    raise ValueError(f"cached_tokens ({cached}) exceeds input_tokens ({inp_val}) at line {line_num}")

                if ordinal != 5388 and attempt_idx != 0:
                    raise ValueError(f"Invalid attempt_index {attempt_idx} for ordinal {ordinal} at line {line_num}")

                observed_receipts_by_condition[condition] += 1
                cached_tokens_by_condition[condition] += cached
                total_cached_tokens += cached
                if cached > 0:
                    if condition != "rag_k1" or ordinal != 5388 or attempt_idx != 1:
                        raise ValueError(
                            f"Unexpected non-zero cached_tokens at line {line_num}: {entry}"
                        )
                    # Enforce strict retry receipt binding
                    if transport_failure_info is not None:
                        if view_id != transport_failure_info["key"][0]:
                            raise ValueError(
                                f"Retry receipt view_id ({view_id}) does not match initial attempt view_id ({transport_failure_info['key'][0]})"
                            )
                    else:
                        if view_id != "view_d870d574":
                            raise ValueError(f"Retry receipt foreign view detected: {view_id}")

                    if status != "SUCCESS":
                        raise ValueError(f"Retry receipt status must be SUCCESS, got: {status}")

                    # Verify exact token counts
                    input_toks = entry.get("input_tokens")
                    if input_toks != 1543:
                        raise ValueError(f"Retry receipt input_tokens mismatch: {input_toks} != 1543")
                    output_toks = entry.get("output_tokens")
                    if output_toks != 452:
                        raise ValueError(f"Retry receipt output_tokens mismatch: {output_toks} != 452")

                    resp_id = entry.get("response_id")
                    if resp_id != "resp_0efb218e56a6ecc1006abf0be6419887d0bca3815a8a0b3f0d":
                        raise ValueError(f"Retry receipt response_id drift: {resp_id}")

                    retry_success_info = {
                        "ordinal": ordinal,
                        "key": key,
                        "attempt_index": attempt_idx,
                        "status": status,
                        "cached_tokens": cached,
                        "input_tokens": input_toks,
                        "output_tokens": output_toks,
                        "response_id": resp_id,
                    }

            # Record terminal receipt for this request key (last attempt is terminal)
            # Since journal ordinals are monotonically increasing, latest entry overwrites earlier retry
            terminal_receipts[(view_id, condition)] = entry

    if total_receipts != 6401:
        raise ValueError(f"Expected exactly 6401 attempt receipts, got {total_receipts}")
    if total_cached_tokens != 1540:
        raise ValueError(f"Expected exactly 1540 total cached tokens, got {total_cached_tokens}")
    if transport_failure_info is None or retry_success_info is None:
        raise ValueError("Failed to locate expected transport failure and retry pair in journal")

    # Strict terminal receipts join against predictions
    if predictions_map:
        if len(terminal_receipts) != 6400:
            raise ValueError(f"Expected exactly 6400 terminal receipts, got {len(terminal_receipts)}")

        receipt_keys = set(terminal_receipts.keys())
        pred_keys = set(predictions_map.keys())
        if receipt_keys != pred_keys:
            missing_in_receipts = pred_keys - receipt_keys
            missing_in_preds = receipt_keys - pred_keys
            raise ValueError(
                f"Receipt and prediction keys mismatch!\n"
                f"  Missing in receipts: {len(missing_in_receipts)}\n"
                f"  Missing in predictions: {len(missing_in_preds)}"
            )

        success_join_count = 0
        incomplete_join_count = 0

        for req_key in sorted(pred_keys):
            receipt = terminal_receipts[req_key]
            pred = predictions_map[req_key]

            r_status = receipt.get("status")
            if r_status not in ("SUCCESS", "INCOMPLETE"):
                raise ValueError(f"Unexpected terminal status in receipt for {req_key}: {r_status}")

            # Verify response_id exists, non-empty, and strictly matches
            r_resp_id = receipt.get("response_id")
            p_resp_id = pred.get("response_id")
            if not r_resp_id or not isinstance(r_resp_id, str):
                raise ValueError(f"Missing or invalid response_id in receipt for {req_key}: {r_resp_id}")
            if not p_resp_id or not isinstance(p_resp_id, str):
                raise ValueError(f"Missing or invalid response_id in prediction for {req_key}: {p_resp_id}")
            if r_resp_id != p_resp_id:
                raise ValueError(
                    f"response_id mismatch for {req_key}!\n"
                    f"  Receipt:    {r_resp_id}\n"
                    f"  Prediction: {p_resp_id}"
                )

            # Verify model identity to prevent model drift
            r_model = receipt.get("model")
            p_model = pred.get("model")
            if not r_model or r_model != "gpt-5.6-luna":
                raise ValueError(f"Receipt model drift for {req_key}: expected gpt-5.6-luna, got {r_model}")
            if r_model != p_model:
                raise ValueError(f"Model mismatch for {req_key}: receipt={r_model} != pred={p_model}")

            # Verify input_tokens == prompt_tokens
            r_inp = receipt.get("input_tokens")
            p_prompt = pred.get("prompt_tokens")
            if isinstance(r_inp, bool) or not isinstance(r_inp, int):
                raise TypeError(f"Receipt input_tokens must be int for {req_key}, got {type(r_inp).__name__}")
            if isinstance(p_prompt, bool) or not isinstance(p_prompt, int):
                raise TypeError(f"Prediction prompt_tokens must be int for {req_key}, got {type(p_prompt).__name__}")
            if r_inp != p_prompt:
                raise ValueError(f"input_tokens mismatch for {req_key}: receipt={r_inp} != pred={p_prompt}")

            # Verify output_tokens == completion_tokens
            r_out = receipt.get("output_tokens")
            p_comp = pred.get("completion_tokens")
            if isinstance(r_out, bool) or not isinstance(r_out, int):
                raise TypeError(f"Receipt output_tokens must be int for {req_key}, got {type(r_out).__name__}")
            if isinstance(p_comp, bool) or not isinstance(p_comp, int):
                raise TypeError(f"Prediction completion_tokens must be int for {req_key}, got {type(p_comp).__name__}")
            if r_out != p_comp:
                raise ValueError(f"output_tokens mismatch for {req_key}: receipt={r_out} != pred={p_comp}")

            # Verify terminal status correspondence with prediction success
            p_success = pred.get("success")
            if r_status == "SUCCESS":
                if p_success is not True:
                    raise ValueError(f"Status SUCCESS requires pred success=True for {req_key}, got {p_success}")
                success_join_count += 1
            elif r_status == "INCOMPLETE":
                if p_success is not False:
                    raise ValueError(f"Status INCOMPLETE requires pred success=False for {req_key}, got {p_success}")
                if r_out != 8192:
                    raise ValueError(f"Status INCOMPLETE must have 8192 output tokens for {req_key}, got {r_out}")
                incomplete_join_count += 1

        if success_join_count != 6387:
            raise ValueError(f"Expected 6387 SUCCESS joined receipts, got {success_join_count}")
        if incomplete_join_count != 13:
            raise ValueError(f"Expected 13 INCOMPLETE joined receipts, got {incomplete_join_count}")

    # Invariants for each condition
    cache_summary_by_condition: Dict[str, Any] = {}
    for c in CONDITIONS:
        sum_c = cached_tokens_by_condition[c]
        obs_c = observed_receipts_by_condition[c]
        miss_c = missing_receipts_by_condition[c]

        # In our study, 1280 logical requests per condition
        # For rag_k1: 1281 receipts (1 missing physical attempt + 1280 observed physical attempts)
        # For other conditions: 1280 receipts (0 missing + 1280 observed)
        if c == "rag_k1":
            if obs_c != 1280 or miss_c != 1 or sum_c != 1540:
                raise ValueError(f"Condition rag_k1 cache invariant breached: obs={obs_c}, miss={miss_c}, sum={sum_c}")
            mean_c = sum_c / 1280.0  # 1.203125
        else:
            if obs_c != 1280 or miss_c != 0 or sum_c != 0:
                raise ValueError(f"Condition {c} cache invariant breached: obs={obs_c}, miss={miss_c}, sum={sum_c}")
            mean_c = 0.0

        cache_summary_by_condition[c] = {
            "condition": c,
            "sum_cached_tokens": sum_c,
            "mean_cached_tokens_per_request": mean_c,
            "terminal_requests_known_count": 1280,
            "terminal_requests_missing_count": 0,
            "physical_attempts_known_count": obs_c,
            "physical_attempts_missing_count": miss_c,
            "total_physical_attempts_count": obs_c + miss_c,
            "logical_sample_count": 1280,
            "cached_tokens_accounting_rule": (
                "Cached tokens represent prompt tokens served from model cache. "
                "Total tokens is prompt_tokens + completion_tokens. "
                "Cached tokens are a subset of prompt tokens and are NOT added into total tokens twice."
            ),
        }

    return {
        "campaign_total_cached_tokens": total_cached_tokens,
        "campaign_total_receipts": total_receipts,
        "campaign_observed_receipts": 6400,
        "campaign_missing_receipts": 1,
        "cache_by_condition": cache_summary_by_condition,
        "transport_failure": transport_failure_info,
        "retry_success": retry_success_info,
    }


def verify_financial_invariants(
    ledger_path: Path,
    raw_ledger_bytes: Optional[bytes] = None,
) -> Dict[str, Any]:
    """
    Verify study_ledger.json against Decimal arithmetic and financial invariants.
    Strictly reconciles item-level settled records by condition and top-level sums.
    """
    if raw_ledger_bytes is not None:
        ledger = json.loads(raw_ledger_bytes.decode("utf-8"), parse_constant=_reject_nonfinite)
    else:
        with open(ledger_path, "r", encoding="utf-8") as f:
            ledger = json.load(f)

    # Top-level ledger checks
    total_budget = Decimal(str(ledger["total_budget_usd"]))
    pilot_hold = Decimal(str(ledger["prior_pilot_provisional_hold_usd"]))
    settled = Decimal(str(ledger["cumulative_settled_cost_usd"]))
    available = Decimal(str(ledger["uncommitted_available_balance_usd"]))
    active_res = Decimal(str(ledger.get("active_reservations_usd", "0")))

    if total_budget != BUDGET_CAP_USD:
        raise ValueError(f"Budget cap mismatch: {total_budget} != {BUDGET_CAP_USD}")
    if pilot_hold != PILOT_HOLD_USD:
        raise ValueError(f"Pilot hold mismatch: {pilot_hold} != {PILOT_HOLD_USD}")
    if settled != SETTLED_USD:
        raise ValueError(f"Settled mismatch: {settled} != {SETTLED_USD}")
    if available != AVAILABLE_BALANCE_USD:
        raise ValueError(f"Available mismatch: {available} != {AVAILABLE_BALANCE_USD}")
    if active_res != Decimal("0"):
        raise ValueError(f"Active reservations remaining: {active_res}")

    # Conservation of money invariant
    accounted = settled + pilot_hold
    if accounted != TOTAL_ACCOUNTED_USD:
        raise ValueError(f"Accounted mismatch: {accounted} != {TOTAL_ACCOUNTED_USD}")
    if accounted + available != total_budget:
        raise ValueError(
            f"Money conservation breached! {accounted} + {available} != {total_budget}"
        )

    # Item-level reconciliation across all 6,400 settled records
    expected_cond_costs: Dict[str, Decimal] = {
        "no_rag": Decimal("0.46714395"),
        "rag_k1": Decimal("1.29723350"),
        "rag_k3": Decimal("1.17888000"),
        "rag_k5": Decimal("1.48311775"),
        "rag_k10": Decimal("2.14938370"),
    }

    settled_records = ledger.get("settled_records", {})
    if len(settled_records) != 6400:
        raise ValueError(f"Expected 6400 settled records in ledger, got {len(settled_records)}")

    derived_cond_costs = {c: Decimal("0") for c in CONDITIONS}
    sum_items = Decimal("0")

    for rec_id, rec_data in settled_records.items():
        parts = rec_id.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid record key format in settled_records: {rec_id}")
        cond = parts[1]
        if cond not in CONDITIONS:
            raise ValueError(f"Unknown condition in settled record: {cond}")
        cost = Decimal(str(rec_data["cost_usd"]))
        refund = Decimal(str(rec_data.get("refund_usd", "0")))
        if cost + refund != LOGICAL_WORST_CASE_RESERVATION_USD:
            raise ValueError(
                f"Record {rec_id} reservation balance broken: cost {cost} + refund {refund} != {LOGICAL_WORST_CASE_RESERVATION_USD}"
            )
        derived_cond_costs[cond] += cost
        sum_items += cost

    if sum_items != settled:
        raise ValueError(
            f"Sum of settled record item costs ({sum_items}) != cumulative_settled_cost_usd ({settled})"
        )

    for cond, expected_c in expected_cond_costs.items():
        if derived_cond_costs[cond] != expected_c:
            raise ValueError(
                f"Derived item cost for {cond} ({derived_cond_costs[cond]}) != expected ({expected_c})"
            )

    return {
        "study_budget_cap_usd": str(total_budget),
        "prior_pilot_provisional_hold_usd": str(pilot_hold),
        "cumulative_settled_cost_usd": str(settled),
        "total_accounted_expenditure_usd": str(accounted),
        "uncommitted_available_balance_usd": str(available),
        "active_reservations_usd": str(active_res),
        "has_breach": ledger.get("has_breach", False),
        "settled_cost_by_condition_usd": {k: str(v) for k, v in derived_cond_costs.items()},
        "commercial_invoice_disclaimer": (
            "Monetary amounts represent tariff-derived accounted costs under API budget guard. "
            "Invoice verification is absent."
        ),
    }


def build_canonical_metric_bundle(
    public_package_dir: Path,
    seal_path: Path,
    output_path: Optional[Path] = None,
    build_timestamp_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Construct canonical_metric_bundle_v2.json from verified inputs and outputs.
    Ensures deterministic bytes, strict non-finite rejection, and machine-generated lineage.
    """
    # Step 1: Verify public package and load manifest + byte cache
    manifest, file_bytes_cache = verify_public_package(public_package_dir)

    # Step 2: Verify run seal
    seal = verify_run_seal(seal_path)

    # Step 3: Parse and cross-verify request journal cache telemetry & predictions
    journal_path = public_package_dir / "inputs" / "request_journal.jsonl"
    cache_telemetry = parse_request_journal_cache(
        journal_path=journal_path,
        predictions_dir=public_package_dir / "inputs",
        raw_journal_bytes=file_bytes_cache.get("inputs/request_journal.jsonl"),
        predictions_bytes_cache=file_bytes_cache,
    )

    # Step 4: Verify financial ledger invariants with item reconciliation
    ledger_path = public_package_dir / "inputs" / "study_ledger.json"
    financial_accounting = verify_financial_invariants(
        ledger_path=ledger_path,
        raw_ledger_bytes=file_bytes_cache.get("inputs/study_ledger.json"),
    )

    # Step 5: Load outputs directly from verified byte cache
    def _parse_output(rel_path: str) -> Dict[str, Any]:
        raw_b = file_bytes_cache.get(rel_path)
        if raw_b is None:
            raw_b = (public_package_dir / rel_path).read_bytes()
        d = json.loads(raw_b.decode("utf-8"), parse_constant=_reject_nonfinite)
        check_finite(d, rel_path)
        return d

    overall_metrics = _parse_output("outputs/overall_metrics.json")
    per_condition_metrics = _parse_output("outputs/per_condition_metrics.json")
    failure_decomposition = _parse_output("outputs/failure_decomposition.json")
    retrieval_conditional_metrics = _parse_output("outputs/retrieval_conditional_metrics.json")
    per_technique_metrics = _parse_output("outputs/per_technique_metrics.json")
    rq_analysis = _parse_output("outputs/rq_analysis.json")
    run_provenance = _parse_output("outputs/run_provenance.json")

    # Step 6: Verify analysis source code sha256 and top-level timestamp
    run_params = rq_analysis.get("analysis_run_parameters", {})
    if run_params.get("analysis_source_sha256") != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise ValueError(
            f"rq_analysis source_sha mismatch: {run_params.get('analysis_source_sha256')} != {EXPECTED_ANALYSIS_SOURCE_SHA256}"
        )
    source_analysis_timestamp = rq_analysis.get("analysis_timestamp")
    if not source_analysis_timestamp or not isinstance(source_analysis_timestamp, str):
        raise ValueError(
            f"Missing or invalid top-level analysis_timestamp in rq_analysis.json: {source_analysis_timestamp}"
        )

    # Step 7: Build Conditions Metric Objects
    rq1_raw = rq_analysis.get("rq1", {}).get("by_condition", {})
    rq2_raw = rq_analysis.get("rq2", {}).get("by_condition", {})
    rq3_raw = rq_analysis.get("rq3", {}).get("tradeoffs_by_condition", {})
    complexity_raw = rq_analysis.get("new_proposed_producer_stratified_gt_complexity", {}).get("by_condition", {})

    conditions_bundle: Dict[str, Any] = {}

    for cond in CONDITIONS:
        k_val = RETRIEVAL_K_VALUES[cond]
        rq1_c = rq1_raw[cond]
        rq2_c = rq2_raw[cond]
        rq3_c = rq3_raw[cond]
        comp_c = complexity_raw[cond]
        cache_c = cache_telemetry["cache_by_condition"][cond]

        # Cohort breakdown for this condition
        cond_cohort = {
            "total_logical_requests": 1280,
            "total_scorable_mapped_views": COHORT_MAPPED_VIEWS,
            "single_gt_mapped_views": comp_c["single_gt_sample_count"],
            "multi_gt_mapped_views": comp_c["multi_gt_sample_count"],
            "ambiguous_excluded_views": COHORT_AMBIGUOUS_VIEWS,
            "unmapped_excluded_views": COHORT_UNMAPPED_VIEWS,
        }
        if cond_cohort["single_gt_mapped_views"] != COHORT_SINGLE_GT_VIEWS or cond_cohort["multi_gt_mapped_views"] != COHORT_MULTI_GT_VIEWS:
            raise ValueError(f"Cohort complexity mismatch in {cond}")

        # RQ1 Metric Object
        acc_e2e = float(rq1_c["accuracy_end_to_end"])
        acc_valid = float(rq1_c["accuracy_valid_outputs"])
        macro_f1 = float(rq1_c["macro_f1"])
        correct_count = int(rq1_c["correct_count"])
        error_count = COHORT_MAPPED_VIEWS - correct_count
        error_rate = error_count / float(COHORT_MAPPED_VIEWS)

        rq1_obj: Dict[str, Any] = {
            "source_pointer": f"outputs/rq_analysis.json#/rq1/by_condition/{cond}",
            "condition": cond,
            "retrieval_k": k_val,
            "is_baseline": (cond == "no_rag"),
            "correct_count": correct_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "error_rate_display": f"{error_rate * 100:.2f}%",
            "scorable_sample_count": COHORT_MAPPED_VIEWS,
            "accuracy_end_to_end": acc_e2e,
            "accuracy_valid_outputs": acc_valid,
            "accuracy_display": f"{acc_e2e * 100:.2f}%",
            "accuracy_e2e_ci_95": rq1_c["accuracy_e2e_ci_95"],
            "accuracy_e2e_ci_95_display": f"[{rq1_c['accuracy_e2e_ci_95'][0] * 100:.2f}%, {rq1_c['accuracy_e2e_ci_95'][1] * 100:.2f}%]",
            "macro_f1": macro_f1,
            "macro_f1_display": f"{macro_f1:.4f}",
            "macro_f1_universe_classes": COHORT_MACRO_UNIVERSE,
            "supported_classes": COHORT_SUPPORTED_CLASSES,
            "unsupported_classes": COHORT_UNSUPPORTED_CLASSES,
            "stratified_complexity": {
                "single_gt": {
                    "sample_count": comp_c["single_gt_sample_count"],
                    "correct_count": comp_c["single_gt_correct_count"],
                    "accuracy_e2e": comp_c["single_gt_accuracy_e2e"],
                    "accuracy_display": f"{comp_c['single_gt_accuracy_e2e'] * 100:.2f}%",
                    "macro_f1": comp_c["single_gt_macro_f1"],
                },
                "multi_gt": {
                    "sample_count": comp_c["multi_gt_sample_count"],
                    "correct_count": comp_c["multi_gt_correct_count"],
                    "accuracy_e2e": comp_c["multi_gt_accuracy_e2e"],
                    "accuracy_display": f"{comp_c['multi_gt_accuracy_e2e'] * 100:.2f}%",
                    "macro_f1": comp_c["multi_gt_macro_f1"],
                }
            }
        }

        if cond != "no_rag":
            delta_info = rq1_c["delta_vs_baseline"]
            delta_acc = float(delta_info["delta_accuracy_end_to_end"])
            delta_ci = delta_info["delta_accuracy_e2e_ci_95"]
            delta_ci_pp = [delta_ci[0] * 100.0, delta_ci[1] * 100.0]
            mcnemar = delta_info["mcnemar_test"]
            p_exact = float(mcnemar["p_value_exact"])
            p_asymptotic = float(mcnemar["p_value_asymptotic"])

            rq1_obj["delta_vs_baseline"] = {
                "delta_accuracy_end_to_end": delta_acc,
                "delta_accuracy_display_pp": f"{delta_acc * 100.0:+.3f} pp",
                "delta_accuracy_ci_95": delta_ci,
                "delta_accuracy_ci_95_display_pp": f"[{delta_ci_pp[0]:+.3f}, {delta_ci_pp[1]:+.3f}] pp",
                "delta_macro_f1": float(delta_info["delta_macro_f1"]),
                "delta_macro_f1_ci_95": delta_info["delta_macro_f1_ci_95"],
                "relative_gain_accuracy_pct": float(delta_info["relative_gain_accuracy_e2e_pct"]),
                "relative_gain_macro_f1_pct": float(delta_info["relative_gain_macro_f1_pct"]),
                "mcnemar_test": {
                    "contingency_table": mcnemar["contingency_table"],
                    "chi2_statistic": float(mcnemar["chi2_statistic"]),
                    "p_value_exact": p_exact,
                    "p_value_asymptotic": p_asymptotic,
                    "display_p_exact": f"{p_exact:.3f}",
                    "display_p_asymptotic": f"{p_asymptotic:.3f}",
                    "significant_at_05": mcnemar["significant_at_05"],
                    "significant_at_01": mcnemar["significant_at_01"],
                }
            }

        # RQ2 Metric Object
        rq2_ret = rq2_c.get("retrieval_metrics", {})
        rq2_cond = rq2_c.get("generation_conditional_accuracy", {})
        rq2_axes = rq2_c.get("independent_failure_axes", {})
        is_retrieval_app = rq2_ret.get("applicable", False)

        rq2_obj: Dict[str, Any] = {
            "source_pointer": f"outputs/rq_analysis.json#/rq2/by_condition/{cond}",
            "condition": cond,
            "retrieval_k": k_val,
            "retrieval_applicable": is_retrieval_app,
        }

        if is_retrieval_app:
            hit_cnt = int(rq2_ret["retrieved_positive_count"])
            tot_cnt = int(rq2_ret["total_positive_sample_count"])
            miss_cnt = tot_cnt - hit_cnt
            hit_rate = float(rq2_ret["retrieval_hit_rate"])
            macro_recall = float(rq2_ret["macro_recall"])

            rq2_obj["retrieval_metrics"] = {
                "applicable": True,
                "retrieval_hit_count": hit_cnt,
                "retrieval_miss_count": miss_cnt,
                "total_scorable_samples": tot_cnt,
                "retrieval_hit_rate": hit_rate,
                "retrieval_hit_rate_display": f"{hit_rate * 100:.2f}%",
                "retrieval_miss_rate": miss_cnt / tot_cnt,
                "retrieval_miss_rate_display": f"{(miss_cnt / tot_cnt) * 100:.2f}%",
                "macro_recall": macro_recall,
            }

            p_corr_hit = float(rq2_cond["p_correct_given_retrieval_success"])
            p_corr_miss = float(rq2_cond["p_correct_given_retrieval_failure"])
            n_succ = int(rq2_cond["retrieval_success_sample_count"])
            n_fail = int(rq2_cond["retrieval_failure_sample_count"])

            rq2_obj["generation_conditional_accuracy"] = {
                "applicable": True,
                "retrieval_success_sample_count": n_succ,
                "p_correct_given_retrieval_success": p_corr_hit,
                "p_correct_given_retrieval_success_display": f"{p_corr_hit * 100:.2f}%",
                "correct_given_retrieval_success_count": round(p_corr_hit * n_succ),
                "retrieval_failure_sample_count": n_fail,
                "p_correct_given_retrieval_failure": p_corr_miss,
                "p_correct_given_retrieval_failure_display": f"{p_corr_miss * 100:.2f}%",
                "correct_given_retrieval_failure_count": round(p_corr_miss * n_fail),
            }

            wrong_cnt = int(rq2_axes["valid_but_wrong_classification_count"])
            overlap_cnt = int(rq2_axes["overlap_retrieval_miss_and_wrong_classification"])
            overlap_frac = overlap_cnt / wrong_cnt if wrong_cnt > 0 else 0.0

            rq2_obj["independent_failure_axes"] = {
                "policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced mutual exclusion. "
                    "Retrieval miss does not establish cause of provider or parse failure."
                ),
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "valid_but_wrong_classification_count": wrong_cnt,
                "valid_but_wrong_classification_rate": float(rq2_axes["valid_but_wrong_classification_rate"]),
                "retrieval_miss_count": miss_cnt,
                "retrieval_miss_rate": float(rq2_axes["retrieval_miss_rate"]),
                "overlap_retrieval_miss_and_wrong_classification": overlap_cnt,
                "overlap_fraction_of_wrong_classification": overlap_frac,
                "overlap_fraction_display": f"{overlap_frac * 100:.2f}%",
                "invalid_attack_id_count": int(rq2_axes.get("invalid_attack_id_count", 0)),
                "parse_failure_count": int(rq2_axes.get("parse_failure_count", 0)),
                "provider_failure_count_mapped": int(rq2_axes.get("provider_failure_count", 0)),
            }
        else:
            # Baseline No-RAG: retrieval metrics are null
            wrong_cnt = int(rq2_axes["valid_but_wrong_classification_count"])
            rq2_obj["retrieval_metrics"] = {
                "applicable": False,
                "note": "Retrieval metrics not applicable to No-RAG baseline (k=0).",
                "retrieval_hit_count": None,
                "retrieval_miss_count": None,
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "retrieval_hit_rate": None,
                "retrieval_miss_rate": None,
                "macro_recall": None,
                "raw_evaluator_trace": {
                    "raw_retrieval_miss_count": 0,
                    "raw_retrieval_miss_rate": 0.0,
                    "raw_overlap_count": 0,
                }
            }
            rq2_obj["generation_conditional_accuracy"] = {
                "applicable": False,
                "note": "Retrieval-conditioned accuracy not applicable to No-RAG baseline (k=0).",
                "p_correct_given_retrieval_success": None,
                "p_correct_given_retrieval_failure": None,
                "retrieval_success_sample_count": None,
                "retrieval_failure_sample_count": None,
            }
            rq2_obj["independent_failure_axes"] = {
                "policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced mutual exclusion."
                ),
                "total_scorable_samples": COHORT_MAPPED_VIEWS,
                "valid_but_wrong_classification_count": wrong_cnt,
                "valid_but_wrong_classification_rate": float(rq2_axes["valid_but_wrong_classification_rate"]),
                "retrieval_miss_count": None,
                "retrieval_miss_rate": None,
                "overlap_retrieval_miss_and_wrong_classification": None,
                "overlap_fraction_of_wrong_classification": None,
                "invalid_attack_id_count": 0,
                "parse_failure_count": 0,
                "provider_failure_count_mapped": 0,
                "raw_evaluator_trace": {
                    "raw_retrieval_miss_count": 0,
                    "raw_retrieval_miss_rate": 0.0,
                    "raw_overlap_count": 0,
                }
            }

        # RQ3 Metric Object
        rq3_lat = rq3_c["latency_ms"]
        rq3_tok = rq3_c["tokens"]
        rq3_cost = rq3_c["financial_cost_usd"]

        prompt_sum = int(rq3_tok["sum_prompt_tokens"])
        comp_sum = int(rq3_tok["sum_completion_tokens"])
        total_tok_sum = int(rq3_tok["sum_total_tokens"])
        if prompt_sum + comp_sum != total_tok_sum:
            raise ValueError(f"Token sum invariant breached in {cond}: {prompt_sum} + {comp_sum} != {total_tok_sum}")

        # Failure rates for this condition
        terminal_incomp_map = {"no_rag": 0, "rag_k1": 0, "rag_k3": 6, "rag_k5": 3, "rag_k10": 4}
        term_incomp_count = terminal_incomp_map[cond]
        term_incomp_rate = term_incomp_count / 1280.0

        rq3_obj: Dict[str, Any] = {
            "source_pointer": f"outputs/rq_analysis.json#/rq3/tradeoffs_by_condition/{cond}",
            "condition": cond,
            "retrieval_k": k_val,
            "observations_count": 1280,
            "latency_ms": {
                "mean": float(rq3_lat["mean"]),
                "median": float(rq3_lat["median"]),
                "p95": None,
                "p95_status": P95_STATUS_POLICY,
                "sum_ms": float(rq3_lat["sum"]),
                "unit": "milliseconds",
                "known_observations_count": 1280,
                "missing_observations_count": 0,
                "measurement_scope": "Client end-to-end request loop including retry backoff",
            },
            "tokens": {
                "prompt_tokens": {
                    "sum": prompt_sum,
                    "mean": float(rq3_tok["mean_prompt_tokens"]),
                    "known_observations_count": 1280,
                    "missing_observations_count": 0,
                },
                "completion_tokens": {
                    "sum": comp_sum,
                    "mean": float(rq3_tok["mean_completion_tokens"]),
                    "known_observations_count": 1280,
                    "missing_observations_count": 0,
                },
                "total_tokens": {
                    "sum": total_tok_sum,
                    "mean": float(rq3_tok["mean_total_tokens"]),
                    "formula": "prompt_tokens + completion_tokens",
                    "known_observations_count": 1280,
                    "missing_observations_count": 0,
                },
                "cached_tokens": {
                    "sum": cache_c["sum_cached_tokens"],
                    "mean": cache_c["mean_cached_tokens_per_request"],
                    "terminal_requests_known_count": cache_c["terminal_requests_known_count"],
                    "terminal_requests_missing_count": cache_c["terminal_requests_missing_count"],
                    "physical_attempts_known_count": cache_c["physical_attempts_known_count"],
                    "physical_attempts_missing_count": cache_c["physical_attempts_missing_count"],
                    "cached_tokens_accounting_rule": cache_c["cached_tokens_accounting_rule"],
                }
            },
            "financial_cost_usd": {
                "ledger_settled_cost_usd": str(Decimal(str(rq3_cost["ledger_settled_cost_usd"]))),
                "token_usage_estimated_cost_usd": str(Decimal(str(rq3_cost["token_usage_estimated_cost_usd"]))),
                "cost_per_logical_request_usd": float(rq3_cost["cost_per_logical_request_usd"]),
                "cost_per_scorable_query_amortized_usd": float(rq3_cost["cost_per_scorable_query_usd"]),
                "cost_per_correct_attribution_usd": float(rq3_cost["cost_per_correct_attribution_usd"]),
                "missing_usage_attempt_receipts_count": int(rq3_cost["missing_usage_attempt_receipts_count"]),
                "missing_usage_attempt_retained_charge_usd": str(Decimal(str(rq3_cost["missing_usage_attempt_worst_charge_usd"]))),
                "observed_cache_credit_usd": "0.00035420" if cond == "rag_k1" else "0.00000000",
                "cost_of_all_excluded_views_usd": float(rq3_cost["cost_of_all_excluded_views_usd"]),
                "cost_of_excluded_ambiguous_views_usd": float(rq3_cost["cost_of_excluded_ambiguous_views_usd"]),
                "cost_of_excluded_unmapped_views_usd": float(rq3_cost["cost_of_excluded_unmapped_views_usd"]),
                "marginal_cost_vs_baseline_usd": float(rq3_cost["marginal_cost_vs_baseline_usd"]),
            },
            "failures": {
                "terminal_incomplete_count": term_incomp_count,
                "terminal_incomplete_rate": term_incomp_rate,
                "terminal_incomplete_denominator": 1280,
                "mapped_scorable_terminal_failures_count": 0,
                "mapped_scorable_attribution_errors_count": error_count,
                "invalid_syntax_count": 0,
                "invalid_id_count": 0,
                "parse_failure_count": 0,
            }
        }

        if cond == "rag_k1":
            rq3_obj["financial_cost_usd"]["k1_reconciliation_formula"] = (
                "token_usage_estimated_cost_usd ($0.75784210) - observed_cache_credit_usd ($0.00035420) + "
                "missing_usage_attempt_retained_charge_usd ($0.53974560) = ledger_settled_cost_usd ($1.29723350)"
            )

        conditions_bundle[cond] = {
            "condition": cond,
            "retrieval_k": k_val,
            "cohort": cond_cohort,
            "rq1_attribution": rq1_obj,
            "rq2_retrieval_and_error": rq2_obj,
            "rq3_resources_and_cost": rq3_obj,
        }

    # Step 8: Metric Definitions & Metadata Dictionary
    metric_definitions = {
        "any_match_semantics": {
            "name": "ANY_MATCH Ground Truth Union Evaluation",
            "decision_ref": "Decision D2",
            "description": (
                "A prediction is scored as correct if the predicted ATT&CK technique ID matches "
                "ANY of the ground truth technique IDs associated with the sample view. "
                "For multi-label views, full recall across all ground truth labels is measured separately as macro_recall."
            ),
        },
        "macro_f1": {
            "name": "Macro-Averaged F1 Across Frozen Benchmark Universe",
            "decision_ref": "Decisions D2b, D2c",
            "universe_denominator": COHORT_MACRO_UNIVERSE,
            "supported_classes": COHORT_SUPPORTED_CLASSES,
            "unsupported_classes": COHORT_UNSUPPORTED_CLASSES,
            "description": (
                "Unweighted average of per-class F1 across all 474 frozen benchmark classes. "
                "Classes with zero support and zero predictions contribute 0 to the numerator and are retained in the denominator."
            ),
        },
        "error_rate": {
            "name": "Attribution Error Rate",
            "formula": "(scorable_sample_count - correct_count) / scorable_sample_count",
            "denominator": COHORT_MAPPED_VIEWS,
            "description": "Proportion of scorable mapped views failing technique attribution.",
        },
        "bootstrap_parameters": {
            "samples": 1000,
            "seed": 42,
            "alpha": 0.05,
            "cluster_unit": "pair_id",
            "cluster_count": COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS,
            "method": "percentile_cluster_bootstrap",
            "description": "Nonparametric percentile bootstrap clustered on telemetry pairs across 440 test clusters.",
        },
        "cost_per_query_amortized": {
            "name": "Amortized Cost per Scorable Query",
            "formula": "condition_settled_cost_usd / 718",
            "description": (
                "Whole-condition settled expenditure divided by 718 scorable queries, "
                "amortizing total resource cost (including excluded views and retries) across scorable attribution tasks."
            ),
        },
        "mapped_scorable_attribution_errors": {
            "name": "Mapped Scorable Attribution Errors",
            "description": (
                "Classification errors among scorable mapped views (718 - correct_count), ranging from 147 (rag_k10) to 165 (rag_k1). "
                "Strictly distinguished from terminal system execution failures (which are 0 among mapped views)."
            ),
        },
        "incomplete_taxonomy": {
            "total_terminal_incomplete": 13,
            "scorable_mapped_terminal_incomplete": 0,
            "unmapped_terminal_incomplete": 11,
            "ambiguous_terminal_incomplete": 2,
            "distinct_views_count": 11,
            "conditions_breakdown": {
                "no_rag": 0,
                "rag_k1": 0,
                "rag_k3": 6,
                "rag_k5": 3,
                "rag_k10": 4,
            },
            "description": (
                "13 terminal INCOMPLETE outcomes across 11 distinct view IDs occurring exclusively in unmapped and ambiguous cohorts "
                "due to output length exhaustion on long contexts. All metered tokens settled cleanly without experiment disruption."
            ),
        },
    }

    # Step 9: Campaign-wide Failure Taxonomy
    failure_taxonomy = {
        "campaign_total_logical_requests": 6400,
        "campaign_total_physical_attempts": 6401,
        "transport_network_failures_count": 1,
        "transport_network_failure_details": cache_telemetry["transport_failure"],
        "retry_success_details": cache_telemetry["retry_success"],
        "terminal_incomplete_count": 13,
        "terminal_incomplete_rate": 13 / 6400.0,
        "terminal_incomplete_by_condition": {
            "no_rag": 0,
            "rag_k1": 0,
            "rag_k3": 6,
            "rag_k5": 3,
            "rag_k10": 4,
        },
        "mapped_scorable_terminal_incomplete_count": 0,
        "completed_records_count": 6387,
        "valid_json_outputs_count": 6387,
        "invalid_syntax_count": 0,
        "invalid_attack_id_count": 0,
        "retired_attack_id_observation_count": 245,
        "retired_attack_id_policy": "ALLOWED_HISTORICAL_PER_DECISION_D2G",
    }

    # Step 10: Assemble Complete Bundle
    bundle = {
        "schema_version": "2.0.0",
        "bundle_type": "canonical-metric-bundle-v2",
        "fixture_only": False,
        "execution_mode": "live",
        "dataset_split": "test",
        "experiment_id": "synthetic-paired-test-1",
        "run_id": "live-66b94b1676bf46a9",
        "study_id": "rag2attack-study-wide",
        "protocol_version": "experiment-protocol-v1.1",
        "protocol_sha256": EXPECTED_PROTOCOL_SHA256,
        "pricing_contract_sha256": EXPECTED_PRICING_CONTRACT_SHA256,
        "core_code_manifest_sha256": EXPECTED_CORE_MANIFEST_SHA256,
        "execution_git_sha": EXECUTION_GIT_SHA,
        "native_evaluation_git_sha": NATIVE_EVALUATION_GIT_SHA,
        "rq_v2_integrated_git_sha": RQ_V2_INTEGRATED_GIT_SHA,
        "candidate_base_git_sha": CANDIDATE_BASE_GIT_SHA,
        "public_package_manifest_sha256": EXPECTED_PUBLIC_MANIFEST_SHA256,
        "evaluator_analysis_source_file": "scripts/analysis/evaluate_rqs.py",
        "evaluator_analysis_source_sha256": EXPECTED_ANALYSIS_SOURCE_SHA256,
        "analysis_timestamp_utc": source_analysis_timestamp,
        "bundle_build_timestamp_utc": build_timestamp_utc or RECORDED_BUNDLE_CREATION_TIMESTAMP_UTC,
        "terminal_seal": {
            "path": "reports/evidence/canonical_run_seal_v1.json",
            "sha256": EXPECTED_TERMINAL_SEAL_SHA256,
            "terminal_proof_sha256": EXPECTED_TERMINAL_PROOF_SHA256,
        },
        "supplementary_source_lineage": {
            "historical_analysis_source_sha256": HISTORICAL_ANALYSIS_SOURCE_SHA256,
            "historical_evaluation_commit_sha": NATIVE_EVALUATION_GIT_SHA,
            "historical_authorizing_packet_public_sha256": AUTHORIZING_PACKET_PUBLIC_SHA256,
            "historical_authorizing_packet_original_sha256": AUTHORIZING_PACKET_ORIGINAL_SHA256,
            "superseding_authorizing_packet_sha256": SUPERSEDING_AUTHORIZING_PACKET_SHA256,
            "root_integrated_source_audit_sha256": ROOT_INTEGRATED_SOURCE_AUDIT_SHA256,
            "root_private_replay_acceptance_sha256": ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256,
            "lineage_note": (
                "Preserves historical b988/d515/c48 development bindings while recording authorized "
                "superseding c34/f85/264ed31 S2_RQ_V2 evaluation lineage."
            ),
        },
        "p95_policy": {
            "status": P95_STATUS_POLICY,
            "rule": "P95 latency is withheld from consumer display pending formal authority approval.",
        },
        "metric_definitions": metric_definitions,
        "cohort_breakdown": {
            "total_views": COHORT_TOTAL_VIEWS,
            "total_pairs": COHORT_TOTAL_PAIRS,
            "mapped_scorable_views": COHORT_MAPPED_VIEWS,
            "ambiguous_excluded_views": COHORT_AMBIGUOUS_VIEWS,
            "unmapped_excluded_views": COHORT_UNMAPPED_VIEWS,
            "single_gt_mapped_views": COHORT_SINGLE_GT_VIEWS,
            "multi_gt_mapped_views": COHORT_MULTI_GT_VIEWS,
            "total_gt_support_instances": COHORT_TOTAL_GT_SUPPORT_INSTANCES,
            "eligible_bootstrap_clusters": COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS,
            "macro_universe_classes": COHORT_MACRO_UNIVERSE,
            "supported_classes": COHORT_SUPPORTED_CLASSES,
            "unsupported_classes": COHORT_UNSUPPORTED_CLASSES,
        },
        "conditions": conditions_bundle,
        "whole_study_financial_accounting": financial_accounting,
        "failure_taxonomy": failure_taxonomy,
        "overall_summary": {
            "overall_accuracy_end_to_end": float(overall_metrics["accuracy_end_to_end"]),
            "overall_accuracy_valid_outputs": float(overall_metrics["accuracy_valid_outputs"]),
            "overall_macro_f1": float(overall_metrics["macro_f1"]),
            "total_scorable_mapped_samples_across_conditions": int(overall_metrics["scorable_sample_count"]),
            "total_completed_records": int(overall_metrics["completed_record_count"]),
            "total_logical_samples": int(overall_metrics["logical_sample_count"]),
            "total_provider_failures": int(overall_metrics["provider_failure_count"]),
            "total_retired_id_observations": int(overall_metrics["retired_id_observation_count"]),
        },
        "source_file_digests": manifest.get("source_file_digests", {}),
        "output_file_digests": manifest.get("output_file_digests", {}),
    }

    # Verify complete finite bundle tree
    check_finite(bundle, "bundle_root")

    # Step 11: Deterministic binary byte write to disk
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        bundle_json_str = json.dumps(bundle, indent=2, sort_keys=True, allow_nan=False)
        bundle_bytes = bundle_json_str.encode("utf-8") + b"\n"

        with open(output_path, "wb") as f:
            f.write(bundle_bytes)

        # Read back actual bytes from disk to guarantee hash matches physical storage
        actual_written_bytes = output_path.read_bytes()
        if b"\r" in actual_written_bytes:
            raise ValueError("Deterministic byte assertion failed: CRLF found in output file")

        bundle_sha256 = hashlib.sha256(actual_written_bytes).hexdigest()
        sha_path = output_path.with_name(f"{output_path.name}.sha256")
        sidecar_bytes = f"{bundle_sha256}  {output_path.name}\n".encode("utf-8")
        with open(sha_path, "wb") as f:
            f.write(sidecar_bytes)

        print(f"Canonical metric bundle successfully written to: {output_path}")
        print(f"Bundle SHA256: {bundle_sha256}")

    return bundle


def generate_lineage_markdown(bundle: Dict[str, Any], output_md_path: Path) -> str:
    """
    Machine-generate reports/evidence/canonical_metric_bundle_v2_lineage.md
    directly from bundle dictionary to ensure 100% numerical and text consistency.
    """
    conds = bundle["conditions"]
    fin = bundle["whole_study_financial_accounting"]
    lineage = bundle["supplementary_source_lineage"]

    rows = []
    for c in CONDITIONS:
        rq1 = conds[c]["rq1_attribution"]
        acc_str = rq1["accuracy_display"]
        ci_str = f"[{rq1['accuracy_e2e_ci_95'][0] * 100:.2f}%, {rq1['accuracy_e2e_ci_95'][1] * 100:.2f}%]"
        macro_f1 = rq1["macro_f1_display"]
        if c == "no_rag":
            delta_str = "Baseline"
            delta_ci_str = "Baseline"
            mcnemar_p = "—"
            sig_str = "—"
        else:
            d_info = rq1["delta_vs_baseline"]
            delta_str = d_info["delta_accuracy_display_pp"]
            delta_ci = d_info["delta_accuracy_ci_95"]
            delta_ci_str = f"[{delta_ci[0] * 100.0:+.3f}, {delta_ci[1] * 100.0:+.3f}] pp"
            mcnemar_p = d_info["mcnemar_test"]["display_p_exact"]
            sig_str = "Có" if d_info["mcnemar_test"]["significant_at_05"] else "Không"

        name_display = "**No-RAG**" if c == "no_rag" else f"**RAG k={conds[c]['retrieval_k']}**"
        rows.append(
            f"| {name_display} | {rq1['correct_count']} / 718 | {acc_str} | {ci_str} | {macro_f1} | "
            f"{delta_str} | {delta_ci_str} | {mcnemar_p} | {sig_str} |"
        )
    rq1_table_md = "\n".join(rows)

    res_rows = []
    total_prompt = 0
    total_comp = 0
    total_tok = 0
    for c in CONDITIONS:
        rq3 = conds[c]["rq3_resources_and_cost"]
        name_display = "**No-RAG**" if c == "no_rag" else f"**RAG k={conds[c]['retrieval_k']}**"
        p_tok = rq3["tokens"]["prompt_tokens"]["sum"]
        c_tok = rq3["tokens"]["completion_tokens"]["sum"]
        t_tok = rq3["tokens"]["total_tokens"]["sum"]
        ca_tok = rq3["tokens"]["cached_tokens"]["sum"]
        cost_s = rq3["financial_cost_usd"]["ledger_settled_cost_usd"]
        total_prompt += p_tok
        total_comp += c_tok
        total_tok += t_tok

        res_rows.append(
            f"| {name_display} | {rq3['latency_ms']['mean']:,.2f} | {rq3['latency_ms']['median']:,.2f} | "
            f"*NOT REPORTED* | {p_tok:,} | {c_tok:,} | {t_tok:,} | {ca_tok:,} | ${cost_s} |"
        )
    res_table_md = "\n".join(res_rows)
    total_cost = fin["cumulative_settled_cost_usd"]

    md_content = f"""# BÁO CÁO DÒNG DÕI VÀ CHỨNG TỰ CANONICAL METRIC BUNDLE V2

**Mã Định Danh Phiên:** `cd393b52-6d99-4f23-878e-7afbb7e0ecf9`  
**Thời gian:** 2026-10-03T03:20:00+07:00  
**Tác giả:** Native Bundle Worker (Track B)  
**Vị trí Tệp:** `artifacts/results/canonical_metric_bundle_v2.json`  

---

## 1. TỔNG QUAN VÀ MỤC TIÊU BẢO MẬT

Tệp `canonical_metric_bundle_v2.json` đóng vai trò là adapter dữ liệu cấu trúc chuẩn mực duy nhất (Single Source of Truth) kết nối kết quả đánh giá khoa học và sổ cái tài chính từ chiến dịch chạy thực nghiệm 6.400 requests tới các bên tiêu thụ báo cáo (Publication Figures, Tables, Markdown Reports, Slides).

Bundle v2 tuân thủ các nguyên tắc bất biến:
1. **Zero Provider API Calls:** Hoàn toàn ngoại tuyến, không gửi bất kỳ request mạng nào.
2. **Fail-Closed Verification:** Tự động đối chiếu và xác thực toàn bộ mã băm SHA-256 của các tệp đầu vào đối với `canonical_bundle_manifest.json` và `canonical_run_seal_v1.json`.
3. **Phân định Hai Mẫu Số Độc Lập:** Phân biệt rạch ròi mẫu số đánh giá gán nhãn khoa học ($N=718$ mapped views) và mẫu số đo lường hệ thống/tài nguyên ($N=1.280$ queries/điều kiện, $6.400$ toàn chiến dịch).
4. **Bảo Toàn Tiền Tệ Tuyệt Đối:** Xác thực bằng số học `Decimal` bảo toàn tiền tệ: Settled ${SETTLED_USD} + Pilot Hold ${PILOT_HOLD_USD} = Accounted ${TOTAL_ACCOUNTED_USD}; Available ${AVAILABLE_BALANCE_USD} trong ngân sách trần ${BUDGET_CAP_USD}.
5. **Chính Sách Ẩn p95 Latency:** Khai báo rõ `"{P95_STATUS_POLICY}"`; trường giá trị số được đặt là `null` để ngăn tiêu thụ trái phép khi chưa có chứng cứ phê duyệt.

---

## 2. BẢNG DÒNG DÕI NGUỒN GỐC VÀ MÃ BĂM (PROVENANCE & LINEAGE)

| Thành Phần | Giá Trị / Đường Dẫn | SHA-256 / Commit | Ghi Chú |
| :--- | :--- | :--- | :--- |
| **Execution Git Commit** | `HEAD` tại lúc chạy thực nghiệm | `{EXECUTION_GIT_SHA}` | Frozen Core Git Commit |
| **Native Evaluation Commit** | `HEAD` tại lúc chạy native evaluator | `{NATIVE_EVALUATION_GIT_SHA}` | Chứa analysis source `{HISTORICAL_ANALYSIS_SOURCE_SHA256}` |
| **RQv2 Integrated Commit** | `HEAD` tích hợp phân tích RQv2 | `{RQ_V2_INTEGRATED_GIT_SHA}` | Chứa analysis source `{EXPECTED_ANALYSIS_SOURCE_SHA256}` |
| **Candidate Base Commit** | `HEAD` nghiệm thu Track A | `{CANDIDATE_BASE_GIT_SHA}` | Base cho các nhánh finalization |
| **Core Code Manifest** | `config/canonical_experiment_lock_v1.json` | `{EXPECTED_CORE_MANIFEST_SHA256}` | Khóa bất biến 53 tệp cốt lõi |
| **Protocol Canonical** | `config/experiment_protocol_v1.json` | `{EXPECTED_PROTOCOL_SHA256}` | Giao thức thực nghiệm v1.1 |
| **Pricing Contract** | `config/pricing_v1.json` | `{EXPECTED_PRICING_CONTRACT_SHA256}` | Hợp đồng biểu giá |
| **Public Manifest** | `canonical_bundle_manifest.json` | `{EXPECTED_PUBLIC_MANIFEST_SHA256}` | Manifest của gói công khai v3 |
| **Canonical Run Seal** | `reports/evidence/canonical_run_seal_v1.json` | `{EXPECTED_TERMINAL_SEAL_SHA256}` | Chứng thư niêm phong vận hành |
| **Terminal Proof** | `artifacts/orchestration/...proof.json` | `{EXPECTED_TERMINAL_PROOF_SHA256}` | Bằng chứng tiến trình hoàn tất 6.400 records |
| **Analysis Source Code**| `scripts/analysis/evaluate_rqs.py` | `{EXPECTED_ANALYSIS_SOURCE_SHA256}` | Mã phân tích S2_RQ_V2 chính thức |
| **Superseding Authorizing Packet** | `s2_rq_v2_execute_exact_20261002.md` | `{SUPERSEDING_AUTHORIZING_PACKET_SHA256}` | Chỉ đạo phân tích S2_RQ_V2 được duyệt |
| **Source Audit Evidence** | `root_integrated_264ed31_source_audit.json` | `{ROOT_INTEGRATED_SOURCE_AUDIT_SHA256}` | Bằng chứng kiểm toán nguồn tích hợp 264ed31 |
| **Private Replay Acceptance** | `root_private_replay_acceptance_20261002.json` | `{ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256}` | Bằng chứng nghiệm thu replay riêng tư 17.894 trường |
| **Historical Public Packet**| `provenance/s2_evaluation_execute_public.md` | `{AUTHORIZING_PACKET_PUBLIC_SHA256}` | Gói chỉ đạo ban đầu (gắn với commit 208) |

---

## 3. THU NHẬP VÀ ĐỐI CHIẾU DỮ LIỆU TOKEN CACHE (RECEIPT JOIN)

Từ việc quét toàn bộ `inputs/request_journal.jsonl` và join với predictions:
- **Tổng số attempt receipts:** Đúng 6.401 receipts.
- **Quan sát thành công:** 6.400 quan sát.
- **Quan sát lỗi mạng:** 1 quan sát (`ordinal: 5387`, `view_d870d574`, điều kiện `rag_k1`, lỗi `InternalServerError`, `cached_tokens: null`).
- **Quan sát retry thành công:** 1 quan sát (`ordinal: 5388`, `view_d870d574`, điều kiện `rag_k1`, `cached_tokens: 1540`, `input_tokens: 1543`, `output_tokens: 452`).
- **Tổng token cache toàn bộ chiến dịch:** **1.540 tokens** (toàn bộ nằm ở điều kiện `rag_k1`).
- **Trung bình token cache:**
  - Điều kiện `rag_k1`: $1.540 / 1.280 = 1,203125$ tokens/query.
  - Các điều kiện khác (`no_rag`, `rag_k3`, `rag_k5`, `rag_k10`): $0,0$ tokens/query.
- **Quy tắc tính tổng token:**
  $$\\text{{Total Tokens}} = \\text{{Prompt Tokens}} + \\text{{Completion Tokens}}$$
  Token cache là tập con của Prompt Tokens và **tuyệt đối không được cộng dồn hai lần** vào tổng token.

---

## 4. TỔNG HỢP CÁC KẾT QUẢ SỐ HỌC ĐÃ KIỂM CHỨNG (MACHINE GENERATED)

### RQ1: Đánh Giá Phân Loại Kỹ Thuật (Attribution Accuracy & Macro-F1)
- **Mẫu số đánh giá:** $N = 718$ mapped views (Single-GT: 678, Multi-GT: 40).
- **Macro-F1 Universe:** 474 kỹ thuật đông kết (8 supported, 466 unsupported).

| Điều Kiện | Đúng / Tổng | Độ Chính Xác (%) | 95% Bootstrap CI (%) | Macro-F1 | Delta vs No-RAG (pp) | 95% CI Delta (pp) | McNemar Exact $p$ | Ý Nghĩa Thống Kê ($p < 0.05$) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{rq1_table_md}

### RQ2: Tách Rời Lỗi Truy Xuất & Sinh Văn Bản (k=10)
- **Truy xuất:** Hit = 321 / 718 (44.71%), Miss = 397 / 718 (55.29%), Macro Recall = 0.4280.
- **Độ chính xác có điều kiện:**
  - $P(\\text{{Đúng}} \\mid \\text{{Truy xuất thành công}}) = 293 / 321 = 91.28\\%$
  - $P(\\text{{Đúng}} \\mid \\text{{Truy xuất thất bại}}) = 278 / 397 = 70.03\\%$
- **Trục lỗi độc lập (Decision D2i):**
  - Lỗi phân loại sai: 147 mẫu.
  - Giao thoa Miss $\\cap$ Phân loại sai: 119 mẫu ($119 / 147 = 80.95\\%$).
  - Truy xuất No-RAG: Khai báo `null` với `applicable: false` (giữ vết 0 trong `raw_evaluator_trace`).

### RQ3: Tài Nguyên, Độ Trễ & Chi Phí (Mẫu số $N=1.280$ queries/điều kiện)

| Điều Kiện | Mean Latency (ms) | Median Latency (ms) | p95 Latency | Prompt Tokens | Completion Tokens | Total Tokens | Cached Tokens | Chi Phí Settled Ledger |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{res_table_md}
| **Tổng Toàn Bộ**| — | — | — | **{total_prompt:,}** | **{total_comp:,}** | **{total_tok:,}** | **1.540** | **${total_cost}** |

*Công thức đối soát tài chính `rag_k1`:*  
Token usage estimate $0.75784210 - Observed cache credit $0.00035420 + Missing-usage retained charge $0.53974560 = Settled ledger $1.29723350.  
(Trong đó chi phí bảo lưu missing usage là số tiền giữ lại thận trọng theo quy tắc bảo vệ ngân sách API khi thiếu thông tin sử dụng ở lần thử 0, không phải là hóa đơn thương mại hay phạt hợp đồng).

---

## 5. BẢO ĐẢM TÍNH TOÀN VẸN VÀ KHÔNG GÂY THOÁT RA NGOÀI (OFFLINE GUARD)

Toàn bộ quá trình tạo và xác thực Canonical Metric Bundle v2 được thực thi hoàn toàn trong môi trường tự cách ly:
- Không tạo kết nối HTTP/HTTPS ra ngoài (`attempted_egress = 0`).
- Ghi tệp nhị phân bảo đảm dòng kết thúc LF đồng nhất cross-platform.
- Tự động đối chiếu mã băm thực tế trên đĩa với tệp sidecar `.sha256`.
"""
    output_md_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md_path, "wb") as f:
        f.write(md_content.encode("utf-8"))
    return md_content


def verify_canonical_metric_bundle_file(
    bundle_path: Path,
    expected_sha256: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verify existing canonical_metric_bundle_v2.json file against sidecar checksum,
    strict schema, typed finite invariants, and non-CRLF binary encoding.
    """
    if not bundle_path.is_file():
        raise FileNotFoundError(f"Bundle file not found: {bundle_path}")

    actual_bytes = bundle_path.read_bytes()
    if b"\r" in actual_bytes:
        raise ValueError("Bundle file contains CRLF bytes; must be deterministic LF")

    actual_sha = hashlib.sha256(actual_bytes).hexdigest()

    sidecar_path = bundle_path.with_name(f"{bundle_path.name}.sha256")
    if not sidecar_path.is_file():
        raise FileNotFoundError(f"Missing sidecar checksum file: {sidecar_path}")

    sidecar_text = sidecar_path.read_bytes().decode("utf-8").strip()
    sidecar_sha = sidecar_text.split()[0]
    if actual_sha != sidecar_sha:
        raise ValueError(
            f"Bundle checksum mismatch with sidecar!\n"
            f"  Actual bytes: {actual_sha}\n"
            f"  Sidecar:      {sidecar_sha}"
        )

    if expected_sha256 is not None and actual_sha != expected_sha256:
        raise ValueError(
            f"Bundle checksum mismatch with expected SHA!\n"
            f"  Actual bytes: {actual_sha}\n"
            f"  Expected:     {expected_sha256}"
        )

    bundle_data = json.loads(actual_bytes.decode("utf-8"), parse_constant=_reject_nonfinite)
    check_finite(bundle_data, "bundle_root")

    # Invariants check: top-level metadata & execution invariants
    if bundle_data.get("schema_version") != "2.0.0":
        raise ValueError(f"Invalid schema_version: {bundle_data.get('schema_version')}")
    if bundle_data.get("bundle_type") != "canonical-metric-bundle-v2":
        raise ValueError(f"Invalid bundle_type: {bundle_data.get('bundle_type')}")
    if bundle_data.get("fixture_only", False) is not False:
        raise ValueError("fixture_only must be False")
    if bundle_data.get("execution_mode") != "live":
        raise ValueError("execution_mode must be live")
    if bundle_data.get("protocol_version") != "experiment-protocol-v1.1":
        raise ValueError(f"Invalid protocol_version: {bundle_data.get('protocol_version')}")

    # 1. Authoritative 11 Source Pins & Provenance Bindings
    if bundle_data.get("protocol_sha256") != EXPECTED_PROTOCOL_SHA256:
        raise ValueError("protocol_sha256 mismatch")
    if bundle_data.get("pricing_contract_sha256") != EXPECTED_PRICING_CONTRACT_SHA256:
        raise ValueError("pricing_contract_sha256 mismatch")
    if bundle_data.get("core_code_manifest_sha256") != EXPECTED_CORE_MANIFEST_SHA256:
        raise ValueError("core_code_manifest_sha256 mismatch")
    if bundle_data.get("execution_git_sha") != EXECUTION_GIT_SHA:
        raise ValueError("execution_git_sha mismatch")
    if bundle_data.get("native_evaluation_git_sha") != NATIVE_EVALUATION_GIT_SHA:
        raise ValueError("native_evaluation_git_sha mismatch")
    if bundle_data.get("rq_v2_integrated_git_sha") != RQ_V2_INTEGRATED_GIT_SHA:
        raise ValueError("rq_v2_integrated_git_sha mismatch")
    if bundle_data.get("candidate_base_git_sha") != CANDIDATE_BASE_GIT_SHA:
        raise ValueError("candidate_base_git_sha mismatch")
    if bundle_data.get("public_package_manifest_sha256") != EXPECTED_PUBLIC_MANIFEST_SHA256:
        raise ValueError("public_package_manifest_sha256 mismatch")
    if bundle_data.get("evaluator_analysis_source_sha256") != EXPECTED_ANALYSIS_SOURCE_SHA256:
        raise ValueError("evaluator_analysis_source_sha256 mismatch")

    seal_info = bundle_data.get("terminal_seal", {})
    if seal_info.get("sha256") != EXPECTED_TERMINAL_SEAL_SHA256:
        raise ValueError("terminal_seal.sha256 mismatch")
    if seal_info.get("terminal_proof_sha256") != EXPECTED_TERMINAL_PROOF_SHA256:
        raise ValueError("terminal_seal.terminal_proof_sha256 mismatch")

    supp = bundle_data.get("supplementary_source_lineage", {})
    if supp.get("historical_analysis_source_sha256") != HISTORICAL_ANALYSIS_SOURCE_SHA256:
        raise ValueError("historical_analysis_source_sha256 mismatch")
    if supp.get("superseding_authorizing_packet_sha256") != SUPERSEDING_AUTHORIZING_PACKET_SHA256:
        raise ValueError("superseding_authorizing_packet_sha256 mismatch")
    if supp.get("root_integrated_source_audit_sha256") != ROOT_INTEGRATED_SOURCE_AUDIT_SHA256:
        raise ValueError("root_integrated_source_audit_sha256 mismatch")
    if supp.get("root_private_replay_acceptance_sha256") != ROOT_PRIVATE_REPLAY_ACCEPTANCE_SHA256:
        raise ValueError("root_private_replay_acceptance_sha256 mismatch")

    # 1b. Verify all source file digests
    exp_source_digests = {
        ".study_anchor.json": "6a15639c213782a6ef7863a960b064d604185297b121ab41197a057774d23097",
        "manifest.json": "66b658cfa9dd42e131ec567bbe043b8bc87ac6e92aeaa5e8f6661b0195e486e5",
        "no_rag_predictions.jsonl": "70034c5e3c417fc4a28c357d00d6a046751175ed03e7815645fa09e0411e228a",
        "rag_k10_predictions.jsonl": "40cd9d2b19c691ed8bcb97ff5dfbebd378857346e9a06b00a9ab54e51fd9a122",
        "rag_k1_predictions.jsonl": "745cb883a90b4d1bac7c76c4007b143893834530a843e153fc24277aae5da7ac",
        "rag_k3_predictions.jsonl": "29f215d74a3139df53036c642c8a14762bec4542d04685125cf28d024571b006",
        "rag_k5_predictions.jsonl": "896d900d10e25af748e00235c33cace84511c450bf7cfb0da2b4d1a658124178",
        "request_journal.jsonl": "f36e0f3099ef704e6ed5e0bc0097affbe98932e1620563a6db22e631ae114f31",
        "run_summary.json": "67df38e336b4250b5a5c044b754ab02e8cc1826b8569f76d9bdf265ae4f84c2a",
        "study_ledger.json": "21e4c49b1f19bba5310bc0e9897d828b16ab27420c1d25b14b9f3e727dce94d8",
    }
    actual_source_digests = bundle_data.get("source_file_digests", {})
    for sf_name, exp_sf_sha in exp_source_digests.items():
        act_sf_sha = actual_source_digests.get(sf_name)
        if act_sf_sha != exp_sf_sha:
            raise ValueError(
                f"source_file_digests.{sf_name} mismatch: actual={act_sf_sha!r} != expected={exp_sf_sha!r}"
            )

    # 2. Authoritative Source Timestamp Check (exact match, no startswith)
    source_ts = bundle_data.get("analysis_timestamp_utc")
    if source_ts != "2026-10-02T04:32:51.956332+00:00":
        raise ValueError(
            f"analysis_timestamp_utc must match exact authoritative timestamp '2026-10-02T04:32:51.956332+00:00', got: {source_ts!r}"
        )

    # 3. 11 Cohort Breakdown & Denominators Invariants
    cohort = bundle_data.get("cohort_breakdown", {})
    if cohort.get("total_views") != COHORT_TOTAL_VIEWS:
        raise ValueError("cohort total_views mismatch")
    if cohort.get("total_pairs") != COHORT_TOTAL_PAIRS:
        raise ValueError("cohort total_pairs mismatch")
    if cohort.get("mapped_scorable_views") != COHORT_MAPPED_VIEWS:
        raise ValueError("cohort mapped_scorable_views mismatch")
    if cohort.get("ambiguous_excluded_views") != COHORT_AMBIGUOUS_VIEWS:
        raise ValueError("cohort ambiguous_excluded_views mismatch")
    if cohort.get("unmapped_excluded_views") != COHORT_UNMAPPED_VIEWS:
        raise ValueError("cohort unmapped_excluded_views mismatch")
    if cohort.get("single_gt_mapped_views") != COHORT_SINGLE_GT_VIEWS:
        raise ValueError("cohort single_gt_mapped_views mismatch")
    if cohort.get("multi_gt_mapped_views") != COHORT_MULTI_GT_VIEWS:
        raise ValueError("cohort multi_gt_mapped_views mismatch")
    if cohort.get("total_gt_support_instances") != COHORT_TOTAL_GT_SUPPORT_INSTANCES:
        raise ValueError("cohort total_gt_support_instances mismatch")
    if cohort.get("eligible_bootstrap_clusters") != COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS:
        raise ValueError("cohort eligible_bootstrap_clusters mismatch")
    if cohort.get("macro_universe_classes") != COHORT_MACRO_UNIVERSE:
        raise ValueError("cohort macro_universe_classes mismatch")
    if cohort.get("supported_classes") != COHORT_SUPPORTED_CLASSES:
        raise ValueError("cohort supported_classes mismatch")
    if cohort.get("unsupported_classes") != COHORT_UNSUPPORTED_CLASSES:
        raise ValueError("cohort unsupported_classes mismatch")

    if (
        cohort["mapped_scorable_views"]
        + cohort["ambiguous_excluded_views"]
        + cohort["unmapped_excluded_views"]
        != COHORT_TOTAL_VIEWS
    ):
        raise ValueError("Cohort partition conservation breached")
    if (
        cohort["single_gt_mapped_views"] + cohort["multi_gt_mapped_views"]
        != COHORT_MAPPED_VIEWS
    ):
        raise ValueError("Mapped cohort complexity conservation breached")
    if (
        cohort["supported_classes"] + cohort["unsupported_classes"]
        != COHORT_MACRO_UNIVERSE
    ):
        raise ValueError("Class universe conservation breached")

    # 4. p95 Latency Suppression Policy Enforcement
    p95_pol = bundle_data.get("p95_policy", {})
    if p95_pol.get("status") != P95_STATUS_POLICY:
        raise ValueError(f"Top-level p95_policy status mismatch: {p95_pol.get('status')}")

    # 5. Conditions Check & Authoritative Metric/Cost Oracle
    conds = bundle_data.get("conditions", {})
    if set(conds.keys()) != set(CONDITIONS):
        raise ValueError(f"Missing conditions in bundle: {set(conds.keys())}")

    expected_condition_oracle = {
        "no_rag": {
            "retrieval_k": 0,
            "correct_count": 560,
            "error_count": 158,
            "accuracy_end_to_end": 0.7799442896935933,
            "accuracy_e2e_ci_95": [0.7464432837582625, 0.8088098670586635],
            "macro_f1": 0.012608366023907785,
            "cost_usd": "0.46714395",
            "cached_tokens": 0,
            "is_baseline": True,
            "p_exact_display": "—",
            "retrieval": {
                "retrieval_hit_count": None,
                "retrieval_miss_count": None,
                "retrieval_hit_rate": None,
                "macro_recall": None,
            },
            "tokens": {
                "prompt_tokens": {"sum": 863139, "mean": 674.32734375},
                "completion_tokens": {"sum": 209466, "mean": 163.6453125},
                "total_tokens": {"sum": 1072605, "mean": 837.97265625},
                "cached_tokens": {"sum": 0, "mean": 0.0},
            },
            "latency_ms": {
                "mean": 2904.4541815625507,
                "median": 2302.815000002738,
            },
            "delta": None,
        },
        "rag_k1": {
            "retrieval_k": 1,
            "correct_count": 553,
            "error_count": 165,
            "accuracy_end_to_end": 0.7701949860724234,
            "accuracy_e2e_ci_95": [0.7350325884543762, 0.8016815680358997],
            "macro_f1": 0.012667935610765985,
            "cost_usd": "1.29723350",
            "cached_tokens": 1540,
            "is_baseline": False,
            "p_exact_display": "0.435",
            "retrieval": {
                "retrieval_hit_count": 27,
                "retrieval_miss_count": 691,
                "retrieval_hit_rate": 0.037604456824512536,
                "macro_recall": 0.02948003714020427,
            },
            "tokens": {
                "prompt_tokens": {"sum": 1595554, "mean": 1246.5265625},
                "completion_tokens": {"sum": 299128, "mean": 233.69375},
                "total_tokens": {"sum": 1894682, "mean": 1480.2203125},
                "cached_tokens": {"sum": 1540, "mean": 1.203125},
            },
            "latency_ms": {
                "mean": 3514.2666282031087,
                "median": 2617.13934999716,
            },
            "delta": {
                "delta_ci": [-0.0318592786225868, 0.01124077046548959],
                "p_value_exact": 0.4349928051221534,
                "p_value_asymptotic": 0.43472400072864303,
            },
        },
        "rag_k3": {
            "retrieval_k": 3,
            "correct_count": 564,
            "error_count": 154,
            "accuracy_end_to_end": 0.7855153203342619,
            "accuracy_e2e_ci_95": [0.7499912587412587, 0.8174190557416043],
            "macro_f1": 0.013642695462066637,
            "cost_usd": "1.17888000",
            "cached_tokens": 0,
            "is_baseline": False,
            "p_exact_display": "0.777",
            "retrieval": {
                "retrieval_hit_count": 118,
                "retrieval_miss_count": 600,
                "retrieval_hit_rate": 0.16434540389972144,
                "macro_recall": 0.15482822655524606,
            },
            "tokens": {
                "prompt_tokens": {"sum": 2780640, "mean": 2172.375},
                "completion_tokens": {"sum": 403100, "mean": 314.921875},
                "total_tokens": {"sum": 3183740, "mean": 2487.296875},
                "cached_tokens": {"sum": 0, "mean": 0.0},
            },
            "latency_ms": {
                "mean": 4215.878584452662,
                "median": 2743.170950008789,
            },
            "delta": {
                "delta_ci": [-0.02786003664534873, 0.039335604430632005],
                "p_value_exact": 0.7769647513696725,
                "p_value_asymptotic": 0.776814004155482,
            },
        },
        "rag_k5": {
            "retrieval_k": 5,
            "correct_count": 566,
            "error_count": 152,
            "accuracy_end_to_end": 0.7883008356545961,
            "accuracy_e2e_ci_95": [0.7506840229889549, 0.8234503042596348],
            "macro_f1": 0.01389077974323129,
            "cost_usd": "1.48311775",
            "cached_tokens": 0,
            "is_baseline": False,
            "p_exact_display": "0.677",
            "retrieval": {
                "retrieval_hit_count": 173,
                "retrieval_miss_count": 545,
                "retrieval_hit_rate": 0.24094707520891365,
                "macro_recall": 0.22957288765088205,
            },
            "tokens": {
                "prompt_tokens": {"sum": 3917047, "mean": 3060.19296875},
                "completion_tokens": {"sum": 419880, "mean": 328.03125},
                "total_tokens": {"sum": 4336927, "mean": 3388.22421875},
                "cached_tokens": {"sum": 0, "mean": 0.0},
            },
            "latency_ms": {
                "mean": 4327.256228515944,
                "median": 2873.740850001923,
            },
            "delta": {
                "delta_ci": [-0.029336848263743918, 0.046026711624319164],
                "p_value_exact": 0.6770697943668329,
                "p_value_asymptotic": 0.6769222390213794,
            },
        },
        "rag_k10": {
            "retrieval_k": 10,
            "correct_count": 571,
            "error_count": 147,
            "accuracy_end_to_end": 0.7952646239554317,
            "accuracy_e2e_ci_95": [0.7581211364272121, 0.8284683107785503],
            "macro_f1": 0.014023799884737108,
            "cost_usd": "2.14938370",
            "cached_tokens": 0,
            "is_baseline": False,
            "p_exact_display": "0.422",
            "retrieval": {
                "retrieval_hit_count": 321,
                "retrieval_miss_count": 397,
                "retrieval_hit_rate": 0.44707520891364905,
                "macro_recall": 0.4280408542246983,
            },
            "tokens": {
                "prompt_tokens": {"sum": 6546274, "mean": 5114.2765625},
                "completion_tokens": {"sum": 427346, "mean": 333.8640625},
                "total_tokens": {"sum": 6973620, "mean": 5448.140625},
                "cached_tokens": {"sum": 0, "mean": 0.0},
            },
            "latency_ms": {
                "mean": 4370.711563358918,
                "median": 2667.00299999502,
            },
            "delta": {
                "delta_ci": [-0.023547341489689132, 0.05300045580982214],
                "p_value_exact": 0.4219388330129739,
                "p_value_asymptotic": 0.42184797545336294,
            },
        },
    }

    for c in CONDITIONS:
        c_data = conds[c]
        oracle = expected_condition_oracle[c]

        if c_data.get("retrieval_k") != oracle["retrieval_k"]:
            raise ValueError(f"retrieval_k mismatch for {c}: {c_data.get('retrieval_k')} != {oracle['retrieval_k']}")

        # Enforce p95 suppression policy per condition
        rq3 = c_data.get("rq3_resources_and_cost", {})
        lat = rq3.get("latency_ms", {})
        if lat.get("p95") is not None:
            raise ValueError(f"p95 suppression policy violated in {c}: p95 must be None, got {lat.get('p95')}")
        if lat.get("p95_status") != P95_STATUS_POLICY:
            raise ValueError(f"p95_status mismatch in {c}: {lat.get('p95_status')}")

        # Enforce RQ3 resources and observation denominator
        if rq3.get("observations_count") != 1280:
            raise ValueError(f"observations_count must be 1280 for {c}, got {rq3.get('observations_count')}")

        # Enforce exact financial settled cost and cached tokens
        cost_info = rq3.get("financial_cost_usd", {})
        if Decimal(str(cost_info.get("ledger_settled_cost_usd"))) != Decimal(oracle["cost_usd"]):
            raise ValueError(
                f"Settled cost mismatch for {c}: {cost_info.get('ledger_settled_cost_usd')} != {oracle['cost_usd']}"
            )
        cached_tok = rq3.get("tokens", {}).get("cached_tokens", {}).get("sum")
        if cached_tok != oracle["cached_tokens"]:
            raise ValueError(f"Cached tokens mismatch for {c}: {cached_tok} != {oracle['cached_tokens']}")

        # Enforce RQ1 attribution metrics
        rq1 = c_data.get("rq1_attribution", {})
        corr_cnt = rq1.get("correct_count")
        if isinstance(corr_cnt, bool) or not isinstance(corr_cnt, int):
            raise TypeError(f"correct_count must be strict int for {c}, got {type(corr_cnt).__name__}")
        if corr_cnt != oracle["correct_count"]:
            raise ValueError(f"correct_count mismatch for {c}: {corr_cnt} != {oracle['correct_count']}")
        if rq1.get("error_count") != oracle["error_count"]:
            raise ValueError(f"error_count mismatch for {c}: {rq1.get('error_count')} != {oracle['error_count']}")
        if rq1.get("scorable_sample_count") != COHORT_MAPPED_VIEWS:
            raise ValueError(f"scorable_sample_count mismatch for {c}: {rq1.get('scorable_sample_count')}")

        exp_acc = oracle["correct_count"] / float(COHORT_MAPPED_VIEWS)
        if abs(float(rq1.get("accuracy_end_to_end", 0.0)) - exp_acc) > 1e-6:
            raise ValueError(f"accuracy_end_to_end mismatch for {c}")

        # Validate macro_f1 and accuracy CI bounds
        act_macro = rq1.get("macro_f1")
        if not isinstance(act_macro, float) or abs(act_macro - oracle["macro_f1"]) > 1e-7:
            raise ValueError(
                f"conditions.{c}.rq1_attribution.macro_f1 mismatch: actual={act_macro!r} != expected={oracle['macro_f1']}"
            )
        act_ci = rq1.get("accuracy_e2e_ci_95")
        if (
            not isinstance(act_ci, list)
            or len(act_ci) != 2
            or abs(act_ci[0] - oracle["accuracy_e2e_ci_95"][0]) > 1e-7
            or abs(act_ci[1] - oracle["accuracy_e2e_ci_95"][1]) > 1e-7
        ):
            raise ValueError(
                f"conditions.{c}.rq1_attribution.accuracy_e2e_ci_95 mismatch: actual={act_ci!r} != expected={oracle['accuracy_e2e_ci_95']}"
            )

        # Validate RQ2 retrieval metrics
        ret_metrics = c_data.get("rq2_retrieval_and_error", {}).get("retrieval_metrics", {})
        exp_ret = oracle["retrieval"]
        for r_key in ("retrieval_hit_count", "retrieval_miss_count"):
            act_v = ret_metrics.get(r_key)
            exp_v = exp_ret[r_key]
            if act_v != exp_v:
                raise ValueError(
                    f"conditions.{c}.rq2_retrieval_and_error.retrieval_metrics.{r_key} mismatch: actual={act_v!r} != expected={exp_v!r}"
                )
        for r_key in ("retrieval_hit_rate", "macro_recall"):
            act_v = ret_metrics.get(r_key)
            exp_v = exp_ret[r_key]
            if exp_v is None:
                if act_v is not None:
                    raise ValueError(f"conditions.{c}.rq2_retrieval_and_error.retrieval_metrics.{r_key} must be None, got {act_v!r}")
            else:
                if not isinstance(act_v, float) or abs(act_v - exp_v) > 1e-7:
                    raise ValueError(
                        f"conditions.{c}.rq2_retrieval_and_error.retrieval_metrics.{r_key} mismatch: actual={act_v!r} != expected={exp_v!r}"
                    )

        # Validate baseline / delta
        if oracle["is_baseline"]:
            if rq1.get("is_baseline") is not True:
                raise ValueError("no_rag is_baseline must be True")
        else:
            if rq1.get("is_baseline") is not False:
                raise ValueError(f"{c} is_baseline must be False")
            delta = rq1.get("delta_vs_baseline", {})
            exp_delta = (oracle["correct_count"] - 560) / float(COHORT_MAPPED_VIEWS)
            if abs(float(delta.get("delta_accuracy_end_to_end", 0.0)) - exp_delta) > 1e-6:
                raise ValueError(f"delta_accuracy_end_to_end mismatch for {c}")
            mcnemar = delta.get("mcnemar_test", {})
            if mcnemar.get("significant_at_05") is not False:
                raise ValueError(f"significant_at_05 must be False for {c}")
            if mcnemar.get("significant_at_01") is not False:
                raise ValueError(f"significant_at_01 must be False for {c}")
            if mcnemar.get("display_p_exact") != oracle["p_exact_display"]:
                raise ValueError(
                    f"mcnemar display_p_exact mismatch for {c}: {mcnemar.get('display_p_exact')} != {oracle['p_exact_display']}"
                )
            # Validate exact numeric p-values and delta CI
            if oracle["delta"] is not None:
                act_p_exact = mcnemar.get("p_value_exact")
                exp_p_exact = oracle["delta"]["p_value_exact"]
                if not isinstance(act_p_exact, float) or abs(act_p_exact - exp_p_exact) > 1e-7:
                    raise ValueError(
                        f"conditions.{c}.rq1_attribution.delta_vs_baseline.mcnemar_test.p_value_exact mismatch: actual={act_p_exact!r} != expected={exp_p_exact}"
                    )
                act_d_ci = delta.get("delta_accuracy_ci_95")
                exp_d_ci = oracle["delta"]["delta_ci"]
                if (
                    not isinstance(act_d_ci, list)
                    or len(act_d_ci) != 2
                    or abs(act_d_ci[0] - exp_d_ci[0]) > 1e-7
                    or abs(act_d_ci[1] - exp_d_ci[1]) > 1e-7
                ):
                    raise ValueError(
                        f"conditions.{c}.rq1_attribution.delta_vs_baseline.delta_accuracy_ci_95 mismatch: actual={act_d_ci!r} != expected={exp_d_ci}"
                    )

        # Validate token stats (sums and means)
        tok_dict = rq3.get("tokens", {})
        for t_group in ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens"):
            grp = tok_dict.get(t_group, {})
            exp_grp = oracle["tokens"][t_group]
            act_sum = grp.get("sum")
            if isinstance(act_sum, bool) or not isinstance(act_sum, int) or act_sum != exp_grp["sum"]:
                raise ValueError(
                    f"conditions.{c}.rq3_resources_and_cost.tokens.{t_group}.sum mismatch: actual={act_sum!r} != expected={exp_grp['sum']}"
                )
            act_mean = grp.get("mean")
            if not isinstance(act_mean, (int, float)) or abs(float(act_mean) - exp_grp["mean"]) > 1e-7:
                raise ValueError(
                    f"conditions.{c}.rq3_resources_and_cost.tokens.{t_group}.mean mismatch: actual={act_mean!r} != expected={exp_grp['mean']}"
                )

        # Validate latency stats (mean and median)
        act_lat_median = lat.get("median")
        exp_lat_median = oracle["latency_ms"]["median"]
        if not isinstance(act_lat_median, float) or abs(act_lat_median - exp_lat_median) > 1e-7:
            raise ValueError(
                f"conditions.{c}.rq3_resources_and_cost.latency_ms.median mismatch: actual={act_lat_median!r} != expected={exp_lat_median}"
            )

    # 5b. Metric Definitions Consistency
    boot = bundle_data.get("metric_definitions", {}).get("bootstrap_parameters", {})
    if (
        boot.get("seed") != 42
        or boot.get("samples") != 1000
        or boot.get("cluster_count") != COHORT_ELIGIBLE_BOOTSTRAP_CLUSTERS
    ):
        raise ValueError("bootstrap_parameters mismatch in metric_definitions")

    # 6. Whole Study Financial Accounting & Money Conservation
    fin = bundle_data.get("whole_study_financial_accounting", {})
    cap = Decimal(str(fin.get("study_budget_cap_usd")))
    hold = Decimal(str(fin.get("prior_pilot_provisional_hold_usd")))
    settled = Decimal(str(fin.get("cumulative_settled_cost_usd")))
    accounted = Decimal(str(fin.get("total_accounted_expenditure_usd")))
    avail = Decimal(str(fin.get("uncommitted_available_balance_usd")))

    if cap != BUDGET_CAP_USD:
        raise ValueError(f"Financial cap mismatch: {cap} != {BUDGET_CAP_USD}")
    if hold != PILOT_HOLD_USD:
        raise ValueError(f"Pilot hold mismatch: {hold} != {PILOT_HOLD_USD}")
    if settled != SETTLED_USD:
        raise ValueError(f"Settled cost mismatch: {settled} != {SETTLED_USD}")
    if accounted != TOTAL_ACCOUNTED_USD:
        raise ValueError(f"Total accounted mismatch: {accounted} != {TOTAL_ACCOUNTED_USD}")
    if avail != AVAILABLE_BALANCE_USD:
        raise ValueError(f"Available balance mismatch: {avail} != {AVAILABLE_BALANCE_USD}")
    if settled + hold != accounted:
        raise ValueError(f"Money conservation breach: {settled} + {hold} != {accounted}")
    if accounted + avail != cap:
        raise ValueError(f"Money conservation breach: {accounted} + {avail} != {cap}")
    if fin.get("has_breach", True) is not False:
        raise ValueError("Financial has_breach is not False")

    # 7. Campaign Failure Taxonomy
    ft = bundle_data.get("failure_taxonomy", {})
    if ft.get("campaign_total_logical_requests") != 6400:
        raise ValueError("campaign_total_logical_requests mismatch")
    if ft.get("campaign_total_physical_attempts") != 6401:
        raise ValueError("campaign_total_physical_attempts mismatch")
    if ft.get("completed_records_count") != 6387:
        raise ValueError("completed_records_count mismatch")
    if ft.get("valid_json_outputs_count") != 6387:
        raise ValueError("valid_json_outputs_count mismatch")
    if ft.get("terminal_incomplete_count") != 13:
        raise ValueError("terminal_incomplete_count mismatch")
    if ft.get("transport_network_failures_count") != 1:
        raise ValueError("transport_network_failures_count mismatch")

    print(f"PASS: Canonical metric bundle verified successfully: {bundle_path}")
    print(f"Verified SHA256: {actual_sha}")
    return bundle_data


def resolve_default_public_package_dir() -> Path:
    env_dir = os.environ.get("RAG2ATTCK_PUBLIC_PACKAGE_DIR")
    if env_dir:
        return Path(env_dir)
    candidates = [
        Path("artifacts/public_package_staging/03_public_canonical_package"),
        Path.home() / ".codex" / "artifacts" / "rag2attck" / "final_handover_package_v3_20261002" / "03_public_canonical_package",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and validate Canonical Metric Bundle v2")
    parser.add_argument(
        "--public-package-dir",
        type=Path,
        default=resolve_default_public_package_dir(),
        help="Path to public canonical package v3 directory",
    )
    parser.add_argument(
        "--seal-path",
        type=Path,
        default=Path("reports/evidence/canonical_run_seal_v1.json"),
        help="Path to canonical run seal JSON",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        default=Path("artifacts/results/canonical_metric_bundle_v2.json"),
        help="Destination path for canonical_metric_bundle_v2.json",
    )
    parser.add_argument(
        "--lineage-output-path",
        type=Path,
        default=Path("reports/evidence/canonical_metric_bundle_v2_lineage.md"),
        help="Destination path for canonical_metric_bundle_v2_lineage.md",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Verify inputs without writing bundle file",
    )
    parser.add_argument(
        "--verify-bundle",
        type=Path,
        default=None,
        help="Verify existing bundle artifact and sidecar on disk",
    )
    parser.add_argument(
        "--expected-bundle-sha256",
        type=str,
        default=None,
        help="Optional expected SHA256 to assert during --verify-bundle",
    )
    parser.add_argument(
        "--build-timestamp-utc",
        type=str,
        default=None,
        help="Explicit build timestamp in ISO 8601 UTC format (defaults to recorded creation timestamp)",
    )
    args = parser.parse_args()

    if args.verify_bundle is not None:
        try:
            verify_canonical_metric_bundle_file(args.verify_bundle, args.expected_bundle_sha256)
            return 0
        except Exception as exc:
            print(f"VERIFY BUNDLE ERROR: {exc}", file=sys.stderr)
            return 1

    out_p = None if args.verify_only else args.output_path
    try:
        bundle = build_canonical_metric_bundle(
            public_package_dir=args.public_package_dir,
            seal_path=args.seal_path,
            output_path=out_p,
            build_timestamp_utc=args.build_timestamp_utc,
        )
        if not args.verify_only and args.lineage_output_path:
            generate_lineage_markdown(bundle, args.lineage_output_path)
            print(f"Lineage markdown successfully written to: {args.lineage_output_path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
