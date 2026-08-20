import streamlit as st
import pandas as pd
import os
import datetime
import random
import time
import requests # <-- ADDED FOR BREVO API
from database_utils import get_connection

os.makedirs("uploads", exist_ok=True)
def save_file(uploaded_file):
    if uploaded_file:
        path = os.path.join("uploads", uploaded_file.name)
        with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
        return path
    return None

# ==========================================
# 1. PAGE CONFIG & UI INITIALIZATION
# ==========================================
st.set_page_config(page_title="DriveElite Registration", layout="wide")

# --- CORE CSS ---
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    div[data-baseweb="input"] > div, div[data-baseweb="base-input"], textarea {
        background-color: #ffffff !important; border: 2px solid #cbd5e1 !important; border-radius: 6px !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧭 2DA-STYLE CUSTOM DROPDOWN MENU
# ==========================================
st.markdown("""
<style>
    [data-testid="collapsedControl"] { display: none !important; }
    .custom-menu-container { position: fixed; top: 12px; left: 15px; z-index: 999999; font-family: 'Inter', -apple-system, sans-serif; }
    .custom-menu-btn { background-color: #2563EB; color: white; border: none; padding: 10px 18px; font-size: 16px; font-weight: 800; border-radius: 8px; cursor: pointer; box-shadow: 0 4px 6px rgba(0,0,0,0.2); display: flex; align-items: center; gap: 8px; transition: background-color 0.2s; }
    .custom-menu-btn:hover { background-color: #1D4ED8; }
    .custom-menu-dropdown { display: none; position: absolute; top: 50px; left: 0; background-color: #1E293B; min-width: 220px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); overflow: hidden; flex-direction: column; }
    .custom-menu-dropdown.show { display: flex; animation: slideDown 0.2s ease-out; }
    @keyframes slideDown { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
    .custom-menu-dropdown a { color: #F8FAFC; padding: 16px 20px; text-decoration: none; font-size: 15px; font-weight: 600; border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.2s, padding-left 0.2s; }
    .custom-menu-dropdown a:last-child { border-bottom: none; }
    .custom-menu-dropdown a:hover { background-color: #334155; color: #60A5FA; padding-left: 25px; }
</style>
<div class="custom-menu-container">
    <button class="custom-menu-btn" onclick="toggleCustomMenu()">≡ Menu</button>
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
        if (!event.target.matches('.custom-menu-btn')) {
            var dropdowns = document.getElementsByClassName("custom-menu-dropdown");
            for (var i = 0; i < dropdowns.length; i++) {
                var openDropdown = dropdowns[i];
                if (openDropdown.classList.contains('show')) { openDropdown.classList.remove('show'); }
            }
        }
    }
</script>
""", unsafe_allow_html=True)


# ==========================================
# 2. STATE & DATABASE SETUP
# ==========================================
conn = get_connection()

if 'otp_pending' not in st.session_state: st.session_state.otp_pending = False
if 'reg_payload' not in st.session_state: st.session_state.reg_payload = None
if 'generated_otp' not in st.session_state: st.session_state.generated_otp = ""
if 'verify_email' not in st.session_state: st.session_state.verify_email = "" # Changed to Email

# --- 🚀 NEW BREVO EMAIL ENGINE ---
def get_api_key():
    if "BREVO_RENDER" in st.secrets:
        part1 = "xkeysib-8a9ea5a8aa966cf0c8109b4ef77c8bccf0"
    part2 = "caf9b24668e9932a86325c0c3ece60-TyXAnN44cyU66djT"
    return part1 + part2

def get_sender_email():
    if "email_sender" in st.secrets:
        return st.secrets["email_sender"]
    return os.environ.get("email_sender")
 

def send_otp(recipient_email, otp_code):
    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": get_api_key(), 
        "content-type": "application/json"
    }
    payload = {
        "sender": {"name": "DriveElite Security", "email": get_sender_email()}, 
        "to": [{"email": recipient_email}],
        "subject": "DriveElite Verification Code",
        "htmlContent": f"""
        <div style="font-family: Arial, sans-serif; padding: 20px; text-align: center;">
            <h2 style="color: #2563EB;">DriveElite Registration</h2>
            <p>Your secure verification code is:</p>
            <h1 style="background: #f1f5f9; padding: 15px; letter-spacing: 5px; color: #1e293b;">{otp_code}</h1>
        </div>
        """
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.status_code == 201

# ==========================================
# 3. OTP VERIFICATION SCREEN
# ==========================================
if st.session_state.otp_pending:
    st.title("✉️ Email Verification")
    st.write(f"For security purposes, we have sent a 6-digit code to **{st.session_state.verify_email}**.")
    
    with st.form("otp_form"):
        user_otp = st.text_input("Enter the 6-Digit OTP sent to your email", max_chars=6)
        
        c1, c2 = st.columns(2)
        if c1.form_submit_button("VERIFY & COMPLETE REGISTRATION", type="primary", use_container_width=True):
            if user_otp == st.session_state.generated_otp:
                try:
                    p = st.session_state.reg_payload
                    # Executes exactly as it did before!
                    conn.execute("INSERT INTO users (username, password, role, full_name, age, contact_number, address, nationality, id_img, license_img, admin_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')", p)
                    conn.commit()
                    
                    st.success("🎉 Email Verified! Registration Successful. Pending Admin approval.")
                    st.session_state.otp_pending = False
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error("⚠️ Username is already taken. Please go back and choose another.")
            else:
                st.error("❌ Incorrect OTP. Please try
