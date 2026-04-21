"""
Supabase client singleton for the backend.

The client is created once from settings and reused across the app.
Use `get_supabase_client()` as a FastAPI dependency or call it directly
from service functions that need Supabase PostgREST / Auth / Storage.

For raw async SQL access prefer `app.database.get_db_session()` instead,
which goes through SQLAlchemy + asyncpg and supports transactions.
"""
from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache(maxsize=1)
def get_supabase_client() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY must be set in the environment."
        )
    return create_client(settings.supabase_url, settings.supabase_key)
