"""Integration tests for the processing, recognition and comparison routes."""

from __future__ import annotations

from tests.conftest import upload_image


def _image_id(client, payload: bytes, filename: str = "palm.png") -> str:
    return upload_image(client, payload, filename=filename)["image"]["id"]


def test_roi_returns_job_and_approximate_flag(client, palm_png: bytes) -> None:
    image_id = _image_id(client, palm_png)
    response = client.post("/api/v1/processing/roi", json={"image_id": image_id})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["job_id"]
    assert body["operation"] == "roi"
    assert body["result"]["is_approximate"] is True
    assert body["artifacts"]
    assert body["warnings"], "the approximate ROI must always carry a warning"


def test_roi_artifact_can_be_downloaded(client, palm_png: bytes) -> None:
    image_id = _image_id(client, palm_png)
    response = client.post("/api/v1/processing/roi", json={"image_id": image_id})
    assert response.status_code == 200, response.text

    artifact_url = response.json()["artifacts"][0]["download_url"]
    download = client.get(artifact_url)
    assert download.status_code == 200, download.text
    assert download.headers["content-type"] == "image/png"
    assert download.content


def test_enhancement_records_algorithm_and_parameters(client, palm_png: bytes) -> None:
    image_id = _image_id(client, palm_png)
    response = client.post(
        "/api/v1/processing/enhancement",
        json={"image_id": image_id, "algorithm": "clahe", "parameters": {"clip_limit": 2.0}},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["algorithm"] == "clahe"
    assert body["artifacts"]
    assert body["result"]["parameters"]["clip_limit"] == 2.0


def test_quality_returns_measured_metrics(client, palm_png: bytes) -> None:
    image_id = _image_id(client, palm_png)
    response = client.post("/api/v1/processing/quality", json={"image_id": image_id})
    assert response.status_code == 200, response.text
    body = response.json()
    quality = body["result"]
    assert quality["combined_score_is_experimental"] is True
    assert "brightness" in quality
    assert quality["dimensions"]["width"] == 240


def test_processing_rejects_unknown_image(client) -> None:
    response = client.post("/api/v1/processing/quality", json={"image_id": "0" * 32})
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_recognition_returns_uncalibrated_similarity(
    client, palm_png: bytes, palm_png_b: bytes
) -> None:
    image_a = _image_id(client, palm_png, "a.png")
    image_b = _image_id(client, palm_png_b, "b.png")
    response = client.post(
        "/api/v1/recognition/compare",
        json={"image_a_id": image_a, "image_b_id": image_b},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["similarity_score"] is not None
    assert body["score_kind"] == "uncalibrated_similarity_index"
    assert body["is_trained_model"] is False
    assert body["is_calibrated_probability"] is False
    assert body["trained_model_available"] is False
    assert body["warnings"]


def test_comparison_returns_pixel_metrics_and_difference(
    client, palm_png: bytes, palm_png_b: bytes
) -> None:
    image_a = _image_id(client, palm_png, "a.png")
    image_b = _image_id(client, palm_png_b, "b.png")
    response = client.post(
        "/api/v1/comparison", json={"image_a_id": image_a, "image_b_id": image_b}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["psnr_db"] is not None
    assert body["ssim"] is not None
    assert body["artifacts"][0]["kind"] == "difference"
    assert any("PSNR" in item for item in body["limitations"])


def test_features_and_landmarks_are_marked_as_non_anatomical(client, palm_png: bytes) -> None:
    image_id = _image_id(client, palm_png)
    features = client.post("/api/v1/processing/features", json={"image_id": image_id})
    assert features.status_code == 200, features.text

    landmarks = client.post("/api/v1/processing/landmarks", json={"image_id": image_id})
    assert landmarks.status_code == 200, landmarks.text
    body = landmarks.json()
    assert body["result"]["anatomical_landmark_model"]["trained_model_available"] is False
    assert body["result"]["is_anatomical"] is False


def test_processing_returns_503_when_ml_service_is_down(
    client, palm_png: bytes, monkeypatch
) -> None:
    from tests.conftest import StubMLClient

    image_id = _image_id(client, palm_png)
    unavailable = StubMLClient(available=False)
    monkeypatch.setattr(
        "app.services.processing_service.MLServiceClient", lambda *a, **k: unavailable
    )
    response = client.post("/api/v1/processing/quality", json={"image_id": image_id})
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "service_unavailable"
