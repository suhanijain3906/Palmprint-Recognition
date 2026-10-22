"""Image comparison endpoint."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ...schemas.recognition import ComparisonRequest, ComparisonResponse
from ...services.processing_service import ProcessingService
from ..dependencies import CurrentUser, DbSession, get_processing_service

logger = logging.getLogger("backend.routes.comparison")

router = APIRouter(prefix="/comparison", tags=["comparison"])


@router.post("", response_model=ComparisonResponse, summary="Compare two stored images")
def compare_images(
    payload: ComparisonRequest,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> ComparisonResponse:
    """Produce the difference image and the pixel similarity metrics.

    PSNR and SSIM measure pixel similarity between two aligned images; they
    do not measure biometric similarity.
    """
    outcome = service.run_comparison(
        image_a_id=payload.image_a_id, image_b_id=payload.image_b_id, owner=user
    )
    result = outcome.get("result", {}) or {}
    return ComparisonResponse(
        job_id=outcome["job_id"],
        psnr_db=result.get("psnr_db"),
        ssim=result.get("ssim"),
        aligned=bool(result.get("aligned", True)),
        resized=bool(result.get("resized", False)),
        metrics=outcome.get("metrics", {}),
        artifacts=outcome.get("artifacts", []),
        warnings=outcome.get("warnings", []),
        limitations=outcome.get("limitations", []),
        processing_time_ms=outcome.get("processing_time_ms", 0.0),
    )


__all__ = ["router"]
