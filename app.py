import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
from datetime import datetime
import pytz

# --- 1. CONFIG & SETTINGS ---
st.set_page_config(page_title="Tonoos Stream XVI", page_icon="🤝", layout="centered")
EST = pytz.timezone('US/Eastern')

# UPDATED: Matches your Google Sheet tab name exactly
TAB_NAME = "Audit_Log" 
PAYOUT_GOAL = 4400.0

# --- 2. EASY ACCESS LOGIN (1234) ---
if "authenticated" not in st.session_state:
    st.title("🤝 Tonoos Stream XVI")
    st.subheader("Member Access")
    access_code = st.text_input("Enter Access Code", type="password")
    if st.button("Access Ledger"):
        if access_code == st.secrets["credentials"]["GROUP_ACCESS_CODE"]:
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Invalid Code. Please try again.")
    st.stop()

# --- 3. INITIALIZE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 4. HELPER FUNCTIONS ---
def get_whatsapp_link(member, amount, cycle, total, goal, recipient):
    percent = int((total / goal) * 100)
    text = (
        f"✅ *Tonoos Stream XVI Update*\n\n"
        f"*Cycle:* {cycle}\n"
        f"*Recipient:* {recipient}\n"
        f"--------------------------\n"
        f"*Member:* {member}\n"
        f"*Confirmed:* ${amount}\n"
        f"*Current Pot:* ${total:,.2f} / ${goal:,.2f} ({percent}%)\n\n"
        f"🔗 View Ledger: {st.secrets['credentials']['APP_URL']}"
    )
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- 5. DATA LOADING ---
# Load from Audit_Log tab with no caching (ttl=0)
df = conn.read(worksheet=TAB_NAME, ttl=0)

# --- 6. HEADER & NAVIGATION ---
st.title("🤝 Tonoos Stream XVI")

# 11-Cycle Recipient Mapping
recipients = {
    "Cycle 1": "Oke 2", "Cycle 2": "Rotimi", "Cycle 3": "Mr Ayo",
    "Cycle 4": "Alhaji Taiwo/Cleopatra", "Cycle 5": "Sonia", "Cycle 6": "Adenike",
    "Cycle 7": "Akinkunle", "Cycle 8": "Mr Adeniji", "Cycle 9": "Oke 1",
    "Cycle 10": "Petagaye/Mmandu", "Cycle 11": "Perfect/Tosin"
}

st.sidebar.header("Navigation")
active_cycle = st.sidebar.selectbox("Select Active Cycle", list(recipients.keys()))
current_recipient = recipients[active_cycle]
is_admin = st.sidebar.checkbox("Admin Mode")

# --- 7. PROGRESS SECTION ---
total_collected = pd.to_numeric(df[active_cycle], errors='coerce').fillna(0).sum()
st.subheader(f"Cycle Payout: ${PAYOUT_GOAL:,.2f} for {current_recipient}")
st.metric("Total Collected", f"${total_collected:,.2f}", f"{int((total_collected/PAYOUT_GOAL)*100)}%")
st.progress(min(total_collected / PAYOUT_GOAL, 1.0))

# --- 8. MEMBER LIST & ADMIN CONTROLS ---
st.write("---")
for index, row in df.iterrows():
    member = row['Member Name']
    paid = pd.to_numeric(row[active_cycle], errors='coerce') if pd.notnull(row[active_cycle]) else 0
    partner = row['Partner']
    
    display_name = f"{member} & {partner}" if pd.notna(partner) and str(partner).strip() != "" else member
    
    col1, col2 = st.columns([3, 2])
    with col1:
        status_emoji = "✅" if paid >= 400 else "⏳"
        st.write(f"{status_emoji} **{display_name}**: ${paid:,.0f}")

    if is_admin and paid < 400:
        with col2:
            c1, c2 = st.columns(2)
            if c1.button(f"+$200", key=f"btn2_{index}"):
                df.loc[index, active_cycle] = paid + 200
                conn.update(worksheet=TAB_NAME, data=df)
                st.success(f"Added $200")
                st.markdown(f"[📲 WhatsApp]({get_whatsapp_link(member, 200, active_cycle, total_collected + 200, PAYOUT_GOAL, current_recipient)})")
            
            if c2.button(f"+$400", key=f"btn4_{index}"):
                df.loc[index, active_cycle] = 400
                conn.update(worksheet=TAB_NAME, data=df)
                st.success(f"Added $400")
                st.markdown(f"[📲 WhatsApp]({get_whatsapp_link(member, 400, active_cycle, total_collected + (400-paid), PAYOUT_GOAL, current_recipient)})")

# Sidebar Info
st.sidebar.info("Deadline: Fridays 7PM EST\n\nGrace Period: Sundays 7PM EST")
