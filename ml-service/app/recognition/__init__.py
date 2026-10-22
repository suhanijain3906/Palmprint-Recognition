"""Recognition / comparison matchers."""

from .base import BiometricMatcher, RecognitionResult
from .classical_matcher import ClassicalMatcher
from .model_loader import (
    TrainedModelAdapter,
    TrainedModelStatus,
    discover_models,
    get_trained_model,
    register_trained_model,
)

__all__ = [
    "BiometricMatcher",
    "ClassicalMatcher",
    "RecognitionResult",
    "TrainedModelAdapter",
    "TrainedModelStatus",
    "discover_models",
    "get_trained_model",
    "register_trained_model",
]
