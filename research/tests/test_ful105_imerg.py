from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from research.ful105_imerg import (
    CenterMaskCache,
    discover_imerg_2005,
    select_imerg_2005,
    valid_data_mask,
)


def _asset(root: Path, year="2005", month="01", *, suffix=None, version="07B", manifest_month=None, payload=b"grid"):
    suffix = suffix or month
    name = f"3B-MO.MS.MRG.3IMERG.{year}{month}01-S000000-E235959.{suffix}.V{version}.HDF5"
    path = root / name
    path.write_bytes(payload)
    metadata = {
        "product": {"key": "imerg_final", "short_name": "GPM_3IMERGM", "version": "07", "variable": "precipitation"},
        "period": {"month": manifest_month or f"{year}-{month}"},
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    Path(f"{path}.manifest.json").write_text(json.dumps(metadata), encoding="utf-8")
    return path


def test_discovery_returns_complete_2005_assets_in_order(tmp_path):
    paths = [_asset(tmp_path, month=f"{month:02d}") for month in range(12, 0, -1)]
    (tmp_path / "notes.txt").write_text("unrelated", encoding="utf-8")
    assets = discover_imerg_2005(tmp_path)
    assert [asset.period for asset in assets] == [f"2005-{month:02d}" for month in range(1, 13)]
    assert assets[0].sha256 == hashlib.sha256(paths[-1].read_bytes()).hexdigest()


def test_selection_rejects_missing_months_with_recovery_hint(tmp_path):
    with pytest.raises(FileNotFoundError, match="2005-11.*2005-12.*README.md"):
        select_imerg_2005([_asset(tmp_path, month=f"{month:02d}") for month in range(1, 11)])


def test_selection_rejects_duplicate_periods(tmp_path):
    first = _asset(tmp_path, month="01")
    # Duplicate detection happens before re-validating the same path.
    with pytest.raises(ValueError, match="duplicados para 2005-01"):
        select_imerg_2005([first, first], require_complete=False)


@pytest.mark.parametrize("kwargs, message", [
    ({"year": "2004"}, "fuera del año 2005"),
    ({"version": "06B"}, "distinta de V07B"),
    ({"month": "01", "suffix": "02"}, "sufijo no coinciden"),
    ({"month": "01", "manifest_month": "2005-02"}, "manifiesto"),
])
def test_selection_rejects_wrong_period_version_or_filename(kwargs, message, tmp_path):
    with pytest.raises(ValueError, match=message):
        select_imerg_2005([_asset(tmp_path, **kwargs)], require_complete=False)


def test_selection_rejects_file_sha_mismatch(tmp_path):
    path = _asset(tmp_path)
    path.write_bytes(b"changed-after-manifest")
    with pytest.raises(ValueError, match="Tamaño/SHA-256 no coincide"):
        select_imerg_2005([path], require_complete=False)


def test_selection_rejects_manifest_identity_mismatch(tmp_path):
    path = _asset(tmp_path)
    metadata = json.loads(Path(f"{path}.manifest.json").read_text(encoding="utf-8"))
    metadata["product"]["variable"] = "other"
    Path(f"{path}.manifest.json").write_text(json.dumps(metadata), encoding="utf-8")
    with pytest.raises(ValueError, match="Identidad/version/variable"):
        select_imerg_2005([path], require_complete=False)


def test_selection_reports_missing_manifest(tmp_path):
    path = _asset(tmp_path)
    Path(f"{path}.manifest.json").unlink()
    with pytest.raises(FileNotFoundError, match="Falta manifiesto de 2005-01"):
        select_imerg_2005([path], require_complete=False)


def _polygon(path, *, hole=False, shift=0):
    exterior = [[0 + shift, 0], [4 + shift, 0], [4 + shift, 4], [0 + shift, 4], [0 + shift, 0]]
    rings = [exterior]
    if hole:
        rings.append([[1 + shift, 1], [3 + shift, 1], [3 + shift, 3], [1 + shift, 3], [1 + shift, 1]])
    path.write_text(json.dumps({"type": "Polygon", "coordinates": rings}), encoding="utf-8")


def test_mask_cache_reuses_and_invalidates_for_coordinates_and_geometry(tmp_path):
    polygon = tmp_path / "polygon.geojson"
    _polygon(polygon)
    from backend.app.data_sources import earthdata_spatial

    original_predicate = earthdata_spatial._inside
    cache = CenterMaskCache()
    lat = np.array([0, 1, 2, 4, 5], dtype=float)
    lon = np.array([0, 1, 2, 4, 5], dtype=float)
    first = cache.get(lat, lon, polygon)
    again = cache.get(lat.copy(), lon.copy(), polygon)
    changed_grid = cache.get(lat + 10, lon, polygon)
    _polygon(polygon, shift=10)
    changed_geometry = cache.get(lat + 10, lon, polygon)
    assert first.values.sum() == 16
    assert first.cache_hit is False and again.cache_hit is True
    assert changed_grid.cache_hit is False and changed_geometry.cache_hit is False
    assert cache.build_count == 3
    assert earthdata_spatial._inside is original_predicate


def test_mask_uses_ful106_boundary_and_hole_semantics(tmp_path):
    polygon = tmp_path / "polygon-with-hole.geojson"
    _polygon(polygon, hole=True)
    result = CenterMaskCache().get(np.array([0, 1, 2, 3, 4]), np.array([0, 1, 2, 3, 4]), polygon)
    assert result.values.sum() == 24
    assert result.values[0, 0]  # exterior boundary included
    assert not result.values[2, 2]  # hole interior excluded
    assert result.values[1, 2]  # hole boundary included, same as FUL-106


def test_zero_is_valid_and_fill_is_missing():
    values = np.array([0.0, 0.5, -9999.900390625, np.nan, np.inf])
    assert valid_data_mask(values, [-9999.9]).tolist() == [True, True, False, False, False]
