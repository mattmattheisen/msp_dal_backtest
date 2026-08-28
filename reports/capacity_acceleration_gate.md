# Capacity Acceleration Gate

## Question
Does the *change* in YoY ASM growth contain more information than the level of YoY ASM growth?

We keep the existing point-in-time discipline: BTS operating data receive the same conservative three-month availability lag. We compare two acceleration definitions:

- 1-month acceleration = current YoY ASM growth minus prior month's YoY ASM growth
- 3-month acceleration = current YoY ASM growth minus YoY ASM growth three months earlier

The clean robustness gate uses non-overlapping 6-month return windows beginning in January and July, across the same six-carrier universe (DAL, UAL, AAL, LUV, ALK, JBLU). The portfolio spread is the average forward return of the top two carriers by signal minus the bottom two.

## Results

### Pre-COVID: Jan 2014-Jul 2019, 12 non-overlapping observations

| Signal | Mean 6m High-Low | Hit rate | t-stat | p-value | Mean rank IC |
|---|---:|---:|---:|---:|---:|
| YoY ASM growth level | +1.21% | 50.0% | 0.34 | 0.739 | +0.10 |
| 1m acceleration | +0.25% | 58.3% | 0.07 | 0.949 | -0.02 |
| 3m acceleration | -0.15% | 41.7% | -0.03 | 0.978 | +0.10 |

Acceleration does not rescue the pre-COVID period.

### Modern: Jan 2022-Jul 2025, 8 non-overlapping observations

| Signal | Mean 6m High-Low | Hit rate | t-stat | p-value | Mean rank IC |
|---|---:|---:|---:|---:|---:|
| YoY ASM growth level | +11.67% | 75.0% | 1.95 | 0.093 | +0.41 |
| 1m acceleration | -5.43% | 37.5% | -0.84 | 0.426 | +0.03 |
| 3m acceleration | +12.35% | 62.5% | 1.99 | 0.087 | +0.28 |

The 1-month acceleration signal clearly fails. Three-month acceleration produces a similar average spread to the level signal, but with a lower hit rate and weaker rank ordering. It therefore does not improve on simple capacity growth.

A joint modern cross-sectional regression using period-demeaned 6-month returns and cross-sectionally standardized predictors also does not establish 3-month acceleration as a superior replacement. Both capacity level and 3-month acceleration have positive coefficients, but with only eight semiannual clusters neither clears a conventional significance threshold when included together.

## Interpretation
The market does not appear to be rewarding the *latest monthly change* in capacity commitment. If there is a useful modern signal, it is closer to a persistent/high relative capacity-growth state than to a sharp one-month inflection.

Three-month acceleration may carry some incremental information, but the present evidence does not justify adding it to the model. Doing so would increase model complexity without a demonstrated robustness gain.

## Decision
**Reject 1-month acceleration. Do not promote 3-month acceleration to the core signal. Keep YoY relative ASM growth as the simpler primary candidate.**

The remaining research question is now less about mathematical transformations of ASM and more about whether the modern ASM-growth signal survives a stricter out-of-sample / placebo framework and whether it is concentrated in identifiable airline/network states.
