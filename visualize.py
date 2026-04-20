# src/visualize.py
"""
Chart generation for the MSP-DAL backtest.

Four charts:
  1. Normalized overlay: MSP pax vs DAL price
  2. Lag correlation bar chart
  3. Equity curve: strategy vs buy-and-hold
  4. Drawdown chart

Saves PNG to reports/ if config.SAVE_CHARTS = True.
"""

import os
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config

REPORT_DIR = Path(__file__).parent.parent / config.REPORT_DIR
REPORT_DIR.mkdir(exist_ok=True)

# Colors — clean, professional
C_MSP    = "#3266ad"   # blue
C_DAL    = "#d85a30"   # coral/orange
C_STRAT  = "#3b6d11"   # green
C_BH     = "#888780"   # gray
C_DD     = "#a32d2d"   # red
C_ACCENT = "#d85a30"   # highlighted bar


def _normalize(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    return (series - mn) / (mx - mn) if mx > mn else series * 0


def plot_all(df_aligned: pd.DataFrame,
             df_signal: pd.DataFrame,
             result,
             lag_table: pd.DataFrame,
             metrics: dict,
             active_lag: int = None) -> plt.Figure:
    """
    Render the full 4-panel backtest dashboard.

    Parameters
    ----------
    df_aligned  : raw aligned data (for overlay chart)
    df_signal   : signal-enriched data
    result      : BacktestResult object
    lag_table   : output of signal.lag_correlation_table()
    metrics     : output of metrics.compute_all()
    active_lag  : currently selected lag (highlighted in lag chart)
    """
    active_lag = active_lag if active_lag is not None else config.LAG_MONTHS

    fig = plt.figure(figsize=(14, 11))
    fig.patch.set_facecolor("white")

    gs = gridspec.GridSpec(4, 2, figure=fig,
                           left=0.07, right=0.97,
                           top=0.92, bottom=0.06,
                           hspace=0.55, wspace=0.35)

    ax_overlay = fig.add_subplot(gs[0, :])
    ax_lag     = fig.add_subplot(gs[1, 0])
    ax_equity  = fig.add_subplot(gs[1, 1])
    ax_dd      = fig.add_subplot(gs[2, :])
    ax_metrics = fig.add_subplot(gs[3, :])

    # ── 1. Normalized overlay ─────────────────────────────────────────────────
    labels_dt = df_aligned["year_month"]
    pax_n = _normalize(df_aligned["passengers_adj"])
    dal_n = _normalize(df_aligned["close"])

    ax_overlay.plot(labels_dt, pax_n, color=C_MSP, lw=1.5, label="MSP passengers (norm.)")
    ax_overlay.plot(labels_dt, dal_n, color=C_DAL, lw=1.5, linestyle="--", label="DAL price (norm.)")
    ax_overlay.set_title("MSP passenger traffic vs DAL price — normalized overlay", fontsize=10, pad=6)
    ax_overlay.legend(fontsize=8, framealpha=0)
    ax_overlay.set_ylabel("Normalized (0–1)", fontsize=8)
    ax_overlay.tick_params(labelsize=8)
    ax_overlay.grid(axis="y", alpha=0.2)
    ax_overlay.spines[["top","right"]].set_visible(False)

    # ── 2. Lag correlation ────────────────────────────────────────────────────
    lags = lag_table["lag"].values
    rs   = lag_table["r"].values
    colors = [C_ACCENT if l == active_lag else C_MSP for l in lags]

    ax_lag.bar(lags, rs, color=colors, width=0.6, zorder=2)
    ax_lag.axhline(0, color="black", lw=0.5, zorder=1)
    ax_lag.set_title("Lag correlation (pax leads/lags DAL)", fontsize=9, pad=5)
    ax_lag.set_xlabel("Lag (months, + = pax leads)", fontsize=8)
    ax_lag.set_ylabel("Pearson r", fontsize=8)
    ax_lag.set_ylim(-1, 1)
    ax_lag.tick_params(labelsize=8)
    ax_lag.grid(axis="y", alpha=0.2)
    ax_lag.spines[["top","right"]].set_visible(False)

    # Annotate active lag
    idx = list(lags).index(active_lag) if active_lag in lags else None
    if idx is not None:
        r_val = rs[idx]
        ax_lag.annotate(f"r={r_val:.2f}", xy=(active_lag, r_val),
                        xytext=(active_lag + 0.3, r_val + (0.07 if r_val >= 0 else -0.07)),
                        fontsize=7, color=C_ACCENT)

    # ── 3. Equity curve ───────────────────────────────────────────────────────
    eq_labels = result.labels
    ax_equity.plot(eq_labels, result.equity_curve,    color=C_STRAT, lw=1.8, label="Signal strategy")
    ax_equity.plot(eq_labels, result.bh_equity_curve, color=C_BH,    lw=1.5, linestyle="--", label="Buy & hold DAL")
    ax_equity.set_title("Equity curve (rebased to 1.0)", fontsize=9, pad=5)
    ax_equity.set_ylabel("Equity (×)", fontsize=8)
    ax_equity.tick_params(labelsize=8)
    ax_equity.legend(fontsize=7, framealpha=0)
    ax_equity.grid(axis="y", alpha=0.2)
    ax_equity.spines[["top","right"]].set_visible(False)

    # ── 4. Drawdown ───────────────────────────────────────────────────────────
    ax_dd.fill_between(eq_labels, result.drawdown_pct, 0,
                       color=C_DD, alpha=0.25, label="Drawdown")
    ax_dd.plot(eq_labels, result.drawdown_pct, color=C_DD, lw=1.0)
    ax_dd.set_title("Drawdown from peak (%)", fontsize=10, pad=6)
    ax_dd.set_ylabel("Drawdown (%)", fontsize=8)
    ax_dd.tick_params(labelsize=8)
    ax_dd.grid(axis="y", alpha=0.2)
    ax_dd.spines[["top","right"]].set_visible(False)

    # ── 5. Metrics table ──────────────────────────────────────────────────────
    ax_metrics.axis("off")
    col_labels = list(metrics.keys())
    col_vals   = [str(v) for v in metrics.values()]
    mid = len(col_labels) // 2

    def _row(keys, vals, ax, y):
        x_step = 1.0 / len(keys)
        for j, (k, v) in enumerate(zip(keys, vals)):
            x = j * x_step + x_step * 0.1
            ax.text(x, y + 0.12, k, fontsize=7, color="#666", transform=ax.transAxes)
            ax.text(x, y,        v, fontsize=9, fontweight="bold",
                    color="#111", transform=ax.transAxes)

    _row(col_labels[:mid],  col_vals[:mid],  ax_metrics, 0.55)
    _row(col_labels[mid:],  col_vals[mid:],  ax_metrics, 0.10)

    # Title
    covid_note = " | COVID 2020–2021 excluded" if config.EXCLUDE_COVID else ""
    seas_note  = " | seasonal adj." if config.SEASONAL_ADJUST else ""
    fig.suptitle(
        f"MSP Airport Passenger Signal — Delta Air Lines Backtest\n"
        f"Lag: +{active_lag}mo | Lookback: {config.LOOKBACK_MONTHS}mo | "
        f"Threshold: {config.SIGNAL_THRESHOLD*100:.0f}% MoM{covid_note}{seas_note}",
        fontsize=11, y=0.975
    )

    if config.SAVE_CHARTS:
        out_path = REPORT_DIR / "backtest_summary.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        if config.VERBOSE:
            print(f"Chart saved: {out_path}")

    return fig


if __name__ == "__main__":
    from data_loader import load_aligned_data
    from signal import compute_signal, lag_correlation_table
    from backtest import run_backtest
    from metrics import compute_all

    df = load_aligned_data()
    df_sig = compute_signal(df)
    result = run_backtest(df_sig)
    lt = lag_correlation_table(df)
    m  = compute_all(result)

    fig = plot_all(df, df_sig, result, lt, m, active_lag=config.LAG_MONTHS)
    plt.show()
