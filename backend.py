import pandas as pd
import hashlib
import os
from datetime import datetime
import re
import uuid
import resend
import streamlit as st   # Required for Streamlit Cloud secrets


class Backend:
    def __init__(self):
        self.USERS_FILE = "users.csv"
        self.BUSINESSES_FILE = "businesses.csv"
        self.BUSINESS_SERVICES_FILE = "business_services.csv"
        self.BOOKINGS_FILE = "bookings.csv"
        self.NOTIFICATIONS_FILE = "notifications.csv"
        self.REVIEWS_FILE = "reviews.csv"
        self.SUBSCRIPTIONS_FILE = "subscriptions.csv"
        self.PAYMENTS_FILE = "payments.csv"

        # Email Configuration - Works on BOTH local and Streamlit Cloud
        self.setup_email_config()

        self.init_db()

    def setup_email_config(self):
        """Handles email configuration for local (.env) and Streamlit Cloud (secrets)"""
        if hasattr(st, "secrets") and "RESEND_API_KEY" in st.secrets:
            # Running on Streamlit Cloud
            resend.api_key = st.secrets["RESEND_API_KEY"]
            self.FROM_EMAIL = st.secrets.get("FROM_EMAIL", "NO-REPLY@LiveLink.app")
            print("✅ Using Streamlit Secrets for email configuration")
        else:
            # Running locally with .env file
            from dotenv import load_dotenv
            load_dotenv()
            resend.api_key = os.getenv("RESEND_API_KEY")
            self.FROM_EMAIL = os.getenv("FROM_EMAIL", "NO-REPLY@LiveLink.app")
            print("✅ Using .env file for email configuration")

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load(self, filename, columns=None):
        if not os.path.exists(filename):
            if columns:
                df = pd.DataFrame(columns=columns)
            else:
                df = pd.DataFrame()
            df.to_csv(filename, index=False)
            return df
        df = pd.read_csv(filename)
        if columns:
            for col in columns:
                if col not in df.columns:
                    df[col] = None
        return df

    def save(self, df, filename):
        df.to_csv(filename, index=False)

    def init_db(self):
        self.load(self.USERS_FILE, ["id", "name", "email", "password", "user_type", "phone"])
        self.load(self.BUSINESSES_FILE, ["id", "name", "category", "address", "phone", "description",
                                         "owner_email", "is_open", "open_time", "close_time"])
        self.load(self.BUSINESS_SERVICES_FILE, ["id", "business_id", "service_name", "price"])
        self.load(self.BOOKINGS_FILE, ["id", "customer_email", "business_id", "business_name", "service_name",
                                       "date", "time", "status", "payment_status", "phone_number",
                                       "delivery_address", "collection_address", "amount", "transaction_id",
                                       "timestamp", "delivery_method"])
        self.load(self.NOTIFICATIONS_FILE, ["id", "business_id", "user_email", "message", "timestamp"])
        self.load(self.REVIEWS_FILE, ["id", "business_id", "user_email", "rating", "review_text", "timestamp"])
        self.load(self.SUBSCRIPTIONS_FILE, ["user_email", "business_id", "timestamp"])
        self.load(self.PAYMENTS_FILE, ["id", "booking_id", "user_email", "business_id", "amount", "status", "transaction_id", "timestamp"])

    # ====================== EMAIL NOTIFICATIONS ======================
    def send_email(self, to_email: str, subject: str, html_body: str):
        try:
            response = resend.Emails.send({
                "from": self.FROM_EMAIL,
                "to": to_email,
                "subject": subject,
                "html": html_body
            })
            print(f"Email sent to {to_email} | ID: {response['id']}")
            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def send_booking_confirmation(self, booking: dict, business_name: str):
        html = f"""
        <h2 style="color:#1f538d;">Your Booking is Confirmed!</h2>
        <p>Dear Customer,</p>
        <p>Thank you for booking with <strong>{business_name}</strong>.</p>
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:20px 0;">
            <strong>Service:</strong> {booking.get('service_name')}<br>
            <strong>Date:</strong> {booking.get('date')}<br>
            <strong>Time:</strong> {booking.get('time')}<br>
            <strong>Amount:</strong> £{float(booking.get('amount', 0)):.2f}<br>
            <strong>Delivery:</strong> {booking.get('delivery_method', 'In-store')}
        </div>
        <p>We look forward to seeing you soon!</p>
        <p>— LiveLink Team</p>
        """
        self.send_email(booking.get('customer_email'), f"Booking Confirmed - {business_name}", html)

    def send_payment_success(self, booking: dict, business_name: str, transaction_id: str):
        html = f"""
        <h2 style="color:#10b981;">Payment Successful!</h2>
        <p>Your payment of <strong>£{float(booking.get('amount', 0)):.2f}</strong> has been received.</p>
        <p><strong>Transaction ID:</strong> {transaction_id}</p>
        <p>Thank you for using LiveLink!</p>
        """
        self.send_email(booking.get('customer_email'), "Payment Confirmed - LiveLink", html)

    def send_new_booking_alert(self, booking: dict, business_email: str):
        html = f"""
        <h3>New Booking Received</h3>
        <p>Customer: {booking.get('customer_email')}</p>
        <p>Service: {booking.get('service_name')}</p>
        <p>Date & Time: {booking.get('date')} at {booking.get('time')}</p>
        <p>Amount: £{float(booking.get('amount', 0)):.2f}</p>
        """
        self.send_email(business_email, "New Booking Alert - LiveLink", html)

    def send_welcome_email(self, user_email: str, name: str, user_type: str):
        html = f"""
        <h2 style="color:#1f538d;">Welcome to LiveLink, {name}!</h2>
        <p>Thank you for joining LiveLink – the easiest way to connect with local businesses.</p>
        <div style="background:#f8f9fa;padding:20px;border-radius:10px;margin:20px 0;">
            <strong>Your Account:</strong><br>
            • Type: {user_type.capitalize()}<br>
            • Email: {user_email}
        </div>
        <p>Start exploring local services, book appointments, and get the best deals near you.</p>
        <p><strong>— The LiveLink Team</strong></p>
        """
        self.send_email(user_email, "Welcome to LiveLink! 🎉", html)

    def send_cancellation_notice(self, booking: dict, business_name: str, cancelled_by: str = "Customer"):
        # To Customer
        html_customer = f"""
        <h2 style="color:#ef4444;">Booking Cancelled</h2>
        <p>Your booking has been cancelled.</p>
        <div style="background:#f8f9fa;padding:15px;border-radius:8px;margin:20px 0;">
            <strong>Business:</strong> {business_name}<br>
            <strong>Service:</strong> {booking.get('service_name')}<br>
            <strong>Date & Time:</strong> {booking.get('date')} at {booking.get('time')}<br>
            <strong>Cancelled by:</strong> {cancelled_by}
        </div>
        <p>If this was a mistake, you can book again anytime.</p>
        """
        self.send_email(booking.get('customer_email'), f"Booking Cancelled - {business_name}", html_customer)

        # To Business Owner
        businesses = self.load(self.BUSINESSES_FILE)
        biz_row = businesses[pd.to_numeric(businesses["id"], errors='coerce') == int(booking.get('business_id', 0))]
        if not biz_row.empty:
            owner_email = biz_row.iloc[0]["owner_email"]
            html_owner = f"""
            <h3>Booking Cancelled</h3>
            <p><strong>Customer:</strong> {booking.get('customer_email')}</p>
            <p><strong>Service:</strong> {booking.get('service_name')}</p>
            <p><strong>Date & Time:</strong> {booking.get('date')} at {booking.get('time')}</p>
            <p><strong>Cancelled by:</strong> {cancelled_by}</p>
            """
            self.send_email(owner_email, f"Booking Cancelled - {business_name}", html_owner)

    # ====================== PAYMENT SYSTEM ======================
    def process_payment(self, amount: float, card_details: dict):
        """Improved realistic test payment processor"""
        card_number = str(card_details.get("card_number", "")).replace(" ", "").replace("-", "")
        expiry = str(card_details.get("expiry", "")).strip()
        cvv = str(card_details.get("cvv", "")).strip()
        name = str(card_details.get("name", "")).strip()

        # Basic validation
        if not card_number or len(card_number) < 13 or len(card_number) > 19:
            return {"status": "fail", "transaction_id": None, "amount": amount,
                    "message": "Invalid card number. Must be 13-19 digits."}

        if not expiry or len(expiry) != 5 or '/' not in expiry:
            return {"status": "fail", "transaction_id": None, "amount": amount,
                    "message": "Invalid expiry date. Use MM/YY format."}

        if not cvv or len(cvv) not in (3, 4):
            return {"status": "fail", "transaction_id": None, "amount": amount,
                    "message": "Invalid CVV. Must be 3 or 4 digits."}

        if not name or len(name.split()) < 2:
            return {"status": "fail", "transaction_id": None, "amount": amount,
                    "message": "Cardholder name is required (First Last)."}

        # Realistic test cards
        test_cards = {
            "4242424242424242": {"status": "success", "message": "Payment approved"},
            "5555555555554444": {"status": "success", "message": "Payment approved (Mastercard)"},
            "4000000000000002": {"status": "fail", "message": "Card declined - Insufficient funds"},
            "4000000000000010": {"status": "fail", "message": "Card declined - Expired card"},
            "4000000000000028": {"status": "fail", "message": "Card declined - Incorrect CVV"},
        }

        result = test_cards.get(card_number,
                               {"status": "fail", "message": "Card not supported. Use a test card from the info box."})

        if result["status"] == "success":
            transaction_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"

            # Save payment record
            payments = self.load(self.PAYMENTS_FILE)
            new_payment = pd.DataFrame([{
                "id": str(uuid.uuid4()),
                "booking_id": card_details.get("booking_id", ""),
                "user_email": card_details.get("user_email", ""),
                "business_id": card_details.get("business_id", ""),
                "amount": float(amount),
                "status": "paid",
                "transaction_id": transaction_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            payments = pd.concat([payments, new_payment], ignore_index=True)
            self.save(payments, self.PAYMENTS_FILE)

            return {
                "status": "success",
                "transaction_id": transaction_id,
                "amount": amount,
                "message": "Payment processed successfully."
            }
        else:
            return {
                "status": "fail",
                "transaction_id": None,
                "amount": amount,
                "message": result["message"]
            }

    def get_time_options(self):
        return [f"{h:02d}:{m:02d}" for h in range(24) for m in range(0, 60, 15)]

    def get_available_times(self, business_id, selected_date):
        all_slots = self.get_time_options()
        businesses = self.load(self.BUSINESSES_FILE)
        biz = businesses[pd.to_numeric(businesses["id"], errors='coerce') == int(business_id)]

        if not biz.empty:
            open_t = str(biz.iloc[0]["open_time"])
            close_t = str(biz.iloc[0]["close_time"])
            all_slots = [t for t in all_slots if open_t <= t <= close_t]

        bookings = self.load(self.BOOKINGS_FILE)
        booked = []
        if not bookings.empty:
            booked = bookings[
                (pd.to_numeric(bookings.get("business_id", 0), errors='coerce') == int(business_id)) &
                (bookings["date"] == selected_date) &
                (bookings["status"].isin(["pending", "confirmed", "accepted"]))
            ]["time"].tolist()

        return [t for t in all_slots if t not in booked]

    def register(self, name, email, password, user_type="customer", **extra):
        users = self.load(self.USERS_FILE)
        email = email.lower().strip()

        if not users.empty and email in users["email"].str.lower().values:
            return False, "Email already registered!"

        hashed = self.hash_password(password)
        user_id = len(users) + 1 if not users.empty else 1

        new_user = pd.DataFrame([{
            "id": user_id,
            "name": name.strip(),
            "email": email,
            "password": hashed,
            "user_type": user_type.lower(),
            "phone": extra.get("phone", "")
        }])

        users = pd.concat([users, new_user], ignore_index=True)
        self.save(users, self.USERS_FILE)

        if user_type.lower() == "business":
            businesses = self.load(self.BUSINESSES_FILE)
            biz_id = len(businesses) + 1 if not businesses.empty else 1

            new_business = pd.DataFrame([{
                "id": biz_id,
                "name": extra.get("business_name", name).strip(),
                "category": extra.get("category", "Other"),
                "address": extra.get("address", ""),
                "phone": extra.get("phone", ""),
                "description": extra.get("description", ""),
                "owner_email": email,
                "is_open": True,
                "open_time": "09:00",
                "close_time": "17:00"
            }])

            businesses = pd.concat([businesses, new_business], ignore_index=True)
            self.save(businesses, self.BUSINESSES_FILE)

        self.send_welcome_email(email, name.strip(), user_type)
        return True, f"Registration successful as {user_type.capitalize()}!"

    def login(self, email, password):
        users = self.load(self.USERS_FILE)
        if users.empty:
            return None
        hashed = self.hash_password(password)
        user = users[(users["email"].str.lower() == email.lower()) & (users["password"] == hashed)]
        return user.iloc[0].to_dict() if not user.empty else None

    def get_business_services(self, business_id):
        services = self.load(self.BUSINESS_SERVICES_FILE)
        if services.empty:
            return pd.DataFrame()
        services["business_id"] = pd.to_numeric(services["business_id"], errors='coerce').fillna(0).astype(int)
        return services[services["business_id"] == int(business_id)]

    def add_business_service(self, business_id, service_name, price):
        services = self.load(self.BUSINESS_SERVICES_FILE)
        service_id = len(services) + 1 if not services.empty else 1
        new_service = pd.DataFrame([{
            "id": service_id,
            "business_id": int(business_id),
            "service_name": service_name.strip(),
            "price": float(price)
        }])
        services = pd.concat([services, new_service], ignore_index=True)
        self.save(services, self.BUSINESS_SERVICES_FILE)
        return True

    def delete_business_service(self, service_id):
        services = self.load(self.BUSINESS_SERVICES_FILE)
        services = services[services["id"] != int(service_id)]
        self.save(services, self.BUSINESS_SERVICES_FILE)

    def get_all_businesses(self):
        businesses = self.load(self.BUSINESSES_FILE)
        if businesses.empty:
            return []
        businesses["id"] = pd.to_numeric(businesses["id"], errors='coerce').fillna(0).astype(int)
        return businesses.to_dict('records')

    def book_appointment(self, user_email, business_id, date_str, time, service_name,
                         delivery_method="In-store", payment_method="Pay on Arrival",
                         customer_phone="", delivery_address="", amount=0.0):

        if customer_phone and not bool(re.match(r'^\+?[\d\s\-\(\)]{10,15}$', str(customer_phone).strip())):
            return False, None, "Invalid phone number"

        bookings = self.load(self.BOOKINGS_FILE)
        conflict = bookings[
            (pd.to_numeric(bookings.get("business_id", 0), errors='coerce') == int(business_id)) &
            (bookings["date"] == date_str) &
            (bookings["time"] == time) &
            (bookings["status"].isin(["pending", "confirmed", "accepted"]))
        ]

        if not conflict.empty:
            return False, None, "Time slot already booked"

        businesses = self.load(self.BUSINESSES_FILE)
        biz = businesses[pd.to_numeric(businesses["id"], errors='coerce') == int(business_id)]
        business_name = biz.iloc[0]["name"] if not biz.empty else "Unknown"
        collection_address = biz.iloc[0]["address"] if not biz.empty else ""

        booking_id = str(uuid.uuid4())

        new_booking = pd.DataFrame([{
            "id": booking_id,
            "customer_email": user_email,
            "business_id": int(business_id),
            "business_name": business_name,
            "service_name": service_name,
            "date": date_str,
            "time": time,
            "status": "pending",
            "payment_status": "unpaid",
            "phone_number": customer_phone,
            "delivery_address": delivery_address if delivery_method == "Delivery" else "",
            "collection_address": collection_address,
            "amount": float(amount),
            "transaction_id": "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "delivery_method": delivery_method,
        }])

        bookings = pd.concat([bookings, new_booking], ignore_index=True)
        self.save(bookings, self.BOOKINGS_FILE)

        self.add_notification(business_id, f"New booking request: {service_name} on {date_str} at {time}")

        booking_dict = new_booking.iloc[0].to_dict()
        self.send_booking_confirmation(booking_dict, business_name)

        owner_email = biz.iloc[0]["owner_email"] if not biz.empty else None
        if owner_email:
            self.send_new_booking_alert(booking_dict, owner_email)

        return True, booking_id, "Booking request submitted (pending approval)"

    def get_user_bookings(self, user_email):
        bookings = self.load(self.BOOKINGS_FILE)
        if bookings.empty:
            return []
        return bookings[bookings["customer_email"] == user_email] \
            .sort_values(by="timestamp", ascending=False).to_dict('records')

    def get_business_bookings(self, business_id):
        bookings = self.load(self.BOOKINGS_FILE)
        if bookings.empty:
            return []
        return bookings[pd.to_numeric(bookings.get("business_id", 0), errors='coerce') == int(business_id)] \
            .sort_values(by="timestamp", ascending=False).to_dict('records')

    def add_notification(self, business_id, message, user_email=None):
        notes = self.load(self.NOTIFICATIONS_FILE)
        new_note = pd.DataFrame([{
            "id": str(uuid.uuid4()),
            "business_id": int(business_id) if business_id else None,
            "user_email": user_email,
            "message": message,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        notes = pd.concat([notes, new_note], ignore_index=True)
        self.save(notes, self.NOTIFICATIONS_FILE)

    def get_notifications(self, business_id=None, user_email=None):
        notes = self.load(self.NOTIFICATIONS_FILE)
        if notes.empty:
            return pd.DataFrame()
        if "user_email" not in notes.columns:
            notes["user_email"] = None

        if business_id is not None:
            return notes[pd.to_numeric(notes.get("business_id", 0), errors='coerce') == int(business_id)] \
                .sort_values(by="timestamp", ascending=False)
        if user_email is not None:
            return notes[notes["user_email"] == user_email].sort_values(by="timestamp", ascending=False)
        return notes.sort_values(by="timestamp", ascending=False)

    def get_business_settings(self, owner_email):
        businesses = self.load(self.BUSINESSES_FILE)
        biz = businesses[businesses["owner_email"] == owner_email]
        if not biz.empty:
            return biz.iloc[0].to_dict()
        return {"is_open": True, "open_time": "09:00", "close_time": "17:00", "description": ""}

    def update_business_settings(self, owner_email, is_open, open_time, close_time, description):
        businesses = self.load(self.BUSINESSES_FILE)
        mask = businesses["owner_email"] == owner_email
        if mask.any():
            businesses.loc[mask, ["is_open", "open_time", "close_time", "description"]] = \
                [bool(is_open), open_time, close_time, description]
            self.save(businesses, self.BUSINESSES_FILE)

    def update_user_email(self, old_email, new_email):
        new_email = new_email.lower().strip()
        users = self.load(self.USERS_FILE)
        if not users.empty:
            users.loc[users["email"] == old_email, "email"] = new_email
            self.save(users, self.USERS_FILE)

        businesses = self.load(self.BUSINESSES_FILE)
        if not businesses.empty:
            businesses.loc[businesses["owner_email"] == old_email, "owner_email"] = new_email
            self.save(businesses, self.BUSINESSES_FILE)

    def subscribe_to_business(self, user_email, business_id):
        subs = self.load(self.SUBSCRIPTIONS_FILE)
        if not subs.empty and ((subs["user_email"] == user_email) & (subs["business_id"] == int(business_id))).any():
            return
        new_sub = pd.DataFrame([{
            "user_email": user_email,
            "business_id": int(business_id),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        }])
        subs = pd.concat([subs, new_sub], ignore_index=True)
        self.save(subs, self.SUBSCRIPTIONS_FILE)

    def unsubscribe_from_business(self, user_email, business_id):
        subs = self.load(self.SUBSCRIPTIONS_FILE)
        subs = subs[~((subs["user_email"] == user_email) & (subs["business_id"] == int(business_id)))]
        self.save(subs, self.SUBSCRIPTIONS_FILE)

    def get_user_subscriptions(self, user_email):
        subs = self.load(self.SUBSCRIPTIONS_FILE)
        if subs.empty:
            return []
        return subs[subs["user_email"] == user_email].to_dict('records')

    def get_average_rating(self, business_id):
        reviews = self.load(self.REVIEWS_FILE)
        if reviews.empty:
            return 0.0
        biz_reviews = reviews[pd.to_numeric(reviews.get("business_id", 0), errors='coerce') == int(business_id)]
        return round(biz_reviews["rating"].mean(), 1) if not biz_reviews.empty else 0.0



backend = Backend()
