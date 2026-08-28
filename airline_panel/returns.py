"""Return-side gate for the Phase-1 airline demand/capacity panel.

This module deliberately keeps the economic signal definition separate from market data.
Prices are joined only after the demand-capacity specification is frozen.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

HORIZONS = (1, 3, 6)  # monthly approximation to 21/63/126 sessions


def attach_monthly_forward_returns(panel: pd.DataFrame, prices: pd.DataFrame) -> pd.DataFrame:
    """Attach forward carrier and equal-weight peer-basket returns.

    prices columns: date, carrier, close.  `date` is the month represented by the
    close. The signal becomes tradable only after `assumed_available_date`; callers
    should map that date to the first complete monthly price observation after release.
    """
    px = prices.copy().sort_values(["carrier", "date"])
    px["date"] = pd.to_datetime(px["date"])
    for h in HORIZONS:
        px[f"fwd_{h}m"] = px.groupby("carrier")["close"].shift(-h) / px["close"] - 1
        basket = px.groupby("date")[f"fwd_{h}m"].transform("mean")
        px[f"excess_{h}m"] = px[f"fwd_{h}m"] - basket

    out = panel.copy()
    out["signal_month"] = pd.to_datetime(out["assumed_available_date"]).dt.to_period("M").dt.to_timestamp()
    keep = ["date", "carrier", "close"] + [c for h in HORIZONS for c in (f"fwd_{h}m", f"excess_{h}m")]
    px = px[keep].rename(columns={"date": "signal_month"})
    return out.merge(px, on=["signal_month", "carrier"], how="left", validate="many_to_one")


def add_cross_sectional_groups(df: pd.DataFrame) -> pd.DataFrame:
    """Create a six-stock cross-sectional rank without pretending six names form five clean quintiles.

    The original plan said quintiles. With exactly six stocks, quintiles mechanically
    create uneven cells. This correction is made before viewing returns: each month is
    ranked 1..6 on dc_gap; bottom two = low, middle two = mid, top two = high. The
    continuous percentile rank is retained for Spearman/information-coefficient tests.
    """
    out = df.copy()
    out["dc_rank"] = out.groupby("date")["dc_gap"].rank(method="first")
    n = out.groupby("date")["dc_gap"].transform("count")
    out["dc_rank_pct"] = (out["dc_rank"] - 1) / (n - 1)
    out["dc_group"] = np.select(
        [out["dc_rank"] <= 2, out["dc_rank"] >= n - 1],
        ["low", "high"],
        default="mid",
    )
    return out


def summarize_gate(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for h in HORIZONS:
        col = f"excess_{h}m"
        for group, g in df.groupby("dc_group", observed=True):
            s = g[col].dropna()
            rows.append({
                "horizon_months": h,
                "group": group,
                "n": int(s.size),
                "mean_excess": s.mean(),
                "median_excess": s.median(),
                "hit_rate": (s > 0).mean(),
            })
    return pd.DataFrame(rows)
