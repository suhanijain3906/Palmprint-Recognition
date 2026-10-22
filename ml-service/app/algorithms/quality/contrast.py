"""Contrast statistics.

Contrast describes the spread of intensities.  A palmprint with sufficient
ridge contrast produces a high standard deviation; a flat, low contrast
capture does not.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ...utils.image_io import to_gray


def contrast_metrics(image: np.ndarray) -> dict[str, Any]:
    """Compute contrast related statistics for a BGR/gray image."""
    gray = to_gray(image)
    pixels = gray.astype(np.float64)

    std = float(pixels.std())
    rms_contrast = std / 255.0

    minimum = float(pixels.min())
    maximum = float(pixels.max())
    michelson = (maximum - minimum) / 255.0 if maximum != minimum else 0.0

    # Dynamic range expressed as the 1st..99th percentile spread, which is
    # more robust to single outlier pixels than min/max.
    p1, p99 = np.percentile(pixels, [1.0, 99.0])
    robust_range = float((p99 - p1) / 255.0)

    # Entropy of the grey level histogram (0..1 normalised).
    histogram = np.bincount(gray.reshape(-1), minlength=256).astype(np.float64)
    total = histogram.sum()
    if total > 0:
        probabilities = histogram[histogram > 0] / total
        entropy = float(-(probabilities * np.log2(probabilities)).sum())
    else:
        entropy = 0.0

    return {
        "std_deviation": round(std, 3),
        "rms_contrast": round(rms_contrast, 4),
        "michelson_contrast": round(michelson, 4),
        "robust_dynamic_range": round(robust_range, 4),
        "entropy_bits": round(entropy, 4),
        "interpretation": (
            "rms_contrast is the normalised standard deviation of grey levels; "
            "values above ~0.2 usually indicate visible ridge structure."
        ),
    }


__all__ = ["contrast_metrics"]
