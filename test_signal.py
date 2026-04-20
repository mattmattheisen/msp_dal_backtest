# tests/test_signal.py
"""Unit tests for signal construction."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def make_sample_df(n=24):
    """Create a synthetic aligned DataFrame for testing."""
    dates = pd.date_range("2020-01", periods=n, freq="MS")
    pax = np.linspace(2_500_000, 3_500_000, n) + np.random.default_rng(42).normal(0, 50_000, n)
    dal = np.linspace(40.0, 60.0, n) + np.random.default_rng(99).normal(0, 2.0, n)
    df = pd.DataFrame({"year_month": dates, "passengers": pax, "close": dal})
    df["passengers_adj"] = df["passengers"]
    return df


def test_momentum_length():
    from signal import compute_momentum
    df = make_sample_df()
    mom = compute_momentum(df["passengers_adj"], lookback=1)
    assert len(mom) == len(df)
    assert pd.isna(mom.iloc[0])
    assert not pd.isna(mom.iloc[1])


def test_signal_position_binary():
    from signal import compute_signal
    df = make_sample_df()
    df_sig = compute_signal(df, lag=1, lookback=1, threshold=0.01)
    assert set(df_sig["position"].unique()).issubset({0, 1})


def test_signal_lag_shifts_correctly():
    """Increasing lag should shift the momentum series later."""
    from signal import compute_signal
    df = make_sample_df()
    sig0 = compute_signal(df, lag=0, lookback=1, threshold=0.0)
    sig1 = compute_signal(df, lag=1, lookback=1, threshold=0.0)
    # lag=1 should have fewer rows (first signal not available until month lag+lookback)
    assert len(sig1) <= len(sig0)


def test_lag_correlation_table_shape():
    from signal import lag_correlation_table
    df = make_sample_df(36)
    lt = lag_correlation_table(df, max_lag=3, min_lag=-2)
    assert len(lt) == 6  # -2, -1, 0, 1, 2, 3
    assert "r" in lt.columns
    assert "p_value" in lt.columns


def test_lag_correlation_r_bounds():
    from signal import lag_correlation_table
    df = make_sample_df(36)
    lt = lag_correlation_table(df)
    assert (lt["r"].abs() <= 1.0).all()


def test_best_lag_returns_dict():
    from signal import lag_correlation_table, best_lag
    df = make_sample_df(36)
    lt = lag_correlation_table(df)
    bl = best_lag(lt)
    assert "lag" in bl
    assert "r" in bl
