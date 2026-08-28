# MSP–DAL divergence: first strict point-in-time pass

## Data reconciliation

This pass uses the verified release-date MSP events for 2025-02-24 through 2026-08-25. Earlier MSP observations are retained for historical context but are not treated as strictly point-in-time because their original release dates are unresolved.

For each verified event, the available fields are: MSP traffic YoY z-score, next-trading-day DAL adjusted close, and subsequent DAL returns at approximately 21, 63, and 126 trading days.

Because this strict event file is release-event based rather than a complete daily market panel, the first-pass DAL momentum proxy is the percentage change in DAL entry price from the previous verified MSP release event. The DAL momentum z-score is computed expanding-only, using information available through the current event. Divergence is:

`divergence = traffic_z - dal_momentum_z`

A fixed threshold of -1.5 defines a negative divergence event (MSP traffic unusually weak relative to DAL price momentum). A +1.5 threshold would define the opposite state, but no positive-divergence events occur in this short verified sample.

## First-pass results

| State | N (21d) | Mean 21d | Median 21d | N (63d) | Mean 63d | Median 63d | N (126d) | Mean 126d | Median 126d |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Negative divergence (<= -1.5) | 8 | 6.7% | 7.9% | 6 | 9.6% | 9.5% | 5 | 30.9% | 32.0% |
| Neutral | 9 | 0.7% | -3.5% | 8 | 15.8% | 22.0% | 7 | 23.2% | 28.7% |

Welch two-sample p-values for negative-divergence versus neutral observations were approximately 0.53 (21d), 0.18 (63d), and 0.42 (126d). These are not statistically persuasive, and overlapping forward-return windows further reduce the effective independent sample size.

## Interpretation

The 21-day result is directionally interesting: weak MSP traffic relative to still-strong DAL price momentum was followed by higher average one-month DAL returns in this sample. The 126-day result also points in the same direction. However, the 63-day result reverses, sample sizes are very small, there are no positive-divergence events to test symmetry, and the event-to-event DAL momentum proxy is only an approximation.

This is therefore **not evidence of a tradable edge yet**. It is enough to justify a cleaner second pass.

## Next required test

Build a complete daily/month-end DAL price panel around the verified MSP release calendar. Then compute DAL momentum on fixed horizons (21d, 63d, and/or 3-month) and standardized trailing-only z-scores on every release date. Re-run the divergence buckets and threshold sensitivity using the exact release dates. Only if the effect persists should WTI be introduced as a conditioning variable.
