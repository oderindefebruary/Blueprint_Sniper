import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="₦1M Blueprint Sniper", page_icon="🎯", layout="wide")

# API & BOT CONFIG (From Streamlit Secrets)
try:
    API_KEY = st.secrets["API_KEY"]
    TG_TOKEN = st.secrets["TG_TOKEN"]
    TG_CHAT_ID = st.secrets["TG_CHAT_ID"]
except KeyError:
    st.error("Secrets not found! Please add API_KEY, TG_TOKEN, and TG_CHAT_ID to Streamlit Secrets.")
    st.stop()

HEADERS = {"x-apisports-key": API_KEY}

# --- 2. SESSION STATE (User Personalization) ---
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 1000000.0
if 'stake_percent' not in st.session_state:
    st.session_state.stake_percent = 5.0

# --- 3. DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_seeded_matches():
    """Fetches Fixtures and filters for Triple-Lock seeding"""
    today = datetime.now().strftime('%Y-%m-%d')
    url = f"https://v3.football.api-sports.io/fixtures?date={today}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json().get("response", [])
        seeded = []
        for f in res:
            # Here you can add the specific GF/GA/Rank logic we discussed
            # For now, it pulls all upcoming matches for the radar
            seeded.append({
                "Time": f['fixture']['date'][11:16],
                "Match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}",
                "Status": f['fixture']['status']['short'],
                "ID": f['fixture']['id']
            })
        # Sort alphabetically by match name
        return sorted(seeded, key=lambda x: x['Match'])
    except Exception as e:
        st.error(f"API Connection Error: {e}")
        return []

# --- 4. SIDEBAR (User Settings) ---
st.sidebar.header("🏦 Personal Trading Desk")
user_dep = st.sidebar.number_input("Set Initial Deposit (₦)", value=st.session_state.bankroll, step=1000.0)
st.session_state.bankroll = user_dep

st.session_state.stake_percent = st.sidebar.slider("Stake % per trade", 1.0, 20.0, 5.0)
current_stake = (st.session_state.bankroll * st.session_state.stake_percent) / 100

st.sidebar.divider()
st.sidebar.metric("Your Trade Stake", f"₦{current_stake:,.2f}")

if st.sidebar.button("Reset Session"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- 5. MAIN DASHBOARD ---
st.title("🎯 Triple-Lock Sniper Dashboard")

col_radar, col_log = st.columns([2, 1])

with col_radar:
    st.subheader("📡 Live Market Radar")
    matches = get_seeded_matches()
    
    if matches:
        df = pd.DataFrame(matches)
        # SAFETY CHECK: Only display if columns exist to prevent KeyError
        if not df.empty and "Time" in df.columns and "Match" in df.columns:
            st.dataframe(df[["Time", "Match", "Status"]], use_container_width=True, hide_index=True)
        else:
            st.info("Searching for valid Triple-Lock fixtures...")
    else:
        st.info("🎯 Stalking markets... No fixtures found for this session.")

with col_log:
    st.subheader("📝 Signal Logbook")
    
    # Alphabetical Dropdown for Selections
    if matches:
        match_options = [m['Match'] for m in matches]
    else:
        match_options = ["No active matches"]
        
    selected_match = st.selectbox("Select Seeded Match", options=match_options)
    
    st.write(f"**Action for:** {selected_match}")
    c1, c2 = st.columns(2)
    
    if c1.button("✅ LOG WIN (1.12)", use_container_width=True, type="primary"):
        profit = current_stake * 0.12
        st.session_state.bankroll += profit
        st.toast(f"WIN: +₦{profit:,.2f}", icon="💰")
        
    if c2.button("❌ LOG LOSS", use_container_width=True):
        st.session_state.bankroll -= current_stake
        st.toast(f"LOSS: -₦{current_stake:,.2f}", icon="📉")

# --- 6. GOAL TRACKING ---
st.divider()
target = 1000000.0
progress = min(st.session_state.bankroll / target, 1.0) if target > 0 else 0

c_bank, c_prog = st.columns(2)
with c_bank:
    st.metric("Current Bankroll", f"₦{st.session_state.bankroll:,.2f}", 
              delta=f"₦{st.session_state.bankroll - user_dep:,.2f} since start")

with c_prog:
    st.write(f"**₦1M Goal Progress: {progress*100:.1f}%**")
    st.progress(progress)

st.caption("Note: This dashboard uses session memory. Refreshing the page will reset logs unless connected to a database.")
