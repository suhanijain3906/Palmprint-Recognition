"""Interface definition for ROI extraction algorithms.

Any algorithm implementing this interface can be plugged into the pipeline.
The pipeline only relies on :meth:`ROIAlgorithm.extract`, so adding a learned
palm detector later does not require changing the API layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class ROIResult:
    """Outcome of a region-of-interest extraction."""

    image: np.ndarray
    bbox: tuple[int, int, int, int]
    method: str
    confidence: float
    is_approximate: bool = True
    warnings: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    @property
    def x(self) -> int:
        return self.bbox[0]

    @property
    def y(self) -> int:
        return self.bbox[1]

    @property
    def width(self) -> int:
        return self.bbox[2]

    @property
    def height(self) -> int:
        return self.bbox[3]


class ROIAlgorithm(ABC):
    """Abstract base class for all ROI extraction algorithms."""

    #: Stable identifier reported in API responses.
    name: str = "abstract_roi"
    #: Version of the concrete implementation.
    version: str = "0.0.0"
    #: Whether the algorithm performs anatomical palm localisation.
    anatomical: bool = False
    #: Human readable description of the method.
    description: str = ""
    #: Known limitations surfaced to the caller.
    limitations: tuple[str, ...] = ()

    @abstractmethod
    def extract(self, image: np.ndarray) -> ROIResult:
        """Extract the region of interest from ``image`` (BGR, uint8)."""

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "anatomical": self.anatomical,
            "description": self.description,
            "limitations": list(self.limitations),
        }
