import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse

# --- 1. CONFIG ---
st.set_page_config(page_title="Tonoos Stream XVI", page_icon="🤝", layout="centered")
TAB_NAME = "Audit_Log" 
PAYOUT_GOAL = 4400.0

# --- 2. LOGIN ---
if "authenticated" not in st.session_state:
    st.title("🤝 Tonoos Stream XVI")
    access_code = st.text_input("Enter Access Code", type="password")
    if st.button("Access Ledger"):
        if access_code == st.secrets["credentials"]["GROUP_ACCESS_CODE"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid Code.")
    st.stop()

# --- 3. CONNECTION & DATA ---
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet=TAB_NAME, ttl=0)

# --- 4. THE OFFICIAL 11-CYCLE SCHEDULE ---
# This dictionary now perfectly matches your calendar screenshot
recipients = {
    "Cycle 1": "Oke 2", 
    "Cycle 2": "Rotimi", 
    "Cycle 3": "Mr Ayo",
    "Cycle 4": "Alhaji Taiwo & Cleopatra", 
    "Cycle 5": "Sonia", 
    "Cycle 6": "Adenike",
    "Cycle 7": "Akinkunle", 
    "Cycle 8": "Mr Adeniji", 
    "Cycle 9": "Oke 1",
    "Cycle 10": "Perfect & Mmandu", 
    "Cycle 11": "Jibola"
}

# --- 5. NAVIGATION ---
st.sidebar.header("Navigation")
active_cycle = st.sidebar.selectbox("Select Active Cycle", list(recipients.keys()))
current_recipient = recipients[active_cycle]
is_admin = st.sidebar.checkbox("Admin Mode")

# --- 6. PROGRESS ---
total_collected = pd.to_numeric(df[active_cycle], errors='coerce').fillna(0).sum()
st.title("🤝 Tonoos Stream XVI")
st.subheader(f"Cycle Payout: ${PAYOUT_GOAL:,.2f} for {current_recipient}")
st.metric("Total Collected", f"${total_collected:,.2f}", f"{int((total_collected/PAYOUT_GOAL)*100)}%")
st.progress(min(total_collected / PAYOUT_GOAL, 1.0))

# --- 7. MAIN LIST (Corrected to filter out Petagaye) ---
st.write("---")
st.write(f"### {active_cycle} Status")

# We only loop through the members that should exist in the 11-cycle run
for index, row in df.iterrows():
    member = str(row['Member Name']).strip()
    partner = str(row['Partner']).strip() if pd.notna(row['Partner']) else ""
    
    # SKIP Petagaye to align with your corrected schedule
    if member == "Petagaye":
        continue
        
    # Formatting display names based on your schedule screenshot
    if member == "Alhaji Taiwo": display_name = "Alhaji Taiwo & Cleopatra"
    elif member == "Perfect": display_name = "Perfect & Mmandu"
    elif partner and partner.lower() != "nan" and partner != "":
        display_name = f"{member} & {partner}"
    else:
        display_name = member

    try:
        paid = float(row[active_cycle]) if pd.notna(row[active_cycle]) else 0.0
    except:
        paid = 0.0

    col1, col2 = st.columns([3, 2])
    with col1:
        status_emoji = "✅" if paid >= 400 else "⏳"
        st.write(f"{status_emoji} **{display_name}**: ${paid:,.0f}")

    if is_admin and paid < 400:
        with col2:
            c1, c2 = st.columns(2)
            if c1.button(f"+$200", key=f"p200_{index}"):
                df.at[index, active_cycle] = paid + 200
                conn.update(worksheet=TAB_NAME, data=df)
                st.rerun()
            if c2.button(f"+$400", key=f"p400_{index}"):
                df.at[index, active_cycle] = 400
                conn.update(worksheet=TAB_NAME, data=df)
                st.rerun()

# --- 8. SIDEBAR SCHEDULE ---
st.sidebar.write("---")
st.sidebar.write("📅 **Full Payout Schedule**")
for cycle, name in recipients.items():
    st.sidebar.text(f"{cycle}: {name}")
