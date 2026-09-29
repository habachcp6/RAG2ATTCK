"""Pre-freeze experiment validation and explicitly synthetic runner fixtures.

There is deliberately no live execution or freeze entry point.
"""

from src.experiment.authorization import (
    ExecutionAuthorization,
    LiveExecutionBlockedError,
    validate_live_authorization,
)
from src.experiment.config import load_plan
from src.experiment.journal import RequestJournalStateMachine, RequestState
from src.experiment.runner import run_live_experiment, run_mock_experiment
from src.experiment.schemas import CONDITIONS, ExperimentConfig, ExperimentRecord

__all__ = [
    "CONDITIONS",
    "ExecutionAuthorization",
    "ExperimentConfig",
    "ExperimentRecord",
    "LiveExecutionBlockedError",
    "RequestJournalStateMachine",
    "RequestState",
    "load_plan",
    "run_live_experiment",
    "run_mock_experiment",
    "validate_live_authorization",
]

