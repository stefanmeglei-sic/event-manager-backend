from datetime import UTC, datetime

from fastapi import HTTPException, status
from supabase import Client

from app.schemas.common import MessageResponse
from app.schemas.lookup import LocationCreate, LocationRead, LocationUpdate, LookupRead


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


def create_location(client: Client, payload: LocationCreate) -> LocationRead:
    if payload.capacitate is not None and payload.capacitate <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="capacitate must be greater than 0",
        )
    try:
        response = client.table("locatii").insert(payload.model_dump(mode="json")).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Location was not created")
        row = rows[0]
        return LocationRead(
            id=row["id"],
            nume_sala=row["nume_sala"],
            corp_cladire=row.get("corp_cladire"),
            capacitate=row.get("capacitate"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to create location",
        ) from exc


def update_location_by_id(client: Client, location_id: str, payload: LocationUpdate) -> LocationRead:
    updates = payload.model_dump(mode="json", exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update",
        )
    if payload.capacitate is not None and payload.capacitate <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="capacitate must be greater than 0",
        )
    try:
        response = (
            client.table("locatii")
            .update(updates)
            .eq("id", location_id)
            .is_("deleted_at", "null")
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        row = rows[0]
        return LocationRead(
            id=row["id"],
            nume_sala=row["nume_sala"],
            corp_cladire=row.get("corp_cladire"),
            capacitate=row.get("capacitate"),
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to update location",
        ) from exc


def delete_location_by_id(client: Client, location_id: str) -> MessageResponse:
    try:
        response = (
            client.table("locatii")
            .update({"deleted_at": datetime.now(UTC).isoformat()})
            .eq("id", location_id)
            .is_("deleted_at", "null")
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found")
        return MessageResponse(detail="Location deleted")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to delete location",
        ) from exc
