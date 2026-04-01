import streamlit as st
import pandas as pd
import datetime
import time
from database_utils import get_connection

st.set_page_config(page_title="DriveElite Showroom", layout="wide")

st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); }
    .promo-banner { background: linear-gradient(90deg, #ff4b4b, #ff8f8f); color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .bill-box { background-color: #ffffff; padding: 20px; border-radius: 10px; border: 1px solid #e0e0e0; margin-top: 10px; }
    .savings-badge { background-color: #d4edda; color: #155724; padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 15px; }
    .star-rating { color: #FFD700; font-size: 18px; }
</style>
""", unsafe_allow_html=True)

conn = get_connection()

if not st.session_state.get('logged_in') or st.session_state.get('role') != 'RENTER':
    st.markdown("<h2 style='text-align: center;'>🚙 RENTER ACCESS</h2>", unsafe_allow_html=True)
    with st.form("login_renter"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("LOGIN TO SHOWROOM", use_container_width=True):
            user = pd.read_sql_query("SELECT * FROM users WHERE username=? AND password=? AND role='RENTER'", conn, params=(u, p))
            if not user.empty:
                if user.iloc[0]['admin_status'] == 'APPROVED':
                    st.session_state.logged_in, st.session_state.username, st.session_state.role = True, u, 'RENTER'
                    st.rerun()
                else: st.warning("⏳ Account pending Admin approval.")
            else: st.error("❌ Invalid credentials.")
    st.stop()

renter_user = st.session_state.username

with st.sidebar:
    st.markdown(f"### 👤 Welcome, {renter_user}!")
    st.markdown("""
    *Quick Rules:*
    * *Fuel:* Match pickup level.
    * *Clean:* Return clean.
    * *Late:* ₱500/hr penalty.
    """)
    if st.button("🔒 LOGOUT", use_container_width=True):
        st.session_state.clear()
        st.rerun()

tabs = st.tabs(["🌟 VEHICLE SHOWROOM", "📅 MY BOOKINGS"])

with tabs[0]:
    try:
        promo = pd.read_sql_query("SELECT title, message FROM admin_promos WHERE active = 1 ORDER BY id DESC LIMIT 1", conn)
        if not promo.empty:
            st.markdown(f'<div class="promo-banner"><h2 style="margin:0;">🔥 {promo.iloc[0]["title"]} 🔥</h2><p style="margin:5px 0 0 0; font-size:18px;">{promo.iloc[0]["message"]}</p></div>', unsafe_allow_html=True)
    except: pass

    try:
        cat_df = pd.read_sql_query("SELECT name FROM vehicle_categories", conn)
        cat_list = ["All"] + [str(n).strip() for n in cat_df['name'].tolist()]
    except: cat_list = ["All", "Sedan", "SUV", "Van"]
    
    c_f1, c_f2 = st.columns([2, 1])
    cat_filter = c_f1.selectbox("Filter by Category", cat_list)
    search_query = c_f2.text_input("Search Brand/Model", placeholder="e.g. Nissan")

    query = "SELECT * FROM vehicles WHERE admin_status = 'APPROVED' AND booking_status = 'AVAILABLE'"
    cars = pd.read_sql_query(query, conn)

    if cat_filter != "All": cars = cars[cars['category'].str.strip() == cat_filter]
    if search_query: cars = cars[cars['make'].str.contains(search_query, case=False) | cars['model'].str.contains(search_query, case=False)]

    if cars.empty: st.info("No vehicles currently matching your search. Check back soon!")
    else:
        for i, car in cars.iterrows():
            with st.container(border=True):
                col1, col2 = st.columns([1, 2])
                with col1:
                    if car.get('vehicle_img'): st.image(car['vehicle_img'], use_container_width=True)
                with col2:
                    st.write(f"### {car['make']} {car['model']} ({car['year']})")
                    
                    try:
                        rat_df = pd.read_sql_query("SELECT AVG(rating) as avg, COUNT(rating) as cnt FROM bookings WHERE vehicle_id=? AND rating IS NOT NULL", conn, params=(car['id'],))
                        if not rat_df.empty and pd.notnull(rat_df.iloc[0]['avg']):
                            real_rating = float(rat_df.iloc[0]['avg'])
                            rev_count = int(rat_df.iloc[0]['cnt'])
                            stars = int(round(real_rating))
                            st.markdown(f"<span class='star-rating'>{'⭐' * stars}</span> *{real_rating:.1f}* ({rev_count} Reviews)", unsafe_allow_html=True)
                        else:
                            st.markdown("✨ *New on DriveElite* (No reviews yet)", unsafe_allow_html=True)
                    except:
                        st.markdown("✨ *New on DriveElite* (No reviews yet)", unsafe_allow_html=True)
                    
                    st.write(f"*Category:* {car['category']} | *Plate:* {car['plate']}")
                    st.write(f"#### ₱{car['approved_price']:,.2f} / Day")
                    
                    with st.popover(f"⚡ BOOK {car['model'].upper()} NOW"):
                        st.write("### 📍 Trip Details")
                        
                        drive_mode = st.radio("Driving Mode", ["Self-Drive", "With Professional Driver (+₱1,000/day)"], key=f"dm_{car['id']}")
                        is_with_driver = 1 if "Driver" in drive_mode else 0
                        
                        if is_with_driver:
                            st.info("👨‍✈️ *Driver Terms:* 10 hours duty/day. Overtime is ₱200/hr. Renter must provide driver meals (or ₱300/day) and safe overnight accommodation if outside Metro Manila.")
                        
                        dest = st.text_input("Destination", key=f"dest_{car['id']}")
                        
                        c_loc1, c_loc2 = st.columns(2)
                        p_loc = c_loc1.text_input("Pickup Location", placeholder="e.g. NAIA Terminal 3", key=f"ploc_{car['id']}")
                        r_loc = c_loc2.text_input("Return Location", placeholder="e.g. NAIA Terminal 3", key=f"rloc_{car['id']}")
                        
                        c_date1, c_date2 = st.columns(2)
                        p_date = c_date1.date_input("Pickup Date", datetime.date.today(), key=f"pdate_{car['id']}")
                        p_time = c_date1.time_input("Pickup Time", datetime.time(9, 0), key=f"ptime_{car['id']}")
                        
                        r_date = c_date2.date_input("Return Date", datetime.date.today() + datetime.timedelta(days=1), key=f"rdate_{car['id']}")
                        r_time = c_date2.time_input("Return Time", datetime.time(9, 0), key=f"rtime_{car['id']}")
                        
                        p_datetime = f"{p_date} {p_time.strftime('%I:%M %p')}"
                        r_datetime = f"{r_date} {r_time.strftime('%I:%M %p')}"
                        
                        days = (r_date - p_date).days if (r_date - p_date).days > 0 else 1
                        subtotal = days * car['approved_price']
                        
                        driver_fee = days * 1000.0 if is_with_driver else 0.0
                        
                        discount_pct = 0
                        if days >= 30: discount_pct = 0.20
                        elif days >= 14: discount_pct = 0.10
                        elif days >= 7: discount_pct = 0.05
                        
                        savings = subtotal * discount_pct
                        total_rent = (subtotal - savings) + driver_fee
                        deposit = 5000.00
                        grand_total = total_rent + deposit
                        
                        if savings > 0:
                            st.markdown(f'<div class="savings-badge">🎉 You saved ₱{savings:,.2f}!</div>', unsafe_allow_html=True)
                        
                        bill_html = '<div class="bill-box"><table style="width:100%">'
                        bill_html += f'<tr><td>Rental ({days} Days)</td><td style="text-align:right">₱{subtotal:,.2f}</td></tr>'
                        if is_with_driver:
                            bill_html += f'<tr><td style="color:#0056b3">Professional Driver Fee</td><td style="text-align:right; color:#0056b3">+ ₱{driver_fee:,.2f}</td></tr>'
                        bill_html += f'<tr><td style="color:red">Long-stay Discount</td><td style="text-align:right; color:red">- ₱{savings:,.2f}</td></tr>'
                        bill_html += f'<tr><td style="color:green">Refundable Deposit</td><td style="text-align:right; color:green">+ ₱{deposit:,.2f}</td></tr>'
                        bill_html += f'<tr style="border-top:2px solid #000"><td><b>GRAND TOTAL</b></td><td style="text-align:right"><b>₱{grand_total:,.2f}</b></td></tr>'
                        bill_html += '</table></div>'
                        
                        st.markdown(bill_html, unsafe_allow_html=True)
                        
                        st.divider()
                        pay_method = st.radio("Payment Method", ["GCash / Maya", "Credit Card"], key=f"pay_{car['id']}")
                        
                        ref_num = ""
                        if pay_method == "GCash / Maya":
                            st.info("📲 Scan the QR code below to send your payment directly to DriveElite.")
                            try:
                                st.image("gcash_qr.jpg", caption=f"Scan to Pay: ₱{grand_total:,.2f}", width=250)
                            except:
                                st.warning("⚠️ [Admin: Please save your QR image as 'gcash_qr.jpg' in the main folder so it appears here.]")
                            
                            ref_num = st.text_input("Enter GCash/Maya Reference Number *", placeholder="e.g. 100239481923", key=f"ref_{car['id']}")
                        elif pay_method == "Credit Card":
                            st.warning("Credit Card processing is currently offline. Please use GCash/Maya.")
                        
                        if st.button("CONFIRM BOOKING", type="primary", use_container_width=True, key=f"btn_{car['id']}"):
                            if not dest or not p_loc or not r_loc: st.error("Please fill Destination, Pickup Location, and Return Location.")
                            elif pay_method == "GCash / Maya" and not ref_num: st.error("Please enter the GCash/Maya Reference Number.")
                            elif pay_method == "Credit Card": st.error("Please select GCash/Maya to proceed.")
                            else:
                                with st.spinner("Verifying Payment Reference..."):
                                    time.sleep(2)
                                    final_payment_string = f"GCash (Ref: {ref_num})"
                                    
                                    conn.execute("""INSERT INTO bookings 
                                        (vehicle_id, renter_username, amount, status, pickup_loc, return_loc, destination, pickup_time, return_time, payment_method, with_driver) 
                                        VALUES (?, ?, ?, 'CONFIRMED', ?, ?, ?, ?, ?, ?, ?)""", 
                                        (car['id'], renter_user, grand_total, p_loc, r_loc, dest, p_datetime, r_datetime, final_payment_string, is_with_driver))
                                    conn.execute("UPDATE vehicles SET booking_status = 'BOOKED' WHERE id = ?", (car['id'],))
                                    conn.commit()
                                    
                                    st.success("✅ Payment Verified & Booking Confirmed! See 'My Trips' for details.")
                                    time.sleep(2); st.rerun()

with tabs[1]:
    st.subheader("Manage Your Trips")
    try:
        my_trips = pd.read_sql_query("""
            SELECT b.id, v.make, v.model, b.amount, b.status, b.pickup_time, b.return_time, b.pickup_loc, b.return_loc, b.destination, b.with_driver, b.rating, b.review 
            FROM bookings b JOIN vehicles v ON b.vehicle_id = v.id 
            WHERE b.renter_username = ? ORDER BY b.id DESC""", conn, params=(renter_user,))
        
        if my_trips.empty: st.info("You haven't booked any trips yet.")
        else:
            for i, t in my_trips.iterrows():
                with st.expander(f"Booking #DRV-{t['id']:05d} | {t['make']} {t['model']} ({t['status']})"):
                    if t.get('with_driver', 0) == 1: st.markdown("👨‍✈️ *[TRIP INCLUDES PROFESSIONAL DRIVER]*")
                    st.write(f"*Dest:* {t.get('destination', 'N/A')}")
                    st.write(f"*Pickup:* {t.get('pickup_loc', 'N/A')} at {t['pickup_time']}")
                    st.write(f"*Return:* {t.get('return_loc', 'N/A')} at {t['return_time']}")
                    st.write(f"*Total Paid:* ₱{t['amount']:,.2f}")
                    
                    # --- THE FIX: INTERACTIVE CLICKABLE STARS! ---
                    if t['status'] == 'COMPLETED':
                        st.divider()
                        if pd.isnull(t.get('rating')):
                            st.write("### 📣 Rate your experience")
                            
                            # Interactive Star Widget!
                            star_index = st.feedback("stars", key=f"star_fb_{t['id']}")
                            user_review = st.text_input("Leave a short review (optional)", key=f"rev_text_{t['id']}")
                            
                            if st.button("SUBMIT REVIEW", type="primary", key=f"btn_rate_{t['id']}"):
                                if star_index is None:
                                    st.error("Please click the stars to leave a rating!")
                                else:
                                    # st.feedback returns 0-4. We add 1 to make it 1-5 stars.
                                    actual_rating = star_index + 1  
                                    conn.execute("UPDATE bookings SET rating=?, review=? WHERE id=?", (actual_rating, user_review, t['id']))
                                    conn.commit()
                                    st.success("Review submitted! Thank you.")
                                    time.sleep(1); st.rerun()
                        else:
                            stars = int(t['rating'])
                            st.info(f"*You rated this trip:* {'⭐' * stars}")
                            if t.get('review'): st.write(f"{t['review']}")
    except Exception as e:
        st.error(f"Error loading trips: {e}")
