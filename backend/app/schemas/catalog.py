from datetime import datetime
from typing import Annotated, Any, Literal, NotRequired, TypedDict

from pydantic import BaseModel, Field


class Envelope(BaseModel):
    contract_version: Literal["0.1-draft"]
    synthetic: bool
    generated_at: datetime


class Region(BaseModel):
    region_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    geometry_version: str | None
    geometry_source: str | None
    crs: str | None
    area_km2: float | None = Field(gt=0)


class RegionsResponse(Envelope):
    regions: list[Region]


class Source(BaseModel):
    agency: str
    distributor: str | None
    collection_id: str | None
    doi: str | None
    source_urls: list[Annotated[str, Field(json_schema_extra={"format": "uri"})]]
    granule_ids: list[str]


class MonthRange(BaseModel):
    start: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    end: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")


class InclusiveMonthRange(MonthRange):
    end_inclusive: Literal[True]


class Metrics(BaseModel):
    slope: float | None
    slope_unit: str | None
    confidence_interval: tuple[float, float] | None
    p_value: float | None = Field(ge=0, le=1)
    significance: bool | None


class UnavailableAnalysis(BaseModel):
    state: Literal["not_available"]
    analysis_id: None
    dataset_id: str
    region_id: str
    product_id: str
    window: InclusiveMonthRange
    method: None
    metrics: Metrics


class ErrorDetails(TypedDict):
    dataset_id: NotRequired[str | None]
    provider_status: NotRequired[int | None]
    analysis: NotRequired[UnavailableAnalysis]


class SourceMissingAttributes(TypedDict):
    fill_value: Any
    missing_value: Any
    scale_factor: Any
    add_offset: Any


class QualityCheck(TypedDict):
    check_id: Annotated[str, Field(min_length=1)]
    version: str | None
    applied: bool
    state: Literal["not_run", "passed", "failed", "partial"]
    excluded_count: Annotated[int, Field(ge=0)] | None
    exclusion_reasons: list[str]


class Quality(TypedDict):
    source_flag_fields: list[str]
    provider_flags_applied: bool
    source_missing_attributes: SourceMissingAttributes
    finite_non_fill_filter_applied: bool
    verification_state: Literal[
        "unassessed", "basic_checks_only", "provider_qa_applied"
    ]
    mask_applied: str | None
    qa_checks: NotRequired[list[QualityCheck]]
    uninterpreted_provider_fields: NotRequired[list[str]]


class Product(BaseModel):
    product_id: str
    short_name: str
    product_version: str
    variable: str
    quantity: str
    unit: str
    availability: Literal["available", "partial", "unavailable"]
    source: Source
    current_dataset_id: str | None
    coverage: MonthRange | None
    quality: Quality | None


class ProductsResponse(Envelope):
    region_id: str
    products: list[Product]


class Error(BaseModel):
    code: Literal[
        "INVALID_PARAMETER",
        "PERIOD_OUT_OF_COVERAGE",
        "LIMIT_EXCEEDED",
        "RESOURCE_NOT_FOUND",
        "INSUFFICIENT_DATA",
        "ANALYSIS_METHOD_UNAVAILABLE",
        "SERVICE_UNAVAILABLE",
        "INTERNAL_ERROR",
    ]
    message: str
    retryable: bool
    request_id: str
    details: ErrorDetails | None


class ErrorResponse(Envelope):
    error: Error
