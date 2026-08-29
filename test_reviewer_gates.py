import pandas as pd

from airline_panel.reviewer_gates import gate16_membership_persistence, gate17_distress_confound


def test_gate16_detects_sticky_state():
    periods = pd.date_range("2024-01-01", periods=4, freq="MS")
    tickers = ["DAL", "UAL", "AAL", "LUV", "ALK", "JBLU"]
    rows = []
    values = {"DAL": 6, "UAL": 5, "AAL": 4, "ALK": 3, "LUV": 2, "JBLU": 1}
    for d in periods:
        for t in tickers:
            rows.append({"date": d, "ticker": t, "carrier_capacity_yoy": values[t]})
    result = gate16_membership_persistence(pd.DataFrame(rows))
    s = result.summary.iloc[0]
    assert s["unique_states_observed"] == 1
    assert s["full_state_month_to_month_change_rate"] == 0
    assert s["max_identical_state_run_months"] == 4


def test_gate16_detects_rotation():
    periods = pd.date_range("2024-01-01", periods=3, freq="MS")
    tickers = ["DAL", "UAL", "AAL", "LUV", "ALK", "JBLU"]
    rankings = [
        ["JBLU", "LUV", "ALK", "AAL", "UAL", "DAL"],
        ["DAL", "AAL", "UAL", "JBLU", "LUV", "ALK"],
        ["LUV", "ALK", "DAL", "UAL", "AAL", "JBLU"],
    ]
    rows = []
    for d, ranking in zip(periods, rankings):
        for v, t in enumerate(ranking, start=1):
            rows.append({"date": d, "ticker": t, "carrier_capacity_yoy": v})
    result = gate16_membership_persistence(pd.DataFrame(rows))
    assert result.summary.iloc[0]["unique_states_observed"] == 3
    assert result.summary.iloc[0]["full_state_month_to_month_change_rate"] == 1


def test_gate17_runs_and_returns_leave_one_out():
    periods = pd.period_range("2024-01", periods=8, freq="M")
    tickers = ["DAL", "UAL", "AAL", "LUV", "ALK", "JBLU"]
    rows = []
    for i, p in enumerate(periods):
        for j, t in enumerate(tickers):
            cap = (j - 2.5) / 10 + i / 100
            distress = (5 - j) / 10
            ret = 0.4 * cap - 0.2 * distress + (j % 2) / 100
            rows.append({"signal_period": str(p), "ticker": t, "carrier_capacity_yoy": cap,
                         "distress": distress, "ret_6m": ret})
    pooled, loo = gate17_distress_confound(pd.DataFrame(rows), distress_cols=["distress"])
    assert len(pooled) == 1
    assert len(loo) == 6
    assert "coef_carrier_capacity_yoy" in pooled.columns
