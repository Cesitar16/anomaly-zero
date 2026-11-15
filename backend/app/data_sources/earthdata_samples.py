"""Bounded MERRA-2 and IMERG downloads with raw inspection for configured products."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import h5py
import numpy as np

from backend.app.data_sources import earthdata_probe as probe

PRODUCTS = {product.key: product for product in probe.PRODUCTS}
DOWNLOADABLE = {"merra2", "imerg_final"}


def _hdf5_dimensions(dataset: h5py.Dataset) -> list[str | None]:
    labels = [dataset.dims[i].label or None for i in range(dataset.ndim)]
    if all(label is None for label in labels):
        names = dataset.attrs.get("DimensionNames")
        if isinstance(names, bytes):
            names = names.decode("utf-8", errors="replace")
        if isinstance(names, str):
            declared = [name.strip() for name in names.split(",")]
            if len(declared) == dataset.ndim and all(declared):
                return declared
    return labels


def _is_imerg_missing(value: Any, sentinel: Any) -> bool:
    if probe._is_missing(value, [sentinel] if sentinel is not None else []):
        return True
    try:
        return sentinel is not None and bool(
            np.isclose(float(value), float(sentinel), rtol=1e-6, atol=1e-8)
        )
    except (TypeError, ValueError):
        return False


def inspect_product(path: Path | str, product_key: str) -> dict[str, Any]:
    product = PRODUCTS.get(product_key)
    if product is None:
        raise probe.ProbeError("unknown product")
    file_path = Path(path)
    if not file_path.is_file() or file_path.stat().st_size == 0:
        raise probe.ProbeError("dataset file is missing or empty")
    with file_path.open("rb") as stream:
        prefix = stream.read(512).lstrip().lower()
    if prefix.startswith((b"<html", b"<!doctype html")):
        raise probe.ProbeError("download is an HTML response, not a dataset")

    if product_key in {"gldas_noah_monthly", "merra2"}:
        return probe.inspect_netcdf(file_path, product.variable)
    if not h5py.is_hdf5(file_path):
        raise probe.ProbeError("file could not be opened as HDF5")

    with h5py.File(file_path, "r") as h5:
        variable_path = "Grid/precipitation"
        if variable_path not in h5 or not isinstance(h5[variable_path], h5py.Dataset):
            raise probe.ProbeError("expected HDF5 dataset Grid/precipitation is absent")
        variable = h5[variable_path]
        quality_paths: list[str] = []
        dataset_paths: list[str] = []

        def collect(name: str, item: Any) -> None:
            if not isinstance(item, h5py.Dataset):
                return
            dataset_paths.append(name)
            if any(token in name.lower() for token in ("quality", "flag", "error")):
                quality_paths.append(name)

        h5.visititems(collect)
        data = np.asarray(variable[tuple(slice(0, min(2, n)) for n in variable.shape)])
        attrs = {str(k): probe._safe_text(v) for k, v in variable.attrs.items()}
        fill = attrs.get("_FillValue", attrs.get("missing_value"))
        preview = [
            None if _is_imerg_missing(value, fill) else probe._safe_text(value)
            for value in data.reshape(-1)[: probe.PREVIEW_LIMIT]
        ]
        coordinate_info: dict[str, Any] = {}
        for name in (
            "Grid/time",
            "Grid/lat",
            "Grid/lon",
            "Grid/lat_bnds",
            "Grid/lon_bnds",
        ):
            if name in h5 and isinstance(h5[name], h5py.Dataset):
                coord = h5[name]
                values = np.asarray(coord[...]).reshape(-1)
                coordinate_info[name] = {
                    "dimensions": [
                        _hdf5_dimensions(coord)[i] for i in range(coord.ndim)
                    ],
                    "size": int(values.size),
                    "attributes": {
                        str(k): probe._safe_text(v) for k, v in coord.attrs.items()
                    },
                    "first_values": probe._safe_text(values[:3]),
                    "last_values": probe._safe_text(values[-3:]),
                }
        return {
            "status": "opened",
            "format": "HDF5",
            "reader": {
                "engine": "h5py",
                "decode_cf": False,
                "mask_and_scale": False,
                "decode_times": False,
                "automatic_transformations_applied": [],
            },
            "groups": [
                name for name, item in h5.items() if isinstance(item, h5py.Group)
            ],
            "dataset_attributes": {
                str(k): probe._safe_text(v) for k, v in h5.attrs.items()
            },
            "group_attributes": {
                name: {str(k): probe._safe_text(v) for k, v in item.attrs.items()}
                for name, item in h5.items()
                if isinstance(item, h5py.Group)
            },
            "dataset_paths": dataset_paths,
            "dimensions": {f"axis_{i}": int(n) for i, n in enumerate(variable.shape)},
            "coordinates": coordinate_info,
            "variable": {
                "name": variable_path,
                "dimensions": [
                    _hdf5_dimensions(variable)[i] for i in range(variable.ndim)
                ],
                "shape": list(variable.shape),
                "dtype": str(variable.dtype),
                "attributes": attrs,
                "units": attrs.get("units"),
                "fill_value": fill,
                "missing_value": attrs.get("missing_value"),
                "scale_factor": attrs.get("scale_factor"),
                "add_offset": attrs.get("add_offset"),
                "preview": {
                    "raw_subset_values_null_for_missing": preview,
                    "subset_count": len(preview),
                },
            },
            "quality_variable_candidates": quality_paths,
            "limitations": [
                "A tiny raw subset was read; no temporal or spatial aggregation was calculated.",
                "Missing HDF5 labels fall back to DimensionNames; spatial QA validates names against coordinate sizes.",
                "QA candidates are reported by path only and have not been interpreted.",
            ],
        }


def download_product(
    product_key: str,
    month: str = probe.DEFAULT_MONTH,
    max_mib: float = probe.DEFAULT_MAX_MIB,
    auth_strategy: str = "netrc",
    persist_auth: bool = False,
    output_dir: Path | str = Path("data/raw/nasa"),
    client: Any | None = None,
) -> dict[str, Any]:
    if product_key not in DOWNLOADABLE:
        raise probe.ProbeError(
            "only MERRA-2 and IMERG are downloadable by this command"
        )
    product = PRODUCTS[product_key]
    probe.month_bounds(month)
    if not 0 < max_mib <= probe.MAX_DOWNLOAD_MIB:
        raise probe.ProbeError(
            f"max-mib must be greater than 0 and at most {probe.MAX_DOWNLOAD_MIB}"
        )
    if auth_strategy not in {"netrc", "environment", "interactive"}:
        raise probe.ProbeError(
            "auth-strategy must be netrc, environment, or interactive"
        )
    if client is None:
        import earthaccess as client
    with probe._quiet_earthaccess():
        try:
            collections = client.search_datasets(
                count=10, short_name=product.short_name, debug=False
            )
        except Exception as exc:
            raise probe.ProbeError(
                f"catalog lookup failed ({type(exc).__name__})", stage="catalog"
            ) from exc
        matches = [
            collection
            for collection in collections
            if str(probe._collection_record(collection)["version"]) == product.version
            and probe._collection_record(collection)["concept_id"]
            == product.expected_collection_id
        ]
        if not matches:
            raise probe.ProbeError(
                "NASA catalog identity/version differs from the configured product",
                stage="catalog",
            )
        start, end = probe.month_bounds(month)
        try:
            granules = client.search_data(
                count=1,
                collection_concept_id=product.expected_collection_id,
                short_name=product.short_name,
                version=product.version,
                temporal=(start, end),
                bounding_box=probe.DEFAULT_BBOX,
            )
        except Exception as exc:
            raise probe.ProbeError(
                f"granule lookup failed ({type(exc).__name__})", stage="catalog"
            ) from exc
        if not granules:
            raise probe.ProbeError(
                "no granule found for the selected product, month, and bbox",
                stage="catalog",
            )
        granule = granules[0]
        record = probe._granule_record(granule)
        expected_mib = record["size_mib"]
        if expected_mib is None or expected_mib <= 0:
            raise probe.ProbeError(
                "CMR did not report a positive expected file size", stage="catalog"
            )
        expected_bytes = math.ceil(expected_mib * probe.MIB_BYTES)
        limit_bytes = math.floor(max_mib * probe.MIB_BYTES)
        if expected_bytes > limit_bytes:
            raise probe.ProbeError(
                "CMR expected size exceeds the configured download limit",
                stage="catalog",
            )
        producer_id = record["producer_granule_id"] or ""
        filename = Path(producer_id.rsplit(":", maxsplit=1)[-1]).name
        if (
            not filename
            or filename != producer_id.rsplit(":", maxsplit=1)[-1]
            or not re.fullmatch(r"[A-Za-z0-9_.-]+", filename)
        ):
            raise probe.ProbeError("CMR granule name is unsafe", stage="catalog")
        expected_suffix = ".HDF5" if product_key == "imerg_final" else ".nc4"
        if not filename.endswith(expected_suffix):
            raise probe.ProbeError(
                "granule extension does not match the expected format", stage="catalog"
            )

        directory = Path(output_dir) / product_key
        destination = directory / filename
        manifest_path = directory / f"{filename}.manifest.json"
        if destination.exists() or manifest_path.exists():
            raise probe.ProbeError(
                "sample or manifest already exists; refusing to overwrite"
            )
        try:
            auth = client.login(strategy=auth_strategy, persist=persist_auth)
        except Exception as exc:
            raise probe.ProbeError(
                f"Earthdata authentication failed ({type(exc).__name__})",
                stage="authentication",
            ) from exc
        if getattr(auth, "authenticated", False) is not True:
            raise probe.ProbeError(
                "Earthdata authentication did not report success",
                stage="authentication",
            )
        directory.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(
            prefix=".earthdata-sample-", dir=directory
        ) as temp_dir:
            try:
                downloaded = client.download(
                    [granule], local_path=temp_dir, threads=1, show_progress=False
                )
            except Exception as exc:
                raise probe.ProbeError(
                    f"file transfer failed ({type(exc).__name__})", stage="download"
                ) from exc
            if len(downloaded) != 1:
                raise probe.ProbeError(
                    "download did not return exactly one file", stage="download"
                )
            staged_file = Path(downloaded[0])
            if not staged_file.is_file() or staged_file.name != filename:
                raise probe.ProbeError(
                    "download result does not match the selected granule",
                    stage="download",
                )
            byte_count = staged_file.stat().st_size
            if byte_count <= 0 or byte_count > limit_bytes:
                raise probe.ProbeError(
                    "download size is empty or exceeds the configured limit",
                    stage="download",
                )
            inspection = inspect_product(staged_file, product_key)
            digest = probe._sha256(staged_file)
            manifest = {
                "manifest_version": 1,
                "product": {
                    "key": product.key,
                    "short_name": product.short_name,
                    "version": product.version,
                    "variable": product.variable,
                    "doi": product.doi,
                },
                "collection_id": product.expected_collection_id,
                "granule_id": record["granule_id"],
                "producer_granule_id": producer_id,
                "filename": filename,
                "source": {
                    "provider": "NASA GES DISC via Earthdata CMR",
                    "collection_metadata": f"https://cmr.earthdata.nasa.gov/search/concepts/{product.expected_collection_id}.umm_json",
                    "granule_metadata": f"https://cmr.earthdata.nasa.gov/search/concepts/{record['granule_id']}.umm_json",
                },
                "period": {
                    "month": month,
                    "start": record["time_start"],
                    "end": record["time_end"],
                },
                "downloaded_at_utc": datetime.now(UTC).isoformat(),
                "expected_size_mib": expected_mib,
                "expected_size_bytes": expected_bytes,
                "download_limit_mib": max_mib,
                "download_limit_bytes": limit_bytes,
                "bytes": byte_count,
                "sha256": digest,
                "relative_path": os.path.relpath(destination.resolve(), Path.cwd()),
                "relative_path_base": str(Path.cwd()),
                "inspection": inspection,
            }
            staged_manifest = Path(temp_dir) / f"{filename}.manifest.json"
            try:
                staged_manifest.write_text(
                    json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
                verified = json.loads(staged_manifest.read_text(encoding="utf-8"))
                if verified["bytes"] != byte_count or verified["sha256"] != digest:
                    raise ValueError("manifest does not match staged file")
            except (OSError, ValueError, KeyError) as exc:
                raise probe.ProbeError(
                    "could not prepare or validate the sample manifest",
                    stage="manifest",
                ) from exc
            probe._publish_staged_sample(
                staged_file, staged_manifest, destination, manifest_path
            )

    return {
        "status": "downloaded_and_opened",
        "product": product_key,
        "file": str(destination),
        "manifest": str(manifest_path),
        "sha256": digest,
        "bytes": byte_count,
        "inspection": inspection,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("product", choices=sorted(DOWNLOADABLE))
    parser.add_argument("--month", default=probe.DEFAULT_MONTH)
    parser.add_argument("--max-mib", type=float, default=probe.DEFAULT_MAX_MIB)
    parser.add_argument(
        "--auth-strategy",
        choices=("netrc", "environment", "interactive"),
        default="netrc",
    )
    parser.add_argument("--persist-auth", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = download_product(
            args.product,
            args.month,
            args.max_mib,
            args.auth_strategy,
            args.persist_auth,
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except Exception as exc:  # noqa: BLE001 - report sanitized command failures
        print(
            json.dumps(
                {"status": "error", "error": probe.safe_error(exc)},
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

