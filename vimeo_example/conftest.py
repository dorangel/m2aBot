import pytest
from api.booking_client import ObjectsClient
from api.user_client import UserApiClient
from tests.data.factories import make_object, make_user_credentials


@pytest.fixture(scope="session")
def objects_client() -> ObjectsClient:
    """ObjectsClient instance shared across the entire test session."""
    return ObjectsClient()


@pytest.fixture
def created_object(objects_client: ObjectsClient):
    """Create an object before the test and delete it afterwards.

    Yields the full response dict (includes ``id``, ``name``, ``data``, ``createdAt``).
    """
    result = objects_client.create_object(make_object())
    yield result
    # Best-effort cleanup — the object may already be deleted by the test
    objects_client.delete_object(result["id"])


@pytest.fixture(scope="session")
def test_user() -> dict:
    """Register a unique user via the API once per test session.

    Yields a dict with ``email`` and ``password`` that can be used to log
    into https://practicesoftwaretesting.com in UI tests.
    """
    credentials = make_user_credentials()
    UserApiClient().register(
        email=credentials["email"],
        password=credentials["password"],
    )
    return credentials
