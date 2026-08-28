# Carrier-Specific Absorption Gate

## Hypothesis

Capacity growth should be more informative when an airline's own revenue passenger miles (RPM) grow at least as fast as its available seat miles (ASM). Define carrier absorption as:

`absorption_gap = YoY(RPM) - YoY(ASM)`

For each signal date, rank the six airlines by YoY ASM growth. The pre-existing return test compares the two fastest capacity growers with the two slowest growers over the next six months. This gate asks whether that long-short spread is stronger when the two fast growers have positive carrier-specific absorption.

The same conservative three-month information lag used in earlier airline-panel gates is retained.

## Pre-COVID non-overlapping sample (2014-2019)

Using the 12 Jan/Jul six-month observations from the frozen pre-COVID gate:

- Fast-grower pair average absorption > 0: 7 observations; mean 6m fast-minus-slow spread **+3.33%**; median **-0.40%**; hit rate **42.9%**.
- Fast-grower pair average absorption <= 0: 5 observations; mean spread **-1.74%**; median **+7.20%**; hit rate **60.0%**.
- Continuous relationship between fast-grower average absorption and the six-month spread: Pearson r **+0.257** (p **0.421**); Spearman rho **+0.203** (p **0.527**).
- Welch difference-in-means test between positive and non-positive absorption states: p **0.541**.

Conclusion: carrier-specific absorption does not materially rescue the pre-COVID capacity signal.

## Modern sample (2024-2026)

Using the frozen monthly six-month spread series:

- Fast-grower pair average absorption > 0: 6 observations; mean spread **+7.67%**; median **+6.02%**; hit rate **66.7%**.
- Fast-grower pair average absorption <= 0: 20 observations; mean spread **+20.48%**; median **+15.27%**; hit rate **90.0%**.
- Continuous relationship between absorption and spread: Pearson r **-0.184** (p **0.368**); Spearman rho **-0.227** (p **0.265**).
- Welch difference-in-means test: p **0.147**.

This is the opposite of the proposed mechanism: the modern capacity signal was stronger when the fastest-growing airlines' RPM growth did *not* keep pace with ASM growth.

## Interpretation

Carrier-specific traffic absorption is not the missing explanatory variable. In the modern sample, requiring RPM growth to match capacity growth would actually discard many of the strongest capacity-signal observations. That weakens the "extra seats are good because they are immediately being filled" story.

The evidence is more consistent with capacity growth acting as a forward-looking management/network decision signal, or with another contemporaneous regime variable driving both capacity plans and subsequent equity performance.

## Research implication

Do not add carrier absorption as a positive filter. The next falsification should move to variables that can distinguish planned/confident expansion from financially destructive expansion before demand is realized. The most economically direct candidates are unit-revenue/pricing (RASM/PRASM or yield) and fuel-cost pressure. These should be tested one at a time, with the signal and cutoffs frozen before inspecting returns.
