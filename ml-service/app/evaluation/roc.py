"""ROC helpers built on top of :mod:`app.evaluation.metrics`."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from .metrics import auc_score, roc_curve


def roc_points(scores: Sequence[float], labels: Sequence[int]) -> list[dict[str, float]]:
    """Return the ROC curve as a list of ``{fpr, tpr, threshold}`` points."""
    curve = roc_curve(scores, labels)
    return [
        {
            "fpr": round(float(fpr), 6),
            "tpr": round(float(tpr), 6),
            "threshold": float(threshold),
        }
        for fpr, tpr, threshold in zip(
            curve["fpr"], curve["tpr"], curve["thresholds"], strict=False
        )
    ]


def summary(scores: Sequence[float], labels: Sequence[int]) -> dict[str, Any]:
    """Compact ROC summary including the AUC."""
    curve = roc_curve(scores, labels)
    return {
        "auc": round(auc_score(scores, labels), 6),
        "points": roc_points(scores, labels),
        "num_genuine": curve["num_genuine"],
        "num_impostor": curve["num_impostor"],
    }


def downsample(points: Sequence[dict[str, float]], max_points: int = 200) -> list[dict[str, float]]:
    """Reduce the number of ROC points so that charts stay responsive."""
    if len(points) <= max_points:
        return list(points)
    step = len(points) / float(max_points)
    indices = {int(index * step) for index in range(max_points)}
    indices.add(len(points) - 1)
    return [points[index] for index in sorted(indices)]


def interpolate(points: Sequence[dict[str, float]], count: int = 100) -> list[dict[str, float]]:
    """Interpolate an ROC curve onto a regular grid (for plotting)."""
    if not points:
        return []
    fpr = np.asarray([point["fpr"] for point in points], dtype=np.float64)
    tpr = np.asarray([point["tpr"] for point in points], dtype=np.float64)
    grid = np.linspace(0.0, 1.0, count)
    interpolated = np.interp(grid, fpr, tpr)
    return [
        {"fpr": round(float(x), 6), "tpr": round(float(y), 6)}
        for x, y in zip(grid, interpolated, strict=False)
    ]


__all__ = ["downsample", "interpolate", "roc_points", "summary"]
