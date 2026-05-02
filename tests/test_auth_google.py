from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app
from app.routers.auth import (
    get_auth_client,
    get_auth_settings,
    get_google_token_verifier,
)


class FakeResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeTableQuery:
    def __init__(self, table_name: str, db: dict[str, list[dict]]):
        self.table_name = table_name
        self.db = db
        self._rows = [dict(row) for row in db.get(table_name, [])]
        self._pending_insert: dict | None = None

    def select(self, _columns: str):
        return self

    def eq(self, column: str, value):
        self._rows = [row for row in self._rows if row.get(column) == value]
        return self

    def is_(self, column: str, value):
        if value is None or value == "null":
            self._rows = [row for row in self._rows if row.get(column) is None]
        return self

    def limit(self, amount: int):
        self._rows = self._rows[:amount]
        return self

    def insert(self, payload: dict):
        self._pending_insert = dict(payload)
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

        return FakeResponse([dict(row) for row in self._rows])


class FakeSupabase:
    def __init__(self):
        self.db = {
            "roluri": [
                {"id": "role-student", "nume": "student"},
                {"id": "role-admin", "nume": "admin"},
            ],
            "utilizatori": [
                {
                    "id": "user-existing",
                    "email": "existing@student.usv.ro",
                    "rol_id": "role-admin",
                    "deleted_at": None,
                }
            ],
        }

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.db)


class FakeSettings:
    def __init__(self):
        self.google_client_id = "test-google-client-id.apps.googleusercontent.com"
        self.google_allowed_domains_list = ["student.usv.ro"]
        self.jwt_expires_minutes = 60
        self.jwt_secret_key = "test-secret"
        self.jwt_algorithm = "HS256"


client = TestClient(app)


def _override_auth_settings() -> Settings:
    return FakeSettings()  # type: ignore[return-value]


def _override_auth_client() -> FakeSupabase:
    return FakeSupabase()


def _verify_allowed(_id_token: str, _client_id: str) -> dict:
    return {
        "email": "new@student.usv.ro",
        "email_verified": True,
    }


def _verify_forbidden_domain(_id_token: str, _client_id: str) -> dict:
    return {
        "email": "user@gmail.com",
        "email_verified": True,
    }


def _verify_existing_user(_id_token: str, _client_id: str) -> dict:
    return {
        "email": "existing@student.usv.ro",
        "email_verified": True,
    }


def setup_function() -> None:
    app.dependency_overrides[get_auth_settings] = _override_auth_settings
    app.dependency_overrides[get_auth_client] = _override_auth_client
    app.dependency_overrides[get_google_token_verifier] = lambda: _verify_allowed


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_google_login_creates_user_and_returns_token() -> None:
    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "google-token-from-frontend"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_google_login_rejects_forbidden_domain() -> None:
    app.dependency_overrides[get_google_token_verifier] = lambda: _verify_forbidden_domain

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "google-token-from-frontend"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Google sign-in is restricted to @student.usv.ro accounts"


def test_google_login_for_existing_user_returns_token() -> None:
    app.dependency_overrides[get_google_token_verifier] = lambda: _verify_existing_user

    response = client.post(
        "/api/v1/auth/google",
        json={"id_token": "google-token-from-frontend"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
