#!/usr/bin/env python
# run_backtest.py
"""
CLI entry point for the MSP-DAL alternative data backtest.

Usage:
    python run_backtest.py
    python run_backtest.py --lag 2 --lookback 1 --threshold 0.05
    python run_backtest.py --lag 1 --no-covid --seasonal
    python run_backtest.py --lag 1 --no-covid --no-charts

Options:
    --lag INT           Months pax signal leads DAL entry (default: config.LAG_MONTHS)
    --lookback INT      Momentum lookback window in months (default: config.LOOKBACK_MONTHS)
    --threshold FLOAT   Min MoM pax growth to go long (default: config.SIGNAL_THRESHOLD)
    --no-covid          Include COVID regime (2020–2021) — default is to exclude
    --seasonal          Apply seasonal adjustment to pax before computing momentum
    --no-charts         Skip chart generation (terminal output only)
"""

import argparse
import sys
from pathlib import Path

# Allow running from repo root without install
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

import config
from src.data_loader import load_aligned_data
from src.signal import compute_signal, lag_correlation_table, best_lag
from src.backtest import run_backtest, trades_to_dataframe
from src.metrics import compute_all, print_metrics


def parse_args():
    p = argparse.ArgumentParser(description="MSP Airport Passenger Signal — DAL Backtest")
    p.add_argument("--lag",       type=int,   default=None)
    p.add_argument("--lookback",  type=int,   default=None)
    p.add_argument("--threshold", type=float, default=None)
    p.add_argument("--no-covid",  action="store_true")
    p.add_argument("--seasonal",  action="store_true")
    p.add_argument("--no-charts", action="store_true")
    return p.parse_args()


def main():
    args = parse_args()

    # Override config with CLI args
    if args.lag       is not None: config.LAG_MONTHS        = args.lag
    if args.lookback  is not None: config.LOOKBACK_MONTHS   = args.lookback
    if args.threshold is not None: config.SIGNAL_THRESHOLD  = args.threshold
    if args.no_covid:              config.EXCLUDE_COVID      = False
    if args.seasonal:              config.SEASONAL_ADJUST    = True
    if args.no_charts:             config.SHOW_CHARTS        = False

    print(f"\n{'─'*50}")
    print("  MSP Airport Passenger Signal — DAL Backtest")
    print(f"{'─'*50}")
    print(f"  Lag:           +{config.LAG_MONTHS} month(s)")
    print(f"  Lookback:      {config.LOOKBACK_MONTHS} month(s)")
    print(f"  Threshold:     {config.SIGNAL_THRESHOLD*100:.1f}% MoM pax growth")
    print(f"  COVID period:  {'excluded' if config.EXCLUDE_COVID else 'included'}")
    print(f"  Seasonal adj.: {'yes' if config.SEASONAL_ADJUST else 'no'}")
    print(f"{'─'*50}")

    # Load + signal
    df = load_aligned_data()
    df_sig = compute_signal(df)

    # Lag correlation analysis
    lt = lag_correlation_table(df)
    bl = best_lag(lt)
    print(f"\nLag correlation table:")
    print(lt.to_string(index=False))
    print(f"\n  Best lag: {'+' if bl['lag'] >= 0 else ''}{int(bl['lag'])} months  "
          f"(r = {bl['r']:.3f}, p = {bl['p_value']:.3f}, n = {int(bl['n_obs'])})")

    # Run backtest
    result = run_backtest(df_sig)

    # Metrics
    m = compute_all(result)
    print_metrics(m)

    # Trade log
    tdf = trades_to_dataframe(result.trades)
    if not tdf.empty:
        print(f"\nTrade log ({len(tdf)} trades):")
        print(tdf[["entry_month", "exit_month", "entry_price",
                   "exit_price", "return_pct", "net_pnl"]].to_string(index=False))
    else:
        print("\nNo completed trades in the selected period.")

    # Charts
    if config.SHOW_CHARTS or config.SAVE_CHARTS:
        try:
            import matplotlib
            if not config.SHOW_CHARTS:
                matplotlib.use("Agg")   # headless for save-only mode
            import matplotlib.pyplot as plt
            from src.visualize import plot_all

            fig = plot_all(df, df_sig, result, lt, m, active_lag=config.LAG_MONTHS)

            if config.SHOW_CHARTS:
                plt.show()
        except ImportError:
            print("\nmatplotlib not installed — skipping charts. Run: pip install matplotlib")


if __name__ == "__main__":
    main()
