"""End-to-end tests of the ML service HTTP API."""

from __future__ import annotations

import numpy as np

from tests.conftest import encode_png


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert "uptime_seconds" in payload
    assert payload["trained_models"]["trained_model_available"] is False


def test_openapi_document_is_available(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/roi/extract" in paths
    assert "/api/v1/recognition/compare" in paths


def test_validate_endpoint_accepts_png(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/validate", files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["validation"]["detected_format"] == "PNG"
    assert payload["validation"]["width"] == 320


def test_validate_endpoint_rejects_non_image(client) -> None:
    response = client.post(
        "/api/v1/validate", files={"file": ("notes.txt", b"hello world", "text/plain")}
    )
    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_media_type"


def test_validate_endpoint_rejects_empty_file(client) -> None:
    response = client.post("/api/v1/validate", files={"file": ("empty.png", b"", "image/png")})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "empty_upload"


def test_roi_endpoint_returns_an_artifact(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/roi/extract", files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["artifacts"], "expected an ROI artefact"
    artifact = payload["artifacts"][0]
    assert artifact["download_path"].startswith("/api/v1/artifacts/")

    download = client.get(artifact["download_path"])
    assert download.status_code == 200
    assert download.headers["content-type"].startswith("image/")


def test_artifact_download_for_unknown_id(client) -> None:
    response = client.get("/api/v1/artifacts/does-not-exist")
    assert response.status_code == 404


def test_enhancement_endpoint(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/enhancement/apply",
        files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
        data={"algorithm": "clahe", "clip_limit": "2.5"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["enhancement"]["parameters"]["clip_limit"] == 2.5
    assert payload["artifacts"]


def test_enhancement_endpoint_rejects_bad_parameter(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/enhancement/apply",
        files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
        data={"algorithm": "clahe", "clip_limit": "500"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_parameter"


def test_quality_endpoint(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/quality/analyze",
        files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert 0 <= payload["quality"]["combined_score"] <= 100
    assert payload["quality"]["combined_score_is_experimental"] is True


def test_features_endpoint(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/features/extract",
        files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
        data={"detector": "orb", "n_features": "300"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["features"]["keypoint_count"] >= 0


def test_recognition_endpoint(client, synthetic_palm: np.ndarray) -> None:
    payload_bytes = encode_png(synthetic_palm)
    response = client.post(
        "/api/v1/recognition/compare",
        files={
            "image_a": ("a.png", payload_bytes, "image/png"),
            "image_b": ("b.png", payload_bytes, "image/png"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["recognition"]["is_calibrated_probability"] is False
    assert payload["recognition"]["matcher"]["is_trained_model"] is False
    assert any("No trained recognition model" in warning for warning in payload["warnings"])


def test_recognition_endpoint_requires_two_images(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/recognition/compare",
        files={"image_a": ("a.png", encode_png(synthetic_palm), "image/png")},
    )
    assert response.status_code == 422


def test_landmarks_endpoint(client, synthetic_palm: np.ndarray) -> None:
    response = client.post(
        "/api/v1/landmarks/visualize",
        files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["landmarks"]["is_anatomical"] is False
    assert (
        payload["landmarks"]["anatomical_landmark_model"]["anatomical_landmark_model_available"]
        is False
    )


def test_images_compare_endpoint(client, synthetic_palm: np.ndarray) -> None:
    payload_bytes = encode_png(synthetic_palm)
    response = client.post(
        "/api/v1/images/compare",
        files={
            "image_a": ("a.png", payload_bytes, "image/png"),
            "image_b": ("b.png", payload_bytes, "image/png"),
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison"]["ssim"] == 1.0
    assert payload["artifacts"]


def test_evaluation_endpoint(client) -> None:
    response = client.post(
        "/api/v1/evaluation/run",
        json={"scores": [0.9, 0.85, 0.3, 0.2], "labels": [1, 1, 0, 0]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["evaluation"]["auc"] == 1.0
    assert payload["evaluation"]["counts"]["num_genuine"] == 2


def test_evaluation_endpoint_rejects_mismatched_lengths(client) -> None:
    response = client.post("/api/v1/evaluation/run", json={"scores": [0.9], "labels": [1, 0]})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_evaluation_request"


def test_algorithms_catalogue(client) -> None:
    response = client.get("/api/v1/algorithms")
    assert response.status_code == 200
    payload = response.json()
    assert any(entry["name"] == "classical_contour_roi" for entry in payload["roi"])
    assert payload["trained_models"]["trained_model_available"] is False


def test_service_token_protects_processing_endpoints(
    monkeypatch, synthetic_palm: np.ndarray
) -> None:
    from fastapi.testclient import TestClient

    from app.config import settings
    from app.main import create_app

    monkeypatch.setattr(settings, "service_api_key", "test-service-token")
    guarded_app = create_app()
    with TestClient(guarded_app) as guarded:
        assert guarded.get("/health").status_code == 200
        missing = guarded.post(
            "/api/v1/validate",
            files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
        )
        assert missing.status_code == 401
        assert missing.json()["error"]["code"] == "unauthorized"
        allowed = guarded.post(
            "/api/v1/validate",
            files={"file": ("palm.png", encode_png(synthetic_palm), "image/png")},
            headers={"X-Service-Token": "test-service-token"},
        )
        assert allowed.status_code == 200
