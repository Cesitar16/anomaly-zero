"""Offline, provisional diagnostics for NASA grid support around MDBA geometry.

No regional means, QA decisions, or production masks are calculated here.
Raw payloads are opened read-only and their identities are rechecked first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import shapely
from netCDF4 import Dataset
from pyproj import Geod, Transformer
from scipy.spatial import cKDTree
from shapely.geometry import Polygon, shape

from research.ful122_inventory import PRODUCTS, inventory

EXPECTED_MDBA_SHA256 = "d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53"
PRODUCT_VARIABLES = {
    "imerg_final": ("Grid/precipitation", "mm/hr"),
    "merra2": ("T2M", "K"),
    "gldas": ("SoilMoi0_10cm_inst", "kg m-2"),
}
AREA_CRS = "EPSG:3577"
SOURCE_CRS = "EPSG:4326"
MAX_SEGMENT_DEGREES = 0.02
STRATEGIES = [
    {"id": "point_nearest_center", "state": "candidate", "summary": "Nearest centers are not identical spatial supports; record offsets and collisions, select target sites only after approval.", "cost": "low"},
    {"id": "cell_polygon_intersection", "state": "candidate", "summary": "Makes partial edge cells explicit; depends on boundary provenance, cell bounds, projection and area denominator; current MERRA/GLDAS bounds are inferred.", "cost": "medium"},
    {"id": "regrid_or_area_weight", "state": "proposal_only", "summary": "Can harmonize a target lattice or use overlap weights, but entails variable-specific conservation, interpolation/aggregation assumptions and amplified uncertainty; no regridding performed.", "cost": "high"},
]


class SpatialAuditError(ValueError):
    """Input provenance, geometry, or grid is not safe to audit."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_boundary(path: Path, expected_sha256: str | None = EXPECTED_MDBA_SHA256) -> tuple[Any, dict[str, Any]]:
    """Read and validate the known MDBA reference artifact without modifying it."""
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if expected_sha256 and digest != expected_sha256:
        raise SpatialAuditError("boundary SHA-256 differs from the documented MDBA artifact")
    try:
        document = json.loads(raw)
        features = document.get("features", []) if document.get("type") == "FeatureCollection" else []
        geometries = [shape(item["geometry"]) for item in features if item.get("geometry")]
        if len(geometries) != 1:
            raise SpatialAuditError("expected one polygon feature in MDBA GeoJSON")
        geometry = geometries[0]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise SpatialAuditError("MDBA GeoJSON is unreadable or malformed") from exc
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise SpatialAuditError("MDBA reference must be polygonal")
    if not geometry.is_valid:
        raise SpatialAuditError(f"MDBA reference geometry is invalid: {shapely.is_valid_reason(geometry)}")
    west, south, east, north = geometry.bounds
    if east - west > 180:
        raise SpatialAuditError("antimeridian-crossing polygons are not supported by this diagnostic")
    rings = list(geometry.geoms) if geometry.geom_type == "MultiPolygon" else [geometry]
    holes = sum(len(poly.interiors) for poly in rings)
    vertices = sum(len(poly.exterior.coords) + sum(len(ring.coords) for ring in poly.interiors) for poly in rings)
    crs = document.get("crs", {}).get("properties", {}).get("name")
    return geometry, {
        "artifact_sha256": digest,
        "artifact_bytes": len(raw),
        "geometry_type": geometry.geom_type,
        "valid": bool(geometry.is_valid),
        "validity_reason": shapely.is_valid_reason(geometry),
        "component_count": len(rings),
        "hole_count": holes,
        "vertex_count_including_closure": vertices,
        "bbox_wgs84_lonlat": [west, south, east, north],
        "geojson_crs_member": crs,
        "crs_interpretation": "EPSG:4326 export; does not identify the source dataset's native datum",
        "source_item": "MDBA ArcGIS item ba731d77d80947fbbcbf7524364372ff",
        "source_item_modified_utc": "2026-01-14T21:08:32Z (item metadata timestamp, not a geometry version date)",
        "source_item_metadata_checked_utc": "2026-11-15",
        "source_derived_from": "Australia's River Basins 1997 (30 June 1997), according to MDBA item metadata",
        "publisher": "Murray-Darling Basin Authority",
        "source_attribution": "Australian Government Department of Climate Change, Energy, the Environment and Water",
        "license_declared_by_item": "CC BY 4.0",
        "source_urls": [
            "https://www.arcgis.com/sharing/rest/content/items/ba731d77d80947fbbcbf7524364372ff?f=pjson",
            "https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0?f=pjson",
            "https://www.ga.gov.au/bigobj/GA8096.pdf",
        ],
        "source_dataset_datum_note": "Geoscience Australia 1997 product metadata reports AGD66; datum lineage of this re-served legal boundary is not established by that fact",
        "service_spatial_reference": "EPSG:3857 (ArcGIS WKID 102100/3857)",
        "exported_artifact_crs": "EPSG:4326",
    }


def _axis_bounds(values: np.ndarray, explicit: np.ndarray | None) -> np.ndarray:
    centers = np.asarray(values, dtype=np.float64)
    if centers.ndim != 1 or len(centers) < 2 or not np.isfinite(centers).all():
        raise SpatialAuditError("grid coordinate must be a finite 1D array with at least two cells")
    differences = np.diff(centers)
    if not (np.all(differences > 0) or np.all(differences < 0)):
        raise SpatialAuditError("grid coordinate must be strictly monotonic")
    if explicit is not None:
        bounds = np.asarray(explicit, dtype=np.float64)
        if bounds.shape == (2, len(centers)):
            bounds = bounds.T
        if bounds.shape != (len(centers), 2) or not np.isfinite(bounds).all():
            raise SpatialAuditError("explicit coordinate bounds have an unexpected shape or nonfinite values")
        return bounds
    midpoints = (centers[:-1] + centers[1:]) / 2
    bounds = np.empty((len(centers), 2), dtype=np.float64)
    bounds[1:, 0] = midpoints
    bounds[:-1, 1] = midpoints
    bounds[0, 0] = centers[0] - differences[0] / 2
    bounds[-1, 1] = centers[-1] + differences[-1] / 2
    if differences[0] < 0:
        bounds[:, :] = bounds[:, ::-1]
    return bounds


def _coord_digest(lat: np.ndarray, lon: np.ndarray, lat_bounds: np.ndarray, lon_bounds: np.ndarray) -> str:
    digest = hashlib.sha256()
    for values in (lat, lon, lat_bounds, lon_bounds):
        digest.update(np.ascontiguousarray(values, dtype="<f8").tobytes())
    return digest.hexdigest()


def _decode(value: Any) -> str | None:
    if value is None:
        return None
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value)


def _bound_seams(bounds: np.ndarray) -> dict[str, Any]:
    ordered = np.sort(np.asarray(bounds, dtype=np.float64), axis=1)
    seam = ordered[1:, 0] - ordered[:-1, 1]
    tolerance = 1e-12
    gaps = seam[seam > tolerance]
    overlaps = -seam[seam < -tolerance]
    return {
        "adjacent_gaps": len(gaps),
        "adjacent_overlaps": len(overlaps),
        "maximum_gap_degrees": float(gaps.max()) if len(gaps) else 0.0,
        "maximum_overlap_degrees": float(overlaps.max()) if len(overlaps) else 0.0,
        "tolerance_degrees": tolerance,
    }


def _read_grid(path: Path, product: str) -> dict[str, Any]:
    variable_path, expected_unit = PRODUCT_VARIABLES[product]
    if product == "imerg_final":
        with h5py.File(path, "r") as dataset:
            group = dataset["Grid"]
            lat = np.asarray(group["lat"][:], dtype=np.float64)
            lon = np.asarray(group["lon"][:], dtype=np.float64)
            lat_b = _axis_bounds(lat, group["lat_bnds"][:])
            lon_b = _axis_bounds(lon, group["lon_bnds"][:])
            variable = group["precipitation"]
            if variable.shape != (1, len(lon), len(lat)):
                raise SpatialAuditError("IMERG variable shape/order differs from time,lon,lat metadata")
            unit = variable.attrs.get("Units", variable.attrs.get("units"))
            fill = variable.attrs.get("_FillValue")
            order = "time,lon,lat (native); transpose only for diagnostic indexing"
            data_order = "lon,lat"
            bounds_declared = True
            coord_unit = "degrees"
            time = group["time"]
            time_bounds = group.get("time_bnds", None)
            attrs = {
                "bounds_declared": True,
                "lat_axis": "Grid/lat",
                "lon_axis": "Grid/lon",
                "time_units": _decode(time.attrs.get("units", "")),
                "calendar": _decode(time.attrs.get("calendar", "unspecified")),
                "time_values": np.asarray(time[:]).astype(float).tolist(),
                "time_bounds_values": np.asarray(time_bounds[:]).astype(float).tolist() if time_bounds is not None else None,
                "cell_methods": str(variable.attrs.get("cell_methods", "not declared")),
                "qa_or_uncertainty_variables_present": [name for name in ("precipitationQualityIndex", "randomError", "gaugeRelativeWeighting", "probabilityLiquidPrecipitation") if name in group],
            }
    else:
        with Dataset(path, "r") as dataset:
            lat_var, lon_var = dataset.variables["lat"], dataset.variables["lon"]
            lat, lon = np.asarray(lat_var[:], dtype=np.float64), np.asarray(lon_var[:], dtype=np.float64)
            lat_b_name, lon_b_name = getattr(lat_var, "bounds", None), getattr(lon_var, "bounds", None)
            lat_b = _axis_bounds(lat, dataset.variables[lat_b_name][:] if lat_b_name in dataset.variables else None)
            lon_b = _axis_bounds(lon, dataset.variables[lon_b_name][:] if lon_b_name in dataset.variables else None)
            variable = dataset.variables[variable_path]
            if variable.shape != (1, len(lat), len(lon)):
                raise SpatialAuditError(f"{product} variable shape/order differs from time,lat,lon metadata")
            unit = getattr(variable, "units", None)
            fill = getattr(variable, "_FillValue", None)
            order = "time,lat,lon"
            data_order = "lat,lon"
            bounds_declared = bool(lat_b_name and lon_b_name)
            coord_unit = (getattr(lat_var, "units", ""), getattr(lon_var, "units", ""))
            time_var = dataset.variables.get("time")
            time_bounds_name = getattr(time_var, "bounds", None) if time_var is not None else None
            if time_var is not None:
                time_var.set_auto_maskandscale(False)
            time_bounds_var = dataset.variables.get(time_bounds_name) if time_bounds_name else None
            if time_bounds_var is not None:
                time_bounds_var.set_auto_maskandscale(False)
            attrs = {
                "bounds_declared": bounds_declared,
                "lat_bounds_name": lat_b_name,
                "lon_bounds_name": lon_b_name,
                "calendar": _decode(getattr(time_var, "calendar", None)) if time_var is not None else None,
                "time_units": _decode(getattr(time_var, "units", None)) if time_var is not None else None,
                "time_values": np.asarray(time_var[:]).astype(float).tolist() if time_var is not None else None,
                "time_bounds_name": time_bounds_name,
                "time_bounds_values": np.asarray(time_bounds_var[:]).astype(float).tolist() if time_bounds_var is not None else None,
                "cell_methods": getattr(variable, "cell_methods", "not declared"),
                "qa_variables_present": [name for name in dataset.variables if any(token in name.lower() for token in ("quality", "flag", "error"))],
            }
    if isinstance(unit, bytes):
        unit = unit.decode("utf-8", errors="replace")
    if unit != expected_unit:
        raise SpatialAuditError(f"{product} native unit mismatch")
    lat = np.asarray(lat, dtype=np.float64)
    lon = np.asarray(lon, dtype=np.float64)
    lat_b, lon_b = np.asarray(lat_b, dtype=np.float64), np.asarray(lon_b, dtype=np.float64)
    lat_step = float(np.median(np.abs(np.diff(lat))))
    lon_step = float(np.median(np.abs(np.diff(lon))))
    info = {
        "product": product,
        "variable": variable_path,
        "unit": expected_unit,
        "array_order": order,
        "shape": list((1, len(lon), len(lat)) if product == "imerg_final" else (1, len(lat), len(lon))),
        "latitude": {"min_center": float(np.min(lat)), "max_center": float(np.max(lat)), "step_degrees": lat_step, "orientation": "ascending" if lat[-1] > lat[0] else "descending"},
        "longitude": {"min_center": float(np.min(lon)), "max_center": float(np.max(lon)), "step_degrees": lon_step, "orientation": "ascending" if lon[-1] > lon[0] else "descending"},
        "nominal_cell_size_degrees_lat_lon": [lat_step, lon_step],
        "adjacent_bound_seams": {"latitude": _bound_seams(lat_b), "longitude": _bound_seams(lon_b)},
        "bounds_method": "native coordinate bounds" if bounds_declared else "inferred from adjacent center midpoints and nominal end spacing",
        "center_footprint_bbox_lonlat": [float(np.min(lon)), float(np.min(lat)), float(np.max(lon)), float(np.max(lat))],
        "cell_edge_bbox_lonlat": [float(np.min(lon_b)), float(np.min(lat_b)), float(np.max(lon_b)), float(np.max(lat_b))],
        "coordinate_units": coord_unit,
        "fill_value": float(fill) if fill is not None else None,
        "coordinates_sha256": _coord_digest(lat, lon, lat_b, lon_b),
        "data_order": data_order,
        "attributes": attrs,
    }
    return {"lat": lat, "lon": lon, "lat_bounds": lat_b, "lon_bounds": lon_b, "info": info}


def _bbox_indices(values: np.ndarray, lower: float, upper: float) -> tuple[int, int]:
    indices = np.flatnonzero((values >= lower) & (values <= upper))
    if not len(indices):
        raise SpatialAuditError("boundary extent does not overlap product grid")
    return int(indices[0]), int(indices[-1]) + 1


def _candidate_centers(grid: dict[str, Any], geometry: Any) -> tuple[np.ndarray, np.ndarray, np.ndarray, tuple[slice, slice]]:
    west, south, east, north = geometry.bounds
    lat, lon = grid["lat"], grid["lon"]
    j0, j1 = _bbox_indices(lat, south, north)
    i0, i1 = _bbox_indices(lon, west, east)
    lon_part, lat_part = lon[i0:i1], lat[j0:j1]
    xx, yy = np.meshgrid(lon_part, lat_part)
    covered = shapely.intersects_xy(geometry, xx, yy)
    return xx, yy, covered, (slice(j0, j1), slice(i0, i1))


def _cell_polygon(lon_bounds: np.ndarray, lat_bounds: np.ndarray) -> Polygon:
    west, east = float(np.min(lon_bounds)), float(np.max(lon_bounds))
    south, north = float(np.min(lat_bounds)), float(np.max(lat_bounds))
    if east - west > 180:
        raise SpatialAuditError("antimeridian cell bounds are unsupported")
    return Polygon([(west, south), (east, south), (east, north), (west, north), (west, south)])


def _area_diagnostics(grid: dict[str, Any], geometry: Any, transformer: Transformer) -> dict[str, Any]:
    west, south, east, north = geometry.bounds
    lat, lon = grid["lat"], grid["lon"]
    j0, j1 = _bbox_indices(lat, south - 1.0, north + 1.0)
    i0, i1 = _bbox_indices(lon, west - 1.0, east + 1.0)
    projected_geom = shapely.transform(
        shapely.segmentize(geometry, MAX_SEGMENT_DEGREES), transformer.transform, interleaved=False
    )
    boundary_area_m2 = float(projected_geom.area)
    candidate_count = intersect_count = partial_count = 0
    sum_intersection_m2 = 0.0
    partial_fractions: list[float] = []
    for j in range(j0, j1):
        for i in range(i0, i1):
            cell = _cell_polygon(grid["lon_bounds"][i], grid["lat_bounds"][j])
            if not cell.intersects(geometry):
                continue
            candidate_count += 1
            projected_cell = shapely.transform(
                shapely.segmentize(cell, MAX_SEGMENT_DEGREES), transformer.transform, interleaved=False
            )
            intersection = projected_cell.intersection(projected_geom)
            overlap = float(intersection.area)
            if overlap <= 0:
                continue
            intersect_count += 1
            cell_area = float(projected_cell.area)
            fraction = min(1.0, max(0.0, overlap / cell_area)) if cell_area else 0.0
            sum_intersection_m2 += overlap
            if fraction < 1.0 - 1e-8:
                partial_count += 1
                partial_fractions.append(fraction)
    return {
        "bbox_candidate_cells": candidate_count,
        "positive_area_intersection_cells": intersect_count,
        "partially_covered_cells": partial_count,
        "partial_fraction_min": min(partial_fractions) if partial_fractions else None,
        "partial_fraction_max": max(partial_fractions) if partial_fractions else None,
        "sum_projected_intersection_area_km2": sum_intersection_m2 / 1e6,
        "projected_boundary_area_diagnostic_km2": boundary_area_m2 / 1e6,
        "sum_intersection_minus_projected_boundary_km2": (sum_intersection_m2 - boundary_area_m2) / 1e6,
        "interpretation": "provisional geometry diagnostic only; not an approved basin area or regional denominator",
    }


def _read_candidate_values(record: dict[str, Any], grid: dict[str, Any], slices: tuple[slice, slice], center_mask: np.ndarray) -> dict[str, int]:
    product = record["product_key"]
    j_slice, i_slice = slices
    if product == "imerg_final":
        with h5py.File(record["path"], "r") as dataset:
            variable = dataset["Grid/precipitation"]
            raw = np.asarray(variable[0, i_slice, j_slice]).T
            fill = float(variable.attrs["_FillValue"])
    else:
        with Dataset(record["path"], "r") as dataset:
            variable = dataset.variables[PRODUCT_VARIABLES[product][0]]
            variable.set_auto_maskandscale(False)
            raw = np.asarray(variable[0, j_slice, i_slice])
            fill = float(variable._FillValue)
    selected = np.asarray(raw)[center_mask]
    is_fill = selected == fill
    is_nonfinite = ~np.isfinite(selected) & ~is_fill
    valid = np.isfinite(selected) & ~is_fill
    return {
        "center_candidate_count": int(selected.size),
        "fill_count": int(is_fill.sum()),
        "nonfinite_nonfill_count": int(is_nonfinite.sum()),
        "finite_nonfill_count": int(valid.sum()),
        "zero_count_within_finite_nonfill": int((selected[valid] == 0).sum()),
        "negative_finite_nonfill_count": int((selected[valid] < 0).sum()),
    }


def _distance_summary(grid_a: dict[str, Any], grid_b: dict[str, Any], geom: Any, transformer: Transformer) -> dict[str, Any]:
    def points(grid: dict[str, Any]) -> np.ndarray:
        xx, yy, mask, _ = _candidate_centers(grid, geom)
        return np.column_stack((xx[mask], yy[mask]))

    points_a, points_b = points(grid_a), points(grid_b)
    if not len(points_a) or not len(points_b):
        return {"source_center_count": len(points_a), "target_center_count": len(points_b), "status": "no_candidate_centers"}
    projected_a = np.column_stack(transformer.transform(points_a[:, 0], points_a[:, 1]))
    projected_b = np.column_stack(transformer.transform(points_b[:, 0], points_b[:, 1]))
    _distances, nearest = cKDTree(projected_b).query(projected_a, k=1)
    geod = Geod(ellps="WGS84")
    _, _, exact_m = geod.inv(points_a[:, 0], points_a[:, 1], points_b[nearest, 0], points_b[nearest, 1])
    return {
        "source_center_count": len(points_a),
        "target_center_count": len(points_b),
        "source_centers_nearest_target_count": len(points_a),
        "nearest_distance_median_m": float(np.median(exact_m)),
        "nearest_distance_p95_m": float(np.quantile(exact_m, 0.95)),
        "nearest_distance_max_m": float(np.max(exact_m)),
        "interpretation": "directed nearest-center distances; not paired observations or proof of equivalent footprints",
    }


def audit(input_dirs: list[Path], boundary_path: Path) -> dict[str, Any]:
    geometry, boundary_info = load_boundary(boundary_path)
    report = inventory(input_dirs)
    target_months = {f"2005-{month:02d}" for month in range(1, 13)}
    records_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in report["records"]:
        if record.get("eligible") and record.get("period") in target_months:
            records_by_product[record["product_key"]].append(record)
    expected_products = set(PRODUCTS)
    if set(records_by_product) != expected_products or any(len(rows) != 12 for rows in records_by_product.values()):
        raise SpatialAuditError("NASA inventory is not 12 eligible months for each of the three products")

    grids: dict[str, dict[str, Any]] = {}
    for product, rows in records_by_product.items():
        rows.sort(key=lambda item: item["period"])
        grid = _read_grid(Path(rows[0]["path"]), product)
        for row in rows[1:]:
            other = _read_grid(Path(row["path"]), product)
            if other["info"]["coordinates_sha256"] != grid["info"]["coordinates_sha256"]:
                raise SpatialAuditError(f"{product} coordinates vary across 2005 months")
        xx, yy, center_mask, slices = _candidate_centers(grid, geometry)
        grid["candidate_x"], grid["candidate_y"], grid["center_mask"], grid["slices"] = xx, yy, center_mask, slices
        j0, j1 = slices[0].start, slices[0].stop
        i0, i1 = slices[1].start, slices[1].stop
        local_lat_bounds = grid["lat_bounds"][max(0, j0 - 1) : min(len(grid["lat"]), j1 + 1)]
        local_lon_bounds = grid["lon_bounds"][max(0, i0 - 1) : min(len(grid["lon"]), i1 + 1)]
        grid["info"]["adjacent_bound_seams_near_reference_bbox"] = {
            "latitude": _bound_seams(local_lat_bounds),
            "longitude": _bound_seams(local_lon_bounds),
        }
        grid["info"]["centers_inside_reference_geometry"] = int(center_mask.sum())
        grid["info"]["analysis_region_is_exploratory_only"] = True
        grids[product] = grid

    transformer = Transformer.from_crs(SOURCE_CRS, AREA_CRS, always_xy=True)
    transformer.transform(140.0, -35.0)
    for product, grid in grids.items():
        grid["info"]["cell_overlap_diagnostic"] = _area_diagnostics(grid, geometry, transformer)
        west, south, east, north = geometry.bounds
        edge_west, edge_south, edge_east, edge_north = grid["info"]["cell_edge_bbox_lonlat"]
        grid["info"]["reference_bbox_within_cell_edge_domain"] = bool(
            edge_west <= west and edge_east >= east and edge_south <= south and edge_north >= north
        )

    distances = {}
    products = ("imerg_final", "merra2", "gldas")
    for i, first in enumerate(products):
        for second in products[i + 1 :]:
            distances[f"{first}_to_{second}"] = _distance_summary(grids[first], grids[second], geometry, transformer)
            distances[f"{second}_to_{first}"] = _distance_summary(grids[second], grids[first], geometry, transformer)

    monthly_records = []
    for product in products:
        grid = grids[product]
        for row in records_by_product[product]:
            entry = json.loads(Path(row["manifest"]).read_text(encoding="utf-8"))
            counts = _read_candidate_values(row, grid, grid["slices"], grid["center_mask"])
            monthly_records.append({
                "product": product,
                "month": row["period"],
                "granule_id": entry.get("granule_id"),
                "producer_granule_id": entry.get("producer_granule_id"),
                "collection_id": entry.get("collection_id"),
                "version": entry.get("product", {}).get("version"),
                "variable": entry.get("product", {}).get("variable"),
                "unit": PRODUCT_VARIABLES[product][1],
                "payload_sha256": row["sha256"],
                "payload_bytes": row["bytes"],
                "source_manifest_sha256": sha256_file(Path(row["manifest"])),
                "temporal_period": entry.get("period"),
                "candidate_center_value_counts": counts,
                "qa_status": "unassessed; no QA filters applied",
                "spatial_support_status": "candidate_not_approved",
            })
    monthly_records.sort(key=lambda item: (item["product"], item["month"]))

    return {
        "schema_version": 1,
        "status": "diagnostic_only_not_approved",
        "generated_by": "research.ful124_spatial_audit",
        "year": 2005,
        "inventory": {
            "eligible_months_by_product": report["counts"],
            "eligible_product_month_records": sum(report["counts"].values()),
            "duplicate_identical_records_excluded": report["rejected_count"],
            "triple_overlap_months": [row["period"] for row in report["matrix"] if row["triple_overlap"]],
        },
        "boundary": boundary_info,
        "area_crs_for_candidate_overlay": AREA_CRS,
        "area_transform_assumption": "transform WGS84 coordinates to EPSG:3577 after densifying segments at 0.02 degrees; no datum/geometry approval is implied",
        "area_transform_metadata": {
            "source_crs": SOURCE_CRS,
            "target_crs": AREA_CRS,
            "operation_description": transformer.description,
            "declared_accuracy_m": transformer.accuracy if transformer.accuracy >= 0 else None,
            "operation_pinned": False,
        },
        "grids": {product: grid["info"] for product, grid in grids.items()},
        "directed_nearest_center_distances": distances,
        "monthly_payload_records": monthly_records,
        "strategies": STRATEGIES,
        "scientific_status": {
            "regional_aggregation_performed": False,
            "inferential_statistics_performed": False,
            "model_training_performed": False,
            "qa_imerg": "unassessed",
            "gate_r": "pending",
            "gate_t": "pending",
            "gldas_mask_lineage": "uncertain",
            "precipitation_unit_conversion": "none; IMERG remains mm/hr",
            "support_approval": "not_approved",
        },
        "limitations": [
            "The cached MDBA shape is an exploratory reference boundary, not a scientifically approved mask or statistical unit.",
            "The ArcGIS item documents a legal Water Act boundary derived from 1997 river basins; source datum lineage of the re-served geometry is not established.",
            "MERRA-2 and GLDAS cell bounds are inferred from centers; they are not present as native coordinate bounds in the inspected files.",
            "IMERG QA, GLDAS mask lineage, Gate R and Gate T remain unresolved.",
            "Candidate center masks, edge counts, overlay areas and nearest-center distances are diagnostics, not approved co-located observations or regional estimates.",
            "The overlay is a projected geometric diagnostic and is sensitive to geometry precision, coordinate transformation, assumed edge curves and segmentation length.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True)
    parser.add_argument("--boundary-geojson", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = audit(args.input_dir, args.boundary_geojson)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "inventory": result["inventory"],
        "boundary_sha256": result["boundary"]["artifact_sha256"],
        "monthly_record_count": len(result["monthly_payload_records"]),
        "output": args.output.as_posix(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
