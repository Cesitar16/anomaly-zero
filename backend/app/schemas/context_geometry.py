"""OpenAPI types for the contextual GeoJSON boundary response."""

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Longitude = Annotated[float, Field(ge=-180, le=180)]
Latitude = Annotated[float, Field(ge=-90, le=90)]
Position = tuple[Longitude, Latitude]
LinearRing = Annotated[list[Position], Field(min_length=4)]
PolygonCoordinates = Annotated[list[LinearRing], Field(min_length=1)]
MultiPolygonCoordinates = Annotated[list[PolygonCoordinates], Field(min_length=1)]


class PolygonGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Polygon"]
    coordinates: PolygonCoordinates


class MultiPolygonGeometry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["MultiPolygon"]
    coordinates: MultiPolygonCoordinates


class ContextualGeometryFeatureProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_id: Literal["murray-darling-basin"]
    name: Literal["Murray–Darling Basin"]


class ContextualGeometryFeature(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["Feature"]
    properties: ContextualGeometryFeatureProperties
    geometry: PolygonGeometry | MultiPolygonGeometry


class ContextualGeometryMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    region_id: Literal["murray-darling-basin"]
    geometry_use: Literal["contextual_outline_only"]
    scientific_approval: Literal["not_approved"]
    source_title: str
    source_url: Annotated[str, Field(json_schema_extra={"format": "uri"})]
    source_item_url: Annotated[str, Field(json_schema_extra={"format": "uri"})]
    license: str
    license_url: Annotated[str | None, Field(json_schema_extra={"format": "uri"})]
    attribution: str
    publisher: str
    retrieved_utc: date | None
    source_item_modified_utc: datetime | None
    service_layer_crs: str | None
    output_crs: Literal["EPSG:4326"]
    native_datum: None
    artifact_sha256: Annotated[str | None, Field(pattern=r"^[a-f0-9]{64}$")]
    artifact_sha256_scope: str


class ContextualGeometryFeatureCollection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: Literal["FeatureCollection"]
    synthetic: bool
    features: Annotated[
        list[ContextualGeometryFeature], Field(min_length=1, max_length=1)
    ]
    metadata: ContextualGeometryMetadata
