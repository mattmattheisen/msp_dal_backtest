# Airline panel: Phase 1 research plan

## Hypothesis
Airline equity returns may respond to the imbalance between industry passenger demand and carrier-specific capacity growth rather than passenger growth alone.

For carrier i and month t:

`demand_capacity_gap[i,t] = demand_yoy[t] - asm_yoy[i,t]`

The first test will ask whether higher demand-capacity gaps are associated with higher subsequent carrier excess returns at approximately 1, 3, and 6 month horizons.

## Universe
Initial research universe: DAL, UAL, AAL, LUV, ALK, JBLU. Carrier-history changes and survivorship issues must be documented before extending backward through mergers or delistings.

## Public data feasibility
### Capacity
Primary source: U.S. DOT Bureau of Transportation Statistics (BTS) TranStats T-100 / T1 carrier traffic and capacity data.

Useful fields include carrier, month/year, Available Seat Miles (ASM), Revenue Passenger Miles (RPM), passengers, and load factor. T1 is monthly, has carrier-level microdata, and begins in 1974; T-100 segment data begin in 1990.

Critical point-in-time rule: BTS states T-100 data are generally public about 10 weeks after the represented month. The TranStats release-history page provides explicit recent release dates and revision information. The panel must store an `available_date` and may not expose a month's capacity before that date.

### Demand
Candidate A: TSA national checkpoint throughput. TSA publishes daily passenger checkpoint counts and updates them Monday-Friday. This is attractive as a high-frequency contemporaneous demand proxy, but the readily accessible official history is strongest in the post-2019/2020 period.

Candidate B: BTS systemwide passenger/RPM data. This has much longer history but shares the roughly 10-week reporting lag with carrier capacity. It is therefore less timely but cleaner for a long historical point-in-time test.

## Recommended sequencing
1. Build the long-history monthly panel first using BTS demand and BTS carrier ASM. This maximizes sample size and gives both sides of the gap a common release framework.
2. Treat all observations as unavailable until their BTS release date; where exact historical release dates are unavailable, use a conservative fixed lag rather than the observation month.
3. Compute YoY demand growth and carrier ASM growth only from data available as of each signal date.
4. Form the demand-capacity gap without optimizing weights.
5. Rank carrier-month observations cross-sectionally and test predetermined quintiles.
6. Measure 21-, 63-, and 126-trading-day forward carrier returns and excess returns versus an equal-weight airline basket.
7. Require monotonicity/stability across quintiles and time subperiods before adding fuel or options variables.
8. After the long-history test, run a higher-frequency TSA-demand variant over the shorter period as a separate robustness/nowcasting experiment.

## Why not airport traffic
The MSP work showed that individual-airport traffic adds geographic noise and creates difficult historical publication-date reconstruction. Phase 1 deliberately avoids collecting multiple airport-terminal datasets.

## Anti-data-mining gates
- No fuel, options, VIX, valuation, or analyst revisions in Phase 1.
- Predetermine horizons and quintile construction.
- No threshold search to maximize returns.
- Report sample counts, means, medians, dispersion, and subperiod results.
- Preserve failed specifications.
- Do not call an effect an edge unless it survives point-in-time and cross-sectional robustness checks.
