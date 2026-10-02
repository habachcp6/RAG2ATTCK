"""Independent Canonical Validator: Terminal Audit Script for Phase S2.

Executes strictly READ-ONLY verification of complete 6,400 record matrix,
journal event lifecycle, financial ledger invariants, hash bindings, and
secret sanitization, generating an independent audit seal.
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from src.evaluation.experiment_metrics import EvaluationInputs, load_evaluation_inputs
from src.experiment.authorization import (
    ScientificProtocolApproval,
    compute_code_manifest_sha256,
    compute_protocol_sha256,
    protocol_decision_dict,
    validate_scientific_protocol,
)
from src.experiment.config import canonical_bytes, digest, load_plan
from src.experiment.monetary_ledger import (
    _strict_json_loads,
    calculate_request_cost_from_receipts,
    compute_pricing_contract_sha256,
    round_cost_up,
    round_credit_down,
    validate_finite_nonnegative_money,
)
from src.experiment.runner import _resume_state, _validate_record_binding
from src.experiment.schemas import CONDITIONS, ExperimentRecord
from src.llm.schemas import ParseStatus

ALLOWED_PARSE_STATUSES: Set[str] = {s.value for s in ParseStatus}

REPO_ROOT = Path(__file__).resolve().parent.parent

EXPECTED_CANARY_RAW_FIRSTLINE_SHA256 = (
    "83351ad996f7d4d70910051f47f7a3d4c45a46259431dcf92e764dbf5d554770"
)
EXPECTED_CANARY_CANONICAL_DIGEST = (
    "dabf60970aa5a18d93f95976aafdaeef2d747e24d9bcb7b13176e63e2edde034"
)
EXPECTED_PRICING_CONTRACT_SHA256 = (
    "4adfe8a0630bc1703a92e233133ea55eeff21ef5312dc3102369c267767c9565"
)
EXPECTED_PROTOCOL_CANONICAL_DIGEST = (
    "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c"
)
EXPECTED_BASELINE_COMMIT_SHA = "80dbeb3fe2316e5d2d39de2ed6a5a2d15cfa9315"
EXPECTED_LAUNCHER_WRAPPER_SHA256 = (
    "05b60f050cb456688ed74bddb72f994f3b61a84b56f8e568dda4c17467c4c7aa"
)

ALLOWED_JOURNAL_EVENTS: Set[str] = {
    "header",
    "monetary_reserve",
    "transition",
    "attempt",
    "attempt_receipt",
    "complete",
    "monetary_settle",
    "reservation_abandoned",
    "monetary_cancel_orphan",
    "monetary_cancel_hold",
}

REQUIRED_PROOF_FIELDS: Set[str] = {
    "run_id",
    "task_id",
    "pid",
    "start_identity",
    "process_status",
    "exit_code",
    "artifact_log_sha256",
    "final_summary",
}

REQUIRED_SUMMARY_FIELDS: Set[str] = {
    "complete",
    "execution_mode",
    "run_id",
    "record_count",
}

ALLOWED_PROCESS_STATUSES: Set[str] = {"non-running", "terminated", "exited"}


class AuditVerificationError(RuntimeError):
    """Raised whenever a terminal audit gate or invariant is violated."""


def audit_completeness_and_cardinality(
    exp_dir: Path,
    expected_sample_ids: Set[str],
    require_all_conditions: bool = True,
    registry_ids: Optional[Set[str]] = None,
    corpus_ids: Optional[Set[str]] = None,
) -> Dict[Tuple[str, str], ExperimentRecord]:
    """Verify that prediction files exist, are newline-complete,

    and contain exactly the expected unique sample IDs across conditions.
    """
    records_by_key: Dict[Tuple[str, str], ExperimentRecord] = {}

    for condition in CONDITIONS:
        pred_path = exp_dir / f"{condition}_predictions.jsonl"
        if not pred_path.exists():
            if require_all_conditions:
                raise AuditVerificationError(f"Missing prediction file: {pred_path}")
            continue

        raw_bytes = pred_path.read_bytes()
        if not raw_bytes.endswith(b"\n"):
            raise AuditVerificationError(
                f"Prediction file {pred_path.name} is not newline-terminated (incomplete write)"
            )

        seen_in_cond: Set[str] = set()
        lines = [line.strip() for line in raw_bytes.splitlines() if line.strip()]

        if len(lines) != len(expected_sample_ids):
            raise AuditVerificationError(
                f"Cardinality error in {condition}: found {len(lines)} records, "
                f"expected {len(expected_sample_ids)}"
            )

        for line_idx, line in enumerate(lines):
            try:
                row = _strict_json_loads(line)
            except Exception as exc:
                raise AuditVerificationError(
                    f"Malformed JSON at {pred_path.name}:{line_idx + 1}: {exc}"
                ) from exc

            rec = ExperimentRecord.model_validate(row)
            if rec.condition != condition:
                raise AuditVerificationError(
                    f"Condition mismatch in {pred_path.name}:{line_idx + 1}: "
                    f"record has '{rec.condition}', file is '{condition}'"
                )

            if rec.sample_id not in expected_sample_ids:
                raise AuditVerificationError(
                    f"Unexpected sample_id '{rec.sample_id}' in {pred_path.name}:{line_idx + 1} "
                    f"outside test split universe"
                )

            if rec.sample_id in seen_in_cond:
                raise AuditVerificationError(
                    f"Duplicate sample_id '{rec.sample_id}' in {pred_path.name}"
                )
            seen_in_cond.add(rec.sample_id)

            if rec.parse_status not in ALLOWED_PARSE_STATUSES:
                raise AuditVerificationError(
                    f"Invalid parse_status '{rec.parse_status}' in {pred_path.name}:{line_idx + 1}"
                )

            key = (rec.sample_id, condition)
            records_by_key[key] = rec

        if seen_in_cond != expected_sample_ids:
            missing = expected_sample_ids - seen_in_cond
            raise AuditVerificationError(
                f"Missing {len(missing)} sample IDs in {condition}: {list(missing)[:5]}"
            )

    manifest_file = exp_dir / "manifest.json"
    if manifest_file.exists() and registry_ids is not None and corpus_ids is not None:
        manifest_data = _strict_json_loads(manifest_file.read_bytes())
        m_sha = digest(canonical_bytes(manifest_data))
        for rec in records_by_key.values():
            try:
                _validate_record_binding(
                    rec, manifest_data, m_sha, registry_ids=registry_ids, corpus_ids=corpus_ids
                )
            except ValueError as exc:
                raise AuditVerificationError(
                    f"Record binding error for {rec.sample_id}:{rec.condition}: {exc}"
                ) from exc

    return records_by_key


def audit_journal_join_and_lifecycle(
    exp_dir: Path,
    records_by_key: Dict[Tuple[str, str], ExperimentRecord],
) -> Tuple[Dict[Tuple[str, str], List[Dict[str, Any]]], Dict[Tuple[str, str], Dict[str, Any]]]:
    """Verify request_journal.jsonl integrity without in-place dictionary overwriting."""
    journal_path = exp_dir / "request_journal.jsonl"
    if not journal_path.exists():
        raise AuditVerificationError(f"Missing journal file at {journal_path}")

    raw_bytes = journal_path.read_bytes()
    if not raw_bytes.endswith(b"\n"):
        raise AuditVerificationError("Journal file is not newline-terminated")

    lines = [line.strip() for line in raw_bytes.splitlines() if line.strip()]
    if not lines:
        raise AuditVerificationError("Journal file is empty")

    header = _strict_json_loads(lines[0])
    if header.get("event") != "header":
        raise AuditVerificationError(f"First journal line must be header event, got {header}")

    manifest_sha = header.get("manifest_sha256")
    if not manifest_sha:
        raise AuditVerificationError("Journal header missing manifest_sha256")

    receipts_by_key: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    completed_shas_by_key: Dict[Tuple[str, str], str] = {}
    settled_events_by_key: Dict[Tuple[str, str], Dict[str, Any]] = {}
    seen_attempts_by_key: Set[Tuple[str, str]] = set()
    attempt_ordinals: List[int] = []

    for line_idx, line in enumerate(lines[1:], start=2):
        ev = _strict_json_loads(line)
        kind = ev.get("event")
        if kind not in ALLOWED_JOURNAL_EVENTS:
            raise AuditVerificationError(f"Unknown journal event '{kind}' at line {line_idx}")

        k_list = ev.get("key")
        k = tuple(k_list) if isinstance(k_list, list) and len(k_list) == 2 else None

        if kind == "attempt":
            ord_val = ev.get("ordinal")
            if not isinstance(ord_val, int) or isinstance(ord_val, bool):
                raise AuditVerificationError(f"Invalid ordinal {ord_val} at line {line_idx}")
            attempt_ordinals.append(ord_val)
            if k:
                seen_attempts_by_key.add(k)

        elif kind == "attempt_receipt":
            if not k:
                raise AuditVerificationError(f"Receipt missing key at line {line_idx}")
            rec_ord = ev.get("ordinal")
            rec_idx = ev.get("attempt_index")
            if not isinstance(rec_ord, int) or not isinstance(rec_idx, int):
                raise AuditVerificationError(
                    f"Receipt has non-int ordinal/index at line {line_idx}"
                )
            key_receipts = receipts_by_key.setdefault(k, [])
            if any(r.get("attempt_index") == rec_idx for r in key_receipts):
                raise AuditVerificationError(
                    f"Duplicate attempt_index {rec_idx} for key {k} at line {line_idx}"
                )
            key_receipts.append(ev)

        elif kind == "complete":
            if not k:
                raise AuditVerificationError(f"Complete missing key at line {line_idx}")
            if k not in seen_attempts_by_key:
                raise AuditVerificationError(
                    f"Reordered journal events: complete before attempt for key {k} "
                    f"at line {line_idx}"
                )
            if k in completed_shas_by_key:
                raise AuditVerificationError(
                    f"Duplicate complete event for key {k} at line {line_idx}"
                )
            rec_sha = ev.get("record_sha256")
            if not rec_sha or len(rec_sha) != 64:
                raise AuditVerificationError(f"Invalid record_sha256 at line {line_idx}")
            completed_shas_by_key[k] = rec_sha

        elif kind == "monetary_settle":
            if not k:
                raise AuditVerificationError(f"Settle missing key at line {line_idx}")
            if k not in completed_shas_by_key:
                raise AuditVerificationError(
                    f"Reordered journal events: monetary_settle before complete for key {k} "
                    f"at line {line_idx}"
                )
            if k in settled_events_by_key:
                raise AuditVerificationError(
                    f"Duplicate monetary_settle event for key {k} at line {line_idx}"
                )
            settled_events_by_key[k] = ev

    # Check monotonic attempt ordinals
    if attempt_ordinals:
        expected_seq = list(range(1, len(attempt_ordinals) + 1))
        if attempt_ordinals != expected_seq:
            raise AuditVerificationError(
                f"Non-monotonic or gapped attempt ordinals: seen {len(attempt_ordinals)}, "
                f"first 5={attempt_ordinals[:5]}, expected contiguous 1..N"
            )

    # 1:1 join between records, completes, and settlements
    if set(completed_shas_by_key.keys()) != set(records_by_key.keys()):
        missing = set(records_by_key.keys()) - set(completed_shas_by_key.keys())
        raise AuditVerificationError(f"Uncompleted records in journal: {len(missing)}")

    if set(settled_events_by_key.keys()) != set(records_by_key.keys()):
        missing = set(records_by_key.keys()) - set(settled_events_by_key.keys())
        raise AuditVerificationError(f"Unsettled records in journal: {len(missing)}")

    for key, rec in records_by_key.items():
        computed_sha = digest(canonical_bytes(rec.model_dump()))
        if completed_shas_by_key[key] != computed_sha:
            raise AuditVerificationError(
                f"Record digest mismatch for {key}: "
                f"journal complete has {completed_shas_by_key[key]}, record computed {computed_sha}"
            )

        settle_ev = settled_events_by_key[key]
        if settle_ev.get("record_sha256") != computed_sha:
            raise AuditVerificationError(
                f"Settlement digest mismatch for {key}: "
                f"settle has {settle_ev.get('record_sha256')}, record computed {computed_sha}"
            )

    return receipts_by_key, settled_events_by_key


def audit_financial_ledger_and_tariffs(
    study_root: Path,
    validator_root: Path,
    records_by_key: Dict[Tuple[str, str], ExperimentRecord],
    receipts_by_key: Dict[Tuple[str, str], List[Dict[str, Any]]],
    settled_events_by_key: Dict[Tuple[str, str], Dict[str, Any]],
    expected_model: str = "gpt-5.6-luna",
) -> Tuple[Decimal, Decimal]:
    """Independently audit study_ledger.json and .study_anchor.json without modifying disk."""
    pricing_path = validator_root / "config" / "pricing_v1.json"
    pricing_data = _strict_json_loads(pricing_path.read_bytes())
    pricing_sha = compute_pricing_contract_sha256(pricing_data)

    anchor_path = study_root / ".study_anchor.json"
    if not anchor_path.exists():
        raise AuditVerificationError(f"Missing study anchor at {anchor_path}")
    anchor = _strict_json_loads(anchor_path.read_bytes())

    if anchor.get("pricing_contract_sha256") != pricing_sha:
        raise AuditVerificationError("Anchor pricing contract SHA-256 drift")
    if anchor.get("total_budget_usd") != "19.99000000":
        raise AuditVerificationError(f"Anchor total budget drift: {anchor.get('total_budget_usd')}")
    if anchor.get("prior_pilot_provisional_hold_usd") != "0.05264010":
        raise AuditVerificationError("Anchor pilot hold drift")
    if anchor.get("initial_available_usd") != "19.93735990":
        raise AuditVerificationError("Anchor initial available drift")

    ledger_path = study_root / "artifacts" / "study_budget" / "study_ledger.json"
    if not ledger_path.exists():
        raise AuditVerificationError(f"Missing study ledger at {ledger_path}")
    ledger = _strict_json_loads(ledger_path.read_bytes())

    if ledger.get("pricing_contract_sha256") != pricing_sha:
        raise AuditVerificationError("Ledger pricing contract SHA-256 drift")
    if ledger.get("total_budget_usd") != "19.99000000":
        raise AuditVerificationError("Ledger total budget drift")
    if ledger.get("prior_pilot_provisional_hold_usd") != "0.05264010":
        raise AuditVerificationError("Ledger pilot hold drift")

    # Native absence semantics: has_breach defaults to False when absent.
    # If present, it must be boolean False.
    has_breach_val = ledger.get("has_breach", False)
    if not isinstance(has_breach_val, bool) or has_breach_val is True:
        raise AuditVerificationError(f"Study ledger reports breach: has_breach={has_breach_val}")

    breached_records = ledger.get("breached_records", {})
    if not isinstance(breached_records, dict) or len(breached_records) > 0:
        raise AuditVerificationError(f"Study ledger reports breached records: {breached_records}")

    active_res = ledger.get("active_reservations", {})
    if not isinstance(active_res, dict) or len(active_res) > 0:
        raise AuditVerificationError(
            f"Active reservations remaining open in ledger at terminal state: {active_res}"
        )

    res_usd_str = ledger.get("active_reservations_usd", "0.00000000")
    res_usd = validate_finite_nonnegative_money(res_usd_str, "active_reservations_usd")
    if res_usd != Decimal("0.0"):
        raise AuditVerificationError(f"Non-zero active_reservations_usd: {res_usd_str}")

    settled_records = ledger.get("settled_records", {})
    if not isinstance(settled_records, dict):
        raise AuditVerificationError("Ledger settled_records must be a dict")
    if len(settled_records) != len(records_by_key):
        raise AuditVerificationError(
            f"Ledger settled records count mismatch: ledger has {len(settled_records)}, "
            f"expected {len(records_by_key)}"
        )

    # Validate settlement_records_count field
    settlement_count = ledger.get("settlement_records_count")
    if settlement_count is not None:
        if not isinstance(settlement_count, int) or isinstance(settlement_count, bool):
            raise AuditVerificationError(
                "Ledger settlement_records_count must be integer, "
                f"got {type(settlement_count).__name__}"
            )
        if settlement_count != len(records_by_key):
            raise AuditVerificationError(
                f"Ledger settlement_records_count mismatch: ledger specifies {settlement_count}, "
                f"expected {len(records_by_key)}"
            )

    # Independent tariff recomputation using frozen calculate_request_cost_from_receipts
    total_recomputed_settled = Decimal("0.0")

    for key, rec in records_by_key.items():
        key_str = f"{key[0]}:{key[1]}"
        if key_str not in settled_records:
            raise AuditVerificationError(f"Key {key_str} missing from ledger settled_records")

        ledger_rec = settled_records[key_str]
        if not isinstance(ledger_rec, dict):
            raise AuditVerificationError(f"Ledger record for {key_str} must be a dict")

        settle_ev = settled_events_by_key.get(key)
        if not settle_ev:
            raise AuditVerificationError(f"Missing settle event in journal for key {key}")

        if settle_ev.get("breach") is not False:
            raise AuditVerificationError(
                f"Journal settle event indicates breach on {key}: {settle_ev.get('breach')}"
            )
        if ledger_rec.get("breach") is True:
            raise AuditVerificationError(f"Ledger record reports breach for {key_str}")

        # Record SHA-256 match
        computed_sha = digest(canonical_bytes(rec.model_dump()))
        ledger_sha = ledger_rec.get("record_sha256")
        if ledger_sha != computed_sha:
            raise AuditVerificationError(
                f"Ledger record_sha256 mismatch for {key_str}: "
                f"ledger={ledger_sha} != computed={computed_sha}"
            )
        journal_sha = settle_ev.get("record_sha256")
        if journal_sha != computed_sha:
            raise AuditVerificationError(
                f"Journal settle record_sha256 mismatch for {key}: "
                f"journal={journal_sha} != computed={computed_sha}"
            )

        key_receipts = receipts_by_key.get(key, [])
        if not key_receipts:
            raise AuditVerificationError(f"No receipts recorded in journal for key {key}")

        last_ord = key_receipts[-1].get("ordinal")
        calc_cost, breach, breach_reason = calculate_request_cost_from_receipts(
            attempts_consumed=len(key_receipts),
            receipts=key_receipts,
            record=rec,
            pricing_config=pricing_data,
            tier="default",
            expected_model=expected_model,
            most_recent_attempt_ordinal=last_ord,
        )

        if breach:
            raise AuditVerificationError(
                f"Tariff calculation flagged breach on {key}: {breach_reason}"
            )

        journal_cost = validate_finite_nonnegative_money(
            settle_ev.get("cost_usd"), f"journal cost_usd for {key}"
        )
        ledger_cost = validate_finite_nonnegative_money(
            ledger_rec.get("cost_usd"), f"ledger cost_usd for {key_str}"
        )

        if journal_cost != calc_cost:
            raise AuditVerificationError(
                f"Journal cost mismatch for {key}: journal={journal_cost} != calc={calc_cost}"
            )
        if ledger_cost != calc_cost:
            raise AuditVerificationError(
                f"Ledger cost mismatch for {key_str}: ledger={ledger_cost} != calc={calc_cost}"
            )

        # Check refund_usd
        journal_refund = validate_finite_nonnegative_money(
            settle_ev.get("refund_usd"), f"journal refund_usd for {key}"
        )
        ledger_refund = validate_finite_nonnegative_money(
            ledger_rec.get("refund_usd"), f"ledger refund_usd for {key_str}"
        )
        if ledger_refund != journal_refund:
            raise AuditVerificationError(
                f"Refund drift for {key_str}: ledger={ledger_refund} != journal={journal_refund}"
            )

        expected_refund = round_credit_down(Decimal("2.15898240") - calc_cost)
        if journal_refund != expected_refund:
            raise AuditVerificationError(
                f"Refund conservation mismatch for {key}: "
                f"journal={journal_refund} != expected={expected_refund}"
            )

        total_recomputed_settled += calc_cost

    total_settled_rounded = round_cost_up(total_recomputed_settled)
    cumulative_ledger = validate_finite_nonnegative_money(
        ledger.get("cumulative_settled_cost_usd", "0.0"), "cumulative_settled_cost_usd"
    )
    if cumulative_ledger != total_settled_rounded:
        raise AuditVerificationError(
            f"Cumulative settled cost mismatch: recorded {cumulative_ledger} "
            f"!= recomputed sum {total_settled_rounded}"
        )

    max_available = Decimal("19.93735990")
    if cumulative_ledger > max_available:
        raise AuditVerificationError(
            f"Budget cap breach: cumulative cost {cumulative_ledger} exceeds "
            f"available {max_available}"
        )

    expected_avail = round_credit_down(
        Decimal("19.99000000") - Decimal("0.05264010") - cumulative_ledger
    )
    ledger_avail = validate_finite_nonnegative_money(
        ledger.get("uncommitted_available_balance_usd", "0.0"), "uncommitted_available_balance_usd"
    )
    if ledger_avail != expected_avail:
        raise AuditVerificationError(
            f"Available balance conservation mismatch: ledger has {ledger_avail}, "
            f"expected {expected_avail}"
        )

    return cumulative_ledger, expected_avail


def audit_provenance_and_hash_invariants(
    validator_root: Path,
    exp_dir: Path,
    records_by_key: Dict[Tuple[str, str], ExperimentRecord],
    canary_raw_firstline_hash: Optional[str] = EXPECTED_CANARY_RAW_FIRSTLINE_SHA256,
    canary_canonical_digest: Optional[str] = EXPECTED_CANARY_CANONICAL_DIGEST,
    launcher_wrapper_path: Optional[Path] = None,
    expected_launcher_hash: Optional[str] = EXPECTED_LAUNCHER_WRAPPER_SHA256,
    fixture_only: bool = False,
    is_production: bool = False,
) -> None:
    """Byte-level verification of canary raw firstline, canonical digest, lock, and launcher."""
    # 1. Launcher Wrapper Script verification (Fail-closed)
    if launcher_wrapper_path is not None:
        if not launcher_wrapper_path.exists():
            raise AuditVerificationError(
                f"Missing launcher wrapper script at {launcher_wrapper_path}"
            )
        if expected_launcher_hash:
            actual_launcher_sha = hashlib.sha256(launcher_wrapper_path.read_bytes()).hexdigest()
            if actual_launcher_sha != expected_launcher_hash:
                raise AuditVerificationError(
                    f"Launcher wrapper SHA-256 drift: expected {expected_launcher_hash}, "
                    f"got {actual_launcher_sha}"
                )
    elif is_production:
        raise AuditVerificationError(
            "Launcher wrapper script path must be provided in production audit"
        )

    # 2. Byte-level verification of Canary First Line Raw SHA-256
    if canary_raw_firstline_hash:
        canary_pred_file = exp_dir / "no_rag_predictions.jsonl"
        if not canary_pred_file.exists():
            raise AuditVerificationError(f"Missing canary prediction file at {canary_pred_file}")
        raw_lines = canary_pred_file.read_bytes().splitlines(keepends=True)
        if not raw_lines:
            raise AuditVerificationError(f"Canary prediction file {canary_pred_file.name} is empty")
        actual_firstline_sha = hashlib.sha256(raw_lines[0]).hexdigest()
        if actual_firstline_sha != canary_raw_firstline_hash:
            raise AuditVerificationError(
                f"Canary first line raw SHA-256 drift: expected {canary_raw_firstline_hash}, "
                f"got {actual_firstline_sha}"
            )

    # 3. Canary Canonical Record Digest
    if canary_canonical_digest:
        canary_rec = records_by_key.get(("view_00477e30", "no_rag"))
        if canary_rec is None:
            raise AuditVerificationError(
                "Missing canary record ('view_00477e30', 'no_rag') in records"
            )
        actual_canary_digest = digest(canonical_bytes(canary_rec.model_dump()))
        if actual_canary_digest != canary_canonical_digest:
            raise AuditVerificationError(
                f"Canary canonical digest drift: expected {canary_canonical_digest}, "
                f"got {actual_canary_digest}"
            )

    # 4. Canonical Lockfile & Core Code Manifest
    if not fixture_only:
        lock_path = validator_root / "config" / "canonical_experiment_lock_v1.json"
        if not lock_path.exists():
            raise AuditVerificationError(f"Missing canonical lockfile at {lock_path}")
        lock_data = _strict_json_loads(lock_path.read_bytes())
        plan_path = validator_root / "config" / "experiment_config.json"
        if not plan_path.exists():
            raise AuditVerificationError(f"Missing experiment config at {plan_path}")
        plan = load_plan(plan_path)
        for art_name, expected_hash in lock_data.get("artifact_hashes", {}).items():
            if art_name not in plan.manifest.get("artifacts", {}):
                raise AuditVerificationError(
                    f"Locked artifact '{art_name}' missing from plan manifest"
                )
            rel_path = plan.manifest["artifacts"][art_name]["path"]
            art_path = validator_root / rel_path
            if not art_path.exists():
                raise AuditVerificationError(f"Missing locked artifact '{art_name}' at {art_path}")
            actual_hash = digest(art_path.read_bytes())
            if actual_hash != expected_hash:
                raise AuditVerificationError(
                    f"Artifact hash mismatch for '{art_name}': "
                    f"expected {expected_hash}, got {actual_hash}"
                )

        # 5. Core Code Manifest SHA-256
        actual_code_manifest = compute_code_manifest_sha256(validator_root)
        expected_code_manifest = lock_data.get("code_manifest_sha256")
        if expected_code_manifest and actual_code_manifest != expected_code_manifest:
            raise AuditVerificationError(
                "Core code manifest SHA-256 drift: "
                f"expected {expected_code_manifest}, got {actual_code_manifest}"
            )


def audit_secret_sanitization(
    files_to_scan: Sequence[Path],
    extra_secret_tokens: Optional[Sequence[str]] = None,
) -> Dict[str, int]:
    """Scan output files for credential patterns, logging match counts ONLY (never contents)."""
    secret_patterns = [
        re.compile(r"sk-[a-zA-Z0-9_-]{20,}"),
        re.compile(r"Bearer\s+[a-zA-Z0-9_\-\.]{20,}"),
    ]
    scan_summary: Dict[str, int] = {}

    for path in files_to_scan:
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        matches = 0
        for pat in secret_patterns:
            matches += len(pat.findall(content))

        if extra_secret_tokens:
            for sec in extra_secret_tokens:
                if sec and len(sec) > 8 and sec in content:
                    matches += 1

        scan_summary[path.name] = matches
        if matches > 0:
            raise AuditVerificationError(
                f"Secret leak detected: {matches} secret pattern occurrences found in {path.name}"
            )

    return scan_summary


def audit_protected_baseline_22_files(
    validator_root: Path,
    baseline_inventory_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Verify all 22 protected baseline files, protocol decisions, and pricing contract."""
    inv_path = baseline_inventory_path or (
        validator_root / "artifacts" / "orchestration" / "integration_protected_baseline.json"
    )
    if not inv_path.exists():
        raise AuditVerificationError(f"Protected baseline inventory missing at {inv_path}")

    inv_data = _strict_json_loads(inv_path.read_bytes())
    baseline_sha = inv_data.get("baseline_sha")
    if baseline_sha != EXPECTED_BASELINE_COMMIT_SHA:
        raise AuditVerificationError(
            f"Protected baseline SHA mismatch: expected {EXPECTED_BASELINE_COMMIT_SHA}, "
            f"got {baseline_sha}"
        )

    protected_files = inv_data.get("protected_files", {})
    if not isinstance(protected_files, dict) or len(protected_files) != 22:
        raise AuditVerificationError(
            f"Protected baseline must contain exactly 22 files, found {len(protected_files)}"
        )

    verified_hashes: Dict[str, str] = {}
    for rel_path_str, expected_sha in protected_files.items():
        file_path = validator_root / rel_path_str
        if not file_path.exists():
            raise AuditVerificationError(
                f"Missing protected baseline file: '{rel_path_str}' at {file_path}"
            )
        actual_sha = hashlib.sha256(file_path.read_bytes()).hexdigest()
        if actual_sha != expected_sha:
            raise AuditVerificationError(
                f"Protected baseline hash mismatch for '{rel_path_str}': "
                f"expected {expected_sha}, got {actual_sha}"
            )
        verified_hashes[rel_path_str] = actual_sha

    # Verify Protocol Semantic Binding & Canonical Digest
    proto_path = validator_root / "config" / "experiment_protocol_v1.json"
    if not proto_path.exists():
        raise AuditVerificationError(f"Missing protocol file at {proto_path}")
    proto_data = _strict_json_loads(proto_path.read_bytes())
    try:
        protocol_obj = ScientificProtocolApproval(**proto_data)
        validate_scientific_protocol(protocol_obj)
    except Exception as exc:
        raise AuditVerificationError(f"Protocol validation failed: {exc}") from exc

    decisions = protocol_decision_dict(protocol_obj)
    computed_proto_hash = compute_protocol_sha256(decisions)
    if (
        protocol_obj.protocol_sha256 != EXPECTED_PROTOCOL_CANONICAL_DIGEST
        or computed_proto_hash != EXPECTED_PROTOCOL_CANONICAL_DIGEST
    ):
        raise AuditVerificationError(
            f"Protocol canonical digest mismatch: expected {EXPECTED_PROTOCOL_CANONICAL_DIGEST}, "
            f"got object={protocol_obj.protocol_sha256}, computed={computed_proto_hash}"
        )

    # Verify Pricing Semantic Contract Binding
    pricing_path = validator_root / "config" / "pricing_v1.json"
    if not pricing_path.exists():
        raise AuditVerificationError(f"Missing pricing config at {pricing_path}")
    pricing_data = _strict_json_loads(pricing_path.read_bytes())
    computed_pricing_sha = compute_pricing_contract_sha256(pricing_data)
    if computed_pricing_sha != EXPECTED_PRICING_CONTRACT_SHA256:
        raise AuditVerificationError(
            f"Pricing semantic contract drift: expected {EXPECTED_PRICING_CONTRACT_SHA256}, "
            f"got {computed_pricing_sha}"
        )

    return {
        "baseline_sha": baseline_sha,
        "verified_file_count": len(verified_hashes),
        "protocol_canonical_digest": EXPECTED_PROTOCOL_CANONICAL_DIGEST,
        "pricing_contract_sha256": EXPECTED_PRICING_CONTRACT_SHA256,
        "all_22_files_verified": True,
    }


def audit_terminal_process_proof(
    terminal_proof_file: Path,
    *,
    expected_run_id: Optional[str] = None,
    expected_task_id: Optional[str] = None,
    log_file_path: Optional[Path] = None,
    expected_execution_mode: Optional[str] = None,
    expected_record_count: Optional[int] = None,
    require_log_file: bool = False,
) -> Dict[str, Any]:
    """Verify authoritative task/process terminal proof with strict schema and byte bindings."""
    if not terminal_proof_file.exists():
        raise AuditVerificationError(f"Missing terminal proof file at {terminal_proof_file}")
    raw_bytes = terminal_proof_file.read_bytes()
    proof_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    proof_data = _strict_json_loads(raw_bytes)

    if not isinstance(proof_data, dict):
        raise AuditVerificationError("Terminal process proof must be a JSON object")

    missing = REQUIRED_PROOF_FIELDS - set(proof_data.keys())
    if missing:
        raise AuditVerificationError(
            f"Terminal process proof missing required fields: {sorted(missing)}"
        )

    # 1. run_id: non-empty string, matches expected if specified
    run_id = proof_data["run_id"]
    if not isinstance(run_id, str) or not run_id.strip():
        raise AuditVerificationError(f"Terminal proof invalid 'run_id': {run_id}")
    if expected_run_id is not None and run_id != expected_run_id:
        raise AuditVerificationError(
            f"Terminal proof run_id mismatch: expected '{expected_run_id}', got '{run_id}'"
        )

    # 2. task_id: non-empty string, matches expected if specified
    task_id = proof_data["task_id"]
    if not isinstance(task_id, str) or not task_id.strip():
        raise AuditVerificationError(f"Terminal proof invalid 'task_id': {task_id}")
    if expected_task_id is not None and task_id != expected_task_id:
        raise AuditVerificationError(
            f"Terminal proof task_id mismatch: expected '{expected_task_id}', got '{task_id}'"
        )

    # 3. pid: integer, strictly not bool, must be positive
    pid = proof_data["pid"]
    if type(pid) is not int:
        raise AuditVerificationError(
            f"Terminal proof 'pid' must be an integer, got {type(pid).__name__}"
        )
    if pid <= 0:
        raise AuditVerificationError(f"Terminal proof 'pid' must be positive, got {pid}")

    # 4. start_identity: non-empty string/valid identifier
    start_identity = proof_data["start_identity"]
    if not isinstance(start_identity, str) or not start_identity.strip():
        raise AuditVerificationError(
            f"Terminal proof missing valid 'start_identity': {start_identity}"
        )

    # 5. process_status: must be 'non-running', 'terminated', or 'exited', NEVER 'running'
    process_status = proof_data["process_status"]
    if not isinstance(process_status, str):
        raise AuditVerificationError(
            f"Terminal proof 'process_status' must be string, got {type(process_status).__name__}"
        )
    status_lower = process_status.strip().lower()
    if status_lower == "running":
        raise AuditVerificationError(
            "Terminal proof process_status is still 'running'; runner must be terminated"
        )
    if status_lower not in ALLOWED_PROCESS_STATUSES:
        raise AuditVerificationError(
            f"Terminal proof invalid process_status '{process_status}'; "
            f"expected one of {ALLOWED_PROCESS_STATUSES}"
        )

    # 6. exit_code: must be integer == 0
    exit_code = proof_data["exit_code"]
    if type(exit_code) is not int:
        raise AuditVerificationError(
            f"Terminal proof 'exit_code' must be an integer, got {type(exit_code).__name__}"
        )
    if exit_code != 0:
        raise AuditVerificationError(f"Terminal process proof indicates non-zero exit: {exit_code}")

    # 7. artifact_log_sha256: 64-char hex SHA-256 string and byte binding
    log_sha256 = proof_data["artifact_log_sha256"]
    if (
        not isinstance(log_sha256, str)
        or len(log_sha256) != 64
        or not re.fullmatch(r"[0-9a-fA-F]{64}", log_sha256)
    ):
        raise AuditVerificationError(f"Terminal proof invalid 'artifact_log_sha256': {log_sha256}")

    target_log_path = log_file_path
    if target_log_path is None and "authoritative_log" in proof_data and proof_data["authoritative_log"]:
        target_log_path = Path(proof_data["authoritative_log"])

    if target_log_path is not None:
        if target_log_path.exists():
            computed_log_sha = hashlib.sha256(target_log_path.read_bytes()).hexdigest()
            if computed_log_sha.lower() != log_sha256.lower():
                raise AuditVerificationError(
                    f"Authoritative log SHA-256 drift: expected {log_sha256}, "
                    f"got {computed_log_sha} from {target_log_path}"
                )
        elif require_log_file or log_file_path is not None:
            raise AuditVerificationError(
                f"Authoritative log file not found at {target_log_path}"
            )
    elif require_log_file:
        raise AuditVerificationError(
            "Terminal proof verification requires an authoritative log file path for byte binding"
        )

    # 8. final_summary: must be present and validate required schema
    final_summary = proof_data["final_summary"]
    if not isinstance(final_summary, dict) or not final_summary:
        raise AuditVerificationError(
            f"Terminal proof missing or empty 'final_summary': {final_summary}"
        )

    missing_summary = REQUIRED_SUMMARY_FIELDS - set(final_summary.keys())
    if missing_summary:
        raise AuditVerificationError(
            f"Terminal proof final_summary missing required fields: {sorted(missing_summary)}"
        )

    complete_val = final_summary.get("complete")
    if type(complete_val) is not bool or complete_val is not True:
        raise AuditVerificationError(
            f"Terminal proof final_summary 'complete' must be strictly True (boolean), got {complete_val}"
        )

    summary_run_id = final_summary.get("run_id")
    if not isinstance(summary_run_id, str) or not summary_run_id.strip():
        raise AuditVerificationError(f"Terminal proof final_summary invalid 'run_id': {summary_run_id}")
    if summary_run_id != run_id:
        raise AuditVerificationError(
            f"Terminal proof final_summary run_id mismatch: summary has '{summary_run_id}', proof has '{run_id}'"
        )
    if expected_run_id is not None and summary_run_id != expected_run_id:
        raise AuditVerificationError(
            f"Terminal proof final_summary run_id mismatch: summary has '{summary_run_id}', expected '{expected_run_id}'"
        )

    mode = final_summary.get("execution_mode")
    if not isinstance(mode, str) or not mode.strip():
        raise AuditVerificationError(f"Terminal proof final_summary invalid 'execution_mode': {mode}")
    if expected_execution_mode is not None and mode != expected_execution_mode:
        raise AuditVerificationError(
            f"Terminal proof final_summary execution_mode mismatch: expected '{expected_execution_mode}', got '{mode}'"
        )
    elif (run_id.startswith("live-") or (expected_run_id and expected_run_id.startswith("live-"))) and mode != "live":
        raise AuditVerificationError(
            f"Terminal proof final_summary execution_mode must be 'live' for live run, got '{mode}'"
        )

    record_count = final_summary.get("record_count")
    if type(record_count) is not int or record_count <= 0:
        raise AuditVerificationError(
            f"Terminal proof final_summary 'record_count' must be a positive integer, got {record_count}"
        )
    if expected_record_count is not None and record_count != expected_record_count:
        raise AuditVerificationError(
            f"Terminal proof final_summary record_count mismatch: expected {expected_record_count}, got {record_count}"
        )

    if "requests_consumed" in final_summary and "consumed_provider_attempts" in final_summary:
        rc = final_summary["requests_consumed"]
        cpa = final_summary["consumed_provider_attempts"]
        if type(rc) is int and type(cpa) is int and rc != cpa:
            raise AuditVerificationError(
                f"Terminal proof final_summary requests_consumed ({rc}) != consumed_provider_attempts ({cpa})"
            )

    if "study_budget" in final_summary:
        sb = final_summary["study_budget"]
        if not isinstance(sb, dict):
            raise AuditVerificationError("Terminal proof final_summary 'study_budget' must be a dictionary")
        if sb.get("has_breach") is not False:
            raise AuditVerificationError("Terminal proof final_summary reports budget breach")
        if "total_budget_usd" in sb:
            try:
                tb = Decimal(str(sb["total_budget_usd"]))
                if tb > Decimal("19.99"):
                    raise AuditVerificationError(f"Terminal proof budget cap exceeded: {tb} > 19.99")
            except Exception:
                pass

    return {
        "path": str(terminal_proof_file),
        "sha256": proof_sha256,
        "run_id": run_id,
        "task_id": task_id,
        "pid": pid,
        "start_identity": start_identity,
        "process_status": process_status,
        "exit_code": exit_code,
        "artifact_log_sha256": log_sha256,
        "final_summary": final_summary,
    }


def audit_production_preloader_and_lifecycle(
    validator_root: Path,
    exp_dir: Path,
    manifest: Dict[str, Any],
) -> EvaluationInputs:
    """Enforce native load_evaluation_inputs and _resume_state lifecycle checks."""
    manifest_path = exp_dir / "manifest.json"
    pred_paths = {c: exp_dir / f"{c}_predictions.jsonl" for c in CONDITIONS}

    # 1. Native preloader
    try:
        inputs = load_evaluation_inputs(manifest_path, pred_paths, repository_root=validator_root)
    except (ValueError, KeyError, TypeError) as exc:
        raise AuditVerificationError(
            f"Production native preloader validation failed: {exc}"
        ) from exc

    registry_ids = set(inputs.registry.keys())
    corpus_ids = set(inputs.corpus_ids)

    # 2. Recovery-aware lifecycle with _resume_state
    manifest_sha = digest(canonical_bytes(manifest))
    cap = (
        manifest.get("authorized_max_provider_attempts")
        or manifest.get("fixture_max_requests")
        or manifest.get("authorized_max_requests")
    )
    if not isinstance(cap, int) or type(cap) is bool or cap <= 0:
        raise AuditVerificationError(f"Invalid or missing attempt budget cap in manifest: {cap}")

    # Verify journal header matches manifest and budget cap
    journal_path = exp_dir / "request_journal.jsonl"
    if not journal_path.exists():
        raise AuditVerificationError(f"Missing request_journal.jsonl at {journal_path}")
    raw_journal = journal_path.read_bytes()
    if not raw_journal.strip():
        raise AuditVerificationError(f"Empty request_journal.jsonl at {journal_path}")
    first_line = raw_journal.splitlines()[0]
    header = _strict_json_loads(first_line)
    if header != {"event": "header", "manifest_sha256": manifest_sha, "max_requests": cap}:
        raise AuditVerificationError(
            f"Journal header does not match expected manifest/budget: "
            f"expected event='header', manifest_sha256={manifest_sha}, max_requests={cap}; "
            f"got {header}"
        )

    try:
        resume_state = _resume_state(
            exp_dir, manifest, manifest_sha, cap, registry_ids=registry_ids, corpus_ids=corpus_ids
        )
        if resume_state.orphan_reservation is not None:
            raise AuditVerificationError(
                "Orphan reservation remaining in journal at complete state: "
                f"{resume_state.orphan_reservation}"
            )
        if resume_state.recoverable_reservation is not None:
            raise AuditVerificationError(
                "Recoverable reservation remaining in journal at complete state: "
                f"{resume_state.recoverable_reservation}"
            )
    except ValueError as exc:
        raise AuditVerificationError(
            f"Native recovery-aware lifecycle audit failed: {exc}"
        ) from exc

    return inputs


def generate_audit_seal(
    exp_dir: Path,
    study_root: Path,
    validator_root: Path,
    output_seal_path: Path,
    records_by_key: Dict[Tuple[str, str], ExperimentRecord],
    cumulative_settled_usd: Decimal,
    uncommitted_avail_usd: Decimal,
    is_production: bool = False,
    terminal_proof_info: Optional[Dict[str, Any]] = None,
    protected_baseline_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate separate, private audit seal manifest locking all artifact digests.

    Fails closed if any required file is missing or if records are empty.
    """
    total_records = len(records_by_key)
    if total_records == 0:
        raise AuditVerificationError("Cannot generate audit seal for empty records")

    if is_production:
        if terminal_proof_info is None or not isinstance(terminal_proof_info, dict):
            raise AuditVerificationError("Production seal requires verified terminal_proof_info")
        if protected_baseline_info is None or not isinstance(protected_baseline_info, dict):
            raise AuditVerificationError("Production seal requires verified protected_baseline_info")
        if not protected_baseline_info.get("all_22_files_verified"):
            raise AuditVerificationError(
                "Production seal requires all 22 protected baseline files verified"
            )
        if total_records != 6400:
            raise AuditVerificationError(
                f"Production audit seal requires exactly 6,400 records, got {total_records}"
            )
        if cumulative_settled_usd > Decimal("19.99"):
            raise AuditVerificationError(
                f"Production seal cumulative settled cost ${cumulative_settled_usd} exceeds $19.99 ceiling"
            )

    required_artifacts = [
        exp_dir / "manifest.json",
        exp_dir / "run_summary.json",
        exp_dir / "request_journal.jsonl",
        exp_dir / "no_rag_predictions.jsonl",
        exp_dir / "rag_k1_predictions.jsonl",
        exp_dir / "rag_k3_predictions.jsonl",
        exp_dir / "rag_k5_predictions.jsonl",
        exp_dir / "rag_k10_predictions.jsonl",
        study_root / "artifacts" / "study_budget" / "study_ledger.json",
        study_root / ".study_anchor.json",
    ]

    sealed_digests: Dict[str, str] = {}
    for p in required_artifacts:
        if not p.exists():
            raise AuditVerificationError(f"Missing required artifact for seal: {p.name}")
        sealed_digests[p.name] = digest(p.read_bytes())

    lock_path = validator_root / "config" / "canonical_experiment_lock_v1.json"
    lock_data = _strict_json_loads(lock_path.read_bytes()) if lock_path.exists() else {}

    seal_type = (
        "canonical-independent-validation-seal-v1" if is_production else "fixture_evaluation"
    )
    seal_payload: Dict[str, Any] = {
        "schema_version": "1.0.0",
        "seal_type": seal_type,
        "fixture_only": not is_production,
        "production_ready": is_production,
        "study_id": "rag2attack-study-wide",
        "experiment_id": lock_data.get("experiment_id", "synthetic-paired-test-1"),
        "protocol_version": lock_data.get("protocol_version", "experiment-protocol-v1.1"),
        "protocol_sha256": lock_data.get("protocol_sha256"),
        "code_manifest_sha256": lock_data.get("code_manifest_sha256"),
        "pricing_contract_sha256": EXPECTED_PRICING_CONTRACT_SHA256,
        "total_records": total_records,
        "cumulative_settled_cost_usd": str(cumulative_settled_usd),
        "uncommitted_available_balance_usd": str(uncommitted_avail_usd),
        "has_breach": False,
        "sealed_artifact_digests": sealed_digests,
    }
    if terminal_proof_info is not None:
        seal_payload["terminal_proof"] = {
            "path": terminal_proof_info.get("path"),
            "sha256": terminal_proof_info.get("sha256"),
            "run_id": terminal_proof_info.get("run_id"),
            "task_id": terminal_proof_info.get("task_id"),
            "pid": terminal_proof_info.get("pid"),
            "start_identity": terminal_proof_info.get("start_identity"),
            "process_status": terminal_proof_info.get("process_status"),
            "exit_code": terminal_proof_info.get("exit_code"),
            "artifact_log_sha256": terminal_proof_info.get("artifact_log_sha256"),
            "final_summary": terminal_proof_info.get("final_summary"),
        }
    if protected_baseline_info is not None:
        seal_payload["protected_baseline"] = protected_baseline_info

    output_seal_path.parent.mkdir(parents=True, exist_ok=True)
    output_seal_path.write_bytes(canonical_bytes(seal_payload))
    return seal_payload


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entrypoint for Phase S2 Terminal Run Independent Audit."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Phase S2 Terminal Run Independent Canonical Audit"
    )
    parser.add_argument(
        "--exp-dir",
        type=Path,
        required=True,
        help="Path to experiment artifacts directory",
    )
    parser.add_argument(
        "--study-root",
        type=Path,
        required=True,
        help="Path to study root containing anchor and ledger",
    )
    parser.add_argument(
        "--validator-root",
        type=Path,
        default=REPO_ROOT,
        help="Path to validator root directory",
    )
    parser.add_argument(
        "--launcher-path",
        type=Path,
        default=None,
        help="Path to launcher wrapper script for hash verification",
    )
    parser.add_argument(
        "--seal-path",
        type=Path,
        default=REPO_ROOT / "reports/evidence/canonical_run_seal_v1.json",
        help="Path to output seal file",
    )
    parser.add_argument(
        "--protected-baseline-path",
        type=Path,
        default=None,
        help="Path to protected baseline inventory JSON file",
    )
    parser.add_argument(
        "--terminal-proof-file",
        type=Path,
        default=None,
        help="Authoritative task exit code / PID start identity / absence evidence file",
    )
    parser.add_argument(
        "--expected-run-id",
        type=str,
        default=None,
        help="Expected run ID for terminal proof validation (defaults to manifest run_id)",
    )
    parser.add_argument(
        "--expected-task-id",
        type=str,
        default="task-1264",
        help="Expected task ID for terminal proof validation (default: task-1264)",
    )
    parser.add_argument(
        "--log-file-path",
        type=Path,
        default=None,
        help="Optional explicit path to log file for byte-level hash verification",
    )
    parser.add_argument(
        "--is-production",
        action="store_true",
        default=False,
        help="Require strict 6,400 record production completeness and terminal proof gates",
    )
    args = parser.parse_args(argv)

    terminal_proof_info = None
    protected_baseline_info = None

    if args.is_production:
        print("Enforcing production terminal proof gates...")
        # 1. Lock release gate
        lock_paths = [
            args.exp_dir / ".run.lock",
            args.study_root / "artifacts" / "study_budget" / "study_ledger.lock",
            args.study_root / ".study_anchor.lock",
            args.study_root / "artifacts" / "study_budget" / "study_ledger.json.lock",
            args.study_root / ".study_anchor.json.lock",
        ]
        for lp in lock_paths:
            if lp.exists():
                raise AuditVerificationError(
                    f"Terminal proof failed: active lockfile found at {lp}"
                )

        # 2. Run summary clean exit gate
        summary_path = args.exp_dir / "run_summary.json"
        if not summary_path.exists():
            raise AuditVerificationError(
                f"Terminal proof failed: missing run summary at {summary_path}"
            )
        summary = _strict_json_loads(summary_path.read_bytes())
        if summary.get("complete") is not True:
            raise AuditVerificationError(
                f"Terminal proof failed: run_summary complete={summary.get('complete')}"
            )
        if summary.get("record_count") != 6400:
            raise AuditVerificationError(
                "Terminal proof failed: "
                f"run_summary record_count={summary.get('record_count')} != 6400"
            )
        if summary.get("has_breach") is True:
            raise AuditVerificationError("Terminal proof failed: run_summary reports breach")
        if summary.get("stopped_reason"):
            raise AuditVerificationError(
                f"Terminal proof failed: run was stopped: {summary.get('stopped_reason')}"
            )

        # 3. Terminal proof file gate
        if not args.terminal_proof_file:
            raise AuditVerificationError("Production audit requires --terminal-proof-file")
        manifest_path = args.exp_dir / "manifest.json"
        if manifest_path.exists():
            manifest = _strict_json_loads(manifest_path.read_bytes())
            if manifest.get("execution_mode") != "live":
                raise AuditVerificationError(
                    "Production audit requires execution_mode='live', "
                    f"got '{manifest.get('execution_mode')}'"
                )
            if not manifest.get("run_id") or manifest["run_id"].startswith("fixture-"):
                raise AuditVerificationError(
                    f"Production audit requires live run_id, got '{manifest.get('run_id')}'"
                )
        else:
            manifest = {}

        expected_run_id = args.expected_run_id or manifest.get("run_id") or "live-66b94b1676bf46a9"
        expected_task_id = args.expected_task_id
        terminal_proof_info = audit_terminal_process_proof(
            args.terminal_proof_file,
            expected_run_id=expected_run_id if manifest_path.exists() or args.expected_run_id else None,
            expected_task_id=expected_task_id,
            log_file_path=args.log_file_path,
            expected_execution_mode="live" if manifest.get("execution_mode") == "live" else None,
            expected_record_count=6400 if manifest_path.exists() else None,
            require_log_file=True if manifest_path.exists() else False,
        )

        # 4. Launcher wrapper requirement
        launcher_wrapper = args.launcher_path or (
            args.study_root / "scripts" / "run_experiments.py"
        )
        if not launcher_wrapper.exists():
            raise AuditVerificationError(
                f"Terminal proof failed: launcher wrapper script missing at {launcher_wrapper}"
            )

        # 5. Production execution mode and manifest validation
        if not manifest_path.exists():
            raise AuditVerificationError(f"Missing manifest file at {manifest_path}")

        # 6. Native preloader and recovery-aware lifecycle validation
        eval_inputs = audit_production_preloader_and_lifecycle(
            args.validator_root, args.exp_dir, manifest
        )
        prod_registry_ids = set(eval_inputs.registry.keys())
        prod_corpus_ids = set(eval_inputs.corpus_ids)

        # 7. Protected 22 baseline gate
        protected_baseline_info = audit_protected_baseline_22_files(
            args.validator_root, args.protected_baseline_path
        )
    else:
        launcher_wrapper = args.launcher_path
        terminal_proof_info = (
            audit_terminal_process_proof(
                args.terminal_proof_file,
                expected_run_id=args.expected_run_id,
                expected_task_id=args.expected_task_id,
            )
            if args.terminal_proof_file and args.terminal_proof_file.exists()
            else None
        )
        base_path = args.protected_baseline_path or (
            args.validator_root
            / "artifacts"
            / "orchestration"
            / "integration_protected_baseline.json"
        )
        protected_baseline_info = (
            audit_protected_baseline_22_files(args.validator_root, base_path)
            if base_path.exists()
            else None
        )
        prod_registry_ids = None
        prod_corpus_ids = None

    plan = load_plan(args.validator_root / "config" / "experiment_config.json")
    expected_ids = {s.sample_id for s in plan.samples}

    print(f"Auditing completeness and cardinality in {args.exp_dir}...")
    records = audit_completeness_and_cardinality(
        args.exp_dir,
        expected_ids,
        require_all_conditions=args.is_production,
        registry_ids=prod_registry_ids,
        corpus_ids=prod_corpus_ids,
    )
    print(f"Verified {len(records)} total records.")

    print("Auditing request journal lifecycle and receipt joins...")
    receipts, settles = audit_journal_join_and_lifecycle(args.exp_dir, records)

    print("Auditing study budget ledger and tariff recomputations...")
    settled_usd, avail_usd = audit_financial_ledger_and_tariffs(
        args.study_root, args.validator_root, records, receipts, settles
    )
    print(f"Financial verification clean: settled=${settled_usd}, available=${avail_usd}")

    print("Auditing provenance, lockfiles, and canary hash invariants...")
    audit_provenance_and_hash_invariants(
        args.validator_root,
        args.exp_dir,
        records,
        launcher_wrapper_path=launcher_wrapper,
        is_production=args.is_production,
    )

    print("Auditing secret sanitization...")
    files_to_scan = (
        list(args.exp_dir.glob("*.json"))
        + list(args.exp_dir.glob("*.jsonl"))
        + [
            args.study_root / ".study_anchor.json",
            args.study_root / "artifacts" / "study_budget" / "study_ledger.json",
        ]
    )
    audit_secret_sanitization([p for p in files_to_scan if p.exists()])

    print(f"Generating audit seal at {args.seal_path}...")
    seal = generate_audit_seal(
        args.exp_dir,
        args.study_root,
        args.validator_root,
        args.seal_path,
        records,
        settled_usd,
        avail_usd,
        is_production=args.is_production,
        terminal_proof_info=terminal_proof_info,
        protected_baseline_info=protected_baseline_info,
    )
    seal_type = seal["seal_type"]
    digests_count = len(seal["sealed_artifact_digests"])
    print(f"AUDIT SUCCESS: Seal generated ({seal_type}) with {digests_count} locked digests.")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
