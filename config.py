# config.py
# All backtest parameters in one place.
# Change values here — no need to touch the engine code.

import os
from dotenv import load_dotenv

load_dotenv()

# ── Data ──────────────────────────────────────────────────────────────────────
TIINGO_API_KEY = os.getenv("TIINGO_API_KEY", "")
USE_LIVE_DATA = False          # True = fetch from Tiingo + MAC; False = use data/ CSVs

DAL_TICKER = "DAL"
START_DATE = "2015-01-01"
END_DATE   = "2024-12-31"

# ── Signal construction ───────────────────────────────────────────────────────
LAG_MONTHS        = 1          # Months MSP pax signal leads DAL entry (0 = same month)
LOOKBACK_MONTHS   = 1          # Momentum lookback window in months
SIGNAL_THRESHOLD  = 0.05       # Minimum MoM pax growth to trigger long (0.05 = 5%)
SEASONAL_ADJUST   = False      # Divide pax by seasonal index before computing momentum

# Monthly seasonal indices (avg pax relative to annual mean, derived from 2015–2019)
SEASONAL_INDEX = {
    1: 0.85, 2: 0.82, 3: 1.00, 4: 1.03, 5: 1.07, 6: 1.15,
    7: 1.18, 8: 1.15, 9: 1.02, 10: 1.01, 11: 0.90, 12: 0.92,
}

# ── Regime / data filters ─────────────────────────────────────────────────────
EXCLUDE_COVID = True           # Drop 2020-01 through 2021-12 (structural break)
COVID_START   = "2020-01"
COVID_END     = "2021-12"

# ── Backtest execution ────────────────────────────────────────────────────────
INITIAL_CAPITAL  = 100_000     # USD
COMMISSION_PCT   = 0.001       # 0.1% round-trip (conservative for DAL liquidity)
ALLOW_SHORT      = False       # Pax decline → cash, not short

# ── Output ────────────────────────────────────────────────────────────────────
REPORT_DIR   = "reports"
SHOW_CHARTS  = True            # Display matplotlib charts interactively
SAVE_CHARTS  = True            # Save PNG to reports/
VERBOSE      = True
