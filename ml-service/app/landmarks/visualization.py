"""Rendering of feature point overlays."""

from __future__ import annotations

import cv2
import numpy as np

from ..utils.image_io import to_bgr
from .detector import LandmarkResult

ACCENT = (140, 90, 20)  # BGR teal-ish accent used for the overlay


def draw_landmarks(
    image: np.ndarray,
    landmarks: LandmarkResult,
    *,
    max_labels: int = 25,
    radius: int = 4,
) -> np.ndarray:
    """Draw the detected feature points and (optionally) their coordinates."""
    canvas = to_bgr(image).copy()
    if landmarks.count == 0:
        return canvas

    for index, (x, y) in enumerate(landmarks.points):
        cv2.circle(canvas, (int(round(x)), int(round(y))), max(2, radius), ACCENT, 1, cv2.LINE_AA)
        if index < max_labels:
            cv2.putText(
                canvas,
                f"{int(round(x))},{int(round(y))}",
                (int(round(x)) + 5, int(round(y)) - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35,
                (40, 40, 40),
                1,
                cv2.LINE_AA,
            )

    caption = f"{landmarks.count} {landmarks.kind.replace('_', ' ')}s - {landmarks.method}"
    cv2.rectangle(canvas, (0, 0), (canvas.shape[1], 22), (255, 255, 255), -1)
    cv2.putText(
        canvas,
        caption,
        (6, 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (60, 60, 60),
        1,
        cv2.LINE_AA,
    )
    return canvas


__all__ = ["ACCENT", "draw_landmarks"]
