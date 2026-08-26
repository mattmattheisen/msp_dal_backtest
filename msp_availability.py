"""
Point-in-time availability controls for MSP enplanement data.

Core rule
---------
A historical simulation may use an MSP observation only when:

    release_date <= as_of_date

Rows with an unverified or missing release date are excluded by default.

This module is the temporal firewall between the canonical MSP dataset and
every forecasting/backtesting model. Historical models should never read the
full canonical dataset directly.
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import pandas as pd

DateLike = Union[str, pd.Timestamp]

REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_MSP_ACTUALS_PATH = REPO_ROOT / "data" / "msp_actual_canonical_2024_2026.csv"


def load_msp_actuals(
    path: Union[str, Path] = DEFAULT_MSP_ACTUALS_PATH,
) -> pd.DataFrame:
    """Load and validate the canonical MSP point-in-time dataset."""
    df = pd.read_csv(path)

    required = {
        "period",
        "enplanements",
        "release_date",
        "yoy_change",
        "source_url",
        "source_workbook",
        "series",
        "release_date_status",
    }
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    df = df.copy()
    df["period"] = pd.PeriodIndex(df["period"], freq="M")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["enplanements"] = pd.to_numeric(df["enplanements"], errors="raise")
    df["yoy_change"] = pd.to_numeric(df["yoy_change"], errors="coerce")

    if df["period"].duplicated().any():
        dups = df.loc[df["period"].duplicated(), "period"].astype(str).tolist()
        raise ValueError(f"Duplicate MSP periods found: {dups}")

    return df.sort_values("period").reset_index(drop=True)


def available_as_of(
    df: pd.DataFrame,
    as_of_date: DateLike,
    *,
    allow_unverified: bool = False,
) -> pd.DataFrame:
    """
    Return only MSP observations that were knowable as of ``as_of_date``.

    Release-day observations are available on the release date itself.

    ``allow_unverified`` exists only for diagnostics. It must remain False in
    point-in-time backtests because historical rows with unknown release dates
    are not provably tradable information.
    """
    as_of = pd.Timestamp(as_of_date).normalize()
    out = df.copy()

    verified = out["release_date"].notna() & (out["release_date"] <= as_of)

    if allow_unverified:
        period_end = out["period"].dt.to_timestamp(how="end").dt.normalize()
        unverified_historical = out["release_date"].isna() & (period_end <= as_of)
        mask = verified | unverified_historical
    else:
        mask = verified

    result = out.loc[mask].copy()
    result["available_as_of"] = as_of
    return result.sort_values("period").reset_index(drop=True)


def unavailable_as_of(df: pd.DataFrame, as_of_date: DateLike) -> pd.DataFrame:
    """Return observations that exist today but were not knowable then."""
    as_of = pd.Timestamp(as_of_date).normalize()
    mask = df["release_date"].isna() | (df["release_date"] > as_of)
    return df.loc[mask].sort_values("period").reset_index(drop=True)


def latest_known_period(df: pd.DataFrame, as_of_date: DateLike) -> pd.Period | None:
    """Return the latest MSP observation period knowable as of a date."""
    known = available_as_of(df, as_of_date)
    if known.empty:
        return None
    return known["period"].max()


def information_gap_months(df: pd.DataFrame, as_of_date: DateLike) -> int | None:
    """
    Return whole calendar months between the as-of month and the latest
    knowable MSP observation month.
    """
    latest = latest_known_period(df, as_of_date)
    if latest is None:
        return None

    as_of_period = pd.Timestamp(as_of_date).to_period("M")
    return (
        (as_of_period.year - latest.year) * 12
        + (as_of_period.month - latest.month)
    )


def point_in_time_snapshot(
    as_of_date: DateLike,
    path: Union[str, Path] = DEFAULT_MSP_ACTUALS_PATH,
) -> dict:
    """Return a compact point-in-time diagnostic snapshot."""
    df = load_msp_actuals(path)
    known = available_as_of(df, as_of_date)
    hidden = unavailable_as_of(df, as_of_date)
    latest = latest_known_period(df, as_of_date)

    return {
        "as_of_date": str(pd.Timestamp(as_of_date).date()),
        "known_observations": len(known),
        "latest_known_period": str(latest) if latest is not None else None,
        "information_gap_months": information_gap_months(df, as_of_date),
        "known_periods": known["period"].astype(str).tolist(),
        "hidden_periods": hidden["period"].astype(str).tolist(),
    }
