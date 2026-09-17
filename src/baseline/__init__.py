"""
RAG2ATTCK - Baseline Module (Milestone M2)
Baseline pipeline execution helper for No-RAG condition.
"""

from src.baseline.pipeline import (
    BaselinePipeline,
    format_baseline_prompt,
)
from src.baseline.smoke import (
    load_smoke_cases,
    run_failure_pathways_suite,
    run_smoke_test_pipeline,
)

__all__ = [
    "BaselinePipeline",
    "format_baseline_prompt",
    "load_smoke_cases",
    "run_failure_pathways_suite",
    "run_smoke_test_pipeline",
]
