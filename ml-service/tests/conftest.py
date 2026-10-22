"""Shared pytest fixtures for the ML service.

The fixtures generate *synthetic* palm-like images.  No real biometric
samples are used anywhere in the test suite, and no test downloads a dataset
from the internet.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

# The application modules read their configuration at import time, so the
# environment has to be prepared before ``app`` is imported anywhere.
_TEST_ARTIFACT_DIR = Path(tempfile.gettempdir()) / "palmprint-ml-test-artifacts"
os.environ.setdefault("ML_ARTIFACT_DIR", str(_TEST_ARTIFACT_DIR))
os.environ.setdefault("ML_LOG_LEVEL", "WARNING")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


def make_synthetic_palm(
    width: int = 320,
    height: int = 320,
    *,
    seed: int = 7,
    blur: bool = False,
    brightness: float = 1.0,
) -> np.ndarray:
    """Create a synthetic palm-like image.

    The image contains an elliptical "palm" with a sinusoidal ridge-like
    texture on a dark background.  It is *not* a real palmprint - it only
    provides structure that the classical algorithms can react to.
    """
    rng = np.random.default_rng(seed)
    background = np.full((height, width, 3), 28, dtype=np.uint8)
    background = np.clip(background + rng.normal(0, 6, (height, width, 3)), 0, 255).astype(np.uint8)

    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    cx, cy = width / 2.0, height / 2.0
    radius_x, radius_y = width * 0.36, height * 0.42
    ellipse = ((xx - cx) / radius_x) ** 2 + ((yy - cy) / radius_y) ** 2

    palm_mask = (ellipse <= 1.0).astype(np.uint8)
    palm_mask = cv2.GaussianBlur(palm_mask * 255, (9, 9), 0).astype(np.uint8) / 255.0

    orientation = np.arctan2(yy - cy, xx - cx)
    radial = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    ridges = 0.5 + 0.5 * np.sin(radial * 1.35 + orientation * 0.7)
    texture = 120 + 55 * ridges + rng.normal(0, 6, (height, width))

    palm = np.stack([texture, texture * 0.92, texture * 0.84], axis=-1)
    palm = np.clip(palm * brightness, 0, 255).astype(np.uint8)

    alpha = palm_mask[..., None]
    image = (palm * alpha + background * (1.0 - alpha)).astype(np.uint8)

    if blur:
        image = cv2.GaussianBlur(image, (9, 9), 3.0)
    return image


@pytest.fixture(scope="session")
def synthetic_palm() -> np.ndarray:
    return make_synthetic_palm()


@pytest.fixture(scope="session")
def synthetic_palm_b() -> np.ndarray:
    return make_synthetic_palm(seed=11, brightness=0.9)


@pytest.fixture(scope="session")
def synthetic_blurred_palm() -> np.ndarray:
    return make_synthetic_palm(blur=True)


@pytest.fixture(scope="session")
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def encode_png(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return buffer.tobytes()
