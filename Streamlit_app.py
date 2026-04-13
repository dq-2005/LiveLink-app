import streamlit as st
import pandas as pd
from datetime import datetime, date
import time
import re
from backend import backend

st.set_page_config(page_title="LiveLink", page_icon="🔗", layout="wide")

# ====================== SESSION STATE ======================
if "current_user" not in st.session_state:
    st.session_state.current_user = None
    st.session_state.current_user_type = None
    st.session_state.selected_business = None
    st.session_state.current_booking_price = 0.0
    st.session_state.selected_booking_id = None
    st.session_state.show_payment = False


def get_current_business_id():
    if st.session_state.current_user_type != "business":
        return None
    businesses = backend.load(backend.BUSINESSES_FILE)
    biz = businesses[businesses["owner_email"] == st.session_state.current_user["email"]]
    return int(biz.iloc[0]["id"]) if not biz.empty else None


# ====================== SIDEBAR NAVIGATION ======================
st.sidebar.title("LiveLink")

if st.session_state.current_user:
    st.sidebar.success(f"👤 {st.session_state.current_user.get('name', 'User')}")

    if st.session_state.current_user_type == "customer":
        page = st.sidebar.radio("Menu",
                                ["Home", "Discover Businesses", "My Bookings", "My Subscriptions", "Profile"])
    else:
        page = st.sidebar.radio("Menu",
                                ["Home", "Dashboard", "Manage Bookings", "Manage Services", "Profile", "Notifications",
                                 "Business Settings"])

    if st.sidebar.button("Logout"):
        st.session_state.current_user = None
        st.session_state.current_user_type = None
        st.rerun()
else:
    page = "Login"


# ====================== LOGIN / REGISTER ======================
if not st.session_state.current_user:
    st.title("LiveLink")
    st.subheader("Connecting Customers & Local Businesses")

    tab1, tab2 = st.tabs(["Login", "Create New Account"])

    with tab1:
        st.subheader("Welcome Back")
        email = st.text_input("Email Address", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", type="primary"):
            if email and password:
                user = backend.login(email, password)
                if user:
                    st.session_state.current_user = user
                    st.session_state.current_user_type = user.get("user_type", "customer")
                    st.success(f"Welcome back, {user.get('name', 'User')}!")
                    st.rerun()
                else:
                    st.error("Invalid email or password")
            else:
                st.warning("Email and Password are required")

    with tab2:
        st.subheader("Create New Account")
        user_type = st.radio("Select Account Type", ["Customer", "Business Owner"], horizontal=True)
        name = st.text_input("Full Name")
        email = st.text_input("Email Address", key="reg_email")
        password = st.text_input("Create Password", type="password", key="reg_password")

        extra = {}
        if user_type == "Business Owner":
            extra["business_name"] = st.text_input("Business Name")
            extra["category"] = st.selectbox("Type of Business",
                                             ["Cafe", "Restaurant", "Salon", "Gym", "Retail", "Services", "Other",
                                              "Custom"])
            extra["address"] = st.text_input("Business Address")
            extra["phone"] = st.text_input("Business Phone Number")

        if st.button("Create Account", type="primary"):
            ut = "business" if user_type == "Business Owner" else "customer"
            if name and email and password:
                success, msg = backend.register(name, email, password, ut, **extra)
                if success:
                    st.success(msg)
                    st.info("You can now login.")
                else:
                    st.error(msg)
            else:
                st.warning("All fields are required")


# ====================== CUSTOMER PAGES ======================
else:
    if st.session_state.current_user_type == "customer":
        if page == "Home":
            st.header(f"Welcome back, {st.session_state.current_user.get('name', 'User')}!")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Discover Local Businesses", use_container_width=True):
                    st.session_state.selected_business = None
                    st.rerun()
            with col2:
                if st.button("View My Bookings", use_container_width=True):
                    st.rerun()

        elif page == "Discover Businesses":
            st.header("Discover Local Businesses")
            search = st.text_input("Search by name or category...", placeholder="Cafe, Salon, Gym...")

            all_businesses = backend.get_all_businesses()
            filtered = [b for b in all_businesses if not search or
                        search.lower() in b.get("name", "").lower() or
                        search.lower() in b.get("category", "").lower()]

            for biz in filtered:
                with st.container(border=True):
                    st.subheader(biz["name"])
                    st.write(f"{biz.get('category')} • {biz.get('address')}")
                    st.write(f"⏰ {biz.get('open_time', 'N/A')} - {biz.get('close_time', 'N/A')}")
                    st.caption(f"Rating: {backend.get_average_rating(biz['id'])}/5")

                    services_df = backend.get_business_services(biz["id"])
                    if not services_df.empty:
                        for _, s in services_df.iterrows():
                            st.write(f"• {s['service_name']} — £{float(s['price']):.2f}")

                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("View & Book", key=f"view_{biz['id']}"):
                            st.session_state.selected_business = biz
                            st.rerun()
                    with col2:
                        if st.button("Subscribe", key=f"sub_{biz['id']}"):
                            backend.subscribe_to_business(st.session_state.current_user["email"], biz["id"])
                            st.success("Subscribed successfully!")
                            st.rerun()

        # ====================== BUSINESS DETAIL & BOOKING PAGE ======================
        elif st.session_state.selected_business:
            biz = st.session_state.selected_business
            st.header(biz["name"])
            st.write(f"📍 {biz.get('address', 'N/A')}")
            st.write(f"⏰ {biz.get('open_time', 'N/A')} – {biz.get('close_time', 'N/A')}")
            st.write(f"Rating: {backend.get_average_rating(biz['id'])}/5")

            services_df = backend.get_business_services(biz["id"])
            service_list = ["Select Service"] + list(services_df["service_name"]) if not services_df.empty else [
                "Select Service"]

            service_name = st.selectbox("Available Services", service_list)
            if service_name != "Select Service":
                row = services_df[services_df["service_name"] == service_name]
                if not row.empty:
                    st.session_state.current_booking_price = float(row.iloc[0]["price"])
                    st.success(f"Price: £{st.session_state.current_booking_price:.2f}")

            selected_date = st.date_input("Select Date", value=date.today(), min_value=date.today())
            available_times = backend.get_available_times(biz["id"], selected_date.strftime("%Y-%m-%d"))
            time_slot = st.selectbox("Available Time Slots",
                                     available_times if available_times else ["No slots available today"])

            delivery = st.selectbox("Service Type", ["In-store", "Collection", "Delivery", "Home visit"])
            phone = st.text_input("Phone Number (required)", placeholder="07123 456 789")
            delivery_addr = st.text_input("Delivery Address (only if Delivery)") if delivery == "Delivery" else ""
            payment_method = st.selectbox("Payment Option", ["Pay on Arrival", "Pay Now (on app)"])

            if st.button("Confirm Booking", type="primary"):
                if service_name == "Select Service" or time_slot in ["No slots available today"] or not phone:
                    st.error("Please fill all required fields")
                else:
                    success, booking_id, msg = backend.book_appointment(
                        st.session_state.current_user["email"], biz["id"],
                        selected_date.strftime("%Y-%m-%d"), time_slot, service_name,
                        delivery, payment_method, phone, delivery_addr, st.session_state.current_booking_price
                    )
                    if success:
                        st.success(msg)
                        st.session_state.selected_booking_id = booking_id
                        if payment_method == "Pay Now (on app)":
                            st.session_state.show_payment = True
                        else:
                            st.rerun()
                    else:
                        st.error(msg)

            # ====================== IMPROVED PAYMENT SCREEN ======================
            if st.session_state.get("show_payment", False):
                st.subheader("🔒 Secure Payment")
                amount = st.session_state.current_booking_price
                biz = st.session_state.selected_business

                st.write(f"**Paying £{amount:.2f}** to **{biz['name']}**")
                st.info("""
                **Test Mode** — Use these cards:\n
                • **4242 4242 4242 4242** → Success\n
                • **5555 5555 5555 4444** → Success (Mastercard)\n
                • **4000 0000 0000 0002** → Declined (Insufficient funds)\n
                • **4000 0000 0000 0010** → Declined (Expired card)
                """)

                with st.form("payment_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        card_number = st.text_input("Card Number", placeholder="4242 4242 4242 4242", max_chars=19)
                    with col2:
                        card_name = st.text_input("Cardholder Name", placeholder="John Doe")

                    col3, col4 = st.columns(2)
                    with col3:
                        expiry = st.text_input("Expiry Date (MM/YY)", placeholder="12/28", max_chars=5)
                    with col4:
                        cvv = st.text_input("CVV", placeholder="123", type="password", max_chars=4)

                    st.caption("Your payment information is secure and encrypted.")

                    if st.form_submit_button(f"Pay Now £{amount:.2f}", type="primary"):
                        if not card_number or not expiry or not cvv or not card_name:
                            st.error("Please fill in all card details")
                        else:
                            with st.spinner("Processing secure payment..."):
                                time.sleep(1.8)  # realistic delay

                                card_details = {
                                    "card_number": card_number,
                                    "expiry": expiry,
                                    "cvv": cvv,
                                    "name": card_name,
                                    "booking_id": st.session_state.selected_booking_id,
                                    "user_email": st.session_state.current_user["email"],
                                    "business_id": biz["id"]
                                }

                                result = backend.process_payment(amount, card_details)

                            if result["status"] == "success":
                                # Update booking
                                bookings_df = backend.load(backend.BOOKINGS_FILE)
                                mask = bookings_df["id"] == st.session_state.selected_booking_id
                                if mask.any():
                                    bookings_df.loc[mask, "payment_status"] = "paid"
                                    bookings_df.loc[mask, "transaction_id"] = result["transaction_id"]
                                    backend.save(bookings_df, backend.BOOKINGS_FILE)

                                updated_booking = bookings_df[mask].iloc[0].to_dict()
                                business_name = biz["name"]

                                backend.send_payment_success(updated_booking, business_name, result["transaction_id"])
                                backend.send_booking_confirmation(updated_booking, business_name)

                                st.success("✅ Payment Successful!")
                                st.balloons()

                                receipt_text = f"""====================================
LIVELINK RECEIPT
====================================
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Business: {biz['name']}
Service: {service_name}
Date & Time: {selected_date} at {time_slot}
Delivery Method: {delivery}
Payment Status: PAID
Transaction ID: {result['transaction_id']}
Amount Paid: £{amount:.2f}
Phone: {phone}
Delivery Address: {delivery_addr if delivery == "Delivery" else "N/A"}
Thank you for using LiveLink!
===================================="""

                                st.download_button(
                                    label="📥 Download Receipt",
                                    data=receipt_text,
                                    file_name=f"receipt_{st.session_state.selected_booking_id[:8]}.txt",
                                    mime="text/plain"
                                )

                                st.session_state.show_payment = False
                                st.rerun()

                            else:
                                st.error(f"❌ Payment Failed: {result.get('message', 'Unknown error')}")

        elif page == "My Bookings":
            st.header("My Bookings")
            bookings = backend.get_user_bookings(st.session_state.current_user["email"])
            if not bookings:
                st.info("No bookings yet.\nGo to Discover to book services!")
            else:
                for b in bookings:
                    with st.container(border=True):
                        st.subheader(f"{b.get('business_name', 'N/A')} — {b.get('service_name', 'N/A')}")
                        st.write(f"{b['date']} at {b['time']}")
                        st.write(f"Delivery: {b.get('delivery_method', 'N/A')} | Status: {b['status'].capitalize()}")
                        st.write(f"Payment: {b.get('payment_status', 'unpaid').upper()}")

                        if st.button("Download Receipt", key=f"rec_{b['id']}"):
                            receipt_text = f"""LIVELINK RECEIPT
Business: {b.get('business_name')}
Service: {b.get('service_name')}
Date & Time: {b.get('date')} at {b.get('time')}
Amount: £{b.get('amount', 0):.2f}
Payment: {b.get('payment_status', 'unpaid').upper()}
Thank you!"""
                            st.download_button("Download", receipt_text, f"receipt_{b['id'][:8]}.txt",
                                               mime="text/plain")

                        if b['status'] in ["pending", "confirmed", "accepted"]:
                            if st.button("Cancel Booking", key=f"cancel_{b['id']}"):
                                df = backend.load(backend.BOOKINGS_FILE)
                                mask = df["id"] == b['id']
                                if mask.any():
                                    booking = df[mask].iloc[0].to_dict()
                                    df.loc[mask, "status"] = "cancelled"
                                    backend.save(df, backend.BOOKINGS_FILE)

                                    businesses = backend.load(backend.BUSINESSES_FILE)
                                    biz_row = businesses[pd.to_numeric(businesses["id"]) == booking.get("business_id")]
                                    business_name = biz_row.iloc[0]["name"] if not biz_row.empty else "Business"

                                    backend.send_cancellation_notice(booking, business_name, "Customer")

                                    st.success("Booking cancelled successfully. Notifications sent.")
                                    st.rerun()

        elif page == "My Subscriptions":
            st.header("My Subscriptions")
            subs = backend.get_user_subscriptions(st.session_state.current_user["email"])
            if not subs:
                st.info("You haven't subscribed to any businesses yet.")
            else:
                businesses = backend.load(backend.BUSINESSES_FILE)
                for sub in subs:
                    biz_row = businesses[businesses["id"] == sub["business_id"]]
                    if not biz_row.empty:
                        biz = biz_row.iloc[0].to_dict()
                        st.subheader(biz["name"])
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("View Business", key=f"vsub_{biz['id']}"):
                                st.session_state.selected_business = biz
                                st.rerun()
                        with col2:
                            if st.button("Unsubscribe", key=f"unsub_{biz['id']}"):
                                backend.unsubscribe_from_business(st.session_state.current_user["email"], biz["id"])
                                st.success("Unsubscribed")
                                st.rerun()

        elif page == "Profile":
            st.header("My Profile")
            name = st.text_input("Full Name", value=st.session_state.current_user.get("name", ""))
            email = st.text_input("Email Address", value=st.session_state.current_user.get("email", ""))

            if st.session_state.current_user_type == "business":
                businesses = backend.load(backend.BUSINESSES_FILE)
                biz_row = businesses[businesses["owner_email"] == st.session_state.current_user.get("email")]
                current_biz = biz_row.iloc[0].to_dict() if not biz_row.empty else {}
                business_name = st.text_input("Business Name", value=current_biz.get("name", ""))
                category = st.text_input("Category", value=current_biz.get("category", ""))
                address = st.text_input("Business Address", value=current_biz.get("address", ""))
                phone = st.text_input("Phone Number", value=current_biz.get("phone", ""))

            if st.button("Save Changes", type="primary"):
                if name and email:
                    old_email = st.session_state.current_user["email"]
                    backend.update_user_email(old_email, email)

                    users = backend.load(backend.USERS_FILE)
                    users.loc[users["email"] == email, "name"] = name
                    backend.save(users, backend.USERS_FILE)

                    st.session_state.current_user["name"] = name
                    st.session_state.current_user["email"] = email

                    if st.session_state.current_user_type == "business":
                        businesses = backend.load(backend.BUSINESSES_FILE)
                        mask = businesses["owner_email"] == email
                        if mask.any():
                            businesses.loc[mask, ["name", "category", "address", "phone"]] = [business_name, category,
                                                                                              address, phone]
                            if old_email != email:
                                businesses.loc[mask, "owner_email"] = email
                            backend.save(businesses, backend.BUSINESSES_FILE)

                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Name and Email cannot be empty")

    # ====================== BUSINESS OWNER PAGES ======================
    else:
        if page == "Home" or page == "Dashboard":
            st.header("Business Dashboard")
            biz_id = get_current_business_id()
            if biz_id:
                bookings_df = backend.load(backend.BOOKINGS_FILE)
                biz_bookings = bookings_df[pd.to_numeric(bookings_df.get("business_id", pd.Series()),
                                                         errors='coerce') == biz_id] if not bookings_df.empty else pd.DataFrame()

                today = datetime.now().strftime("%Y-%m-%d")
                todays_bookings = len(biz_bookings[biz_bookings["date"] == today]) if not biz_bookings.empty else 0
                upcoming_bookings = len(biz_bookings[biz_bookings["date"] > today]) if not biz_bookings.empty else 0
                earnings = biz_bookings[biz_bookings.get("payment_status") == "paid"]["amount"].sum() \
                    if not biz_bookings.empty and "amount" in biz_bookings.columns else 0.0
                services_count = len(backend.get_business_services(biz_id))

                st.metric("Today's Bookings", todays_bookings)
                st.metric("Upcoming Bookings", upcoming_bookings)
                st.metric("Services Offered", services_count)
                st.metric("Total Earnings This Month", f"£{earnings:.2f}")

        elif page == "Manage Bookings":
            st.header("Manage Bookings")
            biz_id = get_current_business_id()
            if biz_id:
                bookings = backend.get_business_bookings(biz_id)
                for b in bookings:
                    with st.container(border=True):
                        st.write(f"Customer: {b.get('customer_email')} | {b.get('service_name')} on {b['date']} at {b['time']}")
                        if b['status'] == "pending":
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("Accept", key=f"acc_{b['id']}"):
                                    df = backend.load(backend.BOOKINGS_FILE)
                                    df.loc[df["id"] == b['id'], "status"] = "accepted"
                                    backend.save(df, backend.BOOKINGS_FILE)
                                    st.success("Accepted")
                                    st.rerun()
                            with col2:
                                if st.button("Decline", key=f"dec_{b['id']}"):
                                    df = backend.load(backend.BOOKINGS_FILE)
                                    df.loc[df["id"] == b['id'], "status"] = "declined"
                                    backend.save(df, backend.BOOKINGS_FILE)
                                    st.success("Declined")
                                    st.rerun()

        elif page == "Manage Services":
            st.header("Manage Services & Prices")
            biz_id = get_current_business_id()
            if biz_id:
                with st.form("add_service_form"):
                    name = st.text_input("Service Name")
                    price = st.number_input("Price (£)", min_value=0.0, step=0.5)
                    if st.form_submit_button("Add Service"):
                        if name:
                            backend.add_business_service(biz_id, name, price)
                            st.success(f"'{name}' added successfully!")
                            st.rerun()

                services_df = backend.get_business_services(biz_id)
                if services_df.empty:
                    st.info("No services added yet.")
                else:
                    for _, s in services_df.iterrows():
                        col1, col2 = st.columns([4, 1])
                        with col1:
                            st.write(f"{s['service_name']} — £{float(s['price']):.2f}")
                        with col2:
                            if st.button("Delete", key=f"del_{s['id']}"):
                                backend.delete_business_service(s['id'])
                                st.success("Service deleted")
                                st.rerun()

        elif page == "Profile":
            # Same profile code as before (unchanged)
            st.header("My Profile")
            name = st.text_input("Full Name", value=st.session_state.current_user.get("name", ""))
            email = st.text_input("Email Address", value=st.session_state.current_user.get("email", ""))

            if st.session_state.current_user_type == "business":
                businesses = backend.load(backend.BUSINESSES_FILE)
                biz_row = businesses[businesses["owner_email"] == st.session_state.current_user.get("email")]
                current_biz = biz_row.iloc[0].to_dict() if not biz_row.empty else {}
                business_name = st.text_input("Business Name", value=current_biz.get("name", ""))
                category = st.text_input("Category", value=current_biz.get("category", ""))
                address = st.text_input("Business Address", value=current_biz.get("address", ""))
                phone = st.text_input("Phone Number", value=current_biz.get("phone", ""))

            if st.button("Save Changes", type="primary"):
                if name and email:
                    old_email = st.session_state.current_user["email"]
                    backend.update_user_email(old_email, email)

                    users = backend.load(backend.USERS_FILE)
                    users.loc[users["email"] == email, "name"] = name
                    backend.save(users, backend.USERS_FILE)

                    st.session_state.current_user["name"] = name
                    st.session_state.current_user["email"] = email

                    if st.session_state.current_user_type == "business":
                        businesses = backend.load(backend.BUSINESSES_FILE)
                        mask = businesses["owner_email"] == email
                        if mask.any():
                            businesses.loc[mask, ["name", "category", "address", "phone"]] = [business_name, category,
                                                                                              address, phone]
                            if old_email != email:
                                businesses.loc[mask, "owner_email"] = email
                            backend.save(businesses, backend.BUSINESSES_FILE)

                    st.success("Profile updated successfully!")
                    st.rerun()
                else:
                    st.error("Name and Email cannot be empty")

        elif page == "Notifications":
            st.header("Notifications")
            biz_id = get_current_business_id()
            notes = backend.get_notifications(business_id=biz_id) if biz_id else pd.DataFrame()
            if notes.empty:
                st.info("No notifications yet.")
            else:
                for _, note in notes.iterrows():
                    st.write(note["message"])
                    st.caption(note["timestamp"])

        elif page == "Business Settings":
            st.header("Business Settings")
            settings = backend.get_business_settings(st.session_state.current_user["email"])

            is_open = st.toggle("Business is currently Open", value=settings.get("is_open", True))
            open_time = st.selectbox("Opening Time (24-hour)", backend.get_time_options(),
                                     index=backend.get_time_options().index(settings.get("open_time", "09:00")))
            close_time = st.selectbox("Closing Time (24-hour)", backend.get_time_options(),
                                      index=backend.get_time_options().index(settings.get("close_time", "17:00")))
            description = st.text_area("Brief Business Description", value=settings.get("description", ""))

            if st.button("Save Settings"):
                backend.update_business_settings(st.session_state.current_user["email"], is_open, open_time, close_time,
                                                 description)
                st.success("Business settings updated successfully!")
                st.rerun()

st.caption("LiveLink - Streamlit Version")