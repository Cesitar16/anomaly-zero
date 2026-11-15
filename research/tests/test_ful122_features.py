import numpy as np
import pandas as pd
import pytest

from research.ful122_features import build_monthly_features, monthly_rate_to_depth


def observations(periods, values):
    return pd.DataFrame(
        {
            "period": [str(period) for period in periods],
            "value": values,
            "product": "gldas",
            "variable": "SoilMoi0_10cm_inst",
            "unit": "kg m-2",
            "support_id": "synthetic-cell-1",
            "source_sha256": [None] * len(periods),
            "source_kind": "synthetic_fixture",
            "synthetic_fixture": [True] * len(periods),
            "qa_status": "synthetic_only",
            "eligible": True,
        }
    )


def test_features_are_causal_and_seasons_match_southern_hemisphere():
    periods = pd.period_range("2005-01", periods=15, freq="M")
    result = build_monthly_features(observations(periods, np.arange(15, dtype=float)))
    frame = result.frame.set_index("period")

    assert frame.loc["2005-02", "lag_1"] == 0
    assert frame.loc["2005-03", "rolling_mean_3"] == 1
    assert frame.loc["2005-03", "difference_1"] == 1
    assert frame.loc["2005-01", "season_southern_hemisphere"] == "summer"
    assert frame.loc["2005-07", "season_southern_hemisphere"] == "winter"
    assert result.metadata["source_kind"] == "synthetic_fixture"
    assert "SYNTHETIC" in result.metadata["synthetic_notice"]
    assert frame.loc["2005-01", "qa_status"] == "synthetic_only"
    assert bool(frame.loc["2005-01", "eligible"])
    assert np.isnan(frame.loc["2005-01", "rolling_mean_3"])
    assert frame.loc["2005-04", "lag_3"] == 0
    assert frame.loc["2005-07", "lag_6"] == 0
    assert frame.loc["2006-01", "lag_12"] == 0


def test_missing_month_is_inserted_and_breaks_lags_and_windows():
    periods = pd.PeriodIndex(["2005-01", "2005-02", "2005-04", "2005-05"], freq="M")
    result = build_monthly_features(observations(periods, [1, 2, 4, 5]))
    frame = result.frame.set_index("period")

    assert result.metadata["missing_periods"] == ["2005-03"]
    assert np.isnan(frame.loc["2005-04", "lag_1"])
    assert np.isnan(frame.loc["2005-04", "rolling_mean_3"])
    assert not bool(frame.loc["2005-03", "row_present"])
    assert not bool(frame.loc["2005-03", "eligible"])


@pytest.mark.parametrize("missing_value", [None, float("nan"), pd.NA])
def test_original_null_is_reported_separately_from_calendar_gap_and_zero_is_kept(missing_value):
    periods = pd.PeriodIndex(["2005-01", "2005-02", "2005-04"], freq="M")
    result = build_monthly_features(observations(periods, [0, missing_value, 4]))
    frame = result.frame.set_index("period")

    assert frame.loc["2005-01", "observed_value"] == 0
    assert np.isnan(frame.loc["2005-02", "observed_value"])
    assert result.metadata["missing_value_periods"] == ["2005-02"]
    assert result.metadata["missing_periods"] == ["2005-03"]
    assert np.isnan(frame.loc["2005-04", "difference_1"])


@pytest.mark.parametrize("bad_period", ["2005-13", "NaT", "not-a-month"])
def test_invalid_calendar_period_is_rejected(bad_period):
    frame = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    frame["period"] = bad_period

    with pytest.raises(ValueError, match="invalid_period"):
        build_monthly_features(frame)


def test_future_observations_cannot_change_features_for_prior_months():
    periods = pd.period_range("2005-01", periods=15, freq="M")
    short = build_monthly_features(observations(periods[:12], np.arange(12, dtype=float))).frame.set_index("period")
    extended = build_monthly_features(observations(periods, [*np.arange(12, dtype=float), 1e12, -1e12, 1e15])).frame.set_index("period")

    columns = ["lag_1", "lag_3", "lag_6", "lag_12", "rolling_mean_3", "rolling_std_3", "difference_1"]
    pd.testing.assert_frame_equal(short[columns], extended.loc[short.index, columns])


def test_duplicate_months_or_mixed_spatial_support_are_rejected():
    duplicate = observations(pd.PeriodIndex(["2005-01", "2005-01"], freq="M"), [1, 2])
    with pytest.raises(ValueError, match="duplicate_months"):
        build_monthly_features(duplicate)

    mixed = observations(pd.period_range("2005-01", periods=2, freq="M"), [1, 2])
    mixed.loc[1, "support_id"] = "different-cell"
    with pytest.raises(ValueError, match="mixed_series_identity"):
        build_monthly_features(mixed)

    missing_support = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    missing_support.loc[0, "support_id"] = None
    with pytest.raises(ValueError, match="missing_series_identity:support_id"):
        build_monthly_features(missing_support)

    missing_qa = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    missing_qa.loc[0, "qa_status"] = None
    with pytest.raises(ValueError, match="missing_qa_status"):
        build_monthly_features(missing_qa)


def test_units_and_synthetic_markers_are_mandatory():
    wrong_unit = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    wrong_unit.loc[0, "unit"] = "mm"
    with pytest.raises(ValueError, match="product_variable_unit_mismatch"):
        build_monthly_features(wrong_unit)

    unmarked = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    unmarked.loc[0, "synthetic_fixture"] = False
    with pytest.raises(ValueError, match="synthetic_fixture_marker_missing"):
        build_monthly_features(unmarked)

    textual_marker = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    textual_marker["synthetic_fixture"] = "False"
    with pytest.raises(ValueError, match="synthetic_fixture_marker_missing"):
        build_monthly_features(textual_marker)

    ineligible = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    ineligible.loc[0, "eligible"] = False
    with pytest.raises(ValueError, match="ineligible_observation_present"):
        build_monthly_features(ineligible)


def test_nasa_source_requires_hash_integrity_and_non_synthetic_provenance():
    frame = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    frame["source_kind"] = "verified_nasa_granule"
    frame["source_sha256"] = "a" * 64
    frame["synthetic_fixture"] = False
    with pytest.raises(ValueError, match="source_hash_verified_missing"):
        build_monthly_features(frame)

    marked_synthetic = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    marked_synthetic["source_kind"] = "verified_nasa_granule"
    marked_synthetic["source_sha256"] = "a" * 64
    for flag in ("hash_verified", "size_verified", "native_payload_verified"):
        marked_synthetic[flag] = True
    with pytest.raises(ValueError, match="source_marked_synthetic"):
        build_monthly_features(marked_synthetic)


def test_monthly_rate_depth_requires_explicit_interpretation_and_uses_calendar_hours():
    periods = pd.period_range("2005-01", periods=2, freq="M")
    rate = pd.Series([1.0, 1.0])
    with pytest.raises(ValueError, match="interpretation_not_confirmed"):
        monthly_rate_to_depth(rate, periods, unit="mm/hr", interpretation_confirmed=False)

    with pytest.raises(ValueError, match="unit_must_be_mm_per_hour"):
        monthly_rate_to_depth(rate, periods, unit="mm", interpretation_confirmed=True)

    depth = monthly_rate_to_depth(rate, periods, unit="mm/hr", interpretation_confirmed=True)
    assert depth.tolist() == [744, 672]
    assert rate.tolist() == [1.0, 1.0]
    assert depth.attrs["input_unit"] == "mm/hr"
    assert depth.attrs["output_unit"] == "mm"


def test_monthly_rate_conversion_preserves_zero_null_and_leap_year_hours():
    periods = pd.period_range("2004-02", periods=3, freq="M")
    rate = pd.Series([1, None, 0])

    depth = monthly_rate_to_depth(rate, periods, unit="mm/hr", interpretation_confirmed=True)

    assert depth.iloc[0] == 696
    assert pd.isna(depth.iloc[1])
    assert depth.iloc[2] == 0
    assert depth.attrs["input_missing_count"] == 1
    assert depth.attrs["missing_periods"] == ["2004-03"]


@pytest.mark.parametrize("bad_value", ["rainy", "NaN", "inf", float("inf"), float("-inf")])
def test_feature_pipeline_rejects_invalid_text_and_infinite_values(bad_value):
    frame = observations(pd.period_range("2005-01", periods=1, freq="M"), [bad_value])

    with pytest.raises(ValueError, match="invalid_numeric_value|non_finite_numeric_value"):
        build_monthly_features(frame)


@pytest.mark.parametrize("bad_value", ["rainy", "NaN", "inf", float("inf"), float("-inf")])
def test_rate_conversion_rejects_invalid_text_and_infinite_values(bad_value):
    with pytest.raises(ValueError, match="invalid_numeric_value|non_finite_numeric_value"):
        monthly_rate_to_depth(
            pd.Series([bad_value]),
            pd.period_range("2005-01", periods=1, freq="M"),
            unit="mm/hr",
            interpretation_confirmed=True,
        )


def test_negative_precipitation_rate_is_rejected():
    with pytest.raises(ValueError, match="negative_precipitation_rate"):
        monthly_rate_to_depth(
            pd.Series([-0.01]),
            pd.period_range("2005-01", periods=1, freq="M"),
            unit="mm/hr",
            interpretation_confirmed=True,
        )

