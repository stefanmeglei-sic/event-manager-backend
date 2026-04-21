from fastapi import FastAPI

from app.config import get_settings
from app.routers import auth, events, lookups, registrations, users


def register_routers(app: FastAPI) -> None:
    settings = get_settings()
    prefix = settings.api_prefix

    app.include_router(auth.router, prefix=prefix)
    app.include_router(users.router, prefix=prefix)
    app.include_router(lookups.router, prefix=prefix)
    app.include_router(events.router, prefix=prefix)
    app.include_router(registrations.router, prefix=prefix)
