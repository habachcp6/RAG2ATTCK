"""Versioned infrastructure contracts; the canonical prediction schema is unchanged."""

from datetime import datetime, timedelta
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.llm.schemas import ParseStatus

CONDITIONS = ("no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10")
DEPTHS = (1, 3, 5, 10)
Condition = Literal["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]
SHA256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Nonempty = Annotated[str, Field(min_length=1)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Artifact(StrictModel):
    path: Nonempty
    sha256: SHA256


class ExperimentIdentity(StrictModel):
    name: Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9_-]*$")]
    version: Nonempty
    status: Literal["pre_freeze"]


class Dataset(StrictModel):
    benchmark: Literal["synthetic-paired-v1"]
    split: Literal["test"]
    expected_sample_count: Annotated[int, Field(gt=0)]
    expected_pair_count: Annotated[int, Field(gt=0)]
    inference: Artifact
    ground_truth: Artifact
    manifest: Artifact
    views: Artifact
    pairs: Artifact
    split_manifest: Artifact


class Attack(StrictModel):
    release: Literal["19.2"]
    corpus: Artifact
    index: Artifact
    document_mapping: Artifact
    retrieval_manifest: Artifact
    registry: Artifact


class Retrieval(StrictModel):
    config: Artifact
    embedding_model: Nonempty
    embedding_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    embedding_dimension: Annotated[int, Field(gt=0)]
    index_type: Literal["IndexFlatIP"]
    normalization: Literal["L2"]
    metric: Literal["cosine"]
    depths: list[int]

    @model_validator(mode="after")
    def exact_depths(self):
        if tuple(self.depths) != DEPTHS:
            raise ValueError("retrieval depths must be exactly [1, 3, 5, 10]")
        return self


class Generation(StrictModel):
    config: Artifact
    provider: Literal["openai"]
    model: Nonempty
    model_version: Nonempty | None
    reasoning_effort: Nonempty
    api_interface: Literal["responses"]
    temperature: Literal["provider_default"]
    seed: Literal["provider_default"]
    max_output_tokens: Annotated[int, Field(gt=0)]


class Prompt(StrictModel):
    template: Artifact
    version: Literal["baseline_v1"]


class Execution(StrictModel):
    retries: Annotated[int, Field(ge=0)]
    timeout_seconds: Annotated[int, Field(gt=0)]
    concurrency: Annotated[int, Field(gt=0)] | None
    max_requests: Annotated[int, Field(ge=0)] | None
    resume: Literal[True]
    fail_closed: Literal[True]


class Logging(StrictModel):
    raw_response: Literal[False]
    parsed_prediction: Literal[True]
    tokens: Literal[True]
    latency: Literal[True]
    retries: Literal[True]
    error_status: Literal[True]
    retrieval_candidates: Literal[True]


class ExperimentConfig(StrictModel):
    schema_version: Literal["1.0.0"]
    experiment: ExperimentIdentity
    dataset: Dataset
    attack: Attack
    retrieval: Retrieval
    conditions: list[Condition]
    generation: Generation
    prompt: Prompt
    execution: Execution
    logging: Logging

    @model_validator(mode="after")
    def exact_conditions(self):
        if tuple(self.conditions) != CONDITIONS:
            raise ValueError("conditions must contain the exact ordered five-condition matrix")
        return self


class Candidate(StrictModel):
    technique_id: Annotated[str, Field(pattern=r"^T[0-9]{4}(?:\.[0-9]{3})?$")]
    rank: Annotated[int, Field(gt=0)]
    score: Annotated[float, Field(allow_inf_nan=False)]


class ExperimentRecord(StrictModel):
    schema_version: Literal["1.0.0"]
    execution_mode: Literal["mock_fixture"]
    experiment_id: Nonempty
    run_id: Nonempty
    manifest_sha256: SHA256
    sample_id: Nonempty
    pair_id: Nonempty
    view_type: Literal["single", "contextual"]
    condition: Condition
    retrieval_k: int
    provider: Nonempty
    model: Nonempty
    model_version: Nonempty | None
    prompt_sha256: SHA256
    model_config_sha256: SHA256
    output_schema_sha256: SHA256
    dataset_sha256: SHA256
    ground_truth_sha256: SHA256
    ground_truth_version: Nonempty
    attack_release: Literal["19.2"]
    corpus_sha256: SHA256
    index_sha256: SHA256
    retrieved_candidates: list[Candidate]
    raw_response: None
    raw_response_logged: Literal[False]
    parsed_technique_ids: Annotated[list[str], Field(max_length=1)]
    parse_status: Literal[
        "VALID",
        "INVALID_ID",
        "MALFORMED_RESPONSE",
        "REFUSAL",
        "INCOMPLETE",
        "API_FAILURE",
        "TIMEOUT",
    ]
    prompt_tokens: Annotated[int, Field(ge=0)] | None
    completion_tokens: Annotated[int, Field(ge=0)] | None
    total_tokens: Annotated[int, Field(ge=0)] | None
    latency_ms: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    retry_count: Annotated[int, Field(ge=0)]
    request_attempt_count: Annotated[int, Field(gt=0)]
    error_type: str | None
    error_message: str | None
    success: bool
    timestamp: Annotated[str, Field(pattern=r"^\d{4}-\d\d-\d\dT.*\+00:00$")]
    terminal: Literal[True]

    @model_validator(mode="after")
    def consistency(self):
        expected_k = 0 if self.condition == "no_rag" else int(self.condition[5:])
        if self.retrieval_k != expected_k or len(self.retrieved_candidates) != expected_k:
            raise ValueError("condition, retrieval_k and candidate length disagree")
        if [c.rank for c in self.retrieved_candidates] != list(range(1, expected_k + 1)):
            raise ValueError("candidate ranks must be contiguous")
        if len({c.technique_id for c in self.retrieved_candidates}) != expected_k:
            raise ValueError("duplicate retrieved candidate")
        if self.success != (self.parse_status == ParseStatus.VALID.value):
            raise ValueError("success must describe VALID parsing, never ground-truth correctness")
        if self.parse_status in {"VALID", "INVALID_ID"}:
            if len(self.parsed_technique_ids) != 1:
                raise ValueError("parsed status requires one technique ID")
        elif self.parsed_technique_ids:
            raise ValueError("unparsed terminal status cannot have a technique ID")
        total = (
            None
            if self.prompt_tokens is None or self.completion_tokens is None
            else self.prompt_tokens + self.completion_tokens
        )
        if self.total_tokens != total:
            raise ValueError("total_tokens must preserve unknown component usage")
        if datetime.fromisoformat(self.timestamp).utcoffset() != timedelta(0):
            raise ValueError("timestamp must be an actual ISO timestamp in UTC")
        if self.retry_count > self.request_attempt_count - 1:
            raise ValueError("retry_count exceeds dispatched retry attempts")
        return self
