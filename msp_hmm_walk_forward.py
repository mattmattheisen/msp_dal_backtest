"""Strict walk-forward evaluation for the experimental MSP HMM regime model."""

from __future__ import annotations

import numpy as np
import pandas as pd

from msp_hmm import hmm_regime_nowcast
from msp_walk_forward import eligible_targets, evaluation_as_of


def walk_forward_evaluate_hmm(
    df: pd.DataFrame,
    *,
    min_observations: int = 8,
    max_iter: int = 200,
    tol: float = 1e-8,
) -> pd.DataFrame:
    """Score HMM forecasts one day before each verified MAC release."""
    rows = []

    for _, target_row in eligible_targets(df).iterrows():
        target = target_row["period"]
        release_date = pd.Timestamp(target_row["release_date"]).normalize()
        as_of = evaluation_as_of(release_date)
        actual = float(target_row["enplanements"])

        result = hmm_regime_nowcast(
            df,
            as_of,
            target,
            min_observations=min_observations,
            max_iter=max_iter,
            tol=tol,
        )

        error = result.forecast_enplanements - actual
        rows.append({
            "target_period": str(target),
            "release_date": release_date,
            "as_of_date": as_of,
            "method": result.method,
            "forecast_enplanements": result.forecast_enplanements,
            "actual_enplanements": actual,
            "error": error,
            "absolute_error": abs(error),
            "absolute_percentage_error": abs(error) / actual if actual else np.nan,
            "latest_known_period": result.latest_known_period,
            "forecast_horizon_months": result.forecast_horizon_months,
            "forecast_yoy_growth": result.forecast_yoy_growth,
            "weak_state_mean": result.weak_state_mean,
            "strong_state_mean": result.strong_state_mean,
            "weak_state_probability": result.weak_state_probability,
            "strong_state_probability": result.strong_state_probability,
            "training_observations": result.training_observations,
            "converged": result.converged,
        })

    return pd.DataFrame(rows).sort_values("target_period").reset_index(drop=True)


def summarize_hmm(results: pd.DataFrame) -> dict:
    """Return standard forecast metrics for HMM walk-forward results."""
    if results.empty:
        raise ValueError("No HMM walk-forward results to summarize.")

    errors = results["error"].astype(float)
    return {
        "method": "hmm_regime",
        "n": int(len(results)),
        "mae": float(results["absolute_error"].mean()),
        "mape": float(results["absolute_percentage_error"].mean()),
        "rmse": float(np.sqrt(np.mean(np.square(errors)))),
        "bias": float(errors.mean()),
    }
