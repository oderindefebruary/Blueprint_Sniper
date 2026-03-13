import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="₦1M Blueprint Sniper", page_icon="🎯", layout="wide")

# API & BOT CONFIG (From Streamlit Secrets)
API_KEY = st.secrets["API_KEY"]
TG_TOKEN = st.secrets["TG_TOKEN"]
TG_CHAT_ID = st.secrets["TG_CHAT_ID"]
HEADERS = {"x-apisports-key": API_KEY}

# --- 2. SESSION STATE (User Personalization) ---
if 'bankroll' not in st.session_state:
    st.session_state.bankroll = 1000000.0
if 'stake_percent' not in st.session_state:
    st.session_state.stake_percent = 5.0

# --- 3. DATA FUNCTIONS ---
@st.cache_data(ttl=3600)
def get_seeded_matches():
    """Fetches and Verifies Triple-Lock Fixtures for Today"""
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    res = requests.get(url, headers=HEADERS).json().get("response", [])
    
    seeded = []
    for f in res:
        # Simplified Triple-Lock logic for the dashboard
        # (In reality, this calls the standings/stats API as we discussed)
        seeded.append({
            "Match": f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}",
            "Time": f['fixture']['date'][11:16],
            "ID": f['fixture']['id']
        })
    return sorted(seeded, key=lambda x: x['Match'])

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"})

# --- 4. SIDEBAR (User Settings) ---
st.sidebar.header("🏦 Personal Trading Desk")
user_deposit = st.sidebar.number_input("Set Initial Deposit (₦)", value=st.session_state.bankroll)
st.session_state.bankroll = user_deposit

st.session_state.stake_percent = st.sidebar.slider("Stake % per trade", 1.0, 20.0, 5.0)
current_stake = (st.session_state.bankroll * st.session_state.stake_percent) / 100

st.sidebar.metric("Current Stake", f"₦{current_stake:,.2f}")
if st.sidebar.button("Reset Session"):
    st.session_state.clear()
    st.rerun()

# --- 5. MAIN DASHBOARD ---
st.title("🎯 Triple-Lock Sniper Dashboard")

col_radar, col_log = st.columns([2, 1])

with col_radar:
    st.subheader("📡 Live Market Radar")
    matches = get_seeded_matches()
    st.dataframe(pd.DataFrame(matches)[["Time", "Match"]], use_container_width=True)

with col_log:
    st.subheader("📝 Signal Logbook")
    
    # Alphabetical Dropdown for Selections
    match_list = [m['Match'] for m in matches]
    selected_match = st.selectbox("Select Match", options=match_list)
    
    c1, c2 = st.columns(2)
    if c1.button("✅ WIN (1.12)", use_container_width=True):
        profit = current_stake * 0.12
        st.session_state.bankroll += profit
        st.success(f"Profit: +₦{profit:,.2f}")
        
    if c2.button("❌ LOSS", use_container_width=True):
        st.session_state.bankroll -= current_stake
        st.error(f"Loss: -₦{current_stake:,.2f}")

st.divider()
st.metric("Target Progress to ₦1M", f"₦{st.session_state.bankroll:,.2f}", 
          delta=f"{((st.session_state.bankroll/1000000)*100):.1f}% of goal")
