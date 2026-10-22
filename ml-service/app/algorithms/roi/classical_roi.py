"""Classical (non-learned) palm-region candidate extraction.

Method
------
1. Convert to grayscale and suppress sensor noise with a median filter.
2. Segment the bright palm region against a darker background using Otsu's
   threshold.  Both polarity hypotheses are evaluated and the one that
   yields the larger, more central foreground component is selected.
3. Morphological closing removes small holes, opening removes speckle.
4. The largest external contour is approximated with ``approxPolyDP``; the
   bounding rectangle of the approximation (or of the contour when the
   approximation degenerates) defines the crop.
5. If no convincing component is found the central 60% of the frame is used
   as a fallback and the result is flagged as low confidence.

Honesty statement
-----------------
This is **not** an anatomical palm detector.  It is a classical baseline that
finds a dominant bright region.  It works for the common "palm on a dark
background" capture condition and fails on cluttered, low contrast or
low-light contact-less captures.  Every response produced by this module is
marked ``is_approximate = True`` and carries warnings.
"""

from __future__ import annotations

import cv2
import numpy as np

from ...utils.errors import AlgorithmError
from ...utils.image_io import to_bgr, to_gray
from .base import ROIAlgorithm, ROIResult


class ClassicalROIAlgorithm(ROIAlgorithm):
    """Contour based palm-region candidate extraction."""

    name = "classical_contour_roi"
    version = "1.1.0"
    anatomical = False
    description = (
        "Otsu segmentation of the bright foreground, morphological cleanup and "
        "bounding rectangle of the dominant contour."
    )
    limitations = (
        "Approximate region proposal, not anatomical palm localisation.",
        "Assumes the palm is brighter than the surrounding background.",
        "Sensitive to shadows, cluttered backgrounds and motion blur.",
        "No palmprint-specific detector or trained weights are involved.",
    )

    def __init__(
        self,
        *,
        median_ksize: int = 5,
        morph_kernel: int = 7,
        min_area_ratio: float = 0.04,
        padding_ratio: float = 0.02,
        fallback_ratio: float = 0.6,
    ) -> None:
        self.median_ksize = median_ksize | 1
        self.morph_kernel = morph_kernel | 1
        self.min_area_ratio = min_area_ratio
        self.padding_ratio = padding_ratio
        self.fallback_ratio = fallback_ratio

    def extract(self, image: np.ndarray) -> ROIResult:
        if image is None or image.size == 0:
            raise AlgorithmError("Cannot extract an ROI from an empty image.")

        height, width = image.shape[:2]
        gray = to_gray(image)
        gray = cv2.medianBlur(gray, self.median_ksize)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        if float(gray.std()) < 1.0:
            # A (near) constant image carries no separable foreground.
            bbox = self._central_crop(width, height, self.fallback_ratio)
            return ROIResult(
                image=to_bgr(image)[bbox[1] : bbox[1] + bbox[3], bbox[0] : bbox[0] + bbox[2]],
                bbox=bbox,
                method=self.name,
                confidence=0.1,
                is_approximate=True,
                warnings=[
                    "The image is (almost) uniform, so no palm region could be "
                    "segmented; a central crop fallback was used.",
                ],
                metrics={
                    "image_width": int(width),
                    "image_height": int(height),
                    "bbox_x": int(bbox[0]),
                    "bbox_y": int(bbox[1]),
                    "bbox_width": int(bbox[2]),
                    "bbox_height": int(bbox[3]),
                    "coverage_ratio": round(float((bbox[2] * bbox[3]) / float(width * height)), 4),
                },
            )

        best: tuple[np.ndarray, float, float] | None = None
        for invert in (False, True):
            mask = self._segment(gray, invert=invert)
            contour, area = self._largest_contour(mask)
            if contour is None:
                continue
            score = area / float(height * width)
            centrality = self._centrality(contour, width, height)
            weighted = score * (0.6 + 0.4 * centrality)
            if best is None or weighted > best[2]:
                best = (mask, score, weighted)

        warnings: list[str] = []
        metrics: dict[str, float | int | bool] = {
            "image_width": int(width),
            "image_height": int(height),
        }

        if best is None:
            bbox = self._central_crop(width, height, self.fallback_ratio)
            confidence = 0.1
            warnings.append(
                "No dominant foreground region could be segmented; a central crop "
                "fallback was used. Treat the region as unreliable."
            )
        else:
            mask, area_ratio, _ = best
            contour, area = self._largest_contour(mask)
            if contour is None:
                bbox = self._central_crop(width, height, self.fallback_ratio)
                confidence = 0.1
                warnings.append(
                    "Segmentation produced no usable contour; central crop fallback used."
                )
            else:
                bbox = self._bbox_from_contour(contour, width, height)
                confidence = self._confidence(area_ratio, bbox, width, height)
                if area_ratio < self.min_area_ratio:
                    warnings.append(
                        f"The segmented region covers only {area_ratio * 100:.1f}% of the frame; "
                        "the extracted region may be too small to be a palm."
                    )
                if bbox[2] < 32 or bbox[3] < 32:
                    warnings.append(
                        "The extracted region is very small and may not contain "
                        "usable ridge detail."
                    )

        x, y, w, h = bbox
        x, y = max(0, x), max(0, y)
        w = min(w, width - x)
        h = min(h, height - y)
        if w < 8 or h < 8:
            raise AlgorithmError(
                "The extracted region of interest is degenerate; the source image "
                "is probably too small or too uniform."
            )

        crop = to_bgr(image)[y : y + h, x : x + w]
        metrics.update(
            {
                "bbox_x": int(x),
                "bbox_y": int(y),
                "bbox_width": int(w),
                "bbox_height": int(h),
                "coverage_ratio": round(float((w * h) / float(width * height)), 4),
            }
        )

        return ROIResult(
            image=crop,
            bbox=(int(x), int(y), int(w), int(h)),
            method=self.name,
            confidence=confidence,
            is_approximate=True,
            warnings=warnings,
            metrics=metrics,
        )

    # -- internals ------------------------------------------------------
    def _segment(self, gray: np.ndarray, *, invert: bool) -> np.ndarray:
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if invert:
            otsu = cv2.bitwise_not(otsu)
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (self.morph_kernel, self.morph_kernel)
        )
        closed = cv2.morphologyEx(otsu, cv2.MORPH_CLOSE, kernel)
        return cv2.morphologyEx(closed, cv2.MORPH_OPEN, kernel)

    @staticmethod
    def _largest_contour(mask: np.ndarray) -> tuple[np.ndarray | None, float]:
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return None, 0.0
        contour = max(contours, key=cv2.contourArea)
        return contour, float(cv2.contourArea(contour))

    @staticmethod
    def _centrality(contour: np.ndarray, width: int, height: int) -> float:
        moments = cv2.moments(contour)
        if moments["m00"] == 0:
            return 0.0
        cx = moments["m10"] / moments["m00"]
        cy = moments["m01"] / moments["m00"]
        dx = abs(cx - width / 2.0) / max(width / 2.0, 1.0)
        dy = abs(cy - height / 2.0) / max(height / 2.0, 1.0)
        return max(0.0, 1.0 - float(np.sqrt(dx * dx + dy * dy)))

    @staticmethod
    def _bbox_from_contour(
        contour: np.ndarray, width: int, height: int
    ) -> tuple[int, int, int, int]:
        perimeter = cv2.arcLength(contour, True)
        epsilon = 0.02 * perimeter
        approx = cv2.approxPolyDP(contour, epsilon, True)
        if len(approx) >= 4:
            x, y, w, h = cv2.boundingRect(approx)
        else:
            x, y, w, h = cv2.boundingRect(contour)
        pad_x = int(w * 0.02)
        pad_y = int(h * 0.02)
        x = max(0, x - pad_x)
        y = max(0, y - pad_y)
        w = min(w + 2 * pad_x, width - x)
        h = min(h + 2 * pad_y, height - y)
        return int(x), int(y), int(w), int(h)

    @staticmethod
    def _central_crop(width: int, height: int, ratio: float) -> tuple[int, int, int, int]:
        w = max(8, int(width * ratio))
        h = max(8, int(height * ratio))
        x = max(0, (width - w) // 2)
        y = max(0, (height - h) // 2)
        return int(x), int(y), int(w), int(h)

    @staticmethod
    def _confidence(
        area_ratio: float, bbox: tuple[int, int, int, int], width: int, height: int
    ) -> float:
        coverage = (bbox[2] * bbox[3]) / float(max(width * height, 1))
        area_term = min(1.0, area_ratio / 0.35)
        coverage_term = 1.0 - abs(coverage - 0.45) / 0.55
        return float(
            round(max(0.05, min(0.95, 0.55 * area_term + 0.45 * max(0.0, coverage_term))), 3)
        )
