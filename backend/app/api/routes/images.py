"""Image upload and management endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from ...models import ImageRecord
from ...repositories import ImageRepository, JobRepository
from ...schemas.common import MessageResponse, Page, PageMeta
from ...schemas.image import ImageResponse, ImageUpdateRequest, ImageUploadResponse
from ...schemas.processing import JobResponse
from ...services.image_service import ImageService
from ..dependencies import CurrentUser, DbSession, get_image_service

logger = logging.getLogger("backend.routes.images")

router = APIRouter(prefix="/images", tags=["images"])


def to_response(image: ImageRecord) -> ImageResponse:
    """Map an ORM record onto the public schema."""
    return ImageResponse(
        id=image.id,
        original_filename=image.original_filename,
        media_type=image.media_type,
        size_bytes=image.size_bytes,
        width=image.width,
        height=image.height,
        checksum_sha256=image.checksum_sha256,
        label=image.label,
        subject_id=image.subject_id,
        notes=image.notes,
        created_at=image.created_at,
        download_url=f"/api/v1/images/{image.id}/file",
    )


@router.get("", response_model=Page[ImageResponse], summary="List the uploaded images")
@router.get("/", response_model=Page[ImageResponse], include_in_schema=False)
def list_images(
    session: DbSession,
    user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
    include_deleted: bool = False,
) -> Page[ImageResponse]:
    """Return the images that belong to the current user."""
    repository = ImageRepository(session)
    offset = (max(page, 1) - 1) * page_size
    items, total = repository.list_for_owner(
        user.id, offset=offset, limit=page_size, include_deleted=include_deleted
    )
    return Page[ImageResponse](
        items=[to_response(item) for item in items],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, -(-total // page_size)),
        ),
    )


@router.post(
    "/upload",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a palmprint image",
)
@router.post(
    "/upload/",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
@router.post(
    "",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a palmprint image (POST /images)",
)
@router.post(
    "/",
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
def upload_image(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ImageService, Depends(get_image_service)],
    file: UploadFile = File(..., description="PNG, JPEG, BMP, TIFF or WebP image"),
    label: Annotated[str | None, Form()] = None,
    subject_id: Annotated[str | None, Form()] = None,
    notes: Annotated[str | None, Form()] = None,
) -> ImageUploadResponse:
    """Validate and store an uploaded palmprint image.

    The file is validated by the ML service (magic bytes, decodability and
    dimensions) before it is stored.  The original file is kept unmodified.
    """
    payload = file.file.read()
    record, report, warnings = service.store_upload(
        payload,
        filename=file.filename or "upload",
        content_type=file.content_type,
        owner=user,
        label=label,
        subject_id=subject_id,
        notes=notes,
    )
    return ImageUploadResponse(image=to_response(record), validation=report, warnings=warnings)


@router.get("/{image_id}", response_model=ImageResponse, summary="Get the metadata of an image")
@router.get("/{image_id}/", response_model=ImageResponse, include_in_schema=False)
def get_image(image_id: str, session: DbSession, user: CurrentUser) -> ImageResponse:
    """Return the metadata of a single image."""
    record = ImageRepository(session).get(image_id)
    if record is None or record.deleted_at is not None or record.owner_id != user.id:
        from ...utils.errors import NotFoundError

        raise NotFoundError(f"Image '{image_id}' was not found.")
    return to_response(record)


@router.get(
    "/{image_id}/file",
    summary="Download the original image",
    response_class=Response,
)
def download_image(
    image_id: str,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ImageService, Depends(get_image_service)],
) -> Response:
    """Stream the original image bytes."""
    from ...utils.errors import NotFoundError

    record = ImageRepository(session).get(image_id)
    if record is None or record.deleted_at is not None or record.owner_id != user.id:
        raise NotFoundError(f"Image '{image_id}' was not found.")

    data = service.load_bytes(record)
    return Response(
        content=data,
        media_type=record.media_type,
        headers={
            "Content-Disposition": (
                f'inline; filename="{record.id}.{record.media_type.split("/")[-1]}"'
            ),
            "Cache-Control": "private, max-age=0, no-store",
        },
    )


@router.patch("/{image_id}", response_model=ImageResponse, summary="Update the image annotations")
def update_image(
    image_id: str,
    payload: ImageUpdateRequest,
    session: DbSession,
    user: CurrentUser,
) -> ImageResponse:
    """Update the optional annotations of an image."""
    from ...utils.errors import NotFoundError

    record = ImageRepository(session).get(image_id)
    if record is None or record.deleted_at is not None or record.owner_id != user.id:
        raise NotFoundError(f"Image '{image_id}' was not found.")

    if payload.label is not None:
        record.label = payload.label
    if payload.subject_id is not None:
        record.subject_id = payload.subject_id
    if payload.notes is not None:
        record.notes = payload.notes
    session.flush()
    return to_response(record)


@router.delete("/{image_id}", response_model=MessageResponse, summary="Delete an image")
def delete_image(
    image_id: str,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ImageService, Depends(get_image_service)],
) -> MessageResponse:
    """Delete an image and remove its file from the storage."""
    from ...utils.errors import NotFoundError

    record = ImageRepository(session).get(image_id)
    if record is None or record.deleted_at is not None or record.owner_id != user.id:
        raise NotFoundError(f"Image '{image_id}' was not found.")

    service.delete(record)
    return MessageResponse(message=f"Image '{image_id}' was deleted.")


@router.get(
    "/{image_id}/jobs", response_model=list[JobResponse], summary="List the jobs of an image"
)
def list_image_jobs(image_id: str, session: DbSession, user: CurrentUser) -> list[JobResponse]:
    """Return the processing jobs that were executed for an image."""
    from ...utils.errors import NotFoundError

    record = ImageRepository(session).get(image_id)
    if record is None or record.deleted_at is not None or record.owner_id != user.id:
        raise NotFoundError(f"Image '{image_id}' was not found.")

    jobs = JobRepository(session).list_for_image(image_id)
    return [
        JobResponse(
            id=job.id,
            image_id=job.image_id,
            operation=job.operation,
            algorithm=job.algorithm,
            algorithm_version=job.algorithm_version,
            status=job.status,
            parameters=job.parameters,
            metrics=job.metrics,
            warnings=job.warnings,
            duration_ms=job.duration_ms,
            error_code=job.error_code,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )
        for job in jobs
    ]


__all__ = ["router", "to_response"]
