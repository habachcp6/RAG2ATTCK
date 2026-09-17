"""
Unit tests for mandatory two-layer post-hoc ATT&CK ID validation (Milestone M2, Task R3).

Verifies:
1. Layer 1: Syntax regex validation (^T\\d{4}(?:\\.\\d{3})?$).
   - Valid root technique IDs (T####)
   - Valid sub-technique IDs (T####.###)
   - Syntactically invalid strings (e.g. malformed prefix, wrong digit count, whitespace, case)
2. Layer 2: Frozen Enterprise ATT&CK v19.2 registry membership check via src/attack_loader.py.
   - Pinned v19.2 registry loading and caching
   - Known valid techniques and sub-techniques in v19.2
   - Syntactically valid but non-existent technique IDs (e.g. T9999, T9999.999)
3. Mandatory post-hoc enforcement:
   - VALID requires passing both Layer 1 and Layer 2
   - INVALID_ID covers failure at either layer
   - Post-hoc only: no auto-correction, no prompt alteration, no external retrieval
"""

from __future__ import annotations

import pytest

from src.llm.schemas import (
    ParseStatus,
    load_attack_registry,
    reset_attack_registry_cache,
    validate_attack_id_syntax,
    validate_technique_id,
)


# ---------------------------------------------------------------------------
# 1. Layer 1: Syntax Validation Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "valid_id",
    [
        "T1059",
        "T1078",
        "T1566",
        "T1053",
        "T1055",
        "T1082",
        "T1003",
        "T1021",
        "T1047",
        "T1543",
    ]
)
def test_syntax_valid_root_techniques(valid_id: str):
    """Verify that canonical 4-digit root technique IDs pass Layer 1 syntax check."""
    assert validate_attack_id_syntax(valid_id) is True


@pytest.mark.parametrize(
    "valid_sub_id",
    [
        "T1059.001",
        "T1059.003",
        "T1059.005",
        "T1078.001",
        "T1078.003",
        "T1566.001",
        "T1566.002",
        "T1053.005",
        "T1055.001",
        "T1055.012",
    ]
)
def test_syntax_valid_subtechniques(valid_sub_id: str):
    """Verify that canonical 4-digit root with 3-digit sub-technique IDs pass Layer 1 syntax check."""
    assert validate_attack_id_syntax(valid_sub_id) is True


@pytest.mark.parametrize(
    "invalid_id",
    [
        "T105",        # Only 3 digits (must be 4)
        "T10590",      # 5 digits (must be 4)
        "T1059.01",    # 2-digit subtechnique (must be 3)
        "T1059.0001",  # 4-digit subtechnique (must be 3)
        "t1059",       # Lowercase 't'
        "t1059.001",   # Lowercase 't' with subtechnique
        "1059",        # Missing 'T' prefix
        "1059.001",    # Missing 'T' prefix with subtechnique
        "T1059.",      # Trailing dot with no subtechnique digits
        "T1059.abc",   # Non-digit subtechnique
        "T1059 ",      # Trailing space
        " T1059",      # Leading space
        "T1059\n",     # Trailing newline
        "T 1059",      # Embedded space
        "T1059. 001",  # Space after dot
        "",            # Empty string
        "technique_id",# Text string
        "T1059; DROP", # Injection attempt
        "T１０５９",      # Full-width Unicode digits (must be strict ASCII)
        "T\uff11\uff10\uff15\uff19",  # Explicit escaped full-width digits
        "T１０５９.００１", # Full-width subtechnique
        "T١٠٥٩",        # Eastern Arabic numerals
    ]
)
def test_syntax_invalid_strings(invalid_id: str):
    """Verify that malformed strings fail Layer 1 syntax check."""
    assert validate_attack_id_syntax(invalid_id) is False


def test_syntax_unicode_and_non_ascii_digits_rejected():
    """Verify that full-width Unicode digits and non-ASCII numerals fail Layer 1 syntax check."""
    assert validate_attack_id_syntax("T１０５９") is False
    assert validate_attack_id_syntax("T\uff11\uff10\uff15\uff19") is False
    assert validate_attack_id_syntax("T１０５９.００１") is False
    assert validate_attack_id_syntax("T١٠٥٩") is False


def test_two_layer_validation_unicode_digits_fails_at_syntax_layer():
    """Verify that full-width Unicode digits fail at Layer 1 syntax check with syntax error reason."""
    is_valid, status, reason = validate_technique_id("T１０５９")
    assert is_valid is False
    assert status == ParseStatus.INVALID_ID
    assert reason is not None
    assert "Syntax error" in reason


def test_syntax_non_string_types():
    """Non-string inputs must return False from syntax validation."""
    assert validate_attack_id_syntax(None) is False  # type: ignore
    assert validate_attack_id_syntax(1059) is False  # type: ignore
    assert validate_attack_id_syntax(["T1059"]) is False  # type: ignore


# ---------------------------------------------------------------------------
# 2. Layer 2: Registry Membership Tests with Production Enterprise ATT&CK v19.2
# ---------------------------------------------------------------------------

def test_production_attack_registry_loading():
    """Verify that Enterprise ATT&CK v19.2 registry loads correctly and caches technique IDs."""
    reset_attack_registry_cache()
    registry = load_attack_registry()
    assert isinstance(registry, set)
    assert len(registry) > 600, "Enterprise ATT&CK v19.2 registry must contain over 600 techniques"

    # Known techniques present in Enterprise ATT&CK v19.2
    assert "T1059" in registry
    assert "T1059.001" in registry
    assert "T1078" in registry
    assert "T1053.005" in registry

    # Second call should return cached set immediately
    registry2 = load_attack_registry()
    assert registry2 is registry


def test_two_layer_validation_production_valid_cases():
    """Known valid ATT&CK v19.2 techniques must pass both Layer 1 and Layer 2 -> VALID."""
    test_cases = [
        "T1059",      # Command and Scripting Interpreter
        "T1059.001",  # PowerShell
        "T1078",      # Valid Accounts
        "T1078.003",  # Local Accounts
        "T1053.005",  # Scheduled Task
        "T1055.001",  # Dynamic-link Library Injection
    ]

    for tid in test_cases:
        is_valid, status, reason = validate_technique_id(tid)
        assert is_valid is True, f"Expected {tid} to be valid"
        assert status == ParseStatus.VALID
        assert reason is None


def test_two_layer_validation_valid_format_but_nonexistent():
    """Syntactically valid IDs that do NOT exist in v19.2 must fail Layer 2 -> INVALID_ID."""
    nonexistent_cases = [
        "T9999",
        "T9999.999",
        "T8888",
        "T1059.999",  # Nonexistent subtechnique of real root
        "T9000.001",
    ]

    for tid in nonexistent_cases:
        is_valid, status, reason = validate_technique_id(tid)
        assert is_valid is False
        assert status == ParseStatus.INVALID_ID
        assert reason is not None
        assert "Registry error" in reason
        assert "does not exist in Enterprise ATT&CK v19.2" in reason


def test_two_layer_validation_syntax_failure_preempts_registry():
    """Syntactically invalid inputs fail Layer 1 immediately without requiring registry lookup."""
    is_valid, status, reason = validate_technique_id("INVALID_ID_FORMAT")
    assert is_valid is False
    assert status == ParseStatus.INVALID_ID
    assert reason is not None
    assert "Syntax error" in reason


# ---------------------------------------------------------------------------
# 3. Custom / Mock Registry Testing
# ---------------------------------------------------------------------------

def test_two_layer_validation_with_custom_registry():
    """Verify two-layer validation using an explicit mock registry set."""
    mock_registry = {"T1059", "T1059.001", "T1082"}

    # Pass both layers
    assert validate_technique_id("T1059", registry_ids=mock_registry) == (True, ParseStatus.VALID, None)
    assert validate_technique_id("T1082", registry_ids=mock_registry) == (True, ParseStatus.VALID, None)

    # Fail layer 1 (syntax)
    is_valid_1, status_1, reason_1 = validate_technique_id("t1059", registry_ids=mock_registry)
    assert is_valid_1 is False
    assert status_1 == ParseStatus.INVALID_ID
    assert "Syntax error" in reason_1

    # Fail layer 2 (registry)
    is_valid_2, status_2, reason_2 = validate_technique_id("T1078", registry_ids=mock_registry)
    assert is_valid_2 is False
    assert status_2 == ParseStatus.INVALID_ID
    assert "Registry error" in reason_2


# ---------------------------------------------------------------------------
# 4. Post-Hoc Enforcement Properties
# ---------------------------------------------------------------------------

def test_post_hoc_validation_is_side_effect_free():
    """
    Post-hoc validation must not mutate input, must be deterministic and idempotent,
    and must never attempt to correct or remap invalid identifiers.
    """
    input_str = "t1059.001"
    # Call multiple times
    res1 = validate_technique_id(input_str)
    res2 = validate_technique_id(input_str)

    assert res1 == res2
    assert res1[0] is False
    assert res1[1] == ParseStatus.INVALID_ID
    # Input remains unchanged
    assert input_str == "t1059.001"
