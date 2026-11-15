"""Offline candidate diagnostics for the first NASA 2005 spatial-support trial.

All point supports and area calculations are exploratory. Nothing here creates
a regional series, changes NASA payloads, applies QA, or approves Gate R/T.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import shapely
from pyproj import Geod, Transformer

from research.ful122_inventory import PRODUCTS, inventory
from research.ful124_spatial_audit import (
    AREA_CRS,
    EXPECTED_MDBA_SHA256,
    PRODUCT_VARIABLES,
    SOURCE_CRS,
    SpatialAuditError,
    _axis_bounds,
    _bbox_indices,
    _cell_polygon,
    _coord_digest,
    _read_grid,
    load_boundary,
    sha256_file,
)

SEAM_TOLERANCES_DEGREES = (0.0, 1e-6, 1e-5, 2e-5)
SEGMENT_LENGTHS_DEGREES = (0.05, 0.02, 0.01)
AREA_PROJECTIONS = ("EPSG:3577", "EPSG:6933")
POINT_TRIAL_STATUS = "candidate_not_approved"


def seam_summary(bounds: np.ndarray, tolerance_degrees: float) -> dict[str, Any]:
    """Count 1D adjacent interval gaps/overlaps and the axis cells they touch."""
    if tolerance_degrees < 0:
        raise ValueError("seam tolerance must be nonnegative")
    ordered = np.sort(np.asarray(bounds, dtype=np.float64), axis=1)
    if ordered.ndim != 2 or ordered.shape[1] != 2 or not np.isfinite(ordered).all():
        raise SpatialAuditError("bounds must be finite pairs")
    seam = ordered[1:, 0] - ordered[:-1, 1]
    gap_indices = np.flatnonzero(seam > tolerance_degrees)
    overlap_indices = np.flatnonzero(seam < -tolerance_degrees)

    def touched_cells(indices: np.ndarray) -> int:
        return int(np.unique(np.concatenate((indices, indices + 1))).size) if len(indices) else 0

    gaps = seam[gap_indices]
    overlaps = -seam[overlap_indices]
    return {
        "adjacent_gaps": len(gaps),
        "adjacent_overlaps": len(overlaps),
        "axis_cells_adjacent_to_gaps": touched_cells(gap_indices),
        "axis_cells_adjacent_to_overlaps": touched_cells(overlap_indices),
        "maximum_gap_degrees": float(gaps.max()) if len(gaps) else 0.0,
        "maximum_overlap_degrees": float(overlaps.max()) if len(overlaps) else 0.0,
        "total_gap_degrees": float(gaps.sum()) if len(gaps) else 0.0,
        "total_overlap_degrees": float(overlaps.sum()) if len(overlaps) else 0.0,
        "tolerance_degrees": float(tolerance_degrees),
        "interpretation": "1D axis intervals; counts are not unique 2D grid cells",
    }


def imerg_bounds_candidates(grid: dict[str, Any]) -> dict[str, dict[str, np.ndarray]]:
    """Return native bounds and a separate center-midpoint candidate."""
    native = {
        "latitude": np.asarray(grid["lat_bounds"], dtype=np.float64).copy(),
        "longitude": np.asarray(grid["lon_bounds"], dtype=np.float64).copy(),
    }
    midpoint = {
        "latitude": _axis_bounds(grid["lat"], None),
        "longitude": _axis_bounds(grid["lon"], None),
    }
    if _coord_digest(grid["lat"], grid["lon"], native["latitude"], native["longitude"]) == _coord_digest(
        grid["lat"], grid["lon"], midpoint["latitude"], midpoint["longitude"]
    ):
        raise SpatialAuditError("native and derived IMERG bounds unexpectedly have identical hashes")
    return {"native_float32_bounds": native, "center_midpoint_bounds": midpoint}


def _projected_area_diagnostic(
    grid: dict[str, Any],
    bounds: dict[str, np.ndarray],
    geometry: Any,
    projection: str,
    segment_length_degrees: float,
) -> dict[str, Any]:
    """Recompute an explicit cell/polygon overlay for one diagnostic setting."""
    transformer = Transformer.from_crs(SOURCE_CRS, projection, always_xy=True)
    transformer.transform(140.0, -35.0)  # Resolve the operation metadata before recording it.
    segmented_boundary = shapely.segmentize(geometry, segment_length_degrees)
    projected_boundary = shapely.transform(segmented_boundary, transformer.transform, interleaved=False)
    shapely.prepare(projected_boundary)
    west, south, east, north = geometry.bounds
    lat, lon = grid["lat"], grid["lon"]
    j0, j1 = _bbox_indices(lat, south - 1.0, north + 1.0)
    i0, i1 = _bbox_indices(lon, west - 1.0, east + 1.0)
    cells = np.asarray(
        [
            _cell_polygon(bounds["longitude"][i], bounds["latitude"][j])
            for j in range(j0, j1)
            for i in range(i0, i1)
        ],
        dtype=object,
    )
    cells = cells[shapely.intersects(cells, geometry)]
    segmented_cells = shapely.segmentize(cells, segment_length_degrees)
    projected_cells = shapely.transform(segmented_cells, transformer.transform, interleaved=False)
    cell_areas = shapely.area(projected_cells)
    fully_covered = shapely.covers(projected_boundary, projected_cells)
    overlap_areas = np.zeros_like(cell_areas)
    overlap_areas[fully_covered] = cell_areas[fully_covered]
    partial_candidates = np.flatnonzero(~fully_covered)
    if len(partial_candidates):
        intersections_geom = shapely.intersection(projected_cells[partial_candidates], projected_boundary)
        overlap_areas[partial_candidates] = shapely.area(intersections_geom)
    positive = overlap_areas > 0
    cell_areas = cell_areas[positive]
    overlap_areas = overlap_areas[positive]
    fractions = np.divide(overlap_areas, cell_areas, out=np.zeros_like(overlap_areas), where=cell_areas > 0)
    fractions = np.clip(fractions, 0.0, 1.0)
    partial_fractions = fractions[fractions < 1.0 - 1e-8]
    intersections = len(overlap_areas)
    partials = len(partial_fractions)
    area_sum_m2 = float(overlap_areas.sum())
    boundary_area_m2 = float(projected_boundary.area)
    delta_km2 = (area_sum_m2 - boundary_area_m2) / 1e6
    return {
        "projection": projection,
        "operation_description": transformer.description,
        "declared_operation_accuracy_m": transformer.accuracy if transformer.accuracy >= 0 else None,
        "operation_pinned": False,
        "max_segment_length_degrees": segment_length_degrees,
        "positive_intersection_cells": intersections,
        "partial_cells_fraction_lt_1_minus_1e-8": partials,
        "partial_fraction_min": float(partial_fractions.min()) if len(partial_fractions) else None,
        "partial_fraction_max": float(partial_fractions.max()) if len(partial_fractions) else None,
        "sum_intersection_area_km2": area_sum_m2 / 1e6,
        "projected_boundary_area_km2": boundary_area_m2 / 1e6,
        "closure_delta_km2": delta_km2,
        "closure_delta_percent_of_projected_boundary": delta_km2 / (boundary_area_m2 / 1e6) * 100,
        "interpretation": "diagnostic planar overlay; not an official basin area or approved denominator",
    }


def _point_support_trial(geometry: Any, grids: dict[str, dict[str, Any]], hashes: dict[str, str]) -> dict[str, Any]:
    """Snap one geometry-derived illustrative point independently to each grid."""
    site = geometry.representative_point()
    site_lon, site_lat = float(site.x), float(site.y)
    transformer = Transformer.from_crs(SOURCE_CRS, AREA_CRS, always_xy=True)
    transformer.transform(site_lon, site_lat)
    geod = Geod(ellps="WGS84")
    snapped: dict[str, dict[str, Any]] = {}
    for product, grid in grids.items():
        lat, lon = grid["lat"], grid["lon"]
        west, south, east, north = geometry.bounds
        j0, j1 = _bbox_indices(lat, south - 1.0, north + 1.0)
        i0, i1 = _bbox_indices(lon, west - 1.0, east + 1.0)
        lon_part, lat_part = lon[i0:i1], lat[j0:j1]
        xx, yy = np.meshgrid(lon_part, lat_part)
        projected_x, projected_y = transformer.transform(xx, yy)
        site_x, site_y = transformer.transform(site_lon, site_lat)
        squared_distance = (projected_x - site_x) ** 2 + (projected_y - site_y) ** 2
        local_j, local_i = np.unravel_index(int(np.argmin(squared_distance)), squared_distance.shape)
        j, i = j0 + int(local_j), i0 + int(local_i)
        center_lon, center_lat = float(lon[i]), float(lat[j])
        _, _, offset_m = geod.inv(site_lon, site_lat, center_lon, center_lat)
        cell = _cell_polygon(grid["lon_bounds"][i], grid["lat_bounds"][j])
        projected_cell = shapely.transform(
            shapely.segmentize(cell, 0.02), transformer.transform, interleaved=False
        )
        snapped[product] = {
            "status": POINT_TRIAL_STATUS,
            "product": product,
            "variable": PRODUCT_VARIABLES[product][0],
            "unit": PRODUCT_VARIABLES[product][1],
            "reference_payload_sha256": hashes[product],
            "grid_cell_index_zero_based": {"row_latitude": j, "column_longitude": i},
            "cell_center_lon_lat": [center_lon, center_lat],
            "cell_bounds_lon_lat": [
                float(np.min(grid["lon_bounds"][i])),
                float(np.min(grid["lat_bounds"][j])),
                float(np.max(grid["lon_bounds"][i])),
                float(np.max(grid["lat_bounds"][j])),
            ],
            "cell_bounds_method": grid["info"]["bounds_method"],
            "center_offset_from_candidate_site_m": float(offset_m),
            "projected_cell_footprint_area_km2_diagnostic": float(projected_cell.area / 1e6),
            "nominal_resolution_degrees_lat_lon": grid["info"]["nominal_cell_size_degrees_lat_lon"],
        }
    pairwise: dict[str, float] = {}
    products = list(snapped)
    for index, first in enumerate(products):
        for second in products[index + 1 :]:
            a = snapped[first]["cell_center_lon_lat"]
            b = snapped[second]["cell_center_lon_lat"]
            _, _, separation_m = geod.inv(a[0], a[1], b[0], b[1])
            pairwise[f"{first}_to_{second}_snapped_center_distance_m"] = float(separation_m)
    return {
        "status": POINT_TRIAL_STATUS,
        "site_selection_rule": "Shapely representative_point of the unapproved exploratory MDBA polygon; chosen only as a reproducible diagnostic location, not a recommended scientific site",
        "candidate_site_lon_lat": [site_lon, site_lat],
        "candidate_site_inside_exploratory_polygon": bool(geometry.covers(site)),
        "products": snapped,
        "pairwise_snapped_center_distances_m": pairwise,
        "interpretation": "each product retains a distinct native cell; nearest centers do not imply equivalent footprints or a co-located observation",
    }


def run_experiment(input_dirs: list[Path], boundary_path: Path) -> dict[str, Any]:
    geometry, boundary_info = load_boundary(boundary_path, EXPECTED_MDBA_SHA256)
    inventory_report = inventory(input_dirs)
    target_months = {f"2005-{month:02d}" for month in range(1, 13)}
    records_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in inventory_report["records"]:
        if row.get("eligible") and row.get("period") in target_months:
            records_by_product[row["product_key"]].append(row)
    if set(records_by_product) != set(PRODUCTS) or any(len(rows) != 12 for rows in records_by_product.values()):
        raise SpatialAuditError("expected 12 eligible, manifest-verified months per NASA product")

    grids: dict[str, dict[str, Any]] = {}
    for product, rows in records_by_product.items():
        rows.sort(key=lambda row: row["period"])
        first = _read_grid(Path(rows[0]["path"]), product)
        for row in rows[1:]:
            current = _read_grid(Path(row["path"]), product)
            if current["info"]["coordinates_sha256"] != first["info"]["coordinates_sha256"]:
                raise SpatialAuditError(f"{product} grid coordinates/bounds differ between months")
        grids[product] = first

    imerg = grids["imerg_final"]
    candidates = imerg_bounds_candidates(imerg)
    bounds_method_results: dict[str, Any] = {}
    bbox = geometry.bounds
    j0, j1 = _bbox_indices(imerg["lat"], bbox[1], bbox[3])
    i0, i1 = _bbox_indices(imerg["lon"], bbox[0], bbox[2])
    tolerance_sensitivity: dict[str, Any] = {}
    for method, axes in candidates.items():
        lat_local = axes["latitude"][max(0, j0 - 1) : min(len(imerg["lat"]), j1 + 1)]
        lon_local = axes["longitude"][max(0, i0 - 1) : min(len(imerg["lon"]), i1 + 1)]
        tolerance_sensitivity[method] = {
            "latitude": [seam_summary(lat_local, tolerance) for tolerance in SEAM_TOLERANCES_DEGREES],
            "longitude": [seam_summary(lon_local, tolerance) for tolerance in SEAM_TOLERANCES_DEGREES],
            "scope": "axis bounds intersecting the MDBA bbox plus the immediately adjacent center on each side",
        }
        method_areas = []
        for projection in AREA_PROJECTIONS:
            for segment_length in SEGMENT_LENGTHS_DEGREES:
                method_areas.append(
                    _projected_area_diagnostic(
                        imerg,
                        axes,
                        geometry,
                        projection,
                        segment_length,
                    )
                )
        bounds_method_results[method] = {
            "bounds_definition": (
                "native HDF5 lat_bnds/lon_bnds; stored as float32 in the NASA payload"
                if method == "native_float32_bounds"
                else "derived bounds are midpoints of adjacent stored float32 centers, calculated in float64; end edges use half the adjacent center spacing"
            ),
            "bounds_sha256": _coord_digest(imerg["lat"], imerg["lon"], axes["latitude"], axes["longitude"]),
            "area_sensitivity": method_areas,
            "state": "candidate_not_approved",
        }

    native_by_setting = {
        (row["projection"], row["max_segment_length_degrees"]): row
        for row in bounds_method_results["native_float32_bounds"]["area_sensitivity"]
    }
    derived_by_setting = {
        (row["projection"], row["max_segment_length_degrees"]): row
        for row in bounds_method_results["center_midpoint_bounds"]["area_sensitivity"]
    }
    for setting, native_row in native_by_setting.items():
        derived_row = derived_by_setting[setting]
        native_area = native_row["sum_intersection_area_km2"]
        derived_area = derived_row["sum_intersection_area_km2"]
        native_row["signed_area_difference_vs_center_midpoint_km2"] = native_area - derived_area
        native_row["absolute_area_difference_vs_center_midpoint_km2"] = abs(native_area - derived_area)
        native_row["relative_area_difference_vs_center_midpoint_percent"] = (
            (native_area - derived_area) / derived_area * 100
        )
        derived_row["signed_area_difference_vs_native_bounds_km2"] = derived_area - native_area
        derived_row["absolute_area_difference_vs_native_bounds_km2"] = abs(derived_area - native_area)
        derived_row["relative_area_difference_vs_native_bounds_percent"] = (
            (derived_area - native_area) / native_area * 100
        )

    reference_transformer = Transformer.from_crs(SOURCE_CRS, AREA_CRS, always_xy=True)
    reference_transformer.transform(140.0, -35.0)
    monthly_records = []
    first_month_hashes: dict[str, str] = {}
    for product, rows in records_by_product.items():
        for row in rows:
            manifest_path = Path(row["manifest"])
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if row["period"] == "2005-01":
                first_month_hashes[product] = row["sha256"]
            monthly_records.append(
                {
                    "product": product,
                    "month": row["period"],
                    "granule_id": manifest.get("granule_id"),
                    "producer_granule_id": manifest.get("producer_granule_id"),
                    "collection_id": manifest.get("collection_id"),
                    "version": manifest.get("product", {}).get("version"),
                    "variable": manifest.get("product", {}).get("variable"),
                    "unit": manifest.get("product", {}).get("unit"),
                    "payload_sha256": row["sha256"],
                    "payload_bytes": row["bytes"],
                    "source_manifest_sha256": sha256_file(manifest_path),
                    "spatial_support_status": POINT_TRIAL_STATUS,
                    "qa_status": "unassessed; no QA filter applied",
                }
            )
    monthly_records.sort(key=lambda item: (item["product"], item["month"]))

    return {
        "schema_version": 1,
        "status": "diagnostic_only_not_approved",
        "generated_by": "research.ful125_support_experiment",
        "year": 2005,
        "inventory": {
            "eligible_months_by_product": inventory_report["counts"],
            "eligible_product_month_records": sum(inventory_report["counts"].values()),
            "rejected_candidates": inventory_report["rejected_count"],
            "triple_overlap_months": [row["period"] for row in inventory_report["matrix"] if row["triple_overlap"]],
        },
        "boundary": boundary_info,
        "boundary_recommendation_for_cesar": "approve_specific_artifact_for_test",
        "boundary_recommendation_rationale": "The live MDBA FeatureServer GeoJSON query at outSR=4326 returned a byte-identical 477805-byte artifact on 2026-11-15; this establishes an exactly reproducible export of this artifact, not the source datum/positional accuracy or approval as a statistical region.",
        "official_export_reproduction": {
            "checked_utc_date": "2026-11-15",
            "verification_mode": "manual read-only HTTP check; not performed by the offline manifest generator",
            "request": "FeatureServer/0/query?where=1%3D1&outFields=%2A&returnGeometry=true&outSR=4326&f=geojson",
            "live_response_sha256": boundary_info["artifact_sha256"],
            "live_response_bytes": boundary_info["artifact_bytes"],
            "byte_identical_to_local_artifact": True,
            "query_url_template": "https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/boundary_gdb/FeatureServer/0/query",
            "catalogue_url": "https://library.mdba.gov.au/data_product/https-mdba-maps-arcgis-com-home-item-html-id-ba731d77d80947fbbcbf7524364372ff-overview",
            "original_dataset_guide_url": "https://www.ga.gov.au/bigobj/GA3352.pdf",
            "reproduction_note": "A future live query may change; compare both response bytes and geometry before replacing the pinned artifact.",
        },
        "imerg_bounds_sensitivity": {
            "candidate_methods": bounds_method_results,
            "seam_tolerance_sensitivity": tolerance_sensitivity,
            "native_bounds_storage_dtype": "float32 as declared by the HDF5 payload; cast to float64 only for computation",
            "segment_lengths_degrees": list(SEGMENT_LENGTHS_DEGREES),
            "projection_candidates": list(AREA_PROJECTIONS),
            "causal_attribution": "The change in seam counts and closure across alternatives quantifies sensitivity; it does not uniquely attribute the DS-07 discrepancy to one cause.",
        },
        "monthly_payload_records": monthly_records,
        "point_support_trial": _point_support_trial(geometry, grids, first_month_hashes),
        "gate_status": {"gate_r": "pending", "gate_t": "pending", "qa_imerg": "unassessed", "gldas_mask_lineage": "uncertain"},
        "regional_aggregation_performed": False,
        "inferential_statistics_performed": False,
        "model_training_performed": False,
        "raw_payloads_modified": False,
        "limitations": [
            "Only the current exploratory MDBA legal-boundary artifact was checked; the 1997 hydrologic source data itself was not downloaded or substituted.",
            "Byte-identical live export proves an export recipe can reproduce this cached artifact on the check date, not its datum lineage, positional accuracy, or scientific suitability.",
            "The area calculation depends on geometry edges treated as straight in lon/lat between vertices, segmentization, projection operation, and cell-edge convention.",
            "Derived midpoint bounds are a sensitivity candidate based on float32 centers and are not asserted to be more correct than native bounds.",
            "The point location is generated from a representative point of the unapproved polygon solely to make the diagnostic deterministic; César must select any scientific sites.",
            "Distinct cells, units, temporal definitions, IMERG QA, GLDAS mask lineage, Gate R, and Gate T remain unresolved.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True)
    parser.add_argument("--boundary-geojson", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run_experiment(args.input_dir, args.boundary_geojson)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": result["status"],
                "inventory": result["inventory"],
                "boundary_sha256": result["boundary"]["artifact_sha256"],
                "imerg_methods": list(result["imerg_bounds_sensitivity"]["candidate_methods"]),
                "point_trial_status": result["point_support_trial"]["status"],
                "output": args.output.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
