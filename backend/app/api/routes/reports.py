"""Report endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from ...repositories import ReportRepository
from ...schemas.common import Page, PageMeta
from ...schemas.experiment import ReportCreateRequest, ReportResponse
from ...services.report_service import ReportService
from ..dependencies import CurrentUser, DbSession, get_report_service

logger = logging.getLogger("backend.routes.reports")

router = APIRouter(prefix="/reports", tags=["reports"])


def to_response(report, *, include_url: bool = True) -> ReportResponse:
    """Map an ORM record onto the public schema."""
    return ReportResponse(
        id=report.id,
        title=report.title,
        report_type=report.report_type,
        status=report.status,
        size_bytes=report.size_bytes,
        experiment_id=report.experiment_id,
        job_id=report.job_id,
        error_message=report.error_message,
        created_at=report.created_at,
        generated_at=report.generated_at,
        download_url=(
            f"/api/v1/reports/{report.id}/download"
            if include_url and report.status == "ready"
            else None
        ),
    )


@router.get("", response_model=Page[ReportResponse], summary="List the generated reports")
def list_reports(
    session: DbSession,
    user: CurrentUser,
    page: int = 1,
    page_size: int = 20,
) -> Page[ReportResponse]:
    """Return the reports of the current user."""
    offset = (max(page, 1) - 1) * page_size
    items, total = ReportRepository(session).list_for_owner(user.id, offset=offset, limit=page_size)
    return Page[ReportResponse](
        items=[to_response(item) for item in items],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, -(-total // page_size)),
        ),
    )


@router.post(
    "",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a report",
)
def create_report(
    payload: ReportCreateRequest,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ReportService, Depends(get_report_service)],
) -> ReportResponse:
    """Generate a PDF report for a set of processing jobs or an experiment."""
    report = service.create_processing_report(
        owner=user,
        title=payload.title,
        report_type=payload.report_type,
        job_ids=payload.job_ids,
        experiment_id=payload.experiment_id,
        include_images=payload.include_images,
    )
    return to_response(report)


@router.get("/{report_id}", response_model=ReportResponse, summary="Get a report")
def get_report(report_id: str, session: DbSession, user: CurrentUser) -> ReportResponse:
    """Return the metadata of a single report."""
    from ...utils.errors import NotFoundError

    report = ReportRepository(session).get(report_id)
    if report is None or report.owner_id != user.id:
        raise NotFoundError(f"Report '{report_id}' was not found.")
    return to_response(report)


@router.get(
    "/{report_id}/download",
    summary="Download a report",
    response_class=Response,
)
def download_report(
    report_id: str,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ReportService, Depends(get_report_service)],
) -> Response:
    """Stream the generated PDF."""
    from ...utils.errors import NotFoundError

    report = ReportRepository(session).get(report_id)
    if report is None or report.owner_id != user.id:
        raise NotFoundError(f"Report '{report_id}' was not found.")
    if report.status != "ready":
        raise NotFoundError(
            f"The report is in state '{report.status}' and cannot be downloaded.",
            code="report_not_ready",
        )

    data = service.load_bytes(report)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="report-{report.id}.pdf"',
            "Cache-Control": "private, max-age=0, no-store",
        },
    )


__all__ = ["router", "to_response"]
