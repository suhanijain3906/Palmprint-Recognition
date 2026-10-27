"""Processing service: orchestrates the ML service and persists the results.

Every processing call

1. loads the original image from the storage,
2. calls the ML service with an explicit timeout,
3. stores the produced artefacts in the backend storage (so that the browser
   never has to reach the ML service),
4. records a :class:`~app.models.job.ProcessingJob` with the parameters,
   the metrics and the warnings.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy.orm import Session

from ..models import ImageRecord, ProcessingJob, User
from ..repositories import JobRepository
from ..schemas.processing import ArtifactResponse
from ..storage import StorageBackend, build_storage, random_key
from ..utils.errors import NotFoundError, ValidationError
from ..utils.helpers import truncate
from .image_service import ImageService
from .ml_client import MLServiceClient

logger = logging.getLogger("backend.processing_service")

#: Mapping of the ML artefact kinds onto the storage prefix.
_ARTIFACT_PREFIX = {
    "roi": "artifacts/roi",
    "enhanced": "artifacts/enhanced",
    "difference": "artifacts/difference",
    "feature_matches": "artifacts/matches",
    "landmark_overlay": "artifacts/landmarks",
}


class ProcessingService:
    """Runs processing pipelines and persists their results."""

    def __init__(
        self,
        session: Session,
        *,
        ml_client: MLServiceClient | None = None,
        storage: StorageBackend | None = None,
    ) -> None:
        self._session = session
        self._jobs = JobRepository(session)
        self._storage = storage or build_storage()
        self._ml_client = ml_client or MLServiceClient()

    # -- helpers ---------------------------------------------------------
    def _require_image(self, image_id: str, owner: User) -> ImageRecord:
        from ..models import ImageRecord as ImageModel

        image = self._session.get(ImageModel, image_id)
        if image is None or image.deleted_at is not None:
            raise NotFoundError(f"Image '{image_id}' was not found.")
        if image.owner_id != owner.id:
            raise NotFoundError(f"Image '{image_id}' was not found.")
        return image

    def _store_artifacts(self, payload: dict[str, Any]) -> list[ArtifactResponse]:
        """Download the artefacts produced by the ML service and store them."""
        artifacts: list[ArtifactResponse] = []
        for artifact in payload.get("artifacts", []):
            artifact_id = artifact.get("id")
            if not artifact_id:
                continue
            try:
                data = self._ml_client.download_artifact(artifact_id)
            except Exception:
                logger.warning("Could not download artefact %s", artifact_id)
                continue
            kind = str(artifact.get("kind", "output"))
            prefix = _ARTIFACT_PREFIX.get(kind, "artifacts/other")
            key = random_key(prefix, ".png")
            self._storage.save(key, data)
            artifacts.append(
                ArtifactResponse(
                    id=key,
                    kind=kind,
                    media_type=str(artifact.get("media_type", "image/png")),
                    size_bytes=len(data),
                    download_url=f"/api/v1/artifacts/{key}",
                )
            )
        return artifacts

    def _record_job(
        self,
        *,
        owner: User,
        image_id: str | None,
        operation: str,
        algorithm: str,
        algorithm_version: str | None,
        parameters: dict[str, Any],
        payload: dict[str, Any] | None,
        duration_ms: float,
        status: str = "succeeded",
        error_code: str | None = None,
        error_message: str | None = None,
    ) -> ProcessingJob:
        job = self._jobs.create(
            owner_id=owner.id,
            image_id=image_id,
            operation=operation,
            algorithm=algorithm,
            algorithm_version=algorithm_version,
            status=status,
            parameters_json=json.dumps(parameters, default=str),
            result_json=json.dumps(payload or {}, default=str),
            metrics_json=json.dumps((payload or {}).get("metrics", {}), default=str),
            warnings_json=json.dumps((payload or {}).get("warnings", []), default=str),
            duration_ms=duration_ms,
            error_code=error_code,
            error_message=truncate(error_message) if error_message else None,
        )
        from ..models import utcnow

        job.completed_at = utcnow()
        self._session.flush()
        return job

    # -- operations ------------------------------------------------------
    def run_roi(
        self,
        *,
        image_id: str,
        owner: User,
        algorithm: str = "classical_contour_roi",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        image = self._require_image(image_id, owner)
        data = self._image_service().load_bytes(image)
        payload = self._ml_client.extract_roi(
            data,
            filename=image.original_filename,
            content_type=image.media_type,
            algorithm=algorithm,
            parameters=parameters or {},
        )
        return self._finalise(
            payload,
            owner=owner,
            image=image,
            operation="roi",
            algorithm=algorithm,
            parameters=parameters or {},
        )

    def run_enhancement(
        self,
        *,
        image_id: str,
        owner: User,
        algorithm: str = "clahe",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        image = self._require_image(image_id, owner)
        data = self._image_service().load_bytes(image)
        payload = self._ml_client.apply_enhancement(
            data,
            filename=image.original_filename,
            content_type=image.media_type,
            algorithm=algorithm,
            parameters=parameters or {},
        )
        return self._finalise(
            payload,
            owner=owner,
            image=image,
            operation="enhancement",
            algorithm=algorithm,
            parameters=parameters or {},
        )

    def run_quality(self, *, image_id: str, owner: User) -> dict[str, Any]:
        image = self._require_image(image_id, owner)
        data = self._image_service().load_bytes(image)
        payload = self._ml_client.analyze_quality(
            data, filename=image.original_filename, content_type=image.media_type
        )
        return self._finalise(
            payload,
            owner=owner,
            image=image,
            operation="quality",
            algorithm="quality_report",
            parameters={},
        )

    def run_features(
        self,
        *,
        image_id: str,
        owner: User,
        detector: str = "orb",
        n_features: int | None = None,
    ) -> dict[str, Any]:
        image = self._require_image(image_id, owner)
        data = self._image_service().load_bytes(image)
        payload = self._ml_client.extract_features(
            data,
            filename=image.original_filename,
            content_type=image.media_type,
            detector=detector,
            n_features=n_features,
        )
        return self._finalise(
            payload,
            owner=owner,
            image=image,
            operation="features",
            algorithm=detector,
            parameters={"detector": detector, "n_features": n_features},
        )

    def run_landmarks(
        self,
        *,
        image_id: str,
        owner: User,
        detector: str = "orb",
        max_points: int | None = None,
    ) -> dict[str, Any]:
        image = self._require_image(image_id, owner)
        data = self._image_service().load_bytes(image)
        payload = self._ml_client.visualize_landmarks(
            data,
            filename=image.original_filename,
            content_type=image.media_type,
            detector=detector,
            max_points=max_points,
        )
        return self._finalise(
            payload,
            owner=owner,
            image=image,
            operation="landmarks",
            algorithm=detector,
            parameters={"detector": detector, "max_points": max_points},
        )

    def run_comparison(self, *, image_a_id: str, image_b_id: str, owner: User) -> dict[str, Any]:
        first = self._require_image(image_a_id, owner)
        second = self._require_image(image_b_id, owner)
        data_a = self._image_service().load_bytes(first)
        data_b = self._image_service().load_bytes(second)
        payload = self._ml_client.compare_images(
            data_a,
            data_b,
            filename_a=first.original_filename,
            filename_b=second.original_filename,
            content_type_a=first.media_type,
            content_type_b=second.media_type,
        )
        return self._finalise(
            payload,
            owner=owner,
            image=first,
            operation="comparison",
            algorithm="image_difference",
            parameters={"image_b_id": image_b_id},
        )

    def run_recognition(
        self,
        *,
        image_a_id: str,
        image_b_id: str,
        owner: User,
        detector: str = "orb",
        lowe_ratio: float | None = None,
    ) -> dict[str, Any]:
        first = self._require_image(image_a_id, owner)
        second = self._require_image(image_b_id, owner)
        data_a = self._image_service().load_bytes(first)
        data_b = self._image_service().load_bytes(second)
        payload = self._ml_client.compare_recognition(
            data_a,
            data_b,
            filename_a=first.original_filename,
            filename_b=second.original_filename,
            content_type_a=first.media_type,
            content_type_b=second.media_type,
            detector=detector,
            lowe_ratio=lowe_ratio,
        )
        return self._finalise(
            payload,
            owner=owner,
            image=first,
            operation="recognition",
            algorithm=detector,
            parameters={
                "image_b_id": image_b_id,
                "detector": detector,
                "lowe_ratio": lowe_ratio,
            },
        )

    def run_evaluation(
        self,
        *,
        scores: list[float],
        labels: list[int],
        thresholds: list[float] | None = None,
    ) -> dict[str, Any]:
        """Compute evaluation metrics from labelled comparison scores."""
        if len(scores) != len(labels):
            raise ValidationError(
                "The number of scores and labels must be identical.",
                code="invalid_evaluation_request",
                details={"scores": len(scores), "labels": len(labels)},
            )
        payload = self._ml_client.run_evaluation(
            scores=scores, labels=labels, thresholds=thresholds
        )
        return payload

    # -- internals -------------------------------------------------------
    def _image_service(self) -> ImageService:
        return ImageService(self._session, storage=self._storage, ml_client=self._ml_client)

    def _finalise(
        self,
        payload: dict[str, Any],
        *,
        owner: User,
        image: ImageRecord,
        operation: str,
        algorithm: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        algorithm_info = payload.get("algorithm") or {}
        duration = float(payload.get("processing_time_ms", 0.0))
        artifacts = self._store_artifacts(payload)
        recorded_payload = {
            **payload,
            "artifacts": [artifact.model_dump() for artifact in artifacts],
        }

        job = self._record_job(
            owner=owner,
            image_id=image.id,
            operation=operation,
            algorithm=str(algorithm_info.get("name") or algorithm),
            algorithm_version=algorithm_info.get("version"),
            parameters=parameters,
            payload=recorded_payload,
            duration_ms=duration,
        )

        return {
            "job_id": job.id,
            "operation": operation,
            "algorithm": str(algorithm_info.get("name") or algorithm),
            "algorithm_version": algorithm_info.get("version"),
            "image_id": image.id,
            "processing_time_ms": duration,
            "metrics": payload.get("metrics", {}),
            "result": payload.get(operation, {}) or payload.get("recognition", {}) or {},
            "artifacts": artifacts,
            "warnings": list(payload.get("warnings", [])),
            "limitations": list(payload.get("limitations", [])),
        }


__all__ = ["ProcessingService"]
