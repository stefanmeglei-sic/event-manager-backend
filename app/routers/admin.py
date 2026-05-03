from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.auth.dependencies import CurrentUser, require_roles
from app.localization import get_message
from app.schemas.common import MessageResponse
from app.schemas.lookup import LookupCreate, LookupRead, LookupUpdate, StatusCreate, StatusRead, StatusUpdate
from app.services.lookups_service import (
    create_lookup_entry,
    delete_lookup_entry,
    update_lookup_entry,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/admin", tags=["admin"])
admin_only = require_roles("admin")


def get_client() -> Client:
    return get_supabase_client()


# ── Event Categories ──────────────────────────────────────────────────────────

@router.post("/categories", response_model=LookupRead, status_code=201, summary="Create event category")
async def create_category(
    payload: LookupCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> LookupRead:
    return create_lookup_entry(client, "categorii_eveniment", payload.model_dump())


@router.patch("/categories/{category_id}", response_model=LookupRead, summary="Update event category")
async def update_category(
    category_id: str,
    payload: LookupUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> LookupRead:
    return update_lookup_entry(client, "categorii_eveniment", category_id, payload.model_dump())


@router.delete("/categories/{category_id}", response_model=MessageResponse, summary="Delete event category")
async def delete_category(
    category_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> MessageResponse:
    return delete_lookup_entry(client, "categorii_eveniment", category_id)


# ── Participation Types ───────────────────────────────────────────────────────

@router.post("/participation-types", response_model=LookupRead, status_code=201, summary="Create participation type")
async def create_participation_type(
    payload: LookupCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> LookupRead:
    return create_lookup_entry(client, "tip_participare", payload.model_dump())


@router.patch("/participation-types/{type_id}", response_model=LookupRead, summary="Update participation type")
async def update_participation_type(
    type_id: str,
    payload: LookupUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> LookupRead:
    return update_lookup_entry(client, "tip_participare", type_id, payload.model_dump())


@router.delete("/participation-types/{type_id}", response_model=MessageResponse, summary="Delete participation type")
async def delete_participation_type(
    type_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> MessageResponse:
    return delete_lookup_entry(client, "tip_participare", type_id)


# ── Event Statuses ────────────────────────────────────────────────────────────

@router.post("/statuses", response_model=StatusRead, status_code=201, summary="Create event status")
async def create_status(
    payload: StatusCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> StatusRead:
    try:
        response = client.table("statusuri").insert(payload.model_dump()).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=get_message("errors.lookups.status_not_created"))
        return StatusRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=get_message("errors.lookups.failed_to_create_status")) from exc


@router.patch("/statuses/{status_id}", response_model=StatusRead, summary="Update event status")
async def update_status(
    status_id: str,
    payload: StatusUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> StatusRead:
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=get_message("errors.lookups.no_fields_to_update"))
    try:
        response = client.table("statusuri").update(updates).eq("id", status_id).execute()
        rows = response.data or []
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=get_message("errors.lookups.status_not_found"))
        return StatusRead(**rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=get_message("errors.lookups.failed_to_update_status")) from exc


@router.delete("/statuses/{status_id}", response_model=MessageResponse, summary="Delete event status")
async def delete_status(
    status_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> MessageResponse:
    return delete_lookup_entry(client, "statusuri", status_id)
