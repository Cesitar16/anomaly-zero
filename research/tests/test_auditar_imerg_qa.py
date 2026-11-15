import hashlib
import json

import h5py
import numpy as np
import pytest

from research.auditar_imerg_qa import (
    CenterMaskCache,
    build_domain_masks,
    build_inventory,
    classify_values,
    describe_distribution,
    inspect_file,
    select_phase2_samples,
    summarize_sample,
)


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


def test_select_phase2_samples_uses_unique_2005_months_and_january_2021():
    entries = [
        {"source_label": "NASA", "period": "2005-01", "file": "nasa-jan", "sha256": "same"},
        {"source_label": "NCAR", "period": "2005-01", "file": "ncar-jan", "sha256": "same"},
        *[
            {"source_label": "NCAR", "period": f"2005-{month:02d}", "file": f"ncar-{month}", "sha256": str(month)}
            for month in range(2, 13)
        ],
        {"source_label": "NASA", "period": "2021-01", "file": "nasa-2021", "sha256": "2021"},
    ]

    selected = select_phase2_samples(entries)

    assert len(selected) == 13
    assert selected[0]["file"] == "nasa-jan"
    assert selected[-1]["file"] == "nasa-2021"
    assert len({entry["period"] for entry in selected}) == 13


def test_select_phase2_samples_rejects_changed_january_identity():
    entries = [
        {"source_label": "NASA", "period": "2005-01", "sha256": "a"},
        {"source_label": "NCAR", "period": "2005-01", "sha256": "b"},
    ]

    with pytest.raises(ValueError, match="ya no son byte-idénticos"):
        select_phase2_samples(entries)


def test_build_domain_masks_uses_inclusive_bbox_and_lon_lat_order():
    lon = np.array([137.9, 138.0, 153.0, 153.1])
    lat = np.array([-38.1, -38.0, -24.0, -23.9])
    basin_lat_lon = np.zeros((4, 4), dtype=bool)
    basin_lat_lon[2, 1] = True  # lat index 2, lon index 1

    masks = build_domain_masks(lon, lat, basin_lat_lon)

    assert masks["global"] is None
    assert masks["bbox_centers"].shape == (4, 4)
    assert int(masks["bbox_centers"].sum()) == 4
    assert masks["basin_centers"][1, 2]
    assert int(masks["basin_centers"].sum()) == 1


def test_classify_values_partitions_fill_nonfinite_and_valid_zero():
    fill = np.float32(-9999.9)
    values = np.array([0.0, fill, np.nan, 2.0], dtype=np.float32)

    assert classify_values(values, float(fill)) == {
        "total": 4,
        "fill": 1,
        "non_finite": 1,
        "finite_non_fill": 2,
        "zero_valid": 1,
    }


def test_describe_distribution_has_exact_quantiles_and_original_counts():
    values = np.array([0, 1, 2, 3, -9999], dtype=np.int16)

    result = describe_distribution(values, -9999, exact_counts=True)

    assert result["n"] == 4
    assert result["min"] == 0
    assert result["max"] == 3
    assert result["quantiles"]["p50"] == pytest.approx(1.5)
    assert result["value_counts"] == {"0.0": 1, "1.0": 1, "2.0": 1, "3.0": 1}


def test_summarize_sample_applies_center_mask_in_hdf_lon_lat_order(tmp_path):
    sample_path = tmp_path / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    _create_granule(sample_path, qa_fields=("randomError",))
    with h5py.File(sample_path, "a") as handle:
        values = np.arange(8, dtype="f4").reshape((1, 4, 2))
        values[0, 2, 0] = 0
        values[0, 1, 1] = np.float32(-9999.9)
        handle["Grid/precipitation"][:] = values
    polygon_path = tmp_path / "basin.geojson"
    polygon_path.write_text(json.dumps({
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {
            "type": "Polygon", "coordinates": [[[1.8, -0.2], [2.2, -0.2], [2.2, 0.2], [1.8, 0.2], [1.8, -0.2]]]
        }}],
    }), encoding="utf-8")
    entry = {"period": "2005-01", "source_label": "NASA", "file": sample_path.name,
             "file_version": "V07B", "sha256": hashlib.sha256(sample_path.read_bytes()).hexdigest()}

    result = summarize_sample(
        sample_path, entry, CenterMaskCache(), polygon_path, bbox=(0, 0, 3, 1)
    )

    assert result["domains"]["basin_centers"]["n"] == 1
    precip = result["fields"]["precipitation"]
    assert precip["counts"]["basin_centers"] == {
        "total": 1, "fill": 0, "non_finite": 0, "finite_non_fill": 1, "zero_valid": 1
    }
    assert result["fields"]["gaugeRelativeWeighting"]["present"] is False
    assert result["fields"]["gaugeRelativeWeighting"]["counts"] is None
    assert result["qa_status"] == "unassessed"
