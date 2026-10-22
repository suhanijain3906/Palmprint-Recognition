"""Unit tests for the ML HTTP client error mapping."""

from __future__ import annotations

import httpx
import pytest

from app.services.ml_client import MLServiceClient
from app.utils.errors import ServiceUnavailableError, UpstreamTimeoutError


def test_timeout_is_mapped_to_gateway_timeout(monkeypatch) -> None:
    def raise_timeout(self, *args, **kwargs):
        raise httpx.ReadTimeout("simulated timeout")

    monkeypatch.setattr(httpx.Client, "request", raise_timeout)
    client = MLServiceClient(base_url="http://ml.test:8001", timeout=0.01)
    with pytest.raises(UpstreamTimeoutError) as excinfo:
        client.health()
    assert excinfo.value.status_code == 504


def test_connection_error_is_mapped_to_service_unavailable(monkeypatch) -> None:
    def raise_connect(self, *args, **kwargs):
        raise httpx.ConnectError("simulated connection refusal")

    monkeypatch.setattr(httpx.Client, "request", raise_connect)
    client = MLServiceClient(base_url="http://ml.test:8001", timeout=0.01)
    with pytest.raises(ServiceUnavailableError) as excinfo:
        client.health()
    assert excinfo.value.status_code == 503


def test_service_api_key_is_forwarded(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def fake_request(self, method, url, *, headers=None, **kwargs):
        captured.update(headers or {})
        return httpx.Response(200, json={"status": "ok"}, request=httpx.Request(method, url))

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    client = MLServiceClient(base_url="http://ml.test:8001", timeout=1.0, api_key="secret-token")
    assert client.health()["status"] == "ok"
    assert captured["X-Service-Token"] == "secret-token"
