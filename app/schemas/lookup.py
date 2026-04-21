from pydantic import BaseModel


class LookupRead(BaseModel):
    id: str
    nume: str
