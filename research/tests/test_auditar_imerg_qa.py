import hashlib

import h5py
import numpy as np
import pytest

from research.auditar_imerg_qa import build_inventory, inspect_file


def _create_granule(path, *, qa_fields=(), bad_precip_shape=False, declared_period=None):
    with h5py.File(path, "w") as handle:
        period = declared_period or ("200501" if "2005" in path.name else "202101")
        granule_name = (
            f"3B-MO.MS.MRG.3IMERG.{period}01-S000000-E235959.{period[4:]}.V07B.HDF5"
        )
        handle.attrs["FileHeader"] = (
            "DOI=10.5067/GPM/IMERG/3B-MONTH/07;\n"
            "DOIshortName=3IMERGM;\n"
            "AlgorithmID=3IMERGM;\n"
            "AlgorithmVersion=3IMERGM_7.0;\n"
            f"FileName={granule_name};\n"
        )
        grid = handle.create_group("Grid")
        grid.attrs["GridHeader"] = "Registration=CENTER;"
        precip_shape = (1, 4, 2) if not bad_precip_shape else (4, 2)
        precip = grid.create_dataset("precipitation", shape=precip_shape, dtype="f4")
        precip.attrs["DimensionNames"] = "time,lon,lat"
        precip.attrs["units"] = "mm/hr"
        precip.attrs["_FillValue"] = np.float32(-9999.9)
        precip.attrs["CodeMissingValue"] = np.float32(-9999.9)
        if not bad_precip_shape:
            for name in qa_fields:
                qa = grid.create_dataset(name, shape=precip_shape, dtype="f4")
                qa.attrs["DimensionNames"] = "time,lon,lat"
                qa.attrs["_FillValue"] = np.float32(-9999.9)
                qa.attrs["CodeMissingValue"] = np.float32(-9999.9)
        grid.create_dataset("time", data=np.array([0], dtype="i4"))
        grid.create_dataset("time_bnds", data=np.zeros((1, 2), dtype="i4"))
        grid.create_dataset("lon", data=np.arange(4, dtype="f4"))
        grid.create_dataset("lat", data=np.arange(2, dtype="f4"))
        grid.create_dataset("lon_bnds", data=np.zeros((4, 2), dtype="f4"))
        grid.create_dataset("lat_bnds", data=np.zeros((2, 2), dtype="f4"))


def test_inspection_records_metadata_and_optional_qa_presence(tmp_path):
    path = tmp_path / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    _create_granule(path, qa_fields=("randomError", "precipitationQualityIndex"))

    entry = inspect_file(path, "NASA")

    assert entry["period"] == "2005-01"
    assert entry["file_version"] == "V07B"
    assert entry["fields"]["precipitation"]["shape"] == [1, 4, 2]
    assert entry["fields"]["precipitation"]["dtype"] == "float32"
    assert entry["fields"]["precipitation"]["attributes"]["units"] == "mm/hr"
    assert entry["fields"]["precipitation"]["attributes"]["_FillValue"] == pytest.approx(-9999.9)
    assert entry["fields"]["randomError"]["present"] is True
    assert entry["fields"]["precipitationQualityIndex"]["present"] is True
    assert "units" in entry["fields"]["precipitationQualityIndex"]["not_declared_attributes"]
    assert "scale_factor" in entry["fields"]["precipitation"]["not_declared_attributes"]
    assert entry["fields"]["gaugeRelativeWeighting"]["present"] is False
    assert entry["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_inspection_fails_for_malformed_precipitation_dimensions(tmp_path):
    path = tmp_path / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    _create_granule(path, bad_precip_shape=True)

    with pytest.raises(ValueError, match="debe tener 3 dimensiones"):
        inspect_file(path, "NASA")


def test_inspection_fails_when_embedded_period_disagrees_with_filename(tmp_path):
    path = tmp_path / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    _create_granule(path, declared_period="202101")

    with pytest.raises(ValueError, match="Periodo/versión del archivo no coincide"):
        inspect_file(path, "NASA")


def test_inventory_confirms_january_byte_identity_and_labels_unassessed(tmp_path):
    nasa_dir, ncar_dir = tmp_path / "nasa", tmp_path / "ncar"
    nasa_dir.mkdir()
    ncar_dir.mkdir()
    nasa_file = nasa_dir / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    ncar_file = ncar_dir / "imerg_200501_v07b_ncar.h5"
    _create_granule(nasa_file, qa_fields=("randomError",))
    ncar_file.write_bytes(nasa_file.read_bytes())

    inventory = build_inventory(nasa_dir, ncar_dir)

    assert len(inventory["entries"]) == 2
    assert inventory["nasa_ncar_comparison"]["status"] == "byte_identical"
    assert inventory["qa_status"] == "unassessed"
