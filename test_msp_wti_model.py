import numpy as np
import pandas as pd
import pytest

from msp_wti_model import trailing_return, expanding_oos, summarize_oos


def test_trailing_return():
    s = pd.Series(range(1, 30), dtype=float)
    expected = 29 / 8 - 1
    assert trailing_return(s, 21) == pytest.approx(expected)


def test_trailing_return_needs_history():
    assert np.isnan(trailing_return(pd.Series([1,2,3]), 21))


def synthetic_panel(n=60):
    rng = np.random.default_rng(7)
    traffic = rng.normal(size=n)
    wti = rng.normal(scale=0.1, size=n)
    interaction = traffic * wti
    y = 0.01 + 0.002 * traffic - 0.01 * wti + rng.normal(scale=0.03, size=n)
    return pd.DataFrame({
        "target_period": [f"m{i}" for i in range(n)],
        "traffic_z": traffic,
        "wti_21d": wti,
        "interaction": interaction,
        "dal_fwd_21d": y,
    })


def test_expanding_oos_has_four_models():
    out = expanding_oos(synthetic_panel(), ycol="dal_fwd_21d", min_train=36)
    assert set(out["model"]) == {
        "historical_mean",
        "traffic_only",
        "traffic_plus_wti",
        "traffic_wti_interaction",
    }


def test_expanding_oos_never_fits_on_test_row():
    panel = synthetic_panel()
    out = expanding_oos(panel, ycol="dal_fwd_21d", min_train=36)
    first = out[out["target_period"] == "m36"]
    assert len(first) == 4


def test_summary_metrics_are_finite():
    out = expanding_oos(synthetic_panel(), ycol="dal_fwd_21d", min_train=36)
    summary = summarize_oos(out)
    assert summary["rmse"].notna().all()
    assert summary["mae"].notna().all()
