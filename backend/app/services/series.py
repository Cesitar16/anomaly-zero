"""Build monthly API responses from an optional verified DS-03 snapshot."""

from __future__ import annotations

import os
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from backend.app.schemas.catalog import MonthRange, Product
from backend.app.schemas.series import SeriesResponse
from backend.app.services.catalog import Catalog, products_for_region
from backend.app.services.snapshot_reader import (
    SnapshotUnavailableError,
    read_snapshot,
)

YEAR_MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
MAX_SERIES_MONTHS = 240
SNAPSHOT_ENV = "ANOMALY_ZERO_IMERG_SNAPSHOT"
DEFAULT_SNAPSHOT_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "processed"
    / "ful116"
    / "imerg_2005_point_snapshot.json"
)


class SeriesRequestError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.public_message = message
        self.details = details


def get_snapshot_path() -> Path:
    configured = os.environ.get(SNAPSHOT_ENV)
    return Path(configured) if configured else DEFAULT_SNAPSHOT_PATH


def read_optional_snapshot(path: Path) -> dict[str, Any] | None:
    try:
        path.stat()
    except FileNotFoundError as exc:
        if os.environ.get(SNAPSHOT_ENV):
            raise SnapshotUnavailableError("Configured snapshot is unavailable") from exc
        return None
    except OSError as exc:
        raise SnapshotUnavailableError("Configured snapshot is unavailable") from exc
    return read_snapshot(path)


def _parse_month(value: str) -> date:
    if YEAR_MONTH.fullmatch(value) is None:
        raise SeriesRequestError(422, "INVALID_PARAMETER", "El período mensual no es válido.")
    try:
        return date.fromisoformat(f"{value}-01")
    except ValueError as exc:
        raise SeriesRequestError(422, "INVALID_PARAMETER", "El período mensual no es válido.") from exc


def _month_count(start: date, end: date) -> int:
    return (end.year - start.year) * 12 + end.month - start.month + 1


def _month_string(value: date) -> str:
    return value.strftime("%Y-%m")


def _no_data_response(
    catalog: Catalog,
    region_id: str,
    product: Product,
    start: str,
    end: str,
    expected_periods: int,
) -> SeriesResponse:
    start_date = _parse_month(start)
    missing = [
        f"{year:04d}-{month:02d}"
        for offset in range(expected_periods)
        for year, month in [
            (
                start_date.year + (start_date.month - 1 + offset) // 12,
                (start_date.month - 1 + offset) % 12 + 1,
            )
        ]
    ]
    return SeriesResponse(
        contract_version="0.1-draft",
        synthetic=catalog.synthetic,
        generated_at=datetime.now(UTC),
        data_state="no_data",
        region=next(region for region in catalog.regions if region.region_id == region_id),
        product=product,
        dataset_id=None,
        provenance=None,
        temporal={"frequency": "monthly", "calendar": None, "date_label": "month_start"},
        requested_coverage={"start": start, "end": end, "end_inclusive": True},
        available_coverage=None,
        coverage={
            "expected_periods": expected_periods,
            "present_periods": 0,
            "valid_periods": 0,
            "missing_periods": missing,
            "spatial_coverage": None,
        },
        quality={
            "source_flag_fields": [],
            "provider_flags_applied": False,
            "source_missing_attributes": {
                "fill_value": None,
                "missing_value": None,
                "scale_factor": None,
                "add_offset": None,
            },
            "finite_non_fill_filter_applied": False,
            "verification_state": "unassessed",
            "mask_applied": None,
            "qa_checks": [],
            "uninterpreted_provider_fields": [],
        },
        spatial_aggregation=None,
        transformations=[],
        series=[],
        message="No hay datos disponibles para el período solicitado.",
    )


def product_for_snapshot(product: Product, snapshot: dict[str, Any]) -> Product:
    records = snapshot["provenance"]["source_records"]
    missing = snapshot["coverage"]["missing_periods"]
    return product.model_copy(
        update={
            "product_version": snapshot["product"]["product_version"],
            "availability": "partial" if missing else "available",
            "current_dataset_id": snapshot["dataset_id"],
            "coverage": MonthRange(**snapshot["available_coverage"]),
            "quality": snapshot["quality"],
            "source": product.source.model_copy(
                update={"granule_ids": [record["granule_id"] for record in records if record["granule_id"]]}
            ),
        }
    )


def build_series_response(
    catalog: Catalog,
    region_id: str,
    product_id: str,
    start: str,
    end: str,
    frequency: str,
    snapshot_path: Path,
) -> SeriesResponse:
    products = products_for_region(catalog, region_id)
    product = next((item for item in products if item.product_id == product_id), None)
    if product is None:
        raise SeriesRequestError(404, "RESOURCE_NOT_FOUND", "La región o el producto solicitado no existe.")
    if frequency != "monthly":
        raise SeriesRequestError(422, "INVALID_PARAMETER", "La frecuencia solicitada no es válida.")

    start_date, end_date = _parse_month(start), _parse_month(end)
    if start_date > end_date:
        raise SeriesRequestError(422, "INVALID_PARAMETER", "El período inicial debe ser anterior o igual al final.")
    expected = _month_count(start_date, end_date)
    if expected > MAX_SERIES_MONTHS:
        raise SeriesRequestError(422, "LIMIT_EXCEEDED", "La consulta excede el máximo de 240 meses.")

    snapshot = read_optional_snapshot(snapshot_path)
    if snapshot is None or snapshot["product"]["short_name"] != product.short_name:
        return _no_data_response(catalog, region_id, product, start, end, expected)

    coverage = snapshot["available_coverage"]
    if start < coverage["start"] or end > coverage["end"]:
        raise SeriesRequestError(422, "PERIOD_OUT_OF_COVERAGE", "El período solicitado excede la cobertura publicada.")

    rows = [point for point in snapshot["series"] if start <= point["date"][:7] <= end]
    months = [_month_string(date.fromisoformat(point["date"])) for point in rows]
    missing = [month for month, point in zip(months, rows, strict=True) if point["value"] is None]
    valid_periods = sum(point["value"] is not None for point in rows)
    data_state = "available_with_gaps" if missing else "available"
    source_records = snapshot["provenance"]["source_records"]

    return SeriesResponse(
        contract_version="0.1-draft",
        synthetic=catalog.synthetic or snapshot["synthetic"],
        generated_at=datetime.now(UTC),
        data_state=data_state,
        region=next(region for region in catalog.regions if region.region_id == region_id),
        product=product_for_snapshot(product, snapshot),
        dataset_id=snapshot["dataset_id"],
        provenance={
            "source_sha256": [record["sha256"] for record in source_records],
            "source_updated_at": None,
            "retrieved_at": None,
            "snapshot_created_at": None,
            "manifest_version": None,
            "manifest_sha256": None,
            "original_file_count": len(source_records),
        },
        temporal={"frequency": "monthly", "calendar": None, "date_label": "month_start"},
        requested_coverage={"start": start, "end": end, "end_inclusive": True},
        available_coverage=coverage,
        coverage={
            "expected_periods": expected,
            "present_periods": len(rows),
            "valid_periods": valid_periods,
            "missing_periods": missing,
            "spatial_coverage": None,
        },
        quality=snapshot["quality"],
        spatial_aggregation=snapshot["spatial_aggregation"],
        transformations=snapshot["provenance"]["transformations"],
        series=rows,
    )
