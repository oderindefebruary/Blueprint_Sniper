import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
import pytz

# --- 1. SETUP ---
st.set_page_config(page_title="Tonoos Stream XVI", page_icon="🤝")
EST = pytz.timezone('US/Eastern')
conn = st.connection("gsheets", type=GSheetsConnection)

def get_whatsapp_link(member, amount, cycle, total, goal):
    percent = int((total / goal) * 100)
    text = (
        f"✅ *Tonoos Stream XVI Update*\n\n"
        f"Member: {member}\n"
        f"Confirmed: ${amount}\n"
        f"Current {cycle} Pot: ${total:,.2f} / ${goal:,.2f} ({percent}%)\n\n"
        f"View Ledger: {st.secrets['credentials']['APP_URL']}"
    )
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- 2. HEADER ---
st.title("🤝 Tonoos Stream XVI")

# --- 3. LOAD DATA ---
df = conn.read(ttl=0)

# Sidebar Config
st.sidebar.header("Navigation")
# Updated to 11 Cycles
active_cycle = st.sidebar.selectbox("Select Active Cycle", [f"Cycle {i}" for i in range(1, 12)])
is_admin = st.sidebar.checkbox("Admin: Confirm Receipts")

# --- 4. TOP LEVEL METRICS ---
total_collected = df[active_cycle].sum()
st.metric(f"Total Collected: {active_cycle}", f"${total_collected:,.2f}")
st.progress(min(total_collected / 4400.0, 1.0))

# --- 5. MEMBER LIST ---
st.write("---")
for index, row in df.iterrows():
    member = row['Member Name']
    paid = row[active_cycle]
    partner = row['Partner']
    
    label = f"{member} & {partner}" if pd.notna(partner) and partner != "" else member
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        status_emoji = "✅" if paid >= 400 else "⏳"
        st.write(f"{status_emoji} **{label}**: ${paid}")

    # --- ADMIN BUTTONS ---
    if is_admin and paid < 400:
        with col2:
            c1, c2 = st.columns(2)
            if c1.button(f"+$200", key=f"btn2_{index}"):
                df.loc[index, active_cycle] = paid + 200
                conn.update(worksheet="Sheet1", data=df)
                st.success(f"Added $200 for {member}")
                st.markdown(f"[📲 WhatsApp Update]({get_whatsapp_link(member, 200, active_cycle, total_collected + 200, 4400.0)})")
            
            if c2.button(f"+$400", key=f"btn4_{index}"):
                df.loc[index, active_cycle] = 400
                conn.update(worksheet="Sheet1", data=df)
                st.success(f"Full Hand for {member}")
                st.markdown(f"[📲 WhatsApp Update]({get_whatsapp_link(member, 400, active_cycle, total_collected + (400-paid), 4400.0)})")
