# MSP/DAL Divergence — Fixed 63-Session Momentum Gate

## Purpose
This is the final pre-specified gate after the fixed 21-session divergence result failed to survive a reasonable momentum specification change.

The DAL conditioning variable is fixed 63-trading-session momentum:

`mom63_t = DAL_close_t / DAL_close_{t-63 sessions} - 1`

Momentum is standardized with an expanding z-score using only prior available observations. Divergence is:

`divergence63_t = MSP_traffic_z_t - DAL_mom63_z_t`

Negative values mean MSP traffic is weak relative to DAL's 63-session price momentum.

## Data notes
- Strict MSP point-in-time release dates are retained.
- Exact 63-session anchor dates were generated from the NYSE trading calendar.
- Two early anchor closes were not sufficiently reliable from the available sources and were deliberately left missing rather than fabricated.
- Because expanding standardization requires history, the first eligible divergence observation is 2025-09-24.
- Forward-return windows overlap, so effective sample size is smaller than raw N.

## Results: subsequent 21-session DAL return

| Divergence threshold | Extreme N | Extreme mean | Extreme median | Other N | Other mean | Other median |
|---|---:|---:|---:|---:|---:|---:|
| <= -1.5 | 8 | 1.31% | -1.07% | 2 | 18.74% | 18.74% |
| <= -2.0 | 4 | 0.47% | 0.47% | 6 | 7.68% | 7.96% |
| <= -2.5 | 2 | -4.25% | -4.25% | 8 | 7.05% | 5.18% |

The ordering is opposite the proposed edge: more extreme negative divergence does not produce stronger subsequent DAL returns. At the most extreme threshold, subsequent 21-session returns are negative on average while the comparison group is positive.

For the <= -1.5 split, a two-sided Mann-Whitney test is approximately p=0.044, but this should not be interpreted as a validated signal. There are only two observations in the comparison group, the windows overlap, and the direction indicates underperformance after extreme divergence rather than the originally hypothesized rebound edge.

## Results: subsequent 63-session DAL return

| Divergence threshold | Extreme N | Extreme mean | Extreme median | Other N | Other mean | Other median |
|---|---:|---:|---:|---:|---:|---:|
| <= -1.5 | 5 | 11.28% | 8.52% | 2 | 20.39% | 20.39% |
| <= -2.0 | 3 | 7.34% | 4.97% | 4 | 18.79% | 20.39% |
| <= -2.5 | 2 | -1.71% | -1.71% | 5 | 20.12% | 22.31% |

Again, increasing divergence severity does not strengthen the proposed return edge. The most extreme observations perform materially worse than the comparison observations.

## Conclusion
**The divergence gate fails.**

The original correlation thesis failed. A first event-to-event divergence pass looked mildly interesting, but that effect weakened under fixed 21-session momentum. The final fixed 63-session gate now fails in the same direction and more clearly: larger negative MSP/DAL divergences are not followed by larger DAL rebounds.

On the evidence currently available, MSP passenger traffic should be documented as a tested null for a standalone DAL trading signal. WTI, VIX, or additional filters should not be introduced merely to rescue this hypothesis, because that would materially increase data-mining risk.

A future revisit would only be justified by substantially more true point-in-time observations, a separate economic mechanism, or a pre-registered cross-airport hypothesis tested on fresh data.
