# MSP HMM / Markov Regime Model

## Purpose

This module tests whether a latent traffic-regime model can improve point-in-time nowcasts of unpublished MSP enplanements.

The HMM is evaluated as an **experimental challenger**, not promoted into the DAL signal simply because it is more sophisticated.

## Observed variable

The model uses year-over-year MSP enplanement growth rather than raw monthly traffic levels:

`g[t] = E[t] / E[t-12] - 1`

This removes most of the airport's recurring seasonal pattern before regime estimation.

## Latent-state model

The current implementation uses a two-state univariate Gaussian Hidden Markov Model:

- State 0: lower-mean YoY growth (labeled **weak** after fitting)
- State 1: higher-mean YoY growth (labeled **strong** after fitting)

The state process follows a first-order Markov chain:

`P(S[t] | S[t-1])`

and observed YoY traffic growth is Gaussian conditional on the hidden state.

The model estimates the initial-state probabilities, transition matrix, state means, and state variances with Baum-Welch expectation-maximization.

## Why two states instead of three

The verified point-in-time history is still short. A three-state contraction / normal / expansion model would currently be too easy to overfit. The two-state model is intentionally conservative until additional historical release dates are reconstructed.

## Point-in-time rule

Every fit is expanding-window and passes through `available_as_of()`.

For each historical target month:

1. Set the information cutoff to one day before the verified MAC release.
2. Hide the target observation and all later observations.
3. Fit the HMM only to YoY growth values that were actually known by that cutoff.
4. Filter the probability of the current hidden state.
5. Propagate that state distribution through the transition matrix for each missing month.
6. Compute expected target YoY growth from the forecast state probabilities.
7. Apply that growth forecast to the known same-month prior-year enplanement count.
8. Reveal the actual only for scoring.

For a target month `t`:

`E_hat[t] = E[t-12] * (1 + g_hat[t])`

where `g_hat[t]` is the HMM probability-weighted expected growth rate.

## Current strict walk-forward results

Eligible sample: January through July 2026.

| Model | N | MAE | MAPE | RMSE | Bias |
|---|---:|---:|---:|---:|---:|
| Seasonal naive | 7 | 30,881 | **2.08%** | 45,974 | +30,881 |
| Recent YoY trend | 7 | 30,000 | 2.16% | 32,900 | -20,826 |
| AR(1) YoY | 7 | 35,204 | 2.32% | 39,027 | -16,925 |
| HMM regime | 7 | 37,374 | 2.49% | 40,813 | -20,892 |

The HMM **does not beat the current seasonal-naive hurdle** on this sample.

That result is retained deliberately. The goal is to determine whether the method adds real forecasting value, not optimize until the Markov model wins.

## March 2026 example

Using only information available on May 1, 2026:

- latest known MSP period: January 2026
- forecast horizon: two months
- training observations: 13 known YoY growth observations
- weak-state mean growth: approximately -4.41%
- strong-state mean growth: approximately -0.03%
- forecast probability of weak state: approximately 74.5%
- forecast probability of strong state: approximately 25.5%
- HMM forecast: approximately 1,585,768 enplanements
- eventual actual: 1,528,083

The HMM missed high by roughly 3.8% for that observation.

## Important limitation

With the current short sample, transition estimates can become extreme or unstable. This is a warning against interpreting the inferred regimes economically too literally yet. The next major improvement is not parameter tuning; it is extending the verified historical release calendar and therefore the true point-in-time training history.

## Files

- `msp_hmm.py` — NumPy implementation of the Gaussian HMM and point-in-time nowcast
- `msp_hmm_walk_forward.py` — strict historical evaluator
- `test_msp_hmm.py` — probability, leakage, release-date, and walk-forward tests

The HMM remains isolated from the production benchmark stack until it demonstrates out-of-sample improvement.
