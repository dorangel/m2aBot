import uuid
from datetime import date, timedelta


def make_object(**overrides) -> dict:
    """Return a valid object payload for restful-api.dev.

    The API accepts any ``name`` string and a free-form ``data`` dict.
    Override any top-level key, e.g.::

        make_object(name="My Widget", data={"color": "red"})
    """
    data = {
        "name": "Test Item",
        "data": {
            "category": "electronics",
            "price": 99.99,
            "inStock": True,
        },
    }
    data.update(overrides)
    return data


def make_user_credentials() -> dict:
    """Generate a unique email/password pair for a fresh test user.

    Returns a dict with ``email`` and ``password`` keys.
    The email uses a UUID suffix to avoid collisions across test runs.
    """
    unique_id = uuid.uuid4().hex[:8]
    return {
        "email": f"testuser+{unique_id}@example.com",
        "password": "Test1234!",
    }
