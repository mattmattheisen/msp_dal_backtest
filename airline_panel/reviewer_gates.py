"""Reviewer-driven falsification gates for Capacity as Information.

Gate 16: membership persistence / effective portfolio-state breadth.
Gate 17: carrier-distress confound conditioning and leave-one-carrier-out robustness.

These are secondary diagnostics. They do not modify the frozen primary capacity rule.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

CARRIER_TO_TICKER = {"DL": "DAL", "UA": "UAL", "AA": "AAL", "WN": "LUV", "AS": "ALK", "B6": "JBLU"}
DEFAULT_TICKERS = tuple(CARRIER_TO_TICKER.values())


@dataclass(frozen=True)
class Gate16Result:
    monthly_states: pd.DataFrame
    summary: pd.DataFrame
    carrier_membership: pd.DataFrame
    state_frequency: pd.DataFrame


def _normalize_panel(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()
    if "ticker" not in df.columns:
        if "carrier" not in df.columns:
            raise ValueError("panel must contain ticker or carrier")
        df["ticker"] = df["carrier"].map(CARRIER_TO_TICKER).fillna(df["carrier"])
    date_col = "signal_period" if "signal_period" in df.columns else "date"
    if date_col not in df.columns:
        raise ValueError("panel must contain signal_period or date")
    df["signal_period"] = pd.PeriodIndex(pd.to_datetime(df[date_col]), freq="M")
    if "carrier_capacity_yoy" not in df.columns:
        if "capacity_yoy" in df.columns:
            df["carrier_capacity_yoy"] = df["capacity_yoy"]
        else:
            raise ValueError("panel must contain carrier_capacity_yoy or capacity_yoy")
    return df


def gate16_membership_persistence(
    panel: pd.DataFrame,
    *,
    tickers: Sequence[str] = DEFAULT_TICKERS,
    min_names: int = 6,
) -> Gate16Result:
    """Measure whether top-2/bottom-2 ranks are one sticky pair trade or rotating states."""
    df = _normalize_panel(panel)
    df = df[df["ticker"].isin(tickers)].dropna(subset=["carrier_capacity_yoy"]).copy()

    rows = []
    for period, g in df.groupby("signal_period"):
        g = g.drop_duplicates("ticker").sort_values("carrier_capacity_yoy")
        if g["ticker"].nunique() < min_names:
            continue
        slow = tuple(sorted(g.head(2)["ticker"].tolist()))
        fast = tuple(sorted(g.tail(2)["ticker"].tolist()))
        middle = tuple(sorted(set(g["ticker"]) - set(slow) - set(fast)))
        rows.append({"signal_period": period, "fast": fast, "slow": slow, "middle": middle,
                     "state": f"L:{'+'.join(fast)}|S:{'+'.join(slow)}"})

    states = pd.DataFrame(rows).sort_values("signal_period").reset_index(drop=True)
    if states.empty:
        raise ValueError("No complete six-carrier months available for Gate 16")

    for side in ("fast", "slow"):
        states[f"{side}_same_prev"] = states[side].eq(states[side].shift(1))
        states[f"{side}_overlap_prev"] = [
            np.nan if i == 0 else len(set(states.at[i, side]) & set(states.at[i - 1, side])) / 2
            for i in range(len(states))
        ]
    states["state_same_prev"] = states["state"].eq(states["state"].shift(1))

    # Consecutive run length of identical full long-short state.
    grp = states["state"].ne(states["state"].shift()).cumsum()
    run_lengths = states.groupby(grp).size()

    all_states = [f"L:{'+'.join(f)}|S:{'+'.join(s)}"
                  for f in combinations(sorted(tickers), 2)
                  for s in combinations(sorted(set(tickers) - set(f)), 2)]
    state_counts = states["state"].value_counts().rename_axis("state").reset_index(name="months")
    state_counts["share"] = state_counts["months"] / len(states)

    membership_rows = []
    for ticker in tickers:
        fast_n = states["fast"].apply(lambda x: ticker in x).sum()
        slow_n = states["slow"].apply(lambda x: ticker in x).sum()
        membership_rows.append({"ticker": ticker, "fast_months": int(fast_n), "slow_months": int(slow_n),
                                "fast_share": fast_n / len(states), "slow_share": slow_n / len(states)})
    membership = pd.DataFrame(membership_rows)

    p = state_counts["share"].to_numpy()
    effective_states_hhi = 1.0 / np.square(p).sum()
    summary = pd.DataFrame([{
        "months": len(states),
        "unique_states_observed": states["state"].nunique(),
        "possible_ordered_states": len(all_states),
        "state_coverage": states["state"].nunique() / len(all_states),
        "full_state_month_to_month_change_rate": 1 - states["state_same_prev"].iloc[1:].mean(),
        "fast_pair_change_rate": 1 - states["fast_same_prev"].iloc[1:].mean(),
        "slow_pair_change_rate": 1 - states["slow_same_prev"].iloc[1:].mean(),
        "mean_fast_overlap_prev": states["fast_overlap_prev"].iloc[1:].mean(),
        "mean_slow_overlap_prev": states["slow_overlap_prev"].iloc[1:].mean(),
        "median_identical_state_run_months": float(run_lengths.median()),
        "max_identical_state_run_months": int(run_lengths.max()),
        "largest_single_state_share": float(state_counts["share"].max()),
        "effective_state_count_hhi": float(effective_states_hhi),
    }])
    return Gate16Result(states, summary, membership, state_counts)


def gate17_distress_confound(
    observations: pd.DataFrame,
    *,
    distress_cols: Iterable[str],
    return_col: str = "ret_6m",
    capacity_col: str = "carrier_capacity_yoy",
    momentum_col: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Condition the capacity-return relation on explicit, pre-specified distress measures.

    Required input is one row per carrier/signal month with the forward six-month return.
    Distress variables must be defined outside this function from point-in-time information.
    The function intentionally refuses to synthesize a distress score from undocumented inputs.

    Outputs:
      1) pooled OLS-style coefficient table using month-demeaned variables;
      2) leave-one-carrier-out coefficient table to detect dependence on a single airline.
    """
    distress_cols = list(distress_cols)
    missing = {return_col, capacity_col, "ticker", "signal_period", *distress_cols} - set(observations.columns)
    if momentum_col:
        missing -= {momentum_col} if momentum_col in observations.columns else set()
        if momentum_col not in observations.columns:
            missing.add(momentum_col)
    if missing:
        raise ValueError(f"Gate 17 missing required columns: {sorted(missing)}")

    df = observations.copy()
    df["signal_period"] = pd.PeriodIndex(df["signal_period"], freq="M")
    cols = [return_col, capacity_col, *distress_cols] + ([momentum_col] if momentum_col else [])
    df = df.dropna(subset=cols + ["ticker", "signal_period"]).copy()

    def fit(d: pd.DataFrame) -> dict:
        # Month demeaning removes common airline-industry shocks without adding dozens of dummies.
        z = d.copy()
        for c in cols:
            z[c] = z[c] - z.groupby("signal_period")[c].transform("mean")
        xcols = [capacity_col, *distress_cols] + ([momentum_col] if momentum_col else [])
        X = z[xcols].to_numpy(float)
        y = z[return_col].to_numpy(float)
        X = np.column_stack([np.ones(len(X)), X])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        resid = y - X @ beta
        dof = max(len(y) - X.shape[1], 1)
        s2 = float(resid @ resid / dof)
        cov = s2 * np.linalg.pinv(X.T @ X)
        se = np.sqrt(np.diag(cov))
        names = ["intercept", *xcols]
        out = {"n": len(y), "r2": 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean())) if len(y) > 1 else np.nan}
        for name, b, s in zip(names, beta, se):
            out[f"coef_{name}"] = b
            out[f"t_{name}"] = b / s if s > 0 else np.nan
        return out

    pooled = pd.DataFrame([fit(df)])
    loo = []
    for ticker in sorted(df["ticker"].unique()):
        r = fit(df[df["ticker"] != ticker])
        r["excluded_ticker"] = ticker
        loo.append(r)
    return pooled, pd.DataFrame(loo)
