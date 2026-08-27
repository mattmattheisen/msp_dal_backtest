# SPY-adjusted MSP / DAL results

## Question

Does the MSP traffic signal become more informative when broad-market returns
are removed from DAL?

For each forward horizon:

    DAL excess return = DAL adjusted-close return - SPY adjusted-close return

DAL and SPY are aligned on the same trading dates before forward returns are
computed.

## Preserved feature specification

No feature is retuned for this section.

- MSP signal: existing exploratory pseudo-real-time traffic z-score.
- WTI: trailing 21-observation DCOILWTICO return.
- Interaction: MSP traffic z-score x WTI return.
- Structural-break years 2020-2022 remain excluded from the exploratory panel.
- Expanding-window out-of-sample testing begins after 36 prior monthly signals.

## Correlation results

| Horizon | N | MSP vs DAL | MSP vs SPY | MSP vs DAL excess | WTI vs DAL excess |
|---|---:|---:|---:|---:|---:|
| 1d | 78 | -0.189 | -0.052 | -0.212 | +0.095 |
| 5d | 78 | +0.029 | +0.046 | +0.010 | -0.070 |
| 21d | 77 | -0.036 | +0.045 | -0.061 | -0.126 |
| 63d | 75 | -0.036 | +0.139 | -0.106 | +0.033 |
| 126d | 72 | -0.167 | +0.115 | -0.251 | -0.078 |

## Expanding-window out-of-sample RMSE

| Horizon | Historical mean | Traffic only | Traffic + WTI | Traffic + WTI + interaction |
|---|---:|---:|---:|---:|
| 1d | 2.06% | 2.01% | 2.14% | 2.26% |
| 5d | 4.91% | 5.02% | 5.15% | 5.34% |
| 21d | 10.70% | 11.03% | 11.06% | 12.07% |
| 63d | 18.57% | 20.24% | 20.58% | 20.21% |
| 126d | 20.91% | 23.83% | 23.95% | 23.18% |

## Result

Subtracting SPY does not reveal a hidden MSP signal.

At 5 trading days, the historical-mean excess-return benchmark has RMSE of
approximately 4.91%, versus 5.02% for traffic-only and 5.15% for traffic + WTI.

At 21 days, the historical mean is approximately 10.70%, versus 11.03% for
traffic-only and 11.06% for traffic + WTI.

At 63 days, the historical mean is approximately 18.57%, versus 20.24% for
traffic-only and 20.58% for traffic + WTI.

At 126 days the MSP signal's raw correlation with DAL excess return reaches
about -0.25, but the expanding-window traffic model still materially
underperforms the historical-mean benchmark. The sign therefore should not be
interpreted as a validated predictive effect.

The 1-day traffic-only model modestly improves RMSE versus the historical mean
(about 2.01% versus 2.06%), but the magnitude is small and does not persist
across longer horizons.

## Interpretation

The negative conclusion survives three increasingly demanding formulations:

1. MSP signal versus raw DAL returns;
2. MSP + WTI versus raw DAL returns;
3. MSP + WTI versus DAL returns after subtracting SPY.

The next defensible extension is an airline-relative benchmark or airline
factor, rather than further tuning the MSP or WTI windows.
