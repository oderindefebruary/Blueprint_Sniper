import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="₦1M Blueprint", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117 !important; }
    .stApp { background-color: #0e1117 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stMetricValue"] { font-size: 2rem !important; color: #00ff00 !important; text-align: center; }
    .block-container { padding: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

# API & GLOBAL CONSTANTS
API_KEY = st.secrets["API_KEY"]
HEADERS = {"x-apisports-key": API_KEY}
INITIAL_FUNDS = 1000000.0
STAKE_PCT = 5.0 

# --- 2. SNIPER RADAR ENGINE (STRICT 0-0 FILTER) ---
@st.cache_data(ttl=60)
def get_football_data():
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        return res.get("response", [])
    except: return []

def process_live_radar(fixtures):
    if not fixtures: return []
    radar = []
    for f in fixtures:
        goals_home = f.get('goals', {}).get('home') or 0
        goals_away = f.get('goals', {}).get('away') or 0
        total_goals = goals_home + goals_away
        
        status = f.get('fixture', {}).get('status', {}).get('short', '')
        elapsed = f.get('fixture', {}).get('status', {}).get('elapsed') or 0
        
        # SNIPER LOGIC: Only list if score is exactly 0-0
        if total_goals == 0 and status in ["NS", "1H", "HT", "2H"]:
            intensity = "🔥 HIGH"
            if 30 <= elapsed <= 45: intensity = "⚡ EXTREME"
            if elapsed > 60: intensity = "🚨 CRITICAL"
            
            radar.append({
                "TIME": f"{elapsed}'" if status != "NS" else "READY", 
                "FIXTURE": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", 
                "STATE": intensity
            })
    return radar

# --- 3. GLOBAL FETCH & AUTH ---
all_fixtures_raw = get_football_data()
IS_ADMIN = st.query_params.get("admin") == "true"
if 'master_log' not in st.session_state: st.session_state.master_log = []

# --- 4. PRECISION ANALYTICS ---
def calculate_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Label": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        label = entry.get("TITLE", "Trade")
        asset = entry.get("ASSET", "⚽")
        
        if entry["RESULT"] == "PAYOUT":
            p_amt = entry.get("AMOUNT", 0)
            balance -= p_amt
            total_paid_out += p_amt
            m_label = f"💰 {label}: ₦{p_amt:,.0f}"
        else:
            stake = (balance * STAKE_PCT) / 100
            odds = entry.get("ODDS", 1.12)
            if entry["RESULT"] == "WIN":
                balance += (stake * odds) - stake
            else:
                balance -= stake
            
            if balance > ath: ath = balance
            m_label = f"{asset} {label} (@{odds})"

        dd = ((ath - balance) / ath) * 100 if ath > 0 else 0
        history.append({
            "Trade": i + 1, "Balance": balance, 
            "Growth": (((balance + total_paid_out) - INITIAL_FUNDS) / INITIAL_FUNDS) * 100,
            "DD": dd, "Label": m_label
        })
    return pd.DataFrame(history), total_paid_out

# --- 5. UI RENDER ---
eq_df, total_payouts = calculate_metrics()
curr_roi = eq_df['Growth'].iloc[-1]
now = datetime.now()

st.markdown(f"<h1 style='text-align: center; color: white;'>🛡️ ₦1M BLUEPRINT</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
c1.metric("TOTAL ROI", f"{curr_roi:.2f}%")
c2.metric("PAYOUTS", f"₦{total_payouts:,.0f}")
c3.metric("CURRENT BAL", f"₦{eq_df['Balance'].iloc[-1]:,.0f}")

fig = px.area(eq_df, x="Trade", y="Growth", title="Institutional Equity Path", 
             color_discrete_sequence=["#00ff00"], hover_data=["Label"])
fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 6. ADMIN GOD MODE (ASSET + DESCRIPTION) ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL", expanded=True):
        t1, t2 = st.tabs(["Log Trade", "Log Payout"])
        with t1:
            col_1, col_2 = st.columns([1, 2])
            asset_type = col_1.selectbox("Asset", ["⚽ Football", "🟡 Gold (XAU)"])
            trade_title = col_2.text_input("Trade Title", placeholder="e.g., Domino-de-Dios Sniper")
            
            all_names = [f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in all_fixtures_raw]
            target = st.selectbox("Market Match (If Football)", options=sorted(all_names) if all_names else ["Manual Entry"])
            
            col_a, col_b = st.columns(2)
            trade_odds = col_a.number_input("Odds", min_value=1.01, value=1.12, step=0.01)
            result = col_b.selectbox("Outcome", ["WIN", "LOSS"])
            
            if st.button("🚀 VERIFY & LOG"):
                st.session_state.master_log.insert(0, {
                    "DATE": now.strftime("%Y-%m-%d"), 
                    "ASSET": "⚽" if "Football" in asset_type else "🟡",
                    "TITLE": trade_title if trade_title else target,
                    "RESULT": result, 
                    "ODDS": trade_odds,
                    "MATCH": target
                })
                st.rerun()
        with t2:
            p_title = st.text_input("Description", value="Monthly Profit Take")
            amt = st.number_input("Amount (₦)", min_value=0.0)
            if st.button("💸 RELEASE"):
                st.session_state.master_log.insert(0, {"DATE": now.strftime("%Y-%m-%d"), "TITLE": p_title, "RESULT": "PAYOUT", "AMOUNT": amt})
                st.balloons(); st.rerun()

# --- 7. RADAR & LOG ---
live_radar_data = process_live_radar(all_fixtures_raw)
st.divider()
st.subheader("📡 Sniper Radar (Strict 0-0)")
if live_radar_data: st.table(pd.DataFrame(live_radar_data))
else: st.info("No high-intensity 0-0 seeds found. Scanning...")

st.subheader("📜 Verified Instance Log")
if st.session_state.master_log:
    st.table(pd.DataFrame(st.session_state.master_log)[["DATE", "TITLE", "RESULT", "ODDS"]].head(10))
