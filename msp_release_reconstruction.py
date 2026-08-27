"""
Historical MSP release-date reconstruction helpers.

The current MAC website exposes an `Updated` date for historical monthly
operations reports. Those timestamps are useful evidence, but many older years
show obvious bulk-refresh/migration behavior (for example, nearly every 2024
monthly report currently shows 2025-01-24).

This module therefore keeps `site_updated_date` separate from `release_date`.
No historical date is promoted into the point-in-time backtest merely because
it appears as an Updated timestamp on today's website.

Confidence/status vocabulary
----------------------------
verified_original
    Independent evidence supports the original publication/release date.

plausible_candidate
    The site timestamp has a realistic reporting lag and is not obviously a
    bulk refresh. It is still NOT backtest-eligible without verification.

bulk_refresh
    The same site timestamp is shared by many months and/or occurs far too
    late to represent a normal monthly publication cadence.

unresolved
    Insufficient evidence.
"""

from __future__ import annotations

import pandas as pd


MIN_NORMAL_LAG_DAYS = 15
MAX_NORMAL_LAG_DAYS = 75
BULK_SHARED_DATE_THRESHOLD = 3


def period_end(period) -> pd.Timestamp:
    """Return normalized calendar month-end for a YYYY-MM period."""
    p = period if isinstance(period, pd.Period) else pd.Period(period, freq="M")
    return p.to_timestamp(how="end").normalize()


def release_lag_days(period, candidate_date) -> int:
    """Calendar days from observation month-end to a candidate release date."""
    return int((pd.Timestamp(candidate_date).normalize() - period_end(period)).days)


def classify_site_update_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Classify current-site historical `Updated` timestamps without promoting
    them to verified release dates.

    Expected columns: period, site_updated_date.
    """
    required = {"period", "site_updated_date"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    out = df.copy()
    out["period"] = pd.PeriodIndex(out["period"], freq="M")
    out["site_updated_date"] = pd.to_datetime(out["site_updated_date"], errors="coerce")

    counts = out["site_updated_date"].value_counts(dropna=True)
    out["shared_timestamp_count"] = out["site_updated_date"].map(counts).fillna(0).astype(int)
    out["candidate_lag_days"] = [
        release_lag_days(p, d) if pd.notna(d) else pd.NA
        for p, d in zip(out["period"], out["site_updated_date"])
    ]

    statuses = []
    for _, row in out.iterrows():
        date = row["site_updated_date"]
        lag = row["candidate_lag_days"]
        shared = row["shared_timestamp_count"]

        if pd.isna(date):
            statuses.append("unresolved")
        elif shared >= BULK_SHARED_DATE_THRESHOLD:
            statuses.append("bulk_refresh")
        elif MIN_NORMAL_LAG_DAYS <= lag <= MAX_NORMAL_LAG_DAYS:
            statuses.append("plausible_candidate")
        else:
            statuses.append("unresolved")

    out["reconstruction_status"] = statuses
    out["backtest_eligible"] = False
    out["release_date"] = pd.NaT
    return out.sort_values("period").reset_index(drop=True)


def promote_verified_release_date(
    df: pd.DataFrame,
    period,
    verified_date,
    *,
    evidence_source: str,
) -> pd.DataFrame:
    """
    Promote one reconstructed date only after independent evidence is found.
    """
    if not evidence_source or not evidence_source.strip():
        raise ValueError("evidence_source is required for verification")

    out = df.copy()
    target = period if isinstance(period, pd.Period) else pd.Period(period, freq="M")
    mask = out["period"] == target
    if mask.sum() != 1:
        raise ValueError(f"Expected exactly one row for {target}; found {int(mask.sum())}")

    verified = pd.Timestamp(verified_date).normalize()
    if verified <= period_end(target):
        raise ValueError("verified release date must be after the observation month ends")

    out.loc[mask, "release_date"] = verified
    out.loc[mask, "reconstruction_status"] = "verified_original"
    out.loc[mask, "backtest_eligible"] = True
    out.loc[mask, "evidence_source"] = evidence_source
    return out
