import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import math
from datetime import datetime

# ========================= DEFAULTS =========================
DEFAULT_CARRIERS = 2
DEFAULT_US_MILITARY = "Extreme"
DEFAULT_IDF_ALERT = "High"
DEFAULT_SENTIMENT = 8.5

# ========================= ASSETS =========================
ASSETS = {
    "CL=F": {"name": "Crude Oil", "weight": 0.30, "direction": 1, "emoji": "🛢️", "color": "#FF6B6B",
             "tooltip": "Surges on Middle East supply disruption fears"},
    "GC=F": {"name": "Gold", "weight": 0.25, "direction": 1, "emoji": "🥇", "color": "#FFD166",
             "tooltip": "Classic safe-haven asset during geopolitical tension"},
    "BTC-USD": {"name": "Bitcoin", "weight": 0.18, "direction": -1, "emoji": "₿", "color": "#F7931A",
                "tooltip": "Often falls sharply in risk-off environments (negative correlation)"},
    "LMT": {"name": "Lockheed Martin", "weight": 0.08, "direction": 1, "emoji": "✈️", "color": "#06D6A0",
            "tooltip": "Defense stocks rise on expected military spending"},
    "RTX": {"name": "Raytheon", "weight": 0.07, "direction": 1, "emoji": "🚀", "color": "#118AB2",
            "tooltip": "Additional defense contractor exposure"},
    "^VIX": {"name": "VIX Fear Index", "weight": 0.12, "direction": 1, "emoji": "📉", "color": "#EF4444",
             "tooltip": "Classic 'fear gauge' – spikes during Middle East crises"},
}

TIMEFRAME_WEIGHTS = {"1h": 0.10, "4h": 0.30, "1d": 0.40, "1wk": 0.20}

# ====================== CACHED DATA ======================
@st.cache_data(ttl=180, show_spinner=False)
def get_all_asset_data(ticker):
    data = {}
    current_price = 0.0
    for tf in TIMEFRAME_WEIGHTS:
        try:
            if tf == "1h": df = yf.download(ticker, period="1d", interval="5m", auto_adjust=True); start_idx = -12
            elif tf == "4h": df = yf.download(ticker, period="5d", interval="15m", auto_adjust=True); start_idx = -16
            elif tf == "1d": df = yf.download(ticker, period="5d", interval="1h", auto_adjust=True); start_idx = -24
            else: df = yf.download(ticker, period="1mo", interval="1d", auto_adjust=True); start_idx = -5
            change = 0.0
            if len(df) >= 5:
                start_p = df['Close'].iloc[start_idx].item()
                end_p = df['Close'].iloc[-1].item()
                change = ((end_p - start_p) / start_p) * 100.0
            data[tf] = change
            if current_price == 0.0 and 'end_p' in locals():
                current_price = float(end_p)
        except:
            data[tf] = 0.0
    return data, current_price

# ====================== CALCULATIONS ======================
def calculate_market_raw(all_data):
    total = 0.0
    for ticker, info in ASSETS.items():
        asset_data = all_data.get(ticker, {}).get("data", {})
        weighted = sum(asset_data.get(tf, 0.0) * info["direction"] * TIMEFRAME_WEIGHTS[tf]
                       for tf in TIMEFRAME_WEIGHTS)
        total += weighted * info["weight"]
    return total

def normalize_market(raw):
    if raw >= 0:
        return min(100, 25 + (raw / 10) * 75)
    else:
        decay = (math.log1p(abs(raw) * 2) / math.log1p(20)) * 25
        return max(0, 25 - decay)

def calculate_geo_score(carriers, us_military, idf_alert, sentiment):
    carrier_score = min(carriers, 4) * 8.75
    military_map = {"Low": 0, "Moderate": 15, "High": 25, "Extreme": 32, "Unprecedented": 40}
    military_score = military_map.get(us_military, 25)
    idf_map = {"Low": 0, "Moderate": 8, "High": 15}
    idf_score = idf_map.get(idf_alert, 8)
    sentiment_score = (sentiment / 10) * 10
    return carrier_score + military_score + idf_score + sentiment_score

def get_progress_color(value, max_val):
    norm = value / max_val
    if norm < 0.3: return "#10b981"
    elif norm < 0.6: return "#facc15"
    elif norm < 0.85: return "#fb923c"
    else: return "#ef4444"

# ====================== UI ======================
st.set_page_config(page_title="METI", page_icon="🧭", layout="wide")

# Interactive hover CSS
st.markdown("""
    <style>
    .asset-card, .geo-card {
        background: rgba(30,41,59,0.95);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        margin: 8px;
        transition: all 0.35s ease;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .asset-card:hover, .geo-card:hover {
        transform: translateY(-8px) scale(1.05);
        box-shadow: 0 16px 32px rgba(0,0,0,0.5);
        background: rgba(45,55,75,0.98);
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align:center;color:white;font-size:3rem;'>Middle-East Tension Index</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#cbd5e1;font-size:1.1rem;'>Assessment of Middle-East conflict possibility based on real-time market signals and geopolitical factors</p>", unsafe_allow_html=True)

if st.button("🔄 Refresh Data", type="primary"):
    st.cache_data.clear()
    st.rerun()

# ────────────────────────────────────────────────
# SIDEBAR
# ────────────────────────────────────────────────
with st.sidebar:
    st.header("Geopolitical Factors")
    st.caption("Defaults reflect current reality (Feb 2026)")
    carriers = st.number_input("US Carriers in Region", 0, 4, value=DEFAULT_CARRIERS, key="carriers")
    us_military = st.selectbox("US Military Activity Level", ["Low", "Moderate", "High", "Extreme", "Unprecedented"],
                               index=["Low", "Moderate", "High", "Extreme", "Unprecedented"].index(DEFAULT_US_MILITARY), key="us_military")
    idf_alert = st.selectbox("IDF Alert Level", ["Low", "Moderate", "High"],
                             index=["Low", "Moderate", "High"].index(DEFAULT_IDF_ALERT), key="idf_alert")
    sentiment = st.slider("News & Social Sentiment (0–10)", 0.0, 10.0, DEFAULT_SENTIMENT, 0.5, key="sentiment")

    if st.button("Reset to Current Reality", type="secondary"):
        for key in ["carriers", "us_military", "idf_alert", "sentiment", "tf"]:
            if key in st.session_state:
                del st.session_state[key]
        st.cache_data.clear()
        st.rerun()

# ────────────────────────────────────────────────
# CALCULATIONS
# ────────────────────────────────────────────────
all_data = {}
with st.spinner("Fetching market signals..."):
    for ticker in ASSETS:
        d, p = get_all_asset_data(ticker)
        all_data[ticker] = {"data": d, "price": p}

market_raw = calculate_market_raw(all_data)
market_norm = normalize_market(market_raw)
geo_score = calculate_geo_score(carriers, us_military, idf_alert, sentiment)
final_index = 0.7 * market_norm + 0.3 * geo_score

level_text, level_color = (
    ("🟢 Low Tension", "#10b981") if final_index < 30 else
    ("🟡 Moderate Tension", "#facc15") if final_index < 60 else
    ("🟠 Elevated Tension", "#fb923c") if final_index < 80 else
    ("🔴 High Tension", "#ef4444")
)

# ────────────────────────────────────────────────
# COOLER GAUGE
# ────────────────────────────────────────────────
fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=final_index,
    title={"text": "Tension Index", "font": {"size": 28, "color": "white"}},
    number={"font": {"size": 72, "color": "white"}},
    gauge={
        "axis": {"range": [0, 100], "tickwidth": 2, "tickcolor": "white"},
        "bar": {"color": level_color, "thickness": 0.32},
        "bgcolor": "rgba(0,0,0,0)",
        "borderwidth": 3,
        "bordercolor": "rgba(255,255,255,0.5)",
        "steps": [
            {"range": [0, 30],  "color": "rgba(16,185,129,0.55)"},
            {"range": [30, 60], "color": "rgba(250,204,21,0.55)"},
            {"range": [60, 80], "color": "rgba(249,115,22,0.55)"},
            {"range": [80, 100],"color": "rgba(239,68,68,0.65)"}
        ],
        "threshold": {"line": {"color": "white", "width": 7}, "thickness": 1.0, "value": final_index}
    }
))

fig.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=40))
st.plotly_chart(fig, width="stretch")

st.markdown(f"""
    <h2 style='text-align:center;color:{level_color};margin:15px 0;padding:22px;
               background:rgba(0,0,0,0.45);border-radius:18px;font-size:2.7rem;'>
        {level_text}
    </h2>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
# MARKET SIGNALS
# ────────────────────────────────────────────────
st.markdown("### 📊 Market Signals")
cols = st.columns(3)
tf = st.session_state.get("tf", "1d")

for i, ticker in enumerate(ASSETS):
    info = ASSETS[ticker]
    change = all_data[ticker]["data"].get(tf, 0.0) * info["direction"]
    color = "#10b981" if change >= 0 else "#ef4444"
    with cols[i % 3]:
        st.markdown(f"""
        <div class="asset-card" title="{info['tooltip']}">
            <div style="font-size:4.5rem;margin-bottom:10px;">{info['emoji']}</div>
            <div style="color:{info['color']};font-weight:bold;font-size:1.35rem;">{info['name']}</div>
            <div style="font-size:1.7rem;color:#e2e8f0;margin:10px 0;">${all_data[ticker]['price']:,.2f}</div>
            <div style="color:{color};font-size:1.6rem;font-weight:bold;">
                {'▲' if change>=0 else '▼'} {abs(change):.2f}%
            </div>
        </div>
        """, unsafe_allow_html=True)

# ────────────────────────────────────────────────
# TIMEFRAME & DETAILS & BREAKDOWN
# ────────────────────────────────────────────────
st.markdown("### ⏱️ Select Timeframe")
timeframe_cols = st.columns(4)
for i, (key, label) in enumerate([("1h","1 Hour"), ("4h","4 Hours"), ("1d","1 Day"), ("1wk","1 Week")]):
    with timeframe_cols[i]:
        if st.button(
            label,
            key=key,
            use_container_width=True,
            type="primary" if tf == key else "secondary"
        ):
            st.session_state.tf = key
            st.rerun()

st.markdown("### 📊 Details & Breakdown")
colM, colG = st.columns(2)
with colM: st.metric("**Market Signals (70%)**", f"{market_norm:.1f}/100")
with colG: st.metric("**Geopolitical Factors (30%)**", f"{geo_score:.1f}/100")

st.markdown("#### Geopolitical Contribution")
gcols = st.columns(4)

for idx, (title, value, score, maxv, color_key) in enumerate([
    ("US Carriers", f"{carriers}/4", min(carriers,4)*8.75, 35, "#a6a6a6"),
    ("US Military", us_military, {"Low":0,"Moderate":15,"High":25,"Extreme":32,"Unprecedented":40}.get(us_military,25), 40, "#a6a6a6"),
    ("IDF Alert", idf_alert, {"Low":0,"Moderate":8,"High":15}.get(idf_alert,8), 15, "#a6a6a6"),
    ("News/Social", f"{sentiment}/10", sentiment, 10, "#a6a6a6")
]):
    score_val = score if isinstance(score, (int,float)) else 0
    color = get_progress_color(score_val, maxv)
    with gcols[idx]:
        st.markdown(f"""
        <div class="geo-card" title="Contribution to overall tension index">
            <div style="font-weight:bold;color:{color_key};font-size:1.25rem;">{title}</div>
            <div style="font-size:1.6rem;color:white;margin:8px 0;">{value}</div>
            <div style="color:{color};font-size:1.35rem;font-weight:bold;">+{score_val:.1f}</div>
            <div style="height:12px;background:{color};border-radius:6px;margin-top:10px;width:{min((score_val/maxv)*100,100)}%"></div>
        </div>
        """, unsafe_allow_html=True)

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
