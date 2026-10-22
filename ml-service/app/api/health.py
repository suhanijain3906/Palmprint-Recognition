"""Health endpoint of the ML service."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter

from ..config import settings
from ..recognition.model_loader import discover_models
from .schemas import HealthResponse

router = APIRouter(tags=["health"])

_STARTED_AT = time.time()


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health() -> HealthResponse:
    """Report service state, uptime and the availability of trained models."""
    from ..algorithms.enhancement import ENHANCEMENT_ALGORITHMS
    from ..algorithms.roi import ROI_ALGORITHMS
    from ..features.classical_features import DETECTORS

    trained: dict[str, Any] = discover_models(settings.model_dir).to_dict()

    return HealthResponse(
        status="ok",
        service=settings.app_name,
        version=settings.version,
        uptime_seconds=round(time.time() - _STARTED_AT, 3),
        trained_models=trained,
        algorithms=[
            *sorted(ROI_ALGORITHMS),
            *sorted(ENHANCEMENT_ALGORITHMS),
            *sorted(DETECTORS),
        ],
    )


__all__ = ["router"]
