# Airline Capacity-Growth Signal: Modern Robustness Check

## Question
Does the apparent cross-sectional airline signal survive outside the 2024-2026 discovery window if we strip the model down to carrier capacity growth alone?

## Signal
For each BTS operating month, compute carrier ASM year-over-year growth. Apply a conservative three-month information lag. On each signal month, rank DAL, UAL, AAL, LUV, ALK, and JBLU by carrier ASM YoY growth:

- Slow = bottom two capacity growers
- Middle = middle two
- Fast = top two capacity growers

Forward returns are measured relative to the equal-weight six-airline basket. The key spread is Fast minus Slow.

## Results

### 2021-2023
- 1m Fast-Slow: +1.26%; HAC t = 1.53; p = 0.126; positive months 63.9%
- 3m Fast-Slow: +1.81%; HAC t = 0.81; p = 0.420; positive months 63.9%
- 6m Fast-Slow: +5.75%; HAC t = 1.75; p = 0.080; positive months 58.3%
- 6m rank IC: +0.21

### 2022-2023
- 1m Fast-Slow: +1.94%; HAC t = 1.75; p = 0.080; positive months 62.5%
- 3m Fast-Slow: +2.28%; HAC t = 0.70; p = 0.483; positive months 62.5%
- 6m Fast-Slow: +8.24%; HAC t = 2.04; p = 0.041; positive months 62.5%
- 6m rank IC: +0.28

### 2023 only
- 1m Fast-Slow: +0.97%; HAC t = 0.61; p = 0.541; positive months 58.3%
- 3m Fast-Slow: +0.34%; HAC t = 0.07; p = 0.945; positive months 58.3%
- 6m Fast-Slow: +8.71%; HAC t = 2.69; p = 0.007; positive months 75.0%
- 6m rank IC: +0.30

### 2024-2026 discovery/continuation sample
- 1m Fast-Slow: +0.30%; HAC t = 0.16; p = 0.870; positive months 48.3%
- 3m Fast-Slow: +8.43%; HAC t = 2.12; p = 0.034; positive months 65.5%
- 6m Fast-Slow: +17.52%; HAC t = 4.79; p < 0.00001; positive months 84.6%
- 6m rank IC: +0.36

## Interpretation
The signal is not unique to 2024-2026. The six-month relationship is positive in 2021-2023, strengthens when the most distorted 2021 reopening period is removed, is statistically positive in 2022-2023, and is positive in 2023 alone. The 2024-2026 magnitude is much larger, so the effect is clearly regime-sensitive.

The one-month horizon remains weak throughout. That is consistent with a slow-moving operating-information interpretation rather than an immediate price-reaction or generic momentum effect.

## Important caveats
1. The pre-2024 validation here only extends to 2021 because the currently connected market-data feed begins in mid-2020. BTS data themselves extend to 2010.
2. Historical BTS publication timestamps are not reconstructed; a fixed three-month lag is used conservatively.
3. The airline universe is only six names, so cross-sectional breadth is limited.
4. COVID/reopening base effects remain a structural concern, especially in 2021.
5. The magnitude increased materially after 2023, so a common latent factor (industry cycle, balance-sheet quality, network mix, fuel exposure, or momentum) could still explain the relationship.

## Current gate decision
PASS, provisionally. Capacity growth alone deserves deeper falsification. Do not optimize thresholds or add factors yet. The next priority is to obtain 2010-2020 monthly adjusted stock prices and run the exact same frozen specification across pre-COVID regimes.
