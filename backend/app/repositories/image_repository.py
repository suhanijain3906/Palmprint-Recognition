"""Repository for image records."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import ImageRecord


class ImageRepository:
    """Data access for :class:`~app.models.image.ImageRecord`."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **values: object) -> ImageRecord:
        image = ImageRecord(**values)  # type: ignore[arg-type]
        self._session.add(image)
        self._session.flush()
        return image

    def get(self, image_id: str) -> ImageRecord | None:
        return self._session.get(ImageRecord, image_id)

    def list_for_owner(
        self,
        owner_id: str,
        *,
        offset: int = 0,
        limit: int = 20,
        include_deleted: bool = False,
    ) -> tuple[list[ImageRecord], int]:
        statement = select(ImageRecord).where(ImageRecord.owner_id == owner_id)
        if not include_deleted:
            statement = statement.where(ImageRecord.deleted_at.is_(None))
        count_statement = select(func.count()).select_from(statement.subquery())
        total = self._session.execute(count_statement).scalar_one()
        statement = statement.order_by(ImageRecord.created_at.desc()).offset(offset).limit(limit)
        items = list(self._session.execute(statement).scalars())
        return items, int(total)

    def count_for_owner(self, owner_id: str) -> int:
        statement = (
            select(func.count())
            .select_from(ImageRecord)
            .where(ImageRecord.owner_id == owner_id, ImageRecord.deleted_at.is_(None))
        )
        return int(self._session.execute(statement).scalar_one())

    def soft_delete(self, image: ImageRecord) -> None:
        from ..models import utcnow

        image.deleted_at = utcnow()
        self._session.flush()

    def list_expired(self, *, older_than_days: int) -> list[ImageRecord]:
        from datetime import timedelta

        from ..models import utcnow

        cutoff = utcnow() - timedelta(days=older_than_days)
        statement = (
            select(ImageRecord)
            .where(ImageRecord.deleted_at.is_not(None), ImageRecord.deleted_at < cutoff)
            .limit(500)
        )
        return list(self._session.execute(statement).scalars())


__all__ = ["ImageRepository"]
