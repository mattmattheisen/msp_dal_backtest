import pandas as pd

from airline_panel.bts_t1 import build_demand_capacity_panel, load_t1_csv


def test_load_t1_aggregates_regions(tmp_path):
    p = tmp_path / "t1.csv"
    pd.DataFrame(
        {
            "Year": [2024, 2024, 2024],
            "Month": [1, 1, 1],
            "UniqueCarrier": ["DL", "DL", "UA"],
            "ServiceClass": ["F", "F", "F"],
            "RevPaxMiles": [100.0, 50.0, 80.0],
            "RevPaxEnplaned": [10.0, 5.0, 8.0],
            "AvailSeatMiles": [120.0, 60.0, 100.0],
        }
    ).to_csv(p, index=False)

    out = load_t1_csv(p)
    dl = out[out["carrier"] == "DL"].iloc[0]
    assert dl["rpm"] == 150.0
    assert dl["pax"] == 15.0
    assert dl["asm"] == 180.0


def test_dc_gap_uses_industry_demand_minus_carrier_capacity():
    rows = []
    for year, scale in [(2024, 1.0), (2025, 1.1)]:
        for month in range(1, 13):
            rows.extend(
                [
                    {"date": pd.Timestamp(year, month, 1), "carrier": "DL", "rpm": 100 * scale, "pax": 10 * scale, "asm": 120 * (1.2 if year == 2025 else 1.0)},
                    {"date": pd.Timestamp(year, month, 1), "carrier": "UA", "rpm": 100 * scale, "pax": 10 * scale, "asm": 120 * (1.0 if year == 2025 else 1.0)},
                    {"date": pd.Timestamp(year, month, 1), "carrier": "AA", "rpm": 100 * scale, "pax": 10 * scale, "asm": 120 * (1.0 if year == 2025 else 1.0)},
                ]
            )

    panel = build_demand_capacity_panel(pd.DataFrame(rows), universe=("DL", "UA", "AA"))
    jan25 = panel[(panel["date"] == "2025-01-01") & (panel["carrier"] == "DL")].iloc[0]

    # Industry RPM grew 10%, while DL ASM grew 20%.
    assert round(jan25["industry_demand_yoy"], 6) == 0.10
    assert round(jan25["carrier_capacity_yoy"], 6) == 0.20
    assert round(jan25["dc_gap"], 6) == -0.10
