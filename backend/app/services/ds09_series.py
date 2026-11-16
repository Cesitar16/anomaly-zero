"""Read the versioned DS-09 point tables without revalidating source granules.

These tables are derived observations. Their source hashes are provenance
references from DS-09, not a claim that this runtime re-opened NASA granules.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from backend.app.schemas.catalog import MonthRange
from backend.app.schemas.series import SeriesResponse

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "research" / "results" / "ful126"
MANIFEST = ROOT / "research" / "manifests" / "ful126-point-eda-2005.json"
SITE_IDS = ("site_west_extent", "site_central_extent", "site_east_extent")
TABLE_PRODUCT = {
    "P01": ("merra2", "M2TMNXSLV", "5.12.4", "T2M", "K"),
    "P02": ("imerg_final", "GPM_3IMERGM", "V07B", "precipitation", "mm/hr"),
    "P03": ("gldas", "GLDAS_NOAH025_M", "2.1", "SoilMoi0_10cm_inst", "kg m-2"),
}
SHA = re.compile(r"^[0-9a-f]{64}$")


class DerivedTableError(Exception):
    """A derived DS-09 table is missing or inconsistent."""


def table_path(product_id: str, site_id: str) -> Path:
    if product_id not in TABLE_PRODUCT or site_id not in SITE_IDS:
        raise DerivedTableError("Unknown product or candidate site")
    return RESULTS / f"{site_id}_{TABLE_PRODUCT[product_id][0]}_2005.csv"


def table_available(product_id: str, site_id: str) -> bool:
    try:
        path = table_path(product_id, site_id)
        if not path.is_file() or not MANIFEST.is_file():
            return False
        if json.loads(MANIFEST.read_text(encoding="utf-8")).get("status") != "diagnostic_only_not_approved":
            return False
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        expected_unit = TABLE_PRODUCT[product_id][4]
        return (
            len(rows) == 12
            and [row.get("month") for row in rows] == [f"2005-{month:02d}" for month in range(1, 13)]
            and all(row.get("site_id") == site_id and row.get("unit_original") == expected_unit for row in rows)
            and all(row.get("decoded_value_status") == "finite" and math.isfinite(float(row["decoded_value"])) for row in rows)
            and all(SHA.fullmatch(row.get("payload_sha256", "")) for row in rows)
        )
    except (DerivedTableError, OSError, ValueError, KeyError, json.JSONDecodeError, csv.Error):
        return False


def load_ds09_series(
    *, catalog: Any, product: Any, region_id: str, site_id: str,
    start: str, end: str, expected: int,
) -> SeriesResponse:
    path = table_path(product.product_id, site_id)
    if not path.is_file() or not MANIFEST.is_file():
        raise DerivedTableError("DS-09 derived table is unavailable")
    try:
        manifest_bytes = MANIFEST.read_bytes()
        manifest = json.loads(manifest_bytes)
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
    except (OSError, UnicodeError, json.JSONDecodeError, csv.Error) as exc:
        raise DerivedTableError("DS-09 derived artifact is unreadable") from exc
    if manifest.get("status") != "diagnostic_only_not_approved":
        raise DerivedTableError("DS-09 scientific status is incompatible")
    table_name, _short_name, version, _variable, unit = TABLE_PRODUCT[product.product_id]
    months = [f"2005-{month:02d}" for month in range(1, 13)]
    if len(rows) != 12 or [row.get("month") for row in rows] != months:
        raise DerivedTableError("DS-09 table must contain twelve ordered monthly rows")
    if any(row.get("site_id") != site_id or row.get("unit_original") != unit for row in rows):
        raise DerivedTableError("DS-09 site or unit metadata is inconsistent")
    source_version = "07" if product.product_id == "P02" else version
    if any(row.get("product_version") != source_version or row.get("collection_id") != product.source.collection_id for row in rows):
        raise DerivedTableError("DS-09 product identity or version metadata is inconsistent")
    if any(row.get("state") != "diagnostic_only_not_approved" for row in rows):
        raise DerivedTableError("DS-09 table scientific status is inconsistent")
    if any(not SHA.fullmatch(row.get("payload_sha256", "")) for row in rows):
        raise DerivedTableError("DS-09 source hash reference is malformed")
    if any(row.get("decoded_value_status") != "finite" for row in rows):
        raise DerivedTableError("DS-09 table contains a value requiring missing/fill interpretation")
    try:
        values = [float(row["decoded_value"]) for row in rows]
        coords = [json.loads(row["cell_center_lon_lat"]) for row in rows]
        cells = [json.loads(row["grid_cell_index_zero_based"]) for row in rows]
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise DerivedTableError("DS-09 observation fields are invalid") from exc
    if any(not math.isfinite(value) for value in values):
        raise DerivedTableError("DS-09 values must be finite or explicitly missing")
    if len({json.dumps(coord, sort_keys=True) for coord in coords}) != 1 or len({json.dumps(cell, sort_keys=True) for cell in cells}) != 1:
        raise DerivedTableError("DS-09 cell identity changes within one site/product series")
    lon, lat = coords[0]
    if not (-180 <= lon <= 180 and -90 <= lat <= 90):
        raise DerivedTableError("DS-09 coordinates are outside geographic bounds")
    cell = cells[0]
    if not isinstance(cell, dict) or set(cell) != {"row_latitude", "column_longitude"}:
        raise DerivedTableError("DS-09 grid-cell indices are invalid")
    cell_id = f"{table_name}-row{cell['row_latitude']}-column{cell['column_longitude']}"
    if not (start >= months[0] and end <= months[-1]):
        raise ValueError("period outside DS-09 coverage")
    selected = [(month, value, row) for month, value, row in zip(months, values, rows, strict=True) if start <= month <= end]
    manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
    table_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    original_product = product.model_copy(update={
        "availability": "available", "product_version": version,
        "current_dataset_id": f"ds09-{product.product_id.lower()}-{site_id}-2005",
        "coverage": MonthRange(start=months[0], end=months[-1]),
        "source": product.source.model_copy(update={"granule_ids": list(dict.fromkeys(r["granule_id"] for r in rows))}),
        "quality": {
            "source_flag_fields": [], "provider_flags_applied": False,
            "source_missing_attributes": {"fill_value": None, "missing_value": None, "scale_factor": None, "add_offset": None},
            "finite_non_fill_filter_applied": False, "verification_state": "unassessed",
            "mask_applied": None, "qa_checks": [], "uninterpreted_provider_fields": [],
        },
    })
    records = [
        {"date": date.fromisoformat(month + "-01"), "value": value,
         "quality": {"state": "unassessed", "provider_flags": [], "missing_reason": None}}
        for month, value, _row in selected
    ]
    missing = [month for month, value, _row in selected if value is None]
    return SeriesResponse(
        contract_version="0.1-draft", synthetic=False, generated_at=datetime.now(UTC),
        data_state="available_with_gaps" if missing else "available",
        region=next(r for r in catalog.regions if r.region_id == region_id), product=original_product,
        dataset_id=original_product.current_dataset_id,
        provenance={"source_sha256": list(dict.fromkeys(r["payload_sha256"] for r in rows)),
                    "source_updated_at": None, "retrieved_at": None, "snapshot_created_at": None,
                    "manifest_version": "DS-09 diagnostic table; originals not reverified at runtime",
                    "manifest_sha256": manifest_sha, "original_file_count": 12},
        temporal={"frequency": "monthly", "calendar": None, "date_label": "month_start"},
        requested_coverage={"start": start, "end": end, "end_inclusive": True},
        available_coverage={"start": months[0], "end": months[-1]},
        coverage={"expected_periods": expected, "present_periods": len(records), "valid_periods": len(records)-len(missing),
                  "missing_periods": missing, "spatial_coverage": None},
        quality=original_product.quality,
        spatial_aggregation={"support_type": "point_sample", "approval_state": "not_assessed", "method": None,
                             "area_weighted": None, "weighting_reference": None, "mask_version": None,
                             "point": {"cell_id": cell_id, "latitude": lat, "longitude": lon}},
        transformations=[], series=records,
        message=f"Sitio candidato DS-09 {site_id}; artefacto derivado diagnostic_only_not_approved. CSV SHA-256 {table_sha}; no implica reverificación del granule original.",
    )
