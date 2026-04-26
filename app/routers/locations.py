from fastapi import APIRouter, Depends, status
from supabase import Client

from app.auth.dependencies import CurrentUser, require_roles
from app.schemas.common import MessageResponse
from app.schemas.lookup import LocationCreate, LocationRead, LocationUpdate
from app.services.lookups_service import (
    create_location,
    delete_location_by_id,
    read_locations,
    update_location_by_id,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/locations", tags=["locations"])
admin_only = require_roles("admin")


def get_locations_client() -> Client:
    return get_supabase_client()


@router.get("", response_model=list[LocationRead], summary="List locations")
async def list_locations(client: Client = Depends(get_locations_client)) -> list[LocationRead]:
    return read_locations(client)


@router.post("", response_model=LocationRead, status_code=status.HTTP_201_CREATED, summary="Create location")
async def create_location_route(
    payload: LocationCreate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_locations_client),
) -> LocationRead:
    return create_location(client, payload)


@router.patch("/{location_id}", response_model=LocationRead, summary="Update location")
async def update_location_route(
    location_id: str,
    payload: LocationUpdate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_locations_client),
) -> LocationRead:
    return update_location_by_id(client, location_id, payload)


@router.delete("/{location_id}", response_model=MessageResponse, summary="Delete location")
async def delete_location_route(
    location_id: str,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_locations_client),
) -> MessageResponse:
    return delete_location_by_id(client, location_id)
