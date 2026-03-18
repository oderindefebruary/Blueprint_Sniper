import streamlit as st
import pandas as pd
import requests
import gspread
from datetime import datetime
from google.oauth2 import service_account

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="TCSI Blueprint Terminal", layout="wide", page_icon="🛡️")

# Custom CSS for that "Institutional" look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ffaa00; color: black; font-weight: bold; }
    .stMetric { background-color: #1e2124; padding: 15px; border-radius: 10px; border: 1px solid #333; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURE CONNECTIONS (GOOGLE SHEETS) ---
@st.cache_resource
def init_connection():
    creds_dict = st.secrets["gcp_service_account"]
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    scoped_creds = credentials.with_scopes([
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ])
    gc = gspread.authorize(scoped_creds)
    return gc.open("TCSI_Master_Ledger")

try:
    sh = init_connection()
    audit_sheet = sh.worksheet("Audit_Log")
    intel_sheet = sh.worksheet("Intelligence_Feed")
except Exception as e:
    st.error(f"Database Connection Failed: {e}")
    st.stop()

# --- 3. DATA FETCHING (ODDS API) ---
API_KEY = st.secrets["ODDS_API_KEY"]
LEAGUE_KEYS = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_italy_serie_a", "soccer_france_ligue_1", "soccer_uefa_champs_league", "soccer_usa_mls"]

@st.cache_data(ttl=600)
def fetch_global_watchlist():
    watchlist = []
    for league in LEAGUE_KEYS:
        url = f"https://api.the-odds-api.com/v4/sports/{league}/odds/?apiKey={API_KEY}&regions=uk&markets=totals&oddsFormat=decimal"
        response = requests.get(url).json()
        if isinstance(response, list):
            for event in response:
                # Filter for Over 1.5 logic
                for bookie in event.get('bookmakers', []):
                    if bookie['key'] == 'betfair_ex_uk': # Using Exchange for higher TVI accuracy
                        for market in bookie['markets']:
                            if market['key'] == 'totals':
                                for outcome in market['outcomes']:
                                    if outcome['name'] == 'Over' and outcome['point'] == 1.5:
                                        watchlist.append({
                                            "time": event['commence_time'],
                                            "league": event['sport_title'],
                                            "match": f"{event['home_team']} vs {event['away_team']}",
                                            "odds": outcome['price']
                                        })
    return watchlist

# --- 4. AUTHENTICATION ---
IS_ADMIN = st.query_params.get("admin") == "true"
USER_RANK = st.query_params.get("rank", "Bronze")

# --- 5. THE HEADER HUD ---
# Read current TCSI from the last row of Audit Log
audit_data = pd.DataFrame(audit_sheet.get_all_records())
current_tcsi = float(audit_data['Impact'].iloc[-1]) if not audit_data.empty else 1.000
daily_target = 0.010
progress = min((current_tcsi - 1.0) / daily_target, 1.0)

col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    st.metric("TCSI INDEX", f"{current_tcsi:.3f}", f"{(current_tcsi-1)*100:+.2f}%")
with col2:
    st.write("### Daily 1% Growth Progress")
    st.progress(progress)
with col3:
    st.metric("SETTLEMENT RANK", USER_RANK, "Next: +10% Bonus")

# --- 6. LIVE INTELLIGENCE FEED (SIDEBAR) ---
st.sidebar.subheader("🎙️ Live Intelligence")
if IS_ADMIN:
    new_intel = st.sidebar.text_area("Post Update")
    if st.sidebar.button("Broadcast Update"):
        intel_sheet.append_row([datetime.now().strftime("%H:%M"), new_intel, "High"])
        st.rerun()

intel_data = pd.DataFrame(intel_sheet.get_all_records()).tail(5).iloc[::-1]
for _, row in intel_data.iterrows():
    st.sidebar.markdown(f"**[{row['Timestamp']}]** {row['Update']}")
    st.sidebar.divider()

# --- 7. GLOBAL WATCHLIST & EXECUTION ---
st.header("📡 Global Sniper Watchlist")
watchlist = fetch_global_watchlist()

if watchlist:
    df_watch = pd.DataFrame(watchlist)
    # Filter by user preference
    selected_leagues = st.multiselect("Filter Markets", df_watch['league'].unique(), default=df_watch['league'].unique())
    filtered_df = df_watch[df_watch['league'].isin(selected_leagues)]

    for _, row in filtered_df.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
            c1.caption(row['time'][11:16])
            c2.write(f"**{row['match']}**")
            c3.info(f"O1.5 @ {row['odds']}")
            
            if IS_ADMIN:
                if c4.button("EXECUTE", key=row['match']):
                    # Log the trade to the Google Sheet
                    new_impact = current_tcsi + 0.004 # Sample winning impact
                    audit_sheet.append_row([datetime.now().strftime("%Y-%m-%d %H:%M"), row['league'], row['match'], row['odds'], "ACTIVE", new_impact])
                    st.success("Trade Executed to Master Ledger")
                    st.rerun()
            else:
                c4.write("👁️ SPECTATING")
else:
    st.warning("No active Over 1.5 seeds found in the current scan.")

# --- 8. THE TVI HEATMAP ---
st.divider()
st.subheader("📊 Volatility Index (TVI)")
if watchlist:
    tvi_counts = df_watch['league'].value_counts(normalize=True)
    st.bar_chart(tvi_counts)
