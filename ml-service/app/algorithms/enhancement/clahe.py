"""Contrast Limited Adaptive Histogram Equalisation (CLAHE).

CLAHE performs local histogram equalisation on tiles and clips the resulting
histograms to limit noise amplification.  It is the default enhancement for
palmprint research because it compensates for the strong illumination
gradients produced by contact sensors while keeping local contrast.

Reference: Zuiderveld, K. (1994). Contrast Limited Adaptive Histogram
Equalisation. In Graphics Gems IV.
"""

from __future__ import annotations

import cv2
import numpy as np

from ...utils.image_io import to_bgr

ALGORITHM_NAME = "clahe"
ALGORITHM_VERSION = "1.0.0"

LIMITATIONS = (
    "Tile size and clip limit interact; results are not comparable across "
    "different parameterisations without re-tuning.",
    "Can amplify sensor noise in low-texture regions.",
    "Does not correct geometric distortion or non-uniform blur.",
)


def apply_clahe(
    image: np.ndarray,
    *,
    clip_limit: float = 2.0,
    tile_grid_size: int = 8,
) -> np.ndarray:
    """Apply CLAHE to the luminance channel of a BGR image."""
    if image is None or image.size == 0:
        raise ValueError("Cannot enhance an empty image.")
    if clip_limit <= 0:
        raise ValueError("clip_limit must be greater than zero.")
    if tile_grid_size < 1:
        raise ValueError("tile_grid_size must be at least 1.")

    source = to_bgr(image)
    clahe = cv2.createCLAHE(
        clipLimit=float(clip_limit), tileGridSize=(tile_grid_size, tile_grid_size)
    )

    if source.shape[2] == 3:
        lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    return clahe.apply(source)


def describe() -> dict[str, object]:
    return {
        "name": ALGORITHM_NAME,
        "version": ALGORITHM_VERSION,
        "parameters": {
            "clip_limit": {
                "type": "float",
                "default": 2.0,
                "range": [0.1, 40.0],
                "description": "Clip limit for the contrast limited histograms.",
            },
            "tile_grid_size": {
                "type": "int",
                "default": 8,
                "range": [1, 32],
                "description": "Number of tiles per axis.",
            },
        },
        "limitations": list(LIMITATIONS),
    }
