"""Independent checks of the frozen T20 JSONL and published summary."""

import json
from hashlib import sha256

import pytest

from scripts import verify_t20_canonical_artifacts as verifier


def test_committed_t20_artifacts_recompute(capsys):
    verifier.main()
    assert json.loads(capsys.readouterr().out)["status"] == "PASS"


def test_rehashed_t1136_summary_drift_is_rejected(tmp_path, monkeypatch):
    summary = json.loads(verifier.ANALYSIS.read_bytes())
    summary["t1136_001_failure"]["absent_top10_count"] = 0
    changed = tmp_path / "summary.json"
    changed.write_text(json.dumps(summary), encoding="utf-8")
    monkeypatch.setattr(verifier, "ANALYSIS", changed)
    monkeypatch.setattr(
        verifier,
        "EXPECTED_HASHES",
        {
            **{path: digest for path, digest in verifier.EXPECTED_HASHES.items()
               if path != verifier.ROOT / "artifacts/analysis/t20_retrieval_failure_summary.json"},
            changed: sha256(changed.read_bytes()).hexdigest(),
        },
    )
    with pytest.raises(ValueError, match="analysis T1136.001 absent_top10_count"):
        verifier.main()
