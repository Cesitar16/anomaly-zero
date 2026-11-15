"""Small center-in-polygon QA extracts without changing native grids or values."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import xarray as xr

from backend.app.data_sources import earthdata_probe as probe
from backend.app.data_sources.earthdata_samples import (
    PRODUCTS,
    _hdf5_dimensions,
    _is_imerg_missing,
    inspect_product,
)


def _geometries(obj: dict[str, Any]) -> Iterator[tuple[list, list[list]]]:
    kind = obj.get("type")
    coordinates = obj.get("coordinates")
    if kind == "FeatureCollection":
        for feature in obj.get("features", []):
            yield from _geometries(feature.get("geometry") or {})
    elif kind == "Feature":
        yield from _geometries(obj.get("geometry") or {})
    elif kind == "Polygon":
        if coordinates:
            yield coordinates[0], coordinates[1:]
    elif kind == "MultiPolygon":
        for polygon in coordinates or []:
            if polygon:
                yield polygon[0], polygon[1:]


def _on_segment(x: float, y: float, a: list, b: list) -> bool:
    cross = (x - a[0]) * (b[1] - a[1]) - (y - a[1]) * (b[0] - a[0])
    scale = max(1.0, abs(x), abs(y), abs(a[0]), abs(a[1]), abs(b[0]), abs(b[1]))
    if abs(cross) > 1e-10 * scale:
        return False
    return (
        min(a[0], b[0]) - 1e-10 <= x <= max(a[0], b[0]) + 1e-10
        and min(a[1], b[1]) - 1e-10 <= y <= max(a[1], b[1]) + 1e-10
    )


def _ring_contains(
    x: float, y: float, ring: list, *, include_boundary: bool = True
) -> bool:
    inside = False
    for a, b in pairwise(ring):
        if _on_segment(x, y, a, b):
            return include_boundary
        if (a[1] > y) != (b[1] > y):
            crossing_x = (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]
            if x < crossing_x:
                inside = not inside
    return inside


def _inside(lon: float, lat: float, polygons: list[tuple[list, list[list]]]) -> bool:
    for exterior, holes in polygons:
        if _ring_contains(lon, lat, exterior) and not any(
            _ring_contains(lon, lat, ring, include_boundary=False)
            for ring in holes
        ):
            return True
    return False


def _centers(
    path: Path,
    product_key: str,
    latitudes: np.ndarray,
    longitudes: np.ndarray,
    values: np.ndarray,
    manifest_path: Path,
    polygon_path: Path,
    max_rows: int,
) -> dict[str, Any]:
    geo = json.loads(polygon_path.read_text(encoding="utf-8"))
    crs_name = (geo.get("crs") or {}).get("properties", {}).get("name")
    if crs_name is not None and crs_name.upper() not in {
        "EPSG:4326",
        "CRS84",
        "OGC:CRS84",
    }:
        raise probe.ProbeError(
            "polygon CRS is not compatible with geographic latitude/longitude"
        )
    polygons = list(_geometries(geo))
    if not polygons:
        raise probe.ProbeError("polygon file contains no Polygon geometry")
    all_points = [point for exterior, _ in polygons for point in exterior]
    west, east = min(p[0] for p in all_points), max(p[0] for p in all_points)
    south, north = min(p[1] for p in all_points), max(p[1] for p in all_points)
    lat_indexes = np.flatnonzero((latitudes >= south) & (latitudes <= north))
    lon_indexes = np.flatnonzero((longitudes >= west) & (longitudes <= east))
    if values.shape != (latitudes.size, longitudes.size):
        raise probe.ProbeError(
            "variable axes cannot be aligned to latitude/longitude coordinates"
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("bytes") != path.stat().st_size or manifest.get(
        "sha256"
    ) != probe._sha256(path):
        raise probe.ProbeError(
            "sample file does not match its manifest checksum or size"
        )
    product = PRODUCTS[product_key]
    inspection = inspect_product(path, product_key)
    fill = inspection["variable"].get("fill_value")
    missing = inspection["variable"].get("missing_value")
    sentinels = [v for v in (fill, missing) if v is not None]
    rows: list[dict[str, Any]] = []
    inside_count = valid_count = 0
    for iy in lat_indexes:
        lat = float(latitudes[iy])
        for ix in lon_indexes:
            lon = float(longitudes[ix])
            if not _inside(lon, lat, polygons):
                continue
            inside_count += 1
            value = values[iy, ix]
            is_missing = any(
                _is_imerg_missing(value, sentinel) for sentinel in sentinels
            ) or not np.isfinite(value)
            if is_missing:
                continue
            valid_count += 1
            if len(rows) < max_rows:
                rows.append(
                    {
                        "period": manifest.get("period", {}).get("month"),
                        "product": product.short_name,
                        "version": product.version,
                        "variable": product.variable,
                        "latitude": lat,
                        "longitude": lon,
                        "value": float(value),
                        "unit": inspection["variable"].get("units"),
                        "quality_candidates": ";".join(
                            inspection.get("quality_variable_candidates", [])
                        ),
                        "quality_filter_applied": False,
                        "original_file": str(path),
                        "manifest": str(manifest_path),
                    }
                )
    missing_count = inside_count - valid_count
    return {
        "selection": "cell center covered by polygon; outer and hole boundaries included",
        "surface_area_claimed": False,
        "denominator_center_cells": inside_count,
        "valid_center_cells": valid_count,
        "missing_center_cells": missing_count,
        "valid_percent": (100.0 * valid_count / inside_count) if inside_count else None,
        "grid_resolution": "native; no resampling",
        "transformations_applied": [],
        "rows": rows,
    }


def spatial_qa(
    path: Path | str,
    manifest_path: Path | str,
    polygon_path: Path | str,
    product_key: str,
    max_rows: int = 20,
) -> dict[str, Any]:
    path, manifest_path, polygon_path = (
        Path(path),
        Path(manifest_path),
        Path(polygon_path),
    )
    if max_rows < 1:
        raise probe.ProbeError("max-rows must be positive")
    if product_key not in PRODUCTS:
        raise probe.ProbeError("unknown product")
    report = inspect_product(path, product_key)
    if product_key == "imerg_final":
        with h5py.File(path, "r") as h5:
            var = h5["Grid/precipitation"]
            labels = _hdf5_dimensions(var)
            if labels.count("lat") != 1 or labels.count("lon") != 1:
                raise probe.ProbeError(
                    "HDF5 variable axes lack unambiguous lat/lon dimension names"
                )
            latitudes = np.asarray(h5["Grid/lat"][...]).reshape(-1)
            longitudes = np.asarray(h5["Grid/lon"][...]).reshape(-1)
            if var.shape[labels.index("lat")] != latitudes.size or var.shape[
                labels.index("lon")
            ] != longitudes.size:
                raise probe.ProbeError(
                    "HDF5 dimension names do not match coordinate sizes"
                )
            lat_units = str(h5["Grid/lat"].attrs.get("units", ""))
            lon_units = str(h5["Grid/lon"].attrs.get("units", ""))
            if "degree" not in lat_units.lower() or "degree" not in lon_units.lower():
                raise probe.ProbeError(
                    "HDF5 latitude/longitude units are not geographic degrees"
                )
            time_axes = [i for i, label in enumerate(labels) if label == "time"]
            if len(time_axes) > 1 or any(
                label not in {"lat", "lon", "time"} for label in labels
            ):
                raise probe.ProbeError("HDF5 variable dimensions are unsupported")
            array = np.asarray(var[...])
            for axis in reversed(time_axes):
                array = np.take(array, 0, axis=axis)
                labels.pop(axis)
            if labels == ["lon", "lat"]:
                array = array.T
            elif labels != ["lat", "lon"]:
                raise probe.ProbeError("HDF5 spatial axis order is unsupported")
    else:
        with xr.open_dataset(
            path,
            engine="netcdf4",
            decode_cf=False,
            mask_and_scale=False,
            decode_times=False,
        ) as ds:
            variable = ds[PRODUCTS[product_key].variable]
            lat_name = next(
                (name for name in ("lat", "latitude") if name in ds.coords), None
            )
            lon_name = next(
                (name for name in ("lon", "longitude") if name in ds.coords), None
            )
            if lat_name is None or lon_name is None:
                raise probe.ProbeError(
                    "NetCDF latitude/longitude coordinates are absent"
                )
            lat_dim = ds[lat_name].dims[0]
            lon_dim = ds[lon_name].dims[0]
            if lat_dim not in variable.dims or lon_dim not in variable.dims:
                raise probe.ProbeError(
                    "NetCDF variable axes cannot be matched to coordinates"
                )
            indexers = {
                dim: 0 for dim in variable.dims if dim not in {lat_dim, lon_dim}
            }
            array = np.asarray(
                variable.isel(indexers).transpose(lat_dim, lon_dim).values
            )
            lat_units = str(ds[lat_name].attrs.get("units", ""))
            lon_units = str(ds[lon_name].attrs.get("units", ""))
            if "degree" not in lat_units.lower() or "degree" not in lon_units.lower():
                raise probe.ProbeError(
                    "NetCDF latitude/longitude units are not geographic degrees"
                )
            latitudes = np.asarray(ds[lat_name].values).reshape(-1)
            longitudes = np.asarray(ds[lon_name].values).reshape(-1)

    result = _centers(
        path,
        product_key,
        latitudes,
        longitudes,
        array,
        manifest_path,
        polygon_path,
        max_rows,
    )
    result["product"] = product_key
    result["inspection_status"] = report["status"]
    result["polygon"] = str(polygon_path)
    result["polygon_sha256"] = hashlib.sha256(polygon_path.read_bytes()).hexdigest()
    return result


def write_csv(result: dict[str, Any], output: Path | str) -> None:
    fields = [
        "period",
        "product",
        "version",
        "variable",
        "latitude",
        "longitude",
        "value",
        "unit",
        "quality_candidates",
        "quality_filter_applied",
        "original_file",
        "manifest",
    ]
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(result["rows"])


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", choices=sorted(PRODUCTS))
    parser.add_argument("file", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("polygon", type=Path)
    parser.add_argument("--max-rows", type=int, default=20)
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = spatial_qa(
            args.file, args.manifest, args.polygon, args.product, args.max_rows
        )
        write_csv(result, args.csv)
        summary = {key: value for key, value in result.items() if key != "rows"}
        summary["csv"] = str(args.csv)
        summary["rows_written"] = len(result["rows"])
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - report sanitized local processing failures
        print(
            json.dumps(
                {"status": "error", "error": probe.safe_error(exc)},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

