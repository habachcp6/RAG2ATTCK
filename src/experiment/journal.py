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

import os
from enum import Enum
from pathlib import Path
from typing import Any

from src.experiment.config import canonical_bytes, parse_jsonl


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


def append_journal_event(journal_path: Path, event: dict[str, Any]) -> None:
    """Durably append a canonical event row to the journal file with immediate fsync."""
    with journal_path.open("ab") as stream:
        stream.write(canonical_bytes(event) + b"\n")
        stream.flush()
        os.fsync(stream.fileno())


def read_journal_events(journal_path: Path) -> list[dict[str, Any]]:
    """Read and parse all canonical events from a durable journal file."""
    return parse_jsonl(journal_path.read_bytes())
