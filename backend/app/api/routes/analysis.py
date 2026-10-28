"""Unified Palmprint Analysis endpoints.

Provides:
- POST /analysis/palmprint - Run complete analysis pipeline (ROI, Quality, CLAHE, Features, Landmarks)
- GET  /analysis/{analysis_id} - Retrieve analysis results and generated artifacts
"""

from __future__ import annotations

import json
import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from pydantic import BaseModel, Field

from ...models import ImageRecord
from ...repositories import ImageRepository, JobRepository
from ...schemas.image import ImageResponse
from ...schemas.processing import ProcessingResponse
from ...services.image_service import ImageService
from ...services.processing_service import ProcessingService
from ...utils.errors import NotFoundError, ValidationError
from ..dependencies import CurrentUser, DbSession, get_image_service, get_processing_service
from .images import to_response
from .processing import _response

logger = logging.getLogger("backend.routes.analysis")

router = APIRouter(prefix="/analysis", tags=["analysis"])


class AnalysisResponse(BaseModel):
    """Aggregated palmprint analysis outcome."""

    status: str = "success"
    analysis_id: str
    image_id: str
    image: ImageResponse | None = None
    roi: ProcessingResponse | None = None
    quality: ProcessingResponse | None = None
    enhancement: ProcessingResponse | None = None
    features: ProcessingResponse | None = None
    landmarks: ProcessingResponse | None = None
    created_at: str | None = None


def _build_analysis_response(image: ImageRecord, jobs: list[Any]) -> AnalysisResponse:
    primary_id = image.id
    roi_resp = None
    quality_resp = None
    enh_resp = None
    feat_resp = None
    land_resp = None

    for job in jobs:
        try:
            res_dict = json.loads(job.result_json or "{}")
        except Exception:
            res_dict = {}

        outcome = {
            "job_id": job.id,
            "operation": job.operation,
            "algorithm": job.algorithm,
            "algorithm_version": job.algorithm_version,
            "image_id": image.id,
            "processing_time_ms": job.duration_ms or 0.0,
            "metrics": res_dict.get("metrics") or {},
            "result": res_dict.get("result") or res_dict,
            "artifacts": res_dict.get("artifacts") or [],
            "warnings": res_dict.get("warnings") or [],
            "limitations": res_dict.get("limitations") or [],
        }

        if job.operation == "roi":
            roi_resp = _response(outcome)
            primary_id = job.id
        elif job.operation == "quality":
            quality_resp = _response(outcome)
        elif job.operation == "enhancement":
            enh_resp = _response(outcome)
        elif job.operation == "features":
            feat_resp = _response(outcome)
        elif job.operation == "landmarks":
            land_resp = _response(outcome)

    return AnalysisResponse(
        status="success",
        analysis_id=primary_id,
        image_id=image.id,
        image=to_response(image),
        roi=roi_resp,
        quality=quality_resp,
        enhancement=enh_resp,
        features=feat_resp,
        landmarks=land_resp,
        created_at=image.created_at.isoformat() if image.created_at else None,
    )


async def _run_full_analysis(
    request: Request,
    session: DbSession,
    user: CurrentUser,
    image_service: ImageService,
    processing_service: ProcessingService,
    file: UploadFile | None = None,
    image_id: str | None = None,
    label: str | None = None,
    subject_id: str | None = None,
) -> AnalysisResponse:
    # Check if JSON body with image_id was sent
    resolved_image_id = image_id
    if not resolved_image_id and not file:
        try:
            body = await request.json()
            if isinstance(body, dict):
                resolved_image_id = body.get("image_id") or body.get("id")
        except Exception:
            pass

    record: ImageRecord | None = None

    if file and file.filename:
        payload = await file.read()
        if payload:
            rec, report, warnings = image_service.store_upload(
                payload,
                filename=file.filename or "upload.png",
                content_type=file.content_type,
                owner=user,
                label=label,
                subject_id=subject_id,
            )
            record = rec
            resolved_image_id = record.id

    if not record and resolved_image_id:
        record = ImageRepository(session).get(resolved_image_id)
        if record is None or record.deleted_at is not None or record.owner_id != user.id:
            raise NotFoundError(f"Image '{resolved_image_id}' was not found.")

    if not record:
        raise ValidationError(
            "An image file or valid image_id is required to perform palmprint analysis.",
            code="missing_image",
        )

    # Execute processing pipelines
    roi_res = None
    quality_res = None
    enh_res = None
    feat_res = None
    land_res = None

    try:
        roi_outcome = processing_service.run_roi(image_id=record.id, owner=user)
        roi_res = _response(roi_outcome)
    except Exception as exc:
        logger.warning("ROI analysis issue on %s: %s", record.id, exc)

    try:
        quality_outcome = processing_service.run_quality(image_id=record.id, owner=user)
        quality_res = _response(quality_outcome)
    except Exception as exc:
        logger.warning("Quality analysis issue on %s: %s", record.id, exc)

    try:
        enh_outcome = processing_service.run_enhancement(
            image_id=record.id, owner=user, algorithm="clahe"
        )
        enh_res = _response(enh_outcome)
    except Exception as exc:
        logger.warning("Enhancement analysis issue on %s: %s", record.id, exc)

    try:
        feat_outcome = processing_service.run_features(image_id=record.id, owner=user, detector="orb")
        feat_res = _response(feat_outcome)
    except Exception as exc:
        logger.warning("Features analysis issue on %s: %s", record.id, exc)

    try:
        land_outcome = processing_service.run_landmarks(image_id=record.id, owner=user, detector="orb")
        land_res = _response(land_outcome)
    except Exception as exc:
        logger.warning("Landmarks analysis issue on %s: %s", record.id, exc)

    primary_id = (roi_res.job_id if roi_res else None) or (quality_res.job_id if quality_res else None) or record.id

    return AnalysisResponse(
        status="success",
        analysis_id=primary_id,
        image_id=record.id,
        image=to_response(record),
        roi=roi_res,
        quality=quality_res,
        enhancement=enh_res,
        features=feat_res,
        landmarks=land_res,
        created_at=record.created_at.isoformat() if record.created_at else None,
    )


@router.post("/palmprint", response_model=AnalysisResponse, status_code=status.HTTP_200_OK, summary="Run palmprint analysis")
@router.post("/palmprint/", response_model=AnalysisResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@router.post("", response_model=AnalysisResponse, status_code=status.HTTP_200_OK, summary="Run analysis")
@router.post("/", response_model=AnalysisResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def analyze_palmprint(
    request: Request,
    session: DbSession,
    user: CurrentUser,
    image_service: Annotated[ImageService, Depends(get_image_service)],
    processing_service: Annotated[ProcessingService, Depends(get_processing_service)],
    file: UploadFile | None = File(None),
    image_id: Annotated[str | None, Form()] = None,
    label: Annotated[str | None, Form()] = None,
    subject_id: Annotated[str | None, Form()] = None,
) -> AnalysisResponse:
    """Run full palmprint analysis pipeline."""
    return await _run_full_analysis(
        request=request,
        session=session,
        user=user,
        image_service=image_service,
        processing_service=processing_service,
        file=file,
        image_id=image_id,
        label=label,
        subject_id=subject_id,
    )


@router.get("/{analysis_id}", response_model=AnalysisResponse, summary="Retrieve analysis results")
@router.get("/{analysis_id}/", response_model=AnalysisResponse, include_in_schema=False)
def get_analysis(analysis_id: str, session: DbSession, user: CurrentUser) -> AnalysisResponse:
    """Retrieve an existing palmprint analysis by job ID or image ID."""
    job_repo = JobRepository(session)
    img_repo = ImageRepository(session)

    # 1. Try finding job directly
    job = job_repo.get(analysis_id)
    if job and job.image_id and job.owner_id == user.id:
        image = img_repo.get(job.image_id)
        if image and image.deleted_at is None:
            jobs = job_repo.list_for_image(image.id)
            return _build_analysis_response(image, jobs)

    # 2. Try finding image directly
    image = img_repo.get(analysis_id)
    if image and image.deleted_at is None and image.owner_id == user.id:
        jobs = job_repo.list_for_image(image.id)
        return _build_analysis_response(image, jobs)

    raise NotFoundError(f"Analysis '{analysis_id}' was not found.", code="analysis_not_found")


__all__ = ["AnalysisResponse", "router"]
