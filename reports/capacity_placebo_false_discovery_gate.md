# Capacity Signal Placebo / False-Discovery Gate

## Objective
Test whether the modern 6-month fast-capacity-growth minus slow-capacity-growth spread is unusually strong under null randomization, while explicitly accounting for the heavy overlap in 6-month forward returns.

## Input
Validated modern 6-month spread series from `load_factor_gate_modern.csv`:
- 26 monthly signal observations
- 2024-01 through 2026-02 signal dates
- Mean spread: +17.52%
- Median spread: +13.71%
- Positive observations: 22 / 26 (84.6%)

The pre-COVID non-overlapping comparison series remains effectively null:
- Mean spread: +1.22%
- Positive observations: 6 / 12 (50%)

## Placebo tests

### 1. Observation-level direction randomization
Randomly flip the sign of each observed monthly spread while preserving its magnitude.

500,000 Monte Carlo sign-randomization draws:
- One-sided empirical p ~ 0.000006
- Two-sided empirical p ~ 0.000016

An exact sign-count test for 22 positives out of 26 gives:
- one-sided p = 0.000267
- two-sided p = 0.000534

This strongly rejects a simple independent-month no-direction null.

### 2. HAC / overlap-aware mean test
Because 6-month forward returns overlap, monthly observations are not independent. OLS on a constant with Newey-West/HAC covariance and 6 monthly lags gives:
- mean = +17.52%
- HAC t = 4.79
- p ~= 0.0000017

This remains strong, but HAC inference is asymptotic and the sample is only 26 months.

### 3. Conservative six-month block sign-flip placebo
To preserve the dependence induced by 6-month overlapping returns, partition the 26-month series into consecutive blocks of approximately one holding period and randomly flip whole block signs rather than individual months.

Using 6-month blocks yields 5 blocks. Every observed block has a positive mean. Enumerating all 2^5 possible block-sign patterns gives:
- one-sided p = 0.03125
- two-sided p = 0.0625

This is the most conservative placebo in the gate and is materially weaker than the naive monthly tests.

Sensitivity by block length:
- 3-month blocks: one-sided p = 0.00195
- 4-month blocks: one-sided p = 0.00781
- 5-month blocks: one-sided p = 0.01563
- 6-month blocks: one-sided p = 0.03125
- 7-8 month blocks: one-sided p = 0.0625

The inference therefore depends meaningfully on how aggressively we account for serial dependence.

### 4. Non-overlapping calendar-phase check
Take every sixth signal month to create six staggered non-overlapping 6-month holding sequences. Mean spreads by starting phase are:
- +14.22%
- +21.62%
- +26.99%
- +5.45%
- +16.21%
- +20.43%

All six phases are positive. This is encouraging stability evidence, but the six phase portfolios are not mutually independent because their underlying calendar holding windows overlap across phases, so this is not treated as a standalone p-value.

### 5. Out-of-regime placebo
The identical capacity-growth concept is effectively null in 2014-2019:
- mean +1.22%
- hit rate 50%
- prior t-stat ~0.34

This confirms the relationship is not a timeless airline-stock law and substantially raises the burden of proof for calling it a durable edge.

## False-discovery interpretation
The research path has examined multiple economically related hypotheses and transformations (airport traffic, divergence, demand, capacity, load factor, carrier absorption, PRASM, momentum, fleet growth, utilization, acceleration). The capacity signal was discovered during that search rather than specified before all analysis.

Therefore the smallest naive p-values should not be interpreted literally as discovery probabilities. A conservative research-path haircut is warranted. Under the strict 6-month block placebo, the one-sided result is ~3.1% and the two-sided result is ~6.3% before any explicit multiple-testing correction.

## Decision
**The placebo gate does not justify declaring a durable statistical edge.**

It does, however, leave a legitimate modern regime-specific anomaly/candidate signal:
- large economic magnitude
- high modern hit rate
- positive across all six non-overlapping calendar phases
- survives several economic confounder tests
- but weak/absent pre-COVID
- and only borderline under the most conservative overlap-preserving placebo.

Classification: **interesting regime signal / research candidate, not validated tradable edge.**

## Next admissible test
Do not add more features. The clean next step is genuine forward/out-of-sample validation: freeze the exact rule now and record future monthly signals/returns without changing the specification. A second option is to test the frozen rule on a genuinely untouched carrier universe or foreign airline panel, if comparable point-in-time capacity data can be obtained.
