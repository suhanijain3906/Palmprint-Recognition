"""Descriptor matching and inlier filtering.

Matching strategy
-----------------
1. Brute force matching of the binary descriptors with Hamming distance.
2. For every descriptor of image A the two best matches in image B are
   retrieved and the **Lowe ratio test** rejects ambiguous matches
   (``best.distance / second_best.distance < ratio``).
3. The surviving matches are additionally verified with a **cross-check**
   (the reverse match must point back to the same keypoint).

The ratio test is the standard way to reject descriptors that have no
unique counterpart.  It does not perform geometric verification: the matched
keypoints are not constrained to a homography, so repeated ridge patterns can
still produce false correspondences.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cv2
import numpy as np

from ..utils.errors import InsufficientFeaturesError
from .classical_features import FeatureSet


@dataclass
class MatchResult:
    """Statistics describing the outcome of a descriptor matching run."""

    good_matches: list[cv2.DMatch] = field(default_factory=list)
    total_candidates: int = 0
    ratio_rejected: int = 0
    cross_check_rejected: int = 0
    mean_distance: float = 0.0
    median_distance: float = 0.0
    descriptor_matcher: str = "BFMatcher(NORM_HAMMING)"
    warnings: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.good_matches)

    def summary(self) -> dict[str, Any]:
        return {
            "matcher": self.descriptor_matcher,
            "good_matches": self.count,
            "candidate_matches": self.total_candidates,
            "rejected_by_ratio_test": self.ratio_rejected,
            "rejected_by_cross_check": self.cross_check_rejected,
            "mean_hamming_distance": round(self.mean_distance, 4),
            "median_hamming_distance": round(self.median_distance, 4),
            "warnings": list(self.warnings),
        }


def match_descriptors(
    features_a: FeatureSet,
    features_b: FeatureSet,
    *,
    lowe_ratio: float = 0.75,
    cross_check: bool = True,
) -> MatchResult:
    """Match the descriptors of two feature sets.

    Raises
    ------
    InsufficientFeaturesError
        One of the images produced no descriptors at all.
    """
    if features_a.descriptors is None or features_b.descriptors is None:
        missing = "first" if features_a.descriptors is None else "second"
        raise InsufficientFeaturesError(
            f"The {missing} image produced no descriptors, so no matching can be performed.",
            details={"first_keypoints": features_a.count, "second_keypoints": features_b.count},
        )

    if not 0.0 < lowe_ratio < 1.0:
        raise ValueError("lowe_ratio must be strictly between 0 and 1.")

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING)
    knn = matcher.knnMatch(features_a.descriptors, features_b.descriptors, k=2)

    good: list[cv2.DMatch] = []
    total = 0
    ratio_rejected = 0
    for pair in knn:
        if len(pair) < 2:
            continue
        best, second = pair[0], pair[1]
        total += 1
        if best.distance == 0:
            # Perfect match: accept only if it is clearly better than the
            # runner up (ratio test degenerates for distance 0).
            if second.distance > 0:
                good.append(best)
            else:
                ratio_rejected += 1
            continue
        if best.distance < lowe_ratio * second.distance:
            good.append(best)
        else:
            ratio_rejected += 1

    cross_check_rejected = 0
    if cross_check and good:
        reverse = matcher.knnMatch(features_b.descriptors, features_a.descriptors, k=1)
        reverse_map: dict[int, int] = {}
        for pair in reverse:
            if pair:
                reverse_map[pair[0].queryIdx] = pair[0].trainIdx
        verified: list[cv2.DMatch] = []
        for match in good:
            if reverse_map.get(match.trainIdx) == match.queryIdx:
                verified.append(match)
            else:
                cross_check_rejected += 1
        good = verified

    distances = [float(m.distance) for m in good]
    warnings: list[str] = []
    if not good:
        warnings.append(
            "No descriptor pair survived the ratio test and cross-check. "
            "The two images most likely do not share detectable structure."
        )
    elif len(good) < 10:
        warnings.append(
            f"Only {len(good)} match(es) survived filtering; the match count is too "
            "small to be statistically meaningful."
        )

    return MatchResult(
        good_matches=good,
        total_candidates=total,
        ratio_rejected=ratio_rejected,
        cross_check_rejected=cross_check_rejected,
        mean_distance=float(np.mean(distances)) if distances else 0.0,
        median_distance=float(np.median(distances)) if distances else 0.0,
        warnings=warnings,
    )


def draw_matches(
    image_a: np.ndarray,
    features_a: FeatureSet,
    image_b: np.ndarray,
    features_b: FeatureSet,
    result: MatchResult,
    *,
    max_draw: int = 120,
) -> np.ndarray:
    """Render the surviving matches into a single visualisation image."""
    if not result.good_matches:
        return np.zeros((1, 1, 3), dtype=np.uint8)

    matches = result.good_matches[:max_draw]
    keypoints_a = features_a.keypoints
    keypoints_b = features_b.keypoints

    visualisation = cv2.drawMatches(
        image_a,
        keypoints_a,
        image_b,
        keypoints_b,
        matches,
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
        matchColor=(0, 200, 120),
        singlePointColor=(120, 120, 120),
        matchesMask=list(range(len(matches))),
    )
    return visualisation


__all__ = ["MatchResult", "draw_matches", "match_descriptors"]
