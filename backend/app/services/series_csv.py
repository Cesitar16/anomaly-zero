"""Serialize an existing SeriesResponse as a spreadsheet-safe UTF-8 CSV."""

from __future__ import annotations

import csv
import io
import json
import re
from typing import Any

from backend.app.schemas.series import SeriesResponse

CSV_COLUMNS = (
    "record_type",
    "period",
    "value",
    "missing_reason",
    "quality_state",
    "provider_flags_json",
    "data_state",
    "region_id",
    "product_id",
    "product_version",
    "variable",
    "quantity",
    "unit",
    "spatial_support_type",
    "spatial_approval_state",
    "dataset_id",
    "source_sha256_json",
    "manifest_sha256",
    "transformations_json",
    "synthetic",
    "provider_flags_applied",
)
_FORMULA_PREFIX = re.compile(r"^[\s\ufeff]*[=+\-@]")


def _json_cell(value: Any) -> str:
    if value is None:
        return "null"
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _text_cell(value: Any) -> str:
    text = str(value)
    return f"'{text}" if _FORMULA_PREFIX.match(text) else text


def _write_row(writer: csv.DictWriter[str], row: dict[str, str]) -> None:
    writer.writerow(
        {
            key: value if key == "value" else _text_cell(value)
            for key, value in row.items()
        }
    )


def _base_row(series: SeriesResponse, record_type: str) -> dict[str, str]:
    provenance = series.provenance
    support = series.spatial_aggregation
    return {
        "record_type": record_type,
        "period": "",
        "value": "",
        "missing_reason": "null",
        "quality_state": "null",
        "provider_flags_json": "null",
        "data_state": series.data_state,
        "region_id": series.region.region_id,
        "product_id": series.product.product_id,
        "product_version": series.product.product_version,
        "variable": series.product.variable,
        "quantity": series.product.quantity,
        "unit": series.product.unit,
        "spatial_support_type": support.support_type if support else "null",
        "spatial_approval_state": support.approval_state if support else "null",
        "dataset_id": series.dataset_id if series.dataset_id is not None else "",
        "source_sha256_json": _json_cell(
            provenance.source_sha256 if provenance else None
        ),
        "manifest_sha256": (
            provenance.manifest_sha256
            if provenance and provenance.manifest_sha256 is not None
            else "null"
        ),
        "transformations_json": _json_cell(
            [item.model_dump(mode="json") for item in series.transformations]
        ),
        "synthetic": str(series.synthetic).lower(),
        "provider_flags_applied": str(series.quality["provider_flags_applied"]).lower(),
    }


def serialize_series_csv(series: SeriesResponse) -> str:
    """Serialize only fields present in the already-validated API series response."""
    output = io.StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        extrasaction="raise",
        lineterminator="\r\n",
    )
    writer.writeheader()
    if series.data_state == "no_data":
        _write_row(writer, _base_row(series, "status"))
        return output.getvalue()

    for point in series.series:
        row = _base_row(series, "observation")
        row.update(
            period=point.date.isoformat(),
            value="" if point.value is None else repr(point.value),
            missing_reason=(
                point.quality.missing_reason
                if point.quality.missing_reason is not None
                else "null"
            ),
            quality_state=point.quality.state,
            provider_flags_json=_json_cell(
                [flag.model_dump(mode="json") for flag in point.quality.provider_flags]
            ),
        )
        # CSV quoting does not stop spreadsheet formula evaluation in text cells.
        _write_row(writer, row)
    return output.getvalue()
