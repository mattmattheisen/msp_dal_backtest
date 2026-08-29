# Municipal CEF Gate 01 — Year-End Discount Compression

## Decision
Determine whether a simple, structural year-end dislocation in municipal closed-end funds is strong enough to justify any further research.

## Primary hypothesis
Municipal CEFs that finish a losing calendar year at an unusually wide discount to NAV experience discount compression during the next ~20 trading days.

This is intended to test a tax-loss-selling / forced-selling mechanism, not a generic value claim.

## Frozen universe
Established municipal closed-end funds with public NAV tickers and sufficient history. The initial screening universe is intentionally small and current-survivor-biased; if the gate survives, a later phase must use a broader point-in-time universe including delisted/merged funds.

| Fund | NAV ticker |
|---|---|
| EOT | XEOTX |
| MMU | XMMUX |
| EVN | XEVNX |
| NZF | XNZFX |
| NEA | XNEAX |
| NAD | XNADX |
| NVG | XNVGX |
| KTF | XKTFX |
| EIM | XEIMX |
| NMI | XNMIX |
| MMD | XMMDX |

## Data
- Exchange market price: Yahoo Finance via `yfinance`
- NAV: public NAV ticker via `yfinance`
- Benchmark: MUB adjusted close
- Sample target: 2007 onward, with year-end observations beginning only after enough trailing history exists

## Signal definition
On the final common trading date of each calendar year:

1. `discount = market_close / NAV_close - 1`
2. Compute the fund's trailing 756-trading-day (about 3-year) 10th percentile of discount using **prior observations only**.
3. `extreme_discount = discount <= trailing_q10`
4. Compute calendar-year total return from adjusted market prices.
5. Primary tax-loss event:

`taxloss_extreme = extreme_discount AND YTD_total_return < 0`

No threshold optimization is allowed in Gate 01.

## Outcomes
Primary:
- Change in premium/discount over the next 20 trading days, in percentage points. Positive = discount compression.

Secondary:
- 20-trading-day CEF total return
- 20-trading-day excess total return versus MUB

## Control
Funds with negative YTD total return in the same sample that are **not** at an extreme discount.

## Chronological eras
- Development: through 2017
- Validation: 2018–2021
- Final OOS screening period: 2022–2025

2026 is excluded because the calendar year is incomplete.

## Pre-declared go/no-go gate
Proceed only if all are true in 2022–2025:

1. At least 10 primary event observations.
2. Mean 20-day discount compression >= +1.0 percentage point.
3. Mean compression exceeds the negative-YTD control group by >= +0.5 percentage point.
4. At least 3 of the 4 OOS calendar years with primary events show positive average compression.
5. Mean 20-day excess total return versus MUB is positive.

If the gate fails, stop. Do not add leverage, duration, distribution yield, state, credit quality, activist involvement, sentiment, or optimized discount thresholds.

## Caveats acknowledged before results
- The initial universe contains funds that exist today, so survivorship bias is present.
- NAV-ticker history from Yahoo is a screening source, not the final institutional source of truth.
- Corporate actions, mergers, tender offers, term conversions, and policy changes can affect comparability.
- Funds are cross-sectionally correlated; fund-year observations are not fully independent.
- The primary outcome is discount change, which avoids needing to estimate NAV total return. MUB-relative market return is secondary.

A surviving result earns a better dataset. A failed result ends the project.