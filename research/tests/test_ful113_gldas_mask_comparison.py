from __future__ import annotations

import hashlib

import h5py
import numpy as np
import pytest

from research.comparar_mascara_gldas_ful113 import (
    _inland_window_counts,
    assert_aligned_grid,
    cross_classify,
    inspect_reference_mask,
)


def test_cross_classification_keeps_fill_nonfinite_and_valid_separate():
    values = np.array([[-9999.0, np.nan, 0.0, 7.0, -9999.0, 8.0]])
    mask = np.array([[0.0, 0.0, 1.0, 1.0, -9999.0, 2.0]])

    result = cross_classify(values, -9999.0, mask, -9999.0)

    assert result["total_cells"] == 6
    assert result["sample_states"] == {
        "fill": 2,
        "nonfinite": 1,
        "finite_nonfill": 3,
    }
    assert result["cross_counts"]["water_0"] == {
        "cells": 2,
        "fill": 1,
        "nonfinite": 1,
        "finite_nonfill": 0,
    }
    assert result["cross_counts"]["land_1"]["finite_nonfill"] == 2
    assert result["cross_counts"]["fill"]["fill"] == 1
    assert result["cross_counts"]["other_finite"]["finite_nonfill"] == 1
    assert result["qa_assessment"] == "unassessed"
    assert result["filters_applied"] == []


def test_cross_classification_fails_on_shape_mismatch():
    with pytest.raises(ValueError, match="Grillas incompatibles"):
        cross_classify(np.zeros((2, 3)), -9999.0, np.zeros((3, 2)), -9999.0)


def test_diagnostic_inland_window_reports_only_inclusive_center_cells():
    lat = np.array([-30.125, -29.875, -29.625, -26.125, -25.875])
    lon = np.array([136.875, 137.125, 137.375, 139.875, 140.125])
    values = np.full((5, 5), 2.0, dtype=np.float32)
    mask = np.ones((5, 5), dtype=np.float32)
    values[1, 1:4] = -9999.0
    mask[1, 1:4] = 0.0
    mask[2, 1:4] = 0.0

    result = _inland_window_counts(
        values,
        -9999.0,
        mask,
        -9999.0,
        lon,
        lat,
        (137.0, -30.0, 140.0, -26.0),
    )

    assert result["total_cells"] == 9
    assert result["mask_states"]["water_0"] == 6
    assert result["cross_counts"]["water_0"]["fill"] == 3
    assert result["cross_counts"]["water_0"]["finite_nonfill"] == 3
    assert result["selection_basis"].startswith("grid-cell centers")


def test_grid_alignment_requires_expected_dimension_order_and_equal_centers():
    axes = [["time"], ["lat"], ["lon"]]
    coordinates = np.array([-0.125, 0.125], dtype=np.float32)

    assert_aligned_grid(axes, axes, coordinates, coordinates.copy(), coordinates, coordinates.copy())

    with pytest.raises(ValueError, match="Orden de ejes incompatible"):
        assert_aligned_grid(axes, [["time"], ["lon"], ["lat"]], coordinates, coordinates, coordinates, coordinates)

    with pytest.raises(ValueError, match="coordenadas lat"):
        assert_aligned_grid(axes, axes, coordinates, coordinates + 0.25, coordinates, coordinates)

    with pytest.raises(ValueError, match="coordenadas lon"):
        assert_aligned_grid(axes, axes, coordinates, coordinates, coordinates, coordinates + 0.25)


def test_reference_mask_inventory_checks_source_structure_and_hash(tmp_path):
    path = tmp_path / "GLDASp5_landmask_025d.nc4"
    with h5py.File(path, "w") as target:
        time = target.create_dataset("time", data=np.array([0.0]))
        lat = target.create_dataset("lat", data=np.array([-0.125, 0.125]))
        lon = target.create_dataset("lon", data=np.array([-0.25, 0.0, 0.25]))
        time.make_scale("time")
        lat.make_scale("lat")
        lon.make_scale("lon")
        mask = target.create_dataset(
            "GLDAS_mask", data=np.array([[[0, 1, 1], [0, 1, 1]]], dtype=np.float32)
        )
        for axis, scale in enumerate((time, lat, lon)):
            mask.dims[axis].attach_scale(scale)
        mask.attrs["units"] = "0 = water; 1 = land"
        mask.attrs["_FillValue"] = np.float32(-9999)
        mask.attrs["long_name"] = "synthetic land/water mask"
        target.attrs["history"] = "synthetic fixture"

    record = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.file_digest(path.open("rb"), "sha256").hexdigest(),
        "shape": [1, 2, 3],
        "dtype": "float32",
        "dimension_scales_by_axis": [["time"], ["lat"], ["lon"]],
        "class_encoding": "0 = water; 1 = land",
        "source_page": "fixture://page",
        "source_file": "fixture://mask",
        "interpretation_limit": "synthetic",
    }

    report = inspect_reference_mask(path, record)

    assert report["sha256"] == record["sha256"]
    assert report["stored_values_and_counts"] == {"0.0": 2, "1.0": 4}
    assert report["dimension_scales_by_axis"] == [["time"], ["lat"], ["lon"]]
    assert report["observed_history"] == "synthetic fixture"


def test_reference_mask_inventory_rejects_wrong_hash(tmp_path):
    path = tmp_path / "GLDASp5_landmask_025d.nc4"
    path.write_bytes(b"not a valid mask")
    record = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": "0" * 64,
    }

    with pytest.raises(ValueError, match="SHA-256 de máscara incompatible"):
        inspect_reference_mask(path, record)
