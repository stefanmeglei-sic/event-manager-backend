from fastapi import HTTPException, status
from passlib.context import CryptContext
from supabase import Client

from app.localization import get_message
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def to_user_read(row: dict) -> UserRead:
    return UserRead(
        id=row["id"],
        email=row["email"],
        nume=row.get("nume"),
        rol_id=row["rol_id"],
        created_at=row.get("created_at"),
    )


def list_users(
    client: Client,
    *,
    limit: int,
    cursor_created_at: str | None,
    cursor_id: str | None,
) -> PaginatedResponse[UserRead]:
    try:
        query = (
            client.table("utilizatori")
            .select("id,email,nume,rol_id,created_at,deleted_at")
            .is_("deleted_at", None)
        )

        if cursor_created_at and cursor_id:
            query = query.or_(
                f"created_at.gt.{cursor_created_at},"
                f"and(created_at.eq.{cursor_created_at},id.gt.{cursor_id})"
            )

        response = query.order("created_at").order("id").limit(limit).execute()
        items = [to_user_read(row) for row in (response.data or [])]
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
            detail=get_message("errors.users.failed_to_fetch_users"),
        ) from exc


def create_user(client: Client, payload: UserCreate) -> UserRead:
    try:
        response = (
            client.table("utilizatori")
            .insert(
                {
                    "email": payload.email,
                    "nume": payload.nume,
                    "password_hash": pwd_context.hash(payload.password),
                    "rol_id": payload.rol_id,
                }
            )
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=500, detail=get_message("errors.users.user_not_created"))
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.users.failed_to_create_user"),
        ) from exc


def get_user_by_id(client: Client, user_id: str) -> UserRead:
    try:
        response = (
            client.table("utilizatori")
            .select("id,email,nume,rol_id,created_at,deleted_at")
            .eq("id", user_id)
            .is_("deleted_at", None)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("errors.users.user_not_found"),
            )
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.users.failed_to_fetch_user"),
        ) from exc


def update_user_by_id(client: Client, user_id: str, payload: UserUpdate) -> UserRead:
    updates = payload.model_dump(exclude_none=True)
    if "password" in updates:
        updates["password_hash"] = pwd_context.hash(updates.pop("password"))
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_message("errors.users.no_fields_for_update"),
        )

    try:
        response = (
            client.table("utilizatori")
            .update(updates)
            .eq("id", user_id)
            .is_("deleted_at", None)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=get_message("errors.users.user_not_found"),
            )
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.users.failed_to_update_user"),
        ) from exc
