import requests

BASE_URL = "https://api.practicesoftwaretesting.com"


class UserApiClient:
    """Client for the practicesoftwaretesting.com user API.

    Used to register unique test users so UI tests are self-contained
    and don't depend on pre-seeded accounts.
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def register(self, email: str, password: str) -> dict:
        """Register a new customer account. Returns the created user dict."""
        payload = {
            "first_name": "Test",
            "last_name": "User",
            "address": "123 Test Street",
            "city": "Test City",
            "state": "TS",
            "country": "US",
            "postcode": "12345",
            "phone": "0123456789",
            "dob": "1990-01-01",
            "email": email,
            "password": password,
        }
        response = self._session.post(f"{self.base_url}/users/register", json=payload)
        response.raise_for_status()
        return response.json()
