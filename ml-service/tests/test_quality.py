"""Tests for the quality assessment algorithms."""

from __future__ import annotations

import numpy as np

from app.algorithms.quality import (
    brightness_metrics,
    contrast_metrics,
    is_blurry,
    quality_report,
    sharpness_metrics,
)
from tests.conftest import make_synthetic_palm


def test_brightness_metrics_on_dark_image() -> None:
    image = np.full((64, 64, 3), 5, dtype=np.uint8)
    metrics = brightness_metrics(image)
    assert metrics["mean_intensity"] == 5.0
    assert metrics["under_exposed_percent"] == 100.0


def test_brightness_metrics_on_bright_image() -> None:
    image = np.full((64, 64, 3), 250, dtype=np.uint8)
    metrics = brightness_metrics(image)
    assert metrics["over_exposed_percent"] == 100.0


def test_contrast_metrics_detect_flat_image() -> None:
    image = np.full((64, 64, 3), 128, dtype=np.uint8)
    metrics = contrast_metrics(image)
    assert metrics["rms_contrast"] == 0.0
    assert metrics["entropy_bits"] == 0.0


def test_sharpness_metrics_are_higher_for_sharp_images() -> None:
    sharp = make_synthetic_palm(200, 200, blur=False)
    blurred = make_synthetic_palm(200, 200, blur=True)
    assert (
        sharpness_metrics(sharp)["variance_of_laplacian"]
        > sharpness_metrics(blurred)["variance_of_laplacian"]
    )


def test_is_blurry_detects_blur() -> None:
    blurred = make_synthetic_palm(200, 200, blur=True)
    assert is_blurry(blurred, threshold=100.0) is True


def test_quality_report_structure(synthetic_palm: np.ndarray) -> None:
    report = quality_report(synthetic_palm)
    assert set(report["sub_scores"]) == {"exposure", "contrast", "sharpness", "resolution"}
    assert 0.0 <= report["combined_score"] <= 100.0
    assert report["combined_score_is_experimental"] is True
    assert report["limitations"]
    assert report["dimensions"]["width"] == synthetic_palm.shape[1]


def test_quality_report_flags_low_resolution() -> None:
    tiny = make_synthetic_palm(32, 32)
    report = quality_report(tiny)
    assert any("megapixel" in warning for warning in report["warnings"])
