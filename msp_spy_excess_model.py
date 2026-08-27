"""
Market-adjusted MSP -> DAL evaluation.

The dependent variable is DAL excess return versus SPY over matching trading
windows:

    excess_return_h = DAL_return_h - SPY_return_h

The feature set preserves the pre-specified MSP and WTI construction:
- traffic_z: exploratory pseudo-real-time MSP traffic z-score;
- wti_21d: trailing 21-observation WTI return known at signal date;
- interaction: traffic_z * wti_21d.

Evaluation uses expanding-window out-of-sample OLS. No feature window is tuned
to maximize DAL results.
"""

from __future__ import annotations
import numpy as np
import pandas as pd


def align_equity_prices(
    dal: pd.DataFrame,
    spy: pd.DataFrame,
    *,
    date_col: str = "date",
    adjusted_col: str = "adj_close",
) -> pd.DataFrame:
    d = dal[[date_col, adjusted_col]].rename(columns={adjusted_col: "dal_adj"})
    s = spy[[date_col, adjusted_col]].rename(columns={adjusted_col: "spy_adj"})
    out = d.merge(s, on=date_col, how="inner").sort_values(date_col).reset_index(drop=True)
    return out


def excess_forward_return(
    aligned: pd.DataFrame,
    signal_date,
    horizon: int,
) -> dict:
    future = aligned.index[aligned["date"] > pd.Timestamp(signal_date)]
    if len(future) == 0:
        return {"entry_date": pd.NaT, "dal_return": np.nan, "spy_return": np.nan, "excess_return": np.nan}

    i = int(future[0])
    j = i + horizon
    if j >= len(aligned):
        return {"entry_date": aligned.loc[i, "date"], "dal_return": np.nan, "spy_return": np.nan, "excess_return": np.nan}

    dal_ret = float(aligned.loc[j, "dal_adj"] / aligned.loc[i, "dal_adj"] - 1.0)
    spy_ret = float(aligned.loc[j, "spy_adj"] / aligned.loc[i, "spy_adj"] - 1.0)

    return {
        "entry_date": aligned.loc[i, "date"],
        "dal_return": dal_ret,
        "spy_return": spy_ret,
        "excess_return": dal_ret - spy_ret,
    }


def _fit_ols(train: pd.DataFrame, ycol: str, xcols: list[str]) -> np.ndarray:
    if not xcols:
        return np.array([float(train[ycol].mean())])
    d = train[[ycol] + xcols].dropna()
    X = np.column_stack([np.ones(len(d))] + [d[c].to_numpy(dtype=float) for c in xcols])
    y = d[ycol].to_numpy(dtype=float)
    return np.linalg.lstsq(X, y, rcond=None)[0]


def expanding_oos_excess(
    panel: pd.DataFrame,
    *,
    ycol: str,
    min_train: int = 36,
) -> pd.DataFrame:
    models = {
        "historical_mean": [],
        "traffic_only": ["traffic_z"],
        "traffic_plus_wti": ["traffic_z", "wti_21d"],
        "traffic_wti_interaction": ["traffic_z", "wti_21d", "interaction"],
    }

    data = panel.dropna(subset=["traffic_z", "wti_21d", "interaction", ycol]).reset_index(drop=True)
    rows = []

    for i in range(min_train, len(data)):
        train = data.iloc[:i]
        test = data.iloc[i]
        actual = float(test[ycol])

        for name, xcols in models.items():
            beta = _fit_ols(train, ycol, xcols)
            if xcols:
                x = np.array([1.0] + [float(test[c]) for c in xcols], dtype=float)
                pred = float(x @ beta)
            else:
                pred = float(beta[0])

            rows.append({
                "target_period": test.get("target_period", i),
                "model": name,
                "prediction": pred,
                "actual": actual,
            })

    out = pd.DataFrame(rows)
    out["error"] = out["prediction"] - out["actual"]
    out["absolute_error"] = out["error"].abs()
    out["squared_error"] = out["error"] ** 2
    out["sign_correct"] = np.sign(out["prediction"]) == np.sign(out["actual"])
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
