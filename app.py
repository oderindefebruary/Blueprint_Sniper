# --- 1. NEW: ADMIN MASTER LIST ENGINE ---
@st.cache_data(ttl=300) # Longer cache for the full list
def get_admin_master_list():
    """Fetches ALL fixtures for the day, ignoring the 0-0 filter for Admin logging."""
    url = f"https://v3.football.api-sports.io/fixtures?date={datetime.now().strftime('%Y-%m-%d')}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json().get("response", [])
        # Get everything so you can log any game, even after a goal
        return [f"{f['teams']['home']['name']} vs {f['teams']['away']['name']}" for f in res]
    except:
        return ["Manual Entry"]

# --- 2. UPDATED ADMIN PANEL ---
if IS_ADMIN:
    with st.expander("🔑 ADMIN MASTER CONTROL PANEL", expanded=True):
        tab1, tab2 = st.tabs(["Verify Signal", "Execute Payout"])
        
        with tab1:
            # We now use the MASTER LIST instead of the filtered radar
            all_matches = get_admin_master_list()
            target = st.selectbox("Select Target (All Today's Games)", options=all_matches)
            
            note = st.text_input("Admin Insights (e.g., 'Goal @ 34min')")
            c1, c2 = st.columns(2)
            if c1.button("✅ LOG WIN"):
                st.session_state.master_log.insert(0, {
                    "DATE": datetime.now().strftime("%Y-%m-%d"), 
                    "MATCH": target, 
                    "RESULT": "WIN", 
                    "NOTE": note
                })
                st.rerun()
            if c2.button("❌ LOG LOSS"):
                st.session_state.master_log.insert(0, {
                    "DATE": datetime.now().strftime("%Y-%m-%d"), 
                    "MATCH": target, 
                    "RESULT": "LOSS", 
                    "NOTE": note
                })
                st.rerun()
