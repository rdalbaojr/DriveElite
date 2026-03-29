import streamlit as st
import pandas as pd
import datetime
import time
import os
from database_utils import get_connection
from streamlit_drawable_canvas import st_canvas

os.makedirs("uploads", exist_ok=True)
def save_file(uploaded_file):
    if uploaded_file:
        path = os.path.join("uploads", uploaded_file.name)
        with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
        return path
    return None

st.set_page_config(page_title="DriveElite Affiliate", layout="wide")
st.markdown("""<style>.stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }</style>""", unsafe_allow_html=True)

conn = get_connection()
try:
    cat_df = pd.read_sql_query("SELECT name, default_price FROM vehicle_categories", conn)
    FIXED_RATES = dict(zip(cat_df['name'], cat_df['default_price']))
except: FIXED_RATES = {"Sedan": 1500.0} 

if not st.session_state.get('logged_in') or st.session_state.get('role') != 'AFFILIATE':
    st.markdown("<h2 style='text-align: center;'>💼 AFFILIATE LOGIN</h2>", unsafe_allow_html=True)
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN", use_container_width=True):
            user = pd.read_sql_query("SELECT * FROM users WHERE username=? AND password=? AND role='AFFILIATE'", conn, params=(u, p))
            if not user.empty:
                if user.iloc[0]['admin_status'] == 'PENDING': st.warning("Account pending Admin approval.")
                elif user.iloc[0]['admin_status'] == 'REJECTED': st.error("Account application rejected.")
                else:
                    st.session_state.logged_in, st.session_state.username, st.session_state.role = True, u, 'AFFILIATE'
                    st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

with st.sidebar:
    st.markdown("<h3 style='text-align: center;'>💼 Affiliate Rules</h3>", unsafe_allow_html=True)
    st.markdown("* *Safety:* Cars must be safe.\n* *Fee:* 15% Platform Fee.\n* *Checklist:* Mandatory Handover/Return signoffs.\n* *Visibility:* Manage in My Assets.")

username = st.session_state.username
st.markdown("<h1 style='text-align: center;'>💼 COMMAND CENTER</h1>", unsafe_allow_html=True)

tabs = st.tabs(["BOOKINGS & HANDOVER", "MY ASSETS", "ADD ASSET", "ADD DRIVER"])

with tabs[0]:
    st.markdown("<h3 style='text-align: center;'>🟡 PENDING DISPATCH</h3>", unsafe_allow_html=True)
    pending = pd.read_sql_query("SELECT b.id, b.renter_username, v.make, v.plate FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE v.owner_username = ? AND b.status = 'CONFIRMED'", conn, params=(username,))
    if pending.empty: st.info("No vehicles pending dispatch.")
    for _, t in pending.iterrows():
        with st.expander(f"START TRIP: {t['make']} ({t['plate']}) - Renter: {t['renter_username']}"):
            st.markdown(f"*HANDOVER CONTRACT (Ref: DRV-{t['id']:05d})*")
            st.write("*PRE-HANDOVER CHECKLIST*")
            chk_col1, chk_col2 = st.columns(2)
            with chk_col1:
                chk_tank = st.checkbox("[ ] Full Tank", key=f"htank_{t['id']}")
                chk_ac = st.checkbox("[ ] Aircon properly functioning", key=f"hac_{t['id']}")
                chk_wiper = st.checkbox("[ ] Wipers properly functioning", key=f"hwiper_{t['id']}")
            with chk_col2:
                chk_exterior = st.checkbox("[ ] Car checked all around", key=f"hext_{t['id']}")
                chk_seats = st.checkbox("[ ] Seats / Interior checked", key=f"hse_{t['id']}")
                chk_deposit = st.checkbox("[ ] Php 5,000.00 Deposit Confirmed", key=f"hdep_{t['id']}")
            
            st.divider()
            c1, c2 = st.columns(2)
            
            # --- PERFECTLY CENTERED RENTER SIGNATURE ---
            with c1:
                st.markdown("<div style='text-align: center;'><b>Renter Signature</b></div>", unsafe_allow_html=True)
                if f"clr_sr_{t['id']}" not in st.session_state: st.session_state[f"clr_sr_{t['id']}"] = 0
                
                # These columns push the canvas to the exact center
                _, mid1, _ = st.columns([1, 4, 1])
                with mid1:
                    s_r = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=150, width=250, display_toolbar=False, key=f"sr_{t['id']}_{st.session_state[f'clr_sr_{t['id']}']}")
                    if st.button("🧹 Clear / Erase", key=f"btn_sr_{t['id']}", use_container_width=True):
                        st.session_state[f"clr_sr_{t['id']}"] += 1
                        st.rerun()

            # --- PERFECTLY CENTERED AFFILIATE SIGNATURE ---
            with c2:
                st.markdown("<div style='text-align: center;'><b>Affiliate Signature</b></div>", unsafe_allow_html=True)
                if f"clr_sa_{t['id']}" not in st.session_state: st.session_state[f"clr_sa_{t['id']}"] = 0
                
                _, mid2, _ = st.columns([1, 4, 1])
                with mid2:
                    s_a = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=150, width=250, display_toolbar=False, key=f"sa_{t['id']}_{st.session_state[f'clr_sa_{t['id']}']}")
                    if st.button("🧹 Clear / Erase", key=f"btn_sa_{t['id']}", use_container_width=True):
                        st.session_state[f"clr_sa_{t['id']}"] += 1
                        st.rerun()
            
            if st.button("EXECUTE CONTRACT & DISPATCH", key=f"ex_{t['id']}", type="primary", use_container_width=True):
                # Ensure something was actually drawn
                has_sr = s_r.json_data is not None and len(s_r.json_data.get("objects", [])) > 0
                has_sa = s_a.json_data is not None and len(s_a.json_data.get("objects", [])) > 0
                
                if not (chk_tank and chk_ac and chk_wiper and chk_exterior and chk_seats and chk_deposit):
                    st.error("You must check off all items on the Pre-Handover Checklist before dispatching.")
                elif not (has_sr and has_sa):
                    st.error("Both Renter and Affiliate signatures are required to execute the contract.")
                else:
                    conn.execute("UPDATE bookings SET status = 'ONGOING' WHERE id = ?", (t['id'],))
                    conn.commit(); st.success("SUCCESS: Dispatched!"); time.sleep(1); st.rerun()

    st.divider()
    st.markdown("<h3 style='text-align: center;'>🔵 ONGOING TRIPS (Returns & Settlement)</h3>", unsafe_allow_html=True)
    ongoing = pd.read_sql_query("SELECT b.id, b.vehicle_id, b.renter_username, v.make, v.plate FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE v.owner_username = ? AND b.status = 'ONGOING'", conn, params=(username,))
    if ongoing.empty: st.info("No vehicles currently on the road.")
    for _, t in ongoing.iterrows():
        with st.expander(f"RECEIVE RETURN: {t['make']} ({t['plate']}) - Renter: {t['renter_username']}"):
            st.markdown(f"*RETURN SETTLEMENT (Ref: DRV-{t['id']:05d})*")
            st.write("Uncheck boxes to apply deductions against the ₱5,000.00 Security Deposit.")
            
            c1, c2 = st.columns(2)
            with c1:
                f_ok = st.checkbox("Fuel OK", value=True, key=f"f_{t['id']}")
                fuel_deduct = 0.0
                if not f_ok:
                    fuel_deduct = st.number_input("Fuel Refill Cost (₱)", min_value=0.0, step=100.0, key=f"f_cost_{t['id']}")
                
                c_ok = st.checkbox("Cleanliness OK", value=True, key=f"c_{t['id']}")
                clean_deduct = 0.0
                if not c_ok:
                    st.warning("⚠️ Soiled Vehicle: ₱500.00 deduction applied.")
                    clean_deduct = 500.0
                
                d_ok = st.checkbox("No Damage Found", value=True, key=f"d_{t['id']}")
                damage_deduct = 0.0
                if not d_ok:
                    dam_type = st.radio("Damage Penalty Type", ["Per Panel (₱4k/panel)", "Custom Repair Estimate"], key=f"d_type_{t['id']}")
                    if dam_type == "Per Panel (₱4k/panel)":
                        panels = st.number_input("Number of Damaged Panels", min_value=1, step=1, key=f"d_pan_{t['id']}")
                        damage_deduct = panels * 4000.0
                    else:
                        damage_deduct = st.number_input("Repair Shop Estimate (₱)", min_value=0.0, step=500.0, key=f"d_est_{t['id']}")

                total_deduct = fuel_deduct + clean_deduct + damage_deduct
                refund_amount = 5000.0 - total_deduct
                
                st.divider()
                st.write(f"*Total Deductions:* ₱{total_deduct:,.2f}")
                
                if refund_amount < 0:
                    st.error(f"🚨 Deductions exceed deposit! Renter owes an additional ₱{abs(refund_amount):,.2f}")
                    refund_amount = 0.0
                else:
                    st.info(f"💰 *Deposit to Refund:* ₱{refund_amount:,.2f}")

            # --- PERFECTLY CENTERED RETURN SIGNATURE ---
            with c2:
                st.markdown("<div style='text-align: center;'><b>Renter Final Sign-off</b></div>", unsafe_allow_html=True)
                if f"clr_sret_{t['id']}" not in st.session_state: st.session_state[f"clr_sret_{t['id']}"] = 0
                
                _, mid_ret, _ = st.columns([1, 4, 1])
                with mid_ret:
                    s_ret = st_canvas(stroke_width=2, stroke_color="#000", background_color="#eee", height=150, width=250, display_toolbar=False, key=f"sret_{t['id']}_{st.session_state[f'clr_sret_{t['id']}']}")
                    if st.button("🧹 Clear / Erase", key=f"btn_sret_{t['id']}", use_container_width=True):
                        st.session_state[f"clr_sret_{t['id']}"] += 1
                        st.rerun()
            
            if st.button("SETTLE & COMPLETE JOURNEY", key=f"comp_{t['id']}", type="primary", use_container_width=True):
                has_sret = s_ret.json_data is not None and len(s_ret.json_data.get("objects", [])) > 0
                
                if has_sret:
                    conn.execute("UPDATE bookings SET amount = amount - ?, status = 'COMPLETED' WHERE id = ?", (refund_amount, t['id']))
                    conn.execute("UPDATE vehicles SET booking_status = 'AVAILABLE' WHERE id = ?", (t['vehicle_id'],))
                    conn.commit()
                    st.success(f"SUCCESS: Journey Completed! Please refund ₱{refund_amount:,.2f} to the renter."); time.sleep(2.5); st.rerun()
                else: 
                    st.error("Renter must sign to acknowledge deductions and settle the trip.")

with tabs[1]:
    st.markdown("<h3 style='text-align: center;'>MY FLEET CONTROLS</h3>", unsafe_allow_html=True)
    fleet = pd.read_sql_query("SELECT id, make, model, plate, booking_status, admin_status FROM vehicles WHERE owner_username = ?", conn, params=(username,))
    if fleet.empty: st.info("You haven't added any vehicles yet.")
    for _, c in fleet.iterrows():
        with st.expander(f"{c['make']} {c['model']} - Status: {c['booking_status']} (Admin: {c['admin_status']})"):
            if c['admin_status'] == 'APPROVED':
                if c['booking_status'] == 'AVAILABLE' and st.button("Hide Vehicle", key=f"h_{c['id']}"):
                    conn.execute("UPDATE vehicles SET booking_status = 'UNAVAILABLE' WHERE id = ?", (c['id'],))
                    conn.commit(); st.rerun()
                elif c['booking_status'] == 'UNAVAILABLE' and st.button("Repost Vehicle", key=f"s_{c['id']}"):
                    conn.execute("UPDATE vehicles SET booking_status = 'AVAILABLE' WHERE id = ?", (c['id'],))
                    conn.commit(); st.rerun()

with tabs[2]:
    st.markdown("<h3 style='text-align: center;'>REGISTER A VEHICLE</h3>", unsafe_allow_html=True)
    with st.form("add_v"):
        cat = st.selectbox("CATEGORY", list(FIXED_RATES.keys()))
        c1, c2 = st.columns(2)
        ma, mo = c1.text_input("MAKE (e.g. Nissan)"), c2.text_input("MODEL (e.g. Terra VE)")
        ye, pl = c1.text_input("YEAR"), c2.text_input("PLATE NUMBER")
        
        c3, c4 = st.columns(2)
        bn = c3.text_input("PAYOUT BANK NAME (e.g. BDO, BPI, GCash)")
        an = c4.text_input("ACCOUNT NUMBER")
        
        vi, orc = st.file_uploader("Vehicle Photo", type=['jpg','png']), st.file_uploader("OR/CR Document", type=['jpg','png'])
        if st.form_submit_button("SUBMIT FOR APPROVAL", type="primary"):
            if ma and mo and pl and bn and an and vi and orc:
                conn.execute("INSERT INTO vehicles (owner_username, make, model, year, plate, bank_name, account_no, vehicle_img, or_cr_img, category, approved_price) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (username, ma.title(), mo.title(), ye, pl.upper(), bn, an, save_file(vi), save_file(orc), cat, FIXED_RATES.get(cat,0)))
                conn.commit(); st.success("SUCCESS: Vehicle Submitted! Pending Admin Approval.")
            else: st.error("Please fill all fields, including Payout Bank details, and upload both images.")

with tabs[3]:
    st.markdown("<h3 style='text-align: center;'>REGISTER A DRIVER</h3>", unsafe_allow_html=True)
    with st.form("add_d"):
        c1, c2, c3 = st.columns(3)
        df_first = c1.text_input("First Name").title()
        df_mid = c2.text_input("Middle Name").title()
        df_last = c3.text_input("Last Name").title()
        c4, c5 = st.columns(2)
        d_contact = c4.text_input("Contact Number")
        d_age = c5.number_input("Age", min_value=18, max_value=99, step=1)
        d_address = st.text_area("Full Address")
        is_owner = st.checkbox("I am the driver (Owner driving)")
        
        st.write("*Identity Verification (2 IDs Required)*")
        c6, c7 = st.columns(2)
        d_gov = c6.file_uploader("Upload Govt ID", type=['jpg','png'], key="dgov")
        d_lic = c7.file_uploader("Upload Professional Driver's License", type=['jpg','png'], key="dlic")
        
        if st.form_submit_button("SUBMIT DRIVER FOR APPROVAL", type="primary"):
            if df_first and df_last and d_contact and d_gov and d_lic:
                conn.execute("INSERT INTO drivers (owner_username, first_name, middle_name, last_name, age, address, contact_number, is_owner, license_img, govt_id_img, admin_status) VALUES (?,?,?,?,?,?,?,?,?,?, 'PENDING')", (username, df_first, df_mid, df_last, d_age, d_address, d_contact, 1 if is_owner else 0, save_file(d_lic), save_file(d_gov)))
                conn.commit(); st.success("SUCCESS: Driver Submitted! Pending Admin Approval.")
            else: st.error("Please fill all required fields and upload both IDs.")
            
    st.divider()
    st.markdown("<h3 style='text-align: center;'>MY REGISTERED DRIVERS</h3>", unsafe_allow_html=True)
    try:
        my_drivers = pd.read_sql_query("SELECT first_name, last_name, contact_number, admin_status FROM drivers WHERE owner_username = ?", conn, params=(username,))
        if not my_drivers.empty: st.dataframe(my_drivers, hide_index=True, use_container_width=True)
        else: st.info("No drivers registered yet.")
    except: pass
