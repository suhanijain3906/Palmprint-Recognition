"""Tests for the image comparison pipeline."""

from __future__ import annotations

import numpy as np

from app.pipelines.comparison_pipeline import compare_images, compute_psnr, compute_ssim
from tests.conftest import make_synthetic_palm


def test_identical_images_have_maximal_psnr(synthetic_palm: np.ndarray) -> None:
    psnr = compute_psnr(synthetic_palm, synthetic_palm)
    assert psnr == float("inf")


def test_identical_images_have_ssim_of_one(synthetic_palm: np.ndarray) -> None:
    assert compute_ssim(synthetic_palm, synthetic_palm) == 1.0


def test_different_images_have_lower_ssim(synthetic_palm: np.ndarray) -> None:
    other = make_synthetic_palm(320, 320, seed=42)
    assert compute_ssim(synthetic_palm, other) < 1.0


def test_comparison_resizes_and_warns(synthetic_palm: np.ndarray) -> None:
    smaller = make_synthetic_palm(160, 160)
    outcome = compare_images(synthetic_palm, smaller)
    assert outcome.resized is True
    assert outcome.aligned is False
    assert any("different dimensions" in warning for warning in outcome.warnings)
    assert outcome.difference_image.shape == synthetic_palm.shape


def test_comparison_of_aligned_images(synthetic_palm: np.ndarray) -> None:
    outcome = compare_images(synthetic_palm, synthetic_palm)
    assert outcome.resized is False
    assert outcome.ssim == 1.0
    assert outcome.metrics["difference_max"] == 0
    assert outcome.limitations


def test_difference_image_shape(synthetic_palm: np.ndarray) -> None:
    other = make_synthetic_palm(320, 320, seed=5)
    outcome = compare_images(synthetic_palm, other)
    assert outcome.difference_image.shape == synthetic_palm.shape
    assert outcome.difference_image.dtype == np.uint8
