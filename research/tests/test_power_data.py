import json

import numpy as np
import pandas as pd
import pytest

from research.power_data import (
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
        "header": {"fill_value": -999.0},
    }


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


def test_quality_detects_gaps_duplicates_and_missing_values() -> None:
    frame = parse_power_monthly(fixture_payload())
    frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)

    report = quality_summary(frame, "2005-01", "2005-03")

    assert report["expected_months"] == 3
    assert report["received_rows"] == 3
    assert report["valid_months"] == 1
    assert report["duplicate_rows"] == 2
    assert report["duplicate_months"] == 1
    assert report["absent_months"] == ["2005-03"]
    assert [str(period) for period in missing_months(frame, "2005-01", "2005-03")] == ["2005-03"]


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
    raw_path = tmp_path / "power.json"
    raw_path.write_text(json.dumps(fixture_payload()), encoding="utf-8")
    metadata = {"request_url": "cached"}
    raw_path.with_suffix(".metadata.json").write_text(
        json.dumps(metadata), encoding="utf-8"
    )

    payload, returned_metadata = fetch_power_response(raw_path)

    assert payload == fixture_payload()
    assert returned_metadata == metadata


def test_cached_response_rejects_different_query_parameters(tmp_path) -> None:
    raw_path = tmp_path / "power.json"
    raw_path.write_text(json.dumps(fixture_payload()), encoding="utf-8")
    raw_path.with_suffix(".metadata.json").write_text(
        json.dumps({"parameters": {"parameters": "PRECIP"}}), encoding="utf-8"
    )

    with pytest.raises(PowerDataError, match="Cached response parameters differ"):
        fetch_power_response(raw_path, query=build_power_query())
