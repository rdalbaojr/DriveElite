import streamlit as st
import pandas as pd
import time
from database_utils import get_connection

st.set_page_config(page_title="DriveElite Admin", layout="wide")
st.markdown("""<style>.stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }</style>""", unsafe_allow_html=True)

conn = get_connection()
try:
    conn.execute("CREATE TABLE IF NOT EXISTS vehicle_categories (name TEXT PRIMARY KEY, default_price REAL)")
    if pd.read_sql_query("SELECT COUNT(*) as cnt FROM vehicle_categories", conn).iloc[0]['cnt'] == 0:
        conn.executemany("INSERT INTO vehicle_categories (name, default_price) VALUES (?, ?)", [("Sedan", 1500), ("SUV", 4500), ("Van", 5000)])
        conn.commit()
except: pass

if not st.session_state.get('logged_in') or st.session_state.get('role') != 'ADMIN':
    st.title("ADMIN LOGIN")
    with st.form("login"):
        u = st.text_input("Master Username")
        p = st.text_input("Master Password", type="password")
        if st.form_submit_button("AUTHORIZE"):
            if u == "masterom" and p == "qZ822118qq":
                st.session_state.logged_in, st.session_state.username, st.session_state.role = True, "masterom", "ADMIN"
                st.rerun()
    st.stop() 

c1, c2 = st.columns([4, 1])
with c1: st.title("🛡️ MASTER COMMAND CENTER")
with c2:
    if st.button("🔒 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.clear(); st.rerun()

tabs = st.tabs(["PENDING USERS", "ASSET APPROVALS", "LOGISTICS DISPATCH", "FINANCIALS & PAYOUTS", "MASTER DB"])

with tabs[0]:
    c_rent, c_aff = st.columns(2)
    with c_rent:
        st.markdown("<h3 style='text-align: center;'>🚙 PENDING RENTERS</h3>", unsafe_allow_html=True)
        renters = pd.read_sql_query("SELECT * FROM users WHERE admin_status = 'PENDING' AND role = 'RENTER'", conn)
        for i, r in renters.iterrows():
            with st.expander(f"{r['full_name']} (@{r['username']})"):
                # ADDED NATIONALITY DISPLAY HERE
                st.write(f"*Age:* {r['age']} | *Nationality:* {r.get('nationality', 'Filipino')} | *Contact:* {r['contact_number']}")
                if r.get('id_img'): st.image(r['id_img'], caption="Passport / Govt ID")
                if r.get('license_img'): st.image(r['license_img'], caption="Driver's License")
                c_b1, c_b2 = st.columns(2)
                if c_b1.button("APPROVE", key=f"ra_{r['id']}", type="primary", use_container_width=True):
                    conn.execute("UPDATE users SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

    with c_aff:
        st.markdown("<h3 style='text-align: center;'>💼 PENDING AFFILIATES</h3>", unsafe_allow_html=True)
        affiliates = pd.read_sql_query("SELECT * FROM users WHERE admin_status = 'PENDING' AND role = 'AFFILIATE'", conn)
        for i, r in affiliates.iterrows():
            with st.expander(f"{r['full_name']} (@{r['username']})"):
                # ADDED NATIONALITY DISPLAY HERE
                st.write(f"*Age:* {r['age']} | *Nationality:* {r.get('nationality', 'Filipino')} | *Contact:* {r['contact_number']}")
                if r.get('id_img'): st.image(r['id_img'], caption="Passport / Govt ID")
                if r.get('license_img'): st.image(r['license_img'], caption="Driver's License") 
                c_b1, c_b2 = st.columns(2)
                if c_b1.button("APPROVE", key=f"aa_{r['id']}", type="primary", use_container_width=True):
                    conn.execute("UPDATE users SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

with tabs[1]:
    st.markdown("<h3 style='text-align: center;'>PENDING VEHICLES</h3>", unsafe_allow_html=True)
    pv = pd.read_sql_query("SELECT * FROM vehicles WHERE admin_status = 'PENDING'", conn)
    for i, r in pv.iterrows():
        with st.expander(f"{r['make']} {r['model']} ({r['plate']}) - Owner: @{r['owner_username']}"):
            st.write(f"*Payout Bank:* {r.get('bank_name', 'N/A')} | *Account:* {r.get('account_no', 'N/A')}")
            col_img1, col_img2 = st.columns(2)
            if r.get('vehicle_img'): col_img1.image(r['vehicle_img'], caption="Vehicle Photo")
            if r.get('or_cr_img'): col_img2.image(r['or_cr_img'], caption="OR/CR")
            if st.button("APPROVE VEHICLE", key=f"va_{r['id']}", type="primary", use_container_width=True):
                conn.execute("UPDATE vehicles SET admin_status = 'APPROVED' WHERE id = ?", (r['id'],)); conn.commit(); st.rerun()

with tabs[2]:
    st.markdown("<h3 style='text-align: center;'>LOGISTICS DISPATCH & ACTIVE TRIPS</h3>", unsafe_allow_html=True)
    try:
        bookings = pd.read_sql_query("SELECT b.*, u.full_name as renter_name FROM bookings b JOIN users u ON b.renter_username = u.username WHERE b.status != 'COMPLETED'", conn)
        for i, r in bookings.iterrows():
            with st.expander(f"Ref #DRV-{r['id']:05d} | STATUS: {r['status']} | RENTER: {r['renter_name']}"):
                st.write(f"*Amount Paid:* ₱{r['amount']:,.2f} | *Dest:* {r.get('destination', 'N/A')}")
    except: pass

with tabs[3]:
    st.markdown("<h3 style='text-align: center;'>💰 PLATFORM FINANCIALS & PAYOUTS</h3>", unsafe_allow_html=True)
    try:
        st.write("#### 💸 PENDING AFFILIATE PAYOUTS")
        q_pending = """
        SELECT b.id, u.full_name, v.bank_name, v.account_no, (b.amount * 0.85) as payout
        FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id JOIN users u ON v.owner_username = u.username
        WHERE b.status = 'COMPLETED' AND b.payout_status = 'PENDING'
        """
        pending_payouts = pd.read_sql_query(q_pending, conn)
        if not pending_payouts.empty:
            for _, p in pending_payouts.iterrows():
                with st.expander(f"Booking #{p['id']:05d} | {p['full_name']} | ₱{p['payout']:,.2f}"):
                    st.write(f"*Transfer To:* {p['bank_name']}")
                    st.write(f"*Account No:* {p['account_no']}")
                    if st.button("✅ MARK AS PAID", key=f"pay_{p['id']}", type="primary"):
                        conn.execute("UPDATE bookings SET payout_status = 'PAID' WHERE id = ?", (p['id'],))
                        conn.commit(); st.rerun()
        else:
            st.info("No pending payouts. All affiliates are paid up!")

        st.divider()

        st.write("#### 📊 MASTER FINANCIAL LEDGER")
        q_ledger = """
        SELECT b.id as 'Booking No', u.full_name as 'Full Name', b.amount as 'Gross Total', 
        (b.amount * 0.15) as 'Admin Fee', (b.amount * 0.85) as 'Affiliate Payout', b.payout_status as 'Status' 
        FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id JOIN users u ON v.owner_username = u.username 
        WHERE b.status = 'COMPLETED'
        """
        df_fin = pd.read_sql_query(q_ledger, conn)
        
        if not df_fin.empty:
            total_admin = df_fin['Admin Fee'].sum()
            
            for col in ['Gross Total', 'Admin Fee', 'Affiliate Payout']:
                df_fin[col] = df_fin[col].apply(lambda x: f"₱{x:,.2f}")
            
            styled_df = df_fin.style.set_properties(
                subset=['Booking No', 'Full Name', 'Status'], 
                **{'font-weight': 'normal', 'text-align': 'center'}
            ).set_properties(
                subset=['Gross Total', 'Admin Fee', 'Affiliate Payout'], 
                **{'font-weight': 'normal', 'text-align': 'right'}
            ).set_table_styles([
                dict(selector='th', props=[('text-align', 'center'), ('font-weight', 'bold')])
            ])
            
            st.dataframe(styled_df, hide_index=True, use_container_width=True)
            st.write(f"*Total Admin Revenue:* ₱{total_admin:,.2f}")
    except Exception as e: pass

with tabs[4]:
    st.markdown("<h3 style='text-align: center;'>📈 CATEGORY MANAGER</h3>", unsafe_allow_html=True)
    with st.form("add_cat", clear_on_submit=True):
        n = st.text_input("New Category")
        p = st.number_input("Daily Rate", min_value=500.0)
        
        if st.form_submit_button("ADD CATEGORY"):
            if n:
                try:
                    conn.execute("INSERT INTO vehicle_categories (name, default_price) VALUES (?, ?)", (n.title(), p))
                    conn.commit()
                    st.success(f"✅ Successfully added '{n.title()}'!")
                    time.sleep(1)
                    st.rerun()
                except:
                    st.error(f"⚠️ The category '{n.title()}' already exists! Please enter a unique category name.")
            else:
                st.error("Please enter a category name.")
    
    st.divider()
    st.markdown("<h3 style='text-align: center;'>ALL REGISTERED USERS</h3>", unsafe_allow_html=True)
    try:
        db_tabs = st.tabs(["🚙 RENTERS", "💼 AFFILIATES"])
        
        q_renters = "SELECT full_name as 'FULLNAME', address as 'ADDRESS', contact_number as 'CONTACT NO.', admin_status as 'ADMIN STATUS' FROM users WHERE role = 'RENTER'"
        with db_tabs[0]: 
            st.dataframe(pd.read_sql_query(q_renters, conn), hide_index=True, use_container_width=True)
            
        q_affiliates = "SELECT full_name as 'FULLNAME', address as 'ADDRESS', contact_number as 'CONTACT NO.', admin_status as 'ADMIN STATUS' FROM users WHERE role = 'AFFILIATE'"
        with db_tabs[1]: 
            st.dataframe(pd.read_sql_query(q_affiliates, conn), hide_index=True, use_container_width=True)
    except: pass
