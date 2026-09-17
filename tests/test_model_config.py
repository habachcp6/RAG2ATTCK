"""Unit tests for model configuration freeze (T11) and prompt freeze (T13).

Verifies:
1. config/model.json exists, is valid JSON, and adheres to the frozen specification.
2. Absence of secrets or API keys in configuration.
3. prompts/baseline_v1.txt exists, contains required placeholders, includes the shared
   generic context instruction, and contains zero forbidden leakage patterns.
4. Symmetrical prompt formatting for No-RAG and RAG conditions.
"""

from __future__ import annotations

import json
import re
from pathlib import Path


WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
MODEL_CONFIG_PATH = WORKSPACE_ROOT / "config" / "model.json"
BASE_PROMPT_PATH = WORKSPACE_ROOT / "prompts" / "baseline_v1.txt"


def test_model_config_file_exists():
    """Verify that config/model.json exists on disk."""
    assert MODEL_CONFIG_PATH.is_file(), f"Missing config file at {MODEL_CONFIG_PATH}"


def test_model_config_valid_json():
    """Verify that config/model.json parses as valid JSON."""
    with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
    assert isinstance(config, dict)
    assert len(config) > 0


def test_model_config_required_fields():
    """Verify presence and correctness of all required model configuration fields."""
    with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Core provider and model identifier
    assert config.get("provider") == "openai"
    assert config.get("model") == "gpt-5.6-luna"
    assert config.get("reasoning_effort") == "xhigh"

    # API interface — Responses API is the sole frozen experimental interface
    assert config.get("api_interface") == "responses"
    assert "fallback_api_interface" not in config, "Fallback API interface must not exist in frozen config"

    # Token budget (Responses API uses max_output_tokens only)
    assert "max_output_tokens" in config
    assert isinstance(config["max_output_tokens"], int)
    assert config["max_output_tokens"] >= 8192, "Output budget must account for xhigh reasoning tokens"
    assert "max_completion_tokens" not in config, "Chat Completions token budget must not exist in frozen config"

    # Execution controls
    assert isinstance(config.get("timeout_seconds"), (int, float))
    assert config["timeout_seconds"] > 0
    assert config.get("retry_policy") == "exponential_backoff"
    assert isinstance(config.get("max_retries"), int)
    assert config["max_retries"] >= 1


def test_model_config_structured_output_and_logging():
    """Verify structured output format specification and logging policies."""
    with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    # Structured output configuration
    structured_output = config.get("structured_output")
    assert isinstance(structured_output, dict)
    assert structured_output.get("format") == "json_schema"
    assert structured_output.get("strict") is True

    # Logging policy configuration
    logging_policy = config.get("logging_policy")
    assert isinstance(logging_policy, dict)
    assert logging_policy.get("log_token_usage") is True
    assert logging_policy.get("log_latency") is True
    assert logging_policy.get("log_prompt_version") is True
    assert logging_policy.get("log_condition") is True
    assert logging_policy.get("log_raw_response") is False


def test_model_config_zero_secrets():
    """Verify that config/model.json contains absolutely no API keys or secrets."""
    raw_content = MODEL_CONFIG_PATH.read_text(encoding="utf-8")

    # Check for OpenAI API key patterns
    secret_pattern = re.compile(r"sk-[A-Za-z0-9_-]{20,}")
    assert not secret_pattern.search(raw_content), "Detected possible OpenAI secret key in config/model.json"

    # Check that no field contains hardcoded secret values
    with open(MODEL_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    def scan_for_secrets(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                lower_k = k.lower()
                # Field names that would indicate leaked credentials
                if lower_k in {"api_key", "secret", "password", "token", "private_key"}:
                    # Must not contain actual credentials
                    assert not isinstance(v, str) or not v.strip() or v.startswith("$"), (
                        f"Found credential-bearing field '{path}.{k}' with value"
                    )
                scan_for_secrets(v, f"{path}.{k}")
        elif isinstance(obj, list):
            for idx, item in enumerate(obj):
                scan_for_secrets(item, f"{path}[{idx}]")
        elif isinstance(obj, str):
            assert not obj.startswith("sk-"), f"Secret prefix detected at {path}: {obj[:10]}..."

    scan_for_secrets(config)


def test_base_prompt_file_exists():
    """Verify that prompts/baseline_v1.txt exists and is non-empty."""
    assert BASE_PROMPT_PATH.is_file(), f"Missing base prompt file at {BASE_PROMPT_PATH}"
    prompt_text = BASE_PROMPT_PATH.read_text(encoding="utf-8").strip()
    assert len(prompt_text) > 100, "Base prompt appears unexpectedly brief or empty"


def test_base_prompt_required_placeholders():
    """Verify presence of exact {ENDPOINT_EVIDENCE} and {RETRIEVED_CONTEXT} placeholders."""
    prompt_text = BASE_PROMPT_PATH.read_text(encoding="utf-8")
    assert "{ENDPOINT_EVIDENCE}" in prompt_text, "Missing {ENDPOINT_EVIDENCE} placeholder in baseline prompt"
    assert "{RETRIEVED_CONTEXT}" in prompt_text, "Missing {RETRIEVED_CONTEXT} placeholder in baseline prompt"


def test_base_prompt_shared_generic_instruction():
    """Verify exact presence of the shared generic context handling instruction."""
    prompt_text = BASE_PROMPT_PATH.read_text(encoding="utf-8")
    expected_instruction = (
        "If reference context is provided below, use it as supporting information for the attribution. "
        "If no reference context is provided, perform the attribution using the endpoint evidence alone."
    )
    assert expected_instruction in prompt_text, (
        "Base prompt must contain verbatim shared generic instruction for context handling to preserve "
        "symmetric reasoning across No-RAG and RAG conditions."
    )


def test_base_prompt_prohibited_leakage_patterns():
    """Verify that prompts/baseline_v1.txt contains no answer-bearing or forbidden metadata patterns."""
    prompt_text = BASE_PROMPT_PATH.read_text(encoding="utf-8")
    lower_text = prompt_text.lower()

    prohibited_patterns = [
        "rule.mitre",
        "wazuh",
        "ground_truth",
        "dataset_id",
        "b8fmtzvpy8",
        "detector_description",
        "rule_description",
    ]

    for pattern in prohibited_patterns:
        assert pattern not in lower_text, f"Prohibited leakage pattern '{pattern}' detected in base prompt!"


def test_base_prompt_formatting_symmetry():
    """Verify that base prompt can be formatted cleanly for both No-RAG (empty context) and RAG."""
    prompt_template = BASE_PROMPT_PATH.read_text(encoding="utf-8")
    test_evidence = "EventID: 1 | Image: C:\\Windows\\System32\\cmd.exe | CommandLine: whoami /all"

    # Test No-RAG formatting (RETRIEVED_CONTEXT is empty string)
    no_rag_prompt = prompt_template.replace("{RETRIEVED_CONTEXT}", "").replace("{ENDPOINT_EVIDENCE}", test_evidence)
    assert test_evidence in no_rag_prompt
    assert "{ENDPOINT_EVIDENCE}" not in no_rag_prompt
    assert "{RETRIEVED_CONTEXT}" not in no_rag_prompt

    # Test RAG formatting (RETRIEVED_CONTEXT populated with mock ATT&CK knowledge)
    mock_rag_context = "Technique: Command and Scripting Interpreter (T1059)\nDescription: Adversaries may execute commands..."
    rag_prompt = prompt_template.replace("{RETRIEVED_CONTEXT}", mock_rag_context).replace("{ENDPOINT_EVIDENCE}", test_evidence)
    assert mock_rag_context in rag_prompt
    assert test_evidence in rag_prompt
    assert "{ENDPOINT_EVIDENCE}" not in rag_prompt
    assert "{RETRIEVED_CONTEXT}" not in rag_prompt
