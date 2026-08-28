from __future__ import annotations

from io import StringIO
from pathlib import Path
import re

import pandas as pd
import requests

DATASET_CSV = "https://data.transportation.gov/api/v3/views/jqx4-4iha/export.csv?accessType=DOWNLOAD"

# Public-company tickers mapped to names/codes commonly seen in BTS T-100.
AIRLINES = {
    "DAL": ("delta", "dl"),
    "UAL": ("united", "ua"),
    "AAL": ("american", "aa"),
    "LUV": ("southwest", "wn"),
    "ALK": ("alaska", "as"),
    "JBLU": ("jetblue", "b6"),
}


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _find_col(columns, *needles: str, exclude: tuple[str, ...] = ()) -> str | None:
    normalized = {c: _norm(c) for c in columns}
    for c, n in normalized.items():
        if all(x in n for x in needles) and not any(x in n for x in exclude):
            return c
    return None


def download_t100(url: str = DATASET_CSV, timeout: int = 120) -> pd.DataFrame:
    """Download BTS AFF T-100 Segment Summary Monthly as published CSV."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return pd.read_csv(StringIO(response.text))


def standardize_t100(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize the BTS summary into carrier-month passengers/seats.

    The AFF export has changed display labels over time, so column discovery is
    deliberately tolerant rather than hard-coding one UI label set.
    """
    cols = list(raw.columns)
    year = _find_col(cols, "year")
    month = _find_col(cols, "month")
    passengers = _find_col(cols, "passenger", exclude=("mile",))
    seats = _find_col(cols, "seat", exclude=("mile",))
    carrier_code = (
        _find_col(cols, "carrier", "code")
        or _find_col(cols, "unique", "carrier")
        or _find_col(cols, "carrier")
    )
    carrier_name = (
        _find_col(cols, "carrier", "name")
        or _find_col(cols, "airline", "name")
        or _find_col(cols, "carrier")
    )

    missing = [
        name
        for name, col in {
            "year": year,
            "month": month,
            "passengers": passengers,
            "seats": seats,
            "carrier": carrier_code or carrier_name,
        }.items()
        if col is None
    ]
    if missing:
        raise ValueError(
            f"Could not identify required T-100 fields: {missing}. Available columns: {cols}"
        )

    out = pd.DataFrame(
        {
            "year": pd.to_numeric(raw[year], errors="coerce"),
            "month": pd.to_numeric(raw[month], errors="coerce"),
            "passengers": pd.to_numeric(raw[passengers], errors="coerce"),
            "seats": pd.to_numeric(raw[seats], errors="coerce"),
            "carrier_code": raw[carrier_code].astype(str) if carrier_code else "",
            "carrier_name": raw[carrier_name].astype(str) if carrier_name else "",
        }
    ).dropna(subset=["year", "month", "passengers", "seats"])

    out["year"] = out["year"].astype(int)
    out["month"] = out["month"].astype(int)
    out = out[out["month"].between(1, 12)]
    out["period"] = pd.PeriodIndex(year=out["year"], month=out["month"], freq="M")
    return out


def _ticker_for_row(row: pd.Series) -> str | None:
    code = _norm(row.get("carrier_code", ""))
    name = _norm(row.get("carrier_name", ""))
    for ticker, (name_token, code_token) in AIRLINES.items():
        if code == code_token or code.startswith(code_token + "_") or name_token in name:
            return ticker
    return None


def build_six_airline_panel(raw: pd.DataFrame, start: str = "2019-01", end: str = "2026-05") -> pd.DataFrame:
    """Create carrier-month passenger/seat panel for the six listed airlines."""
    df = standardize_t100(raw)
    df["ticker"] = df.apply(_ticker_for_row, axis=1)
    df = df[df["ticker"].notna()].copy()

    # T-100 summary can contain multiple operating entities/segments for a carrier.
    # Aggregate to the publicly traded carrier-month before computing growth rates.
    panel = (
        df.groupby(["period", "ticker"], as_index=False)[["passengers", "seats"]]
        .sum()
        .sort_values(["ticker", "period"])
    )
    start_p, end_p = pd.Period(start, "M"), pd.Period(end, "M")
    panel = panel[panel["period"].between(start_p, end_p)].copy()

    panel["passenger_yoy"] = panel.groupby("ticker")["passengers"].pct_change(12)
    panel["seat_yoy"] = panel.groupby("ticker")["seats"].pct_change(12)
    panel["demand_capacity_gap"] = panel["passenger_yoy"] - panel["seat_yoy"]
    return panel


def save_panel(path: str | Path, start: str = "2019-01", end: str = "2026-05") -> pd.DataFrame:
    raw = download_t100()
    panel = build_six_airline_panel(raw, start=start, end=end)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    panel.assign(period=panel["period"].astype(str)).to_csv(path, index=False)
    return panel


if __name__ == "__main__":
    panel = save_panel("data/airline_t100_panel.csv")
    print(panel.tail(18).to_string(index=False))
