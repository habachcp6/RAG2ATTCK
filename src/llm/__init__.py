"""
RAG2ATTCK - LLM Module (Milestone M2)
Unified LLM client, schemas, logging, and two-layer ATT&CK ID validation.
"""

from src.llm.schemas import (
    ExecutionRecord,
    ParseStatus,
    TechniquePrediction,
    load_attack_registry,
    reset_attack_registry_cache,
    validate_attack_id_syntax,
    validate_technique_id,
)
from src.llm.logging import (
    WallClockTimer,
    format_execution_summary,
    log_execution,
    save_records_csv,
    save_records_jsonl,
    serialize_record,
)
from src.llm.client import (
    GLOBAL_LIVE_BUDGET,
    LiveBudget,
    LiveBudgetExceededError,
    LLMClient,
    get_live_request_count,
    reset_live_budget,
)

__all__ = [
    "ParseStatus",
    "TechniquePrediction",
    "ExecutionRecord",
    "validate_attack_id_syntax",
    "load_attack_registry",
    "reset_attack_registry_cache",
    "validate_technique_id",
    "WallClockTimer",
    "serialize_record",
    "log_execution",
    "save_records_jsonl",
    "save_records_csv",
    "format_execution_summary",
    "LLMClient",
    "LiveBudget",
    "LiveBudgetExceededError",
    "GLOBAL_LIVE_BUDGET",
    "get_live_request_count",
    "reset_live_budget",
]
