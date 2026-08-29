from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time

import numpy as np
import pandas as pd
from scipy import stats
import yfinance as yf

# Screening universe only. This is intentionally a current, liquid large-cap universe
# rather than a point-in-time membership history. Survivorship bias is accepted for
# Gate 01 because a negative result should kill the idea cheaply. If the gate survives,
# point-in-time constituent history becomes mandatory before any promotion.
SP100 = [
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AMAT", "AMD", "AMGN", "AMT", "AMZN",
    "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK-B", "C",
    "CAT", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS", "CVX",
    "DE", "DHR", "DIS", "DUK", "EMR", "FDX", "GD", "GE", "GEV", "GILD",
    "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC", "INTU", "ISRG",
    "JNJ", "JPM", "KO", "LIN", "LLY", "LMT", "LOW", "LRCX", "MA", "MCD",
    "MDLZ", "MDT", "META", "MMM", "MO", "MRK", "MS", "MSFT", "MU", "NEE",
    "NFLX", "NKE", "NOW", "NVDA", "ORCL", "PEP", "PFE", "PG", "PLTR", "PM",
    "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TMO", "TMUS", "TSLA",
    "TXN", "UBER", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC", "WMT", "XOM",
]

BENCHMARK = "SPY"
START = "2014-01-01"  # one year of warm-up before the 2015 research sample
RESEARCH_START = pd.Timestamp("2015-01-01")
HORIZONS = (1, 3, 5, 10, 20)
PRIMARY_HORIZON = 10
OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass(frozen=True)
class GateConfig:
    winner_lookback_days: int = 252
    winner_quantile: float = 0.95
    winner_min_periods: int = 126
    return_window_days: int = 5
    volume_window_days: int = 5
    volume_baseline_days: int = 60
    volume_quantile_lookback_days: int = 252
    volume_quantile: float = 0.95
    volume_min_periods: int = 126


CFG = GateConfig()


def _chunks(items: list[str], n: int = 20):
    for i in range(0, len(items), n):
        yield items[i : i + n]


def download_ohlcv(tickers: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Download adjusted close and consolidated daily volume from Yahoo Finance.

    Gate 01 is a free feasibility screen, not production data infrastructure. Failed
    symbols are retained in a diagnostics table and omitted from the event study.
    """
    all_tickers = sorted(set(tickers + [BENCHMARK]))
    close_parts: list[pd.Series] = []
    volume_parts: list[pd.Series] = []

    for batch in _chunks(all_tickers, 20):
        data = None
        for attempt in range(3):
            try:
                data = yf.download(
                    batch,
                    start=START,
                    end=None,
                    auto_adjust=True,
                    actions=False,
                    group_by="ticker",
                    progress=False,
                    threads=True,
                    timeout=30,
                )
                if data is not None and not data.empty:
                    break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))

        if data is None or data.empty:
            continue

        if isinstance(data.columns, pd.MultiIndex):
            for ticker in batch:
                if ticker not in data.columns.get_level_values(0):
                    continue
                sub = data[ticker]
                if "Close" in sub and sub["Close"].notna().sum() > 0:
                    close_parts.append(sub["Close"].rename(ticker))
                    volume_parts.append(sub["Volume"].rename(ticker))
        else:
            ticker = batch[0]
            if "Close" in data and data["Close"].notna().sum() > 0:
                close_parts.append(data["Close"].rename(ticker))
                volume_parts.append(data["Volume"].rename(ticker))

        time.sleep(0.5)

    if not close_parts:
        raise RuntimeError("No market data downloaded.")

    close = pd.concat(close_parts, axis=1).sort_index()
    volume = pd.concat(volume_parts, axis=1).reindex(close.index)
    close = close.loc[:, ~close.columns.duplicated()]
    volume = volume.loc[:, ~volume.columns.duplicated()]
    return close, volume


def build_events_for_ticker(
    ticker: str,
    close: pd.DataFrame,
    volume: pd.DataFrame,
    cfg: GateConfig = CFG,
) -> pd.DataFrame:
    if ticker not in close or ticker not in volume or BENCHMARK not in close:
        return pd.DataFrame()

    df = pd.DataFrame(
        {
            "close": close[ticker],
            "volume": volume[ticker],
            "spy_close": close[BENCHMARK],
        }
    ).dropna(subset=["close", "spy_close"])

    if len(df) < 350:
        return pd.DataFrame()

    df["ret5"] = df["close"].pct_change(cfg.return_window_days)
    df["spy_ret5"] = df["spy_close"].pct_change(cfg.return_window_days)
    df["excess5"] = df["ret5"] - df["spy_ret5"]

    # Thresholds use prior observations only.
    df["winner_threshold"] = (
        df["excess5"]
        .shift(1)
        .rolling(cfg.winner_lookback_days, min_periods=cfg.winner_min_periods)
        .quantile(cfg.winner_quantile)
    )
    df["winner_state"] = df["excess5"] > df["winner_threshold"]

    # Take only the first day entering an extreme-winner state to reduce repeated,
    # highly overlapping observations from the same run-up.
    prior_state = df["winner_state"].shift(1).fillna(False).astype(bool)
    df["winner_event"] = df["winner_state"] & ~prior_state

    df["volume_5d"] = df["volume"].rolling(cfg.volume_window_days).mean()
    df["volume_baseline"] = (
        df["volume"]
        .shift(cfg.volume_window_days)
        .rolling(cfg.volume_baseline_days, min_periods=40)
        .mean()
    )
    df["volume_ratio"] = df["volume_5d"] / df["volume_baseline"]
    df["volume_threshold"] = (
        df["volume_ratio"]
        .shift(1)
        .rolling(cfg.volume_quantile_lookback_days, min_periods=cfg.volume_min_periods)
        .quantile(cfg.volume_quantile)
    )
    df["volume_extreme"] = df["volume_ratio"] > df["volume_threshold"]
    df["crowded_event"] = df["winner_event"] & df["volume_extreme"]
    df["plain_winner_event"] = df["winner_event"] & ~df["volume_extreme"]

    # Signal is known at close t. Entry is the next close (t+1), so the event study
    # cannot earn the signal-day close-to-close move that defined the signal itself.
    for h in HORIZONS:
        stock_entry = df["close"].shift(-1)
        stock_exit = df["close"].shift(-(h + 1))
        spy_entry = df["spy_close"].shift(-1)
        spy_exit = df["spy_close"].shift(-(h + 1))
        df[f"fwd_{h}d"] = stock_exit / stock_entry - 1.0
        df[f"spy_fwd_{h}d"] = spy_exit / spy_entry - 1.0
        df[f"fwd_excess_{h}d"] = df[f"fwd_{h}d"] - df[f"spy_fwd_{h}d"]

    events = df[df["winner_event"]].copy()
    if events.empty:
        return events
    events["ticker"] = ticker
    events["event_type"] = np.where(events["crowded_event"], "crowded", "plain_winner")
    events.index.name = "date"
    return events.reset_index()


def _era(date: pd.Timestamp) -> str:
    if date < pd.Timestamp("2020-01-01"):
        return "development_2015_2019"
    if date < pd.Timestamp("2023-01-01"):
        return "validation_2020_2022"
    return "final_oos_2023_plus"


def _tstat_clustered_by_date(events: pd.DataFrame, value_col: str) -> tuple[float, int]:
    if events.empty:
        return np.nan, 0
    daily = events.groupby("date")[value_col].mean().dropna()
    if len(daily) < 2:
        return np.nan, len(daily)
    se = daily.std(ddof=1) / np.sqrt(len(daily))
    return (daily.mean() / se if se > 0 else np.nan), len(daily)


def summarize(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for era in ["all", "development_2015_2019", "validation_2020_2022", "final_oos_2023_plus"]:
        era_df = events if era == "all" else events[events["era"] == era]
        for group in ["all_winners", "plain_winner", "crowded"]:
            if group == "all_winners":
                g = era_df
            else:
                g = era_df[era_df["event_type"] == group]
            for h in HORIZONS:
                col = f"fwd_excess_{h}d"
                x = g[col].dropna()
                tstat, n_dates = _tstat_clustered_by_date(g, col)
                rows.append(
                    {
                        "era": era,
                        "group": group,
                        "horizon_days": h,
                        "n_events": int(len(x)),
                        "n_event_dates": int(n_dates),
                        "mean_excess": float(x.mean()) if len(x) else np.nan,
                        "median_excess": float(x.median()) if len(x) else np.nan,
                        "hit_rate_positive": float((x > 0).mean()) if len(x) else np.nan,
                        "t_stat_date_clustered": float(tstat) if np.isfinite(tstat) else np.nan,
                    }
                )
    return pd.DataFrame(rows)


def compare_crowded_vs_plain(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for era in ["all", "development_2015_2019", "validation_2020_2022", "final_oos_2023_plus"]:
        era_df = events if era == "all" else events[events["era"] == era]
        for h in HORIZONS:
            col = f"fwd_excess_{h}d"
            c = era_df[era_df["event_type"] == "crowded"].groupby("date")[col].mean().dropna()
            p = era_df[era_df["event_type"] == "plain_winner"].groupby("date")[col].mean().dropna()
            if len(c) >= 2 and len(p) >= 2:
                test = stats.ttest_ind(c, p, equal_var=False, nan_policy="omit")
                pval = float(test.pvalue)
            else:
                pval = np.nan
            rows.append(
                {
                    "era": era,
                    "horizon_days": h,
                    "crowded_n_dates": len(c),
                    "plain_n_dates": len(p),
                    "crowded_mean": float(c.mean()) if len(c) else np.nan,
                    "plain_mean": float(p.mean()) if len(p) else np.nan,
                    "incremental_crowding_effect": float(c.mean() - p.mean()) if len(c) and len(p) else np.nan,
                    "welch_p_value_descriptive": pval,
                }
            )
    return pd.DataFrame(rows)


def write_research_summary(
    events: pd.DataFrame,
    summary: pd.DataFrame,
    comparison: pd.DataFrame,
    downloaded: list[str],
    missing: list[str],
) -> None:
    primary = comparison[comparison["horizon_days"] == PRIMARY_HORIZON].copy()

    lines = [
        "# Crowding Gate 01 — Extreme Winner + Abnormal Volume",
        "",
        "## Pre-declared question",
        "Does unusually high trading volume add incremental short-term reversal information after an extreme 5-day stock-specific gain?",
        "",
        "## Design",
        f"- Screening universe: current S&P 100-style liquid large-cap list ({len(SP100)} names declared in code).",
        "- Benchmark: SPY.",
        "- Extreme winner: 5-day excess return above the stock's prior-only rolling 95th percentile.",
        "- Crowding proxy: 5-day average share volume / prior 60-day average volume above its prior-only rolling 95th percentile.",
        "- Event: first day entering the extreme-winner state.",
        "- Trade timing: signal at close t; forward return starts at close t+1.",
        f"- Primary horizon: {PRIMARY_HORIZON} trading days; secondary: {', '.join(map(str, HORIZONS))} days.",
        "- Era split: development 2015–2019; validation 2020–2022; final OOS 2023+.",
        "- This is intentionally a cheap screen with current constituents; survivorship bias is not corrected in Gate 01.",
        "",
        "## Data coverage",
        f"- Downloaded symbols: {len(downloaded)} including SPY.",
        f"- Missing/insufficient symbols: {', '.join(missing) if missing else 'none'}.",
        f"- Winner events analyzed: {len(events):,}.",
        f"- Crowded winner events: {(events['event_type'] == 'crowded').sum():,}.",
        "",
        "## Primary 10-day incremental result",
        "Negative incremental values favor the crowding-exhaustion hypothesis.",
        "",
        "| Era | Crowded mean | Plain-winner mean | Incremental crowding effect | Crowded event dates |",
        "|---|---:|---:|---:|---:|",
    ]

    for _, r in primary.iterrows():
        def pct(v):
            return "NA" if pd.isna(v) else f"{100*v:.2f}%"
        lines.append(
            f"| {r['era']} | {pct(r['crowded_mean'])} | {pct(r['plain_mean'])} | {pct(r['incremental_crowding_effect'])} | {int(r['crowded_n_dates'])} |"
        )

    # Mechanical, intentionally conservative interpretation. It does not promote the
    # signal based on a p-value alone.
    oos = primary[primary["era"] == "final_oos_2023_plus"]
    dev = primary[primary["era"] == "development_2015_2019"]
    val = primary[primary["era"] == "validation_2020_2022"]
    verdict = "INSUFFICIENT"
    if not oos.empty and not dev.empty and not val.empty:
        oe = oos.iloc[0]
        de = dev.iloc[0]
        ve = val.iloc[0]
        enough = oe["crowded_n_dates"] >= 20
        same_direction = all(
            pd.notna(x) and x < 0
            for x in [de["incremental_crowding_effect"], ve["incremental_crowding_effect"], oe["incremental_crowding_effect"]]
        )
        meaningful = pd.notna(oe["incremental_crowding_effect"]) and oe["incremental_crowding_effect"] <= -0.003
        if enough and same_direction and meaningful:
            verdict = "PROVISIONAL_SURVIVOR"
        elif enough:
            verdict = "STOP"

    lines += [
        "",
        "## Gate verdict",
        f"**{verdict}**",
        "",
        "Interpretation rule used for this cheap gate: proceed only if the final-OOS 10-day incremental effect is at least -0.30 percentage points, the direction is negative in development/validation/final-OOS, and there are at least 20 final-OOS crowded event dates. This is a practical research gate, not a claim of statistical significance.",
        "",
        "If STOP: do not buy options data, sentiment data, or point-in-time constituent history for this idea.",
        "If PROVISIONAL_SURVIVOR: next test sector-relative returns and point-in-time universe membership before adding historical options activity.",
        "",
        "## Caveats",
        "- Current-constituent survivorship bias is deliberately tolerated only for this screening gate.",
        "- Yahoo Finance is convenient research data, not an institutional point-in-time database.",
        "- Overlapping forward horizons create serial dependence; date-clustered event means are reported to reduce false precision.",
        "- Volume is only a proxy for crowding/attention; this test does not establish retail participation or option positioning.",
        "- A positive result must survive a better universe and sector-relative benchmark before any trading conclusion.",
    ]
    (OUTPUT_DIR / "research_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    close, volume = download_ohlcv(SP100)

    downloaded = [t for t in SP100 if t in close.columns and close[t].notna().sum() >= 350]
    missing = [t for t in SP100 if t not in downloaded]

    event_frames = [build_events_for_ticker(t, close, volume) for t in downloaded]
    event_frames = [f for f in event_frames if not f.empty]
    if not event_frames:
        raise RuntimeError("No qualifying events found.")

    events = pd.concat(event_frames, ignore_index=True)
    events = events[events["date"] >= RESEARCH_START].copy()
    events["era"] = events["date"].map(_era)

    summary = summarize(events)
    comparison = compare_crowded_vs_plain(events)

    keep_cols = [
        "date", "ticker", "event_type", "excess5", "winner_threshold", "volume_ratio", "volume_threshold",
        *[f"fwd_excess_{h}d" for h in HORIZONS],
        "era",
    ]
    events[keep_cols].sort_values(["date", "ticker"]).to_csv(OUTPUT_DIR / "event_log.csv", index=False)
    summary.to_csv(OUTPUT_DIR / "group_summary.csv", index=False)
    comparison.to_csv(OUTPUT_DIR / "crowding_incremental.csv", index=False)

    ticker_summary = (
        events.groupby(["ticker", "event_type"])[f"fwd_excess_{PRIMARY_HORIZON}d"]
        .agg(["count", "mean", "median"])
        .reset_index()
        .sort_values(["event_type", "count"], ascending=[True, False])
    )
    ticker_summary.to_csv(OUTPUT_DIR / "ticker_summary.csv", index=False)

    coverage = pd.DataFrame(
        {
            "ticker": SP100,
            "downloaded_with_350plus_rows": [t in downloaded for t in SP100],
            "n_rows": [int(close[t].notna().sum()) if t in close else 0 for t in SP100],
        }
    )
    coverage.to_csv(OUTPUT_DIR / "data_coverage.csv", index=False)

    write_research_summary(events, summary, comparison, downloaded, missing)

    print((OUTPUT_DIR / "research_summary.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
