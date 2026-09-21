"""Known-answer arithmetic exercised only with explicit fixture policy.

These helpers do not define the study's canonical scoring. The canonical
entrypoints in experiment_metrics remain unconditionally closed.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from src.llm.schemas import validate_attack_id_syntax


@dataclass(frozen=True)
class FixtureOnlyPolicy:
    class_ids: tuple[str, ...]
    zero_division: float | None
    accuracy_denominator: str
    purpose: str

    def __post_init__(self):
        if self.purpose != "known_answer_fixture_only":
            raise ValueError("test-only policy required; this is not canonical evaluation")
        if self.accuracy_denominator != "all_fixture_rows":
            raise ValueError("fixture denominator must be explicitly all_fixture_rows")
        if self.zero_division not in (None, 0.0) or isinstance(self.zero_division, bool):
            raise ValueError("fixture zero denominator must explicitly be null or 0.0")
        if (not self.class_ids or len(set(self.class_ids)) != len(self.class_ids)
                or not all(validate_attack_id_syntax(tid) for tid in self.class_ids)):
            raise ValueError("fixture classes must be explicit unique ATT&CK IDs")


def single_label_fixture_metrics(
    truth: Sequence[str], predictions: Sequence[str | None], *, policy: FixtureOnlyPolicy,
) -> dict:
    """Per-class TP/FP/FN arithmetic with no implicit production policy.

    A None fixture prediction represents an unsuccessful prediction, never an
    abstention label. Multi-label and empty GT are deliberately unsupported.
    """
    if not isinstance(policy, FixtureOnlyPolicy):
        raise TypeError("explicit FixtureOnlyPolicy required")
    if len(truth) != len(predictions):
        raise ValueError("truth/prediction length mismatch")
    if any(not isinstance(tid, str) or tid not in policy.class_ids for tid in truth):
        raise ValueError("fixture requires one GT ID per row in the explicit class universe")
    if any(tid is not None and not isinstance(tid, str) for tid in predictions):
        raise ValueError("fixture prediction must be a single ID or None")

    def divide(numerator, denominator):
        return numerator / denominator if denominator else policy.zero_division

    per_class = {}
    for tid in sorted(policy.class_ids):
        tp = sum(t == tid and p == tid for t, p in zip(truth, predictions, strict=True))
        fp = sum(t != tid and p == tid for t, p in zip(truth, predictions, strict=True))
        fn = sum(t == tid and p != tid for t, p in zip(truth, predictions, strict=True))
        per_class[tid] = {"tp": tp, "fp": fp, "fn": fn,
                          "precision": divide(tp, tp + fp), "recall": divide(tp, tp + fn),
                          "f1": divide(2 * tp, 2 * tp + fp + fn)}
    result = {"purpose": policy.purpose, "sample_count": len(truth), "per_class": per_class,
              "exact_accuracy": divide(sum(t == p for t, p in zip(truth, predictions, strict=True)), len(truth))}
    for metric in ("precision", "recall", "f1"):
        values = [row[metric] for row in per_class.values()]
        # Undefined fixture class metrics propagate; they are not silently
        # removed from the explicitly chosen macro universe.
        result[f"macro_{metric}"] = None if None in values else sum(values) / len(values)
    return result
