import json

import numpy as np
import pytest
import shapely

from research.auditar_espacial_ful104 import (
    REQUIRED_SAMPLE_NAMES,
    classify_values,
    geometry_inventory,
    load_basin,
    partial_cell_mask,
    require_samples,
    spatial_selection_masks,
    valid_data_mask,
    validate_results,
)


def test_valid_data_mask_matches_float32_fill_representation():
    fill = np.float32(-9999.9)
    values = np.array([1.25, fill, np.nan], dtype=np.float32)

    np.testing.assert_array_equal(valid_data_mask(values, float(fill)), [True, False, False])


def test_valid_data_mask_handles_integer_fill_values():
    values = np.array([0, -9999, 4], dtype=np.int16)

    np.testing.assert_array_equal(valid_data_mask(values, -9999), [True, False, True])


def test_spatial_selection_distinguishes_centers_from_intersections():
    basin = shapely.box(0, 0, 1, 1)
    cells = np.array(
        [
            shapely.box(0.2, 0.2, 0.8, 0.8),
            shapely.box(0.8, 0.2, 1.4, 0.8),
            shapely.box(1.1, 0.2, 1.5, 0.8),
        ],
        dtype=object,
    )

    centers, intersects = spatial_selection_masks(
        basin, cells, np.array([0.5, 1.1, 1.3]), np.array([0.5, 0.5, 0.5])
    )

    np.testing.assert_array_equal(centers, [True, False, False])
    np.testing.assert_array_equal(intersects, [True, True, False])


def test_require_samples_fails_when_a_required_sample_is_missing(tmp_path):
    for name in REQUIRED_SAMPLE_NAMES[:-1]:
        (tmp_path / name).touch()

    with pytest.raises(FileNotFoundError, match=REQUIRED_SAMPLE_NAMES[-1]):
        require_samples(tmp_path)


def test_validate_results_fails_when_a_sample_was_not_processed():
    results = [{"file": REQUIRED_SAMPLE_NAMES[0], "error": "unreadable"}]

    with pytest.raises(RuntimeError, match="Auditoría incompleta"):
        validate_results(results)


def test_load_basin_rejects_line_string_fixture(tmp_path):
    geometry = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {
            "type": "LineString", "coordinates": [[0, 0], [1, 1]]
        }}],
    }
    path = tmp_path / "line.geojson"
    path.write_text(json.dumps(geometry), encoding="utf-8")

    with pytest.raises(ValueError, match="debe ser poligonal"):
        load_basin(path)


def test_load_basin_accepts_valid_polygon_fixture(tmp_path):
    geometry = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {
            "type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
        }}],
    }
    path = tmp_path / "basin.geojson"
    path.write_text(json.dumps(geometry), encoding="utf-8")

    assert load_basin(path).geom_type == "Polygon"


def test_classify_values_keeps_zero_fill_and_missing_separate():
    fill = np.float32(-9999.9)
    values = np.array([0.0, fill, np.nan, 2.0], dtype=np.float32)

    assert classify_values(values, float(fill)) == {
        "total": 4,
        "non_finite": 1,
        "fill": 1,
        "finite_non_fill": 2,
        "zero_valid": 1,
    }


def test_partial_cell_mask_uses_area_fraction_and_excludes_full_cells():
    np.testing.assert_array_equal(
        partial_cell_mask([0.5, 1.0], [1.0, 1.0]), [True, False]
    )


def test_boundary_touch_is_intersection_but_has_no_positive_area():
    basin = shapely.box(0, 0, 1, 1)
    touching = shapely.box(1, 0, 2, 1)
    overlapping = shapely.box(0.5, 0, 1.5, 1)

    assert shapely.intersects(basin, touching)
    assert shapely.area(shapely.intersection(basin, touching)) == 0
    assert shapely.area(shapely.intersection(basin, overlapping)) == pytest.approx(0.5)

    centers, intersects = spatial_selection_masks(
        basin, np.array([overlapping], dtype=object), np.array([1.0]), np.array([0.5])
    )
    np.testing.assert_array_equal(centers, [True])  # covers includes boundary
    np.testing.assert_array_equal(intersects, [True])


def test_fractional_intersection_areas_close_on_synthetic_partition():
    basin = shapely.box(0, 0, 1, 1)
    cells = np.array([shapely.box(0, 0, 0.5, 1), shapely.box(0.5, 0, 1, 1)], dtype=object)
    areas = shapely.area(shapely.intersection(cells, basin))

    assert areas.sum() == pytest.approx(shapely.area(basin))


def test_load_basin_rejects_invalid_polygon(tmp_path):
    geometry = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "properties": {}, "geometry": {
            "type": "Polygon", "coordinates": [[[0, 0], [1, 1], [1, 0], [0, 1], [0, 0]]]
        }}],
    }
    path = tmp_path / "invalid.geojson"
    path.write_text(json.dumps(geometry), encoding="utf-8")

    with pytest.raises(ValueError, match="topológicamente válida"):
        load_basin(path)


def test_geometry_inventory_counts_polygon_rings_and_holes():
    polygon = shapely.Polygon(
        [(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)],
        holes=[[(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)]],
    )

    assert geometry_inventory(polygon) == {
        "geometry_type": "Polygon",
        "polygon_count": 1,
        "ring_count": 2,
        "hole_count": 1,
        "vertex_count_including_closure": 10,
        "is_valid": True,
    }
