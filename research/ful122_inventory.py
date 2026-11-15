"""Inventory locally available NASA granules and their verified monthly overlap."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

PRODUCTS = {
    "imerg_final": ("GPM_3IMERGM", "V07B", "precipitation", "mm/hr"),
    "merra2": ("M2TMNXSLV", "5.12.4", "T2M", "K"),
    "gldas": ("GLDAS_NOAH025_M", "2.1", "SoilMoi0_10cm_inst", "kg m-2"),
}
FILENAME_PERIOD = re.compile(r"(?:\.|A)(20\d{2})(0[1-9]|1[0-2])(?:\d{2})?")


def _product(manifest: dict[str, Any], filename: str) -> str | None:
    key = manifest.get("product", {}).get("key")
    if key in PRODUCTS:
        return key
    if filename.startswith("3B-MO.MS.MRG.3IMERG."):
        return "imerg_final"
    if filename.startswith("MERRA2_"):
        return "merra2"
    if filename.startswith("GLDAS_NOAH025_M."):
        return "gldas"
    return None


def _period(manifest: dict[str, Any], filename: str) -> str | None:
    period = manifest.get("period", {})
    month = period.get("month")
    if not month and isinstance(period.get("start"), str):
        month = period["start"][:7]
    if isinstance(month, str) and re.fullmatch(r"20\d{2}-(?:0[1-9]|1[0-2])", month):
        return month
    match = FILENAME_PERIOD.search(filename)
    return f"{match.group(1)}-{match.group(2)}" if match else None


def _declared_hash(manifest: dict[str, Any], filename: str) -> tuple[str | None, int | None]:
    if "sha256" in manifest:
        return manifest.get("sha256"), manifest.get("bytes", manifest.get("expected_size_bytes"))
    for sample in manifest.get("samples", []):
        if sample.get("filename") == filename:
            return sample.get("sha256"), sample.get("size_bytes")
    return None, None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inventory(inputs: list[Path]) -> dict[str, Any]:
    records = []
    seen: set[tuple[str, str, str]] = set()
    for source in inputs:
        files = [source] if source.is_file() else [*source.rglob("*.HDF5"), *source.rglob("*.nc4")]
        for path in files:
            if not path.is_file():
                continue
            manifest_path = Path(f"{path}.manifest.json")
            if not manifest_path.is_file():
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            product = _product(manifest, path.name)
            period = _period(manifest, path.name)
            if product is None or period is None:
                continue
            digest = _sha256(path)
            declared_hash, declared_bytes = _declared_hash(manifest, path.name)
            record = {
                "product_key": product,
                "short_name": PRODUCTS[product][0],
                "version": PRODUCTS[product][1],
                "variable": PRODUCTS[product][2],
                "unit": PRODUCTS[product][3],
                "period": period,
                "filename": path.name,
                "bytes": path.stat().st_size,
                "sha256": digest,
                "manifest": str(manifest_path),
                "manifest_hash_matches": digest == declared_hash,
                "manifest_size_matches": path.stat().st_size == declared_bytes,
            }
            identity = (product, period, digest)
            if identity not in seen:
                records.append(record)
                seen.add(identity)

    months = sorted({r["period"] for r in records})
    present = {product: sorted({r["period"] for r in records if r["product_key"] == product}) for product in PRODUCTS}
    matrix = [
        {
            "period": month,
            **{product: month in present[product] for product in PRODUCTS},
            "triple_overlap": all(month in present[p] for p in PRODUCTS),
        }
        for month in months
    ]
    return {"records": records, "matrix": matrix, "counts": {p: len(present[p]) for p in PRODUCTS}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True, help="Directory with NASA granules or data root; repeat for multiple roots.")
    parser.add_argument("--output", type=Path, help="Optional JSON output path; defaults to stdout.")
    args = parser.parse_args()
    result = inventory(args.input_dir)
    rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
