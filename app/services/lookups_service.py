from datetime import UTC, datetime

from fastapi import HTTPException, status
from supabase import Client

from app.localization import get_message
from app.schemas.common import MessageResponse
from app.schemas.lookup import LocationCreate, LocationRead, LocationUpdate, LookupRead


def _is_missing_deleted_at_error(exc: Exception) -> bool:
    return "deleted_at" in str(exc).lower() and "column" in str(exc).lower()

def read_lookup_table(
    client: Client,
    *,
    table: str,
    names_filter: list[str] | None = None,
    active_only: bool = False,
) -> list[LookupRead]:
    try:
        query = client.table(table).select("id,nume").order("nume")
        if names_filter:
            query = query.in_("nume", names_filter)
        if active_only:
            query = query.is_("deleted_at", "null")
        response = query.execute()
        return [LookupRead(**row) for row in (response.data or [])]
    except Exception as exc:
        if active_only and _is_missing_deleted_at_error(exc):
            # Backward-compatibility path for databases where the soft-delete
            # migration has not been applied yet.
            try:
                query = client.table(table).select("id,nume").order("nume")
                if names_filter:
                    query = query.in_("nume", names_filter)
                response = query.execute()
                return [LookupRead(**row) for row in (response.data or [])]
            except Exception as retry_exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=get_message("errors.lookups.failed_to_fetch_lookup_data"),
                ) from retry_exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.lookups.failed_to_fetch_lookup_data"),
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
            detail=get_message("errors.lookups.failed_to_fetch_lookup_data"),
        ) from exc


def create_location(client: Client, payload: LocationCreate) -> LocationRead:
    if payload.capacitate is not None and payload.capacitate <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_message("errors.lookups.invalid_capacity"),
        )
    try:
        response = client.table("locatii").insert(payload.model_dump(mode="json")).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=get_message("errors.lookups.location_not_created"))
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
            detail=get_message("errors.lookups.failed_to_create_location"),
        ) from exc


def update_location_by_id(client: Client, location_id: str, payload: LocationUpdate) -> LocationRead:
    updates = payload.model_dump(mode="json", exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_message("errors.lookups.no_fields_for_update"),
        )
    if payload.capacitate is not None and payload.capacitate <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=get_message("errors.lookups.invalid_capacity"),
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=get_message("errors.lookups.location_not_found"))
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
            detail=get_message("errors.lookups.failed_to_update_location"),
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=get_message("errors.lookups.location_not_found"))
        return MessageResponse(detail=get_message("errors.lookups.location_deleted"))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.lookups.failed_to_delete_location"),
        ) from exc


def create_lookup_entry(client: Client, table: str, payload: dict) -> LookupRead:
    try:
        response = client.table(table).insert(payload).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=get_message("errors.lookups.entry_not_created"))
        return LookupRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=get_message("errors.lookups.failed_to_create_entry")) from exc


def update_lookup_entry(
    client: Client,
    table: str,
    entry_id: str,
    payload: dict,
    *,
    active_only: bool = False,
) -> LookupRead:
    updates = {k: v for k, v in payload.items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=get_message("errors.lookups.no_fields_to_update"))
    try:
        query = client.table(table).update(updates).eq("id", entry_id)
        if active_only:
            query = query.is_("deleted_at", "null")
        response = query.execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=get_message("errors.lookups.entry_not_found"))
        return LookupRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=get_message("errors.lookups.failed_to_update_entry")) from exc


def delete_lookup_entry(
    client: Client,
    table: str,
    entry_id: str,
    *,
    soft_delete: bool = False,
) -> MessageResponse:
    try:
        query = client.table(table)
        if soft_delete:
            response = query.update({"deleted_at": datetime.now(UTC).isoformat()}).eq("id", entry_id).is_("deleted_at", "null").execute()
            rows = response.data or []
            if not rows:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=get_message("errors.lookups.entry_not_found"))
        else:
            query.delete().eq("id", entry_id).execute()
        return MessageResponse(detail=get_message("errors.lookups.deleted_successfully"))
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=get_message("errors.lookups.failed_to_delete_entry")) from exc
