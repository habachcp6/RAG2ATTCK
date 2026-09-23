"""Pre-freeze experiment validation and explicitly synthetic runner fixtures.

There is deliberately no live execution or freeze entry point.
"""

from src.experiment.config import load_plan
from src.experiment.schemas import CONDITIONS, ExperimentConfig, ExperimentRecord

__all__ = ["CONDITIONS", "ExperimentConfig", "ExperimentRecord", "load_plan"]
