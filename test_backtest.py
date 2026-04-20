# tests/test_backtest.py
"""Unit tests for the backtest engine."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def make_signal_df(positions, prices):
    """Build a minimal signal DataFrame for testing."""
    n = len(positions)
    dates = pd.date_range("2018-01", periods=n, freq="MS")
    return pd.DataFrame({
        "year_month":    dates,
        "passengers_adj": np.ones(n) * 3_000_000,
        "close":         prices,
        "momentum":      np.zeros(n),
        "signal_raw":    np.zeros(n),
        "position":      positions,
    })


def test_always_long_matches_bh():
    """If always in position, equity curve should match buy-and-hold (net of commission)."""
    from backtest import run_backtest
    prices = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0]
    df = make_signal_df([1] * len(prices), prices)
    result = run_backtest(df, initial_capital=100_000, commission_pct=0.0)
    # With 0 commission and always-long, strategy ~= B&H
    assert abs(result.equity_curve.iloc[-1] - result.bh_equity_curve.iloc[-1]) < 0.01


def test_always_cash_flat_equity():
    """If always in cash, equity curve stays at 1.0."""
    from backtest import run_backtest
    prices = [40.0, 45.0, 50.0, 55.0, 60.0]
    df = make_signal_df([0] * len(prices), prices)
    result = run_backtest(df, initial_capital=100_000, commission_pct=0.0)
    assert all(abs(v - 1.0) < 1e-6 for v in result.equity_curve.tolist())


def test_drawdown_nonpositive():
    """Drawdown should always be <= 0."""
    from backtest import run_backtest
    prices = [50.0, 55.0, 45.0, 48.0, 52.0, 60.0]
    df = make_signal_df([1, 1, 0, 1, 1, 0], prices)
    result = run_backtest(df)
    assert (result.drawdown_pct <= 0.001).all()


def test_trade_log_populated_on_exit():
    """Strategy that enters and exits should generate at least one trade."""
    from backtest import run_backtest
    prices = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0]
    df = make_signal_df([1, 1, 1, 0, 0, 0], prices)
    result = run_backtest(df, commission_pct=0.0)
    assert len(result.trades) >= 1


def test_trade_return_sign():
    """Winning trade should have positive return_pct."""
    from backtest import run_backtest
    prices = [40.0, 42.0, 44.0, 46.0, 48.0, 50.0]
    df = make_signal_df([1, 1, 1, 0, 0, 0], prices)
    result = run_backtest(df, commission_pct=0.0)
    for trade in result.trades:
        assert trade.return_pct == pytest.approx(
            (trade.exit_price - trade.entry_price) / trade.entry_price * 100, abs=0.5
        )


def test_equity_curve_length_consistency():
    """Equity, B&H, and drawdown series should be same length."""
    from backtest import run_backtest
    prices = [40.0, 42.0, 44.0, 40.0, 38.0, 45.0, 50.0]
    df = make_signal_df([1, 0, 1, 1, 0, 1, 0], prices)
    result = run_backtest(df)
    n = len(result.equity_curve)
    assert len(result.bh_equity_curve) == n
    assert len(result.drawdown_pct) == n
