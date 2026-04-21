from fastapi import APIRouter

from app.schemas.common import MessageResponse


router = APIRouter(prefix="/lookups", tags=["lookups"])


@router.get("/roles", response_model=MessageResponse)
async def get_roles() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")


@router.get("/event-statuses", response_model=MessageResponse)
async def get_event_statuses() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")


@router.get("/registration-statuses", response_model=MessageResponse)
async def get_registration_statuses() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")


@router.get("/event-categories", response_model=MessageResponse)
async def get_event_categories() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")


@router.get("/locations", response_model=MessageResponse)
async def get_locations() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")


@router.get("/participation-types", response_model=MessageResponse)
async def get_participation_types() -> MessageResponse:
    return MessageResponse(detail="Not implemented yet")
