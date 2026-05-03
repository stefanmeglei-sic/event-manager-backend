import io

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user, require_roles
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.event import EventCreate, EventRead, EventUpdate, EventValidate
from app.schemas.registration import RegistrationRead
from app.services.events_service import (
    create_event as create_event_service,
    delete_event_by_id,
    get_event_by_id,
    list_event_participants,
    list_events as list_events_service,
    update_event_by_id,
    validate_event,
)
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/events", tags=["events"])
admin_or_organizer = require_roles("admin", "organizer")
admin_only = require_roles("admin")


def get_events_client() -> Client:
    return get_supabase_client()


@router.get(
    "",
    response_model=PaginatedResponse[EventRead],
    summary="List events",
    description="Returns active events with optional filters and cursor-based pagination.",
)
async def list_events(
    status_id: str | None = Query(default=None, description="Filter by event status id."),
    categorie_id: str | None = Query(default=None, description="Filter by event category id."),
    organizer_id: str | None = Query(default=None, description="Filter by organizer user id."),
    location_id: str | None = Query(default=None, description="Filter by location id."),
    tip_participare_id: str | None = Query(default=None, description="Filter by participation type id."),
    date_from: str | None = Query(default=None, description="Filter events starting on or after this date (ISO 8601)."),
    date_to: str | None = Query(default=None, description="Filter events starting on or before this date (ISO 8601)."),
    requires_registration: bool | None = Query(default=None, description="If true, only events with limited capacity (requires registration)."),
    search: str | None = Query(default=None, description="Search events by title."),
    limit: int = Query(default=100, ge=1, le=200, description="Maximum number of events to return."),
    cursor: str | None = Query(
        default=None,
        description="Cursor for keyset pagination. Format: 'created_at|id'.",
    ),
    client: Client = Depends(get_events_client),
) -> PaginatedResponse[EventRead]:
    cursor_created_at: str | None = None
    cursor_id: str | None = None
    if cursor:
        parts = cursor.split("|", 1)
        if len(parts) == 2:
            cursor_created_at, cursor_id = parts[0], parts[1]
    return list_events_service(
        client,
        status_id=status_id,
        categorie_id=categorie_id,
        organizer_id=organizer_id,
        location_id=location_id,
        tip_participare_id=tip_participare_id,
        date_from=date_from,
        date_to=date_to,
        requires_registration=requires_registration,
        search=search,
        limit=limit,
        cursor_created_at=cursor_created_at,
        cursor_id=cursor_id,
    )


@router.post(
    "",
    response_model=EventRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description="Creates a new event. Requires admin or organizer role.",
)
async def create_event(
    payload: EventCreate,
    _: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return create_event_service(client, payload)


@router.get("/{event_id}", response_model=EventRead, summary="Get event by id")
async def get_event(
    event_id: str,
    client: Client = Depends(get_events_client),
) -> EventRead:
    return get_event_by_id(client, event_id)


@router.patch(
    "/{event_id}",
    response_model=EventRead,
    summary="Update event",
    description="Updates mutable event fields. Requires admin or organizer role.",
)
async def update_event(
    event_id: str,
    payload: EventUpdate,
    current_user: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return update_event_by_id(client, event_id, payload, current_user=current_user)


@router.delete(
    "/{event_id}",
    response_model=MessageResponse,
    summary="Delete event",
    description="Soft-deletes an event by setting deleted_at. Requires admin or organizer role.",
)
async def delete_event(
    event_id: str,
    current_user: CurrentUser = Depends(admin_or_organizer),
    client: Client = Depends(get_events_client),
) -> MessageResponse:
    return delete_event_by_id(client, event_id, current_user=current_user)


@router.patch(
    "/{event_id}/validate",
    response_model=EventRead,
    summary="Validate event",
    description="Admin approves (publishes) or rejects (cancels) an event.",
)
async def validate_event_route(
    event_id: str,
    payload: EventValidate,
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_events_client),
) -> EventRead:
    return validate_event(client, event_id, payload.approved)


@router.get(
    "/{event_id}/qr",
    summary="Get event QR code",
    description="Returns a PNG image of the QR code encoding the event URL.",
    responses={200: {"content": {"image/png": {}}}},
)
async def get_event_qr(
    event_id: str,
    client: Client = Depends(get_events_client),
) -> StreamingResponse:
    import qrcode  # local import to avoid startup failure if not installed

    get_event_by_id(client, event_id)  # 404 if not found

    url = f"http://localhost:3000/events/{event_id}"
    img = qrcode.make(url)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")


@router.get(
    "/{event_id}/participants",
    response_model=list[RegistrationRead],
    summary="List event participants",
)
async def list_participants(
    event_id: str,
    _: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_events_client),
) -> list[RegistrationRead]:
    return list_event_participants(client, event_id)


@router.get(
    "/{event_id}/ics",
    summary="Export event as ICS",
    description="Returns an iCalendar (.ics) file for the event. No authentication required.",
    responses={200: {"content": {"text/calendar": {}}}},
)
async def get_event_ics(
    event_id: str,
    client: Client = Depends(get_events_client),
) -> StreamingResponse:
    from datetime import datetime, timezone, timedelta
    from icalendar import Calendar, Event as ICalEvent

    # Fetch event
    event_resp = (
        client.table("evenimente")
        .select("id,titlu,descriere,start_date,end_date,locatie_id")
        .eq("id", event_id)
        .limit(1)
        .execute()
    )
    event_rows = event_resp.data or []
    if not event_rows:
        from fastapi import HTTPException
        from app.localization import get_message
        raise HTTPException(status_code=404, detail=get_message("errors.events.event_not_found"))
    ev = event_rows[0]

    # Fetch location name
    location_name = ""
    if ev.get("locatie_id"):
        loc_resp = (
            client.table("locatii")
            .select("nume_sala,corp_cladire")
            .eq("id", ev["locatie_id"])
            .limit(1)
            .execute()
        )
        loc_rows = loc_resp.data or []
        if loc_rows:
            loc = loc_rows[0]
            parts = [loc.get("corp_cladire", ""), loc.get("nume_sala", "")]
            location_name = ", ".join(p for p in parts if p)

    # Parse datetimes
    def parse_dt(val: str | None):
        if not val:
            return None
        dt = datetime.fromisoformat(val)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    dtstart = parse_dt(ev.get("start_date"))
    dtend = parse_dt(ev.get("end_date"))
    if dtstart is None:
        from fastapi import HTTPException
        from app.localization import get_message
        raise HTTPException(status_code=422, detail=get_message("errors.events.event_has_no_start_date"))
    if dtend is None:
        dtend = dtstart + timedelta(hours=1)

    # Build iCal
    cal = Calendar()
    cal.add("prodid", "-//USV Event Manager//usv.ro//")
    cal.add("version", "2.0")

    ical_event = ICalEvent()
    ical_event.add("uid", f"{event_id}@usv.ro")
    ical_event.add("summary", ev.get("titlu", ""))
    ical_event.add("description", ev.get("descriere", "") or "")
    ical_event.add("dtstart", dtstart)
    ical_event.add("dtend", dtend)
    ical_event.add("location", location_name)
    cal.add_component(ical_event)

    buf = io.BytesIO(cal.to_ical())
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="event-{event_id}.ics"'},
    )
