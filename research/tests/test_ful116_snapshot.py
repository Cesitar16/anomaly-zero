from __future__ import annotations

import calendar
import hashlib
import json
import zipfile
from pathlib import Path

import h5py
import numpy as np
import pytest

from research import build_ful116_snapshot as snapshot
from research.audit_imerg_bounds_precision import interval_diagnostics


def _write_granules(root: Path, monkeypatch) -> tuple[Path, Path]:
    monkeypatch.setattr(snapshot, "DATASET_SHAPE", (1, 6, 4))
    root.mkdir(parents=True, exist_ok=True)
    input_dir = root / "input"
    input_dir.mkdir()
    point_path = root / "point.json"
    point_path.write_text(
        json.dumps(
            {
                "selection_id": "fixture-panel-center",
                "selection_source": "synthetic fixture derived from a panel-like coordinate list",
                "selection_method": "test only",
                "latitude": -37.65,
                "longitude": 145.75,
                "grid_registration": "center",
            }
        ),
        encoding="utf-8",
    )
    lat = np.array([-37.75, -37.65, -37.55, -37.45], dtype=np.float32)
    lon = np.array([145.55, 145.65, 145.75, 145.85, 145.95, 146.05], dtype=np.float32)
    for month in range(1, 13):
        filename = (
            f"3B-MO.MS.MRG.3IMERG.2005{month:02d}01-S000000-E235959."
            f"{month:02d}.V07B.HDF5"
        )
        path = input_dir / filename
        data = np.ones((1, 6, 4), dtype=np.float32) * month
        if month == 1:
            data[0, 2, 1] = 0.0
            data[0, 3, 2] = np.float32(-9998.9)
        elif month == 2:
            data[0, 2, 1] = np.float32(-9999.9)
        elif month == 3:
            data[0, 2, 1] = np.nan
        with h5py.File(path, "w") as target:
            grid = target.create_group("Grid")
            grid.attrs["FileHeader"] = (
                f"FileName={filename};\nDOIshortName=3IMERGM;\nAlgorithmID=3IMERGM;\n"
                f"StartGranuleDateTime=2005-{month:02d}-01T00:00:00.000Z;\n"
                f"StopGranuleDateTime=2005-{month:02d}-{calendar.monthrange(2005, month)[1]:02d}T23:59:59.999Z;\n"
                "ProductVersion=V07B;\n"
            )
            field = grid.create_dataset("precipitation", data=data, dtype=np.float32)
            field.attrs["DimensionNames"] = "time,lon,lat"
            field.attrs["units"] = "mm/hr"
            field.attrs["_FillValue"] = np.float32(-9999.9)
            field.attrs["CodeMissingValue"] = "-9998.9"
            time = grid.create_dataset("time", data=np.array([month], dtype=np.int32))
            time.attrs["units"] = "seconds since 1980-01-06 00:00:00 UTC"
            time.attrs["calendar"] = "julian"
            grid.create_dataset("time_bnds", data=np.array([[month - 1, month + 1]], dtype=np.int32))
            grid.create_dataset("lon", data=lon)
            grid.create_dataset("lat", data=lat)
            grid.create_dataset("lon_bnds", data=np.column_stack((lon - 0.05, lon + 0.05)))
            grid.create_dataset("lat_bnds", data=np.column_stack((lat - 0.05, lat + 0.05)))
            for qa_name in ("precipitationQualityIndex", "randomError", "gaugeRelativeWeighting"):
                grid.create_dataset(qa_name, data=np.zeros_like(data))
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        manifest = {
            "manifest_version": 1,
            "synthetic_fixture": True,
            "fixture_id": "ful116-synthetic-test-granules",
            "product": {
                "key": "imerg_final",
                "short_name": "GPM_3IMERGM",
                "version": "07",
                "variable": "precipitation",
                "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
            },
            "collection_id": "C2723754851-GES_DISC",
            "filename": filename,
            "source": {
                "provider": "synthetic test fixture",
                "granule_metadata": f"fixture://ful116/{month}",
            },
            "period": {
                "month": f"2005-{month:02d}",
                "start": f"2005-{month:02d}-01T00:00:00.000Z",
                "end": f"2005-{month:02d}-{calendar.monthrange(2005, month)[1]:02d}T23:59:59.999Z",
            },
            "downloaded_at_utc": "2026-01-01T00:00:00Z",
            "bytes": path.stat().st_size,
            "sha256": digest,
        }
        manifest_path = Path(f"{path}.manifest.json")
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return input_dir, point_path


def test_snapshot_classifies_zero_fill_and_nonfinite_and_is_deterministic(tmp_path, monkeypatch):
    input_dir, point_path = _write_granules(tmp_path, monkeypatch)
    output_dir = tmp_path / "processed"

    first = snapshot.build_snapshot(input_dir, point_path, output_dir)
    first_bytes = (output_dir / "imerg_2005_point_snapshot.json").read_bytes()
    preview_bytes = (output_dir / "imerg_2005-01_bbox_preview.npz").read_bytes()
    second = snapshot.build_snapshot(input_dir, point_path, output_dir)

    assert second["dataset_id"] == first["dataset_id"]
    assert second["snapshot_sha256"] == first["snapshot_sha256"]
    assert (output_dir / "imerg_2005_point_snapshot.json").read_bytes() == first_bytes
    assert (output_dir / "imerg_2005-01_bbox_preview.npz").read_bytes() == preview_bytes
    assert first["synthetic"] is True
    assert first["product"]["unit"] == "mm/hr"
    assert first["coverage"]["present_periods"] == 12
    assert first["coverage"]["valid_periods"] == 10
    assert first["coverage"]["missing_periods"] == ["2005-02", "2005-03"]
    assert first["series"][0]["value"] == 0.0
    assert first["series"][0]["quality"]["state"] == "unassessed"
    assert first["series"][1]["value"] is None
    assert first["series"][1]["quality"]["missing_reason"] == "provider_fill_value"
    assert first["series"][2]["value"] is None
    assert first["series"][2]["quality"]["missing_reason"] == "non_finite_source_value"
    assert first["spatial_aggregation"]["support_type"] == "point_sample"
    assert first["quality"]["provider_flags_applied"] is False
    assert first["quality"]["verification_state"] == "basic_checks_only"
    assert "[longitude_index, latitude_index]" in first["provenance"]["preview"]["array_orientation"]
    assert zipfile.is_zipfile(output_dir / "imerg_2005-01_bbox_preview.npz")
    with np.load(output_dir / "imerg_2005-01_bbox_preview.npz") as preview:
        assert preview["values_raw"].shape == (6, 4)
        assert preview["values_raw"][2, 1] == 0.0
        assert preview["finite_nonfill_mask"][2, 1] == 1
        assert preview["fill_mask"].shape == (6, 4)
        assert preview["fill_mask"][3, 2] == 1
        assert preview["finite_nonfill_mask"][3, 2] == 0


def test_discovery_requires_all_verified_months_and_rejects_bad_hash(tmp_path, monkeypatch):
    input_dir, _ = _write_granules(tmp_path, monkeypatch)
    november = next(input_dir.glob("*200511*.HDF5"))
    Path(f"{november}.manifest.json").unlink()
    with pytest.raises(FileNotFoundError, match="Falta manifest"):
        snapshot.discover_granules(input_dir)

    input_dir, _ = _write_granules(tmp_path / "other", monkeypatch)
    january = next(input_dir.glob("*200501*.HDF5"))
    manifest_path = Path(f"{january}.manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="SHA-256/tamaño"):
        snapshot.discover_granules(input_dir)


def test_discovery_reports_absent_periods_instead_of_filling_them(tmp_path, monkeypatch):
    input_dir, _ = _write_granules(tmp_path, monkeypatch)
    december = next(input_dir.glob("*200512*.HDF5"))
    december.unlink()
    Path(f"{december}.manifest.json").unlink()
    with pytest.raises(FileNotFoundError, match="2005-12"):
        snapshot.discover_granules(input_dir)
    found = snapshot.discover_granules(input_dir, require_complete=False)
    assert len(found) == 11


def test_provenance_classifier_requires_a_homogeneous_origin():
    assert snapshot._resolve_synthetic_flag([False] * 12) is False
    assert snapshot._resolve_synthetic_flag([True] * 12) is True
    with pytest.raises(ValueError, match="mezclar granules"):
        snapshot._resolve_synthetic_flag([False] * 11 + [True])
    with pytest.raises(ValueError, match="clasificar la procedencia"):
        snapshot._resolve_synthetic_flag([True] * 11 + [None])


def test_complete_cmr_manifest_is_classified_as_real():
    filename = "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5"
    path = Path(filename)
    manifest = {
        "manifest_version": 1,
        "product": {"doi": "10.5067/GPM/IMERG/3B-MONTH/07"},
        "period": {
            "start": "2005-01-01T00:00:00.000Z",
            "end": "2005-01-31T23:59:59.999Z",
        },
        "granule_id": "G123456789-GES_DISC",
        "producer_granule_id": f"GPM_3IMERGM.07:{filename}",
        "downloaded_at_utc": "2026-11-14T23:23:30.882347+00:00",
        "source": {
            "provider": "NASA GES DISC via Earthdata CMR",
            "collection_metadata": "https://cmr.earthdata.nasa.gov/search/concepts/C2723754851-GES_DISC.umm_json",
            "granule_metadata": "https://cmr.earthdata.nasa.gov/search/concepts/G123456789-GES_DISC.umm_json",
        },
    }
    assert snapshot._manifest_is_synthetic(manifest, path, "01") is False


def test_discovery_rejects_insufficient_or_contradictory_provenance(tmp_path, monkeypatch):
    input_dir, _ = _write_granules(tmp_path, monkeypatch)
    january = next(input_dir.glob("*200501*.HDF5"))
    manifest_path = Path(f"{january}.manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["synthetic_fixture"] = "true"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(TypeError, match="Marca synthetic_fixture inválida"):
        snapshot.discover_granules(input_dir)

    manifest["synthetic_fixture"] = False
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Procedencia NASA/CMR insuficiente"):
        snapshot.discover_granules(input_dir)
    manifest["synthetic_fixture"] = True
    manifest["source"]["provider"] = "NASA GES DISC via Earthdata CMR"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="Procedencia sintética incompleta o contradictoria"):
        snapshot.discover_granules(input_dir)


def test_invalid_preview_request_does_not_leave_partial_outputs(tmp_path, monkeypatch):
    input_dir, point_path = _write_granules(tmp_path, monkeypatch)
    output_dir = tmp_path / "processed"
    with pytest.raises(ValueError, match="BBox"):
        snapshot.build_snapshot(input_dir, point_path, output_dir, bbox=(153, -24, 138, -38))
    assert not output_dir.exists()


def test_bounds_diagnostic_reports_gap_and_overlap_without_repair():
    centers = np.array([0.5, 1.5, 2.5], dtype=np.float32)
    bounds = np.array([[0.0, 1.0], [0.999, 2.0], [2.001, 3.0]], dtype=np.float32)

    result = interval_diagnostics(centers, bounds)

    assert result["adjacent_overlaps"] == 1
    assert result["adjacent_gaps"] == 1
    assert result["center_outside_own_bounds"] == 0
    assert result["cells_differing_from_contiguous_midpoint_edges"] == 2
    np.testing.assert_array_equal(bounds[0], [0.0, 1.0])

