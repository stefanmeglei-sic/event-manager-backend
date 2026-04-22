from fastapi import APIRouter, Depends, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.registration import RegistrationCreate, RegistrationRead
from app.services.registrations_service import (
    cancel_registration as cancel_registration_service,
    check_in_registration as check_in_registration_service,
    confirm_registration as confirm_registration_service,
    register_to_event as register_to_event_service,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/events/{event_id}/registrations", tags=["registrations"])
admin_or_organizer = require_roles("admin", "organizer")


def get_registrations_client() -> Client:
    return get_supabase_client()


@router.post("", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
async def register_to_event(
    event_id: str,
    payload: RegistrationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    return register_to_event_service(
        client,
        event_id=event_id,
        payload=payload,
        current_user=current_user,
    )


@router.patch("/{registration_id}/cancel", response_model=RegistrationRead)
async def cancel_registration(
    event_id: str,
    registration_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    return cancel_registration_service(
        client,
        event_id=event_id,
        registration_id=registration_id,
        current_user=current_user,
    )


@router.patch("/{registration_id}/confirm", response_model=RegistrationRead)
async def confirm_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    return confirm_registration_service(
        client,
        event_id=event_id,
        registration_id=registration_id,
    )


@router.patch("/{registration_id}/check-in", response_model=RegistrationRead)
async def check_in_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    return check_in_registration_service(
        client,
        event_id=event_id,
        registration_id=registration_id,
    )
