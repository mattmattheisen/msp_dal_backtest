import numpy as np
import pandas as pd
import pytest

from msp_availability import load_msp_actuals
from msp_hmm import (
    filtered_state_probabilities,
    fit_gaussian_hmm,
    hmm_regime_nowcast,
)
from msp_hmm_walk_forward import summarize_hmm, walk_forward_evaluate_hmm


@pytest.fixture
def df():
    return load_msp_actuals()


def test_hmm_fit_has_valid_probabilities():
    obs = np.array([
        -0.06, -0.05, -0.04, -0.03, 0.02,
        0.03, 0.04, 0.05, 0.04, 0.03,
    ])
    fit = fit_gaussian_hmm(obs, min_observations=8)

    assert np.isclose(fit.startprob.sum(), 1.0)
    assert np.allclose(fit.transmat.sum(axis=1), 1.0)
    assert fit.means[0] <= fit.means[1]
    assert np.all(fit.variances > 0)


def test_filtered_probabilities_sum_to_one():
    obs = np.array([
        -0.06, -0.05, -0.04, -0.03, 0.02,
        0.03, 0.04, 0.05, 0.04, 0.03,
    ])
    fit = fit_gaussian_hmm(obs, min_observations=8)
    probabilities = filtered_state_probabilities(obs, fit)

    assert np.isclose(probabilities.sum(), 1.0)
    assert np.all(probabilities >= 0)


def test_point_in_time_hmm_march_2026(df):
    result = hmm_regime_nowcast(df, "2026-05-01", "2026-03")

    assert result.latest_known_period == "2026-01"
    assert result.prior_year_period == "2025-03"
    assert result.forecast_horizon_months == 2
    assert result.training_observations >= 8
    assert result.forecast_enplanements > 0
    assert result.weak_state_mean <= result.strong_state_mean
    assert (
        result.weak_state_probability + result.strong_state_probability
        == pytest.approx(1.0)
    )


def test_hmm_rejects_released_target(df):
    with pytest.raises(ValueError, match="already released"):
        hmm_regime_nowcast(df, "2026-05-15", "2026-03")


def test_hmm_information_set_changes_on_release(df):
    before = hmm_regime_nowcast(df, "2026-05-14", "2026-04")
    after = hmm_regime_nowcast(df, "2026-05-15", "2026-04")

    assert before.latest_known_period == "2026-01"
    assert after.latest_known_period == "2026-03"
    assert before.training_observations < after.training_observations


def test_hmm_walk_forward_is_strictly_pre_release(df):
    results = walk_forward_evaluate_hmm(df)
    assert len(results) == 7
    assert (results["as_of_date"] < results["release_date"]).all()
    assert (results["method"] == "hmm_regime").all()


def test_hmm_summary_has_standard_metrics(df):
    summary = summarize_hmm(walk_forward_evaluate_hmm(df))
    assert summary["method"] == "hmm_regime"
    assert summary["n"] == 7
    assert summary["mae"] > 0
    assert summary["mape"] > 0
