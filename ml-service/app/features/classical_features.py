"""Classical feature extraction.

The platform ships with a **replaceable classical baseline**:

* ``orb``   - Oriented FAST and Rotated BRIEF keypoints + binary descriptors.
* ``akaze`` - AKAZE keypoints + binary descriptors (slower, often more
  stable on ridge textures than ORB).

Both are generic computer-vision detectors.  They are **not** palmprint
specific: they respond to corners and texture blobs, not to the oriented
line-like structure of palm ridges.  Their suitability for a particular
dataset has to be established empirically (see :mod:`app.evaluation`).

A third, purely statistical descriptor (``hog``) summarises the gradient
orientation distribution of the image and can be used as a coarse
coarse-structure similarity check.

All descriptors are returned as plain numpy arrays so that they can be
cached, serialised and re-used by the matching stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from ..utils.image_io import to_gray

DETECTORS = ("orb", "akaze")


@dataclass
class FeatureSet:
    """Keypoints and descriptors extracted from a single image."""

    detector: str
    keypoints: list[cv2.KeyPoint] = field(default_factory=list)
    descriptors: np.ndarray | None = None
    descriptor_kind: str = "binary"
    image_width: int = 0
    image_height: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.keypoints)

    @property
    def points(self) -> list[tuple[float, float]]:
        return [(float(kp.pt[0]), float(kp.pt[1])) for kp in self.keypoints]

    def summary(self) -> dict[str, Any]:
        return {
            "detector": self.detector,
            "descriptor_kind": self.descriptor_kind,
            "keypoint_count": self.count,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "warnings": list(self.warnings),
        }


def _build_detector(name: str, *, n_features: int, edge_threshold: int) -> Any:
    if name == "orb":
        return cv2.ORB_create(
            nfeatures=n_features,
            scaleFactor=1.2,
            nlevels=8,
            edgeThreshold=edge_threshold,
            fastThreshold=12,
        )
    if name == "akaze":
        return cv2.AKAZE_create()
    raise ValueError(f"Unknown feature detector '{name}'. Supported: {list(DETECTORS)}")


def extract_features(
    image: np.ndarray,
    *,
    detector: str = "orb",
    n_features: int = 2000,
    edge_threshold: int = 31,
    mask: np.ndarray | None = None,
) -> FeatureSet:
    """Extract keypoints and descriptors from ``image``.

    Raises
    ------
    ValueError
        The detector name is unknown or the image is empty.
    """
    if image is None or image.size == 0:
        raise ValueError("Cannot extract features from an empty image.")

    name = detector.strip().lower()
    if name not in DETECTORS:
        raise ValueError(f"Unknown feature detector '{detector}'. Supported: {list(DETECTORS)}")

    gray = to_gray(image)
    detector_instance = _build_detector(name, n_features=n_features, edge_threshold=edge_threshold)

    keypoints, descriptors = detector_instance.detectAndCompute(gray, mask)

    height, width = gray.shape[:2]
    warnings: list[str] = []
    if descriptors is None or len(keypoints) == 0:
        warnings.append(
            "No keypoints were detected. The image may be too uniform, "
            "blurred or of very low contrast."
        )
        descriptors = None

    return FeatureSet(
        detector=name,
        keypoints=list(keypoints),
        descriptors=descriptors,
        descriptor_kind="binary",
        image_width=int(width),
        image_height=int(height),
        warnings=warnings,
    )


def hog_descriptor(image: np.ndarray, *, orientations: int = 9, cells: int = 4) -> np.ndarray:
    """Return a normalised HOG descriptor (coarse gradient structure)."""
    from skimage.feature import hog

    gray = to_gray(image)
    resized = cv2.resize(gray, (64, 64), interpolation=cv2.INTER_AREA)
    vector = hog(
        resized,
        orientations=orientations,
        pixels_per_cell=(16, 16),
        cells_per_block=(cells, cells),
        block_norm="L2-Hys",
        feature_vector=True,
    )
    return np.asarray(vector, dtype=np.float64)


def describe() -> list[dict[str, Any]]:
    return [
        {
            "name": "orb",
            "type": "keypoint_descriptor",
            "descriptor": "binary (256 bit rBRIEF)",
            "parameters": {
                "n_features": {"type": "int", "default": 2000, "range": [16, 20000]},
                "edge_threshold": {"type": "int", "default": 31, "range": [1, 100]},
            },
            "limitations": [
                "Generic corner detector; not tuned to palm ridge structure.",
                "Binary descriptors degrade strongly under blur and non-uniform illumination.",
            ],
        },
        {
            "name": "akaze",
            "type": "keypoint_descriptor",
            "descriptor": "binary (AKE descriptor)",
            "parameters": {},
            "limitations": [
                "Slower than ORB.",
                "Generic detector; not tuned to palm ridge structure.",
            ],
        },
        {
            "name": "hog",
            "type": "global_descriptor",
            "descriptor": "float vector",
            "parameters": {
                "orientations": {"type": "int", "default": 9, "range": [4, 36]},
                "cells": {"type": "int", "default": 4, "range": [1, 8]},
            },
            "limitations": [
                "Describes coarse gradient structure, not individual ridges.",
                "Insensitive to fine ridge detail; useful only as a coarse sanity check.",
            ],
        },
    ]


__all__ = ["DETECTORS", "FeatureSet", "describe", "extract_features", "hog_descriptor"]
