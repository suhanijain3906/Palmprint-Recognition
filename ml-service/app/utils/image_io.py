"""Safe image decoding and encoding helpers.

Design notes
------------
* Payloads are decoded from memory with ``cv2.imdecode`` so that the service
  never touches the file system with untrusted names.
* ``cv2.imdecode`` is permissive: truncated or malicious files can still
  decode partially.  Every decoded image is therefore validated for size,
  channel count and dimensional sanity.
* ``PIL`` is used as a second opinion decoder for the *same* bytes; if PIL
  raises, the image is treated as corrupted.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

from .errors import InvalidImageError, PayloadTooLargeError

#: Magic byte prefixes used to sniff the real container of a payload.
_MAGIC_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"BM", "image/bmp"),
    (b"II*\x00", "image/tiff"),
    (b"MM\x00*", "image/tiff"),
    (b"RIFF", "image/webp"),
)

#: Extensions mapped to the media type they are allowed to represent.
_EXTENSION_MEDIA_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".jpe": "image/jpeg",
    ".bmp": "image/bmp",
    ".tif": "image/tiff",
    ".tiff": "image/tiff",
    ".webp": "image/webp",
}


@dataclass(frozen=True)
class DecodedImage:
    """A decoded image plus the metadata that is safe to expose."""

    image: np.ndarray
    media_type: str
    original_format: str
    width: int
    height: int
    channels: int

    @property
    def is_color(self) -> bool:
        return self.channels == 3


def sniff_media_type(data: bytes) -> str | None:
    """Return the media type implied by the payload magic bytes."""
    for signature, media_type in _MAGIC_SIGNATURES:
        if data.startswith(signature):
            return media_type
    return None


def extension_media_type(filename: str | None) -> str | None:
    """Return the media type implied by a filename extension (untrusted)."""
    if not filename:
        return None
    lowered = filename.lower()
    for extension, media_type in _EXTENSION_MEDIA_TYPES.items():
        if lowered.endswith(extension):
            return media_type
    return None


def decode_image(
    data: bytes,
    *,
    max_bytes: int,
    max_pixels: int,
    max_dimension: int,
) -> DecodedImage:
    """Decode and validate an image payload.

    Raises
    ------
    PayloadTooLargeError
        The payload is larger than ``max_bytes``.
    InvalidImageError
        The payload is empty, corrupted or not a supported raster image.
    """
    if not data:
        raise InvalidImageError("The uploaded file is empty.")
    if len(data) > max_bytes:
        raise PayloadTooLargeError(
            f"Upload exceeds the configured limit of {max_bytes} bytes.",
            details={"size_bytes": len(data), "max_bytes": max_bytes},
        )

    media_type = sniff_media_type(data)
    if media_type is None:
        raise InvalidImageError(
            "The payload is not a supported raster image "
            "(PNG, JPEG, BMP, TIFF or WebP were expected).",
            details={"detected": "unknown"},
        )

    # Second opinion decoder: PIL is stricter about truncated payloads.
    try:
        with Image.open(io.BytesIO(data)) as probe:
            probe.verify()
        with Image.open(io.BytesIO(data)) as probe:
            detected_format = (probe.format or "UNKNOWN").upper()
            width, height = probe.size
    except UnidentifiedImageError as exc:
        raise InvalidImageError(
            "The payload could not be identified as an image.", details={"reason": str(exc)}
        ) from exc
    except OSError as exc:
        raise InvalidImageError(
            "The image file appears to be corrupted or truncated.", details={"reason": str(exc)}
        ) from exc

    if width <= 0 or height <= 0:
        raise InvalidImageError("The image reports non-positive dimensions.")

    if width > max_dimension or height > max_dimension:
        raise PayloadTooLargeError(
            f"Image dimension {width}x{height} exceeds the limit of {max_dimension} pixels.",
            details={"width": width, "height": height, "max_dimension": max_dimension},
        )

    if width * height > max_pixels:
        raise PayloadTooLargeError(
            f"Image has {width * height} pixels which exceeds the limit of {max_pixels}.",
            details={"width": width, "height": height, "max_pixels": max_pixels},
        )

    buffer = np.frombuffer(data, dtype=np.uint8)
    decoded = cv2.imdecode(buffer, cv2.IMREAD_UNCHANGED)
    if decoded is None:
        raise InvalidImageError(
            "The image could not be decoded by the OpenCV backend.",
            details={"detected_format": detected_format},
        )

    if decoded.dtype != np.uint8:
        raise InvalidImageError(
            f"Unsupported pixel depth '{decoded.dtype}'. Only 8-bit images are supported.",
            details={"dtype": str(decoded.dtype)},
        )

    channels = 1 if decoded.ndim == 2 else decoded.shape[2]
    if channels not in (1, 3, 4):
        raise InvalidImageError(
            f"Unsupported channel count {channels} for image '{detected_format}'.",
            details={"channels": channels},
        )

    return DecodedImage(
        image=decoded,
        media_type=media_type,
        original_format=detected_format,
        width=int(decoded.shape[1]),
        height=int(decoded.shape[0]),
        channels=int(channels),
    )


def to_bgr(image: np.ndarray) -> np.ndarray:
    """Return an 8-bit three channel BGR image regardless of the input layout."""
    if image.ndim == 2:
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    return image


def to_gray(image: np.ndarray) -> np.ndarray:
    """Return a single channel 8-bit grayscale image."""
    if image.ndim == 2:
        return image
    if image.shape[2] == 4:
        return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def encode_png(image: np.ndarray) -> bytes:
    """Encode an image as PNG bytes."""
    ok, buffer = cv2.imencode(".png", image)
    if not ok:
        raise InvalidImageError("The result image could not be encoded as PNG.")
    return buffer.tobytes()


def resize_to_fit(
    image: np.ndarray,
    *,
    max_dimension: int,
    interpolation: int | None = None,
) -> np.ndarray:
    """Downscale an image so that neither side exceeds ``max_dimension``."""
    height, width = image.shape[:2]
    longest = max(height, width)
    if longest <= max_dimension:
        return image
    scale = max_dimension / float(longest)
    new_size = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    if interpolation is None:
        interpolation = cv2.INTER_AREA
    return cv2.resize(image, new_size, interpolation=interpolation)
