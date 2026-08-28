"""BTS T1 ingestion and demand/capacity panel construction.

Expected input is a TranStats export from:
T1: U.S. Air Carrier Traffic And Capacity Summary by Service Class.

Minimum requested fields:
    Year, Month, UniqueCarrier, ServiceClass,
    RevPaxMiles, RevPaxEnplaned, AvailSeatMiles

The loader is intentionally file-based. TranStats download URLs are session/form driven,
so the reproducible workflow is: download a raw CSV snapshot, save it unchanged, record
its BTS release/publication date, and build the research panel from that snapshot.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


DEFAULT_UNIVERSE = ("DL", "UA", "AA", "WN", "AS", "B6")

# T1 service class F is scheduled passenger/cargo service. Do not sum aggregate
# service classes (for example K/Z) together with their component classes.
DEFAULT_SERVICE_CLASSES = ("F",)


@dataclass(frozen=True)
class T1Snapshot:
    """Metadata attached to one immutable BTS download."""

    path: Path
    release_date: pd.Timestamp


_COLUMN_ALIASES: Mapping[str, str] = {
    "year": "year",
    "month": "month",
    "uniquecarrier": "carrier",
    "unique_carrier": "carrier",
    "serviceclass": "service_class",
    "service_class": "service_class",
    "revpaxmiles": "rpm",
    "rev_pax_miles": "rpm",
    "revpaxenplaned": "pax",
    "rev_pax_enplaned": "pax",
    "availseatmiles": "asm",
    "avail_seat_miles": "asm",
}


def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    normalized = {
        c: str(c).strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        for c in out.columns
    }
    rename = {}
    compact_aliases = {k.replace("_", ""): v for k, v in _COLUMN_ALIASES.items()}
    for original, compact in normalized.items():
        if compact in compact_aliases:
            rename[original] = compact_aliases[compact]
    return out.rename(columns=rename)


def load_t1_csv(
    path: str | Path,
    *,
    service_classes: Iterable[str] = DEFAULT_SERVICE_CLASSES,
) -> pd.DataFrame:
    """Load and normalize one raw BTS T1 CSV export.

    Returns carrier/month observations aggregated across carrier reporting regions,
    while retaining only the requested non-overlapping service class(es).
    """
    df = pd.read_csv(path)
    df = _canonicalize_columns(df)

    required = {"year", "month", "carrier", "service_class", "rpm", "pax", "asm"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"T1 file is missing required fields: {sorted(missing)}")

    df["carrier"] = df["carrier"].astype(str).str.strip().str.upper()
    df["service_class"] = df["service_class"].astype(str).str.strip().str.upper()
    allowed = {str(x).upper() for x in service_classes}
    df = df[df["service_class"].isin(allowed)].copy()

    for c in ("year", "month", "rpm", "pax", "asm"):
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["year", "month", "carrier"])
    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)
    df["date"] = pd.to_datetime(
        {"year": df["year"], "month": df["month"], "day": 1}
    )

    # T1 can contain several carrier entities/regions for the same certificate.
    # Summing the primitive traffic/capacity measures produces a carrier-month total.
    result = (
        df.groupby(["date", "carrier"], as_index=False)[["rpm", "pax", "asm"]]
        .sum(min_count=1)
        .sort_values(["date", "carrier"])
        .reset_index(drop=True)
    )
    return result


def build_demand_capacity_panel(
    t1: pd.DataFrame,
    *,
    universe: Iterable[str] = DEFAULT_UNIVERSE,
    min_industry_carriers: int = 3,
) -> pd.DataFrame:
    """Create the Phase-1 monthly airline panel.

    Definitions fixed before looking at returns:
      industry_demand_yoy = YoY growth in aggregate RPM across the full T1 input
      carrier_capacity_yoy = YoY growth in each carrier's ASM
      dc_gap = industry_demand_yoy - carrier_capacity_yoy

    Industry demand deliberately uses all carriers present in the supplied T1 snapshot,
    not only the six-stock research universe.
    """
    df = t1.copy().sort_values(["carrier", "date"])

    industry = (
        df.groupby("date", as_index=False)
        .agg(industry_rpm=("rpm", "sum"), industry_carriers=("carrier", "nunique"))
        .sort_values("date")
    )
    industry["industry_demand_yoy"] = industry["industry_rpm"].pct_change(12)
    industry.loc[industry["industry_carriers"] < min_industry_carriers, "industry_demand_yoy"] = np.nan

    wanted = {str(x).upper() for x in universe}
    carriers = df[df["carrier"].isin(wanted)].copy()
    carriers["carrier_capacity_yoy"] = carriers.groupby("carrier")["asm"].pct_change(12)
    carriers["carrier_rpm_yoy"] = carriers.groupby("carrier")["rpm"].pct_change(12)
    carriers["carrier_pax_yoy"] = carriers.groupby("carrier")["pax"].pct_change(12)

    panel = carriers.merge(
        industry[["date", "industry_rpm", "industry_demand_yoy"]],
        on="date",
        how="left",
        validate="many_to_one",
    )
    panel["dc_gap"] = panel["industry_demand_yoy"] - panel["carrier_capacity_yoy"]
    panel = panel.sort_values(["date", "carrier"]).reset_index(drop=True)
    return panel


def apply_publication_lag(
    panel: pd.DataFrame,
    *,
    release_lag_days: int = 75,
) -> pd.DataFrame:
    """Attach a conservative first-pass availability date.

    BTS states T-100 traffic is generally released around ten weeks after the measured
    month. Until a historical release-calendar table is joined, 75 calendar days after
    month-end is used as a conservative approximation. This field is explicitly named
    `assumed_available_date` so it cannot be mistaken for a verified release date.
    """
    out = panel.copy()
    month_end = out["date"] + pd.offsets.MonthEnd(0)
    out["assumed_available_date"] = month_end + pd.to_timedelta(release_lag_days, unit="D")
    return out


def build_panel_from_snapshot(
    snapshot: T1Snapshot,
    *,
    universe: Iterable[str] = DEFAULT_UNIVERSE,
    service_classes: Iterable[str] = DEFAULT_SERVICE_CLASSES,
) -> pd.DataFrame:
    """Load a snapshot and attach its actual known publication timestamp.

    For a historical vintages workflow, each immutable download should contain only data
    that BTS had released by `snapshot.release_date`. The resulting panel therefore has
    a hard `snapshot_release_date` usable for point-in-time filtering.
    """
    raw = load_t1_csv(snapshot.path, service_classes=service_classes)
    panel = build_demand_capacity_panel(raw, universe=universe)
    panel["snapshot_release_date"] = pd.Timestamp(snapshot.release_date).normalize()
    return panel
