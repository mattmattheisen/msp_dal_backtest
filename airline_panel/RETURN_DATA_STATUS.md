# Phase 1 return-data status

## Market data source
A connected Alpaca market-data feed was queried for DAL, UAL, AAL, LUV, ALK, and JBLU. The IEX feed returned complete monthly bars for all six names from July 2020 through August 2026 (444 bars; 74 per symbol). This is sufficient for a modern-period preliminary gate but not the intended 2010+ long-history test.

The long-history result must not be inferred from the shorter IEX window. A 2010+ price source remains required before the Phase-1 hypothesis can receive a final pass/fail decision.

## Pre-return design correction: quintiles -> 2/2/2 groups
The research plan originally specified cross-sectional quintiles. With exactly six stocks per month, five quintiles are mechanically ill-posed and create uneven cells. Before examining any return results, the gate is corrected to:

- low demand-capacity gap: bottom 2 carriers each month
- middle: middle 2
- high demand-capacity gap: top 2
- retain continuous 1..6 / percentile rank for rank-correlation tests

This is a mechanical design correction, not return-driven optimization.

## Timing
The BTS signal remains unavailable until its assumed/verified publication date. Monthly price tests must enter only after that date. The monthly-bar implementation is an approximation to the pre-specified 21/63/126-session horizons; a daily-price long-history feed is preferred for the final gate.

## Decision rule
Do not call an edge from the modern-period test alone. A candidate must show economically coherent ordering (high > middle > low in subsequent excess returns), reasonable stability across 1/3/6 month horizons, and survive the longer 2010+ sample and COVID/reopening subperiod checks.
