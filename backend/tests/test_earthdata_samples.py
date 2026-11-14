from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import h5py
import numpy as np
import pytest
import xarray as xr

from backend.app.data_sources import earthdata_probe, earthdata_samples

IMERG_FILENAME = "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"


def write_imerg(path: Path) -> None:
    with h5py.File(path, "w") as h5:
        grid = h5.create_group("Grid")
        time = grid.create_dataset("time", data=np.array([0], dtype=np.int32))
        lat = grid.create_dataset(
            "lat", data=np.array([-35.0, -34.9], dtype=np.float32)
        )
        lon = grid.create_dataset(
            "lon", data=np.array([147.0, 147.1], dtype=np.float32)
        )
        time.make_scale("time")
        lat.attrs["units"] = "degrees_north"
        lon.attrs["units"] = "degrees_east"
        lat.make_scale("lat")
        lon.make_scale("lon")
        values = grid.create_dataset(
            "precipitation",
            data=np.array([[[0.0, -9999.9], [1.5, 2.0]]], dtype=np.float32),
        )
        values.dims[0].attach_scale(time)
        values.dims[0].label = "time"
        values.dims[1].attach_scale(lon)
        values.dims[1].label = "lon"
        values.dims[2].attach_scale(lat)
        values.dims[2].label = "lat"
        values.attrs["units"] = "mm/hr"
        values.attrs["_FillValue"] = -9999.9
        grid.create_dataset("precipitationQualityIndex", data=np.ones((1, 2, 2)))


class Client:
    def __init__(self, size: float = 2.0, fail_manifest_publish: bool = False) -> None:
        product = earthdata_samples.PRODUCTS["imerg_final"]
        self.collection = {
            "meta": {"concept-id": product.expected_collection_id},
            "umm": {"ShortName": product.short_name, "Version": product.version},
        }
        self.granule = {
            "meta": {
                "concept-id": "G-TEST-GES_DISC",
                "collection-concept-id": product.expected_collection_id,
            },
            "umm": {
                "GranuleUR": f"GPM_3IMERGM.07:{IMERG_FILENAME}",
                "TemporalExtent": {
                    "RangeDateTime": {
                        "BeginningDateTime": "2005-01-01T00:00:00Z",
                        "EndingDateTime": "2005-01-31T23:59:59Z",
                    }
                },
            },
            "size": size,
        }
        self.login_calls: list[dict[str, Any]] = []
        self.download_calls: list[dict[str, Any]] = []
        self.fail_manifest_publish = fail_manifest_publish

    def search_datasets(self, **kwargs: Any) -> list[Any]:
        return [self.collection]

    def search_data(self, **kwargs: Any) -> list[Any]:
        return [self.granule]

    def login(self, **kwargs: Any) -> Any:
        self.login_calls.append(kwargs)
        return SimpleNamespace(authenticated=True)

    def download(self, granules: list[Any], **kwargs: Any) -> list[Path]:
        self.download_calls.append(kwargs)
        path = Path(kwargs["local_path"]) / IMERG_FILENAME
        write_imerg(path)
        return [path]


def test_imerg_hdf5_inspection_keeps_group_axis_units_and_fill(tmp_path: Path) -> None:
    path = tmp_path / IMERG_FILENAME
    write_imerg(path)
    report = earthdata_samples.inspect_product(path, "imerg_final")

    assert report["format"] == "HDF5"
    assert "Grid" in report["groups"]
    assert "Grid/precipitation" in report["dataset_paths"]
    assert report["coordinates"]["Grid/lat"]["size"] == 2
    assert report["coordinates"]["Grid/lon"]["size"] == 2
    assert report["variable"]["dimensions"] == ["time", "lon", "lat"]
    assert report["variable"]["units"] == "mm/hr"
    assert report["reader"]["automatic_transformations_applied"] == []
    assert report["variable"]["preview"]["raw_subset_values_null_for_missing"] == [
        0.0,
        None,
        1.5,
        2.0,
    ]
    assert "Grid/precipitationQualityIndex" in report["quality_variable_candidates"]


def test_merra_netcdf_axes_units_fill_and_scaling_are_reported_raw(
    tmp_path: Path,
) -> None:
    path = tmp_path / "MERRA2_300.tavgM_2d_slv_Nx.200501.nc4"
    values = np.array([[[0.0, -9999.0], [280.0, 281.0]]], dtype=np.float32)
    dataset = xr.Dataset(
        {"T2M": (("time", "lat", "lon"), values)},
        coords={
            "time": (
                "time",
                [0.0],
                {"units": "hours since 2005-01-01 00:30:00", "calendar": "standard"},
            ),
            "lat": ("lat", [-35.0, -34.5], {"units": "degrees_north"}),
            "lon": ("lon", [147.0, 147.625], {"units": "degrees_east"}),
        },
    )
    dataset["T2M"].attrs.update({"units": "K", "scale_factor": 0.01, "add_offset": 0.0})
    dataset.to_netcdf(path, engine="netcdf4", encoding={"T2M": {"_FillValue": -9999.0}})

    from backend.app.data_sources.earthdata_samples import inspect_product

    report = inspect_product(path, "merra2")

    assert report["format"] == "NetCDF4"
    assert report["variable"]["dimensions"] == ["time", "lat", "lon"]
    assert report["variable"]["units"] == "K"
    assert report["variable"]["scale_factor"] == 0.01
    assert report["reader"]["automatic_transformations_applied"] == []
    assert report["variable"]["preview"]["raw_subset_values_null_for_missing"] == [
        0.0,
        None,
        280.0,
        281.0,
    ]


def test_download_limit_rejects_imerg_before_authentication(tmp_path: Path) -> None:
    client = Client(size=23.91420269012451)
    with pytest.raises(earthdata_probe.ProbeError, match="exceeds"):
        earthdata_samples.download_product(
            "imerg_final", max_mib=23, output_dir=tmp_path, client=client
        )
    assert client.login_calls == []
    assert client.download_calls == []


def test_download_manifest_resolves_relative_path_from_current_directory(
    tmp_path: Path,
) -> None:
    client = Client()
    out_dir = tmp_path / "custom-output"
    result = earthdata_samples.download_product(
        "imerg_final", output_dir=out_dir, client=client
    )
    manifest_path = Path(result["manifest"])
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    resolved = (
        Path(manifest["relative_path_base"]) / manifest["relative_path"]
    ).resolve()
    assert resolved == Path(result["file"]).resolve()
    assert manifest["sha256"] == result["sha256"]
    assert manifest["inspection"]["format"] == "HDF5"
    assert manifest["inspection"]["variable"]["units"] == "mm/hr"


def test_manifest_publish_failure_cleans_new_imerg_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = Client()
    original = earthdata_probe._publish_no_replace

    def fail_manifest(source: Path, destination: Path) -> None:
        if destination.name.endswith(".manifest.json"):
            raise OSError("simulated")
        original(source, destination)

    monkeypatch.setattr(earthdata_probe, "_publish_no_replace", fail_manifest)
    with pytest.raises(
        earthdata_probe.ProbeError, match="publish the validated sample"
    ):
        earthdata_samples.download_product(
            "imerg_final", output_dir=tmp_path, client=client
        )
    assert list(tmp_path.rglob("*.HDF5")) == []
    assert list(tmp_path.rglob("*.manifest.json")) == []


def test_spatial_qa_counts_center_cells_and_keeps_zero_distinct_from_fill(
    tmp_path: Path,
) -> None:

    from backend.app.data_sources.earthdata_spatial import spatial_qa, write_csv

    original = tmp_path / IMERG_FILENAME
    write_imerg(original)
    manifest = tmp_path / f"{IMERG_FILENAME}.manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "period": {"month": "2005-01"},
                "bytes": original.stat().st_size,
                "sha256": hashlib.sha256(original.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    polygon = tmp_path / "polygon.geojson"
    polygon.write_text(
        json.dumps(
            {
                "type": "Polygon",
                "coordinates": [
                    [
                        [147.0, -35.0],
                        [147.11, -35.0],
                        [147.11, -34.89],
                        [147.0, -34.89],
                        [147.0, -35.0],
                    ]
                ],
            }
        ),
        encoding="utf-8",
    )

    result = spatial_qa(original, manifest, polygon, "imerg_final", max_rows=2)
    csv_path = tmp_path / "sample.csv"
    write_csv(result, csv_path)

    assert result["selection"] == "cell center within polygon; boundary included"
    assert result["surface_area_claimed"] is False
    assert result["polygon_sha256"] == hashlib.sha256(polygon.read_bytes()).hexdigest()
    assert result["denominator_center_cells"] == 4
    assert result["valid_center_cells"] == 3
    assert result["missing_center_cells"] == 1
    assert result["valid_percent"] == 75.0
    assert len(result["rows"]) == 2
    assert any(row["value"] == 0.0 for row in result["rows"])
    assert (
        csv_path.read_text(encoding="utf-8")
        .splitlines()[0]
        .startswith("period,product,version")
    )

