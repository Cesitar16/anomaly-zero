import csv
import io
import json
import math
from pathlib import Path

import yaml
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from backend.app.main import app
from backend.app.schemas.catalog import Region
from backend.app.services.catalog import CATALOG, Catalog, get_catalog
from backend.app.services.series import get_snapshot_path
from backend.app.services.series_csv import CSV_COLUMNS, _text_cell
from research import build_ful116_snapshot as snapshot_builder
from research.tests.test_ful116_snapshot import _write_granules

CONTRACT = yaml.safe_load(
    (Path(__file__).parents[2] / "docs" / "openapi-contract-v0.yaml").read_text(
        encoding="utf-8"
    )
)
client = TestClient(app, raise_server_exceptions=False)


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
    monkeypatch.setitem(app.dependency_overrides, get_catalog, synthetic_catalog)
    monkeypatch.setitem(
        app.dependency_overrides, get_snapshot_path, lambda: snapshot_path
    )


def request_export(**params):
    return client.get(
        "/api/v1/series/export.csv",
        params={
            "region_id": "REG01",
            "product_id": "P02",
            "start": "2005-01",
            "end": "2005-12",
            "frequency": "monthly",
            **params,
        },
    )


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


def read_csv(response):
    return list(csv.DictReader(io.StringIO(response.content.decode("utf-8"))))


def validate_error(response) -> None:
    Draft202012Validator(
        {"components": CONTRACT["components"], "$ref": "#/components/schemas/ErrorResponse"},
        format_checker=FormatChecker(),
    ).validate(response.json())


def assert_http_parity(params: dict[str, str], *, expected_status: int = 200):
    json_response = request_series(**params)
    csv_response = request_export(**params)
    assert json_response.status_code == csv_response.status_code == expected_status
    if expected_status != 200:
        validate_error(json_response)
        validate_error(csv_response)
        json_error = json_response.json()["error"]
        csv_error = csv_response.json()["error"]
        assert (json_error["code"], json_error["message"], json_error["retryable"]) == (
            csv_error["code"],
            csv_error["message"],
            csv_error["retryable"],
        )
        assert json_error.get("details") == csv_error.get("details")
        return json_response, csv_response, []

    Draft202012Validator(
        {"components": CONTRACT["components"], "$ref": "#/components/schemas/SeriesResponse"},
        format_checker=FormatChecker(),
    ).validate(json_response.json())
    assert csv_response.headers["content-type"] == "text/csv; charset=utf-8"
    assert csv_response.headers["content-disposition"] == (
        'attachment; filename="anomaly-zero-series.csv"'
    )
    assert csv_response.headers["cache-control"] == "no-store"
    body = json_response.json()
    reader = csv.DictReader(io.StringIO(csv_response.content.decode("utf-8")))
    rows = list(reader)
    assert reader.fieldnames == list(CSV_COLUMNS)
    if body["data_state"] == "no_data":
        assert body["series"] == []
        assert len(rows) == 1
        assert rows[0]["record_type"] == "status"
        assert rows[0]["period"] == rows[0]["value"] == rows[0]["dataset_id"] == ""
        return json_response, csv_response, rows

    product = body["product"]
    quality = body["quality"]
    spatial = body["spatial_aggregation"]
    provenance = body["provenance"]
    assert len(rows) == len(body["series"])
    assert [row["period"] for row in rows] == [point["date"] for point in body["series"]]
    for row, point in zip(rows, body["series"], strict=True):
        assert row["record_type"] == "observation"
        assert row["data_state"] == body["data_state"]
        assert row["region_id"] == body["region"]["region_id"]
        assert row["product_id"] == product["product_id"]
        assert row["product_version"] == product["product_version"]
        assert row["variable"] == product["variable"]
        assert row["quantity"] == product["quantity"]
        assert row["unit"] == product["unit"]
        assert row["spatial_support_type"] == spatial["support_type"]
        assert row["spatial_approval_state"] == spatial["approval_state"]
        assert row["dataset_id"] == body["dataset_id"]
        assert row["synthetic"] == str(body["synthetic"]).lower()
        assert row["provider_flags_applied"] == str(
            quality["provider_flags_applied"]
        ).lower()
        assert row["quality_state"] == point["quality"]["state"]
        assert row["missing_reason"] == (
            point["quality"]["missing_reason"] or "null"
        )
        assert json.loads(row["provider_flags_json"]) == point["quality"][
            "provider_flags"
        ]
        assert json.loads(row["source_sha256_json"]) == provenance["source_sha256"]
        assert row["manifest_sha256"] == (
            provenance["manifest_sha256"] or "null"
        )
        assert json.loads(row["transformations_json"]) == body["transformations"]
        if point["value"] is None:
            assert row["value"] == ""
        else:
            assert math.isfinite(point["value"])
            assert row["value"] == repr(point["value"])
            assert row["value"].lower() not in {"nan", "inf", "-inf", "infinity"}
    return json_response, csv_response, rows


def build_synthetic_snapshot(tmp_path, monkeypatch, *, include_missing=True):
    inputs, point = _write_granules(
        tmp_path / "inputs", monkeypatch, include_missing=include_missing
    )
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    install_overrides(monkeypatch, snapshot_path)
    return generated


def test_export_reuses_verified_snapshot_and_preserves_zero_missing_quality_and_provenance(
    tmp_path, monkeypatch
):
    inputs, point = _write_granules(tmp_path / "inputs", monkeypatch)
    snapshot_path = tmp_path / "processed" / "imerg_2005_point_snapshot.json"
    generated = snapshot_builder.build_snapshot(inputs, point, snapshot_path.parent)
    install_overrides(monkeypatch, snapshot_path)
    try:
        response = request_export()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/csv; charset=utf-8"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"].startswith("attachment;")
    rows = read_csv(response)
    assert len(rows) == 12
    assert rows[0]["record_type"] == "observation"
    assert rows[0]["period"] == "2005-01-01"
    assert rows[0]["value"] == "0.0"
    assert rows[0]["quality_state"] == "unassessed"
    assert rows[0]["missing_reason"] == "null"
    assert rows[0]["dataset_id"] == generated["dataset_id"]
    assert json.loads(rows[0]["source_sha256_json"]) == [
        record["sha256"] for record in generated["provenance"]["source_records"]
    ]
    assert rows[0]["manifest_sha256"] == "null"
    assert rows[0]["synthetic"] == "true"
    assert rows[0]["provider_flags_applied"] == "false"
    assert rows[0]["unit"] == "mm/hr"
    assert rows[0]["spatial_support_type"] == "point_sample"
    assert rows[1]["period"] == "2005-02-01"
    assert rows[1]["value"] == ""
    assert rows[1]["quality_state"] == "missing"
    assert rows[1]["missing_reason"] == "provider_fill_value"
    assert all(row["product_id"] == "P02" for row in rows)


def test_json_and_csv_have_exact_parity_for_complete_synthetic_series(
    tmp_path, monkeypatch
):
    generated = build_synthetic_snapshot(
        tmp_path, monkeypatch, include_missing=False
    )
    body_response, _, rows = assert_http_parity({})

    body = body_response.json()
    assert body["dataset_id"] == generated["dataset_id"]
    assert body["data_state"] == "available"
    assert body["coverage"]["valid_periods"] == 12
    assert body["product"]["product_version"] == "V07B"
    assert body["product"]["variable"] == "precipitation"
    assert body["product"]["quantity"] == "monthly_mean_rate"
    assert [row["period"] for row in rows] == [
        f"2005-{month:02d}-01" for month in range(1, 13)
    ]
    assert [row["value"] for row in rows] == [
        "0.0", "2.0", "3.0", "4.0", "5.0", "6.0",
        "7.0", "8.0", "9.0", "10.0", "11.0", "12.0",
    ]
    assert {row["unit"] for row in rows} == {"mm/hr"}
    assert {row["spatial_support_type"] for row in rows} == {"point_sample"}
    assert {row["spatial_approval_state"] for row in rows} == {"not_assessed"}
    assert {row["synthetic"] for row in rows} == {"true"}
    assert {row["provider_flags_applied"] for row in rows} == {"false"}
    assert {row["manifest_sha256"] for row in rows} == {"null"}
    expected_hashes = [
        record["sha256"] for record in generated["provenance"]["source_records"]
    ]
    assert all(json.loads(row["source_sha256_json"]) == expected_hashes for row in rows)
    assert all(json.loads(row["transformations_json"]) == [] for row in rows)


def test_json_and_csv_parity_for_missing_zero_and_inclusive_subrange(
    tmp_path, monkeypatch
):
    generated = build_synthetic_snapshot(tmp_path, monkeypatch)
    full_json, _, full_rows = assert_http_parity({})
    full = full_json.json()
    assert full["dataset_id"] == generated["dataset_id"]
    assert full["data_state"] == "available_with_gaps"
    assert full["spatial_aggregation"]["support_type"] == "point_sample"
    assert full["spatial_aggregation"]["approval_state"] == "not_assessed"
    assert full["quality"]["provider_flags_applied"] is False
    assert full["series"][0]["value"] == 0
    assert full_rows[0]["value"] == "0.0"
    assert full["series"][1]["value"] is None
    assert full_rows[1]["value"] == ""
    assert full_rows[1]["missing_reason"] == "provider_fill_value"
    assert full_rows[1]["quality_state"] == "missing"
    assert full["series"][2]["quality"]["missing_reason"] == (
        "non_finite_source_value"
    )
    assert full_rows[2]["value"] == ""
    assert full_rows[2]["missing_reason"] == "non_finite_source_value"

    partial_json, _, partial_rows = assert_http_parity(
        {"start": "2005-01", "end": "2005-03"}
    )
    assert partial_json.json()["requested_coverage"] == {
        "start": "2005-01", "end": "2005-03", "end_inclusive": True
    }
    assert [row["period"] for row in partial_rows] == [
        "2005-01-01", "2005-02-01", "2005-03-01"
    ]


def test_json_no_data_matches_exactly_one_csv_status_row(tmp_path, monkeypatch):
    monkeypatch.delenv("ANOMALY_ZERO_IMERG_SNAPSHOT", raising=False)
    install_overrides(monkeypatch, tmp_path / "not-configured.json")
    json_response, csv_response, rows = assert_http_parity({})
    assert json_response.json()["data_state"] == "no_data"
    assert json_response.json()["series"] == []
    assert len(rows) == 1
    assert rows[0]["record_type"] == "status"
    assert rows[0]["period"] == rows[0]["value"] == rows[0]["dataset_id"] == ""
    assert csv_response.headers["content-type"] == "text/csv; charset=utf-8"


def test_json_and_csv_return_matching_contract_errors(tmp_path, monkeypatch):
    build_synthetic_snapshot(tmp_path, monkeypatch)
    cases = (
        ({"region_id": "unknown"}, 404, "RESOURCE_NOT_FOUND"),
        ({"product_id": "unknown"}, 404, "RESOURCE_NOT_FOUND"),
        ({"start": "2005-13"}, 422, "INVALID_PARAMETER"),
        ({"start": "2005-12", "end": "2005-01"}, 422, "INVALID_PARAMETER"),
        ({"start": "2000-01", "end": "2020-01"}, 422, "LIMIT_EXCEEDED"),
        ({"start": "2004-12", "end": "2005-01"}, 422, "PERIOD_OUT_OF_COVERAGE"),
    )
    for params, status, code in cases:
        json_response, csv_response, _ = assert_http_parity(
            params, expected_status=status
        )
        assert json_response.json()["error"]["code"] == code
        assert csv_response.json()["error"]["code"] == code


def test_json_and_csv_match_configured_snapshot_failures_without_path_leaks(
    tmp_path, monkeypatch
):
    missing = tmp_path / "private" / "missing.json"
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(missing))
    install_overrides(monkeypatch, missing)
    for response in (request_series(), request_export()):
        assert response.status_code == 503
        validate_error(response)
        assert response.json()["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert response.json()["error"]["retryable"] is True
        assert str(tmp_path) not in response.text

    invalid = tmp_path / "private" / "invalid.json"
    invalid.parent.mkdir()
    invalid.write_text("{", encoding="utf-8")
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(invalid))
    install_overrides(monkeypatch, invalid)
    for response in (request_series(), request_export()):
        assert response.status_code == 500
        validate_error(response)
        assert response.json()["error"]["code"] == "INTERNAL_ERROR"
        assert str(tmp_path) not in response.text


def test_export_no_data_is_one_status_row_without_observation_identity(
    tmp_path, monkeypatch
):
    monkeypatch.delenv("ANOMALY_ZERO_IMERG_SNAPSHOT", raising=False)
    install_overrides(monkeypatch, tmp_path / "not-configured.json")
    try:
        response = request_export()
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    text = response.content.decode("utf-8")
    rows = read_csv(response)
    assert len(rows) == 1
    row = rows[0]
    assert row["record_type"] == "status"
    assert row["data_state"] == "no_data"
    assert row["period"] == row["value"] == row["dataset_id"] == ""
    assert row["synthetic"] == "true"
    assert row["provider_flags_applied"] == "false"
    assert text.splitlines()[0].split(",") == list(CSV_COLUMNS)


def test_export_contract_has_same_query_parameters_and_synthetic_csv_examples():
    series_params = CONTRACT["paths"]["/series"]["get"]["parameters"]
    export = CONTRACT["paths"]["/series/export.csv"]["get"]
    assert export["parameters"] == series_params
    assert "text/csv" in export["responses"]["200"]["content"]
    examples = export["responses"]["200"]["content"]["text/csv"]["examples"]
    for example in examples.values():
        reader = csv.DictReader(io.StringIO(example["value"]))
        rows = list(reader)
        assert reader.fieldnames == list(CSV_COLUMNS)
        assert all(row["synthetic"] == "true" for row in rows)
    no_data = list(
        csv.DictReader(
            io.StringIO(examples["syntheticNoData"]["value"])
        )
    )
    assert len(no_data) == 1
    assert no_data[0]["record_type"] == "status"
    assert no_data[0]["period"] == no_data[0]["value"] == no_data[0]["dataset_id"] == ""


def test_export_validates_parameters_and_preserves_documented_http_errors(
    tmp_path, monkeypatch
):
    install_overrides(monkeypatch, tmp_path / "not-configured.json")
    try:
        invalid = request_export(start="not-a-month")
        unknown = request_export(region_id="unknown")
        too_long = request_export(start="2000-01", end="2020-01")
    finally:
        app.dependency_overrides.clear()
    assert invalid.status_code == 422
    assert unknown.status_code == 404
    assert too_long.status_code == 422
    for response in (invalid, unknown, too_long):
        validate_error(response)

    monkeypatch.setenv(
        "ANOMALY_ZERO_IMERG_SNAPSHOT", str(tmp_path / "missing.json")
    )
    install_overrides(monkeypatch, tmp_path / "missing.json")
    try:
        unavailable = request_export()
    finally:
        app.dependency_overrides.clear()
    assert unavailable.status_code == 503
    validate_error(unavailable)
    assert str(tmp_path) not in unavailable.text

    invalid_snapshot = tmp_path / "invalid.json"
    invalid_snapshot.write_text("{", encoding="utf-8")
    monkeypatch.setenv("ANOMALY_ZERO_IMERG_SNAPSHOT", str(invalid_snapshot))
    install_overrides(monkeypatch, invalid_snapshot)
    try:
        invalid_content = request_export()
    finally:
        app.dependency_overrides.clear()
    assert invalid_content.status_code == 500
    validate_error(invalid_content)
    assert str(tmp_path) not in invalid_content.text


def test_export_neutralizes_formula_like_text_without_changing_numeric_values():
    assert _text_cell("=HYPERLINK(\"https://example.invalid\")") == "'=HYPERLINK(\"https://example.invalid\")"
    assert _text_cell("  +CMD()") == "'  +CMD()"
    assert _text_cell("provider_field") == "provider_field"
