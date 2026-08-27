import numpy as np
import pandas as pd
import pytest

from msp_spy_excess_model import (
    align_equity_prices,
    excess_forward_return,
    expanding_oos_excess,
    summarize_oos,
)


def sample_prices():
    dates = pd.bdate_range("2026-01-01", periods=60)
    dal = pd.DataFrame({"date": dates, "adj_close": 50 + np.arange(60) * 0.5})
    spy = pd.DataFrame({"date": dates, "adj_close": 500 + np.arange(60) * 1.0})
    return dal, spy


def test_align_equity_prices():
    dal, spy = sample_prices()
    out = align_equity_prices(dal, spy)
    assert list(out.columns) == ["date", "dal_adj", "spy_adj"]
    assert len(out) == 60


def test_excess_forward_return_matches_difference():
    dal, spy = sample_prices()
    aligned = align_equity_prices(dal, spy)
    result = excess_forward_return(aligned, "2026-01-05", 5)
    assert result["excess_return"] == pytest.approx(
        result["dal_return"] - result["spy_return"]
    )


def synthetic_panel(n=60):
    rng = np.random.default_rng(11)
    traffic = rng.normal(size=n)
    wti = rng.normal(scale=0.1, size=n)
    interaction = traffic * wti
    y = rng.normal(scale=0.04, size=n)
    return pd.DataFrame({
        "target_period": [f"m{i}" for i in range(n)],
        "traffic_z": traffic,
        "wti_21d": wti,
        "interaction": interaction,
        "excess_21d": y,
    })


def test_oos_has_four_models():
    out = expanding_oos_excess(synthetic_panel(), ycol="excess_21d")
    assert set(out["model"]) == {
        "historical_mean",
        "traffic_only",
        "traffic_plus_wti",
        "traffic_wti_interaction",
    }


def test_oos_starts_after_minimum_training_window():
    out = expanding_oos_excess(synthetic_panel(), ycol="excess_21d", min_train=36)
    assert (out["target_period"] == "m36").sum() == 4


def test_summary_metrics_are_finite():
    out = expanding_oos_excess(synthetic_panel(), ycol="excess_21d")
    summary = summarize_oos(out)
    assert summary["rmse"].notna().all()
    assert summary["mae"].notna().all()
