"""Tests for the enhancement algorithms and pipeline."""

from __future__ import annotations

import numpy as np
import pytest

from app.algorithms.enhancement import clahe, filtering, histogram_equalization
from app.pipelines.enhancement_pipeline import apply_enhancement
from app.utils.errors import AlgorithmError


def test_clahe_returns_same_shape(synthetic_palm: np.ndarray) -> None:
    result = clahe.apply_clahe(synthetic_palm, clip_limit=2.0, tile_grid_size=8)
    assert result.shape == synthetic_palm.shape
    assert result.dtype == np.uint8


def test_clahe_increases_local_contrast(synthetic_palm: np.ndarray) -> None:
    result = clahe.apply_clahe(synthetic_palm, clip_limit=4.0, tile_grid_size=8)
    assert result.std() >= synthetic_palm.std()


def test_histogram_equalization_returns_same_shape(synthetic_palm: np.ndarray) -> None:
    result = histogram_equalization.equalize_histogram(synthetic_palm)
    assert result.shape == synthetic_palm.shape
    assert result.dtype == np.uint8


def test_histogram_equalization_rejects_invalid_color_space(synthetic_palm: np.ndarray) -> None:
    with pytest.raises(ValueError):
        histogram_equalization.equalize_histogram(synthetic_palm, color_space="hsv")


def test_filters_return_same_shape(synthetic_palm: np.ndarray) -> None:
    for result in (
        filtering.median_filter(synthetic_palm, kernel_size=5),
        filtering.gaussian_filter(synthetic_palm, kernel_size=5),
        filtering.bilateral_filter(synthetic_palm),
        filtering.unsharp_mask(synthetic_palm, amount=1.0),
    ):
        assert result.shape == synthetic_palm.shape
        assert result.dtype == np.uint8


def test_enhancement_pipeline_reports_parameters(synthetic_palm: np.ndarray) -> None:
    outcome = apply_enhancement(synthetic_palm, algorithm="clahe", parameters={"clip_limit": 3.0})
    assert outcome.algorithm == "clahe"
    assert outcome.parameters["clip_limit"] == 3.0
    assert outcome.parameters["tile_grid_size"] == 8
    assert outcome.metadata()["output_width"] == synthetic_palm.shape[1]


def test_enhancement_pipeline_does_not_modify_the_source(synthetic_palm: np.ndarray) -> None:
    original = synthetic_palm.copy()
    apply_enhancement(synthetic_palm, algorithm="clahe")
    assert np.array_equal(original, synthetic_palm)


def test_enhancement_pipeline_rejects_unknown_algorithm(synthetic_palm: np.ndarray) -> None:
    with pytest.raises(AlgorithmError):
        apply_enhancement(synthetic_palm, algorithm="magic")


def test_enhancement_pipeline_validates_parameters(synthetic_palm: np.ndarray) -> None:
    with pytest.raises(AlgorithmError):
        apply_enhancement(synthetic_palm, algorithm="clahe", parameters={"clip_limit": -1})
    with pytest.raises(AlgorithmError):
        apply_enhancement(synthetic_palm, algorithm="clahe", parameters={"tile_grid_size": 99})


def test_enhancement_pipeline_supports_filtering(synthetic_palm: np.ndarray) -> None:
    outcome = apply_enhancement(
        synthetic_palm, algorithm="filtering", parameters={"filter": "sharpen", "amount": 1.5}
    )
    assert outcome.parameters["filter"] == "sharpen"
    assert outcome.parameters["amount"] == 1.5
    assert outcome.image.size > 0
