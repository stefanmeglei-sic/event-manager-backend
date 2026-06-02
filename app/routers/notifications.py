from fastapi import APIRouter, Depends, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.notifications_service import (
    create_notification,
    list_notifications,
    mark_all_notifications_read,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/notifications", tags=["notifications"])
admin_or_organizer = require_roles("admin", "organizer")


def get_notifications_client() -> Client:
    return get_supabase_client()


@router.get("", response_model=list[NotificationRead], summary="List notifications for current user")
async def get_my_notifications(
    limit: int = 20,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_notifications_client),
) -> list[NotificationRead]:
    return list_notifications(client, user_id=current_user.user_id, limit=limit)


@router.patch("/read-all", response_model=MessageResponse, summary="Mark all notifications as read")
async def mark_my_notifications_as_read(
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_notifications_client),
) -> MessageResponse:
    return mark_all_notifications_read(client, user_id=current_user.user_id)


@router.post("", response_model=NotificationRead, status_code=status.HTTP_201_CREATED, summary="Create notification")
async def create_notification_entry(
    payload: NotificationCreate,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_notifications_client),
) -> NotificationRead:
    return create_notification(client, payload)
