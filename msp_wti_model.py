"""
WTI-controlled evaluation for the MSP -> DAL hypothesis.

Pre-specified energy control:
    trailing 21-observation WTI spot-price return known at signal date.

Nested models:
    1. traffic_only
    2. traffic_plus_wti
    3. traffic_wti_interaction

The historical traffic panel uses the existing exploratory pseudo-real-time
assumption: fixed two-month MSP reporting lag and exclusion of 2020-2022
structural-break years. It is not a strict tradable backtest until older MAC
release dates are fully reconstructed.

Model evaluation uses an expanding-window out-of-sample design. No oil
lookback/window is selected based on DAL performance.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def trailing_return(series: pd.Series, lookback: int = 21) -> float:
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s) < lookback + 1:
        return np.nan
    return float(s.iloc[-1] / s.iloc[-1-lookback] - 1.0)


def fit_ols(train: pd.DataFrame, ycol: str, xcols: list[str]) -> np.ndarray:
    d = train[[ycol] + xcols].dropna()
    if len(d) <= len(xcols):
        raise ValueError("Insufficient observations to fit model.")
    X = np.column_stack(
        [np.ones(len(d))] + [d[c].to_numpy(dtype=float) for c in xcols]
    )
    y = d[ycol].to_numpy(dtype=float)
    return np.linalg.lstsq(X, y, rcond=None)[0]


def predict_ols(row: pd.Series, beta: np.ndarray, xcols: list[str]) -> float:
    x = np.array([1.0] + [float(row[c]) for c in xcols], dtype=float)
    return float(x @ beta)


def expanding_oos(
    panel: pd.DataFrame,
    *,
    ycol: str,
    min_train: int = 36,
) -> pd.DataFrame:
    """
    Compare nested MSP/WTI models using expanding-window one-step forecasts.
    """
    data = panel.dropna(
        subset=["traffic_z", "wti_21d", "interaction", ycol]
    ).reset_index(drop=True)

    models = {
        "traffic_only": ["traffic_z"],
        "traffic_plus_wti": ["traffic_z", "wti_21d"],
        "traffic_wti_interaction": ["traffic_z", "wti_21d", "interaction"],
    }

    rows = []
    for i in range(min_train, len(data)):
        train = data.iloc[:i]
        test = data.iloc[i]
        actual = float(test[ycol])

        rows.append({
            "target_period": test.get("target_period", i),
            "model": "historical_mean",
            "prediction": float(train[ycol].mean()),
            "actual": actual,
        })

        for name, xcols in models.items():
            beta = fit_ols(train, ycol, xcols)
            rows.append({
                "target_period": test.get("target_period", i),
                "model": name,
                "prediction": predict_ols(test, beta, xcols),
                "actual": actual,
            })

    out = pd.DataFrame(rows)
    out["error"] = out["prediction"] - out["actual"]
    out["absolute_error"] = out["error"].abs()
    out["squared_error"] = out["error"] ** 2
    out["sign_correct"] = (
        np.sign(out["prediction"]) == np.sign(out["actual"])
    )
    return out


def summarize_oos(results: pd.DataFrame) -> pd.DataFrame:
    return (
        results.groupby("model")
        .agg(
            n=("actual", "size"),
            mae=("absolute_error", "mean"),
            rmse=("squared_error", lambda s: float(np.sqrt(s.mean()))),
            bias=("error", "mean"),
            sign_accuracy=("sign_correct", "mean"),
        )
        .reset_index()
        .sort_values("rmse")
        .reset_index(drop=True)
    )
