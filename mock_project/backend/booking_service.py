"""Business logic for the booking system."""

import uuid
from datetime import date, datetime

from .db import (
    delete_booking,
    get_booking,
    get_bookings,
    get_location,
    get_locations,
    insert_booking,
)


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

def list_locations() -> list[dict]:
    return get_locations()


def fetch_location(location_id: str) -> dict | None:
    return get_location(location_id)


# ---------------------------------------------------------------------------
# Availability
# ---------------------------------------------------------------------------

def is_available(location_id: str, check_in: date, check_out: date) -> bool:
    """Return True if no existing booking overlaps [check_in, check_out)."""
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")

    for booking in get_bookings():
        if booking["location_id"] != location_id:
            continue
        b_in = date.fromisoformat(booking["check_in"])
        b_out = date.fromisoformat(booking["check_out"])
        # Overlap when ranges intersect
        if check_in < b_out and check_out > b_in:
            return False
    return True


def get_booked_ranges(location_id: str) -> list[tuple[date, date]]:
    """Return all booked (check_in, check_out) date pairs for a location."""
    return [
        (date.fromisoformat(b["check_in"]), date.fromisoformat(b["check_out"]))
        for b in get_bookings()
        if b["location_id"] == location_id
    ]


# ---------------------------------------------------------------------------
# Bookings
# ---------------------------------------------------------------------------

def create_booking(
    location_id: str,
    guest_name: str,
    guest_email: str,
    check_in: date,
    check_out: date,
    guests: int,
) -> dict:
    """Validate and persist a new booking. Returns the created booking dict."""
    location = get_location(location_id)
    if location is None:
        raise ValueError(f"Location '{location_id}' not found")

    if guests < 1:
        raise ValueError("guests must be at least 1")
    if guests > location["max_guests"]:
        raise ValueError(
            f"This property accommodates at most {location['max_guests']} guests"
        )
    if check_out <= check_in:
        raise ValueError("check_out must be after check_in")
    if not is_available(location_id, check_in, check_out):
        raise ValueError("Selected dates are not available")

    nights = (check_out - check_in).days
    total = nights * location["price_per_night"]

    booking = {
        "id": f"bk_{uuid.uuid4().hex[:8]}",
        "location_id": location_id,
        "location_name": location["name"],
        "guest_name": guest_name.strip(),
        "guest_email": guest_email.strip().lower(),
        "check_in": check_in.isoformat(),
        "check_out": check_out.isoformat(),
        "nights": nights,
        "guests": guests,
        "price_per_night": location["price_per_night"],
        "total_price": total,
        "created_at": datetime.utcnow().isoformat(),
    }
    return insert_booking(booking)


def cancel_booking(booking_id: str) -> bool:
    """Cancel (delete) a booking by ID. Returns True if found and removed."""
    return delete_booking(booking_id)


def list_bookings(guest_email: str | None = None) -> list[dict]:
    """Return all bookings, optionally filtered by guest email."""
    bookings = get_bookings()
    if guest_email:
        email = guest_email.strip().lower()
        bookings = [b for b in bookings if b["guest_email"] == email]
    return bookings


def get_booking_detail(booking_id: str) -> dict | None:
    return get_booking(booking_id)
