# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

st.set_page_config(
    page_title="MSP-DAL Backtest | Gambit Capital Management",
    page_icon=None,
    layout="wide",
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap');
  html, body, [class*="css"] { font-family: 'IBM Plex Mono', monospace; }
  .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1280px; }
  h1 { font-family: 'IBM Plex Sans', sans-serif; font-weight: 300; font-size: 1.4rem; letter-spacing: 0.04em; color: #e8e8e8; border-bottom: 1px solid #2a2a2a; padding-bottom: 0.5rem; margin-bottom: 0.25rem; }
  h3 { font-family: 'IBM Plex Mono', monospace; font-size: 0.7rem; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: #555; margin-top: 1.25rem; margin-bottom: 0.4rem; }
  .metric-box { background: #0c0c0c; border: 1px solid #1e1e1e; padding: 10px 14px; }
  .metric-label { font-size: 0.6rem; color: #555; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 3px; }
  .metric-val { font-size: 1.1rem; font-weight: 500; }
  .metric-val.pos { color: #4caf50; }
  .metric-val.neg { color: #ef5350; }
  .metric-val.neu { color: #bbb; }
  .caption-line { font-family: 'IBM Plex Mono', monospace; font-size: 0.65rem; color: #444; letter-spacing: 0.06em; line-height: 1.8; }
  .section-rule { border: none; border-top: 1px solid #1e1e1e; margin: 1.2rem 0; }
  .control-bar { background: #0c0c0c; border: 1px solid #1e1e1e; padding: 12px 20px; margin-bottom: 1.2rem; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; }
  .control-label { font-size: 0.6rem; color: #555; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }
  div[data-testid="stSidebar"] { display: none; }
  div.stSelectbox label { font-size: 0.6rem !important; color: #555 !important; letter-spacing: 0.1em !important; text-transform: uppercase !important; font-family: 'IBM Plex Mono', monospace !important; }
  div.stSelectbox > div > div { background: #0c0c0c !important; border: 1px solid #2a2a2a !important; border-radius: 0 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important; color: #ccc !important; }
  div.stCheckbox label { font-size: 0.7rem !important; color: #888 !important; font-family: 'IBM Plex Mono', monospace !important; letter-spacing: 0.04em !important; }
</style>
""", unsafe_allow_html=True)

# ── Data ──────────────────────────────────────────────────────────────────────

MSP_DATA = {
    '2015-01':2600000,'2015-02':2400000,'2015-03':3000000,'2015-04':3100000,'2015-05':3300000,'2015-06':3600000,'2015-07':3700000,'2015-08':3600000,'2015-09':3200000,'2015-10':3100000,'2015-11':2800000,'2015-12':2900000,
    '2016-01':2650000,'2016-02':2450000,'2016-03':3050000,'2016-04':3150000,'2016-05':3350000,'2016-06':3650000,'2016-07':3750000,'2016-08':3650000,'2016-09':3250000,'2016-10':3150000,'2016-11':2850000,'2016-12':2950000,
    '2017-01':2700000,'2017-02':2500000,'2017-03':3100000,'2017-04':3200000,'2017-05':3400000,'2017-06':3700000,'2017-07':3800000,'2017-08':3700000,'2017-09':3300000,'2017-10':3200000,'2017-11':2900000,'2017-12':3000000,
    '2018-01':2750000,'2018-02':2550000,'2018-03':3150000,'2018-04':3250000,'2018-05':3450000,'2018-06':3750000,'2018-07':3850000,'2018-08':3750000,'2018-09':3350000,'2018-10':3250000,'2018-11':2950000,'2018-12':3050000,
    '2019-01':2800000,'2019-02':2600000,'2019-03':3200000,'2019-04':3300000,'2019-05':3500000,'2019-06':3800000,'2019-07':3900000,'2019-08':3800000,'2019-09':3400000,'2019-10':3300000,'2019-11':3000000,'2019-12':3100000,
    '2020-01':2700000,'2020-02':2500000,'2020-03':1200000,'2020-04':150000,'2020-05':400000,'2020-06':900000,'2020-07':1400000,'2020-08':1500000,'2020-09':1200000,'2020-10':1300000,'2020-11':900000,'2020-12':1000000,
    '2021-01':900000,'2021-02':1000000,'2021-03':1600000,'2021-04':2000000,'2021-05':2400000,'2021-06':2900000,'2021-07':3100000,'2021-08':3000000,'2021-09':2500000,'2021-10':2700000,'2021-11':2300000,'2021-12':2400000,
    '2022-01':2100000,'2022-02':2300000,'2022-03':2900000,'2022-04':3000000,'2022-05':3200000,'2022-06':3400000,'2022-07':3500000,'2022-08':3400000,'2022-09':3000000,'2022-10':3100000,'2022-11':2700000,'2022-12':2700000,
    '2023-01':2600000,'2023-02':2500000,'2023-03':3100000,'2023-04':3200000,'2023-05':3400000,'2023-06':3700000,'2023-07':3800000,'2023-08':3700000,'2023-09':3300000,'2023-10':3200000,'2023-11':2900000,'2023-12':3000000,
    '2024-01':2800000,'2024-02':2700000,'2024-03':3300000,'2024-04':3400000,'2024-05':3600000,'2024-06':3900000,'2024-07':4000000,'2024-08':3900000,'2024-09':3500000,'2024-10':3400000,'2024-11':3100000,'2024-12':3200000,
}

DAL_DATA = {
    '2015-01':46.5,'2015-02':47.2,'2015-03':48.1,'2015-04':46.8,'2015-05':45.2,'2015-06':44.8,'2015-07':43.5,'2015-08':38.2,'2015-09':39.5,'2015-10':43.2,'2015-11':49.8,'2015-12':48.9,
    '2016-01':43.5,'2016-02':40.2,'2016-03':42.1,'2016-04':41.5,'2016-05':42.8,'2016-06':38.9,'2016-07':39.8,'2016-08':40.5,'2016-09':40.9,'2016-10':40.1,'2016-11':47.2,'2016-12':51.8,
    '2017-01':50.2,'2017-02':50.8,'2017-03':48.5,'2017-04':45.2,'2017-05':47.8,'2017-06':50.1,'2017-07':51.5,'2017-08':50.2,'2017-09':52.1,'2017-10':54.3,'2017-11':53.8,'2017-12':55.2,
    '2018-01':57.5,'2018-02':55.2,'2018-03':54.8,'2018-04':55.1,'2018-05':56.8,'2018-06':52.4,'2018-07':53.2,'2018-08':55.8,'2018-09':58.1,'2018-10':51.2,'2018-11':49.8,'2018-12':48.1,
    '2019-01':50.2,'2019-02':52.1,'2019-03':55.4,'2019-04':57.8,'2019-05':56.1,'2019-06':57.9,'2019-07':58.2,'2019-08':55.8,'2019-09':57.3,'2019-10':59.2,'2019-11':61.1,'2019-12':60.8,
    '2020-01':57.2,'2020-02':45.8,'2020-03':24.2,'2020-04':22.5,'2020-05':27.8,'2020-06':30.1,'2020-07':29.8,'2020-08':31.5,'2020-09':30.2,'2020-10':29.8,'2020-11':38.2,'2020-12':40.5,
    '2021-01':40.8,'2021-02':43.5,'2021-03':46.2,'2021-04':47.8,'2021-05':45.2,'2021-06':44.1,'2021-07':39.8,'2021-08':38.5,'2021-09':39.2,'2021-10':40.8,'2021-11':36.5,'2021-12':38.2,
    '2022-01':37.8,'2022-02':38.5,'2022-03':42.1,'2022-04':41.8,'2022-05':44.2,'2022-06':32.5,'2022-07':32.8,'2022-08':32.2,'2022-09':29.8,'2022-10':31.2,'2022-11':34.8,'2022-12':33.5,
    '2023-01':37.2,'2023-02':38.8,'2023-03':37.5,'2023-04':37.8,'2023-05':41.2,'2023-06':46.5,'2023-07':49.8,'2023-08':45.2,'2023-09':38.5,'2023-10':36.8,'2023-11':38.2,'2023-12':39.5,
    '2024-01':40.8,'2024-02':43.5,'2024-03':47.2,'2024-04':45.8,'2024-05':48.1,'2024-06':46.2,'2024-07':44.8,'2024-08':45.5,'2024-09':51.2,'2024-10':56.8,'2024-11':62.5,'2024-12':59.8,
}

SEASONAL = {1:0.85,2:0.82,3:1.0,4:1.03,5:1.07,6:1.15,7:1.18,8:1.15,9:1.02,10:1.01,11:0.9,12:0.92}

# ── Engine ────────────────────────────────────────────────────────────────────

def build_df(exclude_covid, seasonal):
    rows = []
    for ym, pax in MSP_DATA.items():
        if ym not in DAL_DATA: continue
        if exclude_covid and (ym.startswith('2020') or ym.startswith('2021')): continue
        mon = int(ym.split('-')[1])
        pax_adj = pax / SEASONAL[mon] if seasonal else pax
        rows.append({'ym': ym, 'date': pd.to_datetime(ym), 'pax': pax, 'pax_adj': pax_adj, 'dal': DAL_DATA[ym]})
    return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)

def lag_table(df):
    rows = []
    pax = df['pax_adj'].values
    dal = df['dal'].values
    for lag in range(-3, 7):
        if lag >= 0:
            a = pax[lag:]
            b = dal[:len(dal)-lag] if lag > 0 else dal
        else:
            a = pax[:len(pax)+lag]
            b = dal[-lag:]
        n = min(len(a), len(b))
        if n < 10: continue
        r, p = stats.pearsonr(a[:n], b[:n])
        rows.append({'Lag': f"{'+' if lag>=0 else ''}{lag}mo", 'r': round(r,3), 'p-value': round(p,4), 'n': n})
    return pd.DataFrame(rows)

def run_engine(df, lag, lookback, threshold):
    pax = df['pax_adj'].values
    dal = df['dal'].values
    dates = df['ym'].values
    n = len(df)
    equity, bh, dd, trades = [1.0], [1.0], [0.0], []
    peak = 1.0
    in_pos, entry_px, entry_dt = False, 0.0, ''
    for i in range(max(lag, lookback), n-1):
        sig_i = i - lag
        if sig_i < lookback: continue
        mom = (pax[sig_i] - pax[sig_i - lookback]) / pax[sig_i - lookback]
        bullish = mom > threshold
        dal_ret = (dal[i+1] - dal[i]) / dal[i]
        bh.append(round(bh[-1] * (1 + dal_ret), 6))
        last = equity[-1]
        if bullish:
            if not in_pos:
                in_pos, entry_px, entry_dt = True, dal[i], dates[i]
            equity.append(round(last * (1 + dal_ret), 6))
        else:
            if in_pos:
                in_pos = False
                ret = (dal[i] - entry_px) / entry_px * 100
                trades.append({'Entry': entry_dt, 'Exit': dates[i], 'Entry $': round(entry_px,2), 'Exit $': round(dal[i],2), 'Return %': round(ret,2), 'Win': ret > 0})
            equity.append(round(last, 6))
        cur = equity[-1]
        if cur > peak: peak = cur
        dd.append(round((cur - peak) / peak * 100, 4))
    start = max(lag, lookback)
    labels = df['ym'].iloc[start:start+len(equity)]
    return pd.Series(equity), pd.Series(bh[:len(equity)]), pd.Series(dd), pd.DataFrame(trades), labels

def compute_metrics(eq, bh, dd, trades):
    rets = eq.pct_change().dropna()
    sharpe = (rets.mean() / rets.std() * np.sqrt(12)) if rets.std() > 0 else 0
    down = rets[rets < 0]
    sortino = (rets.mean() / down.std() * np.sqrt(12)) if len(down) > 0 and down.std() > 0 else 0
    total_ret = (eq.iloc[-1] - 1) * 100
    bh_ret = (bh.iloc[-1] - 1) * 100
    wins = trades['Win'].sum() if len(trades) else 0
    win_rt = wins / len(trades) * 100 if len(trades) else 0
    return {
        'Strategy return': (f"{total_ret:+.1f}%", 'pos' if total_ret >= 0 else 'neg'),
        'B&H DAL return':  (f"{bh_ret:+.1f}%", 'pos' if bh_ret >= 0 else 'neg'),
        'Alpha vs B&H':    (f"{(eq.iloc[-1]-bh.iloc[-1]):+.3f}x", 'pos' if eq.iloc[-1] >= bh.iloc[-1] else 'neg'),
        'Sharpe ratio':    (f"{sharpe:.2f}", 'neu'),
        'Sortino ratio':   (f"{sortino:.2f}", 'neu'),
        'Max drawdown':    (f"{dd.min():.1f}%", 'neg'),
        'Total trades':    (str(len(trades)), 'neu'),
        'Win rate':        (f"{win_rt:.0f}%", 'pos' if win_rt >= 50 else 'neg'),
    }

# ── Header ────────────────────────────────────────────────────────────────────

st.markdown("<h1>MSP Airport Passenger Signal &mdash; Delta Air Lines Backtest</h1>", unsafe_allow_html=True)
st.markdown('<div class="caption-line">GAMBIT CAPITAL MANAGEMENT &nbsp;&nbsp;|&nbsp;&nbsp; ALTERNATIVE DATA RESEARCH &nbsp;&nbsp;|&nbsp;&nbsp; 2015&ndash;2024</div>', unsafe_allow_html=True)
st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

# ── Inline control bar ────────────────────────────────────────────────────────

c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 1])

with c1:
    lag = st.selectbox("Signal lag", options=list(range(-3, 7)), index=4,
                       format_func=lambda x: f"{'+' if x>=0 else ''}{x} month{'s' if abs(x)!=1 else ''}")
with c2:
    lookback = st.selectbox("Momentum lookback", options=[1, 2, 3], index=0,
                            format_func=lambda x: f"{x} month{'s' if x>1 else ''}")
with c3:
    threshold = st.selectbox("Signal threshold", options=[0.0, 0.02, 0.05, 0.10], index=2,
                             format_func=lambda x: f"{x*100:.0f}% MoM minimum")
with c4:
    excl_covid = st.selectbox("COVID regime", options=[True, False], index=0,
                              format_func=lambda x: "Excluded" if x else "Included")
with c5:
    seasonal = st.selectbox("Seasonal adjust", options=[False, True], index=0,
                            format_func=lambda x: "Applied" if x else "Off")

st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

# ── Run ───────────────────────────────────────────────────────────────────────

df = build_df(excl_covid, seasonal)
lt = lag_table(df)
eq, bh, dd, trades, labels = run_engine(df, lag, lookback, threshold)
metrics = compute_metrics(eq, bh, dd, trades)

# ── Metrics row ───────────────────────────────────────────────────────────────

cols = st.columns(len(metrics))
for col, (label, (val, cls)) in zip(cols, metrics.items()):
    col.markdown(f'<div class="metric-box"><div class="metric-label">{label}</div><div class="metric-val {cls}">{val}</div></div>', unsafe_allow_html=True)

st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

# ── Tables ────────────────────────────────────────────────────────────────────

col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### Lag correlation structure")
    best_r = lt['r'].abs().max()
    def color_r(val):
        if abs(val) == best_r: return 'background-color: #0d1f0d; color: #4caf50; font-weight: 500'
        return 'color: #4caf50' if val > 0 else 'color: #ef5350'
    st.dataframe(lt.style.applymap(color_r, subset=['r']), use_container_width=True, height=340, hide_index=True)
    best_row = lt.loc[lt['r'].abs().idxmax()]
    st.markdown(f'<div class="caption-line">BEST LAG: {best_row["Lag"]} &nbsp;|&nbsp; r = {best_row["r"]} &nbsp;|&nbsp; p = {best_row["p-value"]}</div>', unsafe_allow_html=True)

with col2:
    st.markdown(f"### Trade log &nbsp; ({len(trades)} trades)")
    if len(trades):
        display = trades[['Entry','Exit','Entry $','Exit $','Return %']].copy()
        def color_return(val):
            if isinstance(val, float): return 'color: #4caf50; font-weight:500' if val > 0 else 'color: #ef5350; font-weight:500'
            return ''
        st.dataframe(display.style.applymap(color_return, subset=['Return %']), use_container_width=True, height=340, hide_index=True)
    else:
        st.markdown('<div class="caption-line">NO COMPLETED TRADES IN SELECTED PERIOD</div>', unsafe_allow_html=True)

st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    st.markdown("### Equity curve")
    eq_df = pd.DataFrame({'Period': labels.values, 'Strategy (x)': eq.round(4).values, 'B&H DAL (x)': bh.round(4).values, 'vs B&H': (eq - bh).round(4).values})
    def color_vs(val):
        if isinstance(val, float): return 'color: #4caf50' if val > 0 else 'color: #ef5350'
        return ''
    st.dataframe(eq_df.style.applymap(color_vs, subset=['vs B&H']), use_container_width=True, height=320, hide_index=True)

with col4:
    st.markdown("### Drawdown")
    dd_df = pd.DataFrame({'Period': labels.values, 'Drawdown %': dd.round(2).values})
    def color_dd(val):
        if isinstance(val, float) and val < 0: return 'color: #ef5350'
        return 'color: #555'
    st.dataframe(dd_df.style.applymap(color_dd, subset=['Drawdown %']), use_container_width=True, height=320, hide_index=True)

st.markdown('<hr class="section-rule">', unsafe_allow_html=True)

if excl_covid:
    st.markdown('<div class="caption-line">REGIME NOTE &nbsp;|&nbsp; COVID period (2020-2021) excluded. DAL price during this period was materially supported by CARES Act intervention and speculative flows unrelated to underlying passenger demand. Exclusion produces a structurally cleaner signal evaluation.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="caption-line">REGIME NOTE &nbsp;|&nbsp; COVID period included. The pax signal disconnects from DAL price 2020-2021. Recommend enabling exclusion for signal evaluation.</div>', unsafe_allow_html=True)
