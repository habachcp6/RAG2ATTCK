"""Request journal state machine for experiment execution tracking.

At minimum distinguishes:
- RESERVED
- DISPATCH_STARTED
- RESPONSE_RECEIVED
- PARSED
- RECORD_COMMITTED
- RESERVATION_ABANDONED (explicit closure during safe crash recovery)

If execution crashes after dispatch but before durable confirmation:
do not blindly retry. That state is ambiguous and fails closed.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

from src.experiment.config import canonical_bytes, parse_jsonl

EVENT_RESERVATION_ABANDONED = "reservation_abandoned"


class RequestState(str, Enum):
    """Explicit lifecycle states for each sample-condition request."""

    IDLE = "IDLE"
    RESERVED = "RESERVED"
    DISPATCH_STARTED = "DISPATCH_STARTED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    PARSED = "PARSED"
    RECORD_COMMITTED = "RECORD_COMMITTED"
    RESERVATION_ABANDONED = "RESERVATION_ABANDONED"


class RequestJournalStateMachine:
    """Tracks and validates transitions through the durable request lifecycle."""

    _VALID_TRANSITIONS: dict[RequestState, set[RequestState]] = {
        RequestState.IDLE: {RequestState.RESERVED},
        RequestState.RESERVED: {
            RequestState.DISPATCH_STARTED,
            RequestState.RESERVATION_ABANDONED,
        },
        RequestState.DISPATCH_STARTED: {RequestState.RESPONSE_RECEIVED},
        RequestState.RESPONSE_RECEIVED: {RequestState.PARSED},
        RequestState.PARSED: {RequestState.RECORD_COMMITTED},
        RequestState.RECORD_COMMITTED: set(),
        RequestState.RESERVATION_ABANDONED: set(),
    }

    def __init__(self, key: tuple[str, str] | None = None) -> None:
        self.key = key
        self.state = RequestState.IDLE
        self.history: list[tuple[RequestState, dict[str, Any]]] = []

    def transition_to(
        self, new_state: RequestState, metadata: dict[str, Any] | None = None
    ) -> None:
        """Enforce valid transition sequence."""
        valid_targets = self._VALID_TRANSITIONS.get(self.state, set())
        if new_state not in valid_targets:
            raise ValueError(
                f"Invalid request state transition: {self.state.value} -> {new_state.value} "
                f"for key {self.key}"
            )
        self.state = new_state
        self.history.append((new_state, metadata or {}))

    def abandon_reservation(self) -> None:
        """Explicitly abandon a RESERVED request during safe crash recovery."""
        if self.state != RequestState.RESERVED:
            raise ValueError(
                f"Cannot abandon reservation in state {self.state.value} for key {self.key}: "
                "must be in RESERVED state"
            )
        self.transition_to(
            RequestState.RESERVATION_ABANDONED,
            {"event": EVENT_RESERVATION_ABANDONED},
        )

    @property
    def is_in_flight(self) -> bool:
        """True if the request has been dispatched but not yet committed."""
        return self.state in {
            RequestState.DISPATCH_STARTED,
            RequestState.RESPONSE_RECEIVED,
            RequestState.PARSED,
        }

    @property
    def is_committed(self) -> bool:
        return self.state == RequestState.RECORD_COMMITTED

    @property
    def is_abandoned(self) -> bool:
        return self.state == RequestState.RESERVATION_ABANDONED


def validate_live_transition(
    current_state: RequestState | None,
    target_state: RequestState,
    consumed: int,
    start: int,
) -> RequestState:
    """Validate and enforce ordered live request journal state transitions.

    Enforce:
    - RESERVED: allowed only when current_state is None (IDLE).
    - DISPATCH_STARTED: allowed only when current_state == RequestState.RESERVED.
    - RESPONSE_RECEIVED: allowed only when current_state == RequestState.DISPATCH_STARTED
      and consumed > start (at least one provider attempt occurred).
    - PARSED: allowed only when current_state == RequestState.RESPONSE_RECEIVED.
    - RECORD_COMMITTED: allowed only when current_state == RequestState.PARSED.

    Args:
        current_state: Active request state before transition (or None if IDLE).
        target_state: Desired target RequestState.
        consumed: Cumulative provider attempts consumed so far.
        start: Cumulative provider attempts consumed when this request was reserved/begun.

    Returns:
        The validated target_state.

    Raises:
        ValueError: If transition violates the strict live execution order or invariants.
    """
    if not isinstance(target_state, RequestState):
        try:
            target_state = RequestState(target_state)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid target state: {target_state}") from exc

    if current_state is not None and not isinstance(current_state, RequestState):
        try:
            current_state = RequestState(current_state)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid current state: {current_state}") from exc

    if target_state == RequestState.RESERVED:
        if current_state is not None and current_state != RequestState.IDLE:
            raise ValueError(
                f"Cannot transition to RESERVED from state {current_state.value}: "
                "request must be IDLE (None)"
            )
        return RequestState.RESERVED

    if target_state == RequestState.DISPATCH_STARTED:
        if current_state != RequestState.RESERVED:
            current_desc = current_state.value if current_state else "None"
            raise ValueError(
                f"Cannot transition to DISPATCH_STARTED from state {current_desc}: "
                "expected RESERVED"
            )
        return RequestState.DISPATCH_STARTED

    if target_state == RequestState.RESPONSE_RECEIVED:
        if current_state != RequestState.DISPATCH_STARTED:
            current_desc = current_state.value if current_state else "None"
            raise ValueError(
                f"Cannot transition to RESPONSE_RECEIVED from state {current_desc}: "
                "expected DISPATCH_STARTED"
            )
        if consumed <= start:
            raise ValueError(
                "Cannot transition to RESPONSE_RECEIVED: "
                f"at least one provider attempt required (consumed={consumed}, start={start})"
            )
        return RequestState.RESPONSE_RECEIVED

    if target_state == RequestState.PARSED:
        if current_state != RequestState.RESPONSE_RECEIVED:
            current_desc = current_state.value if current_state else "None"
            raise ValueError(
                f"Cannot transition to PARSED from state {current_desc}: expected RESPONSE_RECEIVED"
            )
        return RequestState.PARSED

    if target_state == RequestState.RECORD_COMMITTED:
        if current_state != RequestState.PARSED:
            current_desc = current_state.value if current_state else "None"
            raise ValueError(
                f"Cannot transition to RECORD_COMMITTED from state {current_desc}: expected PARSED"
            )
        return RequestState.RECORD_COMMITTED

    raise ValueError(f"Invalid target state for live transition: {target_state}")


def validate_attempt_event(
    current_state: RequestState | None,
    key: tuple[str, ...],
    event_key: tuple[str, ...],
    ordinal: int,
    expected_ordinal: int,
) -> None:
    """Validate an attempt journal accounting event.

    Attempt rows are accounting events, not state transitions. They are only valid
    while a request is actively in DISPATCH_STARTED (outbound dispatch in flight).

    Args:
        current_state: Active request state.
        key: Active request key tuple.
        event_key: Attempt event key tuple.
        ordinal: Attempt ordinal reported in the event.
        expected_ordinal: Expected monotonic attempt ordinal (e.g. consumed + 1).

    Raises:
        ValueError: If attempt occurs outside DISPATCH_STARTED, keys mismatch,
            or ordinal is not the expected sequential integer.
    """
    if current_state is not None and not isinstance(current_state, RequestState):
        try:
            current_state = RequestState(current_state)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid current state: {current_state}") from exc

    if current_state != RequestState.DISPATCH_STARTED:
        current_desc = current_state.value if current_state else "None"
        raise ValueError(
            f"Attempt event not allowed in state {current_desc}: must be in DISPATCH_STARTED"
        )

    if tuple(key) != tuple(event_key):
        raise ValueError(f"Attempt event key mismatch: active key {key} != event key {event_key}")

    if type(ordinal) is not int or ordinal != expected_ordinal:
        raise ValueError(f"Invalid attempt ordinal: got {ordinal!r}, expected {expected_ordinal!r}")


def validate_reservation_abandonment(
    current_state: RequestState | None,
    key: tuple[str, ...],
    event_key: tuple[str, ...] | list[Any],
    consumed: int,
    start: int,
) -> None:
    """Validate a canonical reservation abandonment event during crash recovery.

    The abandonment event means:
    - Reservation existed (current_state == RequestState.RESERVED).
    - Zero provider attempts occurred (consumed == start).
    - The reservation was explicitly closed during safe crash recovery.

    It MUST NOT consume budget and MUST NOT count as a provider attempt.
    If dispatch has started or any attempt occurred, fail closed (human reconciliation required).

    Args:
        current_state: Active request state.
        key: Active request key tuple.
        event_key: Abandonment event key.
        consumed: Cumulative provider attempts consumed.
        start: Cumulative provider attempts consumed at reservation start.

    Raises:
        ValueError: If state is not RESERVED, keys mismatch, or attempts occurred.
    """
    if current_state is not None and not isinstance(current_state, RequestState):
        try:
            current_state = RequestState(current_state)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid current state: {current_state}") from exc

    if current_state != RequestState.RESERVED:
        current_desc = current_state.value if current_state else "None"
        raise ValueError(
            f"Cannot abandon reservation in state {current_desc}: must be in RESERVED state"
        )

    if tuple(key) != tuple(event_key):
        raise ValueError(
            f"Reservation abandonment key mismatch: active key {key} != event key {event_key}"
        )

    if consumed != start:
        raise ValueError(
            f"Cannot abandon reservation: attempts have occurred "
            f"(consumed={consumed}, start={start})"
        )


def make_reservation_abandoned_event(
    key: tuple[str, ...] | list[Any],
) -> dict[str, Any]:
    """Create a canonical durable reservation_abandoned event dict."""
    return {
        "event": EVENT_RESERVATION_ABANDONED,
        "key": list(key),
    }


create_reservation_abandoned_event = make_reservation_abandoned_event


def append_journal_event(journal_path: Path, event: dict[str, Any]) -> None:
    """Durably append a canonical event row to the journal file with immediate fsync."""
    with journal_path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_journal_events(journal_path: Path) -> list[dict[str, Any]]:
    """Read and parse all canonical events from a durable journal file."""
    return parse_jsonl(journal_path.read_bytes())


__all__ = [
    "EVENT_RESERVATION_ABANDONED",
    "RequestJournalStateMachine",
    "RequestState",
    "append_journal_event",
    "create_reservation_abandoned_event",
    "make_reservation_abandoned_event",
    "read_journal_events",
    "validate_attempt_event",
    "validate_live_transition",
    "validate_reservation_abandonment",
]
