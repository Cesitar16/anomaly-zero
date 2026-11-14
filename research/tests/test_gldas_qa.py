from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from research.gldas_qa import inspect_gldas_sample


def _write_sample(
    path,
    *,
    values=None,
    lat=(-38.0, -24.0),
    lon=(138.0, 145.0, 153.0),
    variable_name="SoilMoi0_10cm_inst",
):
    if values is None:
        values = [[[0.0, -9999.0, np.nan], [4.0, 5.0, 6.0]]]
    dataset = xr.Dataset(
        {
            variable_name: (
                ("time", "lat", "lon"),
                np.array(values, dtype=np.float32),
                {"units": "kg m-2", "_FillValue": np.float32(-9999.0)},
            )
        },
        coords={"time": [0], "lat": list(lat), "lon": list(lon)},
    )
    dataset.to_netcdf(path, engine="netcdf4")


def test_qa_counts_zero_as_valid_and_fill_or_nan_as_missing(tmp_path):
    path = tmp_path / "synthetic-fixture.nc4"
    _write_sample(path)

    dataset, report = inspect_gldas_sample(path)
    try:
        assert report["valid_count"] == 4
        assert report["missing_count"] == 2
        assert report["coverage_fraction"] == pytest.approx(4 / 6)
        assert report["raw_valid_summary"] == {
            "min": 0.0,
            "median": 4.5,
            "mean": 3.75,
            "max": 6.0,
        }
        assert report["bbox_semantics"].startswith("inclusive rectangular")
        assert report["transformations_applied"] == []
        assert dataset["SoilMoi0_10cm_inst"].attrs["_FillValue"] == -9999.0
    finally:
        dataset.close()


def test_qa_reports_empty_bbox_selection(tmp_path):
    path = tmp_path / "synthetic-fixture.nc4"
    _write_sample(path)

    dataset, report = inspect_gldas_sample(path, bbox=(140, -35, 150, -25))
    try:
        assert report["subset_shape"] == [1, 0, 1]
        assert report["raw_value_count"] == 0
        assert report["valid_count"] == 0
        assert report["coverage_fraction"] == 0.0
        assert report["subset_coordinates"]["lat_min"] is None
    finally:
        dataset.close()


def test_qa_handles_descending_latitudes_and_selects_expected_cell(tmp_path):
    path = tmp_path / "synthetic-descending-latitude.nc4"
    values = [[[30.0, 31.0, 32.0], [20.0, 21.0, 22.0], [10.0, 11.0, 12.0]]]
    _write_sample(path, values=values, lat=(-24.0, -31.0, -38.0))

    dataset, report = inspect_gldas_sample(path, bbox=(140, -35, 150, -25))
    try:
        assert report["subset_shape"] == [1, 1, 1]
        assert report["valid_count"] == 1
        assert report["raw_valid_summary"] == {
            "min": 21.0,
            "median": 21.0,
            "mean": 21.0,
            "max": 21.0,
        }
    finally:
        dataset.close()


def test_qa_reports_all_values_missing(tmp_path):
    path = tmp_path / "synthetic-all-missing.nc4"
    values = [[[-9999.0, np.nan, -9999.0], [-9999.0, np.nan, -9999.0]]]
    _write_sample(path, values=values)

    dataset, report = inspect_gldas_sample(path)
    try:
        assert report["raw_value_count"] == 6
        assert report["valid_count"] == 0
        assert report["missing_count"] == 6
        assert report["coverage_fraction"] == 0.0
        assert report["raw_valid_summary"] is None
    finally:
        dataset.close()


def test_qa_rejects_missing_sample(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_gldas_sample(tmp_path / "absent.nc4")


def test_qa_rejects_invalid_nonmonotonic_coordinates(tmp_path):
    path = tmp_path / "synthetic-invalid-coordinates.nc4"
    values = [[[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]]
    _write_sample(path, values=values, lat=(-38.0, -24.0, -30.0))

    with pytest.raises(ValueError, match="strictly monotonic"):
        inspect_gldas_sample(path)


def test_qa_rejects_missing_required_variable(tmp_path):
    path = tmp_path / "synthetic-missing-variable.nc4"
    _write_sample(path, variable_name="another_variable")

    with pytest.raises(ValueError, match="required variable"):
        inspect_gldas_sample(path)
