"""Comprehensive Offline Analysis for Research Questions RQ1, RQ2, and RQ3.

Computes:
- RQ1: Controlled comparison of No-RAG vs RAG (k=1, 3, 5, 10) on exact technique attribution,
  with delta metrics, relative gains, McNemar significance tests, and pair-cluster bootstrap CIs.
- RQ2: Retrieval vs. Generation error decomposition, measuring retrieval Recall@k,
  downstream generation accuracy conditioned on retrieval success, and failure source attribution.
- RQ3: Retrieval depth ablation (k in 1, 3, 5, 10 vs 0), latency, token expenditure, monetary
  costs (pricing-v1 tariffs), full ledger/journal reconciliation, explicit cost denominators,
  and paired Single-View vs Contextual-View diagnostics.

Secondary statistical tests (McNemar test, pair-cluster bootstrap CIs) are exploratory diagnostics
accounting for intra-pair correlation; they do not alter frozen headline protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

import numpy as np

# Support direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.evaluation.experiment_metrics import (
    CONDITIONS,
    EvaluationInputs,
    canonical_json_bytes,
    compute_condition_metrics,
    compute_failure_decomposition,
    compute_retrieval_conditional_metrics,
    load_evaluation_inputs,
)
from src.experiment.authorization import ScientificProtocolApproval
from src.experiment.monetary_ledger import (
    _strict_json_loads,
    calculate_attempt_token_cost,
    calculate_request_cost_from_receipts,
    compute_pricing_contract_sha256,
    load_pricing_config,
    round_cost_up,
    round_credit_down,
    validate_finite_nonnegative_money,
    validate_token_count,
)

ANALYSIS_TOOL_VERSION = "1.2.0"


# ---------------------------------------------------------------------------
# Strict Pricing & Financial Ledger Reconciliation Helpers
# ---------------------------------------------------------------------------


def validate_pricing_config(pricing_config: dict[str, Any]) -> dict[str, Any]:
    """Strictly validate the pricing configuration against pricing-v1 contract.

    Invariants:
    - Rejects missing tariffs or missing 'default' service tier.
    - Requires 'short' and 'long' context tables with all 4 per-million rates.
    - Requires reservation_bounds with positive default_attempt_worst_usd and
      default_logical_worst_usd.
    - Requires ceilings with positive integers max_input_tokens, max_output_tokens,
      short_context_limit.
    - Requires total_study_budget_usd.
    - Programming errors propagate; never falls back to zero or default tier silently.
    """
    if not isinstance(pricing_config, dict):
        raise ValueError(f"Pricing config must be a dict, got {type(pricing_config).__name__}")

    tariffs = pricing_config.get("tariffs")
    if not isinstance(tariffs, dict) or "default" not in tariffs:
        raise ValueError("Pricing config missing 'tariffs' or 'default' service tier")

    for tier_name, tier_dict in tariffs.items():
        if not isinstance(tier_dict, dict):
            raise ValueError(f"Tariff for tier '{tier_name}' must be a dict")
        for ctx in ("short", "long"):
            if ctx not in tier_dict:
                raise ValueError(f"Tariff for tier '{tier_name}' missing '{ctx}' context rates")
            rates = tier_dict[ctx]
            for rate_key in (
                "input_per_million",
                "output_per_million",
                "cache_read_per_million",
                "cache_write_per_million",
            ):
                if rate_key not in rates:
                    raise ValueError(f"Tariff '{tier_name}.{ctx}' missing rate '{rate_key}'")
                try:
                    val = Decimal(str(rates[rate_key]))
                    if val < 0:
                        raise ValueError(
                            f"Rate '{rate_key}' in '{tier_name}.{ctx}' cannot be negative"
                        )
                except Exception as exc:
                    raise ValueError(
                        f"Invalid rate '{rate_key}' in tariff '{tier_name}.{ctx}': {exc}"
                    )

    bounds = pricing_config.get("reservation_bounds")
    if not isinstance(bounds, dict):
        raise ValueError("Pricing config missing 'reservation_bounds'")
    for b_key in ("default_attempt_worst_usd", "default_logical_worst_usd"):
        if b_key not in bounds:
            raise ValueError(f"Missing required reservation bound '{b_key}'")
        val = Decimal(str(bounds[b_key]))
        if val <= 0:
            raise ValueError(f"Reservation bound '{b_key}' must be positive")

    ceilings = pricing_config.get("ceilings")
    if not isinstance(ceilings, dict):
        raise ValueError("Pricing config missing 'ceilings'")
    for c_key in ("max_input_tokens", "max_output_tokens", "short_context_limit"):
        if c_key not in ceilings or not isinstance(ceilings[c_key], int) or ceilings[c_key] <= 0:
            raise ValueError(f"Ceilings missing positive integer '{c_key}'")

    if "total_study_budget_usd" not in pricing_config:
        raise ValueError("Pricing config missing 'total_study_budget_usd'")

    return pricing_config


class RecordObjectAdapter:
    """Adapts a dictionary record from run.jsonl to an object interface with attribute access."""

    def __init__(self, data: Optional[dict[str, Any]]):
        self._data = data or {}

    def __getattr__(self, name: str) -> Any:
        if name in self._data:
            return self._data[name]
        raise AttributeError(f"RecordObjectAdapter has no attribute {name}")


def reconcile_journal_and_ledger(
    records: Sequence[Mapping[str, Any]],
    pricing_config: dict[str, Any],
    *,
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Reconcile request journal attempt receipts and monetary settlements by sample/condition.

    Invariants (B_RECONCILE_REPAIR2):
    1. Read-only validation of supplied study ledger data/bytes against prediction records
       and journal.
    2. Enforce exact journal header/manifest binding, valid keys, complete matrix coverage,
       and reject missing/foreign/extra/duplicate settlements and receipts.
    3. Recompute per-request costs from attempt receipts using native tariff model, retries,
       worst-case missing usage charges, cached usage, and returned tier. Disagreements fail closed.
    4. Interpret reservation lifecycle: complete does NOT release hold; monetary_settle /
       cancel_orphan / cancel_hold does. Read native amount_usd on monetary_cancel_orphan.
    5. Whole-study accounting retains pilot hold, cumulative settled cost, active/orphan holds
       and balance conservation; canonical per-condition costs exclude pilot hold.
    """
    validate_pricing_config(pricing_config)

    records_by_key = {(r["sample_id"], r["condition"]): r for r in records}
    expected_keys = set(records_by_key.keys())

    record_manifest_shas = {
        r.get("manifest_sha256") for r in records if r.get("manifest_sha256") is not None
    }

    # Load journal events
    events: Optional[list[dict[str, Any]]] = None
    if journal_events is not None:
        events = list(journal_events)
    elif journal_path is not None:
        jp = Path(journal_path)
        if jp.is_file():
            raw_lines = jp.read_text(encoding="utf-8").splitlines()
            events = [_strict_json_loads(line) for line in raw_lines if line.strip()]
        else:
            raise FileNotFoundError(f"Journal file not found: {jp}")

    # Load study ledger data (read-only)
    ledger: Optional[dict[str, Any]] = None
    if study_ledger_data is not None:
        ledger = study_ledger_data
    elif study_ledger_path is not None:
        lp = Path(study_ledger_path)
        if lp.is_file():
            ledger = _strict_json_loads(lp.read_bytes())
        else:
            raise FileNotFoundError(f"Study ledger file not found: {lp}")

    if events is None and ledger is None:
        return {
            "journal_present": False,
            "ledger_present": False,
            "receipts_by_condition": {c: [] for c in CONDITIONS},
            "settlements_by_condition": {c: {} for c in CONDITIONS},
            "receipts_cost_by_condition": {c: None for c in CONDITIONS},
            "settled_cost_by_condition": {c: None for c in CONDITIONS},
            "token_estimated_cost_by_condition": {c: None for c in CONDITIONS},
            "retried_attempts_by_condition": {c: 0 for c in CONDITIONS},
            "active_reservations_usd": Decimal("0.0"),
            "orphan_reservations_usd": Decimal("0.0"),
            "has_breach": False,
            "breach_reasons": [],
            "ledger_verified": False,
        }

    if events is None:
        events = []

    header_found = False
    header_manifest_sha = None
    active_reservations: dict[tuple[str, str], Decimal] = {}
    receipts_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    settlements_by_key: dict[tuple[str, str], dict[str, Any]] = {}
    completed_keys: set[tuple[str, str]] = set()
    all_receipt_ordinals: list[int] = []
    orphan_reservations_usd = Decimal("0.0")
    cancelled_holds_usd = Decimal("0.0")
    has_breach = False
    breach_reasons: list[str] = []

    for event in events:
        kind = event.get("event")
        if not isinstance(kind, str):
            raise ValueError(f"Event missing or invalid 'event' type: {event}")

        if kind == "header":
            if header_found:
                raise ValueError("Duplicate header event in journal")
            header_found = True
            header_manifest_sha = event.get("manifest_sha256")
            if not isinstance(header_manifest_sha, str) or len(header_manifest_sha) != 64:
                raise ValueError(f"Invalid journal header manifest_sha256: {header_manifest_sha}")
            if record_manifest_shas and any(m != header_manifest_sha for m in record_manifest_shas):
                raise ValueError(
                    f"Journal header manifest_sha256 mismatch with records: "
                    f"header={header_manifest_sha} != records={record_manifest_shas}"
                )
            continue

        key_raw = event.get("key")
        if key_raw is None:
            continue

        if not (
            isinstance(key_raw, (list, tuple))
            and len(key_raw) == 2
            and isinstance(key_raw[0], str)
            and isinstance(key_raw[1], str)
        ):
            raise ValueError(f"Invalid event key structure: {key_raw}")
        key = (key_raw[0], key_raw[1])

        # Reject foreign conditions or foreign keys for completion/settlement/receipts
        if key[1] not in CONDITIONS:
            raise ValueError(f"Invalid condition in journal event key: {key}")
        if (
            kind in ("attempt_receipt", "complete", "monetary_settle")
            and records
            and key not in expected_keys
        ):
            raise ValueError(f"Foreign/extra key in journal event: {key}")

        if kind == "monetary_reserve":
            amt_val = validate_finite_nonnegative_money(
                event.get("amount_usd"), f"reserve amount for {key}"
            )
            amt_round = round_cost_up(amt_val)
            if amt_round <= Decimal("0.0"):
                raise ValueError(f"monetary_reserve amount must be strictly positive: {amt_round}")
            if key in active_reservations:
                raise ValueError(f"Duplicate active monetary_reserve for key: {key}")
            active_reservations[key] = amt_round

        elif kind == "attempt_receipt":
            ord_val = event.get("ordinal")
            if not isinstance(ord_val, int) or isinstance(ord_val, bool) or ord_val <= 0:
                raise ValueError(
                    f"attempt_receipt ordinal must be positive integer, got: {ord_val}"
                )
            all_receipt_ordinals.append(ord_val)

            idx_val = event.get("attempt_index")
            if not isinstance(idx_val, int) or isinstance(idx_val, bool) or idx_val < 0:
                raise ValueError(
                    f"attempt_receipt attempt_index must be non-negative integer, got: {idx_val}"
                )

            existing_receipts = receipts_by_key[key]
            if any(r.get("attempt_index") == idx_val for r in existing_receipts):
                raise ValueError(f"Duplicate attempt_index {idx_val} for key: {key}")

            p_tok = validate_token_count(event.get("input_tokens"), "input_tokens")
            c_tok = validate_token_count(event.get("output_tokens"), "output_tokens")
            ca_tok = validate_token_count(event.get("cached_tokens"), "cached_tokens")
            if ca_tok is not None and p_tok is not None and ca_tok > p_tok:
                raise ValueError(f"cached_tokens ({ca_tok}) cannot exceed input_tokens ({p_tok})")

            receipts_by_key[key].append(dict(event))

        elif kind == "complete":
            completed_keys.add(key)
            rec_sha = event.get("record_sha256")
            if not isinstance(rec_sha, str) or len(rec_sha) != 64:
                raise ValueError(
                    f"complete event missing valid record_sha256 for key {key}: {rec_sha}"
                )
            if key in records_by_key:
                exp_sha = hashlib.sha256(canonical_json_bytes(records_by_key[key])).hexdigest()
                if rec_sha != exp_sha:
                    raise ValueError(
                        f"complete record_sha256 mismatch for key {key}: {rec_sha} != {exp_sha}"
                    )
            # NOTE: complete does NOT release hold!

        elif kind == "monetary_settle":
            if key in settlements_by_key:
                raise ValueError(f"Duplicate monetary_settle event for key: {key}")

            cost_val = validate_finite_nonnegative_money(
                event.get("cost_usd"), f"settle cost for {key}"
            )
            refund_val = validate_finite_nonnegative_money(
                event.get("refund_usd"), f"settle refund for {key}"
            )
            cost_round = round_cost_up(cost_val)
            refund_round = round_credit_down(refund_val)

            if key not in active_reservations:
                raise ValueError(f"monetary_settle for unreserved key {key}")
            held = active_reservations.pop(key)
            if round_cost_up(cost_round + refund_round) != held:
                raise ValueError(
                    f"Settlement conservation mismatch for key {key}: "
                    f"cost {cost_round} + refund {refund_round} != held {held}"
                )

            settle_sha = event.get("record_sha256")
            if not isinstance(settle_sha, str) or len(settle_sha) != 64:
                raise ValueError(
                    f"Invalid record_sha256 in monetary_settle for key {key}: {settle_sha}"
                )

            if key in records_by_key:
                exp_sha = hashlib.sha256(canonical_json_bytes(records_by_key[key])).hexdigest()
                if settle_sha != exp_sha:
                    raise ValueError(
                        f"Monetary settle record_sha256 mismatch for key {key}: "
                        f"{settle_sha} != {exp_sha}"
                    )

            if event.get("breach", False):
                has_breach = True
                breach_reasons.append(str(event.get("breach_reason", f"Monetary breach on {key}")))

            settlements_by_key[key] = {
                "cost_usd": str(cost_round),
                "refund_usd": str(refund_round),
                "record_sha256": settle_sha,
                "breach": bool(event.get("breach", False)),
                "breach_reason": event.get("breach_reason"),
            }

        elif kind == "monetary_cancel_orphan":
            amt_val = validate_finite_nonnegative_money(
                event.get("amount_usd"), f"cancel orphan amount for {key}"
            )
            amt_round = round_cost_up(amt_val)
            if key in active_reservations:
                held = active_reservations.pop(key)
                if held != amt_round:
                    raise ValueError(
                        f"Cancel orphan amount mismatch for {key}: hold {held} != {amt_round}"
                    )
            orphan_reservations_usd += amt_round

        elif kind in ("monetary_cancel_hold", "cancel_hold"):
            amt_val = validate_finite_nonnegative_money(
                event.get("amount_usd", "0.0"), f"cancel hold for {key}"
            )
            amt_round = round_cost_up(amt_val)
            if key in active_reservations:
                held = active_reservations.pop(key)
                if held != amt_round and amt_val > Decimal("0.0"):
                    raise ValueError(
                        f"Cancel hold amount mismatch for {key}: hold {held} != {amt_round}"
                    )
            cancelled_holds_usd += amt_round

    # Enforce header on completed run with records
    if events and not header_found and any(r.get("manifest_sha256") for r in records):
        raise ValueError("Journal missing header event with manifest_sha256")

    # Ordinal sequence verification
    if all_receipt_ordinals:
        if len(set(all_receipt_ordinals)) != len(all_receipt_ordinals):
            raise ValueError("Duplicate attempt_receipt ordinal detected")
        sorted_ords = sorted(all_receipt_ordinals)
        if sorted_ords and sorted_ords[0] != 1:
            raise ValueError(f"Attempt receipt ordinals must start at 1, got: {sorted_ords[0]}")
        for i in range(len(sorted_ords) - 1):
            if sorted_ords[i + 1] != sorted_ords[i] + 1:
                raise ValueError(
                    f"Non-contiguous attempt_receipt ordinals: "
                    f"{sorted_ords[i]} -> {sorted_ords[i + 1]}"
                )

    # Complete-without-settle check
    complete_unsettled = completed_keys - set(settlements_by_key.keys())
    if complete_unsettled:
        raise ValueError(f"Complete-without-settle detected for keys: {complete_unsettled}")

    # Complete coverage of records on completed run
    if records and (settlements_by_key or receipts_by_key):
        for key in expected_keys:
            if key not in completed_keys:
                raise ValueError(f"Missing complete event for record key: {key}")
            if key not in settlements_by_key:
                raise ValueError(f"Missing monetary_settle for record key: {key}")
            if key not in receipts_by_key:
                raise ValueError(f"Missing attempt_receipt for record key: {key}")

    if active_reservations:
        completed_still_reserved = completed_keys & set(active_reservations.keys())
        if completed_still_reserved:
            raise ValueError(
                f"Completed requests with unsettled active reservations: {completed_still_reserved}"
            )

    # Per-request cost recalculation and settlement binding via native contract
    recomputed_costs_by_key: dict[tuple[str, str], Decimal] = {}
    for key, r_list in receipts_by_key.items():
        r_list_sorted = sorted(r_list, key=lambda r: r.get("attempt_index", 0))
        attempts_consumed = len(r_list_sorted)

        rec = records_by_key.get(key)
        rec_adapter = RecordObjectAdapter(rec) if rec is not None else None

        last_ordinal = r_list_sorted[-1].get("ordinal") if r_list_sorted else None
        exp_model = (
            pricing_config.get("expected_model")
            or (rec.get("model") if rec else None)
            or pricing_config.get("model")
            or "gpt-5.6-luna"
        )

        req_cost, req_breach, breach_reason = calculate_request_cost_from_receipts(
            attempts_consumed=attempts_consumed,
            receipts=r_list_sorted,
            record=rec_adapter,
            pricing_config=pricing_config,
            tier=pricing_config.get("service_tier", "default"),
            expected_model=exp_model,
            most_recent_attempt_ordinal=last_ordinal,
        )

        if req_breach:
            raise ValueError(f"Request {key} native contract breach: {breach_reason}")

        recomputed_costs_by_key[key] = req_cost

        if key in settlements_by_key:
            j_cost = Decimal(str(settlements_by_key[key]["cost_usd"]))
            if j_cost != req_cost:
                raise ValueError(
                    f"Journal settlement cost mismatch for key {key}: "
                    f"journal_settlement={j_cost} != computed_from_receipts={req_cost}"
                )

    # Study Ledger verification
    ledger_verified = False
    if ledger is not None:
        ledger_verified = True
        pricing_sha = compute_pricing_contract_sha256(pricing_config)
        if "pricing_contract_sha256" in ledger and ledger["pricing_contract_sha256"] != pricing_sha:
            raise ValueError(
                f"Pricing contract mismatch in study ledger: "
                f"{ledger['pricing_contract_sha256']} != {pricing_sha}"
            )

        settled_records = ledger.get("settled_records", {})
        if not isinstance(settled_records, dict):
            raise ValueError("Study ledger missing or invalid 'settled_records' dictionary")

        for l_key_raw in settled_records.keys():
            if ":" in l_key_raw:
                parts = l_key_raw.split(":", 1)
            elif "_" in l_key_raw:
                parts = l_key_raw.rsplit("_", 1)
            else:
                parts = [l_key_raw, ""]
            l_tuple_key = (parts[0], parts[1])
            if records and l_tuple_key not in expected_keys:
                raise ValueError(f"Foreign ledger settlement key: {l_key_raw}")

        for key, rec in records_by_key.items():
            sid, cond = key
            key_str = f"{sid}:{cond}"
            if key_str not in settled_records:
                alt_key = str(list(key))
                if alt_key in settled_records:
                    l_entry = settled_records[alt_key]
                else:
                    raise ValueError(f"Study ledger missing settled record for key {key_str}")
            else:
                l_entry = settled_records[key_str]

            if not isinstance(l_entry, dict):
                raise ValueError(f"Study ledger settled_records[{key_str}] must be dict")

            exp_sha = hashlib.sha256(canonical_json_bytes(rec)).hexdigest()
            l_sha = l_entry.get("record_sha256")
            if l_sha != exp_sha:
                raise ValueError(
                    f"Study ledger record_sha256 mismatch for {key_str}: {l_sha} != {exp_sha}"
                )

            l_cost = round_cost_up(
                validate_finite_nonnegative_money(
                    l_entry.get("cost_usd"), f"ledger cost for {key_str}"
                )
            )
            if key in settlements_by_key:
                j_cost = Decimal(str(settlements_by_key[key]["cost_usd"]))
                if l_cost != j_cost:
                    raise ValueError(
                        f"Study ledger cost mismatch for {key_str}: "
                        f"ledger={l_cost} != journal={j_cost}"
                    )

            if "refund_usd" in l_entry and key in settlements_by_key:
                l_ref = round_credit_down(
                    validate_finite_nonnegative_money(
                        l_entry.get("refund_usd"), f"ledger refund for {key_str}"
                    )
                )
                j_ref = Decimal(str(settlements_by_key[key]["refund_usd"]))
                if l_ref != j_ref:
                    raise ValueError(
                        f"Study ledger refund mismatch for {key_str}: "
                        f"ledger={l_ref} != journal={j_ref}"
                    )

        # Balance conservation
        if "total_budget_usd" in ledger:
            tot_b = validate_finite_nonnegative_money(
                ledger["total_budget_usd"], "total_budget_usd"
            )
            pilot_h = validate_finite_nonnegative_money(
                ledger.get("prior_pilot_provisional_hold_usd", "0.0"), "pilot_hold"
            )
            cum_settled = validate_finite_nonnegative_money(
                ledger.get("cumulative_settled_cost_usd", "0.0"), "cumulative_settled"
            )
            act_res = validate_finite_nonnegative_money(
                ledger.get("active_reservations_usd", "0.0"), "active_reservations"
            )
            avail_b = validate_finite_nonnegative_money(
                ledger.get("uncommitted_available_balance_usd", "0.0"), "available_balance"
            )
            expected_avail = round_credit_down(tot_b - pilot_h - cum_settled - act_res)
            if avail_b != expected_avail:
                raise ValueError(
                    f"Study ledger balance conservation drift: available={avail_b} != "
                    f"expected={expected_avail} (total={tot_b} - pilot={pilot_h} - "
                    f"settled={cum_settled} - active={act_res})"
                )

    # Condition aggregation
    receipts_cost_by_cond: dict[str, Optional[Decimal]] = {}
    settled_cost_by_cond: dict[str, Optional[Decimal]] = {}
    token_est_cost_by_cond: dict[str, Optional[Decimal]] = {}
    retried_attempts_by_cond: dict[str, int] = {}

    for cond in CONDITIONS:
        cond_records = [r for r in records if r["condition"] == cond]
        t_est = Decimal("0.0")
        for r in cond_records:
            p_tok = r.get("prompt_tokens")
            c_tok = r.get("completion_tokens")
            t_est += calculate_attempt_token_cost(p_tok, c_tok, pricing_config)
        token_est_cost_by_cond[cond] = round_cost_up(t_est)

        cond_receipt_keys = [k for k in recomputed_costs_by_key if k[1] == cond]
        if cond_receipt_keys:
            receipts_cost_by_cond[cond] = round_cost_up(
                sum(recomputed_costs_by_key[k] for k in cond_receipt_keys)
            )
            retried_count = sum(
                1
                for k in cond_receipt_keys
                for r in receipts_by_key[k]
                if r.get("attempt_index", 0) > 0
            )
            retried_attempts_by_cond[cond] = retried_count
        else:
            receipts_cost_by_cond[cond] = None
            retried_attempts_by_cond[cond] = 0

        cond_settle_keys = [k for k in settlements_by_key if k[1] == cond]
        if cond_settle_keys:
            settled_cost_by_cond[cond] = round_cost_up(
                sum(Decimal(str(settlements_by_key[k]["cost_usd"])) for k in cond_settle_keys)
            )
        else:
            settled_cost_by_cond[cond] = None

    active_res_sum = (
        round_cost_up(sum(active_reservations.values())) if active_reservations else Decimal("0.0")
    )

    return {
        "journal_present": bool(events),
        "ledger_present": ledger is not None,
        "receipts_by_condition": receipts_by_key,
        "settlements_by_condition": settlements_by_key,
        "receipts_cost_by_condition": receipts_cost_by_cond,
        "settled_cost_by_condition": settled_cost_by_cond,
        "token_estimated_cost_by_condition": token_est_cost_by_cond,
        "retried_attempts_by_condition": retried_attempts_by_cond,
        "active_reservation_count": len(active_reservations),
        "active_reservations_usd": active_res_sum,
        "orphan_reservations_usd": orphan_reservations_usd,
        "orphan_cancellations_usd": orphan_reservations_usd,
        "has_breach": has_breach,
        "breach_reasons": breach_reasons,
        "ledger_verified": ledger_verified,
    }


# ---------------------------------------------------------------------------
# Statistical Testing Helpers (with Pair-Cluster Resampling)
# ---------------------------------------------------------------------------


def compute_mcnemar_test(
    y_baseline: Sequence[bool],
    y_treatment: Sequence[bool],
) -> dict[str, Any]:
    """Compute McNemar test on paired binary classification outcomes.

    Contingency table:
      a: both correct (1, 1)
      b: treatment correct, baseline incorrect (1, 0) -> treatment win (discordant)
      c: treatment incorrect, baseline correct (0, 1) -> baseline win (discordant)
      d: both incorrect (0, 0)

    Calculates:
      - Chi-squared statistic with Edwards continuity correction:
        chi2 = (|b - c| - 1)^2 / (b + c) if (b + c) > 0 and |b - c| >= 1 else 0.0
      - Asymptotic p-value from chi2(df=1)
      - Exact two-sided binomial p-value for B(b + c, 0.5)
    """
    if len(y_baseline) != len(y_treatment):
        raise ValueError(
            f"Length mismatch for paired McNemar test: {len(y_baseline)} vs {len(y_treatment)}"
        )

    n = len(y_baseline)
    a = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if y_b and y_t)
    b = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if not y_b and y_t)
    c = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if y_b and not y_t)
    d = sum(1 for y_b, y_t in zip(y_baseline, y_treatment) if not y_b and not y_t)

    disc = b + c
    diff = abs(b - c)

    if disc == 0:
        chi2 = 0.0
        p_val_asymp = 1.0
        p_val_exact = 1.0
    else:
        num = max(0.0, float(diff - 1)) ** 2
        chi2 = num / disc
        p_val_asymp = float(math.erfc(math.sqrt(chi2) / math.sqrt(2.0)))

        k_min = min(b, c)
        prob_tail = sum(math.comb(disc, k) * (0.5**disc) for k in range(k_min + 1))
        p_val_exact = min(1.0, 2.0 * prob_tail)

    return {
        "contingency_table": {
            "total_pairs": n,
            "both_correct_a": a,
            "treatment_win_b": b,
            "baseline_win_c": c,
            "both_incorrect_d": d,
            "total_discordant": disc,
        },
        "chi2_statistic": chi2,
        "p_value_asymptotic": p_val_asymp,
        "p_value_exact": p_val_exact,
        "significant_at_05": p_val_exact < 0.05,
        "significant_at_01": p_val_exact < 0.01,
    }


def compute_paired_bootstrap_ci(
    scores_treatment: Sequence[float],
    scores_baseline: Sequence[float],
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical bootstrap CI for paired differences with pair-cluster resampling.

    When cluster_ids (e.g. pair_id) are provided, resamples clusters with replacement so that
    views sharing a pair_id are sampled together, preserving intra-pair correlation.
    """
    n = len(scores_treatment)
    if n == 0 or len(scores_baseline) != n:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean_delta": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
            "resampling_method": "pair_cluster_bootstrap" if cluster_ids else "paired_bootstrap",
        }

    arr_treat = np.array(scores_treatment, dtype=np.float64)
    arr_base = np.array(scores_baseline, dtype=np.float64)
    rng = np.random.default_rng(seed)
    deltas = np.empty(num_samples, dtype=np.float64)

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            deltas[i] = np.mean(arr_treat[sampled_indices]) - np.mean(arr_base[sampled_indices])

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            deltas[i] = np.mean(arr_treat[indices]) - np.mean(arr_base[indices])

        resampling_method = "paired_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(deltas, lower_pct)),
        "ci_upper": float(np.percentile(deltas, upper_pct)),
        "mean_delta": float(np.mean(deltas)),
        "std_error": float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
    }


def compute_single_bootstrap_ci(
    scores: Sequence[float],
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute empirical percentile bootstrap CI for a single metric series with pair-clustering."""
    n = len(scores)
    if n == 0:
        return {
            "ci_lower": None,
            "ci_upper": None,
            "mean": None,
            "std_error": None,
            "num_samples": num_samples,
            "alpha": alpha,
            "resampling_method": "pair_cluster_bootstrap" if cluster_ids else "single_bootstrap",
        }

    arr = np.array(scores, dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = np.empty(num_samples, dtype=np.float64)

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            means[i] = np.mean(arr[sampled_indices])

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            means[i] = np.mean(arr[indices])

        resampling_method = "single_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(means, lower_pct)),
        "ci_upper": float(np.percentile(means, upper_pct)),
        "mean": float(np.mean(means)),
        "std_error": float(np.std(means, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
    }


def compute_macro_f1_bootstrap_ci(
    records_treat: Sequence[Mapping[str, Any]],
    records_base: Sequence[Mapping[str, Any]],
    ground_truth: Mapping[str, tuple[str, ...]],
    universe_size: int = 474,
    *,
    cluster_ids: Optional[Sequence[str]] = None,
    num_samples: int = 1000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute bootstrap CI for paired delta in Macro-F1 across 474 classes with pair-clustering."""
    n = len(records_treat)
    if n == 0 or len(records_base) != n:
        return {"ci_lower": None, "ci_upper": None, "mean_delta": None}

    treat_pairs = [
        (
            r["sample_id"],
            r.get("parsed_technique_ids", [None])[0] if r["parse_status"] == "VALID" else None,
            set(ground_truth.get(r["sample_id"], ())),
        )
        for r in records_treat
    ]
    base_pairs = [
        (
            r["sample_id"],
            r.get("parsed_technique_ids", [None])[0] if r["parse_status"] == "VALID" else None,
            set(ground_truth.get(r["sample_id"], ())),
        )
        for r in records_base
    ]

    def _calc_fast_macro_f1(pairs_subset: Sequence[tuple[str, Optional[str], set[str]]]) -> float:
        active_classes: set[str] = set()
        for _, pred, gt in pairs_subset:
            if pred:
                active_classes.add(pred)
            active_classes.update(gt)

        if not active_classes or universe_size <= 0:
            return 0.0

        f1_sum = 0.0
        for tid in active_classes:
            tp = sum(1 for _, pred, gt in pairs_subset if pred == tid and tid in gt)
            fp = sum(1 for _, pred, gt in pairs_subset if pred == tid and tid not in gt)
            fn = sum(1 for _, pred, gt in pairs_subset if tid in gt and pred != tid)

            if tp + fp == 0 and tp + fn == 0:
                continue
            prec = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            rec = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
            f1_sum += f1

        return f1_sum / universe_size

    rng = np.random.default_rng(seed)
    deltas = np.empty(num_samples, dtype=np.float64)

    if cluster_ids is not None and len(cluster_ids) == n:
        clusters_map: dict[str, list[int]] = defaultdict(list)
        for idx, cid in enumerate(cluster_ids):
            clusters_map[cid].append(idx)
        cluster_list = list(clusters_map.values())
        num_clusters = len(cluster_list)

        for i in range(num_samples):
            sampled_c_indices = rng.integers(0, num_clusters, size=num_clusters)
            sampled_indices = [idx for c_idx in sampled_c_indices for idx in cluster_list[c_idx]]
            sub_t = [treat_pairs[idx] for idx in sampled_indices]
            sub_b = [base_pairs[idx] for idx in sampled_indices]
            deltas[i] = _calc_fast_macro_f1(sub_t) - _calc_fast_macro_f1(sub_b)

        resampling_method = "pair_cluster_bootstrap"
        cluster_count = num_clusters
    else:
        for i in range(num_samples):
            indices = rng.integers(0, n, size=n)
            sub_t = [treat_pairs[idx] for idx in indices]
            sub_b = [base_pairs[idx] for idx in indices]
            deltas[i] = _calc_fast_macro_f1(sub_t) - _calc_fast_macro_f1(sub_b)

        resampling_method = "paired_bootstrap"
        cluster_count = n

    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    return {
        "ci_lower": float(np.percentile(deltas, lower_pct)),
        "ci_upper": float(np.percentile(deltas, upper_pct)),
        "mean_delta": float(np.mean(deltas)),
        "std_error": float(np.std(deltas, ddof=1)) if num_samples > 1 else 0.0,
        "num_samples": num_samples,
        "alpha": alpha,
        "resampling_method": resampling_method,
        "cluster_count": cluster_count,
    }


# ---------------------------------------------------------------------------
# RQ1 Analysis: Controlled Comparison (No-RAG vs RAG)
# ---------------------------------------------------------------------------


def compute_rq1(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
    *,
    bootstrap_samples: int = 1000,
    seed: int = 42,
) -> dict[str, Any]:
    """Compute RQ1: Controlled comparison of No-RAG vs RAG (k=1,3,5,10) on technique attribution.

    Evaluates:
      - End-to-end accuracy, Valid-output accuracy, Macro-F1 across 474-class universe.
      - Delta vs No-RAG baseline (both absolute and relative percentage gain).
      - Statistical significance via paired McNemar test and pair-cluster bootstrap CIs.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    scorable_by_cond: dict[str, list[dict[str, Any]]] = {}
    correctness_by_cond_sample: dict[str, dict[str, bool]] = {}
    sample_pair_map: dict[str, str] = {}

    for cond in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = []
        sample_correctness = {}

        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")

            is_scorable = False
            if status == "ambiguous":
                is_scorable = protocol.d2c_ambiguous_ground_truth != "EXCLUDE"
            elif status == "unmapped" or not gt:
                is_scorable = protocol.d2b_empty_ground_truth == "TREAT_AS_NEGATIVE"
            else:
                is_scorable = True

            if is_scorable:
                scorable_records.append(r)
                is_correct = (
                    r["parse_status"] == "VALID"
                    and bool(r.get("parsed_technique_ids"))
                    and r["parsed_technique_ids"][0] in set(gt)
                )
                sample_correctness[sid] = is_correct
                sample_pair_map[sid] = r.get("pair_id") or sid

        scorable_by_cond[cond] = scorable_records
        correctness_by_cond_sample[cond] = sample_correctness

    base_cond = "no_rag"
    base_metrics = condition_metrics[base_cond]
    base_correctness = correctness_by_cond_sample[base_cond]
    common_scorable_sids = sorted(base_correctness.keys())

    base_bools = [base_correctness[sid] for sid in common_scorable_sids]
    base_scores = [1.0 if b else 0.0 for b in base_bools]
    cluster_ids = [sample_pair_map.get(sid, sid) for sid in common_scorable_sids]

    universe_size = (
        len(inputs.corpus_ids)
        if inputs.corpus_ids
        else (len(inputs.registry) if inputs.registry else 474)
    )

    by_condition_rq1 = {}

    for cond in CONDITIONS:
        m = condition_metrics[cond]
        cond_bools = [correctness_by_cond_sample[cond][sid] for sid in common_scorable_sids]
        cond_scores = [1.0 if b else 0.0 for b in cond_bools]

        acc_ci = compute_single_bootstrap_ci(
            cond_scores, cluster_ids=cluster_ids, num_samples=bootstrap_samples, seed=seed
        )

        cond_result: dict[str, Any] = {
            "condition": cond,
            "scorable_sample_count": m["scorable_sample_count"],
            "accuracy_end_to_end": m["accuracy_end_to_end"],
            "accuracy_valid_outputs": m["accuracy_valid_outputs"],
            "macro_f1": m["macro_f1"],
            "correct_count": m["correct_count"],
            "accuracy_e2e_ci_95": [acc_ci["ci_lower"], acc_ci["ci_upper"]],
            "resampling_method": acc_ci.get("resampling_method"),
            "cluster_count": acc_ci.get("cluster_count"),
        }

        if cond == base_cond:
            cond_result["is_baseline"] = True
            cond_result["delta_vs_baseline"] = None
        else:
            delta_acc_e2e = (
                m["accuracy_end_to_end"] - base_metrics["accuracy_end_to_end"]
                if m["accuracy_end_to_end"] is not None
                and base_metrics["accuracy_end_to_end"] is not None
                else None
            )
            delta_acc_valid = (
                m["accuracy_valid_outputs"] - base_metrics["accuracy_valid_outputs"]
                if m["accuracy_valid_outputs"] is not None
                and base_metrics["accuracy_valid_outputs"] is not None
                else None
            )
            delta_f1 = (
                m["macro_f1"] - base_metrics["macro_f1"]
                if m["macro_f1"] is not None and base_metrics["macro_f1"] is not None
                else None
            )

            rel_gain_acc = (
                (delta_acc_e2e / base_metrics["accuracy_end_to_end"] * 100.0)
                if (delta_acc_e2e is not None and base_metrics["accuracy_end_to_end"])
                else None
            )
            rel_gain_f1 = (
                (delta_f1 / base_metrics["macro_f1"] * 100.0)
                if (delta_f1 is not None and base_metrics["macro_f1"])
                else None
            )

            mcnemar = compute_mcnemar_test(base_bools, cond_bools)
            paired_acc_ci = compute_paired_bootstrap_ci(
                cond_scores,
                base_scores,
                cluster_ids=cluster_ids,
                num_samples=bootstrap_samples,
                seed=seed,
            )
            paired_f1_ci = compute_macro_f1_bootstrap_ci(
                scorable_by_cond[cond],
                scorable_by_cond[base_cond],
                inputs.ground_truth,
                universe_size=universe_size,
                cluster_ids=cluster_ids,
                num_samples=bootstrap_samples,
                seed=seed,
            )

            cond_result["is_baseline"] = False
            cond_result["delta_vs_baseline"] = {
                "delta_accuracy_end_to_end": delta_acc_e2e,
                "delta_accuracy_valid_outputs": delta_acc_valid,
                "delta_macro_f1": delta_f1,
                "relative_gain_accuracy_e2e_pct": rel_gain_acc,
                "relative_gain_macro_f1_pct": rel_gain_f1,
                "delta_accuracy_e2e_ci_95": [
                    paired_acc_ci["ci_lower"],
                    paired_acc_ci["ci_upper"],
                ],
                "delta_macro_f1_ci_95": [paired_f1_ci["ci_lower"], paired_f1_ci["ci_upper"]],
                "mcnemar_test": mcnemar,
                "exploratory_diagnostics": {
                    "resampling_method": paired_acc_ci.get("resampling_method"),
                    "cluster_count": paired_acc_ci.get("cluster_count"),
                    "note": (
                        "Secondary exploratory diagnostics: pair-clustered bootstrap resampling "
                        "preserves intra-pair correlation between single-view and contextual-view "
                        "samples sharing pair_id; does not alter frozen headline metrics."
                    ),
                },
            }

        by_condition_rq1[cond] = cond_result

    rag_conditions = [c for c in CONDITIONS if c != base_cond]
    best_cond = max(
        rag_conditions,
        key=lambda c: by_condition_rq1[c]["accuracy_end_to_end"] or -1.0,
    )

    return {
        "schema_version": "1.0.0",
        "research_question": (
            "RQ1: Controlled comparison of No-RAG vs RAG on exact technique attribution"
        ),
        "baseline_condition": base_cond,
        "best_rag_condition": best_cond,
        "best_rag_accuracy_delta": by_condition_rq1[best_cond]["delta_vs_baseline"][
            "delta_accuracy_end_to_end"
        ],
        "best_rag_macro_f1_delta": by_condition_rq1[best_cond]["delta_vs_baseline"][
            "delta_macro_f1"
        ],
        "by_condition": by_condition_rq1,
    }


# ---------------------------------------------------------------------------
# RQ2 Analysis: Retrieval vs Generation Error Decomposition
# ---------------------------------------------------------------------------


def compute_rq2(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    retrieval_cond_metrics: Optional[dict[str, Any]] = None,
    failure_decomp_metrics: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Compute RQ2: Retrieval vs. Generation error decomposition.

    Invariants (per Decision D2i and D2j):
    - Independent failure axes: retrieval miss, provider failure, parse failure,
      invalid attack ID, and valid-but-wrong classification are evaluated without
      forced mutual exclusion or unapproved causal source-partition claims.
    - Preserves all provider/parse/invalid counts even when a retrieval miss occurs.
    - Explicitly computes and reports overlaps (e.g., retrieval miss + provider failure,
      retrieval miss + valid but wrong classification).
    - For No-RAG: Hit@k, Recall@k, and retrieval-conditioned metrics are strictly NOT APPLICABLE
      (None / null), not observed zero performance.
    - Zero-denominator rates and percentages evaluate to None (null per D2j), never 0.0.
    """
    if retrieval_cond_metrics is None:
        retrieval_cond_metrics = compute_retrieval_conditional_metrics(inputs, protocol)
    if failure_decomp_metrics is None:
        failure_decomp_metrics = compute_failure_decomposition(inputs, protocol)

    by_condition_rq2 = {}

    for cond in CONDITIONS:
        k = 0 if cond == "no_rag" else int(cond[5:])
        is_rag = k > 0

        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = [
            r
            for r in cond_records
            if inputs.ground_truth_status.get(
                r["sample_id"],
                "mapped" if inputs.ground_truth.get(r["sample_id"]) else "unmapped",
            )
            == "mapped"
            and inputs.ground_truth.get(r["sample_id"])
        ]

        total_scorable = len(scorable_records)
        n_correct = sum(
            1
            for r in scorable_records
            if r["parse_status"] == "VALID"
            and bool(r.get("parsed_technique_ids"))
            and r["parsed_technique_ids"][0] in set(inputs.ground_truth.get(r["sample_id"], ()))
        )
        total_failures = total_scorable - n_correct

        # 1. Retrieval & Conditional Metrics (None for No-RAG)
        if is_rag:
            ret_info = retrieval_cond_metrics["by_condition"].get(cond, {})
            retrieval_metrics = {
                "applicable": True,
                "macro_recall": ret_info.get("macro_recall"),
                "retrieval_hit_rate": ret_info.get("retrieval_hit_rate"),
                "retrieved_positive_count": ret_info.get("retrieved_positive_count"),
                "total_positive_sample_count": ret_info.get("total_positive_sample_count"),
            }
            generation_conditional = {
                "applicable": True,
                "p_correct_given_retrieval_success": ret_info.get(
                    "p_correct_given_retrieval_success"
                ),
                "p_correct_given_retrieval_failure": ret_info.get(
                    "p_correct_given_retrieval_failure"
                ),
                "retrieval_success_sample_count": ret_info.get("retrieval_success_sample_count"),
                "retrieval_failure_sample_count": ret_info.get("retrieval_failure_sample_count"),
            }
        else:
            retrieval_metrics = {
                "applicable": False,
                "macro_recall": None,
                "retrieval_hit_rate": None,
                "retrieved_positive_count": None,
                "total_positive_sample_count": None,
                "note": "Retrieval metrics not applicable to No-RAG baseline (k=0).",
            }
            generation_conditional = {
                "applicable": False,
                "p_correct_given_retrieval_success": None,
                "p_correct_given_retrieval_failure": None,
                "retrieval_success_sample_count": None,
                "retrieval_failure_sample_count": None,
                "note": "Retrieval-conditioned metrics not applicable to No-RAG baseline (k=0).",
            }

        # 2. Independent Failure Axes & Overlaps
        ret_misses = 0 if is_rag else None
        prov_failures = 0
        parse_failures = 0
        invalid_attack_ids = 0
        valid_but_wrong = 0

        overlap_miss_and_wrong = 0 if is_rag else None
        overlap_miss_and_provider = 0 if is_rag else None
        overlap_miss_and_parse = 0 if is_rag else None
        overlap_miss_and_invalid = 0 if is_rag else None

        for r in scorable_records:
            gt = set(inputs.ground_truth.get(r["sample_id"], ()))
            status = r["parse_status"]
            retrieved = {c["technique_id"] for c in r.get("retrieved_candidates", [])}
            is_miss = is_rag and not bool(retrieved & gt)

            if is_miss and ret_misses is not None:
                ret_misses += 1

            if status in {"TIMEOUT", "REFUSAL", "INCOMPLETE", "API_FAILURE"}:
                prov_failures += 1
                if is_miss and overlap_miss_and_provider is not None:
                    overlap_miss_and_provider += 1
            elif status == "MALFORMED_RESPONSE":
                parse_failures += 1
                if is_miss and overlap_miss_and_parse is not None:
                    overlap_miss_and_parse += 1
            elif status == "INVALID_ID":
                invalid_attack_ids += 1
                if is_miss and overlap_miss_and_invalid is not None:
                    overlap_miss_and_invalid += 1
            elif status == "VALID":
                pred = r.get("parsed_technique_ids", [None])[0]
                if pred not in gt:
                    valid_but_wrong += 1
                    if is_miss and overlap_miss_and_wrong is not None:
                        overlap_miss_and_wrong += 1

        # Rates relative to total_scorable (None per D2j if zero denominator)
        def _rate_or_none(count: Optional[int], denom: int) -> Optional[float]:
            if count is None or denom <= 0:
                return None
            return count / denom

        ret_miss_rate = _rate_or_none(ret_misses, total_scorable)
        prov_rate = _rate_or_none(prov_failures, total_scorable)
        parse_rate = _rate_or_none(parse_failures, total_scorable)
        inv_rate = _rate_or_none(invalid_attack_ids, total_scorable)
        wrong_rate = _rate_or_none(valid_but_wrong, total_scorable)

        # Fractions among failures (None per D2j if total_failures == 0)
        frac_ret_miss = _rate_or_none(ret_misses, total_failures)
        frac_prov = _rate_or_none(prov_failures, total_failures)
        frac_parse = _rate_or_none(parse_failures, total_failures)
        frac_inv = _rate_or_none(invalid_attack_ids, total_failures)
        frac_wrong = _rate_or_none(valid_but_wrong, total_failures)

        by_condition_rq2[cond] = {
            "condition": cond,
            "retrieval_k": k,
            "total_scorable_samples": total_scorable,
            "total_failures": total_failures,
            "retrieval_metrics": retrieval_metrics,
            "generation_conditional_accuracy": generation_conditional,
            "independent_failure_axes": {
                "retrieval_miss_count": ret_misses,
                "retrieval_miss_rate": ret_miss_rate,
                "provider_failure_count": prov_failures,
                "provider_failure_rate": prov_rate,
                "parse_failure_count": parse_failures,
                "parse_failure_rate": parse_rate,
                "invalid_attack_id_count": invalid_attack_ids,
                "invalid_attack_id_rate": inv_rate,
                "valid_but_wrong_classification_count": valid_but_wrong,
                "valid_but_wrong_classification_rate": wrong_rate,
                "overlap_retrieval_miss_and_wrong_classification": overlap_miss_and_wrong,
                "overlap_retrieval_miss_and_provider_failure": overlap_miss_and_provider,
                "overlap_retrieval_miss_and_parse_failure": overlap_miss_and_parse,
                "overlap_retrieval_miss_and_invalid_id": overlap_miss_and_invalid,
                "rates_among_failures": {
                    "retrieval_miss": frac_ret_miss,
                    "provider_failure": frac_prov,
                    "parse_failure": frac_parse,
                    "invalid_attack_id": frac_inv,
                    "valid_but_wrong_classification": frac_wrong,
                },
                "canonical_d2i_policy_note": (
                    "Per Decision D2i, failure axes are evaluated independently without forced "
                    "mutual exclusion. Retrieval miss does not establish cause of provider or "
                    "parse failure."
                ),
            },
            # Backward-compatible view preserved without causal partition claims
            "error_decomposition": {
                "retrieval_miss_error_count": ret_misses,
                "generation_misattribution_count": valid_but_wrong,
                "system_or_parse_error_count": prov_failures + parse_failures,
                "overlap_retrieval_miss_and_wrong_classification": overlap_miss_and_wrong,
                "retrieval_miss_fraction_of_failures": frac_ret_miss,
                "generation_misattribution_fraction_of_failures": frac_wrong,
                "system_or_parse_fraction_of_failures": _rate_or_none(
                    prov_failures + parse_failures, total_failures
                ),
            },
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ2: Retrieval vs. Generation error decomposition",
        "by_condition": by_condition_rq2,
    }


# ---------------------------------------------------------------------------
# RQ3 Analysis: Retrieval Depth Ablation, Efficiency, & View Diagnostics
# ---------------------------------------------------------------------------


def compute_rq3(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
    *,
    pricing_config: Optional[dict[str, Any]] = None,
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Compute RQ3: Retrieval depth ablation, latency, financial costs, and view diagnostics.

    Evaluates:
      - Performance curve across k: Accuracy, Macro-F1, Recall@k.
      - Latency distribution: Mean, median, p95, sum (ms).
      - Token usage: Mean prompt/completion/total tokens, sum.
      - Financial cost calculation: Full journal/ledger reconciliation, explicit cost denominators:
        * cost_per_logical_request (N=1,280 in TEST)
        * cost_per_scorable_query (N=718 in TEST)
        * cost_per_correct_attribution
      - Real expenditure disclosure for excluded ambiguous (311) and unmapped (251) views.
      - Whole-study accounting including prior pilot hold ($0.05264010) and active reservations.
      - Paired Single-View (278 scorable) vs Contextual-View (440 scorable) diagnostics.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    if pricing_config is None:
        target_root = repo_root or Path(__file__).resolve().parents[2]
        pricing_config, _ = load_pricing_config(repo_root=target_root)

    validate_pricing_config(pricing_config)

    # Reconcile attempt receipts and ledger settlements
    reconciliation = reconcile_journal_and_ledger(
        inputs.records,
        pricing_config,
        journal_path=journal_path,
        journal_events=journal_events,
        study_ledger_path=study_ledger_path,
        study_ledger_data=study_ledger_data,
    )

    tradeoff_by_condition = {}
    base_cost_usd = 0.0

    worst_charge = Decimal(str(pricing_config["reservation_bounds"]["default_attempt_worst_usd"]))

    for cond in CONDITIONS:
        k = 0 if cond == "no_rag" else int(cond[5:])
        m = condition_metrics[cond]
        rows = [r for r in inputs.records if r["condition"] == cond]

        latencies = [r["latency_ms"] for r in rows if r.get("latency_ms") is not None]
        mean_lat = float(np.mean(latencies)) if latencies else None
        median_lat = float(np.median(latencies)) if latencies else None
        p95_lat = float(np.percentile(latencies, 95)) if latencies else None
        sum_lat = float(np.sum(latencies)) if latencies else None

        prompt_tokens = [r["prompt_tokens"] for r in rows if r.get("prompt_tokens") is not None]
        comp_tokens = [
            r["completion_tokens"] for r in rows if r.get("completion_tokens") is not None
        ]
        total_tokens = [r["total_tokens"] for r in rows if r.get("total_tokens") is not None]

        mean_prompt_tok = float(np.mean(prompt_tokens)) if prompt_tokens else None
        mean_comp_tok = float(np.mean(comp_tokens)) if comp_tokens else None
        mean_tot_tok = float(np.mean(total_tokens)) if total_tokens else None
        sum_prompt_tok = sum(prompt_tokens)
        sum_comp_tok = sum(comp_tokens)
        sum_tot_tok = sum(total_tokens)

        # Token-based estimation per record (worst-case charged on missing usage)
        rec_token_cost = Decimal("0.0")
        missing_usage_count = 0
        missing_usage_cost = Decimal("0.0")
        cost_ambiguous = Decimal("0.0")
        cost_unmapped = Decimal("0.0")

        for r in rows:
            p_tok = r.get("prompt_tokens")
            c_tok = r.get("completion_tokens")
            ca_tok = r.get("cached_tokens")

            if p_tok is None or c_tok is None:
                missing_usage_count += 1
                item_cost = worst_charge
                missing_usage_cost += worst_charge
            else:
                item_cost = calculate_attempt_token_cost(
                    p_tok, c_tok, pricing_config, cached_tokens=ca_tok, tier="default"
                )

            rec_token_cost += item_cost

            # Track spending on excluded views
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "ambiguous":
                cost_ambiguous += item_cost
            elif status == "unmapped" or not gt:
                cost_unmapped += item_cost

        # Determine authoritative condition cost from ledger/receipts if available
        receipts_cost = reconciliation["receipts_cost_by_condition"].get(cond)
        settled_cost = reconciliation["settled_cost_by_condition"].get(cond)
        retried_count = reconciliation["retried_attempts_by_condition"].get(cond, 0)

        if settled_cost is not None:
            authoritative_cost = settled_cost
        elif receipts_cost is not None:
            authoritative_cost = receipts_cost
        else:
            authoritative_cost = rec_token_cost

        total_cost_usd = float(authoritative_cost)
        if cond == "no_rag":
            base_cost_usd = total_cost_usd

        # Explicitly report three distinct cost denominators
        logical_count = len(rows)
        scorable_count = m["scorable_sample_count"]
        correct_count = m["correct_count"]

        cost_per_logical = (total_cost_usd / logical_count) if logical_count > 0 else None
        cost_per_scorable = (total_cost_usd / scorable_count) if scorable_count > 0 else None
        cost_per_correct = (total_cost_usd / correct_count) if correct_count > 0 else None
        cost_all_excluded = float(cost_ambiguous + cost_unmapped)

        tradeoff_by_condition[cond] = {
            "condition": cond,
            "retrieval_k": k,
            "accuracy_end_to_end": m["accuracy_end_to_end"],
            "accuracy_valid_outputs": m["accuracy_valid_outputs"],
            "macro_f1": m["macro_f1"],
            "latency_ms": {
                "mean": mean_lat,
                "median": median_lat,
                "p95": p95_lat,
                "sum": sum_lat,
            },
            "tokens": {
                "mean_prompt_tokens": mean_prompt_tok,
                "mean_completion_tokens": mean_comp_tok,
                "mean_total_tokens": mean_tot_tok,
                "sum_prompt_tokens": sum_prompt_tok,
                "sum_completion_tokens": sum_comp_tok,
                "sum_total_tokens": sum_tot_tok,
            },
            "financial_cost_usd": {
                "token_usage_estimated_cost_usd": float(rec_token_cost),
                "receipts_reconciled_cost_usd": (
                    float(receipts_cost) if receipts_cost is not None else None
                ),
                "ledger_settled_cost_usd": (
                    float(settled_cost) if settled_cost is not None else None
                ),
                "total_cost_usd": total_cost_usd,
                "cost_per_logical_request_usd": cost_per_logical,
                "cost_per_scorable_query_usd": cost_per_scorable,
                "cost_per_correct_attribution_usd": cost_per_correct,
                "marginal_cost_vs_baseline_usd": total_cost_usd - base_cost_usd,
                "missing_usage_records_count": missing_usage_count,
                "missing_usage_worst_charge_usd": float(missing_usage_cost),
                "retried_attempts_count": retried_count,
                "cost_of_excluded_ambiguous_views_usd": float(cost_ambiguous),
                "cost_of_excluded_unmapped_views_usd": float(cost_unmapped),
                "cost_of_all_excluded_views_usd": cost_all_excluded,
                "excluded_views_financial_disclosure": (
                    "Costs of excluded ambiguous (311) and unmapped (251) views remain "
                    "real monetary expenditure incurred during inference and are fully "
                    "included in condition and study totals."
                ),
            },
        }

    # Whole-study financial summary
    total_budget_usd = Decimal(str(pricing_config.get("total_study_budget_usd", "19.99000000")))
    pilot_hold_usd = Decimal(
        str(pricing_config.get("prior_pilot_provisional_hold_usd", "0.05264010"))
    )
    canonical_total = sum(
        Decimal(str(tradeoff_by_condition[c]["financial_cost_usd"]["total_cost_usd"]))
        for c in CONDITIONS
    )
    active_res = reconciliation["active_reservations_usd"]
    orphan_res = reconciliation["orphan_reservations_usd"]
    total_committed = round_cost_up(canonical_total + pilot_hold_usd + active_res)
    uncommitted = round_cost_up(total_budget_usd - total_committed)

    whole_study_accounting = {
        "total_study_budget_usd": float(total_budget_usd),
        "canonical_conditions_total_usd": float(canonical_total),
        "prior_pilot_provisional_hold_usd": float(pilot_hold_usd),
        "active_reservations_usd": float(active_res),
        "orphan_reservations_usd": float(orphan_res),
        "total_study_committed_spend_usd": float(total_committed),
        "net_remaining_uncommitted_budget_usd": float(uncommitted),
        "study_wide_missing_usage_records_count": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["missing_usage_records_count"]
            for c in CONDITIONS
        ),
        "study_wide_missing_usage_charged_usd": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["missing_usage_worst_charge_usd"]
            for c in CONDITIONS
        ),
        "study_wide_retried_attempts_count": sum(
            tradeoff_by_condition[c]["financial_cost_usd"]["retried_attempts_count"]
            for c in CONDITIONS
        ),
        "accounting_policy_disclosure": (
            "Prior pilot provisional hold ($0.05264010) is accounted exclusively at the "
            "whole-study level and is never allocated to individual canonical conditions. "
            "Spending on excluded ambiguous and unmapped views is fully accounted as real "
            "monetary spend."
        ),
    }

    # Paired Single-View (278 scorable) vs Contextual-View (440 scorable) Diagnostics
    view_diagnostics_by_condition = {}

    for cond in CONDITIONS:
        rows = [r for r in inputs.records if r["condition"] == cond]

        single_records = []
        contextual_records = []
        pair_to_views: dict[str, dict[str, Any]] = defaultdict(dict)

        for r in rows:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status != "mapped" or not gt:
                continue

            v_type = r.get("view_type")
            p_id = r.get("pair_id")

            is_correct = (
                r["parse_status"] == "VALID"
                and bool(r.get("parsed_technique_ids"))
                and r["parsed_technique_ids"][0] in set(gt)
            )

            if v_type == "single":
                single_records.append((sid, is_correct))
            elif v_type == "contextual":
                contextual_records.append((sid, is_correct))

            if p_id and v_type:
                pair_to_views[p_id][v_type] = {
                    "sample_id": sid,
                    "correct": is_correct,
                    "gt": tuple(sorted(gt)),
                }

        single_acc = (
            sum(1 for _, c in single_records if c) / len(single_records) if single_records else None
        )
        contextual_acc = (
            sum(1 for _, c in contextual_records if c) / len(contextual_records)
            if contextual_records
            else None
        )
        view_delta = (
            contextual_acc - single_acc
            if contextual_acc is not None and single_acc is not None
            else None
        )

        single_view_records = [r for r in rows if r.get("view_type") == "single"]
        contextual_view_records = [r for r in rows if r.get("view_type") == "contextual"]

        if single_view_records:
            single_metrics = compute_condition_metrics(single_view_records, inputs, protocol, cond)
            single_view_macro_f1 = single_metrics.get("macro_f1")
        else:
            single_view_macro_f1 = None

        if contextual_view_records:
            contextual_metrics = compute_condition_metrics(
                contextual_view_records, inputs, protocol, cond
            )
            contextual_view_macro_f1 = contextual_metrics.get("macro_f1")
        else:
            contextual_view_macro_f1 = None

        view_macro_f1_delta = (
            contextual_view_macro_f1 - single_view_macro_f1
            if contextual_view_macro_f1 is not None and single_view_macro_f1 is not None
            else None
        )

        complete_pairs = [p for p in pair_to_views.values() if "single" in p and "contextual" in p]
        both_corr = sum(
            1 for p in complete_pairs if p["single"]["correct"] and p["contextual"]["correct"]
        )
        single_only = sum(
            1 for p in complete_pairs if p["single"]["correct"] and not p["contextual"]["correct"]
        )
        contextual_only = sum(
            1 for p in complete_pairs if not p["single"]["correct"] and p["contextual"]["correct"]
        )
        both_incorr = sum(
            1
            for p in complete_pairs
            if not p["single"]["correct"] and not p["contextual"]["correct"]
        )

        n_pairs = len(complete_pairs)
        single_paired_acc = (both_corr + single_only) / n_pairs if n_pairs > 0 else None
        contextual_paired_acc = (both_corr + contextual_only) / n_pairs if n_pairs > 0 else None
        paired_delta = (contextual_only - single_only) / n_pairs if n_pairs > 0 else None

        identical_gt_pairs = [
            p for p in complete_pairs if set(p["single"]["gt"]) == set(p["contextual"]["gt"])
        ]
        divergent_gt_pairs = [
            p for p in complete_pairs if set(p["single"]["gt"]) != set(p["contextual"]["gt"])
        ]

        n_ident = len(identical_gt_pairs)
        ident_both = sum(
            1 for p in identical_gt_pairs if p["single"]["correct"] and p["contextual"]["correct"]
        )
        ident_single = sum(
            1
            for p in identical_gt_pairs
            if p["single"]["correct"] and not p["contextual"]["correct"]
        )
        ident_ctx = sum(
            1
            for p in identical_gt_pairs
            if not p["single"]["correct"] and p["contextual"]["correct"]
        )
        ident_neither = sum(
            1
            for p in identical_gt_pairs
            if not p["single"]["correct"] and not p["contextual"]["correct"]
        )
        ident_s_acc = (ident_both + ident_single) / n_ident if n_ident > 0 else None
        ident_c_acc = (ident_both + ident_ctx) / n_ident if n_ident > 0 else None
        ident_delta = (ident_ctx - ident_single) / n_ident if n_ident > 0 else None

        n_div = len(divergent_gt_pairs)
        div_both = sum(
            1 for p in divergent_gt_pairs if p["single"]["correct"] and p["contextual"]["correct"]
        )
        div_single = sum(
            1
            for p in divergent_gt_pairs
            if p["single"]["correct"] and not p["contextual"]["correct"]
        )
        div_ctx = sum(
            1
            for p in divergent_gt_pairs
            if not p["single"]["correct"] and p["contextual"]["correct"]
        )
        div_neither = sum(
            1
            for p in divergent_gt_pairs
            if not p["single"]["correct"] and not p["contextual"]["correct"]
        )
        div_s_acc = (div_both + div_single) / n_div if n_div > 0 else None
        div_c_acc = (div_both + div_ctx) / n_div if n_div > 0 else None
        div_delta = (div_ctx - div_single) / n_div if n_div > 0 else None

        single_bools = [p["single"]["correct"] for p in complete_pairs]
        contextual_bools = [p["contextual"]["correct"] for p in complete_pairs]
        mcnemar_views = (
            compute_mcnemar_test(single_bools, contextual_bools) if complete_pairs else None
        )

        view_diagnostics_by_condition[cond] = {
            "condition": cond,
            "single_view_scorable_count": len(single_records),
            "contextual_view_scorable_count": len(contextual_records),
            "view_split_notes": (
                "Empirical TEST scorable views: 278 single views and 440 contextual views "
                "(718 total), reflecting mapped ground truth rather than an assumed 50/50 balance."
            ),
            "single_view_accuracy_e2e": single_acc,
            "contextual_view_accuracy_e2e": contextual_acc,
            "view_accuracy_delta": view_delta,
            "single_view_macro_f1": single_view_macro_f1,
            "contextual_view_macro_f1": contextual_view_macro_f1,
            "view_macro_f1_delta": view_macro_f1_delta,
            "paired_complete_pairs_count": n_pairs,
            "single_paired_accuracy": single_paired_acc,
            "contextual_paired_accuracy": contextual_paired_acc,
            "paired_delta": paired_delta,
            "pair_concordance": {
                "both_correct_count": both_corr,
                "both_correct_pct": (both_corr / n_pairs * 100.0) if n_pairs > 0 else 0.0,
                "single_only_correct_count": single_only,
                "single_only_correct_pct": (single_only / n_pairs * 100.0) if n_pairs > 0 else 0.0,
                "contextual_only_correct_count": contextual_only,
                "contextual_only_correct_pct": (
                    (contextual_only / n_pairs * 100.0) if n_pairs > 0 else 0.0
                ),
                "both_incorrect_count": both_incorr,
                "both_incorrect_pct": (both_incorr / n_pairs * 100.0) if n_pairs > 0 else 0.0,
            },
            "gt_concordance_decomposition": {
                "identical_gt_pairs": {
                    "pair_count": n_ident,
                    "both_correct_count": ident_both,
                    "single_only_correct_count": ident_single,
                    "contextual_only_correct_count": ident_ctx,
                    "both_incorrect_count": ident_neither,
                    "single_paired_accuracy": ident_s_acc,
                    "contextual_paired_accuracy": ident_c_acc,
                    "paired_delta": ident_delta,
                },
                "divergent_gt_pairs": {
                    "pair_count": n_div,
                    "both_correct_count": div_both,
                    "single_only_correct_count": div_single,
                    "contextual_only_correct_count": div_ctx,
                    "both_incorrect_count": div_neither,
                    "single_paired_accuracy": div_s_acc,
                    "contextual_paired_accuracy": div_c_acc,
                    "paired_delta": div_delta,
                },
            },
            "mcnemar_test_views_exploratory": mcnemar_views,
        }

    return {
        "schema_version": "1.0.0",
        "research_question": "RQ3: Retrieval depth & efficiency ablation and view diagnostics",
        "tradeoffs_by_condition": tradeoff_by_condition,
        "whole_study_financial_accounting": whole_study_accounting,
        "view_diagnostics": view_diagnostics_by_condition,
    }


# ===========================================================================
# NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis
# ===========================================================================


def compute_stratified_gt_complexity_producer(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    condition_metrics: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """NEW PROPOSED PRODUCER: Stratified analysis by ground-truth complexity.

    Evaluates scorable views partitioned into:
      - Single-GT subset: views with exactly 1 annotated technique ID (N=678 on TEST).
      - Multi-GT subset: views with >=2 annotated technique IDs
        (N=40 on TEST, evaluated via ANY_MATCH).

    Preserves the frozen 474-class benchmark universe and Decision D2a ANY_MATCH semantics.
    Requires explicit Codex authorization prior to canonical reporting inclusion.
    """
    if condition_metrics is None:
        condition_metrics = {
            c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
        }

    by_cond = {}
    for cond in CONDITIONS:
        cond_records = [r for r in inputs.records if r["condition"] == cond]
        scorable_records = []
        for r in cond_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            status = inputs.ground_truth_status.get(sid, "mapped" if gt else "unmapped")
            if status == "mapped" and gt:
                scorable_records.append(r)

        single_gt_records = []
        multi_gt_records = []
        for r in scorable_records:
            sid = r["sample_id"]
            gt = inputs.ground_truth.get(sid, ())
            if len(gt) == 1:
                single_gt_records.append(r)
            elif len(gt) >= 2:
                multi_gt_records.append(r)

        s_corr = sum(
            1
            for r in single_gt_records
            if r["parse_status"] == "VALID"
            and bool(r.get("parsed_technique_ids"))
            and r["parsed_technique_ids"][0] in set(inputs.ground_truth.get(r["sample_id"], ()))
        )
        m_corr = sum(
            1
            for r in multi_gt_records
            if r["parse_status"] == "VALID"
            and bool(r.get("parsed_technique_ids"))
            and r["parsed_technique_ids"][0] in set(inputs.ground_truth.get(r["sample_id"], ()))
        )

        n_s = len(single_gt_records)
        n_m = len(multi_gt_records)
        s_acc = s_corr / n_s if n_s > 0 else None
        m_acc = m_corr / n_m if n_m > 0 else None
        delta = (m_acc - s_acc) if (m_acc is not None and s_acc is not None) else None

        tot_corr = s_corr + m_corr
        tot_n = len(scorable_records)
        tot_acc = tot_corr / tot_n if tot_n > 0 else None

        if single_gt_records:
            single_gt_metrics = compute_condition_metrics(single_gt_records, inputs, protocol, cond)
            single_gt_macro_f1 = single_gt_metrics.get("macro_f1")
        else:
            single_gt_macro_f1 = None

        if multi_gt_records:
            multi_gt_metrics = compute_condition_metrics(multi_gt_records, inputs, protocol, cond)
            multi_gt_macro_f1 = multi_gt_metrics.get("macro_f1")
        else:
            multi_gt_macro_f1 = None

        complexity_f1_delta = (
            multi_gt_macro_f1 - single_gt_macro_f1
            if multi_gt_macro_f1 is not None and single_gt_macro_f1 is not None
            else None
        )

        overall_macro_f1_ref = (
            condition_metrics[cond]["macro_f1"] if cond in condition_metrics else None
        )

        by_cond[cond] = {
            "condition": cond,
            "single_gt_sample_count": n_s,
            "single_gt_correct_count": s_corr,
            "single_gt_accuracy_e2e": s_acc,
            "single_gt_macro_f1": single_gt_macro_f1,
            "multi_gt_sample_count": n_m,
            "multi_gt_correct_count": m_corr,
            "multi_gt_accuracy_e2e": m_acc,
            "multi_gt_macro_f1": multi_gt_macro_f1,
            "complexity_accuracy_delta": delta,
            "complexity_macro_f1_delta": complexity_f1_delta,
            "overall_scorable_sample_count": tot_n,
            "overall_scorable_accuracy_e2e": tot_acc,
            "overall_macro_f1_reference": overall_macro_f1_ref,
        }

    return {
        "producer_label": (
            "NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis"
        ),
        "protocol_approval_required": True,
        "frozen_benchmark_universe_size": 474,
        "multi_gt_semantics": protocol.d2a_ground_truth_semantics,
        "by_condition": by_cond,
    }


# ---------------------------------------------------------------------------
# Comprehensive Full Study Pipeline
# ---------------------------------------------------------------------------


def run_rq_analysis(
    inputs: EvaluationInputs,
    protocol: ScientificProtocolApproval,
    *,
    pricing_config: Optional[dict[str, Any]] = None,
    bootstrap_samples: int = 1000,
    seed: int = 42,
    output_dir: Optional[Path | str] = None,
    journal_path: Optional[Path | str] = None,
    journal_events: Optional[Sequence[dict[str, Any]]] = None,
    study_ledger_path: Optional[Path | str] = None,
    study_ledger_data: Optional[dict[str, Any]] = None,
    repo_root: Optional[Path] = None,
) -> dict[str, Any]:
    """Execute complete RQ1, RQ2, and RQ3 analyses and optionally write reports."""
    cond_metrics = {
        c: compute_condition_metrics(inputs.records, inputs, protocol, c) for c in CONDITIONS
    }
    ret_cond_metrics = compute_retrieval_conditional_metrics(inputs, protocol)
    fail_decomp_metrics = compute_failure_decomposition(inputs, protocol)

    rq1 = compute_rq1(
        inputs,
        protocol,
        cond_metrics,
        bootstrap_samples=bootstrap_samples,
        seed=seed,
    )
    rq2 = compute_rq2(inputs, protocol, ret_cond_metrics, fail_decomp_metrics)
    rq3 = compute_rq3(
        inputs,
        protocol,
        cond_metrics,
        pricing_config=pricing_config,
        journal_path=journal_path,
        journal_events=journal_events,
        study_ledger_path=study_ledger_path,
        study_ledger_data=study_ledger_data,
        repo_root=repo_root,
    )

    execution_mode = getattr(inputs, "execution_mode", "unknown")
    dataset_split = (
        inputs.manifest_data.get("split", "unknown")
        if hasattr(inputs, "manifest_data") and inputs.manifest_data
        else "unknown"
    )
    is_fixture = execution_mode != "live"
    provenance_status = (
        "canonical_study"
        if execution_mode == "live" and dataset_split == "test"
        else "diagnostic_fixture"
    )

    overall_summary = {
        "schema_version": "1.0.0",
        "analysis_tool_version": ANALYSIS_TOOL_VERSION,
        "analysis_timestamp": datetime.now(UTC).isoformat(),
        "experiment_id": inputs.experiment_id,
        "manifest_sha256": inputs.manifest_sha256,
        "protocol_version": protocol.protocol_version,
        "protocol_sha256": protocol.protocol_sha256,
        "execution_mode": execution_mode,
        "dataset_split": dataset_split,
        "fixture_only": is_fixture,
        "provenance_status": provenance_status,
        "rq1": rq1,
        "rq2": rq2,
        "rq3": rq3,
        "new_proposed_producer_stratified_gt_complexity": compute_stratified_gt_complexity_producer(
            inputs, protocol, cond_metrics
        ),
    }

    if output_dir is not None:
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        json_file = out_path / "rq_analysis.json"
        json_file.write_bytes(canonical_json_bytes(overall_summary) + b"\n")

        md_file = out_path / "rq_analysis_summary.md"
        md_content = generate_rq_markdown_report(overall_summary)
        md_file.write_text(md_content, encoding="utf-8")

    return overall_summary


# ---------------------------------------------------------------------------
# Markdown Report Generation
# ---------------------------------------------------------------------------


def generate_rq_markdown_report(analysis_dict: dict[str, Any]) -> str:
    """Format structured RQ analysis dictionary into publication-grade Markdown."""
    rq1 = analysis_dict.get("rq1", {})
    rq2 = analysis_dict.get("rq2", {})
    rq3 = analysis_dict.get("rq3", {})
    whole_fin = rq3.get("whole_study_financial_accounting", {})

    exec_mode = analysis_dict.get("execution_mode", "unknown")
    dataset_split = analysis_dict.get("dataset_split", "unknown")
    provenance_status = analysis_dict.get("provenance_status", "unknown")
    is_fixture = analysis_dict.get("fixture_only", exec_mode != "live")

    lines = [
        "# RAG2ATTCK Empirical Analysis Report (RQ1, RQ2, RQ3)",
        "",
        f"- **Experiment ID**: `{analysis_dict.get('experiment_id')}`",
        f"- **Manifest SHA-256**: `{analysis_dict.get('manifest_sha256')}`",
        f"- **Protocol Version**: `{analysis_dict.get('protocol_version')}` "
        f"(`{analysis_dict.get('protocol_sha256', '')[:12]}...`)",
        f"- **Analysis Tool Version**: `{analysis_dict.get('analysis_tool_version')}`",
        f"- **Execution Mode**: `{exec_mode}`",
        f"- **Dataset Split / Scope**: `{dataset_split}`",
        f"- **Provenance Status**: `{provenance_status}`",
        f"- **Report Generated**: `{analysis_dict.get('analysis_timestamp')}`",
        "",
    ]

    if is_fixture:
        lines.extend(
            [
                (
                    f"> [!NOTE] Diagnostic Fixture Provenance: This analysis was executed on "
                    f"diagnostic/mock fixture data (execution_mode='{exec_mode}'). It does not "
                    "constitute canonical empirical research results."
                ),
                "",
            ]
        )

    lines.extend(
        [
            "---",
            "",
            "## RQ1: Controlled Attribution Accuracy (No-RAG vs. RAG)",
            "",
            (
                "> *Does retrieval augmentation improve exact technique attribution over "
                "unaugmented LLM?*"
            ),
            "",
            "| Condition | End-to-End Acc | 95% CI (Cluster) | Macro-F1 (474) | "
            "Delta Acc vs No-RAG | 95% CI Delta | McNemar p (exact) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    by_cond_rq1 = rq1.get("by_condition", {})
    for cond in CONDITIONS:
        row = by_cond_rq1.get(cond, {})
        acc = f"{row.get('accuracy_end_to_end', 0.0):.4f}"
        ci = row.get("accuracy_e2e_ci_95", [0.0, 0.0])
        ci_str = f"[{ci[0]:.4f}, {ci[1]:.4f}]" if ci and ci[0] is not None else "-"
        f1 = f"{row.get('macro_f1', 0.0):.4f}" if row.get("macro_f1") is not None else "-"

        if row.get("is_baseline"):
            d_str = "Baseline"
            d_ci_str = "-"
            p_str = "-"
        else:
            d_info = row.get("delta_vs_baseline", {})
            d_acc = d_info.get("delta_accuracy_end_to_end")
            rel_acc = d_info.get("relative_gain_accuracy_e2e_pct")
            d_str = (
                f"{d_acc:+.4f} ({rel_acc:+.1f}%)"
                if d_acc is not None and rel_acc is not None
                else "-"
            )
            d_ci = d_info.get("delta_accuracy_e2e_ci_95", [0.0, 0.0])
            d_ci_str = f"[{d_ci[0]:+.4f}, {d_ci[1]:+.4f}]" if d_ci and d_ci[0] is not None else "-"
            mcn = d_info.get("mcnemar_test", {})
            p_val = mcn.get("p_value_exact")
            p_str = f"{p_val:.4e}" if p_val is not None else "-"

        lines.append(f"| `{cond}` | {acc} | {ci_str} | {f1} | {d_str} | {d_ci_str} | {p_str} |")

    lines.extend(
        [
            "",
            f"- **Best RAG Condition**: `{rq1.get('best_rag_condition')}` "
            f"({rq1.get('best_rag_accuracy_delta', 0.0):+.4f} accuracy delta vs No-RAG)",
            "- **Note on Statistical Tests**: Pair-cluster bootstrap resampling resamples paired "
            "views sharing `pair_id` together, preserving intra-pair correlation. These tests are "
            "exploratory diagnostics and do not alter frozen headline protocol metrics.",
            "",
            "---",
            "",
            "## RQ2: Retrieval vs. Generation Error Decomposition",
            "",
            "> *Independent diagnostic failure axes and overlap analysis (Decision D2i).* "
            "*Hit/Recall and conditional metrics are not applicable to No-RAG.*",
            "",
            "| Condition | k | Recall@k | Hit@k | P(Corr | Hit) | P(Corr | Miss) | "
            "Ret Miss | Wrong Class | Prov Fail | Parse Fail | Invalid ID |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | "
            ":---: | :---: | :---: | :---: | :---: |",
        ]
    )

    by_cond_rq2 = rq2.get("by_condition", {})
    for cond in CONDITIONS:
        row = by_cond_rq2.get(cond, {})
        k = row.get("retrieval_k", 0)
        ret = row.get("retrieval_metrics", {})
        rec = f"{ret.get('macro_recall', 0.0):.4f}" if ret.get("macro_recall") is not None else "-"
        hit = (
            f"{ret.get('retrieval_hit_rate', 0.0):.4f}"
            if ret.get("retrieval_hit_rate") is not None
            else "-"
        )

        gen = row.get("generation_conditional_accuracy", {})
        p_succ = (
            f"{gen.get('p_correct_given_retrieval_success', 0.0):.4f}"
            if gen.get("p_correct_given_retrieval_success") is not None
            else "-"
        )
        p_fail = (
            f"{gen.get('p_correct_given_retrieval_failure', 0.0):.4f}"
            if gen.get("p_correct_given_retrieval_failure") is not None
            else "-"
        )

        axes = row.get("independent_failure_axes", {})
        ret_miss = (
            f"{axes.get('retrieval_miss_count', '-')}"
            if axes.get("retrieval_miss_count") is not None
            else "-"
        )
        wrong = f"{axes.get('valid_but_wrong_classification_count', '-')}"
        prov = f"{axes.get('provider_failure_count', '-')}"
        parse = f"{axes.get('parse_failure_count', '-')}"
        inv = f"{axes.get('invalid_attack_id_count', '-')}"

        lines.append(
            f"| `{cond}` | {k} | {rec} | {hit} | {p_succ} | {p_fail} | "
            f"{ret_miss} | {wrong} | {prov} | {parse} | {inv} |"
        )

    lines.extend(
        [
            "",
            "- **Note on Independent Failure Axes**: Evaluated independently per Decision D2i "
            "without forced mutual exclusion or unapproved causal attribution. Overlaps are "
            "explicitly tracked in JSON outputs. Retrieval metrics are not applicable to No-RAG.",
        ]
    )

    lines.extend(
        [
            "",
            "---",
            "",
            "## RQ3: Retrieval Depth, Latency, and Cost Trade-offs",
            "",
            "> *What is the resource trade-off across candidate depths k in {1, 3, 5, 10}?*",
            "",
            "| Condition | k | Mean Lat (ms) | Mean Tokens | Total Cost ($) | "
            "Cost / Logical ($) | Cost / Scorable ($) | Cost / Corr ($) | Excluded ($) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    tradeoffs = rq3.get("tradeoffs_by_condition", {})
    for cond in CONDITIONS:
        row = tradeoffs.get(cond, {})
        k = row.get("retrieval_k", 0)
        lat = row.get("latency_ms", {})
        mean_l = f"{lat.get('mean', 0.0):.1f}" if lat.get("mean") is not None else "-"

        tok = row.get("tokens", {})
        mean_t = (
            f"{tok.get('mean_total_tokens', 0.0):.1f}"
            if tok.get("mean_total_tokens") is not None
            else "-"
        )

        cost = row.get("financial_cost_usd", {})
        tot_c = (
            f"${cost.get('total_cost_usd', 0.0):.5f}"
            if cost.get("total_cost_usd") is not None
            else "-"
        )
        log_c = (
            f"${cost.get('cost_per_logical_request_usd', 0.0):.5f}"
            if cost.get("cost_per_logical_request_usd") is not None
            else "-"
        )
        scor_c = (
            f"${cost.get('cost_per_scorable_query_usd', 0.0):.5f}"
            if cost.get("cost_per_scorable_query_usd") is not None
            else "-"
        )
        corr_c = (
            f"${cost.get('cost_per_correct_attribution_usd', 0.0):.5f}"
            if cost.get("cost_per_correct_attribution_usd") is not None
            else "-"
        )
        excl_c = (
            f"${cost.get('cost_of_all_excluded_views_usd', 0.0):.5f}"
            if cost.get("cost_of_all_excluded_views_usd") is not None
            else "-"
        )

        lines.append(
            f"| `{cond}` | {k} | {mean_l} | {mean_t} | {tot_c} | "
            f"{log_c} | {scor_c} | {corr_c} | {excl_c} |"
        )

    lines.extend(
        [
            "",
            "### Study-Wide Financial Accounting",
            "",
            f"- **Total Study Budget**: `${whole_fin.get('total_study_budget_usd', 19.99):.8f}`",
            f"- **Canonical Conditions Cost**: "
            f"`${whole_fin.get('canonical_conditions_total_usd', 0.0):.8f}`",
            f"- **Prior Pilot Provisional Hold**: "
            f"`${whole_fin.get('prior_pilot_provisional_hold_usd', 0.05264010):.8f}`",
            f"- **Active Reservations**: `${whole_fin.get('active_reservations_usd', 0.0):.8f}`",
            f"- **Total Committed Spend**: "
            f"`${whole_fin.get('total_study_committed_spend_usd', 0.0):.8f}`",
            f"- **Net Available Uncommitted Budget**: "
            f"`${whole_fin.get('net_remaining_uncommitted_budget_usd', 0.0):.8f}`",
            f"- **Study-Wide Missing Usage Charges**: "
            f"{whole_fin.get('study_wide_missing_usage_records_count', 0)} records "
            f"(${whole_fin.get('study_wide_missing_usage_charged_usd', 0.0):.8f})",
            f"- **Financial Policy**: {whole_fin.get('accounting_policy_disclosure', '')}",
            "",
            "### Paired View Diagnostics (Single-View vs Contextual-View)",
            "",
            "> *TEST split scorable cohort contains 278 single views and 440 contextual views.* "
            "*Complete paired analysis evaluates the 278 pairs where both views are scorable.*",
            "",
            "| Condition | Single Acc | Single F1 (474) | Ctx Acc | Ctx F1 (474) | "
            "Single Paired Acc | Ctx Paired Acc | Paired Delta (Ctx - Sgl) | "
            "Both Corr | Ctx Win | Sgl Win | Both Incorr |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | "
            ":---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    views = rq3.get("view_diagnostics", {})
    for cond in CONDITIONS:
        row = views.get(cond, {})
        s_acc = (
            f"{row.get('single_view_accuracy_e2e', 0.0):.4f}"
            if row.get("single_view_accuracy_e2e") is not None
            else "-"
        )
        s_f1 = (
            f"{row.get('single_view_macro_f1', 0.0):.4f}"
            if row.get("single_view_macro_f1") is not None
            else "-"
        )
        c_acc = (
            f"{row.get('contextual_view_accuracy_e2e', 0.0):.4f}"
            if row.get("contextual_view_accuracy_e2e") is not None
            else "-"
        )
        c_f1 = (
            f"{row.get('contextual_view_macro_f1', 0.0):.4f}"
            if row.get("contextual_view_macro_f1") is not None
            else "-"
        )
        s_paired = (
            f"{row.get('single_paired_accuracy', 0.0):.4f}"
            if row.get("single_paired_accuracy") is not None
            else "-"
        )
        c_paired = (
            f"{row.get('contextual_paired_accuracy', 0.0):.4f}"
            if row.get("contextual_paired_accuracy") is not None
            else "-"
        )
        p_delta = row.get("paired_delta")
        p_delta_str = f"{p_delta:+.4f}" if p_delta is not None else "-"

        p_conc = row.get("pair_concordance", {})
        both_c = p_conc.get("both_correct_count", "-")
        ctx_win = p_conc.get("contextual_only_correct_count", "-")
        sgl_win = p_conc.get("single_only_correct_count", "-")
        both_inc = p_conc.get("both_incorrect_count", "-")

        lines.append(
            f"| `{cond}` | {s_acc} | {s_f1} | {c_acc} | {c_f1} | {s_paired} | {c_paired} | "
            f"{p_delta_str} | {both_c} | {ctx_win} | {sgl_win} | {both_inc} |"
        )

    lines.extend(
        [
            "",
            "#### Complete Pair Ground Truth Concordance Decomposition",
            "",
            "> *Stratification of complete scorable pairs (N=278) by ground truth technique "
            "label concordance:*",
            "> *Identical GT: pairs where single and contextual view share identical "
            "ground truth technique labels (N=238).* ",
            "> *Divergent GT: pairs where single and contextual view annotate distinct "
            "ground truth technique labels (N=40).* ",
            "",
            "| Condition | Identical Pairs | Ident Sgl Acc | Ident Ctx Acc | Ident Delta | "
            "Divergent Pairs | Div Sgl Acc | Div Ctx Acc | Div Delta |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for cond in CONDITIONS:
        row = views.get(cond, {})
        decomp = row.get("gt_concordance_decomposition", {})
        ident = decomp.get("identical_gt_pairs", {})
        div = decomp.get("divergent_gt_pairs", {})
        n_ident = ident.get("pair_count", "-")
        i_s_acc = (
            f"{ident.get('single_paired_accuracy', 0.0):.4f}"
            if ident.get("single_paired_accuracy") is not None
            else "-"
        )
        i_c_acc = (
            f"{ident.get('contextual_paired_accuracy', 0.0):.4f}"
            if ident.get("contextual_paired_accuracy") is not None
            else "-"
        )
        i_delta = (
            f"{ident.get('paired_delta', 0.0):+.4f}"
            if ident.get("paired_delta") is not None
            else "-"
        )

        n_div = div.get("pair_count", "-")
        d_s_acc = (
            f"{div.get('single_paired_accuracy', 0.0):.4f}"
            if div.get("single_paired_accuracy") is not None
            else "-"
        )
        d_c_acc = (
            f"{div.get('contextual_paired_accuracy', 0.0):.4f}"
            if div.get("contextual_paired_accuracy") is not None
            else "-"
        )
        d_delta = (
            f"{div.get('paired_delta', 0.0):+.4f}" if div.get("paired_delta") is not None else "-"
        )

        lines.append(
            f"| `{cond}` | {n_ident} | {i_s_acc} | {i_c_acc} | {i_delta} | "
            f"{n_div} | {d_s_acc} | {d_c_acc} | {d_delta} |"
        )

    stratified_producer = analysis_dict.get("new_proposed_producer_stratified_gt_complexity")
    if stratified_producer:
        lines.extend(
            [
                "",
                "---",
                "",
                "## NEW PROPOSED PRODUCER: Stratified Ground Truth Complexity & Subset Analysis",
                "",
                "> [!IMPORTANT]",
                "> **Protocol Approval Required**: This is an exploratory proposed producer that "
                "evaluates scorable views partitioned into Single-GT (N=678 on TEST) vs Multi-GT "
                "(N=40 on TEST under Decision D2a ANY_MATCH). Macro-F1 is evaluated across the "
                "frozen 474-class benchmark universe. Explicit supervisor authorization is "
                "required prior to canonical reporting inclusion.",
                "",
                "| Condition | Single-GT (N) | Single-GT Acc | Single-GT F1 (474) | Multi-GT (N) | "
                "Multi-GT Acc (ANY_MATCH) | Multi-GT F1 (474) | Complexity Delta (Acc) | "
                "Overall Scorable Acc | Overall F1 (Ref) |",
                "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            ]
        )
        by_cond_strat = stratified_producer.get("by_condition", {})
        for cond in CONDITIONS:
            row = by_cond_strat.get(cond, {})
            n_s = row.get("single_gt_sample_count", "-")
            s_acc = (
                f"{row.get('single_gt_accuracy_e2e', 0.0):.4f}"
                if row.get("single_gt_accuracy_e2e") is not None
                else "-"
            )
            s_f1 = (
                f"{row.get('single_gt_macro_f1', 0.0):.4f}"
                if row.get("single_gt_macro_f1") is not None
                else "-"
            )
            n_m = row.get("multi_gt_sample_count", "-")
            m_acc = (
                f"{row.get('multi_gt_accuracy_e2e', 0.0):.4f}"
                if row.get("multi_gt_accuracy_e2e") is not None
                else "-"
            )
            m_f1 = (
                f"{row.get('multi_gt_macro_f1', 0.0):.4f}"
                if row.get("multi_gt_macro_f1") is not None
                else "-"
            )
            c_delta = (
                f"{row.get('complexity_accuracy_delta', 0.0):+.4f}"
                if row.get("complexity_accuracy_delta") is not None
                else "-"
            )
            tot_acc = (
                f"{row.get('overall_scorable_accuracy_e2e', 0.0):.4f}"
                if row.get("overall_scorable_accuracy_e2e") is not None
                else "-"
            )
            tot_f1 = (
                f"{row.get('overall_macro_f1_reference', 0.0):.4f}"
                if row.get("overall_macro_f1_reference") is not None
                else "-"
            )
            lines.append(
                f"| `{cond}` | {n_s} | {s_acc} | {s_f1} | {n_m} | {m_acc} | {m_f1} | "
                f"{c_delta} | {tot_acc} | {tot_f1} |"
            )

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI Entrypoint
# ---------------------------------------------------------------------------


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Offline Research Question Evaluator (RQ1, RQ2, RQ3)"
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        help="Path to run manifest.json",
    )
    parser.add_argument(
        "--run-dir",
        type=Path,
        help="Directory containing run manifest.json and condition prediction files",
    )
    parser.add_argument(
        "--protocol-file",
        type=Path,
        default=Path("config/experiment_protocol_v1.json"),
        help="Path to frozen experiment_protocol_v1.json (resolved against repo root if relative)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("outputs/canonical_analysis"),
        help="Directory to write rq_analysis.json and rq_analysis_summary.md",
    )
    parser.add_argument(
        "--pricing-file",
        type=Path,
        default=Path("config/pricing_v1.json"),
        help="Path to pricing configuration file (resolved against repo root if relative)",
    )
    parser.add_argument(
        "--journal-file",
        type=Path,
        help="Path to request_journal.jsonl (defaults to run_dir/request_journal.jsonl if present)",
    )
    parser.add_argument(
        "--study-ledger-file",
        type=Path,
        help="Path to study_ledger.json (defaults to artifacts/study_budget if present)",
    )
    parser.add_argument(
        "--bootstrap-samples",
        type=int,
        default=1000,
        help="Number of bootstrap resamples for confidence intervals",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible bootstrap sampling",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="Repository root for artifact path resolution (defaults to git repo root)",
    )

    args = parser.parse_args(argv)

    # 1. Consistently determine repository root first
    repo_root = (
        Path(args.repository_root).resolve()
        if args.repository_root
        else Path(__file__).resolve().parents[2]
    )

    # 2. Resolve manifest path
    manifest_path = args.manifest
    if manifest_path is None and args.run_dir is not None:
        run_d = Path(args.run_dir)
        if not run_d.is_absolute():
            run_d = (repo_root / run_d).resolve()
        manifest_path = run_d / "manifest.json"
    elif manifest_path is not None and not manifest_path.is_absolute():
        manifest_path = (repo_root / manifest_path).resolve()

    if manifest_path is None or not manifest_path.is_file():
        print(f"Error: Manifest file not found at {manifest_path}", file=sys.stderr)
        return 1

    # 3. Resolve protocol path relative to repo_root if not absolute
    if args.protocol_file.is_absolute():
        proto_path = args.protocol_file.resolve()
    else:
        proto_path = (repo_root / args.protocol_file).resolve()

    if not proto_path.is_file():
        print(f"Error: Protocol file not found at {proto_path}", file=sys.stderr)
        return 1

    proto_dict = json.loads(proto_path.read_bytes())
    protocol = ScientificProtocolApproval(**proto_dict)

    # 4. Resolve pricing path relative to repo_root if not absolute
    pricing_config = None
    if args.pricing_file is not None:
        if args.pricing_file.is_absolute():
            pricing_path = args.pricing_file.resolve()
        else:
            pricing_path = (repo_root / args.pricing_file).resolve()

        if not pricing_path.is_file():
            print(f"Error: Pricing file not found at {pricing_path}", file=sys.stderr)
            return 1
        pricing_config = json.loads(pricing_path.read_bytes())
        validate_pricing_config(pricing_config)

    # 5. Resolve journal and study ledger paths
    journal_path = None
    if args.journal_file is not None:
        journal_path = (
            args.journal_file.resolve()
            if args.journal_file.is_absolute()
            else (repo_root / args.journal_file).resolve()
        )
    elif (manifest_path.parent / "request_journal.jsonl").is_file():
        journal_path = manifest_path.parent / "request_journal.jsonl"

    study_ledger_path = None
    if args.study_ledger_file is not None:
        study_ledger_path = (
            args.study_ledger_file.resolve()
            if args.study_ledger_file.is_absolute()
            else (repo_root / args.study_ledger_file).resolve()
        )
    elif (repo_root / "artifacts" / "study_budget" / "study_ledger.json").is_file():
        study_ledger_path = repo_root / "artifacts" / "study_budget" / "study_ledger.json"

    # 6. Resolve output directory
    out_dir = args.output_dir
    if not out_dir.is_absolute():
        out_dir = (repo_root / out_dir).resolve()

    manifest_dir = manifest_path.parent
    prediction_paths = {c: manifest_dir / f"{c}_predictions.jsonl" for c in CONDITIONS}

    inputs = load_evaluation_inputs(manifest_path, prediction_paths, repository_root=repo_root)

    print(f"Loaded evaluation inputs for experiment: {inputs.experiment_id}")
    print(f"Evaluating RQ1, RQ2, and RQ3 with {args.bootstrap_samples} bootstrap samples...")

    results = run_rq_analysis(
        inputs,
        protocol,
        pricing_config=pricing_config,
        bootstrap_samples=args.bootstrap_samples,
        seed=args.seed,
        output_dir=out_dir,
        journal_path=journal_path,
        study_ledger_path=study_ledger_path,
        repo_root=repo_root,
    )

    print("Offline evaluation complete. Summary:")
    print(f"  Best RAG Condition (RQ1): {results['rq1']['best_rag_condition']}")
    print(f"  Accuracy Gain vs No-RAG: {results['rq1']['best_rag_accuracy_delta']:+.4f}")
    print(f"  Outputs saved to: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
