from fastapi import APIRouter, Depends, status

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate


router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _: CurrentUser = Depends(require_roles("admin")),
) -> MessageResponse:
    _ = payload
    return MessageResponse(detail="Not implemented yet")


@router.get("/{user_id}", response_model=MessageResponse)
async def get_user(
    user_id: str,
    _: CurrentUser = Depends(get_current_user),
) -> MessageResponse:
    _ = user_id
    return MessageResponse(detail="Not implemented yet")


@router.patch("/{user_id}", response_model=MessageResponse)
async def update_user(
    user_id: str,
    payload: UserUpdate,
    _: CurrentUser = Depends(require_roles("admin")),
) -> MessageResponse:
    _ = user_id
    _ = payload
    return MessageResponse(detail="Not implemented yet")
