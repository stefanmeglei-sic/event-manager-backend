from passlib.context import CryptContext

from fastapi.testclient import TestClient

from app.main import app
from app.routers.auth import get_auth_client


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class FakeAuthResponse:
    def __init__(self, data: list[dict]):
        self.data = data


class FakeAuthTableQuery:
    def __init__(self, table_name: str, db: dict[str, list[dict]]):
        self.table_name = table_name
        self.db = db
        self._rows = [dict(row) for row in db.get(table_name, [])]

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

    def execute(self):
        return FakeAuthResponse([dict(row) for row in self._rows])


class FakeAuthSupabase:
    def __init__(self):
        hashed = _pwd_context.hash("testpass")
        self.db: dict[str, list[dict]] = {
            "utilizatori": [
                {
                    "id": "user-login-1",
                    "email": "student@example.com",
                    "password_hash": hashed,
                    "rol_id": "role-student",
                    "deleted_at": None,
                }
            ],
            "roluri": [
                {"id": "role-student", "nume": "student"},
            ],
        }

    def table(self, table_name: str):
        return FakeAuthTableQuery(table_name, self.db)


def _override_auth_client() -> FakeAuthSupabase:
    return FakeAuthSupabase()


client = TestClient(app)


def test_login_returns_access_token() -> None:
    app.dependency_overrides[get_auth_client] = _override_auth_client
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@example.com", "password": "testpass"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"
    finally:
        app.dependency_overrides.clear()


def test_login_returns_401_for_wrong_password() -> None:
    app.dependency_overrides[get_auth_client] = _override_auth_client
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "student@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_login_returns_401_for_unknown_email() -> None:
    app.dependency_overrides[get_auth_client] = _override_auth_client
    try:
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@example.com", "password": "testpass"},
        )
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_me_requires_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
