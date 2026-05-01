from datetime import UTC, datetime

from fastapi import HTTPException, status
from supabase import Client

from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.schemas.registration import RegistrationRead


def _base_event_select(client: Client):
    return (
        client.table("evenimente")
        .select(
            "id,titlu,descriere,start_date,end_date,locatie_id,categorie_id,status_id,"
            "organizer_id,tip_participare_id,max_participanti,deadline_inscriere,"
            "link_inscriere,created_at,deleted_at"
        )
        .is_("deleted_at", None)
    )


def _validate_event_create(payload: EventCreate) -> None:
    if payload.end_date <= payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date",
        )
    if payload.max_participanti is not None and payload.max_participanti <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_participanti must be greater than 0",
        )
    if payload.deadline_inscriere is not None and payload.deadline_inscriere > payload.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="deadline_inscriere must be before or equal to start_date",
        )


def _validate_event_update(payload: EventUpdate) -> None:
    if (
        payload.start_date is not None
        and payload.end_date is not None
        and payload.end_date <= payload.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_date must be after start_date",
        )
    if payload.max_participanti is not None and payload.max_participanti <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_participanti must be greater than 0",
        )
    if (
        payload.deadline_inscriere is not None
        and payload.start_date is not None
        and payload.deadline_inscriere > payload.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="deadline_inscriere must be before or equal to start_date",
        )

def list_events(
    client: Client,
    *,
    status_id: str | None,
    categorie_id: str | None,
    limit: int,
    cursor_created_at: str | None,
    cursor_id: str | None,
) -> PaginatedResponse[EventRead]:
    try:
        query = _base_event_select(client)
        if status_id:
            query = query.eq("status_id", status_id)
        if categorie_id:
            query = query.eq("categorie_id", categorie_id)
        if cursor_created_at and cursor_id:
            query = query.or_(
                f"created_at.gt.{cursor_created_at},"
                f"and(created_at.eq.{cursor_created_at},id.gt.{cursor_id})"
            )
        response = query.order("created_at").order("id").limit(limit).execute()
        items = [EventRead(**row) for row in (response.data or [])]
        next_cursor: str | None = None
        if len(items) == limit:
            last = items[-1]
            next_cursor = f"{last.created_at.isoformat()}|{last.id}"
        return PaginatedResponse(items=items, next_cursor=next_cursor)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch events",
        ) from exc


def create_event(client: Client, payload: EventCreate) -> EventRead:
    _validate_event_create(payload)
    try:
        response = (
            client.table("evenimente")
            .insert(payload.model_dump(mode="json"))
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=500, detail="Event was not created")
        return EventRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create event",
        ) from exc


def get_event_by_id(client: Client, event_id: str) -> EventRead:
    try:
        response = _base_event_select(client).eq("id", event_id).limit(1).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return EventRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch event",
        ) from exc


def update_event_by_id(client: Client, event_id: str, payload: EventUpdate, *, current_user=None) -> EventRead:
    updates = payload.model_dump(mode="json", exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

    _validate_event_update(payload)

    if current_user is not None and current_user.role != "admin":
        event = get_event_by_id(client, event_id)
        if event.organizer_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own events")

    try:
        response = (
            client.table("evenimente")
            .update(updates)
            .eq("id", event_id)
            .is_("deleted_at", None)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return EventRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update event",
        ) from exc


def delete_event_by_id(client: Client, event_id: str, *, current_user=None) -> MessageResponse:
    if current_user is not None and current_user.role != "admin":
        event = get_event_by_id(client, event_id)
        if event.organizer_id != current_user.user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own events")

    try:
        response = (
            client.table("evenimente")
            .update({"deleted_at": datetime.now(UTC).isoformat()})
            .eq("id", event_id)
            .is_("deleted_at", None)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        return MessageResponse(detail="Event deleted")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete event",
        ) from exc


def list_event_participants(client: Client, event_id: str) -> list[RegistrationRead]:
    try:
        response = (
            client.table("inscrieri")
            .select(
                "id,eveniment_id,user_id,tip_participare_id,status_id,"
                "check_in_at,qr_token,created_at"
            )
            .eq("eveniment_id", event_id)
            .order("created_at")
            .execute()
        )
        return [RegistrationRead(**row) for row in (response.data or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch participants",
        ) from exc
