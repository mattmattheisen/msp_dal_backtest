# MSP Nowcast Baselines

This module establishes simple point-in-time forecasting hurdles that any later HMM or regime model must beat out of sample.

## Why start simple

The objective is not to find the model that produces the best historical DAL backtest. The objective is first to determine which method best forecasts unpublished MSP enplanements using only information available at the time.

The forecasting model is therefore developed and evaluated independently of DAL returns.

## Temporal rule

Every benchmark receives its historical information set through `available_as_of(...)` from `msp_availability.py`.

A model may use an MSP observation only when:

`release_date <= as_of_date`

If an observation's release date is not verified, the row is excluded by default.

## Benchmark 1: seasonal naive

For target month `t`:

`forecast_t = enplanements_(t-12)`

This is the simplest sensible benchmark because MSP traffic is highly seasonal.

Example: on May 1, 2026, March 2026 had not yet been published. The seasonal-naive forecast for March 2026 is therefore the known March 2025 value:

`1,639,810 enplanements`

The eventual March 2026 actual was `1,528,083`.

## Benchmark 2: recent YoY trend

The second benchmark applies recent known YoY growth to the same-month prior-year base:

`forecast_t = enplanements_(t-12) * (1 + mean(recent known YoY growth))`

The default window is three known observations.

On May 1, 2026, the latest published MSP observation was January 2026. The three most recent known YoY growth rates were November 2025, December 2025, and January 2026. Their average was approximately `-5.25%`.

For March 2026:

`forecast = 1,639,810 * (1 - 0.0525) ≈ 1,553,708`

The eventual actual was `1,528,083`, making the recent-YoY benchmark materially closer than seasonal naive in this single example.

This example is illustrative only. Model selection must use repeated walk-forward scoring, not one historical month.

## Forecast scoring

`score_forecast(...)` currently reports:

- forecast error
- absolute error
- absolute percentage error

The next step is to build walk-forward evaluation across all months with verified release dates and compare mean/median absolute percentage error across methods.

## HMM promotion rule

A Hidden Markov Model should not enter the DAL signal pipeline merely because it is more sophisticated. It must demonstrate lower out-of-sample MSP forecast error than these simple benchmarks across a reasonable walk-forward sample.

Only after the MSP forecasting methodology is selected and frozen should its nowcasts be tested as predictors of DAL returns.
