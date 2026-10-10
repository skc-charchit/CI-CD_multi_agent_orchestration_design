"""Tests for the example API request/response flow."""

from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_echo_returns_message_and_request_metadata() -> None:
    response = client.post(
        "/api/v1/examples/echo",
        json={"message": "Hello from the frontend"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Hello from the frontend"
    assert body["id"]
    assert body["received_at"]


def test_echo_rejects_empty_message() -> None:
    response = client.post("/api/v1/examples/echo", json={"message": ""})

    assert response.status_code == 422


def test_echo_rejects_message_over_limit() -> None:
    response = client.post(
        "/api/v1/examples/echo",
        json={"message": "x" * 501},
    )

    assert response.status_code == 422


def test_frontend_origin_is_allowed_for_api_requests() -> None:
    response = client.options(
        "/api/v1/examples/echo",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
