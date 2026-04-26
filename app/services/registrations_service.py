from datetime import UTC, datetime

from fastapi import HTTPException, status
from supabase import Client

from app.auth.dependencies import CurrentUser
from app.schemas.registration import RegistrationCreate, RegistrationRead


def get_status_id(client: Client, status_name: str) -> str:
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


def to_registration_read(row: dict) -> RegistrationRead:
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


def register_to_event(
    client: Client,
    *,
    event_id: str,
    payload: RegistrationCreate,
    current_user: CurrentUser,
) -> RegistrationRead:
    try:
        # Fetch event for deadline and capacity checks
        event_resp = (
            client.table("evenimente")
            .select("max_participanti,deadline_inscriere")
            .eq("id", event_id)
            .limit(1)
            .execute()
        )
        event_rows = event_resp.data or []
        if not event_rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found",
            )
        event = event_rows[0]

        # Deadline check
        deadline = event.get("deadline_inscriere")
        if deadline:
            if isinstance(deadline, str):
                from datetime import timezone
                deadline_dt = datetime.fromisoformat(deadline)
                if deadline_dt.tzinfo is None:
                    deadline_dt = deadline_dt.replace(tzinfo=UTC)
            else:
                deadline_dt = deadline
            if datetime.now(UTC) > deadline_dt:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Registration deadline has passed",
                )

        # Capacity check
        max_p = event.get("max_participanti")
        if max_p is not None:
            cancelled_status_id = get_status_id(client, "cancelled")
            count_resp = (
                client.table("inscrieri")
                .select("id")
                .eq("eveniment_id", event_id)
                .neq("status_id", cancelled_status_id)
                .execute()
            )
            current_count = len(count_resp.data or [])
            if current_count >= max_p:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Event is at full capacity",
                )

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

        pending_status_id = get_status_id(client, "pending")
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
        return to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to register for event",
        ) from exc


def cancel_registration(
    client: Client,
    *,
    event_id: str,
    registration_id: str,
    current_user: CurrentUser,
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

        cancelled_status_id = get_status_id(client, "cancelled")
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
        return to_registration_read(updated_rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to cancel registration",
        ) from exc


def confirm_registration(
    client: Client,
    *,
    event_id: str,
    registration_id: str,
) -> RegistrationRead:
    try:
        confirmed_status_id = get_status_id(client, "confirmed")
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
        return to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to confirm registration",
        ) from exc


def check_in_registration(
    client: Client,
    *,
    event_id: str,
    registration_id: str,
) -> RegistrationRead:
    try:
        checked_in_status_id = get_status_id(client, "checked_in")
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
        return to_registration_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to check in registration",
        ) from exc
