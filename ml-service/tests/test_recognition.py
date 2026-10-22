"""Tests for the experimental recognition matcher."""

from __future__ import annotations

import numpy as np

from app.recognition.classical_matcher import ClassicalMatcher
from app.recognition.model_loader import discover_models
from tests.conftest import make_synthetic_palm


def test_matching_identical_images_gives_high_similarity(synthetic_palm: np.ndarray) -> None:
    matcher = ClassicalMatcher()
    result = matcher.compare(synthetic_palm, synthetic_palm)
    assert result.available is True
    assert result.similarity_score is not None
    assert result.similarity_score > 0.5
    assert result.is_trained_model is False
    assert result.is_calibrated_probability is False


def test_similarity_is_not_a_probability(synthetic_palm: np.ndarray) -> None:
    result = ClassicalMatcher().compare(synthetic_palm, synthetic_palm)
    assert result.score_kind == "uncalibrated_similarity_index"
    assert result.is_calibrated_probability is False
    assert result.limitations


def test_unrelated_images_give_lower_similarity(synthetic_palm: np.ndarray) -> None:
    other = make_synthetic_palm(320, 320, seed=123)
    same = ClassicalMatcher().compare(synthetic_palm, synthetic_palm).similarity_score or 0.0
    different = ClassicalMatcher().compare(synthetic_palm, other).similarity_score or 0.0
    assert different < same


def test_comparison_with_featureless_image_is_unavailable() -> None:
    flat = np.full((160, 160, 3), 120, dtype=np.uint8)
    result = ClassicalMatcher().compare(flat, flat)
    assert result.available is False
    assert result.similarity_score is None
    assert any("no detectable features" in warning for warning in result.warnings)


def test_no_trained_model_is_installed_by_default(tmp_path) -> None:
    status = discover_models(tmp_path)
    assert status.available is False
    assert "No trained models" in status.message


def test_details_expose_the_formula(synthetic_palm: np.ndarray) -> None:
    result = ClassicalMatcher().compare(synthetic_palm, synthetic_palm)
    assert "score_formula" in result.details
    assert result.details["matcher"] == "BFMatcher(NORM_HAMMING)"
