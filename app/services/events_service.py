from datetime import UTC, datetime

from fastapi import HTTPException, status
from supabase import Client

from app.schemas.common import MessageResponse
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


def list_events(
    client: Client,
    *,
    status_id: str | None,
    categorie_id: str | None,
    limit: int,
) -> list[EventRead]:
    try:
        query = _base_event_select(client).order("start_date")
        if status_id:
            query = query.eq("status_id", status_id)
        if categorie_id:
            query = query.eq("categorie_id", categorie_id)
        response = query.limit(limit).execute()
        return [EventRead(**row) for row in (response.data or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch events",
        ) from exc


def create_event(client: Client, payload: EventCreate) -> EventRead:
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


def update_event_by_id(client: Client, event_id: str, payload: EventUpdate) -> EventRead:
    updates = payload.model_dump(mode="json", exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )

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


def delete_event_by_id(client: Client, event_id: str) -> MessageResponse:
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
