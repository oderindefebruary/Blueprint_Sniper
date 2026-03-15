import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG & STYLING ---
# We use 'centered' to keep everything in the safe zone of your WordPress page
st.set_page_config(page_title="₦1M Blueprint", layout="centered", initial_sidebar_state="collapsed")

# Professional Institutional Styling
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Center all metrics and adjust font for high-impact readability */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important; 
        color: #00ff00 !important; 
        font-family: 'Courier New', monospace;
    }
    
    /* Pull the app up to the top of the page */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }

    /* Table styling for the Radar */
    .stTable {background-color: #0e1117 !important;}
    </style>
    """, unsafe_allow_html=True)

# API & GLOBAL CONSTANTS
API_KEY = st.secrets["API_KEY"]
HEADERS = {"x-apisports-key": API_KEY}
INITIAL_FUNDS = 1000000.0
STAKE_PCT = 5.0 

# --- 2. DATA ENGINES ---
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
        goals = (f.get('goals', {}).get('home') or 0) + (f.get('goals', {}).get('away') or 0)
        status = f.get('fixture', {}).get('status', {}).get('short', '')
        elapsed = f.get('fixture', {}).get('status', {}).get('elapsed') or 0
        if goals == 0 and status in ["NS", "1H", "HT", "2H"]:
            intensity = "🔥 HIGH"
            if 30 <= elapsed <= 45: intensity = "⚡ EXTREME"
            if 60 <= elapsed <= 80: intensity = "🚨 CRITICAL"
            radar.append({
                "TIME": f"{elapsed}'" if status != "NS" else "READY", 
                "FIXTURE": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", 
                "INTENSITY": intensity
            })
    return radar

# --- 3. FETCH DATA ---
all_fixtures_raw = get_football_data()

# --- 4. AUTHENTICATION ---
IS_ADMIN = st.query_params.get("admin") == "true"

if 'master_log' not in st.session_state:
    st.session_state.master_log = []

# --- 5. ANALYTICS ---
def calculate_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Match": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        if entry["RESULT"] == "PAYOUT":
            p_amt = entry.get("AMOUNT", 0)
            balance -= p_amt
            total_paid_out += p_amt
            m_name = f"💰 PAYOUT: ₦{p_amt:,.0f}"
        else:
            stake = (balance * STAKE_PCT) / 100
            balance += (stake * 0.12) if entry["RESULT"] == "WIN" else -stake
            if balance > ath: ath = balance
            m_name = entry["MATCH"]

        dd = ((ath - balance) / ath) * 100 if ath > 0 else 0
        history.append({
            "Trade": i + 1, "Balance": balance, 
            "Growth": (((balance + total_paid_out) - INITIAL_FUNDS) / INITIAL_FUNDS) * 100,
            "DD": dd, "Match": m_name
        })
    return pd.DataFrame(history), total_paid_out

# --- 6. RENDER HUD ---
eq_df, total_payouts = calculate_metrics()
curr_roi = eq_df['Growth'].iloc[-1]
curr_dd = eq_df['DD'].max()
now = datetime.now()
days_to_pay = ( (now.replace(day=28) + timedelta(days=4)).replace(day=1) - now ).days

# Title & Status Bar
st.markdown(f"<h1 style='text-align: center;'>🛡️ #1M BLUEPRINT</h1>", unsafe_allow_html=True)
st.info(f"⏳ **PAYOUT COUNTDOWN:** {days_to_pay} Days remaining.")

# HUD - 2x2 Grid for Perfect Alignment
c1, c2 = st.columns(2)
c1.metric("TOTAL ROI", f"{curr_roi:.2f}%")
c2.metric("PAYOUTS", f"₦{total_payouts:,.0f}")

c3, c4 = st.columns(2)
velocity = (curr_roi - (eq_df['Growth'].iloc[-3] if len(eq_df) > 3 else 0))
c3.metric("DoD VELOCITY", f"{velocity:+.2f}%")
c4.metric("MAX DRAWDOWN", f"{curr_dd:.2f}%", delta_color="inverse")

# Main Growth Chart - Adjusted for Centered Layout
fig = px.area(eq_df, x="Trade", y="Growth", title="Growth Path (ROI %)", 
             color_discrete_sequence=["#00ff00"], hover_data=["Match"])
fig.update_layout(
    template="plotly_dark", 
    plot_bgcolor='rgba(0,0,0,0)', 
    paper_bgcolor='rgba(0,0,0,0)',
    margin=dict(l=0, r=0, t=30, b=0)
)
st.plotly_chart(fig, use_container_width=True)

# --- 7. ADMIN PANEL ---
if IS_ADMIN:
    st.sidebar.success("🛡️ ADMIN ACTIVE")
    with st.expander("🔑 ADMIN MASTER CONTROL PANEL", expanded=True):
        t1, t2 = st.tabs(["Signals", "Payroll"])
        with t1:
            all_names = [f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in all_fixtures_raw]
            target = st.selectbox("Select Target", options=sorted(all_names) if all_names else ["Manual Entry"])
            note = st.text_input("Insight")
            b1, b2 = st.columns(2)
            if b1.button("✅ LOG WIN"):
                st.session_state.master_log.insert(0, {"DATE": now.strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "WIN", "NOTE": note})
                st.rerun()
            if b2.button("❌ LOG LOSS"):
                st.session_state.master_log.insert(0, {"DATE": now.strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "LOSS", "NOTE": note})
                st.rerun()
        with t2:
            amt = st.number_input("Payout Amount", min_value=0.0)
            if st.button("🚀 RELEASE"):
                st.session_state.master_log.insert(0, {"DATE": now.strftime("%Y-%m-%d"), "MATCH": "PAYOUT", "RESULT": "PAYOUT", "AMOUNT": amt})
                st.balloons()
                st.rerun()

# --- 8. RADAR & LOG ---
live_radar_data = process_live_radar(all_fixtures_raw)
st.divider()
st.subheader("📡 High-Intensity Radar")
if live_radar_data: st.table(pd.DataFrame(live_radar_data))
else: st.info("Scanning for 0-0 targets...")

st.subheader("📜 Institutional Trade Log")
if st.session_state.master_log: st.table(pd.DataFrame(st.session_state.master_log).head(5))
else: st.info("No trades verified in this session.")
