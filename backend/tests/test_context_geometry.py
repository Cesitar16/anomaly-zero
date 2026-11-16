import hashlib
import json
import socket
import urllib.request
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import app
from backend.app.services import context_geometry
from backend.app.services.series import get_snapshot_path

CONTRACT = yaml.safe_load(
    (Path(__file__).parents[2] / "docs" / "openapi-contract-v0.yaml").read_text(
        encoding="utf-8"
    )
)
client = TestClient(app, raise_server_exceptions=False)
ENDPOINT = "/api/v1/regions/murray-darling-basin/geometry"
SYNTHETIC_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
}


def synthetic_document(geometry=SYNTHETIC_POLYGON):
    return {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "EPSG:4326"}},
        "features": [{"type": "Feature", "properties": {}, "geometry": geometry}],
    }


def write_synthetic_artifact(tmp_path, monkeypatch, document=None, raw=None):
    if raw is None:
        raw = json.dumps(
            document or synthetic_document(), separators=(",", ":")
        ).encode("utf-8")
    path = tmp_path / "synthetic_context_geometry.geojson"
    path.write_bytes(raw)
    digest = hashlib.sha256(raw).hexdigest()
    monkeypatch.setenv(context_geometry.CONTEXT_GEOMETRY_ENV, str(path))
    monkeypatch.setattr(context_geometry, "EXPECTED_ARTIFACT_BYTES", len(raw))
    monkeypatch.setattr(context_geometry, "EXPECTED_ARTIFACT_SHA256", digest)
    monkeypatch.setattr(context_geometry, "EXPECTED_BOUNDS", (0, 0, 1, 1))
    monkeypatch.setattr(
        context_geometry,
        "CONTEXT_GEOMETRY_METADATA",
        {
            "region_id": "murray-darling-basin",
            "geometry_use": "contextual_outline_only",
            "scientific_approval": "not_approved",
            "source_title": "Synthetic test fixture only; not MDBA data.",
            "source_url": "fixture://be-10/context-geometry",
            "source_item_url": "fixture://be-10/context-geometry",
            "license": "Synthetic fixture only.",
            "license_url": None,
            "attribution": "Synthetic fixture",
            "publisher": "Synthetic fixture",
            "retrieved_utc": None,
            "source_item_modified_utc": None,
            "service_layer_crs": None,
            "output_crs": "EPSG:4326",
            "native_datum": None,
            "artifact_sha256": digest,
            "artifact_sha256_scope": "Exact bytes of this synthetic fixture only.",
        },
    )
    return path, digest, raw


def validate_against(schema, payload):
    Draft202012Validator(
        {"components": CONTRACT["components"], **schema},
        format_checker=FormatChecker(),
    ).validate(payload)


def test_context_geometry_returns_synthetic_maplibre_geojson_and_metadata(
    tmp_path, monkeypatch
):
    path, digest, raw = write_synthetic_artifact(tmp_path, monkeypatch)

    def no_network(*args, **kwargs):
        raise AssertionError("HTTP request must not perform network access")

    monkeypatch.setattr(urllib.request, "urlopen", no_network)
    monkeypatch.setattr(socket, "create_connection", no_network)
    response = client.get(ENDPOINT)

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/geo+json"
    assert response.headers["cache-control"] == "no-store"
    body = response.json()
    schema = CONTRACT["paths"]["/regions/{region_id}/geometry"]["get"][
        "responses"
    ]["200"]["content"]["application/geo+json"]["schema"]
    validate_against(schema, body)
    openapi = client.get("/openapi.json").json()
    runtime_schema = openapi["paths"]["/api/v1/regions/{region_id}/geometry"][
        "get"
    ]["responses"]["200"]["content"]["application/geo+json"]["schema"]
    if "$ref" in runtime_schema:
        ref_schema = {
            "components": openapi["components"],
            "$ref": runtime_schema["$ref"],
        }
    else:
        ref_schema = {"components": openapi["components"], **runtime_schema}
    Draft202012Validator(ref_schema, format_checker=FormatChecker()).validate(body)

    assert body["type"] == "FeatureCollection"
    feature = body["features"][0]
    assert feature["properties"] == {
        "region_id": "murray-darling-basin",
        "name": "Murray–Darling Basin",
    }
    assert feature["geometry"] == SYNTHETIC_POLYGON
    assert "crs" not in body
    assert body["metadata"]["source_title"].startswith("Synthetic test fixture")
    assert body["metadata"]["geometry_use"] == "contextual_outline_only"
    assert body["metadata"]["scientific_approval"] == "not_approved"
    assert body["metadata"]["native_datum"] is None
    assert body["metadata"]["artifact_sha256"] == digest
    assert body["metadata"]["license_url"] is None
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    assert len(raw) == path.stat().st_size


def test_context_geometry_accepts_synthetic_multipolygon(tmp_path, monkeypatch):
    geometry = {
        "type": "MultiPolygon",
        "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]],
    }
    write_synthetic_artifact(
        tmp_path, monkeypatch, document=synthetic_document(geometry)
    )
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    assert response.json()["features"][0]["geometry"] == geometry


def test_unknown_region_is_404_before_reading_geometry(monkeypatch):
    monkeypatch.delenv(context_geometry.CONTEXT_GEOMETRY_ENV, raising=False)
    response = client.get("/api/v1/regions/unknown/geometry")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "ANOMALY_ZERO_CONTEXT_GEOMETRY" not in response.text


@pytest.mark.parametrize("configured", [False, True])
def test_unconfigured_or_absent_geometry_is_sanitized_503(
    tmp_path, monkeypatch, configured
):
    monkeypatch.delenv(context_geometry.CONTEXT_GEOMETRY_ENV, raising=False)
    if configured:
        path = tmp_path / "missing.geojson"
        monkeypatch.setenv(context_geometry.CONTEXT_GEOMETRY_ENV, str(path))
    response = client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert response.json()["error"]["retryable"] is True
    assert str(tmp_path) not in response.text


def test_inaccessible_geometry_is_sanitized_503(tmp_path, monkeypatch):
    path = tmp_path / "restricted.geojson"
    path.write_bytes(b"synthetic")
    monkeypatch.setenv(context_geometry.CONTEXT_GEOMETRY_ENV, str(path))
    original_open = Path.open

    def deny_geometry(self, *args, **kwargs):
        if self == path:
            raise PermissionError("local file details")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", deny_geometry)
    response = client.get(ENDPOINT)
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
    assert str(path) not in response.text
    assert "local file details" not in response.text


@pytest.mark.parametrize(
    "document,raw",
    [
        (None, b"{"),
        ({"type": "FeatureCollection", "features": []}, None),
        (synthetic_document({"type": "Polygon", "coordinates": []}), None),
        (
            synthetic_document(
                {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [0, 0]]]}
            ),
            None,
        ),
        (
            synthetic_document(
                {"type": "LineString", "coordinates": [[0, 0], [1, 1]]}
            ),
            None,
        ),
        (
            synthetic_document(
                {"type": "Polygon", "coordinates": [[[0, 0], [181, 0], [0, 1], [0, 0]]]}
            ),
            None,
        ),
        (
            synthetic_document(
                {"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1]]]}
            ),
            None,
        ),
        (None, b'{"type":"FeatureCollection","value":NaN}'),
    ],
)
def test_invalid_geojson_is_sanitized_500(tmp_path, monkeypatch, document, raw):
    path, _, _ = write_synthetic_artifact(
        tmp_path, monkeypatch, document=document, raw=raw
    )
    response = client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert str(path) not in response.text
    assert "synthetic_context_geometry" not in response.text


def test_geometry_hash_mismatch_is_sanitized_500(tmp_path, monkeypatch):
    path, _, _ = write_synthetic_artifact(tmp_path, monkeypatch)
    monkeypatch.setattr(context_geometry, "EXPECTED_ARTIFACT_SHA256", "0" * 64)
    response = client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert str(path) not in response.text


def test_oversized_geometry_is_sanitized_500(tmp_path, monkeypatch):
    path, _, _ = write_synthetic_artifact(
        tmp_path, monkeypatch, raw=b"x" * (context_geometry.MAX_GEOMETRY_BYTES + 1)
    )
    response = client.get(ENDPOINT)
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert str(path) not in response.text


def test_without_geometry_health_catalog_series_and_csv_still_work(
    tmp_path, monkeypatch
):
    monkeypatch.delenv(context_geometry.CONTEXT_GEOMETRY_ENV, raising=False)
    monkeypatch.delenv("ANOMALY_ZERO_IMERG_SNAPSHOT", raising=False)
    monkeypatch.setitem(
        app.dependency_overrides, get_snapshot_path, lambda: tmp_path / "absent.json"
    )
    assert client.get("/health").status_code == 200
    assert client.get("/api/v1/regions").status_code == 200
    assert client.get(
        "/api/v1/products", params={"region_id": "murray-darling-basin"}
    ).status_code == 200
    series = client.get(
        "/api/v1/series",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    export = client.get(
        "/api/v1/series/export.csv",
        params={
            "region_id": "murray-darling-basin",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
        },
    )
    assert series.status_code == 200
    assert series.json()["data_state"] == "no_data"
    assert export.status_code == 200
    assert export.headers["content-type"] == "text/csv; charset=utf-8"
