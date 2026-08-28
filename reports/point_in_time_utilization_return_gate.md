# Point-in-time utilization return gate

## Purpose
Test whether the modern monthly ASM-growth return signal is primarily present when the fast-ASM growers were already in a high/rising utilization state, without leaking annual B-43 information backward in time.

## Point-in-time rule
B-43 is annual and is not treated as known during the inventory year. For a conservative availability convention, an annual utilization state for year Y becomes usable beginning in July of Y+1. Therefore Jan-Jun signal dates use at most Y-2 state data and Jul-Dec use at most Y-1 state data.

Utilization state is defined as annual ASM per operating aircraft, with YoY growth calculated from BTS T1 annual ASM and B-43 aircraft with OPERATING_STATUS=Y.

For each monthly signal date, identify the two carriers with the highest YoY ASM growth and average their latest point-in-time utilization-growth states. Compare the already-frozen six-month fast-minus-slow capacity return spread across high versus low utilization states. No threshold was optimized: the sample median is used only as a descriptive split; the continuous relationship is also reported.

## Modern sample result (2024-01 through 2026-02; 26 six-month observations)
- Correlation between fast-grower lagged utilization state and subsequent six-month fast-minus-slow return spread: **+0.188**.
- Simple continuous regression slope: **+0.443** spread units per 1.00 utilization-growth unit; **p = 0.359**. This is not statistically significant.
- Below-median lagged utilization state: **+12.6%** average six-month spread; **80.0%** positive (10 observations).
- At/above-median lagged utilization state: **+20.6%** average six-month spread; **87.5%** positive (16 observations).
- Difference in descriptive averages: about **+8.0 percentage points** in favor of the higher-utilization state.

## Interpretation
The sign is consistent with the operating-deployment hypothesis: the capacity signal is stronger when the fast ASM growers had previously demonstrated stronger ASM-per-aircraft growth. However, the point-in-time annual state does **not** statistically explain the modern return effect. The signal remains strong even in the lower-utilization-state observations.

Therefore the earlier contemporaneous 0.96-0.97 ASM/utilization correlations are useful structural evidence but should not be promoted to a predictive filter. Annual B-43 is too coarse and delayed to establish that utilization state is the source of the return edge.

## Research conclusion
**Gate: suggestive but fails as a standalone explanatory/predictive filter.**

Do not optimize a utilization threshold. Keep the core modern capacity signal separate. The next falsification should ask whether the signal is concentrated in *capacity acceleration/change* rather than capacity level/growth itself, using only monthly T1 data and the existing three-month information lag. That test has much higher temporal resolution and avoids B-43 publication-timing limitations.
