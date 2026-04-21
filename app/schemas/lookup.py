from pydantic import BaseModel


class LookupRead(BaseModel):
    id: str
    nume: str


class LocationRead(BaseModel):
    id: str
    nume_sala: str
    corp_cladire: str | None = None
    capacitate: int | None = None
