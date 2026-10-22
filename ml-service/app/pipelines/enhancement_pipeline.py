"""Image enhancement pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from ..algorithms.enhancement import (
    ENHANCEMENT_ALGORITHMS,
    clahe,
    filtering,
    histogram_equalization,
)
from ..utils.errors import AlgorithmError


@dataclass
class EnhancementResult:
    """Enhanced image plus the exact parameters that produced it."""

    image: np.ndarray
    algorithm: str
    version: str
    parameters: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def metadata(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "algorithm_version": self.version,
            "parameters": self.parameters,
            "output_width": int(self.image.shape[1]),
            "output_height": int(self.image.shape[0]),
        }


def apply_enhancement(
    image: np.ndarray,
    *,
    algorithm: str = "clahe",
    parameters: dict[str, Any] | None = None,
) -> EnhancementResult:
    """Apply the requested enhancement algorithm.

    The original image is never modified; the enhanced result is returned as
    a new array.
    """
    parameters = dict(parameters or {})
    name = (algorithm or "clahe").strip().lower()

    if name not in ENHANCEMENT_ALGORITHMS:
        raise AlgorithmError(
            f"Unknown enhancement algorithm '{algorithm}'.",
            details={"available": sorted(ENHANCEMENT_ALGORITHMS)},
        )

    if image is None or image.size == 0:
        raise AlgorithmError("Cannot enhance an empty image.")

    if name == histogram_equalization.ALGORITHM_NAME:
        color_space = str(parameters.get("color_space", "lab")).lower()
        if color_space not in {"lab", "per_channel"}:
            raise AlgorithmError(
                "color_space must be either 'lab' or 'per_channel'.",
                details={"received": color_space},
            )
        result = histogram_equalization.equalize_histogram(image, color_space=color_space)
        used = {"color_space": color_space}
        version = histogram_equalization.ALGORITHM_VERSION
        limitations = list(histogram_equalization.LIMITATIONS)

    elif name == clahe.ALGORITHM_NAME:
        clip_limit = float(parameters.get("clip_limit", 2.0))
        tile_grid_size = int(parameters.get("tile_grid_size", 8))
        if clip_limit <= 0:
            raise AlgorithmError("clip_limit must be greater than zero.")
        if not 1 <= tile_grid_size <= 32:
            raise AlgorithmError("tile_grid_size must be between 1 and 32.")
        result = clahe.apply_clahe(image, clip_limit=clip_limit, tile_grid_size=tile_grid_size)
        used = {"clip_limit": clip_limit, "tile_grid_size": tile_grid_size}
        version = clahe.ALGORITHM_VERSION
        limitations = list(clahe.LIMITATIONS)

    else:  # filtering
        filter_name = str(parameters.get("filter", "median")).strip().lower()
        if filter_name not in filtering.FILTERS:
            raise AlgorithmError(
                f"Unknown filter '{filter_name}'.",
                details={"available": sorted(filtering.FILTERS)},
            )
        if filter_name == "median":
            kernel_size = int(parameters.get("kernel_size", 5))
            result = filtering.median_filter(image, kernel_size=kernel_size)
            used = {"filter": filter_name, "kernel_size": kernel_size}
        elif filter_name == "gaussian":
            kernel_size = int(parameters.get("kernel_size", 5))
            sigma = float(parameters.get("sigma", 0.0))
            result = filtering.gaussian_filter(image, kernel_size=kernel_size, sigma=sigma)
            used = {"filter": filter_name, "kernel_size": kernel_size, "sigma": sigma}
        elif filter_name == "bilateral":
            diameter = int(parameters.get("diameter", 9))
            sigma_color = float(parameters.get("sigma_color", 75.0))
            sigma_space = float(parameters.get("sigma_space", 75.0))
            result = filtering.bilateral_filter(
                image,
                diameter=diameter,
                sigma_color=sigma_color,
                sigma_space=sigma_space,
            )
            used = {
                "filter": filter_name,
                "diameter": diameter,
                "sigma_color": sigma_color,
                "sigma_space": sigma_space,
            }
        else:  # sharpen
            amount = float(parameters.get("amount", 1.0))
            radius = int(parameters.get("radius", 3))
            result = filtering.unsharp_mask(image, amount=amount, radius=radius)
            used = {"filter": filter_name, "amount": amount, "radius": radius}
        version = filtering.ALGORITHM_VERSION
        limitations = list(filtering.LIMITATIONS)

    return EnhancementResult(
        image=result,
        algorithm=name,
        version=version,
        parameters=used,
        warnings=[
            "Enhancement changes the appearance of the image; the original "
            "capture is never overwritten."
        ],
        limitations=limitations,
    )


__all__ = ["EnhancementResult", "apply_enhancement"]
