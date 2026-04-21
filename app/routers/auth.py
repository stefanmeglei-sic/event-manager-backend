from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from jose import jwt

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import get_settings
from app.schemas.auth import LoginRequest, TokenResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    # Placeholder implementation for checkpoint 1.
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    token = jwt.encode(
        {
            "sub": "placeholder-user-id",
            "role": "admin",
            "email": payload.email,
            "exp": expires_at,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return TokenResponse(access_token=token)


@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, str | None]:
    return {
        "id": current_user.user_id,
        "role": current_user.role,
        "email": current_user.email,
    }
