from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.main import app
from app.routers.events import admin_or_organizer, get_events_client


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

    def order(self, column: str):
        self._rows.sort(key=lambda row: row.get(column) or "")
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
                "id": "evt-new",
                "created_at": datetime.now(UTC).isoformat(),
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
            "evenimente": [
                {
                    "id": "evt-1",
                    "titlu": "Workshop AI",
                    "descriere": "Prompt engineering",
                    "start_date": "2026-05-01T10:00:00+00:00",
                    "end_date": "2026-05-01T12:00:00+00:00",
                    "locatie_id": "loc-1",
                    "categorie_id": "cat-1",
                    "status_id": "st-published",
                    "organizer_id": "user-1",
                    "tip_participare_id": "tp-1",
                    "max_participanti": 100,
                    "deadline_inscriere": None,
                    "link_inscriere": None,
                    "created_at": "2026-04-22T10:00:00+00:00",
                    "deleted_at": None,
                },
                {
                    "id": "evt-2",
                    "titlu": "Draft event",
                    "descriere": None,
                    "start_date": "2026-06-01T10:00:00+00:00",
                    "end_date": "2026-06-01T11:00:00+00:00",
                    "locatie_id": "loc-1",
                    "categorie_id": "cat-1",
                    "status_id": "st-draft",
                    "organizer_id": "user-1",
                    "tip_participare_id": "tp-1",
                    "max_participanti": 50,
                    "deadline_inscriere": None,
                    "link_inscriere": None,
                    "created_at": "2026-04-22T10:00:00+00:00",
                    "deleted_at": None,
                },
            ],
            "inscrieri": [
                {
                    "id": "reg-1",
                    "eveniment_id": "evt-1",
                    "user_id": "user-2",
                    "tip_participare_id": "tp-1",
                    "status_id": "st-confirmed",
                    "check_in_at": None,
                    "qr_token": None,
                    "created_at": "2026-04-22T10:00:00+00:00",
                }
            ],
        }

    def table(self, table_name: str):
        return FakeTableQuery(table_name, self.db)


client = TestClient(app)


def _override_supabase() -> FakeSupabase:
    return FakeSupabase()


def _override_admin_user() -> CurrentUser:
    return CurrentUser(user_id="admin-id", role="admin", email="admin@example.com")


def _override_any_user() -> CurrentUser:
    return CurrentUser(user_id="student-id", role="student", email="student@example.com")


def setup_function() -> None:
    app.dependency_overrides[get_events_client] = _override_supabase
    app.dependency_overrides[admin_or_organizer] = _override_admin_user
    app.dependency_overrides[get_current_user] = _override_any_user


def teardown_function() -> None:
    app.dependency_overrides.clear()


def test_list_events_only_active() -> None:
    response = client.get("/api/v1/events")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == "evt-1"


def test_list_events_filters_by_status() -> None:
    response = client.get("/api/v1/events?status_id=st-published")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["status_id"] == "st-published"


def test_list_events_limit() -> None:
    response = client.get("/api/v1/events?limit=1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_list_events_cursor() -> None:
    response = client.get("/api/v1/events?cursor_id=evt-1")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "evt-2"


def test_get_event_not_found() -> None:
    response = client.get("/api/v1/events/does-not-exist")

    assert response.status_code == 404
    assert response.json()["detail"] == "Event not found"


def test_create_event() -> None:
    payload = {
        "titlu": "New Event",
        "descriere": "desc",
        "start_date": "2026-05-05T10:00:00+00:00",
        "end_date": "2026-05-05T12:00:00+00:00",
        "locatie_id": "loc-1",
        "categorie_id": "cat-1",
        "status_id": "st-published",
        "organizer_id": "user-1",
        "tip_participare_id": "tp-1",
        "max_participanti": 42,
        "deadline_inscriere": None,
        "link_inscriere": None,
    }

    response = client.post("/api/v1/events", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "evt-new"
    assert body["titlu"] == "New Event"


def test_create_event_invalid_date_range() -> None:
    payload = {
        "titlu": "Invalid Event",
        "descriere": "desc",
        "start_date": "2026-05-05T12:00:00+00:00",
        "end_date": "2026-05-05T10:00:00+00:00",
        "locatie_id": "loc-1",
        "categorie_id": "cat-1",
        "status_id": "st-published",
        "organizer_id": "user-1",
        "tip_participare_id": "tp-1",
        "max_participanti": 10,
        "deadline_inscriere": None,
        "link_inscriere": None,
    }

    response = client.post("/api/v1/events", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "end_date must be after start_date"


def test_create_event_invalid_capacity() -> None:
    payload = {
        "titlu": "Invalid Capacity",
        "descriere": "desc",
        "start_date": "2026-05-05T10:00:00+00:00",
        "end_date": "2026-05-05T12:00:00+00:00",
        "locatie_id": "loc-1",
        "categorie_id": "cat-1",
        "status_id": "st-published",
        "organizer_id": "user-1",
        "tip_participare_id": "tp-1",
        "max_participanti": 0,
        "deadline_inscriere": None,
        "link_inscriere": None,
    }

    response = client.post("/api/v1/events", json=payload)

    assert response.status_code == 422


def test_update_event_requires_payload_fields() -> None:
    response = client.patch("/api/v1/events/evt-1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "No fields provided for update"


def test_update_event_invalid_capacity() -> None:
    response = client.patch("/api/v1/events/evt-1", json={"max_participanti": -1})

    assert response.status_code == 422


def test_delete_event() -> None:
    response = client.delete("/api/v1/events/evt-1")

    assert response.status_code == 200
    assert response.json()["detail"] == "Event deleted"


def test_list_participants() -> None:
    response = client.get("/api/v1/events/evt-1/participants")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "reg-1"
