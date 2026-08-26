# MSP Point-in-Time Data Foundation

This branch introduces a point-in-time MSP enplanement data layer for the
MSP/DAL research project.

## Why this exists

The original project used a rounded placeholder traffic series and implicitly
treated an observation month as if it were known at month-end. MAC traffic data
is released with a variable delay, so that assumption creates look-ahead bias.

The new rule is:

```text
MSP observation is usable only when release_date <= simulation as_of_date
```

Every future nowcast and DAL backtest should consume `available_as_of(...)`
rather than reading the full canonical MSP dataset directly.

## Canonical series

The canonical traffic variable is **MSP Grand Total enplanements**, extracted
from the Metropolitan Airports Commission annual **Enplanements by Concourse**
workbooks.

Current source workbooks:

- 2024 Enplanements by concourse.xlsx
- 2025 Enplanements by concourse.xlsx
- 2026 Enplanements by concourse.xlsx

Source page:

https://metroairports.org/msp-passenger-and-operations-reports

The current canonical CSV contains January 2024 through July 2026.

## Growth measure

The first research feature is year-over-year enplanement growth:

```text
YoY growth[t] = enplanements[t] / enplanements[t - 12] - 1
```

YoY growth is preferred to raw month-over-month change for the first benchmark
because MSP traffic has strong calendar seasonality.

## Release-date treatment

Release dates for 2025-2026 are taken from the MAC Monthly Operations Report
page. Historical 2024 website timestamps appear to include later bulk updates,
so those dates are intentionally left unverified.

Unverified observations are excluded from point-in-time simulations by default.
We will reconstruct older original release dates separately before expanding the
historical walk-forward sample.

Examples:

- As of 2026-05-01, January 2026 is the latest knowable observation.
- February and March 2026 both become available on 2026-05-15.
- April 2026 becomes available on 2026-06-02.
- July 2026 becomes available on 2026-08-25.

## Temporal firewall

`msp_availability.py` provides:

- `load_msp_actuals()`
- `available_as_of()`
- `unavailable_as_of()`
- `latest_known_period()`
- `information_gap_months()`
- `point_in_time_snapshot()`

Rows with missing/unverified release dates remain hidden unless the caller
explicitly opts into diagnostic-only `allow_unverified=True`.

## Tests

`test_msp_availability.py` contains look-ahead protection tests covering known
2026 release delays. These tests are intended to fail if future code exposes an
MSP observation before its publication date.

Run:

```bash
pytest -q test_msp_availability.py
```

The standalone prototype passed all seven tests before integration into this
branch.

## Research sequence from here

Do **not** optimize the MSP model on DAL returns yet.

First evaluate MSP nowcasting out of sample using information available at each
historical date:

1. seasonal-naive / prior-year-month benchmark;
2. recent YoY-trend benchmark;
3. autoregressive or seasonal statistical benchmark;
4. Hidden Markov Model regime estimate;
5. compare forecast errors walk-forward.

Only after the MSP methodology is selected and frozen should its nowcast enter
the DAL backtest. That separation reduces the risk of choosing an MSP model
because it happens to maximize historical DAL performance.
