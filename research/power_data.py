"""Cliente mínimo y parser para la API mensual de NASA POWER."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

POWER_URL = "https://power.larc.nasa.gov/api/temporal/monthly/point"
LOCATION = {
    "name": "Wagga Wagga",
    "country": "Australia",
    "region": "New South Wales",
    "latitude": -35.1257741166667,
    "longitude": 147.353737883333,
    "coordinate_source": (
        "Australian Government Bureau of Meteorology, Groundwater Dependent "
        "Ecosystems Atlas, Recognised Places"
    ),
    "coordinate_url": (
        "https://www.bom.gov.au/water/groundwater/gde/service/"
        "simple-location-list.php?letter=W"
    ),
}


class PowerDataError(RuntimeError):
    """Raised when NASA POWER returns an unusable response."""


def _validate_power_payload(
    payload: Any, params: dict[str, str]
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Validate response structure and consistency with a point query."""
    if not isinstance(payload, dict):
        raise PowerDataError("NASA POWER response is malformed: expected an object.")
    properties = payload.get("properties")
    parameter_values = properties.get("parameter") if isinstance(properties, dict) else None
    parameters = payload.get("parameters")
    variable = params["parameters"]
    if not isinstance(parameter_values, dict) or not isinstance(parameters, dict):
        raise PowerDataError(
            "NASA POWER response is malformed: missing properties/parameters objects."
        )
    values = parameter_values.get(variable)
    parameter_metadata = parameters.get(variable)
    if not isinstance(values, dict) or not values:
        raise PowerDataError(
            f"NASA POWER response does not contain usable values for variable {variable}."
        )
    if (
        not isinstance(parameter_metadata, dict)
        or not isinstance(parameter_metadata.get("units"), str)
        or not parameter_metadata["units"]
    ):
        raise PowerDataError(
            f"NASA POWER response has invalid metadata for {variable}."
        )
    header = payload.get("header")
    geometry = payload.get("geometry")
    if not isinstance(header, dict) or not isinstance(geometry, dict):
        raise PowerDataError(
            "NASA POWER response is malformed: missing header or geometry."
        )
    expected_start = f'{params["start"]}0101'
    expected_end = f'{params["end"]}1231'
    if header.get("start") != expected_start or header.get("end") != expected_end:
        raise PowerDataError(
            "NASA POWER response period contradicts the requested start/end years."
        )
    if (
        geometry.get("type") != "Point"
        or not isinstance(geometry.get("coordinates"), list)
        or len(geometry["coordinates"]) < 2
    ):
        raise PowerDataError("NASA POWER response has invalid point geometry.")
    try:
        response_longitude, response_latitude = map(float, geometry["coordinates"][:2])
        requested_longitude = float(params["longitude"])
        requested_latitude = float(params["latitude"])
    except (TypeError, ValueError, KeyError) as exc:
        raise PowerDataError(
            "NASA POWER response geometry or query coordinates are invalid."
        ) from exc
    if (
        not math.isfinite(response_longitude)
        or not math.isfinite(response_latitude)
        or abs(response_longitude - requested_longitude) > 0.01
        or abs(response_latitude - requested_latitude) > 0.01
    ):
        raise PowerDataError(
            "NASA POWER point geometry contradicts the requested coordinates."
        )
    return values, parameter_metadata, header


def build_power_query(
    start_year: int = 2005,
    end_year: int = 2024,
    *,
    parameter: str = "T2M",
    latitude: float = LOCATION["latitude"],
    longitude: float = LOCATION["longitude"],
    community: str = "AG",
) -> dict[str, str]:
    """Build explicit NASA POWER monthly-point query parameters."""
    if start_year > end_year:
        raise ValueError("start_year must be less than or equal to end_year")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Coordinates are outside valid latitude/longitude bounds")
    if not parameter or not community:
        raise ValueError("parameter and community must be non-empty")
    return {
        "parameters": parameter,
        "community": community,
        "longitude": str(longitude),
        "latitude": str(latitude),
        "start": str(start_year),
        "end": str(end_year),
        "format": "JSON",
    }


def fetch_power_response(
    raw_path: str | Path,
    *,
    query: dict[str, str] | None = None,
    timeout: float = 30,
    force: bool = False,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load a cached response or fetch and preserve the original NASA JSON.

    A metadata sidecar records the exact URL, request parameters, and retrieval
    time. Existing raw files are reused only when both files and their
    provenance agree. force=True deliberately makes a fresh request and
    replaces the cache only after a valid response has been received.
    """
    path = Path(raw_path)
    metadata_path = path.with_suffix(".metadata.json")
    params = query or build_power_query()
    required_query_keys = {
        "parameters", "community", "longitude", "latitude", "start", "end", "format"
    }
    if not isinstance(params, dict) or not required_query_keys.issubset(params):
        raise PowerDataError("NASA POWER query is missing required parameters.")
    url = f"{POWER_URL}?{urlencode(params)}"

    if path.exists() and not force:
        if not metadata_path.exists():
            raise PowerDataError(
                f"NASA POWER metadata sidecar missing: {metadata_path}. "
                "Restore the matching sidecar, choose a new cache path, or set force=True "
                "to deliberately download a fresh response."
            )
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PowerDataError(
                f"Cached NASA POWER metadata is invalid: {metadata_path}. "
                "Restore it, choose a new cache path, or set force=True deliberately."
            ) from exc
        if not isinstance(metadata, dict):
            raise PowerDataError("Cached NASA POWER metadata is invalid: expected an object.")
        required_metadata = {
            "institution",
            "service",
            "request_url",
            "parameters",
            "retrieved_at_utc",
            "http_status",
            "parameter_metadata",
            "response_header",
            "response_geometry",
            "requested_years",
            "received_record_count_including_annual_summaries",
        }
        if not required_metadata.issubset(metadata):
            raise PowerDataError(
                "Cached NASA POWER metadata is invalid: required provenance fields are missing."
            )
        if (
            metadata["institution"] != "NASA Langley Research Center POWER Project"
            or metadata["service"] != "NASA POWER Monthly and Annual API"
        ):
            raise PowerDataError("Cached NASA POWER metadata identifies an unexpected source.")
        if metadata["parameters"] != params:
            raise PowerDataError(
                "Cached request parameters do not match this query; use a different "
                "cache path or set force=True deliberately."
            )
        if metadata["request_url"] != url or metadata["http_status"] != 200:
            raise PowerDataError(
                "Cached NASA POWER metadata contradicts the requested URL or successful HTTP status."
            )
        if not isinstance(metadata["retrieved_at_utc"], str) or not metadata["retrieved_at_utc"]:
            raise PowerDataError("Cached NASA POWER metadata has no valid retrieval timestamp.")
        try:
            retrieved_at = datetime.fromisoformat(metadata["retrieved_at_utc"])
        except ValueError as exc:
            raise PowerDataError(
                "Cached NASA POWER metadata has an invalid retrieval timestamp."
            ) from exc
        if retrieved_at.utcoffset() != timedelta(0):
            raise PowerDataError(
                "Cached NASA POWER retrieval timestamp must explicitly use UTC."
            )
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PowerDataError(
                f"Cached NASA POWER response is malformed: {path}. "
                "Restore the original response, choose a new cache path, or set force=True deliberately."
            ) from exc
        try:
            values, parameter_metadata, header = _validate_power_payload(payload, params)
        except PowerDataError as exc:
            raise PowerDataError(f"Cached {exc}") from exc
        if (
            metadata["parameter_metadata"] != parameter_metadata
            or metadata["response_header"] != header
            or metadata["response_geometry"] != payload["geometry"]
            or metadata["requested_years"] != [int(params["start"]), int(params["end"])]
            or metadata["received_record_count_including_annual_summaries"] != len(values)
        ):
            raise PowerDataError(
                "Cached metadata and NASA POWER response disagree; restore the matching "
                "sidecar/response pair or use a new cache path."
            )
        return payload, metadata

    request = Request(url, headers={"User-Agent": "AnomalyZero-research/0.1"})
    try:
        with urlopen(request, timeout=timeout) as response:
            status = response.status
            body = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise PowerDataError(f"NASA POWER HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise PowerDataError(f"Could not reach NASA POWER: {exc}") from exc

    if status != 200:
        raise PowerDataError(f"NASA POWER returned unexpected HTTP status {status}")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise PowerDataError("NASA POWER response was not valid JSON") from exc
    try:
        values, parameter_metadata, response_header = _validate_power_payload(payload, params)
    except PowerDataError as exc:
        messages = payload.get("messages", []) if isinstance(payload, dict) else []
        raise PowerDataError(f"NASA POWER response is invalid: {exc} Messages: {messages}") from exc

    metadata = {
        "institution": "NASA Langley Research Center POWER Project",
        "service": "NASA POWER Monthly and Annual API",
        "request_url": url,
        "parameters": params,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "http_status": status,
        "parameter_metadata": parameter_metadata,
        "response_header": response_header,
        "response_geometry": payload.get("geometry", {}),
        "response_messages": payload.get("messages", []),
        "requested_years": [int(params["start"]), int(params["end"])],
        "received_record_count_including_annual_summaries": len(
            values
        ),
        "restrictions": [
            "A point request represents a single location, not a basin-wide spatial average.",
            "Monthly POWER responses may include month 13 annual summaries.",
            "The service response is preserved as received; annual summaries are excluded only during monthly parsing.",
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return payload, metadata


def parse_power_monthly(
    payload: dict[str, Any],
    *,
    parameter: str = "T2M",
    latitude: float = LOCATION["latitude"],
    longitude: float = LOCATION["longitude"],
    source: str = "NASA POWER",
) -> pd.DataFrame:
    """Extract month 01..12 records; month 13 annual summaries are excluded."""
    try:
        raw_values = payload["properties"]["parameter"][parameter]
        unit = payload["parameters"][parameter]["units"]
    except (KeyError, TypeError) as exc:
        raise PowerDataError(
            f"Response is missing monthly values or metadata for {parameter}"
        ) from exc
    if not isinstance(raw_values, dict) or not unit:
        raise PowerDataError("Parameter values or units have an invalid format")

    fill_value = payload.get("header", {}).get("fill_value")
    rows: list[dict[str, Any]] = []
    for period_key, raw_value in raw_values.items():
        key = str(period_key)
        if len(key) != 6 or not key.isdigit():
            raise PowerDataError(f"Unexpected monthly period key: {period_key!r}")
        year, month = int(key[:4]), int(key[4:])
        if month == 13:
            continue
        if month < 1 or month > 12:
            raise PowerDataError(f"Invalid month in response key: {key}")
        if raw_value is None:
            value = float("nan")
        else:
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise PowerDataError(f"Non-numeric value for period {key}") from exc
        is_missing = (
            raw_value is None
            or not math.isfinite(value)
            or (fill_value is not None and value == float(fill_value))
        )
        timestamp = pd.Period(year=year, month=month, freq="M").to_timestamp()
        rows.append(
            {
                "timestamp": timestamp,
                "value": float("nan") if is_missing else value,
                "variable": parameter,
                "unit": unit,
                "source": source,
                "latitude": latitude,
                "longitude": longitude,
                "is_missing": is_missing,
            }
        )
    frame = pd.DataFrame(rows, columns=[
        "timestamp", "value", "variable", "unit", "source",
        "latitude", "longitude", "is_missing",
    ])
    return frame.sort_values("timestamp", kind="stable").reset_index(drop=True)


def parse_power_annual(
    payload: dict[str, Any], *, parameter: str = "T2M"
) -> pd.DataFrame:
    """Extract the API's month-13 annual summaries separately from monthly data."""
    try:
        raw_values = payload["properties"]["parameter"][parameter]
        unit = payload["parameters"][parameter]["units"]
    except (KeyError, TypeError) as exc:
        raise PowerDataError(
            f"Response is missing annual values or metadata for {parameter}"
        ) from exc
    if not isinstance(raw_values, dict) or not unit:
        raise PowerDataError("Parameter values or units have an invalid format")
    fill_value = payload.get("header", {}).get("fill_value")
    rows: list[dict[str, Any]] = []
    for period_key, raw_value in raw_values.items():
        key = str(period_key)
        if len(key) == 6 and key.isdigit() and key.endswith("13"):
            if raw_value is None:
                value = float("nan")
            else:
                try:
                    value = float(raw_value)
                except (TypeError, ValueError) as exc:
                    raise PowerDataError(
                        f"Non-numeric annual value for period {key}"
                    ) from exc
            missing = (
                raw_value is None
                or not math.isfinite(value)
                or (fill_value is not None and value == float(fill_value))
            )
            rows.append(
                {
                    "year": int(key[:4]),
                    "value": float("nan") if missing else value,
                    "unit": unit,
                    "variable": parameter,
                    "is_missing": missing,
                }
            )
        elif len(key) == 6 and key.isdigit() and not 1 <= int(key[4:]) <= 12:
            raise PowerDataError(f"Invalid month in response key: {key}")
    return pd.DataFrame(
        rows, columns=["year", "value", "unit", "variable", "is_missing"]
    ).sort_values("year", kind="stable").reset_index(drop=True)
