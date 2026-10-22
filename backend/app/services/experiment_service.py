"""Experiment management.

An experiment bundles a configuration (operation, algorithm, parameters) with
a set of images.  Running it executes the corresponding processing pipeline
for every image and stores the measured results.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from sqlalchemy.orm import Session

from ..models import Experiment, User
from ..repositories import ExperimentRepository
from ..utils.errors import NotFoundError, ValidationError
from .processing_service import ProcessingService

logger = logging.getLogger("backend.experiment_service")

#: Operations that an experiment may run.
SUPPORTED_OPERATIONS = {
    "roi": "roi",
    "enhancement": "enhancement",
    "quality": "quality",
    "features": "features",
    "landmarks": "landmarks",
}


class ExperimentService:
    """Creates, runs and reads research experiments."""

    def __init__(self, session: Session, processing: ProcessingService | None = None) -> None:
        self._session = session
        self._repository = ExperimentRepository(session)
        self._processing = processing or ProcessingService(session)

    def create(self, *, owner: User, request: Any) -> Experiment:
        """Create and immediately run an experiment."""
        operation = (request.operation or "enhancement").lower()
        if operation not in SUPPORTED_OPERATIONS:
            raise ValidationError(
                f"Unsupported operation '{operation}'.",
                code="unsupported_operation",
                details={"supported": sorted(SUPPORTED_OPERATIONS)},
            )

        image_ids = list(request.image_ids or [])
        if not image_ids:
            raise ValidationError("An experiment needs at least one image.", code="missing_images")

        experiment = self._repository.create(
            owner_id=owner.id,
            name=request.name,
            description=request.description,
            operation=operation,
            algorithm=request.algorithm,
            parameters_json=json.dumps(request.parameters or {}, default=str),
            image_ids_json=json.dumps(image_ids),
            status="running",
        )

        started = time.perf_counter()
        try:
            self._run(experiment, owner=owner)
        except Exception as exc:
            logger.exception("Experiment %s failed", experiment.id)
            experiment.status = "failed"
            experiment.error_message = str(exc)[:500]
            experiment.duration_ms = (time.perf_counter() - started) * 1000
            self._session.flush()
            raise

        experiment.status = "completed"
        experiment.duration_ms = (time.perf_counter() - started) * 1000
        self._session.flush()
        return experiment

    def _run(self, experiment: Experiment, *, owner: User) -> None:
        parameters = experiment.parameters
        order = 0
        for image_id in experiment.image_ids:
            operation = experiment.operation
            if operation == "roi":
                outcome = self._processing.run_roi(
                    image_id=image_id,
                    owner=owner,
                    algorithm=experiment.algorithm,
                    parameters=parameters,
                )
            elif operation == "enhancement":
                outcome = self._processing.run_enhancement(
                    image_id=image_id,
                    owner=owner,
                    algorithm=experiment.algorithm,
                    parameters=parameters,
                )
            elif operation == "quality":
                outcome = self._processing.run_quality(image_id=image_id, owner=owner)
            elif operation == "features":
                outcome = self._processing.run_features(
                    image_id=image_id, owner=owner, detector=experiment.algorithm
                )
            else:  # landmarks
                outcome = self._processing.run_landmarks(
                    image_id=image_id, owner=owner, detector=experiment.algorithm
                )

            for key, value in (outcome.get("metrics") or {}).items():
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self._repository.add_result(
                        experiment.id,
                        kind="metric",
                        label=key,
                        value=float(value),
                        image_id=image_id,
                        order_index=order,
                    )
                    order += 1

            self._repository.add_result(
                experiment.id,
                kind="processing_time",
                label=f"processing_time[{image_id[:8]}]",
                value=float(outcome.get("processing_time_ms", 0.0)),
                unit="ms",
                image_id=image_id,
                order_index=order,
            )
            order += 1

            self._repository.add_result(
                experiment.id,
                kind="artifacts",
                label=f"artifacts[{image_id[:8]}]",
                value=float(len(outcome.get("artifacts") or [])),
                unit="count",
                details={"artifacts": [a.model_dump() for a in outcome.get("artifacts", [])]},
                image_id=image_id,
                order_index=order,
            )
            order += 1

            for warning in outcome.get("warnings", []):
                self._repository.add_result(
                    experiment.id,
                    kind="warning",
                    label="warning",
                    details={"message": warning, "image_id": image_id},
                    image_id=image_id,
                    order_index=order,
                )
                order += 1

    def get(self, experiment_id: str, *, owner: User) -> Experiment:
        experiment = self._repository.get(experiment_id)
        if experiment is None or experiment.owner_id != owner.id:
            raise NotFoundError(f"Experiment '{experiment_id}' was not found.")
        return experiment

    def list(
        self, *, owner: User, offset: int = 0, limit: int = 20
    ) -> tuple[list[Experiment], int]:
        return self._repository.list_for_owner(owner.id, offset=offset, limit=limit)

    def results(self, experiment_id: str, *, owner: User) -> list[Any]:
        self.get(experiment_id, owner=owner)
        return self._repository.list_results(experiment_id)

    def export_summary(self, experiment_id: str, *, owner: User) -> dict[str, Any]:
        """Return a machine readable summary of an experiment."""
        experiment = self.get(experiment_id, owner=owner)
        results = self._repository.list_results(experiment_id)
        return {
            "experiment": {
                "id": experiment.id,
                "name": experiment.name,
                "description": experiment.description,
                "operation": experiment.operation,
                "algorithm": experiment.algorithm,
                "parameters": experiment.parameters,
                "image_ids": experiment.image_ids,
                "status": experiment.status,
                "duration_ms": experiment.duration_ms,
                "created_at": experiment.created_at.isoformat(),
            },
            "results": [
                {
                    "kind": result.kind,
                    "label": result.label,
                    "value": result.value,
                    "unit": result.unit,
                    "image_id": result.image_id,
                    "details": result.details,
                }
                for result in results
            ],
            "disclaimer": (
                "Experimental results produced by an untested research platform. "
                "The values are uncalibrated heuristics and are not identity "
                "verification outcomes."
            ),
        }


__all__ = ["SUPPORTED_OPERATIONS", "ExperimentService"]
