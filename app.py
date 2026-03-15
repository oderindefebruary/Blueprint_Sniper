import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG & STYLING ---
st.set_page_config(page_title="₦1M Blueprint | Command Center", layout="wide")

# Institutional Dark Theme CSS
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
# Access via yourwebsite.com/sniper?admin=true
query_params = st.query_params
IS_ADMIN = query_params.get("admin") == "true"

# --- 3. PERSISTENT DATA ENGINE ---
if 'master_log' not in st.session_state:
    # Starting with empty log for your fresh launch
    st.session_state.master_log = []

def calculate_advanced_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Match": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        if entry["RESULT"] == "PAYOUT":
            payout_amount = entry.get("AMOUNT", 0)
            balance -= payout_amount
            total_paid_out += payout_amount
            match_name = f"💰 PAYOUT: ₦{payout_amount:,.0f}"
        else:
            stake = (balance * STAKE_PCT) / 100
            balance += (stake * 0.12) if "WIN" in entry["RESULT"] else -stake
            if balance > ath: ath = balance
            match_name = entry["MATCH"]

        dd = ((ath - balance) / ath) * 100 if ath > 0 else 0
        history.append({
            "Trade": i + 1, 
            "Balance": balance, 
            "Growth": (((balance + total_paid_out) - INITIAL_FUNDS) / INITIAL_FUNDS) * 100,
            "DD": dd, 
            "Match": match_name
        })
    return pd.DataFrame(history), total_paid_out

# --- 4. LIVE RADAR ENGINE ---
@st.cache_data(ttl=60)
def get_live_radar():
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json().get("response", [])
        radar = []
        for f in res:
            goals = (f['goals']['home'] or 0) + (f['goals']['away'] or 0)
            status = f['fixture']['status']['short']
            elapsed = f['fixture']['status']['elapsed'] or 0
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
    except: return []

# --- 5. PAYOUT COUNTDOWN ---
def get_payout_countdown():
    now = datetime.now()
    if now.month == 12: next_month = now.replace(year=now.year + 1, month=1, day=1)
    else: next_month = now.replace(month=now.month + 1, day=1)
    delta = next_month - now
    return delta.days, delta.seconds // 3600

# --- 6. DASHBOARD RENDER ---
days_left, hours_left = get_payout_countdown()
st.title("🛡️ ₦1M BLUEPRINT | INSTITUTIONAL COMMAND")
st.info(f"⏳ **PROFIT DISTRIBUTION COUNTDOWN:** {days_left} Days and {hours_left} Hours remaining until next Payout.")

# Metrics Logic
equity_df, total_extracted = calculate_advanced_metrics()
curr_growth = equity_df['Growth'].iloc[-1]
max_dd = equity_df['DD'].max()
curr_bal = equity_df['Balance'].iloc[-1]
total_trades = len([x for x in st.session_state.master_log if x["RESULT"] != "PAYOUT"])
avg_gain = curr_growth / total_trades if total_trades > 0 else 0
dod_growth = curr_growth - (equity_df['Growth'].iloc[-3] if len(equity_df) > 3 else 0)

# Performance HUD
h1, h2, h3, h4 = st.columns(4)
h1.metric("TOTAL ROI", f"{curr_growth:.2f}%")
h2.metric("REALIZED PAYOUTS", f"₦{total_extracted:,.0f}")
h3.metric("DoD VELOCITY", f"{dod_growth:+.2f}%")
h4.metric("MAX DRAWDOWN", f"{max_dd:.2f}%", delta_color="inverse")

# Growth Chart
fig_equity = px.area(equity_df, x="Trade", y="Growth", title="Percentage Growth Path (ROI)",
                    color_discrete_sequence=["#00ff00"], hover_data=["Match", "Balance"])
fig_equity.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', yaxis_title="Growth %")
st.plotly_chart(fig_equity, use_container_width=True)

# --- 7. ADMIN CONTROLS (SECRET) ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL PANEL", expanded=True):
        tab1, tab2 = st.tabs(["Verify Signal", "Execute Payout"])
        
        with tab1:
            radar_data = get_live_radar()
            match_opts = [m['FIXTURE'] for m in radar_data] if radar_data else ["Manual Entry"]
            target = st.selectbox("Select Target", options=match_opts)
            note = st.text_input("Admin Insights")
            c1, c2 = st.columns(2)
            if c1.button("✅ LOG WIN"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "WIN", "NOTE": note})
                st.rerun()
            if c2.button("❌ LOG LOSS"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": target, "RESULT": "LOSS", "NOTE": note})
                st.rerun()
        
        with tab2:
            p_amt = st.number_input("Payout Amount (₦)", min_value=0.0, step=1000.0)
            if st.button("🚀 RELEASE MONTHLY PAYOUT"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "MATCH": "MONTHLY PAYOUT", "RESULT": "PAYOUT", "AMOUNT": p_amt, "NOTE": "Profit Distribution"})
                st.balloons()
                st.rerun()

# --- 8. RADAR & LOG ---
r_col, l_col = st.columns(2)
with r_col:
    st.subheader("📡 High-Intensity Radar (0-0 Stalking)")
    live_fixtures = get_live_radar()
    if live_fixtures: st.table(pd.DataFrame(live_fixtures))
    else: st.info("Scanning global markets for Triple-Lock targets...")

with l_col:
    st.subheader("📜 Verified Trade History")
    if st.session_state.master_log:
        st.table(pd.DataFrame(st.session_state.master_log))
    else: st.info("No trades verified for this session.")

# --- 9. REPORTING ---
with st.expander("📊 GENERATE MONTHLY PERFORMANCE REPORT"):
    st.write(f"### 🏛️ PIP RESOURCES - {datetime.now().strftime('%B %Y')} STATEMENT")
    st.write(f"**Growth Status:** {curr_growth:.2f}% ROI")
    st.write(f"**Capital Extracted:** ₦{total_extracted:,.2f}")
    st.write(f"**Net Liquidity:** ₦{curr_bal:,.2f}")
    st.caption("Press Ctrl+P to save this statement as a PDF.")
