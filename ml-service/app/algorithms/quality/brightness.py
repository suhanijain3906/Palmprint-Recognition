"""Brightness statistics.

The metrics below describe *how much light* reached the sensor.  They say
nothing about whether the image is usable for recognition: a perfectly
exposed but motion blurred palm and a sharp but underexposed palm produce
similar brightness numbers.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from ...utils.image_io import to_gray


def brightness_metrics(image: np.ndarray) -> dict[str, Any]:
    """Compute brightness related statistics for a BGR/gray image."""
    gray = to_gray(image)
    pixels = gray.astype(np.float64)

    mean_intensity = float(pixels.mean())
    median_intensity = float(np.median(pixels))
    std_intensity = float(pixels.std())
    min_intensity = float(pixels.min())
    max_intensity = float(pixels.max())

    # Percentage of pixels that are effectively black / blown out.
    under = float(np.mean(pixels < 10.0) * 100.0)
    over = float(np.mean(pixels > 245.0) * 100.0)

    return {
        "mean_intensity": round(mean_intensity, 3),
        "median_intensity": round(median_intensity, 3),
        "std_intensity": round(std_intensity, 3),
        "min_intensity": round(min_intensity, 3),
        "max_intensity": round(max_intensity, 3),
        "under_exposed_percent": round(under, 3),
        "over_exposed_percent": round(over, 3),
        "interpretation": (
            "mean_intensity is the average grey level on a 0-255 scale; "
            "values near 128 indicate a balanced exposure."
        ),
    }


def mean_luma(image: np.ndarray) -> float:
    """Rec. 601 luma mean, used by the experimental combined score."""
    gray = to_gray(image)
    return float(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR).mean())


__all__ = ["brightness_metrics", "mean_luma"]
