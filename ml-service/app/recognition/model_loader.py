"""Discovery and loading of trained models.

The repository intentionally ships **without** trained weights.  A palmprint
recognition model has to be trained by the researcher on an authorised
dataset; pretending otherwise would misrepresent the platform.

This module therefore does two things:

1. It scans the configured model directory and reports exactly what is
   installed (``weights_present``, file names, sizes).
2. It exposes :class:`TrainedModelAdapter`, the extension point where a
   researcher plugs in a real inference implementation.  Until a concrete
   implementation is registered, the adapter reports
   ``available = False`` and the API answers with an explicit
   "trained model unavailable" payload instead of a fabricated score.

Registering a model
-------------------
.. code-block:: python

    from app.recognition.model_loader import register_trained_model

    @register_trained_model("my_palmprint_cnn")
    class MyModel(TrainedModelAdapter):
        version = "1.0.0"

        def load(self) -> None:
            self._net = torch.load(self.weights_path)  # your own loader

        def embed(self, image):
            return self._net.encode(image)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

#: Registry of trained model implementations keyed by a public model name.
_TRAINED_MODELS: dict[str, type[TrainedModelAdapter]] = {}

#: File extensions that are treated as model weights.
WEIGHT_SUFFIXES = (".pt", ".pth", ".onnx", ".tflite", ".h5", ".ckpt")


def register_trained_model(
    name: str,
) -> Callable[[type[TrainedModelAdapter]], type[TrainedModelAdapter]]:
    """Class decorator that registers a trained model implementation."""

    def decorator(cls: type[TrainedModelAdapter]) -> type[TrainedModelAdapter]:
        _TRAINED_MODELS[name] = cls
        return cls

    return decorator


@dataclass
class ModelInfo:
    """Metadata about the weights that are installed on the machine."""

    name: str
    path: str
    size_bytes: int
    registered: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "file": Path(self.path).name,
            "size_bytes": self.size_bytes,
            "registered_implementation": self.registered,
        }


@dataclass
class TrainedModelStatus:
    """Aggregated information about trained model availability."""

    available: bool = False
    models: list[ModelInfo] = field(default_factory=list)
    registered_names: list[str] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "trained_model_available": self.available,
            "models": [model.to_dict() for model in self.models],
            "registered_implementations": list(self.registered_names),
            "message": self.message,
        }


class TrainedModelAdapter(ABC):
    """Base class for a real trained palmprint recognition model.

    A subclass must implement :meth:`load` and :meth:`embed`.  The platform
    never instantiates a matcher for a model whose implementation is missing.
    """

    name: str = "trained_model"
    version: str = "0.0.0"

    def __init__(self, weights_path: str | Path) -> None:
        self.weights_path = Path(weights_path)
        self._loaded = False

    @property
    def available(self) -> bool:
        return self._loaded and self.weights_path.is_file()

    @abstractmethod
    def load(self) -> None:
        """Load the weights into memory."""

    @abstractmethod
    def embed(self, image: np.ndarray) -> np.ndarray:
        """Return the feature embedding of ``image``."""


def discover_models(model_dir: str | Path) -> TrainedModelStatus:
    """Inspect ``model_dir`` and report which weights are present."""
    directory = Path(model_dir)
    models: list[ModelInfo] = []

    if directory.is_dir():
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.suffix.lower() in WEIGHT_SUFFIXES:
                models.append(
                    ModelInfo(
                        name=path.stem,
                        path=str(path),
                        size_bytes=path.stat().st_size,
                        registered=path.stem in _TRAINED_MODELS,
                    )
                )

    registered = sorted(_TRAINED_MODELS)
    usable = [model for model in models if model.registered]

    if usable:
        message = (
            f"{len(usable)} trained model(s) with a registered inference "
            "implementation are available."
        )
    elif models:
        message = (
            "Weight files are present but no inference implementation is "
            "registered for them. Register an implementation via "
            "app.recognition.model_loader.register_trained_model."
        )
    else:
        message = (
            "No trained models are installed. This deployment therefore only "
            "offers the classical, untrained comparison pipeline."
        )

    return TrainedModelStatus(
        available=bool(usable),
        models=models,
        registered_names=registered,
        message=message,
    )


def get_trained_model(model_dir: str | Path, name: str | None = None) -> TrainedModelAdapter | None:
    """Instantiate a registered trained model, or ``None`` when unavailable."""
    status = discover_models(model_dir)
    if not status.available:
        return None
    if name:
        if name not in _TRAINED_MODELS:
            return None
        for model in status.models:
            if model.name == name:
                implementation = _TRAINED_MODELS[name](model.path)
                implementation.load()
                return implementation
        return None

    model = status.models[0]
    implementation = _TRAINED_MODELS[model.name](model.path)
    implementation.load()
    return implementation


def ensure_model_dir(model_dir: str | Path) -> Path:
    """Create the model directory if it does not exist yet."""
    directory = Path(model_dir)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


__all__ = [
    "WEIGHT_SUFFIXES",
    "ModelInfo",
    "TrainedModelAdapter",
    "TrainedModelStatus",
    "discover_models",
    "ensure_model_dir",
    "get_trained_model",
    "register_trained_model",
]
