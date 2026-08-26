# MSP AR(1) YoY Statistical Benchmark

## Purpose

Add a simple statistical benchmark before introducing a Hidden Markov Model. The HMM should not be judged only against naive rules; it should also have to beat a conventional time-series model.

## Model

The model is fit to year-over-year MSP enplanement growth rather than raw traffic levels:

```text
g[t] = alpha + phi * g[t-1] + epsilon[t]
```

The traffic forecast is then:

```text
E_hat[t] = E[t-12] * (1 + g_hat[t])
```

where `E[t-12]` is the same month one year earlier.

## Point-in-time discipline

The AR(1) model receives only observations allowed through `available_as_of(...)`.

At every walk-forward date:

1. The information cutoff is one calendar day before MAC publishes the target observation.
2. The AR coefficients are re-fit using an expanding window of only known YoY growth observations.
3. Only consecutive monthly YoY observations are used as AR pairs.
4. If the target is more than one month beyond the latest known traffic month, the AR forecast is recursively propagated through the information gap.
5. The target actual is joined only after the forecast is generated.

This avoids fitting the AR process on future observations and avoids using final historical state information in earlier forecasts.

## Current strict walk-forward results

Eligible sample: January through July 2026. This is intentionally small because older release dates have not yet been reconstructed with sufficient confidence.

| Method | N | MAE | MAPE | RMSE | Bias |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seasonal naive | 7 | 30,881 | **2.08%** | 45,974 | +30,881 |
| Recent YoY trend | 7 | **30,000** | 2.16% | **32,900** | -20,826 |
| AR(1) YoY | 7 | 35,204 | 2.32% | 39,027 | -16,925 |

The AR(1) model does **not** beat seasonal naive on MAPE in the current sample. It remains in the benchmark suite because negative results are informative and because future expansion of the verified release-date history may change the ranking.

## Interpretation

The current hurdle remains seasonal naive at approximately 2.08% MAPE.

The purpose of the next HMM/regime model is not merely to produce a more sophisticated forecast. It must demonstrate lower out-of-sample error than these simpler alternatives under the same point-in-time rules.

## Caveat

Seven observations are not enough to make a strong statistical claim about relative model quality. The immediate research priority remains reconstruction of older MAC publication dates so the walk-forward sample can be expanded materially.
