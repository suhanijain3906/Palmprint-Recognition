"""Processing endpoints (ROI, enhancement, quality, features, landmarks)."""

from __future__ import annotations

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends

from ...schemas.processing import ProcessingResponse
from ...services.processing_service import ProcessingService
from ..dependencies import CurrentUser, DbSession, get_processing_service

logger = logging.getLogger("backend.routes.processing")

router = APIRouter(prefix="/processing", tags=["processing"])


def _response(outcome: dict[str, Any]) -> ProcessingResponse:
    return ProcessingResponse(
        job_id=outcome["job_id"],
        operation=outcome["operation"],
        algorithm=outcome["algorithm"],
        algorithm_version=outcome.get("algorithm_version"),
        image_id=outcome["image_id"],
        processing_time_ms=outcome.get("processing_time_ms", 0.0),
        metrics=outcome.get("metrics", {}),
        result=outcome.get("result", {}),
        artifacts=outcome.get("artifacts", []),
        warnings=outcome.get("warnings", []),
        limitations=outcome.get("limitations", []),
    )


@router.post("/roi", response_model=ProcessingResponse, summary="Extract a region of interest")
def extract_roi(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
    payload: Annotated[dict[str, Any], Body(...)] = None,
) -> ProcessingResponse:
    """Run the ROI extraction pipeline on a stored image.

    The result is an *approximate* palm region proposal; the endpoint never
    claims anatomical palm localisation.
    """
    payload = payload or {}
    outcome = service.run_roi(
        image_id=str(payload.get("image_id", "")),
        owner=user,
        algorithm=str(payload.get("algorithm", "classical_contour_roi")),
        parameters=dict(payload.get("parameters") or {}),
    )
    return _response(outcome)


@router.post("/enhancement", response_model=ProcessingResponse, summary="Enhance an image")
def enhance_image(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
    payload: Annotated[dict[str, Any], Body(...)] = None,
) -> ProcessingResponse:
    """Apply an enhancement algorithm to a stored image."""
    payload = payload or {}
    outcome = service.run_enhancement(
        image_id=str(payload.get("image_id", "")),
        owner=user,
        algorithm=str(payload.get("algorithm", "clahe")),
        parameters=dict(payload.get("parameters") or {}),
    )
    return _response(outcome)


@router.post("/quality", response_model=ProcessingResponse, summary="Assess the image quality")
def assess_quality(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
    payload: Annotated[dict[str, Any], Body(...)] = None,
) -> ProcessingResponse:
    """Compute the quality metrics of a stored image."""
    payload = payload or {}
    outcome = service.run_quality(image_id=str(payload.get("image_id", "")), owner=user)
    return _response(outcome)


@router.post("/features", response_model=ProcessingResponse, summary="Extract image features")
def extract_features(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
    payload: Annotated[dict[str, Any], Body(...)] = None,
) -> ProcessingResponse:
    """Extract classical keypoints and descriptors from a stored image."""
    payload = payload or {}
    outcome = service.run_features(
        image_id=str(payload.get("image_id", "")),
        owner=user,
        detector=str(payload.get("detector", "orb")),
        n_features=payload.get("n_features"),
    )
    return _response(outcome)


@router.post("/landmarks", response_model=ProcessingResponse, summary="Visualise feature points")
def visualize_landmarks(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
    payload: Annotated[dict[str, Any], Body(...)] = None,
) -> ProcessingResponse:
    """Render an overlay of the detected feature points.

    The response distinguishes generic feature points from anatomical palm
    landmarks.
    """
    payload = payload or {}
    outcome = service.run_landmarks(
        image_id=str(payload.get("image_id", "")),
        owner=user,
        detector=str(payload.get("detector", "orb")),
        max_points=payload.get("max_points"),
    )
    return _response(outcome)


__all__ = ["router"]
