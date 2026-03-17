import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import requests

# --- 1. SYSTEM CONFIG ---
st.set_page_config(page_title="🛡️ ₦1M Soccer Sniper", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
    <style>
    .main { background-color: #0e1117 !important; }
    .stApp { background-color: #0e1117 !important; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .stDeployButton {display:none;}
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; color: #00ff00 !important; text-align: center; }
    .block-container { padding: 1rem !important; }
    </style>
    """, unsafe_allow_html=True)

INITIAL_FUNDS = 1000000.0
STAKE_PCT = 5.0 

# --- 2. OPEN SOURCE SOCCER ENGINE ---
@st.cache_data(ttl=3600)
def get_open_soccer_fixtures():
    """
    Fetches real upcoming fixtures from an open-source friendly endpoint.
    This replaces the suspended API-Football.
    """
    try:
        # Using a public API endpoint for upcoming matches
        url = "https://worldcupjson.net/matches" # Publicly available soccer data
        res = requests.get(url, timeout=10).json()
        fixtures = []
        for match in res[:15]: # Take the top 15 upcoming/active games
            fixtures.append({
                "TIME": "READY" if match['status'] == 'future' else "LIVE",
                "FIXTURE": f"{match['home_team_country']} vs {match['away_team_country']}",
                "STATE": "🔥 HIGH" if match['status'] == 'future' else "⚽ ACTIVE"
            })
        return fixtures
    except:
        # Failsafe: Realistic seeds for Sunday's session
        return [
            {"TIME": "READY", "FIXTURE": "Liverpool vs Arsenal", "STATE": "🔥 HIGH"},
            {"TIME": "READY", "FIXTURE": "Barcelona vs Real Madrid", "STATE": "⚡ EXTREME"},
            {"TIME": "READY", "FIXTURE": "Bayern Munich vs Dortmund", "STATE": "🚨 CRITICAL"}
        ]

# --- 3. AUTH & STATE ---
IS_ADMIN = st.query_params.get("admin") == "true"
if 'master_log' not in st.session_state: 
    st.session_state.master_log = []

# --- 4. ANALYTICS ---
def calculate_metrics():
    balance = INITIAL_FUNDS
    ath = INITIAL_FUNDS
    total_paid_out = 0.0
    history = [{"Trade": 0, "Balance": balance, "Growth": 0.0, "DD": 0.0, "Label": "Baseline"}]
    
    for i, entry in enumerate(reversed(st.session_state.master_log)):
        label = entry.get("TITLE", "Trade")
        
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
            m_label = f"⚽ {label} (@{odds})"

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

st.markdown(f"<h1 style='text-align: center; color: white;'>🛡️ ₦1M SOCCER SNIPER</h1>", unsafe_allow_html=True)

# Metrics HUD
c1, c2, c3 = st.columns(3)
c1.metric("TOTAL ROI", f"{curr_roi:.2f}%")
c2.metric("PAYOUTS", f"₦{total_extracted:,.0f}")
c3.metric("CURRENT BAL", f"₦{eq_df['Balance'].iloc[-1]:,.0f}")

# Chart
fig = px.area(eq_df, x="Trade", y="Growth", title="Soccer Institutional Equity Path", 
             color_discrete_sequence=["#00ff00"], hover_data=["Label"])
fig.update_layout(template="plotly_dark", plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=40, b=0))
st.plotly_chart(fig, use_container_width=True)

# --- 6. ADMIN PANEL ---
if IS_ADMIN:
    with st.expander("🔑 SNIPER COMMANDER PANEL", expanded=True):
        t1, t2 = st.tabs(["Verify Signal", "Execute Payout"])
        with t1:
            trade_title = st.text_input("Strategy Description", placeholder="e.g. 0-0 Stalking Entry")
            
            # Fetch real fixtures for the dropdown
            fixtures = get_open_soccer_fixtures()
            match_list = [f['FIXTURE'] for f in fixtures]
            target = st.selectbox("Target Fixture", options=match_list + ["Manual Entry"])
            
            col_a, col_b = st.columns(2)
            odds = col_a.number_input("Odds Captured", min_value=1.01, value=1.12, step=0.01)
            res = col_b.selectbox("Result", ["WIN", "LOSS"])
            
            if st.button("🚀 LOG TO EQUITY CURVE"):
                st.session_state.master_log.insert(0, {
                    "DATE": datetime.now().strftime("%Y-%m-%d"),
                    "TITLE": trade_title if trade_title else target,
                    "RESULT": res, "ODDS": odds, "MATCH": target
                })
                st.rerun()
        with t2:
            amt = st.number_input("Payout (₦)", min_value=0.0)
            if st.button("💸 RELEASE PROFITS"):
                st.session_state.master_log.insert(0, {"DATE": datetime.now().strftime("%Y-%m-%d"), "TITLE": "Payout", "RESULT": "PAYOUT", "AMOUNT": amt})
                st.balloons(); st.rerun()

# --- 7. OPEN RADAR ---
st.divider()
st.subheader("📡 Sniper Radar (Open Source Feed)")
radar_data = get_open_soccer_fixtures()
st.table(pd.DataFrame(radar_data))

# --- 8. LOG TABLE ---
st.subheader("📜 Institutional Log")
if st.session_state.master_log:
    st.table(pd.DataFrame(st.session_state.master_log)[["DATE", "TITLE", "RESULT", "ODDS"]].head(5))
