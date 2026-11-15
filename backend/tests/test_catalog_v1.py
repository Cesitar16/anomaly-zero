from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import app
from backend.app.schemas.catalog import Region
from backend.app.services.catalog import CATALOG, Catalog, get_catalog
from backend.app.services.series import get_snapshot_path

CONTRACT = yaml.safe_load(
    (Path(__file__).parents[2] / "docs" / "openapi-contract-v0.yaml").read_text(
        encoding="utf-8"
    )
)
FORMAT_CHECKER = FormatChecker()
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def hide_local_snapshot_from_catalog_fixtures(tmp_path):
    app.dependency_overrides[get_snapshot_path] = lambda: tmp_path / "absent.json"
    yield
    app.dependency_overrides.clear()


def synthetic_catalog(products=CATALOG.products) -> Catalog:
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
        products=products,
        synthetic=True,
    )


def validate_contract(schema_name: str, payload: dict[str, object]) -> None:
    schema = {
        "components": CONTRACT["components"],
        "$ref": f"#/components/schemas/{schema_name}",
    }
    Draft202012Validator(
        schema, format_checker=FORMAT_CHECKER
    ).validate(payload)


def test_regions_publish_authorized_exploratory_reference() -> None:
    response = client.get("/api/v1/regions")

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["synthetic"] is False
    assert len(body["generated_at"]) > 0
    assert body["regions"] == [
        {
            "region_id": "murray-darling-basin",
            "name": "Murray–Darling Basin",
            "geometry_version": None,
            "geometry_source": "https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=json",
            "crs": None,
            "area_km2": None,
        }
    ]
    validate_contract("RegionsResponse", body)


def test_regions_can_return_an_explicit_synthetic_fixture() -> None:
    app.dependency_overrides[get_catalog] = lambda: synthetic_catalog()
    try:
        response = client.get("/api/v1/regions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["synthetic"] is True
    assert response.json()["regions"] == [
        {
            "region_id": "REG01",
            "name": "Región sintética",
            "geometry_version": None,
            "geometry_source": None,
            "crs": None,
            "area_km2": None,
        }
    ]
    validate_contract("RegionsResponse", response.json())


def test_products_return_documented_metadata_for_a_known_fixture_region() -> None:
    app.dependency_overrides[get_catalog] = synthetic_catalog
    try:
        response = client.get("/api/v1/products", params={"region_id": "REG01"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    assert body["synthetic"] is True
    assert [product["product_id"] for product in body["products"]] == [
        "P01",
        "P02",
        "P03",
    ]
    assert [product["unit"] for product in body["products"]] == [
        "K",
        "mm/hr",
        "kg m-2",
    ]
    assert [product["product_version"] for product in body["products"]] == [
        "5.12.4",
        "07",
        "2.1",
    ]
    assert [product["source"]["collection_id"] for product in body["products"]] == [
        "C1276812859-GES_DISC",
        "C2723754851-GES_DISC",
        "C1342986036-GES_DISC",
    ]
    assert all(
        product["availability"] == "unavailable"
        and product["current_dataset_id"] is None
        and product["coverage"] is None
        and product["quality"] is None
        for product in body["products"]
    )
    validate_contract("ProductsResponse", body)


def test_authorized_region_returns_unavailable_products() -> None:
    response = client.get(
        "/api/v1/products", params={"region_id": "murray-darling-basin"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["synthetic"] is False
    assert body["region_id"] == "murray-darling-basin"
    assert [
        (
            product["short_name"],
            product["variable"],
            product["quantity"],
            product["unit"],
            product["product_version"],
            product["source"]["collection_id"],
        )
        for product in body["products"]
    ] == [
        (
            "M2TMNXSLV",
            "T2M",
            "air_temperature_2m",
            "K",
            "5.12.4",
            "C1276812859-GES_DISC",
        ),
        (
            "GPM_3IMERGM",
            "precipitation",
            "monthly_mean_rate",
            "mm/hr",
            "07",
            "C2723754851-GES_DISC",
        ),
        (
            "GLDAS_NOAH025_M",
            "SoilMoi0_10cm_inst",
            "soil_moisture_layer_0_10_cm",
            "kg m-2",
            "2.1",
            "C1342986036-GES_DISC",
        ),
    ]
    assert all(
        product["availability"] == "unavailable"
        and product["current_dataset_id"] is None
        and product["coverage"] is None
        and product["quality"] is None
        for product in body["products"]
    )
    validate_contract("ProductsResponse", body)


def test_known_region_without_products_returns_an_empty_catalog() -> None:
    app.dependency_overrides[get_catalog] = lambda: synthetic_catalog(products=())
    try:
        response = client.get("/api/v1/products", params={"region_id": "REG01"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["products"] == []
    assert response.json()["synthetic"] is True
    validate_contract("ProductsResponse", response.json())


def test_products_distinguish_unknown_region_and_invalid_parameter() -> None:
    for params, expected_status in [({}, 422), ({"region_id": ""}, 422), ({"region_id": "REG99"}, 404)]:
        response = client.get("/api/v1/products", params=params)
        assert response.status_code == expected_status
        validate_contract("ErrorResponse", response.json())


def test_catalog_unavailable_uses_retryable_error_envelope() -> None:
    from backend.app.services.catalog import CatalogUnavailable

    def unavailable() -> Catalog:
        raise CatalogUnavailable

    app.dependency_overrides[get_catalog] = unavailable
    try:
        response = client.get("/api/v1/regions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    validate_contract("ErrorResponse", response.json())


def test_internal_error_is_sanitized_and_health_is_unchanged() -> None:
    def broken() -> Catalog:
        raise RuntimeError("sensitive provider detail")

    app.dependency_overrides[get_catalog] = broken
    try:
        response = client.get("/api/v1/regions")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert "sensitive provider detail" not in response.text
    validate_contract("ErrorResponse", response.json())
    assert client.get("/health").json() == {
        "status": "ok",
        "service": "anomaly-zero-api",
    }


def test_generated_openapi_exposes_catalog_and_series_paths() -> None:
    document = client.get("/openapi.json").json()
    paths = document["paths"]

    assert "/api/v1/regions" in paths
    assert "/api/v1/products" in paths
    assert "/api/v1/series" in paths
    assert "get" in paths["/api/v1/regions"]
    assert "get" in paths["/api/v1/products"]
    assert "get" in paths["/api/v1/series"]
    assert [parameter["name"] for parameter in paths["/api/v1/series"]["get"]["parameters"]] == [
        "region_id",
        "product_id",
        "start",
        "end",
        "frequency",
    ]
    product_parameters = paths["/api/v1/products"]["get"]["parameters"]
    assert product_parameters == [
        {
            "name": "region_id",
            "in": "query",
            "required": True,
            "schema": {"type": "string", "minLength": 1, "title": "Region Id"},
        }
    ]
    schemas = document["components"]["schemas"]
    contract_schemas = CONTRACT["components"]["schemas"]
    for name in (
        "Region",
        "Product",
        "Source",
        "MonthRange",
        "SourceMissingAttributes",
        "Quality",
        "QualityCheck",
        "Error",
        "ErrorDetails",
        "UnavailableAnalysis",
        "Metrics",
    ):
        assert set(schemas[name].get("required", [])) == set(
            contract_schemas[name].get("required", [])
        )
    assert schemas["RegionsResponse"]["required"] == [
        "contract_version",
        "synthetic",
        "generated_at",
        "regions",
    ]
    assert schemas["ProductsResponse"]["required"] == [
        "contract_version",
        "synthetic",
        "generated_at",
        "region_id",
        "products",
    ]
    assert schemas["Product"]["properties"]["availability"]["enum"] == [
        "available",
        "partial",
        "unavailable",
    ]
    assert schemas["Quality"]["properties"]["qa_checks"]["type"] == "array"
    assert schemas["Quality"]["properties"]["uninterpreted_provider_fields"][
        "type"
    ] == "array"
    for path in ("/api/v1/regions", "/api/v1/products"):
        response = paths[path]["get"]["responses"]["200"]
        assert response["headers"]["Cache-Control"]["schema"]["const"] == "no-store"
    assert paths["/api/v1/products"]["get"]["responses"]["422"]["content"][
        "application/json"
    ]["schema"]["$ref"] == "#/components/schemas/ErrorResponse"
