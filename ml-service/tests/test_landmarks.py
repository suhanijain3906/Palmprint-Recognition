"""Tests for the landmark / feature point visualisation."""

from __future__ import annotations

import numpy as np

from app.landmarks.detector import detect_feature_points, landmark_model_status
from app.landmarks.visualization import draw_landmarks


def test_feature_points_are_detected(synthetic_palm: np.ndarray) -> None:
    result = detect_feature_points(synthetic_palm, detector="orb", max_points=50)
    assert result.count > 0
    assert result.count <= 50
    assert result.is_anatomical is False
    assert result.kind == "feature_point"


def test_feature_points_are_not_called_landmarks(synthetic_palm: np.ndarray) -> None:
    result = detect_feature_points(synthetic_palm)
    assert any("not anatomical" in warning.lower() for warning in result.warnings)


def test_coordinates_are_within_the_image(synthetic_palm: np.ndarray) -> None:
    result = detect_feature_points(synthetic_palm, max_points=100)
    height, width = synthetic_palm.shape[:2]
    for x, y in result.points:
        assert 0 <= x <= width
        assert 0 <= y <= height


def test_empty_state_for_uniform_image() -> None:
    flat = np.full((160, 160, 3), 128, dtype=np.uint8)
    result = detect_feature_points(flat)
    assert result.count == 0
    assert any("No feature points" in warning for warning in result.warnings)


def test_overlay_is_rendered(synthetic_palm: np.ndarray) -> None:
    landmarks = detect_feature_points(synthetic_palm, max_points=25)
    overlay = draw_landmarks(synthetic_palm, landmarks)
    assert overlay.shape == synthetic_palm.shape
    assert overlay.dtype == np.uint8


def test_landmark_model_status_without_models(tmp_path) -> None:
    status = landmark_model_status(tmp_path)
    assert status["anatomical_landmark_model_available"] is False
    assert "No trained anatomical landmark model" in status["message"]
