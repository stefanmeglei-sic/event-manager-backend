from datetime import datetime

from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    titlu: str = Field(min_length=3, max_length=200, description="Event title")
    descriere: str | None = None
    descriere: str | None = Field(default=None, max_length=5000, description="Event description")
    start_date: datetime
    end_date: datetime
    locatie_id: str | None = None
    categorie_id: str
    status_id: str
    organizer_id: str
    tip_participare_id: str
    max_participanti: int | None = Field(default=None, gt=0, description="Maximum participant capacity")
    deadline_inscriere: datetime | None = None
    link_inscriere: str | None = Field(default=None, max_length=2048, description="Optional external registration URL")


class EventUpdate(BaseModel):
    titlu: str | None = Field(default=None, min_length=3, max_length=200)
    descriere: str | None = Field(default=None, max_length=5000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    locatie_id: str | None = None
    categorie_id: str | None = None
    status_id: str | None = None
    tip_participare_id: str | None = None
    max_participanti: int | None = Field(default=None, gt=0)
    deadline_inscriere: datetime | None = None
    link_inscriere: str | None = Field(default=None, max_length=2048)


class EventRead(BaseModel):
    id: str
    titlu: str
    descriere: str | None = None
    start_date: datetime
    end_date: datetime
    locatie_id: str | None = None
    categorie_id: str
    status_id: str
    organizer_id: str
    tip_participare_id: str
    max_participanti: int | None = None
    deadline_inscriere: datetime | None = None
    link_inscriere: str | None = None
    created_at: datetime | None = None


class EventValidate(BaseModel):
    approved: bool
