from fastapi import APIRouter, Depends, status
from supabase import Client

from app.auth.dependencies import CurrentUser, require_roles
from app.localization import get_message
from app.schemas.common import MessageResponse
from app.schemas.lookup import LookupCreate, LookupRead, LookupUpdate
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
    return update_lookup_entry(client, "categorii_eveniment", category_id, payload.model_dump(), active_only=True)


@router.delete("/categories/{category_id}", response_model=MessageResponse, summary="Delete event category")
async def delete_category(
    category_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> MessageResponse:
    return delete_lookup_entry(client, "categorii_eveniment", category_id, soft_delete=True)


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
    return update_lookup_entry(client, "tip_participare", type_id, payload.model_dump(), active_only=True)


@router.delete("/participation-types/{type_id}", response_model=MessageResponse, summary="Delete participation type")
async def delete_participation_type(
    type_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> MessageResponse:
    return delete_lookup_entry(client, "tip_participare", type_id, soft_delete=True)
