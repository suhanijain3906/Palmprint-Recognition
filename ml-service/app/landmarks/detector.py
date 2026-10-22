"""Feature point detection used for overlay visualisation.

Naming
------
The functions in this module detect **generic feature points** (keypoints
detected by a classical detector such as ORB or AKAZE).  They are *not*
anatomical palm landmarks: no trained palm-landmark detector is bundled with
this project, so the terms "landmark" and "keypoint" must not be used
interchangeably in documentation or in the API payloads.

An anatomical landmark (for example the centre of the palm or the interdigital
points between the fingers) can only be produced by a dedicated landmark
model.  :func:`landmark_model_status` reports whether such a model is
available so the UI can render an honest empty state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from ..features.classical_features import DETECTORS, extract_features


@dataclass
class LandmarkResult:
    """Detected feature points and the method that produced them."""

    points: list[tuple[float, float]] = field(default_factory=list)
    sizes: list[float] = field(default_factory=list)
    method: str = "none"
    kind: str = "feature_point"
    is_anatomical: bool = False
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.points)

    def summary(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "kind": self.kind,
            "is_anatomical": self.is_anatomical,
            "point_count": self.count,
            "points": [{"x": round(x, 2), "y": round(y, 2)} for x, y in self.points],
            "warnings": list(self.warnings),
        }


def landmark_model_status(model_dir: Path | str) -> dict[str, Any]:
    """Report whether a trained anatomical landmark model is installed."""
    directory = Path(model_dir)
    candidates: list[str] = []
    if directory.is_dir():
        for pattern in ("*.pt", "*.onnx", "*.pth", "*.tflite"):
            candidates.extend(sorted(p.name for p in directory.glob(pattern)))
    return {
        "anatomical_landmark_model_available": bool(candidates),
        "model_files": candidates,
        "message": (
            "A trained anatomical landmark model was found; landmark based "
            "visualisation can be enabled."
            if candidates
            else "No trained anatomical landmark model is installed. Only generic "
            "feature points can be visualised."
        ),
    }


def detect_feature_points(
    image: np.ndarray,
    *,
    detector: str = "orb",
    n_features: int = 500,
    max_points: int = 300,
) -> LandmarkResult:
    """Detect generic feature points and return them as a :class:`LandmarkResult`."""
    name = detector.strip().lower()
    if name not in DETECTORS:
        raise ValueError(f"Unknown detector '{detector}'. Supported: {list(DETECTORS)}")

    features = extract_features(image, detector=name, n_features=n_features)
    points = features.points[:max_points]
    sizes = [float(getattr(kp, "size", 1.0)) for kp in features.keypoints[:max_points]]

    warnings = list(features.warnings)
    warnings.append(
        "These are generic feature points from a classical detector. They are "
        "not anatomical palm landmarks."
    )
    if features.count == 0:
        warnings.append(
            "No feature points could be detected in this image; the overlay will be empty."
        )

    return LandmarkResult(
        points=points,
        sizes=sizes,
        method=f"{name.upper()} feature points",
        kind="feature_point",
        is_anatomical=False,
        warnings=warnings,
    )


__all__ = ["LandmarkResult", "detect_feature_points", "landmark_model_status"]
