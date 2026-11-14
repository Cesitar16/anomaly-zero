from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "anomaly-zero-api"}


def test_openapi_docs_are_available() -> None:
    response = client.get("/docs")

    assert response.status_code == 200
