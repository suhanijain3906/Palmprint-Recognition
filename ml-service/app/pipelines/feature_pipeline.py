"""Feature extraction and matching pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from ..features.classical_features import FeatureSet, extract_features
from ..features.feature_matching import MatchResult, match_descriptors
from ..utils.errors import AlgorithmError


@dataclass
class FeatureExtractionOutcome:
    """Feature set plus the metadata that is safe to return over HTTP."""

    features: FeatureSet
    parameters: dict[str, Any]

    def metadata(self) -> dict[str, Any]:
        data = self.features.summary()
        data["parameters"] = self.parameters
        return data


def extract(
    image: np.ndarray,
    *,
    detector: str = "orb",
    n_features: int = 2000,
    edge_threshold: int = 31,
) -> FeatureExtractionOutcome:
    """Extract features from a single image."""
    if image is None or image.size == 0:
        raise AlgorithmError("Cannot extract features from an empty image.")

    try:
        features = extract_features(
            image,
            detector=detector,
            n_features=n_features,
            edge_threshold=edge_threshold,
        )
    except ValueError as exc:
        raise AlgorithmError(str(exc)) from exc

    return FeatureExtractionOutcome(
        features=features,
        parameters={
            "detector": detector,
            "n_features": n_features,
            "edge_threshold": edge_threshold,
        },
    )


def match(
    features_a: FeatureSet,
    features_b: FeatureSet,
    *,
    lowe_ratio: float = 0.75,
    cross_check: bool = True,
) -> MatchResult:
    """Match two previously extracted feature sets."""
    return match_descriptors(
        features_a,
        features_b,
        lowe_ratio=lowe_ratio,
        cross_check=cross_check,
    )


__all__ = ["FeatureExtractionOutcome", "extract", "match"]
