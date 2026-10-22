"""Recognition endpoint (experimental similarity comparison)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ...schemas.recognition import RecognitionRequest, RecognitionResponse
from ...services.processing_service import ProcessingService
from ..dependencies import CurrentUser, DbSession, get_processing_service

logger = logging.getLogger("backend.routes.recognition")

router = APIRouter(prefix="/recognition", tags=["recognition"])


@router.post(
    "/compare",
    response_model=RecognitionResponse,
    summary="Compare two images experimentally",
)
def compare_images(
    payload: RecognitionRequest,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ProcessingService, Depends(get_processing_service)],
) -> RecognitionResponse:
    """Compare two stored images with the classical matching pipeline.

    The response never presents the similarity score as a probability of
    identity and states explicitly whether a trained model was used.
    """
    outcome = service.run_recognition(
        image_a_id=payload.image_a_id,
        image_b_id=payload.image_b_id,
        owner=user,
        detector=payload.detector,
        lowe_ratio=payload.lowe_ratio,
    )
    result = outcome.get("result", {}) or {}
    metrics = outcome.get("metrics", {}) or {}
    warnings = list(outcome.get("warnings", []))
    limitations = list(outcome.get("limitations", []))

    trained_available = bool(result.get("trained_model_available"))

    return RecognitionResponse(
        job_id=outcome["job_id"],
        similarity_score=result.get("similarity_score"),
        score_kind=str(result.get("score_kind", "unavailable")),
        is_trained_model=bool((result.get("matcher") or {}).get("is_trained_model", False)),
        is_calibrated_probability=bool(result.get("is_calibrated_probability", False)),
        trained_model_available=trained_available,
        matcher=str(result.get("matcher", {}).get("name", "classical_orb_matcher"))
        if isinstance(result.get("matcher"), dict)
        else str(result.get("matcher", "classical_orb_matcher")),
        matcher_version=str(result.get("matcher", {}).get("version", "1.0.0"))
        if isinstance(result.get("matcher"), dict)
        else "1.0.0",
        details={**metrics, **{k: v for k, v in result.items() if k not in {"matcher"}}},
        artifacts=outcome.get("artifacts", []),
        warnings=warnings,
        limitations=limitations,
        processing_time_ms=outcome.get("processing_time_ms", 0.0),
    )


__all__ = ["router"]
