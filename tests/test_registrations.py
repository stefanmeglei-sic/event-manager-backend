from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.localization import get_message
from app.main import app
from app.routers.registrations import admin_or_organizer, get_registrations_client


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

    def neq(self, column: str, value):
        self._rows = [row for row in self._rows if row.get(column) != value]
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
                "id": "reg-new",
                "created_at": "2026-04-22T10:00:00+00:00",
                "check_in_at": None,
                "qr_token": None,
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
            "statusuri": [
                {"id": "st-pending", "nume": "pending"},
                {"id": "st-cancelled", "nume": "cancelled"},
                {"id": "st-confirmed", "nume": "confirmed"},
                {"id": "st-checked", "nume": "checked_in"},
            ],
            "eventi": [],
            "inscrieri": [
                {
                    "id": "reg-1",
                    "eveniment_id": "evt-1",
                    "user_id": "user-1",
                    "tip_participare_id": "tp-1",
                    "status_id": "st-pending",
                    "check_in_at": None,
                    "qr_token": None,
                    "created_at": "2026-04-22T10:00:00+00:00",
                },
                {
                    "id": "reg-full-occupant",
                    "eveniment_id": "evt-full",
                    "user_id": "user-99",
                    "tip_participare_id": "tp-1",
                    "status_id": "st-confirmed",
                    "check_in_at": None,
                    "qr_token": None,
                    "created_at": "2026-04-22T10:00:00+00:00",
                },
            ],
            "evenimente": [
                {
                    "id": "evt-1",
                    "max_participanti": 10,
                    "deadline_inscriere": None,
                },
                {
                    "id": "evt-2",
                    "organizer_id": "org-1",
                    "max_participanti": 100,
                    "deadline_inscriere": None,
                },
                {
                    "id": "evt-deadline",
                    "max_participanti": 100,
                    "deadline_inscriere": "2026-01-01T00:00:00+00:00",
                },
                {
                    "id": "evt-full",
                    "max_participanti": 1,
                    "deadline_inscriere": None,
                },
            ],
        }

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.db)


client = TestClient(app)


def _override_supabase() -> FakeSupabase:
    return FakeSupabase()


def _override_user_1() -> CurrentUser:
    return CurrentUser(user_id="user-1", role="student", email="u1@example.com")


def _override_user_2() -> CurrentUser:
    return CurrentUser(user_id="user-2", role="student", email="u2@example.com")


def _override_admin() -> CurrentUser:
    return CurrentUser(user_id="admin-1", role="admin", email="admin@example.com")


def _override_owner_organizer() -> CurrentUser:
    return CurrentUser(user_id="org-1", role="organizer", email="organizer@example.com")


def setup_function() -> None:
    app.dependency_overrides[get_registrations_client] = _override_supabase
    app.dependency_overrides[get_current_user] = _override_user_2
    app.dependency_overrides[admin_or_organizer] = _override_admin


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_register_to_event_creates_pending_registration() -> None:
    response = client.post(
        "/api/v1/events/evt-2/registrations",
        json={"tip_participare_id": "tp-2"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "reg-new"
    assert body["eveniment_id"] == "evt-2"
    assert body["user_id"] == "user-2"
    assert body["status_id"] == "st-pending"


def test_register_to_event_conflict_if_already_registered() -> None:
    app.dependency_overrides[get_current_user] = _override_user_1

    response = client.post(
        "/api/v1/events/evt-1/registrations",
        json={"tip_participare_id": "tp-1"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == get_message("errors.registrations.already_registered")


def test_cancel_registration_denies_non_owner_non_admin() -> None:
    app.dependency_overrides[get_current_user] = _override_user_2

    response = client.patch("/api/v1/events/evt-1/registrations/reg-1/cancel")

    assert response.status_code == 403
    assert response.json()["detail"] == get_message("errors.permissions.insufficient")


def test_cancel_registration_allows_owner() -> None:
    app.dependency_overrides[get_current_user] = _override_user_1

    response = client.patch("/api/v1/events/evt-1/registrations/reg-1/cancel")

    assert response.status_code == 200
    assert response.json()["status_id"] == "st-cancelled"


def test_confirm_registration() -> None:
    response = client.patch("/api/v1/events/evt-1/registrations/reg-1/confirm")

    assert response.status_code == 200
    assert response.json()["status_id"] == "st-confirmed"


def test_check_in_registration_sets_timestamp_and_status() -> None:
    response = client.patch("/api/v1/events/evt-1/registrations/reg-1/check-in")

    assert response.status_code == 200
    body = response.json()
    assert body["status_id"] == "st-checked"
    assert body["check_in_at"] is not None


def test_register_to_event_deadline_passed() -> None:
    response = client.post(
        "/api/v1/events/evt-deadline/registrations",
        json={"tip_participare_id": "tp-1"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == get_message("errors.registrations.deadline_passed")


def test_register_to_event_at_full_capacity() -> None:
    response = client.post(
        "/api/v1/events/evt-full/registrations",
        json={"tip_participare_id": "tp-1"},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == get_message("errors.registrations.full_capacity")


def test_register_to_event_blocks_organizer_for_own_event() -> None:
    app.dependency_overrides[get_current_user] = _override_owner_organizer

    response = client.post(
        "/api/v1/events/evt-2/registrations",
        json={"tip_participare_id": "tp-2"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == get_message("errors.registrations.organizer_own_event")
