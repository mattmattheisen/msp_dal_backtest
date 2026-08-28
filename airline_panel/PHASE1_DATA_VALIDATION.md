# Phase 1 BTS data validation

## Raw exports received
Annual T1 exports were validated for every year 2010 through 2026. Full years are present for 2010-2025; the 2026 export contains January-May, matching the current BTS vintage.

Current TranStats CSV columns are:
`YEAR`, `MONTH`, `UNIQUE_CARRIER`, `UNIQUE_CARRIER_NAME`, `REGION`, `SERVICE_CLASS`, `REV_PAX_ENP_110`, `REV_PAX_MILES_140`, `AVL_SEAT_MILES_320`.

The ingestion code was updated to recognize the numbered metric names emitted by the current exporter.

## Service-class rule
Only service class `F` is used in Phase 1. Aggregate service classes such as K/Z are not summed with component classes. Carrier/month primitive measures are then summed across reporting regions/entities.

## First assembled panel
Universe: AA, AS, B6, DL, UA, WN.

- Observation months: 197 (2010-01 through 2026-05)
- Carrier-month rows: 1,182
- Rows with computable YoY demand-capacity gap: 1,110 (first 12 months per carrier are naturally unavailable)
- Each of the six carrier codes is represented continuously in the export window.

Signal fixed before returns:
`dc_gap = industry RPM YoY growth - carrier ASM YoY growth`

The current point-in-time scaffold attaches an explicitly *assumed* availability date of month-end + 75 calendar days until exact historical BTS release dates are reconstructed.

## Distribution check before attaching returns
Across the 1,110 computable carrier-month observations, the demand-capacity gap quantiles are approximately:

| Quantile | DC gap |
|---|---:|
| 1% | -0.777 |
| 5% | -0.259 |
| 20% | -0.060 |
| 50% | -0.006 |
| 80% | +0.041 |
| 95% | +0.414 |
| 99% | +1.784 |

The distribution has very large pandemic/base-effect observations. April 2021 industry RPM YoY growth is roughly +1,538%, producing DC gaps around +11.7 to +14.6 across the six carriers. This is an economic/base-effect feature of YoY ratios, not an ingestion error.

## Pre-return decision
Do **not** optimize away the pandemic observations after seeing returns. Preserve the originally specified full-sample quintile test, but require explicit subperiod robustness reporting (pre-pandemic, disruption/reopening, and normalized post-reopening periods). If the apparent effect is driven only by 2020-2021 base effects, it does not pass the Phase-1 gate.

## Next gate
Attach carrier stock prices using the assumed/verified availability date, compute 21-, 63-, and 126-session forward returns and equal-weight airline-basket excess returns, then evaluate pre-specified cross-sectional quintiles and subperiod stability. No fuel/options/valuation variables are permitted before this gate is evaluated.
