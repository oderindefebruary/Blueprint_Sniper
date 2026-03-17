import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

# --- 1. CONFIG & SYSTEM RESET ---
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

# --- 2. LIVE GLOBAL ENGINE (NO FILTERS) ---
@st.cache_data(ttl=30)
def get_global_live_scores():
    """Fetches ALL live matches globally using a public endpoint."""
    try:
        url = "https://prod-public-api.livescore.com/v1/api/react/live/soccer/0.00?MD=1"
        res = requests.get(url, timeout=10).json()
        matches = []
        for stage in res.get('Stages', []):
            league = stage.get('Snm', 'Other')
            for event in stage.get('Events', []):
                score = f"{event.get('Tr1', '0')}-{event.get('Tr2', '0')}"
                status = event.get('Eps', 'NS')
                
                matches.append({
                    "CLOCK": status,
                    "FIXTURE": f"{event['T1'][0]['Nm']} vs {event['T2'][0]['Nm']}",
                    "SCORE": score,
                    "LEAGUE": league
                })
        return matches
    except:
        return []

# --- 3. AUTH & STATE ---
if 'master_log' not in st.session_state: st.session_state.master_log = []
IS_ADMIN = st.query_params.get("admin") == "true"

# --- 4. RENDER DASHBOARD ---
st.markdown("<h1 style='text-align: center; color: white;'>🛡️ ₦1M COMMAND CENTER</h1>", unsafe_allow_html=True)

# Metrics HUD (Simulated for Video)
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL ROI", "0.00%")
c2.metric("PAYOUTS", "₦0")
c3.metric("STATUS", "LIVE")

# Live Radar
st.divider()
st.subheader("📡 Global Live Radar")
live_matches = get_global_live_scores()

if live_matches:
    df = pd.DataFrame(live_matches)
    st.table(df[["CLOCK", "FIXTURE", "SCORE", "LEAGUE"]].head(15))
else:
    st.info("Awaiting next match wave. Scanning global markets...")

# --- 5. ADMIN LOGGING ---
if IS_ADMIN:
    with st.expander("🔑 LOG VERIFIED INSTANCE", expanded=True):
        col1, col2 = st.columns(2)
        match_select = col1.selectbox("Target", [m['FIXTURE'] for m in live_matches] + ["Manual Entry"])
        odds = col2.number_input("Odds", value=1.12)
        if st.button("🚀 LOG WIN"):
            st.success(f"Logged {match_select} @ {odds}")
