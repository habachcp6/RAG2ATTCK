"""
RAG2ATTCK - Adversarial Stress & Correctness Verification Suite (Challenger M4)

Empirically challenges:
1. ATT&CK ID validation (Layer 1 syntax fuzzing, Layer 2 v19.2 registry boundaries, post-hoc purity)
2. LiveBudget enforcement (capacity capping, retry consumption, concurrency / race conditions)
3. Wall-clock latency measurement (backoff sleep inclusion, timer semantics under errors)
4. Schema validation and parse status routing (extra fields, wrong types, broken JSON vs invalid IDs)
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")


import pytest
import openai

from src.llm.schemas import (
    ExecutionRecord,
    ParseStatus,
    TechniquePrediction,
    load_attack_registry,
    reset_attack_registry_cache,
    validate_attack_id_syntax,
    validate_technique_id,
    get_workspace_root,
)
from src.llm.client import (
    LiveBudget,
    LiveBudgetExceededError,
    LLMClient,
    reset_live_budget,
)
from src.llm.logging import WallClockTimer
from src.attack_loader import parse_attack_bundle


def test_section_1_regex_adversarial_fuzzing() -> Dict[str, Any]:
    """Adversarial stress-testing of Layer 1 regex syntax."""
    results = {"total": 0, "passed": 0, "failed": 0, "failures": []}

    # Format should be: ^T\d{4}(?:\.\d{3})?$
    # Cases that MUST FAIL (invalid syntax -> validate_attack_id_syntax returns False)
    adversarial_invalid_cases = [
        # Digit count variations
        ("T1", "1 digit"),
        ("T12", "2 digits"),
        ("T123", "3 digits"),
        ("T12345", "5 digits"),
        ("T123456", "6 digits"),
        ("T1059.0", "1 digit subtechnique"),
        ("T1059.01", "2 digit subtechnique"),
        ("T1059.0001", "4 digit subtechnique"),
        ("T1059.00001", "5 digit subtechnique"),
        ("T1059.001.002", "nested sub-sub-technique"),
        ("T1059..001", "double dot"),
        ("T1059.", "trailing dot"),
        (".T1059", "leading dot"),
        
        # Casing variations
        ("t1059", "lowercase t"),
        ("t1059.001", "lowercase t with subtechnique"),
        ("T1059.abc", "alpha subtechnique"),
        ("Tabcd", "alpha technique"),
        ("T105A", "hex technique"),
        ("t105a.001", "lowercase hex"),

        # Prefix variations
        ("1059", "missing T prefix"),
        ("1059.001", "missing T prefix with subtechnique"),
        ("TT1059", "double T prefix"),
        ("AT1059", "alternate prefix"),
        ("TA0001", "Tactic ID not technique ID"),
        ("S0001", "Software ID not technique ID"),
        ("G0001", "Group ID not technique ID"),
        ("M1001", "Mitigation ID not technique ID"),
        ("DS0001", "Data Source ID not technique ID"),

        # Whitespace and control character variations
        (" T1059", "leading space"),
        ("T1059 ", "trailing space"),
        (" T1059 ", "enclosing space"),
        ("T 1059", "embedded space in technique"),
        ("T1059 .001", "space before dot"),
        ("T1059. 001", "space after dot"),
        ("T1059.001 ", "trailing space subtechnique"),
        ("T1059\n", "trailing newline"),
        ("\nT1059", "leading newline"),
        ("T1059\r\n", "CRLF"),
        ("\tT1059", "tab prefix"),
        ("T1059\t", "tab suffix"),
        ("T1059\x00", "null byte suffix"),
        ("\x00T1059", "null byte prefix"),

        # Injection and metacharacter attempts
        ("T1059; DROP TABLE techniques;", "SQL injection"),
        ("T1059' OR '1'='1", "SQL quote injection"),
        ("T1059.001\nTechnique: T1078", "prompt / header injection"),
        ("<script>alert('T1059')</script>", "XSS attempt"),
        ("T1059$(whoami)", "command substitution"),
        ("T1059`id`", "backtick substitution"),
        ("T.*", "regex wildcard"),
        ("T1059.*", "regex subtechnique wildcard"),
        ("^T1059$", "regex anchor strings"),
        ("T\\d{4}", "regex literal pattern"),

        # Unicode and homoglyph attacks
        ("\u04221059", "Cyrillic capital letter Т (U+0422) lookalike"),
        ("T\uFF11\uFF10\uFF15\uFF19", "Full-width digits １０５９"),
        ("T1059\u200B", "Zero-width space U+200B"),
        ("T1059\uFEFF", "Byte order mark U+FEFF"),
        ("T\u0661\u0660\u0665\u0669", "Eastern Arabic numerals"),

        # Symbols, signs, punctuation
        ("-T1059", "leading minus"),
        ("+T1059", "leading plus"),
        ("T-1059", "hyphenated technique"),
        ("T1059-001", "hyphenated subtechnique"),
        ("T1059/001", "slashed subtechnique"),
        ("T1059:001", "colon subtechnique"),
        ("T1059,001", "comma subtechnique"),

        # Empty / non-string / edge
        ("", "empty string"),
        (" ", "single space"),
        ("   ", "multiple spaces"),
        ("null", "literal string null"),
        ("None", "literal string None"),
        ("undefined", "literal string undefined"),
    ]

    for val, desc in adversarial_invalid_cases:
        results["total"] += 1
        is_valid = validate_attack_id_syntax(val)
        if is_valid is False:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append((val, desc, "Expected False, got True"))

    # Non-string types that must return False
    non_string_cases = [None, 1059, 1059.001, True, False, [], {}, {"technique_id": "T1059"}]
    for val in non_string_cases:
        results["total"] += 1
        is_valid = validate_attack_id_syntax(val)  # type: ignore
        if is_valid is False:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append((val, type(val).__name__, "Expected False, got True"))

    # Cases that MUST PASS syntax validation (canonical format ^T\d{4}(?:\.\d{3})?$)
    valid_syntax_cases = [
        "T1059",
        "T1059.001",
        "T1078.003",
        "T0000",        # Valid syntax even if non-existent in registry
        "T9999",        # Valid syntax even if non-existent in registry
        "T9999.999",    # Valid syntax even if non-existent in registry
        "T0001.001",    # Valid syntax
    ]
    for val in valid_syntax_cases:
        results["total"] += 1
        is_valid = validate_attack_id_syntax(val)
        if is_valid is True:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["failures"].append((val, "canonical valid syntax", "Expected True, got False"))

    return results


def test_section_2_registry_boundary_cases() -> Dict[str, Any]:
    """Adversarial stress-testing of Layer 2 registry membership."""
    ws = get_workspace_root()
    stix_path = ws / "attack" / "raw" / "enterprise-v19.2" / "enterprise-attack-19.2.json"
    bundle = parse_attack_bundle(stix_path)
    registry = load_attack_registry(stix_path)

    active_techs = [t for t in bundle.values() if not t.revoked and not t.deprecated]
    revoked_techs = [t for t in bundle.values() if t.revoked]
    deprecated_techs = [t for t in bundle.values() if t.deprecated]

    # Sample cases
    active_samples = [t.technique_id for t in active_techs[:10]]
    revoked_samples = [t.technique_id for t in revoked_techs[:10]]
    deprecated_samples = [t.technique_id for t in deprecated_techs[:10]]
    nonexistent_samples = ["T9999", "T9999.999", "T0000", "T8888.888", "T1059.999"]

    # Verify active techniques pass both layers
    active_passed = 0
    for tid in active_samples:
        is_val, status, reason = validate_technique_id(tid, registry_ids=registry)
        if is_val and status == ParseStatus.VALID and reason is None:
            active_passed += 1

    # Verify nonexistent techniques fail Layer 2 with INVALID_ID
    nonexistent_passed = 0
    for tid in nonexistent_samples:
        is_val, status, reason = validate_technique_id(tid, registry_ids=registry)
        if (not is_val) and status == ParseStatus.INVALID_ID and "Registry error" in (reason or ""):
            nonexistent_passed += 1

    # Check revoked techniques behavior in registry
    revoked_in_registry = [tid for tid in revoked_samples if tid in registry]
    # Check deprecated techniques behavior in registry
    deprecated_in_registry = [tid for tid in deprecated_samples if tid in registry]

    return {
        "total_bundle_techniques": len(bundle),
        "total_registry_ids": len(registry),
        "active_count": len(active_techs),
        "revoked_count": len(revoked_techs),
        "deprecated_count": len(deprecated_techs),
        "active_tested": len(active_samples),
        "active_passed": active_passed,
        "nonexistent_tested": len(nonexistent_samples),
        "nonexistent_passed": nonexistent_passed,
        "revoked_tested": len(revoked_samples),
        "revoked_in_registry_count": len(revoked_in_registry),
        "deprecated_tested": len(deprecated_samples),
        "deprecated_in_registry_count": len(deprecated_in_registry),
    }


def test_section_3_live_budget_stress() -> Dict[str, Any]:
    """Stress-testing LiveBudget capacity capping, retries, and concurrency."""
    report: Dict[str, Any] = {}

    # 1. Exact limit & exhaustion
    b1 = LiveBudget(max_requests=5)
    consumed_seq = [b1.consume() for _ in range(5)]
    assert consumed_seq == [1, 2, 3, 4, 5]
    assert b1.count == 5
    assert b1.remaining == 0
    assert b1.is_exhausted()

    # 6th must raise
    raised_on_6th = False
    try:
        b1.consume()
    except LiveBudgetExceededError:
        raised_on_6th = True
    report["raised_on_6th"] = raised_on_6th

    # 2. Reset logic
    b1.reset()
    assert b1.count == 0
    assert b1.remaining == 5
    assert not b1.is_exhausted()
    report["reset_works"] = True

    # 3. Retries consumption in client
    mock_openai = MagicMock()
    mock_sleep = MagicMock()
    # 2 rate limit errors then success
    mock_openai.responses.create.side_effect = [
        openai.RateLimitError("429", response=MagicMock(), body=None),
        openai.RateLimitError("429", response=MagicMock(), body=None),
        SimpleNamespace(
            status="completed",
            output_text=json.dumps({"technique_id": "T1059.001"}),
            refusal=None,
            incomplete_details=None,
            usage=SimpleNamespace(input_tokens=10, output_tokens=10),
        ),
    ]

    budget_for_retries = LiveBudget(max_requests=5)
    client_live = LLMClient(
        openai_client=mock_openai,
        live_budget=budget_for_retries,
        is_live=True,
        sleep_fn=mock_sleep,
    )
    rec = client_live.predict(sample_id="test_retries", endpoint_evidence="ev")
    report["retries_consumed"] = budget_for_retries.count  # Expected 3
    report["retries_status"] = rec.parse_status
    report["retries_retry_count"] = rec.retry_count  # Expected 2

    # 4. Mid-retry exhaustion: budget = 2, but needs 3 calls
    mock_openai_exhaust = MagicMock()
    mock_openai_exhaust.responses.create.side_effect = [
        openai.RateLimitError("429", response=MagicMock(), body=None),
        openai.RateLimitError("429", response=MagicMock(), body=None),
        openai.RateLimitError("429", response=MagicMock(), body=None),
    ]
    budget_tight = LiveBudget(max_requests=2)
    client_tight = LLMClient(
        openai_client=mock_openai_exhaust,
        live_budget=budget_tight,
        is_live=True,
        sleep_fn=mock_sleep,
    )
    rec_tight = client_tight.predict(sample_id="test_tight", endpoint_evidence="ev")
    report["tight_consumed"] = budget_tight.count  # Expected 2
    report["tight_status"] = rec_tight.parse_status  # Expected API_FAILURE
    report["tight_reason"] = rec_tight.invalid_reason

    # 5. Thread concurrency stress-test: 50 threads competing for 5 slots
    concurrent_budget = LiveBudget(max_requests=5)
    success_count = 0
    failure_count = 0

    def worker_task():
        nonlocal success_count, failure_count
        try:
            concurrent_budget.consume()
            return True
        except LiveBudgetExceededError:
            return False

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(worker_task) for _ in range(50)]
        results = [f.result() for f in futures]

    successes = sum(1 for r in results if r is True)
    failures = sum(1 for r in results if r is False)
    report["concurrent_threads"] = 50
    report["concurrent_successes"] = successes  # Must be exactly 5
    report["concurrent_failures"] = failures    # Must be exactly 45
    report["concurrent_final_count"] = concurrent_budget.count  # Must be 5

    return report


def test_section_4_wall_clock_latency() -> Dict[str, Any]:
    """Adversarial verification of wall-clock latency measurement."""
    report: Dict[str, Any] = {}

    # 1. Timer includes simulated backoff sleep
    mock_openai = MagicMock()
    
    # We provide a sleep_fn that actually sleeps a small measurable amount (e.g. 30ms)
    def real_short_sleep(secs: float):
        time.sleep(0.03)

    mock_openai.responses.create.side_effect = [
        openai.RateLimitError("429", response=MagicMock(), body=None),
        SimpleNamespace(
            status="completed",
            output_text=json.dumps({"technique_id": "T1059.001"}),
            refusal=None,
            incomplete_details=None,
            usage=SimpleNamespace(input_tokens=10, output_tokens=10),
        ),
    ]

    client = LLMClient(
        openai_client=mock_openai,
        sleep_fn=real_short_sleep,
    )
    rec = client.predict(sample_id="test_latency", endpoint_evidence="ev")
    report["latency_with_sleep_ms"] = rec.latency_ms
    # Latency should be at least 25ms because of real_short_sleep(0.03)
    report["latency_includes_sleep"] = rec.latency_ms >= 25.0
    report["retry_count"] = rec.retry_count

    # 2. Timer handles exception inside context cleanly
    timer = WallClockTimer()
    exception_caught = False
    try:
        with timer:
            time.sleep(0.02)
            raise ValueError("Intentional error inside timer")
    except ValueError:
        exception_caught = True

    report["timer_exception_handled"] = exception_caught
    report["timer_elapsed_ms_after_exception"] = timer.elapsed_ms
    report["timer_computed_on_exception"] = timer.elapsed_ms >= 15.0

    return report


def test_section_5_schema_and_taxonomy_routing() -> Dict[str, Any]:
    """Adversarial stress-testing of output schema and taxonomy routing."""
    report = {"total": 0, "passed": 0, "failed": 0, "details": []}

    mock_openai = MagicMock()
    client = LLMClient(openai_client=mock_openai)

    # Test matrix: (raw_output_text, expected_status, description)
    test_matrix = [
        # MALFORMED_RESPONSE cases: broken JSON, wrong root type, missing fields, extra fields
        ("", ParseStatus.MALFORMED_RESPONSE, "empty string"),
        ("   ", ParseStatus.MALFORMED_RESPONSE, "whitespace string"),
        ("not json", ParseStatus.MALFORMED_RESPONSE, "plain text"),
        ("{broken json", ParseStatus.MALFORMED_RESPONSE, "unclosed JSON object"),
        ("{\"technique_id\": \"T1059.001\"", ParseStatus.MALFORMED_RESPONSE, "truncated JSON"),
        ("[1, 2, 3]", ParseStatus.MALFORMED_RESPONSE, "JSON list instead of dict"),
        ("\"just a string\"", ParseStatus.MALFORMED_RESPONSE, "JSON string literal"),
        ("12345", ParseStatus.MALFORMED_RESPONSE, "JSON integer literal"),
        ("true", ParseStatus.MALFORMED_RESPONSE, "JSON boolean literal"),
        ("null", ParseStatus.MALFORMED_RESPONSE, "JSON null literal"),
        ("{}", ParseStatus.MALFORMED_RESPONSE, "empty dict missing technique_id"),
        ("{\"other_key\": \"T1059.001\"}", ParseStatus.MALFORMED_RESPONSE, "missing technique_id"),
        ("{\"technique_id\": 1059}", ParseStatus.MALFORMED_RESPONSE, "technique_id integer type"),
        ("{\"technique_id\": null}", ParseStatus.MALFORMED_RESPONSE, "technique_id null type"),
        ("{\"technique_id\": [\"T1059\"]}", ParseStatus.MALFORMED_RESPONSE, "technique_id list type"),
        ("{\"technique_id\": {\"id\": \"T1059\"}}", ParseStatus.MALFORMED_RESPONSE, "technique_id dict type"),
        ("{\"technique_id\": \"T1059.001\", \"extra\": \"forbidden\"}", ParseStatus.MALFORMED_RESPONSE, "extra forbidden field"),
        ("{\"technique_id\": \"T1059.001\", \"confidence\": 0.99}", ParseStatus.MALFORMED_RESPONSE, "extra confidence field"),

        # INVALID_ID cases: parsed JSON + technique_id present, but fails syntax or registry
        ("{\"technique_id\": \"\"}", ParseStatus.INVALID_ID, "empty technique_id string"),
        ("{\"technique_id\": \"   \"}", ParseStatus.INVALID_ID, "whitespace technique_id string"),
        ("{\"technique_id\": \"T105\"}", ParseStatus.INVALID_ID, "syntax fail: 3 digits"),
        ("{\"technique_id\": \"T10590\"}", ParseStatus.INVALID_ID, "syntax fail: 5 digits"),
        ("{\"technique_id\": \"t1059.001\"}", ParseStatus.INVALID_ID, "syntax fail: lowercase"),
        ("{\"technique_id\": \"T1059.01\"}", ParseStatus.INVALID_ID, "syntax fail: 2 digit subtechnique"),
        ("{\"technique_id\": \"T1059.0001\"}", ParseStatus.INVALID_ID, "syntax fail: 4 digit subtechnique"),
        ("{\"technique_id\": \"T1059; DROP\"}", ParseStatus.INVALID_ID, "syntax fail: injection"),
        ("{\"technique_id\": \"T9999\"}", ParseStatus.INVALID_ID, "registry fail: nonexistent root"),
        ("{\"technique_id\": \"T9999.999\"}", ParseStatus.INVALID_ID, "registry fail: nonexistent subtechnique"),
        ("{\"technique_id\": \"T1059.999\"}", ParseStatus.INVALID_ID, "registry fail: nonexistent subtechnique of real root"),

        # VALID cases: canonical active techniques in v19.2
        ("{\"technique_id\": \"T1059\"}", ParseStatus.VALID, "valid active root technique"),
        ("{\"technique_id\": \"T1059.001\"}", ParseStatus.VALID, "valid active subtechnique"),
        ("{\"technique_id\": \"T1078\"}", ParseStatus.VALID, "valid active root technique"),
        ("{\"technique_id\": \"T1053.005\"}", ParseStatus.VALID, "valid active subtechnique"),
    ]

    for raw_json, expected_st, desc in test_matrix:
        report["total"] += 1
        mock_openai.responses.create.return_value = SimpleNamespace(
            status="completed",
            output_text=raw_json,
            refusal=None,
            incomplete_details=None,
            usage=SimpleNamespace(input_tokens=10, output_tokens=10),
        )
        rec = client.predict(sample_id="test_schema", endpoint_evidence="ev")
        if rec.parse_status == expected_st.value or rec.parse_status == expected_st:
            report["passed"] += 1
        else:
            report["failed"] += 1
            report["details"].append({
                "description": desc,
                "input": raw_json,
                "expected": str(expected_st),
                "actual": str(rec.parse_status),
                "invalid_reason": rec.invalid_reason,
            })

    return report


def main():
    print("=" * 70)
    print("RAG2ATTCK CHALLENGER M4: ADVERSARIAL STRESS HARNESS")
    print("=" * 70)

    # 1. Regex fuzzing
    print("\n[+] 1. Adversarial Regex Syntax Fuzzing...")
    res1 = test_section_1_regex_adversarial_fuzzing()
    print(f"    Total test cases: {res1['total']}")
    print(f"    Passed: {res1['passed']}")
    print(f"    Failed: {res1['failed']}")
    if res1["failures"]:
        for f in res1["failures"]:
            print(f"    FAILURE: {ascii(f[0])} | {f[1]} | {f[2]}")


    # 2. Registry boundary
    print("\n[+] 2. ATT&CK Registry Membership Boundaries...")
    res2 = test_section_2_registry_boundary_cases()
    for k, v in res2.items():
        print(f"    {k}: {v}")

    # 3. Live Budget stress
    print("\n[+] 3. LiveBudget Capacity, Retries, and Concurrency...")
    res3 = test_section_3_live_budget_stress()
    for k, v in res3.items():
        print(f"    {k}: {v}")

    # 4. Latency semantics
    print("\n[+] 4. Wall-Clock Latency Measurement Semantics...")
    res4 = test_section_4_wall_clock_latency()
    for k, v in res4.items():
        print(f"    {k}: {v}")

    # 5. Schema validation and parse status routing
    print("\n[+] 5. Schema Validation & Parse Status Taxonomy Routing...")
    res5 = test_section_5_schema_and_taxonomy_routing()
    print(f"    Total test cases: {res5['total']}")
    print(f"    Passed: {res5['passed']}")
    print(f"    Failed: {res5['failed']}")
    if res5["details"]:
        print(f"    FAILURES: {res5['details']}")

    print("\n" + "=" * 70)
    all_ok = (
        res1["failed"] == 0
        and res2["active_passed"] == res2["active_tested"]
        and res2["nonexistent_passed"] == res2["nonexistent_tested"]
        and res3["raised_on_6th"] is True
        and res3["retries_consumed"] == 3
        and res3["concurrent_successes"] == 5
        and res3["concurrent_failures"] == 45
        and res4["latency_includes_sleep"] is True
        and res4["timer_computed_on_exception"] is True
        and res5["failed"] == 0
    )
    print(f"OVERALL ADVERSARIAL STRESS HARNESS RESULT: {'ALL PASS' if all_ok else 'FAIL'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
