"""Image comparison pipeline.

Produces the artefacts of the side-by-side comparison page:

* an absolute-difference image,
* the peak signal-to-noise ratio (PSNR),
* the structural similarity index (SSIM),
* an optional feature-match visualisation.

Metric assumptions
------------------
**PSNR** is defined for two images of *identical* dimensions and pixel
alignment.  When the dimensions differ, the second image is resized to the
first one; the resulting value then mixes content difference with resampling
error and is reported with a warning.

**SSIM** (Wang et al., 2004) is likewise only meaningful for aligned images
and is computed on grayscale.  The scikit-image implementation is used with
``data_range`` derived from the image dtype.

Both metrics are *pixel-similarity* measures.  They say nothing about whether
two images depict the same palm.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from ..utils.image_io import to_bgr, to_gray


@dataclass
class ComparisonOutcome:
    """Everything the comparison page needs."""

    difference_image: np.ndarray
    psnr: float | None
    ssim: float | None
    aligned: bool
    resized: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


def compute_psnr(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Peak signal-to-noise ratio between two aligned images."""
    mse = float(np.mean((image_a.astype(np.float64) - image_b.astype(np.float64)) ** 2))
    if mse == 0:
        return float("inf")
    return float(10.0 * np.log10((255.0**2) / mse))


def compute_ssim(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Structural similarity index between two aligned grayscale images."""
    from skimage.metrics import structural_similarity

    gray_a = to_gray(image_a)
    gray_b = to_gray(image_b)
    similarity = structural_similarity(
        gray_a,
        gray_b,
        data_range=float(gray_a.dtype.type(255).item()),
    )
    return float(similarity)


def compare_images(image_a: np.ndarray, image_b: np.ndarray) -> ComparisonOutcome:
    """Compare two images and produce difference image plus pixel metrics."""
    if image_a is None or image_a.size == 0 or image_b is None or image_b.size == 0:
        raise ValueError("Both images are required for a comparison.")

    source_a = to_bgr(image_a)
    source_b = to_bgr(image_b)

    warnings: list[str] = []
    resized = False
    aligned = source_a.shape[:2] == source_b.shape[:2]

    if not aligned:
        resized = True
        warnings.append(
            "The images have different dimensions. The second image was resized "
            "to match the first one, so PSNR and SSIM mix content difference "
            "with resampling error."
        )
        source_b = cv2.resize(
            source_b, (source_a.shape[1], source_a.shape[0]), interpolation=cv2.INTER_AREA
        )

    difference = cv2.absdiff(source_a, source_b)
    amplified = cv2.convertScaleAbs(difference, alpha=3.0)

    psnr_value = compute_psnr(source_a, source_b)
    ssim_value = compute_ssim(source_a, source_b)

    metrics = {
        "first_width": int(source_a.shape[1]),
        "first_height": int(source_a.shape[0]),
        "second_width": int(image_b.shape[1]),
        "second_height": int(image_b.shape[0]),
        "difference_mean": round(float(difference.mean()), 4),
        "difference_max": int(difference.max()),
        "psnr_db": None if np.isinf(psnr_value) else round(psnr_value, 4),
        "ssim": round(ssim_value, 6),
    }

    if np.isinf(psnr_value):
        warnings.append("PSNR is infinite because the two images are pixel identical.")
    if ssim_value < 0:
        warnings.append(
            "The SSIM value is negative, which happens for structurally very different images."
        )

    limitations = [
        "PSNR and SSIM measure pixel-level similarity between two aligned "
        "images, not biometric similarity.",
        "PSNR is unbounded above and is not comparable between different "
        "image resolutions without normalisation.",
        "SSIM depends on the chosen window size and data range.",
        "Neither metric detects whether two images show the same palm.",
    ]

    return ComparisonOutcome(
        difference_image=amplified,
        psnr=None if np.isinf(psnr_value) else psnr_value,
        ssim=ssim_value,
        aligned=aligned,
        resized=resized,
        metrics=metrics,
        warnings=warnings,
        limitations=limitations,
    )


__all__ = ["ComparisonOutcome", "compare_images", "compute_psnr", "compute_ssim"]
