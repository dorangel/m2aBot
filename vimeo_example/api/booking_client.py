import requests

BASE_URL = "https://api.restful-api.dev"


class ObjectsClient:
    """HTTP client for the restful-api.dev /objects endpoint.

    No authentication is required for any operation.
    All IDs returned by the API are strings (UUIDs).
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self._session = requests.Session()
        self._session.headers.update(
            {"Content-Type": "application/json", "Accept": "application/json"}
        )

    def create_object(self, data: dict) -> dict:
        response = self._session.post(f"{self.base_url}/objects", json=data)
        response.raise_for_status()
        return response.json()

    def get_object(self, object_id: str) -> dict:
        response = self._session.get(f"{self.base_url}/objects/{object_id}")
        response.raise_for_status()
        return response.json()

    def update_object(self, object_id: str, data: dict) -> dict:
        response = self._session.put(
            f"{self.base_url}/objects/{object_id}", json=data
        )
        response.raise_for_status()
        return response.json()

    def delete_object(self, object_id: str) -> dict:
        response = self._session.delete(f"{self.base_url}/objects/{object_id}")
        response.raise_for_status()
        return response.json()

    def object_exists(self, object_id: str) -> bool:
        response = self._session.get(f"{self.base_url}/objects/{object_id}")
        return response.status_code == 200
