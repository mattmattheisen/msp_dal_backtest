# MSP Walk-Forward Evaluation

## Purpose

The walk-forward evaluator measures MSP traffic forecast accuracy using only information that would actually have been available at the time.

The evaluator is deliberately separate from the DAL backtest. The MSP forecasting method should be selected on its ability to forecast MSP enplanements, not on which version happens to produce the best historical DAL returns.

## Evaluation clock

For each target month with a verified MAC release date, the information cutoff is:

`as_of_date = release_date - 1 calendar day`

Example:

- March 2026 MSP enplanements were released May 15, 2026.
- The walk-forward forecast for March is therefore generated as of May 14, 2026.
- At that time, the latest verified MSP observation available to the model was January 2026.
- February and March 2026 remain hidden from the forecast model.

The actual March value is joined only after the forecast is generated, solely for scoring.

## Eligibility

A target month is scored only when:

1. the target has a verified release date;
2. the same month one year earlier exists in the canonical dataset; and
3. that prior-year observation also has a verified release date.

Because 2024 website timestamps have not yet been reconstructed reliably, the current strict evaluation sample is January through July 2026: seven target months.

## Current benchmark models

### Seasonal naive

`forecast(t) = actual(t-12)`

### Recent YoY trend

`forecast(t) = actual(t-12) * (1 + mean recent known YoY growth)`

The default YoY window is three known observations.

## Metrics

The evaluator reports:

- MAE: mean absolute error in enplanements;
- MAPE: mean absolute percentage error;
- RMSE: root mean squared error;
- Bias: mean signed forecast error.

The current model hurdle is selected by lowest MAPE, with MAE as the tie-breaker.

## Current strict walk-forward results

Using January through July 2026:

| Method | N | MAE | MAPE | RMSE | Bias |
| --- | ---: | ---: | ---: | ---: | ---: |
| Seasonal naive | 7 | 30,881 | 2.08% | 45,974 | +30,881 |
| Recent YoY trend | 7 | 30,000 | 2.16% | 32,900 | -20,826 |

The seasonal-naive benchmark currently has the lower MAPE and is therefore the hurdle to beat under the stated selection rule. The YoY-trend model has slightly lower MAE and materially lower RMSE, so the small sample does not support a strong conclusion yet.

## Interpretation

The March 2026 example favored the YoY-trend model, but the walk-forward exercise shows why individual examples are insufficient. Across all seven currently eligible observations, seasonal naive performs slightly better on MAPE.

This is the benchmark discipline the HMM must face. A Markov/HMM model should not be promoted into the DAL signal pipeline unless it improves out-of-sample forecast performance over these simple models on a meaningfully larger point-in-time sample.

## Next steps

1. Reconstruct older historical MAC release dates to expand the walk-forward sample.
2. Add an autoregressive/seasonal statistical benchmark.
3. Add HMM regime probabilities using only the point-in-time information set.
4. Compare all models on the same walk-forward target months and scoring metrics.
5. Freeze the preferred MSP model before connecting the signal to DAL returns.
