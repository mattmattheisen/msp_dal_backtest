"""
Point-in-time MSP enplanement nowcast benchmarks.

Methods
-------
1. seasonal_naive:
       E_hat[t] = E[t-12]

2. yoy_trend:
       E_hat[t] = E[t-12] * (1 + mean recent known YoY growth)

3. ar1_yoy:
       g[t] = alpha + phi * g[t-1] + epsilon[t]
       E_hat[t] = E[t-12] * (1 + g_hat[t])

The AR(1) model is fit on an expanding window of known YoY growth rates only.
If the target is multiple months beyond the latest known period, the growth
forecast is recursively propagated one month at a time.
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
    ar_alpha: float | None = None
    ar_phi: float | None = None
    ar_pairs_used: int | None = None
    forecast_horizon_months: int | None = None
    forecast_yoy_growth: float | None = None

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


def _month_gap(later: pd.Period, earlier: pd.Period) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def seasonal_naive(df, as_of_date, target_period) -> NowcastResult:
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


def yoy_trend(df, as_of_date, target_period, *, window: int = 3) -> NowcastResult:
    """Apply recent known mean YoY growth to the prior-year month base."""
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
        raise ValueError("No known YoY growth observations are available.")

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
        forecast_yoy_growth=recent_mean,
    )


def _fit_ar1_growth(
    known: pd.DataFrame,
    *,
    min_pairs: int = 4,
) -> tuple[float, float, int]:
    """Fit g_t = alpha + phi*g_(t-1) using consecutive known monthly YoY data."""
    growth = known.dropna(subset=["yoy_change"])[["period", "yoy_change"]].copy()
    growth = growth.sort_values("period").reset_index(drop=True)

    xs, ys = [], []
    for i in range(1, len(growth)):
        previous_period = growth.loc[i - 1, "period"]
        current_period = growth.loc[i, "period"]
        if _month_gap(current_period, previous_period) != 1:
            continue
        xs.append(float(growth.loc[i - 1, "yoy_change"]))
        ys.append(float(growth.loc[i, "yoy_change"]))

    if len(xs) < min_pairs:
        raise ValueError(
            f"AR(1) requires at least {min_pairs} consecutive YoY pairs; "
            f"only {len(xs)} are available."
        )

    x_matrix = np.column_stack([np.ones(len(xs)), np.asarray(xs)])
    y_vector = np.asarray(ys)
    beta, *_ = np.linalg.lstsq(x_matrix, y_vector, rcond=None)
    alpha, phi = float(beta[0]), float(beta[1])
    return alpha, phi, len(xs)


def ar1_yoy(
    df,
    as_of_date,
    target_period,
    *,
    min_pairs: int = 4,
) -> NowcastResult:
    """
    Expanding-window AR(1) forecast of YoY MSP growth.

    For a multi-month information gap, recursively propagate the AR(1) growth
    forecast from the latest known growth observation through the target month.
    """
    known = available_as_of(df, as_of_date)
    if known.empty:
        raise ValueError("No verified MSP observations are available as of this date.")

    target = _as_period(target_period)
    _known_target_guard(known, target)
    prior, base = _prior_year_base(known, target)

    growth = known.dropna(subset=["yoy_change"]).sort_values("period")
    if growth.empty:
        raise ValueError("No known YoY growth observations are available.")

    latest_growth_row = growth.iloc[-1]
    latest_period = latest_growth_row["period"]
    horizon = _month_gap(target, latest_period)
    if horizon < 1:
        raise ValueError("Target must be after the latest known YoY observation.")

    alpha, phi, pairs = _fit_ar1_growth(known, min_pairs=min_pairs)

    growth_forecast = float(latest_growth_row["yoy_change"])
    for _ in range(horizon):
        growth_forecast = alpha + phi * growth_forecast

    forecast = base * (1.0 + growth_forecast)

    return NowcastResult(
        method="ar1_yoy",
        as_of_date=str(pd.Timestamp(as_of_date).date()),
        target_period=str(target),
        forecast_enplanements=float(forecast),
        prior_year_period=str(prior),
        prior_year_enplanements=base,
        latest_known_period=str(known["period"].max()),
        ar_alpha=alpha,
        ar_phi=phi,
        ar_pairs_used=pairs,
        forecast_horizon_months=horizon,
        forecast_yoy_growth=growth_forecast,
    )


def forecast_benchmarks(
    df,
    as_of_date,
    target_period,
    *,
    yoy_window: int = 3,
    ar_min_pairs: int = 4,
) -> pd.DataFrame:
    """Return all current point-in-time benchmark forecasts."""
    results = [
        seasonal_naive(df, as_of_date, target_period),
        yoy_trend(df, as_of_date, target_period, window=yoy_window),
        ar1_yoy(df, as_of_date, target_period, min_pairs=ar_min_pairs),
    ]
    return pd.DataFrame([result.to_dict() for result in results])


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
