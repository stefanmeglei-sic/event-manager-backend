from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import get_settings
from app.localization import get_message


security = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user_id: str
    role: str
    email: str | None = None
    nume: str | None = None


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> CurrentUser:
    settings = get_settings()

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.missing_bearer_token"),
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.invalid_token"),
        ) from exc

    user_id = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")
    nume = payload.get("nume")

    if not user_id or not role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=get_message("errors.auth.token_payload_missing_claims"),
        )

    return CurrentUser(user_id=user_id, role=role, email=email, nume=nume)


def require_roles(*allowed_roles: str):
    def _checker(current_user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=get_message("errors.permissions.insufficient"),
            )
        return current_user

    return _checker
