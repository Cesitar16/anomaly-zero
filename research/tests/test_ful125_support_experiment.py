"""Offline deterministic tests for FUL-125 candidate spatial diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from pyproj import Transformer
from shapely.geometry import Polygon

from research.ful124_spatial_audit import SpatialAuditError, load_boundary
from research.ful125_support_experiment import (
    POINT_TRIAL_STATUS,
    _point_support_trial,
    _projected_area_diagnostic,
    imerg_bounds_candidates,
    seam_summary,
)


def _polygon_file(path: Path, coords: list[list[float]]) -> Path:
    path.write_text(
        json.dumps(
            {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Polygon", "coordinates": [coords]},
                        "properties": {"fixture": "synthetic_only"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_boundary_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    path = _polygon_file(tmp_path / "synthetic.geojson", [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])

    with pytest.raises(SpatialAuditError, match="SHA-256"):
        load_boundary(path, expected_sha256="0" * 64)


def test_missing_geometry_path_is_not_replaced_with_another_artifact(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_boundary(tmp_path / "missing.geojson")


def test_seam_tolerance_reports_native_float_precision_sensitivity() -> None:
    bounds = np.array([[0.0, 0.5], [0.500004, 1.0], [0.99999, 1.5]])

    strict = seam_summary(bounds, 1e-12)
    coarse = seam_summary(bounds, 1.1e-5)

    assert strict["adjacent_gaps"] == 1
    assert strict["adjacent_overlaps"] == 1
    assert strict["axis_cells_adjacent_to_gaps"] == 2
    assert strict["axis_cells_adjacent_to_overlaps"] == 2
    assert coarse["adjacent_gaps"] == 0
    assert coarse["adjacent_overlaps"] == 0


def test_center_midpoint_bounds_are_separate_and_tile_exactly() -> None:
    grid = {
        "lat": np.array([-35.75, -35.25], dtype=np.float32).astype(np.float64),
        "lon": np.array([139.75, 140.25], dtype=np.float32).astype(np.float64),
        "lat_bounds": np.array([[-36.0, -35.5001], [-35.4999, -35.0]], dtype=np.float32),
        "lon_bounds": np.array([[139.5, 139.9999], [140.0001, 140.5]], dtype=np.float32),
    }

    candidates = imerg_bounds_candidates(grid)

    assert set(candidates) == {"native_float32_bounds", "center_midpoint_bounds"}
    native = candidates["native_float32_bounds"]
    derived = candidates["center_midpoint_bounds"]
    assert seam_summary(native["latitude"], 1e-12)["adjacent_gaps"] == 1
    assert seam_summary(derived["latitude"], 1e-12)["adjacent_gaps"] == 0
    assert seam_summary(native["longitude"], 1e-12)["adjacent_gaps"] == 1
    assert seam_summary(derived["longitude"], 1e-12)["adjacent_gaps"] == 0
    assert not np.shares_memory(native["latitude"], grid["lat_bounds"])


def test_midpoint_area_closure_improves_fixture_without_claiming_correctness() -> None:
    grid = {
        "lat": np.array([-35.75, -35.25]),
        "lon": np.array([139.75, 140.25]),
    }
    geometry = Polygon([(139.6, -35.9), (140.4, -35.9), (140.4, -35.1), (139.6, -35.1), (139.6, -35.9)])
    candidates = {
        "native": {
            "latitude": np.array([[-36.0, -35.5001], [-35.4999, -35.0]]),
            "longitude": np.array([[139.5, 139.9999], [140.0001, 140.5]]),
        },
        "derived": {
            "latitude": np.array([[-36.0, -35.5], [-35.5, -35.0]]),
            "longitude": np.array([[139.5, 140.0], [140.0, 140.5]]),
        },
    }
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3577", always_xy=True)

    native = _projected_area_diagnostic(grid, candidates["native"], geometry, "EPSG:3577", 0.02)
    derived = _projected_area_diagnostic(grid, candidates["derived"], geometry, "EPSG:3577", 0.02)
    repeat = _projected_area_diagnostic(grid, candidates["derived"], geometry, "EPSG:3577", 0.02)
    transformer.transform(140, -35)

    assert abs(derived["closure_delta_km2"]) < abs(native["closure_delta_km2"])
    assert derived["closure_delta_km2"] == pytest.approx(repeat["closure_delta_km2"], abs=1e-12)
    assert "not an official basin area" in derived["interpretation"]


def test_point_trial_preserves_distinct_cells_units_and_candidate_status() -> None:
    geometry = Polygon([(139, -36), (141, -36), (141, -34), (139, -34), (139, -36)])
    grids = {
        "imerg_final": {
            "lat": np.array([-35.9, -35.7, -35.5, -35.3, -35.1]),
            "lon": np.array([139.1, 139.3, 139.5, 139.7, 139.9, 140.1, 140.3, 140.5, 140.7, 140.9]),
            "lat_bounds": np.array([[-36.0, -35.8], [-35.8, -35.6], [-35.6, -35.4], [-35.4, -35.2], [-35.2, -35.0]]),
            "lon_bounds": np.array([[x - 0.1, x + 0.1] for x in [139.1, 139.3, 139.5, 139.7, 139.9, 140.1, 140.3, 140.5, 140.7, 140.9]]),
            "info": {"bounds_method": "synthetic fixture bounds", "nominal_cell_size_degrees_lat_lon": [0.2, 0.2]},
        },
        "merra2": {
            "lat": np.array([-35.75, -35.25]),
            "lon": np.array([139.375, 140.0, 140.625]),
            "lat_bounds": np.array([[-36.0, -35.5], [-35.5, -35.0]]),
            "lon_bounds": np.array([[139.0625, 139.6875], [139.6875, 140.3125], [140.3125, 140.9375]]),
            "info": {"bounds_method": "synthetic inferred bounds", "nominal_cell_size_degrees_lat_lon": [0.5, 0.625]},
        },
        "gldas": {
            "lat": np.array([-35.875, -35.625, -35.375, -35.125]),
            "lon": np.array([139.125, 139.375, 139.625, 139.875, 140.125, 140.375, 140.625, 140.875]),
            "lat_bounds": np.array([[x - 0.125, x + 0.125] for x in [-35.875, -35.625, -35.375, -35.125]]),
            "lon_bounds": np.array([[x - 0.125, x + 0.125] for x in [139.125, 139.375, 139.625, 139.875, 140.125, 140.375, 140.625, 140.875]]),
            "info": {"bounds_method": "synthetic inferred bounds", "nominal_cell_size_degrees_lat_lon": [0.25, 0.25]},
        },
    }
    hashes = {product: f"sha-{product}" for product in grids}

    trial = _point_support_trial(geometry, grids, hashes)

    assert trial["status"] == POINT_TRIAL_STATUS
    assert trial["candidate_site_inside_exploratory_polygon"]
    assert set(trial["products"]) == set(grids)
    assert len({tuple(row["grid_cell_index_zero_based"].values()) for row in trial["products"].values()}) == 3
    assert trial["products"]["imerg_final"]["unit"] == "mm/hr"
    assert trial["products"]["merra2"]["unit"] == "K"
    assert trial["products"]["gldas"]["unit"] == "kg m-2"
    assert all(row["reference_payload_sha256"] == hashes[product] for product, row in trial["products"].items())
    assert "do not imply equivalent" in trial["interpretation"]
