"""Build a deterministic, point-sample IMERG 2005 snapshot from verified granules."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from research.snapshot_format import (
    canonical_json,
    dataset_id_for_input_fingerprint,
    snapshot_sha256,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "data/raw/nasa/imerg_final"
DEFAULT_POINT = ROOT / "research/manifests/ful105_imerg_panel_point.json"
DEFAULT_OUTPUT = ROOT / "data/processed/ful116"
PIPELINE_VERSION = "1.0.0"
COLLECTION_ID = "C2723754851-GES_DISC"
DOI = "10.5067/GPM/IMERG/3B-MONTH/07"
PRODUCT = "GPM_3IMERGM"
VARIABLE_PATH = "Grid/precipitation"
UNITS = "mm/hr"
FILL_CODE_MISSING = -9999.9
DATASET_SHAPE = (1, 3600, 1800)
NASA_NAME = re.compile(
    r"^3B-MO\.MS\.MRG\.3IMERG\.2005(?P<month>0[1-9]|1[0-2])01-"
    r"S000000-E235959\.(?P<suffix>0[1-9]|1[0-2])\.V07B\.HDF5$"
)
QA_FIELDS = (
    "Grid/precipitationQualityIndex",
    "Grid/randomError",
    "Grid/gaugeRelativeWeighting",
)


@dataclass(frozen=True)
class Granule:
    month: str
    path: Path
    manifest_path: Path
    manifest: dict[str, Any]
    sha256: str
    manifest_sha256: str
    synthetic: bool


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _header(value: Any) -> dict[str, str]:
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="strict")
    if not isinstance(value, str):
        raise TypeError("Falta Grid/FileHeader en el granule IMERG")
    return {
        key.strip(): field.strip().rstrip(";").strip()
        for line in value.splitlines()
        if "=" in line
        for key, field in (line.split("=", 1),)
    }


def _manifest_is_synthetic(manifest: dict[str, Any], path: Path, month: str) -> bool:
    marker = manifest.get("synthetic_fixture", False)
    if not isinstance(marker, bool):
        raise TypeError(f"Marca synthetic_fixture inválida en {path.name}")
    if marker:
        source = manifest.get("source")
        if (
            type(manifest.get("manifest_version")) is not int
            or manifest.get("manifest_version") != 1
            or not isinstance(manifest.get("fixture_id"), str)
            or not manifest["fixture_id"].strip()
            or not isinstance(source, dict)
            or source.get("provider") != "synthetic test fixture"
        ):
            raise ValueError(f"Procedencia sintética incompleta o contradictoria: {path.name}")
        return True

    product = manifest.get("product")
    period = manifest.get("period")
    source = manifest.get("source")
    if not all(isinstance(value, dict) for value in (product, period, source)):
        raise ValueError(f"Manifest sin metadatos de procedencia completos: {path.name}")
    expected_start = f"2005-{month}-01T00:00:00.000Z"
    expected_end = (
        f"2005-{month}-{calendar.monthrange(2005, int(month))[1]:02d}T23:59:59.999Z"
    )
    granule_id = manifest.get("granule_id")
    collection_metadata = source.get("collection_metadata")
    granule_metadata = source.get("granule_metadata")
    retrieved_at = manifest.get("downloaded_at_utc")
    try:
        retrieved = datetime.fromisoformat(retrieved_at)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"Timestamp de recuperación inválido: {path.name}") from exc
    if (
        type(manifest.get("manifest_version")) is not int
        or manifest.get("manifest_version") != 1
        or product.get("doi") != DOI
        or period.get("start") != expected_start
        or period.get("end") != expected_end
        or source.get("provider") != "NASA GES DISC via Earthdata CMR"
        or not isinstance(granule_id, str)
        or re.fullmatch(r"G\d+-GES_DISC", granule_id) is None
        or manifest.get("producer_granule_id") != f"GPM_3IMERGM.07:{path.name}"
        or collection_metadata != f"https://cmr.earthdata.nasa.gov/search/concepts/{COLLECTION_ID}.umm_json"
        or granule_metadata != f"https://cmr.earthdata.nasa.gov/search/concepts/{granule_id}.umm_json"
        or retrieved.utcoffset() != timedelta(0)
    ):
        raise ValueError(f"Procedencia NASA/CMR insuficiente o incompatible: {path.name}")
    return False


def _resolve_synthetic_flag(flags: list[bool]) -> bool:
    if not flags or any(not isinstance(flag, bool) for flag in flags):
        raise ValueError("No se pudo clasificar la procedencia de todos los granules")
    if len(set(flags)) != 1:
        raise ValueError("No se permite mezclar granules NASA reales y fixtures sintéticos")
    return flags[0]


def discover_granules(input_dir: Path, *, require_complete: bool = True) -> list[Granule]:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"No existe el directorio de granules: {input_dir}")
    found: dict[str, Granule] = {}
    for path in sorted(input_dir.glob("*.HDF5")):
        match = NASA_NAME.fullmatch(path.name)
        if match is None:
            continue
        month = match.group("month")
        if match.group("suffix") != month:
            raise ValueError(f"Sufijo mensual no coincide: {path.name}")
        if month in found:
            raise ValueError(f"Más de un granule candidato para 2005-{month}")
        manifest_path = Path(f"{path}.manifest.json")
        if not manifest_path.is_file():
            raise FileNotFoundError(f"Falta manifest NASA para {path.name}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise TypeError(f"Manifest debe ser un objeto JSON: {manifest_path.name}")
        synthetic = _manifest_is_synthetic(manifest, path, month)
        expected_filename = manifest.get("filename")
        product = manifest.get("product") or {}
        source = manifest.get("source") or {}
        if not isinstance(product, dict) or not isinstance(source, dict):
            raise TypeError(f"Secciones product/source inválidas: {path.name}")
        if expected_filename != path.name:
            raise ValueError(f"Nombre difiere del manifest: {path.name}")
        if (
            product.get("key") != "imerg_final"
            or product.get("short_name") != PRODUCT
            or product.get("version") != "07"
            or product.get("variable") != "precipitation"
            or manifest.get("collection_id") != COLLECTION_ID
        ):
            raise ValueError(f"Identidad de colección/producto incompatible: {path.name}")
        if not synthetic and source.get("provider") != "NASA GES DISC via Earthdata CMR":
            raise ValueError(f"Origen no verificado como NASA GES DISC: {path.name}")
        if (manifest.get("period") or {}).get("month") != f"2005-{month}":
            raise ValueError(f"Período del manifest incompatible: {path.name}")
        digest = sha256_file(path)
        if manifest.get("sha256") != digest or manifest.get("bytes") != path.stat().st_size:
            raise ValueError(f"SHA-256/tamaño no coincide con manifest: {path.name}")
        manifest_digest = sha256_file(manifest_path)
        found[month] = Granule(
            month=month,
            path=path,
            manifest_path=manifest_path,
            manifest=manifest,
            sha256=digest,
            manifest_sha256=manifest_digest,
            synthetic=synthetic,
        )

    expected = [f"{month:02d}" for month in range(1, 13)]
    missing = [month for month in expected if month not in found]
    if require_complete and missing:
        raise FileNotFoundError(
            "No se puede afirmar una serie anual: faltan granules NASA verificados para "
            + ", ".join(f"2005-{month}" for month in missing)
        )
    if not found:
        raise FileNotFoundError("No hay ningún granule IMERG NASA de 2005 verificable")
    granules = [found[month] for month in sorted(found)]
    _resolve_synthetic_flag([granule.synthetic for granule in granules])
    return granules


def load_point(path: Path) -> dict[str, Any]:
    point = json.loads(path.read_text(encoding="utf-8"))
    for key in ("selection_id", "selection_source", "selection_method", "grid_registration"):
        if not isinstance(point.get(key), str) or not point[key]:
            raise ValueError(f"Punto de panel sin {key}")
    for key in ("latitude", "longitude"):
        if not isinstance(point.get(key), (int, float)) or not np.isfinite(point[key]):
            raise ValueError(f"Coordenada inválida: {key}")
    if not -90 <= point["latitude"] <= 90 or not -180 <= point["longitude"] <= 180:
        raise ValueError("Coordenada de punto fuera de límites geográficos")
    return point


def _nearest_index(values: np.ndarray, requested: float, name: str) -> int:
    values = np.asarray(values)
    index = int(np.argmin(np.abs(values.astype(np.float64) - requested)))
    if not np.isclose(float(values[index]), requested, atol=2e-6, rtol=0):
        raise ValueError(f"El punto elegido no coincide con un centro de grilla IMERG: {name}")
    if values.size > 1 and np.sum(np.isclose(values, values[index], atol=0, rtol=0)) != 1:
        raise ValueError(f"Centro de grilla duplicado para {name}")
    return index


def _inspect_and_sample(granule: Granule, point: dict[str, Any]) -> dict[str, Any]:
    with h5py.File(granule.path, "r") as h5:
        if "Grid" not in h5 or VARIABLE_PATH not in h5:
            raise ValueError(f"Falta {VARIABLE_PATH}: {granule.path.name}")
        grid = h5["Grid"]
        field = grid["precipitation"]
        header = _header(grid.attrs.get("FileHeader", h5.attrs.get("FileHeader")))
        if header.get("FileName") != granule.path.name or header.get("ProductVersion") != "V07B":
            raise ValueError(f"FileHeader NASA incompatible con nombre/versión: {granule.path.name}")
        if header.get("DOIshortName") != "3IMERGM" or header.get("AlgorithmID") != "3IMERGM":
            raise ValueError(f"FileHeader no identifica IMERG mensual Final: {granule.path.name}")
        year, month_num = 2005, int(granule.month)
        period_start = f"{year:04d}-{month_num:02d}-01T00:00:00.000Z"
        period_end = (
            f"{year:04d}-{month_num:02d}-{calendar.monthrange(year, month_num)[1]:02d}"
            "T23:59:59.999Z"
        )
        if header.get("StartGranuleDateTime") != period_start or header.get("StopGranuleDateTime") != period_end:
            raise ValueError(f"Ventana interna del granule incompatible: {granule.path.name}")
        if field.ndim != 3 or tuple(field.shape) != DATASET_SHAPE:
            raise ValueError(f"Shape no esperada de precipitation: {field.shape}")
        dimension_names = field.attrs.get("DimensionNames")
        if isinstance(dimension_names, bytes):
            dimension_names = dimension_names.decode("ascii", errors="strict")
        if dimension_names != "time,lon,lat":
            raise ValueError(f"Orden de dimensiones inesperado: {dimension_names!r}")
        units = field.attrs.get("units", field.attrs.get("Units"))
        if isinstance(units, bytes):
            units = units.decode("ascii", errors="strict")
        if units != UNITS:
            raise ValueError(f"Unidad IMERG inesperada: {units!r}")
        required = ("time", "time_bnds", "lon", "lat", "lon_bnds", "lat_bnds")
        absent = [name for name in required if name not in grid]
        if absent:
            raise ValueError(f"Faltan ejes/bounds en {granule.path.name}: {absent}")
        if grid["time"].shape != (1,) or grid["time_bnds"].shape != (1, 2):
            raise ValueError(f"Dimensiones temporales incompatibles: {granule.path.name}")
        time_units = grid["time"].attrs.get("units", grid["time"].attrs.get("Units"))
        calendar_name = grid["time"].attrs.get("calendar")
        if isinstance(time_units, bytes):
            time_units = time_units.decode("ascii", errors="strict")
        if isinstance(calendar_name, bytes):
            calendar_name = calendar_name.decode("ascii", errors="strict")
        if not isinstance(time_units, str) or not time_units.startswith("seconds since 1980-01-06"):
            raise ValueError(f"Unidades temporales internas no reconocidas: {time_units!r}")
        if calendar_name != "julian":
            raise ValueError(f"Calendario temporal IMERG no coincide con manifiesto: {calendar_name!r}")
        time_value = float(np.asarray(grid["time"][...]).reshape(-1)[0])
        time_bounds = np.asarray(grid["time_bnds"][...], dtype=np.float64).reshape(-1)
        if not np.isfinite(time_value) or not np.isfinite(time_bounds).all() or not time_bounds[0] <= time_value <= time_bounds[1]:
            raise ValueError(f"Tiempo representativo fuera de time_bnds: {granule.path.name}")
        lon = np.asarray(grid["lon"][...])
        lat = np.asarray(grid["lat"][...])
        if grid["lon_bnds"].shape != (lon.size, 2) or grid["lat_bnds"].shape != (lat.size, 2):
            raise ValueError(f"Dimensiones de bounds espaciales incompatibles: {granule.path.name}")
        if not np.all(np.diff(lon) > 0) or not np.all(np.diff(lat) > 0):
            raise ValueError("Coordenadas de IMERG no son estrictamente ascendentes")
        lon_index = _nearest_index(lon, float(point["longitude"]), "longitude")
        lat_index = _nearest_index(lat, float(point["latitude"]), "latitude")
        lon_bounds = np.asarray(grid["lon_bnds"][lon_index], dtype=np.float64)
        lat_bounds = np.asarray(grid["lat_bnds"][lat_index], dtype=np.float64)
        if not min(lon_bounds) <= float(lon[lon_index]) <= max(lon_bounds):
            raise ValueError("El centro de longitud está fuera de los bounds declarados")
        if not min(lat_bounds) <= float(lat[lat_index]) <= max(lat_bounds):
            raise ValueError("El centro de latitud está fuera de los bounds declarados")
        stored = np.asarray(field[0, lon_index, lat_index]).item()
        raw_fill = field.attrs.get("_FillValue", field.attrs.get("CodeMissingValue"))
        fill = float(np.asarray(raw_fill).reshape(-1)[0]) if raw_fill is not None else FILL_CODE_MISSING
        code_missing = field.attrs.get("CodeMissingValue")
        if isinstance(code_missing, bytes):
            code_missing = code_missing.decode("ascii", errors="strict")
        is_fill = float(stored) == np.asarray(fill, dtype=field.dtype).item()
        if code_missing is not None:
            try:
                is_fill = is_fill or np.isclose(float(stored), float(code_missing), rtol=1e-6, atol=1e-8)
            except (TypeError, ValueError):
                pass
        if is_fill:
            value, state, reason = None, "missing", "provider_fill_value"
        elif not np.isfinite(stored):
            value, state, reason = None, "missing", "non_finite_source_value"
        else:
            value, state, reason = float(stored), "unassessed", None
        qa_fields = [name for name in QA_FIELDS if name in h5]
        coordinates = {
            "latitude": float(lat[lat_index]),
            "longitude": float(lon[lon_index]),
            "latitude_index": lat_index,
            "longitude_index": lon_index,
            "latitude_direction": "ascending",
            "longitude_direction": "ascending",
            "dimension_names": dimension_names,
            "source_time_value": time_value,
            "source_time_bounds": [float(value) for value in time_bounds],
            "source_calendar": calendar_name,
            "source_time_units": time_units,
        }
        return {
            "month": granule.month,
            "value": value,
            "state": state,
            "missing_reason": reason,
            "coordinates": coordinates,
            "fill_value": fill,
            "code_missing_value": str(code_missing) if code_missing is not None else None,
            "qa_source_fields_present": qa_fields,
        }


def _deterministic_npz(arrays: dict[str, np.ndarray]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, array in arrays.items():
            payload = io.BytesIO()
            np.lib.format.write_array(payload, np.ascontiguousarray(array), allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload.getvalue())
    return output.getvalue()


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _build_preview(
    granule: Granule,
    *,
    bbox: tuple[float, float, float, float],
) -> tuple[bytes, dict[str, Any]]:
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("BBox debe ser west,south,east,north dentro de EPSG:4326")
    with h5py.File(granule.path, "r") as h5:
        grid = h5["Grid"]
        lon = np.asarray(grid["lon"][...])
        lat = np.asarray(grid["lat"][...])
        lon_idx = np.flatnonzero((lon >= west) & (lon <= east))
        lat_idx = np.flatnonzero((lat >= south) & (lat <= north))
        if lon_idx.size == 0 or lat_idx.size == 0:
            raise ValueError("BBox no intersecta centros de la grilla")
        # Native HDF order is (time, lon, lat); retain that orientation unchanged.
        values = np.asarray(
            grid["precipitation"][0, lon_idx[0] : lon_idx[-1] + 1, lat_idx[0] : lat_idx[-1] + 1]
        )
        field = grid["precipitation"]
        fill_raw = field.attrs.get("_FillValue", field.attrs.get("CodeMissingValue", FILL_CODE_MISSING))
        fill = np.asarray(fill_raw, dtype=values.dtype).item()
        fill_mask = values == fill
        code_missing = field.attrs.get("CodeMissingValue")
        code_missing_value: float | None = None
        if code_missing is not None:
            try:
                code_missing_value = float(code_missing)
                fill_mask |= np.isclose(values, code_missing_value, rtol=1e-6, atol=1e-8)
            except (TypeError, ValueError):
                raise ValueError(f"CodeMissingValue inválido en {granule.path.name}")
        nonfinite_mask = ~np.isfinite(values) & ~fill_mask
        valid_mask = np.isfinite(values) & ~fill_mask
        arrays = {
            "values_raw": values,
            "longitudes": lon[lon_idx],
            "latitudes": lat[lat_idx],
            "fill_mask": fill_mask.astype(np.uint8),
            "nonfinite_mask": nonfinite_mask.astype(np.uint8),
            "finite_nonfill_mask": valid_mask.astype(np.uint8),
        }
        content = _deterministic_npz(arrays)
        meta = {
            "period": f"2005-{granule.month}",
            "source_granule": granule.path.name,
            "source_sha256": granule.sha256,
            "format": "NPZ (NumPy arrays; deterministic ZIP metadata)",
            "coordinate_crs": "EPSG:4326",
            "bbox_wsen": [west, south, east, north],
            "selection": "grid cell centers inclusively inside bbox; no polygon mask or reprojection",
            "array_orientation": "values_raw[longitude_index, latitude_index] (native lon,lat axes)",
            "shape": list(values.shape),
            "dtype": str(values.dtype),
            "units": UNITS,
            "fill_value": float(fill),
            "code_missing_value": code_missing_value,
            "qa_status": "unassessed",
            "qa_fields_present_not_applied": [name for name in QA_FIELDS if name in h5],
            "label": "Muestra NASA exploratoria; no es un promedio regional ni precipitación acumulada.",
        }
        return content, meta


def build_snapshot(
    input_dir: Path,
    point_path: Path,
    output_dir: Path,
    *,
    bbox: tuple[float, float, float, float] = (138.0, -38.0, 153.0, -24.0),
) -> dict[str, Any]:
    granules = discover_granules(input_dir)
    point = load_point(point_path)
    samples = [_inspect_and_sample(granule, point) for granule in granules]
    actual_coordinates = samples[0]["coordinates"]
    for sample in samples[1:]:
        coords = sample["coordinates"]
        if coords["latitude"] != actual_coordinates["latitude"] or coords["longitude"] != actual_coordinates["longitude"]:
            raise ValueError("El centro de grilla seleccionado cambió entre meses")

    preview_bytes, preview = _build_preview(granules[0], bbox=bbox)
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_name = "imerg_2005-01_bbox_preview.npz"
    preview["path"] = preview_name
    preview["sha256"] = hashlib.sha256(preview_bytes).hexdigest()
    preview["bytes"] = len(preview_bytes)

    values = [sample["value"] for sample in samples]
    missing_periods = [f"2005-{sample['month']}" for sample in samples if sample["value"] is None]
    source_records = [
        {
            "period": f"2005-{granule.month}",
            "source_class": "synthetic_fixture" if granule.synthetic else "verified_nasa_granule",
            "granule_id": granule.manifest.get("granule_id"),
            "producer_granule_id": granule.manifest.get("producer_granule_id"),
            "filename": granule.path.name,
            "collection_id": COLLECTION_ID,
            "product": PRODUCT,
            "collection_version": "07",
            "product_version": "V07B",
            "variable_path": VARIABLE_PATH,
            "units": UNITS,
            "sha256": granule.sha256,
            "bytes": granule.path.stat().st_size,
            "manifest_sha256": granule.manifest_sha256,
            "retrieved_at": granule.manifest.get("downloaded_at_utc"),
            "source_metadata_url": granule.manifest["source"].get("granule_metadata"),
        }
        for granule in granules
    ]
    input_fingerprint = {
        "pipeline_version": PIPELINE_VERSION,
        "collection_id": COLLECTION_ID,
        "doi": DOI,
        "point": {
            "selection_id": point["selection_id"],
            "latitude": actual_coordinates["latitude"],
            "longitude": actual_coordinates["longitude"],
            "latitude_index": actual_coordinates["latitude_index"],
            "longitude_index": actual_coordinates["longitude_index"],
        },
        "granule_sha256s": [record["sha256"] for record in source_records],
        "manifest_sha256s": [record["manifest_sha256"] for record in source_records],
    }
    is_synthetic = _resolve_synthetic_flag([granule.synthetic for granule in granules])
    dataset_id = dataset_id_for_input_fingerprint(input_fingerprint)
    fill = samples[0]["fill_value"]
    qa_fields = sorted({field for sample in samples for field in sample["qa_source_fields_present"]})
    snapshot: dict[str, Any] = {
        "snapshot_schema_version": "1.0.0",
        "dataset_id": dataset_id,
        "synthetic": is_synthetic,
        "product": {
            "product_id": PRODUCT,
            "short_name": PRODUCT,
            "collection_id": COLLECTION_ID,
            "collection_version": "07",
            "product_version": "V07B",
            "doi": DOI,
            "variable": "precipitation",
            "variable_path": VARIABLE_PATH,
            "quantity": "monthly_mean_rate",
            "unit": UNITS,
        },
        "requested_coverage": {"start": "2005-01", "end": "2005-12", "end_inclusive": True},
        "available_coverage": {"start": "2005-01", "end": "2005-12"},
        "coverage": {
            "expected_periods": 12,
            "present_periods": len(samples),
            "valid_periods": sum(value is not None for value in values),
            "missing_periods": missing_periods,
            "spatial_coverage": None,
        },
        "data_state": "available_with_gaps" if missing_periods else "available",
        "series": [
            {
                "date": f"2005-{sample['month']}-01",
                "value": sample["value"],
                "quality": {
                    "state": sample["state"],
                    "provider_flags": [],
                    "missing_reason": sample["missing_reason"],
                },
            }
            for sample in samples
        ],
        "spatial_aggregation": {
            "support_type": "point_sample",
            "approval_state": "not_assessed",
            "method": None,
            "area_weighted": None,
            "weighting_reference": None,
            "mask_version": None,
            "point": {
                "cell_id": f"IMERG-v07b-center-lon{actual_coordinates['longitude_index']}-lat{actual_coordinates['latitude_index']}",
                "latitude": actual_coordinates["latitude"],
                "longitude": actual_coordinates["longitude"],
            },
        },
        "quality": {
            "source_flag_fields": qa_fields,
            "provider_flags_applied": False,
            "source_missing_attributes": {
                "fill_value": fill,
                "missing_value": samples[0]["code_missing_value"],
                "scale_factor": None,
                "add_offset": None,
            },
            "finite_non_fill_filter_applied": True,
            "verification_state": "basic_checks_only",
            "mask_applied": None,
            "qa_checks": [],
            "uninterpreted_provider_fields": qa_fields,
        },
        "provenance": {
            "agency": None if is_synthetic else "NASA",
            "distributor": "synthetic test fixture" if is_synthetic else "GES DISC via Earthdata CMR",
            "collection_id": COLLECTION_ID,
            "doi": DOI,
            "source_records": source_records,
            "point_selection": point,
            "transformations": [],
            "processing": {
                "pipeline": "research.build_ful116_snapshot",
                "pipeline_version": PIPELINE_VERSION,
                "code_sha256": sha256_file(Path(__file__)),
                "spatial_method": "one native IMERG grid-cell center from the FUL-105 panel; no aggregation, reprojection, interpolation, or QA filter",
            },
            "preview": preview,
        },
        "limitations": [
            "Exploratory sample; not a basin mean or validated regional series.",
            "IMERG precipitation remains a monthly mean rate in mm/hr; it is not a monthly accumulation.",
            "Provider QA fields are inventoried but not interpreted or applied; QA remains unassessed.",
            "The spatial preview is a native-grid bounding-box crop, not a basin polygon mask.",
            "No anomaly, trend, inference, or completeness claim beyond the 12 verified source granules is produced.",
        ],
        "values_by_period": [
            {
                "period": f"2005-{sample['month']}",
                "raw_value": sample["value"],
                "state": "finite_nonfill" if sample["value"] is not None else sample["missing_reason"],
                "fill_value": sample["fill_value"],
                "coordinates": sample["coordinates"],
            }
            for sample in samples
        ],
    }
    snapshot["snapshot_sha256"] = snapshot_sha256(snapshot)
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / preview_name
    output_path = output_dir / "imerg_2005_point_snapshot.json"
    snapshot_bytes = canonical_json(snapshot) + b"\n"
    _atomic_write(preview_path, preview_bytes)
    _atomic_write(output_path, snapshot_bytes)
    return snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--point", type=Path, default=DEFAULT_POINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--bbox", default="138,-38,153,-24", help="west,south,east,north; native EPSG:4326 centers"
    )
    args = parser.parse_args()
    try:
        bbox = tuple(float(item.strip()) for item in args.bbox.split(","))
        if len(bbox) != 4:
            raise ValueError("BBox debe contener cuatro números")
        snapshot = build_snapshot(args.input_dir, args.point, args.output_dir, bbox=bbox)
        print(json.dumps({
            "status": "success",
            "dataset_id": snapshot["dataset_id"],
            "snapshot_sha256": snapshot["snapshot_sha256"],
            "periods": snapshot["coverage"]["present_periods"],
            "valid_periods": snapshot["coverage"]["valid_periods"],
            "missing_periods": snapshot["coverage"]["missing_periods"],
            "point": snapshot["spatial_aggregation"]["point"],
            "output_dir": str(args.output_dir),
        }, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - sanitized local CLI summary
        print(json.dumps({"status": "error", "error": type(exc).__name__, "message": str(exc)}, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

