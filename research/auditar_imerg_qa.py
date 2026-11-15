"""Inventory IMERG HDF5 provenance, structure, and QA field metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import h5py
import numpy as np

from research.ful105_imerg import CenterMaskCache

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NASA_DIR = ROOT / "data/raw/nasa/ful104"
DEFAULT_NCAR_DIR = ROOT / "data/cache/ful-102"
DEFAULT_OUTPUT = ROOT / "data/cache/ful112/imerg_qa_inventory.json"
QA_FIELDS = (
    "precipitationQualityIndex",
    "randomError",
    "gaugeRelativeWeighting",
)
FIELDS = ("precipitation", *QA_FIELDS)
NASA_NAME = re.compile(
    r"^3B-MO\.MS\.MRG\.3IMERG\.(?P<year>\d{4})(?P<month>\d{2})01-"
    r"S000000-E235959\.(?P<suffix_month>\d{2})\.V(?P<version>\d{2}[A-Z])\.HDF5$"
)
NCAR_NAME = re.compile(r"^imerg_(?P<year>\d{4})(?P<month>\d{2})_v(?P<version>\d{2}[a-z])_ncar\.h5$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if hasattr(value, "tolist"):
        return _json_value(value.tolist())
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _attrs(dataset) -> dict:
    return {
        str(key): _json_value(value)
        for key, value in dataset.attrs.items()
        if key not in {"DIMENSION_LIST", "REFERENCE_LIST"}
    }


def _header_fields(value) -> dict[str, str]:
    if not value:
        return {}
    value = _json_value(value)
    return {
        key.strip(): field.strip().rstrip(";").strip()
        for line in str(value).splitlines()
        if "=" in line
        for key, field in (line.split("=", 1),)
    }


def _period_and_version(path: Path, source: str) -> tuple[str, str]:
    pattern = NASA_NAME if source == "NASA" else NCAR_NAME
    match = pattern.fullmatch(path.name)
    if match is None:
        raise ValueError(f"Nombre de archivo {source} inesperado: {path.name}")
    values = match.groupdict()
    month = int(values["month"])
    if month < 1 or month > 12:
        raise ValueError(f"Mes inválido en nombre de archivo: {path.name}")
    version = values["version"].upper()
    if source == "NASA" and values["suffix_month"] != values["month"]:
        raise ValueError(f"Mes del nombre y sufijo no coinciden: {path.name}")
    if version != "07B":
        raise ValueError(f"Versión de archivo inesperada en {path.name}: {version}")
    return f"{values['year']}-{month:02d}", version


def _inspect_dataset(group, name: str) -> dict:
    if name not in group:
        return {"present": False}
    dataset = group[name]
    attributes = _attrs(dataset)
    return {
        "present": True,
        "path": f"Grid/{name}",
        "shape": list(dataset.shape),
        "dtype": str(dataset.dtype),
        "attributes": attributes,
        "not_declared_attributes": [
            key
            for key in ("units", "Units", "_FillValue", "CodeMissingValue", "scale_factor", "add_offset")
            if key not in attributes
        ],
    }


def inspect_file(path: Path, source: str) -> dict:
    period, version = _period_and_version(path, source)
    result = {
        "source_label": source,
        "file": path.name,
        "period": period,
        "file_version": f"V{version}",
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "groups": [],
        "global_attributes": {},
        "declared_granule": {},
        "fields": {},
        "coordinates": {},
        "issues": [],
    }
    with h5py.File(path, "r") as handle:
        result["groups"] = sorted(name for name, obj in handle.items() if isinstance(obj, h5py.Group))
        result["global_attributes"] = _attrs(handle)
        header = _header_fields(handle.attrs.get("FileHeader"))
        declared_filename = header.get("FileName")
        if not declared_filename:
            raise ValueError(f"FileHeader no declara FileName: {path.name}")
        declared_match = NASA_NAME.fullmatch(declared_filename)
        if declared_match is None:
            raise ValueError(f"FileHeader contiene un FileName IMERG inesperado: {declared_filename}")
        declared_period = f"{declared_match['year']}-{declared_match['month']}"
        if (
            declared_period != period
            or declared_match["version"] != version
            or declared_match["suffix_month"] != declared_match["month"]
        ):
            raise ValueError(
                f"Periodo/versión del archivo no coincide con FileHeader: {path.name} / {declared_filename}"
            )
        result["declared_granule"] = {
            key: header.get(key)
            for key in ("FileName", "DOI", "DOIshortName", "AlgorithmID", "AlgorithmVersion", "ProductVersion")
            if header.get(key) is not None
        }
        if header.get("DOIshortName") != "3IMERGM" or header.get("AlgorithmID") != "3IMERGM":
            raise ValueError(f"FileHeader no identifica IMERG mensual: {path.name}")
        if header.get("ProductVersion") not in {None, f"V{version}"}:
            raise ValueError(f"ProductVersion no coincide con el nombre del archivo: {path.name}")
        if "Grid" not in handle or not isinstance(handle["Grid"], h5py.Group):
            raise ValueError(f"Falta grupo Grid: {path.name}")
        grid = handle["Grid"]
        result["grid_attributes"] = _attrs(grid)
        result["fields"] = {name: _inspect_dataset(grid, name) for name in FIELDS}

        precipitation = grid.get("precipitation")
        if precipitation is None:
            raise ValueError(f"Falta Grid/precipitation: {path.name}")
        if len(precipitation.shape) != 3:
            raise ValueError(f"Grid/precipitation debe tener 3 dimensiones: {path.name}")
        dimensions = precipitation.attrs.get("DimensionNames")
        dimensions = _json_value(dimensions)
        if dimensions != "time,lon,lat":
            raise ValueError(f"DimensionNames de precipitation inesperado: {dimensions!r}: {path.name}")
        units = precipitation.attrs.get("units", precipitation.attrs.get("Units"))
        units = _json_value(units)
        if units != "mm/hr":
            raise ValueError(f"Unidad de precipitation inesperada: {units!r}: {path.name}")

        result["coordinates"] = {
            name: _inspect_dataset(grid, name)
            for name in ("time", "time_bnds", "lon", "lat", "lon_bnds", "lat_bnds")
        }
        expected_shapes = {
            "time": (precipitation.shape[0],),
            "time_bnds": (precipitation.shape[0], 2),
            "lon": (precipitation.shape[1],),
            "lat": (precipitation.shape[2],),
            "lon_bnds": (precipitation.shape[1], 2),
            "lat_bnds": (precipitation.shape[2], 2),
        }
        for name, expected in expected_shapes.items():
            dataset = grid.get(name)
            if dataset is None:
                raise ValueError(f"Falta Grid/{name}: {path.name}")
            if dataset.shape != expected:
                raise ValueError(
                    f"Grid/{name} tiene shape {dataset.shape}, se esperaba {expected}: {path.name}"
                )
            if name in {"time", "lon", "lat"} and np.issubdtype(dataset.dtype, np.number):
                values = np.asarray(dataset[:])
                result["coordinates"][name]["value_summary"] = {
                    "first": _json_value(values.flat[0]),
                    "last": _json_value(values.flat[-1]),
                    "minimum": _json_value(np.nanmin(values)),
                    "maximum": _json_value(np.nanmax(values)),
                    "strictly_increasing": bool(np.all(np.diff(values.reshape(-1)) > 0))
                    if values.size > 1 else None,
                }
        for name in QA_FIELDS:
            dataset = grid.get(name)
            if dataset is not None and dataset.shape != precipitation.shape:
                raise ValueError(
                    f"Grid/{name} tiene shape {dataset.shape}, no coincide con precipitation: {path.name}"
                )
    return result


def discover_files(nasa_dir: Path, ncar_dir: Path) -> list[tuple[Path, str]]:
    if not nasa_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio NASA: {nasa_dir}")
    if not ncar_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio NCAR: {ncar_dir}")
    nasa = sorted(nasa_dir.glob("3B-MO.MS.MRG.3IMERG.*.V07B.HDF5"))
    ncar = sorted(ncar_dir.glob("imerg_2005??_v07b_ncar.h5"))
    return [(path, "NASA") for path in nasa] + [(path, "NCAR") for path in ncar]


def build_inventory(nasa_dir: Path, ncar_dir: Path) -> dict:
    entries = [inspect_file(path, source) for path, source in discover_files(nasa_dir, ncar_dir)]
    if not entries:
        raise FileNotFoundError("No se encontraron muestras IMERG en las rutas configuradas")
    nasa_jan_2005 = next(
        (entry for entry in entries if entry["source_label"] == "NASA" and entry["period"] == "2005-01"),
        None,
    )
    ncar_jan_2005 = next(
        (entry for entry in entries if entry["source_label"] == "NCAR" and entry["period"] == "2005-01"),
        None,
    )
    comparison = {"period": "2005-01", "status": "not_comparable_missing_side"}
    if nasa_jan_2005 and ncar_jan_2005:
        same_hash = nasa_jan_2005["sha256"] == ncar_jan_2005["sha256"]
        comparison = {
            "period": "2005-01",
            "status": "byte_identical" if same_hash else "different_bytes",
            "nasa_sha256": nasa_jan_2005["sha256"],
            "ncar_sha256": ncar_jan_2005["sha256"],
        }
    return {
        "schema_version": 1,
        "purpose": "File identity and HDF5 metadata inventory only; no pixel QA filter is applied.",
        "entries": entries,
        "nasa_ncar_comparison": comparison,
        "qa_status": "unassessed",
    }


def select_phase2_samples(entries: list[dict]) -> list[dict]:
    """Select one source per month: NASA Jan 2005/2021, NCAR Feb-Dec 2005."""
    by_source_period = {(entry["source_label"], entry["period"]): entry for entry in entries}
    nasa_jan = by_source_period.get(("NASA", "2005-01"))
    ncar_jan = by_source_period.get(("NCAR", "2005-01"))
    if nasa_jan is None or ncar_jan is None:
        raise FileNotFoundError("Se necesitan NASA y NCAR enero 2005 para seleccionar el origen")
    if nasa_jan["sha256"] != ncar_jan["sha256"]:
        raise ValueError("NASA/NCAR enero 2005 ya no son byte-idénticos; revisar selección de fuente")
    selected = [nasa_jan]
    for month in range(2, 13):
        period = f"2005-{month:02d}"
        entry = by_source_period.get(("NCAR", period))
        if entry is None:
            raise FileNotFoundError(f"Falta la copia NCAR disponible de {period}")
        selected.append(entry)
    nasa_2021 = by_source_period.get(("NASA", "2021-01"))
    if nasa_2021 is None:
        raise FileNotFoundError("Falta el gránulo NASA IMERG de enero 2021")
    selected.append(nasa_2021)
    return selected


def build_domain_masks(
    longitudes: np.ndarray,
    latitudes: np.ndarray,
    basin_mask_lat_lon: np.ndarray,
    *,
    bbox: tuple[float, float, float, float] = (138.0, -38.0, 153.0, -24.0),
) -> dict[str, np.ndarray | None]:
    """Return masks aligned to HDF order lon,lat; global is represented by None."""
    longitudes = np.asarray(longitudes).reshape(-1)
    latitudes = np.asarray(latitudes).reshape(-1)
    basin_mask_lat_lon = np.asarray(basin_mask_lat_lon, dtype=bool)
    expected_basin_shape = (latitudes.size, longitudes.size)
    if basin_mask_lat_lon.shape != expected_basin_shape:
        raise ValueError(
            f"La máscara lat,lon tiene shape {basin_mask_lat_lon.shape}; "
            f"se esperaba {expected_basin_shape}"
        )
    west, south, east, north = bbox
    bbox_mask = (
        (longitudes[:, None] >= west)
        & (longitudes[:, None] <= east)
        & (latitudes[None, :] >= south)
        & (latitudes[None, :] <= north)
    )
    return {"global": None, "bbox_centers": bbox_mask, "basin_centers": basin_mask_lat_lon.T}


def classify_values(values: np.ndarray, fill) -> dict[str, int]:
    """Partition storage states; zero is counted within finite non-fill values."""
    array = np.asarray(values)
    finite = np.isfinite(array)
    fill_mask = np.zeros(array.shape, dtype=bool)
    if fill is not None:
        fill_in_storage_dtype = np.asarray(fill, dtype=array.dtype).item()
        fill_mask = array == fill_in_storage_dtype
    non_finite = ~finite & ~fill_mask
    finite_non_fill = finite & ~fill_mask
    return {
        "total": int(array.size),
        "fill": int(fill_mask.sum()),
        "non_finite": int(non_finite.sum()),
        "finite_non_fill": int(finite_non_fill.sum()),
        "zero_valid": int((finite_non_fill & (array == 0)).sum()),
    }


def describe_distribution(values: np.ndarray, fill, *, exact_counts: bool = False) -> dict:
    array = np.asarray(values)
    valid = np.isfinite(array)
    if fill is not None:
        fill_in_storage_dtype = np.asarray(fill, dtype=array.dtype).item()
        valid &= array != fill_in_storage_dtype
    observed = array[valid].astype(np.float64, copy=False)
    if not observed.size:
        return {"n": 0, "min": None, "max": None, "quantiles": {}, "value_counts": {}}
    quantile_values = np.quantile(observed, [0, 0.05, 0.25, 0.5, 0.75, 0.95, 1])
    result = {
        "n": int(observed.size),
        "min": float(quantile_values[0]),
        "max": float(quantile_values[-1]),
        "quantiles": {
            key: float(value)
            for key, value in zip(("p05", "p25", "p50", "p75", "p95"), quantile_values[1:-1])
        },
        "value_counts": {},
    }
    if exact_counts:
        unique_values, value_counts = np.unique(observed, return_counts=True)
        result["value_counts"] = {
            str(value): int(count) for value, count in zip(unique_values, value_counts)
        }
    return result


def _selected_values(values: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    return np.asarray(values).reshape(-1) if mask is None else np.asarray(values)[mask]


def summarize_sample(
    path: Path,
    entry: dict,
    basin_mask_cache: CenterMaskCache,
    basin_path: Path,
    *,
    bbox: tuple[float, float, float, float] = (138.0, -38.0, 153.0, -24.0),
) -> dict:
    with h5py.File(path, "r") as handle:
        grid = handle["Grid"]
        longitudes = grid["lon"][:]
        latitudes = grid["lat"][:]
        center_mask = basin_mask_cache.get(latitudes, longitudes, basin_path)
        masks = build_domain_masks(longitudes, latitudes, center_mask.values, bbox=bbox)
        global_cell_count = int(np.prod(grid["precipitation"].shape[1:]))
        if grid["precipitation"].shape[1:] != masks["bbox_centers"].shape:
            raise ValueError(f"La máscara espacial no coincide con la grilla: {path.name}")

        fields = {}
        for name in FIELDS:
            dataset = grid.get(name)
            if dataset is None:
                fields[name] = {"present": False, "counts": None, "distribution": None}
                continue
            values = dataset[0]
            fill = dataset.attrs.get("_FillValue")
            fields[name] = {
                "present": True,
                "units": _json_value(dataset.attrs.get("units", dataset.attrs.get("Units"))),
                "fill_value": _json_value(fill),
                "code_missing_value": _json_value(dataset.attrs.get("CodeMissingValue")),
                "qa_status": "unassessed",
                "counts": {},
                "distribution": {},
            }
            for scope, mask in masks.items():
                selected = _selected_values(values, mask)
                fields[name]["counts"][scope] = classify_values(selected, fill)
                if name in QA_FIELDS:
                    fields[name]["distribution"][scope] = describe_distribution(
                        selected,
                        fill,
                        exact_counts=name == "gaugeRelativeWeighting",
                    )
            del values
    return {
        "period": entry["period"],
        "source_label": entry["source_label"],
        "file": entry["file"],
        "file_version": entry["file_version"],
        "sha256": entry["sha256"],
        "basin_geometry_sha256": center_mask.geometry_sha256,
        "domains": {
            "global": {"definition": "all native-grid cells", "n": global_cell_count},
            "bbox_centers": {"definition": "cell centers, inclusive 138–153°E and -38–-24°", "n": int(masks["bbox_centers"].sum())},
            "basin_centers": {"definition": "MDBA polygon center mask; covers semantics; holes excluded", "n": int(masks["basin_centers"].sum())},
        },
        "fields": fields,
        "qa_status": "unassessed",
    }


def build_empirical_summary(
    inventory: dict,
    nasa_dir: Path,
    ncar_dir: Path,
    basin_geojson: Path,
) -> dict:
    selected_entries = select_phase2_samples(inventory["entries"])
    mask_cache = CenterMaskCache()
    samples = []
    for entry in selected_entries:
        source_dir = nasa_dir if entry["source_label"] == "NASA" else ncar_dir
        sample = summarize_sample(source_dir / entry["file"], entry, mask_cache, basin_geojson)
        samples.append(sample)
    return {
        "schema_version": 1,
        "qa_status": "unassessed",
        "method": {
            "value_state_partition": "fill; non-finite excluding fill; finite non-fill; zero is a subset of finite non-fill",
            "bbox_centers": [138.0, -38.0, 153.0, -24.0],
            "basin_selection": "native-grid centers selected by CenterMaskCache; no area weights",
            "filters_applied": [],
            "thresholds_applied": [],
        },
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nasa-dir", type=Path, default=DEFAULT_NASA_DIR)
    parser.add_argument("--ncar-dir", type=Path, default=DEFAULT_NCAR_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--basin-geojson", type=Path)
    parser.add_argument("--summary-output", type=Path)
    args = parser.parse_args()
    inventory = build_inventory(args.nasa_dir, args.ncar_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_info = None
    if args.basin_geojson is not None or args.summary_output is not None:
        if args.basin_geojson is None or args.summary_output is None:
            parser.error("--basin-geojson y --summary-output deben usarse juntos")
        summary = build_empirical_summary(inventory, args.nasa_dir, args.ncar_dir, args.basin_geojson)
        args.summary_output.parent.mkdir(parents=True, exist_ok=True)
        args.summary_output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        summary_info = {"summary_output": str(args.summary_output), "samples_summarized": len(summary["samples"])}
    print(json.dumps({
        "output": str(args.output),
        "entries": len(inventory["entries"]),
        "qa_status": inventory["qa_status"],
        "nasa_ncar_comparison": inventory["nasa_ncar_comparison"],
        **(summary_info or {}),
        "missing_qa_fields": {
            entry["file"]: [name for name in QA_FIELDS if not entry["fields"][name]["present"]]
            for entry in inventory["entries"]
        },
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
