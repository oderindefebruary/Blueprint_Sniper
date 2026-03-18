import streamlit as st
import pandas as pd
import requests
import gspread
from datetime import datetime
from google.oauth2 import service_account
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIGURATION & CYBER-DARK THEME ---
st.set_page_config(page_title="TCSI Blueprint Terminal", layout="wide", page_icon="⚡")

# Auto-refresh the dashboard every 5 minutes (300,000ms)
st_autorefresh(interval=300000, key="datarefresh")

st.markdown("""
    <style>
    /* Main Background & Glassmorphism */
    .stApp {
        background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
        color: #e0e0e0;
    }
    [data-testid="stVerticalBlock"] > div:has(div.stMetric) {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
    }
    /* Institutional Metric Colors */
    [data-testid="stMetricValue"] { color: #00ffcc !important; font-family: 'Courier New', monospace; }
    /* Neon Buttons */
    .stButton>button {
        border: 1px solid #00ffcc;
        background-color: transparent;
        color: #00ffcc;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00ffcc;
        color: #000;
        box-shadow: 0 0 15px #00ffcc;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE INITIALIZATION ---
@st.cache_resource
def init_db():
    creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    gc = gspread.authorize(creds.with_scopes(scope))
    return gc.open("TCSI_Master_Ledger")

sh = init_db()
audit_sheet = sh.worksheet("Audit_Log")
intel_sheet = sh.worksheet("Intelligence_Feed")

# Auth Check
IS_ADMIN = st.query_params.get("admin") == "true"
current_data = pd.DataFrame(audit_sheet.get_all_records())
current_index = float(current_data['Impact'].iloc[-1]) if not current_data.empty else 1.000

# --- 3. HEADER HUD (GLASS CARDS) ---
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("TCSI ASSET VALUE", f"{current_index:.4f}", f"{(current_index-1)*100:+.2f}%")
with col2:
    target_gap = 1.010 - current_index
    st.metric("DAILY GOAL GAP", f"{max(target_gap, 0):.4f}", "Target: +0.010")
with col3:
    st.metric("MARKET STATUS", "🟢 ACTIVE", "24/7 Global Scan")

# --- 4. ADMIN: PRECISION CALCULATOR & SETTLEMENT ---
if IS_ADMIN:
    with st.expander("🛠️ ADMIN COMMAND CENTER", expanded=True):
        st.subheader("🏁 Settle Active Trades")
        active_trades = current_data[current_data['Status'] == 'ACTIVE']
        
        if not active_trades.empty:
            # Dropdown to select match from the seeded list
            selected_match = st.selectbox("Select Match to Settle", active_trades['Match'].tolist())
            trade_row = active_trades[active_trades['Match'] == selected_match].iloc[0]
            gs_row_idx = active_trades[active_trades['Match'] == selected_match].index[0] + 2

            c_stake, c_odds = st.columns(2)
            stake = c_stake.number_input("Stake (₦)", min_value=0, value=10000, step=1000)
            odds = c_odds.number_input("Secured Odds", min_value=1.01, value=float(trade_row['Odds']), step=0.01)

            btn_win, btn_loss = st.columns(2)
            if btn_win.button("✅ LOG WIN"):
                profit = stake * (odds - 1)
                impact = profit / 1000000 # Scaling against the ₦1M target
                new_idx = current_index + impact
                audit_sheet.update_cell(gs_row_idx, 5, "WIN")
                audit_sheet.update_cell(gs_row_idx, 6, f"{new_idx:.4f}")
                st.success(f"Index updated to {new_idx:.4f}")
                st.rerun()

            if btn_loss.button("❌ LOG LOSS"):
                impact = -(stake / 1000000)
                new_idx = current_index + impact
                audit_sheet.update_cell(gs_row_idx, 5, "LOSS")
                audit_sheet.update_cell(gs_row_idx, 6, f"{new_idx:.4f}")
                st.error("Loss logged. Index adjusted.")
                st.rerun()
        else:
            st.info("No active trades found in the Ledger.")

# --- 5. GLOBAL SNIPER WATCHLIST (EXPANDED SEEDING) ---
st.header("📡 24/7 Global Watchlist")

@st.cache_data(ttl=600)
def fetch_high_goal_markets():
    # Expanded to include High-Frequency Goal Leagues (Norway, Netherlands, etc.)
    LEAGUES = ["soccer_epl", "soccer_uefa_champs_league", "soccer_germany_bundesliga", 
               "soccer_netherlands_eredivisie", "soccer_norway_eliteserien"]
    seeds = []
    for l in LEAGUES:
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{l}/odds/?apiKey={st.secrets['ODDS_API_KEY']}&regions=uk&markets=totals"
            data = requests.get(url).json()
            for event in data:
                for b in event.get('bookmakers', []):
                    if b['key'] == 'betfair_ex_uk':
                        for m in b['markets']:
                            for o in m['outcomes']:
                                if o['name'] == 'Over' and o['point'] == 1.5:
                                    seeds.append({"time": event['commence_time'], "match": f"{event['home_team']} vs {event['away_team']}", "odds": o['price'], "league": event['sport_title']})
        except: continue
    return seeds

watchlist = fetch_high_goal_markets()
if watchlist:
    for item in watchlist:
        with st.container():
            c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
            c1.caption(item['time'][11:16])
            c2.write(f"**{item['match']}**")
            c3.info(f"O1.5 @ {item['odds']}")
            if IS_ADMIN and c4.button("EXECUTE", key=item['match']):
                audit_sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), item['league'], item['match'], item['odds'], "ACTIVE", f"{current_index:.4f}"])
                st.rerun()
else:
    st.write("Scanning global markets... next pulse in 5 minutes.")
