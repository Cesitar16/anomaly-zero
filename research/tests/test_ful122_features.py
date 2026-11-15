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


def test_missing_month_is_inserted_and_breaks_lags_and_windows():
    periods = pd.PeriodIndex(["2005-01", "2005-02", "2005-04", "2005-05"], freq="M")
    result = build_monthly_features(observations(periods, [1, 2, 4, 5]))
    frame = result.frame.set_index("period")

    assert result.metadata["missing_periods"] == ["2005-03"]
    assert np.isnan(frame.loc["2005-04", "lag_1"])
    assert np.isnan(frame.loc["2005-04", "rolling_mean_3"])
    assert not bool(frame.loc["2005-03", "row_present"])
    assert not bool(frame.loc["2005-03", "eligible"])


def test_duplicate_months_or_mixed_spatial_support_are_rejected():
    duplicate = observations(pd.PeriodIndex(["2005-01", "2005-01"], freq="M"), [1, 2])
    with pytest.raises(ValueError, match="duplicate_months"):
        build_monthly_features(duplicate)

    mixed = observations(pd.period_range("2005-01", periods=2, freq="M"), [1, 2])
    mixed.loc[1, "support_id"] = "different-cell"
    with pytest.raises(ValueError, match="mixed_series_identity"):
        build_monthly_features(mixed)


def test_units_and_synthetic_markers_are_mandatory():
    wrong_unit = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    wrong_unit.loc[0, "unit"] = "mm"
    with pytest.raises(ValueError, match="product_variable_unit_mismatch"):
        build_monthly_features(wrong_unit)

    unmarked = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    unmarked.loc[0, "synthetic_fixture"] = False
    with pytest.raises(ValueError, match="synthetic_fixture_marker_missing"):
        build_monthly_features(unmarked)

    ineligible = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    ineligible.loc[0, "eligible"] = False
    with pytest.raises(ValueError, match="ineligible_observation_present"):
        build_monthly_features(ineligible)


def test_nasa_source_requires_valid_hash_and_inventory_verification_flags():
    frame = observations(pd.period_range("2005-01", periods=1, freq="M"), [1])
    frame["source_kind"] = "verified_nasa_granule"
    frame["source_sha256"] = "a" * 64
    frame["synthetic_fixture"] = False
    with pytest.raises(ValueError, match="source_hash_verified_missing"):
        build_monthly_features(frame)

    for flag in ("hash_verified", "size_verified", "native_payload_verified"):
        frame[flag] = True
    result = build_monthly_features(frame)
    assert result.metadata["synthetic_notice"] is None


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

