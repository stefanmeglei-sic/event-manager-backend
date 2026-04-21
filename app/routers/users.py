from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/users", tags=["users"])
admin_only = require_roles("admin")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_users_client() -> Client:
    return get_supabase_client()


def _to_user_read(row: dict) -> UserRead:
    return UserRead(
        id=row["id"],
        email=row["email"],
        rol_id=row["rol_id"],
        created_at=row.get("created_at"),
    )


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> UserRead:
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
        return _to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create user",
        ) from exc


@router.get("/{user_id}", response_model=UserRead)
async def get_user(
    user_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_users_client),
) -> UserRead:
    if current_user.role != "admin" and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

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
        return _to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch user",
        ) from exc


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> UserRead:
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
        return _to_user_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update user",
        ) from exc
