"""Report float32 IMERG cell-bound continuity without altering any coordinates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from research.build_ful116_snapshot import DEFAULT_INPUT, _header, sha256_file


def interval_diagnostics(centers: np.ndarray, bounds: np.ndarray) -> dict[str, Any]:
    centers = np.asarray(centers)
    bounds = np.asarray(bounds)
    if centers.ndim != 1 or bounds.shape != (centers.size, 2) or centers.size < 2:
        raise ValueError("Se requiere un eje 1D con bounds n×2")
    numeric = centers.astype(np.float64)
    edges = bounds.astype(np.float64)
    low = np.minimum(edges[:, 0], edges[:, 1])
    high = np.maximum(edges[:, 0], edges[:, 1])
    gap = low[1:] - high[:-1]
    step = float(np.median(np.diff(numeric)))
    midpoint = (numeric[:-1] + numeric[1:]) / 2
    ideal_edges = np.concatenate(
        ([numeric[0] - (midpoint[0] - numeric[0])], midpoint, [numeric[-1] + (numeric[-1] - midpoint[-1])])
    )
    ideal_low, ideal_high = ideal_edges[:-1], ideal_edges[1:]
    edge_deviation = np.maximum(np.abs(low - ideal_low), np.abs(high - ideal_high))
    return {
        "center_dtype": str(centers.dtype),
        "bound_dtype": str(bounds.dtype),
        "cell_count": int(centers.size),
        "grid_extent": [float(low.min()), float(high.max())],
        "median_center_step": step,
        "interval_width_min_max": [float((high - low).min()), float((high - low).max())],
        "center_outside_own_bounds": int(((numeric < low) | (numeric > high)).sum()),
        "adjacent_exact_continuities": int((gap == 0).sum()),
        "adjacent_gaps": int((gap > 0).sum()),
        "adjacent_overlaps": int((gap < 0).sum()),
        "max_gap_degrees": float(max(0.0, float(gap.max()))),
        "max_overlap_degrees": float(max(0.0, float(-gap.min()))),
        "total_gap_degrees": float(gap[gap > 0].sum()),
        "total_overlap_degrees": float(-gap[gap < 0].sum()),
        "cells_differing_from_contiguous_midpoint_edges": int((edge_deviation > 0).sum()),
        "max_bound_deviation_from_contiguous_midpoint_edges_degrees": float(edge_deviation.max()),
        "interpretation": (
            "Diagnostic only: float32 bounds contain gaps/overlaps relative to adjacent cells; "
            "midpoint bounds are a comparison baseline, not an adopted replacement."
        ),
    }


def audit_file(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with h5py.File(path, "r") as source:
        grid = source["Grid"]
        header = _header(grid.attrs.get("FileHeader", source.attrs.get("FileHeader")))
        return {
            "file": path.name,
            "sha256": sha256_file(path),
            "period": header.get("StartGranuleDateTime", "")[:7] or None,
            "collection_id": "C2723754851-GES_DISC",
            "product_version": "V07B",
            "variable_path": "Grid/precipitation",
            "method": "adjacent declared lon_bnds/lat_bnds intervals, analyzed in float64; no rounding, repair, overlay, or reprojection",
            "longitude": interval_diagnostics(grid["lon"][...], grid["lon_bnds"][...]),
            "latitude": interval_diagnostics(grid["lat"][...], grid["lat_bnds"][...]),
            "conclusion": (
                "The source bounds are not a perfectly continuous partition. This is a plausible "
                "contributor to area-sum excess, but these diagnostics alone do not attribute all "
                "48.38 km² in FUL-111 to one cause or validate an alternative spatial method."
            ),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT / "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_file(args.input)
    serialized = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
