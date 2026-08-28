# Capacity x Pricing-Power Gate

## Frozen hypothesis
Fast airline capacity expansion should be more informative when unit passenger revenue is stable or improving. Unit pricing is measured as quarterly PRASM = scheduled passenger revenue / ASM. Passenger revenue comes from BTS Form 41 Schedule P-1.2; ASM comes from BTS T1, service class F, summed across regions. The 2010 duplicate P-1.2 file is deduplicated. To preserve point-in-time discipline, quarterly PRASM is treated as available three months after quarter-end.

The cross-sectional portfolio remains the previously defined two fastest capacity growers minus the two slowest growers, with six-month forward relative return.

## Pre-COVID: 2014-2019 non-overlapping starts
Classifying a start as favorable when the average YoY PRASM change of the two fastest capacity growers is >= 0:

- Favorable pricing: n=3, average six-month fast-minus-slow spread = +1.57%, hit rate = 66.7%.
- Unfavorable pricing: n=9, average spread = +1.10%, hit rate = 44.4%.
- Difference = +0.47 percentage points.
- Welch test p ~= 0.96. This is no meaningful separation.

Conclusion: improving PRASM does not rescue the pre-COVID capacity signal.

## Modern period: 2024-2026
Using the same information-lag rule and the existing monthly six-month capacity-spread series:

- Favorable pricing: n=5, average six-month spread = +34.55%, hit rate = 100%.
- Unfavorable pricing: n=21, average spread = +13.47%, hit rate = 81.0%.
- Difference = +21.09 percentage points.
- Welch test p ~= 0.018.
- HAC regression (maxlags=5) on the overlapping monthly series gives an estimated pricing-state increment of +21.09 percentage points; the small sample and repeated quarterly state observations mean this statistic should not be read as independent confirmation.

Conclusion: PRASM improvement appears to amplify the modern capacity effect, but it does not explain why the signal failed in 2014-2019. Therefore it is not a stable cross-regime edge by itself.

## Research interpretation
The pricing-power hypothesis partially passes in the modern period and fails the historical robustness gate. This argues against promoting a capacity+PRASM rule to a trading signal. The strongest remaining hypothesis is that the post-2020 airline regime altered the information content of capacity decisions, potentially through constrained fleets, post-COVID network restructuring, labor/aircraft supply constraints, balance-sheet changes, or market-expectation dynamics.

## Stop rule
Do not tune PRASM thresholds, lags, carrier weights, or holding periods to improve this result. The next test should target a specific regime mechanism rather than optimize the observed split.
