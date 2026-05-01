import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def make_admin_token(client: TestClient) -> str:
    resp = client.post("/api/v1/auth/login", json={"email": "admin@usv.ro", "password": "Admin1234!"})
    if resp.status_code != 200:
        pytest.skip("Admin user not available in test DB")
    return resp.json()["access_token"]


def test_summary_requires_auth(client: TestClient):
    resp = client.get("/api/v1/reports/summary")
    assert resp.status_code == 403


def test_events_by_month_requires_auth(client: TestClient):
    resp = client.get("/api/v1/reports/events-by-month")
    assert resp.status_code == 403


def test_summary_admin(client: TestClient):
    token = make_admin_token(client)
    resp = client.get("/api/v1/reports/summary", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "total_events" in data
    assert "total_registrations" in data
    assert "avg_participants_per_event" in data
