import smtplib
from email.message import EmailMessage
from pathlib import Path
from string import Template

from fastapi import HTTPException, status
from supabase import Client

from app.config import get_settings
from app.localization import get_current_locale, get_message
from app.schemas.common import MessageResponse
from app.schemas.notification import NotificationCreate, NotificationRead
from app.services.events_service import event_slug_from_event, get_event_by_id


def _to_notification_read(row: dict) -> NotificationRead:
    return NotificationRead(
        id=row["id"],
        user_id=row["user_id"],
        eveniment_id=row.get("eveniment_id"),
        mesaj=row["mesaj"],
        is_read=bool(row.get("is_read", False)),
        created_at=row.get("created_at"),
    )


def _email_template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "email_templates"


def _build_event_email_context(client: Client, event_id: str) -> dict[str, str]:
    event = get_event_by_id(client, event_id)
    event_slug = event_slug_from_event(event)
    settings = get_settings()
    base_url = (settings.frontend_public_url or "http://localhost:3000").rstrip("/")
    return {
        "event_title": event.titlu,
        "event_slug": event_slug,
        "event_url": f"{base_url}/events/{event_slug}",
    }


def _load_email_template(template_name: str, locale: str | None = None) -> Template:
    locale_name = (locale or get_current_locale()).strip().lower()
    candidate_paths = [
        _email_template_dir() / locale_name / f"{template_name}.txt",
        _email_template_dir() / "en" / f"{template_name}.txt",
    ]
    for path in candidate_paths:
        if path.exists():
            return Template(path.read_text(encoding="utf-8"))
    return Template("$message")


def _render_email_body(template_name: str, *, message: str, locale: str | None = None, **context: str) -> str:
    template = _load_email_template(template_name, locale)
    return template.safe_substitute(message=message, **context)


def _get_user_email(client: Client, user_id: str) -> str | None:
    response = (
        client.table("utilizatori")
        .select("email")
        .eq("id", user_id)
        .is_("deleted_at", None)
        .limit(1)
        .execute()
    )
    rows = response.data or []
    if not rows:
        return None
    return rows[0].get("email")


def _send_email_notification(recipient_email: str, subject: str, body: str) -> None:
    settings = get_settings()
    if not settings.smtp_host or not recipient_email:
        return

    sender = settings.smtp_from_email or settings.smtp_username
    if not sender:
        return

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = f"{settings.smtp_from_name} <{sender}>"
    email["To"] = recipient_email
    email.set_content(body)

    use_ssl = settings.smtp_use_tls and not settings.smtp_use_starttls and settings.smtp_port == 465
    if use_ssl:
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
            if settings.smtp_username:
                smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(email)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        if settings.smtp_use_starttls:
            smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(email)


def list_notifications(client: Client, *, user_id: str, limit: int = 20) -> list[NotificationRead]:
    try:
        safe_limit = max(1, min(limit, 100))
        response = (
            client.table("notificari")
            .select("id,user_id,eveniment_id,mesaj,is_read,created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(safe_limit)
            .execute()
        )
        return [_to_notification_read(row) for row in (response.data or [])]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.notifications.failed_to_fetch"),
        ) from exc


def create_notification(
    client: Client,
    payload: NotificationCreate,
    *,
    recipient_email: str | None = None,
    email_template: str = "generic_notification",
    email_context: dict[str, str] | None = None,
    email_subject: str | None = None,
) -> NotificationRead:
    try:
        response = (
            client.table("notificari")
            .insert(
                {
                    "user_id": payload.user_id,
                    "eveniment_id": payload.eveniment_id,
                    "mesaj": payload.mesaj,
                    "is_read": False,
                }
            )
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=get_message("errors.notifications.not_created"),
            )

        if payload.send_email:
            try:
                resolved_email = recipient_email or _get_user_email(client, payload.user_id)
                if resolved_email:
                    current_locale = get_current_locale()
                    body = _render_email_body(
                        email_template,
                        message=payload.mesaj,
                        locale=current_locale,
                        **(email_context or {}),
                    )
                    if email_subject:
                        subject = email_subject
                    elif email_context and email_context.get("event_title"):
                        subject = get_message(
                            "notifications.registration_subject",
                            event_title=email_context["event_title"],
                        )
                    else:
                        subject = get_message("notifications.email_subject")
                    _send_email_notification(resolved_email, subject, body)
            except Exception:
                # Email delivery is best-effort and should never block API success.
                pass

        return _to_notification_read(rows[0])
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.notifications.failed_to_create"),
        ) from exc


def event_email_context(client: Client, event_id: str) -> dict[str, str]:
    return _build_event_email_context(client, event_id)


def mark_all_notifications_read(client: Client, *, user_id: str) -> MessageResponse:
    try:
        client.table("notificari").update({"is_read": True}).eq("user_id", user_id).eq("is_read", False).execute()
        return MessageResponse(detail=get_message("notifications.marked_all_read"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=get_message("errors.notifications.failed_to_mark_read"),
        ) from exc
