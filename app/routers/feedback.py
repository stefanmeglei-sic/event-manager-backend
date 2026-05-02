import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

from app.auth.dependencies import CurrentUser, get_current_user
from app.schemas.feedback import FeedbackCreate, FeedbackOut
from app.supabase_client import get_supabase_client

router = APIRouter(tags=["feedback"])


def get_fb_client() -> Client:
    return get_supabase_client()


@router.post(
    "/events/{event_id}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback for an event",
    description="Authenticated users who have a confirmed registration can submit feedback.",
)
async def create_feedback(
    event_id: str,
    payload: FeedbackCreate,
    current_user: CurrentUser = Depends(get_current_user),
    client: Client = Depends(get_fb_client),
) -> FeedbackOut:
    # Look up "confirmed" status id in statusuri table
    status_resp = (
        client.table("statusuri")
        .select("id")
        .eq("nume", "confirmed")
        .limit(1)
        .execute()
    )
    status_rows = status_resp.data or []
    if not status_rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Missing 'confirmed' status in statusuri table",
        )
    confirmed_status_id = status_rows[0]["id"]

    # Check that user has a confirmed registration for this event
    reg_resp = (
        client.table("inscrieri")
        .select("id")
        .eq("eveniment_id", event_id)
        .eq("user_id", current_user.user_id)
        .eq("status_id", confirmed_status_id)
        .limit(1)
        .execute()
    )
    if not (reg_resp.data or []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You must have a confirmed registration to submit feedback",
        )

    # Insert feedback
    insert_resp = (
        client.table("feedback")
        .insert(
            {
                "user_id": current_user.user_id,
                "eveniment_id": event_id,
                "rating": payload.rating,
                "comentariu": payload.comentariu,
            }
        )
        .execute()
    )
    rows = insert_resp.data or []
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Feedback was not created",
        )
    return _to_feedback_out(rows[0])


class FeedbackListOut(FeedbackOut):
    pass


class FeedbackListResponse(FeedbackOut):
    pass


@router.get(
    "/events/{event_id}/feedback",
    summary="Get feedback for an event",
    description="Returns all feedback entries for the event with the average rating.",
)
async def list_feedback(
    event_id: str,
    client: Client = Depends(get_fb_client),
):
    resp = (
        client.table("feedback")
        .select("*")
        .eq("eveniment_id", event_id)
        .execute()
    )
    rows = resp.data or []
    items = [_to_feedback_out(r) for r in rows]
    average_rating: Optional[float] = None
    if items:
        average_rating = round(sum(i.rating for i in items) / len(items), 2)
    return {"average_rating": average_rating, "items": [i.model_dump() for i in items]}


def _to_feedback_out(row: dict) -> FeedbackOut:
    return FeedbackOut(
        id=uuid.UUID(str(row["id"])),
        user_id=uuid.UUID(str(row["user_id"])),
        eveniment_id=uuid.UUID(str(row["eveniment_id"])),
        rating=row["rating"],
        comentariu=row.get("comentariu"),
        created_at=str(row.get("created_at", "")),
    )
