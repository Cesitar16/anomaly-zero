"""Inventaría procedencia y estructura de las muestras GLDAS FUL-113."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np

DEFAULT_MANIFEST = Path("research/manifests/gldas_ful113_samples.json")
DEFAULT_OUTPUT = Path("data/cache/ful113/gldas_sample_inventory.json")
EXPECTED_VARIABLE = "SoilMoi0_10cm_inst"
EXPECTED_SHAPE = (1, 600, 1440)


def _json_value(value: Any) -> Any:
    """Convert HDF5 attribute values to JSON-safe scalars/lists."""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _json_value(value.item())
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dimension_names(dataset: h5py.Dataset) -> list[list[str]]:
    names: list[list[str]] = []
    for axis in range(dataset.ndim):
        attached = [Path(scale.name).name for scale in dataset.dims[axis].values()]
        names.append(attached)
    return names


def inspect_sample(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    """Inspect one authentic file and validate its manifest identity/structure."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe el archivo esperado: {path}")
    if path.name != record["filename"]:
        raise ValueError(
            f"Identidad de archivo incompatible: se esperaba {record['filename']}, "
            f"se recibió {path.name}"
        )

    actual_hash = _sha256(path)
    actual_size = path.stat().st_size
    if actual_hash != record["sha256"]:
        raise ValueError(
            f"SHA-256 incompatible para {path.name}: {actual_hash}; "
            f"manifiesto: {record['sha256']}"
        )
    if actual_size != record["size_bytes"]:
        raise ValueError(
            f"Tamaño incompatible para {path.name}: {actual_size}; "
            f"manifiesto: {record['size_bytes']}"
        )

    with h5py.File(path, "r") as source:
        if EXPECTED_VARIABLE not in source:
            raise ValueError(f"Falta la variable {EXPECTED_VARIABLE} en {path.name}")
        variable = source[EXPECTED_VARIABLE]
        if not isinstance(variable, h5py.Dataset):
            raise TypeError(f"{EXPECTED_VARIABLE} no es un dataset en {path.name}")
        if variable.shape != EXPECTED_SHAPE:
            raise ValueError(
                f"Dimensiones inesperadas en {path.name}: {variable.shape}; "
                f"se esperaba {EXPECTED_SHAPE}"
            )
        if variable.dtype != np.dtype("float32"):
            raise ValueError(
                f"Tipo numérico inesperado en {path.name}: {variable.dtype}"
            )
        for coordinate, length in (("time", 1), ("lat", 600), ("lon", 1440)):
            if coordinate not in source or source[coordinate].shape != (length,):
                raise ValueError(f"Coordenada {coordinate} incompatible en {path.name}")
        if "time_bnds" not in source or source["time_bnds"].shape != (1, 2):
            raise ValueError(f"time_bnds incompatible en {path.name}")

        time_values = np.asarray(source["time"][:], dtype=float).tolist()
        time_bounds = np.asarray(source["time_bnds"][:], dtype=float).tolist()
        if time_values != [record["time_value_days"]]:
            raise ValueError(f"Periodo temporal incompatible en {path.name}: {time_values}")
        if time_bounds != [record["time_bounds_days"]]:
            raise ValueError(f"Límites temporales incompatibles en {path.name}: {time_bounds}")

        variable_attrs = {
            key: _json_value(value) for key, value in variable.attrs.items()
        }
        root_attrs = {key: _json_value(value) for key, value in source.attrs.items()}
        if variable_attrs.get("units") != "kg m-2":
            raise ValueError(f"Unidad inesperada en {path.name}: {variable_attrs.get('units')}")
        if variable_attrs.get("cell_methods") != "time: mean":
            raise ValueError(f"cell_methods inesperado en {path.name}")

        relevant_coordinates = {}
        for name in ("time", "time_bnds", "lat", "lon"):
            dataset = source[name]
            relevant_coordinates[name] = {
                "shape": list(dataset.shape),
                "dtype": str(dataset.dtype),
                "attributes": {key: _json_value(value) for key, value in dataset.attrs.items()},
            }

        return {
            "sample_id": record["sample_id"],
            "period": record["period"],
            "source": record["source"],
            "cmr": record["cmr"],
            "filename": path.name,
            "local_path": str(path.resolve()),
            "size_bytes": actual_size,
            "sha256": actual_hash,
            "format": "NetCDF4/HDF5",
            "root_attributes": root_attrs,
            "variable": {
                "path": f"/{EXPECTED_VARIABLE}",
                "shape": list(variable.shape),
                "dimension_scales_by_axis": _dimension_names(variable),
                "dtype": str(variable.dtype),
                "attributes": variable_attrs,
            },
            "coordinates": relevant_coordinates,
            "time_values_days_since_2000": time_values,
            "time_bounds_days_since_2000": time_bounds,
            "qa_assessment": "unassessed",
            "interpretation_limit": (
                "Inventario de identidad, atributos y estructura; no determina "
                "la máscara de aguas continentales ni aprueba uso científico."
            ),
        }


def build_inventory(
    sample_paths: dict[str, Path], manifest: dict[str, Any]
) -> dict[str, Any]:
    records = {record["sample_id"]: record for record in manifest["samples"]}
    expected_ids = set(records)
    if set(sample_paths) != expected_ids:
        raise ValueError(
            f"Se requieren exactamente las muestras {sorted(expected_ids)}; "
            f"recibidas: {sorted(sample_paths)}"
        )
    inspected = [inspect_sample(sample_paths[sample_id], records[sample_id]) for sample_id in sorted(records)]
    return {
        "inventory_version": 1,
        "task": "FUL-113 phase 1",
        "qa_assessment": "unassessed",
        "samples": inspected,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gldas-2005", required=True, type=Path)
    parser.add_argument("--gldas-2021", required=True, type=Path)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST, type=Path)
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    inventory = build_inventory(
        {"gldas-2005-01": args.gldas_2005, "gldas-2021-01": args.gldas_2021},
        manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Inventario escrito: {args.output}")
    print(f"Muestras verificadas: {len(inventory['samples'])}; QA=unassessed")


if __name__ == "__main__":
    main()
