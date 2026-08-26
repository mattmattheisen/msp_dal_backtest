import pandas as pd
import pytest

from msp_availability import load_msp_actuals
from msp_nowcast import (
    ar1_yoy,
    forecast_benchmarks,
    score_forecast,
    seasonal_naive,
    yoy_trend,
)


@pytest.fixture
def df():
    return load_msp_actuals()


def test_seasonal_naive_uses_prior_year_not_unreleased_target(df):
    result = seasonal_naive(df, "2026-05-01", "2026-03")

    assert result.latest_known_period == "2026-01"
    assert result.prior_year_period == "2025-03"
    assert result.prior_year_enplanements == 1_639_810
    assert result.forecast_enplanements == 1_639_810


def test_yoy_trend_uses_only_recent_known_growth(df):
    result = yoy_trend(df, "2026-05-01", "2026-03", window=3)

    expected_mean = ((-0.045552) + (-0.088568) + (-0.023402)) / 3

    assert result.latest_known_period == "2026-01"
    assert result.yoy_window_used == 3
    assert result.recent_yoy_mean == pytest.approx(expected_mean, abs=1e-6)
    assert result.forecast_enplanements == pytest.approx(
        1_639_810 * (1 + expected_mean), rel=1e-6
    )


def test_ar1_is_point_in_time_and_handles_multi_month_gap(df):
    result = ar1_yoy(df, "2026-05-01", "2026-03")

    assert result.latest_known_period == "2026-01"
    assert result.forecast_horizon_months == 2
    assert result.ar_pairs_used >= 4
    assert pd.notna(result.ar_alpha)
    assert pd.notna(result.ar_phi)
    assert result.forecast_enplanements > 0


def test_ar1_parameters_are_finite(df):
    result = ar1_yoy(df, "2026-08-24", "2026-07")

    assert pd.notna(result.ar_alpha)
    assert pd.notna(result.ar_phi)
    assert pd.notna(result.forecast_yoy_growth)


def test_release_day_changes_information_set(df):
    before = yoy_trend(df, "2026-05-14", "2026-04", window=3)
    after = yoy_trend(df, "2026-05-15", "2026-04", window=3)

    assert before.latest_known_period == "2026-01"
    assert after.latest_known_period == "2026-03"
    assert before.forecast_enplanements != after.forecast_enplanements


def test_cannot_nowcast_observation_already_released(df):
    with pytest.raises(ValueError, match="already released"):
        seasonal_naive(df, "2026-05-15", "2026-03")

    with pytest.raises(ValueError, match="already released"):
        ar1_yoy(df, "2026-05-15", "2026-03")


def test_prior_year_base_must_be_point_in_time_available(df):
    with pytest.raises(ValueError, match="prior-year observation"):
        seasonal_naive(df, "2025-06-01", "2025-05")


def test_benchmark_table_has_three_methods(df):
    output = forecast_benchmarks(df, "2026-05-01", "2026-03")

    assert set(output["method"]) == {"seasonal_naive", "yoy_trend", "ar1_yoy"}
    assert len(output) == 3


def test_score_forecast():
    score = score_forecast(1_600_000, 1_500_000)

    assert score["error"] == 100_000
    assert score["absolute_error"] == 100_000
    assert score["absolute_percentage_error"] == pytest.approx(1 / 15)
