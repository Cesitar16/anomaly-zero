"""Read and validate an existing DS-03 point snapshot; never build one here."""

from __future__ import annotations

import json
import math
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from research.snapshot_format import dataset_id_for_input_fingerprint, snapshot_sha256

MAX_SNAPSHOT_BYTES = 1024 * 1024
SNAPSHOT_SCHEMA_VERSION = "1.0.0"
PRODUCT = {
    "product_id": "GPM_3IMERGM",
    "short_name": "GPM_3IMERGM",
    "collection_id": "C2723754851-GES_DISC",
    "collection_version": "07",
    "product_version": "V07B",
    "doi": "10.5067/GPM/IMERG/3B-MONTH/07",
    "variable": "precipitation",
    "variable_path": "Grid/precipitation",
    "quantity": "monthly_mean_rate",
    "unit": "mm/hr",
}
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_DATASET_ID = re.compile(r"^imerg-2005-point-[0-9a-f]{20}$")
_MONTHS = tuple(f"2005-{month:02d}" for month in range(1, 13))


class SnapshotUnavailableError(Exception):
    """The configured snapshot file cannot be read."""


class SnapshotInvalidError(Exception):
    """The snapshot is oversized, malformed, or inconsistent."""


def _invalid(message: str) -> None:
    raise SnapshotInvalidError(message)


def _duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _invalid("Snapshot JSON contains duplicate fields")
        result[key] = value
    return result


def _reject_constant(_: str) -> None:
    _invalid("Snapshot JSON contains a non-finite number")


def _require(condition: bool, message: str) -> None:
    if not condition:
        _invalid(message)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _finite_json(value: Any) -> bool:
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, list):
        return all(_finite_json(item) for item in value)
    if isinstance(value, dict):
        return all(_finite_json(item) for item in value.values())
    return True


def _validate_snapshot(snapshot: Any) -> dict[str, Any]:
    _require(isinstance(snapshot, dict), "Snapshot root must be an object")
    _require(snapshot.get("snapshot_schema_version") == SNAPSHOT_SCHEMA_VERSION, "Unsupported snapshot schema version")
    _require(isinstance(snapshot.get("synthetic"), bool), "Snapshot synthetic marker is missing or invalid")
    _require(
        isinstance(snapshot.get("dataset_id"), str)
        and _DATASET_ID.fullmatch(snapshot["dataset_id"]) is not None,
        "Snapshot dataset identity is invalid",
    )
    _require(snapshot.get("product") == PRODUCT, "Snapshot product identity is incompatible")

    requested = snapshot.get("requested_coverage")
    available = snapshot.get("available_coverage")
    _require(
        requested == {"start": _MONTHS[0], "end": _MONTHS[-1], "end_inclusive": True},
        "Snapshot requested coverage is incompatible",
    )
    _require(
        available == {"start": _MONTHS[0], "end": _MONTHS[-1]},
        "Snapshot available coverage is incompatible",
    )

    series = snapshot.get("series")
    _require(isinstance(series, list) and len(series) == len(_MONTHS), "Snapshot monthly series is incomplete")
    missing: list[str] = []
    for month, point in zip(_MONTHS, series, strict=True):
        _require(isinstance(point, dict), "Snapshot series point is invalid")
        _require(point.get("date") == f"{month}-01", "Snapshot periods are missing, duplicated, or out of order")
        try:
            date.fromisoformat(point["date"])
        except (KeyError, TypeError, ValueError):
            _invalid("Snapshot contains an invalid month")
        value = point.get("value")
        quality_point = point.get("quality")
        _require(isinstance(quality_point, dict), "Snapshot point quality is missing")
        _require(isinstance(quality_point.get("provider_flags"), list), "Snapshot point provider flags are invalid")
        reason = quality_point.get("missing_reason")
        if value is None:
            _require(quality_point.get("state") == "missing", "Missing snapshot point has an incompatible state")
            _require(isinstance(reason, str) and bool(reason), "Missing snapshot point has no reason")
            missing.append(month)
        else:
            _require(
                isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value),
                "Snapshot values must be finite numbers or null",
            )
            _require(quality_point.get("state") == "unassessed" and reason is None, "Present snapshot value has incompatible quality")

    coverage = snapshot.get("coverage")
    _require(isinstance(coverage, dict), "Snapshot coverage is missing")
    _require(
        coverage.get("expected_periods") == 12
        and coverage.get("present_periods") == 12
        and coverage.get("valid_periods") == 12 - len(missing)
        and coverage.get("missing_periods") == missing
        and coverage.get("spatial_coverage") is None,
        "Snapshot coverage does not match its monthly values",
    )
    _require(
        snapshot.get("data_state") == ("available_with_gaps" if missing else "available"),
        "Snapshot data_state does not match its monthly values",
    )

    support = snapshot.get("spatial_aggregation")
    _require(
        isinstance(support, dict)
        and support.get("support_type") == "point_sample"
        and support.get("approval_state") == "not_assessed",
        "Snapshot spatial support is not the DS-03 point sample",
    )
    point = support.get("point")
    _require(isinstance(point, dict), "Snapshot point coordinates are missing")
    latitude, longitude = point.get("latitude"), point.get("longitude")
    _require(
        isinstance(latitude, (int, float))
        and not isinstance(latitude, bool)
        and math.isfinite(latitude)
        and -90 <= latitude <= 90
        and isinstance(longitude, (int, float))
        and not isinstance(longitude, bool)
        and math.isfinite(longitude)
        and -180 <= longitude <= 180,
        "Snapshot point coordinates are invalid",
    )
    cell_match = re.fullmatch(
        r"IMERG-v07b-center-lon(?P<longitude_index>\d+)-lat(?P<latitude_index>\d+)",
        point.get("cell_id", ""),
    )
    _require(cell_match is not None, "Snapshot point cell identity is invalid")

    quality = snapshot.get("quality")
    _require(
        isinstance(quality, dict)
        and quality.get("provider_flags_applied") is False
        and quality.get("verification_state") == "basic_checks_only"
        and quality.get("finite_non_fill_filter_applied") is True
        and quality.get("mask_applied") is None,
        "Snapshot QA metadata is incompatible with DS-03",
    )
    _require(isinstance(quality.get("source_flag_fields"), list), "Snapshot source QA fields are invalid")
    _require(isinstance(quality.get("qa_checks"), list), "Snapshot QA checks are invalid")

    provenance = snapshot.get("provenance")
    _require(isinstance(provenance, dict), "Snapshot provenance is missing")
    processing = provenance.get("processing")
    _require(
        isinstance(processing, dict)
        and processing.get("pipeline") == "research.build_ful116_snapshot"
        and processing.get("pipeline_version") == "1.0.0"
        and _is_sha256(processing.get("code_sha256")),
        "Snapshot processing provenance is incompatible",
    )
    selection = provenance.get("point_selection")
    _require(
        isinstance(selection, dict)
        and isinstance(selection.get("selection_id"), str)
        and selection.get("grid_registration") == "center"
        and isinstance(selection.get("latitude"), (int, float))
        and isinstance(selection.get("longitude"), (int, float))
        and math.isclose(selection["latitude"], latitude, rel_tol=0, abs_tol=2e-6)
        and math.isclose(selection["longitude"], longitude, rel_tol=0, abs_tol=2e-6),
        "Snapshot point selection provenance is incompatible",
    )
    records = provenance.get("source_records")
    _require(isinstance(records, list) and len(records) == 12, "Snapshot source records are incomplete")
    source_class = "synthetic_fixture" if snapshot["synthetic"] else "verified_nasa_granule"
    for month, record in zip(_MONTHS, records, strict=True):
        _require(isinstance(record, dict), "Snapshot source record is invalid")
        expected_filename = (
            f"3B-MO.MS.MRG.3IMERG.{month.replace('-', '')}01-S000000-E235959."
            f"{month[-2:]}.V07B.HDF5"
        )
        expected_granule_id = record.get("granule_id")
        _require(
            record.get("period") == month
            and record.get("source_class") == source_class
            and record.get("filename") == expected_filename
            and record.get("collection_id") == PRODUCT["collection_id"]
            and record.get("product") == PRODUCT["product_id"]
            and record.get("collection_version") == PRODUCT["collection_version"]
            and record.get("product_version") == PRODUCT["product_version"]
            and record.get("variable_path") == PRODUCT["variable_path"]
            and record.get("units") == PRODUCT["unit"]
            and type(record.get("bytes")) is int
            and record["bytes"] > 0
            and _is_sha256(record.get("sha256"))
            and _is_sha256(record.get("manifest_sha256")),
            "Snapshot source identity or hashes are inconsistent",
        )
        retrieved_at = record.get("retrieved_at")
        try:
            retrieved_timestamp = datetime.fromisoformat(retrieved_at)
        except (AttributeError, TypeError, ValueError):
            _invalid("Snapshot retrieval timestamp is invalid")
        _require(retrieved_timestamp.utcoffset() == timedelta(0), "Snapshot retrieval timestamp is not UTC")
        if snapshot["synthetic"]:
            _require(
                expected_granule_id is None
                and record.get("producer_granule_id") is None
                and isinstance(record.get("source_metadata_url"), str)
                and record["source_metadata_url"].startswith("fixture://"),
                "Synthetic source provenance is inconsistent",
            )
        else:
            _require(
                isinstance(expected_granule_id, str)
                and re.fullmatch(r"G\d+-GES_DISC", expected_granule_id) is not None
                and record.get("producer_granule_id") == f"GPM_3IMERGM.07:{expected_filename}"
                and record.get("source_metadata_url")
                == f"https://cmr.earthdata.nasa.gov/search/concepts/{expected_granule_id}.umm_json",
                "NASA source provenance is inconsistent",
            )
    _require(
        provenance.get("agency") == (None if snapshot["synthetic"] else "NASA")
        and provenance.get("distributor") == ("synthetic test fixture" if snapshot["synthetic"] else "GES DISC via Earthdata CMR"),
        "Snapshot provenance origin is inconsistent",
    )

    expected_dataset_fingerprint = {
        "pipeline_version": processing["pipeline_version"],
        "collection_id": PRODUCT["collection_id"],
        "doi": PRODUCT["doi"],
        "point": {
            "selection_id": selection["selection_id"],
            "latitude": latitude,
            "longitude": longitude,
            "latitude_index": int(cell_match["latitude_index"]),
            "longitude_index": int(cell_match["longitude_index"]),
        },
        "granule_sha256s": [record["sha256"] for record in records],
        "manifest_sha256s": [record["manifest_sha256"] for record in records],
    }
    expected_dataset_id = dataset_id_for_input_fingerprint(expected_dataset_fingerprint)
    _require(snapshot["dataset_id"] == expected_dataset_id, "Snapshot dataset identity does not match its sources")

    values_by_period = snapshot.get("values_by_period")
    _require(isinstance(values_by_period, list) and len(values_by_period) == 12, "Snapshot period values are incomplete")
    for month, value_row, series_point in zip(_MONTHS, values_by_period, series, strict=True):
        _require(
            isinstance(value_row, dict)
            and value_row.get("period") == month
            and value_row.get("raw_value") == series_point["value"]
            and value_row.get("state")
            == ("finite_nonfill" if series_point["value"] is not None else series_point["quality"]["missing_reason"])
            and isinstance(value_row.get("coordinates"), dict)
            and value_row["coordinates"].get("latitude") == latitude
            and value_row["coordinates"].get("longitude") == longitude,
            "Snapshot period values disagree with the series",
        )

    snapshot_digest = snapshot.get("snapshot_sha256")
    _require(_is_sha256(snapshot_digest), "Snapshot hash is missing or malformed")
    try:
        actual_digest = snapshot_sha256(snapshot)
    except (TypeError, ValueError, OverflowError) as exc:
        raise SnapshotInvalidError("Snapshot contains values that cannot be canonically hashed") from exc
    _require(actual_digest == snapshot_digest, "Snapshot hash does not match its content")
    return snapshot


def read_snapshot(path: Path) -> dict[str, Any]:
    """Read a server-selected DS-03 JSON file without modifying or generating it."""
    try:
        if path.stat().st_size > MAX_SNAPSHOT_BYTES:
            _invalid("Snapshot exceeds the configured size limit")
        with path.open("rb") as source:
            raw = source.read(MAX_SNAPSHOT_BYTES + 1)
    except SnapshotInvalidError:
        raise
    except OSError as exc:
        raise SnapshotUnavailableError("Configured snapshot is unavailable") from exc
    if len(raw) > MAX_SNAPSHOT_BYTES:
        _invalid("Snapshot exceeds the configured size limit")
    try:
        snapshot = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_duplicate_keys,
            parse_constant=_reject_constant,
        )
    except SnapshotInvalidError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise SnapshotInvalidError("Snapshot JSON is invalid") from exc
    _require(_finite_json(snapshot), "Snapshot contains a non-finite number")
    return _validate_snapshot(snapshot)
