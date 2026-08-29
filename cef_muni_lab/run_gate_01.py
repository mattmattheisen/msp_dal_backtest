from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

FUNDS = {
    "EOT": "XEOTX",
    "MMU": "XMMUX",
    "EVN": "XEVNX",
    "NZF": "XNZFX",
    "NEA": "XNEAX",
    "NAD": "XNADX",
    "NVG": "XNVGX",
    "KTF": "XKTFX",
    "EIM": "XEIMX",
    "NMI": "XNMIX",
    "MMD": "XMMDX",
}
BENCHMARK = "MUB"


@dataclass(frozen=True)
class GateConfig:
    start: str = "2007-01-01"
    end: str = "2026-03-01"  # only complete calendar years through 2025 are evaluated
    rolling_days: int = 756
    min_rolling_days: int = 500
    discount_quantile: float = 0.10
    forward_days: int = 20
    first_event_year: int = 2010
    last_event_year: int = 2025


def _one_symbol(symbol: str, cfg: GateConfig) -> pd.DataFrame:
    raw = yf.download(
        symbol,
        start=cfg.start,
        end=cfg.end,
        auto_adjust=False,
        actions=False,
        progress=False,
        threads=False,
    )
    if raw.empty:
        return pd.DataFrame(columns=["close", "adj_close"])

    # yfinance may return a one-symbol MultiIndex depending on version.
    if isinstance(raw.columns, pd.MultiIndex):
        try:
            raw = raw.xs(symbol, axis=1, level=-1)
        except Exception:
            raw.columns = raw.columns.get_level_values(0)

    close = raw["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]

    if "Adj Close" in raw.columns:
        adj = raw["Adj Close"]
        if isinstance(adj, pd.DataFrame):
            adj = adj.iloc[:, 0]
    else:
        adj = close.copy()

    out = pd.DataFrame({"close": pd.to_numeric(close, errors="coerce"),
                        "adj_close": pd.to_numeric(adj, errors="coerce")})
    out.index = pd.to_datetime(out.index).tz_localize(None)
    return out.dropna(how="all").sort_index()


def _prepare_fund(ticker: str, nav_ticker: str, bench: pd.DataFrame, cfg: GateConfig) -> pd.DataFrame:
    price = _one_symbol(ticker, cfg).rename(columns={"close": "price_close", "adj_close": "price_adj"})
    nav = _one_symbol(nav_ticker, cfg).rename(columns={"close": "nav_close", "adj_close": "nav_adj"})
    if price.empty or nav.empty:
        return pd.DataFrame()

    df = price.join(nav[["nav_close"]], how="inner").join(
        bench[["adj_close"]].rename(columns={"adj_close": "mub_adj"}), how="inner"
    )
    df = df.dropna(subset=["price_close", "price_adj", "nav_close", "mub_adj"]).copy()
    if df.empty:
        return df

    df["discount"] = df["price_close"] / df["nav_close"] - 1.0
    df["q10_prior"] = (
        df["discount"].shift(1).rolling(cfg.rolling_days, min_periods=cfg.min_rolling_days).quantile(cfg.discount_quantile)
    )
    return df


def _last_obs_on_or_before(df: pd.DataFrame, date: pd.Timestamp) -> pd.Timestamp | None:
    idx = df.index[df.index <= date]
    return idx[-1] if len(idx) else None


def build_observations(cfg: GateConfig = GateConfig()) -> tuple[pd.DataFrame, pd.DataFrame]:
    bench = _one_symbol(BENCHMARK, cfg)
    rows: list[dict] = []
    coverage: list[dict] = []

    for ticker, nav_ticker in FUNDS.items():
        df = _prepare_fund(ticker, nav_ticker, bench, cfg)
        coverage.append({
            "ticker": ticker,
            "nav_ticker": nav_ticker,
            "n_common_days": int(len(df)),
            "first_date": str(df.index.min().date()) if not df.empty else "",
            "last_date": str(df.index.max().date()) if not df.empty else "",
        })
        if df.empty:
            continue

        for year in range(cfg.first_event_year, cfg.last_event_year + 1):
            year_end = _last_obs_on_or_before(df, pd.Timestamp(year=year, month=12, day=31))
            prev_end = _last_obs_on_or_before(df, pd.Timestamp(year=year - 1, month=12, day=31))
            if year_end is None or prev_end is None:
                continue
            if year_end.year != year or pd.isna(df.at[year_end, "q10_prior"]):
                continue

            pos = df.index.get_loc(year_end)
            if not isinstance(pos, (int, np.integer)) or pos + cfg.forward_days >= len(df):
                continue
            future_date = df.index[pos + cfg.forward_days]

            price_adj_0 = float(df.at[year_end, "price_adj"])
            price_adj_prev = float(df.at[prev_end, "price_adj"])
            price_adj_f = float(df.at[future_date, "price_adj"])
            mub_0 = float(df.at[year_end, "mub_adj"])
            mub_f = float(df.at[future_date, "mub_adj"])

            discount_0 = float(df.at[year_end, "discount"])
            discount_f = float(df.at[future_date, "discount"])
            q10 = float(df.at[year_end, "q10_prior"])
            ytd = price_adj_0 / price_adj_prev - 1.0
            extreme = discount_0 <= q10
            taxloss_extreme = bool(extreme and ytd < 0)
            neg_ytd_control = bool((ytd < 0) and (not extreme))

            rows.append({
                "ticker": ticker,
                "nav_ticker": nav_ticker,
                "year": year,
                "event_date": year_end.date().isoformat(),
                "future_date": future_date.date().isoformat(),
                "discount_pct": 100.0 * discount_0,
                "prior_q10_pct": 100.0 * q10,
                "ytd_total_return": ytd,
                "extreme_discount": bool(extreme),
                "taxloss_extreme": taxloss_extreme,
                "neg_ytd_control": neg_ytd_control,
                "discount_change_20d_pp": 100.0 * (discount_f - discount_0),
                "cef_return_20d": price_adj_f / price_adj_0 - 1.0,
                "mub_return_20d": mub_f / mub_0 - 1.0,
                "excess_mub_20d": (price_adj_f / price_adj_0 - 1.0) - (mub_f / mub_0 - 1.0),
            })

    obs = pd.DataFrame(rows)
    if not obs.empty:
        obs["era"] = np.select(
            [obs["year"] <= 2017, obs["year"] <= 2021],
            ["development", "validation"],
            default="oos_2022_2025",
        )
    return obs, pd.DataFrame(coverage)


def _summarize_group(df: pd.DataFrame, label: str) -> dict:
    x = df.copy()
    return {
        "group": label,
        "n": int(len(x)),
        "mean_discount_change_pp": x["discount_change_20d_pp"].mean() if len(x) else np.nan,
        "median_discount_change_pp": x["discount_change_20d_pp"].median() if len(x) else np.nan,
        "compression_hit_rate": (x["discount_change_20d_pp"] > 0).mean() if len(x) else np.nan,
        "mean_cef_return_20d": x["cef_return_20d"].mean() if len(x) else np.nan,
        "mean_excess_mub_20d": x["excess_mub_20d"].mean() if len(x) else np.nan,
    }


def summarize(obs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    rows = []
    for era, g in obs.groupby("era"):
        for label, mask in {
            "taxloss_extreme": g["taxloss_extreme"],
            "negative_ytd_control": g["neg_ytd_control"],
            "all_extreme": g["extreme_discount"],
        }.items():
            row = _summarize_group(g[mask], label)
            row["era"] = era
            rows.append(row)

    summary = pd.DataFrame(rows)

    year_rows = []
    for year, g in obs[obs["taxloss_extreme"]].groupby("year"):
        year_rows.append({
            "year": int(year),
            "n_events": int(len(g)),
            "mean_discount_change_pp": g["discount_change_20d_pp"].mean(),
            "mean_excess_mub_20d": g["excess_mub_20d"].mean(),
        })
    return summary, pd.DataFrame(year_rows)


def evaluate_gate(obs: pd.DataFrame, year_summary: pd.DataFrame) -> dict:
    oos = obs[(obs["year"] >= 2022) & (obs["year"] <= 2025)]
    events = oos[oos["taxloss_extreme"]]
    controls = oos[oos["neg_ytd_control"]]

    event_mean = events["discount_change_20d_pp"].mean() if len(events) else np.nan
    control_mean = controls["discount_change_20d_pp"].mean() if len(controls) else np.nan
    incremental = event_mean - control_mean if np.isfinite(event_mean) and np.isfinite(control_mean) else np.nan
    event_years = year_summary[(year_summary["year"] >= 2022) & (year_summary["year"] <= 2025)]
    positive_years = int((event_years["mean_discount_change_pp"] > 0).sum()) if len(event_years) else 0
    mean_excess = events["excess_mub_20d"].mean() if len(events) else np.nan

    checks = {
        "n_events_at_least_10": len(events) >= 10,
        "mean_compression_at_least_1pp": bool(np.isfinite(event_mean) and event_mean >= 1.0),
        "incremental_vs_control_at_least_0_5pp": bool(np.isfinite(incremental) and incremental >= 0.5),
        "positive_in_at_least_3_oos_years": positive_years >= 3,
        "mean_excess_return_vs_mub_positive": bool(np.isfinite(mean_excess) and mean_excess > 0),
    }

    return {
        "decision": "GO" if all(checks.values()) else "STOP",
        "oos_event_count": int(len(events)),
        "oos_control_count": int(len(controls)),
        "oos_mean_discount_compression_pp": event_mean,
        "oos_control_mean_discount_change_pp": control_mean,
        "oos_incremental_compression_pp": incremental,
        "oos_positive_event_years": positive_years,
        "oos_mean_excess_mub_20d": mean_excess,
        **checks,
    }


def write_gate_markdown(result: dict, coverage: pd.DataFrame, out: Path) -> None:
    lines = [
        "# Municipal CEF Gate 01 Result",
        "",
        f"**Decision: {result['decision']}**",
        "",
        "## Primary OOS metrics (2022–2025)",
        "",
        f"- Event observations: {result['oos_event_count']}",
        f"- Negative-YTD control observations: {result['oos_control_count']}",
        f"- Mean 20-day discount compression: {result['oos_mean_discount_compression_pp']:.3f} pp" if np.isfinite(result['oos_mean_discount_compression_pp']) else "- Mean 20-day discount compression: n/a",
        f"- Control mean discount change: {result['oos_control_mean_discount_change_pp']:.3f} pp" if np.isfinite(result['oos_control_mean_discount_change_pp']) else "- Control mean discount change: n/a",
        f"- Incremental compression vs control: {result['oos_incremental_compression_pp']:.3f} pp" if np.isfinite(result['oos_incremental_compression_pp']) else "- Incremental compression vs control: n/a",
        f"- Positive event years: {result['oos_positive_event_years']} of 4 possible",
        f"- Mean 20-day excess return vs MUB: {result['oos_mean_excess_mub_20d']:.3%}" if np.isfinite(result['oos_mean_excess_mub_20d']) else "- Mean 20-day excess return vs MUB: n/a",
        "",
        "## Gate checks",
        "",
    ]
    for key in [
        "n_events_at_least_10",
        "mean_compression_at_least_1pp",
        "incremental_vs_control_at_least_0_5pp",
        "positive_in_at_least_3_oos_years",
        "mean_excess_return_vs_mub_positive",
    ]:
        lines.append(f"- {'PASS' if result[key] else 'FAIL'} — {key}")

    missing = coverage[coverage["n_common_days"] == 0]
    lines += ["", "## Coverage", "", f"Funds attempted: {len(coverage)}", f"Funds with no common price/NAV history: {len(missing)}"]
    if len(missing):
        lines.append("Missing: " + ", ".join(missing["ticker"].tolist()))

    lines += [
        "",
        "## Interpretation rule",
        "",
        "If Decision is STOP, do not add more variables or optimize thresholds. Archive the result. If Decision is GO, the next step is to obtain a broader point-in-time CEF universe including historical/delisted funds and re-run the frozen rule.",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def run(output_dir: str | Path = "cef_muni_lab/outputs") -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    cfg = GateConfig()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    obs, coverage = build_observations(cfg)
    obs.to_csv(out / "observations.csv", index=False)
    coverage.to_csv(out / "coverage.csv", index=False)

    if obs.empty:
        raise RuntimeError("No usable fund-year observations were produced.")

    summary, year_summary = summarize(obs)
    summary.to_csv(out / "summary.csv", index=False)
    year_summary.to_csv(out / "year_summary.csv", index=False)

    result = evaluate_gate(obs, year_summary)
    pd.DataFrame([result]).to_csv(out / "gate_result.csv", index=False)
    write_gate_markdown(result, coverage, out / "gate_result.md")

    print((out / "gate_result.md").read_text(encoding="utf-8"))
    return obs, summary, result


if __name__ == "__main__":
    run()
