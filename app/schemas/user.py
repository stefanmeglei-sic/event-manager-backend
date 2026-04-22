from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol_id: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    rol_id: str | None = None


class UserRead(BaseModel):
    id: str
    email: EmailStr
    rol_id: str
    created_at: datetime | None = None
