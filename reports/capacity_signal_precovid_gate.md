# Capacity Signal Pre-COVID Gate

## Question
Does the modern finding — faster airline capacity growth predicting stronger subsequent relative returns — survive a clean pre-COVID period?

## Frozen specification
- Universe: AAL, ALK, DAL, JBLU, LUV, UAL
- Signal: carrier ASM YoY growth only
- Information lag: 3 months
- Portfolio: top 2 capacity growers minus bottom 2 capacity growers
- Horizon: 6 months
- Sampling for this gate: non-overlapping semiannual starts (January and July)
- Test window: January 2014 through July 2019
- Price source for this historical gate: Digrin monthly adjusted prices

## Results
| Signal date | Fast growers 6m | Slow growers 6m | Fast - Slow |
|---|---:|---:|---:|
| 2014-01 | 28.96% | 19.46% | 9.51% |
| 2014-07 | 58.47% | 38.09% | 20.38% |
| 2015-01 | -3.65% | -18.33% | 14.68% |
| 2015-07 | -1.15% | -8.36% | 7.21% |
| 2016-01 | -6.09% | -7.41% | 1.32% |
| 2016-07 | 16.15% | 36.72% | -20.57% |
| 2017-01 | 9.18% | 9.92% | -0.74% |
| 2017-07 | 2.56% | 12.30% | -9.74% |
| 2018-01 | -8.56% | 7.35% | -15.91% |
| 2018-07 | 5.65% | -5.45% | 11.10% |
| 2019-01 | 3.53% | 5.84% | -2.30% |
| 2019-07 | -2.44% | -2.00% | -0.44% |

Mean Fast-minus-Slow spread: **+1.21% per six months**.

Positive observations: **6 of 12 (50%)**.

Simple non-overlapping t-statistic: **0.34**; two-sided p-value: **0.74**.

## Interpretation
The pre-COVID gate does **not** support a stable, timeless capacity-growth edge. The modern 2024–2026 effect is not reproduced in 2014–2019 under the same economic idea and a non-overlapping six-month test.

The result does, however, suggest regime dependence: the signal was positive in several 2014–2016 observations and then weakened/reversed in much of 2016–2019. That makes a conditional hypothesis more defensible than an unconditional one.

## Research decision
Reject the claim that `higher ASM YoY growth -> higher six-month airline excess return` is a universal standalone rule.

Do not optimize thresholds or add arbitrary indicators to rescue it. If research continues, the next falsifiable question should be whether capacity growth has predictive value only under a pre-specified industry state such as demand acceleration, fuel pressure, or post-capacity-retrenchment recovery.
