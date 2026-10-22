"""Tests for feature extraction and descriptor matching."""

from __future__ import annotations

import numpy as np
import pytest

from app.features.classical_features import extract_features, hog_descriptor
from app.features.feature_matching import draw_matches, match_descriptors
from app.utils.errors import InsufficientFeaturesError
from tests.conftest import make_synthetic_palm


def test_features_are_detected_on_a_textured_image(synthetic_palm: np.ndarray) -> None:
    features = extract_features(synthetic_palm, detector="orb", n_features=500)
    assert features.count > 0
    assert features.descriptors is not None
    assert features.descriptors.shape[0] == features.count
    assert len(features.points) == features.count


def test_unknown_detector_raises(synthetic_palm: np.ndarray) -> None:
    with pytest.raises(ValueError):
        extract_features(synthetic_palm, detector="magic")


def test_empty_image_raises() -> None:
    with pytest.raises(ValueError):
        extract_features(np.zeros((0, 0, 3), dtype=np.uint8))


def test_uniform_image_yields_no_features() -> None:
    flat = np.full((128, 128, 3), 120, dtype=np.uint8)
    features = extract_features(flat)
    assert features.count == 0
    assert features.descriptors is None
    assert features.warnings


def test_matching_same_image_finds_matches(synthetic_palm: np.ndarray) -> None:
    features_a = extract_features(synthetic_palm, n_features=1000)
    features_b = extract_features(synthetic_palm, n_features=1000)
    result = match_descriptors(features_a, features_b)
    assert result.count > 0
    assert result.mean_distance < 60.0


def test_matching_different_images_finds_fewer_matches(synthetic_palm: np.ndarray) -> None:
    other = make_synthetic_palm(320, 320, seed=99)
    features_a = extract_features(synthetic_palm, n_features=1000)
    features_b = extract_features(other, n_features=1000)
    result = match_descriptors(features_a, features_b)
    assert result.count <= 400
    assert result.total_candidates >= result.count


def test_matching_without_features_raises(synthetic_palm: np.ndarray) -> None:
    flat = np.full((128, 128, 3), 120, dtype=np.uint8)
    empty = extract_features(flat)
    features = extract_features(synthetic_palm)
    with pytest.raises(InsufficientFeaturesError):
        match_descriptors(empty, features)
    with pytest.raises(InsufficientFeaturesError):
        match_descriptors(features, empty)


def test_matching_validates_ratio(synthetic_palm: np.ndarray) -> None:
    features = extract_features(synthetic_palm)
    with pytest.raises(ValueError):
        match_descriptors(features, features, lowe_ratio=1.5)


def test_draw_matches_produces_an_image(synthetic_palm: np.ndarray) -> None:
    features_a = extract_features(synthetic_palm, n_features=300)
    features_b = extract_features(synthetic_palm, n_features=300)
    result = match_descriptors(features_a, features_b)
    visualisation = draw_matches(synthetic_palm, features_a, synthetic_palm, features_b, result)
    assert visualisation.size > 0


def test_hog_descriptor_has_expected_length(synthetic_palm: np.ndarray) -> None:
    vector = hog_descriptor(synthetic_palm)
    assert vector.ndim == 1
    assert vector.size > 0
