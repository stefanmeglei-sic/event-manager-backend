from fastapi import APIRouter, Depends, status

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse
from app.schemas.registration import RegistrationCreate


router = APIRouter(prefix="/events/{event_id}/registrations", tags=["registrations"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register_to_event(
    event_id: str,
    payload: RegistrationCreate,
    _: CurrentUser = Depends(get_current_user),
) -> MessageResponse:
    _ = event_id
    _ = payload
    return MessageResponse(detail="Not implemented yet")


@router.patch("/{registration_id}/cancel", response_model=MessageResponse)
async def cancel_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(get_current_user),
) -> MessageResponse:
    _ = event_id
    _ = registration_id
    return MessageResponse(detail="Not implemented yet")


@router.patch("/{registration_id}/confirm", response_model=MessageResponse)
async def confirm_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(require_roles("admin", "organizer")),
) -> MessageResponse:
    _ = event_id
    _ = registration_id
    return MessageResponse(detail="Not implemented yet")


@router.patch("/{registration_id}/check-in", response_model=MessageResponse)
async def check_in_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(require_roles("admin", "organizer")),
) -> MessageResponse:
    _ = event_id
    _ = registration_id
    return MessageResponse(detail="Not implemented yet")
