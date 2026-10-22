"""Repository for report records."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ReportRecord


class ReportRepository:
    """Data access for :class:`~app.models.report.ReportRecord`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **values: object) -> ReportRecord:
        report = ReportRecord(**values)  # type: ignore[arg-type]
        self._session.add(report)
        self._session.flush()
        return report

    def get(self, report_id: str) -> ReportRecord | None:
        return self._session.get(ReportRecord, report_id)

    def list_for_owner(
        self, owner_id: str, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[ReportRecord], int]:
        statement = select(ReportRecord).where(ReportRecord.owner_id == owner_id)
        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self._session.execute(count_statement).scalar_one())
        statement = statement.order_by(ReportRecord.created_at.desc()).offset(offset).limit(limit)
        items = list(self._session.execute(statement).scalars())
        return items, total

    def count_for_owner(self, owner_id: str) -> int:
        statement = (
            select(func.count()).select_from(ReportRecord).where(ReportRecord.owner_id == owner_id)
        )
        return int(self._session.execute(statement).scalar_one())


__all__ = ["ReportRepository"]
