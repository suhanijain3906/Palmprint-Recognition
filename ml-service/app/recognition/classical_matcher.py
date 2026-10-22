"""Classical, untrained comparison matcher.

Pipeline
--------
1. Extract ORB (or AKAZE) keypoints/descriptors from both images.
2. Match the descriptors with the ratio test and cross-check.
3. Derive a similarity score in ``[0, 1]`` from the number of surviving
   matches relative to the size of the smaller descriptor set.

Interpretation
--------------
The score is an **uncalibrated heuristic similarity index**.  It answers
"how much of the smaller feature set could be matched in the other image",
not "how likely is it the same person".  It is *not* a probability, it is
*not* calibrated against a verification protocol and it must never be
presented as an identity confidence.  A genuine/impostor study (see
:mod:`app.evaluation`) is required before any threshold is chosen.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..features.classical_features import extract_features
from ..features.feature_matching import match_descriptors
from ..utils.errors import AlgorithmError
from .base import BiometricMatcher, RecognitionResult


class ClassicalMatcher(BiometricMatcher):
    """Descriptor matching based experimental matcher."""

    name = "classical_orb_matcher"
    version = "1.0.0"
    is_trained_model = False

    def __init__(
        self,
        *,
        detector: str = "orb",
        n_features: int = 2000,
        lowe_ratio: float = 0.75,
        cross_check: bool = True,
    ) -> None:
        self.detector = detector
        self.n_features = n_features
        self.lowe_ratio = lowe_ratio
        self.cross_check = cross_check

    @property
    def available(self) -> bool:
        return True

    def compare(self, image_a: np.ndarray, image_b: np.ndarray) -> RecognitionResult:
        if image_a is None or image_a.size == 0 or image_b is None or image_b.size == 0:
            raise AlgorithmError("Both images must be provided for a comparison.")

        features_a = extract_features(image_a, detector=self.detector, n_features=self.n_features)
        features_b = extract_features(image_b, detector=self.detector, n_features=self.n_features)

        details: dict[str, Any] = {
            "detector": self.detector,
            "first_keypoints": features_a.count,
            "second_keypoints": features_b.count,
            "lowe_ratio": self.lowe_ratio,
            "cross_check": self.cross_check,
        }
        warnings: list[str] = []
        warnings.extend(features_a.warnings)
        warnings.extend(features_b.warnings)

        if features_a.count == 0 or features_b.count == 0:
            warnings.append(
                "At least one image produced no detectable features, so no "
                "similarity score could be computed."
            )
            return RecognitionResult(
                similarity_score=None,
                score_kind="unavailable",
                available=False,
                matcher_name=self.name,
                matcher_version=self.version,
                details=details,
                warnings=warnings,
                limitations=self.limitations(),
            )

        matches = match_descriptors(
            features_a,
            features_b,
            lowe_ratio=self.lowe_ratio,
            cross_check=self.cross_check,
        )
        warnings.extend(matches.warnings)

        smaller = min(features_a.count, features_b.count)
        coverage = matches.count / float(smaller) if smaller else 0.0
        score = float(np.clip(coverage, 0.0, 1.0))

        details.update(matches.summary())
        details["match_coverage"] = round(coverage, 4)
        details["score_formula"] = (
            "match_coverage = good_matches / min(keypoints_a, keypoints_b); "
            "similarity_score = clip(match_coverage, 0, 1)"
        )

        if matches.count == 0:
            warnings.append(
                "No match survived the ratio test; the two images share no "
                "detectable descriptor structure."
            )

        return RecognitionResult(
            similarity_score=round(score, 4),
            score_kind="uncalibrated_similarity_index",
            available=True,
            matcher_name=self.name,
            matcher_version=self.version,
            details=details,
            warnings=warnings,
            limitations=self.limitations(),
        )

    @staticmethod
    def limitations() -> list[str]:
        return [
            "The similarity score is an uncalibrated heuristic, not a probability "
            "of identity and not a similarity score validated against a protocol.",
            "No trained biometric model or learned weights are involved.",
            "Generic ORB/AKAZE keypoints do not encode palm ridge orientation, "
            "which is the dominant cue in palmprint recognition.",
            "A threshold can only be chosen after a genuine/impostor evaluation "
            "on an authorised dataset.",
        ]


__all__ = ["ClassicalMatcher"]
