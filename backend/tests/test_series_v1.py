from pathlib import Path

import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import app
from backend.app.schemas.catalog import Region
from backend.app.services import series as series_service
from backend.app.services.catalog import CATALOG, Catalog, get_catalog
from backend.app.services.series import get_snapshot_path
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


def synthetic_catalog() -> Catalog:
    return Catalog(
        regions=(
            Region(
                region_id="REG01",
                name="Región sintética",
                geometry_version=None,
                geometry_source=None,
                crs=None,
                area_km2=None,
            ),
        ),
        products=CATALOG.products,
        synthetic=True,
    )


def install_overrides(monkeypatch, snapshot_path: Path) -> None:
    app.dependency_overrides[get_catalog] = synthetic_catalog
    app.dependency_overrides[get_snapshot_path] = lambda: snapshot_path


def request_series(**params):
    return client.get(
        "/api/v1/series",
        params={
            "region_id": "REG01",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
            **params,
        },
    )


def test_series_maps_verified_snapshot_to_contract_without_aggregation(
    tmp_path, monkeypatch
):
    inputs, point = _write_granules(tmp_path / "inputs", monkeypatch)
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    install_overrides(monkeypatch, snapshot_path)
    try:
        response = request_series()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    validate_contract("SeriesResponse", body)
    assert body["synthetic"] is True
    assert body["dataset_id"] == generated["dataset_id"]
    assert body["product"]["product_version"] == "V07B"
    assert body["product"]["unit"] == "mm/hr"
    assert body["series"][0]["value"] == 0
    assert body["series"][1]["value"] is None
    assert body["series"][1]["quality"]["missing_reason"] == "provider_fill_value"
    assert body["spatial_aggregation"]["support_type"] == "point_sample"
    assert body["quality"]["provider_flags_applied"] is False
    assert body["quality"]["verification_state"] == "basic_checks_only"
    assert body["coverage"]["present_periods"] == 12
    assert body["coverage"]["valid_periods"] == 10


def test_series_filters_inclusive_month_range_and_marks_no_snapshot_as_no_data(
    tmp_path, monkeypatch
):
    inputs, point = _write_granules(tmp_path / "inputs", monkeypatch)
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    install_overrides(monkeypatch, snapshot_path)
    try:
        partial = request_series(start="2005-01", end="2005-03")
        outside = request_series(start="2004-12", end="2005-01")
    finally:
        app.dependency_overrides.clear()
    assert partial.status_code == 200
    assert [point["date"] for point in partial.json()["series"]] == [
        "2005-01-01",
        "2005-02-01",
        "2005-03-01",
    ]
    assert partial.json()["coverage"]["expected_periods"] == 3
    validate_contract("SeriesResponse", partial.json())
    assert outside.status_code == 422
    validate_contract("ErrorResponse", outside.json())

    install_overrides(monkeypatch, tmp_path / "absent.json")
    try:
        empty = request_series(start="2004-11", end="2004-12")
    finally:
        app.dependency_overrides.clear()
    assert empty.status_code == 200
    assert empty.json()["data_state"] == "no_data"
    assert empty.json()["dataset_id"] is None
    assert empty.json()["provenance"] is None
    assert empty.json()["series"] == []
    assert empty.json()["coverage"]["missing_periods"] == ["2004-11", "2004-12"]
    validate_contract("SeriesResponse", empty.json())


def test_series_returns_documented_errors_for_unknown_and_invalid_requests(
    tmp_path, monkeypatch
):
    install_overrides(monkeypatch, tmp_path / "absent.json")
    try:
        cases = (
            (request_series(region_id="unknown"), 404),
            (request_series(product_id="unknown"), 404),
            (request_series(start="2005-12", end="2005-01"), 422),
            (request_series(start="2000-01", end="2020-01"), 422),
            (request_series(frequency="yearly"), 422),
        )
    finally:
        app.dependency_overrides.clear()
    for response, status in cases:
        assert response.status_code == status
        validate_contract("ErrorResponse", response.json())


def test_products_reflect_only_a_verified_local_snapshot(tmp_path, monkeypatch):
    inputs, point = _write_granules(tmp_path / "inputs", monkeypatch)
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    install_overrides(monkeypatch, snapshot_path)
    try:
        response = client.get("/api/v1/products", params={"region_id": "REG01"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    imerg = next(item for item in response.json()["products"] if item["product_id"] == "P02")
    assert imerg["availability"] == "partial"
    assert imerg["current_dataset_id"] == generated["dataset_id"]
    validate_contract("ProductsResponse", response.json())


def test_real_be03_catalog_serves_a_configured_complete_point_snapshot(
    tmp_path, monkeypatch
):
    inputs, point = _write_granules(
        tmp_path / "inputs", monkeypatch, include_missing=False
    )
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(snapshot_path))

    response = client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    assert response.status_code == 200
    body = response.json()
    validate_contract("SeriesResponse", body)
    assert body["synthetic"] is True
    assert body["region"]["region_id"] == "murray-darling-basin"
    assert body["region"]["name"] == "Murray–Darling Basin"
    assert body["product"]["product_id"] == "P02"
    assert body["product"]["availability"] == "available"
    assert body["product"]["current_dataset_id"] == generated["dataset_id"]
    assert body["product"]["unit"] == "mm/hr"
    assert body["spatial_aggregation"]["support_type"] == "point_sample"
    assert body["spatial_aggregation"]["approval_state"] == "not_assessed"
    assert body["quality"]["provider_flags_applied"] is False
    assert body["quality"]["verification_state"] == "basic_checks_only"
    assert len(body["series"]) == 12

    products = client.get(
        "/api/v1/products", params={"region_id": "murray-darling-basin"}
    )
    assert products.status_code == 200
    product = next(
        item for item in products.json()["products"] if item["product_id"] == "P02"
    )
    assert product["availability"] == "available"
    assert product["current_dataset_id"] == generated["dataset_id"]
    validate_contract("ProductsResponse", products.json())


def test_unconfigured_missing_default_snapshot_returns_no_data(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("ANOMALY_ZERO_IMERG_SNAPSHOT", raising=False)
    monkeypatch.setattr(
        series_service, "DEFAULT_SNAPSHOT_PATH", tmp_path / "not-configured.json"
    )
    response = client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    assert response.status_code == 200
    assert response.json()["data_state"] == "no_data"
    assert response.json()["synthetic"] is False
    validate_contract("SeriesResponse", response.json())


def test_explicitly_configured_missing_snapshot_is_retryable_503(monkeypatch, tmp_path):
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(tmp_path / "missing.json"))
    response = client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert str(tmp_path) not in response.text
    validate_contract("ErrorResponse", response.json())


def test_explicitly_configured_unreadable_snapshot_is_retryable_503(
    monkeypatch, tmp_path
):
    snapshot_path = tmp_path / "private" / "snapshot.json"
    snapshot_path.parent.mkdir()
    snapshot_path.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(snapshot_path))
    original_open = Path.open

    def deny_snapshot(self, *args, **kwargs):
        if self == snapshot_path:
            raise PermissionError("private file detail")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_snapshot)
    response = client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert str(snapshot_path) not in response.text
    assert "private file detail" not in response.text
    validate_contract("ErrorResponse", response.json())


def test_invalid_snapshot_returns_sanitized_internal_error(tmp_path, monkeypatch):
    snapshot_path = tmp_path / "private" / "snapshot.json"
    snapshot_path.parent.mkdir()
    snapshot_path.write_text("{", encoding="utf-8")
    install_overrides(monkeypatch, snapshot_path)
    try:
        response = request_series()
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert str(snapshot_path) not in response.text
    validate_contract("ErrorResponse", response.json())
