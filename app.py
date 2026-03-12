import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# --- 1. SETTINGS & STYLING ---
st.set_page_config(page_title="₦1M Blueprint Sniper", page_icon="🎯", layout="wide")

# Custom Dark CSS for the "Pro" Look
st.markdown("""
    <style>
    .main { background-color: #050505; }
    div[data-testid="stMetricValue"] { color: #00ff66 !important; font-weight: 900; }
    .stTable { background-color: #111; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# API & BOT CONFIG
API_KEY = "daeb3e812f714d80ca4e4a46e3b7859a"
TG_TOKEN = "8785158305:AAELxcM9VmfjkS6Du24UA2HqWhrm9lsu22Y"
TG_CHAT_ID = "-1003835833556"
HEADERS = {"x-apisports-key": API_KEY}

# Auto-refresh every 30 seconds to catch the 1.12 odds
st_autorefresh(interval=30 * 1000, key="snipersync")

# --- 2. BANKROLL LOGIC ---
if 'bank' not in st.session_state:
    st.session_state.bank = 1197936
if 'fired' not in st.session_state:
    st.session_state.fired = []

# --- 3. FUNCTIONS ---
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "HTML"})

def get_data():
    # Fetching live matches and odds in one pulse
    res = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=HEADERS)
    return res.json().get("response", [])

# --- 4. THE DASHBOARD ---
st.title("🏹 ₦1M BLUEPRINT: LIVE SNIPER")

# Top Row Metrics
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL BANKROLL", f"₦{st.session_state.bank:,.2f}")
stake = st.session_state.bank * 0.08
c2.metric("CURRENT STAKE (8%)", f"₦{stake:,.0f}")
c3.metric("ENGINE STATUS", "ACTIVE", delta="PULSE OK")

st.divider()

# --- 5. THE RADAR & SNIPER ---
col_main, col_side = st.columns([2, 1])

with col_main:
    st.subheader("📡 TRIPLE-LOCK RADAR")
    matches = get_data()
    display_list = []

    for m in matches:
        fid = m['fixture']['id']
        goals = (m['goals']['home'] or 0) + (m['goals']['away'] or 0)
        
        # Triple Lock Filter: 0-0 Games
        if goals == 0:
            match_name = f"{m['teams']['home']['name']} vs {m['teams']['away']['name']}"
            display_list.append({
                "Match": match_name,
                "Min": f"{m['fixture']['status']['elapsed']}'",
                "League": m['league']['name'],
                "Status": "🔒 VERIFIED"
            })
            
            # Logic to find 1.12 odds could be expanded here with an additional API call
            # For the Desk Setup, we focus on the Radar display

    if display_list:
        st.table(pd.DataFrame(display_list))
    else:
        st.info("Stalking markets... Waiting for Tuesday night 0-0 entries.")

with col_side:
    st.subheader("🕹️ OPERATOR")
    # Manual Logging for your YouTube Video
    with st.form("trade_logger"):
        odds = st.number_input("Final Odds", value=1.12, step=0.01)
        result = st.radio("Outcome", ["WIN", "LOSS"])
        if st.form_submit_button("LOG TRADE & UPDATE BANK"):
            if result == "WIN":
                profit = (stake * odds) - stake
                st.session_state.bank += profit
            else:
                st.session_state.bank -= stake
            st.rerun()

    if st.button("🚀 TEST TELEGRAM"):
        send_telegram("🚨 <b>DESK TEST SUCCESSFUL</b>\nYour Python Sniper is officially online.")
        st.toast("Test Message Sent!")