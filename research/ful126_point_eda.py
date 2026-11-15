"""Read-only candidate-site point EDA for authentic NASA monthly granules.

This utility preserves each product's native grid, units, stored values, and
provenance. Its sites and cell assignments are experimental candidates only.
It does not create a regional aggregate or apply scientific QA filters.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import h5py
import matplotlib
import numpy as np
import shapely
from netCDF4 import Dataset
from pyproj import Geod, Transformer
from shapely.geometry import Point, box

from research.ful122_inventory import PRODUCTS, inventory
from research.ful124_spatial_audit import (
    AREA_CRS,
    EXPECTED_MDBA_SHA256,
    PRODUCT_VARIABLES,
    SOURCE_CRS,
    _axis_bounds,
    _bbox_indices,
    _read_grid,
    load_boundary,
    sha256_file,
)

YEAR = 2005
MONTHS = tuple(f"{YEAR}-{month:02d}" for month in range(1, 13))
STATUS = "diagnostic_only_not_approved"
QA_STATUS = "unassessed; no scientific QA filters applied"
SITE_STRIPS = (
    ("site_west_extent", "western extent third"),
    ("site_central_extent", "central extent third"),
    ("site_east_extent", "eastern extent third"),
)
PRODUCT_ORDER = ("imerg_final", "merra2", "gldas")
CONTAINMENT_METHODS = {
    "imerg_final": ("native_bounds", "derived_midpoint_bounds"),
    "merra2": ("inferred_bounds",),
    "gldas": ("inferred_bounds",),
}


class PointEdaError(ValueError):
    """Input provenance, product structure, or site selection is invalid."""


def validate_month_coverage(
    records_by_product: dict[str, list[dict[str, Any]]], target_months: set[str]
) -> None:
    """Require exactly one eligible record per target month and NASA product."""
    if set(records_by_product) != set(PRODUCTS):
        raise PointEdaError("all three NASA products must have eligible monthly records")
    for product, records in records_by_product.items():
        periods = [record.get("period") for record in records]
        if len(periods) != len(target_months) or set(periods) != target_months:
            raise PointEdaError(f"{product} must have exactly one eligible record for every target month")


def _float_attr(value: Any) -> float | None:
    array = np.asarray(value)
    if array.size != 1:
        return None
    try:
        return float(array.reshape(-1)[0])
    except (TypeError, ValueError):
        return None


def _text_attr(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _variable_attributes(variable: Any, attribute_names: tuple[str, ...]) -> dict[str, Any]:
    attributes: dict[str, Any] = {}
    for name in attribute_names:
        if hasattr(variable, "attrs"):
            if name not in variable.attrs:
                continue
            value = variable.attrs[name]
        else:
            if not hasattr(variable, name):
                continue
            value = getattr(variable, name)
        array = np.asarray(value)
        if array.size == 1:
            scalar = array.reshape(-1)[0]
            if isinstance(scalar, bytes):
                attributes[name] = scalar.decode("utf-8", errors="replace")
            elif np.issubdtype(array.dtype, np.number):
                attributes[name] = float(scalar)
            else:
                attributes[name] = str(scalar)
        elif np.issubdtype(array.dtype, np.number):
            attributes[name] = [float(item) for item in array.reshape(-1)]
        else:
            attributes[name] = [str(item) for item in array.reshape(-1)]
    return attributes


def classify_value(raw_value: Any, markers: list[float], scale_factor: float, add_offset: float) -> dict[str, Any]:
    """Classify an unpacked storage value and decode only scale/offset once."""
    raw = np.asarray(raw_value).reshape(()).item()
    numeric = float(raw)
    is_fill = False
    if np.issubdtype(np.asarray(raw).dtype, np.number):
        raw_dtype = np.asarray(raw).dtype
        for marker in markers:
            try:
                stored_marker = np.asarray(marker, dtype=raw_dtype).reshape(()).item()
            except (TypeError, ValueError, OverflowError):
                stored_marker = marker
            if numeric == float(stored_marker):
                is_fill = True
                break
    if is_fill:
        stored_status = "fill"
        decoded = None
        decoded_status = "fill"
    elif math.isnan(numeric):
        stored_status = "nan"
        decoded = None
        decoded_status = "nan"
    elif not math.isfinite(numeric):
        stored_status = "nonfinite"
        decoded = None
        decoded_status = "nonfinite"
    else:
        stored_status = "zero_valid" if numeric == 0 else "finite"
        decoded_number = numeric * scale_factor + add_offset
        if not math.isfinite(decoded_number):
            decoded, decoded_status = None, "nonfinite_after_scale_offset"
        else:
            decoded = float(decoded_number)
            if decoded_number == 0:
                decoded_status = "zero_valid"
            elif decoded_number < 0:
                decoded_status = "negative_finite_review"
            else:
                decoded_status = "finite"
    return {
        "stored_value": numeric,
        "stored_status": stored_status,
        "decoded_value": decoded,
        "decoded_status": decoded_status,
        "scale_factor_applied": float(scale_factor),
        "add_offset_applied": float(add_offset),
        "decoding_rule": "decoded_value = raw stored value * scale_factor + add_offset; fill/nonfinite classified before decode",
    }


def select_candidate_sites(geometry: Any) -> list[dict[str, Any]]:
    """Place three deterministic diagnostic candidates in projected extent thirds."""
    transformer = Transformer.from_crs(SOURCE_CRS, AREA_CRS, always_xy=True)
    inverse = Transformer.from_crs(AREA_CRS, SOURCE_CRS, always_xy=True)
    projected = shapely.transform(geometry, transformer.transform, interleaved=False)
    west, south, east, north = projected.bounds
    if not east > west or not north > south:
        raise PointEdaError("experimental boundary has an empty projected extent")
    width = east - west
    sites = []
    for index, (site_id, position) in enumerate(SITE_STRIPS):
        strip_west = west + width * index / 3
        strip_east = west + width * (index + 1) / 3
        clip = box(strip_west, south - 1, strip_east, north + 1)
        segment = shapely.intersection(projected, clip)
        if segment.is_empty:
            raise PointEdaError(f"no polygon area in the {position}")
        site_projected = segment.representative_point()
        lon, lat = inverse.transform(site_projected.x, site_projected.y)
        point = Point(float(lon), float(lat))
        if not geometry.covers(point):
            raise PointEdaError(f"candidate {site_id} is not covered by the experimental polygon")
        sites.append(
            {
                "site_id": site_id,
                "position": position,
                "longitude": float(lon),
                "latitude": float(lat),
                "selection_method": "representative point of the MDBA polygon clipped to one equal-width EPSG:3577 extent third",
                "preliminary_rationale": "spread candidates across the polygon's projected west-east extent to inspect spatial sensitivity; not a hydrological site or statistically representative sample",
                "inside_exploratory_polygon": True,
                "status": "candidate_not_approved",
            }
        )
    return sites


def _nearby_slice(values: np.ndarray, coordinate: float, margin: float = 1.0) -> tuple[int, int]:
    return _bbox_indices(values, coordinate - margin, coordinate + margin)


def nearest_center_cell(site: dict[str, Any], grid: dict[str, Any]) -> dict[str, Any]:
    """Find projected-CRS nearest center in a local window; measure offset geodesically."""
    lat, lon = grid["lat"], grid["lon"]
    j0, j1 = _nearby_slice(lat, site["latitude"])
    i0, i1 = _nearby_slice(lon, site["longitude"])
    lon_part, lat_part = lon[i0:i1], lat[j0:j1]
    xx, yy = np.meshgrid(lon_part, lat_part)
    transformer = Transformer.from_crs(SOURCE_CRS, AREA_CRS, always_xy=True)
    cell_x, cell_y = transformer.transform(xx, yy)
    site_x, site_y = transformer.transform(site["longitude"], site["latitude"])
    distance2 = (cell_x - site_x) ** 2 + (cell_y - site_y) ** 2
    local_row, local_col = np.unravel_index(int(np.argmin(distance2)), distance2.shape)
    row, col = j0 + int(local_row), i0 + int(local_col)
    center_lon, center_lat = float(lon[col]), float(lat[row])
    geod = Geod(ellps="WGS84")
    _, _, distance_m = geod.inv(site["longitude"], site["latitude"], center_lon, center_lat)
    return {
        "row_latitude": row,
        "column_longitude": col,
        "center_lon_lat": [center_lon, center_lat],
        "assignment_rule": "minimum Euclidean distance in EPSG:3577 among grid centers within 1 degree of the site; final offset measured geodesically on WGS84",
        "site_to_center_geodesic_distance_m": float(distance_m),
        "status": "candidate_not_approved",
    }


def containing_cells(site: dict[str, Any], grid: dict[str, Any], method: str) -> list[dict[str, int]]:
    """Return all cells whose axis-aligned lon/lat bounds inclusively contain a site."""
    if method == "native_bounds":
        lat_bounds, lon_bounds = grid["lat_bounds"], grid["lon_bounds"]
    elif method == "derived_midpoint_bounds":
        lat_bounds, lon_bounds = _axis_bounds(grid["lat"], None), _axis_bounds(grid["lon"], None)
    elif method == "inferred_bounds":
        lat_bounds, lon_bounds = grid["lat_bounds"], grid["lon_bounds"]
    else:
        raise ValueError(f"unsupported containment method: {method}")
    lat_sorted = np.sort(np.asarray(lat_bounds, dtype=np.float64), axis=1)
    lon_sorted = np.sort(np.asarray(lon_bounds, dtype=np.float64), axis=1)
    rows = np.flatnonzero((lat_sorted[:, 0] <= site["latitude"]) & (site["latitude"] <= lat_sorted[:, 1]))
    cols = np.flatnonzero((lon_sorted[:, 0] <= site["longitude"]) & (site["longitude"] <= lon_sorted[:, 1]))
    return [{"row_latitude": int(row), "column_longitude": int(col)} for row in rows for col in cols]


def adjacent_cells(cell: dict[str, int], grid: dict[str, Any]) -> list[dict[str, int]]:
    """Return the in-grid four-connected neighbors without longitude wrapping."""
    row, col = cell["row_latitude"], cell["column_longitude"]
    candidates = ((row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1))
    return [
        {"row_latitude": r, "column_longitude": c}
        for r, c in candidates
        if 0 <= r < len(grid["lat"]) and 0 <= c < len(grid["lon"])
    ]


def _read_cells_from_payload(
    path: Path, product: str, indices: list[dict[str, int]]
) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[str, Any]]:
    """Read raw values at requested indices once, with mask/scale auto-decoding disabled."""
    variable_path, expected_unit = PRODUCT_VARIABLES[product]
    if product == "imerg_final":
        with h5py.File(path, "r") as dataset:
            variable = dataset[variable_path]
            if variable.shape[0] != 1:
                raise PointEdaError("IMERG monthly granule must contain exactly one time slice")
            unit = _text_attr(variable.attrs.get("Units", variable.attrs.get("units")))
            attributes = _variable_attributes(variable, ("_FillValue", "CodeMissingValue", "missing_value", "scale_factor", "add_offset"))
            stored_dtype = str(variable.dtype)
            result = {}
            for item in indices:
                row, col = item["row_latitude"], item["column_longitude"]
                raw = variable[0, col, row]
                result[(row, col)] = _classify_from_attributes(raw, attributes, stored_dtype)
    else:
        with Dataset(path, "r") as dataset:
            variable = dataset.variables[variable_path]
            if variable.shape[0] != 1:
                raise PointEdaError(f"{product} monthly granule must contain exactly one time slice")
            variable.set_auto_maskandscale(False)
            unit = _text_attr(getattr(variable, "units", None))
            attributes = _variable_attributes(variable, ("_FillValue", "missing_value", "CodeMissingValue", "scale_factor", "add_offset"))
            stored_dtype = str(variable.dtype)
            result = {}
            for item in indices:
                row, col = item["row_latitude"], item["column_longitude"]
                raw = variable[0, row, col]
                result[(row, col)] = _classify_from_attributes(raw, attributes, stored_dtype)
    if unit != expected_unit:
        raise PointEdaError(f"{product} expected native units {expected_unit!r}, got {unit!r}")
    return result, {
        "variable": variable_path,
        "unit": unit,
        "stored_dtype": stored_dtype,
        "attributes": attributes,
        "auto_maskandscale_disabled": True,
        "scale_factor_present": "scale_factor" in attributes,
        "add_offset_present": "add_offset" in attributes,
    }


def _classify_from_attributes(raw: Any, attributes: dict[str, Any], stored_dtype: str) -> dict[str, Any]:
    raw_scalar = np.asarray(raw).reshape(()).item()
    raw_dtype = np.dtype(stored_dtype)
    markers: list[float] = []
    for key in ("_FillValue", "missing_value", "CodeMissingValue"):
        marker = attributes.get(key)
        if marker is None:
            continue
        for value in marker if isinstance(marker, list) else [marker]:
            try:
                markers.append(float(np.asarray(value, dtype=raw_dtype).reshape(()).item()))
            except (TypeError, ValueError, OverflowError):
                continue
    scale = float(attributes.get("scale_factor", 1.0))
    offset = float(attributes.get("add_offset", 0.0))
    result = classify_value(np.asarray(raw_scalar, dtype=raw_dtype), markers, scale, offset)
    result["stored_dtype"] = stored_dtype
    result["fill_markers_stored_representation"] = markers
    result["units_conversion_applied"] = False
    return result


def _manifest_entry_for(record: dict[str, Any]) -> dict[str, Any]:
    document = json.loads(Path(record["manifest"]).read_text(encoding="utf-8"))
    if document.get("filename") == record["filename"]:
        return document
    for entry in document.get("samples", []):
        if entry.get("filename") == record["filename"]:
            return entry
    raise PointEdaError("eligible inventory record has no matching manifest entry")


def _grid_metadata(grid: dict[str, Any], method: str) -> dict[str, Any]:
    return {
        "grid_shape_time_lat_lon_or_time_lon_lat": grid["info"]["shape"],
        "coordinates_sha256": grid["info"]["coordinates_sha256"],
        "cell_size_degrees_lat_lon": grid["info"]["nominal_cell_size_degrees_lat_lon"],
        "bounds_method": grid["info"]["bounds_method"],
        "coordinate_units": grid["info"]["coordinate_units"],
        "cell_assignment_method": method,
    }


def _summary(observations: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(row["decoded_value_status"] for row in observations)
    finite = [row["decoded_value"] for row in observations if row["decoded_value_status"] in {"finite", "zero_valid", "negative_finite_review"}]
    return {
        "months_expected": 12,
        "months_observed": len(observations),
        "counts_by_value_status": dict(sorted(counts.items())),
        "minimum_decoded_value": min(finite) if finite else None,
        "maximum_decoded_value": max(finite) if finite else None,
        "summary_scope": "descriptive min/max over this candidate site's one native grid cell and 2005 monthly values only; no spatial or inferential interpretation",
    }


def _value_payload(record: dict[str, Any], entry: dict[str, Any], grid: dict[str, Any], cell: dict[str, Any], value: dict[str, Any], variable_meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "month": record["period"],
        "granule_id": entry.get("granule_id"),
        "producer_granule_id": entry.get("producer_granule_id"),
        "collection_id": entry.get("collection_id"),
        "product_version": entry.get("product", {}).get("version"),
        "product": record["product_key"],
        "variable": PRODUCT_VARIABLES[record["product_key"]][0],
        "unit_original": PRODUCT_VARIABLES[record["product_key"]][1],
        "manifest_period": entry.get("period"),
        "payload_sha256": record["sha256"],
        "payload_bytes": record["bytes"],
        "source_manifest_sha256": sha256_file(Path(record["manifest"])),
        "grid_cell_index_zero_based": {"row_latitude": cell["row_latitude"], "column_longitude": cell["column_longitude"]},
        "cell_center_lon_lat": cell["center_lon_lat"],
        "cell_bounds_lon_lat": cell["cell_bounds_lon_lat"],
        "cell_bounds_method": grid["info"]["bounds_method"],
        "cell_assignment_rule": cell["assignment_rule"],
        "site_to_center_geodesic_distance_m": cell["site_to_center_geodesic_distance_m"],
        "stored_value": value["stored_value"],
        "stored_value_status": value["stored_status"],
        "decoded_value": value["decoded_value"],
        "decoded_value_status": value["decoded_status"],
        "stored_dtype": value["stored_dtype"],
        "scale_factor_attribute": variable_meta["attributes"].get("scale_factor"),
        "add_offset_attribute": variable_meta["attributes"].get("add_offset"),
        "scale_factor_applied": value["scale_factor_applied"],
        "add_offset_applied": value["add_offset_applied"],
        "fill_markers_stored_representation": value["fill_markers_stored_representation"],
        "qa_status": QA_STATUS,
        "state": STATUS,
    }


def run_experiment(input_dirs: list[Path], boundary_path: Path) -> dict[str, Any]:
    geometry, boundary_info = load_boundary(boundary_path, EXPECTED_MDBA_SHA256)
    report = inventory(input_dirs)
    target_set = set(MONTHS)
    records_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in report["records"]:
        if record.get("eligible") and record.get("period") in target_set:
            records_by_product[record["product_key"]].append(record)
    validate_month_coverage(records_by_product, target_set)

    grids: dict[str, dict[str, Any]] = {}
    grid_month_metadata: dict[str, dict[str, Any]] = defaultdict(dict)
    for product in PRODUCT_ORDER:
        records_by_product[product].sort(key=lambda row: row["period"])
        for record in records_by_product[product]:
            current = _read_grid(Path(record["path"]), product)
            if product not in grids:
                grids[product] = current
            elif current["info"]["coordinates_sha256"] != grids[product]["info"]["coordinates_sha256"]:
                raise PointEdaError(f"{product} coordinate/bounds arrays vary across 2005 months")
            grid_month_metadata[product][record["period"]] = current["info"]["attributes"]

    sites = select_candidate_sites(geometry)
    assignments: dict[str, dict[str, dict[str, Any]]] = {}
    for site in sites:
        assignments[site["site_id"]] = {}
        for product in PRODUCT_ORDER:
            grid = grids[product]
            nearest = nearest_center_cell(site, grid)
            row, col = nearest["row_latitude"], nearest["column_longitude"]
            nearest["cell_bounds_lon_lat"] = [
                float(np.min(grid["lon_bounds"][col])),
                float(np.min(grid["lat_bounds"][row])),
                float(np.max(grid["lon_bounds"][col])),
                float(np.max(grid["lat_bounds"][row])),
            ]
            nearest["native_cell_resolution_degrees_lat_lon"] = grid["info"]["nominal_cell_size_degrees_lat_lon"]
            sensitivity = {}
            for method in CONTAINMENT_METHODS[product]:
                hits = containing_cells(site, grid, method)
                sensitivity[method] = {
                    "cells_containing_site_inclusive_bounds": hits,
                    "hit_count": len(hits),
                    "status": "candidate_not_approved",
                    "interpretation": "one or more cells can hit at shared bounds; no arbitrary tie break is applied",
                }
            sensitivity["adjacent_cells_4_neighbor"] = {
                "cells": adjacent_cells(nearest, grid),
                "status": "candidate_not_approved",
                "interpretation": "four-connected cardinal neighbors extracted to quantify local cell sensitivity only",
            }
            sensitivity["nearest_center_matches_containing_cells"] = {
                method: any(hit["row_latitude"] == row and hit["column_longitude"] == col for hit in result["cells_containing_site_inclusive_bounds"])
                for method, result in sensitivity.items()
                if method in CONTAINMENT_METHODS[product]
            }
            assignments[site["site_id"]][product] = {
                "status": STATUS,
                "nearest_center": nearest,
                "containment_sensitivity": sensitivity,
                "bounds_method": grid["info"]["bounds_method"],
                "grid_metadata": _grid_metadata(grid, "nearest center in EPSG:3577; offsets via WGS84 geodesic"),
            }

    series: dict[str, dict[str, list[dict[str, Any]]]] = {
        site["site_id"]: {product: [] for product in PRODUCT_ORDER} for site in sites
    }
    sensitivity_observations: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {
        site["site_id"]: {product: {} for product in PRODUCT_ORDER} for site in sites
    }
    file_metadata: dict[tuple[str, str], dict[str, Any]] = {}
    geod = Geod(ellps="WGS84")
    for product in PRODUCT_ORDER:
        for record in records_by_product[product]:
            needed_by_site: dict[str, dict[str, list[dict[str, int]]]] = {}
            unique_cells: dict[tuple[int, int], dict[str, int]] = {}
            for site in sites:
                selection = assignments[site["site_id"]][product]
                methods: dict[str, list[dict[str, int]]] = {"nearest_center": [
                    {"row_latitude": selection["nearest_center"]["row_latitude"], "column_longitude": selection["nearest_center"]["column_longitude"]}
                ]}
                for method, result in selection["containment_sensitivity"].items():
                    if method == "adjacent_cells_4_neighbor":
                        methods[method] = result["cells"]
                    elif not method.startswith("nearest_center_matches"):
                        methods[method] = result["cells_containing_site_inclusive_bounds"]
                needed_by_site[site["site_id"]] = methods
                for cells in methods.values():
                    for cell in cells:
                        unique_cells[(cell["row_latitude"], cell["column_longitude"])] = cell
            values, variable_meta = _read_cells_from_payload(Path(record["path"]), product, list(unique_cells.values()))
            file_metadata[(product, record["period"])] = variable_meta
            entry = _manifest_entry_for(record)
            if entry.get("product", {}).get("variable") != PRODUCTS[product]["variable"]:
                raise PointEdaError("manifest variable does not match the inventoried NASA product")
            for site in sites:
                site_id = site["site_id"]
                selection = assignments[site_id][product]
                nearest = selection["nearest_center"]
                nearest_key = (nearest["row_latitude"], nearest["column_longitude"])
                nearest_record = _value_payload(record, entry, grids[product], nearest, values[nearest_key], variable_meta)
                nearest_record["site_id"] = site_id
                nearest_record["site_lon_lat"] = [site["longitude"], site["latitude"]]
                nearest_record["native_time_metadata"] = grid_month_metadata[product][record["period"]]
                series[site_id][product].append(nearest_record)
                for method, cells in needed_by_site[site_id].items():
                    if method == "nearest_center":
                        continue
                    items = []
                    for cell in cells:
                        key = (cell["row_latitude"], cell["column_longitude"])
                        cell_info = {
                            **cell,
                            "center_lon_lat": [float(grids[product]["lon"][cell["column_longitude"]]), float(grids[product]["lat"][cell["row_latitude"]])],
                            "cell_bounds_lon_lat": [
                                float(np.min(grids[product]["lon_bounds"][cell["column_longitude"]])),
                                float(np.min(grids[product]["lat_bounds"][cell["row_latitude"]])),
                                float(np.max(grids[product]["lon_bounds"][cell["column_longitude"]])),
                                float(np.max(grids[product]["lat_bounds"][cell["row_latitude"]])),
                            ],
                            "assignment_rule": (
                                "four-connected cardinal neighbor of nearest-center cell"
                                if method == "adjacent_cells_4_neighbor"
                                else f"point containment in {method} (inclusive bounds; candidate only)"
                            ),
                            "site_to_center_geodesic_distance_m": float(
                                geod.inv(
                                    site["longitude"], site["latitude"],
                                    float(grids[product]["lon"][cell["column_longitude"]]),
                                    float(grids[product]["lat"][cell["row_latitude"]]),
                                )[2]
                            ),
                        }
                        items.append({"cell": cell_info, "value": values[key]})
                    label = "adjacent_neighbor_cells" if method == "adjacent_cells_4_neighbor" else "cell_containment_candidates"
                    sensitivity_observations[site_id][product].setdefault(method, []).append(
                        {"month": record["period"], "status": label if cells else "no_candidate_cells", "candidates": items}
                    )

    pairwise_distances = {}
    for product in PRODUCT_ORDER:
        pairwise_distances[product] = {}
        for first_index, first_site in enumerate(sites):
            for second_site in sites[first_index + 1 :]:
                first = assignments[first_site["site_id"]][product]["nearest_center"]["center_lon_lat"]
                second = assignments[second_site["site_id"]][product]["nearest_center"]["center_lon_lat"]
                _, _, distance_m = geod.inv(first[0], first[1], second[0], second[1])
                pairwise_distances[product][f"{first_site['site_id']}__{second_site['site_id']}"] = float(distance_m)

    cross_product_center_distances = {}
    for site in sites:
        site_id = site["site_id"]
        centers = {
            product: assignments[site_id][product]["nearest_center"]["center_lon_lat"]
            for product in PRODUCT_ORDER
        }
        distances = {}
        for first_index, first_product in enumerate(PRODUCT_ORDER):
            for second_product in PRODUCT_ORDER[first_index + 1 :]:
                _, _, distance_m = geod.inv(
                    centers[first_product][0], centers[first_product][1],
                    centers[second_product][0], centers[second_product][1],
                )
                distances[f"{first_product}__{second_product}"] = float(distance_m)
        cross_product_center_distances[site_id] = distances

    site_product_summary = {
        site_id: {product: _summary(rows) for product, rows in product_rows.items()}
        for site_id, product_rows in series.items()
    }
    adjacent_sensitivity_summary = {}
    for site in sites:
        site_id = site["site_id"]
        adjacent_sensitivity_summary[site_id] = {}
        for product in PRODUCT_ORDER:
            baseline_by_month = {
                row["month"]: row for row in series[site_id][product]
            }
            comparisons = []
            changed_values = 0
            changed_statuses = 0
            absolute_differences = []
            for month in sensitivity_observations[site_id][product].get("adjacent_cells_4_neighbor", []):
                baseline = baseline_by_month[month["month"]]
                for candidate in month["candidates"]:
                    value = candidate["value"]
                    comparable = (
                        baseline["decoded_value"] is not None
                        and value["decoded_value"] is not None
                        and math.isfinite(baseline["decoded_value"])
                        and math.isfinite(value["decoded_value"])
                    )
                    if baseline["decoded_value_status"] != value["decoded_status"]:
                        changed_statuses += 1
                    if comparable:
                        delta = abs(baseline["decoded_value"] - value["decoded_value"])
                        comparisons.append(delta)
                        if delta != 0:
                            changed_values += 1
                            absolute_differences.append(delta)
            adjacent_sensitivity_summary[site_id][product] = {
                "neighbor_cell_month_comparisons": len(comparisons),
                "comparisons_with_different_finite_value": changed_values,
                "comparisons_with_different_value_status": changed_statuses,
                "maximum_absolute_difference_native_unit": max(absolute_differences) if absolute_differences else 0.0,
                "scope": "exact local cell-value comparison to nearest-center series; descriptive only, no inference or QA filter",
            }
    monthly_identities = []
    for product in PRODUCT_ORDER:
        for record in records_by_product[product]:
            entry = _manifest_entry_for(record)
            monthly_identities.append(
                {
                    "product": product,
                    "month": record["period"],
                    "granule_id": entry.get("granule_id"),
                    "producer_granule_id": entry.get("producer_granule_id"),
                    "collection_id": entry.get("collection_id"),
                    "product_version": entry.get("product", {}).get("version"),
                    "variable": entry.get("product", {}).get("variable"),
                    "unit": entry.get("product", {}).get("unit"),
                    "payload_sha256": record["sha256"],
                    "payload_bytes": record["bytes"],
                    "source_manifest_sha256": sha256_file(Path(record["manifest"])),
                    "native_time_metadata": grid_month_metadata[product][record["period"]],
                    "scale_factor_attribute": file_metadata[(product, record["period"])]["attributes"].get("scale_factor"),
                    "add_offset_attribute": file_metadata[(product, record["period"])]["attributes"].get("add_offset"),
                    "fill_attributes": {key: value for key, value in file_metadata[(product, record["period"])]["attributes"].items() if key in {"_FillValue", "missing_value", "CodeMissingValue"}},
                }
            )
    monthly_identities.sort(key=lambda item: (item["product"], item["month"]))

    return {
        "schema_version": 1,
        "status": STATUS,
        "generated_by": "research.ful126_point_eda",
        "year": YEAR,
        "authorization_scope": "MDBA GeoJSON hash authorized by César exclusively for controlled experimental tests; not as statistical mask or regional denominator",
        "boundary": boundary_info,
        "inventory": {
            "eligible_months_by_product": report["counts"],
            "eligible_records": sum(report["counts"].values()),
            "rejected_candidates": report["rejected_count"],
            "triple_overlap_months": [row["period"] for row in report["matrix"] if row["triple_overlap"]],
            "inventory_policy": report["policy"],
        },
        "sites": sites,
        "grid_assignments": assignments,
        "pairwise_center_distances_m": pairwise_distances,
        "cross_product_center_distances_by_site_m": cross_product_center_distances,
        "observations_by_site_and_product": series,
        "containment_sensitivity_observations": sensitivity_observations,
        "descriptive_summaries_by_site_and_product": site_product_summary,
        "adjacent_cell_sensitivity_summary": adjacent_sensitivity_summary,
        "monthly_granule_identities": monthly_identities,
        "plot_scope": "nine independent static plots; native original units; no trend/smoothing/aggregation; gaps preserved",
        "scientific_status": {
            "qa_imerg": "unassessed",
            "gldas_water_mask_lineage": "uncertain",
            "gate_r": "pending",
            "gate_t": "pending",
            "sites": "candidate_not_approved",
            "cell_assignments": "candidate_not_approved",
            "panel_spatial_equivalence": "not_established",
            "regional_aggregation_performed": False,
            "inferential_statistics_performed": False,
            "long_term_trend_performed": False,
            "anomaly_calculation_performed": False,
            "model_training_performed": False,
            "product_unit_conversion_performed": False,
            "raw_payloads_modified": False,
        },
        "limitations": [
            "The three equal projected-extent strips produce deterministic geometry-derived candidates, not scientifically approved or representative hydroclimate sites.",
            "Nearest-cell assignment uses EPSG:3577 Euclidean center distance; offsets are reported geodesically on WGS84. The datum/positional lineage of the authorized MDBA service geometry is still unresolved.",
            "Cell containment is inclusive on both bounds; overlap can return multiple cells and gaps can return none. No tie-break is silently applied.",
            "IMERG QA remains unassessed and no QA field filters observations; GLDAS mask/lineage uncertainty remains.",
            "Monthly labels coincide but product calendars, temporal averaging semantics, and native cell footprints are not claimed equivalent.",
            "This point experiment does not support a basin mean, co-located multivariable panel, inference, climatological trends, or predictive models.",
        ],
    }


def _csv_row(observation: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "site_id", "month", "decoded_value", "decoded_value_status", "stored_value", "stored_value_status", "stored_dtype",
        "unit_original", "granule_id", "producer_granule_id", "collection_id", "product_version", "payload_sha256",
        "source_manifest_sha256", "grid_cell_index_zero_based", "cell_center_lon_lat", "cell_bounds_lon_lat",
        "cell_bounds_method", "cell_assignment_rule", "site_to_center_geodesic_distance_m", "qa_status", "state",
    )
    row = {key: observation.get(key) for key in keys}
    for key in ("grid_cell_index_zero_based", "cell_center_lon_lat", "cell_bounds_lon_lat"):
        row[key] = json.dumps(row[key], ensure_ascii=False)
    return row


def write_outputs(result: dict[str, Any], manifest_path: Path, table_dir: Path, chart_dir: Path) -> dict[str, list[str]]:
    matplotlib.use("Agg", force=True)
    from matplotlib import pyplot as plt

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    table_dir.mkdir(parents=True, exist_ok=True)
    chart_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    table_files: list[str] = []
    chart_files: list[str] = []
    for site in result["sites"]:
        for product in PRODUCT_ORDER:
            observations = result["observations_by_site_and_product"][site["site_id"]][product]
            file_stem = f"{site['site_id']}_{product}_2005"
            table_path = table_dir / f"{file_stem}.csv"
            with table_path.open("w", encoding="utf-8-sig", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(_csv_row(observations[0]).keys()))
                writer.writeheader()
                writer.writerows(_csv_row(row) for row in observations)
            table_files.append(table_path.as_posix())
            values = [
                row["decoded_value"]
                if row["decoded_value_status"] in {"finite", "zero_valid", "negative_finite_review"}
                else np.nan
                for row in observations
            ]
            figure, axis = plt.subplots(figsize=(9, 4.8), constrained_layout=True)
            x = np.arange(1, len(MONTHS) + 1)
            axis.plot(x, values, marker="o", linewidth=1.2, color="#146C94", label="NASA original, decoded storage value")
            zero_indices = [index + 1 for index, row in enumerate(observations) if row["decoded_value_status"] == "zero_valid"]
            if zero_indices:
                axis.scatter(zero_indices, [0.0] * len(zero_indices), marker="s", s=48, color="#E07A5F", zorder=4, label="zero valid")
            for index, row in enumerate(observations):
                if row["decoded_value_status"] not in {"finite", "zero_valid", "negative_finite_review"}:
                    axis.axvspan(index + 0.82, index + 1.18, color="#D9D9D9", alpha=0.6, hatch="///", linewidth=0)
            variable = PRODUCT_VARIABLES[product][0]
            unit = PRODUCT_VARIABLES[product][1]
            axis.set_xticks(x, [month[5:] for month in MONTHS])
            axis.set_xlabel("Month in 2005")
            axis.set_ylabel(f"{variable} ({unit})")
            axis.set_title(
                f"{site['site_id']} · {product} · {variable}\n"
                "candidate_not_approved · QA unassessed · no trend or spatial aggregation\n"
                "NASA granules verified; synthetic fixtures are tests only",
                fontsize=10,
            )
            axis.grid(axis="y", alpha=0.25)
            if zero_indices:
                axis.legend(loc="best", fontsize=8)
            chart_path = chart_dir / f"{file_stem}.png"
            figure.savefig(chart_path, dpi=150)
            plt.close(figure)
            chart_files.append(chart_path.as_posix())
    return {"tables": table_files, "charts": chart_files}


def portable_output_names(outputs: dict[str, list[str]]) -> dict[str, list[str]]:
    """Strip local directories from output references before writing a manifest."""
    return {key: [Path(path).name for path in paths] for key, paths in outputs.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True)
    parser.add_argument("--boundary-geojson", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, default=Path("research/manifests/ful126-point-eda-2005.json"))
    parser.add_argument("--table-dir", type=Path, default=Path("research/results/ful126"))
    parser.add_argument("--chart-dir", type=Path, default=Path("research/figures/ful126"))
    args = parser.parse_args(argv)
    result = run_experiment(args.input_dir, args.boundary_geojson)
    outputs = write_outputs(result, args.manifest_output, args.table_dir, args.chart_dir)
    result["generated_outputs"] = portable_output_names(outputs)
    args.manifest_output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "inventory": result["inventory"],
                "candidate_sites": [{"site_id": site["site_id"], "longitude": site["longitude"], "latitude": site["latitude"]} for site in result["sites"]],
                "series_count": sum(len(rows) for site in result["observations_by_site_and_product"].values() for rows in site.values()),
                "table_count": len(outputs["tables"]),
                "chart_count": len(outputs["charts"]),
                "manifest": args.manifest_output.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
