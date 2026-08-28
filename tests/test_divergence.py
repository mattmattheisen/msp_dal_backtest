import numpy as np
import pandas as pd

from divergence import DivergenceConfig, build_divergence_frame, summarize_forward_returns, trailing_zscore


def synthetic_frame(n=72):
    dates = pd.date_range("2018-01-01", periods=n, freq="MS")
    passengers = 2_000_000 * (1.002 ** np.arange(n))
    close = 40 * (1.004 ** np.arange(n))
    return pd.DataFrame({"year_month": dates, "passengers": passengers, "close": close})


def test_trailing_zscore_has_warmup():
    s = pd.Series(np.arange(10, dtype=float))
    z = trailing_zscore(s, window=5, min_periods=3)
    assert z.iloc[:2].isna().all()
    assert z.iloc[2:].notna().all()


def test_msp_publication_lag_is_applied():
    df = synthetic_frame()
    cfg = DivergenceConfig(msp_yoy_months=12, msp_release_lag=1, z_min_periods=6, z_window=12)
    out = build_divergence_frame(df, cfg)
    expected = out["msp_yoy"].shift(1)
    pd.testing.assert_series_equal(out["msp_signal_pit"], expected, check_names=False)


def test_forward_return_alignment():
    df = synthetic_frame()
    cfg = DivergenceConfig(z_min_periods=6, z_window=12)
    out = build_divergence_frame(df, cfg)
    i = 30
    expected = df.loc[i + 3, "close"] / df.loc[i, "close"] - 1.0
    assert np.isclose(out.loc[i, "dal_fwd_3m"], expected)


def test_positive_divergence_labels_strong_msp_weak_dal():
    df = synthetic_frame()
    # Create a late traffic surge and DAL drawdown to force positive divergence.
    df.loc[55:, "passengers"] *= 1.25
    df.loc[60:, "close"] *= 0.70
    cfg = DivergenceConfig(z_min_periods=12, z_window=24, extreme_z=1.0)
    out = build_divergence_frame(df, cfg)
    assert (out["divergence_state"] == "strong_msp_weak_dal").any()


def test_summary_contains_expected_statistics():
    df = synthetic_frame()
    df.loc[55:, "passengers"] *= 1.20
    df.loc[60:, "close"] *= 0.75
    cfg = DivergenceConfig(z_min_periods=12, z_window=24, extreme_z=1.0)
    out = build_divergence_frame(df, cfg)
    summary = summarize_forward_returns(out, cfg.forward_horizons)
    assert {"state", "horizon_months", "n", "mean_return", "median_return", "win_rate", "std_return"}.issubset(summary.columns)
    assert (summary["n"] > 0).all()
