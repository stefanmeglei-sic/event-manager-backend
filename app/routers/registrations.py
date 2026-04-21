from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.registration import RegistrationCreate, RegistrationRead
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/events/{event_id}/registrations", tags=["registrations"])
admin_or_organizer = require_roles("admin", "organizer")


def get_registrations_client() -> Client:
    return get_supabase_client()


def _get_status_id(client: Client, status_name: str) -> str:
    response = (
        client.table("statusuri")
        .select("id")
        .eq("nume", status_name)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Missing status: {status_name}",
        )
    return rows[0]["id"]


def _to_registration_read(row: dict) -> RegistrationRead:
    return RegistrationRead(
        id=row["id"],
        eveniment_id=row["eveniment_id"],
        user_id=row["user_id"],
        tip_participare_id=row["tip_participare_id"],
        status_id=row["status_id"],
        check_in_at=row.get("check_in_at"),
        qr_token=row.get("qr_token"),
        created_at=row.get("created_at"),
    )


@router.post("", response_model=RegistrationRead, status_code=status.HTTP_201_CREATED)
async def register_to_event(
    event_id: str,
    payload: RegistrationCreate,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    try:
        existing = (
            client.table("inscrieri")
            .select("id,status_id")
            .eq("eveniment_id", event_id)
            .eq("user_id", current_user.user_id)
            .limit(1)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already registered to this event",
            )

        pending_status_id = _get_status_id(client, "pending")
        response = (
            client.table("inscrieri")
            .insert(
                {
                    "eveniment_id": event_id,
                    "user_id": current_user.user_id,
                    "tip_participare_id": payload.tip_participare_id,
                    "status_id": pending_status_id,
                }
            )
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=500, detail="Registration was not created")
        return _to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to register for event",
        ) from exc


@router.patch("/{registration_id}/cancel", response_model=RegistrationRead)
async def cancel_registration(
    event_id: str,
    registration_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    try:
        existing = (
            client.table("inscrieri")
            .select("id,eveniment_id,user_id,tip_participare_id,status_id,check_in_at,qr_token,created_at")
            .eq("id", registration_id)
            .eq("eveniment_id", event_id)
            .limit(1)
            .execute()
        )
        rows = existing.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )
        registration = rows[0]
        if current_user.role not in ("admin", "organizer") and registration["user_id"] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        cancelled_status_id = _get_status_id(client, "cancelled")
        response = (
            client.table("inscrieri")
            .update({"status_id": cancelled_status_id})
            .eq("id", registration_id)
            .eq("eveniment_id", event_id)
            .execute()
        )
        updated_rows = response.data or []
        if not updated_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )
        return _to_registration_read(updated_rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel registration",
        ) from exc


@router.patch("/{registration_id}/confirm", response_model=RegistrationRead)
async def confirm_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    try:
        confirmed_status_id = _get_status_id(client, "confirmed")
        response = (
            client.table("inscrieri")
            .update({"status_id": confirmed_status_id})
            .eq("id", registration_id)
            .eq("eveniment_id", event_id)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )
        return _to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to confirm registration",
        ) from exc


@router.patch("/{registration_id}/check-in", response_model=RegistrationRead)
async def check_in_registration(
    event_id: str,
    registration_id: str,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_registrations_client),
) -> RegistrationRead:
    try:
        checked_in_status_id = _get_status_id(client, "checked_in")
        response = (
            client.table("inscrieri")
            .update(
                {
                    "status_id": checked_in_status_id,
                    "check_in_at": datetime.now(UTC).isoformat(),
                }
            )
            .eq("id", registration_id)
            .eq("eveniment_id", event_id)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registration not found",
            )
        return _to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to check in registration",
        ) from exc
