"""Noise reduction and sharpening filters.

All filters return BGR uint8 images and never modify their input.
"""

from __future__ import annotations

import cv2
import numpy as np

from ...utils.image_io import to_bgr

ALGORITHM_NAME = "filtering"
ALGORITHM_VERSION = "1.0.0"

LIMITATIONS = (
    "Median filtering removes salt-and-pepper noise but blurs fine ridge structure "
    "when the kernel is large.",
    "Gaussian filtering is isotropic and therefore removes ridge orientation information.",
    "Unsharp masking amplifies high frequency noise together with ridge detail.",
)


def median_filter(image: np.ndarray, *, kernel_size: int = 5) -> np.ndarray:
    """Median filter; ``kernel_size`` is forced to an odd integer >= 3."""
    source = to_bgr(image)
    k = max(3, int(kernel_size) | 1)
    return cv2.medianBlur(source, k)


def gaussian_filter(image: np.ndarray, *, kernel_size: int = 5, sigma: float = 0.0) -> np.ndarray:
    """Gaussian blur; ``sigma`` of 0 means "derive from the kernel size"."""
    source = to_bgr(image)
    k = max(3, int(kernel_size) | 1)
    return cv2.GaussianBlur(source, (k, k), float(sigma))


def bilateral_filter(
    image: np.ndarray, *, diameter: int = 9, sigma_color: float = 75, sigma_space: float = 75
) -> np.ndarray:
    """Edge preserving smoothing."""
    source = to_bgr(image)
    d = max(3, int(diameter))
    return cv2.bilateralFilter(source, d, float(sigma_color), float(sigma_space))


def unsharp_mask(image: np.ndarray, *, amount: float = 1.0, radius: int = 3) -> np.ndarray:
    """Sharpen with an unsharp mask: ``original + amount * (original - blurred)``."""
    source = to_bgr(image).astype(np.float32)
    radius = max(1, int(radius))
    blurred = cv2.GaussianBlur(source, (0, 0), sigmaX=radius, sigmaY=radius)
    sharpened = source + float(amount) * (source - blurred)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


FILTERS = {
    "median": median_filter,
    "gaussian": gaussian_filter,
    "bilateral": bilateral_filter,
    "sharpen": unsharp_mask,
}


def describe() -> dict[str, object]:
    return {
        "name": ALGORITHM_NAME,
        "version": ALGORITHM_VERSION,
        "filters": sorted(FILTERS),
        "parameters": {
            "filter": {"type": "enum", "values": sorted(FILTERS), "default": "median"},
            "kernel_size": {"type": "int", "default": 5, "range": [3, 31]},
            "sigma": {"type": "float", "default": 0.0, "range": [0.0, 10.0]},
            "amount": {"type": "float", "default": 1.0, "range": [0.0, 5.0]},
            "radius": {"type": "int", "default": 3, "range": [1, 15]},
        },
        "limitations": list(LIMITATIONS),
    }
