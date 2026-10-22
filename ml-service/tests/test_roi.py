"""Tests for the classical ROI extraction pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from app.algorithms.roi import ClassicalROIAlgorithm, get_roi_algorithm
from app.pipelines.roi_pipeline import extract_roi
from app.utils.errors import AlgorithmError
from tests.conftest import make_synthetic_palm


def test_roi_result_is_a_valid_image(synthetic_palm: np.ndarray) -> None:
    result = ClassicalROIAlgorithm().extract(synthetic_palm)
    assert result.image.size > 0
    assert result.image.shape[0] > 8 and result.image.shape[1] > 8
    assert result.image.dtype == np.uint8


def test_roi_bbox_is_inside_the_source(synthetic_palm: np.ndarray) -> None:
    result = ClassicalROIAlgorithm().extract(synthetic_palm)
    x, y, width, height = result.bbox
    assert 0 <= x < synthetic_palm.shape[1]
    assert 0 <= y < synthetic_palm.shape[0]
    assert x + width <= synthetic_palm.shape[1]
    assert y + height <= synthetic_palm.shape[0]


def test_roi_is_flagged_as_approximate(synthetic_palm: np.ndarray) -> None:
    result = ClassicalROIAlgorithm().extract(synthetic_palm)
    assert result.is_approximate is True
    assert ClassicalROIAlgorithm.anatomical is False


def test_roi_on_uniform_image_falls_back() -> None:
    flat = np.full((200, 200, 3), 128, dtype=np.uint8)
    result = ClassicalROIAlgorithm().extract(flat)
    assert result.image.size > 0
    assert result.confidence <= 0.5
    assert result.warnings


def test_roi_pipeline_rejects_unknown_algorithm(synthetic_palm: np.ndarray) -> None:
    with pytest.raises(AlgorithmError):
        extract_roi(synthetic_palm, algorithm="does_not_exist")


def test_roi_pipeline_passes_parameters(synthetic_palm: np.ndarray) -> None:
    result = extract_roi(
        synthetic_palm, algorithm="classical_contour_roi", parameters={"median_ksize": 3}
    )
    assert result.metrics["parameters"]["median_ksize"] == 3


def test_get_roi_algorithm_returns_default() -> None:
    algorithm = get_roi_algorithm(None)
    assert algorithm.name == "classical_contour_roi"


def test_roi_of_small_bright_object(synthetic_palm: np.ndarray) -> None:
    # A palm that fills most of the frame must not be cropped away entirely.
    result = ClassicalROIAlgorithm().extract(make_synthetic_palm(300, 300))
    assert result.image.shape[0] >= 32
    assert result.image.shape[1] >= 32
