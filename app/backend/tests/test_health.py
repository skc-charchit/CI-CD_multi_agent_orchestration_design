from backend.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_root_links_to_api_docs_and_health() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs"] == "/docs"
    assert response.json()["health"] == "/api/v1/health"


def test_health_endpoint() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
