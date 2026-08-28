# Capacity signal vs prior price momentum

## Question
Is the strong modern (2024-2026) capacity-growth signal simply a disguised price-momentum effect?

## Frozen test
- Universe: DAL, UAL, AAL, LUV, ALK, JBLU.
- Capacity signal: YoY carrier ASM growth with the existing conservative 3-month information lag.
- Each month: top two capacity growers = Fast; bottom two = Slow.
- Outcome: 6-month forward airline return spread (Fast minus Slow).
- Confounder: prior 6-month stock-price momentum measured at the signal date.
- Cross-sectional regression uses monthly standardized capacity growth and prior 6-month momentum; standard errors clustered by signal month.

## Results
The fast-capacity group usually had already outperformed before the signal date: its prior 6-month momentum exceeded the slow group in 18 of 20 usable signal months (90%), with an average prior-momentum advantage of about +23.2 percentage points.

However, prior momentum does not explain the subsequent capacity effect.

In the cross-sectional regression of 6-month forward excess return on both capacity growth and prior 6-month momentum:
- standardized capacity-growth coefficient: +0.0631 (about +6.3 percentage points per 1 cross-sectional standard deviation)
- clustered z-statistic: 3.94
- p-value: <0.001
- prior 6-month momentum coefficient: approximately -0.0001
- momentum p-value: 0.995

The capacity effect also remained positive in the two months when the fast-capacity group had *not* already been outperforming. Those two observations are far too few for inference, but they argue against a mechanically momentum-driven construction.

## Interpretation
The modern capacity signal is correlated with prior price strength, but the forward-return relationship remains after controlling for that strength. Within this small modern sample, capacity growth contains cross-sectional information that is not captured by ordinary 6-month price momentum.

## Caveats
- Modern sample only; usable regression window is July 2024 through February 2026 because six months of prior momentum and six months of forward returns are both required.
- Six-stock cross section is small.
- This does not prove causality or a durable tradable edge.
- The critical regime-break problem remains: standalone capacity growth failed the 2014-2019 pre-COVID gate.

## Decision
**Momentum confound gate: passed provisionally.** Do not discard the modern capacity signal as simple momentum. Next research should focus on explaining the post-2020 structural regime rather than adding generic technical indicators.
