from __future__ import annotations

import numpy as np
import pytest
import xarray as xr

from research.gldas_qa import inspect_gldas_sample


def _write_sample(path):
    dataset = xr.Dataset(
        {
            "SoilMoi0_10cm_inst": (
                ("time", "lat", "lon"),
                np.array([[[1.0, -9999.0, 3.0], [4.0, 5.0, 6.0]]], dtype=np.float32),
                {"units": "kg m-2", "_FillValue": np.float32(-9999.0)},
            )
        },
        coords={"time": [0], "lat": [-38.0, -24.0], "lon": [138.0, 145.0, 153.0]},
    )
    dataset.to_netcdf(path, engine="netcdf4")


def test_qa_counts_fill_values_and_keeps_zero_valid(tmp_path):
    path = tmp_path / "synthetic-fixture.nc4"
    _write_sample(path)

    dataset, report = inspect_gldas_sample(path)
    try:
        assert report["valid_count"] == 5
        assert report["missing_count"] == 1
        assert report["coverage_fraction"] == pytest.approx(5 / 6)
        assert report["raw_valid_summary"] == {
            "min": 1.0,
            "median": 4.0,
            "mean": 3.8,
            "max": 6.0,
        }
        assert report["bbox_semantics"].startswith("inclusive rectangular")
        assert report["transformations_applied"] == []
        assert dataset["SoilMoi0_10cm_inst"].attrs["_FillValue"] == -9999.0
    finally:
        dataset.close()


def test_qa_selects_only_coordinates_inside_bbox(tmp_path):
    path = tmp_path / "synthetic-fixture.nc4"
    _write_sample(path)

    dataset, report = inspect_gldas_sample(path, bbox=(140, -35, 150, -25))
    try:
        assert report["subset_shape"] == [1, 0, 1]
        assert report["raw_value_count"] == 0
        assert report["coverage_fraction"] == 0.0
    finally:
        dataset.close()


def test_qa_rejects_missing_sample(tmp_path):
    with pytest.raises(FileNotFoundError):
        inspect_gldas_sample(tmp_path / "absent.nc4")
