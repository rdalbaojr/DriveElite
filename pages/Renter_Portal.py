
import streamlit as st
import pandas as pd
import datetime
import time
import os
import base64
from database_utils import get_connection

st.set_page_config(page_title="DriveElite Renter", layout="wide")
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    [data-testid='stSidebarNav'] span { text-transform: uppercase !important; font-weight: bold !important; }
    .bill-box { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

conn = get_connection()

def create_pdf_download(data):
    receipt_text = f"--- DRIVEELITE RECEIPT ---\nRef: {data['ref']}\nDate: {datetime.date.today()}\nRenter: {data['user']}\nVehicle: {data['vehicle']}\nGross Rental: PHP {data['gross']:,.2f}\nSecurity Deposit: PHP {data['deposit']:,.2f}\n---\nTOTAL PAID: PHP {data['net']:,.2f}\nStatus: PAID"
    b64 = base64.b64encode(receipt_text.encode()).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="Receipt_{data["ref"]}.txt">📥 Download Official Receipt</a>'

# --- RENTER LOGIN ---
if not st.session_state.get('logged_in') or st.session_state.get('role') != 'RENTER':
    st.title("🚙 RENTER LOGIN")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN"):
            user = pd.read_sql_query("SELECT * FROM users WHERE username=? AND password=? AND role='RENTER'", conn, params=(u, p))
            if not user.empty:
                if user.iloc[0]['admin_status'] == 'PENDING': st.warning("⏳ Account pending Admin approval.")
                elif user.iloc[0]['admin_status'] == 'REJECTED': st.error("🚫 Account application rejected.")
                else:
                    st.session_state.logged_in, st.session_state.username, st.session_state.role = True, u, 'RENTER'
                    st.rerun()
            else: st.error("❌ Invalid credentials.")
    st.stop()

with st.sidebar:
    st.subheader("📝 Renter Policies")
    st.markdown("* *Fuel:* Match pickup level.\n* *Clean:* Return clean or ₱1.5K fee.\n* *Damage:* Renter liable.\n* *Late:* ₱500/hr.")

st.title("🚙 DriveElite Showroom")
renter_user = st.session_state.username
tabs = st.tabs(["🌟 SHOWROOM", "📅 MY TRIPS"])

with tabs[0]:
    try: cat_list = ["All"] + pd.read_sql_query("SELECT name FROM vehicle_categories", conn)['name'].tolist()
    except: cat_list = ["All", "Sedan", "SUV", "Van"]
    cat_filter = st.selectbox("FILTER CATEGORY", cat_list)
    
    available_cars = pd.read_sql_query("SELECT * FROM vehicles WHERE admin_status = 'APPROVED' AND booking_status = 'AVAILABLE'", conn)
    if cat_filter != "All" and not available_cars.empty: 
        available_cars = available_cars[available_cars['category'].astype(str).str.strip().str.lower() == cat_filter.strip().lower()]

    for i, car in available_cars.iterrows():
        with st.container(border=True):
            col1, col2 = st.columns([1, 2])
            with col1:
                if car.get('vehicle_img'): st.image(car['vehicle_img'])
            with col2:
                st.write(f"### {car['make']} {car['model']}")
                reviews_df = pd.read_sql_query("SELECT rating, review_text FROM reviews WHERE vehicle_id = ?", conn, params=(car['id'],))
                if not reviews_df.empty: st.write(f"⭐ *{reviews_df['rating'].mean():.1f} / 5.0* ({len(reviews_df)} Reviews)")
                st.write(f"*Rate:* ₱{car['approved_price']:,.2f} / day")
                
                with st.popover(f"BOOK THIS {car['model']}"):
                    dest = st.text_input("Destination", key=f"d_{car['id']}")
                    drive_type = st.radio("Drive Type", ["Self-Drive", "With Driver"], key=f"dt_{car['id']}", horizontal=True)
                    
                    c_loc1, c_loc2 = st.columns(2)
                    p_loc = c_loc1.text_input("Pickup Location", key=f"pl_{car['id']}")
                    r_loc = c_loc2.text_input("Return Location", key=f"rl_{car['id']}")
                    
                    c3, c4 = st.columns(2)
                    p_date = c3.date_input("Pickup Date", datetime.date.today(), key=f"pd_{car['id']}")
                    p_time = c4.time_input("Pickup Time", datetime.time(8, 0), key=f"pt_{car['id']}")
                    
                    c5, c6 = st.columns(2)
                    r_date = c5.date_input("Return Date", datetime.date.today() + datetime.timedelta(days=1), key=f"rd_{car['id']}")
                    r_time = c6.time_input("Return Time", datetime.time(18, 0), key=f"rt_{car['id']}")
                    
                    days = (r_date - p_date).days if (r_date - p_date).days > 0 else 1
                    gross_total = days * car['approved_price']
                    security_deposit = 5000.00 
                    net_settlement = gross_total + security_deposit
                    
                    st.markdown(f"""
                    <div class="bill-box">
                        <table style="width:100%">
                            <tr><td><b>Gross Rental ({days} Days)</b></td><td style="text-align:right">₱{gross_total:,.2f}</td></tr>
                            <tr><td><b>Add: Security Deposit (Refundable)</b></td><td style="text-align:right; color:green">+ ₱{security_deposit:,.2f}</td></tr>
                            <tr style="border-top: 2px solid black"><td><b>TOTAL DUE NOW</b></td><td style="text-align:right"><b>₱{net_settlement:,.2f}</b></td></tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    method = st.radio("Payment Method", ["📱 GCash/Maya", "💳 Credit Card"], key=f"m_{car['id']}")
                    
                    cc_name, cc_num, cc_exp, cc_cvv, e_ref = "", "", "", "", ""
                    
                    if method == "📱 GCash/Maya":
                        if os.path.exists("admin_qr.png"): st.image("admin_qr.png", width=180)
                        st.write(f"*Pay exactly: ₱{net_settlement:,.2f} to Romeo A.*")
                        e_ref = st.text_input("Enter Reference No.", key=f"ref_{car['id']}")
                    else:
                        st.markdown("🔒 *Secure Credit Card Checkout*")
                        cc_name = st.text_input("Name on Card", placeholder="Juan Dela Cruz", key=f"ccname_{car['id']}")
                        cc_num = st.text_input("Card Number", max_chars=19, placeholder="0000 0000 0000 0000", key=f"ccnum_{car['id']}")
                        c_exp, c_cvv = st.columns(2)
                        cc_exp = c_exp.text_input("Expiry Date", placeholder="MM/YY", max_chars=5, key=f"ccexp_{car['id']}")
                        cc_cvv = c_cvv.text_input("CVV", type="password", max_chars=4, placeholder="123", key=f"cccvv_{car['id']}")

                    if st.button("CONFIRM & PAY", key=f"btn_{car['id']}", type="primary", use_container_width=True):
                        if not dest or not p_loc or not r_loc:
                            st.error("⚠️ Please fill in Destination and Pickup/Return locations.")
                        elif method == "💳 Credit Card" and (not cc_name or not cc_num or not cc_exp or not cc_cvv):
                            st.error("⚠️ Please fill in all Credit Card details.")
                        elif method == "📱 GCash/Maya" and not e_ref:
                            st.error("⚠️ Please enter your GCash/Maya Reference Number.")
                        else:
                            with st.spinner("🔒 Connecting to secure payment gateway..."):
                                time.sleep(2.5) 
                                
                                cursor = conn.cursor()
                                p_str = f"{p_date} {p_time.strftime('%I:%M %p')}"
                                r_str = f"{r_date} {r_time.strftime('%I:%M %p')}"
                                
                                cursor.execute("INSERT INTO bookings (vehicle_id, renter_username, amount, pickup_loc, return_loc, destination, pickup_time, return_time, drive_type, payment_method, status) VALUES (?,?,?,?,?,?,?,?,?,?, 'CONFIRMED')", (car['id'], renter_user, net_settlement, p_loc, r_loc, dest, p_str, r_str, drive_type, method))
                                bid = cursor.lastrowid
                                conn.execute("UPDATE vehicles SET booking_status = 'BOOKED' WHERE id = ?", (car['id'],))
                                conn.commit()
                                
                                st.success("✅ Payment Approved & Booking Confirmed!")
                                receipt_data = {'ref': f"DRV-{bid:05d}", 'user': renter_user, 'vehicle': f"{car['make']} {car['model']}", 'gross': gross_total, 'deposit': security_deposit, 'net': net_settlement}
                                st.markdown(create_pdf_download(receipt_data), unsafe_allow_html=True)
                                time.sleep(3)
                                st.rerun()

with tabs[1]:
    st.subheader("MY BOOKINGS")
    # Added b.vehicle_id to the query here so the review system knows which car it is!
    my_trips = pd.read_sql_query("SELECT b.id, b.vehicle_id, printf('DRV-%05d', b.id) as 'Ref', v.make, v.model, b.amount, b.status FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id WHERE b.renter_username=?", conn, params=(renter_user,))
    
    # We drop vehicle_id here so it stays hidden from the clean user table
    st.dataframe(my_trips.drop(columns=['id', 'vehicle_id', 'make', 'model']), hide_index=True)
    
    completed = my_trips[my_trips['status'] == 'COMPLETED']
    for i, trip in completed.iterrows():
        rev_check = pd.read_sql_query("SELECT * FROM reviews WHERE booking_id = ?", conn, params=(int(trip['id']),))
        if rev_check.empty:
            with st.expander(f"⭐ Rate your {trip['make']} trip ({trip['Ref']})"):
                with st.form(f"rev_{trip['id']}"):
                    r = st.slider("Rating", 1, 5, 5)
                    t = st.text_area("Review")
                    if st.form_submit_button("Submit Review"):
                        conn.execute("INSERT INTO reviews (booking_id, vehicle_id, renter_username, rating, review_text) VALUES (?,?,?,?,?)", (int(trip['id']), int(trip['vehicle_id']), renter_user, r, t))
                        conn.commit()
                        st.rerun()
