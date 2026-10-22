"""Combined quality report.

The combined score is an **experimental heuristic**.  It has not been
validated against any biometric quality standard (ISO/IEC 19794-5, ISO/IEC
30107-3 or NIST-style acceptance testing).  It exists so that researchers can
rank their own captures in a consistent way and it must not be reported as a
certified quality score.

Formula
-------
Four normalised sub-scores are combined with fixed weights::

    exposure   = 1 - min(1, |mean_intensity - 128| / 128)
    contrast   = min(1, rms_contrast / 0.25)
    sharpness  = min(1, variance_of_laplacian / 500)
    resolution = min(1, megapixels / 1.0)

    score = 100 * (0.30*exposure + 0.30*contrast + 0.30*sharpness + 0.10*resolution)

The weights and the normalisation constants are engineering choices, not
empirically derived values.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from .brightness import brightness_metrics
from .contrast import contrast_metrics
from .sharpness import sharpness_metrics

WEIGHTS = {"exposure": 0.30, "contrast": 0.30, "sharpness": 0.30, "resolution": 0.10}


def quality_report(image: np.ndarray) -> dict[str, Any]:
    """Return the full quality assessment for an image."""
    height, width = image.shape[:2]
    brightness = brightness_metrics(image)
    contrast = contrast_metrics(image)
    sharpness = sharpness_metrics(image)

    megapixels = (width * height) / 1_000_000.0

    exposure = 1.0 - min(1.0, abs(brightness["mean_intensity"] - 128.0) / 128.0)
    contrast_score = min(1.0, contrast["rms_contrast"] / 0.25)
    sharpness_score = min(1.0, sharpness["variance_of_laplacian"] / 500.0)
    resolution_score = min(1.0, megapixels / 1.0)

    combined = 100.0 * (
        WEIGHTS["exposure"] * exposure
        + WEIGHTS["contrast"] * contrast_score
        + WEIGHTS["sharpness"] * sharpness_score
        + WEIGHTS["resolution"] * resolution_score
    )

    warnings: list[str] = []
    if sharpness_score < 0.2:
        warnings.append(
            "The image is likely blurred (low variance of the Laplacian). "
            "Recognition reliability is reduced."
        )
    if contrast_score < 0.2:
        warnings.append("The image has very low contrast; ridge flow may not be recoverable.")
    if brightness["over_exposed_percent"] > 5.0:
        warnings.append("More than 5% of the pixels are saturated, which destroys ridge detail.")
    if brightness["under_exposed_percent"] > 20.0:
        warnings.append("More than 20% of the pixels are effectively black.")
    if megapixels < 0.1:
        warnings.append(
            "The image resolution is below 0.1 megapixel; most published "
            "palmprint benchmarks use considerably larger captures."
        )

    return {
        "brightness": brightness,
        "contrast": contrast,
        "sharpness": sharpness,
        "dimensions": {
            "width": int(width),
            "height": int(height),
            "megapixels": round(megapixels, 4),
        },
        "sub_scores": {
            "exposure": round(exposure, 4),
            "contrast": round(contrast_score, 4),
            "sharpness": round(sharpness_score, 4),
            "resolution": round(resolution_score, 4),
        },
        "weights": dict(WEIGHTS),
        "combined_score": round(float(combined), 2),
        "combined_score_is_experimental": True,
        "warnings": warnings,
        "limitations": [
            "The combined score is an unvalidated engineering heuristic.",
            "It is not an ISO/IEC 19794-5 quality level assessment.",
            "Sub-scores depend on the sensor, capture protocol and scene content.",
            "Use the individual metrics for scientific reporting.",
        ],
    }


__all__ = ["WEIGHTS", "quality_report"]
