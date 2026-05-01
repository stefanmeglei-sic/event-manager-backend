from pydantic import BaseModel


class LookupRead(BaseModel):
    id: str
    nume: str


class LookupCreate(BaseModel):
    nume: str


class LookupUpdate(BaseModel):
    nume: str | None = None


class StatusCreate(BaseModel):
    nume: str
    tip: str  # 'event' or 'registration'


class StatusUpdate(BaseModel):
    nume: str | None = None
    tip: str | None = None


class StatusRead(BaseModel):
    id: str
    nume: str
    tip: str


class LocationRead(BaseModel):
    id: str
    nume_sala: str
    corp_cladire: str | None = None
    capacitate: int | None = None


class LocationCreate(BaseModel):
    nume_sala: str
    corp_cladire: str | None = None
    capacitate: int | None = None


class LocationUpdate(BaseModel):
    nume_sala: str | None = None
    corp_cladire: str | None = None
    capacitate: int | None = None
