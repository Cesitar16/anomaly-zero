"""Deterministic synthetic-only tests for DS-07 spatial diagnostics."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from netCDF4 import Dataset
from pyproj import Transformer
from shapely.geometry import Polygon

from research.ful124_spatial_audit import (
    STRATEGIES,
    SpatialAuditError,
    _area_diagnostics,
    _axis_bounds,
    _candidate_centers,
    _read_candidate_values,
    load_boundary,
)


def _synthetic_geojson(path: Path, coordinates: list[list[float]]) -> Path:
    polygon = {"type": "Polygon", "coordinates": [coordinates]}
    path.write_text(json.dumps({"type": "FeatureCollection", "features": [{"type": "Feature", "geometry": polygon, "properties": {"fixture": "synthetic"}}]}), encoding="utf-8")
    return path


def test_valid_synthetic_geometry_is_reported_without_approval(tmp_path: Path) -> None:
    path = _synthetic_geojson(tmp_path / "synthetic.geojson", [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]])

    geom, metadata = load_boundary(path, expected_sha256=None)

    assert geom.is_valid
    assert metadata["artifact_sha256"]
    assert metadata["exported_artifact_crs"] == "EPSG:4326"
    assert "native datum" in metadata["crs_interpretation"]


def test_invalid_polygon_is_rejected(tmp_path: Path) -> None:
    path = _synthetic_geojson(tmp_path / "invalid.geojson", [[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]])

    with pytest.raises(SpatialAuditError, match="invalid"):
        load_boundary(path, expected_sha256=None)


def test_antimeridian_polygon_is_explicitly_unsupported(tmp_path: Path) -> None:
    path = _synthetic_geojson(tmp_path / "wrapped.geojson", [[179, 0], [-179, 0], [-179, 1], [179, 1], [179, 0]])

    with pytest.raises(SpatialAuditError, match="antimeridian"):
        load_boundary(path, expected_sha256=None)


def test_missing_and_nonmonotonic_coordinates_are_rejected() -> None:
    with pytest.raises(SpatialAuditError, match="finite 1D"):
        _axis_bounds(np.array([0.0, np.nan]), None)
    with pytest.raises(SpatialAuditError, match="strictly monotonic"):
        _axis_bounds(np.array([0.0, 1.0, 0.5]), None)


def test_explicit_and_inferred_bounds_are_deterministic() -> None:
    centers = np.array([0.25, 0.75])
    inferred = _axis_bounds(centers, None)
    explicit = _axis_bounds(centers, np.array([[0, 0.5], [0.5, 1.0]]))

    np.testing.assert_allclose(inferred, explicit)
    np.testing.assert_allclose(_axis_bounds(centers[::-1], None), explicit[::-1])


def test_center_selection_includes_boundary_and_excludes_outside_points() -> None:
    polygon = Polygon(
        [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)],
        holes=[[(0.9, 0.9), (1.1, 0.9), (1.1, 1.1), (0.9, 1.1), (0.9, 0.9)]],
    )
    grid = {"lat": np.array([0.0, 1.0, 2.0]), "lon": np.array([0.0, 1.0, 2.0])}

    xx, yy, mask, _ = _candidate_centers(grid, polygon)

    assert mask.shape == xx.shape == yy.shape == (3, 3)
    assert not mask[1, 1]  # hole center is outside
    assert mask[0, 0]  # outer boundary is included, analogous to covers
    assert int(mask.sum()) == 8


def test_overlap_marks_partial_boundary_cells_and_does_not_claim_approved_area() -> None:
    polygon = Polygon([(0.2, 0.2), (0.8, 0.2), (0.8, 0.8), (0.2, 0.8), (0.2, 0.2)])
    grid = {
        "lat": np.array([0.25, 0.75]),
        "lon": np.array([0.25, 0.75]),
        "lat_bounds": np.array([[0.0, 0.5], [0.5, 1.0]]),
        "lon_bounds": np.array([[0.0, 0.5], [0.5, 1.0]]),
    }
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3577", always_xy=True)

    result = _area_diagnostics(grid, polygon, transformer)

    assert result["positive_area_intersection_cells"] == 4
    assert result["partially_covered_cells"] == 4
    assert result["sum_projected_intersection_area_km2"] > 0
    assert "not an approved" in result["interpretation"]


def test_candidate_missing_fill_zero_and_negative_counts_use_synthetic_payload(tmp_path: Path) -> None:
    path = tmp_path / "synthetic_only.nc"
    with Dataset(path, "w") as dataset:
        dataset.createDimension("time", 1)
        dataset.createDimension("lat", 2)
        dataset.createDimension("lon", 2)
        variable = dataset.createVariable("T2M", "f4", ("time", "lat", "lon"), fill_value=-9999.0)
        variable.set_auto_maskandscale(False)
        variable[:] = np.array([[[0.0, -1.0], [np.nan, -9999.0]]], dtype=np.float32)

    record = {"product_key": "merra2", "path": str(path)}
    result = _read_candidate_values(record, {}, (slice(0, 2), slice(0, 2)), np.ones((2, 2), dtype=bool))

    assert result == {
        "center_candidate_count": 4,
        "fill_count": 1,
        "nonfinite_nonfill_count": 1,
        "finite_nonfill_count": 2,
        "zero_count_within_finite_nonfill": 1,
        "negative_finite_nonfill_count": 1,
    }


def test_all_strategies_remain_candidates_or_proposals() -> None:
    assert {strategy["id"] for strategy in STRATEGIES} == {
        "point_nearest_center", "cell_polygon_intersection", "regrid_or_area_weight"
    }
    assert all(strategy["state"] in {"candidate", "proposal_only"} for strategy in STRATEGIES)
    assert "approved" not in {strategy["state"] for strategy in STRATEGIES}
