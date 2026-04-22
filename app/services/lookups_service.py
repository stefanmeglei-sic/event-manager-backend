from fastapi import HTTPException, status
from supabase import Client

from app.schemas.lookup import LocationRead, LookupRead


def read_lookup_table(
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


def read_locations(client: Client) -> list[LocationRead]:
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
