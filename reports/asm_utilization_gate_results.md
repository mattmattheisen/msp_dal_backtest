# ASM / Fleet Utilization Gate Results

## Question
Is the post-COVID capacity-growth phenomenon primarily physical fleet expansion, or increased deployment/utilization of the existing operating fleet?

## Data
- BTS Schedule T1 annualized scheduled-service ASM, six carriers: AA, AS, B6, DL, UA, WN.
- BTS Schedule B-43 active aircraft inventory (`OPERATING_STATUS=Y`).
- 2010-2025 B-43 history and 2010-2026 T1 history.
- Duplicate annual downloads removed.

## Metrics
- `ASM per operating aircraft = annual ASM / active aircraft count`
- `ASM per physical fleet seat = annual ASM / sum of seats on active aircraft`
- YoY changes calculated carrier by carrier.

## Main structural result
The decomposition changes sharply across regimes.

### 2014-2019
Cross-sectional correlation of ASM growth with:
- aircraft-count growth: **0.813**
- fleet-seat growth: **0.810**
- ASM-per-aircraft growth: **-0.141**
- ASM-per-fleet-seat growth: **-0.081**

Interpretation: before COVID, differences in airline ASM growth were primarily associated with differences in physical fleet growth. Utilization/deployment intensity contributed little cross-sectionally.

### 2022-2025
Cross-sectional correlation of ASM growth with:
- aircraft-count growth: **0.476**
- fleet-seat growth: **0.487**
- ASM-per-aircraft growth: **0.962**
- ASM-per-fleet-seat growth: **0.966**

Interpretation: in the normalized post-COVID period, differences in ASM growth are overwhelmingly associated with differences in output per aircraft / per installed fleet seat rather than simply acquiring more aircraft.

## Fast-vs-slow ASM growers
For each year, carriers were ranked by annual ASM growth; the top two and bottom two were compared on utilization growth.

Difference in YoY ASM-per-aircraft growth (fast minus slow):
- 2022: **+18.6 pp**
- 2023: **+3.2 pp**
- 2024: **+5.9 pp**
- 2025: **+4.4 pp**

Difference in YoY ASM-per-fleet-seat growth is similarly positive in each modern year:
- 2022: **+18.2 pp**
- 2023: **+4.2 pp**
- 2024: **+6.1 pp**
- 2025: **+4.7 pp**

By contrast, the pre-COVID fast-minus-slow utilization differences alternate sign and are not stable year to year.

## Conclusion
The simple fleet-scarcity hypothesis is rejected. The modern capacity signal is much more consistent with a **deployment/utilization signal**: carriers that grow ASM fastest are generating more scheduled seat-miles from each operating aircraft / installed fleet seat.

This is a structural regime break in the operating decomposition itself, independent of stock returns: pre-COVID ASM growth was mostly fleet-growth driven; post-COVID ASM growth is predominantly utilization/deployment driven.

## Important limitation
B-43 is annual inventory data, while T1 is monthly. These ratios are therefore annual structural diagnostics and should not be treated as monthly tradable signals without point-in-time release alignment. The next return test should pre-specify a lagged annual utilization state and test whether the monthly capacity-return relationship is concentrated among carriers with rising ASM per aircraft / fleet seat.
