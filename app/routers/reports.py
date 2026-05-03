from fastapi import APIRouter, Depends
from supabase import Client

from app.auth.dependencies import CurrentUser, require_roles
from app.supabase_client import get_supabase_client


router = APIRouter(prefix="/reports", tags=["reports"])
admin_only = require_roles("admin")


def get_client() -> Client:
    return get_supabase_client()


@router.get("/summary", summary="Summary stats")
async def get_summary(
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> dict:
    # Total events (not deleted)
    events_resp = (
        client.table("evenimente")
        .select("id,organizer_id,utilizatori!organizer_id(nume,email)", count="exact")
        .is_("deleted_at", None)
        .execute()
    )
    total_events = events_resp.count or 0
    events_data = events_resp.data or []

    # Total registrations
    reg_resp = (
        client.table("inscrieri")
        .select("id", count="exact")
        .execute()
    )
    total_registrations = reg_resp.count or 0

    avg = round(total_registrations / total_events, 1) if total_events > 0 else 0.0

    # Top organizers
    from collections import Counter
    organizer_info: dict[str, str] = {}
    for e in events_data:
        oid = e["organizer_id"]
        if oid not in organizer_info:
            user = e.get("utilizatori") or {}
            organizer_info[oid] = user.get("nume") or user.get("email") or oid
    organizer_counts = Counter(e["organizer_id"] for e in events_data)
    top_organizers = [
        {"organizer_id": oid, "organizer_name": organizer_info.get(oid, oid), "event_count": cnt}
        for oid, cnt in organizer_counts.most_common(5)
    ]

    return {
        "total_events": total_events,
        "total_registrations": total_registrations,
        "avg_participants_per_event": avg,
        "top_organizers": top_organizers,
    }


@router.get("/events-by-month", summary="Events count grouped by month")
async def get_events_by_month(
    _: CurrentUser = Depends(admin_only),
    client: Client = Depends(get_client),
) -> list[dict]:
    resp = (
        client.table("evenimente")
        .select("created_at")
        .is_("deleted_at", None)
        .order("created_at")
        .execute()
    )
    rows = resp.data or []

    from collections import defaultdict
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        dt = row["created_at"]
        # dt is ISO string e.g. "2026-04-22T10:30:00+00:00"
        month = dt[:7]  # "YYYY-MM"
        counts[month] += 1

    return [{"month": m, "count": c} for m, c in sorted(counts.items())]
