"""Inventory IMERG HDF5 provenance, structure, and QA field metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import h5py
import numpy as np

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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nasa-dir", type=Path, default=DEFAULT_NASA_DIR)
    parser.add_argument("--ncar-dir", type=Path, default=DEFAULT_NCAR_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    inventory = build_inventory(args.nasa_dir, args.ncar_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "entries": len(inventory["entries"]),
        "qa_status": inventory["qa_status"],
        "nasa_ncar_comparison": inventory["nasa_ncar_comparison"],
        "missing_qa_fields": {
            entry["file"]: [name for name in QA_FIELDS if not entry["fields"][name]["present"]]
            for entry in inventory["entries"]
        },
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
