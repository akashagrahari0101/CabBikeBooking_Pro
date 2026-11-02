import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = Path(__file__).with_name("cab_booking.db")

st.set_page_config(
    page_title="RideFlow | Cab & Bike Booking",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------- STYLE ----------------------
st.markdown("""
<style>
    .stApp { background: #f5f7fb; }
    [data-testid="stSidebar"] { background: #101b35; }
    [data-testid="stSidebar"] * { color: #f3f6ff !important; }
    .hero {
        padding: 28px 30px; border-radius: 20px;
        background: linear-gradient(120deg, #14264e 0%, #2457a7 60%, #377fe8 100%);
        color: white; margin-bottom: 18px;
    }
    .hero h1 { color: white; font-size: 2.15rem; margin: 0 0 8px 0; }
    .hero p { color: #e5edff; margin: 0; font-size: 1rem; }
    .metric-card {
        background: white; border: 1px solid #e5eaf3; border-radius: 16px;
        padding: 18px 20px; box-shadow: 0 4px 18px rgba(22,39,75,.04);
    }
    .metric-label { color: #68758c; font-size: .88rem; margin-bottom: 8px; }
    .metric-value { color: #172748; font-size: 1.75rem; font-weight: 750; }
    .metric-note { color: #7a879b; font-size: .78rem; margin-top: 5px; }
    .section-title { color: #18294b; font-size: 1.25rem; font-weight: 700; margin: 12px 0; }
    div.stButton > button[kind="primary"] {
        background: #2457a7; border: none; border-radius: 10px; font-weight: 650;
    }
    div[data-testid="stForm"] {
        background: white; padding: 20px; border: 1px solid #e5eaf3;
        border-radius: 16px;
    }
    .small-muted { color: #738099; font-size: .9rem; }
</style>
""", unsafe_allow_html=True)

# ---------------------- DATABASE ----------------------
def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer TEXT NOT NULL,
            phone TEXT,
            pickup TEXT NOT NULL,
            destination TEXT NOT NULL,
            vehicle TEXT NOT NULL,
            distance REAL NOT NULL,
            fare REAL NOT NULL,
            booking_time TEXT NOT NULL,
            ride_date TEXT NOT NULL,
            payment_method TEXT NOT NULL,
            status TEXT NOT NULL
        )
        """)
        # Upgrade an older database created by the starter Tkinter app.
        existing = {row[1] for row in conn.execute("PRAGMA table_info(bookings)")}
        upgrades = {
            "phone": "TEXT DEFAULT ''",
            "ride_date": "TEXT DEFAULT ''",
            "payment_method": "TEXT DEFAULT 'Cash'",
        }
        for column, definition in upgrades.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE bookings ADD COLUMN {column} {definition}")
        conn.commit()

def load_data():
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM bookings ORDER BY id DESC", conn)
    if not df.empty:
        for col in ["fare", "distance"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["booking_time"] = pd.to_datetime(df["booking_time"], errors="coerce")
        df["ride_date"] = pd.to_datetime(df["ride_date"], errors="coerce")
    return df

def save_booking(values):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO bookings
            (customer, phone, pickup, destination, vehicle, distance, fare,
             booking_time, ride_date, payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        conn.commit()

def money(value):
    return f"₹{value:,.2f}"

init_db()

# ---------------------- SIDEBAR ----------------------
with st.sidebar:
    st.markdown("## 🚘 RideFlow")
    st.caption("CAB & BIKE BOOKING")
    st.markdown("---")
    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Book a Ride", "My Bookings", "Analytics", "About Project"],
        label_visibility="visible",
    )
    st.markdown("---")
    st.markdown("**Project status**")
    st.success("Local database connected")
    st.caption("Demo app • Python + Streamlit + SQLite")

df = load_data()
active = df[df["status"] != "Cancelled"] if not df.empty else df

# ---------------------- SHARED HEADER ----------------------
def hero(title, subtitle):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )

def metric_card(label, value, note):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )

# ---------------------- DASHBOARD ----------------------
if page == "Dashboard":
    hero("Your city. Your ride.", "Book smarter, travel easier. Manage cab and bike rides from one simple dashboard.")
    total = len(df)
    completed_or_booked = len(active)
    revenue = active["fare"].sum() if not active.empty else 0
    avg_fare = active["fare"].mean() if not active.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card("TOTAL BOOKINGS", f"{total:,}", "All booking records")
    with c2: metric_card("ACTIVE RECORDS", f"{completed_or_booked:,}", "Excluding cancelled rides")
    with c3: metric_card("ESTIMATED FARES", money(revenue), "Booked rides, not actual payments")
    with c4: metric_card("AVERAGE FARE", money(avg_fare), "Per non-cancelled booking")

    st.markdown('<div class="section-title">Quick actions</div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    with a:
        st.info("🚲 **Need a quick trip?**\n\nChoose a bike for short journeys.")
    with b:
        st.info("🚕 **Travelling with others?**\n\nSelect an economy or premium cab.")
    with c:
        st.info("📊 **Review your rides**\n\nView booking status and fare history.")

    left, right = st.columns([1.15, 1])
    with left:
        st.markdown('<div class="section-title">Recent bookings</div>', unsafe_allow_html=True)
        if df.empty:
            st.write("No rides yet. Open **Book a Ride** to create your first booking.")
        else:
            recent = df.head(6)[["id", "customer", "pickup", "destination", "vehicle", "fare", "status"]].copy()
            recent["fare"] = recent["fare"].map(money)
            recent.columns = ["ID", "Customer", "Pickup", "Destination", "Vehicle", "Fare", "Status"]
            st.dataframe(recent, use_container_width=True, hide_index=True)
    with right:
        st.markdown('<div class="section-title">Vehicle mix</div>', unsafe_allow_html=True)
        if active.empty:
            st.caption("Your vehicle chart will appear after your first booking.")
        else:
            counts = active["vehicle"].value_counts().rename_axis("Vehicle").reset_index(name="Bookings")
            fig = px.pie(counts, names="Vehicle", values="Bookings", hole=.62)
            fig.update_layout(margin=dict(t=10, b=10, l=5, r=5), legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)

# ---------------------- BOOK A RIDE ----------------------
elif page == "Book a Ride":
    hero("Book your next ride", "Enter your trip details and get a fare estimate before confirming.")
    rates = {"Bike": 8, "Economy Cab": 14, "Premium Cab": 22}
    with st.form("booking_form", clear_on_submit=True):
        st.subheader("Passenger details")
        col1, col2 = st.columns(2)
        with col1:
            customer = st.text_input("Full name *", placeholder="Enter passenger name")
            phone = st.text_input("Phone number (optional)", placeholder="e.g. 9876543210")
            pickup = st.text_input("Pickup location *", placeholder="e.g. College Gate")
        with col2:
            destination = st.text_input("Destination *", placeholder="e.g. Railway Station")
            vehicle = st.selectbox("Choose vehicle", list(rates.keys()))
            ride_date = st.date_input("Ride date", value=date.today(), min_value=date.today())

        col3, col4 = st.columns(2)
        with col3:
            distance = st.number_input("Estimated distance (km)", min_value=0.5, max_value=500.0, value=5.0, step=0.5)
        with col4:
            payment = st.selectbox("Payment preference", ["Cash", "UPI (demo)", "Card (demo)"])

        fare = 40 + distance * rates[vehicle]
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">ESTIMATED FARE</div>'
            f'<div class="metric-value">{money(fare)}</div>'
            f'<div class="metric-note">Includes ₹40 base fare + {money(rates[vehicle])}/km • sample project rates</div></div>',
            unsafe_allow_html=True,
        )
        submitted = st.form_submit_button("Confirm Booking", type="primary", use_container_width=True)

    if submitted:
        if not customer.strip() or not pickup.strip() or not destination.strip():
            st.error("Please fill in your name, pickup location, and destination.")
        elif pickup.strip().casefold() == destination.strip().casefold():
            st.error("Pickup and destination should be different.")
        else:
            now = datetime.now()
            values = (
                customer.strip(), phone.strip(), pickup.strip(), destination.strip(),
                vehicle, float(distance), float(fare), now.strftime("%Y-%m-%d %H:%M:%S"),
                ride_date.isoformat(), payment, "Booked"
            )
            save_booking(values)
            latest = load_data().iloc[0]
            st.success(f"Booking confirmed! Your booking ID is **#{int(latest['id'])}**.")
            st.balloons()

# ---------------------- BOOKINGS ----------------------
elif page == "My Bookings":
    hero("My bookings", "Search, filter, export, and cancel demo bookings.")
    if df.empty:
        st.info("There are no bookings yet. Go to **Book a Ride** to add one.")
    else:
        f1, f2, f3 = st.columns([1.3, 1, 1])
        with f1:
            search = st.text_input("Search", placeholder="Name, pickup, destination or ID")
        with f2:
            status_filter = st.selectbox("Status", ["All", "Booked", "Cancelled"])
        with f3:
            vehicle_filter = st.selectbox("Vehicle", ["All"] + sorted(df["vehicle"].dropna().unique().tolist()))

        filtered = df.copy()
        if search.strip():
            mask = (
                filtered["customer"].astype(str).str.contains(search, case=False, na=False)
                | filtered["pickup"].astype(str).str.contains(search, case=False, na=False)
                | filtered["destination"].astype(str).str.contains(search, case=False, na=False)
                | filtered["id"].astype(str).str.contains(search, case=False, na=False)
            )
            filtered = filtered[mask]
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        if vehicle_filter != "All":
            filtered = filtered[filtered["vehicle"] == vehicle_filter]

        display = filtered[["id", "customer", "pickup", "destination", "vehicle", "distance", "fare", "ride_date", "payment_method", "status"]].copy()
        display["ride_date"] = display["ride_date"].dt.strftime("%d %b %Y")
        display["fare"] = display["fare"].map(money)
        display.columns = ["ID", "Customer", "Pickup", "Destination", "Vehicle", "Km", "Fare", "Ride date", "Payment preference", "Status"]
        st.dataframe(display, use_container_width=True, hide_index=True)

        csv_data = filtered.drop(columns=["booking_time"], errors="ignore").to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export filtered bookings (CSV)", data=csv_data, file_name="rideflow_bookings.csv", mime="text/csv")

        st.markdown("### Cancel a booking")
        options = {
            f"#{int(row.id)} — {row.customer}: {row.pickup} → {row.destination} ({row.status})": int(row.id)
            for row in df.itertuples() if row.status != "Cancelled"
        }
        if options:
            selected_label = st.selectbox("Choose an active booking", list(options.keys()))
            if st.button("Cancel selected booking", type="secondary"):
                with get_connection() as conn:
                    conn.execute("UPDATE bookings SET status = 'Cancelled' WHERE id = ?", (options[selected_label],))
                    conn.commit()
                st.success("Booking cancelled.")
                st.rerun()
        else:
            st.caption("There are no active bookings to cancel.")

# ---------------------- ANALYTICS ----------------------
elif page == "Analytics":
    hero("Ride analytics", "Understand booking patterns, vehicle preferences, and estimated fares.")
    if df.empty:
        st.info("Analytics will be available after you create bookings.")
    else:
        valid = df[df["status"] != "Cancelled"].copy()
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Bookings by vehicle")
            vehicle_data = valid.groupby("vehicle", as_index=False).size().rename(columns={"size": "Bookings"})
            if vehicle_data.empty:
                st.caption("No active bookings to chart.")
            else:
                fig = px.bar(vehicle_data, x="vehicle", y="Bookings", color="vehicle", text="Bookings")
                fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Bookings")
                st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("### Estimated fare by vehicle")
            fare_data = valid.groupby("vehicle", as_index=False)["fare"].sum()
            if fare_data.empty:
                st.caption("No active bookings to chart.")
            else:
                fig = px.bar(fare_data, x="vehicle", y="fare", color="vehicle", text_auto=".2f")
                fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Fare (₹)")
                st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Booking status")
        status_data = df["status"].value_counts().rename_axis("Status").reset_index(name="Count")
        fig = px.pie(status_data, names="Status", values="Count", hole=.55)
        fig.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Charts use records saved in this local demo database. Fares are estimates, not verified revenue.")

# ---------------------- ABOUT ----------------------
elif page == "About Project":
    hero("About RideFlow", "A Python-based academic demonstration of a cab and bike booking system.")
    st.markdown("### Project overview")
    st.write(
        "RideFlow demonstrates a basic ride-booking workflow with a multi-page dashboard, "
        "sample fare calculation, local database storage, booking search, cancellation, CSV export, "
        "and simple analytics."
    )
    st.markdown("### Technology stack")
    tech1, tech2, tech3 = st.columns(3)
    with tech1:
        st.info("**Python**\n\nApplication logic and fare calculation")
    with tech2:
        st.info("**Streamlit + Plotly**\n\nWeb UI and interactive charts")
    with tech3:
        st.info("**SQLite + Pandas**\n\nPersistent storage and data analysis")
    st.markdown("### Limitations and future improvements")
    st.write("- Login and role-based admin/driver dashboards")
    st.write("- Real maps, GPS, route distance and live driver tracking")
    st.write("- Real payment gateway integration")
    st.write("- Email/SMS notifications and driver assignment")
    st.write("- Machine-learning-based demand prediction")
    st.warning("This is a local demo. UPI and card choices only record a preference; they do not process payments. Live tracking and driver dispatch are not connected.")

st.markdown("---")
st.caption("RideFlow • Educational demo • Fare rates are configurable sample values")
