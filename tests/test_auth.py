from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_returns_access_token() -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "student@example.com", "password": "testpass"},
    )

    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_me_requires_token() -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing bearer token"
