import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import urllib.parse

# --- 1. INITIALIZE CONNECTION ---
# Ensure your Streamlit Secrets has the [connections.gsheets] block
conn = st.connection("gsheets", type=GSheetsConnection)

def get_whatsapp_link(member, amount, cycle, total, goal):
    percent = int((total / goal) * 100)
    text = (
        f"✅ *TCSI Stream XVI Update*\n\n"
        f"Member: {member}\n"
        f"Confirmed: ${amount}\n"
        f"Current {cycle} Pot: ${total:,.2f} / ${goal:,.2f} ({percent}%)\n\n"
        f"View Ledger: {st.secrets['credentials']['APP_URL']}"
    )
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- 2. THE INTERFACE ---
st.title("🤝 TCSI Stream XVI Ledger")

# Load Data (Fresh copy every time)
df = conn.read(ttl=0)

# Sidebar Config
st.sidebar.header("Navigation")
active_cycle = st.sidebar.selectbox("Select Active Cycle", [f"Cycle {i}" for i in range(1, 13)])
is_admin = st.sidebar.checkbox("Admin: Confirm Receipts")

# --- 3. TOP LEVEL METRICS ---
total_collected = df[active_cycle].sum()
st.metric(f"Total Collected: {active_cycle}", f"${total_collected:,.2f}")
st.progress(min(total_collected / 4400.0, 1.0))

# --- 4. MEMBER LIST ---
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
            if c1.button(f"+$200", key=f"2_{index}"):
                df.loc[index, active_cycle] = paid + 200
                conn.update(worksheet="Sheet1", data=df)
                st.success(f"Added $200 to {member}")
                st.markdown(f"[📲 Send WhatsApp Update]({get_whatsapp_link(member, 200, active_cycle, total_collected + 200, 4400.0)})")
            
            if c2.button(f"+$400", key=f"4_{index}"):
                df.loc[index, active_cycle] = 400
                conn.update(worksheet="Sheet1", data=df)
                st.success(f"Hand Completed for {member}")
                st.markdown(f"[📲 Send WhatsApp Update]({get_whatsapp_link(member, 400, active_cycle, total_collected + (400-paid), 4400.0)})")
