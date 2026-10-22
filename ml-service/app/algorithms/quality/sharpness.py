"""Sharpness / blur estimation.

Two well known classical proxies are implemented:

* **Variance of the Laplacian** - the second derivative response of the image.
  A sharp image has a large variance; a blurred image has a small one.
* **Tenengrad gradient energy** - the mean squared Sobel gradient magnitude.

Both are heuristics.  They are only meaningful for a given imaging modality and
camera setup, they depend on the image content (a palm with very sparse ridges
looks "blurrier" than a dense one) and they are not calibrated against any
biometric standard.  Absolute thresholds must therefore be derived from a
labelled dataset before being used for acceptance decisions.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from ...utils.image_io import to_gray


def sharpness_metrics(image: np.ndarray) -> dict[str, Any]:
    """Compute blur proxies for a BGR/gray image."""
    gray = to_gray(image)
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    variance_of_laplacian = float(laplacian.var())

    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    tenengrad = float(np.mean(grad_x**2 + grad_y**2))

    # Local sharpness map (3x3 block variance of the Laplacian) expressed as
    # the fraction of the frame that is "reasonably sharp".  The absolute
    # threshold is a conventional heuristic, not a validated cut-off.
    blurred = cv2.GaussianBlur(laplacian, (3, 3), 0)
    local_variance = float(np.mean((laplacian - blurred) ** 2))
    sharp_pixel_ratio = float(np.mean(np.abs(laplacian) > 10.0) * 100.0)

    return {
        "variance_of_laplacian": round(variance_of_laplacian, 3),
        "tenengrad_energy": round(tenengrad, 3),
        "local_sharpness": round(local_variance, 3),
        "sharp_pixel_ratio_percent": round(sharp_pixel_ratio, 3),
        "interpretation": (
            "variance_of_laplacian is the standard blur proxy. It is relative to "
            "other captures of the same sensor, not an absolute quality verdict."
        ),
    }


def is_blurry(image: np.ndarray, *, threshold: float = 100.0) -> bool:
    """Heuristic blur flag using the variance of the Laplacian."""
    gray = to_gray(image)
    return bool(cv2.Laplacian(gray, cv2.CV_64F).var() < threshold)


__all__ = ["is_blurry", "sharpness_metrics"]
