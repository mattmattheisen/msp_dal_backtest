# BTS T1 historical export specification

This file freezes the exact raw-data request for Phase 1 so the historical panel can be built without changing fields after returns are observed.

## Source
Bureau of Transportation Statistics (BTS) TranStats

Table: **T1: U.S. Air Carrier Traffic And Capacity Summary by Service Class**

Official download page:
`https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=Nv4+Pn44vr4+f7zzn4B&gnoyr_VQ=FJH`

## Required fields
Select only these fields for the core pull:

- Year
- Month
- UniqueCarrier
- UniqueCarrierName
- UniqCarrierEntity
- CarrierRegion
- ServiceClass
- RevPaxEnplaned
- RevPaxMiles
- AvailSeatMiles

Optional audit fields:

- AirlineID
- Carrier
- CarrierName
- RADPerformed

## Date range
Preferred first pull: **2010 through latest available month**.

Reason: this provides a long post-merger sample for Delta/United while avoiding unnecessary pre-2010 carrier-history complexity in the first experiment. If the Phase-1 effect survives, the sample can be extended backward with explicit merger/entity mapping.

## Universe
The downstream panel filters to:

- DL — Delta Air Lines
- UA — United Air Lines
- AA — American Airlines
- WN — Southwest Airlines
- AS — Alaska Airlines
- B6 — JetBlue Airways

Do **not** pre-filter the raw download to those carriers if the BTS interface makes an all-carrier export easier. The ingestion code performs carrier filtering after the raw file is preserved.

## Service-class rule
T1 contains aggregate service classes that are sums of detailed classes. The raw export must preserve `ServiceClass` so the loader can choose one mutually exclusive definition and prevent double counting.

For the initial test, the target economic concept is scheduled passenger service. The loader should prefer the BTS scheduled-service aggregate when present rather than summing an aggregate together with its components.

## Raw-file rule
Do not edit the BTS CSV in Excel before saving it to the repository.

Save the untouched export under:

`data/airline_panel/raw/t1/`

with a filename containing the download date, for example:

`T1_2010_2026_downloaded_2026-08-28.csv`

Then create a sidecar metadata file recording:

- source URL
- download timestamp
- represented start/end month
- whether the file is a current revised vintage or a historical archived vintage

## Point-in-time treatment
A current BTS historical download contains revised history and therefore is **not itself a vintage history**. Phase 1 will use it to construct the economic series, but each observation must still be shifted to an availability date.

Preferred hierarchy:

1. Verified BTS release-history date for the represented month.
2. If unavailable, conservative fixed lag (75 days after month-end), explicitly marked `availability_source = assumed_75d`.

No observation may be matched to an equity return before its availability date.

## Why this export is frozen now
The hypothesis, fields, universe, horizons, and quintile logic are being fixed before the historical returns are attached. This is intended to reduce researcher degrees of freedom and avoid turning the data pull itself into an optimization step.
