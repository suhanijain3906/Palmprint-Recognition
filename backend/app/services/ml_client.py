"""HTTP client for the ML service.

The backend is the only component that talks to the ML service; the browser
never receives ML service credentials or URLs.

Error handling
--------------
* Connection problems raise :class:`ServiceUnavailableError` (HTTP 503).
* Timeouts raise :class:`UpstreamTimeoutError` (HTTP 504).
* Validation problems reported by the ML service are mapped to
  :class:`ValidationError` (HTTP 422) and keep the upstream error code.
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from ..core.config import settings
from ..utils.errors import (
    ServiceUnavailableError,
    UpstreamTimeoutError,
    ValidationError,
)

logger = logging.getLogger("backend.ml_client")

#: Media types accepted by the ML service.
ACCEPTED_MEDIA_TYPES = ("image/png", "image/jpeg", "image/bmp", "image/tiff", "image/webp")

#: Mapping of the ML service error codes onto backend error codes.
_ERROR_CODE_MAP = {
    "invalid_image": "invalid_image",
    "unsupported_media_type": "unsupported_media_type",
    "payload_too_large": "payload_too_large",
    "empty_upload": "empty_upload",
    "invalid_parameter": "invalid_parameter",
    "insufficient_features": "insufficient_features",
    "invalid_evaluation_request": "invalid_evaluation_request",
    "artifact_not_found": "artifact_not_found",
}


class MLServiceClient:
    """Thin, synchronous client around the ML service HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        *,
        timeout: float | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.ml_service_url).rstrip("/")
        self.timeout = timeout if timeout is not None else settings.ml_service_timeout
        self.api_key = api_key if api_key is not None else settings.ml_service_api_key
        self._client = httpx.Client(timeout=httpx.Timeout(self.timeout))

    # -- infrastructure --------------------------------------------------
    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> MLServiceClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["X-Service-Token"] = self.api_key
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        files: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = self._client.request(
                method,
                url,
                files=files,
                data=data,
                json=json_body,
                headers=self._headers(),
            )
        except httpx.TimeoutException as exc:
            logger.warning("ML service timeout for %s %s", method, path)
            raise UpstreamTimeoutError(
                "The ML service did not answer in time. "
                "Please retry or reduce the size of the input.",
                details={"path": path, "timeout_seconds": self.timeout},
            ) from exc
        except httpx.HTTPError as exc:
            logger.warning("ML service unavailable for %s %s: %s", method, path, exc)
            raise ServiceUnavailableError(
                "The ML processing service is currently unavailable.",
                details={"path": path, "reason": str(exc)},
            ) from exc

        if response.status_code >= 400:
            self._raise_for_error(response, path)

        try:
            return response.json()
        except (json.JSONDecodeError, ValueError) as exc:
            raise ServiceUnavailableError(
                "The ML service returned an unreadable response.",
                details={"path": path},
            ) from exc

    def _raise_for_error(self, response: httpx.Response, path: str) -> None:
        code = "upstream_error"
        message = "The ML service rejected the request."
        details: dict[str, Any] = {}
        try:
            payload = response.json()
            error = payload.get("error", {}) if isinstance(payload, dict) else {}
            code = error.get("code", code)
            message = error.get("message", message)
            details = error.get("details", {}) or {}
        except (json.JSONDecodeError, ValueError):
            details = {"upstream_status": response.status_code}

        mapped = _ERROR_CODE_MAP.get(code, code)
        if response.status_code in (400, 413, 415, 422):
            raise ValidationError(
                message, code=mapped, details={**details, "upstream_status": response.status_code}
            )
        raise ServiceUnavailableError(
            message, code=mapped, details={**details, "upstream_status": response.status_code}
        )

    # -- endpoints -------------------------------------------------------
    def health(self) -> dict[str, Any]:
        """Return the health payload of the ML service."""
        return self._request("GET", "/health")

    def validate(self, data: bytes, *, filename: str, content_type: str) -> dict[str, Any]:
        """Ask the ML service to validate an image payload."""
        return self._request(
            "POST",
            f"{settings.api_prefix}/validate",
            files={"file": (filename, data, content_type)},
        )

    def extract_roi(
        self,
        data: bytes,
        *,
        filename: str,
        content_type: str,
        algorithm: str = "classical_contour_roi",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the ROI extraction pipeline."""
        form = {"algorithm": algorithm}
        for key, value in (parameters or {}).items():
            if value is not None:
                form[key] = str(value)
        return self._request(
            "POST",
            f"{settings.api_prefix}/roi/extract",
            files={"file": (filename, data, content_type)},
            data=form,
        )

    def apply_enhancement(
        self,
        data: bytes,
        *,
        filename: str,
        content_type: str,
        algorithm: str = "clahe",
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run the enhancement pipeline."""
        form = {"algorithm": algorithm}
        for key, value in (parameters or {}).items():
            if value is not None:
                form[key] = str(value)
        return self._request(
            "POST",
            f"{settings.api_prefix}/enhancement/apply",
            files={"file": (filename, data, content_type)},
            data=form,
        )

    def analyze_quality(self, data: bytes, *, filename: str, content_type: str) -> dict[str, Any]:
        """Run the quality assessment."""
        return self._request(
            "POST",
            f"{settings.api_prefix}/quality/analyze",
            files={"file": (filename, data, content_type)},
        )

    def extract_features(
        self,
        data: bytes,
        *,
        filename: str,
        content_type: str,
        detector: str = "orb",
        n_features: int | None = None,
    ) -> dict[str, Any]:
        """Run the feature extraction pipeline."""
        form: dict[str, Any] = {"detector": detector}
        if n_features is not None:
            form["n_features"] = str(n_features)
        return self._request(
            "POST",
            f"{settings.api_prefix}/features/extract",
            files={"file": (filename, data, content_type)},
            data=form,
        )

    def compare_recognition(
        self,
        data_a: bytes,
        data_b: bytes,
        *,
        filename_a: str,
        filename_b: str,
        content_type_a: str,
        content_type_b: str,
        detector: str = "orb",
        lowe_ratio: float | None = None,
    ) -> dict[str, Any]:
        """Run the experimental recognition comparison."""
        form: dict[str, Any] = {"detector": detector}
        if lowe_ratio is not None:
            form["lowe_ratio"] = str(lowe_ratio)
        return self._request(
            "POST",
            f"{settings.api_prefix}/recognition/compare",
            files={
                "image_a": (filename_a, data_a, content_type_a),
                "image_b": (filename_b, data_b, content_type_b),
            },
            data=form,
        )

    def visualize_landmarks(
        self,
        data: bytes,
        *,
        filename: str,
        content_type: str,
        detector: str = "orb",
        max_points: int | None = None,
    ) -> dict[str, Any]:
        """Render the feature point overlay."""
        form: dict[str, Any] = {"detector": detector}
        if max_points is not None:
            form["max_points"] = str(max_points)
        return self._request(
            "POST",
            f"{settings.api_prefix}/landmarks/visualize",
            files={"file": (filename, data, content_type)},
            data=form,
        )

    def compare_images(
        self,
        data_a: bytes,
        data_b: bytes,
        *,
        filename_a: str,
        filename_b: str,
        content_type_a: str,
        content_type_b: str,
    ) -> dict[str, Any]:
        """Run the pixel level image comparison."""
        return self._request(
            "POST",
            f"{settings.api_prefix}/images/compare",
            files={
                "image_a": (filename_a, data_a, content_type_a),
                "image_b": (filename_b, data_b, content_type_b),
            },
        )

    def run_evaluation(
        self, *, scores: list[float], labels: list[int], thresholds: list[float] | None = None
    ) -> dict[str, Any]:
        """Compute biometric evaluation metrics from labelled scores."""
        body: dict[str, Any] = {"scores": scores, "labels": labels}
        if thresholds:
            body["thresholds"] = thresholds
        return self._request("POST", f"{settings.api_prefix}/evaluation/run", json_body=body)

    def download_artifact(self, artifact_id: str) -> bytes:
        """Download a generated artefact from the ML service."""
        url = f"{self.base_url}{settings.api_prefix}/artifacts/{artifact_id}"
        try:
            response = self._client.get(url, headers=self._headers(), timeout=self.timeout)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeoutError(
                "The ML service did not answer in time while streaming an artefact.",
                details={"artifact_id": artifact_id},
            ) from exc
        except httpx.HTTPError as exc:
            raise ServiceUnavailableError(
                "The ML service is unavailable while streaming an artefact.",
                details={"artifact_id": artifact_id},
            ) from exc

        if response.status_code == 404:
            raise ValidationError(
                "The generated artefact is no longer available.",
                code="artifact_not_found",
                details={"artifact_id": artifact_id},
            )
        if response.status_code >= 400:
            raise ServiceUnavailableError(
                "The ML service could not deliver the artefact.",
                details={"artifact_id": artifact_id, "upstream_status": response.status_code},
            )
        return response.content

    def algorithms(self) -> dict[str, Any]:
        """Return the algorithm catalogue of the ML service."""
        return self._request("GET", f"{settings.api_prefix}/algorithms")


def get_ml_client() -> MLServiceClient:
    """Return a new client instance."""
    return MLServiceClient()


__all__ = ["ACCEPTED_MEDIA_TYPES", "MLServiceClient", "get_ml_client"]
