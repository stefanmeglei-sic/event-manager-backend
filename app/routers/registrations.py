import io

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.localization import get_message
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


@router.post(
    "",
    response_model=RegistrationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register to event",
)
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


@router.patch("/{registration_id}/cancel", response_model=RegistrationRead, summary="Cancel registration")
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


@router.patch("/{registration_id}/confirm", response_model=RegistrationRead, summary="Confirm registration")
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


@router.patch("/{registration_id}/check-in", response_model=RegistrationRead, summary="Check in registration")
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


@router.get(
    "/{registration_id}/qr",
    summary="Get registration ticket QR code",
    description="Returns a PNG QR code for the registration ticket. Accessible to the registrant, admin, or organizer.",
    responses={200: {"content": {"image/png": {}}}},
)
async def get_registration_qr(
    event_id: str,
    registration_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_registrations_client),
) -> StreamingResponse:
    import qrcode

    # Fetch registration
    resp = (
        client.table("inscrieri")
        .select("id,eveniment_id,user_id,qr_token")
        .eq("id", registration_id)
        .eq("eveniment_id", event_id)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    if not rows:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail=get_message("errors.registrations.registration_not_found"))

    reg = rows[0]
    # Ownership check
    if current_user.role not in ("admin", "organizer") and reg["user_id"] != current_user.user_id:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail=get_message("errors.permissions.insufficient"))

    token = reg.get("qr_token") or registration_id  # fallback to id if token missing

    img = qrcode.make(token)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")
