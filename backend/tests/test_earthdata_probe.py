from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
import xarray as xr
from earthaccess.search import DataGranules

from backend.app.data_sources.earthdata_probe import (
    DEFAULT_BBOX,
    GLDAS,
    PRODUCTS,
    ProbeError,
    discover,
    discover_product,
    download_gldas,
    inspect_netcdf,
    month_bounds,
    safe_error,
)


class FakeCollection(dict[str, Any]):
    @property
    def concept_id(self) -> str:
        return self["meta"]["concept-id"]

    @property
    def version(self) -> str:
        return self["umm"]["Version"]


class FakeGranule(dict[str, Any]):
    @property
    def size(self) -> float:
        return float(self["size_mib"])


class FakeEarthaccess:
    def __init__(
        self,
        granules: list[FakeGranule] | None = None,
        downloaded_payload: str = "netcdf",
    ) -> None:
        self.granules = granules or []
        self.downloaded_payload = downloaded_payload
        self.search_data_calls: list[dict[str, Any]] = []
        self.login_calls: list[dict[str, Any]] = []
        self.download_calls: list[dict[str, Any]] = []

    def search_datasets(self, **kwargs: Any) -> list[FakeCollection]:
        product = next(p for p in PRODUCTS if p.short_name == kwargs["short_name"])
        return [
            FakeCollection(
                {
                    "meta": {"concept-id": product.expected_collection_id},
                    "umm": {
                        "ShortName": product.short_name,
                        "Version": product.version,
                    },
                }
            )
        ]

    def search_data(self, **kwargs: Any) -> list[FakeGranule]:
        self.search_data_calls.append(kwargs)
        return self.granules[: kwargs["count"]]

    def login(self, **kwargs: Any) -> SimpleNamespace:
        self.login_calls.append(kwargs)
        return SimpleNamespace(authenticated=True)

    def download(self, granules: list[FakeGranule], **kwargs: Any) -> list[Path]:
        self.download_calls.append(kwargs)
        granule_name = granules[0]["umm"]["GranuleUR"].rsplit(":", maxsplit=1)[-1]
        path = Path(kwargs["local_path"]) / granule_name
        if self.downloaded_payload == "html":
            path.write_text(
                "<!doctype html><html>provider error</html>", encoding="utf-8"
            )
        else:
            write_tiny_netcdf(path)
        return [path]


def fake_granule(size_mib: float = 23.9) -> FakeGranule:
    return FakeGranule(
        {
            "meta": {
                "concept-id": "G1413723174-GES_DISC",
                "collection-concept-id": GLDAS.expected_collection_id,
            },
            "umm": {
                "GranuleUR": "GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4",
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2005-01-01T00:00:00Z",
                        "EndingDateTime": "2005-01-31T23:59:59Z",
                    }
                },
            },
            "size": size_mib,
            "size_mib": size_mib,
        }
    )


def write_tiny_netcdf(path: Path) -> None:
    values = np.array([[[0.0, -9999.0], [2.5, 3.0]]], dtype=np.float32)
    dataset = xr.Dataset(
        {GLDAS.variable: (("time", "lat", "lon"), values)},
        coords={
            "time": (
                "time",
                [0.0],
                {"units": "hours since 2005-01-01 00:00:00", "calendar": "standard"},
            ),
            "lat": ("lat", [-35.0, -34.75], {"units": "degrees_north"}),
            "lon": ("lon", [147.0, 147.25], {"units": "degrees_east"}),
        },
    )
    dataset[GLDAS.variable].attrs.update(
        {"units": "kg m-2", "scale_factor": 0.1, "add_offset": 2.0}
    )
    dataset.to_netcdf(
        path, engine="netcdf4", encoding={GLDAS.variable: {"_FillValue": -9999.0}}
    )


def test_month_window_is_inclusive_and_bounded() -> None:
    assert month_bounds("2005-01") == ("2005-01-01T00:00:00Z", "2005-01-31T23:59:59Z")
    assert month_bounds("2024-02")[1] == "2024-02-29T23:59:59Z"
    with pytest.raises(ProbeError):
        month_bounds("2025-01")


def test_bounded_discovery_reports_all_products_without_authentication() -> None:
    client = FakeEarthaccess([fake_granule()])
    result = discover(month="2005-01", limit=1, bbox=DEFAULT_BBOX, client=client)
    assert result["authentication_required"] is False
    assert [r["product"]["short_name"] for r in result["results"]] == [
        p.short_name for p in PRODUCTS
    ]
    assert all(
        r["status"] == "found" and len(r["granules"]) == 1 for r in result["results"]
    )
    assert all("links" not in r["granules"][0] for r in result["results"])
    assert client.search_data_calls[0]["temporal"] == (
        "2005-01-01T00:00:00Z",
        "2005-01-31T23:59:59Z",
    )
    assert client.search_data_calls[0]["bounding_box"] == DEFAULT_BBOX
    assert client.search_data_calls[0]["short_name"] == PRODUCTS[0].short_name
    assert client.search_data_calls[0]["version"] == PRODUCTS[0].version


def test_spatial_query_builds_with_earthaccess_collection_guard() -> None:
    for product in PRODUCTS:
        query = DataGranules().parameters(
            collection_concept_id=product.expected_collection_id,
            short_name=product.short_name,
            version=product.version,
            temporal=("2005-01-01T00:00:00Z", "2005-01-31T23:59:59Z"),
            bounding_box=DEFAULT_BBOX,
        )
        assert "short_name" in query._build_url()


def test_empty_catalog_result_is_reported() -> None:
    result = discover_product(GLDAS, "2005-01", 1, DEFAULT_BBOX, FakeEarthaccess())
    assert result["status"] == "no_granules"
    assert result["granules"] == []


def test_error_output_does_not_expose_signed_urls_or_tokens() -> None:
    payload = safe_error(RuntimeError("https://host.example/file?token=do-not-print"))
    assert payload["type"] == "RuntimeError"
    assert "do-not-print" not in json.dumps(payload)


def test_inspection_preserves_raw_attrs_and_nulls_fill_values(tmp_path: Path) -> None:
    file_path = tmp_path / "tiny-fake-gldas.nc4"
    write_tiny_netcdf(file_path)
    report = inspect_netcdf(file_path, GLDAS.variable)
    assert report["status"] == "opened"
    assert report["reader"]["mask_and_scale"] is False
    assert report["reader"]["automatic_transformations_applied"] == []
    assert report["variable"]["attributes"]["_FillValue"] == -9999.0
    assert report["variable"]["units"] == "kg m-2"
    assert report["variable"]["scale_factor"] == 0.1
    assert report["variable"]["add_offset"] == 2.0
    assert report["variable"]["preview"]["raw_subset_values_null_for_missing"] == [
        0.0,
        None,
        2.5,
        3.0,
    ]
    assert report["coordinates"]["time"]["attributes"]["calendar"] == "standard"


def test_inspection_rejects_html_and_missing_variable(tmp_path: Path) -> None:
    html = tmp_path / "error.nc4"
    html.write_text("<!doctype html><html>login</html>", encoding="utf-8")
    with pytest.raises(ProbeError, match="HTML"):
        inspect_netcdf(html, GLDAS.variable)
    nc_file = tmp_path / "without-variable.nc4"
    xr.Dataset({"other": (("x",), [1.0])}).to_netcdf(nc_file, engine="netcdf4")
    with pytest.raises(ProbeError, match="absent"):
        inspect_netcdf(nc_file, GLDAS.variable)


def test_download_limit_is_checked_before_authentication(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule(size_mib=70.0)])
    with pytest.raises(ProbeError, match="exceeds"):
        download_gldas(month="2005-01", max_mib=64, output_dir=tmp_path, client=client)
    assert client.login_calls == []
    assert client.download_calls == []


def test_download_opens_one_file_and_writes_sanitized_manifest(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule()])
    result = download_gldas(
        month="2005-01", max_mib=64, output_dir=tmp_path, client=client
    )
    data_file = tmp_path / "GLDAS_NOAH025_M.A200501.021.nc4"
    manifest_file = tmp_path / "GLDAS_NOAH025_M.A200501.021.nc4.manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert result["status"] == "downloaded_and_opened"
    assert data_file.is_file() and data_file.stat().st_size > 0
    assert manifest["bytes"] == data_file.stat().st_size
    assert manifest["sha256"] == result["sha256"]
    assert manifest["inspection"]["status"] == "opened"
    assert manifest["product"]["doi"] == GLDAS.doi
    assert manifest["producer_granule_id"] == (
        "GLDAS_NOAH025_M.2.1:GLDAS_NOAH025_M.A200501.021.nc4"
    )
    assert manifest["filename"] == data_file.name
    assert manifest["stages"] == {
        "authentication": {"status": "succeeded"},
        "download": {"status": "succeeded", "files": 1},
        "read": {"status": "succeeded", "format": "NetCDF4"},
        "inspection": {"status": "succeeded", "variable": GLDAS.variable},
    }
    assert manifest["inspection"]["variable"]["preview"][
        "raw_subset_values_null_for_missing"
    ] == [0.0, None, 2.5, 3.0]
    assert client.login_calls == [{"strategy": "netrc", "persist": False}]
    assert len(client.download_calls) == 1
    assert client.search_data_calls[0]["short_name"] == GLDAS.short_name
    assert client.search_data_calls[0]["version"] == GLDAS.version
    assert "token" not in manifest_file.read_text(encoding="utf-8").lower()


def test_download_stops_if_authentication_is_not_confirmed(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule()])
    client.login = lambda **kwargs: SimpleNamespace(authenticated=False)  # type: ignore[method-assign]
    with pytest.raises(
        ProbeError, match="authentication did not report success"
    ) as error:
        download_gldas(month="2005-01", max_mib=64, output_dir=tmp_path, client=client)
    assert safe_error(error.value)["stage"] == "authentication"
    assert client.download_calls == []
    assert list(tmp_path.glob("*.nc4")) == []


def test_download_provider_failures_report_safe_stage(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule()])
    client.download = lambda *args, **kwargs: (_ for _ in ()).throw(  # type: ignore[method-assign]
        RuntimeError("https://provider.invalid/file?token=secret")
    )
    with pytest.raises(ProbeError, match="file transfer failed") as error:
        download_gldas(month="2005-01", max_mib=64, output_dir=tmp_path, client=client)
    payload = safe_error(error.value)
    assert payload["stage"] == "download"
    assert "secret" not in json.dumps(payload)


def test_download_catalog_failure_reports_safe_stage(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule()])
    client.search_datasets = lambda **kwargs: (_ for _ in ()).throw(  # type: ignore[method-assign]
        RuntimeError("catalog URL with private response")
    )
    with pytest.raises(ProbeError, match="catalog lookup failed") as error:
        download_gldas(month="2005-01", max_mib=64, output_dir=tmp_path, client=client)
    payload = safe_error(error.value)
    assert payload["stage"] == "catalog"
    assert "private response" not in json.dumps(payload)


def test_download_rejects_html_without_leaving_a_granule(tmp_path: Path) -> None:
    client = FakeEarthaccess([fake_granule()], downloaded_payload="html")
    with pytest.raises(ProbeError, match="HTML"):
        download_gldas(month="2005-01", max_mib=64, output_dir=tmp_path, client=client)
    assert list(tmp_path.glob("*.nc4")) == []
    assert list(tmp_path.glob("*.manifest.json")) == []
