import pandas as pd
import pytest

from msp_availability import load_msp_actuals
from msp_walk_forward import (
    evaluation_as_of,
    eligible_targets,
    model_hurdle,
    summarize_walk_forward,
    walk_forward_evaluate,
)


@pytest.fixture
def df():
    return load_msp_actuals()


def test_cutoff_is_day_before_release():
    assert evaluation_as_of("2026-05-15") == pd.Timestamp("2026-05-14")


def test_eligible_targets_are_2026_only_with_current_release_history(df):
    targets = eligible_targets(df)
    assert targets["period"].astype(str).tolist() == [
        "2026-01",
        "2026-02",
        "2026-03",
        "2026-04",
        "2026-05",
        "2026-06",
        "2026-07",
    ]


def test_every_forecast_is_strictly_pre_release(df):
    results = walk_forward_evaluate(df)
    assert (results["as_of_date"] < results["release_date"]).all()


def test_target_is_not_in_latest_known_period(df):
    results = walk_forward_evaluate(df)
    target = pd.PeriodIndex(results["target_period"], freq="M")
    latest = pd.PeriodIndex(results["latest_known_period"], freq="M")
    assert (latest < target).all()


def test_three_methods_per_target(df):
    results = walk_forward_evaluate(df)
    counts = results.groupby("target_period")["method"].nunique()
    assert (counts == 3).all()
    assert len(results) == 21


def test_summary_contains_standard_forecast_metrics(df):
    results = walk_forward_evaluate(df)
    summary = summarize_walk_forward(results)
    assert set(summary["method"]) == {"seasonal_naive", "yoy_trend", "ar1_yoy"}
    assert {"n", "mae", "mape", "rmse", "bias"}.issubset(summary.columns)
    assert (summary["n"] == 7).all()


def test_hurdle_is_best_summary_row(df):
    results = walk_forward_evaluate(df)
    summary = summarize_walk_forward(results)
    hurdle = model_hurdle(results)
    assert hurdle["method"] == summary.iloc[0]["method"]
    assert hurdle["mape"] == pytest.approx(summary.iloc[0]["mape"])


def test_march_example_is_scored_from_may_14_information_set(df):
    results = walk_forward_evaluate(df)
    march = results[results["target_period"] == "2026-03"]
    assert not march.empty
    assert (march["as_of_date"] == pd.Timestamp("2026-05-14")).all()
    assert (march["latest_known_period"] == "2026-01").all()


def test_ar1_metadata_is_recorded(df):
    results = walk_forward_evaluate(df)
    ar = results[results["method"] == "ar1_yoy"]
    assert ar["ar_phi"].notna().all()
    assert ar["forecast_horizon_months"].notna().all()
