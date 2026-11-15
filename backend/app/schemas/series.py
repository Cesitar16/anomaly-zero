from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel

from backend.app.schemas.catalog import (
    Envelope,
    InclusiveMonthRange,
    Product,
    Quality,
    Region,
)


class Provenance(BaseModel):
    source_sha256: list[str]
    source_updated_at: datetime | None
    retrieved_at: datetime | None
    snapshot_created_at: datetime | None
    manifest_version: str | None
    manifest_sha256: str | None
    original_file_count: int | None


class Coverage(BaseModel):
    expected_periods: int
    present_periods: int
    valid_periods: int
    missing_periods: list[str]
    spatial_coverage: dict[str, Any] | None = None


class Temporal(BaseModel):
    frequency: Literal["monthly"]
    calendar: str | None
    date_label: Literal["month_start"]


class ProviderFlag(BaseModel):
    name: str
    value: Any


class PointQuality(BaseModel):
    state: Literal["unassessed", "missing", "unknown"]
    provider_flags: list[ProviderFlag]
    missing_reason: str | None


class SeriesPoint(BaseModel):
    date: date
    value: float | None
    quality: PointQuality


class PointReference(BaseModel):
    cell_id: str
    latitude: float | None
    longitude: float | None


class PointSampleSupport(BaseModel):
    support_type: Literal["point_sample"]
    approval_state: Literal["not_assessed"]
    method: None
    area_weighted: None
    weighting_reference: None
    mask_version: None
    point: PointReference


class Transformation(BaseModel):
    operation: str
    parameters: dict[str, Any]
    input_unit: str | None
    output_unit: str | None
    code_version: str | None


class SeriesResponse(Envelope):
    data_state: Literal["available", "available_with_gaps", "no_data"]
    region: Region
    product: Product
    dataset_id: str | None
    provenance: Provenance | None
    temporal: Temporal
    requested_coverage: InclusiveMonthRange
    available_coverage: dict[str, str] | None
    coverage: Coverage
    quality: Quality
    spatial_aggregation: PointSampleSupport | None
    transformations: list[Transformation]
    series: list[SeriesPoint]
    message: str = ""
