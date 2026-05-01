from fastapi import FastAPI

from app.config import get_settings
from app.routers import admin, auth, events, locations, lookups, registrations, reports, users


def register_routers(app: FastAPI) -> None:
    settings = get_settings()
    prefix = settings.api_prefix

    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(lookups.router, prefix=prefix)
    app.include_router(locations.router, prefix=prefix)
    app.include_router(events.router, prefix=prefix)
    app.include_router(registrations.router, prefix=prefix)
    app.include_router(admin.router, prefix=prefix)
    app.include_router(reports.router, prefix=prefix)
