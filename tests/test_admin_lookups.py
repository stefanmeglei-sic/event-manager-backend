from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser
from app.main import app
from app.routers.admin import admin_only, get_client


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeAdminQuery:
    def __init__(self, db: list[dict]):
        self.db = db
        self._rows = [dict(row) for row in db]
        self._pending_insert: dict | None = None
        self._pending_update: dict | None = None
        self._pending_delete: bool = False

    def select(self, _columns: str):
        return self

    def order(self, _column: str):
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

    def delete(self):
        self._pending_delete = True
        return self

    def execute(self):
        if self._pending_insert is not None:
            created = {"id": "new-uuid", **self._pending_insert}
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

        if self._pending_delete:
            ids = {row.get("id") for row in self._rows}
            self.db[:] = [row for row in self.db if row.get("id") not in ids]
            return FakeResponse([])

        return FakeResponse([dict(row) for row in self._rows])


class FakeSupabase:
    def __init__(self):
        self.data: dict[str, list[dict]] = {
            "categorii_eveniment": [{"id": "cat-1", "nume": "Workshop"}],
            "tip_participare": [{"id": "tp-1", "nume": "Hybrid"}],
            "statusuri": [{"id": "st-1", "nume": "draft", "tip": "event"}],
        }

    def table(self, table_name: str):
        return FakeAdminQuery(self.data.setdefault(table_name, []))


client = TestClient(app)


def _override_client() -> FakeSupabase:
    return FakeSupabase()


def _override_admin() -> CurrentUser:
    return CurrentUser(user_id="admin-id", role="admin", email="admin@usv.ro")


def setup_function() -> None:
    app.dependency_overrides[get_client] = _override_client
    app.dependency_overrides[admin_only] = _override_admin


def teardown_function() -> None:
    app.dependency_overrides.clear()


# ── Event Categories ──────────────────────────────────────────────────────────

def test_create_category_admin() -> None:
    response = client.post("/api/v1/admin/categories", json={"nume": "Conference"})

    assert response.status_code == 201
    body = response.json()
    assert body["nume"] == "Conference"
    assert "id" in body


def test_create_category_requires_auth() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_client] = _override_client
    response = client.post("/api/v1/admin/categories", json={"nume": "Conference"})
    assert response.status_code in (401, 403)
    # Restore admin override for subsequent tests in module
    app.dependency_overrides[admin_only] = _override_admin


def test_update_category_admin() -> None:
    response = client.patch("/api/v1/admin/categories/cat-1", json={"nume": "Seminar"})

    assert response.status_code == 200
    assert response.json()["nume"] == "Seminar"


def test_delete_category_admin() -> None:
    response = client.delete("/api/v1/admin/categories/cat-1")

    assert response.status_code == 200
    assert response.json()["detail"] == "Deleted successfully"


# ── Participation Types ───────────────────────────────────────────────────────

def test_create_participation_type_admin() -> None:
    response = client.post("/api/v1/admin/participation-types", json={"nume": "Online"})

    assert response.status_code == 201
    body = response.json()
    assert body["nume"] == "Online"
    assert "id" in body


def test_create_participation_type_requires_auth() -> None:
    app.dependency_overrides.clear()
    app.dependency_overrides[get_client] = _override_client
    response = client.post("/api/v1/admin/participation-types", json={"nume": "Online"})
    assert response.status_code in (401, 403)
    app.dependency_overrides[admin_only] = _override_admin


def test_update_participation_type_admin() -> None:
    response = client.patch("/api/v1/admin/participation-types/tp-1", json={"nume": "In-person"})

    assert response.status_code == 200
    assert response.json()["nume"] == "In-person"


def test_delete_participation_type_admin() -> None:
    response = client.delete("/api/v1/admin/participation-types/tp-1")

    assert response.status_code == 200
    assert response.json()["detail"] == "Deleted successfully"
