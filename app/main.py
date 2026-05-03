from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.localization import reset_current_locale, set_current_locale
from app.routers import register_routers
from app.routers.health import router as health_router


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
)

allowed_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def bind_request_locale(request: Request, call_next):
    token = set_current_locale(request.headers.get("x-locale") or settings.default_locale)
    try:
        response = await call_next(request)
    finally:
        reset_current_locale(token)
    return response

app.include_router(health_router)
register_routers(app)
