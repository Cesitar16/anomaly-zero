"""Small, raw-value quality checks for a single GLDAS monthly NetCDF sample."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import xarray as xr


def inspect_gldas_sample(
    path: str | Path,
    *,
    variable: str = "SoilMoi0_10cm_inst",
    bbox: tuple[float, float, float, float] = (138.0, -38.0, 153.0, -24.0),
) -> tuple[xr.Dataset, dict[str, Any]]:
    """Open raw stored values and summarize availability in an inclusive bbox.

    CF decoding and scale/offset are deliberately disabled. Returned values and
    summary statistics therefore remain in the file's stored representation.
    The caller owns the returned dataset and must close it.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(file_path)
    if len(bbox) != 4:
        raise ValueError("bbox must be west,south,east,north")
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("bbox is outside valid longitude/latitude bounds")

    dataset = xr.open_dataset(
        file_path,
        engine="netcdf4",
        decode_cf=False,
        mask_and_scale=False,
        decode_times=False,
    )
    try:
        if variable not in dataset.data_vars:
            raise ValueError(f"required variable {variable!r} is missing")
        for coordinate in ("lat", "lon"):
            if coordinate not in dataset.coords or dataset[coordinate].ndim != 1:
                raise ValueError(f"expected a one-dimensional {coordinate} coordinate")
        da = dataset[variable]
        if "lat" not in da.dims or "lon" not in da.dims:
            raise ValueError("variable must have lat and lon dimensions")
        lat = dataset.lat.values
        lon = dataset.lon.values
        lat_slice = slice(south, north) if lat[0] <= lat[-1] else slice(north, south)
        lon_slice = slice(west, east) if lon[0] <= lon[-1] else slice(east, west)
        subset = da.sel(lat=lat_slice, lon=lon_slice)
        raw = np.asarray(subset.values, dtype=np.float64)

        sentinels: list[float] = []
        for key in ("_FillValue", "missing_value"):
            value = da.attrs.get(key)
            if value is not None:
                for item in np.asarray(value).reshape(-1):
                    try:
                        sentinels.append(float(item))
                    except (TypeError, ValueError):
                        continue
        valid = np.isfinite(raw)
        for sentinel in sentinels:
            valid &= ~np.isnan(raw) if np.isnan(sentinel) else raw != sentinel
        values = raw[valid]
        subset_lat = np.asarray(subset.lat.values)
        subset_lon = np.asarray(subset.lon.values)
        report = {
            "file": file_path.name,
            "variable": variable,
            "dimensions": dict(dataset.sizes),
            "shape": list(da.shape),
            "dtype": str(da.dtype),
            "units": da.attrs.get("units"),
            "attributes": {str(k): _json_safe(v) for k, v in da.attrs.items()},
            "bbox": list(bbox),
            "bbox_semantics": "inclusive rectangular coordinate selection; not a basin mask",
            "subset_shape": list(subset.shape),
            "subset_coordinates": {
                "lat_min": float(np.min(subset_lat)) if subset_lat.size else None,
                "lat_max": float(np.max(subset_lat)) if subset_lat.size else None,
                "lon_min": float(np.min(subset_lon)) if subset_lon.size else None,
                "lon_max": float(np.max(subset_lon)) if subset_lon.size else None,
            },
            "raw_value_count": int(raw.size),
            "valid_count": int(values.size),
            "missing_count": int(raw.size - values.size),
            "coverage_fraction": float(values.size / raw.size) if raw.size else 0.0,
            "raw_valid_summary": (
                {
                    "min": float(np.min(values)),
                    "median": float(np.median(values)),
                    "mean": float(np.mean(values)),
                    "max": float(np.max(values)),
                }
                if values.size
                else None
            ),
            "fill_sentinels": sentinels,
            "scale_factor": _json_safe(da.attrs.get("scale_factor")),
            "add_offset": _json_safe(da.attrs.get("add_offset")),
            "transformations_applied": [],
        }
        return dataset, report
    except Exception:
        dataset.close()
        raise


def _json_safe(value: Any) -> Any:
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return [_json_safe(item) for item in value.tolist()]
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    return value
