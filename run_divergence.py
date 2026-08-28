"""CLI runner for the MSP/DAL divergence experiment."""

from pathlib import Path

import pandas as pd

from divergence import DivergenceConfig, build_divergence_frame, divergence_event_table, summarize_forward_returns


DATA_DIR = Path(__file__).parent / "data"


def load_data() -> pd.DataFrame:
    msp = pd.read_csv(DATA_DIR / "msp_passengers.csv")
    dal = pd.read_csv(DATA_DIR / "dal_prices.csv")
    msp["year_month"] = pd.to_datetime(msp["year_month"])
    dal["year_month"] = pd.to_datetime(dal["year_month"])
    return (
        pd.merge(msp[["year_month", "passengers"]], dal[["year_month", "close"]], on="year_month", how="inner")
        .sort_values("year_month")
        .reset_index(drop=True)
    )


def main() -> None:
    df = load_data()
    cfg = DivergenceConfig()
    frame = build_divergence_frame(df, cfg)
    summary = summarize_forward_returns(frame, cfg.forward_horizons)
    events = divergence_event_table(frame)

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 20)

    print("\nMSP/DAL point-in-time divergence experiment")
    print(f"Rows: {len(frame)} | Extreme threshold: +/-{cfg.extreme_z:.2f} z")
    print("\nConditional forward returns:")
    if summary.empty:
        print("No valid observations after warm-up.")
    else:
        display = summary.copy()
        for c in ["mean_return", "median_return", "win_rate", "std_return"]:
            display[c] = display[c].map(lambda x: f"{x:.2%}" if pd.notna(x) else "NA")
        print(display.to_string(index=False))

    print("\nExtreme divergence events:")
    if events.empty:
        print("No extreme events at the current threshold.")
    else:
        print(events.to_string(index=False))


if __name__ == "__main__":
    main()
