"""
RAG2ATTCK - LLM Prediction and Execution Metadata Schemas (Milestone M2)
Defines:
- TechniquePrediction: Pydantic model for structured prediction {"technique_id": "..."}
- ParseStatus: 7 mutually exclusive parse statuses
- ExecutionRecord: Metadata schema tracking full execution provenance
- Two-layer post-hoc ATT&CK ID validation (syntax regex + v19.2 registry membership)
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
import re
from typing import Any, Dict, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# 1. Parse Status Taxonomy (7 Mutually Exclusive Statuses)
# ---------------------------------------------------------------------------

class ParseStatus(str, Enum):
    """
    Mutually exclusive parse status taxonomy for LLM prediction evaluation.
    """
    VALID = "VALID"
    INVALID_ID = "INVALID_ID"
    MALFORMED_RESPONSE = "MALFORMED_RESPONSE"
    REFUSAL = "REFUSAL"
    INCOMPLETE = "INCOMPLETE"
    API_FAILURE = "API_FAILURE"
    TIMEOUT = "TIMEOUT"


# ---------------------------------------------------------------------------
# 2. Prediction Schema
# ---------------------------------------------------------------------------

class TechniquePrediction(BaseModel):
    """
    Minimal structured prediction payload returned by LLM:
    {"technique_id": "T1059.001"}
    
    Note: Strict format validation is deliberately omitted from the Pydantic schema
    so that syntactically invalid or non-registry IDs successfully pass JSON/schema parsing
    and are subsequently categorized as INVALID_ID by post-hoc validation (rather than MALFORMED_RESPONSE).
    """
    technique_id: str = Field(
        ...,
        description="The predicted MITRE ATT&CK Technique or Sub-technique ID."
    )

    model_config = ConfigDict(
        extra="forbid",
        frozen=True
    )


# ---------------------------------------------------------------------------
# 3. Execution Metadata Record Schema
# ---------------------------------------------------------------------------

class ExecutionRecord(BaseModel):
    """
    Execution metadata record capturing complete runtime and validation provenance.
    Schema fields:
    sample_id, condition, provider, model, reasoning_effort, prompt_version,
    predicted_technique_id, parse_status, invalid_reason,
    input_tokens, output_tokens, latency_ms, retry_count, error_type
    """
    sample_id: str
    condition: str
    provider: str = "openai"
    model: str = "gpt-5.6-luna"
    reasoning_effort: Optional[str] = "xhigh"
    prompt_version: str = "baseline_v1"
    predicted_technique_id: Optional[str] = None
    parse_status: ParseStatus
    invalid_reason: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: float
    retry_count: int = 0
    error_type: Optional[str] = None

    model_config = ConfigDict(
        extra="forbid",
        use_enum_values=True
    )

    @property
    def is_valid(self) -> bool:
        """Convenience property indicating whether prediction is valid."""
        return self.parse_status == ParseStatus.VALID.value or self.parse_status == ParseStatus.VALID

    def to_dict(self) -> Dict[str, Any]:
        """Serialize record to dictionary."""
        return self.model_dump()

    def to_json(self) -> str:
        """Serialize record to JSON string."""
        return self.model_dump_json()


# ---------------------------------------------------------------------------
# 4. Two-Layer Post-Hoc ATT&CK ID Validation
# ---------------------------------------------------------------------------

ATTACK_ID_PATTERN = re.compile(r"^T[0-9]{4}(?:\.[0-9]{3})?$")

_CACHED_REGISTRY_IDS: Optional[Set[str]] = None


def validate_attack_id_syntax(technique_id: str) -> bool:
    """
    Layer 1: Syntax validation.
    Checks whether technique_id matches canonical format:
    T#### (Technique) or T####.### (Sub-technique).
    """
    if not isinstance(technique_id, str):
        return False
    return bool(ATTACK_ID_PATTERN.fullmatch(technique_id))


def get_workspace_root() -> Path:
    """Resolve repository/workspace root."""
    cur = Path(__file__).resolve().parent
    for p in [cur] + list(cur.parents):
        if (p / "config" / "model.json").exists() or (p / "pyproject.toml").exists():
            return p
    return Path.cwd()


def load_attack_registry(stix_path: Optional[Path | str] = None) -> Set[str]:
    """
    Loads Enterprise ATT&CK v19.2 technique and sub-technique IDs using src/attack_loader.py.
    Caches results in memory for high-throughput post-hoc validation.
    """
    global _CACHED_REGISTRY_IDS
    if stix_path is None and _CACHED_REGISTRY_IDS is not None:
        return _CACHED_REGISTRY_IDS

    if stix_path is None:
        ws = get_workspace_root()
        target_path = ws / "attack" / "raw" / "enterprise-v19.2" / "enterprise-attack-19.2.json"
    else:
        target_path = Path(stix_path)

    if not target_path.exists():
        raise FileNotFoundError(
            f"Enterprise ATT&CK v19.2 STIX file not found at {target_path}."
        )

    # Use existing attack_loader to parse STIX bundle
    from src.attack_loader import parse_attack_bundle
    techniques_dict = parse_attack_bundle(target_path)
    loaded_ids = set(techniques_dict.keys())

    if stix_path is None:
        _CACHED_REGISTRY_IDS = loaded_ids

    return loaded_ids


def reset_attack_registry_cache() -> None:
    """Resets the cached in-memory ATT&CK registry (useful in test teardown)."""
    global _CACHED_REGISTRY_IDS
    _CACHED_REGISTRY_IDS = None


def validate_technique_id(
    technique_id: str,
    registry_ids: Optional[Set[str]] = None,
    stix_path: Optional[Path | str] = None,
) -> Tuple[bool, ParseStatus, Optional[str]]:
    """
    Mandatory Two-Layer Post-Hoc ATT&CK ID Validation.
    
    Pipeline:
    1. Layer 1: Syntax validation against regex ^T\\d{4}(?:\\.\\d{3})?$
       - Failure -> returns (False, ParseStatus.INVALID_ID, invalid_reason)
    2. Layer 2: Membership check in pinned Enterprise ATT&CK v19.2 registry
       - Failure -> returns (False, ParseStatus.INVALID_ID, invalid_reason)
    3. Success:
       - Both pass -> returns (True, ParseStatus.VALID, None)
       
    CRITICAL RESEARCH INTEGRITY RULE:
    This function is strictly post-hoc. It must only be invoked AFTER generation,
    and must never be used to guide, retry, or prompt the LLM.
    """
    # Layer 1: Syntax check
    if not validate_attack_id_syntax(technique_id):
        return (
            False,
            ParseStatus.INVALID_ID,
            f"Syntax error: '{technique_id}' does not conform to canonical MITRE ATT&CK ID format '^T\\d{{4}}(?:\\.\\d{{3}})?$'."
        )

    # Layer 2: Registry membership check
    valid_ids = registry_ids if registry_ids is not None else load_attack_registry(stix_path)
    if technique_id not in valid_ids:
        return (
            False,
            ParseStatus.INVALID_ID,
            f"Registry error: '{technique_id}' passes syntax check but does not exist in Enterprise ATT&CK v19.2 registry."
        )

    return True, ParseStatus.VALID, None
