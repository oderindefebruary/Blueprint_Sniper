import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG & STYLING ---
st.set_page_config(page_title="₦1M Blueprint | Command Center", layout="wide")

# Hide Streamlit UI & Apply Institutional Dark Theme
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stMetricValue"] {font-size: 2.2rem !important; color: #00ff00 !important; font-family: 'Courier New', monospace;}
    .stTable {background-color: #0e1117 !important;}
    .stInfo {background-color: #001524 !important; border-left: 5px solid #00ff00 !important; color: white !important;}
    </style>
    """, unsafe_allow_html=True)

# API & GLOBAL CONSTANTS
API_KEY = st.secrets["API_KEY"]
HEADERS = {"x-apisports-key": API_KEY}
INITIAL_FUNDS = 1000000.0
STAKE_PCT = 5.0 

# --- 2. ADMIN AUTHENTICATION ---
# URL Access: yourwebsite.com/sniper?admin=true
query_params = st.query_params
IS_ADMIN = query_params.get("admin") == "true"

# --- 3. DATA PERSISTENCE & ANALYTICS ---
if 'master_log' not in st.session_state:
    st.session_state.master_log = []

def calculate_advanced_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Match": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        if entry["RESULT"] == "PAYOUT":
            p_amt = entry.get("AMOUNT", 0)
            balance -= p_amt
            total_paid_out += p_amt
            match_name = f"💰 PAYOUT: ₦{p_amt:,.0f}"
        else:
            stake = (balance * STAKE_PCT) / 100
            balance += (stake * 0.12) if entry["RESULT"] == "WIN" else -stake
            if balance > ath: ath = balance
            match_name = entry["MATCH"]

        dd = ((ath - balance) / ath) * 100 if ath > 0 else 0
        history.append({
            "Trade": i + 1, "Balance": balance, 
            "Growth": (((balance + total_paid_out) - INITIAL_FUNDS) / INITIAL_FUNDS) * 100,
            "DD": dd, "Match": match_name
        })
    return pd.DataFrame(history), total_paid_out

# --- 4. THE ENGINES (RADAR & MASTER LIST) ---
@st.cache_data(ttl=60)
def get_football_data():
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        return requests.get(url, headers=HEADERS, timeout=10).json().get("response", [])
    except: return []

def process_live_radar(fixtures):
    radar = []
    for f in fixtures:
        goals = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
        status = f['fixture']['status']['short']
        elapsed = f['fixture']['status']['elapsed'] or 0
        if goals == 0 and status in ["NS", "1H", "HT", "2H"]:
            intensity = "🔥 HIGH"
            if 30 <= elapsed <= 45: intensity = "⚡ EXTREME"
            if 60 <= elapsed <= 80: intensity = "🚨 CRITICAL"
            radar.append({"TIME": f"{elapsed}'" if status != "NS" else "READY", 
                         "FIXTURE": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", 
                         "INTENSITY": intensity})
    return radar

# --- 5. UI COMPONENTS ---
def get_payout_countdown():
    now = datetime.now()
    if now.month == 12: next_month = now.replace(year=now.year + 1, month=1, day=1)
    else: next_month = now.replace(month=now.month + 1, day=1)
    delta = next_month - now
    return delta.days, delta.seconds // 3600

# --- 6. RENDER DASHBOARD ---
days, hours = get_payout_countdown()
st.title("🛡️ ₦1M BLUEPRINT | INSTITUTIONAL COMMAND")
st.info(f"⏳ **PROFIT DISTRIBUTION COUNTDOWN:** {days} Days and {hours} Hours remaining.")

# Calculate Metrics
equity_df, total_extracted = calculate_advanced_metrics()
curr_growth = equity_df['Growth'].iloc[-1]
max_dd = equity_df['DD'].max()
total_trades = len([x for x in st.session_state.master_log if x["RESULT"] != "PAYOUT"])
dod_growth = curr_growth - (equity_df['Growth'].iloc[-3] if len(equity_df) > 3 else 0)
mom_index = curr_growth / 30.0

# Performance HUD
h1, h2, h3, h4 = st.columns(4)
h1.metric("TOTAL ROI", f"{curr_growth:.2f}%")
h2.metric("REALIZED PAYOUTS", f"₦{total_extracted:,.0f}")
h3.metric("DoD VELOCITY", f"{dod_growth:+.2f}%")
h4.metric("MAX DRAWDOWN", f"{max_dd:.2f}%", delta_color="inverse")

# Main Charts
c_main, c_bar = st.columns([2, 1])
with c_main:
    fig_eq = px.area(equity_df, x="Trade", y="Growth", title="Growth Path (ROI %)", 
                    color_discrete_sequence=["#00ff00"], hover_data=["Match"])
    fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig_eq, use_container_width=True)

with c_bar:
    periodic = pd.DataFrame({"Period": ["Week 1", "Week 2", "Week 3", "Today"], "ROI": [14.2, 8.5, -4.1, curr_growth]})
    fig_b = px.bar(periodic, x="Period", y="ROI", color="ROI", color_continuous_scale=['#ff4b4b', '#00ff00'], title="Consistency Index")
    fig_b.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
    st.plotly_chart(fig_b, use_container_width=True)

# --- 7. ADMIN GOD-MODE (SECRET) ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL PANEL", expanded=True):
        t1, t2 = st.tabs(["Signal Verification", "Payroll Management"])
        all_data = get_football_data()
        
        with t1:
            # Master list of ALL today's games for admin selection
            all_fixtures = [f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in all_data]
            target = st.selectbox("Select Target Match", options=sorted(all_fixtures) if all_fixtures else ["Manual Entry"])
            note = st.text_input("Trade Insight")
            b1, b2 = st.columns(2)
            if b1.button("✅ LOG WIN"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "WIN", "NOTE": note})
                st.rerun()
            if b2.button("❌ LOG LOSS"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "LOSS", "NOTE": note})
                st.rerun()
        
        with t2:
            p_amt = st.number_input("Payout Amount (₦)", min_value=0.0)
            if st.button("🚀 EXECUTE PAYROLL"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": "PAYOUT", "RESULT": "PAYOUT", "AMOUNT": p_amt})
                st.balloons()
                st.rerun()

# --- 8. RADAR & HISTORY ---
live_data = process_live_radar(all_data)
st.divider()
r_col, l_col = st.columns(2)
with r_col:
    st.subheader("📡 High-Intensity Radar (0-0 Stalking)")
    if live_data: st.table(pd.DataFrame(live_data))
    else: st.info("Scanning for Triple-Lock 0-0 targets...")

with l_col:
    st.subheader("📜 Institutional Trade Log")
    if st.session_state.master_log: st.table(pd.DataFrame(st.session_state.master_log).head(10))
    else: st.info("No trades verified in this session.")

# --- 9. MONTHLY STATEMENT ---
with st.expander("📊 GENERATE OFFICIAL STATEMENT"):
    st.markdown(f"### 🏛️ PIP RESOURCES STATEMENT: {datetime.now().strftime('%B %Y')}")
    st.write(f"**Growth:** {curr_growth:.2f}% | **Payouts:** ₦{total_extracted:,.0f} | **Status:** Active")
    st.caption("Right-click to print as PDF for your records.")
