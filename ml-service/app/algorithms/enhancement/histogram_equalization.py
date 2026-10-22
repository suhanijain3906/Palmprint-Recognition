"""Global histogram equalisation.

Classic single-histogram equalisation applied per colour channel group.
It maximises global contrast but is sensitive to noise and can amplify
background illumination differences.  ``clip_limit``-limited variants live in
:mod:`app.algorithms.enhancement.clahe`.
"""

from __future__ import annotations

import cv2
import numpy as np

from ...utils.image_io import to_bgr

ALGORITHM_NAME = "histogram_equalization"
ALGORITHM_VERSION = "1.0.0"

LIMITATIONS = (
    "Global statistics only: local illumination gradients are not corrected.",
    "Noise in flat regions is amplified because the histogram is stretched.",
    "Colour images are equalised in LAB space to avoid hue shifts.",
)


def equalize_histogram(image: np.ndarray, *, color_space: str = "lab") -> np.ndarray:
    """Apply histogram equalisation and return a BGR uint8 image."""
    if image is None or image.size == 0:
        raise ValueError("Cannot enhance an empty image.")

    color_space = (color_space or "lab").lower()
    if color_space not in {"lab", "per_channel"}:
        raise ValueError("color_space must be either 'lab' or 'per_channel'.")

    source = to_bgr(image)

    if source.shape[2] == 3 and color_space == "lab":
        lab = cv2.cvtColor(source, cv2.COLOR_BGR2LAB)
        lab[:, :, 0] = cv2.equalizeHist(lab[:, :, 0])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    if source.shape[2] == 3:
        channels = [cv2.equalizeHist(channel) for channel in cv2.split(source)]
        return cv2.merge(channels)

    return cv2.equalizeHist(source)


def describe() -> dict[str, object]:
    return {
        "name": ALGORITHM_NAME,
        "version": ALGORITHM_VERSION,
        "parameters": {
            "color_space": {
                "type": "enum",
                "values": ["lab", "per_channel"],
                "default": "lab",
                "description": "Colour space used for equalisation.",
            }
        },
        "limitations": list(LIMITATIONS),
    }
