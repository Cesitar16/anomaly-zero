"""Audit local NASA granules against adjacent manifests and native metadata."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

import h5py
from netCDF4 import Dataset, num2date

PRODUCTS: dict[str, dict[str, str]] = {
    "imerg_final": {
        "short_name": "GPM_3IMERGM", "version": "07", "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
        "collection_id": "C2723754851-GES_DISC", "variable": "precipitation", "path": "Grid/precipitation", "unit": "mm/hr", "suffix": ".HDF5",
    },
    "merra2": {
        "short_name": "M2TMNXSLV", "version": "5.12.4", "doi": "10.5067/AP1B0BA5PD2K",
        "collection_id": "C1276812859-GES_DISC", "variable": "T2M", "path": "T2M", "unit": "K", "suffix": ".nc4",
    },
    "gldas": {
        "short_name": "GLDAS_NOAH025_M", "version": "2.1", "doi": "10.5067/SXAVCZFAQLNO",
        "collection_id": "C1342986036-GES_DISC", "variable": "SoilMoi0_10cm_inst", "path": "SoilMoi0_10cm_inst", "unit": "kg m-2", "suffix": ".nc4",
    },
}
FILENAME_PRODUCT = {
    "3B-MO.MS.MRG.3IMERG.": "imerg_final",
    "MERRA2_": "merra2",
    "GLDAS_NOAH025_M.": "gldas",
}
FILENAME_PERIOD = re.compile(r"(?:\.|A)(20\d{2})(0[1-9]|1[0-2])(?:\d{2})?")


def _product_from_filename(filename: str) -> str | None:
    return next((key for prefix, key in FILENAME_PRODUCT.items() if filename.startswith(prefix)), None)


def _manifest_for(path: Path) -> dict[str, Any]:
    manifest_path = Path(f"{path}.manifest.json")
    if not manifest_path.is_file():
        raise ValueError("manifest_missing")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("manifest_unreadable") from exc
    if not isinstance(manifest, dict):
        raise TypeError("manifest_not_object")
    return manifest


def _manifest_entry(manifest: dict[str, Any], filename: str) -> dict[str, Any]:
    if manifest.get("filename") == filename:
        return manifest
    for entry in manifest.get("samples", []):
        if not isinstance(entry, dict):
            continue
        if entry.get("filename") == filename:
            return entry
    raise ValueError("manifest_filename_mismatch")


def _period_from_filename(filename: str) -> str | None:
    match = FILENAME_PERIOD.search(filename)
    return f"{match.group(1)}-{match.group(2)}" if match else None


def _period_from_manifest(manifest: dict[str, Any]) -> str | None:
    period = manifest.get("period", {})
    month = period.get("month") if isinstance(period, dict) else None
    if not month and isinstance(period, dict) and isinstance(period.get("start"), str):
        month = period["start"][:7]
    if not isinstance(month, str) or not re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])", month):
        return None
    if isinstance(period, dict):
        for key in ("start", "end"):
            bound = period.get(key)
            if bound is not None and (not isinstance(bound, str) or bound[:7] != month):
                return None
    return month


def _declared_integrity(entry: dict[str, Any]) -> tuple[str | None, int | None]:
    expected_hash = entry.get("sha256")
    expected_bytes = entry.get("bytes", entry.get("size_bytes", entry.get("expected_size_bytes")))
    try:
        expected_bytes = int(expected_bytes) if expected_bytes is not None else None
    except (TypeError, ValueError):
        expected_bytes = None
    return expected_hash if isinstance(expected_hash, str) else None, expected_bytes


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_native_payload(path: Path, product: str, expected_month: str | None = None) -> None:
    spec = PRODUCTS[product]
    if product == "imerg_final":
        with h5py.File(path, "r") as handle:
            variable = handle[spec["path"]]
            units = variable.attrs.get("Units", variable.attrs.get("units"))
            if isinstance(units, bytes):
                units = units.decode("utf-8", errors="replace")
            if units != spec["unit"]:
                raise ValueError("native_unit_mismatch")
            header = handle.attrs.get("FileHeader", "")
            if isinstance(header, bytes):
                header = header.decode("utf-8", errors="replace")
            if "ProductVersion=V07B" not in header or "TimeInterval=MONTH" not in header:
                raise ValueError("native_product_metadata_mismatch")
            start = re.search(r"StartGranuleDateTime=(\d{4}-\d{2})", header)
            if not start or (expected_month and start.group(1) != expected_month):
                raise ValueError("native_period_mismatch")
    else:
        with Dataset(path, "r") as handle:
            variable = handle.variables[spec["path"]]
            if getattr(variable, "units", None) != spec["unit"]:
                raise ValueError("native_unit_mismatch")
            if len(variable.shape) != 3 or variable.shape[0] != 1:
                raise ValueError("native_shape_mismatch")
            actual_variable = getattr(variable, "long_name", "")
            if not actual_variable:
                raise ValueError("native_variable_metadata_missing")
            if product == "merra2":
                if getattr(handle, "ShortName", None) != spec["short_name"] or getattr(handle, "VersionID", None) != spec["version"]:
                    raise ValueError("native_product_metadata_mismatch")
                actual_period = str(getattr(handle, "RangeBeginningDate", ""))[:7]
            else:
                if "GLDAS2.1" not in str(getattr(handle, "title", "")):
                    raise ValueError("native_product_metadata_mismatch")
                time_variable = handle.variables.get("time")
                if time_variable is None:
                    raise ValueError("native_time_missing")
                dates = num2date(time_variable[:], time_variable.units, calendar=getattr(time_variable, "calendar", "standard"))
                first = dates[0]
                actual_period = f"{first.year:04d}-{first.month:02d}"
            if expected_month and actual_period != expected_month:
                raise ValueError("native_period_mismatch")


def _validate_identity(
    path: Path,
    manifest: dict[str, Any],
    entry: dict[str, Any],
    product: str,
 ) -> str:
    spec = PRODUCTS[product]
    if manifest.get("synthetic_fixture") is True or entry.get("synthetic_fixture") is True:
        raise ValueError("synthetic_fixture_not_nasa")
    if entry.get("filename") != path.name:
        raise ValueError("manifest_filename_mismatch")
    manifest_product = manifest.get("product", {})
    if not isinstance(manifest_product, dict):
        raise TypeError("manifest_product_section_invalid")
    names = {manifest_product.get("short_name"), manifest_product.get("key")}
    expected_names = {spec["short_name"], product}
    if not names.intersection(expected_names):
        raise ValueError("manifest_product_mismatch")
    version = manifest_product.get("version")
    if product == "imerg_final" and version == "07":
        pass
    elif version != spec["version"]:
        raise ValueError("manifest_version_mismatch")
    doi = manifest_product.get("doi")
    if doi != spec["doi"]:
        raise ValueError("manifest_doi_mismatch")
    if manifest.get("collection_id") != spec["collection_id"]:
        raise ValueError("manifest_collection_mismatch")
    if manifest_product.get("variable") != spec["variable"]:
        raise ValueError("manifest_variable_mismatch")
    producer_id = manifest.get("producer_granule_id")
    producer_prefix = {
        "imerg_final": "GPM_3IMERGM.07:",
        "merra2": "M2TMNXSLV.5.12.4:",
        "gldas": "GLDAS_NOAH025_M.2.1:",
    }[product]
    if producer_id != f"{producer_prefix}{path.name}":
        raise ValueError("manifest_producer_identity_mismatch")
    if not re.fullmatch(r"G\d+-GES_DISC", str(manifest.get("granule_id", ""))):
        raise ValueError("cmr_granule_id_missing_or_invalid")
    source_urls = manifest.get("source", {})
    if not isinstance(source_urls, dict) or not all(
        isinstance(source_urls.get(key), str) and ".umm_json" in source_urls[key]
        for key in ("collection_metadata", "granule_metadata")
    ):
        raise ValueError("cmr_metadata_links_missing")
    if spec["collection_id"] not in source_urls["collection_metadata"] or manifest["granule_id"] not in source_urls["granule_metadata"]:
        raise ValueError("cmr_manifest_identity_mismatch")
    month_name = _period_from_filename(path.name)
    month_manifest = _period_from_manifest(entry)
    if not month_name or not month_manifest or month_name != month_manifest:
        raise ValueError("manifest_period_mismatch")
    source = manifest.get("source", {})
    provider = source.get("provider", "") if isinstance(source, dict) else ""
    if "NASA GES DISC" not in provider and "NASA GES DISC" not in str(entry.get("source", "")):
        raise ValueError("source_not_verified_nasa")
    return month_name


def _candidate_files(inputs: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for source in inputs:
        if source.is_file():
            found.add(source)
            continue
        if not source.exists():
            continue
        for suffix in ("*.HDF5", "*.nc4"):
            found.update(source.rglob(suffix))
    return sorted(found, key=lambda path: str(path).casefold())


def inventory(
    inputs: list[Path], *, payload_validator: Callable[..., None] = _validate_native_payload
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for path in _candidate_files(inputs):
        product = _product_from_filename(path.name)
        record: dict[str, Any] = {
            "filename": path.name,
            "path": str(path),
            "found": path.is_file(),
            "filename_recognized": product is not None,
            "identified": False,
            "manifest_found": False,
            "manifest_identity_verified": False,
            "hash_verified": False,
            "size_verified": False,
            "native_payload_check_attempted": False,
            "native_payload_verified": False,
            "product_key": product,
            "period": _period_from_filename(path.name),
            "eligible": False,
            "rejection_reasons": [],
        }
        if not path.is_file():
            record["rejection_reasons"] = ["not_a_file"]
        elif product is None:
            record["rejection_reasons"] = ["unrecognized_product_filename"]
        else:
            try:
                manifest = _manifest_for(path)
                record["manifest_found"] = True
                entry = _manifest_entry(manifest, path.name)
                month = _validate_identity(path, manifest, entry, product)
                record["identified"] = True
                record["manifest_identity_verified"] = True
                record["period"] = month
                declared_hash, declared_size = _declared_integrity(entry)
                digest = _sha256(path)
                size = path.stat().st_size
                record.update(
                    hash_verified=declared_hash is not None and digest.lower() == declared_hash.lower(),
                    size_verified=declared_size is not None and size == declared_size,
                    bytes=size,
                    sha256=digest,
                    manifest=str(Path(f"{path}.manifest.json")),
                )
                if not record["hash_verified"]:
                    raise ValueError("sha256_mismatch_or_missing")
                if not record["size_verified"]:
                    raise ValueError("size_mismatch_or_missing")
                record["native_payload_check_attempted"] = True
                payload_validator(path, product, month)
                record.update(
                    version=PRODUCTS[product]["version"],
                    variable=PRODUCTS[product]["variable"],
                    unit=PRODUCTS[product]["unit"],
                    native_payload_verified=True,
                    provenance="NASA GES DISC",
                    eligible=True,
                )
            except (OSError, ValueError, KeyError, TypeError, RuntimeError, AttributeError) as exc:
                record["rejection_reasons"] = [str(exc) or type(exc).__name__]

        records.append(record)

    # Collapse byte-identical copies, but reject competing content for a product/month.
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record["eligible"]:
            groups[(record["product_key"], record["period"])].append(record)
    for group in groups.values():
        if len({item["sha256"] for item in group}) > 1:
            for item in group:
                item["eligible"] = False
                item["rejection_reasons"] = ["conflicting_granules_for_product_period"]
        elif len(group) > 1:
            for duplicate in group[1:]:
                duplicate["eligible"] = False
                duplicate["rejection_reasons"] = ["duplicate_identical_granule"]

    eligible_months = {
        product: sorted({item["period"] for item in records if item["eligible"] and item["product_key"] == product})
        for product in PRODUCTS
    }
    all_months = sorted({item["period"] for item in records if item["period"]})
    matrix = [
        {
            "period": month,
            **{product: month in eligible_months[product] for product in PRODUCTS},
            "triple_overlap": all(month in eligible_months[product] for product in PRODUCTS),
        }
        for month in all_months
    ]
    return {
        "records": records,
        "matrix": matrix,
        "counts": {product: len(eligible_months[product]) for product in PRODUCTS},
        "rejected_count": sum(not item["eligible"] for item in records),
        "policy": "only manifest-consistent, hash/size verified, native-payload verified NASA GES DISC granules are eligible; identical duplicates collapse; conflicting product-month payloads are excluded",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True, help="Directory with NASA granules or data root; repeat for multiple roots.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path; defaults to stdout.")
    args = parser.parse_args()
    rendered = json.dumps(inventory(args.input_dir), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
