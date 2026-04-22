from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.users_service import (
    create_user as create_user_service,
    get_user_by_id,
    list_users as list_users_service,
    update_user_by_id,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/users", tags=["users"])
admin_only = require_roles("admin")


def get_users_client() -> Client:
    return get_supabase_client()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> UserRead:
    return create_user_service(client, payload)


@router.get(
    "",
    response_model=list[UserRead],
    summary="List users",
    description="Admin-only endpoint. Returns active users using cursor-based pagination.",
)
async def list_users(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of users to return."),
    cursor_id: str | None = Query(
        default=None,
        description="Cursor for keyset pagination. Returns users with id greater than this value.",
    ),
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> list[UserRead]:
    return list_users_service(client, limit=limit, cursor_id=cursor_id)


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
    return get_user_by_id(client, user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> UserRead:
    return update_user_by_id(client, user_id, payload)
