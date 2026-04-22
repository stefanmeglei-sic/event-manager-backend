from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.main import app
from app.routers.users import admin_only, get_users_client


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeTableQuery:
    def __init__(self, table_name: str, db: dict[str, list[dict]]):
        self.table_name = table_name
        self.db = db
        self._rows = [dict(row) for row in db.get(table_name, [])]
        self._pending_insert: dict | None = None
        self._pending_update: dict | None = None

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value):
        self._rows = [row for row in self._rows if row.get(column) == value]
        return self

    def gt(self, column: str, value):
        self._rows = [row for row in self._rows if row.get(column) > value]
        return self

    def is_(self, column: str, value):
        if value is None or value == "null":
            self._rows = [row for row in self._rows if row.get(column) is None]
        return self

    def order(self, column: str):
        self._rows.sort(key=lambda row: row.get(column) or "")
        return self

    def limit(self, amount: int):
        self._rows = self._rows[:amount]
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
                "id": "user-new",
                "created_at": "2026-04-22T10:00:00+00:00",
                "deleted_at": None,
                **self._pending_insert,
            }
            self.db[self.table_name].append(created)
            return FakeResponse([dict(created)])

        if self._pending_update is not None:
            ids = {row.get("id") for row in self._rows}
            updated_rows: list[dict] = []
            for row in self.db.get(self.table_name, []):
                if row.get("id") in ids:
                    row.update(self._pending_update)
                    updated_rows.append(dict(row))
            return FakeResponse(updated_rows)

        return FakeResponse([dict(row) for row in self._rows])


class FakeSupabase:
    def __init__(self):
        self.db = {
            "utilizatori": [
                {
                    "id": "user-1",
                    "email": "admin@example.com",
                    "password_hash": "hashed-admin",
                    "rol_id": "role-admin",
                    "created_at": "2026-04-22T10:00:00+00:00",
                    "deleted_at": None,
                },
                {
                    "id": "user-deleted",
                    "email": "gone@example.com",
                    "password_hash": "hashed-gone",
                    "rol_id": "role-student",
                    "created_at": "2026-04-22T10:00:00+00:00",
                    "deleted_at": "2026-04-22T12:00:00+00:00",
                },
                {
                    "id": "user-2",
                    "email": "student@example.com",
                    "password_hash": "hashed-student",
                    "rol_id": "role-student",
                    "created_at": "2026-04-22T10:10:00+00:00",
                    "deleted_at": None,
                },
            ]
        }

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.db)


client = TestClient(app)


def _override_supabase() -> FakeSupabase:
    return FakeSupabase()


def _override_admin_user() -> CurrentUser:
    return CurrentUser(user_id="user-1", role="admin", email="admin@example.com")


def _override_student_user() -> CurrentUser:
    return CurrentUser(user_id="user-2", role="student", email="student@example.com")


def setup_function() -> None:
    app.dependency_overrides[get_users_client] = _override_supabase
    app.dependency_overrides[admin_only] = _override_admin_user
    app.dependency_overrides[get_current_user] = _override_admin_user


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_create_user() -> None:
    response = client.post(
        "/api/v1/users",
        json={
            "email": "new@example.com",
            "password": "secret123",
            "rol_id": "role-student",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "user-new"
    assert body["email"] == "new@example.com"
    assert body["rol_id"] == "role-student"


def test_list_users_admin_access() -> None:
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "user-1"


def test_list_users_cursor() -> None:
    response = client.get("/api/v1/users?cursor_id=user-1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "user-2"


def test_get_user_admin_access() -> None:
    response = client.get("/api/v1/users/user-1")

    assert response.status_code == 200
    assert response.json()["email"] == "admin@example.com"


def test_get_user_denies_other_non_admin() -> None:
    app.dependency_overrides[get_current_user] = _override_student_user

    response = client.get("/api/v1/users/user-1")

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_update_user_requires_payload_fields() -> None:
    response = client.patch("/api/v1/users/user-1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields provided for update"


def test_update_user() -> None:
    response = client.patch(
        "/api/v1/users/user-1",
        json={"email": "admin+updated@example.com"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "admin+updated@example.com"


def test_get_user_not_found() -> None:
    response = client.get("/api/v1/users/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
