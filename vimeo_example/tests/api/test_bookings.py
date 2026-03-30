"""API tests for restful-api.dev /objects endpoint.

Target: https://api.restful-api.dev
No authentication required.
"""

from api.booking_client import ObjectsClient
from tests.data.factories import make_object


class TestCreateObject:
    def test_returns_id_and_timestamps(self, objects_client: ObjectsClient):
        result = objects_client.create_object(make_object())

        assert "id" in result
        assert "createdAt" in result

        objects_client.delete_object(result["id"])

    def test_response_matches_payload(self, objects_client: ObjectsClient):
        payload = make_object(name="Custom Widget", data={"color": "blue", "price": 42.0})

        result = objects_client.create_object(payload)

        assert result["name"] == "Custom Widget"
        assert result["data"]["color"] == "blue"
        assert result["data"]["price"] == 42.0

        objects_client.delete_object(result["id"])


class TestGetObject:
    def test_retrieves_correct_object(
        self, objects_client: ObjectsClient, created_object: dict
    ):
        retrieved = objects_client.get_object(created_object["id"])

        assert retrieved["id"] == created_object["id"]
        assert retrieved["name"] == created_object["name"]
        assert retrieved["data"] == created_object["data"]


class TestUpdateObject:
    def test_update_changes_fields(
        self, objects_client: ObjectsClient, created_object: dict
    ):
        updated_payload = make_object(name="Updated Name", data={"version": 2})

        result = objects_client.update_object(created_object["id"], updated_payload)

        assert result["name"] == "Updated Name"
        assert result["data"]["version"] == 2

    def test_update_is_persisted(
        self, objects_client: ObjectsClient, created_object: dict
    ):
        objects_client.update_object(
            created_object["id"], make_object(name="Persisted Name")
        )

        retrieved = objects_client.get_object(created_object["id"])

        assert retrieved["name"] == "Persisted Name"


class TestDeleteObject:
    def test_delete_returns_confirmation_message(self, objects_client: ObjectsClient):
        result = objects_client.create_object(make_object())

        response = objects_client.delete_object(result["id"])

        assert "message" in response
        assert result["id"] in response["message"]

    def test_deleted_object_is_not_accessible(self, objects_client: ObjectsClient):
        result = objects_client.create_object(make_object())

        objects_client.delete_object(result["id"])

        assert not objects_client.object_exists(result["id"])
