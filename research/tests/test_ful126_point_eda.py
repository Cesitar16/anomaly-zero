"""Offline tests for the provisional FUL-126 point extraction utilities."""

from __future__ import annotations

import h5py
import numpy as np
import pytest
from netCDF4 import Dataset
from shapely.geometry import Polygon

from research.ful124_spatial_audit import SpatialAuditError, load_boundary
from research.ful126_point_eda import (
    MONTHS,
    PointEdaError,
    _read_cells_from_payload,
    adjacent_cells,
    classify_value,
    containing_cells,
    nearest_center_cell,
    portable_output_names,
    select_candidate_sites,
    validate_month_coverage,
)


def test_three_candidates_are_repeatable_and_inside_polygon() -> None:
    polygon = Polygon([(140, -36), (151, -36), (151, -29), (140, -29), (140, -36)])

    first = select_candidate_sites(polygon)
    second = select_candidate_sites(polygon)

    assert [site["site_id"] for site in first] == [
        "site_west_extent", "site_central_extent", "site_east_extent"
    ]
    assert [(s["longitude"], s["latitude"]) for s in first] == [
        (s["longitude"], s["latitude"]) for s in second
    ]
    assert all(site["inside_exploratory_polygon"] for site in first)
    assert all(site["status"] == "candidate_not_approved" for site in first)


def test_missing_or_duplicate_product_month_fails_closed() -> None:
    complete = {product: [{"period": month} for month in MONTHS] for product in ("imerg_final", "merra2", "gldas")}
    validate_month_coverage(complete, set(MONTHS))

    incomplete = {**complete, "merra2": complete["merra2"][:-1]}
    with pytest.raises(PointEdaError, match="exactly one"):
        validate_month_coverage(incomplete, set(MONTHS))
    duplicated = {**complete, "gldas": complete["gldas"][:-1] + [{"period": MONTHS[0]}]}
    with pytest.raises(PointEdaError, match="exactly one"):
        validate_month_coverage(duplicated, set(MONTHS))


def test_modified_boundary_hash_is_rejected(tmp_path) -> None:
    path = tmp_path / "synthetic_boundary.geojson"
    path.write_text(
        '{"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Polygon","coordinates":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]},"properties":{}}]}',
        encoding="utf-8",
    )

    with pytest.raises(SpatialAuditError, match="SHA-256"):
        load_boundary(path)


def test_nearest_cell_uses_latitude_row_and_longitude_column() -> None:
    site = {"longitude": 140.4, "latitude": -34.6}
    grid = {
        "lat": np.array([-35.0, -34.5, -34.0]),
        "lon": np.array([140.0, 140.5, 141.0]),
    }

    result = nearest_center_cell(site, grid)

    assert result["row_latitude"] == 1
    assert result["column_longitude"] == 1
    assert result["site_to_center_geodesic_distance_m"] > 0


def test_containment_keeps_all_inclusive_hits_and_reports_gaps() -> None:
    grid = {
        "lat": np.array([0.0, 1.0]),
        "lon": np.array([0.0, 1.0]),
        "lat_bounds": np.array([[-0.5, 0.5], [0.5, 1.5]]),
        "lon_bounds": np.array([[-0.5, 0.5], [0.5, 1.5]]),
    }

    assert containing_cells({"longitude": 0.5, "latitude": 0.5}, grid, "inferred_bounds") == [
        {"row_latitude": 0, "column_longitude": 0},
        {"row_latitude": 0, "column_longitude": 1},
        {"row_latitude": 1, "column_longitude": 0},
        {"row_latitude": 1, "column_longitude": 1},
    ]
    assert containing_cells({"longitude": 0.5, "latitude": 0.25}, grid, "native_bounds") == [
        {"row_latitude": 0, "column_longitude": 0},
        {"row_latitude": 0, "column_longitude": 1},
    ]
    gap_grid = {**grid, "lat_bounds": np.array([[-0.4, 0.4], [0.6, 1.4]])}
    assert containing_cells({"longitude": 0.0, "latitude": 0.5}, gap_grid, "inferred_bounds") == []


def test_adjacent_cells_are_four_connected_and_do_not_wrap_longitude() -> None:
    grid = {"lat": np.arange(3), "lon": np.arange(4)}

    assert adjacent_cells({"row_latitude": 1, "column_longitude": 0}, grid) == [
        {"row_latitude": 0, "column_longitude": 0},
        {"row_latitude": 2, "column_longitude": 0},
        {"row_latitude": 1, "column_longitude": 1},
    ]


@pytest.mark.parametrize(
    ("raw", "markers", "scale", "offset", "stored_status", "decoded", "decoded_status"),
    [
        (0.0, [-9999.0], 2.0, 1.0, "zero_valid", 1.0, "finite"),
        (-9999.0, [-9999.0], 2.0, 1.0, "fill", None, "fill"),
        (float("nan"), [-9999.0], 1.0, 0.0, "nan", None, "nan"),
        (float("inf"), [-9999.0], 1.0, 0.0, "nonfinite", None, "nonfinite"),
        (-4.0, [-9999.0], 1.0, 0.0, "finite", -4.0, "negative_finite_review"),
        (2.0, [], float("inf"), 0.0, "finite", None, "nonfinite_after_scale_offset"),
    ],
)
def test_values_are_classified_before_optional_scale_offset(
    raw, markers, scale, offset, stored_status, decoded, decoded_status
) -> None:
    result = classify_value(raw, markers, scale, offset)

    assert result["stored_status"] == stored_status
    assert result["decoded_value"] == decoded
    assert result["decoded_status"] == decoded_status


def test_imerg_native_time_lon_lat_indexing_and_fill_classification(tmp_path) -> None:
    path = tmp_path / "imerg.h5"
    with h5py.File(path, "w") as handle:
        group = handle.create_group("Grid")
        variable = group.create_dataset("precipitation", data=np.array([[[10.0, -9999.9], [0.0, 4.0]]], dtype="f4"))
        variable.attrs["Units"] = "mm/hr"
        variable.attrs["_FillValue"] = np.float32(-9999.9)
    values, metadata = _read_cells_from_payload(
        path,
        "imerg_final",
        [{"row_latitude": 1, "column_longitude": 0}, {"row_latitude": 0, "column_longitude": 1}],
    )

    assert np.isclose(values[(1, 0)]["stored_value"], -9999.9)
    assert values[(1, 0)]["stored_status"] == "fill"
    assert values[(0, 1)]["stored_value"] == 0
    assert values[(0, 1)]["stored_status"] == "zero_valid"
    assert metadata["auto_maskandscale_disabled"] is True


@pytest.mark.parametrize(
    ("product", "variable_name", "unit"),
    [
        ("merra2", "T2M", "K"),
        ("gldas", "SoilMoi0_10cm_inst", "kg m-2"),
    ],
)
def test_netcdf_native_time_lat_lon_indexing_and_scale_once(
    tmp_path, product, variable_name, unit
) -> None:
    path = tmp_path / f"{product}.nc4"
    with Dataset(path, "w") as dataset:
        dataset.createDimension("time", 1)
        dataset.createDimension("lat", 2)
        dataset.createDimension("lon", 2)
        variable = dataset.createVariable(variable_name, "i2", ("time", "lat", "lon"), fill_value=-999)
        variable.units = unit
        variable.scale_factor = 2.0
        variable.add_offset = 0.0
        variable.set_auto_maskandscale(False)
        variable[:] = np.array([[[1, 2], [3, 4]]], dtype="i2")

    values, metadata = _read_cells_from_payload(
        path, product, [{"row_latitude": 1, "column_longitude": 0}]
    )

    value = values[(1, 0)]
    assert value["stored_value"] == 3.0
    assert value["decoded_value"] == 6.0
    assert value["scale_factor_applied"] == 2.0
    assert metadata["auto_maskandscale_disabled"] is True


def test_manifest_writer_does_not_include_local_roots(tmp_path) -> None:
    outputs = portable_output_names(
        {"charts": [(tmp_path / "Cesar" / "private" / "site.png").as_posix()]}
    )

    assert outputs == {"charts": ["site.png"]}
