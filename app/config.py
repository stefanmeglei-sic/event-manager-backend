from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Event Manager API"
    app_version: str = "0.1.0"
    app_env: str = "development"
    debug: bool = True
    default_locale: str = "ro"

    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/event_manager"

    supabase_url: str = ""
    supabase_key: str = ""  # publishable anon/service key used by supabase-py

    jwt_secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expires_minutes: int = 60

    google_client_id: str = ""
    google_allowed_domains: str = "student.usv.ro"

    @property
    def google_allowed_domains_list(self) -> list[str]:
        return [
            domain.strip().lower()
            for domain in self.google_allowed_domains.split(",")
            if domain.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
