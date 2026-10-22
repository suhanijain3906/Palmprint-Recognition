"""Experiment endpoints."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends

from ...schemas.common import Page, PageMeta
from ...schemas.experiment import (
    ExperimentRequest,
    ExperimentResponse,
    ExperimentResultResponse,
)
from ...services.experiment_service import ExperimentService
from ..dependencies import CurrentUser, DbSession, get_experiment_service

logger = logging.getLogger("backend.routes.experiments")

router = APIRouter(prefix="/experiments", tags=["experiments"])


def to_response(experiment, results=None) -> ExperimentResponse:
    """Map an ORM record onto the public schema."""
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        description=experiment.description,
        operation=experiment.operation,
        algorithm=experiment.algorithm,
        parameters=experiment.parameters,
        image_ids=experiment.image_ids,
        status=experiment.status,
        duration_ms=experiment.duration_ms,
        error_message=experiment.error_message,
        report_id=experiment.report_id,
        created_at=experiment.created_at,
        results=[
            ExperimentResultResponse(
                id=result.id,
                kind=result.kind,
                label=result.label,
                value=result.value,
                unit=result.unit,
                details=result.details,
                image_id=result.image_id,
                order_index=result.order_index,
            )
            for result in (results or [])
        ],
    )


@router.post("", response_model=ExperimentResponse, summary="Create and run an experiment")
def create_experiment(
    payload: ExperimentRequest,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ExperimentService, Depends(get_experiment_service)],
) -> ExperimentResponse:
    """Configure an experiment, run it and persist the measured results."""
    experiment = service.create(owner=user, request=payload)
    results = service.results(experiment.id, owner=user)
    return to_response(experiment, results)


@router.get("", response_model=Page[ExperimentResponse], summary="List the experiments")
def list_experiments(
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ExperimentService, Depends(get_experiment_service)],
    page: int = 1,
    page_size: int = 20,
) -> Page[ExperimentResponse]:
    """Return the experiments of the current user."""
    offset = (max(page, 1) - 1) * page_size
    items, total = service.list(owner=user, offset=offset, limit=page_size)
    return Page[ExperimentResponse](
        items=[to_response(item) for item in items],
        meta=PageMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, -(-total // page_size)),
        ),
    )


@router.get("/{experiment_id}", response_model=ExperimentResponse, summary="Get an experiment")
def get_experiment(
    experiment_id: str,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ExperimentService, Depends(get_experiment_service)],
) -> ExperimentResponse:
    """Return a single experiment with all of its results."""
    experiment = service.get(experiment_id, owner=user)
    results = service.results(experiment_id, owner=user)
    return to_response(experiment, results)


@router.get(
    "/{experiment_id}/summary",
    summary="Export a machine readable experiment summary",
)
def export_experiment(
    experiment_id: str,
    session: DbSession,
    user: CurrentUser,
    service: Annotated[ExperimentService, Depends(get_experiment_service)],
) -> dict:
    """Return the experiment configuration and its results as JSON."""
    return service.export_summary(experiment_id, owner=user)


__all__ = ["router", "to_response"]
