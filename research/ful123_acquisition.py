"""Reproducible, offline-testable acquisition planning for NASA 2005 granules.

This module plans only the missing MERRA-2 and GLDAS monthly granules. It
delegates file transfer to the repository's Earthaccess clients; it never
stores authenticated URLs or credentials in a portable manifest.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.data_sources import earthdata_probe as probe
from research.ful122_inventory import inventory

TARGET_PRODUCTS = ("merra2", "gldas")
PROBE_PRODUCT_KEYS = {"merra2": "merra2", "gldas": "gldas_noah_monthly"}
EXPECTED_MONTHS = tuple(f"2005-{month:02d}" for month in range(1, 13))
DEFAULT_BBOX = probe.DEFAULT_BBOX
PLAN_VERSION = 1
MAX_TRANSFER_BYTES = int(1.5 * 1024**3)
MIN_FREE_BYTES = 4 * 1024**3


class AcquisitionPlanError(ValueError):
    """A plan is incomplete, inconsistent, or outside resource limits."""


def eligible_months(audit: dict[str, Any], product: str) -> set[str]:
    """Return only periods that passed the DS-05 NASA inventory checks."""
    return {
        row["period"]
        for row in audit.get("records", [])
        if row.get("eligible") is True and row.get("product_key") == product
    }


def missing_months(audit: dict[str, Any], product: str) -> list[str]:
    if product not in TARGET_PRODUCTS:
        raise AcquisitionPlanError(f"unsupported acquisition product: {product}")
    return [month for month in EXPECTED_MONTHS if month not in eligible_months(audit, product)]


def verify_resource_budget(
    expected_bytes: int, free_bytes: int, *, max_transfer_bytes: int = MAX_TRANSFER_BYTES,
    min_free_bytes: int = MIN_FREE_BYTES,
) -> None:
    if expected_bytes < 0 or free_bytes < 0:
        raise AcquisitionPlanError("resource sizes must be non-negative")
    if expected_bytes > max_transfer_bytes:
        raise AcquisitionPlanError("estimated transfer exceeds the 1.5 GiB planning cap")
    if free_bytes < min_free_bytes:
        raise AcquisitionPlanError("at least 4 GiB free space is required before bulk acquisition")


def discover_plan(
    audit: dict[str, Any], *, client: Any, bbox: tuple[float, float, float, float] = DEFAULT_BBOX,
    discoverer: Callable[..., dict[str, Any]] = probe.discover_product,
) -> dict[str, Any]:
    """Resolve missing months to CMR granule identities and safe metadata URLs."""
    product_by_key = {product.key: product for product in probe.PRODUCTS}
    items: list[dict[str, Any]] = []
    for key in TARGET_PRODUCTS:
        product = product_by_key[PROBE_PRODUCT_KEYS[key]]
        already_eligible = eligible_months(audit, key)
        for month in EXPECTED_MONTHS:
            if month in already_eligible:
                items.append({"product": key, "month": month, "status": "reused_eligible"})
                continue
            result = discoverer(product, month, 2, bbox, client)
            granules = result.get("granules", [])
            matching = [
                granule for granule in granules
                if granule.get("collection_id") == product.expected_collection_id
                and str(granule.get("producer_granule_id", "")).startswith(
                    f"{product.short_name}.{product.version}:"
                )
                and str(granule.get("time_start", "")).startswith(month)
                and str(granule.get("time_end", "")).startswith(month)
            ]
            if result.get("status") != "found" or len(matching) != 1:
                items.append({
                    "product": key, "month": month, "status": "blocked",
                    "reason": "cmr_not_found_or_ambiguous",
                })
                continue
            granule = matching[0]
            size_mib = granule.get("size_mib")
            if not isinstance(size_mib, (int, float)) or size_mib <= 0:
                items.append({"product": key, "month": month, "status": "blocked", "reason": "cmr_size_missing"})
                continue
            items.append({
                "product": key,
                "month": month,
                "status": "discovered",
                "granule_id": granule["granule_id"],
                "producer_granule_id": granule["producer_granule_id"],
                "collection_id": granule["collection_id"],
                "time_start": granule["time_start"],
                "time_end": granule["time_end"],
                "estimated_bytes": math.ceil(size_mib * 1024**2),
                "cmr_metadata_url": (
                    "https://cmr.earthdata.nasa.gov/search/concepts/"
                    f"{granule['granule_id']}.umm_json"
                ),
                "method": "full_granule_pending_pilot",
            })
    return {
        "manifest_version": PLAN_VERSION,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "year": 2005,
        "bbox_file_selection_only": list(bbox),
        "products": {
            key: {
                "short_name": product.short_name,
                "version": product.version,
                "variable": product.variable,
                "unit": ("K" if product.key == "merra2" else "kg m-2"),
            }
            for key in TARGET_PRODUCTS
            for product in (product_by_key[PROBE_PRODUCT_KEYS[key]],)
        },
        "items": items,
        "transfer_estimate_bytes": sum(
            item.get("estimated_bytes", 0) for item in items if item["status"] == "discovered"
        ),
        "limitations": [
            "CMR discovery verifies catalog identity, not payload integrity.",
            "A bbox selects granules; it does not clip cells or define a basin mask.",
            "No signed data URLs, authorization headers, or credentials are stored.",
        ],
    }


def load_audit(input_dirs: list[Path]) -> dict[str, Any]:
    return inventory(input_dirs)


def _existing_output_item(audit: dict[str, Any], product: str, month: str) -> dict[str, Any] | None:
    matches = [
        record for record in audit.get("records", [])
        if record.get("product_key") == product and record.get("period") == month
    ]
    return next((record for record in matches if record.get("eligible") is True), matches[0] if matches else None)


def _validate_planned_item(item: dict[str, Any]) -> None:
    product_key = item.get("product")
    if product_key not in TARGET_PRODUCTS:
        raise AcquisitionPlanError("plan contains an unsupported product")
    month = item.get("month")
    if month not in EXPECTED_MONTHS:
        raise AcquisitionPlanError("plan contains a period outside 2005")
    product = next(p for p in probe.PRODUCTS if p.key == PROBE_PRODUCT_KEYS[product_key])
    year_month = month.replace("-", "")
    filename = (
        f"MERRA2_300.tavgM_2d_slv_Nx.{year_month}.nc4"
        if product_key == "merra2"
        else f"GLDAS_NOAH025_M.A{year_month}.021.nc4"
    )
    expected_ur = f"{product.short_name}.{product.version}:{filename}"
    if item.get("producer_granule_id") != expected_ur:
        raise AcquisitionPlanError("CMR producer identity does not match product and period")
    if item.get("collection_id") != product.expected_collection_id:
        raise AcquisitionPlanError("CMR collection identity does not match the configured product")
    if not re.fullmatch(r"G\d+-GES_DISC", str(item.get("granule_id", ""))):
        raise AcquisitionPlanError("CMR granule concept ID is invalid")
    if not str(item.get("time_start", "")).startswith(month) or not str(item.get("time_end", "")).startswith(month):
        raise AcquisitionPlanError("CMR period bounds do not match the requested month")
    if not isinstance(item.get("estimated_bytes"), int) or item["estimated_bytes"] <= 0:
        raise AcquisitionPlanError("CMR granule size is missing or invalid")


def _record_matches_plan(record: dict[str, Any], item: dict[str, Any]) -> bool:
    manifest_path = record.get("manifest")
    if not isinstance(manifest_path, str):
        return False
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    product = manifest.get("product", {})
    expected_product = next(p for p in probe.PRODUCTS if p.key == PROBE_PRODUCT_KEYS[item["product"]])
    period = manifest.get("period", {})
    return (
        manifest.get("granule_id") == item.get("granule_id")
        and manifest.get("producer_granule_id") == item.get("producer_granule_id")
        and manifest.get("collection_id") == item.get("collection_id")
        and isinstance(period, dict) and period.get("month") == item.get("month")
        and isinstance(product, dict)
        and product.get("short_name") == expected_product.short_name
        and str(product.get("version")) == expected_product.version
        and product.get("variable") == expected_product.variable
    )


def acquisition_exit_code(results: list[dict[str, Any]]) -> int:
    """Return nonzero for every blocked/failed item so CI/CLI callers see it."""
    return 2 if any(
        result.get("status") == "failed"
        or str(result.get("status", "")).startswith("blocked")
        for result in results
    ) else 0


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _portable_inspection_summary(inspection: dict[str, Any]) -> dict[str, Any]:
    variable = inspection.get("variable", {})
    coordinates = inspection.get("coordinates", {})
    return {
        "format": inspection.get("format"),
        "dimensions": inspection.get("dimensions"),
        "variable": {
            key: variable.get(key)
            for key in ("name", "dimensions", "shape", "dtype", "units", "fill_value", "missing_value", "scale_factor", "add_offset")
            if key in variable
        },
        "coordinates": {
            name: {
                key: coordinate.get(key)
                for key in ("dimensions", "size", "attributes", "first_values", "last_values")
                if key in coordinate
            }
            for name, coordinate in coordinates.items()
        } if isinstance(coordinates, dict) else {},
        "quality_variable_candidates": inspection.get("quality_variable_candidates", []),
    }


def build_results_manifest(
    audit: dict[str, Any], acquisition_root: Path, plan: dict[str, Any],
    progress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a portable record of payload-verified February–December acquisitions."""
    root = acquisition_root.resolve()
    planned = {
        (item.get("product"), item.get("month")): item
        for item in plan.get("items", []) if item.get("status") == "discovered"
    }
    attempts = {
        (item.get("product"), item.get("month")): item.get("attempts")
        for item in (progress or {}).get("items", [])
        if isinstance(item, dict)
    }
    acquisitions: list[dict[str, Any]] = []
    for record in audit.get("records", []):
        product = record.get("product_key")
        month = record.get("period")
        if product not in TARGET_PRODUCTS or month not in EXPECTED_MONTHS[1:] or record.get("eligible") is not True:
            continue
        data_path = Path(record["path"]).resolve()
        try:
            relative_path = data_path.relative_to(root).as_posix()
        except ValueError:
            continue
        item = planned.get((product, month))
        if not item or not _record_matches_plan(record, item):
            raise AcquisitionPlanError(f"eligible {product} {month} payload does not match the saved CMR plan")
        manifest_path = Path(record["manifest"]).resolve()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        spec = plan["products"][product]
        acquisitions.append({
            "product": product,
            "month": month,
            "status": "eligible",
            "granule_id": item["granule_id"],
            "collection_id": item["collection_id"],
            "producer_granule_id": item["producer_granule_id"],
            "time_start": manifest.get("period", {}).get("start"),
            "time_end": manifest.get("period", {}).get("end"),
            "short_name": spec["short_name"],
            "version": spec["version"],
            "variable": spec["variable"],
            "unit": spec["unit"],
            "acquisition_method": "complete_original_granule_via_earthaccess",
            "spatial_subsetting_applied": False,
            "format": manifest.get("inspection", {}).get("format"),
            "relative_path": relative_path,
            "bytes": record["bytes"],
            "sha256": record["sha256"],
            "manifest_sha256": _file_sha256(manifest_path),
            "downloaded_at_utc": manifest.get("downloaded_at_utc"),
            "attempts": attempts.get((product, month)),
            "native_payload_verified": True,
            "native_metadata": _portable_inspection_summary(manifest.get("inspection", {})),
        })
    acquisitions.sort(key=lambda row: (row["product"], row["month"]))
    coverages = {
        product: sorted({
            record["period"] for record in audit.get("records", [])
            if record.get("product_key") == product and record.get("eligible") is True
            and record.get("period") in EXPECTED_MONTHS
        })
        for product in ("imerg_final", *TARGET_PRODUCTS)
    }
    triple = sorted(set(coverages["imerg_final"]) & set(coverages["merra2"]) & set(coverages["gldas"]))
    planned_bytes = sum(
        item.get("estimated_bytes", 0) for item in planned.values()
        if item.get("product") in TARGET_PRODUCTS and item.get("month") in EXPECTED_MONTHS[1:]
    )
    actual_bytes = sum(row["bytes"] for row in acquisitions)
    complete = all(len(coverages[p]) == 12 for p in ("imerg_final", *TARGET_PRODUCTS)) and len(triple) == 12 and len(acquisitions) == 22
    return {
        "manifest_version": 1,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "status": "complete" if complete else "partial",
        "year": 2005,
        "eligible_months_by_product": coverages,
        "eligible_product_month_records": sum(len(coverages[p]) for p in coverages),
        "triple_overlap_months": triple,
        "triple_overlap_count": len(triple),
        "planned_full_granule_payload_bytes": planned_bytes,
        "acquired_full_granule_payload_bytes": actual_bytes,
        "payload_byte_difference_actual_minus_estimate": actual_bytes - planned_bytes,
        "acquisition_method": "complete original NASA source granules; no spatial subsetting, reprojection, interpolation, or masking",
        "acquisitions": acquisitions,
        "scientific_status": {
            "temporal_inventory_compatibility": "verified_for_monthly_2005_periods",
            "spatial_colocation": "not_approved",
            "quality_gates": "Gate R and Gate T pending; IMERG QA remains unassessed",
            "gldas_mask_lineage": "uncertain; existing NASA-05 finding remains",
            "inference_or_modeling": "not performed",
        },
    }


def _default_download(item: dict[str, Any], output_dir: Path, auth_strategy: str) -> dict[str, Any]:
    if item["product"] == "merra2":
        from backend.app.data_sources.earthdata_samples import download_product

        return download_product(
            "merra2", item["month"], max_mib=128, auth_strategy=auth_strategy,
            persist_auth=False, output_dir=output_dir,
        )
    from backend.app.data_sources.earthdata_probe import download_gldas

    return download_gldas(
        item["month"], max_mib=64, auth_strategy=auth_strategy,
        persist_auth=False, output_dir=output_dir,
    )


def acquire_months(
    plan: dict[str, Any], output_dir: Path, *, months: set[str],
    audit_dirs: list[Path] | None = None,
    auth_strategy: str = "netrc",
    max_attempts: int = 3, download_fn: Callable[..., dict[str, Any]] = _default_download,
    audit_fn: Callable[[list[Path]], dict[str, Any]] = load_audit,
    identity_validator: Callable[[dict[str, Any], dict[str, Any]], bool] = _record_matches_plan,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> list[dict[str, Any]]:
    """Acquire selected planned months sequentially, verifying every publication.

    Successful granules are committed atomically with their manifests by the
    existing product downloaders. A rerun skips inventory-eligible outputs and
    restarts any interrupted transfer at that granule boundary.
    """
    if auth_strategy not in {"netrc", "environment", "interactive"}:
        raise AcquisitionPlanError("unsupported Earthdata authentication strategy")
    if not 1 <= max_attempts <= 3:
        raise AcquisitionPlanError("max_attempts must be between 1 and 3")
    sources_to_audit = list(dict.fromkeys([*(audit_dirs or []), output_dir]))
    if any(month != "2005-02" for month in months):
        pilot_audit = audit_fn(sources_to_audit)
        pilot_items = {
            (item.get("product"), item.get("month")): item
            for item in plan.get("items", [])
            if item.get("status") == "discovered"
        }
        pilot_passed = True
        for product in TARGET_PRODUCTS:
            record = _existing_output_item(pilot_audit, product, "2005-02")
            planned_pilot = pilot_items.get((product, "2005-02"))
            if not record or record.get("eligible") is not True:
                pilot_passed = False
                break
            if planned_pilot and not identity_validator(record, planned_pilot):
                pilot_passed = False
                break
        if not pilot_passed:
            raise AcquisitionPlanError("February pilots must be payload-verified before the remaining batch")
    selected = [
        item for item in plan.get("items", [])
        if item.get("status") == "discovered" and item.get("month") in months
    ]
    for item in selected:
        _validate_planned_item(item)
    required = sum(item.get("estimated_bytes", 0) for item in selected)
    parent = output_dir
    while not parent.exists() and parent != parent.parent:
        parent = parent.parent
    free_bytes = shutil.disk_usage(parent).free
    verify_resource_budget(required, free_bytes)
    output_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []

    def record_result(result: dict[str, Any]) -> None:
        results.append(result)
        progress_path = output_dir / ".ful123-acquisition-progress.json"
        staged_path = output_dir / ".ful123-acquisition-progress.json.tmp"
        progress_path.parent.mkdir(parents=True, exist_ok=True)
        previous: list[dict[str, Any]] = []
        if progress_path.is_file():
            saved = json.loads(progress_path.read_text(encoding="utf-8"))
            previous = [item for item in saved.get("items", []) if isinstance(item, dict)]
        merged = {
            (item.get("product"), item.get("month")): item
            for item in [*previous, *results]
            if item.get("product") in TARGET_PRODUCTS and item.get("month") in EXPECTED_MONTHS
        }
        product_order = {product: index for index, product in enumerate(TARGET_PRODUCTS)}
        ordered = sorted(merged.values(), key=lambda item: (product_order[item["product"]], item["month"]))
        staged_path.write_text(json.dumps({
            "manifest_version": PLAN_VERSION,
            "updated_at_utc": datetime.now(UTC).isoformat(),
            "items": ordered,
        }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(staged_path, progress_path)

    for item in selected:
        current = audit_fn(sources_to_audit)
        existing = _existing_output_item(current, item["product"], item["month"])
        if existing and existing.get("eligible") is True:
            if identity_validator(existing, item):
                record_result({"product": item["product"], "month": item["month"], "status": "reused_eligible", "attempts": 0})
            else:
                record_result({"product": item["product"], "month": item["month"], "status": "blocked_existing_identity_mismatch", "attempts": 0})
            continue

        filename = item["producer_granule_id"].rsplit(":", maxsplit=1)[-1]
        product_directory = "merra2" if item["product"] == "merra2" else "gldas"
        destination = output_dir / product_directory / filename
        manifest_path = Path(f"{destination}.manifest.json")
        if destination.exists() or manifest_path.exists():
            record_result({"product": item["product"], "month": item["month"], "status": "blocked_existing_unverified", "attempts": 0})
            continue

        last_error: dict[str, Any] | None = None
        for attempt in range(1, max_attempts + 1):
            try:
                response = download_fn(item, output_dir, auth_strategy)
            except probe.ProbeError as exc:
                stage = getattr(exc, "stage", None)
                last_error = {"type": type(exc).__name__, "stage": stage}
                if stage != "download" or attempt == max_attempts:
                    break
                sleep_fn(float(2 ** (attempt - 1)))
                continue
            if response.get("status") != "downloaded_and_opened":
                last_error = {"type": "unexpected_download_status"}
                break
            verified = audit_fn(sources_to_audit)
            record = _existing_output_item(verified, item["product"], item["month"])
            if not record or record.get("eligible") is not True or not identity_validator(record, item):
                last_error = {"type": "inventory_payload_identity_verification_failed"}
                break
            record_result({
                "product": item["product"], "month": item["month"],
                "status": "payload_verified", "attempts": attempt,
                "bytes": record.get("bytes"), "sha256": record.get("sha256"),
            })
            break
        else:  # pragma: no cover - loop exits through success or the explicit break above
            last_error = {"type": "attempts_exhausted"}
        if not results or results[-1].get("product") != item["product"] or results[-1].get("month") != item["month"]:
            record_result({
                "product": item["product"], "month": item["month"],
                "status": "failed", "attempts": min(attempt, max_attempts),
                "error": last_error,
            })
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--discover", action="store_true", help="Query NASA CMR without downloading data.")
    mode.add_argument("--acquire-pilot", action="store_true", help="Acquire and verify February 2005 for both products.")
    mode.add_argument("--acquire-rest", action="store_true", help="Acquire remaining planned months after both February pilots pass.")
    mode.add_argument("--record-results", action="store_true", help="Reaudit local files and write a portable result manifest.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/raw/nasa"))
    parser.add_argument("--plan-file", type=Path, default=Path("research/manifests/ful123-acquisition-plan-2005.json"))
    parser.add_argument("--auth-strategy", choices=("netrc", "environment", "interactive"), default="netrc")
    args = parser.parse_args(argv)
    input_dirs = list(dict.fromkeys([*args.input_dir, *([args.data_dir] if args.record_results else [])]))
    audit = load_audit(input_dirs)
    if args.record_results:
        if not args.plan_file.is_file():
            parser.error("a saved CMR acquisition plan is required in --plan-file")
        plan = json.loads(args.plan_file.read_text(encoding="utf-8"))
        progress_path = args.data_dir / ".ful123-acquisition-progress.json"
        progress = json.loads(progress_path.read_text(encoding="utf-8")) if progress_path.is_file() else None
        report = build_results_manifest(audit, args.data_dir, plan, progress)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": report["status"],
            "results_manifest": args.output.as_posix(),
            "eligible_product_month_records": report["eligible_product_month_records"],
            "triple_overlap_count": report["triple_overlap_count"],
            "acquisitions": len(report["acquisitions"]),
            "payload_bytes": report["acquired_full_granule_payload_bytes"],
        }, indent=2))
        return 0 if report["status"] == "complete" else 2
    if args.acquire_pilot or args.acquire_rest:
        if not args.output.is_file():
            parser.error("an existing discovered plan is required in --output")
        plan = json.loads(args.output.read_text(encoding="utf-8"))
        if plan.get("manifest_version") != PLAN_VERSION:
            parser.error("the saved acquisition plan has an unsupported version")
        months = {"2005-02"} if args.acquire_pilot else set(EXPECTED_MONTHS[2:])
        results = acquire_months(
            plan, args.data_dir, months=months,
            audit_dirs=[*args.input_dir, args.data_dir],
            auth_strategy=args.auth_strategy,
        )
        print(json.dumps({"results": results}, indent=2))
        return acquisition_exit_code(results)
    if args.discover:
        import earthaccess

        plan = discover_plan(audit, client=earthaccess)
    else:
        plan = {
            "manifest_version": PLAN_VERSION,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "year": 2005,
            "items": [
                {"product": product, "month": month, "status": "missing_cmr_discovery"}
                for product in TARGET_PRODUCTS for month in missing_months(audit, product)
            ],
            "transfer_estimate_bytes": None,
        }
    if plan["transfer_estimate_bytes"] is not None:
        free_bytes = shutil.disk_usage(args.output.parent).free
        try:
            verify_resource_budget(plan["transfer_estimate_bytes"], free_bytes)
            within_transfer_cap = True
            enough_free_space = True
        except AcquisitionPlanError as exc:
            plan["resource_block"] = str(exc)
            within_transfer_cap = plan["transfer_estimate_bytes"] <= MAX_TRANSFER_BYTES
            enough_free_space = free_bytes >= MIN_FREE_BYTES
        plan["resource_check"] = {
            "free_bytes": free_bytes,
            "minimum_free_bytes": MIN_FREE_BYTES,
            "max_planned_transfer_bytes": MAX_TRANSFER_BYTES,
            "estimated_transfer_bytes": plan["transfer_estimate_bytes"],
            "within_transfer_cap": within_transfer_cap,
            "enough_free_space": enough_free_space,
            "resource_gate_passed": within_transfer_cap and enough_free_space,
            "pilot_still_required": True,
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "manifest": args.output.as_posix(),
        "eligible_counts": audit["counts"],
        "missing_counts": {product: len(missing_months(audit, product)) for product in TARGET_PRODUCTS},
        "discovered": sum(item["status"] == "discovered" for item in plan["items"]),
        "blocked": sum(item["status"] == "blocked" for item in plan["items"]),
        "estimated_transfer_bytes": plan["transfer_estimate_bytes"],
        "resource_check": plan.get("resource_check"),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
