from __future__ import annotations

import hashlib

import h5py
import numpy as np
import pytest

from research.inspeccionar_linaje_gldas import build_inventory, inspect_sample


def _write_fixture(path, *, sample_id="gldas-2005-01", time=1827.0):
    with h5py.File(path, "w") as target:
        time_ds = target.create_dataset("time", data=np.array([time], dtype=np.float64))
        lat_ds = target.create_dataset(
            "lat", data=np.linspace(-59.875, 89.875, 600, dtype=np.float32)
        )
        lon_ds = target.create_dataset(
            "lon", data=np.linspace(-179.875, 179.875, 1440, dtype=np.float32)
        )
        bounds_ds = target.create_dataset(
            "time_bnds", data=np.array([[time, time + 31]], dtype=np.float64)
        )
        target.attrs["history"] = "synthetic fixture"
        variable = target.create_dataset(
            "SoilMoi0_10cm_inst",
            data=np.zeros((1, 600, 1440), dtype=np.float32),
            fillvalue=np.float32(-9999),
        )
        time_ds.make_scale("time")
        lat_ds.make_scale("lat")
        lon_ds.make_scale("lon")
        for dim, scale in enumerate((time_ds, lat_ds, lon_ds)):
            variable.dims[dim].attach_scale(scale)
        variable.attrs["units"] = "kg m-2"
        variable.attrs["cell_methods"] = "time: mean"
        variable.attrs["_FillValue"] = np.array([-9999], dtype=np.float32)
        time_ds.attrs["units"] = "days since 2000-01-01 00:00:00"
        time_ds.attrs["calendar"] = "standard"
        time_ds.attrs["bounds"] = "time_bnds"
        bounds_ds.attrs["description"] = "time interval"
        lat_ds.attrs["units"] = "degrees_north"
        lon_ds.attrs["units"] = "degrees_east"
    return path


def _record(path, *, sample_id="gldas-2005-01", time=1827.0):
    digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    year = "2005" if sample_id.endswith("2005-01") else "2021"
    month_code = f"{year}01"
    return {
        "sample_id": sample_id,
        "period": f"{year}-01",
        "filename": f"GLDAS_NOAH025_M.A{month_code}.021.nc4",
        "source": "NASA GES DISC original granule (synthetic fixture)",
        "cmr": {"concept_id": "fixture"},
        "size_bytes": path.stat().st_size,
        "sha256": digest,
        "time_value_days": time,
        "time_bounds_days": [time, time + 31],
    }


def test_inventory_records_identity_structure_and_attributes(tmp_path):
    path = _write_fixture(tmp_path / "GLDAS_NOAH025_M.A200501.021.nc4")
    report = inspect_sample(path, _record(path))

    assert report["sample_id"] == "gldas-2005-01"
    assert report["variable"]["path"] == "/SoilMoi0_10cm_inst"
    assert report["variable"]["shape"] == [1, 600, 1440]
    assert report["variable"]["dtype"] == "float32"
    assert report["variable"]["dimension_scales_by_axis"] == [["time"], ["lat"], ["lon"]]
    assert report["variable"]["attributes"]["_FillValue"] == [-9999.0]
    assert report["coordinates"]["time"]["attributes"]["calendar"] == "standard"
    assert report["qa_assessment"] == "unassessed"


def test_inventory_rejects_incompatible_hash_and_period(tmp_path):
    path = _write_fixture(tmp_path / "GLDAS_NOAH025_M.A200501.021.nc4")
    record = _record(path)
    record["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="SHA-256 incompatible"):
        inspect_sample(path, record)

    record = _record(path)
    record["time_value_days"] = 999.0
    with pytest.raises(ValueError, match="Periodo temporal incompatible"):
        inspect_sample(path, record)


def test_inventory_requires_exactly_the_manifest_samples(tmp_path):
    manifest = {"samples": []}
    with pytest.raises(ValueError, match="Se requieren exactamente"):
        build_inventory({"unexpected": tmp_path / "missing.nc4"}, manifest)


def test_inspection_rejects_wrong_filename_before_reading(tmp_path):
    path = tmp_path / "other.nc4"
    path.touch()
    record = {
        "sample_id": "gldas-2005-01",
        "filename": "GLDAS_NOAH025_M.A200501.021.nc4",
    }
    with pytest.raises(ValueError, match="Identidad de archivo incompatible"):
        inspect_sample(path, record)
