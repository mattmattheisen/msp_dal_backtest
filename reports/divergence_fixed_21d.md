# MSP/DAL divergence: fixed 21-trading-day momentum rerun

## Purpose

This rerun replaces the first-pass event-to-event DAL momentum proxy with a fixed 21-trading-session DAL momentum measure. The objective is to test whether the initially interesting short-horizon result survives a less path-dependent momentum definition.

## Point-in-time rules

- MSP traffic observations are only used on or after their verified MAC release date.
- DAL momentum is computed only from prices known on the MSP release date: `P_t / P_{t-21 sessions} - 1`.
- Forward DAL performance still begins on the next trading session after the MSP release.
- The 2026-05-15 MAC release, which published both February and March observations, remains one event, consistent with the strict event table.
- No WTI conditioning is used in this rerun.

## Reconciliation

The reconciled input rows are stored in `data/divergence_fixed21_inputs.csv`. Daily DAL closes were cross-checked against the previously supplied Yahoo Finance history and current historical-price sources. The calculation uses unadjusted closes consistently for the backward 21-session momentum leg; over a 21-session horizon, the difference from adjusted-close momentum is small and does not change the qualitative conclusion. Forward returns remain the adjusted-price returns from the strict event dataset.

## Standardization

For event `t`, fixed 21-day momentum is standardized using only prior event momentum observations:

`mom21_z_t = (mom21_t - mean(mom21_<t)) / sd(mom21_<t)`

A minimum of five prior events is required. The divergence score is:

`divergence21_t = traffic_z_t - mom21_z_t`

Therefore the first eligible standardized divergence observation is 2025-07-23. There are 12 eligible events with known 21-day forward DAL returns.

## Result

The first-pass +6.7% mean 21-day DAL return after extreme negative divergence **does not survive** the fixed-horizon momentum definition.

| Negative divergence cutoff | Extreme N | Extreme mean 21d | Extreme median 21d | Other N | Other mean 21d | Other median 21d |
|---|---:|---:|---:|---:|---:|---:|
| <= -1.5 | 10 | +3.74% | +1.09% | 2 | +8.43% | +8.43% |
| <= -2.0 | 3 | +1.55% | -1.70% | 9 | +5.51% | +2.63% |
| <= -2.5 | 2 | +3.17% | +3.17% | 10 | +4.79% | +1.09% |

Approximate two-sided Mann-Whitney p-values are 0.61, 0.60, and 0.76 for the -1.5, -2.0, and -2.5 cutoffs respectively. Welch-test p-values are similarly uninformative (about 0.76, 0.60, and 0.90). These tests should not be over-interpreted because the sample is tiny and forward-return windows overlap.

## Interpretation

This is a useful negative result. The apparent first-pass 21-day effect was dependent on the event-to-event momentum proxy. Once DAL momentum is measured over a fixed 21-trading-day horizon, more-negative MSP/DAL divergence does not produce stronger subsequent DAL returns. At the -2.0 threshold, the extreme group actually has a lower mean and median 21-day return than the comparison group.

The fixed-horizon rerun therefore weakens the case that MSP-vs-DAL divergence is a standalone trading edge. It does not prove there is no conditional information in MSP traffic, but it removes the strongest feature from the first pass.

## Next research gate

Before adding WTI or additional conditioning variables, the clean next test is a fixed 63-trading-day DAL momentum rerun using the same point-in-time rules. If the signal also fails there, the divergence branch should be treated as a documented null result rather than expanded into a multi-factor search that risks data mining.
