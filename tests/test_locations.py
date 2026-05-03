from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser
from app.localization import get_message
from app.main import app
from app.routers.locations import admin_only, get_locations_client


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeLocationsQuery:
    def __init__(self, db: list[dict]):
        self.db = db
        self._rows = [dict(row) for row in db]
        self._pending_insert: dict | None = None
        self._pending_update: dict | None = None

    def select(self, _columns: str):
        return self

    def order(self, _column: str):
        self._rows.sort(key=lambda row: row.get("nume_sala") or "")
        return self

    def is_(self, column: str, value: str | None):
        if value in (None, "null"):
            self._rows = [row for row in self._rows if row.get(column) is None]
        return self

    def eq(self, column: str, value: str):
        self._rows = [row for row in self._rows if row.get(column) == value]
        return self

    def insert(self, payload: dict):
        self._pending_insert = dict(payload)
        return self

    def update(self, payload: dict):
        self._pending_update = dict(payload)
        return self

    def execute(self):
        if self._pending_insert is not None:
            created = {
                "id": "loc-new",
                "deleted_at": None,
                **self._pending_insert,
            }
            self.db.append(created)
            return FakeResponse([dict(created)])

        if self._pending_update is not None:
            ids = {row.get("id") for row in self._rows}
            updated: list[dict] = []
            for row in self.db:
                if row.get("id") in ids:
                    row.update(self._pending_update)
                    updated.append(dict(row))
            return FakeResponse(updated)

        return FakeResponse([dict(row) for row in self._rows])


class FakeSupabase:
    def __init__(self):
        self.locations = [
            {
                "id": "loc-1",
                "nume_sala": "Aula Magna",
                "corp_cladire": "A",
                "capacitate": 120,
                "deleted_at": None,
            }
        ]

    def table(self, table_name: str):
        if table_name != "locatii":
            raise AssertionError("Unexpected table")
        return FakeLocationsQuery(self.locations)


client = TestClient(app)


def _override_supabase() -> FakeSupabase:
    return FakeSupabase()


def _override_admin() -> CurrentUser:
    return CurrentUser(user_id="admin-id", role="admin", email="admin@usv.ro")


def setup_function() -> None:
    app.dependency_overrides[get_locations_client] = _override_supabase
    app.dependency_overrides[admin_only] = _override_admin


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_list_locations() -> None:
    response = client.get("/api/v1/locations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "loc-1",
            "nume_sala": "Aula Magna",
            "corp_cladire": "A",
            "capacitate": 120,
        }
    ]


def test_create_location_admin() -> None:
    response = client.post(
        "/api/v1/locations",
        json={"nume_sala": "C2", "corp_cladire": "C", "capacitate": 30},
    )

    assert response.status_code == 201
    assert response.json()["nume_sala"] == "C2"


def test_update_location_admin() -> None:
    response = client.patch(
        "/api/v1/locations/loc-1",
        json={"capacitate": 150},
    )

    assert response.status_code == 200
    assert response.json()["capacitate"] == 150


def test_delete_location_admin() -> None:
    response = client.delete("/api/v1/locations/loc-1")

    assert response.status_code == 200
    assert response.json() == {"detail": get_message("errors.lookups.location_deleted")}
