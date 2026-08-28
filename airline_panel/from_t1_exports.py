from __future__ import annotations

from pathlib import Path
import zipfile
import pandas as pd

TICKER_MAP = {
    "DL": "DAL", "UA": "UAL", "AA": "AAL", "WN": "LUV", "AS": "ALK", "B6": "JBLU"
}

# BTS T1 field names seen in the user's annual exports.
COLMAP = {
    "YEAR": "year",
    "MONTH": "month",
    "UNIQUE_CARRIER": "carrier",
    "UNIQUECARRIER": "carrier",
    "REV_PAX_ENP_110": "passengers",
    "REV_PAX_ENPLANED": "passengers",
    "REV_PAX_MILES_140": "rpm",
    "REV_PAX_MILES": "rpm",
    "AVL_SEAT_MILES_320": "asm",
    "AVAIL_SEAT_MILES": "asm",
    "SERVICE_CLASS": "service_class",
    "SERVICECLASS": "service_class",
}


def _read_one(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".zip":
        with zipfile.ZipFile(path) as zf:
            csvs = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if len(csvs) != 1:
                raise ValueError(f"{path}: expected one CSV, found {csvs}")
            with zf.open(csvs[0]) as fh:
                return pd.read_csv(fh)
    return pd.read_csv(path)


def load_exports(folder: str | Path) -> pd.DataFrame:
    folder = Path(folder)
    files = sorted([*folder.glob("*.zip"), *folder.glob("*.csv")])
    if not files:
        raise FileNotFoundError(f"No BTS T1 CSV/ZIP files found in {folder}")

    frames = []
    for f in files:
        raw = _read_one(f)
        raw.columns = [str(c).strip().upper().replace(" ", "_") for c in raw.columns]
        rename = {c: COLMAP[c] for c in raw.columns if c in COLMAP}
        df = raw.rename(columns=rename)
        need = {"year", "month", "carrier", "rpm", "asm"}
        missing = need - set(df.columns)
        if missing:
            raise ValueError(f"{f}: missing {sorted(missing)}; columns={list(df.columns)}")
        frames.append(df)

    df = pd.concat(frames, ignore_index=True)
    df["carrier"] = df["carrier"].astype(str).str.strip().str.upper()
    df["ticker"] = df["carrier"].map(TICKER_MAP)
    df = df[df["ticker"].notna()].copy()

    # T1 can include several service classes. To avoid double counting aggregate
    # rows, prefer the total service class 'F' when present for a carrier-month;
    # otherwise retain all rows and aggregate once.
    if "service_class" in df.columns:
        df["service_class"] = df["service_class"].astype(str).str.strip().str.upper()
        keys = ["year", "month", "ticker"]
        has_f = df.groupby(keys)["service_class"].transform(lambda s: (s == "F").any())
        df = df[(~has_f) | (df["service_class"] == "F")].copy()

    for c in ["rpm", "asm"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["rpm", "asm"])

    panel = (df.groupby(["year", "month", "ticker"], as_index=False)[["rpm", "asm"]]
               .sum()
               .sort_values(["ticker", "year", "month"]))
    panel["period"] = pd.PeriodIndex(year=panel["year"].astype(int), month=panel["month"].astype(int), freq="M")

    # Industry demand uses the six-carrier universe so it is internally consistent.
    industry = panel.groupby("period", as_index=False)["rpm"].sum().rename(columns={"rpm": "industry_rpm"})
    panel = panel.merge(industry, on="period", how="left")
    panel["industry_rpm_yoy"] = panel.groupby("ticker", group_keys=False)["industry_rpm"].transform(lambda s: s.pct_change(12))
    # transform above repeats industry series by ticker, yielding identical YoY for all names.
    panel["asm_yoy"] = panel.groupby("ticker")["asm"].pct_change(12)
    panel["demand_capacity_gap"] = panel["industry_rpm_yoy"] - panel["asm_yoy"]
    return panel


def save_panel(folder: str | Path, out: str | Path = "data/airline_t1_panel.csv") -> pd.DataFrame:
    panel = load_exports(folder)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    panel.assign(period=panel["period"].astype(str)).to_csv(out, index=False)
    return panel


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("folder", help="Folder containing the annual BTS T1 ZIP/CSV exports")
    p.add_argument("--out", default="data/airline_t1_panel.csv")
    args = p.parse_args()
    panel = save_panel(args.folder, args.out)
    print(panel.tail(24).to_string(index=False))
