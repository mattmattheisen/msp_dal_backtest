"""
Walk-forward evaluation for MSP point-in-time nowcast benchmarks.

Each target month is forecast using a snapshot taken one calendar day before
its verified MAC release date. This asks a clean question:

    "Immediately before the actual observation became public, what would our
    benchmark models have forecast using only information already released?"

The evaluator never supplies the unreleased target observation to the models.
The actual value is joined only after forecasts have been generated.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from msp_nowcast import forecast_benchmarks


REQUIRED_COLUMNS = {"period", "enplanements", "release_date"}


def evaluation_as_of(release_date) -> pd.Timestamp:
    """Information cutoff: the calendar day before MAC release."""
    release = pd.Timestamp(release_date).normalize()
    return release - pd.Timedelta(days=1)


def eligible_targets(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return observations eligible for strict walk-forward scoring.

    A target must have:
    - a verified release date;
    - a prior-year observation in the canonical dataset;
    - a verified release date for that prior-year observation.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    rows = []
    periods = set(df["period"])

    for _, row in df.iterrows():
        target = row["period"]
        if pd.isna(row["release_date"]):
            continue

        prior = target - 12
        if prior not in periods:
            continue

        prior_row = df.loc[df["period"] == prior].iloc[-1]
        if pd.isna(prior_row["release_date"]):
            continue

        rows.append(row)

    if not rows:
        return df.iloc[0:0].copy()

    return pd.DataFrame(rows).sort_values("period").reset_index(drop=True)


def walk_forward_evaluate(
    df: pd.DataFrame,
    *,
    yoy_window: int = 3,
) -> pd.DataFrame:
    """
    Generate and score benchmark forecasts for every eligible target month.

    The full canonical DataFrame is used only to locate eventual actuals and
    verified release dates. Forecast functions receive an as-of date and apply
    the temporal firewall internally.
    """
    targets = eligible_targets(df)
    scored_rows = []

    for _, target_row in targets.iterrows():
        target = target_row["period"]
        release_date = pd.Timestamp(target_row["release_date"]).normalize()
        as_of = evaluation_as_of(release_date)
        actual = float(target_row["enplanements"])

        forecasts = forecast_benchmarks(
            df,
            as_of,
            target,
            yoy_window=yoy_window,
        )

        for _, forecast_row in forecasts.iterrows():
            forecast = float(forecast_row["forecast_enplanements"])
            error = forecast - actual
            absolute_error = abs(error)
            ape = absolute_error / actual if actual else np.nan

            scored_rows.append({
                "target_period": str(target),
                "release_date": release_date,
                "as_of_date": as_of,
                "method": forecast_row["method"],
                "forecast_enplanements": forecast,
                "actual_enplanements": actual,
                "error": error,
                "absolute_error": absolute_error,
                "absolute_percentage_error": ape,
                "latest_known_period": forecast_row["latest_known_period"],
                "prior_year_period": forecast_row["prior_year_period"],
                "prior_year_enplanements": forecast_row["prior_year_enplanements"],
                "recent_yoy_mean": forecast_row.get("recent_yoy_mean", np.nan),
                "yoy_window_used": forecast_row.get("yoy_window_used", np.nan),
            })

    if not scored_rows:
        return pd.DataFrame()

    return pd.DataFrame(scored_rows).sort_values(
        ["target_period", "method"]
    ).reset_index(drop=True)


def summarize_walk_forward(results: pd.DataFrame) -> pd.DataFrame:
    """Aggregate out-of-sample forecast accuracy by method."""
    if results.empty:
        return pd.DataFrame(
            columns=["method", "n", "mae", "mape", "rmse", "bias"]
        )

    summaries = []
    for method, group in results.groupby("method", sort=True):
        errors = group["error"].astype(float)
        summaries.append({
            "method": method,
            "n": len(group),
            "mae": float(group["absolute_error"].mean()),
            "mape": float(group["absolute_percentage_error"].mean()),
            "rmse": float(np.sqrt(np.mean(np.square(errors)))),
            "bias": float(errors.mean()),
        })

    out = pd.DataFrame(summaries)
    return out.sort_values(["mape", "mae"]).reset_index(drop=True)


def model_hurdle(results: pd.DataFrame) -> dict:
    """
    Return the current benchmark to beat.

    Lower MAPE wins; MAE is the tie-breaker.
    """
    summary = summarize_walk_forward(results)
    if summary.empty:
        raise ValueError("No walk-forward results to summarize.")

    winner = summary.iloc[0]
    return {
        "method": winner["method"],
        "n": int(winner["n"]),
        "mae": float(winner["mae"]),
        "mape": float(winner["mape"]),
        "rmse": float(winner["rmse"]),
        "bias": float(winner["bias"]),
    }
