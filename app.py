import streamlit as st
import pandas as pd
import requests
import gspread
from datetime import datetime
from google.oauth2 import service_account

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(page_title="TCSI Blueprint Terminal", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    div[data-testid="stMetricValue"] { font-size: 2.5rem; color: #ffaa00; }
    .stProgress > div > div > div > div { background-color: #00ff00; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATABASE & API CONNECTIONS ---
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
    st.error(f"⚠️ Connection Error: {e}")
    st.stop()

# --- 3. CORE LOGIC & AUTH ---
IS_ADMIN = st.query_params.get("admin") == "true"
USER_RANK = st.query_params.get("rank", "Bronze")

# Pull Master Data
audit_all = audit_sheet.get_all_records()
audit_df = pd.DataFrame(audit_all)

# Calculate Current Index (Institutional Base)
if not audit_df.empty:
    # Ensure Impact column is numeric
    audit_df['Impact'] = pd.to_numeric(audit_df['Impact'], errors='coerce')
    current_tcsi = audit_df['Impact'].iloc[-1]
else:
    current_tcsi = 1.000

# --- 4. HEADER HUD ---
col_idx, col_prog, col_rank = st.columns([1, 2, 1])

with col_idx:
    change = (current_tcsi - 1.000) * 100
    st.metric("TCSI INDEX", f"{current_tcsi:.3f}", f"{change:+.2f}%")

with col_prog:
    daily_target = 0.010
    current_growth = current_tcsi - 1.000
    progress_val = min(max(current_growth / daily_target, 0.0), 1.0)
    st.write(f"**Daily Target Progress (+{daily_target:.3f})**")
    st.progress(progress_val)
    if progress_val >= 1.0:
        st.success("🎯 TARGET ACHIEVED - SESSION LOCKED")

with col_rank:
    st.metric("CURRENT RANK", USER_RANK)

# --- 5. ADMIN SETTLEMENT PANEL (NEW) ---
if IS_ADMIN:
    st.divider()
    st.subheader("🏁 Admin: Settlement Command")
    
    if not audit_df.empty:
        active_trades = audit_df[audit_df['Status'] == 'ACTIVE']
        
        if not active_trades.empty:
            for idx, row in active_trades.iterrows():
                # Correct row index for gspread (1-based + header row)
                gs_row = idx + 2 
                
                with st.expander(f"LIVE: {row['Match']} (@{row['Odds']})"):
                    c1, c2 = st.columns(2)
                    
                    if c1.button(f"✅ LOG WIN (+0.004)", key=f"win_{idx}"):
                        new_val = current_tcsi + 0.004
                        audit_sheet.update_cell(gs_row, 5, "WIN")
                        audit_sheet.update_cell(gs_row, 6, f"{new_val:.3f}")
                        st.toast("Victory Logged!")
                        st.rerun()
                        
                    if c2.button(f"❌ LOG LOSS (-0.010)", key=f"loss_{idx}"):
                        new_val = current_tcsi - 0.010
                        audit_sheet.update_cell(gs_row, 5, "LOSS")
                        audit_sheet.update_cell(gs_row, 6, f"{new_val:.3f}")
                        st.toast("Loss Registered.")
                        st.rerun()
        else:
            st.info("No active trades awaiting settlement. Execute a seed below to begin.")

# --- 6. LIVE INTELLIGENCE FEED (SIDEBAR) ---
st.sidebar.title("🎙️ TCSI Intelligence")
if IS_ADMIN:
    msg = st.sidebar.text_area("Broadcast update to spectators:")
    if st.sidebar.button("Post Update"):
        intel_sheet.append_row([datetime.now().strftime("%H:%M"), msg, "Normal"])
        st.rerun()

intel_all = pd.DataFrame(intel_sheet.get_all_records()).tail(10).iloc[::-1]
for _, row in intel_all.iterrows():
    st.sidebar.markdown(f"**[{row['Timestamp']}]** {row['Update']}")
    st.sidebar.divider()

# --- 7. WATCHLIST ENGINE ---
st.header("📡 Global Sniper Watchlist")

@st.cache_data(ttl=300)
def get_live_odds():
    API_KEY = st.secrets["ODDS_API_KEY"]
    # Scanning major global leagues
    leagues = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga", "soccer_uefa_champs_league", "soccer_italy_serie_a"]
    all_data = []
    
    for l in leagues:
        url = f"https://api.the-odds-api.com/v4/sports/{l}/odds/?apiKey={API_KEY}&regions=uk&markets=totals&oddsFormat=decimal"
        res = requests.get(url).json()
        if isinstance(res, list):
            for event in res:
                for bookie in event.get('bookmakers', []):
                    if bookie['key'] == 'betfair_ex_uk': # Using Betfair Exchange for TVI accuracy
                        for mkt in bookie['markets']:
                            for out in mkt['outcomes']:
                                if out['name'] == 'Over' and out['point'] == 1.5:
                                    all_data.append({
                                        "time": event['commence_time'],
                                        "league": event['sport_title'],
                                        "match": f"{event['home_team']} vs {event['away_team']}",
                                        "odds": out['price']
                                    })
    return all_data

watchlist = get_live_odds()

if watchlist:
    df_watch = pd.DataFrame(watchlist)
    for _, row in df_watch.iterrows():
        with st.container():
            col_t, col_m, col_o, col_a = st.columns([1, 3, 1, 1])
            col_t.caption(row['time'][11:16])
            col_m.write(f"**{row['match']}** ({row['league']})")
            col_o.info(f"O1.5 @ {row['odds']}")
            
            if IS_ADMIN:
                if col_a.button("EXECUTE", key=f"ex_{row['match']}"):
                    audit_sheet.append_row([
                        datetime.now().strftime("%Y-%m-%d %H:%M"),
                        row['league'], row['match'], row['odds'], "ACTIVE", f"{current_tcsi:.3f}"
                    ])
                    st.toast("Asset Deployed!")
                    st.rerun()
            else:
                col_a.write("👁️ SPECTATING")
else:
    st.warning("No active Over 1.5 seeds currently meet institutional criteria.")

# --- 8. TVI HEATMAP ---
st.divider()
st.subheader("📊 Volatility Index (TVI)")
if watchlist:
    st.bar_chart(pd.DataFrame(watchlist)['league'].value_counts())
