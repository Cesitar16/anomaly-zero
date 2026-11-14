"""Small, offline-testable helpers for monthly environmental time series."""

from __future__ import annotations

import numpy as np
import pandas as pd


def missing_months(
    frame: pd.DataFrame,
    start: str | pd.Period,
    end: str | pd.Period,
    *,
    timestamp_column: str = "timestamp",
) -> pd.PeriodIndex:
    """Return absent calendar months within an inclusive monthly interval."""
    expected = pd.period_range(start=start, end=end, freq="M")
    observed = pd.PeriodIndex(
        pd.to_datetime(frame[timestamp_column]).dt.to_period("M").unique(), freq="M"
    )
    return expected.difference(observed).sort_values()


def quality_summary(
    frame: pd.DataFrame,
    start: str | pd.Period,
    end: str | pd.Period,
    *,
    timestamp_column: str = "timestamp",
    value_column: str = "value",
    missing_column: str = "is_missing",
) -> dict[str, object]:
    """Summarize coverage and duplicate timestamps/months without altering rows.

    duplicate_rows counts all rows participating in an exact-timestamp
    duplicate; duplicate_months preserves its legacy meaning as the count of
    exact-timestamp repetitions after the first. The explicit timestamp
    metrics have those same meanings. duplicate_month_rows counts every
    row participating in any repeated calendar month, and
    duplicate_months_count counts distinct calendar months with repeats.
    Missing timestamps (NaT) are not treated as duplicates or valid months.
    """
    expected = pd.period_range(start=start, end=end, freq="M")
    timestamps = pd.to_datetime(frame[timestamp_column])
    values = pd.to_numeric(frame[value_column], errors="coerce")
    missing_flags = (
        frame[missing_column].astype(bool)
        if missing_column in frame
        else values.isna()
    )
    expected_set = set(expected)
    periods = timestamps.dt.to_period("M")
    in_range = periods.isin(expected_set)
    valid = values.notna() & np.isfinite(values) & ~missing_flags & in_range
    valid_months = int(periods[valid].nunique())
    has_timestamp = timestamps.notna()
    exact_duplicate_rows = int(
        (has_timestamp & timestamps.duplicated(keep=False)).sum()
    )
    exact_duplicate_repeats = int(
        (has_timestamp & timestamps.duplicated(keep="first")).sum()
    )
    has_period = periods.notna()
    duplicate_month_mask = has_period & periods.duplicated(keep=False)
    duplicate_month_rows = int(duplicate_month_mask.sum())
    duplicate_months_count = int(periods[duplicate_month_mask].nunique())
    absent = missing_months(frame, start, end, timestamp_column=timestamp_column)
    return {
        "expected_months": len(expected),
        "received_rows": len(frame),
        "valid_months": valid_months,
        "missing_or_invalid_rows": int((~valid).sum()),
        "missing_or_invalid_percent_of_expected": (
            float((len(expected) - valid_months) / len(expected) * 100)
            if len(expected)
            else float("nan")
        ),
        "duplicate_rows": exact_duplicate_rows,
        "duplicate_months": exact_duplicate_repeats,
        "duplicate_timestamp_rows": exact_duplicate_rows,
        "duplicate_timestamp_repeats": exact_duplicate_repeats,
        "duplicate_month_rows": duplicate_month_rows,
        "duplicate_months_count": duplicate_months_count,
        "absent_months": [str(period) for period in absent],
        "non_finite_values": int((values.notna() & ~np.isfinite(values)).sum()),
        "minimum_valid_value": float(values[valid].min()) if valid.any() else None,
        "maximum_valid_value": float(values[valid].max()) if valid.any() else None,
    }


def descriptive_summary(
    frame: pd.DataFrame, *, value_column: str = "value"
) -> pd.Series:
    """Return common descriptive statistics on observed finite values only."""
    values = pd.to_numeric(frame[value_column], errors="coerce")
    values = values[np.isfinite(values)]
    if "is_missing" in frame:
        values = values[~frame.loc[values.index, "is_missing"].astype(bool)]
    result = values.describe(percentiles=[0.25, 0.5, 0.75])
    result["iqr"] = float(values.quantile(0.75) - values.quantile(0.25))
    return result


def monthly_climatology_and_anomalies(
    frame: pd.DataFrame,
    *,
    reference_start: str = "2005-01",
    reference_end: str = "2024-12",
    timestamp_column: str = "timestamp",
    value_column: str = "value",
) -> tuple[pd.Series, pd.Series]:
    """Compute calendar-month means and departures from those means.

    These are descriptive anomalies relative to the explicitly supplied period;
    they are not statistical significance tests.
    """
    data = frame[[timestamp_column, value_column]].copy()
    data[timestamp_column] = pd.to_datetime(data[timestamp_column])
    values = pd.to_numeric(data[value_column], errors="coerce")
    valid = values.notna() & np.isfinite(values)
    if "is_missing" in frame:
        valid &= ~frame["is_missing"].astype(bool)
    data = data.loc[valid].copy()
    data["_value"] = values.loc[valid]
    start = pd.Period(reference_start, freq="M").start_time
    end = pd.Period(reference_end, freq="M").end_time
    reference = data[data[timestamp_column].between(start, end)]
    climatology = reference.groupby(reference[timestamp_column].dt.month)["_value"].mean()
    anomalies = data["_value"] - data[timestamp_column].dt.month.map(climatology)
    anomalies.index = pd.DatetimeIndex(data[timestamp_column], name=timestamp_column)
    return climatology, anomalies
