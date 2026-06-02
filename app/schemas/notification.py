from pydantic import BaseModel


class NotificationRead(BaseModel):
    id: str
    user_id: str
    eveniment_id: str | None = None
    mesaj: str
    is_read: bool
    created_at: str | None = None


class NotificationCreate(BaseModel):
    user_id: str
    mesaj: str
    eveniment_id: str | None = None
    send_email: bool = True
