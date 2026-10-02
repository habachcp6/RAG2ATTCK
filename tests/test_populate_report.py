"""Unit tests for offline scientific report population helper tool (scripts/populate_report.py).

Verifies:
1. Safety boundary: Fails closed on uncertified non-fixture directories.
2. Banner & Disclaimer: All emitted markdown carries prominent private labeling.
3. Invariant: Prevents accidental in-place overwrite of canonical scientific report scaffold.
4. Slot Extraction: Correctly extracts and formats metrics for Tables 2a, 2b, 3, 4, 5.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.populate_report import (
    DEFAULT_TEMPLATE_PATH,
    DISCLAIMER_TEXT,
    assert_fixture_safety,
    run_pipeline,
)


@pytest.fixture
def mock_fixture_dir(tmp_path: Path) -> Path:
    """Create a temporary certified diagnostic test fixture directory."""
    diag_dir = tmp_path / "fixture_diagnostics"
    diag_dir.mkdir(parents=True)

    # 1. Companion metadata
    (diag_dir / "_fixture_metadata.json").write_text(
        json.dumps(
            {
                "fixture_only": True,
                "purpose": "unit_test",
                "description": "Synthetic unit test fixture",
            }
        ),
        encoding="utf-8",
    )

    # 2. per_condition_metrics.json
    conditions = {}
    for c in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        conditions[c] = {
            "accuracy_end_to_end": 0.45,
            "accuracy_valid_outputs": 0.55,
            "macro_f1": 0.35,
            "completed_record_count": 1280,
            "parse_failure_count": 2,
            "invalid_id_count": 5,
            "invalid_id_rate": 0.0039,
            "correct_count": 323,
        }
    (diag_dir / "per_condition_metrics.json").write_text(
        json.dumps({"conditions": conditions}), encoding="utf-8"
    )

    # 3. failure_decomposition.json
    failure_by_cond = {}
    for c in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        failure_by_cond[c] = {
            "total_scorable_samples": 718,
            "retrieval_miss_count": 100 if c != "no_rag" else 0,
            "valid_but_wrong_classification_count": 50 if c != "no_rag" else 0,
            "invalid_attack_id_count": 5,
            "parse_failure_count": 2,
            "provider_failure_count": 0,
        }
    (diag_dir / "failure_decomposition.json").write_text(
        json.dumps({"by_condition": failure_by_cond}), encoding="utf-8"
    )

    # 4. retrieval_conditional_metrics.json
    retrieval_by_cond = {}
    for c in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        retrieval_by_cond[c] = {
            "retrieval_failure_correct_count": 10 if c != "no_rag" else 0,
        }
    (diag_dir / "retrieval_conditional_metrics.json").write_text(
        json.dumps({"by_condition": retrieval_by_cond}), encoding="utf-8"
    )

    # 5. rq_analysis.json
    tradeoffs = {}
    views = {}
    rq1 = {}
    for c in ["no_rag", "rag_k1", "rag_k3", "rag_k5", "rag_k10"]:
        rq1[c] = {
            "accuracy_end_to_end": 0.45,
            "accuracy_valid_outputs": 0.55,
            "macro_f1": 0.35,
        }
        tradeoffs[c] = {
            "latency_ms": {"mean": 8000.0, "median": 7500.0, "p95": 9200.0},
            "tokens": {
                "mean_prompt_tokens": 1200.0,
                "mean_completion_tokens": 600.0,
                "sum_prompt_tokens": 1536000,
                "sum_completion_tokens": 768000,
            },
            "financial_cost_usd": {
                "total_cost_usd": 1.50,
                "cost_per_logical_request_usd": 0.00117,
            },
        }
        views[c] = {
            "single_view_accuracy_e2e": 0.42,
            "contextual_view_accuracy_e2e": 0.48,
            "single_view_macro_f1": 0.30,
            "contextual_view_macro_f1": 0.38,
            "view_accuracy_delta": 0.06,
        }

    rq_analysis = {
        "fixture_only": True,
        "provenance_status": "diagnostic_fixture",
        "rq1": {"by_condition": rq1},
        "rq3": {"tradeoffs_by_condition": tradeoffs, "view_diagnostics": views},
    }
    (diag_dir / "rq_analysis.json").write_text(json.dumps(rq_analysis), encoding="utf-8")

    return diag_dir


def test_assert_fixture_safety_rejects_uncertified_dir(tmp_path: Path) -> None:
    """Safety test: Fails closed when operating on uncertified directory."""
    unsafe_dir = tmp_path / "unsafe_dir"
    unsafe_dir.mkdir()

    with pytest.raises(RuntimeError, match="FAIL_CLOSED"):
        assert_fixture_safety(unsafe_dir)


def test_assert_fixture_safety_accepts_valid_fixture(mock_fixture_dir: Path) -> None:
    """Safety test: Accepts certified fixture directory with fixture_only=True."""
    # Should not raise exception
    assert_fixture_safety(mock_fixture_dir)


def test_safety_prevents_accidental_template_overwrite(
    mock_fixture_dir: Path, tmp_path: Path
) -> None:
    """Safety test: Prohibits overwriting canonical template in-place without force flag."""
    with pytest.raises(ValueError, match="SAFETY_GUARD"):
        run_pipeline(
            fixture_dir=mock_fixture_dir,
            template_path=DEFAULT_TEMPLATE_PATH,
            output_path=DEFAULT_TEMPLATE_PATH,
            force_in_place=False,
        )


def test_run_pipeline_end_to_end(mock_fixture_dir: Path, tmp_path: Path) -> None:
    """Functional test: Populates report markdown and audit JSON from mock fixtures."""
    out_md = tmp_path / "test_report.md"
    out_json = tmp_path / "test_slots.json"

    run_pipeline(
        fixture_dir=mock_fixture_dir,
        template_path=DEFAULT_TEMPLATE_PATH,
        output_path=out_md,
        audit_json_path=out_json,
    )

    assert out_md.is_file()
    assert out_json.is_file()

    content = out_md.read_text(encoding="utf-8")

    # 1. Private label banner check
    assert "<!-- FIXTURE_ONLY: true -->" in content
    assert DISCLAIMER_TEXT in content

    # 2. Table population check: No TBD in Tables 2a, 2b, 3, 4, 5
    lines = content.splitlines()
    table_rows = [line for line in lines if line.strip().startswith("| `")]
    for row in table_rows:
        assert "[TBD_AT_EXECUTION]" not in row, f"Found unpopulated row: {row}"

    # 3. Formatted metrics checks
    assert "45.00%" in content  # acc_e2e
    assert "55.00%" in content  # acc_valid
    assert "35.00%" in content  # macro_f1
    assert "1,280" in content  # completed records
    assert "+6.00 pp" in content  # view delta
    assert "USD 1.50" in content  # total cost

    # 4. Table 6 baseline preservation
    assert "*Table 6: Cryptographic Reproducibility Manifest.*" in content
    assert "d3bf3d31ad307100ac437a7daecc470bf12de9ada49f19de3d77592d5a21974c" in content

    # 5. Audit JSON structure check
    slots = json.loads(out_json.read_text(encoding="utf-8"))
    assert slots["_metadata"]["fixture_only"] is True
    assert slots["_metadata"]["disclaimer"] == DISCLAIMER_TEXT
    assert "no_rag" in slots["table_2a"]
    assert slots["table_2a"]["no_rag"]["accuracy_end_to_end"] == "45.00%"
