# WTI control for MSP -> DAL

## Question

Does adding an energy-price control reveal incremental predictive information in
the MSP traffic signal for DAL?

## Pre-specified energy variable

WTI uses the FRED/EIA DCOILWTICO daily spot-price series supplied by the user.

The energy predictor is fixed before model comparison:

    WTI_21d = last known WTI / WTI 21 observations earlier - 1

No oil lookback is optimized against DAL returns.

## Historical traffic panel

The longer-history analysis retains the prior exploratory pseudo-real-time
rules:

- fixed two-month MSP reporting lag;
- three most recent known YoY MSP observations form the traffic estimate;
- traffic estimate is converted to an expanding-history z-score;
- 2020-2022 are excluded as COVID/reopening structural-break years;
- DAL forward returns begin after target month-end.

Because exact pre-2025 MAC publication dates are still being reconstructed,
this remains an exploratory historical diagnostic, not a fully strict tradable
backtest.

## Models

1. Historical mean DAL forward return
2. Traffic z-score only
3. Traffic z-score + trailing 21-day WTI return
4. Traffic z-score + WTI + traffic x WTI interaction

Evaluation is expanding-window out-of-sample with a minimum of 36 prior monthly
observations.

## Raw correlations

| horizon_days | n | corr_traffic_dal | corr_wti_dal | corr_traffic_wti |
|---:|---:|---:|---:|---:|
| 5 | 78 | 0.0291 | -0.0424 | -0.1322 |
| 21 | 77 | -0.0364 | -0.1032 | -0.1093 |
| 63 | 75 | -0.0358 | 0.0054 | -0.1821 |

## Out-of-sample results

| horizon | model | n | MAE | RMSE | bias | sign accuracy |
|---:|:---|---:|---:|---:|---:|---:|
| 5 | historical_mean | 42 | 0.04395 | 0.06016 | -0.00660 | 0.6190 |
| 5 | traffic_only | 42 | 0.04472 | 0.06105 | -0.00782 | 0.5000 |
| 5 | traffic_plus_wti | 42 | 0.04604 | 0.06207 | -0.00789 | 0.4048 |
| 5 | traffic_wti_interaction | 42 | 0.04440 | 0.06174 | -0.00605 | 0.5714 |
| 21 | historical_mean | 41 | 0.09524 | 0.12121 | -0.01860 | 0.5854 |
| 21 | traffic_only | 41 | 0.09873 | 0.12509 | -0.02432 | 0.5610 |
| 21 | traffic_plus_wti | 41 | 0.10051 | 0.12596 | -0.02337 | 0.5122 |
| 21 | traffic_wti_interaction | 41 | 0.10207 | 0.12919 | -0.01976 | 0.5610 |
| 63 | historical_mean | 39 | 0.19813 | 0.22835 | -0.07028 | 0.6410 |
| 63 | traffic_only | 39 | 0.20986 | 0.24524 | -0.08788 | 0.5641 |
| 63 | traffic_plus_wti | 39 | 0.21190 | 0.25074 | -0.08907 | 0.4872 |
| 63 | traffic_wti_interaction | 39 | 0.19066 | 0.24021 | -0.07372 | 0.6154 |

## Interpretation

Adding WTI does not improve the simple MSP signal out of sample.

At 5 trading days, traffic-only RMSE is about 6.11%, while traffic + WTI is
about 6.21%. At 21 days, traffic-only RMSE is about 12.51% versus 12.60% with
WTI. At 63 days, traffic-only RMSE is about 24.52% versus 25.07% with WTI.

The interaction model is somewhat better than traffic-only at 63 days
(approximately 24.02% RMSE versus 24.52%), but it still trails the historical
mean benchmark (approximately 22.84%). It should therefore not be treated as an
established interaction effect.

The principal conclusion is negative and should be preserved: with the current
MSP construction and a pre-specified WTI control, neither MSP nor WTI provides
incremental out-of-sample DAL forecasting value relative to a simple historical
mean benchmark.

The next economically justified control is the broad equity market / airline
relative return, not additional oil-window tuning.
