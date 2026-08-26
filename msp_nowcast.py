"""
Simple point-in-time MSP enplanement nowcast benchmarks.

These are intentionally simple hurdle models for later HMM/regime work.

Benchmarks
----------
1. seasonal_naive:
       forecast(target t) = actual(t - 12 months)

2. yoy_trend:
       forecast(target t) = actual(t - 12 months) * (1 + mean recent known YoY growth)

Every input observation is filtered through available_as_of() before use.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np
import pandas as pd

from msp_availability import available_as_of


@dataclass(frozen=True)
class NowcastResult:
    method: str
    as_of_date: str
    target_period: str
    forecast_enplanements: float
    prior_year_period: str
    prior_year_enplanements: float
    latest_known_period: str
    recent_yoy_mean: float | None = None
    yoy_window_used: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _as_period(value) -> pd.Period:
    return value if isinstance(value, pd.Period) else pd.Period(value, freq="M")


def _known_target_guard(known: pd.DataFrame, target: pd.Period) -> None:
    if target in set(known["period"]):
        raise ValueError(
            f"Target {target} was already released as of this date; "
            "nowcast benchmarks are for unpublished observations."
        )


def _prior_year_base(
    known: pd.DataFrame,
    target: pd.Period,
) -> tuple[pd.Period, float]:
    prior = target - 12
    row = known.loc[known["period"] == prior]
    if row.empty:
        raise ValueError(
            f"Cannot forecast {target}: prior-year observation {prior} "
            "was not available as of the requested date."
        )
    return prior, float(row.iloc[-1]["enplanements"])


def seasonal_naive(
    df: pd.DataFrame,
    as_of_date,
    target_period,
) -> NowcastResult:
    """Forecast target enplanements as the known same month one year earlier."""
    known = available_as_of(df, as_of_date)
    if known.empty:
        raise ValueError("No verified MSP observations are available as of this date.")

    target = _as_period(target_period)
    _known_target_guard(known, target)
    prior, base = _prior_year_base(known, target)

    return NowcastResult(
        method="seasonal_naive",
        as_of_date=str(pd.Timestamp(as_of_date).date()),
        target_period=str(target),
        forecast_enplanements=base,
        prior_year_period=str(prior),
        prior_year_enplanements=base,
        latest_known_period=str(known["period"].max()),
    )


def yoy_trend(
    df: pd.DataFrame,
    as_of_date,
    target_period,
    *,
    window: int = 3,
) -> NowcastResult:
    """
    Apply the mean of the most recent known YoY growth rates to the
    same-month prior-year enplanement base.
    """
    if window < 1:
        raise ValueError("window must be >= 1")

    known = available_as_of(df, as_of_date)
    if known.empty:
        raise ValueError("No verified MSP observations are available as of this date.")

    target = _as_period(target_period)
    _known_target_guard(known, target)
    prior, base = _prior_year_base(known, target)

    recent = known.dropna(subset=["yoy_change"]).tail(window)
    if recent.empty:
        raise ValueError(
            "No known YoY growth observations are available for the trend model."
        )

    recent_mean = float(recent["yoy_change"].mean())
    forecast = base * (1.0 + recent_mean)

    return NowcastResult(
        method="yoy_trend",
        as_of_date=str(pd.Timestamp(as_of_date).date()),
        target_period=str(target),
        forecast_enplanements=float(forecast),
        prior_year_period=str(prior),
        prior_year_enplanements=base,
        latest_known_period=str(known["period"].max()),
        recent_yoy_mean=recent_mean,
        yoy_window_used=len(recent),
    )


def forecast_benchmarks(
    df: pd.DataFrame,
    as_of_date,
    target_period,
    *,
    yoy_window: int = 3,
) -> pd.DataFrame:
    """Return both benchmark forecasts in one tidy DataFrame."""
    results = [
        seasonal_naive(df, as_of_date, target_period),
        yoy_trend(df, as_of_date, target_period, window=yoy_window),
    ]
    return pd.DataFrame([r.to_dict() for r in results])


def score_forecast(forecast: float, actual: float) -> dict:
    """Return basic forecast errors for one observation."""
    error = float(forecast - actual)
    absolute_error = abs(error)
    ape = absolute_error / actual if actual != 0 else np.nan
    return {
        "error": error,
        "absolute_error": absolute_error,
        "absolute_percentage_error": ape,
    }
