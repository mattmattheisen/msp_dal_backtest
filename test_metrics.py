# tests/test_metrics.py
"""Unit tests for performance metrics."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from backtest import Trade


def flat_equity(n=24, value=1.0):
    return pd.Series([value] * n)

def growing_equity(n=24, monthly_rate=0.01):
    return pd.Series([(1 + monthly_rate) ** i for i in range(n)])

def declining_equity(n=24, monthly_rate=-0.01):
    return pd.Series([(1 + monthly_rate) ** i for i in range(n)])

def zero_drawdown(n=24):
    return pd.Series([0.0] * n)

def make_trades(returns):
    """Build a list of Trade objects from a list of return percentages."""
    trades = []
    for i, r in enumerate(returns):
        entry = 50.0
        exit_p = entry * (1 + r / 100)
        trades.append(Trade(
            entry_month=f"2020-{i+1:02d}",
            exit_month=f"2020-{i+2:02d}",
            entry_price=entry,
            exit_price=exit_p,
            shares=100,
            gross_pnl=entry * 100 * r / 100,
            net_pnl=entry * 100 * r / 100 - 5.0,
            return_pct=r,
            commission=5.0,
        ))
    return trades


def test_cagr_flat():
    from metrics import cagr
    assert cagr(flat_equity()) == pytest.approx(0.0, abs=0.1)


def test_cagr_growing():
    from metrics import cagr
    # 1% monthly ~= 12.68% annual
    assert cagr(growing_equity(24, 0.01)) == pytest.approx(12.68, abs=0.5)


def test_sharpe_flat_zero():
    from metrics import sharpe_ratio
    eq = flat_equity()
    assert sharpe_ratio(eq) == pytest.approx(0.0, abs=0.01)


def test_sharpe_positive_for_growing():
    from metrics import sharpe_ratio
    assert sharpe_ratio(growing_equity()) > 0


def test_sortino_positive_for_growing():
    from metrics import sortino_ratio
    assert sortino_ratio(growing_equity()) > 0


def test_max_drawdown_zero():
    from metrics import max_drawdown
    assert max_drawdown(zero_drawdown()) == 0.0


def test_max_drawdown_negative():
    from metrics import max_drawdown
    dd = pd.Series([0.0, -5.0, -10.0, -3.0, 0.0])
    assert max_drawdown(dd) == pytest.approx(-10.0)


def test_win_rate_all_wins():
    from metrics import win_rate
    trades = make_trades([5.0, 3.0, 10.0])
    assert win_rate(trades) == pytest.approx(100.0)


def test_win_rate_all_losses():
    from metrics import win_rate
    trades = make_trades([-5.0, -3.0])
    assert win_rate(trades) == pytest.approx(0.0)


def test_profit_factor_all_wins():
    from metrics import profit_factor
    trades = make_trades([5.0, 3.0])
    assert profit_factor(trades) == float("inf")


def test_profit_factor_mixed():
    from metrics import profit_factor
    trades = make_trades([10.0, -5.0])
    pf = profit_factor(trades)
    assert pf > 1.0


def test_exposure_full():
    from metrics import exposure_pct
    pos = pd.Series([1] * 20)
    assert exposure_pct(pos) == pytest.approx(100.0)


def test_exposure_half():
    from metrics import exposure_pct
    pos = pd.Series([1, 0] * 10)
    assert exposure_pct(pos) == pytest.approx(50.0)
