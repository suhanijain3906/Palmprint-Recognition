"""Health and meta endpoints."""

from __future__ import annotations


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"ok", "degraded"}
    assert payload["service"]
    assert payload["database"] == "ok"
    assert "ml_service" in payload


def test_ready_endpoint(client) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_openapi_document(client) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for expected in (
        "/api/v1/images",
        "/api/v1/images/upload",
        "/api/v1/processing/roi",
        "/api/v1/processing/enhancement",
        "/api/v1/processing/quality",
        "/api/v1/recognition/compare",
        "/api/v1/comparison",
        "/api/v1/experiments",
        "/api/v1/datasets",
        "/api/v1/reports/{report_id}",
        "/api/v1/reports/{report_id}/download",
    ):
        assert expected in paths, f"missing endpoint {expected}"


def test_auth_mode_is_reported(client) -> None:
    response = client.get("/api/v1/auth/mode")
    assert response.status_code == 200
    payload = response.json()
    assert payload["auth_enabled"] is False
    assert payload["mode"] == "academic_demo"
    assert "demo" in payload["message"].lower()
