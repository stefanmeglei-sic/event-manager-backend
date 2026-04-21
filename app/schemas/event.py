from datetime import datetime

from pydantic import BaseModel


class EventCreate(BaseModel):
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


class EventUpdate(BaseModel):
    titlu: str | None = None
    descriere: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    locatie_id: str | None = None
    categorie_id: str | None = None
    status_id: str | None = None
    tip_participare_id: str | None = None
    max_participanti: int | None = None
    deadline_inscriere: datetime | None = None
    link_inscriere: str | None = None


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
