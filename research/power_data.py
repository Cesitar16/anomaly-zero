"""Cliente mínimo y parser para la API mensual de NASA POWER."""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
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
    time. Existing raw files are reused unless force=True.
    """
    path = Path(raw_path)
    metadata_path = path.with_suffix(".metadata.json")
    params = query or build_power_query()
    url = f"{POWER_URL}?{urlencode(params)}"

    if path.exists() and not force:
        payload = json.loads(path.read_text(encoding="utf-8"))
        metadata = (
            json.loads(metadata_path.read_text(encoding="utf-8"))
            if metadata_path.exists()
            else {
                "institution": "NASA Langley Research Center POWER Project",
                "service": "NASA POWER Monthly and Annual API",
                "request_url": url,
                "parameters": params,
                "retrieved_at_utc": None,
                "note": "Loaded existing raw response; retrieval timestamp unavailable.",
            }
        )
        cached_parameters = metadata.get("parameters")
        if cached_parameters is not None and cached_parameters != params:
            raise PowerDataError(
                "Cached response parameters differ from this request; use a "
                "different raw_path or set force=True deliberately."
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
    if not isinstance(payload, dict) or not isinstance(payload.get("properties"), dict):
        raise PowerDataError("NASA POWER response is missing the properties object")
    properties = payload["properties"]
    if params["parameters"] not in properties.get("parameter", {}):
        messages = payload.get("messages", [])
        raise PowerDataError(
            f"NASA POWER response has no {params['parameters']} parameter: {messages}"
        )

    metadata = {
        "institution": "NASA Langley Research Center POWER Project",
        "service": "NASA POWER Monthly and Annual API",
        "request_url": url,
        "parameters": params,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "http_status": status,
        "parameter_metadata": payload.get("parameters", {}).get(
            params["parameters"], {}
        ),
        "response_header": payload.get("header", {}),
        "response_geometry": payload.get("geometry", {}),
        "response_messages": payload.get("messages", []),
        "requested_years": [int(params["start"]), int(params["end"])],
        "received_record_count_including_annual_summaries": len(
            properties["parameter"][params["parameters"]]
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
