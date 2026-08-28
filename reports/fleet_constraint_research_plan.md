# Fleet / aircraft-supply constraint gate

## Why this test exists
The carrier-capacity signal is weak pre-COVID but strong in the post-2020 period. A plausible structural explanation is that aircraft and labor became scarcer after COVID, so the *ability* to grow ASM became more informative.

## Primary data source
BTS Form 41 Schedule B-43 Inventory (annual, 2006-present). The table contains one row per airframe with carrier identifiers, operating status, seats, manufacturer/model, manufacture year and acquisition date.

## Frozen variables (before return testing)
For each carrier-year:
- operating_aircraft_count: count of airframes with operating status = Y
- operating_seats: sum(NumberOfSeats) across operating airframes
- fleet_growth_yoy: YoY % change in operating_aircraft_count
- seat_capacity_growth_yoy: YoY % change in operating_seats
- avg_fleet_age: weighted/mean aircraft age using ManufactureYear
- new_aircraft_share: share of operating aircraft manufactured in the prior 3 years

## Structural hypothesis
Capacity growth should be more informative when fleet supply is constrained. The first gate will compare fast-ASM growers that also have positive fleet/seat-capacity growth versus fast-ASM growers whose ASM growth is achieved without fleet expansion.

Economic interpretation:
- ASM growth + fleet growth may indicate access to scarce aircraft, delivery slots, financing, crews, and network confidence.
- ASM growth without fleet growth may reflect utilization/scheduling changes rather than a structural supply advantage.

## Timing discipline
B-43 is annual and released with a lag. We will use the prior calendar-year B-43 inventory as available information for the subsequent year unless historical release dates allow a more precise point-in-time rule. No current-year inventory will be used before its public release.

## Return gates
Use the existing six-airline universe and the already frozen 6-month forward excess-return framework.
1. Cross-sectional fast-vs-slow ASM growth spread conditional on fleet growth positive vs non-positive.
2. Repeat using operating-seat growth.
3. Compare pre-COVID (2014-2019) and modern (2022-2026) regimes without changing thresholds.
4. Do not optimize cutoffs after seeing returns.

## Failure rule
If fleet/seat-capacity growth does not materially differentiate the pre-COVID and modern signal, reject the fleet-scarcity explanation and move to labor/financial-capacity or expectations data rather than adding more fleet variables.
