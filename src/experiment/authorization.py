"""Execution authorization and gate enforcement for live experiment execution.

LIVE EXECUTION DEFAULT = DENY.
Real calls must never execute without explicit, validated human authorization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.experiment.config import ValidatedPlan


class LiveExecutionBlockedError(RuntimeError):
    """Raised whenever live execution is blocked by safety or protocol gates."""


class ProtocolNotFrozenError(LiveExecutionBlockedError):
    """Raised when scientific protocol decisions (D1-D7) remain unresolved."""


class HumanAuthorizationRequiredError(LiveExecutionBlockedError):
    """Raised when explicit human authorization token or approval is absent."""


class LiveBudgetRequiredError(LiveExecutionBlockedError):
    """Raised when finite positive request budget is missing or invalid."""


@dataclass(frozen=True)
class ExecutionAuthorization:
    """Explicit human authorization required before any live provider call."""

    human_approval_token: str
    scientific_protocol_approved: bool = False
    authorized_max_requests: int | None = None
    allow_live_dispatch: bool = False
    d1_raw_response_policy_approved: str | None = None
    d7_dataset_scope_approved: str | None = None


def validate_live_authorization(
    authorization: ExecutionAuthorization | None,
    plan: ValidatedPlan,
) -> None:
    """Validate all gates before any live provider dispatch can occur.

    Default is FAIL-CLOSED (DENY).
    """
    if authorization is None:
        raise LiveExecutionBlockedError(
            "LIVE_EXECUTION_BLOCKED: execution authorization is missing; default is DENY"
        )

    if not isinstance(authorization, ExecutionAuthorization):
        raise LiveExecutionBlockedError(
            f"Expected ExecutionAuthorization instance, got {type(authorization).__name__}"
        )

    # Gate 1: Scientific Protocol Decisions (D1-D7) must be explicitly human-approved
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

    # Gate 4: Explicit finite request budget
    if authorization.authorized_max_requests is None:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: explicit finite request budget is required"
        )

    if authorization.authorized_max_requests < 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized_max_requests cannot be negative"
        )

    if authorization.authorized_max_requests == 0:
        raise LiveBudgetRequiredError(
            "LIVE_EXECUTION_BLOCKED: authorized request budget cannot be zero"
        )

    from src.experiment.schemas import CONDITIONS

    required_calls = len(plan.samples) * len(CONDITIONS)
    if authorization.authorized_max_requests < required_calls:
        raise LiveBudgetRequiredError(
            f"LIVE_EXECUTION_BLOCKED: authorized budget ({authorization.authorized_max_requests}) "
            f"cannot cover the required matrix calls ({required_calls})"
        )


def check_live_execution_gates(
    plan: ValidatedPlan,
    authorization: ExecutionAuthorization | None = None,
) -> dict[str, Any]:
    """Inspect authorization status and return non-executing gate report."""
    try:
        validate_live_authorization(authorization, plan)
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
