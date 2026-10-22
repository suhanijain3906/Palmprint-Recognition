"""Integration tests for experiments and PDF report generation."""

from __future__ import annotations

from tests.conftest import upload_image


def _upload(client, payload: bytes) -> str:
    return upload_image(client, payload)["image"]["id"]


def _run_quality_job(client, image_id: str) -> str:
    response = client.post("/api/v1/processing/quality", json={"image_id": image_id})
    assert response.status_code == 200, response.text
    return response.json()["job_id"]


def test_experiment_runs_and_persists_results(client, palm_png: bytes) -> None:
    image_id = _upload(client, palm_png)
    response = client.post(
        "/api/v1/experiments",
        json={
            "name": "Quality baseline",
            "description": "Single synthetic capture",
            "operation": "quality",
            "algorithm": "quality_report",
            "parameters": {},
            "image_ids": [image_id],
        },
    )
    assert response.status_code == 200, response.text
    experiment = response.json()
    assert experiment["status"] == "completed"
    assert experiment["results"]
    assert any(result["kind"] == "processing_time" for result in experiment["results"])

    listed = client.get("/api/v1/experiments")
    assert listed.status_code == 200
    assert listed.json()["meta"]["total"] == 1

    fetched = client.get(f"/api/v1/experiments/{experiment['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == experiment["id"]

    summary = client.get(f"/api/v1/experiments/{experiment['id']}/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["experiment"]["id"] == experiment["id"]
    assert "recommend" not in payload and "disclaimer" in payload


def test_experiment_requires_images(client) -> None:
    response = client.post(
        "/api/v1/experiments",
        json={
            "name": "Empty",
            "operation": "quality",
            "algorithm": "quality_report",
            "parameters": {},
            "image_ids": [],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "missing_images"


def test_experiment_rejects_unsupported_operation(client, palm_png: bytes) -> None:
    image_id = _upload(client, palm_png)
    response = client.post(
        "/api/v1/experiments",
        json={
            "name": "Unsupported",
            "operation": "deep_learning",
            "algorithm": "siamese",
            "parameters": {},
            "image_ids": [image_id],
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "unsupported_operation"


def test_report_generation_and_download(client, palm_png: bytes) -> None:
    image_id = _upload(client, palm_png)
    job_id = _run_quality_job(client, image_id)

    created = client.post(
        "/api/v1/reports",
        json={
            "title": "Quality report",
            "report_type": "processing",
            "job_ids": [job_id],
            "include_images": False,
        },
    )
    assert created.status_code == 201, created.text
    report = created.json()
    assert report["status"] == "ready"
    assert report["download_url"].endswith("/download")

    listing = client.get("/api/v1/reports")
    assert listing.status_code == 200
    assert listing.json()["meta"]["total"] == 1

    metadata = client.get(f"/api/v1/reports/{report['id']}")
    assert metadata.status_code == 200

    download = client.get(f"/api/v1/reports/{report['id']}/download")
    assert download.status_code == 200
    assert download.headers["content-type"] == "application/pdf"
    assert download.content.startswith(b"%PDF")
    assert len(download.content) > 1000
    assert b"Palmprint" in download.content or b"palmprint" in download.content


def test_report_download_unknown_id_is_404(client) -> None:
    response = client.get("/api/v1/reports/does-not-exist/download")
    assert response.status_code == 404
