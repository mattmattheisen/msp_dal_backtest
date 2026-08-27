import pandas as pd
import pytest

from msp_release_reconstruction import (
    classify_site_update_candidates,
    promote_verified_release_date,
    release_lag_days,
)


def test_release_lag_days():
    assert release_lag_days("2024-12", "2025-01-28") == 28


def test_bulk_refresh_dates_are_not_backtest_eligible():
    df = pd.DataFrame({
        "period": ["2024-01", "2024-02", "2024-03", "2024-12"],
        "site_updated_date": [
            "2025-01-24",
            "2025-01-24",
            "2025-01-24",
            "2025-01-28",
        ],
    })
    out = classify_site_update_candidates(df)

    jan = out[out["period"].astype(str) == "2024-01"].iloc[0]
    dec = out[out["period"].astype(str) == "2024-12"].iloc[0]

    assert jan["reconstruction_status"] == "bulk_refresh"
    assert not bool(jan["backtest_eligible"])
    assert dec["reconstruction_status"] == "plausible_candidate"
    assert not bool(dec["backtest_eligible"])


def test_verified_date_requires_evidence():
    df = pd.DataFrame({
        "period": pd.PeriodIndex(["2024-12"], freq="M"),
        "site_updated_date": pd.to_datetime(["2025-01-28"]),
        "release_date": pd.to_datetime([None]),
        "reconstruction_status": ["plausible_candidate"],
        "backtest_eligible": [False],
    })

    with pytest.raises(ValueError, match="evidence_source"):
        promote_verified_release_date(
            df,
            "2024-12",
            "2025-01-28",
            evidence_source="",
        )


def test_verified_date_can_be_promoted_with_evidence():
    df = pd.DataFrame({
        "period": pd.PeriodIndex(["2024-12"], freq="M"),
        "site_updated_date": pd.to_datetime(["2025-01-28"]),
        "release_date": pd.to_datetime([None]),
        "reconstruction_status": ["plausible_candidate"],
        "backtest_eligible": [False],
    })

    out = promote_verified_release_date(
        df,
        "2024-12",
        "2025-01-28",
        evidence_source="archived MAC snapshot",
    )
    row = out.iloc[0]
    assert row["reconstruction_status"] == "verified_original"
    assert bool(row["backtest_eligible"])
    assert row["release_date"] == pd.Timestamp("2025-01-28")
