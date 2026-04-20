# msp_dal_backtest
MSP airport passenger traffic as alternative data signal for Delta Air Lines (DAL) correlation analysis, lag structure, and monthly momentum backtest.
MSP Airport Passenger Signal — Delta Air Lines Backtest
An alternative data backtest using Minneapolis-St. Paul International Airport (MSP) monthly passenger traffic as a leading signal for Delta Air Lines (DAL) equity.
Thesis: MSP is Delta's primary hub, with Delta commanding ~70% passenger market share. Sustained increases in MSP enplanements reflect real demand growth that should precede or accompany DAL earnings and price appreciation. This framework tests whether that signal is tradeable.
---
Repository structure
```
msp-dal-backtest/
├── data/
│   ├── msp_passengers.csv        # MAC monthly enplanement data (2015–2024)
│   └── dal_prices.csv            # DAL monthly close prices
├── src/
│   ├── data_loader.py            # MAC scraper + Tiingo DAL price fetcher
│   ├── signal.py                 # Signal construction + seasonal adjustment
│   ├── backtest.py               # Backtest engine (lag, lookback, threshold)
│   ├── metrics.py                # Sharpe, Sortino, Calmar, drawdown, alpha
│   └── visualize.py              # Matplotlib charts: equity, drawdown, lag correlation
├── notebooks/
│   └── 01_exploration.ipynb      # Full walkthrough with commentary
├── tests/
│   ├── test_signal.py
│   ├── test_backtest.py
│   └── test_metrics.py
├── reports/
│   └── backtest_summary.png      # Output chart (generated)
├── run_backtest.py               # CLI entry point
├── config.py                     # All parameters in one place
├── requirements.txt
├── .env.example                  # Tiingo API key placeholder
├── .gitignore
└── README.md
```
---
Quickstart
```bash
git clone https://github.com/YOUR_USERNAME/msp-dal-backtest.git
cd msp-dal-backtest
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # Add your Tiingo API key
python run_backtest.py
```
Output: terminal summary table + `reports/backtest_summary.png`
---
Signal logic
Each month, the signal computes a momentum score over MSP passenger traffic:
```
momentum = (pax[t] - pax[t - lookback]) / pax[t - lookback]
```
If `momentum > threshold`, the strategy goes long DAL at end-of-month close, lagged by N months. Otherwise it moves to cash (0% return, no short).
The lag parameter tests whether MSP passenger data leads DAL price moves — the core predictive hypothesis.
---
Configuration (`config.py`)
Parameter	Default	Description
`LAG_MONTHS`	1	Months MSP signal leads DAL entry
`LOOKBACK_MONTHS`	1	Momentum lookback window
`SIGNAL_THRESHOLD`	0.05	Minimum MoM pax growth to go long
`EXCLUDE_COVID`	True	Exclude 2020–2021 regime
`SEASONAL_ADJUST`	False	Divide pax by monthly seasonal index
`TIINGO_API_KEY`	env var	Set in `.env` file
---
Key findings (preliminary)
Correlation (r) between MSP pax and DAL price: ~0.61 (ex-COVID)
Best predictive lag: +1 month (pax leads DAL by one month)
Signal accuracy (% of trades that were profitable): ~58% (ex-COVID)
COVID regime (2020–2021) materially distorts results — DAL price was driven by CARES Act support and speculative flows, not actual demand. Recommend excluding.
---
Data sources
MSP passenger traffic: Metropolitan Airports Commission monthly operations reports  
→ https://metroairports.org/msp-passenger-and-operations-reports
DAL price history: Tiingo API (free tier, requires API key)  
→ https://www.tiingo.com
The `data/` folder contains pre-loaded historical data (2015–2024) so the backtest runs without an API key. Set `USE_LIVE_DATA=True` in `config.py` to fetch fresh data.
---
Limitations and caveats
Look-ahead bias: MAC data releases with ~30-day lag. The backtest assumes end-of-month execution using that month's published data — this is realistic only if you are monitoring the MAC release schedule.
COVID distortion: 2020–2021 is a structural break. The pax signal collapsed while DAL price was partially supported by federal intervention. This period should be treated as a separate regime, not signal noise.
Overfitting risk: With only ~10 years of monthly data (120 observations), parameter optimization is dangerous. The default parameters were chosen based on the economic thesis, not in-sample optimization.
Transaction costs: Not modeled. Monthly rebalancing at end-of-month close is assumed frictionless. Real-world slippage would be minimal given DAL liquidity.
This is not investment advice.
---
Extending this framework
Additional airports: Add ATL (Delta's primary hub), JFK, LAX and build a composite signal
TSA throughput: BTS publishes national daily checkpoint numbers — a higher-frequency version of the same thesis
Earnings confirmation: Combine the pax signal with DAL pre-announcement implied volatility as a filter
Regime gate: Suppress the long signal when your macro regime classifier (VIX, MOVE, COR1M) is in Risk-Off state
---
License
MIT. Build on it, break it, improve it.
---
Built by Matt Mattheisen / Shomer Analytics  
Concept originated from Gambit Capital Management alternative data research
