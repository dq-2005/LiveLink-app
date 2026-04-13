import customtkinter as ctk
from tkinter import messagebox
import pandas as pd
from datetime import datetime
import random
import re
import os
from tkcalendar import Calendar
from backend import backend

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

current_user = None
current_user_type = None


class LiveLinkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("LiveLink - Connect with Local Businesses")
        self.geometry("1220x820")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        backend.add_sample_data()

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.current_booking_price = 0.0
        self.selected_business_id = None
        self.selected_booking_id = None

        self.show_login_register_screen()

    def on_closing(self):
        if messagebox.askokcancel("Exit LiveLink", "Are you sure you want to quit?"):
            self.destroy()

    def toggle_mode(self):
        mode = ctk.get_appearance_mode()
        ctk.set_appearance_mode("Light" if mode == "Dark" else "Dark")

    # NAVIGATION BAR
    def create_navbar(self):
        nav = ctk.CTkFrame(self.main_frame, height=65, fg_color="#1f1f1f")
        nav.pack(fill="x", pady=(0, 15))
        nav.pack_propagate(False)

        ctk.CTkLabel(nav, text=" LiveLink", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left", padx=25)
        ctk.CTkButton(nav, text=" Home", width=110, height=40, command=self.show_main_dashboard).pack(side="left",
                                                                                                      padx=6)

        if current_user_type == "customer":
            ctk.CTkButton(nav, text=" Discover", width=120, height=40, command=self.show_discover_businesses).pack(
                side="left", padx=6)
            ctk.CTkButton(nav, text=" My Bookings", width=140, height=40, command=self.show_my_bookings).pack(
                side="left", padx=6)
            ctk.CTkButton(nav, text="️ My Subscriptions", width=160, height=40,
                          command=self.show_my_subscriptions).pack(side="left", padx=6)
        else:
            ctk.CTkButton(nav, text=" Dashboard", width=140, height=40, command=self.show_business_dashboard).pack(
                side="left", padx=6)
            ctk.CTkButton(nav, text=" Manage Bookings", width=160, height=40, command=self.show_business_bookings).pack(
                side="left", padx=6)
            ctk.CTkButton(nav, text=" Services", width=130, height=40, command=self.show_manage_services).pack(
                side="left", padx=6)
            ctk.CTkButton(nav, text=" Profile", width=110, height=40, command=self.show_profile).pack(side="left",
                                                                                                      padx=6)
            ctk.CTkButton(nav, text=" Notifications", width=140, height=40, command=self.show_notifications).pack(
                side="left", padx=6)

        ctk.CTkSwitch(nav, text=" Mode", command=self.toggle_mode).pack(side="right", padx=20)

    # LOGIN / REGISTER PAGES
    def show_login_register_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(expand=True, pady=40)

        ctk.CTkLabel(frame, text=" LiveLink", font=ctk.CTkFont(size=42, weight="bold")).pack(pady=20)
        ctk.CTkLabel(frame, text="Connecting Customers & Local Businesses", font=ctk.CTkFont(size=18)).pack(pady=10)

        ctk.CTkButton(frame, text=" Login", width=340, height=55, font=ctk.CTkFont(size=16),
                      command=self.show_login_screen).pack(pady=25)
        ctk.CTkButton(frame, text=" Create New Account", width=340, height=55, font=ctk.CTkFont(size=16),
                      command=self.show_register_screen).pack(pady=10)

        mode_switch = ctk.CTkSwitch(frame, text="Dark / Light Mode", command=self.toggle_mode)
        mode_switch.pack(pady=50)
        if ctk.get_appearance_mode() == "Dark":
            mode_switch.select()

    def show_login_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(expand=True, pady=60)

        ctk.CTkLabel(frame, text="Welcome Back", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=30)

        self.email_entry = ctk.CTkEntry(frame, placeholder_text="Email Address", width=400, height=50)
        self.email_entry.pack(pady=12)
        self.password_entry = ctk.CTkEntry(frame, placeholder_text="Password", show="*", width=400, height=50)
        self.password_entry.pack(pady=12)

        ctk.CTkButton(frame, text="Login", width=400, height=55, command=self.handle_login).pack(pady=30)
        ctk.CTkButton(frame, text="Back", width=400, height=40, fg_color="transparent",
                      command=self.show_login_register_screen).pack()

    def handle_login(self):
        global current_user, current_user_type
        email = self.email_entry.get().strip()
        password = self.password_entry.get().strip()

        if not email or not password:
            messagebox.showwarning("Warning", "Email and Password are required")
            return

        user = backend.login(email, password)
        if user:
            current_user = user
            current_user_type = user.get("user_type", "customer")
            messagebox.showinfo("Success", f"Welcome back, {user.get('name', 'User')}!")
            self.show_main_dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid email or password")

    def show_register_screen(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        main_frame = ctk.CTkFrame(self.main_frame)
        main_frame.pack(expand=True, pady=20, fill="both")

        ctk.CTkLabel(main_frame, text="Create New Account", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)
        ctk.CTkLabel(main_frame, text="Select Account Type", font=ctk.CTkFont(size=18, weight="bold")).pack(
            pady=(10, 8))

        self.user_type_var = ctk.StringVar(value="customer")
        self.type_segment = ctk.CTkSegmentedButton(main_frame, values=["Customer", "Business Owner"],
                                                   variable=self.user_type_var, command=self.update_register_form)
        self.type_segment.pack(pady=12)

        self.register_scroll = ctk.CTkScrollableFrame(main_frame)
        self.register_scroll.pack(fill="both", expand=True, pady=10, padx=60)
        self.update_register_form()

    def update_register_form(self, *args):
        for widget in self.register_scroll.winfo_children():
            widget.destroy()

        self.reg_name = ctk.CTkEntry(self.register_scroll, placeholder_text="Full Name", width=420)
        self.reg_name.pack(pady=10)
        self.reg_email = ctk.CTkEntry(self.register_scroll, placeholder_text="Email Address", width=420)
        self.reg_email.pack(pady=10)
        self.reg_password = ctk.CTkEntry(self.register_scroll, placeholder_text="Create Password", show="*", width=420)
        self.reg_password.pack(pady=10)

        if self.user_type_var.get() == "Business Owner":
            self.reg_business_name = ctk.CTkEntry(self.register_scroll, placeholder_text="Business Name", width=420)
            self.reg_business_name.pack(pady=10)

            ctk.CTkLabel(self.register_scroll, text="Type of Business (Category - custom title allowed)",
                         font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15, 5))
            self.category_var = ctk.StringVar(value="Cafe")
            cats = ["Cafe", "Restaurant", "Salon", "Gym", "Retail", "Services", "Other", "Custom"]
            ctk.CTkOptionMenu(self.register_scroll, values=cats, variable=self.category_var, width=420).pack(pady=8)

            self.reg_address = ctk.CTkEntry(self.register_scroll, placeholder_text="Business Address", width=420)
            self.reg_address.pack(pady=10)
            self.reg_phone = ctk.CTkEntry(self.register_scroll, placeholder_text="Business Phone Number", width=420)
            self.reg_phone.pack(pady=10)

        ctk.CTkButton(self.register_scroll, text="Create Account", height=50, command=self.handle_register).pack(
            pady=25)
        ctk.CTkButton(self.register_scroll, text="Back", fg_color="transparent",
                      command=self.show_login_register_screen).pack(pady=5)

    def handle_register(self):
        name = self.reg_name.get().strip()
        email = self.reg_email.get().strip()
        password = self.reg_password.get().strip()
        user_type = "business" if self.user_type_var.get() == "Business Owner" else "customer"

        if not name or not email or not password:
            messagebox.showwarning("Missing Information", "All fields are required")
            return

        extra = {}
        if user_type == "business":
            if not hasattr(self, 'reg_business_name') or not self.reg_business_name.get().strip():
                messagebox.showwarning("Missing Information", "Business Name is required")
                return
            extra = {
                "business_name": self.reg_business_name.get().strip(),
                "category": self.category_var.get() if hasattr(self, 'category_var') else "Other",
                "address": self.reg_address.get().strip() if hasattr(self, 'reg_address') else "",
                "phone": self.reg_phone.get().strip() if hasattr(self, 'reg_phone') else ""
            }

        success, msg = backend.register(name, email, password, user_type, **extra)
        if success:
            messagebox.showinfo("Account Created", msg)
            self.show_login_register_screen()
        else:
            messagebox.showerror("Registration Failed", msg)

    #Main Dashboard
    def show_main_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        content = ctk.CTkFrame(self.main_frame)
        content.pack(fill="both", expand=True, padx=40, pady=30)

        ctk.CTkLabel(content, text=f"Welcome back, {current_user.get('name', 'User')}!",
                     font=ctk.CTkFont(size=28, weight="bold")).pack(pady=40)

        if current_user_type == "customer":
            ctk.CTkButton(content, text=" Discover Local Businesses", width=420, height=60,
                          font=ctk.CTkFont(size=16), command=self.show_discover_businesses).pack(pady=15)
            ctk.CTkButton(content, text=" View My Bookings", width=420, height=60,
                          font=ctk.CTkFont(size=16), command=self.show_my_bookings).pack(pady=10)
        else:
            ctk.CTkButton(content, text=" Manage My Services", width=420, height=60,
                          font=ctk.CTkFont(size=16), command=self.show_manage_services).pack(pady=15)
            ctk.CTkButton(content, text=" Business Settings", width=420, height=60,
                          font=ctk.CTkFont(size=16), command=self.show_business_settings).pack(pady=10)

        ctk.CTkButton(content, text="Logout", width=300, height=50, fg_color="#c42b1c",
                      command=self.logout).pack(pady=40)

    #Business Dashboard
    def show_business_dashboard(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        content = ctk.CTkFrame(self.main_frame)
        content.pack(fill="both", expand=True, padx=40, pady=30)

        ctk.CTkLabel(content, text=" Business Dashboard", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)

        biz_id = self.get_current_business_id()
        if not biz_id:
            ctk.CTkLabel(content, text="No business profile found.").pack(pady=100)
            return

        bookings_df = backend.load(backend.BOOKINGS_FILE)
        biz_bookings = bookings_df[
            pd.to_numeric(bookings_df.get("business_id", pd.Series()), errors='coerce') == biz_id] \
            if not bookings_df.empty else pd.DataFrame()

        today = datetime.now().strftime("%Y-%m-%d")
        todays_bookings = len(biz_bookings[biz_bookings["date"] == today]) if not biz_bookings.empty else 0
        upcoming_bookings = len(biz_bookings[biz_bookings["date"] > today]) if not biz_bookings.empty else 0
        earnings = biz_bookings[biz_bookings.get("payment_status") == "paid"]["amount"].sum() \
            if not biz_bookings.empty and "amount" in biz_bookings.columns else 0.0
        services_count = len(backend.get_business_services(biz_id))

        ctk.CTkLabel(content, text=f"Today's Bookings: {todays_bookings}", font=ctk.CTkFont(size=18)).pack(pady=10)
        ctk.CTkLabel(content, text=f"Upcoming Bookings: {upcoming_bookings}", font=ctk.CTkFont(size=18)).pack(pady=10)
        ctk.CTkLabel(content, text=f"Services Offered: {services_count}", font=ctk.CTkFont(size=18)).pack(pady=10)
        ctk.CTkLabel(content, text=f"Total Earnings This Month: £{earnings:.2f}", font=ctk.CTkFont(size=18)).pack(
            pady=10)

        ctk.CTkButton(content, text="View All Bookings", width=300, height=50,
                      command=self.show_business_bookings).pack(pady=20)
        ctk.CTkButton(content, text="Manage Services", width=300, height=50, command=self.show_manage_services).pack(
            pady=10)

    # Dscover, payment details etc
    def show_discover_businesses(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text=" Discover Local Businesses",
                     font=ctk.CTkFont(size=26, weight="bold")).pack(pady=10)

        search_frame = ctk.CTkFrame(self.main_frame)
        search_frame.pack(fill="x", padx=40, pady=10)

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search by name or category...", width=500)
        self.search_entry.pack(side="left", padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.refresh_discover)

        ctk.CTkButton(search_frame, text="Search", width=120, command=self.refresh_discover).pack(side="left", padx=10)

        self.discover_scroll = ctk.CTkScrollableFrame(self.main_frame)
        self.discover_scroll.pack(fill="both", expand=True, padx=30, pady=10)

        self.refresh_discover()

    def refresh_discover(self, event=None):
        for widget in self.discover_scroll.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip().lower() if hasattr(self, 'search_entry') else ""

        all_businesses = backend.get_all_businesses()

        if query:
            filtered = [biz for biz in all_businesses
                        if query in biz.get("name", "").lower() or query in biz.get("category", "").lower()]
        else:
            filtered = all_businesses

        if not filtered:
            ctk.CTkLabel(self.discover_scroll, text="No businesses found.").pack(pady=100)
            return

        for biz in filtered:
            card = ctk.CTkFrame(self.discover_scroll, corner_radius=12)
            card.pack(fill="x", pady=12, padx=10)

            ctk.CTkLabel(card, text=biz["name"], font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20,
                                                                                                pady=(15, 5))
            ctk.CTkLabel(card, text=f"{biz.get('category')} • {biz.get('address')}").pack(anchor="w", padx=20)
            ctk.CTkLabel(card, text=f" {biz.get('open_time', 'N/A')} - {biz.get('close_time', 'N/A')}",
                         text_color="lightblue").pack(anchor="w", padx=20, pady=2)

            services_df = backend.get_business_services(biz["id"])
            if not services_df.empty:
                for _, s in services_df.iterrows():
                    ctk.CTkLabel(card, text=f"• {s['service_name']} — £{float(s['price']):.2f}",
                                 font=ctk.CTkFont(size=13)).pack(anchor="w", padx=40)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=20, pady=12)
            ctk.CTkButton(btn_frame, text="View & Book", width=140, height=40,
                          command=lambda b=biz: self.show_business_detail(b)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Subscribe", fg_color="#1f538d", width=120, height=40,
                          command=lambda bid=biz["id"]: self.subscribe_to_newsletter(bid)).pack(side="left", padx=5)

    def subscribe_to_newsletter(self, business_id):
        backend.subscribe_to_business(current_user["email"], business_id)
        messagebox.showinfo("Subscribed", "You are now following this business!")
        self.refresh_discover()

    def show_business_detail(self, biz):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        self.selected_business_id = biz["id"]

        header = ctk.CTkFrame(self.main_frame)
        header.pack(fill="x", padx=30, pady=15)
        ctk.CTkLabel(header, text=biz["name"], font=ctk.CTkFont(size=28, weight="bold")).pack(anchor="w", padx=20)
        ctk.CTkLabel(header, text=f" {biz.get('address', 'N/A')}", font=ctk.CTkFont(size=16)).pack(anchor="w", padx=20)
        ctk.CTkLabel(header, text=f" {biz.get('open_time', 'N/A')} – {biz.get('close_time', 'N/A')}",
                     text_color="lightblue").pack(anchor="w", padx=20)
        ctk.CTkLabel(header, text=f" {backend.get_average_rating(biz['id'])}/5").pack(anchor="w", padx=20, pady=5)

        form_scroll = ctk.CTkScrollableFrame(self.main_frame)
        form_scroll.pack(fill="both", expand=True, padx=30, pady=10)

        ctk.CTkLabel(form_scroll, text="Available Services", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w",
                                                                                                            pady=(20,
                                                                                                                  5))
        services_df = backend.get_business_services(biz["id"])
        service_list = ["Select Service"] + list(services_df["service_name"]) if not services_df.empty else [
            "Select Service"]

        self.service_var = ctk.StringVar(value="Select Service")
        self.service_menu = ctk.CTkOptionMenu(form_scroll, values=service_list, variable=self.service_var,
                                              command=self.update_price_on_service_select)
        self.service_menu.pack(pady=10, padx=20, fill="x")

        self.price_label = ctk.CTkLabel(form_scroll, text="Price: £0.00", font=ctk.CTkFont(size=18, weight="bold"),
                                        text_color="lightgreen")
        self.price_label.pack(pady=8)

        ctk.CTkLabel(form_scroll, text="Select Date", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w",
                                                                                                     pady=(20, 5))
        self.cal = Calendar(form_scroll, selectmode='day', date_pattern="y-mm-dd")
        self.cal.pack(pady=10, padx=20)
        self.cal.bind("<<CalendarSelected>>", self.update_available_times)

        ctk.CTkLabel(form_scroll, text="Available Time Slots", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(15, 5))
        self.time_var = ctk.StringVar(value="Select date first")
        self.time_menu = ctk.CTkOptionMenu(form_scroll, values=["Select date first"], variable=self.time_var)
        self.time_menu.pack(pady=8, padx=20, fill="x")
        self.update_available_times()

        ctk.CTkLabel(form_scroll, text="Service Type", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w",
                                                                                                      pady=(15, 5))
        self.delivery_var = ctk.StringVar(value="In-store")
        ctk.CTkOptionMenu(form_scroll, values=["In-store", "Collection", "Delivery", "Home visit"],
                          variable=self.delivery_var).pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(form_scroll, text="Phone Number (required)", font=ctk.CTkFont(size=16, weight="bold")).pack(
            anchor="w", pady=(15, 5))
        self.phone_entry = ctk.CTkEntry(form_scroll, placeholder_text="07123 456 789")
        self.phone_entry.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(form_scroll, text="Delivery Address (only if Delivery)",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 5))
        self.delivery_address_entry = ctk.CTkEntry(form_scroll, placeholder_text="Full delivery address")
        self.delivery_address_entry.pack(pady=8, padx=20, fill="x")

        ctk.CTkLabel(form_scroll, text="Payment Option", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w",
                                                                                                        pady=(15, 5))
        self.payment_var = ctk.StringVar(value="Pay on Arrival")
        ctk.CTkOptionMenu(form_scroll, values=["Pay on Arrival", "Pay Now (on app)"], variable=self.payment_var).pack(
            pady=8, padx=20, fill="x")

        btn_frame = ctk.CTkFrame(form_scroll, fg_color="transparent")
        btn_frame.pack(pady=30, fill="x")
        ctk.CTkButton(btn_frame, text="Confirm Booking", width=300, height=50,
                      command=lambda: self.make_booking(biz)).pack(side="left", padx=20)
        ctk.CTkButton(btn_frame, text="Back to Discover", command=self.show_discover_businesses).pack(side="left",
                                                                                                      padx=20)

    def update_available_times(self, event=None):
        selected_date = self.cal.get_date()
        available = backend.get_available_times(self.selected_business_id, selected_date)
        if not available:
            available = ["No slots available today"]
        self.time_menu.configure(values=available)
        self.time_var.set(available[0] if available else "No slots available today")

    def update_price_on_service_select(self, *args):
        service_name = self.service_var.get()
        if service_name == "Select Service":
            self.current_booking_price = 0.0
            self.price_label.configure(text="Price: £0.00")
            return
        services_df = backend.get_business_services(self.selected_business_id)
        row = services_df[services_df["service_name"] == service_name]
        if not row.empty:
            self.current_booking_price = float(row.iloc[0]["price"])
            self.price_label.configure(text=f"Price: £{self.current_booking_price:.2f}")

    def make_booking(self, biz):
        service = self.service_var.get()
        if service == "Select Service":
            messagebox.showwarning("Warning", "Please select a service")
            return
        date = self.cal.get_date()
        time_slot = self.time_var.get()
        if time_slot in ["Select date first", "No slots available today"]:
            messagebox.showwarning("Warning", "Please select a valid date and available time slot")
            return

        delivery = self.delivery_var.get()
        phone = self.phone_entry.get().strip()
        if not phone or len(re.sub(r'\D', '', phone)) < 10:
            messagebox.showwarning("Warning", "Valid phone number (10+ digits) is required")
            return

        delivery_addr = self.delivery_address_entry.get().strip() if delivery == "Delivery" else ""
        if delivery == "Delivery" and not delivery_addr:
            messagebox.showwarning("Warning", "Delivery address is required")
            return

        payment_method = self.payment_var.get()
        amount = self.current_booking_price

        success, booking_id, msg = backend.book_appointment(
            current_user["email"], biz["id"], date, time_slot, service, delivery,
            payment_method, phone, delivery_addr, amount
        )

        if not success:
            messagebox.showerror("Error", msg or "This time slot is already booked.")
            return

        self.selected_booking_id = booking_id
        if payment_method == "Pay Now (on app)":
            self.show_payment_screen(biz, booking_id, amount)
        else:
            messagebox.showinfo("Booking Confirmed",
                                f"Booking for {date} at {time_slot}\nService: {service}\nPrice: £{amount:.2f}")
            self.show_my_bookings()

    #Payment Screen
    def show_payment_screen(self, biz, booking_id, amount):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text="Secure Payment", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)
        ctk.CTkLabel(self.main_frame, text=f"Paying £{amount:.2f} to {biz['name']}", font=ctk.CTkFont(size=16)).pack(
            pady=5)

        frame = ctk.CTkFrame(self.main_frame)
        frame.pack(pady=20, padx=50, fill="x")

        ctk.CTkLabel(frame, text="Card Number").pack(anchor="w", padx=20, pady=(15, 5))
        self.card_number = ctk.CTkEntry(frame, placeholder_text="4242 4242 4242 4242", width=400)
        self.card_number.pack(pady=5, padx=20)

        sub = ctk.CTkFrame(frame, fg_color="transparent")
        sub.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(sub, text="Expiry (MM/YY)").pack(side="left")
        self.expiry = ctk.CTkEntry(sub, placeholder_text="12/28", width=120)
        self.expiry.pack(side="left", padx=(10, 30))
        ctk.CTkLabel(sub, text="CVV").pack(side="left")
        self.cvv = ctk.CTkEntry(sub, placeholder_text="123", width=100, show="*")
        self.cvv.pack(side="left")

        ctk.CTkLabel(frame, text="Cardholder Name").pack(anchor="w", padx=20, pady=(15, 5))
        self.card_name = ctk.CTkEntry(frame, placeholder_text="John Doe", width=400)
        self.card_name.pack(pady=5, padx=20)

        ctk.CTkLabel(frame, text=" Your payment is secure and encrypted", text_color="lightgreen").pack(pady=15)

        btn_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        self.pay_btn = ctk.CTkButton(btn_frame, text="Pay Now", width=180, height=45, fg_color="green",
                                     command=lambda: self.handle_payment(biz, booking_id, amount))
        self.pay_btn.pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", width=180, height=45, fg_color="gray",
                      command=lambda: self.show_business_detail(biz)).pack(side="left", padx=10)

    def handle_payment(self, biz, booking_id, amount):
        self.pay_btn.configure(state="disabled")
        processing = ctk.CTkLabel(self.main_frame, text="Processing payment… ",
                                  font=ctk.CTkFont(size=18), text_color="#ffd700")
        processing.pack(pady=20)

        delay = int(random.uniform(1.5, 3.0) * 1000)
        self.after(delay, lambda: self.complete_payment(biz, booking_id, amount, processing))

    def complete_payment(self, biz, booking_id, amount, processing_label):
        processing_label.destroy()
        card_details = {
            "card_number": self.card_number.get().replace(" ", ""),
            "expiry": self.expiry.get(),
            "cvv": self.cvv.get(),
            "name": self.card_name.get().strip()
        }
        result = backend.process_payment(amount, card_details)

        if result["status"] == "success":
            bookings_df = backend.load(backend.BOOKINGS_FILE)
            mask = bookings_df["id"] == booking_id
            if mask.any():
                bookings_df.loc[mask, "payment_status"] = "paid"
                bookings_df.loc[mask, "transaction_id"] = result["transaction_id"]
                backend.save(bookings_df, backend.BOOKINGS_FILE)

            updated_booking = bookings_df[mask].iloc[0].to_dict() if mask.any() else {}
            businesses = backend.load(backend.BUSINESSES_FILE)
            biz_row = businesses[businesses["id"] == updated_booking.get("business_id")]
            business_name = biz_row.iloc[0]["name"] if not biz_row.empty else "Business"

            backend.send_payment_success(updated_booking, business_name, result["transaction_id"])
            backend.send_booking_confirmation(updated_booking, business_name)

            receipt_path = self.generate_receipt(updated_booking, biz.get("name", "Business"), amount)
            messagebox.showinfo("Payment Successful",
                                f"Payment successful!\nTransaction ID: {result['transaction_id']}\n\nConfirmation email sent!\nReceipt saved to:\n{receipt_path}")
            self.show_my_bookings()
        else:
            messagebox.showerror("Payment Failed", result.get("message", "Payment failed"))
            self.pay_btn.configure(state="normal")

    def generate_receipt(self, booking, biz_name, amount):
        os.makedirs("../receipts", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"receipts/receipt_{booking.get('id', 'unknown')}_{timestamp}.txt"

        receipt_text = f"""====================================
LIVELINK RECEIPT
====================================
Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Business: {biz_name}
Service: {booking.get('service_name', 'N/A')}
Date & Time: {booking.get('date')} at {booking.get('time')}
Delivery Method: {booking.get('delivery_method', 'N/A')}
Payment Status: {booking.get('payment_status', 'unpaid').upper()}
Transaction ID: {booking.get('transaction_id', 'N/A')}
Amount Paid: £{amount:.2f}
Phone: {booking.get('phone_number', 'N/A')}
Delivery Address: {booking.get('delivery_address', 'N/A')}
Thank you for using LiveLink!
===================================="""

        with open(filename, "w", encoding="utf-8") as f:
            f.write(receipt_text.strip())
        return filename

    #My bookings
    def show_my_bookings(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text=" My Bookings", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        bookings = backend.get_user_bookings(current_user["email"])
        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True, pady=10, padx=30)

        if not bookings:
            ctk.CTkLabel(scroll, text="No bookings yet.\nGo to Discover to book services!").pack(pady=100)
            return

        for b in bookings:
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(card, text=f"{b.get('business_name', 'N/A')} — {b.get('service_name', 'N/A')}",
                         font=ctk.CTkFont(size=17, weight="bold")).pack(anchor="w", padx=15, pady=(12, 4))

            details = f" {b['date']}  {b['time']}\nDelivery: {b.get('delivery_method', 'N/A')}\nStatus: {b['status'].capitalize()}\nPayment: {b.get('payment_status', 'unpaid').upper()}"
            ctk.CTkLabel(card, text=details, justify="left").pack(anchor="w", padx=15, pady=6)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=15, pady=10)
            ctk.CTkButton(btn_frame, text="View Receipt", width=140,
                          command=lambda booking=b: self.show_receipt(booking)).pack(side="left", padx=5)
            if b['status'] in ["pending", "confirmed", "accepted"]:
                ctk.CTkButton(btn_frame, text="Cancel Booking", width=140, fg_color="#c42b1c",
                              command=lambda bid=b['id']: self.cancel_booking(bid)).pack(side="left", padx=5)

    def show_receipt(self, booking):
        win = ctk.CTkToplevel(self)
        win.title(f"Receipt - {booking.get('id', '')[:8]}")
        win.geometry("620x520")
        frame = ctk.CTkFrame(win)
        frame.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(frame, text="LIVELINK RECEIPT", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=10)
        for key, label in [("business_name", "Business"), ("service_name", "Service"), ("date", "Date"),
                           ("time", "Time"), ("delivery_method", "Delivery Method"),
                           ("payment_status", "Payment Status"),
                           ("transaction_id", "Transaction ID"), ("phone_number", "Phone"),
                           ("delivery_address", "Delivery Address")]:
            val = booking.get(key, "N/A")
            ctk.CTkLabel(frame, text=f"{label}: {val}", font=ctk.CTkFont(size=16), anchor="w").pack(anchor="w", pady=3)

        ctk.CTkButton(frame, text="Close", command=win.destroy).pack(pady=30)

    def cancel_booking(self, booking_id):
        bookings_df = backend.load(backend.BOOKINGS_FILE)
        mask = bookings_df["id"] == booking_id
        if mask.any():
            booking = bookings_df[mask].iloc[0].to_dict()

            bookings_df.loc[mask, "status"] = "cancelled"
            backend.save(bookings_df, backend.BOOKINGS_FILE)

            #Send cancellation emails
            businesses = backend.load(backend.BUSINESSES_FILE)
            biz_row = businesses[pd.to_numeric(businesses["id"]) == booking.get("business_id")]
            business_name = biz_row.iloc[0]["name"] if not biz_row.empty else "Business"

            backend.send_cancellation_notice(booking, business_name, "Customer")

            messagebox.showinfo("Cancelled",
                                "Booking cancelled successfully.\nNotifications sent to you and the business.")
            self.show_my_bookings()

    # MANAGE BOOKINGS (BUSINESS)
    def show_business_bookings(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text=" Manage Bookings", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        biz_id = self.get_current_business_id()
        if not biz_id:
            ctk.CTkLabel(self.main_frame, text="No business profile found.").pack(pady=100)
            return

        bookings = backend.get_business_bookings(biz_id)
        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True, pady=10, padx=30)

        if not bookings:
            ctk.CTkLabel(scroll, text="No bookings yet.").pack(pady=100)
            return

        for b in bookings:
            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(card, text=f"Customer: {b.get('customer_email', 'N/A')}",
                         font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", padx=15, pady=(12, 4))

            details = f"Service: {b.get('service_name', 'N/A')}\n {b['date']}  {b['time']}\nDelivery: {b.get('delivery_method', 'N/A')}\nStatus: {b['status'].capitalize()}"
            ctk.CTkLabel(card, text=details, justify="left").pack(anchor="w", padx=15, pady=6)

            if b['status'] == "pending":
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(anchor="e", padx=15, pady=10)
                ctk.CTkButton(btn_frame, text="Accept", fg_color="green", width=100,
                              command=lambda bid=b['id']: self.accept_booking(bid)).pack(side="left", padx=5)
                ctk.CTkButton(btn_frame, text="Decline", fg_color="#c42b1c", width=100,
                              command=lambda bid=b['id']: self.decline_booking(bid)).pack(side="left", padx=5)

    def accept_booking(self, booking_id):
        bookings_df = backend.load(backend.BOOKINGS_FILE)
        bookings_df.loc[bookings_df["id"] == booking_id, "status"] = "accepted"
        backend.save(bookings_df, backend.BOOKINGS_FILE)
        messagebox.showinfo("Accepted", "Booking has been accepted.")
        self.show_business_bookings()

    def decline_booking(self, booking_id):
        bookings_df = backend.load(backend.BOOKINGS_FILE)
        bookings_df.loc[bookings_df["id"] == booking_id, "status"] = "declined"
        backend.save(bookings_df, backend.BOOKINGS_FILE)
        messagebox.showinfo("Declined", "Booking has been declined.")
        self.show_business_bookings()

    def get_current_business_id(self):
        if current_user_type != "business":
            return None
        businesses = backend.load(backend.BUSINESSES_FILE)
        biz = businesses[businesses["owner_email"] == current_user["email"]]
        return int(biz.iloc[0]["id"]) if not biz.empty else None

    # MANAGE SERVICES
    def show_manage_services(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        content = ctk.CTkFrame(self.main_frame)
        content.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(content, text="Manage Services & Prices", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=15, padx=50)

        ctk.CTkLabel(frame, text="Service Name").pack(anchor="w", padx=20, pady=5)
        self.new_service_name = ctk.CTkEntry(frame, width=420)
        self.new_service_name.pack(pady=5, padx=20)

        sub = ctk.CTkFrame(frame, fg_color="transparent")
        sub.pack(fill="x", padx=20, pady=8)
        ctk.CTkLabel(sub, text="Price (£)").pack(side="left")
        self.new_service_price = ctk.CTkEntry(sub, width=160)
        self.new_service_price.pack(side="left", padx=15)

        ctk.CTkButton(frame, text="Add Service", height=45, command=self.add_new_service).pack(pady=15)

        scroll = ctk.CTkScrollableFrame(content)
        scroll.pack(fill="both", expand=True, pady=20, padx=50)

        biz_id = self.get_current_business_id()
        services_df = backend.get_business_services(biz_id) if biz_id else pd.DataFrame()

        if services_df.empty:
            ctk.CTkLabel(scroll, text="No services added yet.").pack(pady=80)
        else:
            for _, s in services_df.iterrows():
                card = ctk.CTkFrame(scroll, corner_radius=10)
                card.pack(fill="x", pady=8, padx=10)
                ctk.CTkLabel(card, text=f"{s['service_name']} — £{float(s['price']):.2f}",
                             font=ctk.CTkFont(size=15)).pack(anchor="w", padx=20, pady=15)
                ctk.CTkButton(card, text="Delete", fg_color="#c42b1c", width=90,
                              command=lambda sid=s['id']: self.delete_service(sid)).pack(anchor="e", padx=20)

    def add_new_service(self):
        name = self.new_service_name.get().strip()
        try:
            price = float(self.new_service_price.get().strip())
        except:
            messagebox.showwarning("Error", "Invalid price")
            return
        if not name:
            messagebox.showwarning("Error", "Service name required")
            return

        biz_id = self.get_current_business_id()
        if backend.add_business_service(biz_id, name, price):
            messagebox.showinfo("Success", f"'{name}' added successfully!")
            self.show_manage_services()

    def delete_service(self, service_id):
        if messagebox.askyesno("Confirm", "Delete this service?"):
            backend.delete_business_service(service_id)
            self.show_manage_services()
#Business Settings
    def show_business_settings(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        settings = backend.get_business_settings(current_user["email"])
        content = ctk.CTkFrame(self.main_frame)
        content.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(content, text=" Business Settings", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=20, padx=50)

        self.is_open_var = ctk.BooleanVar(value=settings.get("is_open", True))
        ctk.CTkSwitch(frame, text="Business is currently Open", variable=self.is_open_var).pack(pady=15)

        ctk.CTkLabel(frame, text="Opening Time (24-hour)", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20,
                                                                                           pady=(15, 5))
        self.open_time_var = ctk.StringVar(value=settings.get("open_time", "09:00"))
        ctk.CTkOptionMenu(frame, values=backend.get_time_options(), variable=self.open_time_var, width=420).pack(pady=8,
                                                                                                                 padx=20)

        ctk.CTkLabel(frame, text="Closing Time (24-hour)", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20,
                                                                                           pady=(15, 5))
        self.close_time_var = ctk.StringVar(value=settings.get("close_time", "17:00"))
        ctk.CTkOptionMenu(frame, values=backend.get_time_options(), variable=self.close_time_var, width=420).pack(
            pady=8, padx=20)

        ctk.CTkLabel(frame, text="Brief Business Description").pack(anchor="w", padx=20, pady=(15, 5))
        self.description_entry = ctk.CTkTextbox(frame, height=120, width=500)
        self.description_entry.insert("1.0", settings.get("description", ""))
        self.description_entry.pack(pady=8, padx=20)

        ctk.CTkButton(frame, text="Save Settings", width=300, height=45, command=self.save_business_settings).pack(
            pady=30)

    def save_business_settings(self):
        is_open = self.is_open_var.get()
        open_time = self.open_time_var.get()
        close_time = self.close_time_var.get()
        description = self.description_entry.get("1.0", "end").strip()
        backend.update_business_settings(current_user["email"], is_open, open_time, close_time, description)
        messagebox.showinfo("Success", "Business settings updated successfully!")
        self.show_main_dashboard()

#Profile
    def show_profile(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        content = ctk.CTkFrame(self.main_frame)
        content.pack(fill="both", expand=True, padx=40, pady=20)

        ctk.CTkLabel(content, text=" My Profile", font=ctk.CTkFont(size=28, weight="bold")).pack(pady=20)

        frame = ctk.CTkFrame(content)
        frame.pack(fill="x", pady=20, padx=50)

        ctk.CTkLabel(frame, text="Full Name", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15, 5))
        self.profile_name = ctk.CTkEntry(frame, width=420,
                                         textvariable=ctk.StringVar(value=current_user.get('name', '')))
        self.profile_name.pack(pady=5, padx=20)

        ctk.CTkLabel(frame, text="Email Address", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15, 5))
        self.profile_email = ctk.CTkEntry(frame, width=420,
                                          textvariable=ctk.StringVar(value=current_user.get('email', '')))
        self.profile_email.pack(pady=5, padx=20)

        if current_user_type == "business":
            businesses = backend.load(backend.BUSINESSES_FILE)
            biz_row = businesses[businesses["owner_email"] == current_user.get("email")]
            if not biz_row.empty:
                biz = biz_row.iloc[0].to_dict()
                current_user.update({
                    "business_name": biz.get("name", ""),
                    "category": biz.get("category", ""),
                    "address": biz.get("address", ""),
                    "phone": biz.get("phone", "")
                })

            ctk.CTkLabel(frame, text="Business Name", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(25, 5))
            self.profile_business_name = ctk.CTkEntry(frame, width=420,
                                                      textvariable=ctk.StringVar(
                                                          value=current_user.get('business_name', '')))
            self.profile_business_name.pack(pady=5, padx=20)

            ctk.CTkLabel(frame, text="Category (custom title allowed)", font=ctk.CTkFont(size=14)).pack(anchor="w",
                                                                                                        padx=20,
                                                                                                        pady=(15, 5))
            self.profile_category = ctk.CTkEntry(frame, width=420,
                                                 textvariable=ctk.StringVar(value=current_user.get('category', '')))
            self.profile_category.pack(pady=5, padx=20)

            ctk.CTkLabel(frame, text="Business Address", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20,
                                                                                         pady=(15, 5))
            self.profile_address = ctk.CTkEntry(frame, width=420,
                                                textvariable=ctk.StringVar(value=current_user.get('address', '')))
            self.profile_address.pack(pady=5, padx=20)

            ctk.CTkLabel(frame, text="Phone Number", font=ctk.CTkFont(size=14)).pack(anchor="w", padx=20, pady=(15, 5))
            self.profile_phone = ctk.CTkEntry(frame, width=420,
                                              textvariable=ctk.StringVar(value=current_user.get('phone', '')))
            self.profile_phone.pack(pady=5, padx=20)

        ctk.CTkButton(frame, text=" Save Changes", width=320, height=55,
                      font=ctk.CTkFont(size=16, weight="bold"),
                      command=self.save_profile).pack(pady=40)

        ctk.CTkButton(frame, text="Back to Home", width=320, height=40, fg_color="transparent",
                      command=self.show_main_dashboard).pack(pady=5)

    def save_profile(self):
        new_name = self.profile_name.get().strip()
        new_email = self.profile_email.get().strip()

        if not new_name or not new_email:
            messagebox.showwarning("Error", "Name and Email cannot be empty")
            return

        old_email = current_user["email"]

        backend.update_user_email(old_email, new_email)
        users = backend.load(backend.USERS_FILE)
        users.loc[users["email"] == new_email, "name"] = new_name
        backend.save(users, backend.USERS_FILE)

        current_user["name"] = new_name
        current_user["email"] = new_email

        if current_user_type == "business":
            businesses = backend.load(backend.BUSINESSES_FILE)
            mask = businesses["owner_email"] == new_email
            if mask.any():
                businesses.loc[mask, "name"] = self.profile_business_name.get().strip()
                businesses.loc[mask, "category"] = self.profile_category.get().strip()
                businesses.loc[mask, "address"] = self.profile_address.get().strip()
                businesses.loc[mask, "phone"] = self.profile_phone.get().strip()
                if old_email != new_email:
                    businesses.loc[mask, "owner_email"] = new_email
                backend.save(businesses, backend.BUSINESSES_FILE)

                current_user["business_name"] = self.profile_business_name.get().strip()
                current_user["category"] = self.profile_category.get().strip()
                current_user["address"] = self.profile_address.get().strip()
                current_user["phone"] = self.profile_phone.get().strip()

        messagebox.showinfo("Success", "Profile updated successfully!")
        self.show_profile()

#My Subscriptions
    def show_my_subscriptions(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text=" My Subscriptions", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True, pady=10, padx=30)

        subscriptions = backend.get_user_subscriptions(current_user["email"])
        businesses = backend.load(backend.BUSINESSES_FILE)

        if not subscriptions:
            ctk.CTkLabel(scroll, text="You haven't subscribed to any businesses yet.").pack(pady=100)
            return

        for sub in subscriptions:
            biz_row = businesses[businesses["id"] == sub["business_id"]]
            if biz_row.empty:
                continue
            biz = biz_row.iloc[0]

            card = ctk.CTkFrame(scroll, corner_radius=12)
            card.pack(fill="x", pady=10, padx=10)
            ctk.CTkLabel(card, text=biz["name"], font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", padx=20,
                                                                                                pady=15)

            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(anchor="e", padx=20, pady=10)
            ctk.CTkButton(btn_frame, text="View Business", width=140,
                          command=lambda b=biz: self.show_business_detail(b)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Book Now", width=140, fg_color="#1f538d",
                          command=lambda b=biz: self.show_business_detail(b)).pack(side="left", padx=5)
            ctk.CTkButton(btn_frame, text="Unsubscribe", fg_color="#c42b1c", width=140,
                          command=lambda bid=biz["id"]: self.unsubscribe(bid)).pack(side="left", padx=5)

    def unsubscribe(self, business_id):
        if messagebox.askyesno("Confirm", "Unsubscribe from this business?"):
            backend.unsubscribe_from_business(current_user["email"], business_id)
            messagebox.showinfo("Unsubscribed", "You have unsubscribed.")
            self.show_my_subscriptions()

    # NOTIFICATIONS
    def show_notifications(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.create_navbar()

        ctk.CTkLabel(self.main_frame, text="🛎 Notifications", font=ctk.CTkFont(size=26, weight="bold")).pack(pady=20)

        scroll = ctk.CTkScrollableFrame(self.main_frame)
        scroll.pack(fill="both", expand=True, pady=10, padx=30)

        if current_user_type == "business":
            biz_id = self.get_current_business_id()
            notes = backend.get_notifications(business_id=biz_id) if biz_id else pd.DataFrame()
        else:
            notes = backend.get_notifications(user_email=current_user["email"])

        if notes.empty:
            ctk.CTkLabel(scroll, text="No notifications yet.").pack(pady=80)
            return

        for _, note in notes.iterrows():
            card = ctk.CTkFrame(scroll, corner_radius=10)
            card.pack(fill="x", pady=8, padx=10)
            ctk.CTkLabel(card, text=note["message"], wraplength=900, justify="left").pack(anchor="w", padx=15, pady=10)
            ctk.CTkLabel(card, text=note["timestamp"], text_color="gray", font=ctk.CTkFont(size=12)).pack(anchor="e",
                                                                                                          padx=15)
            ctk.CTkButton(card, text="View Details", width=120,
                          command=lambda m=note["message"]: messagebox.showinfo("Notification Detail", m)).pack(
                anchor="e", padx=15, pady=5)

    def logout(self):
        global current_user, current_user_type
        current_user = None
        current_user_type = None
        self.show_login_register_screen()


if __name__ == "__main__":
    app = LiveLinkApp()
    try:
        app.mainloop()
    except Exception as e:
        print(f"Unexpected error: {e}")