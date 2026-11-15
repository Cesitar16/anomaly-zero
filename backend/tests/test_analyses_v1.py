import hashlib
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import app
from research import build_ful116_snapshot as snapshot_builder
from research.tests.test_ful116_snapshot import _write_granules

CONTRACT = yaml.safe_load(
    (Path(__file__).parents[2] / "docs" / "openapi-contract-v0.yaml").read_text(
        encoding="utf-8"
    )
)
client = TestClient(app, raise_server_exceptions=False)


def validate_contract(schema_name: str, payload: dict) -> None:
    Draft202012Validator(
        {"components": CONTRACT["components"], "$ref": f"#/components/schemas/{schema_name}"},
        format_checker=FormatChecker(),
    ).validate(payload)


def configured_snapshot(tmp_path, monkeypatch) -> tuple[Path, str]:
    inputs, point = _write_granules(tmp_path / "inputs", monkeypatch)
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(snapshot_path))
    return snapshot_path, generated["dataset_id"]


def request_body(dataset_id: str, **window_updates) -> dict:
    window = {
        "start": "2005-01",
        "end": "2005-12",
        "end_inclusive": True,
        **window_updates,
    }
    return {"dataset_id": dataset_id, "window": window}


def test_create_analysis_validates_existing_dataset_then_returns_contractual_409(
    tmp_path, monkeypatch
):
    snapshot_path, dataset_id = configured_snapshot(tmp_path, monkeypatch)
    original_hash = hashlib.sha256(snapshot_path.read_bytes()).hexdigest()
    request_payload = request_body(dataset_id)
    validate_contract("CreateAnalysisRequest", request_payload)

    response = client.post("/api/v1/analyses", json=request_payload)

    assert response.status_code == 409
    error = response.json()
    validate_contract("ErrorResponse", error)
    assert error["contract_version"] == "0.1-draft"
    assert error["synthetic"] is False
    assert datetime.fromisoformat(error["generated_at"]).utcoffset() == UTC.utcoffset(None)
    UUID(error["error"]["request_id"])
    assert error["error"]["code"] == "ANALYSIS_METHOD_UNAVAILABLE"
    assert error["error"]["retryable"] is False
    unavailable = error["error"]["details"]["analysis"]
    assert unavailable == {
        "state": "not_available",
        "analysis_id": None,
        "dataset_id": dataset_id,
        "region_id": "murray-darling-basin",
        "product_id": "P02",
        "window": request_payload["window"],
        "method": None,
        "metrics": {
            "slope": None,
            "slope_unit": None,
            "confidence_interval": None,
            "p_value": None,
            "significance": None,
        },
    }
    assert "analysis_id" not in error
    assert hashlib.sha256(snapshot_path.read_bytes()).hexdigest() == original_hash
    assert client.get("/api/v1/analyses/analysis-synthetic-001").status_code == 404


def test_create_analysis_rejects_invalid_body_before_resolving_snapshot(monkeypatch):
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", "C:/must-not-be-read/snapshot.json")
    missing = client.post("/api/v1/analyses")
    assert missing.status_code == 422
    validate_contract("ErrorResponse", missing.json())
    assert missing.json()["error"]["code"] == "INVALID_PARAMETER"

    top_level_extra = request_body("x")
    top_level_extra["method"] = "invented"
    cases = (
        (top_level_extra, 422),
        (request_body("x", start="2005-13"), 422),
        (request_body("x", start="2005-02", end="2005-01"), 422),
        (request_body("x", end_inclusive=False), 422),
    )
    for body, expected_status in cases:
        response = client.post("/api/v1/analyses", json=body)
        assert response.status_code == expected_status
        validate_contract("ErrorResponse", response.json())
        assert response.json()["error"]["code"] == "INVALID_PARAMETER"


def test_create_analysis_unknown_dataset_and_no_default_snapshot_return_404(
    tmp_path, monkeypatch
):
    snapshot_path, dataset_id = configured_snapshot(tmp_path, monkeypatch)
    assert client.post(
        "/api/v1/analyses", json=request_body("another-dataset")
    ).status_code == 404

    monkeypatch.delenv("ANOMALY_ZERO_IMERG_SNAPSHOT")
    monkeypatch.setattr(
        "backend.app.services.series.DEFAULT_SNAPSHOT_PATH", tmp_path / "absent.json"
    )
    response = client.post("/api/v1/analyses", json=request_body(dataset_id))
    assert response.status_code == 404
    validate_contract("ErrorResponse", response.json())
    assert snapshot_path.exists()


def test_create_analysis_reports_limit_coverage_and_unavailable_source(
    tmp_path, monkeypatch
):
    snapshot_path, dataset_id = configured_snapshot(tmp_path, monkeypatch)
    for body, code in (
        (request_body(dataset_id, start="2004-01", end="2024-01"), "LIMIT_EXCEEDED"),
        (request_body(dataset_id, start="2004-01", end="2004-12"), "PERIOD_OUT_OF_COVERAGE"),
    ):
        response = client.post("/api/v1/analyses", json=body)
        assert response.status_code == 422
        validate_contract("ErrorResponse", response.json())
        assert response.json()["error"]["code"] == code

    missing_path = tmp_path / "private" / "snapshot.json"
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(missing_path))
    response = client.post("/api/v1/analyses", json=request_body(dataset_id))
    assert response.status_code == 503
    validate_contract("ErrorResponse", response.json())
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert str(missing_path) not in response.text
    assert str(snapshot_path) not in response.text


def test_create_analysis_sanitizes_invalid_snapshot_content(tmp_path, monkeypatch):
    snapshot_path, dataset_id = configured_snapshot(tmp_path, monkeypatch)
    snapshot_path.write_text("{invalid", encoding="utf-8")

    response = client.post("/api/v1/analyses", json=request_body(dataset_id))

    assert response.status_code == 500
    validate_contract("ErrorResponse", response.json())
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert str(snapshot_path) not in response.text
    assert "invalid" not in response.text


def test_get_analysis_unknown_and_collection_without_id_are_contractual_routes():
    response = client.get("/api/v1/analyses/analysis-does-not-exist")
    assert response.status_code == 404
    validate_contract("ErrorResponse", response.json())
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert client.get("/api/v1/analyses/%20").status_code == 404

    # The collection defines POST only; GET without an analysis_id is not an operation.
    assert client.get("/api/v1/analyses").status_code == 405


def test_analysis_routes_match_contract_and_do_not_advertise_disabled_success():
    openapi = client.get("/openapi.json").json()
    post = openapi["paths"]["/api/v1/analyses"]["post"]
    request_schema = openapi["components"]["schemas"]["CreateAnalysisRequest"]
    assert request_schema["required"] == ["dataset_id", "window"]
    assert request_schema["additionalProperties"] is False
    assert set(request_schema["properties"]) == {"dataset_id", "window"}
    window_ref = request_schema["properties"]["window"]["$ref"].rsplit("/", 1)[-1]
    window_schema = openapi["components"]["schemas"][window_ref]
    assert window_ref == "InclusiveMonthRange"
    assert window_schema["required"] == ["start", "end", "end_inclusive"]
    assert window_schema.get("additionalProperties") is not False
    assert window_schema["properties"]["end_inclusive"]["const"] is True
    assert {"404", "409", "422", "503", "500"}.issubset(post["responses"])
    assert not {"201", "202"}.intersection(post["responses"])
    get = openapi["paths"]["/api/v1/analyses/{analysis_id}"]["get"]
    assert {"404", "422", "503", "500"}.issubset(get["responses"])
    assert get["parameters"][0]["schema"]["minLength"] == 1


def test_contract_keeps_pending_fixture_synthetic_and_preserves_null_and_zero():
    pending = CONTRACT["components"]["responses"]["AnalysisPending"]["content"][
        "application/json"
    ]["examples"]["pendingAnalysis"]["value"]
    validate_contract("AnalysisResponse", pending)
    assert pending["synthetic"] is True
    assert pending["status"] == "pending"
    assert set(pending["metrics"].values()) == {None}

    metrics = {
        "slope": 0,
        "slope_unit": "mm/hr per year",
        "confidence_interval": [0, 0],
        "p_value": 0,
        "significance": False,
    }
    Draft202012Validator(
        {"components": CONTRACT["components"], "$ref": "#/components/schemas/Metrics"}
    ).validate(metrics)
    assert metrics["slope"] == metrics["p_value"] == 0


def test_health_catalog_and_series_routes_remain_mounted():
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/regions").status_code == 200
    assert client.get(
        "/api/v1/products", params={"region_id": "murray-darling-basin"}
    ).status_code == 200
    assert client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-01",
            "frequency": "monthly",
        },
    ).status_code == 200
