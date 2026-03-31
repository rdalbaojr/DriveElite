import streamlit as st
import pandas as pd
from database_utils import get_connection

st.set_page_config(page_title="DriveElite Admin", layout="wide")
conn = get_connection()

# Auth Check
if not st.session_state.get('logged_in') or st.session_state.get('role') != 'ADMIN':
    st.title("ADMIN LOGIN")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("AUTHORIZE"):
            if u == "masterom" and p == "qZ822118qq":
                st.session_state.logged_in, st.session_state.username, st.session_state.role = True, "masterom", "ADMIN"
                st.rerun()
    st.stop()

st.title("🛡️ MASTER COMMAND CENTER")

with st.sidebar:
    st.markdown("### 👨‍💼 Admin Controls")
    st.info(f"Logged in as: {st.session_state.username}")
    if st.button("🔒 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# DEFINING 6 TABS (Renamed first tab to PENDING APPROVALS)
tabs = st.tabs(["PENDING APPROVALS", "ASSETS", "LOGISTICS", "FINANCIALS", "🗄️ FILING CABINET", "PROMOS & DB"])

with tabs[0]:
    st.markdown("<h3 style='text-align: center;'>📋 PENDING APPROVALS</h3>", unsafe_allow_html=True)
    
    # NEW: 3 Sub-tabs for better organization!
    p_tabs = st.tabs(["🚙 PENDING RENTERS", "💼 PENDING AFFILIATES", "👨‍✈️ PENDING DRIVERS"])
    
    with p_tabs[0]:
        renters = pd.read_sql_query("SELECT * FROM users WHERE admin_status = 'PENDING' AND role = 'RENTER'", conn)
        if renters.empty: st.info("No pending renters.")
        for i, r in renters.iterrows():
            with st.expander(f"{r['full_name']} (@{r['username']})"):
                st.write(f"*Age:* {r['age']} | *Nat:* {r.get('nationality', 'Filipino')} | *Contact:* {r['contact_number']}")
                c_img1, c_img2 = st.columns(2)
                if r.get('id_img'): c_img1.image(r['id_img'], caption="Passport / Govt ID")
                if r.get('license_img'): c_img2.image(r['license_img'], caption="Driver's License")
                if st.button("APPROVE RENTER", key=f"ra_{r['id']}", type="primary", use_container_width=True):
                    conn.execute("UPDATE users SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

    with p_tabs[1]:
        affiliates = pd.read_sql_query("SELECT * FROM users WHERE admin_status = 'PENDING' AND role = 'AFFILIATE'", conn)
        if affiliates.empty: st.info("No pending affiliates.")
        for i, r in affiliates.iterrows():
            with st.expander(f"{r['full_name']} (@{r['username']})"):
                st.write(f"*Age:* {r['age']} | *Nat:* {r.get('nationality', 'Filipino')} | *Contact:* {r['contact_number']}")
                c_img1, c_img2 = st.columns(2)
                if r.get('id_img'): c_img1.image(r['id_img'], caption="Passport / Govt ID")
                if r.get('license_img'): c_img2.image(r['license_img'], caption="Driver's License") 
                if st.button("APPROVE AFFILIATE", key=f"aa_{r['id']}", type="primary", use_container_width=True):
                    conn.execute("UPDATE users SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

    # --- NEW: ADMIN CAN NOW APPROVE DRIVERS ---
    with p_tabs[2]:
        drivers = pd.read_sql_query("SELECT * FROM drivers WHERE admin_status = 'PENDING'", conn)
        if drivers.empty: st.info("No pending drivers.")
        for i, d in drivers.iterrows():
            with st.expander(f"{d['first_name']} {d['last_name']} (Affiliate: @{d['owner_username']})"):
                st.write(f"*Age:* {d['age']} | *Contact:* {d['contact_number']} | *Address:* {d['address']}")
                if d['is_owner']: st.info("ℹ️ This driver is also the registered Affiliate Owner.")
                
                c_img1, c_img2 = st.columns(2)
                if d.get('govt_id_img'): c_img1.image(d['govt_id_img'], caption="Govt ID")
                if d.get('license_img'): c_img2.image(d['license_img'], caption="Professional License")
                
                if st.button("APPROVE DRIVER", key=f"da_{d['id']}", type="primary", use_container_width=True):
                    conn.execute("UPDATE drivers SET admin_status = 'APPROVED' WHERE id = ?", (d['id'],)); conn.commit(); st.rerun()

with tabs[1]:
    st.subheader("Vehicle Approvals")
    pv = pd.read_sql_query("SELECT * FROM vehicles WHERE admin_status = 'PENDING'", conn)
    for i, r in pv.iterrows():
        with st.expander(f"{r['make']} {r['model']} ({r['plate']})"):
            col_img1, col_img2, col_img3 = st.columns(3)
            if r.get('vehicle_img'): col_img1.image(r['vehicle_img'], caption="Vehicle Photo")
            if r.get('or_cr_img'): col_img2.image(r['or_cr_img'], caption="OR/CR")
            if r.get('insurance_img'): col_img3.image(r['insurance_img'], caption="Insurance")
            if st.button("APPROVE ASSET", key=f"v_{r['id']}", type="primary"):
                conn.execute("UPDATE vehicles SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

with tabs[2]:
    st.subheader("Active Logistics")
    try:
        bookings = pd.read_sql_query("SELECT b.*, u.full_name as renter_name FROM bookings b JOIN users u ON b.renter_username = u.username WHERE b.status != 'COMPLETED'", conn)
        for i, r in bookings.iterrows():
            with st.expander(f"Ref #DRV-{r['id']:05d} | STATUS: {r['status']} | RENTER: {r['renter_name']}"):
                if r.get('with_driver', 0) == 1: st.markdown("👨‍✈️ *[TRIP INCLUDES PROFESSIONAL DRIVER]*")
                st.write(f"*Amount Paid:* ₱{r['amount']:,.2f} | *Dest:* {r.get('destination', 'N/A')}")
    except: pass

with tabs[3]:
    st.header("💰 Financial Ledger")
    c_in, c_out = st.columns(2)
    with c_in:
        st.subheader("📥 INCOMING: Verify Renters")
        try:
            q_in = "SELECT b.id, b.amount, b.payment_method, u.full_name FROM bookings b JOIN users u ON b.renter_username = u.username WHERE b.status IN ('CONFIRMED', 'ONGOING') ORDER BY b.id DESC"
            incoming = pd.read_sql_query(q_in, conn)
            if incoming.empty: st.info("No recent incoming payments to verify.")
            for _, r in incoming.iterrows():
                with st.container(border=True):
                    st.write(f"*DRV-{r['id']:05d}* | {r['full_name']} | ₱{r['amount']:,.2f}")
                    st.success(f"*{r.get('payment_method', 'No Reference')}*")
        except: pass

    with c_out:
        st.subheader("📤 OUTGOING: Pay Affiliates")
        try:
            q_pending = "SELECT b.id, u.full_name, v.bank_name, v.account_no, (b.amount * 0.85) as payout FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id JOIN users u ON v.owner_username = u.username WHERE b.status = 'COMPLETED' AND b.payout_status = 'PENDING'"
            pending_payouts = pd.read_sql_query(q_pending, conn)
            if pending_payouts.empty: st.info("No pending affiliate payouts.")
            for _, p in pending_payouts.iterrows():
                with st.expander(f"DRV-{p['id']:05d} | {p['full_name']} | ₱{p['payout']:,.2f}"):
                    st.write(f"*Send To:* {p['bank_name']} | *Account:* {p['account_no']}")
                    if st.button("MARK AS PAID", key=f"pay_{p['id']}", type="primary", use_container_width=True):
                        conn.execute("UPDATE bookings SET payout_status = 'PAID' WHERE id = ?", (p['id'],)); conn.commit(); st.rerun()
        except: pass

with tabs[4]: 
    st.header("🗄️ Master Digital Filing Cabinet")
    search_id = st.number_input("Enter Booking ID", min_value=1, step=1)
    if st.button("PULL FULL CASE FILE"):
        q = "SELECT b.*, v.make, v.model, r.full_name as rname FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id JOIN users r ON b.renter_username = r.username WHERE b.id = ?"
        rec = pd.read_sql_query(q, conn, params=(search_id,))
        if not rec.empty:
            r = rec.iloc[0]
            st.success(f"Record Found: DRV-{r['id']:05d}")
            st.write("### 📸 10-Point Pre-Dispatch Inspection")
            
            c1, c2, c3, c4 = st.columns(4)
            if r['actual_dl_img']: c1.image(r['actual_dl_img'], caption="1. Driver's License")
            if r['front_img']: c2.image(r['front_img'], caption="2. Front Exterior")
            if r['back_img']: c3.image(r['back_img'], caption="3. Back Exterior")
            if r['left_img']: c4.image(r['left_img'], caption="4. Left Exterior")
            
            c5, c6, c7, c8 = st.columns(4)
            if r['right_img']: c5.image(r['right_img'], caption="5. Right Exterior")
            if r['odometer_img']: c6.image(r['odometer_img'], caption="6. Odometer/Dash")
            if r['dseat_img']: c7.image(r['dseat_img'], caption="7. Driver Seat")
            if r['pseat_img']: c8.image(r['pseat_img'], caption="8. Passenger Seat")
            
            c9, c10, c11, c12 = st.columns(4)
            if r['trunk_img']: c9.image(r['trunk_img'], caption="9. Inside Trunk")
            if r['tire_img']: c10.image(r['tire_img'], caption="10. Spare Tire")
            
            if r['damage_img']:
                st.divider()
                st.error("⚠️ DAMAGE REPORTED ON RETURN")
                st.image(r['damage_img'], caption="Proof of Damage", width=400)
        else: st.error("No record found.")

with tabs[5]:
    col_promo, col_cat = st.columns(2)
    with col_promo:
        st.subheader("📢 Promo Manager")
        with st.form("promo"):
            t = st.text_input("Promo Title")
            m = st.text_area("Promo Message")
            if st.form_submit_button("PUBLISH TO RENTERS"):
                if t and m:
                    conn.execute("UPDATE admin_promos SET active = 0")
                    conn.execute("INSERT INTO admin_promos (title, message) VALUES (?,?)", (t, m)); conn.commit(); st.success("Live!")
    with col_cat:
        st.subheader("📈 Category Manager")
        with st.form("add_cat", clear_on_submit=True):
            n = st.text_input("New Category (e.g., Pickup, Luxury)")
            p = st.number_input("Daily Rate (₱)", min_value=500.0, step=100.0, value=2500.0)
            if st.form_submit_button("ADD NEW CATEGORY"):
                if n:
                    try:
                        conn.execute("INSERT INTO vehicle_categories (name, default_price) VALUES (?, ?)", (n.title(), p)); conn.commit()
                    except: pass
    
    st.divider()
    st.write("🔍 *Quick Profile Viewer (Lookup IDs)*")
    all_users = pd.read_sql_query("SELECT username, full_name, role, id_img, license_img FROM users WHERE admin_status = 'APPROVED'", conn)
    if not all_users.empty:
        user_list = ["-- Select a User --"] + all_users['full_name'].tolist()
        selected_user = st.selectbox("Search for an Approved User to view their documents:", user_list)
        if selected_user != "-- Select a User --":
            u_data = all_users[all_users['full_name'] == selected_user].iloc[0]
            c_id1, c_id2 = st.columns(2)
            with c_id1:
                if u_data['id_img']: st.image(u_data['id_img'], caption="GOVT ID")
            with c_id2:
                if u_data['license_img']: st.image(u_data['license_img'], caption="DRIVER'S LICENSE")
    st.divider()
    
    st.markdown("<h3 style='text-align: center;'>ALL REGISTERED USERS</h3>", unsafe_allow_html=True)
    try:
        # NEW: Added Drivers to the Master Database viewer
        db_tabs = st.tabs(["🚙 RENTERS", "💼 AFFILIATES", "👨‍✈️ DRIVERS"])
        q_renters = "SELECT full_name as 'FULLNAME', address as 'ADDRESS', contact_number as 'CONTACT NO.', admin_status as 'ADMIN STATUS' FROM users WHERE role = 'RENTER'"
        with db_tabs[0]: st.dataframe(pd.read_sql_query(q_renters, conn), hide_index=True, use_container_width=True)
        
        q_affiliates = "SELECT full_name as 'FULLNAME', address as 'ADDRESS', contact_number as 'CONTACT NO.', admin_status as 'ADMIN STATUS' FROM users WHERE role = 'AFFILIATE'"
        with db_tabs[1]: st.dataframe(pd.read_sql_query(q_affiliates, conn), hide_index=True, use_container_width=True)
        
        q_drivers = "SELECT first_name || ' ' || last_name as 'FULLNAME', owner_username as 'BELONGS TO AFFILIATE', contact_number as 'CONTACT NO.', admin_status as 'ADMIN STATUS' FROM drivers"
        with db_tabs[2]: st.dataframe(pd.read_sql_query(q_drivers, conn), hide_index=True, use_container_width=True)
    except: pass
