"""Leakage-aware, single-support monthly feature engineering for DS-05.

This module transforms one verified univariate monthly series at one spatial
support. It deliberately does not join NASA products or authorize regional
aggregation.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = {
    "period", "value", "product", "variable", "unit", "support_id", "source_sha256", "source_kind", "qa_status", "eligible"
}
PRODUCT_UNITS = {
    ("imerg_final", "precipitation"): "mm/hr",
    ("merra2", "T2M"): "K",
    ("gldas", "SoilMoi0_10cm_inst"): "kg m-2",
}


@dataclass(frozen=True)
class FeatureResult:
    frame: pd.DataFrame
    metadata: dict[str, object]


def monthly_rate_to_depth(
    rate: pd.Series,
    periods: pd.PeriodIndex,
    *,
    unit: str,
    interpretation_confirmed: bool,
) -> pd.Series:
    """Convert an interval-mean precipitation rate (mm/hr) to depth (mm).

    This conversion is opt-in because IMERG's temporal interpretation must be
    confirmed for the input. Each monthly rate is multiplied by the actual
    number of calendar hours in its month; original rates remain unchanged.
    """
    if unit != "mm/hr":
        raise ValueError("precipitation_rate_unit_must_be_mm_per_hour")
    if not interpretation_confirmed:
        raise ValueError("monthly_rate_interpretation_not_confirmed")
    if len(rate) != len(periods):
        raise ValueError("rate_period_length_mismatch")
    periods = pd.PeriodIndex(periods, freq="M")
    if periods.has_duplicates:
        raise ValueError("duplicate_months")
    hours = np.array([calendar.monthrange(p.year, p.month)[1] * 24 for p in periods])
    result = pd.Series(pd.to_numeric(rate, errors="coerce").to_numpy() * hours, index=rate.index, name="precipitation_depth_mm")
    return result


def build_monthly_features(observations: pd.DataFrame) -> FeatureResult:
    """Build causal calendar, lag, rolling and change features for one series.

    The value at month *t* and trailing window ending at *t* are available
    only after month *t* is complete. Forecasting month t+1 should use row t.
    Missing calendar months are inserted as NaN, so lags/windows never bridge
    gaps silently. Imputation, scaling and target construction are excluded.
    """
    missing = REQUIRED_COLUMNS - set(observations.columns)
    if missing:
        raise ValueError(f"missing_required_columns:{','.join(sorted(missing))}")
    frame = observations.copy()
    frame["period"] = pd.PeriodIndex(frame["period"].astype(str), freq="M")
    if frame["period"].duplicated().any():
        raise ValueError("duplicate_months")
    if len(frame) == 0:
        raise ValueError("empty_series")
    identity_columns = ["product", "variable", "unit", "support_id", "source_kind"]
    if any(frame[column].nunique(dropna=False) != 1 for column in identity_columns):
        raise ValueError("mixed_series_identity_or_spatial_support")
    product = str(frame["product"].iloc[0])
    variable = str(frame["variable"].iloc[0])
    unit = str(frame["unit"].iloc[0])
    expected = PRODUCT_UNITS.get((product, variable))
    if expected is None or unit != expected:
        raise ValueError("product_variable_unit_mismatch")
    source_kind = str(frame["source_kind"].iloc[0])
    is_true = frame["eligible"].map(lambda value: value is True or isinstance(value, np.bool_) and bool(value))
    if not is_true.all():
        raise ValueError("ineligible_observation_present")
    if source_kind not in {"verified_nasa_granule", "synthetic_fixture"}:
        raise ValueError("unknown_source_kind")
    if source_kind == "synthetic_fixture" and not frame.get("synthetic_fixture", pd.Series(False, index=frame.index)).astype(bool).all():
        raise ValueError("synthetic_fixture_marker_missing")
    if source_kind == "verified_nasa_granule" and (
        frame["source_sha256"].isna().any()
        or not frame["source_sha256"].astype(str).str.fullmatch(r"[0-9a-fA-F]{64}").all()
    ):
        raise ValueError("verified_source_hash_invalid")
    if source_kind == "verified_nasa_granule":
        for flag in ("hash_verified", "size_verified", "native_payload_verified"):
            if flag not in frame or not frame[flag].eq(True).all():
                raise ValueError(f"source_{flag}_missing")
    ordered = frame.sort_values("period").set_index("period")
    full_index = pd.period_range(ordered.index.min(), ordered.index.max(), freq="M")
    series = pd.to_numeric(ordered["value"], errors="coerce").astype(float).reindex(full_index)
    if np.isinf(series.to_numpy()).any():
        raise ValueError("infinite_observation")

    result = pd.DataFrame(index=full_index)
    result.index.name = "period"
    months = result.index.month
    result["month_sin"] = np.sin(2 * np.pi * months / 12)
    result["month_cos"] = np.cos(2 * np.pi * months / 12)
    seasons = {12: "summer", 1: "summer", 2: "summer", 3: "autumn", 4: "autumn", 5: "autumn", 6: "winter", 7: "winter", 8: "winter", 9: "spring", 10: "spring", 11: "spring"}
    result["season_southern_hemisphere"] = [seasons[m] for m in months]
    result["observed_value"] = series
    for lag in (1, 3, 6, 12):
        result[f"lag_{lag}"] = series.shift(lag)
    result["rolling_mean_3"] = series.rolling(3, min_periods=3).mean()
    result["rolling_std_3"] = series.rolling(3, min_periods=3).std(ddof=1)
    result["difference_1"] = series.diff(1)
    result["row_present"] = result.index.isin(ordered.index)
    result["eligible"] = ordered["eligible"].reindex(full_index).fillna(False).astype(bool)
    # Keep row-level provenance beside features, never as implicit predictors.
    for column in ("source_sha256", "qa_status", "granule_id", "manifest_sha256", "source_path", "synthetic_fixture"):
        if column in ordered:
            result[column] = ordered[column].reindex(full_index)

    metadata: dict[str, object] = {
        "feature_set": "ful122_monthly_causal_v1",
        "source_kind": source_kind,
        "product": product,
        "variable": variable,
        "unit": unit,
        "support_id": str(frame["support_id"].iloc[0]),
        "qa_status": sorted(frame["qa_status"].dropna().astype(str).unique().tolist()),
        "observed_months": len(frame),
        "calendar_months": len(full_index),
        "missing_periods": [str(period) for period in full_index.difference(ordered.index)],
        "missing_value_periods": [str(period) for period in full_index[series.isna()]],
        "feature_valid_rows": {
            column: int(result[column].notna().sum())
            for column in ("month_sin", "month_cos", "lag_1", "lag_3", "lag_6", "lag_12", "rolling_mean_3", "rolling_std_3", "difference_1")
        },
        "feature_availability": {
            "implemented_verified": ["month_sin", "month_cos", "season_southern_hemisphere", "lag_1", "lag_3", "lag_6", "lag_12", "rolling_mean_3", "rolling_std_3", "difference_1"],
            "experimental_opt_in": ["precipitation_depth_mm via monthly_rate_to_depth; requires confirmed interval-mean rate interpretation"],
            "blocked": ["cross_product_relationships", "spatial_aggregation", "climatological_z_scores", "imputation", "scaling", "forecast_target", "QA filtering"],
        },
        "availability_rule": "all lag/rolling features use current or past rows only; row t is available after month t completes",
        "synthetic_notice": "SYNTHETIC TEST FIXTURE; not NASA evidence" if source_kind == "synthetic_fixture" else None,
    }
    return FeatureResult(frame=result.reset_index(), metadata=metadata)
