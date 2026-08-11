import streamlit as st
import pandas as pd
from database_utils import get_connection
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="DriveElite Messenger", page_icon="logo.png", layout="wide")

# ==========================================
# 🧭 DRIVEELITE THEMED CUSTOM MENU
# ==========================================
st.markdown("""
<style>
    /* Hide the confusing default Streamlit sidebar toggle (>> or >) */
    [data-testid="collapsedControl"], button[kind="header"] { 
        display: none !important; 
    }

    /* Container for the new custom menu */
    .custom-menu-container {
        position: fixed; top: 15px; left: 15px; z-index: 999999;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Main "Menu" button (DriveElite Clean Theme) */
    .custom-menu-btn {
        background-color: #FFFFFF; color: #0F172A;
        border: 1px solid #CBD5E1; padding: 8px 16px;
        font-size: 15px; font-weight: 700; border-radius: 8px;
        cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; align-items: center; gap: 8px; transition: all 0.2s ease;
    }
    .custom-menu-btn:hover {
        background-color: #F8FAFC; border-color: #94A3B8; box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }

    /* Dropdown List */
    .custom-menu-dropdown {
        display: none; position: absolute; top: 45px; left: 0;
        background-color: #FFFFFF; min-width: 220px; border-radius: 12px;
        border: 1px solid #E2E8F0; box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        overflow: hidden; flex-direction: column;
    }
    .custom-menu-dropdown.show { display: flex; animation: popDown 0.2s ease-out; }
    @keyframes popDown { from { opacity: 0; transform: translateY(-5px); } to { opacity: 1; transform: translateY(0); } }

    /* Links inside the Dropdown */
    .custom-menu-dropdown a {
        color: #475569; padding: 14px 20px; text-decoration: none;
        font-size: 14px; font-weight: 600; border-bottom: 1px solid #F1F5F9; transition: all 0.2s;
    }
    .custom-menu-dropdown a:last-child { border-bottom: none; }
    .custom-menu-dropdown a:hover { background-color: #F8FAFC; color: #2563EB; padding-left: 24px; }
</style>

<div class="custom-menu-container">
    <button class="custom-menu-btn" onclick="toggleCustomMenu()">
        <span style="font-size: 18px;">≡</span> Menu
    </button>
    <div class="custom-menu-dropdown" id="deCustomMenu">
        <a href="?portal=JOIN" target="_self">🔑 Join / Login</a>
        <a href="?portal=RENTER" target="_self">🚙 Renter Portal</a>
        <a href="?portal=AFFILIATE" target="_self">💼 Host Dashboard</a>
        <a href="?portal=ADMIN" target="_self">⚙️ Admin Command</a>
    </div>
</div>

<script>
    function toggleCustomMenu() { document.getElementById("deCustomMenu").classList.toggle("show"); }
    window.onclick = function(event) {
        if (!event.target.matches('.custom-menu-btn') && !event.target.closest('.custom-menu-btn')) {
            var dropdowns = document.getElementsByClassName("custom-menu-dropdown");
            for (var i = 0; i < dropdowns.length; i++) {
                if (dropdowns[i].classList.contains('show')) { dropdowns[i].classList.remove('show'); }
            }
        }
    }
</script>
""", unsafe_allow_html=True)


if not st.session_state.get('logged_in'):
    st.warning("Please login to access the Messenger.")
    st.stop()

# --- LIVE CHAT ENGINE ---
# Refreshes the page every 5 seconds (5000ms) to check for new messages
st_autorefresh(interval=5000, key="messenger_refresh")

conn = get_connection()
current_user = st.session_state.username
role = st.session_state.get('role', 'USER')

st.title("💬 DRIVEELITE MESSENGER")
st.write(f"Logged in securely as: *{current_user.upper()}* ({role})")

# --- Get list of users from the Database ---
users_df = pd.read_sql_query("SELECT username, role, full_name FROM users WHERE username != ?", conn, params=(current_user,))

contacts = []

# --- Manually insert the Admin into the list! ---
if current_user != "masterom":
    contacts.append("masterom (System Admin) - ADMIN")
    
for _, r in users_df.iterrows():
    name = r['full_name'] if r['full_name'] else r['username']
    contacts.append(f"{r['username']} ({name}) - {r['role']}")

if not contacts:
    st.info("No other users found on the platform yet.")
    st.stop()

# Dropdown to select who to message
selected_contact_str = st.selectbox("Select someone to message:", contacts)

# Extract just the username
receiver_username = selected_contact_str.split(" ")[0]

st.markdown(f"### Chat History with @{receiver_username}")

# --- Fetch Chat History ---
chat_query = """
    SELECT sender, message, ts 
    FROM support_chats 
    WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) 
    ORDER BY ts ASC
"""
chats = pd.read_sql_query(chat_query, conn, params=(current_user, receiver_username, receiver_username, current_user))

# --- BEAUTIFUL FB MESSENGER UI ---
chat_container = st.container(height=450)
with chat_container:
    if chats.empty:
        st.info("Say hello to start the conversation!")
    else:
        for _, c in chats.iterrows():
            if c['sender'] == current_user:
                # FB Style: Your Messages (Blue, Right-aligned)
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                    <div style="background-color: #0084FF; color: white; padding: 10px 15px; border-radius: 20px 20px 5px 20px; max-width: 75%; font-family: Arial, sans-serif; box-shadow: 0px 2px 5px rgba(0,0,0,0.1);">
                        {c['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # FB Style: Their Messages (Grey, Left-aligned)
                st.markdown(f"""
                <div style="display: flex; justify-content: flex-start; margin-bottom: 10px;">
                    <div style="background-color: #E4E6EB; color: black; padding: 10px 15px; border-radius: 20px 20px 20px 5px; max-width: 75%; font-family: Arial, sans-serif; box-shadow: 0px 2px 5px rgba(0,0,0,0.1);">
                        <small style="color: #65676B;">@{c['sender']}</small><br>
                        {c['message']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

# --- Send a new message ---
with st.form("send_msg", clear_on_submit=True):
    msg = st.text_input("Type your message here...", placeholder="Type here and press Enter to send...")
    if st.form_submit_button("Send Message", type="primary"):
        if msg.strip():
            conn.execute("INSERT INTO support_chats (sender, receiver, message) VALUES (?, ?, ?)", (current_user, receiver_username, msg))
            conn.commit()
            st.rerun()
