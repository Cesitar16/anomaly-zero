"""Compara en forma descriptiva GLDAS SoilMoi0_10cm_inst con una máscara candidata."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

import h5py
import numpy as np

if __package__:
    from .inspeccionar_linaje_gldas import _json_value, inspect_sample
else:
    from inspeccionar_linaje_gldas import _json_value, inspect_sample

SAMPLE_MANIFEST = Path("research/manifests/gldas_ful113_samples.json")
MASK_MANIFEST = Path("research/manifests/gldas_ful113_mask.json")
DEFAULT_OUTPUT = Path("data/cache/ful113/gldas_mask_comparison.json")
MASK_DATASET = "GLDAS_mask"
SOIL_DATASET = "SoilMoi0_10cm_inst"
EXPECTED_AXES = [["time"], ["lat"], ["lon"]]
INLAND_DIAGNOSTIC_BBOX = (137.0, -30.0, 140.0, -26.0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _dimension_scales(dataset: h5py.Dataset) -> list[list[str]]:
    return [
        [Path(scale.name).name for scale in dataset.dims[axis].values()]
        for axis in range(dataset.ndim)
    ]


def assert_aligned_grid(
    sample_axes: list[list[str]],
    reference_axes: list[list[str]],
    sample_lat: np.ndarray,
    reference_lat: np.ndarray,
    sample_lon: np.ndarray,
    reference_lon: np.ndarray,
) -> None:
    """Fail closed unless both arrays use the same time/lat/lon grid and centers."""
    if sample_axes != EXPECTED_AXES or reference_axes != EXPECTED_AXES:
        raise ValueError(
            "Orden de ejes incompatible; se requiere time, lat, lon en muestra y máscara"
        )
    if not np.array_equal(sample_lat, reference_lat):
        raise ValueError("Las coordenadas lat de muestra y máscara no coinciden exactamente")
    if not np.array_equal(sample_lon, reference_lon):
        raise ValueError("Las coordenadas lon de muestra y máscara no coinciden exactamente")


def cross_classify(
    sample_values: np.ndarray,
    sample_fill: float,
    mask_values: np.ndarray,
    mask_fill: float,
) -> dict[str, Any]:
    """Count raw fill/non-finite/finite values by stored mask class, without filtering."""
    sample = np.asarray(sample_values)
    mask = np.asarray(mask_values)
    if sample.shape != mask.shape:
        raise ValueError(f"Grillas incompatibles: muestra {sample.shape}, máscara {mask.shape}")

    sample_fill_cells = np.isfinite(sample) & (sample == sample_fill)
    sample_nonfinite = ~np.isfinite(sample)
    sample_finite_nonfill = np.isfinite(sample) & (sample != sample_fill)
    mask_fill_cells = np.isfinite(mask) & (mask == mask_fill)
    mask_nonfinite = ~np.isfinite(mask)
    mask_water = np.isfinite(mask) & (mask == 0)
    mask_land = np.isfinite(mask) & (mask == 1)
    mask_other = np.isfinite(mask) & ~np.isin(mask, [mask_fill, 0, 1])

    mask_classes = {
        "water_0": mask_water,
        "land_1": mask_land,
        "fill": mask_fill_cells,
        "nonfinite": mask_nonfinite,
        "other_finite": mask_other,
    }
    sample_states = {
        "fill": sample_fill_cells,
        "nonfinite": sample_nonfinite,
        "finite_nonfill": sample_finite_nonfill,
    }
    counts = {
        class_name: {
            "cells": int(class_cells.sum()),
            **{
                state_name: int((class_cells & state_cells).sum())
                for state_name, state_cells in sample_states.items()
            },
        }
        for class_name, class_cells in mask_classes.items()
    }
    return {
        "total_cells": int(sample.size),
        "sample_states": {
            name: int(cells.sum()) for name, cells in sample_states.items()
        },
        "mask_states": {
            "water_0": int(mask_water.sum()),
            "land_1": int(mask_land.sum()),
            "fill": int(mask_fill_cells.sum()),
            "nonfinite": int(mask_nonfinite.sum()),
            "other_finite": int(mask_other.sum()),
        },
        "cross_counts": counts,
        "qa_assessment": "unassessed",
        "filters_applied": [],
    }


def _inland_window_counts(
    sample_values: np.ndarray,
    sample_fill: float,
    mask_values: np.ndarray,
    mask_fill: float,
    lon: np.ndarray,
    lat: np.ndarray,
    bbox: tuple[float, float, float, float],
) -> dict[str, Any]:
    west, south, east, north = bbox
    selected = (
        (lon[np.newaxis, :] >= west)
        & (lon[np.newaxis, :] <= east)
        & (lat[:, np.newaxis] >= south)
        & (lat[:, np.newaxis] <= north)
    )
    if not np.any(selected):
        raise ValueError(f"La ventana diagnóstica no incluye celdas: {bbox}")
    return {
        "bbox_lon_lat_inclusive": list(bbox),
        "selection_basis": "grid-cell centers; diagnostic inland window, not a basin polygon",
        **cross_classify(
            np.asarray(sample_values)[selected],
            sample_fill,
            np.asarray(mask_values)[selected],
            mask_fill,
        ),
    }


def inspect_reference_mask(path: Path, record: dict[str, Any]) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"No existe la máscara de referencia: {path}")
    if path.name != record["filename"]:
        raise ValueError(f"Nombre inesperado de máscara: {path.name}")
    actual_hash = _sha256(path)
    if actual_hash != record["sha256"]:
        raise ValueError(f"SHA-256 de máscara incompatible: {actual_hash}")
    if path.stat().st_size != record["size_bytes"]:
        raise ValueError(f"Tamaño de máscara incompatible: {path.stat().st_size}")

    with h5py.File(path, "r") as source:
        if MASK_DATASET not in source:
            raise ValueError(f"Falta /{MASK_DATASET} en la máscara")
        dataset = source[MASK_DATASET]
        axes = _dimension_scales(dataset)
        if list(dataset.shape) != record["shape"]:
            raise ValueError(f"Dimensiones inesperadas de máscara: {dataset.shape}")
        if str(dataset.dtype) != record["dtype"]:
            raise ValueError(f"Tipo numérico inesperado de máscara: {dataset.dtype}")
        if axes != record["dimension_scales_by_axis"]:
            raise ValueError(f"Orden de ejes inesperado en máscara: {axes}")
        units = _json_value(dataset.attrs.get("units"))
        if units != record["class_encoding"]:
            raise ValueError(f"Codificación de máscara inesperada: {units}")

        attrs = {key: _json_value(value) for key, value in dataset.attrs.items()}
        root_attrs = {key: _json_value(value) for key, value in source.attrs.items()}
        values = dataset[:]
        classes, counts = np.unique(values, return_counts=True)
        return {
            "filename": path.name,
            "local_path": str(path.resolve()),
            "size_bytes": path.stat().st_size,
            "sha256": actual_hash,
            "source_page": record["source_page"],
            "source_file": record["source_file"],
            "shape": list(dataset.shape),
            "dimension_scales_by_axis": axes,
            "dtype": str(dataset.dtype),
            "dataset_attributes": attrs,
            "root_attributes": root_attrs,
            "stored_values_and_counts": {
                str(_json_value(value)): int(count)
                for value, count in zip(classes, counts, strict=True)
            },
            "observed_history": root_attrs.get("history"),
            "interpretation_limit": record["interpretation_limit"],
        }


def compare_sample(
    sample_path: Path,
    sample_record: dict[str, Any],
    mask_path: Path,
    mask_record: dict[str, Any],
) -> dict[str, Any]:
    sample_identity = inspect_sample(sample_path, sample_record)
    with h5py.File(sample_path, "r") as sample, h5py.File(mask_path, "r") as reference:
        soil = sample[SOIL_DATASET]
        mask_ds = reference[MASK_DATASET]
        assert_aligned_grid(
            _dimension_scales(soil),
            _dimension_scales(mask_ds),
            sample["lat"][:],
            reference["lat"][:],
            sample["lon"][:],
            reference["lon"][:],
        )
        if soil.shape != mask_ds.shape:
            raise ValueError(
                f"Dimensiones incompatibles: SoilMoi {soil.shape}, máscara {mask_ds.shape}"
            )
        soil_fill = float(np.asarray(soil.attrs["_FillValue"]).reshape(-1)[0])
        mask_fill = float(np.asarray(mask_ds.attrs["_FillValue"]).reshape(-1)[0])
        soil_values = soil[:]
        mask_values = mask_ds[:]
        global_counts = cross_classify(
            soil_values, soil_fill, mask_values, mask_fill
        )
        inland_counts = _inland_window_counts(
            soil_values[0],
            soil_fill,
            mask_values[0],
            mask_fill,
            sample["lon"][:],
            sample["lat"][:],
            INLAND_DIAGNOSTIC_BBOX,
        )
    return {
        "sample_id": sample_identity["sample_id"],
        "period": sample_identity["period"],
        "sample_filename": sample_identity["filename"],
        "sample_sha256": sample_identity["sha256"],
        "mask_filename": mask_record["filename"],
        "mask_sha256": mask_record["sha256"],
        "variable": SOIL_DATASET,
        "sample_fill_value": soil_fill,
        "mask_fill_value": mask_fill,
        "grid_alignment": "exact coordinate equality; dimensions time,lat,lon",
        "global": global_counts,
        "central_australia_inland_window": inland_counts,
        "interpretation_limit": (
            "Descriptive agreement with the published candidate mask only; it does not "
            "identify the exact mask revision or prove the historical processing path."
        ),
    }


def build_comparison(
    sample_paths: dict[str, Path],
    sample_manifest: dict[str, Any],
    mask_path: Path,
    mask_manifest: dict[str, Any],
) -> dict[str, Any]:
    mask_record = mask_manifest
    mask_metadata = inspect_reference_mask(mask_path, mask_record)
    sample_records = {item["sample_id"]: item for item in sample_manifest["samples"]}
    if set(sample_paths) != set(sample_records):
        raise ValueError("Se requieren las dos muestras registradas en el manifiesto")
    results = [
        compare_sample(sample_paths[key], sample_records[key], mask_path, mask_record)
        for key in sorted(sample_records)
    ]
    return {
        "comparison_version": 1,
        "question": "¿Coincide el patrón actual de fill con la máscara GLDAS publicada?",
        "reference_mask": mask_metadata,
        "results": results,
        "qa_assessment": "unassessed",
        "conclusion_limit": (
            "El patrón de fill no demuestra por sí solo que se aplicara esta revisión "
            "específica de máscara durante el posprocesamiento NASA de octubre de 2020."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gldas-2005", type=Path, required=True)
    parser.add_argument("--gldas-2021", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--sample-manifest", type=Path, default=SAMPLE_MANIFEST)
    parser.add_argument("--mask-manifest", type=Path, default=MASK_MANIFEST)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    sample_manifest = json.loads(args.sample_manifest.read_text(encoding="utf-8"))
    mask_manifest = json.loads(args.mask_manifest.read_text(encoding="utf-8"))
    result = build_comparison(
        {
            "gldas-2005-01": args.gldas_2005,
            "gldas-2021-01": args.gldas_2021,
        },
        sample_manifest,
        args.mask,
        mask_manifest,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Comparación escrita: {args.output}")
    print(f"Muestras comparadas: {len(result['results'])}; QA=unassessed")


if __name__ == "__main__":
    main()
