"""
Auditable two-state Gaussian Hidden Markov Model for MSP YoY traffic growth.

The model is deliberately narrow:
- one observed variable: YoY MSP enplanement growth;
- two latent regimes;
- Gaussian emissions;
- first-order Markov transitions;
- expanding-window, point-in-time fitting.

State labels are assigned after fitting:
    lower mean growth  -> "weak"
    higher mean growth -> "strong"

The implementation uses NumPy only. Baum-Welch EM estimates initial-state
probabilities, the transition matrix, state means, and state variances.
Forecasting propagates the filtered state probabilities through the Markov
transition matrix and converts expected future YoY growth into an enplanement
forecast relative to the known same-month prior-year base.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math

import numpy as np
import pandas as pd

from msp_availability import available_as_of


EPS = 1e-12
MIN_VAR = 1e-6


@dataclass(frozen=True)
class HMMFit:
    startprob: np.ndarray
    transmat: np.ndarray
    means: np.ndarray
    variances: np.ndarray
    log_likelihood: float
    iterations: int
    converged: bool


@dataclass(frozen=True)
class HMMNowcastResult:
    method: str
    as_of_date: str
    target_period: str
    forecast_enplanements: float
    forecast_yoy_growth: float
    prior_year_period: str
    prior_year_enplanements: float
    latest_known_period: str
    forecast_horizon_months: int
    weak_state_mean: float
    strong_state_mean: float
    weak_state_probability: float
    strong_state_probability: float
    transition_weak_to_weak: float
    transition_weak_to_strong: float
    transition_strong_to_weak: float
    transition_strong_to_strong: float
    training_observations: int
    iterations: int
    converged: bool

    def to_dict(self) -> dict:
        return asdict(self)


def _normal_pdf(x, mean, var):
    var = max(float(var), MIN_VAR)
    z = (x - mean) ** 2 / var
    return math.exp(-0.5 * z) / math.sqrt(2.0 * math.pi * var)


def _emission_matrix(obs, means, variances):
    matrix = np.empty((len(obs), len(means)), dtype=float)
    for t, value in enumerate(obs):
        for state in range(len(means)):
            matrix[t, state] = max(
                _normal_pdf(
                    float(value),
                    float(means[state]),
                    float(variances[state]),
                ),
                EPS,
            )
    return matrix


def _forward_scaled(obs, startprob, transmat, means, variances):
    emissions = _emission_matrix(obs, means, variances)
    n_obs, n_states = emissions.shape
    alpha = np.zeros((n_obs, n_states), dtype=float)
    scales = np.zeros(n_obs, dtype=float)

    alpha[0] = startprob * emissions[0]
    scales[0] = max(alpha[0].sum(), EPS)
    alpha[0] /= scales[0]

    for t in range(1, n_obs):
        alpha[t] = (alpha[t - 1] @ transmat) * emissions[t]
        scales[t] = max(alpha[t].sum(), EPS)
        alpha[t] /= scales[t]

    log_likelihood = float(np.log(scales).sum())
    return alpha, scales, emissions, log_likelihood


def _backward_scaled(emissions, scales, transmat):
    n_obs, n_states = emissions.shape
    beta = np.zeros((n_obs, n_states), dtype=float)
    beta[-1] = 1.0

    for t in range(n_obs - 2, -1, -1):
        beta[t] = transmat @ (emissions[t + 1] * beta[t + 1])
        beta[t] /= max(scales[t + 1], EPS)

    return beta


def _initial_parameters(obs):
    q35, q65 = np.quantile(obs, [0.35, 0.65])
    means = np.array([q35, q65], dtype=float)
    global_var = max(float(np.var(obs)), 1e-4)
    variances = np.array([global_var, global_var], dtype=float)
    startprob = np.array([0.5, 0.5], dtype=float)
    transmat = np.array([[0.80, 0.20], [0.20, 0.80]], dtype=float)
    return startprob, transmat, means, variances


def fit_gaussian_hmm(
    observations,
    *,
    max_iter=200,
    tol=1e-8,
    min_observations=8,
):
    """Fit a two-state univariate Gaussian HMM with Baum-Welch EM."""
    obs = np.asarray(observations, dtype=float)
    obs = obs[np.isfinite(obs)]

    if len(obs) < min_observations:
        raise ValueError(
            f"HMM requires at least {min_observations} known YoY observations; "
            f"only {len(obs)} are available."
        )
    if float(np.std(obs)) < 1e-8:
        raise ValueError("HMM cannot be fit to an effectively constant growth series.")

    startprob, transmat, means, variances = _initial_parameters(obs)
    previous_ll = -np.inf
    converged = False

    for iteration in range(1, max_iter + 1):
        alpha, scales, emissions, ll = _forward_scaled(
            obs, startprob, transmat, means, variances
        )
        beta = _backward_scaled(emissions, scales, transmat)

        gamma = alpha * beta
        gamma /= np.maximum(gamma.sum(axis=1, keepdims=True), EPS)

        xi_sum = np.zeros((2, 2), dtype=float)
        for t in range(len(obs) - 1):
            numer = (
                alpha[t][:, None]
                * transmat
                * (emissions[t + 1] * beta[t + 1])[None, :]
            )
            denom = max(numer.sum(), EPS)
            xi_sum += numer / denom

        startprob = gamma[0].copy()
        startprob /= max(startprob.sum(), EPS)

        row_sums = xi_sum.sum(axis=1, keepdims=True)
        transmat = xi_sum / np.maximum(row_sums, EPS)
        transmat = np.clip(transmat, 1e-6, 1.0)
        transmat /= transmat.sum(axis=1, keepdims=True)

        weights = gamma.sum(axis=0)
        means = (gamma * obs[:, None]).sum(axis=0) / np.maximum(weights, EPS)

        centered = obs[:, None] - means[None, :]
        variances = (
            gamma * centered * centered
        ).sum(axis=0) / np.maximum(weights, EPS)
        variances = np.maximum(variances, MIN_VAR)

        if abs(ll - previous_ll) < tol:
            converged = True
            break
        previous_ll = ll

    _, _, _, final_ll = _forward_scaled(
        obs, startprob, transmat, means, variances
    )

    # Canonical state order: lower growth mean first, higher growth mean second.
    order = np.argsort(means)
    startprob = startprob[order]
    means = means[order]
    variances = variances[order]
    transmat = transmat[np.ix_(order, order)]

    return HMMFit(
        startprob=startprob,
        transmat=transmat,
        means=means,
        variances=variances,
        log_likelihood=final_ll,
        iterations=iteration,
        converged=converged,
    )


def filtered_state_probabilities(observations, fit):
    """Return filtered probabilities for the final observed month."""
    obs = np.asarray(observations, dtype=float)
    alpha, _, _, _ = _forward_scaled(
        obs,
        fit.startprob,
        fit.transmat,
        fit.means,
        fit.variances,
    )
    return alpha[-1].copy()


def _month_gap(later, earlier):
    return (
        (later.year - earlier.year) * 12
        + (later.month - earlier.month)
    )


def hmm_regime_nowcast(
    df,
    as_of_date,
    target_period,
    *,
    min_observations=8,
    max_iter=200,
    tol=1e-8,
):
    """Generate a point-in-time HMM regime nowcast for an unpublished month."""
    known = available_as_of(df, as_of_date)
    if known.empty:
        raise ValueError("No verified MSP observations are available as of this date.")

    target = (
        target_period
        if isinstance(target_period, pd.Period)
        else pd.Period(target_period, freq="M")
    )

    if target in set(known["period"]):
        raise ValueError(f"Target {target} was already released as of this date.")

    prior = target - 12
    prior_row = known.loc[known["period"] == prior]
    if prior_row.empty:
        raise ValueError(
            f"Cannot forecast {target}: prior-year observation {prior} "
            "was not available as of the requested date."
        )
    prior_base = float(prior_row.iloc[-1]["enplanements"])

    growth = (
        known.dropna(subset=["yoy_change"])
        .sort_values("period")
        .reset_index(drop=True)
    )
    if growth.empty:
        raise ValueError("No known YoY growth observations are available.")

    observations = growth["yoy_change"].to_numpy(dtype=float)
    fit = fit_gaussian_hmm(
        observations,
        max_iter=max_iter,
        tol=tol,
        min_observations=min_observations,
    )

    latest_period = growth.iloc[-1]["period"]
    horizon = _month_gap(target, latest_period)
    if horizon < 1:
        raise ValueError("Target must be after the latest known YoY observation.")

    state_prob = filtered_state_probabilities(observations, fit)

    target_prob = state_prob.copy()
    for _ in range(horizon):
        target_prob = target_prob @ fit.transmat

    target_prob /= max(target_prob.sum(), EPS)
    forecast_growth = float(target_prob @ fit.means)
    forecast_enplanements = prior_base * (1.0 + forecast_growth)

    return HMMNowcastResult(
        method="hmm_regime",
        as_of_date=str(pd.Timestamp(as_of_date).date()),
        target_period=str(target),
        forecast_enplanements=float(forecast_enplanements),
        forecast_yoy_growth=forecast_growth,
        prior_year_period=str(prior),
        prior_year_enplanements=prior_base,
        latest_known_period=str(known["period"].max()),
        forecast_horizon_months=horizon,
        weak_state_mean=float(fit.means[0]),
        strong_state_mean=float(fit.means[1]),
        weak_state_probability=float(target_prob[0]),
        strong_state_probability=float(target_prob[1]),
        transition_weak_to_weak=float(fit.transmat[0, 0]),
        transition_weak_to_strong=float(fit.transmat[0, 1]),
        transition_strong_to_weak=float(fit.transmat[1, 0]),
        transition_strong_to_strong=float(fit.transmat[1, 1]),
        training_observations=len(observations),
        iterations=fit.iterations,
        converged=fit.converged,
    )
