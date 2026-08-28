"""BTS T1 ingestion and demand/capacity panel construction.

Expected input is a TranStats export from T1: U.S. Air Carrier Traffic And Capacity
Summary by Service Class. The loader accepts both human-readable field names and the
numbered column names emitted by the current TranStats CSV exporter.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
import numpy as np
import pandas as pd

DEFAULT_UNIVERSE = ("DL", "UA", "AA", "WN", "AS", "B6")
DEFAULT_SERVICE_CLASSES = ("F",)  # scheduled passenger/cargo; avoid K/Z aggregates

@dataclass(frozen=True)
class T1Snapshot:
    path: Path
    release_date: pd.Timestamp

_COLUMN_ALIASES: Mapping[str, str] = {
    "year": "year", "month": "month", "uniquecarrier": "carrier",
    "unique_carrier": "carrier", "serviceclass": "service_class",
    "service_class": "service_class", "revpaxmiles": "rpm",
    "rev_pax_miles": "rpm", "revpaxmiles140": "rpm",
    "revpaxenplaned": "pax", "rev_pax_enplaned": "pax",
    "revpaxenp110": "pax", "availseatmiles": "asm",
    "avail_seat_miles": "asm", "avlseatmiles320": "asm",
}

def _canonicalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    compact_aliases = {k.replace("_", ""): v for k, v in _COLUMN_ALIASES.items()}
    rename = {}
    for c in out.columns:
        compact = str(c).strip().lower().replace(" ", "").replace("-", "").replace("_", "")
        if compact in compact_aliases:
            rename[c] = compact_aliases[compact]
    return out.rename(columns=rename)

def load_t1_csv(path: str | Path, *, service_classes: Iterable[str] = DEFAULT_SERVICE_CLASSES) -> pd.DataFrame:
    df = _canonicalize_columns(pd.read_csv(path))
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
    df["year"] = df["year"].astype(int); df["month"] = df["month"].astype(int)
    df["date"] = pd.to_datetime({"year": df["year"], "month": df["month"], "day": 1})
    return (df.groupby(["date", "carrier"], as_index=False)[["rpm", "pax", "asm"]]
            .sum(min_count=1).sort_values(["date", "carrier"]).reset_index(drop=True))

def build_demand_capacity_panel(t1: pd.DataFrame, *, universe: Iterable[str] = DEFAULT_UNIVERSE, min_industry_carriers: int = 3) -> pd.DataFrame:
    df = t1.copy().sort_values(["carrier", "date"])
    industry = (df.groupby("date", as_index=False)
                .agg(industry_rpm=("rpm", "sum"), industry_carriers=("carrier", "nunique"))
                .sort_values("date"))
    industry["industry_demand_yoy"] = industry["industry_rpm"].pct_change(12)
    industry.loc[industry["industry_carriers"] < min_industry_carriers, "industry_demand_yoy"] = np.nan
    wanted = {str(x).upper() for x in universe}
    carriers = df[df["carrier"].isin(wanted)].copy()
    carriers["carrier_capacity_yoy"] = carriers.groupby("carrier")["asm"].pct_change(12)
    carriers["carrier_rpm_yoy"] = carriers.groupby("carrier")["rpm"].pct_change(12)
    carriers["carrier_pax_yoy"] = carriers.groupby("carrier")["pax"].pct_change(12)
    panel = carriers.merge(industry[["date", "industry_rpm", "industry_demand_yoy"]], on="date", how="left", validate="many_to_one")
    panel["dc_gap"] = panel["industry_demand_yoy"] - panel["carrier_capacity_yoy"]
    return panel.sort_values(["date", "carrier"]).reset_index(drop=True)

def apply_publication_lag(panel: pd.DataFrame, *, release_lag_days: int = 75) -> pd.DataFrame:
    out = panel.copy(); month_end = out["date"] + pd.offsets.MonthEnd(0)
    out["assumed_available_date"] = month_end + pd.to_timedelta(release_lag_days, unit="D")
    return out

def build_panel_from_snapshot(snapshot: T1Snapshot, *, universe: Iterable[str] = DEFAULT_UNIVERSE, service_classes: Iterable[str] = DEFAULT_SERVICE_CLASSES) -> pd.DataFrame:
    raw = load_t1_csv(snapshot.path, service_classes=service_classes)
    panel = build_demand_capacity_panel(raw, universe=universe)
    panel["snapshot_release_date"] = pd.Timestamp(snapshot.release_date).normalize()
    return panel
