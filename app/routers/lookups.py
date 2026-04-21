from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.schemas.lookup import LocationRead, LookupRead
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/lookups", tags=["lookups"])


def get_lookup_client() -> Client:
    return get_supabase_client()


def _read_lookup_table(
    client: Client,
    *,
    table: str,
    names_filter: list[str] | None = None,
) -> list[LookupRead]:
    try:
        query = client.table(table).select("id,nume").order("nume")
        if names_filter:
            query = query.in_("nume", names_filter)
        response = query.execute()
        return [LookupRead(**row) for row in (response.data or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch lookup data",
        ) from exc


@router.get("/roles", response_model=list[LookupRead])
async def get_roles(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return _read_lookup_table(client, table="roluri")


@router.get("/event-statuses", response_model=list[LookupRead])
async def get_event_statuses(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return _read_lookup_table(
        client,
        table="statusuri",
        names_filter=["draft", "published", "cancelled", "completed"],
    )


@router.get("/registration-statuses", response_model=list[LookupRead])
async def get_registration_statuses(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return _read_lookup_table(
        client,
        table="statusuri",
        names_filter=["pending", "confirmed", "checked_in"],
    )


@router.get("/event-categories", response_model=list[LookupRead])
async def get_event_categories(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return _read_lookup_table(client, table="categorii_eveniment")


@router.get("/locations", response_model=list[LocationRead])
async def get_locations(client: Client = Depends(get_lookup_client)) -> list[LocationRead]:
    try:
        response = (
            client.table("locatii")
            .select("id,nume_sala,corp_cladire,capacitate,deleted_at")
            .is_("deleted_at", "null")
            .order("nume_sala")
            .execute()
        )
        rows = response.data or []
        return [
            LocationRead(
                id=row["id"],
                nume_sala=row["nume_sala"],
                corp_cladire=row.get("corp_cladire"),
                capacitate=row.get("capacitate"),
            )
            for row in rows
        ]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch lookup data",
        ) from exc


@router.get("/participation-types", response_model=list[LookupRead])
async def get_participation_types(client: Client = Depends(get_lookup_client)) -> list[LookupRead]:
    return _read_lookup_table(client, table="tip_participare")
