"""Streamlit UI for the mock booking site."""

import sys
from datetime import date, timedelta
from pathlib import Path

import streamlit as st

# Make the backend importable when running from the mock_project root
sys.path.insert(0, str(Path(__file__).parent))

from backend.booking_service import (
    cancel_booking,
    create_booking,
    get_booked_ranges,
    is_available,
    list_bookings,
    list_locations,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="StayEasy — Book Your Escape",
    page_icon="🌍",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "browse"
if "selected_location" not in st.session_state:
    st.session_state.selected_location = None
if "booking_success" not in st.session_state:
    st.session_state.booking_success = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def go_to(page: str, location: dict | None = None) -> None:
    st.session_state.page = page
    st.session_state.selected_location = location
    st.session_state.booking_success = None


def fmt_price(amount: int) -> str:
    return f"${amount:,}"


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("🌍 StayEasy")
    st.caption("Find your perfect escape")
    st.divider()

    if st.button("🏠 Browse Locations", use_container_width=True):
        go_to("browse")
    if st.button("📋 My Bookings", use_container_width=True):
        go_to("my_bookings")

    st.divider()
    st.caption("Mock booking site · for testing purposes")


# ---------------------------------------------------------------------------
# Page: Browse locations
# ---------------------------------------------------------------------------

def page_browse() -> None:
    st.title("Find Your Perfect Stay")
    st.write("Choose from our hand-picked properties around the world.")

    locations = list_locations()
    cols = st.columns(2)

    for i, loc in enumerate(locations):
        with cols[i % 2]:
            with st.container(border=True):
                st.subheader(f"{loc['emoji']}  {loc['name']}")
                st.caption(f"📍 {loc['location']}")
                st.write(loc["description"])

                col_price, col_guests = st.columns(2)
                with col_price:
                    st.metric("Per night", fmt_price(loc["price_per_night"]))
                with col_guests:
                    st.metric("Max guests", loc["max_guests"])

                with st.expander("Amenities"):
                    for amenity in loc["amenities"]:
                        st.write(f"• {amenity}")

                if st.button("Book Now", key=f"book_{loc['id']}", type="primary"):
                    go_to("booking_form", loc)
                    st.rerun()


# ---------------------------------------------------------------------------
# Page: Booking form
# ---------------------------------------------------------------------------

def page_booking_form() -> None:
    loc = st.session_state.selected_location
    if loc is None:
        go_to("browse")
        st.rerun()
        return

    if st.button("← Back to Browse"):
        go_to("browse")
        st.rerun()

    st.title(f"{loc['emoji']}  {loc['name']}")
    st.caption(f"📍 {loc['location']}  ·  {fmt_price(loc['price_per_night'])} / night")
    st.divider()

    # Show any existing bookings as a warning
    booked = get_booked_ranges(loc["id"])
    if booked:
        with st.expander("⚠️ Already booked dates"):
            for b_in, b_out in booked:
                st.write(f"• {b_in.strftime('%b %d')} → {b_out.strftime('%b %d, %Y')}")

    with st.form("booking_form"):
        st.subheader("Your Details")
        guest_name = st.text_input("Full name *")
        guest_email = st.text_input("Email address *")

        st.subheader("Stay Details")
        today = date.today()
        col_in, col_out = st.columns(2)
        with col_in:
            check_in = st.date_input(
                "Check-in *",
                value=today + timedelta(days=1),
                min_value=today,
            )
        with col_out:
            check_out = st.date_input(
                "Check-out *",
                value=today + timedelta(days=4),
                min_value=today + timedelta(days=1),
            )

        guests = st.number_input(
            f"Number of guests (max {loc['max_guests']}) *",
            min_value=1,
            max_value=loc["max_guests"],
            value=1,
        )

        # Live price estimate
        if check_out > check_in:
            nights = (check_out - check_in).days
            total = nights * loc["price_per_night"]
            st.info(
                f"**{nights} night{'s' if nights > 1 else ''}**  ·  "
                f"{fmt_price(loc['price_per_night'])} × {nights} = **{fmt_price(total)}**"
            )

        submitted = st.form_submit_button("Confirm Booking", type="primary")

    if submitted:
        errors = []
        if not guest_name.strip():
            errors.append("Full name is required")
        if not guest_email.strip() or "@" not in guest_email:
            errors.append("A valid email address is required")
        if check_out <= check_in:
            errors.append("Check-out must be after check-in")

        if errors:
            for e in errors:
                st.error(e)
        else:
            try:
                booking = create_booking(
                    location_id=loc["id"],
                    guest_name=guest_name,
                    guest_email=guest_email,
                    check_in=check_in,
                    check_out=check_out,
                    guests=int(guests),
                )
                st.session_state.booking_success = booking
                go_to("confirmation")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))


# ---------------------------------------------------------------------------
# Page: Confirmation
# ---------------------------------------------------------------------------

def page_confirmation() -> None:
    booking = st.session_state.booking_success
    if booking is None:
        go_to("browse")
        st.rerun()
        return

    st.balloons()
    st.success("### Booking Confirmed!")

    with st.container(border=True):
        st.subheader(f"📋 Booking #{booking['id']}")
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Property:** {booking['location_name']}")
            st.write(f"**Guest:** {booking['guest_name']}")
            st.write(f"**Email:** {booking['guest_email']}")
        with col2:
            st.write(f"**Check-in:** {booking['check_in']}")
            st.write(f"**Check-out:** {booking['check_out']}")
            st.write(f"**Guests:** {booking['guests']}")
        st.divider()
        st.metric(
            "Total",
            fmt_price(booking["total_price"]),
            help=f"{booking['nights']} nights × {fmt_price(booking['price_per_night'])}/night",
        )

    st.write("")
    col_browse, col_my = st.columns(2)
    with col_browse:
        if st.button("Browse more locations", use_container_width=True):
            go_to("browse")
            st.rerun()
    with col_my:
        if st.button("View my bookings", use_container_width=True):
            go_to("my_bookings")
            st.rerun()


# ---------------------------------------------------------------------------
# Page: My bookings
# ---------------------------------------------------------------------------

def page_my_bookings() -> None:
    st.title("My Bookings")

    email = st.text_input("Enter your email to look up bookings")

    if not email:
        st.info("Enter the email you used when booking.")
        return

    bookings = list_bookings(guest_email=email)

    if not bookings:
        st.warning("No bookings found for that email address.")
        return

    st.write(f"Found **{len(bookings)}** booking(s):")

    for booking in sorted(bookings, key=lambda b: b["check_in"], reverse=True):
        check_in = date.fromisoformat(booking["check_in"])
        is_past = check_in < date.today()

        with st.container(border=True):
            col_info, col_action = st.columns([3, 1])
            with col_info:
                status = "✅ Upcoming" if not is_past else "🕐 Past"
                st.write(f"**{booking['location_name']}** — {status}")
                st.caption(
                    f"📅 {booking['check_in']} → {booking['check_out']}  ·  "
                    f"👥 {booking['guests']} guest(s)  ·  "
                    f"💳 {fmt_price(booking['total_price'])}"
                )
                st.caption(f"Booking ID: `{booking['id']}`")
            with col_action:
                if not is_past:
                    if st.button("Cancel", key=f"cancel_{booking['id']}", type="secondary"):
                        cancel_booking(booking["id"])
                        st.success("Booking cancelled.")
                        st.rerun()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

page = st.session_state.page

if page == "browse":
    page_browse()
elif page == "booking_form":
    page_booking_form()
elif page == "confirmation":
    page_confirmation()
elif page == "my_bookings":
    page_my_bookings()
else:
    go_to("browse")
    st.rerun()
