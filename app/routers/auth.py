from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from jose import jwt
from passlib.context import CryptContext
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user
from app.config import Settings, get_settings
from app.localization import get_message
from app.schemas.auth import GoogleLoginRequest, LoginRequest, TokenResponse
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/auth", tags=["auth"])


GoogleTokenVerifier = Callable[[str, str], dict[str, Any]]

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_auth_settings() -> Settings:
    return get_settings()


def get_auth_client() -> Client:
    return get_supabase_client()


def _verify_google_id_token(token: str, client_id: str) -> dict[str, Any]:
    return google_id_token.verify_oauth2_token(
        token,
        google_requests.Request(),
        client_id,
    )


def get_google_token_verifier() -> GoogleTokenVerifier:
    return _verify_google_id_token


def _issue_access_token(
    settings: Settings,
    *,
    user_id: str,
    role: str,
    email: str,
) -> TokenResponse:
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.jwt_expires_minutes)
    token = jwt.encode(
        {
            "sub": user_id,
            "role": role,
            "email": email,
            "exp": expires_at,
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return TokenResponse(access_token=token)


def _get_role_id_by_name(client: Client, role_name: str) -> str:
    response = client.table("roluri").select("id").eq("nume", role_name).limit(1).execute()
    rows = response.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("errors.roles.missing_role", role_name=role_name),
        )
    return rows[0]["id"]


def _get_role_name_by_id(client: Client, role_id: str | None) -> str:
    if not role_id:
        return "student"
    response = client.table("roluri").select("nume").eq("id", role_id).limit(1).execute()
    rows = response.data or []
    if not rows:
        return "student"
    return rows[0]["nume"]


def _get_or_create_user_from_google_email(client: Client, email: str) -> tuple[str, str]:
    existing = (
        client.table("utilizatori")
        .select("id,rol_id")
        .eq("email", email)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )
    rows = existing.data or []
    if rows:
        user_id = rows[0]["id"]
        role_name = _get_role_name_by_id(client, rows[0].get("rol_id"))
        return user_id, role_name

    student_role_id = _get_role_id_by_name(client, "student")
    created = (
        client.table("utilizatori")
        .insert(
            {
                "email": email,
                "password_hash": None,
                "rol_id": student_role_id,
            }
        )
        .execute()
    )
    created_rows = created.data or []
    if not created_rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("errors.users.user_not_created"),
        )
    return created_rows[0]["id"], "student"


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    settings: Settings = Depends(get_auth_settings),
    client: Client = Depends(get_auth_client),
) -> TokenResponse:
    try:
        response = (
            client.table("utilizatori")
            .select("id,email,password_hash,rol_id")
            .eq("email", payload.email)
            .is_("deleted_at", None)
            .limit(1)
            .execute()
        )
        rows = response.data or []
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.auth.failed_to_authenticate"),
        ) from exc

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.invalid_credentials"),
        )

    user = rows[0]
    password_hash = user.get("password_hash")
    if not password_hash or not _pwd_context.verify(payload.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.invalid_credentials"),
        )

    role = _get_role_name_by_id(client, user.get("rol_id"))
    return _issue_access_token(
        settings,
        user_id=user["id"],
        role=role,
        email=user["email"],
    )


@router.post("/google", response_model=TokenResponse)
async def google_login(
    payload: GoogleLoginRequest,
    settings: Settings = Depends(get_auth_settings),
    client: Client = Depends(get_auth_client),
    verify_token: GoogleTokenVerifier = Depends(get_google_token_verifier),
) -> TokenResponse:
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=get_message("errors.auth.google_not_configured"),
        )

    try:
        google_payload = verify_token(payload.id_token, settings.google_client_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.invalid_google_token"),
        ) from exc

    email = str(google_payload.get("email", "")).strip().lower()
    email_verified = bool(google_payload.get("email_verified", False))

    if not email or not email_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.google_email_not_verified"),
        )

    domain = email.split("@")[-1] if "@" in email else ""
    if domain != "student.usv.ro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=get_message("errors.auth.google_restricted_domain"),
        )

    try:
        user_id, role = _get_or_create_user_from_google_email(client, email)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.auth.failed_to_authenticate_google"),
        ) from exc

    return _issue_access_token(
        settings,
        user_id=user_id,
        role=role,
        email=email,
    )


@router.get("/me")
async def me(current_user: CurrentUser = Depends(get_current_user)) -> dict[str, str | None]:
    return {
        "id": current_user.user_id,
        "role": current_user.role,
        "email": current_user.email,
    }
