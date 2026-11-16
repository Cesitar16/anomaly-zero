from importlib import reload

import pytest
from fastapi.testclient import TestClient

from backend.app import main

FRONTEND = "https://web.example.test"


@pytest.fixture
def configured_app(monkeypatch):
    with monkeypatch.context() as environment:

        def load(frontend_origin):
            if frontend_origin is None:
                environment.delenv("ANOMALY_ZERO_FRONTEND_ORIGIN", raising=False)
            else:
                environment.setenv("ANOMALY_ZERO_FRONTEND_ORIGIN", frontend_origin)
            return reload(main).app

        yield load
    reload(main)


def test_cross_origin_requests_are_not_enabled_by_default(configured_app):
    client = TestClient(configured_app(None))
    response = client.get("/health", headers={"Origin": FRONTEND})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_only_configured_frontend_can_read_api_responses(configured_app):
    client = TestClient(configured_app(f"{FRONTEND}/"))
    response = client.get("/api/v1/regions", headers={"Origin": FRONTEND})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == FRONTEND
    assert "access-control-allow-credentials" not in response.headers

    other = client.get("/api/v1/regions", headers={"Origin": "https://other.test"})
    assert "access-control-allow-origin" not in other.headers


@pytest.mark.parametrize(
    ("request_origin", "method", "expected_status"),
    [
        (FRONTEND, "POST", 200),
        ("https://other.test", "POST", 400),
        (FRONTEND, "DELETE", 400),
    ],
)
def test_preflight_checks_origin_and_method(
    configured_app, request_origin, method, expected_status
):
    client = TestClient(configured_app(FRONTEND))
    response = client.options(
        "/api/v1/analyses",
        headers={
            "Origin": request_origin,
            "Access-Control-Request-Method": method,
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "invalid_origin", ["*", "https://web.test/path", "https://user:pass@web.test"]
)
def test_invalid_frontend_configuration_fails_at_startup(
    configured_app, invalid_origin
):
    with pytest.raises(ValueError, match="must be an HTTP"):
        configured_app(invalid_origin)
