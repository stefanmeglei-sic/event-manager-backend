from fastapi import APIRouter, Depends, Query, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse, PaginatedResponse
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


@router.get(
    "",
    response_model=PaginatedResponse[EventRead],
    summary="List events",
    description="Returns active events with optional filters and cursor-based pagination.",
)
async def list_events(
    status_id: str | None = Query(default=None, description="Filter by event status id."),
    categorie_id: str | None = Query(default=None, description="Filter by event category id."),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum number of events to return."),
    cursor: str | None = Query(
        default=None,
        description="Cursor for keyset pagination. Format: 'created_at|id'.",
    ),
    client: Client = Depends(get_events_client),
) -> PaginatedResponse[EventRead]:
    cursor_created_at: str | None = None
    cursor_id: str | None = None
    if cursor:
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            cursor_created_at, cursor_id = parts[0], parts[1]
    return list_events_service(
        client,
        status_id=status_id,
        categorie_id=categorie_id,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description="Creates a new event. Requires admin or organizer role.",
)
async def create_event(
    payload: EventCreate,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return create_event_service(client, payload)


@router.get("/{event_id}", response_model=EventRead, summary="Get event by id")
async def get_event(
    event_id: str,
    client: Client = Depends(get_events_client),
) -> EventRead:
    return get_event_by_id(client, event_id)


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    summary="Update event",
    description="Updates mutable event fields. Requires admin or organizer role.",
)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    current_user: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return update_event_by_id(client, event_id, payload, current_user=current_user)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    summary="Delete event",
    description="Soft-deletes an event by setting deleted_at. Requires admin or organizer role.",
)
async def delete_event(
    event_id: str,
    current_user: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> MessageResponse:
    return delete_event_by_id(client, event_id, current_user=current_user)


@router.get(
    "/{event_id}/participants",
    response_model=list[RegistrationRead],
    summary="List event participants",
)
async def list_participants(
    event_id: str,
    _: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_events_client),
) -> list[RegistrationRead]:
    return list_event_participants(client, event_id)
