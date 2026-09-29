"""Execution authorization and gate enforcement for live experiment execution.

LIVE EXECUTION DEFAULT = DENY.
Real calls must never execute without explicit, validated human authorization
and an immutable, hash-bound scientific protocol approval contract (D1-D7).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from src.experiment.config import canonical_bytes, digest

if TYPE_CHECKING:
    from src.experiment.config import ValidatedPlan


class LiveExecutionBlockedError(RuntimeError):
    """Raised whenever live execution is blocked by safety or protocol gates."""


class ProtocolNotFrozenError(LiveExecutionBlockedError):
    """Raised when scientific protocol decisions (D1-D7) remain unresolved or invalid."""


class HumanAuthorizationRequiredError(LiveExecutionBlockedError):
    """Raised when explicit human authorization token or approval is absent."""


class LiveBudgetRequiredError(LiveExecutionBlockedError):
    """Raised when finite positive request budget is missing or invalid."""


ALLOWED_PROTOCOL_VALUES: dict[str, set[str]] = {
    "d1_raw_response_policy": {"RECORD_ONLY", "DISCARD", "LOG_SEPARATELY"},
    "d2a_ground_truth_semantics": {"PRIMARY_ONLY", "ANY_MATCH", "ALL_MATCH"},
    "d2b_empty_ground_truth": {"EXCLUDE", "TREAT_AS_NEGATIVE"},
    "d2c_ambiguous_ground_truth": {"EXCLUDE", "DISALLOW_CORRECT"},
    "d2d_macro_f1_universe": {"BENCHMARK_PREDICTED_ONLY", "FULL_ATTACK_UNIVERSE"},
    "d2e_invalid_id_denominator": {"INCLUDE_IN_DENOMINATOR", "EXCLUDE_FROM_DENOMINATOR"},
    "d2f_api_error_denominator": {"INCLUDE_IN_DENOMINATOR", "EXCLUDE_FROM_DENOMINATOR"},
    "d2g_retired_attack_id": {"ALLOW_HISTORICAL", "FAIL_VALIDATION"},
    "d2h_conditional_retrieval": {"RANK_AT_K", "ANY_RANK_IN_CANDIDATES"},
    "d2i_failure_precedence": {"API_ERROR_FIRST", "PARSE_STATUS_FIRST"},
    "d2j_zero_denominator": {"ZERO", "NAN", "UNDEFINED"},
    "d3_model_version_policy": {
        "CAPTURED_SNAPSHOT_OR_FAIL",
        "ALLOW_LATEST_WITH_TIMESTAMP_BINDING",
    },
    "d4_concurrency_policy": {"SEQUENTIAL_ONLY", "BOUNDED_POOL"},
    "d5_budget_policy": {"HARD_CAP_WORST_CASE_ATTEMPTS", "LOGICAL_SAMPLES_CAP"},
    "d6_t15_prerequisite_policy": {
        "NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK",
        "PREREQUISITE_PILOT_SATISFIED",
    },
    "d7_dataset_scope": {"FULL_BENCHMARK", "DEV_SMOKE", "PAIRED_TEST"},
}


@dataclass(frozen=True)
class ScientificProtocolApproval:
    """Immutable scientific protocol approval contract binding D1-D7 decisions.

    The actual scientific decisions must NOT be chosen by automated agents.
    Only explicit human-approved scientific protocol contracts may authorize execution.
    """

    protocol_version: str
    protocol_sha256: str
    d1_raw_response_policy: str
    d2a_ground_truth_semantics: str
    d2b_empty_ground_truth: str
    d2c_ambiguous_ground_truth: str
    d2d_macro_f1_universe: str
    d2e_invalid_id_denominator: str
    d2f_api_error_denominator: str
    d2g_retired_attack_id: str
    d2h_conditional_retrieval: str
    d2i_failure_precedence: str
    d2j_zero_denominator: str
    d3_model_version_policy: str
    d4_concurrency_policy: str
    d5_budget_policy: str
    d6_t15_prerequisite_policy: str
    d7_dataset_scope: str
    approval_timestamp: str
    approval_reference: str


def protocol_decision_dict(protocol: ScientificProtocolApproval) -> dict[str, Any]:
    """Extract canonical mapping of protocol decisions excluding the self-referential hash."""
    return {
        "protocol_version": protocol.protocol_version,
        "d1_raw_response_policy": protocol.d1_raw_response_policy,
        "d2a_ground_truth_semantics": protocol.d2a_ground_truth_semantics,
        "d2b_empty_ground_truth": protocol.d2b_empty_ground_truth,
        "d2c_ambiguous_ground_truth": protocol.d2c_ambiguous_ground_truth,
        "d2d_macro_f1_universe": protocol.d2d_macro_f1_universe,
        "d2e_invalid_id_denominator": protocol.d2e_invalid_id_denominator,
        "d2f_api_error_denominator": protocol.d2f_api_error_denominator,
        "d2g_retired_attack_id": protocol.d2g_retired_attack_id,
        "d2h_conditional_retrieval": protocol.d2h_conditional_retrieval,
        "d2i_failure_precedence": protocol.d2i_failure_precedence,
        "d2j_zero_denominator": protocol.d2j_zero_denominator,
        "d3_model_version_policy": protocol.d3_model_version_policy,
        "d4_concurrency_policy": protocol.d4_concurrency_policy,
        "d5_budget_policy": protocol.d5_budget_policy,
        "d6_t15_prerequisite_policy": protocol.d6_t15_prerequisite_policy,
        "d7_dataset_scope": protocol.d7_dataset_scope,
        "approval_timestamp": protocol.approval_timestamp,
        "approval_reference": protocol.approval_reference,
    }


def compute_protocol_sha256(decisions: dict[str, Any]) -> str:
    """Compute deterministic SHA-256 over canonical JSON of protocol decisions."""
    return digest(canonical_bytes(decisions))


def create_test_protocol_approval(
    *,
    protocol_version: str = "test-protocol-v1",
    d1_raw_response_policy: str = "RECORD_ONLY",
    d2a_ground_truth_semantics: str = "PRIMARY_ONLY",
    d2b_empty_ground_truth: str = "EXCLUDE",
    d2c_ambiguous_ground_truth: str = "EXCLUDE",
    d2d_macro_f1_universe: str = "BENCHMARK_PREDICTED_ONLY",
    d2e_invalid_id_denominator: str = "INCLUDE_IN_DENOMINATOR",
    d2f_api_error_denominator: str = "INCLUDE_IN_DENOMINATOR",
    d2g_retired_attack_id: str = "ALLOW_HISTORICAL",
    d2h_conditional_retrieval: str = "RANK_AT_K",
    d2i_failure_precedence: str = "API_ERROR_FIRST",
    d2j_zero_denominator: str = "ZERO",
    d3_model_version_policy: str = "CAPTURED_SNAPSHOT_OR_FAIL",
    d4_concurrency_policy: str = "SEQUENTIAL_ONLY",
    d5_budget_policy: str = "HARD_CAP_WORST_CASE_ATTEMPTS",
    d6_t15_prerequisite_policy: str = "NOT_REQUIRED_FOR_SYNTHETIC_BENCHMARK",
    d7_dataset_scope: str = "PAIRED_TEST",
    approval_timestamp: str = "2026-09-30T00:00:00+00:00",
    approval_reference: str = "TEST_PROTOCOL_APPROVAL_REF",
    tamper_hash: bool = False,
) -> ScientificProtocolApproval:
    """Construct an explicit TEST-ONLY scientific protocol approval object for unit tests.

    DOES NOT APPROVE SCIENTIFIC PRODUCTION PROTOCOL.
    """
    decisions = {
        "protocol_version": protocol_version,
        "d1_raw_response_policy": d1_raw_response_policy,
        "d2a_ground_truth_semantics": d2a_ground_truth_semantics,
        "d2b_empty_ground_truth": d2b_empty_ground_truth,
        "d2c_ambiguous_ground_truth": d2c_ambiguous_ground_truth,
        "d2d_macro_f1_universe": d2d_macro_f1_universe,
        "d2e_invalid_id_denominator": d2e_invalid_id_denominator,
        "d2f_api_error_denominator": d2f_api_error_denominator,
        "d2g_retired_attack_id": d2g_retired_attack_id,
        "d2h_conditional_retrieval": d2h_conditional_retrieval,
        "d2i_failure_precedence": d2i_failure_precedence,
        "d2j_zero_denominator": d2j_zero_denominator,
        "d3_model_version_policy": d3_model_version_policy,
        "d4_concurrency_policy": d4_concurrency_policy,
        "d5_budget_policy": d5_budget_policy,
        "d6_t15_prerequisite_policy": d6_t15_prerequisite_policy,
        "d7_dataset_scope": d7_dataset_scope,
        "approval_timestamp": approval_timestamp,
        "approval_reference": approval_reference,
    }
    computed_hash = compute_protocol_sha256(decisions)
    return ScientificProtocolApproval(
        protocol_version=protocol_version,
        protocol_sha256="00" * 32 if tamper_hash else computed_hash,
        d1_raw_response_policy=d1_raw_response_policy,
        d2a_ground_truth_semantics=d2a_ground_truth_semantics,
        d2b_empty_ground_truth=d2b_empty_ground_truth,
        d2c_ambiguous_ground_truth=d2c_ambiguous_ground_truth,
        d2d_macro_f1_universe=d2d_macro_f1_universe,
        d2e_invalid_id_denominator=d2e_invalid_id_denominator,
        d2f_api_error_denominator=d2f_api_error_denominator,
        d2g_retired_attack_id=d2g_retired_attack_id,
        d2h_conditional_retrieval=d2h_conditional_retrieval,
        d2i_failure_precedence=d2i_failure_precedence,
        d2j_zero_denominator=d2j_zero_denominator,
        d3_model_version_policy=d3_model_version_policy,
        d4_concurrency_policy=d4_concurrency_policy,
        d5_budget_policy=d5_budget_policy,
        d6_t15_prerequisite_policy=d6_t15_prerequisite_policy,
        d7_dataset_scope=d7_dataset_scope,
        approval_timestamp=approval_timestamp,
        approval_reference=approval_reference,
    )


def validate_scientific_protocol(
    protocol: ScientificProtocolApproval | None,
    plan: ValidatedPlan | None = None,
) -> None:
    """Validate all D1-D7 protocol decisions and verify cryptographic hash binding."""
    if protocol is None:
        raise ProtocolNotFrozenError(
            "LIVE_EXECUTION_BLOCKED: scientific protocol decisions (D1-D7) remain "
            "HUMAN_DECISION_REQUIRED and are not frozen"
        )

    if not isinstance(protocol, ScientificProtocolApproval):
        raise ProtocolNotFrozenError(
            f"Expected ScientificProtocolApproval instance, got {type(protocol).__name__}"
        )

    if not protocol.protocol_version or not protocol.protocol_version.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: protocol_version must not be empty")

    # Validate all required decision policies
    for decision_field, allowed_values in ALLOWED_PROTOCOL_VALUES.items():
        val = getattr(protocol, decision_field, None)
        if not val or not isinstance(val, str) or val.strip() == "":
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: {decision_field} must be approved and non-empty"
            )
        if val not in allowed_values:
            options = sorted(allowed_values)
            raise ProtocolNotFrozenError(
                f"LIVE_EXECUTION_BLOCKED: {decision_field} must be in {options}, got '{val}'"
            )

    # Validate approval reference and timestamp
    if not protocol.approval_reference or not protocol.approval_reference.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: approval_reference must not be empty")
    if not protocol.approval_timestamp or not protocol.approval_timestamp.strip():
        raise ProtocolNotFrozenError("LIVE_EXECUTION_BLOCKED: approval_timestamp must not be empty")

    # Verify cryptographic hash binding
    decisions = protocol_decision_dict(protocol)
    expected_sha256 = compute_protocol_sha256(decisions)
    if protocol.protocol_sha256 != expected_sha256:
        raise ProtocolNotFrozenError(
            f"LIVE_EXECUTION_BLOCKED: protocol SHA-256 hash mismatch: expected {expected_sha256}, "
            f"got {protocol.protocol_sha256}"
        )

    # If plan is provided, check compatibility
    if plan is not None:
        if protocol.d4_concurrency_policy == "SEQUENTIAL_ONLY":
            if plan.config.execution.concurrency not in (None, 1):
                raise ProtocolNotFrozenError(
                    "LIVE_EXECUTION_BLOCKED: plan concurrency contradicts SEQUENTIAL_ONLY"
                )


@dataclass(frozen=True)
class ExecutionAuthorization:
    """Explicit human runtime execution authorization required before live dispatch."""

    human_approval_token: str
    approved_protocol_sha256: str | None = None
    authorized_max_provider_attempts: int | None = None
    allow_live_dispatch: bool = False
    # Backward compatibility fields:
    authorized_max_requests: int | None = None
    scientific_protocol_approved: bool = False
    d1_raw_response_policy_approved: str | None = None
    d7_dataset_scope_approved: str | None = None


def validate_live_authorization(
    authorization: ExecutionAuthorization | None,
    plan: ValidatedPlan,
    protocol: ScientificProtocolApproval | None = None,
) -> None:
    """Validate all gates before any live provider dispatch can occur.

    Default is FAIL-CLOSED (DENY).
    Requires explicit human authorization and hash-bound protocol approval.
    """
    if authorization is None:
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: execution authorization is missing; default is DENY"
        )

    if not isinstance(authorization, ExecutionAuthorization):
        raise LiveExecutionBlockedError(
            f"Expected ExecutionAuthorization instance, got {type(authorization).__name__}"
        )

    budget_cap = (
        authorization.authorized_max_provider_attempts
        if authorization.authorized_max_provider_attempts is not None
        else authorization.authorized_max_requests
    )

    # Gate 1: Scientific Protocol Decisions (D1-D7)
    if protocol is None:
        if not authorization.scientific_protocol_approved:
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: scientific protocol decisions (D1-D7) remain "
                "HUMAN_DECISION_REQUIRED and are not frozen"
            )
        if authorization.d1_raw_response_policy_approved not in {
            "RECORD_ONLY",
            "DISCARD",
            "LOG_SEPARATELY",
        }:
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: D1 raw response policy must be explicitly approved "
                "(RECORD_ONLY, DISCARD, LOG_SEPARATELY)"
            )
        if authorization.d7_dataset_scope_approved not in {
            "FULL_BENCHMARK",
            "DEV_SMOKE",
            "PAIRED_TEST",
        }:
            raise ProtocolNotFrozenError(
                "LIVE_EXECUTION_BLOCKED: D7 dataset scope must be explicitly approved "
                "(FULL_BENCHMARK, DEV_SMOKE, PAIRED_TEST)"
            )
    else:
        validate_scientific_protocol(protocol, plan)
        if authorization.approved_protocol_sha256 is not None:
            if authorization.approved_protocol_sha256 != protocol.protocol_sha256:
                raise ProtocolNotFrozenError(
                    "LIVE_EXECUTION_BLOCKED: authorized protocol SHA-256 does not match protocol"
                )

    # Gate 2: Explicit non-empty human authorization token
    if (
        not authorization.human_approval_token
        or not authorization.human_approval_token.strip()
    ):
        raise HumanAuthorizationRequiredError(
            "LIVE_EXECUTION_BLOCKED: non-empty human approval token is required"
        )

    # Gate 3: Live dispatch must be explicitly enabled
    if not authorization.allow_live_dispatch:
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: allow_live_dispatch flag must be True"
        )

    # Gate 4: Explicit finite request budget (provider attempts)
    if budget_cap is None:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: explicit finite request budget is required"
        )

    if budget_cap < 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized_max_requests cannot be negative"
        )

    if budget_cap == 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized request budget cannot be zero"
        )

    from src.experiment.schemas import CONDITIONS

    required_calls = len(plan.samples) * len(CONDITIONS)
    if budget_cap < required_calls:
        raise LiveBudgetRequiredError(
            f"LIVE_EXECUTION_BLOCKED: authorized budget ({budget_cap}) "
            f"cannot cover the required matrix calls ({required_calls})"
        )


def check_live_execution_gates(
    plan: ValidatedPlan,
    authorization: ExecutionAuthorization | None = None,
    protocol: ScientificProtocolApproval | None = None,
) -> dict[str, Any]:
    """Inspect authorization status and return non-executing gate report."""
    try:
        validate_live_authorization(authorization, plan, protocol=protocol)
        return {
            "status": "AUTHORIZED",
            "provider_calls": 0,
            "prediction_writes": 0,
            "live_execution_permitted": True,
        }
    except (LiveExecutionBlockedError, TypeError, ValueError) as exc:
        return {
            "status": "LIVE_EXECUTION_BLOCKED",
            "reason": str(exc),
            "provider_calls": 0,
            "prediction_writes": 0,
            "live_execution_permitted": False,
        }
