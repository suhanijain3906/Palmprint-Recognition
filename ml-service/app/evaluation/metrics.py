"""Biometric evaluation metrics.

All functions operate on a list of *scores* together with a list of *labels*
where ``1`` marks a genuine comparison (same subject) and ``0`` marks an
impostor comparison (different subjects).

Methodological requirements
---------------------------
* The scores must come from a labelled evaluation set.
* Genuine and impostor comparisons must be separated correctly; a score
  vector that mixes the two cannot be evaluated.
* Train / validation / test splits must be separated **by subject**, otherwise
  the reported numbers leak identity information and do not describe
  generalisation.
* Never evaluate on the data used for training and report it as a
  generalisation result.

These functions compute the numbers; they cannot verify that the caller has
met the requirements above, so every response also carries the warnings.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class EvaluationResult:
    """Outcome of a genuine/impostor evaluation."""

    scores: list[float]
    labels: list[int]
    roc: dict[str, Any]
    auc: float
    far: dict[str, Any]
    frr: dict[str, Any]
    eer: dict[str, Any]
    counts: dict[str, int]
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scores": self.scores,
            "labels": self.labels,
            "roc": self.roc,
            "auc": self.auc,
            "far": self.far,
            "frr": self.frr,
            "eer": self.eer,
            "counts": self.counts,
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
        }


def _validate(
    scores: Sequence[float], labels: Sequence[int]
) -> tuple[np.ndarray, np.ndarray, list[str]]:
    warnings: list[str] = []
    if len(scores) != len(labels):
        raise ValueError("scores and labels must have the same length.")
    if len(scores) == 0:
        raise ValueError("At least one comparison score is required.")

    score_array = np.asarray(scores, dtype=np.float64)
    label_array = np.asarray(labels, dtype=np.int64)

    if np.any(~np.isfinite(score_array)):
        raise ValueError("All scores must be finite numbers.")
    unique = set(np.unique(label_array).tolist())
    if not unique.issubset({0, 1}):
        raise ValueError("Labels must be 0 (impostor) or 1 (genuine).")
    if len(unique) < 2:
        warnings.append(
            "Only one class is present in the evaluation data; ROC/AUC/FAR/FRR "
            "cannot be computed meaningfully."
        )
    return score_array, label_array, warnings


def roc_curve(scores: Sequence[float], labels: Sequence[int]) -> dict[str, Any]:
    """Return the ROC curve (FPR/TPR) over all thresholds."""
    score_array, label_array, warnings = _validate(scores, labels)

    order = np.argsort(-score_array, kind="mergesort")
    sorted_scores = score_array[order]
    sorted_labels = label_array[order]

    positives = int(np.sum(sorted_labels == 1))
    negatives = int(np.sum(sorted_labels == 0))

    thresholds: list[float] = []
    tpr: list[float] = []
    fpr: list[float] = []

    # Start at the highest threshold: nothing is accepted yet.
    thresholds.append(float("inf"))
    tpr.append(0.0)
    fpr.append(0.0)

    true_positives = 0
    false_positives = 0
    index = 0
    total = len(sorted_scores)
    while index < total:
        current = sorted_scores[index]
        while index < total and sorted_scores[index] == current:
            if sorted_labels[index] == 1:
                true_positives += 1
            else:
                false_positives += 1
            index += 1
        thresholds.append(float(current))
        tpr.append(true_positives / positives if positives else 0.0)
        fpr.append(false_positives / negatives if negatives else 0.0)

    return {
        "thresholds": thresholds,
        "tpr": tpr,
        "fpr": fpr,
        "num_genuine": positives,
        "num_impostor": negatives,
        "warnings": warnings,
    }


def auc_score(scores: Sequence[float], labels: Sequence[int]) -> float:
    """Area under the ROC curve computed with the trapezoidal rule."""
    curve = roc_curve(scores, labels)
    fpr = np.asarray(curve["fpr"], dtype=np.float64)
    tpr = np.asarray(curve["tpr"], dtype=np.float64)
    if len(fpr) < 2:
        return 0.0
    return float(np.trapezoid(tpr, fpr)) if hasattr(np, "trapezoid") else float(np.trapz(tpr, fpr))


def false_rates(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    thresholds: Sequence[float] | None = None,
) -> dict[str, Any]:
    """Return FAR and FRR over the requested thresholds (or all of them)."""
    score_array, label_array, warnings = _validate(scores, labels)

    if thresholds is None:
        unique = np.unique(score_array)
        thresholds = sorted(set(unique.tolist()) | {0.0, 1.0})

    positives = int(np.sum(label_array == 1))
    negatives = int(np.sum(label_array == 0))

    points: list[dict[str, float]] = []
    for threshold in thresholds:
        accepted = score_array >= float(threshold)
        false_accepts = int(np.sum(accepted & (label_array == 0)))
        false_rejects = int(np.sum((~accepted) & (label_array == 1)))
        far = false_accepts / negatives if negatives else 0.0
        frr = false_rejects / positives if positives else 0.0
        points.append(
            {
                "threshold": float(threshold),
                "far": round(float(far), 6),
                "frr": round(float(frr), 6),
            }
        )

    return {
        "points": points,
        "warnings": warnings,
        "num_genuine": positives,
        "num_impostor": negatives,
    }


def equal_error_rate(
    scores: Sequence[float],
    labels: Sequence[int],
) -> dict[str, Any]:
    """Compute the Equal Error Rate from the ROC curve.

    The EER is the operating point where FAR and FRR are equal.  It is only
    meaningful when both genuine and impostor comparisons are present.
    """
    curve = roc_curve(scores, labels)
    thresholds = curve["thresholds"]
    tpr = np.asarray(curve["tpr"], dtype=np.float64)
    fpr = np.asarray(curve["fpr"], dtype=np.float64)

    if len(tpr) < 2:
        return {
            "eer": None,
            "threshold": None,
            "message": "Not enough data points to compute an EER.",
            "warnings": curve["warnings"],
        }

    far = 1.0 - tpr
    difference = np.abs(far - fpr)
    index = int(np.argmin(difference))
    eer = float((far[index] + fpr[index]) / 2.0)

    warnings = list(curve["warnings"])
    warnings.append(
        "The EER is estimated on the supplied scores only. Its reliability "
        "depends on the size and quality of the evaluation set."
    )

    return {
        "eer": round(eer, 6),
        "threshold": thresholds[index],
        "far_at_eer": round(float(fpr[index]), 6),
        "frr_at_eer": round(float(far[index]), 6),
        "message": "Equal error rate estimated from the supplied comparison scores.",
        "warnings": warnings,
    }


def evaluate_scores(
    scores: Sequence[float],
    labels: Sequence[int],
    *,
    thresholds: Sequence[float] | None = None,
) -> EvaluationResult:
    """Run the complete evaluation and return every metric."""
    score_array, label_array, warnings = _validate(scores, labels)
    curve = roc_curve(score_array, label_array)
    rates = false_rates(score_array, label_array, thresholds=thresholds)
    eer = equal_error_rate(score_array, label_array)

    counts = {
        "num_comparisons": int(len(score_array)),
        "num_genuine": int(np.sum(label_array == 1)),
        "num_impostor": int(np.sum(label_array == 0)),
    }

    if counts["num_genuine"] == 0 or counts["num_impostor"] == 0:
        warnings.append(
            "Both genuine and impostor comparisons are required. Missing one of "
            "the two classes invalidates the reported metrics."
        )

    warnings.append(
        "The metrics describe the supplied scores only. They do not prove "
        "generalisation unless the evaluation set was held out from training "
        "and split by subject."
    )

    limitations = [
        "No trained model is evaluated by default; the scores originate from "
        "the classical comparison pipeline.",
        "Subject-level separation of train/test splits cannot be verified by this service.",
        "The number of comparisons and the number of distinct subjects "
        "determine the confidence intervals; neither is derivable from the "
        "score list alone.",
    ]

    return EvaluationResult(
        scores=[float(value) for value in score_array],
        labels=[int(value) for value in label_array],
        roc=curve,
        auc=round(auc_score(score_array, label_array), 6),
        far=rates,
        frr=rates,
        eer=eer,
        counts=counts,
        warnings=warnings,
        limitations=limitations,
    )


__all__ = [
    "EvaluationResult",
    "auc_score",
    "equal_error_rate",
    "evaluate_scores",
    "false_rates",
    "roc_curve",
]
