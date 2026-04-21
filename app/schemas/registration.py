from datetime import datetime

from pydantic import BaseModel


class RegistrationCreate(BaseModel):
    tip_participare_id: str


class RegistrationRead(BaseModel):
    id: str
    eveniment_id: str
    user_id: str
    tip_participare_id: str
    status_id: str
    check_in_at: datetime | None = None
    qr_token: str | None = None
    created_at: datetime | None = None
