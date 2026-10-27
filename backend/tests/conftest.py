"""Shared fixtures of the backend test suite.

The tests use a temporary SQLite database and a temporary storage directory.
The ML service is replaced by a stub that mimics the documented behaviour of
the real service, so that the backend can be tested in isolation and
deterministically.  A dedicated test verifies the behaviour when the real ML
service is unreachable.
"""

from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image

_TEST_ROOT = Path(tempfile.gettempdir()) / "palmprint-backend-tests"
_TEST_ROOT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(_TEST_ROOT / 'test.db').as_posix()}")
os.environ.setdefault("STORAGE_ROOT", str(_TEST_ROOT / "storage"))
os.environ.setdefault("AUTH_ENABLED", "false")
os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("ML_SERVICE_URL", "http://ml-service.test:8001")
os.environ.setdefault("ML_SERVICE_TIMEOUT", "5")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import engine as app_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Base  # noqa: E402
from app.services.ml_client import MLServiceClient  # noqa: E402


def make_synthetic_palm(width: int = 240, height: int = 240, *, seed: int = 3) -> np.ndarray:
    """Create a synthetic palm-like test image (no real biometric data)."""
    rng = np.random.default_rng(seed)
    background = np.clip(
        np.full((height, width, 3), 30, dtype=np.int16) + rng.normal(0, 5, (height, width, 3)),
        0,
        255,
    ).astype(np.uint8)

    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    cx, cy = width / 2.0, height / 2.0
    ellipse = ((xx - cx) / (width * 0.35)) ** 2 + ((yy - cy) / (height * 0.4)) ** 2
    mask = (ellipse <= 1.0).astype(np.float32)
    # Simple blur approximation without OpenCV dependency in tests
    mask_pad = np.pad(mask, 4, mode="edge")
    blurred = np.zeros_like(mask)
    for r in range(height):
        for c in range(width):
            window = mask_pad[r : r + 9, c : c + 9]
            blurred[r, c] = window.sum() / 81.0
    mask = blurred

    radial = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    orientation = np.arctan2(yy - cy, xx - cx)
    texture = 120 + 55 * (0.5 + 0.5 * np.sin(radial * 1.4 + orientation * 0.6))
    palm = np.stack([texture, texture * 0.93, texture * 0.85], axis=-1)
    alpha = mask[..., None]
    return (palm * alpha + background * (1.0 - alpha)).astype(np.uint8)


def encode_png(image: np.ndarray) -> bytes:
    pil = Image.fromarray(image.astype(np.uint8))
    buffer = io.BytesIO()
    pil.save(buffer, format="PNG")
    return buffer.getvalue()


class StubMLClient(MLServiceClient):
    """In-process replacement of the HTTP ML client."""

    def __init__(self, *, available: bool = True) -> None:
        self._available = available
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        self.calls.append((path, kwargs))
        if not self._available:
            from app.utils.errors import ServiceUnavailableError

            raise ServiceUnavailableError("The ML processing service is currently unavailable.")
        return _stub_response(path, kwargs)

    def download_artifact(self, artifact_id: str) -> bytes:
        return encode_png(make_synthetic_palm(64, 64, seed=5))


def _stub_response(path: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    """Return a payload that mimics the real ML service."""
    if path.endswith("/health"):
        return {
            "status": "ok",
            "service": "Palmprint ML Service",
            "version": "0.1.0",
            "uptime_seconds": 12.0,
            "trained_models": {"trained_model_available": False},
        }

    if path.endswith("/validate"):
        files = kwargs.get("files") or {}
        file_info = next(iter(files.values()))
        payload = file_info[1]
        filename = file_info[0]
        if not payload:
            from app.utils.errors import ValidationError

            raise ValidationError("The uploaded file is empty.", code="empty_upload")
        # Check if it's a text file
        try:
            if payload[:100].strip().startswith(b"not an image") or (b"not an" in payload[:20]):
                from app.utils.errors import ValidationError

                raise ValidationError("The file is not a valid image.", code="invalid_image")
        except Exception:
            pass
        # Try to decode as image
        try:
            import io

            from PIL import Image

            img = Image.open(io.BytesIO(payload))
            img.verify()
            img = Image.open(io.BytesIO(payload))  # verify closes file
            width, height = img.size
            fmt = (img.format or "PNG").upper()
            media = (
                f"image/{fmt.lower()}"
                if fmt.lower() in ("png", "jpeg", "jpg", "bmp", "tiff", "webp")
                else "image/png"
            )
            if media == "image/jpg":
                media = "image/jpeg"
            return {
                "status": "success",
                "processing_time_ms": 1.0,
                "validation": {
                    "filename": filename,
                    "declared_content_type": None,
                    "detected_media_type": media,
                    "detected_format": fmt,
                    "width": width,
                    "height": height,
                    "channels": len(img.getbands()),
                    "size_bytes": len(payload),
                    "pixel_count": width * height,
                    "extension_matches": True,
                    "warnings": [],
                },
            }
        except Exception:
            from app.utils.errors import ValidationError

            raise ValidationError("The file is not a valid image.", code="invalid_image")

    if path.endswith("/roi/extract"):
        return {
            "status": "success",
            "algorithm": {"name": "classical_contour_roi", "version": "1.1.0", "anatomical": False},
            "processing_time_ms": 12.5,
            "metrics": {"bbox_width": 100, "bbox_height": 120, "coverage_ratio": 0.42},
            "result": {},
            "roi": {
                "bbox": {"x": 10, "y": 12, "width": 100, "height": 120},
                "confidence": 0.62,
                "is_approximate": True,
                "method": "classical_contour_roi",
            },
            "artifacts": [
                {
                    "id": "roi-artifact",
                    "kind": "roi",
                    "media_type": "image/png",
                    "size_bytes": 100,
                    "download_path": "/api/v1/artifacts/roi-artifact",
                }
            ],
            "warnings": ["The extracted region is an approximate proposal."],
            "limitations": ["Not an anatomical palm ROI."],
        }

    if path.endswith("/enhancement/apply"):
        return {
            "status": "success",
            "algorithm": {"name": "clahe", "version": "1.0.0"},
            "processing_time_ms": 8.0,
            "metrics": {"algorithm": "clahe", "parameters": {"clip_limit": 2.0}},
            "enhancement": {
                "algorithm": "clahe",
                "parameters": {"clip_limit": 2.0, "tile_grid_size": 8},
                "output_width": 240,
                "output_height": 240,
            },
            "artifacts": [
                {
                    "id": "enhanced-artifact",
                    "kind": "enhanced",
                    "media_type": "image/png",
                    "size_bytes": 100,
                    "download_path": "/api/v1/artifacts/enhanced-artifact",
                }
            ],
            "warnings": [],
            "limitations": ["CLAHE parameters are not comparable across settings."],
        }

    if path.endswith("/quality/analyze"):
        return {
            "status": "success",
            "algorithm": {"name": "quality_report", "version": "1.0.0"},
            "processing_time_ms": 6.0,
            "metrics": {"combined_score": 61.5},
            "quality": {
                "brightness": {"mean_intensity": 120.0},
                "contrast": {"rms_contrast": 0.22},
                "sharpness": {"variance_of_laplacian": 240.0},
                "dimensions": {"width": 240, "height": 240, "megapixels": 0.0576},
                "sub_scores": {
                    "exposure": 0.94,
                    "contrast": 0.88,
                    "sharpness": 0.48,
                    "resolution": 0.0576,
                },
                "weights": {
                    "exposure": 0.3,
                    "contrast": 0.3,
                    "sharpness": 0.3,
                    "resolution": 0.1,
                },
                "combined_score": 61.5,
                "combined_score_is_experimental": True,
                "warnings": [],
                "limitations": ["The combined score is an unvalidated heuristic."],
            },
            "artifacts": [],
            "warnings": [],
            "limitations": ["The combined score is an unvalidated heuristic."],
        }

    if path.endswith("/features/extract"):
        return {
            "status": "success",
            "algorithm": {"name": "orb", "version": "1.0.0"},
            "processing_time_ms": 18.0,
            "metrics": {"keypoint_count": 120, "descriptor_count": 120},
            "features": {
                "detector": "orb",
                "keypoint_count": 120,
                "descriptor_count": 120,
                "is_trained_model": False,
                "warnings": ["ORB features are generic local descriptors."],
                "limitations": ["Not a specialised palmprint descriptor."],
            },
            "artifacts": [],
            "warnings": ["ORB features are generic local descriptors."],
            "limitations": ["Not a specialised palmprint descriptor."],
        }

    if path.endswith("/landmarks/visualize"):
        return {
            "status": "success",
            "algorithm": {"name": "orb_feature_points", "version": "1.0.0"},
            "processing_time_ms": 21.0,
            "metrics": {"point_count": 3},
            "landmarks": {
                "method": "orb_feature_points",
                "is_anatomical": False,
                "keypoint_count": 3,
                "points": [{"x": 10, "y": 12}, {"x": 30, "y": 42}, {"x": 50, "y": 60}],
                "anatomical_landmark_model": {
                    "trained_model_available": False,
                    "message": "No trained anatomical landmark model is installed.",
                },
                "warnings": ["These are generic keypoints, not palm landmarks."],
                "limitations": ["Anatomical landmarks require a trained model."],
            },
            "artifacts": [
                {
                    "id": "landmark-artifact",
                    "kind": "landmark_overlay",
                    "media_type": "image/png",
                    "size_bytes": 100,
                    "download_path": "/api/v1/artifacts/landmark-artifact",
                }
            ],
            "warnings": ["These are generic keypoints, not palm landmarks."],
            "limitations": ["Anatomical landmarks require a trained model."],
        }

    if path.endswith("/recognition/compare"):
        return {
            "status": "success",
            "algorithm": {"name": "classical_orb_matcher", "version": "1.0.0"},
            "processing_time_ms": 30.0,
            "metrics": {"good_matches": 42, "match_coverage": 0.63},
            "recognition": {
                "similarity_score": 0.63,
                "score_kind": "uncalibrated_similarity_index",
                "available": True,
                "matcher": {
                    "name": "classical_orb_matcher",
                    "version": "1.0.0",
                    "is_trained_model": False,
                },
                "is_calibrated_probability": False,
                "trained_model_available": False,
                "details": {"good_matches": 42},
                "warnings": ["The score is uncalibrated."],
                "limitations": ["No trained biometric model is involved."],
            },
            "artifacts": [],
            "warnings": ["No trained recognition model is installed in this deployment."],
            "limitations": ["No trained biometric model is involved."],
        }

    if path.endswith("/images/compare"):
        return {
            "status": "success",
            "algorithm": {"name": "image_difference", "version": "1.0.0"},
            "processing_time_ms": 15.0,
            "metrics": {"ssim": 0.87, "psnr_db": 22.5},
            "comparison": {
                "psnr_db": 22.5,
                "ssim": 0.87,
                "aligned": True,
                "resized": False,
                "first_width": 240,
                "second_width": 240,
            },
            "artifacts": [
                {
                    "id": "difference-artifact",
                    "kind": "difference",
                    "media_type": "image/png",
                    "size_bytes": 100,
                    "download_path": "/api/v1/artifacts/difference-artifact",
                }
            ],
            "warnings": [],
            "limitations": ["PSNR and SSIM are pixel similarity metrics."],
        }

    if path.endswith("/evaluation/run"):
        body = kwargs.get("json_body") or {}
        scores = body.get("scores", [])
        labels = body.get("labels", [])
        return {
            "status": "success",
            "algorithm": {"name": "biometric_evaluation", "version": "1.0.0"},
            "processing_time_ms": 2.0,
            "metrics": {"auc": 1.0},
            "evaluation": {
                "scores": scores,
                "labels": labels,
                "roc": {"thresholds": [1.0, 0.0], "tpr": [0.0, 1.0], "fpr": [0.0, 1.0]},
                "auc": 1.0,
                "far": {"points": []},
                "frr": {"points": []},
                "eer": {"eer": 0.0, "threshold": 0.5},
                "counts": {
                    "num_comparisons": len(scores),
                    "num_genuine": sum(1 for label in labels if label == 1),
                    "num_impostor": sum(1 for label in labels if label == 0),
                },
                "warnings": ["Verify subject level separation yourself."],
                "limitations": ["Scores must come from a held out evaluation set."],
            },
            "warnings": [],
            "limitations": [],
        }

    return {
        "status": "success",
        "algorithm": {"name": "unknown", "version": "1.0.0"},
        "processing_time_ms": 1.0,
        "metrics": {},
        "artifacts": [],
        "warnings": [],
        "limitations": [],
    }


@pytest.fixture(autouse=True)
def _clean_database():
    """Reset the schema before every test."""
    Base.metadata.drop_all(bind=app_engine)
    Base.metadata.create_all(bind=app_engine)
    yield
    Base.metadata.drop_all(bind=app_engine)


@pytest.fixture
def stub_ml(monkeypatch: pytest.MonkeyPatch) -> StubMLClient:
    """Replace the ML client used by the services with the in-process stub."""
    client = StubMLClient()
    monkeypatch.setattr("app.services.image_service.MLServiceClient", lambda *a, **k: client)
    monkeypatch.setattr("app.services.processing_service.MLServiceClient", lambda *a, **k: client)
    monkeypatch.setattr("app.api.dependencies.MLServiceClient", lambda *a, **k: client)
    monkeypatch.setattr("app.api.routes.health.MLServiceClient", lambda *a, **k: client)
    return client


@pytest.fixture
def client(stub_ml: StubMLClient) -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def palm_png() -> bytes:
    return encode_png(make_synthetic_palm())


@pytest.fixture
def palm_png_b() -> bytes:
    return encode_png(make_synthetic_palm(seed=17))


def upload_image(client: TestClient, payload: bytes, filename: str = "palm.png") -> dict:
    """Helper that uploads an image and returns the parsed response."""
    response = client.post(
        "/api/v1/images/upload",
        files={"file": (filename, payload, "image/png")},
    )
    assert response.status_code == 201, response.text
    return response.json()
