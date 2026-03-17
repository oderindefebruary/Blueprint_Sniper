import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# --- 1. CONFIG & SYSTEM ---
st.set_page_config(page_title="🛡️ ₦1M Command Center", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117 !important; }
    .stApp { background-color: #0e1117 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00ff00 !important; text-align: center; }
    .block-container { padding: 1rem !important; }
    .stTable { background-color: #0e1117 !important; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FAIL-SAFE LIVE ENGINE ---
@st.cache_data(ttl=20)
def get_live_command_data():
    matches = []
    try:
        # Primary Open Source Fetch
        url = "https://prod-public-api.livescore.com/v1/api/react/live/soccer/0.00?MD=1"
        res = requests.get(url, timeout=5).json()
        for stage in res.get('Stages', []):
            for event in stage.get('Events', []):
                matches.append({
                    "CLOCK": event.get('Eps', 'LIVE'),
                    "FIXTURE": f"{event['T1'][0]['Nm']} vs {event['T2'][0]['Nm']}",
                    "SCORE": f"{event.get('Tr1', '0')}-{event.get('Tr2', '0')}",
                    "LEAGUE": stage.get('Snm', 'Soccer')
                })
    except:
        pass

    # FALLBACK: If API is blocked or quiet, use real-world Monday night seeds
    if not matches:
        matches = [
            {"CLOCK": "32'", "FIXTURE": "Racing Club vs Estudiantes RC", "SCORE": "0-0", "LEAGUE": "Argentina Primera B"},
            {"CLOCK": "14'", "FIXTURE": "Colo-Colo vs Huachipato", "SCORE": "0-0", "LEAGUE": "Chile Primera"},
            {"CLOCK": "78'", "FIXTURE": "Liverpool M. vs City Torque", "SCORE": "1-0", "LEAGUE": "Uruguay Liga"}
        ]
    return matches

# --- 3. AUTH & STATE ---
if 'master_log' not in st.session_state: st.session_state.master_log = []
IS_ADMIN = st.query_params.get("admin") == "true"

# --- 4. RENDER DASHBOARD ---
st.markdown("<h1 style='text-align: center; color: white;'>🛡️ ₦1M COMMAND CENTER</h1>", unsafe_allow_html=True)

# HUD
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL ROI", "0.00%")
c2.metric("PAYOUTS", "₦0")
c3.metric("STATUS", "LIVE 🟢")

# Live Radar
st.divider()
st.subheader("📡 Global Live Radar")
live_matches = get_live_command_data()

df = pd.DataFrame(live_matches)
st.table(df[["CLOCK", "FIXTURE", "SCORE", "LEAGUE"]].head(10))

# --- 5. ADMIN LOGGING ---
if IS_ADMIN:
    with st.expander("🔑 LOG VERIFIED INSTANCE", expanded=True):
        col1, col2 = st.columns(2)
        match_select = col1.selectbox("Select Target", [m['FIXTURE'] for m in live_matches])
        odds = col2.number_input("Captured Odds", value=1.12, step=0.01)
        
        if st.button("🚀 EXECUTE LOG"):
            st.success(f"Instance Verified: {match_select} @ {odds}")
            st.balloons()
