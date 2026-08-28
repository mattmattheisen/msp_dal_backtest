# Load-Factor Regime Gate

## Question
Does relative airline capacity expansion work better when the industry's scheduled-passenger load factor is improving?

## Signal and timing
- Cross-sectional signal: rank DAL, UAL, AAL, LUV, ALK, and JBLU by YoY carrier capacity growth (ASM).
- Portfolio spread: two fastest capacity growers minus two slowest.
- Information lag: 3 months from BTS operating month to signal month.
- Load factor: BTS T1 scheduled passenger service (Service Class F), calculated as industry RPM / industry ASM.
- Load-factor regime: improving when current industry load factor is above its year-ago level.

BTS service class F is scheduled passenger/cargo service. We use F rather than aggregate K/Z classes to avoid mixing all-cargo/non-scheduled activity into passenger load factor.

## Pre-COVID non-overlapping 6-month gate (2014-2019)

| Load-factor regime | N | Mean Fast-Slow 6m | Hit rate | Median | t-stat |
|---|---:|---:|---:|---:|---:|
| Improving | 5 | +5.26% | 60.0% | +1.30% | 0.97 |
| Not improving | 7 | -1.67% | 42.9% | -0.70% | -0.36 |

This is directionally consistent with the economic story, but weak. Improvement in industry load factor appears to separate a modestly positive pre-COVID capacity-expansion regime from a slightly negative one, but the sample is tiny and neither subgroup is statistically persuasive.

A second pre-specified-style check using load factor above a trailing 5-year median did not improve the result:
- Healthy/high load factor: mean +1.39%, hit rate 42.9% (N=7)
- Lower load factor: mean +0.98%, hit rate 60.0% (N=5)

## Modern gate (2024-2026)

| Horizon | Load-factor regime | N | Mean Fast-Slow | Hit rate | Median | t-stat |
|---|---|---:|---:|---:|---:|---:|
| 3m | Improving | 7 | +4.19% | 57.1% | +0.93% | 0.94 |
| 3m | Not improving | 22 | +9.78% | 68.2% | +5.90% | 2.21 |
| 6m | Improving | 6 | +14.64% | 83.3% | +13.52% | 1.81 |
| 6m | Not improving | 20 | +18.39% | 85.0% | +13.71% | 4.90 |

The modern capacity signal remains strong regardless of whether industry load factor is improving. In fact, the point estimate is slightly larger in non-improving load-factor months. Therefore load-factor improvement does not explain the post-2023 strength of the capacity signal.

## Interpretation
The load-factor gate partially rehabilitates the older 2014-2019 result: fast capacity expansion looks better when industry seat utilization is improving. However, the effect is weak and sample-limited. More importantly, it fails to explain the much stronger 2024-2026 signal.

Conclusion: **load factor is not a sufficient regime variable and should not be promoted as the edge.**

The next falsification target should distinguish profitable/intentional capacity expansion from indiscriminate seat growth. Candidate variables should be economically upstream of realized equity returns and fixed before testing, such as carrier-specific RPM growth relative to ASM (load-factor change at the carrier level), pricing/yield/RASM if available point-in-time, or fuel-cost pressure. Do not optimize thresholds on the current sample.
