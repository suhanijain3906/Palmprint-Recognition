"""Quality assessment pipeline."""

from __future__ import annotations

from typing import Any

import numpy as np

from ..algorithms.quality import quality_report


def analyze_quality(image: np.ndarray) -> dict[str, Any]:
    """Return the full quality report for an image."""
    if image is None or image.size == 0:
        raise ValueError("Cannot analyse the quality of an empty image.")
    return quality_report(image)


__all__ = ["analyze_quality"]
