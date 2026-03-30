"""Simple JSON-file database layer."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
LOCATIONS_FILE = DATA_DIR / "locations.json"
BOOKINGS_FILE = DATA_DIR / "bookings.json"


def get_locations() -> list[dict]:
    return json.loads(LOCATIONS_FILE.read_text(encoding="utf-8"))


def get_location(location_id: str) -> dict | None:
    return next((loc for loc in get_locations() if loc["id"] == location_id), None)


def get_bookings() -> list[dict]:
    return json.loads(BOOKINGS_FILE.read_text(encoding="utf-8"))


def save_bookings(bookings: list[dict]) -> None:
    BOOKINGS_FILE.write_text(json.dumps(bookings, indent=2), encoding="utf-8")


def get_booking(booking_id: str) -> dict | None:
    return next((b for b in get_bookings() if b["id"] == booking_id), None)


def insert_booking(booking: dict) -> dict:
    bookings = get_bookings()
    bookings.append(booking)
    save_bookings(bookings)
    return booking


def delete_booking(booking_id: str) -> bool:
    bookings = get_bookings()
    new_bookings = [b for b in bookings if b["id"] != booking_id]
    if len(new_bookings) == len(bookings):
        return False
    save_bookings(new_bookings)
    return True
