"""Access-control tests for the optional authenticated mode."""

from __future__ import annotations

from app.core.config import settings


def _register(client, email: str) -> str:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": email.split("@")[0],
            "password": "correct-horse-battery",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


def test_authenticated_mode_requires_token(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "auth_enabled", True)
    response = client.get("/api/v1/images")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "authentication_required"


def test_images_are_isolated_between_accounts(client, palm_png: bytes, monkeypatch) -> None:
    monkeypatch.setattr(settings, "auth_enabled", True)
    owner = _register(client, "owner@example.org")
    stranger = _register(client, "stranger@example.org")

    upload = client.post(
        "/api/v1/images/upload",
        files={"file": ("palm.png", palm_png, "image/png")},
        headers={"Authorization": f"Bearer {owner}"},
    )
    assert upload.status_code == 201, upload.text
    image_id = upload.json()["image"]["id"]

    allowed = client.get(f"/api/v1/images/{image_id}", headers={"Authorization": f"Bearer {owner}"})
    assert allowed.status_code == 200

    denied = client.get(
        f"/api/v1/images/{image_id}", headers={"Authorization": f"Bearer {stranger}"}
    )
    assert denied.status_code == 404

    denied_delete = client.delete(
        f"/api/v1/images/{image_id}", headers={"Authorization": f"Bearer {stranger}"}
    )
    assert denied_delete.status_code == 404

    # An invalid token must be rejected, never silently accepted.
    invalid = client.get("/api/v1/images", headers={"Authorization": "Bearer not-a-real-token"})
    assert invalid.status_code == 401


def test_auth_mode_endpoint_reports_current_mode(client) -> None:
    response = client.get("/api/v1/auth/mode")
    assert response.status_code == 200
    payload = response.json()
    assert payload["auth_enabled"] is False
    assert payload["mode"] == "academic_demo"


def test_session_cookie_authenticates_browser_requests(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "auth_enabled", True)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "cookie@example.org",
            "display_name": "cookie",
            "password": "correct-horse-battery",
        },
    )
    assert response.status_code == 201, response.text
    assert client.cookies.get("access_token")

    without_header = client.get("/api/v1/images")
    assert without_header.status_code == 200

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 200
    after_logout = client.get("/api/v1/images")
    assert after_logout.status_code == 401


def test_registration_can_be_disabled(client, monkeypatch) -> None:
    monkeypatch.setattr(settings, "allow_registration", False)
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "closed@example.org",
            "display_name": "closed",
            "password": "correct-horse-battery",
        },
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "registration_disabled"
