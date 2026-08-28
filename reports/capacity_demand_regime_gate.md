# Capacity × Demand Regime Gate

## Question

Does carrier capacity expansion work better as an airline-stock signal when industry demand is accelerating?

This is a conditional falsification test motivated by the failure of capacity growth as a standalone pre-COVID signal.

## Frozen rule

- Carrier signal: YoY carrier ASM growth.
- Portfolio: two fastest capacity growers minus two slowest capacity growers.
- Information lag: 3 months from BTS operating month to signal month.
- Forward horizon: 6 months.
- Industry-demand state: BTS industry RPM YoY growth is **accelerating** if it is greater than its value 3 months earlier. This state variable is common to all carriers and therefore only acts as a regime filter; it does not affect the cross-sectional ranking.
- No threshold optimization was performed after viewing returns.

## Pre-COVID first gate

Using the 12 non-overlapping Jan/Jul six-month observations from 2014–2019:

| Industry demand state | N | Mean fast-minus-slow | Median | Positive hit rate |
|---|---:|---:|---:|---:|
| Accelerating | 8 | **+4.83%** | **+8.35%** | **75%** |
| Not accelerating | 4 | **-6.00%** | **-1.50%** | **0%** |

Welch comparison of the two small samples: p ≈ 0.139. Fisher exact test on positive/negative outcomes: p ≈ 0.061.

The sample is too small to claim significance, but the direction is economically coherent and materially different from the unconditional 2014–2019 result (+1.2%, 50% hit rate).

## Modern-period check

For the 2024–2026 monthly six-month signal, capacity expansion was strong in both demand states:

- demand accelerating: mean fast-minus-slow ≈ **+16.27%**, positive in **88.9%** of observations;
- demand not accelerating: mean fast-minus-slow ≈ **+18.18%**, positive in **82.4%** of observations.

So simple 3-month demand acceleration does **not** explain why the modern signal is so strong. It appears useful as a pre-COVID regime filter, but the modern regime contains an additional structural driver.

## Interpretation

The current evidence supports a narrower hypothesis:

> Capacity expansion may contain information when demand conditions are favorable, but the post-2023 effect is too strong to attribute to demand acceleration alone.

This keeps the regime hypothesis alive while rejecting the idea that one simple demand filter fully explains the signal.

## Next falsification

Before adding fuel, options, or optimized thresholds, test whether the signal is conditioned by **industry pricing power / load factor** rather than passenger-demand acceleration alone. A capacity increase is economically healthy only if the added seats are being absorbed without destroying yields. The next candidate should therefore use a pre-specified BTS measure such as industry load factor or RPM growth relative to ASM growth, with the same frozen carrier-capacity ranking and 6-month forward excess-return test.
