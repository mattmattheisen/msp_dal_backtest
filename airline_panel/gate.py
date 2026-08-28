from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import yfinance as yf

TICKERS = ["DAL", "UAL", "AAL", "LUV", "ALK", "JBLU"]


@dataclass(frozen=True)
class GateConfig:
    publication_lag_months: int = 3
    horizons: tuple[int, ...] = (1, 3, 6)
    min_names_per_month: int = 6


def load_panel(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["period"] = pd.PeriodIndex(df["period"], freq="M")
    return df


def download_monthly_prices(start: str = "2019-01-01", end: str = "2027-03-01") -> pd.DataFrame:
    """Adjusted month-end closes from Yahoo Finance for reproducibility."""
    raw = yf.download(
        TICKERS,
        start=start,
        end=end,
        interval="1mo",
        auto_adjust=True,
        actions=False,
        group_by="column",
        progress=False,
        threads=True,
    )
    close = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
    if isinstance(close, pd.Series):
        close = close.to_frame(TICKERS[0])
    close.index = pd.to_datetime(close.index)
    close["period"] = close.index.to_period("M")
    long = close.set_index("period").stack(future_stack=True).rename("close").reset_index()
    long.columns = ["period", "ticker", "close"]
    return long.dropna(subset=["close"])


def add_forward_returns(prices: pd.DataFrame, horizons=(1, 3, 6)) -> pd.DataFrame:
    prices = prices.sort_values(["ticker", "period"]).copy()
    for h in horizons:
        prices[f"ret_{h}m"] = prices.groupby("ticker")["close"].shift(-h) / prices["close"] - 1.0
    return prices


def form_signals(panel: pd.DataFrame, cfg: GateConfig) -> pd.DataFrame:
    """Lag the operating-month observation before it is allowed to form a signal.

    Because the AFF T-100 summary export does not itself carry historical release
    timestamps, the preliminary gate uses a conservative fixed publication lag.
    This is intentionally distinct from a strict vintage/release-calendar test.
    """
    sig = panel.dropna(subset=["demand_capacity_gap"]).copy()
    sig["signal_period"] = sig["period"] + cfg.publication_lag_months
    counts = sig.groupby("signal_period")["ticker"].transform("nunique")
    sig = sig[counts >= cfg.min_names_per_month].copy()

    # Ranks are ascending: 1=lowest demand-capacity gap, 6=highest.
    sig["rank"] = sig.groupby("signal_period")["demand_capacity_gap"].rank(
        method="first", ascending=True
    )
    sig["bucket"] = np.select(
        [sig["rank"] <= 2, sig["rank"] <= 4],
        ["Low", "Middle"],
        default="High",
    )
    return sig


def join_returns(signals: pd.DataFrame, prices: pd.DataFrame, cfg: GateConfig) -> pd.DataFrame:
    p = add_forward_returns(prices, cfg.horizons)
    joined = signals.merge(
        p,
        left_on=["signal_period", "ticker"],
        right_on=["period", "ticker"],
        how="inner",
        suffixes=("_operating", "_price"),
    )
    for h in cfg.horizons:
        r = f"ret_{h}m"
        joined[f"basket_{h}m"] = joined.groupby("signal_period")[r].transform("mean")
        joined[f"excess_{h}m"] = joined[r] - joined[f"basket_{h}m"]
    return joined


def _mean_t(series: pd.Series) -> tuple[float, float, int]:
    x = series.dropna().astype(float)
    if len(x) < 2:
        return np.nan, np.nan, len(x)
    se = x.std(ddof=1) / np.sqrt(len(x))
    return x.mean(), (x.mean() / se if se > 0 else np.nan), len(x)


def summarize_gate(joined: pd.DataFrame, cfg: GateConfig) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    ic_rows = []
    for h in cfg.horizons:
        col = f"excess_{h}m"
        for bucket in ["Low", "Middle", "High"]:
            mean, tstat, n = _mean_t(joined.loc[joined["bucket"] == bucket, col])
            rows.append({"horizon_months": h, "metric": bucket, "mean_excess": mean, "t_stat": tstat, "n": n})

        high = joined[joined["bucket"] == "High"].groupby("signal_period")[col].mean()
        low = joined[joined["bucket"] == "Low"].groupby("signal_period")[col].mean()
        spread = high.align(low, join="inner")
        hl = spread[0] - spread[1]
        mean, tstat, n = _mean_t(hl)
        rows.append({"horizon_months": h, "metric": "High-Low", "mean_excess": mean, "t_stat": tstat, "n": n})

        for period, g in joined.dropna(subset=[col]).groupby("signal_period"):
            if g["ticker"].nunique() >= cfg.min_names_per_month:
                rho, _ = stats.spearmanr(g["demand_capacity_gap"], g[col])
                ic_rows.append({"horizon_months": h, "signal_period": str(period), "spearman_ic": rho})

    summary = pd.DataFrame(rows)
    ic = pd.DataFrame(ic_rows)
    if not ic.empty:
        ic_summary = (
            ic.groupby("horizon_months")["spearman_ic"]
            .agg(["mean", "std", "count"])
            .reset_index()
        )
        ic_summary["t_stat"] = ic_summary["mean"] / (ic_summary["std"] / np.sqrt(ic_summary["count"]))
    else:
        ic_summary = pd.DataFrame(columns=["horizon_months", "mean", "std", "count", "t_stat"])
    return summary, ic_summary


def run_gate(
    panel_path: str | Path = "data/airline_t100_panel.csv",
    output_dir: str | Path = "data/airline_gate",
    cfg: GateConfig = GateConfig(),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    panel = load_panel(panel_path)
    prices = download_monthly_prices()
    signals = form_signals(panel, cfg)
    joined = join_returns(signals, prices, cfg)
    summary, ic_summary = summarize_gate(joined, cfg)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    joined.assign(
        period_operating=joined["period_operating"].astype(str),
        signal_period=joined["signal_period"].astype(str),
        period_price=joined["period_price"].astype(str),
    ).to_csv(output_dir / "observations.csv", index=False)
    summary.to_csv(output_dir / "bucket_summary.csv", index=False)
    ic_summary.to_csv(output_dir / "rank_ic_summary.csv", index=False)
    return summary, ic_summary


if __name__ == "__main__":
    summary, ic = run_gate()
    print("\nBucket gate (excess returns vs equal-weight six-airline basket):")
    print(summary.to_string(index=False))
    print("\nCross-sectional Spearman rank IC:")
    print(ic.to_string(index=False))
