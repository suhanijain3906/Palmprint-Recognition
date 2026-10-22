"""Tests for the image upload endpoints."""

from __future__ import annotations

from tests.conftest import encode_png, make_synthetic_palm, upload_image


def test_upload_succeeds(client, palm_png: bytes) -> None:
    payload = upload_image(client, palm_png)
    assert payload["status"] == "success"
    assert payload["image"]["media_type"] == "image/png"
    assert payload["image"]["size_bytes"] == len(palm_png)
    assert len(payload["image"]["checksum_sha256"]) == 64
    assert payload["image"]["download_url"].endswith("/file")


def test_upload_rejects_empty_file(client) -> None:
    response = client.post("/api/v1/images/upload", files={"file": ("empty.png", b"", "image/png")})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "empty_upload"


def test_upload_rejects_non_image(client) -> None:
    response = client.post(
        "/api/v1/images/upload", files={"file": ("notes.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {
        "invalid_image",
        "unsupported_media_type",
    }


def test_upload_rejects_corrupted_image(client) -> None:
    payload = encode_png(make_synthetic_palm(64, 64))
    response = client.post(
        "/api/v1/images/upload",
        files={"file": ("broken.png", payload[: len(payload) // 3], "image/png")},
    )
    assert response.status_code == 422


def test_list_images_is_empty_initially(client) -> None:
    response = client.get("/api/v1/images")
    assert response.status_code == 200
    payload = response.json()
    assert payload["items"] == []
    assert payload["meta"]["total"] == 0


def test_list_images_after_upload(client, palm_png: bytes) -> None:
    upload_image(client, palm_png)
    response = client.get("/api/v1/images")
    assert response.status_code == 200
    assert response.json()["meta"]["total"] == 1


def test_get_image(client, palm_png: bytes) -> None:
    image_id = upload_image(client, palm_png)["image"]["id"]
    response = client.get(f"/api/v1/images/{image_id}")
    assert response.status_code == 200
    assert response.json()["id"] == image_id


def test_get_unknown_image_returns_404(client) -> None:
    response = client.get("/api/v1/images/does-not-exist")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_download_image(client, palm_png: bytes) -> None:
    image_id = upload_image(client, palm_png)["image"]["id"]
    response = client.get(f"/api/v1/images/{image_id}/file")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/")
    assert len(response.content) == len(palm_png)


def test_delete_image(client, palm_png: bytes) -> None:
    image_id = upload_image(client, palm_png)["image"]["id"]
    response = client.delete(f"/api/v1/images/{image_id}")
    assert response.status_code == 200
    assert client.get(f"/api/v1/images/{image_id}").status_code == 404


def test_update_image_annotations(client, palm_png: bytes) -> None:
    image_id = upload_image(client, palm_png)["image"]["id"]
    response = client.patch(
        f"/api/v1/images/{image_id}",
        json={"label": "left hand", "subject_id": "S-001", "notes": "synthetic capture"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["label"] == "left hand"
    assert payload["subject_id"] == "S-001"


def test_upload_strips_the_path_of_the_filename(client, palm_png: bytes) -> None:
    payload = upload_image(client, palm_png, filename="../../etc/passwd.png")
    assert "/" not in payload["image"]["original_filename"]
    assert payload["image"]["original_filename"] == "passwd.png"


def test_uploaded_image_is_persisted(client, palm_png: bytes) -> None:
    image_id = upload_image(client, palm_png)["image"]["id"]
    from app.db.session import session_scope
    from app.models import ImageRecord

    with session_scope() as session:
        record = session.get(ImageRecord, image_id)
        assert record is not None
        assert record.media_type == "image/png"
        assert record.width > 0
        assert record.height > 0
