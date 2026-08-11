import streamlit as st
import pandas as pd
import os
import datetime
import random
import time
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
    /* 1. Hide the confusing default Streamlit sidebar toggle */
    [data-testid="collapsedControl"], button[kind="header"] { 
        display: none !important; 
    }

    /* 2. Container for the new custom menu */
    .custom-menu-container {
        position: fixed;
        top: 15px;
        left: 15px;
        z-index: 999999;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* 3. The main "Menu" button (DriveElite Clean Theme) */
    .custom-menu-btn {
        background-color: #FFFFFF; 
        color: #0F172A;
        border: 1px solid #CBD5E1;
        padding: 8px 16px;
        font-size: 15px;
        font-weight: 700;
        border-radius: 8px;
        cursor: pointer;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        align-items: center;
        gap: 8px;
        transition: all 0.2s ease;
    }
    
    .custom-menu-btn:hover {
        background-color: #F8FAFC; 
        border-color: #94A3B8;
        box-shadow: 0 4px 6px rgba(0,0,0,0.08);
    }

    /* 4. The Dropdown List */
    .custom-menu-dropdown {
        display: none; 
        position: absolute;
        top: 45px;
        left: 0;
        background-color: #FFFFFF; 
        min-width: 220px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        overflow: hidden;
        flex-direction: column;
    }

    .custom-menu-dropdown.show {
        display: flex;
        animation: popDown 0.2s ease-out;
    }

    @keyframes popDown {
        from { opacity: 0; transform: translateY(-5px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* 5. The Links inside the Dropdown */
    .custom-menu-dropdown a {
        color: #475569;
        padding: 14px 20px;
        text-decoration: none;
        font-size: 14px;
        font-weight: 600;
        border-bottom: 1px solid #F1F5F9;
        transition: all 0.2s;
    }

    .custom-menu-dropdown a:last-child {
        border-bottom: none;
    }

    .custom-menu-dropdown a:hover {
        background-color: #F8FAFC; 
        color: #2563EB;
        padding-left: 24px; 
    }
</style>

<!-- HTML STRUCTURE -->
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

<!-- JAVASCRIPT LOGIC -->
<script>
    function toggleCustomMenu() {
        document.getElementById("deCustomMenu").classList.toggle("show");
    }
    
    window.onclick = function(event) {
        if (!event.target.matches('.custom-menu-btn') && !event.target.closest('.custom-menu-btn')) {
            var dropdowns = document.getElementsByClassName("custom-menu-dropdown");
            for (var i = 0; i < dropdowns.length; i++) {
                if (dropdowns[i].classList.contains('show')) {
                    dropdowns[i].classList.remove('show');
                }
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
if 'verify_contact' not in st.session_state: st.session_state.verify_contact = ""

# ==========================================
# 3. OTP VERIFICATION SCREEN
# ==========================================
if st.session_state.otp_pending:
    st.title("🔒 Phone Number Verification")
    st.write("For security purposes, please verify your contact number to complete your registration.")
    
    st.success(f"📱 *MOCK SMS GATEWAY:* Sent OTP '{st.session_state.generated_otp}' to {st.session_state.verify_contact}")
    
    with st.form("otp_form"):
        user_otp = st.text_input("Enter the 6-Digit OTP sent to your phone", max_chars=6)
        
        c1, c2 = st.columns(2)
        # -> REMOVED use_container_width=True BELOW
        if c1.form_submit_button("VERIFY & COMPLETE REGISTRATION", type="primary"):
            if user_otp == st.session_state.generated_otp:
                try:
                    p = st.session_state.reg_payload
                    conn.execute("INSERT INTO users (username, password, role, full_name, age, contact_number, address, nationality, id_img, license_img, admin_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')", p)
                    conn.commit()
                    
                    st.success("🎉 Phone Verified! Registration Successful. Pending Admin approval.")
                    st.session_state.otp_pending = False
                    time.sleep(3)
                    st.rerun()
                except Exception as e:
                    st.error("⚠️ Username is already taken. Please go back and choose another.")
            else:
                st.error("❌ Incorrect OTP. Please try again.")
                
        # -> REMOVED use_container_width=True BELOW
        if c2.form_submit_button("CANCEL & GO BACK"):
            st.session_state.otp_pending = False
            st.rerun()

# ==========================================
# 4. MAIN REGISTRATION SCREEN
# ==========================================
else:
    # Add a bit of spacing so the title doesn't hide under the new menu
    st.write("<br>", unsafe_allow_html=True)
    
    # --- ADD YOUR LOGO HERE ---
    try:
        st.image("logo.png", width=250) 
    except:
        pass
        
    st.title("🚗 Welcome to DriveElite")
    st.write("Join the premier peer-to-peer car rental network. Select your account type below to begin.")

    reg_type = st.radio("I want to register as a:", ["Select...", "Affiliate", "Renter"], horizontal=True)
    st.divider()

    # --- AFFILIATE FLOW ---
    if reg_type == "Affiliate":
        
        # Policies moved to an expander for Mobile UX
        st.info("⚠️ Please read and agree to the policies below to register.")
        with st.expander("📖 Affiliate Policies (Required)", expanded=True):
            st.markdown("""
            * **Vehicle Condition:** Cars must be registered, insured, safe, and clean.
            * **Platform Fee:** DriveElite retains an 18% fee. You receive 82%.
            * **Payouts:** Processed once journey is "COMPLETED".
            * **Handover:** You must verify Renter ID and complete the digital checklist.
            * **GPS:** For your security, GPS must be installed minus audio.
            * **Visibility:** Cars listed as "LIVE" must be ready to book.
            """)

        st.subheader("💼 Affiliate Partner Registration")
        with st.form("affiliate_reg_form"):
            st.write("*Personal Information*")
            c1, c2, c3 = st.columns(3)
            first_name = c1.text_input("First Name").title()
            middle_name = c2.text_input("Middle Name").title()
            surname = c3.text_input("Surname").title()
            
            c4, c5, c6 = st.columns([2, 1, 2])
            dob = c4.date_input("Date of Birth", min_value=datetime.date(1930, 1, 1), max_value=datetime.date(2008, 1, 1), value=datetime.date(2000, 1, 1))
            age = c5.number_input("Age", min_value=18, max_value=99, step=1)
            contact = c6.text_input("Contact Number (e.g. 0917...)")
            
            c_addr, c_nat = st.columns([3, 1])
            address = c_addr.text_area("Full Address")
            nationality = c_nat.text_input("Nationality", value="Filipino")
            
            st.write("*Account Details*")
            username = st.text_input("Choose a Username").lower()
            c7, c8 = st.columns(2)
            password = c7.text_input("Create a Password", type="password")
            confirm_password = c8.text_input("Confirm Password", type="password")
            
            st.write("*Identity Verification (2 IDs Required)*")
            c9, c10 = st.columns(2)
            gov_id = c9.file_uploader("Upload Passport / Govt ID", type=['jpg', 'png'])
            lic_id = c10.file_uploader("Upload Driver's License", type=['jpg', 'png'])
            
            st.divider()
            agreed = st.checkbox("✅ I have read, understood, and agree to the Affiliate Policies & 15% Platform Fee rules shown above.")
            
            if st.form_submit_button("Submit Partner Registration", type="primary"):
                full_name = f"{first_name} {middle_name} {surname}".replace("  ", " ").strip()
                
                if not agreed: st.error("🚨 Registration Blocked: You must check the agreement box.")
                elif password != confirm_password: st.error("🚨 Passwords do not match. Please try again.")
                elif first_name and surname and username and password and gov_id and lic_id and contact and nationality:
                    if not pd.read_sql_query("SELECT username FROM users WHERE username=?", conn, params=(username,)).empty:
                        st.error("⚠️ Username taken. Please choose another.")
                    else:
                        st.session_state.reg_payload = (username, password, 'AFFILIATE', full_name, age, contact, address, nationality.title(), save_file(gov_id), save_file(lic_id))
                        st.session_state.verify_contact = contact
                        st.session_state.generated_otp = str(random.randint(100000, 999999))
                        st.session_state.otp_pending = True
                        st.rerun()
                else: st.error("⚠️ Please fill out all required fields and upload BOTH IDs.")

    # --- RENTER FLOW ---
    elif reg_type == "Renter":
        
        # Policies moved to an expander for Mobile UX
        st.info("⚠️ Please read and agree to the policies below to register.")
        with st.expander("📝 Renter Policies (Required)", expanded=True):
            st.markdown("""
            * **Fuel Policy:** Return with same fuel level. Missing fuel incurs a refill cost + ₱500 fee.
            * **Cleanliness:** Return clean. Excessive dirt incurs up to ₱600 fee.
            * **Damage:** You are fully responsible for damages incurred during booking.
            * **Late Returns:** 30-min grace period. Then strict ₱300/hour late fee.
            * **RFID:** Load Approximated RFID Amount for your convenience. If not Loaded +₱200 Load fee.
            * **Speed Limit:** Observe speed limit at all times to avoid penalties.
            * **Permitted Use:** Personal transport only. No racing/towing and interisland travel is strictly prohibited.
            """)

        st.subheader("🚙 Renter Registration")
        with st.form("renter_reg_form"):
            st.write("*Personal Information*")
            c1, c2, c3 = st.columns(3)
            first_name = c1.text_input("First Name").title()
            middle_name = c2.text_input("Middle Name").title()
            surname = c3.text_input("Surname").title()
            
            c4, c5, c6 = st.columns([2, 1, 2])
            dob = c4.date_input("Date of Birth", min_value=datetime.date(1930, 1, 1), max_value=datetime.date(2008, 1, 1), value=datetime.date(2000, 1, 1))
            age = c5.number_input("Age", min_value=18, max_value=99, step=1)
            contact = c6.text_input("Contact Number (e.g. 0917...)")
            
            c_addr, c_nat = st.columns([3, 1])
            address = c_addr.text_area("Full Address")
            nationality = c_nat.text_input("Nationality", value="Filipino")
            
            st.write("*Account Details*")
            username = st.text_input("Choose a Username").lower()
            c7, c8 = st.columns(2)
            password = c7.text_input("Create a Password", type="password")
            confirm_password = c8.text_input("Confirm Password", type="password")
            
            st.write("*Identity Verification (2 IDs Required)*")
            c9, c10 = st.columns(2)
            gov_id = c9.file_uploader("Upload Passport / Govt ID", type=['jpg', 'png'])
            lic_id = c10.file_uploader("Upload Driver's License", type=['jpg', 'png'])
            
            st.divider()
            agreed = st.checkbox("✅ I have read, understood, and agree to the DriveElite Renter Policies shown above.")
            
            if st.form_submit_button("Submit Registration", type="primary"):
                full_name = f"{first_name} {middle_name} {surname}".replace("  ", " ").strip()
                
                if not agreed: st.error("🚨 Registration Blocked: You must check the agreement box.")
                elif password != confirm_password: st.error("🚨 Passwords do not match. Please try again.")
                elif first_name and surname and username and password and gov_id and lic_id and contact and nationality:
                    if not pd.read_sql_query("SELECT username FROM users WHERE username=?", conn, params=(username,)).empty:
                        st.error("⚠️ Username taken. Please choose another.")
                    else:
                        st.session_state.reg_payload = (username, password, 'RENTER', full_name, age, contact, address, nationality.title(), save_file(gov_id), save_file(lic_id))
                        st.session_state.verify_contact = contact
                        st.session_state.generated_otp = str(random.randint(100000, 999999))
                        st.session_state.otp_pending = True
                        st.rerun()
                else: st.error("⚠️ Please fill out all required fields and upload BOTH IDs.")
