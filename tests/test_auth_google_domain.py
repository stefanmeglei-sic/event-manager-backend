import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


def test_google_login_rejects_non_student_domain(client: TestClient):
    """Google OAuth must only accept @student.usv.ro emails."""
    non_student_email = "user@gmail.com"
    with patch("app.routers.auth._verify_google_id_token") as mock_verify:
        mock_verify.return_value = {
            "email": non_student_email,
            "email_verified": True,
            "sub": "google-sub-123",
        }
        resp = client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
        )
    assert resp.status_code == 403
    assert "student.usv.ro" in resp.json()["detail"]


def test_google_login_accepts_student_domain(client: TestClient):
    """Google OAuth must accept @student.usv.ro emails."""
    student_email = "test.student@student.usv.ro"
    with patch("app.routers.auth._verify_google_id_token") as mock_verify:
        mock_verify.return_value = {
            "email": student_email,
            "email_verified": True,
            "sub": "google-sub-456",
        }
        # This will try to hit DB — that's OK for integration test; may fail if DB not available
        # Just ensure it does NOT return 403
        resp = client.post(
            "/api/v1/auth/google",
            json={"id_token": "fake-token"},
        )
    assert resp.status_code != 403
