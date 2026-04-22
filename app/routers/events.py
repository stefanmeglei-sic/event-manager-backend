from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse
from app.schemas.event import EventCreate, EventRead, EventUpdate
from app.schemas.registration import RegistrationRead
from app.services.events_service import (
    create_event as create_event_service,
    delete_event_by_id,
    get_event_by_id,
    list_event_participants,
    list_events as list_events_service,
    update_event_by_id,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/events", tags=["events"])
admin_or_organizer = require_roles("admin", "organizer")


def get_events_client() -> Client:
    return get_supabase_client()


@router.get("", response_model=list[EventRead])
async def list_events(
    status_id: str | None = Query(default=None),
    categorie_id: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=200),
    client: Client = Depends(get_events_client),
) -> list[EventRead]:
    return list_events_service(
        client,
        status_id=status_id,
        categorie_id=categorie_id,
        limit=limit,
    )


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return create_event_service(client, payload)


@router.get("/{event_id}", response_model=EventRead)
async def get_event(
    event_id: str,
    client: Client = Depends(get_events_client),
) -> EventRead:
    return get_event_by_id(client, event_id)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return update_event_by_id(client, event_id, payload)


@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: str,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> MessageResponse:
    return delete_event_by_id(client, event_id)


@router.get("/{event_id}/participants", response_model=list[RegistrationRead])
async def list_participants(
    event_id: str,
    _: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_events_client),
) -> list[RegistrationRead]:
    return list_event_participants(client, event_id)
