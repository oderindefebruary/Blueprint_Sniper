import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG & STYLING ---
st.set_page_config(page_title="₦1M Blueprint | Command Center", layout="wide")

# Institutional Dark Theme & Metric Styling
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

# --- 2. DATA ENGINES ---
@st.cache_data(ttl=60)
def get_football_data():
    """Fetches global fixture data for the day."""
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        return res.get("response", [])
    except Exception:
        return []

def process_live_radar(fixtures):
    """Filters data for the public 'Kill Zone' (0-0 high intensity)."""
    if not fixtures:
        return []
    radar = []
    for f in fixtures:
        goals = (f.get('goals', {}).get('home') or 0) + (f.get('goals', {}).get('away') or 0)
        status = f.get('fixture', {}).get('status', {}).get('short', '')
        elapsed = f.get('fixture', {}).get('status', {}).get('elapsed') or 0
        
        # Only 0-0 matches currently in play or about to start
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

# --- 3. FETCH GLOBAL DATA (SCOPE FIX) ---
# This line MUST be outside any 'if' blocks so all users can see the radar.
all_data = get_football_data()

# --- 4. ADMIN & ANALYTICS ---
query_params = st.query_params
IS_ADMIN = query_params.get("admin") == "true"

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

# --- 5. RENDER HUD ---
equity_df, total_extracted = calculate_advanced_metrics()
curr_growth = equity_df['Growth'].iloc[-1]
max_dd = equity_df['DD'].max()
now = datetime.now()
next_month = (now.replace(day=28) + timedelta(days=4)).replace(day=1)
days_to_payout = (next_month - now).days

st.title("🛡️ ₦1M BLUEPRINT | COMMAND CENTER")
st.info(f"⏳ **PROFIT DISTRIBUTION COUNTDOWN:** {days_to_payout} Days remaining until next Payout.")

h1, h2, h3, h4 = st.columns(4)
h1.metric("TOTAL ROI", f"{curr_growth:.2f}%")
h2.metric("REALIZED PAYOUTS", f"₦{total_extracted:,.0f}")
h3.metric("DoD VELOCITY", "+0.00%") # Placeholder for velocity calc
h4.metric("MAX DRAWDOWN", f"{max_dd:.2f}%", delta_color="inverse")

# Growth Chart
fig_eq = px.area(equity_df, x="Trade", y="Growth", title="Growth Path (ROI %)", 
                color_discrete_sequence=["#00ff00"], hover_data=["Match"])
fig_eq.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
st.plotly_chart(fig_eq, use_container_width=True)

# --- 6. ADMIN PANEL ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL PANEL", expanded=True):
        t1, t2 = st.tabs(["Signal Verification", "Payroll Management"])
        with t1:
            # Master list of ALL today's games
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

# --- 7. RADAR & LOG ---
live_radar = process_live_radar(all_data)
st.divider()
r_col, l_col = st.columns(2)
with r_col:
    st.subheader("📡 High-Intensity Radar (0-0 Stalking)")
    if live_radar: st.table(pd.DataFrame(live_radar))
    else: st.info("Scanning for Triple-Lock 0-0 targets...")

with l_col:
    st.subheader("📜 Institutional Trade Log")
    if st.session_state.master_log: st.table(pd.DataFrame(st.session_state.master_log).head(10))
    else: st.info("No trades verified in this session.")
