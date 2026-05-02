from typing import Optional
import uuid

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comentariu: Optional[str] = None


class FeedbackOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    eveniment_id: uuid.UUID
    rating: int
    comentariu: Optional[str]
    created_at: str
