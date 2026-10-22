"""Interface for biometric matchers.

The platform deliberately separates two very different things:

``ExperimentalMatcher``
    A classical, untrained comparison pipeline.  It produces a *similarity
    score* that is useful for exploring data, but it is **not** a calibrated
    probability of identity and it is **not** a trained biometric model.

``TrainedMatcher``
    The extension point for a real research model (CNN, Siamese network,
    contrastive palmprint encoder, ...).  A trained matcher is only available
    when actual weights are present in the configured model directory and a
    matching inference implementation exists.

No accuracy, confidence or identity claim is ever produced without a trained
model that is present in the deployment.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass
class RecognitionResult:
    """Outcome of comparing two palmprint images."""

    similarity_score: float | None
    score_kind: str
    available: bool
    matcher_name: str
    matcher_version: str
    is_trained_model: bool = False
    is_calibrated_probability: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    def summary(self) -> dict[str, Any]:
        return {
            "similarity_score": self.similarity_score,
            "score_kind": self.score_kind,
            "available": self.available,
            "matcher": {
                "name": self.matcher_name,
                "version": self.matcher_version,
                "is_trained_model": self.is_trained_model,
            },
            "is_calibrated_probability": self.is_calibrated_probability,
            "details": self.details,
            "warnings": list(self.warnings),
            "limitations": list(self.limitations),
        }


class BiometricMatcher(ABC):
    """Abstract matcher interface."""

    name: str = "abstract_matcher"
    version: str = "0.0.0"
    is_trained_model: bool = False

    @property
    @abstractmethod
    def available(self) -> bool:
        """Whether the matcher can currently produce a result."""

    @abstractmethod
    def compare(self, image_a: np.ndarray, image_b: np.ndarray) -> RecognitionResult:
        """Compare two palmprint images."""

    def info(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "available": self.available,
            "is_trained_model": self.is_trained_model,
        }


__all__ = ["BiometricMatcher", "RecognitionResult"]
