"""Confusion matrix helpers.

Only meaningful for *classification* tasks.  In the biometric literature the
usual operating-point view (ROC / DET / FAR / FRR) is preferred; a confusion
matrix is provided for cases where a decision threshold turns a continuous
score into a binary decision.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .metrics import _validate


def confusion_matrix(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    threshold: float,
) -> dict[str, Any]:
    """Binary confusion matrix for a decision rule ``score >= threshold``.

    ``label == 1`` denotes a genuine comparison.  A correct decision is a
    genuine comparison that is accepted, or an impostor comparison that is
    rejected.
    """
    score_array, label_array, warnings = _validate(scores, labels)

    decisions = score_array >= float(threshold)
    genuine = label_array == 1
    impostor = label_array == 0

    true_positive = int(np.sum(decisions & genuine))
    false_negative = int(np.sum((~decisions) & genuine))
    false_positive = int(np.sum(decisions & impostor))
    true_negative = int(np.sum((~decisions) & impostor))

    total = max(true_positive + false_negative + false_positive + true_negative, 1)
    accuracy = (true_positive + true_negative) / total

    return {
        "threshold": float(threshold),
        "matrix": {
            "true_positive": true_positive,
            "false_negative": false_negative,
            "false_positive": false_positive,
            "true_negative": true_negative,
        },
        "accuracy": round(float(accuracy), 6),
        "notes": [
            "Rows are the true class (genuine / impostor), columns the decision "
            "(accepted / rejected).",
            "A confusion matrix depends on a single threshold; prefer ROC/DET "
            "curves for threshold-independent reporting.",
        ],
        "warnings": warnings,
    }


def threshold_grid(
    scores: Sequence[float], labels: Sequence[int], *, count: int = 11
) -> list[float]:
    """Return a sorted grid of candidate thresholds between 0 and 1."""
    score_array, label_array, _ = _validate(scores, labels)
    low = float(np.min(score_array)) if score_array.size else 0.0
    high = float(np.max(score_array)) if score_array.size else 1.0
    if high <= low:
        high = low + 1.0
    return [round(float(value), 6) for value in np.linspace(low, high, count)]


__all__ = ["confusion_matrix", "threshold_grid"]
