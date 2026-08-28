"""Point-in-time MSP/DAL divergence analysis.

This module tests a different hypothesis from simple correlation: extreme
separations between an MSP travel-demand signal and DAL price momentum may
contain information about subsequent DAL returns.

The implementation is intentionally conservative:
* MSP traffic uses year-over-year growth to remove most seasonality.
* The MSP signal is shifted by a configurable publication lag (default 1 month).
* Standardization uses only trailing observations available at each date.
* Divergence thresholds are fixed z-score cutoffs, not optimized quantiles.
* Forward returns are reported separately at 1, 3, 6, and 12 months.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DivergenceConfig:
    msp_yoy_months: int = 12
    msp_release_lag: int = 1
    dal_momentum_months: int = 3
    z_window: int = 36
    z_min_periods: int = 18
    extreme_z: float = 1.5
    forward_horizons: tuple[int, ...] = (1, 3, 6, 12)


def trailing_zscore(series: pd.Series, window: int, min_periods: int) -> pd.Series:
    """Return a rolling z-score using only data available through each row."""
    mean = series.rolling(window=window, min_periods=min_periods).mean()
    std = series.rolling(window=window, min_periods=min_periods).std(ddof=1)
    z = (series - mean) / std.replace(0.0, np.nan)
    return z


def build_divergence_frame(
    df: pd.DataFrame,
    config: DivergenceConfig | None = None,
    passenger_col: str = "passengers",
    price_col: str = "close",
    date_col: str = "year_month",
) -> pd.DataFrame:
    """Construct point-in-time MSP/DAL divergence signals and forward returns.

    Positive divergence means MSP demand is stronger than DAL price momentum.
    Negative divergence means MSP demand is weaker than DAL price momentum.
    """
    cfg = config or DivergenceConfig()
    required = {date_col, passenger_col, price_col}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    out = out.sort_values(date_col).reset_index(drop=True)

    # Fundamental signal: YoY MSP traffic growth, delayed to reflect publication.
    out["msp_yoy"] = out[passenger_col].pct_change(cfg.msp_yoy_months)
    out["msp_signal_pit"] = out["msp_yoy"].shift(cfg.msp_release_lag)

    # Market signal known at the observation month-end.
    out["dal_momentum"] = out[price_col].pct_change(cfg.dal_momentum_months)

    # Standardize each series separately with trailing-only information.
    out["msp_z"] = trailing_zscore(out["msp_signal_pit"], cfg.z_window, cfg.z_min_periods)
    out["dal_z"] = trailing_zscore(out["dal_momentum"], cfg.z_window, cfg.z_min_periods)
    out["divergence_z"] = out["msp_z"] - out["dal_z"]

    out["divergence_state"] = "normal"
    out.loc[out["divergence_z"] >= cfg.extreme_z, "divergence_state"] = "strong_msp_weak_dal"
    out.loc[out["divergence_z"] <= -cfg.extreme_z, "divergence_state"] = "weak_msp_strong_dal"

    for h in cfg.forward_horizons:
        out[f"dal_fwd_{h}m"] = out[price_col].shift(-h) / out[price_col] - 1.0

    return out


def summarize_forward_returns(
    frame: pd.DataFrame,
    horizons: Iterable[int] = (1, 3, 6, 12),
) -> pd.DataFrame:
    """Summarize conditional DAL returns by divergence state and horizon."""
    rows: list[dict] = []
    for state, group in frame.groupby("divergence_state", sort=False):
        for h in horizons:
            col = f"dal_fwd_{h}m"
            if col not in group.columns:
                raise ValueError(f"Missing forward return column: {col}")
            values = group[col].dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "state": state,
                    "horizon_months": h,
                    "n": int(values.size),
                    "mean_return": float(values.mean()),
                    "median_return": float(values.median()),
                    "win_rate": float((values > 0).mean()),
                    "std_return": float(values.std(ddof=1)) if values.size > 1 else np.nan,
                }
            )
    return pd.DataFrame(rows)


def divergence_event_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Return only extreme divergence observations, strongest first."""
    cols = [
        "year_month",
        "msp_signal_pit",
        "dal_momentum",
        "msp_z",
        "dal_z",
        "divergence_z",
        "divergence_state",
        "dal_fwd_1m",
        "dal_fwd_3m",
        "dal_fwd_6m",
        "dal_fwd_12m",
    ]
    available = [c for c in cols if c in frame.columns]
    events = frame.loc[frame["divergence_state"] != "normal", available].copy()
    if events.empty:
        return events
    return events.reindex(events["divergence_z"].abs().sort_values(ascending=False).index)
