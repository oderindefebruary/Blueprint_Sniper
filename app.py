import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="🛡️ ₦1M Blueprint", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117 !important; }
    .stApp { background-color: #0e1117 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00ff00 !important; text-align: center; }
    .block-container { padding: 1rem !important; }
    .stTable { background-color: #0e1117 !important; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# API & GLOBAL CONSTANTS
# Ensure these are set in Streamlit Cloud -> Settings -> Secrets
try:
    API_KEY = st.secrets["API_KEY"]
except:
    API_KEY = "MISSING"

HEADERS = {"x-apisports-key": API_KEY, "Accept": "application/json"}
INITIAL_FUNDS = 1000000.0
STAKE_PCT = 5.0 

# --- 2. DATA ENGINES ---
@st.cache_data(ttl=30) # Reduced TTL to catch live changes faster
def get_football_data():
    if API_KEY == "MISSING": return {"error": "API Key is not set in Secrets."}
    
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        data = response.json()
        
        # Check for API-level errors
        if data.get("errors"):
            return {"error": str(data["errors"])}
        
        return data.get("response", [])
    except Exception as e:
        return {"error": str(e)}

def process_live_radar(fixtures):
    if not isinstance(fixtures, list): return []
    radar = []
    for f in fixtures:
        goals = (f.get('goals', {}).get('home') or 0) + (f.get('goals', {}).get('away') or 0)
        status = f.get('fixture', {}).get('status', {}).get('short', '')
        elapsed = f.get('fixture', {}).get('status', {}).get('elapsed') or 0
        
        # SNIPER RULE: Only 0-0 and matches in progress or about to start
        if goals == 0 and status in ["NS", "1H", "HT", "2H"]:
            intensity = "🔥 HIGH"
            if 30 <= elapsed <= 45: intensity = "⚡ EXTREME"
            if elapsed > 60: intensity = "🚨 CRITICAL"
            
            radar.append({
                "TIME": f"{elapsed}'" if status != "NS" else "READY", 
                "FIXTURE": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}", 
                "INTENSITY": intensity
            })
    return radar

# --- 3. FETCH & AUTH ---
raw_payload = get_football_data()
all_fixtures = raw_payload if isinstance(raw_payload, list) else []

IS_ADMIN = st.query_params.get("admin") == "true"
if 'master_log' not in st.session_state: st.session_state.master_log = []

# --- 4. ANALYTICS ---
def calculate_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Label": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        label = entry.get("TITLE", "Trade Instance")
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

# --- 5. RENDER UI ---
eq_df, total_extracted = calculate_metrics()
curr_roi = eq_df['Growth'].iloc[-1]

st.markdown(f"<h1 style='text-align: center; color: white; margin-bottom: 0;'>🛡️ ₦1M BLUEPRINT</h1>", unsafe_allow_html=True)
st.write(f"<p style='text-align: center; color: #888;'>Institutional Grade Sniper Console</p>", unsafe_allow_html=True)

# Metrics HUD
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL ROI", f"{curr_roi:.2f}%")
c2.metric("PAYOUTS", f"₦{total_extracted:,.0f}")
c3.metric("CURRENT BAL", f"₦{eq_df['Balance'].iloc[-1]:,.0f}")

# Chart
fig = px.area(eq_df, x="Trade", y="Growth", title="Equity Path", 
             color_discrete_sequence=["#00ff00"], hover_data=["Label"])
fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 6. ADMIN PANEL & DIAGNOSTICS ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL", expanded=True):
        # API HEALTH CHECK
        if isinstance(raw_payload, dict) and "error" in raw_payload:
            st.error(f"📡 API CONNECTION ERROR: {raw_payload['error']}")
        else:
            st.success(f"📡 API LIVE: Found {len(all_fixtures)} global fixtures.")
            
        t1, t2 = st.tabs(["Log Instance", "Log Payout"])
        with t1:
            col_a, col_b = st.columns([1, 2])
            asset_ico = col_a.selectbox("Asset", ["⚽ Football", "🟡 Gold (XAU)"])
            trade_title = col_b.text_input("Trade Description", placeholder="e.g. Elite 5 Sniper Entry")
            
            match_names = [f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in all_fixtures]
            target = st.selectbox("API Target", options=sorted(match_names) if match_names else ["Manual Entry"])
            
            c_odds, c_res = st.columns(2)
            odds = c_odds.number_input("Odds", min_value=1.01, value=1.12, step=0.01)
            res = c_res.selectbox("Result", ["WIN", "LOSS"])
            
            if st.button("🚀 EXECUTE LOG"):
                st.session_state.master_log.insert(0, {
                    "DATE": datetime.now().strftime("%Y-%m-%d"),
                    "ASSET": "⚽" if "Football" in asset_ico else "🟡",
                    "TITLE": trade_title if trade_title else target,
                    "RESULT": res, "ODDS": odds, "MATCH": target
                })
                st.rerun()
        
        with t2:
            p_amt = st.number_input("Payout (₦)", min_value=0.0)
            if st.button("💸 RELEASE FUNDS"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "TITLE": "Payout", "RESULT": "PAYOUT", "AMOUNT": p_amt})
                st.balloons(); st.rerun()

# --- 7. SNIPER RADAR ---
st.divider()
st.subheader("📡 Sniper Radar (Active 0-0)")
live_radar = process_live_radar(all_fixtures)
if live_radar:
    st.table(pd.DataFrame(live_radar))
else:
    st.info("Searching for high-intensity seeds... (API Status: Online)")

# --- 8. LOG TABLE ---
st.subheader("📜 Instance History")
if st.session_state.master_log:
    st.table(pd.DataFrame(st.session_state.master_log)[["DATE", "TITLE", "RESULT", "ODDS"]].head(5))
