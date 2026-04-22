from fastapi import APIRouter, Depends
from supabase import Client

from app.schemas.lookup import LocationRead, LookupRead
from app.services.lookups_service import read_locations, read_lookup_table
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/lookups", tags=["lookups"])


def get_lookup_client() -> Client:
    return get_supabase_client()


@router.get("/roles", response_model=list[LookupRead])
async def get_roles(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return read_lookup_table(client, table="roluri")


@router.get("/event-statuses", response_model=list[LookupRead])
async def get_event_statuses(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return read_lookup_table(
        client,
        table="statusuri",
        names_filter=["draft", "published", "cancelled", "completed"],
    )


@router.get("/registration-statuses", response_model=list[LookupRead])
async def get_registration_statuses(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return read_lookup_table(
        client,
        table="statusuri",
        names_filter=["pending", "confirmed", "checked_in"],
    )


@router.get("/event-categories", response_model=list[LookupRead])
async def get_event_categories(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return read_lookup_table(client, table="categorii_eveniment")


@router.get("/locations", response_model=list[LocationRead])
async def get_locations(client: Client = Depends(get_lookup_client)) -> list[LocationRead]:
    return read_locations(client)


@router.get("/participation-types", response_model=list[LookupRead])
async def get_participation_types(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return read_lookup_table(client, table="tip_participare")
