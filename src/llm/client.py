"""
RAG2ATTCK - Unified LLM Client Module (Milestone M2, Tasks T12, R2, R3)
Implements:
- Unified client loading config/model.json
- OpenAI Responses API primary interface with Chat Completions API fallback
- Generic prediction interface supporting No-RAG (retrieved_context=None) vs RAG
- 7 mutually exclusive parse statuses:
  VALID, INVALID_ID, MALFORMED_RESPONSE, REFUSAL, INCOMPLETE, API_FAILURE, TIMEOUT
- Strict post-hoc two-layer ATT&CK ID validation (syntax regex + v19.2 registry)
- Global live-request budget enforcement (max 5 actual live requests including retries)
- Precision wall-clock latency measurement including retries and backoff
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable, Dict, Optional, Set, Tuple

import openai

from src.llm.schemas import (
    ExecutionRecord,
    ParseStatus,
    TechniquePrediction,
    get_workspace_root,
    validate_technique_id,
)
from src.llm.logging import WallClockTimer

logger = logging.getLogger("rag2attck.llm.client")


# ---------------------------------------------------------------------------
# 1. Global Live Request Budget
# ---------------------------------------------------------------------------

class LiveBudgetExceededError(RuntimeError):
    """Raised when the global live API request budget is exhausted."""
    pass


class LiveBudget:
    """
    Thread-safe live request budget tracker.
    Strictly caps actual live network requests (including retries) across the application lifecycle.
    """

    def __init__(self, max_requests: int = 5) -> None:
        self.max_requests = max_requests
        self._count = 0
        self._lock = threading.Lock()

    def consume(self) -> int:
        """
        Consumes one unit of live budget.
        Raises LiveBudgetExceededError if budget is exhausted.
        """
        with self._lock:
            if self._count >= self.max_requests:
                raise LiveBudgetExceededError(
                    f"Global live request budget exhausted: attempted call exceeds limit of {self.max_requests} requests."
                )
            self._count += 1
            return self._count

    def reset(self) -> None:
        """Resets the live request counter (primarily for testing)."""
        with self._lock:
            self._count = 0

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    @property
    def remaining(self) -> int:
        with self._lock:
            return max(0, self.max_requests - self._count)

    def is_exhausted(self) -> bool:
        with self._lock:
            return self._count >= self.max_requests


GLOBAL_LIVE_BUDGET = LiveBudget(max_requests=5)


def get_live_request_count() -> int:
    """Return the current number of consumed live requests."""
    return GLOBAL_LIVE_BUDGET.count


def reset_live_budget() -> None:
    """Reset global live request budget counter."""
    GLOBAL_LIVE_BUDGET.reset()


# ---------------------------------------------------------------------------
# 2. Unified LLM Client Implementation
# ---------------------------------------------------------------------------

class LLMClient:
    """
    Unified LLM client for RAG2ATTCK experiments.
    Shared identically across No-RAG and RAG conditions.
    """

    def __init__(
        self,
        config_path: Optional[Path | str] = None,
        config_dict: Optional[Dict[str, Any]] = None,
        openai_client: Optional[Any] = None,
        api_key: Optional[str] = None,
        registry_ids: Optional[Set[str]] = None,
        stix_path: Optional[Path | str] = None,
        live_budget: Optional[LiveBudget] = None,
        is_live: Optional[bool] = None,
        sleep_fn: Optional[Callable[[float], None]] = None,
    ) -> None:
        self.ws_root = get_workspace_root()

        # Load configuration
        if config_dict is not None:
            self.config = config_dict
        else:
            c_path = Path(config_path) if config_path else (self.ws_root / "config" / "model.json")
            if not c_path.exists():
                raise FileNotFoundError(f"Model configuration not found at {c_path}")
            with open(c_path, "r", encoding="utf-8") as f:
                self.config = json.load(f)

        # Extract config settings
        self.provider = self.config.get("provider", "openai")
        self.model = self.config.get("model", "gpt-5.6-luna")
        self.reasoning_effort = self.config.get("reasoning_effort", "xhigh")
        self.api_interface = self.config.get("api_interface", "responses")
        self.fallback_api_interface = self.config.get("fallback_api_interface", "chat_completions")
        self.max_output_tokens = self.config.get("max_output_tokens", 8192)
        self.max_completion_tokens = self.config.get("max_completion_tokens", 8192)
        self.timeout_seconds = float(self.config.get("timeout_seconds", 120))
        self.max_retries = int(self.config.get("max_retries", 3))
        self.retry_initial_delay = float(self.config.get("retry_initial_delay_seconds", 1.0))
        self.retry_backoff_factor = float(self.config.get("retry_backoff_factor", 2.0))
        self.retry_max_delay = float(self.config.get("retry_max_delay_seconds", 30.0))

        # ATT&CK Registry for post-hoc validation
        self.registry_ids = registry_ids
        self.stix_path = stix_path

        # Live budget tracker
        self.live_budget = live_budget or GLOBAL_LIVE_BUDGET
        self.sleep_fn = sleep_fn or time.sleep

        # Client setup
        secret_env_var = self.config.get("secret_policy", {}).get("env_var_name", "OPENAI_API_KEY")
        resolved_key = api_key or os.environ.get(secret_env_var, "").strip() or None

        if openai_client is not None:
            self.client = openai_client
            self.is_live = False if is_live is None else is_live
        else:
            if not resolved_key and (is_live is True):
                raise ValueError("OPENAI_API_KEY environment variable is required for live LLM client execution.")
            self.client = openai.OpenAI(
                api_key=resolved_key or "unauthenticated",
                timeout=self.timeout_seconds,
            )
            self.is_live = True if is_live is None else is_live

    def _is_retryable_error(self, exc: Exception) -> bool:
        """Determines whether an exception is retryable (transient network/server/rate limit/timeout error)."""
        if isinstance(exc, LiveBudgetExceededError):
            return False

        if isinstance(exc, (openai.APITimeoutError, TimeoutError)):
            return True

        if isinstance(exc, (openai.RateLimitError, openai.InternalServerError, openai.APIConnectionError)):
            return True

        err_str = str(exc).lower()
        if any(term in err_str for term in ["timeout", "timed out", "rate limit", "connection reset", "503", "502", "500"]):
            return True

        return False

    def _call_responses_api(self, prompt: str) -> Any:
        """Execute request using Responses API."""
        if not hasattr(self.client, "responses") or not hasattr(self.client.responses, "create"):
            raise NotImplementedError("OpenAI client does not support Responses API")

        return self.client.responses.create(
            model=self.model,
            input=prompt,
            reasoning={"effort": self.reasoning_effort},
            max_output_tokens=self.max_output_tokens,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "attack_technique_prediction",
                    "schema": TechniquePrediction.model_json_schema(),
                    "strict": True,
                }
            },
            timeout=self.timeout_seconds,
        )

    def _call_chat_completions_api(self, prompt: str) -> Any:
        """Execute request using Chat Completions API fallback."""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            reasoning_effort=self.reasoning_effort,
            max_completion_tokens=self.max_completion_tokens,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "attack_technique_prediction",
                    "schema": TechniquePrediction.model_json_schema(),
                    "strict": True,
                }
            },
            timeout=self.timeout_seconds,
        )

    def _extract_response_content_and_status(
        self,
        response: Any,
        used_interface: str
    ) -> Tuple[Optional[str], Optional[ParseStatus], Optional[str], Optional[int], Optional[int]]:
        """
        Extracts raw response text, detects upfront refusal or incompleteness,
        and retrieves token accounting metrics.
        Returns: (raw_text, upfront_status, upfront_reason, input_tokens, output_tokens)
        """
        input_tokens: Optional[int] = None
        output_tokens: Optional[int] = None

        # Extract token usage if available
        usage = getattr(response, "usage", None)
        if usage is not None:
            input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)

        if used_interface == "responses":
            # Check response status
            resp_status = getattr(response, "status", None)
            if resp_status == "refused" or getattr(response, "refusal", None):
                refusal_msg = getattr(response, "refusal", None) or "Model refused attribution request"
                return None, ParseStatus.REFUSAL, str(refusal_msg), input_tokens, output_tokens

            if resp_status == "incomplete":
                incomplete_details = getattr(response, "incomplete_details", None)
                reason = f"Response incomplete: {incomplete_details}" if incomplete_details else "Response terminated before completion"
                return None, ParseStatus.INCOMPLETE, reason, input_tokens, output_tokens

            # Extract output text
            raw_text = getattr(response, "output_text", None)
            if raw_text is None:
                # Handle structured output items
                outputs = getattr(response, "output", None)
                if outputs and isinstance(outputs, list):
                    for item in outputs:
                        if hasattr(item, "content") and item.content:
                            for c in item.content:
                                if hasattr(c, "text"):
                                    raw_text = c.text
                                    break
            return raw_text, None, None, input_tokens, output_tokens

        else:
            # Chat Completions
            choices = getattr(response, "choices", [])
            if not choices:
                return None, ParseStatus.MALFORMED_RESPONSE, "Chat Completions returned zero choices", input_tokens, output_tokens

            choice = choices[0]
            finish_reason = getattr(choice, "finish_reason", None)
            msg = getattr(choice, "message", None)

            # Refusal check
            if finish_reason == "refusal" or (msg and getattr(msg, "refusal", None)):
                refusal_reason = getattr(msg, "refusal", None) if msg else None
                return None, ParseStatus.REFUSAL, str(refusal_reason or "Model refused request"), input_tokens, output_tokens

            # Incomplete check
            if finish_reason in ("length", "max_tokens"):
                return None, ParseStatus.INCOMPLETE, f"Response reached max tokens (finish_reason='{finish_reason}')", input_tokens, output_tokens

            raw_text = getattr(msg, "content", None) if msg else None
            return raw_text, None, None, input_tokens, output_tokens

    def _post_hoc_validate_prediction(
        self,
        raw_text: Optional[str]
    ) -> Tuple[ParseStatus, Optional[str], Optional[str]]:
        """
        Post-hoc parsing and validation of LLM output.
        Returns: (parse_status, predicted_technique_id, invalid_reason)
        """
        if raw_text is None or not str(raw_text).strip():
            return ParseStatus.MALFORMED_RESPONSE, None, "Response content is empty or null."

        # Step 1: Parse JSON
        try:
            payload = json.loads(raw_text)
        except Exception as e:
            return ParseStatus.MALFORMED_RESPONSE, None, f"Response is not valid JSON: {str(e)}"

        if not isinstance(payload, dict):
            return ParseStatus.MALFORMED_RESPONSE, None, f"Response JSON must be an object, got {type(payload).__name__}"

        if "technique_id" not in payload:
            return ParseStatus.MALFORMED_RESPONSE, None, "Missing required 'technique_id' field in response JSON."

        # Step 2: Validate Pydantic Schema
        try:
            pred = TechniquePrediction.model_validate(payload)
        except Exception as e:
            return ParseStatus.MALFORMED_RESPONSE, None, f"Schema validation failed: {str(e)}"

        extracted_id = pred.technique_id

        # Step 3: Mandatory Two-Layer Post-Hoc Validation
        is_valid, val_status, val_reason = validate_technique_id(
            extracted_id,
            registry_ids=self.registry_ids,
            stix_path=self.stix_path
        )

        return val_status, extracted_id, val_reason

    def predict(
        self,
        sample_id: str,
        endpoint_evidence: str,
        retrieved_context: Optional[str] = None,
        condition: str = "no_rag",
        prompt_template: Optional[str] = None,
        prompt_version: str = "baseline_v1",
    ) -> ExecutionRecord:
        """
        Executes prediction for a single sample.
        
        Args:
            sample_id: Unique identifier for the telemetry sample
            endpoint_evidence: Sanitized Windows endpoint log string
            retrieved_context: None or empty for No-RAG; populated for RAG
            condition: "no_rag" or "rag"
            prompt_template: Custom prompt template string (defaults to loading prompts/baseline_v1.txt)
            prompt_version: Version identifier of prompt template
            
        Returns:
            ExecutionRecord containing complete metadata and validation status.
        """
        # Load prompt template if not provided
        if prompt_template is None:
            p_file = self.ws_root / "prompts" / f"{prompt_version}.txt"
            if not p_file.exists():
                raise FileNotFoundError(f"Prompt template file not found at {p_file}")
            prompt_template = p_file.read_text(encoding="utf-8")

        # Symmetric prompt construction
        context_str = retrieved_context if retrieved_context is not None else ""
        formatted_prompt = (
            prompt_template
            .replace("{RETRIEVED_CONTEXT}", context_str)
            .replace("{ENDPOINT_EVIDENCE}", endpoint_evidence)
        )

        retry_count = 0
        error_type: Optional[str] = None
        last_error_msg: Optional[str] = None
        response_obj: Any = None
        used_interface = self.api_interface
        raw_text: Optional[str] = None
        upfront_status: Optional[ParseStatus] = None
        upfront_reason: Optional[str] = None

        with WallClockTimer() as timer:
            for attempt in range(self.max_retries + 1):
                try:
                    # Enforce live budget before dispatching actual network call
                    if self.is_live:
                        self.live_budget.consume()

                    # Attempt primary API interface
                    if self.api_interface == "responses":
                        try:
                            response_obj = self._call_responses_api(formatted_prompt)
                            used_interface = "responses"
                        except (NotImplementedError, AttributeError, openai.BadRequestError, openai.NotFoundError) as api_err:
                            logger.warning(
                                "Responses API call failed (%s), falling back to Chat Completions API",
                                api_err
                            )
                            response_obj = self._call_chat_completions_api(formatted_prompt)
                            used_interface = "chat_completions"
                    else:
                        response_obj = self._call_chat_completions_api(formatted_prompt)
                        used_interface = "chat_completions"

                    # Successfully received response
                    break

                except Exception as exc:
                    error_type = type(exc).__name__
                    last_error_msg = str(exc)

                    if isinstance(exc, LiveBudgetExceededError):
                        # Immediately fail on budget exhaustion without retry
                        break

                    if self._is_retryable_error(exc) and attempt < self.max_retries:
                        retry_count += 1
                        delay = min(
                            self.retry_initial_delay * (self.retry_backoff_factor ** attempt),
                            self.retry_max_delay
                        )
                        logger.info(
                            "Transient error on attempt %d: %s. Retrying in %.2fs (retry %d/%d)...",
                            attempt + 1,
                            exc,
                            delay,
                            retry_count,
                            self.max_retries
                        )
                        self.sleep_fn(delay)
                        continue
                    else:
                        # Non-retryable or retries exhausted
                        break

        # Compute elapsed wall-clock latency
        latency_ms = timer.elapsed_ms

        # Determine terminal status
        if response_obj is None:
            # Check if failure was caused by timeout
            is_timeout = (
                error_type in ("APITimeoutError", "TimeoutError")
                or (last_error_msg and "timeout" in last_error_msg.lower())
            )
            final_status = ParseStatus.TIMEOUT if is_timeout else ParseStatus.API_FAILURE
            return ExecutionRecord(
                sample_id=sample_id,
                condition=condition,
                provider=self.provider,
                model=self.model,
                reasoning_effort=self.reasoning_effort,
                prompt_version=prompt_version,
                predicted_technique_id=None,
                parse_status=final_status,
                invalid_reason=last_error_msg,
                input_tokens=None,
                output_tokens=None,
                latency_ms=latency_ms,
                retry_count=retry_count,
                error_type=error_type,
            )

        # Inspect response
        raw_text, upfront_status, upfront_reason, in_tok, out_tok = self._extract_response_content_and_status(
            response_obj,
            used_interface
        )

        if upfront_status is not None:
            return ExecutionRecord(
                sample_id=sample_id,
                condition=condition,
                provider=self.provider,
                model=self.model,
                reasoning_effort=self.reasoning_effort,
                prompt_version=prompt_version,
                predicted_technique_id=None,
                parse_status=upfront_status,
                invalid_reason=upfront_reason,
                input_tokens=in_tok,
                output_tokens=out_tok,
                latency_ms=latency_ms,
                retry_count=retry_count,
                error_type=None,
            )

        # Post-hoc parsing and validation
        post_hoc_status, pred_id, inv_reason = self._post_hoc_validate_prediction(raw_text)

        return ExecutionRecord(
            sample_id=sample_id,
            condition=condition,
            provider=self.provider,
            model=self.model,
            reasoning_effort=self.reasoning_effort,
            prompt_version=prompt_version,
            predicted_technique_id=pred_id,
            parse_status=post_hoc_status,
            invalid_reason=inv_reason,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_ms=latency_ms,
            retry_count=retry_count,
            error_type=None,
        )
