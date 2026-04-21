from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    rol_id: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = None
    rol_id: str | None = None


class UserRead(BaseModel):
    id: str
    email: EmailStr
    rol_id: str
    created_at: datetime | None = None
