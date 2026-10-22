"""Image decoding and validation tests."""

from __future__ import annotations

import io

import cv2
import numpy as np
import pytest
from PIL import Image

from app.utils.errors import InvalidImageError, PayloadTooLargeError, UnsupportedMediaTypeError
from app.utils.image_io import decode_image, encode_png, sniff_media_type, to_bgr, to_gray
from app.utils.validation import validate_payload
from tests.conftest import make_synthetic_palm

LIMITS = {"max_bytes": 5_000_000, "max_pixels": 40_000_000, "max_dimension": 6000}


def test_decode_png_returns_dimensions() -> None:
    image = make_synthetic_palm(64, 48)
    decoded = decode_image(encode_png(image), **LIMITS)
    assert decoded.width == 64
    assert decoded.height == 48
    assert decoded.original_format == "PNG"
    assert decoded.media_type == "image/png"


def test_decode_rejects_empty_payload() -> None:
    with pytest.raises(InvalidImageError):
        decode_image(b"", **LIMITS)


def test_decode_rejects_non_image_payload() -> None:
    with pytest.raises(InvalidImageError):
        decode_image(b"this is definitely not an image", **LIMITS)


def test_decode_rejects_truncated_image() -> None:
    payload = encode_png(make_synthetic_palm(64, 64))
    with pytest.raises(InvalidImageError):
        decode_image(payload[: len(payload) // 3], **LIMITS)


def test_decode_enforces_size_limit() -> None:
    payload = encode_png(make_synthetic_palm(64, 64))
    with pytest.raises(PayloadTooLargeError):
        decode_image(payload, max_bytes=100, max_pixels=40_000_000, max_dimension=6000)


def test_decode_enforces_pixel_limit() -> None:
    payload = encode_png(make_synthetic_palm(200, 200))
    with pytest.raises(PayloadTooLargeError):
        decode_image(payload, max_bytes=5_000_000, max_pixels=100, max_dimension=6000)


def test_decode_enforces_dimension_limit() -> None:
    payload = encode_png(make_synthetic_palm(120, 120))
    with pytest.raises(PayloadTooLargeError):
        decode_image(payload, max_bytes=5_000_000, max_pixels=40_000_000, max_dimension=32)


def test_sniff_media_type_ignores_extension() -> None:
    payload = encode_png(make_synthetic_palm(32, 32))
    assert sniff_media_type(payload) == "image/png"


def test_validation_detects_mismatched_extension() -> None:
    payload = encode_png(make_synthetic_palm(32, 32))
    _, report = validate_payload(
        payload, filename="capture.jpg", declared_content_type="image/jpeg", **LIMITS
    )
    assert report.detected_media_type == "image/png"
    assert report.extension_matches is False
    assert any("extension" in warning.lower() for warning in report.warnings)


def test_validation_rejects_unsupported_media_type() -> None:
    with pytest.raises(UnsupportedMediaTypeError):
        validate_payload(b"GIF89a" + b"0" * 100, filename="x.gif", **LIMITS)


def test_validation_accepts_valid_png() -> None:
    payload = encode_png(make_synthetic_palm(48, 48))
    decoded, report = validate_payload(
        payload, filename="palm.png", declared_content_type="image/png", **LIMITS
    )
    assert report.detected_format == "PNG"
    assert report.width == 48
    assert report.pixel_count == 48 * 48
    assert decoded.image.shape[2] == 3


def test_validation_accepts_grayscale_png() -> None:
    gray = np.full((32, 32), 120, dtype=np.uint8)
    ok, buffer = cv2.imencode(".png", gray)
    assert ok
    decoded, report = validate_payload(buffer.tobytes(), filename="gray.png", **LIMITS)
    assert report.channels == 1
    assert to_bgr(decoded.image).shape[2] == 3
    assert to_gray(decoded.image).ndim == 2


def test_validation_accepts_jpeg() -> None:
    payload = encode_png(make_synthetic_palm(64, 64))
    pil_image = Image.open(io.BytesIO(payload)).convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG")
    _, report = validate_payload(buffer.getvalue(), filename="palm.jpg", **LIMITS)
    assert report.detected_format == "JPEG"
    assert report.detected_media_type == "image/jpeg"
