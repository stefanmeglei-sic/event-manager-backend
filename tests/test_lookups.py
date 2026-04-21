from fastapi.testclient import TestClient

from app.main import app
from app.routers.lookups import get_lookup_client


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeQuery:
    def __init__(self, data: list[dict]):
        self._data = data

    def select(self, _columns: str):
        return self

    def order(self, _column: str):
        return self

    def in_(self, column: str, values: list[str]):
        self._data = [row for row in self._data if row.get(column) in values]
        return self

    def is_(self, column: str, value: str | None):
        if value in (None, "null"):
            self._data = [row for row in self._data if row.get(column) is None]
        return self

    def execute(self):
        return FakeResponse(self._data)


class FakeSupabase:
    def __init__(self):
        self.tables = {
            "roluri": [
                {"id": "1", "nume": "admin"},
                {"id": "2", "nume": "student"},
            ],
            "statusuri": [
                {"id": "3", "nume": "draft"},
                {"id": "4", "nume": "published"},
                {"id": "5", "nume": "pending"},
                {"id": "6", "nume": "checked_in"},
            ],
            "categorii_eveniment": [{"id": "7", "nume": "workshop"}],
            "tip_participare": [{"id": "8", "nume": "hybrid"}],
            "locatii": [
                {
                    "id": "9",
                    "nume_sala": "Aula Magna",
                    "corp_cladire": "A",
                    "capacitate": 120,
                    "deleted_at": None,
                },
                {
                    "id": "10",
                    "nume_sala": "Old room",
                    "corp_cladire": "B",
                    "capacitate": 20,
                    "deleted_at": "2026-01-01T00:00:00Z",
                },
            ],
        }

    def table(self, table_name: str):
        return FakeQuery(list(self.tables.get(table_name, [])))


client = TestClient(app)


def _override_supabase() -> FakeSupabase:
    return FakeSupabase()


def setup_function() -> None:
    app.dependency_overrides[get_lookup_client] = _override_supabase


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_roles_lookup_returns_data() -> None:
    response = client.get("/api/v1/lookups/roles")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "1", "nume": "admin"},
        {"id": "2", "nume": "student"},
    ]


def test_event_statuses_lookup_filters_values() -> None:
    response = client.get("/api/v1/lookups/event-statuses")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "3", "nume": "draft"},
        {"id": "4", "nume": "published"},
    ]


def test_registration_statuses_lookup_filters_values() -> None:
    response = client.get("/api/v1/lookups/registration-statuses")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "5", "nume": "pending"},
        {"id": "6", "nume": "checked_in"},
    ]


def test_locations_lookup_ignores_soft_deleted_rows() -> None:
    response = client.get("/api/v1/lookups/locations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "9",
            "nume_sala": "Aula Magna",
            "corp_cladire": "A",
            "capacitate": 120,
        }
    ]


def test_participation_types_lookup_returns_data() -> None:
    response = client.get("/api/v1/lookups/participation-types")

    assert response.status_code == 200
    assert response.json() == [{"id": "8", "nume": "hybrid"}]
