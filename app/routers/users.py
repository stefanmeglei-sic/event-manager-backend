from fastapi import APIRouter, Depends, HTTPException, Query, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.localization import get_message
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.users_service import (
    create_user as create_user_service,
    delete_user_by_id,
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
    response_model=PaginatedResponse[UserRead],
    summary="List users",
    description="Admin-only endpoint. Returns active users using cursor-based pagination.",
)
async def list_users(
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of users to return."),
    cursor: str | None = Query(
        default=None,
        description="Cursor for keyset pagination. Format: 'created_at|id'.",
    ),
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> PaginatedResponse[UserRead]:
    cursor_created_at: str | None = None
    cursor_id: str | None = None
    if cursor:
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            cursor_created_at, cursor_id = parts[0], parts[1]
    return list_users_service(client, limit=limit, cursor_created_at=cursor_created_at, cursor_id=cursor_id)


@router.get("/me/registrations", summary="Get my registrations")
async def get_my_registrations(
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_users_client),
) -> list[dict]:
    try:
        resp = (
            client.table("inscrieri")
            .select(
                "id,eveniment_id,tip_participare_id,status_id,check_in_at,qr_token,created_at,"
                "evenimente(titlu,start_date)"
            )
            .eq("user_id", current_user.user_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = resp.data or []
        result = []
        for row in rows:
            event_data = row.get("evenimente") or {}
            result.append({
                "id": row["id"],
                "eveniment_id": row["eveniment_id"],
                "event_title": event_data.get("titlu", ""),
                "event_start_date": event_data.get("start_date", ""),
                "tip_participare_id": row.get("tip_participare_id"),
                "status_id": row["status_id"],
                "check_in_at": row.get("check_in_at"),
                "qr_token": row.get("qr_token"),
                "created_at": row.get("created_at"),
            })
        return result
    except Exception as exc:
        from fastapi import HTTPException, status as http_status
        raise HTTPException(
            status_code=http_status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.users.failed_to_fetch_registrations"),
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
            detail=get_message("errors.permissions.insufficient"),
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


@router.delete("/{user_id}", response_model=MessageResponse)
async def delete_user(
    user_id: str,
    current_user: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_users_client),
) -> MessageResponse:
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_message("errors.users.cannot_delete_self"),
        )
    return delete_user_by_id(client, user_id)
