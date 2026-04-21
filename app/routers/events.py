from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse
from app.schemas.event import EventCreate, EventUpdate


router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=MessageResponse)
async def list_events(
    status_id: str | None = Query(default=None),
    categorie_id: str | None = Query(default=None),
) -> MessageResponse:
    _ = status_id
    _ = categorie_id
    return MessageResponse(detail="Not implemented yet")


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_event(
    payload: EventCreate,
    _: CurrentUser = Depends(require_roles("admin", "organizer")),
) -> MessageResponse:
    _ = payload
    return MessageResponse(detail="Not implemented yet")


@router.get("/{event_id}", response_model=MessageResponse)
async def get_event(event_id: str) -> MessageResponse:
    _ = event_id
    return MessageResponse(detail="Not implemented yet")


@router.patch("/{event_id}", response_model=MessageResponse)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    _: CurrentUser = Depends(require_roles("admin", "organizer")),
) -> MessageResponse:
    _ = event_id
    _ = payload
    return MessageResponse(detail="Not implemented yet")


@router.delete("/{event_id}", response_model=MessageResponse)
async def delete_event(
    event_id: str,
    _: CurrentUser = Depends(require_roles("admin", "organizer")),
) -> MessageResponse:
    _ = event_id
    return MessageResponse(detail="Not implemented yet")


@router.get("/{event_id}/participants", response_model=MessageResponse)
async def list_participants(
    event_id: str,
    _: CurrentUser = Depends(get_current_user),
) -> MessageResponse:
    _ = event_id
    return MessageResponse(detail="Not implemented yet")
