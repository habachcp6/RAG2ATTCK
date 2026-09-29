"""Request journal state machine for experiment execution tracking.

At minimum distinguishes:
- RESERVED
- DISPATCH_STARTED
- RESPONSE_RECEIVED
- PARSED
- RECORD_COMMITTED

If execution crashes after dispatch but before durable confirmation:
do not blindly retry. That state is ambiguous and fails closed.
"""

from __future__ import annotations

from enum import Enum
from typing import Any


class RequestState(str, Enum):
    """Explicit lifecycle states for each sample-condition request."""

    IDLE = "IDLE"
    RESERVED = "RESERVED"
    DISPATCH_STARTED = "DISPATCH_STARTED"
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    PARSED = "PARSED"
    RECORD_COMMITTED = "RECORD_COMMITTED"


class RequestJournalStateMachine:
    """Tracks and validates transitions through the durable request lifecycle."""

    _VALID_TRANSITIONS: dict[RequestState, set[RequestState]] = {
        RequestState.IDLE: {RequestState.RESERVED},
        RequestState.RESERVED: {RequestState.DISPATCH_STARTED},
        RequestState.DISPATCH_STARTED: {RequestState.RESPONSE_RECEIVED},
        RequestState.RESPONSE_RECEIVED: {RequestState.PARSED},
        RequestState.PARSED: {RequestState.RECORD_COMMITTED},
        RequestState.RECORD_COMMITTED: set(),
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
