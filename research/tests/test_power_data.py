import json
from unittest.mock import Mock, patch
from urllib.parse import urlencode

import numpy as np
import pandas as pd
import pytest

from research.power_data import (
    POWER_URL,
    PowerDataError,
    build_power_query,
    fetch_power_response,
    parse_power_annual,
    parse_power_monthly,
)
from research.series_quality import (
    descriptive_summary,
    missing_months,
    monthly_climatology_and_anomalies,
    quality_summary,
)


def fixture_payload() -> dict:
    return {
        "properties": {
            "parameter": {
                "T2M": {
                    "200501": 20.0,
                    "200502": -999.0,
                    "200513": 18.0,
                }
            }
        },
        "parameters": {"T2M": {"units": "C", "longname": "Temperature at 2 Meters"}},
        "header": {
            "fill_value": -999.0,
            "start": "20050101",
            "end": "20241231",
        },
        "geometry": {"type": "Point", "coordinates": [147.354, -35.126, 285.71]},
        "messages": [],
    }


def fixture_metadata(payload: dict, query: dict | None = None) -> dict:
    params = query or build_power_query()
    variable = params["parameters"]
    values = payload["properties"]["parameter"][variable]
    return {
        "institution": "NASA Langley Research Center POWER Project",
        "service": "NASA POWER Monthly and Annual API",
        "request_url": f"{POWER_URL}?{urlencode(params)}",
        "parameters": params,
        "retrieved_at_utc": "2026-11-14T16:00:00+00:00",
        "http_status": 200,
        "parameter_metadata": payload["parameters"][variable],
        "response_header": payload["header"],
        "response_geometry": payload["geometry"],
        "requested_years": [int(params["start"]), int(params["end"])],
        "received_record_count_including_annual_summaries": len(values),
        "response_messages": [],
        "restrictions": [],
    }


def write_cache(tmp_path, payload: dict, metadata: dict | None = None):
    raw_path = tmp_path / "power.json"
    raw_path.write_text(json.dumps(payload), encoding="utf-8")
    raw_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata or fixture_metadata(payload)), encoding="utf-8"
    )
    return raw_path


def test_build_query_uses_explicit_monthly_point_arguments() -> None:
    query = build_power_query()

    assert query == {
        "parameters": "T2M",
        "community": "AG",
        "longitude": "147.353737883333",
        "latitude": str(-35.1257741166667),
        "start": "2005",
        "end": "2024",
        "format": "JSON",
    }


def test_build_query_rejects_invalid_year_order() -> None:
    with pytest.raises(ValueError):
        build_power_query(2024, 2005)


def test_parser_skips_annual_month_13_and_marks_fill_value() -> None:
    frame = parse_power_monthly(fixture_payload())

    assert len(frame) == 2
    assert frame["timestamp"].is_monotonic_increasing
    assert frame["unit"].unique().tolist() == ["C"]
    assert frame["is_missing"].tolist() == [False, True]
    assert frame["value"].iloc[0] == 20.0
    assert np.isnan(frame["value"].iloc[1])


def test_parser_handles_null_and_extracts_annual_summary_separately() -> None:
    payload = fixture_payload()
    payload["properties"]["parameter"]["T2M"]["200501"] = None

    monthly = parse_power_monthly(payload)
    annual = parse_power_annual(payload)

    assert len(monthly) == 2
    assert monthly["is_missing"].tolist() == [True, True]
    assert annual[["year", "value"]].to_dict("records") == [{"year": 2005, "value": 18.0}]


def test_parser_rejects_missing_requested_variable() -> None:
    with pytest.raises(PowerDataError):
        parse_power_monthly({"properties": {"parameter": {}}})


def quality_frame(timestamps: list[str | None]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(timestamps),
            "value": np.arange(len(timestamps), dtype=float),
            "is_missing": [False] * len(timestamps),
        }
    )


def test_quality_preserves_exact_duplicate_metrics_and_counts_month_duplicates() -> None:
    frame = quality_frame(["2005-01-01", "2005-01-01", "2005-02-01"])

    report = quality_summary(frame, "2005-01", "2005-02")

    assert report["duplicate_rows"] == 2
    assert report["duplicate_months"] == 1
    assert report["duplicate_timestamp_rows"] == 2
    assert report["duplicate_timestamp_repeats"] == 1
    assert report["duplicate_month_rows"] == 2
    assert report["duplicate_months_count"] == 1
    assert report["valid_months"] == 2


def test_quality_detects_distinct_timestamps_in_same_month_without_mutating_rows() -> None:
    frame = quality_frame(["2005-01-01", "2005-01-15", "2005-02-01"])
    before = frame.copy(deep=True)

    report = quality_summary(frame, "2005-01", "2005-02")

    assert report["duplicate_rows"] == 0
    assert report["duplicate_months"] == 0
    assert report["duplicate_timestamp_rows"] == 0
    assert report["duplicate_timestamp_repeats"] == 0
    assert report["duplicate_month_rows"] == 2
    assert report["duplicate_months_count"] == 1
    assert report["valid_months"] == 2
    pd.testing.assert_frame_equal(frame, before)


def test_quality_reports_no_duplicates_for_consecutive_months() -> None:
    report = quality_summary(
        quality_frame(["2005-01-01", "2005-02-01", "2005-03-01"]),
        "2005-01",
        "2005-03",
    )

    assert report["duplicate_rows"] == 0
    assert report["duplicate_months"] == 0
    assert report["duplicate_timestamp_rows"] == 0
    assert report["duplicate_month_rows"] == 0
    assert report["duplicate_months_count"] == 0


def test_quality_is_order_independent_and_does_not_count_nat_as_a_duplicate_month() -> None:
    report = quality_summary(
        quality_frame(["2005-02-01", None, "2005-01-15", "2005-01-01"]),
        "2005-01",
        "2005-02",
    )

    assert report["valid_months"] == 2
    assert report["duplicate_timestamp_rows"] == 0
    assert report["duplicate_month_rows"] == 2
    assert report["duplicate_months_count"] == 1
    assert report["missing_or_invalid_rows"] == 1


def test_quality_accepts_single_record_and_empty_frame() -> None:
    single = quality_summary(quality_frame(["2005-01-15"]), "2005-01", "2005-02")
    empty_frame = pd.DataFrame(
        {
            "timestamp": pd.Series(dtype="datetime64[ns]"),
            "value": pd.Series(dtype=float),
            "is_missing": pd.Series(dtype=bool),
        }
    )
    empty = quality_summary(empty_frame, "2005-01", "2005-02")

    assert single["duplicate_month_rows"] == 0
    assert single["duplicate_months_count"] == 0
    assert single["valid_months"] == 1
    assert empty["received_rows"] == 0
    assert empty["valid_months"] == 0
    assert empty["absent_months"] == ["2005-01", "2005-02"]
    assert [str(period) for period in missing_months(empty_frame, "2005-01", "2005-02")] == [
        "2005-01",
        "2005-02",
    ]
    assert empty["duplicate_month_rows"] == 0
    assert empty["duplicate_months_count"] == 0


def test_quality_keeps_full_240_month_series_unchanged() -> None:
    frame = quality_frame(
        [timestamp.isoformat() for timestamp in pd.date_range("2005-01-01", periods=240, freq="MS")]
    )

    report = quality_summary(frame, "2005-01", "2024-12")

    assert report["expected_months"] == 240
    assert report["received_rows"] == 240
    assert report["valid_months"] == 240
    assert report["missing_or_invalid_rows"] == 0
    assert report["duplicate_timestamp_rows"] == 0
    assert report["duplicate_month_rows"] == 0
    assert report["duplicate_months_count"] == 0
    assert report["absent_months"] == []


def test_descriptive_statistics_and_anomaly_reference() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(["2005-01-01", "2006-01-01", "2005-02-01"]),
            "value": [10.0, 12.0, 20.0],
            "is_missing": [False, False, False],
        }
    )

    summary = descriptive_summary(frame)
    climatology, anomalies = monthly_climatology_and_anomalies(
        frame, reference_start="2005-01", reference_end="2006-01"
    )

    assert summary["mean"] == pytest.approx(14.0)
    assert summary["iqr"] == pytest.approx(5.0)
    assert climatology.loc[1] == pytest.approx(11.0)
    assert anomalies.iloc[0] == pytest.approx(-1.0)
    assert anomalies.iloc[1] == pytest.approx(1.0)


def test_cached_response_is_reused_without_network(tmp_path) -> None:
    raw_payload = fixture_payload()
    raw_path = write_cache(tmp_path, raw_payload)

    with patch("research.power_data.urlopen") as opener:
        payload, returned_metadata = fetch_power_response(raw_path)

    opener.assert_not_called()
    assert payload == raw_payload
    assert returned_metadata == fixture_metadata(raw_payload)


def test_cache_without_sidecar_fails_without_network(tmp_path) -> None:
    raw_path = tmp_path / "power.json"
    raw_path.write_text(json.dumps(fixture_payload()), encoding="utf-8")

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="metadata sidecar missing"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_corrupt_sidecar_fails_without_network(tmp_path) -> None:
    raw_path = write_cache(tmp_path, fixture_payload())
    raw_path.with_suffix(".metadata.json").write_text("{broken", encoding="utf-8")

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="metadata is invalid"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_incomplete_sidecar_fails_without_network(tmp_path) -> None:
    payload = fixture_payload()
    raw_path = write_cache(tmp_path, payload, {"parameters": build_power_query()})

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="required provenance fields are missing"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_sidecar_with_invalid_retrieval_timestamp_fails_without_network(tmp_path) -> None:
    payload = fixture_payload()
    metadata = fixture_metadata(payload)
    metadata["retrieved_at_utc"] = "not-a-timestamp"
    raw_path = write_cache(tmp_path, payload, metadata)

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="invalid retrieval timestamp"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_cached_response_rejects_different_query_parameters(tmp_path) -> None:
    payload = fixture_payload()
    raw_path = write_cache(tmp_path, payload)
    metadata = fixture_metadata(payload)
    metadata["parameters"] = build_power_query(parameter="PRECIP")
    raw_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="parameters do not match"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()
    assert json.loads(raw_path.read_text(encoding="utf-8")) == payload


def test_cached_malformed_json_fails_without_network(tmp_path) -> None:
    raw_path = write_cache(tmp_path, fixture_payload())
    raw_path.write_text("{broken", encoding="utf-8")

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="response is malformed"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_cached_response_rejects_missing_variable_without_network(tmp_path) -> None:
    payload = fixture_payload()
    metadata = fixture_metadata(payload)
    payload["properties"]["parameter"] = {}
    raw_path = write_cache(tmp_path, payload, metadata)

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="does not contain usable values"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_cached_response_rejects_sidecar_response_mismatch_without_network(tmp_path) -> None:
    payload = fixture_payload()
    raw_path = write_cache(tmp_path, payload)
    metadata = fixture_metadata(payload)
    metadata["response_header"] = {**payload["header"], "end": "20231231"}
    raw_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="metadata and NASA POWER response disagree"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_cached_response_rejects_header_period_contradiction(tmp_path) -> None:
    payload = fixture_payload()
    payload["header"]["end"] = "20231231"
    raw_path = write_cache(tmp_path, payload)

    with patch("research.power_data.urlopen") as opener, pytest.raises(
        PowerDataError, match="period contradicts"
    ):
        fetch_power_response(raw_path)

    opener.assert_not_called()


def test_force_true_deliberately_fetches_and_replaces_invalid_cache(tmp_path) -> None:
    payload = fixture_payload()
    raw_path = write_cache(tmp_path, payload)
    raw_path.with_suffix(".metadata.json").write_text("not-json", encoding="utf-8")
    response = Mock(status=200, read=Mock(return_value=json.dumps(payload).encode()))

    with patch("research.power_data.urlopen") as opener:
        opener.return_value.__enter__.return_value = response
        returned_payload, metadata = fetch_power_response(raw_path, force=True)

    opener.assert_called_once()
    assert returned_payload == payload
    assert metadata["http_status"] == 200
    assert json.loads(raw_path.read_text(encoding="utf-8")) == payload
    assert json.loads(raw_path.with_suffix(".metadata.json").read_text(encoding="utf-8")) == metadata
