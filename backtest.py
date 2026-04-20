# src/data_loader.py
"""
Data acquisition layer.

Two modes:
  USE_LIVE_DATA = False  →  load from data/msp_passengers.csv + data/dal_prices.csv
  USE_LIVE_DATA = True   →  fetch DAL from Tiingo API; MSP pax must still be loaded from CSV
                             (MAC does not offer a machine-readable API; data must be manually
                              downloaded from metroairports.org/msp-passenger-and-operations-reports)
"""

import os
import requests
import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

DATA_DIR = Path(__file__).parent.parent / "data"


# ── MSP passenger data ─────────────────────────────────────────────────────────

def load_msp_passengers() -> pd.DataFrame:
    """
    Load MSP monthly enplanement data.

    Expected CSV columns: year_month (YYYY-MM), passengers (integer)

    Source: Metropolitan Airports Commission monthly operations reports
    https://metroairports.org/msp-passenger-and-operations-reports
    """
    path = DATA_DIR / "msp_passengers.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"MSP passenger data not found at {path}.\n"
            "Download from: https://metroairports.org/msp-passenger-and-operations-reports\n"
            "Format: year_month,passengers (e.g. 2015-01,2600000)"
        )

    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()

    if "year_month" not in df.columns or "passengers" not in df.columns:
        raise ValueError("msp_passengers.csv must have columns: year_month, passengers")

    df["year_month"] = pd.to_datetime(df["year_month"], format="%Y-%m")
    df = df.sort_values("year_month").reset_index(drop=True)
    df["passengers"] = df["passengers"].astype(float)
    return df


def apply_seasonal_adjustment(df: pd.DataFrame) -> pd.DataFrame:
    """Divide raw pax by monthly seasonal index. Returns adjusted copy."""
    df = df.copy()
    df["passengers_adj"] = df.apply(
        lambda r: r["passengers"] / config.SEASONAL_INDEX[r["year_month"].month],
        axis=1
    )
    return df


# ── DAL price data ─────────────────────────────────────────────────────────────

def load_dal_prices() -> pd.DataFrame:
    """
    Load DAL monthly close prices.

    If USE_LIVE_DATA=True, fetches from Tiingo API and requires TIINGO_API_KEY in .env.
    Otherwise loads from data/dal_prices.csv.

    CSV columns: year_month (YYYY-MM), close (float)
    """
    if config.USE_LIVE_DATA:
        return _fetch_dal_tiingo()
    else:
        return _load_dal_csv()


def _load_dal_csv() -> pd.DataFrame:
    path = DATA_DIR / "dal_prices.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"DAL price data not found at {path}.\n"
            "Set USE_LIVE_DATA=True in config.py to fetch from Tiingo,\n"
            "or download historical prices and save as data/dal_prices.csv"
        )
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip().str.lower()
    df["year_month"] = pd.to_datetime(df["year_month"], format="%Y-%m")
    df = df.sort_values("year_month").reset_index(drop=True)
    df["close"] = df["close"].astype(float)
    return df


def _fetch_dal_tiingo() -> pd.DataFrame:
    """Fetch DAL monthly close prices from Tiingo API."""
    if not config.TIINGO_API_KEY:
        raise EnvironmentError(
            "TIINGO_API_KEY not set. Add it to your .env file.\n"
            "Get a free key at https://www.tiingo.com"
        )

    url = (
        f"https://api.tiingo.com/tiingo/daily/{config.DAL_TICKER}/prices"
        f"?startDate={config.START_DATE}&endDate={config.END_DATE}"
        f"&resampleFreq=monthly&token={config.TIINGO_API_KEY}"
    )

    resp = requests.get(url, headers={"Content-Type": "application/json"})
    resp.raise_for_status()
    raw = resp.json()

    df = pd.DataFrame(raw)[["date", "adjClose"]]
    df.columns = ["year_month", "close"]
    df["year_month"] = pd.to_datetime(df["year_month"]).dt.to_period("M").dt.to_timestamp()
    df = df.sort_values("year_month").reset_index(drop=True)
    df["close"] = df["close"].astype(float)

    # Cache to CSV for offline use
    out = DATA_DIR / "dal_prices.csv"
    df_save = df.copy()
    df_save["year_month"] = df_save["year_month"].dt.strftime("%Y-%m")
    df_save.to_csv(out, index=False)
    if config.VERBOSE:
        print(f"DAL prices saved to {out}")

    return df


# ── Merge + filter ─────────────────────────────────────────────────────────────

def load_aligned_data() -> pd.DataFrame:
    """
    Load, align, and optionally filter MSP pax + DAL price data.
    Returns a merged DataFrame indexed by year_month with columns:
        passengers, passengers_adj, close
    """
    msp = load_msp_passengers()
    dal = load_dal_prices()

    if config.SEASONAL_ADJUST:
        msp = apply_seasonal_adjustment(msp)
    else:
        msp["passengers_adj"] = msp["passengers"]

    df = pd.merge(msp, dal, on="year_month", how="inner")
    df = df.sort_values("year_month").reset_index(drop=True)

    # Apply COVID exclusion
    if config.EXCLUDE_COVID:
        covid_start = pd.to_datetime(config.COVID_START, format="%Y-%m")
        covid_end   = pd.to_datetime(config.COVID_END,   format="%Y-%m")
        mask = (df["year_month"] >= covid_start) & (df["year_month"] <= covid_end)
        n_excluded = mask.sum()
        df = df[~mask].reset_index(drop=True)
        if config.VERBOSE:
            print(f"COVID exclusion: {n_excluded} months removed ({config.COVID_START} – {config.COVID_END})")

    if config.VERBOSE:
        print(f"Aligned dataset: {len(df)} months ({df['year_month'].min().strftime('%Y-%m')} – {df['year_month'].max().strftime('%Y-%m')})")

    return df


if __name__ == "__main__":
    df = load_aligned_data()
    print(df.head(10).to_string())
