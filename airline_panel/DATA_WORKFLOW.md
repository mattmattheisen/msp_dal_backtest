# BTS T1 data workflow

## Phase 1 source

Use the Bureau of Transportation Statistics / TranStats table:

**T1: U.S. Air Carrier Traffic And Capacity Summary by Service Class**

Select at minimum these fields:

- Year
- Month
- UniqueCarrier
- ServiceClass
- RevPaxMiles
- RevPaxEnplaned
- AvailSeatMiles

For the first experiment, retain service class **F** only. Do not add aggregate service classes such as K or Z to their component classes; doing so can double count traffic/capacity.

## Why T1

T1 is already a monthly carrier-level summary and contains the two core Phase-1 quantities directly:

- `RevPaxMiles` -> demand proxy (RPM)
- `AvailSeatMiles` -> capacity proxy (ASM)

The initial six-stock universe is DL, UA, AA, WN, AS, and B6. Industry demand is calculated using all carriers present in the raw T1 snapshot, not only those six names.

## Raw-file rule

Never edit the BTS download in place. Save each downloaded file unchanged under a dated vintage name such as:

`data/bts_t1/raw/t1_2026-08-13.csv`

The date in the filename is the date the BTS vintage became available, not the month measured by the observations.

## Point-in-time rule

A backtest observation may only use a T1 row after that row was available to the public. BTS traffic data are released with a material lag, so measured month and usable date are different things.

During initial development, `apply_publication_lag()` can attach a conservative 75-day assumed availability date. That is only a scaffold. Before return testing, the preferred workflow is to join the historical BTS release calendar or reconstruct immutable data vintages and use the actual release date.

## Phase-1 signal

For carrier i in month t:

`industry_demand_yoy[t] = YoY(aggregate industry RPM)`

`carrier_capacity_yoy[i,t] = YoY(carrier ASM)`

`dc_gap[i,t] = industry_demand_yoy[t] - carrier_capacity_yoy[i,t]`

Positive gap: industry demand is expanding faster than the carrier's capacity.
Negative gap: the carrier is adding capacity faster than industry demand.

Do not optimize weights or thresholds before the first cross-sectional return test.
