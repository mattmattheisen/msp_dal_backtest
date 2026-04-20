# src/metrics.py
"""
Performance metrics for the MSP-DAL backtest.

All metrics computed on monthly equity curve (rebased to 1.0).
Annualization factor: 12 months.
"""

import numpy as np
import pandas as pd
from typing import List
from backtest import BacktestResult, Trade


def monthly_returns(equity: pd.Series) -> pd.Series:
    """Compute period-over-period returns from rebased equity curve."""
    return equity.pct_change().dropna()


def annualize(monthly_r: float, periods: int = 12) -> float:
    return (1 + monthly_r) ** periods - 1


def cagr(equity: pd.Series) -> float:
    """Compound annual growth rate from rebased equity curve."""
    n_months = len(equity) - 1
    if n_months <= 0:
        return 0.0
    total_return = equity.iloc[-1] / equity.iloc[0]
    return round((total_return ** (12 / n_months) - 1) * 100, 2)


def sharpe_ratio(equity: pd.Series, risk_free_monthly: float = 0.0) -> float:
    """
    Annualized Sharpe ratio.
    risk_free_monthly: monthly risk-free rate (default 0 for simplicity)
    """
    rets = monthly_returns(equity)
    excess = rets - risk_free_monthly
    if excess.std() == 0:
        return 0.0
    return round((excess.mean() / excess.std()) * np.sqrt(12), 3)


def sortino_ratio(equity: pd.Series, risk_free_monthly: float = 0.0) -> float:
    """Annualized Sortino ratio (downside deviation only)."""
    rets = monthly_returns(equity)
    excess = rets - risk_free_monthly
    downside = excess[excess < 0]
    if downside.std() == 0:
        return 0.0
    return round((excess.mean() / downside.std()) * np.sqrt(12), 3)


def max_drawdown(drawdown_series: pd.Series) -> float:
    """Maximum drawdown percentage (negative number)."""
    return round(drawdown_series.min(), 2)


def calmar_ratio(equity: pd.Series, drawdown_series: pd.Series) -> float:
    """CAGR / abs(max drawdown)."""
    mdd = abs(max_drawdown(drawdown_series))
    if mdd == 0:
        return 0.0
    return round(cagr(equity) / mdd, 3)


def alpha_vs_bh(equity: pd.Series, bh_equity: pd.Series) -> float:
    """Simple alpha: strategy final equity minus buy-and-hold final equity (in x terms)."""
    return round(equity.iloc[-1] - bh_equity.iloc[-1], 4)


def win_rate(trades: List[Trade]) -> float:
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.net_pnl > 0)
    return round(wins / len(trades) * 100, 1)


def avg_trade_return(trades: List[Trade]) -> float:
    if not trades:
        return 0.0
    return round(sum(t.return_pct for t in trades) / len(trades), 2)


def profit_factor(trades: List[Trade]) -> float:
    """Gross profit / gross loss."""
    gross_profit = sum(t.gross_pnl for t in trades if t.gross_pnl > 0)
    gross_loss   = abs(sum(t.gross_pnl for t in trades if t.gross_pnl < 0))
    if gross_loss == 0:
        return float("inf")
    return round(gross_profit / gross_loss, 3)


def exposure_pct(positions: pd.Series) -> float:
    """Percentage of months the strategy was in the market."""
    return round(positions.mean() * 100, 1)


def compute_all(result: BacktestResult) -> dict:
    """Return a dict of all key metrics for the backtest result."""
    eq  = result.equity_curve
    bh  = result.bh_equity_curve
    dd  = result.drawdown_pct
    tr  = result.trades
    pos = result.positions

    return {
        "CAGR (strategy) %"     : cagr(eq),
        "CAGR (B&H DAL) %"      : cagr(bh),
        "Sharpe ratio"           : sharpe_ratio(eq),
        "Sortino ratio"          : sortino_ratio(eq),
        "Calmar ratio"           : calmar_ratio(eq, dd),
        "Max drawdown %"         : max_drawdown(dd),
        "Alpha vs B&H (x)"       : alpha_vs_bh(eq, bh),
        "Win rate %"             : win_rate(tr),
        "Avg trade return %"     : avg_trade_return(tr),
        "Profit factor"          : profit_factor(tr),
        "Total trades"           : len(tr),
        "Exposure %"             : exposure_pct(pos),
        "Final equity (x)"       : round(eq.iloc[-1], 4),
        "Final B&H equity (x)"   : round(bh.iloc[-1], 4),
    }


def print_metrics(metrics: dict) -> None:
    print("\n" + "─" * 44)
    print("  MSP PASSENGER SIGNAL — DAL BACKTEST RESULTS")
    print("─" * 44)
    for k, v in metrics.items():
        print(f"  {k:<28} {v:>10}")
    print("─" * 44)


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))

    from src.data_loader import load_aligned_data
    from src.signal import compute_signal
    from src.backtest import run_backtest

    df = load_aligned_data()
    df_sig = compute_signal(df)
    result = run_backtest(df_sig)
    m = compute_all(result)
    print_metrics(m)
