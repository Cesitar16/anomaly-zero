"""Read the pinned MDBA boundary artifact for contextual map display only."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

CONTEXT_REGION_ID = "murray-darling-basin"
CONTEXT_GEOMETRY_ENV = "ANOMALY_ZERO_CONTEXT_GEOMETRY"
EXPECTED_ARTIFACT_BYTES = 477_805
EXPECTED_ARTIFACT_SHA256 = (
    "d36fe31424758cc4fb8eef25e21b835bb5c05c793c746e8a1eb7b5a5841f6a53"
)
EXPECTED_BOUNDS = (
    138.568466639,
    -37.682084144087,
    152.488546389,
    -24.5856180792855,
)
MAX_GEOMETRY_BYTES = 1_000_000

SOURCE_URL = (
    "https://services8.arcgis.com/5xxEi7I2m6ml97fE/arcgis/rest/services/"
    "boundary_gdb/FeatureServer/0/query?where=1%3D1&outFields=%2A&"
    "returnGeometry=true&outSR=4326&f=geojson"
)
SOURCE_ITEM_URL = (
    "https://www.arcgis.com/sharing/rest/content/items/"
    "ba731d77d80947fbbcbf7524364372ff"
)

CONTEXT_GEOMETRY_METADATA: dict[str, Any] = {
    "region_id": CONTEXT_REGION_ID,
    "geometry_use": "contextual_outline_only",
    "scientific_approval": "not_approved",
    "source_title": "Murray—Darling Basin Boundary as defined in Section 4 (1) of the Water Act 2007",
    "source_url": SOURCE_URL,
    "source_item_url": SOURCE_ITEM_URL,
    "license": "CC BY 4.0",
    "license_url": "https://creativecommons.org/licenses/by/4.0/",
    "attribution": "Australian Government Department of Climate Change, Energy, the Environment and Water",
    "publisher": "Murray–Darling Basin Authority (MDBAGISPUBLISHER)",
    "retrieved_utc": "2026-11-15",
    "source_item_modified_utc": "2026-01-14T21:08:32Z",
    "service_layer_crs": "EPSG:3857",
    "output_crs": "EPSG:4326",
    "native_datum": None,
    "artifact_sha256": EXPECTED_ARTIFACT_SHA256,
    "artifact_sha256_scope": (
        "SHA-256 of the exact stored 477805-byte source GeoJSON file; "
        "not the serialized API response"
    ),
}


class ContextGeometryUnavailableError(Exception):
    """The configured contextual geometry file cannot be read."""


class ContextGeometryInvalidError(Exception):
    """The configured file is not the approved, structurally valid artifact."""


def get_context_geometry_path() -> Path | None:
    configured = os.environ.get(CONTEXT_GEOMETRY_ENV)
    return Path(configured) if configured else None


def _invalid(message: str) -> None:
    raise ContextGeometryInvalidError(message)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _invalid("GeoJSON contains duplicate object members")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    _invalid("GeoJSON contains a non-finite number")


def _position(value: Any, bounds: list[float]) -> None:
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(
            not isinstance(coordinate, (int, float))
            or isinstance(coordinate, bool)
            or not math.isfinite(coordinate)
            for coordinate in value
        )
    ):
        _invalid("GeoJSON position is invalid")
    longitude, latitude = value
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        _invalid("GeoJSON position is outside longitude/latitude bounds")
    bounds[0] = min(bounds[0], longitude)
    bounds[1] = min(bounds[1], latitude)
    bounds[2] = max(bounds[2], longitude)
    bounds[3] = max(bounds[3], latitude)


def _ring(value: Any, bounds: list[float]) -> None:
    if not isinstance(value, list) or len(value) < 4:
        _invalid("GeoJSON polygon ring is empty or too short")
    for position in value:
        _position(position, bounds)
    if value[0] != value[-1]:
        _invalid("GeoJSON polygon ring is not closed")


def _polygon(value: Any, bounds: list[float]) -> None:
    if not isinstance(value, list) or not value:
        _invalid("GeoJSON polygon has no rings")
    for ring in value:
        _ring(ring, bounds)


def _validate_geojson(document: Any) -> dict[str, Any]:
    if (
        not isinstance(document, dict)
        or document.get("type") != "FeatureCollection"
        or document.get("crs")
        != {"type": "name", "properties": {"name": "EPSG:4326"}}
    ):
        _invalid("GeoJSON collection identity or output CRS is invalid")

    features = document.get("features")
    if not isinstance(features, list) or len(features) != 1:
        _invalid("GeoJSON collection must contain the approved single feature")
    feature = features[0]
    if not isinstance(feature, dict) or feature.get("type") != "Feature":
        _invalid("GeoJSON feature is invalid")
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        _invalid("GeoJSON geometry is missing")

    bounds = [math.inf, math.inf, -math.inf, -math.inf]
    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if geometry_type == "Polygon":
        _polygon(coordinates, bounds)
    elif geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            _invalid("GeoJSON multipolygon is empty")
        for polygon in coordinates:
            _polygon(polygon, bounds)
    else:
        _invalid("GeoJSON geometry must be Polygon or MultiPolygon")
    if tuple(bounds) != EXPECTED_BOUNDS:
        _invalid("GeoJSON bounds do not match the approved artifact")

    return {
        "type": "FeatureCollection",
        "synthetic": False,
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "region_id": CONTEXT_REGION_ID,
                    "name": "Murray–Darling Basin",
                },
                "geometry": geometry,
            }
        ],
        "metadata": CONTEXT_GEOMETRY_METADATA.copy(),
    }


def read_context_geometry(path: Path | None) -> dict[str, Any]:
    if path is None:
        raise ContextGeometryUnavailableError("Context geometry is not configured")
    try:
        if path.stat().st_size > MAX_GEOMETRY_BYTES:
            _invalid("Context geometry exceeds the size limit")
        with path.open("rb") as source:
            raw = source.read(MAX_GEOMETRY_BYTES + 1)
    except ContextGeometryInvalidError:
        raise
    except OSError as exc:
        raise ContextGeometryUnavailableError(
            "Configured context geometry is unavailable"
        ) from exc
    if len(raw) > MAX_GEOMETRY_BYTES:
        _invalid("Context geometry exceeds the size limit")
    if len(raw) != EXPECTED_ARTIFACT_BYTES:
        _invalid("Context geometry size does not match the approved artifact")
    if hashlib.sha256(raw).hexdigest() != EXPECTED_ARTIFACT_SHA256:
        _invalid("Context geometry hash does not match the approved artifact")
    try:
        document = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except ContextGeometryInvalidError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ContextGeometryInvalidError("Context geometry JSON is invalid") from exc
    return _validate_geojson(document)
