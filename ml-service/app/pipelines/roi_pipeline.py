"""ROI extraction pipeline.

The pipeline owns parameter validation and result shaping; the actual image
processing lives in :mod:`app.algorithms.roi`.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..algorithms.roi import ROI_ALGORITHMS, ROIResult, get_roi_algorithm
from ..utils.errors import AlgorithmError


def extract_roi(
    image: np.ndarray,
    *,
    algorithm: str | None = None,
    parameters: dict[str, Any] | None = None,
) -> ROIResult:
    """Run the configured ROI algorithm and return a :class:`ROIResult`."""
    parameters = parameters or {}
    try:
        instance = get_roi_algorithm(algorithm)
    except KeyError as exc:
        raise AlgorithmError(str(exc), details={"available": sorted(ROI_ALGORITHMS)}) from exc

    supported = {
        "median_ksize": int,
        "morph_kernel": int,
        "min_area_ratio": float,
        "padding_ratio": float,
        "fallback_ratio": float,
    }
    kwargs: dict[str, Any] = {}
    for key, caster in supported.items():
        if key in parameters and parameters[key] is not None:
            kwargs[key] = caster(parameters[key])

    result = instance.extract(image)
    result.metrics["parameters"] = kwargs
    result.metrics["algorithm"] = instance.name
    result.metrics["algorithm_version"] = instance.version
    return result


__all__ = ["extract_roi"]
