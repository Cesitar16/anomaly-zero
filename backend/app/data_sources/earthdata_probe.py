"""Bounded, non-aggregating NASA Earthdata discovery and sample inspection."""

from __future__ import annotations

import argparse
import calendar
import hashlib
import json
import math
import os
import re
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

import numpy as np
import xarray as xr

DEFAULT_BBOX = (138.0, -38.0, 153.0, -24.0)
DEFAULT_MONTH = "2005-01"
DEFAULT_LIMIT = 3
DEFAULT_MAX_MIB = 64.0
MAX_DISCOVERY_LIMIT = 10
MAX_DOWNLOAD_MIB = 128.0
MIB_BYTES = 1024**2
SAMPLE_RELATIVE_DIR = Path("data/raw/nasa/gldas")
PREVIEW_LIMIT = 16


@dataclass(frozen=True)
class Product:
    key: str
    short_name: str
    version: str
    variable: str
    expected_collection_id: str
    doi: str


PRODUCTS = (
    Product(
        "merra2",
        "M2TMNXSLV",
        "5.12.4",
        "T2M",
        "C1276812859-GES_DISC",
        "10.5067/AP1B0BA5PD2K",
    ),
    Product(
        "imerg_final",
        "GPM_3IMERGM",
        "07",
        "precipitation",
        "C2723754851-GES_DISC",
        "10.5067/GPM/IMERG/3B-MONTH/07",
    ),
    Product(
        "gldas_noah_monthly",
        "GLDAS_NOAH025_M",
        "2.1",
        "SoilMoi0_10cm_inst",
        "C1342986036-GES_DISC",
        "10.5067/SXAVCZFAQLNO",
    ),
)
GLDAS = PRODUCTS[2]


class ProbeError(RuntimeError):
    """An expected probe failure with a safe, local message."""

    def __init__(self, message: str, stage: str | None = None) -> None:
        super().__init__(message)
        self.stage = stage


def month_bounds(month: str) -> tuple[str, str]:
    """Return inclusive UTC bounds for a month in the MVP period."""
    try:
        year_text, month_text = month.split("-", maxsplit=1)
        year, month_number = int(year_text), int(month_text)
        if f"{year:04d}-{month_number:02d}" != month:
            raise ValueError
        if not 2005 <= year <= 2024 or not 1 <= month_number <= 12:
            raise ValueError
    except ValueError as exc:
        raise ProbeError(
            "month must be YYYY-MM within 2005-01 through 2024-12"
        ) from exc
    last_day = calendar.monthrange(year, month_number)[1]
    return (
        f"{month}-01T00:00:00Z",
        f"{year:04d}-{month_number:02d}-{last_day:02d}T23:59:59Z",
    )


def parse_bbox(value: str) -> tuple[float, float, float, float]:
    """Parse a bbox without implying pixel clipping."""
    try:
        bbox = tuple(float(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bbox must contain four numbers") from exc
    if len(bbox) != 4:
        raise argparse.ArgumentTypeError("bbox must contain west,south,east,north")
    west, south, east, north = bbox
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise argparse.ArgumentTypeError("bbox coordinates are outside valid bounds")
    return bbox  # type: ignore[return-value]


def _value(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _collection_record(collection: Any) -> dict[str, Any]:
    meta = _value(collection, "meta", {}) or {}
    umm = _value(collection, "umm", {}) or {}
    return {
        "concept_id": _value(collection, "concept_id") or meta.get("concept-id"),
        "short_name": umm.get("ShortName"),
        "version": _value(collection, "version") or umm.get("Version"),
    }


def _granule_record(granule: Any) -> dict[str, Any]:
    meta = _value(granule, "meta", {}) or {}
    umm = _value(granule, "umm", {}) or {}
    temporal = umm.get("TemporalExtent", {}).get("RangeDateTime", {})
    size_mib = _value(granule, "size")
    try:
        size_mib = float(size_mib) if size_mib is not None else None
    except (TypeError, ValueError):
        size_mib = None
    return {
        "granule_id": meta.get("concept-id"),
        "producer_granule_id": umm.get("GranuleUR"),
        "collection_id": meta.get("collection-concept-id"),
        "time_start": temporal.get("BeginningDateTime"),
        "time_end": temporal.get("EndingDateTime"),
        "size_mib": size_mib,
    }


def _http_status(exc: Exception) -> int | None:
    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    response = getattr(exc, "response", None)
    status = status or getattr(response, "status_code", None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def safe_error(exc: Exception) -> dict[str, Any]:
    """Describe errors without emitting raw exception text or request URLs."""
    result: dict[str, Any] = {"type": type(exc).__name__}
    stage = getattr(exc, "stage", None)
    if stage is not None:
        result["stage"] = stage
    status = _http_status(exc)
    if status is not None:
        result["http_status"] = status
    result["message"] = (
        str(exc)
        if isinstance(exc, ProbeError)
        else "NASA request failed; raw provider details were suppressed."
    )
    return result


def discover_product(
    product: Product,
    month: str,
    limit: int,
    bbox: tuple[float, float, float, float],
    client: Any,
) -> dict[str, Any]:
    start, end = month_bounds(month)
    result: dict[str, Any] = {
        "product": asdict(product),
        "month": month,
        "bbox": list(bbox),
        "bbox_semantics": "file selection only; no pixel clipping",
        "status": "not_found",
        "collections": [],
        "granules": [],
    }
    try:
        collections = client.search_datasets(
            count=10, short_name=product.short_name, debug=False
        )
    except Exception as exc:  # noqa: BLE001 - suppress provider details and signed links
        result.update(status="error", error=safe_error(exc))
        return result

    records = [_collection_record(collection) for collection in collections]
    result["collections"] = records
    matching = [
        record for record in records if str(record["version"]) == product.version
    ]
    if not matching:
        result["status"] = (
            "collection_not_found" if not records else "version_not_found"
        )
        return result

    result["status"] = "no_granules"
    for collection in collections:
        record = _collection_record(collection)
        if str(record["version"]) != product.version or not record["concept_id"]:
            continue
        try:
            granules = client.search_data(
                count=limit - len(result["granules"]),
                collection_concept_id=record["concept_id"],
                short_name=product.short_name,
                version=product.version,
                temporal=(start, end),
                bounding_box=bbox,
            )
        except Exception as exc:  # noqa: BLE001 - continue other product collections safely
            result.setdefault("errors", []).append(safe_error(exc))
            continue
        result["granules"].extend(_granule_record(granule) for granule in granules)
        if len(result["granules"]) >= limit:
            break
    result["granules"] = result["granules"][:limit]
    if result["granules"]:
        result["status"] = "found"
    elif result.get("errors"):
        result["status"] = "error"
    return result


def discover(
    month: str = DEFAULT_MONTH,
    limit: int = DEFAULT_LIMIT,
    bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
    client: Any | None = None,
) -> dict[str, Any]:
    month_bounds(month)
    if not 1 <= limit <= MAX_DISCOVERY_LIMIT:
        raise ProbeError(f"limit must be between 1 and {MAX_DISCOVERY_LIMIT}")
    if client is None:
        import earthaccess as client_module

        client = client_module
    return {
        "queried_at_utc": datetime.now(UTC).isoformat(),
        "authentication_required": False,
        "results": [
            discover_product(product, month, limit, bbox, client)
            for product in PRODUCTS
        ],
    }


def _safe_text(value: Any) -> Any:
    if isinstance(value, np.generic):
        return _safe_text(value.item())
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, np.ndarray):
        return [_safe_text(item) for item in value.reshape(-1)[:PREVIEW_LIMIT]]
    if isinstance(value, (list, tuple)):
        return [_safe_text(item) for item in value[:PREVIEW_LIMIT]]
    if isinstance(value, Mapping):
        return {str(key): _safe_text(item) for key, item in value.items()}
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str) and value.startswith(("https://", "http://")):
        parts = urlsplit(value)
        return urlunsplit((parts.scheme, parts.hostname or "", parts.path, "", ""))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _is_missing(value: Any, sentinels: list[Any]) -> bool:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return False
    if not math.isfinite(numeric):
        return True
    for sentinel in sentinels:
        try:
            candidate = float(sentinel)
            if (math.isnan(candidate) and math.isnan(numeric)) or numeric == candidate:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _preview_values(variable: Any) -> dict[str, Any]:
    indexers = {
        dimension: slice(0, min(2, size)) for dimension, size in variable.sizes.items()
    }
    values = np.asarray(variable.isel(indexers).values).reshape(-1)[:PREVIEW_LIMIT]
    sentinels = [variable.attrs.get("_FillValue"), variable.attrs.get("missing_value")]
    sentinels = [value for value in sentinels if value is not None]
    preview = [
        None if _is_missing(value, sentinels) else _safe_text(value) for value in values
    ]
    return {"raw_subset_values_null_for_missing": preview, "subset_count": len(preview)}


def _attributes(attrs: Mapping[str, Any]) -> dict[str, Any]:
    return {str(name): _safe_text(value) for name, value in attrs.items()}


def inspect_netcdf(path: Path | str, variable_name: str) -> dict[str, Any]:
    """Inspect source metadata without CF decoding, scaling, or aggregation."""
    file_path = Path(path)
    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise ProbeError("dataset file is missing or empty")
    with file_path.open("rb") as stream:
        prefix = stream.read(512).lstrip().lower()
    if prefix.startswith((b"<html", b"<!doctype html")):
        raise ProbeError("download is an HTML response, not a dataset")
    try:
        dataset = xr.open_dataset(
            file_path,
            engine="netcdf4",
            decode_cf=False,
            mask_and_scale=False,
            decode_times=False,
        )
    except Exception as exc:
        raise ProbeError("file could not be opened as NetCDF4") from exc

    with dataset:
        if variable_name not in dataset.data_vars:
            raise ProbeError(f"expected variable {variable_name} is absent")
        variable = dataset[variable_name]
        coordinates: dict[str, Any] = {}
        for name, coordinate in dataset.coords.items():
            values = np.asarray(coordinate.values).reshape(-1)
            coordinates[name] = {
                "dimensions": list(coordinate.dims),
                "size": int(values.size),
                "attributes": _attributes(coordinate.attrs),
                "first_values": _safe_text(values[:3]),
                "last_values": _safe_text(values[-3:]),
            }
        quality_candidates = [
            name
            for name in dataset.data_vars
            if any(token in name.lower() for token in ("quality", "flag", "error"))
        ]
        return {
            "status": "opened",
            "format": "NetCDF4",
            "reader": {
                "engine": "netcdf4",
                "decode_cf": False,
                "mask_and_scale": False,
                "decode_times": False,
                "automatic_transformations_applied": [],
            },
            "dataset_attributes": _attributes(dataset.attrs),
            "dimensions": {name: int(size) for name, size in dataset.sizes.items()},
            "coordinates": coordinates,
            "variable": {
                "name": variable_name,
                "dimensions": list(variable.dims),
                "shape": list(variable.shape),
                "dtype": str(variable.dtype),
                "attributes": _attributes(variable.attrs),
                "units": _safe_text(variable.attrs.get("units")),
                "fill_value": _safe_text(variable.attrs.get("_FillValue")),
                "missing_value": _safe_text(variable.attrs.get("missing_value")),
                "scale_factor": _safe_text(variable.attrs.get("scale_factor")),
                "add_offset": _safe_text(variable.attrs.get("add_offset")),
                "preview": _preview_values(variable),
            },
            "quality_variable_candidates": quality_candidates,
            "limitations": [
                "Only a tiny raw subset was read; no spatial or temporal aggregation was calculated.",
                "QA flags are listed by name only and have not been interpreted.",
                "The bbox selected the granule; the file remains a global grid.",
            ],
        }


@contextmanager
def _quiet_earthaccess() -> Iterator[None]:
    import logging

    logger = logging.getLogger("earthaccess")
    old_disabled = logger.disabled
    logger.disabled = True
    try:
        yield
    finally:
        logger.disabled = old_disabled


def _collection_for_download(client: Any, month: str) -> tuple[Any, Any]:
    collections = client.search_datasets(
        count=10, short_name=GLDAS.short_name, debug=False
    )
    matching = [
        collection
        for collection in collections
        if str(_collection_record(collection)["version"]) == GLDAS.version
    ]
    start, end = month_bounds(month)
    for collection in matching:
        collection_id = _collection_record(collection)["concept_id"]
        granules = client.search_data(
            count=1,
            collection_concept_id=collection_id,
            short_name=GLDAS.short_name,
            version=GLDAS.version,
            temporal=(start, end),
            bounding_box=DEFAULT_BBOX,
        )
        if granules:
            return collection, granules[0]
    raise ProbeError("no GLDAS granule found for the selected month and bbox")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _publish_staged_sample(
    staged_file: Path,
    staged_manifest: Path,
    destination: Path,
    manifest_path: Path,
) -> None:
    """Publish validated files without replacing an existing sample.

    Each no-overwrite publication is atomic on its filesystem, but publishing
    the pair is not. If the manifest publication fails after the data file, try
    to remove only the data file this call created so a retry is possible.
    """
    data_published = False
    try:
        _publish_no_replace(staged_file, destination)
        data_published = True
        _publish_no_replace(staged_manifest, manifest_path)
    except OSError as exc:
        if data_published:
            try:
                destination.unlink()
            except OSError as cleanup_exc:
                raise ProbeError(
                    "manifest publication failed and the new sample file could not be removed",
                    stage="manifest",
                ) from cleanup_exc
        raise ProbeError(
            "could not publish the validated sample and manifest", stage="manifest"
        ) from exc


def _publish_no_replace(source: Path, destination: Path) -> None:
    """Atomically move/link one staged file without overwriting a destination."""
    if os.name == "nt":
        os.rename(source, destination)
    else:
        os.link(source, destination)


def download_gldas(
    month: str = DEFAULT_MONTH,
    max_mib: float = DEFAULT_MAX_MIB,
    auth_strategy: str = "netrc",
    persist_auth: bool = False,
    output_dir: Path | str = SAMPLE_RELATIVE_DIR,
    client: Any | None = None,
) -> dict[str, Any]:
    """Download one size-checked GLDAS granule, open it, and write a safe manifest."""
    month_bounds(month)
    if not 0 < max_mib <= MAX_DOWNLOAD_MIB:
        raise ProbeError(
            f"max-mib must be greater than 0 and at most {MAX_DOWNLOAD_MIB}"
        )
    if auth_strategy not in {"netrc", "environment", "interactive"}:
        raise ProbeError("auth-strategy must be netrc, environment, or interactive")
    if client is None:
        import earthaccess as client_module

        client = client_module

    with _quiet_earthaccess():
        try:
            collection, granule = _collection_for_download(client, month)
        except ProbeError as exc:
            exc.stage = exc.stage or "catalog"
            raise
        except Exception as exc:
            raise ProbeError(
                f"catalog lookup failed ({type(exc).__name__})", stage="catalog"
            ) from exc
        record = _granule_record(granule)
        expected_size_mib = record["size_mib"]
        if expected_size_mib is None or expected_size_mib <= 0:
            raise ProbeError("CMR did not report a positive expected file size")
        expected_size_bytes = math.ceil(expected_size_mib * MIB_BYTES)
        download_limit_bytes = math.floor(max_mib * MIB_BYTES)
        if expected_size_bytes > download_limit_bytes:
            raise ProbeError("CMR expected size exceeds the configured download limit")

        producer_id = record["producer_granule_id"] or ""
        filename = Path(producer_id.rsplit(":", maxsplit=1)[-1]).name
        if not re.fullmatch(r"GLDAS_NOAH025_M\.A\d{6}\.021\.nc4", filename):
            raise ProbeError(
                "CMR granule name does not match the expected GLDAS monthly format"
            )
        destination_dir = Path(output_dir)
        destination = destination_dir / filename
        manifest_path = destination_dir / f"{filename}.manifest.json"
        if destination.exists() or manifest_path.exists():
            raise ProbeError("sample or manifest already exists; refusing to overwrite")
        try:
            auth = client.login(strategy=auth_strategy, persist=persist_auth)
        except Exception as exc:
            raise ProbeError(
                f"Earthdata authentication failed ({type(exc).__name__})",
                stage="authentication",
            ) from exc
        if getattr(auth, "authenticated", False) is not True:
            raise ProbeError(
                "Earthdata authentication did not report success",
                stage="authentication",
            )
        destination_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix=".earthdata-probe-", dir=destination_dir
        ) as tmp:
            try:
                paths = client.download(
                    [granule], local_path=tmp, threads=1, show_progress=False
                )
            except Exception as exc:
                raise ProbeError(
                    f"file transfer failed ({type(exc).__name__})", stage="download"
                ) from exc
            if len(paths) != 1:
                raise ProbeError("download did not return exactly one file")
            staged_file = Path(paths[0])
            if not staged_file.is_file():
                raise ProbeError("download result is not a file")
            if staged_file.name != filename:
                raise ProbeError(
                    "downloaded filename does not match the selected granule"
                )
            byte_count = staged_file.stat().st_size
            if byte_count <= 0 or byte_count > download_limit_bytes:
                raise ProbeError(
                    "download size is empty or exceeds the configured limit"
                )
            with staged_file.open("rb") as stream:
                prefix = stream.read(512).lstrip().lower()
            if prefix.startswith((b"<html", b"<!doctype html")):
                raise ProbeError("provider returned HTML instead of a dataset")
            inspection = inspect_netcdf(staged_file, GLDAS.variable)
            digest = _sha256(staged_file)
            collection_id = (
                record["collection_id"] or _collection_record(collection)["concept_id"]
            )
            granule_id = record["granule_id"]
            manifest = {
                "manifest_version": 1,
                "product": {
                    "short_name": GLDAS.short_name,
                    "version": GLDAS.version,
                    "variable": GLDAS.variable,
                    "doi": GLDAS.doi,
                },
                "collection_id": collection_id,
                "granule_id": granule_id,
                "producer_granule_id": producer_id,
                "filename": filename,
                "source": {
                    "provider": "NASA GES DISC via Earthdata CMR",
                    "collection_metadata": f"https://cmr.earthdata.nasa.gov/search/concepts/{collection_id}.umm_json",
                    "granule_metadata": f"https://cmr.earthdata.nasa.gov/search/concepts/{granule_id}.umm_json",
                },
                "period": {
                    "month": month,
                    "start": record["time_start"],
                    "end": record["time_end"],
                },
                "downloaded_at_utc": datetime.now(UTC).isoformat(),
                "stages": {
                    "authentication": {"status": "succeeded"},
                    "download": {"status": "succeeded", "files": 1},
                    "read": {"status": "succeeded", "format": "NetCDF4"},
                    "inspection": {"status": "succeeded", "variable": GLDAS.variable},
                },
                "expected_size_mib": expected_size_mib,
                "expected_size_bytes": expected_size_bytes,
                "download_limit_mib": max_mib,
                "download_limit_bytes": download_limit_bytes,
                "bytes": byte_count,
                "sha256": digest,
                "relative_path": filename,
                "inspection": inspection,
            }
            staged_manifest = Path(tmp) / f"{filename}.manifest.json"
            try:
                staged_manifest.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                validated_manifest = json.loads(
                    staged_manifest.read_text(encoding="utf-8")
                )
                if (
                    validated_manifest["bytes"] != byte_count
                    or validated_manifest["sha256"] != digest
                    or validated_manifest["relative_path"] != filename
                ):
                    raise ValueError("manifest does not match the staged sample")
            except (OSError, ValueError, KeyError) as exc:
                raise ProbeError(
                    "could not prepare or validate the sample manifest",
                    stage="manifest",
                ) from exc
            _publish_staged_sample(
                staged_file, staged_manifest, destination, manifest_path
            )

    return {
        "status": "downloaded_and_opened",
        "file": str(destination),
        "manifest": str(manifest_path),
        "sha256": digest,
        "bytes": byte_count,
        "inspection": inspection,
    }


def _emit(payload: dict[str, Any], exit_code: int = 0) -> int:
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return exit_code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    discover_parser = subparsers.add_parser(
        "discover", help="query one bounded CMR month"
    )
    discover_parser.add_argument("--month", default=DEFAULT_MONTH)
    discover_parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    discover_parser.add_argument("--bbox", type=parse_bbox, default=DEFAULT_BBOX)
    inspect_parser = subparsers.add_parser(
        "inspect", help="inspect one local NetCDF4 file"
    )
    inspect_parser.add_argument("file", type=Path)
    inspect_parser.add_argument("--variable", default=GLDAS.variable)
    download_parser = subparsers.add_parser(
        "download-gldas", help="download one GLDAS monthly file"
    )
    download_parser.add_argument("--month", default=DEFAULT_MONTH)
    download_parser.add_argument("--max-mib", type=float, default=DEFAULT_MAX_MIB)
    download_parser.add_argument(
        "--auth-strategy",
        choices=("netrc", "environment", "interactive"),
        default="netrc",
    )
    download_parser.add_argument("--persist-auth", action="store_true")

    args = parser.parse_args(argv)
    try:
        if args.command == "discover":
            result = discover(args.month, args.limit, args.bbox)
            failed = any(item["status"] == "error" for item in result["results"])
            return _emit(result, 2 if failed else 0)
        if args.command == "inspect":
            return _emit(inspect_netcdf(args.file, args.variable))
        return _emit(
            download_gldas(
                args.month, args.max_mib, args.auth_strategy, args.persist_auth
            )
        )
    except Exception as exc:  # noqa: BLE001 - never print raw provider exception details
        return _emit({"status": "error", "error": safe_error(exc)}, 2)


if __name__ == "__main__":
    raise SystemExit(main())

