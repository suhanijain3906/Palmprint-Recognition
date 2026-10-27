"""Download endpoints for the generated artefacts (ROI, enhanced, overlays).

Artefacts are stored by the backend, not by the ML service, and every
artefact is bound to a processing job of the current user.  A user can only
download artefacts that belong to their own jobs.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Depends, Response

from ...repositories import JobRepository
from ...utils.errors import NotFoundError
from ..dependencies import CurrentUser, DbSession, get_storage

logger = logging.getLogger("backend.routes.artifacts")

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


def _find_owner_job(session, owner_id: str, artifact_key: str):
    """Return the job that produced the artefact, if the user owns it."""
    jobs = JobRepository(session)
    owner_jobs, _ = jobs.list_for_owner(owner_id, offset=0, limit=500)
    for job in owner_jobs:
        try:
            result = json.loads(job.result_json or "{}")
        except json.JSONDecodeError:  # pragma: no cover - defensive
            continue
        for artifact in result.get("artifacts", []) or []:
            if artifact.get("id") == artifact_key:
                return job
    return None


@router.get("/{artifact_key:path}", summary="Download a generated artefact")
def download_artifact(
    artifact_key: str,
    session: DbSession,
    user: CurrentUser,
    storage=Depends(get_storage),
) -> Response:
    """Stream a generated artefact that belongs to the current user."""
    job = _find_owner_job(session, user.id, artifact_key)
    if job is None:
        raise NotFoundError("The artefact was not found.", code="artifact_not_found")

    try:
        data = storage.read(artifact_key)
    except FileNotFoundError as exc:
        raise NotFoundError(
            "The artefact file is no longer available.", code="artifact_not_found"
        ) from exc

    return Response(
        content=data,
        media_type="image/png",
        headers={"Cache-Control": "private, max-age=0, no-store"},
    )


__all__ = ["router"]
