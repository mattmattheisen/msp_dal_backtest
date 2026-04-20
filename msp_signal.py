# src/signal.py
"""
Signal construction for the MSP passenger momentum strategy.

Signal logic:
    momentum[t] = (pax[t] - pax[t - lookback]) / pax[t - lookback]
    long_signal[t] = 1 if momentum[t - lag] > threshold else 0

The lag parameter tests whether the MSP passenger series leads DAL price.
Positive lag = pax leads DAL (the predictive hypothesis).
Negative lag = pax lags DAL (confirmatory, not predictive).
"""

import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
import config


def compute_momentum(pax: pd.Series, lookback: int) -> pd.Series:
    """
    Compute month-over-month (or N-month) pax momentum.

    Returns percentage change series aligned to the same index as pax.
    First `lookback` values will be NaN.
    """
    return pax.pct_change(periods=lookback)


def compute_signal(df: pd.DataFrame,
                   lag: int = None,
                   lookback: int = None,
                   threshold: float = None) -> pd.DataFrame:
    """
    Add momentum and long/cash signal columns to the aligned DataFrame.

    Parameters
    ----------
    df : DataFrame with columns [year_month, passengers_adj, close]
    lag : int, months pax signal leads DAL entry (default: config.LAG_MONTHS)
    lookback : int, momentum lookback window (default: config.LOOKBACK_MONTHS)
    threshold : float, minimum momentum to go long (default: config.SIGNAL_THRESHOLD)

    Returns
    -------
    DataFrame with additional columns:
        momentum       raw pax momentum at time t
        signal_raw     momentum shifted forward by lag months (what we know at trade time)
        position       1 = long DAL, 0 = cash
    """
    lag       = lag       if lag       is not None else config.LAG_MONTHS
    lookback  = lookback  if lookback  is not None else config.LOOKBACK_MONTHS
    threshold = threshold if threshold is not None else config.SIGNAL_THRESHOLD

    df = df.copy()

    # Momentum at each month
    df["momentum"] = compute_momentum(df["passengers_adj"], lookback)

    # Shift forward by lag: signal_raw[t] = momentum[t - lag]
    # Positive lag means we are using older (leading) pax data to enter DAL today
    df["signal_raw"] = df["momentum"].shift(lag)

    # Long if signal exceeds threshold, else cash
    df["position"] = (df["signal_raw"] > threshold).astype(int)

    # Drop rows where we don't yet have a valid signal
    df = df.dropna(subset=["signal_raw"]).reset_index(drop=True)

    return df


def lag_correlation_table(df: pd.DataFrame,
                           max_lag: int = 6,
                           min_lag: int = -3) -> pd.DataFrame:
    """
    Compute Pearson correlation between MSP pax and DAL close at each lag.

    Positive lag = pax leads DAL by N months.
    Negative lag = DAL leads pax by N months.

    Returns a DataFrame with columns: lag, r, p_value, n_obs
    """
    pax = df["passengers_adj"].values
    dal = df["close"].values
    results = []

    for lag in range(min_lag, max_lag + 1):
        if lag >= 0:
            a = pax[lag:]
            b = dal[:len(dal) - lag] if lag > 0 else dal
        else:
            a = pax[:len(pax) + lag]
            b = dal[-lag:]

        n = min(len(a), len(b))
        a, b = a[:n], b[:n]

        if n < 10:
            continue

        r, p = stats.pearsonr(a, b)
        results.append({"lag": lag, "r": round(r, 4), "p_value": round(p, 4), "n_obs": n})

    return pd.DataFrame(results)


def best_lag(lag_table: pd.DataFrame) -> dict:
    """Return the lag row with the highest absolute correlation."""
    idx = lag_table["r"].abs().idxmax()
    return lag_table.loc[idx].to_dict()


if __name__ == "__main__":
    # Quick smoke test
    from data_loader import load_aligned_data
    df = load_aligned_data()
    df_sig = compute_signal(df)

    print("\nSignal sample:")
    print(df_sig[["year_month", "passengers_adj", "momentum", "signal_raw", "position"]].tail(12).to_string())

    print("\nLag correlation table:")
    lt = lag_correlation_table(df)
    print(lt.to_string())
    print(f"\nBest lag: {best_lag(lt)}")
