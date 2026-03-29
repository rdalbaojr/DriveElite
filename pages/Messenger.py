import streamlit as st
import pandas as pd
from database_utils import get_connection

# --- UNIVERSAL THEME & PAGE CONFIG ---
st.set_page_config(page_title="DriveElite Messenger", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    [data-testid='stSidebarNav'] span { text-transform: uppercase !important; font-weight: bold !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="base-input"], div[data-baseweb="select"] > div, textarea {
        background-color: #ffffff !important; border: 2px solid #cbd5e1 !important; border-radius: 6px !important; color: #0f172a !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="base-input"]:focus-within, div[data-baseweb="select"] > div:focus-within, textarea:focus {
        border-color: #2563eb !important; box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important;
    }
</style>
""", unsafe_allow_html=True)

# THE CRITICAL DATABASE CONNECTION
conn = get_connection()

if not st.session_state.get('logged_in'):
    st.warning("Please log in through your respective portal first to access the Messenger.")
    st.stop()

current_user = st.session_state.username
role = st.session_state.role

st.title("DRIVEELITE MESSENGER")
st.write(f"Logged in securely as: *{current_user.upper()}* ({role})")
st.divider()

# --- FETCH USERS DIRECTORY ---
try:
    # Allow users to message anyone except themselves
    users_df = pd.read_sql_query("SELECT username, role, full_name FROM users WHERE username != ? AND admin_status = 'APPROVED'", conn, params=(current_user,))
    
    if users_df.empty:
        st.info("No other approved users are available to chat with yet.")
    else:
        # Create a clean dropdown list
        user_list = [f"{row['full_name']} (@{row['username']}) - {row['role']}" for _, row in users_df.iterrows()]
        selected_user_str = st.selectbox("Select someone to message:", user_list)
        
        # Extract the exact username from the dropdown string
        receiver_username = selected_user_str.split("(@")[1].split(")")[0]

        st.divider()
        st.subheader(f"Chat History with @{receiver_username}")

        # --- DISPLAY CHAT HISTORY ---
        chat_query = """
        SELECT sender, message, ts FROM support_chats 
        WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?) 
        ORDER BY ts ASC
        """
        chats = pd.read_sql_query(chat_query, conn, params=(current_user, receiver_username, receiver_username, current_user))

        # Create a scrolling container for messages
        chat_container = st.container(height=400)
        with chat_container:
            if chats.empty:
                st.write("No messages yet. Say hello!")
            else:
                for _, chat in chats.iterrows():
                    # If I sent the message
                    if chat['sender'] == current_user:
                        with st.chat_message("user"):
                            st.write(f"*You:* {chat['message']}")
                    # If they sent the message
                    else:
                        with st.chat_message("assistant"):
                            st.write(f"*@{chat['sender']}:* {chat['message']}")

        # --- SEND NEW MESSAGE ---
        new_msg = st.chat_input("Type your message here...")
        if new_msg:
            conn.execute("INSERT INTO support_chats (sender, receiver, message) VALUES (?, ?, ?)", (current_user, receiver_username, new_msg))
            conn.commit()
            st.rerun()

# THIS IS THE BLOCK THAT WAS MISSING!
except Exception as e:
    st.error(f"Database error: {e}")
