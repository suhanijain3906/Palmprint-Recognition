"""Repository for processing jobs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ProcessingJob


class JobRepository:
    """Data access for :class:`~app.models.job.ProcessingJob`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **values: object) -> ProcessingJob:
        job = ProcessingJob(**values)  # type: ignore[arg-type]
        self._session.add(job)
        self._session.flush()
        return job

    def get(self, job_id: str) -> ProcessingJob | None:
        return self._session.get(ProcessingJob, job_id)

    def list_for_owner(
        self,
        owner_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        operation: str | None = None,
        status: str | None = None,
    ) -> tuple[list[ProcessingJob], int]:
        statement = select(ProcessingJob).where(ProcessingJob.owner_id == owner_id)
        if operation:
            statement = statement.where(ProcessingJob.operation == operation)
        if status:
            statement = statement.where(ProcessingJob.status == status)
        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self._session.execute(count_statement).scalar_one())
        statement = statement.order_by(ProcessingJob.created_at.desc()).offset(offset).limit(limit)
        items = list(self._session.execute(statement).scalars())
        return items, total

    def count_for_owner(self, owner_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(ProcessingJob)
            .where(ProcessingJob.owner_id == owner_id)
        )
        return int(self._session.execute(statement).scalar_one())

    def list_recent(self, owner_id: str, *, limit: int = 10) -> list[ProcessingJob]:
        statement = (
            select(ProcessingJob)
            .where(ProcessingJob.owner_id == owner_id)
            .order_by(ProcessingJob.created_at.desc())
            .limit(limit)
        )
        return list(self._session.execute(statement).scalars())

    def list_for_image(self, image_id: str) -> list[ProcessingJob]:
        statement = (
            select(ProcessingJob)
            .where(ProcessingJob.image_id == image_id)
            .order_by(ProcessingJob.created_at.desc())
        )
        return list(self._session.execute(statement).scalars())


__all__ = ["JobRepository"]
