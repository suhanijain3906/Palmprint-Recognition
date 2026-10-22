"""Repository for experiments and their results."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Experiment, ExperimentResult


class ExperimentRepository:
    """Data access for experiments."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, **values: object) -> Experiment:
        experiment = Experiment(**values)  # type: ignore[arg-type]
        self._session.add(experiment)
        self._session.flush()
        return experiment

    def get(self, experiment_id: str) -> Experiment | None:
        return self._session.get(Experiment, experiment_id)

    def list_for_owner(
        self, owner_id: str, *, offset: int = 0, limit: int = 20
    ) -> tuple[list[Experiment], int]:
        statement = select(Experiment).where(Experiment.owner_id == owner_id)
        count_statement = select(func.count()).select_from(statement.subquery())
        total = int(self._session.execute(count_statement).scalar_one())
        statement = statement.order_by(Experiment.created_at.desc()).offset(offset).limit(limit)
        items = list(self._session.execute(statement).scalars())
        return items, total

    def count_for_owner(self, owner_id: str) -> int:
        statement = (
            select(func.count()).select_from(Experiment).where(Experiment.owner_id == owner_id)
        )
        return int(self._session.execute(statement).scalar_one())

    def add_result(
        self,
        experiment_id: str,
        *,
        kind: str,
        label: str | None = None,
        value: float | None = None,
        unit: str | None = None,
        details: dict[str, Any] | None = None,
        image_id: str | None = None,
        order_index: int = 0,
    ) -> ExperimentResult:
        result = ExperimentResult(
            experiment_id=experiment_id,
            kind=kind,
            label=label,
            value=value,
            unit=unit,
            details_json=json.dumps(details or {}),
            image_id=image_id,
            order_index=order_index,
        )
        self._session.add(result)
        self._session.flush()
        return result

    def list_results(self, experiment_id: str) -> list[ExperimentResult]:
        statement = (
            select(ExperimentResult)
            .where(ExperimentResult.experiment_id == experiment_id)
            .order_by(ExperimentResult.order_index, ExperimentResult.created_at)
        )
        return list(self._session.execute(statement).scalars())


__all__ = ["ExperimentRepository"]
