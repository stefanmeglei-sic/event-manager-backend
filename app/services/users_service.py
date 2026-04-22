from fastapi import HTTPException, status
from passlib.context import CryptContext
from supabase import Client

from app.schemas.user import UserCreate, UserRead, UserUpdate


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def to_user_read(row: dict) -> UserRead:
    return UserRead(
        id=row["id"],
        email=row["email"],
        rol_id=row["rol_id"],
        created_at=row.get("created_at"),
    )


def list_users(client: Client, *, limit: int, cursor_id: str | None) -> list[UserRead]:
    try:
        query = (
            client.table("utilizatori")
            .select("id,email,rol_id,created_at,deleted_at")
            .is_("deleted_at", None)
        )

        if cursor_id:
            query = query.gt("id", cursor_id)

        response = query.order("id").limit(limit).execute()
        return [to_user_read(row) for row in (response.data or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch users",
        ) from exc


def create_user(client: Client, payload: UserCreate) -> UserRead:
    try:
        response = (
            client.table("utilizatori")
            .insert(
                {
                    "email": payload.email,
                    "password_hash": pwd_context.hash(payload.password),
                    "rol_id": payload.rol_id,
                }
            )
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=500, detail="User was not created")
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create user",
        ) from exc


def get_user_by_id(client: Client, user_id: str) -> UserRead:
    try:
        response = (
            client.table("utilizatori")
            .select("id,email,rol_id,created_at,deleted_at")
            .eq("id", user_id)
            .is_("deleted_at", None)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch user",
        ) from exc


def update_user_by_id(client: Client, user_id: str, payload: UserUpdate) -> UserRead:
    updates = payload.model_dump(exclude_none=True)
    if "password" in updates:
        updates["password_hash"] = pwd_context.hash(updates.pop("password"))
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
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
                detail="User not found",
            )
        return to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update user",
        ) from exc
