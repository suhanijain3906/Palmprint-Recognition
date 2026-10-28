"""Palmprint alias routes.

Aliases `/palmprints` to `/images` to support standard biometric API path conventions.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status

from ...repositories import ImageRepository
from ...schemas.common import MessageResponse, Page, PageMeta
from ...schemas.image import ImageResponse, ImageUpdateRequest, ImageUploadResponse
from ...schemas.processing import JobResponse
from ...services.image_service import ImageService
from ..dependencies import CurrentUser, DbSession, get_image_service
from .images import (
    delete_image,
    download_image,
    get_image,
    list_image_jobs,
    list_images,
    to_response,
    update_image,
    upload_image,
)

router = APIRouter(prefix="/palmprints", tags=["palmprints"])

# Upload endpoint aliases
router.add_api_route(
    "/upload",
    upload_image,
    methods=["POST"],
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a palmprint image",
)
router.add_api_route(
    "/upload/",
    upload_image,
    methods=["POST"],
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)
router.add_api_route(
    "",
    upload_image,
    methods=["POST"],
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a palmprint image (POST /palmprints)",
)
router.add_api_route(
    "/",
    upload_image,
    methods=["POST"],
    response_model=ImageUploadResponse,
    status_code=status.HTTP_201_CREATED,
    include_in_schema=False,
)

# Listing and detail routes
router.add_api_route(
    "",
    list_images,
    methods=["GET"],
    response_model=Page[ImageResponse],
    summary="List palmprint images",
)
router.add_api_route(
    "/",
    list_images,
    methods=["GET"],
    response_model=Page[ImageResponse],
    include_in_schema=False,
)
router.add_api_route(
    "/{image_id}",
    get_image,
    methods=["GET"],
    response_model=ImageResponse,
    summary="Get palmprint image metadata",
)
router.add_api_route(
    "/{image_id}/",
    get_image,
    methods=["GET"],
    response_model=ImageResponse,
    include_in_schema=False,
)
router.add_api_route(
    "/{image_id}/file",
    download_image,
    methods=["GET"],
    response_class=Response,
    summary="Download palmprint image file",
)
router.add_api_route(
    "/{image_id}",
    update_image,
    methods=["PATCH"],
    response_model=ImageResponse,
    summary="Update palmprint image metadata",
)
router.add_api_route(
    "/{image_id}",
    delete_image,
    methods=["DELETE"],
    response_model=MessageResponse,
    summary="Delete palmprint image",
)
router.add_api_route(
    "/{image_id}/jobs",
    list_image_jobs,
    methods=["GET"],
    response_model=list[JobResponse],
    summary="List processing jobs for a palmprint image",
)

__all__ = ["router"]

