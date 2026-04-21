# streamlit_app.py
"""
MSP Airport Passenger Signal — DAL Backtest
Streamlit web application for Gambit Capital Management
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

st.set_page_config(
    page_title="MSP–DAL Backtest | Shomer Analytics",
    page_icon=None,
    layout="wide",
)

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
        if ym not in DAL_DATA:
            continue
        if exclude_covid and (ym.startswith('2020') or ym.startswith('2021')):
            continue
        mon = int(ym.split('-')[1])
        pax_adj = pax / SEASONAL[mon] if seasonal else pax
        rows.append({'ym': ym, 'date': pd.to_datetime(ym), 'pax': pax, 'pax_adj': pax_adj, 'dal': DAL_DATA[ym]})
    return pd.DataFrame(rows).sort_values('date').reset_index(drop=True)

def pearson(a, b):
    r, p = stats.pearsonr(a, b)
    return r, p

def lag_table(df, min_lag=-3, max_lag=6):
    rows = []
    pax = df['pax_adj'].values
    dal = df['dal'].values
    for lag in range(min_lag, max_lag+1):
        if lag >= 0:
            a, b = pax[lag:], dal[:len(dal)-lag] if lag > 0 else dal
        else:
            a, b = pax[:len(pax)+lag], dal[-lag:]
        n = min(len(a), len(b))
        if n < 10: continue
        r, p = pearson(a[:n], b[:n])
        rows.append({'Lag (months)': lag, 'r': round(r,3), 'p-value': round(p,4), 'n': n})
    return pd.DataFrame(rows)

def run_engine(df, lag, lookback, threshold):
    pax = df['pax_adj'].values
    dal = df['dal'].values
    dates = df['date'].values
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
                in_pos, entry_px = True, dal[i]
                entry_dt = str(dates[i])[:7]
            equity.append(round(last * (1 + dal_ret), 6))
        else:
            if in_pos:
                in_pos = False
                ret = (dal[i] - entry_px) / entry_px * 100
                trades.append({'Entry': entry_dt, 'Exit': str(dates[i])[:7],
                               'Entry $': round(entry_px,2), 'Exit $': round(dal[i],2),
                               'Return %': round(ret,2), 'Win': ret > 0})
            equity.append(round(last, 6))

        cur = equity[-1]
        if cur > peak: peak = cur
        dd.append(round((cur - peak) / peak * 100, 4))

    start = max(lag, lookback)
    labels = df['date'].iloc[start:start+len(equity)]
    return (pd.Series(equity), pd.Series(bh[:len(equity)]),
            pd.Series(dd), pd.DataFrame(trades), labels)

def compute_metrics(eq, bh, dd, trades):
    n = len(eq) - 1
    total_ret = (eq.iloc[-1] - 1) * 100
    bh_ret    = (bh.iloc[-1] - 1) * 100
    rets = eq.pct_change().dropna()
    sharpe = (rets.mean() / rets.std() * np.sqrt(12)) if rets.std() > 0 else 0
    wins   = sum(1 for t in trades.itertuples() if t._6) if len(trades) else 0
    win_rt = wins / len(trades) * 100 if len(trades) else 0
    return {
        'Strategy return': f"{total_ret:+.1f}%",
        'B&H DAL return':  f"{bh_ret:+.1f}%",
        'Alpha vs B&H':    f"{(eq.iloc[-1]-bh.iloc[-1]):+.3f}x",
        'Sharpe ratio':    f"{sharpe:.2f}",
        'Max drawdown':    f"{dd.min():.1f}%",
        'Total trades':    str(len(trades)),
        'Win rate':        f"{win_rt:.0f}%",
        'Months in market': f"{(eq.pct_change().dropna() != 0).mean()*100:.0f}%",
    }

# ── Layout ────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  h1 { font-size: 1.4rem; font-weight: 600; }
  h3 { font-size: 1rem; font-weight: 500; margin-top: 1.2rem; }
  .metric-label { font-size: 0.75rem; color: #888; }
  .metric-value { font-size: 1.3rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

st.title("MSP Airport Passenger Signal — Delta Air Lines Backtest")
st.caption("Alternative data research | Shomer Analytics / Gambit Capital Management")

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Parameters")
    lag        = st.slider("Signal lag (months)",  -3, 6,  1)
    lookback   = st.slider("Momentum lookback",     1, 3,  1)
    threshold  = st.selectbox("Signal threshold", [0.0, 0.02, 0.05, 0.10],
                               index=2, format_func=lambda x: f"{x*100:.0f}% MoM")
    excl_covid = st.checkbox("Exclude COVID regime (2020–2021)", value=True)
    seasonal   = st.checkbox("Seasonal adjustment", value=False)

    st.divider()
    st.caption("**Thesis:** MSP is Delta's primary hub (~70% market share). Rising passenger momentum should precede or accompany DAL price appreciation.")
    st.caption("**Data:** MAC monthly enplanements 2015–2024. DAL approximate monthly close prices.")
    st.caption("**Not investment advice.**")

# ── Run ───────────────────────────────────────────────────────────────────────
df = build_df(excl_covid, seasonal)
lt = lag_table(df)
eq, bh, dd, trades, labels = run_engine(df, lag, lookback, threshold)
metrics = compute_metrics(eq, bh, dd, trades)

# ── Metrics row ───────────────────────────────────────────────────────────────
cols = st.columns(len(metrics))
for col, (k, v) in zip(cols, metrics.items()):
    col.metric(k, v)

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────
def norm(s): mn,mx=s.min(),s.max(); return (s-mn)/(mx-mn) if mx>mn else s*0

fig, axes = plt.subplots(2, 2, figsize=(14, 8))
fig.patch.set_facecolor('white')

# 1. Overlay
ax = axes[0,0]
ax.plot(df['date'], norm(df['pax_adj']), color='#3266ad', lw=1.5, label='MSP passengers')
ax.plot(df['date'], norm(df['dal']),     color='#d85a30', lw=1.5, ls='--', label='DAL price')
ax.set_title('Normalized signal overlay', fontsize=10)
ax.legend(fontsize=8, framealpha=0)
ax.grid(axis='y', alpha=0.2); ax.spines[['top','right']].set_visible(False)

# 2. Lag correlation
ax = axes[0,1]
colors = ['#d85a30' if l==lag else '#3266ad' for l in lt['Lag (months)']]
ax.bar(lt['Lag (months)'], lt['r'], color=colors, width=0.6)
ax.axhline(0, color='black', lw=0.5)
ax.set_title('Lag correlation (+ = pax leads DAL)', fontsize=10)
ax.set_xlabel('Lag months'); ax.set_ylabel('Pearson r')
ax.set_ylim(-1,1); ax.grid(axis='y', alpha=0.2)
ax.spines[['top','right']].set_visible(False)

# 3. Equity
ax = axes[1,0]
ax.plot(labels, eq, color='#3b6d11', lw=2,   label='Signal strategy')
ax.plot(labels, bh, color='#888780', lw=1.5, ls='--', label='Buy & hold DAL')
ax.set_title('Equity curve (rebased to 1.0)', fontsize=10)
ax.legend(fontsize=8, framealpha=0)
ax.grid(axis='y', alpha=0.2); ax.spines[['top','right']].set_visible(False)

# 4. Drawdown
ax = axes[1,1]
ax.fill_between(range(len(dd)), dd, 0, color='#a32d2d', alpha=0.3)
ax.plot(range(len(dd)), dd, color='#a32d2d', lw=1)
ax.set_title('Drawdown from peak (%)', fontsize=10)
ax.grid(axis='y', alpha=0.2); ax.spines[['top','right']].set_visible(False)

plt.tight_layout()
st.pyplot(fig)
plt.close()

st.divider()

# ── Lag table + trade log ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.subheader("Lag correlation table")
    best_row = lt.loc[lt['r'].abs().idxmax()]
    st.dataframe(lt.style.highlight_max(subset=['r'], color='#d4edda')
                          .highlight_min(subset=['r'], color='#f8d7da'),
                 use_container_width=True)
    st.caption(f"Best lag: **{'+' if best_row['Lag (months)']>=0 else ''}{int(best_row['Lag (months)'])} months** (r = {best_row['r']:.3f}, p = {best_row['p-value']:.3f})")

with col2:
    st.subheader(f"Trade log ({len(trades)} trades)")
    if len(trades):
        display = trades[['Entry','Exit','Entry $','Exit $','Return %']].copy()
        st.dataframe(
            display.style.applymap(
                lambda v: 'color: #3b6d11; font-weight:600' if isinstance(v,float) and v>0
                     else ('color: #a32d2d; font-weight:600' if isinstance(v,float) and v<0 else ''),
                subset=['Return %']
            ),
            use_container_width=True, height=320
        )
    else:
        st.info("No completed trades in selected period.")

# ── Regime note ───────────────────────────────────────────────────────────────
st.divider()
if excl_covid:
    st.info("COVID regime (2020–2021) excluded. During this period DAL price was driven by CARES Act support and speculative flows — not actual passenger demand. Exclusion produces a cleaner signal evaluation.")
else:
    st.warning("COVID regime included. The pax signal disconnects from DAL price 2020–2021. Consider enabling exclusion for signal evaluation.")
