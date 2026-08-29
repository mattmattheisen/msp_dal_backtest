# Crowding Gate 01

This folder is intentionally a small falsification test, not a new trading platform.

## Question

Does abnormal trading volume add incremental short-term reversal information after an extreme 5-day stock-specific gain?

## Pre-declared screen

- Universe: current S&P 100-style liquid large-cap list, frozen in `gate01.py`.
- Benchmark: SPY.
- Extreme winner: stock 5-day excess return exceeds its own prior-only rolling 95th percentile.
- Abnormal volume: 5-day average volume divided by the prior 60-day average exceeds its own prior-only rolling 95th percentile.
- Event: first day entering the extreme-winner state.
- Entry timing: next day's close, so the signal-day move is not captured as profit.
- Forward horizons: 1, 3, 5, 10, 20 trading days.
- Primary horizon: 10 trading days.
- Chronological eras:
  - Development: 2015–2019
  - Validation: 2020–2022
  - Final OOS: 2023+

## Why SPY rather than sector ETFs in Gate 01?

This is the cheapest possible screen. If volume does not add information even after controlling for the broad market, the project stops. If it survives, the next gate replaces SPY with sector-relative returns and requires point-in-time universe membership before any options or sentiment data are purchased.

## Deliberate limitations

This screen uses today's liquid large-cap universe and therefore has survivorship bias. That bias is tolerated only because the test is asymmetric: a negative result stops the project; a positive result is merely provisional and must survive a better data design.

Yahoo Finance is used for free historical OHLCV. No historical options, Reddit, Google Trends, news sentiment, LPPLS, machine learning, or optimized thresholds are included.

## Outputs

Running:

```bash
python crowding_lab/gate01.py
```

writes:

```text
crowding_lab/output/
    event_log.csv
    group_summary.csv
    crowding_incremental.csv
    ticker_summary.csv
    data_coverage.csv
    research_summary.md
```

## Stop rule

Do not expand the project unless the final-OOS 10-day incremental effect of crowded winners versus non-crowded extreme winners is at least -0.30 percentage points, has the same negative direction in development/validation/final-OOS, and has at least 20 final-OOS crowded event dates.

If the gate fails, archive it and do not buy additional data for this hypothesis.
