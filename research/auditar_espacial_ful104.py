"""Audita geometría y sensibilidad de agregación en muestras NASA de FUL-104.

No calcula una serie temporal ni una máscara aprobada para producción. Los pesos
fraccionales usan celdas rectangulares transformadas por sus esquinas a EPSG:3577;
densificación y sensibilidad al datum se reportan como límites pendientes.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import zipfile
from pathlib import Path

import h5py
import netCDF4
import numpy as np
import shapefile
import shapely
from pyproj import Transformer
from shapely.geometry import shape
from shapely.ops import transform, unary_union

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/nasa/ful104"
MDBA_PATH = ROOT / "data/cache/ful-102/mdba_boundary_4326.geojson"
NSW_ZIP = ROOT / "data/cache/ful-102/nsw_boundary.zip"
WGS84_TO_AEA = Transformer.from_crs("EPSG:4326", "EPSG:3577", always_xy=True).transform
REQUIRED_SAMPLE_NAMES = (
    "MERRA2_300.tavgM_2d_slv_Nx.200501.nc4",
    "MERRA2_400.tavgM_2d_slv_Nx.202101.nc4",
    "3B-MO.MS.MRG.3IMERG.20050101-S000000-E235959.01.V07B.HDF5",
    "3B-MO.MS.MRG.3IMERG.20210101-S000000-E235959.01.V07B.HDF5",
    "GLDAS_NOAH025_M.A200501.021.nc4",
    "GLDAS_NOAH025_M.A202101.021.nc4",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_geometries(mdba_path: Path = MDBA_PATH, nsw_zip: Path = NSW_ZIP):
    gj = json.loads(mdba_path.read_text(encoding="utf-8"))
    basin = shape(gj["features"][0]["geometry"])
    with zipfile.ZipFile(nsw_zip) as archive:
        shp_name = next(n for n in archive.namelist() if n.endswith(".shp"))
        dbf_name = next(n for n in archive.namelist() if n.endswith(".dbf"))
        shp = shapefile.Reader(
            shp=io.BytesIO(archive.read(shp_name)),
            dbf=io.BytesIO(archive.read(dbf_name)),
        )
        names = [field[0] for field in shp.fields[1:]]
        state_i = names.index("STE_NAME26")
        states = [shape(record.__geo_interface__) for record, attrs in zip(shp.shapes(), shp.records()) if attrs[state_i] == "New South Wales"]
        nsw = unary_union(states)
    return basin, nsw


def valid_data_mask(values, fill):
    """Compara el fill usando la precisión del tipo numérico almacenado."""
    array = np.asarray(values)
    valid = np.isfinite(array)
    if fill is not None:
        fill_in_storage_dtype = np.asarray(fill, dtype=array.dtype).item()
        valid &= array != fill_in_storage_dtype
    return valid


def spatial_selection_masks(basin, cells, lon, lat):
    """Devuelve las celdas seleccionadas por centro y por intersección."""
    centers = shapely.covers(basin, shapely.points(lon, lat))
    intersects = shapely.intersects(cells, basin)
    return centers, intersects


def require_samples(data_dir: Path):
    missing = [name for name in REQUIRED_SAMPLE_NAMES if not (data_dir / name).is_file()]
    if missing:
        raise FileNotFoundError("Faltan muestras NASA obligatorias: " + ", ".join(missing))
    return [data_dir / name for name in REQUIRED_SAMPLE_NAMES]


def validate_results(results):
    failed = [result.get("file", "<desconocido>") for result in results if result.get("error")]
    processed = {result.get("file") for result in results if not result.get("error")}
    missing = [name for name in REQUIRED_SAMPLE_NAMES if name not in processed]
    if failed or missing:
        details = []
        if failed:
            details.append("fallaron: " + ", ".join(failed))
        if missing:
            details.append("no procesadas: " + ", ".join(missing))
        raise RuntimeError("Auditoría incompleta; " + "; ".join(details))


def read_sample(path: Path):
    if path.suffix.lower() == ".hdf5":
        with h5py.File(path, "r") as f:
            g = f["Grid"]
            qa = {}
            for name in ("randomError", "gaugeRelativeWeighting", "precipitationQualityIndex"):
                dataset = g[name]
                qa[name] = {
                    "values": dataset[0].T,
                    "fill": float(dataset.attrs["_FillValue"]) if "_FillValue" in dataset.attrs else None,
                }
            return {
                "dataset": "IMERG",
                "field": "Grid/precipitation",
                "values": g["precipitation"][0].T,
                "fill": float(g["precipitation"].attrs["_FillValue"]),
                "units": g["precipitation"].attrs["units"].decode(),
                "lon": g["lon"][:], "lat": g["lat"][:],
                "lon_bnds": g["lon_bnds"][:], "lat_bnds": g["lat_bnds"][:],
                "qa": qa,
            }
    # Abrir en memoria evita incompatibilidad con rutas Unicode de Windows y
    # permite que --data-dir apunte a cualquier checkout/directorio local.
    with path.open("rb") as stream:
        payload = stream.read()
    with netCDF4.Dataset("sample.nc4", mode="r", memory=payload) as ds:
        field = "T2M" if "T2M" in ds.variables else "SoilMoi0_10cm_inst"
        values = np.asarray(ds.variables[field][0])
        lon, lat = np.asarray(ds.variables["lon"][:]), np.asarray(ds.variables["lat"][:])
        return {
            "dataset": "MERRA-2" if field == "T2M" else "GLDAS",
            "field": field,
            "values": values,
            "fill": float(getattr(ds.variables[field], "_FillValue", np.nan)),
            "units": str(getattr(ds.variables[field], "units", "")),
            "lon": lon, "lat": lat,
            "lon_bnds": None, "lat_bnds": None,
            "qa": {},
        }


def bounds_1d(values, declared, fallback_step):
    if declared is not None:
        return declared
    step = float(np.median(np.diff(values)))
    if not np.isfinite(step) or abs(step) == 0:
        step = fallback_step
    half = abs(step) / 2
    return np.column_stack((values - half, values + half))


def audit_one(path: Path, basin):
    sample = read_sample(path)
    values = sample["values"]
    lon, lat = sample["lon"], sample["lat"]
    lons = sample["lon_bnds"]
    lats = sample["lat_bnds"]
    if lons is None:
        step_lon = 360 / len(lon) if sample["dataset"] == "GLDAS" else (0.625 if sample["dataset"] == "MERRA-2" else 0.25)
        step_lat = 180 / (len(lat) - 1) if sample["dataset"] == "MERRA-2" else (0.25)
        lons, lats = bounds_1d(lon, None, step_lon), bounds_1d(lat, None, step_lat)
    basin_p = transform(WGS84_TO_AEA, basin)
    minx, miny, maxx, maxy = basin.bounds
    ix = np.flatnonzero((lon >= minx - 1) & (lon <= maxx + 1))
    iy = np.flatnonzero((lat >= miny - 1) & (lat <= maxy + 1))
    ii, jj = np.meshgrid(ix, iy)
    i_flat, j_flat = ii.ravel(), jj.ravel()
    lon0, lon1 = np.minimum(lons[i_flat, 0], lons[i_flat, 1]), np.maximum(lons[i_flat, 0], lons[i_flat, 1])
    lat0, lat1 = np.minimum(lats[j_flat, 0], lats[j_flat, 1]), np.maximum(lats[j_flat, 0], lats[j_flat, 1])
    cells = shapely.box(lon0, lat0, lon1, lat1)
    keep = shapely.intersects(cells, basin)
    cells, i_flat, j_flat = cells[keep], i_flat[keep], j_flat[keep]
    projected = shapely.transform(cells, lambda c: np.column_stack(WGS84_TO_AEA(c[:, 0], c[:, 1])))
    overlays = shapely.intersection(projected, basin_p)
    areas_all = shapely.area(overlays)
    positive = areas_all > 0
    areas, full = areas_all[positive], shapely.area(projected)[positive]
    i_flat, j_flat = i_flat[positive], j_flat[positive]
    vals = values[j_flat, i_flat].astype(float)
    valid = np.isfinite(vals) & (vals != sample["fill"])
    center, _ = spatial_selection_masks(basin, cells, lon[i_flat], lat[j_flat])
    n_cells = len(areas)
    def summary(selection, weights):
        take = selection & valid
        if not take.any():
            return {"cells": int(selection.sum()), "valid": 0, "mean": None}
        return {"cells": int(selection.sum()), "valid": int(take.sum()), "coverage_pct": float(100 * take.sum() / max(1, selection.sum())), "weighted_mean": float(np.average(vals[take], weights=weights[take]))}
    qa_report = {}
    for key, qa in sample["qa"].items():
        qfield = qa["values"]
        qvals = qfield[j_flat, i_flat]
        qvalid = valid_data_mask(qvals, qa["fill"])
        qvals = qvals.astype(float)
        qa_report[key] = {"valid_basin_cells": int(qvalid.sum()), "min": float(qvals[qvalid].min()) if qvalid.any() else None, "max": float(qvals[qvalid].max()) if qvalid.any() else None}
    return {
        "file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
        "dataset": sample["dataset"], "field": sample["field"], "units": sample["units"],
        "grid_shape_lat_lon": list(values.shape), "basin_intersecting_cells": n_cells,
        "basin_area_km2_from_overlay": basin_p.area / 1e6,
        "center_equal_weight": summary(center, np.ones(n_cells)),
        "intersect_fraction_area_weighted": summary(np.ones(n_cells, dtype=bool), areas),
        "whole_cell_area_weighted_for_intersecting_cells": summary(np.ones(n_cells, dtype=bool), full),
        "area_coverage_by_valid_data_pct": float(100 * areas[valid].sum() / areas.sum()) if areas.sum() else None,
        "qa_bbox_or_basin_ranges_and_counts": qa_report,
        "limitations": ["Muestra mensual; no valida la serie completa.", "Celdas rectangulares se proyectan por esquinas sin densificación.", "No se aplican filtros QA científicos ni una regla de faltantes aprobada.", "MERRA-2 y GLDAS bounds se infieren de coordenadas y resolución nominal cuando el archivo no declara bounds."],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA, help="Directorio con las seis muestras NASA obligatorias")
    parser.add_argument("--mdba-geojson", type=Path, default=MDBA_PATH, help="GeoJSON MDBA completo")
    parser.add_argument("--nsw-zip", type=Path, default=NSW_ZIP, help="ZIP ABS del shapefile estatal")
    parser.add_argument("--output", type=Path, default=ROOT / "data/cache/ful104/spatial_audit.json")
    args = parser.parse_args()
    files = require_samples(args.data_dir)
    basin, nsw = load_geometries(args.mdba_geojson, args.nsw_zip)
    basin_p, nsw_p = transform(WGS84_TO_AEA, basin), transform(WGS84_TO_AEA, nsw)
    overlap = basin_p.intersection(nsw_p)
    results = []
    for path in files:
        try:
            results.append(audit_one(path, basin))
        except Exception as exc:  # noqa: BLE001 - se registra por archivo y el proceso termina con error al final
            results.append({"file": path.name, "error": f"{type(exc).__name__}: {exc}"})
    report = {
        "generated_utc": "2026-11-15",
        "method": {"basin_crs": "EPSG:4326 ArcGIS export", "nsw_crs": "EPSG:7844 ABS ASGS 2026", "analysis_crs": "EPSG:3577 GDA94 Australian Albers", "area_method": "projected cell-box intersection; no edge densification"},
        "nsw_basin_overlap": {"intersection_km2": overlap.area / 1e6, "pct_nsw": overlap.area / nsw_p.area * 100, "pct_basin": overlap.area / basin_p.area * 100, "geometries_valid": {"basin": basin_p.is_valid, "nsw": nsw_p.is_valid, "intersection": overlap.is_valid}},
        "samples": results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "nsw_basin_overlap": report["nsw_basin_overlap"], "samples": [{"file": x["file"], "dataset": x.get("dataset"), "error": x.get("error"), "center": x.get("center_equal_weight"), "fractional": x.get("intersect_fraction_area_weighted"), "valid_area_pct": x.get("area_coverage_by_valid_data_pct")} for x in results]}, indent=2))
    validate_results(results)


if __name__ == "__main__":
    main()
