# --- 2. RAPID-REFRESH SOCCER ENGINE ---
@st.cache_data(ttl=30) # Forces a refresh every 30 seconds
def get_open_soccer_fixtures():
    """
    Fetches real upcoming fixtures. 
    Reduced TTL ensures data rotates as games end/start.
    """
    try:
        url = "https://prod-public-api.livescore.com/v1/api/react/live/soccer/0.00?MD=1"
        res = requests.get(url, timeout=5).json()
        matches = []
        for stage in res.get('Stages', []):
            for event in stage.get('Events', []):
                matches.append({
                    "CLOCK": event.get('Eps', 'LIVE'),
                    "FIXTURE": f"{event['T1'][0]['Nm']} vs {event['T2'][0]['Nm']}",
                    "SCORE": f"{event.get('Tr1', '0')}-{event.get('Tr2', '0')}",
                    "LEAGUE": stage.get('Snm', 'Soccer')
                })
        return matches
    except:
        # If the public feed is down, show these specific live seeds for now
        return [
            {"CLOCK": "44'", "FIXTURE": "Racing Club vs Estudiantes RC", "SCORE": "0-0", "LEAGUE": "Argentina"},
            {"CLOCK": "26'", "FIXTURE": "Colo-Colo vs Huachipato", "SCORE": "0-0", "LEAGUE": "Chile"},
            {"CLOCK": "89'", "FIXTURE": "Liverpool M. vs City Torque", "SCORE": "1-0", "LEAGUE": "Uruguay"}
        ]

# --- 5. ADMIN "FORCE REFRESH" ---
if IS_ADMIN:
    if st.sidebar.button("🔄 FORCE API REFRESH"):
        st.cache_data.clear() # This wipes the memory and forces a new fetch
        st.rerun()
