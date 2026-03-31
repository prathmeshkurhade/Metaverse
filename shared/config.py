"""
Centralized configuration for all microservices.

WHY a shared config?
All 3 services (HTTP API, WebSocket, AI Assistant) need the same Supabase
credentials and JWT secret. Instead of duplicating env var loading in each
service, we define it once here. Each service does:
    from shared.config import settings

WHY Pydantic BaseSettings?
It automatically reads from environment variables AND .env files, with type
validation. If SUPABASE_URL is missing, you get a clear error at startup --
not a cryptic KeyError deep in your code at runtime.

WHY @lru_cache?
Settings are read once and cached for the process lifetime. Without caching,
every call to get_settings() would re-read the .env file and re-parse env vars.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Supabase ──
    # SUPABASE_URL: The URL of your Supabase project (e.g., https://xyz.supabase.co)
    # SUPABASE_KEY: The "anon" public key -- used for RLS-enforced queries
    # SUPABASE_SERVICE_KEY: The "service_role" key -- bypasses RLS (use carefully)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""

    # ── JWT ──
    # We handle auth ourselves (not Supabase Auth) because the test spec requires
    # username/password signup with admin/user roles. We sign tokens with HS256.
    # JWT_SECRET: The secret key used to sign and verify JWTs. MUST be a long random string in production.
    # JWT_ALGORITHM: HS256 = HMAC-SHA256. Symmetric signing -- same key signs and verifies.
    #   (vs ES256 which is asymmetric -- Supabase uses that, but we don't need it here)
    # JWT_EXPIRATION_MINUTES: How long a token is valid. 60 min = user re-logs once per hour.
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # ── Gemini (AI Room Assistant) ──
    # WHY Gemini instead of Anthropic? Gemini has a free tier, so no cost for learning.
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash"
    GEMINI_MAX_TOKENS: int = 1024

    # ── Service URLs (for inter-service communication) ──
    # WHY: The AI Assistant needs to call the HTTP API to get room context.
    # In Docker, these become container names (http://http-api:8000).
    # In k8s, these become service DNS names (http://http-api.default.svc.cluster.local:8000).
    HTTP_API_URL: str = "http://localhost:8000"
    WS_SERVER_URL: str = "ws://localhost:8001"
    AI_ASSISTANT_URL: str = "http://localhost:8002"

    model_config = SettingsConfigDict(
        # WHY env_file: Loads variables from .env file if it exists.
        # In production (Docker/k8s), env vars are injected directly, so no .env needed.
        # In local dev, .env is convenient so you don't export vars manually.
        # WHY absolute path? The bat scripts cd into services/http_api/ before running,
        # so a relative ".env" would look in the wrong folder. This always finds the
        # project root's .env regardless of which directory uvicorn starts from.
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        env_file_encoding="utf-8",
        # WHY extra="ignore": If .env has variables we don't define above (e.g., RANDOM_VAR),
        # Pydantic won't throw an error. This makes .env files reusable across services.
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached Settings instance. Called once per process."""
    return Settings()


# Module-level convenience -- import this directly:
#   from shared.config import settings
settings = get_settings()
