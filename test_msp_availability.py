"""Tests for MSP point-in-time availability and look-ahead protection."""

import pandas as pd
import pytest

from msp_availability import (
    available_as_of,
    information_gap_months,
    latest_known_period,
    load_msp_actuals,
    unavailable_as_of,
)


@pytest.fixture
def df():
    return load_msp_actuals()


def periods(frame):
    return set(frame["period"].astype(str))


def test_may_1_2026_cannot_see_february_or_march(df):
    known = available_as_of(df, "2026-05-01")
    known_periods = periods(known)

    assert "2026-01" in known_periods
    assert "2026-02" not in known_periods
    assert "2026-03" not in known_periods
    assert latest_known_period(df, "2026-05-01") == pd.Period("2026-01", freq="M")
    assert information_gap_months(df, "2026-05-01") == 4


def test_release_day_is_inclusive(df):
    before = periods(available_as_of(df, "2026-05-14"))
    release_day = periods(available_as_of(df, "2026-05-15"))

    assert "2026-02" not in before
    assert "2026-03" not in before
    assert "2026-02" in release_day
    assert "2026-03" in release_day


def test_april_2026_hidden_until_june_2(df):
    assert "2026-04" not in periods(available_as_of(df, "2026-06-01"))
    assert "2026-04" in periods(available_as_of(df, "2026-06-02"))


def test_july_2026_hidden_until_august_25(df):
    assert "2026-07" not in periods(available_as_of(df, "2026-08-24"))
    assert "2026-07" in periods(available_as_of(df, "2026-08-25"))


def test_unverified_2024_release_dates_are_excluded_by_default(df):
    known = available_as_of(df, "2025-12-31")
    assert not any(p.startswith("2024-") for p in known["period"].astype(str))


def test_unavailable_contains_future_releases(df):
    hidden = periods(unavailable_as_of(df, "2026-05-01"))

    assert "2026-02" in hidden
    assert "2026-03" in hidden
    assert "2026-07" in hidden


def test_dataset_has_no_duplicate_periods(df):
    assert not df["period"].duplicated().any()
